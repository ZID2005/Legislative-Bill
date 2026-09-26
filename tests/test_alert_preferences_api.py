"""
tests/test_alert_preferences_api.py
===================================
Tests for user AlertPreference API endpoints, read-all actions, and digest feeds.
"""

import pytest
from fastapi.testclient import TestClient

from api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_alert_preferences_crud(client):
    """Test retrieval and update of AlertPreference."""
    headers = {
        "X-Tenant-ID": "test_pref_tenant",
        "X-User-ID": "test_pref_user",
    }

    # 1. Get default preferences
    get_res = client.get("/api/v1/alerts/preferences", headers=headers)
    assert get_res.status_code == 200
    pref = get_res.json()
    assert pref["user_id"] == "test_pref_user"
    assert pref["enabled"] is True
    assert "minimum_severity" in pref
    assert "digest_frequency" in pref

    # 2. Update preferences via PATCH
    update_payload = {
        "enabled": False,
        "minimum_severity": "HIGH",
        "digest_frequency": "DAILY_DIGEST",
    }
    patch_res = client.patch("/api/v1/alerts/preferences", json=update_payload, headers=headers)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["enabled"] is False
    assert updated["minimum_severity"] == "HIGH"
    assert updated["digest_frequency"] == "DAILY_DIGEST"

    # 3. Update preferences via PUT
    put_payload = {
        "enabled": True,
        "minimum_severity": "MEDIUM",
        "digest_frequency": "REAL_TIME",
    }
    put_res = client.put("/api/v1/alerts/preferences", json=put_payload, headers=headers)
    assert put_res.status_code == 200
    put_data = put_res.json()
    assert put_data["enabled"] is True
    assert put_data["minimum_severity"] == "MEDIUM"
    assert put_data["digest_frequency"] == "REAL_TIME"


def test_alert_read_all(client):
    """Test read-all for alerts via POST and PATCH."""
    headers = {
        "X-Tenant-ID": "test_pref_tenant",
        "X-User-ID": "test_pref_user",
    }

    post_res = client.post("/api/v1/alerts/read-all", headers=headers)
    assert post_res.status_code == 200
    assert "marked_count" in post_res.json()

    patch_res = client.patch("/api/v1/alerts/read-all", headers=headers)
    assert patch_res.status_code == 200
    assert "marked_count" in patch_res.json()


def test_notification_digests_endpoint(client):
    """Test notification digests endpoint."""
    headers = {
        "X-Tenant-ID": "test_pref_tenant",
        "X-User-ID": "test_pref_user",
    }

    res = client.get("/api/v1/notifications/digests", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)
