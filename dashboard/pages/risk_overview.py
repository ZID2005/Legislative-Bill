"""
dashboard/pages/risk_overview.py
================================
Risk Overview page displaying portfolio distributions, summary stats, and risk matrix.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts.distribution_charts import (
    create_anticipation_bar,
    create_direction_pie,
    create_impact_score_hist,
    create_market_moving_distribution,
    create_risk_category_bar,
)
from dashboard.charts.risk_matrix import create_risk_matrix
from dashboard.charts.sector_charts import create_sector_risk_comparison
from dashboard.components.disclaimer import render_general_disclaimer
from dashboard.services.data_service import DashboardDataService


def render_risk_overview(data_service: DashboardDataService, df: pd.DataFrame) -> None:
    """
    Render Risk Overview dashboard.
    """
    st.markdown("## ⚡ Quantitative Risk & Impact Overview")
    st.caption(
        "Comprehensive statistical distributions and risk matrix mapping across the active candidate universe."
    )

    if df.empty:
        st.warning("No records match the current filter criteria.")
        return

    # Summary Statistics Table
    st.markdown("### 📊 Descriptive Summary Statistics")

    stats_dict = {
        "Metric": ["Composite Risk Score (R)", "Directional Impact Score (I)", "P(Market-Moving)"],
        "Mean": [df["risk_score"].mean(), df["impact_score"].mean(), df["market_moving_probability"].mean()],
        "Median": [df["risk_score"].median(), df["impact_score"].median(), df["market_moving_probability"].median()],
        "Std Dev": [df["risk_score"].std(), df["impact_score"].std(), df["market_moving_probability"].std()],
        "Minimum": [df["risk_score"].min(), df["impact_score"].min(), df["market_moving_probability"].min()],
        "Maximum": [df["risk_score"].max(), df["impact_score"].max(), df["market_moving_probability"].max()],
    }
    stats_df = pd.DataFrame(stats_dict)
    st.dataframe(
        stats_df.style.format({
            "Mean": "{:.4f}",
            "Median": "{:.4f}",
            "Std Dev": "{:.4f}",
            "Minimum": "{:.4f}",
            "Maximum": "{:.4f}",
        }),
        use_container_width=True,
    )

    st.markdown("---")

    # 2D Risk Matrix
    st.markdown("### 🎯 Decision Risk Matrix")
    st.caption(
        "Maps Directional Impact Score against Composite Decision Risk Score. "
        "Quadrants distinguish high-conviction events from noise and extreme volatility."
    )
    st.plotly_chart(create_risk_matrix(df), use_container_width=True)

    st.markdown("---")

    # Distributions Grid
    st.markdown("### 📈 Core Score Distributions")
    r1, r2 = st.columns(2)
    with r1:
        st.plotly_chart(create_risk_category_bar(df), use_container_width=True)
    with r2:
        st.plotly_chart(create_impact_score_hist(df), use_container_width=True)

    r3, r4 = st.columns(2)
    with r3:
        st.plotly_chart(create_market_moving_distribution(df), use_container_width=True)
    with r4:
        st.plotly_chart(create_anticipation_bar(df), use_container_width=True)

    # Sector Comparison
    st.markdown("---")
    st.markdown("### 🏭 Sectoral Risk & Impact Comparison")
    st.plotly_chart(create_sector_risk_comparison(df), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    render_general_disclaimer()
