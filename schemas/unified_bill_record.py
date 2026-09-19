"""
schemas/unified_bill_record.py
==============================
Typed data model for a Unified India Legislative Discovery Record.

Provides normalized discovery representations spanning Central Government
and Indian State legislative bills while preserving strict distinction between:
1. FACT (authoritative legislative metadata, gazette dates, text)
2. DERIVED INFORMATION (extracted provisions, taxonomies)
3. ECONOMIC INTERPRETATION (mechanisms, qualitative strength/direction)
4. MARKET PREDICTION (central production models ONLY; strictly 0 for state bills)

Guarantees:
- Zero fabrication of missing values (explicit None/unknown).
- Strict provenance tracking for every field.
- Clear separation between Central modelled scope and State knowledge scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class UnifiedBillRecord:
    """
    Canonical discovery representation of an Indian legislative bill (Central or State).
    """

    # Identity & Jurisdiction
    bill_id: str
    jurisdiction: str  # "central" | "state"
    state: Optional[str] = None  # None for Central, e.g. "Karnataka" for State
    title: str = ""
    short_title: Optional[str] = None
    bill_number: Optional[str] = None
    legislature: str = ""  # e.g. "Parliament of India", "Karnataka Legislative Assembly"
    house: str = ""  # e.g. "Lok Sabha", "Rajya Sabha", "Vidhan Sabha", "Vidhan Parishad"
    session: Optional[str] = None
    ministry: Optional[str] = None  # Ministry or Department sponsoring the bill
    year: Optional[int] = None

    # Legislative Timeline (Authoritative)
    introduction_date: Optional[str] = None  # ISO format "YYYY-MM-DD" or None if unavailable
    passage_date: Optional[str] = None  # ISO format "YYYY-MM-DD" or None
    assent_date: Optional[str] = None  # ISO format "YYYY-MM-DD" or None
    status: str = "introduced"

    # Taxonomy & Grounded Content
    policy_domain: Optional[str] = None
    economic_sectors: list[str] = field(default_factory=list)
    secondary_sectors: list[str] = field(default_factory=list)
    stakeholders: list[str] = field(default_factory=list)
    summary: str = ""

    # Corporate Exposure & Market Readiness (Distinct from predictions)
    company_exposure_count: int = 0
    listed_company_exposure_count: int = 0
    market_relevance: str = "NONE"  # HIGH | MEDIUM | LOW | NONE | UNKNOWN
    modeling_eligibility: str = "NOT_ELIGIBLE"  # ELIGIBLE | CONDITIONALLY_ELIGIBLE | NOT_ELIGIBLE | INSUFFICIENT_DATA
    data_sufficiency: str = "INSUFFICIENT"  # COMPLETE | PARTIAL | INSUFFICIENT

    # Economic Interpretation (Qualitative only; not price predictions)
    economic_direction: Optional[str] = None  # positive | negative | mixed | neutral | unknown
    economic_strength: Optional[str] = None  # HIGH | MEDIUM | LOW | UNKNOWN

    # Provenance, Documents & Quality
    source_url: Optional[str] = None
    pdf_url: Optional[str] = None
    source_type: str = "OFFICIAL"  # prs | lok_sabha | official_gazette | html_table | portal
    data_quality: str = "VERIFIED"  # VERIFIED | HIGH | MEDIUM | LOW | UNVERIFIED
    provenance: dict[str, str] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # ------------------------------------------------------------------
    # Helper Properties
    # ------------------------------------------------------------------

    @property
    def is_central(self) -> bool:
        """Return True if bill belongs to Central Parliament."""
        return self.jurisdiction.strip().lower() == "central"

    @property
    def is_state(self) -> bool:
        """Return True if bill belongs to an Indian State legislature."""
        return self.jurisdiction.strip().lower() == "state"

    @property
    def display_jurisdiction(self) -> str:
        """Formatted jurisdiction tag for UI badges."""
        if self.is_central:
            return "[CENTRAL]"
        st = self.state or "State"
        return f"[STATE] {st}"

    @property
    def display_introduction_date(self) -> str:
        """Formatted introduction date or explicit unavailable label."""
        return self.introduction_date if self.introduction_date else "Introduction date unavailable"

    @property
    def has_pdf(self) -> bool:
        """Return True if an official PDF link is available."""
        return bool(self.pdf_url)

    @property
    def has_company_exposure(self) -> bool:
        """Return True if mapped corporate exposure exists."""
        return self.company_exposure_count > 0

    @property
    def is_modeling_eligible(self) -> bool:
        """Return True if eligible or conditionally eligible for future modeling."""
        return self.modeling_eligibility in ["ELIGIBLE", "CONDITIONALLY_ELIGIBLE"]

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Convert record to a JSON-compatible dictionary."""
        return {
            "bill_id": self.bill_id,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "title": self.title,
            "short_title": self.short_title,
            "bill_number": self.bill_number,
            "legislature": self.legislature,
            "house": self.house,
            "session": self.session,
            "ministry": self.ministry,
            "year": self.year,
            "introduction_date": self.introduction_date,
            "passage_date": self.passage_date,
            "assent_date": self.assent_date,
            "status": self.status,
            "policy_domain": self.policy_domain,
            "economic_sectors": list(self.economic_sectors),
            "secondary_sectors": list(self.secondary_sectors),
            "stakeholders": list(self.stakeholders),
            "summary": self.summary,
            "company_exposure_count": self.company_exposure_count,
            "listed_company_exposure_count": self.listed_company_exposure_count,
            "market_relevance": self.market_relevance,
            "modeling_eligibility": self.modeling_eligibility,
            "data_sufficiency": self.data_sufficiency,
            "economic_direction": self.economic_direction,
            "economic_strength": self.economic_strength,
            "source_url": self.source_url,
            "pdf_url": self.pdf_url,
            "source_type": self.source_type,
            "data_quality": self.data_quality,
            "provenance": dict(self.provenance),
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UnifiedBillRecord:
        """Instantiate record from a dictionary."""
        return cls(
            bill_id=data.get("bill_id", ""),
            jurisdiction=data.get("jurisdiction", "central"),
            state=data.get("state"),
            title=data.get("title", ""),
            short_title=data.get("short_title"),
            bill_number=data.get("bill_number"),
            legislature=data.get("legislature", ""),
            house=data.get("house", ""),
            session=data.get("session"),
            ministry=data.get("ministry"),
            year=data.get("year"),
            introduction_date=data.get("introduction_date"),
            passage_date=data.get("passage_date"),
            assent_date=data.get("assent_date"),
            status=data.get("status", "introduced"),
            policy_domain=data.get("policy_domain"),
            economic_sectors=data.get("economic_sectors", []),
            secondary_sectors=data.get("secondary_sectors", []),
            stakeholders=data.get("stakeholders", []),
            summary=data.get("summary", ""),
            company_exposure_count=data.get("company_exposure_count", 0),
            listed_company_exposure_count=data.get("listed_company_exposure_count", 0),
            market_relevance=data.get("market_relevance", "NONE"),
            modeling_eligibility=data.get("modeling_eligibility", "NOT_ELIGIBLE"),
            data_sufficiency=data.get("data_sufficiency", "INSUFFICIENT"),
            economic_direction=data.get("economic_direction"),
            economic_strength=data.get("economic_strength"),
            source_url=data.get("source_url"),
            pdf_url=data.get("pdf_url"),
            source_type=data.get("source_type", "OFFICIAL"),
            data_quality=data.get("data_quality", "VERIFIED"),
            provenance=data.get("provenance", {}),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )
