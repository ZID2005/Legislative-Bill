"""
tests/test_prediction_schemas.py
================================
Unit tests for Task 7.1 Prediction Schemas and serialization helpers.
"""

from __future__ import annotations

from datetime import datetime, timezone
import pytest

from schemas.prediction import (
    ConfidencePrediction,
    DirectionPrediction,
    ImpactStrengthPrediction,
    PredictionRecord,
    PredictionValidationReport,
    make_prediction_id,
    sanitize_id,
    ImpactLabel,
    SectorImpact,
    CompanyImpact,
    Prediction,
)


class TestPredictionEnums:
    def test_direction_prediction_values(self) -> None:
        assert DirectionPrediction.POSITIVE.value == "POSITIVE"
        assert DirectionPrediction.NEGATIVE.value == "NEGATIVE"
        assert DirectionPrediction.NEUTRAL.value == "NEUTRAL"

    def test_impact_strength_values(self) -> None:
        assert ImpactStrengthPrediction.LOW.value == "LOW"
        assert ImpactStrengthPrediction.MEDIUM.value == "MEDIUM"
        assert ImpactStrengthPrediction.HIGH.value == "HIGH"
        assert ImpactStrengthPrediction.VERY_HIGH.value == "VERY_HIGH"

    def test_confidence_prediction_values(self) -> None:
        assert ConfidencePrediction.LOW.value == "LOW"
        assert ConfidencePrediction.MEDIUM.value == "MEDIUM"
        assert ConfidencePrediction.HIGH.value == "HIGH"


class TestIdHelpers:
    def test_sanitize_id_replaces_invalid_chars(self) -> None:
        raw = "bill/2024:fin [101] +5 -2,test"
        sanitized = sanitize_id(raw)
        assert "/" not in sanitized
        assert ":" not in sanitized
        assert "[" not in sanitized
        assert "]" not in sanitized
        assert "+" not in sanitized
        assert "," not in sanitized
        assert "p5" in sanitized
        assert "-2" in sanitized

    def test_sanitize_id_empty(self) -> None:
        assert sanitize_id("") == ""

    def test_make_prediction_id_deterministic(self) -> None:
        id1 = make_prediction_id("fin-bill-2024", "INE002A01018", "[-20,+20]")
        id2 = make_prediction_id("fin-bill-2024", "INE002A01018", "[-20,+20]")
        assert id1 == id2
        assert id1.startswith("pred_")
        assert "fin-bill-2024" in id1
        assert "INE002A01018" in id1


