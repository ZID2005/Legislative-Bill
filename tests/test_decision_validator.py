"""
tests/test_decision_validator.py
================================
Unit tests for DecisionSupportValidator input integrity and record audit (Task 7.2).
"""

from __future__ import annotations

import pytest

from decision_support.validator import DecisionSupportValidator
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company, MarketCapCategory
from schemas.decision import DecisionSupportRecord
from schemas.prediction import PredictionRecord


@pytest.fixture
def validator() -> DecisionSupportValidator:
    return DecisionSupportValidator()


@pytest.fixture
def valid_prediction() -> PredictionRecord:
    return PredictionRecord(
        prediction_id="pred_bill_1_isin_1_[-20,+20]",
        bill_id="the-telecom-act-2024",
        company_isin="INE002A01018",
        company_name="Reliance Industries",
        company_symbol="RELIANCE",
        event_window="[-20,+20]",
        predicted_direction="POSITIVE",
        direction_probability={"POSITIVE": 0.80, "NEGATIVE": 0.10, "NEUTRAL": 0.10},
        predicted_market_moving=True,
        market_moving_probability=0.85,
        predicted_impact_strength="HIGH",
        impact_probabilities={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.70, "VERY_HIGH": 0.10},
        predicted_confidence="HIGH",
        confidence_probability={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.80},
        anticipation_class="NO_EVIDENCE",
        anticipation_score=0.10,
        model_name={"direction": "lgbm"},
        model_version="v1.0",
        feature_version="v1.0",
        prediction_timestamp="2026-08-16T12:00:00Z",
        decision_reason="Preliminary prediction rationale.",
    )


@pytest.fixture
def valid_bill() -> Bill:
    return Bill(
        bill_id="the-telecom-act-2024",
        title="The Telecommunications Act, 2024",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://prsindia.org/bills/the-telecom-act-2024",
        year=2024,
        ministry="Ministry of Communications",
    )


@pytest.fixture
def valid_company() -> Company:
    return Company(
        isin="INE002A01018",
        company_name="Reliance Industries Limited",
        bse_code="500325",
        ticker_nse="RELIANCE",
        sector="Energy & Telecom",
        industry="Telecommunications",
        market_cap_category=MarketCapCategory.LARGE_CAP,
    )


class TestInputValidation:
    def test_valid_inputs_pass(
        self,
        validator: DecisionSupportValidator,
        valid_prediction: PredictionRecord,
        valid_bill: Bill,
        valid_company: Company,
    ) -> None:
        report = validator.validate_inputs(
            prediction=valid_prediction,
            bill=valid_bill,
            company=valid_company,
            expected_model_version="v1.0",
            expected_feature_version="v1.0",
        )
        assert report.is_valid is True
        assert len(report.errors) == 0

    def test_missing_prediction_rejected(self, validator: DecisionSupportValidator) -> None:
        report = validator.validate_inputs(prediction=None)
        assert report.is_valid is False
        assert any("PredictionRecord is missing" in e for e in report.errors)

    def test_missing_bill_rejected(
        self,
        validator: DecisionSupportValidator,
        valid_prediction: PredictionRecord,
        valid_company: Company,
    ) -> None:
        report = validator.validate_inputs(
            prediction=valid_prediction,
            bill=None,
            company=valid_company,
        )
        assert report.is_valid is False
        assert any("Bill metadata missing" in e for e in report.errors)

    def test_missing_company_rejected(
        self,
        validator: DecisionSupportValidator,
        valid_prediction: PredictionRecord,
        valid_bill: Bill,
    ) -> None:
        report = validator.validate_inputs(
            prediction=valid_prediction,
            bill=valid_bill,
            company=None,
        )
        assert report.is_valid is False
        assert any("Company metadata missing" in e for e in report.errors)

    def test_version_mismatch_rejected(
        self,
        validator: DecisionSupportValidator,
        valid_prediction: PredictionRecord,
        valid_bill: Bill,
        valid_company: Company,
    ) -> None:
        report = validator.validate_inputs(
            prediction=valid_prediction,
            bill=valid_bill,
            company=valid_company,
            expected_model_version="v2.0",
        )
        assert report.is_valid is False
        assert any("Model version mismatch" in e for e in report.errors)

    def test_invalid_probabilities_rejected(
        self,
        validator: DecisionSupportValidator,
        valid_prediction: PredictionRecord,
        valid_bill: Bill,
        valid_company: Company,
    ) -> None:
        valid_prediction.direction_probability["POSITIVE"] = 1.50  # Out of bounds
        report = validator.validate_inputs(
            prediction=valid_prediction,
            bill=valid_bill,
            company=valid_company,
        )
        assert report.is_valid is False
        assert any("out of bounds" in e for e in report.errors)

    def test_nan_probabilities_rejected(
        self,
        validator: DecisionSupportValidator,
        valid_prediction: PredictionRecord,
        valid_bill: Bill,
        valid_company: Company,
    ) -> None:
        valid_prediction.market_moving_probability = float("nan")
        report = validator.validate_inputs(
            prediction=valid_prediction,
            bill=valid_bill,
            company=valid_company,
        )
        assert report.is_valid is False
        assert any("Market-moving probability" in e for e in report.errors)

    def test_anticipation_score_out_of_bounds_rejected(
        self,
        validator: DecisionSupportValidator,
        valid_prediction: PredictionRecord,
        valid_bill: Bill,
        valid_company: Company,
    ) -> None:
        valid_prediction.anticipation_score = 1.8
        report = validator.validate_inputs(
            prediction=valid_prediction,
            bill=valid_bill,
            company=valid_company,
        )
        assert report.is_valid is False
        assert any("Anticipation score is out of bounds" in e for e in report.errors)

    def test_missing_mapping_generates_warning(
        self,
        validator: DecisionSupportValidator,
        valid_prediction: PredictionRecord,
        valid_bill: Bill,
        valid_company: Company,
    ) -> None:
        report = validator.validate_inputs(
            prediction=valid_prediction,
            bill=valid_bill,
            company=valid_company,
            mapping=None,
        )
        assert report.is_valid is True
        assert any("Bill-Company mapping record missing" in w for w in report.warnings)


