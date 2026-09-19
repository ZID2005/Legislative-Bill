# Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation

**India Legislative Intelligence & Market Impact Prediction Platform**  
**Task:** 8.13.2 — Schemas & Persistent Storage Foundation for Watchlists & Alerts  
**Status:** COMPLETE — ALL 38 SCENARIOS VERIFIED — FROZEN PRODUCTION BASELINES PRESERVED  
**Date:** 2026-09-16  

---

## 1. Objective

Following the architectural audit and design completed in **Task 8.13.1**, the objective of **Task 8.13.2** is to implement the foundational schemas, deterministic validation rules, tenant isolation mechanisms, SHA-256 deduplication logic, and clean file-backed JSON repository storage for the Watchlists and Alerts platform subsystem.

This task establishes the robust data layer for:
1. `User` (Minimal future-compatible identity)
2. `Watchlist` (User collections of monitored entities)
3. `WatchlistItem` (Entity references for Company, Bill, Sector, Industry, State, Jurisdiction)
4. `AlertRule` (Subscription filters and severity thresholds)
5. `AlertEvent` (User inbox alert records with SHA-256 deduplication)
6. `Notification` (In-App delivery state tracking)
7. `AlertPreference` (User cadence and notification channel preferences)

In accordance with strict boundary invariants, this task does **NOT** retrain ML models, does not generate market predictions, strictly preserves 0 State predictions, and defers alert matching, email/push providers, user authentication, and billing to future sub-tasks.

---

## 2. Schema Architecture

The subsystem implements clean separation between identity, subscription, monitoring event detection, user alerting, and notification delivery:

```
┌─────────────────────────────────────────────────────────────┐
│                          Tenant                             │
│               (Default: "default_tenant")                   │
└──────────────────────────────┬──────────────────────────────┘
                               │ 1:N
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                           User                              │
│                 (Default: "default_user")                   │
└───────┬──────────────────────┬───────────────────────┬──────┘
        │ 1:N                  │ 1:1                   │ 1:N
        ▼                      ▼                       ▼
┌───────────────┐      ┌───────────────┐       ┌───────────────┐
│   Watchlist   │      │AlertPreference│       │  AlertEvent   │
└───────┬───────┘      └───────────────┘       │  (User Inbox) │
        │ 1:N                                  └───────┬───────┘
        ▼                                              │ 1:N
┌───────────────┐                                      ▼
│ WatchlistItem │                             ┌────────────────┐
│ (6 categories)│                             │  Notification  │
└───────────────┘                             │  (Deliveries)  │
                                              └────────────────┘
```

---

## 3. User Model (`schemas/user.py`)

A future-compatible multi-tenant identity representation without requiring full authentication at this stage.

```python
@dataclass
class User:
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    display_name: str = ""
    email: Optional[str] = None
    is_active: bool = True
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)
```

- **Invariants**: `user_id` and `tenant_id` cannot be empty or whitespace.
- **Tenant Scoping**: All operations in the system inherit `tenant_id` from the user context.

---

## 4. Watchlist Model (`schemas/watchlist.py`)

Represents a user-owned collection of watched entities.

```python
@dataclass
class Watchlist:
    watchlist_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    name: str = "Default Watchlist"
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)
```

- **Ownership**: A watchlist belongs to exactly one user within a tenant.
- **Status**: Supports soft deactivation (`is_active = False`) and hard deletion.

---

## 5. WatchlistItem Model (`schemas/watchlist.py`)

Represents an individual watched target entity within a specific watchlist.

```python
@dataclass
class WatchlistItem:
    watchlist_id: str
    entity_type: WatchlistEntityType
    entity_id: str
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    display_name: str = ""
    notes: Optional[str] = None
    custom_tags: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: str = field(default_factory=_utcnow_iso)
```

### Supported Entity Types:
1. `COMPANY`: Canonical ISIN or synthetic ID (e.g. `PRIV-BUNDL-SWIGGY`, `INE009A01021`, `INE758T01015`).
2. `BILL`: Canonical legislative bill identifier (e.g. `the-coastal-shipping-bill-2024`, `the-digital-personal-data-protection-bill-2023`).
3. `SECTOR`: Canonical sector classification (e.g. `Technology`, `Banking & Financial Services`).
4. `INDUSTRY`: Granular sub-industry taxonomy (e.g. `Food Delivery & Quick Commerce`).
5. `STATE`: Normalized Indian State name (e.g. `Kerala`, `Karnataka`, `Telangana`).
6. `JURISDICTION`: `central` or `state`.

### Entity Reference Validation (`validate_entity_reference`):
- Guarantees entity identifiers are stable and validated against canonical taxonomy rules.
- Prevents empty strings, whitespace, or random invalid symbols.
- Normalizes State names through `utils.state_normalizer.normalize_state`.

