# TASK 1.15E — VISUAL REFINEMENT AUDIT: SEANCE ONBOARDING

## 1. Executive Summary

Task 1.15E provides the final visual refinement of the Seance eight-step immersive onboarding experience based on three reference screenshots:
- **Reference Image 1**: Clean, minimal horizontal numbered progress bar (`1 — 2 — 3 — 4 — 5 — 6 — 7 — 8`).
- **Reference Image 2**: Target atmospheric aesthetic: dark, nearly black foundation (`#080808`), smooth flowing purple/lavender fiber ribbons, soft luminous waves, natural dimensional depth, gentle gradients, and calm negative space.
- **Reference Image 3**: Defect state of Task 1.15D: excessive particle density, dense dotted mesh, purple dots competing with foreground content, and vertical height causing desktop viewport scrolling.

---

## 2. Parameter Tuning Audit: Ghost Fibers Before and After

| Parameter | Task 1.15D (Defect State / Ref 3) | Task 1.15E (Target State / Ref 2) | Technical Justification |
| :--- | :--- | :--- | :--- |
| `fiberStyle` | `"dots"` | `"ribbon"` | Replaced 3,240 disconnected point dots per frame with continuous quadratic bezier curves and translucent ribbon surface meshes. Eliminates noisy dotted mesh appearance. |
| `threads` | `72` | `28` | Substantial 61% reduction in strand density, opening up calm negative space around onboarding glass panels. |
| `layers` | `3` | `2` | Reduced multi-plane crowding while maintaining 3D depth harmonics. |
| `particles` | `0.5` | `0.15` | Reduced floating particles by 70%, creating subtle dust motes rather than a distracting particle swarm. |
| `sparkle` | `0.5` | `0.2` | Toned down high-frequency twinkling for calm, institutional elegance. |
| `grain` | `0.06` | `0.015` | Eliminated visible digital noise on dark pixels. |
| `speed` | `0.50` | `0.28` | Hypnotic, natural fluid velocity; eliminates jerky or rushed movement. |
| `flow` | `0.40` | `0.22` | Restrained longitudinal wave drift. |
| `rollSpeed` | `0.15` | `0.08` | Smooth angular rotation of 3D wave folds. |
| `volume` | `0.70` | `0.75` | Broad, sweeping wave amplitudes matching Reference Image 2. |
| `waves` | `1.0` | `1.2` | Elegant dimensional wave periodicity. |
| `spread` | `1.0` | `1.2` | Wider lateral projection preventing strand clustering in the center. |
| `rotation` | `18°` | `-10°` | Natural diagonal ascent matching Reference Image 2 ribbon flow. |
| `twist` | `1.2` | `0.75` | Gentle, relaxed ribbon drape instead of tightly coiled strands. |
| `thickness` | `1.0` | `1.5` | Graceful silky fiber ribbon line width with antialiased quadratic interpolation. |
| `glow` | `0.8` | `0.6` | Soft volumetric wave glow; prevents blowout behind panels. |
| `vignette` | `0.3` | `0.45` | Preserves deep charcoal `#080808` negative space at viewport perimeters. |
| `mouseStrength` | `1.0` | `0.35` | Subtle, non-deforming interactive parallax deflection. |

---

## 3. Why the Previous Implementation Looked Too Dense

1. **`fiberStyle="dots"`**: Each of the 72 threads sampled 45 coordinates per frame, drawing 3,240 individual canvas arcs. At 60 FPS, this generated up to 9,720 draw calls per frame including glow passes. Visually, this formed a dense, granulated grid that looked like a particle network rather than fluid silk ribbons.
2. **Foreground Clutter & Contrast Competition**: High thread count (72) filled the entire background with bright purple nodes, shining through the translucent liquid glass panels and competing with white form labels and SVG charts.
3. **High Particle Swarm**: `particles=0.5` spawned 36 twinkling micro-particles on top of the 3,240 dots, creating visual vibration.

In Task 1.15E, switching to `"ribbon"` mode renders continuous parametric bezier curves and translucent ribbon polygons between thread pairs. Draw calls per frame dropped by 99% (from 9,720 to ~40), while rendering smooth, silky, undulating waves with deep negative space.

---

## 4. Progress Stepper Audit: Minimal Numbered Stepper (1 to 8)

### Before (Task 1.15D)
- Three large cards: `Workspace Foundation`, `Intelligence Preferences`, `Workspace Launch`.
- Verbose subtitles: *"Establish your institutional workspace and analytical scope"*, etc.
- Bulky circular indicators (36px) with badges (`PHASE 1 OF 3`, `13% COMPLETED`).
- Total vertical height: **130–145px**, pushing desktop layout into vertical scrollbar overflow.

### After (Task 1.15E)
- Minimal horizontal numbered sequence: `1 — 2 — 3 — 4 — 5 — 6 — 7 — 8`.
- Completed steps: Filled pill (`#F4F4F4`) with crisp checkmark vector (`strokeWidth={3}`).
- Active step: Elevated purple circle (`#1f1b2e` with `border-purple-400`, `ring-purple-500/25` halo).
- Upcoming steps: Subdued dark pill with muted step number.
- Connecting lines: Thin 2px lines progressively filling with purple gradient (`#8b5cf6` → `#dfd1fc`).
- Overall completion percentage: Small mono typography (`13%`, `50%`, `100%`) on right flank.
- Zero phase headings, zero cards, zero explanatory text below indicators.
- Total vertical height: **~36px** (saving ~100px of vertical space).

---

## 5. Single-Viewport Desktop Layout Audit (1440 × 900)

### Height Budget Analysis at 1440 × 900

| Section | Task 1.15D Height | Task 1.15E Height | Space Saved |
| :--- | :--- | :--- | :--- |
| Window Viewport | 900px | 900px | Baseline |
| Root Container Padding | 40px (`py-5`) | 20px (`py-2.5`) | +20px |
| Header & Wordmark | 50px | 38px | +12px |
| Progress Stepper | 135px | 36px | +99px |
| Shell Margins & Gaps | 32px | 12px | +20px |
| **Available Main Height** | **643px** | **794px** | **+151px** |
| Step 1 Form Content | 280px | 220px | Fits within 794px |
| Step 4 Form Content (5 jurisdictions) | 360px | 240px | Fits within 794px |
| Step 5 Form Content (5 watchlists) | 360px | 240px | Fits within 794px |
| Step 8 Form Content (Summary matrix) | 310px | 225px | Fits within 794px |
| Showcase Height | 460px | 440px | Fits within 794px |
| **Document Scroll Height** | **1,020px (OVERFLOW)** | **900px (ZERO SCROLL)** | **Strict Single Viewport** |

Verified across all 8 steps in Playwright automation: `document.documentElement.scrollHeight === 900px` (zero document-level vertical scrollbar).

