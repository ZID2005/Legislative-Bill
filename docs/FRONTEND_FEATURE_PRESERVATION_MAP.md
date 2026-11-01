# FRONTEND FEATURE PRESERVATION MAP
## India Legislative Intelligence & Market Impact Platform
**Document Version:** 1.0.0  
**Status:** Canonical Feature & Invariant Preservation Specification  
**Execution Gate:** READ-ONLY SPECIFICATION (No source files modified).

---

## 1. Non-Negotiable Invariants & Analytical Baseline

The platform's analytical baseline is strictly **IMMUTABLE and FROZEN**. The frontend redesign is an interface elevation and usability overhaul; it must never mutate, recalculate, re-index, or bypass any established econometric data or statutory firewall.

### 1.1 Authoritative Baseline Inventory (`docs/production_baseline.json`)
The following metrics and invariants must remain 100% bit-for-bit identical before, during, and after any frontend redesign:

| Invariant / Dataset | Authoritative Metric | Firewall Status | Preservation Guarantee |
|---|---|---|---|
| **Central Production Bills** | **20 Acts** (22 Scanned Records) | `IMMUTABLE_FROZEN` | Retained across `/bills`, `/explorer`, `/workspace`. |
| **Quantitative Securities** | **47 Listed Equities** (NSE/BSE) | `LEVEL 1 QUANTITATIVE` | Retained across `/companies`, `/predictions`. |
| **Bill-Company Pairs** | **940 Pairs** | `FROZEN_RELATIONSHIP` | Retained across corporate exposure matrices. |
| **Market Predictions** | **4,700 Predictions** | `IMMUTABLE_FROZEN` | 940 pairs × 5 event study windows. |
| **Decision Support Records** | **4,700 Decisions** | `IMMUTABLE_FROZEN` | Deterministic recommendations preserved. |
| **Anticipation Scores** | **940 Diffusion Scores** | `IMMUTABLE_FROZEN` | Deciles & media evidence retained. |
| **Stakeholder Reports** | **14,100 Reports** | `IMMUTABLE_FROZEN` | 4,700 Investor + 4,700 Business + 4,700 Public. |
| **State Production Bills** | **44 Pilot Acts** | `PILOT_STABLE` | AP=12, KA=11, KL=11, TS=10. |
| **State Stock Predictions** | **EXACTLY 0** | `STATUTORY_FIREWALL_LOCKED` | **Zero stock predictions for State acts.** |
| **Intelligence Entities** | **20 Companies** (+ 3 Reference) | `FIREWALL_INTEL_ONLY` | Segregated from quant models. |
| **Total Corporate Exposures**| **104 Linkages** | `AUTHORITATIVE_MAPPING` | 18 Central + 86 State corporate exposures. |
| **Baseline SHA-256 Manifest**| `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7` | **FROZEN / UNTOUCHED** | **Bit-for-bit exact match verification.** |

---

## 2. Complete 78-Capability Preservation Matrix

Every single one of the 78 audited functional capabilities (CAP-1 to CAP-78) is formally mapped below to its redesigned location, interaction model, and validation suite:

