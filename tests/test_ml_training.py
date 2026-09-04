"""
tests/test_ml_training.py
==========================
Comprehensive test suite for Task 6.1 — ML Training Engine.

Coverage targets:
  * DatasetBuilder (leakage prevention, chronological sorting, dataset split)
  * ModelRepository (save, load, exists, list_models)
  * MLTrainer (TimeSeriesSplit, model training, hyperparameter search)
  * Prediction pipeline (loaded model produces valid predictions)
  * TrainingReport schema (serialisation / deserialisation)
  * Settings (new ML fields)

Design principles:
  * Every test operates on synthetic in-memory data — no real pipeline required
  * All file I/O uses ``tmp_path`` (pytest's built-in temp directory)
  * External ML libraries (lightgbm, xgboost) are tested for availability
    but tests degrade gracefully if absent
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import TimeSeriesSplit

# Pre-evaluate library availability at import time (fast, no actual import)
_HAS_LIGHTGBM = importlib.util.find_spec("lightgbm") is not None
_HAS_XGBOOST = importlib.util.find_spec("xgboost") is not None

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_synthetic_dataset(
    n_rows: int = 120,
    include_post_event: bool = True,
    seed: int = 0,
) -> pd.DataFrame:
    """
    Generate a synthetic feature dataset that mirrors the real schema.

    Includes both pre-event (training-safe) and post-event (leakage) columns.
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2018-01-01", periods=n_rows, freq="15D")

    df = pd.DataFrame(
        {
            # ---- Metadata ----
            "record_id": [f"bill_{i:04d}|INE{i:06d}|[-5,+5]" for i in range(n_rows)],
            "bill_id": [f"bill_{i:04d}" for i in range(n_rows)],
            "company_isin": [f"INE{i:06d}" for i in range(n_rows)],
            "event_window": "[-5,+5]",
            "bill_title": [f"Test Bill {i}" for i in range(n_rows)],
            "company_name": [f"Company {i}" for i in range(n_rows)],
            "nse_symbol": [f"SYM{i}" for i in range(n_rows)],
            "isin": [f"INE{i:06d}" for i in range(n_rows)],
            "introduction_date": dates,
            "feature_version": "1.0",
            "built_at": "2025-01-01",
            # ---- Pre-event features (training-safe) ----
            "alpha": rng.normal(0, 0.01, n_rows),
            "beta": rng.normal(1.0, 0.3, n_rows),
            "r_squared": rng.uniform(0.1, 0.9, n_rows),
            "residual_variance": rng.uniform(0.0001, 0.005, n_rows),
            "observation_count": rng.integers(60, 120, n_rows),
            "ministry": rng.choice(["Finance", "Agriculture", "Defence"], n_rows),
            "policy_domain": rng.choice(["Fiscal", "Trade", "Social"], n_rows),
            "company_sector": rng.choice(["Banking", "IT", "Energy"], n_rows),
            # ---- Embedding-like features ----
            "finbert_emb_0": rng.normal(0, 1, n_rows),
            "finbert_emb_1": rng.normal(0, 1, n_rows),
            # ---- Targets ----
            "direction": rng.choice(["POSITIVE", "NEGATIVE", "NEUTRAL"], n_rows),
            "market_moving": rng.choice([True, False], n_rows),
            "impact_strength": rng.choice(["LOW", "MEDIUM", "HIGH", "VERY_HIGH"], n_rows),
            "confidence_label": rng.choice(["LOW", "MEDIUM", "HIGH"], n_rows),
        }
    )

    if include_post_event:
        # Post-event / leakage columns
        df["car"] = rng.normal(0, 0.05, n_rows)
        df["final_car"] = rng.normal(0, 0.05, n_rows)
        df["avg_ar"] = rng.normal(0, 0.01, n_rows)
        df["max_ar"] = rng.uniform(0, 0.1, n_rows)
        df["min_ar"] = rng.uniform(-0.1, 0, n_rows)
        df["peak_car_day"] = rng.integers(-5, 5, n_rows)
        df["peak_ar_day"] = rng.integers(-5, 5, n_rows)
        df["t_statistic"] = rng.normal(0, 2, n_rows)
        df["p_value"] = rng.uniform(0, 1, n_rows)
        df["significance_level"] = rng.choice(["1%", "5%", "Not Significant"], n_rows)
        df["effect_size"] = rng.choice(["Small", "Medium", "Large"], n_rows)
        df["confidence_interval_lower"] = rng.normal(-0.1, 0.05, n_rows)
        df["confidence_interval_upper"] = rng.normal(0.1, 0.05, n_rows)
        df["significant_flag"] = rng.choice([True, False], n_rows)
        # Running series columns
        df["ar_day_0"] = rng.normal(0, 0.01, n_rows)
        df["ar_day_1"] = rng.normal(0, 0.01, n_rows)
        df["car_day_0"] = rng.normal(0, 0.02, n_rows)

    return df


@pytest.fixture
def synthetic_df() -> pd.DataFrame:
    """Synthetic feature dataset with post-event columns."""
    return _make_synthetic_dataset(n_rows=120, include_post_event=True)


