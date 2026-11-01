# Database Architecture Specification (PostgreSQL & Supabase-Free)

**Document Reference:** `docs/DATABASE_ARCHITECTURE.md`  
**Task Association:** Task 8.31D — PostgreSQL Persistence & Supabase-Free Compatible Architecture  
**Canonical Database Technology:** PostgreSQL  
**Zero-Cost Infrastructure Target:** Local PostgreSQL & SQLite Fallback (₹0) / Supabase Free Hosted Testing (₹0)  
**Baseline SHA-256:** `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`  

---

## 1. Executive Summary & Canonical Decision

The Legislative Intelligence and Market Impact Platform implements a persistent, updateable, multi-tenant database architecture anchored strictly on **PostgreSQL** as the canonical database technology.

### 1.1 Architectural Principle
```text
                            APPLICATION
                                 │
                                 ▼
                         PostgreSQL Layer
                                 │
                     ┌───────────┴───────────┐
                     │                       │
                     ▼                       ▼
              LOCAL POSTGRESQL         SUPABASE FREE
               Development             Hosted/Test Option
                     │                       │
                     └───────────┬───────────┘
                                 │
                          SAME SCHEMA
                          SAME MIGRATIONS
                          SAME DATA MODEL
```

The system operates identically across:
1. **Local PostgreSQL** (Canonical development and air-gapped deployments at ₹0 cost).
2. **Supabase Free** (Hosted testing using Supabase's managed PostgreSQL, Auth, and RLS at ₹0 cost).
3. **Local Embedded SQLite** (Zero-configuration local development fallback allowing 100% offline unit and integration testing without running local database services).

### 1.2 Zero Vendor Lock-in & Cost Guarantee
- Standard PostgreSQL DDL, SQL constraints, foreign keys, and indexes are used exclusively.
- No proprietary Supabase extensions or paid addons (Supabase Pro, AWS RDS, paid Redis, paid Kafka) are required.
- Local development is strictly guaranteed at **₹0 infrastructure cost**.

---

## 2. Fourfold Data Classification Model

Every entity in the platform belongs to one of four authoritative data domains:

| Category | Storage Target | Mutability | Scoping | Description |
|:---|:---|:---|:---|:---|
| **A. Frozen Analytical Data** | `analytical_baselines`, `predictions`, `decisions`, `anticipation_scores`, `stakeholder_reports` | **IMMUTABLE** (Hard Triggers & Repository Guards) | Global / Read-Only | 4,700 predictions, 4,700 decisions, 940 anticipation scores, 14,100 stakeholder reports across 5 authoritative event windows `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`. Anchored to SHA-256 `50ae76039bccf2e4`. |
| **B. Live Legislative Intelligence** | `bills`, `bill_versions`, `official_documents`, `sources`, `source_health`, `evidence` | **PERSISTENT & UPDATABLE** | Global / Provenance-Aware | Central acts, State legislation (44 acts across AP, KA, KL, TS), official PDFs, PRS metadata, pipeline ingestion logs, evidence items with temporal discovery timestamps. |
| **C. Tenant / Application Data** | `tenants`, `users`, `tenant_memberships`, `portfolios`, `portfolio_holdings`, `watchlists`, `watchlist_items`, `alert_rules`, `alert_events`, `notifications` | **MUTABLE** | **TENANT-SCOPED** (`tenant_id`) | Institutional user state, portfolios, multi-asset holdings, custom watchlists, notification preferences, saved filters. Protected by RLS and IDOR service firewalls. |
| **D. Reference Data** | `jurisdictions`, `sectors`, `industries`, `companies`, `corporate_exposures` | **FROZEN / UPDATABLE REFERENCE** | Global Reference | 29 jurisdictions (1 Central, 4 Active States, 24 Roadmap), 70 corporate master entities (47 quantitative, 20 intelligence-only, 3 reference), 104 corporate exposure linkages. |

---

## 3. Database Schema Architecture

The database schema is organized into 6 normalized functional domains spanning 32 tables.

### 3.1 Domain 1: Identity & Multi-Tenancy
- **`tenants`**: Multi-tenant organizations (`tenant_id`, `name`, `slug`, `plan_tier`, `status`, `settings_json`, `created_at`).
- **`users`**: Platform users (`user_id`, `tenant_id`, `email`, `display_name`, `role`, `status`, `hashed_password`).
- **`tenant_memberships`**: M:N user-tenant mapping with granular RBAC (`membership_id`, `tenant_id`, `user_id`, `role` [OWNER, ADMIN, MEMBER, VIEWER]).
- **`user_preferences`**: User-scoped UI/UX settings (`user_id`, `theme`, `default_jurisdiction`, `preferences_json`).

### 3.2 Domain 2: Legislation & Sources
- **`jurisdictions`**: Legislative bodies (`jurisdiction_code`, `name`, `type` [CENTRAL, STATE], `status`, `bills_count`).
- **`bills`**: Master legislative catalog (`bill_id`, `jurisdiction`, `state`, `bill_number`, `title`, `status`, `category`, `introduced_date`, `is_central_production`, `is_state_statutory`).
- **`bill_versions`**: Historical versions and revisions of bills (`version_id`, `bill_id`, `version_number`, `pdf_url`, `content_hash`).
- **`official_documents`**: Gazette publications and PRS bill tracks (`document_id`, `bill_id`, `title`, `document_type`, `file_path`, `content_hash`).
- **`sources`**: Ingestion source registry (`source_id`, `source_name`, `source_type`, `base_url`, `jurisdiction`).
- **`source_health`**: Automated crawler telemetry (`health_id`, `source_id`, `status`, `response_time_ms`, `last_successful_sync`).

### 3.3 Domain 3: Corporate Universe & Exposures
- **`sectors`**: Macro-economic sectors (`sector_name`, `code`, `description`).
- **`industries`**: Granular industries (`industry_name`, `sector_name`, `description`).
- **`companies`**: 70 master corporate entities (`isin`, `name`, `symbol`, `sector`, `industry`, `market_cap_category`, `coverage_tier` [QUANTITATIVE, INTELLIGENCE_ONLY, REFERENCE], `is_quant_eligible`).
- **`corporate_exposures`**: 104 corporate operational and statutory exposure mappings (`exposure_id`, `isin`, `jurisdiction`, `state`, `exposure_type`, `severity`, `description`).

### 3.4 Domain 4: Evidence & Anticipation Contexts
- **`evidence_sources`**: Public information registries (`source_id`, `name`, `url`, `credibility_score`).
- **`evidence`**: Verified pre-event public signals (`evidence_id`, `bill_id`, `company_isin`, `headline`, `publication_timestamp`, `discovery_timestamp`, `verification_status`).
- **`anticipation_scores`**: 940 decoupled anticipation records (`score_id`, `bill_id`, `company_isin`, `market_signal_level`, `market_signal_score`, `public_info_level`, `information_signal_score`, `combined_classification`).

### 3.5 Domain 5: User Workspace & SaaS Portfolios
- **`portfolios`**: Tenant-scoped institutional portfolios (`portfolio_id`, `tenant_id`, `user_id`, `name`, `currency`).
- **`portfolio_holdings`**: Securities tracked in portfolio (`holding_id`, `portfolio_id`, `tenant_id`, `isin`, `ticker`, `quantity`, `avg_purchase_price`).
- **`watchlists`**: Custom tracked entity collections (`watchlist_id`, `tenant_id`, `user_id`, `name`).
- **`watchlist_items`**: Tracked bills and companies (`item_id`, `watchlist_id`, `tenant_id`, `item_type`, `item_id_ref`).
- **`alert_rules`**: User-defined notification rules (`rule_id`, `tenant_id`, `user_id`, `rule_type`, `conditions_json`).
- **`alert_events`**: Dispatched alerts (`event_id`, `tenant_id`, `rule_id`, `severity`, `title`, `payload_json`).
- **`notifications`**: In-app user notifications (`notification_id`, `tenant_id`, `user_id`, `title`, `is_read`).
- **`audit_logs`**: Tenant security audit trail (`log_id`, `tenant_id`, `user_id`, `action`, `resource`, `ip_address`).

### 3.6 Domain 6: Frozen Econometric Baseline
- **`analytical_baselines`**: Baseline manifest ledger (`baseline_id`, `version`, `sha256`, `status` [FROZEN], `record_counts`, `is_frozen`).
- **`predictions`**: 4,700 central event-study predictions across 5 authoritative event windows (`prediction_id`, `baseline_id`, `bill_id`, `company_isin`, `event_window`, `predicted_direction`, `predicted_market_moving`, `predicted_confidence`, `is_frozen`).
- **`decisions`**: 4,700 multi-criteria stakeholder decisions (`decision_id`, `baseline_id`, `bill_id`, `company_isin`, `event_window`, `risk_category`, `impact_score`, `risk_score`).
- **`stakeholder_reports`**: 14,100 institutional impact reports (`report_id`, `baseline_id`, `bill_id`, `company_isin`, `stakeholder_type` [INVESTOR, BUSINESS, PUBLIC], `event_window`, `executive_summary`, `actionable_recommendations`).

---

## 4. Statutory Firewalls & Immutability Enforcement

### 4.1 Statutory State Prediction Firewall
State legislation (44 acts across Andhra Pradesh, Karnataka, Kerala, Telangana) is strictly qualitative.
The database enforces:
```sql
CONSTRAINT chk_predictions_state_firewall
    CHECK (bill_id NOT LIKE 'ap_%' AND bill_id NOT LIKE 'ka_%' AND bill_id NOT LIKE 'kl_%' AND bill_id NOT LIKE 'ts_%');
```
**Invariant:** `STATE STOCK PREDICTIONS = 0` (Verified by automated unit test `test_13_state_stock_predictions_remain_zero`).

### 4.2 Intelligence-Only Company Quarantine
20 companies are classified as `INTELLIGENCE_ONLY` (non-listed statutory entities, public boards, municipal corporations).
- Database foreign key and application repositories prevent intelligence-only ISINs from being registered in `predictions` or `decisions`.
- **Invariant:** `INTELLIGENCE_ONLY in predictions = 0` (Verified by `test_15_intelligence_only_companies_quarantined_from_predictions`).

### 4.3 Frozen Econometric Immutability Trigger
In PostgreSQL, an automated trigger intercepts any illegal `UPDATE` or `DELETE` against the 5 frozen tables:
```sql
CREATE OR REPLACE FUNCTION enforce_frozen_immutability()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'IMMUTABLE_FROZEN_RECORD_VIOLATION: Table % contains immutable frozen econometric data (SHA-256: 50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7). Updates and deletions are strictly prohibited.', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_protect_predictions_immutability
BEFORE UPDATE OR DELETE ON predictions
FOR EACH ROW EXECUTE FUNCTION enforce_frozen_immutability();
```
In local SQLite/dev provider, the `DevelopmentDatabaseProvider.execute_mutation()` intercepts all `UPDATE` and `DELETE` statements targeting frozen tables and raises `FrozenRecordImmutabilityError`.

---

## 5. Multi-Tenancy & Row-Level Security (RLS)

### 5.1 Portable RLS Policy Structure
In hosted Supabase PostgreSQL, RLS is enabled on all tenant-owned tables (`portfolios`, `watchlists`, `alert_rules`, `notifications`):
```sql
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_portfolios ON portfolios
    FOR ALL
    USING (
        tenant_id = current_setting('app.current_tenant_id', true)
        OR tenant_id = auth.jwt() ->> 'tenant_id'
    );
```
### 5.2 Local Service Isolation
When running against Local PostgreSQL or SQLite without Supabase Auth, the repository layer (`storage/portfolio_repository.py`, `storage/watchlist_repository.py`) injects strict `WHERE tenant_id = :tenant_id` clauses on every query and mutation, rejecting cross-tenant lookups (IDOR attempts return `None` or raise `TenantMismatchError`).

---

## 6. Performance Indexing Strategy

Targeted B-tree indexes are implemented for high-frequency analytical lookups:
- `idx_predictions_bill`: `predictions(bill_id)`
- `idx_predictions_company`: `predictions(company_isin)`
- `idx_predictions_window`: `predictions(event_window)`
- `idx_predictions_baseline`: `predictions(baseline_id)`
- `idx_holdings_portfolio`: `portfolio_holdings(portfolio_id)`
- `idx_holdings_tenant`: `portfolio_holdings(tenant_id)`
- `idx_watchlists_tenant`: `watchlists(tenant_id)`
- `idx_alert_rules_tenant`: `alert_rules(tenant_id)`

---

## 7. Migration & Backup Strategy

### 7.1 Migrations Engine (`storage/database/migrator.py`)
- Versioned SQL files in `migrations/`:
  - `001_initial_core_schema.sql`
  - `002_analytical_baseline_schema.sql`
  - `003_row_level_security.sql`
- Tracked in `schema_migrations` table with SHA-256 checksums to detect script tampering.
- 100% idempotent: running repeatedly executes 0 redundant statements.

### 7.2 Backup & Restore Utility (`scripts/backup_restore.py`)
```bash
# 1. Verify all baseline invariants and counts
python scripts/backup_restore.py verify

# 2. Generate timestamped database backup with SHA-256 manifest
python scripts/backup_restore.py backup

# 3. Restore database from backup archive
python scripts/backup_restore.py restore --source storage/backups/sqlite_backup_*.sqlite
```
