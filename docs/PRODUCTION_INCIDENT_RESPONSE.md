# PRODUCTION INCIDENT RESPONSE

**Platform**: India Legislative Intelligence & Market Impact Platform  
**Milestone**: Task 8.21  
**Scope**: Incident classification, response procedures, and escalation matrix  

---

## 1. Severity Classification

| Level | Label | Description | Response Time |
|:------|:------|:-----------|:-------------|
| **SEV-1** | CRITICAL | Platform completely down; data breach; State Prediction Firewall breach | 15 minutes |
| **SEV-2** | HIGH | Major feature unavailable; authentication failures; database degraded | 1 hour |
| **SEV-3** | MEDIUM | Non-critical feature degraded; elevated latency; email delivery failures | 4 hours |
| **SEV-4** | LOW | Minor UI issues; non-urgent warnings; single-user reports | Next business day |

---

## 2. Escalation Matrix

| Severity | Primary Responder | Escalation | External Escalation |
|:---------|:------------------|:----------|:-------------------|
| SEV-1 | On-call engineer | Engineering lead + CTO (15 min) | AWS Support (if infra) |
| SEV-2 | On-call engineer | Engineering lead (1 hour) | AWS Support (if infra) |
| SEV-3 | Engineering team | Engineering lead (4 hours) | — |
| SEV-4 | Engineering team | Normal sprint process | — |

---

## 3. Incident Response Procedures

### 3.1 Platform Unavailable (SEV-1)

```bash
# Step 1: Check ECS service status
aws ecs describe-services \
  --cluster legis-intel-production \
  --services legis-api legis-frontend legis-worker legis-scheduler

# Step 2: Check health endpoints
curl -sv https://api.legis-intel.in/health

# Step 3: Check RDS status
aws rds describe-db-instances --db-instance-identifier legis-intel-prod

# Step 4: Check Redis status
aws elasticache describe-cache-clusters

# Step 5: Review CloudWatch logs for errors
aws logs filter-log-events \
  --log-group-name /legis-intel/production \
  --filter-pattern '{ $.level = "ERROR" || $.level = "CRITICAL" }' \
  --start-time $(date -d '30 minutes ago' +%s000)

# Step 6: Rollback if recent deployment caused issue
aws ecs update-service \
  --cluster legis-intel-production \
  --service legis-api \
  --task-definition legis-api:<previous_version>
```

### 3.2 Database Unavailable (SEV-1/SEV-2)

```bash
# Check RDS status
aws rds describe-db-instances \
  --db-instance-identifier legis-intel-prod \
  --query 'DBInstances[0].DBInstanceStatus'

# Check connectivity from ECS task
aws ecs execute-command \
  --cluster legis-intel-production \
  --task <task-id> \
  --container legis-api \
  --command "pg_isready -h $POSTGRES_HOST -p 5432"

# Failover to Multi-AZ standby if primary unavailable
aws rds failover-db-instance --db-instance-identifier legis-intel-prod
```

### 3.3 Redis Unavailable (SEV-2)

```bash
# Application falls back to in-memory cache provider automatically
# Monitor for:
# - Rate limiting no longer cluster-wide
# - Distributed locks fall back to single-process
# - Session revocation limited to instance scope

# Restart Redis cluster node
aws elasticache reboot-cache-cluster \
  --cache-cluster-id legis-intel-redis \
  --cache-node-ids-to-reboot 0001
```

### 3.4 State Prediction Firewall Breach (SEV-1 — CRITICAL)

> [!CAUTION]
> A State Prediction Firewall breach is the most critical incident type. It means the platform has generated stock predictions for state bills — a core invariant violation.

```bash
# IMMEDIATE ACTIONS:
# 1. Take platform offline
aws ecs update-service \
  --cluster legis-intel-production \
  --service legis-api --desired-count 0

# 2. Document: which state, which bill, which prediction records
# 3. Do NOT delete the breach records until legally reviewed
# 4. Notify engineering lead + CTO immediately
# 5. Review code change that caused breach
# 6. Fix code + verify analytical firewall regression tests pass
# 7. Deploy fix with full regression suite gate
# 8. Restore service only after all gates pass
echo "STATE PREDICTION FIREWALL BREACH: SEV-1 CRITICAL"
```

### 3.5 Data Breach / Unauthorized Access (SEV-1)

