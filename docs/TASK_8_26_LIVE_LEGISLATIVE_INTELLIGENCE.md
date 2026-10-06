# Task 8.26 — Live Legislative Intelligence & Automatic Update Pipeline

> **Status:** IMPLEMENTED
> **Date:** 2026-09-29
> **Frozen Baseline:** UNMODIFIED — Task 8.25 invariants preserved

## Critical Architecture: FROZEN vs LIVE

```
FROZEN ANALYTICAL DATASET  (20 bills / 47 companies / 940 pairs — immutable)
  analytical_model_status = MODELLED
  <- ONLY reachable via approved analytical ingestion CLI

          STRICT FIREWALL (assert_not_frozen_model() guard)
                    never automatically crossed

LIVE KNOWLEDGE BASE  (Task 8.26 — newly discovered bills)
  analytical_model_status = KNOWLEDGE_ONLY  (pipeline default)
  live_status: DISCOVERED -> VERIFIED -> UPDATED -> KNOWLEDGE_ONLY
```

## Deliverables

| File | What it does |
|---|---|
| schemas/monitoring.py | +SourceCategory, LiveStatus, AnalyticalModelStatus, LiveKnowledgeRecord |
| storage/live_knowledge_repository.py | Thread-safe JSON store; enforces firewall on every write |
| services/monitoring/source_url_validator.py | SSRF-protective validator (50+ Indian legislative domains) |
| services/monitoring/update_processor.py | Creates LiveKnowledgeRecord on NEW_BILL events |
| api/schemas.py | +LiveKnowledgeRecordItem, LiveKnowledgeListResponse, LiveKnowledgeStatsResponse |
| api/routers/monitoring.py | 3 new endpoints under /monitoring/live-knowledge |
| config/monitoring_sources.json | All 12 sources: authority_name + source_category |
| tests/test_task_8_26_live_intelligence.py | 30 tests — ALL PASS |

## New API Endpoints

- GET /monitoring/live-knowledge        — paginated list (filters: live_status, analytical_model_status, jurisdiction)
- GET /monitoring/live-knowledge/stats  — aggregate stats + firewall health check
- GET /monitoring/live-knowledge/{id}   — single record by record_id

## Test Results

  30/30 PASS  (0.94s)
  Frontend typecheck: CLEAN

## Frozen Baseline Invariants

  Central bills: 20 (unchanged)
  Quant companies: 47 (unchanged)
  Bill-company pairs: 940 (unchanged)
  State predictions: 0 (strict, unchanged)
  Historical training data: immutable (unchanged)

## SSRF Protection

Blocks: localhost, private IPs, cloud metadata, embedded credentials, non-HTTP schemes.
Warns on unknown domains (optional strict mode: enforce_allowlist=True).
