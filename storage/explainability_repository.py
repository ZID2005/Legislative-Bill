"""
storage/explainability_repository.py
=====================================
ExplainabilityRepository — persistence layer for SHAP explanations (Task 6.3).

Stores SHAP values, feature importance tables, local explanations, and
visualizations under the ``explainability/`` directory.

Directory Layout
----------------
::

    explainability/
    ├── <target>/
    │   └── <model_type>/
    │       ├── shap_values.parquet       ← SHAP value matrix (rows=samples, cols=features)
    │       ├── feature_importance.csv    ← mean |SHAP| per feature, sorted desc
    │       ├── local_explanations.json   ← per-sample SHAP for selected instances
    │       ├── summary_plot.png
    │       ├── bar_plot.png
    │       └── dependence_plots/
    │           └── <feature>_dependence.png (×10)
    ├── global_summary.json               ← top-20 features aggregated across all models
    ├── model_comparison.json             ← cross-model importance comparison
    └── feature_comparison.png

API
---
``save(target, model_type, shap_values_df, feature_importance_df, local_explanations)``
    Persist SHAP values, feature importance, and local explanations.

``load(target, model_type)``
    Load and return persisted SHAP artefacts as a dict.

``exists(target, model_type)``
    Return ``True`` if core artefacts exist for a (target, model_type) pair.

``save_global_summary(summary)``
    Persist the root-level ``global_summary.json``.

``save_model_comparison(comparison)``
    Persist the root-level ``model_comparison.json``.

``save_local_explanations(target, model_type, explanations)``
    Persist per-sample SHAP explanations for a given (target, model_type).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from config.logging_config import get_logger
from utils.file_utils import ensure_dir

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_TARGETS: frozenset[str] = frozenset(
    {"direction", "market_moving", "impact_strength", "confidence"}
)

VALID_MODEL_TYPES: frozenset[str] = frozenset(
    {"lgbm", "xgboost", "random_forest"}
)


class ExplainabilityRepository:
    """
    Persistence layer for SHAP explainability artefacts.

    Parameters
    ----------
    root_dir : Path, optional
        Root directory for explainability outputs.
        Defaults to ``settings.EXPLAINABILITY_DIR`` (``explainability/``).
    """

    SHAP_VALUES_FILE = "shap_values.parquet"
    FEATURE_IMPORTANCE_FILE = "feature_importance.csv"
    LOCAL_EXPLANATIONS_FILE = "local_explanations.json"
    GLOBAL_SUMMARY_FILE = "global_summary.json"
    MODEL_COMPARISON_FILE = "model_comparison.json"
    SUMMARY_PLOT_FILE = "summary_plot.png"
    BAR_PLOT_FILE = "bar_plot.png"
    DEPENDENCE_PLOTS_DIR = "dependence_plots"

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._root: Path = root_dir or settings.EXPLAINABILITY_DIR
        ensure_dir(self._root)
        logger.debug("ExplainabilityRepository initialised | root=%s", self._root)

    # ------------------------------------------------------------------
    # Directory helpers
    # ------------------------------------------------------------------

    def _model_dir(self, target: str, model_type: str) -> Path:
        """Return (and create) the per-model artefact directory."""
        self._validate(target, model_type)
        d = self._root / target / model_type
        ensure_dir(d)
        return d

    def _dependence_dir(self, target: str, model_type: str) -> Path:
        """Return (and create) the dependence_plots sub-directory."""
        d = self._model_dir(target, model_type) / self.DEPENDENCE_PLOTS_DIR
        ensure_dir(d)
        return d

    @staticmethod
    def _validate(target: str, model_type: str) -> None:
        """Raise ValueError for unrecognised target or model_type."""
        if target not in VALID_TARGETS:
            raise ValueError(
                f"Unknown target '{target}'. Must be one of {sorted(VALID_TARGETS)}."
            )
        if model_type not in VALID_MODEL_TYPES:
            raise ValueError(
                f"Unknown model_type '{model_type}'. "
                f"Must be one of {sorted(VALID_MODEL_TYPES)}."
            )

    # ------------------------------------------------------------------
    # save
    # ------------------------------------------------------------------

    def save(
        self,
        target: str,
        model_type: str,
        shap_values_df: pd.DataFrame,
        feature_importance_df: pd.DataFrame,
        local_explanations: dict[str, Any],
    ) -> dict[str, Path]:
        """
        Persist SHAP values, feature importance, and local explanations.

        Parameters
        ----------
        target : str
            One of ``direction``, ``market_moving``, ``impact_strength``,
            ``confidence``.
        model_type : str
            One of ``lgbm``, ``xgboost``, ``random_forest``.
        shap_values_df : pd.DataFrame
            SHAP value matrix — rows=samples, columns=features.
        feature_importance_df : pd.DataFrame
            Mean |SHAP| per feature, sorted descending.
            Expected columns: ``feature``, ``mean_abs_shap``.
        local_explanations : dict
            Nested dict of per-sample SHAP details keyed by category
            (``correct``, ``misclassified``, ``high_confidence``).

        Returns
        -------
        dict[str, Path]
            Mapping of artefact name → absolute path.
        """
        model_dir = self._model_dir(target, model_type)
        paths: dict[str, Path] = {}

        # 1. SHAP values (Parquet)
        shap_path = model_dir / self.SHAP_VALUES_FILE
        try:
            shap_values_df.to_parquet(shap_path, index=False)
            paths["shap_values"] = shap_path
            logger.info("Saved SHAP values: %s", shap_path)
        except Exception as exc:
            logger.error("Failed to save SHAP values to %s: %s", shap_path, exc)
            raise

        # 2. Feature importance (CSV)
        fi_path = model_dir / self.FEATURE_IMPORTANCE_FILE
        try:
            feature_importance_df.to_csv(fi_path, index=False)
            paths["feature_importance"] = fi_path
            logger.info("Saved feature importance: %s", fi_path)
        except Exception as exc:
            logger.error("Failed to save feature importance to %s: %s", fi_path, exc)
            raise

        # 3. Local explanations (JSON)
        local_path = model_dir / self.LOCAL_EXPLANATIONS_FILE
        try:
            with local_path.open("w", encoding="utf-8") as fh:
                json.dump(local_explanations, fh, indent=2, default=str)
            paths["local_explanations"] = local_path
            logger.info("Saved local explanations: %s", local_path)
        except Exception as exc:
            logger.error("Failed to save local explanations to %s: %s", local_path, exc)
            raise

        return paths

    # ------------------------------------------------------------------
    # load
    # ------------------------------------------------------------------

    def load(self, target: str, model_type: str) -> dict[str, Any]:
        """
        Load persisted SHAP artefacts for a (target, model_type).

        Returns
        -------
        dict
            Keys: ``shap_values`` (DataFrame), ``feature_importance`` (DataFrame),
            ``local_explanations`` (dict).

        Raises
        ------
        FileNotFoundError
            If the SHAP values Parquet file is missing.
        """
        model_dir = self._model_dir(target, model_type)
        result: dict[str, Any] = {}

        # SHAP values
        shap_path = model_dir / self.SHAP_VALUES_FILE
        if not shap_path.is_file():
            raise FileNotFoundError(
                f"SHAP values not found: {shap_path}. Run explain-models first."
            )
        result["shap_values"] = pd.read_parquet(shap_path)
        logger.info("Loaded SHAP values: %s", shap_path)

        # Feature importance
        fi_path = model_dir / self.FEATURE_IMPORTANCE_FILE
        if fi_path.is_file():
            result["feature_importance"] = pd.read_csv(fi_path)
        else:
            result["feature_importance"] = pd.DataFrame()

        # Local explanations
        local_path = model_dir / self.LOCAL_EXPLANATIONS_FILE
        if local_path.is_file():
            with local_path.open("r", encoding="utf-8") as fh:
                result["local_explanations"] = json.load(fh)
        else:
            result["local_explanations"] = {}

        return result

    # ------------------------------------------------------------------
    # exists
    # ------------------------------------------------------------------

    def exists(self, target: str, model_type: str) -> bool:
        """
        Return ``True`` if core SHAP artefacts exist for this (target, model_type).
        """
        try:
            self._validate(target, model_type)
        except ValueError:
            return False
        shap_path = self._root / target / model_type / self.SHAP_VALUES_FILE
        fi_path = self._root / target / model_type / self.FEATURE_IMPORTANCE_FILE
        return shap_path.is_file() and fi_path.is_file()

    # ------------------------------------------------------------------
    # Global summary
    # ------------------------------------------------------------------

    def save_global_summary(self, summary: dict[str, Any]) -> Path:
        """
        Persist the root-level ``global_summary.json``.

        Parameters
        ----------
        summary : dict
            Top-20 features aggregated across all models and targets.

        Returns
        -------
        Path
            Absolute path of the written file.
        """
        path = self._root / self.GLOBAL_SUMMARY_FILE
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(summary, fh, indent=2, default=str)
            logger.info("Saved global summary: %s", path)
        except Exception as exc:
            logger.error("Failed to save global summary to %s: %s", path, exc)
            raise
        return path

    def load_global_summary(self) -> dict[str, Any]:
        """Load ``global_summary.json`` from the repository root."""
        path = self._root / self.GLOBAL_SUMMARY_FILE
        if not path.is_file():
            raise FileNotFoundError(f"Global summary not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    # ------------------------------------------------------------------
    # Model comparison
    # ------------------------------------------------------------------

    def save_model_comparison(self, comparison: dict[str, Any]) -> Path:
        """
        Persist the root-level ``model_comparison.json``.

        Parameters
        ----------
        comparison : dict
            Cross-model feature importance comparison data.

        Returns
        -------
        Path
            Absolute path of the written file.
        """
        path = self._root / self.MODEL_COMPARISON_FILE
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(comparison, fh, indent=2, default=str)
            logger.info("Saved model comparison: %s", path)
        except Exception as exc:
            logger.error("Failed to save model comparison to %s: %s", path, exc)
            raise
        return path

    def load_model_comparison(self) -> dict[str, Any]:
        """Load ``model_comparison.json`` from the repository root."""
        path = self._root / self.MODEL_COMPARISON_FILE
        if not path.is_file():
            raise FileNotFoundError(f"Model comparison not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    # ------------------------------------------------------------------
    # Save local explanations separately (convenience overload)
    # ------------------------------------------------------------------

    def save_local_explanations(
        self,
        target: str,
        model_type: str,
        explanations: dict[str, Any],
    ) -> Path:
        """
        Persist only the local explanations JSON for a (target, model_type).

        Useful for updating local explanations without overwriting SHAP values.
        """
        model_dir = self._model_dir(target, model_type)
        path = model_dir / self.LOCAL_EXPLANATIONS_FILE
        with path.open("w", encoding="utf-8") as fh:
            json.dump(explanations, fh, indent=2, default=str)
        logger.info("Saved local explanations: %s", path)
        return path

    # ------------------------------------------------------------------
    # Directory accessors (used by Visualizer)
    # ------------------------------------------------------------------

    def model_dir(self, target: str, model_type: str) -> Path:
        """Public accessor for the per-model artefact directory."""
        return self._model_dir(target, model_type)

    def dependence_dir(self, target: str, model_type: str) -> Path:
        """Public accessor for the dependence_plots sub-directory."""
        return self._dependence_dir(target, model_type)

    @property
    def root(self) -> Path:
        """Repository root directory."""
        return self._root
