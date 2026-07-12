"""
storage/label_repository.py
============================
Repository for storing and retrieving ground-truth ``LabelRecord``
objects produced by the Label Generation Engine (Task 4.4).

Design
------
*  Follows the exact Repository Pattern established by
   ``StatisticalRepository`` and ``EventStudyRepository``.
*  File-based JSON persistence under ``data/labels/`` (configurable
   via ``settings.LABELS_DIR``).
*  Naming convention: ``{bill_id}_{company_isin}_{sanitized_window}.json``
*  Supports full CRUD plus filtered queries by bill or company.
*  Duplicate-safe: ``save`` overwrites an existing file; ``exists``
   allows the caller to implement idempotent / incremental workflows.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.label_record import LabelRecord
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


def _sanitize_window(window: str) -> str:
    """
    Make an event-window label safe for OS file systems.

    Examples
    --------
    >>> _sanitize_window("[-5,+5]")
    'm5,p5'
    >>> _sanitize_window("[0,+20]")
    '0,p20'
    """
    return (
        window.replace("[", "")
        .replace("]", "")
        .replace("+", "p")
        .replace("-", "m")
    )


class LabelRepository:
    """
    Repository for persisting and querying ``LabelRecord`` objects.

    Each label is stored as a single JSON file named::

        {bill_id}_{company_isin}_{sanitized_window}.json

    Parameters
    ----------
    label_dir : Path, optional
        Root directory for label JSON files.  Defaults to
        ``settings.LABELS_DIR`` (``data/labels/``).
    """

    def __init__(self, label_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._label_dir: Path = label_dir or settings.LABELS_DIR
        ensure_dir(self._label_dir)
        logger.debug("LabelRepository initialised | label_dir=%s", self._label_dir)

    # ------------------------------------------------------------------
    # Internal path helpers
    # ------------------------------------------------------------------

    def _get_path(self, bill_id: str, company_isin: str, event_window: str) -> Path:
        """Construct the deterministic file path for a label record."""
        sanitized_bill = bill_id.replace("/", "_").replace("\\", "_")
        sanitized_win = _sanitize_window(event_window)
        return self._label_dir / f"{sanitized_bill}_{company_isin}_{sanitized_win}.json"

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, record: LabelRecord) -> None:
        """
        Persist a label record as a JSON file.

        If a file already exists for the same (bill, company, window)
        triple it is overwritten atomically.
        """
        dest = self._get_path(record.bill_id, record.company, record.event_window)
        save_json(record.to_dict(), dest)
        logger.info(
            "Saved label: bill=%s company=%s window=%s direction=%s",
            record.bill_id,
            record.company,
            record.event_window,
            record.direction.value,
        )

    def save_many(self, records: list[LabelRecord]) -> None:
        """Persist multiple label records, saving each atomically."""
        for record in records:
            self.save(record)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(
        self,
        bill_id: str,
        company_isin: str,
        event_window: str,
    ) -> Optional[LabelRecord]:
        """
        Retrieve a single label record.

        Returns ``None`` if the record does not exist or cannot be
        deserialised.
        """
        src = self._get_path(bill_id, company_isin, event_window)
        if not file_exists(src):
            return None
        try:
            data = load_json(src)
            return LabelRecord.from_dict(data)
        except Exception as exc:
            logger.error(
                "Failed to load label record bill=%s company=%s window=%s: %s",
                bill_id,
                company_isin,
                event_window,
                exc,
            )
            return None

    def get_all(self) -> list[LabelRecord]:
        """Return all stored label records, skipping any that fail to load."""
        records: list[LabelRecord] = []
        try:
            for f in list_files(self._label_dir, "*.json"):
                try:
                    records.append(LabelRecord.from_dict(load_json(f)))
                except Exception as exc:
                    logger.error("Failed to load label file %s: %s", f.name, exc)
        except Exception as exc:
            logger.error("Failed to list label records: %s", exc)
        return records

    # ------------------------------------------------------------------
    # Existence check
    # ------------------------------------------------------------------

    def exists(self, bill_id: str, company_isin: str, event_window: str) -> bool:
        """Return ``True`` if a label record already exists on disk."""
        return file_exists(self._get_path(bill_id, company_isin, event_window))

    # ------------------------------------------------------------------
    # Filtered queries
    # ------------------------------------------------------------------

    def get_by_bill(self, bill_id: str) -> list[LabelRecord]:
        """Return all label records for a specific bill."""
        records: list[LabelRecord] = []
        try:
            sanitized = bill_id.replace("/", "_").replace("\\", "_")
            for f in list_files(self._label_dir, f"{sanitized}_*.json"):
                try:
                    records.append(LabelRecord.from_dict(load_json(f)))
                except Exception as exc:
                    logger.error("Failed to load label file %s: %s", f.name, exc)
        except Exception as exc:
            logger.error(
                "Failed to filter label records by bill %s: %s", bill_id, exc
            )
        return records

    def get_by_company(self, company_isin: str) -> list[LabelRecord]:
        """Return all label records for a specific company ISIN."""
        records: list[LabelRecord] = []
        try:
            for f in list_files(self._label_dir, "*.json"):
                if company_isin in f.name:
                    try:
                        records.append(LabelRecord.from_dict(load_json(f)))
                    except Exception as exc:
                        logger.error("Failed to load label file %s: %s", f.name, exc)
        except Exception as exc:
            logger.error(
                "Failed to filter label records by company %s: %s",
                company_isin,
                exc,
            )
        return records

    # ------------------------------------------------------------------
    # Delete / utility
    # ------------------------------------------------------------------

    def delete(self, bill_id: str, company_isin: str, event_window: str) -> None:
        """Remove a label record from disk, if it exists."""
        path = self._get_path(bill_id, company_isin, event_window)
        if file_exists(path):
            os.remove(path)
            logger.info(
                "Deleted label: bill=%s company=%s window=%s",
                bill_id,
                company_isin,
                event_window,
            )

    def count(self) -> int:
        """Return the total number of stored label records."""
        try:
            return len(list_files(self._label_dir, "*.json"))
        except Exception as exc:
            logger.error("Failed to count label records: %s", exc)
            return 0
