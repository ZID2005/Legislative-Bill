"""
schemas/training_dataset.py
============================
Schema descriptors for the Training and Research datasets produced by
the ``DatasetBuilder`` (Task 6.1).

Purpose
-------
``TrainingDataset``
    Machine-learning-ready dataset.  Contains **only** features that are
    known before or at the time a bill is introduced.  Post-event
    variables are removed to prevent target leakage.

``ResearchDataset``
    Full feature set retained for statistical analysis, visualisation,
    academic reporting, and model evaluation.  Must **never** be used
    as input to model training.

Both are stored in Apache Parquet under ``data/ml/``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Constant: post-event columns that must be stripped from training data
# ---------------------------------------------------------------------------

#: All column name fragments that indicate a post-event / target-leakage
#: variable.  Any column whose name *exactly matches* one of these strings,
#: or whose name *starts with* ``"ar_day"`` or ``"car_day"`` (running
#: AR/CAR time-series columns), will be removed from the training dataset.
POST_EVENT_COLUMNS: frozenset[str] = frozenset(
    {
        # ---- Cumulative Abnormal Return ----
        "car",
        "final_car",
        "avg_car",
        # ---- Daily Abnormal Returns ----
        "ar",
        "avg_ar",
        "max_ar",
        "min_ar",
        # ---- Peak day offsets (derived from post-event series) ----
        "peak_car_day",
        "peak_ar_day",
        # ---- Statistical test outputs ----
        "t_statistic",
        "p_value",
        "significance_level",
        "significant_flag",
        "confidence_interval_lower",
        "confidence_interval_upper",
        "effect_size",
        # ---- Any computed label / score derived post-event ----
        "generated_label",
        "label_score",
        "decision_reason",
        "calculation_timestamp",
    }
)

#: Column name *prefixes* that always indicate post-event series data.
POST_EVENT_PREFIXES: tuple[str, ...] = (
    "ar_day_",   # daily abnormal return at offset t
    "car_day_",  # running CAR at offset t
)


@dataclass
class DatasetDescriptor:
    """
    Lightweight metadata descriptor attached to each saved dataset.

    Attributes
    ----------
    name : str
        Human-readable dataset name (``"training"`` or ``"research"``).
    path : str
        Absolute file path to the Parquet artefact.
    n_rows : int
        Number of rows in the dataset.
    n_features : int
        Number of feature columns (excludes metadata and targets).
    feature_columns : list[str]
        Ordered list of feature column names.
    target_columns : list[str]
        Target / label column names present in the dataset.
    metadata_columns : list[str]
        Non-feature, non-target identifier columns (e.g. ``record_id``).
    removed_columns : list[str]
        Columns removed relative to the full feature set (training only).
    source_mode : str
        Feature-selection mode this dataset was derived from.
    built_at : str
        ISO-8601 UTC timestamp when the dataset was built.
    notes : str
        Free-text annotation (e.g. ``"post-event columns stripped"``).
    """

    name: str
    path: str
    n_rows: int
    n_features: int
    feature_columns: list[str] = field(default_factory=list)
    target_columns: list[str] = field(default_factory=list)
    metadata_columns: list[str] = field(default_factory=list)
    removed_columns: list[str] = field(default_factory=list)
    source_mode: str = ""
    built_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "name": self.name,
            "path": self.path,
            "n_rows": self.n_rows,
            "n_features": self.n_features,
            "feature_columns": self.feature_columns,
            "target_columns": self.target_columns,
            "metadata_columns": self.metadata_columns,
            "removed_columns": self.removed_columns,
            "source_mode": self.source_mode,
            "built_at": self.built_at,
            "notes": self.notes,
        }
