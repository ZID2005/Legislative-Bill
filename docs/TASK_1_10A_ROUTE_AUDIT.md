# TASK 1.10A ROUTE AND CAPABILITY AUDIT
**Decision Support, Risk, Anticipation & State Intelligence Routes**

**Date:** October 29, 2026  
**Status:** Canonical Audit Completed  
**Authoritative References:**  
- `docs/SEANCE_DESIGN_SYSTEM.md`  
- `docs/TASK_1_6A_EXPERIENCE_REDESIGN_AUDIT_AND_SPECIFICATION.md`  
- Canonical Frozen Baseline Manifest: `docs/production_baseline.json` (SHA-256: `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`)

---

## 1. Executive Route Inventory

| Route | Primary Component | Persona & Core Workflow | Active API Contracts | Redesign Dest / Architecture |
|---|---|---|---|---|
| `/risk` | `frontend/app/risk/RiskContent.tsx` | Chief Risk Officer / Compliance Desk: Assess multi-horizon legislative risk distributions, pricing-in status, sector dispersion, and portfolio exposure aggregation. | `riskApi.getRiskSummary()`, `riskApi.listRiskBills()`, `riskApi.listRiskCompanies()`, `riskApi.analyzePortfolioRisk()`, `watchlistsApi.listWatchlists()`, `aiApi.ask()` | Restructured editorial workspace with Executive Risk Summary, Interactive 5-Band Register, Progressive Drawer for Portfolio Risk Calculator, and Grounded AI Risk Analyst. |
| `/anticipation` | `frontend/app/anticipation/AnticipationContent.tsx` | Market Surveillance / Macro Strategist: Evaluate pre-event information diffusion, public media/search signals, and Anticipation Paradox dynamics without claiming causal trading impact. | `anticipationApi.getAnticipationSummary()`, `anticipationApi.listAnticipation()`, `anticipationApi.getContext()`, `aiApi.ask()` | Chronological intelligence desk: "What was known & when" timeline, Diffusion Spectrum, 940-Pair Register with Evidence Drawer, and prominent Statutory Research Notices. |
| `/states` | `frontend/app/states/StatesContent.tsx` | Regional Policy Analyst / Legal Counsel: Audit sub-national assembly enactments across 4 active pilot states (44 acts, 86 exposures) and 24 union expansion states. | `statesApi.getStateCoverage()`, `billsApi.listBills({ jurisdiction: "state" })` | Tabular Sub-National Legislative Registry with assembly cards, jurisdictional filtering, and strict State Prediction Firewall. |
| `/states/[state]` | `frontend/app/states/[state]/StateDetailContent.tsx` | Regional Legal Analyst: Deep inspection of state assembly acts, statutory transmission channels, and corporate operational footprint within a specific state. | `billsApi.listBills({ jurisdiction: "state", state })`, static profile registry | High-conviction State Legislative Dossier with assembly enactments register, corporate transmission matrix, and statutory firewall. |

---

## 2. Detailed Capability & Feature Inventory

### 2.1 Risk Intelligence (`/risk`)
- **Existing User-Visible Features:**
  - Executive title, Central Level 1 badge, epistemic DERIVED indicator, and fast links to `/predictions`, `/anticipation`, and `/watchlists`.
  - 5-Tier Deterministic Risk Model distribution metrics: 4,700 evaluated decisions, cross-sectional mean risk (44.2%), and threshold guidance.
  - Risk Distribution Visualizer bar chart.
  - Market Pricing-In Status breakdown across 4 categories: `PRICED_IN`, `PARTIALLY_PRICED_IN`, `UNPRICED`, `NOT_APPLICABLE`.
  - Risk by Event Window breakdown across 5 temporal horizons: `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`.
  - Cross-Sector Legislative Risk Dispersion (grid of sector cards with avg risk score, record count, and mini horizontal band breakdown).
  - Portfolio Legislative Risk Aggregator: select saved watchlist or enter comma-separated ISINs to compute composite risk score, dominant risk band, total exposure records, and company-level risk table.
  - Qualitative entity isolation notice: explicit reminder that unmodeled/qualitative entities carry 0 quantitative risk scores.
  - Entity Risk Profiles: Tabbed table switching between Bill Risk Profiles and Company Risk Profiles with search, sector filtering, and inspection links.
  - Grounded AI Risk Analyst with 3 analyst personas (`INVESTOR`, `POLICY`, `GENERAL_PUBLIC`).
  - Persistent `StatePredictionFirewall` notice.
- **Identified Friction Points & Information Architecture Issues:**
  - Excessive vertical stacking: 6 full-width sections force deep scrolling.
  - The Portfolio Risk Calculator and AI Analyst compete heavily with the primary risk register.
  - Card-in-card nesting in pricing-in and event window modules creates visual clutter.
  - Missing progressive disclosure for technical calculation details (e.g. thresholds, dispersion formulas).
  - Badging density can be rationalized using restrained editorial typography and non-color indicators.
- **Feature Retention Mapping:**
  - *Retain 100% of existing functionality.*
  - Move the Portfolio Risk Calculator into a dedicated, clean interactive panel with tabbed or drawer-accessible workflow so it doesn't displace the primary register.
  - Consolidate overview metrics into a high-density Executive Summary Strip.
  - Retain the tabbed Bill / Company risk registers with refined `InstitutionalTable` styling, tabular numerals, and non-color glyphs.
  - Retain the AI Analyst with grounded provenance disclaimers.

