"""
dashboard/components/filters.py
================================
Task 7.4.1 — Enhanced sidebar filter panel.

Provides all required filter dimensions for the bills feed and overview:
- Introduction date range (with preset shortcuts)
- Bill identity
- House
- Ministry / Department
- Bill type / category
- Legislative status
- Sector
- Company
- Impact direction
- Risk category
- Anticipation classification
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

import streamlit as st

from dashboard.services.dashboard_service import DashboardService


# Date preset shortcuts
DATE_PRESETS: dict[str, int] = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
    "Last 180 days": 180,
    "Last 365 days": 365,
    "All time": 0,
    "Custom range": -1,
}


def render_bill_feed_filters(
    service: DashboardService,
) -> dict[str, Any]:
    """
    Render sidebar filters for the Newly Arrived Bills feed.

    Returns a dictionary of filter criteria.
    """
    st.sidebar.markdown("### 📅 Date Range")

    preset = st.sidebar.selectbox(
        "Period",
        options=list(DATE_PRESETS.keys()),
        index=1,  # Default: Last 30 days
        key="bill_feed_date_preset",
    )

    today = date.today()
    since: Optional[date] = None
    until: Optional[date] = today

    if preset == "All time":
        since = date(2000, 1, 1)
    elif preset == "Custom range":
        col_from, col_to = st.sidebar.columns(2)
        with col_from:
            since = st.date_input(
                "From",
                value=today - timedelta(days=365),
                max_value=today,
                key="bill_feed_since",
            )
        with col_to:
            until = st.date_input(
                "To",
                value=today,
                max_value=today,
                key="bill_feed_until",
            )
    else:
        days = DATE_PRESETS[preset]
        since = today - timedelta(days=days)

    # Ensure since is a date (not datetime)
    if hasattr(since, "date"):
        since = since.date()
    if hasattr(until, "date"):
        until = until.date()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Bill Filters")

    options = service.get_filter_options()

    # House filter
    house_opts = ["All"] + ["Lok Sabha", "Rajya Sabha", "Not specified"]
    selected_house = st.sidebar.selectbox("House", house_opts, index=0, key="bill_feed_house")

    # Ministry filter
    ministry_opts = ["All"] + options.get("ministries", [])
    selected_ministry = st.sidebar.selectbox(
        "Ministry / Department", ministry_opts, index=0, key="bill_feed_ministry"
    )

    # Bill type filter
    categories = ["All"] + options.get("categories", [])
    selected_category = st.sidebar.selectbox(
        "Bill Type / Category", categories, index=0, key="bill_feed_category"
    )

    # Status filter
    statuses = ["All"] + options.get("statuses", [])
    selected_status = st.sidebar.selectbox(
        "Legislative Status", statuses, index=0, key="bill_feed_status"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Market & Risk Filters")

    # Sector filter
    sector_opts = ["All"] + options.get("sectors", [])
    selected_sector = st.sidebar.selectbox(
        "Sector", sector_opts, index=0, key="bill_feed_sector"
    )

    # Direction filter
    dir_opts = ["All", "POSITIVE", "NEGATIVE", "NEUTRAL"]
    selected_direction = st.sidebar.selectbox(
        "Impact Direction", dir_opts, index=0, key="bill_feed_direction"
    )

    # Risk category filter
    risk_opts = ["All"] + options.get("risk_categories", [])
    selected_risk = st.sidebar.selectbox(
        "Risk Category", risk_opts, index=0, key="bill_feed_risk"
    )

    # Anticipation filter
    ant_opts = [
        "All",
        "NO_EVIDENCE",
        "WEAK_EVIDENCE",
        "MODERATE_EVIDENCE",
        "STRONG_EVIDENCE",
        "NOT_ANALYZED",
    ]
    selected_ant = st.sidebar.selectbox(
        "Anticipation Evidence", ant_opts, index=0, key="bill_feed_anticipation"
    )

    return {
        "since": since,
        "until": until,
        "preset": preset,
        "house": None if selected_house == "All" else selected_house,
        "ministry": None if selected_ministry == "All" else selected_ministry,
        "category": None if selected_category == "All" else selected_category,
        "status": None if selected_status == "All" else selected_status,
        "sector": None if selected_sector == "All" else selected_sector,
        "direction": None if selected_direction == "All" else selected_direction,
        "risk_category": None if selected_risk == "All" else selected_risk,
        "anticipation": None if selected_ant == "All" else selected_ant,
    }


def apply_bill_summary_filters(
    summaries: list[Any],
    filters: dict[str, Any],
) -> list[Any]:
    """
    Apply filter criteria to a list of BillSummary objects.
    All filtering is deterministic and read-only.

    Parameters
    ----------
    summaries : list[BillSummary]
    filters : dict
        Output of render_bill_feed_filters()

    Returns
    -------
    Filtered list[BillSummary], sorted newest-first.
    """
    result = list(summaries)

    # Date range (already handled by service; apply again for safety)
    since = filters.get("since")
    until = filters.get("until")
    if since or until:
        filtered = []
        for s in result:
            if s.introduction_date is None:
                continue
            if since and s.introduction_date < since:
                continue
            if until and s.introduction_date > until:
                continue
            filtered.append(s)
        result = filtered

    # House filter
    house_filter = filters.get("house")
    if house_filter:
        result = [s for s in result if s.house == house_filter]

    # Ministry filter
    ministry_filter = filters.get("ministry")
    if ministry_filter:
        result = [s for s in result if s.ministry == ministry_filter]

    # Category filter
    cat_filter = filters.get("category")
    if cat_filter:
        result = [s for s in result if s.bill_category == cat_filter]

    # Status filter
    status_filter = filters.get("status")
    if status_filter:
        result = [s for s in result if s.status == status_filter]

    # Sector filter
    sector_filter = filters.get("sector")
    if sector_filter:
        result = [s for s in result if sector_filter in (s.sectors or [])]

    # Direction filter
    dir_filter = filters.get("direction")
    if dir_filter:
        result = [s for s in result if s.predicted_direction == dir_filter]

    # Risk category filter
    risk_filter = filters.get("risk_category")
    if risk_filter:
        result = [s for s in result if s.risk_category == risk_filter]

    # Anticipation filter
    ant_filter = filters.get("anticipation")
    if ant_filter:
        result = [s for s in result if s.anticipation_class == ant_filter]

    # Sort newest-first
    result.sort(
        key=lambda s: s.introduction_date or date(1900, 1, 1),
        reverse=True,
    )
    return result
