"""
services/knowledge_service.py
=============================
Orchestration service for Legislative Knowledge Layer workflows.
"""

from __future__ import annotations

from typing import Any, Optional

from config.logging_config import get_logger
from knowledge.engine import RuleEngine
from storage.bill_repository import BillRepository
from storage.knowledge_repository import KnowledgeRepository
from validation.validator import Validator

logger = get_logger(__name__)


class KnowledgeService:
    """
    Coordinates and runs the legislative knowledge generation and validation pipeline.
    """

    def __init__(
        self,
        bill_repository: Optional[BillRepository] = None,
        knowledge_repository: Optional[KnowledgeRepository] = None,
        validator: Optional[Validator] = None,
        rule_engine: Optional[RuleEngine] = None,
    ) -> None:
        self.bill_repo = bill_repository or BillRepository()
        self.knowledge_repo = knowledge_repository or KnowledgeRepository()
        self.validator = validator or Validator()
        self.rule_engine = rule_engine or RuleEngine()

    def generate_knowledge(
        self,
        year: Optional[int] = None,
        bill_id_filter: Optional[str] = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Run knowledge generation for bills matching the filters.

        Parameters
        ----------
        year : int | None
            Filter bills by year.
        bill_id_filter : str | None
            Process a single bill by ID.
        dry_run : bool
            If True, generate records and run validation without saving.

        Returns
        -------
        dict[str, Any]
            Execution stats (processed, saved, validation_passed, validation_failed, warnings_raised).
        """
        logger.info(
            "Starting knowledge generation | year=%s | bill_id_filter=%s | dry_run=%s",
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

        # 2. Process each bill
        for bill in bills:
            try:
                stats["processed"] += 1
                # Generate record
                record = self.rule_engine.generate_record(bill)

                # Validate record
                report = self.validator.validate_knowledge_record(record)
                if not report.is_valid:
                    stats["validation_failed"] += 1
                    logger.warning(
                        "Knowledge record validation failed for %s: %s",
                        bill.bill_id,
                        report.errors,
                    )
                else:
                    stats["validation_passed"] += 1

                if report.warnings:
                    stats["warnings_raised"] += len(report.warnings)

                # Persist if not dry-run
                if not dry_run:
                    self.knowledge_repo.save(record)
                    stats["saved"] += 1

            except Exception as e:
                logger.error(
                    "Error generating knowledge record for bill '%s': %s",
                    bill.bill_id,
                    e,
                    exc_info=True,
                )

        logger.info("Knowledge generation complete | stats=%s", stats)
        return stats
