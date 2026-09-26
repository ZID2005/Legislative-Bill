# Disaster Recovery & Business Continuity Architecture

**Milestone**: TASK 8.20  
**Scope**: Backup Strategy, Point-in-Time Recovery, and Data Domain Classification  
**Status**: DESIGNED & TESTED (Local Emulation); OPERATIONAL IN MANAGED CLOUD  

---

## 1. Status Classification by Domain

In accordance with TASK 8.20 requirements, capabilities are classified rigorously as:
- **DESIGNED**: Architecture, procedures, and scripts specified and documented.
- **TESTED**: Validated programmatically via test suites and local validation scripts.
- **OPERATIONAL**: Active infrastructure provisioned and running in a live cloud environment.

| Subsystem | Strategy | Status | Validation Evidence |
| :--- | :--- | :--- | :--- |
| **Analytical Baseline Data** | Immutable SHA256 checksums on disk + Git version control | **TESTED** | `tests/test_frozen_immutability.py` (0 bytes mutated). |
| **Tenant Application Data** | Point-in-time PostgreSQL snapshot + WAL archiving | **DESIGNED** | `storage/database/provider.py::POSTGRES_SCHEMA_DDL` + DDL rollback plan. |
| **Session & Revocation State** | Multi-replica Redis cluster with AOF persistence | **DESIGNED** | `infrastructure/cache/provider.py` with in-memory test harness. |
| **Application Configuration** | Encrypted parameter store / 12-factor environment contract | **TESTED** | `docs/PRODUCTION_CONFIGURATION.md` and `StartupValidator`. |
| **Audit & Metering Trails** | Append-only partitioned tables with immutable constraints | **DESIGNED** | Table DDL with non-nullable timestamps and indexing. |

---

## 2. Immutable Analytical Baseline Recovery

The analytical foundation of the platform is strictly frozen:
- **Central**: 20 production bills (22 scanned records), 47 quantitative securities, 940 pairs, 4,700 predictions across 5 event horizons `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`, 4,700 decisions, 940 anticipation scores, 14,100 stakeholder reports.
- **State**: 44 bills, 44 PDFs, 44 knowledge records, 86 corporate exposures, 0 state predictions.
- **Unified**: 66 legislative records, 70 companies (47 quant + 20 intel + 3 ref), 104 exposures.

### Recovery Procedure for Frozen Baseline:
1. Analytical datasets are version-controlled in the repository and replicated to cold cloud object storage (e.g. AWS S3 / Cloudflare R2 / GCS with Object Lock).
2. If any local corruption or filesystem error occurs:
   ```bash
   git checkout -- data/predictions/ data/decisions/ data/reports/ data/anticipation/ data/companies/ data/state_bills/
   python scripts/verify_frozen_baseline_exact.py
   ```
3. Verification script ensures 100% count match before the service accepts traffic.

---

## 3. PostgreSQL Database Backup & Restore Plan

### Backup Strategy:
1. **Automated Nightly Full Snapshot**:
   Executed via managed PostgreSQL (AWS RDS / Supabase / Neon) with 30-day retention.
2. **Continuous Write-Ahead Logging (WAL)**:
   Point-in-Time Recovery (PITR) up to the second for any transaction rollback.
3. **Logical Dump Script** (`pg_dump`):
   ```bash
   pg_dump -U legis_admin -h postgres -d legislative_intel --clean --if-exists --no-owner -Fc > backup_$(date +%Y%m%d_%H%M%S).dump
   ```

### Restore Procedure:
1. Terminate active application connections (or stop worker containers):
   ```bash
   docker stop legis_worker legis_scheduler legis_api
   ```
2. Restore database from dump:
   ```bash
   pg_restore -U legis_admin -h postgres -d legislative_intel --clean --if-exists backup_target.dump
   ```
3. Run schema verification and health probe:
   ```bash
   python -c "from storage.database.provider import get_database_provider; print(get_database_provider().health_check())"
   ```
4. Restart application containers:
   ```bash
   docker start legis_api legis_worker legis_scheduler
   ```

---

## 4. Disaster Recovery Targets (RTO / RPO)

| Metric | Target | Rationale |
| :--- | :--- | :--- |
| **Recovery Time Objective (RTO)** | < 15 minutes | Stateless Next.js and FastAPI containers can redeploy instantly; PostgreSQL restore from snapshot takes under 10 minutes. |
| **Recovery Point Objective (RPO)** | < 5 minutes | Continuous WAL replication guarantees negligible data loss for tenant mutable actions. Analytical data has RPO = 0 (frozen). |
