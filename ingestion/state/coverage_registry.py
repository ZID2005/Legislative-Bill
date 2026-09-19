"""
ingestion/state/coverage_registry.py
====================================
28-State Coverage and Readiness Registry for India Legislative Platform.

Tracks legislative source feasibility, adapter implementation status,
corpus counts, and document capability across all 28 Indian States.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from utils.file_utils import ensure_dir, save_json
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)

_DEFAULT_REGISTRY_PATH = settings.STATE_BILLS_DIR / "state_coverage_registry.json"


class CoverageStatus(str, Enum):
    """Explicit coverage and implementation statuses for Indian States."""

    IMPLEMENTED = "IMPLEMENTED"
    PILOT = "PILOT"
    RESEARCHED = "RESEARCHED"
    READY_FOR_ADAPTER = "READY_FOR_ADAPTER"
    SOURCE_FOUND = "SOURCE_FOUND"
    SOURCE_LIMITED = "SOURCE_LIMITED"
    NOT_YET_VALIDATED = "NOT_YET_VALIDATED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class StateCoverageRecord:
    """Readiness and coverage audit record for a single Indian State."""

    state: str
    legislative_source: str
    source_status: str
    source_type: str
    authority: str
    adapter_status: CoverageStatus
    ingestion_status: str
    bill_count: int = 0
    pdf_count: int = 0
    corpus_count: int = 0
    knowledge_count: int = 0
    language_support: list[str] = field(default_factory=lambda: ["English"])
    search_support: bool = False
    provenance_support: bool = False
    feasibility: str = "HIGH"  # "HIGH" | "MEDIUM" | "LOW"
    notes: str = ""
    last_verified: str = "2026-09-07"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["adapter_status"] = self.adapter_status.value if isinstance(self.adapter_status, CoverageStatus) else str(self.adapter_status)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateCoverageRecord":
        status_val = data.get("adapter_status", CoverageStatus.NOT_YET_VALIDATED.value)
        try:
            status = CoverageStatus(status_val)
        except ValueError:
            status = CoverageStatus.NOT_YET_VALIDATED

        return cls(
            state=data["state"],
            legislative_source=data.get("legislative_source", ""),
            source_status=data.get("source_status", "UNKNOWN"),
            source_type=data.get("source_type", "portal"),
            authority=data.get("authority", "UNAVAILABLE"),
            adapter_status=status,
            ingestion_status=data.get("ingestion_status", "NOT_STARTED"),
            bill_count=data.get("bill_count", 0),
            pdf_count=data.get("pdf_count", 0),
            corpus_count=data.get("corpus_count", 0),
            knowledge_count=data.get("knowledge_count", 0),
            language_support=data.get("language_support", ["English"]),
            search_support=data.get("search_support", False),
            provenance_support=data.get("provenance_support", False),
            feasibility=data.get("feasibility", "MEDIUM"),
            notes=data.get("notes", ""),
            last_verified=data.get("last_verified", "2026-09-07"),
        )


class StateCoverageRegistry:
    """
    Registry managing coverage, readiness, and metrics for all 28 Indian States.
    """

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        self.registry_path = registry_path or _DEFAULT_REGISTRY_PATH
        self._states: dict[str, StateCoverageRecord] = {}
        self._load()

    def _load(self) -> None:
        """Load state coverage records from disk or initialize 28 states baseline."""
        if self.registry_path.is_file():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    rec = StateCoverageRecord.from_dict(item)
                    norm = (normalize_state(rec.state) or rec.state).lower()
                    self._states[norm] = rec
                logger.info("Loaded %d state coverage records from %s", len(self._states), self.registry_path)
                return
            except Exception as e:
                logger.error("Failed to load coverage registry from %s: %s", self.registry_path, e)

        self._initialize_baseline_28_states()

    def _initialize_baseline_28_states(self) -> None:
        """Initialize records for all 28 Indian States."""
        baseline_data: list[StateCoverageRecord] = [
            StateCoverageRecord(
                state="Andhra Pradesh",
                legislative_source="Andhra Pradesh Legislative Assembly (aplegislature.org)",
                source_status="ACTIVE",
                source_type="html_table",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.IMPLEMENTED,
                ingestion_status="PILOT_INGESTED",
                bill_count=12,
                pdf_count=12,
                corpus_count=12,
                knowledge_count=12,
                language_support=["English", "Telugu"],
                search_support=True,
                provenance_support=True,
                feasibility="HIGH",
                notes="Primary official portal operated by AP Legislature Secretariat.",
            ),
            StateCoverageRecord(
                state="Arunachal Pradesh",
                legislative_source="Arunachal Pradesh Legislative Assembly (arunachalassembly.gov.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_LIMITED,
                ingestion_status="NOT_STARTED",
                feasibility="LOW",
                notes="Limited digital bills repository; periodic PDF uploads.",
            ),
            StateCoverageRecord(
                state="Assam",
                legislative_source="Assam Legislative Assembly (assambidhansabha.org)",
                source_status="INACTIVE",
                source_type="session_list",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Bilingual English/Assamese; legislative business listed per session.",
            ),
            StateCoverageRecord(
                state="Bihar",
                legislative_source="Bihar Vidhan Sabha (vidhansabha.bih.nic.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Hindi-primary portal; session business papers accessible.",
            ),
            StateCoverageRecord(
                state="Chhattisgarh",
                legislative_source="Chhattisgarh Vidhan Sabha (cgvidhansabha.gov.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Session debates and bills in Hindi.",
            ),
            StateCoverageRecord(
                state="Goa",
                legislative_source="Goa Legislative Assembly (goavidhansabha.gov.in)",
                source_status="INACTIVE",
                source_type="session_list",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.READY_FOR_ADAPTER,
                ingestion_status="RESEARCHED",
                feasibility="HIGH",
                notes="English-first portal with clear session bills and acts listings.",
            ),
            StateCoverageRecord(
                state="Gujarat",
                legislative_source="Gujarat Legislative Assembly (gujaratassembly.gov.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Bilingual Gujarati/English legislative business.",
            ),
            StateCoverageRecord(
                state="Haryana",
                legislative_source="Haryana Vidhan Sabha (haryanaassembly.gov.in)",
                source_status="INACTIVE",
                source_type="session_list",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Bills and acts uploaded per session.",
            ),
            StateCoverageRecord(
                state="Himachal Pradesh",
                legislative_source="Himachal Pradesh Vidhan Sabha (hpvidhansabha.nic.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.RESEARCHED,
                ingestion_status="RESEARCHED",
                feasibility="MEDIUM",
                notes="Pioneer of eVidhan paperless initiative. Currently network connectivity timeouts observed.",
            ),
            StateCoverageRecord(
                state="Jharkhand",
                legislative_source="Jharkhand Vidhan Sabha (jharkhandvidhansabha.nic.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Session business and bills listed in Hindi.",
            ),
            StateCoverageRecord(
                state="Karnataka",
                legislative_source="Karnataka Legislative Assembly (kla.kar.nic.in)",
                source_status="ACTIVE",
                source_type="session_list",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.IMPLEMENTED,
                ingestion_status="PILOT_INGESTED",
                bill_count=11,
                pdf_count=11,
                corpus_count=11,
                knowledge_count=11,
                language_support=["English", "Kannada"],
                search_support=True,
                provenance_support=True,
                feasibility="HIGH",
                notes="Official NIC portal with session-wise bill listings and direct PDF downloads.",
            ),
            StateCoverageRecord(
                state="Kerala",
                legislative_source="Kerala Legislative Assembly (niyamasabha.nic.in)",
                source_status="ACTIVE",
                source_type="html_table",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.IMPLEMENTED,
                ingestion_status="PILOT_INGESTED",
                bill_count=11,
                pdf_count=11,
                corpus_count=11,
                knowledge_count=11,
                language_support=["English", "Malayalam"],
                search_support=True,
                provenance_support=True,
                feasibility="HIGH",
                notes="Official Niyamasabha portal with comprehensive bill tracking (Introduced, Passed, Assented).",
            ),
            StateCoverageRecord(
                state="Madhya Pradesh",
                legislative_source="Madhya Pradesh Vidhan Sabha (mpvidhansabha.nic.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Hindi-language legislative business.",
            ),
            StateCoverageRecord(
                state="Maharashtra",
                legislative_source="Maharashtra Legislature (mls.org.in)",
                source_status="INACTIVE",
                source_type="html_table",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.RESEARCHED,
                ingestion_status="RESEARCHED",
                feasibility="MEDIUM",
                notes="Bicameral legislature (MLS). Primary language Marathi with high translation overhead.",
            ),
            StateCoverageRecord(
                state="Manipur",
                legislative_source="Manipur Legislative Assembly (manipurassembly.nic.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_LIMITED,
                ingestion_status="NOT_STARTED",
                feasibility="LOW",
                notes="Intermittent updates on assembly portal.",
            ),
            StateCoverageRecord(
                state="Meghalaya",
                legislative_source="Meghalaya Legislative Assembly (megassembly.gov.in)",
                source_status="INACTIVE",
                source_type="session_list",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="English-language bills listed per session.",
            ),
            StateCoverageRecord(
                state="Mizoram",
                legislative_source="Mizoram Legislative Assembly (mizoramassembly.gov.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_LIMITED,
                ingestion_status="NOT_STARTED",
                feasibility="LOW",
                notes="Limited digital bills documentation.",
            ),
            StateCoverageRecord(
                state="Nagaland",
                legislative_source="Nagaland Legislative Assembly (nagaland.gov.in / nla)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_LIMITED,
                ingestion_status="NOT_STARTED",
                feasibility="LOW",
                notes="English-primary; limited structured bills archive.",
            ),
            StateCoverageRecord(
                state="Odisha",
                legislative_source="Odisha Legislative Assembly (odishaassembly.nic.in)",
                source_status="INACTIVE",
                source_type="session_list",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Odia and English legislative business.",
            ),
            StateCoverageRecord(
                state="Punjab",
                legislative_source="Punjab Vidhan Sabha (punjabassembly.nic.in)",
                source_status="INACTIVE",
                source_type="session_list",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Session bills and acts listed in Punjabi and English.",
            ),
            StateCoverageRecord(
                state="Rajasthan",
                legislative_source="Rajasthan Legislative Assembly (rajasthanassembly.nic.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.READY_FOR_ADAPTER,
                ingestion_status="RESEARCHED",
                feasibility="HIGH",
                notes="Well-structured session bills portal with PDF links.",
            ),
            StateCoverageRecord(
                state="Sikkim",
                legislative_source="Sikkim Legislative Assembly (sikkimassembly.gov.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_LIMITED,
                ingestion_status="NOT_STARTED",
                feasibility="LOW",
                notes="Limited historical bills digitized.",
            ),
            StateCoverageRecord(
                state="Tamil Nadu",
                legislative_source="Tamil Nadu Legislative Assembly (assembly.tn.gov.in)",
                source_status="INACTIVE",
                source_type="html_table",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.RESEARCHED,
                ingestion_status="RESEARCHED",
                feasibility="MEDIUM",
                notes="Digital repository (TNLAS) and Government Gazette archive. Tamil and English.",
            ),
            StateCoverageRecord(
                state="Telangana",
                legislative_source="Telangana Legislature (legislature.telangana.gov.in)",
                source_status="ACTIVE",
                source_type="html_table",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.IMPLEMENTED,
                ingestion_status="PILOT_INGESTED",
                bill_count=10,
                pdf_count=10,
                corpus_count=10,
                knowledge_count=10,
                language_support=["English", "Telugu", "Urdu"],
                search_support=True,
                provenance_support=True,
                feasibility="HIGH",
                notes="Official government portal with Assembly and Council legislative business.",
            ),
            StateCoverageRecord(
                state="Tripura",
                legislative_source="Tripura Legislative Assembly (tripuraassembly.nic.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_LIMITED,
                ingestion_status="NOT_STARTED",
                feasibility="LOW",
                notes="Limited structured digital documentation.",
            ),
            StateCoverageRecord(
                state="Uttar Pradesh",
                legislative_source="Uttar Pradesh Vidhan Sabha (upvidhansabhaproceedings.gov.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.READY_FOR_ADAPTER,
                ingestion_status="RESEARCHED",
                feasibility="HIGH",
                notes="Large volume bicameral legislature; session bills repository active.",
            ),
            StateCoverageRecord(
                state="Uttarakhand",
                legislative_source="Uttarakhand Vidhan Sabha (vidhansabha.uk.gov.in)",
                source_status="INACTIVE",
                source_type="portal",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Hindi-language session business.",
            ),
            StateCoverageRecord(
                state="West Bengal",
                legislative_source="West Bengal Legislative Assembly (wbassembly.gov.in)",
                source_status="INACTIVE",
                source_type="session_list",
                authority="AUTHORITATIVE",
                adapter_status=CoverageStatus.SOURCE_FOUND,
                ingestion_status="NOT_STARTED",
                feasibility="MEDIUM",
                notes="Session bills published in English and Bengali.",
            ),
        ]

        for rec in baseline_data:
            norm = (normalize_state(rec.state) or rec.state).lower()
            self._states[norm] = rec

        self.save()

    def save(self) -> None:
        """Persist registry to disk."""
        ensure_dir(self.registry_path.parent)
        data = [r.to_dict() for r in self.get_all_states()]
        save_json(data, self.registry_path)
        logger.info("Saved 28-State coverage registry to %s", self.registry_path)

    def get_state(self, state: str) -> Optional[StateCoverageRecord]:
        """Get record by state name or alias."""
        norm = (normalize_state(state) or state).lower()
        return self._states.get(norm)

    def get_all_states(self) -> list[StateCoverageRecord]:
        """Return all 28 State records sorted by state name."""
        return sorted(self._states.values(), key=lambda x: x.state)

    def update_metrics(
        self,
        state: str,
        bill_count: Optional[int] = None,
        pdf_count: Optional[int] = None,
        corpus_count: Optional[int] = None,
        knowledge_count: Optional[int] = None,
    ) -> None:
        """Update bill, pdf, corpus, and knowledge counts for a state."""
        rec = self.get_state(state)
        if not rec:
            return
        if bill_count is not None:
            rec.bill_count = bill_count
        if pdf_count is not None:
            rec.pdf_count = pdf_count
        if corpus_count is not None:
            rec.corpus_count = corpus_count
        if knowledge_count is not None:
            rec.knowledge_count = knowledge_count
        self.save()

    def get_summary_statistics(self) -> dict[str, Any]:
        """Compute readiness and coverage summary statistics across all 28 states."""
        all_recs = self.get_all_states()
        status_counts: dict[str, int] = {}
        total_bills = sum(r.bill_count for r in all_recs)
        total_pdfs = sum(r.pdf_count for r in all_recs)
        total_knowledge = sum(r.knowledge_count for r in all_recs)

        for r in all_recs:
            st = r.adapter_status.value
            status_counts[st] = status_counts.get(st, 0) + 1

        implemented_states = [r.state for r in all_recs if r.adapter_status == CoverageStatus.IMPLEMENTED]

        return {
            "total_states": len(all_recs),
            "implemented_count": len(implemented_states),
            "implemented_states": implemented_states,
            "status_distribution": status_counts,
            "total_state_bills": total_bills,
            "total_state_pdfs": total_pdfs,
            "total_state_knowledge_records": total_knowledge,
        }
