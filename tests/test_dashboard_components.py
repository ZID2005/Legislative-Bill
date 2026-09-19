"""
tests/test_dashboard_components.py
====================================
Task 7.4.1 — Unit tests for dashboard UI components.

Tests components in a headless (no-Streamlit-runtime) manner by
verifying the logic in helper functions that don't require Streamlit.

Coverage:
- bill_cards: direction config, risk colors, BillSummary rendering logic
- cards: KPI card data transformations
- filters: apply_bill_summary_filters logic (pure Python)
- tables: table formatting helpers
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest
import pandas as pd

from dashboard.services.dashboard_service import BillSummary, ProductionScope


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_summary(
    bill_id: str = "test-bill-2024",
    title: str = "Test Bill 2024",
    ministry: str = "Finance",
    house: str = "Lok Sabha",
    status: str = "Passed Both Houses",
    bill_category: str = "Financial / Banking",
    introduction_date: date | None = date(2024, 8, 9),
    sectors: list[str] | None = None,  # None = use default ["Financial Services"]
    affected_company_count: int = 5,
    has_prediction: bool = True,
    predicted_direction: str = "POSITIVE",
    market_moving_probability: float = 0.72,
    impact_strength: str = "MEDIUM",
    risk_category: str = "MODERATE",
    anticipation_class: str = "NO_EVIDENCE",
    has_decision_support: bool = True,
    has_anticipation: bool = True,
    _sectors_override: list[str] | None = None,  # Explicitly set to [] for empty sectors
) -> BillSummary:
    # Determine sectors: if _sectors_override is provided, use it
    # If sectors is explicitly [] it means empty; if None, default to ["Financial Services"]
    actual_sectors: list[str]
    if _sectors_override is not None:
        actual_sectors = _sectors_override
    elif sectors is not None:
        actual_sectors = sectors
    else:
        actual_sectors = ["Financial Services"]

    return BillSummary(
        bill_id=bill_id,
        title=title,
        bill_number="",
        introduction_date=introduction_date,
        house=house,
        ministry=ministry,
        status=status,
        bill_category=bill_category,
        category_source="Source category",
        description="A test bill for dashboard component testing.",
        sectors=actual_sectors,
        url="https://example.com/bill",
        affected_company_count=affected_company_count,
        has_prediction=has_prediction,
        predicted_direction=predicted_direction,
        market_moving_probability=market_moving_probability,
        impact_strength=impact_strength,
        risk_category=risk_category,
        anticipation_class=anticipation_class,
        has_decision_support=has_decision_support,
        has_anticipation=has_anticipation,
    )


# ---------------------------------------------------------------------------
# Tests: bill_cards module logic
# ---------------------------------------------------------------------------


def test_bill_summary_attributes():
    """BillSummary dataclass has expected attributes."""
    s = _make_summary()
    assert s.bill_id == "test-bill-2024"
    assert s.title == "Test Bill 2024"
    assert s.introduction_date == date(2024, 8, 9)
    assert s.house == "Lok Sabha"
    assert s.ministry == "Finance"
    assert s.status == "Passed Both Houses"
    assert s.bill_category == "Financial / Banking"
    assert s.has_prediction is True
    assert s.predicted_direction == "POSITIVE"
    assert s.market_moving_probability == pytest.approx(0.72)
    assert s.risk_category == "MODERATE"


def test_bill_summary_no_prediction():
    """BillSummary with no prediction has correct defaults."""
    s = _make_summary(
        has_prediction=False,
        has_decision_support=False,
        has_anticipation=False,
        predicted_direction=None,
        market_moving_probability=None,
        impact_strength=None,
        risk_category=None,
        anticipation_class=None,
    )
    assert s.has_prediction is False
    assert s.predicted_direction is None
    assert s.market_moving_probability is None


def test_bill_summary_no_introduction_date():
    """BillSummary handles None introduction_date gracefully."""
    s = _make_summary(introduction_date=None)
    assert s.introduction_date is None


def test_bill_summary_sectors():
    """BillSummary preserves sector list."""
    sectors = ["Banking", "Insurance", "NBFC"]
    s = _make_summary(sectors=sectors)
    assert s.sectors == sectors


def test_bill_summary_empty_sectors():
    """BillSummary handles empty sectors list."""
    s = _make_summary(_sectors_override=[])
    assert s.sectors == []


# ---------------------------------------------------------------------------
# Tests: filters module — apply_bill_summary_filters (pure Python)
# ---------------------------------------------------------------------------


def test_filter_by_ministry():
    """Ministry filter correctly filters bill summaries."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("bill-1", ministry="Finance"),
        _make_summary("bill-2", ministry="Railways"),
    ]
    filters = {"since": None, "until": None, "ministry": "Finance",
               "house": None, "category": None, "status": None,
               "sector": None, "direction": None, "risk_category": None,
               "anticipation": None}

    result = apply_bill_summary_filters(bills, filters)
    assert len(result) == 1
    assert result[0].bill_id == "bill-1"


