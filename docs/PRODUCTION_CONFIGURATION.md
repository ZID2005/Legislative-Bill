# Production Configuration Specification & Secrets Contract

**Milestone**: TASK 8.20  
**Status**: APPROVED ARCHITECTURE  
**Target Environment**: SaaS Cloud Architecture  

---

## 1. Architectural Principles

1. **Strict Immutability of Frozen Analytical Baselines**:
   No configuration changes, database migrations, or environment overrides may alter Central prediction models, event study windows `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`, or the State/Intelligence Prediction Firewalls.
2. **Zero Credentials in Git / Code / Logs / API**:
   Credentials must never be hard-coded, checked into Git, printed in stdout/stderr, written to file logs, or returned in API responses.
3. **Graceful Fallback & Honest Status Reporting**:
   If external infrastructure is not configured (e.g. absent Redis, PostgreSQL, SMTP, or Stripe keys), the application explicitly reports `STATUS = NOT_CONFIGURED`. Under no circumstances are mock credentials or synthetic statuses fabricated.
4. **Environment Categorization**:
   Every environment variable is classified into one of four tiers:
   - `REQUIRED_IN_DEVELOPMENT`
   - `REQUIRED_IN_STAGING`
   - `REQUIRED_IN_PRODUCTION`
   - `OPTIONAL`

---

## 2. Environment Variables Matrix

| Domain | Variable | Classification | Default Value | Description & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **APPLICATION** | `ENV` | REQUIRED_IN_ALL | `development` | Deployment environment: `development`, `staging`, `production`. |
| **APPLICATION** | `APP_NAME` | REQUIRED_IN_DEV | `LegislativeIntelligence` | Service name identifier. |
| **APPLICATION** | `APP_PORT` | REQUIRED_IN_ALL | `8000` | Port for FastAPI application. |
| **APPLICATION** | `FRONTEND_URL` | REQUIRED_IN_STAGING | `http://localhost:3000` | Public URL of Next.js frontend for CORS and redirects. |
| **APPLICATION** | `JOB_EXECUTION_MODE` | REQUIRED_IN_PROD | `single_instance` | `single_instance`, `multi_instance`, `worker`, `scheduler`. |
| **SECURITY** | `SECRET_KEY` | REQUIRED_IN_PROD | (auto-generated in dev) | Cryptographic signing secret (min 32 bytes). |
| **SECURITY** | `SESSION_COOKIE_NAME` | REQUIRED_IN_DEV | `legis_saas_session` | Name of session cookie. |
| **SECURITY** | `CSRF_SECRET` | REQUIRED_IN_PROD | (auto-generated in dev) | Double-submit CSRF token secret. |
| **SECURITY** | `API_CORS_ORIGINS` | REQUIRED_IN_PROD | `http://localhost:3000,...` | Comma-delimited list of allowed origin URLs. |
| **SECURITY** | `RATE_LIMIT_ENABLED` | REQUIRED_IN_PROD | `false` | Enable sliding window rate limiting. |
| **AUTH** | `JWT_SECRET_KEY` | REQUIRED_IN_PROD | `legis_saas_default_...` | HMAC-SHA256 session token secret. |
| **AUTH** | `JWT_ALGORITHM` | REQUIRED_IN_PROD | `HS256` | Algorithmic token signing header. |
| **AUTH** | `JWT_EXPIRATION_SECONDS` | REQUIRED_IN_PROD | `86400` | Token TTL (default 24 hours). |
| **AUTH** | `OIDC_ISSUER_URL` | REQUIRED_IN_PROD* | `""` | External IdP Issuer URL (Auth0 / Okta / Google). |
| **AUTH** | `OIDC_AUDIENCE` | REQUIRED_IN_PROD* | `""` | Target API audience identifier. |
| **AUTH** | `OIDC_JWKS_URL` | OPTIONAL | `""` | Key rotation endpoint for public key discovery. |
| **DATABASE** | `DATABASE_URL` | REQUIRED_IN_PROD | `""` | PostgreSQL connection URI (`postgresql://...`). |
| **DATABASE** | `POSTGRES_DB` | REQUIRED_IN_PROD | `legislative_intel` | PostgreSQL target database name. |
| **DATABASE** | `DATABASE_POOL_SIZE`| REQUIRED_IN_PROD | `10` | Maximum persistent connection pool size. |
| **DATABASE** | `DATABASE_TIMEOUT` | REQUIRED_IN_PROD | `10` | Connection timeout in seconds. |
| **REDIS** | `REDIS_URL` | REQUIRED_IN_PROD* | `""` | Redis connection URI for locks & rate limiting. |
| **REDIS** | `REDIS_TIMEOUT` | REQUIRED_IN_PROD* | `2.0` | Socket connect and read timeout in seconds. |
| **EMAIL** | `EMAIL_PROVIDER` | REQUIRED_IN_PROD* | `smtp` | Outbound email driver (`smtp`, `sendgrid`, `resend`). |
| **EMAIL** | `SMTP_HOST` | REQUIRED_IN_PROD* | `""` | Hostname of SMTP server. |
| **EMAIL** | `SMTP_PORT` | REQUIRED_IN_PROD* | `587` | Port for SMTP (STARTTLS). |
| **EMAIL** | `SMTP_USER` | REQUIRED_IN_PROD* | `""` | Authenticated username for SMTP. |
| **EMAIL** | `SMTP_PASSWORD` | REQUIRED_IN_PROD* | `""` | Password for SMTP. |
| **EMAIL** | `SENDER_EMAIL` | REQUIRED_IN_PROD* | `notifications@...` | Verified sending email address. |
| **BILLING** | `BILLING_PROVIDER` | OPTIONAL | `stripe` | Payment provider (`stripe`, `razorpay`). |
| **BILLING** | `STRIPE_SECRET_KEY`| OPTIONAL | `""` | Stripe secret API key (`sk_live_...`). |
| **BILLING** | `STRIPE_WEBHOOK_SECRET`| OPTIONAL | `""` | Stripe webhook signing secret (`whsec_...`). |
| **AI** | `GROQ_API_KEY` | OPTIONAL | `""` | Groq Cloud API key (`gsk_...`). |
| **AI** | `GROQ_MODEL` | OPTIONAL | `llama-3.3-70b-versatile` | LLM model checkpoint. |
| **MONITORING**| `LEGISLATIVE_MONITOR_ENABLED` | REQUIRED_IN_PROD | `false` | Autonomous legislative scraping scheduler flag. |
| **MONITORING**| `CENTRAL_MONITOR_INTERVAL` | REQUIRED_IN_PROD | `24` | Central Parliament checking interval (hours). |
| **MONITORING**| `STATE_MONITOR_INTERVAL` | REQUIRED_IN_PROD | `48` | State Legislature checking interval (hours). |

*\*Notes: If external services (OIDC, Redis, SMTP, Stripe) are unconfigured in production, corresponding subsystems operate in safe fallback mode without blocking core platform startup.*

---

## 3. Secret Redaction & Sanitization Guarantees

1. **Logging Redaction**:
   All log handlers pipe through `RedactingFilter` in `config/logging_config.py`. Regex patterns automatically replace Bearer tokens, passwords, private keys, and API keys with `[REDACTED]`.
2. **API Response Sanitization**:
   The `/ready`, `/health`, and `/api/v1/monitoring/*` endpoints never echo secret values or host filesystem absolute paths.
3. **Startup Pre-Flight Diagnostic**:
   `StartupValidator` validates string patterns (e.g. verifying that a key is non-empty and non-placeholder) without printing the actual key characters in stdout or logs.
