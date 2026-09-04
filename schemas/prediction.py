"""
schemas/prediction.py
=====================
Typed data models for the Final Prediction & Decision Engine (Task 7.1).

Defines canonical data structures for:
1. DirectionPrediction, ImpactStrengthPrediction, ConfidencePrediction (Enums)
2. PredictionRecord: Full bill-company-event multi-target prediction and decision support output.
3. PredictionValidationReport: Integrity, dimension, and anti-leakage diagnostic audit record.
4. Backward-compatible stubs for legacy prediction consumers.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


def sanitize_id(identifier: str) -> str:
    """Sanitize identifier string to make it safe for OS filesystems and deterministic IDs."""
    if not identifier:
        return ""
    return (
        str(identifier)
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace(" ", "_")
        .replace("[", "")
        .replace("]", "")
        .replace("+", "p")
        .replace(",", "_")
    )


def make_prediction_id(bill_id: str, company_isin: str, event_window: str) -> str:
    """Generate a deterministic, unique prediction ID for a (bill, company, event_window) tuple."""
    b_id = sanitize_id(bill_id)
    isin = sanitize_id(company_isin)
    win = sanitize_id(event_window)
    return f"pred_{b_id}_{isin}_{win}"


# ---------------------------------------------------------------------------
# Prediction Target Enumerations
# ---------------------------------------------------------------------------


class DirectionPrediction(str, Enum):
    """Categorical market direction prediction."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class ImpactStrengthPrediction(str, Enum):
    """Categorical impact magnitude strength tier."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class ConfidencePrediction(str, Enum):
    """Categorical model confidence tier."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ---------------------------------------------------------------------------
# Canonical PredictionRecord
# ---------------------------------------------------------------------------


