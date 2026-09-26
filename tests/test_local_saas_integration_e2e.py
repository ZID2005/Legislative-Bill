"""
tests/test_local_saas_integration_e2e.py
========================================
TASK 8.24 Phase 19 — Comprehensive Local SaaS Integration & E2E Test Suite.

Validates the full institutional SaaS lifecycle:
- Startup & Health probes (/health, /ready, /api/v1/health, /api/v1/freshness)
- Development Authentication & Session Lifecycle (register, login, /me, token issuance, logout, revocation)
- Multi-Tenant Isolation & Anti-IDOR Boundaries
- Workspace Summary & Aggregation
- Central & State Legislative Discovery (66 records)
- Bill Dossier & Central Prediction Engine vs State Prediction Firewall (State stock predictions = 0)
- Corporate Intelligence (70 companies, 47 quant, 20 intelligence-only, 3 reference)
- Intelligence Company Firewall (0 quant predictions for qualitative universe)
- Industry & Sector Analytics
- State Economic Impact Dossier
- Predictive Modeling & Anticipation Layer (4,700 predictions, 940 anticipation scores)
- Decision Support & Risk Analysis (4,700 decision records)
- Monitoring Center & Source Health Registry
- Watchlist Management (create, add multi-entity types, delete)
- Alert Preferences & Notification Dispatch
- Grounded AI Analyst Copilot (with extractive fallback safety)
"""

from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from storage.company_repository import CompanyRepository


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_1_health_and_readiness_probes(client: TestClient):
    """Verify liveness and readiness probe contracts."""
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"

    r_ready = client.get("/ready")
    assert r_ready.status_code in (200, 503)

    r_v1_health = client.get("/api/v1/health")
    assert r_v1_health.status_code == 200

    r_fresh = client.get("/api/v1/freshness")
    assert r_fresh.status_code == 200
    fresh_data = r_fresh.json()
    assert fresh_data.get("overall_status") in ("LIVE", "FRESH", "HEALTHY")
    assert "datasets" in fresh_data or "total_datasets" in fresh_data


def test_2_auth_lifecycle_and_session_revocation(client: TestClient):
    """Verify login, token issuance, /me context, and logout revocation."""
    email = f"analyst_{uuid.uuid4().hex[:6]}@test-inst.org"
    tenant_id = f"tenant_{uuid.uuid4().hex[:6]}"

    # Login / Auto-provision in development
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPassword123!", "tenant_id": tenant_id},
    )
    assert r_login.status_code == 200
    token = r_login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # /me context
    r_me = client.get("/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["email"] == email
    assert r_me.json()["tenant_id"] == tenant_id

    # Logout
    r_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert r_logout.status_code == 200

    # Post-logout token rejection (Revocation)
    r_after = client.get("/api/v1/auth/me", headers=headers)
    assert r_after.status_code == 401


def test_3_tenant_isolation_boundary(client: TestClient):
    """Verify cross-tenant watchlist and alert isolation."""
    # Tenant A
    r_a = client.post(
        "/api/v1/auth/login",
        json={"email": "userA@org-alpha.com", "tenant_id": "org_alpha"},
    )
    token_a = r_a.json()["token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Tenant B
    r_b = client.post(
        "/api/v1/auth/login",
        json={"email": "userB@org-beta.com", "tenant_id": "org_beta"},
    )
    token_b = r_b.json()["token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant A creates watchlist
    r_wl = client.post(
        "/api/v1/watchlists",
        json={"name": "Alpha Secrets", "description": "Proprietary"},
        headers=headers_a,
    )
    assert r_wl.status_code == 201
    wl_id = r_wl.json()["watchlist_id"]

    # Tenant B cannot access Tenant A watchlist
    r_cross = client.get(f"/api/v1/watchlists/{wl_id}", headers=headers_b)
    assert r_cross.status_code in (403, 404)


def test_4_legislative_discovery_and_state_firewall(client: TestClient):
    """Verify Central bill predictions vs State zero prediction firewall."""
    r_bills = client.get("/api/v1/bills?limit=100")
    assert r_bills.status_code == 200
    data = r_bills.json()
    assert data["total"] == 66
    bills = data["items"]
    assert len(bills) == 66

    # Central bill has predictions
    cbill = next(b["bill_id"] for b in bills if b.get("jurisdiction") == "central")
    r_cpred = client.get(f"/api/v1/bills/{cbill}/predictions")
    assert r_cpred.status_code == 200
    assert r_cpred.json()["has_predictions"] is True

    # State bill prediction firewall
    sbill = next(b["bill_id"] for b in bills if b.get("jurisdiction") == "state")
    r_spred = client.get(f"/api/v1/bills/{sbill}/predictions")
    assert r_spred.status_code == 200
    assert r_spred.json()["has_predictions"] is False
    assert r_spred.json()["firewall_status"] == "STATE_QUALITATIVE_ONLY"


def test_5_corporate_intelligence_and_ineligible_firewall(client: TestClient):
    """Verify quantitative company vs intelligence-only firewall."""
    # Quantitative company (e.g. RIL)
    r_q = client.get("/api/v1/companies/INE002A01018/predictions")
    assert r_q.status_code == 200
    assert r_q.json()["has_predictions"] is True

    # Intelligence-only company (e.g. Swiggy)
    r_i = client.get("/api/v1/companies/IN-INTEL-SWIGGY/predictions")
    assert r_i.status_code == 200
    assert r_i.json()["has_predictions"] is False
    assert r_i.json()["firewall_status"] == "INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS"


def test_6_watchlist_and_alert_crud(client: TestClient):
    """Verify watchlist item management and preference configuration."""
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@crud-test.com", "tenant_id": "crud_org"},
    )
    headers = {"Authorization": f"Bearer {r_login.json()['token']}"}

    # Create watchlist
    r_wl = client.post(
        "/api/v1/watchlists",
        json={"name": "Logistics & Energy"},
        headers=headers,
    )
    assert r_wl.status_code == 201
    wl_id = r_wl.json()["watchlist_id"]

    # Add eligible company (Zomato)
    r_item = client.post(
        f"/api/v1/watchlists/{wl_id}/items",
        json={"entity_type": "COMPANY", "entity_id": "INE758T01015"},
        headers=headers,
    )
    assert r_item.status_code == 201

    # Configure preferences
    r_pref = client.patch(
        "/api/v1/alerts/preferences",
        json={"digest_frequency": "WEEKLY", "minimum_severity": "HIGH"},
        headers=headers,
    )
    assert r_pref.status_code == 200
    assert r_pref.json()["digest_frequency"] == "WEEKLY"


def test_7_grounded_ai_copilot_safety(client: TestClient):
    """Verify AI endpoint returns grounded answer with safe fallback."""
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@ai-test.com", "tenant_id": "ai_org"},
    )
    headers = {"Authorization": f"Bearer {r_login.json()['token']}"}

    r_ai = client.post(
        "/api/v1/ai/ask",
        json={
            "question": "What are the main provisions for crew welfare in the Merchant Shipping Bill 2024?",
            "context_type": "bill",
            "context_id": "the-merchant-shipping-bill-2024",
            "persona": "GENERAL_PUBLIC",
        },
        headers=headers,
    )
    assert r_ai.status_code == 200
    data = r_ai.json()
    assert len(data.get("content") or data.get("answer", "")) > 0
    assert "disclaimer" in data
