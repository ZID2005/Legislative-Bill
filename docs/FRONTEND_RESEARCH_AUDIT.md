# FRONTEND RESEARCH & ARCHITECTURE AUDIT
## Legislative Bill Impact Prediction & Decision Intelligence Platform
**Document Version:** 1.0.0  
**Audit Date:** October 2026  
**Scope:** Complete repository inspection of `frontend/`, layout systems, styling architecture, component library, routing tree, test suites, and design diagnostics.  
**Execution Mode:** READ-ONLY AUDIT (Zero application code modified, zero dependencies installed).

---

## 1. Executive Summary & Audit Methodology

This document establishes the authoritative technical and visual audit of the existing Next.js frontend for the **Indian Parliamentary Intelligence & Market Impact Platform** (`frontend/`). 

### 1.1 Methodology
The audit was conducted via direct codebase inspection, AST inspection of App Router hierarchies, dependency graphing, CSS token extraction, and route traversal. Every assertion in this document is backed by concrete file paths and code artifacts.

- **Total App Routes Audited:** 35 active App Router pages (`page.tsx`).
- **Total Audited Functional Capabilities:** 78 distinct capabilities (CAP-1 through CAP-78).
- **Core Design Problem:** The interface exhibits classic "AI-generated boilerplate" traits—monolithic dark mode with hardcoded color values (`#05090f`, `bg-slate-950`), uncalibrated glowing effects (`.glow-blue`, `.glow-emerald`), gradient text headers (`.gradient-text`), repetitive card layouts, unicode emojis used as system icons (`⚖`, `📜`, `📈`), and lack of progressive disclosure on analytical screens.
- **Analytical Baseline Status:** Verified frozen and untouched (SHA-256: `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`).

---

## 2. Core Frontend Architecture & Dependency Audit

### 2.1 Package Manifest (`frontend/package.json`)
The application is built on cutting-edge Next.js and React primitives:

| Dependency | Installed Version | Architectural Role | Observations & Risks |
|---|---|---|---|
| `next` | `16.3.5` | Framework / App Router | Next.js 16 App Router with React Server Components (RSC) and Client Components (`"use client"`). |
| `react` | `19.2.8` | UI Library | React 19 canary/GA. Strict hook lifecycles, asynchronous transitions, action hooks. Third-party UI libraries must be verified for React 19 compatibility. |
| `react-dom` | `19.2.8` | DOM Renderer | React 19 DOM bindings. |
| `tailwindcss` | `^4.0.0` | CSS Framework | **Tailwind CSS v4** engine. Uses CSS-first `@import "tailwindcss";` instead of `tailwind.config.js`. |
| `@tailwindcss/postcss` | `^4.0.0` | PostCSS Plugin | Tailwind v4 compilation pipeline. |
| `clsx` | `^2.1.1` | Class Composition | Utility for conditional class string concatenation. |
| `tailwind-merge` | `^3.7.0` | Conflict Resolution | Merges conflicting Tailwind utilities (used in `cn()` in `frontend/lib/utils.ts`). |
| `vitest` | `^5.0.1` | Test Runner | Fast Vite-native unit and component test runner. |
| `@testing-library/react` | `^16.3.3` | Test Utilities | Component testing under React 19. |
| `typescript` | `^5.0.0` | Type Safety | Strict TypeScript configuration (`tsconfig.json`). |

#### Crucial Dependency Observations
1. **No External Animation Libraries Installed:** Neither `framer-motion` nor `motion` is currently installed. All existing animations are CSS keyframes defined in `frontend/app/globals.css`.
2. **No Icon Library Installed:** Neither `lucide-react`, `heroicons`, nor `radix-icons` is installed. The UI currently relies on raw unicode emoji characters (`⚖`, `📜`, `📈`, `🏢`, `🔍`, `✦`) or inline SVG strings.
3. **No Component Primitive Library Installed:** Neither Radix UI, Headless UI, nor React Aria is installed. All drawers, dialogs, and popovers are custom-built in `components/ui/`.
4. **No Theme Provider Installed:** `next-themes` is not present. The entire application is permanently hardcoded in dark mode.

---

## 3. Layout Hierarchy & Shell Architecture

### 3.1 Root Layout (`frontend/app/layout.tsx`)
The root layout establishes the top-level shell:
- **Font Integration:** Google Fonts `Inter` loaded via `next/font/google` (`variable: "--font-inter"`).
- **Hardcoded Dark Theme:**
  ```tsx
  // frontend/app/layout.tsx:54
  <body className="bg-[#05090f] text-slate-200 antialiased">
    <TopNavbar />
    <main id="main-content" className="pt-14 min-h-screen bg-[#05090f]" role="main" tabIndex={-1}>
      {children}
    </main>
  </body>
  ```
  The body and main tags hardcode hex `#05090f` directly into class strings, bypassing semantic CSS variables and preventing theme toggling.
