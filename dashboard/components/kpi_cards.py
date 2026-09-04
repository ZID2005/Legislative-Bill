"""
dashboard/components/kpi_cards.py
=================================
KPI metric summary cards for the Decision-Support Dashboard.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_kpi_cards(df: pd.DataFrame, total_bills: int = 20, total_companies: int = 47) -> None:
    """
    Render horizontal row of key performance indicator cards.
    """
    col1, col2, col3, col4, col5 = st.columns(5)

    n_records = len(df)
    n_bills = df["bill_id"].nunique() if not df.empty else 0
    n_companies = df["company_isin"].nunique() if not df.empty else 0
    avg_impact = df["impact_score"].mean() if not df.empty else 0.0
    avg_risk = df["risk_score"].mean() if not df.empty else 0.0

    with col1:
        st.metric(
            label="Active Bills",
            value=f"{n_bills}",
            delta=f"of {total_bills} Total" if n_bills != total_bills else "100% Scope",
        )

    with col2:
        st.metric(
            label="Active Companies",
            value=f"{n_companies}",
            delta=f"of {total_companies} Total" if n_companies != total_companies else "100% Scope",
        )

    with col3:
        st.metric(
            label="Decision Records",
            value=f"{n_records:,}",
            delta="4,700 Full Universe",
        )

    with col4:
        st.metric(
            label="Mean Impact Score",
            value=f"{avg_impact:.4f}",
            delta="Scale: 0.0 → 1.0",
        )

    with col5:
        st.metric(
            label="Mean Risk Score",
            value=f"{avg_risk:.4f}",
            delta="Scale: 0.0 → 1.0",
        )
