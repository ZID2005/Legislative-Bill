# TASK 8.22 — Production Operations Runbook

**System**: India Legislative Intelligence & Market Impact Platform  
**Target Environment**: AWS ECS/Fargate (`ap-south-1`)  
**Document Version**: 1.0 (Task 8.22)  
**Classification**: Operational Standard Operating Procedures (SOP)  
**Current Operational Status**: CLOUD_PRODUCTION_OPERATIONAL = NOT_READY (AWS Deployment Blocked by Missing Credentials; SOP Prepared for Post-Provisioning)  

---

## 1. System Architecture & Component Mapping

| Subsystem | Component | Runtime / Image | Port | Monitoring Alarm | Auto-Scaling Target |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ingress** | Application Load Balancer | AWS ALB | 80/443 | `HTTPCode_Target_5XX_Count > 10` | N/A |
| **API** | REST API Layer | `Dockerfile.api` | 8000 | `API_Latency_p95 > 1500ms` | CPU > 70%, 2 to 10 tasks |
| **Frontend** | Web UI (Next.js 16) | `frontend/Dockerfile` | 3000 | `Frontend_Error_Rate > 1%` | CPU > 70%, 2 to 6 tasks |
| **Worker** | Background Job Worker | `Dockerfile.worker` | N/A | `Worker_DeadLetterQueue > 0` | Queue Depth > 100, 1 to 4 |
| **Scheduler**| Cron Dispatcher | `Dockerfile.scheduler`| N/A | `Scheduler_Heartbeat_Missed` | **Strictly 1 (No Scale)** |
| **Database** | Primary OLTP | AWS RDS PG 15.4 | 5432 | `CPUUtilization > 80%` | Storage Auto-grow |
| **Cache** | Cache & Lock Broker | ElastiCache Redis 7 | 6379 | `DatabaseMemoryUsagePercentage > 80%`| N/A |

---

## 2. Production Deployment Procedure

### Pre-Deployment Verification (Gate Checklist)
Before any code deployment to AWS ECR / ECS:

```bash
# 1. Activate project virtual environment
& ".\.venv\Scripts\python.exe" -V

# 2. Verify frozen baseline immutability
& ".\.venv\Scripts\python.exe" scripts/verify_frozen_baseline_exact.py

# 3. Verify clean working tree on analytical data
git status --short data/

# 4. Run CI/CD deployment gate
& ".\.venv\Scripts\python.exe" scripts/production_deployment_gate.py
```

### ECS Deployment Commands
Once CI/CD gate passes and AWS credentials are set:

```bash
# 1. Authenticate Docker with Amazon ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com

# 2. Build and tag container images
docker build -t legis-api:latest -f Dockerfile.api .
docker build -t legis-worker:latest -f Dockerfile.worker .
docker build -t legis-scheduler:latest -f Dockerfile.scheduler .
docker build -t legis-frontend:latest -f frontend/Dockerfile ./frontend

# 3. Push images to ECR repository
docker tag legis-api:latest $AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/legis-api:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/legis-api:latest

docker tag legis-frontend:latest $AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/legis-frontend:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/legis-frontend:latest

docker tag legis-worker:latest $AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/legis-worker:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/legis-worker:latest

docker tag legis-scheduler:latest $AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/legis-scheduler:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com/legis-scheduler:latest

# 4. Trigger ECS Rolling Update with Circuit Breaker
aws ecs update-service --cluster legis-intel-production --service legis-api --force-new-deployment
aws ecs update-service --cluster legis-intel-production --service legis-frontend --force-new-deployment
aws ecs update-service --cluster legis-intel-production --service legis-worker --force-new-deployment
aws ecs update-service --cluster legis-intel-production --service legis-scheduler --force-new-deployment
```

---

## 3. Database Migration & Schema Safety SOP

### Schema Classification & Immutability Rules
- **PUBLIC_FROZEN**: Tables storing 4,700 predictions, 4,700 decisions, 940 anticipation scores, 14,100 reports, 20 Central bills, 44 State acts, 86 exposures, 70 company master records.
  - Granted `SELECT` only to runtime database user `legis_app`.
  - Zero `UPDATE`, `DELETE`, or `DROP` permissions.
- **TENANT_OWNED_MUTABLE**: Tables storing user workspaces, watchlists, alert rules, and audit logs.
  - Scoped by `tenant_id` UUID foreign key.
  - Row-Level Security (RLS) enabled.

