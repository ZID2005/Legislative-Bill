"""
dashboard/components/unified_bill_cards.py
==========================================
Unified Legislative Bill Discovery Card Component.

Renders standardized discovery cards for both Central Parliament and Indian State
legislative bills, displaying:
- Jurisdiction badge ([CENTRAL] or [STATE: Karnataka])
- Authoritative legislative metadata (title, number, house, introduction date)
- Policy domains and economic sectors
- Affected stakeholders
- Corporate exposure metrics
- Market relevance and modeling eligibility
- Field-level provenance indicator
- Action triggers (View Intelligence / Dossier, Official Source, PDF, Related Bills)

STRICT RULE:
Discovery cards represent facts, derived metadata, and eligibility classifications.
They NEVER display predicted stock market returns.
"""

from __future__ import annotations

from typing import Callable, Optional
import streamlit as st

from schemas.unified_bill_record import UnifiedBillRecord


# Market Relevance color map
_MARKET_RELEVANCE_COLORS: dict[str, tuple[str, str]] = {
    "HIGH": ("🔴 High Relevance", "#fee2e2", "#991b1b"),
    "MEDIUM": ("🟠 Medium Relevance", "#ffedd5", "#9a3412"),
    "LOW": ("🟡 Low Relevance", "#fef9c3", "#854d0e"),
    "NONE": ("⚪ Economic-Only", "#f1f5f9", "#475569"),
    "UNKNOWN": ("⚪ Unknown", "#f1f5f9", "#475569"),
}

# Modeling Eligibility color map
_ELIGIBILITY_COLORS: dict[str, tuple[str, str]] = {
    "ELIGIBLE": ("✅ Eligible for Modeling", "#dcfce7", "#166534"),
    "CONDITIONALLY_ELIGIBLE": ("⚠️ Conditionally Eligible", "#fef3c7", "#92400e"),
    "NOT_ELIGIBLE": ("⛔ Not Eligible", "#f1f5f9", "#475569"),
    "INSUFFICIENT_DATA": ("❓ Insufficient Data", "#fee2e2", "#991b1b"),
}


