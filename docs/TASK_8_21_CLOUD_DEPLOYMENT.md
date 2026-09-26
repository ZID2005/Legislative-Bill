# TASK 8.21 — Cloud Deployment Architecture

**Milestone**: TASK 8.21  
**Prerequisite**: TASK 8.20 APPROVED ✅  
**Document Purpose**: Selected cloud target, architecture, deployment model, and integration status  
**Analytical System**: STRICTLY FROZEN — IMMUTABLE  

---

## 1. Authoritative Frozen Baseline Verification (Pre-Deployment)

Verified at **2026-09-25T21:33:53+05:30** via `scripts/verify_frozen_baseline_exact.py` (exit code 0):

| Layer | Metric | Target | Verified | Status |
|:------|:-------|:-------|:---------|:-------|
| **Central** | Production Bills | 20 | 20 | ✅ MATCH |
| **Central** | Scanned Records | 22 | 22 | ✅ MATCH |
| **Central** | Auxiliary Records | 2 | 2 | ✅ MATCH |
| **Central** | Quantitative Securities | 47 | 47 | ✅ MATCH |
| **Central** | Bill-Company Pairs | 940 | 940 | ✅ MATCH |
| **Central** | Event-Study Predictions | 4,700 | 4,700 | ✅ MATCH |
| **Central** | Decision Records | 4,700 | 4,700 | ✅ MATCH |
| **Central** | Anticipation Scores | 940 | 940 | ✅ MATCH |
| **Central** | Stakeholder Reports | 14,100 | 14,100 | ✅ MATCH |
| **Central** | Event Horizons | 5 windows | `[-1,+1]`,`[-3,+3]`,`[-5,+5]`,`[-5,+10]`,`[-10,+10]` | ✅ MATCH |
| **State** | Andhra Pradesh | 12 | 12 | ✅ MATCH |
| **State** | Karnataka | 11 | 11 | ✅ MATCH |
| **State** | Kerala | 11 | 11 | ✅ MATCH |
| **State** | Telangana | 10 | 10 | ✅ MATCH |
| **State** | Total Bills | 44 | 44 | ✅ MATCH |
| **State** | Official PDFs | 44 | 44 | ✅ MATCH |
| **State** | Knowledge Records | 44 | 44 | ✅ MATCH |
| **State** | Corporate Exposures | 86 | 86 | ✅ MATCH |
| **State** | Stock Predictions | 0 | 0 | ✅ FIREWALLED |
| **State** | Decision Records | 0 | 0 | ✅ FIREWALLED |
| **State** | Anticipation Scores | 0 | 0 | ✅ FIREWALLED |
| **Unified** | Legislative Records | 66 | 66 | ✅ MATCH |
| **Unified** | Companies | 70 | 70 | ✅ MATCH |
| **Unified** | Quantitative | 47 | 47 | ✅ MATCH |
| **Unified** | Intelligence-Only | 20 | 20 | ✅ MATCH |
| **Unified** | Reference | 3 | 3 | ✅ MATCH |
| **Unified** | Corporate Exposures | 104 | 104 | ✅ MATCH |

**Baseline Result**: ALL VALUES MATCH — Deployment authorized to proceed.

---

## 2. Selected Cloud Target

### Decision: AWS ECS/Fargate — ap-south-1 (Mumbai)

**Rationale for AWS ECS/Fargate:**
1. **Indian Data Residency**: `ap-south-1` (Mumbai) keeps legislative intelligence data within Indian jurisdiction
2. **Serverless Compute**: Fargate eliminates EC2 management overhead for a small-to-mid SaaS
3. **Managed Services**: RDS PostgreSQL, ElastiCache Redis, ACM TLS — all managed within one ecosystem
4. **Native Container Support**: Existing Docker container architecture maps directly to ECS Task Definitions
5. **Cost Efficiency**: Pay-per-task billing suits variable legislative monitoring workloads

**Rejected alternatives:**
- GCP Cloud Run: Less mature managed PostgreSQL in `asia-south1`; different secret management ecosystem
- Azure Container Apps: Higher complexity for Indian-origin startup; Auth0 preferred over Entra
- Kubernetes (EKS/GKE): Over-engineered for current scale; can migrate later if needed
- AWS App Runner: Does not support worker/scheduler separated service pattern needed for distributed locking

---

## 3. Architecture Overview

