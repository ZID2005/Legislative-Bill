"""
dashboard/components/ai_explanation_panel.py
============================================
Reusable Streamlit UI component for Groq AI Intelligence & Explanations.

Supports:
- Central and State bills
- Persona switching (Investor, Business Owner, Employee, Consumer, Farmer, MSME, General Public, Industry)
- Dedicated tabs for all core AI operations
- Conversational "Ask AI about this bill" Q&A
- Graceful degradation when GROQ_API_KEY is not configured
- Zero prediction guarantee for State bills
- Side-by-side bill comparison with AI
"""

from __future__ import annotations

from typing import Optional
import streamlit as st

from services.ai.ai_explanation_service import AIExplanationResult, AIExplanationService
from services.ai.groq_client import GroqClient
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService


@st.cache_resource
def get_ai_service() -> AIExplanationService:
    """Instantiate and cache AIExplanationService."""
    return AIExplanationService()


def render_ai_explanation_panel(
    bill_id: str,
    default_persona: str = "General Public",
    key_prefix: str = "ai_panel",
) -> None:
    """
    Render a comprehensive, interactive Groq AI intelligence panel for a bill.

    Parameters
    ----------
    bill_id : str
        The unique bill identifier.
    default_persona : str
        Initial persona for the explanation.
    key_prefix : str
        Unique Streamlit widget key prefix.
    """
    service = get_ai_service()

    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
            <span style="font-size:1.4rem;">🤖</span>
            <h3 style="margin:0;padding:0;">Groq AI Intelligence & Explanation Layer</h3>
        </div>
        <p style="color:#64748b;font-size:0.92rem;margin-top:0;">
            Plain-language explanations, provisions analysis, and persona-adapted insights grounded in verified legislative data.
        </p>
        """,
        unsafe_allow_html=True,
    )

    if not service.client.is_available:
        st.info(
            "ℹ️ **AI Explanation Layer:** The Groq API key is not currently configured in the environment (`GROQ_API_KEY`). "
            "AI-powered conversational Q&A and narrative summaries are unavailable. "
            "All authoritative statutory facts, taxonomies, and quantitative model outputs remain accessible above.",
            icon="ℹ️",
        )
        return

    # Persona Selector Bar
    persona_options = [
        "General Public",
        "Investor",
        "Business Owner",
        "MSME",
        "Employee",
        "Consumer",
        "Farmer",
        "Industry",
    ]
    def_idx = persona_options.index(default_persona) if default_persona in persona_options else 0

    c_pers, c_info = st.columns([2, 3])
    with c_pers:
        selected_persona = st.selectbox(
            "Select Stakeholder Persona:",
            options=persona_options,
            index=def_idx,
            key=f"{key_prefix}_persona_select_{bill_id}",
            help="Adapts the explanation focus, tone, and practical implications without providing personalized advice.",
        )
    with c_info:
        st.caption(
            f"Active Lens: **{selected_persona}**. Focuses on practical implications relevant to this stakeholder "
            "while strictly respecting verified legislative facts."
        )

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # Operations Tabs
    tabs = st.tabs([
        "💡 Plain Summary",
        "⚖️ Provisions",
        "🏭 Sectors & Stakeholders",
        "🏢 Company Exposure",
        "📈 Market Assessment",
        "⚠️ Risk Profile",
        "🔍 Anticipation",
        "💬 Ask AI",
    ])

    # 1. Plain Summary & Why It Matters
    with tabs[0]:
        st.markdown("#### 💡 Plain-Language Summary & Practical Significance")
        if st.button("Generate Summary", key=f"{key_prefix}_btn_summary_{bill_id}"):
            with st.spinner("Generating grounded plain-language summary via Groq…"):
                res = service.explain_bill_summary(bill_id, persona=selected_persona)
                st.markdown(res.display_markdown)

        if st.button("Why Does This Bill Matter?", key=f"{key_prefix}_btn_why_{bill_id}"):
            with st.spinner("Analyzing legislative significance…"):
                res_why = service.explain_why_it_matters(bill_id, persona=selected_persona)
                st.markdown(res_why.display_markdown)

    # 2. Provisions
    with tabs[1]:
        st.markdown("#### ⚖️ Statutory Provisions Explained")
        if st.button("Explain Key Provisions", key=f"{key_prefix}_btn_prov_{bill_id}"):
            with st.spinner("Deconstructing statutory provisions…"):
                res_prov = service.explain_provisions(bill_id, persona=selected_persona)
                st.markdown(res_prov.display_markdown)

    # 3. Sectors & Stakeholders
    with tabs[2]:
        st.markdown("#### 🏭 Affected Sectors & Stakeholders")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.button("Explain Sector Impact", key=f"{key_prefix}_btn_sec_{bill_id}"):
                with st.spinner("Evaluating sector transmission channels…"):
                    res_sec = service.explain_sector_impact(bill_id, persona=selected_persona)
                    st.markdown(res_sec.display_markdown)
        with col_s2:
            if st.button("Explain Stakeholder Impact", key=f"{key_prefix}_btn_stake_{bill_id}"):
                with st.spinner("Mapping stakeholder impact…"):
                    res_stake = service.explain_stakeholders(bill_id, persona=selected_persona)
                    st.markdown(res_stake.display_markdown)

    # 4. Corporate Exposure
    with tabs[3]:
        st.markdown("#### 🏢 Verified Corporate Exposure Mechanisms")
        st.caption("Explains why specific companies are identified as exposed in project records. Zero stock tipping.")
        if st.button("Explain Corporate Exposure", key=f"{key_prefix}_btn_exposure_{bill_id}"):
            with st.spinner("Analyzing corporate regulatory transmission…"):
                res_exp = service.explain_company_exposure(bill_id, persona=selected_persona)
                st.markdown(res_exp.display_markdown)

    # 5. Market Assessment (Central vs State)
    with tabs[4]:
        st.markdown("#### 📈 Market Impact Assessment")
        st.caption("Translates existing quantitative model outputs into qualitative plain language.")
        if st.button("Explain Market Intelligence", key=f"{key_prefix}_btn_market_{bill_id}"):
            with st.spinner("Translating market intelligence…"):
                res_mkt = service.explain_market_intelligence(bill_id, persona=selected_persona)
                st.markdown(res_mkt.display_markdown)

    # 6. Risk Profile
    with tabs[5]:
        st.markdown("#### ⚠️ Regulatory & Policy Risk Profile")
        if st.button("Explain Risk Classification", key=f"{key_prefix}_btn_risk_{bill_id}"):
            with st.spinner("Analyzing risk tier rationale…"):
                res_risk = service.explain_risk_profile(bill_id, persona=selected_persona)
                st.markdown(res_risk.display_markdown)

    # 7. Anticipation
    with tabs[6]:
        st.markdown("#### 🔍 Pre-Event Pricing-In & Information Diffusion")
        st.caption("Neutral academic interpretation of pre-event price and volume dynamics. Never accusatory.")
        if st.button("Explain Anticipation Dynamics", key=f"{key_prefix}_btn_ant_{bill_id}"):
            with st.spinner("Examining pricing-in indicators…"):
                res_ant = service.explain_anticipation(bill_id, persona=selected_persona)
                st.markdown(res_ant.display_markdown)

    # 8. Ask AI (Free-form conversational Q&A)
    with tabs[7]:
        st.markdown("#### 💬 Ask AI About This Bill")
        st.caption("Ask natural-language questions strictly bounded to this bill's verified facts and records.")

        user_q = st.text_input(
            "Your Question:",
            placeholder="e.g. 'What does this mean for gig workers?', 'Why are private banks exposed?', 'What is the compliance deadline?'",
            key=f"{key_prefix}_q_input_{bill_id}",
        )
        if st.button("Submit Question", key=f"{key_prefix}_btn_submit_q_{bill_id}"):
            if user_q and user_q.strip():
                with st.spinner("Consulting verified legislative intelligence…"):
                    res_q = service.ask_ai(bill_id, user_q.strip(), persona=selected_persona)
                    st.markdown(res_q.display_markdown)
            else:
                st.warning("Please type a question before submitting.")


def render_bill_comparison_ai_panel(
    unified_service: UnifiedLegislativeDiscoveryService,
    current_bill_id: Optional[str] = None,
    key_prefix: str = "comp_ai",
) -> None:
    """
    Render comparative AI analysis between two selected bills.
    """
    ai_service = get_ai_service()
    all_bills = unified_service.get_all_bills()
    if len(all_bills) < 2:
        st.caption("Need at least two bills in repository to compare.")
        return

    bill_dict = {
        b.bill_id: f"{b.display_jurisdiction} {b.title[:45]}… ({b.bill_id})"
        for b in all_bills
    }
    bill_keys = list(bill_dict.keys())

    idx1 = bill_keys.index(current_bill_id) if current_bill_id in bill_keys else 0
    idx2 = 1 if len(bill_keys) > 1 else 0

    st.markdown("### ⚖️ AI Bill Comparison (Cross-Jurisdiction)")
    st.caption("Compare two Central or State bills across provisions, sectors, stakeholders, and regulatory impact.")

    col1, col2 = st.columns(2)
    with col1:
        sel_b1 = st.selectbox(
            "Select Bill 1:",
            options=bill_keys,
            index=idx1,
            format_func=lambda k: bill_dict[k],
            key=f"{key_prefix}_b1",
        )
    with col2:
        sel_b2 = st.selectbox(
            "Select Bill 2:",
            options=bill_keys,
            index=idx2,
            format_func=lambda k: bill_dict[k],
            key=f"{key_prefix}_b2",
        )

    persona = st.selectbox(
        "Comparison Perspective:",
        options=["General Public", "Investor", "Business Owner", "MSME", "Employee", "Industry"],
        index=0,
        key=f"{key_prefix}_persona",
    )

    if not ai_service.client.is_available:
        st.info(
            "AI bill comparison requires `GROQ_API_KEY`. "
            "Please configure the environment variable to enable AI comparative synthesis.",
            icon="ℹ️",
        )
        return

    if st.button("🔬 Compare Bills with AI", key=f"{key_prefix}_btn_compare"):
        if sel_b1 == sel_b2:
            st.warning("Please select two different bills to perform a meaningful comparison.")
            return

        with st.spinner("Synthesizing comparative legislative intelligence via Groq…"):
            res = ai_service.compare_bills(sel_b1, sel_b2, persona=persona)
            st.markdown(res.display_markdown)
