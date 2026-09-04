"""
tests/test_dashboard_pages.py
=============================
Unit tests for Task 7.4 Dashboard page renderers and component integration.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pandas as pd
import pytest

from dashboard.components.filter_sidebar import render_filter_sidebar
from dashboard.components.header import render_header
from dashboard.components.kpi_cards import render_kpi_cards
from dashboard.components.report_viewer import (
    render_bill_report,
    render_company_report,
    render_stakeholder_report,
)
from dashboard.pages.anticipation_view import render_anticipation_view
from dashboard.pages.backtest_view import render_backtest_view
from dashboard.pages.bill_explorer import render_bill_explorer
from dashboard.pages.business_view import render_business_view
from dashboard.pages.company_explorer import render_company_explorer
from dashboard.pages.explainability_view import render_explainability_view
from dashboard.pages.investor_view import render_investor_view
from dashboard.pages.landing import render_landing_page
from dashboard.pages.methodology_view import render_methodology_view
from dashboard.pages.public_view import render_public_view
from dashboard.pages.risk_overview import render_risk_overview
from dashboard.services.data_service import DashboardDataService
from dashboard.services.scope_service import ScopeDiagnostic
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company
from schemas.report import BillLevelReport, CompanyLevelReport, StakeholderReport, StakeholderType


@pytest.fixture
def mock_populated_service():
    service = DashboardDataService()

    b1 = Bill(
        bill_id="bill-1",
        title="Banking Laws Bill",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://example.com/b1",
        ministry="Ministry of Finance",
        sectors=["Financial Services"],
        summary="A bill amending banking governance.",
    )
    c1 = Company(
        isin="INE001",
        company_name="State Bank Corp",
        sector="Financial Services",
        ticker_nse="SBC",
        industry="Public Bank",
    )

    service.bill_repo.get_all = MagicMock(return_value=[b1])
    service.company_repo.get_all = MagicMock(return_value=[c1])

    mock_dec = MagicMock()
    mock_dec.decision_id = "dec_bill-1_INE001_-10_p10"
    mock_dec.bill_id = "bill-1"
    mock_dec.company_isin = "INE001"
    mock_dec.event_window = "[-10,+10]"
    mock_dec.predicted_direction = "POSITIVE"
    mock_dec.confidence = "HIGH"
    mock_dec.market_moving_probability = 0.72
    mock_dec.impact_score = 0.45
    mock_dec.risk_score = 0.38
    mock_dec.risk_category = "LOW"
    mock_dec.anticipation_evidence = "NO_EVIDENCE"
    mock_dec.pricing_in_risk = "LOW"
    mock_dec.impact_strength = "MEDIUM"
    service.decision_repo.load_all = MagicMock(return_value=[mock_dec])

    service.explainability_repo.load_global_summary = MagicMock(
        return_value={"top_20_features": [{"feature": "car_lag", "mean_abs_shap": 0.25}]}
    )
    service.explainability_repo.load_model_comparison = MagicMock(
        return_value={"targets": {"direction": {"lgbm": 0.45}}}
    )
    service.explainability_repo.exists = MagicMock(return_value=True)
    service.explainability_repo.load = MagicMock(
        return_value={"local_explanations": {"sample_1": {"feature": "val"}}}
    )
    service.backtest_repo.list_runs = MagicMock(return_value=["v641_direction"])
    service.backtest_repo.load = MagicMock(
        return_value={
            "strategy_metrics": {"cumulative_return": 0.18, "sharpe_ratio": 1.45, "max_drawdown": -0.08},
            "benchmark_metrics": {"cumulative_return": 0.10},
            "backtest_report": {"macro_f1": 0.44, "balanced_accuracy": 0.45, "mcc": 0.15, "roc_auc": 0.62},
            "portfolio_timeseries": pd.DataFrame([
                {"date": "2024-01-01", "cumulative_strategy_return": 0.05, "cumulative_benchmark_return": 0.02, "drawdown": -0.01}
            ]),
        }
    )

    # Mock reports
    stk_rpt = StakeholderReport(
        report_id="rpt_bill-1_INE001_-10_p10_investor",
        bill_id="bill-1",
        company_isin="INE001",
        event_window="[-10,+10]",
        stakeholder_type="INVESTOR",
        decision_version="v1.0",
        generated_timestamp="2026-08-16T00:00:00Z",
        report_version="v1.0",
        executive_summary="Executive investor summary.",
        bill_summary="Banking bill summary.",
        company_summary="State Bank Corp summary.",
        impact_summary="Moderate positive impact.",
        risk_summary="Low risk assessment.",
        anticipation_summary="No pre-event drift.",
        confidence_summary="High confidence tier.",
        key_factors=["Factor 1: Capital adequacy", "Factor 2: Beta"],
        methodology_note="Academic event study model.",
        disclaimer="Institutional non-advisory disclaimer.",
    )
    service.report_repo.get = MagicMock(return_value=stk_rpt)

    bill_rpt = BillLevelReport(
        report_id="bill_rpt_bill-1",
        bill_id="bill-1",
        bill_title="Banking Laws Bill",
        bill_ministry="Ministry of Finance",
        bill_year=2024,
        event_window="[-10,+10]",
        generated_timestamp="2026-08-16T00:00:00Z",
        report_version="v1.0",
        total_companies=10,
        positive_count=2,
        negative_count=1,
        neutral_count=7,
        market_moving_count=1,
        high_impact_count=2,
        avg_impact_score=0.42,
        avg_risk_score=0.38,
        anticipation_distribution={"NO_EVIDENCE": 10},
        risk_distribution={"LOW": 10},
        sectors_affected=["Financial Services"],
        company_summaries=[{"company_name": "State Bank Corp", "isin": "INE001", "impact_score": 0.45}],
    )
    service.report_repo.load_bill_report = MagicMock(return_value=bill_rpt)

    comp_rpt = CompanyLevelReport(
        report_id="co_rpt_INE001",
        company_isin="INE001",
        company_name="State Bank Corp",
        company_sector="Financial Services",
        generated_timestamp="2026-08-16T00:00:00Z",
        report_version="v1.0",
        total_bills=1,
        positive_bill_count=1,
        negative_bill_count=0,
        neutral_bill_count=0,
        avg_impact_score=0.45,
        avg_risk_score=0.38,
        bill_summaries=[{"bill_id": "bill-1", "impact_score": 0.45}],
    )
    service.report_repo.load_company_report = MagicMock(return_value=comp_rpt)

    return service


@pytest.fixture
def sample_test_df():
    return pd.DataFrame([
        {
            "decision_id": "dec_bill-1_INE001_-10_p10",
            "bill_id": "bill-1",
            "bill_title": "Banking Laws Bill",
            "company_isin": "INE001",
            "company_name": "State Bank Corp",
            "ticker": "SBC",
            "sector": "Financial Services",
            "industry": "Public Bank",
            "ministry": "Ministry of Finance",
            "policy_domain": "Financial Services",
            "event_window": "[-10,+10]",
            "predicted_direction": "POSITIVE",
            "confidence": "HIGH",
            "market_moving_probability": 0.72,
            "impact_score": 0.45,
            "risk_score": 0.38,
            "risk_category": "LOW",
            "anticipation_evidence": "NO_EVIDENCE",
            "pricing_in_risk": "LOW",
            "impact_strength": "MEDIUM",
        }
    ])


def test_render_landing_page(mock_populated_service, sample_test_df):
    """Verify landing page renders successfully."""
    render_landing_page(mock_populated_service, sample_test_df)


def test_render_bill_explorer(mock_populated_service, sample_test_df):
    """Verify bill explorer renders successfully."""
    render_bill_explorer(mock_populated_service, sample_test_df)
    # Empty case
    empty_serv = DashboardDataService()
    empty_serv.bill_repo.get_all = MagicMock(return_value=[])
    render_bill_explorer(empty_serv, pd.DataFrame())


def test_render_company_explorer(mock_populated_service, sample_test_df):
    """Verify company explorer renders successfully."""
    render_company_explorer(mock_populated_service, sample_test_df)
    # Empty case
    empty_serv = DashboardDataService()
    empty_serv.company_repo.get_all = MagicMock(return_value=[])
    render_company_explorer(empty_serv, pd.DataFrame())


def test_render_investor_view(mock_populated_service, sample_test_df):
    """Verify investor view renders with compliant narratives."""
    render_investor_view(mock_populated_service, sample_test_df)
    render_investor_view(mock_populated_service, pd.DataFrame())


def test_render_business_view(mock_populated_service, sample_test_df):
    """Verify business view renders."""
    render_business_view(mock_populated_service, sample_test_df)
    render_business_view(mock_populated_service, pd.DataFrame())


def test_render_public_view(mock_populated_service, sample_test_df):
    """Verify public view renders."""
    render_public_view(mock_populated_service, sample_test_df)
    render_public_view(mock_populated_service, pd.DataFrame())


def test_render_risk_overview(mock_populated_service, sample_test_df):
    """Verify risk overview renders."""
    render_risk_overview(mock_populated_service, sample_test_df)
    render_risk_overview(mock_populated_service, pd.DataFrame())


def test_render_anticipation_view(mock_populated_service, sample_test_df):
    """Verify anticipation overview renders."""
    render_anticipation_view(mock_populated_service, sample_test_df)
    render_anticipation_view(mock_populated_service, pd.DataFrame())


def test_render_explainability_view(mock_populated_service, sample_test_df):
    """Verify explainability view renders."""
    render_explainability_view(mock_populated_service, sample_test_df)


def test_render_backtest_view(mock_populated_service, sample_test_df):
    """Verify backtest view renders."""
    render_backtest_view(mock_populated_service, sample_test_df)
    # Empty runs case
    empty_serv = DashboardDataService()
    empty_serv.backtest_repo.list_runs = MagicMock(return_value=[])
    render_backtest_view(empty_serv, pd.DataFrame())


def test_render_methodology_view():
    """Verify methodology view renders."""
    render_methodology_view()


def test_render_header_with_diagnostic():
    """Verify header renders with scope diagnostic."""
    diag = ScopeDiagnostic()
    render_header(diag)
    render_header(None)


def test_render_kpi_cards(sample_test_df):
    """Verify KPI cards render with populated and empty data."""
    render_kpi_cards(sample_test_df)
    render_kpi_cards(pd.DataFrame())


def test_render_filter_sidebar(sample_test_df):
    """Verify filter sidebar renders and returns criteria dictionary."""
    criteria = render_filter_sidebar(sample_test_df)
    assert isinstance(criteria, dict)
    assert "bill_id" in criteria
    assert "company_isin" in criteria


def test_render_reports_populated(mock_populated_service):
    """Verify report viewers render populated objects."""
    stk = mock_populated_service.get_stakeholder_report("bill-1", "INE001", "[-10,+10]", "INVESTOR")
    render_stakeholder_report(stk)

    bill_rpt = mock_populated_service.get_bill_report("bill-1")
    render_bill_report(bill_rpt)

    comp_rpt = mock_populated_service.get_company_report("INE001")
    render_company_report(comp_rpt)


def test_app_main_orchestration(sample_test_df):
    """Verify app.main() executes and routes across pages cleanly."""
    from unittest.mock import patch
    import dashboard.app as app_mod

    # Test routes across the 11 pages
    pages_to_test = [
        "🌐 Global Overview",
        "📜 Bill Explorer",
        "🏢 Company Explorer",
        "📈 Investor View",
        "💼 Business View",
        "🌍 Public View",
        "⚡ Risk Overview",
        "🛡️ Anticipation Overview",
        "🧠 Model Explainability",
        "📊 Backtesting Summary",
        "📐 Methodology",
    ]

    for p in pages_to_test:
        with patch.object(app_mod, "get_data_service") as mock_get_ds, \
             patch.object(app_mod.st, "set_page_config"), \
             patch.object(app_mod.st.sidebar, "radio", return_value=p), \
             patch.object(app_mod, "render_filter_sidebar", return_value={
                 "bill_id": None, "company_isin": None, "sector": None, "ministry": None,
                 "risk_category": None, "direction": None, "market_moving_only": None,
                 "anticipation_category": None, "event_window": None
             }):

            mock_ds = MagicMock()
            mock_ds.get_decision_dataframe.return_value = sample_test_df
            mock_ds.get_bills.return_value = []
            mock_ds.get_companies.return_value = []
            mock_ds.get_backtest_runs.return_value = []
            mock_ds.get_global_explainability.return_value = {}
            mock_ds.get_model_comparison_explainability.return_value = {}
            mock_get_ds.return_value = mock_ds

            app_mod.main()


def test_app_main_with_active_filter(sample_test_df):
    """Verify app.main() when an active filter is present."""
    from unittest.mock import patch
    import dashboard.app as app_mod

    with patch.object(app_mod, "get_data_service") as mock_get_ds, \
         patch.object(app_mod.st, "set_page_config"), \
         patch.object(app_mod.st.sidebar, "radio", return_value="🌐 Global Overview"), \
         patch.object(app_mod.st.sidebar, "button", return_value=False), \
         patch.object(app_mod, "render_filter_sidebar", return_value={
             "bill_id": "bill-1", "company_isin": None, "sector": None, "ministry": None,
             "risk_category": None, "direction": None, "market_moving_only": None,
             "anticipation_category": None, "event_window": None
         }):

        mock_ds = MagicMock()
        mock_ds.get_decision_dataframe.return_value = sample_test_df
        mock_ds.get_bills.return_value = []
        mock_ds.get_companies.return_value = []
        mock_get_ds.return_value = mock_ds

        app_mod.main()
