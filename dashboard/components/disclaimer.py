"""
dashboard/components/disclaimer.py
==================================
Mandatory institutional disclaimers and compliance notices for the dashboard.
"""

from __future__ import annotations

import streamlit as st


def render_general_disclaimer() -> None:
    """Render the standard institutional quantitative finance disclaimer."""
    st.info(
        "⚖️ **Regulatory & Institutional Disclaimer**: This system produces quantitative research interpretations "
        "and probabilistic impact assessments based on historical event-study models. It does not provide personalized "
        "financial advice, investment recommendations, or trade execution. Past backtested performance is hypothetical "
        "and does not guarantee future results."
    )


def render_anticipation_disclaimer() -> None:
    """Render mandatory legal disclaimer regarding pre-event market anticipation."""
    st.warning(
        "🛡️ **Anticipation Evidence Notice**: Pre-event abnormal volume or return metrics reflect potential informational "
        "diffusion or early pricing-in by market participants. **Anticipation evidence does not establish insider trading, "
        "unlawful information leakage, or regulatory misconduct.**"
    )


def render_zero_modification_banner() -> None:
    """Render presentation-layer invariant notice."""
    st.caption(
        "🔒 **Read-Only Presentation Layer Active**: Zero model retraining, zero parameter adjustments, "
        "and zero post-event price lookahead. All metrics originate from verified repository outputs."
    )
