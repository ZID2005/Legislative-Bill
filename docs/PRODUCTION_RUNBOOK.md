# PRODUCTION RUNBOOK

**Platform**: India Legislative Intelligence & Market Impact Platform  
**Version**: v1.0.0 (Task 8.21)  
**Environment**: AWS ECS/Fargate — `ap-south-1`  
**Analytical System**: STRICTLY FROZEN  

---

## 1. Service Topology

```
legis-frontend     → ECS Fargate / Port 3000  / 2 replicas
legis-api          → ECS Fargate / Port 8000  / 2 replicas
legis-worker       → ECS Fargate / No port    / 1 replica
legis-scheduler    → ECS Fargate / No port    / 1 replica (MUST remain 1)
legis-postgres     → AWS RDS PostgreSQL 15.4 / Private subnet
legis-redis        → AWS ElastiCache Redis 7 / Private subnet
```

---

## 2. Health Check Endpoints

| Endpoint | Method | Expected Response | Purpose |
|:---------|:-------|:-----------------|:--------|
| `GET /health` | GET | `{"status": "healthy"}` | Container liveness |
| `GET /ready` | GET | `{"status": "ready", ...}` | Full readiness check |
| `GET /api/v1/monitoring/status` | GET | `{"sources": [...]}` | Legislative source health |

### Testing Health from CLI

```bash
# Local / staging
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Production (replace with actual ALB DNS)
curl https://api.legis-intel.in/health
curl https://api.legis-intel.in/ready
```

### Expected `/ready` Response

```json
{
  "status": "ready",
  "database": "healthy",
  "cache": "healthy",
  "workers": "healthy",
  "legislative_monitor": "active",
  "baseline_verified": true,
  "state_predictions": 0
}
```

---

## 3. Startup Procedure

### First-Time Production Deployment

1. **Provision infrastructure** via Terraform/CDK
2. **Upload secrets** to AWS Secrets Manager
3. **Apply database migration** (see Migration section)
4. **Push container images** to ECR
5. **Deploy ECS services** (api → worker → scheduler → frontend, in dependency order)
6. **Verify health endpoints** `/health` + `/ready`
7. **Run smoke test**: `python scripts/smoke_test_all_routes.py --base-url https://api.legis-intel.in`
8. **Verify baseline**: confirm `state_predictions = 0` in `/ready` response

### Rolling Update (Zero-Downtime)

```bash
# Build and push new images
docker build -t $ECR_URI/legis-api:$VERSION -f Dockerfile.api .
docker push $ECR_URI/legis-api:$VERSION

# Update ECS service (rolling deploy)
aws ecs update-service \
  --cluster legis-intel-production \
  --service legis-api \
  --force-new-deployment \
  --region ap-south-1
```

---

## 4. Database Migration

> [!CAUTION]
> **NEVER run migrations directly against analytical baseline tables.**
> Frozen analytical data (predictions, decisions, anticipation scores) is write-protected for the application user.

### Migration Procedure

```bash
# Step 1: Create database backup
aws rds create-db-snapshot \
  --db-instance-identifier legis-intel-prod \
  --db-snapshot-identifier legis-pre-migration-$(date +%Y%m%d%H%M%S)

# Step 2: Validate migration (dry-run)
alembic upgrade head --sql  # Print SQL without executing

# Step 3: Confirm rollback procedure is documented

# Step 4: Apply migration
alembic upgrade head

# Step 5: Verify application health
curl https://api.legis-intel.in/ready

# Step 6: Log migration
echo "MIGRATION: $(alembic current) at $(date -u)" >> migration.log
```

### Rollback Procedure

```bash
# Rollback to previous revision
alembic downgrade -1

# Or rollback to specific revision
alembic downgrade <revision_id>

# Restore from snapshot if structural damage
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier legis-intel-prod-restored \
  --db-snapshot-identifier legis-pre-migration-<timestamp>
```

---

## 5. Secret Management

### Retrieving Secrets (ECS Runtime)

Secrets are automatically injected via ECS Task IAM Role from AWS Secrets Manager. The application reads them from environment at runtime — never from Docker image build args.

### Rotating Secrets

```bash
# Rotate JWT secret (triggers automatic re-signing on next request)
aws secretsmanager rotate-secret \
  --secret-id legis/prod/jwt-secret \
  --rotation-lambda-arn arn:aws:lambda:ap-south-1:...

# Manually update email credentials
aws secretsmanager update-secret \
  --secret-id legis/prod/smtp-credentials \
  --secret-string '{"host":"smtp.sendgrid.net","user":"apikey","password":"SG.xxx"}'
```

> [!IMPORTANT]
> After rotating `OIDC_CLIENT_SECRET`, the application must be redeployed to pick up the new value from Secrets Manager.

---

## 6. Background Worker Operations

### Checking Worker Status

```bash
# Check ECS worker task status
aws ecs list-tasks \
  --cluster legis-intel-production \
  --service-name legis-worker

# Check scheduler task status
aws ecs list-tasks \
  --cluster legis-intel-production \
  --service-name legis-scheduler
```

