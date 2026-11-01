# TASK 1.15A — Seance Immersive Full-Screen Onboarding Redesign Report

**Document**: `docs/TASK_1_15A_ONBOARDING_REDESIGN_REPORT.md`  
**Task ID**: TASK 1.15A  
**Module**: SaaS Onboarding Experience & Architectural Isolation  
**Route**: `/onboarding`  
**Status**: Verified & Production Ready  
**Canonical Baseline SHA-256**: `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`  

---

## 1. Executive Summary & Design Transformation

Task 1.15A completely overhauls the visual and interactive experience of Seance's eight-step onboarding workflow, transforming a conventional in-dashboard wizard into a **premium, immersive, full-screen product experience**.

### Primary Visual Foundations
- **Reference 1 Direction**:
  - Full-viewport dark charcoal/black baseline (`#070b12` background base, `#0c1322` card surface, `#121b2f` elevated containers).
  - Large rounded composition (`rounded-2xl` / `rounded-3xl`) with a subtle double-border frame (`p-[1px]` gradient from `white/15` via `white/5` to `white/10`) and deep natural shadows (`shadow-2xl shadow-black/80`).
  - Restrained institutional contrast without decorative AI-style rainbow gradients.
- **Reference 2 Direction**:
  - Clear, focused eight-step progress bar showing current step, total steps, percentage complete, and active step pill indicators.
- **Critical Isolation Invariant**:
  - Absolutely zero global dashboard chrome is visible on `/onboarding`. Global TopNavbar, collaboration toolbar, notification bell, header theme switcher, standard sidebar, dashboard footer, and breadcrumbs are completely suppressed.
  - The top-left corner exclusively renders the institutional **SEANCE** wordmark (`text-sm font-mono font-bold tracking-[0.2em]`).

---

## 2. Full-Screen Route Isolation Architecture

### 2.1 Shell Separation via `AppShell.tsx`
To prevent chrome leakage without fragile CSS selector hacks or runtime DOM mutations, a clean React architecture was implemented via `frontend/components/layout/AppShell.tsx`:
- Detects whether current pathname matches `/onboarding` or `/onboarding/*`.
- When on `/onboarding`:
  - Suppresses `<TopNavbar />` completely (does not render in DOM).
  - Eliminates the `pt-14` (56px) top navbar padding on `<main>`, granting 100% full viewport height to the onboarding experience.
- When on standard dashboard routes:
  - Renders standard `<TopNavbar />` with collaboration toolbar, notification bell, theme switcher, and padded `<main className="pt-14 ...">`.

### 2.2 Defensive Suppression in `TopNavbar.tsx`
In addition to shell-level isolation, `frontend/components/layout/TopNavbar.tsx` implements a defensive guard:
```tsx
export function TopNavbar() {
  const pathname = usePathname();
  const router = useRouter();

  // Task 1.15A: Suppress TopNavbar on /onboarding
  if (pathname === "/onboarding" || (typeof pathname === "string" && pathname.startsWith("/onboarding"))) {
    return null;
  }
  // ...
```
This ensures that even if `TopNavbar` were referenced anywhere on `/onboarding`, it immediately returns `null`, preventing collaboration toolbars, avatars, notification links, or command palette shortcuts from entering the accessibility tree or DOM.

### 2.3 Dedicated Route Encapsulation via `app/onboarding/layout.tsx`
`frontend/app/onboarding/layout.tsx` defines dedicated metadata and semantic layout scoping for the route:
- Document title: `"Workspace Setup · Seance"`.
- Semantic viewport flex layout without fixed header offsets.

---

## 3. FeatureCarousel Component & Eight-Stage Showcase

### 3.1 Data-Driven Configurable Architecture
The animation foundation was built in `frontend/components/ui/feature-carousel.tsx`:
- **Dual Compatibility**:
  - Exports `DEFAULT_FOUR_STAGES` matching the 4-stage legacy showcase API (Step 1: 2 images, Step 2: 2 images, Step 3: 1 image, Step 4: 1 image).
  - Exports `SEANCE_EIGHT_STAGES` for the full eight-stage Seance workflow.
- **Controlled & Uncontrolled Modes**:
  - In controlled mode (via `activeStep` prop), the carousel is driven directly by Seance's onboarding step (1..8).
  - In uncontrolled mode, internal state and `autoPlay` allow autonomous stage cycling.
- **Layered Screenshot Positioning**:
  - Stages with two images display a primary foreground screenshot in front (`z-10`, `w-[88%]`, `border-white/15`, `shadow-2xl shadow-black/90`) and an offset background screenshot (`w-[82%]`, `translate-x-5 translate-y-5`, `opacity-75`, elevating to `opacity-90` on hover).
  - Stages with one image display a focal screenshot with subtle perspective, crisp border highlights, and controlled zoom on hover.
- **Micro-Interactions & Spring Transitions**:
  - Smooth easing curves (`transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)]`).
  - Hover-elevation (`hover:-translate-y-1 hover:border-white/25`).
  - Active step indicator pills at bottom allowing one-click stage inspection.
- **Reduced-Motion Support**:
  - Full `motion-reduce:transform-none motion-reduce:transition-none` compliance.

