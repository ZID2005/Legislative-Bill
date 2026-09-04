"""
tests/test_prediction_model_selector.py
=======================================
Unit tests for ModelSelector (Task 7.1).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from prediction.model_selector import DEFAULT_BEST_MODELS, ModelSelector
from storage.evaluation_repository import EvaluationRepository


@pytest.fixture
def mock_eval_repo() -> EvaluationRepository:
    repo = MagicMock(spec=EvaluationRepository)
    repo.exists.return_value = True
    repo.load_comparison_report.return_value = {
        "direction": {
            "best_model": {"model_type": "lgbm", "f1_macro": 0.7467, "accuracy": 0.9466},
            "rankings": [{"rank": 1, "model_type": "lgbm", "f1_macro": 0.7467}],
        },
        "market_moving": {
            "best_model": {"model_type": "random_forest", "f1_macro": 0.8106, "accuracy": 0.9470},
            "rankings": [{"rank": 1, "model_type": "random_forest", "f1_macro": 0.8106}],
        },
        "impact_strength": {
            "best_model": {"model_type": "lgbm", "f1_macro": 0.5979, "accuracy": 0.5960},
            "rankings": [{"rank": 1, "model_type": "lgbm", "f1_macro": 0.5979}],
        },
        "confidence": {
            "best_model": {"model_type": "lgbm", "f1_macro": 0.7057, "accuracy": 0.7513},
            "rankings": [{"rank": 1, "model_type": "lgbm", "f1_macro": 0.7057}],
        },
    }
    repo.load_metrics.return_value = {
        "direction": {
            "lgbm": {"f1_macro": 0.7467, "balanced_accuracy": 0.6897, "roc_auc": 0.9813},
            "xgboost": {"f1_macro": 0.7410, "balanced_accuracy": 0.6803, "roc_auc": 0.9812},
        }
    }
    return repo


class TestModelSelector:
    def test_select_best_model_from_comparison_report(
        self, mock_eval_repo: EvaluationRepository
    ) -> None:
        selector = ModelSelector(eval_repo=mock_eval_repo)
        model_type, rationale = selector.select_best_model("direction")
        assert model_type == "lgbm"
        assert rationale["source"] == "comparison_report.json"
        assert rationale["best_model_metrics"]["f1_macro"] == 0.7467

        mm_type, mm_rationale = selector.select_best_model("market_moving")
        assert mm_type == "random_forest"

    def test_select_best_model_from_metrics_fallback(self) -> None:
        repo = MagicMock(spec=EvaluationRepository)
        repo.exists.return_value = True
        repo.load_comparison_report.return_value = {}  # Empty comparison report
        repo.load_metrics.return_value = {
            "direction": {
                "xgboost": {"f1_macro": 0.72, "balanced_accuracy": 0.65, "roc_auc": 0.95},
                "lgbm": {"f1_macro": 0.78, "balanced_accuracy": 0.70, "roc_auc": 0.98},
            }
        }
        selector = ModelSelector(eval_repo=repo)
        model_type, rationale = selector.select_best_model("direction")
        assert model_type == "lgbm"
        assert rationale["source"] == "metrics.json"

    def test_select_best_model_default_when_missing_repo(self) -> None:
        repo = MagicMock(spec=EvaluationRepository)
        repo.exists.return_value = False
        selector = ModelSelector(eval_repo=repo)

        dir_model, r_dir = selector.select_best_model("direction")
        assert dir_model == "lgbm"
        assert r_dir["source"] == "default_rules"

        mm_model, r_mm = selector.select_best_model("market_moving")
        assert mm_model == "random_forest"

    def test_select_best_model_handles_exceptions_gracefully(self) -> None:
        repo = MagicMock(spec=EvaluationRepository)
        repo.exists.side_effect = RuntimeError("File I/O error")
        selector = ModelSelector(eval_repo=repo)

        model_type, rationale = selector.select_best_model("impact_strength")
        assert model_type == "lgbm"
        assert rationale["source"] == "default_rules"

    def test_select_all_best_models(
        self, mock_eval_repo: EvaluationRepository
    ) -> None:
        selector = ModelSelector(eval_repo=mock_eval_repo)
        all_models = selector.select_all_best_models()
        assert all_models["direction"] == "lgbm"
        assert all_models["market_moving"] == "random_forest"
        assert all_models["impact_strength"] == "lgbm"
        assert all_models["confidence"] == "lgbm"

    def test_get_selection_report(
        self, mock_eval_repo: EvaluationRepository
    ) -> None:
        selector = ModelSelector(eval_repo=mock_eval_repo)
        report = selector.get_selection_report()
        assert "direction" in report
        assert "market_moving" in report
        assert "impact_strength" in report
        assert "confidence" in report