def render_unified_bill_card(
    record: UnifiedBillRecord,
    expanded: bool = False,
    on_select_bill: Optional[Callable[[UnifiedBillRecord], None]] = None,
    related_bills: Optional[list[UnifiedBillRecord]] = None,
) -> None:
    """
    Render a single UnifiedBillRecord as an institutional discovery card.
    """
    # 1. Badge & Title
    if record.is_central:
        jurisdiction_tag = "🏛️ [CENTRAL]"
        header_color = "#1e3a8a"
    else:
        st_name = record.state or "State"
        jurisdiction_tag = f"🇮🇳 [STATE: {st_name}]"
        header_color = "#047857"

    num_str = f" • {record.bill_number}" if record.bill_number else ""
    card_title = f"{jurisdiction_tag} **{record.title}**{num_str}"

    with st.expander(card_title, expanded=expanded):
        # Top Meta Row
        col1, col2, col3 = st.columns([1.2, 1.2, 1.0])

        with col1:
            st.markdown(
                f"📅 **Introduced:** `{record.display_introduction_date}`",
                help="Authoritative legislative tabling date from official gazette/proceedings.",
            )
            st.markdown(f"🏛️ **Legislature:** {record.legislature}")
            st.markdown(f"🏛️ **Chamber / House:** {record.house}")

        with col2:
            status_display = record.status.replace("_", " ").title()
            st.markdown(f"📜 **Status:** `{status_display}`")
            if record.ministry:
                st.markdown(f"🏢 **Ministry / Dept:** {record.ministry}")
            elif record.state:
                st.markdown(f"📍 **State Jurisdiction:** {record.state}")

            pol_dom = record.policy_domain or "General Policy"
            st.markdown(f"📂 **Policy Domain:** `{pol_dom}`")

        with col3:
            rel_label, rel_bg, rel_fg = _MARKET_RELEVANCE_COLORS.get(
                record.market_relevance, ("⚪ " + record.market_relevance, "#f1f5f9", "#475569")
            )
            st.markdown(
                f"<div style='background-color:{rel_bg};color:{rel_fg};padding:4px 8px;border-radius:4px;font-size:0.8rem;font-weight:600;margin-bottom:4px;display:inline-block;'>"
                f"{rel_label}</div>",
                unsafe_allow_html=True,
            )

            elig_label, elig_bg, elig_fg = _ELIGIBILITY_COLORS.get(
                record.modeling_eligibility, ("⚪ " + record.modeling_eligibility, "#f1f5f9", "#475569")
            )
            st.markdown(
                f"<div style='background-color:{elig_bg};color:{elig_fg};padding:4px 8px;border-radius:4px;font-size:0.8rem;font-weight:600;display:inline-block;'>"
                f"{elig_label}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Middle Row: Content, Sectors & Stakeholders
        if record.summary:
            st.markdown(f"**Executive Summary:** {record.summary[:350]}{'…' if len(record.summary) > 350 else ''}")

        c_sec, c_sh, c_corp = st.columns([1, 1, 1])

        with c_sec:
            st.markdown("##### 🏷️ Affected Sectors")
            if record.economic_sectors:
                for sec in record.economic_sectors[:3]:
                    st.markdown(f"- {sec}")
                if len(record.economic_sectors) > 3:
                    st.caption(f"+ {len(record.economic_sectors) - 3} more sectors")
            else:
                st.caption("No statutory sectors mapped")

        with c_sh:
            st.markdown("##### 👥 Key Stakeholders")
            if record.stakeholders:
                for sh in record.stakeholders[:3]:
                    st.markdown(f"- {sh}")
                if len(record.stakeholders) > 3:
                    st.caption(f"+ {len(record.stakeholders) - 3} more stakeholders")
            else:
                st.caption("No stakeholder groups identified")

        with c_corp:
            st.markdown("##### 🏢 Corporate Universe")
            if record.company_exposure_count > 0:
                st.markdown(f"**Total Exposures:** `{record.company_exposure_count}` companies")
                st.markdown(f"**Listed Companies:** `{record.listed_company_exposure_count}` securities")
            else:
                st.caption("No corporate exposure mapped (Public/Civic scope)")

            # Provenance badge
            prov_count = len(record.provenance)
            st.caption(f"🛡️ Provenance: **{record.data_quality}** ({prov_count} audit fields)")

        st.markdown("---")

        # Action Buttons Row
        b1, b2, b3, b4 = st.columns([1.2, 1, 1, 1.2])

        with b1:
            if record.is_central:
                btn_label = "🔍 Bill Intelligence →"
            else:
                btn_label = "🔍 State Dossier →"

            if st.button(btn_label, key=f"btn_sel_{record.bill_id}_{record.jurisdiction}"):
                if on_select_bill:
                    on_select_bill(record)

        with b2:
            if record.source_url:
                st.markdown(f"[🌐 Official Portal]({record.source_url})")
            else:
                st.caption("Portal unavailable")

        with b3:
            if record.has_pdf and record.pdf_url:
                st.markdown(f"[📄 Official PDF]({record.pdf_url})")
            else:
                st.caption("PDF unavailable")

        with b4:
            if related_bills:
                st.caption(f"🔗 **{len(related_bills)}** related bills available")

        # Related Bills expander (if supplied)
        if related_bills:
            with st.expander(f"🔗 Related Bills for {record.title[:30]}…", expanded=False):
                for rb in related_bills:
                    tag = "[CENTRAL]" if rb.is_central else f"[STATE: {rb.state}]"
                    st.markdown(f"- **{tag}** {rb.title} (`{rb.policy_domain or 'General'}`) • *{rb.display_introduction_date}*")
