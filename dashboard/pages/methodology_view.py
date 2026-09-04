"""
dashboard/pages/methodology_view.py
===================================
End-to-End Methodology, Architecture, and Governance Walkthrough.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.disclaimer import (
    render_general_disclaimer,
    render_zero_modification_banner,
)


def render_methodology_view(*args: Any, **kwargs: Any) -> None:
    """
    Render complete architectural and methodological reference page.
    """
    st.markdown("## 📐 End-to-End System Architecture & Methodology")
    st.caption(
        "Institutional specification of data flows, temporal isolation guarantees, "
        "and quantitative modeling standards."
    )

    render_zero_modification_banner()
    st.markdown("---")

    st.markdown("### 🏛️ 10-Stage Pipeline Flow")
    st.markdown(
        """
        ```
        [1. Raw Ingestion]
                │
                ▼
        [2. Market & Event Study]
                │
                ▼
        [3. NLP Embeddings] (Legal-RoBERTa & FinBERT)
                │
                ▼
        [4. Feature Fusion & Selection]
                │
                ▼
        [5. ML Model Training] (LightGBM, XGBoost, Random Forest)
                │
                ▼
        [6. Explainability] (Task 6.3 SHAP)
                │
                ▼
        [7. Walk-Forward Backtesting] (Task 6.4)
                │
                ▼
        [8. Anticipation Auditing] (Task 6.5 Pre-Event Leakage)
                │
                ▼
        [9. Prediction & Decision Support Engine] (Task 7.1 & 7.2)
                │
                ▼
        [10. Stakeholder Reports & Interactive Dashboard] (Task 7.3 & 7.4)
        ```
        """
    )

    st.markdown("### 🛡️ Institutional Governance Invariants")
    g1, g2 = st.columns(2)

    with g1:
        st.markdown(
            """
            #### 1. Zero Lookahead & Target Leakage
            - All model training and feature selections use expanding walk-forward temporal splits.
            - Predictions consume only pre-event market data and bill introduction text.
            - Ground truth post-event CARs and event labels are strictly excluded from the prediction and decision engine.
            
            #### 2. Clean Layer Decoupling
            - Decision scoring does not modify raw ML probabilities.
            - Presentation layer (Task 7.3 & 7.4) does not alter decision scores, risk formulas, or historical backtests.
            - All reports and dashboard views are read-only views over immutable storage repositories.
            """
        )

    with g2:
        st.markdown(
            """
            #### 3. Calibrated Probabilistic Framing
            - Zero illicit insider trading vocabulary (*"insider"*, *"leakage"*, *"front-running criminal act"*).
            - Pre-event activity is characterized strictly as statistical *anticipation* or *information diffusion*.
            - Investor narratives use non-advisory language (*"model indicates potential impact"* rather than *"buy"* or *"sell"*).
            
            #### 4. Scope Parity & Auditability
            - 20 Production Bills × 47 Production Companies × 5 Windows = Exactly 4,700 Decision Support Records.
            - Every decision ID and report ID is generated deterministically from its composite key.
            """
        )

    st.markdown("<br>", unsafe_allow_html=True)
    render_general_disclaimer()