| # | Capability Name | Current Route & Component | Proposed Redesigned Location | Interaction Pattern | Preservation Guarantee | Verification Test |
|---|---|---|---|---|---|---|
| **1** | Multi-Tenant Organization Switcher | Global / `TopNavbar.tsx` | Global Header User Menu | Contextual Dropdown in User Profile | Session state persisted in `localStorage` & `/api/v1/auth/me` | `task-8-25-navigation.test.tsx` |
| **2** | Role-Based Access Control (RBAC) Indicator | Global / `TopNavbar.tsx` | Global Header User Badge | Pill badge (OWNER/ADMIN/MEMBER/VIEWER) | Reads `session.role` with zero logic changes | `task-8-25-navigation.test.tsx` |
| **3** | Command Palette Fuzzy Search (`⌘K`) | Global / `CommandPalette.tsx` | Global Overlay (`⌘K`) | Centered modal with keyboard navigation | Calls `/api/v1/search` with full category mapping | Verified in UI / Vitest |
| **4** | Live Monitoring Health Pulse | Global / `TopNavbar.tsx` | Global Header Utility | Heartbeat dot with status popover | Polls `/api/v1/monitoring/overview` every 60s | `monitoring.test.tsx` |
| **5** | Unread Urgent Alert Badge Counter | Global / `TopNavbar.tsx` | Global Header Utility | Pill counter on notification bell | Queries unread alert count from backend | `alerts.test.tsx` |
| **6** | Navigation Dropdowns (5 Workspaces) | Global / `TopNavbar.tsx` | Global Header Navigation | Micro-dropdowns with smooth CSS fade | Preserves all 22 navigation destination routes | `task-8-25-navigation.test.tsx` |
| **7** | Mobile Slide-Over Navigation Drawer | Global / `TopNavbar.tsx` | Mobile Shell Drawer | Slide-over panel (`translateX`) | Mirrors 100% of desktop navigation links | `task-8-25-navigation.test.tsx` |
| **8** | Central Production Acts Register | `/bills` / `BillsContent.tsx` | `/bills` Directory Tab 1 | High-density data grid with fast filters | Renders all 20 Central production acts | `bill-detail.test.tsx` |
| **9** | State Assembly Acts Register | `/bills` / `BillsContent.tsx` | `/bills` Directory Tab 2 | High-density data grid with state pills | Renders all 44 State pilot acts | `explorer.test.tsx` |
| **10** | Jurisdiction Filter Tabs (All/Central/State) | `/bills` / `BillsContent.tsx` | `/bills` Filter Bar | Segmented control with instant filtering | Client-side filter over statutory jurisdiction | `bills.test.tsx` |
| **11** | Dense Table vs Card View Switcher | `/bills` / `BillsContent.tsx` | `/bills` View Controls | Icon button segmented toggle | State preserved in local component state | `bills.test.tsx` |
| **12** | Bill Search with Client Debouncing | `/bills` / `SearchInput.tsx` | `/bills` Search Input | Debounced 250ms input field | Queries bill title and statutory tags | `bills.test.tsx` |
| **13** | Bill Pagination Controls | `/bills` / `Pagination.tsx` | `/bills` Table Footer | Pagination bar with items-per-page selector | Standardized page index & page size | `bills.test.tsx` |
| **14** | Bill Dossier Executive Header | `/bills/[id]` / `BillHeader.tsx` | `/bills/[billId]` Header | Hero metadata block with status badges | Displays Ministry, Gazette date, Act number | `bill-detail.test.tsx` |
| **15** | Multi-Chamber Procedural Timeline | `/bills/[id]` / `LegislativeTimeline.tsx` | `/bills/[billId]` Tab 1 | Interactive horizontal stepper timeline | Chronological milestones (Intro, Pass, Assent) | `bill-detail.test.tsx` |
| **16** | Statutory Key Provisions Listing | `/bills/[id]` / `KeyProvisions.tsx` | `/bills/[billId]` Tab 2 | Expandable provision cards with legal tags | Full statutory text fragments & summaries | `bill-detail.test.tsx` |
| **17** | Corporate Exposure Matrix | `/bills/[id]` / `CorporateExposureTable.tsx`| `/bills/[billId]` Tab 3 | Exposure table with ticker & ISIN badges | Direct & indirect exposure linkages | `bill-detail.test.tsx` |
| **18** | Central Event Study Predictions Table | `/bills/[id]` / `CentralPredictionSection.tsx`| `/bills/[billId]` Tab 4 | Event study table across 5 windows | CAR predictions, t-stat, p-value | `bill-detail.test.tsx` |
| **19** | State Stock Prediction Firewall | `/bills/[id]` / `StatePredictionFirewall.tsx`| `/bills/[billId]` Notice Banner | High-visibility statutory firewall alert | **Hard blocks predictions for State bills** | `StatePredictionFirewall.test.tsx` |
| **20** | Pre-Event Market Anticipation Scores | `/bills/[id]` / `AnticipationSection.tsx`| `/bills/[billId]` Tab 5 | Decile diffusion gauge & signal breakdown | 940 anticipation scores preserved | `bill-detail.test.tsx` |
| **21** | Official Gazette PDF Download | `/bills/[id]` / `DocumentSourcesSection.tsx`| `/bills/[billId]` Action Cluster| PDF viewer trigger & download link | Links to canonical gazette PDF archive | `bill-detail.test.tsx` |
| **22** | Plain-Language AI Synthesis | `/bills/[id]` / `PlainLanguageSection.tsx`| `/bills/[billId]` Overview | Executive synthesis callout with disclaimer | Layman summary with non-advice firewall | `bill-detail.test.tsx` |
| **23** | Stakeholder Impact Breakdown | `/bills/[id]` / `StakeholderIntelligence.tsx`| `/bills/[billId]` Tab 6 | Tri-stakeholder cards (Investor/Business/Public)| Preserves all 3 stakeholder impact views | `bill-detail.test.tsx` |
| **24** | Gazette Text Changes Diff Audit | `/bills/[id]` / `WhatChangedView.tsx` | `/bills/[billId]` Tab 7 | Side-by-side text diff with additions/deletions | Statutory amendment comparison | `bill-detail.test.tsx` |
| **25** | Provenance & Source Metadata | `/bills/[id]` / `ProvenancePanel.tsx` | `/bills/[billId]` Drawer / Footer | Verification stamp with hash & crawler origin | Full provenance audit trail preserved | `bill-detail.test.tsx` |
| **26** | Dual Bill Comparison Selector | `/bills/compare` / `page.tsx` | `/bills/compare` Header | Dual combobox selector with search | Compares any 2 Central or State bills | `compare.test.tsx` |
| **27** | Side-by-Side Metadata Diff | `/bills/compare` / `page.tsx` | `/bills/compare` Section 1 | Split column comparison table | Compares dates, ministries, jurisdictions | `compare.test.tsx` |
| **28** | Corporate Exposure Overlap Matrix | `/bills/compare` / `page.tsx` | `/bills/compare` Section 2 | Overlapping corporate entity matrix | Identifies shared corporate vulnerabilities | `compare.test.tsx` |
| **29** | Statutory Provisions Diff Table | `/bills/compare` / `page.tsx` | `/bills/compare` Section 3 | Comparative provision diff grid | Aligns related sections across acts | `compare.test.tsx` |
| **30** | Multi-Facet Legislative Explorer | `/explorer` / `ExplorerContent.tsx` | `/explorer` Main View | Dual-view faceted discovery console | Multi-criteria search across all 66 acts | `explorer.test.tsx` |
| **31** | Explorer Table / Card View Switcher | `/explorer` / `ExplorerContent.tsx` | `/explorer` View Toolbar | Segmented view switcher | Supports both dense grid and card view | `explorer.test.tsx` |
| **32** | Jurisdiction Multi-Filter Sidebar | `/explorer` / `ExplorerContent.tsx` | `/explorer` Filter Panel | Collapsible filter panel with count chips | Filters by Central, AP, KA, KL, TS | `explorer.test.tsx` |
| **33** | Legislative Enactment Status Filter | `/explorer` / `ExplorerContent.tsx` | `/explorer` Filter Panel | Multi-select checkboxes with counts | Filters by PASSED, ASSENT_PENDING, etc. | `explorer.test.tsx` |
| **34** | Modeling Level (L1/L2) Filter | `/explorer` / `ExplorerContent.tsx` | `/explorer` Filter Panel | Capability tier filter pills | Separates Quantitative from Intelligence | `explorer.test.tsx` |
| **35** | Chronological Latest Bills Feed | `/latest-bills` / `page.tsx` | `/latest-bills` Feed | Unified chronological timeline feed | Live updates of latest bill introductions | `task-8-25-navigation.test.tsx` |
| **36** | Parliamentary Session Calendar | `/upcoming-legislation` / `page.tsx` | `/upcoming-legislation` View | Calendar & agenda list view | Parliamentary agenda tracking | Build verified |
| **37** | Automated Live Intake Stream | `/live-discovery` / `page.tsx` | `/live-discovery` Telemetry | Real-time intake stream with pause/resume | Telemetry feed for unmodelled gazettes | `task-8-25-navigation.test.tsx` |
| **38** | 70-Entity Corporate Universe Directory | `/companies` / `CompaniesContent.tsx` | `/companies` Main Directory | High-density corporate directory | Covers 47 Quant + 20 Intel + 3 Ref entities | `companies.test.tsx` |
| **39** | Quant vs. Intel Universe Filter | `/companies` / `CompaniesContent.tsx` | `/companies` Filter Bar | Segmented filter tabs | Enforces strict modeling separation | `companies.test.tsx` |
| **40** | Corporate Sector & Industry Filter | `/companies` / `CompaniesContent.tsx` | `/companies` Filter Bar | Dropdown taxonomy filter | Filters across 13 macro sectors | `companies.test.tsx` |
| **41** | Corporate Table with Exposure Counts | `/companies` / `CompaniesContent.tsx` | `/companies` Data Grid | Sortable corporate table with exposure pills | Displays ISIN, ticker, exposure total | `companies.test.tsx` |
| **42** | Quick Tear-Sheet Inspection Drawer | `/companies` / `CompaniesContent.tsx` | `/companies` Slide-over Drawer | Right-hand slide-over drawer (`480px`) | Instant corporate summary on row click | `companies.test.tsx` |
| **43** | Corporate Profile Executive Header | `/companies/[id]` / `CompanyHeader.tsx` | `/companies/[companyId]` Header | Hero corporate card with ticker & exchange | Displays market cap tier, ISIN, sector | `company-detail.test.tsx` |
| **44** | Corporate Exposure Matrix | `/companies/[id]` / `CompanyExposureMatrix.tsx`| `/companies/[companyId]` Tab 1 | Exposure matrix listing all linked acts | Direct vs. indirect regulatory linkages | `company-detail.test.tsx` |
| **45** | Operational State Geographic Footprint | `/companies/[id]` / `StateGeographicSection.tsx`| `/companies/[companyId]` Tab 2 | Interactive state facility listing | Displays facilities across AP, KA, KL, TS | `company-detail.test.tsx` |
| **46** | Economic Transmission Mechanism Map | `/companies/[id]` / `EconomicTransmissionSection.tsx`| `/companies/[companyId]` Tab 3| Transmission mechanism flow diagram | Explains policy-to-earnings channels | `company-detail.test.tsx` |
| **47** | Quantitative CAR Predictions Grid | `/companies/[id]` / `CompanyPredictionsSection.tsx`| `/companies/[companyId]` Tab 4| Multi-horizon event study grid | 5 event horizons with statistical bounds | `company-detail.test.tsx` |
| **48** | Intelligence Entity Firewall Notice | `/companies/[id]` / `IntelligenceCompanyFirewall.tsx`| `/companies/[companyId]` Banner | Statutory firewall warning card | Segregates non-listed companies from quant | `IntelligenceCompanyFirewall.test.tsx` |
| **49** | Corporate Anticipation Evidence Drawer | `/companies/[id]` / `CompanyAnticipationSection.tsx`| `/companies/[companyId]` Tab 5 | Anticipation timeline & news evidence drawer | Public news diffusion diagnostics | `company-detail.test.tsx` |
| **50** | Grounded Corporate AI Analyst | `/companies/[id]` / `CompanyAIPanel.tsx` | `/companies/[companyId]` Tab 6 | Conversational AI copilot scoped to company | Verified citations with refusal guards | `company-detail.test.tsx` |
| **51** | Watchlist Quick-Add Modal | `/companies/[id]` / `CompanyWatchlistModal.tsx`| `/companies/[companyId]` Modal | Quick-add modal with basket selector | Adds company to user watchlists | `company-detail.test.tsx` |
| **52** | Granular Industries Taxonomy | `/industries` / `IndustriesContent.tsx` | `/industries` Main View | Expandable tree/accordion taxonomy | 13 sectors and granular sub-industries | `industries.test.tsx` |
| **53** | Industry Sector Groupings | `/industries` / `IndustriesContent.tsx` | `/industries` Sector Tiles | Sector overview cards with exposure pills | Groups sub-industries under macro sectors | `industries.test.tsx` |
| **54** | Granular Industry Detail Dossier | `/industry/[id]` / `IndustryDetailContent.tsx`| `/industry/[industryId]` Main View | 4-tab analytical dossier | Legislative footprint, transmission, companies | `industry-detail.test.tsx` |
| **55** | Macroeconomic Sectors Heatmap | `/sectors` / `SectorsContent.tsx` | `/sectors` Main View | Macroeconomic policy transmission heatmap | 13 macro sectors with regulatory intensity | Build verified |
| **56** | 4 Implemented States Registry | `/states` / `StatesContent.tsx` | `/states` Pilot Register | State overview cards with act counts | AP (12), KA (11), KL (11), TS (10) | `states.test.tsx` |
| **57** | 24 Planned Expansion States Matrix | `/states` / `StatesContent.tsx` | `/states` Expansion Table | Expansion roadmap data table | 24 states in Union marked non-production | `states.test.tsx` |
| **58** | State Assembly Detail Dossier | `/states/[state]` / `StateDetailContent.tsx`| `/states/[state]` Header | Jurisdictional dossier header | Assembly details, gazette portal links | `states.test.tsx` |
| **59** | State Assembly Acts Listing | `/states/[state]` / `StateDetailContent.tsx`| `/states/[state]` Tab 1 | State acts table with gazette links | Complete list of enacted pilot acts | `states.test.tsx` |
| **60** | State Corporate Footprint Table | `/states/[state]` / `StateDetailContent.tsx`| `/states/[state]` Tab 2 | Corporate facilities & land lease table | Corporate operational exposure in state | `states.test.tsx` |
| **61** | Econometric Predictions Screener | `/predictions` / `PredictionsContent.tsx` | `/predictions` Main View | High-density multi-horizon quant screener | Screens all 4,700 prediction records | `predictions.test.tsx` |
| **62** | 5 Event Windows Workbench | `/predictions` / `PredictionsContent.tsx` | `/predictions` Window Filter | Segmented window switcher (`[-1,+1]` to `[-10,+10]`)| Filters across 5 authoritative horizons | `predictions.test.tsx` |
| **63** | CAR Trajectory & Statistical Diagnostics | `/predictions/[id]` / `PredictionDetailContent.tsx`| `/predictions/[predictionId]` View | Interactive event-study trajectory chart | Trajectory curve, p-value, t-statistic | `prediction-detail.test.tsx` |
| **64** | Decision Support Recommendations | `/predictions/[id]` / `PredictionDetailContent.tsx`| `/predictions/[predictionId]` Panel | Decision recommendation box | Preserves 4,700 frozen decision records | `prediction-detail.test.tsx` |
| **65** | Multi-Horizon Comparative Matrix | `/predictions/[id]` / `PredictionDetailContent.tsx`| `/predictions/[predictionId]` Table | 5-window comparison matrix | Side-by-side CAR comparisons | `prediction-detail.test.tsx` |
| **66** | Systemic Legislative Risk Matrix | `/risk` / `RiskContent.tsx` | `/risk` Main View | Systemic risk distribution matrix | Categorizes high, moderate, low risk | `risk.test.tsx` |
| **67** | Portfolio Composite Risk Calculator | `/risk` / `RiskContent.tsx` | `/risk` Calculator Tab | Interactive portfolio sensitivity calculator | Calculates composite regulatory risk | `risk.test.tsx` |
| **68** | 940-Pair Pre-Event Anticipation Analytics | `/anticipation` / `AnticipationContent.tsx`| `/anticipation` Main View | Anticipation screener with tier badges | 940 anticipation scores preserved | `anticipation.test.tsx` |
| **69** | Public News Diffusion Evidence Drawer | `/anticipation` / `AnticipationEvidenceSection.tsx`| `/anticipation` Drawer | Slide-over evidence drawer | Verified news leak chronology & signals | `anticipation.test.tsx` |
| **70** | 5-Tier Portfolio Exposure Workspace | `/portfolio` / `page.tsx` | `/portfolio` Tab 1 | Portfolio exposure workspace | 5 tiers: DIRECT, HIGH, MODERATE, etc. | Build verified |
| **71** | Portfolio Holdings CSV/XLSX Importer | `/portfolio` / `page.tsx` | `/portfolio` Upload Modal | Drag-and-drop CSV parser with validation | Imports ticker, ISIN, shares, weight | Build verified |
| **72** | "Why is this bill relevant?" Modal | `/portfolio` / `page.tsx` | `/portfolio` Relevance Dialog | Grounded AI modal with statutory citations | Explains portfolio exposure rationale | Build verified |
| **73** | Personalized Decision Workspace Feed | `/workspace` / `page.tsx` | `/workspace` Main Feed | Chronological priority intelligence stream | Watched entity changes & alert digest | `workspace.test.tsx` |
| **74** | User Watchlists & Custom Alert Rules | `/watchlists` / `page.tsx` | `/watchlists` Main View | Watchlist manager with alert toggles | Manages entity baskets and thresholds | `watchlists.test.tsx` |
| **75** | Legislative Alerts Severity Center | `/alerts` / `page.tsx` | `/alerts` Main View | Triage inbox (URGENT, ELEVATED, STANDARD)| Grouped alert feed with read/dismiss | `alerts.test.tsx` |
| **76** | Observability Hub (22 Sources Monitored) | `/monitoring` / `MonitoringCenterContent.tsx`| `/monitoring` Main View | Telemetry dashboard for 22 crawlers | Health history, scheduler, uptime | `monitoring.test.tsx` |
| **77** | Invariant Verification & Coverage Audit | `/coverage` / `CoverageContent.tsx` | `/coverage` Main View | Interactive compliance & SHA-256 verifier | Audits all 78 capabilities & baseline | `coverage.test.tsx` |
| **78** | Institutional Report Center (7 Templates) | `/reports` / `page.tsx` | `/reports` Main View | Report generator with live preview | Generates PDF, CSV, XLSX for 7 templates | Build verified |

---

## 3. Summary of Preservation Guarantees

1. **Zero Deprecations:** Exactly **0 of 78 capabilities** are removed, hidden, or deprecated.
2. **Zero Route Loss:** Exactly **35 of 35 App Router routes** remain accessible at identical URL paths.
3. **Zero Analytical Mutation:** All 4,700 predictions, 4,700 decisions, 940 anticipation scores, and 14,100 stakeholder reports remain identical to the frozen SHA-256 reference manifest (`50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`).
4. **Zero Statutory Firewall Breaches:** The State stock prediction firewall (0 predictions for State acts) and the Intelligence corporate firewall (isolation of non-listed entities from quant models) remain strictly enforced.
