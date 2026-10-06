# Local Development & Release Runbook

**Document:** Local Development Runbook  
**Milestone:** TASK 8.30  
**Stack:** FastAPI (Python 3.13) + Next.js 16 (TypeScript) + TailwindCSS/Vanilla CSS  
**Target Environment:** Localhost / Self-Contained SaaS  

---

## 1. Quick Start

### 1.1 Prerequisites
- Python 3.11+ (Python 3.13 recommended)
- Node.js 18+ (Node 20+ recommended)
- Git

### 1.2 Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*Note: In development, local file-backed JSON repositories and mock providers operate automatically. No external cloud credentials (AWS, Stripe, Groq) are required to boot the application.*

---

## 2. Running the Application Locally

### 2.1 Backend (FastAPI)
From the repository root:
```bash
python3 -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/api/v1/health`

### 2.2 Frontend (Next.js)
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
- Web Application: `http://localhost:3000`

---

## 3. Running Test Suites

### 3.1 Milestone & Regression Test Suites
Run the full targeted regression and validation suite:
```bash
python3 -m pytest \
  tests/test_task_8_30_final_validation.py \
  tests/test_task_8_29_anticipation_evidence.py \
  tests/test_task_8_28_decision_intelligence.py \
  tests/test_task_8_27_dossier.py \
  tests/test_task_8_26_live_intelligence.py \
  tests/test_security_idor.py \
  tests/test_security_headers_ratelimit.py \
  tests/test_saas_auth_lifecycle.py
```
*Expected: 151 / 151 PASSED.*

### 3.2 Frontend Unit Tests & Build Verification
From the `frontend/` directory:
```bash
# Vitest unit test suite (205 tests)
npm run test

# TypeScript type checking (0 errors)
npm run typecheck

# Production build verification (all routes pre-rendered)
npm run build
```

### 3.3 End-to-End Local Smoke Test
While both backend and frontend are running:
```bash
python3 scripts/run_local_saas_smoke_test.py
```
*Executes the complete 23-step critical user journey from login to AI grounding and logout revocation.*

---

## 4. Architectural Invariants & Epistemic Rules

1. **Frozen Baseline:**
   - Manifest path: `docs/production_baseline.json`
   - Authoritative SHA-256: `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`
   - NEVER alter baseline model weights, prediction counts, or event horizons.
2. **State Bill Firewall:**
   - State-level stock price predictions remain strictly **0**.
   - State bills provide qualitative sector intelligence, employment dimensions, and corporate operational exposures only.
3. **Decoupled Anticipation Evidence:**
   - Econometric market signals (CAR magnitude, z-score) are strictly decoupled from public information evidence (news, parliamentary bulletins).
   - No causal linkages or allegations of insider trading are ever inferred or generated.
4. **Cloud Status:**
   - AWS deployment remains strictly `FUTURE`. Localhost / on-premise SaaS is the release target.