class TestPredictionRecord:
    def test_prediction_record_round_trip(self) -> None:
        rec = PredictionRecord(
            prediction_id="pred_bill1_isin1_win1",
            bill_id="test-bill-2024",
            company_isin="INE001A01036",
            company_name="HDFC Bank",
            company_symbol="HDFCBANK",
            event_window="[-20,+20]",
            predicted_direction="POSITIVE",
            direction_probability={"POSITIVE": 0.85, "NEGATIVE": 0.05, "NEUTRAL": 0.10},
            predicted_market_moving=True,
            market_moving_probability=0.88,
            predicted_impact_strength="HIGH",
            impact_probabilities={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.70, "VERY_HIGH": 0.10},
            predicted_confidence="HIGH",
            confidence_probability={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.80},
            anticipation_class="STRONG_EVIDENCE",
            anticipation_score=0.82,
            model_name={"direction": "lgbm", "market_moving": "random_forest"},
            model_version="v1.0",
            feature_version="v1.0",
            prediction_timestamp="2026-08-16T12:00:00Z",
            decision_reason="Positive outlook with anticipation caution.",
            expected_impact_estimate="Expected positive return [+3%, +6%]",
            risk_indicators=["High pre-event run-up"],
            model_confidence=0.82,
            data_quality_status="VALID",
        )

        d = rec.to_dict()
        assert d["prediction_id"] == "pred_bill1_isin1_win1"
        assert d["predicted_direction"] == "POSITIVE"
        assert d["direction_probability"]["POSITIVE"] == 0.85
        assert d["predicted_market_moving"] is True
        assert d["risk_indicators"] == ["High pre-event run-up"]

        reconstructed = PredictionRecord.from_dict(d)
        assert reconstructed.prediction_id == rec.prediction_id
        assert reconstructed.bill_id == rec.bill_id
        assert reconstructed.company_isin == rec.company_isin
        assert reconstructed.predicted_direction == rec.predicted_direction
        assert reconstructed.direction_probability == rec.direction_probability
        assert reconstructed.predicted_market_moving == rec.predicted_market_moving
        assert reconstructed.market_moving_probability == rec.market_moving_probability
        assert reconstructed.predicted_impact_strength == rec.predicted_impact_strength
        assert reconstructed.impact_probabilities == rec.impact_probabilities
        assert reconstructed.predicted_confidence == rec.predicted_confidence
        assert reconstructed.confidence_probability == rec.confidence_probability
        assert reconstructed.anticipation_class == rec.anticipation_class
        assert reconstructed.anticipation_score == rec.anticipation_score
        assert reconstructed.model_name == rec.model_name
        assert reconstructed.risk_indicators == rec.risk_indicators

    def test_post_init_defaults(self) -> None:
        rec = PredictionRecord(
            prediction_id="",
            bill_id="bill-1",
            company_isin="INE123",
            event_window="[-5,+5]",
            predicted_direction="NEUTRAL",
            direction_probability={"NEUTRAL": 0.9},
            predicted_market_moving=False,
            market_moving_probability=0.1,
            predicted_impact_strength="LOW",
            impact_probabilities={"LOW": 0.9},
            predicted_confidence="MEDIUM",
            confidence_probability={"MEDIUM": 0.8},
            anticipation_class="NO_EVIDENCE",
            anticipation_score=0.05,
            model_name={"direction": "lgbm"},
            model_version="v1.0",
            feature_version="v1.0",
            prediction_timestamp="",
            decision_reason="Neutral",
        )
        assert rec.prediction_id.startswith("pred_")
        assert "bill-1" in rec.prediction_id
        assert rec.prediction_timestamp != ""


class TestPredictionValidationReport:
    def test_report_valid_and_invalid(self) -> None:
        rep_valid = PredictionValidationReport(
            report_id="",
            bill_id="bill-1",
            company_isin="INE123",
            event_window="[-20,+20]",
            is_valid=True,
            errors=[],
            warnings=["Minor warning"],
            checks_performed={"dim": True},
            details={"samples": 1},
        )
        assert rep_valid.is_valid is True
        assert rep_valid.report_id.startswith("val_")

        d = rep_valid.to_dict()
        assert d["is_valid"] is True
        assert d["warnings"] == ["Minor warning"]

        loaded = PredictionValidationReport.from_dict(d)
        assert loaded.bill_id == "bill-1"
        assert loaded.is_valid is True

        rep_invalid = PredictionValidationReport(
            report_id="val_custom",
            bill_id="bill-2",
            company_isin="INE456",
            event_window="[-20,+20]",
            errors=["Missing feature"],
        )
        assert rep_invalid.is_valid is False
        assert rep_invalid.report_id == "val_custom"


class TestLegacySchemas:
    def test_legacy_schemas_to_dict(self) -> None:
        c_impact = CompanyImpact(
            isin="INE001",
            ticker="ABC",
            company_name="ABC Ltd",
            sector="Finance",
            impact_label=ImpactLabel.POSITIVE,
            confidence=0.8,
            car_predicted=0.04,
            car_lower=0.02,
            car_upper=0.06,
            rationale="Strong impact",
            top_features=["beta"],
        )
        c_dict = c_impact.to_dict()
        assert c_dict["isin"] == "INE001"
        assert c_dict["impact_label"] == "positive"

        sector_impact = SectorImpact(
            sector="Finance",
            impact_label=ImpactLabel.POSITIVE,
            confidence=0.8,
        )
        assert sector_impact.sector == "Finance"

        pred = Prediction(
            bill_id="bill-1",
            model_version="v1",
            predicted_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            companies=[c_impact],
            sectors=[sector_impact],
            overall_impact=ImpactLabel.POSITIVE,
            notes="Note",
        )
        p_dict = pred.to_dict()
        assert p_dict["bill_id"] == "bill-1"
        assert len(p_dict["companies"]) == 1
        assert repr(pred).startswith("<Prediction")
