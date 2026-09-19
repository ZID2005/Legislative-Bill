"""
dashboard/components/cards.py
================================
Task 7.4.1 — Summary metric cards and KPI panels for the dashboard.

Provides reusable, styled metric display components for:
- KPI summary header cards (bill count, company count, predictions, etc.)
- Scope diagnostic panel
- Market impact summary cards
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from dashboard.services.dashboard_service import ProductionScope


def render_kpi_header(scope: ProductionScope, df: pd.DataFrame) -> None:
    """
    Render the top-level KPI metric cards for the dashboard overview.

    Displays:
    - Total Production Bills
    - Recently Introduced Bills (last 30 days from df)
    - Total Mapped Companies
    - Prediction / Decision Records
    - Decision-Support Records
    - Anticipation Records
    - Stakeholder Reports
    - Bills with Strong Anticipation Evidence
    """
    st.markdown("### 📊 System Overview")

    # Row 1: Core legislative + company scope
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.metric(
            label="🏛️ Production Bills",
            value=str(scope.production_bills_count),
            delta=f"{scope.total_bills_in_repo} in repo ({len(scope.non_legislative_bills)} excluded)",
            help=(
                "Authoritative count of legislative bills in the 2024 parliamentary session. "
                f"Excludes {', '.join(scope.non_legislative_bills)} (non-legislative stubs)."
            ),
        )

    with c2:
        st.metric(
            label="🏢 Mapped Companies",
            value=str(scope.production_companies_count),
            delta=f"{scope.total_companies_in_repo} in repo",
            help=(
                f"{scope.total_companies_in_repo} total company records. "
                f"{len(scope.excluded_companies)} excluded due to insufficient market data."
            ),
        )

    with c3:
        st.metric(
            label="🔗 Bill-Company Pairs",
            value=f"{scope.production_bill_company_pairs:,}",
            delta=f"{scope.production_bills_count} bills × {scope.production_companies_count} cos",
            help="Total bill-company analytical pairs across the production universe.",
        )

    with c4:
        st.metric(
            label="📈 Predictions",
            value=f"{scope.production_prediction_records:,}",
            delta="940 pairs × 5 windows",
            help="Forward-looking multi-target prediction records.",
        )

    with c5:
        st.metric(
            label="🔮 Decision Records",
            value=f"{scope.production_decision_records:,}",
            delta="940 pairs × 5 windows",
            help="Total decision-support records covering all bill-company-event-window combinations.",
        )

    # Row 2: Intelligence metrics
    c6, c7, c8, c9 = st.columns(4)

    n_bills_in_df = df["bill_id"].nunique() if not df.empty and "bill_id" in df.columns else 0
    mean_mmp = df["market_moving_probability"].mean() if not df.empty and "market_moving_probability" in df.columns else 0.0
    positive = int((df["predicted_direction"] == "POSITIVE").sum()) if not df.empty and "predicted_direction" in df.columns else 0
    negative = int((df["predicted_direction"] == "NEGATIVE").sum()) if not df.empty and "predicted_direction" in df.columns else 0

    with c6:
        st.metric(
            label="📋 Stakeholder Reports",
            value=f"{scope.production_report_records:,}",
            delta="Investor + Business + Public",
            help="3 stakeholder-perspective reports per decision record (4,700 × 3 = 14,100).",
        )

    with c7:
        st.metric(
            label="🆕 Anticipation Records",
            value=f"{scope.production_anticipation_records:,}",
            delta=(
                f"✅ Available"
                if scope.production_anticipation_records > 0
                else "⚠️ Not loaded"
            ),
            help="Pre-event market anticipation/pricing-in diffusion records (940 pairs).",
        )

    with c8:
        st.metric(
            label="🔴 Strong Anticipation Bills",
            value=str(scope.strong_anticipation_bills),
            delta="Bills with pricing-in evidence",
            help=(
                "Bills where pre-event market activity shows STRONG_EVIDENCE of "
                "anticipatory pricing. See Anticipation Overview for details."
            ),
        )

    with c9:
        st.metric(
            label="📈 Market Predictions",
            value=f"{positive:,} Pos / {negative:,} Neg",
            delta=f"of {len(df):,} records ({positive/max(len(df),1)*100:.1f}% positive)" if not df.empty else "—",
            help="Directional breakdown across active decision records.",
        )


def render_scope_diagnostic_card(scope: ProductionScope) -> None:
    """
    Render a scope provenance panel showing verified production counts
    and any discrepancies with clear explanations.
    """
    st.markdown("### 🔬 Production Scope & Data Provenance")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown(
            f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;
                        border-radius:8px;padding:16px;">
              <h4 style="margin-top:0;color:#1e293b;">Production Dataset Scope</h4>
              <p>• <b>{scope.production_bills_count} Production Bills</b>: Verified 2024 parliamentary bills.</p>
              <p>• <b>{scope.production_companies_count} Production Companies</b>: BSE/NSE-listed entities with complete market datasets.</p>
              <p>• <b>{scope.production_bill_company_pairs:,} Bill-Company Pairs</b>: Exactly 20 bills × 47 companies.</p>
              <p>• <b>5 Event Windows</b>: <code>[-30,-1]</code>, <code>[-5,+5]</code>, <code>[0,+1]</code>, <code>[0,+5]</code>, <code>[0,+20]</code>.</p>
              <p>• <b>{scope.production_prediction_records:,} Prediction Records</b>: Multi-target machine learning outputs (940 × 5).</p>
              <p>• <b>{scope.production_decision_records:,} Decision Records</b>: Risk &amp; decision support scores (940 × 5).</p>
              <p>• <b>{scope.production_anticipation_records:,} Anticipation Records</b>: Pre-event diffusion analyses across all 940 pairs.</p>
              <p>• <b>{scope.production_report_records:,} Stakeholder Reports</b>: Multi-stakeholder dossiers (4,700 × 3 lenses).</p>
              <p style="color:green;font-weight:600;">✅ {scope.scope_integrity_verdict}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        excl_bills = ", ".join(scope.non_legislative_bills) or "None"
        st.markdown(
            f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;
                        border-radius:8px;padding:16px;">
              <h4 style="margin-top:0;color:#1e293b;">Scope Reconciliation Notes</h4>
              <p>• <b>{scope.total_bills_in_repo} vs {scope.production_bills_count} Bills</b>:
                 {len(scope.non_legislative_bills)} non-legislative files excluded:
                 <code>{excl_bills}</code>.</p>
              <p>• <b>{scope.total_companies_in_repo} vs {scope.production_companies_count} Companies</b>:
                 {len(scope.excluded_companies)} companies excluded (insufficient market liquidity / trading history).</p>
              <p>• <b>Reconciliation with Earlier Pilot Counts</b>:
                 Earlier reported 10 companies / 60 pairs was an isolated banking pilot. True production scope is 940 pairs &amp; 4,700 records.</p>
              <p>• <b>Anticipation Records</b>: {scope.production_anticipation_records:,} records.
                 {scope.strong_anticipation_bills} bills show STRONG_EVIDENCE of pre-event pricing-in.</p>
              <p style="color:#0ea5e9;font-size:0.85rem;">
                 Data source: BillRepository + CompanyRepository + DecisionRepository + AnticipationRepository
              </p>
            </div>
            """,
            unsafe_allow_html=True,
        )



