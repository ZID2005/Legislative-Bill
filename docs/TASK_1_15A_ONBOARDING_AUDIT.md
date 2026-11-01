# TASK 1.15A — Seance Onboarding Audit & Architecture Specification

**Status**: Verified & Audited  
**Document**: `docs/TASK_1_15A_ONBOARDING_AUDIT.md`  
**Target Route**: `/onboarding`  
**Parent Shell**: `frontend/app/layout.tsx`  
**Underlying Component**: `frontend/app/onboarding/page.tsx`  
**Target Animation Foundation**: `@/components/ui/feature-carousel`  

---

## 1. Executive Summary

This document performs an exhaustive pre-implementation audit of Seance's eight-step onboarding workflow in accordance with **Task 1.15A Phase 1**.

The goal of Task 1.15A is to transform the existing wizard (which currently renders inside the standard application shell with the global dashboard navbar visible) into a **premium, immersive, full-screen product experience**. The design references mandate:
- A full-screen dark charcoal/black visual aesthetic (`#070b12` base, `#0c1322` / `#121b2f` surfaces) with a subtle layered/double outer frame and generous rounded corners.
- An eight-stage animated showcase powered by an extensible `FeatureCarousel` animation system with authentic Seance application screenshots.
- Complete isolation from the dashboard chrome (no global `TopNavbar`, no collaboration toolbar, no notification bell, no standard sidebar or dashboard breadcrumbs).
- Strict preservation of all 8 onboarding steps, data fields, validation rules, multi-tenant state persistence, and redirect behavior.

---

## 2. Global Shell & Layout Audit

### 2.1 Current Shell Architecture
In `frontend/app/layout.tsx`:
```tsx
<body className="bg-[var(--bg-base)] text-[var(--text-primary)] antialiased transition-colors duration-150">
  <ThemeProvider>
    {/* Fixed top navigation bar */}
    <TopNavbar />

    {/* Main content area — padded below navbar (56px) */}
    <main
      id="main-content"
      className="pt-14 min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)]"
      role="main"
      tabIndex={-1}
    >
      {children}
    </main>
  </ThemeProvider>
</body>
```

### 2.2 Shell Deficiencies Identified
1. **Chrome Leakage**: `TopNavbar` is currently rendered across all pages, including `/onboarding`. As a result, users entering onboarding see the global 4-hub navigation (`Legislation`, `Markets & Risk`, `Corporate Universe`, `Workspace`, `Portfolio`, `Reports`, `AI Analyst`), the live telemetry badge, the collaboration toolbar, the command palette trigger, and the dashboard theme switcher.
2. **Fixed Padding Conflict**: The `<main>` container hardcodes `pt-14` (56px) for the fixed top navbar, reducing the vertical viewport and breaking immersive full-screen presentation.
3. **Missing Isolation Guard**: Navigating back or interacting with dashboard controls from within onboarding allows users to bypass necessary tenant profile initialization.

### 2.3 Required Isolation Strategy (Phase 2)
- Introduce route awareness in the layout shell (`AppShell` or conditional chrome rendering in `app/layout.tsx`).
- When `pathname === "/onboarding"` or `pathname.startsWith("/onboarding")`:
  - `TopNavbar` is completely suppressed.
  - Collaboration toolbar, notification bell, and dashboard theme switcher are not rendered.
  - Top padding (`pt-14`) is removed so the onboarding viewport spans 100% of the screen height.
  - The dedicated onboarding frame renders its own institutional Seance wordmark in the top-left corner (`text-sm font-semibold tracking-wider font-mono text-slate-300`).

---

## 3. Audit of the Eight Existing Onboarding Steps

All eight steps are preserved with 100% fidelity. Below is the comprehensive step-by-step audit:

### Step 1: Welcome & Platform Introduction
- **Identifier**: `step === 1`
- **Header**: "Welcome to Seance" / "India's Legislative Intelligence Engine"
- **Context Copy**: Institutional workspace setup introducing access to:
  - 20 Central Parliament Acts (22 scanned records)
  - 44 State Enacted Acts (AP, KA, KL, TS)
  - 47 quantitative securities
  - 4,700 statistical econometric predictions
