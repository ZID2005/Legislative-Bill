"""
storage/event_study_repository.py
=================================
Repository for storing and retrieving Event Study calculation records.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.event_study import EventStudyRecord
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


def sanitize_window(window: str) -> str:
    """Sanitize the window label to make it safe for OS filesystems (e.g. [-5,+5] -> m5_p5)."""
    return window.replace("[", "").replace("]", "").replace("+", "p").replace("-", "m")


class EventStudyRepository:
    """
    Repository for persisting and querying EventStudyRecord objects.
    """

    def __init__(self, study_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._study_dir = study_dir or settings.DATA_DIR / "event_studies"
        ensure_dir(self._study_dir)
        logger.debug("EventStudyRepository initialised | study_dir=%s", self._study_dir)

    def _get_path(self, bill_id: str, company_isin: str, event_window: str) -> Path:
        # Sanitize to prevent directory traversal
        sanitized_bill = bill_id.replace("/", "_").replace("\\", "_")
        sanitized_win = sanitize_window(event_window)
        return self._study_dir / f"{sanitized_bill}_{company_isin}_{sanitized_win}.json"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, record: EventStudyRecord) -> None:
        """
        Persist an event study record as a JSON file.
        """
        dest_path = self._get_path(record.bill_id, record.company_isin, record.event_window)
        save_json(record.to_dict(), dest_path)
        logger.info(
            "Saved event study record for bill %s, company %s, window %s",
            record.bill_id,
            record.company_symbol,
            record.event_window,
        )

    def save_many(self, records: list[EventStudyRecord]) -> None:
        """
        Persist multiple event study records.
        """
        for record in records:
            self.save(record)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, bill_id: str, company_isin: str, event_window: str) -> Optional[EventStudyRecord]:
        """
        Retrieve an event study record.
        """
        src_path = self._get_path(bill_id, company_isin, event_window)
        if not file_exists(src_path):
            return None
        try:
            data = load_json(src_path)
            return EventStudyRecord.from_dict(data)
        except Exception as e:
            logger.error(
                "Failed to load event study record for bill %s, company %s, window %s: %s",
                bill_id,
                company_isin,
                event_window,
                e,
            )
            return None

    def get_all(self) -> list[EventStudyRecord]:
        """
        Return all stored event study records.
        """
        records = []
        try:
            files = list_files(self._study_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    records.append(EventStudyRecord.from_dict(data))
                except Exception as e:
                    logger.error("Failed to load event study file %s: %s", f.name, e)
        except Exception as e:
            logger.error("Failed to list event study records: %s", e)
        return records

    def exists(self, bill_id: str, company_isin: str, event_window: str) -> bool:
        """
        Check if an event study record exists.
        """
        src_path = self._get_path(bill_id, company_isin, event_window)
        return file_exists(src_path)

    # ------------------------------------------------------------------
    # Query Filters
    # ------------------------------------------------------------------

    def get_by_bill(self, bill_id: str) -> list[EventStudyRecord]:
        """
        Get all event study records for a specific bill.
        """
        records = []
        try:
            # Match files starting with bill_id
            sanitized_bill = bill_id.replace("/", "_").replace("\\", "_")
            files = list_files(self._study_dir, f"{sanitized_bill}_*.json")
            for f in files:
                try:
                    data = load_json(f)
                    records.append(EventStudyRecord.from_dict(data))
                except Exception as e:
                    logger.error("Failed to load event study file %s: %s", f.name, e)
        except Exception as e:
            logger.error("Failed to filter event study records by bill %s: %s", bill_id, e)
        return records

    def get_by_company(self, company_isin: str) -> list[EventStudyRecord]:
        """
        Get all event study records for a specific company.
        """
        # Since files are named {bill_id}_{company_isin}_{window}.json, we can filter them by name pattern
        records = []
        try:
            files = list_files(self._study_dir, "*.json")
            for f in files:
                if company_isin in f.name:
                    try:
                        data = load_json(f)
                        records.append(EventStudyRecord.from_dict(data))
                    except Exception as e:
                        logger.error("Failed to load event study file %s: %s", f.name, e)
        except Exception as e:
            logger.error("Failed to filter event study records by company %s: %s", company_isin, e)
        return records
