"""
prediction/engine.py
====================
Master orchestrator for the Final Prediction & Decision Engine (Task 7.1).

Coordinates:
1. Feature dataset ingestion (from FeatureSelectionRepository or DatasetBuilder).
2. Multi-target model selection via ModelSelector (backed by Task 6.2 evaluation).
3. Pre-inference integrity and compatibility validation via PredictionValidator.
4. Inference execution on trained estimators without retraining.
5. Contextual decision-support and anticipation reasoning via DecisionEngine.
6. Incremental execution management (version matching and --force-refresh support).
7. Persistence of PredictionRecord and PredictionValidationReport objects.
"""

from __future__ import annotations

import math
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.settings import settings
from models.training.dataset_builder import DatasetBuilder
from prediction.decision_engine import DecisionEngine
from prediction.model_selector import ModelSelector
from prediction.validator import PredictionValidator
from schemas.anticipation import AnticipationScore
from schemas.prediction import (
    PredictionRecord,
    PredictionValidationReport,
    make_prediction_id,
)
from storage.anticipation_repository import AnticipationRepository
from storage.company_repository import CompanyRepository
from storage.evaluation_repository import EvaluationRepository
from storage.feature_selection_repository import FeatureSelectionRepository
from storage.model_repository import ModelRepository
from storage.prediction_repository import PredictionRepository

logger = get_logger(__name__)

CURRENT_MODEL_VERSION = "v1.0"
CURRENT_FEATURE_VERSION = "v1.0"


