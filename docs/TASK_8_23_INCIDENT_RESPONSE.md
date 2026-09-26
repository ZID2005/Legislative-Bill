# TASK 8.23 — Operational Incident Response Runbooks

**Status**: AUTHORITATIVE / TESTED — UPDATED BY TASK 8.23A  
**Date**: September 2026  
**Application Code Status**: READY  
**Cloud Deployment Status**: BLOCKED_BY_CREDENTIALS  

---

## Overview & Severity Matrix

This document provides actionable operational runbooks for fourteen failure and security scenarios. Each runbook defines severity level, detection criteria, containment steps, recovery procedure, verification commands, and post-incident actions.

| Severity | Definition | Response SLA | Escalation Path |
|---|---|---|---|
| **P1 — Critical** | Total outage of API, baseline corruption, or active security breach | $\le$ 15 minutes | Lead Architect, SecOps, On-call Engineer |
| **P2 — Major** | Degraded user experience, database or cache failover, background worker disruption | $\le$ 30 minutes | Senior Platform Engineer, On-call Engineer |
| **P3 — Moderate** | Single third-party provider failure (Groq, Stripe, Resend), elevated latency | $\le$ 2 hours | Feature Team / DevOps Engineer |
| **P4 — Minor** | Transient scrape failure, minor UI alert issue, non-blocking disk alert (>75%) | $\le$ 24 hours | Assigned Engineer |

---

## Incident Runbooks

### Runbook 1: API Service Crash / Unhandled Exception Spike
- **Severity**: P1 / P2
- **Detection**:
  - CloudWatch Alarm / Prometheus: HTTP 5xx error rate > 2% over 2 minutes.
  - Process exit or container crash loop detected.
- **Immediate Containment**:
  1. Automated orchestrator (ECS/Docker) initiates replacement task.
  2. If persistent crash on boot, inspect recent release tag and freeze incoming traffic via ALB maintenance banner if necessary.
- **Diagnosis**:
  - Run log search for unhandled traceback:
    ```bash
    grep -E "CRITICAL|Traceback|ERROR" /var/log/app/app.log | tail -n 50
    ```
  - Verify if crash is related to configuration change or database schema mismatch.
- **Recovery**:
  1. If code defect, trigger zero-downtime rollback to previous container digest (`TASK_8_23_ROLLBACK_RUNBOOK.md`).
  2. If memory leak or OOM: increase task memory limit or restart container task.
- **Verification**:
  ```bash
  curl -fsS http://localhost:8000/ready
  curl -fsS http://localhost:8000/health/ready
  ```
- **Post-Incident**: Root-cause analysis (RCA), add regression test covering specific exception trigger.

---

### Runbook 2: Database Connection Failure / Pool Exhaustion
- **Severity**: P1
- **Detection**:
  - Logs indicate `OperationalError: connection to server lost` or `Timeout: pool exhausted`.
  - `/ready` endpoint reports `"database": "unhealthy"` or `"NOT_CONFIGURED"`.
- **Immediate Containment**:
  1. Fast-fail non-essential read requests; return cached baseline if applicable.
  2. Block new administrative long-running batch migrations.
- **Diagnosis**:
  - Check active connections on RDS / PostgreSQL:
    ```sql
    SELECT count(*), state FROM pg_stat_activity GROUP BY state;
    ```
  - Inspect connection pool configuration (`DB_POOL_SIZE`, `DB_MAX_OVERFLOW`).
- **Recovery**:
  1. Restart idle connections or terminate hung queries:
     ```sql
     SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle in transaction' AND state_change < now() - interval '5 minutes';
     ```
  2. If primary database crashed, verify RDS Multi-AZ automatic failover.
- **Verification**:
  ```bash
  python -c "from services.db_provider import get_db; db = get_db(); print('DB Connected' if db.is_healthy() else 'DB Failed')"
  ```
- **Post-Incident**: Review connection pool limits, implement connection leasing TTLs.

---

### Runbook 3: Redis Failure / Connection Timeout
- **Severity**: P2
- **Detection**:
  - Logs show `redis.exceptions.ConnectionError` or `TimeoutError`.
  - Rate limiting fallbacks triggered.
- **Immediate Containment**:
  1. The platform automatically activates graceful degradation:
     - Rate limiter defaults to in-memory sliding window or permits request with warning log.
     - Distributed lock falls back to single-instance memory lock or skips concurrent run.
  2. Cache misses fall through to primary data sources.
