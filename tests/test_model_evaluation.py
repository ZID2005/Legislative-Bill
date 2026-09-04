"""
tests/test_model_evaluation.py
===============================
Comprehensive test suite for Task 6.2 — Model Evaluation Engine.

Coverage targets:
- EvaluationRepository (save, load, exists, clear)
- compute_metrics helper (binary, multiclass, probability-based metrics)
- ModelEvaluator (dataset loading, prediction pipeline, rankings, error analysis)
- Integration with main CLI parser

All tests use pytest fixtures and in-memory mock data.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from models.evaluation.evaluator import ModelEvaluator
from models.evaluation.metrics import compute_metrics
from storage.evaluation_repository import EvaluationRepository

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def dummy_true_pred() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Synthetic binary true, pred, prob arrays."""
    y_true = np.array([0, 1, 0, 1, 0, 1, 0, 0, 1, 1])
    y_pred = np.array([0, 1, 0, 0, 0, 1, 1, 0, 1, 1])
    y_prob = np.array(
        [
            [0.9, 0.1],
            [0.2, 0.8],
            [0.7, 0.3],
            [0.6, 0.4],
            [0.8, 0.2],
            [0.1, 0.9],
            [0.4, 0.6],
            [0.9, 0.1],
            [0.3, 0.7],
            [0.2, 0.8],
        ]
    )
    classes = ["False", "True"]
    return y_true, y_pred, y_prob, classes


@pytest.fixture
def dummy_multiclass() -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    """Synthetic multiclass true, pred, prob arrays."""
    y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
    y_pred = np.array([0, 1, 2, 1, 1, 2, 0, 2, 2, 0])
    y_prob = np.array(
        [
            [0.8, 0.1, 0.1],
            [0.1, 0.8, 0.1],
            [0.1, 0.1, 0.8],
            [0.3, 0.5, 0.2],
            [0.2, 0.6, 0.2],
            [0.1, 0.2, 0.7],
            [0.7, 0.2, 0.1],
            [0.2, 0.1, 0.7],
            [0.1, 0.1, 0.8],
            [0.9, 0.05, 0.05],
        ]
    )
    classes = ["NEGATIVE", "NEUTRAL", "POSITIVE"]
    return y_true, y_pred, y_prob, classes


@pytest.fixture
def mock_dataset(tmp_path):
    """Generates synthetic dataset to be returned by mock DatasetBuilder."""
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    df = pd.DataFrame(
        {
            "record_id": [f"rec_{i}" for i in range(10)],
            "introduction_date": dates,
            "f1": np.random.randn(10),
            "f2": np.random.randn(10),
            "direction": ["POSITIVE", "NEUTRAL", "NEGATIVE"] * 3 + ["NEUTRAL"],
            "market_moving": [True, False] * 5,
            "impact_strength": ["LOW", "MEDIUM", "HIGH"] * 3 + ["LOW"],
            "confidence_label": ["HIGH", "LOW", "MEDIUM"] * 3 + ["HIGH"],
        }
    )
    return df


