"""
services/anticipation_evidence/base_adapter.py
==============================================
Abstract base class for extensible public-information evidence source adapters.

All adapters must inherit from BaseEvidenceAdapter, allowing pluggable integrations
(official gazettes, mainstream press, GDELT, Google Trends, parliamentary bulletins).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from schemas.anticipation_evidence import (
    PublicInformationEvidence,
    PublicInformationSourceType,
    SourceCredibilityTier,
)
from schemas.unified_bill_record import UnifiedBillRecord


class BaseEvidenceAdapter(ABC):
    """
    Abstract interface for public information evidence adapters.
    """

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Human-readable identifier for the adapter."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> PublicInformationSourceType:
        """Default source taxonomy classification."""
        pass

    @property
    @abstractmethod
    def default_credibility(self) -> SourceCredibilityTier:
        """Default credibility tier for this source category."""
        pass

    @abstractmethod
    def discover_evidence(
        self,
        bill: UnifiedBillRecord,
        company_symbol: Optional[str] = None,
        company_isin: Optional[str] = None,
        company_name: Optional[str] = None,
        max_results: int = 10,
    ) -> list[PublicInformationEvidence]:
        """
        Discover public-information evidence candidates for the given bill and optional company.
        Must return strongly-typed PublicInformationEvidence objects.
        """
        pass
