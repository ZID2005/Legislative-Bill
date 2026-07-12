"""
storage/statistical_repository.py
==================================
Repository for storing and retrieving Statistical Significance calculation records.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.statistical_result import StatisticalResult
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


def sanitize_window(window: str) -> str:
    """Sanitize the window label to make it safe for OS filesystems (e.g. [-5,+5] -> m5_p5)."""
    return window.replace("[", "").replace("]", "").replace("+", "p").replace("-", "m")


class StatisticalRepository:
    """
    Repository for persisting and querying StatisticalResult objects.
    """

    def __init__(self, result_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._result_dir = result_dir or settings.STAT_RESULTS_DIR
        ensure_dir(self._result_dir)
        logger.debug("StatisticalRepository initialised | result_dir=%s", self._result_dir)

    def _get_path(self, bill_id: str, company_isin: str, event_window: str) -> Path:
        # Sanitize to prevent directory traversal
        sanitized_bill = bill_id.replace("/", "_").replace("\\", "_")
        sanitized_win = sanitize_window(event_window)
        return self._result_dir / f"{sanitized_bill}_{company_isin}_{sanitized_win}.json"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, record: StatisticalResult) -> None:
        """
        Persist a statistical significance record as a JSON file.
        """
        dest_path = self._get_path(record.bill_id, record.company, record.event_window)
        save_json(record.to_dict(), dest_path)
        logger.info(
            "Saved statistical result for bill %s, company %s, window %s",
            record.bill_id,
            record.company_symbol,
            record.event_window,
        )

    def save_many(self, records: list[StatisticalResult]) -> None:
        """
        Persist multiple statistical significance records.
        """
        for record in records:
            self.save(record)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(
        self, bill_id: str, company_isin: str, event_window: str
    ) -> Optional[StatisticalResult]:
        """
        Retrieve a statistical significance record.
        """
        src_path = self._get_path(bill_id, company_isin, event_window)
        if not file_exists(src_path):
            return None
        try:
            data = load_json(src_path)
            return StatisticalResult.from_dict(data)
        except Exception as e:
            logger.error(
                "Failed to load statistical result for bill %s, company %s, window %s: %s",
                bill_id,
                company_isin,
                event_window,
                e,
            )
            return None

    def get_all(self) -> list[StatisticalResult]:
        """
        Return all stored statistical significance records.
        """
        records = []
        try:
            files = list_files(self._result_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    records.append(StatisticalResult.from_dict(data))
                except Exception as e:
                    logger.error("Failed to load statistical result file %s: %s", f.name, e)
        except Exception as e:
            logger.error("Failed to list statistical result records: %s", e)
        return records

    def exists(self, bill_id: str, company_isin: str, event_window: str) -> bool:
        """
        Check if a statistical significance record exists.
        """
        src_path = self._get_path(bill_id, company_isin, event_window)
        return file_exists(src_path)

    # ------------------------------------------------------------------
    # Query Filters
    # ------------------------------------------------------------------

    def get_by_bill(self, bill_id: str) -> list[StatisticalResult]:
        """
        Get all statistical significance records for a specific bill.
        """
        records = []
        try:
            sanitized_bill = bill_id.replace("/", "_").replace("\\", "_")
            files = list_files(self._result_dir, f"{sanitized_bill}_*.json")
            for f in files:
                try:
                    data = load_json(f)
                    records.append(StatisticalResult.from_dict(data))
                except Exception as e:
                    logger.error("Failed to load statistical result file %s: %s", f.name, e)
        except Exception as e:
            logger.error("Failed to filter statistical result records by bill %s: %s", bill_id, e)
        return records

    def get_by_company(self, company_isin: str) -> list[StatisticalResult]:
        """
        Get all statistical significance records for a specific company.
        """
        records = []
        try:
            files = list_files(self._result_dir, "*.json")
            for f in files:
                if company_isin in f.name:
                    try:
                        data = load_json(f)
                        records.append(StatisticalResult.from_dict(data))
                    except Exception as e:
                        logger.error("Failed to load statistical result file %s: %s", f.name, e)
        except Exception as e:
            logger.error(
                "Failed to filter statistical result records by company %s: %s",
                company_isin,
                e,
            )
        return records

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def delete(self, bill_id: str, company_isin: str, event_window: str) -> None:
        """
        Remove a statistical result record.
        """
        src_path = self._get_path(bill_id, company_isin, event_window)
        if file_exists(src_path):
            os.remove(src_path)
            logger.info(
                "Deleted statistical result: bill=%s, company=%s, window=%s",
                bill_id,
                company_isin,
                event_window,
            )

    def count(self) -> int:
        """
        Return the total number of stored statistical significance records.
        """
        try:
            files = list_files(self._result_dir, "*.json")
            return len(files)
        except Exception as e:
            logger.error("Failed to count statistical result records: %s", e)
            return 0
