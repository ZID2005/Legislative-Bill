"""
dashboard/pages/company_detail.py
=================================
Task 7.4.2 — Company Detail page.

Provides a dedicated company intelligence dossier:
1. Company Profile (Name, ISIN, Ticker, Sector, Industry)
2. Aggregate Exposure Metrics across the legislative universe
3. Related Bills Table (Direction, Impact, Risk, Anticipation per bill)
4. Persisted Company-Level Report Dossier from ReportRepository
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd
import streamlit as st

from dashboard.services.dashboard_service import DashboardService


def render_company_detail_page(
    service: DashboardService,
    master_df: Optional[pd.DataFrame] = None,
) -> None:
    """
    Render the '🏢 Company Detail' page.
    """
    # 1. Resolve selected company ISIN
    all_companies = service.get_all_companies()
    if not all_companies:
        st.error("No companies found in repository.")
        return

    comp_options = [c.isin for c in all_companies]
    comp_labels = {}
    for c in all_companies:
        u_tag = "Quant" if getattr(c, "universe_type", "") == "quantitative" else "Intel"
        comp_labels[c.isin] = f"{c.company_name} ({getattr(c, 'ticker_nse', '') or c.isin}) [{u_tag}]"

    default_isin = st.session_state.get("selected_company_isin")
    if not default_isin or default_isin not in comp_labels:
        default_isin = comp_options[0]

    default_idx = comp_options.index(default_isin)

    st.markdown(
        "<h1 style='margin-bottom:0;'>🏢 Company Detail</h1>",
        unsafe_allow_html=True,
    )
    st.caption("Comprehensive corporate intelligence dossier: profile, business activities, legislative exposure, traceable evidence, and AI explanation.")

    # Selector
    c_sel, c_back = st.columns([4, 1])
    with c_sel:
        selected_isin = st.selectbox(
            "Select Corporate Entity (Quantitative & Intelligence):",
            options=comp_options,
            index=default_idx,
            format_func=lambda isin: comp_labels.get(isin, isin),
            key="company_detail_selector",
        )
    with c_back:
        st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
        if st.button("⬅️ All Companies", key="btn_back_to_companies"):
            st.session_state["nav_override"] = "🏢 Company Intelligence"
            st.rerun()

    st.session_state["selected_company_isin"] = selected_isin

    # 2. Load Company Data
    try:
        data = service.get_company_detail_data(selected_isin)
    except Exception as exc:
        st.error(f"Error loading company data: {exc}")
        return

    if not data:
        st.warning(f"No detail available for identifier '{selected_isin}'.")
        return

    company = data["company"]
    profile = data.get("profile")
    related_df = data["related_bills_table"]
    comp_report = data.get("company_report")
    is_intel_only = data.get("is_intelligence_only", False)

    st.markdown("---")

    # Company Profile Card
    st.markdown(f"## 🏢 {company.company_name}")
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown(f"**ISIN / ID:** `{company.isin}`")
        st.markdown(f"**NSE / BSE Ticker:** `{getattr(company, 'ticker_nse', 'N/A') or 'N/A'}`")
        st.markdown(f"**Entity Type:** `{getattr(company, 'entity_type', 'listed_company')}`")
    with p2:
        st.markdown(f"**Primary Sector:** `{company.sector}`")
        st.markdown(f"**Sub-Industry:** `{getattr(company, 'industry', 'General')}`")
        if getattr(company, "group_name", None):
            st.markdown(f"**Corporate Group:** `{company.group_name}`")
    with p3:
        st.markdown(f"**Associated Bills:** `{data['associated_bills_count']}`")
        st.markdown(f"**Universe:** `{'INTELLIGENCE' if is_intel_only else 'QUANTITATIVE'}`")
        if getattr(company, "hq_state", ""):
            st.markdown(f"**Headquarters:** `{company.hq_city + ', ' if company.hq_city else ''}{company.hq_state}`")
    with p4:
        if is_intel_only:
            st.markdown("**Data Provenance:** `Intelligence Master (Verified)`")
            st.markdown("**Quantitative Firewall:** `ACTIVE (Zero Predictions)`")
        else:
            st.markdown("**Data Provenance:** `Production Master`")
            st.markdown("**Prediction Status:** `Pre-computed (Read-only)`")

    # Business activities & State presences
    if getattr(company, "business_activities", None):
        st.markdown("##### 💼 Verified Business Activities")
        st.write(", ".join(f"`{act}`" for act in company.business_activities))

    if is_intel_only:
        st.info(
            "🛡️ **Quantitative Firewall Active**: This entity belongs to the Company Intelligence universe. "
            "Financial market return models, price targets, and trading signals are strictly disabled. "
            "All exposure analysis is qualitative and grounded in verified statutory evidence.",
            icon="🛡️",
        )

    st.markdown("---")

    # Exposure Summary Metrics
    st.markdown("### 📊 Legislative Exposure Summary")
    if not related_df.empty:
        pos_cnt = int((related_df["Direction"] == "POSITIVE").sum())
        neg_cnt = int((related_df["Direction"] == "NEGATIVE").sum())
        neut_cnt = int((related_df["Direction"].isin(["NEUTRAL", "MIXED", "UNKNOWN"])).sum())

        if not is_intel_only:
            mm_cnt = int((related_df["Market Moving"] >= 0.50).sum())
            avg_imp = float(related_df["Impact Score"].mean())
            avg_risk = float(related_df["Risk Score"].mean())

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Positive Exposure", f"{pos_cnt} bills", delta=f"{pos_cnt/len(related_df):.0%}")
            with m2:
                st.metric("Negative Exposure", f"{neg_cnt} bills", delta=f"{neg_cnt/len(related_df):.0%}", delta_color="inverse")
            with m3:
                st.metric("Market-Moving Bills", f"{mm_cnt} bills", delta="High Impact" if mm_cnt > 0 else "Low Impact")
            with m4:
                st.metric("Average Impact Score", f"{avg_imp:.3f}", delta=f"Risk: {avg_risk:.3f}")
        else:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Associated Bills", f"{len(related_df)} bills")
            with m2:
                st.metric("Direct Exposures", f"{sum(1 for d in related_df.get('Direct/Indirect', []) if d == 'DIRECT')} bills")
            with m3:
                st.metric("Statutory Mechanisms", f"{len(set(related_df.get('Mechanism', [])))} mechanisms")
            with m4:
                st.metric("Market Prediction", "Zero (Firewalled)", delta="Qualitative Only", delta_color="off")

    st.markdown("---")

    # Related Bills Table
    st.markdown("### 📜 Associated Legislative Bills")
    st.caption("Authoritative legislation with verified business exposure to this corporate entity.")

    if not related_df.empty:
        cols = ["Bill Title", "Ministry", "Direction"]
        for opt_c in ["Exposure Type", "Mechanism", "Direct/Indirect", "Impact Strength", "Risk Category", "bill_id"]:
            if opt_c in related_df.columns:
                cols.append(opt_c)

        st.dataframe(
            related_df[cols].drop(columns=["bill_id"] if "bill_id" in cols else []),
            use_container_width=True,
            hide_index=True,
        )

        # Drill into a specific bill
        if "bill_id" in related_df.columns:
            sel_drill_bill = st.selectbox(
                "Select an Associated Bill to view complete intelligence dossier:",
                options=related_df["bill_id"].tolist(),
                format_func=lambda bid: f"{related_df[related_df['bill_id'] == bid].iloc[0]['Bill Title']}",
                key="company_detail_drill_bill",
            )
            if st.button("🔍 Open Bill Intelligence", key="btn_drill_bill"):
                st.session_state["selected_bill_id"] = sel_drill_bill
                st.session_state["nav_override"] = "🔍 Bill Intelligence"
                st.rerun()
    else:
        st.info("No associated bills found for this company.")

    st.markdown("---")

    # 3. Evidence-Grounded Exposure Details (First-class Dossier)
    if profile and profile.related_bills:
        st.markdown("### 🔍 Verified Exposure & Evidence Dossier")
        st.caption("Statutory provisions, operational links, and official evidence connecting this entity to legislation.")

        for idx, exp in enumerate(profile.related_bills):
            with st.expander(f"📜 {exp.bill_title} ({exp.jurisdiction.title()}) — {exp.direct_indirect} [{exp.exposure_strength} Strength]", expanded=(idx == 0)):
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.markdown(f"**Exposure Type:** `{exp.exposure_type}`")
                    st.markdown(f"**Statutory Mechanism:** `{exp.mechanism}`")
                with d2:
                    st.markdown(f"**Business Activity:** `{exp.business_activity or 'Sector operations'}`")
                    st.markdown(f"**Geographic Relevance:** `{exp.state or exp.geographic_scope}`")
                with d3:
                    st.markdown(f"**Market Relevance:** `{exp.market_relevance}`")
                    st.markdown(f"**Verification Status:** `Verified Statutory Grounding`")

                if exp.evidence:
                    st.markdown("##### 📑 Authoritative Evidence Citations:")
                    for ev in exp.evidence:
                        st.markdown(f"- **Claim:** {ev.claim}")
                        st.caption(f"  *Reference: {ev.reference} ({ev.source_type})*")

    st.markdown("---")

    # 4. Groq AI Company Intelligence Assistant
    with st.expander("🤖 AI Company Intelligence Assistant (Groq)", expanded=False):
        st.markdown("#### Natural Language Company & Exposure Explanation")
        st.caption("Grounded in verified project records; zero speculative financial predictions.")

        c_q, c_btn = st.columns([4, 1])
        with c_q:
            ai_q = st.text_input(
                "Ask AI about this company:",
                placeholder=f"e.g. 'Why is this legislation relevant to {company.company_name}?' or 'What activities create exposure?'",
                key="company_detail_ai_query",
            )
        with c_btn:
            st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
            ask_clicked = st.button("Ask Groq", key="btn_ask_company_ai", type="primary")

        if ask_clicked and ai_q:
            try:
                from services.ai.ai_explanation_service import AIExplanationService
                ai_service = AIExplanationService()
                with st.spinner("Generating grounded AI explanation via Groq Cloud…"):
                    res = ai_service.ask_company_ai(company.isin, ai_q)
                if res.success:
                    st.markdown(res.display_markdown)
                else:
                    st.warning(res.content)
            except Exception as e:
                st.info(f"AI explanation service unavailable: {e}")

    # Persisted Company Report Viewer (for quantitative companies)
    if comp_report:
        st.markdown("---")
        st.markdown("### 📋 Synthesized Company Intelligence Report")
        st.markdown(
            f"""
            <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:20px;border-radius:8px;line-height:1.7;">
                <h4 style="margin-top:0;color:#1e40af;">Corporate Exposure Report: {company.company_name}</h4>
                <p><b>Executive Summary:</b> {getattr(comp_report, 'executive_summary', 'Detailed company analysis.')}</p>
                <p><b>Regulatory & Strategic Headwinds:</b> {getattr(comp_report, 'risk_summary', 'Evaluated based on ministerial jurisdiction.')}</p>
                <div style="background:#F8FAFC;padding:10px;border-radius:4px;font-size:0.85rem;color:#64748b;margin-top:12px;">
                    <b>Report Metadata:</b> Version {getattr(comp_report, 'report_version', 'v1.0')} | 
                    Generated Timestamp: {getattr(comp_report, 'generated_timestamp', 'Production persistence')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
