# TASK 1.11A ROUTE AND CAPABILITY AUDIT
**Monitoring, Observability, Freshness, Evidence Navigation & Cross-Route Consistency**

**Date:** October 30, 2026  
**Status:** Canonical Audit Completed  
**Authoritative References:**  
- `docs/SEANCE_DESIGN_SYSTEM.md`  
- `docs/TASK_1_6A_EXPERIENCE_REDESIGN_AUDIT_AND_SPECIFICATION.md`  
- `docs/TASK_1_7A_COMPLETION_REPORT.md`  
- `docs/TASK_1_8A_COMPLETION_REPORT.md`  
- `docs/TASK_1_9A_COMPLETION_REPORT.md`  
- `docs/TASK_1_10A_COMPLETION_REPORT.md`  
- Canonical Frozen Baseline Manifest: `docs/production_baseline.json` (SHA-256: `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`)

---

## 1. Executive Inventory of Audited Routes & Surfaces

| Route | Primary Component | Persona & Core Workflow | Authoritative Data Contracts | Redesign / Consistency Objectives |
|---|---|---|---|---|
| `/monitoring` | `frontend/app/monitoring/MonitoringCenterContent.tsx` | Platform SRE / Compliance Auditor / Legislative Researcher: Real-time telemetry, source registry health, change detection, pipeline execution history, and scheduler observability. | `GET /api/v1/monitoring/overview`<br>`GET /api/v1/monitoring/sources`<br>`GET /api/v1/monitoring/sources/{id}`<br>`GET /api/v1/monitoring/runs`<br>`GET /api/v1/monitoring/changes`<br>`GET /api/v1/monitoring/changes/{id}`<br>`GET /api/v1/monitoring/scheduler`<br>`POST /api/v1/monitoring/check`<br>`GET /api/v1/freshness` | 3-Level Information Architecture (Overview, Detail, Diagnostics). Eliminate emoji tabs. Align with Seance Design System. Integrate genuine dataset freshness telemetry. Sync URL query parameters (`?tab=`, `?source=`, `?change=`) for browser back/forward and deep linking. Correct manual check endpoint. |
| `/coverage` | `frontend/app/coverage/CoverageContent.tsx` | Research Director / Quantitative Lead: Verify platform-wide coverage boundaries (Central vs. State, Modelled vs. Intelligence-only, 0-prediction guarantee). | `GET /api/v1/coverage`<br>`GET /api/v1/freshness` | Institutionalize styling: eliminate card-in-card nesting, replace emojis with clean typographic tokens, link directly to monitoring provenance and canonical dossiers. |
| `/watchlists` & `/watchlists/[id]` | `frontend/app/watchlists/page.tsx`<br>`frontend/app/watchlists/[watchlistId]/page.tsx` | Portfolio Manager / Policy Analyst: Multi-dimensional alert rules and entity monitoring across bills, companies, industries, and sub-national jurisdictions. | `GET/POST /api/v1/watchlists`<br>`GET/PUT/DELETE /api/v1/watchlists/{id}`<br>`GET/POST/DELETE /api/v1/watchlists/{id}/items`<br>`GET/POST/DELETE /api/v1/watchlists/{id}/rules` | Reconcile navigation targets (ensure state assembly items link to canonical `/states/[state]` and bill items link to `/bills/[billId]`), ensure consistent empty and error states, replace raw forms with institutional modals. |
| `/alerts` & `/notifications` | `frontend/app/alerts/page.tsx`<br>`frontend/app/notifications/page.tsx` | Investment Analyst / Compliance Officer: Monitor triggered statutory events, severity escalation, and daily/weekly digests. | `GET /api/v1/alerts`<br>`GET /api/v1/notifications`<br>`GET /api/v1/notifications/digests`<br>`GET /api/v1/notifications/summary` | Standardize badge tokens (`badge-severity-*`, `badge-epistemic-*`), ensure entity links navigate with appropriate tab context, harmonize drawer/inspector interaction. |
| Evidence & Audit Navigation | `AnticipationEvidenceSection.tsx`<br>`DocumentSourcesSection.tsx`<br>`ProvenancePanel.tsx`<br>`DocumentViewer.tsx`<br>`ChangeDetailDrawer.tsx` | Legal Counsel / Research Auditor: End-to-end provenance verification, Gazette PDF inspection, epistemic classification audits, and diff analysis. | Context JSONs (`data/anticipation_evidence/contexts/*`), source registry records, change event provenance payloads | Ensure 100% consistent epistemic tokens (`FACT`, `OBSERVED`, `DERIVED`, `INTERPRETATION`, `PREDICTION`, `EVIDENCE`), eliminate inconsistent color definitions, provide robust empty/partial states when before-state is unavailable without fabricating values. |

---

## 2. Detailed Route & Capability Audit

