"""
dashboard/pages/methodology.py
==============================
Task 7.4.2 — Academic Methodology & Architectural Foundations.

Provides a comprehensive 18-stage academic blueprint of the Legislative
Intelligence & Market Impact Prediction System:
1. Legislative Ingestion
2. Legislative Metadata
3. Knowledge Layer
4. Company Mapping
5. Market Data
6. Event Studies
7. Ground-Truth Labels
8. FinBERT Embeddings
9. Legal Transformer Embeddings
10. Feature Fusion
11. Feature Selection
12. ML Models
13. Model Evaluation
14. Walk-Forward Backtesting
15. Anticipation Analysis
16. Decision Support
17. Risk Scoring
18. Stakeholder Reporting

Key methodological principles:
- Strict Temporal Separation (no lookahead bias)
- The Anticipation Paradox
- Diagnostic, non-accusatory pre-event diffusion modeling
- Read-only presentation architecture
"""

from __future__ import annotations

from typing import Any, Optional
import streamlit as st


def render_methodology_page(*args: Any, **kwargs: Any) -> None:
    """
    Render the '📐 Academic Methodology' page.
    """
    st.markdown(
        "<h1 style='margin-bottom:0;'>📐 Academic Methodology & System Blueprint</h1>",
        unsafe_allow_html=True,
    )
    st.caption("Theoretical foundations, mathematical formulations, and econometric pipeline architecture.")

    # Core Guiding Principles
    st.markdown(
        r"""
        <div style="background:#F0FDF4;border-left:4px solid #16A34A;padding:14px 18px;border-radius:4px;font-size:0.92rem;margin-bottom:20px;line-height:1.6;">
            <b>Core Methodological Principles:</b>
            <br>
            • <b>Strict Temporal Isolation</b>: At every stage, the information set available at time $T_0$ is restricted strictly to historical and pre-event signals ($\mathcal{F}_{T \le 0}$). Future price action and announcement reactions are excluded.
            <br>
            • <b>Presentation Immutability</b>: The dashboard is an observational layer. No machine learning models are retrained, no predictions are computed on-the-fly, and pre-computed risk and anticipation scores are immutable.
            <br>
            • <b>Non-Accusatory Diagnostic Modeling</b>: Pre-event abnormal drift reflects legitimate informational diffusion and price discovery. It does not constitute proof of insider trading.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 18-Stage Pipeline Accordions
    st.markdown("### 🔬 The 18-Stage Quantitative Pipeline")

    stages = [
        ("1. Legislative Ingestion", "Automated parsing and extraction of official Gazette notifications and Lok Sabha / Rajya Sabha parliamentary tabling records for the 2024 session."),
        ("2. Legislative Metadata", "Extraction of authoritative introduction dates, sponsoring ministries, session identifiers, parliamentary bill numbers, and formal lifecycle status."),
        ("3. Knowledge Layer", "Construction of structured domain knowledge graphs capturing ministerial portfolios, economic jurisdictions, and statutory frameworks."),
        ("4. Company Mapping", "Deterministic mapping linking legislative enactments to listed BSE/NSE entities via GICS sector taxonomies, ministry regulation tables, and text entity resolution."),
        ("5. Market Data", "Cleaned daily split- and dividend-adjusted equity prices and Nifty 50 benchmark indices spanning from 2014 through 2024."),
        ("6. Event Studies", "Estimation of Market Model parameters ($\alpha_i, \beta_i$) over the pre-event estimation window ($T = -120$ to $-10$) and computation of Abnormal Returns ($AR_{it}$) and Cumulative Abnormal Returns ($CAR_{i}[t_1, t_2]$)."),
        ("7. Ground-Truth Labels", "Generation of standardized research targets across 5 event windows ([-1,+1], [-3,+3], [-5,+5], [-5,+10], [-10,+10]) classifying direction (Positive, Negative, Neutral) and volatility magnitude."),
        ("8. FinBERT Embeddings", "Domain-adapted financial language model (Prosus FinBERT) producing 768-dimensional contextual vector representations of legislative provisions."),
        ("9. Legal Transformer Embeddings", "InLegalBERT embeddings capturing statutory nuances, regulatory compliance obligations, and legislative intent."),
        ("10. Feature Fusion", "Multi-modal concatenation and alignment uniting text embeddings, company market beta, pre-event volatility, ministerial dummies, and sector covariates."),
        ("11. Feature Selection", "Variance filtering, mutual information ranking, and multi-collinearity pruning ($VIF < 5$) reducing dimensionality to optimal signal subsets."),
        ("12. ML Models", "Ensemble architecture combining LightGBM, Random Forests, and calibrated Logistic Regressors with Platt scaling for probability calibration."),
        ("13. Model Evaluation", "Strict holdout evaluation computing Macro F1, Balanced Accuracy, Matthews Correlation Coefficient (MCC), and ROC-AUC under class imbalance."),
        ("14. Walk-Forward Backtesting", "Expanding-window out-of-sample simulation testing systematic trading strategies with realistic transaction costs (15 bps) and liquidity constraints."),
        ("15. Anticipation Analysis", "Econometric drift detection measuring pre-event cumulative abnormal returns ($T = -30$ to $-2$) to detect market pricing-in and informational diffusion."),
        ("16. Decision Support", "Synthesis of multi-dimensional quantitative predictions into human-interpretable risk tiers and decision vectors."),
        ("17. Risk Scoring", "Composite risk formulation integrating market-moving probability, prediction entropy, confidence discounts, and structural tail-risk flags."),
        ("18. Stakeholder Reporting", "Generation of institutional research dossiers tailored to Investor, Corporate / Business, and Public / Citizen perspectives."),
    ]

    for title, desc in stages:
        with st.expander(f"📌 {title}", expanded=False):
            st.markdown(f"<p style='font-size:0.95rem;line-height:1.6;'>{desc}</p>", unsafe_allow_html=True)

    st.markdown("---")

    # Special Focus: The Anticipation Paradox & Temporal Separation
    st.markdown("### 💡 Theoretical Pillars")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### ⏳ Temporal Separation & Anti-Leakage")
        st.markdown(
            r"""
            In financial econometrics, predictive models frequently suffer from subtle lookahead biases:
            - **Estimation Window Leakage**: Using event window returns to fit benchmark parameters.
            - **Feature Lookahead**: Using post-event text revisions or subsequent parliamentary amendments as inputs.
            - **Target Contamination**: Allowing announcement volatility to influence pre-event features.

            *Our pipeline enforces strict chronological barriers*: all features are constructed exclusively from information published prior to formal introduction date ($T \le 0$).
            """
        )

    with col2:
        st.markdown("#### ⚡ The Anticipation Paradox")
        st.markdown(
            """
            In political economy, significant legislative proposals rarely occur in a vacuum:
            - Industry consultations, white papers, and standing committee deliberations circulate weeks prior to parliamentary tabling.
            - When markets efficiently discount regulatory expectations, abnormal returns occur *before* the formal event.
            - **The Paradox**: High-impact, heavily anticipated bills often demonstrate *zero abnormal return* on tabling day because the event is 100% priced in.
            - Our anticipation framework diagnostically models this diffusion without presuming illicit leakage.
            """
        )

    st.markdown("---")
    st.caption("Institutional Quantitative Decision System — Designed for rigorous academic evaluation and institutional governance.")
