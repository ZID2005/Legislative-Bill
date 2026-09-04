"""
models/training/trainer.py
===========================
ML Training Engine — Task 6.1.

Trains four independent classifiers to predict the market impact of newly
introduced legislative bills using chronological cross-validation only.

Targets
-------
1. ``direction``       — POSITIVE / NEUTRAL / NEGATIVE
2. ``market_moving``   — True / False
3. ``impact_strength`` — LOW / MEDIUM / HIGH / VERY_HIGH
4. ``confidence``      — LOW / MEDIUM / HIGH

Models (per target)
-------------------
* **Primary**   : LightGBM (``lgbm``)
* **Secondary** : XGBoost  (``xgboost``)
* **Baseline**  : Random Forest (``random_forest``)

Validation
----------
ONLY chronological validation is used:
  * ``sklearn.model_selection.TimeSeriesSplit``
  * Walk-forward windows respecting temporal ordering
  * **Never** random train/test splitting

Anti-Leakage Guarantee
-----------------------
The trainer receives a ``DatasetBuilder`` instance and explicitly calls
``build()`` which strips all post-event columns before training.
The ``DatasetBuilder`` guarantees the training dataset is clean.

References
----------
Bergstra, J. & Bengio, Y. (2012). Random Search for Hyper-Parameter
Optimization. JMLR, 13, 281–305.
"""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from config.logging_config import get_logger
from models.training.dataset_builder import DatasetBuilder
from schemas.training_report import FoldResult, TrainingReport
from storage.model_repository import ModelRepository

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional ML library imports — graceful degradation
# ---------------------------------------------------------------------------

try:
    from lightgbm import LGBMClassifier
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    logger.warning("lightgbm not installed. LightGBM classifier will be unavailable.")

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    logger.warning("xgboost not installed. XGBoost classifier will be unavailable.")

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder

# ---------------------------------------------------------------------------
# Target definitions
# ---------------------------------------------------------------------------

TARGETS: list[str] = ["direction", "market_moving", "impact_strength", "confidence"]

TARGET_COLUMN_MAP: dict[str, str] = {
    "direction": "direction",
    "market_moving": "market_moving",
    "impact_strength": "impact_strength",
    "confidence": "confidence_label",
}

# ---------------------------------------------------------------------------
# Hyperparameter search grids (kept deliberately compact per spec)
# ---------------------------------------------------------------------------

_LGBM_PARAM_GRID: dict[str, list] = {
    "classifier__n_estimators": [100, 300],
    "classifier__max_depth": [4, 7],
    "classifier__learning_rate": [0.05, 0.1],
    "classifier__num_leaves": [31, 63],
    "classifier__min_child_samples": [10, 20],
}

_XGBOOST_PARAM_GRID: dict[str, list] = {
    "classifier__n_estimators": [100, 300],
    "classifier__max_depth": [4, 6],
    "classifier__learning_rate": [0.05, 0.1],
    "classifier__subsample": [0.8, 1.0],
    "classifier__colsample_bytree": [0.8, 1.0],
}

_RF_PARAM_GRID: dict[str, list] = {
    "classifier__n_estimators": [100, 300],
    "classifier__max_depth": [None, 10],
    "classifier__min_samples_split": [2, 5],
    "classifier__min_samples_leaf": [1, 2],
}


# ---------------------------------------------------------------------------
# MLTrainer
# ---------------------------------------------------------------------------


