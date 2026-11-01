# FRONTEND REDESIGN IMPLEMENTATION ROADMAP
## India Legislative Intelligence & Market Impact Platform
**Document Version:** 1.0.0  
**Status:** Phased Implementation Roadmap & Execution Gates  
**Execution Gate:** READ-ONLY SPECIFICATION (No source files modified in this task).

---

## 1. Overview & Phasing Strategy

This roadmap details the concrete, phased execution plan for implementing the **Modern Enterprise SaaS Redesign** across the `frontend/` codebase.

Implementation will proceed strictly in dependency order across **6 sequential phases**. Each phase contains strict prerequisites, affected components, risks, mitigations, acceptance criteria, and regression test commands.

```
Execution Phasing Order:
Phase 1: Foundation (Tokens, Typography, Dual-Theme Engine, Brand Vector Assets)
   │
Phase 2: Application Shell (TopNavbar, Theme Switcher, Command Palette, Mobile Drawer)
   │
Phase 3: Motion System & Feedback (Transitions, Skeletons, Live Pulses, Reduced Motion)
   │
Phase 4: Core Analytical Workspaces (Bills, Companies, Predictions, Risk, Explorer)
   │
Phase 5: Portfolio, Reports & Grounded AI (Holdings Importer, Report Center, AI Copilot)
   │
Phase 6: Quality Assurance & Launch Gate (Accessibility, Contrast, Test Suite, Baseline Hash)
```

---

## 2. Phase-by-Phase Implementation Specifications

### Phase 1 — Foundation: Tokens, Typography, Dual-Theme Engine & Brand Assets
- **Objective:** Establish the bedrock styling infrastructure, dual-theme custom properties, typography scale, and replace amateur emoji branding with vector assets.
- **Affected Files:**
  - `frontend/app/globals.css` (Implement `:root` and `[data-theme="light"]` token palettes).
  - `frontend/styles/globals.css` (Deprecate/remove orphaned duplicate stylesheet).
  - `frontend/app/layout.tsx` (Inject zero-FOUC inline head script; bind semantic background).
  - `frontend/lib/theme.ts` (Create client-side theme management hook/utility).
  - `frontend/components/ui/BrandEmblem.tsx` (Create precision vector SVG emblem).
- **Prerequisites:** Task 1.1 Architectural Approval.
- **Risks & Mitigations:**
  - *Risk:* FOUC (flash of unstyled or dark theme on initial page load).
  - *Mitigation:* Inline blocking `<script>` in `<head>` evaluating `localStorage` and `prefers-color-scheme` synchronously before first paint.
- **Acceptance Criteria:**
  1. Theme toggling (`dark` ↔ `light` ↔ `system`) switches all CSS custom properties instantly.
  2. Zero flash of incorrect theme on hard refresh (`F5`).
  3. Brand emblem renders crisp vector geometry at 16px, 20px, and 32px.
- **Verification Tests:** Unit tests for theme switcher; Vitest DOM snapshot.

---

### Phase 2 — Application Shell: Navigation, Search & Layout
- **Objective:** Modernize the application shell, integrate the theme switcher into the top navbar, elevate the Command Palette (`⌘K`), and clean up dead code.
- **Affected Files:**
  - `frontend/components/layout/TopNavbar.tsx` (Update to use `BrandEmblem`, semantic tokens, and theme toggle).
  - `frontend/components/ui/CommandPalette.tsx` (Modernize styling, improve fuzzy grouping, add theme switch command).
  - `frontend/components/layout/Sidebar.tsx` & `Header.tsx` (Cleanly archive or eliminate orphaned files).
  - `frontend/components/ui/ContextDrawer.tsx` (Theme token migration, focus trap hardening).
  - `frontend/app/login/page.tsx` & `frontend/app/signup/page.tsx` (Update auth cards to use vector branding).