@dataclass
class PredictionRecord:
    """
    Strongly-typed final prediction and decision-support record for a (bill × company × event_window) observation.

    Separates objective model probability outputs from contextual decision-support interpretation.
    """

    prediction_id: str
    bill_id: str
    company_isin: str
    event_window: str
    predicted_direction: str  # POSITIVE, NEGATIVE, NEUTRAL
    direction_probability: dict[str, float]  # e.g. {"POSITIVE": 0.82, "NEGATIVE": 0.05, "NEUTRAL": 0.13}
    predicted_market_moving: bool  # True / False
    market_moving_probability: float  # probability of True [0.0 - 1.0]
    predicted_impact_strength: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    impact_probabilities: dict[str, float]  # e.g. {"LOW": 0.1, "MEDIUM": 0.3, "HIGH": 0.5, "VERY_HIGH": 0.1}
    predicted_confidence: str  # LOW, MEDIUM, HIGH
    confidence_probability: dict[str, float]  # e.g. {"LOW": 0.1, "MEDIUM": 0.2, "HIGH": 0.7}
    anticipation_class: str  # NO_EVIDENCE, WEAK_EVIDENCE, MODERATE_EVIDENCE, STRONG_EVIDENCE, NOT_ANALYZED
    anticipation_score: float  # [0.0 - 1.0]
    model_name: dict[str, str]  # e.g. {"direction": "lgbm", "market_moving": "random_forest", ...}
    model_version: str  # e.g. "v1.0"
    feature_version: str  # e.g. "v1.0"
    prediction_timestamp: str  # ISO-8601 UTC
    decision_reason: str  # Contextual interpretation separating prediction from trading advice
    expected_impact_estimate: Optional[str] = None
    risk_indicators: list[str] = field(default_factory=list)
    model_confidence: float = 0.0  # Scalar summary confidence score [0.0 - 1.0]
    data_quality_status: str = "VALID"  # VALID, IMPUTED, WARNING
    company_name: str = ""
    company_symbol: str = ""

    def __post_init__(self) -> None:
        if not self.prediction_id:
            self.prediction_id = make_prediction_id(
                self.bill_id, self.company_isin, self.event_window
            )
        if not self.prediction_timestamp:
            self.prediction_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def to_dict(self) -> dict[str, Any]:
        """Serialise PredictionRecord to JSON-safe dictionary."""
        return {
            "prediction_id": self.prediction_id,
            "bill_id": self.bill_id,
            "company_isin": self.company_isin,
            "company_name": self.company_name,
            "company_symbol": self.company_symbol,
            "event_window": self.event_window,
            "predicted_direction": str(self.predicted_direction),
            "direction_probability": {
                k: float(v) for k, v in self.direction_probability.items()
            },
            "predicted_market_moving": bool(self.predicted_market_moving),
            "market_moving_probability": float(self.market_moving_probability),
            "predicted_impact_strength": str(self.predicted_impact_strength),
            "impact_probabilities": {
                k: float(v) for k, v in self.impact_probabilities.items()
            },
            "predicted_confidence": str(self.predicted_confidence),
            "confidence_probability": {
                k: float(v) for k, v in self.confidence_probability.items()
            },
            "anticipation_class": str(self.anticipation_class),
            "anticipation_score": float(self.anticipation_score),
            "model_name": dict(self.model_name),
            "model_version": str(self.model_version),
            "feature_version": str(self.feature_version),
            "prediction_timestamp": str(self.prediction_timestamp),
            "decision_reason": str(self.decision_reason),
            "expected_impact_estimate": self.expected_impact_estimate,
            "risk_indicators": list(self.risk_indicators),
            "model_confidence": float(self.model_confidence),
            "data_quality_status": str(self.data_quality_status),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PredictionRecord:
        """Deserialise PredictionRecord from dictionary."""
        return cls(
            prediction_id=str(data.get("prediction_id", "")),
            bill_id=str(data["bill_id"]),
            company_isin=str(data["company_isin"]),
            company_name=str(data.get("company_name", "")),
            company_symbol=str(data.get("company_symbol", "")),
            event_window=str(data.get("event_window", "[-20,+20]")),
            predicted_direction=str(data["predicted_direction"]),
            direction_probability={
                k: float(v) for k, v in data.get("direction_probability", {}).items()
            },
            predicted_market_moving=bool(data.get("predicted_market_moving", False)),
            market_moving_probability=float(data.get("market_moving_probability", 0.0)),
            predicted_impact_strength=str(data.get("predicted_impact_strength", "LOW")),
            impact_probabilities={
                k: float(v) for k, v in data.get("impact_probabilities", {}).items()
            },
            predicted_confidence=str(data.get("predicted_confidence", "LOW")),
            confidence_probability={
                k: float(v) for k, v in data.get("confidence_probability", {}).items()
            },
            anticipation_class=str(data.get("anticipation_class", "NOT_ANALYZED")),
            anticipation_score=float(data.get("anticipation_score", 0.0)),
            model_name=dict(data.get("model_name", {})),
            model_version=str(data.get("model_version", "v1.0")),
            feature_version=str(data.get("feature_version", "v1.0")),
            prediction_timestamp=str(
                data.get("prediction_timestamp", datetime.now(timezone.utc).isoformat())
            ),
            decision_reason=str(data.get("decision_reason", "")),
            expected_impact_estimate=data.get("expected_impact_estimate"),
            risk_indicators=list(data.get("risk_indicators", [])),
            model_confidence=float(data.get("model_confidence", 0.0)),
            data_quality_status=str(data.get("data_quality_status", "VALID")),
        )


# ---------------------------------------------------------------------------
# PredictionValidationReport
# ---------------------------------------------------------------------------


@dataclass
class PredictionValidationReport:
    """
    Validation and audit report generated during pre-prediction data verification.
    """

    report_id: str
    bill_id: str
    company_isin: str
    event_window: str
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks_performed: dict[str, bool] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def __post_init__(self) -> None:
        if self.errors:
            self.is_valid = False
        if not self.report_id:
            b = sanitize_id(self.bill_id)
            c = sanitize_id(self.company_isin)
            w = sanitize_id(self.event_window)
            self.report_id = f"val_{b}_{c}_{w}"

    def to_dict(self) -> dict[str, Any]:
        """Serialise PredictionValidationReport to JSON-safe dictionary."""
        return {
            "report_id": self.report_id,
            "bill_id": self.bill_id,
            "company_isin": self.company_isin,
            "event_window": self.event_window,
            "is_valid": bool(self.is_valid),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "checks_performed": dict(self.checks_performed),
            "details": dict(self.details),
            "timestamp": str(self.timestamp),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PredictionValidationReport:
        """Deserialise PredictionValidationReport from dictionary."""
        return cls(
            report_id=str(data.get("report_id", "")),
            bill_id=str(data.get("bill_id", "")),
            company_isin=str(data.get("company_isin", "")),
            event_window=str(data.get("event_window", "")),
            is_valid=bool(data.get("is_valid", True)),
            errors=list(data.get("errors", [])),
            warnings=list(data.get("warnings", [])),
            checks_performed=dict(data.get("checks_performed", {})),
            details=dict(data.get("details", {})),
            timestamp=str(data.get("timestamp", datetime.now(timezone.utc).isoformat())),
        )


# ---------------------------------------------------------------------------
# Legacy Models (Preserved for backward compatibility)
# ---------------------------------------------------------------------------


class ImpactLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class SectorImpact:
    sector: str
    impact_label: ImpactLabel
    confidence: float
    rationale: str = ""
    top_features: list[str] = field(default_factory=list)


@dataclass
class CompanyImpact:
    isin: str
    ticker: str
    company_name: str
    sector: str
    impact_label: ImpactLabel
    confidence: float
    car_predicted: float
    car_lower: float = 0.0
    car_upper: float = 0.0
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