def render_market_impact_cards(stats: dict[str, Any]) -> None:
    """
    Render high-level market impact summary from pre-computed statistics.
    Does NOT calculate predictions — reads stored outputs only.
    """
    if not stats or stats.get("total_records", 0) == 0:
        st.warning("Market impact statistics not available.", icon="⚠️")
        return

    st.markdown("### 📊 Market Impact Distribution *(read-only)*")
    total = stats["total_records"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        pos = stats.get("positive_count", 0)
        st.metric(
            "📈 Positive",
            f"{pos:,}",
            f"{pos/max(total,1)*100:.1f}%",
            delta_color="normal",
        )
    with c2:
        neg = stats.get("negative_count", 0)
        st.metric(
            "📉 Negative",
            f"{neg:,}",
            f"{neg/max(total,1)*100:.1f}%",
            delta_color="inverse",
        )
    with c3:
        neu = stats.get("neutral_count", 0)
        st.metric(
            "➡️ Neutral",
            f"{neu:,}",
            f"{neu/max(total,1)*100:.1f}%",
            delta_color="off",
        )
    with c4:
        mmp = stats.get("mean_market_moving_prob", 0.0)
        st.metric(
            "⚡ Mean Mkt Moving P",
            f"{mmp:.3f}",
            "Range: 0.0→1.0",
            delta_color="off",
        )
