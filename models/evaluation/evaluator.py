"""
models/evaluation/evaluator.py
===============================
ModelEvaluator — orchestrator for ML evaluation, comparison, and error analysis (Task 6.2).

Loads all trained models, runs predictions on the training dataset,
computes individual/class metrics, ranks algorithms, performs error analysis,
and persists all outputs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from config.logging_config import get_logger
from models.evaluation.metrics import compute_metrics
from models.training.dataset_builder import DatasetBuilder
from storage.evaluation_repository import EvaluationRepository
from storage.model_repository import ModelRepository, VALID_MODEL_TYPES, VALID_TARGETS

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

logger = get_logger(__name__)

TARGET_COLUMN_MAP: dict[str, str] = {
    "direction": "direction",
    "market_moving": "market_moving",
    "impact_strength": "impact_strength",
    "confidence": "confidence_label",
}


class ModelEvaluator:
    """
    Evaluates every trained model, compares performance, and performs error analysis.

    Parameters
    ----------
    eval_repo : EvaluationRepository, optional
        Repository to save evaluation reports.
    model_repo : ModelRepository, optional
        Repository to load models from.
    dataset_builder : DatasetBuilder, optional
        Builder to load datasets from.
    mode : str, optional
        Feature-selection mode to evaluate. Defaults to "structured".
    """

    def __init__(
        self,
        eval_repo: Optional[EvaluationRepository] = None,
        model_repo: Optional[ModelRepository] = None,
        dataset_builder: Optional[DatasetBuilder] = None,
        mode: str = "structured",
    ) -> None:
        self._eval_repo = eval_repo or EvaluationRepository()
        self._model_repo = model_repo or ModelRepository()
        self._builder = dataset_builder or DatasetBuilder()
        self._mode = mode

    # ------------------------------------------------------------------
    # Public Evaluation Interface
    # ------------------------------------------------------------------

    def evaluate_all(self, rebuild_dataset: bool = False) -> dict[str, Any]:
        """
        Execute the full evaluation pipeline.

        1. Load training dataset (preventing leakage).
        2. Evaluate every available model.
        3. Rank algorithms (Best vs. Worst, Averages).
        4. Analyze errors (Imbalances, Hard classes, Confidence).
        5. Persist reports.
        """
        logger.info("Starting model evaluation pipeline | mode=%s", self._mode)

        # 1. Load data
        df_train, _, _, _ = self._builder.build(mode=self._mode, rebuild=rebuild_dataset)
        if df_train.empty:
            raise ValueError(f"No training data found for mode '{self._mode}'.")

        # 2. Iterate targets × model_types to collect predictions & metrics
        metrics_dict: dict[str, dict[str, Any]] = {}
        classification_reports: dict[str, dict[str, Any]] = {}
        cm_records: list[dict[str, Any]] = []

        for target in sorted(VALID_TARGETS):
            target_col = TARGET_COLUMN_MAP[target]
            if target_col not in df_train.columns:
                logger.warning("Target column '%s' missing from dataset. Skipping.", target_col)
                continue

            # Drop missing target values
            df_valid = df_train[df_train[target_col].notnull()].reset_index(drop=True)
            if len(df_valid) == 0:
                logger.warning("No valid samples for target '%s'. Skipping.", target)
                continue

            metrics_dict[target] = {}
            classification_reports[target] = {}

            # Convert target labels to string
            y_raw = df_valid[target_col].astype(str)

            for model_type in sorted(VALID_MODEL_TYPES):
                if not self._model_repo.exists(target, model_type):
                    logger.debug("Model target=%s type=%s not found. Skipping.", target, model_type)
                    continue

                try:
                    logger.info("Evaluating target=%s model=%s ...", target, model_type)

                    # Load model, preprocessor, and feature list
                    model_bundle, preprocessor, feature_list = self._model_repo.load(target, model_type)

                    # Extract model components
                    estimator = model_bundle["estimator"]
                    label_encoder: LabelEncoder = model_bundle["label_encoder"]
                    classes = label_encoder.classes_

                    # Map raw y to encoded integer targets
                    y_true = label_encoder.transform(y_raw)

                    # Align features
                    X = df_valid[feature_list]

                    # Process and predict
                    X_proc = preprocessor.transform(X)
                    y_pred = estimator.predict(X_proc)

                    # Get probability distributions if supported
                    y_prob = None
                    if hasattr(estimator, "predict_proba"):
                        try:
                            y_prob = estimator.predict_proba(X_proc)
                        except Exception as exc:
                            logger.debug("Failed to call predict_proba: %s", exc)

                    # A. Compute metrics
                    model_metrics = compute_metrics(y_true, y_pred, y_prob, classes)
                    metrics_dict[target][model_type] = model_metrics

                    # B. Generate standard classification report
                    sk_report = classification_report(
                        y_true,
                        y_pred,
                        target_names=[str(c) for c in classes],
                        output_dict=True,
                        zero_division=0,
                    )

                    # C. Generate confusion matrix
                    cm = confusion_matrix(y_true, y_pred, labels=np.arange(len(classes)))
                    for r_idx, true_cls in enumerate(classes):
                        for c_idx, pred_cls in enumerate(classes):
                            cm_records.append(
                                {
                                    "target": target,
                                    "model_type": model_type,
                                    "true_label": str(true_cls),
                                    "predicted_label": str(pred_cls),
                                    "count": int(cm[r_idx, c_idx]),
                                }
                            )

                    # D. Perform Error Analysis
                    error_analysis = self._analyze_errors(
                        y_true=y_true,
                        y_pred=y_pred,
                        y_prob=y_prob,
                        classes=classes,
                        sk_report=sk_report,
                        cm=cm,
                    )

                    classification_reports[target][model_type] = {
                        "classification_report": sk_report,
                        "error_analysis": error_analysis,
                    }

                except Exception as exc:
                    logger.error(
                        "Failed to evaluate target=%s model=%s: %s",
                        target,
                        model_type,
                        exc,
                        exc_info=True,
                    )

        # 3. Model Comparison & Rankings
        comparison_report = self._compare_models(metrics_dict)

        # 4. Save results
        self._eval_repo.save_metrics(metrics_dict)
        self._eval_repo.save_classification_report(classification_reports)
        self._eval_repo.save_comparison_report(comparison_report)

        cm_df = pd.DataFrame(cm_records)
        self._eval_repo.save_confusion_matrix(cm_df)

        logger.info("Model evaluation pipeline completed successfully.")
        return {
            "metrics": metrics_dict,
            "comparison": comparison_report,
            "classification_reports": classification_reports,
            "confusion_matrix": cm_df,
        }

    # ------------------------------------------------------------------
    # Error Analysis Logic
    # ------------------------------------------------------------------

    def _analyze_errors(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Optional[np.ndarray],
        classes: np.ndarray,
        sk_report: dict[str, Any],
        cm: np.ndarray,
    ) -> dict[str, Any]:
        """
        Identify misclassifications, class imbalances, hard classes,
        and confidence distributions.
        """
        # Class imbalance calculation
        total_samples = len(y_true)
        class_imbalance = {}
        for idx, cls in enumerate(classes):
            count = int((y_true == idx).sum())
            class_imbalance[str(cls)] = {
                "count": count,
                "percentage": float(count / total_samples) if total_samples > 0 else 0.0,
            }

        # Hard classes identification (lowest F1 or recall)
        hard_classes = []
        for cls in classes:
            cls_str = str(cls)
            if cls_str in sk_report:
                f1 = sk_report[cls_str].get("f1-score", 1.0)
                recall = sk_report[cls_str].get("recall", 1.0)
                # Flag as hard if F1 < 0.6 or Recall < 0.6
                if f1 < 0.6 or recall < 0.6:
                    hard_classes.append(
                        {
                            "class": cls_str,
                            "f1_score": float(f1),
                            "recall": float(recall),
                        }
                    )
        # Sort hard classes by F1 ascending
        hard_classes = sorted(hard_classes, key=lambda x: x["f1_score"])

        # Most common misclassifications (top 3 pairs)
        misclassifications = []
        for r_idx, true_cls in enumerate(classes):
            for c_idx, pred_cls in enumerate(classes):
                if r_idx != c_idx:  # off-diagonal
                    count = int(cm[r_idx, c_idx])
                    if count > 0:
                        misclassifications.append(
                            {
                                "true_label": str(true_cls),
                                "predicted_label": str(pred_cls),
                                "count": count,
                            }
                        )
        # Sort by count descending, keep top 3
        misclassifications = sorted(misclassifications, key=lambda x: x["count"], reverse=True)[:3]

        # Prediction confidence distribution
        confidence_stats = {}
        if y_prob is not None:
            # Maximum probability assigned to predicted label
            max_probs = np.max(y_prob, axis=1)
            confidence_stats = {
                "mean": float(np.mean(max_probs)),
                "std": float(np.std(max_probs)),
                "min": float(np.min(max_probs)),
                "max": float(np.max(max_probs)),
                "p25": float(np.percentile(max_probs, 25)),
                "median": float(np.percentile(max_probs, 50)),
                "p75": float(np.percentile(max_probs, 75)),
            }

        return {
            "class_imbalance": class_imbalance,
            "hard_classes": hard_classes,
            "most_common_misclassifications": misclassifications,
            "prediction_confidence_distribution": confidence_stats,
        }

    # ------------------------------------------------------------------
    # Comparative Ranking Logic
    # ------------------------------------------------------------------

    def _compare_models(self, metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Rank algorithms per target. Identify Best, Worst, and Averages."""
        comparison: dict[str, Any] = {}

        for target, models in metrics.items():
            if not models:
                continue

            comparison[target] = {}

            # Rank by macro F1 descending
            ranked = sorted(
                models.items(),
                key=lambda x: x[1].get("f1_macro", 0.0) or 0.0,
                reverse=True,
            )

            # Best model
            best_model_type, best_metrics = ranked[0]
            comparison[target]["best_model"] = {
                "model_type": best_model_type,
                "accuracy": best_metrics.get("accuracy"),
                "f1_macro": best_metrics.get("f1_macro"),
            }

            # Worst model
            worst_model_type, worst_metrics = ranked[-1]
            comparison[target]["worst_model"] = {
                "model_type": worst_model_type,
                "accuracy": worst_metrics.get("accuracy"),
                "f1_macro": worst_metrics.get("f1_macro"),
            }

            # Average performance across all algorithms for this target
            acc_list = [m.get("accuracy", 0.0) for m in models.values()]
            f1_list = [m.get("f1_macro", 0.0) for m in models.values()]
            logloss_list = [
                m.get("log_loss")
                for m in models.values()
                if m.get("log_loss") is not None
            ]

            comparison[target]["average_performance"] = {
                "accuracy": float(np.mean(acc_list)) if acc_list else 0.0,
                "f1_macro": float(np.mean(f1_list)) if f1_list else 0.0,
                "log_loss": float(np.mean(logloss_list)) if logloss_list else None,
            }

            # Algorithm rankings
            rankings = []
            for rank, (model_type, m_val) in enumerate(ranked, start=1):
                rankings.append(
                    {
                        "rank": rank,
                        "model_type": model_type,
                        "accuracy": m_val.get("accuracy"),
                        "f1_macro": m_val.get("f1_macro"),
                        "log_loss": m_val.get("log_loss"),
                    }
                )
            comparison[target]["rankings"] = rankings

        return comparison
