"""
anticipation/signal_detector.py
===============================
Deterministic signal detection engine for Task 6.5 — Anticipation Bias Engine.

Flags potential pre-event anticipation patterns when one or more configurable rules trigger:
1. STATISTICAL_SIGNIFICANCE: Pre-event CAR is statistically unusual (|z| >= threshold or p < 0.05).
2. HIGH_MAGNITUDE: Unusually high abnormal return magnitude (|CAR| >= threshold).
3. SUSTAINED_DIRECTION: Sustained directional drift (>= 70% positive or negative AR days).
4. IMMEDIATE_PRE_EVENT_ACCELERATION: Abnormal returns concentrated immediately before T0 ([-5,-3] or [-2,-1]).
5. MULTI_WINDOW_PERSISTENCE: 3 or more consecutive sub-windows show persistent AR in the same direction.
"""

from __future__ import annotations

from typing import Any, Optional
from config.logging_config import get_logger
from config.settings import settings
from schemas.anticipation import PreEventWindowStats

logger = get_logger(__name__)


class PreEventSignalDetector:
    """
    Deterministic detector for pre-event legislative market anticipation signals.
    """

    def __init__(
        self,
        z_threshold: Optional[float] = None,
        car_magnitude_threshold: Optional[float] = None,
        sustained_direction_ratio: Optional[float] = None,
        immediate_car_threshold: Optional[float] = None,
    ) -> None:
        self.z_threshold = (
            z_threshold if z_threshold is not None else settings.ANTICIPATION_Z_THRESHOLD
        )
        self.car_magnitude_threshold = (
            car_magnitude_threshold
            if car_magnitude_threshold is not None
            else settings.ANTICIPATION_CAR_MAGNITUDE_THRESHOLD
        )
        self.sustained_direction_ratio = (
            sustained_direction_ratio
            if sustained_direction_ratio is not None
            else settings.ANTICIPATION_SUSTAINED_DIRECTION_RATIO
        )
        self.immediate_car_threshold = (
            immediate_car_threshold
            if immediate_car_threshold is not None
            else settings.ANTICIPATION_IMMEDIATE_CAR_THRESHOLD
        )

    def detect_signals(
        self, window_stats: dict[str, PreEventWindowStats]
    ) -> tuple[list[str], dict[str, Any]]:
        """
        Evaluate deterministic pre-event signals across calculated window statistics.

        Parameters
        ----------
        window_stats : dict[str, PreEventWindowStats]
            Mapping of window label -> PreEventWindowStats.

        Returns
        -------
        tuple[list[str], dict[str, Any]]
            (detected_signal_names, detailed_diagnostics_dict)
        """
        signals: list[str] = []
        details: dict[str, Any] = {}

        cum_stats = window_stats.get("[-30,-1]")

        # 1. Statistical Significance Check
        sig_windows = []
        for win_name, st in window_stats.items():
            if st.observation_count >= 2 and (abs(st.ar_z_score) >= self.z_threshold or st.p_value < 0.05):
                sig_windows.append(f"{win_name} (z={st.ar_z_score:.2f}, p={st.p_value:.4f})")

        if sig_windows:
            sig_name = "STATISTICAL_SIGNIFICANCE_PRE_EVENT"
            signals.append(sig_name)
            details[sig_name] = {"significant_windows": sig_windows}

        # 2. High Magnitude Check
        high_mag_windows = []
        for win_name, st in window_stats.items():
            thresh = (
                self.immediate_car_threshold
                if win_name in {"[-5,-3]", "[-2,-1]"}
                else self.car_magnitude_threshold
            )
            if st.observation_count >= 2 and abs(st.cumulative_abnormal_return) >= thresh:
                high_mag_windows.append(
                    f"{win_name} (CAR={st.cumulative_abnormal_return * 100.0:+.2f}%)"
                )

        if high_mag_windows:
            mag_name = "HIGH_MAGNITUDE_PRE_EVENT_RETURN"
            signals.append(mag_name)
            details[mag_name] = {"high_magnitude_windows": high_mag_windows}

        # 3. Sustained Directional Movement Check
        if cum_stats and cum_stats.observation_count >= 5:
            max_ratio = max(cum_stats.pct_positive_ar, cum_stats.pct_negative_ar)
            if max_ratio >= self.sustained_direction_ratio:
                direction = "POSITIVE" if cum_stats.pct_positive_ar >= cum_stats.pct_negative_ar else "NEGATIVE"
                sus_name = f"SUSTAINED_{direction}_DRIFT"
                signals.append(sus_name)
                details[sus_name] = {
                    "direction": direction,
                    "ratio": max_ratio,
                    "pct_positive": cum_stats.pct_positive_ar,
                    "pct_negative": cum_stats.pct_negative_ar,
                    "observations": cum_stats.observation_count,
                }

        # 4. Immediate Pre-Event Concentration Check
        imm_triggers = []
        for imm_win in ["[-5,-3]", "[-2,-1]"]:
            st = window_stats.get(imm_win)
            if st and st.observation_count >= 1:
                if (
                    abs(st.cumulative_abnormal_return) >= self.immediate_car_threshold
                    or abs(st.ar_z_score) >= self.z_threshold
                ):
                    imm_triggers.append(
                        f"{imm_win} (CAR={st.cumulative_abnormal_return * 100.0:+.2f}%, z={st.ar_z_score:.2f})"
                    )

        if imm_triggers:
            imm_name = "IMMEDIATE_PRE_T0_ACCELERATION"
            signals.append(imm_name)
            details[imm_name] = {"immediate_windows": imm_triggers}

        # 5. Multi-Window Persistence Check
        sub_windows = ["[-30,-21]", "[-20,-11]", "[-10,-6]", "[-5,-3]", "[-2,-1]"]
        mars = [
            window_stats[w].mean_abnormal_return
            for w in sub_windows
            if w in window_stats and window_stats[w].observation_count >= 1
        ]
        if len(mars) >= 3:
            # Check for 3 consecutive windows of same sign
            consecutive_pos = 0
            consecutive_neg = 0
            max_consecutive_pos = 0
            max_consecutive_neg = 0

            for m in mars:
                if m > 0.001:  # slightly positive
                    consecutive_pos += 1
                    consecutive_neg = 0
                elif m < -0.001:  # slightly negative
                    consecutive_neg += 1
                    consecutive_pos = 0
                else:
                    consecutive_pos = 0
                    consecutive_neg = 0
                max_consecutive_pos = max(max_consecutive_pos, consecutive_pos)
                max_consecutive_neg = max(max_consecutive_neg, consecutive_neg)

            if max_consecutive_pos >= 3 or max_consecutive_neg >= 3:
                pers_direction = "POSITIVE" if max_consecutive_pos >= 3 else "NEGATIVE"
                pers_name = f"MULTI_WINDOW_PERSISTENT_{pers_direction}_DRIFT"
                signals.append(pers_name)
                details[pers_name] = {
                    "direction": pers_direction,
                    "consecutive_count": max(max_consecutive_pos, max_consecutive_neg),
                }

        return signals, details
