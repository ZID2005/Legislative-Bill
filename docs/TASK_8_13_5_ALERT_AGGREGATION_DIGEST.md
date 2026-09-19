# TASK 8.13.5 — ALERT AGGREGATION & DIGEST PIPELINE

**Status**: Verified & Complete  
**Regression Suite**: 448 Passed, 0 Failed, 3 Skipped (100% Pass Rate)  
**Frozen Baseline**: Intact (47 Central Companies, 940 Pairs, 4,700 Predictions, 86 State Exposures, 0 State Predictions)

---

## 1. Objective

Task 8.13.5 establishes the Alert Aggregation and Digest Pipeline within the Legislative Intelligence Platform. The purpose is to reduce alert noise and fatigue by clustering related individual `AlertEvent` records produced by Task 8.13.4 into coherent, entity-centered `AlertGroup` records and preparing structured, presentation-ready digests (`REAL_TIME`, `DAILY`, `WEEKLY`).

The pipeline enforces strict separation of responsibilities:
```
Monitoring / Exposure Event
        ↓
Alert Matching Engine (Task 8.13.4)
        ↓
AlertEvent (Immutable Raw Record)
        ↓
Aggregation Engine (Task 8.13.5)
        ↓
AlertGroup (Clustered by Entity & Window)
        ↓
Digest Builder (Task 8.13.5)
        ↓
Notification-Center Ready Structured Data
```

---

## 2. Architecture

```
                                  [AlertEvents Repository]
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │ AlertAggregationService   │
                               │ - Dimension Resolution    │
                               │ - Anchor Window Clustering│
                               │ - Idempotent Indexing     │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                                  [AlertGroup Repository]
                                  storage/alerts/groups/
                                  ├── group_index.json
                                  └── {tenant_id}/{user_id}/
                                      └── group_{group_id}.json
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │ AlertDigestService        │
                               │ - User Preference Filters │
                               │ - Deterministic Ordering  │
                               │ - Structured Summary Prep │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                                  [AlertDigest Records]
                                  storage/alerts/digests/
                                  └── {tenant_id}/{user_id}/
                                      └── digest_{digest_id}.json
```

---

## 3. AlertGroup Model

