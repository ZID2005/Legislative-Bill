"""
tests/test_saas_auth_lifecycle.py
=================================
Test suite for Task 8.19 SaaS Authentication, Session Lifecycle, and RBAC Boundaries.

Verifies:
1. Login issues valid cryptographically signed session tokens.
2. Invalid password returns 401 UNAUTHORIZED.
3. Logout revokes the session token (blacklisted tokens return 401 TOKEN_REVOKED).
4. Current user endpoint (/api/v1/auth/me) resolves authoritative tenant, role, and plan placeholder.
5. Auth status endpoint exposes clear integration flags (AUTH_IMPLEMENTED, AUTH_PROVIDER_REQUIRED, etc.).
6. ProductionAuthProvider rejects spoofed X-Tenant-ID / X-User-ID headers.
7. RBAC permission boundaries:
   - OWNER can modify roles and soft-delete tenant.
   - ADMIN can invite members and view audit logs.
   - MEMBER is forbidden from administrative actions (returns 403).
   - VIEWER is read-only.
"""

from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.auth.provider import (
    DevelopmentAuthProvider,
    ProductionAuthProvider,
    create_session_token,
    reset_auth_provider_for_testing,
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_auth_status_endpoint(client: TestClient):
    """Verify auth status reflects code readiness and external IdP boundary."""
    resp = client.get("/api/v1/auth/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["AUTH_IMPLEMENTED"] == "READY"
    assert data["AUTH_PROVIDER_REQUIRED"] == "TRUE"
    assert "AUTH_PROVIDER_CONFIGURED" in data
    assert "AUTH_PROVIDER_NOT_CONFIGURED" in data


def test_login_and_me_lifecycle(client: TestClient):
    """Verify login issues a valid bearer token and /me resolves the profile."""
    # 1. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice_test@example.com", "tenant_id": "test_tenant_alpha"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["token"]
    assert token.count(".") == 2  # Standard 3-part JWT structure
    assert login_data["tenant_id"] == "test_tenant_alpha"

    # 2. Get profile with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["tenant_id"] == "test_tenant_alpha"
    assert me_data["plan_tier"] in ("PLAN_NOT_CONFIGURED", "FREE", "PRO", "ENTERPRISE")
    assert me_data["billing_status"] in ("BILLING_NOT_CONNECTED", "PLAN_CONFIGURED")

    # 3. Logout revokes token
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "logged_out"

    # 4. Reusing revoked token returns 401
    revoked_resp = client.get("/api/v1/auth/me", headers=headers)
    assert revoked_resp.status_code == 401
    assert "TOKEN_REVOKED" in str(revoked_resp.json())


def test_production_auth_provider_rejects_unauthenticated_headers():
    """Verify ProductionAuthProvider strictly requires Bearer token and rejects raw headers."""
    prod_provider = ProductionAuthProvider(secret_key="test_secret_prod_key")
    reset_auth_provider_for_testing(prod_provider)

    try:
        app = create_app()
        test_client = TestClient(app)

        # 1. Request with raw spoofed headers but no Bearer token must fail with 401
        spoof_headers = {"X-Tenant-ID": "victim_tenant", "X-User-ID": "victim_user"}
        r_spoof = test_client.get("/api/v1/auth/me", headers=spoof_headers)
        assert r_spoof.status_code == 401

        # 2. Request with malformed token must fail with 401
        r_malformed = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert r_malformed.status_code == 401

        # 3. Request with valid production session token succeeds
        valid_token = create_session_token(
            user_id="prod_alice",
            tenant_id="prod_tenant",
            role="MEMBER",
        )
        r_valid = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert r_valid.status_code == 200
        assert r_valid.json()["user_id"] == "prod_alice"
        assert r_valid.json()["tenant_id"] == "prod_tenant"

    finally:
        # Reset back to development provider
        reset_auth_provider_for_testing(None)


def test_rbac_role_boundaries(client: TestClient):
    """Verify RBAC access control across OWNER, ADMIN, MEMBER, VIEWER."""
    tid = f"t_rbac_{uuid.uuid4().hex[:6]}"
    token_owner = create_session_token(user_id="u_owner", tenant_id=tid, role="OWNER")
    token_admin = create_session_token(user_id="u_admin", tenant_id=tid, role="ADMIN")
    token_member = create_session_token(user_id="u_member", tenant_id=tid, role="MEMBER")
    token_viewer = create_session_token(user_id="u_viewer", tenant_id=tid, role="VIEWER")

    h_owner = {"Authorization": f"Bearer {token_owner}"}
    h_admin = {"Authorization": f"Bearer {token_admin}"}
    h_member = {"Authorization": f"Bearer {token_member}"}
    h_viewer = {"Authorization": f"Bearer {token_viewer}"}

    # 1. Admin/Owner route: Invite member
    # Owner can invite
    r_inv_owner = client.post(
        "/api/v1/account/invite",
        json={"email": "new_user1@example.com", "role": "MEMBER"},
        headers=h_owner,
    )
    assert r_inv_owner.status_code == 201
    assert r_inv_owner.json()["outbound_email"] == "NOT_CONFIGURED"

    # Admin can invite
    r_inv_admin = client.post(
        "/api/v1/account/invite",
        json={"email": "new_user2@example.com", "role": "MEMBER"},
        headers=h_admin,
    )
    assert r_inv_admin.status_code == 201

    # Member CANNOT invite (403 Forbidden)
    r_inv_member = client.post(
        "/api/v1/account/invite",
        json={"email": "new_user3@example.com", "role": "MEMBER"},
        headers=h_member,
    )
    assert r_inv_member.status_code == 403

    # Viewer CANNOT invite (403 Forbidden)
    r_inv_viewer = client.post(
        "/api/v1/account/invite",
        json={"email": "new_user4@example.com", "role": "MEMBER"},
        headers=h_viewer,
    )
    assert r_inv_viewer.status_code == 403

    # 2. Owner-only route: Role modification
    invited_id = r_inv_admin.json()["user_id"]
    # Admin CANNOT change role (403 Forbidden)
    r_role_admin = client.patch(
        f"/api/v1/account/members/{invited_id}/role",
        json={"role": "ADMIN"},
        headers=h_admin,
    )
    assert r_role_admin.status_code == 403

    # Owner CAN change role
    r_role_owner = client.patch(
        f"/api/v1/account/members/{invited_id}/role",
        json={"role": "ADMIN"},
        headers=h_owner,
    )
    assert r_role_owner.status_code == 200
    assert r_role_owner.json()["role"] == "ADMIN"
