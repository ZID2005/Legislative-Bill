"""
tests/test_decision_stakeholder.py
==================================
Unit tests for multi-stakeholder perspectives synthesis (Task 7.2).
"""

from __future__ import annotations

import pytest

from decision_support.stakeholder_synthesizer import (
    DISCLAIMER_TEXT,
    StakeholderSynthesizer,
)
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company, MarketCapCategory
from schemas.mapping_record import BillCompanyMapping
from schemas.prediction import PredictionRecord


@pytest.fixture
def synthesizer() -> StakeholderSynthesizer:
    return StakeholderSynthesizer()


@pytest.fixture
def sample_prediction_positive() -> PredictionRecord:
    return PredictionRecord(
        prediction_id="pred_bill_1_isin_1_[-20,+20]",
        bill_id="the-telecom-act-2024",
        company_isin="INE002A01018",
        company_name="Reliance Industries",
        company_symbol="RELIANCE",
        event_window="[-20,+20]",
        predicted_direction="POSITIVE",
        direction_probability={"POSITIVE": 0.82, "NEGATIVE": 0.05, "NEUTRAL": 0.13},
        predicted_market_moving=True,
        market_moving_probability=0.88,
        predicted_impact_strength="HIGH",
        impact_probabilities={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.70, "VERY_HIGH": 0.10},
        predicted_confidence="HIGH",
        confidence_probability={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.80},
        anticipation_class="STRONG_EVIDENCE",
        anticipation_score=0.85,
        model_name={"direction": "lgbm"},
        model_version="v1.0",
        feature_version="v1.0",
        prediction_timestamp="2026-08-16T12:00:00Z",
        decision_reason="Preliminary prediction rationale.",
    )


@pytest.fixture
def sample_prediction_negative() -> PredictionRecord:
    return PredictionRecord(
        prediction_id="pred_bill_2_isin_2_[-20,+20]",
        bill_id="the-mining-cess-amendment-bill-2024",
        company_isin="INE059A01026",
        company_name="Coal India Limited",
        company_symbol="COALINDIA",
        event_window="[-20,+20]",
        predicted_direction="NEGATIVE",
        direction_probability={"POSITIVE": 0.08, "NEGATIVE": 0.78, "NEUTRAL": 0.14},
        predicted_market_moving=True,
        market_moving_probability=0.80,
        predicted_impact_strength="MEDIUM",
        impact_probabilities={"LOW": 0.10, "MEDIUM": 0.65, "HIGH": 0.20, "VERY_HIGH": 0.05},
        predicted_confidence="MEDIUM",
        confidence_probability={"LOW": 0.15, "MEDIUM": 0.70, "HIGH": 0.15},
        anticipation_class="NO_EVIDENCE",
        anticipation_score=0.10,
        model_name={"direction": "lgbm"},
        model_version="v1.0",
        feature_version="v1.0",
        prediction_timestamp="2026-08-16T12:00:00Z",
        decision_reason="Preliminary prediction rationale.",
    )


@pytest.fixture
def sample_company() -> Company:
    return Company(
        isin="INE002A01018",
        company_name="Reliance Industries Limited",
        bse_code="500325",
        ticker_nse="RELIANCE",
        sector="Energy & Telecom",
        industry="Integrated Telecommunications & Refining",
        market_cap_category=MarketCapCategory.LARGE_CAP,
    )


@pytest.fixture
def sample_bill() -> Bill:
    return Bill(
        bill_id="the-telecom-act-2024",
        title="The Telecommunications Act, 2024",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://prsindia.org/bills/the-telecom-act-2024",
        year=2024,
        ministry="Ministry of Communications",
        summary="A bill to overhaul telecommunications regulation, spectrum assignment, and digital network security.",
    )


@pytest.fixture
def sample_mapping() -> BillCompanyMapping:
    return BillCompanyMapping(
        bill_id="the-telecom-act-2024",
        bill_title="The Telecommunications Act, 2024",
        ministry="Ministry of Communications",
        policy_domain="Telecommunications",
        economic_domain="Infrastructure",
        primary_sector="Energy & Telecom",
        candidate_companies=[
            {
                "isin": "INE002A01018",
                "symbol": "RELIANCE",
                "confidence": 0.92,
                "exposure_type": "DIRECT",
                "reason": "Major cellular network provider directly governed by spectrum allocation terms.",
            }
        ],
        mapping_confidence=0.92,
        mapping_reason="Major cellular network provider directly governed by spectrum allocation terms.",
    )


