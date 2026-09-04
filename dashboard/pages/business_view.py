"""
dashboard/pages/business_view.py
================================
Business View tailored for corporate strategy, regulatory compliance, and executive leadership.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.disclaimer import render_general_disclaimer
from dashboard.components.report_viewer import render_stakeholder_report
from dashboard.services.data_service import DashboardDataService


def render_business_view(data_service: DashboardDataService, df: pd.DataFrame) -> None:
    """
    Render Business Lens emphasizing operational, compliance, and regulatory exposures.
    """
    st.markdown("## 🏢 Business & Corporate Strategy View")
    st.caption(
        "Synthesizes parliamentary policy changes into operational compliance impacts, "
        "sectoral exposures, and ministerial regulatory risk."
    )

    if df.empty:
        st.warning("No records match the current filter selection.")
        return

    # Candidate selection
    st.markdown("### 📋 Executive Regulatory Assessment")
    col_b, col_c, col_w = st.columns(3)

    unique_bills = sorted(df["bill_id"].unique())
    selected_bill = col_b.selectbox("Select Legislation", unique_bills, key="bus_bill")

    sub_comps = sorted(df[df["bill_id"] == selected_bill]["company_isin"].unique())
    selected_comp = col_c.selectbox("Select Enterprise", sub_comps, key="bus_comp")

    sub_windows = sorted(
        df[(df["bill_id"] == selected_bill) & (df["company_isin"] == selected_comp)]["event_window"].unique()
    )
    selected_window = col_w.selectbox("Reaction Horizon", sub_windows, key="bus_window")

    cand_rows = df[
        (df["bill_id"] == selected_bill)
        & (df["company_isin"] == selected_comp)
        & (df["event_window"] == selected_window)
    ]

    if not cand_rows.empty:
        cand = cand_rows.iloc[0]
        bill_obj = data_service.get_bill_by_id(selected_bill)
        comp_obj = data_service.get_company_by_isin(selected_comp)

        st.markdown(
            f"#### Corporate Entity: **{cand.get('company_name', cand['company_isin'])}** "
            f"| Sector: **{cand.get('sector', 'Unspecified')}**"
        )

        b1, b2, b3, b4 = st.columns(4)
        b1.markdown(f"**Sponsoring Ministry:**<br>{cand.get('ministry', 'Unknown')}", unsafe_allow_html=True)
        b2.markdown(f"**Policy Domain:**<br>{cand.get('policy_domain', 'General')}", unsafe_allow_html=True)
        b3.markdown(f"**Exposure Level:**<br>{cand.get('risk_category', 'MODERATE')}", unsafe_allow_html=True)
        b4.markdown(f"**Pre-Event Awareness:**<br>{cand.get('anticipation_evidence', 'NO_EVIDENCE')}", unsafe_allow_html=True)

        # Strategic & operational pillars
        st.markdown("### 💼 Operational & Regulatory Implications")
        p1, p2 = st.columns(2)

        with p1:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 14px; border-radius: 6px;">
                    <h5 style="margin-top:0; color: #1E293B;">Compliance & Legal Mandates</h5>
                    <p style="font-size: 0.9em; color: #475569;">
                        New legislative clauses may require adjustments to standard operating procedures,
                        licensing renewals, audit disclosures, or reporting deadlines. Legal teams should
                        review statutory text for structural compliance shifts.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with p2:
            st.markdown(
                """
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 14px; border-radius: 6px;">
                    <h5 style="margin-top:0; color: #1E293B;">Commercial & Market Dynamics</h5>
                    <p style="font-size: 0.9em; color: #475569;">
                        Supply chain partners, procurement contracts, and competitive barriers may experience
                        asymmetric shocks. Strategic leadership should evaluate pricing flexibility and
                        sectoral capital expenditure commitments.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Integrated Task 7.3 Report
    st.markdown("---")
    st.markdown("### 📑 Official Task 7.3 Business & Enterprise Report")
    report = data_service.get_stakeholder_report(selected_bill, selected_comp, selected_window, "BUSINESS")
    render_stakeholder_report(report)

    st.markdown("<br>", unsafe_allow_html=True)
    render_general_disclaimer()