---

## 6. AlertRule Model (`schemas/alert.py`)

Represents user-defined subscription filters that govern when alerts should trigger.

```python
@dataclass
class AlertRule:
    alert_rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    watchlist_id: Optional[str] = None  # None = applies across all user watchlists
    alert_type: AlertType = AlertType.BILL_STATUS_CHANGE
    minimum_severity: AlertSeverity = AlertSeverity.LOW
    enabled: bool = True
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)
```

- **Supported Alert Types**:
  - `NEW_BILL`
  - `BILL_STATUS_CHANGE`
  - `BILL_VERSION_CHANGE`
  - `BILL_DOCUMENT_CHANGE`
  - `NEW_COMPANY_EXPOSURE`
  - `EXPOSURE_CHANGE`
  - `SECTOR_IMPACT`
  - `STATE_IMPACT`
  - `LEGISLATIVE_MONITORING_CHANGE`
- **Quantitative Firewall**: Explicitly rejects unsupported speculative prediction alert types (e.g. `PREDICTION_UPDATE`).

---

## 7. AlertEvent Model (`schemas/alert.py`)

Represents a user-relevant alert generated from an underlying monitoring or corporate exposure change event.

```python
@dataclass
class AlertEvent:
    alert_event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default_tenant"
    user_id: str = "default_user"
    watchlist_id: Optional[str] = None
    alert_rule_id: Optional[str] = None
    source_event_id: str = ""
    alert_type: AlertType = AlertType.BILL_STATUS_CHANGE
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str = ""
    summary: str = ""
    entity_type: Optional[WatchlistEntityType] = None
    entity_id: Optional[str] = None
    created_at: str = field(default_factory=_utcnow_iso)
    is_read: bool = False
    read_at: Optional[str] = None
    is_archived: bool = False
    archived_at: Optional[str] = None
    dedup_key: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
```

- **Traceability**: Contains `source_event_id` linking back to the raw `ChangeEvent` or `NotificationEvent` from Task 8.11.
- **Inbox Actions**: Supports `mark_read()` and `archive()` with ISO timestamps.

---

## 8. Notification Model (`schemas/alert.py`)

Tracks the delivery state and channel dispatch of an alert event.

```python
@dataclass
class Notification:
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default_tenant"
    user_id: str = "default_user"
    alert_event_id: str = ""
    channel: NotificationChannel = NotificationChannel.IN_APP
    status: NotificationStatus = NotificationStatus.DELIVERED
    created_at: str = field(default_factory=_utcnow_iso)
    delivered_at: Optional[str] = field(default_factory=_utcnow_iso)
    read_at: Optional[str] = None
    error_message: Optional[str] = None
```

- **Initial Supported Channel**: `IN_APP` (with enum support for future `EMAIL`, `PUSH`, `WEBHOOK`).
- **Statuses**: `PENDING`, `DELIVERED`, `FAILED`, `READ`, `SUPPRESSED`.

---

## 9. AlertPreference Model (`schemas/alert.py`)

User-level configuration governing notification cadence and channels.

```python
@dataclass
class AlertPreference:
    preference_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    enabled: bool = True
    minimum_severity: AlertSeverity = AlertSeverity.LOW
    allowed_alert_types: list[AlertType] = field(default_factory=lambda: list(AlertType))
    allowed_channels: list[NotificationChannel] = field(
        default_factory=lambda: [NotificationChannel.IN_APP]
    )
    digest_frequency: DigestFrequency = DigestFrequency.REAL_TIME
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)
```

- **Cadence Options**: `REAL_TIME`, `DAILY_DIGEST`, `WEEKLY_DIGEST`.

---

## 10. Enum Definitions

