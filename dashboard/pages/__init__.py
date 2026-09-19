"""
dashboard/pages/__init__.py
===========================
Page views package for the Legislative Intelligence Dashboard.

Task 7.4.2 — Extended with modular analytical pages:
- bills.py (All Bills master table)
- bill_detail.py (Bill Intelligence deep dive)
- companies.py (Company Intelligence multi-entity comparative)
- company_detail.py (Company Detail exposure breakdown)
- predictions.py (Market Impact Predictions aggregate view)
- risk.py (Risk Overview canonical tiers & matrix)
- anticipation.py (Anticipation & Pricing-In analysis)
- backtesting.py (Historical Backtesting walk-forward simulation)
- methodology.py (Academic Methodology & 18-stage blueprint)
"""

from __future__ import annotations

# Task 7.4.2 Modular Pages
from dashboard.pages.anticipation import render_anticipation_page
from dashboard.pages.backtesting import render_backtesting_page
from dashboard.pages.bill_detail import render_bill_detail_page
from dashboard.pages.bills import render_bills_page
from dashboard.pages.companies import render_companies_page
from dashboard.pages.company_detail import render_company_detail_page
from dashboard.pages.methodology import render_methodology_page
from dashboard.pages.overview import render_overview_page
from dashboard.pages.predictions import render_predictions_page
from dashboard.pages.risk import render_risk_page
from dashboard.pages.india_explorer import render_india_explorer_page

# Legacy / Task 7.3 Exploratory Pages (Kept for backwards compatibility)
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
    # Task 7.4.2 Canonical Pages
    "render_overview_page",
    "render_bills_page",
    "render_bill_detail_page",
    "render_companies_page",
    "render_company_detail_page",
    "render_predictions_page",
    "render_risk_page",
    "render_anticipation_page",
    "render_backtesting_page",
    "render_methodology_page",
    "render_india_explorer_page",
    # Task 7.3 Exploratory Pages
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
