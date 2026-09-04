"""
dashboard/charts/backtest_charts.py
===================================
Visualizations for Historical Backtesting results and Model Explainability.
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd


def create_feature_importance_bar(feature_importance: list[dict[str, Any]] | pd.DataFrame, top_k: int = 15) -> Any:
    """
    Generate horizontal bar chart of top SHAP / model feature importances.
    """
    import plotly.graph_objects as go

    if isinstance(feature_importance, list):
        df = pd.DataFrame(feature_importance)
    else:
        df = feature_importance.copy()

    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="<b>Feature Importance (No Data)</b>")
        return fig

    # Standardize column names
    col_feat = "feature" if "feature" in df.columns else df.columns[0]
    col_val = "importance" if "importance" in df.columns else ("mean_abs_shap" if "mean_abs_shap" in df.columns else df.columns[1])

    df = df.sort_values(by=col_val, ascending=True).tail(top_k)

    fig = go.Figure(
        data=[
            go.Bar(
                y=df[col_feat],
                x=df[col_val],
                orientation="h",
                marker_color="#4F46E5",
                text=[f"{v:.4f}" for v in df[col_val]],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title=f"<b>Top {top_k} Features by Explanatory Importance (SHAP)</b>",
        xaxis_title="Mean |SHAP Value| (Impact on Model Log-Odds)",
        yaxis_title="Feature Name",
        template="plotly_white",
        margin=dict(l=60, r=40, t=50, b=40),
        height=420,
    )
    return fig


def create_portfolio_equity_curve(timeseries_df: pd.DataFrame) -> Any:
    """
    Generate timeseries chart of cumulative strategy returns vs benchmark returns.
    """
    import plotly.graph_objects as go

    if timeseries_df.empty:
        fig = go.Figure()
        fig.update_layout(title="<b>Cumulative Portfolio Performance (No Data)</b>")
        return fig

    fig = go.Figure()

    date_col = "date" if "date" in timeseries_df.columns else timeseries_df.columns[0]

    if "cumulative_strategy_return" in timeseries_df.columns:
        fig.add_trace(
            go.Scatter(
                x=timeseries_df[date_col],
                y=timeseries_df["cumulative_strategy_return"] * 100,
                mode="lines",
                name="Backtest Strategy",
                line=dict(color="#10B981", width=2.5),
            )
        )
    elif "portfolio_value" in timeseries_df.columns:
        norm_val = timeseries_df["portfolio_value"] / timeseries_df["portfolio_value"].iloc[0] - 1.0
        fig.add_trace(
            go.Scatter(
                x=timeseries_df[date_col],
                y=norm_val * 100,
                mode="lines",
                name="Backtest Strategy",
                line=dict(color="#10B981", width=2.5),
            )
        )

    if "cumulative_benchmark_return" in timeseries_df.columns:
        fig.add_trace(
            go.Scatter(
                x=timeseries_df[date_col],
                y=timeseries_df["cumulative_benchmark_return"] * 100,
                mode="lines",
                name="Benchmark (Nifty 50)",
                line=dict(color="#6B7280", width=1.5, dash="dot"),
            )
        )

    fig.update_layout(
        title="<b>Historical Backtest: Cumulative Strategy Return (%) vs Benchmark</b>",
        xaxis_title="Date",
        yaxis_title="Cumulative Return (%)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_drawdown_curve(timeseries_df: pd.DataFrame) -> Any:
    """
    Generate underwater drawdown curve chart.
    """
    import plotly.graph_objects as go

    if timeseries_df.empty or "drawdown" not in timeseries_df.columns:
        fig = go.Figure()
        return fig

    date_col = "date" if "date" in timeseries_df.columns else timeseries_df.columns[0]
    fig = go.Figure(
        data=[
            go.Scatter(
                x=timeseries_df[date_col],
                y=timeseries_df["drawdown"] * 100,
                fill="tozeroy",
                mode="lines",
                name="Drawdown",
                line=dict(color="#EF4444", width=1.5),
                fillcolor="rgba(239, 68, 68, 0.2)",
            )
        ]
    )
    fig.update_layout(
        title="<b>Underwater Drawdown Profile (%)</b>",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        template="plotly_white",
        margin=dict(l=40, r=40, t=50, b=40),
        height=260,
    )
    return fig
