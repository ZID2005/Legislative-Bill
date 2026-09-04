"""
tests/test_decision_risk_scorer.py
==================================
Unit tests for deterministic mathematical risk and impact scoring (Task 7.2).
"""

from __future__ import annotations

import math
import pytest

from decision_support.risk_scorer import RiskScorer
from schemas.decision import PricingInRisk, RiskCategory


@pytest.fixture
def default_scorer() -> RiskScorer:
    return RiskScorer()


class TestCategorization:
    def test_default_category_thresholds(self, default_scorer: RiskScorer) -> None:
        assert default_scorer.categorize_score(0.10) == RiskCategory.VERY_LOW.value
        assert default_scorer.categorize_score(0.30) == RiskCategory.LOW.value
        assert default_scorer.categorize_score(0.50) == RiskCategory.MODERATE.value
        assert default_scorer.categorize_score(0.70) == RiskCategory.HIGH.value
        assert default_scorer.categorize_score(0.90) == RiskCategory.VERY_HIGH.value

    def test_clamped_boundary_values(self, default_scorer: RiskScorer) -> None:
        assert default_scorer.categorize_score(0.0) == RiskCategory.VERY_LOW.value
        assert default_scorer.categorize_score(1.0) == RiskCategory.VERY_HIGH.value
        assert default_scorer.categorize_score(1.5) == RiskCategory.VERY_HIGH.value
        assert default_scorer.categorize_score(-0.5) == RiskCategory.VERY_LOW.value

    def test_invalid_nan_inf_categorization(self, default_scorer: RiskScorer) -> None:
        with pytest.raises(ValueError):
            default_scorer.categorize_score(float("nan"))
        with pytest.raises(ValueError):
            default_scorer.categorize_score(float("inf"))


class TestPricingInRisk:
    def test_pricing_in_tiers(self, default_scorer: RiskScorer) -> None:
        score, cat = default_scorer.compute_pricing_in_risk(0.15)
        assert score == 0.15
        assert cat == PricingInRisk.VERY_LOW.value

        score, cat = default_scorer.compute_pricing_in_risk(0.35)
        assert score == 0.35
        assert cat == PricingInRisk.LOW.value

        score, cat = default_scorer.compute_pricing_in_risk(0.60)
        assert score == 0.60
        assert cat == PricingInRisk.MODERATE.value

        score, cat = default_scorer.compute_pricing_in_risk(0.85)
        assert score == 0.85
        assert cat == PricingInRisk.HIGH.value

    def test_invalid_nan_anticipation_score_handling(self, default_scorer: RiskScorer) -> None:
        score, cat = default_scorer.compute_pricing_in_risk(float("nan"))
        assert score == 0.0
        assert cat == PricingInRisk.VERY_LOW.value


class TestConfidenceScore:
    def test_compute_confidence_score(self, default_scorer: RiskScorer) -> None:
        conf_probs = {"LOW": 0.10, "MEDIUM": 0.20, "HIGH": 0.70}
        score, cat = default_scorer.compute_confidence_score(conf_probs, model_confidence=0.80)
        assert 0.0 <= score <= 1.0
        # prob_weighted = 0.20*0.1 + 0.60*0.2 + 1.00*0.7 = 0.02 + 0.12 + 0.70 = 0.84
        # score = 0.40 * 0.80 + 0.60 * 0.84 = 0.32 + 0.504 = 0.824
        assert pytest.approx(score, abs=0.01) == 0.824
        assert cat == RiskCategory.VERY_HIGH.value

    def test_nan_confidence_error(self, default_scorer: RiskScorer) -> None:
        with pytest.raises(ValueError):
            default_scorer.compute_confidence_score({"LOW": float("nan"), "MEDIUM": 0.5, "HIGH": 0.5})


