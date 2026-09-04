"""
decision_support/risk_scorer.py
===============================
Deterministic mathematical risk and impact scoring engine (Task 7.2).

Architectural Principles
------------------------
1. Strict Mathematical Determinism: All scores are purely mathematical functions
   of validated model probability distributions and Task 6.5 anticipation evidence.
2. Anti-Leakage / Forward-Looking Integrity: Never consumes future event-study CAR,
   ground-truth labels, or post-event market prices.
3. Bounded & Safe: All inputs and outputs are strictly validated and constrained to [0.0, 1.0],
   with defensive guards against NaN, Inf, and missing probability keys.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.decision import PricingInRisk, RiskCategory

logger = get_logger(__name__)


def _is_valid_num(val: Any) -> bool:
    """Check whether value is a finite float/int."""
    if val is None:
        return False
    if not isinstance(val, (int, float)):
        return False
    return not (math.isnan(val) or math.isinf(val))


def _clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp float value to [min_val, max_val]."""
    return max(min_val, min(max_val, val))


class RiskScorer:
    """
    Computes composite impact, risk, confidence, and pricing-in metrics
    using configurable deterministic mathematical weighting.
    """

    def __init__(
        self,
        weight_direction_polarity: Optional[float] = None,
        weight_impact_strength: Optional[float] = None,
        anticipation_discount_factor: Optional[float] = None,
        risk_uncertainty_weight: Optional[float] = None,
        risk_anticipation_weight: Optional[float] = None,
        risk_tail_magnitude_weight: Optional[float] = None,
        risk_directional_conflict_weight: Optional[float] = None,
        risk_threshold_very_low: Optional[float] = None,
        risk_threshold_low: Optional[float] = None,
        risk_threshold_moderate: Optional[float] = None,
        risk_threshold_high: Optional[float] = None,
    ) -> None:
        self.w_dir_polarity = (
            weight_direction_polarity
            if weight_direction_polarity is not None
            else settings.DECISION_WEIGHT_DIRECTION_POLARITY
        )
        self.w_impact_strength = (
            weight_impact_strength
            if weight_impact_strength is not None
            else settings.DECISION_WEIGHT_IMPACT_STRENGTH
        )
        self.anticipation_discount = (
            anticipation_discount_factor
            if anticipation_discount_factor is not None
            else settings.DECISION_ANTICIPATION_DISCOUNT_FACTOR
        )

        self.w_risk_uncert = (
            risk_uncertainty_weight
            if risk_uncertainty_weight is not None
            else settings.DECISION_RISK_UNCERTAINTY_WEIGHT
        )
        self.w_risk_anticip = (
            risk_anticipation_weight
            if risk_anticipation_weight is not None
            else settings.DECISION_RISK_ANTICIPATION_WEIGHT
        )
        self.w_risk_tail_mag = (
            risk_tail_magnitude_weight
            if risk_tail_magnitude_weight is not None
            else settings.DECISION_RISK_TAIL_MAGNITUDE_WEIGHT
        )
        self.w_risk_dir_conflict = (
            risk_directional_conflict_weight
            if risk_directional_conflict_weight is not None
            else settings.DECISION_RISK_DIRECTIONAL_CONFLICT_WEIGHT
        )

        self.thresh_very_low = (
            risk_threshold_very_low
            if risk_threshold_very_low is not None
            else settings.RISK_THRESHOLD_VERY_LOW
        )
        self.thresh_low = (
            risk_threshold_low
            if risk_threshold_low is not None
            else settings.RISK_THRESHOLD_LOW
        )
        self.thresh_moderate = (
            risk_threshold_moderate
            if risk_threshold_moderate is not None
            else settings.RISK_THRESHOLD_MODERATE
        )
        self.thresh_high = (
            risk_threshold_high
            if risk_threshold_high is not None
            else settings.RISK_THRESHOLD_HIGH
        )

    # ------------------------------------------------------------------
    # Category Assignment
    # ------------------------------------------------------------------

    def categorize_score(self, score: float) -> str:
        """
        Map a continuous score [0.0, 1.0] to a RiskCategory tier.
        """
        if not _is_valid_num(score):
            raise ValueError(f"Invalid score value for categorization: {score}")

        score = _clamp(score, 0.0, 1.0)
        if score < self.thresh_very_low:
            return RiskCategory.VERY_LOW.value
        elif score < self.thresh_low:
            return RiskCategory.LOW.value
        elif score < self.thresh_moderate:
            return RiskCategory.MODERATE.value
        elif score < self.thresh_high:
            return RiskCategory.HIGH.value
        else:
            return RiskCategory.VERY_HIGH.value

    # ------------------------------------------------------------------
    # Pricing-in Risk Computation
    # ------------------------------------------------------------------

    def compute_pricing_in_risk(
        self, anticipation_score: float, anticipation_class: str = "NOT_ANALYZED"
    ) -> tuple[float, str]:
        """
        Compute pricing-in risk score and categorical tier from Task 6.5 anticipation metrics.

        Parameters
        ----------
        anticipation_score : float
            Pre-event anticipation score [0.0, 1.0].
        anticipation_class : str
            Categorical anticipation classification.

        Returns
        -------
        tuple[float, str]
            (pricing_in_score, pricing_in_risk_tier)
        """
        if not _is_valid_num(anticipation_score):
            logger.warning("Invalid anticipation_score: %s, defaulting to 0.0", anticipation_score)
            anticipation_score = 0.0

        p_score = round(_clamp(anticipation_score, 0.0, 1.0), 4)

        if p_score < 0.25:
            cat = PricingInRisk.VERY_LOW.value
        elif p_score < 0.50:
            cat = PricingInRisk.LOW.value
        elif p_score < 0.75:
            cat = PricingInRisk.MODERATE.value
        else:
            cat = PricingInRisk.HIGH.value

        return p_score, cat

    # ------------------------------------------------------------------
    # Confidence Score Computation
    # ------------------------------------------------------------------

    def compute_confidence_score(
        self,
        confidence_probs: dict[str, float],
        model_confidence: float = 0.0,
    ) -> tuple[float, str]:
        """
        Compute composite confidence scalar [0.0, 1.0] and category.

        Formula:
        S_conf = clip(0.40 * model_confidence + 0.60 * (0.20 * P(LOW) + 0.60 * P(MEDIUM) + 1.00 * P(HIGH)), 0.0, 1.0)
        """
        p_low = confidence_probs.get("LOW", 0.0)
        p_med = confidence_probs.get("MEDIUM", 0.0)
        p_high = confidence_probs.get("HIGH", 0.0)

        for p_name, p_val in [("LOW", p_low), ("MEDIUM", p_med), ("HIGH", p_high), ("model_confidence", model_confidence)]:
            if not _is_valid_num(p_val):
                raise ValueError(f"Invalid confidence probability for {p_name}: {p_val}")

        prob_weighted = 0.20 * p_low + 0.60 * p_med + 1.00 * p_high
        m_conf = _clamp(model_confidence, 0.0, 1.0) if model_confidence > 0.0 else prob_weighted

        conf_scalar = round(_clamp(0.40 * m_conf + 0.60 * prob_weighted, 0.0, 1.0), 4)
        cat = self.categorize_score(conf_scalar)
        return conf_scalar, cat

    # ------------------------------------------------------------------
    # Impact Score Computation
    # ------------------------------------------------------------------

    def compute_impact_score(
        self,
        direction_probs: dict[str, float],
        market_moving_prob: float,
        impact_probs: dict[str, float],
        confidence_scalar: float,
        anticipation_score: float,
        predicted_direction: str = "NEUTRAL",
    ) -> tuple[float, str]:
        """
        Compute deterministic composite impact score [0.0, 1.0] and category tier.

        Formula:
        1. S_polarity = |P(POSITIVE) - P(NEGATIVE)|
        2. S_strength = 0.20 * P(LOW) + 0.50 * P(MED) + 0.80 * P(HIGH) + 1.00 * P(VHIGH)
        3. anticipation_adj = max(0.0, 1.0 - delta * anticipation_score)
        4. weighted_strength = w_dir * S_polarity + w_strength * S_strength
        5. impact_score = clip(weighted_strength * market_moving_prob * (0.50 + 0.50 * conf) * anticipation_adj, 0.0, 1.0)
        """
        p_pos = direction_probs.get("POSITIVE", 0.0)
        p_neg = direction_probs.get("NEGATIVE", 0.0)
        p_neu = direction_probs.get("NEUTRAL", 0.0)

        for name, val in [
            ("P(POSITIVE)", p_pos),
            ("P(NEGATIVE)", p_neg),
            ("P(NEUTRAL)", p_neu),
            ("market_moving_prob", market_moving_prob),
            ("confidence_scalar", confidence_scalar),
            ("anticipation_score", anticipation_score),
        ]:
            if not _is_valid_num(val):
                raise ValueError(f"Invalid input for {name}: {val}")

        p_low = impact_probs.get("LOW", 0.0)
        p_med = impact_probs.get("MEDIUM", 0.0)
        p_high = impact_probs.get("HIGH", 0.0)
        p_vhigh = impact_probs.get("VERY_HIGH", 0.0)

        s_polarity = abs(p_pos - p_neg)
        s_strength = 0.20 * p_low + 0.50 * p_med + 0.80 * p_high + 1.00 * p_vhigh

        # If direction is neutral, directional conviction is dampened
        if predicted_direction == "NEUTRAL":
            s_polarity *= (1.0 - p_neu)

        anticipation_adj = max(0.0, 1.0 - self.anticipation_discount * _clamp(anticipation_score, 0.0, 1.0))
        conf_adj = 0.50 + 0.50 * _clamp(confidence_scalar, 0.0, 1.0)

        weighted_strength = (
            self.w_dir_polarity * s_polarity + self.w_impact_strength * s_strength
        )
        raw_impact = weighted_strength * _clamp(market_moving_prob, 0.0, 1.0) * conf_adj * anticipation_adj
        impact_score = round(_clamp(raw_impact, 0.0, 1.0), 4)
        cat = self.categorize_score(impact_score)
        return impact_score, cat

    # ------------------------------------------------------------------
    # Risk Score Computation
    # ------------------------------------------------------------------

    def compute_risk_score(
        self,
        confidence_scalar: float,
        anticipation_score: float,
        market_moving_prob: float,
        impact_probs: dict[str, float],
        direction_probs: dict[str, float],
    ) -> tuple[float, str]:
        """
        Compute deterministic composite decision risk score [0.0, 1.0] and category tier.

        Formula:
        risk_score = clip(
            w_uncert * (1.0 - S_confidence) +
            w_anticip * anticipation_score +
            w_mag * (market_moving_prob * S_strength) +
            w_conflict * (1.0 - |P(POSITIVE) - P(NEGATIVE)|),
            0.0, 1.0
        )
        """
        for name, val in [
            ("confidence_scalar", confidence_scalar),
            ("anticipation_score", anticipation_score),
            ("market_moving_prob", market_moving_prob),
        ]:
            if not _is_valid_num(val):
                raise ValueError(f"Invalid input for {name}: {val}")

        p_pos = direction_probs.get("POSITIVE", 0.0)
        p_neg = direction_probs.get("NEGATIVE", 0.0)
        s_polarity = abs(p_pos - p_neg)

        p_low = impact_probs.get("LOW", 0.0)
        p_med = impact_probs.get("MEDIUM", 0.0)
        p_high = impact_probs.get("HIGH", 0.0)
        p_vhigh = impact_probs.get("VERY_HIGH", 0.0)
        s_strength = 0.20 * p_low + 0.50 * p_med + 0.80 * p_high + 1.00 * p_vhigh

        c_scalar = _clamp(confidence_scalar, 0.0, 1.0)
        a_score = _clamp(anticipation_score, 0.0, 1.0)
        mm_prob = _clamp(market_moving_prob, 0.0, 1.0)

        uncert_term = self.w_risk_uncert * (1.0 - c_scalar)
        anticip_term = self.w_risk_anticip * a_score
        mag_term = self.w_risk_tail_mag * (mm_prob * s_strength)
        conflict_term = self.w_risk_dir_conflict * (1.0 - s_polarity)

        raw_risk = uncert_term + anticip_term + mag_term + conflict_term
        risk_score = round(_clamp(raw_risk, 0.0, 1.0), 4)
        cat = self.categorize_score(risk_score)
        return risk_score, cat
