"""
tests/test_workspace_api.py
===========================
Comprehensive unit and integration tests for Task 8.15:
- Workspace Summary API (/api/v1/workspace/summary)
- Workspace Activity Feed API (/api/v1/workspace/activity)
- Workspace Grouped Watchlist Activity (/api/v1/workspace/watchlist-activity)
- Workspace Analytics Snapshot (/api/v1/workspace/analytics-snapshot)
- Multi-tenant and User Isolation on Workspace endpoints
- State Firewall and Intelligence Company Firewall guarantees
- Grounded AI Workspace Assistant with authorized user context
"""

import pytest
from fastapi.testclient import TestClient

from api.app import app
from schemas.alert import AlertEvent, AlertSeverity, AlertType
from schemas.watchlist import WatchlistEntityType
from services.watchlist_service import WatchlistService
from storage.alert_event_repository import AlertEventRepository
from storage.watchlist_repository import WatchlistRepository


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_setup():
    """Setup clean test data for tenant_a and user_a."""
    wl_repo = WatchlistRepository()
    alert_repo = AlertEventRepository()
    wl_service = WatchlistService(watchlist_repo=wl_repo)

    tenant_id = "test_tenant_workspace"
    user_id = "test_user_workspace"

    # Create watchlist
    wl = wl_service.create_watchlist(
        tenant_id=tenant_id,
        user_id=user_id,
        name="Energy & Infra Portfolio",
        description="Key energy bills and quantitative securities",
    )

    # Add central bill item
    item_bill = wl_service.add_item(
        watchlist_id=wl.watchlist_id,
        entity_type="BILL",
        entity_id="the-coastal-shipping-bill-2024",
        tenant_id=tenant_id,
        user_id=user_id,
        display_name="The Coastal Shipping Bill, 2024",
    )

    # Add company item
    item_comp = wl_service.add_item(
        watchlist_id=wl.watchlist_id,
        entity_type="COMPANY",
        entity_id="INE758T01015",
        tenant_id=tenant_id,
        user_id=user_id,
        display_name="Zomato Limited",
    )

    # Add an unread alert event
    alert = AlertEvent(
        user_id=user_id,
        tenant_id=tenant_id,
        watchlist_id=wl.watchlist_id,
        alert_type=AlertType.BILL_STATUS_CHANGE,
        severity=AlertSeverity.HIGH,
        title="Status Change - Coastal Shipping Bill",
        summary="Passed Lok Sabha with amendments.",
        entity_type=WatchlistEntityType.BILL,
        entity_id="the-coastal-shipping-bill-2024",
        is_read=False,
    )
    alert_repo.create(alert)

    yield {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "watchlist_id": wl.watchlist_id,
        "alert_id": alert.alert_event_id,
    }

    # Cleanup
    try:
        wl_service.deactivate_watchlist(wl.watchlist_id, tenant_id=tenant_id, user_id=user_id)
        from config.settings import settings
        ev_file = settings.ALERTS_DIR / "events" / tenant_id / user_id / f"event_{alert.alert_event_id}.json"
        if ev_file.is_file():
            ev_file.unlink()
    except Exception:
        pass


def test_workspace_summary(client, test_setup):
    """Test 1: Workspace summary returns accurate live telemetry."""
    headers = {
        "X-Tenant-ID": test_setup["tenant_id"],
        "X-User-ID": test_setup["user_id"],
    }
    response = client.get("/api/v1/workspace/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["tenant_id"] == test_setup["tenant_id"]
    assert data["user_id"] == test_setup["user_id"]
    assert data["total_watchlists"] >= 1
    assert data["watched_bills"] >= 1
    assert data["watched_companies"] >= 1
    assert data["active_alerts"] >= 1
    assert data["recent_changes_count"] >= 1


def test_workspace_activity_feed(client, test_setup):
    """Test 2: Workspace activity returns events with epistemic labels."""
    headers = {
        "X-Tenant-ID": test_setup["tenant_id"],
        "X-User-ID": test_setup["user_id"],
    }
    response = client.get("/api/v1/workspace/activity?limit=20", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1

    # Verify epistemic label is present and one of OBSERVED, DERIVED, or PREDICTION
    for item in data["items"]:
        assert item["epistemic_status"] in ("OBSERVED", "DERIVED", "PREDICTION")
        assert item["deep_link"].startswith("/")


def test_workspace_watchlist_activity_grouping(client, test_setup):
    """Test 3: Watchlist activity groups entities into Bills, Companies, Industries, Jurisdictions."""
    headers = {
        "X-Tenant-ID": test_setup["tenant_id"],
        "X-User-ID": test_setup["user_id"],
    }
    response = client.get("/api/v1/workspace/watchlist-activity", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "bills" in data
    assert "companies" in data
    assert "industries" in data
    assert "jurisdictions" in data

    # Verify the watched bill is in bills
    bill_ids = [b["entity_id"] for b in data["bills"]]
    assert "the-coastal-shipping-bill-2024" in bill_ids

    # Verify the watched company is in companies
    comp_ids = [c["entity_id"] for c in data["companies"]]
    assert "INE758T01015" in comp_ids


def test_workspace_analytics_snapshot_and_firewalls(client, test_setup):
    """Test 4: Analytics snapshot includes risk/anticipation data and enforces State/Intel firewalls."""
    headers = {
        "X-Tenant-ID": test_setup["tenant_id"],
        "X-User-ID": test_setup["user_id"],
    }
    response = client.get("/api/v1/workspace/analytics-snapshot", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "epistemic_disclaimer" in data
    assert len(data["items"]) >= 1

    for item in data["items"]:
        assert item["epistemic_label"] in ("[DERIVED]", "[PREDICTION]")
        if item["is_state_firewall_active"]:
            assert "0" in str(item["firewall_note"])
        if item["is_intelligence_firewall_active"]:
            assert "Quantitative predictions permanently disabled" in str(item["firewall_note"])


def test_workspace_tenant_isolation(client, test_setup):
    """Test 5: Cross-tenant isolation blocks other tenants from seeing user data."""
    # Tenant B querying
    headers_b = {
        "X-Tenant-ID": "foreign_tenant_xyz",
        "X-User-ID": "foreign_user_xyz",
    }
    response = client.get("/api/v1/workspace/summary", headers=headers_b)
    assert response.status_code == 200
    data = response.json()

    # Tenant B has 0 watchlists and 0 active alerts
    assert data["total_watchlists"] == 0
    assert data["active_alerts"] == 0
    assert data["watched_bills"] == 0
    assert data["watched_companies"] == 0


def test_workspace_ai_assistant_grounding(client, test_setup):
    """Test 6: AI workspace assistant operates on authorized context only."""
    headers = {
        "X-Tenant-ID": test_setup["tenant_id"],
        "X-User-ID": test_setup["user_id"],
    }
    payload = {
        "question": "What changed in my watchlists?",
        "context_type": "workspace",
        "context_id": "workspace_home",
        "persona": "GENERAL_PUBLIC",
    }
    response = client.post("/api/v1/ai/ask", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["context_type"] == "workspace"
    assert "content" in data
    assert len(data["content"]) > 0
    # Must not give investment advice
    assert "disclaimer" in data
