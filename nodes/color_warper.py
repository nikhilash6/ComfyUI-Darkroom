"""
Color Warper node for ComfyUI-Darkroom.
2D hue+saturation region warping with multi-region presets.
"""

import numpy as np

from ..utils.color import srgb_to_linear, linear_to_srgb, blend
from ..utils.image import tensor_to_numpy_batch, numpy_batch_to_tensor
from ..utils.raw import rgb_to_hsl, hsl_to_rgb
from ..utils.grading import hue_range_mask
from ..data.grading_presets import COLOR_WARPER_PRESETS, COLOR_WARPER_PRESET_NAMES


def _sat_range_weight(sat, sat_min, sat_max, softness=0.1):
    """
    Smooth saturation range mask. 1.0 inside [sat_min, sat_max], smooth falloff outside.
    """
    soft = max(softness, 0.01)
    # Smooth step at low end
    low_weight = np.clip((sat - sat_min + soft) / (2.0 * soft), 0.0, 1.0)
    # Smooth step at high end
    high_weight = np.clip((sat_max + soft - sat) / (2.0 * soft), 0.0, 1.0)
    return (low_weight * high_weight).astype(np.float32)


class ColorWarper:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "preset": (COLOR_WARPER_PRESET_NAMES, {
                    "default": "Custom (manual)",
                    "tooltip": "Select a color warping preset or use Custom for single-region manual control"
                }),
            },
            "optional": {
                # Source region selection
                "source_hue": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 360.0, "step": 1.0,
                    "tooltip": "Center hue of the region to warp"
                }),
                "source_hue_width": ("FLOAT", {
                    "default": 60.0, "min": 10.0, "max": 180.0, "step": 1.0,
                    "tooltip": "Width of hue range to affect (degrees)"
                }),
                "source_sat_min": ("FLOAT", {
                    "default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "Minimum saturation to affect"
                }),
                "source_sat_max": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01,
                    "tooltip": "Maximum saturation to affect"
                }),
                # Target shift
                "hue_shift": ("FLOAT", {
                    "default": 0.0, "min": -180.0, "max": 180.0, "step": 1.0,
                    "tooltip": "Shift hue by this many degrees"
                }),
                "sat_shift": ("FLOAT", {
                    "default": 0.0, "min": -100.0, "max": 100.0, "step": 1.0,
                    "tooltip": "Adjust saturation within the selected region"
                }),
                # Softness
                "feather": ("FLOAT", {
                    "default": 0.5, "min": 0.1, "max": 1.0, "step": 0.05,
                    "tooltip": "Edge softness of the warped region"
                }),
                "strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "Blend between original (0) and warped (1)"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "execute"
    CATEGORY = "AKURATE/Darkroom/Grading"

    def _apply_region(self, h, s, l, src_hue, src_hue_width, src_sat_min, src_sat_max,
                      hue_shift, sat_shift, feather):
        """Apply a single warping region to HSL data."""
        # Combined hue + saturation mask
        h_mask = hue_range_mask(h, src_hue, width=src_hue_width, softness=feather)
        s_mask = _sat_range_weight(s, src_sat_min, src_sat_max, softness=0.05 + feather * 0.1)
        combined_mask = h_mask * s_mask

        # Apply hue shift
        if abs(hue_shift) > 0.1:
            h = h + combined_mask * hue_shift
            h = h % 360.0

        # Apply saturation shift
        if abs(sat_shift) > 0.5:
            s = s * (1.0 + combined_mask * (sat_shift / 100.0))
            s = np.clip(s, 0.0, 1.0)

        return h, s

    def execute(self, image, preset="Custom (manual)",
                source_hue=0.0, source_hue_width=60.0,
                source_sat_min=0.0, source_sat_max=1.0,
                hue_shift=0.0, sat_shift=0.0,
                feather=0.5, strength=1.0):

        if strength <= 0.0:
            return (image,)

        # Build region list
        use_preset = preset != "Custom (manual)" and preset in COLOR_WARPER_PRESETS

        if not use_preset:
            # Check manual controls
            if abs(hue_shift) < 0.1 and abs(sat_shift) < 0.5:
                return (image,)

        print(f"[Darkroom] Color Warper: preset={preset}, strength={strength}")

        images = tensor_to_numpy_batch(image)
        results = []

        for img in images:
            original = img.copy()
            linear = srgb_to_linear(img)
            h, s, l = rgb_to_hsl(linear)

            if use_preset:
                # Apply all regions from preset
                p = COLOR_WARPER_PRESETS[preset]
                for region in p.regions:
                    h, s = self._apply_region(
                        h, s, l,
                        region.src_hue, region.src_hue_width,
                        region.src_sat_min, region.src_sat_max,
                        region.hue_shift, region.sat_shift,
                        feather
                    )

                # Also apply manual shift on top if active
                if abs(hue_shift) > 0.1 or abs(sat_shift) > 0.5:
                    h, s = self._apply_region(
                        h, s, l,
                        source_hue, source_hue_width,
                        source_sat_min, source_sat_max,
                        hue_shift, sat_shift,
                        feather
                    )
            else:
                # Manual single-region mode
                h, s = self._apply_region(
                    h, s, l,
                    source_hue, source_hue_width,
                    source_sat_min, source_sat_max,
                    hue_shift, sat_shift,
                    feather
                )

            result = hsl_to_rgb(h, s, l)
            result = linear_to_srgb(result)
            results.append(blend(original, result, strength))

        return (numpy_batch_to_tensor(results),)


NODE_CLASS_MAPPINGS = {"DarkroomColorWarper": ColorWarper}
NODE_DISPLAY_NAME_MAPPINGS = {"DarkroomColorWarper": "Color Warper"}