---

## 4. Authentic Seance Visual Assets

All visual showcase assets were captured directly from the running Seance application using Playwright in dark theme and saved to `frontend/public/onboarding/`:

| Stage | Asset Path | Resolution / Size | Authentic Product Source |
|---|---|---|---|
| **Stage 1** | `/onboarding/stage1_bill_dossier.png` | 900×620 (22.2 KB) | Central Legislative Bill Dossier (`/bills/bill_01_telecom_2023`) |
| **Stage 1 (Layer 2)** | `/onboarding/stage1_statutory_mechanics.png` | 850×550 (19.8 KB) | Statutory Mechanics & Procedural Journey Diff |
| **Stage 2** | `/onboarding/stage2_workspace_telemetry.png` | 950×650 (70.6 KB) | Command Center Workspace (`/workspace`) |
| **Stage 2 (Layer 2)** | `/onboarding/stage2_command_center.png` | 880×560 (57.9 KB) | Workspace Telemetry & Activity Stream |
| **Stage 3** | `/onboarding/stage3_exposure_matrix.png` | 950×650 (80.2 KB) | Corporate Exposure Matrix (`/companies/INE002A01018`) |
| **Stage 4** | `/onboarding/stage4_state_firewall.png` | 950×650 (98.1 KB) | State Assemblies & Statutory Firewall (`/states`) |
| **Stage 5** | `/onboarding/stage5_watchlist_seed.png` | 950×650 (49.2 KB) | Priority Regulatory Watchlists (`/watchlists`) |
| **Stage 6** | `/onboarding/stage6_alert_rules.png` | 950×650 (40.4 KB) | Alert Rules & Notification Center (`/alerts`) |
| **Stage 7** | `/onboarding/stage7_ai_analyst.png` | 950×650 (52.0 KB) | Grounded AI Analyst Terminal (`/ai-analyst`) |
| **Stage 8** | `/onboarding/stage8_launch_overview.png` | 950×650 (74.5 KB) | Quantitative Predictions Terminal (`/predictions`) |

---

## 5. Eight-Step Onboarding Interaction & State Preservation

All eight original steps, form fields, validation logic, and backend API interactions are preserved with 100% fidelity:

1. **Step 1: Welcome & Platform Introduction**
   - Introduces the 20 Central Parliament Acts (22 scanned records), 44 State Enacted Acts, 47 quantitative securities, and 4,700 statistical predictions.
2. **Step 2: Organization Profile Setup**
   - Inputs: `orgName` (text), `industryFocus` (dropdown with 5 financial domains), `teamSize` (3-way toggle button).
   - Validation: blocks empty or <2 character firm names with a visible error banner.
3. **Step 3: Role & Persona Selection**
   - Interactive selection across 4 personas: *Equity Research Analyst*, *Regulatory Affairs Director*, *Portfolio Manager*, *General Counsel & Policy Head*.
4. **Step 4: Jurisdiction Coverage**
   - Multi-state toggles across *Central Parliament* and 4 state legislatures (*AP, KA, KL, TS*).
   - Validation: prevents proceeding with 0 jurisdictions.
5. **Step 5: Initial Watchlist Creation**
   - Landmark legislation selection (*Telecommunications Act*, *DPDP Act*, *Mines & Minerals*, *TS Electricity*, *KA Gig Workers*).
6. **Step 6: Alert Preferences & Digest Frequency**
   - 3-way toggle for digest schedule (*Real-time*, *Daily Digest*, *Weekly Brief*).
   - In-app notification toggle; outbound email marked `NOT_CONFIGURED` (requires SMTP).
7. **Step 7: Platform Capabilities Overview**
   - Overview cards for Command Center, Legislative Explorer, Predictions Engine, and Grounded AI Analyst.
8. **Step 8: Launch & Command Center Entry**
   - Summary of configured parameters.
   - Action: calls `watchlistsApi.createWatchlist(...)`, `watchlistsApi.addItem(...)`, and `alertsApi.updatePreferences(...)`.
   - Clears draft from `localStorage` and redirects to `/workspace`.

### Session Continuity
- State is automatically synced to `localStorage` under `seance_onboarding_draft`.
- On browser refresh or accidental navigation interruption, the session cleanly rehydrates without data loss.
- A "Reset Draft" button in the header bar allows resetting to factory defaults at any time.

---

## 6. Responsive & Dual-Theme Experience

- **Desktop (1440×900)**: Two-column layout with left form controls (7 cols) and right FeatureCarousel showcase (5 cols).
- **Tablet (768×1024)**: Proportional balanced layout with responsive screenshot scaling and zero horizontal overflow.
- **Mobile (375×812)**: Single-column stacked layout, institutional wordmark at top-left, 8-segment progress pills, step controls, and responsive showcase.
- **Themes**:
  - Dark Theme (Default): Rich near-black `#070b12` background, `#0c1322` cards, `#121b2f` elevated containers, white/10 borders.
  - Light Theme: Warm neutral off-white background, crisp dark foreground text, soft borders, zero hardcoded dark tints.
  - System Theme: Dynamically tracks OS preference without layout shift.

