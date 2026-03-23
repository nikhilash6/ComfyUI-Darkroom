"""
Chromatic Aberration node for ComfyUI-Darkroom.

Simulates lateral and longitudinal chromatic aberration — the color fringing
caused by a lens failing to focus all wavelengths to the same point.

Lateral CA: color shift increases toward the edges (radial scaling per channel).
Longitudinal CA: color fringing at depth transitions (focus-dependent).
"""

import numpy as np
from scipy.ndimage import map_coordinates

from ..utils.image import tensor_to_numpy_batch, numpy_batch_to_tensor


CA_PRESETS = {
    "Subtle": {"shift_r": -0.5, "shift_b": 0.5, "mode": "lateral"},
    "Moderate": {"shift_r": -1.0, "shift_b": 1.0, "mode": "lateral"},
    "Heavy": {"shift_r": -2.0, "shift_b": 2.0, "mode": "lateral"},
    "Vintage Lens": {"shift_r": -1.5, "shift_b": 1.8, "mode": "lateral"},
    "Anamorphic": {"shift_r": -0.8, "shift_b": 1.2, "mode": "lateral"},
    "Custom": {"shift_r": -1.0, "shift_b": 1.0, "mode": "lateral"},
}

PRESET_NAMES = list(CA_PRESETS.keys())


def _apply_lateral_ca(img, shift_r, shift_b):
    """
    Apply lateral CA by radially scaling R and B channels.
    Green channel stays fixed (reference). Shift in pixels at the image edge.
    """
    h, w = img.shape[:2]
    cy, cx = h / 2.0, w / 2.0

    # Max radius (corner distance)
    max_r = np.sqrt(cx * cx + cy * cy)

    # Build coordinate grid
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)

    # Offset from center
    dy = yy - cy
    dx = xx - cx

    # Radial distance normalized to [0, 1]
    r = np.sqrt(dy * dy + dx * dx) / max_r

    result = np.empty_like(img)

    for c, shift in enumerate([shift_r, 0.0, shift_b]):
        if abs(shift) < 0.01:
            result[..., c] = img[..., c]
            continue

        # Scale factor: at the edge, pixel shifts by `shift` pixels
        # Quadratic radial profile (realistic — CA grows with r^2)
        scale = 1.0 + (shift / max_r) * r

        # New coordinates
        new_y = cy + dy * scale
        new_x = cx + dx * scale

        # Remap using cubic interpolation
        result[..., c] = map_coordinates(
            img[..., c], [new_y, new_x],
            order=3, mode='reflect'
        ).astype(np.float32)

    return np.clip(result, 0.0, 1.0).astype(np.float32)


class ChromaticAberration:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "preset": (PRESET_NAMES, {
                    "default": "Moderate",
                    "tooltip": "CA preset. 'Custom' uses manual controls"
                }),
                "strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 3.0, "step": 0.1,
                    "tooltip": "Overall CA intensity multiplier"
                }),
            },
            "optional": {
                "shift_r": ("FLOAT", {
                    "default": -1.0, "min": -5.0, "max": 5.0, "step": 0.1,
                    "tooltip": "Red channel shift in pixels at image edge. Negative = inward"
                }),
                "shift_b": ("FLOAT", {
                    "default": 1.0, "min": -5.0, "max": 5.0, "step": 0.1,
                    "tooltip": "Blue channel shift in pixels at image edge. Positive = outward"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "execute"
    CATEGORY = "AKURATE/Darkroom/Lens"

    def execute(self, image, preset, strength, shift_r=-1.0, shift_b=1.0):
        if strength <= 0.0:
            return (image,)

        if preset != "Custom":
            p = CA_PRESETS[preset]
            shift_r = p["shift_r"]
            shift_b = p["shift_b"]

        # Scale by strength and image resolution
        arrays = tensor_to_numpy_batch(image)
        processed = []

        for img in arrays:
            h, w = img.shape[:2]
            scale = min(h, w) / 1024.0  # normalize to 1024px
            sr = shift_r * strength * scale
            sb = shift_b * strength * scale

            print(f"[Darkroom] Chromatic Aberration: shift_r={sr:.2f}px, shift_b={sb:.2f}px")
            result = _apply_lateral_ca(img, sr, sb)
            processed.append(result)

        return (numpy_batch_to_tensor(processed),)


NODE_CLASS_MAPPINGS = {
    "DarkroomChromaticAberration": ChromaticAberration,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DarkroomChromaticAberration": "Chromatic Aberration",
}
