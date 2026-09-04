"""
dashboard/pages/explainability_view.py
======================================
Model Explainability page loading verified Task 6.3 SHAP artifacts.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.charts.backtest_charts import create_feature_importance_bar
from dashboard.components.disclaimer import render_general_disclaimer
from dashboard.services.data_service import DashboardDataService


def render_explainability_view(data_service: DashboardDataService, df: pd.DataFrame) -> None:
    """
    Render Explainability view from existing Task 6.3 artifacts (zero runtime recalculation).
    """
    st.markdown("## 🧠 Machine Learning Model Explainability")
    st.caption(
        "Direct inspection of Task 6.3 SHAP (SHapley Additive exPlanations) values, "
        "global feature importance rankings, and cross-model audits."
    )

    st.info(
        "🔒 **Pre-Computed Artifact Audit**: SHAP values are loaded directly from verified repository files "
        "(`explainability/global_summary.json` and `model_comparison.json`). No retraining or recalculation is performed."
    )

    global_summary = data_service.get_global_explainability()
    model_comparison = data_service.get_model_comparison_explainability()

    tab_global, tab_compare, tab_local = st.tabs([
        "🌟 Global Feature Rankings",
        "⚖️ Model Architecture Comparison",
        "🎯 Local Instance Explanations",
    ])

    with tab_global:
        st.markdown("### Top Global Predictive Drivers")
        top_features = global_summary.get("top_20_features", [])
        if top_features:
            df_feat = pd.DataFrame(top_features)
            st.plotly_chart(create_feature_importance_bar(df_feat, top_k=20), use_container_width=True)

            st.markdown("#### Feature Importance Matrix")
            st.dataframe(df_feat, use_container_width=True)
        else:
            st.warning("Global summary feature data not found. Ensure Task 6.3 artifacts exist in `explainability/`.")

    with tab_compare:
        st.markdown("### Cross-Model Predictive Consensus")
        if model_comparison:
            st.write(
                "Evaluates agreement across LightGBM, XGBoost, and Random Forest architectures "
                "across Direction, Impact Strength, Market-Moving, and Confidence targets."
            )
            targets = model_comparison.get("targets", {})
            if targets:
                for target_name, t_data in targets.items():
                    with st.expander(f"Target: **{target_name.upper()}**", expanded=False):
                        st.json(t_data)
            else:
                st.json(model_comparison)
        else:
            st.info("Cross-model comparison artifacts not available.")

    with tab_local:
        st.markdown("### Sample Case Local Feature Attributions")
        st.write(
            "Exemplar local SHAP force contributions demonstrating how individual legal provision embeddings, "
            "market beta, and volatility features influence specific candidate probabilities."
        )
        try:
            exp_repo = data_service.explainability_repo
            if exp_repo.exists("direction", "lgbm"):
                artifacts = exp_repo.load("direction", "lgbm")
                local_exps = artifacts.get("local_explanations", {})
                if local_exps:
                    st.json(local_exps)
                else:
                    st.caption("No specific local explanation instances stored in this model directory.")
            else:
                st.caption("Default local explanation artifacts not found for direction/lgbm.")
        except Exception as exc:
            st.caption(f"Local explanations unavailable: {exc}")

    st.markdown("<br>", unsafe_allow_html=True)
    render_general_disclaimer()
