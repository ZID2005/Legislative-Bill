# TASK 8.31B — FRONTEND DESIGN SYSTEM & INFORMATION ARCHITECTURE SPECIFICATION

**Document Version:** 1.0.0  
**Status:** COMPLETE / APPROVED FOR IMPLEMENTATION  
**Date:** October 7, 2026  
**System:** Indian Parliamentary Intelligence & Market Impact Prediction Platform  
**Target Milestone:** Task 8.31C (Modern Frontend Implementation)  
**Scope:** Design System, Information Architecture, and UI/UX Specification Only (Zero code changes, zero API changes, zero database migrations, zero feature removals)

---

## 1. Executive Summary & Design Direction Approval

This specification establishes the authoritative architectural blueprint for redesigning the Indian Parliamentary Intelligence and Market Impact Prediction SaaS frontend into an **Institutional Intelligence Workspace** (Direction A, as evaluated in Task 8.31A).

### Key Architectural Tenets:
1. **Direction A — Institutional Intelligence Workspace Approved:**
   The interface transitions from an accumulated "generic AI SaaS dashboard" into an institutional-grade financial and legislative research environment. It fuses the analytical density, tabular precision, and high-contrast scannability of Wall Street research terminals (e.g., FactSet, Bloomberg Government, PitchBook) with modern typography and clean information hierarchy.
2. **Strict Invariant & Capability Preservation (78 / 78 Preserved, 0 Removed):**
   Every single one of the 78 discrete functional capabilities inventoried in `docs/TASK_8_31A_FRONTEND_UX_DATA_ARCHITECTURE_AUDIT.md` is mapped to an authoritative destination in the new architecture. There are **zero feature deprecations or removals**.
3. **Statutory Firewalls Permanently Intact:**
   - **State Legislative Firewall:** State legislation pages (`/states`, `/bills` where `jurisdiction = State`) strictly display qualitative legal dossiers, transmission mechanisms, and operational corporate exposures. **State Stock Predictions = 0** remains an invariant.
   - **Intelligence Company Firewall:** Non-listed intelligence companies (20) and reference entities (3) display corporate footprint, supply chain linkages, and regulatory risks, with quantitative market models permanently disabled and guarded by firewall banners.
4. **Epistemic Classification System Maintained:**
   Every analytical card, metric, table cell, and LLM output enforces strict epistemic taxonomy:
   - `[FACT]`: Official Gazette records, Lok Sabha / Rajya Sabha parliamentary records, PRS legislative tracking data.
   - `[OBSERVED]`: Historical trading figures, BSE/NSE market prices, introduction dates, gazette notification timestamps.
   - `[DERIVED]`: Econometric calculations, Ordinary Least Squares (OLS) market model residuals, Cumulative Abnormal Return (CAR), t-statistics.
   - `[INTERPRETATION]`: Grounded Groq AI executive summaries, policy analysis, stakeholder perspectives.
   - `[PREDICTION]`: Forward-looking econometric event-study projections across the 5 authoritative horizons (`[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`).
5. **No System Alterations in Task 8.31B:**
   As mandated by the hard constraints:
   - No frontend implementation code modified.
   - No backend APIs altered.
   - No database migration executed (filesystem repository layer preserved).
   - Analytical models, weights, predictions, and frozen baseline (`50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`) remain 100% frozen.

---

## 2. Final Navigation Architecture

### 2.1 Navigation Strategy & Problem Resolution
The UX audit in Task 8.31A identified four key navigation challenges:
- *Mega-menu cognitive overload:* 9 items under a single "Discover" dropdown created excessive visual friction.
- *Route ambiguity:* Overlapping paths (`/explorer` vs `/bills`, `/live-discovery` vs `/latest-bills`) confused users regarding canonical records vs discovery tools.
- *Buried daily workspace:* `/workspace` was hidden within a dropdown rather than serving as the user's primary daily operating dashboard.
- *Dead-end placeholders:* Routes like `/companies`, `/states`, `/bills/compare`, and `/ai-analyst` showed placeholder banners despite existing backend data.

The new **Institutional Navigation Architecture** consolidates the application into **5 Logical Macro Workspaces**, alongside **4 Global Institutional Anchors**:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [⚖ LEGISINTEL]  [Workspace]  |  [Legislation ▾]  [Markets & Risk ▾]  [Entities ▾]  [Portfolio]  [Reports] │
│                                         Search [⌘K]   [Live Pulse 22/22]   [Notifications 🔔]   [User ▾]│
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### 2.2 Global Primary Navigation Bar (Desktop >= 1024px)

| Navigation Item | Route / Action | Type | Contents / Destinations | Target Persona |
|---|---|---|---|---|
| **Platform Brand / Home** | `/` | Direct Link | Institutional Landing Page, Value Proposition, Public Key Metrics | All / Prospects |
| **Workspace** | `/workspace` | Direct Anchor (Primary) | "What changed since I last looked?", Personal Watched Bills/Companies, Priority Feed | Daily Active Users |
| **Legislation ▾** | Dropdown Hub | Group Dropdown (7 Items) | • **Legislative Explorer** (`/explorer` - Dual-view multi-facet discovery)<br>• **Bills Directory** (`/bills` - Canonical parliamentary act registry)<br>• **Latest Enactments** (`/latest-bills` - Central & State bills introduced)<br>• **Upcoming Calendar** (`/upcoming-legislation` - Parliamentary session agenda)<br>• **Live Intake Feed** (`/live-discovery` - Unmodelled gazette intake)<br>• **Bill Comparison** (`/bills/compare` - Side-by-side provision diff)<br>• **State Assemblies** (`/states` - Sub-national legislative coverage) | Legal Counsel, Policy Researchers |
| **Markets & Risk ▾** | Dropdown Hub | Group Dropdown (3 Items) | • **Market Predictions** (`/predictions` - 4,700 event-study records & horizon comparator)<br>• **Legislative Risk Matrix** (`/risk` - Systemic risk classification & ISIN calculator)<br>• **Pre-Event Anticipation** (`/anticipation` - 940 diffusion scores & news evidence) | Quantitative PMs, Chief Risk Officers |
| **Entities ▾** | Dropdown Hub | Group Dropdown (3 Items) | • **Corporate Directory** (`/companies` - 70 entities: 47 Quant + 20 Intel + 3 Ref)<br>• **Industries Taxonomy** (`/industries` - 13 sectors & granular industries)<br>• **Macro Economic Sectors** (`/sectors` - Macro policy transmission map) | Equity Analysts, Sector Specialists |
| **Portfolio** | `/portfolio` | Direct Anchor | Portfolio Holdings Exposure, CSV Upload, Relevance Explainer, Impact Reports | Asset Managers, CIOs |
| **Reports** | `/reports` | Direct Anchor | Institutional Downloadable Reports Catalog, 7 Audit Templates, PDF/CSV Exports | Executives, Compliance |

#### Right Utility Controls (Desktop):
1. **Global Search Input (`⌘K`):** Instant search trigger with category badge hints and keyboard navigation.
2. **Live Monitoring Pulse Indicator (`/monitoring`):** Live badge showing real-time crawler health (`22/22 Sources Active` with emerald heartbeat dot), linking directly to the Monitoring Center.
3. **Notification Bell (`/notifications`):** Unread counter badge showing active alerts with popover preview for quick triage.
4. **AI Terminal Quick-Launch (`/ai-analyst`):** Sparkle badge button launching the Grounded AI Analyst drawer/terminal from anywhere in the app.
5. **Organization & User Profile (`/settings`):** User avatar showing tenant name, current role (`ADMIN`, `MEMBER`), quick links to `/settings`, `/coverage`, and `/login` (Sign Out).

---

### 2.3 Mobile Navigation Architecture (< 1024px)

```
┌────────────────────────────────────────────────────────┐
│ [⚖ LegisIntel]           [⌘K] [🔔] [AI] [☰ Menu]       │
├────────────────────────────────────────────────────────┤
│ [Quick Bar:  Workspace  |  Bills  |  Predictions  |  Port]│
└────────────────────────────────────────────────────────┘
```

1. **Compact Sticky Mobile Header (Height: 52px):**
   - Brand logo (compact shield + text).
   - Quick search button (triggers full-screen mobile search modal).
   - Unread notifications pill.
   - Hamburger icon (triggers full-height slide-over drawer).
2. **Horizontal Mobile Quick-Scroll Bar (Height: 38px):**
   - Direct touch tabs for the 5 most accessed operational pages: `Workspace`, `Bills`, `Predictions`, `Portfolio`, `Alerts`.
3. **Full-Screen Slide-Over Drawer:**
   - **Section 1: Daily Intelligence:** Workspace, Notifications, Alerts, Watchlists.
   - **Section 2: Legislative Registry:** Explorer, Bills, States, Latest, Upcoming, Compare.
   - **Section 3: Econometric & Risk:** Predictions, Risk Matrix, Pre-Event Anticipation.
   - **Section 4: Corporate Universe:** Companies, Industries, Sectors.
   - **Section 5: Executive Tools:** Portfolio, Reports, AI Analyst, Monitoring Center, Coverage.
   - **Footer:** Organization Switcher, User Settings, Session Sign Out.

---

### 2.4 Command Palette Search Architecture (`⌘K`)

The search modal is elevated into an institutional Command Palette supporting fuzzy search and entity filtering:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🔍 Type a bill, company, ticker, ISIN, or command...                     [ESC]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│ Filters:  [All]  [/b Bills]  [/c Companies]  [/s Sectors]  [/p Predictions]     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ RECENT SEARCHES                                                                 │
│ • Digital Personal Data Protection Act, 2023                        Central Bill │
│ • Tata Consultancy Services (TCS)                              Quant Company    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ LEGISLATIVE BILLS (Central & State)                                             │
│ 📜 Energy Conservation (Amendment) Act, 2022 (Central)              [L1 Modelled]│
│ 📋 Telangana Gaming (Amendment) Act, 2017 (State)                 [Qualitative] │
├─────────────────────────────────────────────────────────────────────────────────┤
│ CORPORATE ENTITIES (47 Quantitative + 20 Intelligence)                          │
│ 📈 Reliance Industries Limited (RELIANCE.NS)                     Quant Security │
│ 🏢 National Payments Corporation of India (NPCI)                Intel Company   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ SYSTEM COMMANDS                                                                 │
│ ⚡ Go to Portfolio Exposure Workspace                              /portfolio    │
│ ⚡ Open System Source Monitoring Center                             /monitoring   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

