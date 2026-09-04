"""
tests/test_decision_schemas.py
===============================
Unit tests for Task 7.2 Decision Support Schemas and serialization helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from schemas.decision import (
    DecisionSupportRecord,
    DecisionValidationReport,
    PricingInRisk,
    RiskCategory,
    StakeholderPerspective,
    make_decision_id,
    sanitize_id,
)


class TestDecisionEnums:
    def test_risk_category_values(self) -> None:
        assert RiskCategory.VERY_LOW.value == "VERY_LOW"
        assert RiskCategory.LOW.value == "LOW"
        assert RiskCategory.MODERATE.value == "MODERATE"
        assert RiskCategory.HIGH.value == "HIGH"
        assert RiskCategory.VERY_HIGH.value == "VERY_HIGH"

    def test_pricing_in_risk_values(self) -> None:
        assert PricingInRisk.VERY_LOW.value == "VERY_LOW"
        assert PricingInRisk.LOW.value == "LOW"
        assert PricingInRisk.MODERATE.value == "MODERATE"
        assert PricingInRisk.HIGH.value == "HIGH"

    def test_stakeholder_perspective_values(self) -> None:
        assert StakeholderPerspective.INVESTOR.value == "INVESTOR"
        assert StakeholderPerspective.BUSINESS.value == "BUSINESS"
        assert StakeholderPerspective.PUBLIC.value == "PUBLIC"


class TestDecisionIdHelpers:
    def test_sanitize_id_replaces_invalid_chars(self) -> None:
        raw = "bill/2024:telecom [001] +10 -5,test"
        sanitized = sanitize_id(raw)
        assert "/" not in sanitized
        assert ":" not in sanitized
        assert "[" not in sanitized
        assert "]" not in sanitized
        assert "+" not in sanitized
        assert "," not in sanitized
        assert "p10" in sanitized
        assert "-5" in sanitized

    def test_sanitize_id_empty(self) -> None:
        assert sanitize_id("") == ""

    def test_make_decision_id_deterministic(self) -> None:
        id1 = make_decision_id("telecom-bill-2024", "INE002A01018", "[-20,+20]")
        id2 = make_decision_id("telecom-bill-2024", "INE002A01018", "[-20,+20]")
        assert id1 == id2
        assert id1.startswith("dec_")
        assert "telecom-bill-2024" in id1
        assert "INE002A01018" in id1


class TestDecisionSupportRecord:
    def test_decision_record_round_trip(self) -> None:
        rec = DecisionSupportRecord(
            decision_id="dec_bill1_isin1_win1",
            bill_id="test-bill-2024",
            company_isin="INE001A01036",
            company_name="HDFC Bank",
            company_symbol="HDFCBANK",
            sector="Financial Services",
            event_window="[-20,+20]",
            predicted_direction="POSITIVE",
            direction_probability={"POSITIVE": 0.85, "NEGATIVE": 0.05, "NEUTRAL": 0.10},
            market_moving_probability=0.88,
            predicted_impact_strength="HIGH",
            impact_probabilities={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.70, "VERY_HIGH": 0.10},
            predicted_confidence="HIGH",
            confidence_probability={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.80},
            confidence_score=0.85,
            anticipation_class="STRONG_EVIDENCE",
            anticipation_score=0.82,
            impact_score=0.72,
            impact_category="HIGH",
            risk_score=0.48,
            risk_category="MODERATE",
            pricing_in_risk="HIGH",
            pricing_in_score=0.82,
            investor_summary="Model indicates potential positive impact.",
            business_summary="Direct regulatory relevance to banking operations.",
            public_summary="The bill modernizes banking oversight.",
            decision_reason="Positive impact indicated with moderate risk.",
            model_version="v1.0",
            feature_version="v1.0",
            decision_version="v1.0",
            generation_timestamp="2026-08-16T12:00:00Z",
            data_quality_status="VALID",
        )

        d = rec.to_dict()
        assert d["decision_id"] == "dec_bill1_isin1_win1"
        assert d["bill_id"] == "test-bill-2024"
        assert d["company_isin"] == "INE001A01036"
        assert d["impact_score"] == 0.72
        assert d["risk_score"] == 0.48
        assert d["risk_category"] == "MODERATE"
        assert d["pricing_in_risk"] == "HIGH"

        rec2 = DecisionSupportRecord.from_dict(d)
        assert rec2.decision_id == rec.decision_id
        assert rec2.bill_id == rec.bill_id
        assert rec2.company_isin == rec.company_isin
        assert rec2.impact_score == rec.impact_score
        assert rec2.risk_score == rec.risk_score
        assert rec2.risk_category == rec.risk_category
        assert rec2.pricing_in_risk == rec.pricing_in_risk
        assert rec2.investor_summary == rec.investor_summary

    def test_auto_generate_decision_id(self) -> None:
        rec = DecisionSupportRecord(
            decision_id="",
            bill_id="banking-bill-2024",
            company_isin="INE002A01018",
            event_window="[-20,+20]",
            predicted_direction="NEUTRAL",
            direction_probability={"POSITIVE": 0.1, "NEGATIVE": 0.1, "NEUTRAL": 0.8},
            market_moving_probability=0.1,
            predicted_impact_strength="LOW",
            confidence_probability={"LOW": 0.8, "MEDIUM": 0.15, "HIGH": 0.05},
            anticipation_class="NO_EVIDENCE",
            anticipation_score=0.1,
            impact_score=0.15,
            risk_score=0.25,
            risk_category="LOW",
            pricing_in_risk="VERY_LOW",
            investor_summary="Neutral outlook.",
            business_summary="Low direct exposure.",
            public_summary="Standard reform measure.",
            decision_reason="Subdued impact.",
            model_version="v1.0",
            feature_version="v1.0",
            generation_timestamp="",
        )
        assert rec.decision_id.startswith("dec_banking-bill-2024_INE002A01018_")
        assert rec.generation_timestamp != ""


class TestDecisionValidationReport:
    def test_validation_report_round_trip(self) -> None:
        report = DecisionValidationReport(
            report_id="",
            bill_id="bill-1",
            company_isin="INE001A01036",
            event_window="[-10,+10]",
            is_valid=True,
            errors=[],
            warnings=["Minor mismatch"],
            checks_performed={"probabilities_valid": True},
            details={"risk_score": 0.35},
        )
        assert report.report_id.startswith("val_dec_bill-1_INE001A01036_")
        assert report.is_valid is True

        d = report.to_dict()
        assert d["bill_id"] == "bill-1"
        assert d["is_valid"] is True
        assert d["warnings"] == ["Minor mismatch"]

        report2 = DecisionValidationReport.from_dict(d)
        assert report2.report_id == report.report_id
        assert report2.bill_id == report.bill_id
        assert report2.is_valid is True
        assert report2.warnings == ["Minor mismatch"]

    def test_validation_report_auto_invalid_on_errors(self) -> None:
        report = DecisionValidationReport(
            report_id="",
            bill_id="bill-1",
            company_isin="INE001A01036",
            event_window="[-10,+10]",
            is_valid=True,
            errors=["Missing prediction record"],
        )
        assert report.is_valid is False
