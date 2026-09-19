# Task 8.13.4 — Alert Matching Engine & Event Generation

## 1. Objective
The objective of Task 8.13.4 is to connect live legislative monitoring updates, statutory bill events, and validated corporate exposure intelligence to user watchlists. This layer accepts incoming events, normalizes them into a canonical contract, resolves affected entities and their subscribers via deterministic inverted indices, evaluates user alert rules and preferences, and generates persisted, deduplicated in-app `AlertEvent` records.

In strict compliance with architectural boundaries, Task 8.13.4 does **not** implement notification delivery (emails, push notifications, webhooks) and maintains the project's frozen production baseline intact.

---

## 2. Architecture
The alert matching and event generation pipeline is structured as follows:

```
Monitoring / Exposure Event
          ↓
  Event Normalization (ChangeEvent / StateCorporateExposure / Dict)
          ↓
  Affected Entity Resolution (Direct dimensions + Validated Exposure links)
          ↓
  WatchlistIndexService (O(1) Inverted Index Resolution across 6 dimensions)
          ↓
  Subscriber Resolution & Multi-Dimension Candidate Grouping
          ↓
  AlertRule Evaluation (User/Watchlist scope, AlertType, Severity Threshold)
          ↓
  AlertEvent Generation (Structured FACT / DERIVED / INTERPRETATION / PREDICTION)
          ↓
  Deduplication & Idempotent Persistence (AlertEventRepository + dedup_index)
```

### Components
- **`services/alert_matching_service.py`**: The core matching engine coordinating normalization, entity expansion, subscriber lookup, rule evaluation, and event persistence.
- **`services/watchlist_index_service.py`**: The O(1) in-memory and JSON-backed inverted index service from Task 8.13.3 (`idx_company`, `idx_bill`, `idx_sector`, `idx_industry`, `idx_state`, `idx_jurisdiction`).
- **`storage/alert_event_repository.py`**: In-app inbox persistence engine storing `AlertEvent` records partitioned by `{tenant_id}/{user_id}/event_{alert_event_id}.json` with a global `dedup_index.json`.
- **`storage/alert_rule_repository.py`**: User and watchlist alert rule store with enabled/disabled state, alert types, and severity thresholds.
- **`storage/alert_preference_repository.py`**: Master user controls for alert enablement, global minimum severity, and permitted alert types.
- **`storage/company_exposure_repository.py`**: Ground truth for verified corporate exposures linking bills to companies.

---

## 3. Event Normalization
The normalization layer (`NormalizedEvent`) provides a uniform, deterministic interface across disparate ingestion sources:
- **`normalize_monitoring_event()`**: Ingests `ChangeEvent` and `NotificationEvent` records from the legislative monitoring scheduler. Converts `ChangeEventType` (`NEW_BILL`, `STATUS_CHANGED`, `DOCUMENT_CHANGED`, etc.) to canonical `AlertType` (`NEW_BILL`, `BILL_STATUS_CHANGE`, `BILL_DOCUMENT_CHANGE`, `BILL_VERSION_CHANGE`, `LEGISLATIVE_MONITORING_CHANGE`).
- **`normalize_exposure_event()`**: Ingests `StateCorporateExposure` records, creating `AlertType.NEW_COMPANY_EXPOSURE` or `AlertType.EXPOSURE_CHANGE` with verified company, bill, sector, and evidence references.
- **`normalize_legislative_event()` & `normalize_event()`**: Polymorphic dispatchers handling dictionary payloads and unified discovery records safely.

All normalizers preserve original event identifiers, timestamps, source identifiers, and references without fabricating missing information.

---

## 4. Monitoring Integration
Legislative monitoring events produced by `services/monitoring/` (or stored in `storage/monitoring/change_events/`) can be seamlessly routed to:
```python
alert_events = alert_matching_service.process_monitoring_event(change_event)
```
The integration requires zero changes to the monitoring engine, scheduler cadence, or adapter scrapers.

---

## 5. Exposure Integration
Corporate exposure records produced by `CompanyExposureRepository` can be processed directly:
```python
alert_events = alert_matching_service.process_company_exposure_event(exposure)
```
The matching service queries `CompanyExposureRepository` as read-only canonical evidence. It does not re-generate or modify existing State or Central corporate exposures.

---

## 6. Entity Resolution
When an event is received, the matching engine extracts all directly affected dimensions:
- Direct: `company_id`, `bill_id`, `sector_id`, `industry_id`, `state_id`, `jurisdiction`.
- Linked Exposure Dimensions: For bill events, the engine queries `CompanyExposureRepository` to identify validated exposed companies (e.g. Swiggy exposed to `telangana-vs-bill-11-2024`, Adani Ports exposed to `the-coastal-shipping-bill-2024`) and adds them to the candidate search keys.
- Linked Bill Taxonomy: Queries `BillRepository` or `StateBillRepository` to retrieve verified sectors and state affiliations.

