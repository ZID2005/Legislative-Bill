# TASK 8.23 — Production Rollback Runbooks

**Status**: AUTHORITATIVE / TESTED — UPDATED BY TASK 8.23A  
**Date**: September 2026  
**Application Code Status**: READY  
**Cloud Deployment Status**: BLOCKED_BY_CREDENTIALS  

---

## 1. Overview & Rollback Principles

When a deployment introduces critical regressions, elevated error rates, or data integrity anomalies, rolling back to a known healthy state must be fast, deterministic, and safe.

The platform follows five rollback principles:
1. **Zero Analytical Data Loss**: Baseline data (`PUBLIC_FROZEN`) is pinned in Git and immutable in runtime. Rollbacks never overwrite or modify baseline analytical calculations.
2. **Backward-Compatible Schema Migrations**: All database schema changes follow the *Expand-Contract* pattern (additive changes first, destructive changes in subsequent releases).
3. **Immutable Artifacts**: Every container image is tagged with git commit SHA and immutable digest.
4. **Isolated Rollback Strata**: Code, containers, database schemas, and configuration can be rolled back independently.
5. **Verification Gating**: A rollback is not complete until health endpoints and baseline verification pass.

---

## 2. Rollback Tiers & Runbooks

### Tier 1: Container & Task Definition Rollback (ECS / Docker)
- **Trigger Conditions**:
  - Unhandled exception rate $> 1\%$ within 15 minutes of deployment.
  - Container health check failures (`/health/ready` non-200).
  - P99 latency spike $> 500\%$.
- **Prerequisites**: Previous task definition ARN or Docker image digest known.
- **Estimated Time**: 2 to 5 minutes.
- **Step-by-Step Procedure**:
  ```bash
  # Step 1: Identify previous stable task definition revision
  PREV_REVISION=$(aws ecs describe-services \
    --cluster legislative-prod-cluster \
    --services legislative-api-service \
    --query "services[0].taskDefinition" \
    --output text | awk -F: '{print $1":"$2":"$3":"$4":"$5":"$6":"$7-1}')

  # Step 2: Update ECS service to previous revision
  aws ecs update-service \
    --cluster legislative-prod-cluster \
    --services legislative-api-service \
    --task-definition "${PREV_REVISION}" \
    --force-new-deployment

  # Step 3: Monitor deployment rollout
  aws ecs wait services-stable \
    --cluster legislative-prod-cluster \
    --services legislative-api-service
  ```
- **Verification**:
  ```bash
  curl -fsS https://api.legislativeplatform.com/health/ready
  ```

---

### Tier 2: Application Code Rollback (Git)
- **Trigger Conditions**:
  - Logic bug or calculation regression discovered post-release.
  - Fast-forward hotfix not viable within SLA.
- **Prerequisites**: Access to git repository, clean working tree.
- **Estimated Time**: 3 to 8 minutes.
- **Step-by-Step Procedure**:
  ```bash
  # Step 1: Check out last known stable release tag
  STABLE_TAG=$(git tag -l "v*" --sort=-v:refname | sed -n '2p')
  echo "Rolling back code to ${STABLE_TAG}"

  # Step 2: Create rollback branch and revert
  git checkout -b rollback-to-${STABLE_TAG}
  git revert --no-edit HEAD..${STABLE_TAG}

  # Step 3: Run baseline verification locally before pushing
  python scripts/verify_frozen_baseline_exact.py

  # Step 4: Push to trigger automated CI build
  git push origin rollback-to-${STABLE_TAG}
  ```
- **Verification**:
  - CI pipeline passes all tests (2,252 unit/integration tests).
  - Production deployment triggers via deployment pipeline.

---

### Tier 3: Database Schema Migration Rollback (Alembic / PostgreSQL)
- **Trigger Conditions**:
  - Failed migration leaves schema in inconsistent state.
  - Query performance regression caused by new index/constraint.
