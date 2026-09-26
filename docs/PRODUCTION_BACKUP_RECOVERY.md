# Production Backup, Disaster Recovery & Data Persistence Plan

**Product:** India Legislative Intelligence & Market Impact Platform  
**Version:** 1.0.0-rc  
**Document Classification:** Operations & Infrastructure Runbook  
**Last Verified:** 2026-09-20  

---

## 1. Executive Statement on Production State

> [!IMPORTANT]
> **Operational Transparency Notice**:
> In local development and staging environments, persistence is currently hosted on local filesystem and SQLite stores. Automated cloud object replication (e.g. AWS S3 Glacier, Azure Blob, Google Cloud Storage) is **NOT YET CONFIGURED** at the physical infrastructure tier.
> 
> This document specifies the authoritative **Target Recovery Objectives (RPO/RTO)**, data classification matrix, backup cadences, and step-by-step restoration procedures required prior to production go-live.

---

## 2. Recovery Objectives (RPO & RTO)

| Dataset Tier | Target RPO (Recovery Point Objective) | Target RTO (Recovery Time Objective) | Maximum Tolerable Data Loss | Primary Recovery Mechanism |
| :--- | :---: | :---: | :---: | :--- |
| **Tier 1: Frozen Analytical Baselines** | **0 seconds** (Immutable) | **< 15 minutes** | Zero tolerance | Redundant read-only replicas / immutable git-LFS / cold storage |
| **Tier 2: User Personalization (Watchlists & Alerts)** | **< 1 hour** | **< 30 minutes** | Max 1 hour user configuration changes | Point-in-time database WAL archiving / scheduled volume snapshots |
| **Tier 3: Monitoring Run Logs & Telemetry** | **< 24 hours** | **< 2 hours** | Max 24 hours monitoring check traces | Daily differential filesystem backups / log aggregators |
| **Tier 4: Extractive Statutory Text & PDFs** | **< 7 days** | **< 4 hours** | Zero loss of statutory text (re-fetchable) | Offsite cold storage mirror of official PDFs |

---

## 3. Data Classification & Persistence Architecture

```
                                  DATA PERSISTENCE ARCHITECTURE
                                                │
         ┌──────────────────────────────┬───────┴──────────────────────────────┐
         ▼                              ▼                                      ▼
┌──────────────────┐          ┌──────────────────┐                   ┌──────────────────┐
│ FROZEN BASELINES │          │ DYNAMIC TENANCY  │                   │ MONITORING STATE │
│ (Read-Only)      │          │ (Read/Write)     │                   │ (Append-Only)    │
├──────────────────┤          ├──────────────────┤                   ├──────────────────┤
│ Central Preds    │          │ User Watchlists  │                   │ Source Registry  │
│ Central Decs     │          │ Alert Rules      │                   │ Check Runs       │
│ Anticipation     │          │ Notifications    │                   │ Change Events    │
│ Reports (14.1k)  │          │ Preferences      │                   │ Bill Versions    │
└──────────────────┘          └──────────────────┘                   └──────────────────┘
         │                              │                                      │
   Snapshot Mode:                 Snapshot Mode:                         Snapshot Mode:
   Immutable Hash                 Hourly WAL/Diff                        Daily Rolling
```

### Dataset Breakdown

1. **Frozen Analytical Datasets (Central)**:
   - **Path**: `data/predictions/`, `data/decision_support/`, `data/anticipation/scores/`, `data/reports/`
   - **Records**: 4,700 predictions, 4,700 decisions, 940 anticipation scores, 14,100 stakeholder reports.
   - **Source of Truth**: Static versioned JSON artifacts.
   - **Mutability**: Strictly **IMMUTABLE** (`read_only=True`, guarded by `FrozenDatasetImmutableError`).
   - **Backup Requirement**: High-durability mirror (99.999999999% durability S3/GCS bucket with Object Lock).

