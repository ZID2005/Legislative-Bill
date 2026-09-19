"""
dashboard/pages/india_explorer.py
=================================
Task 8.9 — India Legislative Explorer page.

Unified discovery experience across Central Government Parliament and
Indian State legislative assemblies:
- Central and State discovery from one place
- Jurisdiction and state filtering
- Deterministic multi-attribute search
- Explore India taxonomy quick-filters
- State coverage transparency (4 implemented, 24 planned)
- Discovery cards with provenance and market-modeling eligibility
- Seamless detail routing (Central → Bill Intelligence, State → State Dossier)
- Zero State predictions guarantee
"""

from __future__ import annotations

from typing import Optional
import pandas as pd
import streamlit as st

from dashboard.components.unified_bill_cards import render_unified_bill_card
from dashboard.components.ai_explanation_panel import (
    render_ai_explanation_panel,
    render_bill_comparison_ai_panel,
)
from schemas.unified_bill_record import UnifiedBillRecord
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from storage.state_knowledge_repository import StateKnowledgeRepository


def render_india_explorer_page(
    discovery_service: Optional[UnifiedLegislativeDiscoveryService] = None,
) -> None:
    """Render the comprehensive India Legislative Explorer page."""
    if discovery_service is None:
        discovery_service = UnifiedLegislativeDiscoveryService()

    st.markdown("<h1 style='margin-bottom:0;'>🏛️ India Legislative Explorer</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#64748b;font-size:1.05rem;margin-top:4px;'>"
        "Unified discovery and search layer across Central Parliament and Indian State Legislatures.</p>",
        unsafe_allow_html=True,
    )

    stats = discovery_service.get_statistics()
    coverage_info = discovery_service.get_state_coverage()

    # 1. Top Metrics Banner
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Bills", f"{stats['total_unified_records']:,}")
    with m2:
        st.metric("Central Bills", f"{stats['central_records']}")
    with m3:
        st.metric("State Bills", f"{stats['state_records']}")
    with m4:
        st.metric("States Implemented", f"{coverage_info['implemented_count']} / 28")
    with m5:
        st.metric("With Corporate Exposure", f"{stats['records_with_company_exposure']}")

    # 2. Transparent State Coverage Expander
    with st.expander("🗺️ State Legislative Coverage & Architecture Roadmap", expanded=False):
        c_imp, c_plan = st.columns([1, 1])
        with c_imp:
            st.markdown("#### ✅ Implemented States (Active Pilot)")
            for entry in coverage_info["implemented_states"]:
                st.markdown(f"- **{entry['state']}**: `{entry['bills_count']}` bills ({entry['source']})")
        with c_plan:
            st.markdown(f"#### ⏳ Planned States ({coverage_info['planned_count']} States & UTs)")
            planned_names = [e["state"] for e in coverage_info["planned_states"]]
            st.caption(", ".join(planned_names[:12]) + f" and {len(planned_names) - 12} more…")
            st.info(
                "Planned states are represented transparently in the architecture and have not yet had "
                "bills ingested. No fake data is generated for un-ingested states.",
                icon="ℹ️",
            )

    # AI Bill Comparison Assistant
    with st.expander("⚖️ AI Bill Comparison Assistant (Central & State)", expanded=False):
        render_bill_comparison_ai_panel(discovery_service, key_prefix="explorer_ai_comp")

    # 3. Explore India Categories
    st.markdown("### 🧭 Explore India")
    cat_options = ["All Bills"] + discovery_service.get_explore_categories()
    selected_category = st.selectbox(
        "Browse by policy area or legislative scope:",
        options=cat_options,
        index=0,
        key="explore_india_category_select",
    )

    # 4. Search and Filters Row
    c_search, c_jur, c_state = st.columns([2.5, 1, 1])

    with c_search:
        search_query = st.text_input(
            "🔍 Search Legislative Bills",
            placeholder="Search title, bill #, company (e.g. 'Swiggy', 'Zomato'), sector, or activity (e.g. 'gig economy', 'ports')…",
            key="india_explorer_search_query",
        )

    with c_jur:
        jur_choice = st.selectbox(
            "Jurisdiction",
            options=["All", "Central", "State"],
            index=0,
            key="india_explorer_jurisdiction",
        )

    with c_state:
        state_options = ["All"] + sorted([e["state"] for e in coverage_info["implemented_states"]])
        state_choice = st.selectbox(
            "State (when applicable)",
            options=state_options,
            index=0,
            key="india_explorer_state",
        )

    # Advanced Filters Expander
    with st.expander("⚙️ Advanced Metadata & Modeling Filters", expanded=False):
        f1, f2, f3, f4, f5 = st.columns([1, 1, 1, 1.2, 1.2])
        with f1:
            market_rel_options = ["All", "HIGH", "MEDIUM", "LOW", "NONE"]
            sel_market_rel = st.selectbox("Market Relevance", options=market_rel_options, index=0)
        with f2:
            elig_options = ["All", "ELIGIBLE", "CONDITIONALLY_ELIGIBLE", "NOT_ELIGIBLE", "INSUFFICIENT_DATA"]
            sel_elig = st.selectbox("Modeling Eligibility", options=elig_options, index=0)
        with f3:
            corp_exposure_options = ["All", "With Company Exposure", "Without Exposure"]
            sel_corp_exp = st.selectbox("Corporate Exposure", options=corp_exposure_options, index=0)
        with f4:
            sel_comp = st.text_input("🏢 Company Filter", placeholder="e.g. Swiggy, Zomato, KSEB", key="explorer_filter_comp")
        with f5:
            sort_by = st.selectbox(
                "Sort Results",
                options=["Introduction Date (Newest)", "Title (A-Z)", "Company Exposure (High-Low)"],
                index=0,
            )

    # 5. Execute Query & Filtering
    # Base category filtering if selected
    if selected_category and selected_category != "All Bills":
        cat_bills = discovery_service.get_bills_by_category(selected_category)
        cat_bill_ids = {b.bill_id for b in cat_bills}
    else:
        cat_bill_ids = None

    # Corp exposure flag
    corp_flag = None
    if sel_corp_exp == "With Company Exposure":
        corp_flag = True
    elif sel_corp_exp == "Without Exposure":
        corp_flag = False

    # Execute search
    results = discovery_service.search(
        query=search_query,
        jurisdiction=jur_choice.lower() if jur_choice != "All" else None,
        state=state_choice if state_choice != "All" else None,
        market_relevance=sel_market_rel if sel_market_rel != "All" else None,
        modeling_eligibility=sel_elig if sel_elig != "All" else None,
        has_company_exposure=corp_flag,
        company=sel_comp.strip() if sel_comp and sel_comp.strip() else None,
    )

    # If category filter was applied, intersect
    if cat_bill_ids is not None:
        results = [b for b in results if b.bill_id in cat_bill_ids]

    # Apply sorting
    if sort_by == "Introduction Date (Newest)":
        results.sort(key=lambda b: (1 if b.introduction_date else 0, b.introduction_date or ""), reverse=True)
    elif sort_by == "Title (A-Z)":
        results.sort(key=lambda b: b.title.lower())
    elif sort_by == "Company Exposure (High-Low)":
        results.sort(key=lambda b: b.company_exposure_count, reverse=True)

    # 6. Results Header & View Toggle
    st.markdown("---")
    c_res_count, c_view_toggle = st.columns([3, 1])

    with c_res_count:
        st.markdown(f"#### Results ({len(results)} bills found)")

    with c_view_toggle:
        view_mode = st.radio("View Mode:", options=["Cards", "Table"], horizontal=True, key="india_explorer_view_mode")

    # 7. Check for Selected State Bill to Render State Dossier
    selected_state_bill_id = st.session_state.get("selected_unified_state_bill_id")

    def _select_bill(record: UnifiedBillRecord) -> None:
        if record.is_central:
            st.session_state["selected_bill_id"] = record.bill_id
            st.session_state["nav_override"] = "🔍 Bill Intelligence"
            st.rerun()
        else:
            st.session_state["selected_unified_state_bill_id"] = record.bill_id
            st.rerun()

    if selected_state_bill_id:
        _render_state_dossier_panel(selected_state_bill_id)

    # 8. Render Results
    if not results:
        st.info("No legislative bills matched the selected criteria. Try broadening your search or filters.", icon="ℹ️")
        return

    if view_mode == "Cards":
        for rec in results:
            related = discovery_service.get_related_bills(rec.bill_id, limit=3)
            render_unified_bill_card(
                record=rec,
                expanded=False,
                on_select_bill=_select_bill,
                related_bills=related,
            )
    else:
        # Table view
        table_rows = []
        for r in results:
            table_rows.append({
                "Jurisdiction": r.display_jurisdiction,
                "Title": r.title,
                "Bill #": r.bill_number or "—",
                "Introduced": r.display_introduction_date,
                "Chamber": r.house,
                "Policy Domain": r.policy_domain or "—",
                "Status": r.status.replace("_", " ").title(),
                "Exposures": r.company_exposure_count,
                "Market Relevance": r.market_relevance,
                "Modeling Eligibility": r.modeling_eligibility,
            })
        df_display = pd.DataFrame(table_rows)
        st.dataframe(df_display, use_container_width=True, hide_index=True)


