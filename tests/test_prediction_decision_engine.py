"""
tests/test_prediction_decision_engine.py
========================================
Unit tests for DecisionEngine contextual reasoning and anticipation integration (Task 7.1).
"""

from __future__ import annotations

import pytest

from prediction.decision_engine import DISCLAIMER_TEXT, DecisionEngine
from schemas.anticipation import AnticipationClassification, AnticipationScore


@pytest.fixture
def decision_engine() -> DecisionEngine:
    return DecisionEngine()


class TestDecisionEngine:
    def test_strong_anticipation_integration_narrative(
        self, decision_engine: DecisionEngine
    ) -> None:
        anticipation_rec = AnticipationScore(
            bill_id="telecom-bill-2023",
            company_isin="INE002A01018",
            company_symbol="RELIANCE",
            official_introduction_date="2023-08-01",
            market_signal_score=0.85,
            information_signal_score=0.80,
            anticipation_score=0.82,
            classification=AnticipationClassification.STRONG_EVIDENCE.value,
            anticipation_flag=True,
            confidence="HIGH",
            evidence_count=5,
            media_data_available=True,
            decision_reason="Strong abnormal pre-event volume and return run-up.",
        )

        direction_probs = {"POSITIVE": 0.85, "NEGATIVE": 0.05, "NEUTRAL": 0.10}
        impact_probs = {"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.70, "VERY_HIGH": 0.10}
        confidence_probs = {"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.80}

        (
            reason,
            impact_est,
            risk_indicators,
            scalar_conf,
            data_quality,
        ) = decision_engine.generate_decision_support(
            predicted_direction="POSITIVE",
            direction_probs=direction_probs,
            predicted_market_moving=True,
            market_moving_prob=0.88,
            predicted_impact_strength="HIGH",
            impact_probs=impact_probs,
            predicted_confidence="HIGH",
            confidence_probs=confidence_probs,
            anticipation_score_record=anticipation_rec,
            company_meta={"beta": 1.6, "is_imputed": False},
        )

        assert "Prediction is positive with high model confidence" in reason
        assert "substantial pre-event market activity" in reason
        assert "priced in" in reason
        assert DISCLAIMER_TEXT in reason
        assert impact_est is not None
        assert "Expected positive abnormal return in range [+3.0% to 6.0%]" in impact_est
        assert any("priced-in" in r for r in risk_indicators)
        assert any("Beta = 1.60" in r for r in risk_indicators)
        assert scalar_conf >= 0.75
        assert data_quality == "VALID"

    def test_moderate_anticipation_integration(
        self, decision_engine: DecisionEngine
    ) -> None:
        anticipation_rec = AnticipationScore(
            bill_id="data-protection-bill",
            company_isin="INE009A01021",
            company_symbol="INFY",
            official_introduction_date="2023-08-01",
            market_signal_score=0.55,
            information_signal_score=0.50,
            anticipation_score=0.52,
            classification=AnticipationClassification.MODERATE_EVIDENCE.value,
            anticipation_flag=True,
            confidence="MEDIUM",
            evidence_count=2,
            media_data_available=True,
            decision_reason="Moderate signals.",
        )

        (
            reason,
            impact_est,
            risk_indicators,
            scalar_conf,
            data_quality,
        ) = decision_engine.generate_decision_support(
            predicted_direction="NEGATIVE",
            direction_probs={"POSITIVE": 0.1, "NEGATIVE": 0.7, "NEUTRAL": 0.2},
            predicted_market_moving=True,
            market_moving_prob=0.75,
            predicted_impact_strength="MEDIUM",
            impact_probs={"LOW": 0.1, "MEDIUM": 0.7, "HIGH": 0.1, "VERY_HIGH": 0.1},
            predicted_confidence="MEDIUM",
            confidence_probs={"LOW": 0.2, "MEDIUM": 0.6, "HIGH": 0.2},
            anticipation_score_record=anticipation_rec,
            company_meta={"beta": 0.4},
        )

        assert "Prediction is negative" in reason
        assert "partial price-in possible" in reason or "Moderate pre-event" in reason
        assert any("Low market sensitivity (Beta = 0.40)" in r for r in risk_indicators)

    def test_no_anticipation_novel_event(
        self, decision_engine: DecisionEngine
    ) -> None:
        anticipation_rec = AnticipationScore(
            bill_id="surprise-amendment-bill",
            company_isin="INE001",
            company_symbol="TEST",
            official_introduction_date="2024-01-01",
            market_signal_score=0.1,
            information_signal_score=0.1,
            anticipation_score=0.1,
            classification=AnticipationClassification.NO_EVIDENCE.value,
            anticipation_flag=False,
            confidence="LOW",
            evidence_count=0,
            media_data_available=False,
            decision_reason="No evidence.",
        )

        (
            reason,
            impact_est,
            risk_indicators,
            scalar_conf,
            data_quality,
        ) = decision_engine.generate_decision_support(
            predicted_direction="POSITIVE",
            direction_probs={"POSITIVE": 0.9, "NEGATIVE": 0.05, "NEUTRAL": 0.05},
            predicted_market_moving=True,
            market_moving_prob=0.9,
            predicted_impact_strength="VERY_HIGH",
            impact_probs={"LOW": 0.05, "MEDIUM": 0.05, "HIGH": 0.1, "VERY_HIGH": 0.8},
            predicted_confidence="HIGH",
            confidence_probs={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.8},
            anticipation_score_record=anticipation_rec,
        )

        assert "Little to no pre-event market anticipation detected" in reason
        assert "novel to the market" in reason
        assert "> 6.0%" in str(impact_est)

    def test_neutral_impact_and_imputed_data_quality(
        self, decision_engine: DecisionEngine
    ) -> None:
        (
            reason,
            impact_est,
            risk_indicators,
            scalar_conf,
            data_quality,
        ) = decision_engine.generate_decision_support(
            predicted_direction="NEUTRAL",
            direction_probs={"POSITIVE": 0.2, "NEGATIVE": 0.2, "NEUTRAL": 0.6},
            predicted_market_moving=False,
            market_moving_prob=0.2,
            predicted_impact_strength="LOW",
            impact_probs={"LOW": 0.8, "MEDIUM": 0.1, "HIGH": 0.05, "VERY_HIGH": 0.05},
            predicted_confidence="LOW",
            confidence_probs={"LOW": 0.7, "MEDIUM": 0.2, "HIGH": 0.1},
            anticipation_score_record=None,
            company_meta={"is_imputed": True},
        )

        assert "Model predicts neutral market impact" in reason
        assert "Expected neutral market impact" in str(impact_est)
        assert any("Low model confidence" in r for r in risk_indicators)
        assert data_quality == "IMPUTED"
