"""
dashboard/pages/overview.py
============================
Task 7.4.1 — Dashboard Home / Overview page.

PRIMARY FEATURES:
  1. KPI summary cards (Total Bills, Companies, Predictions, etc.)
  2. 🆕 Newly Introduced Bills Feed — uses Bill.introduction_date exclusively
  3. Market impact summary statistics
  4. Company exposure table
  5. Scope diagnostic panel
  6. Research integrity disclaimer

RESEARCH INTEGRITY:
  - Bill introduction dates come exclusively from Bill.introduction_date
    (the authoritative parliamentary tabling date)
  - PDF download dates, file creation dates, and embedding timestamps
    are NEVER used to determine bill recency
  - Predictions and scores are read-only — not recalculated
  - Ground-truth labels are not displayed on this page
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import streamlit as st
import pandas as pd

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
from dashboard.components.filters import apply_bill_summary_filters, render_bill_feed_filters
from dashboard.components.tables import render_company_exposure_table
from dashboard.services.dashboard_service import DashboardService


# ---------------------------------------------------------------------------
# Disclaimer constants
# ---------------------------------------------------------------------------

_DISCLAIMER = """
> **Research Disclaimer:** This dashboard presents probabilistic research outputs from a 
> Legislative Market Impact Prediction System. Results are **not guaranteed financial returns** 
> and should not be interpreted as personalized investment advice.
>
> - **Predictions are probabilistic** — they express model-estimated likelihood, not certainty.
> - **Historical backtesting is separate** from forward prediction and uses walk-forward methodology.
> - **Anticipation analysis** represents potential pre-event information diffusion and pricing-in effects.
> - **Anticipation evidence is NOT proof of insider trading** — it reflects statistical market patterns.
> - **Future/post-event information is excluded** from all prediction model inputs.
"""

_ZERO_MOD_BANNER = """
<div style="background:#fef3c7;border:1px solid #d97706;border-radius:6px;
            padding:10px 14px;margin-bottom:16px;font-size:0.85rem;">
