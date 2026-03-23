"""
Vignette node for ComfyUI-Darkroom.

Physically-based optical vignette simulation using the cos^4 law
(natural light falloff) plus mechanical vignetting from lens barrel.

Supports both darkening (natural) and brightening (anti-vignette for correction).
"""

import numpy as np

from ..utils.image import tensor_to_numpy_batch, numpy_batch_to_tensor


VIGNETTE_PRESETS = {
    "Subtle": {"intensity": 0.3, "midpoint": 0.7, "roundness": 1.0, "feather": 0.5, "cos4": True},
    "Standard": {"intensity": 0.5, "midpoint": 0.5, "roundness": 1.0, "feather": 0.4, "cos4": True},
    "Heavy": {"intensity": 0.8, "midpoint": 0.4, "roundness": 1.0, "feather": 0.3, "cos4": True},
    "Vintage Wide": {"intensity": 0.6, "midpoint": 0.35, "roundness": 0.8, "feather": 0.5, "cos4": False},
    "Portrait Soft": {"intensity": 0.4, "midpoint": 0.6, "roundness": 1.0, "feather": 0.6, "cos4": True},
    "Anamorphic": {"intensity": 0.5, "midpoint": 0.45, "roundness": 0.5, "feather": 0.4, "cos4": False},
    "Custom": {"intensity": 0.5, "midpoint": 0.5, "roundness": 1.0, "feather": 0.4, "cos4": True},
}

PRESET_NAMES = list(VIGNETTE_PRESETS.keys())


def _build_vignette_mask(h, w, midpoint, roundness, feather, use_cos4):
    """
    Build a vignette falloff mask.

    midpoint: where falloff begins (0=center, 1=edge)
    roundness: 1.0=circular, <1=elliptical (wider), >1=elliptical (taller)
    feather: transition smoothness (0=hard, 1=very gradual)
    use_cos4: apply cos^4 natural light falloff
    """
    cy, cx = h / 2.0, w / 2.0

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)

    # Normalized distance from center, accounting for aspect ratio and roundness
    dy = (yy - cy) / cy
    dx = (xx - cx) / cx

    # Apply roundness (stretch one axis)
    if roundness != 1.0:
        dy = dy / max(roundness, 0.01)

    # Radial distance [0..~1.4 at corners]
    r = np.sqrt(dx * dx + dy * dy)

    if use_cos4:
        # Cos^4 law: I = I0 * cos^4(theta)
        # theta = arctan(r * sensor_factor), approximate with r directly
        # Softer, physically accurate falloff
        cos_theta = 1.0 / np.sqrt(1.0 + r * r)
        falloff = cos_theta ** 4
        # Blend with midpoint control
        mask = np.where(r < midpoint, 1.0, falloff)
        # Smooth transition at midpoint
        transition = np.clip((r - midpoint * 0.8) / max(feather, 0.01), 0.0, 1.0)
        mask = 1.0 - transition * (1.0 - falloff)
    else:
        # Simple radial falloff with feather
        inner = midpoint
        outer = midpoint + feather * (1.414 - midpoint)  # extend to corners
        mask = 1.0 - np.clip((r - inner) / max(outer - inner, 0.01), 0.0, 1.0)
        # Smooth the transition with power curve
        mask = mask ** 1.5

    return mask.astype(np.float32)


class Vignette:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "preset": (PRESET_NAMES, {
                    "default": "Standard",
                    "tooltip": "Vignette preset. 'Custom' uses manual controls"
                }),
                "intensity": ("FLOAT", {
                    "default": 0.5, "min": -1.0, "max": 1.0, "step": 0.05,
                    "tooltip": "Darkening intensity. Negative = anti-vignette (brighten edges)"
                }),
            },
            "optional": {
                "midpoint": ("FLOAT", {
                    "default": 0.5, "min": 0.1, "max": 1.0, "step": 0.05,
                    "tooltip": "Where falloff begins. 0.1=near center, 1.0=only at corners"
                }),
                "roundness": ("FLOAT", {
                    "default": 1.0, "min": 0.3, "max": 2.0, "step": 0.1,
                    "tooltip": "Shape: 1.0=circular, <1=wide ellipse, >1=tall ellipse"
                }),
                "feather": ("FLOAT", {
                    "default": 0.4, "min": 0.05, "max": 1.0, "step": 0.05,
                    "tooltip": "Transition smoothness. Higher = more gradual falloff"
                }),
                "cos4_falloff": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Use physically-based cos^4 light falloff law"
                }),
                "tint_r": ("FLOAT", {
                    "default": 1.0, "min": 0.5, "max": 1.5, "step": 0.05,
                    "tooltip": "Red tint in vignetted areas. >1 = warm vignette"
                }),
                "tint_g": ("FLOAT", {
                    "default": 1.0, "min": 0.5, "max": 1.5, "step": 0.05,
                    "tooltip": "Green tint in vignetted areas"
                }),
                "tint_b": ("FLOAT", {
                    "default": 1.0, "min": 0.5, "max": 1.5, "step": 0.05,
                    "tooltip": "Blue tint in vignetted areas. >1 = cool vignette"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "execute"
    CATEGORY = "AKURATE/Darkroom/Lens"

    def execute(self, image, preset, intensity,
                midpoint=0.5, roundness=1.0, feather=0.4, cos4_falloff=True,
                tint_r=1.0, tint_g=1.0, tint_b=1.0):

        if abs(intensity) < 0.01:
            return (image,)

        if preset != "Custom":
            p = VIGNETTE_PRESETS[preset]
            midpoint = p["midpoint"]
            roundness = p["roundness"]
            feather = p["feather"]
            cos4_falloff = p["cos4"]

        print(f"[Darkroom] Vignette: preset={preset}, intensity={intensity}, midpoint={midpoint}")

        arrays = tensor_to_numpy_batch(image)
        processed = []

        for img in arrays:
            h, w = img.shape[:2]
            mask = _build_vignette_mask(h, w, midpoint, roundness, feather, cos4_falloff)

            # Apply intensity
            if intensity > 0:
                # Darken: multiply by mask raised to intensity power
                vignette = mask ** (intensity * 2)
            else:
                # Anti-vignette: invert the effect (brighten edges)
                vignette = 1.0 + (1.0 - mask) * abs(intensity)

            # Apply per-channel with tint
            tint = np.array([tint_r, tint_g, tint_b], dtype=np.float32)
            result = img.copy()
            for c in range(3):
                if intensity > 0:
                    # Darken with tint shift in dark areas
                    channel_vignette = vignette * (1.0 + (tint[c] - 1.0) * (1.0 - mask))
                    result[..., c] = img[..., c] * channel_vignette
                else:
                    result[..., c] = img[..., c] * vignette * tint[c]

            result = np.clip(result, 0.0, 1.0).astype(np.float32)
            processed.append(result)

        return (numpy_batch_to_tensor(processed),)


NODE_CLASS_MAPPINGS = {
    "DarkroomVignette": Vignette,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DarkroomVignette": "Vignette",
}
