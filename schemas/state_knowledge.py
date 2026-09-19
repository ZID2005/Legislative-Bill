"""
schemas/state_knowledge.py
==========================
Typed data model for an Indian State Legislative Bill Knowledge Record.

Represents the structured domain knowledge extracted and assigned for an
Indian State legislative bill, maintaining complete isolation from Central
prediction/market modeling schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class StateBillSummary:
    """
    Structured plain-language summary for an Indian State bill.
    Grounded strictly in extracted text and verified metadata without speculation.
    """

    what_is_bill: str = ""
    what_it_changes: str = ""
    why_it_matters: str = ""
    who_is_affected: str = ""
    key_provisions: list[str] = field(default_factory=list)
    administrative_implications: str = ""
    legislative_status: str = ""
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "what_is_bill": self.what_is_bill,
            "what_it_changes": self.what_it_changes,
            "why_it_matters": self.why_it_matters,
            "who_is_affected": self.who_is_affected,
            "key_provisions": self.key_provisions,
            "administrative_implications": self.administrative_implications,
            "legislative_status": self.legislative_status,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateBillSummary":
        return cls(
            what_is_bill=data.get("what_is_bill", ""),
            what_it_changes=data.get("what_it_changes", ""),
            why_it_matters=data.get("why_it_matters", ""),
            who_is_affected=data.get("who_is_affected", ""),
            key_provisions=data.get("key_provisions", []),
            administrative_implications=data.get("administrative_implications", ""),
            legislative_status=data.get("legislative_status", ""),
            source=data.get("source", ""),
        )


@dataclass
class StateBillKnowledge:
    """
    Canonical representation of structured domain knowledge for an Indian State legislative bill.
    """

    bill_id: str
    jurisdiction: str
    state: str
    title: str
    bill_number: str
    chamber: str
    status: str
    source_url: str
    policy_category: str
    category_provenance: str = "SYSTEM_DERIVED"
    year: Optional[int] = None
    introduction_date: Optional[str] = None
    assent_date: Optional[str] = None
    pdf_url: Optional[str] = None
    corpus_path: Optional[str] = None
    document_hash: Optional[str] = None
    summary: StateBillSummary = field(default_factory=StateBillSummary)
    objective: Optional[str] = None
    key_provisions: list[str] = field(default_factory=list)
    amended_acts: list[str] = field(default_factory=list)
    affected_stakeholders: list[str] = field(default_factory=list)
    administrative_authority: Optional[str] = None
    financial_provisions: Optional[str] = None
    penalties_provisions: Optional[str] = None
    extraction_status: str = "pending"  # "success" | "ocr_required" | "failed"
    language: str = "English"
    page_count: Optional[int] = None
    character_count: int = 0
    word_count: int = 0
    provenance: dict[str, str] = field(default_factory=dict)
    economic_profile: Optional[Any] = None  # StateBillEconomicProfile
    corporate_exposures: list[Any] = field(default_factory=list)  # list[StateCorporateExposure]
    impact_assessment: Optional[Any] = None  # StateImpactAssessment
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize StateBillKnowledge to a JSON-compatible dictionary."""
        summary_dict = (
            self.summary.to_dict()
            if isinstance(self.summary, StateBillSummary)
            else self.summary
        )
        econ_dict = None
        if self.economic_profile is not None:
            econ_dict = (
                self.economic_profile.to_dict()
                if hasattr(self.economic_profile, "to_dict")
                else self.economic_profile
            )

        res: dict[str, Any] = {
            "bill_id": self.bill_id,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "title": self.title,
            "bill_number": self.bill_number,
            "chamber": self.chamber,
            "status": self.status,
            "source_url": self.source_url,
            "policy_category": self.policy_category,
            "category_provenance": self.category_provenance,
            "year": self.year,
            "introduction_date": self.introduction_date,
            "assent_date": self.assent_date,
            "pdf_url": self.pdf_url,
            "corpus_path": self.corpus_path,
            "document_hash": self.document_hash,
            "summary": summary_dict,
            "objective": self.objective,
            "key_provisions": self.key_provisions,
            "amended_acts": self.amended_acts,
            "affected_stakeholders": self.affected_stakeholders,
            "administrative_authority": self.administrative_authority,
            "financial_provisions": self.financial_provisions,
            "penalties_provisions": self.penalties_provisions,
            "extraction_status": self.extraction_status,
            "language": self.language,
            "page_count": self.page_count,
            "character_count": self.character_count,
            "word_count": self.word_count,
            "provenance": self.provenance,
            "created_at": self.created_at,
        }
        if econ_dict is not None:
            res["economic_profile"] = econ_dict
        if self.corporate_exposures:
            res["corporate_exposures"] = [
                e.to_dict() if hasattr(e, "to_dict") else e
                for e in self.corporate_exposures
            ]
        if self.impact_assessment is not None:
            res["impact_assessment"] = (
                self.impact_assessment.to_dict()
                if hasattr(self.impact_assessment, "to_dict")
                else self.impact_assessment
            )
        return res

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateBillKnowledge":
        """Deserialize StateBillKnowledge from a dictionary."""
        from schemas.state_economic_profile import StateBillEconomicProfile
        from schemas.state_corporate_exposure import StateCorporateExposure
        from schemas.state_impact_assessment import StateImpactAssessment

        summary_raw = data.get("summary", {})
        if isinstance(summary_raw, dict):
            summary = StateBillSummary.from_dict(summary_raw)
        elif isinstance(summary_raw, StateBillSummary):
            summary = summary_raw
        else:
            summary = StateBillSummary()

        econ_raw = data.get("economic_profile")
        if isinstance(econ_raw, dict):
            economic_profile = StateBillEconomicProfile.from_dict(econ_raw)
        elif isinstance(econ_raw, StateBillEconomicProfile):
            economic_profile = econ_raw
        else:
            economic_profile = None

        corp_exps = []
        for exp_raw in data.get("corporate_exposures", []):
            if isinstance(exp_raw, dict):
                corp_exps.append(StateCorporateExposure.from_dict(exp_raw))
            elif isinstance(exp_raw, StateCorporateExposure):
                corp_exps.append(exp_raw)

        impact_raw = data.get("impact_assessment")
        if isinstance(impact_raw, dict):
            impact_assessment = StateImpactAssessment.from_dict(impact_raw)
        elif isinstance(impact_raw, StateImpactAssessment):
            impact_assessment = impact_raw
        else:
            impact_assessment = None

        return cls(
            bill_id=data["bill_id"],
            jurisdiction=data.get("jurisdiction", "state"),
            state=data.get("state", ""),
            title=data.get("title", ""),
            bill_number=data.get("bill_number", ""),
            chamber=data.get("chamber", ""),
            status=data.get("status", ""),
            source_url=data.get("source_url", ""),
            policy_category=data.get("policy_category", "Other / Unclassified"),
            category_provenance=data.get("category_provenance", "SYSTEM_DERIVED"),
            year=data.get("year"),
            introduction_date=data.get("introduction_date"),
            assent_date=data.get("assent_date"),
            pdf_url=data.get("pdf_url"),
            corpus_path=data.get("corpus_path"),
            document_hash=data.get("document_hash"),
            summary=summary,
            objective=data.get("objective"),
            key_provisions=data.get("key_provisions", []),
            amended_acts=data.get("amended_acts", []),
            affected_stakeholders=data.get("affected_stakeholders", []),
            administrative_authority=data.get("administrative_authority"),
            financial_provisions=data.get("financial_provisions"),
            penalties_provisions=data.get("penalties_provisions"),
            extraction_status=data.get("extraction_status", "pending"),
            language=data.get("language", "English"),
            page_count=data.get("page_count"),
            character_count=data.get("character_count", 0),
            word_count=data.get("word_count", 0),
            provenance=data.get("provenance", {}),
            economic_profile=economic_profile,
            corporate_exposures=corp_exps,
            impact_assessment=impact_assessment,
            created_at=data.get(
                "created_at", datetime.now(timezone.utc).isoformat()
            ),
        )

    def __repr__(self) -> str:
        return (
            f"<StateBillKnowledge bill_id={self.bill_id!r} state={self.state!r} "
            f"category={self.policy_category!r} extraction_status={self.extraction_status!r}>"
        )
