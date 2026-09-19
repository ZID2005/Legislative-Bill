"""
dashboard/app.py
================
Main application entry point for the Legislative Intelligence & Market Impact Dashboard.

Task 7.4.2: Integrated complete 10-page analytical architecture:
- 🏠 Overview & New Bills
- 📜 All Bills (Searchable / Filterable master table)
- 🔍 Bill Intelligence (Deep dive, timeline, affected companies, stakeholder views)
- 🏢 Company Intelligence (Comparative multi-company universe)
- 🏢 Company Detail (Per-company exposure & related bills)
- 📈 Market Impact Predictions (Aggregate distributions & Plotly charts)
- ⚠️ Risk Overview (Canonical risk tiers, 2D matrix, drilldowns)
- 🔍 Anticipation & Pricing-In (Diffusion analysis, Anticipation Paradox, non-insider language)
- 🔬 Historical Backtesting (Out-of-sample walk-forward performance vs benchmark)
- 📐 Methodology (18-stage academic blueprint)

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

# Task 7.4.2 Pages
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
from dashboard.pages.monitoring import render_monitoring_page  # Task 8.11

# Legacy Pages (Preserved for compatibility)
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

from dashboard.services.dashboard_service import DashboardService
from dashboard.services.data_service import DashboardDataService
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService


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


@st.cache_resource
def get_dashboard_service() -> DashboardService:
    """Instantiate and cache the Task 7.4.1/7.4.2 DashboardService."""
    return DashboardService()


@st.cache_resource
def get_unified_discovery_service() -> UnifiedLegislativeDiscoveryService:
    """Instantiate and cache the Task 8.9 UnifiedLegislativeDiscoveryService."""
    return UnifiedLegislativeDiscoveryService()


def main() -> None:
    """Main application orchestrator."""
    configure_page()
    data_service = get_data_service()
    dashboard_service = get_dashboard_service()
    unified_discovery_service = get_unified_discovery_service()

    # Sidebar Header
    st.sidebar.title("🏛️ LegisIntel India")
    st.sidebar.caption("Parliamentary Impact & Decision Platform")
    st.sidebar.markdown("---")

    # Global Bill Search in Sidebar (Central + State Multi-Jurisdiction)
    st.sidebar.markdown("### 🔎 Global Bill Search")
    global_search_q = st.sidebar.text_input(
        "Search all legislative bills:",
        placeholder="Title, bill #, ministry, sector, state…",
        key="global_bill_search_input",
    )

    if global_search_q and global_search_q.strip():
        search_hits = unified_discovery_service.search(global_search_q)
        if search_hits:
            st.sidebar.caption(f"Found **{len(search_hits)}** matching bills:")
            hit_titles = {
                h.bill_id: (
                    f"🏛️ [CENTRAL] {h.title[:24]}…" if h.is_central
                    else f"🇮🇳 [STATE: {h.state or 'State'}] {h.title[:20]}…"
                )
                for h in search_hits
            }
            sel_hit = st.sidebar.selectbox(
                "Select matching bill:",
                options=list(hit_titles.keys()),
                format_func=lambda x: hit_titles[x],
                key="global_search_hit_selector",
            )
            hit_rec = unified_discovery_service.get_bill_by_id(sel_hit)
            btn_label = "Go to Bill Intelligence" if (hit_rec and hit_rec.is_central) else "Go to State Dossier"
            if st.sidebar.button(btn_label, key="btn_go_search_bill"):
                if hit_rec and hit_rec.is_central:
                    st.session_state["selected_bill_id"] = sel_hit
                    st.session_state["nav_override"] = "🔍 Bill Intelligence"
                else:
                    st.session_state["selected_unified_state_bill_id"] = sel_hit
                    st.session_state["nav_override"] = "🏛️ India Legislative Explorer"
                st.rerun()
        else:
            st.sidebar.caption("No matching bills found.")

    st.sidebar.markdown("---")

    # Load master decision dataframe
    with st.spinner("Loading legislative decision repository..."):
        master_df = data_service.get_decision_dataframe()

    # Sidebar Navigation Menu
    nav_options = [
        "🏠 Overview & New Bills",
        "🏛️ India Legislative Explorer",
        "📜 All Bills",
        "🔍 Bill Intelligence",
        "🏢 Company Intelligence",
        "🏢 Company Detail",
        "📈 Market Impact Predictions",
        "⚠️ Risk Overview",
        "🔍 Anticipation & Pricing-In",
        "🔬 Historical Backtesting",
        "📐 Methodology",
        "🔭 Legislative Monitor",  # Task 8.11
        # Legacy / Sub-perspectives
        "🌐 Global Overview",
        "📜 Bill Explorer",
        "🏢 Company Explorer",
        "📈 Investor View",
        "💼 Business View",
        "🌍 Public View",
        "⚡ Risk Overview (Legacy)",
        "🛡️ Anticipation Overview",
        "🧠 Model Explainability",
        "📊 Backtesting Summary",
    ]

    # Handle navigation override from drilldowns
    default_nav_idx = 0
    nav_override = st.session_state.pop("nav_override", None)
    if nav_override and nav_override in nav_options:
        default_nav_idx = nav_options.index(nav_override)

    selected_page = st.sidebar.radio(
        "Navigation",
        nav_options,
        index=default_nav_idx,
        key="main_nav_radio",
    )
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
    if selected_page == "🏠 Overview & New Bills":
        render_overview_page(dashboard_service, filtered_df)
    elif selected_page == "🏛️ India Legislative Explorer":
        render_india_explorer_page(unified_discovery_service)
    elif selected_page == "📜 All Bills":
        render_bills_page(dashboard_service, filtered_df)
    elif selected_page == "🔍 Bill Intelligence":
        render_bill_detail_page(dashboard_service, filtered_df)
    elif selected_page == "🏢 Company Intelligence":
        render_companies_page(dashboard_service, filtered_df)
    elif selected_page == "🏢 Company Detail":
        render_company_detail_page(dashboard_service, filtered_df)
    elif selected_page == "📈 Market Impact Predictions":
        render_predictions_page(dashboard_service, filtered_df)
    elif selected_page == "⚠️ Risk Overview":
        render_risk_page(dashboard_service, filtered_df)
    elif selected_page == "🔍 Anticipation & Pricing-In":
        render_anticipation_page(dashboard_service, filtered_df)
    elif selected_page == "🔬 Historical Backtesting":
        render_backtesting_page(dashboard_service, filtered_df)
    elif selected_page == "📐 Methodology":
        render_methodology_page()
    elif selected_page == "🔭 Legislative Monitor":  # Task 8.11
        render_monitoring_page()
    # Legacy routing
    elif selected_page == "🌐 Global Overview":
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
    elif selected_page == "⚡ Risk Overview (Legacy)":
        render_risk_overview(data_service, filtered_df)
    elif selected_page == "🛡️ Anticipation Overview":
        render_anticipation_view(data_service, filtered_df)
    elif selected_page == "🧠 Model Explainability":
        render_explainability_view(data_service, filtered_df)
    elif selected_page == "📊 Backtesting Summary":
        render_backtest_view(data_service, filtered_df)


if __name__ == "__main__":
    main()
