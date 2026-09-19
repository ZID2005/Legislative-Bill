# Task 8.13.8: Watchlist & Alert System Integration, E2E Verification & Hardening

## 1. Objective

Task 8.13.8 is the final backend integration, end-to-end (E2E) verification, and hardening checkpoint for the Indian Legislative Intelligence Platform's Watchlist & Alert subsystem. Its purpose is to prove that all individual layers developed across Tasks 8.13.1 through 8.13.7 function together cohesively, safely, and deterministically under diverse operating conditions, edge cases, and failure modes—without modifying the frozen baseline or introducing unapproved features.

---

## 2. Complete Pipeline Architecture

The end-to-end alert pipeline connects authoritative legislative sources to user consumption through a strict unidirectional lifecycle:

```
Official Legislative Sources (Lok Sabha / Rajya Sabha / Gazette / State Assemblies)
        ↓
Legislative Monitoring Subsystem (Scrapers, Change Detection, Content Hashing)
        ↓
ChangeEvent / NotificationEvent / StateCorporateExposure
        ↓
Alert Matching Service (Entity resolution, inverted index lookup, rule evaluation)
        ↓
AlertEvent (User-specific, watchlist-bound, deduped, structured content)
        ↓
Alert Aggregation Service (Temporal sliding window, entity grouping, digest grouping)
        ↓
AlertGroup (Canonical cluster of correlated alert events)
        ↓
Alert Digest Service (Daily/weekly/real-time summaries & statistical rollups)
        ↓
Notification Service & Center (In-app notifications, read/archive states, soft-delete)
        ↓
Notification Dispatcher (Channel routing, preference filtering, idempotency keys)
        ↓
Outbound Providers (MockEmailProvider, MockPushProvider, WebhookNotificationProvider)
```

### Key Architectural Properties
- **Strict Inverted Index Querying**: O(1) subscriber resolution without scanning all users, watchlists, or entities.
- **Structured Content Firewall**: Preserves Facts vs. Derived vs. Interpretation vs. Prediction across transformations.
- **Fail-Safe Downstream Degradation**: A downstream outbound provider failure (e.g. webhook timeout) never invalidates or deletes upstream `AlertEvent`, `AlertGroup`, or `Notification` records.
- **Quantitative Model Isolation**: Zero state predictions, zero intelligence company predictions, and zero modifications to the 4,700 Central baseline predictions.

---

## 3. E2E Flow

The end-to-end pipeline is orchestrated by `services/alert_pipeline_service.py` via `AlertPipelineService.process_event()` and `AlertPipelineService.process_batch()`:

1. **Ingest & Normalize**: Receives heterogeneous events (`ChangeEvent`, `NotificationEvent`, `StateCorporateExposure`, or dicts) and normalizes them into a canonical `NormalizedEvent`.
2. **Subscriber Resolution**: Queries the `WatchlistIndexService` inverted indices (`idx_company`, `idx_bill`, `idx_state`, `idx_sector`, `idx_industry`, `idx_jurisdiction`) to resolve eligible subscribers `(tenant_id, user_id, watchlist_id)`.
3. **Candidate Deduplication**: Multi-dimension matches belonging to the same `(tenant_id, user_id, watchlist_id)` are deduplicated into a single candidate with merged matching dimensions.
4. **Rule & Preference Evaluation**: Evaluates active `AlertRule` criteria (alert type, minimum severity) and user-level `AlertPreference` filters (enabled status, muted channels).
5. **AlertEvent Persistence**: Generates canonical `AlertEvent` records with SHA-256 deduplication keys and persists them to `storage/alerts/events/`.
6. **AlertGroup Aggregation**: Clusters events by entity or bill within configurable sliding windows (default 60 minutes) and persists `AlertGroup` records to `storage/alerts/groups/`.
7. **In-App Notification**: Materializes `Notification` entities with deep links and operational metadata into `storage/alerts/notifications/`.
8. **Optional Outbound Dispatch**: If requested, routes notifications through `NotificationDispatcher` to registered channel providers (`EMAIL`, `PUSH`, `WEBHOOK`).
9. **Pipeline Observability**: Returns a structured `PipelineResult` with per-stage execution durations (ms), success flags, and error details.

