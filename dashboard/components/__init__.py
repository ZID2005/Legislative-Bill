"""
dashboard/components/__init__.py
================================
UI components for the Legislative Intelligence Dashboard.

Task 7.4.1 additions:
- bill_cards: Newly-arrived bill card components
- cards: KPI summary metric cards and scope diagnostic
- filters: Enhanced bill feed filter panel
- tables: Company exposure and bills summary tables
"""

from __future__ import annotations

from dashboard.components.bill_cards import (
    render_bill_card,
    render_bill_mini_card,
    render_no_bills_message,
)
from dashboard.components.cards import (
    render_kpi_header,
    render_market_impact_cards,
    render_scope_diagnostic_card,
)
from dashboard.components.disclaimer import (
    render_anticipation_disclaimer,
    render_general_disclaimer,
    render_zero_modification_banner,
)
from dashboard.components.filter_sidebar import render_filter_sidebar
from dashboard.components.filters import (
    apply_bill_summary_filters,
    render_bill_feed_filters,
)
from dashboard.components.header import render_header
from dashboard.components.kpi_cards import render_kpi_cards
from dashboard.components.report_viewer import (
    render_bill_report,
    render_company_report,
    render_stakeholder_report,
)
from dashboard.components.tables import (
    render_bills_summary_table,
    render_company_exposure_table,
)

__all__ = [
    # Task 7.4.1 new components
    "apply_bill_summary_filters",
    "render_bill_card",
    "render_bill_feed_filters",
    "render_bill_mini_card",
    "render_bills_summary_table",
    "render_company_exposure_table",
    "render_kpi_header",
    "render_market_impact_cards",
    "render_no_bills_message",
    "render_scope_diagnostic_card",
    # Task 7.3 legacy components
    "render_anticipation_disclaimer",
    "render_bill_report",
    "render_company_report",
    "render_filter_sidebar",
    "render_general_disclaimer",
    "render_header",
    "render_kpi_cards",
    "render_stakeholder_report",
    "render_zero_modification_banner",
]
