"""
dashboard/pages/bill_detail.py
==============================
Task 7.4.2 — Bill Intelligence & Deep Dive.

Provides an authoritative, multi-perspective intelligence dossier for a selected
legislative bill:
1. Legislative Information & Plain-English Summary
2. Key Areas (Sectors, Industries, Companies, Policy Domains)
3. Market Impact (Exact probabilities, direction, impact strength, confidence)
4. Risk Profile (Composite risk, category, uncertainty, tail risks)
5. Anticipation & Pricing-In (Diffusion analysis, non-accusatory academic terminology)
6. Legislative Timeline (Authoritative milestone dates)
7. Affected Company View (Sortable by impact, risk, confidence, market-moving)
8. Stakeholder Views (Investor, Business/Corporate, Public/Citizen dossiers)
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd
import streamlit as st

from dashboard.components.ai_explanation_panel import render_ai_explanation_panel
from dashboard.services.dashboard_service import DashboardService


def render_bill_detail_page(
    service: DashboardService,
    master_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Render the comprehensive '🔍 Bill Intelligence' page.
    """
    # 1. Resolve selected bill
    production_bills = service.get_production_bills()
    if not production_bills:
        st.error("No production bills available in repository.")
        return

    bill_map = {b.bill_id: b for b in production_bills}
    bill_options = [b.bill_id for b in production_bills]
    bill_titles = {b.bill_id: f"{b.title} ({b.bill_number or 'N/A'})" for b in production_bills}

    # Check session state for navigation pre-selection
    default_id = st.session_state.get("selected_bill_id")
    if not default_id or default_id not in bill_titles:
        default_id = bill_options[0]

    default_index = bill_options.index(default_id)

    st.markdown(
        "<h1 style='margin-bottom:0;'>🔍 Bill Intelligence</h1>",
        unsafe_allow_html=True,
    )
    st.caption("Deep-dive parliamentary intelligence, market impact forecasts, risk profiles, and stakeholder interpretation.")

    # Selector
    col_sel, col_back = st.columns([4, 1])
    with col_sel:
        selected_bill_id = st.selectbox(
            "Select Legislative Bill:",
            options=bill_options,
            index=default_index,
            format_func=lambda bid: bill_titles.get(bid, bid),
            key="bill_detail_bill_selector",
        )
    with col_back:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        if st.button("⬅️ All Bills", key="btn_back_to_all_bills"):
            st.session_state["nav_override"] = "📜 All Bills"
            st.rerun()

    # Update session state
    st.session_state["selected_bill_id"] = selected_bill_id

    # 2. Load Bill Detail Data
    try:
        data = service.get_bill_detail_data(selected_bill_id)
    except Exception as exc:
        st.error(f"Error loading bill intelligence: {exc}")
        return

    if not data:
        st.warning(f"Could not retrieve details for bill '{selected_bill_id}'.")
        return

    bill = data["bill"]
    summary_obj = data["bill_summary"]
    market_impact = data["market_impact"]
    risk_info = data["risk"]
    ant_info = data["anticipation"]
    timeline = data["timeline"]
    affected_table = data["affected_companies_table"]
    stakeholder_reports = data["stakeholder_reports"]

    st.markdown("---")

    # =========================================================================
    # SECTION 1: LEGISLATIVE INFORMATION & PLAIN-ENGLISH SUMMARY
    # =========================================================================
    st.markdown(f"## 🏛️ {bill.title}")

    col_meta1, col_meta2 = st.columns([3, 2])

    with col_meta1:
        intro_date_str = bill.introduction_date.strftime("%d %b %Y") if bill.introduction_date else "Date unavailable"
        st.markdown(
            f"""
            <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:16px;border-radius:8px;line-height:1.8;">
                <b>Parliament Bill Number:</b> {bill.bill_number or 'Not assigned'}<br>
                <b>Authoritative Introduction Date:</b> {intro_date_str}<br>
                <b>House of Origin:</b> {bill.house.value if hasattr(bill.house, 'value') else bill.house}<br>
                <b>Sponsoring Ministry:</b> {bill.ministry or 'Not specified'}<br>
                <b>Official Parliamentary Type:</b> Government Bill (PRS Legislative Source)<br>
                <b>System-Derived Policy Category:</b> <span style="font-weight:600;color:#0284c7;">{summary_obj.bill_category if summary_obj else 'General'}</span><br>
                <b>Current Legislative Status:</b> <span style="font-weight:600;color:#1e40af;">{summary_obj.status if summary_obj else 'Status not available.'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_meta2:
        st.markdown("#### 📋 What Does This Bill Change?")
        st.markdown(
            f"""
            <div style="background:#FFFFFF;border-left:4px solid #3B82F6;padding:14px 16px;border:1px solid #E2E8F0;border-radius:4px;font-size:0.92rem;line-height:1.6;">
                <b>Core Legislative Provisions:</b><br>
                {data['plain_summary']}
            </div>
            """,
            unsafe_allow_html=True,
        )


    st.markdown("---")

    # Groq AI Intelligence & Explanation Layer
    with st.expander("🤖 AI Intelligence & Explanations (Groq Layer)", expanded=False):
        render_ai_explanation_panel(
            bill_id=bill.bill_id,
            default_persona="General Public",
            key_prefix=f"central_ai_{bill.bill_id}",
        )

    # =========================================================================
    # SECTION 2: KEY AREAS
    # =========================================================================
    st.markdown("### 🎯 Key Policy & Economic Areas")
    ka1, ka2, ka3 = st.columns(3)

    with ka1:
        st.markdown("**Affected Sectors:**")
        if data["sectors"]:
            for sec in data["sectors"]:
                st.markdown(f"- 🏷️ `{sec}`")
        else:
            st.caption("General / Multi-sector governance")

    with ka2:
        st.markdown("**Affected Industries:**")
        if data["industries"]:
            for ind in data["industries"][:5]:
                st.markdown(f"- 🏭 `{ind}`")
            if len(data["industries"]) > 5:
                st.caption(f"+ {len(data['industries']) - 5} more industries")
        else:
            st.caption("Broad industry impact")

    with ka3:
        st.markdown(f"**Affected Companies ({len(data['affected_companies'])} mapped):**")
        comp_names = [f"{c.company_name} ({getattr(c, 'ticker_nse', '')})" for c in data["affected_companies"][:4]]
        for cn in comp_names:
            st.markdown(f"- 🏢 {cn}")
        if len(data["affected_companies"]) > 4:
            st.caption(f"+ {len(data['affected_companies']) - 4} additional listed entities")

    st.markdown("---")

    # =========================================================================
    # SECTION 3: MARKET IMPACT FORECAST
    # =========================================================================
    st.markdown("### 📈 Market Impact Forecast")
    st.caption("Machine-learning predictions derived from pre-introduction legislative text and cross-sector market embeddings. Read-only.")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(
            "Predicted Direction",
            market_impact["predicted_direction"],
            help="Predicted directional movement across the affected cohort.",
        )
    with m2:
        st.metric(
            "Market-Moving Prob",
            f"{market_impact['market_moving_probability']:.1%}",
            delta="Significant" if market_impact['market_moving_probability'] >= 0.50 else "Subdued",
            help="Model estimated probability that this bill generates market-moving abnormal volatility.",
        )
    with m3:
        st.metric(
            "Impact Strength",
            market_impact["impact_strength"],
            help="Magnitude tier of estimated abnormal returns.",
        )
    with m4:
        st.metric(
            "Impact Score",
            f"{market_impact['impact_score']:.3f}",
            help="Normalized continuous impact intensity score [0.0 - 1.0].",
        )

    # Calibrated probabilities display
    st.markdown("##### Directional Probability Breakdown")
    p_pos = market_impact["positive_probability"]
    p_neg = market_impact["negative_probability"]
    p_neut = market_impact["neutral_probability"]

    pr_col1, pr_col2, pr_col3 = st.columns(3)
    with pr_col1:
        st.markdown(f"🟢 **Positive:** `{p_pos:.1%}`")
        st.progress(min(max(p_pos, 0.0), 1.0))
    with pr_col2:
        st.markdown(f"⚪ **Neutral:** `{p_neut:.1%}`")
        st.progress(min(max(p_neut, 0.0), 1.0))
    with pr_col3:
        st.markdown(f"🔴 **Negative:** `{p_neg:.1%}`")
        st.progress(min(max(p_neg, 0.0), 1.0))

    st.caption("ℹ️ Stored probabilities are preserved exactly from the model inference pipeline without recalculation.")
    st.markdown("---")

    # =========================================================================
    # SECTION 4: RISK & UNCERTAINTY
    # =========================================================================
    st.markdown("### ⚠️ Risk & Uncertainty Profile")
    r1, r2, r3 = st.columns(3)

    with r1:
        st.metric(
            "Risk Category",
            risk_info["risk_category"],
            help="Categorical risk tier based on model confidence and volatility dispersion.",
        )
    with r2:
        st.metric(
            "Composite Risk Score",
            f"{risk_info['risk_score']:.3f}",
            help="Quantitative composite risk score [0.0 - 1.0].",
        )
    with r3:
        st.metric(
            "Confidence-Related Risk",
            f"{risk_info['confidence_risk']:.3f}",
            help="Risk discount due to epistemic uncertainty.",
        )

    st.markdown(
        f"""
        <div style="background:#FFFBEB;border:1px solid #FDE68A;padding:12px;border-radius:6px;font-size:0.9rem;margin-top:8px;">
            <b>Uncertainty Assessment:</b> {risk_info['uncertainty_explanation']}<br>
            <b>Tail-Risk Flags:</b> {', '.join(risk_info['tail_risk_flags'])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # =========================================================================
    # SECTION 5: ANTICIPATION & PRICING-IN
    # =========================================================================
    st.markdown("### 🔍 Anticipation & Pre-Event Diffusion Analysis")
    st.caption("Measures pre-event informational diffusion and market pricing-in before formal introduction.")

    a1, a2 = st.columns([1, 2])
    with a1:
        st.metric(
            "Anticipation Classification",
            ant_info["anticipation_class"],
            help="Degree of abnormal pre-introduction market drift detected.",
        )
        st.metric(
            "Mean Anticipation Score",
            f"{ant_info['anticipation_score']:.3f}",
            help="Quantitative pre-event drift score [0.0 - 1.0].",
        )

    with a2:
        st.markdown(
            f"""
            <div style="background:#F0FDF4;border:1px solid #BBF7D0;padding:16px;border-radius:6px;font-size:0.9rem;line-height:1.6;">
                <h5 style="margin-top:0;color:#166534;">Evidence Summary</h5>
                <p>{ant_info['evidence_summary']}</p>
                <p style="color:#4b5563;font-size:0.85rem;margin-bottom:0;">
                    <b>Academic Interpretation:</b> Evidence suggests that relevant information may have been 
                    partially or fully priced in before formal introduction.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="background:#FEF2F2;border:1px solid #FECACA;padding:10px 14px;border-radius:6px;font-size:0.85rem;color:#991B1B;margin-top:10px;">
            🛡️ <b>Mandatory Compliance Notice:</b> Anticipation analysis measures statistical price movements in public equity markets.
            <b>Anticipation evidence is NOT proof of insider trading or unlawful activity.</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # =========================================================================
    # SECTION 6: LEGISLATIVE TIMELINE
    # =========================================================================
    st.markdown("### ⏳ Legislative Timeline")
    st.caption("Authoritative parliamentary progression stages. Only official verified dates are displayed.")

    tl_cols = st.columns(len(timeline))
    for idx, stage in enumerate(timeline):
        with tl_cols[idx]:
            icon = "✅" if stage["status"] == "Completed" else ("🔄" if "Progress" in stage["status"] or "Committee" in stage["status"] else "⏳")
            st.markdown(
                f"""
                <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:12px;border-radius:6px;text-align:center;">
                    <div style="font-size:1.4rem;">{icon}</div>
                    <b>{stage['stage']}</b><br>
                    <span style="font-size:0.85rem;color:#64748b;">{stage['date']}</span><br>
                    <span style="font-size:0.8rem;color:#2563eb;font-weight:600;">{stage['status']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # =========================================================================
    # SECTION 7: AFFECTED COMPANY VIEW
    # =========================================================================
    st.markdown("### 🏢 Affected Company Cohort")
    st.caption("Individual corporate entities subject to regulatory or market impact under this bill.")

    if not affected_table.empty:
        sort_by = st.selectbox(
            "Sort Company Table By:",
            options=["Impact Score", "Risk Score", "Market-Moving Prob", "Company Name"],
            index=0,
            key="bill_detail_comp_sort",
        )

        sorted_table = affected_table.copy()
        if sort_by == "Impact Score":
            sorted_table = sorted_table.sort_values(by="impact_score", ascending=False)
        elif sort_by == "Risk Score":
            sorted_table = sorted_table.sort_values(by="risk_score", ascending=False)
        elif sort_by == "Market-Moving Prob":
            sorted_table = sorted_table.sort_values(by="market_moving_prob", ascending=False)
        elif sort_by == "Company Name":
            sorted_table = sorted_table.sort_values(by="company_name", ascending=True)

        # Format display table
        display_comp_df = sorted_table[[
            "company_name", "ticker", "sector", "direction",
            "market_moving_prob", "impact_strength", "confidence",
            "risk_category", "anticipation", "isin"
        ]].copy()

        display_comp_df["market_moving_prob"] = display_comp_df["market_moving_prob"].apply(lambda p: f"{p:.1%}")
        display_comp_df.columns = [
            "Company", "Ticker", "Sector", "Direction", "Market Moving",
            "Impact", "Confidence", "Risk Tier", "Anticipation", "ISIN"
        ]

        st.dataframe(display_comp_df, use_container_width=True, hide_index=True)

        # Drill-down selector
        sel_drill_isin = st.selectbox(
            "Select a Company to view detailed exposure:",
            options=sorted_table["isin"].tolist(),
            format_func=lambda isin: f"{sorted_table[sorted_table['isin'] == isin].iloc[0]['company_name']} ({isin})",
            key="bill_detail_drill_isin",
        )
        if st.button("🏢 Inspect Company Detail", key="btn_drill_company"):
            st.session_state["selected_company_isin"] = sel_drill_isin
            st.session_state["nav_override"] = "🏢 Company Detail"
            st.rerun()

    st.markdown("---")

    # =========================================================================
    # SECTION 8: STAKEHOLDER VIEWS
    # =========================================================================
    st.markdown("### 👥 Stakeholder Interpretation Dossier")
    st.caption("Synthesized intelligence reports tailored to distinct decision-making lenses. Read-only.")

    stk_lens = st.radio(
        "Select Decision-Support Lens:",
        options=["💼 Investor Perspective", "🏢 Business / Corporate", "🌍 Public / Citizen"],
        index=0,
        horizontal=True,
        key="bill_detail_stk_lens",
    )

    lens_key = "INVESTOR" if "Investor" in stk_lens else ("BUSINESS" if "Business" in stk_lens else "PUBLIC")
    report = stakeholder_reports.get(lens_key)

    if report:
        st.markdown(
            f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:20px;border-radius:8px;line-height:1.7;">
                <h4 style="margin-top:0;color:#1e40af;">{lens_key.title()} Executive Dossier</h4>
                <p><b>Executive Summary:</b> {getattr(report, 'executive_summary', 'Summary unavailable.')}</p>
                <p><b>Impact Assessment:</b> {getattr(report, 'impact_summary', 'Impact summary unavailable.')}</p>
                <p><b>Risk & Uncertainty:</b> {getattr(report, 'risk_summary', 'Risk assessment unavailable.')}</p>
                <p><b>Anticipation / Diffusion:</b> {getattr(report, 'anticipation_summary', 'Pre-event drift summary unavailable.')}</p>
                <div style="background:#F8FAFC;padding:10px;border-radius:4px;font-size:0.85rem;color:#64748b;margin-top:12px;">
                    <b>Institutional Disclaimer:</b> {getattr(report, 'disclaimer', 'This dossier is for analytical decision-support only and does not constitute investment advice.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # Graceful fallback presentation
        if lens_key == "INVESTOR":
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:16px;border-radius:8px;">
                    <h5 style="color:#065F46;">Investor Dossier</h5>
                    <p><b>Market Impact:</b> Direction is predicted as <b>{market_impact['predicted_direction']}</b> with <b>{market_impact['impact_strength']}</b> impact intensity.</p>
                    <p><b>Probability Distribution:</b> P(Positive)={p_pos:.1%}, P(Negative)={p_neg:.1%}, P(Neutral)={p_neut:.1%}.</p>
                    <p><b>Risk Category:</b> {risk_info['risk_category']} (Confidence risk: {risk_info['confidence_risk']:.3f}).</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif lens_key == "BUSINESS":
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:16px;border-radius:8px;">
                    <h5 style="color:#1E40AF;">Corporate & Regulatory Dossier</h5>
                    <p><b>Regulatory Implications:</b> Pertains to {bill.ministry} oversight across {', '.join(data['sectors']) if data['sectors'] else 'General'}.</p>
                    <p><b>Sector Exposure:</b> Affects {len(data['affected_companies'])} listed market participants across {len(data['industries'])} sub-industries.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:16px;border-radius:8px;">
                    <h5 style="color:#92400E;">Public & Societal Dossier</h5>
                    <p><b>Plain-Language Overview:</b> {data['plain_summary']}</p>
                    <p><b>Economic Relevance:</b> Tabled in {bill.house.value if hasattr(bill.house, 'value') else bill.house} with broader economic impact across {', '.join(data['sectors']) if data['sectors'] else 'General'}.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
