# TASK 8.14.9 — LEGISLATIVE MONITORING & DISCOVERY CENTER

## 1. Executive Summary

Task 8.14.9 establishes the production-grade **Legislative Monitoring & Discovery Center** for the India Legislative Intelligence platform. It turns the platform's multi-source legislative scraping, check scheduling, and change detection infrastructure into an authoritative, transparent, and interactive operational discovery center across Central Parliament (Lok Sabha, Rajya Sabha, PRS India) and State Legislative Assemblies (Andhra Pradesh, Karnataka, Kerala, Maharashtra, Telangana, Delhi, Tamil Nadu, etc.).

This implementation is **strictly additive, read-only to existing datasets, and grounded in verifiable telemetry**:
- **Zero model retraining** was performed.
- **Zero predictions or decisions were regenerated or modified**.
- **All frozen baseline datasets remain 100% untouched**:
  - Central: 20 production bills, 47 quantitative securities, 940 pairs, 4,700 predictions, 4,700 decisions, 940 anticipation scores, 14,100 stakeholder reports.
  - State: 44 bills, 44 official PDFs, 44 knowledge records, 88 corporate exposures, strictly **0 stock price predictions**.
  - Platform totals: 64 monitored bills, 5 jurisdictions, 70 corporate entities, permanently 0 state stock predictions.
- **Epistemic Classification**: Every detected change and event is strictly categorized as `[OBSERVED]` (direct scraper report) or `[DERIVED]` (diff computation across versions).
- **Statutory Firewalls Maintained**:
  - State legislative monitoring does not generate stock market predictions (`state_stock_predictions_count == 0`).
  - No synthetic legislative events are fabricated when scrapers return empty results.
  - No political intent, party ranking, or minister scoring is inferred.
  - No Buy/Sell/Hold stock recommendations are generated.

---

## 2. Architecture & Data Flow

```mermaid
flowchart TD
    subgraph Legislative Sources
        LS[Lok Sabha Portal]
        RS[Rajya Sabha Portal]
        PRS[PRS Legislative Research]
        AP[Andhra Pradesh Assembly]
        KA[Karnataka Assembly]
        KL[Kerala Assembly]
        MH[Maharashtra Assembly]
        TS[Telangana Assembly]
    end

    subgraph Monitoring Engine
        SR[MonitoringSourceRegistry<br/>12 configured sources]
        MR[MonitoringRunner<br/>Poller & Scraper Engine]
        SCH[LegislativeScheduler<br/>Async APScheduler]
        REPO[MonitoringRepository<br/>Runs, Events, Versions Storage]
    end

    subgraph REST API Layer [/api/v1]
        EP_OV[GET /monitoring/overview]
        EP_SRC[GET /monitoring/sources & /{source_id}]
        EP_RUN[GET /monitoring/runs & /{run_id}]
        EP_CHG[GET /monitoring/changes & /{event_id}]
        EP_VER[GET /monitoring/bill-versions/{bill_id}]
        EP_SCH[GET /monitoring/scheduler]
        EP_CHK[POST /monitoring/check]
        EP_AI[POST /ai/ask context_type=monitoring]
        EP_COV[GET /coverage]
    end

    subgraph Monitoring Discovery Center UI
        T1[Tab 1: Telemetry Overview Panel]
        T2[Tab 2: Source Registry & Health Badges]
        T3[Tab 3: Check History & Run Inspection]
        T4[Tab 4: Detected Changes Feed]
        T5[Tab 5: Unified Discovery Feed]
        T6[Tab 6: Scheduler Observability]
        T7[Tab 7: Grounded AI Analyst]
    end

    LS --> SR
    RS --> SR
    PRS --> SR
    AP --> SR
    KA --> SR
    KL --> SR
    MH --> SR
    TS --> SR

    SR --> MR
    SCH --> MR
    MR --> REPO

    REPO --> EP_OV
    REPO --> EP_SRC
    REPO --> EP_RUN
    REPO --> EP_CHG
    REPO --> EP_VER
    SCH --> EP_SCH
    MR --> EP_CHK
    REPO --> EP_AI

    EP_OV --> T1
    EP_SRC --> T2
    EP_RUN --> T3
    EP_CHG --> T4
    EP_CHG --> T5
    EP_SCH --> T6
    EP_AI --> T7
```

---

## 3. Backend Implementation

