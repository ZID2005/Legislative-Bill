"""
schemas/label_record.py
=======================
Typed data model for a ground-truth label record produced by the
Label Generation Engine (Task 4.4).

Each ``LabelRecord`` encapsulates all four supervised-learning labels
derived from a single ``StatisticalResult`` (bill × company × event-window):

1. **DirectionLabel** — POSITIVE / NEGATIVE / NEUTRAL
2. **market_moving** — binary True/False
3. **ImpactStrength** — LOW / MEDIUM / HIGH / VERY_HIGH
4. **ConfidenceLabel** — HIGH / MEDIUM / LOW

These records form the authoritative ground-truth dataset that will be
consumed by future Feature Engineering (Task 7) and Model Training
(Task 8) pipelines.

References
----------
MacKinlay, A.C. (1997). Event Studies in Economics and Finance.
Journal of Economic Literature, 35(1), 13–39.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Label Enumerations
# ---------------------------------------------------------------------------


class DirectionLabel(str, Enum):
    """
    Directional market-impact label derived from CAR and statistical
    significance.

    Thresholds are configurable via ``settings.LABEL_POSITIVE_CAR_THRESHOLD``
    and ``settings.LABEL_NEGATIVE_CAR_THRESHOLD``.

    Rules
    -----
    POSITIVE  : CAR > +threshold  AND statistically significant
    NEGATIVE  : CAR < −threshold  AND statistically significant
    NEUTRAL   : All other cases (insignificant, or |CAR| below threshold)
    """

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class ImpactStrength(str, Enum):
    """
    Ordinal impact-magnitude label derived from the absolute value of CAR.

    Thresholds are configurable via settings:
    - LABEL_STRENGTH_LOW_MAX    (default 1%)
    - LABEL_STRENGTH_MEDIUM_MAX (default 3%)
    - LABEL_STRENGTH_HIGH_MAX   (default 6%)

    Ranges
    ------
    LOW       : |CAR| < LOW_MAX
    MEDIUM    : LOW_MAX  ≤ |CAR| < MEDIUM_MAX
    HIGH      : MEDIUM_MAX ≤ |CAR| < HIGH_MAX
    VERY_HIGH : |CAR| ≥ HIGH_MAX
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class ConfidenceLabel(str, Enum):
    """
    Composite confidence label combining p-value precision and effect size.

    Derivation
    ----------
    HIGH   : p_value ≤ 0.01  AND  effect_size == "Large"
    MEDIUM : p_value ≤ 0.05  OR   effect_size in {"Medium", "Large"}
    LOW    : All other cases
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ---------------------------------------------------------------------------
# LabelRecord Dataclass
# ---------------------------------------------------------------------------


@dataclass
class LabelRecord:
    """
    Ground-truth label record for a (bill, company, event-window) triple.

    This is the canonical output of the Label Generation Engine and the
    primary input to the Feature Engineering and ML Training pipelines.

    Attributes
    ----------
    bill_id : str
        Unique slug identifying the legislative bill.
    company : str
        Company ISIN (primary key consistent with StatisticalResult).
    company_symbol : str
        Exchange ticker symbol (e.g. "RELIANCE", "INFY").
    event_window : str
        Event window specification (e.g. "[-5,+5]").
    car : float
        Cumulative Abnormal Return over the event window.
    p_value : float
        Two-tailed p-value from the statistical significance test.
    direction : DirectionLabel
        POSITIVE / NEGATIVE / NEUTRAL directional label.
    market_moving : bool
        True if the event is statistically significant AND |CAR| exceeds
        the market-moving threshold.
    impact_strength : ImpactStrength
        LOW / MEDIUM / HIGH / VERY_HIGH magnitude label.
    confidence : ConfidenceLabel
        HIGH / MEDIUM / LOW composite confidence label.
    decision_reason : str
        Human-readable explanation of how all labels were derived.
    calculation_timestamp : str
        ISO-8601 UTC timestamp of label generation.
    """

    bill_id: str
    company: str            # ISIN
    company_symbol: str     # Ticker
    event_window: str       # e.g. "[-5,+5]"
    car: float
    p_value: float
    direction: DirectionLabel
    market_moving: bool
    impact_strength: ImpactStrength
    confidence: ConfidenceLabel
    decision_reason: str
    calculation_timestamp: str

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise the record to a JSON-compatible dictionary."""
        return {
            "bill_id": self.bill_id,
            "company": self.company,
            "company_symbol": self.company_symbol,
            "event_window": self.event_window,
            "car": self.car,
            "p_value": self.p_value,
            "direction": self.direction.value,
            "market_moving": self.market_moving,
            "impact_strength": self.impact_strength.value,
            "confidence": self.confidence.value,
            "decision_reason": self.decision_reason,
            "calculation_timestamp": self.calculation_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LabelRecord":
        """Deserialise the record from a dictionary."""
        return cls(
            bill_id=data["bill_id"],
            company=data["company"],
            company_symbol=data["company_symbol"],
            event_window=data["event_window"],
            car=float(data["car"]),
            p_value=float(data["p_value"]),
            direction=DirectionLabel(data["direction"]),
            market_moving=bool(data["market_moving"]),
            impact_strength=ImpactStrength(data["impact_strength"]),
            confidence=ConfidenceLabel(data["confidence"]),
            decision_reason=data["decision_reason"],
            calculation_timestamp=data["calculation_timestamp"],
        )

    def __repr__(self) -> str:
        return (
            f"<LabelRecord bill={self.bill_id!r} "
            f"company={self.company!r} "
            f"window={self.event_window!r} "
            f"car={self.car:.4f} "
            f"direction={self.direction.value} "
            f"confidence={self.confidence.value}>"
        )