- **TopNavbar Mount:** `TopNavbar` is mounted globally. It has a fixed height of `56px` (`h-14`), with `main` offset via `pt-14`.

### 3.2 Active Navigation System (`frontend/components/layout/TopNavbar.tsx`)
`TopNavbar.tsx` (769 lines, 31.4 kB) was deployed in Task 8.25/8.31C to replace the legacy left sidebar. It organizes the platform into 5 macro-workspace dropdowns:
1. **Workspace:** Direct link to `/workspace`
2. **Legislation:** Dropdown linking to `/bills`, `/explorer`, `/states`, `/latest-bills`, `/upcoming-legislation`, `/live-discovery`, `/bills/compare`, `/overview`
3. **Markets & Risk:** Dropdown linking to `/predictions`, `/risk`, `/anticipation`
4. **Corporate Universe:** Dropdown linking to `/companies`, `/industries`, `/sectors`
5. **Portfolio:** Direct link to `/portfolio`
6. **Reports:** Direct link to `/reports`
7. **AI Analyst:** Direct link to `/ai-analyst`
8. **Right Utility Cluster:** Command Palette trigger (`⌘K`), Live Monitoring pulse indicator, Notifications bell, User Profile menu (`UserSession` from `localStorage`), and Mobile hamburger drawer (`MobileDrawer`).

### 3.3 Dead & Orphaned Layout Components
Code inspection revealed two substantial orphaned layout components that are never imported or rendered by the application shell:
1. **`frontend/components/layout/Sidebar.tsx` (200 lines, 7.8 kB):** Legacy collapsible 60px/240px left sidebar. It remains in the repository but has 0 import references.
2. **`frontend/components/layout/Header.tsx` (309 lines, 10.7 kB):** Legacy header with search input and user profile. It has 0 import references.
3. **`frontend/styles/globals.css` (159 lines, 3.9 kB):** Legacy styling file from early Task 8.14 foundation. The active layout in `app/layout.tsx` imports `app/globals.css`, rendering `styles/globals.css` completely unused.

---

## 4. Comprehensive 35-Route Inventory

Every single page (`page.tsx`) in the `frontend/app/` directory was inspected. Below is the granular route register:

```
Route Inventory Summary:
├── Core & Overview:        /, /overview, /coverage
├── Daily Workspace:        /workspace, /watchlists, /watchlists/[watchlistId], /alerts, /notifications
├── Parliamentary Bills:    /bills, /bills/[billId], /bills/compare, /explorer, /latest-bills, /upcoming-legislation, /live-discovery
├── Sub-National States:    /states, /states/[state]
├── Econometrics & Risk:    /predictions, /predictions/[predictionId], /risk, /anticipation
├── Corporate Universe:     /companies, /companies/[companyId], /industries, /industries/[industryId], /industry/[industryId], /sectors
├── Portfolio & Executive:  /portfolio, /reports, /ai-analyst
└── Admin & Lifecycle:      /settings, /onboarding, /login, /signup, /monitoring
Total: 35 Routes
```

### Granular Route Specification Table

