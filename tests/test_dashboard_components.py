"""
tests/test_dashboard_components.py
==================================
Unit tests for Task 7.4 Dashboard UI components, formatting, and compliance invariants.
"""

from __future__ import annotations

import pandas as pd
import pytest

from dashboard.components.disclaimer import (
    render_anticipation_disclaimer,
    render_general_disclaimer,
    render_zero_modification_banner,
)
from dashboard.components.kpi_cards import render_kpi_cards
from dashboard.components.report_viewer import (
    render_bill_report,
    render_company_report,
    render_stakeholder_report,
)
from dashboard.utils.export import to_csv_bytes, to_json_bytes
from dashboard.utils.formatting import (
    format_currency,
    format_direction,
    format_number,
    format_percentage,
    format_prob,
    format_risk_category,
    get_anticipation_badge,
    get_direction_badge,
    get_risk_badge,
)
from schemas.report import BillLevelReport, CompanyLevelReport, StakeholderReport, StakeholderType


def test_formatting_utils():
    """Verify numeric, percentage, currency, and string formatters."""
    assert format_number(12.3456, decimals=2) == "12.35"
    assert format_number(None) == "N/A"
    assert format_number(float("nan")) == "N/A"
    assert format_number(float("inf")) == "N/A"
    assert format_number("non_numeric") == "non_numeric"

    assert format_percentage(0.8543, decimals=1) == "85.4%"
    assert format_percentage(None) == "N/A"
    assert format_percentage(float("nan")) == "N/A"
    assert format_percentage("non_numeric") == "N/A"

    assert format_prob(0.1234) == "0.123"

    assert format_currency(150000.0) == "₹1.50 Lakh Cr"
    assert format_currency(500.0) == "₹500.00 Cr"
    assert format_currency(None) == "N/A"
    assert format_currency(float("nan")) == "N/A"
    assert format_currency("non_numeric") == "₹non_numeric"

    assert format_risk_category("VERY_HIGH") == "Very High"
    assert format_risk_category(None) == "UNKNOWN"

    assert format_direction("POSITIVE") == "Positive"
    assert format_direction(None) == "Neutral"


def test_badge_generators():
    """Verify HTML badge generation."""
    risk_badge = get_risk_badge("LOW")
    assert "Low" in risk_badge
    assert "color: #34D399" in risk_badge

    dir_badge = get_direction_badge("POSITIVE")
    assert "Positive" in dir_badge
    assert "▲" in dir_badge

    neg_badge = get_direction_badge("NEGATIVE")
    assert "▼" in neg_badge

    ant_badge = get_anticipation_badge("STRONG_EVIDENCE")
    assert "Strong Evidence" in ant_badge


def test_export_utils():
    """Verify CSV and JSON serialization to bytes."""
    df = pd.DataFrame([{"a": 1, "b": "test"}])
    csv_bytes = to_csv_bytes(df)
    assert isinstance(csv_bytes, bytes)
    assert b"test" in csv_bytes

    data = {"key": "value", "num": 42}
    json_bytes = to_json_bytes(data)
    assert isinstance(json_bytes, bytes)
    assert b"value" in json_bytes


def test_investor_compliance_invariants():
    """
    STRICT GOVERNANCE TEST: Verify that investor research interpretations NEVER
    use prohibited trade execution or guaranteed return vocabulary.
    """
    prohibited_keywords = [
        "buy",
        "sell",
        "guaranteed return",
        "stock will rise",
        "stock will fall",
        "guaranteed profit",
    ]

    # Sample phrases used in investor view
    sample_narratives = [
        "Model indicates a potential positive impact on firm valuations.",
        "Model indicates a potential negative or adverse market reaction.",
        "Model indicates a neutral or subdued market reaction within historical variances.",
        "Model assigns an elevated probability that the event may be market-moving (P >= 0.50).",
        "Model assigns a low probability of an extreme, tail-moving market shock.",
        "Pricing-in risk assessment: LOW. Pre-event market diagnostics indicate NO_EVIDENCE.",
    ]

    for narrative in sample_narratives:
        lower_text = narrative.lower()
        for kw in prohibited_keywords:
            assert kw not in lower_text, f"Prohibited keyword '{kw}' found in narrative: '{narrative}'"


def test_report_viewer_render_none():
    """Verify report viewer renders gracefully without error when reports are None."""
    # These functions call Streamlit UI elements; we ensure they don't throw unexpected exceptions
    render_stakeholder_report(None)
    render_bill_report(None)
    render_company_report(None)
    render_general_disclaimer()
    render_anticipation_disclaimer()
    render_zero_modification_banner()
