# TASK 8.24 — Local SaaS Platform Architecture

**Milestone:** TASK 8.24  
**Classification:** Local Production-Like SaaS Integration & Demonstration Architecture  
**Date:** September 2026  
**Status:** APPROVED / PRODUCTION-READY FOR LOCAL DEPLOYMENT  

---

## 1. Executive Summary

This document specifies the authoritative multi-tier architecture of the Legislative Intelligence SaaS platform when executed in a local development, demonstration, or evaluation environment. 

The primary objective of Milestone 8.24 is to provide a complete, reliable, and production-like SaaS system running entirely on a local workstation without dependencies on AWS credentials, cloud infrastructure, or external paid services.

---

## 2. Multi-Tier Local System Topology

The local platform is structured into five distinct operational tiers:

```
[ Browser / Client ]
        │  HTTP / HTTPS (Port 3000)
        ▼
┌────────────────────────────────────────────────────────┐
│  Tier 1: Next.js 16 Web Application                     │
│  - App Router / React Server Components                │
│  - Modern Glassmorphic Dark UI (Tailored HSL)          │
│  - Client-Side Auth Cookie / Token Store               │
│  - Proxies / Communicates via NEXT_PUBLIC_API_URL       │
└────────────────────────────────────────────────────────┘
        │  REST API / Bearer Auth (Port 8000)
        ▼
┌────────────────────────────────────────────────────────┐
│  Tier 2: FastAPI Application Gateway                    │
│  - REST API Engine (Uvicorn ASGI)                      │
│  - Development & Production Auth Middleware            │
│  - Tenant Context Injection (X-Tenant-ID / Token)      │
│  - CORS & Security Boundary Enforcement               │
│  - State Prediction Firewall & Company Firewall        │
│  - Grounded AI Engine (with safe heuristic fallback)   │
└────────────────────────────────────────────────────────┘
        │                               │
        ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│ Tier 3A: Storage Layer     │   │ Tier 3B: Cache & Locks    │
│ - PostgreSQL (Docker) OR  │   │ - Redis 7 (Docker) OR     │
│ - Development JSON Store  │   │ - Thread-Safe In-Memory   │
│   (data/storage/ & data/) │   │   Cache Provider          │
│ - FROZEN Analytical Data  │   │ - Fail-Closed Distributed │
│   (Read-Only Artifacts)   │   │   Scheduler Locks         │
└───────────────────────────┘   └───────────────────────────┘
        │                               ▲
        ▼                               │
┌────────────────────────────────────────────────────────┐
│  Tier 4: Background Worker System                      │
│  - Asynchronous Task Queue Consumer                    │
│  - Alert Evaluation & Digest Generation                │
│  - Notification Delivery Engine                        │
│  - Non-blocking Out-of-Band Work Execution             │
└────────────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────┐
│  Tier 5: Background Scheduler System                   │
│  - Distributed Cron & Polling Daemon                   │
│  - Source Registry Monitoring (3 Central, 4 State)     │
│  - Strict Fail-Closed Lock Verification                │
│  - Non-mutating Provenance Discovery                   │
└────────────────────────────────────────────────────────┘
```

---

## 3. Component & Port Allocations

| Component | Default Port | Internal Protocol | Environment Variable Override | Local Fallback Provider |
|---|---|---|---|---|
| **Frontend** (Next.js) | `3000` | HTTP / HTML / JSON | `PORT=3000` | Node.js / Next Dev/Prod Server |
| **Backend** (FastAPI) | `8000` | HTTP / REST JSON | `API_PORT=8000`, `PORT=8000` | Python Uvicorn ASGI Server |
| **Database** (PostgreSQL) | `5432` | PostgreSQL Wire | `DATABASE_URL` | `DevelopmentDatabaseProvider` (local JSON store) |
| **Cache & Locks** (Redis) | `6379` | RESP / Redis Protocol | `REDIS_URL` | `DevelopmentCacheProvider` (thread-safe in-memory) |
| **Worker Engine** | N/A (Process) | Async Task Protocol | `TASK_QUEUE_MODE` | In-process asyncio task runner |
| **Scheduler Engine** | N/A (Process) | Distributed Poller | `SCHEDULER_DISTRIBUTED_LOCK` | Distributed Redis lock with strict fail-closed |

---

## 4. Architectural Boundaries & Firewalls

