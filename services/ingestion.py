"""
services/ingestion.py
=====================
Orchestration service for data ingestion workflows.

Unified entry point for ingesting parliament bills, company masters, and market prices.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from ingestion.parliament.service import ParliamentIngestionService
from storage.bill_repository import BillRepository
from validation.validator import Validator

logger = get_logger(__name__)


class IngestionService:
    """
    Coordinates and runs all data ingestion flows across different data sources.
    """

    def __init__(
        self,
        bill_repository: Optional[BillRepository] = None,
        validator: Optional[Validator] = None,
        parliament_service: Optional[ParliamentIngestionService] = None,
    ) -> None:
        """
        Initialize the ingestion service. Uses dependency injection.
        """
        self.bill_repo = bill_repository or BillRepository()
        self.validator = validator or Validator()
        self.parliament_service = parliament_service or ParliamentIngestionService(
            bill_repository=self.bill_repo,
            validator=self.validator,
        )

    async def ingest_bills(
        self,
        source: str = "prs",
        year: Optional[int] = None,
        latest_only: bool = False,
        dry_run: bool = False,
        bill_id_filter: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Orchestrate bill ingestion. Delegates to ParliamentIngestionService.
        """
        logger.info("IngestionService: starting bill ingestion | source=%s | dry_run=%s", source, dry_run)
        return await self.parliament_service.ingest_bills(
            source=source,
            year=year,
            latest_only=latest_only,
            dry_run=dry_run,
            bill_id_filter=bill_id_filter,
        )

    async def ingest_companies(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Orchestrate company master ingestion. (Stub for Task 2).
        """
        logger.info("IngestionService: starting company master ingestion | dry_run=%s", dry_run)
        # To be implemented in Task 2.
        return {"inserted": 0, "updated": 0, "skipped": 0, "failed": 0}

    async def ingest_market_prices(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Orchestrate market price ingestion. (Stub for Task 2).
        """
        logger.info("IngestionService: starting market price ingestion | dry_run=%s", dry_run)
        # To be implemented in Task 2.
        return {"inserted": 0, "updated": 0, "skipped": 0, "failed": 0}
