# Task 8.14.1 — SaaS Frontend Architecture & UI Audit

**Document Version**: 1.0.0  
**Date**: September 18, 2026  
**Status**: COMPLETE / AUDITED & FROZEN  
**Target Milestone**: Migration from Streamlit Research Prototype to Next.js / FastAPI Modern SaaS Platform

---

## 1. Executive Summary

This audit establishes the definitive architectural blueprint, information architecture, and technical migration plan for transitioning the **Indian Parliamentary Intelligence & Market Impact Platform** from its current Streamlit research/validation prototype into a commercial, multi-tenant SaaS frontend.

The project currently combines:
1. **Central Government Market Impact Modeling (Level 1 — Production Modeled)**: 20 Central Parliamentary bills, 47 quantitative companies, 940 bill-company pairs, 4,700 machine learning predictions, 4,700 decision-support records, 940 anticipation scores, and 14,100 multi-stakeholder analytical reports across 5 event windows with backtested historical validation.
2. **State Legislative & Economic Intelligence (Level 2 — Intelligence Layer)**: 44 State bills across four active pilot states (Andhra Pradesh: 12, Karnataka: 11, Kerala: 11, Telangana: 10) backed by 44/44 official gazette/assembly PDFs, 44/44 structured knowledge records, and 86 validated corporate exposures—enforcing a strict statutory and econometric guarantee of **exactly 0 State stock predictions**.
3. **Corporate Intelligence Universe**: 70 total corporate records (47 quantitative prediction-eligible companies, 20 curated intelligence entities such as Swiggy, Flipkart, Amazon India, KSEB, AP-GENCO, and 3 baseline reference records) protected by an active quantitative firewall.
4. **Legislative Monitoring & Alert Pipeline (E2E Hardened)**: Inverted-index subscriber resolution, temporal alert aggregation, in-app notification center, and multi-channel outbound delivery abstractions (Email, Push, Webhooks).
5. **AI Analyst Infrastructure**: Groq LLM context builders and guardrails enforcing strict factual citation, separation of concerns, and zero financial-advice language.

### Core Architectural Decision
- **Next.js (React 19, TypeScript, Tailwind CSS)** will serve as the commercial, multi-tenant SaaS frontend.
- **FastAPI (Python)** will expose high-performance, asynchronous REST/JSON endpoints wrapping the existing Python services layer (`services/`, `storage/`, `schemas/`).
- **Streamlit (`dashboard/app.py`)** is explicitly retained as an internal research, offline audit, and ML validation environment—ensuring that research integrity and model evaluation workflows remain uninterrupted.
- **Frozen Baseline Guarantee**: The existing quantitative models, feature pipelines, predictions, and State economic layers are strictly frozen and will not be altered, retrained, or regenerated during frontend migration.

---

## 2. Existing Frontend & Dashboard Audit

The repository contains two generations of Streamlit dashboard code: the current 12-page production analytical dashboard (`dashboard/pages/`) and 10 legacy analytical views.

### A. Existing Dashboard Pages

| Page File | Title / Route | Primary Purpose | Key Components / Visualizations | SaaS Destination Route |
| :--- | :--- | :--- | :--- | :--- |
| `overview.py` | 🏠 Overview & New Bills | Executive KPIs, macro statistics, recent legislative activity | KPI metric tiles, cross-sector distribution, high-impact alert cards | `/overview` |
| `india_explorer.py` | 🏛️ India Legislative Explorer | Unified discovery across Central and State legislatures | Coverage roadmap, Explore India taxonomy filters, unified bill cards, zero-prediction badges | `/explorer` |
| `bills.py` | 📜 All Bills | Central bill master directory | Searchable DataFrame table, ministry/status filters, drilldown navigation | `/bills` |
| `bill_detail.py` | 🔍 Bill Intelligence | Deep-dive dossier for single bill | Timeline, provisions, corporate exposure table, prediction breakdown, anticipation paradox, stakeholder tabs, AI panel | `/bills/[billId]` |
| `companies.py` | 🏢 Company Intelligence | Corporate universe master directory | Sector/cap filters, quant vs intelligence badges, exposure counts | `/companies` |
| `company_detail.py` | 🏢 Company Detail | Per-company exposure & related bills | Corporate profile, operating states, exposure table, quantitative vs intelligence firewall banner, AI explanation | `/companies/[companyId]` |
| `predictions.py` | 📈 Market Impact Predictions | Macro distribution of ML forecasts | Direction balance, probability histograms, confidence metrics, event window filters | `/predictions` |
| `risk.py` | ⚠️ Risk Overview | Institutional risk classification | 4-tier risk matrix, impact vs probability scatter, capital allocation recommendations | `/risk` |
| `anticipation.py` | 🔍 Anticipation & Pricing-In | Pre-event market diffusion analysis | Anticipation Paradox score, pre-event volume trends, information leakage evidence | `/anticipation` |
| `backtesting.py` | 🔬 Historical Backtesting | Out-of-sample strategy evaluation | Cumulative wealth curves vs Nifty 50, Sharpe ratio, drawdown, win-rate metrics | `/backtesting` (or retained in Streamlit) |
| `methodology.py` | 📐 Methodology | 18-stage academic blueprint | Theoretical foundation, mathematical formulas, data lineage architecture | `/methodology` |
| `monitoring.py` | 🔭 Legislative Monitor | Real-time legislative source tracking | Scraper status, change detection logs, manual trigger controls | `/monitoring` |

*Legacy pages preserved for compatibility*: `landing.py`, `bill_explorer.py`, `company_explorer.py`, `investor_view.py`, `business_view.py`, `public_view.py`, `risk_overview.py`, `anticipation_view.py`, `explainability_view.py`, `backtest_view.py`.

### B. Existing Reusable Dashboard Components

| Component | File Path | Current Capabilities | Limitations / SaaS Gaps |
| :--- | :--- | :--- | :--- |
| **Unified Bill Card** | `dashboard/components/unified_bill_cards.py` | Renders cards for Central & State bills; shows jurisdiction badge, sectors, modeling eligibility, corporate exposure counts, official source link | Tightly coupled to Streamlit HTML/markdown injection; lacks responsive CSS grid layout |
| **Bill Cards** | `dashboard/components/bill_cards.py` | Central bill cards with status chips and drilldown button | Only supports Central bills; no state support |
| **AI Explanation Panel** | `dashboard/components/ai_explanation_panel.py` | Bill-level, company-level, and comparative AI panels with FACT/DERIVED/INTERPRETATION/PREDICTION tabs | Executes synchronous Python calls to Groq; lacks streaming tokens (SSE), typing animation, or chat history |
| **Filter Sidebar** | `dashboard/components/filter_sidebar.py` | Multi-select filters for bills, companies, sectors, ministries, risk tiers, event windows | Mutates Streamlit session state; needs translation to URL query parameters and TanStack Table state |
| **Report Viewer** | `dashboard/components/report_viewer.py` | Renders Investor, Business, and Public stakeholder reports in tabbed views | Static text blocks; lacks interactive export (PDF/DOCX), bookmarking, or differential highlights |
| **KPI Cards** | `dashboard/components/kpi_cards.py` & `cards.py` | Formatted metric tiles with delta values | Hardcoded inline styles; needs Tailwind CSS design token adoption |
| **Tables** | `dashboard/components/tables.py` | Formatted pandas DataFrames | Client-side pagination only; lacks virtual scrolling for 4,700 records |
| **Disclaimer Banner** | `dashboard/components/disclaimer.py` | Mandatory academic and non-financial advice disclaimers | Banner only; needs persistent footer integration across all SaaS routes |

---

## 3. Existing Backend & Service Audit

The repository contains mature, well-tested Python backend services and storage repositories. However, **no REST or GraphQL HTTP APIs currently exist**. The Streamlit dashboard calls Python service classes directly in-process.

### Capability Classification Audit

Each backend capability is classified using the mandatory audit criteria:
- **READY_TO_CONSUME**: Service logic is complete, tested, and can be wrapped directly in an API route.
- **SERVICE_EXISTS_API_MISSING**: Python service and repository are complete and validated, but no HTTP API layer exists.
- **PARTIAL**: Basic logic exists, but requires enrichment or schema adaptation for SaaS consumption.
- **NOT_IMPLEMENTED**: Required for commercial SaaS but not yet written in backend.
- **NOT_APPLICABLE**: Not relevant or prohibited by project governance.

