from .film_stock_color import NODE_CLASS_MAPPINGS as FSC, NODE_DISPLAY_NAME_MAPPINGS as FSC_N
from .film_stock_bw import NODE_CLASS_MAPPINGS as FSB, NODE_DISPLAY_NAME_MAPPINGS as FSB_N
from .film_grain import NODE_CLASS_MAPPINGS as FG, NODE_DISPLAY_NAME_MAPPINGS as FG_N
from .halation import NODE_CLASS_MAPPINGS as HAL, NODE_DISPLAY_NAME_MAPPINGS as HAL_N
from .print_stock import NODE_CLASS_MAPPINGS as PS, NODE_DISPLAY_NAME_MAPPINGS as PS_N
from .cross_process import NODE_CLASS_MAPPINGS as CP, NODE_DISPLAY_NAME_MAPPINGS as CP_N
from .chromatic_aberration import NODE_CLASS_MAPPINGS as CA, NODE_DISPLAY_NAME_MAPPINGS as CA_N
from .vignette import NODE_CLASS_MAPPINGS as VIG, NODE_DISPLAY_NAME_MAPPINGS as VIG_N
from .lens_distortion import NODE_CLASS_MAPPINGS as LD, NODE_DISPLAY_NAME_MAPPINGS as LD_N
from .perspective_correct import NODE_CLASS_MAPPINGS as PC, NODE_DISPLAY_NAME_MAPPINGS as PC_N
from .lens_profile import NODE_CLASS_MAPPINGS as LP, NODE_DISPLAY_NAME_MAPPINGS as LP_N
from .white_balance import NODE_CLASS_MAPPINGS as WB, NODE_DISPLAY_NAME_MAPPINGS as WB_N
from .exposure_tone import NODE_CLASS_MAPPINGS as ET, NODE_DISPLAY_NAME_MAPPINGS as ET_N
from .hsl_selective import NODE_CLASS_MAPPINGS as HSL, NODE_DISPLAY_NAME_MAPPINGS as HSL_N
from .clarity_texture_dehaze import NODE_CLASS_MAPPINGS as CTD, NODE_DISPLAY_NAME_MAPPINGS as CTD_N
from .vibrance import NODE_CLASS_MAPPINGS as VIB, NODE_DISPLAY_NAME_MAPPINGS as VIB_N
from .sharpening_pro import NODE_CLASS_MAPPINGS as SP, NODE_DISPLAY_NAME_MAPPINGS as SP_N

NODE_CLASS_MAPPINGS = {**FSC, **FSB, **FG, **HAL, **PS, **CP, **CA, **VIG, **LD, **PC, **LP, **WB, **ET, **HSL, **CTD, **VIB, **SP}
NODE_DISPLAY_NAME_MAPPINGS = {**FSC_N, **FSB_N, **FG_N, **HAL_N, **PS_N, **CP_N, **CA_N, **VIG_N, **LD_N, **PC_N, **LP_N, **WB_N, **ET_N, **HSL_N, **CTD_N, **VIB_N, **SP_N}
