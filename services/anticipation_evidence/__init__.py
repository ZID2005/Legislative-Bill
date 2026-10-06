"""
services/anticipation_evidence/__init__.py
==========================================
Package exports for Task 8.29 Anticipation Evidence Enrichment & Media Diffusion Intelligence.
"""

from services.anticipation_evidence.base_adapter import BaseEvidenceAdapter
from services.anticipation_evidence.official_source_adapter import OfficialSourceAdapter
from services.anticipation_evidence.news_adapter import NewsAdapter
from services.anticipation_evidence.search_trend_adapter import SearchTrendAdapter
from services.anticipation_evidence.evidence_normalizer import EvidenceNormalizer
from services.anticipation_evidence.evidence_validator import EvidenceValidator
from services.anticipation_evidence.evidence_deduplicator import EvidenceDeduplicator
from services.anticipation_evidence.evidence_repository import AnticipationEvidenceRepository
from services.anticipation_evidence.evidence_service import AnticipationEvidenceService

__all__ = [
    "BaseEvidenceAdapter",
    "OfficialSourceAdapter",
    "NewsAdapter",
    "SearchTrendAdapter",
    "EvidenceNormalizer",
    "EvidenceValidator",
    "EvidenceDeduplicator",
    "AnticipationEvidenceRepository",
    "AnticipationEvidenceService",
]
