"""
schemas/anticipation_evidence.py
=================================
Data schemas for Task 8.29: Anticipation Evidence Enrichment & Media Diffusion Intelligence.

Strict Epistemic & Institutional Disclaimers:
- Pre-event public information diffusion analytics measure observable public disclosures and market signals.
- They NEVER allege, prove, or imply:
  * insider trading
  * market manipulation
  * illegal disclosure
  * unlawful conduct
  * confidential information leakage
- Output is strictly: PUBLIC INFORMATION DIFFUSION INTELLIGENCE.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Optional


class PublicInformationSourceType(str, Enum):
    """Extensible taxonomy of public information sources."""

    OFFICIAL_LEGISLATIVE = "OFFICIAL_LEGISLATIVE"
    OFFICIAL_GOVERNMENT = "OFFICIAL_GOVERNMENT"
    PARLIAMENTARY = "PARLIAMENTARY"
    MINISTRY = "MINISTRY"
    REGULATOR = "REGULATOR"
    NEWS = "NEWS"
    BUSINESS_MEDIA = "BUSINESS_MEDIA"
    FINANCIAL_MEDIA = "FINANCIAL_MEDIA"
    SEARCH_TREND = "SEARCH_TREND"
    PUBLIC_DOCUMENT = "PUBLIC_DOCUMENT"
    OTHER = "OTHER"


class SourceCredibilityTier(str, Enum):
    """
    Deterministic evidence-quality classifications.
    These are evidence-quality classifications, NOT political credibility rankings.
    """

    TIER_1 = "TIER_1"  # Official government / legislature / regulator
    TIER_2 = "TIER_2"  # Established mainstream news / financial media
    TIER_3 = "TIER_3"  # Recognized industry publication
    TIER_4 = "TIER_4"  # Search/trend signal
    TIER_5 = "TIER_5"  # Unverified / low-confidence source


class TemporalRelation(str, Enum):
    """
    Temporal relation between publication timestamp and official legislative event timestamp.
    STRICT RULE: publication_timestamp < official_event_timestamp for PRE_EVENT.
    """

    PRE_EVENT = "PRE_EVENT"
    SAME_DAY = "SAME_DAY"
    POST_EVENT = "POST_EVENT"
    UNKNOWN = "UNKNOWN"


class VerificationStatus(str, Enum):
    """Data quality and verification state of public information evidence."""

    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    TEMPORALLY_UNKNOWN = "TEMPORALLY_UNKNOWN"


class EvidenceStrength(str, Enum):
    """Qualitative evidentiary strength of a match."""

    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class MarketSignalLevel(str, Enum):
    """Categorical strength of pre-event econometric market movements."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class PublicInformationSignalLevel(str, Enum):
    """Categorical strength of verified pre-event public information."""

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AnticipationContextClassification(str, Enum):
    """
    Additive anticipation context classification combining market signal and media evidence.
    Never collapses market and media signals into one opaque number.
    """

    MARKET_SIGNAL_ONLY = "MARKET_SIGNAL_ONLY"
    PUBLIC_INFORMATION_SUPPORTED = "PUBLIC_INFORMATION_SUPPORTED"
    MULTI_SOURCE_PUBLIC_INFORMATION = "MULTI_SOURCE_PUBLIC_INFORMATION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NO_PRE_EVENT_SIGNAL = "NO_PRE_EVENT_SIGNAL"
    UNKNOWN = "UNKNOWN"


NON_ACCUSATORY_DISCLAIMER: str = (
    "Observable public-information evidence and market signals measure pre-event "
    "information diffusion patterns only. They do not establish causation, illegal "
    "disclosure, market manipulation, or insider trading."
)


