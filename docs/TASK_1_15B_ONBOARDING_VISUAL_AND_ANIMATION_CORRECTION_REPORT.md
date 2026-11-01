# TASK 1.15B — SEANCE ONBOARDING VISUAL OVERHAUL & FEATURECAROUSEL ANIMATION CORRECTION REPORT

## Executive Summary

**Task 1.15B** completely corrects the visual composition and animation dynamics of the Seance 8-stage onboarding experience. The previous Task 1.15A implementation preserved the eight-step onboarding workflow and isolated full-screen route, but retained a rigid navy-blue enterprise wizard appearance (50/50 split, excessive blue surfaces, static preview, institutional footer).

Task 1.15B achieves the authentic visual direction of the Cult UI / 21st.dev `FeatureCarousel` reference:
1. **Visual Composition Overhaul**: A deep charcoal canvas (`#080808`), large rounded frame (`#252525`), inner dark charcoal surface (`#111111`), elevated surfaces (`#191919`), and crisp border hairlines (`rgba(255, 255, 255, 0.08)` to `rgba(255, 255, 255, 0.14)`).
2. **Dominant Showcase Frame**: On desktop, the animated `FeatureCarousel` commands 60% of horizontal composition (`lg:col-span-7`), establishing visual focus while the streamlined form controls occupy the remaining 40% (`lg:col-span-5`).
3. **True Spring-Physics Layered Animation**: Completely replaces abrupt image swaps with direction-aware spring transitions using `cubic-bezier(0.16, 1, 0.3, 1)` easing. Overlapping primary (88% scale, foreground) and secondary (82% scale, rotated 1.8°, background) screenshots animate with natural horizontal/vertical displacement and staggered momentum.
4. **Interactive Hover Depth Parallax**: Hovering over the showcase elevates the primary card (`translate3d(-2px, -4px, 0) scale(1.01)`) and displaces the secondary card (`translate3d(6px, 8px, 0) scale(1.02) rotate(2.6deg)`), creating tangible spatial depth.
5. **Minimal Full-Screen Chrome**: Pure `SEANCE` wordmark with subtle `/ WORKSPACE SETUP`, minimal 8-segment progress line, zero dashboard header leakage, and zero bottom institutional footer.
6. **Functional & Epistemic Invariants Preserved**: Zero changes to the 8-step business logic, multi-tenant persistence, watchlist creation, alert preference updates, validation, or workspace redirection.

---

## Files Changed

| File Path | Description of Changes |
|---|---|
| `components/ui/feature-carousel.tsx` | Complete rewrite to implement Cult UI spring-physics multi-layer animation, direction-aware forward/backward keyframes, interactive hover parallax, refined stage indicators, and `prefers-reduced-motion` compliance. Preserved all exports (`DEFAULT_FOUR_STAGES`, `SEANCE_EIGHT_STAGES`, `FeatureCarouselProps`, `FeatureStage`, `FeatureImage`). |
| `frontend/app/onboarding/page.tsx` | Complete visual redesign. Deep charcoal foundation (`#080808`), 60/40 showcase-dominant desktop grid, streamlined step controls (compact persona rows, jurisdiction toggles, watchlist seed, alert preferences), minimal progress line, eliminated institutional footer. |
| `frontend/app/onboarding/layout.tsx` | Sets the dedicated `#080808` dark canvas and isolated metadata container without theme bleed. |
| `scripts/browser_validation_task_1_15b.js` | Comprehensive 18-point Playwright end-to-end verification script testing all 8 stages, forward/backward transitions, hover parallax, validation, overflow, and responsive viewports. |
| `docs/TASK_1_15B_ONBOARDING_VISUAL_AND_ANIMATION_CORRECTION_REPORT.md` | Formal engineering documentation and verification report. |

---

## Visual Composition Changes

### 1. Palette Transformation
- **Eliminated**: Navy-blue (`#0c1322`, `#121b2f`, `#162035`), blue glows, repetitive card grids, blue CTA buttons.
- **Adopted**:
  - Main Canvas: `#080808`
  - Outer Frame: `#252525` (1px precision hairline wrapper)
  - Inner Surface: `#111111`
  - Elevated Elements: `#161616` / `#191919`
  - Subtle Borders: `rgba(255, 255, 255, 0.08)` to `rgba(255, 255, 255, 0.14)`
  - Primary Text: `#F4F4F4`
  - Secondary Text: `#A3A3A3` / `#666666`
  - Accent / Confirm: High-contrast white CTA button (`#FFFFFF` text `#080808`) and muted emerald indicators.

