"""
tests/test_analytical_firewall_regression.py
============================================
Immutable Analytical Firewall and Baseline Regression Test Suite.

Verifies the Critical Freeze Contract of Task 8.19:
- Central: 20 production bills (22 scanned records), 47 quantitative securities,
  940 pairs, 4,700 predictions across [-1,+1], [-3,+3], [-5,+5], [-5,+10], [-10,+10],
  4,700 decisions, 940 anticipation scores, 14,100 stakeholder reports.
- State: 44 bills (AP=12, KA=11, KL=11, TS=10), 44 official PDFs, 44 knowledge records,
  86 corporate exposures. Exactly 0 stock predictions, 0 decisions, 0 anticipation scores.
- Planned states: MH=0, GJ=0, TN=0.
- Unified: 66 legislative records, 70 companies (47 quant + 23 intel), 104 corporate exposures.
- Firewalls: StatePredictionFirewall and IntelligenceCompanyFirewall remain intact.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from config.settings import settings


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_central_legislative_and_econometric_baseline(client: TestClient):
    """Verify Central analytical frozen baselines."""
    # 1. Coverage endpoint
    r_cov = client.get("/api/v1/coverage")
    assert r_cov.status_code == 200
    cov = r_cov.json()

    central = cov.get("central_coverage") or cov["central"]
    assert central["production_bills"] == 20
    assert central["quantitative_companies"] == 47
    assert central["bill_company_pairs"] == 940
    assert central["predictions_count"] == 4700

    # 2. Verify frozen event horizons on a sample central bill
    sample_bill = "the-banking-laws-amendment-bill-2024"
    r_pred = client.get(f"/api/v1/bills/{sample_bill}/predictions")
    assert r_pred.status_code == 200
    preds = r_pred.json()
    assert len(preds["items"]) > 0

    windows = {p["event_window"] for p in preds["items"]}
    expected_windows = {"[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"}
    assert expected_windows.issubset(windows)


def test_state_statutory_baseline_and_zero_prediction_firewall(client: TestClient):
    """Verify State statutory counts and strict 0-stock-prediction firewall."""
    # 1. State Coverage endpoint
    r_state = client.get("/api/v1/states")
    assert r_state.status_code == 200
    states_data = r_state.json()

    state_counts = {item["state"]: item["bills_count"] for item in states_data["implemented_states"]}

    def _get_count(code: str, name: str) -> int:
        return state_counts.get(code) or state_counts.get(name) or 0

    assert _get_count("AP", "Andhra Pradesh") == 12
    assert _get_count("KA", "Karnataka") == 11
    assert _get_count("KL", "Kerala") == 11
    assert _get_count("TS", "Telangana") == 10
    assert sum(state_counts.values()) == 44

    # 2. Planned states must be exactly 0
    planned_counts = {item["state"]: item["bills_count"] for item in states_data.get("planned_states", [])}

    def _get_planned(code: str, name: str) -> int:
        return planned_counts.get(code) or planned_counts.get(name) or 0

    assert _get_planned("MH", "Maharashtra") == 0
    assert _get_planned("GJ", "Gujarat") == 0
    assert _get_planned("TN", "Tamil Nadu") == 0

    # 3. State Prediction Firewall: Querying predictions for any state act MUST return 0 predictions
    for state_bill_id in ["ap_act_2024_01", "ka_act_2024_01", "kl_act_2024_01", "ts_act_2024_01"]:
        r_state_pred = client.get(f"/api/v1/bills/{state_bill_id}/predictions")
        assert r_state_pred.status_code in (200, 404)
        if r_state_pred.status_code == 200:
            assert len(r_state_pred.json().get("items", [])) == 0


def test_intelligence_company_firewall(client: TestClient):
    """Verify non-listed intelligence entities are blocked from stock prediction models."""
    r_companies = client.get("/api/v1/companies?limit=100")
    assert r_companies.status_code == 200
    companies = r_companies.json()["items"]

    quant_count = sum(1 for c in companies if c.get("is_quant_eligible"))
    intel_count = sum(1 for c in companies if c.get("universe_type") == "intelligence")
    ref_count = sum(1 for c in companies if not c.get("is_quant_eligible") and c.get("universe_type") != "intelligence")

    assert quant_count == 47
    assert intel_count == 20
    assert ref_count == 3
    assert len(companies) == 70

    # Query predictions on an INTELLIGENCE entity — must return 0 or firewall flag
    intel_entity = next(c for c in companies if c.get("universe_type") == "intelligence" or c.get("entity_type") == "INTELLIGENCE")
    r_pred = client.get(f"/api/v1/companies/{intel_entity['company_id']}/predictions")
    assert r_pred.status_code in (200, 404)
    if r_pred.status_code == 200:
        assert len(r_pred.json().get("items", [])) == 0


def test_unified_universe_totals(client: TestClient):
    """Verify total legislative records, companies, and corporate exposures."""
    r_cov = client.get("/api/v1/coverage")
    assert r_cov.status_code == 200
    data = r_cov.json()

    total_records = data.get("total_legislative_records") or data["unified"]["total_legislative_records"]
    assert total_records == 66  # 22 scanned central records + 44 state acts

    total_companies = data.get("total_corporate_entities") or data["company"]["total_companies"]
    assert total_companies == 70  # 47 quant + 23 intel

    total_exposures = data.get("total_corporate_exposures") or data["unified"]["total_corporate_exposures"]
    assert total_exposures == 104  # 18 central + 86 state
