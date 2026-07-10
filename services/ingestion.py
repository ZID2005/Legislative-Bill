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
        logger.info(
            "IngestionService: starting bill ingestion | source=%s | dry_run=%s", source, dry_run
        )
        return await self.parliament_service.ingest_bills(
            source=source,
            year=year,
            latest_only=latest_only,
            dry_run=dry_run,
            bill_id_filter=bill_id_filter,
        )

    async def ingest_companies(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Orchestrate company master ingestion.
        """
        logger.info("IngestionService: starting company master ingestion | dry_run=%s", dry_run)
        from ingestion.companies.company_loader import CompanyLoader

        loader = CompanyLoader()
        try:
            companies = loader.load_company_master(dry_run=dry_run)
            report = self.validator.validate_companies_list(companies)

            return {
                "processed": len(companies),
                "validation_passed": len(companies) if report.is_valid else 0,
                "errors": len(report.errors),
                "warnings": len(report.warnings),
            }
        except Exception as e:
            logger.error("Company master ingestion failed: %s", e, exc_info=True)
            return {"processed": 0, "validation_passed": 0, "errors": 1, "warnings": 0}

    async def ingest_market_prices(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Orchestrate market price ingestion. (Stub for Task 2).
        """
        logger.info("IngestionService: starting market price ingestion | dry_run=%s", dry_run)
        # To be implemented in Task 2.
        return {"inserted": 0, "updated": 0, "skipped": 0, "failed": 0}

    async def download_bill_documents(
        self,
        year: Optional[int] = None,
        dry_run: bool = False,
        bill_id_filter: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Orchestrate document collection for legislative bills.
        """
        logger.info(
            "IngestionService: starting bill document download | year=%s | dry_run=%s",
            year,
            dry_run,
        )
        return await self.parliament_service.download_bill_documents(
            year=year, dry_run=dry_run, bill_id_filter=bill_id_filter
        )

    async def extract_bill_text(
        self,
        year: Optional[int] = None,
        dry_run: bool = False,
        bill_id_filter: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Orchestrate text extraction and corpus generation for legislative bills.
        Delegates to ParliamentIngestionService.extract_bill_text().
        """
        logger.info(
            "IngestionService: starting bill text extraction | year=%s | dry_run=%s", year, dry_run
        )
        return await self.parliament_service.extract_bill_text(
            year=year,
            dry_run=dry_run,
            bill_id_filter=bill_id_filter,
        )
