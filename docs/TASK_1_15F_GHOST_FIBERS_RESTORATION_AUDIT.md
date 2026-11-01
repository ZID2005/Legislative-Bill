# TASK 1.15F — GHOST FIBERS RESTORATION & STRUCTURAL AUDIT

**Date:** November 1, 2026  
**Auditor:** Antigravity Agentic Engineer  
**Status:** COMPLETE & VERIFIED  
**Commitment Scope:** `frontend/components/onboarding/GhostFibers.tsx`, `frontend/components/onboarding/GhostFibersBackground.tsx`, `frontend/components/ui/feature-carousel.tsx`, `frontend/app/onboarding/page.tsx`, `frontend/app/globals.css`

---

## 1. Executive Summary

Task 1.15F resolves two structural and visual degradation issues in the Seance onboarding experience (`/onboarding`):
1. **Background Visual Degradation:** The previous implementation had drifted from the authoritative reference into a static, distorted ribbon/wireframe using 28 threads, connected quadrilateral polygons, and synthetic pseudo-gradients.
2. **Structural Box-in-a-Box Clutter:** The onboarding layout had accumulated up to six layers of nested bordered containers (`glass-shell` -> `p-[1px]` double border -> `glass-panel` -> column panels -> `FeatureCarousel` wrapper -> stage panel), resulting in visual tension, uneven radii, and inconsistent borders.

Both issues have been remediated. The authentic dot-based particle-fiber field (72 threads, 3 layers, `fiberStyle="dots"`, `#8b5cf6`/`#dfd1fc`/`#6f4ac5`) has been restored with interactive mouse focus, click pulse, and zero-allocation 60 FPS rendering. The layout has been unified into a single liquid-glass shell with standardized 24px/18px/12px/8px geometry.

---

## 2. Root Cause Analysis

### 2.1 Background Drift: Connected Polygon Ribbons vs. Dense Particle Dots
- **Previous Flaw (Task 1.15E):** The previous iteration modified `fiberStyle` from `"dots"` to `"ribbon"` and lowered thread count from 72 to 28. In ribbon mode, consecutive thread samples were joined into quad strip polygons (`ctx.lineTo()`, `ctx.fill()`). Because adjacent threads twist through differing mathematical 3D harmonic phases, these quad polygons folded in upon themselves, generating jagged, distorted diamond meshes that looked like a broken wireframe rather than the organic purple particle ribbons seen in the reference.
- **Remediation (Task 1.15F):** Restored the authoritative specification:
  - `threads={72}` (2.57x density increase)
  - `layers={3}` (depth stratification at $Z \in \{-80, 0, +80\}$)
  - `fiberStyle="dots"` (rendering dense particle discs instead of connected quad strips)
  - Off-screen high-resolution radial gradient sprites (primary `#dfd1fc`, secondary `#6f4ac5`, atmospheric bloom `#8b5cf6`, sparkle `#ffffff`) stamped via `ctx.drawImage` for GPU-accelerated blitting.
  - Zero-allocation render loop: drawing layer-by-layer without allocating intermediate point arrays or running `.sort()` in `requestAnimationFrame`.

### 2.2 Structural Geometry: Box-in-a-Box Nested Cards
- **Previous Flaw:** The onboarding dialog was constructed with nested card wrappers:
  1. Outer `glass-shell` container with 1px border.
  2. Nested `p-[1px]` wrapper generating a secondary hairline outline.
  3. Inner `glass-panel` container with a third border and mismatched inner corner radius.
  4. Left (5-col) and Right (7-col) children both rendered as separate `glass-panel` cards with individual 1px borders.
  5. Inside the right column, `FeatureCarousel` wrapped the visual in an additional `glass-shell` card with a 1px border.
  6. The visual stage inside `FeatureCarousel` had its own `glass-panel` border.
  *Total:* Up to 6 concentric borders with divergent radii (16px, 12px, 20px, 8px), resulting in a fragmented, cluttered "antiquated dashboard" appearance.
