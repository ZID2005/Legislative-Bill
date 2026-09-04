"""
prediction/decision_engine.py
=============================
Contextual decision-support and anticipation reasoning engine (Task 7.1).

Architectural Principle
-----------------------
The prediction engine must NOT blindly convert statistical model probabilities into
deterministic trading recommendations.

This module enforces a strict separation between:
1. **Model Prediction**: Pure mathematical classification outputs and class probabilities.
2. **Decision-Support Interpretation**: Qualitative financial synthesis integrating model
   confidence, impact magnitude, and Task 6.5 pre-event anticipation evidence.

Anticipation Integration Rationale
----------------------------------
- If high predicted impact + strong anticipation:
  Explains that pre-event market activity suggests substantial price-in before introduction,
  warning against chasing post-event returns.
- If high predicted impact + no anticipation:
  Notes that the event appears un-anticipated, indicating potential for novel market repricing.
- Explicit non-guarantee disclaimer: Probabilistic quantitative intelligence only, NOT investment advice.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from schemas.anticipation import AnticipationClassification, AnticipationScore

logger = get_logger(__name__)

# Standard academic / quantitative decision disclaimer
DISCLAIMER_TEXT = (
    "Probabilistic decision-support assessment for quantitative research purposes only. "
    "Does not constitute guaranteed price movements or investment advice."
)


class DecisionEngine:
    """
    Synthesizes contextual decision-support interpretations by blending multi-target
    model predictions with Task 6.5 anticipation evidence and financial risk indicators.
    """

    def generate_decision_support(
        self,
        predicted_direction: str,
        direction_probs: dict[str, float],
        predicted_market_moving: bool,
        market_moving_prob: float,
        predicted_impact_strength: str,
        impact_probs: dict[str, float],
        predicted_confidence: str,
        confidence_probs: dict[str, float],
        anticipation_score_record: Optional[AnticipationScore] = None,
        company_meta: Optional[dict[str, Any]] = None,
    ) -> tuple[str, Optional[str], list[str], float, str]:
        """
        Synthesize decision reason, expected impact estimate, risk indicators, scalar confidence, and data quality status.

        Returns
        -------
        tuple[str, Optional[str], list[str], float, str]
            (decision_reason, expected_impact_estimate, risk_indicators, model_confidence_scalar, data_quality_status)
        """
        company_meta = company_meta or {}
        risk_indicators: list[str] = []

        # 1. Compute summary model confidence score
        dir_conf = direction_probs.get(predicted_direction, 0.5)
        conf_high_prob = confidence_probs.get("HIGH", 0.0)
        conf_med_prob = confidence_probs.get("MEDIUM", 0.0)
        scalar_confidence = round(
            float(0.6 * dir_conf + 0.3 * conf_high_prob + 0.1 * (1.0 - confidence_probs.get("LOW", 0.0))),
            4,
        )
        scalar_confidence = max(0.0, min(1.0, scalar_confidence))

        # 2. Extract anticipation details
        anticipation_class = "NOT_ANALYZED"
        anticipation_score = 0.0
        anticipation_flag = False
        if anticipation_score_record is not None:
            anticipation_class = str(anticipation_score_record.classification)
            anticipation_score = float(anticipation_score_record.anticipation_score)
            anticipation_flag = bool(anticipation_score_record.anticipation_flag)

        # 3. Assess Risk Indicators
        if anticipation_class in {
            AnticipationClassification.STRONG_EVIDENCE.value,
            "STRONG_EVIDENCE",
        } or anticipation_score >= 0.75:
            risk_indicators.append(
                f"Substantial pre-event market anticipation detected (Score: {anticipation_score:.2f}) — high risk of priced-in event reaction."
            )
        elif anticipation_class in {
            AnticipationClassification.MODERATE_EVIDENCE.value,
            "MODERATE_EVIDENCE",
        } or anticipation_score >= 0.50:
            risk_indicators.append(
                f"Moderate pre-event market activity observed (Score: {anticipation_score:.2f}) — partial pricing-in possible."
            )

        if predicted_confidence == "LOW" or dir_conf < 0.55:
            risk_indicators.append(
                f"Low model confidence ({dir_conf*100:.1f}% direction probability) — high forecast uncertainty."
            )

        beta_val = company_meta.get("beta")
        if beta_val is not None and isinstance(beta_val, (int, float)):
            if beta_val > 1.5:
                risk_indicators.append(f"Elevated systematic risk (Beta = {beta_val:.2f}).")
            elif beta_val < 0.5:
                risk_indicators.append(f"Low market sensitivity (Beta = {beta_val:.2f}).")

        # 4. Formulate Expected Impact Estimate
        expected_impact_estimate = self._build_impact_estimate(
            direction=predicted_direction,
            dir_prob=dir_conf,
            market_moving=predicted_market_moving,
            strength=predicted_impact_strength,
        )

        # 5. Formulate Synthesized Decision Reason
        decision_reason = self._build_decision_narrative(
            direction=predicted_direction,
            dir_prob=dir_conf,
            market_moving=predicted_market_moving,
            strength=predicted_impact_strength,
            confidence=predicted_confidence,
            anticipation_class=anticipation_class,
            anticipation_score=anticipation_score,
            anticipation_flag=anticipation_flag,
        )

        data_quality_status = "VALID"
        if company_meta.get("is_imputed", False):
            data_quality_status = "IMPUTED"

        return (
            decision_reason,
            expected_impact_estimate,
            risk_indicators,
            scalar_confidence,
            data_quality_status,
        )

    def _build_impact_estimate(
        self,
        direction: str,
        dir_prob: float,
        market_moving: bool,
        strength: str,
    ) -> str:
        """Construct descriptive expected impact string."""
        if not market_moving or direction == "NEUTRAL":
            return f"Expected neutral market impact ({strength} magnitude tier, {dir_prob*100:.1f}% confidence)."

        strength_ranges = {
            "LOW": "0.0% to 1.0%",
            "MEDIUM": "1.0% to 3.0%",
            "HIGH": "3.0% to 6.0%",
            "VERY_HIGH": "> 6.0%",
        }
        car_range = strength_ranges.get(strength, "1.0% to 3.0%")
        sign = "+" if direction == "POSITIVE" else "-"
        return (
            f"Expected {direction.lower()} abnormal return in range [{sign}{car_range}] "
            f"with {strength} impact strength ({dir_prob*100:.1f}% direction probability)."
        )

    def _build_decision_narrative(
        self,
        direction: str,
        dir_prob: float,
        market_moving: bool,
        strength: str,
        confidence: str,
        anticipation_class: str,
        anticipation_score: float,
        anticipation_flag: bool,
    ) -> str:
        """
        Synthesize human-interpretable contextual decision reason.
        """
        narrative_parts: list[str] = []

        # Part A: Core Prediction Summary
        if not market_moving or direction == "NEUTRAL":
            narrative_parts.append(
                f"Model predicts neutral market impact with {confidence.lower()} confidence ({dir_prob*100:.1f}% directional probability)."
            )
        else:
            narrative_parts.append(
                f"Prediction is {direction.lower()} with {confidence.lower()} model confidence and {strength.lower()} impact strength ({dir_prob*100:.1f}% probability)."
            )

        # Part B: Anticipation Context Blending
        if anticipation_class in {
            AnticipationClassification.STRONG_EVIDENCE.value,
            "STRONG_EVIDENCE",
        } or anticipation_score >= 0.75:
            narrative_parts.append(
                f"However, substantial pre-event market activity (Anticipation Score: {anticipation_score:.2f}, {anticipation_class}) suggests that part or all of the expected reaction may already be priced in by the market."
            )
        elif anticipation_class in {
            AnticipationClassification.MODERATE_EVIDENCE.value,
            "MODERATE_EVIDENCE",
        } or anticipation_score >= 0.50:
            narrative_parts.append(
                f"Moderate pre-event volume or return movement (Anticipation Score: {anticipation_score:.2f}) indicates potential partial price-in; exercise caution."
            )
        elif anticipation_class in {
            AnticipationClassification.WEAK_EVIDENCE.value,
            "WEAK_EVIDENCE",
            AnticipationClassification.NO_EVIDENCE.value,
            "NO_EVIDENCE",
        }:
            narrative_parts.append(
                "Little to no pre-event market anticipation detected, indicating that the legislative event is likely novel to the market."
            )

        # Part C: Compliance Disclaimer
        narrative_parts.append(f"[{DISCLAIMER_TEXT}]")

        return " ".join(narrative_parts)
