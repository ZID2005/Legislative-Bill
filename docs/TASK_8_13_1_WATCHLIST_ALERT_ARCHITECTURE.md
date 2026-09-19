# Task 8.13.1 — Watchlist & Alert Architecture Audit + System Design

**India Legislative Intelligence & Market Impact Prediction Platform**  
**Audit Date:** 2026-09-16  
**Status:** AUDIT COMPLETE — ARCHITECTURE DESIGNED — IMPLEMENTATION DEFERRED TO TASK 8.13.2+  

---

## 1. Executive Summary & Objective

### 1.1 Objective
Following the completion of Tasks 8.12.1 through 8.12.5 (Company Intelligence Universe, Evidence-Based Exposure Expansion, Sector/Industry Integration, and Groq AI Explanation Layer), the platform possesses a unified Central + State legislative intelligence base covering 70 corporate entities (47 frozen Central quantitative companies + 23 qualitative intelligence entities), 22 Central bills, 182 State bills, 86 validated State corporate exposures, and a live legislative monitoring scheduler.

The next major product capability is **Task 8.13 — Product Features + Watchlists & Alerts**.

The sole objective of **Task 8.13.1** is to:
1. Conduct a rigorous, comprehensive audit of the existing monitoring, event feed, company exposure, and discovery subsystems.
2. Design a production-grade, SaaS-compatible, multi-tenant ready architecture for **User Watchlists**, **Entity Watchlists** (Companies, Bills, Sectors, Industries, States, Jurisdictions), **Deterministic Alert Rules**, **Alert Deduplication & Aggregation**, **Explainable Severity Scoring**, **Groq AI-powered Alert Explanations**, and **Digest/Notification Delivery**.
3. Establish clean service boundaries and storage recommendations to prepare for phased implementation in Tasks 8.13.2 through 8.13.6 without modifying frozen production baselines.

### 1.2 Strict Baseline Invariants (FROZEN)
This architecture is strictly design-only. No models are retrained, no predictions created, and all production baselines remain frozen:

| Baseline Dimension | Frozen Production Requirement | Audit Verification Value | Status |
|---|---|---|---|
| Central Quantitative Companies | Exactly 47 | 47 | **FROZEN / UNCHANGED** |
| Production Central Bills | Exactly 20 | 20 | **FROZEN / UNCHANGED** |
| Central Bill-Company Pairs | Exactly 940 (20 bills × 47 companies) | 940 | **FROZEN / UNCHANGED** |
| Central Market Predictions | Exactly 4,700 (940 pairs × 5 event windows) | 4,700 | **FROZEN / UNCHANGED** |
| Validated State Corporate Exposures | Exactly 86 | 86 | **FROZEN / UNCHANGED** |
| State Stock-Market Predictions | Strictly 0 | 0 | **FROZEN / UNCHANGED** |
| Quantitative Firewall | Active (Zero predictions for Intel-only entities) | Active | **ENFORCED** |

---

## 2. Existing Monitoring Architecture Audit

The monitoring pipeline was implemented in **Task 8.11** as an automated polling and change-detection engine across Central and State legislative sources.

### 2.1 Component Inspection

```
[Official Central / State Portals]
                 │ (HTML scraping / table parsing / PDF fetch)
                 ▼
      services.monitoring.source_registry
        MonitoringSourceRegistry (10 sources: Central + 4 Implemented States)
                 │
                 ▼
      services.monitoring.scheduler
        LegislativeScheduler (Threaded background loop, lock-guarded)
                 │
                 ▼
      services.monitoring.monitoring_runner
        MonitoringRunner (Per-source error isolation, run orchestration)
                 │
        ┌────────┴──────────────────────────┐
        ▼                                   ▼
CentralMonitor                         StateMonitor
        │                                   │
        └────────┬──────────────────────────┘
                 │ (Raw bill snapshots compared)
                 ▼
      services.monitoring.change_detector
        LegislativeChangeDetector (Field-by-field deterministic diffing)
                 │
                 ▼ (Emits ChangeEvent / DocumentChangeEvent)
      services.monitoring.update_processor
        UpdateProcessor (Routes changes to repositories; preserves firewall)
                 │
                 ▼
      storage.monitoring_repository
        MonitoringRepository (Persists runs, events, and bill versions)
```

### 2.2 Core Schemas (`schemas/monitoring.py`)
- `ChangeEventType`: Enum classifying changes (`NEW_BILL`, `STATUS_CHANGED`, `METADATA_CHANGED`, `DATE_CHANGED`, `DOCUMENT_CHANGED`, `SOURCE_CHANGED`, `NO_CHANGE`, `ERROR`).
- `RunStatus`: Enum (`SUCCESS`, `PARTIAL_SUCCESS`, `FAILED`, `RUNNING`).
- `MonitoringSource`: Source descriptor with polling intervals, priority, status, and health metrics (`last_checked_at`, `last_success_at`, `last_error`).
- `ChangeEvent`: Deterministic record of a single field change:
  - `event_id`: Unique identifier (UUID).
  - `bill_id`: Bill identifier (e.g. `the-digital-personal-data-protection-bill-2023`).
  - `jurisdiction`: `"central"` or `"state"`.
  - `state`: Optional state name (e.g. `"Kerala"`).
  - `event_type`: `ChangeEventType`.
  - `field_name`: Specific changed field (e.g. `"status"`, `"pdf_sha256"`).
  - `old_value`, `new_value`: Normalized values.
  - `confidence`: Detection confidence (1.0 default).
