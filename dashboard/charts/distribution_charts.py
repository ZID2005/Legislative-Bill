"""
dashboard/charts/distribution_charts.py
=======================================
Distribution charts for risk scores, impact scores, probabilities, and categories.
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd

from dashboard.utils.formatting import (
    ANTICIPATION_COLORS,
    DIRECTION_COLORS,
    RISK_COLORS,
)


def create_risk_category_bar(df: pd.DataFrame) -> Any:
    """
    Generate bar chart of Decision Risk Categories (VERY_LOW to VERY_HIGH).
    """
    import plotly.graph_objects as go

    order = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"]
    counts = {cat: 0 for cat in order}

    if not df.empty and "risk_category" in df.columns:
        val_counts = df["risk_category"].value_counts().to_dict()
        for k, v in val_counts.items():
            if k in counts:
                counts[k] = v

    categories = [cat.replace("_", " ").title() for cat in order]
    values = [counts[cat] for cat in order]
    colors = [RISK_COLORS[cat] for cat in order]

    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color=colors,
                text=values,
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="<b>Risk Category Distribution</b>",
        xaxis_title="Risk Category",
        yaxis_title="Record Count",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=320,
    )
    return fig


def create_impact_score_hist(df: pd.DataFrame, nbins: int = 20) -> Any:
    """
    Generate histogram distribution of Directional Impact Scores [0.0, 1.0].
    """
    import plotly.graph_objects as go

    if df.empty or "impact_score" not in df.columns:
        values = []
    else:
        values = df["impact_score"].dropna().tolist()

    fig = go.Figure(
        data=[
            go.Histogram(
                x=values,
                nbinsx=nbins,
                marker_color="#3B82F6",
                opacity=0.85,
            )
        ]
    )
    fig.update_layout(
        title="<b>Directional Impact Score Distribution</b>",
        xaxis_title="Impact Score (0.0 to 1.0)",
        yaxis_title="Frequency",
        xaxis=dict(range=[0, 1]),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=320,
    )
    return fig


def create_market_moving_distribution(df: pd.DataFrame) -> Any:
    """
    Generate distribution for Market-Moving Probabilities.
    """
    import plotly.graph_objects as go

    if df.empty or "market_moving_probability" not in df.columns:
        values = []
    else:
        values = df["market_moving_probability"].dropna().tolist()

    fig = go.Figure(
        data=[
            go.Histogram(
                x=values,
                nbinsx=20,
                marker_color="#8B5CF6",
                opacity=0.85,
            )
        ]
    )
    fig.update_layout(
        title="<b>Market-Moving Probability Distribution</b>",
        xaxis_title="P(Market-Moving)",
        yaxis_title="Frequency",
        xaxis=dict(range=[0, 1]),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=320,
    )
    return fig


def create_direction_pie(df: pd.DataFrame) -> Any:
    """
    Generate donut/pie chart of Predicted Direction breakdown.
    """
    import plotly.graph_objects as go

    order = ["POSITIVE", "NEGATIVE", "NEUTRAL"]
    counts = {d: 0 for d in order}

    if not df.empty and "predicted_direction" in df.columns:
        val_counts = df["predicted_direction"].value_counts().to_dict()
        for k, v in val_counts.items():
            if k in counts:
                counts[k] = v

    labels = [d.capitalize() for d in order]
    values = [counts[d] for d in order]
    colors = [DIRECTION_COLORS[d] for d in order]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker=dict(colors=colors),
                textinfo="label+percent",
            )
        ]
    )
    fig.update_layout(
        title="<b>Predicted Direction Distribution</b>",
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        height=300,
    )
    return fig


def create_anticipation_bar(df: pd.DataFrame) -> Any:
    """
    Generate horizontal bar chart of Anticipation Evidence classifications.
    """
    import plotly.graph_objects as go

    order = ["NO_EVIDENCE", "WEAK_EVIDENCE", "MODERATE_EVIDENCE", "STRONG_EVIDENCE"]
    counts = {tier: 0 for tier in order}

    if not df.empty and "anticipation_evidence" in df.columns:
        val_counts = df["anticipation_evidence"].value_counts().to_dict()
        for k, v in val_counts.items():
            if k in counts:
                counts[k] = v

    labels = [tier.replace("_", " ").title() for tier in order]
    values = [counts[tier] for tier in order]
    colors = [ANTICIPATION_COLORS[tier] for tier in order]

    fig = go.Figure(
        data=[
            go.Bar(
                y=labels,
                x=values,
                orientation="h",
                marker_color=colors,
                text=values,
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="<b>Anticipation Evidence Classifications</b>",
        xaxis_title="Record Count",
        yaxis_title="Evidence Tier",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=300,
    )
    return fig