```
Internet
    │
    ▼
[AWS Route 53 DNS]
    │
    ▼
[AWS ACM TLS Certificate]
    │
    ▼
[AWS ALB — Application Load Balancer]
 public subnets: 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24
    │                    │
    ▼                    ▼
[ECS Fargate]        [ECS Fargate]
[legis-frontend]     [legis-api]
 Port 3000            Port 8000
 2 replicas           2 replicas
    │
    ▼  (internal traffic only)
 private subnets: 10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24
    │                    │                    │
    ▼                    ▼                    ▼
[ECS Fargate]    [AWS RDS PG 15]    [AWS ElastiCache]
[legis-worker]   Multi-AZ           Redis 7.x
[legis-sched.]   Encrypted          Encrypted
1 replica each   Private subnet     Private subnet
```

---

## 4. Cloud Architecture Parameters

### Compute

| Service | Platform | CPU | Memory | Replicas | Port |
|:--------|:---------|:----|:-------|:---------|:-----|
| `legis-api` | ECS Fargate | 1024 (1 vCPU) | 2048 MB | 2 | 8000 |
| `legis-frontend` | ECS Fargate | 512 | 1024 MB | 2 | 3000 |
| `legis-worker` | ECS Fargate | 512 | 1024 MB | 1 | — |
| `legis-scheduler` | ECS Fargate | 256 | 512 MB | **1** | — |

> [!IMPORTANT]
> Scheduler is explicitly limited to **1 replica** to prevent duplicate scheduled job execution. Distributed lock coordination via Redis provides additional safety if this constraint is ever relaxed.

### Region & Availability Zones

- **Region**: `ap-south-1` (Mumbai)
- **AZs**: `ap-south-1a`, `ap-south-1b`, `ap-south-1c`
- **VPC CIDR**: `10.0.0.0/16`

---

## 5. Networking Model

### Subnet Allocation

| Subnet Type | CIDR | AZ | Hosts |
|:-----------|:-----|:---|:------|
| Public (ALB) | `10.0.1.0/24` | `ap-south-1a` | Frontend/API ALB |
| Public (ALB) | `10.0.2.0/24` | `ap-south-1b` | Frontend/API ALB |
| Public (ALB) | `10.0.3.0/24` | `ap-south-1c` | Frontend/API ALB |
| Private (DB) | `10.0.10.0/24` | `ap-south-1a` | RDS, ElastiCache |
| Private (DB) | `10.0.11.0/24` | `ap-south-1b` | RDS, ElastiCache |
| Private (DB) | `10.0.12.0/24` | `ap-south-1c` | RDS, ElastiCache |

### Security Group Rules

```
sg-alb-public:
  Inbound:  0.0.0.0/0:443 (HTTPS), 0.0.0.0/0:80 → redirect
  Outbound: sg-ecs-tasks:8000, sg-ecs-tasks:3000

sg-ecs-tasks:
  Inbound:  sg-alb-public:any
  Outbound: sg-rds:5432, sg-redis:6379, 0.0.0.0/0:443 (external APIs)

sg-rds:
  Inbound:  sg-ecs-tasks:5432
  Outbound: NONE

sg-redis:
  Inbound:  sg-ecs-tasks:6379
  Outbound: NONE
```

---

## 6. Database — AWS RDS PostgreSQL 15.4

| Parameter | Value |
|:----------|:------|
| Engine | PostgreSQL 15.4 |
| Instance Class | `db.t3.medium` |
| Multi-AZ | Yes |
| Storage | 100 GB gp3, encrypted |
| Publicly Accessible | **No** |
| Subnet Group | Private |
| Backup Retention | 7 days |
| Point-in-Time Recovery | Enabled |
| Performance Insights | Enabled |
| Connection Pooling | PgBouncer (ECS sidecar) |
| Database Name | `legislative_intel` |
| Application User | `legis_app` (non-superuser) |
| Superuser | Disabled for application |

### Database User Permissions

```sql
-- Application user (non-superuser)
CREATE USER legis_app WITH PASSWORD '<secret_from_aws_secrets_manager>';
GRANT CONNECT ON DATABASE legislative_intel TO legis_app;
GRANT USAGE ON SCHEMA public TO legis_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO legis_app;

-- Read-only analytical baseline tables
REVOKE INSERT, UPDATE, DELETE ON TABLE
  bills, predictions, decision_records, anticipation_scores,
  stakeholder_reports, event_horizons, state_bills, state_knowledge,
  state_corporate_exposures
FROM legis_app;
```

> [!CAUTION]
> The application user has **no write access** to frozen analytical tables (bills, predictions, etc.). Only the migration user may touch those, and only during explicit, approved migration procedures.

---

## 7. Redis — AWS ElastiCache Redis 7.x