- **Prefix Commands:**
  - `/b <query>`: Scope search exclusively to Central and State Acts.
  - `/c <query>`: Scope search to Master Companies (ISIN, Ticker, or Corporate Name).
  - `/s <query>`: Scope search to Macro Sectors and Granular Industries.
  - `/p <query>`: Scope search to Market Impact Predictions.
  - `> <command>`: System navigation shortcuts (e.g., `> export`, `> alerts`, `> audit`).
- **Keyboard Navigation:** Full arrow-key up/down navigation, `Enter` to open, `Tab` to autocomplete prefix, `Esc` to dismiss.

---

## 3. Page-by-Page Redesign Specification

Below is the exhaustive specification for all 35 routes across the platform.

---

### 3.1 Institutional Landing Page (`/`)
- **Route:** `/` (`frontend/app/page.tsx`)
- **Primary Persona:** Prospective institutional client, equity analyst, compliance officer.
- **Primary Objective:** Establish authority, institutional trust, statutory firewalls, and multi-tenant entry.
- **Key Layout Zones:**
  1. *Institutional Header:* Platform brand, live baseline metrics badge (66 Acts, 70 Companies, 4,700 Predictions), Sign In / Launch buttons.
  2. *Authoritative Hero:* High-contrast typography ("Indian Parliamentary Intelligence & Market Impact Terminal"), sub-headline highlighting econometric event study methodology and PRS statutory indexing.
  3. *Authoritative Metric Strip:* 6 high-density cards displaying verified invariants:
     - 20 Central Production Acts
     - 44 State Assembly Acts
     - 47 Quantitative Securities (NSE/BSE)
     - 4,700 Horizon Predictions (Zero State Predictions)
     - 104 Documented Corporate Exposures
     - 22 Legislative Official Sources Monitored
  4. *Statutory Firewall Guarantees Strip:* 2 formal callouts explaining the State Stock Prediction Firewall and the Non-Listed Intelligence Company Firewall.
  5. *Core Capabilities Grid:* 4 functional pillars: Legislative Dossiers, Econometric Event Studies, Corporate Exposure Mapping, and Grounded Groq AI Intelligence.
  6. *Interactive Tour CTA & Footer:* Direct links to `/onboarding`, `/login`, and `/workspace`.
- **States:**
  - *Loading:* Static Server Component (instant load, 0ms latency).
  - *Auth Detected:* Hero CTA dynamically changes from "Sign In" to "Enter Workspace →".

---

### 3.2 Personalized Workspace (`/workspace`)
- **Route:** `/workspace` (`frontend/app/workspace/page.tsx`)
- **Primary Persona:** Active Daily User (Equity Analyst, Policy Director).
- **Primary Objective:** Provide the user's primary operating dashboard answering: *"What changed since I last logged in?"*
- **Key Layout Zones:**
  1. *Workspace Header:* Tenant organization indicator, user greeting, last synced timestamp, "Refresh Feed" button, "New Watchlist" shortcut.
  2. *Quick Ticker Strip:* 4 compact stat pills:
     - Watched Bills Count
     - Watched Companies Count
     - Unread Urgent Alerts (with Rose badge)
     - Source Crawlers Status (22/22 Active)
  3. *Two-Column Command Layout (70% / 30% split on desktop):*
     - **Left Main Stream (70%):**
       - Filter Bar: All, Watched Only, Bills, Companies, High Impact.
       - *Chronological Intelligence Feed:* Cards displaying detected changes, procedural stage advances, and new anticipation signals. Each item includes explicit epistemic badges (`[OBSERVED]`, `[FACT]`, `[PREDICTION]`).
     - **Right Operational Panel (30%):**
       - *Priority Action Items:* Pending legislative amendments affecting portfolio holdings.
       - *Active Watchlists Quick Access:* Compact list of user watchlists with item counts.
       - *Embedded Groq AI Workspace Assistant:* Compact conversational input for asking questions about the active change feed.
- **Empty State:** If user has no watchlists, displays an onboarding prompt: "No entities tracked yet. Add bills or companies to your watchlist to personalize your feed."
- **Error State:** Dismissible error banner with retry button.

---

### 3.3 Platform Overview Dashboard (`/overview`)
- **Route:** `/overview` (`frontend/app/overview/page.tsx`)
- **Primary Persona:** Senior Research Analyst, Investment Director.
- **Primary Objective:** Comprehensive system-wide overview of the entire legislative and econometric landscape.
- **Key Layout Zones:**
  1. *Executive Breadcrumbs & Title:* "Platform Overview & Econometric Coverage".
  2. *Coverage Metrics Grid (6 High-Density Stat Cards):*
     - Central Acts: 20
     - State Acts: 44 (AP, KA, KL, TS)
     - Quant Companies: 47
     - Market Predictions: 4,700
     - Corporate Exposures: 104
     - System Invariants: Verified 100%
  3. *Two-Tier Capability Breakdown:* Side-by-side cards comparing Level 1 Quantitative Modeling (Central) vs Level 2 Qualitative Intelligence (State).
  4. *Active Legislative Landscape Table:* Compact 10-row table of recently enacted or updated bills with jurisdiction, status, corporate exposure count, and model tier.
  5. *Market Impact Snapshot:* Top 5 positive and top 5 negative predicted CAR movers across the `[-5,+5]` window.
  6. *Corporate Exposure Network Snapshot:* Most exposed corporations across Central and State legislation.
  7. *Monitoring Health Status Strip:* Source crawler health indicator linking to `/monitoring`.
- **States:**
  - *Loading:* Skeleton grids with shimmer animation.
  - *Data Source:* Live backend `/api/v1/coverage`, `/api/v1/bills`, `/api/v1/predictions`.

---

### 3.4 Legislative Explorer (`/explorer`)
- **Route:** `/explorer` (`frontend/app/explorer/page.tsx`)
- **Primary Persona:** Legal Counsel, Regulatory Affairs Specialist, Equity Research Analyst.
- **Primary Objective:** Power-user search and multi-facet filtering engine for all 66 acts and 70 companies.
- **Key Layout Zones:**
  1. *Explorer Top Toolbar:*
     - Full-text search input with instantaneous client debouncing.
     - View Switcher Toggle: **Table Mode (Default / Dense)** vs **Card Mode (Detailed)**.
     - Active filter chips strip with "Clear All" button.
     - Total results counter ("Showing 66 of 66 Legislative Acts").
  2. *Two-Column Layout (240px Sidebar + Fluid Content):*
     - **Left Filter Sidebar:**
       - Jurisdiction: Central (20), State (44 - AP, KA, KL, TS).
       - Enactment Status: Enacted, Passed, Bill Pending.
       - Modeling Level: Level 1 Quantitative, Level 2 Qualitative.
       - Macro Sectors: Energy, Financials, Tech, Manufacturing, Agriculture, etc.
       - Predictions Available: Yes, No (Firewalled).
     - **Right Results View:**
       - **Table Mode (Institutional Default):** Dense tabular rows showing Bill Title, Act ID, Jurisdiction, Ministry/State, Year, Exposures, Predictions Badge, Actions (`View Dossier`, `Add Watchlist`).
       - **Card Mode:** Detailed cards showing provisions summary and affected corporations.
  3. *Bottom Pagination Bar:* Standard institutional pagination with page size selector (15, 30, 50).
- **States:**
  - *Empty State:* "No legislation matches the selected filters. Reset filters to view all 66 acts."

---

### 3.5 Bills Directory (`/bills`)
- **Route:** `/bills` (`frontend/app/bills/page.tsx`)
- **Primary Persona:** Research Analyst, Legal Counsel, Compliance Auditor.
- **Primary Objective:** Canonical statutory index of Central Parliament and State Assembly enactments.
- **Key Layout Zones:**
  1. *Header & Index Tabs:* Tabs for `All Legislation (66)`, `Central Parliament (20)`, `State Assemblies (44)`.
  2. *Search & Filter Row:* Keyword search, ministry/state dropdown, year selector.
  3. *Institutional Statutory Table:*
     - Columns: Bill / Act Name, Jurisdiction, Enactment Date, Ministry / Assembly, Key Provisions Count, Documented Corporate Exposures, Capability Tier, Action.
     - Sortable by date, title, and exposures.
  4. *State Firewall Disclaimer Banner:* Prominently displayed when viewing the State tab, reinforcing that State legislation does not trigger stock predictions.
- **Component Refinement:** Differentiates itself from `/explorer` by functioning as a formal gazette catalog rather than a multi-entity cross-discovery engine.

---

### 3.6 Legislative Dossier (`/bills/[billId]`)
- **Route:** `/bills/[billId]` (`frontend/app/bills/[billId]/page.tsx`)
- **Primary Persona:** Equity Analyst, Legal Counsel, Chief Risk Officer.
- **Primary Objective:** Definitive, authoritative single-bill intelligence hub unifying statutory text, corporate exposures, econometric predictions, and stakeholder analysis.
- **Key Architecture Change (Tab Consolidation):**
  Instead of 12 horizontal tabs that overflow and hide content, the dossier is consolidated into **5 Cohesive Master Workspaces** with a persistent contextual intelligence right sidebar:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ BILL HEADER: Energy Conservation (Amendment) Act, 2022          [Central Level 1] [ENACTED] │
