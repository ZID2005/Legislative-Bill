"""
dashboard/components/filter_sidebar.py
======================================
Interactive sidebar controls for multi-dimensional filtering.
"""

from __future__ import annotations

from typing import Any
import pandas as pd
import streamlit as st

from dashboard.filters.filter_engine import FilterEngine


def render_filter_sidebar(df: pd.DataFrame) -> dict[str, Any]:
    """
    Render sidebar filter widgets and return selected criteria.
    """
    st.sidebar.markdown("### 🔍 Global Filters")

    options = FilterEngine.get_filter_options(df)

    # 1. Bill filter
    bill_opts = ["All"] + options["bills"]
    selected_bill = st.sidebar.selectbox("Select Bill", options=bill_opts, index=0)

    # 2. Company filter
    comp_opts = ["All"] + options["companies"]
    selected_company = st.sidebar.selectbox("Select Company ISIN", options=comp_opts, index=0)

    # 3. Sector filter
    sector_opts = ["All"] + options["sectors"]
    selected_sector = st.sidebar.selectbox("Sector", options=sector_opts, index=0)

    # 4. Event Window filter
    window_opts = ["All"] + options["event_windows"]
    selected_window = st.sidebar.selectbox("Event Window", options=window_opts, index=0)

    with st.sidebar.expander("⚙️ Advanced Filters", expanded=False):
        # 5. Ministry filter
        ministry_opts = ["All"] + options["ministries"]
        selected_ministry = st.selectbox("Ministry", options=ministry_opts, index=0)

        # 6. Risk Category
        risk_opts = ["All"] + options["risk_categories"]
        selected_risk = st.selectbox("Risk Category", options=risk_opts, index=0)

        # 7. Direction
        dir_opts = ["All"] + options["directions"]
        selected_dir = st.selectbox("Predicted Direction", options=dir_opts, index=0)

        # 8. Anticipation Tier
        anticip_opts = ["All"] + options["anticipation_tiers"]
        selected_anticip = st.selectbox("Anticipation Level", options=anticip_opts, index=0)

        # 9. Market-Moving Only toggle
        mm_choice = st.radio("Market-Moving Only", options=["All", "Yes (P >= 0.50)", "No (P < 0.50)"], index=0)
        market_moving_only = True if mm_choice == "Yes (P >= 0.50)" else (False if mm_choice == "No (P < 0.50)" else None)

    return {
        "bill_id": None if selected_bill == "All" else selected_bill,
        "company_isin": None if selected_company == "All" else selected_company,
        "sector": None if selected_sector == "All" else selected_sector,
        "event_window": None if selected_window == "All" else selected_window,
        "ministry": None if selected_ministry == "All" else selected_ministry,
        "risk_category": None if selected_risk == "All" else selected_risk,
        "direction": None if selected_dir == "All" else selected_dir,
        "anticipation_category": None if selected_anticip == "All" else selected_anticip,
        "market_moving_only": market_moving_only,
    }
