"""
dashboard/pages/__init__.py
===========================
Page views package for the Legislative Intelligence Dashboard.
"""

from __future__ import annotations

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

__all__ = [
    "render_anticipation_view",
    "render_backtest_view",
    "render_bill_explorer",
    "render_business_view",
    "render_company_explorer",
    "render_explainability_view",
    "render_investor_view",
    "render_landing_page",
    "render_methodology_view",
    "render_public_view",
    "render_risk_overview",
]