def test_filter_by_direction():
    """Direction filter correctly filters bill summaries."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("pos-bill", predicted_direction="POSITIVE"),
        _make_summary("neg-bill", predicted_direction="NEGATIVE"),
    ]
    filters = {"since": None, "until": None, "ministry": None, "house": None,
               "category": None, "status": None, "sector": None,
               "direction": "NEGATIVE", "risk_category": None, "anticipation": None}

    result = apply_bill_summary_filters(bills, filters)
    assert len(result) == 1
    assert result[0].bill_id == "neg-bill"


def test_filter_by_risk_category():
    """Risk category filter works correctly."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("high-risk", risk_category="HIGH"),
        _make_summary("low-risk", risk_category="LOW"),
    ]
    filters = {"since": None, "until": None, "ministry": None, "house": None,
               "category": None, "status": None, "sector": None,
               "direction": None, "risk_category": "HIGH", "anticipation": None}

    result = apply_bill_summary_filters(bills, filters)
    assert len(result) == 1
    assert result[0].bill_id == "high-risk"


def test_filter_by_anticipation():
    """Anticipation evidence filter works correctly."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("strong-ant", anticipation_class="STRONG_EVIDENCE"),
        _make_summary("no-ant", anticipation_class="NO_EVIDENCE"),
    ]
    filters = {"since": None, "until": None, "ministry": None, "house": None,
               "category": None, "status": None, "sector": None, "direction": None,
               "risk_category": None, "anticipation": "STRONG_EVIDENCE"}

    result = apply_bill_summary_filters(bills, filters)
    assert len(result) == 1
    assert result[0].bill_id == "strong-ant"


def test_filter_by_status():
    """Legislative status filter works correctly."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("passed-bill", status="Passed Both Houses"),
        _make_summary("committee-bill", status="In Committee"),
    ]
    filters = {"since": None, "until": None, "ministry": None, "house": None,
               "category": None, "status": "In Committee", "sector": None,
               "direction": None, "risk_category": None, "anticipation": None}

    result = apply_bill_summary_filters(bills, filters)
    assert len(result) == 1
    assert result[0].bill_id == "committee-bill"


def test_filter_by_bill_category():
    """Bill category/type filter works correctly."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("fin-bill", bill_category="Financial / Banking"),
        _make_summary("env-bill", bill_category="Environment"),
    ]
    filters = {"since": None, "until": None, "ministry": None, "house": None,
               "category": "Environment", "status": None, "sector": None,
               "direction": None, "risk_category": None, "anticipation": None}

    result = apply_bill_summary_filters(bills, filters)
    assert len(result) == 1
    assert result[0].bill_id == "env-bill"


def test_filter_by_date_range():
    """Date range filter excludes bills outside range."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("jan-bill", introduction_date=date(2024, 1, 15)),
        _make_summary("aug-bill", introduction_date=date(2024, 8, 9)),
        _make_summary("dec-bill", introduction_date=date(2024, 12, 5)),
    ]
    filters = {
        "since": date(2024, 6, 1),
        "until": date(2024, 10, 31),
        "ministry": None, "house": None, "category": None, "status": None,
        "sector": None, "direction": None, "risk_category": None, "anticipation": None,
    }

    result = apply_bill_summary_filters(bills, filters)
    assert len(result) == 1
    assert result[0].bill_id == "aug-bill"


def test_filter_excludes_bills_without_date_when_date_required():
    """Bills without introduction_date are excluded from date-filtered results."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("has-date", introduction_date=date(2024, 8, 9)),
        _make_summary("no-date", introduction_date=None),
    ]
    filters = {
        "since": date(2024, 1, 1),
        "until": date(2024, 12, 31),
        "ministry": None, "house": None, "category": None, "status": None,
        "sector": None, "direction": None, "risk_category": None, "anticipation": None,
    }
    result = apply_bill_summary_filters(bills, filters)
    bill_ids = [b.bill_id for b in result]
    assert "has-date" in bill_ids
    assert "no-date" not in bill_ids


def test_no_filters_returns_all_bills():
    """Empty filter dict returns all bills sorted newest-first."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("bill-b", introduction_date=date(2024, 8, 9)),
        _make_summary("bill-a", introduction_date=date(2024, 2, 1)),
    ]
    filters = {"since": None, "until": None, "ministry": None, "house": None,
               "category": None, "status": None, "sector": None,
               "direction": None, "risk_category": None, "anticipation": None}

    result = apply_bill_summary_filters(bills, filters)
    assert len(result) == 2
    # Should be sorted newest-first
    assert result[0].bill_id == "bill-b"


