"""
storage/evaluation_repository.py
================================
EvaluationRepository — persistence layer for model evaluation outputs (Task 6.2).

Stores the evaluation metrics, confusion matrices, classification reports,
and algorithm comparison rankings under the `evaluation/` directory.

Files stored:
- `metrics.json`
- `confusion_matrix.csv`
- `classification_report.json`
- `comparison_report.json`
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from config.logging_config import get_logger
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


class EvaluationRepository:
    """
    Persistence layer for model evaluation outputs.

    Parameters
    ----------
    eval_dir : Path, optional
        Directory where evaluation files are saved.
        Defaults to `settings.ML_EVAL_DIR` (`evaluation/`).
    """

    METRICS_FILE = "metrics.json"
    CONFUSION_MATRIX_FILE = "confusion_matrix.csv"
    CLASSIFICATION_REPORT_FILE = "classification_report.json"
    COMPARISON_REPORT_FILE = "comparison_report.json"

    def __init__(self, eval_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._root: Path = eval_dir or settings.ML_EVAL_DIR
        ensure_dir(self._root)
        logger.debug("EvaluationRepository initialised | root=%s", self._root)

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def save_metrics(self, metrics: dict[str, Any]) -> Path:
        """Save evaluation metrics to metrics.json."""
        path = self._root / self.METRICS_FILE
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(metrics, fh, indent=2, default=str)
            logger.info("Saved evaluation metrics: %s", path)
        except Exception as exc:
            logger.error("Failed to save metrics to %s: %s", path, exc)
            raise
        return path

    def load_metrics(self) -> dict[str, Any]:
        """Load evaluation metrics from metrics.json."""
        path = self._root / self.METRICS_FILE
        if not path.is_file():
            raise FileNotFoundError(f"Metrics file not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    # ------------------------------------------------------------------
    # Confusion Matrix
    # ------------------------------------------------------------------

    def save_confusion_matrix(self, df: pd.DataFrame) -> Path:
        """Save confusion matrices DataFrame to confusion_matrix.csv."""
        path = self._root / self.CONFUSION_MATRIX_FILE
        try:
            df.to_csv(path, index=False)
            logger.info("Saved confusion matrices: %s", path)
        except Exception as exc:
            logger.error("Failed to save confusion matrix to %s: %s", path, exc)
            raise
        return path

    def load_confusion_matrix(self) -> pd.DataFrame:
        """Load confusion matrices from confusion_matrix.csv."""
        path = self._root / self.CONFUSION_MATRIX_FILE
        if not path.is_file():
            raise FileNotFoundError(f"Confusion matrix file not found: {path}")
        return pd.read_csv(path)

    # ------------------------------------------------------------------
    # Classification Report
    # ------------------------------------------------------------------

    def save_classification_report(self, report: dict[str, Any]) -> Path:
        """Save detailed classification reports to classification_report.json."""
        path = self._root / self.CLASSIFICATION_REPORT_FILE
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2, default=str)
            logger.info("Saved classification report: %s", path)
        except Exception as exc:
            logger.error("Failed to save classification report to %s: %s", path, exc)
            raise
        return path

    def load_classification_report(self) -> dict[str, Any]:
        """Load classification reports from classification_report.json."""
        path = self._root / self.CLASSIFICATION_REPORT_FILE
        if not path.is_file():
            raise FileNotFoundError(f"Classification report file not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    # ------------------------------------------------------------------
    # Comparison Report
    # ------------------------------------------------------------------

    def save_comparison_report(self, report: dict[str, Any]) -> Path:
        """Save algorithm comparative ranking to comparison_report.json."""
        path = self._root / self.COMPARISON_REPORT_FILE
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(report, fh, indent=2, default=str)
            logger.info("Saved model comparison report: %s", path)
        except Exception as exc:
            logger.error("Failed to save comparison report to %s: %s", path, exc)
            raise
        return path

    def load_comparison_report(self) -> dict[str, Any]:
        """Load algorithm comparison from comparison_report.json."""
        path = self._root / self.COMPARISON_REPORT_FILE
        if not path.is_file():
            raise FileNotFoundError(f"Comparison report file not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    # ------------------------------------------------------------------
    # Status Helpers
    # ------------------------------------------------------------------

    def exists(self) -> bool:
        """Return True if all four required evaluation files exist."""
        return (
            (self._root / self.METRICS_FILE).is_file()
            and (self._root / self.CONFUSION_MATRIX_FILE).is_file()
            and (self._root / self.CLASSIFICATION_REPORT_FILE).is_file()
            and (self._root / self.COMPARISON_REPORT_FILE).is_file()
        )

    def clear(self) -> None:
        """Remove all evaluation files from the repository."""
        for filename in [
            self.METRICS_FILE,
            self.CONFUSION_MATRIX_FILE,
            self.CLASSIFICATION_REPORT_FILE,
            self.COMPARISON_REPORT_FILE,
        ]:
            path = self._root / filename
            if path.is_file():
                try:
                    path.unlink()
                    logger.debug("Deleted evaluation file: %s", path)
                except Exception as exc:
                    logger.warning("Could not delete %s: %s", path, exc)
