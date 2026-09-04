"""
schemas/training_report.py
==========================
Schema for the ML training report produced by Task 6.1.

Each ``TrainingReport`` captures all metadata required to:
  * audit the training run
  * reproduce the trained model
  * compare models across targets and algorithms
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class FoldResult:
    """
    Metrics for a single chronological cross-validation fold.

    Attributes
    ----------
    fold_index : int
        Zero-based fold index (matches TimeSeriesSplit ordering).
    train_samples : int
        Number of training rows in this fold.
    val_samples : int
        Number of validation rows in this fold.
    train_accuracy : float
        Accuracy on the training split.
    val_accuracy : float
        Accuracy on the validation split.
    val_f1_macro : float
        Macro-averaged F1 on the validation split.
    train_start_date : str or None
        Earliest ``introduction_date`` in the training split (ISO-8601).
    train_end_date : str or None
        Latest ``introduction_date`` in the training split (ISO-8601).
    val_start_date : str or None
        Earliest ``introduction_date`` in the validation split (ISO-8601).
    val_end_date : str or None
        Latest ``introduction_date`` in the validation split (ISO-8601).
    """

    fold_index: int
    train_samples: int
    val_samples: int
    train_accuracy: float
    val_accuracy: float
    val_f1_macro: float
    train_start_date: Optional[str] = None
    train_end_date: Optional[str] = None
    val_start_date: Optional[str] = None
    val_end_date: Optional[str] = None


@dataclass
class TrainingReport:
    """
    Complete training metadata for one (target, model_type) combination.

    Attributes
    ----------
    target : str
        Label target name — one of ``direction``, ``market_moving``,
        ``impact_strength``, ``confidence``.
    model_type : str
        Algorithm name — ``lgbm``, ``xgboost``, or ``random_forest``.
    feature_selection_mode : str
        The fusion/selection mode used (e.g. ``"structured"``).
    feature_count : int
        Number of input features used at training time.
    feature_list : list[str]
        Ordered list of feature column names.
    training_samples : int
        Total rows in the training split (last fold or full refit).
    validation_samples : int
        Total rows across all validation folds.
    class_distribution : dict[str, int]
        Counts per class label in the full training dataset.
    best_hyperparameters : dict[str, Any]
        Hyperparameters selected by GridSearchCV.
    mean_train_accuracy : float
        Mean training accuracy across all CV folds.
    mean_val_accuracy : float
        Mean validation accuracy across all CV folds.
    mean_val_f1_macro : float
        Mean macro-F1 across all CV folds.
    n_splits : int
        Number of TimeSeriesSplit folds used.
    folds : list[FoldResult]
        Per-fold breakdown of training/validation metrics.
    trained_at : str
        ISO-8601 UTC timestamp when training completed.
    dataset_path : str
        Path to the training dataset parquet file used.
    model_path : str
        Path where the trained model artefact was saved.
    preprocessor_path : str
        Path where the fitted preprocessor was saved.
    features_path : str
        Path where the feature list JSON was saved.
    metadata_path : str
        Path where this report was saved as JSON.
    notes : str
        Free-text notes (e.g. fallback decisions during training).
    """

    target: str
    model_type: str
    feature_selection_mode: str
    feature_count: int
    feature_list: list[str]
    training_samples: int
    validation_samples: int
    class_distribution: dict[str, int]
    best_hyperparameters: dict[str, Any]
    mean_train_accuracy: float
    mean_val_accuracy: float
    mean_val_f1_macro: float
    n_splits: int
    folds: list[FoldResult] = field(default_factory=list)
    trained_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    dataset_path: str = ""
    model_path: str = ""
    preprocessor_path: str = ""
    features_path: str = ""
    metadata_path: str = ""
    notes: str = ""

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dictionary (JSON-safe)."""
        raw = asdict(self)
        return raw

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainingReport":
        """Reconstruct from a plain dictionary (loaded from JSON)."""
        folds_raw = data.pop("folds", [])
        folds = [FoldResult(**f) for f in folds_raw]
        return cls(folds=folds, **data)