### 2.1 Legislative Monitoring & Discovery Center (`/monitoring`)

1. **Existing Purpose & Capabilities:**
   - Centralized operational center for legislative change detection across Central Parliament (Lok Sabha / Rajya Sabha) and 4 Sub-National State Assemblies (Andhra Pradesh, Karnataka, Kerala, Telangana).
   - Six functional areas:
     - **Overview Panel**: High-level telemetry of source counts (total, enabled, central, state, implemented, planned), health counts (healthy, errors, never checked), last run summary (status, new bills, changed bills, errors), and scheduler status.
     - **Sources Registry**: Paginated table of all registered data sources, polling intervals, last check/success timestamps, and slide-in drawer (`SourceDetailDrawer`) for individual source inspection.
     - **Check History**: Paginated log of monitoring runs (`MonitoringRunDetail`) showing duration, trigger (`scheduled` / `manual_api`), sources succeeded/failed, and changes detected.
     - **Detected Changes**: Chronological feed of detected delta events (`ChangeEventDetail`) with change types (`NEW_BILL`, `STATUS_CHANGED`, `METADATA_CHANGED`, `DATE_CHANGED`, `DOCUMENT_CHANGED`, `SOURCE_CHANGED`), epistemic status labels, and slide-in drawer (`ChangeDetailDrawer`) displaying BEFORE/AFTER diffs.
     - **Discovery Feed**: Unified intake feed linking directly to Bill Dossiers (`/bills/[billId]`) with State statutory intelligence isolation notice.
     - **Scheduler Observability**: Inspection of background polling thread, next scheduled run, execution interval, and configuration parameters.
     - **AI Analyst**: Grounded conversational assistant answering questions regarding system monitoring.

2. **Authoritative Data Sources & Loading Behavior:**
   - `GET /api/v1/monitoring/overview`: Returns `MonitoringOverview` with genuine counts and last run statistics.
   - `GET /api/v1/monitoring/sources`: Paginated source list filtered by jurisdiction.
   - `GET /api/v1/monitoring/sources/{source_id}`: Detailed source metadata including last error message and raw URL.
   - `GET /api/v1/monitoring/runs`: Paginated run history.
   - `GET /api/v1/monitoring/changes`: Paginated change events filtered by jurisdiction, event type, and source ID.
   - `GET /api/v1/monitoring/changes/{event_id}`: Full change event detail including field name, old value, and new value.
   - `GET /api/v1/monitoring/scheduler`: Scheduler status and configuration.
   - `POST /api/v1/monitoring/check`: Triggers safe manual check across enabled sources.
   - `GET /api/v1/freshness`: High-precision dataset freshness telemetry (LIVE, RECENT, STALE, NOT_AVAILABLE) and provenance summaries.

3. **Links & Cross-Route Connectivity:**
   - Discovery feed links to `/bills/[billId]`.
   - Source detail drawer links to source URLs.
   - Changes feed connects to `/bills/[billId]`.
   - Global navbar pulse indicator links directly to `/monitoring`.

4. **Inconsistencies, Friction Points & Gaps Discovered:**
   - **Tab Navigation & Emojis**: Uses casual emoji icons (`📊`, `🔌`, `🕐`, `🔄`, `📡`, `⏱`, `🤖`) instead of institutional typography and Lucide SVG icons.
   - **Lack of URL Query Parameter Synchronization**: Tab selection and drawer openings (`selectedSourceId`, `selectedEventId`) are stored strictly in local React state. Navigating away or refreshing loses state; browser back/forward button does not navigate between tabs.
   - **Endpoint Contract Bug in Manual Trigger**: `frontend/lib/api/monitoring.ts` calls `POST /api/v1/monitoring/sources/${sourceId}/check`, but the FastAPI backend router (`api/routers/monitoring.py`) actually implements `POST /api/v1/monitoring/check`!
   - **Omission of Freshness Telemetry**: The rich backend dataset freshness engine (`api/routers/freshness.py` with `GET /api/v1/freshness`) is completely unrepresented on the monitoring page.
   - **Hardcoded Colors & Styling**: Several components (`SourceHealthBadge`, `EpistemicLabel`, `ProvenanceStrip`) use hardcoded Tailwind classes (`bg-emerald-500`, `text-blue-400`, `text-purple-400`, `border-slate-600`) rather than semantic CSS tokens (`--color-success`, `--epistemic-*`, `--border-hairline`).
   - **Information Density**: The overview cards stack vertically with repetitive headings and inconsistent borders.

5. **Missing / Misleading States:**
   - When no runs exist or no changes have occurred, the empty state displays casual text without guidance on triggering a manual check.
   - In `ChangeDetailDrawer`, when `previous_version_available` is false, it states "Unavailable" but does not clarify whether this is because the bill is newly introduced (`NEW_BILL`) or because historical snapshotting was disabled.

