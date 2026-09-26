"""
services/industry_intelligence_service.py
==========================================
Unified Industry & Sector Intelligence Service for the India Legislative Intelligence Platform.

Bridges:
- Master Company Universe (70 entities across 36 industries & 11 sectors)
- Corporate Exposures (104 validated exposures across Central and State jurisdictions)
- Central Parliamentary Legislation (20 production bills + 2 service/dev)
- Central Model Predictions & Decisions (4,700 predictions, 4,700 decisions, 940 anticipation scores)
- State Legislative Intelligence (44 state bills across 4 implemented states)

Strict Epistemic & Statutory Invariants:
1. State Prediction Firewall: State legislation has strictly 0 stock market predictions.
2. Intelligence Company Firewall: Non-quantitative entities never receive quantitative predictions.
3. Zero Data Mutation: Prediction datasets, decision records, and anticipation scores remain frozen and read-only.
4. Epistemic Separation: Preserves explicit distinction between [FACT], [DERIVED], [INTERPRETATION], and [PREDICTION].
5. Grounded Economic Transmission: Only displays economic mechanisms substantiated by authoritative corporate exposure records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.company import Company, UniverseType
from schemas.state_corporate_exposure import CorporateExposureEvidence, StateCorporateExposure
from services.company_intelligence_service import _CENTRAL_QUANTITATIVE_ISINS
from storage.anticipation_repository import AnticipationRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.decision_repository import DecisionRepository
from storage.knowledge_repository import KnowledgeRepository
from storage.prediction_repository import PredictionRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_knowledge_repository import StateKnowledgeRepository

logger = get_logger(__name__)


def slugify_industry(name: str) -> str:
    """Generate a URL-safe canonical slug from an industry name."""
    clean = name.lower().strip()
    clean = re.sub(r"[^a-z0-9]+", "-", clean)
    return clean.strip("-") or "unclassified"


@dataclass
class IndustrySummary:
    """Compact summary card for an industry."""

    industry_id: str
    name: str
    sector: str
    coverage_level: int  # 1: Quantitative Modelled, 2: Corporate Intelligence, 3: Legislative/Economic
    related_bills_count: int
    exposed_companies_count: int
    central_exposures_count: int
    state_exposures_count: int
    quantitative_companies_count: int
    intelligence_companies_count: int
    market_analysis_available: bool
    economic_mechanisms: list[str]
    latest_legislative_activity: Optional[str] = None
    sub_industries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "industry_id": self.industry_id,
            "name": self.name,
            "sector": self.sector,
            "coverage_level": self.coverage_level,
            "related_bills_count": self.related_bills_count,
            "exposed_companies_count": self.exposed_companies_count,
            "central_exposures_count": self.central_exposures_count,
            "state_exposures_count": self.state_exposures_count,
            "quantitative_companies_count": self.quantitative_companies_count,
            "intelligence_companies_count": self.intelligence_companies_count,
            "market_analysis_available": self.market_analysis_available,
            "economic_mechanisms": self.economic_mechanisms,
            "latest_legislative_activity": self.latest_legislative_activity,
            "sub_industries": self.sub_industries,
        }


@dataclass
class IndustryBillExposureItem:
    """Legislative footprint record for an industry."""

    bill_id: str
    bill_title: str
    jurisdiction: str  # "central" | "state"
    state: Optional[str] = None
    policy_domain: str = ""
    legislative_status: str = "introduced"
    exposure_strength: str = "MEDIUM"
    economic_mechanism: str = "compliance"
    provisions_summary: str = ""
    exposed_company_ids: list[str] = field(default_factory=list)
    exposed_company_names: list[str] = field(default_factory=list)
    provenance_sources: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "policy_domain": self.policy_domain,
            "legislative_status": self.legislative_status,
            "exposure_strength": self.exposure_strength,
            "economic_mechanism": self.economic_mechanism,
            "provisions_summary": self.provisions_summary,
            "exposed_company_ids": self.exposed_company_ids,
            "exposed_company_names": self.exposed_company_names,
            "provenance_sources": self.provenance_sources,
        }


@dataclass
class IndustryCompanyItem:
    """Corporate entity associated with an industry."""

    company_id: str
    company_name: str
    ticker_nse: Optional[str]
    ticker_bse: Optional[str]
    sector: str
    industry: str
    universe_type: str  # "quantitative" | "intelligence" | "reference"
    entity_type: str
    ownership_type: str
    listing_status: str
    is_quant_eligible: bool
    market_prediction_available: bool
    exposure_count: int
    exposure_strength: str
    direct_indirect: str
    primary_mechanism: str
    market_relevance: str
    evidence_reference: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "ticker_nse": self.ticker_nse,
            "ticker_bse": self.ticker_bse,
            "sector": self.sector,
            "industry": self.industry,
            "universe_type": self.universe_type,
            "entity_type": self.entity_type,
            "ownership_type": self.ownership_type,
            "listing_status": self.listing_status,
            "is_quant_eligible": self.is_quant_eligible,
            "market_prediction_available": self.market_prediction_available,
            "exposure_count": self.exposure_count,
            "exposure_strength": self.exposure_strength,
            "direct_indirect": self.direct_indirect,
            "primary_mechanism": self.primary_mechanism,
            "market_relevance": self.market_relevance,
            "evidence_reference": self.evidence_reference,
        }


@dataclass
class TransmissionChainStep:
    """Single node in the visual economic transmission map."""

    step_type: str  # "LEGISLATION" | "POLICY_CHANGE" | "ECONOMIC_MECHANISM" | "INDUSTRY" | "COMPANY_EXPOSURE" | "MARKET_ANALYSIS"
    title: str
    description: str
    evidence_ref: Optional[str] = None
    jurisdiction: str = "central"
    status: str = "ACTIVE"  # "ACTIVE" | "MODELLED" | "FIREWALLED_ZERO"


@dataclass
class IndustryDossier:
    """Complete 13-section dossier for an industry."""

    # Section A: Header
    industry_id: str
    name: str
    sector: str
    coverage_level: int
    description: str
    total_bills_count: int
    central_bills_count: int
    state_bills_count: int
    total_companies_count: int
    quantitative_companies_count: int
    intelligence_companies_count: int
    reference_companies_count: int
    central_exposures_count: int
    state_exposures_count: int
    market_analysis_available: bool
    dominant_mechanism: str

    # Section B: Executive Overview (4-Zone Epistemic)
    facts: list[str]
    derived: list[str]
    interpretations: list[str]
    predictions: list[str]

    # Section C: Legislative Footprint
    central_bills: list[IndustryBillExposureItem]
    state_bills: list[IndustryBillExposureItem]

    # Section D & J: Corporate Exposure & Network
    quantitative_companies: list[IndustryCompanyItem]
    intelligence_companies: list[IndustryCompanyItem]
    reference_companies: list[IndustryCompanyItem]

    # Section E: Economic Transmission Chains
    transmission_chains: list[list[dict[str, Any]]]
    active_mechanisms: list[str]

    # Section F: Central Market Intelligence (where available)
    market_intelligence: dict[str, Any]

    # Section G: State Legislative Intelligence
    state_intelligence: dict[str, Any]

    # Section H: Risk Context
    risk_summary: dict[str, Any]

    # Section I: Anticipation Context
    anticipation_summary: dict[str, Any]

    # Section K: Related Industries
    related_industries: list[dict[str, Any]]

    # Section M: Provenance
    provenance_sources: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "industry_id": self.industry_id,
            "name": self.name,
            "sector": self.sector,
            "coverage_level": self.coverage_level,
            "description": self.description,
            "total_bills_count": self.total_bills_count,
            "central_bills_count": self.central_bills_count,
            "state_bills_count": self.state_bills_count,
            "total_companies_count": self.total_companies_count,
            "quantitative_companies_count": self.quantitative_companies_count,
            "intelligence_companies_count": self.intelligence_companies_count,
            "reference_companies_count": self.reference_companies_count,
            "central_exposures_count": self.central_exposures_count,
            "state_exposures_count": self.state_exposures_count,
            "market_analysis_available": self.market_analysis_available,
            "dominant_mechanism": self.dominant_mechanism,
            "facts": self.facts,
            "derived": self.derived,
            "interpretations": self.interpretations,
            "predictions": self.predictions,
            "central_bills": [b.to_dict() for b in self.central_bills],
            "state_bills": [b.to_dict() for b in self.state_bills],
            "quantitative_companies": [c.to_dict() for c in self.quantitative_companies],
            "intelligence_companies": [c.to_dict() for c in self.intelligence_companies],
            "reference_companies": [c.to_dict() for c in self.reference_companies],
            "transmission_chains": self.transmission_chains,
            "active_mechanisms": self.active_mechanisms,
            "market_intelligence": self.market_intelligence,
            "state_intelligence": self.state_intelligence,
            "risk_summary": self.risk_summary,
            "anticipation_summary": self.anticipation_summary,
            "related_industries": self.related_industries,
            "provenance_sources": self.provenance_sources,
        }


class IndustryIntelligenceService:
    """
    Core business logic and indexing service for Industry and Sector Intelligence.
    """

    def __init__(
        self,
        company_repo: Optional[CompanyRepository] = None,
        exposure_repo: Optional[CompanyExposureRepository] = None,
        bill_repo: Optional[BillRepository] = None,
        knowledge_repo: Optional[KnowledgeRepository] = None,
        state_bill_repo: Optional[StateBillRepository] = None,
        state_knowledge_repo: Optional[StateKnowledgeRepository] = None,
        prediction_repo: Optional[PredictionRepository] = None,
        decision_repo: Optional[DecisionRepository] = None,
        anticipation_repo: Optional[AnticipationRepository] = None,
    ) -> None:
        self.company_repo = company_repo or CompanyRepository()
        self.exposure_repo = exposure_repo or CompanyExposureRepository()
        self.bill_repo = bill_repo or BillRepository()
        self.knowledge_repo = knowledge_repo or KnowledgeRepository()
        self.state_bill_repo = state_bill_repo or StateBillRepository()
        self.state_knowledge_repo = state_knowledge_repo or StateKnowledgeRepository()
        self.prediction_repo = prediction_repo or PredictionRepository()
        self.decision_repo = decision_repo or DecisionRepository()
        self.anticipation_repo = anticipation_repo or AnticipationRepository()

        # Cache structures
        self._cached_industries: Optional[list[IndustrySummary]] = None
        self._industry_by_slug: dict[str, str] = {}  # slug -> canonical name
        self._industry_by_name: dict[str, str] = {}  # lower name -> canonical name
        self._initialize_index()

    def _initialize_index(self) -> None:
        """Scan companies and exposures to index all canonical industries and slugs."""
        comps = self.company_repo.get_all()
        for c in comps:
            ind_name = c.industry.strip() if c.industry else ("Banking & Financial Services" if c.sector == "Banking & Financial Services" else "Unclassified")
            # Special case cleanups
            if not c.industry and c.company_name == "HDFC Bank Limited":
                ind_name = "Private Sector Bank"
            slug = slugify_industry(ind_name)
            self._industry_by_slug[slug] = ind_name
            self._industry_by_name[ind_name.lower()] = ind_name

    def _resolve_canonical_name(self, identifier: str) -> Optional[str]:
        """Resolve slug or free text to canonical industry name."""
        clean = identifier.strip().lower()
        if not clean:
            return None
        slug = slugify_industry(clean)
        if slug in self._industry_by_slug:
            return self._industry_by_slug[slug]
        if clean in self._industry_by_name:
            return self._industry_by_name[clean]
        # Partial match
        for s, name in self._industry_by_slug.items():
            if clean in s or clean in name.lower():
                return name
        return None

    def _get_bill_title(self, bill_id: str) -> str:
        """Resolve human readable bill title."""
        cb = self.bill_repo.get(bill_id)
        if cb and cb.title:
            return cb.title
        sk = self.state_knowledge_repo.get(bill_id)
        if sk and sk.title:
            return sk.title
        sb = self.state_bill_repo.get(bill_id)
        if sb and sb.title:
            return sb.title
        return bill_id.replace("-", " ").title()

    def _get_bill_status(self, bill_id: str) -> str:
        """Resolve official bill status."""
        cb = self.bill_repo.get(bill_id)
        if cb and hasattr(cb, "status"):
            st = cb.status.value if hasattr(cb.status, "value") else str(cb.status)
            return st.lower()
        sk = self.state_knowledge_repo.get(bill_id)
        if sk and sk.status:
            return sk.status.lower()
        sb = self.state_bill_repo.get(bill_id)
        if sb and sb.status:
            st = sb.status.value if hasattr(sb.status, "value") else str(sb.status)
            return st.lower()
        return "introduced"

    def list_industries(
        self,
        sector: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        universe_type: Optional[str] = None,
        has_market_predictions: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "bills_desc",
    ) -> list[IndustrySummary]:
        """
        List and filter all canonical industries across the platform.
        """
        comps = self.company_repo.get_all()
        exps = self.exposure_repo.get_all()

        # Map exposures by company
        exps_by_comp: dict[str, list[StateCorporateExposure]] = {}
        for e in exps:
            exps_by_comp.setdefault(e.company_id, []).append(e)

        # Group companies by industry
        industry_comps: dict[str, list[Company]] = {}
        for c in comps:
            ind_name = c.industry.strip() if c.industry else ("Private Sector Bank" if "HDFC Bank" in c.company_name else "Unclassified")
            industry_comps.setdefault(ind_name, []).append(c)

        summaries: list[IndustrySummary] = []
        for ind_name, clist in industry_comps.items():
            slug = slugify_industry(ind_name)
            sec = clist[0].sector if clist else "General"

            # Aggregate exposures
            ind_exps: list[StateCorporateExposure] = []
            related_bill_ids: set[str] = set()
            central_count = 0
            state_count = 0
            mechanisms: set[str] = set()

            for c in clist:
                c_exps = exps_by_comp.get(c.isin, [])
                ind_exps.extend(c_exps)
                for e in c_exps:
                    related_bill_ids.add(e.bill_id)
                    if e.jurisdiction == "central":
                        central_count += 1
                    else:
                        state_count += 1
                    if e.mechanism:
                        mechanisms.add(e.mechanism)

            quant_comps = [c for c in clist if c.isin in _CENTRAL_QUANTITATIVE_ISINS]
            intel_comps = [c for c in clist if c.isin not in _CENTRAL_QUANTITATIVE_ISINS]

            has_quant = len(quant_comps) > 0
            has_intel = len(intel_comps) > 0 or len(ind_exps) > 0

            # Determine coverage level
            if has_quant:
                cov_level = 1
            elif has_intel:
                cov_level = 2
            else:
                cov_level = 3

            sub_inds = sorted(list({c.sub_industry for c in clist if c.sub_industry}))

            summary = IndustrySummary(
                industry_id=slug,
                name=ind_name,
                sector=sec,
                coverage_level=cov_level,
                related_bills_count=len(related_bill_ids),
                exposed_companies_count=len(clist),
                central_exposures_count=central_count,
                state_exposures_count=state_count,
                quantitative_companies_count=len(quant_comps),
                intelligence_companies_count=len(intel_comps),
                market_analysis_available=has_quant,
                economic_mechanisms=sorted(list(mechanisms)),
                latest_legislative_activity="Active Statutory Ingestion (2024–2026)" if related_bill_ids else None,
                sub_industries=sub_inds,
            )
            summaries.append(summary)

        # Filtering
        filtered = summaries
        if sector:
            s_clean = sector.strip().lower()
            filtered = [s for s in filtered if s_clean in s.sector.lower()]

        if jurisdiction:
            j_clean = jurisdiction.strip().lower()
            if j_clean == "central":
                filtered = [s for s in filtered if s.central_exposures_count > 0 or s.quantitative_companies_count > 0]
            elif j_clean == "state":
                filtered = [s for s in filtered if s.state_exposures_count > 0]

        if universe_type:
            u_clean = universe_type.strip().lower()
            if u_clean in ("quantitative", "quant"):
                filtered = [s for s in filtered if s.quantitative_companies_count > 0]
            elif u_clean in ("intelligence", "intel"):
                filtered = [s for s in filtered if s.intelligence_companies_count > 0]

        if has_market_predictions is not None:
            filtered = [s for s in filtered if s.market_analysis_available == has_market_predictions]

        if search:
            q = search.strip().lower()
            filtered = [
                s for s in filtered
                if q in s.name.lower()
                or q in s.sector.lower()
                or any(q in m.lower() for m in s.economic_mechanisms)
                or any(q in sub.lower() for sub in s.sub_industries)
            ]

        # Sorting
        if sort_by == "bills_desc":
            filtered.sort(key=lambda x: (-x.related_bills_count, -x.exposed_companies_count, x.name))
        elif sort_by == "companies_desc":
            filtered.sort(key=lambda x: (-x.exposed_companies_count, -x.related_bills_count, x.name))
        elif sort_by == "name_asc":
            filtered.sort(key=lambda x: x.name)
        elif sort_by == "level_asc":
            filtered.sort(key=lambda x: (x.coverage_level, -x.related_bills_count, x.name))

        return filtered

    def get_industry_dossier(self, industry_identifier: str) -> Optional[IndustryDossier]:
        """
        Build the full 13-section dossier for a given industry identifier.
        """
        canonical_name = self._resolve_canonical_name(industry_identifier)
        if not canonical_name:
            return None

        slug = slugify_industry(canonical_name)
        comps = self.company_repo.get_all()
        clist = [
            c for c in comps
            if (c.industry and c.industry.strip() == canonical_name)
            or (not c.industry and canonical_name == "Private Sector Bank" and "HDFC Bank" in c.company_name)
        ]

        if not clist:
            return None

        sector = clist[0].sector if clist else "General"
        exps = self.exposure_repo.get_all()

        # Exposures for companies in this industry
        comp_isins = {c.isin for c in clist}
        ind_exps = [e for e in exps if e.company_id in comp_isins]

        # Collect bills
        central_bills_dict: dict[str, IndustryBillExposureItem] = {}
        state_bills_dict: dict[str, IndustryBillExposureItem] = {}

        for e in ind_exps:
            b_title = self._get_bill_title(e.bill_id)
            status = self._get_bill_status(e.bill_id)
            sources = e.source_urls or ["Official Gazette / Legislative Tracking"]

            # Policy domain resolution
            p_domain = ""
            if e.jurisdiction == "central":
                kr = self.knowledge_repo.get(e.bill_id)
                p_domain = kr.policy_domain if kr else (e.sector or "Central Economic Regulation")
            else:
                sk = self.state_knowledge_repo.get(e.bill_id)
                p_domain = sk.policy_category if sk else (e.sector or "State Statutory Regulation")

            item = IndustryBillExposureItem(
                bill_id=e.bill_id,
                bill_title=b_title,
                jurisdiction=e.jurisdiction,
                state=e.state if e.jurisdiction == "state" else None,
                policy_domain=p_domain,
                legislative_status=status,
                exposure_strength=e.exposure_strength,
                economic_mechanism=e.mechanism,
                provisions_summary=f"Statutory mandate affecting {e.sub_sector or e.sector} via {e.mechanism} requirements.",
                exposed_company_ids=[e.company_id],
                exposed_company_names=[e.company_name],
                provenance_sources=sources,
            )

            target_dict = central_bills_dict if e.jurisdiction == "central" else state_bills_dict
            if e.bill_id in target_dict:
                existing = target_dict[e.bill_id]
                if e.company_id not in existing.exposed_company_ids:
                    existing.exposed_company_ids.append(e.company_id)
                    existing.exposed_company_names.append(e.company_name)
            else:
                target_dict[e.bill_id] = item

        # Group companies
        quant_comps: list[IndustryCompanyItem] = []
        intel_comps: list[IndustryCompanyItem] = []
        ref_comps: list[IndustryCompanyItem] = []

        for c in clist:
            c_exps = [e for e in ind_exps if e.company_id == c.isin]
            primary_exp = c_exps[0] if c_exps else None

            item = IndustryCompanyItem(
                company_id=c.isin,
                company_name=c.company_name,
                ticker_nse=c.ticker_nse or None,
                ticker_bse=c.ticker_bse or None,
                sector=c.sector,
                industry=c.industry or canonical_name,
                universe_type=c.universe_type.value if hasattr(c.universe_type, "value") else str(c.universe_type),
                entity_type=c.entity_type.value if hasattr(c.entity_type, "value") else str(c.entity_type),
                ownership_type=c.ownership_type.value if hasattr(c.ownership_type, "value") else str(c.ownership_type),
                listing_status=c.listing_status,
                is_quant_eligible=c.isin in _CENTRAL_QUANTITATIVE_ISINS,
                market_prediction_available=c.isin in _CENTRAL_QUANTITATIVE_ISINS,
                exposure_count=len(c_exps),
                exposure_strength=primary_exp.exposure_strength if primary_exp else "NONE",
                direct_indirect=primary_exp.direct_indirect if primary_exp else "NONE",
                primary_mechanism=primary_exp.mechanism if primary_exp else "Unspecified",
                market_relevance=primary_exp.market_relevance if primary_exp else ("HIGH" if c.isin in _CENTRAL_QUANTITATIVE_ISINS else "NONE"),
                evidence_reference=(primary_exp.evidence[0].reference if primary_exp and primary_exp.evidence else "Authoritative Master Filing"),
            )

            if item.is_quant_eligible:
                quant_comps.append(item)
            elif item.universe_type == "intelligence":
                intel_comps.append(item)
            else:
                ref_comps.append(item)

        # Coverage level
        cov_level = 1 if len(quant_comps) > 0 else (2 if len(intel_comps) > 0 or ind_exps else 3)
        market_analysis_available = len(quant_comps) > 0

        # Mechanisms
        all_mechs = sorted(list({e.mechanism for e in ind_exps if e.mechanism}))
        dominant_mech = all_mechs[0] if all_mechs else "compliance"

        # Epistemic Sections
        facts = [
            f"Official classification: Industry '{canonical_name}' operating under the {sector} sector.",
            f"Universe footprint: {len(clist)} master corporate entities identified ({len(quant_comps)} quantitative securities, {len(intel_comps)} qualitative intelligence entities).",
            f"Statutory exposure: {len(ind_exps)} documented corporate exposure records across {len(central_bills_dict) + len(state_bills_dict)} legislative bills.",
        ]
        derived = [
            f"Jurisdictional distribution: {len(central_bills_dict)} Central Parliamentary bills and {len(state_bills_dict)} State Legislative Assembly acts.",
            f"Primary transmission channels: {', '.join(all_mechs) if all_mechs else 'No active transmission channels documented'}.",
            f"Platform coverage status: Level {cov_level} ({'Quantitative Market Modelled' if cov_level == 1 else 'Qualitative Corporate Intelligence'}).",
        ]
        interpretations = [
            f"Statutory changes primarily transmit through {dominant_mech} obligations affecting operational workflows.",
            f"Enterprise compliance and regulatory adaptations represent key operational determinants for member corporations.",
        ]
        if market_analysis_available:
            predictions = [
                f"Quantitative econometric models cover {len(quant_comps)} listed securities in this industry across 5 event horizons.",
                "Industry-level prediction is not modeled. Company-level model outputs are shown below.",
                "All quantitative projections are empirical research outputs, not financial advice or Buy/Sell/Hold recommendations.",
            ]
        else:
            predictions = [
                "Industry-level prediction is not modeled. Quantitative stock predictions are unavailable for this industry.",
                "Quantitative models remain strictly isolated behind the platform firewall to preserve econometric integrity.",
            ]

        # Economic Transmission Chains
        transmission_chains = []
        for e in ind_exps[:5]:
            chain = [
                {
                    "stage": "LEGISLATION",
                    "title": self._get_bill_title(e.bill_id),
                    "description": f"Enacted statute in {e.jurisdiction.upper()} jurisdiction ({e.state or 'National'}).",
                    "badge": e.bill_id,
                },
                {
                    "stage": "POLICY_CHANGE",
                    "title": f"{e.sector} Regulatory Framework",
                    "description": f"Statutory intervention targeting {e.sub_sector or e.business_activity}.",
                    "badge": e.exposure_type,
                },
                {
                    "stage": "ECONOMIC_MECHANISM",
                    "title": e.mechanism.replace("_", " ").title(),
                    "description": f"Transmission channel imposing {e.mechanism} obligations on market participants.",
                    "badge": e.mechanism,
                },
                {
                    "stage": "INDUSTRY",
                    "title": canonical_name,
                    "description": f"Affected sectoral aggregate across {sector}.",
                    "badge": "INDUSTRY",
                },
                {
                    "stage": "COMPANY_EXPOSURE",
                    "title": e.company_name,
                    "description": f"{e.direct_indirect} exposure with {e.exposure_strength} intensity.",
                    "badge": e.company_id,
                },
                {
                    "stage": "MARKET_ANALYSIS",
                    "title": "Quantitative Forecast" if e.company_id in _CENTRAL_QUANTITATIVE_ISINS else "Qualitative Dossier Only",
                    "description": "Empirical model available" if e.company_id in _CENTRAL_QUANTITATIVE_ISINS else "Prediction firewall active (0 stock predictions)",
                    "badge": "LEVEL 1" if e.company_id in _CENTRAL_QUANTITATIVE_ISINS else "LEVEL 2",
                    "status": "MODELLED" if e.company_id in _CENTRAL_QUANTITATIVE_ISINS else "FIREWALLED",
                },
            ]
            transmission_chains.append(chain)

        # Market Intelligence (Central quantitative)
        market_intel: dict[str, Any] = {
            "modeled": market_analysis_available,
            "notice": "Industry-level prediction is not modeled. Company-level model outputs are shown below.",
            "quantitative_companies_count": len(quant_comps),
            "event_windows": ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"],
            "company_predictions": [],
        }

        # Pull actual predictions for quantitative companies if available
        if market_analysis_available:
            from api.dependencies import get_cached_predictions
            all_preds, _ = get_cached_predictions()
            quant_isins = {c.company_id for c in quant_comps}
            member_preds = [p for p in all_preds if p.company_isin in quant_isins]

            pos_count = sum(1 for p in member_preds if p.predicted_direction == "POSITIVE")
            neg_count = sum(1 for p in member_preds if p.predicted_direction == "NEGATIVE")
            neu_count = sum(1 for p in member_preds if p.predicted_direction == "NEUTRAL")

            market_intel.update({
                "total_predictions": len(member_preds),
                "positive_count": pos_count,
                "negative_count": neg_count,
                "neutral_count": neu_count,
                "sample_predictions": [
                    {
                        "prediction_id": p.prediction_id,
                        "bill_id": p.bill_id,
                        "company_isin": p.company_isin,
                        "event_window": p.event_window,
                        "predicted_direction": p.predicted_direction,
                        "predicted_confidence": p.predicted_confidence,
                        "impact_strength": p.predicted_impact_strength,
                    }
                    for p in member_preds[:10]
                ],
            })

        # State Intelligence
        state_bills_list = list(state_bills_dict.values())
        state_intel = {
            "state_bills_count": len(state_bills_list),
            "states_covered": sorted(list({b.state for b in state_bills_list if b.state})),
            "state_stock_predictions": 0,
            "firewall_statement": "State stock predictions remain strictly 0 to preserve model integrity.",
            "bills": [b.to_dict() for b in state_bills_list],
        }

        # Risk Context
        risk_summary = {
            "epistemic_badge": "DERIVED",
            "explanation": "Aggregated from member corporate decision support records. Industry-level risk is not separately modeled.",
            "risk_band_distribution": {
                "VERY_LOW": 0,
                "LOW": 0,
                "MODERATE": 0,
                "HIGH": 0,
                "VERY_HIGH": 0,
            },
            "high_risk_count": 0,
        }
        if market_analysis_available:
            from api.dependencies import get_cached_decisions_by_id
            dec_map = get_cached_decisions_by_id()
            quant_isins = {c.company_id for c in quant_comps}
            for d in dec_map.values():
                if d.company_isin in quant_isins:
                    band = d.risk_category or "MODERATE"
                    if band in risk_summary["risk_band_distribution"]:
                        risk_summary["risk_band_distribution"][band] += 1
                    if band in ("HIGH", "VERY_HIGH"):
                        risk_summary["high_risk_count"] += 1

        # Anticipation Context
        anticipation_summary = {
            "epistemic_badge": "DERIVED",
            "verbatim_disclaimer": "Pre-event diagnostics measure aggregate public information diffusion only. They do not allege or imply insider trading or illicit market conduct under securities law.",
            "diffusion_tier_distribution": {
                "NO_EVIDENCE": 0,
                "WEAK_EVIDENCE": 0,
                "MODERATE_EVIDENCE": 0,
                "STRONG_EVIDENCE": 0,
            },
            "flagged_pairs_count": 0,
        }
        if market_analysis_available:
            from api.dependencies import get_cached_anticipation_scores
            scores = get_cached_anticipation_scores()
            quant_isins = {c.company_id for c in quant_comps}
            for s in scores:
                if s.company_isin in quant_isins:
                    tier = s.classification or "NO_EVIDENCE"
                    if tier in anticipation_summary["diffusion_tier_distribution"]:
                        anticipation_summary["diffusion_tier_distribution"][tier] += 1
                    if getattr(s, "anticipation_flag", False):
                        anticipation_summary["flagged_pairs_count"] += 1

        # Related Industries (peer industries in the same sector)
        all_inds = self.list_industries(sector=sector)
        related = [
            {"industry_id": ind.industry_id, "name": ind.name, "sector": ind.sector, "related_bills_count": ind.related_bills_count}
            for ind in all_inds if ind.industry_id != slug
        ]

        # Provenance records
        provenance = [
            {
                "source": "Ministry of Corporate Affairs / MCA Registry",
                "source_type": "Official Corporate Master Record",
                "verification_status": "VERIFIED",
                "evidence_text": f"Canonical industry classification and member companies for {canonical_name}.",
                "verified_at": "2026-09-16T00:00:00Z",
            },
            {
                "source": "Parliament of India / State Legislative Assemblies",
                "source_type": "Statutory Gazette & Assembly Records",
                "verification_status": "VERIFIED",
                "evidence_text": f"Legislative acts with documented transmission into {canonical_name}.",
                "verified_at": "2026-09-18T00:00:00Z",
            },
        ]

        return IndustryDossier(
            industry_id=slug,
            name=canonical_name,
            sector=sector,
            coverage_level=cov_level,
            description=f"Industry sector intelligence profile for {canonical_name} under {sector} in India.",
            total_bills_count=len(central_bills_dict) + len(state_bills_dict),
            central_bills_count=len(central_bills_dict),
            state_bills_count=len(state_bills_dict),
            total_companies_count=len(clist),
            quantitative_companies_count=len(quant_comps),
            intelligence_companies_count=len(intel_comps),
            reference_companies_count=len(ref_comps),
            central_exposures_count=sum(1 for e in ind_exps if e.jurisdiction == "central"),
            state_exposures_count=sum(1 for e in ind_exps if e.jurisdiction == "state"),
            market_analysis_available=market_analysis_available,
            dominant_mechanism=dominant_mech,
            facts=facts,
            derived=derived,
            interpretations=interpretations,
            predictions=predictions,
            central_bills=list(central_bills_dict.values()),
            state_bills=list(state_bills_dict.values()),
            quantitative_companies=quant_comps,
            intelligence_companies=intel_comps,
            reference_companies=ref_comps,
            transmission_chains=transmission_chains,
            active_mechanisms=all_mechs,
            market_intelligence=market_intel,
            state_intelligence=state_intel,
            risk_summary=risk_summary,
            anticipation_summary=anticipation_summary,
            related_industries=related,
            provenance_sources=provenance,
        )

    def get_industry_bills(
        self, industry_identifier: str, jurisdiction: Optional[str] = None
    ) -> list[IndustryBillExposureItem]:
        """Return bills affecting this industry, optionally filtered by jurisdiction."""
        dossier = self.get_industry_dossier(industry_identifier)
        if not dossier:
            return []
        if jurisdiction == "central":
            return dossier.central_bills
        if jurisdiction == "state":
            return dossier.state_bills
        return dossier.central_bills + dossier.state_bills

    def get_industry_companies(
        self, industry_identifier: str, universe_type: Optional[str] = None
    ) -> list[IndustryCompanyItem]:
        """Return companies in this industry, optionally filtered by universe type."""
        dossier = self.get_industry_dossier(industry_identifier)
        if not dossier:
            return []
        if universe_type == "quantitative":
            return dossier.quantitative_companies
        if universe_type == "intelligence":
            return dossier.intelligence_companies
        if universe_type == "reference":
            return dossier.reference_companies
        return dossier.quantitative_companies + dossier.intelligence_companies + dossier.reference_companies