- `DocumentChangeEvent`: Dedicated SHA-256 PDF hash comparison to distinguish true statutory text modifications from cosmetic URL changes.
- `MonitoringRun`: Auditable run record tracking sources checked, succeeded, failed, new bills, and changed bills.

### 2.3 Storage Layout (`storage/monitoring_repository.py`)
- `storage/monitoring/monitoring_runs/run_{run_id}.json`
- `storage/monitoring/change_events/event_{event_id}.json`
- `storage/monitoring/bill_versions/{bill_id}/version_{timestamp}.json`
- Deduplication: In-memory sets `_seen_event_ids` and `_seen_run_ids` backed by disk file scanning ensure idempotency.

---

## 3. Existing Notification-Event Infrastructure Audit

### 3.1 Component Inspection (`services/monitoring/notification_events.py`)
The system currently includes a basic `LegislativeEventFeed` and `NotificationEvent` schema:

- `NotificationEvent`:
  - `event_id`: String UUID matching the underlying `ChangeEvent.event_id`.
  - `event_type`: `ChangeEventType`.
  - `bill_id`, `bill_title`: Bill reference.
  - `jurisdiction`, `state`: Geographic scope.
  - `detected_at`: ISO timestamp.
  - `summary`: Human-readable change summary string.
  - `metadata`: Contains `affected_companies` (resolved via `CompanyExposureRepository.get_companies_for_bill()`) and `affected_company_count`.
- `LegislativeEventFeed`:
  - Persists JSON records to `storage/monitoring/notification_events/event_{event_id}.json`.
  - Maintains `_seen_ids` to guarantee idempotent append-only behavior.
  - Exposes `get_recent_events()` for dashboard display.

### 3.2 Pre-existing Watchlist Hooks in Master Data
In **Task 8.12.2** (`schemas/company.py`), a dedicated forward-compatible field was added to the `Company` dataclass:
```python
watchlist_eligible: bool = False
"""True if this company may be selected by users for watchlists in a future task.
False is the conservative default; eligibility must be explicitly granted."""
```

### 3.3 Critical Architectural Gap Analysis
While the current monitoring and notification event layers function reliably for system-level event capture, they do **not** provide a user-facing watchlist or alert product:

| Capability | Current System State | Required Future State (Task 8.13) |
|---|---|---|
| **Event Audience** | Global broadcast only (system-wide feed) | Multi-user / multi-tenant personalized inbox |
| **Subscription Logic** | None (all events logged globally) | User watchlists (Company, Bill, Sector, State) |
| **Alert Rules** | None (no user-defined filters) | User preferences (severity, types, channels) |
| **Notification State** | Ephemeral feed (no read/unread/archived state) | Persistent user notification inbox with read tracking |
| **Multi-Company Aggregation** | Emits a list in metadata; no consolidation | Consolidates multi-company impacts into 1 alert |
| **Deduplication** | Idempotent by `event_id` only | Contextual dedup by `(user_id, item_id, event_id)` |
| **Severity Scoring** | None (all events equal weight) | Transparent, deterministic 5-level severity model |
| **AI Explanation Delivery** | AI available on-demand in dashboard | Contextual AI summary embedded directly in alerts |
| **Delivery Channels** | None (file log only) | In-App drawer (8.13) + Email/Push/Webhook (SaaS) |

---

## 4. Core Product Objects Design

To support a scalable, SaaS-compatible product layer without premature complexity, we define the following core entities:

```
┌─────────────────────────────────────────────────────────────┐
│                         Tenant / Org                        │
│                 (Default: "default_tenant")                 │
└──────────────────────────────┬──────────────────────────────┘
                               │ 1:N
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                             User                            │
│                  (Default: "default_user")                  │
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
└───────────────┘                             │  Notification  │
                                              │  (Deliveries)  │
                                              └────────────────┘
```

### 4.1 Schema Definitions

#### A. `User` (Identity Abstraction)
```python
@dataclass
class User:
    user_id: str
    tenant_id: str = "default_tenant"
    email: str = ""
    display_name: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True
```

#### B. `Watchlist` (User Collection)
```python
@dataclass
class Watchlist:
    watchlist_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    name: str = "Default Watchlist"
    description: Optional[str] = None
    is_default: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    item_count: int = 0
    is_active: bool = True
```

#### C. `WatchlistItem` (Entity Reference)
```python
class WatchlistEntityType(str, Enum):
    COMPANY = "COMPANY"
    BILL = "BILL"
    SECTOR = "SECTOR"
    INDUSTRY = "INDUSTRY"
    STATE = "STATE"
    JURISDICTION = "JURISDICTION"

@dataclass
class WatchlistItem:
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    watchlist_id: str = ""
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    entity_type: WatchlistEntityType = WatchlistEntityType.COMPANY
    entity_id: str = ""          # Stable ID: ISIN, bill_id, canonical sector slug, normalized state name
    entity_name: str = ""        # Cached display name
    added_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: Optional[str] = None
    custom_tags: list[str] = field(default_factory=list)
    is_active: bool = True
```

#### D. `AlertRule` (Subscription Filter)
```python
@dataclass
class AlertRule:
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    watchlist_id: Optional[str] = None   # None = applies across all user watchlists
    alert_types: list[str] = field(default_factory=list)  # Empty = all types
    min_severity: str = "LOW"            # INFO, LOW, MEDIUM, HIGH, CRITICAL
    jurisdictions: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    channels: list[str] = field(default_factory=lambda: ["IN_APP"])
    is_enabled: bool = True
```