- **Diagnosis**:
  - Check Redis process status:
    ```bash
    redis-cli ping
    # Expected: PONG
    ```
  - Check Redis memory usage: `redis-cli info memory`.
- **Recovery**:
  1. Restart Redis service or promote read-replica in Redis cluster.
  2. Flush stale lock keys: `redis-cli del "scheduler:lock:leader"`.
- **Verification**:
  ```bash
  python -c "from services.cache_provider import get_cache; c = get_cache(); print('Cache OK' if c.is_healthy() else 'Cache Failed')"
  ```
- **Post-Incident**: Increase Redis memory allocation; adjust cache eviction policy to `volatile-lru`.

---

### Runbook 4: Worker Crash / Unresponsive Background Tasks
- **Severity**: P2
- **Detection**:
  - Celery / Async worker queue backlog increases continuously.
  - Heartbeat missing for > 120 seconds.
- **Immediate Containment**:
  1. Unfinished tasks remain in message broker queue (unacknowledged).
  2. Isolate failed task payload to dead-letter queue (DLQ) to prevent crash loop.
- **Diagnosis**:
  - Check worker task logs for segfaults or memory exhaustion:
    ```bash
    celery -A services.worker status
    ```
- **Recovery**:
  1. Restart worker daemon.
  2. Replay DLQ messages individually after identifying offending payload.
- **Verification**:
  ```bash
  pytest tests/test_scheduler_worker_resilience.py
  ```
- **Post-Incident**: Implement stricter payload schema validation before queue enqueueing.

---

### Runbook 5: Scheduler Failure / Missed Scheduled Runs
- **Severity**: P2
- **Detection**:
  - Expected hourly / daily batch jobs not recorded in execution history.
  - Distributed lock held by non-existent worker node.
- **Immediate Containment**:
  1. Stale-lock recovery mechanism automatically invalidates lock after TTL (300 seconds).
  2. Do NOT run duplicate jobs in parallel.
- **Diagnosis**:
  - Verify scheduler leader lock ownership:
    ```bash
    python -c "from services.scheduler_service import check_scheduler_lock; print(check_scheduler_lock())"
    ```
- **Recovery**:
  1. Clear stale lock if node died without releasing:
     ```python
     from services.cache_provider import get_cache
     get_cache().delete("scheduler:lock:leader")
     ```
  2. Trigger missed cron job via manual CLI with idempotent flags.
- **Verification**:
  - Confirm singleton scheduler acquires lock and resumes schedule.
- **Post-Incident**: Ensure lock renewal heartbeats run asynchronously from job execution.

---

### Runbook 6: External AI Service (Groq) Outage
- **Severity**: P3
- **Detection**:
  - Groq API returns HTTP 429 (Rate Limit), 500, 502, or 503.
  - Logs show `GroqProvider: API unreachable, falling back to local heuristic/rule-based synthesis`.
- **Immediate Containment**:
  1. Platform automatically routes summary generation to offline cached templates / heuristic extraction.
  2. High-value quantitative predictions remain 100% operational (market models require zero external LLM calls).
- **Diagnosis**:
  - Check status at `status.groq.com`.
  - Validate API key quota and credentials.
- **Recovery**:
  1. Once Groq recovers, the platform resumes AI-enhanced summaries automatically.
- **Verification**:
  ```bash
  python -c "from services.llm_service import test_llm_connection; print(test_llm_connection())"
  ```
- **Post-Incident**: Evaluate multi-provider fallback (e.g. Claude / OpenAI / local vLLM).

---

### Runbook 7: Email Provider Outage (Resend / SMTP)
- **Severity**: P3
- **Detection**:
  - Outbound email delivery queue size growing.
  - Provider returns HTTP 5xx or connection timeout.
- **Immediate Containment**:
  1. Outbound alert notifications buffered in transactional retry queue with exponential backoff (up to 72 hours).
  2. UI displays in-app notification banner for alerts to ensure users receive legislative updates.
- **Diagnosis**:
  - Check Resend status page.
  - Verify sender domain DKIM/SPF/DMARC status.
- **Recovery**:
  1. Resume queue processing once provider is restored.
  2. Flush backlog at a controlled rate (e.g., 50 emails/sec) to avoid provider rate limiting.
- **Verification**:
  ```bash
  python -c "from services.email_provider import get_email_provider; print(get_email_provider().is_healthy())"
  ```