@pytest.fixture
def synthetic_df_clean() -> pd.DataFrame:
    """Synthetic feature dataset WITHOUT post-event columns."""
    return _make_synthetic_dataset(n_rows=120, include_post_event=False)


@pytest.fixture
def mock_selection_repo(synthetic_df, tmp_path):
    """Mock FeatureSelectionRepository that returns synthetic data."""
    repo = MagicMock()
    repo.load.return_value = synthetic_df
    return repo


@pytest.fixture
def dataset_builder(mock_selection_repo, tmp_path):
    """DatasetBuilder wired to mock repo with tmp output dir."""
    from models.training.dataset_builder import DatasetBuilder

    return DatasetBuilder(
        selection_repo=mock_selection_repo,
        output_dir=tmp_path,
    )


# ---------------------------------------------------------------------------
# 1. DatasetBuilder tests
# ---------------------------------------------------------------------------


class TestDatasetBuilder:
    """Tests for DatasetBuilder — leakage prevention and dataset splits."""

    def test_build_returns_two_dataframes(self, dataset_builder):
        """build() must return training and research DataFrames."""
        df_train, df_research, train_desc, research_desc = dataset_builder.build(mode="structured")
        assert isinstance(df_train, pd.DataFrame)
        assert isinstance(df_research, pd.DataFrame)
        assert len(df_train) > 0
        assert len(df_research) > 0

    def test_research_dataset_has_all_columns(self, dataset_builder, synthetic_df):
        """Research dataset must retain all original columns."""
        _, df_research, _, _ = dataset_builder.build(mode="structured")
        for col in synthetic_df.columns:
            assert col in df_research.columns, f"Research dataset missing column: {col}"

    def test_training_dataset_strips_car_columns(self, dataset_builder):
        """Training dataset must not contain CAR, AR, or statistical columns."""
        leakage_cols = [
            "car", "final_car", "avg_ar", "max_ar", "min_ar",
            "peak_car_day", "peak_ar_day", "t_statistic", "p_value",
            "significance_level", "effect_size",
            "confidence_interval_lower", "confidence_interval_upper",
            "significant_flag",
        ]
        df_train, _, _, _ = dataset_builder.build(mode="structured")
        for col in leakage_cols:
            assert col not in df_train.columns, (
                f"Leakage column '{col}' found in training dataset!"
            )

    def test_training_dataset_strips_running_series(self, dataset_builder):
        """Training dataset must not contain ar_day_* or car_day_* columns."""
        df_train, _, _, _ = dataset_builder.build(mode="structured")
        series_cols = [c for c in df_train.columns
                       if c.startswith("ar_day_") or c.startswith("car_day_")]
        assert series_cols == [], f"Running series columns in training dataset: {series_cols}"

    def test_training_dataset_retains_targets(self, dataset_builder):
        """Training dataset must retain all target label columns (they are supervised targets, not leaked features)."""
        df_train, _, _, _ = dataset_builder.build(mode="structured")
        present = set(df_train.columns)
        # All four target columns must be retained in the training dataset
        assert "direction" in present, "direction missing from training dataset!"
        assert "market_moving" in present, "market_moving missing from training dataset!"
        assert "impact_strength" in present, "impact_strength missing from training dataset!"
        assert "confidence_label" in present, "confidence_label missing from training dataset!"

    def test_training_dataset_retains_pre_event_features(self, dataset_builder):
        """Training dataset must retain pre-event features (alpha, beta, etc.)."""
        pre_event_features = ["alpha", "beta", "r_squared", "residual_variance",
                              "observation_count", "ministry", "policy_domain"]
        df_train, _, _, _ = dataset_builder.build(mode="structured")
        for col in pre_event_features:
            assert col in df_train.columns, f"Pre-event feature '{col}' stripped from training!"

    def test_chronological_sorting(self, dataset_builder, synthetic_df):
        """Training and research datasets must be sorted by introduction_date."""
        df_train, df_research, _, _ = dataset_builder.build(mode="structured")
        # Introduction dates must be non-decreasing
        dates_train = pd.to_datetime(df_train["introduction_date"], errors="coerce")
        assert (dates_train.diff().dropna() >= pd.Timedelta(0)).all(), (
            "Training dataset is not sorted chronologically!"
        )

    def test_row_counts_match(self, dataset_builder, synthetic_df):
        """Training and research datasets should have the same number of rows."""
        df_train, df_research, _, _ = dataset_builder.build(mode="structured")
        assert len(df_train) == len(df_research)

    def test_descriptors_populated(self, dataset_builder):
        """DatasetDescriptors returned by build() must have correct name fields."""
        _, _, train_desc, research_desc = dataset_builder.build(mode="structured")
        assert train_desc.name == "training"
        assert research_desc.name == "research"
        assert train_desc.n_rows > 0
        assert research_desc.n_rows > 0

    def test_research_descriptor_has_empty_removed_columns(self, dataset_builder):
        """Research dataset descriptor should report no removed columns."""
        _, _, _, research_desc = dataset_builder.build(mode="structured")
        assert research_desc.removed_columns == []

    def test_training_descriptor_reports_removed_columns(self, dataset_builder):
        """Training dataset descriptor should list removed post-event columns."""
        _, _, train_desc, _ = dataset_builder.build(mode="structured")
        assert len(train_desc.removed_columns) > 0
        # car should be among removed
        assert "car" in train_desc.removed_columns

    def test_parquet_files_created(self, dataset_builder, tmp_path):
        """Both Parquet files must exist on disk after build()."""
        dataset_builder.build(mode="structured")
        assert (tmp_path / "training_dataset.parquet").is_file()
        assert (tmp_path / "research_dataset.parquet").is_file()

    def test_rebuild_false_loads_existing(self, dataset_builder, tmp_path):
        """Calling build() twice with rebuild=False should load cached files."""
        dataset_builder.build(mode="structured", rebuild=False)
        # Second call — mock repo should NOT be called again
        dataset_builder._selection_repo.reset_mock()
        dataset_builder.build(mode="structured", rebuild=False)
        dataset_builder._selection_repo.load.assert_not_called()

    def test_rebuild_true_reprocesses(self, dataset_builder):
        """build(rebuild=True) must reprocess even when files exist."""
        dataset_builder.build(mode="structured", rebuild=False)
        dataset_builder._selection_repo.reset_mock()
        dataset_builder.build(mode="structured", rebuild=True)
        dataset_builder._selection_repo.load.assert_called_once()

    def test_get_feature_columns_excludes_metadata_and_targets(self, dataset_builder, synthetic_df_clean):
        """get_feature_columns() must exclude known metadata and target columns."""
        feat_cols = dataset_builder.get_feature_columns(synthetic_df_clean)
        for col in ["record_id", "bill_id", "company_isin", "event_window",
                    "direction", "market_moving", "impact_strength", "confidence_label"]:
            assert col not in feat_cols, f"Metadata/target column '{col}' in feature list"

    def test_empty_source_raises_value_error(self, mock_selection_repo, tmp_path):
        """build() must raise ValueError if the source dataset is empty."""
        from models.training.dataset_builder import DatasetBuilder

        mock_selection_repo.load.return_value = pd.DataFrame()
        builder = DatasetBuilder(selection_repo=mock_selection_repo, output_dir=tmp_path)
        with pytest.raises(ValueError, match="empty"):
            builder.build(mode="structured", rebuild=True)