#### E. `AlertEvent` (User Alert Inbox Item)
```python
class AlertSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class AlertEvent:
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dedup_key: str = ""                  # SHA-256 hash preventing duplicate generation
    event_id: str = ""                   # Upstream ChangeEvent.event_id
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    watchlist_id: str = ""
    watchlist_item_id: Optional[str] = None
    alert_type: str = "BILL_STATUS_CHANGE"
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str = ""
    summary: str = ""
    entity_type: WatchlistEntityType = WatchlistEntityType.COMPANY
    entity_id: str = ""
    bill_id: str = ""
    company_ids: list[str] = field(default_factory=list)
    sector: Optional[str] = None
    state: Optional[str] = None
    jurisdiction: str = "central"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    read_at: Optional[str] = None
    is_read: bool = False
    is_archived: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
```

#### F. `Notification` (Delivery Record)
```python
class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    WEBHOOK = "WEBHOOK"

class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    SUPPRESSED = "SUPPRESSED"

@dataclass
class Notification:
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_id: str = ""
    user_id: str = "default_user"
    channel: NotificationChannel = NotificationChannel.IN_APP
    status: NotificationStatus = NotificationStatus.DELIVERED
    delivered_at: Optional[str] = None
    error_message: Optional[str] = None
    payload: dict[str, Any] = field(default_factory=dict)
```

#### G. `AlertPreference` (User Configuration)
```python
class DeliveryFrequency(str, Enum):
    REAL_TIME = "REAL_TIME"
    DAILY_DIGEST = "DAILY_DIGEST"
    WEEKLY_DIGEST = "WEEKLY_DIGEST"

@dataclass
class AlertPreference:
    preference_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    delivery_frequency: DeliveryFrequency = DeliveryFrequency.REAL_TIME
    min_severity: AlertSeverity = AlertSeverity.LOW
    channels_enabled: list[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.IN_APP])
    email_address: Optional[str] = None
    webhook_url: Optional[str] = None
    quiet_hours_enabled: bool = False
    quiet_hours_start_utc: int = 16       # 21:30 IST
    quiet_hours_end_utc: int = 1          # 06:30 IST
```

---

## 5. Watchlist Types & Phased Roadmap

To maintain clean scoping, watchlist capabilities are partitioned into distinct implementation phases:

| Watchlist Entity Type | Supported in 8.13? | Identification Mechanism | Example Entity | Data Validation Store |
|---|---|---|---|---|
| **COMPANY** | **YES (Core)** | Canonical `company_id` / ISIN | `PRIV-BUNDL-SWIGGY`, `INE009A01021` | `CompanyRepository` |
| **BILL** | **YES (Core)** | Canonical `bill_id` | `the-digital-personal-data-protection-bill-2023` | `BillRepository`, `StateBillRepository` |
| **SECTOR** | **YES (Core)** | Canonical Sector Slug | `Technology`, `Banking & Financial Services` | `_EXPLORE_CATEGORY_MAPPINGS` |
| **STATE** | **YES (Core)** | Normalized State Name | `Kerala`, `Karnataka`, `Telangana` | `state_normalizer` / `StateCoverage` |
| **JURISDICTION** | **YES (Core)** | Jurisdiction Enum | `central`, `state` | Core System Taxonomy |
| **INDUSTRY** | Phase 2 (Later SaaS) | Sub-industry classification | `Food Delivery & Quick Commerce` | Granular Corporate Taxonomy |
| **CUSTOM QUERY** | Phase 3 (Enterprise) | Saved search boolean DSL | `sector:Energy AND state:Telangana` | Discovery Service Engine |

---

## 6. Watchlist Item Design & Reference Stability

### 6.1 Avoiding Fragile String References
A critical architectural pitfall in watchlist systems is storing unvalidated display strings (e.g. `"Swiggy"`, `"The DPDP Bill"`). If names are updated, localized, or hyphenated differently, matching breaks.

All `WatchlistItem` records **must** enforce stable, validated primary identifiers:

```
User Input ("Swiggy")
         │
         ▼
CompanyExposureRepository.resolve_company_identifier()
         │
         ▼
Canonical Company ID: "PRIV-BUNDL-SWIGGY" (Verified in CompanyRepository)
         │
         ▼
WatchlistItem.entity_id = "PRIV-BUNDL-SWIGGY"
WatchlistItem.entity_name = "Swiggy Limited" (Cached snapshot)
```

### 6.2 Primary Key Reference Guarantees
1. **Companies**: Validated against `CompanyRepository.exists(isin)` or alias resolver. Unrecognized entities cannot be added.
2. **Bills**: Validated against `UnifiedLegislativeDiscoveryService.get_bill_by_id(bill_id)`. Non-existent bill IDs are rejected.
3. **States**: Normalized via `utils.state_normalizer.normalize_state()`.
4. **Sectors**: Matched against canonical sector taxonomy keys.

---

## 7. Alert Taxonomy & Boundary Firewall

### 7.1 Comprehensive Alert Taxonomy

