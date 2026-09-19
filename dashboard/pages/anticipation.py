"""
dashboard/pages/anticipation.py
===============================
Task 7.4.2 — Anticipation & Pricing-In page.

Provides academic analysis of pre-event information diffusion:
- Anticipation Classifications: No Evidence, Weak, Moderate, Strong
- Distribution across bills and companies
- Academic explanation of pre-event drift & The Anticipation Paradox
- Mandatory non-accusatory research integrity disclaimers
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from dashboard.components.ai_explanation_panel import get_ai_service
from dashboard.services.dashboard_service import DashboardService


def render_anticipation_page(
    service: DashboardService,
    master_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Render the '🔍 Anticipation & Pricing-In' analytical page.
    """
    st.markdown(
        "<h1 style='margin-bottom:0;'>🔍 Anticipation & Pricing-In</h1>",
        unsafe_allow_html=True,
    )
    st.caption("Quantitative auditing of pre-event informational diffusion, market drift, and price discovery prior to parliamentary introduction.")

    # 1. Academic Disclaimer Banner
    st.markdown(
        """
        <div style="background:#EFF6FF;border-left:4px solid #3B82F6;padding:12px 16px;border-radius:4px;font-size:0.9rem;margin-bottom:16px;">
            <b>Academic Principle:</b> Anticipation analysis measures pre-introduction abnormal return drift ($T = -30$ to $T = -2$).
            Evidence suggests that relevant economic information may have been partially or fully priced in by public markets prior to formal tabling.
            <br><br>
            <span style="color:#DC2626;font-weight:600;">⚠️ Critical Research Integrity Rule:</span>
            <b>Anticipation evidence is NOT evidence of insider trading, leaks, or illegal activity.</b>
            Public disclosures, industry consultations, parliamentary question sessions, and macro trends frequently generate legitimate pre-introduction price discovery.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Load dataset
    df = master_df if (master_df is not None and not master_df.empty) else service.get_decision_dataframe()

    if df.empty:
        st.warning("No decision or anticipation records available.")
        return

    # 3. Aggregate Tiers & Distribution
    tier_order = ["NO_EVIDENCE", "WEAK_EVIDENCE", "MODERATE_EVIDENCE", "STRONG_EVIDENCE"]
    tier_labels = {
        "NO_EVIDENCE": "🟢 No Evidence",
        "WEAK_EVIDENCE": "🟡 Weak Evidence",
        "MODERATE_EVIDENCE": "🟠 Moderate Evidence",
        "STRONG_EVIDENCE": "🔴 Strong Evidence",
    }

    st.markdown("### 📊 Anticipation Evidence Classification")
    k1, k2, k3, k4 = st.columns(4)

    tot = len(df)
    counts = df["anticipation_evidence"].value_counts().to_dict()

    with k1:
        cnt = counts.get("NO_EVIDENCE", 0)
        st.metric("No Evidence", f"{cnt:,}", delta=f"{cnt/tot:.1%}" if tot > 0 else "0%")
    with k2:
        cnt = counts.get("WEAK_EVIDENCE", 0)
        st.metric("Weak Evidence", f"{cnt:,}", delta=f"{cnt/tot:.1%}" if tot > 0 else "0%")
    with k3:
        cnt = counts.get("MODERATE_EVIDENCE", 0)
        st.metric("Moderate Evidence", f"{cnt:,}", delta=f"{cnt/tot:.1%}" if tot > 0 else "0%")
    with k4:
        cnt = counts.get("STRONG_EVIDENCE", 0)
        st.metric("Strong Evidence", f"{cnt:,}", delta=f"{cnt/tot:.1%}" if tot > 0 else "0%", delta_color="inverse")

    st.markdown("---")

    # 4. Interactive Distribution Chart & Paradox Explanation
    col_chart, col_paradox = st.columns([1, 1])

    with col_chart:
        st.markdown("##### 📈 Distribution Across Candidate Pairs")
        if HAS_PLOTLY:
            bar_df = pd.DataFrame([
                {"Tier": tier_labels.get(t, t), "Count": counts.get(t, 0)}
                for t in tier_order
            ])
            fig = px.bar(
                bar_df,
                x="Tier",
                y="Count",
                color="Tier",
                color_discrete_sequence=["#10B981", "#FBBF24", "#F97316", "#EF4444"],
            )
            fig.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=320, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.json(counts)

    with col_paradox:
        st.markdown("##### 💡 The Anticipation Paradox")
        st.markdown(
            """
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:16px;border-radius:6px;font-size:0.88rem;line-height:1.6;">
                <b>Definition:</b> The phenomenon where legislative bills that are heavily anticipated by financial markets 
                exhibit <i>smaller</i> abnormal returns upon formal parliamentary introduction than unexpected bills.
                <br><br>
                <b>Key Mechanism:</b>
                <ul>
                    <li>When draft proposals circulate via ministry stakeholder consultations, markets gradually absorb the regulatory impact ($T = -30$ to $-2$).</li>
                    <li>By tabling date ($T = 0$), prices already reflect the expected cash flow impact.</li>
                    <li>Consequently, post-introduction announcement returns ($\text{CAR}[0, +1]$) are muted or reverse, creating a diagnostic paradox for standard event studies.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 5. Searchable Anticipation Table
    st.markdown("### 📋 Anticipation Records by Bill & Corporate Entity")
    st.caption("Searchable breakdown of pre-event diffusion classification.")

    search_ant = st.text_input(
        "Filter by Bill or Company:",
        placeholder="Type bill name, company, or sector…",
        key="anticipation_search_input",
    )

    filtered_ant = df.copy()
    if search_ant:
        q = search_ant.strip().lower()
        mask = (
            filtered_ant["bill_title"].astype(str).str.lower().str.contains(q)
            | filtered_ant["company_name"].astype(str).str.lower().str.contains(q)
            | filtered_ant["sector"].astype(str).str.lower().str.contains(q)
        )
        filtered_ant = filtered_ant[mask]

    cols_show = [
        "bill_title", "company_name", "ticker", "sector",
        "anticipation_evidence", "pricing_in_risk", "predicted_direction", "event_window"
    ]
    available = [c for c in cols_show if c in filtered_ant.columns]
    
    sample_table = filtered_ant[available].head(150).copy()
    sample_table.columns = [c.replace("_", " ").title() for c in available]
    st.dataframe(sample_table, use_container_width=True, hide_index=True)

    # 6. Groq AI Anticipation & Pricing-In Explanation
    st.markdown("---")
    with st.expander("🤖 AI Anticipation & Pricing-In Explanation (Groq)", expanded=False):
        ai_svc = get_ai_service()
        if not ai_svc.client.is_available:
            st.info(
                "AI Anticipation Explanation requires `GROQ_API_KEY` to be configured in the environment. "
                "The quantitative empirical anticipation scores above remain fully authoritative.",
                icon="ℹ️",
            )
        else:
            ant_bills = sorted(filtered_ant["bill_id"].dropna().unique()) if "bill_id" in filtered_ant.columns else []
            if ant_bills:
                c_sel, c_btn = st.columns([3, 1])
                with c_sel:
                    chosen_bid = st.selectbox("Select Bill to Explain Pricing-In Dynamics:", options=ant_bills, key="ai_ant_bill_sel")
                with c_btn:
                    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                    run_exp = st.button("Explain Anticipation", key="ai_ant_explain_btn")
                if run_exp:
                    with st.spinner("Analyzing pre-event informational diffusion…"):
                        ant_res = ai_svc.explain_anticipation(chosen_bid, persona="INVESTOR")
                        st.markdown(ant_res.display_markdown)
            else:
                st.caption("No bills available in current selection.")

