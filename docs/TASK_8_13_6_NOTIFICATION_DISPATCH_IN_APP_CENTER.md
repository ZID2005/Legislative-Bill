# TASK 8.13.6 — Notification Dispatch & In-App Notification Center API

## 1. Objective
Task 8.13.6 establishes the notification application layer connecting upstream `AlertEvent`, `AlertGroup`, and `AlertDigest` pipelines to an in-app notification center and persistence engine. This layer creates presentation-ready, deduplicated, traceable notifications with complete lifecycle management (read/unread toggling, archiving, and evidence-preserving soft deletion), multi-dimensional deterministic filtering, pagination, and multi-tenant isolation.

```
Monitoring / Exposure Event
        ↓
Alert Matching (Task 8.13.4)
        ↓
AlertEvent
        ↓
Alert Aggregation (Task 8.13.5)
        ↓
AlertGroup
        ↓
Alert Digest (Task 8.13.5)
        ↓
========================= TASK 8.13.6 =========================
Notification Creation & Deduplication
        ↓
NotificationDispatcher (In-App & Preferences)
        ↓
NotificationRepository (JSON Persistence & notif_index.json)
        ↓
In-App Notification Center Service & API Contract
        ↓
Read / Unread / Archive / Delete State Management
        ↓
Frontend-Ready Data & Navigation Deep-Links
```

---