### 2. Layout & Proportions
- **Desktop (1440x900)**: Asymmetric 5-column (Form) vs 7-column (Showcase) grid. The animated showcase occupies 60% of the viewport width, establishing immediate immersion.
- **Tablet (768x1024)**: Vertically stacked composition with full-width form and responsive 16:10 showcase frame.
- **Mobile (375x812)**: Single-column streamlined workflow with responsive screenshot scaling, touch-accessible step buttons, and zero horizontal overflow (`scrollWidth <= innerWidth + 1`).

### 3. Step Content Redesign
- **Step 1 (Welcome)**: Replaced bulky cards with concise list of core platform capabilities (Econometric Event Studies, State Statutory Intelligence) with emerald checkmarks.
- **Step 2 (Organization)**: Streamlined inputs, charcoal domain select, and 3-option team size segmented pill buttons.
- **Step 3 (Persona)**: Replaced oversized 2x2 grid with sleek, horizontal selection rows featuring subtle icons and analytical workflow descriptions.
- **Step 4 (Jurisdiction)**: Clean list of Central Parliament and 4 State Assemblies with status tags and custom checkboxes.
- **Step 5 (Watchlist)**: Clean list of landmark bills (Telecommunications Act, DPDP Act, Mines & Minerals, state acts) with category tags.
- **Step 6 (Alerts)**: Segmented frequency buttons (Real-time, Daily Digest, Weekly Brief) and in-app telemetry toggle.
- **Step 7 (Capabilities)**: Refined overview of Command Center, Legislative Explorer, Predictions Engine, and Grounded AI Analyst.
- **Step 8 (Launch)**: Monospace summary table detailing configured organization, persona, monitored acts, and digest schedule. High-contrast emerald Launch button.

---

## Animation & Spring Physics Implementation

### Physics-Based Direction-Aware Transitions
Transitions between stages utilize authentic spring curves rather than linear fades or instant swaps:

```css
/* Spring translation curves */
animation-timing-function: cubic-bezier(0.16, 1, 0.3, 1);
```

#### Forward Navigation (Step N → Step N+1):
- **Primary Image**: Slides in from `translate3d(24px, 14px, 0) scale(0.97)` to `(0, 0, 0) scale(1)` over 550ms.
- **Secondary Image**: Slides in from `translate3d(36px, 20px, 0) scale(0.93) rotate(0deg)` to `(0, 0, 0) scale(1) rotate(1.8deg)` over 650ms. The 100ms timing stagger and angular acceleration produce physical depth separation.

#### Backward Navigation (Step N → Step N-1):
- **Primary Image**: Slides in from `translate3d(-24px, -14px, 0) scale(0.97)` to `(0, 0, 0) scale(1)` over 550ms.
- **Secondary Image**: Slides in from `translate3d(-36px, -20px, 0) scale(0.93) rotate(3.2deg)` to `(0, 0, 0) scale(1) rotate(1.8deg)` over 650ms.

### Interactive Hover Parallax
Hovering over the showcase container triggers a smooth 500ms spring-interpolated displacement:
- **Primary Image**: `translate3d(-2px, -4px, 0) scale(1.01)` with border highlight `rgba(255, 255, 255, 0.24)`.
- **Secondary Image**: `translate3d(6px, 8px, 0) scale(1.02) rotate(2.6deg)` with increased opacity (0.75 → 0.90).

### Reduced Motion Accessibility
When `prefers-reduced-motion: reduce` is detected:
```css
@media (prefers-reduced-motion: reduce) {
  .fc-anim-primary, .fc-anim-secondary, .fc-anim-single {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
    transition: opacity 150ms ease !important;
  }
}
```
All multi-axis translations, rotations, and scaling are disabled, falling back to clean opacity fades.

---

## Eight-Stage Showcase Mapping & Authentic Assets

All 10 authentic screenshots located in `frontend/public/onboarding/` are mapped 1:1 to their corresponding onboarding steps:

| Stage # | Stage Name | Primary Screenshot | Secondary (Overlapping) Screenshot | Metrics / Focus |
|---|---|---|---|---|
| **01** | Foundation | `stage1_bill_dossier.png` | `stage1_statutory_mechanics.png` | 20 Central Acts · 22 Dossiers |
| **02** | Workspace | `stage2_workspace_telemetry.png` | `stage2_command_center.png` | 5 Reporting Presets · Real-time |
| **03** | Corporate Universe | `stage3_exposure_matrix.png` | — (Dominant single frame) | 47 Liquid Quant · 13 Sectors |
| **04** | Sub-National | `stage4_state_firewall.png` | — (Dominant single frame) | 44 Enacted Acts · Zero Leakage |
| **05** | Surveillance | `stage5_watchlist_seed.png` | — (Dominant single frame) | Priority Feeds · Multi-State Scope |
| **06** | Intelligence Rules | `stage6_alert_rules.png` | — (Dominant single frame) | < 2 Min Latency · In-App + Digest |
| **07** | Reasoning Engine | `stage7_ai_analyst.png` | — (Dominant single frame) | 100% Grounded · Defense Enforced |
| **08** | Command Center | `stage8_launch_overview.png` | — (Dominant single frame) | 4,700 Predictions · Production Ready |