---

### 2.2 Platform Coverage & Research Integrity (`/coverage`)

1. **Existing Purpose & Capabilities:**
   - Factual transparency report detailing the platform's analytical universe:
     - Central Parliament: 20 canonical bills, 20 modeled, 2024–2025 horizon, 4,700 predictions.
     - State Legislatures: 4 implemented states (AP, KA, KL, TS), 44 state acts, 86 corporate exposures, strictly 0 predictions (enforced by statutory invariant).
     - Corporate Universe: 70 total entities (47 quantitatively modeled, 20 qualitative intelligence-only, 3 reference indices).
     - Unified Statistics: 64 total legislative records, 24 planned expansion states, 100% econometric model integrity.

2. **Authoritative Data Source:**
   - `GET /api/v1/coverage` (`CoverageReportResponse`).
   - `GET /api/v1/freshness` (`FreshnessResponse`).

3. **Links & Cross-Route Connectivity:**
   - Links to `/bills`, `/states`, `/companies`, `/predictions`, and `/overview`.

4. **Inconsistencies & Gaps Discovered:**
   - Visual design features card-in-card containers with emojis (`🏛`, `🗳`, `🏢`, `🌐`, `✓`).
   - Numerical metrics lack tabular formatting (`font-tabular font-mono`).
   - No direct drill-down or linkage to `/monitoring` or `/freshness` provenance records.

---

### 2.3 Custom Watchlists & Workspaces (`/watchlists`, `/watchlists/[id]`, `/workspace`)

1. **Existing Purpose & Capabilities:**
   - User-defined monitoring lists for tracking specific bills, companies, industries, or states.
   - Alert rule binding (e.g. `BILL_STATUS_CHANGE`, `AMENDMENT_DETECTED`, `EVENT_STUDY_CALCULATED`).
   - In `/workspace`, unified personal analyst workbench with 4-tab entity registry, activity feed, and Groq AI Assistant.

2. **Authoritative Data Sources:**
   - `GET/POST /api/v1/watchlists`
   - `GET/PUT/DELETE /api/v1/watchlists/{id}`
   - `GET/POST/DELETE /api/v1/watchlists/{id}/items`
   - `GET/POST/DELETE /api/v1/watchlists/{id}/rules`
   - `GET /api/v1/workspace/attention`
   - `GET /api/v1/workspace/feed`

3. **Cross-Route Linkage Inconsistencies:**
   - In `/watchlists/[id]`, entity links must strictly navigate to:
     - Bill -> `/bills/[billId]`
     - Company -> `/companies/[companyId]`
     - Industry -> `/industry/[industryId]`
     - State -> `/states/[state]` (using canonical state name e.g. `Karnataka`, not lowercase slug that could 404).

---

### 2.4 Alerts & Notifications (`/alerts`, `/notifications`)

1. **Existing Purpose & Capabilities:**
   - Live stream of detected statutory alerts filtered by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), read/unread status, and entity type.
   - Grouped daily/weekly alert digests with delivery status tracking.

2. **Authoritative Data Sources:**
   - `GET /api/v1/alerts`
   - `GET /api/v1/notifications`
   - `GET /api/v1/notifications/digests`
   - `GET /api/v1/notifications/summary`

3. **Inconsistencies & Gaps:**
   - Badge styling uses generic pastel shades instead of the institutional `badge-severity-*` tokens defined in `docs/SEANCE_DESIGN_SYSTEM.md`.
   - Empty states show unstyled text without clear calls to action (e.g. "Create Alert Rule in Watchlists").

---

### 2.5 Evidence Navigation & Audit Trails

1. **Existing Purpose & Capabilities:**
   - Verified audit trails across Pre-Event Information Diffusion (`/anticipation`), Legislative Document Sources (`/bills/[billId]`), Corporate Operational Footprints (`/companies/[companyId]`), and Monitoring Diffs (`/monitoring`).
   - Strict epistemic distinction:
     - `FACT`: Official Gazette notifications, parliamentary bulletin entries, statutory text clauses.
     - `OBSERVED`: BSE/NSE traded returns, trading volumes, recorded timestamps.
     - `DERIVED`: OLS regression residuals, CAR %, beta coefficients, diff detections.
     - `INTERPRETATION`: Grounded AI policy analysis, committee sentiment summaries.
     - `PREDICTION`: Forward-looking econometric event study estimates across the 5 horizons.
     - `EVIDENCE`: Media mentions, press releases, public announcements.

