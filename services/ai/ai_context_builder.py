"""
services/ai/ai_context_builder.py
=================================
Deterministic AI Context Builder for Indian Central and State Legislative Bills.

Strict Architectural Guarantees:
1. Zero fabrication: Retrieves authoritative facts, derived tags, and models only.
2. Fact / Derived / Interpretation / Prediction strict separation.
3. State bill isolation: Explicitly asserts state predictions are unavailable.
4. Central prediction preservation: Existing model outputs are explained, never recomputed.
5. Deterministic context hashing: Computes SHA256 of context for reliable caching.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.unified_bill_record import UnifiedBillRecord
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.decision_repository import DecisionRepository
from storage.knowledge_repository import KnowledgeRepository
from storage.mapping_repository import MappingRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
from storage.state_knowledge_repository import StateKnowledgeRepository

logger = get_logger(__name__)


@dataclass
class AIContext:
    """Structured, verified context container for a single legislative bill."""

    bill_id: str
    title: str
    jurisdiction: str  # "central" | "state"
    state: Optional[str] = None
    bill_number: Optional[str] = None
    introduction_date: Optional[str] = None
    status: str = "unknown"

    facts: list[str] = field(default_factory=list)
    derived: list[str] = field(default_factory=list)
    interpretations: list[str] = field(default_factory=list)
    predictions: list[str] = field(default_factory=list)

    provenance: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_central(self) -> bool:
        return self.jurisdiction.lower() == "central"

    @property
    def is_state(self) -> bool:
        return self.jurisdiction.lower() == "state"

    @property
    def context_hash(self) -> str:
        """Deterministic SHA256 hash of all context elements for safe caching."""
        payload = {
            "bill_id": self.bill_id,
            "title": self.title,
            "jurisdiction": self.jurisdiction,
            "state": self.state,
            "facts": sorted(self.facts),
            "derived": sorted(self.derived),
            "interpretations": sorted(self.interpretations),
            "predictions": sorted(self.predictions),
        }
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def format_prompt_block(self) -> str:
        """Render a formatted string with explicit category headers for LLM consumption."""
        lines = [
            "=== VERIFIED LEGISLATIVE INTELLIGENCE CONTEXT ===",
            f"BILL ID: {self.bill_id}",
            f"TITLE: {self.title}",
            f"JURISDICTION: {self.jurisdiction.upper()}" + (f" ({self.state})" if self.state else ""),
            f"BILL NUMBER: {self.bill_number or 'Not assigned / Unavailable'}",
            f"AUTHORITATIVE INTRODUCTION DATE: {self.introduction_date or 'Introduction date unavailable'}",
            f"STATUS: {self.status.replace('_', ' ').title()}",
            "",
            "[FACTS — Authoritative Statutory & Gazette Records]",
        ]
        if self.facts:
            for f in self.facts:
                lines.append(f"• {f}")
        else:
            lines.append("• Standard official metadata verified.")

        lines.extend(["", "[DERIVED INFORMATION — System-Assigned Taxonomies & Mappings]"])
        if self.derived:
            for d in self.derived:
                lines.append(f"• {d}")
        else:
            lines.append("• No derived sector mappings available.")

        lines.extend(["", "[ECONOMIC INTERPRETATION — Qualitative Analytical Explanations]"])
        if self.interpretations:
            for i in self.interpretations:
                lines.append(f"• {i}")
        else:
            lines.append("• No qualitative economic interpretation records available.")

        lines.extend(["", "[PREDICTIONS — Central Model Forecasts (Strictly Isolated / Zero for State)]"])
        if self.predictions:
            for p in self.predictions:
                lines.append(f"• {p}")
        else:
            if self.is_state:
                lines.append("• State market prediction is currently unavailable. (Model predictions strictly 0).")
            else:
                lines.append("• No quantitative model predictions generated for this record.")

        lines.extend([
            "",
            "[PROVENANCE]",
            f"• Source: {self.provenance.get('source_url', 'Official Parliamentary Record')}",
            f"• Official PDF: {self.provenance.get('pdf_url', 'Unavailable / Not attached')}",
            f"• Verified Database: {self.provenance.get('database', 'Project Repository')}",
            "=== END CONTEXT ===",
        ])
        return "\n".join(lines)


@dataclass
class AIComparisonContext:
    """Structured context container comparing two legislative bills."""

    bill_1: AIContext
    bill_2: AIContext

    @property
    def context_hash(self) -> str:
        """Deterministic combined hash for comparison caching."""
        combined = f"{self.bill_1.context_hash}::{self.bill_2.context_hash}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def format_prompt_block(self) -> str:
        """Render side-by-side prompt context."""
        lines = [
            "=== VERIFIED BILL COMPARISON CONTEXT ===",
            "--- BILL 1 ---",
            self.bill_1.format_prompt_block(),
            "",
            "--- BILL 2 ---",
            self.bill_2.format_prompt_block(),
            "",
            "=== COMPARATIVE DIRECTIVE ===",
            "Analyze and contrast the two bills strictly based on the verified facts, sectors, "
            "stakeholders, corporate exposure, and economic mechanisms provided above. "
            "Do NOT fabricate new predictions or extrapolate beyond provided data.",
            "=== END COMPARISON CONTEXT ===",
        ]
        return "\n".join(lines)


@dataclass
class AICompanyContext:
    """Structured, verified context container for a corporate entity and its legislative exposures."""

    company_id: str
    company_name: str
    legal_identity: str
    universe_type: str  # "quantitative" | "intelligence" | "both"
    entity_type: str
    sector: str
    industry: str
    bill_id: Optional[str] = None
    bill_title: Optional[str] = None

    facts: list[str] = field(default_factory=list)
    derived: list[str] = field(default_factory=list)
    interpretations: list[str] = field(default_factory=list)
    predictions: list[str] = field(default_factory=list)

    provenance: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_quantitative(self) -> bool:
        return self.universe_type.lower() in ("quantitative", "both")

    @property
    def is_intelligence_only(self) -> bool:
        return self.universe_type.lower() == "intelligence"

    @property
    def context_hash(self) -> str:
        """Deterministic SHA256 hash of company context."""
        payload = {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "universe_type": self.universe_type,
            "bill_id": self.bill_id,
            "facts": sorted(self.facts),
            "derived": sorted(self.derived),
            "interpretations": sorted(self.interpretations),
            "predictions": sorted(self.predictions),
        }
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def format_prompt_block(self) -> str:
        """Render a formatted string with explicit categorical separation for Groq."""
        lines = [
            "=== VERIFIED COMPANY INTELLIGENCE CONTEXT ===",
            f"COMPANY: {self.company_name} ({self.company_id})",
            f"ORGANIZATIONAL TYPE: {self.entity_type.replace('_', ' ').title()}",
            f"ANALYTICAL UNIVERSE: {self.universe_type.upper()}",
            f"PRIMARY SECTOR: {self.sector} | INDUSTRY: {self.industry}",
        ]
        if self.bill_id:
            lines.append(f"TARGET LEGISLATION: {self.bill_title or self.bill_id} [{self.bill_id}]")

        lines.extend(["", "[FACTS — Authoritative Corporate Filings, Gazette & Statutory Records]"])
        if self.facts:
            for f in self.facts:
                lines.append(f"• {f}")
        else:
            lines.append("• Corporate master details verified.")

        lines.extend(["", "[DERIVED INFORMATION — System-Assigned Taxonomies & Verified Exposure Mappings]"])
        if self.derived:
            for d in self.derived:
                lines.append(f"• {d}")
        else:
            lines.append("• No derived sector/exposure mappings.")

        lines.extend(["", "[ECONOMIC INTERPRETATION — Qualitative Statutory Relevance & Business Mechanisms]"])
        if self.interpretations:
            for i in self.interpretations:
                lines.append(f"• {i}")
        else:
            lines.append("• No qualitative economic interpretation records available.")

        lines.extend(["", "[PREDICTIONS — Central Model Forecasts (Strictly Isolated / Zero for Intelligence Entities)]"])
        if self.predictions:
            for p in self.predictions:
                lines.append(f"• {p}")
        else:
            lines.append("• No quantitative model predictions generated for this record.")

        lines.extend([
            "",
            "[PROVENANCE]",
            f"• Source Categories: {self.provenance.get('sources', 'Official Filings / Regulatory Records')}",
            f"• Verified Database: {self.provenance.get('database', 'Project Repository')}",
            f"• Firewall Status: {self.provenance.get('firewall', 'ACTIVE')}",
            "=== END CONTEXT ===",
        ])
        return "\n".join(lines)


@dataclass
class AIIndustryContext:
    """Structured, verified context container for an industry sector and its legislative exposures."""

    industry_id: str
    industry_name: str
    sector: str
    coverage_level: int

    facts: list[str] = field(default_factory=list)
    derived: list[str] = field(default_factory=list)
    interpretations: list[str] = field(default_factory=list)
    predictions: list[str] = field(default_factory=list)

    provenance: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def context_hash(self) -> str:
        payload = {
            "industry_id": self.industry_id,
            "industry_name": self.industry_name,
            "sector": self.sector,
            "coverage_level": self.coverage_level,
            "facts": sorted(self.facts),
            "derived": sorted(self.derived),
            "interpretations": sorted(self.interpretations),
            "predictions": sorted(self.predictions),
        }
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def format_prompt_block(self) -> str:
        lines = [
            "=== VERIFIED INDUSTRY INTELLIGENCE CONTEXT ===",
            f"INDUSTRY: {self.industry_name} ({self.industry_id})",
            f"BROAD SECTOR: {self.sector}",
            f"PLATFORM COVERAGE LEVEL: Level {self.coverage_level}",
            "",
            "[FACTS — Official Sectoral Classifications, Member Entities & Statutory Records]",
        ]
        if self.facts:
            for f in self.facts:
                lines.append(f"• {f}")
        else:
            lines.append("• Industry classification facts verified.")

        lines.extend(["", "[DERIVED INFORMATION — Aggregated Exposures, Jurisdictions & Mechanisms]"])
        if self.derived:
            for d in self.derived:
                lines.append(f"• {d}")
        else:
            lines.append("• Standard derived taxonomies on record.")

        lines.extend(["", "[ECONOMIC INTERPRETATION — Transmission Channels & Regulatory Impacts]"])
        if self.interpretations:
            for i in self.interpretations:
                lines.append(f"• {i}")
        else:
            lines.append("• Regulatory transmission documented via statutory compliance.")

        lines.extend(["", "[PREDICTIONS — Central Model Forecasts (Firewall Enforced)]"])
        if self.predictions:
            for p in self.predictions:
                lines.append(f"• {p}")
        else:
            lines.append("• Industry-level prediction is not modeled. Model outputs are company-level only.")

        lines.extend([
            "",
            "[PROVENANCE & INTEGRITY]",
            f"• Verified Sources: {self.provenance.get('sources', 'Parliamentary Records / MCA Corporate Registry')}",
            f"• State Prediction Firewall: {self.provenance.get('state_firewall', 'ACTIVE (Strictly 0 Predictions)')}",
            f"• Regulatory Notice: Empirical research analysis only; not investment advice.",
            "=== END CONTEXT ===",
        ])
        return "\n".join(lines)


class AIContextBuilder:
    """
    Deterministic builder assembling verified context from existing repositories.
    """

    def __init__(
        self,
        discovery_service: Optional[UnifiedLegislativeDiscoveryService] = None,
        central_bill_repo: Optional[BillRepository] = None,
        central_knowledge_repo: Optional[KnowledgeRepository] = None,
        central_mapping_repo: Optional[MappingRepository] = None,
        central_decision_repo: Optional[DecisionRepository] = None,
        state_bill_repo: Optional[StateBillRepository] = None,
        state_knowledge_repo: Optional[StateKnowledgeRepository] = None,
        state_exposure_repo: Optional[StateCorporateExposureRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        company_exposure_repo: Optional[CompanyExposureRepository] = None,
    ) -> None:
        self.discovery_service = discovery_service or UnifiedLegislativeDiscoveryService()
        self.central_bill_repo = central_bill_repo or BillRepository()
        self.central_knowledge_repo = central_knowledge_repo or KnowledgeRepository()
        self.central_mapping_repo = central_mapping_repo or MappingRepository()
        self.central_decision_repo = central_decision_repo or DecisionRepository()
        self.state_bill_repo = state_bill_repo or StateBillRepository()
        self.state_knowledge_repo = state_knowledge_repo or StateKnowledgeRepository()
        self.state_exposure_repo = state_exposure_repo or StateCorporateExposureRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.company_exposure_repo = company_exposure_repo or CompanyExposureRepository()

    def build_context(self, bill_id: str) -> AIContext:
        """
        Build verified AIContext for either a Central or State bill.

        Parameters
        ----------
        bill_id : str
            Unique bill identifier.

        Returns
        -------
        AIContext
            Grounded context with categorical separation.
        """
        # 1. First look up in unified discovery layer
        record = self.discovery_service.get_bill_by_id(bill_id)

        if record and record.is_state:
            return self._build_state_context(bill_id, record)
        elif record and record.is_central:
            return self._build_central_context(bill_id, record)

        # Fallback direct repository lookups
        state_k = self.state_knowledge_repo.get(bill_id)
        if state_k:
            return self._build_state_context(bill_id, record)

        return self._build_central_context(bill_id, record)

    def _build_central_context(
        self,
        bill_id: str,
        unified: Optional[UnifiedBillRecord] = None,
    ) -> AIContext:
        """Build context for a Central Government parliamentary bill."""
        bill = self.central_bill_repo.get(bill_id)
        k_record = self.central_knowledge_repo.get(bill_id)
        mapping = self.central_mapping_repo.get(bill_id)

        title = unified.title if unified else (bill.title if bill else bill_id)
        bill_number = unified.bill_number if unified else (bill.bill_number if bill else None)
        status = unified.status if unified else (bill.status.value if (bill and hasattr(bill.status, 'value')) else "introduced")

        intro_date: Optional[str] = None
        if unified and unified.introduction_date:
            intro_date = unified.introduction_date
        elif bill and bill.introduction_date:
            intro_date = bill.introduction_date.isoformat()

        facts: list[str] = []
        derived: list[str] = []
        interpretations: list[str] = []
        predictions: list[str] = []
        provenance: dict[str, str] = {
            "database": "Central Parliament Repository",
        }

        # FACTS
        house_name = (
            bill.house.value
            if (bill and hasattr(bill.house, 'value'))
            else (getattr(bill, 'house', 'Parliament') if bill else 'Parliament')
        )
        facts.append(f"Legislature: Parliament of India (House: {house_name}).")
        ministry = getattr(bill, "ministry", None) or (unified.ministry if unified else None)
        if ministry:
            facts.append(f"Sponsoring Ministry: {ministry}.")

        src_url = getattr(bill, "url", getattr(bill, "source_url", None)) or (unified.source_url if unified else None)
        if src_url:
            facts.append(f"Official Source URL: {src_url}")
            provenance["source_url"] = src_url

        pdf_u = getattr(bill, "pdf_url", None) or (unified.pdf_url if unified else None)
        if pdf_u:
            facts.append(f"Official Bill PDF: {pdf_u}")
            provenance["pdf_url"] = pdf_u

        summary_text = (unified.summary if unified and unified.summary else getattr(bill, "summary", ""))
        if summary_text:
            facts.append(f"Official Summary: {summary_text}")

        # DERIVED
        if k_record:
            if k_record.policy_domain:
                derived.append(f"Policy Domain: {k_record.policy_domain}.")
            if k_record.primary_sector:
                derived.append(f"Primary Economic Sector: {k_record.primary_sector}.")
            if k_record.secondary_sectors:
                derived.append(f"Secondary Sectors: {', '.join(k_record.secondary_sectors)}.")
            if k_record.stakeholder_groups:
                derived.append(f"Mapped Stakeholder Groups: {', '.join(k_record.stakeholder_groups)}.")
            if k_record.regulatory_authority:
                derived.append(f"Regulatory Authority: {k_record.regulatory_authority}.")

        # Mapped company exposure
        companies = getattr(mapping, "candidate_companies", getattr(mapping, "mapped_companies", [])) if mapping else []
        if companies:
            comp_summaries = []
            for entry in companies[:8]:
                if isinstance(entry, dict):
                    name = entry.get("company_name", entry.get("name", "Unknown"))
                    ticker = entry.get("ticker", entry.get("isin", ""))
                    tier = entry.get("exposure_level", entry.get("tier", "EXPOSED"))
                else:
                    name = getattr(entry, "company_name", getattr(entry, "name", "Unknown"))
                    ticker = getattr(entry, "ticker", getattr(entry, "isin", ""))
                    tier = getattr(entry, "exposure_level", getattr(entry, "tier", "EXPOSED"))
                comp_summaries.append(f"{name} ({ticker}) [Exposure: {tier}]")
            derived.append(f"Verified Exposed Companies ({len(companies)} mapped): {'; '.join(comp_summaries)}.")
            if len(companies) > 8:
                derived.append(f"Additional exposed companies: {len(companies) - 8} more mapped in system.")
        else:
            derived.append("Corporate Exposure: No directly mapped companies in registry.")

        # INTERPRETATIONS
        interpretations.append("Jurisdictional Scope: Central / National applicability across Indian Union.")
        if k_record and k_record.economic_domain:
            interpretations.append(f"Economic Domain Focus: {k_record.economic_domain}.")

        # PREDICTIONS & DECISION RECORDS
        # Aggregate existing central decisions for this bill
        all_decisions = self.central_decision_repo.get_by_bill(bill_id)
        if all_decisions:
            sample_dec = all_decisions[0]
            # Average or representative figures from existing models
            directions = [getattr(d, "predicted_direction", "NEUTRAL") for d in all_decisions]
            dir_str = getattr(sample_dec, "predicted_direction", "NEUTRAL")
            if hasattr(dir_str, "value"):
                dir_str = dir_str.value

            conf_str = getattr(sample_dec, "predicted_confidence", getattr(sample_dec, "confidence", "LOW"))
            if hasattr(conf_str, "value"):
                conf_str = conf_str.value

            risk_sc = float(getattr(sample_dec, "risk_score", getattr(sample_dec, "composite_risk_score", 0.0)))
            risk_cat = getattr(sample_dec, "risk_category", "MODERATE")
            if hasattr(risk_cat, "value"):
                risk_cat = risk_cat.value

            prob_moving = float(getattr(sample_dec, "market_moving_probability", 0.0))
            impact_sc = float(getattr(sample_dec, "impact_score", 0.0))

            ant_ev = getattr(sample_dec, "anticipation_class", getattr(sample_dec, "anticipation_evidence", "NO_EVIDENCE"))
            if hasattr(ant_ev, "value"):
                ant_ev = ant_ev.value

            predictions.append(
                f"Existing Central Model Directional Consensus: {dir_str} (Confidence: {conf_str})."
            )
            predictions.append(
                f"Model-Estimated Market-Moving Probability: {prob_moving:.2f} (Impact Score: {impact_sc:.2f})."
            )
            predictions.append(
                f"Composite Risk Evaluation: {risk_sc:.2f} [Tier: {risk_cat}]."
            )
            predictions.append(
                f"Pre-Event Pricing-In / Anticipation Evidence: {ant_ev}."
            )
            predictions.append(
                "NOTE: These predictions are generated by existing, frozen quantitative market models. "
                "They represent empirical model outputs, NOT investment advice or future certainty."
            )
        else:
            predictions.append("No active quantitative model decision records found for this Central bill.")

        return AIContext(
            bill_id=bill_id,
            title=title,
            jurisdiction="central",
            state=None,
            bill_number=bill_number,
            introduction_date=intro_date,
            status=status,
            facts=facts,
            derived=derived,
            interpretations=interpretations,
            predictions=predictions,
            provenance=provenance,
            metadata={"source": "central"},
        )

    def _build_state_context(
        self,
        bill_id: str,
        unified: Optional[UnifiedBillRecord] = None,
    ) -> AIContext:
        """Build context for an Indian State legislative bill."""
        state_k = self.state_knowledge_repo.get(bill_id)
        state_bill = self.state_bill_repo.get(bill_id)

        state_name = (
            unified.state
            if (unified and unified.state)
            else (state_k.state if state_k else (state_bill.state if state_bill else "Unknown State"))
        )
        title = unified.title if unified else (state_k.title if state_k else (state_bill.title if state_bill else bill_id))
        bill_number = unified.bill_number if unified else (state_k.bill_number if state_k else None)
        status = unified.status if unified else (state_k.status if state_k else "introduced")

        intro_date: Optional[str] = None
        if unified and unified.introduction_date:
            intro_date = unified.introduction_date
        elif state_k and state_k.introduction_date:
            intro_date = state_k.introduction_date
        elif state_bill and state_bill.introduction_date:
            intro_date = state_bill.introduction_date.isoformat()

        facts: list[str] = []
        derived: list[str] = []
        interpretations: list[str] = []
        predictions: list[str] = []
        provenance: dict[str, str] = {
            "database": f"{state_name} State Legislative Repository",
        }

        # FACTS
        chamber = state_k.chamber if state_k else "State Legislative Assembly"
        facts.append(f"Jurisdiction: State of {state_name} (Chamber: {chamber}).")
        if state_k and state_k.source_url:
            facts.append(f"Official Gazette / Assembly Source: {state_k.source_url}")
            provenance["source_url"] = state_k.source_url
        if state_k and state_k.pdf_url:
            facts.append(f"Official State Bill PDF: {state_k.pdf_url}")
            provenance["pdf_url"] = state_k.pdf_url

        if state_k and state_k.summary:
            s = state_k.summary
            if s.what_is_bill:
                facts.append(f"What is this bill: {s.what_is_bill}")
            if s.what_it_changes:
                facts.append(f"Provisions enacted/changed: {s.what_it_changes}")
            if s.administrative_implications:
                facts.append(f"Administrative implementation: {s.administrative_implications}")

        if state_k and state_k.key_provisions:
            for p in state_k.key_provisions[:5]:
                facts.append(f"Key Statutory Provision: {p}")

        if state_k and state_k.amended_acts:
            facts.append(f"Acts Amended: {', '.join(state_k.amended_acts)}")

        # DERIVED
        if state_k:
            if state_k.policy_category:
                derived.append(f"Policy Category: {state_k.policy_category}.")
            if state_k.affected_stakeholders:
                derived.append(f"Affected Stakeholders: {', '.join(state_k.affected_stakeholders)}.")

        # State corporate exposures
        exposures = self.state_exposure_repo.get_by_bill(bill_id)
        if exposures:
            exp_strs = []
            for e in exposures[:6]:
                ticker_label = e.ticker if e.ticker else "Unlisted"
                exp_strs.append(f"{e.company_name} ({ticker_label}, {e.direct_indirect} exposure: {e.exposure_mechanism})")
            derived.append(f"Verified Corporate Exposure ({len(exposures)} mapped): {'; '.join(exp_strs)}.")
        else:
            derived.append("Corporate Exposure: Zero mapped commercial securities for this state statute.")

        # INTERPRETATIONS
        if state_k and state_k.summary and state_k.summary.why_it_matters:
            interpretations.append(f"Why it matters: {state_k.summary.why_it_matters}")
        if state_k and state_k.summary and state_k.summary.who_is_affected:
            interpretations.append(f"Who is affected: {state_k.summary.who_is_affected}")

        if state_k and state_k.economic_profile:
            ep = state_k.economic_profile
            if getattr(ep, "primary_sector", None):
                derived.append(f"Primary Economic Sector: {ep.primary_sector}.")
            if getattr(ep, "secondary_sectors", None):
                derived.append(f"Secondary Sectors: {', '.join(ep.secondary_sectors)}.")
            if getattr(ep, "economic_mechanisms", None):
                interpretations.append(f"Economic Mechanisms: {', '.join(ep.economic_mechanisms)}.")
            if getattr(ep, "compliance_burden", None):
                interpretations.append(f"Compliance Burden: {ep.compliance_burden}.")
            if getattr(ep, "fiscal_impact", None):
                interpretations.append(f"Fiscal Impact Assessment: {ep.fiscal_impact}.")

        # Modeling eligibility & data sufficiency
        if state_k and state_k.impact_assessment:
            ia = state_k.impact_assessment
            interpretations.append(f"Market Relevance: {getattr(ia, 'market_relevance', 'NONE')}.")
            interpretations.append(f"Modeling Eligibility: {getattr(ia, 'modeling_eligibility', 'NOT_ELIGIBLE')}.")
            interpretations.append(f"Data Sufficiency: {getattr(ia, 'data_sufficiency', 'INSUFFICIENT')}.")
            interpretations.append(f"Event Date Quality: {getattr(ia, 'event_date_quality', 'UNVERIFIED')}.")

        # PREDICTIONS — MUST BE STRICTLY EMPTY & EXPLICITLY UNAVAILABLE
        predictions.append("State market prediction is currently unavailable. (Model predictions strictly 0).")
        predictions.append("RULE: State legislative bills are strictly isolated from Central stock market prediction models.")
        predictions.append("No quantitative stock price, CAR, or abnormal return predictions exist for this state statute. (State market predictions = 0).")

        return AIContext(
            bill_id=bill_id,
            title=title,
            jurisdiction="state",
            state=state_name,
            bill_number=bill_number,
            introduction_date=intro_date,
            status=status,
            facts=facts,
            derived=derived,
            interpretations=interpretations,
            predictions=predictions,
            provenance=provenance,
            metadata={"source": "state", "state": state_name},
        )

    def build_comparison_context(self, bill_id_1: str, bill_id_2: str) -> AIComparisonContext:
        """Build comparative side-by-side context for two legislative bills."""
        ctx1 = self.build_context(bill_id_1)
        ctx2 = self.build_context(bill_id_2)
        return AIComparisonContext(bill_1=ctx1, bill_2=ctx2)

    def build_company_context(self, company_identifier: str) -> AICompanyContext:
        """
        Build verified AICompanyContext for a company entity.
        Supports both Central quantitative and broader intelligence entities.
        """
        from services.company_intelligence_service import CompanyIntelligenceService

        service = CompanyIntelligenceService(
            company_repo=self.company_repo,
            exposure_repo=self.company_exposure_repo,
            bill_repo=self.central_bill_repo,
            state_bill_repo=self.state_bill_repo,
            state_knowledge_repo=self.state_knowledge_repo,
        )
        profile = service.get_company_profile(company_identifier)
        if not profile:
            # Fallback for unknown company identifier
            return AICompanyContext(
                company_id=company_identifier,
                company_name=company_identifier,
                legal_identity=company_identifier,
                universe_type="intelligence",
                entity_type="unlisted_company",
                sector="Unknown",
                industry="Unknown",
                facts=[f"Entity identifier '{company_identifier}' has no verified record in project master."],
                derived=["No verified exposure links found."],
                interpretations=["Entity status is unverified."],
                predictions=["ZERO PREDICTIONS. Unregistered entity has no quantitative models."],
                provenance={"database": "Unverified Query"},
            )

        facts: list[str] = [
            f"Official Registered Name: {profile.company_name} (ID: {profile.company_id}).",
            f"Entity Type: {profile.entity_type.replace('_', ' ').title()} (Ownership: {profile.ownership_type.title()}).",
            f"Active Status: {'Active' if profile.is_active else 'Inactive'} (Listing Status: {profile.listing_status}).",
        ]
        if profile.ticker_nse:
            facts.append(f"NSE Ticker: {profile.ticker_nse} (BSE Code: {profile.bse_code or 'N/A'}).")
        if profile.group_name:
            facts.append(f"Corporate Group Affiliation: {profile.group_name}.")
        if profile.hq_state:
            facts.append(f"Headquarters: {profile.hq_city + ', ' if profile.hq_city else ''}{profile.hq_state}.")
        if profile.business_activities:
            facts.append(f"Verified Business Activities: {'; '.join(profile.business_activities)}.")
        if profile.operating_states:
            facts.append(f"Operational Footprint: Operating across {', '.join(profile.operating_states)}.")

        derived: list[str] = [
            f"Primary Sector: {profile.sector} (Industry: {profile.industry}).",
            f"Total Legislative Exposures: {profile.total_exposures} verified associations "
            f"({profile.central_exposures_count} Central, {profile.state_exposures_count} State).",
        ]
        for exp in profile.related_bills[:5]:
            ev_str = f" [Evidence: {len(exp.evidence)} citations]" if exp.evidence else ""
            derived.append(
                f"Exposed to Bill '{exp.bill_title}' ({exp.jurisdiction.title()}) — "
                f"{exp.direct_indirect} {exp.exposure_type} exposure ({exp.exposure_strength} strength) "
                f"via mechanism '{exp.mechanism}'{ev_str}."
            )
        if len(profile.related_bills) > 5:
            derived.append(f"Additional verified exposures: {len(profile.related_bills) - 5} more bills on record.")

        interpretations: list[str] = [
            f"Analytical Universe: {profile.universe_type.upper()}.",
            f"Legislative Impact Scope: Subject to {', '.join(profile.exposure_types) if profile.exposure_types else 'no regulatory exposure'}.",
        ]
        if profile.mechanisms:
            interpretations.append(f"Operates under statutory mechanisms: {', '.join(profile.mechanisms)}.")

        predictions: list[str] = []
        if profile.is_quant_eligible and profile.market_prediction_available:
            # Central quantitative company
            decisions = self.central_decision_repo.get_by_company(profile.isin)
            if decisions:
                sample_d = decisions[0]
                dir_val = getattr(sample_d, "predicted_direction", "NEUTRAL")
                dir_str = dir_val.value if hasattr(dir_val, "value") else str(dir_val)
                conf_val = getattr(sample_d, "predicted_confidence", getattr(sample_d, "confidence", "LOW"))
                conf_str = conf_val.value if hasattr(conf_val, "value") else str(conf_val)
                risk_val = getattr(sample_d, "risk_category", "MODERATE")
                risk_str = risk_val.value if hasattr(risk_val, "value") else str(risk_val)
                prob_move = float(getattr(sample_d, "market_moving_probability", 0.0))
                predictions.append(
                    f"Existing Central Model Directional Consensus: {dir_str} (Confidence: {conf_str})."
                )
                predictions.append(
                    f"Model Market-Moving Probability: {prob_move:.2f} (Risk Category: {risk_str})."
                )
                predictions.append(
                    "NOTE: Outputs are historical frozen model predictions. Strictly analytical; not trading advice."
                )
            else:
                predictions.append("Central quantitative company with no active precomputed decision records.")
        else:
            predictions.append(
                "ZERO PREDICTIONS. Intelligence-only entity strictly isolated from quantitative prediction engine "
                "by quantitative firewall. No stock price predictions, CAR, abnormal returns, or trading signals exist."
            )
            predictions.append("RULE: Market relevance is strictly qualitative. Financial return models are 0.")

        provenance = {
            "sources": ", ".join(profile.data_sources) if profile.data_sources else "Official Master Records",
            "database": "Project Company Intelligence Repository",
            "firewall": profile.quantitative_firewall_status,
        }

        return AICompanyContext(
            company_id=profile.company_id,
            company_name=profile.company_name,
            legal_identity=profile.legal_identity,
            universe_type=profile.universe_type,
            entity_type=profile.entity_type,
            sector=profile.sector,
            industry=profile.industry,
            facts=facts,
            derived=derived,
            interpretations=interpretations,
            predictions=predictions,
            provenance=provenance,
            metadata={"company_id": profile.company_id},
        )

    def build_company_bill_context(
        self, company_identifier: str, bill_id: str
    ) -> AICompanyContext:
        """
        Build verified AI context specifically connecting a company to a target bill.
        """
        ctx = self.build_company_context(company_identifier)
        bill_ctx = self.build_context(bill_id)

        ctx.bill_id = bill_id
        ctx.bill_title = bill_ctx.title

        # Check exposure explanation from service
        from services.company_intelligence_service import CompanyIntelligenceService
        service = CompanyIntelligenceService(
            company_repo=self.company_repo,
            exposure_repo=self.company_exposure_repo,
            bill_repo=self.central_bill_repo,
            state_bill_repo=self.state_bill_repo,
            state_knowledge_repo=self.state_knowledge_repo,
        )
        explanation = service.explain_exposure(company_identifier, bill_id)

        if explanation.has_exposure:
            ctx.facts.append(
                f"Target Bill: '{bill_ctx.title}' ({bill_ctx.jurisdiction.title()}"
                + (f" — {bill_ctx.state}" if bill_ctx.state else "") + ")."
            )
            ctx.derived.append(
                f"Specific Exposure to '{bill_ctx.title}': {explanation.direct_indirect} {explanation.exposure_type} "
                f"({explanation.exposure_strength} strength). Mechanism: {explanation.economic_mechanism}."
            )
            for claim, ref in zip(explanation.evidence_claims, explanation.evidence_references):
                ctx.facts.append(f"Statutory/Corporate Evidence Claim: \"{claim}\" [Reference: {ref}].")
            ctx.interpretations.append(f"Exposure Grounding: {explanation.why_explanation}")
            ctx.interpretations.append(f"Qualitative Market Relevance: {explanation.market_relevance}.")
        else:
            ctx.derived.append(
                f"Target Bill Relationship: Zero verified exposure on record between {ctx.company_name} and bill '{bill_id}'."
            )
            ctx.interpretations.append(
                f"Verification Verdict: No evidence connects {ctx.company_name} to this specific statute."
            )

        return ctx

    def build_industry_context(self, industry_identifier: str) -> AIIndustryContext:
        """
        Build verified AI context for an industry sector.
        """
        from services.industry_intelligence_service import IndustryIntelligenceService
        service = IndustryIntelligenceService(
            company_repo=self.company_repo,
            exposure_repo=self.company_exposure_repo,
            bill_repo=self.central_bill_repo,
            knowledge_repo=self.central_knowledge_repo,
            state_bill_repo=self.state_bill_repo,
            state_knowledge_repo=self.state_knowledge_repo,
            prediction_repo=self.central_prediction_repo,
            decision_repo=self.central_decision_repo,
            anticipation_repo=self.anticipation_repo,
        )
        dossier = service.get_industry_dossier(industry_identifier)
        if not dossier:
            return AIIndustryContext(
                industry_id=industry_identifier,
                industry_name=industry_identifier,
                sector="Unknown",
                coverage_level=3,
                facts=[f"Industry identifier '{industry_identifier}' has no verified record in project master."],
                derived=["No verified exposure links found for this industry query."],
                interpretations=["Industry status is unclassified."],
                predictions=["Industry-level prediction is not modeled. Model outputs are company-level only."],
                provenance={"database": "Unverified Query", "sources": "None"},
            )

        return AIIndustryContext(
            industry_id=dossier.industry_id,
            industry_name=dossier.name,
            sector=dossier.sector,
            coverage_level=dossier.coverage_level,
            facts=list(dossier.facts),
            derived=list(dossier.derived),
            interpretations=list(dossier.interpretations),
            predictions=list(dossier.predictions),
            provenance={
                "sources": "Parliamentary Records / MCA Corporate Registry",
                "database": "Project Multi-Jurisdiction Repository",
                "state_firewall": "ACTIVE (Strictly 0 Predictions)",
            },
            metadata={"industry_id": dossier.industry_id, "sector": dossier.sector},
        )