│ Ministry: Power | Enacted: Dec 2022 | Gazette: PRS Verified | Official PDF: [Download ⤓]   │
├──────────────────────────────────────────────────────────────────┬──────────────────────────┤
│ WORKSPACE TABS:                                                  │ CONTEXTUAL SIDEBAR       │
│ [1. Executive & Provisions] [2. Corporate Exposures]            │ • Procedural Timeline    │
│ [3. Market & Anticipation]  [4. Stakeholder Perspectives]       │ • Official Gazette Links │
│ [5. Statutory Provenance]                                        │ • Related Acts           │
├──────────────────────────────────────────────────────────────────┤ • Groq AI Copilot        │
│ TAB PANEL CONTENT:                                               │   [Ask Question...]      │
│ (High-density provisions, exposure tables, CAR charts)           │                          │
└──────────────────────────────────────────────────────────────────┴──────────────────────────┘
```

#### Detailed Workspace Tabs:
1. **Tab 1: Executive Dossier & Statutory Provisions:**
   - Executive Summary with epistemic label `[INTERPRETATION]`.
   - Key Statutory Provisions Table: Section number, regulatory requirement, penalty clause, enforcement authority.
   - "What Changed" Statutory Diff Viewer: Section-by-section comparison against predecessor act (if amending legislation).
2. **Tab 2: Corporate & Sector Exposures:**
   - Documented Corporate Exposures Table: Company name, ISIN, Sector, Transmission Channel (Revenue/Cost/CapEx), Regulatory Impact Score, Evidence Citation.
   - Affected Economic Sectors Breakdown.
3. **Tab 3: Econometric Market Impact & Anticipation:**
   - *If Central Bill (Level 1):*
     - Predictions Table: 47 Quantitative Securities, CAR %, t-stat, Confidence %, Direction (`POSITIVE`, `NEGATIVE`, `NEUTRAL`), Market-Moving flag.
     - Multi-Horizon Selector: `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`.
     - Anticipation Diagnostics: Pre-event diffusion score, media attention trends, parliamentary bulletin mentions.
   - *If State Bill (Level 2):*
     - `StatePredictionFirewall` Banner: Explicit statutory explanation why market predictions are disabled for sub-national acts.
4. **Tab 4: Multi-Perspective Stakeholder Intelligence:**
   - Persona Grid:
     - *Investor Persona:* Capital allocation implications, earnings sensitivity, compliance risks.
     - *Business / Industry Persona:* Operating cost changes, compliance burden, supply chain adjustments.
     - *Public / Societal Persona:* Consumer rights, environmental protection, fee structures.
   - Epistemic tags strictly labeled on each perspective.
5. **Tab 5: Document Provenance & Verification:**
   - Official Gazette PDF viewer (`DocumentViewer.tsx`).
   - PRS Legislative Research tracking metadata.
   - Content SHA-256 hash, ingestion timestamp, and auditor verification status.

---

### 3.7 Bill Comparison Workbench (`/bills/compare`)
- **Route:** `/bills/compare` (`frontend/app/bills/compare/page.tsx`)
- **Primary Persona:** Legal Analyst, Regulatory Strategy Lead.
- **Primary Objective:** Side-by-side analytical comparison of two legislative enactments (upgrades existing placeholder).
- **Key Layout Zones:**
  1. *Dual Bill Selector:* Left Bill picker combobox vs Right Bill picker combobox.
  2. *Metadata Comparison Grid:* Side-by-side comparison of Jurisdiction, Ministry/Assembly, Year, Status, Regulatory Scope.
  3. *Provisions Diff Table:* Comparative mapping of statutory levers, penalties, and compliance mandates.
  4. *Corporate Exposure Overlap Matrix:* Highlights companies affected by both enactments vs uniquely exposed companies.
  5. *Market Impact Delta View:* (If both are Central Level 1 bills) Comparative CAR delta across the 5 event horizons.

---

### 3.8 Latest Bills Feed (`/latest-bills`)
- **Route:** `/latest-bills` (`frontend/app/latest-bills/page.tsx`)
- **Primary Persona:** Legislative Monitoring Specialist.
- **Primary Objective:** Chronological feed of newly introduced and enacted parliamentary bills.
- **Key Layout Zones:**
  1. *Feed Controls:* Time range filter (Last 7 days, 30 days, 90 days), Jurisdiction pills (All, Central, States).
  2. *Chronological Timeline Cards:* Date-grouped cards displaying introduction date, house of parliament, status, and summary.
  3. *Data Source Notice:* Badged as `[LIVE INTAKE]`, noting that newly introduced bills undergo validation before econometric modeling.

---

### 3.9 Upcoming Parliamentary Calendar (`/upcoming-legislation`)
- **Route:** `/upcoming-legislation` (`frontend/app/upcoming-legislation/page.tsx`)
- **Primary Persona:** Public Affairs Officer, Portfolio Strategist.
- **Primary Objective:** Track parliamentary session dates, scheduled committee meetings, and anticipated legislative agendas.
- **Key Layout Zones:**
  1. *Session Banner:* Current session status (e.g., Budget Session, Monsoon Session, Winter Session) with official dates.
  2. *Scheduled Business Table:* Bill name, procedural milestone (Introduction, Committee Report, Discussion, Voting), scheduled date, confidence rating.
  3. *Rule of Truth Banner:* Strict disclaimer stating that calendar entries are sourced exclusively from official Lok Sabha / Rajya Sabha provisional calendars, with zero fabricated projections.

---

### 3.10 Live Legislative Discovery (`/live-discovery`)
- **Route:** `/live-discovery` (`frontend/app/live-discovery/page.tsx`)
- **Primary Persona:** Data Operations, Regulatory Intelligence Lead.
- **Primary Objective:** Real-time intake stream of newly discovered legislative records from automated crawlers.
- **Key Layout Zones:**
  1. *Intake Status Bar:* Active crawlers running, last check timestamp, newly discovered records in last 24h.
  2. *Live Stream Table:* Discovered Date, Bill / Gazette Title, Source Portal, Ingestion Status (`PENDING_AUDIT`, `VERIFIED`, `REJECTED`), Content Checksum, Actions.
  3. *Model Firewall Notice:* Prominent badge confirming that live intake records are tagged `KNOWLEDGE_ONLY` and cannot mutate frozen baseline models.

---

### 3.11 Corporate Intelligence Directory (`/companies`)
- **Route:** `/companies` (`frontend/app/companies/page.tsx`)
- **Primary Persona:** Equity Analyst, Buy-Side Portfolio Manager.
- **Primary Objective:** Master directory of the 70 corporate entities across quantitative and intelligence tiers (upgrades placeholder).
- **Key Layout Zones:**
  1. *Directory Header:* Total universe metrics (70 Master Companies: 47 Quantitative Securities, 20 Intelligence-Only Entities, 3 Reference Entities).
  2. *Universe Filter Strip:* All (70), Quantitative Securities (47), Intelligence Entities (20), Reference Benchmarks (3).
  3. *Sector Dropdown & Search:* Search by company name, NSE ticker, or ISIN.
  4. *Institutional Corporate Table:*
     - Columns: Company Name, Ticker / ID, ISIN, Sector, Industry, Universe Tier (`QUANTITATIVE` vs `INTELLIGENCE`), Active Legislative Exposures Count, Predicted Market Sensitivity (`HIGH`, `MEDIUM`, `LOW`, `FIREWALLED`), Actions.
  5. *Quick Tear-Sheet Modal Trigger:* Click row to view quick metrics or navigate to full profile.

---

### 3.12 Corporate Intelligence Profile (`/companies/[companyId]`)
- **Route:** `/companies/[companyId]` (`frontend/app/companies/[companyId]/page.tsx`)
- **Primary Persona:** Portfolio Manager, Equity Research Analyst.
- **Primary Objective:** Comprehensive corporate dossier evaluating legislative exposure, economic transmission mechanisms, and market sensitivity.
- **Key Layout Zones:**
  1. *Corporate Header:* Company name, ISIN, NSE/BSE ticker, sector, ownership, Universe Badge (`QUANTITATIVE` vs `INTELLIGENCE`), "Add to Watchlist" button.
  2. *Consolidated Workspace Tabs (4 Tabs):*
     - **Tab 1: Legislative Exposure Matrix & Footprint:**
       - All bills affecting this company (Central & State).
       - Exposure Transmission Details: Revenue sensitivity, CapEx obligations, compliance cost impact.
       - Geographic & State Operational Footprint: Manufacturing plants, key operating states (AP, KA, KL, TS), state-level assembly act exposure.
     - **Tab 2: Economic Transmission Architecture:**
       - Flow Diagram: Statutory Lever → Operational Variable → Financial Metric → Market Valuation.
     - **Tab 3: Econometric Market Impact (Dual Mode):**
       - *Mode A (If 47 Quantitative Securities):* Event study CAR projections, t-stats, horizon comparison across all 20 Central bills, decision support recommendations.
       - *Mode B (If 20 Intelligence Entities):* `IntelligenceCompanyFirewall` banner explaining non-listed status and isolation from financial market models.
     - **Tab 4: Corporate Provenance & Grounded AI Analyst:**
       - Embedded Groq AI analyst for corporate questions.
       - Annual report citations, regulatory filing links, peer comparison group.

---

### 3.13 Industries Directory (`/industries`)
- **Route:** `/industries` (`frontend/app/industries/page.tsx`)
- **Primary Persona:** Sector Strategist, Equity Research Analyst.
- **Primary Objective:** Interactive taxonomy connecting parliamentary legislation to granular economic industries.
- **Key Layout Zones:**
  1. *Sector Filter & Search Bar:* Search across all granular industries and sector mappings.
  2. *Macro Sector Grouping:* Grid of industry cards grouped by parent sector (Energy & Utilities, Financial Services, Information Technology, Healthcare, Consumer Goods, Industrials, etc.).
  3. *Industry Cards:* Each card displays Industry Name, Parent Sector, Number of Associated Companies, Active Legislative Acts Count, Average Legislative Risk Tier.

---

### 3.14 Industry Detail Dossier (`/industry/[industryId]` & `/industries/[id]`)
- **Route:** `/industry/[industryId]` and `/industries/[id]` (both supported via alias)
- **Primary Persona:** Sector Specialist, Risk Committee Member.
- **Primary Objective:** In-depth 13-section dossier evaluating industry-level legislative transmission, corporate constituents, and regulatory headwinds.
- **Key Layout Zones:**
  1. *Industry Executive Header:* Industry title, parent sector, constituent companies count, total legislative exposures count.
  2. *Executive Summary (Section A):* Macro legislative posture and regulatory environment overview.
  3. *Economic Transmission Mechanism (Section C):* Diagram connecting policy levers to industry cost structures.
  4. *Corporate Constituents Table (Section D):* Table of all companies operating within this industry, showing ISIN, ticker, and exposure count.
  5. *Legislative Exposures Table (Section E):* Central and State acts impacting this industry.
  6. *Grounded AI Sector Analyst:* Contextual assistant answering industry regulatory questions.

---

### 3.15 Economic Sectors Directory (`/sectors`)
- **Route:** `/sectors` (`frontend/app/sectors/page.tsx`)
- **Primary Persona:** Chief Investment Officer, Macro Strategist.
- **Primary Objective:** Macroeconomic view of legislative intensity and policy transmission across the Indian economy.
- **Key Layout Zones:**
  1. *Macro Policy Heatmap:* Visual intensity map showing which economic sectors face the heaviest legislative intervention.
  2. *Sector Comparison Table:* Sector name, active bills count, total exposed market capitalization, aggregate risk index, constituent industries.
  3. *Quick Navigation:* Direct drill-down links to constituent industry dossiers.

---

### 3.16 State Coverage Directory (`/states`)
- **Route:** `/states` (`frontend/app/states/page.tsx`)
- **Primary Persona:** Regional Regulatory Analyst, Policy Director.
- **Primary Objective:** Sub-national legislative coverage overview (upgrades placeholder).
- **Key Layout Zones:**
  1. *State Coverage Summary Bar:* 4 Implemented Pilot States (44 Production Acts: Andhra Pradesh 12, Karnataka 11, Kerala 11, Telangana 10) + 24 Planned States.
  2. *Strict State Firewall Banner:* Universal notice reiterating **State Stock Predictions = 0** across all sub-national jurisdictions.
  3. *Implemented State Cards (4 States):*
     - Andhra Pradesh (AP): 12 Acts, 26 Corporate Exposures, Official AP Gazette Ingestion.
     - Karnataka (KA): 11 Acts, 22 Corporate Exposures, Karnataka Gazette Ingestion.
     - Kerala (KL): 11 Acts, 18 Corporate Exposures, Kerala Gazette Ingestion.
     - Telangana (TS): 10 Acts, 20 Corporate Exposures, Telangana Gazette Ingestion.
  4. *Planned Union Jurisdictions Grid:* Visual matrix of the remaining 24 Indian states and union territories marked as `PLANNED`.

---

### 3.17 State Detail Dossier (`/states/[state]`)
- **Route:** `/states/[state]` (`frontend/app/states/[state]/page.tsx`)
- **Primary Persona:** Regional Counsel, Operations Risk Manager.
- **Primary Objective:** State assembly enactments, official gazette links, and corporate exposures (upgrades placeholder).
- **Key Layout Zones:**
  1. *State Header:* State name, capital, legislative assembly name, total enacted acts count, corporate exposures count.
  2. *State Assembly Acts Table:* State act title, act number, enactment year, key statutory provisions, gazette PDF download link.
  3. *State Corporate Operational Exposure Table:* Companies with operating facilities or regulatory liability within this state.
  4. *State Firewall Permanent Card:* Explains why sub-national acts are preserved as qualitative intelligence dossiers rather than equity prediction models.

---

### 3.18 Market Predictions Engine (`/predictions`)
- **Route:** `/predictions` (`frontend/app/predictions/page.tsx`)
- **Primary Persona:** Quantitative Portfolio Manager, Equity Analyst.
- **Primary Objective:** Deep econometric exploration of 4,700 event-study market impact predictions.
- **Key Architecture Change (Split-Screen Screener & Workbench):**

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ PREDICTIONS ENGINE  [4,700 Econometric Records]  [5 Authoritative Event Windows]      │
│ [FACT: OLS Model] [OBSERVED: BSE/NSE Returns] [DERIVED: CAR & t-stat] [PREDICTION: CAR] │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ HORIZON WORKBENCH:  [-1,+1]  |  [-3,+3]  |  [-5,+5]  |  [-5,+10]  |  [-10,+10]         │
├─────────────────────────────────────────────────────────────┬──────────────────────────┤
│ PREDICTION SCREENER (Dense Sortable Table):                 │ CAR TRAJECTORY INSPECTOR │
│ Filter: [Bill ▾] [Company ▾] [Direction ▾] [Moving Only ☐]   │ Bill: Energy Conserv.    │
│ • Energy Conservation ↔ Tata Steel | CAR +4.2% | t=2.85 | + │ Co: Tata Power (TPWR)   │
│ • DPDP Act, 2023 ↔ Infosys Ltd     | CAR -1.8% | t=-1.92| - │ ──────────────────────── │
│ • Mines & Minerals ↔ Vedanta Ltd   | CAR +6.1% | t=3.41 | + │ Horizon Trajectory Chart │
│ • Biological Diversity ↔ Sun Pharma| CAR +0.4% | t=0.52 | = │ [-10] ----0---- [+10]    │
│ (Showing 1 - 25 of 4,700 records)               [Export CSV]│ Decision: OVERWEIGHT     │
└─────────────────────────────────────────────────────────────┴──────────────────────────┘
```