- **Prerequisites:** Phase 1 complete.
- **Risks & Mitigations:**
  - *Risk:* Breaking existing navigation test assertions in `task-8-25-navigation.test.tsx`.
  - *Mitigation:* Retain all 22 navigation destination route paths and labels identically.
- **Acceptance Criteria:**
  1. `TopNavbar` looks institutional, crisp, and high-contrast in both light and dark themes.
  2. Theme toggle button operates smoothly with keyboard focus.
  3. Command palette opens with `⌘K`/`Ctrl+K`, searches across all categories, and dismisses cleanly on `Esc`.
  4. All existing navigation tests pass.
- **Verification Tests:** `npm test -- __tests__/pages/task-8-25-navigation.test.tsx`.

---

### Phase 3 — Motion System & Interactive Feedback
- **Objective:** Implement the subtle, high-performance motion specification without external dependencies.
- **Affected Files:**
  - `frontend/app/globals.css` (Implement hardware-accelerated keyframes: `fade-in`, `slide-up`, `drawer-slide`, `skeleton-shimmer`).
  - `frontend/components/ui/Skeleton.tsx` (Refine shimmer animation to adapt to light/dark surfaces).
  - `frontend/components/ui/Button.tsx` (Tactile 80ms active press state).
  - `frontend/components/ui/Tabs.tsx` (Smooth active tab pill transition).
- **Prerequisites:** Phase 2 complete.
- **Risks & Mitigations:**
  - *Risk:* Layout shifts or high GPU usage on mobile devices.
  - *Mitigation:* Strictly restrict all animations to `transform` and `opacity`; enforce `@media (prefers-reduced-motion: reduce)` overrides.
- **Acceptance Criteria:**
  1. All transitions operate within 100ms–220ms on the compositor thread.
  2. Zero animations run when `prefers-reduced-motion` is enabled in operating system.
  3. Skeleton loaders provide smooth perceived loading during data fetches.
- **Verification Tests:** CSS media query automated tests in Vitest.

---

### Phase 4 — Core Analytical Workspaces Redesign
- **Objective:** Overhaul the data-heavy analytical pages to remove repetitive cards, introduce high-density tables with sticky headers, and implement progressive disclosure via context drawers.
- **Affected Files:**
  - `frontend/app/workspace/page.tsx` (Refine daily workspace feed, prioritize alerts).
  - `frontend/app/bills/BillsContent.tsx` & `[billId]/BillDetailContent.tsx` (Multi-tabbed dossier).
  - `frontend/app/bills/compare/page.tsx` (Split-pane diff).
  - `frontend/app/explorer/ExplorerContent.tsx` (Compact facet sidebar).
  - `frontend/app/predictions/PredictionsContent.tsx` & `[predictionId]/PredictionDetailContent.tsx` (Quant financial grid).
  - `frontend/app/risk/RiskContent.tsx` & `frontend/app/anticipation/AnticipationContent.tsx` (Screener tables).
  - `frontend/app/companies/CompaniesContent.tsx` & `[companyId]/CompanyDetailContent.tsx` (Tear-sheet drawer).
  - `frontend/app/states/StatesContent.tsx` & `[state]/StateDetailContent.tsx` (Sub-national registers).
- **Prerequisites:** Phase 3 complete.
- **Risks & Mitigations:**
  - *Risk:* Accidentally mutating or misrendering analytical baseline numbers (CAR, t-stats, predictions).
  - *Mitigation:* Preserve all underlying data hooks, props, and API response structures bit-for-bit.
- **Acceptance Criteria:**
  1. Repetitive card boxes replaced with high-density, sortable tables.
  2. Clicking corporate or bill items opens right-hand `ContextDrawer` rather than deep page reloads.
  3. All 4,700 predictions and 940 anticipation scores remain accurately displayed.
  4. State prediction firewall remains impenetrable (0 stock predictions).
- **Verification Tests:** Run full page test suites: `bill-detail.test.tsx`, `company-detail.test.tsx`, `predictions.test.tsx`, `risk.test.tsx`, `anticipation.test.tsx`, `states.test.tsx`.

