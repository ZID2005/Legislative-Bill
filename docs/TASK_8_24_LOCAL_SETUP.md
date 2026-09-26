# TASK 8.24 — Local SaaS Setup & Installation Guide

**Milestone:** TASK 8.24  
**Classification:** Local Developer & Evaluator Setup Guide  
**Target Environment:** Local Workstation (Windows / macOS / Linux)  
**AWS Dependencies:** ZERO (Strictly Local)  

---

## 1. Prerequisites

Before installing and running the SaaS platform locally, ensure your system has the following runtimes installed:

| Requirement | Minimum Version | Tested Version | Purpose |
|---|---|---|---|
| **Python** | 3.11+ | 3.14.x / 3.12.x | Backend API, ML Models, Worker, Scheduler |
| **Node.js** | 18.0.0+ | 22.x | Next.js 16 Web Frontend |
| **npm** | 9.0.0+ | 10.x | Frontend Package Manager |
| **Git** | 2.30+ | 2.40+ | Version Control |
| **Docker & Docker Compose** | *(Optional)* | 24.x+ | Optional containerized Postgres & Redis |

> **Note:** Docker is completely optional. When Docker is not available or not running, the application automatically uses high-performance, thread-safe, local development storage providers (`DevelopmentDatabaseProvider` and `DevelopmentCacheProvider`).

---

## 2. Step-by-Step Installation

### Step 2.1: Clone the Repository
```bash
git clone <repository-url>
cd Legislative-bill
```

### Step 2.2: Setup Python Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS (bash/zsh)
python3 -m venv venv
source venv/bin/activate
```

### Step 2.3: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2.4: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 3. Environment Configuration

The local SaaS platform comes with turnkey configuration templates designed for zero-config local startup:

### Step 3.1: Configure Backend Environment
Copy the development environment template:
```bash
# Windows
copy .env.development.example .env

# Linux / macOS
cp .env.development.example .env
```

Key local settings in `.env`:
```ini
APP_ENV=development
API_PORT=8000
ALLOW_DEV_AUTH=true
DATABASE_URL=sqlite:///./data/storage/saas_dev.db
REDIS_URL=redis://localhost:6379/0
GROQ_API_KEY=
```

### Step 3.2: Configure Frontend Environment
```bash
# Windows
copy frontend\.env.local.example frontend\.env.local

# Linux / macOS
cp frontend/.env.local.example frontend/.env.local
```

Key frontend setting:
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 4. Pre-Flight Diagnostic Verification

Verify that your local system satisfies all requirements and data integrity constraints before starting servers:

```bash
python scripts/start_local_saas.py --check-only
```

Expected output:
```text
======================================================================
TASK 8.24 — LOCAL SAAS PRE-FLIGHT DIAGNOSTIC
======================================================================
[PASS] Environment Contract      : Mode=development, Port=8000, DevAuth=True
[PASS] Frozen Analytical Baseline: Central=20/4700/4700/14100, State=44/0/0/0, Unified=66/70/104
[PASS] Storage Subsystem         : Local storage directory initialized (data/storage)
[PASS] Cache Subsystem           : Development cache provider active (in-memory)
[PASS] Frontend Dependency Tree  : Next.js installed and dependencies present
======================================================================
PRE-FLIGHT STATUS: READY FOR LOCAL STARTUP
======================================================================
```

---

## 5. Troubleshooting & FAQ

### Port Conflicts
- **Port 8000 in use:** Modify `API_PORT=8001` in `.env` and `NEXT_PUBLIC_API_URL=http://localhost:8001` in `frontend/.env.local`.
- **Port 3000 in use:** Start Next.js with `npm run dev -- -p 3001` or `npm run start -- -p 3001`.

### Data Reset Safe Mode
- To reset local user accounts, watchlists, and alert preferences without touching the frozen analytical dataset:
  ```bash
  python scripts/reset_dev_database.py --confirm
  ```
- This command executes pre- and post-reset verifications of the frozen baseline to guarantee 100% analytical immutability.
