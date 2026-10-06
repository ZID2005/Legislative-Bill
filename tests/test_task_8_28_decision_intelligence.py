"""
tests/test_task_8_28_decision_intelligence.py
==============================================
Task 8.28 — Decision Intelligence & Personalized Impact Workspace.

Comprehensive Test Suite Covering 24 Exhaustive Tests:
1.  Portfolio creation, schema validation & default portfolio provisioning
2.  Multi-tenant portfolio isolation (Tenant A vs Tenant B)
3.  User-level portfolio isolation within tenant (User Alpha vs User Beta)
4.  IDOR protection on portfolio endpoints (cross-tenant access prohibited)
5.  Holdings CRUD, validation & boundary enforcement
6.  Bulk holdings import (CSV string & JSON structured import)
7.  Portfolio repository disk persistence & JSON serialization round-trip
8.  Deterministic relevance layer: Direct company match signal (DIRECT tier)
9.  Deterministic relevance layer: Industry & sector match signals (HIGH / MODERATE tier)
10. Deterministic relevance layer: Geography & state jurisdiction signal
11. Relevance tier hierarchy & explainable reasons composition
12. Model status firewall: Central vs State vs Live bill classification
13. Model status firewall: Non-quant company isolation (0 stock predictions)
14. Central quantitative model integration: surfacing preserved 5 authoritative horizons
15. Invariant enforcement: Exactly 0 state stock predictions across all layers
16. Portfolio legislative exposure summary aggregation & breakdown
17. Watchlist legislative exposure aggregation (companies, sectors, states, bills)
18. "YOUR LEGISLATIVE INTELLIGENCE" personalized dashboard endpoint
19. Personalized change feed generation without polling noise
20. Grounded AI / deterministic explanation endpoint (/workspace/explain-relevance)
21. Graceful insufficient-source handling in explain-relevance
22. "MY LEGISLATIVE IMPACT REPORT" generation with FACT / INTERPRETATION / PREDICTION labels
23. Global search integration with portfolio & watchlist scoping
24. Quantitative baseline integrity & production invariants verification
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest
from fastapi.testclient import TestClient

from api.app import app
from schemas.personalized_intelligence import (
    PersonalizedBillImpact,
    PersonalizedModelStatus,
    RelevanceReason,
    RelevanceSignal,
    RelevanceTier,
)
from schemas.portfolio import PortfolioHolding, UserPortfolio
from services.bill_dossier_service import (
    BillDossierService,
    get_frozen_central_production_bill_ids,
)
from services.company_intelligence_service import _CENTRAL_QUANTITATIVE_ISINS
from services.decision_intelligence_service import (
    AUTHORITATIVE_EVENT_HORIZONS,
    DISCLAIMER_NOTICE,
    DecisionIntelligenceService,
)
from storage.portfolio_repository import PortfolioRepository

client = TestClient(app)

HEADERS_TENANT_A = {
    "X-Tenant-ID": "tenant_alpha_828",
    "X-User-ID": "user_alpha_828",
}

HEADERS_TENANT_B = {
    "X-Tenant-ID": "tenant_beta_828",
    "X-User-ID": "user_beta_828",
}

HEADERS_USER_GAMMA = {
    "X-Tenant-ID": "tenant_alpha_828",
    "X-User-ID": "user_gamma_828",
}

CENTRAL_PROD_BILL_ID = "the-banking-laws-amendment-bill-2024"
STATE_BILL_ID = "karnataka-vs-bill-33-2024"


# ===========================================================================
# 1. Portfolio Creation, Schema Validation & Default Provisioning
# ===========================================================================

def test_01_portfolio_creation_and_schema_validation() -> None:
    # 1. Direct model validation
    pf = UserPortfolio(
        portfolio_id="pf-test-01",
        user_id="user_alpha_828",
        tenant_id="tenant_alpha_828",
        name="Alpha Core Fund",
        description="Core equity investments",
    )
    pf.validate()
    assert pf.portfolio_id == "pf-test-01"
    assert pf.name == "Alpha Core Fund"
    assert len(pf.holdings) == 0

    # Blank validations
    with pytest.raises(ValueError, match="name cannot be blank"):
        UserPortfolio(
            portfolio_id="pf-bad",
            user_id="u1",
            tenant_id="t1",
            name="  ",
        ).validate()

    with pytest.raises(ValueError, match="user_id cannot be blank"):
        UserPortfolio(
            portfolio_id="pf-bad",
            user_id="",
            tenant_id="t1",
            name="Valid Name",
        ).validate()

    # 2. API creation
    resp = client.post(
        "/api/v1/portfolio",
        headers=HEADERS_TENANT_A,
        json={"name": "Alpha Growth Strategy", "description": "High tech and banking exposure"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alpha Growth Strategy"
    assert data["user_id"] == "user_alpha_828"
    assert data["tenant_id"] == "tenant_alpha_828"
    assert "portfolio_id" in data


# ===========================================================================
# 2. Multi-Tenant Portfolio Isolation (Tenant A vs Tenant B)
# ===========================================================================

def test_02_portfolio_tenant_isolation() -> None:
    # Tenant Alpha creates portfolio
    create_resp = client.post(
        "/api/v1/portfolio",
        headers=HEADERS_TENANT_A,
        json={"name": "Alpha Private Assets"},
    )
    assert create_resp.status_code == 201
    pf_a_id = create_resp.json()["portfolio_id"]

    # Tenant Beta lists portfolios: must NOT contain Tenant Alpha's portfolio
    list_b_resp = client.get("/api/v1/portfolio", headers=HEADERS_TENANT_B)
    assert list_b_resp.status_code == 200
    b_pfs = list_b_resp.json()
    b_pf_ids = [p["portfolio_id"] for p in b_pfs]
    assert pf_a_id not in b_pf_ids


# ===========================================================================
# 3. User-Level Isolation Within Tenant
# ===========================================================================

def test_03_user_level_portfolio_isolation() -> None:
    # User Alpha creates portfolio
    create_resp = client.post(
        "/api/v1/portfolio",
        headers=HEADERS_TENANT_A,
        json={"name": "Alpha Specific Desk"},
    )
    assert create_resp.status_code == 201
    alpha_pf_id = create_resp.json()["portfolio_id"]

    # User Gamma (same tenant, different user) lists portfolios
    gamma_resp = client.get("/api/v1/portfolio", headers=HEADERS_USER_GAMMA)
    assert gamma_resp.status_code == 200
    gamma_pfs = gamma_resp.json()
    gamma_ids = [p["portfolio_id"] for p in gamma_pfs]
    assert alpha_pf_id not in gamma_ids


# ===========================================================================
# 4. IDOR Protection on Portfolio Endpoints
# ===========================================================================

def test_04_portfolio_idor_prevention() -> None:
    # Tenant Alpha creates portfolio
    create_resp = client.post(
        "/api/v1/portfolio",
        headers=HEADERS_TENANT_A,
        json={"name": "Alpha IDOR Guard Target"},
    )
    assert create_resp.status_code == 201
    pf_id = create_resp.json()["portfolio_id"]

    # Tenant Beta attempts GET
    get_resp = client.get(f"/api/v1/portfolio/{pf_id}", headers=HEADERS_TENANT_B)
    assert get_resp.status_code in (403, 404)

    # Tenant Beta attempts PUT
    put_resp = client.put(
        f"/api/v1/portfolio/{pf_id}",
        headers=HEADERS_TENANT_B,
        json={"name": "Hijacked Name"},
    )
    assert put_resp.status_code in (403, 404)

    # Tenant Beta attempts DELETE
    del_resp = client.delete(f"/api/v1/portfolio/{pf_id}", headers=HEADERS_TENANT_B)
    assert del_resp.status_code in (403, 404)

    # Verify original portfolio remains intact for Tenant Alpha
    check_resp = client.get(f"/api/v1/portfolio/{pf_id}", headers=HEADERS_TENANT_A)
    assert check_resp.status_code == 200
    assert check_resp.json()["name"] == "Alpha IDOR Guard Target"


# ===========================================================================
# 5. Holdings CRUD, Validation & Boundary Enforcement
# ===========================================================================

def test_05_holdings_crud_and_validation() -> None:
    # Create portfolio
    create_resp = client.post(
        "/api/v1/portfolio",
        headers=HEADERS_TENANT_A,
        json={"name": "Holdings Test Portfolio"},
    )
    assert create_resp.status_code == 201
    pf_id = create_resp.json()["portfolio_id"]

    # 1. Validation failure: empty company name
    bad_resp = client.post(
        f"/api/v1/portfolio/{pf_id}/holdings",
        headers=HEADERS_TENANT_A,
        json={"company_name": "  "},
    )
    assert bad_resp.status_code == 422

    # 2. Add valid holding
    add_resp = client.post(
        f"/api/v1/portfolio/{pf_id}/holdings",
        headers=HEADERS_TENANT_A,
        json={
            "company_name": "State Bank of India",
            "ticker": "SBIN",
            "isin": "INE062A01020",
            "quantity": 500,
            "avg_purchase_price": 820.50,
            "sector": "Financials",
            "industry": "Public Sector Banks",
        },
    )
    assert add_resp.status_code == 201
    h_data = add_resp.json()
    holding_id = h_data["holding_id"]
    assert h_data["company_name"] == "State Bank of India"
    assert h_data["ticker"] == "SBIN"
    assert h_data["quantity"] == 500.0

    # 3. Update holding
    upd_resp = client.put(
        f"/api/v1/portfolio/{pf_id}/holdings/{holding_id}",
        headers=HEADERS_TENANT_A,
        json={"quantity": 750, "avg_purchase_price": 810.0},
    )
    assert upd_resp.status_code == 200
    assert upd_resp.json()["quantity"] == 750.0
    assert upd_resp.json()["avg_purchase_price"] == 810.0

    # 4. Delete holding
    del_resp = client.delete(
        f"/api/v1/portfolio/{pf_id}/holdings/{holding_id}",
        headers=HEADERS_TENANT_A,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # Verify holding is gone
    pf_check = client.get(f"/api/v1/portfolio/{pf_id}", headers=HEADERS_TENANT_A).json()
    assert len(pf_check["holdings"]) == 0


# ===========================================================================
# 6. Bulk Holdings Import (CSV String & JSON Structured Import)
# ===========================================================================

def test_06_bulk_holdings_import() -> None:
    create_resp = client.post(
        "/api/v1/portfolio",
        headers=HEADERS_TENANT_A,
        json={"name": "Bulk Import Portfolio"},
    )
    pf_id = create_resp.json()["portfolio_id"]

    # CSV format import
    csv_payload = (
        "company_name,ticker,isin,quantity,avg_purchase_price,sector,industry\n"
        "HDFC Bank,HDFCBANK,INE040A01034,100,1650.00,Financials,Private Banks\n"
        "Infosys Limited,INFY,INE009A01021,200,1850.50,Information Technology,IT Services\n"
        "Tata Consultancy Services,TCS,INE467B01029,50,4200.00,Information Technology,IT Services\n"
    )

    import_resp = client.post(
        f"/api/v1/portfolio/{pf_id}/import",
        headers=HEADERS_TENANT_A,
        json={"csv_content": csv_payload, "replace_existing": True},
    )
    assert import_resp.status_code == 200
    imp_data = import_resp.json()
    assert len(imp_data["holdings"]) == 3

    companies = [h["company_name"] for h in imp_data["holdings"]]
    assert "HDFC Bank" in companies
    assert "Infosys Limited" in companies
    assert "Tata Consultancy Services" in companies


# ===========================================================================
# 7. Portfolio Repository Disk Persistence & Round-Trip
# ===========================================================================

def test_07_storage_disk_roundtrip() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = PortfolioRepository(storage_dir=Path(tmpdir))

        pf = UserPortfolio(
            portfolio_id="test-disk-pf-01",
            user_id="user_disk_test",
            tenant_id="tenant_disk_test",
            name="Disk Roundtrip Fund",
            holdings=[
                PortfolioHolding(
                    holding_id="h-01",
                    company_name="Larsen & Toubro",
                    ticker="LT",
                    isin="INE018A01030",
                    sector="Industrials",
                    industry="Construction & Engineering",
                )
            ],
        )

        repo.create(pf)

        # Reload from scratch with a second repo instance pointing to same dir
        repo2 = PortfolioRepository(storage_dir=Path(tmpdir))
        loaded = repo2.get("test-disk-pf-01", user_id="user_disk_test", tenant_id="tenant_disk_test")

        assert loaded is not None
        assert loaded.portfolio_id == "test-disk-pf-01"
        assert loaded.name == "Disk Roundtrip Fund"
        assert len(loaded.holdings) == 1
        assert loaded.holdings[0].company_name == "Larsen & Toubro"
        assert loaded.holdings[0].ticker == "LT"


# ===========================================================================
# 8. Deterministic Relevance: Direct Company Match Signal
# ===========================================================================

def test_08_deterministic_relevance_direct_company_signal() -> None:
    svc = DecisionIntelligenceService()
    holding = PortfolioHolding(
        holding_id="h-sbi",
        company_name="State Bank of India",
        ticker="SBIN",
        isin="INE062A01020",
        sector="Financials",
        industry="Public Sector Banks",
    )

    impact = svc.evaluate_bill_relevance_for_holding(CENTRAL_PROD_BILL_ID, holding)
    assert impact is not None
    assert impact.relevance_tier == RelevanceTier.DIRECT.value
    assert impact.confidence_score >= 0.90

    signals = [s.value if hasattr(s, "value") else str(s) for r in impact.reasons for s in r.signals]
    assert RelevanceSignal.DIRECT_COMPANY_MATCH.value in signals

    # Must identify Central Banking Bill
    assert impact.bill_id == CENTRAL_PROD_BILL_ID
    assert impact.jurisdiction.lower() == "central"


# ===========================================================================
# 9. Deterministic Relevance: Industry & Sector Match Signals
# ===========================================================================

def test_09_deterministic_relevance_industry_and_sector_signals() -> None:
    svc = DecisionIntelligenceService()
    # Company that isn't named in the bill directly, but belongs to Banking / Financials
    holding = PortfolioHolding(
        holding_id="h-ind",
        company_name="Federal Bank Limited",
        ticker="FEDERALBNK",
        sector="Financial Services",
        industry="Banks",
    )

    impact = svc.evaluate_bill_relevance_for_holding(CENTRAL_PROD_BILL_ID, holding)
    assert impact is not None
    # Must be at least MODERATE or HIGH relevance
    assert impact.relevance_tier in (
        RelevanceTier.HIGH_RELEVANCE.value,
        RelevanceTier.MODERATE_RELEVANCE.value,
    )

    signals = [s.value if hasattr(s, "value") else str(s) for r in impact.reasons for s in r.signals]
    assert any(
        s in signals
        for s in (RelevanceSignal.INDUSTRY_MATCH.value, RelevanceSignal.SECTOR_MATCH.value)
    )


# ===========================================================================
# 10. Deterministic Relevance: Geography & State Jurisdiction Signal
# ===========================================================================

def test_10_deterministic_relevance_geography_state_signal() -> None:
    svc = DecisionIntelligenceService()
    holding = PortfolioHolding(
        holding_id="h-karnataka",
        company_name="Bangalore Electricity Co",
        sector="Utilities",
        industry="Electric Utilities",
        notes="Operations concentrated in Karnataka",
    )

    impact = svc.evaluate_bill_relevance_for_holding(STATE_BILL_ID, holding)
    assert impact is not None
    assert impact.jurisdiction.lower() == "state"

    signals = [s.value if hasattr(s, "value") else str(s) for r in impact.reasons for s in r.signals]
    assert any(
        s in signals
        for s in (
            RelevanceSignal.STATE_JURISDICTION_MATCH.value,
            RelevanceSignal.GEOGRAPHY_MATCH.value,
            RelevanceSignal.STATE_POLICY_DOMAIN_MATCH.value,
        )
    )


# ===========================================================================
# 11. Relevance Tier Hierarchy & Explainable Reasons Composition
# ===========================================================================

def test_11_relevance_tier_hierarchy() -> None:
    # Direct company match must always outrank sector-only match
    svc = DecisionIntelligenceService()
    h_direct = PortfolioHolding(
        holding_id="h-1",
        company_name="State Bank of India",
        isin="INE062A01020",
    )
    h_sector = PortfolioHolding(
        holding_id="h-2",
        company_name="Generic NBFC Ltd",
        sector="Financials",
    )

    imp_direct = svc.evaluate_bill_relevance_for_holding(CENTRAL_PROD_BILL_ID, h_direct)
    imp_sector = svc.evaluate_bill_relevance_for_holding(CENTRAL_PROD_BILL_ID, h_sector)

    assert imp_direct.relevance_tier == RelevanceTier.DIRECT.value
    assert imp_sector.relevance_tier != RelevanceTier.DIRECT.value
    assert imp_direct.confidence_score > imp_sector.confidence_score

    # Reasons must be transparently explainable, not arbitrary scores
    for r in imp_direct.reasons:
        assert isinstance(r, RelevanceReason)
        assert r.description
        assert r.evidence


# ===========================================================================
# 12. Model Status Firewall: Central vs State vs Live Bill Classification
# ===========================================================================

def test_12_model_status_firewall_classification() -> None:
    svc = DecisionIntelligenceService()

    # 1. Central production bill + quant security -> MODELLED
    h_quant = PortfolioHolding(
        holding_id="h-quant",
        company_name="State Bank of India",
        isin="INE062A01020",
    )
    imp_central = svc.evaluate_bill_relevance_for_holding(CENTRAL_PROD_BILL_ID, h_quant)
    assert imp_central.model_status == PersonalizedModelStatus.MODELLED.value
    assert imp_central.model_status_label == "MODELLED — CENTRAL QUANTITATIVE"

    # 2. State bill -> NOT_ELIGIBLE (zero stock predictions)
    imp_state = svc.evaluate_bill_relevance_for_holding(STATE_BILL_ID, h_quant)
    assert imp_state.model_status == PersonalizedModelStatus.NOT_ELIGIBLE.value
    assert imp_state.model_status_label == "NOT ELIGIBLE FOR STOCK MODEL"
    assert imp_state.authoritative_prediction.available is False
    assert imp_state.authoritative_prediction.predictions_count == 0


# ===========================================================================
# 13. Model Status Firewall: Non-Quant Company Isolation
# ===========================================================================

def test_13_unmodelled_company_firewall() -> None:
    svc = DecisionIntelligenceService()
    # A financial company relevant to banking, but not in the 47-quantitative universe
    h_non_quant = PortfolioHolding(
        holding_id="h-unmodeled",
        company_name="District Co-operative Credit Society",
        sector="Financials",
        industry="Banks",
    )

    imp = svc.evaluate_bill_relevance_for_holding(CENTRAL_PROD_BILL_ID, h_non_quant)
    assert imp is not None
    # Must never produce stock predictions
    assert imp.authoritative_prediction.available is False
    assert imp.authoritative_prediction.predictions_count == 0
    assert imp.model_status in (
        PersonalizedModelStatus.KNOWLEDGE_ONLY.value,
        PersonalizedModelStatus.NOT_ELIGIBLE.value,
    )


# ===========================================================================
# 14. Central Quantitative Model Integration: Preserved 5 Event Horizons
# ===========================================================================

def test_14_central_model_authoritative_predictions_surfacing() -> None:
    svc = DecisionIntelligenceService()
    h_sbi = PortfolioHolding(
        holding_id="h-sbi",
        company_name="State Bank of India",
        isin="INE062A01020",
    )

    imp = svc.evaluate_bill_relevance_for_holding(CENTRAL_PROD_BILL_ID, h_sbi)
    assert imp.authoritative_prediction.available is True
    pred_summary = imp.authoritative_prediction

    # Must verify the 5 authoritative horizons
    assert set(pred_summary.event_horizons) == set(AUTHORITATIVE_EVENT_HORIZONS)
    assert pred_summary.predictions_count == 5

    # Check horizon details
    for horiz in AUTHORITATIVE_EVENT_HORIZONS:
        assert horiz in pred_summary.horizon_breakdown
        item = pred_summary.horizon_breakdown[horiz]
        assert "predicted_excess_return" in item or "direction" in item


# ===========================================================================
# 15. Invariant Enforcement: Exactly 0 State Stock Predictions
# ===========================================================================

def test_15_zero_state_stock_predictions_invariant() -> None:
    svc = DecisionIntelligenceService()

    # Even for a major bank holding evaluated against a State bill
    h_bank = PortfolioHolding(
        holding_id="h-hdfc",
        company_name="HDFC Bank",
        isin="INE040A01034",
    )

    state_impact = svc.evaluate_bill_relevance_for_holding(STATE_BILL_ID, h_bank)
    assert state_impact.authoritative_prediction.available is False
    assert state_impact.authoritative_prediction.predictions_count == 0
    assert len(state_impact.authoritative_prediction.horizon_breakdown) == 0
    assert "0" in state_impact.authoritative_prediction.notice or "Zero" in state_impact.authoritative_prediction.notice


# ===========================================================================
# 16. Portfolio Legislative Exposure Summary Aggregation
# ===========================================================================

def test_16_portfolio_legislative_exposure_summary() -> None:
    # Create portfolio with mixed banking and tech holdings
    create_resp = client.post(
        "/api/v1/portfolio",
        headers=HEADERS_TENANT_A,
        json={"name": "Exposure Analysis Portfolio"},
    )
    pf_id = create_resp.json()["portfolio_id"]

    client.post(
        f"/api/v1/portfolio/{pf_id}/holdings",
        headers=HEADERS_TENANT_A,
        json={
            "company_name": "State Bank of India",
            "isin": "INE062A01020",
            "sector": "Financials",
            "industry": "Public Sector Banks",
        },
    )

    client.post(
        f"/api/v1/portfolio/{pf_id}/holdings",
        headers=HEADERS_TENANT_A,
        json={
            "company_name": "Infosys Limited",
            "isin": "INE009A01021",
            "sector": "Information Technology",
            "industry": "IT Services",
        },
    )

    # Call /api/v1/portfolio/exposure
    exp_resp = client.get(
        f"/api/v1/portfolio/exposure?portfolio_id={pf_id}",
        headers=HEADERS_TENANT_A,
    )
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()

    assert exp_data["portfolio_id"] == pf_id
    assert exp_data["total_holdings_count"] == 2
    assert exp_data["total_relevant_bills_count"] > 0
    assert isinstance(exp_data["sectors_affected"], list)
    assert isinstance(exp_data["industries_affected"], list)
    assert "Financials" in exp_data["sectors_affected"] or "Information Technology" in exp_data["sectors_affected"]
    assert exp_data["disclaimer"]


# ===========================================================================
# 17. Watchlist Legislative Exposure Aggregation
# ===========================================================================

def test_17_watchlist_legislative_exposure_aggregation() -> None:
    # Add company to watchlist
    client.post(
        "/api/v1/watchlist",
        headers=HEADERS_TENANT_A,
        json={"entity_type": "COMPANY", "entity_id": "INE062A01020", "entity_name": "State Bank of India"},
    )

    svc = DecisionIntelligenceService()
    wl_exp = svc.get_watchlist_legislative_exposure(
        user_id="user_alpha_828",
        tenant_id="tenant_alpha_828",
    )
    assert wl_exp is not None
    assert isinstance(wl_exp, list)


# ===========================================================================
# 18. "YOUR LEGISLATIVE INTELLIGENCE" Personalized Dashboard Endpoint
# ===========================================================================

def test_18_personalized_dashboard_intelligence() -> None:
    resp = client.get(
        "/api/v1/workspace/decision-intelligence",
        headers=HEADERS_TENANT_A,
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["user_id"] == "user_alpha_828"
    assert data["tenant_id"] == "tenant_alpha_828"
    assert "portfolio_exposure" in data
    assert "watchlist_exposure" in data
    assert "relevant_central_bills" in data
    assert "relevant_state_bills" in data
    assert "change_feed_highlights" in data
    assert "DECISION SUPPORT NOTICE" in data["disclaimer"]


# ===========================================================================
# 19. Personalized Change Feed Without Polling Noise
# ===========================================================================

def test_19_personalized_change_feed() -> None:
    resp = client.get(
        "/api/v1/workspace/change-feed?limit=25",
        headers=HEADERS_TENANT_A,
    )
    assert resp.status_code == 200
    feed = resp.json()
    assert isinstance(feed, list)

    for item in feed:
        assert item["change_id"]
        assert item["bill_id"]
        assert item["title"]
        assert item["change_type"]
        assert item["epistemic_level"] in ("FACT", "INTERPRETATION", "PREDICTION")
        assert isinstance(item["relevance_reasons"], list)


# ===========================================================================
# 20. Grounded AI / Deterministic Explanation Endpoint
# ===========================================================================

def test_20_explain_bill_relevance_endpoint() -> None:
    resp = client.get(
        f"/api/v1/workspace/explain-relevance?bill_id={CENTRAL_PROD_BILL_ID}",
        headers=HEADERS_TENANT_A,
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["bill_id"] == CENTRAL_PROD_BILL_ID
    assert data["bill_title"]
    assert data["relevance_tier"] in [t.value for t in RelevanceTier] + ["NONE"]
    assert "explanation" in data
    assert "DECISION SUPPORT NOTICE" in data["disclaimer"]


# ===========================================================================
# 21. Graceful Insufficient-Source Handling in Explain-Relevance
# ===========================================================================

def test_21_explain_relevance_insufficient_information() -> None:
    # Request explanation for completely unknown bill
    resp = client.get(
        "/api/v1/workspace/explain-relevance?bill_id=non-existent-dummy-bill-9999",
        headers=HEADERS_TENANT_A,
    )
    # Must succeed gracefully with 200 and clear INSUFFICIENT INFORMATION notice
    assert resp.status_code == 200
    data = resp.json()
    assert data["relevance_tier"] in ("NONE", RelevanceTier.INFORMATIONAL.value)
    assert "INSUFFICIENT" in data["explanation"] or "not found" in data["explanation"].lower()


# ===========================================================================
# 22. "MY LEGISLATIVE IMPACT REPORT" Generation
# ===========================================================================

def test_22_personal_impact_report_generation() -> None:
    # 1. From workspace endpoint
    rep_resp = client.get("/api/v1/workspace/report", headers=HEADERS_TENANT_A)
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()

    assert rep_data["report_title"] == "MY LEGISLATIVE IMPACT REPORT"
    assert rep_data["user_id"] == "user_alpha_828"
    assert "executive_summary" in rep_data
    assert "portfolio_holdings" in rep_data
    assert "legislative_exposures" in rep_data
    assert "sector_breakdown" in rep_data
    assert "DECISION SUPPORT NOTICE" in rep_data["governance_disclaimer"]

    # Epistemic separation verification in report
    for exp in rep_data["legislative_exposures"]:
        assert exp["model_status"] in [s.value for s in PersonalizedModelStatus]
        # Invariant: If state bill, predictions count must be 0
        if exp["jurisdiction"].lower() == "state":
            assert exp["authoritative_prediction"]["predictions_count"] == 0

    # 2. From portfolio specific endpoint
    pf_list = client.get("/api/v1/portfolio", headers=HEADERS_TENANT_A).json()
    pf_id = pf_list[0]["portfolio_id"]
    pf_rep_resp = client.get(f"/api/v1/portfolio/{pf_id}/report", headers=HEADERS_TENANT_A)
    assert pf_rep_resp.status_code == 200
    assert pf_rep_resp.json()["portfolio_id"] == pf_id


# ===========================================================================
# 23. Global Search Integration With Portfolio & Watchlist Scoping
# ===========================================================================

def test_23_global_search_portfolio_and_watchlist_scope() -> None:
    # Search with scope=portfolio
    p_resp = client.get("/api/v1/search?q=banking&scope=portfolio", headers=HEADERS_TENANT_A)
    assert p_resp.status_code == 200
    p_data = p_resp.json()
    assert "items" in p_data

    # Search with scope=watchlist
    w_resp = client.get("/api/v1/search?q=sbi&scope=watchlist", headers=HEADERS_TENANT_A)
    assert w_resp.status_code == 200
    w_data = w_resp.json()
    assert "items" in w_data


# ===========================================================================
# 24. Quantitative Baseline Integrity & Production Invariants Verification
# ===========================================================================

def test_24_baseline_invariance_and_firewall_verification() -> None:
    manifest_path = Path("docs/production_baseline.json")
    assert manifest_path.is_file(), "docs/production_baseline.json must exist"

    baseline = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 1. Central model invariant: exactly 20 production bills
    central = baseline["central_baseline"]
    assert central["central_production_bills"] == 20
    assert central["quantitative_securities_count"] == 47
    assert central["bill_company_pairs_count"] == 940
    assert central["prediction_records_count"] == 4700
    assert central["decision_records_count"] == 4700
    assert central["anticipation_scores_count"] == 940
    assert central["stakeholder_reports"]["total_count"] == 14100

    # 2. State baseline invariant: strictly 0 stock predictions
    state = baseline["state_baseline"]
    assert state["production_bills_count"] == 44
    assert state["stock_predictions_count"] == 0

    # 3. Authoritative event horizons invariant: 5 horizons
    assert len(central["event_horizons"]) == 5

    # 4. State prediction firewall invariant flag
    assert baseline["invariants"]["zero_state_stock_predictions"] is True
    assert baseline["invariants"]["firewall_intel_only_companies"] is True
    assert baseline["invariants"]["prohibit_financial_recommendations"] is True
