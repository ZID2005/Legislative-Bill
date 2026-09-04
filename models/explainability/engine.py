"""
models/explainability/engine.py
=================================
ExplainabilityEngine — Task 6.3.

Generates global and local SHAP-based explanations for every trained model
without retraining.  Loads serialised artefacts from ``models/`` and persists
all explanation outputs to ``explainability/``.

Explanation types
-----------------
Global (per target × model_type):
  1. SHAP global feature importance     — mean |SHAP| per feature
  2. SHAP summary plot                  — beeswarm / dot plot
  3. SHAP bar plot                      — horizontal bar chart
  4. SHAP dependence plots              — scatter for top-10 features
  5. Feature importance CSV             — sorted table

Global (cross-model):
  5. Feature importance comparison      — grouped bar chart (top-20)
  6. Model comparison JSON              — side-by-side ranking

Local (per selected sample set):
  • Top correctly predicted samples     — y_pred == y_true AND prob ≥ 0.8
  • Misclassified samples               — y_pred != y_true
  • High-confidence predictions         — max(prob) ≥ 0.9

SHAP explainer selection
------------------------
LightGBM, XGBoost, Random Forest → ``shap.TreeExplainer`` (exact, fast).
Any model that TreeExplainer cannot handle → ``shap.KernelExplainer``
with a small background sample (50 rows) as fallback.

References
----------
Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting
model predictions. *NeurIPS*, 30.
"""

from __future__ import annotations

import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from config.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional SHAP import — graceful degradation
# ---------------------------------------------------------------------------