## 2. Notification Architecture
The notification system is structured into five cohesive modules:
1. **Schema Layer** ([schemas/alert.py](file:///d:/Legislative-bill/schemas/alert.py)): Defines `Notification`, `NotificationType`, `NotificationSourceType`, `NotificationChannel`, `NotificationStatus`, deduplication key computation, and deep-link routing structures.
2. **Storage Layer** ([storage/notification_repository.py](file:///d:/Legislative-bill/storage/notification_repository.py)): Implements isolated JSON persistence per tenant and user (`storage/alerts/notifications/{tenant_id}/{user_id}/notif_{notification_id}.json`) with a deterministic deduplication index (`notif_index.json`).
3. **Dispatcher Abstraction** ([services/notification_dispatcher.py](file:///d:/Legislative-bill/services/notification_dispatcher.py)): Evaluates recipient `AlertPreference` configuration and dispatches in-app notifications while explicitly reserving stubbed interfaces for future external channels without network calls.
4. **Notification Business Service** ([services/notification_service.py](file:///d:/Legislative-bill/services/notification_service.py)): Handles transformations from `AlertEvent`, `AlertGroup`, and `AlertDigest` into deduplicated in-app notifications.
5. **Notification Center Service** ([services/notification_center_service.py](file:///d:/Legislative-bill/services/notification_center_service.py)): Exposes an API-ready contract for listing, retrieving, paginating, filtering, toggling read/archive/delete states, and computing summary metrics.

---

## 3. Notification Data Model
The `Notification` dataclass incorporates full presentation, traceability, routing, and lifecycle fields:

| Field | Type | Description |
|---|---|---|
| `notification_id` | `str` | Unique notification identifier (UUID or deterministic). |
| `tenant_id` | `str` | Tenant identifier for multi-tenant isolation. |
| `user_id` | `str` | Recipient user identifier. |
| `alert_event_id` | `str` | Reference to AlertEvent (or first event in group/digest). |
| `channel` | `NotificationChannel` | `IN_APP` (primary), `EMAIL`, `PUSH`, `WEBHOOK`. |
| `status` | `NotificationStatus` | `PENDING`, `DELIVERED`, `FAILED`, `READ`, `SUPPRESSED`. |
| `created_at` | `str` | UTC ISO-8601 creation timestamp. |
| `delivered_at` | `Optional[str]` | UTC ISO-8601 timestamp of delivery to notification center. |
| `read_at` | `Optional[str]` | UTC ISO-8601 timestamp when marked read. |
| `error_message` | `Optional[str]` | Failure reason if status is `FAILED`. |
| `title` | `str` | Human-readable headline. |
| `summary` | `str` | Detailed factual summary body. |
| `notification_type`| `NotificationType` | Categorization enum. |
| `severity` | `Optional[AlertSeverity]` | Grounded severity level (`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). |
| `source_type` | `str` | Source object kind (`ALERT_EVENT`, `ALERT_GROUP`, `DIGEST`, `SYSTEM`). |
| `source_id` | `str` | Primary source identifier. |
| `alert_group_id` | `Optional[str]` | Foreign key to AlertGroup if derived from group. |
| `digest_id` | `Optional[str]` | Foreign key to AlertDigest if derived from digest. |
| `entity_type` | `Optional[str]` | Primary impacted entity kind (`BILL`, `COMPANY`, `STATE`, etc.). |
| `entity_id` | `Optional[str]` | Primary impacted entity identifier. |
| `state` | `Optional[str]` | State identifier if state-specific. |
| `jurisdiction` | `Optional[str]` | `'central'` or `'state'`. |
| `is_read` | `bool` | Fast boolean read toggle. |
| `is_archived` | `bool` | Active vs. archived state flag. |
| `archived_at` | `Optional[str]` | UTC ISO-8601 timestamp when archived. |
| `is_deleted` | `bool` | Soft delete flag preserving evidence. |
| `deleted_at` | `Optional[str]` | UTC ISO-8601 timestamp of soft deletion. |
| `deep_link` | `dict[str, Any]` | Structured frontend routing metadata. |
| `dedup_key` | `str` | SHA-256 deduplication key. |
| `metadata` | `dict[str, Any]` | Contextual metadata (predictions, exposures, counts). |

---

## 4. AlertEvent → Notification
`create_notification_from_alert_event(event: AlertEvent)`:
- Preserves `source_id = event.alert_event_id`, `source_type = "ALERT_EVENT"`.
- Preserves `tenant_id`, `user_id`, `watchlist_id`, `alert_rule_id`.
- Maps `alert_type` to `NotificationType` (e.g. `NEW_BILL` → `BILL_UPDATE`, `NEW_COMPANY_EXPOSURE` → `COMPANY_EXPOSURE`, `STATE_IMPACT` → `STATE_UPDATE`).
- Reuses grounded title, summary, and severity without modification.
- Preserves Central bill prediction references (`prediction_id`, `predicted_car`) without recalculation.
- Avoids fabricating stock predictions for State bills and intelligence-only companies.

---

## 5. AlertGroup → Notification
`create_notification_from_alert_group(group: AlertGroup)`:
- Preserves `source_id = group.group_id`, `alert_group_id = group.group_id`, `source_type = "ALERT_GROUP"`.
- Preserves `event_ids` and references the first underlying event in `alert_event_id`.
- Reuses aggregated title, summary, and group maximum severity.
- Reduces notification noise by generating one notification per aggregated group.

---

## 6. Digest → Notification
`create_notification_from_digest(digest: AlertDigest)`:
- Preserves `source_id = digest.digest_id`, `digest_id = digest.digest_id`, `source_type = "DIGEST"`.
- Sets `notification_type = NotificationType.DIGEST`.
- Constructs structured headline and summary referencing period and entity counts.
- Stores deep-link routing metadata to the digest view.
- Strictly in-app: no external email/push delivery.

---

## 7. Notification Deduplication
Deduplication is computed deterministically using:
$$\text{dedup\_key} = \text{SHA-256}(\text{tenant\_id} \parallel \text{user\_id} \parallel \text{source\_type} \parallel \text{source\_id} \parallel \text{channel})$$
- Evaluated before persistence.
- Maintained across invocations via `storage/alerts/notifications/notif_index.json`.
- Multiple calls to `create_notification_from_alert_event`, `create_notification_from_alert_group`, or `create_notification_from_digest` return the existing notification instance without duplicating records.
- Separate users receiving the same underlying alert event generate distinct, isolated notification records.

---

## 8. In-App Dispatcher
`NotificationDispatcher`:
- Coordinates in-app delivery via `NotificationRepository`.
- Evaluates recipient preferences prior to dispatch:
  - If user master toggle is disabled: `status = NotificationStatus.SUPPRESSED`.
  - If `IN_APP` channel is not permitted: `status = NotificationStatus.SUPPRESSED`.
  - If severity is below user's minimum severity threshold: `status = NotificationStatus.SUPPRESSED`.
  - If alert type is disallowed: `status = NotificationStatus.SUPPRESSED`.
  - If permitted: `status = NotificationStatus.DELIVERED`, `delivered_at = _utcnow_iso()`.
- Unimplemented external channels (`dispatch_email`, `dispatch_push`, `dispatch_webhook`) raise `NotImplementedError` to safeguard against accidental external network calls.

---

## 9. Read / Unread Behavior
- `mark_as_read(notification_id, tenant_id, user_id)`:
  - Sets `is_read = True`, `status = NotificationStatus.READ`, `read_at = _utcnow_iso()`.
- `mark_as_unread(notification_id, tenant_id, user_id)`:
  - Sets `is_read = False`, `status = NotificationStatus.DELIVERED`, `read_at = None`.
- `mark_all_read(user_id, tenant_id)`:
  - Identifies all active unread notifications belonging to the user and tenant.
  - Updates each to read status and returns the count of updated records.
  - Does not affect archived or deleted records.

---

## 10. Archive Behavior
- `archive(notification_id, tenant_id, user_id)`:
  - Sets `is_archived = True`, `archived_at = _utcnow_iso()`.
- `unarchive(notification_id, tenant_id, user_id)`:
  - Sets `is_archived = False`, `archived_at = None`.
- `archive_multiple(notification_ids, user_id, tenant_id)`:
  - Batch archives matching notifications for the user.
- **Default Exclusion**: By default, `list_notifications` excludes archived records (`is_archived=False`), keeping the primary inbox clean while preserving archived records accessible via `is_archived=True`.

---

## 11. Delete Behavior
- `delete(notification_id, tenant_id, user_id, soft=True)`:
  - **Soft Delete** (`soft=True`): Sets `is_deleted = True`, `deleted_at = _utcnow_iso()`. Preserves historical alert evidence on disk while excluding it from all standard active and archived views.
  - **Hard Delete** (`soft=False`): Removes the JSON file from disk and cleans up `notif_index.json`. Does NOT touch source `AlertEvent`, `AlertGroup`, or `AlertDigest` records.
- Legislative monitoring and exposure evidence is never destroyed by notification deletion.

---

## 12. Filtering
`NotificationCenterService.list_notifications` supports deterministic multi-dimensional filtering:
- `is_read`: `True` (read only), `False` (unread only), `None` (all).
- `is_archived`: `True` (archived only), `False` (active only), `None` (all).
- `is_deleted`: Defaults to `False`.
- `notification_type`: Filters by `ALERT`, `DIGEST`, `BILL_UPDATE`, `COMPANY_EXPOSURE`, `STATE_UPDATE`, `LEGISLATIVE_UPDATE`, `SYSTEM`.
- `severity`: Filters by `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
- `start_time` / `end_time`: ISO UTC timestamp boundary filtering.
- `entity_type` / `entity_id`: Matches canonical impacted entities.
- `bill_id`: Matches bill identifiers in entity or metadata.
- `company_id`: Matches company identifiers or ISINs.
- `state`: Matches State jurisdiction identifiers (e.g. `'karnataka'`, `'maharashtra'`).
- `jurisdiction`: Matches `'central'` or `'state'`.
- `source_type` / `source_id`: Filters by underlying source reference.

---

## 13. Pagination
- Supported parameters: `limit` (page size) and `offset` (record skip).
- Applied in memory after filtering user-scoped records.
- Prevents unlimited memory consumption.
- Complexity: $O(\text{page\_size})$ slice retrieval after sorting user-scoped records.

---

## 14. Deterministic Ordering
Notifications are sorted deterministically using a two-tuple key:
$$\text{Sort Key} = (\text{created\_at} \text{ desc}, \text{notification\_id} \text{ desc})$$
If creation timestamps are identical, the stable secondary identifier prevents non-deterministic ordering or pagination jitter.

---

## 15. User & Tenant Isolation
Strict isolation is enforced at directory, repository, and service boundaries:
- Storage layout: `storage/alerts/notifications/{tenant_id}/{user_id}/notif_{notification_id}.json`.
- Service queries only inspect the folder for `(tenant_id, user_id)`.
- Verification guarantees:
  - User A cannot read User B's notifications.
  - User A cannot modify (read/archive/delete) User B's notifications.
  - Tenant A cannot read Tenant B's notifications.
  - Tenant A cannot modify Tenant B's notifications.

---

## 16. Preference Integration
Integrated with `AlertPreferenceRepository`:
- Evaluates recipient preferences for master toggle (`enabled`), permitted channels (`allowed_channels`), minimum severity threshold (`minimum_severity`), and allowed alert types (`allowed_alert_types`).
- Non-qualifying notifications are marked `NotificationStatus.SUPPRESSED` and excluded from the user's active notification inbox.

---

## 17. Deep-Link Navigation Metadata
`build_deep_link` populates structured routing metadata prepared for future frontend web/mobile navigation:
- Bills: `{"destination_type": "BILL_DETAIL", "entity_type": "BILL", "entity_id": "...", "route": "/bills/{bill_id}"}`
- Companies: `{"destination_type": "COMPANY_DETAIL", "entity_type": "COMPANY", "entity_id": "...", "route": "/companies/{company_id}"}`
- States: `{"destination_type": "STATE_EXPLORER", "entity_type": "STATE", "entity_id": "...", "route": "/states/{state}"}`
- Alert Groups: `{"destination_type": "ALERT_GROUP_DETAIL", "entity_type": "ALERT_GROUP", "entity_id": "...", "route": "/alerts/groups/{group_id}"}`
- Digests: `{"destination_type": "DIGEST_DETAIL", "entity_type": "DIGEST", "entity_id": "...", "route": "/digests/{digest_id}"}`

---

## 18. Notification Center Summary
`NotificationCenterSummary` provides high-level metrics for dashboard header widgets:
- `total_active`: Count of active un-archived notifications.
- `unread_count`: Count of active unread notifications.
- `archived_count`: Count of archived notifications.
- `alert_count`: Non-digest alert notifications.
- `digest_count`: Digest notifications.
- `latest_notification_at`: Timestamp of newest active notification.
- `counts_by_type`: Breakdown dictionary per `NotificationType`.
- `counts_by_severity`: Breakdown dictionary per `AlertSeverity`.

---

## 19. API-Ready Service Contract
Methods in `NotificationCenterService` map directly to future HTTP endpoints:
- `GET /notifications` → `list_notifications(user_id, tenant_id, limit, offset, ...)`
- `GET /notifications/unread` → `get_unread_notifications(user_id, tenant_id, limit)`
- `GET /notifications/unread-count` → `get_unread_count(user_id, tenant_id, include_archived)`
- `GET /notifications/recent` → `get_recent_notifications(user_id, tenant_id, limit)`
- `GET /notifications/summary` → `get_notification_center_summary(user_id, tenant_id)`
- `GET /notifications/{notification_id}` → `get_notification(notification_id, tenant_id, user_id)`
- `POST /notifications/{notification_id}/read` → `mark_read(notification_id, tenant_id, user_id)`
- `POST /notifications/{notification_id}/unread` → `mark_unread(notification_id, tenant_id, user_id)`
- `POST /notifications/read-all` → `mark_all_read(user_id, tenant_id)`
- `POST /notifications/{notification_id}/archive` → `archive(notification_id, tenant_id, user_id)`
- `POST /notifications/{notification_id}/unarchive` → `unarchive(notification_id, tenant_id, user_id)`
- `POST /notifications/archive-multiple` → `archive_multiple(notification_ids, user_id, tenant_id)`
- `DELETE /notifications/{notification_id}` → `delete(notification_id, tenant_id, user_id, soft=True)`

---

## 20. Performance & Complexity
- **Storage Access**: Scoped directly to `storage/alerts/notifications/{tenant_id}/{user_id}/`. Unrelated tenants or users are never scanned.
- **Deduplication Lookup**: $O(1)$ dictionary lookup against persistent `notif_index.json`.
- **Query Retrieval**: $O(N \log N)$ sorting for $N$ user-scoped notifications, followed by $O(\text{page\_size})$ pagination slicing.
- **Unread Count**: Single pass $O(N)$ over user's notification records without reading entire system state.

---

## 21. Tests & Validation
The suite covers all 52 required test points:
- `tests/test_notification_service.py`: 26 tests covering creation, deduplication, preferences, traceability, State notifications, Central notifications, intelligence-only companies, dispatch stubs, pipeline integration, and baseline integrity.
- `tests/test_notification_center_service.py`: 16 tests covering read state, archive lifecycle, multi-criteria filtering, pagination, deterministic ordering, tenant/user isolation, summary metrics, and bulk operations.

---

## 22. Baseline Integrity Verification
- `CENTRAL_QUANTITATIVE_COMPANIES` = 47 (Verified)
- `CENTRAL_BILL_COMPANY_PAIRS` = 940 (Verified)
- `CENTRAL_PREDICTIONS` = 4,700 (Verified)
- `STATE_EXPOSURES` = 86 (Verified)
- `STATE_PREDICTIONS` = 0 (Verified)
- `CENTRAL_BASELINE_CHANGED` = `False` (Verified)

---

## 23. Strict Non-Goals Respected
- No email, SMS, push, or webhook external delivery providers implemented.
- No SaaS frontend / Next.js / React components constructed.
- No AI notification synthesis or speculative text generation.
- No model retraining, prediction regeneration, or market model modification.
- No State stock predictions or fabricated intelligence company alpha forecasts.

---

## 24. Recommended Next Task
**Task 8.13.7 — SaaS Notification Delivery Providers & Outbound Dispatch Webhooks**
- Implement concrete provider integrations (SendGrid/SMTP for Email, Webhook Dispatcher with HMAC signing, WebPush for mobile/browser).
- Implement delivery retry logic with exponential backoff and dead-letter handling.
- Extend alert preferences for recipient webhook endpoints and notification delivery schedules.