```bash
# 1. Identify the affected tenant(s) from logs
aws logs filter-log-events \
  --log-group-name /legis-intel/production \
  --filter-pattern '{ $.status_code = 200 && $.tenant_id != $.authenticated_tenant }'

# 2. Revoke all active sessions immediately
# Execute via internal admin API (requires admin JWT):
curl -X POST https://api.legis-intel.in/api/v1/admin/sessions/revoke-all \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 3. Rotate JWT secret
aws secretsmanager rotate-secret --secret-id legis/prod/jwt-secret

# 4. Document access patterns
# 5. Notify affected tenants per data breach notification requirements
# 6. File incident report
```

### 3.6 Authentication Failures (SEV-2)

```bash
# Check OIDC provider status
curl https://<oidc-issuer>/.well-known/openid-configuration

# Check JWKS endpoint
curl https://<oidc-issuer>/.well-known/jwks.json

# If OIDC is down, verify fallback JWT mode is active
curl https://api.legis-intel.in/health | python -c "import sys,json; d=json.load(sys.stdin); print(d)"

# Check JWT secret is current
aws secretsmanager get-secret-value --secret-id legis/prod/jwt-secret
```

### 3.7 Scheduler Not Running (SEV-2)

```bash
# Check scheduler ECS task
aws ecs list-tasks \
  --cluster legis-intel-production \
  --service-name legis-scheduler

# Check for scheduler heartbeat in Redis
redis-cli -h $REDIS_HOST --tls GET "legis:scheduler:heartbeat"

# Check scheduler logs
aws logs filter-log-events \
  --log-group-name /legis-intel/production/scheduler \
  --start-time $(date -d '1 hour ago' +%s000)

# Restart scheduler (will re-acquire distributed lock)
aws ecs update-service \
  --cluster legis-intel-production \
  --service legis-scheduler \
  --force-new-deployment
```

---

## 4. Post-Incident Review (PIR)

After every SEV-1 or SEV-2 incident, complete a Post-Incident Review within 48 hours:

```
PIR Template:

Date: YYYY-MM-DD
Severity: SEV-X
Duration: X hours Y minutes
Impact: Description of customer/system impact

Timeline:
  HH:MM - Incident detected
  HH:MM - On-call notified
  HH:MM - Root cause identified
  HH:MM - Mitigation applied
  HH:MM - Service restored

Root Cause:
  Technical: [What broke?]
  Contributing factors: [Why did it break?]

Resolution:
  Immediate: [What was done to restore service?]
  Long-term: [What prevents recurrence?]

Action Items:
  - [ ] Action 1 (Owner: X, Due: YYYY-MM-DD)
  - [ ] Action 2 (Owner: Y, Due: YYYY-MM-DD)

Was the Analytical Firewall breached? YES / NO
Were State predictions generated? YES / NO
```

---

## 5. Communication Templates

### Internal Alert

```
[LEGIS-INTEL INCIDENT] SEV-{level}: {title}

Status: {INVESTIGATING | IDENTIFIED | MONITORING | RESOLVED}
Time: {UTC timestamp}
Impact: {Brief description}
Current action: {What is being done}

Next update: {time}
```

### Tenant Notification (SEV-1 only — use sparingly)

```
Subject: Legislative Intelligence Platform — Maintenance in Progress

We are currently experiencing a service disruption and our engineering team
is working to resolve it. Legislative intelligence data is not affected.
Estimated resolution time: {ETA}.

We apologize for the inconvenience and will notify you when service is restored.
```

---

## 6. Absolute Non-Negotiables

These actions are **forbidden** during any incident response:

1. ❌ Never delete or modify frozen analytical data (predictions, decisions, anticipation)
2. ❌ Never generate State stock predictions as a "workaround"
3. ❌ Never deploy without running the production deployment gate
4. ❌ Never log credentials while debugging
5. ❌ Never share raw database access with non-engineers
6. ❌ Never modify the State Prediction Firewall code under incident pressure

---

## 7. Key Contacts & Resources

| Resource | Details |
|:---------|:--------|
| AWS Support | Console → Support Center |
| CloudWatch Dashboards | `legis-production-overview`, `legis-api-latency` |
| Runbook | `docs/PRODUCTION_RUNBOOK.md` |
| Smoke Test | `docs/PRODUCTION_SMOKE_TEST.md` |
| Security Checklist | `docs/PRODUCTION_SECURITY_CHECKLIST.md` |
| Baseline Verification | `scripts/verify_frozen_baseline_exact.py` |
| Deployment Gate | `scripts/production_deployment_gate.py` |
