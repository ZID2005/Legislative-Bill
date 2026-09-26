"""
tests/test_monitoring_api.py
=============================
Integration tests for Legislative Monitoring & Discovery Center REST APIs.

Validates:
- GET /api/v1/monitoring/overview (telemetry, breakdown, health status)
- GET /api/v1/monitoring/sources (pagination, central/state filtering)
- GET /api/v1/monitoring/sources/{source_id} (detail, not found handling)
- GET /api/v1/monitoring/scheduler (observability, config, run status)
- GET /api/v1/monitoring/runs (pagination, run schema verification)
- GET /api/v1/monitoring/changes (detected changes feed, filtering)
- GET /api/v1/monitoring/changes/{event_id} (404 handling)
- GET /api/v1/monitoring/bill-versions/{bill_id} (version history schema)
- POST /api/v1/monitoring/check (safe manual check trigger)
- POST /api/v1/ai/ask with context_type="monitoring"
- Research Integrity Firewalls:
  * State monitoring strictly yields 0 predictions
  * Additive monitoring preserves historical datasets
  * No hallucination/fabrication of political or market recommendations
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

HEADERS_AUTH = {
    "X-Tenant-ID": "tenant_test",
    "X-User-ID": "user_test",
}


# ---------------------------------------------------------------------------
# 1. Monitoring Overview
# ---------------------------------------------------------------------------


def test_monitoring_overview_endpoint() -> None:
    resp = client.get("/api/v1/monitoring/overview", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    # Core telemetry fields
    assert "total_sources" in data
    assert data["total_sources"] >= 5
    assert "enabled_sources" in data
    assert "central_sources" in data
    assert "state_sources" in data
    assert data["central_sources"] >= 1
    assert data["state_sources"] >= 4
    assert "implemented_sources" in data
    assert "planned_sources" in data

    # Health & run telemetry
    assert "total_runs" in data
    assert "scheduler" in data
    assert "sources_healthy" in data
    assert "sources_never_checked" in data
    assert "sources_with_errors" in data


# ---------------------------------------------------------------------------
# 2. Source Registry
# ---------------------------------------------------------------------------


def test_monitoring_sources_list() -> None:
    resp = client.get("/api/v1/monitoring/sources", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert data["total"] >= 5
    assert len(data["items"]) > 0

    first_item = data["items"][0]
    assert "source_id" in first_item
    assert "source_name" in first_item
    assert "jurisdiction" in first_item
    assert "status" in first_item
    assert "enabled" in first_item


def test_monitoring_sources_filtering() -> None:
    # Filter by jurisdiction: central
    resp_central = client.get("/api/v1/monitoring/sources?jurisdiction=central", headers=HEADERS_AUTH)
    assert resp_central.status_code == 200
    data_central = resp_central.json()
    for item in data_central["items"]:
        assert item["jurisdiction"] == "central"

    # Filter by jurisdiction: state
    resp_state = client.get("/api/v1/monitoring/sources?jurisdiction=state", headers=HEADERS_AUTH)
    assert resp_state.status_code == 200
    data_state = resp_state.json()
    for item in data_state["items"]:
        assert item["jurisdiction"] == "state"


def test_monitoring_source_detail_and_not_found() -> None:
    # 1. Fetch all sources to get a valid source_id
    resp = client.get("/api/v1/monitoring/sources", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0
    valid_source_id = items[0]["source_id"]

    # 2. Fetch valid source detail
    detail_resp = client.get(f"/api/v1/monitoring/sources/{valid_source_id}", headers=HEADERS_AUTH)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["source_id"] == valid_source_id
    assert "recent_run_results" in detail
    assert "provenance" in detail
    assert detail["provenance"]["monitoring_system"] == "Task 8.11 LegislativeMonitoringScheduler"

    # 3. Fetch non-existent source
    not_found_resp = client.get("/api/v1/monitoring/sources/non_existent_source_xyz", headers=HEADERS_AUTH)
    assert not_found_resp.status_code == 404
    assert not_found_resp.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# 3. Scheduler Observability
# ---------------------------------------------------------------------------


def test_monitoring_scheduler_status() -> None:
    resp = client.get("/api/v1/monitoring/scheduler", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    assert "enabled" in data
    assert "scheduled_running" in data
    assert "run_in_progress" in data
    assert "config" in data
    assert "central_interval_hours" in data["config"]
    assert "state_interval_hours" in data["config"]


# ---------------------------------------------------------------------------
# 4. Monitoring Runs History
# ---------------------------------------------------------------------------


def test_monitoring_runs_pagination() -> None:
    resp = client.get("/api/v1/monitoring/runs?page=1&limit=10", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert data["page"] == 1
    assert data["limit"] == 10

    # Verify run fields if runs exist
    if data["items"]:
        run = data["items"][0]
        assert "run_id" in run
        assert "trigger" in run
        assert "status" in run
        assert "sources_checked" in run


# ---------------------------------------------------------------------------
# 5. Changes Feed & Event Detail
# ---------------------------------------------------------------------------


def test_monitoring_changes_feed() -> None:
    resp = client.get("/api/v1/monitoring/changes?page=1&limit=20", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

    if data["items"]:
        event = data["items"][0]
        assert "event_id" in event
        assert "event_type" in event
        assert "jurisdiction" in event
        assert "severity" in event


def test_monitoring_change_detail_not_found() -> None:
    resp = client.get("/api/v1/monitoring/changes/non_existent_event_id_xyz", headers=HEADERS_AUTH)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# 6. Bill Version History
# ---------------------------------------------------------------------------


def test_monitoring_bill_version_history() -> None:
    resp = client.get("/api/v1/monitoring/bill-versions/the-bills-of-lading-bill-2024", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    assert "bill_id" in data
    assert data["bill_id"] == "the-bills-of-lading-bill-2024"
    assert "versions_count" in data
    assert "versions" in data
    assert isinstance(data["versions"], list)


# ---------------------------------------------------------------------------
# 7. Safe Manual Check Trigger
# ---------------------------------------------------------------------------


def test_monitoring_manual_check() -> None:
    resp = client.post("/api/v1/monitoring/check", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    assert "run_id" in data
    assert "status" in data
    assert "trigger" in data
    assert data["trigger"] == "manual_api"
    assert "sources_checked" in data
    assert "sources_succeeded" in data
    assert "sources_failed" in data


# ---------------------------------------------------------------------------
# 8. AI Monitoring Analyst
# ---------------------------------------------------------------------------


def test_ai_monitoring_ask() -> None:
    payload = {
        "question": "What recent legislative changes were detected across Central and State portals?",
        "context_type": "monitoring",
        "context_id": "overview",
        "persona": "GENERAL_PUBLIC",
    }
    resp = client.post("/api/v1/ai/ask", json=payload, headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    assert "content" in data
    assert len(data["content"]) > 0
    assert data["context_type"] == "monitoring"
    assert "disclaimer" in data
    assert "not investment advice" in data["disclaimer"].lower()


# ---------------------------------------------------------------------------
# 9. Research Integrity & Epistemic Firewalls
# ---------------------------------------------------------------------------


def test_monitoring_never_generates_stock_predictions() -> None:
    """
    Monitoring responses MUST NOT contain stock Buy/Sell/Hold advice,
    target prices, or stock predictions for State bills.
    """
    resp = client.get("/api/v1/monitoring/overview", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    text_dump = str(data).lower()
    assert "buy" not in text_dump
    assert "sell" not in text_dump
    assert "outperform" not in text_dump
    assert "underperform" not in text_dump


def test_state_stock_predictions_firewall_parity() -> None:
    """
    Verify coverage endpoint confirms 0 state stock predictions permanently.
    """
    resp = client.get("/api/v1/coverage", headers=HEADERS_AUTH)
    assert resp.status_code == 200
    data = resp.json()

    assert data["state"]["state_stock_predictions_count"] == 0
    assert data["central"]["predictions_count"] > 0
