"""
labeling/label_generator.py
============================
Ground-truth label generator — Task 4.4.

Responsibility
--------------
Convert a ``StatisticalResult`` (from the Statistical Significance Engine,
Task 4.3) into a set of supervised machine-learning labels encapsulated
in a ``LabelRecord``.

Four label types are computed per (bill, company, event-window) triple:

1.  **DirectionLabel**    — POSITIVE / NEGATIVE / NEUTRAL
2.  **market_moving**     — binary True / False
3.  **ImpactStrength**    — LOW / MEDIUM / HIGH / VERY_HIGH
4.  **ConfidenceLabel**   — HIGH / MEDIUM / LOW

All thresholds are read from ``config.settings`` and can be overridden
via environment variables or by injecting a custom ``LabelConfig``.

Validation
----------
A label is rejected (→ ``LabelValidationReport``) if:
*  The source ``StatisticalResult`` is ``None``.
*  The CAR value is missing or is not a finite number.
*  The p-value is not a finite number.

Incremental execution
---------------------
``LabelGenerator.generate`` accepts an optional ``skip_if_exists``
callable so that the orchestrating service can skip records that are
already persisted in the ``LabelRepository``.

References
----------
MacKinlay, A.C. (1997). Event Studies in Economics and Finance.
Journal of Economic Literature, 35(1), 13–39.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

from config.logging_config import get_logger
from schemas.label_record import ConfidenceLabel, DirectionLabel, ImpactStrength, LabelRecord
from schemas.statistical_result import StatisticalResult
from schemas.validation_report import LabelValidationReport

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Configuration dataclass (mirrors settings with override capability)
# ---------------------------------------------------------------------------


@dataclass
class LabelConfig:
    """
    Configurable thresholds for all label-generation rules.

    Defaults are sourced from ``config.settings`` at instantiation time.
    Pass a custom ``LabelConfig`` to override individual thresholds for
    testing or experimentation without changing environment variables.
    """

    positive_car_threshold: float
    negative_car_threshold: float
    market_moving_car_threshold: float
    strength_low_max: float
    strength_medium_max: float
    strength_high_max: float
    confidence_high_pvalue: float
    confidence_medium_pvalue: float

    @classmethod
    def from_settings(cls) -> "LabelConfig":
        """Construct a ``LabelConfig`` from the global settings singleton."""
        from config.settings import settings

        return cls(
            positive_car_threshold=settings.LABEL_POSITIVE_CAR_THRESHOLD,
            negative_car_threshold=settings.LABEL_NEGATIVE_CAR_THRESHOLD,
            market_moving_car_threshold=settings.LABEL_MARKET_MOVING_CAR_THRESHOLD,
            strength_low_max=settings.LABEL_STRENGTH_LOW_MAX,
            strength_medium_max=settings.LABEL_STRENGTH_MEDIUM_MAX,
            strength_high_max=settings.LABEL_STRENGTH_HIGH_MAX,
            confidence_high_pvalue=settings.LABEL_CONFIDENCE_HIGH_PVALUE,
            confidence_medium_pvalue=settings.LABEL_CONFIDENCE_MEDIUM_PVALUE,
        )


# ---------------------------------------------------------------------------
# LabelGenerator
# ---------------------------------------------------------------------------


class LabelGenerator:
    """
    Converts a ``StatisticalResult`` into a ``LabelRecord`` containing
    all four supervised-learning labels.

    Parameters
    ----------
    config : LabelConfig, optional
        Threshold configuration.  If ``None``, defaults are read from
        ``config.settings``.

    Usage
    -----
    ::

        from labeling.label_generator import LabelGenerator
        from storage.statistical_repository import StatisticalRepository

        stat_repo = StatisticalRepository()
        generator = LabelGenerator()

        for stat_result in stat_repo.get_all():
            result = generator.generate(stat_result)
            if isinstance(result, LabelRecord):
                label_repo.save(result)
            else:
                # LabelValidationReport — log or store separately
                logger.warning("Rejected: %s", result)
    """

    def __init__(self, config: Optional[LabelConfig] = None) -> None:
        self._config: LabelConfig = config or LabelConfig.from_settings()
        logger.debug(
            "LabelGenerator initialised | pos_threshold=%.4f | neg_threshold=%.4f",
            self._config.positive_car_threshold,
            self._config.negative_car_threshold,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        stat_result: Optional[StatisticalResult],
        skip_if_exists: Optional[Callable[[str, str, str], bool]] = None,
    ) -> LabelRecord | LabelValidationReport:
        """
        Generate a ``LabelRecord`` from a ``StatisticalResult``.

        Parameters
        ----------
        stat_result : StatisticalResult or None
            Source statistical significance record.  If ``None``, a
            ``LabelValidationReport`` is returned immediately.
        skip_if_exists : callable, optional
            A callable ``(bill_id, company_isin, event_window) -> bool``
            that returns ``True`` if the label already exists.  When
            ``True`` is returned, this method returns the existing-label
            sentinel ``None`` is **not** used — instead the caller should
            handle the skip in the service layer.  If not provided, no
            skipping occurs.

        Returns
        -------
        LabelRecord | LabelValidationReport
            A ``LabelRecord`` on success, or a ``LabelValidationReport``
            when the input fails validation.
        """
        # --- 1. Validate presence -------------------------------------------
        if stat_result is None:
            return self._reject(
                bill_id="<unknown>",
                company="<unknown>",
                event_window="<unknown>",
                reason="StatisticalResult is None — cannot generate label.",
            )

        bill_id = stat_result.bill_id
        company = stat_result.company
        event_window = stat_result.event_window

        # --- 2. Validate CAR -------------------------------------------------
        car = stat_result.car
        if car is None or not math.isfinite(car):
            return self._reject(
                bill_id=bill_id,
                company=company,
                event_window=event_window,
                reason=f"CAR is not a finite number (car={car!r}). "
                "Label generation aborted.",
            )

        # --- 3. Validate p-value ---------------------------------------------
        p_value = stat_result.p_value
        if p_value is None or not math.isfinite(p_value):
            return self._reject(
                bill_id=bill_id,
                company=company,
                event_window=event_window,
                reason=f"p-value is not a finite number (p_value={p_value!r}). "
                "Label generation aborted.",
            )

        # --- 4. Compute all four labels --------------------------------------
        direction = self._compute_direction(car, stat_result.significant)
        market_moving = self._compute_market_moving(car, stat_result.significant)
        impact_strength = self._compute_impact_strength(car)
        confidence = self._compute_confidence(p_value, stat_result.effect_size)

        # --- 5. Build decision reason ----------------------------------------
        reason = self._build_reason(
            car=car,
            p_value=p_value,
            significant=stat_result.significant,
            effect_size=stat_result.effect_size,
            direction=direction,
            market_moving=market_moving,
            impact_strength=impact_strength,
            confidence=confidence,
        )

        # --- 6. Assemble record ----------------------------------------------
        record = LabelRecord(
            bill_id=bill_id,
            company=company,
            company_symbol=stat_result.company_symbol,
            event_window=event_window,
            car=car,
            p_value=p_value,
            direction=direction,
            market_moving=market_moving,
            impact_strength=impact_strength,
            confidence=confidence,
            decision_reason=reason,
            calculation_timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger.debug(
            "Generated label: bill=%s company=%s window=%s direction=%s confidence=%s",
            bill_id,
            company,
            event_window,
            direction.value,
            confidence.value,
        )
        return record

    def generate_many(
        self,
        stat_results: list[StatisticalResult],
        skip_if_exists: Optional[Callable[[str, str, str], bool]] = None,
    ) -> tuple[list[LabelRecord], list[LabelValidationReport]]:
        """
        Generate labels for a batch of statistical results.

        Parameters
        ----------
        stat_results : list[StatisticalResult]
            Source statistical results.
        skip_if_exists : callable, optional
            Incremental-execution guard.  See ``generate()`` for details.

        Returns
        -------
        tuple[list[LabelRecord], list[LabelValidationReport]]
            A tuple of (valid_labels, rejected_reports).
        """
        valid: list[LabelRecord] = []
        rejected: list[LabelValidationReport] = []

        for stat_result in stat_results:
            # Incremental skip check
            if skip_if_exists is not None and stat_result is not None:
                if skip_if_exists(
                    stat_result.bill_id, stat_result.company, stat_result.event_window
                ):
                    logger.debug(
                        "Skipping existing label: bill=%s company=%s window=%s",
                        stat_result.bill_id,
                        stat_result.company,
                        stat_result.event_window,
                    )
                    continue

            outcome = self.generate(stat_result)
            if isinstance(outcome, LabelRecord):
                valid.append(outcome)
            else:
                rejected.append(outcome)

        logger.info(
            "Batch label generation complete: %d valid, %d rejected",
            len(valid),
            len(rejected),
        )
        return valid, rejected

    # ------------------------------------------------------------------
    # Private label computation methods
    # ------------------------------------------------------------------

    def _compute_direction(self, car: float, significant: bool) -> DirectionLabel:
        """
        Compute the direction label.

        Rules
        -----
        POSITIVE  :  CAR > +pos_threshold  AND  significant == True
        NEGATIVE  :  CAR < −neg_threshold  AND  significant == True
        NEUTRAL   :  all other cases
        """
        cfg = self._config
        if significant and car > cfg.positive_car_threshold:
            return DirectionLabel.POSITIVE
        if significant and car < -cfg.negative_car_threshold:
            return DirectionLabel.NEGATIVE
        return DirectionLabel.NEUTRAL

    def _compute_market_moving(self, car: float, significant: bool) -> bool:
        """
        Compute the market-moving label.

        Rule
        ----
        True  :  significant == True  AND  |CAR| > market_moving_threshold
        False :  otherwise
        """
        return significant and abs(car) > self._config.market_moving_car_threshold

    def _compute_impact_strength(self, car: float) -> ImpactStrength:
        """
        Compute impact strength from the absolute value of CAR.

        Ranges (default thresholds)
        ---------------------------
        LOW       : |CAR| < 1%
        MEDIUM    : 1% ≤ |CAR| < 3%
        HIGH      : 3% ≤ |CAR| < 6%
        VERY_HIGH : |CAR| ≥ 6%
        """
        abs_car = abs(car)
        cfg = self._config
        if abs_car < cfg.strength_low_max:
            return ImpactStrength.LOW
        if abs_car < cfg.strength_medium_max:
            return ImpactStrength.MEDIUM
        if abs_car < cfg.strength_high_max:
            return ImpactStrength.HIGH
        return ImpactStrength.VERY_HIGH

    def _compute_confidence(self, p_value: float, effect_size: str) -> ConfidenceLabel:
        """
        Compute the composite confidence label.

        Rules
        -----
        HIGH   :  p_value ≤ high_pvalue_threshold  AND  effect_size == "Large"
        MEDIUM :  p_value ≤ medium_pvalue_threshold  OR  effect_size in {"Medium","Large"}
        LOW    :  all other cases
        """
        cfg = self._config
        es_upper = effect_size.strip().title()  # normalise casing

        if p_value <= cfg.confidence_high_pvalue and es_upper == "Large":
            return ConfidenceLabel.HIGH

        if p_value <= cfg.confidence_medium_pvalue or es_upper in {"Medium", "Large"}:
            return ConfidenceLabel.MEDIUM

        return ConfidenceLabel.LOW

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _reject(
        bill_id: str,
        company: str,
        event_window: str,
        reason: str,
    ) -> LabelValidationReport:
        """Construct a rejection report with the current UTC timestamp."""
        ts = datetime.now(timezone.utc).isoformat()
        logger.warning(
            "Label rejected: bill=%s company=%s window=%s | %s",
            bill_id,
            company,
            event_window,
            reason,
        )
        return LabelValidationReport(
            bill_id=bill_id,
            company=company,
            event_window=event_window,
            rejection_reason=reason,
            timestamp=ts,
        )

    @staticmethod
    def _build_reason(
        car: float,
        p_value: float,
        significant: bool,
        effect_size: str,
        direction: DirectionLabel,
        market_moving: bool,
        impact_strength: ImpactStrength,
        confidence: ConfidenceLabel,
    ) -> str:
        """Compose a human-readable decision reason string."""
        sig_str = "significant" if significant else "not significant"
        mm_str = "market-moving" if market_moving else "not market-moving"
        return (
            f"direction={direction.value} ({sig_str}, CAR={car:+.4f}, p={p_value:.4f}); "
            f"market_moving={market_moving} ({mm_str}); "
            f"impact_strength={impact_strength.value} (|CAR|={abs(car):.4f}); "
            f"confidence={confidence.value} (p={p_value:.4f}, effect_size={effect_size})"
        )
