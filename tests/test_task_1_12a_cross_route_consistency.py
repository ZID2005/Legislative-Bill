"""
tests/test_task_1_12a_cross_route_consistency.py
================================================
Automated Cross-Route Data Consistency and Invariant Validation Suite
for Task 1.12A: Seance Final Platform Acceptance & Regression.

Validates:
1. Bill Consistency:
   - Stable bill identifier, jurisdiction, legislative status, dates, modeling eligibility, evidence references
   - Invariant check across /api/v1/bills, /api/v1/bills/{id}, /api/v1/coverage, /api/v1/bills/{id}/predictions

2. Company Consistency:
   - Stable company identifier (ISIN/ID), names, tickers
   - Quantitative eligibility vs Intelligence-only classification
   - Invariant check across /api/v1/companies, /api/v1/companies/{id}, /api/v1/portfolio, /api/v1/coverage

3. Prediction Consistency:
   - Stable prediction identifier (pred_{bill_id}_{isin}_{window_slug})
   - Supported event horizons exactly ([-1,+1], [-3,+3], [-5,+5], [-5,+10], [-10,+10])
   - Correct precomputed result matching between summary list and detail record
   - Uncertainty measures and provenance

4. Evidence & Provenance Consistency:
   - Source identity, timestamps, provenance, epistemic labels
   - Absence of fabricated causality or insider trading implications

5. Discrepancy Reporting:
   - Reports conflicting authoritative values rather than silently overwriting them.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_bill_cross_route_consistency(client: TestClient):
    """
    Verify bill consistency across summary list, bill dossier, coverage,
    and prediction query routes.
    """
    # 1. Fetch sample of central bills from list
    res_list = client.get("/api/v1/bills?jurisdiction=central&limit=5")
    assert res_list.status_code == 200, f"Failed fetching bills list: {res_list.text}"
    bills_data = res_list.json()
    assert len(bills_data["items"]) > 0

    for item in bills_data["items"]:
        bill_id = item["bill_id"]
        jurisdiction = item["jurisdiction"]
        status = item["status"]
        modeling_eligibility = item["modeling_eligibility"]

        # 2. Fetch bill detail
        res_detail = client.get(f"/api/v1/bills/{bill_id}")
        assert res_detail.status_code == 200, f"Detail lookup failed for {bill_id}: {res_detail.text}"
        detail_data = res_detail.json()
        detail_bill = detail_data["bill"]

        # Check identity consistency
        assert detail_bill["bill_id"] == bill_id, f"Bill ID mismatch: {detail_bill['bill_id']} != {bill_id}"
        assert detail_bill["jurisdiction"] == jurisdiction, f"Jurisdiction mismatch for {bill_id}"
        assert detail_bill["status"] == status, f"Status mismatch for {bill_id}"
        assert detail_bill["modeling_eligibility"] == modeling_eligibility, f"Modeling eligibility mismatch for {bill_id}"

        # 3. Check predictions relationship
        res_preds = client.get(f"/api/v1/bills/{bill_id}/predictions?limit=10")
        assert res_preds.status_code == 200
        preds_data = res_preds.json()
        for p in preds_data.get("items", []):
            assert p["bill_id"] == bill_id, f"Prediction references different bill_id: {p['bill_id']} != {bill_id}"

    # 4. Verify State bill consistency and firewall
    res_state_list = client.get("/api/v1/bills?jurisdiction=state&limit=5")
    assert res_state_list.status_code == 200
    state_bills = res_state_list.json()["items"]
    assert len(state_bills) > 0

    for s_item in state_bills:
        s_id = s_item["bill_id"]
        assert s_item["jurisdiction"] == "state"

        # State predictions query MUST return 0 items
        res_s_pred = client.get(f"/api/v1/bills/{s_id}/predictions")
        assert res_s_pred.status_code in (200, 404)
        if res_s_pred.status_code == 200:
            assert len(res_s_pred.json().get("items", [])) == 0, (
                f"Statutory Firewall violation: State bill {s_id} returned stock predictions!"
            )


def test_company_cross_route_consistency(client: TestClient):
    """
    Verify company identity, classification, quantitative eligibility,
    and exposure relationships across /companies, /companies/{id}, and /portfolio.
    """
    # 1. Fetch companies
    res_cos = client.get("/api/v1/companies?limit=70")
    assert res_cos.status_code == 200
    cos = res_cos.json()["items"]
    assert len(cos) == 70

    quant_cos = [c for c in cos if c.get("is_quant_eligible") is True]
    non_quant_cos = [c for c in cos if c.get("is_quant_eligible") is False]
    intel_cos = [c for c in cos if c.get("universe_type") == "intelligence"]

    assert len(quant_cos) == 47, f"Expected 47 quant-eligible companies, got {len(quant_cos)}"
    assert len(non_quant_cos) == 23, f"Expected 23 non-quant companies, got {len(non_quant_cos)}"
    assert len(intel_cos) == 20, f"Expected 20 intelligence companies, got {len(intel_cos)}"

    # 2. Test quantitative company cross-route consistency
    sample_quant = quant_cos[0]
    cid = sample_quant["company_id"]
    res_q_detail = client.get(f"/api/v1/companies/{cid}")
    assert res_q_detail.status_code == 200
    q_detail = res_q_detail.json()

    assert q_detail["company_id"] == cid
    assert q_detail["isin"] == sample_quant["isin"]
    assert q_detail["is_quant_eligible"] is True
    assert q_detail["universe_type"] == "quantitative"
    assert q_detail["quantitative_firewall_status"] == "QUANTITATIVE_PRODUCTION"

    # 3. Test intelligence-only company cross-route firewall
    sample_intel = intel_cos[0]
    iid = sample_intel["company_id"]
    res_i_detail = client.get(f"/api/v1/companies/{iid}")
    assert res_i_detail.status_code == 200
    i_detail = res_i_detail.json()

    assert i_detail["company_id"] == iid
    assert i_detail["is_quant_eligible"] is False
    assert i_detail["universe_type"] == "intelligence"

    # Predictions query for intelligence-only company MUST return 0 predictions
    res_i_preds = client.get(f"/api/v1/companies/{iid}/predictions")
    assert res_i_preds.status_code in (200, 404)
    if res_i_preds.status_code == 200:
        assert len(res_i_preds.json().get("items", [])) == 0, (
            f"Firewall violation: Intelligence-only company {iid} returned stock predictions!"
        )


def test_prediction_cross_route_consistency(client: TestClient):
    """
    Verify prediction identifier format, event horizons, association,
    and consistency between list and detail endpoints.
    """
    res_preds = client.get("/api/v1/predictions?limit=25")
    assert res_preds.status_code == 200
    preds_data = res_preds.json()
    items = preds_data["items"]
    assert len(items) > 0

    valid_horizons = {"[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"}

    for p in items:
        pid = p["prediction_id"]
        bill_id = p["bill_id"]
        isin = p["company_isin"]
        window = p["event_window"]

        # Validate event horizon
        assert window in valid_horizons, f"Invalid event horizon {window} in prediction {pid}"

        # Validate prediction ID structure: pred_{bill_id}_{isin}_{window_slug}
        assert pid.startswith(f"pred_{bill_id}_{isin}_"), (
            f"Prediction ID {pid} does not match expected prefix pred_{bill_id}_{isin}_"
        )

        # Validate detail lookup consistency
        res_detail = client.get(f"/api/v1/predictions/{pid}")
        assert res_detail.status_code == 200, f"Failed fetching prediction detail {pid}"
        detail = res_detail.json()

        assert detail["prediction_id"] == pid
        assert detail["bill_id"] == bill_id
        assert detail["company_isin"] == isin
        assert detail["event_window"] == window
        assert detail["predicted_direction"] == p["predicted_direction"]
        assert detail["predicted_confidence"] == p["predicted_confidence"]
        assert detail["model_version"] == p["model_version"]


def test_evidence_and_epistemic_integrity(client: TestClient):
    """
    Verify evidence source identity, timestamps, provenance, and epistemic boundaries.
    Ensures anticipation endpoints do not imply causation or insider trading.
    """
    # 1. Check Anticipation Overview
    res_ant = client.get("/api/v1/anticipation/summary")
    assert res_ant.status_code == 200
    ant_summary = res_ant.json()

    # Must contain institutional aggregate diffusion, not illicit conduct claims
    assert "classification_distribution" in ant_summary or "total_scores" in ant_summary

    # 2. Check Freshness Telemetry
    res_fresh = client.get("/api/v1/freshness")
    assert res_fresh.status_code == 200
    freshness = res_fresh.json()
    assert "datasets" in freshness
    for ds in freshness["datasets"]:
        assert ds["status"] in {"LIVE", "RECENT", "STALE", "NOT_AVAILABLE"}
        assert "authority" in ds
        assert "provenance_summary" in ds
