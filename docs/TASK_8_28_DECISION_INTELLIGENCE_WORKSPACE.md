# TASK 8.28 — DECISION INTELLIGENCE & PERSONALIZED IMPACT WORKSPACE

## Executive Summary

Task 8.28 establishes the next major product layer on top of the validated legislative intelligence system: a personalized **Decision Intelligence Workspace** connecting:

$$\text{LEGISLATION} \longrightarrow \text{SECTORS / INDUSTRIES} \longrightarrow \text{COMPANY EXPOSURE} \longrightarrow \text{USER PORTFOLIO / WATCHLIST} \longrightarrow \text{EXISTING MODELLED IMPACT} \longrightarrow \text{PERSONALIZED INTELLIGENCE} \longrightarrow \text{ALERTS / REPORTS}$$

The system answers two core user questions:
1. **"Which legislative developments are relevant to me?"**
2. **"Why is this bill relevant to my companies, sectors, or portfolio?"**

The system operates strictly as **decision-support**—never automated investment advice, buy/sell/hold ratings, or price targets. All analytical model baselines remain frozen and unmodified.

---

## 1. Architectural Guardrails & Invariants

| Guardrail / Rule | Implementation & Enforcement | Status |
| :--- | :--- | :--- |
| **No Automated Investment Advice** | All endpoints, reports, alerts, and views return structured governance disclaimers. Zero Buy/Sell/Hold, price targets, or algorithmic trading triggers. | **ENFORCED** |
| **Frozen Quantitative Baseline** | Exactly 20 Central production bills, 47 quantitative companies, 940 pairs, 4,700 predictions, 4,700 decisions, 940 anticipation scores across the 5 authoritative horizons: `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`. SHA-256 of `docs/production_baseline.json` is preserved (`50ae76039bcc...`). | **FROZEN** |
| **Zero State Stock Predictions** | All 44 State bills remain `NOT_ELIGIBLE` with strictly 0 stock predictions (`predictions_count == 0`). | **ENFORCED** |
| **Live Bills Knowledge-Only** | Newly discovered bills ingested via monitoring remain strictly `KNOWLEDGE_ONLY` or `PENDING_REVIEW` with zero stock projections. | **ENFORCED** |
| **Strict Epistemic Separation** | Every personalized datum is tagged with `FACT`, `INTERPRETATION`, or `PREDICTION`. Facts stem from verified gazettes/bills; interpretations from deterministic exposure mappings; predictions from the frozen quantitative baseline. | **ENFORCED** |
| **Multi-Tenant & User Isolation** | Portfolios, holdings, watchlists, alerts, reports, and AI query contexts are isolated by `tenant_id` and `user_id` with strict IDOR protections. | **ENFORCED** |

---

## 2. Core Subsystems & Components

### 2.1 Portfolio Management & Holdings Store
- **Domain Models (`schemas/portfolio.py`)**: `UserPortfolio` and `PortfolioHolding` supporting multi-tenant isolation, company identification (ISIN, ticker, name), industry, sector, weight, notes, and geographic operational presence.
- **Repository (`storage/portfolio_repository.py`)**: JSON-persisted repository with automatic directory initialization, CRUD operations (`create`, `get`, `list`, `update`, `delete`), holding operations (`add_holding`, `update_holding`, `remove_holding`), and CSV/bulk import with duplicate ISIN/name merging.
- **Endpoints (`api/routers/portfolio.py`)**:
  - `POST /api/v1/portfolio`: Create portfolio
  - `GET /api/v1/portfolio`: List portfolios for current user
  - `GET /api/v1/portfolio/{portfolio_id}`: Retrieve specific portfolio
  - `PUT /api/v1/portfolio/{portfolio_id}`: Update portfolio details
  - `DELETE /api/v1/portfolio/{portfolio_id}`: Delete portfolio
  - `POST /api/v1/portfolio/{portfolio_id}/holdings`: Add holding
  - `PUT /api/v1/portfolio/{portfolio_id}/holdings/{holding_id}`: Update holding
  - `DELETE /api/v1/portfolio/{portfolio_id}/holdings/{holding_id}`: Remove holding
  - `POST /api/v1/portfolio/{portfolio_id}/import`: Bulk CSV / JSON import
  - `GET /api/v1/portfolio/exposure`: Aggregated portfolio exposure summary
  - `GET /api/v1/portfolio/{portfolio_id}/report` & `POST`: Personal impact report