1. *Epistemic Classification Bar:* Sticky header explaining the statistical methodology (OLS Market Model, Estimation Window `[-120, -21]`, Benchmark Beta against NIFTY 500).
2. *Authoritative Horizon Tabs:* Quick switch between the 5 event windows (`[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`).
3. *Prediction Screener Table:*
   - Columns: Bill Title, Company Name, NSE Ticker, Horizon, CAR (%), t-statistic, p-value, Direction (`POSITIVE`, `NEGATIVE`, `NEUTRAL`), Market-Moving Flag, Confidence %, Actions.
   - Fully sortable headers with tabular monospace numerals.
4. *Side Inspector (Trajectory & Decision Support):* Clicking any prediction displays its CAR curve across all 5 horizons and its corresponding Decision Support record.
5. *Grounded Groq AI Analyst Drawer:* Contextual panel providing grounded econometric synthesis with explicit persona toggles.

---

### 3.19 Prediction Detail View (`/predictions/[predictionId]`)
- **Route:** `/predictions/[predictionId]` (`frontend/app/predictions/[predictionId]/page.tsx`)
- **Primary Persona:** Quantitative Analyst, Econometric Auditor.
- **Primary Objective:** Comprehensive statistical diagnostic teardown for a single bill-company-horizon prediction.
- **Key Layout Zones:**
  1. *Prediction Header:* Bill name, company name, ISIN, event horizon window, predicted CAR %, t-stat, confidence tier.
  2. *Statistical Diagnostics Cards:*
     - Cumulative Abnormal Return (CAR) with 95% confidence intervals.
     - Student's t-statistic and two-tailed p-value.
     - Beta ($\beta$) relative to NIFTY 500 index.
     - Residual standard error ($\sigma_\epsilon$).
     - Estimation window length (100 trading days).
  3. *Decision Support Recommendation:* Structured output (Action recommendation: `OVERWEIGHT`, `NEUTRAL`, `UNDERWEIGHT`, `HEDGE_EXPOSURE`, rationale bullets, tail risk factors).
  4. *Multi-Horizon Comparative Table:* Shows the other 4 horizons for this exact bill-company pair to evaluate mean-reversion vs trend continuation.

---

### 3.20 Legislative Risk Matrix (`/risk`)
- **Route:** `/risk` (`frontend/app/risk/page.tsx`)
- **Primary Persona:** Chief Risk Officer, Investment Committee Member.
- **Primary Objective:** Multi-dimensional legislative risk classification across bills, companies, and portfolios.
- **Key Layout Zones:**
  1. *Systemic Risk Summary Cards:* Distribution of risk across VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH bands.
  2. *Legislative Risk Matrix (Heatmap):* Sector (Y-axis) vs Risk Severity Band (X-axis).
  3. *Bill Risk & Company Risk Tabs:* Tabular rankings of highest risk legislation and most exposed corporations.
  4. *Interactive Portfolio Risk Calculator:*
     - Select from saved user watchlists or enter custom ISIN list.
     - Calculates composite weighted risk score (0.0 to 1.0).
     - Deconstructs score into: Procedural Uncertainty Weight (0.25), Pre-Event Anticipation Weight (0.25), Tail Magnitude Weight (0.25), Directional Conflict Weight (0.25).

---

### 3.21 Pre-Event Anticipation Analytics (`/anticipation`)
- **Route:** `/anticipation` (`frontend/app/anticipation/page.tsx`)
- **Primary Persona:** Regulatory Compliance Officer, Quantitative Strategist.
- **Primary Objective:** Evaluates pre-event market information diffusion and news flow prior to bill introduction.
- **Key Layout Zones:**
  1. *Mandatory Legal Disclaimer Banner:* Prominently states that anticipation analytics track public media diffusion and econometric price discovery, strictly **not** allegations of insider trading or statutory violations.
  2. *Anticipation Tier Summary Cards:*
     - Tier 1: Strong Diffusion (Pre-event CAR > 2.0%, news volume > 90th percentile)
     - Tier 2: Moderate Diffusion
     - Tier 3: Emerging Diffusion
     - Tier 4: Baseline / Unanticipated
  3. *Two-Panel Interactive Master-Detail Layout:*
     - **Left Panel (Score Table):** 940 bill-company anticipation scores with z-scores and tier badges.
     - **Right Panel (Evidence Drawer):** Selecting a pair immediately displays its public news articles, parliamentary bulletin mentions, publication timestamps, and search volume trend lines.

---

### 3.22 Portfolio Legislative Exposure (`/portfolio`)
- **Route:** `/portfolio` (`frontend/app/portfolio/page.tsx`)
- **Primary Persona:** Wealth Manager, Portfolio Manager, Family Office CIO.
- **Primary Objective:** Connects a user's actual portfolio holdings to relevant legislation with 5 relevance tiers.
- **Key Layout Zones:**
  1. *Portfolio Header:* Portfolio selector dropdown, aggregate portfolio value, total positions count, active exposed positions count, "Import Holdings (CSV/XLSX)" button, "Generate Impact Report" button.
  2. *Relevance Tier Breakdown Cards:*
     - DIRECT Exposure (Immediate statutory name mention / single-industry monopoly)
     - HIGH Exposure (Core operational mandate change)
     - MODERATE Exposure (Supply chain / compliance impact)
     - INDIRECT Exposure (Macro economic feedback)
     - INFORMATIONAL (General statutory awareness)
  3. *Two-Column Workspace Layout:*
     - **Left Column (Holdings Table):** Security Name, ISIN, Ticker, Shares, Weight %, Exposed Bills Count, Highest Relevance Tier, Model Status (`MODELLED`, `KNOWLEDGE_ONLY`, `NOT_ELIGIBLE`).
     - **Right Column (Active Legislative Impacts):** Stream of bills impacting portfolio positions.
  4. *Integrated Modals:*
     - *Holdings Import Modal:* Drag-and-drop CSV/XLSX parser with template preview and validation errors.
     - *"Why is this bill relevant?" Modal:* Grounded AI reasoning explaining why a specific bill affects the user's holdings with statutory citations.
     - *Impact Report Generator:* Preview and PDF export for executive committees.

---

