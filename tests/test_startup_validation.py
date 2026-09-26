"""
tests/test_startup_validation.py
================================
Unit and integration tests for Task 8.17 Startup Validation & Health Endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app
from services.startup_validator import StartupValidator, CheckLevel, CheckStatus

client = TestClient(app)


def test_startup_validator_execution() -> None:
    validator = StartupValidator()
    report = validator.run_validation(strict=False)

    assert report.can_start is True
    assert report.critical_failures == 0
    assert report.passed_count >= 5
    assert report.status in ("READY", "DEGRADED")


def test_liveness_probe_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "api_version" in data


def test_readiness_probe_ready() -> None:
    resp = client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["summary"] in ("READY", "DEGRADED")
    assert data["passed_checks"] >= 5


def test_api_v1_health() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_x_request_id_injected_in_response() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) > 0
