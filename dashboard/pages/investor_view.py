"""
dashboard/pages/investor_view.py
================================
Investor View tailored for portfolio managers and quantitative research analysts.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.disclaimer import render_general_disclaimer
from dashboard.components.report_viewer import render_stakeholder_report
from dashboard.services.data_service import DashboardDataService
from dashboard.utils.formatting import get_direction_badge, get_risk_badge


def render_investor_view(data_service: DashboardDataService, df: pd.DataFrame) -> None:
    """
    Render Investor Lens with compliant probabilistic quantitative research framing.
    """
    st.markdown("## 📈 Investor View")
    st.caption(
        "Institutional quantitative decision intelligence. Formulated with calibrated probabilistic "
        "evidence and zero illicit trading terminology."
    )

    # Compliance callout
    st.info(
        "ℹ️ **Investor Research Framework**: Evaluates directional probabilities, market-moving likelihood, "
        "pricing-in front-running discounts, and historical event-study robustness. "
        "Strictly probabilistic; non-advisory."
    )

    if df.empty:
        st.warning("No records match the current active filter criteria.")
        return

    # Filter down to single candidate selector
    st.markdown("### 🎯 Candidate Inspection")
    col_b, col_c, col_w = st.columns(3)

    unique_bills = sorted(df["bill_id"].unique())
    selected_bill = col_b.selectbox("Select Bill", unique_bills, key="inv_bill")

    sub_comps = sorted(df[df["bill_id"] == selected_bill]["company_isin"].unique())
    selected_comp = col_c.selectbox("Select Company ISIN", sub_comps, key="inv_comp")

    sub_windows = sorted(
        df[(df["bill_id"] == selected_bill) & (df["company_isin"] == selected_comp)]["event_window"].unique()
    )
    selected_window = col_w.selectbox("Event Window", sub_windows, key="inv_window")

    # Selected candidate metrics
    cand_rows = df[
        (df["bill_id"] == selected_bill)
        & (df["company_isin"] == selected_comp)
        & (df["event_window"] == selected_window)
    ]

    if not cand_rows.empty:
        cand = cand_rows.iloc[0]

        st.markdown(
            f"#### Assessment: **{cand.get('company_name', cand['company_isin'])}** ({cand.get('ticker', '')}) "
            f"— *{cand.get('bill_title', cand['bill_id'])}* [`{cand['event_window']}`]"
        )

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.markdown(f"**Direction:**<br>{get_direction_badge(cand['predicted_direction'])}", unsafe_allow_html=True)
        m2.metric("P(Market-Moving)", f"{cand['market_moving_probability']:.3f}")
        m3.metric("Impact Score", f"{cand['impact_score']:.4f}")
        m4.markdown(f"**Risk Category:**<br>{get_risk_badge(cand['risk_category'])}", unsafe_allow_html=True)
        m5.metric("Confidence", f"{cand['confidence']}")

        # Quantitative narrative interpretation
        st.markdown("### 📝 Calibrated Research Interpretation")

        dir_narrative = (
            "Model indicates a potential positive impact on firm valuations."
            if cand["predicted_direction"] == "POSITIVE"
            else (
                "Model indicates a potential negative or adverse market reaction."
                if cand["predicted_direction"] == "NEGATIVE"
                else "Model indicates a neutral or subdued market reaction within historical variances."
            )
        )

        mm_narrative = (
            "Model assigns an elevated probability that the event may be market-moving (P >= 0.50)."
            if cand["market_moving_probability"] >= 0.50
            else "Model assigns a low probability of an extreme, tail-moving market shock."
        )

        pricing_narrative = (
            f"Pricing-in risk assessment: **{cand['pricing_in_risk']}**. "
            f"Pre-event market diagnostics indicate **{cand['anticipation_evidence']}**, "
            f"discounting the net post-event impact score accordingly."
        )

        st.markdown(
            f"""
            <div style="background: #F0FDF4; border-left: 4px solid #10B981; padding: 14px; border-radius: 4px; margin-bottom: 12px;">
                <p style="margin: 0 0 6px 0; font-weight: 600; color: #065F46;">Directional Assessment</p>
                <p style="margin: 0; color: #047857;">{dir_narrative}</p>
            </div>
            <div style="background: #F5F3FF; border-left: 4px solid #8B5CF6; padding: 14px; border-radius: 4px; margin-bottom: 12px;">
                <p style="margin: 0 0 6px 0; font-weight: 600; color: #5B21B6;">Market-Moving Likelihood</p>
                <p style="margin: 0; color: #6D28D9;">{mm_narrative}</p>
            </div>
            <div style="background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 14px; border-radius: 4px; margin-bottom: 12px;">
                <p style="margin: 0 0 6px 0; font-weight: 600; color: #92400E;">Information Diffusion & Pricing-In</p>
                <p style="margin: 0; color: #B45309;">{pricing_narrative}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Integrated Task 7.3 Report
    st.markdown("---")
    st.markdown("### 📑 Official Task 7.3 Investor Report")
    report = data_service.get_stakeholder_report(selected_bill, selected_comp, selected_window, "INVESTOR")
    render_stakeholder_report(report)

    st.markdown("<br>", unsafe_allow_html=True)
    render_general_disclaimer()