### 2.2 Anticipation Intelligence (`/anticipation`)
- **Existing User-Visible Features:**
  - Top and bottom mandatory verbatim legal disclaimer: *"Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law."*
  - Coverage Baseline KPI strip: 940 evaluated pairs (20 Central bills × 47 securities), flagged pairs count (82 pairs), mean anticipation score (38.4%), mean market signal (41.2%), mean information signal (35.6%).
  - 4-Tier Neutral Information Diffusion Spectrum: `NO_EVIDENCE`, `WEAK_EVIDENCE`, `MODERATE_EVIDENCE`, `STRONG_EVIDENCE` with score ranges and stacked proportional bar.
  - Pre-Event Trading Windows CAR Statistics across 5 pre-event windows (`[-30,-21]`, `[-30,-1]`, etc.) with mean CAR, mean MAR, and significant pairs count.
  - Top 10 Highest Diffusion Flagged Pairs with detected signals and direct links.
  - 940-Pair Information Diffusion Matrix: paginated table with Bill search, Company ISIN/symbol search, Tier filter dropdown, Sector filter dropdown, Flagged-only checkbox, and Predictions links.
  - Anticipation Evidence Section (`AnticipationEvidenceSection`): context inspection of market signal vs. public information signals.
  - Grounded AI Information Diffusion Analyst with persona switching.
  - Persistent `StatePredictionFirewall` notice.
- **Identified Friction Points & Information Architecture Issues:**
  - The mandatory legal disclaimer was placed in an ordinary card rather than an authoritative institutional banner.
  - The relationship between pre-event public media attention and market price absorption needs clearer chronological framing: "What was known, and when".
  - Missing evidence must be explicitly indicated rather than obscured.
  - The evidence inspection was static at the bottom instead of dynamically connecting with rows selected in the 940-pair register.
- **Feature Retention Mapping:**
  - *Retain 100% of existing functionality.*
  - Position the mandatory legal disclaimer in an authoritative institutional notice frame at the top.
  - Provide an interactive pair inspection drawer/panel that connects directly to any row in the diffusion matrix, rendering chronological milestones, media signals, and pre-event CAR metrics.
  - Retain all filters (Bill ID, ISIN/symbol, Tier, Sector, Flagged-only, Pagination) and summary metrics.

### 2.3 State Intelligence (`/states` & `/states/[state]`)
- **Existing User-Visible Features:**
  - Invariant metric strip: 4 Implemented States, 44 Production State Acts, 86 Corporate Exposures, 0 State Stock Predictions, 24 Planned Expansion States.
  - Mandatory `StatePredictionFirewall` prominent notice.
  - 4 Active Production Pilot States (Andhra Pradesh, Karnataka, Kerala, Telangana) with capital, assembly name, acts count, exposures count, official gazette source, key sectors, description, and link to state dossier and bills register.
  - 24 Planned Expansion States matrix with geographic zone filter (`All`, `Northern`, `Western`, `Southern`, `Eastern`, `Central`, `North-Eastern`).
  - State Detail Dossier (`/states/[state]`): State metadata, assembly enactments table (`InstitutionalTable` fetching state bills via `billsApi.listBills`), documented corporate operational footprint (operating facilities and state statutory transmission mechanisms), and firewall notice.
- **Identified Friction Points & Information Architecture Issues:**
  - Visual repetition across state cards; lacked a dense, tabular summary view for institutional users.
  - Potential navbar clipping and spacing inconsistency on mobile viewports.
  - Absence of a quick-search or tabbed switch between active pilot assemblies and union roadmap jurisdictions.
- **Feature Retention Mapping:**
  - *Retain 100% of existing functionality.*
  - Introduce an authoritative dual view (Tabular Registry + Assembly Dossier Cards) for the 4 active pilot states.
  - Maintain the strict State Prediction Firewall invariant (0 quantitative stock predictions).
  - Keep corporate operational footprint and statutory transmission channels intact.
  - Preserve all deep links (`/bills?jurisdiction=state&state=...`, `/states/[state]`, `/companies/[companyId]`).

---

## 3. Data Contract & Backend Verification

All fields rendered across `/risk`, `/anticipation`, and `/states` are backed by genuine API endpoints:
- `GET /api/v1/risk/summary`: Real baseline calculations over 4,700 decisions.
- `GET /api/v1/risk/bills`: Central bill risk records.
- `GET /api/v1/risk/companies`: Corporate risk records.
- `POST /api/v1/risk/portfolio`: Dynamic portfolio risk evaluation with unmodeled entity detection.
- `GET /api/v1/anticipation/summary`: Verified 940-pair diffusion baseline metrics.
- `GET /api/v1/anticipation`: Paginated diffusion pair records with full filtering.
- `GET /api/v1/anticipation/context`: Detailed market vs. media signals and chronological evidence.
- `GET /api/v1/bills?jurisdiction=state`: 44 state acts across AP, KA, KL, TS.
- `POST /api/v1/ai/ask`: Grounded Groq Llama-3-70b RAG assistant.

**Strict Prohibition:** No synthetic stock predictions, target prices, or probability figures are ever fabricated. State bills strictly produce 0 quantitative stock predictions. Intelligence-only companies are quarantined from quantitative prediction tables.

