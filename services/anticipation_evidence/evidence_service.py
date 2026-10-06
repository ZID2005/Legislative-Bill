"""
services/anticipation_evidence/evidence_service.py
==================================================
Anticipation Evidence Enrichment & Media Diffusion Intelligence Service.

Combines pre-event market signals from frozen records with independently
verified public-information evidence WITHOUT modifying frozen baselines.

Non-Negotiable Project Policies:
- Output is strictly PUBLIC INFORMATION DIFFUSION INTELLIGENCE.
- Never alleges, implies, or suggests:
  * insider trading
  * market manipulation
  * illegal disclosure
  * unlawful conduct
  * confidential information leakage
- State bills: strictly 0 stock predictions, 0 abnormal returns, market signal UNKNOWN.
- Intelligence-only entities: firewall maintained.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.anticipation import AnticipationScore
from schemas.anticipation_evidence import (
    AnticipationContextClassification,
    AnticipationEvidenceContext,
    CombinedAnticipationContextSummary,
    EvidenceStrength,
    MarketSignalLevel,
    MarketSignalSummary,
    NON_ACCUSATORY_DISCLAIMER,
    PublicInformationEvidence,
    PublicInformationSignalLevel,
    PublicInformationSignalSummary,
    PublicInformationSourceType,
    SearchTrendEvidence,
    SourceCredibilityTier,
    TemporalRelation,
    VerificationStatus,
)
from schemas.monitoring import ChangeEvent
from schemas.unified_bill_record import UnifiedBillRecord
from services.anticipation_evidence.base_adapter import BaseEvidenceAdapter
from services.anticipation_evidence.evidence_deduplicator import EvidenceDeduplicator
from services.anticipation_evidence.evidence_normalizer import EvidenceNormalizer
from services.anticipation_evidence.evidence_repository import AnticipationEvidenceRepository
from services.anticipation_evidence.evidence_validator import EvidenceValidator
from services.anticipation_evidence.news_adapter import NewsAdapter
from services.anticipation_evidence.official_source_adapter import OfficialSourceAdapter
from services.anticipation_evidence.search_trend_adapter import SearchTrendAdapter
from storage.anticipation_repository import AnticipationRepository

logger = get_logger(__name__)

# Credibility tier weights (Phase 4)
CREDIBILITY_WEIGHTS: dict[SourceCredibilityTier, float] = {
    SourceCredibilityTier.TIER_1: 1.0,  # Official government / legislature / regulator
    SourceCredibilityTier.TIER_2: 0.8,  # Established mainstream / financial media
    SourceCredibilityTier.TIER_3: 0.6,  # Recognized industry publication
    SourceCredibilityTier.TIER_4: 0.4,  # Search/trend attention signal
    SourceCredibilityTier.TIER_5: 0.2,  # Unverified / low-confidence source
}


class AnticipationEvidenceService:
    """
    Main domain service coordinating evidence discovery, temporal validation,
    scoring, and contextual synthesis.
    """

    def __init__(
        self,
        evidence_repo: Optional[AnticipationEvidenceRepository] = None,
        anticipation_repo: Optional[AnticipationRepository] = None,
        custom_adapters: Optional[list[BaseEvidenceAdapter]] = None,
    ) -> None:
        self.evidence_repo = evidence_repo or AnticipationEvidenceRepository()
        self.anticipation_repo = anticipation_repo or AnticipationRepository()

        # Default source adapters
        self.official_adapter = OfficialSourceAdapter()
        self.news_adapter = NewsAdapter()
        self.search_adapter = SearchTrendAdapter()

        self._adapters: list[BaseEvidenceAdapter] = custom_adapters or [
            self.official_adapter,
            self.news_adapter,
            self.search_adapter,
        ]

    def register_adapter(self, adapter: BaseEvidenceAdapter) -> None:
        """Register an additional public-information source adapter."""
        self._adapters.append(adapter)

    # ------------------------------------------------------------------
    # Public Information Evidence Scoring (Phase 9)
    # ------------------------------------------------------------------

    @classmethod
    def calculate_public_information_evidence_score(
        cls,
        verified_pre_event_items: list[PublicInformationEvidence],
        official_event_timestamp: str,
    ) -> float:
        """
        Calculate deterministic public_information_evidence_score normalized in [0.0, 1.0].

        Weights:
        - Source Credibility: 0.30
        - Temporal Proximity: 0.25
        - Relevance Strength: 0.20
        - Independent Source Count: 0.15
        - Source Diversity: 0.10
        Total: 1.00
        """
        if not verified_pre_event_items:
            return 0.0

        canonical_items = [ev for ev in verified_pre_event_items if not ev.duplicate_of]
        if not canonical_items:
            return 0.0

        event_dt = EvidenceNormalizer.parse_timestamp(official_event_timestamp)

        # 1. Source Credibility (Avg of canonical items)
        cred_scores = [CREDIBILITY_WEIGHTS.get(ev.source_credibility, 0.4) for ev in canonical_items]
        avg_cred = sum(cred_scores) / len(cred_scores)

        # 2. Temporal Proximity (Exponential proximity to T0)
        proximity_scores: list[float] = []
        for ev in canonical_items:
            pub_dt = EvidenceNormalizer.parse_timestamp(ev.publication_timestamp)
            if pub_dt and event_dt and event_dt >= pub_dt:
                days_before = max(0, (event_dt.date() - pub_dt.date()).days)
                # Exponential decay: items closer to event date have higher proximity weight
                prox = math.exp(-0.05 * days_before)
            else:
                prox = 0.5
            proximity_scores.append(prox)
        avg_proximity = sum(proximity_scores) / len(proximity_scores)

        # 3. Relevance Strength (Avg relevance)
        rel_scores = [float(ev.relevance) for ev in canonical_items]
        avg_relevance = sum(rel_scores) / len(rel_scores)

        # 4. Independent Source Count (max at 3 independent publishers)
        independent_count = EvidenceDeduplicator.count_independent_sources(canonical_items)
        ind_score = min(1.0, independent_count / 3.0)

        # 5. Source Diversity (ratio)
        diversity = EvidenceDeduplicator.calculate_source_diversity(canonical_items)

        # Weighted composite
        raw_score = (
            0.30 * avg_cred
            + 0.25 * avg_proximity
            + 0.20 * avg_relevance
            + 0.15 * ind_score
            + 0.10 * diversity
        )

        return float(max(0.0, min(1.0, round(raw_score, 4))))

    # ------------------------------------------------------------------
    # Context Interpretation Matrix (Phases 10 & 11)
    # ------------------------------------------------------------------

    @classmethod
    def determine_context_classification(
        cls,
        market_level: MarketSignalLevel,
        info_level: PublicInformationSignalLevel,
        independent_sources_count: int,
        verified_evidence_count: int,
    ) -> tuple[AnticipationContextClassification, str]:
        """
        Deterministic interpretation matrix combining Market Signal with Public Information.

        Rule:
        - NEVER implies causation.
        - High market signal without media evidence is strictly MARKET_SIGNAL_ONLY.
        - Multiple independent sources with evidence yield MULTI_SOURCE_PUBLIC_INFORMATION.
        """
        # Unknown market (e.g. State bill or unmodelled pair)
        if market_level == MarketSignalLevel.UNKNOWN:
            if info_level == PublicInformationSignalLevel.NONE or verified_evidence_count == 0:
                return (
                    AnticipationContextClassification.INSUFFICIENT_EVIDENCE,
                    "Insufficient verified public-information evidence and market prediction unavailable.",
                )
            elif independent_sources_count >= 2:
                return (
                    AnticipationContextClassification.MULTI_SOURCE_PUBLIC_INFORMATION,
                    "Observable pre-event public information was documented across multiple independent sources before the official legislative event.",
                )
            else:
                return (
                    AnticipationContextClassification.PUBLIC_INFORMATION_SUPPORTED,
                    "Observable public-information evidence was present before the official legislative event.",
                )

        # Low market signal
        if market_level == MarketSignalLevel.LOW:
            if info_level == PublicInformationSignalLevel.NONE or verified_evidence_count == 0:
                return (
                    AnticipationContextClassification.NO_PRE_EVENT_SIGNAL,
                    "No measurable pre-event econometric movement or verified public information observed prior to event.",
                )
            elif info_level == PublicInformationSignalLevel.LOW:
                return (
                    AnticipationContextClassification.NO_PRE_EVENT_SIGNAL,
                    "Weak pre-event market signals and minimal public information diffusion observed prior to event.",
                )
            elif independent_sources_count >= 2 and info_level == PublicInformationSignalLevel.HIGH:
                return (
                    AnticipationContextClassification.MULTI_SOURCE_PUBLIC_INFORMATION,
                    "Observable pre-event public information was verified across multiple independent sources prior to the official event.",
                )
            else:
                return (
                    AnticipationContextClassification.PUBLIC_INFORMATION_SUPPORTED,
                    "Observable public-information evidence was present before the official event with low market price reaction.",
                )

        # Medium market signal
        if market_level == MarketSignalLevel.MEDIUM:
            if info_level == PublicInformationSignalLevel.NONE or verified_evidence_count == 0:
                return (
                    AnticipationContextClassification.MARKET_SIGNAL_ONLY,
                    "Moderate pre-event market drift observed without corroborating pre-event public-information records.",
                )
            elif independent_sources_count >= 2 and info_level in {PublicInformationSignalLevel.MEDIUM, PublicInformationSignalLevel.HIGH}:
                return (
                    AnticipationContextClassification.MULTI_SOURCE_PUBLIC_INFORMATION,
                    "Moderate pre-event market movement coincided with verified public-information evidence from multiple independent sources.",
                )
            else:
                return (
                    AnticipationContextClassification.PUBLIC_INFORMATION_SUPPORTED,
                    "Observable public-information evidence was present before the official event alongside moderate pre-event market signals.",
                )

        # High market signal
        if market_level == MarketSignalLevel.HIGH:
            if info_level == PublicInformationSignalLevel.NONE or verified_evidence_count == 0:
                return (
                    AnticipationContextClassification.MARKET_SIGNAL_ONLY,
                    "Abnormal pre-event market movement detected without corroborating pre-event public media records. Movement is categorized as market-signal-only.",
                )
            elif independent_sources_count >= 2 and info_level in {PublicInformationSignalLevel.MEDIUM, PublicInformationSignalLevel.HIGH}:
                return (
                    AnticipationContextClassification.MULTI_SOURCE_PUBLIC_INFORMATION,
                    "Strong pre-event market movement coincided with verifiable public information from multiple independent sources prior to official introduction.",
                )
            else:
                return (
                    AnticipationContextClassification.PUBLIC_INFORMATION_SUPPORTED,
                    "Observable public-information evidence was present before the official event alongside elevated pre-event market signals.",
                )

        return (
            AnticipationContextClassification.INSUFFICIENT_EVIDENCE,
            "Insufficient verified pre-event records to classify anticipation pattern.",
        )

    # ------------------------------------------------------------------
    # Core Context Synthesis
    # ------------------------------------------------------------------

    def build_evidence_context(
        self,
        bill: UnifiedBillRecord,
        company_isin: Optional[str] = None,
        company_symbol: Optional[str] = None,
        company_name: Optional[str] = None,
        additional_evidence: Optional[list[PublicInformationEvidence]] = None,
    ) -> AnticipationEvidenceContext:
        """
        Build additive AnticipationEvidenceContext for a bill or bill-company pair.
        Does NOT recalculate or mutate historical frozen anticipation records.
        """
        is_state = getattr(bill, "jurisdiction", "central").lower() == "state"

        # 1. Resolve market signal from frozen dataset
        market_summary = self._resolve_market_signal(bill.bill_id, company_isin, is_state)

        # 2. Collect evidence from adapters
        collected_evidence: list[PublicInformationEvidence] = []
        if additional_evidence:
            collected_evidence.extend(additional_evidence)

        # Query registered adapters
        for adapter in self._adapters:
            try:
                ad_items = adapter.discover_evidence(
                    bill=bill,
                    company_symbol=company_symbol,
                    company_isin=company_isin,
                    company_name=company_name,
                )
                collected_evidence.extend(ad_items)
            except Exception as e:
                logger.warning("Adapter %s failed during discovery: %s", getattr(adapter, "adapter_name", "unknown"), e)

        # Retrieve any previously stored evidence
        stored_items = self.evidence_repo.get_evidence_by_bill(bill.bill_id)
        collected_evidence.extend(stored_items)

        # Deduplicate and validate
        deduped = EvidenceDeduplicator.deduplicate(collected_evidence)

        # 3. Filter pre-event evidence
        pre_event_items: list[PublicInformationEvidence] = []
        all_dates: list[str] = []
        cred_counts: dict[str, int] = {}

        for item in deduped:
            if item.temporal_relation == TemporalRelation.PRE_EVENT and item.verification_status == VerificationStatus.VERIFIED:
                pre_event_items.append(item)
                all_dates.append(item.publication_timestamp[:10])
                c_tier = item.source_credibility.value if hasattr(item.source_credibility, "value") else str(item.source_credibility)
                cred_counts[c_tier] = cred_counts.get(c_tier, 0) + 1

        # 4. Public Information Scoring
        event_ref = getattr(bill, "introduction_date", "") or ""
        info_score = self.calculate_public_information_evidence_score(pre_event_items, event_ref)

        # Classify public info level
        if not pre_event_items or info_score == 0.0:
            info_level = PublicInformationSignalLevel.NONE
        elif info_score < 0.35:
            info_level = PublicInformationSignalLevel.LOW
        elif info_score < 0.65:
            info_level = PublicInformationSignalLevel.MEDIUM
        else:
            info_level = PublicInformationSignalLevel.HIGH

        independent_count = EvidenceDeduplicator.count_independent_sources(pre_event_items)
        diversity = EvidenceDeduplicator.calculate_source_diversity(pre_event_items)

        earliest_d = min(all_dates) if all_dates else None
        latest_d = max(all_dates) if all_dates else None
        trading_window_str = f"{earliest_d} to {latest_d}" if earliest_d and latest_d else None

        public_info_summary = PublicInformationSignalSummary(
            level=info_level,
            public_information_evidence_score=info_score,
            verified_pre_event_count=len(pre_event_items),
            independent_sources_count=independent_count,
            source_diversity_ratio=diversity,
            credibility_tier_summary=cred_counts,
            earliest_evidence_date=earliest_d,
            latest_evidence_date=latest_d,
            evidence_window_trading_days=trading_window_str,
        )

        # 5. Combined Context Classification & Interpretation
        classification, interpretation = self.determine_context_classification(
            market_level=market_summary.level,
            info_level=info_level,
            independent_sources_count=independent_count,
            verified_evidence_count=len(pre_event_items),
        )

        combined_summary = CombinedAnticipationContextSummary(
            classification=classification,
            interpretation=interpretation,
            market_signal=market_summary.level,
            information_signal=info_level,
            epistemic_tag="[EVIDENCE]",
            non_accusatory_disclaimer=NON_ACCUSATORY_DISCLAIMER,
        )

        # 6. Collect search trends
        trend_items = self.search_adapter.discover_trends(bill)

        context = AnticipationEvidenceContext(
            bill_id=bill.bill_id,
            company_isin=company_isin,
            company_symbol=company_symbol,
            jurisdiction=getattr(bill, "jurisdiction", "central") or "central",
            market_signal=market_summary,
            public_information_signal=public_info_summary,
            combined_context=combined_summary,
            evidence_items=deduped,
            search_trend_items=trend_items,
            created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )

        # Cache or persist
        self.evidence_repo.save_context(context)
        return context

    def _resolve_market_signal(
        self,
        bill_id: str,
        company_isin: Optional[str],
        is_state: bool,
    ) -> MarketSignalSummary:
        """
        Safely resolve pre-event market signal from frozen dataset.
        For State bills, STRICTLY returns UNKNOWN with 0 metrics (firewall).
        """
        if is_state or not company_isin:
            return MarketSignalSummary(
                level=MarketSignalLevel.UNKNOWN,
                market_signal_score=0.0,
                car_magnitude=0.0,
                z_score=0.0,
                directional_persistence=0.0,
                volatility=0.0,
                signals_detected=[],
            )

        # Look up frozen anticipation record
        score: Optional[AnticipationScore] = self.anticipation_repo.get_score(bill_id, company_isin)
        if not score:
            return MarketSignalSummary(
                level=MarketSignalLevel.UNKNOWN,
                market_signal_score=0.0,
                car_magnitude=0.0,
                z_score=0.0,
                directional_persistence=0.0,
                volatility=0.0,
                signals_detected=[],
            )

        m_score = float(getattr(score, "market_signal_score", 0.0))
        if m_score >= 0.50:
            m_level = MarketSignalLevel.HIGH
        elif m_score >= 0.25:
            m_level = MarketSignalLevel.MEDIUM
        else:
            m_level = MarketSignalLevel.LOW

        car_mag = 0.0
        z_val = 0.0
        signals = list(getattr(score, "detected_signals", []))

        if hasattr(score, "window_stats") and "[-30,-1]" in score.window_stats:
            cum_win = score.window_stats["[-30,-1]"]
            car_mag = abs(float(getattr(cum_win, "cumulative_abnormal_return", 0.0)))
            z_val = float(getattr(cum_win, "ar_z_score", 0.0))

        return MarketSignalSummary(
            level=m_level,
            market_signal_score=m_score,
            car_magnitude=round(car_mag, 4),
            z_score=round(z_val, 4),
            directional_persistence=0.70 if "directional_persistence" in signals else 0.50,
            volatility=0.02,
            signals_detected=signals,
        )

    # ------------------------------------------------------------------
    # Monitoring Integration (Phase 18)
    # ------------------------------------------------------------------

    def promote_monitoring_event_to_evidence(
        self,
        event: ChangeEvent,
        bill: UnifiedBillRecord,
    ) -> Optional[PublicInformationEvidence]:
        """
        Promote an OBSERVED MONITORING EVENT to PUBLIC INFORMATION EVIDENCE.

        Guarantees:
        - Distinct from PREDICTION.
        - Preserves full provenance: originating_event_id, source URL, timestamp.
        - Strictly evaluates temporal anti-leakage.
        """
        event_ref = getattr(bill, "introduction_date", "") or ""
        event_ts = event.detected_at or datetime.now(timezone.utc).isoformat()

        temp_rel, temp_reason = EvidenceValidator.evaluate_temporal_relation(event_ts, event_ref)

        headline = f"Official Monitoring Update: {event.change_type.value} on {bill.title}"
        summary = (
            f"Automated statutory monitoring detected {event.change_type.value} event "
            f"for bill '{bill.title}'. {event.description or ''}"
        )

        rel, strength, e_m, s_m, k_m, m_reason = EvidenceValidator.evaluate_relevance(
            bill=bill,
            headline=headline,
            summary=summary,
        )

        ev_id = f"pie_mon_{event.event_id[:12]}"

        evidence = PublicInformationEvidence(
            evidence_id=ev_id,
            bill_id=bill.bill_id,
            jurisdiction=getattr(bill, "jurisdiction", "central") or "central",
            source_type=PublicInformationSourceType.OFFICIAL_LEGISLATIVE,
            source_name=f"Legislative Monitoring Engine ({getattr(bill, 'house', 'Parliament')})",
            source_url=getattr(bill, "source_url", "") or f"https://prsindia.org/bills/{bill.bill_id}",
            publication_timestamp=event_ts,
            discovery_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            event_reference=event_ref,
            headline=headline,
            summary=summary,
            relevance=rel,
            evidence_strength=strength,
            temporal_relation=temp_rel,
            source_credibility=SourceCredibilityTier.TIER_1,
            entity_matches=e_m,
            sector_matches=s_m,
            keywords=k_m,
            provenance={
                "originating_event_id": event.event_id,
                "change_type": event.change_type.value,
                "source_system": "Task 8.11/8.26 Monitoring Runner",
                "detected_at": event.detected_at,
                "temporal_reason": temp_reason,
            },
            verification_status=(
                VerificationStatus.VERIFIED
                if temp_rel != TemporalRelation.UNKNOWN
                else VerificationStatus.TEMPORALLY_UNKNOWN
            ),
            match_reason=f"Promoted from official monitoring event. {m_reason}",
        )

        self.evidence_repo.save_evidence(evidence)
        return evidence