### Distributed Lock Verification (Anti-Duplicate)

```bash
# Connect to Redis and verify scheduler lock
redis-cli -h $REDIS_HOST -p 6379 --tls KEYS "legis:lock:*"
```

Expected: At most one lock per job type exists at any time.

### Manual Job Trigger

```bash
# Trigger legislative monitoring immediately
python scripts/run_worker.py --job legislative_monitoring

# Trigger alert processing
python scripts/run_worker.py --job alert_processing
```

---

## 7. Legislative Monitoring Operations

### Monitoring Flow Verification

```
New Central bill discovered
         ↓
   Deduplication check
         ↓
   Version tracking
         ↓
   Knowledge record update
         ↓
   Monitoring event emitted
         ↓
   NO stock prediction generated  ← immutable safeguard
```

```
State bill discovered
         ↓
   Deduplication check
         ↓
   Knowledge + exposure update
         ↓
   NO stock prediction generated  ← FIREWALL ABSOLUTE
```

### Check Monitoring Source Health

```bash
curl https://api.legis-intel.in/api/v1/monitoring/status
```

### Expected Sources (7 active)

- PRS Legislative Research (`prs.parliament`)
- Parliament of India Bills (`parliament.india`)
- India Code MegaSearch (`indiacode.nic.in`)
- Karnataka Legislature (`kla.kar.nic.in`)
- Kerala Legislature (`niyamasabha.kerala.gov.in`)
- Andhra Pradesh Legislature (`aplegislature.org`)
- Telangana Legislature (`tslegislature.telangana.gov.in`)

---

## 8. Logging and Observability

### Log Levels

| Level | When to use |
|:------|:-----------|
| DEBUG | Local development only |
| INFO | Normal operations, request handling |
| WARNING | Non-critical anomalies (missing optional config) |
| ERROR | Operation failures requiring attention |
| CRITICAL | System-level failures (database down, firewall breach) |

### Querying CloudWatch Logs

```bash
# Find all 5xx errors in last 1 hour
aws logs filter-log-events \
  --log-group-name /legis-intel/production \
  --filter-pattern '{ $.status_code >= 500 }' \
  --start-time $(date -d '1 hour ago' +%s000)

# Find all requests from a specific tenant
aws logs filter-log-events \
  --log-group-name /legis-intel/production \
  --filter-pattern '{ $.tenant_id = "tenant-alpha" }'
```

---

## 9. Backup & Recovery

### Backup Schedule

| Resource | Method | Frequency | Retention |
|:---------|:-------|:---------|:---------|
| PostgreSQL | RDS automated | Daily | 7 days |
| PostgreSQL | Manual snapshot | Pre-migration | Until confirmed safe |
| Redis | ElastiCache snapshot | Daily | 1 day |
| Application data (frozen) | Git | Every commit | Indefinite |

### RPO / RTO

| Classification | RPO | RTO |
|:--------------|:----|:----|
| PostgreSQL (tenant data) | 24 hours (daily backup) | ~2 hours (RDS restore) |
| PostgreSQL (with PITR) | 5 minutes | ~30 minutes |
| Redis (cache) | 0 (stateless by design) | < 1 minute (restart) |
| Frozen analytical data | 0 (Git-immutable) | < 5 minutes (clone + restart) |

### Point-in-Time Recovery

```bash
# Restore database to specific point in time
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier legis-intel-prod \
  --target-db-instance-identifier legis-intel-restored \
  --restore-time 2026-09-25T12:00:00Z
```

---

## 10. Scaling Operations

### Horizontal Scaling (API)

```bash
# Scale API to 4 replicas
aws ecs update-service \
  --cluster legis-intel-production \
  --service legis-api \
  --desired-count 4
```

> [!WARNING]
> Never scale `legis-scheduler` above **1 replica** without verifying distributed lock behavior. Use Redis-backed distributed locking before scaling.

---

## 11. Emergency Procedures

### Emergency Shutdown

```bash
# Set desired count to 0 (does not delete service)
aws ecs update-service --cluster legis-intel-production --service legis-api --desired-count 0
aws ecs update-service --cluster legis-intel-production --service legis-worker --desired-count 0
aws ecs update-service --cluster legis-intel-production --service legis-scheduler --desired-count 0
```

### Emergency Rollback

```bash
# Rollback to previous task definition
aws ecs update-service \
  --cluster legis-intel-production \
  --service legis-api \
  --task-definition legis-api:<previous_version>
```

---

## 12. Absolute Constraints (Never Violate)

1. **State predictions = 0**: Never deploy code that generates stock predictions for state bills
2. **Central baseline immutable**: Never modify `data/predictions/`, `data/decision_support/`, `data/anticipation/`
3. **Scheduler = 1 replica**: Never run more than one scheduler instance without distributed lock verification
4. **No secrets in logs**: Never log credentials, tokens, or API keys
5. **No superuser in app**: Application database user is non-superuser
6. **No analytical table writes**: Application user has no write access to frozen analytical tables