### 4.1. Authentication & Tenant Isolation Boundary
- **Development Mode (`ALLOW_DEV_AUTH=True`):** In local environments, users authenticate via `/api/v1/auth/login` using credentials or mock enterprise identity. A signed HMAC-SHA256 JWT is issued containing `sub`, `tenant_id`, `role`, and `exp`.
- **Tenant Context (`TenantContextMiddleware`):** Every incoming request is scoped to a specific tenant. Cross-tenant access to private watchlists, alert rules, or audit trails returns `403 Forbidden` or `404 Not Found`.
- **Session Revocation:** Logout explicitly invalidates session tokens in the cache layer; subsequent requests with revoked tokens immediately return `401 Unauthorized`.

### 4.2. State Prediction Firewall (`StatePredictionFirewall`)
- **Authoritative Rule:** State legislation is strictly qualitative and policy-focused. **Zero stock predictions are ever generated, stored, or returned for State bills.**
- **Endpoint Enforcement:** Calls to `/api/v1/bills/{state_bill_id}/predictions` return:
  ```json
  {
    "bill_id": "{state_bill_id}",
    "has_predictions": false,
    "predictions": [],
    "firewall_status": "STATE_QUALITATIVE_ONLY",
    "reason": "State legislative records are policy/intelligence only. Quantitative market modeling is restricted to Central jurisdiction."
  }
  ```

### 4.3. Intelligence Company Firewall (`IntelligenceCompanyFirewall`)
- **Authoritative Rule:** Unlisted, startup, or qualitative entities (e.g. Swiggy, Zepto, Zerodha) remain prediction-ineligible.
- **Endpoint Enforcement:** Calls to `/api/v1/companies/{ineligible_id}/predictions` return:
  ```json
  {
    "company_id": "{ineligible_id}",
    "has_predictions": false,
    "predictions": [],
    "firewall_status": "INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS",
    "reason": "Entity is categorized under qualitative intelligence. Quantitative market return predictions are reserved for listed equity universe."
  }
  ```

### 4.4. Fail-Closed Scheduler Boundary
- When configured in distributed mode, the background scheduler requires a healthy distributed lock in Redis.
- If Redis becomes unavailable, unreachable, or responds with connection timeout, the scheduler **immediately halts execution** (`scheduler execution = 0`).
- Local lock substitution is strictly prohibited in distributed mode to prevent split-brain and duplicate job execution.

---

## 5. Frozen Analytical Data Architecture

The analytical core of the platform is immutable and frozen as of Milestone 8.20.

| Dimension | Scope | Authoritative Count | Local Storage Location |
|---|---|---|---|
| **Central Bills** | Production | 20 bills | `data/analytical/` |
| **Central Scanned** | Total Parsed | 22 records | `data/analytical/` |
| **Central Aux** | Secondary | 2 records | `data/analytical/` |
| **Quantitative Securities** | Equities | 47 securities | `data/analytical/` |
| **Bill-Company Pairs** | Pairs | 940 pairs | `data/analytical/` |
| **Stock Predictions** | Multi-Horizon | 4,700 predictions | `data/analytical/predictions.json` |
| **Trading Decisions** | Prescriptive | 4,700 decisions | `data/analytical/decisions.json` |
| **Anticipation Scores** | Early Signals | 940 records | `data/analytical/anticipation.json` |
| **Stakeholder Reports** | Triple Perspective | 14,100 reports | `data/analytical/stakeholder_reports.json` |
| **State Bills** | 4 Pilot States | 44 bills (AP: 12, KA: 11, KL: 11, TS: 10) | `data/state_legislation/` |
| **State PDFs** | Official Gazettes | 44 PDFs | `data/state_legislation/` |
| **State Knowledge** | Deep Extraction | 44 knowledge records | `data/state_legislation/` |
| **State Exposures** | Corporate Links | 86 exposures | `data/state_legislation/` |
| **State Predictions** | Market Models | **0 (Strict Firewall)** | Enforced via software guardrails |
| **Unified Bills** | Central + State | 66 bills | Unified Registry |
| **Unified Companies** | Quant + Intel + Ref | 70 companies (47 + 20 + 3) | Unified Registry |
| **Unified Exposures** | Central + State | 104 corporate exposures | Unified Registry |

---

## 6. Zero AWS Dependency Guarantee

The local SaaS deployment operates with absolute independence from cloud providers:

1. **Zero AWS Credentials Required:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` are completely optional and not loaded or required by the local runtime.
2. **Local Storage:** All assets, PDF gazettes, analytical JSON artifacts, and session data are stored locally in the workspace filesystem.
3. **Local Compute & Networking:** All communications occur across `localhost` (`127.0.0.1`) loops.
4. **Cloud Future Roadmap:** Cloud infrastructure configurations (`terraform/`, `ecs/`, `lambda/`) are reserved for future staging/production rollout and remain inactive during local execution.