| Parameter | Value |
|:----------|:------|
| Engine | Redis 7.x |
| Node Type | `cache.t3.micro` |
| Nodes | 1 (upgradeable to cluster) |
| Encryption at Rest | Yes |
| Encryption in Transit | Yes (TLS) |
| Publicly Accessible | **No** |
| Subnet Group | Private |

### Redis Key Namespaces

```
legis:lock:<job_type>       # Distributed job locks (scheduler)
legis:rate:<user_id>        # Rate limit sliding window
legis:session:<session_id>  # Session revocation blacklist
legis:cache:<resource>      # API response caching
legis:queue:<job_type>      # Background job coordination
```

---

## 8. Secrets Management

**Provider**: AWS Secrets Manager

| Secret Name | Contents | Rotation |
|:-----------|:---------|:---------|
| `legis/prod/database-url` | PostgreSQL connection URL | 90 days |
| `legis/prod/redis-url` | Redis connection URL | Manual |
| `legis/prod/jwt-secret` | JWT signing key (≥256 bits) | 90 days |
| `legis/prod/oidc-client-secret` | OIDC provider client secret | Per-IdP |
| `legis/prod/smtp-credentials` | Email provider credentials | Manual |
| `legis/prod/stripe-keys` | Stripe API keys + webhook secret | Manual |
| `legis/prod/groq-api-key` | Groq LLM API key | Manual |

### Secret Injection

Secrets are injected at runtime via **ECS Task IAM Role** — not environment variables embedded in Docker images. The `taskRoleArn` has `secretsmanager:GetSecretValue` permission scoped only to `legis/prod/*`.

> [!CAUTION]
> Secrets are **never** stored in:
> - Git repository
> - Docker images (build args that embed secret values)
> - Frontend JavaScript bundles
> - Logs
> - Database records
> - Documentation

---

## 9. Ingress & TLS

| Parameter | Value |
|:----------|:------|
| Load Balancer | AWS ALB (Application Load Balancer) |
| TLS Certificate | AWS ACM (auto-renewed) |
| HTTP→HTTPS Redirect | Yes (ALB listener rule) |
| SSL Policy | `ELBSecurityPolicy-TLS13-1-2-2021-06` |
| Idle Timeout | 60 seconds |
| HSTS | `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| CORS Origins | Production domain only |
| Secure Cookies | `Secure; HttpOnly; SameSite=Strict` |

---

## 10. Logging

**Provider**: AWS CloudWatch Logs

```json
{
  "log_group": "/legis-intel/production",
  "retention_days": 90,
  "log_driver": "awslogs",
  "format": "structured-json"
}
```

**Mandatory log fields**: `request_id`, `service`, `timestamp`, `severity`

**Redacted fields** (never logged):
- `password`, `bearer_token`, `api_key`, `db_password`
- `stripe_key`, `razorpay_key`, `client_secret`, `groq_api_key`
- `x-tenant-id` (header, before authentication)

---

## 11. Monitoring

**Provider**: AWS CloudWatch + CloudWatch Alarms

### Tracked Metrics

| Metric | Alarm Threshold |
|:-------|:---------------|
| HTTP 5xx error rate | > 5% for 5 min → SNS notification |
| Request latency P99 | > 2000 ms for 5 min → SNS |
| Database connections | > 80% for 10 min → SNS |
| Redis memory usage | > 80% for 10 min → SNS |
| Scheduler heartbeat | Missing > 10 min → CRITICAL SNS |
| Worker job failures | > 10 in 5 min → SNS |
| AI API calls | Tracked for billing attribution |
| Email delivery failures | > 5 in 1 hour → SNS |
| Billing webhook failures | Any → SNS |

### Dashboard

- `legis-production-overview`: System health, error rates, active tenants
- `legis-api-latency`: Endpoint latency breakdown, search benchmark tracking

---

## 12. Deployment Strategy

**Type**: Rolling deployment (50% minimum healthy, 200% maximum)

```
Step 1: Build Docker images
    ↓
Step 2: pytest tests/ (BLOCKING gate)
    ↓
Step 3: npm run test + typecheck + build (BLOCKING gate)
    ↓
Step 4: Security suite (BLOCKING gate)
    ↓
Step 5: Frozen baseline verification — State predictions == 0 (BLOCKING gate)
    ↓
Step 6: Push images to AWS ECR
    ↓
Step 7: Update ECS task definitions
    ↓
Step 8: ECS rolling deploy (50% healthy minimum)
    ↓
Step 9: /health + /ready health check verification
    ↓
Step 10: Production smoke test
    ↓
