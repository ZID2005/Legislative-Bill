"""
dashboard/charts/risk_matrix.py
===============================
Interactive 2D Decision Risk Matrix: Impact Score vs Composite Risk Score.
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd

from dashboard.utils.formatting import RISK_COLORS


def create_risk_matrix(df: pd.DataFrame) -> Any:
    """
    Generate interactive 2D scatter plot of Impact Score vs Composite Risk Score.
    """
    import plotly.graph_objects as go

    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="<b>Risk Matrix (No Data Available)</b>",
            xaxis_title="Directional Impact Score",
            yaxis_title="Composite Decision Risk Score",
            template="plotly_white",
        )
        return fig

    # Create scatter traces by risk category for clean legend grouping
    fig = go.Figure()

    categories = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"]
    for cat in categories:
        sub_df = df[df["risk_category"] == cat]
        if sub_df.empty:
            continue

        hover_text = [
            f"<b>{row.get('company_name', row.get('company_isin'))}</b> ({row.get('ticker', '')})<br>"
            f"Bill: {row.get('bill_title', row.get('bill_id'))}<br>"
            f"Direction: {row.get('predicted_direction')}<br>"
            f"Impact Score: {row.get('impact_score'):.4f}<br>"
            f"Risk Score: {row.get('risk_score'):.4f}<br>"
            f"P(Market-Moving): {row.get('market_moving_probability'):.3f}<br>"
            f"Confidence: {row.get('confidence')}<br>"
            f"Window: {row.get('event_window')}"
            for _, row in sub_df.iterrows()
        ]

        fig.add_trace(
            go.Scatter(
                x=sub_df["impact_score"],
                y=sub_df["risk_score"],
                mode="markers",
                name=cat.replace("_", " ").title(),
                marker=dict(
                    color=RISK_COLORS.get(cat, "#6B7280"),
                    size=8,
                    opacity=0.75,
                    line=dict(width=1, color="white"),
                ),
                text=hover_text,
                hoverinfo="text",
            )
        )

    # Add quadrant reference lines
    fig.add_vline(x=0.20, line_width=1, line_dash="dash", line_color="gray")
    fig.add_hline(y=0.50, line_width=1, line_dash="dash", line_color="gray")

    # Add annotations for quadrants
    fig.add_annotation(
        x=0.05, y=0.95, text="High Risk / Low Impact", showarrow=False,
        font=dict(size=10, color="gray")
    )
    fig.add_annotation(
        x=0.85, y=0.95, text="High Risk / High Impact (Volatile)", showarrow=False,
        font=dict(size=10, color="crimson")
    )
    fig.add_annotation(
        x=0.05, y=0.15, text="Low Risk / Low Impact (Benign)", showarrow=False,
        font=dict(size=10, color="green")
    )
    fig.add_annotation(
        x=0.85, y=0.15, text="High Impact / Lower Risk (High Conviction)", showarrow=False,
        font=dict(size=10, color="green")
    )

    fig.update_layout(
        title="<b>Decision Risk Matrix: Directional Impact vs Composite Risk</b>",
        xaxis_title="Directional Impact Score (0.0 → 1.0)",
        yaxis_title="Composite Decision Risk Score (0.0 → 1.0)",
        xaxis=dict(range=[-0.02, 1.02]),
        yaxis=dict(range=[-0.02, 1.02]),
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=480,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
