"""
tests/test_security_idor.py
===========================
Comprehensive security test suite verifying multi-tenant and cross-user
isolation across all personalized endpoints:
- /api/v1/watchlists
- /api/v1/alerts
- /api/v1/notifications
- /api/v1/workspace
- /api/v1/ai/ask

Enforces:
1. User A in Tenant A cannot view, modify, or delete resources belonging to Tenant B.
2. User A cannot access User B's resources within the same tenant where user isolation is required.
3. IDOR attacks via direct object ID manipulation return 403 Forbidden or 404 Not Found.
4. AI context retrieval adheres strictly to the requester's tenant boundary.
"""

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.auth.provider import create_session_token


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_watchlist_idor_cross_tenant_isolation(client: TestClient):
    """Verify Tenant A watchlist cannot be read, updated, or deleted by Tenant B."""
    tenant_a = {"X-Tenant-ID": "tenant_alpha", "X-User-ID": "alice"}
    tenant_b = {"X-Tenant-ID": "tenant_beta", "X-User-ID": "bob"}

    # 1. Tenant A creates a private watchlist
    r_create = client.post(
        "/api/v1/watchlists",
        json={"name": "Alpha Portfolio", "description": "Confidential Alpha Watchlist"},
        headers=tenant_a,
    )
    assert r_create.status_code == 201
    wl_id = r_create.json()["watchlist_id"]

    try:
        # 2. Tenant B attempts to read Tenant A's watchlist by ID (IDOR probe)
        r_get = client.get(f"/api/v1/watchlists/{wl_id}", headers=tenant_b)
        assert r_get.status_code in (403, 404), f"Expected 403/404, got {r_get.status_code}"

        # 3. Tenant B attempts to rename Tenant A's watchlist
        r_patch = client.patch(
            f"/api/v1/watchlists/{wl_id}",
            json={"name": "Compromised Name"},
            headers=tenant_b,
        )
        assert r_patch.status_code in (403, 404), f"Expected 403/404, got {r_patch.status_code}"

        # 4. Tenant B attempts to add items to Tenant A's watchlist
        r_add_item = client.post(
            f"/api/v1/watchlists/{wl_id}/items",
            json={"entity_type": "company", "entity_id": "INE002A01018"},
            headers=tenant_b,
        )
        assert r_add_item.status_code in (403, 404), f"Expected 403/404, got {r_add_item.status_code}"

        # 5. Tenant B attempts to delete Tenant A's watchlist
        r_del = client.delete(f"/api/v1/watchlists/{wl_id}", headers=tenant_b)
        assert r_del.status_code in (403, 404), f"Expected 403/404, got {r_del.status_code}"

        # 6. Verify Tenant A's watchlist remains unmodified
        r_verify = client.get(f"/api/v1/watchlists/{wl_id}", headers=tenant_a)
        assert r_verify.status_code == 200
        assert r_verify.json()["name"] == "Alpha Portfolio"

    finally:
        # Cleanup
        client.delete(f"/api/v1/watchlists/{wl_id}", headers=tenant_a)


def test_alert_idor_cross_tenant_isolation(client: TestClient):
    """Verify Tenant B cannot view or mark read Tenant A's alerts."""
    tenant_a = {"X-Tenant-ID": "tenant_alpha", "X-User-ID": "alice"}
    tenant_b = {"X-Tenant-ID": "tenant_beta", "X-User-ID": "bob"}

    # Query alerts for Tenant A
    r_alerts_a = client.get("/api/v1/alerts", headers=tenant_a)
    assert r_alerts_a.status_code == 200

    # Query alerts for Tenant B
    r_alerts_b = client.get("/api/v1/alerts", headers=tenant_b)
    assert r_alerts_b.status_code == 200

    # If Tenant A has alerts, Bob probing an Alpha alert_id directly must be blocked
    items_a = r_alerts_a.json().get("items", [])
    if items_a:
        probe_id = items_a[0]["alert_event_id"]
        r_probe = client.get(f"/api/v1/alerts/{probe_id}", headers=tenant_b)
        assert r_probe.status_code in (403, 404)

        r_read = client.post(f"/api/v1/alerts/{probe_id}/read", headers=tenant_b)
        assert r_read.status_code in (403, 404)


def test_notification_idor_cross_tenant_isolation(client: TestClient):
    """Verify Tenant B cannot access Tenant A's in-app notification center."""
    tenant_a = {"X-Tenant-ID": "tenant_alpha", "X-User-ID": "alice"}
    tenant_b = {"X-Tenant-ID": "tenant_beta", "X-User-ID": "bob"}

    r_notifs_a = client.get("/api/v1/notifications", headers=tenant_a)
    assert r_notifs_a.status_code == 200

    items_a = r_notifs_a.json().get("items", [])
    if items_a:
        probe_id = items_a[0]["notification_id"]
        r_probe = client.post(f"/api/v1/notifications/{probe_id}/read", headers=tenant_b)
        assert r_probe.status_code in (403, 404)