- **Informational Highlights**:
  1. *Econometric Event Studies*: Pre-computed historical market impact on 47 liquid NSE/BSE securities across 5 event horizons ($[-30,-1]$, $[-5,-1]$, $[0,0]$, $[+1,+5]$, $[+1,+30]$).
  2. *State Statutory Intelligence*: Comprehensive state acts with strict zero-stock-prediction firewall enforcement.
- **Form Controls**: None (Editorial overview).
- **Validation**: None required; proceed via "Continue →".
- **Visual Mapping**: Stage 1 of FeatureCarousel showcasing the Legislative Bill Dossier and Statutory Mechanics.

### Step 2: Organization Profile Setup
- **Identifier**: `step === 2`
- **Header**: "Organization Profile"
- **Description**: Configure organization defaults and reporting templates.
- **Form Controls**:
  - `orgName` (string): Text input. Default: `"My Organization"`.
  - `industryFocus` (string): Select dropdown with 5 financial/regulatory domains:
    - `"Institutional Equity Research"`
    - `"Macro Hedge Fund / Portfolio Strategy"`
    - `"Corporate Regulatory Affairs"`
    - `"Legal & Policy Advisory"`
    - `"Risk & Compliance Management"`
  - `teamSize` (string): Button toggle group with 3 options:
    - `"1-5"` analysts
    - `"5-20"` analysts
    - `"20+"` analysts
- **Validation Rules**: `orgName.trim().length >= 2`.
- **Visual Mapping**: Stage 2 of FeatureCarousel showcasing workspace configuration and portfolio risk telemetry.

### Step 3: Role & Persona Selection
- **Identifier**: `step === 3`
- **Header**: "Select Your Persona"
- **Description**: Tailors analytical priorities to the user's primary workflow.
- **Options** (4 interactive cards):
  1. `Equity Research Analyst`: Focus on stock return distributions, quantitative event studies, and sector beta.
  2. `Regulatory Affairs Director`: Focus on bill lifecycles, state gazette compliance, and corporate risk dossiers.
  3. `Portfolio Manager`: High-level risk matrix, anticipation trends, and multi-tenant custom watchlists.
  4. `General Counsel & Policy Head`: Statutory provisions, legal impact reports, and unpolluted state legislative records.
- **Form Controls**: `persona` (string). Default: `"Equity Research Analyst"`.
- **Validation Rules**: Exactly one persona must be selected.
- **Visual Mapping**: Stage 3 of FeatureCarousel showcasing the Corporate Exposure Matrix and Stock Distribution Terminal.

### Step 4: Jurisdiction & Domain Interests
- **Identifier**: `step === 4`
- **Header**: "Jurisdiction Coverage"
- **Description**: Select parliamentary and state assemblies to track in primary telemetry.
- **Options** (5 interactive items):
  1. `CENTRAL`: Central Parliament of India (20 Scanned Acts / 22 Records, Active Quant + Intel).
  2. `AP`: Andhra Pradesh Assembly (12 Acts Enacted, Active Statutory).
  3. `KA`: Karnataka Legislature (11 Acts Enacted, Active Statutory).
  4. `KL`: Kerala Assembly (11 Acts Enacted, Active Statutory).
  5. `TS`: Telangana Legislature (10 Acts Enacted, Active Statutory).
- **Form Controls**: `selectedJurisdictions` (`string[]`). Default: `["CENTRAL", "KA", "TS"]`.
- **Validation Rules**: At least 1 jurisdiction must remain selected (`selectedJurisdictions.length >= 1`).
- **Visual Mapping**: Stage 4 of FeatureCarousel showcasing State Statutory Intelligence and the Sub-National Firewall.

