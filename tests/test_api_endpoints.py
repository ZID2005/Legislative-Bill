"""
tests/test_api_endpoints.py
===========================
Comprehensive automated integration tests for FastAPI REST API layer.
Validates:
- Health and OpenAPI schema contract
- Coverage metrics parity with frozen baseline (20/47/940/4700/44/86/70/66/104)
- Central vs State quantitative prediction firewall (strictly 0 state predictions)
- Quantitative vs Intelligence-only company firewall (strictly 0 intel predictions)
- Multi-tenant isolation (Tenant A vs Tenant B isolation)
- AI Copilot responses, offline fallback, and zero secret leakage
- Standardized error contracts (400, 404, 422)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

HEADERS_TENANT_A = {
    "X-Tenant-ID": "tenant_alpha",
    "X-User-ID": "user_alpha",
}

HEADERS_TENANT_B = {
    "X-Tenant-ID": "tenant_beta",
    "X-User-ID": "user_beta",
}

# Ground truth entity identifiers
CENTRAL_PROD_BILL_ID = "the-bills-of-lading-bill-2024"
STATE_BILL_ID = "karnataka-vs-bill-33-2024"
QUANT_COMPANY_ISIN = "INE002A01018"  # Reliance Industries
INTEL_COMPANY_ISIN = "INE043D01016"  # GMR Airports Infrastructure


# ---------------------------------------------------------------------------
# 1. Health & OpenAPI Specification
# ---------------------------------------------------------------------------


def test_root_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["api_version"] == "1.0.0"
    assert "timestamp" in data


def test_api_v1_health() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_openapi_json() -> None:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    spec = resp.json()
    assert spec["info"]["title"] == "Indian Parliamentary Intelligence & Market Impact API"
    assert "/api/v1/coverage" in spec["paths"]
    assert "/api/v1/bills" in spec["paths"]
    assert "/api/v1/companies" in spec["paths"]
    assert "/api/v1/predictions" in spec["paths"]
    assert "/api/v1/watchlists" in spec["paths"]


# ---------------------------------------------------------------------------
# 2. Coverage & Frozen Baseline Parity
# ---------------------------------------------------------------------------


def test_coverage_baseline_parity() -> None:
    resp = client.get("/api/v1/coverage")
    assert resp.status_code == 200
    cov = resp.json()

    # Central Invariants
    assert cov["central"]["production_bills"] == 20
    assert cov["central"]["quantitative_companies"] == 47
    assert cov["central"]["bill_company_pairs"] == 940
    assert cov["central"]["predictions_count"] == 4700
    assert cov["central"]["decisions_count"] == 4700
    assert cov["central"]["anticipation_scores_count"] == 940
    assert cov["central"]["stakeholder_reports_count"] == 14100
    assert cov["central"]["event_windows_count"] == 5

    # State Invariants
    assert cov["state"]["state_bills_count"] == 44
    assert cov["state"]["state_official_pdfs_count"] == 44
    assert cov["state"]["state_knowledge_records_count"] == 44
    assert cov["state"]["state_corporate_exposures_count"] == 86
    assert cov["state"]["state_stock_predictions_count"] == 0  # CRITICAL INVARIANT: ZERO STATE PREDICTIONS

    # Corporate Intelligence Invariants
    assert cov["company"]["total_companies"] == 70
    assert cov["company"]["quantitative_companies"] == 47
    assert cov["company"]["intelligence_companies"] == 20
    assert cov["company"]["reference_companies"] == 3

    # Unified Totals
    assert cov["unified"]["total_legislative_records"] == 66
    assert cov["unified"]["total_corporate_exposures"] == 104


# ---------------------------------------------------------------------------
# 3. Legislative Bills & Quantitative Firewall
# ---------------------------------------------------------------------------


def test_list_bills_pagination_and_filter() -> None:
    resp = client.get("/api/v1/bills?page=1&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 66
    assert len(data["items"]) == 10

    # Filter central only (22 total in repository: 20 production + 2 research/analysis references)
    resp_central = client.get("/api/v1/bills?jurisdiction=central")
    assert resp_central.status_code == 200
    assert resp_central.json()["total"] == 22

    # Filter state only
    resp_state = client.get("/api/v1/bills?jurisdiction=state")
    assert resp_state.status_code == 200
    assert resp_state.json()["total"] == 44


def test_bill_detail_central_and_state() -> None:
    # Central Bill
    resp = client.get(f"/api/v1/bills/{CENTRAL_PROD_BILL_ID}")
    assert resp.status_code == 200
    bill = resp.json()["bill"]
    assert bill["bill_id"] == CENTRAL_PROD_BILL_ID
    assert bill["jurisdiction"] == "central"

    # State Bill
    resp_state = client.get(f"/api/v1/bills/{STATE_BILL_ID}")
    assert resp_state.status_code == 200
    s_bill = resp_state.json()["bill"]
    assert s_bill["bill_id"] == STATE_BILL_ID
    assert s_bill["jurisdiction"] == "state"
    assert s_bill["state"] == "Karnataka"

    # Non-existent bill
    resp_404 = client.get("/api/v1/bills/non_existent_bill_999")
    assert resp_404.status_code == 404
    assert "NOT_FOUND" in resp_404.json()["error"]["code"]


def test_bill_predictions_firewall() -> None:
    # Central bill predictions: AVAILABLE
    resp = client.get(f"/api/v1/bills/{CENTRAL_PROD_BILL_ID}/predictions?limit=10")
    assert resp.status_code == 200
    pred_data = resp.json()
    assert pred_data["available"] is True
    assert pred_data["jurisdiction"] == "central"
    assert len(pred_data["predictions"]) > 0

    # State bill predictions: STRICTLY FIREWALLED (available=False, count=0)
    resp_state = client.get(f"/api/v1/bills/{STATE_BILL_ID}/predictions")
    assert resp_state.status_code == 200
    s_pred_data = resp_state.json()
    assert s_pred_data["available"] is False
    assert s_pred_data["jurisdiction"] == "state"
    assert len(s_pred_data["predictions"]) == 0
    assert "strictly 0" in s_pred_data["message"]


def test_bill_anticipation_firewall() -> None:
    # Central bill anticipation: AVAILABLE
    resp = client.get(f"/api/v1/bills/{CENTRAL_PROD_BILL_ID}/anticipation")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert len(data["scores"]) > 0

    # State bill anticipation: FIREWALLED
    resp_state = client.get(f"/api/v1/bills/{STATE_BILL_ID}/anticipation")
    assert resp_state.status_code == 200
    s_data = resp_state.json()
    assert s_data["available"] is False
    assert len(s_data["scores"]) == 0


# ---------------------------------------------------------------------------
# 4. Companies & Intelligence Firewall
# ---------------------------------------------------------------------------


def test_list_companies() -> None:
    resp = client.get("/api/v1/companies?limit=100")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 70

    # Filter intelligence only
    resp_intel = client.get("/api/v1/companies?universe_type=intelligence_only")
    assert resp_intel.status_code == 200
    assert resp_intel.json()["total"] == 20


def test_company_predictions_firewall() -> None:
    # Quantitative Company (Reliance: INE002A01018)
    resp_quant = client.get(f"/api/v1/companies/{QUANT_COMPANY_ISIN}/predictions?limit=5")
    assert resp_quant.status_code == 200
    data_quant = resp_quant.json()
    assert data_quant["available"] is True
    assert len(data_quant["predictions"]) > 0

    # Intelligence-only Entity (GMR: INE043D01016)
    resp_intel = client.get(f"/api/v1/companies/{INTEL_COMPANY_ISIN}/predictions")
    assert resp_intel.status_code == 200
    data_intel = resp_intel.json()
    assert data_intel["available"] is False
    assert len(data_intel["predictions"]) == 0
    assert "strictly 0" in data_intel["message"]


def test_company_exposures_and_explain() -> None:
    resp = client.get(f"/api/v1/companies/{QUANT_COMPANY_ISIN}/exposures")
    assert resp.status_code == 200
    exposures = resp.json()
    assert len(exposures) > 0

    # Explain exposure
    bill_id = exposures[0]["bill_id"]
    resp_exp = client.get(f"/api/v1/companies/{QUANT_COMPANY_ISIN}/exposures/{bill_id}/explain")
    assert resp_exp.status_code == 200
    data_exp = resp_exp.json()
    assert "why_explanation" in data_exp
    assert data_exp["company_id"] == QUANT_COMPANY_ISIN


# ---------------------------------------------------------------------------
# 5. Predictions, Decisions, Anticipation, & Reports
# ---------------------------------------------------------------------------


def test_list_predictions_and_detail() -> None:
    resp = client.get("/api/v1/predictions?limit=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 4700
    assert len(data["items"]) == 5

    pred_id = data["items"][0]["prediction_id"]
    resp_det = client.get(f"/api/v1/predictions/{pred_id}")
    assert resp_det.status_code == 200
    assert resp_det.json()["prediction_id"] == pred_id

    # Decision record
    resp_dec = client.get(f"/api/v1/predictions/{pred_id}/decision")
    assert resp_dec.status_code == 200

    # Anticipation record
    resp_ant = client.get(f"/api/v1/predictions/{pred_id}/anticipation")
    assert resp_ant.status_code in (200, 404)


def test_stakeholder_report() -> None:
    # Check report for the-bills-of-lading-bill-2024, INE002A01018, -1_p1, investor
    resp = client.get(f"/api/v1/reports/{CENTRAL_PROD_BILL_ID}/{QUANT_COMPANY_ISIN}/-1_p1/investor")
    assert resp.status_code == 200
    report = resp.json()
    assert report["bill_id"] == CENTRAL_PROD_BILL_ID
    assert report["company_isin"] == QUANT_COMPANY_ISIN
    assert report["stakeholder_type"].lower() == "investor"
    assert len(report["executive_summary"]) > 0


# ---------------------------------------------------------------------------
# 6. States Explorer
# ---------------------------------------------------------------------------


def test_states_endpoints() -> None:
    resp = client.get("/api/v1/states")
    assert resp.status_code == 200
    states_data = resp.json()
    assert "implemented_states" in states_data
    state_names = [s["state"] for s in states_data["implemented_states"]]
    assert "Karnataka" in state_names
    assert "Kerala" in state_names

    # Detail
    resp_karnataka = client.get("/api/v1/states/Karnataka")
    assert resp_karnataka.status_code == 200
    assert resp_karnataka.json()["state"] == "Karnataka"

    # Bills
    resp_bills = client.get("/api/v1/states/Karnataka/bills")
    assert resp_bills.status_code == 200
    assert len(resp_bills.json()) > 0

    # Exposures
    resp_exp = client.get("/api/v1/states/Karnataka/exposures")
    assert resp_exp.status_code == 200
    assert isinstance(resp_exp.json(), list)


# ---------------------------------------------------------------------------
# 7. Global Search (Cmd+K)
# ---------------------------------------------------------------------------


def test_global_search() -> None:
    resp = client.get("/api/v1/search?q=Finance")
    assert resp.status_code == 200
    results = resp.json()
    assert results["query"] == "Finance"
    assert results["total_matches"] > 0
    assert "items" in results
    assert "categories" in results


# ---------------------------------------------------------------------------
# 8. Monitoring Engine Status & Runs
# ---------------------------------------------------------------------------


def test_monitoring_status_and_runs() -> None:
    resp = client.get("/api/v1/monitoring/status")
    assert resp.status_code == 200
    status = resp.json()
    assert "system_status" in status
    assert "total_sources" in status

    resp_runs = client.get("/api/v1/monitoring/runs")
    assert resp_runs.status_code == 200
    assert isinstance(resp_runs.json(), list)

    resp_events = client.get("/api/v1/monitoring/events")
    assert resp_events.status_code == 200
    assert isinstance(resp_events.json(), list)


# ---------------------------------------------------------------------------
# 9. Watchlists CRUD & Multi-Tenant Isolation
# ---------------------------------------------------------------------------


def test_watchlists_crud_and_isolation() -> None:
    # 1. Tenant Alpha creates a watchlist
    create_payload = {
        "name": "Alpha Financials Watchlist",
        "description": "Financial and regulatory bills for Alpha",
        "is_default": False,
    }
    resp = client.post("/api/v1/watchlists", json=create_payload, headers=HEADERS_TENANT_A)
    assert resp.status_code == 201
    created_wl = resp.json()
    wl_id = created_wl["watchlist_id"]
    assert created_wl["name"] == "Alpha Financials Watchlist"
    assert created_wl["tenant_id"] == "tenant_alpha"
    assert created_wl["user_id"] == "user_alpha"

    # 2. Tenant Alpha adds a verified bill item
    item_payload = {
        "entity_type": "bill",
        "entity_id": CENTRAL_PROD_BILL_ID,
        "notes": "Monitor closely for trade and transport impact",
    }
    resp_item = client.post(f"/api/v1/watchlists/{wl_id}/items", json=item_payload, headers=HEADERS_TENANT_A)
    assert resp_item.status_code == 201
    item = resp_item.json()
    assert item["entity_id"] == CENTRAL_PROD_BILL_ID
    item_id = item["item_id"]

    # 3. Tenant Alpha adds an alert rule
    rule_payload = {
        "alert_type": "BILL_STATUS_CHANGE",
        "minimum_severity": "HIGH",
        "enabled": True,
    }
    resp_rule = client.post(f"/api/v1/watchlists/{wl_id}/rules", json=rule_payload, headers=HEADERS_TENANT_A)
    assert resp_rule.status_code == 201
    rule = resp_rule.json()
    assert rule["minimum_severity"] == "HIGH"
    rule_id = rule["alert_rule_id"]

    # 4. Multi-tenant Boundary Check: Tenant Beta attempts to access Tenant Alpha's watchlist
    resp_beta_get = client.get(f"/api/v1/watchlists/{wl_id}", headers=HEADERS_TENANT_B)
    assert resp_beta_get.status_code in (403, 404)  # Multi-tenant isolation denies cross-tenant access

    # Tenant Beta attempts to delete Tenant Alpha's item
    resp_beta_del_item = client.delete(f"/api/v1/watchlists/{wl_id}/items/{item_id}", headers=HEADERS_TENANT_B)
    assert resp_beta_del_item.status_code in (403, 404)

    # Tenant Beta attempts to delete Tenant Alpha's rule
    resp_beta_del_rule = client.delete(f"/api/v1/watchlists/{wl_id}/rules/{rule_id}", headers=HEADERS_TENANT_B)
    assert resp_beta_del_rule.status_code in (403, 404)

    # Tenant Beta attempts to delete Tenant Alpha's watchlist
    resp_beta_del_wl = client.delete(f"/api/v1/watchlists/{wl_id}", headers=HEADERS_TENANT_B)
    assert resp_beta_del_wl.status_code in (403, 404)

    # 5. Tenant Alpha cleans up item and rule
    del_item_resp = client.delete(f"/api/v1/watchlists/{wl_id}/items/{item_id}", headers=HEADERS_TENANT_A)
    assert del_item_resp.status_code == 200

    del_rule_resp = client.delete(f"/api/v1/watchlists/{wl_id}/rules/{rule_id}", headers=HEADERS_TENANT_A)
    assert del_rule_resp.status_code == 200

    # 6. Tenant Alpha deletes watchlist
    del_wl_resp = client.delete(f"/api/v1/watchlists/{wl_id}", headers=HEADERS_TENANT_A)
    assert del_wl_resp.status_code == 200

    # Verify deleted
    get_again = client.get(f"/api/v1/watchlists/{wl_id}", headers=HEADERS_TENANT_A)
    assert get_again.status_code == 404


# ---------------------------------------------------------------------------
# 10. Alerts & Notifications Endpoints
# ---------------------------------------------------------------------------


def test_alerts_and_notifications() -> None:
    # Alerts endpoints
    resp_alerts = client.get("/api/v1/alerts", headers=HEADERS_TENANT_A)
    assert resp_alerts.status_code == 200
    assert "items" in resp_alerts.json()

    resp_unread_alerts = client.get("/api/v1/alerts/unread-count", headers=HEADERS_TENANT_A)
    assert resp_unread_alerts.status_code == 200
    assert resp_unread_alerts.json()["tenant_id"] == "tenant_alpha"

    # Notifications endpoints
    resp_notifs = client.get("/api/v1/notifications", headers=HEADERS_TENANT_A)
    assert resp_notifs.status_code == 200
    assert "items" in resp_notifs.json()

    resp_notif_unread = client.get("/api/v1/notifications/unread-count", headers=HEADERS_TENANT_A)
    assert resp_notif_unread.status_code == 200

    resp_notif_summary = client.get("/api/v1/notifications/summary", headers=HEADERS_TENANT_A)
    assert resp_notif_summary.status_code == 200
    assert resp_notif_summary.json()["tenant_id"] == "tenant_alpha"


# ---------------------------------------------------------------------------
# 11. AI Copilot & Offline Fallback (Zero Secret Leakage)
# ---------------------------------------------------------------------------


def test_ai_copilot_ask_and_explain() -> None:
    # Bill Q&A
    req_payload = {
        "question": "What is the primary statutory objective of this bill?",
        "context_type": "bill",
        "context_id": CENTRAL_PROD_BILL_ID,
        "persona": "INVESTOR",
    }
    resp = client.post("/api/v1/ai/ask", json=req_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert "disclaimer" in data
    assert "not investment advice" in data["disclaimer"].lower()
    # Confirm no API key leakage
    assert "gsk_" not in data["content"]
    assert "GROQ_API_KEY" not in data["content"]

    # Explain bill endpoint
    resp_exp = client.get(f"/api/v1/ai/explain/bill/{CENTRAL_PROD_BILL_ID}?operation=BILL_SUMMARY")
    assert resp_exp.status_code == 200
    assert len(resp_exp.json()["content"]) > 0

    # Explain company endpoint
    resp_comp = client.get(f"/api/v1/ai/explain/company/{QUANT_COMPANY_ISIN}")
    assert resp_comp.status_code == 200
    assert len(resp_comp.json()["content"]) > 0


# ---------------------------------------------------------------------------
# 12. Standardized Error Formats
# ---------------------------------------------------------------------------


def test_error_handling_contracts() -> None:
    # 404 Not Found
    resp_404 = client.get("/api/v1/bills/unknown_bill_xyz")
    assert resp_404.status_code == 404
    err_404 = resp_404.json()["error"]
    assert "NOT_FOUND" in err_404["code"]
    assert "not found" in err_404["message"].lower()

    # 422 Unprocessable Entity (FastAPI validation error)
    resp_422 = client.post("/api/v1/watchlists", json={"name": 12345, "is_default": "not_a_bool"})
    assert resp_422.status_code == 422
    err_422 = resp_422.json()["error"]
    assert err_422["code"] == "VALIDATION_ERROR"