### 3.1 Pydantic Schemas (`api/schemas.py`)
- **`MonitoringOverviewResponse`**: Telemetry summary returning total sources, enabled sources, central vs. state breakdown, implemented vs. planned, run totals, last run status and timestamp, change event totals, scheduler status, and source health breakdown (healthy, errors, never checked).
- **`MonitoringSourceItem`**: Lightweight representation of each source including `source_id`, `source_name`, `jurisdiction`, `state`, `source_type`, `enabled`, `status`, `polling_interval_hours`, `priority`, and last check timestamps.
- **`MonitoringSourceDetailResponse`**: Deep inspection record for an individual source with run history, last error messages, and full provenance metadata.
- **`SchedulerStatusResponse`**: Read-only observability model reporting scheduler enabled state, scheduled running flag, in-progress flag, next run timestamp, and configuration intervals.
- **`ChangeEventDetailResponse`**: Full diff record with `event_id`, `bill_id`, `bill_title`, `jurisdiction`, `state`, `event_type`, `field_name`, `old_value`, `new_value`, `detected_at`, `confidence`, `epistemic_status` (`[OBSERVED]` vs. `[DERIVED]`), and complete provenance strip.
- **`BillVersionHistoryResponse` & `BillVersionItem`**: Chronological snapshot trail of changes to an individual bill.
- **`MonitoringRunResponse` & `MonitoringRunDetailResponse`**: Backward-compatible run responses supporting both legacy `start_time` and modern `started_at`/`completed_at` timestamps.

### 3.2 FastAPI Router (`api/routers/monitoring.py`)
- `GET /api/v1/monitoring/overview`: Aggregates live source registry, repository runs, event counts, and scheduler status into a unified telemetry payload.
- `GET /api/v1/monitoring/sources`: Paginated and filterable by `jurisdiction` (`central` | `state`), `status` (`IMPLEMENTED` | `PLANNED`), and `enabled_only`.
- `GET /api/v1/monitoring/sources/{source_id}`: Single source lookup with 404 handling and execution history.
- `GET /api/v1/monitoring/scheduler`: Read-only endpoint exposing scheduler health and configuration without mutating job queues.
- `GET /api/v1/monitoring/runs`: Polymorphic dual-mode endpoint returning `PaginatedResponse[MonitoringRunDetailResponse]` when `page` is requested, and `list[MonitoringRunResponse]` when unpaginated for backwards compatibility.
- `GET /api/v1/monitoring/runs/{run_id}`: Deep inspection of an individual run with per-source check metrics.
- `GET /api/v1/monitoring/changes`: Server-filtered, paginated feed of all detected legislative diffs with epistemic labeling.
- `GET /api/v1/monitoring/changes/{event_id}`: Detailed diff inspection; returns null for previous values when not recorded rather than inventing historical diffs.
- `GET /api/v1/monitoring/bill-versions/{bill_id}`: Full chronological version history for a given bill.
- `POST /api/v1/monitoring/check`: Safe manual poll trigger executing scrapers across enabled sources.

### 3.3 AI Copilot Grounding (`api/routers/ai.py`)
- Added `context_type="monitoring"` to `POST /api/v1/ai/ask`.
- Injects live telemetry into system prompt context (active sources, enabled count, last run status, event totals).
- Explicit guardrails prevent hallucination of events, dates, companies, or political motives.
- Mandatory legal disclaimer and State prediction isolation notice attached to all responses.

---

## 4. Frontend Implementation

### 4.1 Reusable UI Components (`frontend/components/monitoring/`)
1. **`EpistemicLabel.tsx`**: Renders `[OBSERVED]` (cyan badge for direct source extractions) and `[DERIVED]` (purple badge for diff computations) with tooltip definitions.
2. **`ProvenanceStrip.tsx`**: Displays verification status, retrieval method, source identifier, and timestamp in a clean monospace badge.
3. **`SourceHealthBadge.tsx`**: Renders the 6 canonical health states:
   - `HEALTHY` (emerald pulse)
   - `DEGRADED` (amber warning)
   - `ERROR` (rose error)
   - `NEVER_CHECKED` (slate outline)
   - `DISABLED` (zinc muted)
   - `NOT_IMPLEMENTED` / `PLANNED` (sky blue)
4. **`MonitoringOverviewPanel.tsx`**: High-density telemetry cards with source breakdown, run counter, change counter, scheduler health badge, and quick action trigger.
5. **`SourceRegistryTable.tsx`**: Searchable and filterable registry table with jurisdiction filtering, polling intervals, and drawer triggers.
6. **`SourceDetailDrawer.tsx`**: Slide-over drawer presenting source configuration, execution history, last error diagnostic, and source provenance.
7. **`CheckHistoryTable.tsx`**: Timeline/table of historical scraper runs with duration, bills checked, new bills, changed bills, and error counts.
8. **`ChangesFeed.tsx`**: Live change stream with jurisdiction badges, epistemic labels, field diffs, and deep link to the change drawer.
9. **`ChangeDetailDrawer.tsx`**: Before/after inspection drawer displaying field changes side-by-side with confidence metrics and bill dossier deep links.
10. **`DiscoveryFeed.tsx`**: Unified multi-jurisdiction feed with Central vs State filter chips, economic intelligence badges, and dossiers navigation.
11. **`JurisdictionBanner.tsx`**: Epistemic disclaimer banner explaining Central (quantitative models) vs State (intelligence-only, 0 predictions).
12. **`SchedulerPanel.tsx`**: Read-only scheduler observability monitor showing configured polling intervals, scheduled status, and next scheduled run.
13. **`MonitoringAIAnalyst.tsx`**: Interactive chat analyst with suggested prompt chips ("What changed recently?", "Which state assemblies had activity?"), live streaming, and grounding firewalls.