### Step 5: Initial Watchlist Creation
- **Identifier**: `step === 5`
- **Header**: "Create Starter Watchlist"
- **Description**: Seed the organization's priority regulatory watchlist with landmark statutes.
- **Options** (5 selectable acts):
  1. `bill_01_telecom_2023`: *Telecommunications Act 2023* (Central · Telecom & Satcom)
  2. `bill_02_dpdp_2023`: *Digital Personal Data Protection Act 2023* (Central · Tech & Information)
  3. `bill_04_mines_minerals_2023`: *Mines and Minerals Amendment 2023* (Central · Mining & Resources)
  4. `ts_act_2024_03`: *Telangana Electricity Regulation Act 2024* (State TS · Power & Utilities)
  5. `ka_act_2024_01`: *Karnataka Gig Workers Welfare Act 2024* (State KA · Labor & Platform)
- **Form Controls**: `selectedBills` (`string[]`). Default: `["bill_01_telecom_2023", "bill_02_dpdp_2023"]`.
- **Validation Rules**: Minimum 1 bill recommended (non-blocking if empty, but seeds watchlist if present).
- **Visual Mapping**: Stage 5 of FeatureCarousel showcasing Watchlist Telemetry and Real-Time Bill Tracking.

### Step 6: Alert Preferences & Digest Frequency
- **Identifier**: `step === 6`
- **Header**: "Notification & Digest Frequency"
- **Description**: Configure delivery triggers for legislative events affecting monitored securities.
- **Form Controls**:
  - `digestFrequency` (string): Toggle selector (`"REAL_TIME"`, `"DAILY"`, `"WEEKLY"`). Default: `"DAILY"`.
  - `inAppAlerts` (boolean): Checkbox for in-app bell & notification center. Default: `true`.
  - `emailAlerts` (boolean): Outbound email delivery. Marked `NOT_CONFIGURED` (disabled, requires SMTP).
- **Validation Rules**: `digestFrequency` must be one of the three valid options.
- **Visual Mapping**: Stage 6 of FeatureCarousel showcasing Notification Center and Rule Alerts.

### Step 7: Feature Walkthrough Preview
- **Identifier**: `step === 7`
- **Header**: "Platform Capabilities Overview"
- **Description**: Comprehensive overview of the 4 core surfaces ready for exploration:
  1. *Command Center (`/workspace`)*: Single-pane workspace showing watchlists, active alerts, and regulatory telemetry.
  2. *Legislative Explorer (`/explorer`)*: Faceted multi-state search across 66 acts, 70 corporations, and stages.
  3. *Predictions Engine (`/predictions`)*: 4,700 quantitative statistical predictions for Central acts on 47 listed securities.
  4. *Grounded AI Analyst (`/ai-analyst`)*: Questions grounded in statutory text and verified corporate exposure mappings.
- **Form Controls**: None (Review step).
- **Validation Rules**: None; proceed via "Continue →".
- **Visual Mapping**: Stage 7 of FeatureCarousel showcasing the Grounded AI Analyst Terminal and Multi-Faceted Explorer.

### Step 8: Launch & Command Center Entry
- **Identifier**: `step === 8`
- **Header**: "You're All Set!"
- **Description**: Final review and workspace provisioning summary.
- **Configuration Summary**:
  - Organization Name (`state.orgName`)
  - Selected Persona (`state.persona`)
  - Monitored Acts count (`state.selectedBills.length`)
  - Digest Frequency (`state.digestFrequency`)
- **Action Button**: "Launch Command Center 🏛" / "Initializing Workspace…"
- **Backend Persistence**:
  1. Calls `watchlistsApi.createWatchlist({ name: "Priority Regulatory Watchlist", description: "Curated during initial onboarding wizard" })`.
  2. Calls `watchlistsApi.addItem(watchlist_id, { entity_type: "bill", entity_id: billId, notes: "Added via Onboarding" })` for each selected bill.
  3. Calls `alertsApi.updatePreferences({ digest_frequency: state.digestFrequency, allowed_channels: state.inAppAlerts ? ["IN_APP"] : [] })`.
  4. Clears local onboarding draft cache.
  5. Redirects to `/workspace`.

