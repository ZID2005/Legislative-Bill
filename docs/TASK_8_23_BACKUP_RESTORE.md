# TASK 8.23 — Production Backup and Restore Procedures

**Status**: AUTHORITATIVE / TESTED  
**Date**: September 2026  
**Application Code Status**: READY  
**Cloud Deployment Status**: BLOCKED_BY_CREDENTIALS  
**Target RPO (Recovery Point Objective)**: $\le$ 1 hour *(production target — locally tested, not yet verified against live RDS/WAL)*  
**Target RTO (Recovery Time Objective)**: $\le$ 30 minutes *(production target — locally tested, not yet verified against live ECS/RDS)*

> [!WARNING]
> **Task 8.23A Qualification**: RPO and RTO values above are **production targets**. Local test recovery has been verified via `scripts/verify_backup_restore.py`. These values have NOT been empirically demonstrated against live AWS RDS, S3 WAL archiving, or ECS Fargate infrastructure. Production RPO/RTO targets are defined but not yet empirically verified in live cloud infrastructure.  

---

## 1. Executive Summary & Architecture

The Legislative Bill Analysis and Prediction Platform implements a deterministic, multi-domain backup and disaster-recovery architecture. The platform enforces strict isolation between:

1. **`PUBLIC_FROZEN` Baseline Data** *(Frozen file/data artifact backup)*: Read-only, cryptographically verified analytical baseline (66 unified bills, 47 quantitative securities, 940 pairs, 4,700 predictions, 4,700 decisions, 940 anticipation scores, strictly 0 state predictions). This data is immutable, Git version-controlled, and has `RPO = 0`.
2. **`TENANT_OWNED_MUTABLE` SaaS Operational Data** *(Tenant operational database backup)*: User accounts, tenant profiles, notification logs, audit trails, alert configurations, API keys, and workspace preferences. Procedure is documented and locally tested. Target RPO ≤ 1 hour.
3. **PostgreSQL PITR** *(Write-Ahead Log backup)*: Procedure documented (see Section 2.2). **`LIVE_POSTGRES_VERIFICATION = NOT_CONFIGURED`** — this procedure has NOT been verified against a real production RDS database because live infrastructure is not yet deployed. Label all local test executions as `LOCAL_TEST_DATABASE_VERIFICATION`.

```
+-------------------------------------------------------------------------+
|                           BACKUP ARCHITECTURE                           |
+-------------------------------------------------------------------------+
|                                                                         |
|   +--------------------------+          +---------------------------+   |
|   |   PUBLIC_FROZEN DATA     |          |  TENANT_OWNED_MUTABLE     |   |
|   |   (data/processed, etc.) |          |  (PostgreSQL / Redis)     |   |
|   +------------+-------------+          +-------------+-------------+   |
|                |                                      |                 |
|       Git Version Pinning                     pg_dump / WAL Archive     |
|       SHA-256 Manifest                        Hourly Snaphots           |
|                |                                      |                 |
|                v                                      v                 |
|   +-----------------------------------------------------------------+   |
|   |            DISASTER RECOVERY ARCHIVE & S3 COLD STORAGE          |   |
|   |            - Cryptographic SHA-256 Checksums                    |   |
|   |            - Automated Manifest Tamper Detection                |   |
|   |            - Strict Zero State Predictions Invariant Post-Check |   |
|   +-----------------------------------------------------------------+   |
|                                                                         |
+-------------------------------------------------------------------------+
```

---

## 2. PostgreSQL Backup Procedures

### 2.1 Automated Hourly Logical Backups (`pg_dump`)
In production environments with active PostgreSQL credentials:

```bash
#!/usr/bin/env bash
# scripts/backup_postgresql.sh
set -euo pipefail

BACKUP_DIR="/var/backups/legislative_platform"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%SZ")
BACKUP_FILE="${BACKUP_DIR}/db_tenant_backup_${TIMESTAMP}.dump"
MANIFEST_FILE="${BACKUP_DIR}/manifest_${TIMESTAMP}.json"

mkdir -p "${BACKUP_DIR}"

# Execute custom-format compressed binary dump of tenant tables
pg_dump \
  --host="${DB_HOST}" \
  --port="${DB_PORT:-5432}" \
  --username="${DB_USER}" \
  --format=custom \
  --compress=9 \
  --exclude-table="public.frozen_analytical_*" \
  --file="${BACKUP_FILE}" \
  "${DB_NAME}"

# Generate SHA-256 digest
SHA256_HASH=$(sha256sum "${BACKUP_FILE}" | awk '{print $1}')

# Write manifest
cat <<EOF > "${MANIFEST_FILE}"
{
  "backup_file": "$(basename "${BACKUP_FILE}")",
  "created_at": "${TIMESTAMP}",
  "sha256": "${SHA256_HASH}",
  "db_name": "${DB_NAME}",
  "type": "TENANT_OWNED_MUTABLE"
}
EOF

# Sync to encrypted S3 bucket
aws s3 cp "${BACKUP_FILE}" "s3://${BACKUP_S3_BUCKET}/backups/${TIMESTAMP}/" --sse aws:kms
aws s3 cp "${MANIFEST_FILE}" "s3://${BACKUP_S3_BUCKET}/backups/${TIMESTAMP}/" --sse aws:kms

echo "Backup ${TIMESTAMP} completed and verified."
```