class TestImpactScore:
    def test_high_impact_scenario(self, default_scorer: RiskScorer) -> None:
        dir_probs = {"POSITIVE": 0.90, "NEGATIVE": 0.05, "NEUTRAL": 0.05}
        impact_probs = {"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.60, "VERY_HIGH": 0.20}
        score, cat = default_scorer.compute_impact_score(
            direction_probs=dir_probs,
            market_moving_prob=0.90,
            impact_probs=impact_probs,
            confidence_scalar=0.85,
            anticipation_score=0.10,
            predicted_direction="POSITIVE",
        )
        assert 0.0 <= score <= 1.0
        assert score > 0.50
        assert cat in [RiskCategory.MODERATE.value, RiskCategory.HIGH.value, RiskCategory.VERY_HIGH.value]

    def test_anticipation_dampening_effect(self, default_scorer: RiskScorer) -> None:
        dir_probs = {"POSITIVE": 0.90, "NEGATIVE": 0.05, "NEUTRAL": 0.05}
        impact_probs = {"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.60, "VERY_HIGH": 0.20}

        # Scenario 1: Low anticipation (Novel event)
        score_novel, _ = default_scorer.compute_impact_score(
            direction_probs=dir_probs,
            market_moving_prob=0.90,
            impact_probs=impact_probs,
            confidence_scalar=0.85,
            anticipation_score=0.0,
            predicted_direction="POSITIVE",
        )

        # Scenario 2: High anticipation (Priced-in event)
        score_priced_in, _ = default_scorer.compute_impact_score(
            direction_probs=dir_probs,
            market_moving_prob=0.90,
            impact_probs=impact_probs,
            confidence_scalar=0.85,
            anticipation_score=0.90,
            predicted_direction="POSITIVE",
        )

        # High anticipation should mathematically dampen novel post-event impact score
        assert score_novel > score_priced_in

    def test_neutral_non_market_moving_impact(self, default_scorer: RiskScorer) -> None:
        dir_probs = {"POSITIVE": 0.05, "NEGATIVE": 0.05, "NEUTRAL": 0.90}
        impact_probs = {"LOW": 0.90, "MEDIUM": 0.10, "HIGH": 0.0, "VERY_HIGH": 0.0}
        score, cat = default_scorer.compute_impact_score(
            direction_probs=dir_probs,
            market_moving_prob=0.05,
            impact_probs=impact_probs,
            confidence_scalar=0.70,
            anticipation_score=0.10,
            predicted_direction="NEUTRAL",
        )
        assert score < 0.20
        assert cat == RiskCategory.VERY_LOW.value

    def test_nan_impact_inputs_raise_error(self, default_scorer: RiskScorer) -> None:
        with pytest.raises(ValueError):
            default_scorer.compute_impact_score(
                direction_probs={"POSITIVE": float("nan")},
                market_moving_prob=0.5,
                impact_probs={"LOW": 1.0},
                confidence_scalar=0.5,
                anticipation_score=0.5,
            )


class TestRiskScore:
    def test_high_uncertainty_elevates_decision_risk(self, default_scorer: RiskScorer) -> None:
        dir_probs_conflict = {"POSITIVE": 0.50, "NEGATIVE": 0.50, "NEUTRAL": 0.0}
        impact_probs = {"LOW": 0.25, "MEDIUM": 0.25, "HIGH": 0.25, "VERY_HIGH": 0.25}

        # Low confidence + high anticipation + conflict = HIGH risk
        high_risk, cat_high = default_scorer.compute_risk_score(
            confidence_scalar=0.10,
            anticipation_score=0.90,
            market_moving_prob=0.80,
            impact_probs=impact_probs,
            direction_probs=dir_probs_conflict,
        )

        # High confidence + zero anticipation + decisive direction = LOW risk
        dir_probs_decisive = {"POSITIVE": 0.95, "NEGATIVE": 0.0, "NEUTRAL": 0.05}
        low_risk, cat_low = default_scorer.compute_risk_score(
            confidence_scalar=0.95,
            anticipation_score=0.05,
            market_moving_prob=0.20,
            impact_probs={"LOW": 0.8, "MEDIUM": 0.2, "HIGH": 0.0, "VERY_HIGH": 0.0},
            direction_probs=dir_probs_decisive,
        )

        assert high_risk > low_risk
        assert high_risk > 0.50
        assert low_risk < 0.40

    def test_nan_risk_inputs_raise_error(self, default_scorer: RiskScorer) -> None:
        with pytest.raises(ValueError):
            default_scorer.compute_risk_score(
                confidence_scalar=float("nan"),
                anticipation_score=0.5,
                market_moving_prob=0.5,
                impact_probs={},
                direction_probs={},
            )
