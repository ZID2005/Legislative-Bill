"""
schemas/decision.py
===================
Typed data models for the Decision Support & Risk Scoring Engine (Task 7.2).

Defines canonical data structures for:
1. RiskCategory, PricingInRisk, StakeholderPerspective (Enums)
2. DecisionSupportRecord: Multi-stakeholder decision interpretation, composite risk/impact scores.
3. DecisionValidationReport: Pre-decision integrity, anti-leakage, and compatibility audit report.
4. Deterministic ID generation and serialization helpers.
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


def make_decision_id(bill_id: str, company_isin: str, event_window: str) -> str:
    """Generate a deterministic, unique decision support ID for a (bill, company, event_window) tuple."""
    b_id = sanitize_id(bill_id)
    isin = sanitize_id(company_isin)
    win = sanitize_id(event_window)
    return f"dec_{b_id}_{isin}_{win}"


# ---------------------------------------------------------------------------
# Decision Support Target Enumerations
# ---------------------------------------------------------------------------


class RiskCategory(str, Enum):
    """Deterministic categorical risk/impact tier."""

    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class PricingInRisk(str, Enum):
    """Categorical pre-event market pricing-in tier."""

    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class StakeholderPerspective(str, Enum):
    """Target stakeholder perspective for synthesized narrative."""

    INVESTOR = "INVESTOR"
    BUSINESS = "BUSINESS"
    PUBLIC = "PUBLIC"


# ---------------------------------------------------------------------------
# Canonical DecisionSupportRecord
# ---------------------------------------------------------------------------


@dataclass
class DecisionSupportRecord:
    """
    Strongly-typed decision-support and risk-scoring record for a (bill × company × event_window) observation.

    Transforms Task 7.1 predictions into qualitative interpretations for investors,
    corporates, and the general public, backed by deterministic composite risk scores.
    """

    decision_id: str
    bill_id: str
    company_isin: str
    event_window: str
    predicted_direction: str  # POSITIVE, NEGATIVE, NEUTRAL
    direction_probability: dict[str, float]  # e.g. {"POSITIVE": 0.82, "NEGATIVE": 0.05, "NEUTRAL": 0.13}
    market_moving_probability: float  # [0.0 - 1.0]
    predicted_impact_strength: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    confidence_probability: dict[str, float]  # e.g. {"LOW": 0.1, "MEDIUM": 0.2, "HIGH": 0.7}
    anticipation_class: str  # NO_EVIDENCE, WEAK_EVIDENCE, MODERATE_EVIDENCE, STRONG_EVIDENCE, NOT_ANALYZED
    anticipation_score: float  # [0.0 - 1.0]
    impact_score: float  # [0.0 - 1.0]
    risk_score: float  # [0.0 - 1.0]
    risk_category: str  # VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH
    pricing_in_risk: str  # VERY_LOW, LOW, MODERATE, HIGH
    investor_summary: str  # Perspective 1: Direction, strength, confidence, pricing-in
    business_summary: str  # Perspective 2: Sector, exposure, regulatory implications
    public_summary: str  # Perspective 3: Plain-English bill explanation
    decision_reason: str  # Comprehensive decision rationale
    model_version: str  # e.g. "v1.0"
    feature_version: str  # e.g. "v1.0"
    company_name: str = ""
    company_symbol: str = ""
    sector: str = ""
    impact_probabilities: dict[str, float] = field(default_factory=dict)
    predicted_confidence: str = "LOW"
    confidence_score: float = 0.0  # Scalar summary confidence score [0.0 - 1.0]
    pricing_in_score: float = 0.0  # Scalar pricing-in factor [0.0 - 1.0]
    impact_category: str = "LOW"  # VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH
    decision_version: str = "v1.0"
    generation_timestamp: str = ""  # ISO-8601 UTC
    data_quality_status: str = "VALID"

    def __post_init__(self) -> None:
        if not self.decision_id:
            self.decision_id = make_decision_id(
                self.bill_id, self.company_isin, self.event_window
            )
        if not self.generation_timestamp:
            self.generation_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def to_dict(self) -> dict[str, Any]:
        """Serialise DecisionSupportRecord to JSON-safe dictionary."""
        return {
            "decision_id": self.decision_id,
            "bill_id": self.bill_id,
            "company_isin": self.company_isin,
            "company_name": self.company_name,
            "company_symbol": self.company_symbol,
            "sector": self.sector,
            "event_window": self.event_window,
            "predicted_direction": str(self.predicted_direction),
            "direction_probability": {
                k: float(v) for k, v in self.direction_probability.items()
            },
            "market_moving_probability": float(self.market_moving_probability),
            "predicted_impact_strength": str(self.predicted_impact_strength),
            "impact_probabilities": {
                k: float(v) for k, v in self.impact_probabilities.items()
            },
            "predicted_confidence": str(self.predicted_confidence),
            "confidence_probability": {
                k: float(v) for k, v in self.confidence_probability.items()
            },
            "confidence_score": float(self.confidence_score),
            "anticipation_class": str(self.anticipation_class),
            "anticipation_score": float(self.anticipation_score),
            "impact_score": float(self.impact_score),
            "impact_category": str(self.impact_category),
            "risk_score": float(self.risk_score),
            "risk_category": str(self.risk_category),
            "pricing_in_risk": str(self.pricing_in_risk),
            "pricing_in_score": float(self.pricing_in_score),
            "investor_summary": str(self.investor_summary),
            "business_summary": str(self.business_summary),
            "public_summary": str(self.public_summary),
            "decision_reason": str(self.decision_reason),
            "model_version": str(self.model_version),
            "feature_version": str(self.feature_version),
            "decision_version": str(self.decision_version),
            "generation_timestamp": str(self.generation_timestamp),
            "data_quality_status": str(self.data_quality_status),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DecisionSupportRecord:
        """Deserialise DecisionSupportRecord from dictionary."""
        return cls(
            decision_id=str(data.get("decision_id", "")),
            bill_id=str(data["bill_id"]),
            company_isin=str(data["company_isin"]),
            company_name=str(data.get("company_name", "")),
            company_symbol=str(data.get("company_symbol", "")),
            sector=str(data.get("sector", "")),
            event_window=str(data.get("event_window", "[-20,+20]")),
            predicted_direction=str(data["predicted_direction"]),
            direction_probability={
                k: float(v) for k, v in data.get("direction_probability", {}).items()
            },
            market_moving_probability=float(data.get("market_moving_probability", 0.0)),
            predicted_impact_strength=str(data.get("predicted_impact_strength", "LOW")),
            impact_probabilities={
                k: float(v) for k, v in data.get("impact_probabilities", {}).items()
            },
            predicted_confidence=str(data.get("predicted_confidence", "LOW")),
            confidence_probability={
                k: float(v) for k, v in data.get("confidence_probability", {}).items()
            },
            confidence_score=float(data.get("confidence_score", 0.0)),
            anticipation_class=str(data.get("anticipation_class", "NOT_ANALYZED")),
            anticipation_score=float(data.get("anticipation_score", 0.0)),
            impact_score=float(data.get("impact_score", 0.0)),
            impact_category=str(data.get("impact_category", "LOW")),
            risk_score=float(data.get("risk_score", 0.0)),
            risk_category=str(data.get("risk_category", "LOW")),
            pricing_in_risk=str(data.get("pricing_in_risk", "VERY_LOW")),
            pricing_in_score=float(data.get("pricing_in_score", 0.0)),
            investor_summary=str(data.get("investor_summary", "")),
            business_summary=str(data.get("business_summary", "")),
            public_summary=str(data.get("public_summary", "")),
            decision_reason=str(data.get("decision_reason", "")),
            model_version=str(data.get("model_version", "v1.0")),
            feature_version=str(data.get("feature_version", "v1.0")),
            decision_version=str(data.get("decision_version", "v1.0")),
            generation_timestamp=str(
                data.get("generation_timestamp", datetime.now(timezone.utc).isoformat())
            ),
            data_quality_status=str(data.get("data_quality_status", "VALID")),
        )


# ---------------------------------------------------------------------------
# DecisionValidationReport
# ---------------------------------------------------------------------------


@dataclass
class DecisionValidationReport:
    """
    Validation and audit report generated during pre-decision data and integrity verification.
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
            self.report_id = f"val_dec_{b}_{c}_{w}"

    def to_dict(self) -> dict[str, Any]:
        """Serialise DecisionValidationReport to JSON-safe dictionary."""
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
    def from_dict(cls, data: dict[str, Any]) -> DecisionValidationReport:
        """Deserialise DecisionValidationReport from dictionary."""
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