⚠️ <b>Read-Only Mode:</b> This dashboard reads pre-computed artifacts only.
No ML models, predictions, risk scores, anticipation scores, or backtesting
results have been modified or recalculated.
</div>
"""


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------


def render_overview_page(service: DashboardService, master_df: pd.DataFrame) -> None:
    """
    Render the dashboard overview / home page.

    Parameters
    ----------
    service : DashboardService
        The authoritative data access service.
    master_df : pd.DataFrame
        The pre-loaded, pre-filtered master decision DataFrame.
    """
    # --- Header ---
    st.markdown(
        "<h1 style='margin-bottom:0;'>🏛️ Legislative Intelligence Dashboard</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#64748b;font-size:1.05rem;margin-top:4px;'>"
        "Parliamentary Impact &amp; Market Decision Support Platform — India 2024</p>",
        unsafe_allow_html=True,
    )
    st.markdown(_ZERO_MOD_BANNER, unsafe_allow_html=True)

    # --- Scope verification ---
    with st.spinner("Loading production scope…"):
        scope = service.get_production_scope()

    # --- KPI Cards ---
    render_kpi_header(scope, master_df)
    st.markdown("---")

    # === NEWLY ARRIVED BILLS FEED ===
    _render_newly_arrived_bills_section(service)
    st.markdown("---")

    # === MARKET IMPACT SUMMARY ===
    _render_market_impact_section(service, master_df)
    st.markdown("---")

    # === COMPANY EXPOSURE TABLE ===
    _render_company_exposure_section(service, master_df)
    st.markdown("---")

    # === SCOPE DIAGNOSTICS ===
    with st.expander("🔬 Production Scope & Data Provenance", expanded=False):
        render_scope_diagnostic_card(scope)

    # === DISCLAIMER ===
    st.markdown("---")
    st.markdown("#### ⚠️ Important Disclaimers")
    st.markdown(_DISCLAIMER)


# ---------------------------------------------------------------------------
# Section: Newly Arrived Bills
# ---------------------------------------------------------------------------


def _render_newly_arrived_bills_section(service: DashboardService) -> None:
    """
    PRIMARY FEATURE: Render the Newly Introduced Bills feed.

    Uses Bill.introduction_date exclusively (authoritative legislative tabling date).
    Provides configurable date range filters.
    """
    st.markdown(
        "<h2 style='color:#1e40af;'>🆕 Newly Introduced Bills</h2>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Bills are identified by their **authoritative legislative introduction date** "
        "(the date formally tabled in Parliament). "
        "PDF download date, file creation date, and prediction generation date are never used."
    )

    # Sidebar filters for bill feed
    filters = render_bill_feed_filters(service)

    since = filters["since"]
    until = filters["until"]
    preset = filters["preset"]

    # Load bills in date range
    try:
        all_prod_summaries = service._get_all_bill_summaries()
    except Exception as exc:
        st.error(f"Could not load bill summaries: {exc}", icon="🚨")
        return

    # Apply date filter
    if preset == "All time":
        date_filtered = list(all_prod_summaries)
    else:
        date_filtered = [
            s for s in all_prod_summaries
            if s.introduction_date is not None
            and (since is None or s.introduction_date >= since)
            and (until is None or s.introduction_date <= until)
        ]

    # Apply remaining filters
    bill_summaries = apply_bill_summary_filters(date_filtered, filters)

    # Date range label
    since_str = since.strftime("%d %b %Y") if since else "all time"
    until_str = until.strftime("%d %b %Y") if until else "today"

    # Results count header
    col_count, col_mode = st.columns([3, 1])
    with col_count:
        st.markdown(
            f"**{len(bill_summaries)} bills** found  "
            f"(period: {since_str} → {until_str})"
        )
    with col_mode:
        view_mode = st.radio(
            "View",
            options=["Cards", "Table"],
            horizontal=True,
            key="bills_view_mode",
            label_visibility="collapsed",
        )

    if not bill_summaries:
        if preset == "All time":
            st.warning(
                "No production bills found. Check that the bill repository is correctly configured.",
                icon="⚠️",
            )
        else:
            render_no_bills_message(f"{since_str} → {until_str}")
        return

    # Show availability notice for bills without dates
    no_date_bills = [
        s for s in all_prod_summaries if s.introduction_date is None
    ]
    if no_date_bills and preset != "All time":
        with st.expander(
            f"ℹ️ {len(no_date_bills)} bills have no authoritative introduction date "
            f"(not shown in date-filtered view)"
        ):
            for s in no_date_bills:
                st.markdown(f"- {s.title} — {s.ministry}")

    # Render view
    if view_mode == "Table":
        from dashboard.components.tables import render_bills_summary_table
        render_bills_summary_table(bill_summaries)

    else:
        # Card view — show first 10, then offer expander for more
        INITIAL_DISPLAY = 5
        shown = bill_summaries[:INITIAL_DISPLAY]
        remaining = bill_summaries[INITIAL_DISPLAY:]

        for s in shown:
            render_bill_card(s, expanded=(len(shown) == 1))

        if remaining:
            with st.expander(
                f"▾ Show {len(remaining)} more bills…", expanded=False
            ):
                for s in remaining:
                    render_bill_mini_card(s)


# ---------------------------------------------------------------------------
# Section: Market Impact Summary
# ---------------------------------------------------------------------------


def _render_market_impact_section(
    service: DashboardService, df: pd.DataFrame
) -> None:
    """
    Render high-level market impact summary statistics from decision records.
    All values are read from stored pipeline outputs — no recalculation.
    """
    st.markdown("### 📊 Market Impact Overview *(read-only)*")
    st.caption(
        "Summary statistics from pre-computed decision-support records. "
        "Predictions, risk scores, and confidence values are not modified."
    )

    if not service.decisions_available:
        st.warning(
            "Decision-support data unavailable. "
            "Other legislative information remains available.",
            icon="⚠️",
        )
        return

    try:
        stats = service.get_market_impact_summary(df if not df.empty else None)
        render_market_impact_cards(stats)

        if stats["total_records"] > 0:
            _render_impact_charts(stats)

    except Exception as exc:
        st.warning(f"Market impact summary could not be loaded: {exc}", icon="⚠️")


def _render_impact_charts(stats: dict) -> None:
    """Render compact distribution charts for market impact."""
    try:
        import plotly.graph_objects as go

        col1, col2, col3 = st.columns(3)

        with col1:
            direction_dist = stats.get("direction_distribution", {})
            if direction_dist:
                labels = list(direction_dist.keys())
                values = list(direction_dist.values())
                colors = {"POSITIVE": "#22c55e", "NEGATIVE": "#ef4444", "NEUTRAL": "#94a3b8"}
                fig = go.Figure(
                    go.Pie(
                        labels=labels,
                        values=values,
                        marker_colors=[colors.get(l, "#94a3b8") for l in labels],
                        hole=0.4,
                    )
                )
                fig.update_layout(
                    title="Direction Distribution",
                    height=280,
                    showlegend=True,
                    margin=dict(t=40, b=20, l=10, r=10),
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            risk_dist = stats.get("risk_distribution", {})
            if risk_dist:
                order = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"]
                ordered_risk = {k: risk_dist.get(k, 0) for k in order if k in risk_dist}
                risk_colors = {
                    "VERY_LOW": "#22c55e",
                    "LOW": "#86efac",
                    "MODERATE": "#fbbf24",
                    "HIGH": "#f97316",
                    "VERY_HIGH": "#ef4444",
                }
                fig = go.Figure(
                    go.Bar(
                        x=list(ordered_risk.keys()),
                        y=list(ordered_risk.values()),
                        marker_color=[risk_colors.get(k, "#94a3b8") for k in ordered_risk],
                    )
                )
                fig.update_layout(
                    title="Risk Distribution",
                    height=280,
                    margin=dict(t=40, b=20, l=10, r=10),
                    xaxis_title="",
                    yaxis_title="Count",
                )
                st.plotly_chart(fig, use_container_width=True)

        with col3:
            ant_dist = stats.get("anticipation_distribution", {})
            if ant_dist:
                labels = {
                    "NO_EVIDENCE": "No Evidence",
                    "WEAK_EVIDENCE": "Weak",
                    "MODERATE_EVIDENCE": "Moderate",
                    "STRONG_EVIDENCE": "Strong",
                    "NOT_ANALYZED": "Not Analyzed",
                }
                ant_colors = {
                    "NO_EVIDENCE": "#22c55e",
                    "WEAK_EVIDENCE": "#86efac",
                    "MODERATE_EVIDENCE": "#fbbf24",
                    "STRONG_EVIDENCE": "#ef4444",
                    "NOT_ANALYZED": "#94a3b8",
                }
                fig = go.Figure(
                    go.Bar(
                        x=[labels.get(k, k) for k in ant_dist],
                        y=list(ant_dist.values()),
                        marker_color=[ant_colors.get(k, "#94a3b8") for k in ant_dist],
                    )
                )
                fig.update_layout(
                    title="Anticipation Evidence",
                    height=280,
                    margin=dict(t=40, b=20, l=10, r=10),
                    xaxis_title="",
                    yaxis_title="Count",
                )
                st.plotly_chart(fig, use_container_width=True)

    except ImportError:
        # Plotly not available — show raw stats
        st.json(stats)


# ---------------------------------------------------------------------------
# Section: Company Exposure
# ---------------------------------------------------------------------------


def _render_company_exposure_section(
    service: DashboardService, df: pd.DataFrame
) -> None:
    """
    Render the company exposure table with filtering and sorting.
    """
    st.markdown("### 🏢 Company Exposure")
    st.caption(
        "One row per (company, bill) pair for the [-10,+10] event window. "
        "Direction, impact, risk, and anticipation are read from stored pipeline outputs."
    )

    if not service.decisions_available:
        st.warning(
            "Company exposure data unavailable. Decision records could not be loaded.",
            icon="⚠️",
        )
        return

    try:
        exposure_df = service.get_company_exposure_table(
            df=df if not df.empty else None,
            event_window="[-10,+10]",
        )

        if exposure_df.empty:
            st.info("No company exposure data available for the current filters.", icon="ℹ️")
            return

        # Search control
        search = st.text_input(
            "🔍 Search companies or bills",
            placeholder="Type company name, ticker, or bill name…",
            key="company_exposure_search",
        )

        render_company_exposure_table(exposure_df, max_rows=300, search_term=search or None)

    except Exception as exc:
        st.warning(f"Company exposure table could not be loaded: {exc}", icon="⚠️")
