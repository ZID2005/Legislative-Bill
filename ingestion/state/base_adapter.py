"""
ingestion/state/base_adapter.py
===============================
Abstract base adapter for State legislative bill sources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from config.logging_config import get_logger
from ingestion.parliament.connector import ParliamentConnector
from schemas.state_source import StateBillSource

logger = get_logger(__name__)


class BaseStateSourceAdapter(ABC):
    """
    Abstract interface for State-specific legislative bill source adapters.
    """

    def __init__(
        self,
        source: StateBillSource,
        connector: Optional[ParliamentConnector] = None,
    ) -> None:
        self.source = source
        self.connector = connector or ParliamentConnector()

    @abstractmethod
    async def discover_bills(
        self,
        year: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Query the official state source portal to discover bill listings.

        Returns
        -------
        list[dict]
            Raw bill records extracted from the official listing.
        """
        raise NotImplementedError

    async def fetch_document(self, document_url: str) -> Optional[bytes]:
        """
        Fetch binary PDF document from an authoritative document URL.
        """
        try:
            content = await self.connector.fetch(document_url, is_binary=True)
            if isinstance(content, bytes):
                return content
            logger.warning("Fetched document was not bytes for URL: %s", document_url)
            return None
        except Exception as e:
            logger.error("Failed to fetch state bill document from %s: %s", document_url, e)
            return None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} state={self.source.state!r} source={self.source.source_name!r}>"