# ---------------------------------------------------------------------------
# 2. POST_EVENT_COLUMNS schema tests
# ---------------------------------------------------------------------------


class TestPostEventSchema:
    """Tests for the leakage column constants in schemas/training_dataset.py."""

    def test_car_in_post_event_columns(self):
        from schemas.training_dataset import POST_EVENT_COLUMNS
        assert "car" in POST_EVENT_COLUMNS

    def test_t_statistic_in_post_event_columns(self):
        from schemas.training_dataset import POST_EVENT_COLUMNS
        assert "t_statistic" in POST_EVENT_COLUMNS

    def test_p_value_in_post_event_columns(self):
        from schemas.training_dataset import POST_EVENT_COLUMNS
        assert "p_value" in POST_EVENT_COLUMNS

    def test_direction_not_in_post_event_columns(self):
        """Target labels must NOT be in POST_EVENT_COLUMNS - they are supervised targets kept in training set."""
        from schemas.training_dataset import POST_EVENT_COLUMNS
        assert "direction" not in POST_EVENT_COLUMNS
        assert "market_moving" not in POST_EVENT_COLUMNS
        assert "impact_strength" not in POST_EVENT_COLUMNS
        assert "confidence_label" not in POST_EVENT_COLUMNS

    def test_ar_prefix_in_post_event_prefixes(self):
        from schemas.training_dataset import POST_EVENT_PREFIXES
        assert "ar_day_" in POST_EVENT_PREFIXES

    def test_car_prefix_in_post_event_prefixes(self):
        from schemas.training_dataset import POST_EVENT_PREFIXES
        assert "car_day_" in POST_EVENT_PREFIXES


# ---------------------------------------------------------------------------
# 3. ModelRepository tests
# ---------------------------------------------------------------------------


