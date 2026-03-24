"""
Skin Tone Uniformity node for ComfyUI-Darkroom.
Capture One-style skin tone evening: smooths color variations in skin
while fully preserving luminance texture and fine detail.

The key insight: local chrominance blur barely works because skin pixels
already have similar hues. Instead, we PULL each skin pixel toward the
AREA-WEIGHTED MEAN skin color. This evens out redness, sallowness, and
uneven tan while preserving luminance detail completely.
"""

import numpy as np
from scipy.ndimage import gaussian_filter

from ..utils.color import luminance_rec709, blend
from ..utils.image import tensor_to_numpy_batch, numpy_batch_to_tensor
from ..utils.raw import rgb_to_hsl, hsl_to_rgb


# Preset definitions: (hue_center, hue_width, sat_min, sat_max, lum_min, lum_max)
SKIN_PRESETS = {
    "Universal — all skin tones": (25.0, 45.0, 0.08, 0.85, 0.10, 0.92),
    "Light / Fair skin": (20.0, 30.0, 0.10, 0.65, 0.40, 0.92),
    "Medium / Olive skin": (25.0, 35.0, 0.12, 0.75, 0.25, 0.80),
    "Dark / Deep skin": (22.0, 40.0, 0.10, 0.80, 0.08, 0.55),
    "Warm / Golden skin": (30.0, 35.0, 0.15, 0.80, 0.20, 0.85),
    "Cool / Pink skin": (12.0, 30.0, 0.10, 0.70, 0.30, 0.90),
    "Custom": None,
}

PRESET_LIST = list(SKIN_PRESETS.keys())


def _skin_mask(h, s, l, hue_center, hue_width, sat_min, sat_max, lum_min, lum_max):
    """
    Build a soft skin-tone mask from HSL channels.
    Uses raised-cosine feathering on hue and smooth ramps on sat/lum.
    """
    diff = np.abs(h - hue_center)
    diff = np.minimum(diff, 360.0 - diff)
    hue_weight = np.clip((1.0 + np.cos(np.pi * diff / hue_width)) * 0.5, 0.0, 1.0)
    hue_weight[diff > hue_width] = 0.0

    sat_feather = 0.08
    sat_weight = np.clip((s - sat_min) / (sat_feather + 1e-10), 0.0, 1.0)
    sat_weight *= np.clip((sat_max - s) / (sat_feather + 1e-10), 0.0, 1.0)

    lum_feather = 0.10
    lum_weight = np.clip((l - lum_min) / (lum_feather + 1e-10), 0.0, 1.0)
    lum_weight *= np.clip((lum_max - l) / (lum_feather + 1e-10), 0.0, 1.0)

    return (hue_weight * sat_weight * lum_weight).astype(np.float32)


