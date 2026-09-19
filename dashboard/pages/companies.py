"""
dashboard/pages/companies.py
============================
Task 7.4.2 — Company Intelligence master exploratory page.

Provides a multi-entity comparative analysis across all 47 mapped production
listed corporate entities:
- Company name, Ticker, Sector, Industry
- Number of associated legislative bills
- Directional breakdown (Positive, Negative, Neutral exposure counts)
- Market-moving exposure count
- Average impact score & Average risk score
- Strong anticipation exposure count
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd
import streamlit as st

from dashboard.services.dashboard_service import DashboardService


def render_companies_page(
    service: DashboardService,
    master_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Render the '🏢 Company Intelligence' comparative table and overview page.
    """
    st.markdown(
        "<h1 style='margin-bottom:0;'>🏢 Company Intelligence</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#64748b;font-size:1.05rem;margin-top:4px;'>"
        "Comparative corporate exposure universe across quantitative prediction and qualitative intelligence entities.</p>",
        unsafe_allow_html=True,
    )

    # 1. Load data
    try:
        df = service.get_all_companies_summary()
    except Exception as exc:
        st.error(f"Error loading company intelligence table: {exc}")
        return

    if df.empty:
        st.info("No company exposure data available in repository.", icon="ℹ️")
        return

    # 2. Controls & Search
    c_search, c_universe, c_sector, c_sort = st.columns([3, 1.8, 2, 2])

    with c_search:
        search_query = st.text_input(
            "🔍 Search Companies",
            placeholder="Search by company name, ticker, or industry…",
            key="companies_page_search",
        )

    with c_universe:
        univ_options = ["All Universes", "Quantitative (Models)", "Intelligence Universe"]
        sel_universe = st.selectbox("Universe Scope", options=univ_options, index=0, key="companies_page_universe")

    with c_sector:
        sectors = ["All"] + sorted([str(s) for s in df["Sector"].dropna().unique()])
        sel_sector = st.selectbox("Filter Sector", options=sectors, index=0, key="companies_page_sector")

    with c_sort:
        sort_col = st.selectbox(
            "Sort By",
            options=[
                "Associated Bills",
                "Market-Moving Bills",
                "Avg Impact Score",
                "Avg Risk Score",
                "Positive Exposure",
                "Negative Exposure",
                "Strong Anticipation Exposure",
                "Company Name",
            ],
            index=0,
            key="companies_page_sort_col",
        )

    # 3. Filter and Sort
    filtered_df = df.copy()

    if search_query and search_query.strip():
        q = search_query.strip().lower()
        mask = (
            filtered_df["Company Name"].astype(str).str.lower().str.contains(q)
            | filtered_df["Ticker"].astype(str).str.lower().str.contains(q)
            | filtered_df["Industry"].astype(str).str.lower().str.contains(q)
            | filtered_df["isin"].astype(str).str.lower().str.contains(q)
        )
        filtered_df = filtered_df[mask]

    if sel_universe == "Quantitative (Models)":
        filtered_df = filtered_df[filtered_df["Universe"] == "Quantitative"]
    elif sel_universe == "Intelligence Universe":
        filtered_df = filtered_df[filtered_df["Universe"] == "Intelligence"]

    if sel_sector != "All":
        filtered_df = filtered_df[filtered_df["Sector"] == sel_sector]

    if sort_col in filtered_df.columns:
        asc = sort_col == "Company Name"
        filtered_df = filtered_df.sort_values(by=sort_col, ascending=asc).reset_index(drop=True)

    # Summary metric cards
    quant_count = sum(1 for u in df.get("Universe", []) if u == "Quantitative")
    intel_count = sum(1 for u in df.get("Universe", []) if u == "Intelligence")

    st.markdown("### 📊 Active Universe Summary")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Mapped Entities", f"{len(df)} companies", delta=f"{quant_count} quant / {intel_count} intel")
    with k2:
        tot_bills = int(filtered_df["Associated Bills"].sum())
        st.metric("Total Bill Associations", f"{tot_bills:,} links")
    with k3:
        mm_total = int(filtered_df["Market-Moving Bills"].sum())
        st.metric("Market-Moving (Quant)", f"{mm_total:,} instances")
    with k4:
        strong_ant = int(filtered_df["Strong Anticipation Exposure"].sum())
        st.metric("Pre-Event Diffusion", f"{strong_ant} instances")

    st.markdown("---")

    # 4. Selection & Drilldown
    st.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** entities in company intelligence universe")

    selected_comp_name = st.selectbox(
        "🔎 Select a Company to Inspect Details & Exposure:",
        options=filtered_df["Company Name"].tolist(),
        index=0 if not filtered_df.empty else None,
        key="all_companies_selector",
    )

    if selected_comp_name:
        matched = filtered_df[filtered_df["Company Name"] == selected_comp_name].iloc[0]
        act_col1, act_col2 = st.columns([1, 4])
        with act_col1:
            if st.button("🚀 Open Company Detail", key="btn_open_company_detail", type="primary"):
                st.session_state["selected_company_isin"] = matched["isin"]
                st.session_state["nav_override"] = "🏢 Company Detail"
                st.rerun()
        with act_col2:
            st.info(
                f"Selected **{selected_comp_name}** ({matched['Ticker'] or matched['isin']}) — "
                f"Universe: **{matched.get('Universe', 'N/A')}** | "
                f"Sector: **{matched['Sector']}** | Associated Bills: **{matched['Associated Bills']}**"
            )

    st.markdown("---")

    # 5. Display Table
    cols_to_display = [
        "Company Name",
        "Ticker",
        "Universe",
        "Entity Type",
        "Sector",
        "Industry",
        "Associated Bills",
        "Positive Exposure",
        "Negative Exposure",
        "Neutral Exposure",
        "Market-Moving Bills",
        "Avg Impact Score",
        "Avg Risk Score",
        "Strong Anticipation Exposure",
    ]

    available = [c for c in cols_to_display if c in filtered_df.columns]
    st.dataframe(
        filtered_df[available],
        use_container_width=True,
        hide_index=True,
    )
