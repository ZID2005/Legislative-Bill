"""
ingestion/parliament/service.py
===============================
Orchestration service for Parliament legislative data ingestion.

Runs the pipeline: Discovery → Fetch details → Download PDF → Normalize →
Validate → Duplicate Detection → Persistence → Catalog registry.
Task 1A.4 adds: Text Extraction → Corpus Generation.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from ingestion.parliament.connector import ParliamentConnector
from ingestion.parliament.discovery import ParliamentDiscovery
from ingestion.parliament.downloader import ParliamentDownloader
from ingestion.parliament.extractor import LegislativeTextExtractor
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
            self.connector.user_agent = (
                "LegislativeIntelligenceBot/0.1 (+https://github.com/your-org/legislative-bill)"
            )
        else:
            self.connector = connector

        self.discovery = discovery or ParliamentDiscovery(prs_base_url=settings.PRS_BASE_URL)
        self.downloader = downloader or ParliamentDownloader()
        self.normalizer = normalizer or ParliamentNormalizer()
        self.extractor = LegislativeTextExtractor()

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
        logger.info(
            "Starting legislative ingestion run | source=%s | year=%s | dry_run=%s",
            source,
            year,
            dry_run,
        )

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
                        enriched_meta = self.discovery.parser.parse_html_details(
                            detail_html, raw_bill
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to fetch detail page for %s: %s. Using list metadata.", title, e
                        )

                # Normalize to Bill schema object
                bill = self.normalizer.normalize(enriched_meta)

                # If bill_id_filter is specified, match against normalized bill_id
                if bill_id_filter and bill.bill_id != bill_id_filter:
                    stats["skipped"] += 1
                    continue

                # NOTE: PDF download (Task 1A.3+) is intentionally skipped here.
                # pdf_url is recorded on the Bill object by the normalizer (from
                # enriched_meta["pdf_url"]). Actual PDF bytes are downloaded in a
                # later pipeline stage. Do NOT call downloader here.

                # 3. Validate Normalized Bill
                report = self.validator.validate_bill(bill)
                if not report.is_valid:
                    logger.error(
                        "Validation failed for bill %s. Errors: %s", bill.bill_id, report.errors
                    )
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
                        logger.info(
                            "SKIPPED duplicate bill (no changes detected): %s", bill.bill_id
                        )
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

    # ------------------------------------------------------------------
    # Fields that participate in change detection.
    #
    # Rules for inclusion / exclusion:
    #   INCLUDE  — actual legislative content that can be enriched
    #              on re-runs (comes from the source portal).
    #   EXCLUDE  — volatile runtime / provenance fields that change
    #              independently of the legislative record itself:
    #              ingested_at   (set once on first insert)
    #              pdf_path      (set by a later download task)
    #              source        (static identifier, never changes)
    #              bill_id       (identity key, used for lookup)
    #              sectors       (populated by mapping module, Task 5)
    #              keywords      (populated by NLP module, Task 4)
    #              full_text     (populated by PDF extractor, later task)
    # ------------------------------------------------------------------
    _TRACKED_FIELDS: tuple[str, ...] = (
        # Core identity metadata
        "title",
        "bill_number",
        "year",
        "house",
        "status",
        "ministry",
        # Dates
        "introduction_date",
        "assent_date",
        "gazette_date",
        "last_updated",
        # Task 1A.2 enriched fields
        "pdf_url",
        "session",
        "sponsor",
        "related_bills",
        "related_acts",
        "language",
        "summary",
    )

    def _has_changed(self, existing: Any, current: Any) -> bool:
        """
        Return True if any tracked legislative metadata field differs
        between the stored bill and the newly ingested bill.

        Comparison strategy
        -------------------
        Each field in ``_TRACKED_FIELDS`` is compared with ``==``.
        This correctly handles:
        - Scalar fields (str, int, Enum, date, None)
        - List fields (related_bills, related_acts): Python list equality
          compares element-by-element; order changes are detected.
        - Enum fields (house, status): equality is value-based because
          BillStatus and BillHouse inherit from (str, Enum).
        - Optional fields: ``None == None`` is True, so a missing field
          on both sides does not trigger a spurious update.

        Excluded fields (see ``_TRACKED_FIELDS`` docblock above):
        ingested_at, pdf_path, source, bill_id, sectors, keywords,
        full_text — these are managed by other pipeline stages and must
        not cause re-saves during a metadata-only sync run.
        """
        for field_name in self._TRACKED_FIELDS:
            existing_val = getattr(existing, field_name, None)
            current_val = getattr(current, field_name, None)
            if existing_val != current_val:
                logger.debug(
                    "Change detected on field '%s': %r → %r",
                    field_name,
                    existing_val,
                    current_val,
                )
                return True
        return False

    async def download_bill_documents(
        self,
        year: Optional[int] = None,
        dry_run: bool = False,
        bill_id_filter: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Orchestrates document collection for legislative bills.
        Scans repository, downloads missing/invalid PDFs, validates, and updates audit fields.
        """
        logger.info(
            "Starting bill document download run | year=%s | dry_run=%s | bill_id_filter=%s",
            year,
            dry_run,
            bill_id_filter,
        )

        all_bills = self.bill_repo.get_all()
        stats = {
            "total": 0,
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
        }

        # Filter bills matching criteria and containing official PDF URLs
        target_bills = []
        for bill in all_bills:
            if not bill.pdf_url:
                continue
            if year is not None and bill.year != year:
                continue
            if bill_id_filter is not None and bill.bill_id != bill_id_filter:
                continue
            target_bills.append(bill)

        stats["total"] = len(target_bills)
        logger.info("Found %d bills eligible for document download.", stats["total"])

        for idx, bill in enumerate(target_bills):
            logger.info(
                "Processing document download %d/%d: %s", idx + 1, len(target_bills), bill.title
            )

            # Determine storage paths
            year_folder = str(bill.year) if bill.year else "unknown"
            dest_dir = settings.BILLS_DIR / "documents" / year_folder
            dest_path = dest_dir / f"{bill.bill_id}.pdf"

            # Duplicate Check: If file exists, has correct checksum, and matches repo
            already_exists = False
            if bill.document_checksum and dest_path.is_file():
                try:
                    import hashlib  # noqa: PLC0415

                    sha256 = hashlib.sha256()
                    with dest_path.open("rb") as f:
                        while chunk := f.read(8192):
                            sha256.update(chunk)
                    if sha256.hexdigest() == bill.document_checksum:
                        already_exists = True
                except Exception as e:
                    logger.warning(
                        "Error calculating checksum for duplicate check on %s: %s",
                        dest_path.name,
                        e,
                    )

            if already_exists:
                logger.info("Document already exists and is verified: %s", dest_path.name)
                # Keep fields synchronized
                if not bill.document_path:
                    bill.document_path = str(dest_path.resolve())
                    bill.pdf_path = bill.document_path
                    if not dry_run:
                        self.bill_repo.save(bill)
                stats["skipped"] += 1
                continue

            if dry_run:
                logger.info(
                    "[Dry Run] Would download document for bill %s from %s to %s",
                    bill.bill_id,
                    bill.pdf_url,
                    dest_path,
                )
                stats["downloaded"] += 1
                continue

            # Execute safe download
            try:
                success, msg, size, checksum = await self.downloader.download_document(
                    document_url=bill.pdf_url,
                    dest_path=dest_path,
                    connector=self.connector,
                )

                if success:
                    # Run semantic/corruption validation
                    report = self.validator.validate_document(dest_path)
                    if report.is_valid:
                        # Save successful metadata details
                        bill.document_path = str(dest_path.resolve())
                        bill.document_size = size
                        bill.document_checksum = checksum
                        bill.download_timestamp = datetime.utcnow().isoformat() + "Z"
                        bill.download_status = "success"
                        bill.pdf_path = bill.document_path  # legacy sync

                        self.bill_repo.save(bill)
                        logger.info(
                            "Successfully downloaded and validated document: %s", dest_path.name
                        )
                        stats["downloaded"] += 1
                    else:
                        logger.error(
                            "Downloaded document for bill %s failed validation: %s",
                            bill.bill_id,
                            report.errors,
                        )
                        # Delete corrupted file on semantic validation failure
                        if dest_path.is_file():
                            dest_path.unlink()

                        bill.download_status = "failed"
                        bill.download_timestamp = datetime.utcnow().isoformat() + "Z"
                        self.bill_repo.save(bill)
                        stats["failed"] += 1
                else:
                    logger.error("Download failed for bill %s: %s", bill.bill_id, msg)
                    # Note: We keep partial file on disk for resumable retries later
                    bill.download_status = "failed"
                    bill.download_timestamp = datetime.utcnow().isoformat() + "Z"
                    self.bill_repo.save(bill)
                    stats["failed"] += 1

            except Exception as e:
                logger.error(
                    "Unexpected error collecting document for bill %s: %s",
                    bill.bill_id,
                    e,
                    exc_info=True,
                )
                bill.download_status = "failed"
                bill.download_timestamp = datetime.utcnow().isoformat() + "Z"
                self.bill_repo.save(bill)
                stats["failed"] += 1

        logger.info("Document download run completed. Stats: %s", stats)
        return stats

    async def extract_bill_text(
        self,
        year: Optional[int] = None,
        dry_run: bool = False,
        bill_id_filter: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Extract text from all successfully downloaded bill PDFs.

        For each bill with ``download_status == 'success'``:
        -  Delegates to ``LegislativeTextExtractor.extract()``.
        -  Applies checksum-based skip logic for incremental runs.
        -  Updates the Bill record with text metadata and quality metrics.
        -  Persists the updated record to the bill repository.

        Parameters
        ----------
        year : int | None
            Only process bills from this year. None processes all years.
        dry_run : bool
            Compute metrics and validate without writing corpus files or
            updating the repository.
        bill_id_filter : str | None
            Limit extraction to a single bill ID.

        Returns
        -------
        dict
            ``{total, extracted, skipped, scanned, failed}``
        """
        logger.info(
            "Starting bill text extraction | year=%s | dry_run=%s | bill_id_filter=%s",
            year,
            dry_run,
            bill_id_filter,
        )

        stats: dict[str, Any] = {
            "total": 0,
            "extracted": 0,
            "skipped": 0,
            "scanned": 0,
            "failed": 0,
        }

        # Load candidate bills
        all_bills = self.bill_repo.get_all()
        target_bills = []
        for bill in all_bills:
            if bill_id_filter and bill.bill_id != bill_id_filter:
                continue
            if year is not None and bill.year != year:
                continue
            if bill.download_status != "success":
                logger.debug(
                    "Skipping bill %s — download_status=%s", bill.bill_id, bill.download_status
                )
                continue
            target_bills.append(bill)

        stats["total"] = len(target_bills)
        logger.info("Found %d bills eligible for text extraction.", stats["total"])

        for idx, bill in enumerate(target_bills):
            logger.info("Extracting text %d/%d: %s", idx + 1, len(target_bills), bill.title)
            try:
                result = self.extractor.extract(
                    bill_id=bill.bill_id,
                    pdf_path=bill.document_path or bill.pdf_path,
                    year=bill.year,
                    document_checksum=bill.document_checksum,
                    existing_text_checksum=bill.text_checksum,
                    existing_text_path=bill.text_path,
                    dry_run=dry_run,
                )

                # Map result status to stats counter
                if result.text_status == "success":
                    if "skipped" in result.warnings[0] if result.warnings else False:
                        stats["skipped"] += 1
                    else:
                        stats["extracted"] += 1
                elif result.text_status == "scanned_pdf":
                    stats["scanned"] += 1
                else:
                    stats["failed"] += 1

                # Update Bill fields — never touch metadata or document fields
                bill.text_path = result.text_path
                bill.text_checksum = result.text_checksum
                bill.text_size = result.text_size
                bill.text_status = result.text_status
                bill.extraction_method = result.extraction_method
                bill.extraction_timestamp = result.extraction_timestamp
                bill.page_count = result.page_count if result.page_count else bill.page_count
                bill.quality_metrics = result.quality_metrics

                if not dry_run:
                    self.bill_repo.save(bill)
                    logger.info(
                        "Repository updated for bill %s | status=%s",
                        bill.bill_id,
                        result.text_status,
                    )

            except Exception as exc:
                logger.error(
                    "Unexpected error during text extraction for bill %s: %s",
                    bill.bill_id,
                    exc,
                    exc_info=True,
                )
                stats["failed"] += 1

        logger.info("Text extraction run completed. Stats: %s", stats)
        return stats
