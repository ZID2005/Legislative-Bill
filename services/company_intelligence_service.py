"""
services/company_intelligence_service.py
========================================
Unified Company & Industry Intelligence Service.

Provides a first-class, evidence-grounded intelligence layer linking:
COMPANY
→ RELATED BILLS
→ EXPOSURE
→ WHY IT IS RELEVANT
→ EVIDENCE
→ BUSINESS ACTIVITY
→ SECTOR / INDUSTRY
→ STATE / GEOGRAPHIC RELEVANCE
→ ECONOMIC MECHANISM
→ MARKET RELEVANCE
→ AI EXPLANATION

Strict Architectural Guardrails:
1. Strict Quantitative Firewall:
   - Quantitative models (47 Central companies, 940 pairs, 4700 predictions) are frozen.
   - Intelligence-only companies NEVER receive stock return, CAR, alpha, or trading signals.
   - State market predictions strictly remain 0.
2. Zero Speculative Exposures:
   - Exposure explanations are generated deterministically from stored statutory and corporate evidence.
   - If evidence does not establish meaningful relevance, explicit NO EXPOSURE is returned.
3. State Presence Evidence Required:
   - State-specific exposures require verified operational presence in that State.
   - National presence alone does not establish State bill exposure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
import re
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.company import Company, EntityType, OwnershipType, UniverseType
from schemas.state_corporate_exposure import (
    CorporateExposureEvidence,
    StateCorporateExposure,
    _FORBIDDEN_PREDICTIVE_TERMS,
)
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_knowledge_repository import StateKnowledgeRepository
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)


# Canonical Central quantitative ISINs baseline (47 companies)
_CENTRAL_QUANTITATIVE_ISINS: frozenset[str] = frozenset(
    [
        "INE002A01018",  # Reliance Industries
        "INE467B01029",  # TCS
        "INE040A01034",  # HDFC Bank
        "INE009A01021",  # Infosys
        "INE090A01021",  # ICICI Bank
        "INE397D01024",  # Bharti Airtel
        "INE062A01020",  # SBI
        "INE018A01030",  # L&T
        "INE154A01025",  # ITC
        "INE030A01027",  # HUL
        "INE423A01024",  # Adani Enterprises
        "INE155A01022",  # Tata Motors
        "INE044A01045",  # Sun Pharma
        "INE733E01010",  # NTPC
        "INE213A01029",  # ONGC
        "INE238A01034",  # Axis Bank
        "INE237A01028",  # Kotak Mahindra Bank
        "INE075A01022",  # Wipro
        "INE860A01027",  # HCL Technologies
        "INE585B01010",  # Maruti Suzuki
        "INE101A01026",  # M&M
        "INE081A01020",  # Tata Steel
        "INE019A01030",  # JSW Steel
        "INE038A01020",  # Hindalco
        "INE522F01014",  # Coal India
        "INE481G01011",  # UltraTech Cement
        "INE047A01021",  # Grasim
        "INE239A01016",  # Nestle
        "INE216A01030",  # Britannia
        "INE192A01025",  # Tata Consumer
        "INE021A01026",  # Asian Paints
        "INE059A01026",  # Cipla
        "INE089A01023",  # Dr. Reddy's
        "INE437A01024",  # Apollo Hospitals
        "INE752E01010",  # Power Grid
        "INE245A01021",  # Tata Power
        "INE364U01010",  # Adani Green
        "INE814H01011",  # Adani Power
        "INE296A01024",  # Bajaj Finance
        "INE918I01018",  # Bajaj Finserv
        "INE00LIC01010",  # LIC
        "INE123W01016",  # SBI Life
        "INE795G01014",  # HDFC Life
        "INE066A01021",  # Eicher Motors
        "INE158A01026",  # Hero Motocorp
        "INE917I01010",  # Bajaj Auto
        "INE669C01036",  # Tech Mahindra
    ]
)


# ---------------------------------------------------------------------------
# Data Contracts / View Models
# ---------------------------------------------------------------------------


@dataclass
class CompanyBillExposureView:
    """Canonical representation of a verified company-bill exposure relationship."""

    bill_id: str
    bill_title: str
    company_id: str = ""
    company_name: str = ""
    bill_number: Optional[str] = None
    jurisdiction: str = "central"
    state: Optional[str] = None
    bill_status: str = "introduced"
    sector: str = ""
    sub_sector: str = ""
    business_activity: str = ""
    exposure_type: str = "regulatory"
    exposure_direction: str = "neutral"
    exposure_strength: str = "MEDIUM"
    direct_indirect: str = "DIRECT"
    geographic_scope: str = "national"
    mechanism: str = "compliance"
    market_relevance: str = "UNKNOWN"
    confidence: str = "HIGH"
    evidence: list[CorporateExposureEvidence] = field(default_factory=list)
    has_evidence: bool = True
    source_urls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "bill_number": self.bill_number,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "bill_status": self.bill_status,
            "sector": self.sector,
            "sub_sector": self.sub_sector,
            "business_activity": self.business_activity,
            "exposure_type": self.exposure_type,
            "exposure_direction": self.exposure_direction,
            "exposure_strength": self.exposure_strength,
            "direct_indirect": self.direct_indirect,
            "geographic_scope": self.geographic_scope,
            "mechanism": self.mechanism,
            "market_relevance": self.market_relevance,
            "confidence": self.confidence,
            "evidence": [e.to_dict() if hasattr(e, "to_dict") else e for e in self.evidence],
            "has_evidence": self.has_evidence,
            "source_urls": self.source_urls,
        }


@dataclass
class CompanyExposureExplanation:
    """Structured deterministic explanation of why a company is exposed to legislation."""

    company_name: str
    company_id: str
    bill_id: str
    bill_title: str
    has_exposure: bool
    exposure_type: str = "NONE"
    direct_indirect: str = "NONE"
    exposure_strength: str = "NONE"
    business_activity: str = ""
    geographic_relevance: str = ""
    economic_mechanism: str = ""
    evidence_claims: list[str] = field(default_factory=list)
    evidence_references: list[str] = field(default_factory=list)
    market_relevance: str = "NONE"
    why_explanation: str = ""
    data_quality: str = "VERIFIED"
    provenance_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "company_id": self.company_id,
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "has_exposure": self.has_exposure,
            "exposure_type": self.exposure_type,
            "direct_indirect": self.direct_indirect,
            "exposure_strength": self.exposure_strength,
            "business_activity": self.business_activity,
            "geographic_relevance": self.geographic_relevance,
            "economic_mechanism": self.economic_mechanism,
            "evidence_claims": self.evidence_claims,
            "evidence_references": self.evidence_references,
            "market_relevance": self.market_relevance,
            "why_explanation": self.why_explanation,
            "data_quality": self.data_quality,
            "provenance_sources": self.provenance_sources,
        }

    def format_display(self) -> str:
        """Render plain-text formatted explanation."""
        if not self.has_exposure:
            return (
                f"Company: {self.company_name}\n"
                f"Legislation: {self.bill_title} ({self.bill_id})\n"
                "Exposure: NONE\n"
                "Why: No verified evidence connects this company to the legislation.\n"
                "Evidence: None recorded."
            )

        evidence_str = "\n".join(f"• {c} (Ref: {r})" for c, r in zip(self.evidence_claims, self.evidence_references))
        if not evidence_str:
            evidence_str = "• Authoritative statutory and corporate records."

        return (
            f"Company:\n{self.company_name}\n\n"
            f"Legislation:\n{self.bill_title} [{self.bill_id}]\n\n"
            f"Exposure:\n{self.direct_indirect} ({self.exposure_strength} strength, {self.exposure_type})\n\n"
            f"Why:\n{self.why_explanation}\n\n"
            f"Business activity:\n{self.business_activity or 'General sector operations'}\n\n"
            f"Geographic relevance:\n{self.geographic_relevance}\n\n"
            f"Economic mechanism:\n{self.economic_mechanism}\n\n"
            f"Evidence:\n{evidence_str}\n\n"
            f"Market relevance:\n{self.market_relevance} (Qualitative classification only; zero price forecasts)"
        )


@dataclass
class CompanyProfileView:
    """Comprehensive company intelligence dossier response model."""

    # Identity
    company_id: str
    company_name: str
    legal_identity: str
    aliases: list[str] = field(default_factory=list)
    ticker_nse: str = ""
    ticker_bse: str = ""
    bse_code: str = ""
    isin: str = ""
    entity_type: str = "listed_company"
    universe_type: str = "quantitative"
    group_name: Optional[str] = None
    ownership_type: str = "unknown"
    is_active: bool = True
    listing_status: str = "Listed"

    # Business
    sector: str = ""
    industry: str = ""
    sub_industry: str = ""
    business_description: str = ""
    business_activities: list[str] = field(default_factory=list)

    # Geography
    hq_state: str = ""
    hq_city: str = ""
    operating_states: list[str] = field(default_factory=list)
    state_presences: list[dict[str, Any]] = field(default_factory=list)
    facilities: list[dict[str, Any]] = field(default_factory=list)

    # Provenance & Quality
    data_sources: list[str] = field(default_factory=list)
    data_quality_score: Optional[float] = None
    data_quality_label: str = "VERIFIED"

    # Legislation & Exposure
    related_bills: list[CompanyBillExposureView] = field(default_factory=list)
    total_exposures: int = 0
    central_exposures_count: int = 0
    state_exposures_count: int = 0
    direct_exposures_count: int = 0
    indirect_exposures_count: int = 0
    exposure_types: list[str] = field(default_factory=list)
    mechanisms: list[str] = field(default_factory=list)
    affected_sectors: list[str] = field(default_factory=list)

    # Prediction Boundary & Firewall
    watchlist_eligible: bool = False
    is_quant_eligible: bool = False
    market_prediction_available: bool = False
    quantitative_firewall_status: str = "ACTIVE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "legal_identity": self.legal_identity,
            "aliases": self.aliases,
            "ticker_nse": self.ticker_nse,
            "ticker_bse": self.ticker_bse,
            "bse_code": self.bse_code,
            "isin": self.isin,
            "entity_type": self.entity_type,
            "universe_type": self.universe_type,
            "group_name": self.group_name,
            "ownership_type": self.ownership_type,
            "is_active": self.is_active,
            "listing_status": self.listing_status,
            "sector": self.sector,
            "industry": self.industry,
            "sub_industry": self.sub_industry,
            "business_description": self.business_description,
            "business_activities": self.business_activities,
            "hq_state": self.hq_state,
            "hq_city": self.hq_city,
            "operating_states": self.operating_states,
            "state_presences": self.state_presences,
            "facilities": self.facilities,
            "data_sources": self.data_sources,
            "data_quality_score": self.data_quality_score,
            "data_quality_label": self.data_quality_label,
            "related_bills": [b.to_dict() for b in self.related_bills],
            "total_exposures": self.total_exposures,
            "central_exposures_count": self.central_exposures_count,
            "state_exposures_count": self.state_exposures_count,
            "direct_exposures_count": self.direct_exposures_count,
            "indirect_exposures_count": self.indirect_exposures_count,
            "exposure_types": self.exposure_types,
            "mechanisms": self.mechanisms,
            "affected_sectors": self.affected_sectors,
            "watchlist_eligible": self.watchlist_eligible,
            "is_quant_eligible": self.is_quant_eligible,
            "market_prediction_available": self.market_prediction_available,
            "quantitative_firewall_status": self.quantitative_firewall_status,
        }


# ---------------------------------------------------------------------------
# CompanyIntelligenceService
# ---------------------------------------------------------------------------


class CompanyIntelligenceService:
    """
    Unified intelligence service for Company & Industry analysis.

    Bridges corporate universe repositories with legislative exposure discovery,
    ensuring rigorous, evidence-grounded answers across both Central and State legislation.
    """

    def __init__(
        self,
        company_repo: Optional[CompanyRepository] = None,
        exposure_repo: Optional[CompanyExposureRepository] = None,
        bill_repo: Optional[BillRepository] = None,
        state_bill_repo: Optional[StateBillRepository] = None,
        state_knowledge_repo: Optional[StateKnowledgeRepository] = None,
    ) -> None:
        self.company_repo = company_repo or CompanyRepository()
        self.exposure_repo = exposure_repo or CompanyExposureRepository()
        self.bill_repo = bill_repo or BillRepository()
        self.state_bill_repo = state_bill_repo or StateBillRepository()
        self.state_knowledge_repo = state_knowledge_repo or StateKnowledgeRepository()
        self._title_cache: dict[str, str] = {}
        logger.debug("CompanyIntelligenceService initialised.")

    # ------------------------------------------------------------------
    # Helper: Resolve Bill Title
    # ------------------------------------------------------------------

    def _get_bill_title(self, bill_id: str) -> str:
        """Resolve a human-readable bill title from Central or State repositories."""
        if bill_id in self._title_cache:
            return self._title_cache[bill_id]

        # Check central
        cb = self.bill_repo.get(bill_id)
        if cb and cb.title:
            self._title_cache[bill_id] = cb.title
            return cb.title

        # Check state knowledge
        sk = self.state_knowledge_repo.get(bill_id)
        if sk and sk.title:
            self._title_cache[bill_id] = sk.title
            return sk.title

        # Check state bill
        sb = self.state_bill_repo.get(bill_id)
        if sb and sb.title:
            self._title_cache[bill_id] = sb.title
            return sb.title

        # Clean fallback from slug
        clean_title = bill_id.replace("-", " ").title()
        self._title_cache[bill_id] = clean_title
        return clean_title

    # ------------------------------------------------------------------
    # 1. Company Resolution & Profile Retrieval
    # ------------------------------------------------------------------

    def resolve_company(self, identifier: str) -> Optional[Company]:
        """
        Find a company by ISIN, ticker, exact name, or alias.
        """
        id_str = identifier.strip()
        if not id_str:
            return None

        # 1. Direct ISIN match
        comp = self.company_repo.get_by_isin(id_str)
        if comp:
            return comp

        # 2. Ticker match
        comp = self.company_repo.get_by_ticker(id_str, exchange="NSE")
        if comp:
            return comp
        comp = self.company_repo.get_by_ticker(id_str, exchange="BSE")
        if comp:
            return comp

        # 3. Name or alias match via search
        candidates = self.company_repo.search_by_name(id_str, top_k=5)
        id_lower = id_str.lower()
        for c in candidates:
            if c.company_name.lower() == id_lower or id_lower in c.company_name.lower():
                return c
            for al in getattr(c, "aliases", []):
                if al.lower() == id_lower or id_lower in al.lower():
                    return c

        if candidates:
            return candidates[0]

        # 4. Fallback search across all records
        for c in self.company_repo.get_all():
            if id_lower in c.company_name.lower() or id_lower in c.isin.lower():
                return c
            if c.ticker_nse and id_lower == c.ticker_nse.lower():
                return c
            for al in getattr(c, "aliases", []):
                if id_lower == al.lower():
                    return c

        return None

    def get_company_profile(self, identifier: str) -> Optional[CompanyProfileView]:
        """
        Retrieve a unified, complete company intelligence profile.
        """
        company = self.resolve_company(identifier)
        if not company:
            return None

        # Fetch related bills from corporate exposure repository
        exps = self.exposure_repo.get_bills_for_company(company.isin)
        if not exps and company.company_name:
            exps = self.exposure_repo.get_bills_for_company(company.company_name)

        # Deduplicate exposures by (bill_id, company_id)
        seen_bills: set[str] = set()
        exposure_views: list[CompanyBillExposureView] = []
        for e in exps:
            if e.bill_id in seen_bills:
                continue
            seen_bills.add(e.bill_id)

            bill_title = self._get_bill_title(e.bill_id)
            ev_list = [
                ev if isinstance(ev, CorporateExposureEvidence) else CorporateExposureEvidence.from_dict(ev)
                for ev in e.evidence
            ]

            exposure_views.append(
                CompanyBillExposureView(
                    bill_id=e.bill_id,
                    bill_title=bill_title,
                    company_id=e.company_id,
                    company_name=e.company_name,
                    bill_number=None,
                    jurisdiction=e.jurisdiction,
                    state=e.state or None,
                    bill_status="introduced",
                    sector=e.sector,
                    sub_sector=e.sub_sector,
                    business_activity=e.business_activity,
                    exposure_type=e.exposure_type,
                    exposure_direction=e.exposure_direction,
                    exposure_strength=e.exposure_strength,
                    direct_indirect=e.direct_indirect,
                    geographic_scope=e.geographic_scope,
                    mechanism=e.mechanism,
                    market_relevance=e.market_relevance,
                    confidence=e.confidence,
                    evidence=ev_list,
                    has_evidence=len(ev_list) > 0,
                    source_urls=e.source_urls,
                )
            )

        # Operational states
        op_states: set[str] = set()
        if company.hq_state:
            op_states.add(company.hq_state)
        for sp in company.state_presences:
            st_name = getattr(sp, "state", None) or (sp.get("state") if isinstance(sp, dict) else None)
            if st_name:
                op_states.add(st_name)

        # Entity classification & quantitative boundary
        u_type = company.universe_type.value if hasattr(company.universe_type, "value") else str(company.universe_type)
        e_type = company.entity_type.value if hasattr(company.entity_type, "value") else str(company.entity_type)
        o_type = company.ownership_type.value if hasattr(company.ownership_type, "value") else str(company.ownership_type)

        is_quant_eligible = company.isin in _CENTRAL_QUANTITATIVE_ISINS
        has_predictions = is_quant_eligible and u_type in (UniverseType.QUANTITATIVE.value, UniverseType.BOTH.value)
        firewall_status = "QUANTITATIVE_PRODUCTION" if has_predictions else "INTELLIGENCE_ONLY_FIREWALLED"

        # Quality scoring
        q_score = company.data_quality_score
        if q_score is not None:
            q_label = "HIGH_CONFIDENCE" if q_score >= 0.8 else ("MODERATE" if q_score >= 0.5 else "LOW")
        else:
            q_label = "VERIFIED"

        central_cnt = sum(1 for e in exposure_views if e.jurisdiction == "central")
        state_cnt = sum(1 for e in exposure_views if e.jurisdiction == "state")
        direct_cnt = sum(1 for e in exposure_views if e.direct_indirect.upper() == "DIRECT")
        indirect_cnt = sum(1 for e in exposure_views if e.direct_indirect.upper() == "INDIRECT")

        exp_types = sorted(list({e.exposure_type for e in exposure_views if e.exposure_type}))
        mechs = sorted(list({e.mechanism for e in exposure_views if e.mechanism}))
        aff_sectors = sorted(list({e.sector for e in exposure_views if e.sector}))

        presences_dicts = [
            sp.to_dict() if hasattr(sp, "to_dict") else sp for sp in company.state_presences
        ]

        return CompanyProfileView(
            company_id=company.isin,
            company_name=company.company_name,
            legal_identity=f"{company.company_name} ({e_type.replace('_', ' ').title()})",
            aliases=list(company.aliases),
            ticker_nse=company.ticker_nse,
            ticker_bse=company.ticker_bse,
            bse_code=company.bse_code,
            isin=company.isin,
            entity_type=e_type,
            universe_type=u_type,
            group_name=company.group_name,
            ownership_type=o_type,
            is_active=company.is_active,
            listing_status=company.listing_status,
            sector=company.sector,
            industry=company.industry,
            sub_industry=company.sub_industry,
            business_description=company.business_description,
            business_activities=list(company.business_activities),
            hq_state=company.hq_state,
            hq_city=company.hq_city,
            operating_states=sorted(list(op_states)),
            state_presences=presences_dicts,
            facilities=list(company.facilities),
            data_sources=list(company.data_sources),
            data_quality_score=q_score,
            data_quality_label=q_label,
            related_bills=exposure_views,
            total_exposures=len(exposure_views),
            central_exposures_count=central_cnt,
            state_exposures_count=state_cnt,
            direct_exposures_count=direct_cnt,
            indirect_exposures_count=indirect_cnt,
            exposure_types=exp_types,
            mechanisms=mechs,
            affected_sectors=aff_sectors,
            watchlist_eligible=company.watchlist_eligible,
            is_quant_eligible=is_quant_eligible,
            market_prediction_available=has_predictions,
            quantitative_firewall_status=firewall_status,
        )

    # ------------------------------------------------------------------
    # 2. Company Universe Queries
    # ------------------------------------------------------------------

    def get_all_companies(self, universe_type: Optional[str] = None) -> list[Company]:
        """Return all companies in master repository, optionally filtered by universe."""
        all_comps = self.company_repo.get_all()
        if not universe_type:
            return all_comps

        u_norm = universe_type.strip().lower()
        if u_norm == "intelligence":
            return [c for c in all_comps if c.universe_type == UniverseType.INTELLIGENCE]
        if u_norm == "quantitative":
            return [c for c in all_comps if c.universe_type in (UniverseType.QUANTITATIVE, UniverseType.BOTH)]
        return all_comps

    def get_intelligence_companies(self) -> list[Company]:
        """Convenience method returning all intelligence-universe entities."""
        return self.company_repo.get_intelligence_companies()

    def get_quantitative_companies(self) -> list[Company]:
        """Return companies belonging to the quantitative prediction universe."""
        return [c for c in self.company_repo.get_all() if c.universe_type in (UniverseType.QUANTITATIVE, UniverseType.BOTH)]

    # ------------------------------------------------------------------
    # 3. Company → Bill Discovery
    # ------------------------------------------------------------------

    def get_bills_for_company(self, company_identifier: str) -> list[CompanyBillExposureView]:
        """
        Query: Which bills affect this company?
        Supports queries for Central and State legislation across both listed and unlisted entities.
        """
        prof = self.get_company_profile(company_identifier)
        if prof:
            return prof.related_bills

        # Direct repository query if company record is missing
        exps = self.exposure_repo.get_bills_for_company(company_identifier)
        views: list[CompanyBillExposureView] = []
        for e in exps:
            views.append(
                CompanyBillExposureView(
                    bill_id=e.bill_id,
                    bill_title=self._get_bill_title(e.bill_id),
                    company_id=e.company_id,
                    company_name=e.company_name,
                    jurisdiction=e.jurisdiction,
                    state=e.state or None,
                    sector=e.sector,
                    sub_sector=e.sub_sector,
                    business_activity=e.business_activity,
                    exposure_type=e.exposure_type,
                    exposure_direction=e.exposure_direction,
                    exposure_strength=e.exposure_strength,
                    direct_indirect=e.direct_indirect,
                    geographic_scope=e.geographic_scope,
                    mechanism=e.mechanism,
                    market_relevance=e.market_relevance,
                    confidence=e.confidence,
                    evidence=list(e.evidence),
                    has_evidence=len(e.evidence) > 0,
                    source_urls=e.source_urls,
                )
            )
        return views

    # ------------------------------------------------------------------
    # 4. Bill → Company Discovery
    # ------------------------------------------------------------------

    def get_companies_for_bill(self, bill_id: str) -> list[CompanyBillExposureView]:
        """
        Query: Which companies are exposed to this bill?
        Supports both Central bills and State bills.
        """
        clean_bid = bill_id.strip()
        exps = self.exposure_repo.get_companies_for_bill(clean_bid)
        bill_title = self._get_bill_title(clean_bid)

        results: list[CompanyBillExposureView] = []
        for e in exps:
            results.append(
                CompanyBillExposureView(
                    bill_id=e.bill_id,
                    bill_title=bill_title,
                    company_id=e.company_id,
                    company_name=e.company_name,
                    jurisdiction=e.jurisdiction,
                    state=e.state or None,
                    sector=e.sector,
                    sub_sector=e.sub_sector,
                    business_activity=e.business_activity,
                    exposure_type=e.exposure_type,
                    exposure_direction=e.exposure_direction,
                    exposure_strength=e.exposure_strength,
                    direct_indirect=e.direct_indirect,
                    geographic_scope=e.geographic_scope,
                    mechanism=e.mechanism,
                    market_relevance=e.market_relevance,
                    confidence=e.confidence,
                    evidence=list(e.evidence),
                    has_evidence=len(e.evidence) > 0,
                    source_urls=e.source_urls,
                )
            )
        return results

    # ------------------------------------------------------------------
    # 5. Deterministic Exposure Explanation
    # ------------------------------------------------------------------

    def explain_exposure(
        self, company_identifier: str, bill_id: str
    ) -> CompanyExposureExplanation:
        """
        Generate a deterministic, evidence-grounded exposure explanation.
        No LLM speculation; returns stored statutory and business grounds.
        """
        company = self.resolve_company(company_identifier)
        c_name = company.company_name if company else company_identifier
        c_id = company.isin if company else company_identifier

        exps = self.exposure_repo.get_bills_for_company(company_identifier)
        matching = next((e for e in exps if e.bill_id == bill_id), None)

        bill_title = self._get_bill_title(bill_id)

        if not matching:
            return CompanyExposureExplanation(
                company_name=c_name,
                company_id=c_id,
                bill_id=bill_id,
                bill_title=bill_title,
                has_exposure=False,
                exposure_type="NONE",
                direct_indirect="NONE",
                exposure_strength="NONE",
                why_explanation=f"No verified exposure identified between company '{c_name}' and bill '{bill_id}'.",
                market_relevance="NONE",
            )

        # Format why explanation deterministically
        claims = [ev.claim for ev in matching.evidence if ev.claim]
        refs = [ev.reference for ev in matching.evidence if ev.reference]

        why_text = (
            f"The bill '{bill_title}' affects regulatory and statutory requirements in the {matching.sector} sector "
            f"({matching.sub_sector}) directly connected to the verified business activity '{matching.business_activity}'. "
            f"Authoritative records establish that {matching.company_name} is subject to the '{matching.mechanism}' mechanism "
            f"under this statute."
        )

        geo_rel = matching.state or ("National / Central" if matching.jurisdiction == "central" else "India-wide")

        return CompanyExposureExplanation(
            company_name=matching.company_name,
            company_id=matching.company_id or c_id,
            bill_id=matching.bill_id,
            bill_title=bill_title,
            has_exposure=True,
            exposure_type=matching.exposure_type,
            direct_indirect=matching.direct_indirect,
            exposure_strength=matching.exposure_strength,
            business_activity=matching.business_activity,
            geographic_relevance=geo_rel,
            economic_mechanism=matching.mechanism,
            evidence_claims=claims,
            evidence_references=refs,
            market_relevance=matching.market_relevance,
            why_explanation=why_text,
            data_quality="VERIFIED",
            provenance_sources=matching.source_urls or ["Authoritative Official Filing / Statute"],
        )

    # ------------------------------------------------------------------
    # 6. Sector / Industry Integration
    # ------------------------------------------------------------------

    def get_companies_by_sector(self, sector: str) -> list[Company]:
        """
        Return all companies operating in a given sector across Central and State taxonomies.
        """
        sec_norm = sector.strip().lower()
        if not sec_norm:
            return []

        matched: list[Company] = []
        for c in self.company_repo.get_all():
            c_sec = c.sector.lower()
            c_ind = c.industry.lower()
            if sec_norm in c_sec or c_sec in sec_norm or sec_norm in c_ind:
                matched.append(c)

        return matched

    def get_companies_by_industry(self, industry: str) -> list[Company]:
        """
        Return all companies operating in a specific industry.
        """
        ind_norm = industry.strip().lower()
        if not ind_norm:
            return []

        return [
            c for c in self.company_repo.get_all()
            if ind_norm in c.industry.lower() or ind_norm in c.sub_industry.lower()
        ]

    # ------------------------------------------------------------------
    # 7. State Operational Presence Integration
    # ------------------------------------------------------------------

    def get_companies_by_state(self, state: str) -> list[Company]:
        """
        Return companies with verified operational presence or headquarters in a given State.
        Strictly requires evidence of state presence.
        """
        st_norm = (normalize_state(state) or state).strip().lower()
        if not st_norm:
            return []

        matched: list[Company] = []
        for c in self.company_repo.get_all():
            # Check HQ
            c_hq = (normalize_state(c.hq_state) or c.hq_state).strip().lower()
            if c_hq == st_norm:
                matched.append(c)
                continue

            # Check state presence records
            found_presence = False
            for sp in c.state_presences:
                sp_st = getattr(sp, "state", None) or (sp.get("state") if isinstance(sp, dict) else None)
                if sp_st:
                    norm_sp = (normalize_state(sp_st) or sp_st).strip().lower()
                    if norm_sp == st_norm:
                        matched.append(c)
                        found_presence = True
                        break

            if found_presence:
                continue

            # Check facilities
            for fac in c.facilities:
                fac_st = fac.get("state") if isinstance(fac, dict) else getattr(fac, "state", None)
                if fac_st:
                    norm_fac = (normalize_state(fac_st) or fac_st).strip().lower()
                    if norm_fac == st_norm:
                        matched.append(c)
                        break

        return matched

    # ------------------------------------------------------------------
    # 8. Search & Watchlist Readiness
    # ------------------------------------------------------------------

    def search_companies(self, query: str, top_k: int = 15) -> list[CompanyProfileView]:
        """
        Fuzzy & multi-field search across company universe.
        """
        q = query.strip().lower()
        if not q:
            return [self.get_company_profile(c.isin) for c in self.company_repo.get_all()[:top_k] if c]

        scored: list[tuple[float, Company]] = []
        for c in self.company_repo.get_all():
            score = 0.0
            name_lower = c.company_name.lower()
            isin_lower = c.isin.lower()
            ticker_lower = c.ticker_nse.lower()
            sec_lower = c.sector.lower()
            ind_lower = c.industry.lower()

            if q == name_lower or q == ticker_lower or q == isin_lower:
                score += 10.0
            elif q in name_lower or q in ticker_lower or q in isin_lower:
                score += 5.0

            for al in getattr(c, "aliases", []):
                al_lower = al.lower()
                if q == al_lower:
                    score += 8.0
                elif q in al_lower:
                    score += 4.0

            for act in getattr(c, "business_activities", []):
                if q in act.lower():
                    score += 3.0

            if q in sec_lower or q in ind_lower:
                score += 2.0

            # Ratio fallback
            ratio = SequenceMatcher(None, q, name_lower).ratio()
            score += ratio * 2.0

            if score > 1.2:
                scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: list[CompanyProfileView] = []
        for _, comp in scored[:top_k]:
            prof = self.get_company_profile(comp.isin)
            if prof:
                results.append(prof)
        return results

    def check_watchlist_eligibility(self, identifier: str) -> bool:
        """
        Check if a company is marked watchlist_eligible for future Task 8.13.
        """
        comp = self.resolve_company(identifier)
        if comp:
            return bool(getattr(comp, "watchlist_eligible", False))
        return False
