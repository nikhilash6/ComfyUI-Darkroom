"""
Lens Profile Correction node for ComfyUI-Darkroom.

Combines distortion correction, chromatic aberration correction, and
vignetting correction in one node — simulating what Lightroom/Capture One
do with lens profiles.

Uses predefined profiles for common lens categories rather than the full
Lensfun database, keeping this dependency-free. For exact lens matching,
use the individual CA, Distortion, and Vignette nodes.
"""

import numpy as np
from scipy.ndimage import map_coordinates

from ..utils.image import tensor_to_numpy_batch, numpy_batch_to_tensor


# Lens profiles: typical distortion + CA + vignette for common lens types.
# Based on averaged Lensfun data for each category.
LENS_PROFILES = {
    "None (Bypass)": {
        "k1": 0.0, "k2": 0.0,
        "ca_r": 0.0, "ca_b": 0.0,
        "vignette": 0.0, "vignette_mid": 0.7,
    },
    "Ultra Wide (14-16mm)": {
        "k1": -0.35, "k2": 0.08,
        "ca_r": -1.5, "ca_b": 1.8,
        "vignette": 0.6, "vignette_mid": 0.35,
    },
    "Wide (20-24mm)": {
        "k1": -0.18, "k2": 0.03,
        "ca_r": -0.8, "ca_b": 1.0,
        "vignette": 0.4, "vignette_mid": 0.45,
    },
    "Wide (28-35mm)": {
        "k1": -0.08, "k2": 0.01,
        "ca_r": -0.5, "ca_b": 0.6,
        "vignette": 0.25, "vignette_mid": 0.55,
    },
    "Standard (50mm)": {
        "k1": -0.02, "k2": 0.0,
        "ca_r": -0.3, "ca_b": 0.3,
        "vignette": 0.15, "vignette_mid": 0.65,
    },
    "Short Tele (85mm)": {
        "k1": 0.01, "k2": 0.0,
        "ca_r": -0.2, "ca_b": 0.2,
        "vignette": 0.1, "vignette_mid": 0.7,
    },
    "Telephoto (135-200mm)": {
        "k1": 0.04, "k2": -0.01,
        "ca_r": -0.15, "ca_b": 0.15,
        "vignette": 0.08, "vignette_mid": 0.75,
    },
    "Super Tele (300mm+)": {
        "k1": 0.06, "k2": -0.015,
        "ca_r": -0.1, "ca_b": 0.1,
        "vignette": 0.05, "vignette_mid": 0.8,
    },
    "Vintage 50mm f/1.4": {
        "k1": -0.05, "k2": 0.01,
        "ca_r": -1.2, "ca_b": 1.5,
        "vignette": 0.5, "vignette_mid": 0.4,
    },
    "Vintage 35mm f/2.8": {
        "k1": -0.12, "k2": 0.02,
        "ca_r": -1.0, "ca_b": 1.2,
        "vignette": 0.45, "vignette_mid": 0.4,
    },
    "Cheap Kit Lens (18-55mm)": {
        "k1": -0.15, "k2": 0.04,
        "ca_r": -1.8, "ca_b": 2.0,
        "vignette": 0.5, "vignette_mid": 0.35,
    },
    "Cinema Prime": {
        "k1": -0.01, "k2": 0.0,
        "ca_r": -0.1, "ca_b": 0.1,
        "vignette": 0.05, "vignette_mid": 0.75,
    },
    "Anamorphic": {
        "k1": -0.08, "k2": 0.02,
        "ca_r": -0.6, "ca_b": 0.8,
        "vignette": 0.35, "vignette_mid": 0.4,
    },
}

PROFILE_NAMES = list(LENS_PROFILES.keys())


