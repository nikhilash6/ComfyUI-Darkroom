"""
Black & white film stock profiles for ComfyUI-Darkroom.

Spectral sensitivity coefficients derived from darktable's published film data,
corrected for D50 illuminant. These represent how each B&W emulsion responds
to different wavelengths — NOT the naive luminosity formula.

Color filter data represents real Wratten-equivalent filter transmissions.
"""

from dataclasses import dataclass
from typing import Tuple

from .color_stocks import CurveParams


@dataclass(frozen=True)
class BWFilmStock:
    name: str
    red_weight: float
    green_weight: float
    blue_weight: float
    contrast_curve: CurveParams  # Single-channel curve applied after conversion
    base_fog: float              # Minimum density (lifts black point). 0.0 = pure black
    description: str


# --- ILFORD STOCKS ---

HP5_PLUS = BWFilmStock(
    name="Ilford HP5+",
    red_weight=0.253, green_weight=0.260, blue_weight=0.487,
    contrast_curve=CurveParams(toe_power=1.4, shoulder_power=1.5, slope=1.0, pivot_x=0.18, pivot_y=0.18),
    base_fog=0.02,
    description="Classic all-rounder. Medium contrast, versatile, pushable. The workhorse."
)

DELTA_100 = BWFilmStock(
    name="Ilford Delta 100",
    red_weight=0.246, green_weight=0.254, blue_weight=0.501,
    contrast_curve=CurveParams(toe_power=1.5, shoulder_power=1.6, slope=1.05, pivot_x=0.18, pivot_y=0.18),
    base_fog=0.01,
    description="Tabular grain, extremely fine. Smooth gradations, moderate contrast."
)

DELTA_400 = BWFilmStock(
    name="Ilford Delta 400",
    red_weight=0.244, green_weight=0.236, blue_weight=0.520,
    contrast_curve=CurveParams(toe_power=1.4, shoulder_power=1.5, slope=1.02, pivot_x=0.18, pivot_y=0.18),
    base_fog=0.015,
    description="Tabular grain, medium speed. Good all-round stock."
)

DELTA_3200 = BWFilmStock(
    name="Ilford Delta 3200",
    red_weight=0.244, green_weight=0.236, blue_weight=0.520,
    contrast_curve=CurveParams(toe_power=1.3, shoulder_power=1.4, slope=1.05, pivot_x=0.18, pivot_y=0.19),
    base_fog=0.025,
    description="Ultra-high speed. Visible grain, moody character. Push to 6400+."
)

FP4_PLUS = BWFilmStock(
    name="Ilford FP4+",
    red_weight=0.241, green_weight=0.221, blue_weight=0.537,
    contrast_curve=CurveParams(toe_power=1.5, shoulder_power=1.6, slope=1.08, pivot_x=0.18, pivot_y=0.18),
    base_fog=0.01,
    description="Fine grain, lower speed. Beautiful tonal rendering. Studio favorite."
)

ORTHO_PLUS = BWFilmStock(
    name="Ilford Ortho Plus",
    # Orthochromatic: ZERO red sensitivity. Only sees blue and green.
    # Red objects go very dark. Skin blemishes enhanced.
    red_weight=0.0, green_weight=0.50, blue_weight=0.50,
    contrast_curve=CurveParams(toe_power=1.6, shoulder_power=1.4, slope=1.10, pivot_x=0.18, pivot_y=0.17),
    base_fog=0.01,
    description="Orthochromatic: blind to red. Dramatic skin, dark lips, ethereal skies."
)

# --- KODAK ---

TRI_X_400 = BWFilmStock(
    name="Kodak Tri-X 400",
    # Tri-X has slightly more red sensitivity than Ilford stocks
    red_weight=0.30, green_weight=0.28, blue_weight=0.42,
    contrast_curve=CurveParams(toe_power=1.3, shoulder_power=1.4, slope=1.12, pivot_x=0.18, pivot_y=0.18),
    base_fog=0.02,
    description="Legendary. High contrast, punchy midtones, gritty character. Street photography icon."
)

# --- FUJI ---

ACROS_100 = BWFilmStock(
    name="Fuji Acros 100",
    red_weight=0.21, green_weight=0.32, blue_weight=0.47,
    contrast_curve=CurveParams(toe_power=1.5, shoulder_power=1.55, slope=1.05, pivot_x=0.18, pivot_y=0.18),
    base_fog=0.01,
    description="Extremely fine grain. Superb reciprocity characteristics. Clean, precise."
)


# --- COLOR FILTER SIMULATIONS ---
# Real Wratten-equivalent filter transmissions (R, G, B multipliers)
# Applied before B&W conversion to control tonal relationships

COLOR_FILTERS = {
    "None": (1.0, 1.0, 1.0),
    "Red (25A)": (1.8, 0.4, 0.1),     # Darkens sky dramatically, lightens skin
    "Orange (21)": (1.5, 0.6, 0.2),    # Moderate sky darkening, good skin tones
    "Yellow (8)": (1.2, 0.8, 0.3),     # Slight sky darkening, natural look
    "Green (11)": (0.3, 1.4, 0.4),     # Lightens foliage, darkens skin
    "Blue (47)": (0.2, 0.4, 1.5),      # Lightens sky, darkens warm tones
}


# --- REGISTRY ---

BW_STOCKS = {
    "Ilford HP5+": HP5_PLUS,
    "Kodak Tri-X 400": TRI_X_400,
    "Ilford Delta 100": DELTA_100,
    "Ilford Delta 400": DELTA_400,
    "Ilford Delta 3200": DELTA_3200,
    "Ilford FP4+": FP4_PLUS,
    "Fuji Acros 100": ACROS_100,
    "Ilford Ortho Plus": ORTHO_PLUS,
}

BW_STOCK_NAMES = list(BW_STOCKS.keys())
FILTER_NAMES = list(COLOR_FILTERS.keys())