| Enum | Values |
|---|---|
| `WatchlistEntityType` | `COMPANY`, `BILL`, `SECTOR`, `INDUSTRY`, `STATE`, `JURISDICTION` |
| `AlertType` | `NEW_BILL`, `BILL_STATUS_CHANGE`, `BILL_VERSION_CHANGE`, `BILL_DOCUMENT_CHANGE`, `NEW_COMPANY_EXPOSURE`, `EXPOSURE_CHANGE`, `SECTOR_IMPACT`, `STATE_IMPACT`, `LEGISLATIVE_MONITORING_CHANGE` |
| `AlertSeverity` | `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `NotificationChannel` | `IN_APP`, `EMAIL`, `PUSH`, `WEBHOOK` |
| `NotificationStatus` | `PENDING`, `DELIVERED`, `FAILED`, `READ`, `SUPPRESSED` |
| `DigestFrequency` | `REAL_TIME`, `DAILY_DIGEST`, `WEEKLY_DIGEST` |

---

## 11. Validation Rules

1. **Mandatory Non-Empty IDs**: `user_id`, `tenant_id`, `watchlist_id`, `item_id`, `alert_rule_id`, `alert_event_id`, `notification_id`, `preference_id` cannot be blank.
2. **Entity Validation**: Entity references cannot be arbitrary strings; they are validated per type.
3. **Parent Existence**: WatchlistItem creation strictly checks that the parent watchlist exists and belongs to the same user/tenant.
4. **Duplicate Prevention**: Adding an active item with identical `(watchlist_id, entity_type, entity_id)` raises a `ValueError`.
5. **Severity & Alert Type Validation**: Only recognized enum values are accepted; invalid or predictive alert strings are rejected.

---

## 12. Tenant Isolation

Every entity carries `(tenant_id, user_id)`.
- Filesystem paths partition data by tenant and user: `storage/{module}/{tenant_id}/{user_id}/...`.
- Repository `get()`, `list()`, `update()`, and `delete()` methods scope queries to the requesting tenant and user.
- Cross-tenant and cross-user lookups strictly return `None`.

---

## 13. Deduplication Architecture

Deterministic deduplication is enforced via SHA-256:

$$\text{dedup\_key} = \text{SHA-256}(\text{user\_id} \mathbin{\Vert} \text{watchlist\_id} \mathbin{\Vert} \text{source\_event\_id} \mathbin{\Vert} \text{alert\_type})$$

- Stored directly on `AlertEvent.dedup_key`.
- `AlertEventRepository` maintains a persistent `dedup_index.json` mapping dedup keys to event metadata.
- Attempting to persist an `AlertEvent` with an existing `dedup_key` raises a `ValueError("Duplicate alert event...")`, protecting user inboxes from scheduler retries and re-scrapes.

---

## 14. Storage Architecture

```
storage/
  ├── users/
  │   └── {tenant_id}/
  │       └── user_{user_id}.json
  ├── watchlists/
  │   └── {tenant_id}/
  │       └── {user_id}/
  │           ├── watchlists/
  │           │   └── wl_{watchlist_id}.json
  │           └── items/
  │               └── item_{item_id}.json
  └── alerts/
      ├── rules/
      │   └── {tenant_id}/
      │       └── {user_id}/
      │           └── rule_{alert_rule_id}.json
      ├── events/
      │   ├── dedup_index.json
      │   └── {tenant_id}/
      │       └── {user_id}/
      │           └── event_{alert_event_id}.json
      ├── notifications/
      │   └── {tenant_id}/
      │       └── {user_id}/
      │           └── notif_{notification_id}.json
      └── preferences/
          └── {tenant_id}/
              └── {user_id}/
                  └── preference.json