### 4.2 Application Pages
- **`app/monitoring/page.tsx` & `MonitoringCenterContent.tsx`**: Full 7-tab command center:
  1. *Overview*: Telemetry summary, active sources, quick triggers, jurisdiction notice.
  2. *Sources*: Full source registry with health statuses and detail drawers.
  3. *Check History*: Paginated table of all scraper executions and error logs.
  4. *Detected Changes*: Filterable feed with before/after diffs and epistemic classifications.
  5. *Discovery Feed*: Unified legislative discovery across Central and State bills.
  6. *Scheduler*: Observability dashboard for scheduled background tasks.
  7. *AI Analyst*: Grounded conversational AI assistant for legislative monitoring inquiries.
- **`app/coverage/page.tsx` & `CoverageContent.tsx`**: Data-driven platform coverage page driven by `/api/v1/coverage`, displaying repository-verified statistics and research integrity statements.

---

## 5. Verification & Test Suite

### 5.1 Frontend Tests (Vitest)
```bash
npx vitest run __tests__/pages/monitoring.test.tsx __tests__/pages/coverage.test.tsx
```
- **`__tests__/pages/monitoring.test.tsx` (38 tests)**:
  - Telemetry card rendering & loading skeleton verification.
  - Tab switching across all 7 tabs.
  - Source registry table rendering and jurisdiction filtering.
  - Health badge states (`HEALTHY`, `DEGRADED`, `ERROR`, `NEVER_CHECKED`, `DISABLED`, `PLANNED`).
  - Epistemic label rendering (`[OBSERVED]` vs. `[DERIVED]`).
  - Provenance strip rendering (`source_id`, `detected_at`).
  - Firewall verification (confirms no stock predictions or political recommendations appear).
  - Empty states and error retries.
  - Non-fabrication invariant (empty API payload strictly yields empty feed).
- **`__tests__/pages/coverage.test.tsx` (8 tests)**:
  - Central Parliament metrics (20 bills, 47 companies, 4,700 predictions).
  - State Legislatures metrics (4 implemented states, 44 bills, 0 state stock predictions).
  - Company coverage metrics (70 total, 47 quantitative, 19 intelligence, 4 reference).
  - Unified metrics (64 legislative records, 88 corporate exposures).
  - Research Integrity Statement verification.

### 5.2 Backend Tests (Pytest)
```bash
python -m pytest tests/test_api_endpoints.py tests/test_monitoring_api.py -v
```
- **`tests/test_monitoring_api.py` (13 tests)**:
  - `test_monitoring_overview_endpoint`: Validates telemetry fields and source breakdown.
  - `test_monitoring_sources_list`: Validates pagination and item structure.
  - `test_monitoring_sources_filtering`: Tests Central and State query filtering.
  - `test_monitoring_source_detail_and_not_found`: Verifies detail schema and 404 response.
  - `test_monitoring_scheduler_status`: Verifies scheduler config and status payload.
  - `test_monitoring_runs_pagination`: Validates pagination of historical run records.
  - `test_monitoring_changes_feed`: Tests detected change feed schema.
  - `test_monitoring_change_detail_not_found`: Tests standardized 404 handling.
  - `test_monitoring_bill_version_history`: Tests bill version tracking.
  - `test_monitoring_manual_check`: Tests safe manual polling execution.
  - `test_ai_monitoring_ask`: Tests AI Copilot responses under monitoring context.
  - `test_monitoring_never_generates_stock_predictions`: Verifies no stock buy/sell/prediction advice is generated.
  - `test_state_stock_predictions_firewall_parity`: Confirms state predictions count is permanently 0.
- **`tests/test_api_endpoints.py` (21 tests)**:
  - Validated complete backwards compatibility across all core endpoints with 0 regressions.

---

## 6. Summary of Accomplishments

| Item | Status | Verification |
| :--- | :---: | :--- |
| **Pydantic Schemas** | Completed | Clean imports in `api/schemas.py` |
| **Monitoring Router** | Completed | 10 REST endpoints in `api/routers/monitoring.py` |
| **AI Copilot Grounding** | Completed | `context_type="monitoring"` in `api/routers/ai.py` |
| **Frontend UI Components**| Completed | 13 high-density components in `components/monitoring/` |
| **Monitoring Center Page**| Completed | 7-tab command center in `app/monitoring/` |
| **Data-Driven Coverage** | Completed | Live repository-verified page in `app/coverage/` |
| **Frontend Tests** | Passed | 46/46 tests passing in Vitest |
| **Backend Tests** | Passed | 34/34 tests passing in Pytest |
| **Firewall Integrity** | Enforced | State stock predictions = 0 permanently verified |
