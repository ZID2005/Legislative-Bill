"""
dashboard/pages/bill_explorer.py
================================
Bill Explorer page for browsing bills, provisions, and aggregated market impacts.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts.distribution_charts import (
    create_anticipation_bar,
    create_direction_pie,
    create_impact_score_hist,
    create_risk_category_bar,
)
from dashboard.components.report_viewer import render_bill_report
from dashboard.services.data_service import DashboardDataService
from dashboard.utils.export import to_csv_bytes


def render_bill_explorer(data_service: DashboardDataService, df: pd.DataFrame) -> None:
    """
    Render Bill Explorer view.
    """
    st.markdown("## 📜 Bill Explorer")
    st.caption("Deep-dive into Parliamentary legislation, regulatory scope, and aggregated decision intelligence.")

    bills = data_service.get_bills()
    if not bills:
        st.warning("No bills found in the repository.")
        return

    # Bill selector
    bill_options = {b.bill_id: f"{b.title} ({b.bill_id})" for b in bills}
    selected_bill_id = st.selectbox(
        "Select Legislative Bill to Inspect",
        options=list(bill_options.keys()),
        format_func=lambda x: bill_options.get(x, x),
    )

    selected_bill = data_service.get_bill_by_id(selected_bill_id)
    if selected_bill is None:
        st.error("Selected bill record could not be loaded.")
        return

    # Filter dataframe for this bill
    bill_df = df[df["bill_id"] == selected_bill_id] if not df.empty else pd.DataFrame()

    # Metadata dossier
    with st.container():
        st.markdown(f"### {selected_bill.title}")
        pol_domain = getattr(selected_bill, "policy_domain", (selected_bill.sectors[0] if getattr(selected_bill, "sectors", None) else "General"))
        bill_type = getattr(selected_bill, "bill_type", getattr(selected_bill, "house", "Government"))
        intro_date = getattr(selected_bill, "introduction_date", "N/A")

        col1, col2, col3, col4 = st.columns(4)
        col1.markdown(f"**Ministry:**<br>{selected_bill.ministry or 'Not Specified'}", unsafe_allow_html=True)
        col2.markdown(f"**Policy Domain:**<br>{pol_domain}", unsafe_allow_html=True)
        col3.markdown(f"**Introduction Date:**<br>{intro_date}", unsafe_allow_html=True)
        col4.markdown(f"**Bill Type:**<br>{bill_type}", unsafe_allow_html=True)

        if selected_bill.summary:
            st.markdown("#### Legislative Summary")
            st.info(selected_bill.summary)

    st.markdown("---")

    # Aggregated Decision Support Metrics
    st.markdown("### 📊 Aggregated Decision Intelligence")

    if bill_df.empty:
        st.warning("No decision records found for this bill in the active filtered view.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        avg_imp = bill_df["impact_score"].mean()
        avg_rsk = bill_df["risk_score"].mean()
        mm_count = (bill_df["market_moving_probability"] >= 0.50).sum()
        tot_comps = bill_df["company_isin"].nunique()

        m1.metric("Evaluated Companies", f"{tot_comps}")
        m2.metric("Mean Impact Score", f"{avg_imp:.4f}")
        m3.metric("Mean Risk Score", f"{avg_rsk:.4f}")
        m4.metric("Market-Moving Observations", f"{mm_count} / {len(bill_df)}")

        # Charts row
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(create_direction_pie(bill_df), use_container_width=True)
        with c2:
            st.plotly_chart(create_risk_category_bar(bill_df), use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            st.plotly_chart(create_impact_score_hist(bill_df), use_container_width=True)
        with c4:
            st.plotly_chart(create_anticipation_bar(bill_df), use_container_width=True)

        # Table of Affected Companies
        st.markdown("### 🏢 Affected Companies Table")
        disp_cols = [
            "company_name", "ticker", "sector", "industry", "event_window",
            "predicted_direction", "market_moving_probability",
            "impact_score", "risk_score", "risk_category", "confidence", "anticipation_evidence"
        ]
        available_cols = [c for c in disp_cols if c in bill_df.columns]
        st.dataframe(bill_df[available_cols], use_container_width=True)

        st.download_button(
            label="⬇️ Export Bill Candidate Decisions (CSV)",
            data=to_csv_bytes(bill_df[available_cols]),
            file_name=f"decisions_{selected_bill_id}.csv",
            mime="text/csv",
        )

    # Integrated Task 7.3 Bill Report
    st.markdown("---")
    st.markdown("### 📑 Official Task 7.3 Bill-Level Aggregation Report")
    bill_report = data_service.get_bill_report(selected_bill_id)
    render_bill_report(bill_report)
