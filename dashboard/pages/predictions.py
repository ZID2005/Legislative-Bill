"""
dashboard/pages/predictions.py
==============================
Task 7.4.2 — Market Impact Predictions page.

Provides aggregate views and empirical distributions across:
- Direction (Positive, Negative, Neutral)
- Market-Moving Likelihood (P >= 0.50 vs P < 0.50)
- Impact Strength (Low, Medium, High, Very High)
- Model Confidence (Low, Medium, High)

Interactive Plotly visualizations and multi-dimensional filtering.
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from dashboard.components.ai_explanation_panel import get_ai_service
from dashboard.services.dashboard_service import DashboardService


def render_predictions_page(
    service: DashboardService,
    master_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Render the '📈 Market Impact Predictions' analytical page.
    """
    st.markdown(
        "<h1 style='margin-bottom:0;'>📈 Market Impact Predictions</h1>",
        unsafe_allow_html=True,
    )
    st.caption("Quantitative distribution of forward-looking predictions generated from pre-event legislative embeddings.")

    # 1. Load dataframe
    df = master_df if (master_df is not None and not master_df.empty) else service.get_decision_dataframe()

    if df.empty:
        st.warning("No prediction or decision records available to display.")
        return

    # 2. Multi-dimensional Filters
    with st.expander("🔍 Filter Predictions Dataset", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            bill_opts = ["All"] + sorted([str(b) for b in df["bill_title"].dropna().unique()])
            sel_bill = st.selectbox("Filter Bill", options=bill_opts, index=0)

            dir_opts = ["All"] + sorted([str(d) for d in df["predicted_direction"].dropna().unique()])
            sel_dir = st.selectbox("Predicted Direction", options=dir_opts, index=0)

        with c2:
            sec_opts = ["All"] + sorted([str(s) for s in df["sector"].dropna().unique()])
            sel_sec = st.selectbox("Sector", options=sec_opts, index=0)

            imp_opts = ["All"] + sorted([str(i) for i in df["impact_strength"].dropna().unique()])
            sel_imp = st.selectbox("Impact Strength", options=imp_opts, index=0)

        with c3:
            risk_opts = ["All"] + sorted([str(r) for r in df["risk_category"].dropna().unique()])
            sel_risk = st.selectbox("Risk Category", options=risk_opts, index=0)

            mm_choice = st.selectbox("Market Moving", options=["All", "Market-Moving Only (P >= 0.5)", "Subdued (P < 0.5)"], index=0)

    # Apply filters
    filtered_df = df.copy()
    if sel_bill != "All":
        filtered_df = filtered_df[filtered_df["bill_title"] == sel_bill]
    if sel_dir != "All":
        filtered_df = filtered_df[filtered_df["predicted_direction"] == sel_dir]
    if sel_sec != "All":
        filtered_df = filtered_df[filtered_df["sector"] == sel_sec]
    if sel_imp != "All":
        filtered_df = filtered_df[filtered_df["impact_strength"] == sel_imp]
    if sel_risk != "All":
        filtered_df = filtered_df[filtered_df["risk_category"] == sel_risk]
    if mm_choice == "Market-Moving Only (P >= 0.5)":
        filtered_df = filtered_df[filtered_df["market_moving_probability"] >= 0.50]
    elif mm_choice == "Subdued (P < 0.5)":
        filtered_df = filtered_df[filtered_df["market_moving_probability"] < 0.50]

    # 3. KPI Header Cards
    st.markdown("### 📊 Aggregate Summary Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)
    tot = len(filtered_df)
    pos_cnt = int((filtered_df["predicted_direction"] == "POSITIVE").sum())
    neg_cnt = int((filtered_df["predicted_direction"] == "NEGATIVE").sum())
    neut_cnt = int((filtered_df["predicted_direction"] == "NEUTRAL").sum())
    mm_cnt = int((filtered_df["market_moving_probability"] >= 0.50).sum())

    with m1:
        st.metric("Total Records", f"{tot:,}")
    with m2:
        st.metric("Positive Forecasts", f"{pos_cnt:,}", delta=f"{pos_cnt/tot:.1%}" if tot > 0 else "0%")
    with m3:
        st.metric("Neutral Forecasts", f"{neut_cnt:,}", delta=f"{neut_cnt/tot:.1%}" if tot > 0 else "0%")
    with m4:
        st.metric("Negative Forecasts", f"{neg_cnt:,}", delta=f"{neg_cnt/tot:.1%}" if tot > 0 else "0%", delta_color="inverse")
    with m5:
        st.metric("Market-Moving", f"{mm_cnt:,}", delta=f"{mm_cnt/tot:.1%}" if tot > 0 else "0%")

    st.markdown("---")

    # 4. Charts: 2x2 Grid
    st.markdown("### 📉 Empirical Prediction Distributions")
    if HAS_PLOTLY and not filtered_df.empty:
        ch1, ch2 = st.columns(2)

        # Chart 1: Direction Distribution
        with ch1:
            st.markdown("##### 🧭 Direction Distribution")
            dir_counts = filtered_df["predicted_direction"].value_counts().reset_index()
            dir_counts.columns = ["Direction", "Count"]
            color_map = {
                "POSITIVE": "#10B981",
                "NEUTRAL": "#64748B",
                "NEGATIVE": "#EF4444",
            }
            fig_dir = px.pie(
                dir_counts,
                values="Count",
                names="Direction",
                color="Direction",
                color_discrete_map=color_map,
                hole=0.45,
            )
            fig_dir.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300)
            st.plotly_chart(fig_dir, use_container_width=True)

        # Chart 2: Impact Strength Distribution
        with ch2:
            st.markdown("##### ⚡ Impact Strength Distribution")
            imp_order = ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]
            imp_counts = filtered_df["impact_strength"].value_counts().reindex(imp_order).fillna(0).reset_index()
            imp_counts.columns = ["Impact Strength", "Count"]
            fig_imp = px.bar(
                imp_counts,
                x="Impact Strength",
                y="Count",
                color="Impact Strength",
                color_discrete_sequence=["#93C5FD", "#3B82F6", "#1D4ED8", "#1E3A8A"],
            )
            fig_imp.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300, showlegend=False)
            st.plotly_chart(fig_imp, use_container_width=True)

        ch3, ch4 = st.columns(2)

        # Chart 3: Model Confidence Distribution
        with ch3:
            st.markdown("##### 🎯 Model Confidence Distribution")
            conf_order = ["LOW", "MEDIUM", "HIGH"]
            conf_counts = filtered_df["confidence"].value_counts().reindex(conf_order).fillna(0).reset_index()
            conf_counts.columns = ["Confidence", "Count"]
            fig_conf = px.bar(
                conf_counts,
                x="Confidence",
                y="Count",
                color="Confidence",
                color_discrete_sequence=["#FCA5A5", "#FBBF24", "#34D399"],
            )
            fig_conf.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300, showlegend=False)
            st.plotly_chart(fig_conf, use_container_width=True)

        # Chart 4: Market-Moving Probability Distribution
        with ch4:
            st.markdown("##### 🌊 Market-Moving Probability Spread")
            fig_mm = px.histogram(
                filtered_df,
                x="market_moving_probability",
                nbins=20,
                color_discrete_sequence=["#8B5CF6"],
                labels={"market_moving_probability": "Market Moving Probability"},
            )
            fig_mm.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300, showlegend=False)
            st.plotly_chart(fig_mm, use_container_width=True)

    else:
        st.info("Interactive charts require Plotly and non-empty data.")

    st.markdown("---")

    # 5. Filtered Predictions Table
    st.markdown("### 📋 Filtered Prediction Records")
    st.caption(f"Showing {min(len(filtered_df), 100):,} sample records out of {len(filtered_df):,} filtered results.")

    tbl_cols = [
        "bill_title", "company_name", "ticker", "sector", "event_window",
        "predicted_direction", "market_moving_probability", "impact_strength",
        "impact_score", "confidence", "risk_category"
    ]
    available = [c for c in tbl_cols if c in filtered_df.columns]
    
    sample_df = filtered_df[available].head(100).copy()
    if "market_moving_probability" in sample_df.columns:
        sample_df["market_moving_probability"] = sample_df["market_moving_probability"].apply(lambda p: f"{p:.1%}")
    if "impact_score" in sample_df.columns:
        sample_df["impact_score"] = sample_df["impact_score"].apply(lambda s: f"{s:.3f}")

    sample_df.columns = [c.replace("_", " ").title() for c in available]
    st.dataframe(sample_df, use_container_width=True, hide_index=True)

    # 6. Groq AI Prediction Explanation
    st.markdown("---")
    with st.expander("🤖 AI Prediction Explanation & Analytical Insights (Groq)", expanded=False):
        ai_svc = get_ai_service()
        if not ai_svc.client.is_available:
            st.info(
                "AI Prediction Explanation requires `GROQ_API_KEY` to be configured in the environment. "
                "The quantitative predictions above remain fully authoritative.",
                icon="ℹ️",
            )
        else:
            pred_bills = sorted(filtered_df["bill_id"].dropna().unique()) if "bill_id" in filtered_df.columns else []
            if pred_bills:
                c_sel, c_btn = st.columns([3, 1])
                with c_sel:
                    chosen_bid = st.selectbox("Select Bill to Explain Prediction:", options=pred_bills, key="ai_pred_bill_sel")
                with c_btn:
                    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                    run_exp = st.button("Explain Prediction", key="ai_pred_explain_btn")
                if run_exp:
                    with st.spinner("Generating analytical prediction explanation…"):
                        pred_res = ai_svc.explain_market_intelligence(chosen_bid, persona="INVESTOR")
                        st.markdown(pred_res.display_markdown)
            else:
                st.caption("No bills available in current filter selection.")

