"""
dashboard/pages/risk.py
=======================
Task 7.4.2 — Risk Overview page.

Provides quantitative risk analysis across canonical risk tiers:
- Very Low
- Low
- Moderate
- High
- Very High

Displays:
- Counts, percentages, average impact, and average confidence per tier
- 2D Risk Matrix visualization
- Bill and company drill-down filters
- Strict preservation of pre-computed risk metrics
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


def render_risk_page(
    service: DashboardService,
    master_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Render the '⚠️ Risk Overview' analytical page.
    """
    st.markdown(
        "<h1 style='margin-bottom:0;'>⚠️ Risk Overview</h1>",
        unsafe_allow_html=True,
    )
    st.caption("Quantitative risk evaluation, multi-tier volatility dispersion, and decision-support risk matrices. Read-only.")

    # 1. Load data
    df = master_df if (master_df is not None and not master_df.empty) else service.get_decision_dataframe()

    if df.empty:
        st.warning("No risk or decision records available.")
        return

    # 2. Drilldown Controls
    with st.expander("🔍 Bill & Company Risk Drill-Down", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            bills = ["All Bills"] + sorted([str(b) for b in df["bill_title"].dropna().unique()])
            sel_bill = st.selectbox("Filter by Bill:", options=bills, index=0, key="risk_page_bill")
        with c2:
            companies = ["All Companies"] + sorted([str(c) for c in df["company_name"].dropna().unique()])
            sel_company = st.selectbox("Filter by Company:", options=companies, index=0, key="risk_page_comp")

    filtered_df = df.copy()
    if sel_bill != "All Bills":
        filtered_df = filtered_df[filtered_df["bill_title"] == sel_bill]
    if sel_company != "All Companies":
        filtered_df = filtered_df[filtered_df["company_name"] == sel_company]

    st.markdown("---")

    # 3. Canonical Risk Tiers Table & Metrics
    st.markdown("### 📊 Risk Tier Breakdown")
    st.caption("Distribution across the 5 canonical risk tiers codified in Task 7.2.")

    tiers = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"]
    tier_labels = {
        "VERY_LOW": "🟢 Very Low",
        "LOW": "🟢 Low",
        "MODERATE": "🟡 Moderate",
        "HIGH": "🟠 High",
        "VERY_HIGH": "🔴 Very High",
    }

    tier_stats: list[dict[str, Any]] = []
    tot_records = len(filtered_df)

    for t in tiers:
        sub = filtered_df[filtered_df["risk_category"] == t]
        cnt = len(sub)
        pct = (cnt / tot_records * 100) if tot_records > 0 else 0.0
        avg_imp = float(sub["impact_score"].mean()) if cnt > 0 else 0.0
        # Confidence resolution
        conf_map = {"LOW": 1.0, "MEDIUM": 2.0, "HIGH": 3.0}
        conf_num = sub["confidence"].map(conf_map).dropna()
        avg_conf_str = "N/A"
        if not conf_num.empty:
            mean_c = conf_num.mean()
            avg_conf_str = "High" if mean_c >= 2.5 else ("Medium" if mean_c >= 1.5 else "Low")

        tier_stats.append({
            "Risk Tier": tier_labels.get(t, t),
            "Record Count": cnt,
            "Percentage": f"{pct:.1f}%",
            "Average Impact Score": round(avg_imp, 3),
            "Average Confidence": avg_conf_str,
        })

    tier_df = pd.DataFrame(tier_stats)
    st.dataframe(tier_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # 4. 2D Risk Matrix Chart
    st.markdown("### 🎯 2D Risk Matrix (Impact vs. Volatility Risk)")
    st.caption("Scatter profile of individual decision records plotting normalized Impact Intensity vs Composite Risk Score.")

    if HAS_PLOTLY and not filtered_df.empty:
        # Sample to prevent browser lag if thousands of records
        plot_sample = filtered_df.sample(min(len(filtered_df), 500), random_state=42) if len(filtered_df) > 500 else filtered_df

        color_discrete = {
            "VERY_LOW": "#10B981",
            "LOW": "#34D399",
            "MODERATE": "#FBBF24",
            "HIGH": "#F97316",
            "VERY_HIGH": "#EF4444",
        }

        fig_matrix = px.scatter(
            plot_sample,
            x="impact_score",
            y="risk_score",
            color="risk_category",
            color_discrete_map=color_discrete,
            hover_data=["bill_title", "company_name", "predicted_direction", "event_window"],
            labels={
                "impact_score": "Impact Intensity Score",
                "risk_score": "Composite Risk Score",
                "risk_category": "Risk Category",
            },
        )
        fig_matrix.update_layout(
            margin=dict(l=40, r=40, t=30, b=30),
            height=400,
            xaxis=dict(range=[0, 1.05]),
            yaxis=dict(range=[0, 1.05]),
        )
        st.plotly_chart(fig_matrix, use_container_width=True)

    st.markdown("---")

    # 5. Risk Insights & Safety Disclaimers
    st.markdown(
        """
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:16px;border-radius:8px;font-size:0.9rem;line-height:1.6;">
            <h5 style="margin-top:0;color:#1e40af;">Methodological Risk Scoring Framework</h5>
            <p>Risk scores reflect a composite function of:</p>
            <ul>
                <li><b>Market-moving probability</b>: Likelihood of anomalous post-introduction return variance.</li>
                <li><b>Directional entropy</b>: Dispersion across Positive, Neutral, and Negative calibrated probabilities.</li>
                <li><b>Model confidence discount</b>: Penalty applied when epistemic model uncertainty is elevated.</li>
                <li><b>Tail-risk flags</b>: Structural industry headwinds identified by legal NLP feature extractors.</li>
            </ul>
            <p style="color:#64748b;margin-bottom:0;">
                All risk scores are persisted read-only outputs from Task 7.2 and are not recalculated dynamically in the dashboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 6. Groq AI Risk Profile Explanation
    st.markdown("---")
    with st.expander("🤖 AI Risk Profile Explanation & Analytical Translation (Groq)", expanded=False):
        ai_svc = get_ai_service()
        if not ai_svc.client.is_available:
            st.info(
                "AI Risk Explanation requires `GROQ_API_KEY` to be configured in the environment. "
                "The quantitative composite risk tiers above remain fully authoritative.",
                icon="ℹ️",
            )
        else:
            risk_bills = sorted(df["bill_id"].dropna().unique()) if "bill_id" in df.columns else []
            if risk_bills:
                c_sel, c_btn = st.columns([3, 1])
                with c_sel:
                    chosen_bid = st.selectbox("Select Bill to Explain Risk Profile:", options=risk_bills, key="ai_risk_bill_sel")
                with c_btn:
                    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                    run_exp = st.button("Explain Risk", key="ai_risk_explain_btn")
                if run_exp:
                    with st.spinner("Generating qualitative risk explanation…"):
                        risk_res = ai_svc.explain_risk_profile(chosen_bid, persona="INVESTOR")
                        st.markdown(risk_res.display_markdown)
            else:
                st.caption("No bills available in current selection.")

