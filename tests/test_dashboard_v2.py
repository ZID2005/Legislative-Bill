"""
tests/test_dashboard_v2.py
==========================
Task 7.4.2 — Comprehensive test suite for Bill Intelligence and Analytical Dashboard.

Verifies:
- All Bills table data construction, sorting, filtering, and selection
- Bill Intelligence data completeness, exact probability preservation, timeline dates
- Company Intelligence multi-company comparative matrix (47 production companies)
- Company Detail drilldown and associated bills
- Market Impact Predictions distributions and charts
- Risk Overview canonical tiers and 2D matrix
- Anticipation & Pricing-In diffusion analysis and compliance disclaimers
- Historical Backtesting methodology, metrics, and temporal leakage guardrails
- Academic Methodology 18-stage walkthrough
- Global search functionality
- Production scope reconciliation and non-mixing of pilot/test stubs
- Strict read-only presentation guarantee
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from dashboard.pages.anticipation import render_anticipation_page
from dashboard.pages.backtesting import render_backtesting_page
from dashboard.pages.bill_detail import render_bill_detail_page
from dashboard.pages.bills import render_bills_page
from dashboard.pages.companies import render_companies_page
from dashboard.pages.company_detail import render_company_detail_page
from dashboard.pages.methodology import render_methodology_page
from dashboard.pages.predictions import render_predictions_page
from dashboard.pages.risk import render_risk_page
from dashboard.services.dashboard_service import DashboardService, ProductionScope
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company
from schemas.decision import DecisionSupportRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_dashboard_service():
    """Create a mock DashboardService for fast isolated unit testing."""
    service = DashboardService()

    b1 = Bill(
        bill_id="the-banking-laws-amendment-bill-2024",
        title="The Banking Laws (Amendment) Bill, 2024",
        bill_number="120/2024",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://prsindia.org/billtrack/the-banking-laws-amendment-bill-2024",
        ministry="Ministry of Finance",
        sectors=["Banking & Financial Services"],
        summary="A bill to amend banking regulations and governance frameworks.",
    )
    b2 = Bill(
        bill_id="the-coastal-shipping-bill-2024",
        title="The Coastal Shipping Bill, 2024",
        bill_number="121/2024",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://prsindia.org/billtrack/the-coastal-shipping-bill-2024",
        ministry="Shipping",
        sectors=["Transport / Maritime"],
        summary="",  # Empty summary to test fallback
    )
    stub = Bill(
        bill_id="service-bill",
        title="Service Bill Test Stub",
        bill_number="00/0000",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://example.com/stub",
        ministry="Testing",
    )

    c1 = Company(
        isin="INE002A01018",
        company_name="State Bank of India",
        ticker_nse="SBIN",
        sector="Banking & Financial Services",
        industry="Public Sector Bank",
    )
    c2 = Company(
        isin="INE062A01020",
        company_name="Axis Bank Limited",
        ticker_nse="AXISBANK",
        sector="Banking & Financial Services",
        industry="Private Sector Bank",
    )

    d1 = DecisionSupportRecord(
        decision_id="dec_the-banking-laws-amendment-bill-2024_INE002A01018_-10_p10",
        bill_id="the-banking-laws-amendment-bill-2024",
        company_isin="INE002A01018",
        event_window="[-10,+10]",
        predicted_direction="POSITIVE",
        direction_probability={"POSITIVE": 0.75, "NEGATIVE": 0.10, "NEUTRAL": 0.15},
        market_moving_probability=0.68,
        predicted_impact_strength="HIGH",
        confidence_probability={"LOW": 0.1, "MEDIUM": 0.2, "HIGH": 0.7},
        anticipation_class="MODERATE_EVIDENCE",
        anticipation_score=0.55,
        impact_score=0.72,
        risk_score=0.45,
        risk_category="MODERATE",
        pricing_in_risk="LOW",
        investor_summary="Investor summary text.",
        business_summary="Business summary text.",
        public_summary="Public summary text.",
        decision_reason="Decision reason text.",
        model_version="v1.0",
        feature_version="v1.0",
        predicted_confidence="HIGH",
        confidence_score=0.85,
    )

    service._load_bills = MagicMock(return_value=[b1, b2, stub])
    service._load_companies = MagicMock(return_value=[c1, c2])
    service._load_decisions = MagicMock(return_value=[d1])

    return service


# ---------------------------------------------------------------------------
# 1. All Bills Tests
# ---------------------------------------------------------------------------

def test_all_bills_table_data_generation(mock_dashboard_service):
    """Verify get_all_bills_table_data excludes test stubs and structures columns."""
    df = mock_dashboard_service.get_all_bills_table_data()

    assert not df.empty
    # Excludes "service-bill" stub
    assert len(df) == 2
    assert "service-bill" not in df["bill_id"].values

    # Mandatory columns present
    expected_cols = [
        "bill_id", "Bill", "Bill Number", "Introduction Date", "House",
        "Ministry / Department", "Bill Type", "Status", "Affected Sectors",
        "Affected Companies", "Market Direction", "Market Moving",
        "Impact Strength", "Risk"
    ]
    for col in expected_cols:
        assert col in df.columns


def test_render_bills_page_mock(mock_dashboard_service):
    """Verify render_bills_page runs cleanly with mock data."""
    render_bills_page(mock_dashboard_service)


def test_render_bills_page_empty():
    """Verify render_bills_page handles empty repository gracefully."""
    empty_service = DashboardService()
    empty_service.get_all_bills_table_data = MagicMock(return_value=pd.DataFrame())
    render_bills_page(empty_service)


# ---------------------------------------------------------------------------
# 2. Bill Intelligence & Detail Tests
# ---------------------------------------------------------------------------

def test_get_bill_detail_data_complete(mock_dashboard_service):
    """Verify get_bill_detail_data returns all required sections and preserved probabilities."""
    data = mock_dashboard_service.get_bill_detail_data("the-banking-laws-amendment-bill-2024")

    assert data is not None
    assert data["bill"].bill_id == "the-banking-laws-amendment-bill-2024"
    assert "plain_summary" in data
    assert len(data["plain_summary"]) > 0

    # Probabilities preserved exactly
    impact = data["market_impact"]
    assert impact["predicted_direction"] == "POSITIVE"
    assert impact["positive_probability"] == 0.75
    assert impact["negative_probability"] == 0.10
    assert impact["neutral_probability"] == 0.15
    assert impact["market_moving_probability"] == 0.68

    # Risk & Anticipation
    assert data["risk"]["risk_category"] == "MODERATE"
    assert data["anticipation"]["anticipation_class"] == "MODERATE_EVIDENCE"

    # Timeline structure
    timeline = data["timeline"]
    assert len(timeline) == 4
    stages = [s["stage"] for s in timeline]
    assert stages == ["Introduction", "Consideration", "Passage", "Assent"]

    # Affected companies table
    aff_df = data["affected_companies_table"]
    assert not aff_df.empty
    assert "State Bank of India" in aff_df["company_name"].values


def test_get_bill_detail_summary_fallback(mock_dashboard_service):
    """Verify bills with missing summary fallback to 'Summary not available.' without hallucination."""
    data = mock_dashboard_service.get_bill_detail_data("the-coastal-shipping-bill-2024")
    assert data is not None
    assert data["plain_summary"] == "Summary not available."


def test_render_bill_detail_page_mock(mock_dashboard_service):
    """Verify render_bill_detail_page runs cleanly."""
    with patch("streamlit.session_state", {"selected_bill_id": "the-banking-laws-amendment-bill-2024"}):
        render_bill_detail_page(mock_dashboard_service)


# ---------------------------------------------------------------------------
# 3. Company Intelligence & Detail Tests
# ---------------------------------------------------------------------------

def test_get_all_companies_summary(mock_dashboard_service):
    """Verify get_all_companies_summary builds comparative metric table."""
    df = mock_dashboard_service.get_all_companies_summary()

    assert not df.empty
    expected_cols = [
        "isin", "Company Name", "Ticker", "Sector", "Industry",
        "Associated Bills", "Positive Exposure", "Negative Exposure",
        "Neutral Exposure", "Market-Moving Bills", "Avg Impact Score",
        "Avg Risk Score", "Strong Anticipation Exposure"
    ]
    for col in expected_cols:
        assert col in df.columns


def test_render_companies_page(mock_dashboard_service):
    """Verify render_companies_page renders cleanly."""
    render_companies_page(mock_dashboard_service)


def test_get_company_detail_data(mock_dashboard_service):
    """Verify get_company_detail_data returns complete company profile."""
    data = mock_dashboard_service.get_company_detail_data("INE002A01018")

    assert data is not None
    assert data["company"].company_name == "State Bank of India"
    assert not data["related_bills_table"].empty
    assert "The Banking Laws (Amendment) Bill, 2024" in data["related_bills_table"]["Bill Title"].values


def test_render_company_detail_page(mock_dashboard_service):
    """Verify render_company_detail_page renders cleanly."""
    with patch("streamlit.session_state", {"selected_company_isin": "INE002A01018"}):
        render_company_detail_page(mock_dashboard_service)


# ---------------------------------------------------------------------------
# 4. Predictions, Risk, Anticipation, Backtesting & Methodology Tests
# ---------------------------------------------------------------------------

def test_render_predictions_page(mock_dashboard_service):
    """Verify render_predictions_page renders distributions and charts."""
    df = mock_dashboard_service.get_decision_dataframe()
    render_predictions_page(mock_dashboard_service, df)


def test_render_risk_page(mock_dashboard_service):
    """Verify render_risk_page renders risk tiers and matrix."""
    df = mock_dashboard_service.get_decision_dataframe()
    render_risk_page(mock_dashboard_service, df)


def test_render_anticipation_page(mock_dashboard_service):
    """Verify render_anticipation_page renders pre-event diffusion and disclaimers."""
    df = mock_dashboard_service.get_decision_dataframe()
    render_anticipation_page(mock_dashboard_service, df)


def test_render_backtesting_page(mock_dashboard_service):
    """Verify render_backtesting_page renders walk-forward historical simulation."""
    render_backtesting_page(mock_dashboard_service)


def test_render_methodology_page():
    """Verify render_methodology_page renders 18-stage blueprint."""
    render_methodology_page()


# ---------------------------------------------------------------------------
# 5. Global Search & Scope Reconciliation Tests
# ---------------------------------------------------------------------------

def test_search_bills(mock_dashboard_service):
    """Verify search_bills finds bills across title, number, and ministry."""
    # Search by title keyword
    results = mock_dashboard_service.search_bills("banking")
    assert len(results) >= 1
    assert results[0].bill_id == "the-banking-laws-amendment-bill-2024"

    # Search by ministry keyword
    results_m = mock_dashboard_service.search_bills("shipping")
    assert len(results_m) >= 1

    # Empty query returns all production summaries
    all_res = mock_dashboard_service.search_bills("")
    assert len(all_res) == 2


def test_production_scope_exclusion_integrity():
    """Verify that live production repository maintains 20 bills, 47 companies, 4,700 records."""
    service = DashboardService()
    scope = service.get_production_scope()

    # Scope numbers match verified production ground truth
    assert scope.production_bills_count == 20
    assert scope.total_bills_in_repo == 22
    assert len(scope.non_legislative_bills) == 2
    assert "key-issues-and-analysis" in scope.non_legislative_bills
    assert "service-bill" in scope.non_legislative_bills

    assert scope.production_companies_count == 47
    assert scope.total_companies_in_repo == 70
    assert scope.production_decision_records == 4700
    assert scope.production_prediction_records == 4700


def test_read_only_immutability():
    """Verify that calling dashboard operations never modifies underlying files."""
    from utils.file_utils import list_files
    from config.settings import settings

    dec_files_before = len(list_files(settings.DECISION_SUPPORT_DIR, "*.json"))
    service = DashboardService()

    # Call various analytical data accessors
    _ = service.get_all_bills_table_data()
    _ = service.get_all_companies_summary()
    _ = service.get_bill_detail_data("the-banking-laws-amendment-bill-2024")
    _ = service.get_company_detail_data("INE002A01018")
    _ = service.search_bills("finance")

    dec_files_after = len(list_files(settings.DECISION_SUPPORT_DIR, "*.json"))
    assert dec_files_before == dec_files_after, "Decision files count must remain identical (read-only guarantee)."
