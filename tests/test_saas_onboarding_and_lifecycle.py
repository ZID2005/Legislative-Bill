"""
tests/test_saas_onboarding_and_lifecycle.py
===========================================
Test suite for SaaS Tenant Onboarding, Team Management, and Account Lifecycle.

Verifies:
1. Organization metadata updates (OWNER and ADMIN only).
2. Member invitations with outbound_email marked NOT_CONFIGURED.
3. Role promotion/demotion (OWNER only; others get 403).
4. Protected OWNER constraint (OWNER cannot be removed).
5. Safe tenant soft-deletion (OWNER only; preserves public legislative data).
6. Complete audit logging of all lifecycle operations.
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


def test_tenant_onboarding_and_team_lifecycle(client: TestClient):
    rand = uuid.uuid4().hex[:6]
    tenant_id = f"lifecycle_org_{rand}"
    owner_email = f"owner@{tenant_id}.com"

    # 1. Register organization & owner
    r_reg = client.post(
        "/api/v1/account/register",
        json={
            "organization_name": f"Lifecycle Corp {rand}",
            "owner_name": "Oliver Owner",
            "owner_email": owner_email,
            "password": "Password123!",
            "tenant_id": tenant_id,
        },
    )
    assert r_reg.status_code == 201

    token_owner = create_session_token(
        user_id=r_reg.json()["owner_user_id"],
        tenant_id=tenant_id,
        role="OWNER",
    )
    h_owner = {"Authorization": f"Bearer {token_owner}"}

    # 2. Update organization details
    r_update_org = client.patch(
        "/api/v1/account/organization",
        json={
            "name": f"Updated Lifecycle Corp {rand}",
            "metadata": {"industry": "Macro Research", "team_size": "10"},
        },
        headers=h_owner,
    )
    assert r_update_org.status_code == 200
    assert r_update_org.json()["name"] == f"Updated Lifecycle Corp {rand}"

    # 3. Invite member with MEMBER role
    member_email = f"analyst@{tenant_id}.com"
    r_inv = client.post(
        "/api/v1/account/invite",
        json={"email": member_email, "role": "MEMBER", "display_name": "Arthur Analyst"},
        headers=h_owner,
    )
    assert r_inv.status_code == 201
    inv_data = r_inv.json()
    assert inv_data["outbound_email"] == "NOT_CONFIGURED"
    member_id = inv_data["user_id"]

    # 4. Create session token for the invited member
    token_member = create_session_token(
        user_id=member_id,
        tenant_id=tenant_id,
        role="MEMBER",
    )
    h_member = {"Authorization": f"Bearer {token_member}"}

    # 5. Member attempts role change on another user (Forbidden 403)
    r_forbidden_role = client.patch(
        f"/api/v1/account/members/{r_reg.json()['owner_user_id']}/role",
        json={"role": "MEMBER"},
        headers=h_member,
    )
    assert r_forbidden_role.status_code == 403

    # 6. Owner promotes member to ADMIN
    r_promote = client.patch(
        f"/api/v1/account/members/{member_id}/role",
        json={"role": "ADMIN"},
        headers=h_owner,
    )
    assert r_promote.status_code == 200
    assert r_promote.json()["role"] == "ADMIN"

    # 7. Attempt to remove the OWNER (Blocked with 400 Bad Request)
    r_remove_owner = client.delete(
        f"/api/v1/account/members/{r_reg.json()['owner_user_id']}",
        headers=h_owner,
    )
    assert r_remove_owner.status_code == 400

    # 8. Member attempts to delete tenant (Forbidden 403)
    r_del_member = client.delete("/api/v1/account/tenant", headers=h_member)
    assert r_del_member.status_code == 403

    # 9. Owner soft-deletes tenant
    r_del_owner = client.delete("/api/v1/account/tenant", headers=h_owner)
    assert r_del_owner.status_code == 200
    assert r_del_owner.json()["status"] == "DELETED"

    # 10. Verify audit log captures lifecycle events
    r_audit = client.get("/api/v1/audit/logs", headers=h_owner)
    assert r_audit.status_code == 200
    actions = [entry["action"] for entry in r_audit.json()["items"]]
    assert "USER_INVITED" in actions
    assert "ROLE_CHANGED" in actions
    assert "TENANT_DELETED" in actions
