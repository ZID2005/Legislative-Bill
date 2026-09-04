"""
tests/test_dashboard_filters.py
===============================
Unit tests for Task 7.4 FilterEngine.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dashboard.filters.filter_engine import FilterEngine


@pytest.fixture
def sample_df():
    return pd.DataFrame([
        {
            "decision_id": "dec_1",
            "bill_id": "bill-a",
            "company_isin": "INE001",
            "sector": "Banking",
            "ministry": "Finance",
            "policy_domain": "Financial",
            "risk_category": "LOW",
            "predicted_direction": "POSITIVE",
            "market_moving_probability": 0.65,
            "anticipation_evidence": "NO_EVIDENCE",
            "event_window": "[-10,+10]",
        },
        {
            "decision_id": "dec_2",
            "bill_id": "bill-a",
            "company_isin": "INE002",
            "sector": "Aviation",
            "ministry": "Civil Aviation",
            "policy_domain": "Transport",
            "risk_category": "MODERATE",
            "predicted_direction": "NEGATIVE",
            "market_moving_probability": 0.40,
            "anticipation_evidence": "MODERATE_EVIDENCE",
            "event_window": "[-1,+1]",
        },
        {
            "decision_id": "dec_3",
            "bill_id": "bill-b",
            "company_isin": "INE003",
            "sector": "Energy",
            "ministry": "Petroleum",
            "policy_domain": "Energy",
            "risk_category": "HIGH",
            "predicted_direction": "NEUTRAL",
            "market_moving_probability": 0.80,
            "anticipation_evidence": "STRONG_EVIDENCE",
            "event_window": "[-5,+5]",
        },
    ])


def test_filter_all_returns_unmodified(sample_df):
    """Verify 'All' or None criteria return full DataFrame."""
    res = FilterEngine.apply_filters(sample_df, bill_id="All", sector=None)
    assert len(res) == len(sample_df)


def test_filter_by_bill_id(sample_df):
    """Verify filtering by single bill_id and list of bill_ids."""
    res = FilterEngine.apply_filters(sample_df, bill_id="bill-a")
    assert len(res) == 2
    assert set(res["decision_id"]) == {"dec_1", "dec_2"}

    res_list = FilterEngine.apply_filters(sample_df, bill_id=["bill-a", "bill-b"])
    assert len(res_list) == 3


def test_filter_by_company_isin(sample_df):
    """Verify filtering by company_isin."""
    res = FilterEngine.apply_filters(sample_df, company_isin="INE001")
    assert len(res) == 1
    assert res.iloc[0]["decision_id"] == "dec_1"


def test_filter_by_sector_and_ministry(sample_df):
    """Verify filtering by sector and ministry."""
    res_sec = FilterEngine.apply_filters(sample_df, sector="Aviation")
    assert len(res_sec) == 1
    assert res_sec.iloc[0]["decision_id"] == "dec_2"

    res_min = FilterEngine.apply_filters(sample_df, ministry="Petroleum")
    assert len(res_min) == 1
    assert res_min.iloc[0]["decision_id"] == "dec_3"


def test_filter_by_risk_category_and_direction(sample_df):
    """Verify filtering by risk category and predicted direction."""
    res_risk = FilterEngine.apply_filters(sample_df, risk_category="HIGH")
    assert len(res_risk) == 1
    assert res_risk.iloc[0]["decision_id"] == "dec_3"

    res_dir = FilterEngine.apply_filters(sample_df, direction="POSITIVE")
    assert len(res_dir) == 1
    assert res_dir.iloc[0]["decision_id"] == "dec_1"


def test_filter_market_moving(sample_df):
    """Verify boolean filtering for market-moving flag (threshold 0.50)."""
    res_mm = FilterEngine.apply_filters(sample_df, market_moving_only=True)
    assert len(res_mm) == 2  # dec_1 (0.65) and dec_3 (0.80)
    assert set(res_mm["decision_id"]) == {"dec_1", "dec_3"}

    res_non_mm = FilterEngine.apply_filters(sample_df, market_moving_only=False)
    assert len(res_non_mm) == 1
    assert res_non_mm.iloc[0]["decision_id"] == "dec_2"


def test_filter_anticipation_and_window(sample_df):
    """Verify filtering by anticipation evidence and event window."""
    res_ant = FilterEngine.apply_filters(sample_df, anticipation_category="STRONG_EVIDENCE")
    assert len(res_ant) == 1
    assert res_ant.iloc[0]["decision_id"] == "dec_3"

    res_win = FilterEngine.apply_filters(sample_df, event_window="[-1,+1]")
    assert len(res_win) == 1
    assert res_win.iloc[0]["decision_id"] == "dec_2"


def test_filter_empty_dataframe():
    """Verify empty DataFrame input returns empty DataFrame gracefully."""
    empty_df = pd.DataFrame()
    res = FilterEngine.apply_filters(empty_df, bill_id="bill-a")
    assert res.empty


def test_get_filter_options(sample_df):
    """Verify extraction of available options across dimensions."""
    options = FilterEngine.get_filter_options(sample_df)
    assert "bill-a" in options["bills"]
    assert "INE001" in options["companies"]
    assert "Banking" in options["sectors"]
    assert "Finance" in options["ministries"]
    assert "LOW" in options["risk_categories"]
    assert "POSITIVE" in options["directions"]
    assert "NO_EVIDENCE" in options["anticipation_tiers"]
    assert "[-10,+10]" in options["event_windows"]

    # Test empty dataframe returns empty lists
    empty_opts = FilterEngine.get_filter_options(pd.DataFrame())
    assert empty_opts["bills"] == []
