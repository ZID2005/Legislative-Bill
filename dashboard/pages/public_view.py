"""
dashboard/pages/public_view.py
==============================
Public View tailored for citizens, journalists, civil society, and policy researchers.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.components.disclaimer import render_general_disclaimer
from dashboard.components.report_viewer import render_stakeholder_report
from dashboard.services.data_service import DashboardDataService


def render_public_view(data_service: DashboardDataService, df: pd.DataFrame) -> None:
    """
    Render Public Lens explaining legislative intent and societal impacts in plain English.
    """
    st.markdown("## 🌍 Public Interest & Citizen View")
    st.caption(
        "Clear, accessible explanations of Parliamentary bills, societal significance, "
        "and broader economic ramifications in plain language."
    )

    if df.empty:
        st.warning("No records match the active filter criteria.")
        return

    # Select Bill
    bills = data_service.get_bills()
    bill_options = {b.bill_id: b.title for b in bills}
    selected_bill = st.selectbox(
        "Select Parliamentary Bill",
        options=list(bill_options.keys()),
        format_func=lambda x: bill_options.get(x, x),
        key="pub_bill",
    )

    bill_obj = data_service.get_bill_by_id(selected_bill)
    bill_df = df[df["bill_id"] == selected_bill] if not df.empty else pd.DataFrame()

    if bill_obj is not None:
        st.markdown(f"### 📖 {bill_obj.title}")
        st.markdown(
            f"**Sponsoring Ministry**: {bill_obj.ministry or 'Government of India'} | "
            f"**Introduced**: {bill_obj.introduction_date or '2024 Session'}"
        )

        st.markdown("---")

        q1, q2 = st.columns(2)
        with q1:
            st.markdown("#### 1. What does this bill do?")
            st.info(bill_obj.summary or "This legislation establishes updated statutory frameworks under central jurisdiction.")

            st.markdown("#### 2. Why does it matter?")
            st.write(
                "Parliamentary legislation alters national policy, governance guidelines, consumer safeguards, "
                "or regulatory requirements, influencing the economic climate and commercial conduct across India."
            )

        with q2:
            st.markdown("#### 3. Who is affected?")
            pol = getattr(bill_obj, "policy_domain", (bill_obj.sectors[0] if getattr(bill_obj, "sectors", None) else "General"))
            st.write(
                f"Primarily affects participants in the **{pol}** domain, "
                "including corporate enterprises, industry workforces, consumers, and public institutions."
            )

            st.markdown("#### 4. Pre-Event Market Awareness")
            st.write(
                "Our statistical analysis tracks whether financial markets anticipated this bill prior to its "
                "formal introduction, reflecting public information diffusion and healthy price discovery."
            )

    # Integrated Task 7.3 Public Report
    st.markdown("---")
    st.markdown("### 📑 Official Task 7.3 Public Interest Report")

    # Select sample candidate from this bill
    sub_comps = sorted(bill_df["company_isin"].unique()) if not bill_df.empty else []
    if sub_comps:
        c1, c2 = st.columns(2)
        comp_sel = c1.selectbox("Exemplar Company", sub_comps, key="pub_comp")
        sub_wins = sorted(bill_df[bill_df["company_isin"] == comp_sel]["event_window"].unique())
        win_sel = c2.selectbox("Event Window", sub_wins, key="pub_win")

        report = data_service.get_stakeholder_report(selected_bill, comp_sel, win_sel, "PUBLIC")
        render_stakeholder_report(report)
    else:
        st.info("No stakeholder report candidates available for this selection.")

    st.markdown("<br>", unsafe_allow_html=True)
    render_general_disclaimer()