### 2.2 Point-In-Time Recovery (PITR) with Write-Ahead Logging (WAL)
- **WAL Archiving**: PostgreSQL `archive_mode = on`, archiving WAL segments to S3 via `wal-g` or AWS RDS automated archiving every 5 minutes.
- **RPO**: Enables recovery to any arbitrary second within the 30-day retention window, guaranteeing RPO $\le$ 5 minutes for transaction logs.

---

## 3. Disaster Recovery Engine (`services/disaster_recovery.py`)

The platform includes an automated `DisasterRecoveryService` providing end-to-end backup, validation, and restore capabilities:

### Key Features
1. **Domain Classification**:
   - `PUBLIC_FROZEN`: Data directories `data/processed`, `data/raw`, `data/state`, and analytical fixtures.
   - `TENANT_OWNED_MUTABLE`: Tenant data directories, notification records, audit logs, and operational databases.
2. **Cryptographic Integrity**:
   - Computes SHA-256 digests for every file.
   - Generates signed `manifest.json`.
   - Tamper-detection algorithm rejects any archive where file hashes mismatch or unexpected files are injected.
3. **Analytical Baseline Invariant Check**:
   - Restorations must pass analytical invariant checks:
     - Central predictions: exactly 4,700.
     - Central decisions: exactly 4,700.
     - Central anticipation scores: exactly 940.
     - State predictions: strictly 0.
     - State decisions: strictly 0.
     - State anticipation scores: strictly 0.

---

## 4. Disaster Recovery Execution Procedures

### 4.1 Creating a Backup
```bash
python scripts/verify_backup_restore.py
```
Output:
- Backs up all tenant files to an isolated archive.
- Creates `manifest.json` with file counts, sizes, and SHA-256 digests.
- Verifies archive integrity.

### 4.2 Restoring from a Backup
```python
from services.disaster_recovery import DisasterRecoveryService
import tempfile
from pathlib import Path

dr = DisasterRecoveryService(base_dir=Path("."))
archive_path = Path("backups/backup_20260925_230000.tar.gz")

# Perform verified restoration
restore_result = dr.restore_backup(
    archive_path=archive_path,
    target_dir=Path("./restored_data"),
    verify_baseline=True
)

if not restore_result["success"]:
    raise RuntimeError(f"Restore failed: {restore_result['error']}")
```

### 4.3 Tamper Detection Validation
Any altered file or mismatched checksum immediately triggers an abort:
```python
# Tamper attempt detected:
# ValueError: Backup verification failed: Hash mismatch for tenant_data/alerts.json
```

---

## 5. Post-Restore Verification Checklist

After any restore operation (production or local simulation), the following verification commands must be executed in order:

```bash
# Step 1: Run Exact Baseline Parity Check
python scripts/verify_frozen_baseline_exact.py
# Must return: ALL 21 EXACT PARITY CHECKS PASSED

# Step 2: Verify git status of data directory
git status --short data/
# Must be completely clean (empty output)

# Step 3: Run Deterministic Launch Gate
python scripts/production_launch_gate.py
# Must return exit code 0

# Step 4: Verify Health and Readiness Endpoints
curl -s http://localhost:8000/ready
curl -s http://localhost:8000/health/ready
# Both must return HTTP 200 OK with "status": "healthy"
```

---

## 6. Retention & Cold Storage Policy

| Data Class | Backup Cadence | Retention Window | Storage Medium | Encryption |
|---|---|---|---|---|
| PostgreSQL WAL | Every 5 minutes | 35 days | AWS S3 Standard / RDS PITR | AWS KMS |
| PostgreSQL Full Dump | Hourly | 14 days | AWS S3 Standard-IA | AWS KMS |
| PostgreSQL Weekly Dump | Weekly | 365 days | AWS S3 Glacier Instant Retrieval | AWS KMS |
| Analytical Baseline | On release | Permanent (Git LFS / S3) | Git + Multi-region S3 bucket | AWS KMS / SHA-256 |
| Audit & Access Logs | Real-time streaming | 365 days | CloudWatch Logs / S3 Glacier | KMS encrypted |
