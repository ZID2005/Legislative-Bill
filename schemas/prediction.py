"""
schemas/prediction.py
=====================
Typed data models for model prediction outputs.

The ``Prediction`` schema is the canonical output of the prediction pipeline
(Task 9).  It is returned by the Predictor, consumed by the API layer, and
stored for audit and feedback collection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ImpactLabel(str, Enum):
    """
    Directional market impact label for a (bill, company) pair.

    Thresholds (to be calibrated in Task 8):
    *  Positive : CAR[0, +20] > +2%
    *  Negative : CAR[0, +20] < -2%
    *  Neutral  : -2% ≤ CAR[0, +20] ≤ +2%
    """

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class SectorImpact:
    """Impact assessment for a single sector."""

    sector: str
    impact_label: ImpactLabel
    confidence: float  # 0.0 – 1.0
    rationale: str = ""  # Human-readable explanation (SHAP-driven)
    top_features: list[str] = field(default_factory=list)


@dataclass
class CompanyImpact:
    """Impact assessment for a single listed company."""

    isin: str
    ticker: str
    company_name: str
    sector: str
    impact_label: ImpactLabel
    confidence: float  # 0.0 – 1.0
    car_predicted: float  # Predicted CAR[0, +20d]
    car_lower: float = 0.0  # Lower bound of 95% CI
    car_upper: float = 0.0  # Upper bound of 95% CI
    rationale: str = ""
    top_features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "isin": self.isin,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "sector": self.sector,
            "impact_label": self.impact_label.value,
            "confidence": self.confidence,
            "car_predicted": self.car_predicted,
            "car_lower": self.car_lower,
            "car_upper": self.car_upper,
            "rationale": self.rationale,
            "top_features": self.top_features,
        }


@dataclass
class Prediction:
    """
    Full prediction report for a single bill.

    This is the top-level output returned by the Predictor and served
    by the prediction API (Task 9).

    Attributes
    ----------
    bill_id : str
        The bill for which predictions are generated.
    model_version : str
        Version string of the model that generated this prediction.
    predicted_at : datetime
        Timestamp of prediction generation.
    sectors : list[SectorImpact]
        Sector-level impact rankings (ordered by confidence descending).
    companies : list[CompanyImpact]
        Company-level impact rankings (ordered by |car_predicted| descending).
    overall_impact : ImpactLabel
        Aggregate bill-level impact label (majority vote across companies).
    notes : str
        Any free-text notes or caveats from the prediction pipeline.
    """

    bill_id: str
    model_version: str
    predicted_at: datetime
    sectors: list[SectorImpact] = field(default_factory=list)
    companies: list[CompanyImpact] = field(default_factory=list)
    overall_impact: ImpactLabel = ImpactLabel.UNKNOWN
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "bill_id": self.bill_id,
            "model_version": self.model_version,
            "predicted_at": self.predicted_at.isoformat(),
            "overall_impact": self.overall_impact.value,
            "sectors": [
                {
                    "sector": s.sector,
                    "impact_label": s.impact_label.value,
                    "confidence": s.confidence,
                    "rationale": s.rationale,
                }
                for s in self.sectors
            ],
            "companies": [c.to_dict() for c in self.companies],
            "notes": self.notes,
        }

    def __repr__(self) -> str:
        return (
            f"<Prediction bill_id={self.bill_id!r} "
            f"overall={self.overall_impact.value!r} "
            f"companies={len(self.companies)}>"
        )
