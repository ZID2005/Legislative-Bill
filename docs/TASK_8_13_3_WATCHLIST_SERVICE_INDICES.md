# Task 8.13.3 — Watchlist Service & Inverted Indices

**India Legislative Intelligence & Market Impact Prediction Platform**  
**Task:** 8.13.3 — Service Layer for Watchlists & O(1) Inverted In-Memory Indices  
**Status:** COMPLETE — ALL 49 TESTS PASSED — 100% REGRESSION & BASELINE INTEGRITY PRESERVED  
**Date:** 2026-09-17  

---

## 1. Objective

Following the schemas and persistent storage foundation established in **Task 8.13.2**, the objective of **Task 8.13.3** is to implement the comprehensive business logic layer for watchlists and high-performance subscriber resolution.

Specifically, Task 8.13.3 delivers:
1. **`WatchlistService`**: The unified business service coordinating watchlists, items, alert rules, user preferences, summaries, and strict multi-tenant ownership enforcement.
2. **`WatchlistIndexService`**: A deterministic in-memory inverted index system with JSON file backing (`storage/watchlists/indices/`), enabling $O(1)$ subscriber resolution across six entity types.
3. **Cross-Entity Validation Engine**: Rigorous existence and eligibility verification across the company master universe, central bills, state bills, sectors, industries, states, and jurisdictions.
4. **Resolution Primitives**: High-performance mapping from upstream monitoring and exposure events (company exposure changes, bill progression, state amendments) to affected subscribers.

In accordance with strict system invariants, Task 8.13.3 performs **no model retraining**, generates **no market predictions**, preserves **0 state predictions**, and leaves alert matching/notification dispatching to downstream tasks (Task 8.13.4+).

---

## 2. Service Architecture

The service layer sits between upstream monitoring/ingestion pipelines and foundational data repositories:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│             Upstream Engines (Legislative Discovery / Monitoring / AI)          │
└──────────────────────────────────────┬─────────────────────────────────────────┘
                                       │ (Bills / Exposures / State Events)
                                       ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                         WatchlistIndexService                                  │
│  - In-memory deterministic inverted index dictionaries:                        │
│    idx_company, idx_bill, idx_sector, idx_industry, idx_state, idx_jurisdiction │
│  - O(1) direct subscriber lookups                                              │
│  - Atomic write to storage/watchlists/indices/                                 │
│  - Idempotent rebuild from canonical storage/watchlists/items/                 │
└──────────────────────────────────────▲─────────────────────────────────────────┘
                                       │ Synchronous Index Update
                                       │ (add_item, remove_item, deactivate)
