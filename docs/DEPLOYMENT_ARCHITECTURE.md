# Cloud SaaS Deployment Architecture Specification

**Milestone**: TASK 8.20  
**Scope**: Production SaaS Infrastructure & Service Integration Topology  
**Analytical Invariants**: Strict Immutability of Central and State Baselines  

---

## 1. High-Level Architecture Topology

```
+-----------------------------------------------------------------------------------+
|                                 USER CLIENTS                                      |
|            Desktop Browsers / Institutional Risk Teams / Policy Analysts          |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ HTTPS / WSS
+-----------------------------------------------------------------------------------+
|                        EDGE / INGRESS & REVERSE PROXY                             |
|               Cloudflare / AWS ALB / NGINX (TLS Termination, DDoS Guard)           |
+-----------------------------------------------------------------------------------+
                  │                                                 │
                  ▼                                                 ▼
+------------------------------------+           +----------------------------------+
|          NEXT.JS FRONTEND          |           |            FASTAPI API           |
|      (Node.js 20 Alpine Runner)    |           |    (Uvicorn Multi-Worker ASGI)   |
|   Stateless Client Application     |──────────►|  Stateless REST & Copilot Engine |
|   Container: legis_frontend:3000   |   HTTP    |   Container: legis_api:8000      |
+------------------------------------+           +----------------------------------+
                                                                │
                     ┌──────────────────────────────────────────┴─────────────────────────┐
                     ▼                                                                    ▼
+------------------------------------------+                     +------------------------------------------+
|          POSTGRESQL DATABASE             |                     |               REDIS CLUSTER              |
|        (Managed PostgreSQL 16)           |                     |          (Managed Redis 7 Engine)        |
|  Tenant-Owned Mutable Data & RBAC        |                     |  Distributed Locks, Sliding Rate Limits, |
|  Container: legis_postgres:5432          |                     |  Session Blacklist & Query Caching       |
+------------------------------------------+                     +------------------------------------------+
                     ▲                                                                    ▲
                     │                                                                    │
                     └──────────────────────────┬─────────────────────────────────────────┘
                                                │
                     ┌──────────────────────────┴─────────────────────────┐
                     ▼                                                    ▼
+------------------------------------------+     +------------------------------------------+
|            BACKGROUND WORKER             |     |           RECURRING SCHEDULER            |
|       (Python Background Process)        |     |        (Clock Daemon with Locks)         |
|  Alert Evaluation, Notification Dispatch,|     |  Periodic Source Checking, Daily Digest  |
|  Transactional Email Delivery            |     |  Aggregation, Maintenance Dispatch       |
|  Container: legis_worker                 |     |  Container: legis_scheduler              |
+------------------------------------------+     +------------------------------------------+
```

---

## 2. Component Inventory & Operational Status

Each component is classified with its exact operational status based on empirical evidence:

| Component | Architecture Role | Readiness Status | Configuration Status | Deployment Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Next.js Frontend** | Institutional Web UI | **READY** | **CONFIGURED** | **STAGING_READY** | Fully built, 180 Vitest unit/page tests passing, TypeScript strictly clean. |
| **FastAPI Backend** | Core Analytical & Multi-Tenant API | **READY** | **CONFIGURED** | **STAGING_READY** | 97 unique routes, 108 endpoints, lifespan startup validator active. |
| **PostgreSQL** | Tenant Data Persistence | **READY** | **NOT_CONFIGURED** | **STAGING_READY** | Architecture, schema DDL, and migrations designed; local dev uses file-backed JSON. |
| **Redis** | Distributed Lock & Rate Limiting | **READY** | **NOT_CONFIGURED** | **STAGING_READY** | Distributed lock & token revocation interface implemented; dev uses thread-safe in-memory cache. |
| **Background Worker** | Async Alert & Delivery Processor | **READY** | **CONFIGURED** | **STAGING_READY** | Dedicated worker runner with lock coordination in `scripts/run_worker.py`. |
| **Recurring Scheduler**| Periodic Source Check & Digests | **READY** | **CONFIGURED** | **STAGING_READY** | Dedicated scheduler with distributed lock in `scripts/run_scheduler.py`. |

---

## 3. External Integration Boundaries

| External Integration | Target Provider(s) | Status | Behavioral Fallback When Unconfigured |
| :--- | :--- | :--- | :--- |
| **External IdP (SSO)** | Auth0, Okta, Google OIDC | **NOT_CONFIGURED** | Cryptographically signed internal JWT tokens (`create_session_token`) active; header spoofing strictly rejected. |
| **Transactional Email** | SMTP, SendGrid, Resend | **NOT_CONFIGURED** | Safe `DevelopmentEmailProvider` records messages in memory without external network egress. |
| **Groq AI Provider** | Groq Cloud (Llama 3.3 70B) | **NOT_CONFIGURED** | Offline extractive citation-backed copilot active; zero financial or political recommendations. |
| **Billing Gateway** | Stripe, Razorpay | **NOT_CONFIGURED** | Provider-neutral `DevelopmentBillingProvider` manages customer creation and plan entitlements without live charging. |
| **Official Sources** | Lok Sabha, Rajya Sabha, PRS, 4 State Portals | **CONFIGURED** (7 implemented, 5 planned) | Read-only scraping with deduplication; State Prediction Firewall guarantees 0 state stock predictions. |

---

## 4. Execution Modes

1. **Single-Instance Mode** (`JOB_EXECUTION_MODE=single_instance`):
   Standard development and small-scale self-hosted deployments. Web server, background jobs, and scheduler operate within the same process lifecycle or adjacent threads.
2. **Multi-Instance Mode** (`JOB_EXECUTION_MODE=multi_instance`):
   Horizontally replicated web API instances behind a load balancer. Redis distributed locking (`SETNX`) guarantees that scheduled checks and alert processing never execute concurrently across nodes.
3. **Worker Mode** (`JOB_EXECUTION_MODE=worker`):
   Dedicated compute worker containers (`Dockerfile.worker`) consuming background tasks independently of the web API.
4. **Scheduler Mode** (`JOB_EXECUTION_MODE=scheduler`):
   Single clock process (`Dockerfile.scheduler`) firing periodic cron ticks for legislative monitoring, digest aggregation, and cache invalidation.
