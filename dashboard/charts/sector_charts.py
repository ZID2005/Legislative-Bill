"""
dashboard/charts/sector_charts.py
=================================
Sector-level exposure, comparison, and distribution charts.
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd


def create_sector_impact_bar(df: pd.DataFrame) -> Any:
    """
    Generate horizontal bar chart comparing average impact score by sector.
    """
    import plotly.graph_objects as go

    if df.empty or "sector" not in df.columns or "impact_score" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="<b>Sector Impact Comparison (No Data)</b>")
        return fig

    sector_agg = (
        df.groupby("sector")
        .agg(avg_impact=("impact_score", "mean"), count=("decision_id", "count"))
        .reset_index()
        .sort_values(by="avg_impact", ascending=True)
    )

    fig = go.Figure(
        data=[
            go.Bar(
                y=sector_agg["sector"],
                x=sector_agg["avg_impact"],
                orientation="h",
                marker_color="#2563EB",
                text=[f"{val:.3f}" for val in sector_agg["avg_impact"]],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="<b>Average Directional Impact Score by Sector</b>",
        xaxis_title="Mean Impact Score",
        yaxis_title="Sector",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=380,
    )
    return fig


def create_sector_risk_comparison(df: pd.DataFrame) -> Any:
    """
    Generate grouped bar chart comparing average Impact Score vs Risk Score by sector.
    """
    import plotly.graph_objects as go

    if df.empty or "sector" not in df.columns:
        fig = go.Figure()
        return fig

    sector_agg = (
        df.groupby("sector")
        .agg(
            avg_impact=("impact_score", "mean"),
            avg_risk=("risk_score", "mean"),
        )
        .reset_index()
        .sort_values(by="avg_impact", ascending=False)
    )

    fig = go.Figure(
        data=[
            go.Bar(
                name="Avg Impact Score",
                x=sector_agg["sector"],
                y=sector_agg["avg_impact"],
                marker_color="#3B82F6",
            ),
            go.Bar(
                name="Avg Risk Score",
                x=sector_agg["sector"],
                y=sector_agg["avg_risk"],
                marker_color="#F59E0B",
            ),
        ]
    )
    fig.update_layout(
        barmode="group",
        title="<b>Sector Comparison: Mean Impact vs Mean Risk Score</b>",
        xaxis_title="Sector",
        yaxis_title="Score (0.0 to 1.0)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