| Functional Area | Backend Class / Service | Underlying Storage / Repo | Audit Status | Key Strengths & Gaps |
| :--- | :--- | :--- | :--- | :--- |
| **Unified Legislative Discovery** | `UnifiedLegislativeDiscoveryService` (`services/unified_legislative_discovery.py`) | `BillRepository`, `StateBillRepository`, `StateKnowledgeRepository` | **SERVICE_EXISTS_API_MISSING** | 66 unified records (22 Central, 44 State); deterministic ranking; category & state filters. Needs REST endpoint with pagination. |
| **Company Intelligence** | `CompanyIntelligenceService` (`services/company_intelligence_service.py`) | `CompanyRepository`, `CompanyExposureRepository`, `StateCorporateExposureRepository` | **SERVICE_EXISTS_API_MISSING** | 70 companies; 104 exposures; 86 State exposures; quantitative firewall active; deterministic exposure explanations. Needs REST endpoint. |
| **State Knowledge & Dossiers** | `StateKnowledgeService` (`services/state_knowledge_service.py`) | `StateKnowledgeRepository`, `StateImpactRepository` | **SERVICE_EXISTS_API_MISSING** | 44/44 dossiers; economic mechanisms; state economic profiles; 0 state predictions enforced. Needs REST endpoint. |
| **Market Predictions (Central)** | `PredictionRepository`, `MarketModelService` | `data/predictions/` (4,700 JSON files) | **SERVICE_EXISTS_API_MISSING** | 4,700 prediction records; 5 event windows; probability, confidence, direction. High file I/O overhead; needs indexed retrieval. |
| **Decision & Risk Support** | `DecisionRepository`, `DecisionService` | `data/decision_support/` (4,700 JSON files) | **SERVICE_EXISTS_API_MISSING** | 4,700 decision records; 4-tier risk matrix; capital allocation recommendations. Needs indexed API endpoint. |
| **Anticipation Bias Analysis** | `AnticipationRepository`, `AnticipationService` | `data/anticipation/scores/` (940 JSON files) | **SERVICE_EXISTS_API_MISSING** | 940 scores; pre-event stats; leakage indicators; Anticipation Paradox index. Needs indexed API endpoint. |
| **Stakeholder Reporting** | `ReportRepository`, `ReportingService` | `data/reports/` (14,100 JSON files) | **SERVICE_EXISTS_API_MISSING** | 14,100 reports (4,700 Investor, 4,700 Business, 4,700 Public). High storage volume; needs efficient key-based lookup. |
| **Legislative Monitoring** | `services/monitoring/` (`CentralMonitor`, `StateMonitor`, `ChangeDetector`) | `storage/monitoring_repository.py` | **SERVICE_EXISTS_API_MISSING** | Scrapers for Parliament and 4 States; change events; notification events. Lacks background Celery/scheduler worker daemon. |
| **Watchlist Management** | `WatchlistService` (`services/watchlist_service.py`) | `storage/watchlist_repository.py`, `storage/alert_rule_repository.py` | **SERVICE_EXISTS_API_MISSING** | Multi-dimension items (company, bill, sector, industry, state, jurisdiction); CRUD; multi-tenant isolation. Needs REST API. |
| **Inverted Index Querying** | `WatchlistIndexService` (`services/watchlist_index_service.py`) | `data/watchlists/indices/` | **READY_TO_CONSUME** | O(1) subscriber matching across 6 dimensions; corruption recovery; disk persistence. High performance (< 2ms). |
| **Alert Matching & E2E Pipeline** | `AlertMatchingService`, `AlertPipelineService` | `storage/alerts/` | **SERVICE_EXISTS_API_MISSING** | Complete E2E event processing; deduplication; multi-dimensional candidate grouping; sliding window aggregation. Needs API. |
| **In-App Notification Center** | `NotificationCenterService`, `NotificationService` | `storage/notification_repository.py` | **SERVICE_EXISTS_API_MISSING** | Unread counters; mark as read; archive; user/tenant isolation. Needs REST API with SSE or WebSockets for live alerts. |
| **Outbound Notification Dispatch** | `NotificationDispatcher`, `NotificationProviders` | `storage/notification_delivery_repository.py` | **SERVICE_EXISTS_API_MISSING** | MockEmail, MockPush, WebhookProvider with HMAC-SHA256 signing. Real SMTP / SendGrid / FCM providers are **NOT_IMPLEMENTED**. |
| **AI Analyst / Groq Copilot** | `AIExplanationService`, `AIContextBuilder` (`services/ai/`) | In-memory context builder + Groq LLM | **SERVICE_EXISTS_API_MISSING** | Robust context grounding; FACT/DERIVED/INTERPRETATION/PREDICTION separation; deterministic offline fallback. Needs streaming API. |
| **Multi-Tenancy & Auth** | `user_repository.py`, `schemas/user.py` | In-memory / file user store | **PARTIAL** | User and Tenant models exist; multi-tenant path scoping implemented in storage. JWT authentication, OAuth2, RBAC are **NOT_IMPLEMENTED**. |
| **State Predictions** | Econometric models for State Assemblies | None | **NOT_APPLICABLE** | **Prohibited by Project Scope & Methodology**. State predictions must remain strictly 0. |

---

## 4. Frontend Capability Matrix

The table below defines the 27 frontend capabilities required for the SaaS platform:

| # | Capability | Frontend Route | Backend Service | Primary Repository | Schema | API Exists? | Target API Contract | Data Source | Central? | State? | Pred.? | AI? | Watchlist? | Primary Limitations |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | **India Legislative Explorer** | `/explorer` | `UnifiedLegislativeDiscoveryService` | `BillRepository`, `StateBillRepository` | `UnifiedBillRecord` | No | `GET /api/v1/bills` | Local JSON catalogs | ✅ | ✅ | ⚠️ (Central only) | ✅ | ✅ | 66 bills currently indexed; 24 states planned |
| 2 | **New Bills Activity** | `/overview`, `/bills?status=new` | `UnifiedLegislativeDiscoveryService`, `CentralMonitor` | `BillRepository`, `MonitoringRepository` | `UnifiedBillRecord`, `ChangeEvent` | No | `GET /api/v1/bills/recent` | Scrapers / Ingestion records | ✅ | ✅ | ⚠️ | ❌ | ✅ | Depends on monitoring run freshness |
| 3 | **Central Bills Directory** | `/bills?jurisdiction=central` | `UnifiedLegislativeDiscoveryService` | `BillRepository` | `Bill`, `UnifiedBillRecord` | No | `GET /api/v1/bills?jurisdiction=central` | `data/central_bills/` | ✅ | ❌ | ✅ (20 prod) | ❌ | ✅ | 20 modeled bills + 2 non-legislative |
| 4 | **State Bills Directory** | `/bills?jurisdiction=state` | `UnifiedLegislativeDiscoveryService` | `StateBillRepository` | `UnifiedBillRecord` | No | `GET /api/v1/bills?jurisdiction=state` | `data/state_bills/` | ❌ | ✅ | ❌ (Zero pred) | ❌ | ✅ | 44 bills across 4 implemented states |
| 5 | **Bill Detail Dossier** | `/bills/[billId]` | `UnifiedLegislativeDiscoveryService`, `CompanyIntelligenceService` | `BillRepository`, `StateKnowledgeRepository` | `UnifiedBillRecord`, `StateBillKnowledgeRecord` | No | `GET /api/v1/bills/{id}` | Structured knowledge JSONs | ✅ | ✅ | ⚠️ (Central only) | ✅ | ✅ | State bills show qualitative knowledge only |
| 6 | **Bill Comparison** | `/bills/compare` | `UnifiedLegislativeDiscoveryService`, `AIExplanationService` | `BillRepository`, `StateKnowledgeRepository` | `UnifiedBillRecord` | No | `POST /api/v1/bills/compare` | Cross-repository records | ✅ | ✅ | ⚠️ | ✅ | ❌ | Max 3 bills side-by-side |
| 7 | **Company Directory** | `/companies` | `CompanyIntelligenceService` | `CompanyRepository` | `Company`, `CompanyProfileView` | No | `GET /api/v1/companies` | `data/companies/companies.json` | ✅ | ✅ | ⚠️ (Quant only) | ❌ | ✅ | 70 entities: 47 quant, 20 intel, 3 legacy |
| 8 | **Company Detail Dossier** | `/companies/[companyId]` | `CompanyIntelligenceService` | `CompanyRepository`, `CompanyExposureRepository` | `CompanyProfileView` | No | `GET /api/v1/companies/{id}` | Exposure & corporate JSONs | ✅ | ✅ | ⚠️ (Quant only) | ✅ | ✅ | Firewalled: intel-only has zero stock widgets |
| 9 | **Company ↔ Bill Exposure** | `/companies/[companyId]/bills` | `CompanyIntelligenceService` | `CompanyExposureRepository`, `StateCorporateExposureRepository` | `CompanyBillExposureView` | No | `GET /api/v1/companies/{id}/exposures` | Exposure records (104 total) | ✅ | ✅ | ⚠️ | ✅ | ✅ | Evidence-backed only; no speculative links |
| 10 | **Industry Discovery** | `/industries` | `CompanyIntelligenceService` | `CompanyRepository` | `Company` | No | `GET /api/v1/industries` | Canonical taxonomy | ✅ | ✅ | ⚠️ | ❌ | ✅ | Filtered from corporate master records |
| 11 | **Sector Discovery** | `/sectors` | `UnifiedLegislativeDiscoveryService`, `CompanyIntelligenceService` | Canonical sector mappings | `ExploreIndiaCategory` | No | `GET /api/v1/sectors` | Central & State taxonomies | ✅ | ✅ | ⚠️ | ❌ | ✅ | 18 canonical sectors mapped |
| 12 | **State Discovery** | `/states`, `/states/[state]` | `UnifiedLegislativeDiscoveryService`, `StateKnowledgeService` | `StateBillRepository`, `StateKnowledgeRepository` | `StateEconomicProfile`, `UnifiedBillRecord` | No | `GET /api/v1/states/{state}` | State profiles & bills | ❌ | ✅ | ❌ | ✅ | ✅ | 4 implemented states; 24 planned |
| 13 | **Market Prediction Master** | `/predictions` | `PredictionRepository`, `DashboardService` | `data/predictions/` | `PredictionRecord` | No | `GET /api/v1/predictions` | 4,700 prediction records | ✅ | ❌ | ✅ | ❌ | ✅ | Central production only (20 bills x 47 companies) |
| 14 | **Prediction Detail** | `/predictions/[predictionId]` | `PredictionRepository` | `data/predictions/` | `PredictionRecord` | No | `GET /api/v1/predictions/{id}` | Prediction JSON | ✅ | ❌ | ✅ | ✅ | ✅ | 5 event windows per pair |
| 15 | **Decision & Risk Analysis** | `/risk` | `DecisionRepository`, `DashboardService` | `data/decision_support/` | `DecisionSupportRecord` | No | `GET /api/v1/decisions` | 4,700 decision JSONs | ✅ | ❌ | ✅ | ✅ | ✅ | 4-tier risk matrix; strictly Central |
| 16 | **Anticipation & Pricing-In** | `/anticipation` | `AnticipationRepository`, `AnticipationService` | `data/anticipation/` | `AnticipationScore` | No | `GET /api/v1/anticipation` | 940 anticipation scores | ✅ | ❌ | ✅ | ✅ | ❌ | Strictly Central; non-insider public signals |
| 17 | **Stakeholder Explanations** | `/bills/[billId]/reports` | `ReportRepository` | `data/reports/` | `StakeholderReport` | No | `GET /api/v1/reports/{id}` | 14,100 stakeholder reports | ✅ | ❌ | ✅ | ✅ | ❌ | Central only (Investor, Business, Public) |
| 18 | **AI Analyst / Ask AI** | `/ai-analyst`, in-page drawers | `AIExplanationService`, `AIContextBuilder` | Cross-repository context | `AIExplanationResponse` | No | `POST /api/v1/ai/ask` | Groq API + offline fallback | ✅ | ✅ | ⚠️ (Central only) | ✅ | ❌ | Anti-hallucination guardrails; no financial advice |
| 19 | **Legislative Monitoring** | `/monitoring` | `services/monitoring/` | `MonitoringRepository` | `MonitoringJob`, `ChangeEvent` | No | `GET /api/v1/monitoring/jobs` | Parliament & Assembly scrapers | ✅ | ✅ | ❌ | ❌ | ✅ | Real-time scraper status & change feed |
| 20 | **Watchlists** | `/watchlists` | `WatchlistService` | `WatchlistRepository`, `AlertRuleRepository` | `Watchlist`, `WatchlistItem` | No | `GET /api/v1/watchlists` | `data/watchlists/` | ✅ | ✅ | ⚠️ | ❌ | ✅ | Scoped to `(tenant_id, user_id)` |
| 21 | **Alerts Feed** | `/alerts` | `AlertMatchingService`, `AlertAggregationService` | `storage/alerts/` | `AlertEvent`, `AlertGroup` | No | `GET /api/v1/alerts` | `storage/alerts/events/` | ✅ | ✅ | ⚠️ | ❌ | ✅ | Clustered by sliding temporal windows |
| 22 | **Notification Center** | `/notifications`, navbar dropdown | `NotificationCenterService` | `storage/notification_repository.py` | `Notification` | No | `GET /api/v1/notifications` | `storage/alerts/notifications/`| ✅ | ✅ | ⚠️ | ❌ | ✅ | Read/unread, archive, badge counter |
| 23 | **Daily/Weekly Digest** | `/settings/digests` | `AlertDigestService` | `storage/alerts/` | `AlertDigest` | No | `GET /api/v1/digests` | Aggregated alert groups | ✅ | ✅ | ⚠️ | ❌ | ✅ | Real-time, daily, weekly rollup options |
| 24 | **Coverage & Capabilities** | `/coverage` | `UnifiedLegislativeDiscoveryService` | Hardcoded registries & repo counts | `CoverageReport` | No | `GET /api/v1/coverage` | Repository file counts | ✅ | ✅ | ⚠️ | ❌ | ❌ | Complete transparency on Levels 1, 2, 3 |
| 25 | **Unified Global Search** | Navbar search bar / Command menu (`Cmd+K`) | `UnifiedLegislativeDiscoveryService`, `CompanyIntelligenceService` | Unified in-memory index | `SearchResult` | No | `GET /api/v1/search` | Multi-repository indexes | ✅ | ✅ | ⚠️ | ❌ | ❌ | Sub-50ms deterministic multi-attribute lookup |
| 26 | **Faceted Filters** | Filter bar across listing pages | Service query parameters | Repository metadata | Filter criteria | No | Query parameters on listing APIs | In-memory indexes | ✅ | ✅ | ⚠️ | ❌ | ❌ | Sector, state, jurisdiction, market relevance |
| 27 | **Source & Provenance Display**| In-dossier provenance badges / modal | Storage metadata | Original PDFs & gazette registries | `ProvenanceAuditMap` | No | Embedded in detail payloads | Official portals & Gazette files | ✅ | ✅ | ⚠️ | ❌ | ❌ | Official links, PDF download, SHA-256 hashes |

---

## 5. Critical Coverage Model

A foundational design requirement of the SaaS frontend is to **never mislead users into assuming every Indian bill has a stock-market prediction**. The UI must enforce a clear, three-tier capability hierarchy:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        LEVEL 1 — MARKET-MODELLED (PRODUCTION)                          │
│  Central Parliament | 20 Bills | 47 Quant Companies | 940 Pairs | 4,700 Predictions   │
│  Predictions: AVAILABLE | Anticipation: AVAILABLE | Risk Tiers: AVAILABLE              │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                   LEVEL 2 — LEGISLATIVE + ECONOMIC INTELLIGENCE                        │
│  4 States (AP, KA, KL, TS) | 44 Bills | 44 PDFs | 44 Knowledge Dossiers | 86 Exposures│
│  Predictions: ZERO (FIREWALLED) | Statutory Analysis: AVAILABLE | AI: AVAILABLE        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                       LEVEL 3 — DISCOVERY / FUTURE ROADMAP                             │
│  24 Remaining States & UTs | Roadmap Transparency | Scraper Architecture               │
│  Bills Ingested: 0 | Predictions: ZERO | Status: CLEARLY MARKED AS "PLANNED"           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Coverage Tier Matrix

| Dimension | Level 1: Market-Modelled | Level 2: Legislative & Economic Intel | Level 3: Discovery / Roadmap |
| :--- | :--- | :--- | :--- |
| **Jurisdictions Covered** | Central Government of India (Parliament) | Andhra Pradesh, Karnataka, Kerala, Telangana | 24 Remaining Indian States and Union Territories |
| **Active Bills Ingested** | 20 production modeled bills | 44 State legislative bills (AP: 12, KA: 11, KL: 11, TS: 10) | 0 bills ingested |
| **Primary Sources** | Official Lok Sabha / Rajya Sabha / Gazette PDFs | 44/44 Official State Assembly Gazettes & PDFs | Official Assembly Portals identified in roadmap |
| **Corporate Exposure** | 47 NSE-listed quantitative companies (940 pairs) | 86 validated statutory corporate exposures (20 entities) | None |
| **Market Predictions** | **4,700 verified predictions** across 5 event windows | **STRICTLY 0 PREDICTIONS** (Econometrically firewalled) | **STRICTLY 0 PREDICTIONS** |
| **Anticipation Analysis** | 940 pre-event anticipation scores & diffusion metrics | Not applicable (no market price models) | Not applicable |
| **Risk / Decision Support** | 4,700 institutional risk tier records | Qualitative compliance & economic transmission channels | None |
| **Stakeholder Reports** | 14,100 structured reports (Investor, Business, Public) | Structured legislative summaries and policy domain notes | None |
| **AI Analyst Grounding** | Grounded in bill text, exposures, and prediction stats | Grounded in bill text, state gazettes, and exposure evidence | Explains roadmap status and coverage timeline |
| **UI Presentation** | Full quantitative dashboard, charts, gauges, risk tiers | Qualitative dossier, exposure citations, **"No Stock Model" banner** | Roadmap card, **"Coverage Planned" tag**, zero fake records |