2. **Inconsistencies Discovered:**
   - Multiple divergent epistemic badge implementations: `frontend/components/monitoring/EpistemicLabel.tsx` vs. `frontend/components/ui/EpistemicBadge.tsx`. The former uses inline Tailwind classes and casual emojis; the latter uses canonical semantic CSS classes (`badge-epistemic-*`).
   - Timestamps format inconsistently across surfaces: some use Indian Standard Time (`en-IN`), some ISO UTC, and some relative durations (`3m ago`).
   - When historical snapshots are absent, some drawers display "Unavailable" without context, risking user confusion.

---

## 3. Cross-Route Entity Consistency Matrix

| Entity Dimension | Bill Dossier (`/bills/[id]`) | Predictions (`/predictions`) | Risk (`/risk`) | Anticipation (`/anticipation`) | States (`/states/[id]`) | Monitoring (`/monitoring`) | Required Unification |
|---|---|---|---|---|---|---|---|
| **Central Bill Identity** | `bill_id`, official title, status, introduction date | `bill_id`, `bill_title` | `bill_id`, `bill_title`, sector | `bill_id`, `bill_title` | N/A (State only) | `bill_id`, `bill_title` | Standardize bill title fallback: `bill.title || bill.bill_id` |
| **State Assembly Bill** | `jurisdiction="state"`, `state` name | Strictly 0 predictions (`StatePredictionFirewall`) | Strictly 0 predictions (`StatePredictionFirewall`) | Strictly 0 predictions (`StatePredictionFirewall`) | Listed in Assembly Enactments register | Intakes to live discovery; strictly no predictions | Persistent `StatePredictionFirewall` across all decision-support views |
| **Corporate Identity** | Listed in exposure tables | 47 Modeled securities (ISIN, ticker, name) | 47 Modeled securities | 47 Modeled securities | Listed in Operational Footprint | N/A | Strict isolation: 20 qualitative intelligence-only companies never present in quantitative tables |
| **Event Horizons** | `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]` | Exactly identical 5 horizons | Exactly identical 5 horizons | Exactly identical 5 horizons | N/A | N/A | Canonical 5-horizon array; no ad-hoc windows |
| **Epistemic Classification** | `EpistemicBadge` (`FACT`, `DERIVED`, etc.) | `EpistemicBadge` (`PREDICTION`) | `EpistemicBadge` (`DERIVED`) | `EpistemicBadge` (`EVIDENCE`) | `EpistemicBadge` (`FACT`) | Standardized `EpistemicBadge` | Migrate `EpistemicLabel.tsx` to canonical `EpistemicBadge.tsx` tokens |

---

## 4. Prioritized Engineering Action Plan for Task 1.11A

1. **Phase 2 — Redesign `/monitoring` around 3 Information Levels:**
   - **Level 1 (Operational Overview)**: Executive masthead with telemetry metrics strip (total sources, active, healthy, degraded, never checked, runs, events), actual backend freshness summary, and clear scope statement.
   - **Level 2 (Operational Detail)**: Refined tabbed register with synchronized URL parameters (`?tab=sources|changes|history|freshness|scheduler|ai`):
     - Sources Registry: Refined institutional table with health badges, intervals, and drawer triggers.
     - Detected Changes Feed: Compact scannable cards with canonical epistemic badges and diff triggers.
     - Check History: Run execution log with durations and success/fail counts.
     - Freshness & Pipeline Status: Live integration of `GET /api/v1/freshness` data.
     - Scheduler Panel: Observability metrics and safe manual poll trigger (`POST /api/v1/monitoring/check`).
     - AI Monitoring Analyst: Grounded assistant with prompt chips.
   - **Level 3 (Technical Diagnostics)**: Progressive disclosure in `SourceDetailDrawer` and `ChangeDetailDrawer` with raw JSON inspection toggles, error stack traces, and provenance strips.

2. **Phase 3 & 4 — Polish Shared Observability & Cross-Route Consistency:**
   - Update `frontend/lib/api/monitoring.ts` to implement `triggerCheck(): Promise<MonitoringCheckResponse>` against `POST /api/v1/monitoring/check`.
   - Update `EpistemicLabel.tsx` to utilize `frontend/components/ui/EpistemicBadge.tsx` semantic design tokens.
   - Standardize `SourceHealthBadge.tsx` and `ProvenanceStrip.tsx` to eliminate hardcoded dark tints and inline emoji clutter.
   - Ensure deep link and query-parameter synchronization across all monitoring tabs and drawers.
   - Polish `/coverage` to incorporate institutional table styling and direct freshness links.
   - Validate navigation back/forward coherence across all cross-route entity links.

3. **Phase 5 & 6 — Test Automation & Baseline Verification:**
   - Create `scripts/browser_validation_task_1_11a.js` executing 6 comprehensive browser automation scenarios across viewports and themes.
   - Verify all 8 analytical safeguards and ensure exact SHA-256 match for `docs/production_baseline.json`.
   - Produce `docs/TASK_1_11A_COMPLETION_REPORT.md`.

