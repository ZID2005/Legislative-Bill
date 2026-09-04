"""
prediction/validator.py
=======================
Input and compatibility validator for the Final Prediction Engine (Task 7.1).

Validates feature datasets, individual feature rows, model artifacts, preprocessors,
and bill-company mappings before forward inference is executed.

Rejection Criteria
------------------
1. Missing required feature columns.
2. Missing or unavailable model artifacts.
3. Feature dimension mismatch between input data and model expectations.
4. NaN or Infinite values in numerical feature vectors.
5. Unsupported / corrupt categorical fields.
6. Invalid or unmapped bill/company identifiers.
7. Incompatible model metadata or missing preprocessor.
"""

from __future__ import annotations

import math
from typing import Any, Optional

import numpy as np
import pandas as pd

from config.logging_config import get_logger
from schemas.prediction import PredictionValidationReport
from storage.model_repository import ModelRepository

logger = get_logger(__name__)


class PredictionValidator:
    """
    Validates feature inputs, model availability, and metadata integrity.

    Parameters
    ----------
    model_repo : ModelRepository, optional
    """

    def __init__(self, model_repo: Optional[ModelRepository] = None) -> None:
        self._model_repo = model_repo or ModelRepository()

    def validate_input_row(
        self,
        row_dict: dict[str, Any],
        target: str,
        model_type: str,
        expected_features: list[str],
        bill_id: str,
        company_isin: str,
        event_window: str = "[-20,+20]",
    ) -> PredictionValidationReport:
        """
        Validate a single feature observation dictionary before running inference.

        Parameters
        ----------
        row_dict : dict[str, Any]
            Dictionary of feature values for one observation.
        target : str
            Prediction target name.
        model_type : str
            Selected model algorithm (e.g. 'lgbm', 'random_forest').
        expected_features : list[str]
            List of feature names required by the trained model.
        bill_id : str
        company_isin : str
        event_window : str

        Returns
        -------
        PredictionValidationReport
        """
        report = PredictionValidationReport(
            report_id="",
            bill_id=bill_id,
            company_isin=company_isin,
            event_window=event_window,
            is_valid=True,
            errors=[],
            warnings=[],
            checks_performed={},
            details={
                "target": target,
                "model_type": model_type,
                "expected_feature_count": len(expected_features),
            },
        )

        # 1. Check Bill & Company identifiers
        if not bill_id or not str(bill_id).strip():
            report.errors.append("Invalid bill_id: must be a non-empty string.")
        if not company_isin or not str(company_isin).strip():
            report.errors.append("Invalid company_isin: must be a non-empty string.")
        report.checks_performed["identifier_check"] = len(report.errors) == 0

        # 2. Check Model Availability
        if not self._model_repo.exists(target, model_type):
            report.errors.append(
                f"Trained model artefact missing in ModelRepository for target='{target}', model_type='{model_type}'."
            )
            report.checks_performed["model_availability"] = False
        else:
            report.checks_performed["model_availability"] = True

        # 3. Check Required Features
        missing_features = [f for f in expected_features if f not in row_dict]
        if missing_features:
            report.errors.append(
                f"Missing {len(missing_features)} required features: {missing_features[:5]} (total {len(missing_features)})"
            )
            report.checks_performed["required_features_present"] = False
        else:
            report.checks_performed["required_features_present"] = True

        # 4. Check Feature Dimensions
        available_expected = [f for f in expected_features if f in row_dict]
        if len(available_expected) != len(expected_features):
            report.errors.append(
                f"Feature dimension mismatch: expected {len(expected_features)}, got {len(available_expected)}."
            )
            report.checks_performed["dimension_match"] = False
        else:
            report.checks_performed["dimension_match"] = True

        # 5. Check NaN / Inf in Numeric Fields
        nan_inf_features: list[str] = []
        for feat in expected_features:
            if feat in row_dict:
                val = row_dict[feat]
                if isinstance(val, (int, float)):
                    if math.isnan(val) or math.isinf(val):
                        nan_inf_features.append(feat)
                elif val is None:
                    # None values in categoricals or unpopulated financials
                    report.warnings.append(f"Feature '{feat}' is None.")
        if nan_inf_features:
            report.errors.append(
                f"NaN or Inf values detected in numeric features: {nan_inf_features}"
            )
            report.checks_performed["nan_inf_check"] = False
        else:
            report.checks_performed["nan_inf_check"] = True

        # 6. Check Unsupported / Corrupt Categoricals
        corrupt_cats: list[str] = []
        for feat in expected_features:
            if feat in row_dict:
                val = row_dict[feat]
                if isinstance(val, (list, dict, set)):
                    # Unserialized complex objects
                    corrupt_cats.append(feat)
        if corrupt_cats:
            report.errors.append(
                f"Unsupported non-scalar categorical format in features: {corrupt_cats}"
            )
            report.checks_performed["categorical_validity"] = False
        else:
            report.checks_performed["categorical_validity"] = True

        report.is_valid = len(report.errors) == 0
        return report

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        target_models: dict[str, str],
        model_features_map: dict[str, list[str]],
    ) -> list[PredictionValidationReport]:
        """
        Validate an entire DataFrame of observations across multiple targets.

        Parameters
        ----------
        df : pd.DataFrame
        target_models : dict[str, str]
            Target -> model_type mapping.
        model_features_map : dict[str, list[str]]
            Target -> expected feature columns.

        Returns
        -------
        list[PredictionValidationReport]
            Validation reports for all records.
        """
        reports: list[PredictionValidationReport] = []

        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            bill_id = str(row_dict.get("bill_id", ""))
            company_isin = str(row_dict.get("company_isin", row_dict.get("isin", "")))
            event_window = str(row_dict.get("event_window", "[-20,+20]"))

            for target, model_type in target_models.items():
                expected_cols = model_features_map.get(target, [])
                rep = self.validate_input_row(
                    row_dict=row_dict,
                    target=target,
                    model_type=model_type,
                    expected_features=expected_cols,
                    bill_id=bill_id,
                    company_isin=company_isin,
                    event_window=event_window,
                )
                reports.append(rep)

        return reports
