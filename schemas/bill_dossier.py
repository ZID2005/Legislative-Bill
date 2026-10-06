"""
schemas/bill_dossier.py
=======================
Task 8.27 — Legislative Intelligence Enrichment & Bill Dossier 2.0.

Extensible domain data models for enriched legislative dossiers spanning
Central and State jurisdictions, live and frozen datasets.

Strict Architectural Separation:
- FACT: Directly supported by authoritative sources (dates, official numbers, gazette text).
- DERIVED: Systematically structured attributes (extracted provisions, sector classifications).
- INTERPRETATION: Analytical explanations of mechanisms and implications (plain language, stakeholder impact).
- PREDICTION: Quantitative market forecasts from the validated Central analytical engine ONLY.

CRITICAL INVARIANTS:
1. Zero automatic stock predictions for newly discovered or State bills.
2. Newly discovered live bills default to KNOWLEDGE_ONLY.
3. No buy/sell/hold or investment recommendations in stakeholder views.
4. Document changes strictly distinguished from legislative status changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ModelStatus(str, Enum):
    """Analytical model status of a legislative bill."""

    MODELLED = "MODELLED"              # Frozen Central quantitative model (20 bills)
    KNOWLEDGE_ONLY = "KNOWLEDGE_ONLY"  # Live knowledge base or qualitative only
    PENDING_REVIEW = "PENDING_REVIEW"  # Queued for quantitative analytical ingestion
    NOT_ELIGIBLE = "NOT_ELIGIBLE"      # Ineligible (e.g., State bills, non-legislative bills)


class TimelineStage(str, Enum):
    """Authoritative stages in a bill's procedural journey."""

    DISCOVERED = "DISCOVERED"
    INTRODUCED = "INTRODUCED"
    REFERRED = "REFERRED"
    COMMITTEE_REVIEW = "COMMITTEE_REVIEW"
    PASSED = "PASSED"
    ASSENT = "ASSENT"
    NOTIFIED = "NOTIFIED"
    UPDATED = "UPDATED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"


class ExposureType(str, Enum):
    """Categorical exposure classification."""

    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"
    POTENTIAL = "POTENTIAL"
    UNKNOWN = "UNKNOWN"


class StakeholderPersona(str, Enum):
    """Standardized stakeholder personas for factual impact views."""

    INVESTOR = "INVESTOR"
    BUSINESS_OWNER = "BUSINESS_OWNER"
    EMPLOYEE_PROFESSIONAL = "EMPLOYEE_PROFESSIONAL"
    COMMON_CITIZEN = "COMMON_CITIZEN"
    RESEARCHER = "RESEARCHER"


# ---------------------------------------------------------------------------
# Timeline & Changes
# ---------------------------------------------------------------------------


@dataclass
class TimelineEvent:
    """Chronological milestone in a bill's journey supported by evidence."""

    event_id: str
    stage: str                          # TimelineStage value
    stage_label: str
    date: Optional[str] = None          # ISO format or None if not officially verified
    source_authority: str = "Authoritative Legislative Source"
    description: str = ""
    evidence_type: str = "FACT"         # FACT | OFFICIAL_RECORD
    document_url: Optional[str] = None
    chamber: Optional[str] = None
    verified: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "stage": self.stage,
            "stage_label": self.stage_label,
            "date": self.date,
            "source_authority": self.source_authority,
            "description": self.description,
            "evidence_type": self.evidence_type,
            "document_url": self.document_url,
            "chamber": self.chamber,
            "verified": self.verified,
        }


@dataclass
class DocumentChangeDetail:
    """Document-level modification detail (e.g., PDF hash update)."""

    document_url: str
    previous_hash: Optional[str] = None
    new_hash: Optional[str] = None
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    change_type: str = "DOCUMENT_METADATA_UPDATE"
    file_size_bytes: Optional[int] = None
    notes: str = "Document binary/hash changed; does not necessarily constitute legislative status change."

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_url": self.document_url,
            "previous_hash": self.previous_hash,
            "new_hash": self.new_hash,
            "detected_at": self.detected_at,
            "change_type": self.change_type,
            "file_size_bytes": self.file_size_bytes,
            "notes": self.notes,
        }