| # | Route Path | Primary Purpose | Existing Capabilities | Main Components | Current Layout Pattern | Repeated UI Patterns | Visual / Usability Problems | Recommended Redesign Direction | Features Preserved | Suggested Validation |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `/` | Product Landing & Institutional Overview | Platform value proposition, production metrics, firewall status, workflow cards, auth entry. | `app/page.tsx` | Full-width landing layout, top status ticker, hero, 6-metric KPI grid, 3-firewall cards, 4-workflow cards, footer. | Gradient text, glowing blur balls, dark card grids with emoji icons. | Feels like an AI template; glowing blue/indigo blur (`blur-[120px]`); unstyled emoji icons (`🔍`, `📈`). | Refined editorial SaaS overview with structured typography, micro-benchmarks, and interactive demo preview. | Real metrics (20 Central, 44 State, 47 Quant, 4,700 Preds), firewalls, auth routing. | Vitest visual snapshot + auth redirection test. |
| 2 | `/workspace` | Daily Decision Intelligence Center | Personalized daily feed, watched entity activity, alerts, analytics snapshot, AI assistant. | `workspace/page.tsx`, `AIWorkspaceAssistant.tsx` | 3-column dashboard: Summary KPIs, activity feed, entity baskets, and AI side panel. | Flat card grid, stacked epistemic badges, tabbed lists. | Visual clutter; too many competing cards without clear focal hierarchy; dense without progressive disclosure. | Linear-style command dashboard with unified activity stream, priority grouping, and collapsible AI copilot. | Summary KPIs, activity feeds, watchlist grouping, analytics snapshots, AI integration. | `workspace.test.tsx` |
| 3 | `/bills` | Parliamentary Bills Registry | Canonical registry of 20 Central + 44 State acts, search, jurisdiction filters, card/table view. | `BillsContent.tsx`, `SearchInput.tsx`, `Pagination.tsx` | Filter bar at top, view switcher (Table/Card), paginated list, jurisdiction tabs. | Repeated rounded cards with status badges, hardcoded dark borders (`#0c1322`). | In card view, cards look identical; table view lacks sticky header contrast; emojis in tabs. | Clean, high-density data grid with fast column sorting, quick preview drawer on row click, and refined badges. | Central/State act directory, search debouncing, card/table view toggle, pagination. | `bill-detail.test.tsx`, `bills.test.tsx` |
| 4 | `/bills/[billId]` | Bill Intelligence Dossier | Complete statutory dossier: provisions, exposure, predictions, anticipation, official PDF. | `BillDetailContent.tsx`, `BillHeader.tsx`, `KeyProvisions.tsx`, `CorporateExposureTable.tsx` | 2-column layout: 2/3 main analytical stream + 1/3 contextual metadata sidebar. | Stacked cards with colored left borders (`card-live`, `card-modelled`), dense tables. | Overwhelming vertical scroll length (19,000 bytes component); deep nested sections require too much scrolling. | Multi-tabbed executive dossier: Provisions \| Exposure \| Econometrics \| Gazette PDF with sticky breadcrumb bar. | Multi-chamber timeline, provisions list, exposure matrix, event study table, state firewall, PDF link. | `bill-detail.test.tsx` |
| 5 | `/bills/compare` | Side-by-Side Bill Comparison | Comparative analysis of 2 bills: provisions, exposure overlap, regulatory divergence. | `bills/compare/page.tsx` | Dual selector header, side-by-side comparison tables, overlap matrix. | Split column layout, comparison table with alternating dark rows. | Horizontal scroll issues on smaller viewports; diffs lack syntax/legal text highlighting. | Split-pane view with synchronized scrolling, inline provision diff engine, and corporate overlap Venn diagram. | Dual bill selection, provision comparison, exposure overlap matrix. | `compare.test.tsx` |
| 6 | `/explorer` | Multi-Facet Legislative Explorer | Comprehensive faceted search across Central & State acts, modeling levels, and stages. | `ExplorerContent.tsx`, `CapabilityBadge.tsx` | Split layout: Left facet sidebar (jurisdiction, status, L1/L2) + Right results feed. | Facet filter pills, card/table switch, capability level badges. | Left filter sidebar is overly tall; filter pills lack visual feedback; heavy DOM re-rendering. | Compact collapsible filter panel with active filter chips, instant search, and instant facet counts. | All facet filters, modeling level filters, search query, card/table views. | `explorer.test.tsx` |
| 7 | `/states` | Sub-National Legislative Register | State legislative tracking across 4 implemented states + 24 planned states. | `StatesContent.tsx`, `CapabilityBadge.tsx` | Top state metrics, 4 pilot state cards, 24 planned state table. | Grid of identical state cards with state flags/icons and exposure counts. | Pilot cards look disconnected from the planned expansion matrix; lack of geographical context. | Interactive sub-national map visualizer or segmented tabs with clear statutory firewall indicators. | 4 implemented states, 44 pilot acts, 24 expansion states, zero stock prediction firewall notice. | `states.test.tsx` |
| 8 | `/states/[state]` | State Assembly Dossier | Granular intelligence on a specific state: acts, corporate exposure, industrial hubs. | `StateDetailContent.tsx` | Header, summary KPIs, acts table, corporate facilities table, geographic map details. | Standard dark cards, exposure table with ISINs. | Facilities data looks plain; lack of clear separation between statutory mandates and local regulations. | Refined jurisdictional dossier with facility map badges, industrial corridor linkages, and gazette links. | All enacted state acts, corporate exposure table, facilities list, zero stock prediction guarantee. | `states.test.tsx` |
| 9 | `/latest-bills` | Chronological Enactments Feed | Live feed of recently introduced, amended, and enacted bills across all assemblies. | `latest-bills/page.tsx`, `DataStatusBadge.tsx` | Single column chronological feed with status filters and search. | Feed item cards with timestamp pills and status badges. | Repetitive card design; lacks visual distinction between Central Parliament and State Assembly events. | Timeline view with distinct chamber badges, timestamp precision, and quick-add to watchlist action. | Chronological sorting, status filters, direct link to dossier. | `task-8-25-navigation.test.tsx` |
| 10 | `/upcoming-legislation` | Parliamentary Calendar & Agendas | Upcoming bills, session agendas, and committee review timelines. | `upcoming-legislation/page.tsx` | Calendar view / list of upcoming legislative events. | Calendar date badge cards, agenda item rows. | Text is dense; status labels lack visual hierarchy. | Interactive parliamentary calendar with chamber filter (Lok Sabha / Rajya Sabha / Vidhan Sabha). | Scheduled legislative dates, bill introduction notices, agenda summaries. | Build verified |
| 11 | `/live-discovery` | Automated Gazette Intake Feed | Real-time intake stream of unmodelled official gazette publications and notices. | `live-discovery/page.tsx`, `DataStatusBadge.tsx` | Live stream table with polling indicator, status filters, and source links. | Blinking live pulse indicators (`.live-pulse`), table rows with status badges. | Excessive blinking dots; unformatted raw gazette titles; lacks structured intake provenance. | High-frequency telemetry table with clean paused/streaming controls and source inspection drawer. | Live unmodelled stream, status filtering, source verification flags, zero prediction guarantee. | `task-8-25-navigation.test.tsx` |
| 12 | `/overview` | Platform Baseline & Analytics | Authoritative metrics: 20 Central bills, 44 State bills, 4,700 predictions, 70 companies. | `OverviewContent.tsx` | Executive summary dashboard with baseline metrics and system diagrams. | Flat metric cards, ASCII-art or SVG diagrams with glowing borders. | Diagrams use fixed pixel widths causing overflow on tablets; colors compete with each other. | Modern institutional telemetry dashboard with clear data provenance and baseline hash audit badge. | Complete baseline invariant counters, system architecture summary, API health indicators. | `overview.test.tsx` |
| 13 | `/predictions` | Central Econometric Predictions | Screener for 4,700 quantitative market impact predictions across 5 event study windows. | `PredictionsContent.tsx`, `InstitutionalTable.tsx` | Top filters (Bill, Company, Window, Direction), summary stats, dense prediction table. | Dense tabular layout, positive/negative color tags, multi-select dropdowns. | Table is 44 kB; filters take up massive vertical space; horizontal scroll can feel clunky. | High-performance institutional financial data grid with column filters, sparkline trajectories, and quick drawer. | 4,700 predictions, 5 event horizons, CAR values, confidence intervals, model status. | `predictions.test.tsx` |
| 14 | `/predictions/[predictionId]` | Prediction Detail & CAR Trajectory | In-depth econometric breakdown: CAR trajectory, t-stat, p-value, decision support. | `PredictionDetailContent.tsx` | Multi-panel view: CAR trajectory, statistical diagnostics, decision matrix, anticipation score. | Chart cards, statistical metric grid, recommendations box. | Heavy monospace tables; decision recommendations box uses generic green/amber borders. | Institutional quant tear-sheet: interactive event-study trajectory chart, regression parameters, decision rationale. | CAR trajectory, statistical significance (p-value, t-stat), 5-horizon matrix, decision support. | `prediction-detail.test.tsx` |
| 15 | `/risk` | Systemic Legislative Risk Matrix | Cross-sector systemic risk classification, portfolio risk calculator, exposure scores. | `RiskContent.tsx` | Risk distribution cards, composite risk calculator, high-risk bills table. | Danger/warning color tags (`text-rose-400`, `text-amber-400`), slider inputs. | High cognitive load; sliders feel like an afterthought; danger colors are over-saturated. | Institutional risk workbench: risk distribution breakdown, sensitivity matrix, and stress-testing simulator. | Risk score formula, high-risk bill rankings, company risk rankings, ISIN calculator. | `risk.test.tsx` |
| 16 | `/anticipation` | Pre-Event Market Anticipation | Screener for 940 bill-company anticipation scores and public media diffusion signals. | `AnticipationContent.tsx`, `AnticipationEvidenceSection.tsx` | Filterable table of anticipation diffusion scores, tier badges, and evidence drawer trigger. | Tier badges (`TIER_1_SURPRISE`, etc.), tabular rows, slide-out drawer for evidence. | Tier badges are all uppercase with underscores (`TIER_1_HIGH_DIFFUSION`); drawer animation is basic. | Clean diffusion ranking with score deciles, visual timeline of news leaks, and structured evidence drawer. | 940 anticipation scores, anticipation tiers, media signal counts, news evidence. | `anticipation.test.tsx` |
| 17 | `/companies` | Corporate Universe Directory | Directory of 70 covered companies (47 Quantitative + 20 Intelligence + 3 Reference). | `CompaniesContent.tsx`, `CapabilityBadge.tsx` | Universe tabs (All / Quant / Intel), sector filters, exposure count table, tear-sheet drawer. | Tabular rows with company logos/initials, ticker tags, exposure count badges. | Initials badges look flat; company cards lack clear visual differentiation between Quant and Intel entities. | Precision corporate registry with clear exchange pills (NSE/BSE), market cap indicators, and tear-sheet drawer. | 70 companies, 47 quant vs 23 non-quant separation, exposure counts, ISINs, tickers. | `companies.test.tsx` |
| 18 | `/companies/[companyId]` | Corporate Intelligence Dossier | Full corporate profile: legislative exposure, state operational footprint, predictions, AI copilot. | `CompanyDetailContent.tsx`, `CompanyHeader.tsx`, `CompanyExposureMatrix.tsx` | 2-column layout: Header, exposure matrix, geographic footprint, predictions, AI panel. | Stacked analytical cards, repeated tables, intelligence firewall banner. | Very long scroll; state geographic facilities are plain text; predictions table is cramped. | Tabbed corporate terminal: Regulatory Exposure \| Facility Geography \| Event Studies \| AI Copilot. | Exposure matrix, geographic facilities, 5-horizon predictions (if quant), firewall notice (if intel). | `company-detail.test.tsx` |
| 19 | `/industries` | Granular Industries Taxonomy | 13 economic sectors and granular sub-industries with legislative exposure counts. | `IndustriesContent.tsx` | Grid of sector cards with expandable industry lists and affected bill counts. | Sector cards with icons, list of nested industries with exposure pills. | Repetitive cards; nested industry links can be hard to click on mobile. | Interactive taxonomy explorer: Tree view or accordion cards with industry exposure heatmaps. | 13 macro sectors, granular sub-industries, affected bill and company counts. | `industries.test.tsx` |
| 20 | `/industries/[industryId]` | Plural Industry Dossier Route | Alias route redirecting/rendering the singular industry dossier. | `industries/[industryId]/page.tsx` | Delegates directly to `IndustryDetailContent`. | N/A (Alias route). | Duplicate route maintenance risk; ensure metadata matches singular route. | Keep as canonical redirect or seamless alias to `/industry/[industryId]`. | Route compatibility, metadata generation. | `industries.test.tsx` |
| 21 | `/industry/[industryId]` | Singular Industry Dossier | Detailed legislative footprint, affected companies, and economic transmission mechanisms. | `IndustryDetailContent.tsx`, `IndustryHeader.tsx`, `EconomicTransmissionMap.tsx` | Industry header, legislative footprint table, transmission diagram, corporate table. | Diagram boxes with arrows, exposure tables. | Transmission diagram uses static ASCII/CSS boxes; lacks interactive drill-down. | Interactive transmission flow diagram, company exposure ranking, and regulatory vulnerability scores. | Affected bills list, corporate exposure list, transmission mechanisms, AI summary. | `industry-detail.test.tsx` |
| 22 | `/sectors` | Macroeconomic Transmission Map | High-level macro view of all 13 economic sectors, policy exposure, and transmission channels. | `SectorsContent.tsx` | Macro overview grid, policy transmission map, cross-sector vulnerability table. | Sector tiles with colored icons, tabular summary rows. | Tiles look like a toy dashboard; lacks comparative sector weighting. | Treemap or matrix visualizer showing legislative intensity across macroeconomic sectors. | 13 sectors, policy transmission pathways, affected corporate count. | Build verified |
| 23 | `/portfolio` | Portfolio Holdings & Exposure | User portfolio workspace: holdings upload (CSV/XLSX), exposure tiers, relevance explanations. | `portfolio/page.tsx` | Portfolio switcher, exposure summary KPIs, 3 tabs (Exposure, Holdings, Report), upload modal. | Tier badge colors (`DIRECT`, `HIGH RELEVANCE`), holdings table, modal overlays. | Upload modal error handling is basic; relevance modal is text-heavy; tables lack density controls. | High-performance portfolio workbench: drag-and-drop CSV parser with instant validation, exposure matrix. | CSV/XLSX holdings import, manual holding entry, 5 exposure tiers, "Why is this relevant?" AI modal. | Build verified |
| 24 | `/reports` | Institutional Report Center | Generate and download 7 institutional report types (Bill, Company, Portfolio, Risk, etc.). | `reports/page.tsx`, `DataStatusBadge.tsx` | Template selection grid (7 templates), format selectors (PDF/CSV/XLSX), generated reports table. | Template cards with emoji icons (`📜`, `🏢`, `📊`), download buttons. | Emojis in template cards look unprofessional; lack of report preview before generation. | Professional report generator with live document preview, template customization, and export queue. | 7 report templates, format options (PDF, CSV, XLSX), provenance stamps, epistemic labels. | Build verified |
| 25 | `/ai-analyst` | Grounded AI Research Terminal | Conversational research assistant grounded in parliamentary acts and gazette records. | `ai-analyst/page.tsx`, `AIAnalystContent.tsx`, `ContextDrawer.tsx` | Split screen: Left chat panel (tri-persona selector, messages) + Right evidence drawer. | Chat bubbles with avatar pills, persona buttons, source link citations. | Chat bubbles look like consumer messengers; lack of rich markdown tables in AI responses; citation pills small. | Enterprise research workstation: Split-pane with persistent source documents, verified citation highlights. | Tri-persona selection (Investor, Policy, Compliance), context binding, statutory citations, guardrails. | `ai-analyst.test.tsx` |
| 26 | `/watchlists` | Custom Watchlists Management | Create and manage custom entity baskets (bills, companies, states) with alert rules. | `watchlists/page.tsx` | Watchlist list cards, create watchlist modal, quick entity count summary. | Card grid of user watchlists with delete/edit icons. | Cards look generic; lacks batch entity addition. | Compact workspace list with drag-and-drop ordering, quick entity search, and alert rule toggles. | Watchlist CRUD, entity baskets, notification frequency settings. | `watchlists.test.tsx` |
| 27 | `/watchlists/[watchlistId]` | Watchlist Basket Detail | Detailed view of a specific watchlist: member entities, live changes, basket risk. | `watchlists/[watchlistId]/page.tsx` | Watchlist header, add entity search, entity table, basket activity feed. | Tabular rows with remove buttons, activity cards. | Activity feed is unranked; entity search lacks category grouping. | High-density watchlist command center with grouped entity tables and chronological change feed. | Entity management, alert threshold triggers, activity feed. | `watchlists.test.tsx` |
| 28 | `/alerts` | Legislative Alerts Severity Center | Central alerts inbox grouped by severity (URGENT, ELEVATED, STANDARD), rule builder. | `alerts/page.tsx` | Severity summary KPIs, severity filter tabs, alerts feed, dismiss/read actions. | Severity badges with pulse dots, list of alert cards with action buttons. | Card list becomes overwhelming when alert volume is high; lacks bulk actions (mark all read). | Linear-style triage inbox with keyboard navigation (J/K to move, E to archive), severity filters. | Severity grouping, unread tracking, dismiss actions, rule linkages. | `alerts.test.tsx` |
| 29 | `/notifications` | In-App Notification Center | In-app notification center for system updates, crawler events, and digest summaries. | `notifications/page.tsx` | Notification list, unread filter, mark all read button, channel settings link. | Simple card list with timestamp and unread dot indicator. | Plain styling; lacks category icons or direct deep-links to changed sections. | Clean notification stream with actionable deep links, grouping by day, and toast integration. | Read/unread state, clear notifications, channel routing. | `notifications.test.tsx` |
| 30 | `/monitoring` | Observability & Crawler Hub | Observability center for 22 monitored sources: health status, crawl history, scheduler. | `MonitoringCenterContent.tsx`, `SourceRegistryTable.tsx`, `SchedulerPanel.tsx` | 4-tab panel: Overview KPIs, 22 Sources Registry, Crawl History, Scheduler telemetry. | Health status pills (`HEALTHY`, `DEGRADED`), dense registry table, scheduler cards. | Scheduler cron cards are visually noisy; drawer for source detail is slightly cramped. | Datadog/Vercel-style telemetry console: source uptime sparklines, latency metrics, and crawl logs. | 22 source crawlers, health check history, scheduler status, epistemic labels. | `monitoring.test.tsx` |
| 31 | `/coverage` | Platform Coverage & Invariants | Formal audit page displaying the 78 capabilities, analytical baseline, and firewalls. | `CoverageContent.tsx`, `CapabilityBadge.tsx` | System verification banner, capability audit matrix, frozen baseline hash display. | Long checklist with green checkmarks, code blocks displaying JSON hashes. | Long static text list; difficult to search across the 78 items on screen. | Interactive compliance audit console with capability search, filter by tier, and cryptographic SHA-256 verifier. | All 78 capability checks, baseline SHA-256 verification, statutory firewalls. | `coverage.test.tsx` |
| 32 | `/settings` | Organization Settings & RBAC | Multi-tenant tenant configuration, member management, RBAC roles, alert preferences. | `settings/page.tsx` | Tabbed settings: Organization Profile, Team Members & Roles, Notification Rules, API Keys. | Standard form fields, member table with role dropdowns, toggle switches. | Form inputs have hardcoded dark backgrounds (`bg-slate-900 border-slate-700`); toggle switches basic. | Polished enterprise settings console with tenant switcher, audit log export, and granular notification preferences. | Tenant ID, display name, RBAC roles (OWNER, ADMIN, MEMBER, VIEWER), quiet hours. | `settings.test.tsx` |
| 33 | `/onboarding` | Interactive Product Tour | 8-step interactive tour explaining statutory intelligence, firewalls, and workflows. | `onboarding/page.tsx` | Step carousel / stepper with progress bar, explanatory cards, and "Launch" action. | Stepper circles with connecting lines, next/back buttons. | Stepper controls are basic; text copy is heavy; lacks interactive product screenshots. | Interactive guided onboarding with progressive feature highlights, keyboard shortcuts, and role customization. | 8-step workflow onboarding, role setup, quick watchlist creation. | Build verified |
| 34 | `/login` | Tenant Authentication Sign In | Organization login with demo account switchers, credentials input, error banners. | `login/page.tsx` | Centered authentication card, brand logo, email/password form, quick-fill demo buttons. | Centered card with dark backdrop blur, demo role buttons (`bg-slate-800`). | Card has amateur emoji logo (`<span className="text-2xl">⚖</span>`); looks like a prototype login. | Sleek enterprise auth portal with custom vector brand emblem, passkey/SSO readiness, and secure session management. | JWT authentication, role resolution, demo analyst credentials, error handling. | `task-8-25-navigation.test.tsx` |
| 35 | `/signup` | Organization Account Registration | New tenant registration: organization name, admin credentials, workspace provisioning. | `signup/page.tsx` | Centered registration card, form fields, role description, link to sign in. | Centered card, standard input fields, submit button. | Visual styling mirrors login; lacks organization tier selector or validation feedback. | Multi-step organization onboarding with domain verification, tenant workspace preview, and invitation links. | Tenant creation, admin registration, validation rules. | Build verified |

