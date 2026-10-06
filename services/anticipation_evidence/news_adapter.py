"""
services/anticipation_evidence/news_adapter.py
==============================================
Pluggable news, business, and financial media source adapter.

Phase 12: Media Discovery Adapter
Phase 14: GDELT / News Integration Boundary
- Pluggable provider architecture.
- Graceful "NO MEDIA DATA AVAILABLE" state when no external provider configured.
- Pluggable mock/test provider for test assertions.
- Does not make network availability a requirement for tests.
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
    SourceCredibilityTier,
    TemporalRelation,
    VerificationStatus,
)
from schemas.unified_bill_record import UnifiedBillRecord
from services.anticipation_evidence.base_adapter import BaseEvidenceAdapter
from services.anticipation_evidence.evidence_validator import EvidenceValidator

logger = get_logger(__name__)


class NewsAdapter(BaseEvidenceAdapter):
    """
    Adapter for mainstream news, business media, and financial press articles.
    """

    def __init__(
        self,
        custom_provider: Optional[Callable[[UnifiedBillRecord, Optional[str]], list[dict[str, Any]]]] = None,
    ) -> None:
        self._custom_provider = custom_provider

    @property
    def adapter_name(self) -> str:
        return "FinancialAndMainstreamNewsAdapter"

    @property
    def source_type(self) -> PublicInformationSourceType:
        return PublicInformationSourceType.FINANCIAL_MEDIA

    @property
    def default_credibility(self) -> SourceCredibilityTier:
        return SourceCredibilityTier.TIER_2

    def discover_evidence(
        self,
        bill: UnifiedBillRecord,
        company_symbol: Optional[str] = None,
        company_isin: Optional[str] = None,
        company_name: Optional[str] = None,
        max_results: int = 10,
    ) -> list[PublicInformationEvidence]:
        """
        Discover news articles referencing the legislative measure.
        If no provider is configured, returns empty list gracefully.
        """
        if not self._custom_provider:
            # Graceful "NO MEDIA DATA AVAILABLE" state
            logger.debug("No external news provider registered; returning empty media evidence list.")
            return []

        raw_items = self._custom_provider(bill, company_symbol)
        if not raw_items:
            return []

        event_ref = getattr(bill, "introduction_date", "") or ""
        evidence_list: list[PublicInformationEvidence] = []

        for item in raw_items[:max_results]:
            pub_ts = item.get("publication_timestamp") or item.get("published_at") or ""
            url = item.get("source_url") or item.get("url") or ""
            headline = item.get("headline") or item.get("title") or ""
            summary = item.get("summary") or item.get("description") or ""
            source_name = item.get("source_name") or item.get("publisher") or "Mainstream Media"

            source_type_val = item.get("source_type", PublicInformationSourceType.NEWS)
            if isinstance(source_type_val, str):
                try:
                    source_type_val = PublicInformationSourceType(source_type_val)
                except ValueError:
                    source_type_val = PublicInformationSourceType.NEWS

            credibility_val = item.get("source_credibility", SourceCredibilityTier.TIER_2)
            if isinstance(credibility_val, str):
                try:
                    credibility_val = SourceCredibilityTier(credibility_val)
                except ValueError:
                    credibility_val = SourceCredibilityTier.TIER_2

            rel, strength, e_m, s_m, k_m, m_reason = EvidenceValidator.evaluate_relevance(
                bill=bill,
                headline=headline,
                summary=summary,
                company_symbol=company_symbol,
                company_isin=company_isin,
                company_name=company_name,
            )

            temp_rel, _ = EvidenceValidator.evaluate_temporal_relation(pub_ts, event_ref)

            ev_id = f"pie_news_{uuid.uuid5(uuid.NAMESPACE_URL, f'{bill.bill_id}_{url}_{pub_ts}').hex[:12]}"

            ev = PublicInformationEvidence(
                evidence_id=ev_id,
                bill_id=bill.bill_id,
                jurisdiction=getattr(bill, "jurisdiction", "central") or "central",
                source_type=source_type_val,
                source_name=source_name,
                source_url=url,
                publication_timestamp=pub_ts,
                discovery_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                event_reference=event_ref,
                headline=headline,
                summary=summary,
                relevance=rel,
                evidence_strength=strength,
                temporal_relation=temp_rel,
                source_credibility=credibility_val,
                entity_matches=e_m,
                sector_matches=s_m,
                keywords=k_m,
                provenance={
                    "adapter": self.adapter_name,
                    "provider": getattr(self._custom_provider, "__name__", "custom_provider"),
                    "raw_metadata": item.get("metadata", {}),
                },
                verification_status=(
                    VerificationStatus.VERIFIED
                    if temp_rel != TemporalRelation.UNKNOWN
                    else VerificationStatus.TEMPORALLY_UNKNOWN
                ),
                match_reason=m_reason,
            )
            evidence_list.append(ev)

        return evidence_list
