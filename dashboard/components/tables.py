"""
dashboard/components/tables.py
================================
Task 7.4.1 — Reusable data tables for the dashboard.

Provides styled, sortable, filterable data tables for:
- Company exposure table
- Decision records summary table
- Bill-level summary table
"""

from __future__ import annotations

from typing import Optional

import pandas as pd
import streamlit as st


# Display column configs for different table types
_DIRECTION_DISPLAY = {
    "POSITIVE": "📈 Positive",
    "NEGATIVE": "📉 Negative",
    "NEUTRAL": "➡️ Neutral",
}

_RISK_DISPLAY = {
    "VERY_LOW": "🟢 Very Low",
    "LOW": "🟢 Low",
    "MODERATE": "🟡 Moderate",
    "HIGH": "🟠 High",
    "VERY_HIGH": "🔴 Very High",
}

_ANTICIPATION_DISPLAY = {
    "NO_EVIDENCE": "🟢 No Evidence",
    "WEAK_EVIDENCE": "🟡 Weak",
    "MODERATE_EVIDENCE": "🟠 Moderate",
    "STRONG_EVIDENCE": "🔴 Strong",
    "NOT_ANALYZED": "⚪ Not Analyzed",
}


def render_company_exposure_table(
    df: pd.DataFrame,
    max_rows: int = 200,
    search_term: Optional[str] = None,
) -> None:
    """
    Render the Company Exposure table with formatting.

    Columns: Company | Sector | Bill | Direction | Market Moving | Impact | Confidence | Risk | Anticipation

    Parameters
    ----------
    df : pd.DataFrame
        Output of DashboardService.get_company_exposure_table()
    max_rows : int
        Maximum rows to display (performance guard)
    search_term : str, optional
        Free-text search filter applied to company_name and bill_title columns
    """
    if df.empty:
        st.info("No company exposure data available for the selected filters.", icon="ℹ️")
        return

    display_df = df.copy()

    # Apply search filter
    if search_term:
        mask = pd.Series(False, index=display_df.index)
        for col in ["company_name", "bill_title", "ticker", "sector"]:
            if col in display_df.columns:
                mask |= display_df[col].astype(str).str.contains(
                    search_term, case=False, na=False
                )
        display_df = display_df[mask]

    if display_df.empty:
        st.info(f"No results matching '{search_term}'.", icon="🔍")
        return

    # Format columns for display
    col_renames = {
        "company_name": "Company",
        "ticker": "Ticker",
        "sector": "Sector",
        "bill_title": "Bill",
        "predicted_direction": "Direction",
        "market_moving_probability": "Mkt Moving P",
        "impact_strength": "Impact",
        "confidence": "Confidence",
        "risk_category": "Risk",
        "anticipation_evidence": "Anticipation",
    }

    # Only show columns that exist
    available_renames = {k: v for k, v in col_renames.items() if k in display_df.columns}
    display_df = display_df[list(available_renames.keys())].rename(columns=available_renames)

    # Format numeric column
    if "Mkt Moving P" in display_df.columns:
        display_df["Mkt Moving P"] = display_df["Mkt Moving P"].apply(
            lambda x: f"{x:.2%}" if pd.notna(x) else "—"
        )

    # Apply emoji formatting
    if "Direction" in display_df.columns:
        display_df["Direction"] = display_df["Direction"].map(
            lambda x: _DIRECTION_DISPLAY.get(str(x), str(x))
        )
    if "Risk" in display_df.columns:
        display_df["Risk"] = display_df["Risk"].map(
            lambda x: _RISK_DISPLAY.get(str(x), str(x))
        )
    if "Anticipation" in display_df.columns:
        display_df["Anticipation"] = display_df["Anticipation"].map(
            lambda x: _ANTICIPATION_DISPLAY.get(str(x), str(x))
        )

    total = len(display_df)
    if total > max_rows:
        st.caption(f"Showing first {max_rows:,} of {total:,} records. Use filters to narrow results.")
        display_df = display_df.head(max_rows)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"📊 {total:,} company-bill pairs | Read-only — no predictions modified")


def render_bills_summary_table(summaries: list[Any]) -> None:
    """
    Render a summary table of bills with key attributes.
    """
    if not summaries:
        st.info("No bills available.", icon="ℹ️")
        return

    rows = []
    for s in summaries:
        rows.append({
            "Bill": s.title,
            "Introduced": s.introduction_date.strftime("%d %b %Y") if s.introduction_date else "—",
            "Ministry": s.ministry,
            "Category": s.bill_category,
            "Status": s.status,
            "House": s.house,
            "Companies": s.affected_company_count,
            "Direction": _DIRECTION_DISPLAY.get(s.predicted_direction or "", "—") if s.has_prediction else "—",
            "Risk": _RISK_DISPLAY.get(s.risk_category or "", "—") if s.has_decision_support else "—",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"📋 {len(rows)} bills | Sorted by introduction date (newest first)")
