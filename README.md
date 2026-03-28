# ComfyUI-Darkroom

Professional color grading and film emulation suite for ComfyUI — 29 nodes, 161 film stocks, 102 lens profiles, zero API costs.

The most complete color toolset in the ComfyUI ecosystem. From physics-based film emulation to DaVinci Resolve-level color grading, Camera Raw processing, and optical simulation — everything runs locally with no external dependencies.

## Nodes

### Film Emulation (6 nodes)

| Node | Description |
|------|-------------|
| **Film Stock (Color)** | 111 color film stocks with per-channel H&D characteristic curves. Kodak Portra, Ektar, Fuji Velvia, Cinestill, Polaroid, and more. Capture One curve data integration. |
| **Film Stock (B&W)** | 50 B&W stocks with real spectral sensitivity coefficients. Ilford HP5+, Kodak Tri-X, T-MAX, with pushed variants. |
| **Film Grain** | Multi-octave luminance-dependent grain. ISO-scaled, resolution-aware, blue-channel emphasis like real film. |
| **Halation** | Physics-based light bounce from film base. Screen-blended highlight glow with disk blur. |
| **Print Stock** | Photographic paper simulation — the negative-to-print chain. |
| **Cross Process** | E-6 in C-41 and C-41 in E-6 cross-processing color shifts. |

### Camera Raw Tools (9 nodes)

| Node | Description |
|------|-------------|
| **White Balance** | Color temperature (Kelvin) and tint adjustment via Planckian locus approximation. |
| **Exposure & Tone** | EV-stop exposure, S-curve contrast, parametric shadows/highlights/whites/blacks. |
| **HSL Selective** | Per-hue adjustments to hue, saturation, and luminance across 8 color bands with smooth feathering. |
| **Clarity / Texture / Dehaze** | Local contrast enhancement, surface texture detail, and atmospheric haze removal. |
| **Vibrance** | Intelligent saturation with skin tone protection — boosts muted colors, protects already-saturated areas. |
| **Sharpening Pro** | Advanced unsharp mask with edge-aware masking and radius/amount/threshold control. |
| **Noise Reduction** | Multi-pass guided filter with 7 presets — from light denoise to heavy smoothing. |
| **Skin Tone Uniformity** | Mask-weighted mean pull for even skin tones. 6 skin type presets. Preserves texture. |
| **Color Qualifier** | Color range analysis and isolation with 19 action presets combining selection + correction. |

### Color Grading (9 nodes)

| Node | Description |
|------|-------------|
| **Tone Curve** | 5-point cubic spline per channel (PchipInterpolator — monotonic, no overshoot). 11 presets: S-curves, Faded Blacks, Matte Film, Cross-over pushes. |
| **Lift Gamma Gain** | DaVinci Resolve primary corrector. Per-channel R/G/B + Master for Lift, Gamma, Gain, and Offset — 16 precision sliders. |
| **Log Wheels** | Resolve Log-mode grading. Soft Gaussian zone masks in log2-encoded luminance space. Hue angle + saturation + density per zone. 7 presets. |
| **3-Way Color Balance** | Preset-first creative color tinting. Shadow/midtone/highlight zones with hue + intensity. 15 looks — Orange & Teal, Vintage Warm, Moonlight Blue, Bleach Bypass, and more. |
| **Hue vs Hue** | Remap specific hue ranges to different hues. 8 bands with feathering. 9 presets — skin tone correction, sky shifts, autumn warmth. |
| **Hue vs Sat** | Adjust saturation per hue range. 8 bands. 8 presets — pop blues, mute greens, teal & orange pop. |
| **Lum vs Sat** | Adjust saturation based on luminance. 5 zones. 7 presets — film look (desat highlights), punch midtones, bleach bypass. |
| **Sat vs Sat** | Adjust saturation based on existing saturation level. Compress oversaturated areas, boost muted tones. 4 zones, 6 presets. |
| **Color Warper** | 2D hue + saturation region warping with multi-region presets. 9 presets — Orange & Teal push, skin cleanup, sunset enhance. Manual mode for single-region custom work. |

### Lens & Optics (5 nodes)

| Node | Description |
|------|-------------|
| **Chromatic Aberration** | Lateral CA simulation/correction with per-channel shift. |
| **Vignette** | Optical vignette with shape, midpoint, and falloff control. |
| **Lens Distortion** | Brown-Conrady barrel/pincushion distortion model. |
| **Perspective Correct** | Keystone and trapezoid correction for architectural shots. |
| **Lens Profile** | All-in-one lens correction — distortion + CA + vignette from 102 real lens models (Canon, Nikon, Sony, Zeiss, Leica, vintage). |

## Installation

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/jeremieLouvaert/ComfyUI-Darkroom.git
pip install -r ComfyUI-Darkroom/requirements.txt
```

Restart ComfyUI. All 29 nodes appear under **AKURATE/Darkroom/** with subcategories: Film, Raw, Grading, Lens.

### Dependencies

- **scipy** (>= 1.10.0) — spline interpolation, Gaussian filters, FFT convolution
- **opensimplex** (>= 0.4) — high-quality simplex noise for film grain

No API keys. No GPU required. Pure numpy/scipy computation.

## Architecture

All processing happens in **linear light** (sRGB gamma removed before processing, reapplied after). Every node supports:

- **Strength slider** (0-1) — non-destructive blending with original
- **Batch processing** — handles ComfyUI's multi-image batches
- **Preset + override** — presets provide instant results, sliders fine-tune

Film stock data sourced from Capture One Film Styles (586 .costyle files parsed) and published Kodak/Fuji/Ilford technical data sheets. Lens profiles measured from real optical characteristics.

## License

MIT

## Author

Jeremie Louvaert — [jeremielouvaert.com](https://jeremielouvaert.com)
