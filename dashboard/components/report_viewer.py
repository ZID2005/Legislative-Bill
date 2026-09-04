"""
dashboard/components/report_viewer.py
=====================================
Formatted viewer for Task 7.3 stakeholder, bill-level, and company-level reports.
"""

from __future__ import annotations

import json
from typing import Any, Optional
import pandas as pd
import streamlit as st

from dashboard.utils.export import to_json_bytes
from schemas.report import BillLevelReport, CompanyLevelReport, StakeholderReport


def render_stakeholder_report(report: Optional[StakeholderReport]) -> None:
    """
    Render formatted view of an individual StakeholderReport.
    """
    if report is None:
        st.info("No report generated for this candidate. Use filters to select an existing report.")
        return

    st.markdown(f"### 📄 Stakeholder Report: `{report.report_id}`")
    st_val = report.stakeholder_type.value if hasattr(report.stakeholder_type, "value") else str(report.stakeholder_type)
    st.caption(
        f"**Type**: {st_val.upper()} | "
        f"**Bill**: {report.bill_id} | "
        f"**ISIN**: {report.company_isin} | "
        f"**Window**: {report.event_window} | "
        f"**Version**: {report.report_version}"
    )

    tab_narrative, tab_sections, tab_json = st.tabs(["📝 Executive Narrative", "📊 Key Sections", "⚙️ Raw Schema JSON"])

    with tab_narrative:
        st.markdown(f"#### Executive Summary")
        st.info(report.executive_summary)

        if st_val.upper() == "INVESTOR":
            st.markdown("#### Key Investment & Market Factors")
            if getattr(report, "key_factors", None):
                for f in report.key_factors:
                    st.markdown(f"• {f}")
            else:
                st.caption("No specific key factors annotated.")

        discs = getattr(report, "disclaimers", None) or ([report.disclaimer] if getattr(report, "disclaimer", None) else [])
        if discs:
            st.markdown("#### Disclaimers & Regulatory Notices")
            for d in discs:
                st.caption(f"⚖️ {d}")

    with tab_sections:
        if getattr(report, "impact_summary", None):
            with st.expander("📈 Impact Summary", expanded=True):
                st.markdown(report.impact_summary)
        if getattr(report, "risk_summary", None):
            with st.expander("⚡ Risk Summary", expanded=True):
                st.markdown(report.risk_summary)
        if getattr(report, "anticipation_summary", None):
            with st.expander("🛡️ Anticipation & Pricing-In Summary", expanded=True):
                st.markdown(report.anticipation_summary)
        if getattr(report, "confidence_summary", None):
            with st.expander("🎯 Confidence Summary", expanded=False):
                st.markdown(report.confidence_summary)
        if getattr(report, "methodology_note", None):
            with st.expander("📐 Methodology Note", expanded=False):
                st.markdown(report.methodology_note)
        if getattr(report, "sections", None):
            for title, content in report.sections.items():
                with st.expander(f"📌 {title}", expanded=True):
                    if isinstance(content, (dict, list)):
                        st.json(content)
                    else:
                        st.markdown(str(content))

    with tab_json:
        report_dict = report.to_dict()
        st.json(report_dict)
        st.download_button(
            label="⬇️ Download Report JSON",
            data=to_json_bytes(report_dict),
            file_name=f"{report.report_id}.json",
            mime="application/json",
        )


def render_bill_report(bill_report: Optional[BillLevelReport]) -> None:
    """Render formatted view of a BillLevelReport."""
    if bill_report is None:
        st.info("No bill-level aggregation report found.")
        return

    st.markdown(f"### 📜 Bill Summary Report: `{bill_report.bill_id}`")
    st.caption(f"**Title**: {bill_report.bill_title} | **Window**: {getattr(bill_report, 'event_window', 'All')}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Affected Companies", f"{bill_report.total_companies}")
    c2.metric("Mean Impact Score", f"{bill_report.avg_impact_score:.4f}")
    c3.metric("Mean Risk Score", f"{bill_report.avg_risk_score:.4f}")
    c4.metric("Market-Moving Count", f"{bill_report.market_moving_count}")

    summary_text = getattr(bill_report, "executive_summary", "")
    if summary_text:
        st.markdown("#### Executive Summary")
        st.info(summary_text)

    comp_summaries = getattr(bill_report, "company_summaries", None) or getattr(bill_report, "affected_companies", [])
    if comp_summaries:
        st.markdown("#### Affected Companies Detail")
        df_aff = pd.DataFrame(comp_summaries)
        st.dataframe(df_aff, use_container_width=True)

    st.download_button(
        label="⬇️ Download Bill Report JSON",
        data=to_json_bytes(bill_report.to_dict()),
        file_name=f"bill_report_{bill_report.bill_id}.json",
        mime="application/json",
    )


def render_company_report(comp_report: Optional[CompanyLevelReport]) -> None:
    """Render formatted view of a CompanyLevelReport."""
    if comp_report is None:
        st.info("No company-level aggregation report found.")
        return

    sector_name = getattr(comp_report, "company_sector", getattr(comp_report, "sector", "Unknown"))
    st.markdown(f"### 🏢 Company Summary Report: `{comp_report.company_name}`")
    st.caption(f"**ISIN**: {comp_report.company_isin} | **Sector**: {sector_name}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Relevant Bills", f"{comp_report.total_bills}")
    c2.metric("Mean Impact Score", f"{comp_report.avg_impact_score:.4f}")
    c3.metric("Mean Risk Score", f"{comp_report.avg_risk_score:.4f}")
    c4.metric("Net Positive Bills", f"{comp_report.positive_bill_count}")

    comp_summary = getattr(comp_report, "executive_summary", "")
    if comp_summary:
        st.markdown("#### Executive Summary")
        st.info(comp_summary)

    bill_exposures = getattr(comp_report, "bill_summaries", None) or getattr(comp_report, "bill_exposures", [])
    if bill_exposures:
        st.markdown("#### Legislative Exposures Detail")
        df_exp = pd.DataFrame(bill_exposures)
        st.dataframe(df_exp, use_container_width=True)

    st.download_button(
        label="⬇️ Download Company Report JSON",
        data=to_json_bytes(comp_report.to_dict()),
        file_name=f"company_report_{comp_report.company_isin}.json",
        mime="application/json",
    )