### 2.2 Deterministic Relevance Engine (`services/decision_intelligence_service.py`)
Relevance between a legislative record and a user's holding or watchlist entity is evaluated through deterministic, explainable evidence signals:
1. **Direct Company Match / Corporate Exposure (`DIRECT`)**:
   - Company named in official bill metadata or statutory corporate exposure registry (`CompanyExposureRepository` / `StateCorporateExposureRepository`).
   - Covered under 47-company quantitative universe for Central production bills.
2. **Industry Match (`HIGH_RELEVANCE`)**:
   - Holding industry matches regulated business activities or statutory policy domains.
3. **Sector Match (`MODERATE_RELEVANCE`)**:
   - Macro sector governance linkage under the bill's economic sectors.
4. **Geographic / State Jurisdiction Match (`HIGH_RELEVANCE` / `MODERATE_RELEVANCE`)**:
   - For State bills: matches company HQ state, operational state presences, or geographic notes.
5. **Informational Overlap (`INFORMATIONAL`)**:
   - Macro policy and cross-cutting governance developments.

### 2.3 Model Status Firewall & 5 Authoritative Horizons Integration
- **Model Status Classification**:
  - `MODELLED`: Central production bill + 47-quantitative universe holding. Surfaces predictions across the 5 authoritative horizons: `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`.
  - `NOT_ELIGIBLE`: All 44 State bills and unmodelled Central auxiliary items (`service-bill`, `key-issues-and-analysis`). Stock prediction count is strictly 0.
  - `KNOWLEDGE_ONLY`: Live-discovered bills and qualitative enterprises. Stock prediction count is strictly 0.
- **Authoritative Horizons Preserved**:
  - `event_horizons`: `["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"]`
  - Horizon breakdown with predicted direction, excess return, and confidence score.

### 2.4 Personalized Dashboard & Change Feed
- **Workspace Dashboard (`/api/v1/workspace/decision-intelligence`)**:
  - "YOUR LEGISLATIVE INTELLIGENCE" aggregator combining:
    - Relevant new bills
    - Recent bill changes
    - Relevant State legislation
    - Companies exposed
    - Sectors affected
    - Modelled Central bills
    - Knowledge-only developments
    - Upcoming verified legislation
    - Recent document changes
    - High-level portfolio exposure summary
- **Change Feed (`/api/v1/workspace/change-feed`)**:
  - Filtered feed of verified statutory updates and regulatory changes touching user holdings, eliminating polling noise.
- **Explain Relevance (`/api/v1/workspace/explain-relevance?bill_id={bill_id}`)**:
  - Deterministic and grounded explanation answering "Why is this bill relevant to my portfolio?", with graceful fallback for insufficient information.

### 2.5 "MY LEGISLATIVE IMPACT REPORT" Generation
- Generated via `/api/v1/workspace/report` and `/api/v1/portfolio/{id}/report`.
- Structured executive summary, portfolio holdings, legislative exposures, sector breakdown, upcoming verified legislation, and governance disclaimers.

### 2.6 Global Search Integration
- Extended `/api/v1/search` with `scope=portfolio` and `scope=watchlist` query options.
- Displays relevance tier badges, portfolio match tags, and `data_layer="FROZEN_MODEL"` flags.

---

## 3. Frontend Implementation

1. **Portfolio Management UI (`frontend/app/portfolio/page.tsx`)**:
   - Create, edit, and switch portfolios.
   - Add, edit, and delete holdings with ISIN validation, sector, industry, weight, and operational notes.
   - Bulk CSV import dialog with live preview.
   - Exposure analytics panel: direct bills, modelled bills, state bills, and sector breakdown.
2. **Decision Intelligence Workspace UI (`frontend/app/workspace/page.tsx`)**:
   - "YOUR LEGISLATIVE INTELLIGENCE" personalized command center.
   - Filterable impact feed across Central, State, and Live-discovered bills.
   - Epistemic badges (`FACT`, `INTERPRETATION`, `PREDICTION`).
   - Model status firewall badges (`MODELLED`, `KNOWLEDGE ONLY`, `NOT ELIGIBLE`).
   - "Explain Relevance" drawer grounded in holding evidence.
   - One-click "Generate My Legislative Impact Report" with export capabilities.
3. **API Client Layer (`frontend/lib/api/portfolio.ts`, `frontend/lib/api/workspace.ts`)**:
   - Fully typed TypeScript client methods with proper error handling and fallback states.
4. **TypeScript Definitions (`frontend/types/api.ts`)**:
   - `UserPortfolio`, `PortfolioHolding`, `PersonalizedBillImpact`, `PortfolioLegislativeExposure`, `PersonalizedDashboardData`, `PersonalizedImpactReport`.

---

## 4. Test & Verification Matrix