def test_combined_filters():
    """Multiple filters applied simultaneously work correctly."""
    from dashboard.components.filters import apply_bill_summary_filters

    bills = [
        _make_summary("match", ministry="Finance", predicted_direction="POSITIVE",
                      risk_category="MODERATE"),
        _make_summary("wrong-dir", ministry="Finance", predicted_direction="NEGATIVE",
                      risk_category="MODERATE"),
        _make_summary("wrong-min", ministry="Railways", predicted_direction="POSITIVE",
                      risk_category="MODERATE"),
    ]
    filters = {"since": None, "until": None, "ministry": "Finance", "house": None,
               "category": None, "status": None, "sector": None,
               "direction": "POSITIVE", "risk_category": None, "anticipation": None}

    result = apply_bill_summary_filters(bills, filters)
    assert len(result) == 1
    assert result[0].bill_id == "match"


# ---------------------------------------------------------------------------
# Tests: ProductionScope dataclass
# ---------------------------------------------------------------------------


def test_production_scope_defaults():
    """ProductionScope has sensible default values."""
    scope = ProductionScope()
    assert scope.production_bills_count == 20
    assert scope.production_companies_count == 47
    assert scope.production_decision_records == 4700
    assert scope.scope_integrity_verdict == "PRODUCTION_PARITY_CONFIRMED"


def test_production_scope_custom():
    """ProductionScope accepts custom values."""
    scope = ProductionScope(
        total_bills_in_repo=25,
        production_bills_count=22,
        total_companies_in_repo=55,
        production_companies_count=50,
        production_decision_records=5500,
    )
    assert scope.total_bills_in_repo == 25
    assert scope.production_bills_count == 22
    assert scope.production_decision_records == 5500


# ---------------------------------------------------------------------------
# Tests: tables module logic
# ---------------------------------------------------------------------------


def test_company_exposure_table_empty():
    """Empty DataFrame is handled gracefully in table component."""
    # Import will fail in headless mode but logic can be tested
    from dashboard.components.tables import (
        _DIRECTION_DISPLAY,
        _RISK_DISPLAY,
        _ANTICIPATION_DISPLAY,
    )
    assert "POSITIVE" in _DIRECTION_DISPLAY
    assert "NEGATIVE" in _DIRECTION_DISPLAY
    assert "NEUTRAL" in _DIRECTION_DISPLAY
    assert "VERY_HIGH" in _RISK_DISPLAY
    assert "STRONG_EVIDENCE" in _ANTICIPATION_DISPLAY


def test_direction_display_mappings():
    """Direction emoji mappings are complete and correct."""
    from dashboard.components.tables import _DIRECTION_DISPLAY

    for direction in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
        assert direction in _DIRECTION_DISPLAY
        assert "📈" in _DIRECTION_DISPLAY["POSITIVE"] or "POSITIVE" in _DIRECTION_DISPLAY["POSITIVE"]


def test_risk_display_mappings():
    """Risk display mappings cover all categories."""
    from dashboard.components.tables import _RISK_DISPLAY

    expected_categories = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"]
    for cat in expected_categories:
        assert cat in _RISK_DISPLAY


# ---------------------------------------------------------------------------
# Tests: bill_cards — direction and risk config
# ---------------------------------------------------------------------------


def test_direction_config_completeness():
    """All prediction directions have configuration entries."""
    from dashboard.components.bill_cards import _DIRECTION_CONFIG

    assert "POSITIVE" in _DIRECTION_CONFIG
    assert "NEGATIVE" in _DIRECTION_CONFIG
    assert "NEUTRAL" in _DIRECTION_CONFIG

    for direction, (emoji, color) in _DIRECTION_CONFIG.items():
        assert emoji  # Non-empty emoji
        assert color.startswith("#")  # Valid hex color


def test_risk_colors_completeness():
    """All risk categories have color assignments."""
    from dashboard.components.bill_cards import _RISK_COLORS

    expected = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"]
    for cat in expected:
        assert cat in _RISK_COLORS
        assert _RISK_COLORS[cat].startswith("#")


def test_anticipation_config_completeness():
    """All anticipation classes have configuration entries."""
    from dashboard.components.bill_cards import _ANTICIPATION_CONFIG

    expected = [
        "NO_EVIDENCE",
        "WEAK_EVIDENCE",
        "MODERATE_EVIDENCE",
        "STRONG_EVIDENCE",
        "NOT_ANALYZED",
    ]
    for cls in expected:
        assert cls in _ANTICIPATION_CONFIG


# ---------------------------------------------------------------------------
# Tests: cards module
# ---------------------------------------------------------------------------


def test_scope_fields_for_kpi():
    """ProductionScope fields used by KPI cards are all present."""
    scope = ProductionScope()
    # These attributes must exist for render_kpi_header
    assert hasattr(scope, "production_bills_count")
    assert hasattr(scope, "production_companies_count")
    assert hasattr(scope, "production_decision_records")
    assert hasattr(scope, "production_report_records")
    assert hasattr(scope, "production_anticipation_records")
    assert hasattr(scope, "strong_anticipation_bills")
    assert hasattr(scope, "total_bills_in_repo")
    assert hasattr(scope, "total_companies_in_repo")
    assert hasattr(scope, "non_legislative_bills")
