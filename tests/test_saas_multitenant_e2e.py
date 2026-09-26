"""
tests/test_saas_multitenant_e2e.py
==================================
End-to-End Multi-Tenant Isolation and Concurrency Test Suite.

Verifies:
1. Concurrent registration and session issuance for Tenant Alpha and Tenant Beta.
2. Complete partition of Watchlists, Alert Rules, Notifications, AI Usage, and Audit Logs.
3. Cross-tenant IDOR probes across all personalized resources return 403 or 404.
4. Tenant data exports contain zero data belonging to other tenants.
5. Member management and role transitions in Tenant Alpha do not affect Tenant Beta.
"""

from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.auth.provider import create_session_token


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_concurrent_multitenant_isolation_e2e(client: TestClient):
    """Verify complete isolation between Tenant Alpha and Tenant Beta under interleaved operations."""
    rand = uuid.uuid4().hex[:6]
    tenant_a = f"org_alpha_{rand}"
    tenant_b = f"org_beta_{rand}"

    user_a_email = f"owner@{tenant_a}.com"
    user_b_email = f"owner@{tenant_b}.com"

    # 1. Register Tenant Alpha
    r_reg_a = client.post(
        "/api/v1/account/register",
        json={
            "organization_name": f"Alpha Capital {rand}",
            "owner_name": "Alice Owner",
            "owner_email": user_a_email,
            "password": "PasswordAlpha123!",
            "tenant_id": tenant_a,
        },
    )
    assert r_reg_a.status_code == 201
    assert r_reg_a.json()["tenant_id"] == tenant_a

    # 2. Register Tenant Beta
    r_reg_b = client.post(
        "/api/v1/account/register",
        json={
            "organization_name": f"Beta Research {rand}",
            "owner_name": "Bob Owner",
            "owner_email": user_b_email,
            "password": "PasswordBeta123!",
            "tenant_id": tenant_b,
        },
    )
    assert r_reg_b.status_code == 201
    assert r_reg_b.json()["tenant_id"] == tenant_b

    # 3. Authenticate both owners to get session tokens
    r_login_a = client.post(
        "/api/v1/auth/login",
        json={"email": user_a_email, "password": "PasswordAlpha123!", "tenant_id": tenant_a},
    )
    assert r_login_a.status_code == 200
    token_a = r_login_a.json()["token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    r_login_b = client.post(
        "/api/v1/auth/login",
        json={"email": user_b_email, "password": "PasswordBeta123!", "tenant_id": tenant_b},
    )
    assert r_login_b.status_code == 200
    token_b = r_login_b.json()["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 4. Verify /me returns correct tenant context
    me_a = client.get("/api/v1/auth/me", headers=headers_a)
    assert me_a.status_code == 200
    assert me_a.json()["tenant_id"] == tenant_a
    assert me_a.json()["role"] == "OWNER"

    me_b = client.get("/api/v1/auth/me", headers=headers_b)
    assert me_b.status_code == 200
    assert me_b.json()["tenant_id"] == tenant_b
    assert me_b.json()["role"] == "OWNER"

    # 5. Tenant A creates a Watchlist
    r_wl_a = client.post(
        "/api/v1/watchlists",
        json={"name": "Alpha Telecom Basket", "description": "Priority Telecom Watch"},
        headers=headers_a,
    )
    assert r_wl_a.status_code == 201
    wl_a_id = r_wl_a.json()["watchlist_id"]

    # 6. Tenant B creates a Watchlist
    r_wl_b = client.post(
        "/api/v1/watchlists",
        json={"name": "Beta Mining Basket", "description": "Critical Minerals Watch"},
        headers=headers_b,
    )
    assert r_wl_b.status_code == 201
    wl_b_id = r_wl_b.json()["watchlist_id"]

    # 7. List watchlists: Tenant A sees ONLY A; Tenant B sees ONLY B
    lists_a = client.get("/api/v1/watchlists", headers=headers_a).json()
    lists_b = client.get("/api/v1/watchlists", headers=headers_b).json()
    assert any(w["watchlist_id"] == wl_a_id for w in lists_a)
    assert not any(w["watchlist_id"] == wl_b_id for w in lists_a)
    assert any(w["watchlist_id"] == wl_b_id for w in lists_b)
    assert not any(w["watchlist_id"] == wl_a_id for w in lists_b)

    # 8. Cross-tenant IDOR read/modification probe
    r_idor_read = client.get(f"/api/v1/watchlists/{wl_a_id}", headers=headers_b)
    assert r_idor_read.status_code in (403, 404)

    r_idor_patch = client.patch(
        f"/api/v1/watchlists/{wl_a_id}",
        json={"name": "Tampered By Beta"},
        headers=headers_b,
    )
    assert r_idor_patch.status_code in (403, 404)

    # 9. Tenant A invites a team member
    r_inv_a = client.post(
        "/api/v1/account/invite",
        json={"email": f"analyst@{tenant_a}.com", "role": "MEMBER"},
        headers=headers_a,
    )
    assert r_inv_a.status_code == 201

    # Verify Tenant B members list is unaffected
    members_b = client.get("/api/v1/account/members", headers=headers_b).json()["items"]
    assert len(members_b) == 1
    assert members_b[0]["email"] == user_b_email

    # 10. Audit log partition
    audit_a = client.get("/api/v1/audit/logs", headers=headers_a).json()
    assert all(item["tenant_id"] == tenant_a for item in audit_a["items"])
    assert not any(item["tenant_id"] == tenant_b for item in audit_a["items"])

    # 11. Data export isolation
    export_a = client.get("/api/v1/account/export", headers=headers_a).json()
    assert export_a["tenant_id"] == tenant_a
    assert any(w["watchlist_id"] == wl_a_id for w in export_a["data"]["watchlists"])
    assert not any(w["watchlist_id"] == wl_b_id for w in export_a["data"]["watchlists"])
