# Task 8.11 — Legislative Monitoring System Documentation

## Overview

The Legislative Monitoring & Automatic Update Scheduler is a backend system that
periodically checks official Indian legislative sources, detects new bills and
meaningful changes, and updates the knowledge/discovery layer without touching
frozen production data.

**Task 8.11 is additive only.** All existing Central predictions, backtesting,
training datasets, state predictions, and existing baselines are frozen and
protected by explicit guards in the update processor.

---

## Architecture

```
SCHEDULER (LegislativeScheduler)
    │
    ▼
SOURCE REGISTRY (MonitoringSourceRegistry)
    │
    ├── Central Sources: Lok Sabha, Rajya Sabha, PRS
    └── State Sources: AP, Karnataka, Kerala, Telangana
    │
    ▼
MONITORS (BaseMonitor subclasses)
    ├── CentralMonitor
    └── StateMonitor (×4 pilot states)
    │
    ▼
CHANGE DETECTOR (LegislativeChangeDetector)
    │
    ▼
DEDUPLICATION (MonitoringRepository.event_exists)
    │
    ▼
UPDATE PROCESSOR (UpdateProcessor)
    ├── NEW_BILL → knowledge extraction queued → discovery update
    └── CHANGED_BILL → field-level patch → audit trail → version record
    │
    ▼
NOTIFICATION EVENT FEED (LegislativeEventFeed)
    │
    ▼
MONITORING REPOSITORY (MonitoringRepository)
    ├── storage/monitoring/monitoring_runs/
    ├── storage/monitoring/change_events/
    └── storage/monitoring/bill_versions/
```

---

## Source Registry

### Configuration File
`config/monitoring_sources.json` — Unified monitoring source registry.

Fields per source:
| Field | Description |
|---|---|
| `source_id` | Unique identifier |
| `jurisdiction` | `"central"` or `"state"` |
| `state` | State name (null for Central) |
| `source_name` | Human-readable name |
| `source_url` | Official listing URL |
| `adapter` | Adapter class identifier |
| `enabled` | Whether this source is polled |
| `polling_interval_hours` | How often to check (hours) |
| `priority` | Execution order |
| `source_type` | `html_table`, `session_list`, `portal` |
| `status` | `IMPLEMENTED` or `NOT_IMPLEMENTED` |
| `last_checked_at` | Last check timestamp (UTC) |
| `last_success_at` | Last successful check timestamp |
| `last_error_at` | Last error timestamp |
| `last_error` | Last error message |

### Enabled Sources (Currently Monitored)
| Source ID | Jurisdiction | Status |
|---|---|---|
| `central_lok_sabha` | Central | IMPLEMENTED |
| `central_rajya_sabha` | Central | IMPLEMENTED |
| `central_prs` | Central | IMPLEMENTED |
| `state_andhra_pradesh` | State | IMPLEMENTED |
| `state_karnataka` | State | IMPLEMENTED |
| `state_kerala` | State | IMPLEMENTED |
| `state_telangana` | State | IMPLEMENTED |

All other states: `enabled: false`, `status: NOT_IMPLEMENTED` (PLANNED)

---

## Scheduler

### Environment Configuration
```bash
LEGISLATIVE_MONITOR_ENABLED=false    # Master switch (default: disabled)
CENTRAL_MONITOR_INTERVAL=24          # Hours between Central checks
STATE_MONITOR_INTERVAL=48            # Hours between State checks
MONITOR_MAX_RETRIES=3                # Retries per source
MONITOR_TIMEOUT=60                   # Seconds per source
```

### Manual Trigger
```python
from services.monitoring.scheduler import LegislativeScheduler

scheduler = LegislativeScheduler()
result = scheduler.run_now(trigger="manual")
print(result)
```

### Background Scheduling
```python
scheduler = LegislativeScheduler()
scheduler.start()   # Starts background thread (only if LEGISLATIVE_MONITOR_ENABLED=true)
# ... application runs ...
scheduler.stop()    # Graceful shutdown
```

---

## Adapters

### BaseMonitor
All monitors extend `BaseMonitor` which provides:
- Retry logic with exponential backoff (max 3 attempts by default)
- Error isolation (exceptions caught, returned as ERROR events)
- Consistent `MonitorResult` wrapping

### CentralMonitor
- Reads from `BillRepository` as the "known" baseline
- Compares against injected source snapshot or performs self-check
- Detects: new bill, status change, metadata change, date change, PDF hash change
- **NEVER modifies training data, predictions, or backtesting records**

### StateMonitor
- Reads from `StateKnowledgeRepository` as the "known" baseline
- Wraps existing AP, Karnataka, Kerala, Telangana adapters
- **NEVER creates state market predictions**

---

## Change Detection

The `LegislativeChangeDetector` performs deterministic, field-by-field comparison.

### Detected Fields
| Field | Event Type |
|---|---|
| `status` | STATUS_CHANGED |
| `introduction_date`, `passage_date`, `assent_date` | DATE_CHANGED |
| `pdf_url`, `pdf_sha256`, `document_url` | DOCUMENT_CHANGED |
| `source_url` | SOURCE_CHANGED |
| `title`, `bill_number`, `house`, etc. | METADATA_CHANGED |

### PDF Change Detection
- Uses **SHA-256** content hashes, not URL changes alone
- A URL change without content change does NOT trigger DOCUMENT_CHANGED
- Actual content hashes compared: `old_sha256` vs `new_sha256`