class TestDecisionRecordValidation:
    def test_valid_record_passes(self, validator: DecisionSupportValidator) -> None:
        record = DecisionSupportRecord(
            decision_id="dec_bill_1_isin_1_[-20,+20]",
            bill_id="the-telecom-act-2024",
            company_isin="INE002A01018",
            event_window="[-20,+20]",
            predicted_direction="POSITIVE",
            direction_probability={"POSITIVE": 0.8, "NEGATIVE": 0.1, "NEUTRAL": 0.1},
            market_moving_probability=0.8,
            predicted_impact_strength="HIGH",
            confidence_probability={"LOW": 0.1, "MEDIUM": 0.2, "HIGH": 0.7},
            anticipation_class="NO_EVIDENCE",
            anticipation_score=0.1,
            impact_score=0.65,
            impact_category="HIGH",
            risk_score=0.35,
            risk_category="LOW",
            pricing_in_risk="VERY_LOW",
            investor_summary="Investor summary text.",
            business_summary="Business summary text.",
            public_summary="Public summary text.",
            decision_reason="Decision reason text.",
            model_version="v1.0",
            feature_version="v1.0",
            generation_timestamp="2026-08-16T12:00:00Z",
        )
        report = validator.validate_decision_record(record)
        assert report.is_valid is True

    def test_invalid_score_and_category_rejected(self, validator: DecisionSupportValidator) -> None:
        record = DecisionSupportRecord(
            decision_id="invalid_id_format",
            bill_id="the-telecom-act-2024",
            company_isin="INE002A01018",
            event_window="[-20,+20]",
            predicted_direction="POSITIVE",
            direction_probability={},
            market_moving_probability=0.8,
            predicted_impact_strength="HIGH",
            confidence_probability={},
            anticipation_class="NO_EVIDENCE",
            anticipation_score=0.1,
            impact_score=1.5,  # Out of bounds
            impact_category="INVALID_CATEGORY",
            risk_score=-0.2,  # Out of bounds
            risk_category="UNKNOWN_RISK",
            pricing_in_risk="INVALID_PRICING",
            investor_summary="",  # Empty
            business_summary="Business summary.",
            public_summary="Public summary.",
            decision_reason="Decision reason.",
            model_version="v1.0",
            feature_version="v1.0",
        )
        report = validator.validate_decision_record(record)
        assert report.is_valid is False
        assert len(report.errors) >= 5
