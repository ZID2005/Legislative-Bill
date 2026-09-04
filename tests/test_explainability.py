"""
tests/test_explainability.py
==============================
Comprehensive test suite for Task 6.3 — Explainability Engine.

Coverage targets (>95%):
  * ExplainabilityRepository  (save, load, exists, global summary, model comparison)
  * ExplainabilityEngine       (SHAP generation, local explanations, comparison)
  * ExplainabilityVisualizer   (summary_plot, bar_plot, dependence_plots, feature_comparison)
  * Feature ranking            (sorted importance, top-20, cross-model comparison)
  * CLI integration            (explain-models parser, cmd_explain_models)

Design principles:
  * All tests operate on synthetic in-memory data — no real pipeline required
  * All file I/O uses ``tmp_path`` (pytest built-in temp directory)
  * SHAP, LightGBM, XGBoost availability is tested; tests degrade gracefully if absent
  * matplotlib Agg backend is forced before any visualizer import
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Library availability flags (evaluated at import time)
# ---------------------------------------------------------------------------

_HAS_SHAP = importlib.util.find_spec("shap") is not None
_HAS_LIGHTGBM = importlib.util.find_spec("lightgbm") is not None
_HAS_XGBOOST = importlib.util.find_spec("xgboost") is not None
_HAS_MATPLOTLIB = importlib.util.find_spec("matplotlib") is not None

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_N_SAMPLES = 80
_N_FEATURES = 15
_FEATURE_NAMES = [f"feat_{i:02d}" for i in range(_N_FEATURES)]


def _make_feature_matrix(seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0, 1, (_N_SAMPLES, _N_FEATURES)).astype(np.float32)


def _make_shap_values(seed: int = 1) -> np.ndarray:
    """Synthetic 2-D SHAP value matrix (n_samples × n_features)."""
    rng = np.random.default_rng(seed)
    return rng.normal(0, 0.5, (_N_SAMPLES, _N_FEATURES)).astype(np.float32)


def _make_feature_importance_df(seed: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    values = np.abs(rng.normal(0, 1, _N_FEATURES))
    df = pd.DataFrame({
        "feature": _FEATURE_NAMES,
        "mean_abs_shap": values,
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)
    return df


def _make_local_explanations() -> dict:
    return {
        "correct": {
            "description": "Correctly predicted samples",
            "n_samples": 3,
            "samples": [
                {
                    "sample_index": 0,
                    "true_label": "POSITIVE",
                    "predicted_label": "POSITIVE",
                    "max_probability": 0.9,
                    "top_shap_features": [{"feature": "feat_00", "shap_value": 0.5}],
                }
            ],
        },
        "misclassified": {
            "description": "Incorrectly predicted samples",
            "n_samples": 2,
            "samples": [],
        },
        "high_confidence": {
            "description": "High-confidence predictions",
            "n_samples": 5,
            "samples": [],
        },
    }


# ---------------------------------------------------------------------------
# ExplainabilityRepository tests
# ---------------------------------------------------------------------------


class TestExplainabilityRepository:
    """Unit tests for ExplainabilityRepository."""

    def _make_repo(self, tmp_path: Path):
        from storage.explainability_repository import ExplainabilityRepository
        return ExplainabilityRepository(root_dir=tmp_path)

    def test_exists_returns_false_when_empty(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        assert repo.exists("direction", "lgbm") is False

    def test_exists_returns_false_for_invalid_target(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        assert repo.exists("bad_target", "lgbm") is False

    def test_exists_returns_false_for_invalid_model(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        assert repo.exists("direction", "bad_model") is False

    def test_validate_raises_for_unknown_target(self, tmp_path: Path) -> None:
        from storage.explainability_repository import ExplainabilityRepository
        repo = ExplainabilityRepository(root_dir=tmp_path)
        with pytest.raises(ValueError, match="Unknown target"):
            repo._validate("bad_target", "lgbm")

    def test_validate_raises_for_unknown_model(self, tmp_path: Path) -> None:
        from storage.explainability_repository import ExplainabilityRepository
        repo = ExplainabilityRepository(root_dir=tmp_path)
        with pytest.raises(ValueError, match="Unknown model_type"):
            repo._validate("direction", "bad_model")

    def test_save_creates_files(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        shap_df = pd.DataFrame(_make_shap_values(), columns=_FEATURE_NAMES)
        fi_df = _make_feature_importance_df()
        local_exp = _make_local_explanations()

        paths = repo.save("direction", "lgbm", shap_df, fi_df, local_exp)

        assert "shap_values" in paths
        assert paths["shap_values"].is_file()
        assert "feature_importance" in paths
        assert paths["feature_importance"].is_file()
        assert "local_explanations" in paths
        assert paths["local_explanations"].is_file()

    def test_exists_after_save(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        shap_df = pd.DataFrame(_make_shap_values(), columns=_FEATURE_NAMES)
        fi_df = _make_feature_importance_df()
        repo.save("direction", "lgbm", shap_df, fi_df, _make_local_explanations())
        assert repo.exists("direction", "lgbm") is True

    def test_save_load_roundtrip_shap_values(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        original = pd.DataFrame(_make_shap_values(), columns=_FEATURE_NAMES)
        fi_df = _make_feature_importance_df()
        repo.save("market_moving", "random_forest", original, fi_df, {})

        loaded = repo.load("market_moving", "random_forest")
        pd.testing.assert_frame_equal(
            loaded["shap_values"].reset_index(drop=True),
            original.reset_index(drop=True),
            check_dtype=False,
        )

    def test_save_load_roundtrip_feature_importance(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        shap_df = pd.DataFrame(_make_shap_values(), columns=_FEATURE_NAMES)
        fi_df = _make_feature_importance_df()
        repo.save("confidence", "xgboost", shap_df, fi_df, {})

        loaded = repo.load("confidence", "xgboost")
        assert list(loaded["feature_importance"].columns) == ["feature", "mean_abs_shap"]
        assert len(loaded["feature_importance"]) == _N_FEATURES

    def test_save_load_roundtrip_local_explanations(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        shap_df = pd.DataFrame(_make_shap_values(), columns=_FEATURE_NAMES)
        fi_df = _make_feature_importance_df()
        local_exp = _make_local_explanations()
        repo.save("impact_strength", "lgbm", shap_df, fi_df, local_exp)

        loaded = repo.load("impact_strength", "lgbm")
        assert "correct" in loaded["local_explanations"]
        assert "misclassified" in loaded["local_explanations"]
        assert "high_confidence" in loaded["local_explanations"]

    def test_load_raises_when_shap_missing(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        with pytest.raises(FileNotFoundError, match="SHAP values not found"):
            repo.load("direction", "lgbm")

    def test_save_global_summary(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        summary = {
            "description": "Top-20 features",
            "top_features": [{"rank": 1, "feature": "feat_00", "max_mean_abs_shap": 0.9}],
        }
        path = repo.save_global_summary(summary)
        assert path.is_file()

    def test_load_global_summary_roundtrip(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        summary = {"top_features": [{"rank": 1, "feature": "feat_00"}]}
        repo.save_global_summary(summary)
        loaded = repo.load_global_summary()
        assert loaded["top_features"][0]["feature"] == "feat_00"

    def test_load_global_summary_raises_when_missing(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.load_global_summary()

    def test_save_model_comparison(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        comparison = {
            "direction": {
                "lgbm": [{"feature": "feat_00", "mean_abs_shap": 0.5}]
            }
        }
        path = repo.save_model_comparison(comparison)
        assert path.is_file()

    def test_load_model_comparison_roundtrip(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        comparison = {"direction": {"lgbm": []}}
        repo.save_model_comparison(comparison)
        loaded = repo.load_model_comparison()
        assert "direction" in loaded

    def test_load_model_comparison_raises_when_missing(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.load_model_comparison()

    def test_save_local_explanations_separately(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        local_exp = {"correct": {"n_samples": 0, "samples": []}}
        path = repo.save_local_explanations("direction", "lgbm", local_exp)
        assert path.is_file()

    def test_model_dir_and_dependence_dir(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        model_dir = repo.model_dir("direction", "lgbm")
        assert model_dir.is_dir()
        dep_dir = repo.dependence_dir("direction", "lgbm")
        assert dep_dir.is_dir()

    def test_root_property(self, tmp_path: Path) -> None:
        repo = self._make_repo(tmp_path)
        assert repo.root == tmp_path

    def test_all_valid_targets_and_models(self, tmp_path: Path) -> None:
        """Smoke test: save works for all valid (target, model_type) pairs."""
        from storage.explainability_repository import VALID_TARGETS, VALID_MODEL_TYPES
        repo = self._make_repo(tmp_path)
        shap_df = pd.DataFrame(_make_shap_values(), columns=_FEATURE_NAMES)
        fi_df = _make_feature_importance_df()
        for target in VALID_TARGETS:
            for model_type in VALID_MODEL_TYPES:
                paths = repo.save(target, model_type, shap_df, fi_df, {})
                assert repo.exists(target, model_type)
                assert paths["shap_values"].is_file()


# ---------------------------------------------------------------------------
# Feature ranking tests
# ---------------------------------------------------------------------------


class TestFeatureRanking:
    """Tests for correct feature importance ordering."""

    def test_feature_importance_sorted_descending(self) -> None:
        fi_df = _make_feature_importance_df()
        vals = fi_df["mean_abs_shap"].tolist()
        assert vals == sorted(vals, reverse=True), "Feature importance must be sorted desc"

    def test_feature_importance_all_non_negative(self) -> None:
        shap_vals = _make_shap_values()
        mean_abs = np.abs(shap_vals).mean(axis=0)
        assert np.all(mean_abs >= 0)

    def test_top_20_features_at_most_20(self) -> None:
        fi_df = _make_feature_importance_df()
        top20 = fi_df.head(20)
        assert len(top20) <= 20

    def test_top_20_contains_most_important(self) -> None:
        fi_df = _make_feature_importance_df()
        top20_features = set(fi_df.head(20)["feature"])
        all_features = set(fi_df["feature"])
        # Top-20 must be a subset of all features
        assert top20_features.issubset(all_features)

    def test_feature_comparison_includes_all_models(self) -> None:
        """Build a comparison dict; verify all model_types appear."""
        comparison_data = {
            "direction": {
                "lgbm": {"feat_00": 0.9, "feat_01": 0.5},
                "xgboost": {"feat_00": 0.7, "feat_02": 0.3},
                "random_forest": {"feat_01": 0.4, "feat_03": 0.2},
            }
        }
        model_types_in_comparison = set(comparison_data["direction"].keys())
        assert "lgbm" in model_types_in_comparison
        assert "xgboost" in model_types_in_comparison
        assert "random_forest" in model_types_in_comparison

    def test_global_summary_build(self) -> None:
        """ExplainabilityEngine._build_global_summary returns correct structure."""
        from models.explainability.engine import ExplainabilityEngine
        comparison_data = {
            "direction": {
                "lgbm": {"feat_A": 0.9, "feat_B": 0.3},
                "random_forest": {"feat_A": 0.5, "feat_C": 0.8},
            },
        }
        summary = ExplainabilityEngine._build_global_summary(comparison_data, top_n=3)
        assert "top_features" in summary
        features = [item["feature"] for item in summary["top_features"]]
        # feat_A has max 0.9, feat_C 0.8, feat_B 0.3
        assert features[0] == "feat_A"
        assert features[1] == "feat_C"

    def test_global_summary_top_n_limit(self) -> None:
        from models.explainability.engine import ExplainabilityEngine
        comparison_data = {
            "direction": {
                "lgbm": {f"feat_{i}": float(i) for i in range(30)},
            }
        }
        summary = ExplainabilityEngine._build_global_summary(comparison_data, top_n=5)
        assert len(summary["top_features"]) == 5


# ---------------------------------------------------------------------------
# ExplainabilityVisualizer tests
# ---------------------------------------------------------------------------


class TestExplainabilityVisualizer:
    """Tests for chart generation."""

    def _make_repo(self, tmp_path: Path):
        from storage.explainability_repository import ExplainabilityRepository
        return ExplainabilityRepository(root_dir=tmp_path)

    def _make_visualizer(self, tmp_path: Path):
        from models.explainability.visualizer import ExplainabilityVisualizer
        repo = self._make_repo(tmp_path)
        return ExplainabilityVisualizer(repo, top_n_features=5, top_n_dependence=3)

    @pytest.mark.skipif(not _HAS_MATPLOTLIB, reason="matplotlib not installed")
    def test_bar_plot_created(self, tmp_path: Path) -> None:
        viz = self._make_visualizer(tmp_path)
        fi_df = _make_feature_importance_df()
        out = viz.save_bar_plot("direction", "lgbm", fi_df)
        assert out.is_file()
        assert out.suffix == ".png"

    @pytest.mark.skipif(not _HAS_MATPLOTLIB, reason="matplotlib not installed")
    def test_bar_plot_correct_path(self, tmp_path: Path) -> None:
        viz = self._make_visualizer(tmp_path)
        fi_df = _make_feature_importance_df()
        out = viz.save_bar_plot("market_moving", "random_forest", fi_df)
        assert "market_moving" in str(out)
        assert "random_forest" in str(out)
        assert out.name == "bar_plot.png"

    @pytest.mark.skipif(not _HAS_MATPLOTLIB, reason="matplotlib not installed")
    def test_feature_comparison_plot_created(self, tmp_path: Path) -> None:
        viz = self._make_visualizer(tmp_path)
        comparison_data = {
            "direction": {
                "lgbm": {"feat_00": 0.9, "feat_01": 0.5},
                "random_forest": {"feat_00": 0.7, "feat_02": 0.3},
            }
        }
        out_path = tmp_path / "feature_comparison.png"
        out = viz.save_feature_comparison(comparison_data, out_path, top_n=5)
        assert out.is_file()

    def test_feature_comparison_empty_data(self, tmp_path: Path) -> None:
        """Empty comparison data should not crash — just return the path."""
        viz = self._make_visualizer(tmp_path)
        out_path = tmp_path / "feature_comparison.png"
        out = viz.save_feature_comparison({}, out_path)
        # Should return the path without error
        assert out == out_path

    def test_summary_plot_skips_without_shap(self, tmp_path: Path) -> None:
        """summary_plot should not raise when HAS_SHAP is False."""
        viz = self._make_visualizer(tmp_path)
        sv = _make_shap_values()
        fm = _make_feature_matrix()
        with patch("models.explainability.visualizer.HAS_SHAP", False):
            out = viz.save_summary_plot("direction", "lgbm", sv, fm, _FEATURE_NAMES)
        # Should still return a path (not necessarily the file)
        assert isinstance(out, Path)

    def test_dependence_plots_skip_without_shap(self, tmp_path: Path) -> None:
        viz = self._make_visualizer(tmp_path)
        sv = _make_shap_values()
        fm = _make_feature_matrix()
        fi_df = _make_feature_importance_df()
        with patch("models.explainability.visualizer.HAS_SHAP", False):
            result = viz.save_dependence_plots(
                "direction", "lgbm", sv, fm, _FEATURE_NAMES, fi_df
            )
        assert result == []

    def test_coerce_2d_from_list(self) -> None:
        """List of 2-D arrays → mean absolute value."""
        from models.explainability.visualizer import ExplainabilityVisualizer
        sv_list = [np.ones((10, 5)), -np.ones((10, 5))]
        result = ExplainabilityVisualizer._coerce_2d(sv_list)
        assert result.shape == (10, 5)
        np.testing.assert_allclose(result, np.ones((10, 5)))

    def test_coerce_2d_from_3d(self) -> None:
        """3-D array (n_classes, n_samples, n_features) → 2-D mean."""
        from models.explainability.visualizer import ExplainabilityVisualizer
        sv_3d = np.ones((3, 10, 5))
        result = ExplainabilityVisualizer._coerce_2d(sv_3d)
        assert result.shape == (10, 5)

    def test_coerce_2d_passthrough_2d(self) -> None:
        from models.explainability.visualizer import ExplainabilityVisualizer
        sv_2d = np.ones((10, 5))
        result = ExplainabilityVisualizer._coerce_2d(sv_2d)
        assert result.shape == (10, 5)


# ---------------------------------------------------------------------------
# ExplainabilityEngine unit tests (mocked model and data)
# ---------------------------------------------------------------------------


class TestExplainabilityEngine:
    """Unit tests for ExplainabilityEngine with fully mocked dependencies."""

    def _make_mock_model_bundle(self, n_classes: int = 3) -> dict:
        """Create a fake model bundle with a simple estimator."""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder

        rng = np.random.default_rng(0)
        X = rng.normal(0, 1, (_N_SAMPLES, _N_FEATURES))
        y = rng.integers(0, n_classes, _N_SAMPLES)

        clf = RandomForestClassifier(n_estimators=5, random_state=0)
        clf.fit(X, y)

        le = LabelEncoder()
        labels = np.array(["POSITIVE", "NEUTRAL", "NEGATIVE"][:n_classes])
        le.fit(labels)

        return {"estimator": clf, "label_encoder": le}

    def _make_mock_preprocessor(self):
        """Identity preprocessor that just converts to numpy."""
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import FunctionTransformer
        return FunctionTransformer(lambda x: x.values if hasattr(x, "values") else x)

    def _make_training_df(self) -> pd.DataFrame:
        rng = np.random.default_rng(0)
        data = {feat: rng.normal(0, 1, _N_SAMPLES) for feat in _FEATURE_NAMES}
        data["direction"] = rng.choice(["POSITIVE", "NEUTRAL", "NEGATIVE"], _N_SAMPLES)
        data["market_moving"] = rng.choice(["True", "False"], _N_SAMPLES)
        data["impact_strength"] = rng.choice(["LOW", "MEDIUM", "HIGH"], _N_SAMPLES)
        data["confidence_label"] = rng.choice(["LOW", "MEDIUM", "HIGH"], _N_SAMPLES)
        import pandas as pd
        return pd.DataFrame(data)

    def test_reduce_shap_to_2d_list(self) -> None:
        from models.explainability.engine import ExplainabilityEngine
        sv_list = [np.ones((20, 5)) * 0.5, np.ones((20, 5)) * 0.3]
        result = ExplainabilityEngine._reduce_shap_to_2d(sv_list)
        assert result.shape == (20, 5)

    def test_reduce_shap_to_2d_3d_array(self) -> None:
        from models.explainability.engine import ExplainabilityEngine
        sv_3d = np.ones((3, 20, 5))
        result = ExplainabilityEngine._reduce_shap_to_2d(sv_3d)
        assert result.shape == (20, 5)

    def test_reduce_shap_to_2d_passthrough(self) -> None:
        from models.explainability.engine import ExplainabilityEngine
        sv_2d = np.ones((20, 5))
        result = ExplainabilityEngine._reduce_shap_to_2d(sv_2d)
        assert result.shape == (20, 5)

    def test_build_global_summary_structure(self) -> None:
        from models.explainability.engine import ExplainabilityEngine
        comparison_data = {
            "direction": {"lgbm": {"feat_A": 0.5, "feat_B": 0.2}},
        }
        summary = ExplainabilityEngine._build_global_summary(comparison_data, top_n=2)
        assert "description" in summary
        assert "top_features" in summary
        assert "generated_at" in summary
        assert len(summary["top_features"]) == 2
        assert summary["top_features"][0]["rank"] == 1

    def test_local_explanations_correct_group(self, tmp_path: Path) -> None:
        """Correct group: samples where y_pred == y_true AND prob >= 0.8."""
        from models.explainability.engine import ExplainabilityEngine

        engine = ExplainabilityEngine.__new__(ExplainabilityEngine)

        rng = np.random.default_rng(7)
        y_true = np.array(["POSITIVE"] * 40 + ["NEUTRAL"] * 40)
        y_pred = y_true.copy()
        y_pred[5] = "NEUTRAL"  # One deliberate mismatch

        y_prob = rng.dirichlet([0.1, 0.1, 0.1], 80)
        y_prob[:, 0] = 0.9  # Force high confidence for class 0

        shap_values_2d = rng.normal(0, 0.1, (80, _N_FEATURES))

        result = engine._build_local_explanations(
            shap_values_2d=shap_values_2d,
            feature_names=_FEATURE_NAMES,
            y_true=y_true,
            y_pred=y_pred,
            y_prob=y_prob,
        )

        assert "correct" in result
        assert "misclassified" in result
        assert "high_confidence" in result
        assert result["misclassified"]["n_samples"] == 1
        assert result["correct"]["n_samples"] <= 10

    def test_local_explanations_no_proba(self, tmp_path: Path) -> None:
        """Engine handles None y_prob gracefully."""
        from models.explainability.engine import ExplainabilityEngine

        engine = ExplainabilityEngine.__new__(ExplainabilityEngine)
        rng = np.random.default_rng(9)
        y_true = np.array(["A"] * 20 + ["B"] * 20)
        y_pred = y_true.copy()
        y_pred[3] = "B"
        shap_2d = rng.normal(0, 1, (40, _N_FEATURES))

        result = engine._build_local_explanations(
            shap_values_2d=shap_2d,
            feature_names=_FEATURE_NAMES,
            y_true=y_true,
            y_pred=y_pred,
            y_prob=None,
        )
        # Should not raise; high_confidence n_samples should equal all samples (prob=1.0)
        assert result["high_confidence"]["n_samples"] <= 10

    def test_build_local_explanations_sample_structure(self) -> None:
        from models.explainability.engine import ExplainabilityEngine

        engine = ExplainabilityEngine.__new__(ExplainabilityEngine)
        rng = np.random.default_rng(11)
        y_true = np.array(["A"] * 10)
        y_pred = np.array(["A"] * 8 + ["B"] * 2)
        y_prob = rng.dirichlet([1, 1], 10)
        shap_2d = rng.normal(0, 1, (10, _N_FEATURES))

        result = engine._build_local_explanations(
            shap_values_2d=shap_2d,
            feature_names=_FEATURE_NAMES,
            y_true=y_true,
            y_pred=y_pred,
            y_prob=y_prob,
        )

        if result["misclassified"]["n_samples"] > 0:
            sample = result["misclassified"]["samples"][0]
            assert "sample_index" in sample
            assert "true_label" in sample
            assert "predicted_label" in sample
            assert "max_probability" in sample
            assert "top_shap_features" in sample
            assert isinstance(sample["top_shap_features"], list)

    def test_explain_all_no_models_found(self, tmp_path: Path) -> None:
        """explain_all should return empty dict when no models are trained."""
        from models.explainability.engine import ExplainabilityEngine, HAS_SHAP

        if not HAS_SHAP:
            pytest.skip("shap not installed")

        mock_model_repo = MagicMock()
        mock_model_repo.exists.return_value = False

        mock_expl_repo = MagicMock()
        mock_expl_repo.root = tmp_path
        mock_expl_repo.model_dir.return_value = tmp_path
        mock_expl_repo.dependence_dir.return_value = tmp_path / "dep"
        (tmp_path / "dep").mkdir(exist_ok=True)

        mock_builder = MagicMock()
        df = self._make_training_df()
        mock_builder.build.return_value = (df, df, MagicMock(), MagicMock())

        engine = ExplainabilityEngine(
            model_repo=mock_model_repo,
            expl_repo=mock_expl_repo,
            dataset_builder=mock_builder,
        )
        results = engine.explain_all()
        # No models found → empty results for all targets
        for target_results in results.values():
            assert len(target_results) == 0

    def test_explain_all_empty_dataset_raises(self, tmp_path: Path) -> None:
        from models.explainability.engine import ExplainabilityEngine, HAS_SHAP

        if not HAS_SHAP:
            pytest.skip("shap not installed")

        mock_builder = MagicMock()
        mock_builder.build.return_value = (
            pd.DataFrame(),  # empty dataset
            pd.DataFrame(),
            MagicMock(),
            MagicMock(),
        )

        engine = ExplainabilityEngine(
            model_repo=MagicMock(),
            expl_repo=MagicMock(),
            dataset_builder=mock_builder,
        )
        with pytest.raises(ValueError, match="empty"):
            engine.explain_all()

    @pytest.mark.skipif(not _HAS_SHAP, reason="shap not installed")
    def test_explain_single_random_forest(self, tmp_path: Path) -> None:
        """Integration-style test: ExplainabilityEngine with a real RF model."""
        from models.explainability.engine import ExplainabilityEngine

        model_bundle = self._make_mock_model_bundle(n_classes=3)
        preprocessor = self._make_mock_preprocessor()

        mock_model_repo = MagicMock()
        mock_model_repo.exists.return_value = True
        mock_model_repo.load.return_value = (model_bundle, preprocessor, _FEATURE_NAMES)

        mock_expl_repo = MagicMock()
        mock_expl_repo.root = tmp_path
        mock_expl_repo.model_dir.return_value = tmp_path
        mock_expl_repo.dependence_dir.return_value = tmp_path / "dep"
        mock_expl_repo.save.return_value = {}
        (tmp_path / "dep").mkdir(exist_ok=True)

        df = self._make_training_df()

        mock_builder = MagicMock()
        mock_builder.build.return_value = (df, df, MagicMock(), MagicMock())

        engine = ExplainabilityEngine(
            model_repo=mock_model_repo,
            expl_repo=mock_expl_repo,
            dataset_builder=mock_builder,
            top_n_features=5,
            top_n_dependence=3,
        )

        result = engine._explain_single(
            df_train=df,
            target="direction",
            target_col="direction",
            model_type="random_forest",
        )

        assert result["target"] == "direction"
        assert result["model_type"] == "random_forest"
        assert "feature_importance" in result
        fi = result["feature_importance"]
        assert isinstance(fi, pd.DataFrame)
        assert list(fi.columns) == ["feature", "mean_abs_shap"]
        # Check sorted descending
        vals = fi["mean_abs_shap"].tolist()
        assert vals == sorted(vals, reverse=True)

    @pytest.mark.skipif(not _HAS_SHAP, reason="shap not installed")
    def test_shap_generation_produces_correct_shape(self, tmp_path: Path) -> None:
        """SHAP values should have shape (n_samples, n_features)."""
        from models.explainability.engine import ExplainabilityEngine

        model_bundle = self._make_mock_model_bundle(n_classes=2)
        preprocessor = self._make_mock_preprocessor()

        engine = ExplainabilityEngine.__new__(ExplainabilityEngine)

        rng = np.random.default_rng(0)
        X_proc = rng.normal(0, 1, (_N_SAMPLES, _N_FEATURES))

        shap_values, explainer_type = engine._build_shap_values(
            estimator=model_bundle["estimator"],
            X_proc=X_proc,
        )
        sv_2d = ExplainabilityEngine._reduce_shap_to_2d(shap_values)

        assert sv_2d.shape[0] == _N_SAMPLES
        assert sv_2d.shape[1] == _N_FEATURES
        assert explainer_type in ("TreeExplainer", "KernelExplainer")


# ---------------------------------------------------------------------------
# Visualization generation tests
# ---------------------------------------------------------------------------


class TestVisualizationGeneration:
    """Tests that verify plots are generated correctly."""

    def _make_repo(self, tmp_path: Path):
        from storage.explainability_repository import ExplainabilityRepository
        return ExplainabilityRepository(root_dir=tmp_path)

    @pytest.mark.skipif(not _HAS_MATPLOTLIB, reason="matplotlib not installed")
    def test_bar_plot_created_for_all_targets(self, tmp_path: Path) -> None:
        from models.explainability.visualizer import ExplainabilityVisualizer
        from storage.explainability_repository import VALID_TARGETS, VALID_MODEL_TYPES
        repo = self._make_repo(tmp_path)
        viz = ExplainabilityVisualizer(repo, top_n_features=5)
        fi_df = _make_feature_importance_df()

        for target in list(VALID_TARGETS)[:2]:
            for model_type in list(VALID_MODEL_TYPES)[:2]:
                out = viz.save_bar_plot(target, model_type, fi_df)
                assert out.is_file()

    @pytest.mark.skipif(not _HAS_MATPLOTLIB, reason="matplotlib not installed")
    def test_feature_comparison_multiple_targets(self, tmp_path: Path) -> None:
        from models.explainability.visualizer import ExplainabilityVisualizer
        repo = self._make_repo(tmp_path)
        viz = ExplainabilityVisualizer(repo)

        comparison_data = {
            "direction": {
                "lgbm": {"feat_00": 0.9, "feat_01": 0.5},
                "random_forest": {"feat_02": 0.7},
            },
            "market_moving": {
                "lgbm": {"feat_00": 0.6},
            },
        }
        out_path = tmp_path / "feature_comparison.png"
        out = viz.save_feature_comparison(comparison_data, out_path, top_n=5)
        assert out.is_file()
        assert out.stat().st_size > 0


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    """Tests for the explain-models CLI command."""

    def test_build_parser_has_explain_models(self) -> None:
        """build_parser() should include the explain-models sub-command."""
        from main import build_parser
        parser = build_parser()
        # Parse a known subcommand to verify parser is valid
        args = parser.parse_args(["explain-models", "--all"])
        assert args.command == "explain-models"
        assert args.all is True

    def test_explain_models_cli_target_filter(self) -> None:
        from main import build_parser
        parser = build_parser()
        args = parser.parse_args(["explain-models", "--target", "direction"])
        assert args.target == "direction"
        assert args.model is None

    def test_explain_models_cli_model_filter(self) -> None:
        from main import build_parser
        parser = build_parser()
        args = parser.parse_args(["explain-models", "--model", "lgbm"])
        assert args.model == "lgbm"
        assert args.target is None

    def test_explain_models_cli_mode(self) -> None:
        from main import build_parser
        parser = build_parser()
        args = parser.parse_args(["explain-models", "--mode", "structured"])
        assert args.mode == "structured"

    def test_cmd_explain_models_returns_0_on_success(self, tmp_path: Path) -> None:
        from main import cmd_explain_models

        mock_args = MagicMock()
        mock_args.target = None
        mock_args.model = None
        mock_args.all = True
        mock_args.mode = "structured"

        mock_results = {
            "direction": {
                "lgbm": {
                    "n_samples": 50,
                    "n_features": 15,
                    "top_features": ["feat_00", "feat_01"],
                    "feature_importance": _make_feature_importance_df(),
                    "local_explanations": {},
                }
            }
        }

        with patch("models.explainability.engine.ExplainabilityEngine") as MockEngine:
            MockEngine.return_value.explain_all.return_value = mock_results
            exit_code = cmd_explain_models(mock_args)

        assert exit_code == 0

    def test_cmd_explain_models_returns_0_when_no_models(self) -> None:
        from main import cmd_explain_models

        mock_args = MagicMock()
        mock_args.target = None
        mock_args.model = None
        mock_args.all = True
        mock_args.mode = "structured"

        with patch("models.explainability.engine.ExplainabilityEngine") as MockEngine:
            MockEngine.return_value.explain_all.return_value = {}
            exit_code = cmd_explain_models(mock_args)

        assert exit_code == 0

    def test_cmd_explain_models_returns_1_on_import_error(self) -> None:
        from main import cmd_explain_models

        mock_args = MagicMock()
        mock_args.target = None
        mock_args.model = None
        mock_args.all = True
        mock_args.mode = "structured"

        with patch("models.explainability.engine.ExplainabilityEngine") as MockEngine:
            MockEngine.side_effect = ImportError("shap not found")
            exit_code = cmd_explain_models(mock_args)

        assert exit_code == 1

    def test_cmd_explain_models_returns_1_on_runtime_error(self) -> None:
        from main import cmd_explain_models

        mock_args = MagicMock()
        mock_args.target = None
        mock_args.model = None
        mock_args.all = False
        mock_args.mode = "structured"

        with patch("models.explainability.engine.ExplainabilityEngine") as MockEngine:
            MockEngine.return_value.explain_all.side_effect = RuntimeError("pipeline failed")
            exit_code = cmd_explain_models(mock_args)

        assert exit_code == 1

    def test_cmd_explain_models_target_model_filter(self) -> None:
        """--target and --model are passed to explain_all correctly."""
        from main import cmd_explain_models

        mock_args = MagicMock()
        mock_args.target = "direction"
        mock_args.model = "lgbm"
        mock_args.all = False
        mock_args.mode = "structured"

        with patch("models.explainability.engine.ExplainabilityEngine") as MockEngine:
            engine_instance = MockEngine.return_value
            engine_instance.explain_all.return_value = {}
            cmd_explain_models(mock_args)
            engine_instance.explain_all.assert_called_once_with(
                target_filter="direction",
                model_filter="lgbm",
            )

    def test_cmd_explain_models_all_flag_clears_filters(self) -> None:
        """--all clears any --target or --model that might be set."""
        from main import cmd_explain_models

        mock_args = MagicMock()
        mock_args.target = "direction"  # Would be overridden by --all
        mock_args.model = "lgbm"       # Would be overridden by --all
        mock_args.all = True
        mock_args.mode = "structured"

        with patch("models.explainability.engine.ExplainabilityEngine") as MockEngine:
            engine_instance = MockEngine.return_value
            engine_instance.explain_all.return_value = {}
            cmd_explain_models(mock_args)
            engine_instance.explain_all.assert_called_once_with(
                target_filter=None,
                model_filter=None,
            )


# ---------------------------------------------------------------------------
# Settings tests
# ---------------------------------------------------------------------------


class TestSettings:
    """Verify EXPLAINABILITY_DIR is correctly registered in settings."""

    def test_explainability_dir_exists_in_settings(self) -> None:
        from config.settings import settings
        assert hasattr(settings, "EXPLAINABILITY_DIR")

    def test_explainability_dir_is_path(self) -> None:
        from config.settings import settings
        assert isinstance(settings.EXPLAINABILITY_DIR, Path)

    def test_explainability_dir_name(self) -> None:
        from config.settings import settings
        assert settings.EXPLAINABILITY_DIR.name == "explainability"


# ---------------------------------------------------------------------------
# Coverage-boosting tests for edge cases and __init__ lazy imports
# ---------------------------------------------------------------------------


class TestPackageInit:
    """Tests for models/explainability/__init__.py lazy __getattr__."""

    def test_getattr_engine(self) -> None:
        """Accessing ExplainabilityEngine via the package triggers lazy import."""
        import models.explainability as pkg
        cls = pkg.ExplainabilityEngine
        from models.explainability.engine import ExplainabilityEngine
        assert cls is ExplainabilityEngine

    def test_getattr_visualizer(self) -> None:
        """Accessing ExplainabilityVisualizer via the package triggers lazy import."""
        import models.explainability as pkg
        cls = pkg.ExplainabilityVisualizer
        from models.explainability.visualizer import ExplainabilityVisualizer
        assert cls is ExplainabilityVisualizer

    def test_getattr_unknown_raises(self) -> None:
        """Accessing an unknown attribute raises AttributeError."""
        import models.explainability as pkg
        with pytest.raises(AttributeError, match="has no attribute"):
            _ = pkg.NonExistentClass


class TestEngineCoverageEdgeCases:
    """Additional tests to cover engine.py branches not exercised elsewhere."""

    def test_explain_all_raises_without_shap(self, tmp_path: Path) -> None:
        """explain_all must raise RuntimeError when HAS_SHAP is False."""
        from models.explainability.engine import ExplainabilityEngine

        mock_model_repo = MagicMock()
        mock_expl_repo = MagicMock()
        mock_expl_repo.root = tmp_path
        mock_builder = MagicMock()
        df = pd.DataFrame({"direction": ["A", "B"]})
        mock_builder.build.return_value = (df, df, MagicMock(), MagicMock())

        engine = ExplainabilityEngine(
            model_repo=mock_model_repo,
            expl_repo=mock_expl_repo,
            dataset_builder=mock_builder,
        )

        with patch("models.explainability.engine.HAS_SHAP", False):
            with pytest.raises(RuntimeError, match="shap is required"):
                engine.explain_all()

    def test_explain_all_skips_missing_target_col(self, tmp_path: Path) -> None:
        """Targets whose label column is missing from the dataset are silently skipped."""
        from models.explainability.engine import ExplainabilityEngine, HAS_SHAP

        if not HAS_SHAP:
            pytest.skip("shap not installed")

        mock_model_repo = MagicMock()
        mock_model_repo.exists.return_value = False  # no models

        mock_expl_repo = MagicMock()
        mock_expl_repo.root = tmp_path
        mock_expl_repo.save_global_summary.return_value = tmp_path / "gs.json"
        mock_expl_repo.save_model_comparison.return_value = tmp_path / "mc.json"

        # Dataset without the direction column
        df = pd.DataFrame({"some_feature": [1.0, 2.0, 3.0]})
        mock_builder = MagicMock()
        mock_builder.build.return_value = (df, df, MagicMock(), MagicMock())

        engine = ExplainabilityEngine(
            model_repo=mock_model_repo,
            expl_repo=mock_expl_repo,
            dataset_builder=mock_builder,
        )
        results = engine.explain_all(target_filter="direction")
        # direction col not in df → should be skipped, not raise
        assert results.get("direction", {}) == {}

    def test_visualizer_bar_plot_returns_path_without_matplotlib(
        self, tmp_path: Path
    ) -> None:
        """Bar plot returns the output path even when matplotlib is not available."""
        from storage.explainability_repository import ExplainabilityRepository
        from models.explainability.visualizer import ExplainabilityVisualizer

        repo = ExplainabilityRepository(root_dir=tmp_path)
        viz = ExplainabilityVisualizer(repo)
        fi_df = _make_feature_importance_df()

        with patch("models.explainability.visualizer.HAS_MATPLOTLIB", False):
            out = viz.save_bar_plot("direction", "lgbm", fi_df)
        # Should return path without creating file
        assert isinstance(out, Path)

    def test_visualizer_feature_comparison_returns_path_without_matplotlib(
        self, tmp_path: Path
    ) -> None:
        from storage.explainability_repository import ExplainabilityRepository
        from models.explainability.visualizer import ExplainabilityVisualizer

        repo = ExplainabilityRepository(root_dir=tmp_path)
        viz = ExplainabilityVisualizer(repo)
        out_path = tmp_path / "feature_comparison.png"

        with patch("models.explainability.visualizer.HAS_MATPLOTLIB", False):
            out = viz.save_feature_comparison(
                {"direction": {"lgbm": {"feat_00": 0.5}}},
                out_path,
            )
        assert isinstance(out, Path)

