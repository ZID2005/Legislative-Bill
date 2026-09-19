"""
ingestion/state package
=======================
Data acquisition and normalization layer for Indian State legislative bills.
"""

from ingestion.state.base_adapter import BaseStateSourceAdapter
from ingestion.state.deduplicator import StateBillDeduplicator
from ingestion.state.normalizer import StateBillNormalizer
from ingestion.state.provenance import (
    BillProvenanceRecord,
    FieldProvenance,
    ProvenanceLevel,
    StateProvenanceTracker,
)
from ingestion.state.registry import StateSourceRegistry
from ingestion.state.service import StateIngestionService

__all__ = [
    "BaseStateSourceAdapter",
    "StateBillDeduplicator",
    "StateBillNormalizer",
    "BillProvenanceRecord",
    "FieldProvenance",
    "ProvenanceLevel",
    "StateProvenanceTracker",
    "StateSourceRegistry",
    "StateIngestionService",
]
