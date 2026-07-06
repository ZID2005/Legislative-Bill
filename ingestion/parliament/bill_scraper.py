"""
ingestion/parliament/bill_scraper.py
===================================
Delegation wrapper for backward compatibility with Scraper placeholder.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from ingestion.parliament.service import ParliamentIngestionService


class BillScraper:
    """
    Wrapper for ParliamentIngestionService.
    """

    def __init__(self) -> None:
        self.service = ParliamentIngestionService()

    def scrape_bills(
        self,
        source: str = "prs",
        start_year: int = 2000,
        end_year: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Synchronous wrapper to scrape bills.
        """
        stats = asyncio.run(
            self.service.ingest_bills(
                source=source,
                year=start_year,
            )
        )
        return [stats]