- **Post-Incident**: Review queue durability and retry policies.

---

### Runbook 8: Billing Provider (Stripe) Outage
- **Severity**: P3
- **Detection**:
  - Stripe webhook failures or checkout session creation timeouts.
- **Immediate Containment**:
  1. Existing tenant entitlements granted in grace-period mode (subscriptions do not immediately cancel upon webhook failure).
  2. Queue webhook retries in Stripe dashboard or platform incoming queue.
- **Diagnosis**:
  - Check status at `status.stripe.com`.
  - Validate webhook signing secret in production environment.
- **Recovery**:
  1. Replay missed webhooks from Stripe Dashboard.
  2. Validate tenant tier reconciliation.
- **Verification**:
  ```bash
  python -c "from services.billing_provider import get_billing_provider; print(get_billing_provider().is_healthy())"
  ```
- **Post-Incident**: Confirm idempotent webhook handler prevented duplicate ledger entries.

---

### Runbook 9: External Legislative Source Outage / Scrape Failure
- **Severity**: P4
- **Detection**:
  - Scheduled scraper reports HTTP 503 / 403 or DOM structure change from legislative source.
- **Immediate Containment**:
  1. Scraper logs error and exits cleanly without modifying the `PUBLIC_FROZEN` baseline.
  2. Existing bill database remains fully functional.
- **Diagnosis**:
  - Inspect source portal (e.g., Parliament / State legislative gazette).
  - Check if CAPTCHA or Cloudflare protection was added.
- **Recovery**:
  1. Update scraper selector or API client in a patch release.
  2. Run scraper manually in dry-run mode before scheduling.
- **Verification**:
  ```bash
  python scripts/verify_frozen_baseline_exact.py
  ```
- **Post-Incident**: Implement DOM drift alerting.

---

### Runbook 10: Security Incident: Compromised JWT / Token Leak
- **Severity**: P1
- **Detection**:
  - Irregular geographical access patterns or leaked token identified in public repos.
- **Immediate Containment**:
  1. Immediately rotate `JWT_SECRET_KEY` in environment / AWS Secrets Manager.
  2. This instantly invalidates all active sessions globally.
  3. Invalidate compromised user session tokens in Redis blacklist.
- **Diagnosis**:
  - Audit access logs for token usage:
    ```bash
    grep "token_id=COMPROMISED_ID" /var/log/app/access.log
    ```
- **Recovery**:
  1. Redeploy application containers with new secret key.
  2. Notify affected users to re-authenticate with MFA.
- **Verification**:
  - Verify old tokens receive HTTP 401 Unauthorized.
  - Verify new tokens can authenticate successfully.
- **Post-Incident**: Review secret scanning tools (git-secrets, Trufflehog) in CI/CD pipeline.

---

### Runbook 11: Data Corruption Detected in Analytical Baseline
- **Severity**: P1
- **Detection**:
  - `scripts/verify_frozen_baseline_exact.py` fails any check.
  - Central prediction count $\ne 4,700$ or State predictions $> 0$.
- **Immediate Containment**:
  1. Stop all analytical write pipelines immediately.
  2. Switch platform to read-only analytical mode.
- **Diagnosis**:
  - Run git status and diff on `data/`:
    ```bash
    git status --short data/
    git diff data/
    ```
- **Recovery**:
  1. Revert corrupted files to Git pinned baseline:
     ```bash
     git checkout HEAD -- data/
     ```
  2. Re-run verification script:
     ```bash
     python scripts/verify_frozen_baseline_exact.py
     ```
- **Verification**:
  - All 21 exact parity checks MUST PASS.
  - `git status --short data/` must be 100% clean.
- **Post-Incident**: Audit file permissions on production volume (`chmod -R 555 data/`).

---

### Runbook 12: Disk Space Exhaustion on Host / Container
- **Severity**: P2
- **Detection**:
  - Host disk utilization > 85%.
  - Write errors reported by PostgreSQL or log rotators.
- **Immediate Containment**:
  1. Prune dangling Docker volumes and containers:
     ```bash
     docker system prune -af --volumes
     ```
  2. Truncate rotated log files if safe:
     ```bash
     find /var/log/app -name "*.log.*" -mtime +7 -delete
     ```
- **Diagnosis**:
  - Identify largest consumers:
    ```bash
    du -sh /* 2>/dev/null | sort -h
    ```
