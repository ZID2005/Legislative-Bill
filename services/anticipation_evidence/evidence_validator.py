"""
services/anticipation_evidence/evidence_validator.py
====================================================
Deterministic evidence validator and anti-leakage temporal engine.

Phase 5: Temporal Anti-Leakage Logic
Phase 6: Deterministic Relevance & Match Reason Engine
Phase 22: Provenance Completeness
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.anticipation_evidence import (
    EvidenceStrength,
    PublicInformationEvidence,
    TemporalRelation,
    VerificationStatus,
)
from schemas.unified_bill_record import UnifiedBillRecord
from services.anticipation_evidence.evidence_normalizer import EvidenceNormalizer

logger = get_logger(__name__)


class EvidenceValidator:
    """
    Validates temporal anti-leakage invariants and calculates deterministic relevance matching.
    """

    @classmethod
    def evaluate_temporal_relation(
        cls,
        publication_timestamp_str: str,
        official_event_timestamp_str: str,
    ) -> tuple[TemporalRelation, str]:
        """
        Evaluate temporal relation with strict anti-leakage rules:
        - If parsing fails for either timestamp: UNKNOWN
        - publication_timestamp < official_event_timestamp:
            * If published on earlier calendar day: PRE_EVENT
            * If published on same calendar day:
                If both timestamps provide intra-day time precision (HH:MM:SS) and pub < event:
                    PRE_EVENT
                Else if same calendar day with date-only or insufficient time precision:
                    UNKNOWN (do NOT guess!)
        - publication_timestamp == official_event_timestamp: SAME_DAY
        - publication_timestamp > official_event_timestamp:
            * If same calendar day (with pub > event): SAME_DAY
            * If later calendar day: POST_EVENT

        Returns
        -------
        tuple[TemporalRelation, str]
            (TemporalRelation, explanation_reason)
        """
        pub_dt = EvidenceNormalizer.parse_timestamp(publication_timestamp_str)
        event_dt = EvidenceNormalizer.parse_timestamp(official_event_timestamp_str)

        if not pub_dt or not event_dt:
            return TemporalRelation.UNKNOWN, "Insufficient timestamp precision to determine temporal relation."

        # Check precision: did both strings include time components?
        pub_has_time = "T" in publication_timestamp_str or ":" in publication_timestamp_str
        event_has_time = "T" in official_event_timestamp_str or ":" in official_event_timestamp_str

        pub_date = pub_dt.date()
        event_date = event_dt.date()

        if pub_date < event_date:
            days_prior = (event_date - pub_date).days
            return TemporalRelation.PRE_EVENT, f"Published {days_prior} day(s) before official legislative event date."

        elif pub_date > event_date:
            days_after = (pub_date - event_date).days
            return TemporalRelation.POST_EVENT, f"Published {days_after} day(s) after official legislative event date."

        else:
            # Same calendar day!
            if not (pub_has_time and event_has_time):
                # Date-only comparison on same day has insufficient precision
                return (
                    TemporalRelation.UNKNOWN,
                    "Published on the same date as official event, but timestamp precision is insufficient to verify prior release.",
                )

            # Both have time precision
            if pub_dt < event_dt:
                diff_seconds = (event_dt - pub_dt).total_seconds()
                diff_hours = diff_seconds / 3600.0
                return (
                    TemporalRelation.PRE_EVENT,
                    f"Published {diff_hours:.1f} hours prior to official event timestamp on the same date.",
                )
            elif pub_dt == event_dt:
                return (
                    TemporalRelation.SAME_DAY,
                    "Published concurrently with official event timestamp.",
                )
            else:
                return (
                    TemporalRelation.SAME_DAY,
                    "Published on same date after official event timestamp.",
                )

    @classmethod
    def evaluate_relevance(
        cls,
        bill: UnifiedBillRecord,
        headline: str,
        summary: str,
        company_symbol: Optional[str] = None,
        company_isin: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> tuple[float, EvidenceStrength, list[str], list[str], list[str], str]:
        """
        Deterministic evidence matching against bill, sectors, and optional company.

        Returns
        -------
        tuple:
          (relevance_score, strength, entity_matches, sector_matches, keyword_matches, match_reason)
        """
        text = f"{headline} {summary}".lower()
        title_norm = EvidenceNormalizer.normalize_title(bill.title)
        bill_id_tokens = set(re.findall(r"\w+", bill.bill_id.lower()))
        bill_num_tokens = set(re.findall(r"\w+", (bill.bill_number or "").lower())) if bill.bill_number else set()

        match_reasons: list[str] = []
        entity_matches: list[str] = []
        sector_matches: list[str] = []
        keyword_matches: list[str] = []
        base_relevance = 0.0

        # 1. Exact bill title or strong phrase match
        if title_norm and title_norm in EvidenceNormalizer.normalize_title(text):
            base_relevance += 0.50
            match_reasons.append(f"Direct mention of bill title '{bill.title}'")
        else:
            # Token overlap with bill title (ignoring generic terms)
            title_tokens = set(re.findall(r"\w+", title_norm)) - {
                "the", "bill", "act", "amendment", "2023", "2024", "2025", "2026", "of", "and", "for"
            }
            if title_tokens:
                overlap = title_tokens.intersection(set(re.findall(r"\w+", text)))
                overlap_ratio = len(overlap) / len(title_tokens)
                if overlap_ratio >= 0.6:
                    base_relevance += 0.35 * overlap_ratio
                    matched_words = ", ".join(sorted(overlap))
                    keyword_matches.extend(sorted(overlap))
                    match_reasons.append(f"Substantial title keyword match ({matched_words})")

        # 2. Bill number match
        if bill.bill_number and bill.bill_number.lower() in text:
            base_relevance += 0.25
            match_reasons.append(f"Explicit bill number reference '{bill.bill_number}'")

        # 3. Ministry match
        ministry = getattr(bill, "ministry", "") or ""
        if ministry and len(ministry) > 3 and ministry.lower() in text:
            base_relevance += 0.15
            match_reasons.append(f"References nodal ministry '{ministry}'")

        # 4. Sector matches
        bill_sectors = (
            getattr(bill, "economic_sectors", None)
            or getattr(bill, "sectors", None)
            or []
        )
        for sec in bill_sectors:
            if sec.lower() in text:
                sector_matches.append(sec)
                base_relevance += 0.10
        if sector_matches:
            match_reasons.append(f"References affected sector(s): {', '.join(sector_matches)}")

        # 5. Company matches if evaluating company pair
        if company_name and len(company_name) > 3 and company_name.lower() in text:
            entity_matches.append(company_name)
            base_relevance += 0.20
            match_reasons.append(f"Explicitly references company '{company_name}'")
        if company_symbol and len(company_symbol) >= 3 and company_symbol.lower() in text:
            if company_symbol not in entity_matches:
                entity_matches.append(company_symbol)
            base_relevance += 0.15
            match_reasons.append(f"Mentions ticker symbol '{company_symbol}'")
        if company_isin and company_isin.lower() in text:
            if company_isin not in entity_matches:
                entity_matches.append(company_isin)
            base_relevance += 0.25
            match_reasons.append(f"Mentions statutory ISIN '{company_isin}'")

        # 6. Jurisdiction match
        jurisdiction = getattr(bill, "jurisdiction", "central") or "central"
        state = getattr(bill, "state", None)
        if state and state.lower() in text:
            match_reasons.append(f"References subnational jurisdiction '{state}'")

        # Normalize score
        final_relevance = min(1.0, max(0.0, round(base_relevance, 4)))

        # Evidentiary strength
        if final_relevance >= 0.70:
            strength = EvidenceStrength.STRONG
        elif final_relevance >= 0.35:
            strength = EvidenceStrength.MODERATE
        else:
            strength = EvidenceStrength.WEAK

        full_reason = "; ".join(match_reasons) if match_reasons else "General domain keywords without specific bill/entity citation."
        return final_relevance, strength, entity_matches, sector_matches, keyword_matches, full_reason

    @classmethod
    def validate_evidence(
        cls,
        evidence: PublicInformationEvidence,
        bill: UnifiedBillRecord,
    ) -> PublicInformationEvidence:
        """
        Validate and enrich a PublicInformationEvidence record with strict temporal
        classification, deterministic hashing, and data quality status.
        """
        # 1. Temporal relationship
        temp_rel, temp_reason = cls.evaluate_temporal_relation(
            evidence.publication_timestamp,
            evidence.event_reference or getattr(bill, "introduction_date", "") or "",
        )
        evidence.temporal_relation = temp_rel

        # 2. Verification status
        if temp_rel == TemporalRelation.UNKNOWN:
            evidence.verification_status = VerificationStatus.TEMPORALLY_UNKNOWN
        elif not evidence.source_url or not evidence.headline:
            evidence.verification_status = VerificationStatus.INSUFFICIENT_DATA
        else:
            evidence.verification_status = VerificationStatus.VERIFIED

        # 3. Compute hash
        evidence.hash = evidence.compute_hash()

        # 4. Provenance
        if not evidence.provenance:
            evidence.provenance = {
                "source_name": evidence.source_name,
                "source_url": evidence.source_url,
                "publication_timestamp": evidence.publication_timestamp,
                "temporal_relation": evidence.temporal_relation.value,
                "credibility_tier": evidence.source_credibility.value,
                "match_reason": evidence.match_reason,
            }

        return evidence