class TestModelRepository:
    """Tests for ModelRepository save/load/exists/list_models."""

    @pytest.fixture
    def repo(self, tmp_path):
        from storage.model_repository import ModelRepository
        return ModelRepository(models_dir=tmp_path)

    @pytest.fixture
    def dummy_model(self):
        from sklearn.ensemble import RandomForestClassifier
        rf = RandomForestClassifier(n_estimators=5, random_state=42)
        rf.fit([[1, 2], [3, 4], [5, 6]], [0, 1, 0])
        return rf

    @pytest.fixture
    def dummy_preprocessor(self):
        from sklearn.preprocessing import StandardScaler
        sc = StandardScaler()
        sc.fit([[1, 2], [3, 4]])
        return sc

    def test_exists_returns_false_before_save(self, repo):
        assert repo.exists("direction", "random_forest") is False

    def test_save_creates_model_file(self, repo, dummy_model, dummy_preprocessor, tmp_path):
        repo.save(
            target="direction",
            model_type="random_forest",
            model=dummy_model,
            preprocessor=dummy_preprocessor,
            feature_list=["f1", "f2"],
        )
        model_path = tmp_path / "direction" / "random_forest" / "model.pkl"
        assert model_path.is_file()

    def test_save_creates_preprocessor_file(self, repo, dummy_model, dummy_preprocessor, tmp_path):
        repo.save("direction", "random_forest", dummy_model, dummy_preprocessor, ["f1", "f2"])
        preprocessor_path = tmp_path / "direction" / "random_forest" / "preprocessor.pkl"
        assert preprocessor_path.is_file()

    def test_save_creates_features_json(self, repo, dummy_model, dummy_preprocessor, tmp_path):
        repo.save("direction", "random_forest", dummy_model, dummy_preprocessor, ["f1", "f2"])
        features_path = tmp_path / "direction" / "random_forest" / "features.json"
        assert features_path.is_file()
        data = json.loads(features_path.read_text())
        assert data["features"] == ["f1", "f2"]

    def test_save_creates_metadata_json(self, repo, dummy_model, dummy_preprocessor, tmp_path):
        repo.save("direction", "random_forest", dummy_model, dummy_preprocessor, ["f1", "f2"])
        meta_path = tmp_path / "direction" / "random_forest" / "metadata.json"
        assert meta_path.is_file()

    def test_exists_returns_true_after_save(self, repo, dummy_model, dummy_preprocessor):
        repo.save("direction", "random_forest", dummy_model, dummy_preprocessor, ["f1"])
        assert repo.exists("direction", "random_forest") is True

    def test_load_returns_correct_model_type(self, repo, dummy_model, dummy_preprocessor):
        from sklearn.ensemble import RandomForestClassifier
        repo.save("direction", "random_forest", dummy_model, dummy_preprocessor, ["f1", "f2"])
        model, _, _ = repo.load("direction", "random_forest")
        assert isinstance(model, RandomForestClassifier)

    def test_load_returns_feature_list(self, repo, dummy_model, dummy_preprocessor):
        repo.save("direction", "random_forest", dummy_model, dummy_preprocessor, ["feat_a", "feat_b"])
        _, _, feature_list = repo.load("direction", "random_forest")
        assert feature_list == ["feat_a", "feat_b"]

    def test_list_models_empty_initially(self, repo):
        assert repo.list_models() == []

    def test_list_models_after_multiple_saves(self, repo, dummy_model, dummy_preprocessor):
        repo.save("direction", "random_forest", dummy_model, dummy_preprocessor, ["f1"])
        repo.save("market_moving", "random_forest", dummy_model, dummy_preprocessor, ["f1"])
        results = repo.list_models()
        assert ("direction", "random_forest") in results
        assert ("market_moving", "random_forest") in results

    def test_list_models_sorted(self, repo, dummy_model, dummy_preprocessor):
        repo.save("impact_strength", "random_forest", dummy_model, dummy_preprocessor, ["f1"])
        repo.save("confidence", "random_forest", dummy_model, dummy_preprocessor, ["f1"])
        results = repo.list_models()
        names = [r[0] for r in results]
        assert names == sorted(names)

    def test_invalid_target_raises_error(self, repo, dummy_model, dummy_preprocessor):
        with pytest.raises(ValueError, match="Unknown target"):
            repo.save("invalid_target", "random_forest", dummy_model, dummy_preprocessor, [])

    def test_invalid_model_type_raises_error(self, repo, dummy_model, dummy_preprocessor):
        with pytest.raises(ValueError, match="Unknown model_type"):
            repo.save("direction", "neural_net", dummy_model, dummy_preprocessor, [])

    def test_load_missing_model_raises_file_not_found(self, repo):
        with pytest.raises(FileNotFoundError):
            repo.load("direction", "lgbm")

    def test_exists_with_invalid_target_returns_false(self, repo):
        assert repo.exists("invalid_target", "lgbm") is False

    def test_save_with_report(self, repo, dummy_model, dummy_preprocessor, tmp_path):
        """Saving with a TrainingReport should create training_report.json."""
        from schemas.training_report import TrainingReport
        report = TrainingReport(
            target="direction",
            model_type="random_forest",
            feature_selection_mode="structured",
            feature_count=2,
            feature_list=["f1", "f2"],
            training_samples=100,
            validation_samples=20,
            class_distribution={"POSITIVE": 30, "NEGATIVE": 30, "NEUTRAL": 40},
            best_hyperparameters={},
            mean_train_accuracy=0.85,
            mean_val_accuracy=0.72,
            mean_val_f1_macro=0.68,
            n_splits=3,
        )
        repo.save("direction", "random_forest", dummy_model, dummy_preprocessor, ["f1", "f2"],
                  report=report)
        report_path = tmp_path / "direction" / "random_forest" / "training_report.json"
        assert report_path.is_file()

    def test_load_report_returns_dict(self, repo, dummy_model, dummy_preprocessor, tmp_path):
        from schemas.training_report import TrainingReport
        report = TrainingReport(
            target="direction", model_type="random_forest",
            feature_selection_mode="structured", feature_count=1,
            feature_list=["f1"], training_samples=50, validation_samples=10,
            class_distribution={}, best_hyperparameters={},
            mean_train_accuracy=0.8, mean_val_accuracy=0.7, mean_val_f1_macro=0.65,
            n_splits=3,
        )
        repo.save("direction", "random_forest", dummy_model, dummy_preprocessor, ["f1"],
                  report=report)
        loaded = repo.load_report("direction", "random_forest")
        assert isinstance(loaded, dict)
        assert loaded["target"] == "direction"
        assert loaded["model_type"] == "random_forest"

    def test_load_report_returns_none_when_missing(self, repo):
        # Save without report
        from sklearn.ensemble import RandomForestClassifier
        m = RandomForestClassifier(n_estimators=2).fit([[1], [2]], [0, 1])
        repo.save("direction", "random_forest", m, None, ["f1"])
        loaded = repo.load_report("direction", "random_forest")
        # Will be None since no report was provided
        assert loaded is None