> [!IMPORTANT]
> The SaaS UI must **never** present a missing prediction as an error, crash, or 404. Level 2 State bills must proudly display a **"Qualitative Legislative & Economic Intelligence Layer"** badge, accompanied by an explicit disclosure explaining that econometric models are intentionally isolated to Central quantitative equities.

---

## 6. Proposed SaaS Information Architecture

### Technology Stack
- **Frontend Framework**: Next.js 15 (App Router), React 19, TypeScript
- **Styling**: Tailwind CSS, CSS Modules, Lucide React icons, Radix UI / shadcn/ui primitives
- **Data Fetching & State**: TanStack Query (React Query v5) for server cache; Zustand for UI preferences
- **Visualizations**: Recharts / Tremor for charts; Plotly.js for advanced 2D risk matrices and backtesting curves
- **Backend**: Python 3.11+ / FastAPI with Pydantic v2 schemas wrapping existing Python services
- **Internal Research UI**: Retain existing Streamlit app (`dashboard/app.py`) for offline QA and academic validation

### Information Architecture & Sitemap

```
/ (Marketing & Institutional Landing)
│
├── /overview (Executive Dashboard & Recent Activity)
├── /explorer (Unified India Legislative Explorer — Central + State)
│
├── /bills (Legislative Directory)
│   ├── /bills/[billId] (Comprehensive Bill Detail Dossier)
│   └── /bills/compare (Side-by-Side Multi-Bill Comparison)
│
├── /companies (Corporate Universe Directory)
│   └── /companies/[companyId] (Company Intelligence & Exposure Dossier)
│
├── /sectors (Sectoral Intelligence & Legislative Heatmap)
│   └── /sectors/[sectorId] (Sector Detail & Impacted Entities)
│
├── /industries (Sub-Sector & Industry Explorer)
│
├── /states (State Legislative Intelligence Explorer)
│   └── /states/[state] (State Dossier, Assemblies & Economic Profile)
│
├── /predictions (Central Market Impact Predictions Explorer)
│   └── /predictions/[predictionId] (Prediction & Decision Deep-Dive)
│
├── /risk (Institutional Risk Matrix & Capital Allocation)
├── /anticipation (Pre-Event Anticipation & Market Diffusion Analysis)
├── /backtesting (Walk-Forward Strategy Validation Summary)
│
├── /monitoring (Real-Time Legislative Source Monitoring)
│
├── /watchlists (Watchlist Management & Entity Subscriptions)
│   └── /watchlists/[watchlistId] (Watchlist Detail, Items & Alert Rules)
│
├── /alerts (Alert Feed, Temporal Clusters & Notifications)
├── /notifications (In-App Notification Center Drawer / Page)
│
├── /ai-analyst (Interactive AI Legislative Copilot & Query Engine)
├── /coverage (Platform Coverage, Methodology & Capability Transparency)
└── /settings (User Profile, Notification Channels & Alert Preferences)
```

---

## 7. Proposed Route Map & Page Specifications

| Route | Page Name | Primary Objective | Key UI Components | Underlying Backend Service |
| :--- | :--- | :--- | :--- | :--- |
| `/` | Landing Page | Academic & institutional introduction, coverage highlights, sample insights | Hero banner, live stats counter, sample bill cards, methodology highlights, academic disclaimer | `UnifiedLegislativeDiscoveryService` |
| `/overview` | SaaS Overview | Macro executive dashboard for authenticated analysts | Top KPI ribbon, new bills ticker, high-impact alerts feed, cross-sector distribution bar chart | `UnifiedLegislativeDiscoveryService`, `DashboardService` |
| `/explorer` | India Legislative Explorer | Primary multi-jurisdiction discovery engine | Coverage status pill, Explore India taxonomy pills, multi-attribute filter bar, unified bill card grid | `UnifiedLegislativeDiscoveryService` |
| `/bills` | Bills Master Directory | Filterable master catalog of Central and State legislation | TanStack data table, jurisdiction tabs (All/Central/State), sector filter, status badges | `UnifiedLegislativeDiscoveryService` |
| `/bills/[billId]` | Bill Detail Dossier | Comprehensive legislative, economic, corporate, and predictive dossier | Sticky header, Fact/Derived/Interpretation/Prediction sections, exposure table, AI drawer | `UnifiedLegislativeDiscoveryService`, `CompanyIntelligenceService`, `PredictionRepository` |
| `/bills/compare` | Bill Comparison | Side-by-side comparative analysis of 2-3 bills | Differential table, provisions contrast, economic mechanisms comparison, AI comparative synthesis | `UnifiedLegislativeDiscoveryService`, `AIExplanationService` |
| `/companies` | Company Universe | Directory of 70 corporations and entities | Universe tabs (All / Quantitative Modeled / Intelligence Only), sector filter, exposure count column | `CompanyIntelligenceService` |
| `/companies/[companyId]` | Company Detail | Per-company exposure, operating footprint, and modeling status | Profile card, firewall status badge, operating states map, related bills table, prediction tab (quant only) | `CompanyIntelligenceService`, `PredictionRepository` |
| `/sectors` | Sectoral Intelligence | High-level sectoral exposure matrix | Sector cards with bill counts, company counts, market impact summary | `UnifiedLegislativeDiscoveryService`, `CompanyIntelligenceService` |
| `/states` | State Intelligence | State assembly coverage and roadmap | Map of India with 4 active states highlighted, 24 planned states, assembly source status | `UnifiedLegislativeDiscoveryService`, `StateKnowledgeService` |
| `/states/[state]` | State Dossier | Single state deep dive (AP, KA, KL, TS) | State economic profile, assembly session status, bill list, corporate exposure list, gazette links | `StateKnowledgeService`, `StateBillRepository` |
| `/predictions` | Predictions Explorer | Master quantitative prediction table (Level 1 Central only) | Multi-event window tabs, probability slider, direction filter, confidence badge, export CSV | `PredictionRepository`, `DecisionRepository` |
| `/predictions/[predictionId]` | Prediction Detail | Micro-level inspection of bill-company pair forecast | Prediction gauge, event window comparison, SHAP feature importance chart, decision risk tier | `PredictionRepository`, `DecisionRepository`, `ExplainabilityRepository` |
| `/risk` | Risk Overview | Institutional portfolio risk classification | 2D Risk Matrix (Probability vs Impact), Tier 1-4 breakdown, capital allocation recommendations | `DecisionRepository`, `DashboardService` |
| `/anticipation` | Anticipation Analysis | Pre-event market diffusion and pricing-in analysis | Diffusion timeline, Anticipation Paradox indicator, public media evidence log | `AnticipationRepository`, `AnticipationService` |
| `/backtesting` | Backtesting Results | Out-of-sample historical walk-forward performance | Cumulative return curve vs Nifty 50, maximum drawdown chart, annual performance table | `BacktestRepository` |
| `/monitoring` | Legislative Monitor | Operational status of legislative web scrapers | Source health status, last poll timestamp, change feed, manual trigger button | `services/monitoring/` |
| `/watchlists` | Watchlists Hub | Manage user watchlists and subscription dimensions | Watchlist cards, create watchlist modal, subscriber counts, quick add entity | `WatchlistService`, `WatchlistIndexService` |
| `/watchlists/[watchlistId]` | Watchlist Detail | Configure watched entities, rules, and alerts | Entities table (companies, bills, sectors, states), alert rules editor, threshold slider | `WatchlistService`, `AlertRuleRepository` |
| `/alerts` | Alert Feed | Real-time and clustered alert feed | Temporal event groups, severity tags, deep link to bill/company, filter by watchlist | `AlertMatchingService`, `AlertAggregationService` |
| `/notifications` | Notification Center | User notification inbox | Unread badge, filter read/unread/archived, mark as read button, delivery status | `NotificationCenterService` |
| `/ai-analyst` | AI Legislative Analyst | Interactive chat & structured inquiry interface | Chat input, suggested questions, FACT/DERIVED/INTERPRETATION/PREDICTION chips, citation links | `AIExplanationService`, `AIContextBuilder` |
| `/coverage` | Coverage & Transparency | Academic transparency and capability breakdown | 3-tier coverage matrix, statistics tables, methodology citations, limitations disclaimer | Hardcoded registries & repo counts |
| `/settings` | User Settings | Profile, tenants, and notification channels | Tenant info, webhook URL + secret configuration, email/push toggles, digest frequency | `UserRepository`, `AlertPreferenceRepository` |

