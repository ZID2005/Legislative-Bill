"""
storage/fusion_repository.py
=============================
Repository for persisting and querying fused ML datasets (Task 5.3).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd
from config.logging_config import get_logger
from schemas.fusion_validation_report import FusionValidationReport
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


class FusionRepository:
    """
    Repository for persisting and querying fused legislative datasets.

    Parameters
    ----------
    fused_dir : Path, optional
        Root directory for fused datasets. Defaults to settings.FUSED_DIR.
    """

    SUPPORTED_MODES = {
        "structured": "structured_dataset.parquet",
        "finbert": "finbert_dataset.parquet",
        "legal": "legal_dataset.parquet",
        "structured-finbert": "structured_finbert_dataset.parquet",
        "structured-legal": "structured_legal_dataset.parquet",
        "hybrid": "hybrid_dataset.parquet",
    }

    def __init__(self, fused_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._fused_dir: Path = fused_dir or settings.FUSED_DIR
        ensure_dir(self._fused_dir)

        logger.debug(
            "FusionRepository initialised | dir=%s",
            self._fused_dir,
        )

    def _get_paths(self, mode: str) -> tuple[Path, Path]:
        """Get the Parquet and validation report JSON file paths for a mode."""
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(
                f"Unsupported fusion mode: '{mode}'. "
                f"Must be one of {list(self.SUPPORTED_MODES.keys())}"
            )
        filename = self.SUPPORTED_MODES[mode]
        parquet_path = self._fused_dir / filename
        report_path = self._fused_dir / f"validation_report_{mode}.json"
        return parquet_path, report_path

    def save(
        self,
        mode: str,
        df: pd.DataFrame,
        report: FusionValidationReport,
    ) -> Path:
        """
        Persist a fused DataFrame and its companion validation report.

        Parameters
        ----------
        mode : str
            The fusion mode.
        df : pd.DataFrame
            The fused DataFrame to persist.
        report : FusionValidationReport
            The companion validation report to persist.

        Returns
        -------
        Path
            Path to the written Parquet file.
        """
        parquet_path, report_path = self._get_paths(mode)

        # 1. Write Parquet dataset
        try:
            df.to_parquet(parquet_path, index=False)
            logger.info("Persisted fused dataset for mode '%s' at %s", mode, parquet_path)
        except Exception as exc:
            logger.error("Failed to write fused Parquet for mode '%s': %s", mode, exc)
            raise

        # 2. Write Validation Report JSON
        try:
            with report_path.open("w", encoding="utf-8") as fh:
                json.dump(report.to_dict(), fh, indent=2)
            logger.info("Persisted validation report for mode '%s' at %s", mode, report_path)
        except Exception as exc:
            logger.error("Failed to write validation report JSON for mode '%s': %s", mode, exc)
            raise

        return parquet_path

    def load(self, mode: str) -> pd.DataFrame:
        """
        Load the fused dataset for the given mode.

        Parameters
        ----------
        mode : str
            The fusion mode to load.

        Returns
        -------
        pd.DataFrame
            The loaded fused dataset.
        """
        parquet_path, _ = self._get_paths(mode)
        if not parquet_path.is_file():
            raise FileNotFoundError(f"Fused dataset for mode '{mode}' does not exist at {parquet_path}.")
        try:
            return pd.read_parquet(parquet_path)
        except Exception as exc:
            logger.error("Failed to load fused Parquet for mode '%s': %s", mode, exc)
            raise

    def load_report(self, mode: str) -> Optional[FusionValidationReport]:
        """
        Load the validation report for the given mode.

        Parameters
        ----------
        mode : str
            The fusion mode.

        Returns
        -------
        FusionValidationReport or None
            The validation report, or None if it doesn't exist.
        """
        _, report_path = self._get_paths(mode)
        if not report_path.is_file():
            return None
        try:
            with report_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return FusionValidationReport.from_dict(data)
        except Exception as exc:
            logger.error("Failed to load validation report for mode '%s': %s", mode, exc)
            return None

    def exists(self, mode: str) -> bool:
        """
        Check if the fused dataset for a given mode exists.

        Parameters
        ----------
        mode : str
            The fusion mode.

        Returns
        -------
        bool
            True if the Parquet file exists.
        """
        try:
            parquet_path, _ = self._get_paths(mode)
            return parquet_path.is_file()
        except ValueError:
            return False

    def list_modes(self) -> list[str]:
        """
        Return the list of all supported fusion modes.

        Returns
        -------
        list[str]
            List of supported fusion modes.
        """
        return list(self.SUPPORTED_MODES.keys())

    def clear(self) -> None:
        """Delete all fused datasets and validation reports in the directory."""
        for mode in self.SUPPORTED_MODES:
            try:
                parquet_path, report_path = self._get_paths(mode)
                if parquet_path.is_file():
                    parquet_path.unlink()
                if report_path.is_file():
                    report_path.unlink()
                logger.info("Cleared files for mode '%s'", mode)
            except Exception as exc:
                logger.error("Error clearing files for mode '%s': %s", mode, exc)

    @property
    def fused_dir(self) -> Path:
        """Path to the fused directory."""
        return self._fused_dir
