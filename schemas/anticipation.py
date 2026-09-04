"""
schemas/anticipation.py
=======================
Data schemas for Task 6.5: Anticipation Bias / Pre-Event Information Analysis Engine.

Defines typed dataclasses for:
1. PreEventWindowStats: Statistics for a specific pre-event trading window.
2. InformationEvidence: External media/trends/official evidence records.
3. AnticipationClassification: Enumeration of anticipation strength tiers.
4. AnticipationScore: Company-bill pair anticipation score and diagnostic evidence.
5. BillAnticipationRecord: Aggregate bill-level anticipation rollup across companies.
6. AnticipationValidationReport: Data quality, anti-leakage audit, and rejection reports.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class AnticipationClassification(str, Enum):
    """
    Categorical strength of evidence for pre-event market anticipation.
    """

    NO_EVIDENCE = "NO_EVIDENCE"
    WEAK_EVIDENCE = "WEAK_EVIDENCE"
    MODERATE_EVIDENCE = "MODERATE_EVIDENCE"
    STRONG_EVIDENCE = "STRONG_EVIDENCE"


class EvidenceType(str, Enum):
    """
    Type of external pre-event information evidence.
    """

    NEWS = "NEWS"
    SEARCH_TREND = "SEARCH_TREND"
    PARLIAMENTARY = "PARLIAMENTARY"
    OFFICIAL = "OFFICIAL"
    OTHER = "OTHER"


class EvidenceConfidence(str, Enum):
    """
    Confidence level for an evidence item.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class PreEventWindowStats:
    """
    Statistical metrics for a single pre-event trading window (e.g. [-30,-21], [-2,-1], [-30,-1]).
    """

    window: str  # e.g. "[-30,-21]", "[-2,-1]", "[-30,-1]"
    start_offset: int  # e.g. -30
    end_offset: int  # e.g. -21
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    mean_abnormal_return: float  # MAR
    cumulative_abnormal_return: float  # CAR
    volatility: float  # Standard deviation of daily AR
    ar_z_score: float  # Z-score of CAR (CAR / (sqrt(N) * sigma_epsilon))
    observation_count: int  # Number of valid trading day observations (N)
    pct_positive_ar: float  # Fraction of days with AR > 0 (0.0 to 1.0)
    pct_negative_ar: float  # Fraction of days with AR < 0 (0.0 to 1.0)
    daily_dates: list[str] = field(default_factory=list)
    daily_ar: list[float] = field(default_factory=list)
    daily_car: list[float] = field(default_factory=list)
    is_statistically_significant: bool = False
    p_value: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict."""
        return {
            "window": self.window,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "mean_abnormal_return": float(self.mean_abnormal_return),
            "cumulative_abnormal_return": float(self.cumulative_abnormal_return),
            "volatility": float(self.volatility),
            "ar_z_score": float(self.ar_z_score),
            "observation_count": int(self.observation_count),
            "pct_positive_ar": float(self.pct_positive_ar),
            "pct_negative_ar": float(self.pct_negative_ar),
            "daily_dates": self.daily_dates,
            "daily_ar": [float(x) for x in self.daily_ar],
            "daily_car": [float(x) for x in self.daily_car],
            "is_statistically_significant": bool(self.is_statistically_significant),
            "p_value": float(self.p_value),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PreEventWindowStats:
        """Deserialise from dict."""
        return cls(
            window=str(data["window"]),
            start_offset=int(data["start_offset"]),
            end_offset=int(data["end_offset"]),
            start_date=str(data["start_date"]),
            end_date=str(data["end_date"]),
            mean_abnormal_return=float(data.get("mean_abnormal_return", 0.0)),
            cumulative_abnormal_return=float(data.get("cumulative_abnormal_return", 0.0)),
            volatility=float(data.get("volatility", 0.0)),
            ar_z_score=float(data.get("ar_z_score", 0.0)),
            observation_count=int(data.get("observation_count", 0)),
            pct_positive_ar=float(data.get("pct_positive_ar", 0.0)),
            pct_negative_ar=float(data.get("pct_negative_ar", 0.0)),
            daily_dates=list(data.get("daily_dates", [])),
            daily_ar=[float(x) for x in data.get("daily_ar", [])],
            daily_car=[float(x) for x in data.get("daily_car", [])],
            is_statistically_significant=bool(data.get("is_statistically_significant", False)),
            p_value=float(data.get("p_value", 1.0)),
        )


@dataclass
class InformationEvidence:
    """
    A single external evidence record (e.g. news article, search trend spike, consultation paper).
    """

    bill_id: str
    source: str  # e.g. "GDELT", "Google Trends", "PIB", "Lok Sabha Bulletin", "NewsAPI"
    publication_date: str  # YYYY-MM-DD
    headline: str
    source_url: str
    relevance_score: float  # 0.0 to 1.0
    evidence_type: str  # NEWS, SEARCH_TREND, PARLIAMENTARY, OFFICIAL, OTHER
    evidence_timestamp: str  # ISO-8601 timestamp
    confidence: str = "MEDIUM"  # LOW, MEDIUM, HIGH

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict."""
        return {
            "bill_id": self.bill_id,
            "source": self.source,
            "publication_date": self.publication_date,
            "headline": self.headline,
            "source_url": self.source_url,
            "relevance_score": float(self.relevance_score),
            "evidence_type": str(self.evidence_type),
            "evidence_timestamp": self.evidence_timestamp,
            "confidence": str(self.confidence),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InformationEvidence:
        """Deserialise from dict."""
        return cls(
            bill_id=str(data["bill_id"]),
            source=str(data.get("source", "")),
            publication_date=str(data["publication_date"]),
            headline=str(data.get("headline", "")),
            source_url=str(data.get("source_url", "")),
            relevance_score=float(data.get("relevance_score", 0.0)),
            evidence_type=str(data.get("evidence_type", "OTHER")),
            evidence_timestamp=str(data.get("evidence_timestamp", data["publication_date"])),
            confidence=str(data.get("confidence", "MEDIUM")),
        )


@dataclass
class AnticipationScore:
    """
    Anticipation evaluation record for a single bill-company pair.
    """

    bill_id: str
    company_isin: str
    company_symbol: str
    official_introduction_date: str  # T0 date
    market_signal_score: float  # Normalized 0.0 to 1.0
    information_signal_score: float  # Normalized 0.0 to 1.0
    anticipation_score: float  # Composite 0.0 to 1.0
    classification: str  # NO_EVIDENCE, WEAK_EVIDENCE, MODERATE_EVIDENCE, STRONG_EVIDENCE
    anticipation_flag: bool  # True if anticipation_score >= threshold
    confidence: str  # LOW, MEDIUM, HIGH
    evidence_count: int
    media_data_available: bool
    decision_reason: str
    window_stats: dict[str, PreEventWindowStats] = field(default_factory=dict)
    detected_signals: list[str] = field(default_factory=list)
    calculation_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict."""
        return {
            "bill_id": self.bill_id,
            "company_isin": self.company_isin,
            "company_symbol": self.company_symbol,
            "official_introduction_date": self.official_introduction_date,
            "market_signal_score": float(self.market_signal_score),
            "information_signal_score": float(self.information_signal_score),
            "anticipation_score": float(self.anticipation_score),
            "classification": str(self.classification),
            "anticipation_flag": bool(self.anticipation_flag),
            "confidence": str(self.confidence),
            "evidence_count": int(self.evidence_count),
            "media_data_available": bool(self.media_data_available),
            "decision_reason": self.decision_reason,
            "window_stats": {
                win_name: stats.to_dict() for win_name, stats in self.window_stats.items()
            },
            "detected_signals": self.detected_signals,
            "calculation_timestamp": self.calculation_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnticipationScore:
        """Deserialise from dict."""
        raw_stats = data.get("window_stats", {})
        window_stats = {
            win_name: PreEventWindowStats.from_dict(val)
            for win_name, val in raw_stats.items()
        }
        return cls(
            bill_id=str(data["bill_id"]),
            company_isin=str(data["company_isin"]),
            company_symbol=str(data.get("company_symbol", "")),
            official_introduction_date=str(data["official_introduction_date"]),
            market_signal_score=float(data.get("market_signal_score", 0.0)),
            information_signal_score=float(data.get("information_signal_score", 0.0)),
            anticipation_score=float(data.get("anticipation_score", 0.0)),
            classification=str(data.get("classification", AnticipationClassification.NO_EVIDENCE.value)),
            anticipation_flag=bool(data.get("anticipation_flag", False)),
            confidence=str(data.get("confidence", "LOW")),
            evidence_count=int(data.get("evidence_count", 0)),
            media_data_available=bool(data.get("media_data_available", False)),
            decision_reason=str(data.get("decision_reason", "")),
            window_stats=window_stats,
            detected_signals=list(data.get("detected_signals", [])),
            calculation_timestamp=str(
                data.get("calculation_timestamp", datetime.now(timezone.utc).isoformat())
            ),
        )


@dataclass
class BillAnticipationRecord:
    """
    Aggregated anticipation profile for a legislative bill across all associated companies.
    """

    bill_id: str
    bill_title: str
    official_introduction_date: str
    overall_anticipation_score: float
    overall_classification: str
    overall_anticipation_flag: bool
    overall_confidence: str
    total_companies_analyzed: int
    companies_with_anticipation_flag: int
    pct_companies_flagged: float
    mean_market_signal_score: float
    mean_info_signal_score: float
    total_evidence_count: int
    media_data_available: bool
    company_scores: list[AnticipationScore] = field(default_factory=list)
    decision_reason: str = ""
    calculation_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict."""
        return {
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "official_introduction_date": self.official_introduction_date,
            "overall_anticipation_score": float(self.overall_anticipation_score),
            "overall_classification": str(self.overall_classification),
            "overall_anticipation_flag": bool(self.overall_anticipation_flag),
            "overall_confidence": str(self.overall_confidence),
            "total_companies_analyzed": int(self.total_companies_analyzed),
            "companies_with_anticipation_flag": int(self.companies_with_anticipation_flag),
            "pct_companies_flagged": float(self.pct_companies_flagged),
            "mean_market_signal_score": float(self.mean_market_signal_score),
            "mean_info_signal_score": float(self.mean_info_signal_score),
            "total_evidence_count": int(self.total_evidence_count),
            "media_data_available": bool(self.media_data_available),
            "company_scores": [cs.to_dict() for cs in self.company_scores],
            "decision_reason": self.decision_reason,
            "calculation_timestamp": self.calculation_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BillAnticipationRecord:
        """Deserialise from dict."""
        company_scores = [
            AnticipationScore.from_dict(cs)
            for cs in data.get("company_scores", [])
        ]
        return cls(
            bill_id=str(data["bill_id"]),
            bill_title=str(data.get("bill_title", "")),
            official_introduction_date=str(data["official_introduction_date"]),
            overall_anticipation_score=float(data.get("overall_anticipation_score", 0.0)),
            overall_classification=str(
                data.get("overall_classification", AnticipationClassification.NO_EVIDENCE.value)
            ),
            overall_anticipation_flag=bool(data.get("overall_anticipation_flag", False)),
            overall_confidence=str(data.get("overall_confidence", "LOW")),
            total_companies_analyzed=int(data.get("total_companies_analyzed", 0)),
            companies_with_anticipation_flag=int(data.get("companies_with_anticipation_flag", 0)),
            pct_companies_flagged=float(data.get("pct_companies_flagged", 0.0)),
            mean_market_signal_score=float(data.get("mean_market_signal_score", 0.0)),
            mean_info_signal_score=float(data.get("mean_info_signal_score", 0.0)),
            total_evidence_count=int(data.get("total_evidence_count", 0)),
            media_data_available=bool(data.get("media_data_available", False)),
            company_scores=company_scores,
            decision_reason=str(data.get("decision_reason", "")),
            calculation_timestamp=str(
                data.get("calculation_timestamp", datetime.now(timezone.utc).isoformat())
            ),
        )


@dataclass
class AnticipationValidationReport:
    """
    Diagnostic validation report capturing data issues, anomalies, and anti-leakage audit results.
    """

    bill_id: str
    company_isin: Optional[str] = None
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    rejected_evidence_count: int = 0
    rejected_evidence_details: list[dict[str, Any]] = field(default_factory=list)
    validation_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def __post_init__(self) -> None:
        if self.errors:
            self.is_valid = False

    def add_error(self, message: str) -> None:
        """Add an error message and mark valid=False."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def add_rejected_evidence(self, evidence: InformationEvidence, reason: str) -> None:
        """Record rejected information evidence violating anti-leakage rules."""
        self.rejected_evidence_count += 1
        self.rejected_evidence_details.append({
            "evidence": evidence.to_dict(),
            "rejection_reason": reason,
        })
        self.warnings.append(
            f"REJECTED_EVIDENCE: [{evidence.source}] {evidence.headline} ({evidence.publication_date}) - {reason}"
        )

    def merge(self, other: AnticipationValidationReport) -> None:
        """Merge findings from another validation report."""
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.rejected_evidence_count += other.rejected_evidence_count
        self.rejected_evidence_details.extend(other.rejected_evidence_details)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to dict."""
        return {
            "bill_id": self.bill_id,
            "company_isin": self.company_isin,
            "is_valid": bool(self.is_valid),
            "errors": self.errors,
            "warnings": self.warnings,
            "rejected_evidence_count": int(self.rejected_evidence_count),
            "rejected_evidence_details": self.rejected_evidence_details,
            "validation_timestamp": self.validation_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnticipationValidationReport:
        """Deserialise from dict."""
        return cls(
            bill_id=str(data["bill_id"]),
            company_isin=data.get("company_isin"),
            is_valid=bool(data.get("is_valid", True)),
            errors=list(data.get("errors", [])),
            warnings=list(data.get("warnings", [])),
            rejected_evidence_count=int(data.get("rejected_evidence_count", 0)),
            rejected_evidence_details=list(data.get("rejected_evidence_details", [])),
            validation_timestamp=str(
                data.get("validation_timestamp", datetime.now(timezone.utc).isoformat())
            ),
        )
