"""
schemas/statistical_result.py
==============================
Data schema for a Statistical Significance calculation record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class StatisticalResult:
    """
    Statistical significance analysis result for a company-bill-window event study.
    """

    bill_id: str
    company: str  # Stores company_isin
    company_symbol: str  # Ticker
    event_window: str  # e.g., "[-5,+5]"
    car: float  # Cumulative Abnormal Return
    variance: float  # CAR Variance
    standard_error: float  # CAR Standard Error
    t_statistic: float  # Student's t-stat
    p_value: float  # Two-tailed p-value
    confidence_interval: list[float]  # [lower, upper] at 95%
    significant: bool  # Significance flag (True/False)
    confidence_level: str  # "1%", "5%", "10%", or "Not Significant"
    effect_size: str  # "Small", "Medium", "Large"
    decision_reason: str  # Explanation, e.g. "Significant because p=0.012 and |t|=2.43"
    calculation_timestamp: str  # ISO-8601 UTC timestamp

    def to_dict(self) -> dict[str, Any]:
        """Serialise the record to a dictionary."""
        return {
            "bill_id": self.bill_id,
            "company": self.company,
            "company_symbol": self.company_symbol,
            "event_window": self.event_window,
            "car": self.car,
            "variance": self.variance,
            "standard_error": self.standard_error,
            "t_statistic": self.t_statistic,
            "p_value": self.p_value,
            "confidence_interval": self.confidence_interval,
            "significant": self.significant,
            "confidence_level": self.confidence_level,
            "effect_size": self.effect_size,
            "decision_reason": self.decision_reason,
            "calculation_timestamp": self.calculation_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StatisticalResult:
        """Deserialise the record from a dictionary."""
        return cls(
            bill_id=data["bill_id"],
            company=data["company"],
            company_symbol=data["company_symbol"],
            event_window=data["event_window"],
            car=float(data["car"]),
            variance=float(data["variance"]),
            standard_error=float(data["standard_error"]),
            t_statistic=float(data["t_statistic"]),
            p_value=float(data["p_value"]),
            confidence_interval=[float(x) for x in data["confidence_interval"]],
            significant=bool(data["significant"]),
            confidence_level=data["confidence_level"],
            effect_size=data["effect_size"],
            decision_reason=data["decision_reason"],
            calculation_timestamp=data["calculation_timestamp"],
        )

    def __repr__(self) -> str:
        return (
            f"<StatisticalResult bill={self.bill_id!r} "
            f"company={self.company!r} "
            f"window={self.event_window!r} "
            f"car={self.car:.4f} "
            f"significant={self.significant}>"
        )