| Category | Alert Type | Trigger Condition | Severity Default |
|---|---|---|---|
| **Legislative** | `NEW_BILL` | New bill detected in Central Parliament or State Assembly | `HIGH` |
| **Legislative** | `BILL_STATUS_CHANGE` | Legislative lifecycle advancement (e.g. Passed, Assented) | `HIGH` / `CRITICAL` |
| **Legislative** | `BILL_VERSION_CHANGE` | New draft, amendments, or committee report published | `MEDIUM` |
| **Legislative** | `BILL_DOCUMENT_CHANGE` | Official PDF text/content hash updated (SHA-256 diff) | `MEDIUM` |
| **Legislative** | `BILL_METADATA_CHANGE` | Date update, ministry reassignment, session detail | `LOW` |
| **Corporate** | `NEW_COMPANY_EXPOSURE` | Corporate entity newly linked to bill with verified evidence | `HIGH` |
| **Corporate** | `EXPOSURE_CHANGE` | Exposure strength, direction, or statutory mechanism updated | `MEDIUM` |
| **Sector** | `SECTOR_IMPACT` | Legislative change affecting multiple companies in a sector | `HIGH` |
| **Jurisdiction** | `STATE_IMPACT` | Major statutory or regulatory action within a watched State | `MEDIUM` |
| **System** | `LEGISLATIVE_MONITORING_CHANGE` | Source adapter status change, portal downtime notice | `INFO` |

### 7.2 Strict Boundary Firewall Against Quantitative Predictions
The platform maintains a strict boundary:
1. **State Bills**: **Zero stock-market predictions.** State bills must **NEVER** produce `PREDICTION_UPDATE` or price target alerts.
2. **Intelligence-Only Companies**: Entities such as Swiggy, Flipkart, BSNL, KSEB belong to the intelligence universe and are firewalled. They must **NEVER** receive stock price prediction or abnormal return alerts.
3. **Central Quantitative Companies**: For the 47 frozen Central companies, quantitative decision updates may occur in future tasks, but are **FROZEN** in 8.13.

```python
def validate_alert_firewall(alert_type: str, jurisdiction: str, universe_type: str) -> None:
    """Enforce strict quantitative firewall at the alert generation boundary."""
    if alert_type in ("PREDICTION_UPDATE", "RISK_UPDATE", "ANTICIPATION_UPDATE"):
        if jurisdiction.lower() == "state":
            raise ValueError("FIREWALL VIOLATION: State bills cannot receive quantitative prediction alerts.")
        if universe_type.lower() == "intelligence":
            raise ValueError("FIREWALL VIOLATION: Intelligence-only companies cannot receive prediction alerts.")
```

---

## 8. Trigger & Matching Architecture

### 8.1 End-to-End Reactive Event Flow
The watchlist and alert engine consumes events produced by the existing monitoring scheduler without duplicating source polling:

```
                    [Official Portals]
                            │
                            ▼
              services.monitoring.scheduler
                (Runs polling cycle)
                            │
                            ▼
              services.monitoring.change_detector
                (Produces ChangeEvent)
                            │
                            ▼
              services.monitoring.update_processor
                (Applies safe data updates)
                            │
                            ▼
              services.watchlist.alert_matching_engine
                (Consumes ChangeEvent / NotificationEvent)
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
     Bill Watchlists  Company Matches  Sector Matches
     (Direct Match)   (Exposure Graph) (Taxonomy Match)
           │                │                │
           └────────────────┼────────────────┘
                            │
                            ▼
              services.watchlist.alert_aggregation_service
                (Compresses bursts: 1 bill -> 5 companies)
                            │
                            ▼
              services.watchlist.alert_deduplication_service
                (Verifies dedup_key against sliding window)
                            │
                            ▼
              storage.alert_repository
                (Persists AlertEvent to User Inbox)
                            │
                            ▼
              services.notification.notification_service
                (Dispatches In-App / Digest Delivery)
                            │
                            ▼
              services.ai.ai_explanation_service
                (On-demand Groq explanation generation)
```

---

## 9. Matching Engine & Inverted Indices

To evaluate incoming events against thousands of user watchlists in $O(1)$ time, the architecture uses **Inverted Indices**:

### 9.1 Inverted Index Structure
```
storage/watchlists/indices/
  ├── idx_company.json      # company_id -> [ {user_id, watchlist_id, item_id}, ... ]
  ├── idx_bill.json         # bill_id    -> [ {user_id, watchlist_id, item_id}, ... ]
  ├── idx_sector.json       # sector     -> [ {user_id, watchlist_id, item_id}, ... ]
  └── idx_state.json        # state      -> [ {user_id, watchlist_id, item_id}, ... ]
```

### 9.2 Step-by-Step Resolution Algorithm
When an event arrives: `ChangeEvent(bill_id="kl-gig-workers-2024", event_type=STATUS_CHANGED)`:
1. **Direct Bill Matching**:
   - Query `idx_bill["kl-gig-workers-2024"]`.
   - Result: Users watching this specific bill directly receive `BILL_STATUS_CHANGE`.
2. **Company Exposure Resolution**:
   - Call `CompanyExposureRepository.get_companies_for_bill("kl-gig-workers-2024")`.
   - Returns exposed entities: `["PRIV-BUNDL-SWIGGY", "INE758T01015"]` (Swiggy, Zomato).
   - For each exposed company, query `idx_company[company_id]`.
   - Result: Users watching Swiggy or Zomato match for corporate alerts.
