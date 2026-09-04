"""
storage/feature_selection_repository.py
=======================================
Repository for persisting and querying feature selection results (Task 5.4).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd
from config.logging_config import get_logger
from schemas.feature_selection_validation_report import FeatureSelectionValidationReport
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


class FeatureSelectionRepository:
    """
    Repository for persisting and loading feature selection outputs.

    Parameters
    ----------
    selection_dir : Path, optional
        Root directory for feature selection outputs. Defaults to settings.DATA_DIR / "feature_selection".
    """

    SUPPORTED_MODES = [
        "structured",
        "finbert",
        "legal",
        "structured-finbert",
        "structured-legal",
        "hybrid",
    ]

    def __init__(self, selection_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._selection_dir: Path = selection_dir or (settings.DATA_DIR / "feature_selection")
        ensure_dir(self._selection_dir)

        logger.debug(
            "FeatureSelectionRepository initialised | dir=%s",
            self._selection_dir,
        )

    def _get_mode_dir(self, mode: str) -> Path:
        """Get and ensure the directory for a specific mode."""
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(
                f"Unsupported fusion/selection mode: '{mode}'. "
                f"Must be one of {self.SUPPORTED_MODES}"
            )
        mode_dir = self._selection_dir / mode
        ensure_dir(mode_dir)
        return mode_dir

    def _get_paths(self, mode: str) -> dict[str, Path]:
        """Get the paths for all feature selection outputs of a mode."""
        mode_dir = self._get_mode_dir(mode)
        return {
            "selected_features": mode_dir / "selected_features.parquet",
            "feature_importance": mode_dir / "feature_importance.csv",
            "removed_features": mode_dir / "removed_features.json",
            "selection_report": mode_dir / "selection_report.json",
        }

    def save(
        self,
        mode: str,
        df: pd.DataFrame,
        importance: pd.DataFrame,
        removed: dict,
        report: FeatureSelectionValidationReport,
    ) -> dict[str, Path]:
        """
        Persist feature selection outputs for a specific mode.

        Parameters
        ----------
        mode : str
            The fusion mode.
        df : pd.DataFrame
            DataFrame of selected features.
        importance : pd.DataFrame
            DataFrame of ranked feature importance.
        removed : dict
            Dict mapping feature elimination techniques to the lists of removed features.
        report : FeatureSelectionValidationReport
            Companion validation report.

        Returns
        -------
        dict[str, Path]
            Dict of written paths.
        """
        paths = self._get_paths(mode)

        # 1. Save selected features Parquet
        try:
            df.to_parquet(paths["selected_features"], index=False)
            logger.info("Persisted selected features Parquet for mode '%s' at %s", mode, paths["selected_features"])
        except Exception as exc:
            logger.error("Failed to write selected features Parquet for mode '%s': %s", mode, exc)
            raise

        # 2. Save feature importance CSV
        try:
            importance.to_csv(paths["feature_importance"], index=False)
            logger.info("Persisted feature importance CSV for mode '%s' at %s", mode, paths["feature_importance"])
        except Exception as exc:
            logger.error("Failed to write feature importance CSV for mode '%s': %s", mode, exc)
            raise

        # 3. Save removed features JSON
        try:
            with paths["removed_features"].open("w", encoding="utf-8") as fh:
                json.dump(removed, fh, indent=2)
            logger.info("Persisted removed features JSON for mode '%s' at %s", mode, paths["removed_features"])
        except Exception as exc:
            logger.error("Failed to write removed features JSON for mode '%s': %s", mode, exc)
            raise

        # 4. Save validation/selection report JSON
        try:
            with paths["selection_report"].open("w", encoding="utf-8") as fh:
                json.dump(report.to_dict(), fh, indent=2)
            logger.info("Persisted selection report JSON for mode '%s' at %s", mode, paths["selection_report"])
        except Exception as exc:
            logger.error("Failed to write selection report JSON for mode '%s': %s", mode, exc)
            raise

        return paths

    def load(self, mode: str) -> pd.DataFrame:
        """
        Load the selected features dataset for the given mode.

        Parameters
        ----------
        mode : str
            The mode to load.

        Returns
        -------
        pd.DataFrame
            The loaded DataFrame.
        """
        paths = self._get_paths(mode)
        parquet_path = paths["selected_features"]
        if not parquet_path.is_file():
            raise FileNotFoundError(f"Selected features dataset for mode '{mode}' does not exist at {parquet_path}.")
        try:
            return pd.read_parquet(parquet_path)
        except Exception as exc:
            logger.error("Failed to load selected features Parquet for mode '%s': %s", mode, exc)
            raise

    def load_importance(self, mode: str) -> pd.DataFrame:
        """Load feature importance CSV for the given mode."""
        paths = self._get_paths(mode)
        csv_path = paths["feature_importance"]
        if not csv_path.is_file():
            raise FileNotFoundError(f"Feature importance CSV for mode '{mode}' does not exist at {csv_path}.")
        try:
            return pd.read_csv(csv_path)
        except Exception as exc:
            logger.error("Failed to load feature importance CSV for mode '%s': %s", mode, exc)
            raise

    def load_removed(self, mode: str) -> dict:
        """Load removed features JSON for the given mode."""
        paths = self._get_paths(mode)
        json_path = paths["removed_features"]
        if not json_path.is_file():
            raise FileNotFoundError(f"Removed features JSON for mode '{mode}' does not exist at {json_path}.")
        try:
            with json_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            logger.error("Failed to load removed features JSON for mode '%s': %s", mode, exc)
            raise

    def load_report(self, mode: str) -> Optional[FeatureSelectionValidationReport]:
        """Load validation/selection report JSON for the given mode."""
        paths = self._get_paths(mode)
        json_path = paths["selection_report"]
        if not json_path.is_file():
            return None
        try:
            with json_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return FeatureSelectionValidationReport.from_dict(data)
        except Exception as exc:
            logger.error("Failed to load selection report JSON for mode '%s': %s", mode, exc)
            raise

    def exists(self, mode: str) -> bool:
        """Check if selection outputs exist for the given mode."""
        try:
            paths = self._get_paths(mode)
            return all(p.is_file() for p in paths.values())
        except ValueError:
            return False

    def list_modes(self) -> list[str]:
        """List all supported modes."""
        return self.SUPPORTED_MODES