try:
    import shap as _shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    logger.warning(
        "shap is not installed. SHAP explanations will be unavailable. "
        "Install with: pip install shap"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TARGET_COLUMN_MAP: dict[str, str] = {
    "direction": "direction",
    "market_moving": "market_moving",
    "impact_strength": "impact_strength",
    "confidence": "confidence_label",
}

# Maximum background samples for KernelExplainer fallback
_KERNEL_BACKGROUND_SIZE = 50

# Maximum samples for SHAP value computation (performance guard)
_MAX_SHAP_SAMPLES = 500

# Local explanation thresholds
_CORRECT_PROB_THRESHOLD = 0.8
_HIGH_CONF_PROB_THRESHOLD = 0.9
_MAX_LOCAL_SAMPLES = 10


class ExplainabilityEngine:
    """
    Orchestrates SHAP computation, visualization, and persistence.

    Parameters
    ----------
    model_repo : ModelRepository, optional
        Source of trained model artefacts.  Defaults to a fresh
        ``ModelRepository()``.
    expl_repo : ExplainabilityRepository, optional
        Destination for explanation outputs.  Defaults to a fresh
        ``ExplainabilityRepository()``.
    dataset_builder : DatasetBuilder, optional
        Provides the training dataset for SHAP background samples.
    mode : str, optional
        Feature-selection mode.  Defaults to ``settings.ML_DEFAULT_MODE``.
    top_n_features : int, optional
        Number of features to display in summary / bar plots (default: 20).
    top_n_dependence : int, optional
        Number of features for dependence plots (default: 10).
    """

    def __init__(
        self,
        model_repo: Optional[Any] = None,
        expl_repo: Optional[Any] = None,
        dataset_builder: Optional[Any] = None,
        mode: Optional[str] = None,
        top_n_features: int = 20,
        top_n_dependence: int = 10,
    ) -> None:
        # All heavy project imports are lazy — done here, not at module level
        from config.settings import settings
        from storage.explainability_repository import ExplainabilityRepository
        from storage.model_repository import ModelRepository

        self._model_repo = model_repo or ModelRepository()
        self._expl_repo = expl_repo or ExplainabilityRepository()
        self._mode: str = mode or settings.ML_DEFAULT_MODE
        self._top_n = top_n_features
        self._top_dep = top_n_dependence

        # DatasetBuilder is imported lazily here too
        if dataset_builder is not None:
            self._builder = dataset_builder
        else:
            from models.training.dataset_builder import DatasetBuilder
            self._builder = DatasetBuilder()

        from models.explainability.visualizer import ExplainabilityVisualizer
        self._viz = ExplainabilityVisualizer(
            repo=self._expl_repo,
            top_n_features=top_n_features,
            top_n_dependence=top_n_dependence,
        )


    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explain_all(
        self,
        target_filter: Optional[str] = None,
        model_filter: Optional[str] = None,
        rebuild_dataset: bool = False,
    ) -> dict[str, Any]:
        """
        Run the full explainability pipeline for all (target × model_type).

        Parameters
        ----------
        target_filter : str, optional
            If set, restrict to a single target
            (e.g. ``"direction"``).
        model_filter : str, optional
            If set, restrict to a single model type
            (e.g. ``"lgbm"``).
        rebuild_dataset : bool
            Force rebuild of the training dataset before running.

        Returns
        -------
        dict
            Nested ``{target: {model_type: explanation_result}}``.
        """
        if not HAS_SHAP:
            raise RuntimeError(
                "shap is required for explainability. "
                "Install with: pip install shap"
            )

        logger.info(
            "=== ExplainabilityEngine.explain_all | mode=%s ===", self._mode
        )

        # Lazy import of valid sets
        from storage.model_repository import VALID_TARGETS, VALID_MODEL_TYPES

        # 1. Load training data
        df_train, _, _, _ = self._builder.build(mode=self._mode, rebuild=rebuild_dataset)
        if df_train.empty:
            raise ValueError(
                f"Training dataset is empty for mode='{self._mode}'. "
                "Run feature selection and training first."
            )

        # 2. Determine targets and models to process
        targets = [target_filter] if target_filter else sorted(VALID_TARGETS)
        model_types = [model_filter] if model_filter else sorted(VALID_MODEL_TYPES)

        all_results: dict[str, dict[str, Any]] = {}
        # Accumulate data for cross-model comparison
        comparison_data: dict[str, dict[str, dict[str, float]]] = {}

        for target in targets:
            target_col = TARGET_COLUMN_MAP.get(target)
            if target_col is None or target_col not in df_train.columns:
                logger.warning(
                    "Target column '%s' not found in dataset — skipping '%s'.",
                    target_col, target,
                )
                continue

            all_results[target] = {}
            comparison_data[target] = {}

            for model_type in model_types:
                if not self._model_repo.exists(target, model_type):
                    logger.info(
                        "Model not found: target=%s model=%s — skipping.",
                        target, model_type,
                    )
                    continue

                try:
                    result = self._explain_single(
                        df_train=df_train,
                        target=target,
                        target_col=target_col,
                        model_type=model_type,
                    )
                    all_results[target][model_type] = result

                    # Accumulate feature importance for cross-model comparison
                    if "feature_importance" in result:
                        fi_df: pd.DataFrame = result["feature_importance"]
                        if not fi_df.empty:
                            comparison_data[target][model_type] = dict(
                                zip(fi_df["feature"], fi_df["mean_abs_shap"])
                            )

                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Explainability failed: target=%s model=%s | %s",
                        target, model_type, exc, exc_info=True,
                    )

        # 3. Cross-model feature comparison
        if comparison_data:
            self._generate_comparison(comparison_data)

        # 4. Global summary (top-20 across all models)
        global_summary = self._build_global_summary(comparison_data)
        self._expl_repo.save_global_summary(global_summary)

        n_done = sum(len(v) for v in all_results.values())
        logger.info(
            "=== ExplainabilityEngine complete: %d (target, model) pairs explained ===",
            n_done,
        )
        return all_results

    # ------------------------------------------------------------------
    # Core private logic
    # ------------------------------------------------------------------

    def _explain_single(
        self,
        df_train: pd.DataFrame,
        target: str,
        target_col: str,
        model_type: str,
    ) -> dict[str, Any]:
        """
        Run full SHAP pipeline for one (target, model_type) combination.

        Steps
        -----
        1. Load model bundle + preprocessor + feature list.
        2. Align features and preprocess.
        3. Build SHAP explainer (TreeExplainer → KernelExplainer fallback).
        4. Compute SHAP values (capped at _MAX_SHAP_SAMPLES).
        5. Derive global feature importance (mean |SHAP|).
        6. Select local explanation samples.
        7. Persist SHAP values, feature importance, local explanations.
        8. Generate and save visualizations.
        9. Return result dict.
        """
        logger.info("--- Explaining: target=%s | model=%s ---", target, model_type)

        # --- 1. Load artefacts ---
        model_bundle, preprocessor, feature_list = self._model_repo.load(
            target, model_type
        )
        estimator = model_bundle["estimator"]
        label_encoder = model_bundle["label_encoder"]

        # --- 2. Align features and preprocess ---
        df_valid = df_train[df_train[target_col].notnull()].reset_index(drop=True)
        available_features = [f for f in feature_list if f in df_valid.columns]
        X_raw = df_valid[available_features].copy()
        y_raw = df_valid[target_col].astype(str).values

        # Preprocess
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            X_proc = preprocessor.transform(X_raw)

        # Encode labels
        y_encoded = label_encoder.transform(y_raw)

        # Cap sample size for SHAP performance
        n_samples = len(X_proc)
        if n_samples > _MAX_SHAP_SAMPLES:
            rng = np.random.default_rng(42)
            idx = rng.choice(n_samples, _MAX_SHAP_SAMPLES, replace=False)
            X_proc_shap = X_proc[idx]
            y_enc_shap = y_encoded[idx]
            y_raw_shap = y_raw[idx]
        else:
            X_proc_shap = X_proc
            y_enc_shap = y_encoded
            y_raw_shap = y_raw

        # --- 3. Build SHAP explainer ---
        import shap

        shap_values, explainer_type = self._build_shap_values(
            estimator=estimator,
            X_proc=X_proc_shap,
        )

        logger.info(
            "SHAP values computed | explainer=%s shape=%s",
            explainer_type,
            np.shape(shap_values),
        )

        # --- 4. Reduce to 2D for importance computation ---
        shap_values_2d = self._reduce_shap_to_2d(shap_values)

        # Ensure shape matches features
        n_feat = len(available_features)
        if shap_values_2d.shape[1] != n_feat:
            # Truncate or pad to available feature count
            shap_values_2d = shap_values_2d[:, :n_feat]

        # --- 5. Global feature importance ---
        mean_abs_shap = np.abs(shap_values_2d).mean(axis=0)
        feature_importance_df = pd.DataFrame({
            "feature": available_features,
            "mean_abs_shap": mean_abs_shap,
        }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

        # --- 6. Local explanations ---
        y_pred_enc = estimator.predict(X_proc_shap)
        y_pred_raw = label_encoder.inverse_transform(y_pred_enc)

        y_prob: Optional[np.ndarray] = None
        if hasattr(estimator, "predict_proba"):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    y_prob = estimator.predict_proba(X_proc_shap)
            except Exception as exc:
                logger.debug("predict_proba failed: %s", exc)

        local_explanations = self._build_local_explanations(
            shap_values_2d=shap_values_2d,
            feature_names=available_features,
            y_true=y_raw_shap,
            y_pred=y_pred_raw,
            y_prob=y_prob,
        )

        # --- 7. Persist core artefacts ---
        shap_df = pd.DataFrame(shap_values_2d, columns=available_features)
        self._expl_repo.save(
            target=target,
            model_type=model_type,
            shap_values_df=shap_df,
            feature_importance_df=feature_importance_df,
            local_explanations=local_explanations,
        )

        # --- 8. Visualizations ---
        self._viz.save_summary_plot(
            target=target,
            model_type=model_type,
            shap_values=shap_values_2d,
            feature_matrix=X_proc_shap if isinstance(X_proc_shap, np.ndarray) else np.array(X_proc_shap),
            feature_names=available_features,
        )
        self._viz.save_bar_plot(
            target=target,
            model_type=model_type,
            feature_importance_df=feature_importance_df,
        )
        self._viz.save_dependence_plots(
            target=target,
            model_type=model_type,
            shap_values=shap_values_2d,
            feature_matrix=X_proc_shap if isinstance(X_proc_shap, np.ndarray) else np.array(X_proc_shap),
            feature_names=available_features,
            feature_importance_df=feature_importance_df,
        )

        logger.info(
            "Explainability complete: target=%s model=%s | %d features",
            target, model_type, len(available_features),
        )

        return {
            "target": target,
            "model_type": model_type,
            "explainer_type": explainer_type,
            "n_samples": int(X_proc_shap.shape[0]),
            "n_features": len(available_features),
            "feature_importance": feature_importance_df,
            "local_explanations": local_explanations,
            "top_features": feature_importance_df["feature"].head(20).tolist(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # SHAP computation
    # ------------------------------------------------------------------

    def _build_shap_values(
        self,
        estimator: Any,
        X_proc: np.ndarray,
    ) -> tuple[Any, str]:
        """
        Build SHAP values using TreeExplainer (preferred) or
        KernelExplainer (fallback).

        Returns
        -------
        tuple
            ``(shap_values, explainer_type_str)``
        """
        import shap

        # --- TreeExplainer (fast, exact for tree-based models) ---
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                explainer = shap.TreeExplainer(estimator)
                shap_values = explainer.shap_values(X_proc)
            return shap_values, "TreeExplainer"
        except Exception as tree_exc:
            logger.debug(
                "TreeExplainer failed (%s). Trying KernelExplainer.", tree_exc
            )

        # --- KernelExplainer fallback ---
        try:
            bg_size = min(_KERNEL_BACKGROUND_SIZE, X_proc.shape[0])
            rng = np.random.default_rng(42)
            bg_idx = rng.choice(X_proc.shape[0], bg_size, replace=False)
            background = shap.kmeans(X_proc[bg_idx], min(10, bg_size))

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                explainer = shap.KernelExplainer(
                    estimator.predict_proba
                    if hasattr(estimator, "predict_proba")
                    else estimator.predict,
                    background,
                )
                # Use a small subset for KernelExplainer (slow)
                n_kernel = min(100, X_proc.shape[0])
                shap_values = explainer.shap_values(X_proc[:n_kernel])
            return shap_values, "KernelExplainer"
        except Exception as kernel_exc:
            raise RuntimeError(
                f"Both TreeExplainer and KernelExplainer failed. "
                f"Tree error: {tree_exc}. Kernel error: {kernel_exc}"
            ) from kernel_exc

    @staticmethod
    def _reduce_shap_to_2d(shap_values: Any) -> np.ndarray:
        """
        Reduce SHAP output to 2-D (n_samples × n_features).

        Multiclass models may return a list of per-class arrays
        (shape: list of (n_samples, n_features)) or a 3-D array.
        We take the element-wise absolute mean across classes.
        """
        if isinstance(shap_values, list):
            # Binary (len=2) or multiclass (len=n_classes)
            stacked = np.stack([np.abs(sv) for sv in shap_values], axis=0)
            return stacked.mean(axis=0)

        arr = np.array(shap_values)
        if arr.ndim == 3:
            # (n_classes, n_samples, n_features) or (n_samples, n_features, n_classes)
            if arr.shape[0] < arr.shape[1]:
                # (n_classes, n_samples, n_features)
                return np.abs(arr).mean(axis=0)
            else:
                # (n_samples, n_features, n_classes)
                return np.abs(arr).mean(axis=2)

        return arr

    # ------------------------------------------------------------------
    # Local explanations
    # ------------------------------------------------------------------

    def _build_local_explanations(
        self,
        shap_values_2d: np.ndarray,
        feature_names: list[str],
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray],
    ) -> dict[str, Any]:
        """
        Build JSON-serialisable local explanation dicts for three sample groups.

        Groups
        ------
        correct          : correctly predicted samples with high confidence
        misclassified    : incorrectly predicted samples
        high_confidence  : any prediction with max prob ≥ threshold
        """
        max_probs = (
            np.max(y_prob, axis=1) if y_prob is not None
            else np.ones(len(y_true))
        )

        correct_mask = (y_pred == y_true) & (max_probs >= _CORRECT_PROB_THRESHOLD)
        misclassified_mask = y_pred != y_true
        high_conf_mask = max_probs >= _HIGH_CONF_PROB_THRESHOLD

        def _select_indices(mask: np.ndarray) -> list[int]:
            indices = np.where(mask)[0].tolist()
            return indices[:_MAX_LOCAL_SAMPLES]

        def _build_sample_records(indices: list[int]) -> list[dict[str, Any]]:
            records = []
            for idx in indices:
                row_shap = shap_values_2d[idx]
                top_shap = sorted(
                    zip(feature_names, row_shap.tolist()),
                    key=lambda x: abs(x[1]),
                    reverse=True,
                )[:10]
                record: dict[str, Any] = {
                    "sample_index": int(idx),
                    "true_label": str(y_true[idx]),
                    "predicted_label": str(y_pred[idx]),
                    "max_probability": float(max_probs[idx]),
                    "top_shap_features": [
                        {"feature": f, "shap_value": round(float(v), 6)}
                        for f, v in top_shap
                    ],
                }
                records.append(record)
            return records

        correct_idx = _select_indices(correct_mask)
        misclassified_idx = _select_indices(misclassified_mask)
        high_conf_idx = _select_indices(high_conf_mask)

        return {
            "correct": {
                "description": (
                    f"Correctly predicted samples with confidence ≥ "
                    f"{_CORRECT_PROB_THRESHOLD:.0%}"
                ),
                "n_samples": len(correct_idx),
                "samples": _build_sample_records(correct_idx),
            },
            "misclassified": {
                "description": "Incorrectly predicted samples",
                "n_samples": len(misclassified_idx),
                "samples": _build_sample_records(misclassified_idx),
            },
            "high_confidence": {
                "description": (
                    f"Predictions with max probability ≥ "
                    f"{_HIGH_CONF_PROB_THRESHOLD:.0%}"
                ),
                "n_samples": len(high_conf_idx),
                "samples": _build_sample_records(high_conf_idx),
            },
        }

    # ------------------------------------------------------------------
    # Cross-model comparison
    # ------------------------------------------------------------------

    def _generate_comparison(
        self,
        comparison_data: dict[str, dict[str, dict[str, float]]],
    ) -> None:
        """Persist model comparison JSON and feature_comparison.png."""
        # Build model comparison JSON: per target, per model → top-20 features
        comparison_json: dict[str, Any] = {}
        for target, models in comparison_data.items():
            comparison_json[target] = {}
            for model_type, fi in models.items():
                top20 = sorted(fi.items(), key=lambda x: x[1], reverse=True)[:20]
                comparison_json[target][model_type] = [
                    {"feature": f, "mean_abs_shap": round(v, 6)} for f, v in top20
                ]

        self._expl_repo.save_model_comparison(comparison_json)

        # Feature comparison plot
        out_path = self._expl_repo.root / "feature_comparison.png"
        self._viz.save_feature_comparison(
            comparison_data=comparison_data,
            out_path=out_path,
            top_n=20,
        )

    @staticmethod
    def _build_global_summary(
        comparison_data: dict[str, dict[str, dict[str, float]]],
        top_n: int = 20,
    ) -> dict[str, Any]:
        """
        Build the global_summary.json: top-N features aggregated across
        all targets and model types by maximum mean |SHAP|.
        """
        global_fi: dict[str, float] = {}

        for target, models in comparison_data.items():
            for model_type, fi in models.items():
                for feat, val in fi.items():
                    global_fi[feat] = max(global_fi.get(feat, 0.0), val)

        top_features = sorted(global_fi, key=global_fi.get, reverse=True)[:top_n]  # type: ignore[arg-type]

        return {
            "description": (
                f"Top-{top_n} most important features by maximum mean |SHAP value| "
                "across all targets and model types."
            ),
            "top_features": [
                {"rank": rank + 1, "feature": feat, "max_mean_abs_shap": round(global_fi[feat], 6)}
                for rank, feat in enumerate(top_features)
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
