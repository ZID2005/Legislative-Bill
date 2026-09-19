"""
dashboard/components/bill_cards.py
====================================
Task 7.4.1 — Newly Introduced Bill Card components.

Renders rich, informational cards for newly introduced bills, incorporating:
- Legislative metadata (authoritative only)
- Market impact prediction overlays (read-only from decision artifacts)
- Risk and anticipation indicators
"""

from __future__ import annotations

from datetime import date
from typing import Optional

import streamlit as st

from dashboard.services.dashboard_service import BillSummary

# Direction emoji and color mapping
_DIRECTION_CONFIG: dict[str, tuple[str, str]] = {
    "POSITIVE": ("📈", "#22c55e"),
    "NEGATIVE": ("📉", "#ef4444"),
    "NEUTRAL": ("➡️", "#94a3b8"),
}

# Risk category colors
_RISK_COLORS: dict[str, str] = {
    "VERY_LOW": "#22c55e",
    "LOW": "#86efac",
    "MODERATE": "#fbbf24",
    "HIGH": "#f97316",
    "VERY_HIGH": "#ef4444",
}

# Anticipation emoji
_ANTICIPATION_CONFIG: dict[str, tuple[str, str]] = {
    "NO_EVIDENCE": ("🟢", "No evidence"),
    "WEAK_EVIDENCE": ("🟡", "Weak evidence"),
    "MODERATE_EVIDENCE": ("🟠", "Moderate evidence"),
    "STRONG_EVIDENCE": ("🔴", "Strong evidence"),
    "NOT_ANALYZED": ("⚪", "Not analyzed"),
}

# Impact strength labels
_IMPACT_LABELS: dict[str, str] = {
    "VERY_LOW": "Very Low",
    "LOW": "Low",
    "MEDIUM": "Medium",
    "HIGH": "High",
    "VERY_HIGH": "Very High",
}


def render_bill_card(summary: BillSummary, expanded: bool = False) -> None:
    """
    Render a single newly-introduced bill as an expandable card.

    Shows all 11 key questions from the product vision:
    1. Bill title + number
    2. What the bill does (description)
    3. Bill type/category
    4. Introduction date (authoritative legislative date)
    5. House of introduction
    6. Ministry/department
    7. Affected sectors and company count
    8. Predicted direction (if available)
    9. Market-moving probability (if available)
    10. Impact strength (if available)
    11. Risk category + anticipation evidence (if available)
    """
    # Build card header
    intro_str = (
        summary.introduction_date.strftime("%d %b %Y")
        if summary.introduction_date
        else "Date not available"
    )
    direction_emoji = ""
    if summary.has_prediction and summary.predicted_direction:
        cfg = _DIRECTION_CONFIG.get(summary.predicted_direction, ("", ""))
        direction_emoji = cfg[0] + " "

    header = f"{direction_emoji}**{summary.title}**"

    with st.expander(header, expanded=expanded):
        # Top row: metadata chips
        col_meta1, col_meta2, col_meta3 = st.columns([1, 1, 1])
        with col_meta1:
            st.markdown(
                f"📅 **Introduced:** {intro_str}",
                help="Authoritative legislative introduction date from parliamentary records",
            )
            st.markdown(f"🏛️ **House:** {summary.house}")
        with col_meta2:
            st.markdown(f"🏢 **Ministry:** {summary.ministry}")
            cat_label = "System-derived Category"
            st.markdown(
                f"📂 **{cat_label}:** {summary.bill_category}",
                help="System-derived policy/sector category inferred from ministry and legislative text mapping.",
            )
        with col_meta3:
            st.markdown(f"⚖️ **Status:** {summary.status}")
            if summary.bill_number:
                st.markdown(f"🔢 **Bill No.:** {summary.bill_number}")


        st.markdown("---")

        # Description
        if summary.description:
            st.markdown("**📋 Description:**")
            desc = summary.description
            if len(desc) > 350:
                desc = desc[:350] + "…"
            st.markdown(f"> {desc}")
        else:
            st.caption("_Short description not available._")

        st.markdown("---")

        # Sector & Company exposure row
        sec_col, comp_col = st.columns([2, 1])
        with sec_col:
            if summary.sectors:
                sector_str = ", ".join(summary.sectors[:5])
                st.markdown(f"🏭 **Affected Sectors:** {sector_str}")
            else:
                st.markdown("🏭 **Affected Sectors:** Not available")
        with comp_col:
            if summary.affected_company_count > 0:
                st.metric(
                    "Affected Companies",
                    str(summary.affected_company_count),
                    help="Companies with decision records for this bill",
                )
            else:
                st.caption("Company mapping: Not available")

        # Market Impact section
        if summary.has_prediction or summary.has_decision_support:
            st.markdown("**📊 Market Impact Intelligence** *(read-only from pipeline)*")
            imp_cols = st.columns(4)

            with imp_cols[0]:
                if summary.has_prediction and summary.predicted_direction:
                    dir_emoji, dir_color = _DIRECTION_CONFIG.get(
                        summary.predicted_direction, ("➡️", "#94a3b8")
                    )
                    st.markdown(
                        f"<div style='text-align:center;'>"
                        f"<div style='font-size:1.5rem;'>{dir_emoji}</div>"
                        f"<div style='color:{dir_color};font-weight:600;font-size:0.9rem;'>"
                        f"{summary.predicted_direction}</div>"
                        f"<div style='color:#64748b;font-size:0.75rem;'>Direction</div></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Direction: N/A")

            with imp_cols[1]:
                if summary.has_prediction and summary.market_moving_probability is not None:
                    prob_pct = summary.market_moving_probability * 100
                    st.markdown(
                        f"<div style='text-align:center;'>"
                        f"<div style='font-size:1.4rem;font-weight:700;color:#3b82f6;'>"
                        f"{prob_pct:.1f}%</div>"
                        f"<div style='color:#64748b;font-size:0.75rem;'>Market Moving P</div></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Mkt Moving P: N/A")

            with imp_cols[2]:
                if summary.has_prediction and summary.impact_strength:
                    label = _IMPACT_LABELS.get(summary.impact_strength, summary.impact_strength)
                    st.markdown(
                        f"<div style='text-align:center;'>"
                        f"<div style='font-size:1.2rem;font-weight:600;'>{label}</div>"
                        f"<div style='color:#64748b;font-size:0.75rem;'>Impact Strength</div></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Impact: N/A")

            with imp_cols[3]:
                if summary.has_decision_support and summary.risk_category:
                    risk_color = _RISK_COLORS.get(summary.risk_category, "#94a3b8")
                    st.markdown(
                        f"<div style='text-align:center;'>"
                        f"<div style='background:{risk_color};color:white;border-radius:6px;"
                        f"padding:4px 8px;font-weight:600;font-size:0.9rem;'>"
                        f"{summary.risk_category.replace('_', ' ')}</div>"
                        f"<div style='color:#64748b;font-size:0.75rem;margin-top:4px;'>Risk Category</div></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Risk: N/A")

        else:
            st.info(
                "Market impact data not available for this bill.",
                icon="ℹ️",
            )

        # Anticipation evidence
        if summary.has_anticipation and summary.anticipation_class:
            ant_emoji, ant_label = _ANTICIPATION_CONFIG.get(
                summary.anticipation_class, ("⚪", "Unknown")
            )
            st.markdown(
                f"**🔍 Anticipation Evidence:** {ant_emoji} {ant_label} "
                f"*(pre-event market activity signal — see methodology for interpretation)*"
            )

        # Source URL
        if summary.url:
            st.markdown(f"🔗 [View on PRS India]({summary.url})")