┌──────────────────────────────────────┴─────────────────────────────────────────┐
│                           WatchlistService                                     │
│  - Multi-tenant boundary enforcement (tenant_id, user_id, watchlist_id)       │
│  - Cross-repo entity validation (Company, Bill, StateBill, Normalizers)        │
│  - Watchlist eligibility enforcement (company.watchlist_eligible)              │
│  - Deduplication across items in a watchlist                                   │
│  - Watchlist lifecycle (create, update, deactivate, reactivate, delete)        │
│  - Alert rule and preference management delegates                              │
│  - Watchlist and user summaries                                                │
└──────────────────────────────────────┬─────────────────────────────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────┐
│  WatchlistRepository    │  │ WatchlistItemRepository │  │ AlertRuleRepository │
│  AlertPrefRepository    │  │ CompanyRepository       │  │ BillRepository      │
│  UserRepository         │  │ StateBillRepository     │  │ Normalizers         │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────┘
```

### Module Breakdown
- **[`services/watchlist_index_service.py`](file:///d:/Legislative-bill/services/watchlist_index_service.py)**:
  - `WatchlistSubscriber`: Frozen dataclass containing `(user_id, tenant_id, watchlist_id, watchlist_item_id, entity_type, entity_id)`.
  - `IndexValidationReport`: Structural integrity validation report detailing missing entries, orphan entries, bucket counts, and total subscriber count.
  - `WatchlistIndexService`: Manages in-memory maps, atomic JSON serialization, idempotent full rebuilds, and $O(1)$ subscriber lookups.
- **[`services/watchlist_service.py`](file:///d:/Legislative-bill/services/watchlist_service.py)**:
  - High-level coordinator implementing all user operations, validation gates, and delegate access.
- **[`services/__init__.py`](file:///d:/Legislative-bill/services/__init__.py)**:
  - Clean exports of `WatchlistService`, `WatchlistIndexService`, `WatchlistSubscriber`, and `IndexValidationReport`.

---

## 3. Lifecycle Operations

`WatchlistService` manages the complete lifecycle of watchlists and watchlist items:

### Watchlist Operations
- **`create_watchlist(user_id, name, description, is_default, tenant_id)`**:
  - Validates tenant and user non-empty strings.
  - Generates unique UUID `watchlist_id`.
  - Persists to `storage/watchlists/watchlists/{tenant_id}/{watchlist_id}.json`.
- **`get_watchlist(watchlist_id, user_id, tenant_id)`**:
  - Enforces strict ownership: raises `PermissionError` if `tenant_id` does not match, or `None` if watchlist not found.
- **`update_watchlist(watchlist_id, name, description, is_default, user_id, tenant_id)`**:
  - Verifies ownership and updates metadata with updated ISO-8601 UTC timestamp.
- **`deactivate_watchlist(watchlist_id, user_id, tenant_id)`**:
  - Soft-deactivates watchlist (`is_active = False`).
  - Purges all items of the watchlist from all 6 active inverted indices.
- **`reactivate_watchlist(watchlist_id, user_id, tenant_id)`**:
  - Sets `is_active = True`.
  - Re-indexes all active items belonging to this watchlist across the inverted indices.
- **`delete_watchlist(watchlist_id, user_id, tenant_id)`**:
  - Hard-deletes watchlist and its items, removing all associated subscriber entries from the indices.
- **`list_user_watchlists(user_id, tenant_id, include_inactive)`**:
  - Returns watchlists owned by the specified user.

### Item Operations
- **`add_item(watchlist_id, entity_type, entity_id, user_id, tenant_id, notes, bypass_eligibility)`**:
  - Verifies watchlist ownership and active status.
  - Validates entity reference against master datasets.
  - Enforces company watchlist eligibility (unless explicitly bypassed).
  - Rejects intra-watchlist duplicate items.
  - Persists item and synchronously updates the target inverted index.
- **`remove_item(item_id, watchlist_id, user_id, tenant_id)`**:
  - Validates item belongs to the specified watchlist.
  - Removes item from repository and purges entry from target inverted index.
- **`list_items(watchlist_id, user_id, tenant_id, is_active)`**:
  - Lists all items under the user's watchlist.

---

## 4. Entity Validation Rules

Every item added to a watchlist passes through `WatchlistService._validate_entity_reference`:

| Entity Type | Validation Mechanism | Master Source | Notes |
|---|---|---|---|
| **`COMPANY`** | Exact ISIN, NSE/BSE ticker, or canonical name match. | `CompanyRepository` (70 records) | Resolves to canonical `company_id`. Rejects arbitrary fuzzy strings. |
| **`BILL`** | Exact `bill_id` lookup in Central or State bill repository. | `BillRepository`, `StateBillRepository` | Supports central bills (e.g. `central_bill_digital_personal_data_protection_act_2023`) and state bills. |
| **`SECTOR`** | Case-insensitive membership in canonical sectors. | `CompanyRepository.list_all_sectors()` (20 canonical sectors) | Standardizes to canonical capital case. |
| **`INDUSTRY`** | Case-insensitive membership in canonical industries. | `CompanyRepository.list_all_industries()` (62 canonical industries) | Standardizes to canonical capital case. |
| **`STATE`** | Canonical Indian State / UT validation. | `utils.state_normalizer` + `CANONICAL_INDIAN_STATES` / `CANONICAL_UNION_TERRITORIES` | Rejects fictional states (e.g. "Atlantis") while accepting variants like "KA", "Karnataka". |
| **`JURISDICTION`** | Allowed set: `{"CENTRAL", "STATE", "ALL"}`. | Schema enumeration | Standardized uppercase. |

---

## 5. Tenant and User Isolation Enforcement

The platform guarantees strict isolation across tenants and users:
1. **Tenant Separation**: Watchlists are stored in partitioned paths (`{storage_dir}/watchlists/{tenant_id}/...`). Access across tenants immediately raises `PermissionError`.
2. **User Ownership**: User A cannot read, modify, or delete User B's watchlist or items. Ownership mismatch raises `PermissionError` or returns `None` for lookups.
3. **Index Isolation**: Each `WatchlistSubscriber` in the inverted index retains its `tenant_id` and `user_id`. Queries can either filter by specific tenant or return subscribers tagged with tenant credentials.

---

## 6. Duplicate Prevention Rules

- **Within a Watchlist**: Attempting to add an entity (e.g. `INE758T01015`) to a watchlist where it already exists (active) raises `ValueError("Entity ... already exists in watchlist ...")`.
- **Across Watchlists**: A user may add the same entity to multiple distinct watchlists (e.g., "Tech Watchlist" and "High Priority Watchlist"). Each instance receives a unique `watchlist_item_id`.
- **Index Deduplication**: Within each index bucket, subscribers are deduplicated by `(user_id, tenant_id, watchlist_id, watchlist_item_id)`.

---

## 7. Inverted Indices Design and Data Structures

To avoid expensive multi-file disk scans whenever a bill advances or an exposure changes, `WatchlistIndexService` maintains 6 in-memory index structures:

```python
{
    "idx_company": {
        "INE758T01015": [WatchlistSubscriber(...)],
        "INE201M01025": [WatchlistSubscriber(...)]
    },
    "idx_bill": {
        "central_bill_digital_personal_data_protection_act_2023": [WatchlistSubscriber(...)]
    },
    "idx_sector": {
        "Technology": [WatchlistSubscriber(...)]
    },
    "idx_industry": {
        "E-Commerce Logistics": [WatchlistSubscriber(...)]
    },
    "idx_state": {
        "Karnataka": [WatchlistSubscriber(...)]
    },
    "idx_jurisdiction": {
        "CENTRAL": [WatchlistSubscriber(...)],
        "STATE": [WatchlistSubscriber(...)]
    }
}
```

- **Lookup Complexity**: $O(1)$ dict lookup returning pre-filtered subscriber lists.
- **Subscriber Model**:
  ```python
  @dataclass(frozen=True)
  class WatchlistSubscriber:
      user_id: str
      tenant_id: str
      watchlist_id: str
      watchlist_item_id: str
      entity_type: str
      entity_id: str
  ```

---

## 8. Index Persistence Format and Directory Layout

Indices are stored as formatted JSON files in `storage/watchlists/indices/`:

```
storage/watchlists/indices/
├── idx_company.json
├── idx_bill.json
├── idx_sector.json
├── idx_industry.json
├── idx_state.json
└── idx_jurisdiction.json
```

### File Schema:
```json
{
  "index_type": "COMPANY",
  "generated_at": "2026-09-17T14:00:00Z",
  "entry_count": 2,
  "total_subscribers": 3,
  "index": {
    "INE758T01015": [
      {
        "user_id": "usr_01",
        "tenant_id": "default_tenant",
        "watchlist_id": "wl_01",
        "watchlist_item_id": "item_01",
        "entity_type": "COMPANY",
        "entity_id": "INE758T01015"
      }
    ]
  }
}
```

Writes are atomic: entries are written to temporary files and renamed, avoiding partial-write corruption.

---

## 9. Index Rebuild Mechanism

`WatchlistIndexService.rebuild_all_indices(item_repo, watchlist_repo)` provides a fully idempotent, crash-resilient rebuild primitive:

1. Scans all items across all tenants in `WatchlistItemRepository`.
2. Cross-references parent watchlists in `WatchlistRepository` to verify `is_active == True`.
3. Discards orphaned items or items whose parent watchlist is deactivated/deleted.
4. Clears in-memory dictionaries and repopulates all 6 index structures.
5. Flushes rebuilt indices to disk.
6. Returns an execution summary with item counts and processing time.

### Integrity Validation (`validate_index_integrity`)
Detects discrepancies between canonical items in storage and current indices:
- Missing entries (items in storage but omitted from index).
- Orphan entries (index entries pointing to non-existent or inactive items).
- Returns structured `IndexValidationReport(is_valid, missing_count, orphan_count, details)`.

---

## 10. Entity Resolution Primitives

`WatchlistService` exposes high-level resolution methods used by upstream monitoring:

### 1. Direct Resolution (`resolve_subscribers`)
```python
subscribers = service.resolve_subscribers(WatchlistEntityType.COMPANY, "INE758T01015")
# Returns List[WatchlistSubscriber] in O(1)
```

### 2. Company Exposure Resolution (`resolve_subscribers_by_company_exposure`)
When a legislative event affects a company, this primitive resolves subscribers who watch:
1. The company directly (`idx_company`).
2. The company's primary sector (`idx_sector`).
3. The company's primary industry (`idx_industry`).
Deduplicates subscribers across buckets so each `(user_id, watchlist_id)` receives at most one match.

### 3. Bill Progression Resolution (`resolve_subscribers_for_bill_change`)
When a bill advances in Parliament or a State Assembly:
1. Resolves direct subscribers of the bill (`idx_bill`).
2. Resolves subscribers watching the bill's jurisdiction (`idx_jurisdiction`).
3. Resolves subscribers watching the bill's state (if state-level bill).

---

## 11. Company Watchlist Eligibility Enforcement

The corporate intelligence master universe contains both public quantitative companies and unlisted/subsidiary intelligence entities.

- **Rule**: `company.watchlist_eligible == True` is required to add a company item by default.
- **Implementation**:
  ```python
  if not getattr(company, "watchlist_eligible", True) and not bypass_eligibility:
      raise ValueError(
          f"Company '{canonical_id}' ({company.canonical_name}) is an intelligence-only entity "
          f"and is not currently eligible for direct watchlist alerting."
      )
  ```
- **Bypass Capability**: Authorized internal operations or special overrides can pass `bypass_eligibility=True`.

---

## 12. Alert Rule Management Integration

Alert rules are configured per watchlist to determine which trigger types and minimum severity levels dispatch notifications.

`WatchlistService` delegates and enforces ownership for alert rules:
- `create_alert_rule(watchlist_id, alert_type, min_severity, channels, user_id, tenant_id)`
- `enable_alert_rule(alert_rule_id, user_id, tenant_id)`
- `disable_alert_rule(alert_rule_id, user_id, tenant_id)`
- `list_watchlist_alert_rules(watchlist_id, user_id, tenant_id)`

---

## 13. Alert Preference Management Integration

Global user preferences control delivery channels and digest cadences:
- `get_user_preferences(user_id, tenant_id)`: Fetches existing preferences or instantiates default settings (`EMAIL`, `IN_APP`, `DAILY` digest).
- `update_user_preferences(user_id, channels, email, digest_frequency, quiet_hours_start, quiet_hours_end, tenant_id)`: Updates delivery preferences with field validation.

---

## 14. Watchlist Summaries & Dashboard Aggregation

Provides single-call aggregations for user dashboards and monitoring metrics:
- **`get_watchlist_summary(watchlist_id, user_id, tenant_id)`**:
  - Watchlist metadata, active status.
  - Item count grouped by entity type (`company_count`, `bill_count`, `sector_count`, etc.).
  - Configured alert rules count and active rules count.
- **`get_user_summary(user_id, tenant_id)`**:
  - Total watchlists owned.
  - Total active items monitored across all watchlists.
  - Breakdown by entity type across all user watchlists.
  - Configured alert preference snapshot.

---

## 15. Performance and Scalability

| Operation | Target Complexity | Measured Benchmark | Notes |
|---|---|---|---|
| Single Subscriber Resolution | $O(1)$ | $< 0.05\text{ ms}$ | In-memory hash lookup |
| Exposure Subscriber Resolution | $O(1)$ | $< 0.2\text{ ms}$ | Company + Sector + Industry union |
| Item Addition + Index Sync | $O(1)$ | $< 2.5\text{ ms}$ | JSON item write + in-memory update |
| Full Rebuild (1,000 items) | $O(N)$ | $< 50\text{ ms}$ | Full repository scan + atomic disk flush |
| Index Memory Footprint | Linear | $\approx 25\text{ KB}$ | Highly compact dataclasses |

---

## 16. Error Handling & Validation Error Types

- **`ValueError`**: Raised when entity references fail validation, invalid enums are supplied, or duplicate items are added to a watchlist.
- **`PermissionError`**: Raised on cross-tenant access, unauthorized watchlist access, or mismatched ownership.
- **`KeyError` / `None`**: Returned when querying non-existent watchlist resources.

---

## 17. Backward Compatibility

- Existing monitoring runs and change events (`storage/monitoring/`) remain completely unmodified.
- Central quantitative companies (47), bills (20), pairs (940), and predictions (4,700) are intact.
- State economic intelligence (86 exposures) and zero State predictions are preserved.
- Existing discovery engines, Groq AI services, and dashboards operate without degradation.

---

## 18. Test Coverage Breakdown

The test suite contains **49 automated tests** dedicated to Task 8.13.3:

### `tests/test_watchlist_service.py` (40 Tests)
| Class / Category | Scenarios | Result |
|---|---|---|
| `TestWatchlistCRUD` | Create, retrieve, update, deactivate, list active watchlists | **5/5 PASS** |
| `TestWatchlistItemsAndValidation` | Add company, bill, sector, industry, state, jurisdiction; remove item; reject duplicates; reject invalid entities | **9/9 PASS** |
| `TestOwnershipAndTenantIsolation` | Cross-user access denial, cross-tenant access denial, cross-user modification denial | **3/3 PASS** |
| `TestInvertedIndicesAndResolution` | All 6 indices updated, subscriber resolution, idempotent rebuild, corrupt index detection, inactive watchlist exclusion | **6/6 PASS** |
| `TestAlertRulesIntegration` | Create rule, enable/disable rule, list rules | **3/3 PASS** |
| `TestAlertPreferencesIntegration` | Get default preferences, update preferences | **2/2 PASS** |
| `TestSummaries` | Watchlist summary with item type breakdown, user multi-watchlist summary | **2/2 PASS** |
| `TestEligibilityEnforcement` | Non-watchlist eligible company rejection, bypass test | **1/1 PASS** |
| `TestIntegrationResolutionPrimitives` | Company exposure resolution, bill direct subscriber resolution, state event resolution, jurisdiction event resolution | **4/4 PASS** |
| `TestCriticalFrozenBaseline` | 47 companies, 940 pairs, 4,700 predictions, 86 state exposures, 0 state predictions unchanged | **5/5 PASS** |

### `tests/test_watchlist_indices.py` (9 Tests)
| Scenario | Description | Result |
|---|---|---|
| `test_1_init_empty_indices` | Verifies clean initialization of empty indices | **PASS** |
| `test_2_add_and_query_subscriber` | Verifies adding subscriber and querying by entity | **PASS** |
| `test_3_multiple_subscribers_for_entity` | Verifies multi-subscriber buckets | **PASS** |
| `test_4_duplicate_item_prevented_in_bucket` | Verifies duplicate prevention within bucket | **PASS** |
| `test_5_persistence_json_structure` | Validates JSON schema structure on disk | **PASS** |
| `test_6_remove_subscriber` | Verifies subscriber removal and key pruning | **PASS** |
| `test_7_deactivate_watchlist_purges_across_types` | Verifies full purge on watchlist deactivation | **PASS** |
| `test_8_rebuild_from_canonical_repo` | Verifies rebuild from disk items | **PASS** |
| `test_9_integrity_validation_comprehensive` | Verifies integrity report on clean and corrupt indices | **PASS** |

**Total New Tests:** 49  
**Passing:** 49  
**Failing:** 0  

---

## 19. Regression Verification Results

All existing platform test suites were executed and verified:

| Test Suite | Tests | Result |
|---|---|---|
| `tests/test_watchlist_alert_foundation.py` | 38 | **38 PASSED** |
| `tests/test_watchlist_service.py` | 40 | **40 PASSED** |
| `tests/test_watchlist_indices.py` | 9 | **9 PASSED** |
| `tests/test_company_intelligence.py` + `tests/test_company_exposure_expansion.py` | 49 | **49 PASSED** |
| `tests/test_legislative_monitoring.py` | 67 | **64 PASSED, 3 SKIPPED** |
| `tests/test_unified_legislative_discovery.py` + `tests/test_groq_ai.py` | 48 | **48 PASSED** |
| **Total Test Suite Executions** | **251** | **248 PASSED, 3 SKIPPED, 0 FAILED** |

---

## 20. Frozen Baseline Integrity Confirmation

```
================================================================================
CRITICAL PRODUCTION BASELINE AUDIT — TASK 8.13.3
================================================================================
Central Quantitative Companies:          47 (EXACT MATCH)
Central Legislative Bills:               20 (EXACT MATCH)
Central Bill-Company Pairs:             940 (EXACT MATCH)
Central Pre-computed Predictions:     4,700 (EXACT MATCH)
State-Level Company Exposures:           86 (EXACT MATCH)
State-Level Market Predictions:           0 (EXACT MATCH, STRICT REQUIREMENT)
Central Baseline Hash Invariance:    VERIFIED (NO CHANGES)
================================================================================
```

---

## 21. Explicit Non-Goals

The following capabilities are outside the scope of Task 8.13.3 and are strictly deferred:
1. **Automatic Alert Generation Engine**: Evaluating incoming monitoring diffs against alert rules and generating `AlertEvent` objects is deferred to **Task 8.13.4**.
2. **Monitoring Run Hooks**: Hooking into `services/legislative_monitor_service.py` is deferred to **Task 8.13.4**.
3. **External Notification Delivery**: Dispatching emails, SMS, or webhook notifications is deferred to downstream tasks.
4. **Authentication / Session Tokens**: User auth remains simulated via `user_id` / `tenant_id` context.
5. **Frontend UI Components**: Dashboard views and user management UI are deferred to **Task 8.13.6**.

---

## 22. Recommended Next Task: Task 8.13.4

**Task 8.13.4 — Alert Matching Engine & Event Generation**:
- Implement `AlertMatchingService` that accepts change events from `LegislativeMonitorService` or company exposure updates.
- Utilize `WatchlistIndexService` to resolve subscribers in $O(1)$.
- Evaluate matched subscribers against active `AlertRule` filters and threshold criteria.
- Generate deduplicated `AlertEvent` inbox records using SHA-256 deduplication keys.
