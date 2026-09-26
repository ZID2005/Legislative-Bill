"""
tests/test_saas_user_journey_e2e.py
===================================
End-to-End Single User Journey Test Suite.

Simulates a real institutional analyst traversing the entire SaaS platform:
1. Register organization & OWNER account.
2. Authenticate and obtain cryptographically verified session token.
3. Fetch /me context (confirming OWNER role and BILLING_NOT_CONNECTED status).
4. Global search for legislative bills (Central & State).
5. Create custom portfolio watchlist and add items.
6. Configure alert delivery preferences.
7. Query grounded AI analyst with watchlist context (metered telemetry).
8. Inspect corporate exposure dossier for quantitative company.
9. Export full tenant portfolio package.
10. Terminate session via /logout (verifying token revocation).
"""

from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient

from api.app import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_full_user_journey_e2e(client: TestClient):
    rand = uuid.uuid4().hex[:6]
    tenant_id = f"journey_org_{rand}"
    owner_email = f"lead.analyst@{tenant_id}.com"
    password = "SecurePassword2026!"

    # 1. Organization & Owner Registration
    r_reg = client.post(
        "/api/v1/account/register",
        json={
            "organization_name": f"Global Quant Research {rand}",
            "owner_name": "Dr. Lead Analyst",
            "owner_email": owner_email,
            "password": password,
            "tenant_id": tenant_id,
        },
    )
    assert r_reg.status_code == 201
    assert r_reg.json()["billing_status"] == "BILLING_NOT_CONNECTED"

    # 2. Login to acquire session token
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": owner_email, "password": password, "tenant_id": tenant_id},
    )
    assert r_login.status_code == 200
    token = r_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Resolve authoritative user identity (/me)
    r_me = client.get("/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["email"] == owner_email
    assert r_me.json()["role"] == "OWNER"

    # 4. Search platform database
    r_search = client.get("/api/v1/search?q=telecom", headers=headers)
    assert r_search.status_code == 200
    search_data = r_search.json()
    assert search_data["total_matches"] > 0

    # 5. Create a custom watchlist and add bills
    r_wl = client.post(
        "/api/v1/watchlists",
        json={"name": "Priority Infrastructure", "description": "Core tech & infra bills"},
        headers=headers,
    )
    assert r_wl.status_code == 201
    wl_id = r_wl.json()["watchlist_id"]

    r_item = client.post(
        f"/api/v1/watchlists/{wl_id}/items",
        json={"entity_type": "COMPANY", "entity_id": "INE758T01015", "notes": "Key watch"},
        headers=headers,
    )
    assert r_item.status_code == 201

    # 6. Configure notification & alert preferences
    r_pref = client.patch(
        "/api/v1/alerts/preferences",
        json={
            "digest_frequency": "DAILY",
            "minimum_severity": "MEDIUM",
            "allowed_channels": ["IN_APP"],
        },
        headers=headers,
    )
    assert r_pref.status_code == 200
    assert r_pref.json()["digest_frequency"] == "DAILY"

    # 7. Ask Grounded AI Analyst with Watchlist context
    r_ai = client.post(
        "/api/v1/ai/ask",
        json={
            "question": "What are the regulatory implications for satcom spectrum allocation under the Telecom Act 2023?",
            "watchlist_id": wl_id,
        },
        headers=headers,
    )
    assert r_ai.status_code == 200
    ai_resp = r_ai.json()
    assert "answer" in ai_resp
    assert "context_sources" in ai_resp

    # 8. Check AI metering usage for this tenant
    r_usage = client.get("/api/v1/ai/usage", headers=headers)
    assert r_usage.status_code == 200
    usage_data = r_usage.json()
    assert usage_data["total_queries"] >= 1

    # 9. View corporate exposure dossier
    r_comp = client.get("/api/v1/companies/INE002A01018/dossier", headers=headers)
    assert r_comp.status_code == 200
    dossier = r_comp.json()
    assert dossier["isin"] == "INE002A01018"

    # 10. Export tenant data package
    r_export = client.get("/api/v1/account/export", headers=headers)
    assert r_export.status_code == 200
    export_payload = r_export.json()
    assert export_payload["tenant_id"] == tenant_id
    assert len(export_payload["data"]["watchlists"]) >= 1

    # 11. Logout and verify token is revoked
    r_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert r_logout.status_code == 200

    r_me_after = client.get("/api/v1/auth/me", headers=headers)
    assert r_me_after.status_code == 401