---

## 5. Detailed Visual Design Audit: Why the Current UI Feels AI-Generated

### 5.1 Concrete Repository Evidence of Visual Problems

#### A. Overuse of Gradients & Glow Effects
- **Evidence in Code:**
  - `frontend/app/globals.css:617-629`:
    ```css
    .gradient-text {
      background: linear-gradient(135deg, #60a5fa, #818cf8, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    .glow-blue {
      box-shadow: 0 0 20px rgba(59, 130, 246, 0.15);
    }
    ```
  - `frontend/app/page.tsx:60`:
    ```tsx
    <div className="h-96 w-[45rem] rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 blur-[120px]" />
    ```
- **Harm to Usability & Identity:** Gradient text reduces contrast on analytical headers. The 120px blurred gradient ball is the quintessential hallmark of automated "AI SaaS template" generators. It has no functional connection to parliamentary analysis or econometrics.
- **Correction:** Replace gradient text with crisp, high-contrast typography (`text-slate-100` / `text-slate-900`) and subtle, restrained typography tracking. Eliminate all heavy blurred background blobs in favor of subtle CSS border geometry or an ultra-low-opacity ambient mesh.

#### B. Repetitive Rounded Cards Without Visual Hierarchy
- **Evidence in Code:**
  - In `frontend/app/page.tsx:121-152`, six metric cards use the exact same classes:
    `bg-slate-900/80 border border-slate-800 rounded-xl p-4 text-center`.
  - In `frontend/app/workspace/page.tsx`, every module is wrapped in identical `border border-slate-800 rounded-xl bg-slate-900/60` containers.