3. **Sector Matching**:
   - Identify bill sectors from `UnifiedBillRecord`: `["Labour, Employment & Skills"]`.
   - Query `idx_sector["Labour, Employment & Skills"]`.
   - Result: Users watching this sector match for sector alerts.
4. **State Matching**:
   - Identify bill state: `"Kerala"`.
   - Query `idx_state["Kerala"]`.
   - Result: Users watching the State of Kerala match.

---

## 10. Company Watchlist Logic

### 10.1 Grounded Trigger Requirement
The system **never** alerts simply because a company exists. Alerts require a verified, authoritative triggering event linked through the corporate exposure graph:

```
[User Watches Swiggy (PRIV-BUNDL-SWIGGY)]
                      │
                      ▼
[Legislative Change Event Detected]
  Bill: "The Kerala Gig Workers Welfare Bill, 2024"
  Event: STATUS_CHANGED (Passed Assembly)
                      │
                      ▼
[Corporate Exposure Repository Lookup]
  Query: get_companies_for_bill("kl-gig-workers-2024")
  Match: PRIV-BUNDL-SWIGGY found!
  Evidence: Section 4 platform registration requirement
  Directness: DIRECT | Strength: HIGH | Mechanism: compliance
                      │
                      ▼
[Watchlist Match Confirmed]
  Emit Alert: "Legislative Advance: Kerala Gig Workers Bill impacts Swiggy"
```

### 10.2 Alias and Corporate Identity Resilience
Users might search or refer to companies using various colloquial names. The matching service normalizes all queries through the canonical `_COMPANY_ALIAS_MAP`:
- `"Swiggy"`, `"Bundl"`, `"Bundl Technologies"`, `"INE00H001014"` $\rightarrow$ `PRIV-BUNDL-SWIGGY`
- `"Zomato"`, `"Eternal Limited"`, `"ZOMATO"` $\rightarrow$ `INE758T01015`
- `"Adani Ports"`, `"APSEZ"` $\rightarrow$ `INE742F01042`
- `"KSEB"`, `"Kerala State Electricity Board"` $\rightarrow$ `UNLISTED-KL-KSEB`

---

## 11. Bill Watchlist Logic

Users watching specific bills (e.g. `the-finance-bill-2024` or `dpdp-2023`) receive granular lifecycle tracking:

- **Status Transitions**: `introduced` $\rightarrow$ `referred_to_committee` $\rightarrow$ `passed_first_house` $\rightarrow$ `passed_both_houses` $\rightarrow$ `assented` $\rightarrow$ `enacted`.
- **Document Versioning**: Detection of official gazette PDF modifications via SHA-256 diff.
- **Date Changes**: Authoritative introduction, passage, or assent date updates.
- **Committee & Sponsor Changes**: Ministry or parliamentary committee reporting updates.

Every alert links directly to the bill's version snapshot history in `storage/monitoring/bill_versions/{bill_id}/`.

---

## 12. Sector / Industry Watchlist Logic

### 12.1 Sector Scope
Sector watchlists track broader macroeconomic and regulatory shifts:
- `Technology & Digital Platforms`
- `Banking & Financial Services`
- `Energy & Power Generation`
- `Transport & Logistics`
- `Healthcare & Pharmaceuticals`

### 12.2 Multi-Company Noise Suppression
When a legislative bill impacts an entire sector (e.g. the Central Telecommunications Act impacts 10 telecom entities), generating 10 separate notifications for a sector watcher creates alert fatigue.

The sector matching engine enforces **Sector Aggregation**:
- Consolidates all exposed companies into a single **Sector Impact Alert**.
- Headline: *"New Legislation in Telecommunications: Telecommunications Act, 2023 affecting 4 sector entities (Airtel, Vodafone Idea, BSNL, Indus Towers)"*.
- Provides expandable exposure details per entity.

---

## 13. State / Jurisdiction Watchlist Logic

Users can subscribe to legislative streams for:
- Specific States: `Kerala`, `Karnataka`, `Andhra Pradesh`, `Telangana` (active pilot states).
- Planned States: Transparent coverage notices when newly implemented.
- Jurisdiction: `Central Government` or `All States`.

### 13.1 State Presence Validation
Corporate alerts generated from State bills require verified operational presence in that State. For example:
- A Kerala electricity bill alerts on KSEB or companies with verified Kerala operations (`StatePresenceRecord.state == "Kerala"`).
- It will **not** trigger false alerts on companies with zero Kerala footprint.

---

## 14. Deterministic Severity Scoring Model

The severity model is **transparent, explainable, and deterministic**. It is based strictly on statutory and operational factors, with **zero political or ideological scoring**.

### 14.1 Scoring Formula

$$\text{Severity Score} = W_{\text{event}} + W_{\text{strength}} + W_{\text{directness}} + W_{\text{status}} + W_{\text{relevance}}$$

### 14.2 Weight Coefficients