---

## 4. Central Event Flow

- **Input**: A Central legislative change event (e.g. Lok Sabha bill status update).
- **Resolution**: Resolves bill subscriber via `idx_bill["the-banking-laws-amendment-bill-2024"]` and jurisdiction subscriber via `idx_jurisdiction["CENTRAL"]`.
- **Alert Generation**: Triggers `AlertEvent` with `jurisdiction="central"`.
- **Integrity**: References existing Central model predictions where applicable; never recomputes or alters production prediction files.

---

## 5. State Event Flow

- **Input**: A State assembly monitoring event (e.g. Kerala Gig Workers Bill gazette notification).
- **Resolution**: Resolves state subscriber via `idx_state["KERALA"]` and jurisdiction subscriber via `idx_jurisdiction["STATE"]`.
- **Zero Prediction Guarantee**: `prediction_summary` is enforced as `None` or `"none"`.
- **Integrity**: State identity (`state="Kerala"`) and state bill identity are preserved throughout the pipeline with zero stock-market predictions generated.

---

## 6. Company Exposure Flow

- **Input**: Evidence-based `StateCorporateExposure` record (e.g. Swiggy Limited exposure under Kerala Gig Workers Bill).
- **Resolution**: Resolves company subscriber via `idx_company["PRIV-BUNDL-SWIGGY"]`.
- **Evidence Preservation**: Grounded statutory evidence (e.g. Section 3(1) citations) is preserved in `AlertEvent.evidence` and propagated into notification payloads.
- **Firewall Isolation**: Validated corporate exposure intelligence remains strictly non-predictive.

---

## 7. Sector & Industry Flow

- **Sector Resolution**: Legislative events tagging sectors (e.g. `Technology`, `Financial Services`) resolve subscribers via `idx_sector` without scanning unrelated watchlists.
- **Industry Resolution**: Events specifying sub-sectors/industries (e.g. `Food Delivery & Quick Commerce`) resolve subscribers via `idx_industry`.
- **Taxonomy Adherence**: Only existing verified sector and industry identifiers from the canonical taxonomy are accepted.

---

## 8. Multi-Dimensional Matching

When a single event impacts multiple dimensions simultaneously (e.g. Bill X in Kerala affecting Technology sector and Company Z):
1. The engine queries all relevant indices concurrently or sequentially.
2. Candidate grouping groups matches on `(tenant_id, user_id, watchlist_id)`.
3. Exactly **one** `AlertEvent` is generated per watchlist, preserving all matched dimensions in its metadata.
4. Redundant alert spam is eliminated at the engine layer.

---

## 9. Multi-Watchlist Behavior

- When a single user maintains multiple distinct watchlists (e.g. "Core Tech" and "Logistics") both watching the same entity:
  - Each watchlist evaluates its own rules independently.
  - Each eligible watchlist receives its own distinct `AlertEvent` with distinct `watchlist_id`.
  - Aggregation preserves watchlist provenance without conflating watchlist-specific contexts.

---

## 10. Multi-User Isolation

- Two users watching the same entity within the same tenant:
  - User A receives `AlertEvent` and `Notification` keyed only to User A.
  - User B receives records keyed only to User B.
  - Notification center queries strictly filter by `user_id` and `tenant_id`; neither user can see or alter the other's records.

---

## 11. Multi-Tenant Isolation

- Users in Tenant A and Tenant B watching the same company or bill:
  - Directory storage paths partition by tenant ID (`storage/alerts/{tenant_id}/...`).
  - Index keys and subscriber records are tenant-scoped.
  - Cross-tenant queries return zero records, preventing any data leakage.

---

## 12. Failure Recovery

