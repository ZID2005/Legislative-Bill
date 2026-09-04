"""
storage/decision_repository.py
==============================
DecisionRepository — persistence layer for decision-support records (Task 7.2).

Manages storage, retrieval, and querying of strongly-typed DecisionSupportRecord
and DecisionValidationReport artifacts within ``data/decision_support/``.

Storage Structure
-----------------
::

    data/decision_support/
        dec_<bill_id>_<company_isin>_<event_window>.json
        ...
        reports/
            val_dec_<bill_id>_<company_isin>_<event_window>.json
            ...

Deterministic Filenames & IDs
-----------------------------
Decision IDs and filenames are generated deterministically from
(bill_id, company_isin, event_window) using `make_decision_id()`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.decision import (
    DecisionSupportRecord,
    DecisionValidationReport,
    make_decision_id,
    sanitize_id,
)
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


class DecisionRepository:
    """
    Persistence layer for DecisionSupportRecord and DecisionValidationReport records.

    Parameters
    ----------
    decision_dir : Path, optional
        Root directory for decision records.
        Defaults to ``settings.DECISION_SUPPORT_DIR`` (``data/decision_support/``).
    """

    def __init__(self, decision_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._root: Path = decision_dir or settings.DECISION_SUPPORT_DIR
        self._reports_dir: Path = self._root / "reports"

        ensure_dir(self._root)
        ensure_dir(self._reports_dir)

        logger.debug("DecisionRepository initialised | root=%s", self._root)

    # ------------------------------------------------------------------
    # Path resolution
    # ------------------------------------------------------------------

    def _decision_path(self, decision_id: str) -> Path:
        """Return the JSON filepath for a given decision ID."""
        sanitized = sanitize_id(decision_id)
        if not sanitized.startswith("dec_"):
            sanitized = f"dec_{sanitized}"
        return self._root / f"{sanitized}.json"

    def _report_path(self, report_id: str) -> Path:
        """Return the JSON filepath for a given validation report ID."""
        sanitized = sanitize_id(report_id)
        if not sanitized.startswith("val_dec_"):
            sanitized = f"val_dec_{sanitized}"
        return self._reports_dir / f"{sanitized}.json"

    # ------------------------------------------------------------------
    # CRUD: DecisionSupportRecord
    # ------------------------------------------------------------------

    def save(self, record: DecisionSupportRecord) -> Path:
        """
        Persist a single DecisionSupportRecord to disk.

        Parameters
        ----------
        record : DecisionSupportRecord
            The decision support record to save.

        Returns
        -------
        Path
            Absolute path to the saved JSON file.
        """
        if not record.decision_id:
            record.decision_id = make_decision_id(
                record.bill_id, record.company_isin, record.event_window
            )

        path = self._decision_path(record.decision_id)
        try:
            save_json(record.to_dict(), path)
            logger.debug("Saved decision record: %s", path)
            return path
        except Exception as exc:
            logger.error("Failed to save decision record %s to %s: %s", record.decision_id, path, exc)
            raise

    def save_many(self, records: list[DecisionSupportRecord]) -> list[Path]:
        """
        Persist a list of DecisionSupportRecord objects.

        Parameters
        ----------
        records : list[DecisionSupportRecord]

        Returns
        -------
        list[Path]
        """
        saved_paths: list[Path] = []
        for record in records:
            path = self.save(record)
            saved_paths.append(path)
        logger.info("Saved %d decision support records to %s", len(saved_paths), self._root)
        return saved_paths

    def get(self, decision_id: str) -> Optional[DecisionSupportRecord]:
        """
        Retrieve a DecisionSupportRecord by its decision_id.

        Returns None if the record does not exist.
        """
        path = self._decision_path(decision_id)
        if not file_exists(path):
            return None
        try:
            data = load_json(path)
            return DecisionSupportRecord.from_dict(data)
        except Exception as exc:
            logger.warning("Error loading decision support record %s: %s", path, exc)
            return None

    def get_by_key(
        self, bill_id: str, company_isin: str, event_window: str
    ) -> Optional[DecisionSupportRecord]:
        """
        Retrieve a DecisionSupportRecord by its composite key.
        """
        dec_id = make_decision_id(bill_id, company_isin, event_window)
        return self.get(dec_id)

    def exists(self, bill_id: str, company_isin: str, event_window: str) -> bool:
        """
        Check whether a decision record exists for the given composite key.
        """
        dec_id = make_decision_id(bill_id, company_isin, event_window)
        return file_exists(self._decision_path(dec_id))

    def get_by_bill(self, bill_id: str) -> list[DecisionSupportRecord]:
        """
        Retrieve all DecisionSupportRecord objects associated with a specific bill_id.
        """
        all_records = self.load_all()
        return [rec for rec in all_records if rec.bill_id == bill_id]

    def get_by_company(self, company_isin: str) -> list[DecisionSupportRecord]:
        """
        Retrieve all DecisionSupportRecord objects associated with a specific company ISIN.
        """
        all_records = self.load_all()
        return [rec for rec in all_records if rec.company_isin == company_isin]

    def load_all(self) -> list[DecisionSupportRecord]:
        """
        Load all stored DecisionSupportRecord objects from the decision support directory.
        """
        records: list[DecisionSupportRecord] = []
        if not self._root.is_dir():
            return records

        json_files = list_files(self._root, pattern="*.json")
        for filepath in json_files:
            # Skip reports or subdirectories
            if filepath.parent != self._root or not filepath.name.startswith("dec_"):
                continue
            try:
                data = load_json(filepath)
                records.append(DecisionSupportRecord.from_dict(data))
            except Exception as exc:
                logger.warning("Failed to deserialize decision record %s: %s", filepath, exc)
        return records

    # ------------------------------------------------------------------
    # CRUD: DecisionValidationReport
    # ------------------------------------------------------------------

    def save_validation_report(self, report: DecisionValidationReport) -> Path:
        """
        Persist a DecisionValidationReport.
        """
        path = self._report_path(report.report_id)
        try:
            save_json(report.to_dict(), path)
            logger.debug("Saved decision validation report: %s", path)
            return path
        except Exception as exc:
            logger.error("Failed to save decision validation report %s: %s", report.report_id, exc)
            raise

    def load_validation_reports(self) -> list[DecisionValidationReport]:
        """
        Load all stored decision validation reports.
        """
        reports: list[DecisionValidationReport] = []
        if not self._reports_dir.is_dir():
            return reports

        for filepath in list_files(self._reports_dir, pattern="*.json"):
            try:
                data = load_json(filepath)
                reports.append(DecisionValidationReport.from_dict(data))
            except Exception as exc:
                logger.warning("Failed to load decision validation report %s: %s", filepath, exc)
        return reports

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Delete all decision records and validation reports from disk."""
        if self._root.is_dir():
            for f in list_files(self._root, pattern="*.json"):
                try:
                    f.unlink()
                except Exception as exc:
                    logger.warning("Could not delete %s: %s", f, exc)
        if self._reports_dir.is_dir():
            for f in list_files(self._reports_dir, pattern="*.json"):
                try:
                    f.unlink()
                except Exception as exc:
                    logger.warning("Could not delete %s: %s", f, exc)
        logger.info("DecisionRepository cleared: %s", self._root)
