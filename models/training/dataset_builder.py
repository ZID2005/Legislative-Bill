"""
models/training/dataset_builder.py
====================================
Dataset preparation layer for Task 6.1 — ML Training Engine.

Responsibility
--------------
Load the feature-selected dataset (output of Task 5.4) and produce two
strictly separated artefacts:

1. **Training Dataset** (``data/ml/training_dataset.parquet``)
   Contains *only* information available before or at bill introduction.
   All post-event variables are removed to prevent target leakage.

2. **Research Dataset** (``data/ml/research_dataset.parquet``)
   Retains the complete feature set for statistical analysis,
   visualisation, academic reporting, and model evaluation.
   Must **never** be used as input to model training.

Leakage Prevention
------------------
Post-event columns are identified by:
  * Exact column name match against ``POST_EVENT_COLUMNS`` (see
    ``schemas/training_dataset.py``)
  * Column name prefix match against ``POST_EVENT_PREFIXES``

Both matching criteria are applied *case-insensitively* so that minor
naming variations (e.g. ``T_Statistic`` vs ``t_statistic``) are caught.

References
----------
MacKinlay, A.C. (1997). Event Studies in Economics and Finance.
Journal of Economic Literature, 35(1), 13–39.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd
from config.logging_config import get_logger
from schemas.training_dataset import (
    POST_EVENT_COLUMNS,
    POST_EVENT_PREFIXES,
    DatasetDescriptor,
)
from storage.feature_selection_repository import FeatureSelectionRepository
from utils.file_utils import ensure_dir

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Column groups — metadata identifiers that are neither features nor targets
# ---------------------------------------------------------------------------
_METADATA_COLS: frozenset[str] = frozenset(
    {
        "record_id",
        "bill_id",
        "company_isin",
        "event_window",
        "bill_title",
        "company_name",
        "nse_symbol",
        "isin",
        "introduction_date",
        "feature_version",
        "built_at",
    }
)

_TARGET_COLS: frozenset[str] = frozenset(
    {
        "direction",
        "market_moving",
        "impact_strength",
        "confidence_label",
    }
)


class DatasetBuilder:
    """
    Builds Training and Research datasets from selected features.

    Parameters
    ----------
    selection_repo : FeatureSelectionRepository, optional
        Repository to load selected features from.  Defaults to the
        standard ``FeatureSelectionRepository``.
    output_dir : Path, optional
        Directory where the two Parquet files are written.  Defaults to
        ``settings.ML_DATA_DIR`` (``data/ml/``).
    """

    TRAINING_FILENAME = "training_dataset.parquet"
    RESEARCH_FILENAME = "research_dataset.parquet"
    TRAINING_META_FILENAME = "training_dataset_metadata.json"
    RESEARCH_META_FILENAME = "research_dataset_metadata.json"

    def __init__(
        self,
        selection_repo: Optional[FeatureSelectionRepository] = None,
        output_dir: Optional[Path] = None,
    ) -> None:
        from config.settings import settings

        self._selection_repo = selection_repo or FeatureSelectionRepository()
        self._output_dir: Path = output_dir or settings.ML_DATA_DIR
        ensure_dir(self._output_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        mode: str = "structured",
        rebuild: bool = False,
    ) -> tuple[pd.DataFrame, pd.DataFrame, DatasetDescriptor, DatasetDescriptor]:
        """
        Build and persist the Training and Research datasets.

        Parameters
        ----------
        mode : str
            Feature-selection mode to load (e.g. ``"structured"``).
        rebuild : bool
            If ``False`` (default) and both Parquet files already exist,
            load and return them without reprocessing.

        Returns
        -------
        tuple
            ``(df_training, df_research, training_descriptor,
              research_descriptor)``
        """
        train_path = self._output_dir / self.TRAINING_FILENAME
        research_path = self._output_dir / self.RESEARCH_FILENAME
        train_meta_path = self._output_dir / self.TRAINING_META_FILENAME
        research_meta_path = self._output_dir / self.RESEARCH_META_FILENAME

        if not rebuild and train_path.is_file() and research_path.is_file():
            logger.info(
                "Datasets already exist — loading from disk (use rebuild=True to force)."
            )
            df_train = pd.read_parquet(train_path)
            df_research = pd.read_parquet(research_path)

            train_desc = self._load_descriptor(train_meta_path)
            research_desc = self._load_descriptor(research_meta_path)

            if train_desc is None:
                train_desc = self._make_descriptor(
                    "training", df_train, [], mode, str(train_path)
                )
            if research_desc is None:
                research_desc = self._make_descriptor(
                    "research", df_research, [], mode, str(research_path)
                )
            return df_train, df_research, train_desc, research_desc

        logger.info("Building ML datasets from feature-selection mode='%s'.", mode)

        # 1. Load selected features
        df_full = self._selection_repo.load(mode)
        if df_full.empty:
            raise ValueError(
                f"Selected features for mode='{mode}' are empty. "
                "Run feature selection (Task 5.4) first."
            )

        logger.info(
            "Loaded selected features: %d rows × %d columns.",
            len(df_full),
            len(df_full.columns),
        )

        # 2. Sort chronologically by introduction_date (required for time-split)
        df_full = self._sort_chronologically(df_full)

        # 3. Build research dataset (full features — no columns removed)
        df_research = df_full.copy()
        research_desc = self._make_descriptor(
            name="research",
            df=df_research,
            removed=[],
            mode=mode,
            path=str(research_path),
            notes="Complete feature set. For academic analysis only.",
        )

        # 4. Build training dataset (strip post-event columns)
        df_training, removed_cols = self._strip_post_event_columns(df_full)
        train_desc = self._make_descriptor(
            name="training",
            df=df_training,
            removed=removed_cols,
            mode=mode,
            path=str(train_path),
            notes=(
                f"Post-event columns removed ({len(removed_cols)} total). "
                "Safe for model training."
            ),
        )

        # 5. Validate targets are present
        self._validate_targets(df_training)

        # 6. Persist both datasets
        df_training.to_parquet(train_path, index=False)
        logger.info("Training dataset saved: %s (%d rows).", train_path, len(df_training))

        df_research.to_parquet(research_path, index=False)
        logger.info("Research dataset saved: %s (%d rows).", research_path, len(df_research))

        # 7. Persist descriptors
        self._save_descriptor(train_desc, train_meta_path)
        self._save_descriptor(research_desc, research_meta_path)

        logger.info(
            "Dataset build complete. "
            "Training columns: %d. Research columns: %d. Removed: %d.",
            len(df_training.columns),
            len(df_research.columns),
            len(removed_cols),
        )

        return df_training, df_research, train_desc, research_desc

    # ------------------------------------------------------------------
    # Feature access helpers (for the trainer to use)
    # ------------------------------------------------------------------

    def get_feature_columns(self, df: pd.DataFrame) -> list[str]:
        """
        Return the list of feature columns from a dataset DataFrame.

        Excludes metadata identifiers and target label columns.
        """
        return [
            c
            for c in df.columns
            if c not in _METADATA_COLS and c not in _TARGET_COLS
        ]

    def get_target_columns(self, df: pd.DataFrame) -> list[str]:
        """Return target columns present in the DataFrame."""
        return [c for c in _TARGET_COLS if c in df.columns]

    def get_metadata_columns(self, df: pd.DataFrame) -> list[str]:
        """Return metadata/identifier columns present in the DataFrame."""
        return [c for c in _METADATA_COLS if c in df.columns]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sort_chronologically(df: pd.DataFrame) -> pd.DataFrame:
        """
        Sort DataFrame by ``introduction_date`` ascending.

        If the column is absent or unparseable, emit a warning and
        return the original order (TimeSeriesSplit will still work
        but splits may be less meaningful).
        """
        if "introduction_date" not in df.columns:
            logger.warning(
                "'introduction_date' column missing — cannot sort chronologically. "
                "TimeSeriesSplit may not produce clean temporal folds."
            )
            return df

        try:
            df = df.copy()
            df["introduction_date"] = pd.to_datetime(
                df["introduction_date"], errors="coerce"
            )
            df = df.sort_values("introduction_date", ascending=True, na_position="last")
            df = df.reset_index(drop=True)
            logger.debug(
                "Sorted %d rows chronologically by introduction_date.", len(df)
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to sort by introduction_date: %s. Using original order.", exc
            )
        return df

    @staticmethod
    def _strip_post_event_columns(
        df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, list[str]]:
        """
        Remove all post-event columns from *df*.

        Returns
        -------
        tuple
            ``(df_stripped, removed_column_names)``
        """
        cols_lower = {c.lower(): c for c in df.columns}
        to_remove: set[str] = set()

        for col_lower, col_orig in cols_lower.items():
            # Exact match against blacklist
            if col_lower in POST_EVENT_COLUMNS:
                to_remove.add(col_orig)
                continue
            # Prefix match
            for prefix in POST_EVENT_PREFIXES:
                if col_lower.startswith(prefix):
                    to_remove.add(col_orig)
                    break

        removed = sorted(to_remove)
        if removed:
            logger.info(
                "Stripped %d post-event / target-leakage column(s): %s",
                len(removed),
                removed,
            )
        else:
            logger.info("No post-event columns detected — training dataset unchanged.")

        df_stripped = df.drop(columns=removed)
        return df_stripped, removed

    @staticmethod
    def _validate_targets(df: pd.DataFrame) -> None:
        """Warn if any target column is entirely missing from the dataset."""
        present = [c for c in _TARGET_COLS if c in df.columns]
        missing = _TARGET_COLS - set(present)
        if missing:
            logger.warning(
                "Target column(s) missing from training dataset: %s. "
                "Those classifiers cannot be trained.",
                sorted(missing),
            )
        if not present:
            raise ValueError(
                "Training dataset contains none of the required target columns: "
                f"{sorted(_TARGET_COLS)}. Cannot train any classifier."
            )

    def _make_descriptor(
        self,
        name: str,
        df: pd.DataFrame,
        removed: list[str],
        mode: str,
        path: str,
        notes: str = "",
    ) -> DatasetDescriptor:
        """Construct a ``DatasetDescriptor`` from a DataFrame."""
        feature_cols = self.get_feature_columns(df)
        target_cols = self.get_target_columns(df)
        meta_cols = self.get_metadata_columns(df)
        return DatasetDescriptor(
            name=name,
            path=path,
            n_rows=len(df),
            n_features=len(feature_cols),
            feature_columns=feature_cols,
            target_columns=target_cols,
            metadata_columns=meta_cols,
            removed_columns=removed,
            source_mode=mode,
            notes=notes,
        )

    @staticmethod
    def _save_descriptor(desc: DatasetDescriptor, path: Path) -> None:
        """Persist a ``DatasetDescriptor`` to JSON."""
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(desc.to_dict(), fh, indent=2, default=str)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not save dataset descriptor to %s: %s", path, exc)

    @staticmethod
    def _load_descriptor(path: Path) -> Optional[DatasetDescriptor]:
        """Load a ``DatasetDescriptor`` from JSON, or return None."""
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return DatasetDescriptor(**data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load dataset descriptor from %s: %s", path, exc)
            return None