@pytest.fixture
def mock_model_repo():
    """Generates mock ModelRepository with pre-fitted dummy classifiers."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer

    repo = MagicMock()
    repo.exists.return_value = True

    # Build fitted estimator for target
    def mock_load(target, model_type):
        # Fit dummy random forest
        rf = RandomForestClassifier(n_estimators=3, random_state=42)
        X_dummy = np.random.randn(10, 2)
        y_dummy = np.array([0, 1, 0, 1, 0, 1, 0, 0, 1, 1])
        if target == "direction":
            y_dummy = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
        elif target == "impact_strength":
            y_dummy = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])
        elif target == "confidence":
            y_dummy = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2, 0])

        rf.fit(X_dummy, y_dummy)

        # LabelEncoder
        le = LabelEncoder()
        if target == "market_moving":
            le.fit(["False", "True"])
        elif target == "direction":
            le.fit(["NEGATIVE", "NEUTRAL", "POSITIVE"])
        elif target == "impact_strength":
            le.fit(["HIGH", "LOW", "MEDIUM"])
        else:
            le.fit(["HIGH", "LOW", "MEDIUM"])

        bundle = {"estimator": rf, "label_encoder": le}

        # Preprocessor
        prep = ColumnTransformer([("num", SimpleImputer(), ["f1", "f2"])])
        prep.fit(pd.DataFrame({"f1": [1.0] * 10, "f2": [2.0] * 10}))

        feature_list = ["f1", "f2"]

        return bundle, prep, feature_list

    repo.load.side_effect = mock_load
    return repo


# ---------------------------------------------------------------------------
# 1. Metrics Computation Tests
# ---------------------------------------------------------------------------


class TestMetricsHelper:
    """Tests for compute_metrics helper function."""

    def test_binary_metrics_keys(self, dummy_true_pred):
        y_true, y_pred, y_prob, classes = dummy_true_pred
        res = compute_metrics(y_true, y_pred, y_prob, classes)

        assert "accuracy" in res
        assert "balanced_accuracy" in res
        assert "mcc" in res
        assert "f1_macro" in res
        assert "f1_weighted" in res
        assert "roc_auc" in res
        assert "log_loss" in res
        assert res["samples"] == 10

    def test_multiclass_metrics(self, dummy_multiclass):
        y_true, y_pred, y_prob, classes = dummy_multiclass
        res = compute_metrics(y_true, y_pred, y_prob, classes)

        assert res["accuracy"] >= 0.0
        assert res["roc_auc"] is not None
        assert res["log_loss"] is not None

    def test_none_prob_graceful(self, dummy_true_pred):
        y_true, y_pred, _, classes = dummy_true_pred
        res = compute_metrics(y_true, y_pred, None, classes)

        assert res["roc_auc"] is None
        assert res["log_loss"] is None

    def test_invalid_prob_shape_graceful(self, dummy_true_pred):
        y_true, y_pred, _, classes = dummy_true_pred
        bad_prob = np.array([0.5, 0.5])
        res = compute_metrics(y_true, y_pred, bad_prob, classes)
        assert res["roc_auc"] is None


# ---------------------------------------------------------------------------
# 2. EvaluationRepository Tests
# ---------------------------------------------------------------------------


class TestEvaluationRepository:
    """Tests for EvaluationRepository save/load/exists/clear."""

    @pytest.fixture
    def repo(self, tmp_path):
        return EvaluationRepository(eval_dir=tmp_path)

    def test_save_load_metrics(self, repo):
        dummy_metrics = {"target_a": {"rf": {"accuracy": 0.85}}}
        path = repo.save_metrics(dummy_metrics)
        assert path.is_file()

        loaded = repo.load_metrics()
        assert loaded["target_a"]["rf"]["accuracy"] == 0.85

    def test_save_load_confusion_matrix(self, repo):
        df = pd.DataFrame(
            [
                {
                    "target": "target_a",
                    "model_type": "rf",
                    "true_label": "A",
                    "predicted_label": "B",
                    "count": 5,
                }
            ]
        )
        path = repo.save_confusion_matrix(df)
        assert path.is_file()

        loaded = repo.load_confusion_matrix()
        assert loaded.shape[0] == 1
        assert loaded.iloc[0]["count"] == 5

    def test_save_load_classification_report(self, repo):
        dummy_rep = {"target_a": {"rf": {"A": {"precision": 0.9}}}}
        path = repo.save_classification_report(dummy_rep)
        assert path.is_file()

        loaded = repo.load_classification_report()
        assert loaded["target_a"]["rf"]["A"]["precision"] == 0.9

    def test_save_load_comparison_report(self, repo):
        dummy_comp = {"target_a": {"best_model": {"model_type": "rf"}}}
        path = repo.save_comparison_report(dummy_comp)
        assert path.is_file()

        loaded = repo.load_comparison_report()
        assert loaded["target_a"]["best_model"]["model_type"] == "rf"

    def test_save_metrics_error(self, repo):
        with patch("pathlib.Path.open", side_effect=OSError("Disk Full")):
            with pytest.raises(OSError):
                repo.save_metrics({})

    def test_save_confusion_matrix_error(self, repo):
        with patch("pandas.DataFrame.to_csv", side_effect=OSError("Disk Full")):
            with pytest.raises(OSError):
                repo.save_confusion_matrix(pd.DataFrame())

    def test_save_classification_report_error(self, repo):
        with patch("pathlib.Path.open", side_effect=OSError("Disk Full")):
            with pytest.raises(OSError):
                repo.save_classification_report({})

    def test_save_comparison_report_error(self, repo):
        with patch("pathlib.Path.open", side_effect=OSError("Disk Full")):
            with pytest.raises(OSError):
                repo.save_comparison_report({})

    def test_load_nonexistent_files_raise_error(self, repo):
        with pytest.raises(FileNotFoundError):
            repo.load_metrics()
        with pytest.raises(FileNotFoundError):
            repo.load_confusion_matrix()
        with pytest.raises(FileNotFoundError):
            repo.load_classification_report()
        with pytest.raises(FileNotFoundError):
            repo.load_comparison_report()

    def test_exists_initially_false(self, repo):
        assert repo.exists() is False

    def test_exists_true_after_all_saves(self, repo):
        repo.save_metrics({})
        repo.save_confusion_matrix(pd.DataFrame())
        repo.save_classification_report({})
        repo.save_comparison_report({})
        assert repo.exists() is True

    def test_clear_removes_files(self, repo):
        repo.save_metrics({})
        repo.save_confusion_matrix(pd.DataFrame())
        repo.save_classification_report({})
        repo.save_comparison_report({})
        assert repo.exists() is True

        repo.clear()
        assert repo.exists() is False


# ---------------------------------------------------------------------------
# 3. ModelEvaluator Tests
# ---------------------------------------------------------------------------


class TestModelEvaluator:
    """Tests for ModelEvaluator execution flow, rankings, and error analysis."""

    @pytest.fixture
    def mock_builder(self, mock_dataset):
        builder = MagicMock()
        builder.build.return_value = (mock_dataset, mock_dataset, MagicMock(), MagicMock())
        return builder

    @pytest.fixture
    def evaluator(self, tmp_path, mock_model_repo, mock_builder):
        eval_repo = EvaluationRepository(eval_dir=tmp_path)
        return ModelEvaluator(
            eval_repo=eval_repo,
            model_repo=mock_model_repo,
            dataset_builder=mock_builder,
            mode="structured",
        )

    def test_evaluate_all_produces_reports(self, evaluator, tmp_path):
        res = evaluator.evaluate_all()
        assert isinstance(res, dict)
        assert "metrics" in res
        assert "comparison" in res
        assert "classification_reports" in res
        assert "confusion_matrix" in res

        # Check repository files
        assert (tmp_path / "metrics.json").is_file()
        assert (tmp_path / "confusion_matrix.csv").is_file()
        assert (tmp_path / "classification_report.json").is_file()
        assert (tmp_path / "comparison_report.json").is_file()

    def test_comparison_report_format(self, evaluator):
        res = evaluator.evaluate_all()
        comp = res["comparison"]

        assert "direction" in comp
        assert "best_model" in comp["direction"]
        assert "worst_model" in comp["direction"]
        assert "average_performance" in comp["direction"]
        assert "rankings" in comp["direction"]

        # rankings should be sorted by rank
        ranks = [r["rank"] for r in comp["direction"]["rankings"]]
        assert ranks == sorted(ranks)

    def test_error_analysis_diagnostics(self, evaluator):
        res = evaluator.evaluate_all()
        rep = res["classification_reports"]

        assert "direction" in rep
        assert "random_forest" in rep["direction"]
        rf_rep = rep["direction"]["random_forest"]

        assert "classification_report" in rf_rep
        assert "error_analysis" in rf_rep

        err = rf_rep["error_analysis"]
        assert "class_imbalance" in err
        assert "hard_classes" in err
        assert "most_common_misclassifications" in err
        assert "prediction_confidence_distribution" in err

    def test_empty_dataset_raises_value_error(self, evaluator):
        evaluator._builder.build.return_value = (pd.DataFrame(), pd.DataFrame(), None, None)
        with pytest.raises(ValueError, match="No training data found"):
            evaluator.evaluate_all()

    def test_evaluator_missing_model_file(self, evaluator):
        """If repo.exists returns False, it should skip without error."""
        evaluator._model_repo.exists.return_value = False
        res = evaluator.evaluate_all()
        # Rankings should be empty because no models were evaluated
        assert res["comparison"] == {}

    def test_evaluator_missing_target_column(self, evaluator, mock_dataset):
        """If target column is missing, it should skip that target."""
        df_missing = mock_dataset.drop(columns=["direction"])
        evaluator._builder.build.return_value = (df_missing, df_missing, None, None)
        res = evaluator.evaluate_all()
        assert "direction" not in res["metrics"]

    def test_evaluator_empty_target_label(self, evaluator, mock_dataset):
        """If target column is all NaN, it should skip that target."""
        df_empty = mock_dataset.copy()
        df_empty["direction"] = np.nan
        evaluator._builder.build.return_value = (df_empty, df_empty, None, None)
        res = evaluator.evaluate_all()
        assert "direction" not in res["metrics"]

    def test_evaluator_load_error(self, evaluator):
        """If loading model fails, it should log the error and continue."""
        evaluator._model_repo.load.side_effect = RuntimeError("Mock load failure")
        res = evaluator.evaluate_all()
        # Should complete successfully but metrics dictionary for targets should be empty
        assert res["metrics"]["direction"] == {}

    def test_metrics_exceptions(self, dummy_true_pred):
        """Test fallback exception coverage in compute_metrics."""
        y_true, y_pred, y_prob, classes = dummy_true_pred
        
        # Test log loss error (with mismatched shapes/labels)
        # Passing wrong labels to trigger sklearn log_loss ValueError
        res = compute_metrics(y_true, y_pred, y_prob[:, :1], classes)
        assert res["log_loss"] is None

        # Test ROC-AUC error (when class targets contain only one class)
        res_single_class = compute_metrics(np.array([1]*10), y_pred, y_prob, classes)
        assert res_single_class["roc_auc"] is None



# ---------------------------------------------------------------------------
# 4. Settings Configuration Verification
# ---------------------------------------------------------------------------


class TestSettings:
    """Verify new settings configuration variables for model evaluation."""

    def test_ml_eval_dir_is_path(self):
        from config.settings import settings

        assert hasattr(settings, "ML_EVAL_DIR")
        assert isinstance(settings.ML_EVAL_DIR, Path)

    def test_ml_eval_dir_auto_created(self):
        from config.settings import settings

        settings.ensure_directories()
        assert settings.ML_EVAL_DIR.is_dir()