def _render_state_dossier_panel(bill_id: str) -> None:
    """Render comprehensive state legislative dossier when a state bill is selected."""
    repo = StateKnowledgeRepository()
    record = repo.get(bill_id)
    if not record:
        st.warning(f"State bill record for '{bill_id}' not found.")
        return

    st.markdown("---")
    st.markdown(f"### 📋 State Legislative Dossier: {record.title}")
    st.caption(f"State: **{record.state}** • Legislature: **{record.chamber}** • Bill #: **{record.bill_number or 'N/A'}**")

    # Important Academic Disclaimer
    st.warning(
        "**Strict Isolation Notice:** This Indian State legislative bill is part of the validated State Knowledge & Economic Layer. "
        "State legislative bills are strictly isolated from Central stock market predictions. State predictions remain **strictly 0**.",
        icon="⚠️",
    )

    d1, d2 = st.columns([2, 1])

    with d1:
        st.markdown("#### 📜 Grounded Plain-Language Summary")
        if record.summary:
            st.markdown(f"**What is this Bill?** {record.summary.what_is_bill}")
            st.markdown(f"**What does it change?** {record.summary.what_it_changes}")
            if record.summary.why_it_matters:
                st.markdown(f"**Why does it matter?** {record.summary.why_it_matters}")
            if record.summary.who_is_affected:
                st.markdown(f"**Who is affected?** {record.summary.who_is_affected}")

        if record.key_provisions:
            st.markdown("#### ⚖️ Key Statutory Provisions")
            for p in record.key_provisions[:5]:
                st.markdown(f"- {p}")

    with d2:
        st.markdown("#### 🔍 Modeling & Impact Assessment")
        ia = record.impact_assessment
        if ia:
            st.markdown(f"**Economic Direction:** `{ia.economic_direction.upper()}`")
            st.markdown(f"**Economic Strength:** `{ia.economic_strength}`")
            st.markdown(f"**Market Relevance:** `{ia.market_relevance}`")
            st.markdown(f"**Modeling Eligibility:** `{ia.modeling_eligibility}`")
            st.markdown(f"**Data Sufficiency:** `{ia.data_sufficiency}`")
            st.markdown(f"**Event Date Quality:** `{ia.event_date_quality}`")
        else:
            st.caption("Detailed impact assessment not available.")

        if record.corporate_exposures:
            st.markdown(f"#### 🏢 Corporate Exposures ({len(record.corporate_exposures)})")
            for exp in record.corporate_exposures[:4]:
                st.markdown(f"- **{exp.company_name}** ({exp.ticker or 'Unlisted'}) • *{exp.direct_indirect}*")
            if len(record.corporate_exposures) > 4:
                st.caption(f"+ {len(record.corporate_exposures) - 4} more exposures mapped")
        else:
            st.caption("No mapped corporate securities for this state statute.")

    st.markdown("---")
    with st.expander("🤖 Ask AI & Generate Plain-Language Intelligence (Groq)", expanded=False):
        render_ai_explanation_panel(
            bill_id=record.bill_id,
            default_persona="General Public",
            key_prefix=f"state_ai_{record.bill_id}",
        )

    if st.button("✖️ Close State Dossier", key="btn_close_state_dossier"):
        st.session_state.pop("selected_unified_state_bill_id", None)
        st.rerun()