2. **Personalization & Tenancy State**:
   - **Path**: `storage/watchlists/`, `storage/alerts/`, `storage/users/`
   - **Records**: Multi-tenant custom watchlists, active event trigger rules, user notification inboxes.
   - **Source of Truth**: Structured JSON / SQLite database.
   - **Mutability**: Read/Write tenant-isolated.
   - **Backup Requirement**: Hourly automated incremental snapshots with 30-day retention.

3. **Legislative Monitoring & Discovery State**:
   - **Path**: `storage/monitoring/` (`source_registry_state.json`, `monitoring_runs/`, `change_events/`)
   - **Records**: Source check timestamps, SHA-256 document diffs, detected legislative updates.
   - **Source of Truth**: Monitoring repository event log.
   - **Mutability**: Append-only event stream.
   - **Backup Requirement**: Daily automated snapshots; ephemeral cache rebuildable via re-scan.

4. **Statutory Corpus & Official Gazettes**:
   - **Path**: `data/bills/`, `data/state_bills/`
   - **Records**: 20 Central bills + 44 State pilot bills, official PDFs, extracted metadata, knowledge layers.
   - **Source of Truth**: Primary state gazette and parliamentary portal documents.
   - **Mutability**: Append-only as new statutes are enacted.
   - **Backup Requirement**: Weekly differential sync to cold storage.

---

## 4. Operational Backup Procedures

### A. Pre-Deployment Cold Backup
Prior to any production deployment or server migration:
```bash
# Generate deterministic tar archive of frozen analytical baselines
tar -czvf /backups/legislative_intel_frozen_baselines_$(date +%F).tar.gz \
    data/predictions/ \
    data/decision_support/ \
    data/anticipation/scores/ \
    data/reports/ \
    data/state_bills/

# Generate SHA-256 checksum manifest
sha256sum /backups/legislative_intel_frozen_baselines_$(date +%F).tar.gz > \
    /backups/legislative_intel_frozen_baselines_$(date +%F).tar.gz.sha256
```

### B. User Tenancy & Alerts Incremental Backup
Scheduled hourly cron on production host:
```bash
# Incremental snapshot of active user storage
rsync -a --delete storage/ /backups/hourly/storage_latest/
```

---

## 5. Disaster Recovery & Restoration Playbook

### Scenario 1: Accidental Baseline File Deletion or Corruption
1. **Detect**: Alert raised by `GET /ready` failing baseline parity checks.
2. **Halt**: Stop traffic routing to degraded node.
3. **Restore**:
   ```bash
   # Restore frozen baseline directory from verified archive
   tar -xzvf /backups/legislative_intel_frozen_baselines_*.tar.gz -C /
   ```
4. **Verify**:
   ```bash
   python -c "from utils.baseline_verifier import verify_production_baseline; r = verify_production_baseline(); assert r.passed, 'Baseline parity mismatch!'"
   ```
5. **Resume**: Re-enable node traffic.

### Scenario 2: Storage Volume Catastrophic Loss
1. Provision fresh storage volume mounted at `/app/storage` and `/app/data`.
2. Restore latest base image and extract baseline archive.
3. Apply latest incremental backup of `/app/storage`.
4. Run startup verification diagnostics:
   ```bash
   python -c "from services.startup_validator import StartupValidator; r = StartupValidator().run_validation(strict=True)"
   ```
5. Start backend daemon:
   ```bash
   uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4
   ```

---

## 6. In-Memory Cache Recovery Policy

The application utilizes high-performance in-memory indexes (`api/dependencies.py`) for:
- 4,700 Central Prediction records
- 4,700 Central Decision records
- 940 Anticipation Scores

**Recovery Characteristic**:
- **Durability**: Non-durable cache (read-through).
- **Restart Impact**: Caches are cleared on process termination.
- **Warm-up**: Rebuilt automatically on first request within ~15–20 seconds on cold start.
- **Zero Loss**: Because data is read directly from disk, no data is ever lost on service restarts.