class FinalPredictionEngine:
    """
    Final Prediction and Decision Support Engine for the Legislative Market Impact System.

    Parameters
    ----------
    model_repo : ModelRepository, optional
    eval_repo : EvaluationRepository, optional
    anticipation_repo : AnticipationRepository, optional
    prediction_repo : PredictionRepository, optional
    selection_repo : FeatureSelectionRepository, optional
    company_repo : CompanyRepository, optional
    dataset_builder : DatasetBuilder, optional
    model_selector : ModelSelector, optional
    validator : PredictionValidator, optional
    decision_engine : DecisionEngine, optional
    mode : str, optional
        Feature selection mode (default: "structured").
    """

    def __init__(
        self,
        model_repo: Optional[ModelRepository] = None,
        eval_repo: Optional[EvaluationRepository] = None,
        anticipation_repo: Optional[AnticipationRepository] = None,
        prediction_repo: Optional[PredictionRepository] = None,
        selection_repo: Optional[FeatureSelectionRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        dataset_builder: Optional[DatasetBuilder] = None,
        model_selector: Optional[ModelSelector] = None,
        validator: Optional[PredictionValidator] = None,
        decision_engine: Optional[DecisionEngine] = None,
        mode: str = "structured",
    ) -> None:
        self.model_repo = model_repo or ModelRepository()
        self.eval_repo = eval_repo or EvaluationRepository()
        self.anticipation_repo = anticipation_repo or AnticipationRepository()
        self.prediction_repo = prediction_repo or PredictionRepository()
        self.selection_repo = selection_repo or FeatureSelectionRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.dataset_builder = dataset_builder or DatasetBuilder(selection_repo=self.selection_repo)

        self.model_selector = model_selector or ModelSelector(eval_repo=self.eval_repo)
        self.validator = validator or PredictionValidator(model_repo=self.model_repo)
        self.decision_engine = decision_engine or DecisionEngine()
        self.mode = mode

        self._cached_models: dict[str, Any] = {}
        self._cached_preprocessors: dict[str, Any] = {}
        self._cached_features: dict[str, list[str]] = {}
        self._cached_encoders: dict[str, Any] = {}

        logger.debug("FinalPredictionEngine initialised | mode=%s", self.mode)

    # ------------------------------------------------------------------
    # Model Loading (Cached)
    # ------------------------------------------------------------------

    def _load_model_bundle(self, target: str, model_type: str) -> tuple[Any, Any, list[str], Any]:
        """
        Load estimator, preprocessor, feature list, and label encoder for a target.
        """
        key = f"{target}:{model_type}"
        if key in self._cached_models:
            return (
                self._cached_models[key],
                self._cached_preprocessors[key],
                self._cached_features[key],
                self._cached_encoders.get(key),
            )

        model_obj, preprocessor, feature_list = self.model_repo.load(target, model_type)

        # Handle wrapped bundle vs raw estimator
        label_encoder = None
        if isinstance(model_obj, dict) and "estimator" in model_obj:
            estimator = model_obj["estimator"]
            label_encoder = model_obj.get("label_encoder")
        else:
            estimator = model_obj

        self._cached_models[key] = estimator
        self._cached_preprocessors[key] = preprocessor
        self._cached_features[key] = feature_list
        self._cached_encoders[key] = label_encoder

        return estimator, preprocessor, feature_list, label_encoder

    # ------------------------------------------------------------------
    # Single Observation Inference
    # ------------------------------------------------------------------

    def predict_observation(
        self,
        feature_dict: dict[str, Any],
        selected_models: Optional[dict[str, str]] = None,
        force_refresh: bool = False,
    ) -> tuple[Optional[PredictionRecord], Optional[PredictionValidationReport]]:
        """
        Execute prediction for a single bill-company-event observation dictionary.

        Parameters
        ----------
        feature_dict : dict[str, Any]
            Observation features dictionary.
        selected_models : dict[str, str], optional
            Target -> model_type override.
        force_refresh : bool

        Returns
        -------
        tuple[Optional[PredictionRecord], Optional[PredictionValidationReport]]
        """
        bill_id = str(feature_dict.get("bill_id", ""))
        company_isin = str(
            feature_dict.get("company_isin", feature_dict.get("isin", ""))
        )
        event_window = str(
            feature_dict.get(
                "event_window", getattr(settings, "PREDICTION_DEFAULT_EVENT_WINDOW", "[-20,+20]")
            )
        )
        pred_id = make_prediction_id(bill_id, company_isin, event_window)

        # 1. Incremental Check
        if not force_refresh and self.prediction_repo.exists(bill_id, company_isin, event_window):
            existing = self.prediction_repo.get(pred_id)
            if existing is not None:
                if (
                    existing.model_version == CURRENT_MODEL_VERSION
                    and existing.feature_version == CURRENT_FEATURE_VERSION
                ):
                    logger.debug("Incremental execution: skipping cached prediction %s", pred_id)
                    return existing, None

        # 2. Select Models for all 4 targets
        target_models = selected_models or self.model_selector.select_all_best_models()

        # 3. Load & Validate Models & Features
        target_probs: dict[str, dict[str, float]] = {}
        target_preds: dict[str, Any] = {}
        combined_validation_errors: list[str] = []
        combined_validation_warnings: list[str] = []

        for target in ["direction", "market_moving", "impact_strength", "confidence"]:
            model_type = target_models[target]
            try:
                estimator, preprocessor, expected_features, label_encoder = self._load_model_bundle(
                    target, model_type
                )
            except Exception as exc:
                err_msg = f"Failed to load model for target='{target}', model_type='{model_type}': {exc}"
                logger.error(err_msg)
                val_rep = PredictionValidationReport(
                    report_id="",
                    bill_id=bill_id,
                    company_isin=company_isin,
                    event_window=event_window,
                    is_valid=False,
                    errors=[err_msg],
                )
                self.prediction_repo.save_validation_report(val_rep)
                return None, val_rep

            # Run pre-inference validation
            val_rep = self.validator.validate_input_row(
                row_dict=feature_dict,
                target=target,
                model_type=model_type,
                expected_features=expected_features,
                bill_id=bill_id,
                company_isin=company_isin,
                event_window=event_window,
            )

            if not val_rep.is_valid:
                logger.warning(
                    "Validation failed for %s on target '%s': %s",
                    pred_id,
                    target,
                    val_rep.errors,
                )
                self.prediction_repo.save_validation_report(val_rep)
                return None, val_rep

            if val_rep.warnings:
                combined_validation_warnings.extend(val_rep.warnings)

            # Construct single-row DataFrame with expected features
            row_df = pd.DataFrame([{f: feature_dict.get(f) for f in expected_features}])

            # Apply Preprocessing Pipeline
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    if preprocessor is not None:
                        X_proc = preprocessor.transform(row_df)
                    else:
                        X_proc = row_df.values
            except Exception as exc:
                err_msg = f"Preprocessor transform failed for target='{target}': {exc}"
                logger.error(err_msg)
                val_rep.errors.append(err_msg)
                val_rep.is_valid = False
                self.prediction_repo.save_validation_report(val_rep)
                return None, val_rep

            # Compute Probabilities & Predictions
            probs_dict, pred_class = self._evaluate_estimator(
                estimator=estimator,
                X_proc=X_proc,
                target=target,
                label_encoder=label_encoder,
            )
            target_probs[target] = probs_dict
            target_preds[target] = pred_class

        # 4. Extract Company & Anticipation Metadata
        company_obj = self.company_repo.get_by_isin(company_isin)
        company_name = feature_dict.get("company_name", company_obj.company_name if company_obj else "")
        company_symbol = feature_dict.get(
            "nse_symbol",
            getattr(company_obj, "ticker_nse", getattr(company_obj, "ticker", "")) if company_obj else "",
        )

        anticipation_score_rec: Optional[AnticipationScore] = None
        try:
            anticipation_score_rec = self.anticipation_repo.get_score(bill_id, company_isin)
        except Exception as exc:
            logger.debug("Could not retrieve anticipation score for (%s, %s): %s", bill_id, company_isin, exc)

        # 5. Contextual Decision Engine Blending
        dir_probs = target_probs["direction"]
        predicted_dir = str(target_preds["direction"]).upper()
        if predicted_dir not in {"POSITIVE", "NEGATIVE", "NEUTRAL"}:
            predicted_dir = "NEUTRAL"

        market_moving_pred = bool(target_preds["market_moving"])
        market_moving_prob = float(target_probs["market_moving"].get("TRUE", target_probs["market_moving"].get("True", 0.0)))
        if market_moving_prob == 0.0 and True in target_probs["market_moving"]:
            market_moving_prob = float(target_probs["market_moving"][True])

        strength_pred = str(target_preds["impact_strength"]).upper()
        impact_probs = target_probs["impact_strength"]

        conf_pred = str(target_preds["confidence"]).upper()
        conf_probs = target_probs["confidence"]

        company_meta = {
            "beta": feature_dict.get("beta"),
            "alpha": feature_dict.get("alpha"),
            "r_squared": feature_dict.get("r_squared"),
            "residual_variance": feature_dict.get("residual_variance"),
            "is_imputed": len(combined_validation_warnings) > 0,
        }

        (
            decision_reason,
            expected_impact_estimate,
            risk_indicators,
            model_confidence_scalar,
            data_quality_status,
        ) = self.decision_engine.generate_decision_support(
            predicted_direction=predicted_dir,
            direction_probs=dir_probs,
            predicted_market_moving=market_moving_pred,
            market_moving_prob=market_moving_prob,
            predicted_impact_strength=strength_pred,
            impact_probs=impact_probs,
            predicted_confidence=conf_pred,
            confidence_probs=conf_probs,
            anticipation_score_record=anticipation_score_rec,
            company_meta=company_meta,
        )

        # 6. Construct strongly-typed PredictionRecord
        anticipation_class_str = (
            str(anticipation_score_rec.classification)
            if anticipation_score_rec
            else "NOT_ANALYZED"
        )
        anticipation_score_float = (
            float(anticipation_score_rec.anticipation_score)
            if anticipation_score_rec
            else 0.0
        )

        record = PredictionRecord(
            prediction_id=pred_id,
            bill_id=bill_id,
            company_isin=company_isin,
            company_name=company_name,
            company_symbol=company_symbol,
            event_window=event_window,
            predicted_direction=predicted_dir,
            direction_probability=dir_probs,
            predicted_market_moving=market_moving_pred,
            market_moving_probability=market_moving_prob,
            predicted_impact_strength=strength_pred,
            impact_probabilities=impact_probs,
            predicted_confidence=conf_pred,
            confidence_probability=conf_probs,
            anticipation_class=anticipation_class_str,
            anticipation_score=anticipation_score_float,
            model_name=target_models,
            model_version=CURRENT_MODEL_VERSION,
            feature_version=CURRENT_FEATURE_VERSION,
            prediction_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            decision_reason=decision_reason,
            expected_impact_estimate=expected_impact_estimate,
            risk_indicators=risk_indicators,
            model_confidence=model_confidence_scalar,
            data_quality_status=data_quality_status,
        )

        # 7. Persist to PredictionRepository
        self.prediction_repo.save(record)
        return record, None

    # ------------------------------------------------------------------
    # Estimator Probability Extraction Helper
    # ------------------------------------------------------------------

    def _evaluate_estimator(
        self,
        estimator: Any,
        X_proc: Any,
        target: str,
        label_encoder: Optional[Any] = None,
    ) -> tuple[dict[str, float], Any]:
        """
        Extract class probabilities and predicted class from estimator and label encoder.
        """
        classes: list[Any] = []
        if hasattr(estimator, "classes_"):
            classes = list(estimator.classes_)
        elif label_encoder is not None and hasattr(label_encoder, "classes_"):
            classes = list(label_encoder.classes_)

        # Default class labels per target
        default_target_classes = {
            "direction": ["NEGATIVE", "NEUTRAL", "POSITIVE"],
            "market_moving": ["FALSE", "TRUE"],
            "impact_strength": ["HIGH", "LOW", "MEDIUM", "VERY_HIGH"],
            "confidence": ["HIGH", "LOW", "MEDIUM"],
        }

        # Predict Probabilities
        if hasattr(estimator, "predict_proba"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                raw_probs = estimator.predict_proba(X_proc)[0]
        else:
            # Fallback if estimator does not support predict_proba
            raw_pred = estimator.predict(X_proc)[0]
            raw_probs = np.zeros(len(classes) if classes else 2)
            if classes and raw_pred in classes:
                raw_probs[classes.index(raw_pred)] = 1.0
            else:
                raw_probs[0] = 1.0

        # Map to class string labels
        probs_dict: dict[str, float] = {}
        if classes:
            for idx, cls_val in enumerate(classes):
                if label_encoder is not None and isinstance(cls_val, (int, np.integer)):
                    try:
                        cls_name = str(label_encoder.inverse_transform([cls_val])[0]).upper()
                    except Exception:
                        cls_name = str(cls_val).upper()
                else:
                    cls_name = str(cls_val).upper()
                probs_dict[cls_name] = round(float(raw_probs[idx]), 4)
        else:
            expected_c = default_target_classes.get(target, ["CLASS_0", "CLASS_1"])
            for idx, c_name in enumerate(expected_c):
                p_val = float(raw_probs[idx]) if idx < len(raw_probs) else 0.0
                probs_dict[c_name] = round(p_val, 4)

        # Normalize probabilities to sum to 1.0
        total_p = sum(probs_dict.values())
        if total_p > 0:
            probs_dict = {k: round(v / total_p, 4) for k, v in probs_dict.items()}

        # Determine predicted class
        pred_class_name = max(probs_dict.items(), key=lambda x: x[1])[0]

        # Handle binary boolean conversion for market_moving
        if target == "market_moving":
            is_true = pred_class_name in {"TRUE", "1", "1.0"}
            return probs_dict, is_true

        return probs_dict, pred_class_name

    # ------------------------------------------------------------------
    # Batch Execution
    # ------------------------------------------------------------------

    def run_all(
        self,
        bill_id_filter: Optional[str] = None,
        company_isin_filter: Optional[str] = None,
        year_filter: Optional[int] = None,
        event_window_filter: Optional[str] = None,
        force_refresh: bool = False,
        feature_mode: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute prediction pipeline across matching observations.

        Parameters
        ----------
        bill_id_filter : str, optional
        company_isin_filter : str, optional
        year_filter : int, optional
        event_window_filter : str, optional
        force_refresh : bool, optional
        feature_mode : str, optional

        Returns
        -------
        dict[str, Any]
            Execution metrics, counts, and generated predictions.
        """
        mode = feature_mode or self.mode
        logger.info(
            "FinalPredictionEngine: running prediction pipeline | mode=%s bill=%s isin=%s year=%s force=%s",
            mode,
            bill_id_filter,
            company_isin_filter,
            year_filter,
            force_refresh,
        )

        # 1. Load Pre-Event Training / Research Dataset
        df_training, df_research, _, _ = self.dataset_builder.build(mode=mode, rebuild=False)

        # Work on research dataset which retains bill_id, isin, event_window identifiers
        df = df_research.copy()

        # 2. Apply Filters
        if bill_id_filter:
            df = df[df["bill_id"].astype(str) == str(bill_id_filter)]
        if company_isin_filter:
            isin_col = "company_isin" if "company_isin" in df.columns else "isin"
            df = df[df[isin_col].astype(str) == str(company_isin_filter)]
        if event_window_filter and "event_window" in df.columns:
            df = df[df["event_window"].astype(str) == str(event_window_filter)]
        if year_filter is not None:
            if "introduction_date" in df.columns:
                try:
                    df["_year"] = pd.to_datetime(df["introduction_date"], errors="coerce").dt.year
                    df = df[df["_year"] == int(year_filter)]
                except Exception:
                    pass

        total_records = len(df)
        logger.info("Found %d matching candidate records for prediction.", total_records)

        stats: dict[str, Any] = {
            "total_candidates": total_records,
            "predictions_generated": 0,
            "predictions_skipped": 0,
            "predictions_failed": 0,
            "records": [],
            "models_used": self.model_selector.select_all_best_models(),
            "target_distributions": {
                "direction": {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0},
                "market_moving": {"TRUE": 0, "FALSE": 0},
                "impact_strength": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "VERY_HIGH": 0},
                "confidence": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
            },
        }

        selected_models = stats["models_used"]

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            bill_id = str(row_dict.get("bill_id", ""))
            isin = str(row_dict.get("company_isin", row_dict.get("isin", "")))
            win = str(row_dict.get("event_window", "[-20,+20]"))

            # Check if skipped via incremental caching
            pred_id = make_prediction_id(bill_id, isin, win)
            if not force_refresh and self.prediction_repo.exists(bill_id, isin, win):
                existing = self.prediction_repo.get(pred_id)
                if existing is not None and (
                    existing.model_version == CURRENT_MODEL_VERSION
                    and existing.feature_version == CURRENT_FEATURE_VERSION
                ):
                    stats["predictions_skipped"] += 1
                    stats["records"].append(existing)
                    # Count distributions
                    stats["target_distributions"]["direction"][existing.predicted_direction] = (
                        stats["target_distributions"]["direction"].get(existing.predicted_direction, 0) + 1
                    )
                    mm_key = "TRUE" if existing.predicted_market_moving else "FALSE"
                    stats["target_distributions"]["market_moving"][mm_key] = (
                        stats["target_distributions"]["market_moving"].get(mm_key, 0) + 1
                    )
                    stats["target_distributions"]["impact_strength"][existing.predicted_impact_strength] = (
                        stats["target_distributions"]["impact_strength"].get(existing.predicted_impact_strength, 0) + 1
                    )
                    stats["target_distributions"]["confidence"][existing.predicted_confidence] = (
                        stats["target_distributions"]["confidence"].get(existing.predicted_confidence, 0) + 1
                    )
                    continue

            record, err_rep = self.predict_observation(
                feature_dict=row_dict,
                selected_models=selected_models,
                force_refresh=force_refresh,
            )

            if record is not None:
                stats["predictions_generated"] += 1
                stats["records"].append(record)
                stats["target_distributions"]["direction"][record.predicted_direction] = (
                    stats["target_distributions"]["direction"].get(record.predicted_direction, 0) + 1
                )
                mm_key = "TRUE" if record.predicted_market_moving else "FALSE"
                stats["target_distributions"]["market_moving"][mm_key] = (
                    stats["target_distributions"]["market_moving"].get(mm_key, 0) + 1
                )
                stats["target_distributions"]["impact_strength"][record.predicted_impact_strength] = (
                    stats["target_distributions"]["impact_strength"].get(record.predicted_impact_strength, 0) + 1
                )
                stats["target_distributions"]["confidence"][record.predicted_confidence] = (
                    stats["target_distributions"]["confidence"].get(record.predicted_confidence, 0) + 1
                )
            else:
                stats["predictions_failed"] += 1

        logger.info(
            "Prediction run complete: %d generated, %d skipped, %d failed out of %d candidates.",
            stats["predictions_generated"],
            stats["predictions_skipped"],
            stats["predictions_failed"],
            stats["total_candidates"],
        )
        return stats