```

---

## 15. Repository API

### `UserRepository`
- `create(user: User) -> User`
- `get(user_id: str, tenant_id: str = "default_tenant") -> Optional[User]`
- `update(user: User) -> User`
- `list(tenant_id: Optional[str] = None, is_active: Optional[bool] = None) -> list[User]`

### `WatchlistRepository`
- `create(watchlist: Watchlist) -> Watchlist`
- `get(watchlist_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[Watchlist]`
- `update(watchlist: Watchlist) -> Watchlist`
- `delete(watchlist_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None, hard_delete: bool = False) -> bool`
- `list_by_user(user_id: str, tenant_id: str = "default_tenant", is_active: Optional[bool] = None) -> list[Watchlist]`
- `add_item(item: WatchlistItem) -> WatchlistItem`
- `get_item(item_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[WatchlistItem]`
- `remove_item(item_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None, hard_delete: bool = False) -> bool`
- `list_items_by_watchlist(watchlist_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None, is_active: Optional[bool] = None) -> list[WatchlistItem]`
- `find_by_entity(entity_type: WatchlistEntityType | str, entity_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> list[WatchlistItem]`

### `AlertRuleRepository`
- `create(rule: AlertRule) -> AlertRule`
- `get(alert_rule_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[AlertRule]`
- `update(rule: AlertRule) -> AlertRule`
- `enable(alert_rule_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> bool`
- `disable(alert_rule_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> bool`
- `list_by_watchlist(watchlist_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> list[AlertRule]`
- `list_by_user(user_id: str, tenant_id: str = "default_tenant") -> list[AlertRule]`

### `AlertEventRepository`
- `create(event: AlertEvent) -> AlertEvent`
- `get(alert_event_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[AlertEvent]`
- `list_by_user(user_id: str, tenant_id: str = "default_tenant", limit: int = 100) -> list[AlertEvent]`
- `list_by_watchlist(watchlist_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None, limit: int = 100) -> list[AlertEvent]`
- `list_unread(user_id: str, tenant_id: str = "default_tenant", limit: int = 100) -> list[AlertEvent]`
- `mark_read(alert_event_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> bool`
- `archive(alert_event_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> bool`
- `find_by_dedup_key(dedup_key: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[AlertEvent]`
- `is_duplicate(dedup_key: str) -> bool`

### `NotificationRepository`
- `create(notification: Notification) -> Notification`
- `get(notification_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[Notification]`
- `list_by_user(user_id: str, tenant_id: str = "default_tenant", limit: int = 100) -> list[Notification]`
- `mark_delivered(notification_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> bool`
- `mark_read(notification_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> bool`

### `AlertPreferenceRepository`
- `create(pref: AlertPreference) -> AlertPreference`
- `get_by_user(user_id: str, tenant_id: str = "default_tenant") -> Optional[AlertPreference]`
- `update(pref: AlertPreference) -> AlertPreference`

---

## 16. Serialization

All models implement:
- `to_dict() -> dict[str, Any]`
- `from_dict(data: dict[str, Any]) -> ModelClass`
- Full round-trip fidelity: `Model.from_dict(json.loads(json.dumps(model.to_dict()))).to_dict() == model.to_dict()`.
- ISO-8601 UTC timestamps used consistently.

---

## 17. Backward Compatibility

- Existing monitoring runs and change events (`storage/monitoring/`) remain completely untouched.
- Central quantitative companies (47) and intelligence-only entities (20+) load without modification.
- Existing Central predictions (4,700) and State exposures (86) are unmodified.
- The new storage directories (`storage/watchlists`, `storage/alerts`, `storage/users`) start empty and do not require data migrations.

---

## 18. Test Coverage

Comprehensive test suite in `tests/test_watchlist_alert_foundation.py` covering all 38 required test scenarios:

| Category | Test Scenarios | Status |
|---|---|---|
| **User** | 1. Create user, 2. Retrieve user, 3. Tenant isolation | **PASS** |
| **Watchlist** | 4. Create watchlist, 5. Retrieve watchlist, 6. List user's watchlists, 7. Prevent cross-user access | **PASS** |
| **Watchlist Item** | 8. Add company, 9. Add bill, 10. Add sector, 11. Add State, 12. Add jurisdiction, 13. Reject invalid entity references, 14. Prevent duplicate watchlist items | **PASS** |
| **Alert Rule** | 15. Create rule, 16. Enable/disable rule, 17. Validate alert type, 18. Validate severity | **PASS** |
| **Alert Event** | 19. Create alert event, 20. Retrieve alert, 21. Mark read, 22. Archive, 23. Deduplication key, 24. Duplicate event detection | **PASS** |
| **Notification** | 25. Create notification, 26. Delivery state, 27. Read state | **PASS** |
| **Preferences** | 28. Create preferences, 29. Update preferences, 30. Validate digest frequency | **PASS** |
| **Serialization** | 31. Round-trip all schemas | **PASS** |
| **Security / Isolation** | 32. User A cannot retrieve User B watchlist, 33. User A cannot retrieve User B alerts, 34. Tenant A cannot retrieve Tenant B records | **PASS** |
| **Regression** | 35. Existing monitoring data unchanged, 36. Existing company intelligence unchanged, 37. Central quantitative universe unchanged, 38. State predictions remain 0 | **PASS** |

**Total Tests**: 38  
**Passed**: 38  
**Failed**: 0  

---

## 19. Security Considerations

1. **Path Traversal Protection**: Identifiers are validated to prevent directory traversal in file storage.
2. **Tenant Enclosure**: Repository operations restrict directory scanning to specific tenant folders when tenant context is supplied.
3. **Immutability of Invariants**: Firewalls prevent arbitrary external modification of production baseline files.

---

## 20. Explicit Non-Goals

1. **Alert Matching Engine**: Deferred to Task 8.13.4.
2. **Monitoring Scheduler Hook**: Deferred to Task 8.13.4.
3. **External Notification Providers** (SendGrid, Twilio, Slack webhooks): Deferred to future SaaS phases.
4. **Authentication & Session Tokens** (JWT, OAuth): Deferred.
5. **Billing & Tier Quotas**: Deferred.
6. **Frontend UI Components**: Deferred to Task 8.13.6.

---

## 21. Recommended Next Task: Task 8.13.3

**Task 8.13.3 — Watchlist Service & Inverted Indices**:
- Implement high-level `WatchlistService` providing entity existence validation across `CompanyRepository`, `BillRepository`, and `StateBillRepository`.
- Implement automated inverted index maintenance (`idx_company.json`, `idx_bill.json`, `idx_sector.json`, `idx_state.json`) for $O(1)$ subscriber resolution during monitoring runs.
