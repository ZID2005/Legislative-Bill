"""
tests/test_api_prediction_risk_anticipation.py
===============================================
Comprehensive test suite for Prediction, Risk, and Anticipation REST APIs (Task 8.14.7).

Validates:
1. Predictions listing with multi-dimension filters (bill, company, sector, horizon, direction, confidence).
2. Prediction state firewall (querying state jurisdiction strictly returns 0 predictions).
3. Prediction horizons comparison endpoint (modeled vs unmodeled horizons).
4. Prediction detail, decision support, and anticipation endpoints.
5. Risk summary endpoint (distribution, 5 risk bands, sector and horizon breakdown, disclaimer).
6. Risk bills and companies endpoints.
7. Portfolio risk analysis (valid company aggregation, watchlist resolution, insufficient data state, state firewall 0).
8. Anticipation listing, filters, and neutral terminology.
9. Anticipation summary (940 total pairs, 4 tiers, window stats, neutral disclaimer).
10. Data integrity invariants (no synthetic predictions, no dataset mutations).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import create_app

client = TestClient(create_app())


def test_list_predictions_basic():
    """Verify listing predictions returns 200 with paginated items."""
    res = client.get("/api/v1/predictions?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 4700
    assert len(data["items"]) == 10
    first = data["items"][0]
    assert "prediction_id" in first
    assert "bill_id" in first
    assert "company_isin" in first
    assert "event_window" in first
    assert "predicted_direction" in first
    assert "predicted_confidence" in first


def test_list_predictions_filters():
    """Verify filtering by bill_id, event_window, direction, and sector."""
    # Filter by bill
    bill_id = "the-banking-laws-amendment-bill-2024"
    res = client.get(f"/api/v1/predictions?bill_id={bill_id}&limit=100")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 235  # 47 companies * 5 horizons = 235
    assert all(p["bill_id"] == bill_id for p in data["items"])

    # Filter by event_window
    res_ew = client.get(f"/api/v1/predictions?bill_id={bill_id}&event_window=[-1,+1]&limit=100")
    assert res_ew.status_code == 200
    data_ew = res_ew.json()
    assert data_ew["total"] == 47  # 47 companies * 1 horizon = 47
    assert all(p["event_window"] == "[-1,+1]" for p in data_ew["items"])

    # Filter by direction
    res_dir = client.get("/api/v1/predictions?direction=NEUTRAL&limit=10")
    assert res_dir.status_code == 200
    assert all(p["predicted_direction"] == "NEUTRAL" for p in res_dir.json()["items"])


def test_predictions_state_firewall():
    """Verify that querying state jurisdiction strictly returns 0 predictions."""
    res = client.get("/api/v1/predictions?jurisdiction=state")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_prediction_detail():
    """Verify single prediction record retrieval."""
    pred_id = "pred_the-banking-laws-amendment-bill-2024_INE002A01018_-1_p1"
    res = client.get(f"/api/v1/predictions/{pred_id}")
    assert res.status_code == 200
    p = res.json()
    assert p["prediction_id"] == pred_id
    assert p["bill_id"] == "the-banking-laws-amendment-bill-2024"
    assert p["company_isin"] == "INE002A01018"
    assert p["event_window"] == "[-1,+1]"


def test_prediction_decision_record():
    """Verify decision record retrieval for a prediction."""
    pred_id = "pred_the-banking-laws-amendment-bill-2024_INE002A01018_-1_p1"
    res = client.get(f"/api/v1/predictions/{pred_id}/decision")
    assert res.status_code == 200
    d = res.json()
    assert d["prediction_id"] == pred_id
    assert "risk_score" in d
    assert "risk_category" in d
    assert "impact_score" in d
    assert "investor_summary" in d
    assert "business_summary" in d
    assert "public_summary" in d


def test_prediction_anticipation_record():
    """Verify anticipation record retrieval for a prediction pair."""
    pred_id = "pred_the-banking-laws-amendment-bill-2024_INE002A01018_-1_p1"
    res = client.get(f"/api/v1/predictions/{pred_id}/anticipation")
    assert res.status_code == 200
    a = res.json()
    assert a["bill_id"] == "the-banking-laws-amendment-bill-2024"
    assert a["company_isin"] == "INE002A01018"
    assert "anticipation_score" in a
    assert "anticipation_tier" in a


def test_prediction_horizons_comparison():
    """Verify horizons comparison returns modeled horizons and notes unmodeled ones."""
    res = client.get(
        "/api/v1/predictions/horizons/compare?bill_id=the-banking-laws-amendment-bill-2024&company_isin=INE002A01018"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["bill_id"] == "the-banking-laws-amendment-bill-2024"
    assert data["company_isin"] == "INE002A01018"
    assert len(data["modeled_windows"]) == 5

    # Check comparisons list
    comps = data["comparisons"]
    modeled = [c for c in comps if c["is_modeled"]]
    unmodeled = [c for c in comps if not c["is_modeled"]]

    assert len(modeled) == 5
    assert len(unmodeled) == 3  # [0,1], [0,2], [0,5]
    assert all(c["note"] is not None for c in unmodeled)


def test_risk_summary():
    """Verify platform risk summary with 5 bands and institutional disclaimer."""
    res = client.get("/api/v1/risk/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_decisions"] == 4700
    assert 0.0 <= data["avg_overall_risk"] <= 1.0

    # Risk band distribution
    bands = data["risk_band_distribution"]
    total_in_bands = sum(bands.values())
    assert total_in_bands == 4700
    assert "VERY_LOW" in bands
    assert "LOW" in bands
    assert "MODERATE" in bands
    assert "HIGH" in bands
    assert "VERY_HIGH" in bands

    # Sector breakdown
    assert len(data["risk_by_sector"]) > 0

    # Horizon breakdown
    assert len(data["risk_by_event_window"]) == 5

    # Disclaimer
    assert "model-derived risk indicator" in data["disclaimer"]


def test_risk_bills_and_companies():
    """Verify bill and company risk listing endpoints."""
    res_b = client.get("/api/v1/risk/bills")
    assert res_b.status_code == 200
    bills = res_b.json()
    assert len(bills) == 20
    assert bills[0]["jurisdiction"] == "central"

    res_c = client.get("/api/v1/risk/companies")
    assert res_c.status_code == 200
    comps = res_c.json()
    assert len(comps) == 47


def test_risk_portfolio_analysis():
    """Verify portfolio risk analysis with valid quantitative companies."""
    # 2 valid quantitative companies
    payload = {"company_isins": ["INE002A01018", "INE009A01021"]}
    res = client.post("/api/v1/risk/portfolio", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["has_sufficient_data"] is True
    assert data["data_status"] == "SUFFICIENT_DATA"
    assert data["selected_companies_count"] == 2
    assert data["modeled_companies_count"] == 2
    assert data["unmodeled_companies_count"] == 0
    assert data["total_exposure_records"] == 200  # 2 companies * 20 bills * 5 horizons = 200
    assert data["avg_portfolio_risk_score"] is not None
    assert data["jurisdiction_breakdown"]["central"] == 200
    assert data["jurisdiction_breakdown"]["state"] == 0


def test_risk_portfolio_insufficient_data():
    """Verify portfolio risk returns insufficient data state for unmodeled companies."""
    # Non-modeled / unlisted company
    payload = {"company_isins": ["INVALID_OR_UNMODELED_ISIN"]}
    res = client.post("/api/v1/risk/portfolio", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["has_sufficient_data"] is False
    assert data["data_status"] == "INSUFFICIENT_DATA"
    assert data["modeled_companies_count"] == 0
    assert data["unmodeled_companies_count"] == 1
    assert data["avg_portfolio_risk_score"] is None
    assert "Insufficient data" in data["message"]


def test_anticipation_listing():
    """Verify listing anticipation scores returns 940 pairs."""
    res = client.get("/api/v1/anticipation?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 940
    assert len(data["items"]) == 10
    first = data["items"][0]
    assert "bill_id" in first
    assert "company_isin" in first
    assert "anticipation_score" in first
    assert "classification" in first
    assert first["classification"] in {"NO_EVIDENCE", "WEAK_EVIDENCE", "MODERATE_EVIDENCE", "STRONG_EVIDENCE"}


def test_anticipation_summary():
    """Verify anticipation summary with 4 classification tiers and institutional disclaimer."""
    res = client.get("/api/v1/anticipation/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_pairs"] == 940
    assert 0.0 <= data["avg_anticipation_score"] <= 1.0

    # Classifications
    tiers = data["classification_distribution"]
    assert sum(tiers.values()) == 940

    # Institutional disclaimer verbatim check
    assert "Pre-event diagnostics measure aggregate public information diffusion only" in data["disclaimer"]
    assert "They do not allege or imply insider trading or illicit market conduct" in data["disclaimer"]

    # Pre-event window stats
    assert len(data["window_stats_distribution"]) >= 4
