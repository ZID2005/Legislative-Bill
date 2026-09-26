# TASK 8.23 — Production Security Hardening Specification

**Status**: AUTHORITATIVE / TESTED — UPDATED BY TASK 8.23A  
**Date**: September 2026  
**Application Code Status**: READY  
**Cloud Deployment Status**: BLOCKED_BY_CREDENTIALS  

---

## 1. Overview & Threat Model

The platform enforces multi-layered defense-in-depth across the API boundary, authentication pipeline, tenant tenancy isolation, log telemetry, and database interactions.

```
[ Inbound Client Request ]
           │
           ▼
[ CloudFront / ALB / Reverse Proxy ]
  ├── TLS 1.3 Termination
  └── WAF Protection
           │
           ▼
[ FastAPI Middleware Stack ]
  ├── Security Headers Middleware (HSTS, CSP, X-Frame-Options, etc.)
  ├── CORS Middleware (Strict Origin Allowlist)
  ├── Rate Limiter (Per-IP / Per-Tenant Sliding Window)
  └── Request ID / Correlation Tracker
           │
           ▼
[ Authentication & Authorization Layer ]
  ├── JWT Signature & Expiration Verification
  ├── Multi-Tenant Isolation & Ownership Validator (IDOR Prevention)
  └── Role-Based Access Control (RBAC)
           │
           ▼
[ Pydantic Request Validation & SQL Injection Firewall ]
           │
           ▼
[ Application Core & Logging with RedactingFilter ]
```

---

## 2. Security Controls & Implementations

### 2.1 JWT Authentication & Token Security
- **Algorithm**: HMAC-SHA256 (`HS256`) or RS256 for OIDC.
- **Claims Verification**:
  - `exp`: Strict expiration enforcement; clock skew tolerance $\le 10$ seconds.
  - `iat`: Issued-at validation; tokens issued in the future are rejected.
  - `tenant_id`: Mandatory claim for all authenticated requests.
  - `user_id`: Mandatory claim.
- **Rejection Tests**:
  - Malformed tokens: Rejected with HTTP 401 Unauthorized.
  - Expired tokens: Rejected with HTTP 401.
  - Forged / incorrect secret signature: Rejected with HTTP 401.
  - Missing claims: Rejected with HTTP 401.

### 2.2 IDOR Prevention & Multi-Tenant Isolation
- **Tenant Context Scoping**: Every database entity (alerts, bookmarks, notification preferences, billing records) contains a `tenant_id` foreign key.
- **Ownership Verification**:
  - API routers resolve `current_user` from the authenticated session.
  - Query filters strictly inject `WHERE tenant_id = :current_user.tenant_id`.
  - Resource access across tenant boundaries is rejected with HTTP 403 Forbidden.
  - Verified by `tests/test_operational_hardening_chaos.py` (Scenario 10).

### 2.3 Strict CORS Configuration
- **Allowed Origins**: Configured via `CORS_ORIGINS` environment variable (defaults to trusted frontend domains, e.g., `https://app.legislativeplatform.com` and `http://localhost:3000` in dev).
- **Wildcard Rejection**: `*` origin is strictly forbidden when credentials (`allow_credentials=True`) are enabled.
- **Allowed Methods**: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`.
- **Allowed Headers**: `Authorization`, `Content-Type`, `X-Request-ID`, `X-Tenant-ID`.
- **Exposed Headers**: `X-Request-ID`, `Retry-After`.

### 2.4 HTTP Security Headers
All HTTP responses from the FastAPI application include the following headers:
```http
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
Content-Security-Policy: default-src 'self'; img-src 'self' data: https:; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';
```

### 2.5 Sensitive Data Redaction in Logging (`config/logging_config.py`)
All log records pass through the deterministic `RedactingFilter`:
- **Bearer Tokens**: `Bearer [REDACTED_TOKEN]`
- **JWTs**: `[REDACTED_JWT]` (detects `eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+`)
- **API Keys**: `[REDACTED_API_KEY]` (detects Groq `gsk_...`, Stripe `sk_...`, general 32+ char hex/base64 keys)
- **Passwords**: `password="[REDACTED]"` and unquoted CLI passwords
- **Connection Strings**: `postgresql://[REDACTED]@...` and `redis://[REDACTED]@...`
- **Application**: Applied to console handler, rotating file handler, and Celery worker loggers.

### 2.6 Rate Limiting & Throttling
- **Algorithm**: Sliding window counter.
- **Granularity**: Dual-keyed on Client IP and Tenant ID.
- **Tiers**:
  - Free / Anonymous: 60 requests / minute.
  - Standard Tenant: 300 requests / minute.
  - Enterprise Tenant: 1,200 requests / minute.
- **Degradation**: If Redis is offline, rate limiter falls back to in-memory sliding window cache.

### 2.7 Distributed Scheduler Safety (Task 8.23A)
- When Redis is unavailable in production distributed mode (`multi_instance`/`worker`/`scheduler`):
  - The scheduler **FAILS CLOSED** — execution is DEFERRED, not substituted with a local process lock.
  - A structured `SCHEDULER_DEFERRED` event is logged with `local_lock_substituted=False`.
  - `scheduler_degraded=True` is exposed in scheduler health status.
- A process-level thread lock is permitted ONLY in `single_instance` (local/dev/test) mode.
- **Critical invariant**: `REDIS_UNAVAILABLE + MULTI_CONTAINER_PRODUCTION_MODE => SCHEDULER_EXECUTION_COUNT == 0`

### 2.7 Input Validation & Injection Defense
- **Pydantic V2**: Strict schema validation on all incoming request bodies, query parameters, and path arguments.
- **SQL Injection Defense**: 100% parameterized queries via SQLAlchemy 2.0 ORM and Core; zero raw string concatenation in SQL expressions.
- **Analytical Baseline Shield**: `data/` directory is treated as read-only by the application runtime; writes are strictly forbidden outside specific migration/data generation scripts.

### 2.8 Secret & Credential Management
- Zero hardcoded passwords, tokens, or encryption keys in source control.
- Configuration strictly read from environment variables via `pydantic-settings` (`config/settings.py`).
- Production deployment utilizes AWS Secrets Manager / Parameter Store with KMS customer-managed keys.