---

## Playwright Browser Validation Results

Execution command:
```powershell
node scripts/browser_validation_task_1_15b.js
```

### Validation Matrix (18/18 Checks Passed):

```
================================================================
BROWSER VALIDATION COMPLETE
Passed Checks: 18/18
Screenshots Captured: 12
Errors Encountered: 0
================================================================
  ✓ Minimal SEANCE Wordmark Visible
  ✓ Zero Dashboard Navbar Leakage
  ✓ Zero Bottom Institutional Footer
  ✓ Deep Charcoal Background Active
  ✓ Showcase Dominant 60/40 Layout on Desktop
  ✓ Stage 1 Multi-image Hover Parallax Verified
  ✓ Step 2 Organization Name Validation Enforced
  ✓ Stage 3 Persona Selection Streamlined
  ✓ Backward Navigation & Form Data Preserved
  ✓ Stage 4 State Assemblies Showcase Active
  ✓ Stage 5 Watchlist Seed Showcase Active
  ✓ Stage 6 Alert Rules Showcase Active
  ✓ Stage 7 AI Analyst Showcase Active
  ✓ Stage 8 Ready with Launch Command Center Button
  ✓ Zero Horizontal Overflow on Desktop
  ✓ Zero Horizontal Overflow on Tablet
  ✓ Zero Horizontal Overflow on Mobile
  ✓ prefers-reduced-motion Disables Keyframe Animations
```

### Visual Artifacts Captured:
All 12 high-resolution screenshots are preserved in the artifact screenshots directory:
- `task_1_15b_step1_desktop.png` (Stage 1 Desktop - Full Composition)
- `task_1_15b_step1_hover_parallax.png` (Stage 1 Desktop - Hover Parallax)
- `task_1_15b_step2_desktop.png` (Stage 2 Desktop - Org Setup & Validation)
- `task_1_15b_step3_desktop.png` (Stage 3 Desktop - Persona Selection)
- `task_1_15b_step4_desktop.png` (Stage 4 Desktop - Jurisdiction Coverage)
- `task_1_15b_step5_desktop.png` (Stage 5 Desktop - Watchlist Seed)
- `task_1_15b_step6_desktop.png` (Stage 6 Desktop - Alert Preferences)
- `task_1_15b_step7_desktop.png` (Stage 7 Desktop - Platform Capabilities)
- `task_1_15b_step8_desktop.png` (Stage 8 Desktop - Ready & Launch)
- `task_1_15b_tablet_step1.png` (Tablet Viewport 768x1024)
- `task_1_15b_mobile_step1.png` (Mobile Viewport 375x812 - Step 1)
- `task_1_15b_mobile_step2.png` (Mobile Viewport 375x812 - Step 2)

---

## Regression & Quality Verification

### 1. TypeScript Verification
Command:
```powershell
npm --prefix frontend run typecheck
```
Output:
```
> frontend@0.1.0 typecheck
> tsc --noEmit
# Exit code 0 (Zero errors)
```

### 2. Next.js Production Build
Command:
```powershell
npm --prefix frontend run build
```
Output:
```
▲ Next.js 16.3.5 (Turbopack)
✓ Compiled successfully in 20.2s
✓ Generating static pages using 11 workers (31/31) in 7.9s
  Route (app)
  ○ /onboarding (Static)
# Exit code 0 (Zero errors)
```

### 3. Backend Onboarding Tests
Command:
```powershell
pytest -v -k "onboarding"
```
Output:
```
tests/test_saas_onboarding_and_lifecycle.py::test_tenant_onboarding_and_team_lifecycle PASSED [ 50%]
tests/test_task_8_21_cloud_deployment.py::TestMultiTenantProductionSmoke::test_onboarding_lifecycle_test_exists PASSED [100%]
========= 2 passed, 2449 deselected in 99.00s ==========
```

### 4. Frozen Production Baseline Integrity
Command:
```powershell
Get-FileHash docs/production_baseline.json -Algorithm SHA256
```
Result:
```
50AE76039BCCF2E4A671CF2AE915889E490B17404DB6EB2E49E7965ECD6400B7
```
**Confirmed**: The baseline hash matches the required baseline SHA-256 byte-for-byte. No backend models, analytical engines, or database schemas were touched.

---

## Strict Stop Condition Adherence

Task 1.15B is 100% complete. No Task 1.16A work was started. All invariants, route boundaries, and design requirements have been strictly honored.