Step 11 (conditional): Rollback if smoke test fails
```

**Circuit Breaker**: Enabled — automatic rollback on consecutive task failures.

---

## 13. DNS & TLS Status

**DNS_STATUS = NOT_CONFIGURED**  
**TLS_CUSTOM_DOMAIN = NOT_CONFIGURED**

No production domain has been provisioned. Architecture is ready for domain configuration.

**When domain is available**:
1. Register domain in Route 53 (or configure existing registrar NS records)
2. Request ACM certificate for `app.yourdomain.com` and `api.yourdomain.com`
3. Create Route 53 alias A records pointing to ALB DNS name
4. Update `API_CORS_ORIGINS`, `FRONTEND_URL`, `SESSION_COOKIE_DOMAIN`

---

## 14. External Service Status Table

| Service | Architecture | Provisioning Status |
|:--------|:-----------|:-------------------|
| Cloud Compute (AWS ECS/Fargate) | READY | **NOT_DEPLOYED** (BLOCKED_BY_CREDENTIALS) |
| PostgreSQL (AWS RDS PG 15.4) | READY | **NOT_CONFIGURED** |
| Redis (AWS ElastiCache Redis 7) | READY | **NOT_CONFIGURED** |
| OIDC / SSO (Auth0 / Okta) | READY | **NOT_CONFIGURED** |
| Email (SendGrid / SMTP) | READY | **NOT_CONFIGURED** |
| Groq AI | READY | **NOT_CONFIGURED** |
| Billing (Stripe) | READY | **NOT_CONFIGURED** |
| DNS (Route 53) | READY | **NOT_CONFIGURED** |
| TLS (ACM) | READY | **NOT_CONFIGURED** |
| Monitoring (CloudWatch) | READY | **PARTIAL** (config ready, not provisioned) |
| Backups (RDS automated) | READY | **NOT_CONFIGURED** (activates on RDS provision) |

> [!NOTE]
> `NOT_CONFIGURED` means architecture and integration code are complete and correct; actual cloud provisioning requires AWS account credentials and explicit manual provisioning. No fabrication of credentials or resources has occurred.

---

## 15. Production Readiness Classification

```
APPLICATION_CODE          = READY
SAAS_ARCHITECTURE         = READY
STAGING_SELF_HOSTED       = READY
CLOUD_INFRASTRUCTURE      = NOT_CONFIGURED  (BLOCKED_BY_CREDENTIALS)
DATABASE                  = NOT_CONFIGURED
REDIS                     = NOT_CONFIGURED
AUTH                      = NOT_CONFIGURED
EMAIL                     = NOT_CONFIGURED
AI                        = NOT_CONFIGURED
BILLING                   = NOT_CONFIGURED
DNS_TLS                   = NOT_CONFIGURED
CLOUD_DEPLOYMENT          = NOT_DEPLOYED
PRODUCTION_SMOKE_TEST     = NOT_RUN  (requires live deployment)
PRODUCTION_OPERATIONAL    = NOT_READY
```

---

## 16. What Remains for Live Deployment

1. **AWS Account**: Active account with billing configured
2. **Terraform / CDK**: Run infrastructure-as-code to provision VPC, RDS, ElastiCache, ECS cluster, ALB
3. **AWS Secrets Manager**: Upload all production secrets
4. **ECR**: Push container images with correct tags
5. **ECS Task Definitions**: Register and deploy all 4 service definitions
6. **OIDC Provider**: Register application with Auth0/Okta; configure callback URLs
7. **Email Domain**: Verify sending domain with SendGrid/SES; configure SPF/DKIM
8. **Stripe/Razorpay**: Create production account; configure webhook endpoint
9. **Groq API Key**: Obtain from Groq console
10. **DNS**: Configure Route 53 records and ACM certificate validation

---

## 17. Task 8.21A Regression Reconciliation & Test Verification Summary

Following corrective task **TASK 8.21A**, the backend test suite execution was fully reconciled:

- **Canonical Command**: `pytest tests/`
- **Total Collected**: `2,229` (Task 8.19A: 2,145 + Task 8.20: 14 + Task 8.21: 70 = 2,229)
- **Total Passed**: `2,229` (100.0%)
- **Total Failed**: `0`
- **Total Skipped**: `0`
- **Duration**: `392.44s (6m 32s)` across 96 test files
- **Task 8.21 Dedicated Tests**: `70 passed / 70 collected (100%)`
- **Accumulated Security & Deployment Suite**: `124 passed / 124 collected (100%)`
- **Frozen Analytical Baseline**: 100% verified unchanged across all 21 dimensions
- **Data Directory Immutability**: Clean (`git status --short data/` is empty)
- **Deployment Status**: Architecture READY; Cloud Deployment NOT_DEPLOYED (BLOCKED_BY_CREDENTIALS)