class MLTrainer:
    """
    Orchestrates training of all (target × model_type) combinations.

    Parameters
    ----------
    dataset_builder : DatasetBuilder, optional
        Builds and provides the training dataset.
    model_repo : ModelRepository, optional
        Persists and loads trained model artefacts.
    n_splits : int, optional
        Number of TimeSeriesSplit folds.  Defaults to ``settings.ML_N_SPLITS``.
    random_seed : int, optional
        Random seed for reproducibility.  Defaults to ``settings.ML_RANDOM_SEED``.
    mode : str, optional
        Feature-selection mode to load.  Defaults to ``settings.ML_DEFAULT_MODE``.
    n_jobs : int, optional
        Parallelism for GridSearchCV. Defaults to ``-1`` (all cores).
    verbose : bool, optional
        If True, emit more detailed training progress logs.
    """

    def __init__(
        self,
        dataset_builder: Optional[DatasetBuilder] = None,
        model_repo: Optional[ModelRepository] = None,
        n_splits: Optional[int] = None,
        random_seed: Optional[int] = None,
        mode: Optional[str] = None,
        n_jobs: int = -1,
        verbose: bool = True,
    ) -> None:
        from config.settings import settings

        self._builder = dataset_builder or DatasetBuilder()
        self._repo = model_repo or ModelRepository()
        self._n_splits: int = n_splits if n_splits is not None else settings.ML_N_SPLITS
        self._seed: int = random_seed if random_seed is not None else settings.ML_RANDOM_SEED
        self._mode: str = mode or settings.ML_DEFAULT_MODE
        self._n_jobs = n_jobs
        self._verbose = verbose

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def train_all(
        self,
        rebuild_datasets: bool = False,
        skip_existing: bool = False,
    ) -> dict[str, dict[str, TrainingReport]]:
        """
        Train all four classifiers with all three model types.

        Parameters
        ----------
        rebuild_datasets : bool
            Force rebuild of training/research datasets even if they exist.
        skip_existing : bool
            If True, skip any (target, model_type) that already has a saved model.

        Returns
        -------
        dict
            Nested mapping ``{target: {model_type: TrainingReport}}``.
        """
        logger.info(
            "=== MLTrainer.train_all | mode=%s n_splits=%d seed=%d ===",
            self._mode, self._n_splits, self._seed,
        )

        # 1. Build datasets
        df_training, df_research, train_desc, _ = self._builder.build(
            mode=self._mode,
            rebuild=rebuild_datasets,
        )

        logger.info(
            "Training dataset: %d rows × %d cols | Research dataset: %d rows",
            len(df_training), len(df_training.columns), len(df_research),
        )

        # 2. Prepare features
        feature_cols = self._builder.get_feature_columns(df_training)
        if not feature_cols:
            raise ValueError(
                "No feature columns found in training dataset. "
                "Verify that feature selection has been run (Task 5.4)."
            )

        logger.info("Using %d feature columns for training.", len(feature_cols))

        # 3. Iterate targets × model_types
        all_reports: dict[str, dict[str, TrainingReport]] = {}

        for target in TARGETS:
            target_col = TARGET_COLUMN_MAP[target]
            all_reports[target] = {}

            if target_col not in df_training.columns:
                logger.warning(
                    "Target column '%s' not in training dataset — skipping target '%s'.",
                    target_col, target,
                )
                continue

            for model_type in ["lgbm", "xgboost", "random_forest"]:
                if skip_existing and self._repo.exists(target, model_type):
                    logger.info(
                        "Skipping existing model: target=%s model=%s",
                        target, model_type,
                    )
                    continue

                try:
                    report = self._train_single(
                        df=df_training,
                        feature_cols=feature_cols,
                        target=target,
                        target_col=target_col,
                        model_type=model_type,
                        dataset_path=train_desc.path,
                    )
                    all_reports[target][model_type] = report
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Failed to train target=%s model=%s: %s",
                        target, model_type, exc, exc_info=True,
                    )

        n_trained = sum(len(v) for v in all_reports.values())
        logger.info(
            "=== Training complete: %d models trained across %d targets ===",
            n_trained, len(all_reports),
        )
        return all_reports

    def train_target(
        self,
        target: str,
        model_type: str,
        rebuild_datasets: bool = False,
    ) -> TrainingReport:
        """
        Train a single (target, model_type) combination.

        Parameters
        ----------
        target : str
            One of ``direction``, ``market_moving``, ``impact_strength``,
            ``confidence``.
        model_type : str
            One of ``lgbm``, ``xgboost``, ``random_forest``.
        rebuild_datasets : bool
            Force dataset rebuild.

        Returns
        -------
        TrainingReport
        """
        df_training, _, train_desc, _ = self._builder.build(
            mode=self._mode, rebuild=rebuild_datasets
        )
        feature_cols = self._builder.get_feature_columns(df_training)
        target_col = TARGET_COLUMN_MAP[target]

        if target_col not in df_training.columns:
            raise ValueError(
                f"Target column '{target_col}' not found in training dataset."
            )

        return self._train_single(
            df=df_training,
            feature_cols=feature_cols,
            target=target,
            target_col=target_col,
            model_type=model_type,
            dataset_path=train_desc.path,
        )

    # ------------------------------------------------------------------
    # Core private training logic
    # ------------------------------------------------------------------

    def _train_single(
        self,
        df: pd.DataFrame,
        feature_cols: list[str],
        target: str,
        target_col: str,
        model_type: str,
        dataset_path: str,
    ) -> TrainingReport:
        """
        Train one (target, model_type) model with TimeSeriesSplit CV.

        Steps
        -----
        1. Extract X (features) and y (target labels).
        2. Encode categoricals; impute missing values.
        3. Encode labels with LabelEncoder.
        4. Run TimeSeriesSplit walk-forward validation.
        5. GridSearchCV on the last fold for hyperparameter selection.
        6. Refit final model on the full training dataset.
        7. Save all artefacts to ModelRepository.
        8. Return TrainingReport.
        """
        logger.info(
            "--- Training: target=%s | model=%s ---", target, model_type
        )

        # --- 1. Extract X, y ---
        X_raw, y_raw, valid_mask = self._extract_Xy(df, feature_cols, target_col)

        n_samples = len(X_raw)
        if n_samples < self._n_splits + 1:
            logger.warning(
                "Too few samples (%d) for %d-fold TimeSeriesSplit on target='%s'. "
                "Reducing to %d folds.",
                n_samples, self._n_splits, target, max(2, n_samples - 1),
            )
            n_splits = max(2, n_samples - 1)
        else:
            n_splits = self._n_splits

        # --- 2. Build preprocessor pipeline ---
        preprocessor = self._build_preprocessor(X_raw)
        X_proc = preprocessor.fit_transform(X_raw)

        # --- 3. Encode labels ---
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(y_raw.astype(str))

        class_distribution = {
            cls: int((y_raw.astype(str) == cls).sum())
            for cls in sorted(y_raw.astype(str).unique())
        }
        logger.info("Class distribution: %s", class_distribution)

        # --- 4. Introduce_date ordering for fold date ranges ---
        dates: Optional[pd.Series] = None
        if "introduction_date" in df.columns:
            dates = df.loc[valid_mask, "introduction_date"].reset_index(drop=True)

        # --- 5. TimeSeriesSplit walk-forward validation ---
        tscv = TimeSeriesSplit(n_splits=n_splits)
        fold_results: list[FoldResult] = []
        val_accuracies: list[float] = []
        val_f1_scores: list[float] = []
        train_accuracies: list[float] = []

        base_estimator = self._make_base_estimator(model_type)

        for fold_idx, (train_idx, val_idx) in enumerate(tscv.split(X_proc)):
            X_train_f, X_val_f = X_proc[train_idx], X_proc[val_idx]
            y_train_f, y_val_f = y[train_idx], y[val_idx]

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                base_estimator.fit(X_train_f, y_train_f)

            y_train_pred = base_estimator.predict(X_train_f)
            y_val_pred = base_estimator.predict(X_val_f)

            train_acc = float(accuracy_score(y_train_f, y_train_pred))
            val_acc = float(accuracy_score(y_val_f, y_val_pred))
            val_f1 = float(
                f1_score(y_val_f, y_val_pred, average="macro", zero_division=0)
            )

            train_accuracies.append(train_acc)
            val_accuracies.append(val_acc)
            val_f1_scores.append(val_f1)

            # Date ranges for this fold
            train_start = train_end = val_start = val_end = None
            if dates is not None:
                try:
                    td = pd.to_datetime(dates.iloc[train_idx], errors="coerce")
                    vd = pd.to_datetime(dates.iloc[val_idx], errors="coerce")
                    train_start = str(td.min())
                    train_end = str(td.max())
                    val_start = str(vd.min())
                    val_end = str(vd.max())
                except Exception:
                    pass

            fold_results.append(
                FoldResult(
                    fold_index=fold_idx,
                    train_samples=len(train_idx),
                    val_samples=len(val_idx),
                    train_accuracy=round(train_acc, 4),
                    val_accuracy=round(val_acc, 4),
                    val_f1_macro=round(val_f1, 4),
                    train_start_date=train_start,
                    train_end_date=train_end,
                    val_start_date=val_start,
                    val_end_date=val_end,
                )
            )

            if self._verbose:
                logger.info(
                    "  Fold %d/%d | train=%d val=%d | "
                    "train_acc=%.4f val_acc=%.4f val_f1=%.4f",
                    fold_idx + 1, n_splits,
                    len(train_idx), len(val_idx),
                    train_acc, val_acc, val_f1,
                )

        mean_train_acc = float(np.mean(train_accuracies))
        mean_val_acc = float(np.mean(val_accuracies))
        mean_val_f1 = float(np.mean(val_f1_scores))

        logger.info(
            "CV summary | mean_train_acc=%.4f mean_val_acc=%.4f mean_val_f1=%.4f",
            mean_train_acc, mean_val_acc, mean_val_f1,
        )

        # --- 6. GridSearchCV on the full dataset for best hyperparameters ---
        logger.info("Running GridSearchCV for target=%s model=%s ...", target, model_type)
        best_params = self._run_grid_search(
            X_proc=X_proc,
            y=y,
            model_type=model_type,
            n_splits=n_splits,
        )
        logger.info("Best hyperparameters: %s", best_params)

        # --- 7. Final refit with best hyperparameters on full training data ---
        final_model = self._make_base_estimator(model_type, params=best_params)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            final_model.fit(X_proc, y)

        # --- 8. Persist artefacts ---
        from config.settings import settings

        model_dir = settings.ML_MODELS_DIR / target / model_type
        model_dir.mkdir(parents=True, exist_ok=True)

        # Wrap model + label_encoder together for predict convenience
        model_bundle = {
            "estimator": final_model,
            "label_encoder": label_encoder,
        }

        # Build the report first so we can embed paths
        report = TrainingReport(
            target=target,
            model_type=model_type,
            feature_selection_mode=self._mode,
            feature_count=len(feature_cols),
            feature_list=feature_cols,
            training_samples=n_samples,
            validation_samples=int(np.sum([f.val_samples for f in fold_results])),
            class_distribution=class_distribution,
            best_hyperparameters=best_params,
            mean_train_accuracy=round(mean_train_acc, 4),
            mean_val_accuracy=round(mean_val_acc, 4),
            mean_val_f1_macro=round(mean_val_f1, 4),
            n_splits=n_splits,
            folds=fold_results,
            trained_at=datetime.now(timezone.utc).isoformat(),
            dataset_path=dataset_path,
        )

        saved_paths = self._repo.save(
            target=target,
            model_type=model_type,
            model=model_bundle,
            preprocessor=preprocessor,
            feature_list=feature_cols,
            report=report,
        )

        # Back-fill paths into the report
        report.model_path = str(saved_paths.get("model", ""))
        report.preprocessor_path = str(saved_paths.get("preprocessor", ""))
        report.features_path = str(saved_paths.get("features", ""))
        report.metadata_path = str(saved_paths.get("metadata", ""))

        # Re-save report with paths filled in
        if "report" in saved_paths:
            report_path = saved_paths["report"]
        else:
            from storage.model_repository import ModelRepository
            report_path = (
                settings.ML_MODELS_DIR / target / model_type / "training_report.json"
            )
        with report_path.open("w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        report.metadata_path = str(report_path)

        logger.info(
            "Saved: target=%s model=%s | "
            "val_acc=%.4f val_f1=%.4f",
            target, model_type, mean_val_acc, mean_val_f1,
        )
        return report

    # ------------------------------------------------------------------
    # Preprocessing
    # ------------------------------------------------------------------

    def _extract_Xy(
        self,
        df: pd.DataFrame,
        feature_cols: list[str],
        target_col: str,
    ) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
        """
        Extract feature matrix and target vector, dropping rows with null targets.

        Returns
        -------
        tuple
            ``(X_raw, y_raw, valid_mask)``
        """
        valid_mask = df[target_col].notnull()
        df_valid = df[valid_mask].reset_index(drop=True)

        # Keep only feature columns that are in the dataframe
        available_features = [c for c in feature_cols if c in df_valid.columns]
        missing = set(feature_cols) - set(available_features)
        if missing:
            logger.warning("Feature columns missing from data: %s", sorted(missing))

        X_raw = df_valid[available_features].copy()
        y_raw = df_valid[target_col].copy()
        return X_raw, y_raw, valid_mask

    @staticmethod
    def _build_preprocessor(X: pd.DataFrame) -> Any:
        """
        Build a column-level preprocessor that:
          * Imputes numeric NaN with column medians
          * Encodes categorical columns as ordinal integers

        Returns a fitted-to-nothing Pipeline that will be fit inside training.
        """
        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import OrdinalEncoder

        numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = X.select_dtypes(
            include=["object", "category", "bool"]
        ).columns.tolist()

        transformers: list = []

        if numeric_cols:
            transformers.append(
                (
                    "num",
                    SimpleImputer(strategy="median"),
                    numeric_cols,
                )
            )

        if categorical_cols:
            transformers.append(
                (
                    "cat",
                    Pipeline(
                        steps=[
                            ("impute", SimpleImputer(strategy="constant", fill_value="missing")),
                            ("encode", OrdinalEncoder(
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                            )),
                        ]
                    ),
                    categorical_cols,
                )
            )

        if not transformers:
            # Fallback: identity transform — passthrough all columns
            from sklearn.preprocessing import FunctionTransformer
            return FunctionTransformer(lambda x: x.values if hasattr(x, "values") else x)

        ct = ColumnTransformer(transformers=transformers, remainder="drop")
        return ct

    # ------------------------------------------------------------------
    # Estimator factory
    # ------------------------------------------------------------------

    def _make_base_estimator(
        self, model_type: str, params: Optional[dict[str, Any]] = None
    ) -> Any:
        """
        Construct an unfitted estimator for the given model_type.

        Parameters
        ----------
        model_type : str
        params : dict, optional
            Hyperparameter overrides.  Keys should be bare parameter names
            (without the ``"classifier__"`` GridSearchCV prefix).
        """
        p = params or {}

        if model_type == "lgbm":
            if not HAS_LIGHTGBM:
                raise RuntimeError(
                    "lightgbm is not installed. "
                    "Install with: pip install lightgbm"
                )
            return LGBMClassifier(
                n_estimators=p.get("n_estimators", 200),
                max_depth=p.get("max_depth", 6),
                learning_rate=p.get("learning_rate", 0.05),
                num_leaves=p.get("num_leaves", 31),
                min_child_samples=p.get("min_child_samples", 10),
                random_state=self._seed,
                verbose=-1,
                n_jobs=1,
            )

        if model_type == "xgboost":
            if not HAS_XGBOOST:
                raise RuntimeError(
                    "xgboost is not installed. "
                    "Install with: pip install xgboost"
                )
            return XGBClassifier(
                n_estimators=p.get("n_estimators", 200),
                max_depth=p.get("max_depth", 5),
                learning_rate=p.get("learning_rate", 0.05),
                subsample=p.get("subsample", 0.8),
                colsample_bytree=p.get("colsample_bytree", 0.8),
                random_state=self._seed,
                eval_metric="mlogloss",
                verbosity=0,
                n_jobs=1,
            )

        if model_type == "random_forest":
            return RandomForestClassifier(
                n_estimators=p.get("n_estimators", 200),
                max_depth=p.get("max_depth", None),
                min_samples_split=p.get("min_samples_split", 2),
                min_samples_leaf=p.get("min_samples_leaf", 1),
                random_state=self._seed,
                n_jobs=-1,
            )

        raise ValueError(f"Unknown model_type: '{model_type}'")

    # ------------------------------------------------------------------
    # GridSearchCV
    # ------------------------------------------------------------------

    def _run_grid_search(
        self,
        X_proc: np.ndarray,
        y: np.ndarray,
        model_type: str,
        n_splits: int,
    ) -> dict[str, Any]:
        """
        Run GridSearchCV with TimeSeriesSplit and return best *bare* parameters.

        The GridSearchCV pipeline wraps the base estimator under the key
        ``"classifier"`` so param_grid keys use the ``"classifier__"`` prefix.
        After fitting, the prefix is stripped before returning.
        """
        try:
            base = self._make_base_estimator(model_type)
            pipe = Pipeline(steps=[("classifier", base)])

            if model_type == "lgbm":
                param_grid = _LGBM_PARAM_GRID
            elif model_type == "xgboost":
                param_grid = _XGBOOST_PARAM_GRID
            else:
                param_grid = _RF_PARAM_GRID

            tscv = TimeSeriesSplit(n_splits=min(3, n_splits))

            gs = GridSearchCV(
                estimator=pipe,
                param_grid=param_grid,
                cv=tscv,
                scoring="f1_macro",
                n_jobs=self._n_jobs,
                refit=False,
                error_score=0.0,
            )

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gs.fit(X_proc, y)

            # Strip "classifier__" prefix
            best_params: dict[str, Any] = {
                k.replace("classifier__", ""): v
                for k, v in gs.best_params_.items()
            }
            return best_params

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "GridSearchCV failed for model_type=%s: %s. "
                "Using default hyperparameters.",
                model_type, exc,
            )
            return {}

    # ------------------------------------------------------------------
    # Prediction helper (for pipeline testing)
    # ------------------------------------------------------------------

    @staticmethod
    def predict(
        model_bundle: dict[str, Any],
        preprocessor: Any,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """
        Run inference with a loaded model bundle.

        Parameters
        ----------
        model_bundle : dict
            ``{"estimator": <model>, "label_encoder": <LabelEncoder>}``
        preprocessor : Any
            Fitted column transformer.
        X : pd.DataFrame
            Raw feature DataFrame (pre-preprocessing).

        Returns
        -------
        np.ndarray
            Decoded string class labels.
        """
        estimator = model_bundle["estimator"]
        label_encoder = model_bundle["label_encoder"]
        X_proc = preprocessor.transform(X)
        y_pred_enc = estimator.predict(X_proc)
        return label_encoder.inverse_transform(y_pred_enc)
