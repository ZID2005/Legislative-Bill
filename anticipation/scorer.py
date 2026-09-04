"""
anticipation/scorer.py
======================
Anticipation scoring and classification engine for Task 6.5 — Anticipation Bias Engine.

Produces:
- market_signal_score: Normalized score [0.0, 1.0] from pre-event market statistics.
- information_signal_score: Normalized score [0.0, 1.0] from external evidence.
- anticipation_score: Composite deterministic score [0.0, 1.0].
- anticipation_flag: Boolean flag indicating notable anticipation patterns.
- classification: NO_EVIDENCE | WEAK_EVIDENCE | MODERATE_EVIDENCE | STRONG_EVIDENCE.
- confidence: LOW | MEDIUM | HIGH.
- decision_reason: Transparent academic explanation string.
"""

from __future__ import annotations

import datetime
import math
from typing import Optional
from config.logging_config import get_logger
from config.settings import settings
from schemas.anticipation import (
    AnticipationClassification,
    AnticipationScore,
    InformationEvidence,
    PreEventWindowStats,
)
from schemas.market_model import MarketModelRecord

logger = get_logger(__name__)


class AnticipationScorer:
    """
    Computes normalized anticipation scores and evidence classifications.
    """

    def __init__(
        self,
        flag_threshold: Optional[float] = None,
        strong_threshold: Optional[float] = None,
        moderate_threshold: Optional[float] = None,
        weak_threshold: Optional[float] = None,
    ) -> None:
        self.flag_threshold = (
            flag_threshold if flag_threshold is not None else settings.ANTICIPATION_FLAG_THRESHOLD
        )
        self.strong_threshold = (
            strong_threshold if strong_threshold is not None else settings.ANTICIPATION_STRONG_THRESHOLD
        )
        self.moderate_threshold = (
            moderate_threshold if moderate_threshold is not None else settings.ANTICIPATION_MODERATE_THRESHOLD
        )
        self.weak_threshold = (
            weak_threshold if weak_threshold is not None else settings.ANTICIPATION_WEAK_THRESHOLD
        )

    def calculate_market_signal_score(
        self,
        window_stats: dict[str, PreEventWindowStats],
        detected_signals: list[str],
    ) -> float:
        """
        Compute normalized market signal score in [0.0, 1.0].

        Components:
        1. Cumulative CAR Magnitude [-30,-1] (Weight: 0.35)
        2. Statistical Significance z-score (Weight: 0.25)
        3. Immediate Window Acceleration ([-5,-3] and [-2,-1]) (Weight: 0.25)
        4. Triggered Signal Diversity (Weight: 0.15)
        """
        cum_stats = window_stats.get("[-30,-1]")
        if not cum_stats or cum_stats.observation_count < 2:
            # Fallback if cumulative window is missing or insufficient
            return 0.0

        # Component 1: Cumulative CAR magnitude (target 5% for full points)
        car_mag = abs(cum_stats.cumulative_abnormal_return)
        comp_car = min(1.0, car_mag / 0.05) * 0.35

        # Component 2: Statistical Significance (target |z| = 3.0 for full points)
        z_mag = abs(cum_stats.ar_z_score)
        comp_z = min(1.0, z_mag / 3.0) * 0.25

        # Component 3: Immediate Proximity Acceleration
        imm_2_1 = window_stats.get("[-2,-1]")
        imm_5_3 = window_stats.get("[-5,-3]")
        imm_car_sum = 0.0
        if imm_2_1 and imm_2_1.observation_count >= 1:
            imm_car_sum += abs(imm_2_1.cumulative_abnormal_return)
        if imm_5_3 and imm_5_3.observation_count >= 1:
            imm_car_sum += abs(imm_5_3.cumulative_abnormal_return)

        # Target 3% immediate abnormal movement for full points
        comp_imm = min(1.0, imm_car_sum / 0.03) * 0.25

        # Component 4: Signal count
        comp_sig = min(1.0, len(detected_signals) / 4.0) * 0.15

        raw_score = comp_car + comp_z + comp_imm + comp_sig
        return float(max(0.0, min(1.0, round(raw_score, 4))))

    def calculate_information_signal_score(
        self,
        evidence_items: list[InformationEvidence],
        official_introduction_date: str,
    ) -> tuple[float, bool]:
        """
        Compute normalized information signal score in [0.0, 1.0] from pre-event evidence.

        Returns
        -------
        tuple[float, bool]
            (info_signal_score, media_data_available)
        """
        if not evidence_items:
            return 0.0, False

        intro_dt = datetime.datetime.strptime(official_introduction_date[:10], "%Y-%m-%d")

        confidence_weights = {
            "HIGH": 1.0,
            "MEDIUM": 0.7,
            "LOW": 0.4,
        }

        weighted_sum = 0.0
        weight_total = 0.0

        for ev in evidence_items:
            try:
                ev_dt = datetime.datetime.strptime(ev.publication_date[:10], "%Y-%m-%d")
                days_before = max(0, (intro_dt - ev_dt).days)
            except Exception:
                days_before = 15

            # Exponential decay: evidence closer to T0 has higher impact
            # Half-life of ~14 days (lambda = 0.05)
            time_decay = math.exp(-0.05 * days_before)
            conf_weight = confidence_weights.get(ev.confidence.upper(), 0.7)
            item_weight = conf_weight * time_decay

            item_score = ev.relevance_score * item_weight
            weighted_sum += item_score
            weight_total += item_weight

        if weight_total > 0:
            avg_score = weighted_sum / weight_total
            # Boost score if multiple corroborating evidence items exist
            corroboration_factor = min(1.3, 1.0 + 0.05 * (len(evidence_items) - 1))
            final_info_score = min(1.0, avg_score * corroboration_factor)
            return float(max(0.0, round(final_info_score, 4))), True

        return 0.0, True

    def calculate_composite_score(
        self,
        market_signal_score: float,
        information_signal_score: float,
        media_data_available: bool,
    ) -> float:
        """
        Combine market and information signals into composite anticipation score in [0.0, 1.0].
        """
        if not media_data_available:
            # Market-driven diagnostic score
            return float(market_signal_score)

        # Blended score: 60% market, 40% information
        composite = 0.60 * market_signal_score + 0.40 * information_signal_score
        return float(max(0.0, min(1.0, round(composite, 4))))

    def classify(self, score: float) -> AnticipationClassification:
        """
        Classify anticipation score into evidence strength tier.
        """
        if score >= self.strong_threshold:
            return AnticipationClassification.STRONG_EVIDENCE
        if score >= self.moderate_threshold:
            return AnticipationClassification.MODERATE_EVIDENCE
        if score >= self.weak_threshold:
            return AnticipationClassification.WEAK_EVIDENCE
        return AnticipationClassification.NO_EVIDENCE

    def determine_confidence(
        self,
        market_model: MarketModelRecord,
        observation_count: int,
        media_data_available: bool,
    ) -> str:
        """
        Determine confidence level (LOW, MEDIUM, HIGH) for the evaluation.
        """
        if observation_count >= 20 and market_model.r_squared >= 0.10:
            return "HIGH"
        if observation_count >= 10:
            return "MEDIUM"
        return "LOW"

    def generate_decision_reason(
        self,
        classification: AnticipationClassification,
        anticipation_score: float,
        market_score: float,
        info_score: float,
        media_data_available: bool,
        cum_stats: Optional[PreEventWindowStats],
        detected_signals: list[str],
    ) -> str:
        """
        Generate academic and transparent diagnostic reason string.
        """
        car_str = (
            f"CAR[-30,-1]={cum_stats.cumulative_abnormal_return * 100.0:+.2f}% (z={cum_stats.ar_z_score:.2f}, p={cum_stats.p_value:.4f})"
            if cum_stats and cum_stats.observation_count > 0
            else "N/A"
        )

        sig_summary = ", ".join(detected_signals) if detected_signals else "None"

        if classification == AnticipationClassification.STRONG_EVIDENCE:
            lead = "Evidence strongly consistent with pre-event market anticipation"
        elif classification == AnticipationClassification.MODERATE_EVIDENCE:
            lead = "Evidence moderately consistent with pre-event market anticipation"
        elif classification == AnticipationClassification.WEAK_EVIDENCE:
            lead = "Weak or inconclusive pre-event market signals"
        else:
            lead = "No measurable evidence of pre-event anticipation"

        media_note = "External media data incorporated" if media_data_available else "External media data unavailable (market-only evaluation)"

        reason = (
            f"{lead} (Score: {anticipation_score:.4f} | Market: {market_score:.4f} | Info: {info_score:.4f}). "
            f"Pre-event metrics: {car_str}. "
            f"Triggered signals: [{sig_summary}]. "
            f"{media_note}. "
            f"Note: This reflects quantitative diagnostic patterns, not proof of non-public information leakage."
        )
        return reason
