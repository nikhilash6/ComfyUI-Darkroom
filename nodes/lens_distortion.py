"""
Lens Distortion node for ComfyUI-Darkroom.

Simulates barrel distortion (wide-angle), pincushion distortion (telephoto),
and mustache/complex distortion. Uses the Brown-Conrady distortion model.

Select a real lens profile or use Custom for manual control.
"""

import numpy as np
from scipy.ndimage import map_coordinates

from ..data.lens_profiles import LENS_PROFILES_FLAT, LENS_PROFILE_NAMES
from ..utils.image import tensor_to_numpy_batch, numpy_batch_to_tensor


PRESET_NAMES = ["Custom"] + LENS_PROFILE_NAMES


def _apply_distortion(img, k1, k2):
    """
    Apply Brown-Conrady radial distortion.
    r_distorted = r * (1 + k1*r^2 + k2*r^4)
    """
    h, w = img.shape[:2]
    cy, cx = h / 2.0, w / 2.0

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    ny = (yy - cy) / cy
    nx = (xx - cx) / cx

    r2 = nx * nx + ny * ny
    r4 = r2 * r2
    distort = 1.0 + k1 * r2 + k2 * r4

    src_x = nx * distort * cx + cx
    src_y = ny * distort * cy + cy

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
                "lens": (PRESET_NAMES, {
                    "default": "Custom",
                    "tooltip": "Select a real lens or 'Custom' for manual distortion control"
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

    def execute(self, image, lens, strength, k1=0.0, k2=0.0):
        if lens != "Custom" and lens in LENS_PROFILES_FLAT:
            p = LENS_PROFILES_FLAT[lens]
            k1 = p.k1
            k2 = p.k2

        k1 *= strength
        k2 *= strength

        if abs(k1) < 0.001 and abs(k2) < 0.001:
            return (image,)

        print(f"[Darkroom] Lens Distortion: {lens}, k1={k1:.4f}, k2={k2:.4f}")

        arrays = tensor_to_numpy_batch(image)
        processed = [_apply_distortion(img, k1, k2) for img in arrays]

        return (numpy_batch_to_tensor(processed),)


NODE_CLASS_MAPPINGS = {
    "DarkroomLensDistortion": LensDistortion,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DarkroomLensDistortion": "Lens Distortion",
}
