"""
tests/test_dashboard_services.py
================================
Unit tests for Task 7.4 DashboardDataService.
"""

from __future__ import annotations

from unittest.mock import MagicMock
import pandas as pd
import pytest

from dashboard.services.data_service import DashboardDataService
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company
from schemas.decision import DecisionSupportRecord, RiskCategory, PricingInRisk
from schemas.report import BillLevelReport, CompanyLevelReport, StakeholderReport, StakeholderType


@pytest.fixture
def sample_bill():
    return Bill(
        bill_id="the-banking-laws-amendment-bill-2024",
        title="The Banking Laws (Amendment) Bill, 2024",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://example.com/bill",
        ministry="Ministry of Finance",
        sectors=["Financial Sector"],
    )


@pytest.fixture
def sample_company():
    return Company(
        isin="INE002A01018",
        company_name="State Bank of India",
        ticker_nse="SBIN",
        sector="Financial Services",
        industry="Public Sector Bank",
    )


@pytest.fixture
def sample_decision():
    return DecisionSupportRecord(
        decision_id="dec_the-banking-laws-amendment-bill-2024_INE002A01018_-10_p10",
        bill_id="the-banking-laws-amendment-bill-2024",
        company_isin="INE002A01018",
        event_window="[-10,+10]",
        predicted_direction="POSITIVE",
        direction_probability={"POSITIVE": 0.8, "NEGATIVE": 0.1, "NEUTRAL": 0.1},
        market_moving_probability=0.72,
        predicted_impact_strength="MEDIUM",
        confidence_probability={"LOW": 0.1, "MEDIUM": 0.2, "HIGH": 0.7},
        anticipation_class="WEAK_EVIDENCE",
        anticipation_score=0.25,
        impact_score=0.45,
        risk_score=0.38,
        risk_category="LOW",
        pricing_in_risk="LOW",
        investor_summary="Positive reaction expected.",
        business_summary="Financial compliance impacts.",
        public_summary="Banking regulatory reforms.",
        decision_reason="Solid capital position.",
        model_version="v1.0",
        feature_version="v1.0",
        predicted_confidence="HIGH",
    )


def test_data_service_bills_loading(sample_bill):
    """Verify bills loading and test stub filtering."""
    mock_bill_repo = MagicMock()
    test_stub = Bill(
        bill_id="service-bill",
        title="Stub Bill",
        house=BillHouse.UNKNOWN,
        status=BillStatus.DRAFT,
        url="https://example.com/stub",
    )
    mock_bill_repo.get_all.return_value = [sample_bill, test_stub]

    service = DashboardDataService(bill_repo=mock_bill_repo)
    bills = service.get_bills()
    assert len(bills) == 2

    prod_bills = service.get_production_bills()
    assert len(prod_bills) == 1
    assert prod_bills[0].bill_id == "the-banking-laws-amendment-bill-2024"

    found = service.get_bill_by_id("the-banking-laws-amendment-bill-2024")
    assert found is not None
    assert found.title == sample_bill.title

    not_found = service.get_bill_by_id("non-existent-bill")
    assert not_found is None


def test_data_service_companies_loading(sample_company):
    """Verify company master loading and lookup."""
    mock_comp_repo = MagicMock()
    mock_comp_repo.get_all.return_value = [sample_company]

    service = DashboardDataService(company_repo=mock_comp_repo)
    companies = service.get_companies()
    assert len(companies) == 1

    comp = service.get_company_by_isin("INE002A01018")
    assert comp is not None
    assert comp.company_name == "State Bank of India"

    missing = service.get_company_by_isin("INE999999999")
    assert missing is None