---

## 4. State Persistence & Session Continuity Audit

### Existing Issue
Currently, `OnboardingPage` initializes state using React's in-memory `useState`. If a user refreshes the browser at Step 5, all previous inputs (`orgName`, `persona`, `selectedJurisdictions`) are reset to default values and the step resets to 1.

### Enhanced Persistence Architecture
We introduce `localStorage` persistence under key `seance_onboarding_draft`:
- Persists all fields and current step index.
- Automatically rehydrates on mount.
- Includes a subtle "Reset / Start Over" option if the user wishes to clear saved draft.
- Cleans up draft upon successful workspace creation in Step 8.

---

## 5. FeatureCarousel Architecture & 8-Stage Showcase

### Component Requirements
The supplied component specification calls for `@/components/ui/feature-carousel`.
The component supports:
- Data-driven `FeatureStage` definitions.
- Default 4-stage export for backward compatibility with standard demos.
- Dynamic 8-stage configuration for the Seance onboarding workflow.
- Smooth spring-based layered image animations (`--ease-editorial`, transform scale/rotation/translation).
- High-contrast charcoal frames with subtle double-border depth.
- Full respect for `prefers-reduced-motion`.

### Authentic Visual Asset Mapping (Phase 5)
Real application screenshots captured via Playwright from actual running Seance routes:
1. `onboarding/stage1_bill_dossier.png`: Central Bill Dossier (`/bills/bill_01_telecom_2023`).
2. `onboarding/stage1_statutory_mechanics.png`: Statutory Mechanics & Timeline.
3. `onboarding/stage2_workspace_telemetry.png`: Command Center Workspace (`/workspace`).
4. `onboarding/stage3_exposure_matrix.png`: Corporate Exposure Matrix (`/companies/INE002A01018`).
5. `onboarding/stage4_state_firewall.png`: State Assemblies & Firewall Guarantee (`/states`).
6. `onboarding/stage5_watchlist_seed.png`: Priority Regulatory Watchlist (`/watchlists`).
7. `onboarding/stage6_alert_rules.png`: Real-Time Alerts & Notification Center (`/alerts`).
8. `onboarding/stage7_ai_analyst.png`: Grounded AI Analyst Terminal (`/ai-analyst`).
9. `onboarding/stage8_launch_overview.png`: Institutional Command Center Overview (`/overview`).

---

## 6. Audit Conclusion & Implementation Plan

| Phase | Objective | Status |
|---|---|---|
| **Phase 1** | Exhaustive audit of routes, steps, state, validation, and APIs | **Complete** (This document) |
| **Phase 2** | Full-screen isolated layout without TopNavbar, footer, or dashboard chrome | Ready for execution |
| **Phase 3** | Charcoal editorial styling with subtle outer frame and restrained typography | Ready for execution |
| **Phase 4** | Build data-driven `FeatureCarousel` supporting 4 and 8 stages | Ready for execution |
| **Phase 5** | Capture authentic application screenshots via Playwright | Ready for execution |
| **Phase 6** | Wire 8-step wizard interactions, validation, and localStorage continuity | Ready for execution |
| **Phase 7** | Integrate layout balance, responsive views (Desktop, Tablet, Mobile) | Ready for execution |
| **Phase 8** | Verify Dark default with complete Light & System theme fidelity | Ready for execution |
| **Phase 9** | Spring animations, reduced-motion compliance | Ready for execution |
| **Phase 10** | Responsive validation across 1440px, 768px, 375px viewports | Ready for execution |
| **Phase 11** | Full accessibility (ARIA, keyboard navigation, focus trap prevention) | Ready for execution |
| **Phase 12** | Browser validation script `scripts/browser_validation_task_1_15a.js` | Ready for execution |
| **Phase 13** | Regression checks, typecheck, vitest (420+ tests), build, baseline hash | Ready for execution |