### 4.1 Task 8.28 Test Suite (`tests/test_task_8_28_decision_intelligence.py`)
All 24 test cases pass with 100% compliance:

```
tests/test_task_8_28_decision_intelligence.py::test_01_portfolio_creation_and_schema_validation PASSED [  4%]
tests/test_task_8_28_decision_intelligence.py::test_02_portfolio_tenant_isolation PASSED [  8%]
tests/test_task_8_28_decision_intelligence.py::test_03_user_level_portfolio_isolation PASSED [ 12%]
tests/test_task_8_28_decision_intelligence.py::test_04_portfolio_idor_prevention PASSED [ 16%]
tests/test_task_8_28_decision_intelligence.py::test_05_holdings_crud_and_validation PASSED [ 20%]
tests/test_task_8_28_decision_intelligence.py::test_06_bulk_holdings_import PASSED [ 25%]
tests/test_task_8_28_decision_intelligence.py::test_07_storage_disk_roundtrip PASSED [ 29%]
tests/test_task_8_28_decision_intelligence.py::test_08_deterministic_relevance_direct_company_signal PASSED [ 33%]
tests/test_task_8_28_decision_intelligence.py::test_09_deterministic_relevance_industry_and_sector_signals PASSED [ 37%]
tests/test_task_8_28_decision_intelligence.py::test_10_deterministic_relevance_geography_state_signal PASSED [ 41%]
tests/test_task_8_28_decision_intelligence.py::test_11_relevance_tier_hierarchy PASSED [ 45%]
tests/test_task_8_28_decision_intelligence.py::test_12_model_status_firewall_classification PASSED [ 50%]
tests/test_task_8_28_decision_intelligence.py::test_13_unmodelled_company_firewall PASSED [ 54%]
tests/test_task_8_28_decision_intelligence.py::test_14_central_model_authoritative_predictions_surfacing PASSED [ 58%]
tests/test_task_8_28_decision_intelligence.py::test_15_zero_state_stock_predictions_invariant PASSED [ 62%]
tests/test_task_8_28_decision_intelligence.py::test_16_portfolio_legislative_exposure_summary PASSED [ 66%]
tests/test_task_8_28_decision_intelligence.py::test_17_watchlist_legislative_exposure_aggregation PASSED [ 70%]
tests/test_task_8_28_decision_intelligence.py::test_18_personalized_dashboard_intelligence PASSED [ 75%]
tests/test_task_8_28_decision_intelligence.py::test_19_personalized_change_feed PASSED [ 79%]
tests/test_task_8_28_decision_intelligence.py::test_20_explain_bill_relevance_endpoint PASSED [ 83%]
tests/test_task_8_28_decision_intelligence.py::test_21_explain_relevance_insufficient_information PASSED [ 87%]
tests/test_task_8_28_decision_intelligence.py::test_22_personal_impact_report_generation PASSED [ 91%]
tests/test_task_8_28_decision_intelligence.py::test_23_global_search_portfolio_and_watchlist_scope PASSED [ 95%]
tests/test_task_8_28_decision_intelligence.py::test_24_baseline_invariance_and_firewall_verification PASSED [100%]
======================== 24 passed in 1.78s ========================
```

### 4.2 Comprehensive Regression Suite
| Test Suite | Purpose | Result |
| :--- | :--- | :--- |
| `tests/test_task_8_28_decision_intelligence.py` | Task 8.28 Decision Intelligence Test Suite | **24 / 24 PASS (100%)** |
| `tests/test_task_8_27_dossier.py` | Task 8.27 Bill Dossier 2.0 Test Suite | **20 / 20 PASS (100%)** |
| `tests/test_task_8_26_live_intelligence.py` | Task 8.26 Live Legislative Discovery Suite | **30 / 30 PASS (100%)** |
| `tests/test_security_idor.py` + `tests/test_security_headers_ratelimit.py` + `tests/test_saas_auth_lifecycle.py` | Security, Multi-Tenant & RBAC Suites | **17 / 17 PASS (100%)** |
| `scripts/run_local_saas_smoke_test.py` | 23-Step Critical Path User Journey Smoke Test | **23 / 23 PASS (100%)** |
| Frontend Typecheck (`npm run typecheck`) | TypeScript Strict Compilation Check | **0 errors (PASS)** |
| Frontend Vitest (`npm run test`) | Frontend Component & Page Unit Tests | **22 / 22 files, 205 / 205 PASS** |
| Frontend Build (`npm run build`) | Production Next.js Bundle Compilation | **31 / 31 routes generated (PASS)** |
| Production Baseline Integrity Check | SHA-256 verification of `docs/production_baseline.json` | **`50ae7603...` EXACT MATCH** |
