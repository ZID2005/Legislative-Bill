"""
dashboard/pages/anticipation_view.py
===================================
Anticipation & Pre-Event Information Diffusion View.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts.distribution_charts import create_anticipation_bar
from dashboard.components.disclaimer import (
    render_anticipation_disclaimer,
    render_general_disclaimer,
)
from dashboard.services.data_service import DashboardDataService
from dashboard.utils.formatting import get_anticipation_badge


def render_anticipation_view(data_service: DashboardDataService, df: pd.DataFrame) -> None:
    """
    Render Anticipation & Pricing-In intelligence view.
    """
    st.markdown("## 🛡️ Pre-Event Market Anticipation & Pricing-In")
    st.caption(
        "Audits pre-event volume and return dynamics to identify whether legislative information "
        "diffused into markets prior to formal parliamentary introduction."
    )

    # Mandatory Legal Notice
    render_anticipation_disclaimer()

    st.markdown("---")

    # Tier Definitions
    st.markdown("### 🏷️ Anticipation Evidence Hierarchy")
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.markdown(
            """
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; padding: 12px; border-radius: 6px;">
                <h5 style="color: #15803D; margin-top:0;">NO_EVIDENCE</h5>
                <p style="font-size: 0.85em; color: #166534;">
                    Normal volume & return variance prior to event. Zero statistical drift. Full post-event reaction expected.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with t2:
        st.markdown(
            """
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; padding: 12px; border-radius: 6px;">
                <h5 style="color: #1D4ED8; margin-top:0;">WEAK_EVIDENCE</h5>
                <p style="font-size: 0.85em; color: #1E40AF;">
                    Mild pre-event abnormal activity; marginal price discovery. Impact score discounted modestly (5%).
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with t3:
        st.markdown(
            """
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; padding: 12px; border-radius: 6px;">
                <h5 style="color: #B45309; margin-top:0;">MODERATE_EVIDENCE</h5>
                <p style="font-size: 0.85em; color: #92400E;">
                    Observable cumulative abnormal return run-up or elevated volume. 15% pricing-in discount applied.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with t4:
        st.markdown(
            """
            <div style="background: #FEF2F2; border: 1px solid #FECACA; padding: 12px; border-radius: 6px;">
                <h5 style="color: #B91C1C; margin-top:0;">STRONG_EVIDENCE</h5>
                <p style="font-size: 0.85em; color: #991B1B;">
                    Pronounced pre-event drift. Significant likelihood the event is heavily priced in. 30% discount applied.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    if not df.empty:
        # Chart
        st.markdown("### 📊 Universe Anticipation Breakdown")
        st.plotly_chart(create_anticipation_bar(df), use_container_width=True)

        # Candidate Listing by Anticipation
        st.markdown("### 🔍 Filter by Evidence Tier")
        sel_tier = st.selectbox(
            "Evidence Tier",
            options=["All", "STRONG_EVIDENCE", "MODERATE_EVIDENCE", "WEAK_EVIDENCE", "NO_EVIDENCE"],
        )
        sub_df = df if sel_tier == "All" else df[df["anticipation_evidence"] == sel_tier]

        st.markdown(f"**Showing {len(sub_df):,} candidates**")
        disp_cols = [
            "bill_id", "company_name", "sector", "event_window",
            "anticipation_evidence", "pricing_in_risk", "impact_score", "risk_score"
        ]
        available_cols = [c for c in disp_cols if c in sub_df.columns]
        st.dataframe(sub_df[available_cols], use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    render_general_disclaimer()