| Dimension | Attribute Value | Weight Points |
|---|---|---|
| **Event Type ($W_{\text{event}}$)** | `BILL_STATUS_CHANGE` (to Assented/Enacted) | 8 |
| | `NEW_BILL` | 6 |
| | `BILL_STATUS_CHANGE` (Committee / House Passage) | 5 |
| | `NEW_COMPANY_EXPOSURE` | 5 |
| | `DOCUMENT_CHANGED` (Content SHA-256 modified) | 4 |
| | `EXPOSURE_CHANGE` | 4 |
| | `METADATA_CHANGED` / `DATE_CHANGED` | 2 |
| | `SOURCE_CHANGED` | 1 |
| **Exposure Strength ($W_{\text{strength}}$)** | `HIGH` | 5 |
| | `MEDIUM` | 3 |
| | `LOW` | 1 |
| | `UNKNOWN` / `NONE` | 0 |
| **Directness ($W_{\text{directness}}$)** | `DIRECT` statutory exposure | 4 |
| | `INDIRECT` supply chain / market exposure | 2 |
| | `NONE` | 0 |
| **Bill Status ($W_{\text{status}}$)** | `assented` / `enacted` / `passed` | 4 |
| | `introduced` / `pending` | 2 |
| | `lapsed` / `withdrawn` | 1 |
| **Market Relevance ($W_{\text{relevance}}$)** | `HIGH` | 4 |
| | `MEDIUM` | 2 |
| | `LOW` | 1 |
| | `NONE` / `UNKNOWN` | 0 |

### 14.3 Score Mapping to Severity Levels

| Total Score Range | Severity Level | UI Badge | Notification Behavior |
|---|---|---|---|
| **$\ge 22$ points** | `CRITICAL` | 🔴 Red | Immediate in-app banner; instant alert |
| **$16 - 21$ points** | `HIGH` | 🟠 Orange | Prominent in-app alert; included in priority digest |
| **$10 - 15$ points** | `MEDIUM` | 🟡 Yellow | Standard alert feed item; regular digest |
| **$5 - 9$ points** | `LOW` | 🔵 Blue | Low-priority badge; quiet feed entry |
| **$< 5$ points** | `INFO` | ⚪ Gray | Informational note; suppressed from digests |

---

## 15. Alert Deduplication Engine

To eliminate repeated alerts from scheduler retries, re-scrapes, or source quirks, the system implements deterministic deduplication.

### 15.1 Deduplication Hash Key

$$\text{dedup\_key} = \text{SHA-256}(\text{user\_id} \mathbin{\Vert} \text{watchlist\_id} \mathbin{\Vert} \text{event\_id} \mathbin{\Vert} \text{alert\_type})$$

### 15.2 Deduplication Rules
1. **Event Identity**: If an `AlertEvent` with the same `dedup_key` exists in `storage/alerts/dedup/dedup_index.json`, the duplicate is silently discarded.
2. **Sliding Window**: Dedup keys are retained for a 72-hour sliding window.
3. **Bill Version Suppressor**: A `DOCUMENT_CHANGED` event is only emitted if the PDF SHA-256 hash genuinely differs from the last stored version.
4. **Retry Safety**: Monitoring scheduler retries or failed source recovery runs cannot re-trigger previously delivered user alerts.

---

## 16. Alert Aggregation Engine

### 16.1 Multi-Entity Consolidation
When a single bill impacts multiple entities watched by the same user, sending $N$ separate alerts clutters the feed.

The `AlertAggregationService` batches incoming alerts during a scheduler run window (e.g. 5 minutes):

```
Incoming Matches for User "U-101" from Bill "DPDP-2023":
  - Match: Swiggy (Watched Company)
  - Match: Zomato (Watched Company)
  - Match: Infosys (Watched Company)
  - Match: Technology (Watched Sector)
                     │
                     ▼
          [Alert Aggregation Engine]
                     │
                     ▼
           Single Consolidated Alert:
  Title: "Digital Personal Data Protection Bill impacts 3 watched companies & 1 watched sector"
  Severity: HIGH
  Sub-records:
    • Swiggy: Direct regulatory compliance (Section 6 consent manager)
    • Zomato: Direct regulatory compliance (Section 6 consent manager)
    • Infosys: Direct data fiduciary requirements (Section 8 obligations)
    • Sector: Technology & Digital Platforms
```

Users can click the consolidated alert to expand individual entity dossiers.

---

## 17. Groq AI Alert Explanation Layer

The platform’s Groq AI integration (`services/ai/ai_context_builder.py` and `services/ai/ai_explanation_service.py`) is extended conceptually to provide natural-language alert synthesis.

### 17.1 Grounding Invariants
1. **Zero Hallucination**: Context is assembled strictly from verified records (`ChangeEvent`, `CompanyExposureRecord`, `UnifiedBillRecord`).
2. **No Speculative Market Tips**: The AI must not invent stock return predictions, price targets, or trading recommendations.
3. **Four-Part Categorical Output**:
   - `[FACTS]`: Official legislative change details.
   - `[DERIVED]`: Verified sector and statutory exposure links.
   - `[ECONOMIC INTERPRETATION]`: Operational compliance and business implications.
   - `[PREDICTIONS]`: Explicitly stated as unavailable for State bills and intelligence-only companies.

### 17.2 AI Explanation Template
```markdown
### 🤖 AI Alert Dossier: What Changed & Why It Matters

**What Changed:**
On 2026-09-16, the State of Kerala published an amended draft of the Kerala Gig Workers Welfare Bill, introducing a revised statutory dispute resolution mechanism (Section 12).

**Relevance to Watched Company (Swiggy):**
Swiggy has verified operational presence in Kerala across food delivery and quick commerce (Instamart). The statute establishes platform registration requirements and mandatory welfare board contributions.

**Authoritative Statutory Evidence:**
• Section 4(1): Mandatory aggregation of gig worker registries.
• Section 8(2): Transaction-level welfare fee allocation.

**Analytical Boundary Note:**
This entity belongs to the Company Intelligence universe. Financial market return models are strictly firewalled (0 predictions).
```

