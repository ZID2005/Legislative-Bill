"""
tests/test_prediction_validator.py
==================================
Unit tests for PredictionValidator (Task 7.1).
"""

from __future__ import annotations

import math
from unittest.mock import MagicMock
import pandas as pd
import pytest

from prediction.validator import PredictionValidator
from storage.model_repository import ModelRepository


@pytest.fixture
def mock_model_repo() -> ModelRepository:
    repo = MagicMock(spec=ModelRepository)
    repo.exists.return_value = True
    return repo


@pytest.fixture
def valid_row() -> dict:
    return {
        "bill_id": "finance-bill-2024",
        "company_isin": "INE002A01018",
        "event_window": "[-20,+20]",
        "bill_type": "Finance",
        "ministry": "Finance",
        "department": "Revenue",
        "policy_domain": "Taxation",
        "economic_domain": "Fiscal",
        "primary_sector": "Banking",
        "secondary_sectors": ["Finance"],
        "regulatory_authority": "RBI",
        "geographic_scope": "National",
        "company_sector": "Financials",
        "industry": "Banking",
        "sub_industry": "Private Bank",
        "hq_state": "Maharashtra",
        "alpha": 0.001,
        "beta": 1.15,
        "r_squared": 0.45,
        "residual_variance": 0.0002,
    }


class TestPredictionValidator:
    def test_validate_valid_input_row(
        self, mock_model_repo: ModelRepository, valid_row: dict
    ) -> None:
        validator = PredictionValidator(model_repo=mock_model_repo)
        features = [
            "bill_type",
            "ministry",
            "department",
            "policy_domain",
            "economic_domain",
            "primary_sector",
            "company_sector",
            "industry",
            "sub_industry",
            "hq_state",
            "alpha",
            "beta",
            "r_squared",
            "residual_variance",
        ]
        rep = validator.validate_input_row(
            row_dict=valid_row,
            target="direction",
            model_type="lgbm",
            expected_features=features,
            bill_id="finance-bill-2024",
            company_isin="INE002A01018",
        )
        assert rep.is_valid is True
        assert len(rep.errors) == 0

    def test_reject_invalid_identifiers(
        self, mock_model_repo: ModelRepository, valid_row: dict
    ) -> None:
        validator = PredictionValidator(model_repo=mock_model_repo)
        rep = validator.validate_input_row(
            row_dict=valid_row,
            target="direction",
            model_type="lgbm",
            expected_features=["alpha", "beta"],
            bill_id="",
            company_isin="",
        )
        assert rep.is_valid is False
        assert any("bill_id" in err for err in rep.errors)
        assert any("company_isin" in err for err in rep.errors)

    def test_reject_missing_model_in_repository(
        self, valid_row: dict
    ) -> None:
        repo = MagicMock(spec=ModelRepository)
        repo.exists.return_value = False
        validator = PredictionValidator(model_repo=repo)

        rep = validator.validate_input_row(
            row_dict=valid_row,
            target="direction",
            model_type="lgbm",
            expected_features=["alpha", "beta"],
            bill_id="finance-bill-2024",
            company_isin="INE002A01018",
        )
        assert rep.is_valid is False
        assert any("missing in ModelRepository" in err for err in rep.errors)

    def test_reject_missing_required_features(
        self, mock_model_repo: ModelRepository, valid_row: dict
    ) -> None:
        validator = PredictionValidator(model_repo=mock_model_repo)
        expected_features = ["alpha", "beta", "non_existent_feature_123"]

        rep = validator.validate_input_row(
            row_dict=valid_row,
            target="direction",
            model_type="lgbm",
            expected_features=expected_features,
            bill_id="finance-bill-2024",
            company_isin="INE002A01018",
        )
        assert rep.is_valid is False
        assert any("Missing 1 required features" in err for err in rep.errors)

    def test_reject_nan_and_inf_values(
        self, mock_model_repo: ModelRepository, valid_row: dict
    ) -> None:
        validator = PredictionValidator(model_repo=mock_model_repo)
        nan_row = dict(valid_row)
        nan_row["beta"] = float("nan")

        rep = validator.validate_input_row(
            row_dict=nan_row,
            target="direction",
            model_type="lgbm",
            expected_features=["alpha", "beta"],
            bill_id="finance-bill-2024",
            company_isin="INE002A01018",
        )
        assert rep.is_valid is False
        assert any("NaN or Inf values detected" in err for err in rep.errors)

        inf_row = dict(valid_row)
        inf_row["alpha"] = float("inf")
        rep_inf = validator.validate_input_row(
            row_dict=inf_row,
            target="direction",
            model_type="lgbm",
            expected_features=["alpha", "beta"],
            bill_id="finance-bill-2024",
            company_isin="INE002A01018",
        )
        assert rep_inf.is_valid is False
        assert any("NaN or Inf values detected" in err for err in rep_inf.errors)

    def test_reject_unsupported_complex_categoricals(
        self, mock_model_repo: ModelRepository, valid_row: dict
    ) -> None:
        validator = PredictionValidator(model_repo=mock_model_repo)
        bad_row = dict(valid_row)
        bad_row["primary_sector"] = {"invalid": "dict_object"}

        rep = validator.validate_input_row(
            row_dict=bad_row,
            target="direction",
            model_type="lgbm",
            expected_features=["primary_sector", "beta"],
            bill_id="finance-bill-2024",
            company_isin="INE002A01018",
        )
        assert rep.is_valid is False
        assert any("Unsupported non-scalar" in err for err in rep.errors)

    def test_validate_dataframe(
        self, mock_model_repo: ModelRepository, valid_row: dict
    ) -> None:
        validator = PredictionValidator(model_repo=mock_model_repo)
        df = pd.DataFrame([valid_row, valid_row])
        target_models = {"direction": "lgbm", "market_moving": "random_forest"}
        model_features_map = {
            "direction": ["alpha", "beta"],
            "market_moving": ["alpha", "beta"],
        }
        reports = validator.validate_dataframe(df, target_models, model_features_map)
        assert len(reports) == 4
        assert all(r.is_valid for r in reports)

    def test_none_feature_generates_warning(
        self, mock_model_repo: ModelRepository, valid_row: dict
    ) -> None:
        validator = PredictionValidator(model_repo=mock_model_repo)
        none_row = dict(valid_row)
        none_row["hq_state"] = None

        rep = validator.validate_input_row(
            row_dict=none_row,
            target="direction",
            model_type="lgbm",
            expected_features=["hq_state", "beta"],
            bill_id="finance-bill-2024",
            company_isin="INE002A01018",
        )
        assert rep.is_valid is True
        assert any("Feature 'hq_state' is None" in w for w in rep.warnings)