- **Harm to Usability & Identity:** Every element competes at the same visual weight. The human eye cannot establish where to look first.
- **Correction:** Introduce varied information densities: primary focal modules receive distinct surface elevations, while secondary data is presented in clean divider-separated tables or structured lists without card boxing.

#### C. Emojis Substituted for Professional Vector Icons
- **Evidence in Code:**
  - `frontend/components/layout/TopNavbar.tsx:62, 68-75`:
    `icon: "🏛"`, `icon: "📜"`, `icon: "🔍"`, `icon: "🗺"`, `icon: "⚡"`, `icon: "📅"`, `icon: "📡"`, `icon: "⚖"`, `icon: "📈"`.
  - `frontend/components/layout/Sidebar.tsx:96`: `<span className="text-blue-400 text-lg font-bold">⚖</span>`.
  - `frontend/app/login/page.tsx:71`: `<span className="text-2xl">⚖</span>`.
- **Harm to Usability & Identity:** Operating systems render emojis differently (Windows emoji rendering looks drastically different from Apple or Linux rendering). Emojis convey an informal, hobbyist aesthetic inappropriate for a multi-million-rupee institutional financial intelligence tool.
- **Correction:** Replace all raw unicode emojis with a cohesive, lightweight inline SVG icon set (e.g., customized 16px/20px geometric icons with consistent 1.5px stroke weight).

