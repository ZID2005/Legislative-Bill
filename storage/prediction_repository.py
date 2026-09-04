"""
storage/prediction_repository.py
================================
PredictionRepository — persistence layer for final prediction records (Task 7.1).

Manages storage, retrieval, and indexing of strongly-typed PredictionRecord
and PredictionValidationReport artifacts within ``data/predictions/``.

Storage Structure
-----------------
::

    data/predictions/
        pred_<bill_id>_<company_isin>_<event_window>.json
        ...
        reports/
            val_<bill_id>_<company_isin>_<event_window>.json
            ...

Deterministic Filenames & IDs
-----------------------------
Prediction IDs and filenames are generated deterministically from
(bill_id, company_isin, event_window) using `make_prediction_id()`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.prediction import (
    PredictionRecord,
    PredictionValidationReport,
    make_prediction_id,
    sanitize_id,
)
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


class PredictionRepository:
    """
    Persistence layer for PredictionRecord and PredictionValidationReport records.

    Parameters
    ----------
    predictions_dir : Path, optional
        Root directory for prediction records.
        Defaults to ``settings.PREDICTIONS_DIR`` (``data/predictions/``).
    """

    def __init__(self, predictions_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._root: Path = predictions_dir or settings.PREDICTIONS_DIR
        self._reports_dir: Path = self._root / "reports"

        ensure_dir(self._root)
        ensure_dir(self._reports_dir)

        logger.debug("PredictionRepository initialised | root=%s", self._root)

    # ------------------------------------------------------------------
    # Path resolution
    # ------------------------------------------------------------------

    def _prediction_path(self, prediction_id: str) -> Path:
        """Return the JSON filepath for a given prediction ID."""
        sanitized = sanitize_id(prediction_id)
        if not sanitized.startswith("pred_"):
            sanitized = f"pred_{sanitized}"
        return self._root / f"{sanitized}.json"

    def _report_path(self, report_id: str) -> Path:
        """Return the JSON filepath for a given validation report ID."""
        sanitized = sanitize_id(report_id)
        if not sanitized.startswith("val_"):
            sanitized = f"val_{sanitized}"
        return self._reports_dir / f"{sanitized}.json"

    # ------------------------------------------------------------------
    # CRUD: PredictionRecord
    # ------------------------------------------------------------------

    def save(self, prediction: PredictionRecord) -> Path:
        """
        Persist a single PredictionRecord to disk.

        Parameters
        ----------
        prediction : PredictionRecord
            The prediction record to save.

        Returns
        -------
        Path
            Absolute path to the saved JSON file.
        """
        if not prediction.prediction_id:
            prediction.prediction_id = make_prediction_id(
                prediction.bill_id, prediction.company_isin, prediction.event_window
            )

        path = self._prediction_path(prediction.prediction_id)
        try:
            save_json(prediction.to_dict(), path)
            logger.debug("Saved prediction record: %s", path)
            return path
        except Exception as exc:
            logger.error("Failed to save prediction %s to %s: %s", prediction.prediction_id, path, exc)
            raise

    def save_many(self, predictions: list[PredictionRecord]) -> list[Path]:
        """
        Persist a list of PredictionRecord objects.

        Parameters
        ----------
        predictions : list[PredictionRecord]

        Returns
        -------
        list[Path]
        """
        saved_paths: list[Path] = []
        for record in predictions:
            path = self.save(record)
            saved_paths.append(path)
        logger.info("Saved %d prediction records to %s", len(saved_paths), self._root)
        return saved_paths

    def get(self, prediction_id: str) -> Optional[PredictionRecord]:
        """
        Retrieve a PredictionRecord by its prediction_id.

        Returns None if the record does not exist.
        """
        path = self._prediction_path(prediction_id)
        if not file_exists(path):
            return None
        try:
            data = load_json(path)
            return PredictionRecord.from_dict(data)
        except Exception as exc:
            logger.warning("Error loading prediction record %s: %s", path, exc)
            return None

    def get_by_key(
        self, bill_id: str, company_isin: str, event_window: str
    ) -> Optional[PredictionRecord]:
        """
        Retrieve a PredictionRecord by its composite key.
        """
        pred_id = make_prediction_id(bill_id, company_isin, event_window)
        return self.get(pred_id)

    def exists(self, bill_id: str, company_isin: str, event_window: str) -> bool:
        """
        Check whether a prediction record exists for the given composite key.
        """
        pred_id = make_prediction_id(bill_id, company_isin, event_window)
        return file_exists(self._prediction_path(pred_id))

    def get_by_bill(self, bill_id: str) -> list[PredictionRecord]:
        """
        Retrieve all PredictionRecord objects associated with a specific bill_id.
        """
        all_records = self.load_all()
        return [rec for rec in all_records if rec.bill_id == bill_id]

    def get_by_company(self, company_isin: str) -> list[PredictionRecord]:
        """
        Retrieve all PredictionRecord objects associated with a specific company ISIN.
        """
        all_records = self.load_all()
        return [rec for rec in all_records if rec.company_isin == company_isin]

    def load_all(self) -> list[PredictionRecord]:
        """
        Load all stored PredictionRecord objects from the predictions directory.
        """
        records: list[PredictionRecord] = []
        if not self._root.is_dir():
            return records

        json_files = list_files(self._root, pattern="*.json")
        for filepath in json_files:
            # Skip reports or subdirectories
            if filepath.parent != self._root or not filepath.name.startswith("pred_"):
                continue
            try:
                data = load_json(filepath)
                records.append(PredictionRecord.from_dict(data))
            except Exception as exc:
                logger.warning("Failed to deserialize prediction file %s: %s", filepath, exc)
        return records

    # ------------------------------------------------------------------
    # CRUD: PredictionValidationReport
    # ------------------------------------------------------------------

    def save_validation_report(self, report: PredictionValidationReport) -> Path:
        """
        Persist a PredictionValidationReport.
        """
        path = self._report_path(report.report_id)
        try:
            save_json(report.to_dict(), path)
            logger.debug("Saved prediction validation report: %s", path)
            return path
        except Exception as exc:
            logger.error("Failed to save validation report %s: %s", report.report_id, exc)
            raise

    def load_validation_reports(self) -> list[PredictionValidationReport]:
        """
        Load all stored validation reports.
        """
        reports: list[PredictionValidationReport] = []
        if not self._reports_dir.is_dir():
            return reports

        for filepath in list_files(self._reports_dir, pattern="*.json"):
            try:
                data = load_json(filepath)
                reports.append(PredictionValidationReport.from_dict(data))
            except Exception as exc:
                logger.warning("Failed to load validation report %s: %s", filepath, exc)
        return reports

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Delete all predictions and validation reports from disk."""
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
        logger.info("PredictionRepository cleared: %s", self._root)