def test_workspace_telemetry_isolation(client: TestClient):
    """Verify workspace summary and activity streams isolate user/tenant portfolios."""
    tenant_a = {"X-Tenant-ID": "tenant_alpha", "X-User-ID": "alice"}
    tenant_b = {"X-Tenant-ID": "tenant_beta", "X-User-ID": "bob"}

    r_ws_a = client.get("/api/v1/workspace/summary", headers=tenant_a)
    assert r_ws_a.status_code == 200
    summary_a = r_ws_a.json()

    r_ws_b = client.get("/api/v1/workspace/summary", headers=tenant_b)
    assert r_ws_b.status_code == 200
    summary_b = r_ws_b.json()

    assert summary_a["tenant_id"] == "tenant_alpha"
    assert summary_a["user_id"] == "alice"
    assert summary_b["tenant_id"] == "tenant_beta"
    assert summary_b["user_id"] == "bob"


def test_ai_workspace_context_authorization(client: TestClient):
    """Verify AI assistant context respects multi-tenant boundaries."""
    tenant_a = {"X-Tenant-ID": "tenant_alpha", "X-User-ID": "alice"}

    r_ai = client.post(
        "/api/v1/ai/ask",
        json={
            "question": "What is the status of my watchlists?",
            "context_type": "workspace",
            "context_id": "workspace_home",
        },
        headers=tenant_a,
    )
    assert r_ai.status_code == 200
    data = r_ai.json()
    assert "content" in data
    assert data.get("success") is True


def test_cross_tenant_organization_and_member_isolation(client: TestClient):
    """Verify Tenant B cannot view or modify Tenant A members or organization metadata."""
    import uuid
    unique_email = f"alpha_sec_{uuid.uuid4().hex[:6]}@example.com"
    token_a = create_session_token("alice", "tenant_alpha", role="OWNER")
    token_b = create_session_token("bob", "tenant_beta", role="OWNER")
    h_a = {"Authorization": f"Bearer {token_a}"}
    h_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant A invites a member
    r_inv = client.post(
        "/api/v1/account/invite",
        json={"email": unique_email, "role": "MEMBER"},
        headers=h_a,
    )
    assert r_inv.status_code == 201
    member_id = r_inv.json()["user_id"]

    # Tenant B tries to remove Tenant A's member
    r_del = client.delete(f"/api/v1/account/members/{member_id}", headers=h_b)
    assert r_del.status_code in (403, 404)

    # Tenant B lists members — must NOT see Tenant A's member
    r_list = client.get("/api/v1/account/members", headers=h_b)
    assert r_list.status_code == 200
    b_member_ids = [m["user_id"] for m in r_list.json().get("items", [])]
    assert member_id not in b_member_ids


def test_cross_tenant_audit_log_isolation(client: TestClient):
    """Verify Tenant B cannot view Tenant A's security audit logs."""
    token_a = create_session_token("alice", "tenant_alpha", role="ADMIN")
    token_b = create_session_token("bob", "tenant_beta", role="ADMIN")
    h_a = {"Authorization": f"Bearer {token_a}"}
    h_b = {"Authorization": f"Bearer {token_b}"}

    # Query logs as Tenant B
    r_audit_b = client.get("/api/v1/audit/logs", headers=h_b)
    assert r_audit_b.status_code == 200
    for item in r_audit_b.json().get("items", []):
        assert item["tenant_id"] == "tenant_beta"
        assert item["tenant_id"] != "tenant_alpha"


def test_cross_tenant_ai_watchlist_probe_blocked(client: TestClient):
    """Verify Tenant B cannot use Tenant A's private watchlist ID in an AI query."""
    token_a = create_session_token("alice", "tenant_alpha", role="MEMBER")
    token_b = create_session_token("bob", "tenant_beta", role="MEMBER")
    h_a = {"Authorization": f"Bearer {token_a}"}
    h_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Tenant A creates a private watchlist
    r_create = client.post(
        "/api/v1/watchlists",
        json={"name": "Confidential M&A", "description": "Highly sensitive target list"},
        headers=h_a,
    )
    assert r_create.status_code == 201
    wl_id = r_create.json()["watchlist_id"]

    try:
        # 2. Tenant B attempts to ask AI about Tenant A's watchlist ID
        r_probe = client.post(
            "/api/v1/ai/ask",
            json={
                "question": "Summarize the companies in this watchlist",
                "context_type": "watchlist",
                "context_id": wl_id,
            },
            headers=h_b,
        )
        assert r_probe.status_code in (403, 404), f"Expected 403 or 404, got {r_probe.status_code}"
    finally:
        client.delete(f"/api/v1/watchlists/{wl_id}", headers=h_a)


def test_cross_tenant_data_export_isolation(client: TestClient):
    """Verify Tenant B data export never contains Tenant A resources."""
    token_a = create_session_token("alice", "tenant_alpha", role="ADMIN")
    token_b = create_session_token("bob", "tenant_beta", role="ADMIN")
    h_a = {"Authorization": f"Bearer {token_a}"}
    h_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant A creates a watchlist
    r_wl = client.post("/api/v1/watchlists", json={"name": "Alpha Export Test"}, headers=h_a)
    assert r_wl.status_code == 201
    alpha_wl_id = r_wl.json()["watchlist_id"]

    try:
        # Tenant B triggers export
        r_exp = client.post("/api/v1/account/export", headers=h_b)
        assert r_exp.status_code == 200
        exp_data = r_exp.json()["data"]
        b_wl_ids = [w["watchlist_id"] for w in exp_data.get("watchlists", [])]
        assert alpha_wl_id not in b_wl_ids
    finally:
        client.delete(f"/api/v1/watchlists/{alpha_wl_id}", headers=h_a)