# ---------------------------------------------------------------------------
# 4. TrainingReport schema tests
# ---------------------------------------------------------------------------


class TestTrainingReportSchema:
    """Tests for TrainingReport and FoldResult serialisation."""

    def _make_report(self, **kwargs) -> Any:
        from schemas.training_report import FoldResult, TrainingReport
        folds = [
            FoldResult(
                fold_index=0,
                train_samples=80,
                val_samples=20,
                train_accuracy=0.85,
                val_accuracy=0.72,
                val_f1_macro=0.68,
            )
        ]
        defaults = dict(
            target="direction",
            model_type="lgbm",
            feature_selection_mode="structured",
            feature_count=10,
            feature_list=[f"f{i}" for i in range(10)],
            training_samples=100,
            validation_samples=20,
            class_distribution={"POSITIVE": 30, "NEGATIVE": 30, "NEUTRAL": 40},
            best_hyperparameters={"n_estimators": 200, "max_depth": 6},
            mean_train_accuracy=0.85,
            mean_val_accuracy=0.72,
            mean_val_f1_macro=0.68,
            n_splits=3,
            folds=folds,
        )
        defaults.update(kwargs)
        return TrainingReport(**defaults)

    def test_to_dict_contains_required_fields(self):
        report = self._make_report()
        d = report.to_dict()
        required = [
            "target", "model_type", "feature_selection_mode", "feature_count",
            "feature_list", "training_samples", "validation_samples",
            "class_distribution", "best_hyperparameters",
            "mean_train_accuracy", "mean_val_accuracy", "mean_val_f1_macro",
            "n_splits", "folds", "trained_at",
        ]
        for field in required:
            assert field in d, f"Missing field in TrainingReport.to_dict(): {field}"

    def test_to_dict_folds_serialised(self):
        report = self._make_report()
        d = report.to_dict()
        assert isinstance(d["folds"], list)
        assert len(d["folds"]) == 1
        fold = d["folds"][0]
        assert fold["fold_index"] == 0
        assert fold["train_samples"] == 80

    def test_from_dict_roundtrip(self):
        from schemas.training_report import TrainingReport
        report = self._make_report()
        d = report.to_dict()
        restored = TrainingReport.from_dict(d)
        assert restored.target == report.target
        assert restored.model_type == report.model_type
        assert restored.mean_val_accuracy == report.mean_val_accuracy
        assert len(restored.folds) == len(report.folds)

    def test_trained_at_is_iso_string(self):
        report = self._make_report()
        # Must be parseable as a datetime
        from datetime import datetime
        dt = datetime.fromisoformat(report.trained_at.replace("Z", "+00:00"))
        assert dt is not None

    def test_json_serialisable(self):
        report = self._make_report()
        d = report.to_dict()
        # Should not raise
        json_str = json.dumps(d, default=str)
        restored = json.loads(json_str)
        assert restored["target"] == "direction"


# ---------------------------------------------------------------------------
# 5. TimeSeriesSplit chronological validation tests
# ---------------------------------------------------------------------------


class TestTimeSeriesSplitValidation:
    """Verify that TimeSeriesSplit is truly chronological (no random splits)."""

    def test_timeseries_split_is_monotonic(self):
        """Validation indices must always come AFTER training indices."""
        X = np.arange(100).reshape(-1, 1)
        tscv = TimeSeriesSplit(n_splits=5)
        for train_idx, val_idx in tscv.split(X):
            assert max(train_idx) < min(val_idx), (
                "TimeSeriesSplit produced non-chronological fold: "
                f"max(train)={max(train_idx)} >= min(val)={min(val_idx)}"
            )

    def test_timeseries_split_grows_training_set(self):
        """Each successive fold should have a larger training set."""
        X = np.arange(100).reshape(-1, 1)
        tscv = TimeSeriesSplit(n_splits=5)
        prev_train_size = 0
        for train_idx, _ in tscv.split(X):
            assert len(train_idx) >= prev_train_size
            prev_train_size = len(train_idx)

    def test_no_overlap_between_train_and_val(self):
        """Train and val sets must be disjoint in every fold."""
        X = np.arange(100).reshape(-1, 1)
        tscv = TimeSeriesSplit(n_splits=5)
        for train_idx, val_idx in tscv.split(X):
            overlap = set(train_idx) & set(val_idx)
            assert len(overlap) == 0, f"Train/val overlap in fold: {overlap}"

    def test_5_folds_produces_5_splits(self):
        X = np.arange(60).reshape(-1, 1)
        tscv = TimeSeriesSplit(n_splits=5)
        splits = list(tscv.split(X))
        assert len(splits) == 5