### 3.23 Watchlist Manager & Detail (`/watchlists` & `/watchlists/[watchlistId]`)
- **Routes:** `/watchlists` and `/watchlists/[watchlistId]`
- **Primary Persona:** Research Analyst, Sector Lead.
- **Primary Objective:** Custom curation and alerting configuration for custom baskets of bills, companies, and states.
- **Key Layout Zones:**
  - *List Page (`/watchlists`):* High-density grid of user watchlists with item counts, active alert rules count, last modified date, and "Create Watchlist" modal.
  - *Detail Page (`/watchlists/[watchlistId]`):*
    - Header: Watchlist title, description, aggregate risk rating, export button.
    - Quick-Add Search Combobox: Inline search allowing instant addition of bills or companies without opening a modal.
    - Tracked Entities Table: Entity Name, Type (Bill, Company, State), Jurisdiction/Sector, Added Date, Actions (Remove).
    - Custom Alert Rules Panel: Rules triggered when watched entities change procedural stage, receive new predictions, or exhibit media diffusion.

---

### 3.24 Legislative Alerts Center (`/alerts`)
- **Route:** `/alerts` (`frontend/app/alerts/page.tsx`)
- **Primary Persona:** Risk Officer, Regulatory Affairs Director.
- **Primary Objective:** Review triggered legislative change events, filter by severity, and manage alert subscriptions.
- **Key Layout Zones:**
  1. *Alert Severity Tabs:* All, Critical (Rose), High (Amber), Medium (Sky), Low (Slate).
  2. *Bulk Action Bar:* "Mark All as Read", "Archive Selected", "Filter by Watchlist".
  3. *Alert Event Stream:* Timestamped cards showing Triggered Entity, Alert Rule Name, Change Description, Epistemic Tag, Action Link (`View Bill Dossier` / `View Company Profile`).

---

### 3.25 In-App Notifications Center (`/notifications`)
- **Route:** `/notifications` (`frontend/app/notifications/page.tsx`)
- **Primary Persona:** All Users.
- **Primary Objective:** In-app notification center, daily digest archive, and delivery status tracking.
- **Key Layout Zones:**
  1. *Notification Stream:* Unread vs Read feeds with direct action buttons.
  2. *Daily Digest Archive:* Accordion list of past automated executive daily intelligence digests.
  3. *Notification Delivery Status:* Shows delivery confirmation across In-App, Email, and Webhook channels.

---

### 3.26 Legislative Monitoring Center (`/monitoring`)
- **Route:** `/monitoring` (`frontend/app/monitoring/page.tsx`)
- **Primary Persona:** Data Operations, IT Administrator, Compliance Auditor.
- **Primary Objective:** Full transparency and observability hub tracking 22+ Central and State legislative sources, crawlers, and change detection engines.
- **Key Layout Zones:**
  1. *Observability Banner:* Central Parliament & 4 State Assemblies crawler status (AP, KA, KL, TS).
  2. *Operational Tabs (7 Tabs):*
     - Tab 1: System Overview (Total checks, uptime percentage, mean latency).
     - Tab 2: Official Sources Registry (22 Sources Table: Source Name, Jurisdiction, URL, Health Status, Last Check, Response Time).
     - Tab 3: Check History Table (Crawler execution audit log).
     - Tab 4: Detected Changes Feed (Statutory diff events).
     - Tab 5: Discovery Feed (Intake candidates).
     - Tab 6: Scheduler Panel (Crawler interval inspection and manual trigger button).
     - Tab 7: Monitoring AI Analyst (Operational telemetry queries).
  3. *Integrated Drawers:*
     - *Source Detail Drawer:* Latency history chart, HTTP response headers, error tracebacks.
     - *Change Detail Drawer:* Side-by-side diff of detected text changes in official gazettes.

---

### 3.27 Platform Coverage Audit (`/coverage`)
- **Route:** `/coverage` (`frontend/app/coverage/page.tsx`)
- **Primary Persona:** Compliance Auditor, Technical Management.
- **Primary Objective:** Dynamic audit report on verified system counts, invariants, and firewall integrity.
- **Key Layout Zones:**
  1. *Authoritative Invariant Verification Status:* Verified Live against `/api/v1/coverage`.
  2. *Baseline Invariant Audit Table:*
     - Central Bills: 20 / 20 PASS
     - Central Scanned Records: 22 / 22 PASS
     - State Production Bills: 44 / 44 PASS
     - State Stock Predictions: 0 (Strict Firewall Invariant) PASS
     - Master Companies: 70 / 70 PASS
     - Quantitative Securities: 47 / 47 PASS
     - Predictions: 4,700 / 4,700 PASS
     - Stakeholder Reports: 14,100 / 14,100 PASS
     - Authoritative Horizons: 5 / 5 PASS
  3. *SHA-256 Manifest Verification:* Authoritative hash `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`.

---

### 3.28 Institutional Report Center (`/reports`)
- **Route:** `/reports` (`frontend/app/reports/page.tsx`)
- **Primary Persona:** Investment Director, Legal Partner, Compliance Officer.
- **Primary Objective:** Institutional catalog for configuring, generating, and downloading audit-grade intelligence reports.
- **Key Layout Zones:**
  1. *Template Catalog (7 Standard Institutional Templates):*
     - 1. Executive Legislative Impact Dossier (PDF)
     - 2. Quantitative Market Impact & Event Study Report (PDF/CSV)
     - 3. Corporate Legislative Risk Exposure Profile (PDF)
     - 4. Portfolio Regulatory Sensitivity Audit (PDF/XLSX)
     - 5. Pre-Event Anticipation & Diffusion Report (PDF)
     - 6. State Assembly Sub-National Legislative Digest (PDF)
     - 7. System Provenance & Statutory Compliance Verification (PDF)
  2. *Report Generation Modal:* Template parameters selector (Bill, Company, Sector, Event Horizon).
  3. *Generated Reports Archive:* Table of previously generated documents with download links, file sizes, and generation timestamps.

---

### 3.29 Standalone AI Analyst Terminal (`/ai-analyst`)
- **Route:** `/ai-analyst` (`frontend/app/ai-analyst/page.tsx`)
- **Primary Persona:** Research Analyst, Legal Associate.
- **Primary Objective:** Dedicated conversational terminal for in-depth legislative and financial intelligence inquiries (upgrades placeholder).
- **Key Layout Zones:**
  1. *Terminal Header:* Grounded Groq AI Model indicator, session title, "New Session" button, Token usage meter.
  2. *Active Context Bar:* Entity Selector allowing analyst to anchor conversation to a specific Bill, Company, Industry, or Portfolio.
  3. *Persona Selector:* Toggle between:
     - Institutional Investor (Focus on capital allocation, margins, and market sensitivity)
     - Policy Researcher (Focus on statutory mechanisms, constitutional validity, and parliamentary precedent)
     - Public Affairs Lead (Focus on compliance burden, timelines, and stakeholder reactions)
  4. *Chat Stream:* Message bubbles with markdown rendering, LaTeX formula display, and explicit statutory citation pill links.
  5. *Evidence Citation Drawer (Right Side):* Clicking any citation pill opens the exact gazette provision or market data row referenced by the AI.
  6. *Strict Refusal Guardrails Banner:* Prominent footer confirming that the AI strictly refuses price targets, buy/sell investment advice, and insider speculation.

---

### 3.30 SaaS Settings & Team RBAC (`/settings`)
- **Route:** `/settings` (`frontend/app/settings/page.tsx`)
- **Primary Persona:** Organization Owner, Tenant Admin.
- **Primary Objective:** Organization control panel, member management, RBAC, and alert preferences.
- **Key Layout Zones:**
  1. *Settings Sidebar Tabs (7 Tabs):*
     - 1. User Profile: Name, email, title, password change.
     - 2. Organization & RBAC: Tenant name, ID, member table (OWNER, ADMIN, MEMBER, VIEWER), invite member form.
     - 3. Security & Sessions: Active sessions, token expiry, audit log download.
     - 4. Alert Preferences: Email/webhook notification channels, minimum severity thresholds, Quiet Hours controller.
     - 5. AI Metering & Telemetry: Monthly Groq token quota, usage chart, rate limits.
     - 6. Data Management: Full tenant data export (JSON), watchlist backups.
     - 7. Subscription & Licensing: Institutional tier tier indicator, enterprise features enabled.

---

### 3.31 Authentication & Onboarding Routes
- **`/login` (`frontend/app/login/page.tsx`):**
  - Institutional branded login form (Email, Password, Tenant slug).
  - One-click demo credential autofill buttons (`Institutional Analyst`, `Compliance Officer`, `Admin`).
  - Strict JWT bearer authentication with tenant isolation.
- **`/signup` (`frontend/app/signup/page.tsx`):**
  - New tenant registration form (Organization name, admin user, domain, plan selection).
- **`/onboarding` (`frontend/app/onboarding/page.tsx`):**
  - 8-Step Interactive Onboarding Wizard configuring team focus (Central vs State), initial watchlists, alert thresholds, and sample portfolio upload.

---

## 4. Modern Design System Specification

### 4.1 Design Philosophy: "Restrained Authority"
The design system rejects generic AI dashboard tropes (neon glow effects, low-contrast text, cartoonish cards) and adopts an **Institutional Intelligence Aesthetic**:
- **Information Density:** Optimized for financial and legal analysts who require maximum data visibility per viewport without visual chaos.
- **Typographic Precision:** Strict mathematical hierarchy, consistent line-heights, and tabular numbers for all quantitative metrics.
- **Micro-Border Architecture:** 1px hairline borders (`rgba(255, 255, 255, 0.07)`) separating structured data panes instead of bulky drop shadows.
- **Subtle Surface Elevation:** Layered slate surfaces (`#070b12` base, `#0c1322` card, `#121b2f` elevated) creating natural visual depth.

---

### 4.2 Typography System

```css
/* Typography Tokens */
--font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
--font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
```

#### Typographic Scale & Usage:
| Token Name | Size | Line Height | Weight | Tracking | Purpose / Applied Elements |
|---|---|---|---|---|---|
| `text-display` | 28px (1.75rem) | 34px | 700 Bold | -0.025em | Landing Hero, Major Metric Headers |
| `text-headline` | 22px (1.375rem) | 28px | 600 SemiBold | -0.02em | Page Titles (`/workspace`, `/predictions`) |
| `text-title` | 17px (1.0625rem) | 22px | 600 SemiBold | -0.015em | Card Titles, Workspace Section Headers |
| `text-subheading`| 14px (0.875rem) | 18px | 500 Medium | -0.01em | Table Headers, Form Labels, Tab Titles |
| `text-body` | 13px (0.8125rem) | 19px | 400 Regular | normal | Paragraphs, Summaries, Provisions Text |
| `text-caption` | 11px (0.6875rem) | 15px | 400 Regular | +0.01em | Timestamps, Secondary Metadata, ISINs |
| `text-micro` | 9.5px (0.59rem) | 13px | 700 Bold | +0.08em | Uppercase Badges, Status Pills, Epistemics |
| `font-mono-num` | 13px (0.8125rem) | 18px | 500 Medium | normal | **All quantitative numbers, CAR %, t-stats, dates** (uses `font-variant-numeric: tabular-nums`) |