def test_data_service_decision_dataframe_enrichment(sample_bill, sample_company, sample_decision):
    """Verify decision records are loaded and enriched into a DataFrame."""
    mock_bill_repo = MagicMock()
    mock_bill_repo.get_all.return_value = [sample_bill]
    mock_comp_repo = MagicMock()
    mock_comp_repo.get_all.return_value = [sample_company]
    mock_dec_repo = MagicMock()
    mock_dec_repo.load_all.return_value = [sample_decision]

    service = DashboardDataService(
        bill_repo=mock_bill_repo,
        company_repo=mock_comp_repo,
        decision_repo=mock_dec_repo,
    )

    df = service.get_decision_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    row = df.iloc[0]

    assert row["decision_id"] == sample_decision.decision_id
    assert row["company_name"] == "State Bank of India"
    assert row["sector"] == "Financial Services"
    assert row["bill_title"] == "The Banking Laws (Amendment) Bill, 2024"
    assert row["predicted_direction"] == "POSITIVE"
    assert row["risk_category"] == "LOW"
    assert row["impact_score"] == pytest.approx(0.45)
    assert row["risk_score"] == pytest.approx(0.38)


def test_data_service_empty_decisions():
    """Verify handling when decision repository is empty."""
    mock_dec_repo = MagicMock()
    mock_dec_repo.load_all.return_value = []

    service = DashboardDataService(decision_repo=mock_dec_repo)
    df = service.get_decision_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert "decision_id" in df.columns
    assert "impact_score" in df.columns


def test_data_service_reports_loading():
    """Verify loading of bill, company, and stakeholder reports."""
    mock_report_repo = MagicMock()
    mock_bill_rpt = MagicMock(spec=BillLevelReport)
    mock_comp_rpt = MagicMock(spec=CompanyLevelReport)
    mock_stk_rpt = MagicMock(spec=StakeholderReport)

    mock_report_repo.load_bill_report.return_value = mock_bill_rpt
    mock_report_repo.load_company_report.return_value = mock_comp_rpt
    mock_report_repo.get.return_value = mock_stk_rpt

    service = DashboardDataService(report_repo=mock_report_repo)

    assert service.get_bill_report("bill-1") is mock_bill_rpt
    assert service.get_company_report("INE001") is mock_comp_rpt
    assert service.get_stakeholder_report("b", "c", "w", "INVESTOR") is mock_stk_rpt

    # Fallback when invalid stakeholder type
    assert service.get_stakeholder_report("b", "c", "w", "INVALID_TYPE") is None


def test_data_service_explainability_and_backtests():
    """Verify explainability and backtest loaders with missing artifact tolerance."""
    mock_exp_repo = MagicMock()
    mock_exp_repo.load_global_summary.return_value = {"top_20_features": [{"feature": "f1", "mean_abs_shap": 0.1}]}
    mock_exp_repo.load_model_comparison.return_value = {"targets": {}}

    mock_bt_repo = MagicMock()
    mock_bt_repo.list_runs.return_value = ["v641_direction"]
    mock_bt_repo.load.return_value = {"strategy_metrics": {"sharpe_ratio": 1.25}}

    service = DashboardDataService(explainability_repo=mock_exp_repo, backtest_repo=mock_bt_repo)

    expl = service.get_global_explainability()
    assert "top_20_features" in expl

    runs = service.get_backtest_runs()
    assert runs == ["v641_direction"]

    bt = service.get_backtest_data("v641_direction")
    assert bt["strategy_metrics"]["sharpe_ratio"] == 1.25

    # Test error handling when repos raise exceptions
    mock_exp_repo.load_global_summary.side_effect = FileNotFoundError("Missing")
    assert service.get_global_explainability() == {}

    mock_bt_repo.load.side_effect = RuntimeError("Failed")
    assert service.get_backtest_data("v641_direction") == {}


def test_data_service_clear_cache():
    """Verify cache clearing resets in-memory attributes."""
    service = DashboardDataService()
    service._cached_dataframe = pd.DataFrame([{"a": 1}])
    service._cached_decisions = [MagicMock()]
    service._cached_bills = [MagicMock()]
    service._cached_companies = [MagicMock()]

    service.clear_cache()
    assert service._cached_dataframe is None
    assert service._cached_decisions is None
    assert service._cached_bills is None
    assert service._cached_companies is None


