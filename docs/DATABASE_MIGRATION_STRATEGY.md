# Multi-Tenant Database Migration Strategy & Data Isolation Contract

**Milestone**: TASK 8.20  
**Scope**: Production Database Persistence Boundary & Migration Safety  
**Engine**: PostgreSQL 16 (Production) / Local Repository Adapter (Development)  

---

## 1. Architectural Data Boundary Principles

1. **Analytical Baseline Freeze Isolation**:
   Frozen econometric and statutory baselines (`data/predictions/`, `data/decisions/`, `data/reports/`, `data/anticipation/`, `data/central_bills/`, `data/state_bills/`, `data/companies/`) **NEVER reside in mutable application database tables**.
   They remain immutable read-only artefacts on file storage or S3/GCS buckets. Database migrations must never touch, alter, or reindex these frozen records.
2. **Strict Multi-Tenant Scoping**:
   All tenant-owned tables (`watchlists`, `watchlist_items`, `alert_rules`, `alert_events`, `notifications`, `notification_preferences`, `tenant_memberships`) mandate a `tenant_id` foreign key and composite index.
3. **Reversibility & Non-Destructive Migrations**:
   All migrations are strictly additive (no column drops or irreversible type conversions without deprecation cycles).

---

## 2. Table Classification & Logical Schema

```
================================================================================
                               SCHEMA MAP
================================================================================

+------------------------------------------------------------------------------+
|                            USER IDENTITIES (PRIVATE)                         |
|  users                                                                       |
|  - user_id (PK), email (UQ), hashed_password, external_idp_sub, full_name    |
+------------------------------------------------------------------------------+
                                       │
                                       ▼ (1:N)
+------------------------------------------------------------------------------+
|                            TENANT ORGANIZATIONS (MUTABLE)                    |
|  tenants                                                                     |
|  - tenant_id (PK), name, plan_tier (FREE/PRO/TEAM/ENTERPRISE), status        |
+------------------------------------------------------------------------------+
         │                                                      │
         ▼ (1:N)                                                ▼ (1:N)
+----------------------------------+          +----------------------------------+
|      TENANT MEMBERSHIPS          |          |          WATCHLISTS              |
|  tenant_memberships              |          |  watchlists                      |
|  - membership_id (PK)            |          |  - watchlist_id (PK)             |
|  - tenant_id (FK), user_id (FK)  |          |  - tenant_id (FK), user_id       |
|  - role (OWNER/ADMIN/MEMBER)     |          +----------------------------------+
+----------------------------------+                            │
                                                                ▼ (1:N)
                                              +----------------------------------+
                                              |        WATCHLIST ITEMS           |
                                              |  watchlist_items                 |
                                              |  - item_id (PK)                  |
                                              |  - watchlist_id (FK)             |
                                              |  - entity_type, entity_id        |
                                              +----------------------------------+

+------------------------------------------------------------------------------+
|                              ALERTING SUBSYSTEM                              |
|  alert_rules                                                                 |
|  - rule_id (PK), tenant_id (FK), user_id, rule_type, conditions (JSONB)      |
|                                                                              |
|  alert_events                                                                |
|  - event_id (PK), rule_id (FK), tenant_id (FK), bill_id, severity, payload   |
|                                                                              |
|  notifications                                                               |
|  - notification_id (PK), tenant_id (FK), user_id, title, channel, status     |
|                                                                              |
|  notification_preferences                                                    |
|  - preference_id (PK), tenant_id (FK), user_id, email_enabled, digest_freq   |
+------------------------------------------------------------------------------+

+------------------------------------------------------------------------------+
|                       OPERATIONAL & AUDIT TELEMETRY (APPEND-ONLY)            |
|  audit_logs                                                                  |
|  - log_id (PK), tenant_id, user_id, action, resource_type, ip_address        |
|                                                                              |
|  ai_usage_records                                                            |
|  - record_id (PK), tenant_id, user_id, prompt_tokens, completion_tokens      |
+------------------------------------------------------------------------------+
```

---

## 3. Migration Sequence (Phased Roadmap)

### Phase 1: Local Development Emulation (CURRENT / TASK 8.20)
- Implemented via `DevelopmentDatabaseProvider` in `storage/database/provider.py`.
- Persists tenant application entities cleanly in structured JSON repository files under `storage/tenants/`, `storage/watchlists/`, `storage/alerts/`, `storage/users/`, and `storage/audit/`.
- Ready for zero-dependency local operation and test runs.

### Phase 2: Schema Definition & Staging PostgreSQL Migration
- Schema DDL defined in `storage/database/provider.py::POSTGRES_SCHEMA_DDL`.
- PostgreSQL container definition configured in `docker-compose.production.yml`.
- `ProductionDatabaseProvider.migrate_schema()` executes idempotent DDL (`CREATE TABLE IF NOT EXISTS`) and builds composite indexes.

### Phase 3: Tenant Data Sync & Cutover
- Synchronizes existing local tenant records into PostgreSQL without downtime.
- Preserves referential integrity between users, tenants, and watchlists.
- Verifies cross-tenant isolation before traffic switchover.

---

## 4. Rollback and Disaster Recovery Procedures

1. **Zero Impact on Predictions**:
   If a database migration fails or experiences connection errors, Central predictions, State dossiers, and Company profiles continue serving with 100% availability because analytical data does not depend on PostgreSQL.
2. **Reversible DDL**:
   All new schema additions use nullable fields or backward-compatible defaults (`plan_tier DEFAULT 'FREE'`, `status DEFAULT 'ACTIVE'`).
3. **Database Snapshot Backups**:
   Automated hourly WAL archiving and daily snapshot restores before applying migrations.