#### D. Hardcoded Dark Color Palette & Missing Light Mode
- **Evidence in Code:**
  - 41 files in `frontend/` contain hardcoded `bg-slate-950` or `bg-slate-900`.
  - `frontend/app/layout.tsx:54` hardcodes `<body className="bg-[#05090f] text-slate-200">`.
  - `frontend/app/globals.css` only specifies tokens for `:root` with dark values, lacking any light-theme definitions.
- **Harm to Usability & Identity:** Institutional analysts in corporate, legal, or governmental environments frequently require light mode for document review and daylight viewing. The absence of light mode severely limits enterprise adoption.
- **Correction:** Establish a complete semantic design token architecture where all surfaces, borders, and text map to CSS custom properties that switch seamlessly between light and dark modes via a `data-theme` attribute.

---

## 6. Performance Audit: Measured vs. Perceived Latency

A rigorous audit distinguishes visual clunkiness from actual measured performance:

### 6.1 Measured Performance Data
From prior production benchmarks (`docs/PRODUCTION_SMOKE_TEST.md` and `docs/TASK_8_22_FINAL_DEPLOYMENT_REPORT.md`):
- **Fast Endpoints:**
  - `/api/v1/bills`: 1.84 ms ($p_{50}$), 2.91 ms ($p_{95}$) — **EXTREMELY FAST**
  - `/api/v1/companies`: 1.25 ms ($p_{50}$), 1.95 ms ($p_{95}$) — **EXTREMELY FAST**
  - `/api/v1/predictions`: 2.15 ms ($p_{50}$), 3.40 ms ($p_{95}$) — **EXTREMELY FAST**