### Migration Execution Procedure
1. Take an immediate RDS snapshot before migration:
   ```bash
   aws rds create-db-snapshot --db-instance-identifier legis-prod-db --db-snapshot-identifier pre-mig-$(date +%Y%m%d%H%M)
   ```
2. Execute migration script inside a transactional migration runner task:
   ```bash
   aws ecs run-task --cluster legis-intel-production --task-definition legis-migration-runner --launch-type FARGATE ...
   ```
3. Verify baseline parity post-migration:
   ```bash
   python scripts/verify_frozen_baseline_exact.py
   ```

### Rollback Procedure
If a migration fails or induces regression:
1. Revert ECS service task definitions to the previous revision:
   ```bash
   aws ecs update-service --cluster legis-intel-production --service legis-api --task-definition legis-api:PREVIOUS_REVISION
   ```
2. If schema corruption occurred, restore RDS database from the pre-migration snapshot:
   ```bash
   aws rds restore-db-instance-from-db-snapshot --db-instance-identifier legis-prod-db-restored --db-snapshot-identifier pre-mig-XXXX
   ```

---

## 4. Background Scheduler & Singleton Protection

### Duplicate Prevention Safeguards
The legislative monitoring scheduler runs recurring scraping jobs to detect newly introduced parliamentary bills and gazettes.
- **ECS Replica Count**: Configured strictly to `1`.
- **Process Lock**: Internal `threading.Lock` prevents duplicate threads inside the same container.
- **Distributed Lock**: Acquires Redis lock `legis:lock:job_monitoring_central_pipeline` and `legis:lock:job_monitoring_state_pipeline` with 1-hour expiration.
- **Firewall Invariant**: `LegislativeScheduler.run_now()` verifies that the runner never possesses ML retraining or prediction generation functions. Any attempt to invoke model retraining immediately raises `RuntimeError` and terminates the run.

---

## 5. Secret Management & Rotation SOP

All production secrets reside in **AWS Secrets Manager**:
- `legis/prod/database-url`
- `legis/prod/redis-url`
- `legis/prod/jwt-secret`
- `legis/prod/oidc-client-secret`
- `legis/prod/smtp-credentials`
- `legis/prod/stripe-keys`
- `legis/prod/groq-api-key`

### Rotation Steps
1. Create a new secret version in AWS Secrets Manager:
   ```bash
   aws secretsmanager put-secret-value --secret-id legis/prod/jwt-secret --secret-string '{"JWT_SECRET_KEY":"new-cryptographic-key-2026"}'
   ```
2. Force a graceful rolling restart of `legis-api` to pull updated secrets via ECS task IAM role:
   ```bash
   aws ecs update-service --cluster legis-intel-production --service legis-api --force-new-deployment
   ```

---

## 6. Incident Response Playbook

| Severity | Incident | Immediate Action | Mitigation |
| :--- | :--- | :--- | :--- |
| **SEV-1** | 5xx error spike on API (>5% for 5 min) | Check CloudWatch `/legis-intel/production` logs | Rollback ECS task definition; inspect database connection limits |
| **SEV-1** | Database connectivity loss | Verify RDS instance status in AWS Console | Check security group rules; verify PgBouncer connection pool saturation |
| **SEV-2** | State prediction firewall breach attempt | Automatic alert triggered; system rejects with 403 | Verify API router code immutability; inspect git diff on repository |
| **SEV-2** | Scheduler missing heartbeat > 10 min | Check ECS task status for `legis-scheduler` | Inspect task exit reason; restart scheduler container |
| **SEV-3** | Outbound Groq AI timeout / rate limit | Extractive fallback activates automatically | Check Groq API usage quota; notify operations |

---

## 7. Authoritative Status Classification Block

```ini
APPLICATION_CODE = READY
CLOUD_ARCHITECTURE = READY
AWS_DEPLOYMENT = BLOCKED_BY_CREDENTIALS
DATABASE = NOT_CONFIGURED
REDIS = NOT_CONFIGURED
OIDC = NOT_CONFIGURED
EMAIL = NOT_CONFIGURED
BILLING = NOT_CONFIGURED
GROQ = NOT_CONFIGURED
DOMAIN = NOT_CONFIGURED
HTTPS = NOT_CONFIGURED
SCHEDULER = READY_ONLY
MONITORING = READY_ONLY
CLOUD_PRODUCTION_OPERATIONAL = NOT_READY
ANALYTICAL_BASELINE = FROZEN
STATE_PREDICTIONS = 0
```