---

### 4.3 Color Palette & Semantic Tokens

```
Base Background:    #070b12  (Deep Slate Black)
Surface Layer:      #0c1322  (Card Background)
Elevated Surface:   #121b2f  (Modal / Popover / Hover)
Border Subtle:      rgba(255, 255, 255, 0.06)
Border Default:     rgba(255, 255, 255, 0.10)
Border Highlight:   rgba(255, 255, 255, 0.18)
```

#### Semantic Color Tokens:
| Semantic Purpose | Light/Dark Token | Hex Value | Usage / Component Context |
|---|---|---|---|
| **Text Primary** | `--text-primary` | `#f8fafc` (Slate 50) | Primary titles, active values, high-contrast text |
| **Text Secondary** | `--text-secondary`| `#94a3b8` (Slate 400)| Explanatory text, table cell descriptions |
| **Text Muted** | `--text-muted` | `#64748b` (Slate 500)| Timestamps, inactive tabs, column headers |
| **Financial Positive** | `--color-positive` | `#10b981` (Emerald 500) | Positive CAR (+%), Healthy Crawlers, `[FACT]` |
| **Financial Negative** | `--color-negative` | `#f43f5e` (Rose 500) | Negative CAR (-%), High Risk, Failed Crawler |
| **Neutral / Hold** | `--color-neutral` | `#94a3b8` (Slate 400) | Neutral Direction, Moderate Risk |
| **Econometric Model** | `--color-model` | `#6366f1` (Indigo 500) | Central Level 1, OLS Betas, `[DERIVED]` |
| **State Assembly** | `--color-state` | `#0284c7` (Sky 600) | State Assembly Level 2, Regional Gazettes |
| **Intelligence Co.** | `--color-intel` | `#06b6d4` (Cyan 500) | Non-listed Intelligence Entities |
| **Anticipation Signal**| `--color-warning`| `#f59e0b` (Amber 500) | Pre-event Anticipation, `[INTERPRETATION]` |
| **AI Copilot** | `--color-ai` | `#a855f7` (Purple 500) | Groq AI Assistant, Conversational Tokens |

---

### 4.4 Epistemic Classification Visual System

Every card, table cell, or report element containing analytical content must carry a standardized epistemic tag:

```css
/* Epistemic Badges */
.badge-epistemic-fact {
  color: #34d399;
  background: rgba(16, 185, 129, 0.10);
  border: 1px solid rgba(16, 185, 129, 0.25);
}
.badge-epistemic-observed {
  color: #38bdf8;
  background: rgba(14, 165, 233, 0.10);
  border: 1px solid rgba(14, 165, 233, 0.25);
}
.badge-epistemic-derived {
  color: #818cf8;
  background: rgba(99, 102, 241, 0.10);
  border: 1px solid rgba(99, 102, 241, 0.25);
}
.badge-epistemic-interpretation {
  color: #fbbf24;
  background: rgba(245, 158, 11, 0.10);
  border: 1px solid rgba(245, 158, 11, 0.25);
}
.badge-epistemic-prediction {
  color: #c084fc;
  background: rgba(168, 85, 247, 0.10);
  border: 1px solid rgba(168, 85, 247, 0.25);
}
```

- `[FACT]`: Official Gazettes, PRS bills, statutory clauses.
- `[OBSERVED]`: Historical BSE/NSE equity prices, trading volume, event dates.
- `[DERIVED]`: Econometric OLS abnormal returns, beta estimates, t-statistics.
- `[INTERPRETATION]`: Grounded Groq AI executive summaries, policy perspectives.
- `[PREDICTION]`: Forward-looking event-study cumulative abnormal returns (`[-1,+1]` to `[-10,+10]`).

---

### 4.5 Statutory Firewall Component System

#### 1. State Bill Prediction Firewall Banner
```html
<div class="border border-sky-500/30 bg-sky-950/20 rounded-lg p-3.5">
  <div class="flex items-center gap-2">
    <span class="text-sky-400 font-bold text-xs uppercase tracking-wider">⚖ STATUTORY FIREWALL: STATE LEGISLATION</span>
    <span class="text-[10px] px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 font-mono">STATE_STOCK_PREDICTIONS = 0</span>
  </div>
  <p class="text-xs text-slate-300 mt-1.5 leading-relaxed">
    By statutory design, sub-national State Assembly legislation (Andhra Pradesh, Karnataka, Kerala, Telangana) is classified as Level 2 Qualitative Intelligence. Stock market prediction models are strictly firewalled to prevent spurious correlations with national equity indices.
  </p>
</div>
```

#### 2. Intelligence Company Firewall Banner
```html
<div class="border border-cyan-500/30 bg-cyan-950/20 rounded-lg p-3.5">
  <div class="flex items-center gap-2">
    <span class="text-cyan-400 font-bold text-xs uppercase tracking-wider">🏢 ENTITY FIREWALL: NON-LISTED INTELLIGENCE ENTITY</span>
    <span class="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono">QUANT_MODEL = DISABLED</span>
  </div>
  <p class="text-xs text-slate-300 mt-1.5 leading-relaxed">
    This corporate entity is not publicly traded on the National Stock Exchange (NSE) or Bombay Stock Exchange (BSE). Quantitative event-study models are disabled. Statutory exposure mapping and operational transmission mechanisms are displayed for corporate risk tracking.
  </p>
</div>
```

---

### 4.6 UI Component Library Specifications

#### 1. Button System
- **Primary Institutional Button:** Solid indigo/slate (`bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs px-3.5 py-2 rounded-md shadow-sm transition-colors`).
- **Secondary Outline Button:** Crisp hairline border (`border border-slate-700 hover:border-slate-500 text-slate-200 hover:bg-slate-800/50 text-xs px-3 py-1.5 rounded-md`).
- **Ghost Action Button:** Minimalist icon/text button (`text-slate-400 hover:text-slate-100 hover:bg-slate-800/40 text-xs px-2 py-1.5 rounded`).
- **Danger Button:** Rose border/fill (`border border-rose-500/40 text-rose-300 hover:bg-rose-950/40 text-xs px-3 py-1.5 rounded-md`).

#### 2. Institutional Table System
- **Row Heights:** Compact (36px per row) or Standard (44px per row).
- **Sticky Header:** `position: sticky; top: 0; background: #0c1322; z-index: 10; border-bottom: 1px solid rgba(255,255,255,0.12);`
- **Header Cells:** Uppercase 10px tracking-wider font (`text-slate-400 font-semibold uppercase tracking-wider text-[10px] py-2.5 px-3`).
- **Numeric Cells:** Right-aligned, `font-mono tabular-nums text-xs text-slate-200`.
- **Row Hover State:** `hover:bg-[#121b2f] transition-colors duration-100 cursor-pointer`.
- **Striping:** Subtle alternating background (`nth-child(even): bg-[#090e18]`).

#### 3. Modal Dialogues & Slide-Over Drawers
- **Backdrop:** `bg-black/70 backdrop-blur-sm fixed inset-0 z-50`.
- **Container:** `bg-[#0c1322] border border-white/10 rounded-xl shadow-2xl overflow-hidden`.
- **Accessibility:** Automatic `Escape` key close listener, focus trap inside modal, `aria-modal="true"`.

#### 4. Animations & Micro-Interactions
- **Strict Reduced-Motion Compliance:**
  ```css
  @media (prefers-reduced-motion: reduce) {
    *, ::before, ::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }
  ```
- **Durations:** Fast micro-interactions capped at 150ms (`transition: all 150ms ease-out`).
- **Drawer Slide:** 200ms ease-in-out (`transform 200ms cubic-bezier(0.16, 1, 0.3, 1)`).

---

## 5. Responsive Design Architecture

### 5.1 Breakpoint System
- **Wide Desktop (`xl` / `>= 1440px`):** Full 3-column / 3-pane analytical layouts (Navigation + Master Explorer Table + Contextual Intelligence Inspector).
- **Standard Desktop (`lg` / `1024px – 1439px`):** 2-pane analytical layouts (Master View + Slide-out drawer).
- **Tablet (`md` / `768px – 1023px`):** Single fluid column with sticky toolbar; tables enable horizontal scroll with visual fade affordances.
- **Mobile (`sm` / `< 768px`):** Single column, stacked cards, sticky mobile action headers, full-screen slide-over drawers.

### 5.2 Responsive Table Strategy
Financial data tables (Predictions, Exposures, Watchlists) handle mobile screens through **Dual-Mode Rendering**:
1. **Desktop / Tablet:** Native high-density HTML table with sticky left columns (e.g., Bill Name, Ticker) and smooth horizontal scrolling for secondary metrics.
2. **Mobile Screen:** Interactive card-list mirror where each row renders as a compact 3-row card displaying the primary entity, primary metric (CAR %), and expand button for diagnostics.

---

## 6. Complete 78-Capability Preservation Mapping

The table below confirms the exact destination and redesign pattern for **all 78 capabilities** identified in Task 8.31A. **Zero capabilities are removed.**

