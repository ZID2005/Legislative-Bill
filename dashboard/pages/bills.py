"""
dashboard/pages/bills.py
========================
Task 7.4.2 — All Bills master exploratory page.

Provides a comprehensive, searchable, filterable, and sortable legislative
table covering all 20 production Central Government legislative bills.

Columns:
- Bill (Title)
- Bill Number
- Introduction Date (Default sorted newest first)
- House
- Ministry / Department
- Bill Type (Categorical taxonomy)
- Status
- Affected Sectors
- Affected Companies
- Market Direction
- Market Moving
- Impact Strength
- Risk
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd
import streamlit as st

from dashboard.services.dashboard_service import DashboardService


def render_bills_page(
    service: DashboardService,
    master_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Render the '📜 All Bills' master legislative table page.
    """
    st.markdown(
        "<h1 style='margin-bottom:0;'>📜 All Bills</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#64748b;font-size:1.05rem;margin-top:4px;'>"
        "Master repository of official 2024 Central Government legislative bills with market-impact overlays.</p>",
        unsafe_allow_html=True,
    )

    # 1. Load data
    try:
        df = service.get_all_bills_table_data()
    except Exception as exc:
        st.error(f"Error loading bills table: {exc}")
        return

    if df.empty:
        st.info("No legislative bills found in repository.", icon="ℹ️")
        return

    # 2. Controls & Search Row
    c_search, c_sort, c_order = st.columns([3, 2, 1])

    with c_search:
        search_query = st.text_input(
            "🔍 Search Bills",
            placeholder="Search by title, number, ministry, sector, or category…",
            key="bills_page_search",
        )

    with c_sort:
        sort_col = st.selectbox(
            "Sort By",
            options=[
                "Introduction Date",
                "Bill",
                "Market Moving",
                "Affected Companies",
                "Ministry / Department",
                "Status",
            ],
            index=0,
            key="bills_page_sort_col",
        )

    with c_order:
        sort_asc = st.selectbox(
            "Order",
            options=["Descending", "Ascending"],
            index=0,
            key="bills_page_sort_order",
        ) == "Ascending"

    # 3. Filter expander
    with st.expander("Filter Legislative Universe", expanded=False):
        f1, f2, f3 = st.columns(3)
        with f1:
            houses = ["All"] + sorted([str(h) for h in df["House"].dropna().unique()])
            sel_house = st.selectbox("House", options=houses, index=0)
            
            statuses = ["All"] + sorted([str(s) for s in df["Status"].dropna().unique()])
            sel_status = st.selectbox("Status", options=statuses, index=0)

        with f2:
            ministries = ["All"] + sorted([str(m) for m in df["Ministry / Department"].dropna().unique()])
            sel_ministry = st.selectbox("Ministry", options=ministries, index=0)

            categories = ["All"] + sorted([str(c) for c in df["Bill Type"].dropna().unique()])
            sel_category = st.selectbox("Bill Type / Category", options=categories, index=0)

        with f3:
            directions = ["All"] + sorted([str(d) for d in df["Market Direction"].dropna().unique()])
            sel_direction = st.selectbox("Market Direction", options=directions, index=0)

            risks = ["All"] + sorted([str(r) for r in df["Risk"].dropna().unique()])
            sel_risk = st.selectbox("Risk Tier", options=risks, index=0)

    # 4. Apply Filters
    filtered_df = df.copy()

    if search_query and search_query.strip():
        q = search_query.strip().lower()
        mask = (
            filtered_df["Bill"].astype(str).str.lower().str.contains(q)
            | filtered_df["Bill Number"].astype(str).str.lower().str.contains(q)
            | filtered_df["Ministry / Department"].astype(str).str.lower().str.contains(q)
            | filtered_df["Bill Type"].astype(str).str.lower().str.contains(q)
            | filtered_df["Affected Sectors"].astype(str).str.lower().str.contains(q)
            | filtered_df["bill_id"].astype(str).str.lower().str.contains(q)
        )
        filtered_df = filtered_df[mask]

    if sel_house != "All":
        filtered_df = filtered_df[filtered_df["House"] == sel_house]
    if sel_status != "All":
        filtered_df = filtered_df[filtered_df["Status"] == sel_status]
    if sel_ministry != "All":
        filtered_df = filtered_df[filtered_df["Ministry / Department"] == sel_ministry]
    if sel_category != "All":
        filtered_df = filtered_df[filtered_df["Bill Type"] == sel_category]
    if sel_direction != "All":
        filtered_df = filtered_df[filtered_df["Market Direction"] == sel_direction]
    if sel_risk != "All":
        filtered_df = filtered_df[filtered_df["Risk"] == sel_risk]

    # 5. Apply Sorting
    if sort_col in filtered_df.columns:
        if sort_col == "Introduction Date":
            filtered_df["_sort_key"] = pd.to_datetime(filtered_df["Introduction Date"])
            filtered_df = filtered_df.sort_values(by="_sort_key", ascending=sort_asc, na_position="last").drop(columns=["_sort_key"])
        else:
            filtered_df = filtered_df.sort_values(by=sort_col, ascending=sort_asc)
        filtered_df = filtered_df.reset_index(drop=True)

    # Summary bar
    st.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** production legislative bills")

    # 6. Interactive Selector to drill into Bill Intelligence
    selected_bill_title = st.selectbox(
        "🔎 Select a Bill to Inspect in Detail:",
        options=filtered_df["Bill"].tolist(),
        index=0 if not filtered_df.empty else None,
        key="all_bills_selector",
    )

    if selected_bill_title:
        matched_row = filtered_df[filtered_df["Bill"] == selected_bill_title].iloc[0]
        col_act1, col_act2 = st.columns([1, 4])
        with col_act1:
            if st.button("🚀 Open Bill Intelligence", key="btn_open_bill_detail", type="primary"):
                st.session_state["selected_bill_id"] = matched_row["bill_id"]
                st.session_state["nav_override"] = "🔍 Bill Intelligence"
                st.rerun()
        with col_act2:
            st.info(
                f"Selected **{selected_bill_title}** ({matched_row['Bill Number']}) — "
                f"Direction: **{matched_row['Market Direction']}** | Risk: **{matched_row['Risk']}**"
            )

    st.markdown("---")

    # 7. Render display table with clean column names and formatted badges
    display_cols = [
        "Bill",
        "Bill Number",
        "Introduction Date",
        "House",
        "Ministry / Department",
        "Bill Type",
        "Status",
        "Affected Sectors",
        "Affected Companies",
        "Market Direction",
        "Market Moving",
        "Impact Strength",
        "Risk",
    ]

    available_cols = [c for c in display_cols if c in filtered_df.columns]
    table_to_show = filtered_df[available_cols].copy()

    # Format numeric values
    if "Market Moving" in table_to_show.columns:
        table_to_show["Market Moving"] = table_to_show["Market Moving"].apply(
            lambda x: f"{x:.1%}" if pd.notnull(x) else "0.0%"
        )

    st.dataframe(
        table_to_show,
        use_container_width=True,
        hide_index=True,
    )
