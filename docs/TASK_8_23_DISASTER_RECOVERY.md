# TASK 8.23 — Disaster Recovery & Business Continuity Architecture

**Milestone**: TASK 8.23  
**Date**: 2026-09-25  
**Type**: Disaster Recovery, Point-in-Time Recovery & Data Boundary Enforcement  
**Target Environment**: AWS ECS/RDS/S3 (`ap-south-1` — Mumbai)  
**Status**: **VERIFIED_LOCALLY** (Automated End-to-End Simulation)  
**Analytical Foundation**: 100% FROZEN & IMMUTABLE  

---

## 1. Executive Summary & Recovery Objectives

TASK 8.23 defines and validates the Disaster Recovery (DR) and Business Continuity Plan (BCP) for the Legislative Intelligence Platform.

### Recovery Metrics (Task 8.23A Corrected Classification)

> [!WARNING]
> The following RPO/RTO values are **production targets**, not empirically verified production measurements. Verification against live RDS, S3 WAL archiving, or ECS Fargate infrastructure has NOT been performed because those services are not yet deployed. Only local test simulations have been executed.

```
TARGET_RPO                 = <= 1 hour
TARGET_RTO                 = <= 30 minutes
LOCAL_TEST_RECOVERY        = VERIFIED (via scripts/verify_backup_restore.py)
PRODUCTION_RPO_VERIFIED    = NOT_CONFIGURED
PRODUCTION_RTO_VERIFIED    = NOT_CONFIGURED

DATABASE_BACKUP            = PROCEDURE_READY
DATABASE_RESTORE           = PROCEDURE_READY
LIVE_POSTGRES_VERIFICATION = NOT_CONFIGURED (requires live RDS instance)
```

**Production RPO/RTO targets are defined but not yet empirically verified in live cloud infrastructure.**

#### Reference Classifications:
- **A. Frozen file/data artifact backup**: `PUBLIC_FROZEN` analytical baseline — Git versioned, SHA-256 verified. `RPO = 0` (immutable, never changes).
- **B. Tenant operational database backup**: `TENANT_OWNED_MUTABLE` data — procedure defined, locally tested with `DisasterRecoveryService`. Target RPO ≤ 1 hour.
- **C. PostgreSQL PITR**: Write-Ahead Log (WAL) archiving procedure documented (see Section 3). **NOT yet configured against a real production RDS database.** Label: `LOCAL_TEST_DATABASE_VERIFICATION` only.

---

## 2. Data Classification & Domain Partitioning Contract

All data within the platform is classified into four mutually exclusive domains:

```
+---------------------------------------------------------------------------------------+
|                               DATA DOMAIN ARCHITECTURE                                |
+---------------------------------------------------------------------------------------+
|  1. PUBLIC_FROZEN (Analytical Baseline)                                               |
|     - Storage: Read-only files / AWS S3 Object Lock (cold storage)                    |
|     - Content: 20 Central bills, 4,700 predictions, 4,700 decisions,                   |
|                940 anticipation scores, 14,100 stakeholder reports,                   |
|                44 State acts, 44 knowledge dossiers, 86 corporate exposures,          |
|                70 master companies (47 quant, 20 intel, 3 ref), 104 exposures.        |
|     - Invariant: NEVER stored in mutable PostgreSQL tables. NEVER regenerated.        |
+---------------------------------------------------------------------------------------+
|  2. TENANT_OWNED_MUTABLE (SaaS Organization State)                                    |
|     - Storage: Managed PostgreSQL / local JSON repository (`storage/tenants/`, etc.)  |
|     - Content: Tenants, memberships, watchlists, watchlist_items, alert_rules,        |
|                alert_events, notifications, notification_preferences.                 |
|     - Scoping: Strictly scoped by `tenant_id` foreign keys with composite indexes.    |
+---------------------------------------------------------------------------------------+
|  3. USER_OWNED_PRIVATE (Authentication & Identity)                                    |
|     - Storage: PostgreSQL `users` table (`storage/users/` in dev)                     |
|     - Content: User profiles, hashed credentials (Argon2id/bcrypt), sessions.         |
+---------------------------------------------------------------------------------------+
|  4. SYSTEM_OPERATIONAL (Telemetry & Metering)                                         |
|     - Storage: PostgreSQL `audit_logs`, `ai_usage_records` (append-only)              |
|     - Content: Security audit trails, LLM token metering, job execution records.      |
+---------------------------------------------------------------------------------------+
```

---

## 3. Disaster Recovery Procedures

