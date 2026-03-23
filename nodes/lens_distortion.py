"""
Lens Distortion node for ComfyUI-Darkroom.

Simulates barrel distortion (wide-angle), pincushion distortion (telephoto),
and mustache/complex distortion. Uses the Brown-Conrady distortion model
with k1/k2 radial coefficients.

Can also be used to CORRECT distortion by inverting the coefficients.
"""

import numpy as np
from scipy.ndimage import map_coordinates

from ..utils.image import tensor_to_numpy_batch, numpy_batch_to_tensor


DISTORTION_PRESETS = {
    "None": {"k1": 0.0, "k2": 0.0},
    "Barrel - Subtle": {"k1": -0.1, "k2": 0.0},
    "Barrel - Moderate": {"k1": -0.25, "k2": 0.02},
    "Barrel - Heavy (Fisheye)": {"k1": -0.5, "k2": 0.1},
    "Pincushion - Subtle": {"k1": 0.1, "k2": 0.0},
    "Pincushion - Moderate": {"k1": 0.25, "k2": -0.02},
    "Mustache": {"k1": -0.3, "k2": 0.15},
    "Wide-Angle 24mm": {"k1": -0.15, "k2": 0.03},
    "Wide-Angle 16mm": {"k1": -0.35, "k2": 0.08},
    "Telephoto 200mm": {"k1": 0.05, "k2": -0.01},
    "Custom": {"k1": 0.0, "k2": 0.0},
}

PRESET_NAMES = list(DISTORTION_PRESETS.keys())


def _apply_distortion(img, k1, k2):
    """
    Apply Brown-Conrady radial distortion.

    r_distorted = r * (1 + k1*r^2 + k2*r^4)

    k1 < 0: barrel distortion (wide-angle)
    k1 > 0: pincushion distortion (telephoto)
    k2: higher-order correction (mustache distortion when sign differs from k1)
    """
    h, w = img.shape[:2]
    cy, cx = h / 2.0, w / 2.0

    # Normalize coordinates to [-1, 1]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    ny = (yy - cy) / cy
    nx = (xx - cx) / cx

    # Radial distance squared
    r2 = nx * nx + ny * ny
    r4 = r2 * r2

    # Distortion factor
    distort = 1.0 + k1 * r2 + k2 * r4

    # Distorted normalized coordinates
    dnx = nx * distort
    dny = ny * distort

    # Convert back to pixel coordinates
    src_x = dnx * cx + cx
    src_y = dny * cy + cy

    # Remap all channels
    result = np.empty_like(img)
    for c in range(img.shape[2]):
        result[..., c] = map_coordinates(
            img[..., c], [src_y, src_x],
            order=3, mode='constant', cval=0.0
        ).astype(np.float32)

    return np.clip(result, 0.0, 1.0).astype(np.float32)


class LensDistortion:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "preset": (PRESET_NAMES, {
                    "default": "None",
                    "tooltip": "Distortion preset simulating common lens types"
                }),
                "strength": ("FLOAT", {
                    "default": 1.0, "min": -2.0, "max": 2.0, "step": 0.1,
                    "tooltip": "Multiplier. Negative inverts (correct distortion instead of adding it)"
                }),
            },
            "optional": {
                "k1": ("FLOAT", {
                    "default": 0.0, "min": -1.0, "max": 1.0, "step": 0.01,
                    "tooltip": "Primary radial coefficient. Negative=barrel, Positive=pincushion"
                }),
                "k2": ("FLOAT", {
                    "default": 0.0, "min": -0.5, "max": 0.5, "step": 0.01,
                    "tooltip": "Secondary radial coefficient. Creates mustache distortion when opposite sign to k1"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "execute"
    CATEGORY = "AKURATE/Darkroom/Lens"

    def execute(self, image, preset, strength, k1=0.0, k2=0.0):
        if preset != "Custom":
            p = DISTORTION_PRESETS[preset]
            k1 = p["k1"]
            k2 = p["k2"]

        k1 *= strength
        k2 *= strength

        if abs(k1) < 0.001 and abs(k2) < 0.001:
            return (image,)

        print(f"[Darkroom] Lens Distortion: k1={k1:.4f}, k2={k2:.4f}")

        arrays = tensor_to_numpy_batch(image)
        processed = [_apply_distortion(img, k1, k2) for img in arrays]

        return (numpy_batch_to_tensor(processed),)


NODE_CLASS_MAPPINGS = {
    "DarkroomLensDistortion": LensDistortion,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DarkroomLensDistortion": "Lens Distortion",
}