- **Invalid Events**: Missing mandatory fields or malformed dictionaries trigger graceful fallbacks or safe validation skips without crashing the pipeline.
- **Disabled Rules/Watchlists**: Inactive watchlists or disabled alert rules are excluded during candidate resolution or rule evaluation.
- **Unreachable Outbound Provider**: Network or HTTP 500 errors in outbound providers (Email, Push, Webhook) record delivery status as `FAILED` with retry backoff metadata; upstream `AlertEvent`, `AlertGroup`, and `Notification` records remain fully intact.

---

## 13. Idempotency & Duplicate Protection

- Processing the identical monitoring event multiple times:
  - SHA-256 deduplication key based on `(tenant_id, user_id, watchlist_id, event_id)` prevents duplicate `AlertEvent` generation.
  - `AlertGroup` membership checks prevent duplicate event clustering.
  - In-app notification creation enforces deduplication against existing source event references.
  - Outbound providers enforce idempotency keys via `X-Notification-Idempotency-Key` headers.

---

## 14. Restart / Reload Behavior

- All primary state is persisted to disk in JSON format:
  - Watchlists: `data/watchlists/`
  - Inverted Indices: `data/watchlists/indices/`
  - Alert Events: `storage/alerts/events/`
  - Alert Groups: `storage/alerts/groups/`
  - Notifications: `storage/alerts/notifications/`
- After stopping and reloading the service instances, indices are automatically reloaded from disk or rebuilt from canonical watchlists.
- Reprocessing previously ingested events produces zero duplicates.

---

## 15. Index Corruption Recovery

- `WatchlistIndexService.validate_indices()` inspects all inverted index buckets against the canonical watchlist repository.
- Corrupted, stale, or tampered index buckets are flagged with explicit error diagnostics.
- `WatchlistIndexService.rebuild_all_indices()` idempotently reconstructs all 6 inverted indices from source records, restoring a verified healthy state.

---

## 16. Watchlist Deactivation

- Deactivating a watchlist sets `is_active=False` and purges its subscribers from all inverted indices.
- Subsequent legislative events matching entities previously in that watchlist generate zero new alerts for that watchlist.
- Historical `AlertEvent` and `Notification` records created prior to deactivation remain preserved for auditing.

---

## 17. Alert-Rule Deactivation

- Disabling a rule sets `is_enabled=False`.
- The matching engine skips disabled rules during candidate evaluation.
- Historical alert events generated while the rule was active remain intact.

---

## 18. Preference Handling

- `AlertPreference.minimum_severity`: Suppresses alert generation when event severity is lower than the user's configured threshold (e.g. `INFO` suppressed when threshold is `HIGH`).
- `AlertPreference.allowed_alert_types`: Blocks events whose alert types are not in the user's allow-list.
- Channel mutes: When `email_enabled=False` or `webhook_enabled=False`, outbound delivery is bypassed.

---

## 19. Outbound Provider Handling

- **Email Provider**: Validates email format, verifies recipient, logs mock delivery with payload hashes.
- **Push Provider**: Validates push tokens, enforces mock push transport.
- **Webhook Provider**:
  - Enforces HTTPS URL validation (with safe HTTP mock override in test fixtures).
  - Signs payloads with HMAC-SHA256 (`X-Notification-Signature`).
  - Transmits RFC 3339 timestamps and unique idempotency keys.
  - Redacts webhook secrets and tokens from logs and error messages.

---

## 20. Source Traceability

- Every in-app `Notification` contains:
  - `source_event_id`: ID of the originating `AlertEvent` or `AlertGroup`.
  - `source_reference`: Direct reference to the originating bill or company identifier.
  - `deep_link`: Canonical URL pointing to the bill or company detail page.
- Every `AlertGroup` maintains `event_ids: list[str]` linking back to individual `AlertEvent` records.
- Every `AlertEvent` links directly to the originating `ChangeEvent` or `StateCorporateExposure` record.

---

## 21. Fact / Derived / Interpretation / Prediction Integrity