# ---------------------------------------------------------------------------
# 6. MLTrainer tests (with mocked repositories)
# ---------------------------------------------------------------------------


class TestMLTrainer:
    """Tests for MLTrainer training logic with synthetic data."""

    @pytest.fixture
    def small_df(self):
        """Small synthetic dataset (30 rows) for fast training."""
        return _make_synthetic_dataset(n_rows=30, include_post_event=True)

    @pytest.fixture
    def mock_builder(self, small_df, tmp_path):
        """Mock DatasetBuilder that returns synthetic data."""
        from models.training.dataset_builder import DatasetBuilder
        from schemas.training_dataset import DatasetDescriptor

        builder = MagicMock(spec=DatasetBuilder)
        # Strip post-event cols from training df
        post_event = [
            "car", "final_car", "avg_ar", "max_ar", "min_ar",
            "peak_car_day", "peak_ar_day", "t_statistic", "p_value",
            "significance_level", "effect_size", "confidence_interval_lower",
            "confidence_interval_upper", "significant_flag",
            "ar_day_0", "ar_day_1", "car_day_0",
        ]
        df_train = small_df.drop(columns=[c for c in post_event if c in small_df.columns])
        df_research = small_df.copy()

        train_desc = DatasetDescriptor(
            name="training", path=str(tmp_path / "training_dataset.parquet"),
            n_rows=len(df_train), n_features=5,
        )
        research_desc = DatasetDescriptor(
            name="research", path=str(tmp_path / "research_dataset.parquet"),
            n_rows=len(df_research), n_features=20,
        )
        builder.build.return_value = (df_train, df_research, train_desc, research_desc)

        # get_feature_columns returns numeric + categorical features
        feature_cols = [
            c for c in df_train.columns
            if c not in {
                "record_id", "bill_id", "company_isin", "event_window",
                "bill_title", "company_name", "nse_symbol", "isin",
                "introduction_date", "feature_version", "built_at",
                "direction", "market_moving", "impact_strength", "confidence_label",
            }
        ]
        builder.get_feature_columns.return_value = feature_cols
        return builder

    @pytest.fixture
    def mock_repo(self, tmp_path):
        """Mock ModelRepository."""
        from storage.model_repository import ModelRepository
        return ModelRepository(models_dir=tmp_path)

    @pytest.fixture
    def trainer(self, mock_builder, mock_repo):
        from models.training.trainer import MLTrainer
        return MLTrainer(
            dataset_builder=mock_builder,
            model_repo=mock_repo,
            n_splits=2,
            random_seed=42,
            mode="structured",
            n_jobs=1,
            verbose=False,
        )

    def test_train_random_forest_direction(self, trainer, mock_repo):
        """Training a single Random Forest on direction should succeed."""
        report = trainer.train_target("direction", "random_forest")
        assert report is not None
        assert report.target == "direction"
        assert report.model_type == "random_forest"
        assert report.training_samples > 0
        assert 0.0 <= report.mean_val_accuracy <= 1.0

    def test_training_report_has_folds(self, trainer):
        """Report must contain at least 1 fold result."""
        report = trainer.train_target("direction", "random_forest")
        assert len(report.folds) >= 1

    def test_training_report_fold_val_samples_positive(self, trainer):
        """Each fold must have positive validation sample count."""
        report = trainer.train_target("direction", "random_forest")
        for fold in report.folds:
            assert fold.val_samples > 0

    def test_model_saved_to_repo(self, trainer, mock_repo):
        """Model must exist in the repository after training."""
        trainer.train_target("direction", "random_forest")
        assert mock_repo.exists("direction", "random_forest")

    def test_report_saved_to_json(self, trainer, mock_repo, tmp_path):
        """training_report.json must exist after training."""
        trainer.train_target("direction", "random_forest")
        report_path = tmp_path / "direction" / "random_forest" / "training_report.json"
        assert report_path.is_file()

    def test_report_json_has_required_fields(self, trainer, mock_repo, tmp_path):
        """training_report.json must include all spec-required fields."""
        trainer.train_target("direction", "random_forest")
        report_path = tmp_path / "direction" / "random_forest" / "training_report.json"
        data = json.loads(report_path.read_text())
        required_fields = [
            "target", "model_type", "best_hyperparameters",
            "mean_train_accuracy", "mean_val_accuracy", "mean_val_f1_macro",
            "training_samples", "validation_samples",
            "feature_count", "feature_list", "n_splits", "trained_at",
        ]
        for field in required_fields:
            assert field in data, f"Missing field in training_report.json: {field}"

    def test_train_market_moving_target(self, trainer):
        """Training on boolean market_moving target should succeed."""
        report = trainer.train_target("market_moving", "random_forest")
        assert report.target == "market_moving"
        assert report.training_samples > 0

    def test_train_impact_strength_target(self, trainer):
        """Training on 4-class impact_strength target should succeed."""
        report = trainer.train_target("impact_strength", "random_forest")
        assert report.target == "impact_strength"

    def test_train_confidence_target(self, trainer):
        """Training on confidence target should succeed."""
        report = trainer.train_target("confidence", "random_forest")
        assert report.target == "confidence"

    def test_train_all_returns_nested_dict(self, trainer):
        """train_all() must return a dict of {target: {model_type: report}}."""
        all_reports = trainer.train_all()
        # At least some targets should be trained
        assert isinstance(all_reports, dict)

    def test_feature_list_in_report_is_not_empty(self, trainer):
        """The feature list in the training report must be non-empty."""
        report = trainer.train_target("direction", "random_forest")
        assert len(report.feature_list) > 0

    def test_class_distribution_in_report(self, trainer):
        """class_distribution in the report must be non-empty."""
        report = trainer.train_target("direction", "random_forest")
        assert isinstance(report.class_distribution, dict)
        assert len(report.class_distribution) > 0