- **Remediation (Task 1.15F):**
  - Consolidated into a **single unified liquid-glass shell** (`rounded-3xl` / `24px` radius) with one hairline border (`border-white/10`) and continuous translucent charcoal backdrop blur (`backdrop-blur-2xl`).
  - Removed all `p-[1px]` double wrappers and superfluous outer frames.
  - Left configuration column and right showcase column are separated by a clean vertical hairline divider (`border-r border-white/[0.08]`), presenting as one integrated instrument.
  - Internal stage framed at `rounded-[18px]`, individual cards at `rounded-xl` (`12px`), and inputs/buttons at `rounded-lg` (`8px`).

---

## 3. Authoritative Architectural Matrix

| Metric / Attribute | Previous (Task 1.15E) | Restored (Task 1.15F) | Authoritative Reference Requirement |
| :--- | :--- | :--- | :--- |
| **Fiber Style** | `"ribbon"` (distorted quads) | `"dots"` (dense particle field) | `"dots"` |
| **Thread Count** | 28 threads | 72 threads | 72 threads |
| **Layers** | 2 layers | 3 layers | 3 layers |
| **Primary Color** | Synthetic linear gradient | `#dfd1fc` (luminous lavender) | `#dfd1fc` |
| **Secondary Color** | Mid violet | `#6f4ac5` (deep purple) | `#6f4ac5` |
| **Glow Color** | Neon magenta | `#8b5cf6` (atmospheric violet) | `#8b5cf6` |
| **Mouse Interaction** | Passive drift | Real localized 3D focus (`hoverEffect="focus"`) | Real localized 3D focus |
| **Click Pulse** | None | Radial shockwave ripple (`pulseOnClick`) | Pulse on click |
| **Introductory Unfurl** | Instant pop | Smooth parametric scale/alpha unfurl (`intro`) | Natural intro |
| **Motion Accessibility** | Hidden or unhandled | Static frozen frame (`prefers-reduced-motion`) | Static frozen frame |
| **Main Shell Radius** | Multi-tier (16px / 20px) | Single coherent 24px (`rounded-3xl`) | Standardized 22–26px |
| **Nested Border Layers** | 4 to 6 stacked outlines | 1 outer hairline border | 1 coherent border system |
| **Showcase Container** | Double-card wrapper | Single unified 18px stage | Coherent product experience |
| **State Prediction Firewall** | 0% (maintained) | 0.00% Statutory Firewall (maintained) | 0 quantitative predictions |
| **Baseline Manifest Hash** | `50ae76039bcc...` | `50ae76039bcc...` (Verified Exact) | Exact frozen SHA-256 |

---

## 4. Verification and Audit Confirmation

1. **Interactive Ghost Fibers Rendering:**
   - 72 threads across 3 depth layers produce fluid, non-intersecting particle waves with visible negative space behind the glass shell.
   - Pointer events set to `none` with `z-0`, ensuring zero interference with form inputs, steppers, or interactive buttons.
   - Mouse movement drives localized 3D coordinate elevation (`Math.exp(-dist / 320) * 44`), creating a tactile depth-of-field lens effect.
   - Clicking generates a decaying pulse ripple expanding across the 3D wave plane.
   - Full support for `prefers-reduced-motion: reduce`, rendering a static frame without background removal or animation timers.

2. **Liquid-Glass Structural Integrity:**
   - Single outer 24px shell with high-contrast typography (`text-white`, `text-zinc-300`, `text-zinc-400`).
   - Zero horizontal overflow across all viewports (1440x900 desktop, 768x1024 tablet, 375x812 mobile).
   - Stepper cleanly displays 8 numbered positions with direct navigation to completed stages.
   - Draft reset and localStorage rehydration operate reliably.

3. **Statutory and Baseline Safeguards:**
   - SHA-256 of `docs/production_baseline.json` remains frozen at `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`.
   - State legislation predictions strictly verified at 0 across all 44 state bills and 86 exposures.
   - 20 intelligence-only companies strictly quarantined from quantitative predictions.

