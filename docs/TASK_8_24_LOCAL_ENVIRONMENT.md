# TASK 8.24 — Local Environment Contract & Configuration Specification

**Milestone:** TASK 8.24  
**Classification:** Operational Environment Contract & Configuration Dictionary  
**Target Environments:** DEVELOPMENT | TEST | STAGING/SELF-HOSTED | CLOUD PRODUCTION  

---

## 1. Environment Tiers & Lifecycle Contracts

The platform explicitly distinguishes four deployment tiers to prevent accidental bypasses, mock data leaks, or cloud mutations:

| Environment Tier (`APP_ENV`) | Description | Auth Boundary | Storage Provider | Cache Provider | Analytical State |
|---|---|---|---|---|---|
| `development` (LOCAL) | Local engineer workstation / FYP demo | HMAC Dev Auth (`ALLOW_DEV_AUTH=True`) | Local JSON / Postgres | In-Memory / Redis | Frozen Analytical (Read-Only) |
| `test` (CI / AUTOMATION) | Pytest and Vitest test suites | Mock Auth & TestClient Injections | Ephemeral In-Memory | Ephemeral In-Memory | Frozen Analytical (Read-Only) |
| `staging` (SELF-HOSTED) | Private VPC or On-Premise staging | OIDC Enterprise Auth / SAML | Dedicated PostgreSQL | Dedicated Redis Cluster | Frozen Analytical (Read-Only) |
| `production` (CLOUD) | Future multi-region AWS cloud rollout | AWS Cognito / Okta OIDC | Amazon Aurora Serverless | Amazon ElastiCache Redis | Frozen Analytical (Read-Only) |

---

## 2. Configuration Dictionary

### 2.1. Core Application Settings
| Variable | Type | Default | Required in Dev | Description |
|---|---|---|---|---|
| `APP_ENV` | String | `development` | Yes | Target runtime environment (`development`, `test`, `staging`, `production`). |
| `APP_NAME` | String | `Legislative Intelligence SaaS` | No | System branding and logging identifier. |
| `LOG_LEVEL` | String | `INFO` | No | Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `API_PORT` | Integer | `8000` | No | Local HTTP listen port for FastAPI. |
| `API_HOST` | String | `127.0.0.1` | No | Local interface binding. |

### 2.2. Authentication & Tenant Security
| Variable | Type | Default | Required in Dev | Description |
|---|---|---|---|---|
| `ALLOW_DEV_AUTH` | Boolean | `true` | Yes | Enables local `/api/v1/auth/login` token generation. **STRICTLY PROHIBITED IN PRODUCTION.** |
| `SECRET_KEY` | String | `dev-local-secret-do-not-use-in-production-32bytes` | Yes | Signing key for HMAC-SHA256 session tokens. |
| `TOKEN_EXPIRE_MINUTES`| Integer | `1440` | No | Token lifetime (24 hours in dev). |

### 2.3. Storage & Cache Layers
| Variable | Type | Default | Required in Dev | Description |
|---|---|---|---|---|
| `DATABASE_URL` | String | `sqlite:///./data/storage/saas_dev.db` | No | PostgreSQL or local SQLite/JSON storage connection URI. |
| `REDIS_URL` | String | `redis://localhost:6379/0` | No | Redis connection URI for distributed cache & locks. |
| `SCHEDULER_DISTRIBUTED_LOCK` | Boolean | `false` (in dev) / `true` (in prod) | No | When `true`, enforces Redis fail-closed distributed lock. |

### 2.4. AI & External Intelligence Services
| Variable | Type | Default | Required in Dev | Description |
|---|---|---|---|---|
| `GROQ_API_KEY` | String | *Empty* | Optional | API key for Groq Llama 3 models. When empty, safe grounded heuristic fallback operates automatically. |
| `GROQ_MODEL` | String | `llama3-70b-8192` | No | Target LLM model for grounded legislative synthesis. |

### 2.5. Frontend Client Settings (`frontend/.env.local`)
| Variable | Type | Default | Required in Dev | Description |
|---|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | String | `http://localhost:8000` | Yes | Local FastAPI backend endpoint accessed by Next.js client. |
| `PORT` | Integer | `3000` | No | Next.js local HTTP server port. |

---

## 3. Strict Security & Safety Rules

1. **NO AWS CREDENTIALS IN LOCAL CONFIG:** Under no circumstances should AWS IAM access keys, secret keys, or session tokens be stored in `.env`, `.env.development`, or committed to the repository.
2. **ZERO EXTERNAL SECRETS:** Development configuration relies entirely on local parameters.
3. **PRODUCTION DEV-AUTH FIREWALL:** If `APP_ENV=production` and `ALLOW_DEV_AUTH=true`, the FastAPI application startup raises an unrecoverable `RuntimeError` and terminates immediately.
4. **STRICT IMMUTABILITY OF FROZEN ANALYTICAL DATA:** All analytical artifacts in `data/analytical/` and `data/state_legislation/` are treated as read-only code constants. Mutable user preferences, watchlists, and alerts reside exclusively in `data/storage/`.