def test_data_service_cached_decisions_hit():
    """Verify that cached decisions list is returned on second call."""
    mock_repo = MagicMock()
    mock_repo.load_all.return_value = ["dec1"]
    service = DashboardDataService(decision_repo=mock_repo)

    r1 = service.get_decision_records()
    assert r1 == ["dec1"]
    assert mock_repo.load_all.call_count == 1

    # Second call hits in-memory cache
    r2 = service.get_decision_records()
    assert r2 == ["dec1"]
    assert mock_repo.load_all.call_count == 1


def test_data_service_enum_attribute_decisions(sample_bill, sample_company):
    """Verify enum attributes with .value are converted cleanly in dataframe."""
    from enum import Enum

    class MockEnum(Enum):
        VAL = "MOCK_VAL"

    mock_rec = MagicMock()
    mock_rec.decision_id = "dec_enum"
    mock_rec.bill_id = sample_bill.bill_id
    mock_rec.company_isin = sample_company.isin
    mock_rec.event_window = "[-10,+10]"
    mock_rec.predicted_direction = MockEnum.VAL
    mock_rec.predicted_confidence = MockEnum.VAL
    mock_rec.risk_score = 0.5
    mock_rec.risk_category = MockEnum.VAL
    mock_rec.anticipation_class = MockEnum.VAL
    mock_rec.pricing_in_risk = MockEnum.VAL
    mock_rec.predicted_impact_strength = MockEnum.VAL
    mock_rec.market_moving_probability = 0.8
    mock_rec.impact_score = 0.6

    mock_bill_repo = MagicMock()
    mock_bill_repo.get_all.return_value = [sample_bill]
    mock_comp_repo = MagicMock()
    mock_comp_repo.get_all.return_value = [sample_company]
    mock_dec_repo = MagicMock()
    mock_dec_repo.load_all.return_value = [mock_rec]

    service = DashboardDataService(
        bill_repo=mock_bill_repo,
        company_repo=mock_comp_repo,
        decision_repo=mock_dec_repo,
    )
    df = service.get_decision_dataframe()
    assert len(df) == 1
    assert df.iloc[0]["predicted_direction"] == "MOCK_VAL"
    assert df.iloc[0]["risk_category"] == "MOCK_VAL"


def test_data_service_backtest_list_runs_error():
    """Verify error in list_runs returns empty list gracefully."""
    mock_bt = MagicMock()
    mock_bt.list_runs.side_effect = OSError("Disk read error")
    service = DashboardDataService(backtest_repo=mock_bt)
    assert service.get_backtest_runs() == []


def test_run_dashboard_launcher():
    """Verify run_dashboard invokes streamlit subprocess correctly."""
    from unittest.mock import patch
    from dashboard.dashboard import run_dashboard

    with patch("subprocess.run") as mock_sub:
        mock_sub.return_value.returncode = 0
        ret = run_dashboard(port=8502, host="127.0.0.1")
        assert ret == 0
        mock_sub.assert_called_once()
        cmd = mock_sub.call_args[0][0]
        assert "--server.port" in cmd
        assert "8502" in cmd
        assert "--server.address" in cmd
        assert "127.0.0.1" in cmd

    # Test keyboard interrupt handling
    with patch("subprocess.run", side_effect=KeyboardInterrupt):
        assert run_dashboard() == 0

    # Test exception handling
    with patch("subprocess.run", side_effect=RuntimeError("Subprocess failed")):
        assert run_dashboard() == 1


def test_cached_data_and_clear():
    """Verify cached_data decorator and clear_dashboard_cache."""
    from dashboard.utils.cache import cached_data, clear_dashboard_cache

    @cached_data
    def compute(x: int) -> int:
        return x * 2

    assert compute(5) == 10
    clear_dashboard_cache()