- **Recovery**:
  1. Expand EBS volume via AWS CLI / Console without unmounting.
  2. Resize filesystem: `resize2fs /dev/xvda1`.
- **Verification**:
  ```bash
  df -h /
  ```
- **Post-Incident**: Configure automated CloudWatch alarm for disk space < 20%.

---

### Runbook 13: Cross-Tenant Data Leak Attempt Detected (IDOR Alert)
- **Severity**: P1
- **Detection**:
  - Security audit logs show HTTP 403 Forbidden with `Cross-tenant access attempt detected`.
  - User `tenant_a` attempted accessing resource belonging to `tenant_b`.
- **Immediate Containment**:
  1. The platform's multi-tenant isolation layer blocks the request automatically.
  2. Temporarily suspend offending user/IP address.
- **Diagnosis**:
  - Check audit trail for caller user ID, IP address, and target URI:
    ```bash
    grep "IDOR_VIOLATION" /var/log/app/security.log
    ```
- **Recovery**:
  1. Audit endpoints involved to verify parameter-level tenant scoping.
  2. Confirm test coverage in `tests/test_operational_hardening_chaos.py` (Scenario 10).
- **Verification**:
  ```bash
  pytest tests/test_operational_hardening_chaos.py -k "idor"
  ```
- **Post-Incident**: Review API endpoint authorization decorators across all routers.

---

### Runbook 14: Secret / Credential Exposure in Logs or Telemetry
- **Severity**: P1
- **Detection**:
  - Automated log scanner or developer notices unredacted token, password, or key in logs.
- **Immediate Containment**:
  1. Immediately rotate exposed credential (e.g. database password, Stripe key, Groq key).
  2. Flush and scrub affected log group from CloudWatch / local disk.
- **Diagnosis**:
  - Verify that `RedactingFilter` in `config/logging_config.py` covers the exposed pattern.
- **Recovery**:
  1. Update regex patterns in `RedactingFilter` to catch the new credential format.
  2. Deploy logging configuration update.
- **Verification**:
  ```bash
  python -c "
  import logging
  from config.logging_config import setup_logging
  logger = setup_logging()
  logger.info('Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.fake')
  "
  # Confirm output displays [REDACTED_JWT]
  ```
- **Post-Incident**: Add automated pre-commit hook scanning git diffs for credentials.

---

### Runbook 15: Distributed Scheduler Degraded (Redis Unavailable — Task 8.23A)
- **Severity**: P2
- **Detection**:
  - Scheduler status API or logs report `SCHEDULER_DEFERRED` events.
  - `scheduler_degraded: True` visible in scheduler health endpoint.
  - Redis health check reports `connected: false`.
- **Behavior** (Task 8.23A Fail-Closed):
  - In distributed production mode (`multi_instance`/`worker`/`scheduler`), the scheduler **fails closed** when Redis is unavailable.
  - Execution is DEFERRED \u2014 NOT substituted with a local process lock.
  - This is the correct, safe behavior. No scheduled jobs execute until Redis is restored.
- **Immediate Containment**:
  1. Confirm Redis health: check ElastiCache cluster health in AWS console.
  2. Confirm `scheduler_degraded` via scheduler status endpoint or logs.
  3. **Do NOT attempt to bypass fail-closed by setting JOB_EXECUTION_MODE=single_instance in production** \u2014 this disables distributed protection.
- **Diagnosis**:
  ```bash
  # Check scheduler status
  python -c "
  from services.monitoring.scheduler import LegislativeScheduler
  s = LegislativeScheduler()
  print(s.get_status())
  "
  # Check Redis connectivity
  python -c "
  from infrastructure.cache.provider import get_cache_provider
  c = get_cache_provider()
  print(c.health_check())
  "
  ```
- **Recovery**:
  1. Restore Redis connectivity (restart ElastiCache cluster, fix security group rules, etc.)
  2. Once Redis is available, scheduler will automatically resume on next scheduler interval.
  3. No manual intervention needed \u2014 the scheduler retries at next safe interval.
- **Verification**:
  ```bash
  pytest tests/test_task_8_23a_redis_fail_closed_scheduler.py -k "redis_recovers"
  ```
- **Critical Invariant**: `REDIS_UNAVAILABLE + MULTI_CONTAINER_PRODUCTION_MODE => SCHEDULER_EXECUTION_COUNT == 0`
- **Post-Incident**: Review ElastiCache multi-AZ configuration and failover settings.
