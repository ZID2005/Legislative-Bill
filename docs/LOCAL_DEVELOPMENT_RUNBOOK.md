# Local Development & Release Runbook

**Document:** Local Development Runbook  
**Milestone:** TASK 8.31D — PostgreSQL Persistence & Supabase-Free Compatible Architecture  
**Stack:** FastAPI (Python 3.14/3.13) + Next.js 16 (TypeScript) + PostgreSQL / SQLite  
**Target Environment:** Localhost / Self-Contained SaaS / Supabase Free Hosted Testing  
**Infrastructure Cost:** ₹0 (Zero Paid Services Required)  

---

## 1. Quick Start

### 1.1 Prerequisites
- Python 3.11+ (Python 3.13 or 3.14 recommended)
- Node.js 18+ (Node 20+ recommended)
- PostgreSQL 14+ (Optional for local PostgreSQL development; SQLite fallback operates automatically without any database installation)
- Git

### 1.2 Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

#### Database Provider Options:
1. **Local SQLite Fallback (Default for zero-setup local development):**
   Leave `DATABASE_URL` commented out or empty. The system will automatically use embedded SQLite at `data/local_dev.sqlite`.
2. **Local PostgreSQL:**
   ```env
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legislative_intel
   ```
3. **Supabase Free (Hosted PostgreSQL):**
   ```env
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   DIRECT_DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
   SUPABASE_ANON_KEY=[YOUR-ANON-KEY]
   ```

---

## 2. Database Migrations, Seeding & Invariant Verification

### 2.1 Running Schema Migrations
Execute the idempotent migration runner against the active database:
```bash
python -c "from storage.database.migrator import MigrationRunner; MigrationRunner().run_migrations()"
```
This applies and records all migrations in `schema_migrations`:
- `001_initial_core_schema.sql` (Core SaaS tenancy, legislation, corporate universe, portfolios)
- `002_analytical_baseline_schema.sql` (Frozen baselines, predictions, decisions, reports with immutability triggers)
- `003_row_level_security.sql` (Tenant-scoped Row Level Security policies)

### 2.2 Deterministic Database Seeding
Seed all 24,000+ records deterministically (idempotent, safe to re-run):
```bash
python scripts/seed_database.py
```
This populates:
- 29 Jurisdictions (1 Central, 4 Active States, 24 Roadmap States)
- 70 Corporate master entities (47 quantitative, 20 intelligence-only, 3 reference)
- 66 Bills (22 Central including 20 production, 44 State acts across AP, KA, KL, TS)
- 104 Corporate operational & state exposures
- 4,700 Central predictions across the 5 authoritative event windows
- 4,700 Multi-stakeholder decisions
- 940 Decoupled anticipation scores
- 14,100 Stakeholder reports (Investor, Business, Public)
- Default tenant organizations and users

### 2.3 Verification & Invariant Audit
Run the automated database verification tool:
```bash
python scripts/backup_restore.py verify
```
*Expected: 100% of all record counts match, state predictions = 0, baseline SHA-256 = `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`.*

### 2.4 Backup and Restore
Create a point-in-time database backup:
```bash
python scripts/backup_restore.py backup
```
Restore the database from an existing backup:
```bash
python scripts/backup_restore.py restore --source storage/backups/sqlite_backup_20261008_150009.sqlite
```

---

## 3. Running the Application Locally

### 3.1 Backend (FastAPI)
From the repository root:
```bash
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/v1/health`

### 3.2 Frontend (Next.js)
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:3000`

---

## 4. Running Test Suites

### 4.1 Database Persistence Test Suite
Run the 25-point persistence and invariant verification suite:
```bash
pytest tests/test_database_persistence.py -v
```
*Expected: 25 / 25 PASSED (100%).*

### 4.2 Full Regression & Analytical Firewall Suite
Run the complete regression suite across all platform milestones:
```bash
pytest \
  tests/test_task_8_30_final_validation.py \
  tests/test_frozen_immutability.py \
  tests/test_analytical_firewall_regression.py \
  tests/test_security_idor.py \
  tests/test_database_persistence.py -v
```
*Expected: 73 / 73 PASSED.*

### 4.3 Frontend Unit Tests & Build Verification
From the `frontend/` directory:
```bash
# Vitest test suite (220 tests)
npm test

# Production build verification (all 35 routes pre-rendered)
npm run build
```

---

## 5. Architectural Invariants & Epistemic Rules

1. **Frozen Baseline:**
   - Manifest path: `docs/production_baseline.json` & database table `analytical_baselines`
   - Authoritative SHA-256: `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`
   - Model weights, predictions (4,700), decisions (4,700), anticipation (940), and stakeholder reports (14,100) are **strictly immutable**.
2. **State Bill Firewall:**
   - State-level stock price predictions remain strictly **0**.
   - State bills provide qualitative sector intelligence, employment dimensions, and corporate operational exposures only.
   - Enforced at database level via `CONSTRAINT chk_predictions_state_firewall`.
3. **Intelligence-Only Company Quarantine:**
   - 20 statutory/public entities are quarantined from quantitative market prediction models.
4. **Decoupled Anticipation Evidence:**
   - Econometric market signals (CAR magnitude, z-score) are strictly decoupled from public information evidence (news, parliamentary bulletins).
   - No causal linkages or allegations of insider trading are ever inferred or generated.
5. **Groq AI Assistant Configuration (Task 8.31E):**
   - Configure in backend `.env`:
     ```env
     GROQ_API_KEY=gsk_your_actual_groq_api_key_here
     GROQ_MODEL=openai/gpt-oss-120b
     ```
   - `GROQ_API_KEY` is strictly backend-only. Never expose it in `frontend/.env.local` or client-side bundles.
   - If unconfigured, the AI analyst displays a graceful offline degradation message without crashing.
6. **Resetting Local Development Data Safely:**
   - Mutable user and tenant data (portfolios, watchlists, alerts) can be reset without altering the frozen baseline:
     ```bash
     python scripts/reset_dev_database.py
     ```
   - NEVER delete or overwrite files in `data/predictions/`, `data/decision_support/`, or `docs/production_baseline.json`.
7. **Infrastructure Cost & Vendor Lock-in:**
   - Local development operates at ₹0 infrastructure cost.
   - AWS deployment remains strictly `FUTURE`.

