"""
dashboard/app.py
================
Main application entry point for the Legislative Intelligence & Market Impact Dashboard.

Executes as a Streamlit web application:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from dashboard.components.filter_sidebar import render_filter_sidebar
from dashboard.filters.filter_engine import FilterEngine
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
from dashboard.services.data_service import DashboardDataService


def configure_page() -> None:
    """Configure Streamlit app page layout and metadata."""
    st.set_page_config(
        page_title="Legislative Intelligence Dashboard",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


@st.cache_resource
def get_data_service() -> DashboardDataService:
    """Instantiate and cache the shared DashboardDataService."""
    return DashboardDataService()


def main() -> None:
    """Main application orchestrator."""
    configure_page()
    data_service = get_data_service()

    # Sidebar Header
    st.sidebar.title("🏛️ LegisIntel India")
    st.sidebar.caption("Parliamentary Impact & Decision Platform")
    st.sidebar.markdown("---")

    # Load master decision dataframe
    with st.spinner("Loading legislative decision repository..."):
        master_df = data_service.get_decision_dataframe()

    # Sidebar Navigation Menu
    nav_options = [
        "🌐 Global Overview",
        "📜 Bill Explorer",
        "🏢 Company Explorer",
        "📈 Investor View",
        "💼 Business View",
        "🌍 Public View",
        "⚡ Risk Overview",
        "🛡️ Anticipation Overview",
        "🧠 Model Explainability",
        "📊 Backtesting Summary",
        "📐 Methodology",
    ]

    selected_page = st.sidebar.radio("Navigation", nav_options, index=0)
    st.sidebar.markdown("---")

    # Sidebar Interactive Filters (applies across exploratory views)
    criteria = render_filter_sidebar(master_df)
    filtered_df = FilterEngine.apply_filters(
        df=master_df,
        bill_id=criteria["bill_id"],
        company_isin=criteria["company_isin"],
        sector=criteria["sector"],
        ministry=criteria["ministry"],
        risk_category=criteria["risk_category"],
        direction=criteria["direction"],
        market_moving_only=criteria["market_moving_only"],
        anticipation_category=criteria["anticipation_category"],
        event_window=criteria["event_window"],
    )

    # Active Filter Status Badge in Sidebar
    active_filters = [k for k, v in criteria.items() if v is not None]
    if active_filters:
        st.sidebar.info(f"Filtered: **{len(filtered_df):,}** of **{len(master_df):,}** records")
        if st.sidebar.button("Clear All Filters"):
            st.rerun()
    else:
        st.sidebar.caption(f"Universe: **{len(master_df):,}** decision records active")

    st.sidebar.markdown("---")
    st.sidebar.caption("Institutional Quantitative Decision System | v1.0")

    # Page Router
    if selected_page == "🌐 Global Overview":
        render_landing_page(data_service, filtered_df)
    elif selected_page == "📜 Bill Explorer":
        render_bill_explorer(data_service, filtered_df)
    elif selected_page == "🏢 Company Explorer":
        render_company_explorer(data_service, filtered_df)
    elif selected_page == "📈 Investor View":
        render_investor_view(data_service, filtered_df)
    elif selected_page == "💼 Business View":
        render_business_view(data_service, filtered_df)
    elif selected_page == "🌍 Public View":
        render_public_view(data_service, filtered_df)
    elif selected_page == "⚡ Risk Overview":
        render_risk_overview(data_service, filtered_df)
    elif selected_page == "🛡️ Anticipation Overview":
        render_anticipation_view(data_service, filtered_df)
    elif selected_page == "🧠 Model Explainability":
        render_explainability_view(data_service, filtered_df)
    elif selected_page == "📊 Backtesting Summary":
        render_backtest_view(data_service, filtered_df)
    elif selected_page == "📐 Methodology":
        render_methodology_view()


if __name__ == "__main__":
    main()
