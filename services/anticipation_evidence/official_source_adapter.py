"""
services/anticipation_evidence/official_source_adapter.py
=========================================================
Adapter for official parliamentary, government, and regulatory records.

Source Taxonomy:
- OFFICIAL_LEGISLATIVE
- OFFICIAL_GOVERNMENT
- PARLIAMENTARY
- REGULATOR
Credibility: TIER_1 (Official government / legislature / regulator)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import uuid

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
from services.anticipation_evidence.evidence_normalizer import EvidenceNormalizer
from services.anticipation_evidence.evidence_validator import EvidenceValidator


class OfficialSourceAdapter(BaseEvidenceAdapter):
    """
    Adapter that extracts official pre-event publication records from authoritative sources:
    - Lok Sabha / Rajya Sabha legislative bulletins
    - Official Gazette notifications
    - PRS Legislative Research bill tracking dossiers
    - Ministry press releases & public consultation papers
    """

    @property
    def adapter_name(self) -> str:
        return "OfficialLegislativeAdapter"

    @property
    def source_type(self) -> PublicInformationSourceType:
        return PublicInformationSourceType.OFFICIAL_LEGISLATIVE

    @property
    def default_credibility(self) -> SourceCredibilityTier:
        return SourceCredibilityTier.TIER_1

    def discover_evidence(
        self,
        bill: UnifiedBillRecord,
        company_symbol: Optional[str] = None,
        company_isin: Optional[str] = None,
        company_name: Optional[str] = None,
        max_results: int = 10,
    ) -> list[PublicInformationEvidence]:
        """
        Extract official public records for the bill.
        """
        evidence_list: list[PublicInformationEvidence] = []
        event_ref = getattr(bill, "introduction_date", "") or ""

        # 1. Official Parliamentary Introduction Record
        if getattr(bill, "source_url", None):
            source_url = bill.source_url
            headline = f"Official Introduction: {bill.title}"
            summary = (
                f"Official legislative record for {bill.title} (Bill No. {bill.bill_number or 'N/A'}) "
                f"under {getattr(bill, 'house', 'Parliament') or 'Legislature'}."
            )

            # Build evidence
            pub_ts = (
                getattr(bill, "introduction_date", "")
                or getattr(bill, "status_date", "")
                or datetime.now(timezone.utc).isoformat()
            )
            if len(pub_ts) == 10:  # YYYY-MM-DD
                pub_ts = f"{pub_ts}T09:00:00Z"

            ev_id = f"pie_off_{uuid.uuid5(uuid.NAMESPACE_URL, f'{bill.bill_id}_official_{source_url}').hex[:12]}"
            rel, strength, e_m, s_m, k_m, m_reason = EvidenceValidator.evaluate_relevance(
                bill=bill,
                headline=headline,
                summary=summary,
                company_symbol=company_symbol,
                company_isin=company_isin,
                company_name=company_name,
            )

            temp_rel, _ = EvidenceValidator.evaluate_temporal_relation(pub_ts, event_ref)

            ev = PublicInformationEvidence(
                evidence_id=ev_id,
                bill_id=bill.bill_id,
                jurisdiction=getattr(bill, "jurisdiction", "central") or "central",
                source_type=PublicInformationSourceType.OFFICIAL_LEGISLATIVE,
                source_name="Official Parliament Record / PRS",
                source_url=source_url,
                publication_timestamp=pub_ts,
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
                    "adapter": self.adapter_name,
                    "source_authority": "Parliament of India / State Assembly",
                    "official_pdf_url": getattr(bill, "pdf_url", None),
                },
                verification_status=VerificationStatus.VERIFIED,
                match_reason=m_reason,
            )
            evidence_list.append(ev)

        return evidence_list[:max_results]