class TestStakeholderNarratives:
    def test_investor_summary_positive_with_strong_anticipation(
        self, synthesizer: StakeholderSynthesizer, sample_prediction_positive: PredictionRecord
    ) -> None:
        summary = synthesizer.generate_investor_summary(
            prediction=sample_prediction_positive,
            impact_score=0.72,
            risk_score=0.45,
            risk_category="MODERATE",
            pricing_in_risk="HIGH",
        )
        assert "potential positive impact" in summary
        assert "82.0%" in summary
        assert "elevated market-moving probability" in summary
        assert "Substantial pre-event market activity suggests part or all of the expected reaction may already be priced in" in summary
        assert "Pricing-In Risk: HIGH" in summary
        # Ensure no illegal phrasing
        assert "insider trading" not in summary.lower()
        assert "guaranteed" not in summary.lower()

    def test_investor_summary_negative_with_low_anticipation(
        self, synthesizer: StakeholderSynthesizer, sample_prediction_negative: PredictionRecord
    ) -> None:
        summary = synthesizer.generate_investor_summary(
            prediction=sample_prediction_negative,
            impact_score=0.60,
            risk_score=0.35,
            risk_category="LOW",
            pricing_in_risk="VERY_LOW",
        )
        assert "potential negative impact" in summary
        assert "78.0%" in summary
        assert "Limited pre-event evidence suggests a larger portion of the predicted reaction may occur around the event window" in summary

    def test_business_summary_generation(
        self,
        synthesizer: StakeholderSynthesizer,
        sample_prediction_positive: PredictionRecord,
        sample_company: Company,
        sample_bill: Bill,
        sample_mapping: BillCompanyMapping,
    ) -> None:
        summary = synthesizer.generate_business_summary(
            prediction=sample_prediction_positive,
            company=sample_company,
            bill=sample_bill,
            mapping=sample_mapping,
        )
        assert "The Telecommunications Act, 2024" in summary
        assert "Ministry of Communications" in summary
        assert "Reliance Industries Limited" in summary
        assert "Energy & Telecom" in summary
        assert "relevance of 0.92" in summary
        assert "potential positive business implications" in summary

    def test_public_summary_plain_english(
        self,
        synthesizer: StakeholderSynthesizer,
        sample_bill: Bill,
        sample_prediction_positive: PredictionRecord,
    ) -> None:
        summary = synthesizer.generate_public_summary(
            bill=sample_bill,
            prediction=sample_prediction_positive,
        )
        assert "The Telecommunications Act, 2024" in summary
        assert "Ministry of Communications" in summary
        assert "overhaul telecommunications regulation" in summary
        assert "without financial or market jargon" in summary

    def test_decision_reason_disclaimer_integration(
        self, synthesizer: StakeholderSynthesizer, sample_prediction_positive: PredictionRecord
    ) -> None:
        reason = synthesizer.synthesize_decision_reason(
            prediction=sample_prediction_positive,
            impact_score=0.72,
            risk_score=0.45,
            risk_category="MODERATE",
            pricing_in_risk="HIGH",
            investor_summary="Investor summary text.",
        )
        assert "Decision support assessment indicates a potential positive market impact" in reason
        assert "0.72" in reason
        assert "0.45" in reason
        assert "Pricing-in risk is evaluated as HIGH" in reason
        assert DISCLAIMER_TEXT in reason

    def test_investor_summary_neutral_and_moderate_anticipation(
        self, synthesizer: StakeholderSynthesizer, sample_prediction_positive: PredictionRecord
    ) -> None:
        sample_prediction_positive.predicted_direction = "NEUTRAL"
        sample_prediction_positive.predicted_market_moving = False
        sample_prediction_positive.market_moving_probability = 0.20
        sample_prediction_positive.anticipation_class = "MODERATE_EVIDENCE"
        sample_prediction_positive.anticipation_score = 0.55
        summary = synthesizer.generate_investor_summary(
            prediction=sample_prediction_positive,
            impact_score=0.15,
            risk_score=0.20,
            risk_category="VERY_LOW",
            pricing_in_risk="MODERATE",
        )
        assert "neutral or subdued market reaction" in summary
        assert "low market-moving probability" in summary
        assert "partial pricing-in is plausible" in summary

    def test_investor_summary_weak_anticipation_and_very_high_impact(
        self, synthesizer: StakeholderSynthesizer, sample_prediction_positive: PredictionRecord
    ) -> None:
        sample_prediction_positive.predicted_impact_strength = "VERY_HIGH"
        sample_prediction_positive.anticipation_class = "WEAK_EVIDENCE"
        sample_prediction_positive.anticipation_score = 0.20
        summary = synthesizer.generate_investor_summary(
            prediction=sample_prediction_positive,
            impact_score=0.88,
            risk_score=0.65,
            risk_category="HIGH",
            pricing_in_risk="LOW",
        )
        assert "potential positive impact" in summary
        assert "very_high impact strength tier" in summary
        assert "Limited pre-event evidence suggests a larger portion of the predicted reaction" in summary

    def test_business_summary_negative_and_neutral(
        self,
        synthesizer: StakeholderSynthesizer,
        sample_prediction_negative: PredictionRecord,
        sample_company: Company,
        sample_bill: Bill,
    ) -> None:
        # Negative branch
        summary_neg = synthesizer.generate_business_summary(
            prediction=sample_prediction_negative,
            company=sample_company,
            bill=sample_bill,
            mapping=None,
        )
        assert "potential negative business implications" in summary_neg
        assert "compliance costs" in summary_neg

        # Neutral branch
        sample_prediction_negative.predicted_direction = "NEUTRAL"
        summary_neu = synthesizer.generate_business_summary(
            prediction=sample_prediction_negative,
            company=sample_company,
            bill=sample_bill,
            mapping=None,
        )
        assert "neutral net business implications" in summary_neu

    def test_public_summary_without_bill_summary(
        self,
        synthesizer: StakeholderSynthesizer,
        sample_prediction_positive: PredictionRecord,
    ) -> None:
        bill_no_summary = Bill(
            bill_id="the-customs-act-2024",
            title="The Customs Amendment Act, 2024",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://prsindia.org/bills/the-customs-act-2024",
            year=2024,
            ministry="Ministry of Finance",
            summary="",
        )
        summary = synthesizer.generate_public_summary(
            bill=bill_no_summary,
            prediction=sample_prediction_positive,
        )
        assert "The Customs Amendment Act, 2024" in summary
        assert "Ministry of Finance" in summary

