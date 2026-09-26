"""
tests/test_freshness_service.py
===============================
Unit tests for Task 8.17 Data Freshness and Stale Data Detection.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app
from schemas.freshness import FreshnessStatus, SystemFreshnessOverview
from services.freshness_service import FreshnessService, get_freshness_service

client = TestClient(app)


def test_freshness_service_evaluates_all_domains() -> None:
    service = FreshnessService()
    overview = service.evaluate_system_freshness()

    assert isinstance(overview, SystemFreshnessOverview)
    assert len(overview.datasets) == 8
    assert overview.overall_status in (FreshnessStatus.LIVE, FreshnessStatus.RECENT, FreshnessStatus.STALE)

    names = [d.dataset_name for d in overview.datasets]
    assert "Monitored Legislative Sources" in names
    assert "Central Parliamentary Bills" in names
    assert "State Legislative Knowledge" in names
    assert "Corporate Exposure Network" in names
    assert "Company Intelligence Universe" in names
    assert "Historical Market Data" in names


def test_freshness_api_endpoint() -> None:
    resp = client.get("/api/v1/freshness")
    assert resp.status_code == 200
    data = resp.json()

    assert "overall_status" in data
    assert "datasets" in data
    assert len(data["datasets"]) in (8, 9)
    assert "timestamp" in data