No exposures or entity relationships are ever inferred or fabricated.

---

## 7. Inverted Index Usage
Instead of performing an $O(\text{users} \times \text{watchlists} \times \text{items})$ scan, the matching service performs direct $O(1)$ lookups into `WatchlistIndexService`:
- `company_id` $\to$ `idx_company`
- `bill_id` $\to$ `idx_bill`
- `sector_id` $\to$ `idx_sector`
- `industry_id` $\to$ `idx_industry`
- `state_id` $\to$ `idx_state`
- `jurisdiction` $\to$ `idx_jurisdiction`

This bounds total execution time to $O(\text{matched subscribers} + \text{rule evaluations})$.

---

## 8. Multi-Dimensional Matching
A single event may simultaneously match multiple dimensions watched by the same user.
For example, a user watching:
- The Bill: `the-kerala-platform-based-gig-workers-bill-2024`
- The State: `Kerala`
- The Company: `PRIV-BUNDL-SWIGGY`

The engine resolves subscribers across all three dimensions, groups them by `(tenant_id, user_id, watchlist_id)`, deduplicates candidate entries, and records all matched dimensions in the `AlertEvent.metadata["matched_dimensions"]`. Exactly **one** `AlertEvent` is generated for this watchlist subscription rather than three separate alerts.

---

## 9. Alert Rule Evaluation
Subscriber candidates are evaluated against `AlertRuleRepository` and `AlertPreferenceRepository`:
1. **Watchlist Active Check**: Inactive or deleted watchlists are suppressed.
2. **User Preferences**: If `AlertPreference.enabled == False`, or the event's severity is below `preference.minimum_severity`, or `event.alert_type` is not in `allowed_alert_types`, generation is suppressed.
3. **Alert Rule Matching**:
   - Matches rule `enabled == True`.
   - Matches `rule.alert_type == event.alert_type`.
   - Threshold check: `severity_rank(event.severity) >= severity_rank(rule.minimum_severity)`.
   - Rule scoping: Watchlist-specific rules take precedence over user-wide rules (`watchlist_id == None`).
   - If no enabled rule matches, no `AlertEvent` is created.

---