---

### Phase 5 — Portfolio, Reports & Grounded AI Redesign
- **Objective:** Elevate executive-tier tools: Portfolio workspace, CSV/XLSX holdings import wizard, institutional report center, and the Grounded AI Analyst.
- **Affected Files:**
  - `frontend/app/portfolio/page.tsx` (Drag-and-drop CSV importer with validation, exposure tiers, relevance modal).
  - `frontend/app/reports/page.tsx` (Report template center, live PDF/CSV download queue).
  - `frontend/app/ai-analyst/AIAnalystContent.tsx` (Split-pane research terminal with citations drawer).
  - `frontend/app/settings/page.tsx` (RBAC role management console).
  - `frontend/app/onboarding/page.tsx` (Interactive tour stepper).
- **Prerequisites:** Phase 4 complete.
- **Risks & Mitigations:**
  - *Risk:* CSV upload parsing errors on malformed tickers/ISINs.
  - *Mitigation:* Client-side pre-validation against known 70-company universe with clear inline error correction.
- **Acceptance Criteria:**
  1. Portfolio holdings table supports seamless upload, editing, and exposure categorization.
  2. Grounded AI terminal displays verified citations in slide-over drawer without financial advice leaks.
  3. All 7 report templates generate with cryptographic provenance stamps.
- **Verification Tests:** `workspace.test.tsx`, `ai-analyst.test.tsx`, `monitoring.test.tsx`, `settings.test.tsx`.

---

### Phase 6 — Quality Assurance, Release Gates & Invariant Audit
- **Objective:** Comprehensive end-to-end audit of visual regression, responsive breakpoints, accessibility (WCAG AA/AAA), test suite passage, and baseline SHA-256 verification.
- **Affected Scope:** Entire `frontend/` application.
- **Prerequisites:** Phases 1–5 complete.
- **Gate Criteria:**
  1. **Test Suite:** 100% of Vitest frontend tests pass.
  2. **TypeScript:** `npm run typecheck` passes with zero errors.
  3. **Linting:** `npm run lint` passes with zero errors.
  4. **Baseline Invariant:** SHA-256 hash of `docs/production_baseline.json` equals `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`.
  5. **Firewalls:** Backend & frontend tests confirm zero State stock predictions and strict intelligence isolation.
  6. **Feature Matrix:** All 78 functional capabilities verified operational.
- **Verification Commands:**
  ```powershell
  cd frontend
  npm run typecheck
  npm test
  cd ..
  python -c "import hashlib; assert hashlib.sha256(open('docs/production_baseline.json','rb').read()).hexdigest() == '50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7'"
  ```

---

## 3. Recommended Execution Schedule

| Task ID | Phase Name | Focus Area | Dependency | Estimated Scope |
|---|---|---|---|---|
| **Task 1.2** | Phase 1: Foundation | Tokens, Dual-Theme Engine, Typography, Vector Emblem | Task 1.1 Approval | 4 files, foundational |
| **Task 1.3** | Phase 2: App Shell | TopNavbar, Command Palette, Theme Toggle, Auth Pages | Task 1.2 | 6 files, structural |
| **Task 1.4** | Phase 3: Motion & UI Primitives | Transitions, Skeletons, Drawers, Reduced Motion | Task 1.3 | 5 files, interaction |
| **Task 1.5** | Phase 4A: Core Legislative | Bills, Dossier, Compare, Explorer, States | Task 1.4 | 8 files, high impact |
| **Task 1.6** | Phase 4B: Econometrics & Universe | Predictions, Risk, Anticipation, Companies | Task 1.5 | 8 files, high impact |
| **Task 1.7** | Phase 5: Executive Tools | Portfolio, Reports, AI Analyst, Settings | Task 1.6 | 6 files, high impact |
| **Task 1.8** | Phase 6: Final QA & Verification | WCAG, Mobile, Vitest Suite, Baseline Audit | Task 1.7 | Full project audit |