def _apply_lens_profile(img, k1, k2, ca_r, ca_b, vignette_strength, vignette_mid):
    """Apply combined lens correction: distortion + CA + vignette."""
    h, w = img.shape[:2]
    cy, cx = h / 2.0, w / 2.0
    scale = min(h, w) / 1024.0

    # Normalized coordinates
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    ny = (yy - cy) / cy
    nx = (xx - cx) / cx
    r2 = nx * nx + ny * ny
    r4 = r2 * r2
    r = np.sqrt(r2)

    result = np.empty_like(img)

    # Per-channel: each gets distortion + its own CA shift
    ca_shifts = [ca_r * scale, 0.0, ca_b * scale]
    max_r = np.sqrt(cx * cx + cy * cy)

    for c in range(3):
        # Distortion
        distort = 1.0 + k1 * r2 + k2 * r4

        # Add CA (radial shift)
        ca = ca_shifts[c]
        if abs(ca) > 0.01:
            ca_factor = 1.0 + (ca / max_r) * r
            total_factor = distort * ca_factor
        else:
            total_factor = distort

        src_nx = nx * total_factor
        src_ny = ny * total_factor

        src_x = src_nx * cx + cx
        src_y = src_ny * cy + cy

        result[..., c] = map_coordinates(
            img[..., c], [src_y, src_x],
            order=3, mode='reflect'
        ).astype(np.float32)

    # Vignette correction (brighten edges to counteract natural falloff)
    if vignette_strength > 0.01:
        # Cos^4 falloff model
        cos_theta = 1.0 / np.sqrt(1.0 + r2)
        falloff = cos_theta ** 4
        # Correction: divide by falloff (brighten edges)
        transition = np.clip((r - vignette_mid * 0.8) / 0.4, 0.0, 1.0)
        correction = 1.0 + transition * (1.0 / np.clip(falloff, 0.3, 1.0) - 1.0) * vignette_strength
        result = result * correction[..., np.newaxis]

    return np.clip(result, 0.0, 1.0).astype(np.float32)


class LensProfile:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "profile": (PROFILE_NAMES, {
                    "default": "None (Bypass)",
                    "tooltip": "Lens profile to simulate or correct. Applies distortion, CA, and vignette together"
                }),
                "mode": (["Add Aberrations", "Correct Aberrations"], {
                    "default": "Add Aberrations",
                    "tooltip": "'Add' simulates lens flaws. 'Correct' removes them (inverts the profile)"
                }),
            },
            "optional": {
                "strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 2.0, "step": 0.1,
                    "tooltip": "Overall profile strength. 0.5 = half effect"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "execute"
    CATEGORY = "AKURATE/Darkroom/Lens"

    def execute(self, image, profile, mode, strength=1.0):
        if profile == "None (Bypass)" or strength < 0.01:
            return (image,)

        p = LENS_PROFILES[profile]
        sign = 1.0 if mode == "Add Aberrations" else -1.0

        k1 = p["k1"] * strength * sign
        k2 = p["k2"] * strength * sign
        ca_r = p["ca_r"] * strength * sign
        ca_b = p["ca_b"] * strength * sign
        vig = p["vignette"] * strength
        vig_mid = p["vignette_mid"]

        # In correct mode, vignette is additive (brighten edges)
        # In add mode, vignette is subtractive (darken edges) — handled inside
        if mode == "Correct Aberrations":
            vig = vig  # correction brightens edges
        else:
            vig = -vig  # simulation darkens edges

        print(f"[Darkroom] Lens Profile: {profile} ({mode}), strength={strength}")

        arrays = tensor_to_numpy_batch(image)
        processed = []

        for img in arrays:
            result = _apply_lens_profile(img, k1, k2, ca_r, ca_b, abs(vig), vig_mid)

            # For "Add" mode with vignette, apply darkening instead of brightening
            if vig < 0:
                h, w = result.shape[:2]
                cy, cx = h / 2.0, w / 2.0
                yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
                ny = (yy - cy) / cy
                nx = (xx - cx) / cx
                r2 = nx * nx + ny * ny
                cos_theta = 1.0 / np.sqrt(1.0 + r2)
                r = np.sqrt(r2)
                falloff = cos_theta ** 4
                transition = np.clip((r - vig_mid * 0.8) / 0.4, 0.0, 1.0)
                mask = 1.0 - transition * (1.0 - falloff) * abs(vig) * 2
                result = result * np.clip(mask, 0.0, 1.0)[..., np.newaxis]
                result = np.clip(result, 0.0, 1.0).astype(np.float32)

            processed.append(result)

        return (numpy_batch_to_tensor(processed),)


NODE_CLASS_MAPPINGS = {
    "DarkroomLensProfile": LensProfile,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DarkroomLensProfile": "Lens Profile",
}