---

## 18. Notification Channels & Delivery Strategy

### 18.1 Channel Architecture

```
                 AlertEvent Generated
                          │
                          ▼
            NotificationDeliveryService
                          │
     ┌────────────────────┼────────────────────┐
     ▼                    ▼                    ▼
In-App Channel       Email Channel      Webhook Channel
(Task 8.13 Core)     (Phase 2 SaaS)     (Phase 3 Enterprise)
  • Badge Count        • Daily Digest     • Slack App
  • Dropdown Feed      • Weekly Rollup    • Teams Webhook
  • Alert Inbox        • Instant Urgent   • Custom REST API
```

### 18.2 Phase 1 (Task 8.13 Scope): In-App First
- Primary focus is the **In-App Notification Center**:
  - Unread badge counter in the navigation bar.
  - Dedicated `/alerts` page with unread filtering, category tabs, and search.
  - Interactive "Mark as Read" and "Archive" actions.
- External delivery (SendGrid email, Push notifications) is architected via standard abstract adapters (`NotificationChannelAdapter`), with stub implementations for Task 8.13.

---

## 19. User Preferences & Digest Strategy

### 19.1 Separation of Event Detection and Notification Delivery
A core architectural principle is decoupling:
- **Event Detection**: Driven by the monitoring scheduler (polling every 24h for Central, 48h for State, or manual trigger).
- **Notification Delivery**: Driven by user cadence preferences:
  - `REAL_TIME`: In-app notification created immediately upon event detection.
  - `DAILY_DIGEST`: Events queued and aggregated into a single morning briefing (08:00 IST).
  - `WEEKLY_DIGEST`: Events queued for Monday morning executive brief.

### 19.2 Digest Compilation Algorithm
1. Query un-notified alerts for user within digest window.
2. Group by:
   - Watched Companies (with statutory changes)
   - Watched Bills (with lifecycle advances)
   - Watched Sectors & States
3. Highlight highest severity alert (`CRITICAL` / `HIGH`).
4. Generate structured markdown summary with deep-links to platform pages.

---

## 20. Watchlist Safety Limits

To safeguard system performance and prevent abuse in future multi-tenant deployments:

| Resource | Free Tier Limit | Pro / SaaS Tier Limit | Enterprise Tier Limit |
|---|---|---|---|
| Watchlists per User | 3 | 25 | Unlimited |
| Items per Watchlist | 20 | 250 | Unlimited |
| Daily Alert Volume Cap | 50 alerts/day | 500 alerts/day | Unlimited |
| Dedup Retention Window | 72 hours | 30 days | 90 days |
| Alert History Retention | 30 days | 1 year | 7 years (Audit compliance) |

---

## 21. Storage Architecture Recommendation

### 21.1 Storage Hierarchy
The existing filesystem storage in `storage/` is extended cleanly:

```
storage/
  ├── monitoring/              # (Existing Task 8.11 monitoring storage)
  │   ├── monitoring_runs/
  │   ├── change_events/
  │   ├── bill_versions/
  │   └── notification_events/ # (System-wide event feed)
  │
  ├── watchlists/              # (New Task 8.13 watchlist storage)
  │   ├── users/
  │   │   └── {tenant_id}/
  │   │       └── {user_id}/
  │   │           ├── profile.json
  │   │           ├── preferences.json
  │   │           └── watchlists/
  │   │               ├── {watchlist_id_1}.json
  │   │               └── {watchlist_id_2}.json
  │   └── indices/             # (Inverted matching indices)
  │       ├── idx_company.json
  │       ├── idx_bill.json
  │       ├── idx_sector.json
  │       └── idx_state.json
  │
  └── alerts/                  # (New Task 8.13 alert storage)
      ├── inbox/
      │   └── {tenant_id}/
      │       └── {user_id}/
      │           ├── unread_alerts.json
      │           └── alert_history_{YYYY_MM}.json
      ├── events/              # (Raw alert event records)
      │   └── {YYYY}/{MM}/
      │       └── alert_{alert_id}.json
      └── dedup/
          └── dedup_index.json # (Sliding window hash table)
```

### 21.2 Future SQL / Database Schema Mapping
When migrating from local JSON storage to Supabase / PostgreSQL in the SaaS phase:
- `watchlists` table: `id (UUID), tenant_id (UUID), user_id (UUID), name (TEXT), is_default (BOOL), created_at (TIMESTAMPTZ)`
- `watchlist_items` table: `id (UUID), watchlist_id (UUID), entity_type (TEXT), entity_id (TEXT), added_at (TIMESTAMPTZ)`
- `alert_events` table: `id (UUID), tenant_id (UUID), user_id (UUID), event_id (TEXT), alert_type (TEXT), severity (TEXT), is_read (BOOL)`
- `alert_dedup` table: `dedup_key (TEXT PRIMARY KEY), created_at (TIMESTAMPTZ)`

---

## 22. Service Boundaries & Interface Contracts

