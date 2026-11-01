# TASK 1.15D — SEANCE ONBOARDING VISUAL AUDIT & SURFACE ARCHITECTURE

## 1. Executive Summary

Task 1.15D executes the visual refinement of Seance's eight-stage immersive onboarding wizard. It unifies three core design evolutions into a singular, cohesive aesthetic:
1. **Full-Viewport Ghost Fibers Background**: An atmospheric charcoal foundation (`#080808`) layered with parametric purple/lavender fiber waves (`#8b5cf6`, `#dfd1fc`, `#6f4ac5`) projecting subtle dimensional depth behind all onboarding interfaces.
2. **Connected Three-Phase Progress Stepper**: Grouping the eight concrete institutional onboarding steps into three logical phases (`Workspace Foundation`, `Intelligence Preferences`, `Workspace Launch`), preserving full eight-step business logic while providing a minimal connected visual progression inspired by Reference 1.
3. **Liquid Glass Showcase Surfaces**: Upgrading showcase shells, panel enclosures, and interactive form elements into smoked liquid glass (`.glass-shell`, `.glass-panel`, `.glass-elevated`) featuring 20–28px backdrop blur, subtle rim reflections, and strictly opaque, high-contrast foreground text, SVG vector paths, and interactive controls.

The onboarding business logic, multi-tenant persistence, draft state rehydration, 8 native intelligence visualizations, and analytical firewalls remain completely intact.

---

## 2. Visual Component & Hierarchy Audit

| Component | Previous Treatment (Task 1.15C) | Refined Treatment (Task 1.15D) | Visual Purpose |
| :--- | :--- | :--- | :--- |
| **Viewport Background** | Solid `#080808` canvas with static ambient radial gradient | Dedicated full-viewport `GhostFibersBackground` with parametric 3D wave simulation | Atmospheric depth, institutional energy, continuous immersion behind all panels |
| **Progress Navigation** | 8-segment horizontal bar with discrete rounded pills | Connected 3-step progress indicator with filled checkmarks, outlined active rings, progressive connecting lines, and descriptive subtitles | Clear macroscopic momentum across Foundation, Preferences, and Launch phases |
| **Showcase Shell** | `#252525` outer border, `#111111` solid inner container | `.glass-shell` (`rgba(18, 18, 22, 0.48)`, `blur(28px)`, `saturate(145%)`, `border: 1px solid rgba(255, 255, 255, 0.13)`) | Floating dimensional smoked glass surface revealing subtle fiber motion beneath |
| **Setup Content Surface** | Solid `#111111` background | Translucent `.glass-panel` (`rgba(24, 24, 28, 0.42)`, `blur(20px)`) | High-contrast, glare-free readability for firm setup, persona, and watchlists |
| **Interactive Form Cards** | `#161616` solid cards | `.glass-elevated` (`rgba(35, 35, 42, 0.46)`, `blur(24px)`) | Soft depth hierarchy for selection buttons, checklist options, and summary blocks |
| **Showcase Stage Panels** | `#141414` / `#161616` solid cards | `.glass-panel` and `.glass-elevated` translucent cards | Allows purple fiber motion to subtly bleed behind charts, networks, and device mockups |
| **Mobile Mockup Showcase** | Apple iPhone 17 Pro Max with solid `#09090b` screen | Apple iPhone 17 Pro Max with `.glass-panel` translucent mobile app cards | Hardware realism paired with modern glass card semantics |

---

## 3. Ghost Fibers Background Architecture

The Ghost Fibers engine (`GhostFibers.tsx`) executes high-performance 2D/3D parametric curve calculations on an HTML5 canvas:

- **Mathematical Mechanics**:
  - 3 depth layers (`layers: 3`) with 72 threads (`threads: 72`).
  - Harmonic wave equation:
    $$\theta = u \cdot 2\pi \cdot \text{waves} + t \cdot \text{flow} + \phi_{\text{thread}} \cdot \text{twist}$$
  - 3D spatial displacement with 18° rotation matrix:
    $$X_{\text{rot}} = X_0 \cos(18^\circ) - Y_0 \sin(18^\circ)$$
    $$Y_{\text{rot}} = X_0 \sin(18^\circ) + Y_0 \cos(18^\circ)$$
  - Perspective projection:
    $$S = \frac{\text{fov}}{\text{fov} + Z + 250}$$
    $$X_{\text{screen}} = X_{\text{center}} + X_{\text{rot}} \cdot S \cdot \text{scale}$$