@dataclass
class PublicInformationEvidence:
    """
    Additive evidence model representing a verified, provenance-traceable
    public information record published prior to or surrounding a legislative event.
    """

    evidence_id: str
    bill_id: str
    jurisdiction: str
    source_type: PublicInformationSourceType
    source_name: str
    source_url: str
    publication_timestamp: str  # ISO-8601
    discovery_timestamp: str  # ISO-8601
    event_reference: str  # Official event timestamp / introduction date (e.g. "2024-02-01T11:00:00Z")
    headline: str
    summary: str
    relevance: float  # 0.0 to 1.0
    evidence_strength: EvidenceStrength
    temporal_relation: TemporalRelation
    source_credibility: SourceCredibilityTier
    entity_matches: list[str] = field(default_factory=list)
    sector_matches: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    hash: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    verification_status: VerificationStatus = VerificationStatus.VERIFIED
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    duplicate_of: Optional[str] = None
    canonical_evidence_id: Optional[str] = None
    match_reason: str = ""

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """Deterministic SHA-256 hash across canonical identity fields."""
        payload = f"{self.bill_id}|{self.source_url.strip().lower()}|{self.headline.strip().lower()}|{self.publication_timestamp}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "bill_id": self.bill_id,
            "jurisdiction": self.jurisdiction,
            "source_type": self.source_type.value if hasattr(self.source_type, "value") else str(self.source_type),
            "source_name": self.source_name,
            "source_url": self.source_url,
            "publication_timestamp": self.publication_timestamp,
            "discovery_timestamp": self.discovery_timestamp,
            "event_reference": self.event_reference,
            "headline": self.headline,
            "summary": self.summary,
            "relevance": float(self.relevance),
            "evidence_strength": (
                self.evidence_strength.value if hasattr(self.evidence_strength, "value") else str(self.evidence_strength)
            ),
            "temporal_relation": (
                self.temporal_relation.value if hasattr(self.temporal_relation, "value") else str(self.temporal_relation)
            ),
            "source_credibility": (
                self.source_credibility.value
                if hasattr(self.source_credibility, "value")
                else str(self.source_credibility)
            ),
            "entity_matches": list(self.entity_matches),
            "sector_matches": list(self.sector_matches),
            "keywords": list(self.keywords),
            "hash": self.hash,
            "provenance": dict(self.provenance),
            "verification_status": (
                self.verification_status.value
                if hasattr(self.verification_status, "value")
                else str(self.verification_status)
            ),
            "created_at": self.created_at,
            "duplicate_of": self.duplicate_of,
            "canonical_evidence_id": self.canonical_evidence_id,
            "match_reason": self.match_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PublicInformationEvidence:
        """Deserialize from dictionary."""
        source_type = data.get("source_type", PublicInformationSourceType.OTHER.value)
        if isinstance(source_type, str):
            try:
                source_type = PublicInformationSourceType(source_type)
            except ValueError:
                source_type = PublicInformationSourceType.OTHER

        source_credibility = data.get("source_credibility", SourceCredibilityTier.TIER_5.value)
        if isinstance(source_credibility, str):
            try:
                source_credibility = SourceCredibilityTier(source_credibility)
            except ValueError:
                source_credibility = SourceCredibilityTier.TIER_5

        temporal_relation = data.get("temporal_relation", TemporalRelation.UNKNOWN.value)
        if isinstance(temporal_relation, str):
            try:
                temporal_relation = TemporalRelation(temporal_relation)
            except ValueError:
                temporal_relation = TemporalRelation.UNKNOWN

        evidence_strength = data.get("evidence_strength", EvidenceStrength.MODERATE.value)
        if isinstance(evidence_strength, str):
            try:
                evidence_strength = EvidenceStrength(evidence_strength)
            except ValueError:
                evidence_strength = EvidenceStrength.MODERATE

        verification_status = data.get("verification_status", VerificationStatus.VERIFIED.value)
        if isinstance(verification_status, str):
            try:
                verification_status = VerificationStatus(verification_status)
            except ValueError:
                verification_status = VerificationStatus.VERIFIED

        return cls(
            evidence_id=str(data["evidence_id"]),
            bill_id=str(data["bill_id"]),
            jurisdiction=str(data.get("jurisdiction", "central")),
            source_type=source_type,
            source_name=str(data.get("source_name", "")),
            source_url=str(data.get("source_url", "")),
            publication_timestamp=str(data.get("publication_timestamp", "")),
            discovery_timestamp=str(data.get("discovery_timestamp", "")),
            event_reference=str(data.get("event_reference", "")),
            headline=str(data.get("headline", "")),
            summary=str(data.get("summary", "")),
            relevance=float(data.get("relevance", 0.0)),
            evidence_strength=evidence_strength,
            temporal_relation=temporal_relation,
            source_credibility=source_credibility,
            entity_matches=list(data.get("entity_matches", [])),
            sector_matches=list(data.get("sector_matches", [])),
            keywords=list(data.get("keywords", [])),
            hash=str(data.get("hash", "")),
            provenance=dict(data.get("provenance", {})),
            verification_status=verification_status,
            created_at=str(data.get("created_at", "")),
            duplicate_of=data.get("duplicate_of"),
            canonical_evidence_id=data.get("canonical_evidence_id"),
            match_reason=str(data.get("match_reason", "")),
        )