Defined in [`schemas/alert_group.py`](file:///d:/Legislative-bill/schemas/alert_group.py):

| Field | Type | Description |
|---|---|---|
| `group_id` | `str` | Deterministic group identifier (`grp_{hash[:16]}`). |
| `tenant_id` | `str` | Multi-tenant isolation boundary. |
| `user_id` | `str` | User inbox owner. |
| `watchlist_id` | `Optional[str]` | Watchlist boundary if scoped to a specific watchlist. |
| `group_type` | `AlertGroupType` | Dimension (`BILL`, `COMPANY`, `SECTOR`, `INDUSTRY`, `STATE`, `JURISDICTION`, `WATCHLIST`, `EVENT`). |
| `aggregation_key` | `str` | Deterministic SHA-256 aggregation identity hash. |
| `title` | `str` | Concise human-readable headline. |
| `summary` | `str` | Combined structured summary (FACT \| DERIVED \| INTERPRETATION \| PREDICTION). |
| `alert_count` | `int` | Count of aggregated underlying `AlertEvent`s. |
| `first_event_at` | `str` | Earliest ISO timestamp anchoring the window. |
| `latest_event_at` | `str` | Most recent ISO timestamp in the group. |
| `severity` | `AlertSeverity` | Maximum severity tier across member events. |
| `event_ids` | `list[str]` | Ordered list of member `AlertEvent` IDs. |
| `affected_entity_ids` | `list[str]` | Canonical identifiers of entities impacted. |
| `status` | `AlertGroupStatus` | `ACTIVE` or `ARCHIVED`. |
| `created_at` / `updated_at` | `str` | ISO UTC audit timestamps. |
| `metadata` | `dict[str, Any]` | Provenance, entity attributes, and structured content. |

---

## 4. Aggregation Keys

The deterministic aggregation key prevents unrelated events from merging while ensuring exact idempotency:

```python
aggregation_key = compute_aggregation_key(
    tenant_id=tenant_id,
    user_id=user_id,
    watchlist_id=watchlist_id,
    group_type=group_type,
    entity_type=entity_type,
    entity_id=canonical_entity_id,
    window_id=f"anchor_{first_event_at}",
)
```

The payload is hashed via SHA-256:
$$\text{key} = \text{SHA-256}(T \parallel U \parallel W \parallel G \parallel E_t \parallel E_i \parallel \text{Win})$$

---

## 5. Group Types

The engine supports 8 technical and business grouping dimensions:

1. `BILL`: Central and State bills.
2. `COMPANY`: BSE/NSE listed companies and validated unlisted entities.
3. `SECTOR`: Macro sector classifications.
4. `INDUSTRY`: Granular industry segments.
5. `STATE`: Indian States (e.g. Karnataka, Kerala, Telangana, AP).
6. `JURISDICTION`: Central vs State policy jurisdiction.
7. `WATCHLIST`: Grouping scoped to a user watchlist.
8. `EVENT`: Direct event-level grouping for standalone notifications.

No political or ideological taxonomy is introduced.

---

## 6. Bill-Level Aggregation

Multiple lifecycle events for the same bill (`NEW_BILL`, `BILL_STATUS_CHANGE`, `BILL_DOCUMENT_CHANGE`) are clustered into a single `AlertGroup`:
- **Title**: `[BILL] {bill_title} ({count} updates)`
- **Member References**: Individually preserved in `event_ids`.
- **Underlying Events**: Untouched in `storage/alerts/events/`.

---

## 7. Company-Level Aggregation

Multiple exposure and regulatory updates for a company within the aggregation window form a company group:
- **Title**: `[COMPANY] {ISIN/name} ({count} updates)`
- **Affected Entity IDs**: Contains the company ISIN.
- **Traceability**: Underlying bills and exposures are retained in structured summaries and metadata.

---

## 8. Sector & Industry Aggregation

Aggregates events impacting multiple related entities across an entire sector or industry segment (e.g. `Technology`, `Food Delivery & Quick Commerce`) without flattening individual company exposure links.

---

## 9. State Aggregation

Aggregates State legislative and corporate exposure events:
- **Zero Market Predictions**: State alert summaries enforce `PREDICTION: none`.
- **No Hallucinations**: Factual and derived summaries are strictly grounded in validated sources.

---

## 10. Jurisdiction Aggregation

Supports macro policy tracking at the Central or State jurisdiction level, allowing institutional users to view all Central reforms or all State gazette updates as a cohesive group.

---

## 11. Aggregation Window

- **Setting**: `ALERT_AGGREGATION_WINDOW_HOURS` in `config/settings.py` (Default: `24` hours).
- **Window Model**: Chronological anchor window.
  - The earliest event $E_0$ in a cluster defines the window $[T_0, T_0 + \Delta]$.
  - Any event occurring within $\Delta = 24\text{h}$ joins the group.
  - Events occurring beyond $\Delta$ establish a new anchor window and group.
- **Deterministic Boundary**: Events are sorted by `(created_at, alert_event_id)` prior to clustering, guaranteeing 100% reproducible boundaries.

---

## 12. Idempotency & Deduplication

- Re-processing identical events produces identical group keys and memberships.
- Duplicate event IDs within a group are strictly rejected (`add_event()` returns `False`).
- `group_index.json` provides an $O(1)$ lookup mapping `aggregation_key` to `(group_id, tenant_id, user_id)`.

---

## 13. Event Preservation

`AlertEvent`s are strictly immutable. Aggregation:
- Never deletes or modifies original `AlertEvent` files.
- References `alert_event_id` in `AlertGroup.event_ids`.
- Extracts structured content without altering source records.

---

## 14. Tenant & User Isolation

Multi-tenancy and user isolation are enforced at the repository and service layers:
- Storage path: `storage/alerts/groups/{tenant_id}/{user_id}/group_{group_id}.json`.
- Lookup queries require explicit `tenant_id` and `user_id`.
- Tenant A data is physically partitioned and invisible to Tenant B.
- User A groups are never accessible to User B.

---

## 15. Digest Architecture

Implemented in [`services/alert_digest_service.py`](file:///d:/Legislative-bill/services/alert_digest_service.py):
- Consumes `AlertGroup` and `AlertEvent` records.
- Applies user `AlertPreference` criteria.
- Sorts groups deterministically.
- Serializes presentation-ready data.
- Stores digests in `storage/alerts/digests/{tenant_id}/{user_id}/digest_{digest_id}.json`.

---

## 16. Real-Time Digest

- **Cadence**: `DigestType.REAL_TIME` (`DigestFrequency.REAL_TIME`).
- **Scope**: Immediately eligible alert groups for instant notification dispatch.

---

## 17. Daily Digest

- **Cadence**: `DigestType.DAILY` (`DigestFrequency.DAILY_DIGEST`).
- **Scope**: Gathers active groups over the past 24 hours.

---

## 18. Weekly Digest

- **Cadence**: `DigestType.WEEKLY` (`DigestFrequency.WEEKLY_DIGEST`).
- **Scope**: Gathers active groups over the past 7 days.

---

## 19. Preference Integration

Respects user configurations from `storage/alerts/preferences/`:
- **Master Enabled Switch**: If `enabled=False`, returns an empty, suppressed digest.
- **Severity Threshold**: Filters out any groups below `minimum_severity`.
- **Allowed Alert Types**: Excludes groups whose underlying events do not match permitted types.
- **Delivery Frequency**: Matches user cadence preference.

---

## 20. Empty Digest Behavior

When no qualifying alerts exist:
- Returns a valid, structured `AlertDigest` dataclass instance.
- `group_count = 0`, `event_count = 0`, empty lists.
- **No Fabricated Content**: Never invents fake updates, simulated bills, or placeholder companies.

---

## 21. Performance & Complexity

- **Partitioning**: Events are grouped in-memory by hash key in $O(N \log N)$ time (due to deterministic timestamp sorting).
- **Index Lookup**: Existing groups are resolved in $O(1)$ via `group_index.json`.
- **Storage**: Scoped strictly to `{tenant_id}/{user_id}` directories; never executes unindexed global directory scans.

---

## 22. Tests

All 50 unit and integration tests in `test_alert_aggregation_service.py` and `test_alert_digest_service.py` pass:
- Grouping across 7 dimensions (BILL, COMPANY, SECTOR, INDUSTRY, STATE, JURISDICTION, WATCHLIST).
- Event immutability and provenance tracking.
- Windowing and boundary determinism.
- Deduplication and repeated execution.
- Multi-watchlist separation.
- Cross-user and cross-tenant isolation.
- State alert aggregation with 0 predictions.
- Central alert aggregation preserving existing predictions.
- Intelligence company aggregation with 0 financial forecasts.
- Real-time, daily, weekly, and empty digest construction.
- Preference threshold and allowed type filtering.
- Repository reload and persistence.
- Critical frozen baseline verification.

---

## 23. Baseline Integrity

| Metric | Target | Actual | Status |
|---|---|---|---|
| `CENTRAL_QUANTITATIVE_COMPANIES` | 47 | 47 | Invariant Maintained |
| `CENTRAL_BILL_COMPANY_PAIRS` | 940 | 940 | Invariant Maintained |
| `CENTRAL_PREDICTIONS` | 4,700 | 4,700 | Invariant Maintained |
| `STATE_EXPOSURES` | 86 | 86 | Invariant Maintained |
| `STATE_PREDICTIONS` | 0 | 0 | Invariant Maintained |
| `CENTRAL_BASELINE_CHANGED` | false | false | Invariant Maintained |

---

## 24. Non-Goals Respected

- **No external delivery**: No email, SMS, push, or webhooks.
- **No UI/Frontend**: No React/Next.js components.
- **No AI synthesis**: Digest summaries are ground-truth deterministic aggregations without Groq generation.
- **No ML generation**: 0 models retrained; 0 new predictions generated.
- **No political scoring**: Grouping and sorting are strictly technical and factual.

---

## 25. Recommended Task 8.13.6

**Task 8.13.6 — Notification Dispatch & In-App Notification Center API**:
- Implement in-app notification state management (delivery status, read/unread markers, archiving).
- Build the REST/FastAPI endpoints for notification center polling and digest retrieval.
- Prepare extensible dispatch adapters (in-app store, with pluggable email/webhook hooks for subsequent operationalization).