class SkinToneUniformity:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "preset": (PRESET_LIST, {
                    "default": "Universal — all skin tones",
                    "tooltip": (
                        "Skin tone range preset. Each covers different skin types. "
                        "Select 'Custom' to set HSL ranges manually"
                    )
                }),
                "amount": ("FLOAT", {
                    "default": 60.0, "min": 0.0, "max": 100.0, "step": 1.0,
                    "tooltip": "How much to even out skin color (0 = off, 100 = fully uniform)"
                }),
            },
            "optional": {
                "smoothing_radius": ("FLOAT", {
                    "default": 60.0, "min": 10.0, "max": 100.0, "step": 1.0,
                    "tooltip": "Color averaging radius. Lower = local patches only, Higher = global average"
                }),
                "hue_center": ("FLOAT", {
                    "default": 25.0, "min": 0.0, "max": 360.0, "step": 1.0,
                    "tooltip": "(Custom only) Center hue for skin detection"
                }),
                "hue_width": ("FLOAT", {
                    "default": 45.0, "min": 10.0, "max": 90.0, "step": 1.0,
                    "tooltip": "(Custom only) Hue range width"
                }),
                "saturation_min": ("FLOAT", {
                    "default": 0.08, "min": 0.0, "max": 0.5, "step": 0.01,
                    "tooltip": "(Custom only) Minimum saturation"
                }),
                "saturation_max": ("FLOAT", {
                    "default": 0.85, "min": 0.3, "max": 1.0, "step": 0.01,
                    "tooltip": "(Custom only) Maximum saturation"
                }),
                "luminance_min": ("FLOAT", {
                    "default": 0.10, "min": 0.0, "max": 0.5, "step": 0.01,
                    "tooltip": "(Custom only) Minimum luminance"
                }),
                "luminance_max": ("FLOAT", {
                    "default": 0.92, "min": 0.5, "max": 1.0, "step": 0.01,
                    "tooltip": "(Custom only) Maximum luminance"
                }),
                "strength": ("FLOAT", {
                    "default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05,
                    "tooltip": "Blend between original (0) and corrected (1)"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "IMAGE",)
    RETURN_NAMES = ("image", "mask_preview",)
    FUNCTION = "execute"
    CATEGORY = "AKURATE/Darkroom/Raw"

    def execute(self, image, preset="Universal — all skin tones", amount=60.0,
                smoothing_radius=60.0, hue_center=25.0, hue_width=45.0,
                saturation_min=0.08, saturation_max=0.85,
                luminance_min=0.10, luminance_max=0.92,
                strength=1.0):

        # Apply preset (override manual sliders unless Custom)
        p = SKIN_PRESETS.get(preset)
        if p is not None:
            hue_center, hue_width, saturation_min, saturation_max, luminance_min, luminance_max = p

        if strength <= 0.0 or amount < 0.5:
            return (image, image)

        images = tensor_to_numpy_batch(image)
        results = []
        masks = []

        for img in images:
            original = img.copy()
            h_img, w_img = img.shape[:2]

            h, s, l = rgb_to_hsl(img)

            # Build soft skin mask
            mask = _skin_mask(h, s, l, hue_center, hue_width,
                              saturation_min, saturation_max,
                              luminance_min, luminance_max)

            # Smooth mask edges
            mask_smooth = gaussian_filter(mask, sigma=max(h_img, w_img) * 0.015)
            mask_smooth = np.clip(mask_smooth, 0.0, 1.0)

            # --- STRATEGY: Pull toward weighted-average skin color ---
            # Instead of local blur (which barely changes similar hues),
            # compute the MASK-WEIGHTED MEAN hue and saturation across the
            # entire skin area, then blend each pixel toward that mean.
            # This is what Capture One actually does — it normalizes
            # skin color toward an area average.

            ref_size = 1024.0
            scale = max(h_img, w_img) / ref_size

            # Compute weighted-average target color using large-radius blur
            # Higher smoothing_radius = more global average, lower = local patches
            target_sigma = (smoothing_radius / 100.0) * 40.0 * scale

            # Hue averaging in circular space (handles wraparound)
            h_sin = np.sin(np.radians(h))
            h_cos = np.cos(np.radians(h))

            # Weight by mask so non-skin doesn't pollute the average
            weighted_sin = h_sin * mask_smooth
            weighted_cos = h_cos * mask_smooth
            weight_sum = mask_smooth.copy()

            # Large blur to compute local weighted average
            avg_sin = gaussian_filter(weighted_sin, sigma=target_sigma)
            avg_cos = gaussian_filter(weighted_cos, sigma=target_sigma)
            avg_weight = gaussian_filter(weight_sum, sigma=target_sigma) + 1e-10

            # Normalized weighted average hue
            target_h = np.degrees(np.arctan2(avg_sin / avg_weight, avg_cos / avg_weight)) % 360.0

            # Weighted average saturation
            weighted_s = s * mask_smooth
            avg_s = gaussian_filter(weighted_s, sigma=target_sigma)
            target_s = np.clip(avg_s / avg_weight, 0.0, 1.0)

            # Amount controls how far we pull toward the target
            pull = amount / 100.0

            # Compute hue difference (circular)
            h_diff = target_h - h
            # Handle wraparound: take shortest path
            h_diff = np.where(h_diff > 180, h_diff - 360, h_diff)
            h_diff = np.where(h_diff < -180, h_diff + 360, h_diff)

            # Apply: pull hue and saturation toward target, weighted by mask
            h_new = h + mask_smooth * pull * h_diff
            h_new = h_new % 360.0

            s_diff = target_s - s
            s_new = s + mask_smooth * pull * s_diff
            s_new = np.clip(s_new, 0.0, 1.0)

            # Reconstruct with ORIGINAL luminance (preserves all texture/detail)
            result = hsl_to_rgb(h_new.astype(np.float32),
                                s_new.astype(np.float32),
                                l)
            result = np.clip(result, 0.0, 1.0).astype(np.float32)
            results.append(blend(original, result, strength))

            # Mask preview
            mask_vis = np.stack([mask, mask, mask], axis=-1).astype(np.float32)
            masks.append(mask_vis)

        return (numpy_batch_to_tensor(results),
                numpy_batch_to_tensor(masks))


NODE_CLASS_MAPPINGS = {"DarkroomSkinToneUniformity": SkinToneUniformity}
NODE_DISPLAY_NAME_MAPPINGS = {"DarkroomSkinToneUniformity": "Skin Tone Uniformity"}
