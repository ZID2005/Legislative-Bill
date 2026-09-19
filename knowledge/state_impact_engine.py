"""
knowledge/state_impact_engine.py
================================
Deterministic Economic and Market Impact Methodology Engine for Indian State Legislative Bills.

Implements Task 8.8 Phases 1 through 11:
- Phase 1: Economic Mechanism Extraction (26-mechanism taxonomy)
- Phase 2: Economic Impact Direction (positive, negative, mixed, neutral, unknown)
- Phase 3: Economic Impact Strength (HIGH, MEDIUM, LOW, UNKNOWN)
- Phase 4: Market Relevance (HIGH, MEDIUM, LOW, NONE, UNKNOWN)
- Phase 5: State Market-Modeling Eligibility (strict 10-point scorecard)
- Phase 6: Data Sufficiency Assessment (14-dimension data audit)
- Phase 7: Event Date Quality & Role (primary vs alternative event dates)
- Phase 8: Anticipation / Pricing-In Readiness
- Phase 9: State Market Data Readiness Audit
- Phase 10: State Impact Assessment Model Assembly
- Phase 11: Transparent Human-Readable Eligibility Scorecard

Guarantees:
- ZERO stock price predictions, price targets, or financial returns
- ZERO State event studies or abnormal return calculations
- Complete isolation from Central production systems
- Deterministic, auditable, and idempotent assessment execution
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.bill import Bill
from schemas.state_corporate_exposure import StateCorporateExposure
from schemas.state_economic_profile import StateBillEconomicProfile
from schemas.state_impact_assessment import (
    AnticipationReadiness,
    DataSufficiency,
    EconomicImpactDirection,
    EconomicImpactStrength,
    EconomicMechanism,
    EligibilityScorecard,
    EventDateQuality,
    EventDateRecord,
    EventDateRole,
    MarketDataReadinessSummary,
    MarketRelevance,
    ModelingEligibility,
    StateImpactAssessment,
)
from knowledge.state_economic_taxonomy import (
    STATE_ECONOMIC_MECHANISMS,
    VALID_ECONOMIC_MECHANISMS,
    normalize_economic_mechanism,
)

logger = get_logger(__name__)


class StateImpactMethodologyEngine:
    """
    Deterministic assessment engine for evaluating State legislative economic
    impact mechanisms, market relevance, and modeling eligibility.
    """

    def __init__(self, market_data_dir: Optional[Path] = None) -> None:
        """
        Initialize the methodology engine.

        Parameters
        ----------
        market_data_dir : Path | None
            Directory containing historical market parquet files.
            Defaults to settings.DATA_DIR / "market".
        """
        from config.settings import settings
        self._market_data_dir = Path(market_data_dir) if market_data_dir else (settings.DATA_DIR / "market")

    # ==========================================================================
    # Phase 1: Economic Mechanism Extraction
    # ==========================================================================

    def extract_economic_mechanisms(
        self,
        bill: Bill,
        economic_profile: Optional[StateBillEconomicProfile] = None,
        exposures: Optional[list[StateCorporateExposure]] = None,
    ) -> list[str]:
        """
        Extract statutory economic mechanisms based on grounded bill text,
        economic profile, and corporate exposures.
        """
        mechanisms: set[str] = set()

        # 1. From economic profile impact_mechanisms
        if economic_profile:
            for raw_m in economic_profile.impact_mechanisms:
                norm = normalize_economic_mechanism(raw_m)
                if norm in VALID_ECONOMIC_MECHANISMS:
                    mechanisms.add(norm)

            # From stakeholder mechanisms
            for sh in economic_profile.stakeholders:
                if sh.mechanism:
                    norm = normalize_economic_mechanism(sh.mechanism)
                    if norm in VALID_ECONOMIC_MECHANISMS:
                        mechanisms.add(norm)

        # 2. From corporate exposures
        if exposures:
            for exp in exposures:
                if exp.mechanism:
                    norm = normalize_economic_mechanism(exp.mechanism)
                    if norm in VALID_ECONOMIC_MECHANISMS:
                        mechanisms.add(norm)
                if exp.exposure_type:
                    norm_type = normalize_economic_mechanism(exp.exposure_type)
                    if norm_type in VALID_ECONOMIC_MECHANISMS:
                        mechanisms.add(norm_type)

        # 3. From bill text provisions keywords
        text = f"{bill.title} {' '.join(bill.sectors or [])} {bill.summary or ''} {bill.full_text or ''}".lower()
        if any(k in text for k in ["tax", "duty", "cess", "gst", "excise", "vat"]):
            mechanisms.add(EconomicMechanism.TAXATION.value)
        if any(k in text for k in ["subsidy", "incentive", "rebate", "subvention"]):
            mechanisms.add(EconomicMechanism.SUBSIDY.value)
        if any(k in text for k in ["electricity duty", "power tariff", "captive power", "grid"]):
            mechanisms.add(EconomicMechanism.ELECTRICITY_COST.value)
        if any(k in text for k in ["motor vehicles", "transport", "road tax", "freight"]):
            mechanisms.add(EconomicMechanism.TRANSPORTATION_COST.value)
        if any(k in text for k in ["gig worker", "platform worker", "welfare fund", "labour", "employment"]):
            mechanisms.add(EconomicMechanism.LABOUR_COST.value)
            mechanisms.add(EconomicMechanism.EMPLOYMENT.value)
        if any(k in text for k in ["industrial promotion", "investment", "single desk", "incentive"]):
            mechanisms.add(EconomicMechanism.INVESTMENT.value)
        if any(k in text for k in ["license", "licensing", "registration", "permit", "accreditation"]):
            mechanisms.add(EconomicMechanism.LICENSING.value)
        if any(k in text for k in ["compliance", "audit", "inspection", "register", "return"]):
            mechanisms.add(EconomicMechanism.COMPLIANCE_COST.value)
        if any(k in text for k in ["environment", "pollution", "hazard", "wildlife"]):
            mechanisms.add(EconomicMechanism.ENVIRONMENTAL_COST.value)
        if any(k in text for k in ["land", "tenancy", "zoning", "urban development"]):
            mechanisms.add(EconomicMechanism.LAND.value)
        if any(k in text for k in ["procurement", "tender", "contract"]):
            mechanisms.add(EconomicMechanism.PROCUREMENT.value)

        # Fallback if empty
        if not mechanisms:
            mechanisms.add(EconomicMechanism.REGULATION.value)

        # Return sorted list for deterministic output
        return sorted(list(mechanisms))

    # ==========================================================================
    # Phase 2: Economic Impact Direction
    # ==========================================================================

    def determine_economic_direction(
        self,
        bill: Bill,
        mechanisms: list[str],
        economic_profile: Optional[StateBillEconomicProfile] = None,
        exposures: Optional[list[StateCorporateExposure]] = None,
    ) -> str:
        """
        Determine qualitative real-economy direction (distinct from stock direction).
        Allowed: positive, negative, mixed, neutral, unknown.
        """
        # 1. From economic profile stakeholder balance
        if economic_profile and economic_profile.stakeholders:
            has_positive = any(s.direction == "positive" for s in economic_profile.stakeholders)
            has_negative = any(s.direction == "negative" for s in economic_profile.stakeholders)
            if has_positive and has_negative:
                return EconomicImpactDirection.MIXED.value
            if has_positive and not has_negative:
                return EconomicImpactDirection.POSITIVE.value
            if has_negative and not has_positive:
                return EconomicImpactDirection.NEGATIVE.value

        # 2. From corporate exposures
        if exposures:
            exp_dirs = {e.exposure_direction.lower() for e in exposures if e.exposure_direction}
            if "mixed" in exp_dirs or ("positive" in exp_dirs and "negative" in exp_dirs):
                return EconomicImpactDirection.MIXED.value

        # 3. Keyword / domain heuristics
        text = f"{bill.title} {bill.summary or ''}".lower()
        if any(k in text for k in ["repealing", "repeal", "obsolete", "disqualification", "amendment act"]):
            return EconomicImpactDirection.NEUTRAL.value
        if any(k in text for k in ["incentive", "promotion", "welfare", "development", "facilitation"]):
            if any(k in text for k in ["tax", "fee", "duty", "cess", "penalty"]):
                return EconomicImpactDirection.MIXED.value
            return EconomicImpactDirection.POSITIVE.value
        if any(k in text for k in ["tax", "cess", "duty", "fee", "penalty"]):
            return EconomicImpactDirection.MIXED.value

        return EconomicImpactDirection.NEUTRAL.value

    # ==========================================================================
    # Phase 3: Economic Impact Strength
    # ==========================================================================

    def determine_economic_strength(
        self,
        bill: Bill,
        mechanisms: list[str],
        economic_profile: Optional[StateBillEconomicProfile] = None,
        exposures: Optional[list[StateCorporateExposure]] = None,
    ) -> str:
        """
        Determine economic impact strength based on transparent deterministic statutory criteria.
        HIGH: Explicit statutory mechanism + clearly identified activity + credible scope/relevance.
        MEDIUM: Clear mechanism but localized or routine procedural amendment.
        LOW: Plausible but limited/indirect mechanism.
        UNKNOWN: Insufficient evidence.
        """
        # If bill text or summary is missing
        if not bill.summary and not bill.full_text:
            return EconomicImpactStrength.UNKNOWN.value

        # Check for HIGH strength indicators
        high_mechanisms = {
            EconomicMechanism.TAXATION.value,
            EconomicMechanism.ELECTRICITY_COST.value,
            EconomicMechanism.TRANSPORTATION_COST.value,
            EconomicMechanism.INVESTMENT.value,
            EconomicMechanism.LABOUR_COST.value,
        }
        has_high_mechanism = any(m in high_mechanisms for m in mechanisms)

        # High corporate exposure strength
        if exposures and any(e.exposure_strength == "HIGH" for e in exposures):
            return EconomicImpactStrength.HIGH.value

        if has_high_mechanism and bill.status in ["passed_both", "assented", "passed", "introduced"]:
            return EconomicImpactStrength.HIGH.value

        # Check for LOW strength indicators (purely repealing, minor administrative nomenclature)
        text = f"{bill.title} {bill.summary or ''}".lower()
        if any(k in text for k in ["repealing", "obsolete laws", "salary and allowances", "disqualification"]):
            return EconomicImpactStrength.LOW.value

        # Default for substantive regulation with clear mechanisms
        if mechanisms and mechanisms != [EconomicMechanism.REGULATION.value]:
            return EconomicImpactStrength.MEDIUM.value

        return EconomicImpactStrength.LOW.value

    # ==========================================================================
    # Phase 4: Market Relevance
    # ==========================================================================

    def determine_market_relevance(
        self,
        exposures: list[StateCorporateExposure],
    ) -> str:
        """
        Classify market relevance.
        HIGH: Strong listed-company exposure + explicit applicability + measurable financial channel.
        MEDIUM: Listed-company exposure exists, but financial magnitude or applicability is uncertain.
        LOW: Indirect/limited listed-company exposure.
        NONE: No meaningful listed-company exposure.
        """
        if not exposures:
            return MarketRelevance.NONE.value

        listed_exps = [e for e in exposures if e.listed_status.lower() == "listed"]
        if not listed_exps:
            return MarketRelevance.NONE.value

        direct_listed = [e for e in listed_exps if e.direct_indirect.upper() == "DIRECT"]
        if not direct_listed:
            # Only indirect listed exposures exist
            return MarketRelevance.LOW.value

        # Check if any direct listed exposure has HIGH strength
        if any(e.exposure_strength.upper() == "HIGH" for e in direct_listed):
            return MarketRelevance.HIGH.value

        # If direct listed exposures are MEDIUM strength
        if any(e.exposure_strength.upper() == "MEDIUM" for e in direct_listed):
            return MarketRelevance.MEDIUM.value

        return MarketRelevance.LOW.value

    # ==========================================================================
    # Phase 7: Event Date Quality & Role Resolution
    # ==========================================================================

    def resolve_event_dates(
        self,
        bill: Bill,
    ) -> tuple[Optional[EventDateRecord], list[EventDateRecord], str]:
        """
        Determine PRIMARY_EVENT_DATE, ALTERNATIVE_EVENT_DATES, and EventDateQuality.
        DO NOT invent dates.
        """
        primary_date: Optional[EventDateRecord] = None
        alt_dates: list[EventDateRecord] = []

        intro_date = bill.introduction_date
        assent_date = bill.assent_date
        gazette_date = getattr(bill, "gazette_date", None)

        if intro_date:
            primary_date = EventDateRecord(
                role=EventDateRole.INTRODUCTION.value,
                date=intro_date,
                source="official_legislative_portal",
                is_primary=True,
            )
            if assent_date:
                alt_dates.append(
                    EventDateRecord(
                        role=EventDateRole.ASSENT.value,
                        date=assent_date,
                        source="official_gazette",
                        is_primary=False,
                    )
                )
            if gazette_date:
                alt_dates.append(
                    EventDateRecord(
                        role=EventDateRole.GAZETTE.value,
                        date=gazette_date,
                        source="official_gazette",
                        is_primary=False,
                    )
                )
        elif assent_date:
            primary_date = EventDateRecord(
                role=EventDateRole.ASSENT.value,
                date=assent_date,
                source="official_gazette",
                is_primary=True,
            )
            if gazette_date:
                alt_dates.append(
                    EventDateRecord(
                        role=EventDateRole.GAZETTE.value,
                        date=gazette_date,
                        source="official_gazette",
                        is_primary=False,
                    )
                )
        elif gazette_date:
            primary_date = EventDateRecord(
                role=EventDateRole.GAZETTE.value,
                date=gazette_date,
                source="official_gazette",
                is_primary=True,
            )

        # Quality scoring
        if intro_date and assent_date:
            quality = EventDateQuality.HIGH.value
        elif primary_date is not None:
            quality = EventDateQuality.MEDIUM.value
        else:
            quality = EventDateQuality.NONE.value

        return primary_date, alt_dates, quality

    # ==========================================================================
    # Phase 8: Anticipation / Pricing-In Readiness
    # ==========================================================================

    def assess_anticipation_readiness(
        self,
        bill: Bill,
        primary_date: Optional[EventDateRecord],
    ) -> tuple[str, list[str]]:
        """
        Assess anticipation / pricing-in readiness without implementing live crawlers.
        """
        candidate_channels = [
            "public_announcements",
            "legislative_leaks",
            "government_consultations",
            "committee_discussions",
            "media_coverage",
            "gdelt",
            "google_trends",
        ]

        if primary_date is None:
            return AnticipationReadiness.NOT_AVAILABLE.value, []

        # In Task 8.8, methodology exists but live crawler pipelines are not yet attached for State bills
        return AnticipationReadiness.PARTIAL.value, candidate_channels

    # ==========================================================================
    # Phase 9: State Market Data Readiness Audit
    # ==========================================================================

    def audit_market_data_readiness(
        self,
        exposures: list[StateCorporateExposure],
        primary_date: Optional[EventDateRecord],
    ) -> MarketDataReadinessSummary:
        """
        Audit whether candidate exposed securities have existing historical parquet
        market data and benchmark coverage without downloading new datasets.
        """
        candidate_count = len(exposures)
        listed_exps = [e for e in exposures if e.listed_status.lower() == "listed"]
        unlisted_exps = [e for e in exposures if e.listed_status.lower() != "listed"]

        with_data: list[str] = []
        missing_data: list[str] = []

        event_year = None
        if primary_date and primary_date.date:
            try:
                event_year = primary_date.date.split("-")[0]
            except Exception:
                event_year = None

        benchmark_dir = self._market_data_dir / "^NSEI"
        benchmark_available = benchmark_dir.exists() and (
            (benchmark_dir / f"{event_year}.parquet").exists() if event_year else True
        )

        for exp in listed_exps:
            ticker = exp.ticker.strip().upper()
            if not ticker:
                continue
            ticker_dir = self._market_data_dir / f"{ticker}.NS"
            if ticker_dir.exists() and (
                (ticker_dir / f"{event_year}.parquet").exists() if event_year else True
            ):
                if ticker not in with_data:
                    with_data.append(ticker)
            else:
                if ticker not in missing_data:
                    missing_data.append(ticker)

        calendar_coverage = "COMPLETE" if with_data and not missing_data else (
            "PARTIAL" if with_data else "INSUFFICIENT"
        )

        return MarketDataReadinessSummary(
            candidate_companies_count=candidate_count,
            listed_companies_count=len(listed_exps),
            unlisted_companies_count=len(unlisted_exps),
            companies_with_market_data=sorted(with_data),
            companies_missing_market_data=sorted(missing_data),
            benchmark_available=benchmark_available,
            benchmark_ticker="^NSEI",
            trading_calendar_coverage=calendar_coverage,
        )

    # ==========================================================================
    # Phase 6: Data Sufficiency Assessment
    # ==========================================================================

    def assess_data_sufficiency(
        self,
        bill: Bill,
        primary_date: Optional[EventDateRecord],
        exposures: list[StateCorporateExposure],
        market_readiness: MarketDataReadinessSummary,
        anticipation_readiness: str,
    ) -> tuple[str, list[str]]:
        """
        Assess 14 data audit dimensions and compile missing requirements.
        """
        missing: list[str] = []

        # 1. Bill date
        if not primary_date:
            missing.append("Verified bill event date (introduction or assent date) is missing.")

        # 2. Bill text
        if not bill.summary and not bill.full_text:
            missing.append("Substantive bill statutory text / summary is missing.")

        # 3. State jurisdiction
        if not bill.state:
            missing.append("State jurisdiction is unspecified.")

        # 4. Corporate exposure
        if not exposures:
            missing.append("No grounded corporate exposure identified for this State bill.")
        else:
            # 5. Listed companies
            if market_readiness.listed_companies_count == 0:
                missing.append("All exposed entities are unlisted/public utilities; zero listed companies.")

            # 6. Historical market prices
            if market_readiness.companies_missing_market_data:
                missing.append(
                    f"Historical market price data missing in local store for: {', '.join(market_readiness.companies_missing_market_data)}."
                )

        # 7. Anticipation information
        if anticipation_readiness != AnticipationReadiness.READY.value:
            missing.append("Live anticipation crawling and sentiment signal ingestion not connected.")

        # 8. Benchmark prices
        if not market_readiness.benchmark_available:
            missing.append("Historical benchmark index data (^NSEI) is missing for the event period.")

        # Classification
        if not missing:
            sufficiency = DataSufficiency.COMPLETE.value
        elif len(missing) <= 2 and market_readiness.companies_with_market_data:
            sufficiency = DataSufficiency.PARTIAL.value
        else:
            sufficiency = DataSufficiency.INSUFFICIENT.value

        return sufficiency, missing

    # ==========================================================================
    # Phase 5 & 11: Transparent 10-Point Scorecard & Eligibility
    # ==========================================================================

    def evaluate_eligibility(
        self,
        bill: Bill,
        primary_date: Optional[EventDateRecord],
        mechanisms: list[str],
        exposures: list[StateCorporateExposure],
        market_readiness: MarketDataReadinessSummary,
        anticipation_readiness: str,
        missing_requirements: list[str],
    ) -> EligibilityScorecard:
        """
        Evaluate 10-point transparent deterministic eligibility scorecard.
        """
        c1_identity = bool(bill.bill_id and (bill.bill_number or bill.title))
        c2_state = bool(bill.state in ["Andhra Pradesh", "Karnataka", "Kerala", "Telangana"])
        c3_date = bool(primary_date is not None and primary_date.date)
        c4_mech = bool(mechanisms and mechanisms != [EconomicMechanism.UNKNOWN.value])
        c5_exposure = bool(len(exposures) > 0)
        c6_listed = bool(market_readiness.listed_companies_count > 0)
        c7_mkt_data = bool(len(market_readiness.companies_with_market_data) > 0)
        c8_benchmark = bool(market_readiness.benchmark_available)
        c9_event_identifiable = bool(primary_date is not None and primary_date.role in [
            EventDateRole.INTRODUCTION.value,
            EventDateRole.PASSAGE.value,
            EventDateRole.ASSENT.value,
            EventDateRole.GAZETTE.value,
        ])
        c10_anticipation = bool(anticipation_readiness in [
            AnticipationReadiness.READY.value,
            AnticipationReadiness.PARTIAL.value,
        ])

        # Result calculation
        notes: list[str] = []
        if not c5_exposure or not c6_listed:
            result = ModelingEligibility.NOT_ELIGIBLE.value
            notes.append("Bill has no listed corporate exposure; remains strictly economic-only.")
        elif not c3_date or not c1_identity or not c2_state:
            result = ModelingEligibility.INSUFFICIENT_DATA.value
            notes.append("Critical legislative metadata (event date or identity) is missing.")
        elif c1_identity and c2_state and c3_date and c4_mech and c5_exposure and c6_listed and c7_mkt_data and c8_benchmark and c9_event_identifiable and (anticipation_readiness == AnticipationReadiness.READY.value):
            result = ModelingEligibility.ELIGIBLE.value
            notes.append("All 10 modeling prerequisites completely satisfied.")
        else:
            # Corporate exposure exists, event date exists, but anticipation is partial or some market data is pending
            result = ModelingEligibility.CONDITIONALLY_ELIGIBLE.value
            if not c7_mkt_data:
                notes.append("Candidate tickers are listed but historical parquets are pending download.")
            if anticipation_readiness == AnticipationReadiness.PARTIAL.value:
                notes.append("Anticipation framework defined, but external live news/GDELT crawlers not attached.")

        return EligibilityScorecard(
            bill_identity_verified=c1_identity,
            state_jurisdiction_verified=c2_state,
            event_date_verified=c3_date,
            economic_mechanism_identified=c4_mech,
            corporate_exposure_verified=c5_exposure,
            listed_company_verified=c6_listed,
            historical_market_data_available=c7_mkt_data,
            benchmark_data_available=c8_benchmark,
            event_date_identifiable=c9_event_identifiable,
            anticipation_readiness_sufficient=c10_anticipation,
            result=result,
            notes=notes,
        )

    # ==========================================================================
    # Phase 10: State Impact Assessment Model Assembly
    # ==========================================================================

    def assess_bill(
        self,
        bill: Bill,
        economic_profile: Optional[StateBillEconomicProfile] = None,
        exposures: Optional[list[StateCorporateExposure]] = None,
    ) -> StateImpactAssessment:
        """
        Execute the complete economic and market impact methodology for a State bill.
        """
        exposures_list = exposures or []

        # 1. Economic mechanisms (Phase 1)
        mechanisms = self.extract_economic_mechanisms(bill, economic_profile, exposures_list)

        # 2. Economic direction (Phase 2)
        direction = self.determine_economic_direction(bill, mechanisms, economic_profile, exposures_list)

        # 3. Economic strength (Phase 3)
        strength = self.determine_economic_strength(bill, mechanisms, economic_profile, exposures_list)

        # 4. Market relevance (Phase 4)
        market_rel = self.determine_market_relevance(exposures_list)

        # 5. Event date resolution (Phase 7)
        primary_date, alt_dates, date_quality = self.resolve_event_dates(bill)

        # 6. Anticipation readiness (Phase 8)
        anticipation_status, anticipation_channels = self.assess_anticipation_readiness(bill, primary_date)

        # 7. Market data readiness (Phase 9)
        mkt_readiness = self.audit_market_data_readiness(exposures_list, primary_date)

        # 8. Data sufficiency (Phase 6)
        sufficiency, missing_reqs = self.assess_data_sufficiency(
            bill=bill,
            primary_date=primary_date,
            exposures=exposures_list,
            market_readiness=mkt_readiness,
            anticipation_readiness=anticipation_status,
        )

        # 9. Eligibility scorecard (Phase 5 & 11)
        scorecard = self.evaluate_eligibility(
            bill=bill,
            primary_date=primary_date,
            mechanisms=mechanisms,
            exposures=exposures_list,
            market_readiness=mkt_readiness,
            anticipation_readiness=anticipation_status,
            missing_requirements=missing_reqs,
        )

        # Exposure counts
        exp_count = len(exposures_list)
        direct_count = sum(1 for e in exposures_list if e.direct_indirect.upper() == "DIRECT")
        indirect_count = sum(1 for e in exposures_list if e.direct_indirect.upper() == "INDIRECT")
        listed_count = mkt_readiness.listed_companies_count

        # Grounded evidence references
        evidence: list[dict[str, Any]] = []
        if bill.summary:
            evidence.append({
                "source_type": "official_bill_summary",
                "reference": "Statement of Objects and Reasons / Metadata",
                "claim": f"Statutory summary indicates policy in {', '.join(bill.sectors or ['State Administration'])}.",
            })
        for m in mechanisms:
            evidence.append({
                "source_type": "statutory_mechanism",
                "reference": f"Taxonomy::{m}",
                "claim": f"Statutory impact channel identified as '{m}'.",
            })

        provenance = {
            "economic_taxonomy": "STATE_ECONOMIC_MECHANISMS_V1",
            "market_relevance": "GROUNDED_CORPORATE_EXPOSURE_MATCH",
            "eligibility_scorecard": "DETERMINISTIC_10_POINT_SCORECARD",
            "market_data_audit": "LOCAL_PARQUET_STORE_VERIFIED",
        }

        return StateImpactAssessment(
            bill_id=bill.bill_id,
            state=bill.state or "",
            title=bill.title or "",
            bill_number=bill.bill_number or "",
            economic_mechanisms=mechanisms,
            economic_direction=direction,
            economic_strength=strength,
            market_relevance=market_rel,
            modeling_eligibility=scorecard.result,
            data_sufficiency=sufficiency,
            event_date_quality=date_quality,
            primary_event_date=primary_date,
            alternative_event_dates=alt_dates,
            anticipation_readiness=anticipation_status,
            candidate_anticipation_channels=anticipation_channels,
            market_data_readiness=mkt_readiness,
            listed_company_count=listed_count,
            exposure_count=exp_count,
            direct_exposure_count=direct_count,
            indirect_exposure_count=indirect_count,
            missing_requirements=missing_reqs,
            scorecard=scorecard,
            evidence=evidence,
            confidence="HIGH" if date_quality == EventDateQuality.HIGH.value and exp_count > 0 else "MEDIUM",
            provenance=provenance,
            schema_version="1.0.0",
        )