- **Prerequisites**: Down migration scripts verified; database connection string available.
- **Estimated Time**: 1 to 3 minutes.
- **Step-by-Step Procedure**:
  ```bash
  # Step 1: Check current migration head
  alembic current

  # Step 2: Downgrade by one revision (or specific target revision)
  alembic downgrade -1

  # Step 3: Verify current revision matches expected previous hash
  alembic current
  ```
- **Safety Rules**:
  - Never downgrade a migration that dropped columns without a verified backup.
  - All migrations must have tested `downgrade()` functions.

---

### Tier 4: Environment & Configuration Rollback (SSM / Secrets)
- **Trigger Conditions**:
  - Application crash on boot due to invalid environment variable or credential misconfiguration.
- **Prerequisites**: AWS CLI access with SSM permissions.
- **Estimated Time**: 1 to 2 minutes.
- **Step-by-Step Procedure**:
  ```bash
  # Step 1: Revert parameter in AWS SSM Parameter Store to previous version
  PREV_VERSION=$(aws ssm get-parameter-history \
    --name "/legislative/prod/CONFIG_JSON" \
    --query "Parameters[-2].Version" \
    --output text)

  aws ssm put-parameter \
    --name "/legislative/prod/CONFIG_JSON" \
    --value "$(aws ssm get-parameter-history --name "/legislative/prod/CONFIG_JSON" --query "Parameters[-2].Value" --output text)" \
    --overwrite

  # Step 2: Restart application tasks to reload environment
  aws ecs update-service \
    --cluster legislative-prod-cluster \
    --service legislative-api-service \
    --force-new-deployment
  ```
- **Verification**:
  - Container logs show successful boot with `StartupValidator` diagnostic passed.

---

### Tier 5: Background Worker & Scheduler Rollback
- **Trigger Conditions**:
  - Worker queue poison-pill task causing repeat worker restarts.
  - Scheduler triggering duplicate jobs.
- **Prerequisites**: Worker cluster management access.
- **Estimated Time**: 2 to 4 minutes.
- **Step-by-Step Procedure**:
  ```bash
  # Step 1: Gracefully drain active worker tasks
  # Sends SIGTERM, allowing in-flight jobs up to 60s to complete
  docker compose stop -t 60 worker scheduler

  # Step 2: Clear stale distributed scheduler leader lock
  # Lock key: distributed_scheduler:legislative_monitor
  python -c "
from infrastructure.cache.provider import get_cache_provider
cache = get_cache_provider()
cache.release_lock('distributed_scheduler:legislative_monitor')
print('Distributed scheduler lock cleared')
"

  # Step 3: Verify lock is cleared (should return False = no lock held)
  python -c "
from infrastructure.cache.provider import get_cache_provider
cache = get_cache_provider()
acquired = cache.acquire_lock('distributed_scheduler:legislative_monitor', timeout_seconds=0.1, expire_seconds=1)
cache.release_lock('distributed_scheduler:legislative_monitor')
print('Lock clear verified:', acquired)
"

  # Step 4: Start previous worker image version
  docker compose -f docker-compose.prod.yml up -d worker scheduler
  ```
- **Verification**:
  - Worker heartbeat logs resume.
  - Scheduler logs single leader election notice.

---

## 3. Post-Rollback Comprehensive Verification Matrix

Following any rollback action, execute this mandatory verification sequence:

| Step | Action / Command | Expected Result |
|---|---|---|
| 1 | `curl -s http://localhost:8000/health/ready` | HTTP 200 `{"status": "healthy"}` |
| 2 | `curl -s http://localhost:8000/ready` | HTTP 200 `{"status": "healthy"}` |
| 3 | `python scripts/verify_frozen_baseline_exact.py` | `ALL 21 EXACT PARITY CHECKS PASSED` |
| 4 | `git status --short data/` | Empty output (0 dirty files) |
| 5 | Verify State Predictions Invariant | Strictly 0 State predictions |
| 6 | CloudWatch Alarm Status | All alarms in `OK` state |
