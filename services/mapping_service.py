"""
services/mapping_service.py
===========================
Orchestration service for Bill-to-Company mapping workflows.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from mapping.sector_mapper import SectorMapper
from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.knowledge_repository import KnowledgeRepository
from storage.mapping_repository import MappingRepository
from validation.validator import Validator

logger = get_logger(__name__)


class MappingService:
    """
    Coordinates and runs the legislative bill to listed company mapping pipeline.
    """

    def __init__(
        self,
        bill_repository: Optional[BillRepository] = None,
        knowledge_repository: Optional[KnowledgeRepository] = None,
        company_repository: Optional[CompanyRepository] = None,
        mapping_repository: Optional[MappingRepository] = None,
        validator: Optional[Validator] = None,
        sector_mapper: Optional[SectorMapper] = None,
    ) -> None:
        self.bill_repo = bill_repository or BillRepository()
        self.knowledge_repo = knowledge_repository or KnowledgeRepository()
        self.company_repo = company_repository or CompanyRepository()
        self.mapping_repo = mapping_repository or MappingRepository()
        self.validator = validator or Validator()
        self.sector_mapper = sector_mapper or SectorMapper(company_repository=self.company_repo)

    def generate_mappings(
        self,
        year: Optional[int] = None,
        bill_id_filter: Optional[str] = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Run bill-company mapping for bills matching the filters.

        Parameters
        ----------
        year : int | None
            Filter bills by year.
        bill_id_filter : str | None
            Process a single bill by ID.
        dry_run : bool
            If True, generate mappings and run validation without saving.

        Returns
        -------
        dict[str, Any]
            Execution stats (processed, saved, validation_passed, validation_failed, warnings_raised).
        """
        logger.info(
            "Starting bill-company mapping generation | year=%s | bill_id_filter=%s | dry_run=%s",
            year,
            bill_id_filter,
            dry_run,
        )

        stats = {
            "processed": 0,
            "saved": 0,
            "validation_passed": 0,
            "validation_failed": 0,
            "warnings_raised": 0,
        }

        # 1. Fetch bills matching filters
        if bill_id_filter:
            bill = self.bill_repo.get(bill_id_filter)
            bills = [bill] if bill else []
        elif year is not None:
            bills = self.bill_repo.get_by_year(year)
        else:
            bills = self.bill_repo.get_all()

        if not bills:
            logger.info("No bills found matching the specified filters.")
            return stats

        # 2. Process mappings for each bill
        for bill in bills:
            try:
                # Fetch knowledge record
                knowledge_record = self.knowledge_repo.get(bill.bill_id)
                if not knowledge_record:
                    logger.warning(
                        "Skipping mapping for bill '%s': No KnowledgeRecord found in repository.",
                        bill.bill_id,
                    )
                    continue

                stats["processed"] += 1

                # Generate mapping record
                mapping = self.sector_mapper.map_bill_to_companies(bill, knowledge_record)

                # Validate mapping
                report = self.validator.validate_mapping_record(mapping, self.company_repo)
                if not report.is_valid:
                    stats["validation_failed"] += 1
                    logger.warning(
                        "Mapping record validation failed for bill '%s': %s",
                        bill.bill_id,
                        report.errors,
                    )
                else:
                    stats["validation_passed"] += 1

                if report.warnings:
                    stats["warnings_raised"] += len(report.warnings)

                # Save if not dry-run
                if not dry_run:
                    self.mapping_repo.save(mapping)
                    stats["saved"] += 1

            except Exception as e:
                logger.error(
                    "Error generating mapping for bill '%s': %s",
                    bill.bill_id,
                    e,
                    exc_info=True,
                )

        logger.info("Mapping generation complete | stats=%s", stats)
        return stats
