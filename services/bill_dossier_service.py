"""
services/bill_dossier_service.py
================================
Task 8.27 — Legislative Intelligence Enrichment & Bill Dossier 2.0.

Core orchestration service that synthesizes:
- Bill Identity & Status (Central, State, and Live Knowledge)
- Chronological Evidence-Based Timeline (Phase 3)
- Structured 'What Changed?' View (Phase 4)
- Plain-Language Non-Expert Explanations (Phase 5)
- Multi-Persona Factual Stakeholder Perspectives (Phase 6)
- Macro Sector Directory & Industry Mappings (Phase 7)
- Corporate Intelligence Connections & Linkage Reasons (Phase 8)
- Model Status Firewall & Clear Epistemic Labelling (Phase 9)
- Document Viewer Metadata & SHA-256 Provenance (Phase 10)
- Grounded AI Explanations with Strict Separation (Phases 12 & 13)

Strict Invariants:
1. Zero stock predictions generated for State bills or live knowledge bills.
2. Fact, Interpretation, and Prediction remain strictly separated.
3. No buy/sell/hold investment recommendations or ranking of stakeholders.
4. Historical records preserved without overwrite.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.bill_dossier import (
    BillChangeSummary,
    BillDocumentItem,
    DocumentChangeDetail,
    DossierContent,
    DossierIdentity,
    DossierImpactContext,
    DossierProvenance,
    DossierStatus,
    EnrichedBillDossier,
    ExposureType,
    LegislativeChangeDetail,
    LinkedCompanyExposureItem,
    ModelStatus,
    PlainLanguageExplanation,
    SectorExposureItem,
    StakeholderPersona,
    StakeholderPersonaView,
    TimelineEvent,
    TimelineStage,
)
from schemas.monitoring import LiveKnowledgeRecord
from schemas.unified_bill_record import UnifiedBillRecord
from services.company_intelligence_service import (
    CompanyIntelligenceService,
    _CENTRAL_QUANTITATIVE_ISINS,
)
from services.industry_intelligence_service import IndustryIntelligenceService
from services.monitoring.source_url_validator import SourceURLValidator
from services.unified_legislative_discovery import (
    _CENTRAL_NON_LEGISLATIVE_IDS,
    UnifiedLegislativeDiscoveryService,
)
from storage.knowledge_repository import KnowledgeRepository
from storage.live_knowledge_repository import LiveKnowledgeRepository
from storage.monitoring_repository import MonitoringRepository
from storage.state_knowledge_repository import StateKnowledgeRepository

logger = get_logger(__name__)

# Expected size of the frozen Central production set (docs/production_baseline.json).
_EXPECTED_CENTRAL_PRODUCTION_BILLS = 20


@lru_cache(maxsize=1)
def get_frozen_central_production_bill_ids() -> frozenset[str]:
    """
    Derive the frozen Central production bill IDs from the authoritative
    metadata store (``data/bills/metadata``) minus the auxiliary records.

    Fail-safe: if metadata is unavailable the set is empty, so no bill is
    ever over-claimed as MODELLED.
    """
    metadata_dir = Path(settings.BILLS_DIR) / "metadata"
    ids: set[str] = set()
    if metadata_dir.is_dir():
        for path in metadata_dir.glob("*.json"):
            try:
                bill_id = json.loads(path.read_text(encoding="utf-8")).get("bill_id") or path.stem
            except (OSError, ValueError):
                bill_id = path.stem
            ids.add(str(bill_id).strip())
    production = frozenset(ids - set(_CENTRAL_NON_LEGISLATIVE_IDS))
    if len(production) != _EXPECTED_CENTRAL_PRODUCTION_BILLS:
        logger.warning(
            "Frozen Central production set size mismatch | expected=%d actual=%d dir=%s",
            _EXPECTED_CENTRAL_PRODUCTION_BILLS,
            len(production),
            metadata_dir,
        )
    return production


class BillDossierService:
    """
    High-level intelligence orchestration service constructing Enriched Bill Dossiers.
    """

    def __init__(
        self,
        discovery_service: Optional[UnifiedLegislativeDiscoveryService] = None,
        company_intel_service: Optional[CompanyIntelligenceService] = None,
        industry_service: Optional[IndustryIntelligenceService] = None,
        live_knowledge_repo: Optional[LiveKnowledgeRepository] = None,
        monitoring_repo: Optional[MonitoringRepository] = None,
        central_knowledge_repo: Optional[KnowledgeRepository] = None,
        state_knowledge_repo: Optional[StateKnowledgeRepository] = None,
        url_validator: Optional[SourceURLValidator] = None,
    ) -> None:
        self.discovery_service = discovery_service or UnifiedLegislativeDiscoveryService()
        self.company_intel_service = company_intel_service or CompanyIntelligenceService()
        self.industry_service = industry_service or IndustryIntelligenceService()
        storage_path = Path(getattr(settings, "storage_path", "storage"))
        self.live_knowledge_repo = live_knowledge_repo or LiveKnowledgeRepository(storage_dir=storage_path)
        self.monitoring_repo = monitoring_repo or MonitoringRepository()
        self.central_knowledge_repo = central_knowledge_repo or KnowledgeRepository()
        self.state_knowledge_repo = state_knowledge_repo or StateKnowledgeRepository()
        self.url_validator = url_validator or SourceURLValidator()

    # ------------------------------------------------------------------
    # Bill Record Resolution
    # ------------------------------------------------------------------

    def resolve_bill(self, bill_id: str) -> Optional[UnifiedBillRecord]:
        """
        Resolve a bill by ID across Central, State, and Live Knowledge stores.
        """
        clean_id = bill_id.strip()

        # 1. Check Unified Discovery (Central + State catalog)
        rec = self.discovery_service.get_bill_by_id(clean_id)
        if rec:
            return rec

        # 2. Check Live Knowledge Base
        live_rec = (
            self.live_knowledge_repo.get(clean_id)
            or self.live_knowledge_repo.get_by_canonical_bill_id(clean_id)
            or self.live_knowledge_repo.get_by_bill_number(clean_id)
        )
        if live_rec:
            return self._live_record_to_unified(live_rec)

        return None

    def _live_record_to_unified(self, lr: LiveKnowledgeRecord) -> UnifiedBillRecord:
        """Convert a LiveKnowledgeRecord into UnifiedBillRecord with firewall intact."""
        is_central = lr.jurisdiction.lower() == "central"
        prov = {
            "title": "AUTHORITATIVE_SOURCE",
            "bill_number": "AUTHORITATIVE_SOURCE" if lr.bill_number else "UNAVAILABLE",
            "jurisdiction": "AUTHORITATIVE_SOURCE",
            "status": "LIVE_DISCOVERY",
            "source_category": lr.source_category,
            "authority_name": lr.authority_name or "Official Portal",
        }
        return UnifiedBillRecord(
            bill_id=lr.canonical_bill_id or lr.record_id,
            jurisdiction=lr.jurisdiction,
            state=lr.state,
            title=lr.title,
            short_title=lr.short_title or lr.title,
            bill_number=lr.bill_number,
            legislature=lr.authority_name or ("Parliament of India" if is_central else f"{lr.state} Legislature"),
            house="Parliament" if is_central else (f"{lr.state} Assembly" if lr.state else "Assembly"),
            session=None,
            ministry=None,
            year=datetime.now(timezone.utc).year,
            introduction_date=lr.introduction_date,
            passage_date=None,
            assent_date=lr.assent_date,
            status=lr.bill_status_text or lr.live_status,
            policy_domain="General Legislative",
            economic_sectors=lr.tags or ["General"],
            secondary_sectors=[],
            stakeholders=["General Public", "Regulated Industry"],
            summary=lr.summary or f"Live legislative discovery recorded from {lr.authority_name or 'official source'}.",
            company_exposure_count=0,
            listed_company_exposure_count=0,
            market_relevance="LOW",
            modeling_eligibility="NOT_ELIGIBLE",  # Live bills NEVER eligible automatically
            data_sufficiency="PARTIAL",
            source_url=lr.source_url,
            pdf_url=lr.document_url,
            source_type=lr.source_category,
            data_quality="LIVE_DISCOVERED",
            provenance=prov,
            created_at=lr.discovered_at,
        )

    # ------------------------------------------------------------------
    # Phase 9: Model Status & Firewall Classification
    # ------------------------------------------------------------------

    def get_model_status_info(self, bill: UnifiedBillRecord) -> tuple[str, str, str, bool]:
        """
        Determine exact model status, label, explanation, and prediction availability.

        Returns: (model_status, label, description, prediction_available)
        """
        clean_id = bill.bill_id.strip()

        # Invariant: State bills NEVER have stock predictions
        if bill.is_state:
            return (
                ModelStatus.NOT_ELIGIBLE.value,
                "NOT ELIGIBLE FOR STOCK MODEL",
                "State assembly legislation is strictly isolated from Central stock market models. "
                "Quantitative stock predictions remain exactly 0.",
                False,
            )

        # Central non-legislative bills
        if clean_id in _CENTRAL_NON_LEGISLATIVE_IDS:
            return (
                ModelStatus.NOT_ELIGIBLE.value,
                "NOT ELIGIBLE FOR STOCK MODEL",
                "Non-legislative auxiliary record; excluded from quantitative predictive models.",
                False,
            )

        # Frozen Central 20 Production Bills
        if bill.is_central and clean_id in get_frozen_central_production_bill_ids():
            return (
                ModelStatus.MODELLED.value,
                "MODELLED — CENTRAL QUANTITATIVE",
                "Validated production bill in the frozen analytical dataset (20 bills / 47 companies / 940 pairs).",
                True,
            )

        # Other Central Bills or Live Discoveries
        # Check if stored as KNOWLEDGE_ONLY in live repository
        live_rec = (
            self.live_knowledge_repo.get(clean_id)
            or self.live_knowledge_repo.get_by_canonical_bill_id(clean_id)
        )
        if live_rec:
            ams = live_rec.analytical_model_status or ModelStatus.KNOWLEDGE_ONLY.value
            if ams == ModelStatus.PENDING_REVIEW.value:
                return (
                    ModelStatus.PENDING_REVIEW.value,
                    "LIVE — PENDING REVIEW",
                    "Newly discovered legislative measure queued for analytical methodology review.",
                    False,
                )
            return (
                ModelStatus.KNOWLEDGE_ONLY.value,
                "LIVE — KNOWLEDGE ONLY",
                "Live legislative intelligence record. Strictly firewalled from quantitative stock predictions.",
                False,
            )

        return (
            ModelStatus.KNOWLEDGE_ONLY.value,
            "LIVE — KNOWLEDGE ONLY",
            "Legislative intelligence record maintained for qualitative statutory analysis.",
            False,
        )

    # ------------------------------------------------------------------
    # Phase 3: Chronological Evidence-Based Timeline
    # ------------------------------------------------------------------

    def build_timeline(self, bill: UnifiedBillRecord) -> list[TimelineEvent]:
        """
        Build chronological timeline of meaningful events supported strictly by evidence.
        Never infers future or undocumented stages.
        """
        events: list[TimelineEvent] = []
        norm_status = (bill.status or "").lower()

        # 1. DISCOVERED
        # Only if recorded timestamp exists
        if bill.created_at:
            events.append(
                TimelineEvent(
                    event_id=f"{bill.bill_id}_discovered",
                    stage=TimelineStage.DISCOVERED.value,
                    stage_label="Legislative Record Discovered",
                    date=bill.created_at[:10] if len(bill.created_at) >= 10 else None,
                    source_authority=bill.legislature or "Authoritative Source",
                    description=f"Legislative measure ingested and indexed from {bill.source_type or 'official repository'}.",
                    evidence_type="FACT",
                    document_url=bill.source_url,
                    chamber=bill.house,
                    verified=True,
                )
            )

        # 2. INTRODUCED
        if bill.introduction_date:
            events.append(
                TimelineEvent(
                    event_id=f"{bill.bill_id}_introduced",
                    stage=TimelineStage.INTRODUCED.value,
                    stage_label="Tabled & Formally Introduced",
                    date=bill.introduction_date,
                    source_authority=bill.legislature or "Legislative House",
                    description=f"Bill formally tabled in {bill.house or 'Legislature'}.",
                    evidence_type="FACT",
                    document_url=bill.pdf_url or bill.source_url,
                    chamber=bill.house,
                    verified=True,
                )
            )

        # 3. REFERRED / COMMITTEE REVIEW (if supported by status text or knowledge)
        if "referred" in norm_status or "select committee" in norm_status or "standing committee" in norm_status:
            events.append(
                TimelineEvent(
                    event_id=f"{bill.bill_id}_committee",
                    stage=TimelineStage.COMMITTEE_REVIEW.value,
                    stage_label="Referred to Parliamentary / Assembly Committee",
                    date=None,  # Do not invent unverified committee date
                    source_authority=bill.legislature,
                    description="Bill referred for detailed committee scrutiny and stakeholder examination.",
                    evidence_type="OFFICIAL_RECORD",
                    document_url=bill.source_url,
                    chamber=bill.house,
                    verified=True,
                )
            )

        # 4. PASSED
        # If passed one chamber or both
        is_passed = any(
            p in norm_status
            for p in ["passed", "passed_lok_sabha", "passed_rajya_sabha", "passed_both", "assented", "enacted"]
        )
        if is_passed:
            chamber_pass_desc = "Passed by Legislature"
            if "passed_lok_sabha" in norm_status:
                chamber_pass_desc = "Passed by Lok Sabha (Lower House)"
            elif "passed_rajya_sabha" in norm_status:
                chamber_pass_desc = "Passed by Rajya Sabha (Upper House)"
            elif "passed_both" in norm_status or "assented" in norm_status or "enacted" in norm_status:
                chamber_pass_desc = "Passed by Both Legislative Chambers"

            events.append(
                TimelineEvent(
                    event_id=f"{bill.bill_id}_passed",
                    stage=TimelineStage.PASSED.value,
                    stage_label="Legislative Passage",
                    date=bill.passage_date,
                    source_authority=bill.legislature,
                    description=chamber_pass_desc,
                    evidence_type="FACT" if bill.passage_date else "OFFICIAL_RECORD",
                    document_url=bill.source_url,
                    chamber=bill.house,
                    verified=True,
                )
            )

        # 5. ASSENT
        # Governor or President
        if bill.assent_date or "assented" in norm_status or "enacted" in norm_status:
            authority = "Governor Assent" if bill.is_state else "Presidential Assent"
            events.append(
                TimelineEvent(
                    event_id=f"{bill.bill_id}_assent",
                    stage=TimelineStage.ASSENT.value,
                    stage_label=f"Constitutional Assent ({authority})",
                    date=bill.assent_date,
                    source_authority=f"Head of State ({authority})",
                    description=f"Formal constitutional assent granted to the enacted statute.",
                    evidence_type="FACT" if bill.assent_date else "OFFICIAL_RECORD",
                    document_url=bill.pdf_url or bill.source_url,
                    chamber=None,
                    verified=True,
                )
            )

        # 6. NOTIFIED (Gazette)
        if "notified" in norm_status or "enacted" in norm_status:
            events.append(
                TimelineEvent(
                    event_id=f"{bill.bill_id}_notified",
                    stage=TimelineStage.NOTIFIED.value,
                    stage_label="Official Gazette Notification",
                    date=None,
                    source_authority="Official Gazette of India / State Gazette",
                    description="Statute published in the Official Gazette for public commencement.",
                    evidence_type="OFFICIAL_RECORD",
                    document_url=bill.pdf_url,
                    chamber=None,
                    verified=True,
                )
            )

        # 7. WITHDRAWN / SUPERSEDED
        if "withdrawn" in norm_status or "lapsed" in norm_status:
            events.append(
                TimelineEvent(
                    event_id=f"{bill.bill_id}_withdrawn",
                    stage=TimelineStage.WITHDRAWN.value,
                    stage_label="Withdrawn / Lapsed",
                    date=None,
                    source_authority=bill.legislature,
                    description="Measure formally withdrawn or lapsed by parliamentary procedure.",
                    evidence_type="OFFICIAL_RECORD",
                    document_url=bill.source_url,
                    chamber=bill.house,
                    verified=True,
                )
            )
        elif "superseded" in norm_status:
            events.append(
                TimelineEvent(
                    event_id=f"{bill.bill_id}_superseded",
                    stage=TimelineStage.SUPERSEDED.value,
                    stage_label="Superseded by Newer Measure",
                    date=None,
                    source_authority=bill.legislature,
                    description="Provisions superseded by subsequent legislative measure.",
                    evidence_type="OFFICIAL_RECORD",
                    document_url=bill.source_url,
                    chamber=bill.house,
                    verified=True,
                )
            )

        # 8. Check monitoring change events for historical updates
        change_events = self.monitoring_repo.list_events(bill_id=bill.bill_id, limit=10)
        for ce in change_events:
            events.append(
                TimelineEvent(
                    event_id=ce.event_id,
                    stage=TimelineStage.UPDATED.value,
                    stage_label=f"Update Detected ({ce.event_type})",
                    date=ce.detected_at[:10] if ce.detected_at else None,
                    source_authority=ce.source_id or "Monitoring Pipeline",
                    description=f"Field '{ce.field_name}' updated from '{ce.old_value}' to '{ce.new_value}'.",
                    evidence_type="FACT",
                    document_url=ce.source_reference,
                    chamber=bill.house,
                    verified=True,
                )
            )

        # Sort chronologically by date where available; undated events append in logical sequence
        def _sort_key(ev: TimelineEvent) -> tuple[int, str]:
            if ev.date:
                return (1, ev.date)
            # Prioritize discovery -> intro -> committee -> pass -> assent -> notify
            stage_order = {
                TimelineStage.DISCOVERED.value: 10,
                TimelineStage.INTRODUCED.value: 20,
                TimelineStage.REFERRED.value: 30,
                TimelineStage.COMMITTEE_REVIEW.value: 40,
                TimelineStage.PASSED.value: 50,
                TimelineStage.ASSENT.value: 60,
                TimelineStage.NOTIFIED.value: 70,
                TimelineStage.UPDATED.value: 80,
                TimelineStage.SUPERSEDED.value: 90,
                TimelineStage.WITHDRAWN.value: 100,
            }
            return (0, str(stage_order.get(ev.stage, 99)))

        return sorted(events, key=_sort_key)

    # ------------------------------------------------------------------
    # Phase 4: "What Changed?" Structured Summary
    # ------------------------------------------------------------------

    def build_change_summary(self, bill: UnifiedBillRecord) -> BillChangeSummary:
        """
        Build structured change summary distinguishing DOCUMENT CHANGE from LEGISLATIVE STATUS CHANGE.
        """
        doc_changes: list[DocumentChangeDetail] = []
        leg_changes: list[LegislativeChangeDetail] = []

        # Pull recorded events from MonitoringRepository
        events = self.monitoring_repo.list_events(bill_id=bill.bill_id, limit=50)
        for ev in events:
            ev_type_str = ev.event_type.value if hasattr(ev.event_type, "value") else str(ev.event_type)
            if ev_type_str in ("DOCUMENT_CHANGED", "METADATA_CHANGED") and "pdf" in (ev.field_name or "").lower():
                doc_changes.append(
                    DocumentChangeDetail(
                        document_url=str(ev.new_value or bill.pdf_url or ""),
                        previous_hash=str(ev.old_value) if "hash" in (ev.field_name or "") else None,
                        new_hash=str(ev.new_value) if "hash" in (ev.field_name or "") else None,
                        detected_at=ev.detected_at,
                        change_type="DOCUMENT_CONTENT_HASH_CHANGE" if "hash" in (ev.field_name or "") else "DOCUMENT_URL_UPDATED",
                        notes="Official document binary or link updated; verified independently from procedural stage.",
                    )
                )
            elif ev_type_str in ("STATUS_CHANGED", "DATE_CHANGED", "NEW_BILL"):
                leg_changes.append(
                    LegislativeChangeDetail(
                        field_name=ev.field_name or "status",
                        old_value=str(ev.old_value) if ev.old_value is not None else None,
                        new_value=str(ev.new_value) if ev.new_value is not None else None,
                        detected_at=ev.detected_at,
                        source_authority=ev.source_id or bill.legislature,
                        change_type="LEGISLATIVE_STATUS_CHANGE",
                        description=f"Legislative attribute '{ev.field_name}' transitioned.",
                    )
                )

        # Check Live Knowledge store for duplicate discoveries or document hash diffs
        live_rec = (
            self.live_knowledge_repo.get(bill.bill_id)
            or self.live_knowledge_repo.get_by_canonical_bill_id(bill.bill_id)
        )
        if live_rec and live_rec.document_hash_sha256:
            # Document is tracked with SHA-256
            pass

        has_changes = (len(doc_changes) + len(leg_changes)) > 0
        total_changes = len(doc_changes) + len(leg_changes)
        last_dt = None
        if events:
            last_dt = events[0].detected_at

        if not has_changes:
            summary_text = (
                f"Baseline version active for '{bill.short_title or bill.title}'. "
                "No subsequent revisions, amendments, or document hash changes have been officially detected."
            )
        else:
            summary_text = (
                f"{len(leg_changes)} legislative procedural changes and {len(doc_changes)} "
                "document metadata updates detected across official monitoring runs."
            )

        return BillChangeSummary(
            has_changes=has_changes,
            total_changes=total_changes,
            last_change_detected_at=last_dt,
            document_changes=doc_changes,
            legislative_changes=leg_changes,
            summary_text=summary_text,
        )

    # ------------------------------------------------------------------
    # Phase 5: Plain-Language Explanation
    # ------------------------------------------------------------------

    def build_plain_language_explanation(
        self,
        bill: UnifiedBillRecord,
        provisions: list[str],
        knowledge_obj: Optional[Any] = None,
    ) -> PlainLanguageExplanation:
        """
        Build plain-language explanation structured into 5 non-expert questions.
        """
        sectors_str = ", ".join(bill.economic_sectors) if bill.economic_sectors else "National Economy"
        jurisdiction_label = "Central Parliament" if bill.is_central else f"{bill.state} State Legislature"

        # 1. WHAT IS THIS BILL?
        what_is = (
            bill.summary
            if bill.summary and len(bill.summary) > 40
            else f"The {bill.title} is an official legislative measure introduced in {jurisdiction_label} "
                 f"to establish statutory governance and regulatory oversight over {sectors_str}."
        )

        # 2. WHAT DOES IT CHANGE?
        if provisions:
            key_pts = [f"• {p.strip()}" for p in provisions[:4]]
            what_changes = "Key statutory changes documented in the official text include:\n" + "\n".join(key_pts)
        elif knowledge_obj and getattr(knowledge_obj, "key_provisions", None):
            key_pts = [f"• {p.strip()}" for p in knowledge_obj.key_provisions[:4]]
            what_changes = "Key statutory provisions include:\n" + "\n".join(key_pts)
        else:
            what_changes = (
                f"Defines regulatory standards, administrative oversight, and statutory obligations "
                f"applicable across entities operating in {sectors_str}."
            )

        # 3. WHO COULD BE AFFECTED?
        who_affected = (
            f"Enterprises and organizations operating in {sectors_str}, supervisory regulatory authorities, "
            f"contractual vendors, and citizens interacting with related services."
        )
        if bill.stakeholders:
            who_affected += f" Specifically touches: {', '.join(bill.stakeholders)}."

        # 4. WHY COULD IT MATTER ECONOMICALLY?
        why_matter = (
            f"Economic significance stems from documented regulatory compliance mandates, structural governance reforms, "
            f"and institutional enforcement procedures in {sectors_str}. These statutory mechanisms can shift operational overhead, "
            f"contractual certainty, and investment planning across exposed business activities without presenting speculative stock forecasts."
        )

        # 5. WHAT IS STILL UNKNOWN?
        unknowns = []
        if not bill.assent_date and bill.status != "enacted":
            unknowns.append("Date of final constitutional assent or enactment")
        if not bill.passage_date:
            unknowns.append("Specific date of second-chamber or floor voting")
        unknowns.append("Subordinate procedural rules and delegated executive notifications to be framed post-enactment")
        what_unknown = (
            "Statutory items remaining to be officially notified include: "
            + "; ".join(unknowns) + "."
        )

        sources = []
        if bill.source_url:
            sources.append(bill.source_url)
        if bill.pdf_url:
            sources.append(bill.pdf_url)
        if not sources:
            sources.append(bill.legislature or "Official Parliamentary Records")

        return PlainLanguageExplanation(
            what_is_this_bill=what_is,
            what_does_it_change=what_changes,
            who_could_be_affected=who_affected,
            why_could_it_matter_economically=why_matter,
            what_is_still_unknown=what_unknown,
            grounded_sources=sources,
            epistemic_level="INTERPRETATION",
        )

    # ------------------------------------------------------------------
    # Phase 6: Stakeholder Perspectives
    # ------------------------------------------------------------------

    def build_stakeholder_views(
        self,
        bill: UnifiedBillRecord,
        is_modelled: bool,
    ) -> dict[str, StakeholderPersonaView]:
        """
        Build factual stakeholder perspectives across 5 standard personas.
        Never provides Buy/Sell/Hold or investment recommendations.
        """
        sectors_str = ", ".join(bill.economic_sectors) if bill.economic_sectors else "General Economy"
        leg_str = bill.legislature or ("Parliament of India" if bill.is_central else f"{bill.state} Assembly")

        # Prediction statement
        if is_modelled:
            pred_text = "Central quantitative model provides event-horizon return and anticipation telemetry across exposed securities."
        else:
            pred_text = "Quantitative stock prediction is NOT AVAILABLE under project invariants (non-modelled or State bill)."

        views: dict[str, StakeholderPersonaView] = {
            StakeholderPersona.INVESTOR.value: StakeholderPersonaView(
                persona=StakeholderPersona.INVESTOR.value,
                persona_title="Investor",
                icon="💼",
                fact=f"Statutory measure '{bill.short_title or bill.title}' tabled in {leg_str} under status '{bill.status}'.",
                interpretation=(
                    f"Assesses statutory compliance burdens, corporate governance shifts, and capital expenditure mandates across "
                    f"{sectors_str}. Focuses on operational headroom and regulatory risk premiums without speculative recommendations."
                ),
                prediction=pred_text,
                caveats="Factual legislative analysis only. Does NOT provide Buy, Sell, Hold, or investment recommendations.",
            ),
            StakeholderPersona.BUSINESS_OWNER.value: StakeholderPersonaView(
                persona=StakeholderPersona.BUSINESS_OWNER.value,
                persona_title="Business Owner",
                icon="🏢",
                fact=f"Supervisory framework governing {sectors_str} with enforcement jurisdiction under {bill.ministry or leg_str}.",
                interpretation=(
                    "Direct enterprise adaptation required for statutory filings, supervisory inspections, "
                    "contract revisions, and compliance documentation. Requires review of institutional thresholds."
                ),
                prediction="Operating cash-flow and administrative overhead sensitivity governed by statutory enforcement timelines.",
                caveats="Factual operational guidance; consult legal and compliance counsel for statutory enforcement.",
            ),
            StakeholderPersona.EMPLOYEE_PROFESSIONAL.value: StakeholderPersonaView(
                persona=StakeholderPersona.EMPLOYEE_PROFESSIONAL.value,
                persona_title="Employee / Professional",
                icon="👷",
                fact=f"Governs statutory operating conditions, professional qualifications, and workplace guidelines in {sectors_str}.",
                interpretation=(
                    "Influences workforce compliance standards, occupational health/safety rules, "
                    "and professional certification requirements depending on statutory adoption."
                ),
                prediction="Labor elasticity and professional demand proxies apply; zero equity price implication.",
                caveats="Descriptive analysis of statutory workplace and professional standards.",
            ),
            StakeholderPersona.COMMON_CITIZEN.value: StakeholderPersonaView(
                persona=StakeholderPersona.COMMON_CITIZEN.value,
                persona_title="Common Citizen",
                icon="👥",
                fact=f"Enacted rules setting consumer transparency benchmarks and public rights in {sectors_str}.",
                interpretation=(
                    "Aims to enhance public service reliability, dispute redressal access, "
                    "and statutory protection standards across citizens and end consumers."
                ),
                prediction="Broad socioeconomic public utility effects; zero market asset pricing implication.",
                caveats="Summary of statutory rights and public impact.",
            ),
            StakeholderPersona.RESEARCHER.value: StakeholderPersonaView(
                persona=StakeholderPersona.RESEARCHER.value,
                persona_title="Researcher",
                icon="🔬",
                fact=f"Official bill text referenced under bill number '{bill.bill_number or 'Unassigned'}' in {leg_str}.",
                interpretation=(
                    "Provides structural data for legislative drafting comparison, constitutional competency review, "
                    "regulatory architecture design, and federal distribution of legislative powers."
                ),
                prediction="Academic and institutional comparative metrics; independent of capital market valuations.",
                caveats="Structured research context grounded in authoritative gazette and parliamentary records.",
            ),
        }

        return views

    # ------------------------------------------------------------------
    # Phase 7 & 8: Sector, Industry & Corporate Exposure
    # ------------------------------------------------------------------

    def build_sector_exposures(self, bill: UnifiedBillRecord) -> list[SectorExposureItem]:
        """
        Build sector exposure items connected to Macro Sector Directory.
        """
        items: list[SectorExposureItem] = []
        all_sectors = list(bill.economic_sectors)
        for sec in bill.secondary_sectors:
            if sec not in all_sectors:
                all_sectors.append(sec)

        if not all_sectors:
            all_sectors = ["General Legislative"]

        for idx, sec in enumerate(all_sectors):
            # Classify direct vs indirect based on primary vs secondary
            is_primary = idx == 0
            exp_type = ExposureType.DIRECT.value if is_primary else ExposureType.INDIRECT.value

            # Query related industries from IndustryIntelligenceService
            try:
                inds = self.industry_service.list_industries(sector=sec)
                ind_names = [i.name for i in inds[:5]]
            except Exception:
                ind_names = []

            if not ind_names:
                ind_names = [f"{sec} Services", f"{sec} Infrastructure"]

            items.append(
                SectorExposureItem(
                    sector=sec,
                    industries=ind_names,
                    relevance="HIGH" if is_primary else "MEDIUM",
                    business_activities=[f"{sec} Operations", f"{sec} Regulatory Compliance"],
                    exposure_type=exp_type,
                    transmission_channel=f"Statutory mandate affecting {sec} operating entities.",
                )
            )

        return items

    def build_company_exposures(
        self,
        bill: UnifiedBillRecord,
        is_modelled: bool,
    ) -> list[LinkedCompanyExposureItem]:
        """
        Build evidence-grounded company exposures with explicit linkage reasons.
        Preserves strict boundary: company intelligence != market prediction.
        """
        raw_views = self.company_intel_service.get_companies_for_bill(bill.bill_id)
        linked: list[LinkedCompanyExposureItem] = []

        for v in raw_views:
            # Determine linkage reasons
            reasons: list[str] = []
            if v.business_activity:
                reasons.append("regulated_activity")
            if v.exposure_type:
                reasons.append("product_service_exposure")
            if v.direct_indirect and v.direct_indirect.upper() == "INDIRECT":
                reasons.append("supply_chain_exposure")
            if v.geographic_scope:
                reasons.append("geographic_scope")
            if v.sector:
                reasons.append("sector_exposure")
            if v.has_evidence:
                reasons.append("documented_corporate_relevance")

            if not reasons:
                reasons = ["documented_corporate_relevance"]

            # Exposure type mapping
            e_type = ExposureType.DIRECT.value
            if v.direct_indirect and v.direct_indirect.upper() == "INDIRECT":
                e_type = ExposureType.INDIRECT.value
            elif v.direct_indirect and v.direct_indirect.upper() == "POTENTIAL":
                e_type = ExposureType.POTENTIAL.value

            is_quant = v.company_id in _CENTRAL_QUANTITATIVE_ISINS
            has_preds = is_quant and is_modelled

            ev_summary = ""
            if v.evidence:
                ev_summary = v.evidence[0].claim if hasattr(v.evidence[0], "claim") else str(v.evidence[0])

            linked.append(
                LinkedCompanyExposureItem(
                    company_id=v.company_id,
                    company_name=v.company_name,
                    isin=v.company_id if v.company_id.startswith("INE") else None,
                    ticker_nse=None,
                    sector=v.sector or "General",
                    industry=v.sub_sector or "General",
                    linkage_reasons=reasons,
                    exposure_type=e_type,
                    exposure_direction=v.exposure_direction or "neutral",
                    exposure_strength=v.exposure_strength or "MEDIUM",
                    mechanism=v.mechanism or "Regulatory Compliance",
                    evidence_summary=ev_summary,
                    source_urls=list(v.source_urls),
                    is_quant_eligible=is_quant,
                    has_market_predictions=has_preds,
                )
            )

        return linked

    # ------------------------------------------------------------------
    # Phase 10: Document Viewer Integration
    # ------------------------------------------------------------------

    def build_documents(self, bill: UnifiedBillRecord) -> list[BillDocumentItem]:
        """
        Build document items supporting in-platform viewer and official access.
        Never fabricates a document.
        """
        docs: list[BillDocumentItem] = []

        # 1. Primary official PDF where available
        if bill.pdf_url:
            # Check if live knowledge has document hash
            live_rec = (
                self.live_knowledge_repo.get(bill.bill_id)
                or self.live_knowledge_repo.get_by_canonical_bill_id(bill.bill_id)
            )
            doc_hash = live_rec.document_hash_sha256 if live_rec else None

            docs.append(
                BillDocumentItem(
                    document_id=f"{bill.bill_id}_primary_pdf",
                    title=f"Official Bill Text — {bill.short_title or bill.title}",
                    url=bill.pdf_url,
                    hash_sha256=doc_hash,
                    format="PDF",
                    retrieved_at=live_rec.document_retrieved_at if live_rec else bill.created_at,
                    retrieval_status="AVAILABLE",
                    provenance="AUTHORITATIVE",
                    page_count=None,
                    source_authority=bill.legislature or "Parliament of India",
                )
            )

        # 2. Official Portal / Source Link
        if bill.source_url:
            docs.append(
                BillDocumentItem(
                    document_id=f"{bill.bill_id}_official_source",
                    title=f"Official Parliamentary Portal Reference",
                    url=bill.source_url,
                    hash_sha256=None,
                    format="HTML",
                    retrieved_at=bill.created_at,
                    retrieval_status="AVAILABLE",
                    provenance="AUTHORITATIVE",
                    page_count=None,
                    source_authority=bill.legislature or "Official Portal",
                )
            )

        # If no documents at all
        if not docs:
            docs.append(
                BillDocumentItem(
                    document_id=f"{bill.bill_id}_source_link",
                    title="Official Source Portal",
                    url=None,
                    hash_sha256=None,
                    format="PORTAL",
                    retrieved_at=None,
                    retrieval_status="OFFICIAL_PORTAL_ONLY",
                    provenance="AUTHORITATIVE",
                    page_count=None,
                    source_authority=bill.legislature or "Official Authority",
                )
            )

        return docs

    # ------------------------------------------------------------------
    # Complete Dossier Assembly
    # ------------------------------------------------------------------

    def get_dossier(self, bill_id: str) -> Optional[EnrichedBillDossier]:
        """
        Retrieve and assemble the full Enriched Legislative Dossier for a bill.
        """
        bill = self.resolve_bill(bill_id)
        if not bill:
            return None

        # Determine Model Status & Firewall
        model_status, status_label, status_desc, pred_avail = self.get_model_status_info(bill)

        # Central knowledge or State knowledge
        provisions: list[str] = []
        obligations: list[str] = []
        affected_activities: list[str] = []
        implementation_info: Optional[str] = None
        knowledge_obj = None

        if bill.is_central:
            kr = self.central_knowledge_repo.get(bill.bill_id)
            if kr:
                knowledge_obj = kr
                provisions = list(getattr(kr, "key_provisions", None) or [])
                obligations = list(getattr(kr, "compliance_requirements", None) or [])
                affected_activities = [kr.primary_sector] if getattr(kr, "primary_sector", None) else []
        elif bill.is_state:
            skr = self.state_knowledge_repo.get(bill.bill_id)
            if skr:
                knowledge_obj = skr
                if skr.economic_profile and hasattr(skr.economic_profile, "key_provisions"):
                    provisions = list(skr.economic_profile.key_provisions or [])
                if skr.impact_assessment and hasattr(skr.impact_assessment, "compliance_obligations"):
                    obligations = list(skr.impact_assessment.compliance_obligations or [])

        # Sub-components
        identity = DossierIdentity(
            bill_id=bill.bill_id,
            title=bill.title,
            short_title=bill.short_title or bill.title,
            bill_number=bill.bill_number,
            jurisdiction=bill.jurisdiction,
            state=bill.state,
            house=bill.house,
            legislature=bill.legislature,
            ministry=bill.ministry,
            bill_type="Government Bill",
            year=bill.year,
        )

        status = DossierStatus(
            current_status=bill.status,
            current_legislative_stage=bill.status.replace("_", " ").title(),
            introduction_date=bill.introduction_date,
            passage_date=bill.passage_date,
            assent_date=bill.assent_date,
            latest_verified_update=bill.created_at,
            status_history=[],
        )

        plain_lang = self.build_plain_language_explanation(bill, provisions, knowledge_obj)
        content = DossierContent(
            executive_summary=bill.summary,
            plain_language=plain_lang,
            key_provisions=provisions,
            obligations=obligations,
            affected_activities=affected_activities,
            implementation_info=implementation_info,
        )

        impact_context = DossierImpactContext(
            affected_sectors=list(bill.economic_sectors),
            affected_industries=list(bill.secondary_sectors),
            economic_themes=list(bill.economic_sectors),
            potentially_exposed_business_activities=affected_activities,
            company_exposure_count=bill.company_exposure_count,
            listed_company_exposure_count=bill.listed_company_exposure_count,
            market_relevance=bill.market_relevance,
        )

        provenance = DossierProvenance(
            official_source=bill.source_type,
            source_authority=bill.legislature or "Parliamentary Authority",
            source_url=bill.source_url,
            document_url=bill.pdf_url,
            document_hash=None,
            discovered_at=bill.created_at,
            verified_at=bill.created_at,
            last_updated_at=bill.created_at,
            data_quality=bill.data_quality,
            provenance_map=dict(bill.provenance or {}),
        )

        timeline = self.build_timeline(bill)
        changes = self.build_change_summary(bill)
        stakeholders = self.build_stakeholder_views(bill, is_modelled=pred_avail)
        sector_exposures = self.build_sector_exposures(bill)
        company_exposures = self.build_company_exposures(bill, is_modelled=pred_avail)
        documents = self.build_documents(bill)

        return EnrichedBillDossier(
            identity=identity,
            status=status,
            content=content,
            impact_context=impact_context,
            provenance=provenance,
            model_status=model_status,
            model_status_label=status_label,
            model_status_description=status_desc,
            prediction_available=pred_avail,
            timeline=timeline,
            change_summary=changes,
            stakeholder_views=stakeholders,
            sector_exposures=sector_exposures,
            company_exposures=company_exposures,
            documents=documents,
            ai_explanation=None,
        )