---

## 8. Bill Detail Experience Design

The Bill Detail page is the cornerstone of the application. It must present complex legislative, economic, corporate, and predictive data with total clarity while maintaining strict separation between **verifiable facts** and **analytical inferences**.

### Section-by-Section Epistemic Breakdown

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ [STICKY TOP BAR]  Bill Title | Bill Number | Jurisdiction Badge | Watchlist Bookmark    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. BILL IDENTITY & OFFICIAL PROVENANCE (FACT)                                          │
│    - Jurisdiction: Central Parliament (Lok Sabha / Rajya Sabha) OR State Assembly      │
│    - Status: Introduced / Passed / Pending Assent | Dates: Authoritative Only         │
│    - Official Sources: Gazette Link | Official PDF Download | SHA-256 Provenance Hash  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. SUMMARY & STATUTORY STRUCTURE (FACT + DERIVED)                                      │
│    - Official Overview & Stated Legislative Intent                                     │
│    - Key Provisions Accordion (Section-by-section breakdown)                           │
│    - Policy Domain Tags (e.g. Financial Regulation, Gig Economy, Public Health)        │
│    - Primary & Secondary Economic Sectors Mapped                                       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. CORPORATE EXPOSURE & ECONOMIC MECHANISMS (DERIVED + INTERPRETATION)                 │
│    - Table of impacted companies (Direct vs Indirect, Exposure Strength, Mechanism)   │
│    - Statutory Citation Evidence (e.g. "Section 3(1) mandates 1-2% welfare cess")      │
│    - Transmission Channels (Compliance Costs, Capex Requirements, Revenue Disruption)  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. MARKET PREDICTION & RISK SUPPORT (PREDICTION — LEVEL 1 CENTRAL ONLY)               │
│    * If Central Level 1 Bill:                                                          │
│      - Direction Forecast (Positive / Negative / Neutral) & Probability Gauge (e.g. 74%)│
│      - Event Window Comparison ([-1,+1], [-2,+2], [-5,+5], [-10,+10], [-30,+30])       │
│      - Model Confidence Score & Top Predictive Features (SHAP values)                  │
│      - Anticipation Paradox Badge (e.g. "Priced-In (High Diffusion)")                  │
│      - Institutional Risk Tier (Tier 1-4) & Downside Sensitivity                       │
│      - Multi-Stakeholder Tabs (Investor View / Business View / Public Policy View)     │
│    * If State Level 2 Bill:                                                            │
│      - PROMINENT BANNER: "Qualitative Legislative & Economic Intelligence Mode"        │
│      - Explicit Notice: "State Assembly bills are strictly firewalled from quantitative│
│        market prediction models. Stock forecasts are not computed for State bills."    │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. AI ANALYST EXPLANATION PANEL                                                        │
│    - Synthesized structured summary with [FACT], [DERIVED], [INTERPRETATION] chips     │
│    - Proactive questions ("Which companies bear highest compliance cost?", etc.)       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Company Detail Experience Design

The Company Detail experience must support both **Quantitative Modeled Companies** and **Intelligence-Only Entities** without confusing their capabilities or breaking the quantitative firewall.

### A. Quantitative Companies (47 Central-Modeled)
- **Identity & Master Data**: Legal name, NSE/BSE tickers, ISIN, Sector, Industry, Market cap category (Large/Mid/Small), HQ state, operating states.
- **Badge**: `🏛️ QUANTITATIVE MODELLED (LEVEL 1)`.
- **Active Legislative Exposures**: Table of Central bills impacting the company, direct vs indirect exposure, statutory evidence, and economic transmission mechanisms.
- **Aggregated Market Predictions**:
  - Net legislative sentiment across pending/passed bills.
  - Event-window sensitivity profile (how quickly the stock reacts).
  - Decision-support risk tier (Tier 1 to 4) and capital allocation guidance.
  - Anticipation score and diffusion metrics.
- **AI Analyst**: Synthesizes regulatory exposure across all bills with grounded citations.

### B. Intelligence-Only Companies & Entities (20 Curated Entities)
- **Identity & Structure**: Legal name, Entity Type (Unlisted Company, Public Utility, State-Owned Enterprise, Private Company, Industry Association), Sector, Industry, HQ & State operational footprint.
- **Badge**: `🇮🇳 QUALITATIVE INTELLIGENCE ONLY (LEVEL 2)`.
- **Quantitative Firewall Banner**:
  > [!NOTE]
  > **Quantitative Model Isolation Active**  
  > This entity belongs to the qualitative corporate intelligence universe. In accordance with platform governance and econometric validity standards, unlisted entities and state-level utilities are strictly isolated from stock-market price prediction models. No stock return or trading signals are generated.
- **Validated Legislative Exposures**:
  - Detailed table of State and Central bills affecting the entity.
  - Verifiable evidence: statutory section citations (e.g. Kerala Gig Workers Welfare Act Section 3(1)), operational facility references, and state government circulars.
  - Economic mechanisms: fee mandates, licensing restrictions, compliance burdens.
  - Geographic presence verification: confirmed operational presence in the regulating State.
- **AI Analyst**: Focuses exclusively on operational compliance, cost impacts, and statutory liabilities—with zero stock forecasts.

---

## 10. Search & Discovery UX

### Unified Global Search Engine
The platform requires a centralized, multi-attribute discovery system available via a global search bar and a keyboard-accessible Command Palette (`Cmd+K` / `Ctrl+K`).

### Supported Attributes & Matching Rules
1. **Title & Short Title**: Exact and prefix matching with fuzzy fallback.
2. **Bill Number & Act Number**: Exact alphanumeric lookup (e.g., `"Bill No. 104 of 2024"`).
3. **Company Names & Tickers**: Resolves NSE ticker (`"RELIANCE"`), legal name (`"Reliance Industries Limited"`), and corporate aliases (`"Swiggy"`, `"Zomato"`, `"KSEB"`).
4. **Sectors & Industries**: Matches across 18 canonical sectors (e.g., `"Labour"`, `"Banking"`, `"Energy"`).
5. **Jurisdiction & State**: Filters by `"Central"`, `"State"`, or specific states (`"Kerala"`, `"Telangana"`).
6. **Market Relevance**: Filters by `"HIGH"`, `"MEDIUM"`, `"LOW"`, `"NONE"`.
7. **Corporate Exposure**: Filters bills with verified corporate exposure vs without.

### Autocomplete & Empty States
- **Sub-50ms Typeahead**: Categorized results grouped into `Bills (Central)`, `Bills (State)`, `Companies (Quant)`, `Companies (Intel)`, and `Sectors`.
- **No Results Found**: Provides actionable alternatives: "No legislative records matched 'crypto'. Would you like to explore related bills under **Banking & Finance**?"
- **Un-Ingested State Queries**: When searching for an un-ingested state (e.g., `"Maharashtra"`, `"Gujarat"`), displays a helpful status card:
  > **State Assembly on Roadmap**  
  > Maharashtra Legislative Assembly is planned for Tier-2 expansion. Official portal scrapers are under active development. 0 bills currently ingested.

---

## 11. Watchlist & Alert UX

The watchlist and alert system connects legislative changes to targeted user feeds while maintaining strict tenant isolation.

