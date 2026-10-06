"""
services/anticipation_evidence/search_trend_adapter.py
======================================================
Search-trend and public-attention signal adapter.

Phase 13: Search-Trend Signal
- Captures Google Trends or public search-index fluctuations.
- Strictly classified as PUBLIC_ATTENTION_SIGNAL, NOT PUBLIC_KNOWLEDGE_PROOF.
- Credibility tier: TIER_4.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Optional
import uuid

from config.logging_config import get_logger
from schemas.anticipation_evidence import (
    EvidenceStrength,
    PublicInformationEvidence,
    PublicInformationSourceType,
    SearchTrendEvidence,
    SourceCredibilityTier,
    TemporalRelation,
    VerificationStatus,
)
from schemas.unified_bill_record import UnifiedBillRecord
from services.anticipation_evidence.base_adapter import BaseEvidenceAdapter
from services.anticipation_evidence.evidence_validator import EvidenceValidator

logger = get_logger(__name__)


class SearchTrendAdapter(BaseEvidenceAdapter):
    """
    Adapter that parses search trend series and produces both SearchTrendEvidence records
    and PublicInformationEvidence candidates.
    """

    def __init__(
        self,
        trend_provider: Optional[Callable[[str, str], list[dict[str, Any]]]] = None,
    ) -> None:
        self._trend_provider = trend_provider

    @property
    def adapter_name(self) -> str:
        return "SearchTrendAttentionAdapter"

    @property
    def source_type(self) -> PublicInformationSourceType:
        return PublicInformationSourceType.SEARCH_TREND

    @property
    def default_credibility(self) -> SourceCredibilityTier:
        return SourceCredibilityTier.TIER_4

    def discover_trends(
        self,
        bill: UnifiedBillRecord,
        region: str = "IN",
    ) -> list[SearchTrendEvidence]:
        """
        Discover raw search trend signals for the bill.
        """
        if not self._trend_provider:
            return []

        raw_trends = self._trend_provider(bill.title, region)
        trend_items: list[SearchTrendEvidence] = []

        for item in raw_trends:
            val = float(item.get("trend_value", 0.0))
            baseline = float(item.get("baseline_value", 50.0))
            is_spike = bool(item.get("spike_indicator", val >= baseline * 1.5))

            st = SearchTrendEvidence(
                query=str(item.get("query", bill.title)),
                region=str(item.get("region", region)),
                timestamp=str(item.get("timestamp", datetime.now(timezone.utc).isoformat())),
                trend_value=val,
                baseline_value=baseline,
                spike_indicator=is_spike,
                source=str(item.get("source", "Google Trends")),
                classification="PUBLIC_ATTENTION_SIGNAL",
                provenance={
                    "adapter": self.adapter_name,
                    "bill_id": bill.bill_id,
                    "search_engine": "Public Web Search Trends",
                },
            )
            trend_items.append(st)

        return trend_items

    def discover_evidence(
        self,
        bill: UnifiedBillRecord,
        company_symbol: Optional[str] = None,
        company_isin: Optional[str] = None,
        company_name: Optional[str] = None,
        max_results: int = 10,
    ) -> list[PublicInformationEvidence]:
        """
        Converts significant search trend spikes into PublicInformationEvidence candidates.
        """
        trends = self.discover_trends(bill)
        evidence_list: list[PublicInformationEvidence] = []
        event_ref = getattr(bill, "introduction_date", "") or ""

        for st in trends:
            if not st.spike_indicator:
                continue

            temp_rel, _ = EvidenceValidator.evaluate_temporal_relation(st.timestamp, event_ref)
            ev_id = f"pie_trend_{uuid.uuid5(uuid.NAMESPACE_URL, f'{bill.bill_id}_{st.query}_{st.timestamp}').hex[:12]}"

            headline = f"Search Interest Spike: '{st.query}'"
            summary = (
                f"Statistically significant search trend spike ({st.trend_value:.1f} vs baseline {st.baseline_value:.1f}) "
                f"observed in region {st.region} on {st.timestamp[:10]}. Classified as PUBLIC_ATTENTION_SIGNAL."
            )

            rel, strength, e_m, s_m, k_m, m_reason = EvidenceValidator.evaluate_relevance(
                bill=bill,
                headline=headline,
                summary=summary,
                company_symbol=company_symbol,
                company_isin=company_isin,
                company_name=company_name,
            )

            ev = PublicInformationEvidence(
                evidence_id=ev_id,
                bill_id=bill.bill_id,
                jurisdiction=getattr(bill, "jurisdiction", "central") or "central",
                source_type=PublicInformationSourceType.SEARCH_TREND,
                source_name=st.source,
                source_url=f"https://trends.google.com/trends/explore?q={st.query}",
                publication_timestamp=st.timestamp,
                discovery_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                event_reference=event_ref,
                headline=headline,
                summary=summary,
                relevance=rel,
                evidence_strength=strength,
                temporal_relation=temp_rel,
                source_credibility=SourceCredibilityTier.TIER_4,
                entity_matches=e_m,
                sector_matches=s_m,
                keywords=k_m,
                provenance={
                    "adapter": self.adapter_name,
                    "classification": "PUBLIC_ATTENTION_SIGNAL",
                    "trend_value": st.trend_value,
                    "baseline_value": st.baseline_value,
                },
                verification_status=(
                    VerificationStatus.VERIFIED
                    if temp_rel != TemporalRelation.UNKNOWN
                    else VerificationStatus.TEMPORALLY_UNKNOWN
                ),
                match_reason=f"Public search attention spike for legislative query. {m_reason}",
            )
            evidence_list.append(ev)

        return evidence_list[:max_results]