## 10. AlertEvent Generation
When a candidate matches an active rule, an `AlertEvent` is generated with:
- `alert_event_id`: Unique UUID.
- `tenant_id` & `user_id`: Scoped to owner.
- `watchlist_id` & `alert_rule_id`: Scoped to parent subscription and matching rule.
- `source_event_id`: Traceable back to the originating event.
- `alert_type`: Standardized `AlertType`.
- `severity`: Standardized `AlertSeverity` (`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- `title`: Clean headline (e.g. `[Bill Status Change] The Coastal Shipping Bill, 2024`).
- `summary`: Structured 4-way separation.
- `dedup_key`: Canonical SHA-256 hash.
- `metadata`: Contains matched dimensions, source event payload, provenance, and structured content.

---

## 11. Deduplication
Deduplication identity adheres to the mathematical design from Task 8.13.1 / 8.13.2:
$$\text{dedup\_key} = \text{SHA-256}(\text{user\_id} \mathbin{\Vert} \text{watchlist\_id} \mathbin{\Vert} \text{source\_event\_id} \mathbin{\Vert} \text{alert\_type})$$

Before creating an `AlertEvent`, `AlertEventRepository.is_duplicate(dedup_key)` is checked. If present, the duplicate creation is avoided and the existing record is returned.

---

## 12. Idempotency
Given identical input events and unchanged watchlist/rule configurations:
- First execution: Generates and persists the `AlertEvent`.
- Subsequent executions: Detect existing `dedup_key` in `dedup_index.json` and return the existing record without writing duplicate files to disk.

---

## 13. State Handling
State legislative and exposure events remain strictly jurisdiction-aware:
- Match `idx_state` and `idx_jurisdiction["state"]`.
- Include verified legislative status, statutory evidence, and qualitative sector relevance.
- State predictions are strictly **none**.
- Never predict stock returns, price targets, or market impact for State legislation.

---

## 14. Central Handling
Central bills match direct bill subscribers, sector subscribers, and `idx_jurisdiction["central"]`. Validated corporate exposures to Central bills (such as Adani Ports or Container Corporation of India) resolve company subscribers accurately. Central quantitative prediction baseline data remains strictly read-only.

---

## 15. Fact / Derived / Interpretation / Prediction Separation
All `AlertEvent` records strictly enforce the project's four-pillar knowledge separation in both human-readable `summary` and machine-readable `metadata.structured_content`:
- **FACT**: Factual description of legislative change or official filing.
- **DERIVED**: Analytical classifications (e.g. sector, jurisdiction, directness, exposure mechanism).
- **INTERPRETATION**: Qualitative assessment of operational relevance and regulatory compliance lead time.
- **PREDICTION**: Strictly `"none"` for all State events and intelligence-only companies. Only references validated production predictions if an explicit Central quantitative prediction artifact exists.

---

## 16. Persistence
All `AlertEvent` records are persisted via `AlertEventRepository` under:
```
storage/alerts/events/
  dedup_index.json
  {tenant_id}/{user_id}/
    event_{alert_event_id}.json
```
The repository enforces schema validation, atomic JSON serialization, and automatic synchronization with `dedup_index.json`.

---

## 17. Tenant / User Isolation
The matching service enforces complete multi-tenant and user isolation:
- Candidates are partitioned by `(tenant_id, user_id, watchlist_id)`.
- Alert rules and preferences are only evaluated for the candidate's tenant and user.
- Persisted files reside in tenant- and user-specific subdirectories.
- Cross-tenant and cross-user data leakage is strictly prevented.

---

## 18. Performance
Performance is optimized for real-time and batch execution:
- Index queries use $O(1)$ dictionary lookups from memory.
- Multi-dimensional candidates are deduplicated in memory.
- Total processing time scales with the number of matched subscribers, not the universe size.
- Benchmarked test suite processes 40 multi-dimensional tests in under 6 seconds.

---

## 19. Tests
Comprehensive coverage implemented in `tests/test_alert_matching_service.py` (40 tests):
1. Monitoring event normalization
2. Exposure event normalization
3. Missing optional fields handled safely
4. Provenance preserved
5. Company event matches company subscriber
6. Bill event matches bill subscriber
7. Sector event matches sector subscriber
8. Industry event matches industry subscriber
9. State event matches State subscriber
10. Jurisdiction event matches jurisdiction subscriber
11. Event matching multiple dimensions
12. Duplicate subscriber candidate removed
13. Different watchlists remain separate
14. Enabled rule triggers AlertEvent
15. Disabled rule does not trigger
16. Non-matching rule does not trigger
17. Rule isolation by user/watchlist
18. Inactive watchlist does not trigger
19. Tenant isolation
20. User isolation
21. Same event processed twice creates one AlertEvent
22. Same event in different watchlists creates separate AlertEvents
23. Different events create separate AlertEvents
24. Validated company exposure resolves subscribers
25. Invalid/unverified exposure is not fabricated
26. State event resolves State subscriber
27. State event resolves STATE jurisdiction subscriber
28. State event creates no prediction
29. Central bill event resolves Central subscribers
30. Existing Central prediction data remains untouched
31. AlertEvent survives repository reload
32. Dedup survives service restart/reload
33. Monitoring ChangeEvent can be processed
34. Company exposure event can be processed
35. Unified bill event can be processed
36. Central 47 companies unchanged
37. Central 940 pairs unchanged
38. Central 4,700 predictions unchanged
39. State 86 exposures unchanged
40. State predictions remain 0

---

## 20. Baseline Integrity
Validation confirms:
- `CENTRAL_QUANTITATIVE_COMPANIES == 47`
- `CENTRAL_BILL_COMPANY_PAIRS == 940`
- `CENTRAL_PREDICTIONS == 4700`
- `STATE_EXPOSURES == 86`
- `STATE_PREDICTIONS == 0`
- `CENTRAL_BASELINE_CHANGED == False`

---

## 21. Non-Goals
The following areas are strictly out of scope and were **not** implemented in Task 8.13.4:
- Notification delivery (Email, SMS, Webhooks, Push notifications).
- External messaging integrations.
- Digest generation or delivery schedulers.
- Frontend SaaS UI (Next.js, React).
- User authentication, login, or registration pages.
- AI alert synthesis or automatic prediction generation.
- Model retraining or model modification.
- Multi-entity alert aggregation across distinct events (deferred to Task 8.13.5).

---

## 22. Recommended Task 8.13.5
**Task 8.13.5 — Alert Aggregation, Digest Pipeline & In-App Notification Center**:
- Implement alert batching and aggregation across multiple events (e.g. daily/weekly rollups).
- Build digest formatting models (`DAILY_DIGEST`, `WEEKLY_DIGEST`).
- Implement user notification delivery state management (`Notification` record lifecycle: `DELIVERED`, `READ`, `SUPPRESSED`).
- Establish in-app notification center data providers.