### Change Event Types
```python
class ChangeEventType(str, Enum):
    NEW_BILL = "NEW_BILL"
    STATUS_CHANGED = "STATUS_CHANGED"
    METADATA_CHANGED = "METADATA_CHANGED"
    DATE_CHANGED = "DATE_CHANGED"
    DOCUMENT_CHANGED = "DOCUMENT_CHANGED"
    SOURCE_CHANGED = "SOURCE_CHANGED"
    NO_CHANGE = "NO_CHANGE"
    ERROR = "ERROR"
```

---

## New Bill Processing

When a genuinely new bill is detected:

1. Store metadata in version history (`storage/monitoring/bill_versions/`)
2. Queue knowledge record generation
3. Route based on jurisdiction:
   - **Central**: knowledge extraction → discovery update (NOT training/predictions)
   - **State**: state knowledge extraction → state discovery update (NO predictions)
4. Publish `NEW_BILL` notification event

---

## Update Processing (Changed Bills)

When an existing bill changes:

1. Identify changed fields (via `LegislativeChangeDetector`)
2. Create a version snapshot with `old_value` and `new_value`
3. Queue appropriate downstream refresh:
   - STATUS_CHANGED → lifecycle status refresh
   - DATE_CHANGED → date field refresh
   - DOCUMENT_CHANGED → text re-extraction + knowledge refresh
4. Publish notification event

Historical information is always preserved in version records.

---

## Version History

Every change creates an immutable version snapshot:

```
storage/monitoring/
  bill_versions/
    {bill_id}/
      version_20260915T143022123456.json    ← initial record
      version_20260920T091542789012.json    ← status change record
      version_20261001T120000000000.json    ← PDF update record
```

Each version record contains:
```json
{
  "version": "change_{event_id}",
  "captured_at": "2026-09-15T14:30:22+00:00",
  "source_id": "central_lok_sabha",
  "event_type": "STATUS_CHANGED",
  "field_name": "status",
  "old_value": "introduced",
  "new_value": "passed_lok_sabha",
  "jurisdiction": "central",
  "state": null
}
```

---

## Retry & Failure Isolation

### Retry Logic
- `max_retries = 3` (configurable via `MONITOR_MAX_RETRIES`)
- Exponential backoff: `delay = base_delay × 2^(attempt-1)`
- Base delay: 2 seconds
- Example: attempt 1 fails → wait 2s → attempt 2 fails → wait 4s → attempt 3

### Failure Isolation
One source failure does NOT abort the entire run:

```
Central Lok Sabha:     SUCCESS (0 new, 0 changed)
Central Rajya Sabha:   SUCCESS (0 new, 0 changed)
Central PRS:           SUCCESS (0 new, 0 changed)
Andhra Pradesh:        SUCCESS (0 new, 0 changed)
Karnataka:             ERROR  (Connection timeout)
Kerala:                SUCCESS (0 new, 0 changed)
Telangana:             SUCCESS (0 new, 0 changed)

Overall Status:        PARTIAL_SUCCESS
```

### Run Status
| Condition | Status |
|---|---|
| All sources succeeded | `SUCCESS` |
| Some succeeded, some failed | `PARTIAL_SUCCESS` |
| All sources failed | `FAILED` |

---

## State-Specific Limitations

### Current Coverage
Only four states are currently monitored:
- **Andhra Pradesh** — IMPLEMENTED
- **Karnataka** — IMPLEMENTED
- **Kerala** — IMPLEMENTED
- **Telangana** — IMPLEMENTED

### Unimplemented States
24 remaining states are marked `NOT_IMPLEMENTED` and are not polled.
They will be enabled incrementally in future tasks.

### State Model Protection
State monitoring can update:
- State knowledge records
- State economic assessments
- State company exposure records
- Unified discovery layer

State monitoring will NEVER:
- Create state market predictions
- Create state event studies
- Create state backtesting records
- Run central prediction pipeline on state bills

---

## Central Model Protection

**CRITICAL**: The monitoring pipeline NEVER alters:
- Central training dataset
- Historical predictions (4,700 records)
- Decision support records (4,700 records)
- Backtesting records
- Anticipation records (940 records)
- Stakeholder reports (14,100 records)

New Central bills are routed to knowledge/discovery only.
Promotion to the prediction pipeline requires an explicit separate stage.

---

## Notification Event Feed

Backend-only event log at `storage/monitoring/notification_events/`.

Events published for:
- `NEW_BILL` — newly detected bill
- `STATUS_CHANGED` — bill status update
- `DATE_CHANGED` — date field update
- `DOCUMENT_CHANGED` — PDF content change
- `METADATA_CHANGED` — other field updates

**Not implemented yet** (future tasks):
- Email delivery
- Push notifications
- WhatsApp notifications
- Watchlist alerts
- User preferences

---

## Monitoring Dashboard

Access via Streamlit: **🔭 Legislative Monitor** page.

Features:
- System status (enabled/disabled, last run)
- Source status table (all sources, last checked, errors)
- Recent events feed
- **"Check Now"** manual trigger button
- Data protection guarantees panel

---

## Future SaaS Integration

The monitoring system is designed to integrate with the future SaaS product:

1. **Task 8.13** — Watchlists + user preferences + alert routing
2. **Task 8.14** — SaaS frontend showing "What's New" feed
3. **Task 8.15** — Full integration with notification delivery (email, push)

The `LegislativeEventFeed` backend is already in place to support this.
