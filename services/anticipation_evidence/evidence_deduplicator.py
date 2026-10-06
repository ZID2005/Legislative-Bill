"""
services/anticipation_evidence/evidence_deduplicator.py
======================================================
Deterministic duplicate and syndication detection for public-information evidence.

Phase 7: Duplicate & Syndication Control
- Prevents syndicated copies across media outlets from being counted as independent evidence.
- Flags duplicate_of / canonical_evidence_id on derived items.
- Computes independent publisher counts and source diversity ratios.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Optional
from urllib.parse import urlparse

from config.logging_config import get_logger
from schemas.anticipation_evidence import (
    PublicInformationEvidence,
    PublicInformationSourceType,
)
from services.anticipation_evidence.evidence_normalizer import EvidenceNormalizer

logger = get_logger(__name__)


def _extract_domain(url: str) -> str:
    """Extract base hostname/domain from URL."""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def _title_similarity(t1: str, t2: str) -> float:
    """Calculate normalized token-based sequence similarity between two titles."""
    n1 = EvidenceNormalizer.normalize_title(t1)
    n2 = EvidenceNormalizer.normalize_title(t2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return SequenceMatcher(None, n1, n2).ratio()


class EvidenceDeduplicator:
    """
    Identifies exact and syndicated duplicate evidence items.
    """

    @classmethod
    def deduplicate(
        cls,
        evidence_items: list[PublicInformationEvidence],
    ) -> list[PublicInformationEvidence]:
        """
        Process a list of PublicInformationEvidence items:
        - Links duplicate items to canonical parent via duplicate_of and canonical_evidence_id.
        - Preserves chronological order (earliest published is canonical).
        - Returns list with duplicate_of populated on duplicate entries.
        """
        if not evidence_items:
            return []

        # Sort chronologically so earliest is candidate canonical
        sorted_items = sorted(
            evidence_items,
            key=lambda x: (x.publication_timestamp, x.evidence_id),
        )

        processed: list[PublicInformationEvidence] = []
        canonical_pool: list[PublicInformationEvidence] = []

        for item in sorted_items:
            canonical_match: Optional[PublicInformationEvidence] = None

            item_norm_url = EvidenceNormalizer.normalize_url(item.source_url)
            item_norm_title = EvidenceNormalizer.normalize_title(item.headline)
            item_hash = item.hash

            for canon in canonical_pool:
                canon_norm_url = EvidenceNormalizer.normalize_url(canon.source_url)
                canon_norm_title = EvidenceNormalizer.normalize_title(canon.headline)

                # Condition 1: Same hash
                if item_hash and canon.hash and item_hash == canon.hash:
                    canonical_match = canon
                    break

                # Condition 2: Identical canonical URL
                if item_norm_url and canon_norm_url and item_norm_url == canon_norm_url:
                    canonical_match = canon
                    break

                # Condition 3: Exact same title & same publication date (Syndicated news feed)
                pub_item_dt = EvidenceNormalizer.parse_timestamp(item.publication_timestamp)
                pub_canon_dt = EvidenceNormalizer.parse_timestamp(canon.publication_timestamp)
                same_date = (
                    pub_item_dt
                    and pub_canon_dt
                    and pub_item_dt.date() == pub_canon_dt.date()
                )

                if same_date and _title_similarity(item.headline, canon.headline) >= 0.85:
                    canonical_match = canon
                    break

            if canonical_match:
                item.duplicate_of = canonical_match.evidence_id
                item.canonical_evidence_id = canonical_match.evidence_id
            else:
                item.duplicate_of = None
                item.canonical_evidence_id = item.evidence_id
                canonical_pool.append(item)

            processed.append(item)

        return processed

    @classmethod
    def count_independent_sources(
        cls,
        evidence_items: list[PublicInformationEvidence],
    ) -> int:
        """
        Count the number of unique, non-syndicated publishers/sources.
        Syndicated copies (with duplicate_of set) do NOT contribute to independent source count.
        """
        independent_publishers: set[str] = set()

        for ev in evidence_items:
            if ev.duplicate_of:
                # Skip duplicate / syndicated copies
                continue
            # Extract domain or source name
            domain = _extract_domain(ev.source_url)
            pub_key = domain or ev.source_name.strip().lower()
            if pub_key:
                independent_publishers.add(pub_key)

        return len(independent_publishers)

    @classmethod
    def calculate_source_diversity(
        cls,
        evidence_items: list[PublicInformationEvidence],
    ) -> float:
        """
        Calculate source diversity ratio [0.0, 1.0].
        Considers unique source types and distinct publishers among canonical items.
        """
        canonical_items = [ev for ev in evidence_items if not ev.duplicate_of]
        if not canonical_items:
            return 0.0

        unique_source_types = {ev.source_type for ev in canonical_items}
        unique_publishers = {
            _extract_domain(ev.source_url) or ev.source_name.strip().lower()
            for ev in canonical_items
        }

        # Diversity ratio scales with distinct publishers (up to 3) and types (up to 3)
        type_factor = min(1.0, len(unique_source_types) / 2.0)
        pub_factor = min(1.0, len(unique_publishers) / 3.0)

        diversity = 0.5 * type_factor + 0.5 * pub_factor
        return round(float(diversity), 4)