### 1. PostgreSQL Backup Procedure

> [!IMPORTANT]
> **LOCAL_TEST_DATABASE_VERIFICATION**: The PostgreSQL backup procedures below are documented and procedurally ready. However, they have NOT been executed against a real production RDS database because live AWS infrastructure is not yet deployed. Do NOT represent these as production RDS backup/restore verifications.

In production environments with active PostgreSQL credentials and live RDS:
- **Daily Automated Full Snapshot**: Retained for 30 days across multiple availability zones.
- **Continuous Write-Ahead Log (WAL) Shipping**: Streamed to Amazon S3 with 5-minute RPO window.
- **On-Demand Cryptographic Snapshot** (Logical Dump):
  ```bash
  pg_dump -U legis_admin -h postgres -d legislative_intel \
    --clean --if-exists --no-owner -Fc > tenant_backup_$(date +%Y%m%d_%H%M%S).dump
  ```
- **Local/Staging Cryptographic Manifest Backup** (`LOCAL_TEST_DATABASE_VERIFICATION`):
  Executed via `services/disaster_recovery.py::DisasterRecoveryService.create_tenant_backup()`.
  Generates SHA-256 digests for each domain, packaging tenant state while strictly excluding analytical directories.

### 2. Point-in-Time Recovery (PITR) Strategy
In the event of accidental data deletion, ransomware attack, or logical corruption:
1. Identify the exact recovery timestamp $T_{\text{target}}$ prior to the corruption incident.
2. In AWS RDS console or via AWS CLI, initiate restore to point in time:
   ```bash
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier legis-prod-pg-instance \
     --target-db-instance-identifier legis-prod-pg-restored \
     --restore-time 2026-09-25T14:30:00Z \
     --db-subnet-group-name legis-prod-db-subnets
   ```
3. Update ECS task definition `DATABASE_URL` secret reference to point to `legis-prod-pg-restored`.
4. Run schema version check:
   ```bash
   python -c "from services.disaster_recovery import DisasterRecoveryService; print(DisasterRecoveryService.get_schema_version_status())"
   ```

### 3. Restore Verification Procedure
During any restore:
1. Verify backup archive integrity (`verify_backup_integrity()`):
   - Computes SHA-256 for all restored domains.
   - Compares with cryptographic manifest digest.
   - Detects any byte tampering or truncated payload.
2. Restore mutable tenant records.
3. **Mandatory Post-Restore Baseline Parity Verification**:
   - Executes `scripts/verify_frozen_baseline_exact.py`.
   - Validates that all 21 baseline dimensions match 100%.
   - Strictly asserts: $\mathbf{\text{State Predictions}} \equiv 0$.
   - Any baseline count divergence immediately halts system boot and sounds critical alert.

### 4. Migration Rollback Procedure
1. Schema migrations are strictly additive (`CREATE TABLE IF NOT EXISTS`, `ADD COLUMN`).
2. Rollback safety is verified by `DisasterRecoveryService.verify_migration_rollback_safety()`:
   - Validates target schema version exists in `SUPPORTED_SCHEMA_VERSIONS`.
   - Reversible DDL executes without dropping tenant data columns prematurely.
   - Decoupled analytical files in `data/` remain untouched during DDL execution.

---

## 4. Local Deterministic Disaster Recovery Verification

The recovery procedure was tested empirically via `scripts/verify_backup_restore.py`:
- **Step 1**: Verified 10 PUBLIC_FROZEN and 9 TENANT_OWNED_MUTABLE domains.
- **Step 2**: Generated tenant backup archive containing 1,117 files with SHA-256 manifest hash `f43f00ea65b0ba02...`.
- **Step 3**: Tested cryptographic tamper detection — tampered archive correctly rejected with `Checksum mismatch in domains: ['tenants']`.
- **Step 4**: Executed simulated restore of all 1,117 files. Verified frozen baseline parity (`Passed=True`, `State Predictions=0`).
- **Step 5**: Schema version `2026.09.25.v1` and migration rollback safety validated.

Status: **DISASTER_RECOVERY = VERIFIED_LOCALLY**.

> [!NOTE]
> **Verification Scope**: All disaster recovery steps were executed in local test simulation using `scripts/verify_backup_restore.py` against the `DevelopmentDatabaseProvider` and local file system. This is classified as `LOCAL_TEST_DATABASE_VERIFICATION`. Production RDS PITR and S3 WAL archiving have not been exercised. Production RPO/RTO targets are defined but not yet empirically verified in live cloud infrastructure.