| ID | Feature Name | Current Location | Target Destination | Redesign Pattern / Interaction Model | Data Source / Verification Status |
|---|---|---|---|---|---|
| **1** | Institutional Landing Page | `/` | `/` | Rebalance typography with high-contrast institutional styling; live KPI ticker strip; statutory firewall cards | Static + `/api/v1/coverage` |
| **2** | Top Navigation Bar | `TopNavbar.tsx` | Global Shell | Consolidated 5-macro-workspace dropdowns; sticky 56px header; live pulse indicator | Active in `layout.tsx` |
| **3** | Legacy Left Sidebar | `Sidebar.tsx` | Retired after parity | Maintained in repo during Task 8.31B/C; replaced by TopNavbar | Replaced cleanly |
| **4** | Global Search Modal | `Header.tsx` | Global Shell (⌘K) | Upgraded to Command Palette with entity prefixes (`/b`, `/c`, `/s`, `/p`) | `/api/v1/search` |
| **5** | Platform Overview Dashboard | `/overview` | `/overview` | 3-zone command center: System Pulse (top), Legislative Landscape (center table), Market Highlights (right) | `/api/v1/coverage`, `/api/v1/bills` |
| **6** | Legislative Explorer | `/explorer` | `/explorer` | Dual-view toggle (Dense Table vs Card Stream); multi-facet sidebar; active filter chips | `/api/v1/bills`, `/api/v1/search` |
| **7** | Bills Directory | `/bills` | `/bills` | Structured canonical statutory index; Central vs State tabs; column-sortable table | `/api/v1/bills` |
| **8** | Legislative Dossier (Detail) | `/bills/[billId]` | `/bills/[billId]` | 5 master workspaces (Executive, Exposures, Markets, Stakeholders, Provenance) + persistent AI sidebar | `/api/v1/bills/{id}/dossier` |
| **9** | Bill Timeline & Journey | `/bills/[billId]` | Dossier Sidebar & Tab 1 | Procedural milestone stepper (Introduction → Committee → Lok Sabha → Rajya Sabha → Assent) | `/api/v1/bills/{id}/dossier` |
| **10** | Bill Provision Analyzer | `/bills/[billId]` | Dossier Tab 1 | Section-by-section statutory provisions table with regulatory powers and penalties | `/api/v1/bills/{id}` |
| **11** | Bill Corporate Exposure Table | `/bills/[billId]` | Dossier Tab 2 | High-density financial table of exposed companies with transmission channels and ISIN links | `/api/v1/bills/{id}/companies` |
| **12** | Central Bill Predictions Table | `/bills/[billId]` | Dossier Tab 3 | Event-study predictions table across 5 windows for 47 securities with t-stats and CAR | `/api/v1/bills/{id}/predictions` |
| **13** | Bill Anticipation Diagnostics | `/bills/[billId]` | Dossier Tab 3 | Pre-event market diffusion metrics, media attention trend lines, and bulletin mentions | `/api/v1/bills/{id}/anticipation` |
| **14** | Stakeholder Persona Analysis | `/bills/[billId]` | Dossier Tab 4 | Multi-perspective impact grid (Investor, Business, Public) with prominent epistemic tags | `/api/v1/bills/{id}/stakeholders` |
| **15** | Bill Provenance & Source Viewer | `/bills/[billId]` | Dossier Tab 5 | Official gazette URLs, PRS tracking links, ingestion timestamps, and SHA-256 hash | `/api/v1/bills/{id}/provenance` |
| **16** | Bill Compare Tool | `/bills/compare` | `/bills/compare` | Upgraded from placeholder: Dual bill picker with side-by-side provision diff and CAR delta | Full interactive view |
| **17** | Latest Bills Feed | `/latest-bills` | `/latest-bills` | Chronological timeline cards connected to live intake feed; jurisdiction pills | `/api/v1/monitoring/changes` |
| **18** | Upcoming Legislation Calendar | `/upcoming-legislation` | `/upcoming-legislation` | Scheduled parliamentary sessions and committee hearings table; zero fabricated dates | Official session agendas |
| **19** | Live Legislative Discovery | `/live-discovery` | `/live-discovery` | Intake stream of newly discovered bills tagged `KNOWLEDGE_ONLY`; checksum verification | `/api/v1/monitoring/discovery` |
| **20** | Company Intelligence Directory | `/companies` | `/companies` | Upgraded from placeholder: 70-company master directory; Quant vs Intel filter pills | `/api/v1/companies` |
| **21** | Corporate Intelligence Profile | `/companies/[companyId]` | `/companies/[companyId]` | Consolidated 4-tab corporate tear sheet (Exposures, Transmission, Predictions/Firewall, AI) | `/api/v1/companies/{id}` |
| **22** | Company Exposure Matrix | `/companies/[companyId]` | Profile Tab 1 | Filterable matrix connecting bills to operational divisions, CapEx, and compliance | `/api/v1/companies/{id}/exposures` |
| **23** | Economic Transmission Architecture | `/companies/[companyId]` | Profile Tab 2 | Flow diagrams: Statutory Levers → Operational Variables → Revenue/Cost Impact | `/api/v1/companies/{id}` |
| **24** | Geographic & State Footprint | `/companies/[companyId]` | Profile Tab 1 | Operating states, manufacturing facilities, and state assembly act exposures | `/api/v1/companies/{id}` |
| **25** | Company Predictions Tab | `/companies/[companyId]` | Profile Tab 3 | Mode A: 20-bill CAR projections & t-stats; Mode B: Intelligence Company Firewall banner | `/api/v1/companies/{id}/predictions` |
| **26** | Industries Directory | `/industries` | `/industries` | Sector taxonomy cards connecting legislation to granular economic industries | `/api/v1/industries` |
| **27** | Industry Detail Dossier | `/industry/[id]` & `/industries/[id]` | Both Routes | 13-section dossier: footprint, exposures, transmission map, constituent companies | `/api/v1/industries/{id}` |
| **28** | Economic Sectors Directory | `/sectors` | `/sectors` | Macro policy intensity heatmap and sector comparison table linking to industries | `/api/v1/industries` |
| **29** | State Coverage Directory | `/states` | `/states` | Upgraded from placeholder: Implemented states cards (AP, KA, KL, TS) + 24 planned states | `/api/v1/coverage` |
| **30** | State Detail Dossier | `/states/[state]` | `/states/[state]` | Upgraded from placeholder: State assembly acts table, corporate exposures, gazette links | State knowledge repo |
| **31** | Market Predictions Engine | `/predictions` | `/predictions` | Split-view workbench: Top Horizon Selector, Dense Screener Table, CAR curve inspector | `/api/v1/predictions` |
| **32** | Prediction Detail View | `/predictions/[predictionId]` | `/predictions/[id]` | Statistical teardown: OLS market model, beta, residual variance, Decision Support card | `/api/v1/predictions/{id}` |
| **33** | Horizon Comparator Tool | `/predictions` section | Predictions Workbench | Interactive tabs comparing `[-1,+1]` to `[-10,+10]` with trajectory curve | `/api/v1/predictions/compare` |
| **34** | Legislative Risk Matrix | `/risk` | `/risk` | Heatmap matrix (Sector vs Risk Severity) + ranked high-risk legislation table | `/api/v1/risk/summary` |
| **35** | Portfolio Risk Calculator | `/risk` section | `/risk` Workbench | Interactive composite risk calculator for custom ISIN arrays or saved watchlists | `/api/v1/risk/portfolio` |
| **36** | Pre-Event Anticipation Analytics | `/anticipation` | `/anticipation` | 940 diffusion scores table across 4 tiers; mandatory legal disclaimer header | `/api/v1/anticipation` |
| **37** | Anticipation Evidence Explorer | `/anticipation` section | Anticipation Drawer | Split-panel evidence drawer displaying news mentions and parliamentary bulletins | `/api/v1/anticipation/evidence` |
| **38** | Personalized Workspace | `/workspace` | `/workspace` | Two-column command center: Chronological Change Feed (left) + Priority Actions (right) | `/api/v1/workspace` |
| **39** | Watchlist Manager | `/watchlists` | `/watchlists` | Multi-entity watchlist card grid with creation modal and quick stats | `/api/v1/watchlists` |
| **40** | Watchlist Detail Workspace | `/watchlists/[id]` | `/watchlists/[id]` | Entity management table with inline search-to-add combobox and alert rules list | `/api/v1/watchlists/{id}` |
| **41** | Legislative Alerts Center | `/alerts` | `/alerts` | Severity-filtered alerts stream (Critical, High, Medium, Low) with bulk actions | `/api/v1/alerts` |
| **42** | Notification Center | `/notifications` | `/notifications` | In-app notification center, daily digest archive, and delivery channel statuses | `/api/v1/notifications` |
| **43** | Legislative Monitoring Center | `/monitoring` | `/monitoring` | 7 operational tabs: Overview, Sources (22), History, Changes, Intake, Scheduler, AI | `/api/v1/monitoring` |
| **44** | Source Detail Drawer | `/monitoring` component | Monitoring Drawer | Real-time uptime, response latency graph, HTTP status codes, and crawler logs | `/api/v1/monitoring/sources/{id}` |
| **45** | Change Detail Drawer | `/monitoring` component | Monitoring Drawer | Side-by-side text diff inspector for detected statutory changes across versions | `/api/v1/monitoring/changes/{id}` |
| **46** | Crawler Scheduler Panel | `/monitoring` component | Monitoring Tab 6 | Crawler execution interval inspector and manual check trigger controls | `/api/v1/monitoring/scheduler` |
| **47** | Platform Coverage Audit | `/coverage` | `/coverage` | Dynamic audit report verifying baseline invariants, central/state counts, and SHA-256 | `/api/v1/coverage` |
| **48** | Portfolio Legislative Exposure | `/portfolio` | `/portfolio` | 5 relevance tiers (DIRECT to INFORMATIONAL); holdings table; impact cards stream | `/api/v1/portfolio` |
| **49** | Portfolio Holdings Upload Modal | `/portfolio` component | Portfolio Modal | Bulk import of positions via CSV/XLSX drag-and-drop with column mapping validator | `/api/v1/portfolio/upload` |
| **50** | "Why is this bill relevant?" Modal | `/portfolio` component | Portfolio Modal | Grounded Groq AI reasoning explaining bill relevance to specific user holdings | `/api/v1/workspace/explain` |
| **51** | Personalized Impact Report Generator | `/portfolio` component | Portfolio Modal | One-click generation of comprehensive executive impact report with PDF download | `/api/v1/portfolio/report` |
| **52** | Report Center | `/reports` | `/reports` | Institutional catalog across 7 templates; multi-format support (PDF, CSV, XLSX) | Report generation service |
| **53** | Grounded Groq AI Analyst | Embedded across 9 pages | Embedded Drawers | Contextual statutory Q&A, persona selection, and strict refusal guardrails | `/api/v1/ai/ask` |
| **54** | Standalone AI Analyst Page | `/ai-analyst` | `/ai-analyst` | Upgraded from placeholder: Full conversational terminal with active context selector | Dedicated AI terminal |
| **55** | SaaS Settings & Organization | `/settings` | `/settings` | 7 settings tabs: Profile, Organization RBAC, Security, Alerts, AI Metering, Export | `/api/v1/account` |
| **56** | Multi-Tenant User Sign-In | `/login` | `/login` | Organization login form with JWT token issuance and demo role quick-fill buttons | `/api/v1/auth/login` |
| **57** | Organization Registration | `/signup` | `/signup` | New tenant provisioning and initial administrator onboarding | `/api/v1/account/register` |
| **58** | Interactive Onboarding Wizard | `/onboarding` | `/onboarding` | 8-step walkthrough configuring team focus, initial watchlists, and alert preferences | Initial provisioning |
| **59** | Document Viewer Component | `DocumentViewer.tsx` | Global Component | Embedded official PDF and statutory gazette viewer with download link | Sourced from official URLs |
| **60** | Capability Badge Component | `CapabilityBadge.tsx` | Global Component | Universal visual token distinguishing Central Level 1, State Level 2, and Intel | Predefined enum |
| **61** | State Prediction Firewall Component | `StatePredictionFirewall.tsx` | Global Component | Prominent UI banner explaining 0 stock predictions guarantee on State pages | Statutory invariant |
| **62** | Intelligence Company Firewall Component | `IntelligenceCompanyFirewall.tsx` | Global Component | Prominent UI banner explaining non-listed company quantitative firewall | Statutory invariant |
| **63** | Data Status Badge & Layer Banner | `DataStatusBadge.tsx` | Global Component | Visual pill tag distinguishing LIVE, MODELLED, INTELLIGENCE, and PLANNED | Data classification |
| **64** | Search Input with Shortcuts | `SearchInput.tsx` | Global Component | Keyboard-accessible search input with ⌘K hotkey display and clear button | Search input token |
| **65** | Reusable Card & StatCard | `Card.tsx` | Global Component | Standard container card with hairline borders, stat indicators, and hover states | Core UI token |
| **66** | Reusable Tab Controller | `Tabs.tsx` | Global Component | Accessible tab button bar with item counts, icons, and keyboard navigation | Core UI token |
| **67** | Reusable Pagination Controller | `Pagination.tsx` | Global Component | Standard pagination bar with page numbers, prev/next buttons, and limit dropdown | Core UI token |
| **68** | Skeleton Loading States | `Skeleton.tsx` | Global Component | Shimmer placeholder cards, tables, and text lines for smooth perceived performance | Loading UI token |
| **69** | Decision Support Metric Cards | `PredictionDetailContent.tsx` | Global Component | Institutional cards presenting OLS betas, standard errors, and confidence intervals | Quantitative metric token |
| **70** | What Changed Diff View | `/bills/[billId]` | Dossier Tab 1 | Section-by-section diff viewer comparing statutory amendments against prior acts | Statutory diff token |
| **71** | Related Bills & Cross-References | `/bills/[billId]` | Dossier Sidebar | Card list of related legislation by ministry, subject matter, or sector | Bill cross-reference |
| **72** | Document Sources & Gazette Downloads | `/bills/[billId]` | Dossier Tab 5 | Official gazette URLs, PRS tracking links, and PDF download triggers | Gazette provenance |
| **73** | Company Peer Group Exposure | `CompanyDetailContent.tsx` | Profile Tab 1 | Comparative cards showing peer companies within the same industry and their exposures | Sector peer network |
| **74** | AI Workspace Assistant Widget | `AIWorkspaceAssistant.tsx` | Workspace Sidebar | Embedded conversational widget answering questions on active user change feeds | Groq AI widget |
| **75** | Alert Severity Thresholds Controller | `AlertRuleFormModal.tsx` | Watchlist / Alerts | Multi-level slider and toggle selector for minimum trigger severity | Alert rule modal |
| **76** | Tenant Data Export | `SettingsContent.tsx` | Settings Tab 6 | Automated one-click JSON/CSV export of tenant watchlists, portfolios, and audit logs | SaaS data portability |
| **77** | AI Metering & Token Telemetry | `SettingsContent.tsx` | Settings Tab 5 | Real-time progress bar tracking monthly Groq LLM token consumption and limits | AI telemetry token |
| **78** | Quiet Hours Alert Controller | `AlertPreferencesSection.tsx`| Settings Tab 4 | Timezone-aware quiet hours scheduler pausing push notifications during off-hours | Notification preferences |