```
┌─────────────────────────────────────────────────────────────┐
│                       WatchlistService                      │
│  - create_watchlist(user_id, name)                          │
│  - add_item(watchlist_id, entity_type, entity_id)           │
│  - remove_item(watchlist_id, item_id)                       │
│  - get_user_watchlists(user_id)                             │
│  - rebuild_inverted_indices()                               │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      AlertMatchingEngine                    │
│  - process_change_event(change_event: ChangeEvent)          │
│  - match_subscribers(entity_type, entity_id)                │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 AlertAggregationService                     │
│  - aggregate_burst(matches: list[MatchResult])              │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                AlertDeduplicationService                    │
│  - is_duplicate(dedup_key: str) -> bool                     │
│  - record_alert(dedup_key: str)                             │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      AlertInboxService                      │
│  - get_user_alerts(user_id, unread_only, limit)             │
│  - mark_as_read(alert_id, user_id)                          │
│  - mark_all_as_read(user_id)                                │
│  - archive_alert(alert_id, user_id)                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 NotificationDeliveryService                 │
│  - deliver(alert: AlertEvent)                               │
│  - send_digest(user_id, frequency)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 23. SaaS / Multi-Tenancy & Data Isolation

1. **Tenant Separation**: Every record includes `tenant_id` and `user_id`. Queries in repositories enforce tenant scoping.
2. **Local Fallback**: In the single-user local Streamlit environment, `tenant_id = "default_tenant"` and `user_id = "default_user"`. This ensures 100% immediate usability while guaranteeing zero code rewrites when multi-user authentication is attached.
3. **Data Privacy**: Custom user notes, watchlist names, alert history, and unread statuses are isolated strictly to the owning user. No user can view another user's watch preferences.

---

## 24. Future Frontend Requirements

### 24.1 Streamlit Pages (Task 8.13 Scope)
1. **Watchlists Management Page (`/watchlists`)**:
   - Tabbed view of user watchlists.
   - Add/remove entities with auto-complete lookup.
   - Filter by entity type: Companies, Bills, Sectors, States.
   - Quick statistics: total items, active alerts, last trigger.
2. **Alerts Center Page (`/alerts`)**:
   - Filterable inbox: All, Unread, Critical, Watched Companies, Watched Bills.
   - Severity badges (Red, Orange, Yellow, Blue, Gray).
   - "Mark as Read", "Archive", and "Open AI Explanation" actions.
3. **Contextual Action Buttons**:
   - `Company Detail Page`: Add `[⭐ Add to Watchlist]` button.
   - `Bill Intelligence / State Dossier`: Add `[🔔 Watch this Bill]` button.
   - `Explore India`: Add `[📢 Watch Sector]` / `[🏛️ Watch State]` button.

### 24.2 Future SaaS Frontend (Next.js Roadmap)
- Navigation top-bar with notification bell icon and animated unread badge.
- Floating notification popover drawer for real-time alerts.
- Dedicated `/settings/notifications` page for channel and digest configuration.

---

## 25. Implementation Roadmap for Tasks 8.13.2+

| Sub-task | Title | Deliverables |
|---|---|---|
| **Task 8.13.2** | Schemas & Repositories Foundation | Create `schemas/watchlist.py`, `schemas/alert.py`, `storage/watchlist_repository.py`, `storage/alert_repository.py`. |
| **Task 8.13.3** | Watchlist Service & Inverted Indices | Build `WatchlistService`, entity existence validation, and automatic inverted index maintenance. |
| **Task 8.13.4** | Alert Engine & Monitoring Integration | Implement `AlertMatchingEngine`, `AlertDeduplicationService`, `AlertAggregationService`, and hook into `MonitoringRunner`. |
| **Task 8.13.5** | AI Alert Synthesis & Digest Delivery | Build Groq-powered alert explanations, `AlertInboxService`, and digest generator. |
| **Task 8.13.6** | Dashboard UI & End-to-End Test Suite | Implement Streamlit Watchlists and Alerts pages; add 20+ comprehensive pytest scenarios; verify baselines. |

---

## 26. Explicit Non-Goals

This task must **NOT**:
1. Implement the complete watchlist/alert system yet (strictly design/audit).
2. Implement user authentication, login screens, or JWT tokens.
3. Integrate third-party email providers (SendGrid, AWS SES) or SMS/WhatsApp APIs.
4. Build payment, billing, or subscription tier gates.
5. Migrate Streamlit to Next.js.
6. Retrain ML models or generate new stock-market predictions.
7. Assign political or ideological importance rankings to bills.
8. Create stock-market predictions for State bills or intelligence-only companies.

---

## 27. Baseline Verification Report

All frozen baseline counts have been verified in the local environment:

| System Metric | Baseline Expectation | Verified Actual Value | Status |
|---|---|---|---|
| `TOTAL_COMPANIES` | 70 | 70 | **PASS** |
| `CENTRAL_QUANTITATIVE_COMPANIES` | 47 | 47 | **PASS** |
| `PRODUCTION_CENTRAL_BILLS` | 20 | 20 | **PASS** |
| `CENTRAL_BILL_COMPANY_PAIRS` | 940 | 940 | **PASS** |
| `CENTRAL_PREDICTIONS` | 4,700 | 4,700 | **PASS** |
| `STATE_EXPOSURES` | 86 | 86 | **PASS** |
| `STATE_PREDICTIONS` | 0 | 0 | **PASS** |
| `CENTRAL_BASELINE_CHANGED` | false | false | **PASS** |
| `TESTS_RUN` | 144 | 144 | **PASS** |
| `TESTS_PASSED` | 141 (3 skipped) | 141 (3 skipped) | **PASS** |
| `TESTS_FAILED` | 0 | 0 | **PASS** |
