"""
dashboard/pages/company_explorer.py
===================================
Company Explorer page for browsing company legislative exposures and risk scores.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts.distribution_charts import (
    create_anticipation_bar,
    create_direction_pie,
    create_risk_category_bar,
)
from dashboard.components.report_viewer import render_company_report
from dashboard.services.data_service import DashboardDataService
from dashboard.utils.export import to_csv_bytes


def render_company_explorer(data_service: DashboardDataService, df: pd.DataFrame) -> None:
    """
    Render Company Explorer view.
    """
    st.markdown("## 🏢 Company Explorer")
    st.caption("Examine company-specific legislative risk exposures, impact distributions, and stakeholder interpretations.")

    companies = data_service.get_companies()
    if not companies:
        st.warning("No company records found in the repository.")
        return

    # Selector
    comp_options = {
        c.isin: f"{c.company_name} ({getattr(c, 'ticker_nse', getattr(c, 'ticker', c.isin))}) — {c.sector}"
        for c in companies
    }
    selected_isin = st.selectbox(
        "Select Company to Inspect",
        options=list(comp_options.keys()),
        format_func=lambda x: comp_options.get(x, x),
    )

    company = data_service.get_company_by_isin(selected_isin)
    if company is None:
        st.error("Selected company record could not be loaded.")
        return

    # Filter decisions for this company
    comp_df = df[df["company_isin"] == selected_isin] if not df.empty else pd.DataFrame()

    # Company Dossier
    with st.container():
        st.markdown(f"### {company.company_name}")
        t_sym = getattr(company, "ticker_nse", getattr(company, "ticker", "N/A"))
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**ISIN:**<br>`{company.isin}`", unsafe_allow_html=True)
        c2.markdown(f"**Ticker / Exchange:**<br>{t_sym} (NSE)", unsafe_allow_html=True)
        c3.markdown(f"**Sector:**<br>{company.sector or 'Unspecified'}", unsafe_allow_html=True)
        c4.markdown(f"**Industry:**<br>{getattr(company, 'industry', 'Unspecified')}", unsafe_allow_html=True)

    st.markdown("---")

    # Decision metrics across bills
    st.markdown("### 📊 Legislative Exposures & Predictions")

    if comp_df.empty:
        st.warning("No decision records found for this company in the active filtered dataset.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        n_bills = comp_df["bill_id"].nunique()
        avg_imp = comp_df["impact_score"].mean()
        avg_rsk = comp_df["risk_score"].mean()
        mm_count = (comp_df["market_moving_probability"] >= 0.50).sum()

        m1.metric("Exposed Bills", f"{n_bills}")
        m2.metric("Mean Impact Score", f"{avg_imp:.4f}")
        m3.metric("Mean Risk Score", f"{avg_rsk:.4f}")
        m4.metric("Market-Moving Signals", f"{mm_count} / {len(comp_df)}")

        # Visualizations
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(create_direction_pie(comp_df), use_container_width=True)
        with c2:
            st.plotly_chart(create_risk_category_bar(comp_df), use_container_width=True)

        # Tabular breakdown
        st.markdown("### 📜 Relevant Bills & Impact Records")
        disp_cols = [
            "bill_id", "bill_title", "event_window", "predicted_direction",
            "market_moving_probability", "impact_score", "risk_score",
            "risk_category", "confidence", "anticipation_evidence"
        ]
        available_cols = [c for c in disp_cols if c in comp_df.columns]
        st.dataframe(comp_df[available_cols], use_container_width=True)

        st.download_button(
            label="⬇️ Export Company Decisions (CSV)",
            data=to_csv_bytes(comp_df[available_cols]),
            file_name=f"decisions_{selected_isin}.csv",
            mime="text/csv",
        )

    # Integrated Task 7.3 Company Report
    st.markdown("---")
    st.markdown("### 📑 Official Task 7.3 Company-Level Aggregation Report")
    comp_report = data_service.get_company_report(selected_isin)
    render_company_report(comp_report)
