"""
tests/test_api_industries.py
============================
Comprehensive test suite for Industry & Sector Intelligence REST API (Task 8.14.8).

Validates:
1. Industry listing, pagination, filtering, and search.
2. Industry dossier retrieval across Level 1 (quantitative) and Level 2 (intelligence) coverage.
3. 13-section dossier structure and epistemic labeling ([FACT], [DERIVED], [INTERPRETATION], [PREDICTION]).
4. Visual economic transmission map generation.
5. Statutory firewalls:
   - StatePredictionFirewall (state stock predictions strictly 0)
   - IntelligenceCompanyFirewall (intelligence entities have market_prediction_available=False)
6. Grounded AI Ask endpoint with industry context.
7. Central baseline preservation invariants.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.dependencies import get_cached_predictions, get_cached_anticipation_scores

client = TestClient(create_app())


def test_list_industries_basic():
    """Verify listing industries returns 200 with paginated items."""
    res = client.get("/api/v1/industries?limit=50")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 35  # 36 canonical industries in platform universe
    assert len(data["items"]) > 0

    first = data["items"][0]
    assert "industry_id" in first
    assert "name" in first
    assert "sector" in first
    assert "coverage_level" in first
    assert "related_bills_count" in first
    assert "exposed_companies_count" in first
    assert "central_exposures_count" in first
    assert "state_exposures_count" in first
    assert "quantitative_companies_count" in first
    assert "intelligence_companies_count" in first
    assert "market_analysis_available" in first
    assert "economic_mechanisms" in first


def test_list_industries_filters():
    """Verify sector, jurisdiction, universe_type, and search filters."""
    # Sector filter
    res_sec = client.get("/api/v1/industries?sector=Technology")
    assert res_sec.status_code == 200
    data_sec = res_sec.json()
    assert all("technology" in item["sector"].lower() for item in data_sec["items"])

    # Jurisdiction filter (Central)
    res_c = client.get("/api/v1/industries?jurisdiction=central")
    assert res_c.status_code == 200
    data_c = res_c.json()
    assert all(item["central_exposures_count"] > 0 or item["quantitative_companies_count"] > 0 for item in data_c["items"])

    # Jurisdiction filter (State)
    res_s = client.get("/api/v1/industries?jurisdiction=state")
    assert res_s.status_code == 200
    data_s = res_s.json()
    assert all(item["state_exposures_count"] > 0 for item in data_s["items"])

    # Universe type filter (Quantitative)
    res_q = client.get("/api/v1/industries?universe_type=quantitative")
    assert res_q.status_code == 200
    data_q = res_q.json()
    assert all(item["quantitative_companies_count"] > 0 for item in data_q["items"])

    # Search filter
    res_srch = client.get("/api/v1/industries?search=auto")
    assert res_srch.status_code == 200
    data_srch = res_srch.json()
    assert any("auto" in item["name"].lower() for item in data_srch["items"])


def test_get_industry_dossier_level_1():
    """Verify complete dossier retrieval for a Level 1 quantitative industry (Automobiles)."""
    res = client.get("/api/v1/industries/automobiles")
    assert res.status_code == 200
    data = res.json()

    # Section A: Header
    assert data["industry_id"] == "automobiles"
    assert data["name"] == "Automobiles"
    assert data["sector"] == "Manufacturing"
    assert data["coverage_level"] == 1
    assert data["total_companies_count"] == 6
    assert data["quantitative_companies_count"] == 6
    assert data["market_analysis_available"] is True

    # Section B: Executive Overview (4-zone epistemic)
    assert len(data["facts"]) > 0
    assert len(data["derived"]) > 0
    assert len(data["interpretations"]) > 0
    assert len(data["predictions"]) > 0

    # Section C: Legislative Footprint
    assert "central_bills" in data
    assert "state_bills" in data
    assert isinstance(data["central_bills"], list)
    assert isinstance(data["state_bills"], list)

    # Section D: Corporate Exposure
    assert len(data["quantitative_companies"]) == 6
    for comp in data["quantitative_companies"]:
        assert comp["is_quant_eligible"] is True
        assert comp["market_prediction_available"] is True

    # Section E: Economic Transmission Chains
    assert len(data["transmission_chains"]) > 0
    chain = data["transmission_chains"][0]
    stages = [node["stage"] for node in chain]
    assert "LEGISLATION" in stages
    assert "ECONOMIC_MECHANISM" in stages
    assert "INDUSTRY" in stages
    assert "COMPANY_EXPOSURE" in stages
    assert "MARKET_ANALYSIS" in stages

    # Section F: Market Intelligence
    market_intel = data["market_intelligence"]
    assert market_intel["modeled"] is True
    assert "total_predictions" in market_intel
    assert market_intel["total_predictions"] > 0
    assert "sample_predictions" in market_intel

    # Section G: State Intelligence & Firewall
    state_intel = data["state_intelligence"]
    assert state_intel["state_stock_predictions"] == 0
    assert "State stock predictions remain strictly 0" in state_intel["firewall_statement"]

    # Section H: Risk Context
    risk_summary = data["risk_summary"]
    assert risk_summary["epistemic_badge"] == "DERIVED"
    assert "risk_band_distribution" in risk_summary

    # Section I: Anticipation Context
    ant_summary = data["anticipation_summary"]
    assert ant_summary["epistemic_badge"] == "DERIVED"
    assert "diffusion_tier_distribution" in ant_summary
    assert "Pre-event diagnostics measure aggregate public information diffusion only" in ant_summary["verbatim_disclaimer"]

    # Section K & M: Related Industries & Provenance
    assert isinstance(data["related_industries"], list)
    assert len(data["provenance_sources"]) >= 2


def test_get_industry_dossier_level_2():
    """Verify dossier retrieval for a Level 2 qualitative corporate intelligence industry (Food Delivery & Quick Commerce)."""
    res = client.get("/api/v1/industries/food-delivery-quick-commerce")
    assert res.status_code == 200
    data = res.json()

    assert data["coverage_level"] == 2
    assert data["market_analysis_available"] is False
    assert data["quantitative_companies_count"] == 0
    assert data["intelligence_companies_count"] == 2

    # Intelligence companies must have market_prediction_available = False
    for comp in data["intelligence_companies"]:
        assert comp["is_quant_eligible"] is False
        assert comp["market_prediction_available"] is False

    # Market intelligence indicates unmodeled
    assert data["market_intelligence"]["modeled"] is False
    assert "Zero" in data["market_intelligence"]["notice"] or "not modeled" in data["market_intelligence"]["notice"]

    # State firewall
    assert data["state_intelligence"]["state_stock_predictions"] == 0


def test_get_industry_dossier_not_found():
    """Verify 404 for non-existent industry."""
    res = client.get("/api/v1/industries/space-tourism-quantum")
    assert res.status_code == 404
    body = res.json()
    msg = body.get("error", {}).get("message", "") or str(body)
    assert "not found" in msg.lower()


def test_get_industry_bills():
    """Verify industry bills sub-endpoint."""
    res = client.get("/api/v1/industries/automobiles/bills")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


def test_get_industry_companies():
    """Verify industry companies sub-endpoint."""
    res = client.get("/api/v1/industries/automobiles/companies")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] == 6
    assert all(c["is_quant_eligible"] is True for c in data["items"])


def test_ai_ask_industry_context():
    """Verify grounded AI question answering with industry context."""
    payload = {
        "question": "Which companies are exposed to legislation in this industry?",
        "context_type": "industry",
        "context_id": "automobiles",
        "persona": "INVESTOR",
    }
    res = client.post("/api/v1/ai/ask", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["context_type"] == "industry"
    assert data["context_id"] == "automobiles"
    assert "disclaimer" in data
    assert len(data["content"]) > 10


def test_central_baseline_preservation():
    """Verify that adding Industry intelligence does not mutate frozen Central records."""
    all_preds, _ = get_cached_predictions()
    assert len(all_preds) == 4700

    all_ants = get_cached_anticipation_scores()
    assert len(all_ants) == 940
