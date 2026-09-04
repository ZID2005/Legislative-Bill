"""
tests/test_prediction_engine.py
===============================
Unit and integration tests for FinalPredictionEngine, incremental execution, and PredictionService (Task 7.1).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.preprocessing import LabelEncoder

from main import cmd_generate_predictions
from models.training.dataset_builder import DatasetBuilder
from prediction.decision_engine import DecisionEngine
from prediction.engine import (
    CURRENT_FEATURE_VERSION,
    CURRENT_MODEL_VERSION,
    FinalPredictionEngine,
)
from prediction.model_selector import ModelSelector
from prediction.validator import PredictionValidator
from schemas.anticipation import AnticipationClassification, AnticipationScore
from schemas.company import Company, MarketCapCategory
from schemas.prediction import PredictionRecord, make_prediction_id
from services.prediction import PredictionService
from storage.anticipation_repository import AnticipationRepository
from storage.company_repository import CompanyRepository
from storage.evaluation_repository import EvaluationRepository
from storage.feature_selection_repository import FeatureSelectionRepository
from storage.model_repository import ModelRepository
from storage.prediction_repository import PredictionRepository


class MockClassifier(BaseEstimator, ClassifierMixin):
    """Sklearn-compatible mock classifier returning predictable probabilities."""

    def __init__(self, classes: list[str], default_probs: list[float]) -> None:
        self.classes_ = np.array(classes)
        self.default_probs = np.array(default_probs)

    def fit(self, X, y=None):
        return self

    def predict_proba(self, X):
        n_samples = len(X)
        return np.tile(self.default_probs, (n_samples, 1))

    def predict(self, X):
        idx = np.argmax(self.default_probs)
        return np.array([self.classes_[idx]] * len(X))


@pytest.fixture
def mock_models() -> dict[str, Any]:
    return {
        "direction": MockClassifier(["NEGATIVE", "NEUTRAL", "POSITIVE"], [0.1, 0.2, 0.7]),
        "market_moving": MockClassifier(["FALSE", "TRUE"], [0.15, 0.85]),
        "impact_strength": MockClassifier(["HIGH", "LOW", "MEDIUM", "VERY_HIGH"], [0.6, 0.1, 0.2, 0.1]),
        "confidence": MockClassifier(["HIGH", "LOW", "MEDIUM"], [0.75, 0.05, 0.20]),
    }


@pytest.fixture
def sample_feature_row() -> dict:
    return {
        "bill_id": "test-telecom-act-2024",
        "company_isin": "INE002A01018",
        "isin": "INE002A01018",
        "event_window": "[-20,+20]",
        "introduction_date": "2024-03-15",
        "company_name": "Reliance Industries",
        "nse_symbol": "RELIANCE",
        "bill_type": "Ordinary",
        "ministry": "Communications",
        "department": "Telecommunications",
        "policy_domain": "Infrastructure",
        "economic_domain": "Technology",
        "primary_sector": "Telecommunications",
        "secondary_sectors": ["Digital"],
        "regulatory_authority": "TRAI",
        "geographic_scope": "National",
        "company_sector": "Energy",
        "industry": "Telecom",
        "sub_industry": "Wireless",
        "hq_state": "Maharashtra",
        "alpha": 0.002,
        "beta": 1.25,
        "r_squared": 0.55,
        "residual_variance": 0.0003,
    }


@pytest.fixture
def sample_research_df(sample_feature_row: dict) -> pd.DataFrame:
    r2 = dict(sample_feature_row)
    r2["company_isin"] = "INE009A01021"
    r2["isin"] = "INE009A01021"
    r2["company_name"] = "Infosys Limited"
    r2["nse_symbol"] = "INFY"
    r2["beta"] = 0.95

    r3 = dict(sample_feature_row)
    r3["bill_id"] = "data-protection-bill-2023"
    r3["introduction_date"] = "2023-08-04"

    return pd.DataFrame([sample_feature_row, r2, r3])


@pytest.fixture
def prediction_engine_env(
    tmp_path: Path, mock_models: dict[str, Any], sample_research_df: pd.DataFrame
) -> FinalPredictionEngine:
    # 1. Setup mock repositories
    pred_dir = tmp_path / "predictions"
    pred_repo = PredictionRepository(predictions_dir=pred_dir)

    model_repo = MagicMock(spec=ModelRepository)
    model_repo.exists.return_value = True

    features_list = [
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

    def mock_load(target, model_type):
        est = mock_models[target]
        le = LabelEncoder().fit(est.classes_)
        bundle = {"estimator": est, "label_encoder": le}
        return bundle, None, features_list

    model_repo.load.side_effect = mock_load

    eval_repo = MagicMock(spec=EvaluationRepository)
    eval_repo.exists.return_value = True
    eval_repo.load_comparison_report.return_value = {
        "direction": {"best_model": {"model_type": "lgbm", "f1_macro": 0.75}},
        "market_moving": {"best_model": {"model_type": "random_forest", "f1_macro": 0.81}},
        "impact_strength": {"best_model": {"model_type": "lgbm", "f1_macro": 0.60}},
        "confidence": {"best_model": {"model_type": "lgbm", "f1_macro": 0.71}},
    }

    anticipation_repo = MagicMock(spec=AnticipationRepository)
    anticipation_repo.get_score.return_value = AnticipationScore(
        bill_id="test-telecom-act-2024",
        company_isin="INE002A01018",
        company_symbol="RELIANCE",
        official_introduction_date="2024-03-15",
        market_signal_score=0.85,
        information_signal_score=0.80,
        anticipation_score=0.82,
        classification=AnticipationClassification.STRONG_EVIDENCE.value,
        anticipation_flag=True,
        confidence="HIGH",
        evidence_count=5,
        media_data_available=True,
        decision_reason="Strong run-up.",
    )

    company_repo = MagicMock(spec=CompanyRepository)
    company_repo.get_by_isin.return_value = Company(
        isin="INE002A01018",
        company_name="Reliance Industries Limited",
        ticker_nse="RELIANCE",
        ticker_bse="RELIANCE",
        bse_code="500325",
        sector="Energy",
        industry="Refining & Telecom",
        market_cap_category=MarketCapCategory.LARGE_CAP,
    )

    dataset_builder = MagicMock(spec=DatasetBuilder)
    dataset_builder.build.return_value = (
        sample_research_df,
        sample_research_df,
        MagicMock(path="path"),
        MagicMock(path="path"),
    )

    engine = FinalPredictionEngine(
        model_repo=model_repo,
        eval_repo=eval_repo,
        anticipation_repo=anticipation_repo,
        prediction_repo=pred_repo,
        company_repo=company_repo,
        dataset_builder=dataset_builder,
    )
    return engine


class TestFinalPredictionEngine:
    def test_predict_single_observation(
        self, prediction_engine_env: FinalPredictionEngine, sample_feature_row: dict
    ) -> None:
        rec, err = prediction_engine_env.predict_observation(sample_feature_row)
        assert err is None
        assert rec is not None
        assert rec.bill_id == "test-telecom-act-2024"
        assert rec.company_isin == "INE002A01018"
        assert rec.predicted_direction == "POSITIVE"
        assert rec.direction_probability["POSITIVE"] == 0.7
        assert rec.predicted_market_moving is True
        assert rec.market_moving_probability == 0.85
        assert rec.predicted_impact_strength == "HIGH"
        assert rec.predicted_confidence == "HIGH"
        assert rec.anticipation_class == "STRONG_EVIDENCE"
        assert rec.anticipation_score == 0.82
        assert "priced in" in rec.decision_reason

        # Verify saved in repository
        assert prediction_engine_env.prediction_repo.exists(
            rec.bill_id, rec.company_isin, rec.event_window
        )

    def test_incremental_execution_caching_and_force_refresh(
        self, prediction_engine_env: FinalPredictionEngine, sample_feature_row: dict
    ) -> None:
        # First execution -> saves
        rec1, _ = prediction_engine_env.predict_observation(sample_feature_row, force_refresh=False)
        assert rec1 is not None

        # Second execution -> hits cache
        with patch.object(prediction_engine_env, "_evaluate_estimator") as mock_eval:
            rec2, _ = prediction_engine_env.predict_observation(sample_feature_row, force_refresh=False)
            assert rec2 is not None
            assert rec2.prediction_id == rec1.prediction_id
            mock_eval.assert_not_called()

        # Force refresh -> recomputes
        with patch.object(prediction_engine_env, "_evaluate_estimator", wraps=prediction_engine_env._evaluate_estimator) as mock_eval:
            rec3, _ = prediction_engine_env.predict_observation(sample_feature_row, force_refresh=True)
            assert rec3 is not None
            assert mock_eval.call_count == 4  # 4 targets evaluated

    def test_version_mismatch_regenerates_prediction(
        self, prediction_engine_env: FinalPredictionEngine, sample_feature_row: dict
    ) -> None:
        # Save a record with an outdated model_version
        pred_id = make_prediction_id(
            sample_feature_row["bill_id"],
            sample_feature_row["company_isin"],
            sample_feature_row["event_window"],
        )
        old_record = PredictionRecord(
            prediction_id=pred_id,
            bill_id=sample_feature_row["bill_id"],
            company_isin=sample_feature_row["company_isin"],
            event_window=sample_feature_row["event_window"],
            predicted_direction="NEUTRAL",
            direction_probability={"NEUTRAL": 1.0},
            predicted_market_moving=False,
            market_moving_probability=0.0,
            predicted_impact_strength="LOW",
            impact_probabilities={"LOW": 1.0},
            predicted_confidence="LOW",
            confidence_probability={"LOW": 1.0},
            anticipation_class="NO_EVIDENCE",
            anticipation_score=0.0,
            model_name={"direction": "lgbm"},
            model_version="v0.1-legacy",  # Stale version
            feature_version="v1.0",
            prediction_timestamp="2025-01-01T00:00:00Z",
            decision_reason="Old",
        )
        prediction_engine_env.prediction_repo.save(old_record)

        # Execution without force_refresh should detect version mismatch and regenerate
        rec, _ = prediction_engine_env.predict_observation(sample_feature_row, force_refresh=False)
        assert rec is not None
        assert rec.model_version == CURRENT_MODEL_VERSION
        assert rec.predicted_direction == "POSITIVE"

    def test_run_all_batch_execution(
        self, prediction_engine_env: FinalPredictionEngine
    ) -> None:
        stats = prediction_engine_env.run_all()
        assert stats["total_candidates"] == 3
        assert stats["predictions_generated"] == 3
        assert stats["predictions_skipped"] == 0
        assert stats["predictions_failed"] == 0
        assert len(stats["records"]) == 3

        # Run again -> should skip all 3
        stats_cached = prediction_engine_env.run_all(force_refresh=False)
        assert stats_cached["predictions_skipped"] == 3
        assert stats_cached["predictions_generated"] == 0

    def test_run_all_with_filters(
        self, prediction_engine_env: FinalPredictionEngine
    ) -> None:
        # Filter by year 2024
        stats_2024 = prediction_engine_env.run_all(year_filter=2024, force_refresh=True)
        assert stats_2024["total_candidates"] == 2

        # Filter by specific bill
        stats_bill = prediction_engine_env.run_all(
            bill_id_filter="data-protection-bill-2023", force_refresh=True
        )
        assert stats_bill["total_candidates"] == 1

        # Filter by specific company
        stats_isin = prediction_engine_env.run_all(
            company_isin_filter="INE009A01021", force_refresh=True
        )
        assert stats_isin["total_candidates"] == 1


class TestPredictionService:
    def test_service_methods(
        self, prediction_engine_env: FinalPredictionEngine, sample_feature_row: dict
    ) -> None:
        service = PredictionService(
            engine=prediction_engine_env,
            repository=prediction_engine_env.prediction_repo,
        )
        # Generate predictions
        res = service.generate_predictions(force_refresh=True)
        assert res["total_candidates"] == 3

        # Single predict
        rec, err = service.predict_observation(sample_feature_row)
        assert rec is not None

        # Query methods
        b_records = service.get_predictions_for_bill("test-telecom-act-2024")
        assert len(b_records) >= 1

        c_records = service.get_predictions_for_company("INE002A01018")
        assert len(c_records) >= 1

        all_preds = service.get_all_predictions()
        assert len(all_preds) >= 1


class TestCliIntegration:
    def test_cmd_generate_predictions_success(
        self, prediction_engine_env: FinalPredictionEngine
    ) -> None:
        with patch("services.prediction.PredictionService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.generate_predictions.return_value = {
                "total_candidates": 2,
                "predictions_generated": 2,
                "predictions_skipped": 0,
                "predictions_failed": 0,
                "models_used": {
                    "direction": "lgbm",
                    "market_moving": "random_forest",
                    "impact_strength": "lgbm",
                    "confidence": "lgbm",
                },
                "target_distributions": {
                    "direction": {"POSITIVE": 2, "NEGATIVE": 0, "NEUTRAL": 0},
                    "market_moving": {"TRUE": 2, "FALSE": 0},
                    "impact_strength": {"HIGH": 2, "LOW": 0, "MEDIUM": 0, "VERY_HIGH": 0},
                    "confidence": {"HIGH": 2, "LOW": 0, "MEDIUM": 0},
                },
                "records": [
                    PredictionRecord(
                        prediction_id="p1",
                        bill_id="bill-1",
                        company_isin="INE1",
                        company_symbol="SYM1",
                        event_window="[-20,+20]",
                        predicted_direction="POSITIVE",
                        direction_probability={"POSITIVE": 0.9},
                        predicted_market_moving=True,
                        market_moving_probability=0.9,
                        predicted_impact_strength="HIGH",
                        impact_probabilities={"HIGH": 0.9},
                        predicted_confidence="HIGH",
                        confidence_probability={"HIGH": 0.9},
                        anticipation_class="STRONG_EVIDENCE",
                        anticipation_score=0.8,
                        model_name={"direction": "lgbm"},
                        model_version="v1.0",
                        feature_version="v1.0",
                        prediction_timestamp="2026-08-16T12:00:00Z",
                        decision_reason="Reason",
                    )
                ],
            }
            mock_service_cls.return_value = mock_service

            args = argparse.Namespace(
                year=2024,
                bill_id=None,
                company_isin=None,
                event_window=None,
                force_refresh=True,
                rebuild=False,
                mode="structured",
            )
            exit_code = cmd_generate_predictions(args)
            assert exit_code == 0

    def test_cmd_generate_predictions_error(self) -> None:
        with patch("services.prediction.PredictionService") as mock_service_cls:
            mock_service = MagicMock()
            mock_service.generate_predictions.side_effect = RuntimeError("Fatal DB error")
            mock_service_cls.return_value = mock_service

            args = argparse.Namespace(
                year=None,
                bill_id="bad-bill",
                company_isin=None,
                event_window=None,
                force_refresh=False,
                rebuild=False,
                mode="structured",
            )
            exit_code = cmd_generate_predictions(args)
            assert exit_code == 1

    def test_model_load_failure_returns_validation_error(
        self, prediction_engine_env: FinalPredictionEngine, sample_feature_row: dict
    ) -> None:
        prediction_engine_env.model_repo.load.side_effect = FileNotFoundError("Missing model.pkl")
        rec, err_rep = prediction_engine_env.predict_observation(sample_feature_row, force_refresh=True)
        assert rec is None
        assert err_rep is not None
        assert not err_rep.is_valid
        assert any("Failed to load model" in e for e in err_rep.errors)

    def test_preprocessor_transform_failure_returns_validation_error(
        self, prediction_engine_env: FinalPredictionEngine, sample_feature_row: dict
    ) -> None:
        bad_preproc = MagicMock()
        bad_preproc.transform.side_effect = ValueError("Incompatible transformer")

        def mock_load_bad(target, model_type):
            est = MockClassifier(["NEGATIVE", "NEUTRAL", "POSITIVE"], [0.1, 0.2, 0.7])
            return est, bad_preproc, ["alpha", "beta"]

        prediction_engine_env.model_repo.load.side_effect = mock_load_bad
        rec, err_rep = prediction_engine_env.predict_observation(sample_feature_row, force_refresh=True)
        assert rec is None
        assert err_rep is not None
        assert not err_rep.is_valid
        assert any("Preprocessor transform failed" in e for e in err_rep.errors)

    def test_estimator_without_predict_proba_fallback(
        self, prediction_engine_env: FinalPredictionEngine
    ) -> None:
        class NonProbaClassifier(BaseEstimator):
            def __init__(self):
                self.classes_ = np.array(["NEGATIVE", "NEUTRAL", "POSITIVE"])
            def predict(self, X):
                return np.array(["POSITIVE"] * len(X))

        non_proba = NonProbaClassifier()
        probs, pred_cls = prediction_engine_env._evaluate_estimator(
            estimator=non_proba,
            X_proc=np.array([[1.0, 2.0]]),
            target="direction",
            label_encoder=None,
        )
        assert pred_cls == "POSITIVE"
        assert probs["POSITIVE"] == 1.0

    def test_run_all_event_window_filter_and_failure_counter(
        self, prediction_engine_env: FinalPredictionEngine
    ) -> None:
        # Window filter matching none
        stats_none = prediction_engine_env.run_all(event_window_filter="[-5,+5]", force_refresh=True)
        assert stats_none["total_candidates"] == 0

        # Prediction failure simulation in run_all
        with patch.object(prediction_engine_env, "predict_observation", return_value=(None, MagicMock())):
            stats_failed = prediction_engine_env.run_all(force_refresh=True)
            assert stats_failed["predictions_failed"] == 3