@dataclass
class LegislativeChangeDetail:
    """Substantive legislative or procedural change."""

    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    detected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source_authority: str = "Official Parliamentary Source"
    change_type: str = "LEGISLATIVE_STATUS_CHANGE"
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "detected_at": self.detected_at,
            "source_authority": self.source_authority,
            "change_type": self.change_type,
            "description": self.description,
        }


@dataclass
class BillChangeSummary:
    """Structured 'What Changed?' summary distinguishing document from legislative changes."""

    has_changes: bool = False
    total_changes: int = 0
    last_change_detected_at: Optional[str] = None
    document_changes: list[DocumentChangeDetail] = field(default_factory=list)
    legislative_changes: list[LegislativeChangeDetail] = field(default_factory=list)
    summary_text: str = "No revisions detected since baseline recording."
    separation_notice: str = (
        "DOCUMENT CHANGE vs LEGISLATIVE STATUS CHANGE: Document-level comparison distinguishes "
        "file re-indexing from substantive procedural advancements. A metadata/PDF change is not "
        "claimed as a statutory status change without authoritative procedural evidence."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_changes": self.has_changes,
            "total_changes": self.total_changes,
            "last_change_detected_at": self.last_change_detected_at,
            "document_changes": [d.to_dict() for d in self.document_changes],
            "legislative_changes": [l.to_dict() for l in self.legislative_changes],
            "summary_text": self.summary_text,
            "separation_notice": self.separation_notice,
        }


# ---------------------------------------------------------------------------
# Plain-Language & Stakeholder Views
# ---------------------------------------------------------------------------


@dataclass
class PlainLanguageExplanation:
    """Structured plain-language analysis for non-experts."""

    what_is_this_bill: str = ""
    what_does_it_change: str = ""
    who_could_be_affected: str = ""
    why_could_it_matter_economically: str = ""
    what_is_still_unknown: str = ""
    grounded_sources: list[str] = field(default_factory=list)
    epistemic_level: str = "INTERPRETATION"
    epistemic_notice: str = (
        "INTERPRETATION: Derived explanation grounded strictly in the underlying legislative record. "
        "Does not constitute legal advice or market prediction."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "what_is_this_bill": self.what_is_this_bill,
            "what_does_it_change": self.what_does_it_change,
            "who_could_be_affected": self.who_could_be_affected,
            "why_could_it_matter_economically": self.why_could_it_matter_economically,
            "what_is_still_unknown": self.what_is_still_unknown,
            "grounded_sources": self.grounded_sources,
            "epistemic_level": self.epistemic_level,
            "epistemic_notice": self.epistemic_notice,
        }


@dataclass
class StakeholderPersonaView:
    """Factual stakeholder perspective with strict epistemic separation."""

    persona: str                        # StakeholderPersona value
    persona_title: str
    icon: str
    fact: str                           # FACT: Official legislative text / status
    interpretation: str                 # INTERPRETATION: Structured operational impact
    prediction: str                     # PREDICTION: Quant forecast if modelled, else explicitly unavailable
    caveats: str = "Informational analysis only. Does not provide investment recommendations (Buy/Sell/Hold)."

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona": self.persona,
            "persona_title": self.persona_title,
            "icon": self.icon,
            "fact": self.fact,
            "interpretation": self.interpretation,
            "prediction": self.prediction,
            "caveats": self.caveats,
        }


# ---------------------------------------------------------------------------
# Sector & Corporate Exposure
# ---------------------------------------------------------------------------


@dataclass
class SectorExposureItem:
    """Sector/Industry exposure item connected to Macro Sector Directory."""

    sector: str
    industries: list[str] = field(default_factory=list)
    relevance: str = "HIGH"
    business_activities: list[str] = field(default_factory=list)
    exposure_type: str = ExposureType.DIRECT.value
    transmission_channel: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sector": self.sector,
            "industries": self.industries,
            "relevance": self.relevance,
            "business_activities": self.business_activities,
            "exposure_type": self.exposure_type,
            "transmission_channel": self.transmission_channel,
        }


