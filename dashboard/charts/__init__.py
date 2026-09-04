"""
dashboard/charts/__init__.py
============================
Visualization factory package for the Legislative Intelligence Dashboard.
"""

from __future__ import annotations

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

__all__ = [
    "create_anticipation_bar",
    "create_direction_pie",
    "create_drawdown_curve",
    "create_feature_importance_bar",
    "create_impact_score_hist",
    "create_market_moving_distribution",
    "create_portfolio_equity_curve",
    "create_risk_category_bar",
    "create_risk_matrix",
    "create_sector_impact_bar",
    "create_sector_risk_comparison",
]