# ---------------------------------------------------------------------------
# 7. Prediction pipeline test
# ---------------------------------------------------------------------------


class TestPredictionPipeline:
    """Test that a saved model can be loaded and used for inference."""

    def test_predict_after_save_load(self, tmp_path):
        """Save a model, load it, then predict on new data — must work end-to-end."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder

        # Fit a simple model
        X_train = pd.DataFrame({"f1": [1.0, 2.0, 3.0, 4.0, 5.0],
                                 "f2": [0.1, 0.2, 0.3, 0.4, 0.5]})
        y_raw = ["POSITIVE", "NEGATIVE", "NEUTRAL", "POSITIVE", "NEGATIVE"]

        le = LabelEncoder()
        y = le.fit_transform(y_raw)

        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        preprocessor = ColumnTransformer(
            [("num", SimpleImputer(strategy="median"), ["f1", "f2"])]
        )
        X_proc = preprocessor.fit_transform(X_train)

        clf = RandomForestClassifier(n_estimators=5, random_state=42)
        clf.fit(X_proc, y)

        model_bundle = {"estimator": clf, "label_encoder": le}

        # Save via repo
        from storage.model_repository import ModelRepository
        repo = ModelRepository(models_dir=tmp_path)
        repo.save(
            target="direction",
            model_type="random_forest",
            model=model_bundle,
            preprocessor=preprocessor,
            feature_list=["f1", "f2"],
        )

        # Load
        loaded_bundle, loaded_preprocessor, loaded_features = repo.load("direction", "random_forest")

        # Predict
        from models.training.trainer import MLTrainer
        X_test = pd.DataFrame({"f1": [2.5, 3.5], "f2": [0.25, 0.35]})
        predictions = MLTrainer.predict(loaded_bundle, loaded_preprocessor, X_test)

        assert len(predictions) == 2
        assert all(p in ["POSITIVE", "NEGATIVE", "NEUTRAL"] for p in predictions)

    def test_predict_returns_valid_labels_for_market_moving(self, tmp_path):
        """Predictions for market_moving (boolean) must be valid class labels."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder

        X_train = pd.DataFrame({"f1": np.random.randn(20)})
        y_raw = ["True", "False"] * 10
        le = LabelEncoder()
        y = le.fit_transform(y_raw)

        from sklearn.compose import ColumnTransformer
        from sklearn.impute import SimpleImputer
        prep = ColumnTransformer([("n", SimpleImputer(), ["f1"])])
        X_proc = prep.fit_transform(X_train)

        clf = RandomForestClassifier(n_estimators=3, random_state=0)
        clf.fit(X_proc, y)
        bundle = {"estimator": clf, "label_encoder": le}

        from storage.model_repository import ModelRepository
        repo = ModelRepository(models_dir=tmp_path)
        repo.save("market_moving", "random_forest", bundle, prep, ["f1"])
        loaded_bundle, loaded_prep, _ = repo.load("market_moving", "random_forest")

        from models.training.trainer import MLTrainer
        X_test = pd.DataFrame({"f1": [0.5, -0.5]})
        preds = MLTrainer.predict(loaded_bundle, loaded_prep, X_test)
        assert all(p in ["True", "False"] for p in preds)


# ---------------------------------------------------------------------------
# 8. Settings tests
# ---------------------------------------------------------------------------


class TestMLSettings:
    """Verify new ML configuration fields in Settings."""

    def test_ml_data_dir_is_path(self):
        from config.settings import settings
        assert hasattr(settings, "ML_DATA_DIR")
        assert isinstance(settings.ML_DATA_DIR, Path)

    def test_ml_models_dir_is_path(self):
        from config.settings import settings
        assert isinstance(settings.ML_MODELS_DIR, Path)

    def test_ml_default_mode_is_string(self):
        from config.settings import settings
        assert isinstance(settings.ML_DEFAULT_MODE, str)
        assert settings.ML_DEFAULT_MODE in [
            "structured", "finbert", "legal",
            "structured-finbert", "structured-legal", "hybrid",
        ]

    def test_ml_n_splits_is_positive_int(self):
        from config.settings import settings
        assert isinstance(settings.ML_N_SPLITS, int)
        assert settings.ML_N_SPLITS >= 2

    def test_ml_random_seed_is_int(self):
        from config.settings import settings
        assert isinstance(settings.ML_RANDOM_SEED, int)

    def test_ml_data_dir_under_data(self):
        from config.settings import settings
        assert "ml" in str(settings.ML_DATA_DIR)

    def test_ml_models_dir_under_project(self):
        from config.settings import settings
        assert settings.ML_MODELS_DIR.is_absolute()