@dataclass
class SearchTrendEvidence:
    """
    Search-trend attention signal.
    Classified as PUBLIC_ATTENTION_SIGNAL, NOT PUBLIC_KNOWLEDGE_PROOF.
    """

    query: str
    region: str
    timestamp: str  # ISO-8601
    trend_value: float
    baseline_value: float
    spike_indicator: bool
    source: str = "Google Trends"
    classification: str = "PUBLIC_ATTENTION_SIGNAL"
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "region": self.region,
            "timestamp": self.timestamp,
            "trend_value": float(self.trend_value),
            "baseline_value": float(self.baseline_value),
            "spike_indicator": bool(self.spike_indicator),
            "source": self.source,
            "classification": self.classification,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchTrendEvidence:
        return cls(
            query=str(data["query"]),
            region=str(data.get("region", "IN")),
            timestamp=str(data["timestamp"]),
            trend_value=float(data.get("trend_value", 0.0)),
            baseline_value=float(data.get("baseline_value", 0.0)),
            spike_indicator=bool(data.get("spike_indicator", False)),
            source=str(data.get("source", "Google Trends")),
            classification=str(data.get("classification", "PUBLIC_ATTENTION_SIGNAL")),
            provenance=dict(data.get("provenance", {})),
        )


@dataclass
class MarketSignalSummary:
    """
    Summary of pre-event econometric market behavior from frozen records.
    Separated from external information evidence.
    """

    level: MarketSignalLevel
    market_signal_score: float  # Normalized 0.0 to 1.0
    car_magnitude: float
    z_score: float
    directional_persistence: float
    volatility: float
    signals_detected: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value if hasattr(self.level, "value") else str(self.level),
            "market_signal_score": float(self.market_signal_score),
            "car_magnitude": float(self.car_magnitude),
            "z_score": float(self.z_score),
            "directional_persistence": float(self.directional_persistence),
            "volatility": float(self.volatility),
            "signals_detected": list(self.signals_detected),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketSignalSummary:
        lvl = data.get("level", MarketSignalLevel.UNKNOWN.value)
        if isinstance(lvl, str):
            try:
                lvl = MarketSignalLevel(lvl)
            except ValueError:
                lvl = MarketSignalLevel.UNKNOWN

        return cls(
            level=lvl,
            market_signal_score=float(data.get("market_signal_score", 0.0)),
            car_magnitude=float(data.get("car_magnitude", 0.0)),
            z_score=float(data.get("z_score", 0.0)),
            directional_persistence=float(data.get("directional_persistence", 0.0)),
            volatility=float(data.get("volatility", 0.0)),
            signals_detected=list(data.get("signals_detected", [])),
        )


@dataclass
class PublicInformationSignalSummary:
    """
    Summary of independently verified public-information evidence.
    """

    level: PublicInformationSignalLevel
    public_information_evidence_score: float  # Normalized 0.0 to 1.0
    verified_pre_event_count: int
    independent_sources_count: int
    source_diversity_ratio: float  # Normalized 0.0 to 1.0
    credibility_tier_summary: dict[str, int] = field(default_factory=dict)
    earliest_evidence_date: Optional[str] = None
    latest_evidence_date: Optional[str] = None
    evidence_window_trading_days: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value if hasattr(self.level, "value") else str(self.level),
            "public_information_evidence_score": float(self.public_information_evidence_score),
            "verified_pre_event_count": int(self.verified_pre_event_count),
            "independent_sources_count": int(self.independent_sources_count),
            "source_diversity_ratio": float(self.source_diversity_ratio),
            "credibility_tier_summary": dict(self.credibility_tier_summary),
            "earliest_evidence_date": self.earliest_evidence_date,
            "latest_evidence_date": self.latest_evidence_date,
            "evidence_window_trading_days": self.evidence_window_trading_days,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PublicInformationSignalSummary:
        lvl = data.get("level", PublicInformationSignalLevel.NONE.value)
        if isinstance(lvl, str):
            try:
                lvl = PublicInformationSignalLevel(lvl)
            except ValueError:
                lvl = PublicInformationSignalLevel.NONE

        return cls(
            level=lvl,
            public_information_evidence_score=float(data.get("public_information_evidence_score", 0.0)),
            verified_pre_event_count=int(data.get("verified_pre_event_count", 0)),
            independent_sources_count=int(data.get("independent_sources_count", 0)),
            source_diversity_ratio=float(data.get("source_diversity_ratio", 0.0)),
            credibility_tier_summary=dict(data.get("credibility_tier_summary", {})),
            earliest_evidence_date=data.get("earliest_evidence_date"),
            latest_evidence_date=data.get("latest_evidence_date"),
            evidence_window_trading_days=data.get("evidence_window_trading_days"),
        )


