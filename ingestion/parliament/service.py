"""
ingestion/parliament/service.py
===============================
Orchestration service for Parliament legislative data ingestion.

Runs the pipeline: Discovery → Fetch details → Download PDF → Normalize →
Validate → Duplicate Detection → Persistence → Catalog registry.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from ingestion.parliament.connector import ParliamentConnector
from ingestion.parliament.discovery import ParliamentDiscovery
from ingestion.parliament.downloader import ParliamentDownloader
from ingestion.parliament.normalizer import ParliamentNormalizer
from storage.bill_repository import BillRepository
from storage import catalog
from validation.validator import Validator

logger = get_logger(__name__)


class ParliamentIngestionService:
    """
    Main ingestion service coordinating all subcomponents.
    """

    def __init__(
        self,
        bill_repository: Optional[BillRepository] = None,
        validator: Optional[Validator] = None,
        connector: Optional[ParliamentConnector] = None,
        discovery: Optional[ParliamentDiscovery] = None,
        downloader: Optional[ParliamentDownloader] = None,
        normalizer: Optional[ParliamentNormalizer] = None,
    ) -> None:
        """
        Initialize the service. Uses Dependency Injection.
        """
        self.bill_repo = bill_repository or BillRepository()
        self.validator = validator or Validator()

        # Instantiate defaults if not injected
        if connector is None:
            self.connector = ParliamentConnector(
                user_agent=settings.LOG_FORMAT,  # fallback if setting absent, but let's be descriptive
                timeout_seconds=settings.REQUEST_TIMEOUT_SECONDS,
                delay_seconds=settings.REQUEST_DELAY_SECONDS,
            )
            # Custom descriptive agent if possible
            self.connector.user_agent = "LegislativeIntelligenceBot/0.1 (+https://github.com/your-org/legislative-bill)"
        else:
            self.connector = connector

        self.discovery = discovery or ParliamentDiscovery(prs_base_url=settings.PRS_BASE_URL)
        self.downloader = downloader or ParliamentDownloader()
        self.normalizer = normalizer or ParliamentNormalizer()

    async def ingest_bills(
        self,
        source: str = "prs",
        year: Optional[int] = None,
        latest_only: bool = False,
        dry_run: bool = False,
        bill_id_filter: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run the ingestion pipeline.

        Parameters
        ----------
        source : str
            Ingestion source ("prs", "lok_sabha", "rajya_sabha").
        year : int | None
            Filter to discover bills only for this year.
        latest_only : bool
            True to only ingest recently updated bills.
        dry_run : bool
            True to parse and validate without persisting.
        bill_id_filter : str | None
            If provided, only ingest the bill matching this ID.

        Returns
        -------
        dict
            Ingestion summary statistics.
        """
        logger.info("Starting legislative ingestion run | source=%s | year=%s | dry_run=%s", source, year, dry_run)

        # 1. Discover bills
        raw_list = await self.discovery.discover_bills(
            connector=self.connector,
            source=source,
            year=year,
            latest_only=latest_only,
        )

        stats = {
            "discovered": len(raw_list),
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
        }

        # 2. Process each discovered bill
        for idx, raw_bill in enumerate(raw_list):
            title = raw_bill.get("title", "Unknown Title")
            logger.info("Processing discovered bill %d/%d: %s", idx + 1, len(raw_list), title)

            try:
                # Resolve details page URL
                url = raw_bill.get("url")
                enriched_meta = raw_bill.copy()

                # Enrich metadata if details URL is present
                if url:
                    try:
                        logger.info("Fetching details for bill: %s", url)
                        detail_html = await self.connector.fetch(url)
                        enriched_meta = self.discovery.parser.parse_html_details(detail_html, raw_bill)
                    except Exception as e:
                        logger.warning("Failed to fetch detail page for %s: %s. Using list metadata.", title, e)

                # Normalize to Bill schema object
                bill = self.normalizer.normalize(enriched_meta)

                # If bill_id_filter is specified, match against normalized bill_id
                if bill_id_filter and bill.bill_id != bill_id_filter:
                    stats["skipped"] += 1
                    continue

                # 3. Retrieve document text (PDF download) if PDF link is found
                doc_url = enriched_meta.get("document_url")
                if doc_url:
                    try:
                        pdf_path = await self.downloader.download_pdf(doc_url, bill.bill_id, self.connector)
                        bill.pdf_path = pdf_path

                        # Extract text content from PDF
                        bill.full_text = self.downloader.extract_text_from_pdf(pdf_path)
                    except Exception as e:
                        logger.warning("Failed to retrieve or parse PDF from %s: %s", doc_url, e)

                # 4. Validate Normalized Bill
                report = self.validator.validate_bill(bill)
                if not report.is_valid:
                    logger.error("Validation failed for bill %s. Errors: %s", bill.bill_id, report.errors)
                    stats["failed"] += 1
                    continue

                # 5. Duplicate Detection
                if self.bill_repo.exists(bill.bill_id):
                    existing_bill = self.bill_repo.get(bill.bill_id)
                    if existing_bill and self._has_changed(existing_bill, bill):
                        # UPDATE: Preserve original ingested_at timestamp if present
                        bill.ingested_at = existing_bill.ingested_at or date.today()
                        if not dry_run:
                            self.bill_repo.save(bill)
                        logger.info("UPDATED existing bill record: %s", bill.bill_id)
                        stats["updated"] += 1
                    else:
                        logger.info("SKIPPED duplicate bill (no changes detected): %s", bill.bill_id)
                        stats["skipped"] += 1
                else:
                    # INSERT
                    if not dry_run:
                        self.bill_repo.save(bill)
                    logger.info("INSERTED new bill record: %s", bill.bill_id)
                    stats["inserted"] += 1

            except Exception as e:
                logger.error("Error processing bill '%s': %s", title, e, exc_info=True)
                stats["failed"] += 1
                # Continue processing other bills in the list to make the service resilient

        logger.info("Ingestion completed. Stats: %s", stats)

        # 6. Update Catalog
        if not dry_run and not bill_id_filter:
            # Map source to catalog dataset ID
            dataset_id = f"bills_{source}"
            try:
                catalog.bills.update(
                    dataset_id=dataset_id,
                    record_count=self.bill_repo.count(),
                    is_complete=True,
                    notes=(
                        f"Ingestion run completed. Added: {stats['inserted']}, "
                        f"Updated: {stats['updated']}, Failed: {stats['failed']}"
                    ),
                )
            except KeyError:
                # If dataset_id is not in catalog schema (e.g. if custom source), ignore
                pass

        return stats

    def _has_changed(self, existing: Any, current: Any) -> bool:
        """
        Compare fields to detect updates.
        """
        # Compare key metadata fields: status, ministry, pdf_path, full_text length
        if existing.status != current.status:
            return True
        if existing.ministry != current.ministry:
            return True
        if existing.pdf_path != current.pdf_path:
            return True
        if len(existing.full_text or "") != len(current.full_text or ""):
            return True
        return False
