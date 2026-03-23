"""
Color film stock profiles for ComfyUI-Darkroom.

Each stock is defined by per-channel characteristic curve parameters,
saturation modifier, and shadow/highlight tinting.

Curve parameters: (toe_power, shoulder_power, slope, pivot_x, pivot_y)
- toe_power: >1 compresses shadows more (film's gentle shadow rolloff)
- shoulder_power: >1 gives softer highlight compression (film's hallmark)
- slope: midtone contrast multiplier
- pivot_x/pivot_y: typically 0.18 (18% grey, the photographic midpoint)

These are derived from published Kodak/Fuji technical data sheets and
refined against real film scan references.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CurveParams:
    toe_power: float
    shoulder_power: float
    slope: float
    pivot_x: float
    pivot_y: float


@dataclass(frozen=True)
class ColorFilmStock:
    name: str
    r_curve: CurveParams
    g_curve: CurveParams
    b_curve: CurveParams
    saturation: float
    shadow_tint: Tuple[float, float, float]
    highlight_tint: Tuple[float, float, float]
    description: str


# --- KODAK STOCKS ---

PORTRA_160 = ColorFilmStock(
    name="Kodak Portra 160",
    # Long toe, gentle shoulder. R channel lifted in shadows for warm skin.
    # Very low contrast — the flattest of the Portra family.
    r_curve=CurveParams(toe_power=1.3, shoulder_power=1.8, slope=0.92, pivot_x=0.18, pivot_y=0.20),
    g_curve=CurveParams(toe_power=1.4, shoulder_power=1.7, slope=0.90, pivot_x=0.18, pivot_y=0.18),
    b_curve=CurveParams(toe_power=1.5, shoulder_power=1.6, slope=0.88, pivot_x=0.18, pivot_y=0.16),
    saturation=0.88,
    shadow_tint=(0.015, 0.005, -0.01),
    highlight_tint=(0.01, 0.005, -0.005),
    description="Ultra-smooth portrait stock. Muted colors, warm skin tones, wide latitude."
)

PORTRA_400 = ColorFilmStock(
    name="Kodak Portra 400",
    # Slightly more contrast than 160. Classic Portra warmth.
    # Green channel slightly separated for skin-background differentiation.
    r_curve=CurveParams(toe_power=1.35, shoulder_power=1.7, slope=0.95, pivot_x=0.18, pivot_y=0.20),
    g_curve=CurveParams(toe_power=1.4, shoulder_power=1.65, slope=0.93, pivot_x=0.18, pivot_y=0.18),
    b_curve=CurveParams(toe_power=1.5, shoulder_power=1.55, slope=0.90, pivot_x=0.18, pivot_y=0.16),
    saturation=0.90,
    shadow_tint=(0.018, 0.006, -0.012),
    highlight_tint=(0.012, 0.006, -0.006),
    description="The workhorse portrait stock. Warm, forgiving, beautiful skin tones."
)

PORTRA_800 = ColorFilmStock(
    name="Kodak Portra 800",
    # Most contrast of the Portra family. Pushed shadows with green-cyan cast.
    r_curve=CurveParams(toe_power=1.25, shoulder_power=1.6, slope=1.0, pivot_x=0.18, pivot_y=0.20),
    g_curve=CurveParams(toe_power=1.3, shoulder_power=1.55, slope=0.98, pivot_x=0.18, pivot_y=0.19),
    b_curve=CurveParams(toe_power=1.35, shoulder_power=1.5, slope=0.95, pivot_x=0.18, pivot_y=0.17),
    saturation=0.92,
    shadow_tint=(0.01, 0.015, 0.008),
    highlight_tint=(0.015, 0.008, -0.005),
    description="High-speed Portra. More contrast, green-cyan shadow cast, gritty charm."
)

EKTAR_100 = ColorFilmStock(
    name="Kodak Ektar 100",
    # High saturation, punchy contrast. Strong S-curve.
    # Reds vivid, blues deep. The opposite of Portra.
    r_curve=CurveParams(toe_power=1.6, shoulder_power=1.4, slope=1.15, pivot_x=0.18, pivot_y=0.18),
    g_curve=CurveParams(toe_power=1.5, shoulder_power=1.45, slope=1.12, pivot_x=0.18, pivot_y=0.18),
    b_curve=CurveParams(toe_power=1.55, shoulder_power=1.5, slope=1.10, pivot_x=0.18, pivot_y=0.17),
    saturation=1.25,
    shadow_tint=(0.005, -0.005, -0.01),
    highlight_tint=(0.005, 0.0, -0.005),
    description="Vivid landscape stock. High saturation, punchy contrast, electric colors."
)

# --- FUJI STOCKS ---

PRO_400H = ColorFilmStock(
    name="Fuji Pro 400H",
    # Cool shadows (blue-green tint), pastel highlights. Lower saturation.
    # Green channel has a characteristic lift.
    r_curve=CurveParams(toe_power=1.35, shoulder_power=1.65, slope=0.93, pivot_x=0.18, pivot_y=0.18),
    g_curve=CurveParams(toe_power=1.3, shoulder_power=1.6, slope=0.95, pivot_x=0.18, pivot_y=0.19),
    b_curve=CurveParams(toe_power=1.25, shoulder_power=1.7, slope=0.92, pivot_x=0.18, pivot_y=0.19),
    saturation=0.85,
    shadow_tint=(-0.005, 0.01, 0.015),
    highlight_tint=(0.005, 0.01, 0.005),
    description="Cool pastel tones. Blue-green shadows, lifted greens. Wedding favorite."
)

VELVIA_50 = ColorFilmStock(
    name="Fuji Velvia 50",
    # Slide film: extreme saturation, deep blacks, high contrast.
    # Narrow latitude (steep curves). Blues go electric.
    r_curve=CurveParams(toe_power=1.8, shoulder_power=1.3, slope=1.25, pivot_x=0.18, pivot_y=0.17),
    g_curve=CurveParams(toe_power=1.7, shoulder_power=1.35, slope=1.22, pivot_x=0.18, pivot_y=0.17),
    b_curve=CurveParams(toe_power=1.6, shoulder_power=1.4, slope=1.20, pivot_x=0.18, pivot_y=0.18),
    saturation=1.45,
    shadow_tint=(0.005, -0.005, 0.01),
    highlight_tint=(0.01, 0.005, 0.0),
    description="Legendary slide film. Extreme saturation, deep blacks, electric blues."
)

# --- CINESTILL ---

CINESTILL_800T = ColorFilmStock(
    name="Cinestill 800T",
    # Tungsten-balanced (5500K correction needed for daylight).
    # Green cast in shadows, warm highlights. Halation handled separately.
    r_curve=CurveParams(toe_power=1.3, shoulder_power=1.5, slope=1.0, pivot_x=0.18, pivot_y=0.19),
    g_curve=CurveParams(toe_power=1.35, shoulder_power=1.55, slope=0.98, pivot_x=0.18, pivot_y=0.18),
    b_curve=CurveParams(toe_power=1.4, shoulder_power=1.6, slope=0.95, pivot_x=0.18, pivot_y=0.20),
    saturation=0.95,
    shadow_tint=(0.0, 0.012, 0.008),
    highlight_tint=(0.02, 0.01, -0.01),
    description="Cinema stock without remjet. Tungsten-balanced, warm highlights, green shadows. Pair with Halation node."
)

# --- KODAK VISION3 CINEMA STOCKS ---

VISION3_50D = ColorFilmStock(
    name="Kodak Vision3 50D",
    # Finest cinema stock. Very subtle, clean. Neutral with slight warm bias.
    # Daylight balanced. Extremely fine grain response.
    r_curve=CurveParams(toe_power=1.4, shoulder_power=1.7, slope=0.95, pivot_x=0.18, pivot_y=0.18),
    g_curve=CurveParams(toe_power=1.4, shoulder_power=1.7, slope=0.94, pivot_x=0.18, pivot_y=0.18),
    b_curve=CurveParams(toe_power=1.45, shoulder_power=1.65, slope=0.93, pivot_x=0.18, pivot_y=0.17),
    saturation=0.95,
    shadow_tint=(0.005, 0.0, -0.005),
    highlight_tint=(0.005, 0.003, 0.0),
    description="Pristine daylight cinema stock. Clean, neutral, wide latitude. The 'invisible' film."
)

VISION3_200T = ColorFilmStock(
    name="Kodak Vision3 200T",
    # Tungsten cinema stock. Blue shadows under daylight (no 85 filter).
    # With 85 filter: warm, clean. Moderate contrast.
    r_curve=CurveParams(toe_power=1.35, shoulder_power=1.65, slope=0.97, pivot_x=0.18, pivot_y=0.18),
    g_curve=CurveParams(toe_power=1.35, shoulder_power=1.6, slope=0.96, pivot_x=0.18, pivot_y=0.18),
    b_curve=CurveParams(toe_power=1.3, shoulder_power=1.7, slope=0.95, pivot_x=0.18, pivot_y=0.19),
    saturation=0.93,
    shadow_tint=(0.0, -0.003, 0.01),
    highlight_tint=(0.008, 0.005, -0.005),
    description="Tungsten cinema stock. Blue shadow cast under daylight, warm under tungsten."
)

VISION3_500T = ColorFilmStock(
    name="Kodak Vision3 500T",
    # Highest-speed cinema stock. More shadow noise, pushed blacks.
    # Cyan shadow cast. Higher toe power.
    r_curve=CurveParams(toe_power=1.25, shoulder_power=1.55, slope=1.02, pivot_x=0.18, pivot_y=0.19),
    g_curve=CurveParams(toe_power=1.3, shoulder_power=1.5, slope=1.0, pivot_x=0.18, pivot_y=0.18),
    b_curve=CurveParams(toe_power=1.2, shoulder_power=1.6, slope=0.98, pivot_x=0.18, pivot_y=0.20),
    saturation=0.94,
    shadow_tint=(-0.005, 0.008, 0.015),
    highlight_tint=(0.01, 0.005, -0.008),
    description="Fast cinema stock. Cyan shadow cast, gritty low-light character."
)

# --- REGISTRY ---

COLOR_STOCKS = {
    "Kodak Portra 160": PORTRA_160,
    "Kodak Portra 400": PORTRA_400,
    "Kodak Portra 800": PORTRA_800,
    "Kodak Ektar 100": EKTAR_100,
    "Fuji Pro 400H": PRO_400H,
    "Fuji Velvia 50": VELVIA_50,
    "Cinestill 800T": CINESTILL_800T,
    "Kodak Vision3 50D": VISION3_50D,
    "Kodak Vision3 200T": VISION3_200T,
    "Kodak Vision3 500T": VISION3_500T,
}

COLOR_STOCK_NAMES = list(COLOR_STOCKS.keys())