@dataclass
class LinkedCompanyExposureItem:
    """Company intelligence exposure record grounded in evidence."""

    company_id: str
    company_name: str
    isin: Optional[str] = None
    ticker_nse: Optional[str] = None
    sector: str = ""
    industry: str = ""
    linkage_reasons: list[str] = field(default_factory=list)
    exposure_type: str = ExposureType.DIRECT.value
    exposure_direction: str = "neutral"
    exposure_strength: str = "MEDIUM"
    mechanism: str = ""
    evidence_summary: str = ""
    source_urls: list[str] = field(default_factory=list)
    is_quant_eligible: bool = False
    has_market_predictions: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "isin": self.isin,
            "ticker_nse": self.ticker_nse,
            "sector": self.sector,
            "industry": self.industry,
            "linkage_reasons": self.linkage_reasons,
            "exposure_type": self.exposure_type,
            "exposure_direction": self.exposure_direction,
            "exposure_strength": self.exposure_strength,
            "mechanism": self.mechanism,
            "evidence_summary": self.evidence_summary,
            "source_urls": self.source_urls,
            "is_quant_eligible": self.is_quant_eligible,
            "has_market_predictions": self.has_market_predictions,
        }


@dataclass
class BillDocumentItem:
    """Official supporting document representation."""

    document_id: str
    title: str
    url: Optional[str] = None
    hash_sha256: Optional[str] = None
    format: str = "PDF"                 # PDF | HTML | GAZETTE
    retrieved_at: Optional[str] = None
    retrieval_status: str = "AVAILABLE" # AVAILABLE | RETRIEVAL_PENDING | OFFICIAL_PORTAL_ONLY | FAILED_FETCH
    provenance: str = "AUTHORITATIVE"
    page_count: Optional[int] = None
    source_authority: str = "Official Parliamentary Repository"

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "url": self.url,
            "hash_sha256": self.hash_sha256,
            "format": self.format,
            "retrieved_at": self.retrieved_at,
            "retrieval_status": self.retrieval_status,
            "provenance": self.provenance,
            "page_count": self.page_count,
            "source_authority": self.source_authority,
        }


# ---------------------------------------------------------------------------
# Enriched Bill Dossier Core
# ---------------------------------------------------------------------------


@dataclass
class DossierIdentity:
    """Bill Identity attributes."""

    bill_id: str
    title: str
    short_title: str
    bill_number: Optional[str] = None
    jurisdiction: str = "central"       # central | state
    state: Optional[str] = None
    house: str = ""                     # Lok Sabha, Rajya Sabha, Vidhan Sabha, etc.
    legislature: str = ""               # Parliament of India, Karnataka Legislative Assembly, etc.
    ministry: Optional[str] = None
    bill_type: str = "Government Bill"  # Government Bill | Private Member Bill | Amendment Bill
    year: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_id": self.bill_id,
            "title": self.title,
            "short_title": self.short_title,
            "bill_number": self.bill_number,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "house": self.house,
            "legislature": self.legislature,
            "ministry": self.ministry,
            "bill_type": self.bill_type,
            "year": self.year,
        }


@dataclass
class DossierStatus:
    """Bill Status and procedural tracking."""

    current_status: str
    current_legislative_stage: str
    introduction_date: Optional[str] = None
    passage_date: Optional[str] = None
    assent_date: Optional[str] = None
    latest_verified_update: Optional[str] = None
    status_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_status": self.current_status,
            "current_legislative_stage": self.current_legislative_stage,
            "introduction_date": self.introduction_date,
            "passage_date": self.passage_date,
            "assent_date": self.assent_date,
            "latest_verified_update": self.latest_verified_update,
            "status_history": self.status_history,
        }