- **Slower Endpoints:**
  - `/api/v1/search`: **693.78 ms** ($p_{50}$) — Deep multi-jurisdiction text scanning across 66 records. This latency is backend text search execution, not frontend rendering.

### 6.2 Perceived Frontend Bottlenecks
1. **Unvirtualized DOM in Heavy Pages:** `PredictionsContent.tsx` renders large arrays of tabular items without virtual scrolling, causing brief UI thread stutter during rapid filtering.
2. **Missing Optimistic UI Updates:** Watchlist toggle and alert dismissal wait for round-trip API responses rather than providing instant tactile feedback.
3. **Monolithic Page Bundles:** `PredictionsContent.tsx` (44.4 kB) and `RiskContent.tsx` (46.0 kB) contain multiple complex sub-components in single files rather than code-split progressive modules.

---

## 7. Audit Conclusion & Identified Unknowns

### 7.1 Verified Architectural Facts
1. The frontend uses Next.js 16.3.5 and React 19.2.8 with App Router.
2. The CSS framework is Tailwind CSS v4 using CSS-first imports.
3. The routing tree contains exactly 35 active `page.tsx` routes.
4. All 78 functional capabilities identified in Task 8.31A remain preserved and active.
5. The platform baseline is strictly frozen and verified against SHA-256 `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`.

### 7.2 Explicit UNKNOWNs & Future Investigation Steps
- **[UNKNOWN-1] Production Bundle Size & Route Split Analysis:** Next.js production build (`next build`) has not been executed in this audit turn to preserve read-only constraints. Route bundle sizes should be measured in a dedicated non-destructive build task.
- **[UNKNOWN-2] Vector Asset Preference:** The codebase contains 0 custom SVG logo files. Whether stakeholders prefer a standalone abstract geometric emblem or an architectural pillar monogram must be formally presented in the Brand Blueprint.
- **[UNKNOWN-3] High-DPI Chart Rendering:** Charts currently rely on HTML/CSS tables and SVG snippets. Transitioning to canvas-based or interactive vector charts in future phases must be tested against React 19 SSR hydration.