---

## 7. Implementation & Migration Plan (Task 8.31C Blueprint)

### 7.1 Component Architecture Strategy

```
frontend/
├── components/
│   ├── ui/                    ← Universal design primitives (Buttons, Tables, Badges, Modals)
│   │   ├── Badge.tsx           (Preserved & enhanced)
│   │   ├── Button.tsx          (Preserved & upgraded)
│   │   ├── Card.tsx            (Preserved & upgraded to hairline styling)
│   │   ├── InstitutionalTable.tsx (NEW: High-density sortable table primitive)
│   │   ├── ContextDrawer.tsx   (NEW: Slide-over right inspection drawer)
│   │   ├── CommandPalette.tsx  (NEW: ⌘K fuzzy search modal)
│   │   ├── DataStatusBadge.tsx (Preserved)
│   │   ├── EpistemicBadge.tsx  (NEW: Standardized FACT, DERIVED, PREDICTION token)
│   │   ├── Pagination.tsx      (Preserved)
│   │   ├── SearchInput.tsx     (Preserved)
│   │   ├── Skeleton.tsx        (Preserved)
│   │   └── Tabs.tsx            (Preserved)
│   ├── layout/                ← Global shell components
│   │   ├── TopNavbar.tsx       (Redesigned: 5-macro-workspace navigation + mobile drawer)
│   │   └── Header.tsx          (Preserved / integrated with CommandPalette)
│   ├── firewalls/             ← Statutory firewall banners
│   │   ├── StatePredictionFirewall.tsx (Preserved & styled)
│   │   └── IntelligenceCompanyFirewall.tsx (Preserved & styled)
│   └── [domain]/              ← Domain-specific feature modules
│       ├── bills/              (Dossier 5-tab consolidation, provisions, timeline)
│       ├── companies/          (Corporate profile tear sheet, transmission diagram)
│       ├── predictions/        (Horizon workbench, econometric screener table)
│       ├── risk/               (Risk heatmap, portfolio calculator)
│       ├── anticipation/       (Score table, split evidence drawer)
│       ├── portfolio/          (Holdings table, CSV parser, relevance explainer)
│       ├── workspace/          (Two-column command center, change feed)
│       └── monitoring/         (7 operational tabs, source health, diff drawer)
```

---

### 7.2 Phased Migration Order (Task 8.31C Execution)

1. **Phase 1: Design System Foundation & Global CSS (`globals.css`):**
   - Establish CSS variables for institutional slate palette, hairline borders, and monospace tabular numerics.
   - Implement `InstitutionalTable.tsx`, `EpistemicBadge.tsx`, and `ContextDrawer.tsx` primitives.
   - Verify zero breaking changes to existing CSS classes.
2. **Phase 2: Global Navigation & Command Palette:**
   - Refactor `TopNavbar.tsx` to implement the 5 macro workspaces (Legislation, Markets, Entities, Portfolio, Reports) + direct Workspace anchor.
   - Refactor `CommandPalette.tsx` for keyboard-driven fuzzy search (`⌘K`).
   - Run `task-8-25-navigation.test.tsx` to maintain 100% route test passing rate.
3. **Phase 3: Core Legislative Workspaces:**
   - Consolidate `/bills/[billId]` from 12 tabs into 5 master workspaces + persistent AI sidebar.
   - Upgrade `/bills` and `/explorer` to utilize `InstitutionalTable` with dual-view mode.
   - Upgrade placeholder routes `/bills/compare`, `/latest-bills`, `/upcoming-legislation`, and `/live-discovery`.
4. **Phase 4: Quantitative Markets & Risk Workspaces:**
   - Refactor `/predictions` into split Horizon Workbench + Screener Table.
   - Upgrade `/risk` with interactive Sector vs Risk Severity heatmap.
   - Upgrade `/anticipation` with side-by-side evidence drawer.
5. **Phase 5: Corporate & Sub-National Entities:**
   - Upgrade `/companies` placeholder into full 70-company institutional directory.
   - Consolidate `/companies/[companyId]` into 4-tab corporate tear sheet.
   - Upgrade `/states` and `/states/[state]` placeholders with AP, KA, KL, TS statutory records.
6. **Phase 6: Daily Workspace, Portfolio & Operational Modules:**
   - Rebalance `/workspace` into two-column executive command center.
   - Polish `/portfolio`, `/watchlists`, `/alerts`, `/notifications`, and `/monitoring`.
   - Upgrade `/ai-analyst` placeholder into dedicated conversational research terminal.
7. **Phase 7: Full Regression & Cross-Browser Validation:**
   - Execute all 205+ Vitest tests (`npm run test`).
   - Execute Next.js build verification (`npm run build`).
   - Execute TypeScript check (`npm run typecheck`).
   - Confirm 0 test regressions, 0 analytical baseline modifications.

---

### 7.3 Risk Register & Mitigation Controls

| Risk | Likelihood | Impact | Strict Mitigation Control |
|---|---|---|---|
| **Breaking Existing Vitest Tests** | Medium | High | Maintain all data attributes, existing component prop interfaces, and route URLs. Existing tests mock specific IDs (`bill-header`, `predictions-tab`, `risk-calculator`) which will be strictly preserved. |
| **Accidental State Stock Predictions** | Low | Critical | Backend firewall assertions + frontend `StatePredictionFirewall` component permanently enforced. State bill pages never render equity prediction tables. |
| **Accidental Baseline Mutation** | Low | Critical | The entire `data/` directory remains strictly read-only. No frontend code writes to analytical JSONs. Invariant manifest SHA-256 is audited before and after. |
| **Information Overload in Tables** | Medium | Moderate | Default to essential columns with an inline "Customize Columns" drawer and row expansion trays for deep metadata. |
| **Mobile Layout Clipping** | Medium | Moderate | Implement dual-mode table rendering (sticky table on desktop, responsive card mirrors on mobile). |

---

## 8. Formal Status & Sign-off

```text
TASK_8_31B = DESIGN SPECIFICATION COMPLETE

78/78 FEATURES PRESERVED
0 FEATURES REMOVED
ANALYTICAL BASELINE = UNCHANGED
DATABASE = UNCHANGED
FRONTEND CODE = UNCHANGED
DESIGN DIRECTION = APPROVED FOR IMPLEMENTATION
```