@dataclass
class DossierContent:
    """Statutory and grounded analytical content."""

    executive_summary: str = ""
    plain_language: PlainLanguageExplanation = field(default_factory=PlainLanguageExplanation)
    key_provisions: list[str] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    affected_activities: list[str] = field(default_factory=list)
    implementation_info: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "executive_summary": self.executive_summary,
            "plain_language": self.plain_language.to_dict(),
            "key_provisions": self.key_provisions,
            "obligations": self.obligations,
            "affected_activities": self.affected_activities,
            "implementation_info": self.implementation_info,
        }


@dataclass
class DossierImpactContext:
    """Economic, sectoral, and enterprise impact context."""

    affected_sectors: list[str] = field(default_factory=list)
    affected_industries: list[str] = field(default_factory=list)
    economic_themes: list[str] = field(default_factory=list)
    potentially_exposed_business_activities: list[str] = field(default_factory=list)
    company_exposure_count: int = 0
    listed_company_exposure_count: int = 0
    market_relevance: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "affected_sectors": self.affected_sectors,
            "affected_industries": self.affected_industries,
            "economic_themes": self.economic_themes,
            "potentially_exposed_business_activities": self.potentially_exposed_business_activities,
            "company_exposure_count": self.company_exposure_count,
            "listed_company_exposure_count": self.listed_company_exposure_count,
            "market_relevance": self.market_relevance,
        }


@dataclass
class DossierProvenance:
    """Source authority and provenance verification."""

    official_source: str
    source_authority: str
    source_url: Optional[str] = None
    document_url: Optional[str] = None
    document_hash: Optional[str] = None
    discovered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    verified_at: Optional[str] = None
    last_updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    data_quality: str = "VERIFIED"
    provenance_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "official_source": self.official_source,
            "source_authority": self.source_authority,
            "source_url": self.source_url,
            "document_url": self.document_url,
            "document_hash": self.document_hash,
            "discovered_at": self.discovered_at,
            "verified_at": self.verified_at,
            "last_updated_at": self.last_updated_at,
            "data_quality": self.data_quality,
            "provenance_map": self.provenance_map,
        }


@dataclass
class EnrichedBillDossier:
    """
    Complete enriched legislative intelligence dossier representation.
    Unifies identity, status, statutory content, impact, provenance, timeline,
    changes, documents, stakeholder perspectives, and model boundaries.
    """

    identity: DossierIdentity
    status: DossierStatus
    content: DossierContent
    impact_context: DossierImpactContext
    provenance: DossierProvenance
    model_status: str                   # ModelStatus value (MODELLED | KNOWLEDGE_ONLY | PENDING_REVIEW | NOT_ELIGIBLE)
    model_status_label: str
    model_status_description: str
    prediction_available: bool = False
    timeline: list[TimelineEvent] = field(default_factory=list)
    change_summary: BillChangeSummary = field(default_factory=BillChangeSummary)
    stakeholder_views: dict[str, StakeholderPersonaView] = field(default_factory=dict)
    sector_exposures: list[SectorExposureItem] = field(default_factory=list)
    company_exposures: list[LinkedCompanyExposureItem] = field(default_factory=list)
    documents: list[BillDocumentItem] = field(default_factory=list)
    ai_explanation: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity.to_dict(),
            "status": self.status.to_dict(),
            "content": self.content.to_dict(),
            "impact_context": self.impact_context.to_dict(),
            "provenance": self.provenance.to_dict(),
            "model_status": self.model_status,
            "model_status_label": self.model_status_label,
            "model_status_description": self.model_status_description,
            "prediction_available": self.prediction_available,
            "timeline": [t.to_dict() for t in self.timeline],
            "change_summary": self.change_summary.to_dict(),
            "stakeholder_views": {k: v.to_dict() for k, v in self.stakeholder_views.items()},
            "sector_exposures": [s.to_dict() for s in self.sector_exposures],
            "company_exposures": [c.to_dict() for c in self.company_exposures],
            "documents": [d.to_dict() for d in self.documents],
            "ai_explanation": self.ai_explanation,
        }