Four distinct analytical layers are preserved throughout the entire transformation chain:
1. **Facts**: Verifiable events (e.g., "Bill passed Lok Sabha on 2024-08-09").
2. **Derived**: Computed classifications (e.g., sector mappings, affected company counts).
3. **Interpretation**: Qualitative analysis (e.g., statutory compliance mechanisms).
4. **Prediction**: Quantitative model forecasts (strictly Central, never State, never intelligence companies).

Transformations never promote derived data to facts, nor interpretation to predictions.

---

## 22. Central Prediction Protection

- All 4,700 Central predictions in `data/predictions/` remain read-only.
- The alert pipeline references existing predictions without recomputing, retraining, or regenerating files.
- SHA-256 hashes and file counts are verified before and after pipeline execution.

---

## 23. Concurrency Considerations

- The alert pipeline utilizes thread-safe file operations and deterministic deduplication keys.
- Near-concurrent processing of the same event yields identical deduplication hashes, preventing duplicate state.
- In single-node deployments, local directory structures provide reliable isolation; distributed locking is documented as a future non-goal until multi-node clustering is required.

---

## 24. Data Integrity

- Automated audit checks confirm:
  - Every `AlertGroup` references existing, valid `AlertEvent` IDs.
  - Every `Notification` contains a valid user ID, tenant ID, and title.
  - Inactive watchlists do not contain active subscribers in the inverted indices.
  - Zero cross-tenant references exist across all repositories.

---

## 25. Performance

- **Subscriber Resolution**: Resolves subscribers across all 6 indices in < 2ms per event via in-memory inverted indices.
- **Full E2E Pipeline**: Matching + Aggregation + Notification + Mock Outbound completes in < 15ms per event.
- **No Table Scans**: Eliminates full-scan complexity ($O(\text{users} \times \text{watchlists} \times \text{items})$).

---

## 26. Verification Test Suite

Task 8.13.8 introduces 71 new tests across two test modules:
- `tests/test_alert_pipeline_e2e.py` (42 tests): Complete E2E integration, multi-dimension, multi-tenant, restart, traceability, and baseline tests.
- `tests/test_alert_hardening.py` (29 tests): Edge-case inputs, malformed events, boundary limits, HMAC tampering, and preference enforcement.

### Test Run Summary
- **E2E Pipeline Tests (`test_alert_pipeline_e2e.py`)**: 42 passed / 0 failed (8.27s)
- **Hardening Tests (`test_alert_hardening.py`)**: 29 passed / 0 failed (3.48s)
- **Watchlist & Alert Test Suite (13 test files)**: 350 passed / 0 failed (25.79s)
- **Extended Platform Regression**: 718+ passed / 0 failed

---

## 27. Baseline Integrity

All frozen baseline parameters were independently verified and confirmed unchanged:

| Metric | Required Frozen Baseline | Verified Actual | Status |
| :--- | :---: | :---: | :---: |
| Central Quantitative Companies | 47 | 47 | PASS |
| Central Bill-Company Pairs | 940 | 940 | PASS |
| Central Predictions | 4,700 | 4,700 | PASS |
| State Corporate Exposures | 86 | 86 | PASS |
| State Predictions | 0 | 0 | PASS |
| Central Baseline Changed | False | False | PASS |

---

## 28. Known Limitations

- **Headless Environment**: Streamlit UI pages (`dashboard/pages/*`) require Streamlit runtime to render visually; tests properly skip UI-specific rendering when Streamlit is uninstalled.
- **Mock Outbound Providers**: Production email, push, and webhook providers operate against mock transports in accordance with strict security and offline testing requirements.
- **Single-Node Persistence**: Local JSON filesystem persistence is optimized for single-node development and verification; multi-node distributed setups will require external database adapters.

---

## 29. Recommended Next Task

- **Task 8.14 — Production Deployment & Operational Hardening** (or Scheduled Background Worker Daemon orchestration for automated periodic monitoring and alert digestion).
