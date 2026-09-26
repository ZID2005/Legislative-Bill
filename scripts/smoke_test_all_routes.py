"""
scripts/smoke_test_all_routes.py
================================
Programmatic smoke testing for Task 8.16.
Probes all major static and dynamic routes and their corresponding REST API endpoints.
Validates:
- HTTP status 200 (or expected controlled responses)
- No unhandled exceptions (500)
- Correct response schemas and firewall invariants
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from api.app import create_app


def run_smoke_tests():
    print("=" * 70)
    print("TASK 8.16 — SYSTEM-WIDE ROUTE & API SMOKE TESTS")
    print("=" * 70)

    app = create_app()
    client = TestClient(app)

    auth_headers = {"X-Tenant-ID": "smoke_tenant", "X-User-ID": "smoke_user"}

    # 1. Health, Readiness, Docs, & Freshness
    health_routes = ["/health", "/ready", "/api/v1/health", "/api/v1/freshness", "/docs", "/openapi.json"]
    for r in health_routes:
        res = client.get(r)
        assert res.status_code == 200, f"Failed {r}: {res.status_code}"
        print(f"  [OK] {r} -> 200")

    # 2. Bills (Central & State)
    res = client.get("/api/v1/bills")
    assert res.status_code == 200
    bills_data = res.json()
    assert bills_data["total"] >= 66
    cbill = next((b["bill_id"] for b in bills_data["items"] if b.get("jurisdiction") == "central"), None)
    sbill = next((b["bill_id"] for b in bills_data["items"] if b.get("jurisdiction") == "state"), None)
    assert cbill, "No Central bill found"
    assert sbill, "No State bill found"
    print(f"  [OK] /api/v1/bills -> 200 (Found Central: {cbill}, State: {sbill})")

    # Central Bill detail & predictions
    res_cb = client.get(f"/api/v1/bills/{cbill}")
    assert res_cb.status_code == 200
    res_cb_p = client.get(f"/api/v1/bills/{cbill}/predictions")
    assert res_cb_p.status_code == 200
    assert res_cb_p.json()["has_predictions"] is True
    print(f"  [OK] Central Bill Detail & Predictions ({cbill}) -> 200")

    # State Bill detail & firewalled predictions
    res_sb = client.get(f"/api/v1/bills/{sbill}")
    assert res_sb.status_code == 200
    res_sb_p = client.get(f"/api/v1/bills/{sbill}/predictions")
    assert res_sb_p.status_code == 200
    assert res_sb_p.json()["has_predictions"] is False
    assert res_sb_p.json()["firewall_status"] == "STATE_QUALITATIVE_ONLY"
    print(f"  [OK] State Bill Detail & Firewalled Predictions ({sbill}) -> 200")

    # 3. Companies (Quantitative & Intelligence)
    res_c = client.get("/api/v1/companies")
    assert res_c.status_code == 200
    c_data = res_c.json()
    assert c_data["total"] == 70

    q_isin = "INE002A01018"
    i_isin = "IN-INTEL-SWIGGY"

    res_q = client.get(f"/api/v1/companies/{q_isin}")
    assert res_q.status_code == 200
    res_qp = client.get(f"/api/v1/companies/{q_isin}/predictions")
    assert res_qp.status_code == 200
    assert res_qp.json()["has_predictions"] is True
    print(f"  [OK] Quantitative Company ({q_isin}) -> 200 (Predictions Available)")

    res_i = client.get(f"/api/v1/companies/{i_isin}")
    assert res_i.status_code == 200
    res_ip = client.get(f"/api/v1/companies/{i_isin}/predictions")
    assert res_ip.status_code == 200
    assert res_ip.json()["has_predictions"] is False
    assert res_ip.json()["firewall_status"] == "INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS"
    print(f"  [OK] Intelligence Company ({i_isin}) -> 200 (Firewalled: 0 Predictions)")

    # 4. Industries & Sectors
    res_ind = client.get("/api/v1/industries")
    assert res_ind.status_code == 200
    ind_items = res_ind.json()["items"]
    sample_ind_id = ind_items[0]["industry_id"]

    res_ind_det = client.get(f"/api/v1/industries/{sample_ind_id}")
    assert res_ind_det.status_code == 200
    print(f"  [OK] Industries List & Detail ({sample_ind_id}) -> 200")

    # 5. Predictions & Analytics
    res_preds = client.get("/api/v1/predictions?limit=5")
    assert res_preds.status_code == 200
    p_items = res_preds.json()["items"]
    sample_pid = p_items[0]["prediction_id"]

    res_p_det = client.get(f"/api/v1/predictions/{sample_pid}")
    assert res_p_det.status_code == 200
    print(f"  [OK] Predictions List & Detail ({sample_pid}) -> 200")

    res_risk = client.get("/api/v1/risk/summary")
    assert res_risk.status_code == 200
    print("  [OK] /api/v1/risk/summary -> 200")

    res_ant = client.get("/api/v1/anticipation/summary")
    assert res_ant.status_code == 200
    print("  [OK] /api/v1/anticipation/summary -> 200")

    # 6. Monitoring & Coverage
    res_mon = client.get("/api/v1/monitoring/overview")
    assert res_mon.status_code == 200
    print("  [OK] /api/v1/monitoring/overview -> 200")

    res_cov = client.get("/api/v1/coverage")
    assert res_cov.status_code == 200
    cov = res_cov.json()
    assert cov["central"]["production_bills"] == 20
    assert cov["state"]["state_bills_count"] == 44
    assert cov["company"]["total_companies"] == 70
    assert cov["state"]["state_stock_predictions_count"] == 0
    print("  [OK] /api/v1/coverage -> 200 (Coverage baseline validated)")

    # 7. States
    res_st = client.get("/api/v1/states")
    assert res_st.status_code == 200
    res_st_det = client.get("/api/v1/states/Karnataka")
    assert res_st_det.status_code == 200
    print("  [OK] /api/v1/states & /states/Karnataka -> 200")

    # 8. Global Search (Cmd+K)
    res_s = client.get("/api/v1/search?q=Energy")
    assert res_s.status_code == 200
    s_data = res_s.json()
    assert s_data["total_matches"] > 0
    print(f"  [OK] /api/v1/search?q=Energy -> 200 ({s_data['total_matches']} matches across {list(s_data['categories'].keys())})")

    # 9. Workspace, Watchlists, Alerts, Notifications
    res_ws = client.get("/api/v1/workspace/summary", headers=auth_headers)
    assert res_ws.status_code == 200
    print("  [OK] /api/v1/workspace/summary -> 200")

    res_wl = client.get("/api/v1/watchlists", headers=auth_headers)
    assert res_wl.status_code == 200
    print("  [OK] /api/v1/watchlists -> 200")

    res_al = client.get("/api/v1/alerts", headers=auth_headers)
    assert res_al.status_code == 200
    print("  [OK] /api/v1/alerts -> 200")

    res_not = client.get("/api/v1/notifications", headers=auth_headers)
    assert res_not.status_code == 200
    print("  [OK] /api/v1/notifications -> 200")

    print("\n" + "=" * 70)
    print("ALL ROUTE SMOKE TESTS PASSED WITH 100% SUCCESS.")
    print("=" * 70)


if __name__ == "__main__":
    run_smoke_tests()