### Core User Flows
1. **Watchlist Creation**:
   - Create named watchlists (e.g., `"Tech & Gig Economy"`, `"Energy Sector Monitor"`).
   - Set custom alert rules: Minimum severity threshold (`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), allowed alert types.
2. **Entity Subscriptions (6 Dimensions)**:
   - Add **Company** (e.g., Swiggy, Reliance).
   - Add **Bill** (e.g., Banking Laws Amendment Bill 2024).
   - Add **Sector** (e.g., Information Technology).
   - Add **Industry** (e.g., Food Delivery & Quick Commerce).
   - Add **State** (e.g., Karnataka, Kerala).
   - Add **Jurisdiction** (e.g., Central, State).
3. **Alert Activity Feed (`/alerts`)**:
   - Shows chronological and clustered alert cards generated by the `AlertPipelineService`.
   - Displays matched dimension tags (e.g., `Matched via: Company (Swiggy) + State (Kerala)`).
   - Shows severity pill, source event summary, and deep link.
4. **In-App Notification Center (`/notifications`)**:
   - Dropdown panel in top navigation + dedicated full-page inbox.
   - Unread count badge updated in real time.
   - Actions: Mark as Read, Mark All Read, Archive.
5. **Digest Preferences (`/settings`)**:
   - Configure frequency: Real-time, Daily Digest (specify time in IST), Weekly Digest.
   - Outbound channel toggles: Email, Push, Webhooks.
   - Webhook configuration: HTTPS endpoint URL, secret key generation, payload test button.

---

## 12. AI Analyst UX

The AI Analyst provides natural language explanations powered by the existing Groq LLM integration and the structured `AIContextBuilder`.

### Key UX Guardrails
1. **Four-Tier Grounded Content Separation**:
   Every response must be visually segregated using distinct badges:
   - `[FACTS]`: Official dates, bill titles, enacted provisions, legal citations.
   - `[DERIVED]`: Computed sector mappings, candidate companies, exposure counts.
   - `[INTERPRETATION]`: Qualitative economic mechanism analysis, compliance impacts.
   - `[PREDICTION]`: Machine learning model forecasts (Central only; clearly designated as model outputs).
2. **Mandatory Statutory Disclaimer**:
   Every AI card or chat response includes:
   *"Antigravity AI Analyst provides academic research synthesis based on official records and statistical models. It does not provide legal advice or financial trading recommendations."*
3. **Proactive Context-Aware Prompts**:
   When viewing a bill or company, the UI displays clickable prompt chips:
   - *"What are the primary compliance obligations in this bill?"*
   - *"Which sectors experience the highest economic friction?"*
   - *"Explain why this company is exposed to the legislation."*
   - *(Central Only)*: *"Explain why the model predicts positive market impact."*
   - *(Central Only)*: *"What evidence supports the anticipation score?"*
4. **Side-by-Side Bill Comparison**:
   Allows selecting two bills (e.g., Central Gig Workers provisions vs Karnataka Gig Workers Bill) and generates a side-by-side comparative table of definitions, welfare cess rates, dispute mechanisms, and penalties.

---

## 13. Source & Provenance UX

To maintain academic and institutional credibility, every substantive claim must have direct, verifiable provenance.

### Visual Provenance Elements
1. **Authoritative Source Badges**:
   - `🏛️ Lok Sabha Official Portal`
   - `🏛️ Rajya Sabha Official Portal`
   - `📜 Gazette of India`
   - `🇮🇳 Kerala Legislative Assembly Official Gazette`
   - `🇮🇳 Karnataka Legislative Assembly Official Portal`
   - `🇮🇳 Telangana State Assembly Official Portal`
   - `🇮🇳 Andhra Pradesh State Gazette`
2. **Official Document Access**:
   - Direct link to official government portal URL.
   - Direct download button for official gazette PDF stored in repository (`data/bills/` or `data/state_bills/`).
   - In-app PDF viewer drawer with page-specific jump links where available.
3. **Provenance Audit Drawer**:
   An expandable panel on every dossier displaying field-by-field audit provenance:
   - `Bill Title`: AUTHORITATIVE (Official Assembly Record)
   - `Introduction Date`: AUTHORITATIVE (Official Session Bulletin; never inferred)
   - `Provisions`: DERIVED (NLP extraction verified against official text)
   - `Corporate Exposure`: DERIVED (Statutory section cited + corporate operational filing)
   - `Market Prediction`: MODEL_OUTPUT (Central ML model artifact hash; zero for State bills)
4. **Data Freshness Indicator**:
   Displays last scraper check timestamp and data version hash.

---

## 14. Coverage & Capabilities Page Design

A dedicated `/coverage` page makes the platform's current scope completely transparent to institutional reviewers and academic examiners.

### Page Sections
1. **India-Wide Legislative Landscape Overview**:
   - Total legislative jurisdictions in India: 1 Central Parliament + 28 States + 3 UTs with assemblies = 32 jurisdictions.
   - Visual interactive map of India with states color-coded by implementation status:
     - **Active Market-Modelled (Central)**: Navy Blue
     - **Active Economic & Legislative Intelligence (4 States)**: Emerald Green
     - **Planned Expansion Roadmap (24 States/UTs)**: Slate Gray
2. **Current Quantified Scope Table**:
   - Central Production Bills: **20**
   - Central Quantitative Companies: **47**
   - Central Bill-Company Pairs: **940**
   - Central Predictions: **4,700**
   - Central Decisions: **4,700**
   - Central Anticipation Scores: **940**
   - Central Stakeholder Reports: **14,100**
   - Implemented State Bills: **44** (AP: 12, KA: 11, KL: 11, TS: 10)
   - Implemented State Gazette PDFs: **44 / 44**
   - Implemented State Knowledge Records: **44 / 44**
   - Validated State Corporate Exposures: **86**
   - State Stock Predictions: **EXACTLY 0**
   - Total Corporate Universe: **70 entities** (47 quant, 20 intelligence, 3 reference)
3. **State Expansion Roadmap & Ingestion Criteria**:
   - Explains technical prerequisites for ingesting a new state assembly: digitized official gazette availability, machine-readable text, structured assembly bulletin feeds.
4. **Academic & Non-Financial Advice Disclaimer**:
   - Formal institutional research statement.

---

## 15. Required Future API Contracts (REST / FastAPI)

These REST API endpoints will be implemented in **Task 8.14.2** to power the SaaS frontend. They wrap the existing Python services layer without duplicating business logic.

### 1. Legislative Discovery & Bill APIs

#### `GET /api/v1/bills`
- **Purpose**: Retrieve paginated, filterable list of unified legislative bills (Central & State).
- **Service**: `UnifiedLegislativeDiscoveryService.get_all_bills()`
- **Query Params**: `page=1`, `limit=20`, `jurisdiction` (`all|central|state`), `state`, `sector`, `market_relevance`, `search`
- **Response**: `{ items: UnifiedBillRecord[], total: int, page: int, pages: int }`
- **Auth**: Public / Optional Bearer
- **Priority**: **P0 (Critical)**

#### `GET /api/v1/bills/{bill_id}`
- **Purpose**: Retrieve complete bill detail dossier.
- **Service**: `UnifiedLegislativeDiscoveryService.get_bill_by_id(bill_id)`
- **Response**: `UnifiedBillRecord` + `ProvenanceAuditMap`
- **Auth**: Public
- **Priority**: **P0 (Critical)**

#### `GET /api/v1/bills/{bill_id}/exposures`
- **Purpose**: Retrieve corporate exposure list for a bill with statutory citations.
- **Service**: `CompanyIntelligenceService.get_companies_for_bill(bill_id)`
- **Response**: `{ bill_id: str, exposures: CompanyBillExposureView[] }`
- **Auth**: Public
- **Priority**: **P0 (Critical)**

#### `POST /api/v1/bills/compare`
- **Purpose**: Comparative analysis between 2 or 3 bills.
- **Service**: `UnifiedLegislativeDiscoveryService`, `AIExplanationService`
- **Body**: `{ bill_ids: string[] }`
- **Response**: `{ bills: UnifiedBillRecord[], comparison_matrix: dict, ai_summary: dict }`
- **Auth**: Public / Authenticated
- **Priority**: **P1 (High)**

---

### 2. Corporate Intelligence APIs

#### `GET /api/v1/companies`
- **Purpose**: Retrieve corporate universe directory with filtering.
- **Service**: `CompanyIntelligenceService.get_all_company_summaries()`
- **Query Params**: `page=1`, `limit=20`, `universe_type` (`all|quantitative|intelligence`), `sector`, `entity_type`, `search`
- **Response**: `{ items: CompanySummary[], total: int, page: int }`
- **Auth**: Public
- **Priority**: **P0 (Critical)**

#### `GET /api/v1/companies/{company_id}`
- **Purpose**: Retrieve comprehensive company profile and dossier.
- **Service**: `CompanyIntelligenceService.get_company_profile(company_id)`
- **Response**: `CompanyProfileView` (includes firewall status and related bills)
- **Auth**: Public
- **Priority**: **P0 (Critical)**

#### `GET /api/v1/companies/{company_id}/exposures/{bill_id}/explain`
- **Purpose**: Retrieve deterministic explanation of why a company is exposed to a bill.
- **Service**: `CompanyIntelligenceService.explain_company_exposure(company_id, bill_id)`
- **Response**: `CompanyExposureExplanation`
- **Auth**: Public
- **Priority**: **P1 (High)**

---

### 3. Quantitative Prediction & Risk APIs (Level 1 Central Only)

#### `GET /api/v1/predictions`
- **Purpose**: Filterable master list of Central market predictions.
- **Service**: `PredictionRepository.load_all()`, `DecisionRepository.load_all()`
- **Query Params**: `page=1`, `limit=50`, `bill_id`, `company_isin`, `event_window`, `direction`, `min_confidence`
- **Response**: `{ items: PredictionRecord[], total: int }`
- **Auth**: Public
- **Priority**: **P0 (Critical)**

#### `GET /api/v1/predictions/{prediction_id}`
- **Purpose**: Single prediction record with decision support and explainability.
- **Service**: `PredictionRepository.get()`, `DecisionRepository.get()`
- **Response**: `{ prediction: PredictionRecord, decision: DecisionSupportRecord, explainability: dict }`
- **Auth**: Public
- **Priority**: **P1 (High)**

#### `GET /api/v1/bills/{bill_id}/anticipation`
- **Purpose**: Pre-event anticipation scores and diffusion metrics for a bill.
- **Service**: `AnticipationRepository.get_scores_by_bill(bill_id)`
- **Response**: `{ bill_id: str, scores: AnticipationScore[], bill_record: BillAnticipationRecord }`
- **Auth**: Public
- **Priority**: **P1 (High)**

#### `GET /api/v1/reports/{bill_id}/{company_isin}/{event_window}/{stakeholder_type}`
- **Purpose**: Retrieve structured stakeholder analytical report.
- **Service**: `ReportRepository.get_report()`
- **Response**: `StakeholderReport`
- **Auth**: Public
- **Priority**: **P1 (High)**

---

### 4. Watchlists & Alert APIs

#### `GET /api/v1/watchlists`
- **Purpose**: List watchlists for authenticated user/tenant.
- **Service**: `WatchlistService.list_watchlists(user_id, tenant_id)`
- **Response**: `Watchlist[]`
- **Auth**: JWT Bearer (Enforces tenant isolation)
- **Priority**: **P0 (Critical)**

#### `POST /api/v1/watchlists`
- **Purpose**: Create a new watchlist.
- **Service**: `WatchlistService.create_watchlist()`
- **Body**: `{ name: str, description: str, rules: AlertRuleCreate[] }`
- **Response**: `Watchlist`
- **Auth**: JWT Bearer
- **Priority**: **P0 (Critical)**

#### `POST /api/v1/watchlists/{watchlist_id}/items`
- **Purpose**: Add entity item to watchlist (synchronizes inverted index).
- **Service**: `WatchlistService.add_item()`
- **Body**: `{ entity_type: str, entity_id: str, entity_name: str, state: Optional[str] }`
- **Response**: `WatchlistItem`
- **Auth**: JWT Bearer
- **Priority**: **P0 (Critical)**

#### `DELETE /api/v1/watchlists/{watchlist_id}/items/{item_id}`
- **Purpose**: Remove entity item from watchlist.
- **Service**: `WatchlistService.remove_item()`
- **Response**: `{ success: bool }`
- **Auth**: JWT Bearer
- **Priority**: **P0 (Critical)**

#### `GET /api/v1/alerts`
- **Purpose**: Retrieve alert feed matching user subscriptions.
- **Service**: `AlertMatchingService`, `AlertAggregationService`
- **Query Params**: `page=1`, `limit=30`, `severity`, `watchlist_id`
- **Response**: `{ items: AlertEvent[], total: int }`
- **Auth**: JWT Bearer
- **Priority**: **P0 (Critical)**

#### `GET /api/v1/notifications`
- **Purpose**: Retrieve in-app notification inbox.
- **Service**: `NotificationCenterService.list_notifications()`
- **Query Params**: `status` (`all|unread|read|archived`), `page=1`, `limit=20`
- **Response**: `{ items: Notification[], unread_count: int, total: int }`
- **Auth**: JWT Bearer
- **Priority**: **P0 (Critical)**

#### `PATCH /api/v1/notifications/{notification_id}/read`
- **Purpose**: Mark single notification as read.
- **Service**: `NotificationCenterService.mark_as_read()`
- **Response**: `{ success: bool }`
- **Auth**: JWT Bearer
- **Priority**: **P0 (Critical)**

---

### 5. AI Analyst & Search APIs

#### `POST /api/v1/ai/ask`
- **Purpose**: Execute natural language inquiry against grounded legislative context.
- **Service**: `AIExplanationService.explain_with_guardrails()`
- **Body**: `{ question: str, bill_id: Optional[str], company_id: Optional[str] }`
- **Response**: `{ facts: str[], derived: str[], interpretation: str[], prediction: Optional[str], disclaimer: str }`
- **Auth**: Authenticated / Rate-Limited
- **Priority**: **P0 (Critical)**

#### `GET /api/v1/search`
- **Purpose**: Global multi-attribute typeahead search.
- **Service**: `UnifiedLegislativeDiscoveryService.search()`
- **Query Params**: `q=query_string`, `limit=10`
- **Response**: `{ bills: UnifiedBillRecord[], companies: CompanySummary[], sectors: str[] }`
- **Auth**: Public
- **Priority**: **P0 (Critical)**

#### `GET /api/v1/coverage`
- **Purpose**: System capability statistics and coverage transparency.
- **Service**: `UnifiedLegislativeDiscoveryService.get_state_coverage()`
- **Response**: `{ central: dict, state: dict, companies: dict, models: dict }`
- **Auth**: Public
- **Priority**: **P0 (Critical)**

---

## 16. Security & Multi-Tenancy Findings

Transitioning from an internal Streamlit script to a multi-tenant SaaS application introduces critical security and tenancy requirements:

### Current Findings & Risks
1. **User & Tenant Scoping**:
   - *Current State*: `WatchlistService`, `NotificationCenterService`, and `AlertPipelineService` require `tenant_id` and `user_id` parameters and store records in tenant-partitioned paths (`storage/alerts/{tenant_id}/...`).
   - *SaaS Requirement*: An API middleware layer must extract `tenant_id` and `user_id` from verified JWT claims. Endpoint handlers must **never** trust user-supplied tenant IDs in query parameters.
2. **Filesystem Storage Persistence**:
   - *Current State*: Repositories write JSON files directly to local disks (`data/`, `storage/`).
   - *SaaS Requirement*: Local filesystem persistence works in development, but fails in containerized, multi-replica cloud environments (Docker/Kubernetes). Production migration will require migrating transactional tables (users, watchlists, alert rules, notifications) to a managed relational database (e.g. PostgreSQL with Row Level Security) while keeping static datasets (4,700 predictions, PDFs) on object storage (S3 / Cloud Storage).
3. **API Key & Secret Isolation**:
   - *Current State*: `GROQ_API_KEY` is read from environment variables or `.env`.
   - *SaaS Requirement*: Secrets must never be exposed to the Next.js client bundle. All LLM and external provider requests must execute server-side in FastAPI.
4. **Webhook Security**:
   - *Current State*: `WebhookNotificationProvider` implements HMAC-SHA256 request signing with `X-Notification-Signature` and `X-Notification-Timestamp`.
   - *SaaS Requirement*: User webhook secrets must be encrypted at rest (e.g. AES-256) in the database and redacted as `********` in all GET responses.
5. **Quantitative Model Protection**:
   - The FastAPI layer must strictly enforce that prediction endpoints reject any requests referencing State bills or intelligence-only entities with HTTP 400 (`Bad Request: Entity is firewalled from market models`).

---

## 17. Performance & Caching Requirements

The SaaS platform handles a substantial volume of analytical artifacts:
- 66 unified legislative bills
- 70 companies
- 104 company-bill exposures
- 4,700 Central prediction records
- 4,700 decision support records
- 940 anticipation score records
- 14,100 stakeholder reports
- 44 State PDFs (~80 MB total)

### Caching Architecture

```
Client (Browser) ───[ HTTP Cache: Cache-Control: max-age=3600 ]───► Next.js (Edge Cache)
                                                                           │
                                                                 [ REST API / JSON ]
                                                                           │
                                                                           ▼
FastAPI Backend ────[ In-Memory LRU / Redis Cache (5 min TTL) ]───► Repositories
                                                                           │
                                                                    [ JSON on Disk ]
```

### Performance Optimization Strategies
1. **HTTP Caching**:
   - Since Central model predictions, decisions, anticipation scores, and stakeholder reports are **frozen production artifacts**, their API responses can be cached aggressively with `Cache-Control: public, max-age=86400, immutable`.
2. **Server-Side Pagination**:
   - Endpoints returning collections (`/api/v1/predictions`, `/api/v1/bills`, `/api/v1/alerts`) must enforce default limits of 20 to 50 records per page.
3. **Lazy Loading of Heavy Dossier Subsections**:
   - The Bill Detail page must load core legislative metadata first (< 100ms).
   - Predictions, anticipation charts, stakeholder reports, and AI explanations should be fetched asynchronously in secondary requests when their respective tabs are opened.
4. **Fast Autocomplete Indexing**:
   - Pre-load a lightweight search index (< 250 KB compressed) containing all 66 bill titles, 70 company names, tickers, and sectors into client memory using MiniSearch for instant (< 15ms) Command Palette results without server roundtrips.
5. **In-Memory Inverted Index**:
   - Keep the `WatchlistIndexService` inverted indices in application memory on the backend for O(1) subscriber matching during monitoring ingestion.

---

## 18. Migration Strategy from Streamlit to SaaS

We recommend a phased, non-breaking migration strategy:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Architecture & UI Audit (Task 8.14.1) ───────────────► [COMPLETED]   │
│ - Baseline frozen, capability matrix defined, routes specified                 │
├────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2: REST API Layer Implementation (Task 8.14.2)                           │
│ - Implement FastAPI application in backend/api/                                │
│ - Expose P0/P1 endpoints wrapping existing Python services                     │
│ - Add OpenAPI / Swagger documentation & API integration tests                  │
├────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 3: SaaS Frontend Project Initialization (Task 8.14.3)                    │
│ - Initialize Next.js 15 app in frontend/ directory                             │
│ - Setup Tailwind CSS, shadcn/ui components, TypeScript schemas                 │
│ - Configure TanStack Query, layout shell, navbar, and Command Palette          │
├────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 4: Core Discovery & Dossier Pages (Task 8.14.4)                          │
│ - Implement /explorer, /bills, /bills/[billId], /companies, /companies/[id]   │
│ - Implement Level 1 vs Level 2 coverage badges & quantitative firewall UI      │
├────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 5: Quantitative Intelligence & Risk Pages (Task 8.14.5)                  │
│ - Implement /predictions, /risk, /anticipation, and multi-stakeholder views    │
├────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 6: Watchlists, Alerts & AI Analyst Integration (Task 8.14.6)             │
│ - Implement /watchlists, /alerts, /notifications center, and /ai-analyst chat  │
├────────────────────────────────────────────────────────────────────────────────┤
│ PHASE 7: E2E Verification & Streamlit Dual-Mode Hardening (Task 8.14.7)       │
│ - End-to-end integration tests between Next.js and FastAPI                     │
│ - Document dual-mode operational runbook                                       │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 19. What Should Remain in Streamlit

The Streamlit dashboard (`dashboard/app.py`) is a valuable asset that should **not** be deleted or abandoned. It should be explicitly preserved as an **Internal Research, Model QA, and Offline Audit Station**:

| Workflow / Use Case | Recommended Interface | Rationale |
| :--- | :---: | :--- |
| **Commercial SaaS User (Financial Analyst, Policy Officer)** | **Next.js Frontend** | Needs responsive UI, bookmarks, notifications, fast search, multi-tenant security |
| **Academic / Offline Defense & Model Audit** | **Streamlit** | Immediate Python runtime execution, zero build step, raw DataFrame inspections |
| **Historical Walk-Forward Backtesting Deep Dive** | **Streamlit** | Dynamic Python parameter tuning, raw slice inspection, direct plot rendering |
| **SHAP Feature Importance & Explainability QA** | **Streamlit** | Interactive Matplotlib / SHAP force plots that are costly to rebuild in React |
| **Scraper Debugging & Ingestion Inspection** | **Streamlit** | Direct access to local filesystem paths and scraper exception tracebacks |
| **Model Re-validation & Parity Checks** | **Streamlit** | Evaluates production scope parity directly against Python repository instances |

---

## 20. Recommended Implementation Order for Task 8.14.2 Onward

The immediate next task should be strictly bounded to backend API foundation:

### Next Task: `TASK 8.14.2 — FASTAPI BACKEND REST SERVICE & API LAYER`
**Scope**:
1. Create a clean FastAPI application module (e.g., `services/api/` or `api/main.py`).
2. Implement typed Pydantic v2 request/response models corresponding to the contracts in Section 15.
3. Expose P0 endpoints:
   - `GET /api/v1/bills` & `GET /api/v1/bills/{id}`
   - `GET /api/v1/companies` & `GET /api/v1/companies/{id}`
   - `GET /api/v1/predictions` & `GET /api/v1/predictions/{id}`
   - `GET /api/v1/search`
   - `GET /api/v1/coverage`
   - `GET /api/v1/watchlists` & `POST /api/v1/watchlists`
   - `GET /api/v1/notifications`
4. Add CORS middleware for Next.js localhost development.
5. Create comprehensive API tests (`tests/test_api_endpoints.py`) verifying parity with underlying Python services.

Do not start frontend code until Task 8.14.2 is complete and all API contracts are tested and verified.

---

## 21. Risks, Guardrails & Limitations

1. **Econometric Integrity Risk**:
   - *Risk*: A frontend developer might accidentally hook a State bill into a prediction chart or show a random return percentage.
   - *Guardrail*: The backend API must return `prediction_available: false` and `prediction_data: null` for all State bills and intelligence entities, and the frontend components must conditionally unmount all predictive charts when this flag is false.
2. **File I/O Bottlenecks on Prediction Endpoints**:
   - *Risk*: Loading 4,700 individual JSON files on disk during a `/api/v1/predictions` request would cause multi-second latency.
   - *Guardrail*: Implement in-memory index caching on FastAPI startup, or load from a pre-indexed SQLite/Parquet cache table for fast pagination.
3. **AI Hallucination & Advisory Liability**:
   - *Risk*: Groq LLM generating speculative stock predictions or buy/sell advice.
   - *Guardrail*: The existing `ai_guardrails.py` system prompt must continue to strip forbidden predictive language, enforce the academic disclaimer, and forbid financial recommendations.
4. **Headless Test Environment Limitation**:
   - *Risk*: Streamlit rendering calls in `dashboard/pages/` require a Streamlit runtime and fail when invoked in pure pytest headless mode.
   - *Mitigation*: Existing unit tests correctly test backend logic and service functions; UI-level tests are skipped when Streamlit is headless.

---

## 22. Baseline Verification Audit

An automated baseline verification script confirmed 100% data integrity against the frozen baseline:

| Metric / Artifact | Required Frozen Baseline | Verified Actual Count | Audit Status |
| :--- | :---: | :---: | :---: |
| **Central Production Modeled Bills** | 20 | 20 | **PASS** |
| **Central Quantitative Companies** | 47 | 47 | **PASS** |
| **Central Bill-Company Pairs** | 940 | 940 | **PASS** |
| **Central Prediction Records** | 4,700 | 4,700 | **PASS** |
| **Central Decision Support Records** | 4,700 | 4,700 | **PASS** |
| **Anticipation Bias Scores** | 940 | 940 | **PASS** |
| **Stakeholder Reports** | 14,100 (4,700 x 3) | 14,100 (4,700 Inv, 4,700 Biz, 4,700 Pub) | **PASS** |
| **Event Windows Modeled** | 5 ([-1,+1], [-2,+2], [-5,+5], [-10,+10], [-30,+30]) | 5 | **PASS** |
| **State Legislative Bills** | 44 | 44 (AP: 12, KA: 11, KL: 11, TS: 10) | **PASS** |
| **State Official Gazette PDFs** | 44 / 44 | 44 / 44 | **PASS** |
| **State Knowledge Records** | 44 / 44 | 44 / 44 | **PASS** |
| **State Corporate Exposures** | 86 | 86 | **PASS** |
| **State Stock Price Predictions** | **0** | **0** | **PASS** |
| **Total Company Records** | 70 | 70 (47 quant, 20 intel, 3 reference) | **PASS** |
| **Unified Legislative Records** | 66 | 66 (22 Central, 44 State) | **PASS** |
| **Company Exposures (Central + State)**| 104 | 104 | **PASS** |
| **Model Artifact Files Modified** | 0 | 0 | **PASS** |
| **Prediction Files Modified** | 0 | 0 | **PASS** |

### Test Suite Summary
- **Total Tests Executed**: 2,032
- **Passed**: 2,027
- **Skipped**: 3
- **Failed**: 2 (Both are legacy scope tests written prior to Task 8.12.3: `test_production_scope_exclusion_integrity` asserted 50 total companies instead of 70, and `test_all_isins_valid_prefix` asserted that all 70 companies must have an 'INE' prefix, which is intentionally untrue for the 20 unlisted intelligence entities like Swiggy, Flipkart, and KSEB).
- **Alert & Watchlist Pipeline Tests (Tasks 8.13.1 - 8.13.8)**: 100% PASSING.