# ---------------------------------------------------------------------------
# 9. LightGBM availability test (graceful degradation)
# ---------------------------------------------------------------------------


class TestLibraryAvailability:
    """Verify graceful import behaviour for optional ML libraries."""

    def test_lgbm_importable(self):
        """LightGBM should be importable (it is in requirements.txt)."""
        if not _HAS_LIGHTGBM:
            pytest.skip("lightgbm not installed — skipping availability check")
        import lightgbm  # noqa: F401
        assert True

    def test_xgboost_importable(self):
        """XGBoost should be importable (it is in requirements.txt)."""
        if not _HAS_XGBOOST:
            pytest.skip("xgboost not installed — skipping availability check")
        import xgboost  # noqa: F401
        assert True

    def test_joblib_importable(self):
        import joblib  # noqa: F401

    def test_sklearn_timeseriessplit_importable(self):
        from sklearn.model_selection import TimeSeriesSplit  # noqa: F401

    def test_sklearn_gridsearchcv_importable(self):
        from sklearn.model_selection import GridSearchCV  # noqa: F401


# ---------------------------------------------------------------------------
# 10. LightGBM and XGBoost training (skipped if not installed)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_LIGHTGBM, reason="lightgbm not installed")
class TestLightGBMTraining:
    """Test LightGBM training path (skipped if not installed)."""

    @pytest.fixture
    def small_training_df(self):
        return _make_synthetic_dataset(n_rows=40, include_post_event=False)

    @pytest.fixture
    def lgbm_trainer(self, small_training_df, tmp_path):
        from models.training.dataset_builder import DatasetBuilder
        from models.training.trainer import MLTrainer
        from schemas.training_dataset import DatasetDescriptor
        from storage.model_repository import ModelRepository

        builder = MagicMock(spec=DatasetBuilder)
        feature_cols = [
            c for c in small_training_df.columns
            if c not in {
                "record_id", "bill_id", "company_isin", "event_window",
                "bill_title", "company_name", "nse_symbol", "isin",
                "introduction_date", "feature_version", "built_at",
                "direction", "market_moving", "impact_strength", "confidence_label",
            }
        ]
        train_desc = DatasetDescriptor(
            name="training",
            path=str(tmp_path / "training_dataset.parquet"),
            n_rows=len(small_training_df), n_features=len(feature_cols),
        )
        builder.build.return_value = (
            small_training_df, small_training_df, train_desc, train_desc
        )
        builder.get_feature_columns.return_value = feature_cols

        repo = ModelRepository(models_dir=tmp_path)
        return MLTrainer(
            dataset_builder=builder,
            model_repo=repo,
            n_splits=2,
            random_seed=42,
            mode="structured",
            n_jobs=1,
            verbose=False,
        )

    def test_lgbm_direction_trains_successfully(self, lgbm_trainer, tmp_path):
        report = lgbm_trainer.train_target("direction", "lgbm")
        assert report.model_type == "lgbm"
        assert report.training_samples > 0

    def test_lgbm_model_saved(self, lgbm_trainer, tmp_path):
        lgbm_trainer.train_target("direction", "lgbm")
        assert (tmp_path / "direction" / "lgbm" / "model.pkl").is_file()


@pytest.mark.skipif(not _HAS_XGBOOST, reason="xgboost not installed")
class TestXGBoostTraining:
    """Test XGBoost training path (skipped if not installed)."""

    @pytest.fixture
    def xgb_trainer(self, tmp_path):
        from models.training.dataset_builder import DatasetBuilder
        from models.training.trainer import MLTrainer
        from schemas.training_dataset import DatasetDescriptor
        from storage.model_repository import ModelRepository

        df = _make_synthetic_dataset(n_rows=40, include_post_event=False)
        builder = MagicMock(spec=DatasetBuilder)
        feature_cols = [
            c for c in df.columns
            if c not in {
                "record_id", "bill_id", "company_isin", "event_window",
                "bill_title", "company_name", "nse_symbol", "isin",
                "introduction_date", "feature_version", "built_at",
                "direction", "market_moving", "impact_strength", "confidence_label",
            }
        ]
        desc = DatasetDescriptor(
            name="training", path=str(tmp_path / "td.parquet"),
            n_rows=len(df), n_features=len(feature_cols),
        )
        builder.build.return_value = (df, df, desc, desc)
        builder.get_feature_columns.return_value = feature_cols

        repo = ModelRepository(models_dir=tmp_path)
        return MLTrainer(
            dataset_builder=builder, model_repo=repo,
            n_splits=2, random_seed=42, mode="structured",
            n_jobs=1, verbose=False,
        )

    def test_xgboost_direction_trains_successfully(self, xgb_trainer, tmp_path):
        report = xgb_trainer.train_target("direction", "xgboost")
        assert report.model_type == "xgboost"
        assert report.training_samples > 0

    def test_xgboost_model_saved(self, xgb_trainer, tmp_path):
        xgb_trainer.train_target("direction", "xgboost")
        assert (tmp_path / "direction" / "xgboost" / "model.pkl").is_file()