@dataclass
class CombinedAnticipationContextSummary:
    """
    Combined context providing descriptive combination of market signal and public information evidence.
    NEVER collapses market and media signals into one opaque number.
    """

    classification: AnticipationContextClassification
    interpretation: str
    market_signal: MarketSignalLevel
    information_signal: PublicInformationSignalLevel
    epistemic_tag: str = "[EVIDENCE]"
    non_accusatory_disclaimer: str = NON_ACCUSATORY_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": (
                self.classification.value
                if hasattr(self.classification, "value")
                else str(self.classification)
            ),
            "interpretation": self.interpretation,
            "market_signal": (
                self.market_signal.value
                if hasattr(self.market_signal, "value")
                else str(self.market_signal)
            ),
            "information_signal": (
                self.information_signal.value
                if hasattr(self.information_signal, "value")
                else str(self.information_signal)
            ),
            "epistemic_tag": self.epistemic_tag,
            "non_accusatory_disclaimer": self.non_accusatory_disclaimer,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CombinedAnticipationContextSummary:
        cls_val = data.get("classification", AnticipationContextClassification.UNKNOWN.value)
        if isinstance(cls_val, str):
            try:
                cls_val = AnticipationContextClassification(cls_val)
            except ValueError:
                cls_val = AnticipationContextClassification.UNKNOWN

        m_sig = data.get("market_signal", MarketSignalLevel.UNKNOWN.value)
        if isinstance(m_sig, str):
            try:
                m_sig = MarketSignalLevel(m_sig)
            except ValueError:
                m_sig = MarketSignalLevel.UNKNOWN

        i_sig = data.get("information_signal", PublicInformationSignalLevel.NONE.value)
        if isinstance(i_sig, str):
            try:
                i_sig = PublicInformationSignalLevel(i_sig)
            except ValueError:
                i_sig = PublicInformationSignalLevel.NONE

        return cls(
            classification=cls_val,
            interpretation=str(data.get("interpretation", "")),
            market_signal=m_sig,
            information_signal=i_sig,
            epistemic_tag=str(data.get("epistemic_tag", "[EVIDENCE]")),
            non_accusatory_disclaimer=str(
                data.get("non_accusatory_disclaimer", NON_ACCUSATORY_DISCLAIMER)
            ),
        )


@dataclass
class AnticipationEvidenceContext:
    """
    Additive bill-company anticipation evidence context.
    Combines frozen market signal with new verified public-information evidence
    WITHOUT mutating the original frozen anticipation record.
    """

    bill_id: str
    company_isin: Optional[str] = None
    company_symbol: Optional[str] = None
    jurisdiction: str = "central"
    market_signal: MarketSignalSummary = field(
        default_factory=lambda: MarketSignalSummary(
            level=MarketSignalLevel.UNKNOWN,
            market_signal_score=0.0,
            car_magnitude=0.0,
            z_score=0.0,
            directional_persistence=0.0,
            volatility=0.0,
            signals_detected=[],
        )
    )
    public_information_signal: PublicInformationSignalSummary = field(
        default_factory=lambda: PublicInformationSignalSummary(
            level=PublicInformationSignalLevel.NONE,
            public_information_evidence_score=0.0,
            verified_pre_event_count=0,
            independent_sources_count=0,
            source_diversity_ratio=0.0,
        )
    )
    combined_context: CombinedAnticipationContextSummary = field(
        default_factory=lambda: CombinedAnticipationContextSummary(
            classification=AnticipationContextClassification.INSUFFICIENT_EVIDENCE,
            interpretation="Insufficient verified public-information evidence.",
            market_signal=MarketSignalLevel.UNKNOWN,
            information_signal=PublicInformationSignalLevel.NONE,
        )
    )
    evidence_items: list[PublicInformationEvidence] = field(default_factory=list)
    search_trend_items: list[SearchTrendEvidence] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_id": self.bill_id,
            "company_isin": self.company_isin,
            "company_symbol": self.company_symbol,
            "jurisdiction": self.jurisdiction,
            "market_signal": self.market_signal.to_dict(),
            "public_information_signal": self.public_information_signal.to_dict(),
            "combined_context": self.combined_context.to_dict(),
            "evidence_items": [ev.to_dict() for ev in self.evidence_items],
            "search_trend_items": [st.to_dict() for st in self.search_trend_items],
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnticipationEvidenceContext:
        return cls(
            bill_id=str(data["bill_id"]),
            company_isin=data.get("company_isin"),
            company_symbol=data.get("company_symbol"),
            jurisdiction=str(data.get("jurisdiction", "central")),
            market_signal=MarketSignalSummary.from_dict(data.get("market_signal", {})),
            public_information_signal=PublicInformationSignalSummary.from_dict(
                data.get("public_information_signal", {})
            ),
            combined_context=CombinedAnticipationContextSummary.from_dict(
                data.get("combined_context", {})
            ),
            evidence_items=[
                PublicInformationEvidence.from_dict(e) for e in data.get("evidence_items", [])
            ],
            search_trend_items=[
                SearchTrendEvidence.from_dict(s) for s in data.get("search_trend_items", [])
            ],
            created_at=str(data.get("created_at", "")),
        )