def render_bill_mini_card(summary: BillSummary) -> None:
    """
    Render a compact horizontal bill card for list views.
    Used in the main bills feed when showing many bills at once.
    """
    intro_str = (
        summary.introduction_date.strftime("%d %b %Y")
        if summary.introduction_date
        else "—"
    )

    direction_emoji = "➡️"
    direction_color = "#94a3b8"
    if summary.has_prediction and summary.predicted_direction:
        cfg = _DIRECTION_CONFIG.get(summary.predicted_direction, ("➡️", "#94a3b8"))
        direction_emoji, direction_color = cfg

    risk_badge = ""
    if summary.has_decision_support and summary.risk_category:
        risk_color = _RISK_COLORS.get(summary.risk_category, "#94a3b8")
        risk_badge = (
            f"<span style='background:{risk_color};color:white;border-radius:4px;"
            f"padding:2px 6px;font-size:0.72rem;margin-left:6px;'>"
            f"{summary.risk_category.replace('_', ' ')}</span>"
        )

    st.markdown(
        f"""
        <div style="border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;
                    margin-bottom:8px;background:#fafafa;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div style="flex:1;">
              <div style="font-weight:600;font-size:0.95rem;color:#1e293b;">
                {summary.title}
              </div>
              <div style="color:#64748b;font-size:0.8rem;margin-top:4px;">
                📅 {intro_str} &nbsp;|&nbsp; 🏢 {summary.ministry}
                &nbsp;|&nbsp; ⚖️ {summary.status}
              </div>
              <div style="color:#64748b;font-size:0.8rem;margin-top:2px;">
                📂 {summary.bill_category} &nbsp;|&nbsp;
                🏭 {', '.join(summary.sectors[:2]) if summary.sectors else 'Not specified'}
                &nbsp;|&nbsp; 🏢 {summary.affected_company_count} companies
              </div>
            </div>
            <div style="text-align:right;min-width:100px;">
              <div style="font-size:1.4rem;color:{direction_color};">{direction_emoji}</div>
              {risk_badge}
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_no_bills_message(period_label: str = "this period") -> None:
    """Display a clear 'no bills' message when no results match the date filter."""
    st.info(
        f"No bills introduced in {period_label}. "
        "Adjust the date range filter to see bills from a different period.",
        icon="📋",
    )