- **Color Matrix**:
  - Primary Line Color: `#dfd1fc` (Lavender)
  - Secondary Line Color: `#6f4ac5` (Deep Violet)
  - Glow Color: `#8b5cf6` (Electric Purple)
  - Gradient: Depth-based interpolation between foreground and background z-coordinates.
- **Atmospheric Isolation**:
  - Wrapper container: `fixed inset-0 w-full h-full pointer-events-none z-0 overflow-hidden`.
  - Non-blocking mouse interaction: Window listeners listen for mousemove and clicks passively, deflecting fiber nodes without intercepting clicks on buttons, inputs, links, or carousel dots.
  - Zero layout shifts or horizontal scrollbars.

---

## 4. Connected Stepper Phase Mapping & State Transitions

The eight actual onboarding steps are mapped into three macro-phases:

```
[Phase 1: Workspace Foundation] (Steps 1–3)
 ├── Step 1: Welcome & Platform Introduction
 ├── Step 2: Organization Profile Setup
 └── Step 3: Role & Persona Selection

[Phase 2: Intelligence Preferences] (Steps 4–7)
 ├── Step 4: Jurisdiction Coverage
 ├── Step 5: Initial Watchlist Creation
 ├── Step 6: Alert Preferences & Digest Frequency
 └── Step 7: Platform Capabilities Overview

[Phase 3: Workspace Launch] (Step 8)
 └── Step 8: Launch & Command Center Entry
```

### State Progression Matrix

| Step | Active Phase | Phase 1 State | Phase 2 State | Phase 3 State | Line 1-2 Fill | Line 2-3 Fill | Completed % |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Step 1** | Phase 1 | `active` | `upcoming` | `upcoming` | 33% | 0% | 13% |
| **Step 2** | Phase 1 | `active` | `upcoming` | `upcoming` | 66% | 0% | 25% |
| **Step 3** | Phase 1 | `active` | `upcoming` | `upcoming` | 100% | 0% | 38% |
| **Step 4** | Phase 2 | `completed` | `active` | `upcoming` | 100% | 25% | 50% |
| **Step 5** | Phase 2 | `completed` | `active` | `upcoming` | 100% | 50% | 63% |
| **Step 6** | Phase 2 | `completed` | `active` | `upcoming` | 100% | 75% | 75% |
| **Step 7** | Phase 2 | `completed` | `active` | `upcoming` | 100% | 100% | 88% |
| **Step 8** | Phase 3 | `completed` | `completed` | `completed` | 100% | 100% | 100% |

- **Step Jump Invariant**: Clicking on an earlier completed phase navigates directly to the earliest step of that phase (e.g. clicking Phase 1 from Step 5 returns to Step 1).
- **Validation Guard**: Forward phase jump requires satisfying step validation rules (e.g., valid organization name on Step 2, non-empty jurisdiction selection on Step 4).

---

## 5. Liquid Glass Tokens & Contrast Validation

The design tokens are codified in `frontend/app/globals.css`:

```css
.glass-shell {
  background: rgba(18, 18, 22, 0.48);
  backdrop-filter: blur(28px) saturate(145%);
  -webkit-backdrop-filter: blur(28px) saturate(145%);
  border: 1px solid rgba(255, 255, 255, 0.13);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.10),
    0 20px 60px rgba(0, 0, 0, 0.28);
}

.glass-panel {
  background: rgba(24, 24, 28, 0.42);
  backdrop-filter: blur(20px) saturate(135%);
  -webkit-backdrop-filter: blur(20px) saturate(135%);
  border: 1px solid rgba(255, 255, 255, 0.10);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 10px 30px rgba(0, 0, 0, 0.22);
}

.glass-elevated {
  background: rgba(35, 35, 42, 0.46);
  backdrop-filter: blur(24px) saturate(150%);
  -webkit-backdrop-filter: blur(24px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    0 14px 40px rgba(0, 0, 0, 0.32);
}
```

### Contrast & Readability Verification
- **Background Opacity**: Restricted to 42%–48% alpha on container panels, allowing backdrop blur to soften the purple fiber motion while eliminating visual noise.
- **Foreground Content**: Text colors (`#F4F4F4`, `#FFFFFF`, `#A3A3A3`), SVG stroke paths, form input values, and badges are styled with 100% opacity.
- **Accessibility Ratio**: Text-to-surface contrast exceeds 12.8:1 for `#F4F4F4` on `.glass-panel` over `#080808`, exceeding WCAG AAA requirements (7:1).
- **Reduced Motion Fallback**: When `prefers-reduced-motion: reduce` is active, the canvas loop is halted, rendering a static reference frame with zero CPU/GPU overhead.

