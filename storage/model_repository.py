"""
storage/model_repository.py
============================
ModelRepository — persistence layer for trained ML model artefacts (Task 6.1).

Each trained model is stored in a target-specific subdirectory under
``models/<target>/<model_type>/``:

::

    models/
        direction/
            lgbm/
                model.pkl
                preprocessor.pkl
                features.json
                metadata.json
                training_report.json
            xgboost/
                ...
            random_forest/
                ...
        market_moving/   ...
        impact_strength/ ...
        confidence/      ...

API
---
ModelRepository provides four operations:

``save(target, model_type, model, preprocessor, feature_list, report)``
    Serialise and persist all model artefacts.

``load(target, model_type)``
    Deserialise and return ``(model, preprocessor, feature_list)``.

``exists(target, model_type)``
    Return ``True`` if a saved model is available.

``list_models()``
    Return a list of ``(target, model_type)`` tuples for all persisted models.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from utils.file_utils import ensure_dir

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

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


class ModelRepository:
    """
    Persistence layer for trained ML model artefacts.

    Parameters
    ----------
    models_dir : Path, optional
        Root directory that contains per-target subdirectories.
        Defaults to ``settings.ML_MODELS_DIR`` (``models/``).
    """

    MODEL_FILE = "model.pkl"
    PREPROCESSOR_FILE = "preprocessor.pkl"
    FEATURES_FILE = "features.json"
    METADATA_FILE = "metadata.json"
    REPORT_FILE = "training_report.json"

    def __init__(self, models_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._root: Path = models_dir or settings.ML_MODELS_DIR
        ensure_dir(self._root)

        if not HAS_JOBLIB:
            logger.warning(
                "joblib is not installed. Model serialisation will be unavailable. "
                "Install it with: pip install joblib"
            )

        logger.debug("ModelRepository initialised | root=%s", self._root)

    # ------------------------------------------------------------------
    # Directory resolution
    # ------------------------------------------------------------------

    def _model_dir(self, target: str, model_type: str) -> Path:
        """Return and ensure the directory for a (target, model_type) pair."""
        self._validate(target, model_type)
        d = self._root / target / model_type
        ensure_dir(d)
        return d

    @staticmethod
    def _validate(target: str, model_type: str) -> None:
        """Raise ValueError if target or model_type is not recognised."""
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
        model: Any,
        preprocessor: Any,
        feature_list: list[str],
        report: Optional[Any] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Path]:
        """
        Serialise and persist all model artefacts.

        Parameters
        ----------
        target : str
            Label target — one of ``direction``, ``market_moving``,
            ``impact_strength``, ``confidence``.
        model_type : str
            Algorithm name — ``lgbm``, ``xgboost``, or ``random_forest``.
        model : Any
            Fitted estimator object (sklearn-compatible).
        preprocessor : Any
            Fitted ``ColumnTransformer`` / ``Pipeline`` object, or ``None``.
        feature_list : list[str]
            Ordered list of feature column names used at training time.
        report : TrainingReport, optional
            Full training report.  Serialised to ``training_report.json``.
        metadata : dict, optional
            Extra key/value metadata stored in ``metadata.json``.

        Returns
        -------
        dict[str, Path]
            Mapping of artefact name → absolute path.
        """
        if not HAS_JOBLIB:
            raise RuntimeError(
                "joblib is required for model persistence. "
                "Install with: pip install joblib"
            )

        model_dir = self._model_dir(target, model_type)
        paths: dict[str, Path] = {}

        # 1. Model
        model_path = model_dir / self.MODEL_FILE
        joblib.dump(model, model_path)
        paths["model"] = model_path
        logger.info("Saved model: %s", model_path)

        # 2. Preprocessor
        preprocessor_path = model_dir / self.PREPROCESSOR_FILE
        joblib.dump(preprocessor, preprocessor_path)
        paths["preprocessor"] = preprocessor_path
        logger.info("Saved preprocessor: %s", preprocessor_path)

        # 3. Feature list
        features_path = model_dir / self.FEATURES_FILE
        with features_path.open("w", encoding="utf-8") as fh:
            json.dump({"features": feature_list}, fh, indent=2)
        paths["features"] = features_path
        logger.info("Saved feature list (%d features): %s", len(feature_list), features_path)

        # 4. Metadata
        meta = {
            "target": target,
            "model_type": model_type,
            "feature_count": len(feature_list),
            **(metadata or {}),
        }
        metadata_path = model_dir / self.METADATA_FILE
        with metadata_path.open("w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=2, default=str)
        paths["metadata"] = metadata_path

        # 5. Training report
        if report is not None:
            report_path = model_dir / self.REPORT_FILE
            report_data = report.to_dict() if hasattr(report, "to_dict") else report
            with report_path.open("w", encoding="utf-8") as fh:
                json.dump(report_data, fh, indent=2, default=str)
            paths["report"] = report_path
            logger.info("Saved training report: %s", report_path)

        return paths

    # ------------------------------------------------------------------
    # load
    # ------------------------------------------------------------------

    def load(
        self,
        target: str,
        model_type: str,
    ) -> tuple[Any, Any, list[str]]:
        """
        Deserialise and return the model, preprocessor, and feature list.

        Parameters
        ----------
        target : str
            Label target name.
        model_type : str
            Algorithm name.

        Returns
        -------
        tuple
            ``(model, preprocessor, feature_list)``

        Raises
        ------
        FileNotFoundError
            If the model directory or any required artefact is missing.
        RuntimeError
            If joblib is not installed.
        """
        if not HAS_JOBLIB:
            raise RuntimeError(
                "joblib is required for model loading. "
                "Install with: pip install joblib"
            )

        model_dir = self._model_dir(target, model_type)

        model_path = model_dir / self.MODEL_FILE
        if not model_path.is_file():
            raise FileNotFoundError(
                f"Model artefact not found: {model_path}. "
                "Run training first."
            )

        preprocessor_path = model_dir / self.PREPROCESSOR_FILE
        features_path = model_dir / self.FEATURES_FILE

        model = joblib.load(model_path)
        logger.info("Loaded model: %s", model_path)

        preprocessor = None
        if preprocessor_path.is_file():
            preprocessor = joblib.load(preprocessor_path)
            logger.debug("Loaded preprocessor: %s", preprocessor_path)

        feature_list: list[str] = []
        if features_path.is_file():
            with features_path.open("r", encoding="utf-8") as fh:
                feature_list = json.load(fh).get("features", [])
            logger.debug("Loaded %d features from: %s", len(feature_list), features_path)

        return model, preprocessor, feature_list

    # ------------------------------------------------------------------
    # exists
    # ------------------------------------------------------------------

    def exists(self, target: str, model_type: str) -> bool:
        """
        Return ``True`` if a saved model exists for this (target, model_type).

        Parameters
        ----------
        target : str
        model_type : str

        Returns
        -------
        bool
        """
        try:
            self._validate(target, model_type)
        except ValueError:
            return False
        model_path = self._root / target / model_type / self.MODEL_FILE
        return model_path.is_file()

    # ------------------------------------------------------------------
    # list_models
    # ------------------------------------------------------------------

    def list_models(self) -> list[tuple[str, str]]:
        """
        Return a sorted list of all persisted ``(target, model_type)`` tuples.

        Returns
        -------
        list[tuple[str, str]]
            e.g. ``[("confidence", "lgbm"), ("direction", "lgbm"), ...]``
        """
        results: list[tuple[str, str]] = []
        for target in sorted(VALID_TARGETS):
            for model_type in sorted(VALID_MODEL_TYPES):
                if self.exists(target, model_type):
                    results.append((target, model_type))
        return results

    # ------------------------------------------------------------------
    # load_report
    # ------------------------------------------------------------------

    def load_report(self, target: str, model_type: str) -> Optional[dict[str, Any]]:
        """
        Load the training report JSON for a given (target, model_type).

        Returns ``None`` if the report does not exist.
        """
        self._validate(target, model_type)
        report_path = self._root / target / model_type / self.REPORT_FILE
        if not report_path.is_file():
            return None
        with report_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def load_metadata(self, target: str, model_type: str) -> Optional[dict[str, Any]]:
        """
        Load the metadata JSON for a given (target, model_type).

        Returns ``None`` if the metadata file does not exist.
        """
        self._validate(target, model_type)
        meta_path = self._root / target / model_type / self.METADATA_FILE
        if not meta_path.is_file():
            return None
        with meta_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
