"""
Lens Profile node for ComfyUI-Darkroom.

Combines distortion correction, chromatic aberration correction, and
vignetting correction in one node — simulating what Lightroom/Capture One
do with lens profiles.

Select a real lens to apply or correct all its optical characteristics at once.
"""

import numpy as np
from scipy.ndimage import map_coordinates

from ..data.lens_profiles import LENS_PROFILES_FLAT, LENS_PROFILE_NAMES
from ..utils.image import tensor_to_numpy_batch, numpy_batch_to_tensor


PRESET_NAMES = LENS_PROFILE_NAMES  # No "Custom" — use individual nodes for that


def _apply_lens_profile(img, k1, k2, ca_r, ca_b, vignette_strength, vignette_mid, mode):
    """Apply combined lens correction: distortion + CA + vignette."""
    h, w = img.shape[:2]
    cy, cx = h / 2.0, w / 2.0
    scale = min(h, w) / 1024.0

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    ny = (yy - cy) / cy
    nx = (xx - cx) / cx
    r2 = nx * nx + ny * ny
    r4 = r2 * r2
    r = np.sqrt(r2)
    max_r = np.sqrt(cx * cx + cy * cy)

    result = np.empty_like(img)

    # Per-channel: each gets distortion + its own CA shift
    ca_shifts = [ca_r * scale, 0.0, ca_b * scale]

    for c in range(3):
        distort = 1.0 + k1 * r2 + k2 * r4

        ca = ca_shifts[c]
        if abs(ca) > 0.01:
            ca_factor = 1.0 + (ca / max_r) * r
            total_factor = distort * ca_factor
        else:
            total_factor = distort

        src_x = nx * total_factor * cx + cx
        src_y = ny * total_factor * cy + cy

        result[..., c] = map_coordinates(
            img[..., c], [src_y, src_x],
            order=3, mode='reflect'
        ).astype(np.float32)

    # Vignette
    if vignette_strength > 0.01:
        cos_theta = 1.0 / np.sqrt(1.0 + r2)
        falloff = cos_theta ** 4
        transition = np.clip((r - vignette_mid * 0.8) / 0.4, 0.0, 1.0)

        if mode == "Add Aberrations":
            # Darken edges
            mask = 1.0 - transition * (1.0 - falloff) * vignette_strength * 2
            result = result * np.clip(mask, 0.0, 1.0)[..., np.newaxis]
        else:
            # Brighten edges (correct vignette)
            correction = 1.0 + transition * (1.0 / np.clip(falloff, 0.3, 1.0) - 1.0) * vignette_strength
            result = result * correction[..., np.newaxis]

    return np.clip(result, 0.0, 1.0).astype(np.float32)


class LensProfile:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "lens": (PRESET_NAMES, {
                    "default": PRESET_NAMES[0],
                    "tooltip": "Select a lens to simulate or correct its optical characteristics"
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

    def execute(self, image, lens, mode, strength=1.0):
        if strength < 0.01 or lens not in LENS_PROFILES_FLAT:
            return (image,)

        p = LENS_PROFILES_FLAT[lens]
        sign = 1.0 if mode == "Add Aberrations" else -1.0

        k1 = p.k1 * strength * sign
        k2 = p.k2 * strength * sign
        ca_r = p.ca_r * strength * sign
        ca_b = p.ca_b * strength * sign
        vig = p.vig_strength * strength
        vig_mid = p.vig_midpoint

        print(f"[Darkroom] Lens Profile: {p.name} ({mode}), strength={strength}")

        arrays = tensor_to_numpy_batch(image)
        processed = [
            _apply_lens_profile(img, k1, k2, ca_r, ca_b, vig, vig_mid, mode)
            for img in arrays
        ]

        return (numpy_batch_to_tensor(processed),)


NODE_CLASS_MAPPINGS = {
    "DarkroomLensProfile": LensProfile,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DarkroomLensProfile": "Lens Profile",
}
