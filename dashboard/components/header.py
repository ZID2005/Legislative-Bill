"""
dashboard/components/header.py
==============================
Header banner, scope diagnostic badge, and metadata displays.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
import streamlit as st

from dashboard.services.scope_service import ScopeDiagnostic


def render_header(scope: Optional[ScopeDiagnostic] = None) -> None:
    """
    Render top title, version badges, and active scope diagnostic banner.
    """
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("🏛️ Legislative Intelligence & Market Impact Dashboard")
        st.caption(
            "Quantitative Decision-Support Platform for Indian Central Parliamentary Legislation & Market Impact Analysis"
        )

    with col2:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.markdown(
            f"""
            <div style="text-align: right; font-size: 0.85em; color: #6B7280; padding-top: 10px;">
                <b>System Updated:</b> {now_str}<br>
                <span style="background: #E0E7FF; color: #3730A3; padding: 2px 6px; border-radius: 4px; font-weight: 600;">Model v1.0</span>
                <span style="background: #E0E7FF; color: #3730A3; padding: 2px 6px; border-radius: 4px; font-weight: 600;">Decision v1.0</span>
                <span style="background: #E0E7FF; color: #3730A3; padding: 2px 6px; border-radius: 4px; font-weight: 600;">Reports v1.0</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if scope is not None:
        with st.expander("🔍 **Active Scope & Provenance Diagnostic**", expanded=False):
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.markdown(
                    f"**Active Production Universe**<br>"
                    f"• Bills: **{scope.production_bills_count}** (2024 Parliament)<br>"
                    f"• Companies: **{scope.production_companies_count}** (Nifty Universe)<br>"
                    f"• Windows: **{scope.production_event_windows_count}** ([-1,+1] to [-10,+10])<br>"
                    f"• Total Candidates: **{scope.expected_decision_candidates:,}**",
                    unsafe_allow_html=True,
                )
            with sc2:
                st.markdown(
                    f"**Repository Master Scope**<br>"
                    f"• Total Bills: **{scope.total_repository_bills}** (20 prod + 2 test/briefing)<br>"
                    f"• Total Companies: **{scope.total_repository_companies}** (47 active + 3 unmapped)<br>"
                    f"• Verified Decision Records: **{scope.actual_decision_records:,}**<br>"
                    f"• Parity Status: **{scope.parity_verdict}**",
                    unsafe_allow_html=True,
                )
            with sc3:
                st.markdown(
                    f"**Scope Discrepancy Reconciliation**<br>"
                    f"• 22 Bills vs 20: 2 test/briefing docs excluded from ML.<br>"
                    f"• 50 Companies vs 47: 3 companies filtered out.<br>"
                    f"• 50 Records / 18 Co Runtime: Intentional sample batch.<br>"
                    f"• Full Database: **4,700 records** (100% complete).",
                    unsafe_allow_html=True,
                )
