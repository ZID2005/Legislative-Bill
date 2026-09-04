"""
tests/test_dashboard_charts.py
==============================
Unit tests for Task 7.4 Dashboard Chart Generators.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dashboard.charts.backtest_charts import (
    create_drawdown_curve,
    create_feature_importance_bar,
    create_portfolio_equity_curve,
)
from dashboard.charts.distribution_charts import (
    create_anticipation_bar,
    create_direction_pie,
    create_impact_score_hist,
    create_market_moving_distribution,
    create_risk_category_bar,
)
from dashboard.charts.risk_matrix import create_risk_matrix
from dashboard.charts.sector_charts import (
    create_sector_impact_bar,
    create_sector_risk_comparison,
)


@pytest.fixture
def populated_df():
    return pd.DataFrame([
        {
            "decision_id": "dec_1",
            "bill_id": "bill-a",
            "bill_title": "Banking Bill",
            "company_isin": "INE001",
            "company_name": "Bank Corp",
            "ticker": "BANK",
            "sector": "Financials",
            "impact_score": 0.45,
            "risk_score": 0.35,
            "risk_category": "LOW",
            "predicted_direction": "POSITIVE",
            "market_moving_probability": 0.75,
            "anticipation_evidence": "NO_EVIDENCE",
            "confidence": "HIGH",
            "event_window": "[-10,+10]",
        },
        {
            "decision_id": "dec_2",
            "bill_id": "bill-b",
            "bill_title": "Aviation Bill",
            "company_isin": "INE002",
            "company_name": "Air Corp",
            "ticker": "AIR",
            "sector": "Aviation",
            "impact_score": 0.15,
            "risk_score": 0.55,
            "risk_category": "MODERATE",
            "predicted_direction": "NEGATIVE",
            "market_moving_probability": 0.30,
            "anticipation_evidence": "STRONG_EVIDENCE",
            "confidence": "MEDIUM",
            "event_window": "[-1,+1]",
        },
    ])


def test_distribution_charts(populated_df):
    """Verify distribution chart generation on populated and empty data."""
    fig_risk = create_risk_category_bar(populated_df)
    assert fig_risk is not None
    assert hasattr(fig_risk, "data")
    assert len(fig_risk.data) > 0

    fig_impact = create_impact_score_hist(populated_df)
    assert fig_impact is not None

    fig_mm = create_market_moving_distribution(populated_df)
    assert fig_mm is not None

    fig_dir = create_direction_pie(populated_df)
    assert fig_dir is not None

    fig_anticip = create_anticipation_bar(populated_df)
    assert fig_anticip is not None

    # Test empty dataframe behavior
    empty_df = pd.DataFrame()
    assert create_risk_category_bar(empty_df) is not None
    assert create_impact_score_hist(empty_df) is not None
    assert create_market_moving_distribution(empty_df) is not None
    assert create_direction_pie(empty_df) is not None
    assert create_anticipation_bar(empty_df) is not None


def test_risk_matrix_chart(populated_df):
    """Verify 2D Risk Matrix scatter plot generation."""
    fig = create_risk_matrix(populated_df)
    assert fig is not None
    assert len(fig.data) > 0

    fig_empty = create_risk_matrix(pd.DataFrame())
    assert fig_empty is not None


def test_sector_charts(populated_df):
    """Verify sector comparison charts."""
    fig_imp = create_sector_impact_bar(populated_df)
    assert fig_imp is not None

    fig_comp = create_sector_risk_comparison(populated_df)
    assert fig_comp is not None

    empty_df = pd.DataFrame()
    assert create_sector_impact_bar(empty_df) is not None
    assert create_sector_risk_comparison(empty_df) is not None


def test_backtest_charts():
    """Verify backtesting and feature importance visualizations."""
    feat_data = [{"feature": "beta", "mean_abs_shap": 0.12}, {"feature": "nlp_emb", "mean_abs_shap": 0.35}]
    fig_feat = create_feature_importance_bar(feat_data)
    assert fig_feat is not None
    assert len(fig_feat.data) > 0

    ts_df = pd.DataFrame([
        {"date": "2024-01-01", "cumulative_strategy_return": 0.05, "cumulative_benchmark_return": 0.02, "drawdown": -0.01},
        {"date": "2024-01-02", "cumulative_strategy_return": 0.07, "cumulative_benchmark_return": 0.03, "drawdown": -0.005},
    ])

    fig_eq = create_portfolio_equity_curve(ts_df)
    assert fig_eq is not None
    assert len(fig_eq.data) == 2

    fig_dd = create_drawdown_curve(ts_df)
    assert fig_dd is not None
    assert len(fig_dd.data) == 1

    # Empty inputs
    assert create_feature_importance_bar([]) is not None
    assert create_portfolio_equity_curve(pd.DataFrame()) is not None
    assert create_drawdown_curve(pd.DataFrame()) is not None
