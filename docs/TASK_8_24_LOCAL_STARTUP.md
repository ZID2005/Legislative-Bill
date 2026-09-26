# TASK 8.24 — Local SaaS Operational Runbook & Startup Guide

**Milestone:** TASK 8.24  
**Classification:** Operational Runbook & Lifecycle Management  
**Scope:** Complete Local SaaS Stack (Frontend, Backend, DB, Cache, Worker, Scheduler)  

---

## 1. Quick Reference: Operational Commands

| Action | Primary Command | Alternative / Native Command |
|---|---|---|
| **PRE-FLIGHT CHECK** | `python scripts/start_local_saas.py --check-only` | `python scripts/verify_frozen_baseline_exact.py` |
| **START FULL STACK** | `docker compose up` | Native Terminals (see Section 2) |
| **START BACKEND** | `python -m uvicorn api.app:app --host 127.0.0.1 --port 8000` | `python scripts/start_local_saas.py --backend-only` |
| **START FRONTEND** | `cd frontend && npm run dev` | `cd frontend && npm run start` (production mode) |
| **RUN WORKER ONCE** | `python scripts/start_local_saas.py --run-worker-once` | `python -m infrastructure.jobs.runner alerts` |
| **RUN SCHEDULER ONCE** | `python scripts/start_local_saas.py --run-scheduler-once`| `python -m infrastructure.jobs.runner scheduler` |
| **HEALTH CHECK** | `curl -f http://127.0.0.1:8000/health` | `python -c "import httpx; print(httpx.get('http://127.0.0.1:8000/health').json())"` |
| **RUN SMOKE TEST** | `python scripts/run_local_saas_smoke_test.py` | Automated 23-step local user journey |
| **DEV DATABASE RESET** | `python scripts/reset_dev_database.py --confirm` | Safely purges mutable storage; baseline protected |
| **RUN REGRESSION** | `pytest tests/` | `npm test` (in `frontend/`) |
| **STOP DOCKER STACK** | `docker compose down` | `Ctrl+C` in native terminal windows |

---

## 2. Native Multi-Terminal Startup Workflow

For local demonstration and development without Docker, use two terminal sessions:

### Terminal 1: FastAPI Backend
```bash
# In repository root
venv\Scripts\activate
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```
*Backend is accessible at:* `http://127.0.0.1:8000`  
*Swagger Documentation:* `http://127.0.0.1:8000/docs`

### Terminal 2: Next.js Frontend
```bash
cd frontend
npm run dev
```
*Frontend is accessible at:* `http://localhost:3000`

---

## 3. Asynchronous Worker & Scheduler Execution

The background workers and scheduled monitoring daemons can be triggered out-of-band:

### Trigger Background Worker Cycle
Evaluates pending alert rules, processes queued notifications, and compiles user digests:
```bash
python scripts/start_local_saas.py --run-worker-once
```

### Trigger Background Monitoring Scheduler Cycle
Polls all registered legislative sources (3 Central, 4 State pilot portals) under distributed lock safeguards:
```bash
python scripts/start_local_saas.py --run-scheduler-once
```

---

## 4. Docker Compose Startup (Optional Containerized Stack)

If Docker is installed on the host system:

```bash
# Start all 6 services in the foreground
docker compose up

# Or start in detached background mode
docker compose up -d

# Check service container logs
docker compose logs -f api
docker compose logs -f frontend

# Gracefully stop the stack
docker compose down
```

---

## 5. Development Database Reset Procedure

When re-testing clean onboarding or creating fresh demonstration tenants, use the safe reset script:

```bash
python scripts/reset_dev_database.py --confirm
```

### Safety Guarantees of `reset_dev_database.py`:
1. **Pre-Reset Check:** Runs `BaselineVerifier` before executing any deletions. If analytical baseline is corrupted, reset halts immediately.
2. **Targeted Purge:** Only clears mutable user tables (`users`, `tenants`, `watchlists`, `alerts`, `notifications`, `audit_logs`).
3. **Immutable Analytical Protection:** Never deletes or alters `data/analytical/` or `data/state_legislation/`.
4. **Post-Reset Verification:** Re-verifies all 4,700 predictions, 4,700 decisions, 940 anticipation scores, and 44 State bills to guarantee zero mutation.

---

## 6. Local Health & Readiness Verification

Run the following HTTP checks from PowerShell or terminal to inspect stack health:

```bash
# Liveness probe
curl http://127.0.0.1:8000/health

# Readiness probe (inspects storage, cache, and baseline integrity)
curl http://127.0.0.1:8000/api/v1/system/readiness

# Monitoring source registry status
curl http://127.0.0.1:8000/api/v1/monitoring/sources
```
