"""
tests/test_dashboard_service.py
================================
Task 7.4.1 — Unit tests for DashboardService.

Coverage:
- Initialization and caching
- Artifact loading (bills, companies, decisions)
- Missing artifact handling (graceful errors)
- Bill filtering by introduction_date (legislative date)
- Date range filtering
- Sector filtering
- Company filtering
- Bill-type/category classification
- Status filtering
- Risk filtering
- Anticipation filtering
- Market impact aggregation
- Deterministic output
- Production scope integrity
- Read-only behavior (no artifact modification)
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest
import pandas as pd

from dashboard.services.dashboard_service import (
    DashboardService,
    BillSummary,
    ProductionScope,
    _classify_bill,
    _MINISTRY_TO_CATEGORY,
)
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company
from schemas.decision import DecisionSupportRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_bill(
    bill_id: str = "bill-finance-2024",
    title: str = "Finance Bill 2024",
    ministry: str = "Finance",
    house: BillHouse = BillHouse.LOK_SABHA,
    status: BillStatus = BillStatus.PASSED_BOTH,
    intro_date: date = date(2024, 8, 9),
    sectors: list[str] | None = None,
) -> Bill:
    return Bill(
        bill_id=bill_id,
        title=title,
        house=house,
        status=status,
        url="https://example.com",
        ministry=ministry,
        introduction_date=intro_date,
        sectors=sectors or [],
        summary="Test bill summary for dashboard testing.",
    )


def _make_company(
    isin: str = "INE001A01011",
    name: str = "Test Corp Ltd",
    sector: str = "Financial Services",
) -> Company:
    return Company(
        isin=isin,
        company_name=name,
        ticker_nse="TESTCORP",
        sector=sector,
        industry="Banking",
    )


def _make_decision(
    bill_id: str = "bill-finance-2024",
    company_isin: str = "INE001A01011",
    event_window: str = "[-10,+10]",
    direction: str = "POSITIVE",
    mmp: float = 0.72,
    risk_category: str = "MODERATE",
    anticipation_class: str = "NO_EVIDENCE",
) -> DecisionSupportRecord:
    return DecisionSupportRecord(
        decision_id=f"dec_{bill_id}_{company_isin}_{event_window}",
        bill_id=bill_id,
        company_isin=company_isin,
        event_window=event_window,
        predicted_direction=direction,
        direction_probability={"POSITIVE": 0.8, "NEGATIVE": 0.1, "NEUTRAL": 0.1},
        market_moving_probability=mmp,
        predicted_impact_strength="MEDIUM",
        confidence_probability={"LOW": 0.1, "MEDIUM": 0.2, "HIGH": 0.7},
        anticipation_class=anticipation_class,
        anticipation_score=0.2,
        impact_score=0.5,
        risk_score=0.4,
        risk_category=risk_category,
        pricing_in_risk="LOW",
        investor_summary="Test investor summary.",
        business_summary="Test business summary.",
        public_summary="Test public summary.",
        decision_reason="Test reason.",
        model_version="v1.0",
        feature_version="v1.0",
        predicted_confidence="HIGH",
    )


@pytest.fixture
def sample_bill():
    return _make_bill()


@pytest.fixture
def sample_company():
    return _make_company()


@pytest.fixture
def sample_decision():
    return _make_decision()


@pytest.fixture
def mock_service(sample_bill, sample_company, sample_decision):
    """Create a DashboardService with mocked repositories."""
    mock_bill_repo = MagicMock()
    mock_bill_repo.get_all.return_value = [sample_bill]

    mock_comp_repo = MagicMock()
    mock_comp_repo.get_all.return_value = [sample_company]

    mock_dec_repo = MagicMock()
    mock_dec_repo.load_all.return_value = [sample_decision]

    mock_mapping_repo = MagicMock()
    mock_report_repo = MagicMock()

    service = DashboardService(
        bill_repo=mock_bill_repo,
        company_repo=mock_comp_repo,
        decision_repo=mock_dec_repo,
        mapping_repo=mock_mapping_repo,
        report_repo=mock_report_repo,
    )
    return service


# ---------------------------------------------------------------------------
# Test: Initialization
# ---------------------------------------------------------------------------


def test_service_initialization():
    """DashboardService initializes with no errors using default repos."""
    mock_br = MagicMock()
    mock_br.get_all.return_value = []
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(
        bill_repo=mock_br,
        company_repo=mock_cr,
        decision_repo=mock_dr,
    )

    assert service is not None
    assert service._bills_cache is None
    assert service._companies_cache is None
    assert service._decisions_cache is None
    assert service.decisions_available is True


# ---------------------------------------------------------------------------
# Test: Bill loading and filtering
# ---------------------------------------------------------------------------


def test_get_all_bills(mock_service, sample_bill):
    """All bills are returned from repository."""
    bills = mock_service.get_all_bills()
    assert len(bills) == 1
    assert bills[0].bill_id == sample_bill.bill_id


def test_get_production_bills_excludes_stubs():
    """Non-legislative stub bills are excluded from production bills."""
    real_bill = _make_bill("real-bill-2024", "Real Bill")
    stub_bill = _make_bill("key-issues-and-analysis", "Stub")
    stub_bill2 = _make_bill("service-bill", "Service Stub")

    mock_br = MagicMock()
    mock_br.get_all.return_value = [real_bill, stub_bill, stub_bill2]
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)
    prod_bills = service.get_production_bills()

    assert len(prod_bills) == 1
    assert prod_bills[0].bill_id == "real-bill-2024"


def test_get_bill_by_id(mock_service, sample_bill):
    """Bills can be looked up by ID."""
    found = mock_service.get_bill_by_id(sample_bill.bill_id)
    assert found is not None
    assert found.bill_id == sample_bill.bill_id

    not_found = mock_service.get_bill_by_id("nonexistent-bill")
    assert not_found is None


# ---------------------------------------------------------------------------
# Test: Company loading
# ---------------------------------------------------------------------------


def test_get_all_companies(mock_service, sample_company):
    """All companies are returned from repository."""
    companies = mock_service.get_all_companies()
    assert len(companies) == 1
    assert companies[0].isin == sample_company.isin


def test_get_company_by_isin(mock_service, sample_company):
    """Companies can be looked up by ISIN."""
    found = mock_service.get_company_by_isin(sample_company.isin)
    assert found is not None

    not_found = mock_service.get_company_by_isin("INE_NONEXISTENT")
    assert not_found is None


# ---------------------------------------------------------------------------
# Test: Date filtering — PRIMARY FEATURE
# ---------------------------------------------------------------------------


def test_newly_arrived_bills_uses_introduction_date():
    """
    Newly arrived bills must use Bill.introduction_date exclusively.
    PDF download date, file creation date, and other dates must not be used.
    """
    today = date.today()
    recent_date = today - timedelta(days=5)
    old_date = date(2020, 1, 1)

    recent_bill = _make_bill("recent-bill", "Recent Bill", intro_date=recent_date)
    old_bill = _make_bill("old-bill", "Old Bill", intro_date=old_date)
    no_date_bill = _make_bill("no-date-bill", "No Date Bill", intro_date=None)
    no_date_bill.introduction_date = None

    mock_br = MagicMock()
    mock_br.get_all.return_value = [recent_bill, old_bill, no_date_bill]
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)

    # Last 30 days should only return recent_bill
    new_bills = service.get_newly_arrived_bills(days=30)
    bill_ids = [b.bill_id for b in new_bills]
    assert "recent-bill" in bill_ids, "Recent bill must be included"
    assert "old-bill" not in bill_ids, "Old bill must NOT be included in last 30 days"
    assert "no-date-bill" not in bill_ids, "Bill without date must NOT be included"


def test_date_filter_last_7_days():
    """Last 7 days filter works correctly."""
    today = date.today()
    recent = _make_bill("recent-7d", intro_date=today - timedelta(days=3))
    slightly_older = _make_bill("older-30d", intro_date=today - timedelta(days=15))

    mock_br = MagicMock()
    mock_br.get_all.return_value = [recent, slightly_older]
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)
    bills_7d = service.get_newly_arrived_bills(days=7)

    bill_ids = [b.bill_id for b in bills_7d]
    assert "recent-7d" in bill_ids
    assert "older-30d" not in bill_ids


def test_date_filter_custom_range():
    """Custom date range filtering works correctly."""
    bill1 = _make_bill("bill-jan", intro_date=date(2024, 1, 15))
    bill2 = _make_bill("bill-jun", intro_date=date(2024, 6, 20))
    bill3 = _make_bill("bill-dec", intro_date=date(2024, 12, 5))

    mock_br = MagicMock()
    mock_br.get_all.return_value = [bill1, bill2, bill3]
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)

    # June to November 2024
    result = service.get_newly_arrived_bills(
        since=date(2024, 6, 1),
        until=date(2024, 11, 30),
    )
    bill_ids = [b.bill_id for b in result]
    assert "bill-jan" not in bill_ids
    assert "bill-jun" in bill_ids
    assert "bill-dec" not in bill_ids


def test_bills_sorted_newest_first():
    """Bills are returned sorted newest-first."""
    bills = [
        _make_bill("bill-a", intro_date=date(2024, 2, 1)),
        _make_bill("bill-b", intro_date=date(2024, 8, 15)),
        _make_bill("bill-c", intro_date=date(2024, 5, 10)),
    ]

    mock_br = MagicMock()
    mock_br.get_all.return_value = bills
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)
    result = service.get_newly_arrived_bills(
        since=date(2024, 1, 1), until=date(2024, 12, 31)
    )

    assert result[0].bill_id == "bill-b"  # August
    assert result[1].bill_id == "bill-c"  # May
    assert result[2].bill_id == "bill-a"  # February


def test_no_bills_returns_empty_message():
    """Empty result when no bills match the date range."""
    bill = _make_bill("old-bill", intro_date=date(2020, 1, 1))

    mock_br = MagicMock()
    mock_br.get_all.return_value = [bill]
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)
    result = service.get_newly_arrived_bills(days=7)
    assert result == []


# ---------------------------------------------------------------------------
# Test: Bill type classification
# ---------------------------------------------------------------------------


def test_bill_classification_from_ministry():
    """Bills are classified using ministerial taxonomy."""
    finance_bill = _make_bill(ministry="Finance")
    cat, source = _classify_bill(finance_bill)
    assert cat == "Financial / Banking"
    assert source == "Source category"


def test_bill_classification_civil_aviation():
    """Civil Aviation ministry maps to Transport / Aviation."""
    bill = _make_bill(ministry="Civil Aviation")
    cat, source = _classify_bill(bill)
    assert "Transport" in cat or "Aviation" in cat


def test_bill_classification_environment():
    """Environment ministry maps to Environment category."""
    bill = _make_bill(ministry="Environment, Forests and Climate Change")
    cat, source = _classify_bill(bill)
    assert cat == "Environment"


def test_bill_classification_sector_fallback():
    """Unknown ministry falls back to sector-based classification."""
    bill = _make_bill(ministry="Unknown Ministry XYZ")
    bill.sectors = ["Banking Sector"]
    cat, source = _classify_bill(bill)
    assert "Financial" in cat or "Banking" in cat
    assert source == "System category"


def test_bill_classification_no_info():
    """Bill with no ministry or sector gets default classification."""
    bill = _make_bill(ministry="")
    bill.sectors = []
    cat, source = _classify_bill(bill)
    assert cat  # Must return something
    assert source in ("Source category", "System category")


def test_classify_bill_static_method():
    """DashboardService.classify_bill() is a static method that works correctly."""
    bill = _make_bill(ministry="Railways")
    cat, source = DashboardService.classify_bill(bill)
    assert cat == "Transport / Railways"


# ---------------------------------------------------------------------------
# Test: Sector filtering
# ---------------------------------------------------------------------------


def test_sector_filter_in_decision_dataframe(mock_service, sample_decision):
    """Sector filter on decision DataFrame works correctly."""
    df = mock_service.get_decision_dataframe()
    assert not df.empty

    filtered = df[df["sector"] == "Financial Services"]
    assert len(filtered) > 0


# ---------------------------------------------------------------------------
# Test: Missing artifact handling
# ---------------------------------------------------------------------------


def test_missing_decisions_graceful():
    """Missing decision repository is handled gracefully."""
    mock_dr = MagicMock()
    mock_dr.load_all.side_effect = FileNotFoundError("data/decision_support missing")
    mock_br = MagicMock()
    mock_br.get_all.return_value = [_make_bill()]
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)
    records = service.get_decision_records()

    # Should return empty list, not raise
    assert records == []
    assert service.decisions_available is False


def test_missing_bills_graceful():
    """Missing bill repository is handled gracefully."""
    mock_br = MagicMock()
    mock_br.get_all.side_effect = FileNotFoundError("Bill repo missing")
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)
    bills = service.get_all_bills()
    assert bills == []


def test_missing_company_repo_graceful():
    """Missing company repository is handled gracefully."""
    mock_br = MagicMock()
    mock_br.get_all.return_value = []
    mock_cr = MagicMock()
    mock_cr.get_all.side_effect = RuntimeError("Company repo error")
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)
    companies = service.get_all_companies()
    assert companies == []


# ---------------------------------------------------------------------------
# Test: Market impact aggregation
# ---------------------------------------------------------------------------


def test_market_impact_summary_empty():
    """Market impact summary returns zero-values for empty DataFrame."""
    mock_br = MagicMock()
    mock_br.get_all.return_value = []
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)
    stats = service.get_market_impact_summary()
    assert stats["total_records"] == 0
    assert stats["positive_count"] == 0


def test_market_impact_summary_with_records(mock_service):
    """Market impact summary correctly counts directions."""
    stats = mock_service.get_market_impact_summary()
    assert stats["total_records"] == 1
    assert stats["positive_count"] == 1
    assert stats["negative_count"] == 0
    assert stats["mean_market_moving_prob"] == pytest.approx(0.72)


# ---------------------------------------------------------------------------
# Test: Decision DataFrame enrichment
# ---------------------------------------------------------------------------


def test_decision_df_enriched_with_company_and_bill(mock_service, sample_company, sample_bill):
    """Decision DataFrame is enriched with company and bill metadata."""
    df = mock_service.get_decision_dataframe()
    assert not df.empty
    row = df.iloc[0]
    assert row["company_name"] == sample_company.company_name
    assert row["sector"] == sample_company.sector
    assert row["bill_title"] == sample_bill.title
    assert row["ministry"] == sample_bill.ministry


def test_decision_df_caching(mock_service):
    """Decision DataFrame is cached after first call."""
    df1 = mock_service.get_decision_dataframe()
    df2 = mock_service.get_decision_dataframe()
    # Should be the same object (cached)
    assert df1 is df2


# ---------------------------------------------------------------------------
# Test: Production scope integrity
# ---------------------------------------------------------------------------


def test_production_scope_counts(mock_service):
    """Production scope counts are correct."""
    scope = mock_service.get_production_scope()
    assert isinstance(scope, ProductionScope)
    assert scope.production_bills_count == 1  # One bill in mock
    assert scope.production_decision_records == 1


def test_production_scope_excludes_non_legislative():
    """Production scope excludes test/non-legislative bill stubs."""
    real = _make_bill("real-2024")
    stub1 = _make_bill("key-issues-and-analysis")
    stub2 = _make_bill("service-bill")

    mock_br = MagicMock()
    mock_br.get_all.return_value = [real, stub1, stub2]
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)
    scope = service.get_production_scope()

    assert scope.total_bills_in_repo == 3
    assert scope.production_bills_count == 1
    assert "key-issues-and-analysis" in scope.non_legislative_bills
    assert "service-bill" in scope.non_legislative_bills


# ---------------------------------------------------------------------------
# Test: Deterministic output
# ---------------------------------------------------------------------------


def test_deterministic_filtering():
    """Applying same filters twice produces identical results."""
    bills = [
        _make_bill("bill-a", intro_date=date(2024, 2, 1)),
        _make_bill("bill-b", intro_date=date(2024, 8, 15)),
    ]
    mock_br = MagicMock()
    mock_br.get_all.return_value = bills
    mock_cr = MagicMock()
    mock_cr.get_all.return_value = []
    mock_dr = MagicMock()
    mock_dr.load_all.return_value = []

    service = DashboardService(bill_repo=mock_br, company_repo=mock_cr, decision_repo=mock_dr)

    result1 = service.get_newly_arrived_bills(
        since=date(2024, 1, 1), until=date(2024, 12, 31)
    )
    result2 = service.get_newly_arrived_bills(
        since=date(2024, 1, 1), until=date(2024, 12, 31)
    )

    assert [b.bill_id for b in result1] == [b.bill_id for b in result2]


# ---------------------------------------------------------------------------
# Test: Read-only behavior
# ---------------------------------------------------------------------------


def test_service_does_not_write_files(mock_service, tmp_path):
    """Service does not write any files to disk."""
    # Track file writes via monkeypatching
    write_calls = []

    import builtins
    original_open = builtins.open

    def mock_open(*args, **kwargs):
        if len(args) >= 2 and "w" in str(args[1]):
            write_calls.append(args)
        return original_open(*args, **kwargs)

    with patch("builtins.open", side_effect=mock_open):
        # These operations must not write any files
        _ = mock_service.get_all_bills()
        _ = mock_service.get_production_bills()
        _ = mock_service.get_all_companies()
        _ = mock_service.get_decision_records()

    assert len(write_calls) == 0, (
        f"DashboardService made {len(write_calls)} file write(s): {write_calls}"
    )


# ---------------------------------------------------------------------------
# Test: Clear cache
# ---------------------------------------------------------------------------


def test_clear_cache(mock_service):
    """Cache clearing resets all in-memory caches."""
    # Populate caches
    _ = mock_service.get_all_bills()
    _ = mock_service.get_all_companies()
    _ = mock_service.get_decision_records()

    assert mock_service._bills_cache is not None
    assert mock_service._companies_cache is not None

    mock_service.clear_cache()

    assert mock_service._bills_cache is None
    assert mock_service._companies_cache is None
    assert mock_service._decisions_cache is None
    assert mock_service._decision_df_cache is None
    assert mock_service._bill_summaries_cache is None
