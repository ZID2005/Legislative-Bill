"""
tests/test_feature_selection.py
================================
Comprehensive test suite for Task 5.4 — Feature Selection Engine.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from features.selection_engine import FeatureSelectionEngine
from main import cmd_select_features
from schemas.feature_selection_validation_report import FeatureSelectionValidationReport
from storage.feature_selection_repository import FeatureSelectionRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_fused_df() -> pd.DataFrame:
    """Return a mock fused dataset with structured features for testing."""
    np.random.seed(42)
    rows = 20
    
    # Target variables (classification targets)
    direction = np.random.choice(["POSITIVE", "NEGATIVE", "NEUTRAL"], size=rows)
    market_moving = np.random.choice([True, False], size=rows)
    impact_strength = np.random.choice(["LOW", "MEDIUM", "HIGH"], size=rows)
    confidence_label = np.random.choice(["HIGH", "LOW"], size=rows)
    
    # Feature variables
    feat_norm = np.random.normal(0, 1, size=rows)
    feat_constant = np.ones(rows) * 5.0
    feat_low_var = np.random.normal(0, 0.001, size=rows)
    feat_dup1 = np.random.normal(5, 2, size=rows)
    feat_dup2 = feat_dup1.copy()
    feat_highly_corr = feat_norm * 0.99 + np.random.normal(0, 0.01, size=rows)
    feat_missing = feat_norm.copy()
    feat_missing[0:12] = np.nan  # 60% missing values
    feat_cat = np.random.choice(["cat1", "cat2", None], size=rows)
    feat_list = [["a", "b"]] * rows
    
    return pd.DataFrame({
        "record_id": [f"bill-{i}|isin-1|window-1" for i in range(rows)],
        "bill_id": [f"bill-{i}" for i in range(rows)],
        "company_isin": ["isin-1"] * rows,
        "event_window": ["window-1"] * rows,
        
        "feat_norm": feat_norm,
        "feat_constant": feat_constant,
        "feat_low_var": feat_low_var,
        "feat_dup1": feat_dup1,
        "feat_dup2": feat_dup2,
        "feat_highly_corr": feat_highly_corr,
        "feat_missing": feat_missing,
        "feat_cat": feat_cat,
        "feat_list": feat_list,
        
        "direction": direction,
        "market_moving": market_moving,
        "impact_strength": impact_strength,
        "confidence_label": confidence_label
    })


# ---------------------------------------------------------------------------
# Test schemas & serialization
# ---------------------------------------------------------------------------

def test_validation_report_serialization():
    """Verify FeatureSelectionValidationReport dict round-trips correctly."""
    report = FeatureSelectionValidationReport(
        mode="structured",
        timestamp="2026-07-16T12:00:00Z",
        success=True,
        no_duplicate_columns=True,
        no_nan_only_columns=True,
        selected_features_exist=True,
        ranking_generated=True,
        errors=[],
        warnings=["Test warning"],
        details={"features_count": 10}
    )
    
    serialized = report.to_dict()
    assert serialized["mode"] == "structured"
    assert serialized["success"] is True
    assert serialized["no_duplicate_columns"] is True
    assert serialized["warnings"] == ["Test warning"]
    
    deserialized = FeatureSelectionValidationReport.from_dict(serialized)
    assert deserialized.mode == "structured"
    assert deserialized.success is True
    assert deserialized.no_duplicate_columns is True
    assert deserialized.warnings == ["Test warning"]
    assert repr(deserialized).startswith("<FeatureSelectionValidationReport")


# ---------------------------------------------------------------------------
# Test Repository
# ---------------------------------------------------------------------------

def test_feature_selection_repository(temp_dir):
    """Verify save, load, and checking helper methods on FeatureSelectionRepository."""
    repo = FeatureSelectionRepository(selection_dir=temp_dir)
    
    assert repo.list_modes() == [
        "structured", "finbert", "legal", "structured-finbert", "structured-legal", "hybrid"
    ]
    
    # Create test DataFrames
    df_selected = pd.DataFrame({"record_id": ["r1", "r2"], "feat_1": [1.0, 2.0]})
    df_importance = pd.DataFrame({"feature": ["feat_1"], "mean_importance": [1.0]})
    removed = {"constant": ["feat_2"]}
    report = FeatureSelectionValidationReport(
        mode="structured",
        timestamp=datetime.now(timezone.utc).isoformat(),
        success=True,
        no_duplicate_columns=True,
        no_nan_only_columns=True,
        selected_features_exist=True,
        ranking_generated=True
    )
    
    # Check exists is False initially
    assert repo.exists("structured") is False
    
    # Save
    repo.save("structured", df_selected, df_importance, removed, report)
    
    # Check exists is True
    assert repo.exists("structured") is True
    
    # Load and verify
    df_loaded = repo.load("structured")
    pd.testing.assert_frame_equal(df_loaded, df_selected)
    
    imp_loaded = repo.load_importance("structured")
    pd.testing.assert_frame_equal(imp_loaded, df_importance)
    
    rem_loaded = repo.load_removed("structured")
    assert rem_loaded == removed
    
    rep_loaded = repo.load_report("structured")
    assert rep_loaded.mode == "structured"
    assert rep_loaded.success is True

    # Error cases
    with pytest.raises(ValueError):
        repo.save("invalid_mode", df_selected, df_importance, removed, report)
        
    with pytest.raises(FileNotFoundError):
        repo.load("finbert")

    with pytest.raises(FileNotFoundError):
        repo.load_importance("finbert")

    with pytest.raises(FileNotFoundError):
        repo.load_removed("finbert")
        
    assert repo.load_report("finbert") is None


# ---------------------------------------------------------------------------
# Test FeatureSelectionEngine
# ---------------------------------------------------------------------------

def test_feature_selection_filters(mock_fused_df, temp_dir):
    """Verify that all pruning steps (constant, duplicates, missingness, correlation, variance) execute correctly."""
    mock_fusion_repo = MagicMock()
    mock_fusion_repo.load.return_value = mock_fused_df
    
    mock_feature_repo = MagicMock()
    mock_feature_repo.load_dataframe.return_value = pd.DataFrame() # No dynamic labels needed since they exist in the mock df
    
    repo_selection = FeatureSelectionRepository(selection_dir=temp_dir)
    engine = FeatureSelectionEngine(
        fusion_repo=mock_fusion_repo,
        selection_repo=repo_selection,
        feature_repo=mock_feature_repo
    )
    
    # Run feature selection
    df_selected, report = engine.select_features(
        mode="structured",
        missing_threshold=0.5,
        correlation_threshold=0.95,
        variance_threshold=0.01,
        rebuild=True,
        use_lightgbm=False  # use Random Forest
    )
    
    assert report.success is True
    
    # Check which features were removed by checking the report details
    summary = report.details["removed_features_summary"]
    
    # constant: feat_constant
    assert summary["constant"] == 1
    # duplicate: feat_dup2
    assert summary["duplicate"] == 1
    # missing_values: feat_missing (60% missing)
    assert summary["missing_values"] == 1
    # low_variance: feat_low_var (std is small)
    assert summary["low_variance"] == 1
    # high_correlation: feat_highly_corr (corr with feat_norm is 0.99)
    assert summary["high_correlation"] == 1
    
    # Check that remaining features are feat_norm, feat_dup1, feat_cat, and feat_list
    remaining_features = [
        c for c in df_selected.columns
        if c not in ["record_id", "bill_id", "company_isin", "event_window", "direction", "market_moving", "impact_strength", "confidence_label"]
    ]
    assert sorted(remaining_features) == sorted(["feat_norm", "feat_dup1", "feat_cat", "feat_list"])


def test_feature_selection_no_features_selected(mock_fused_df, temp_dir):
    """Verify validation report outputs an error when no features are selected."""
    # Create a DataFrame where all features are constant
    df_constant = mock_fused_df[["record_id", "bill_id", "company_isin", "event_window", "feat_constant", "direction"]].copy()
    
    mock_fusion_repo = MagicMock()
    mock_fusion_repo.load.return_value = df_constant
    
    repo_selection = FeatureSelectionRepository(selection_dir=temp_dir)
    engine = FeatureSelectionEngine(
        fusion_repo=mock_fusion_repo,
        selection_repo=repo_selection
    )
    
    df_selected, report = engine.select_features(
        mode="structured",
        rebuild=True,
        use_lightgbm=False
    )
    
    assert report.success is False
    assert any("No feature columns were selected" in err for err in report.errors)


def test_importance_ranking(mock_fused_df, temp_dir):
    """Verify that Mutual Information and Tree-based rankings are computed and output columns are structured correctly."""
    mock_fusion_repo = MagicMock()
    mock_fusion_repo.load.return_value = mock_fused_df
    
    repo_selection = FeatureSelectionRepository(selection_dir=temp_dir)
    engine = FeatureSelectionEngine(
        fusion_repo=mock_fusion_repo,
        selection_repo=repo_selection
    )
    
    # Prune nothing to check ranking on multiple features
    df_selected, report = engine.select_features(
        mode="structured",
        missing_threshold=None,
        correlation_threshold=1.0,
        variance_threshold=-1.0,
        rebuild=True,
        use_lightgbm=False  # Random Forest fallback
    )
    
    assert report.success is True
    
    # Load importance report
    importance_df = repo_selection.load_importance("structured")
    assert not importance_df.empty
    
    # Verify importance columns
    expected_cols = [
        "feature",
        "mi_direction", "tree_direction",
        "mi_market_moving", "tree_market_moving",
        "mi_impact_strength", "tree_impact_strength",
        "mi_confidence_label", "tree_confidence_label",
        "mean_importance"
    ]
    for col in expected_cols:
        assert col in importance_df.columns
        
    # Verify sorted by mean_importance
    assert list(importance_df["mean_importance"]) == sorted(list(importance_df["mean_importance"]), reverse=True)


def test_incremental_rebuilding(mock_fused_df, temp_dir):
    """Verify that engine loads existing files incrementally if rebuild=False and recalculates if rebuild=True."""
    mock_fusion_repo = MagicMock()
    mock_fusion_repo.load.return_value = mock_fused_df
    
    repo_selection = FeatureSelectionRepository(selection_dir=temp_dir)
    engine = FeatureSelectionEngine(
        fusion_repo=mock_fusion_repo,
        selection_repo=repo_selection
    )
    
    # Run once
    df1, rep1 = engine.select_features(mode="structured", rebuild=True, use_lightgbm=False)
    
    # Run again with rebuild=False (should load from repo without invoking fusion load)
    mock_fusion_repo.load.reset_mock()
    df2, rep2 = engine.select_features(mode="structured", rebuild=False, use_lightgbm=False)
    
    mock_fusion_repo.load.assert_not_called()
    assert rep1.timestamp == rep2.timestamp
    pd.testing.assert_frame_equal(df1, df2)


@patch("features.selection_engine.HAS_LIGHTGBM", True)
@patch("features.selection_engine.LGBMClassifier")
def test_lightgbm_integration(mock_lgbm, mock_fused_df, temp_dir):
    """Verify LightGBM is invoked for importance ranking if installed and requested."""
    mock_fusion_repo = MagicMock()
    mock_fusion_repo.load.return_value = mock_fused_df
    
    mock_instance = MagicMock()
    # Mock feature_importances_ to return array of 1.0s
    mock_instance.feature_importances_ = np.ones(1)
    mock_lgbm.return_value = mock_instance
    
    repo_selection = FeatureSelectionRepository(selection_dir=temp_dir)
    engine = FeatureSelectionEngine(
        fusion_repo=mock_fusion_repo,
        selection_repo=repo_selection
    )
    
    # Keep only one feature to match mock_instance mock size
    mock_df_subset = mock_fused_df[["record_id", "bill_id", "company_isin", "event_window", "feat_norm", "direction"]].copy()
    mock_fusion_repo.load.return_value = mock_df_subset
    
    df_selected, report = engine.select_features(
        mode="structured",
        rebuild=True,
        use_lightgbm=True
    )
    
    assert report.success is True
    mock_lgbm.assert_called()


# ---------------------------------------------------------------------------
# Test CLI Integration
# ---------------------------------------------------------------------------

def test_cli_command(temp_dir):
    """Verify the command line subcommand operates successfully and passes parameters correctly."""
    mock_engine = MagicMock()
    report = FeatureSelectionValidationReport(
        mode="structured",
        timestamp="2026-07-16T12:00:00Z",
        success=True,
        errors=[],
        warnings=[],
        details={"removed_features_summary": {"constant": 0}}
    )
    mock_engine.select_features.return_value = (pd.DataFrame(), report)
    
    with patch("features.selection_engine.FeatureSelectionEngine", return_value=mock_engine):
        args = argparse.Namespace(
            mode="structured",
            all=False,
            missing_threshold=0.5,
            correlation_threshold=0.95,
            variance_threshold=0.01,
            rebuild=True,
            use_random_forest=True
        )
        
        exit_code = cmd_select_features(args)
        assert exit_code == 0
        mock_engine.select_features.assert_called_with(
            mode="structured",
            missing_threshold=0.5,
            correlation_threshold=0.95,
            variance_threshold=0.01,
            rebuild=True,
            use_lightgbm=False
        )


def test_cli_command_all(temp_dir):
    """Verify that --all triggers selection across all 6 modes."""
    mock_engine = MagicMock()
    report = FeatureSelectionValidationReport(
        mode="structured",
        timestamp="2026-07-16T12:00:00Z",
        success=True,
        errors=[],
        warnings=[],
        details={"removed_features_summary": {}}
    )
    mock_engine.select_features.return_value = (pd.DataFrame(), report)
    
    with patch("features.selection_engine.FeatureSelectionEngine", return_value=mock_engine):
        args = argparse.Namespace(
            mode=None,
            all=True,
            missing_threshold=0.5,
            correlation_threshold=0.95,
            variance_threshold=0.01,
            rebuild=False,
            use_random_forest=False
        )
        
        exit_code = cmd_select_features(args)
        assert exit_code == 0
        assert mock_engine.select_features.call_count == 6


def test_repository_exceptions(temp_dir):
    """Verify repository methods raise/handle exceptions correctly when encountering I/O errors."""
    repo = FeatureSelectionRepository(selection_dir=temp_dir)
    df = pd.DataFrame({"feat": [1.0]})
    df_importance = pd.DataFrame({"feature": ["feat"], "mean_importance": [1.0]})
    removed = {"constant": []}
    report = FeatureSelectionValidationReport(
        mode="structured",
        timestamp=datetime.now(timezone.utc).isoformat(),
        success=True
    )
    
    # Mock to_parquet to fail
    with patch.object(df, "to_parquet", side_effect=OSError("Disk full")):
        with pytest.raises(OSError):
            repo.save("structured", df, df_importance, removed, report)
            
    # Mock to_csv to fail
    with patch("pandas.DataFrame.to_csv", side_effect=OSError("Permission denied")):
        with pytest.raises(OSError):
            repo.save("structured", df, df_importance, removed, report)
            
    # Mock open for json files to fail
    with patch("pathlib.Path.open", side_effect=OSError("Access denied")):
        with pytest.raises(OSError):
            repo.save("structured", df, df_importance, removed, report)

    # Mock load to fail (read_parquet raises error)
    # First create file so exists checks are bypassed orTouch file
    paths = repo._get_paths("structured")
    paths["selected_features"].touch()
    with patch("pandas.read_parquet", side_effect=OSError("Read error")):
        with pytest.raises(OSError):
            repo.load("structured")
            
    paths["feature_importance"].touch()
    with patch("pandas.read_csv", side_effect=OSError("Read error")):
        with pytest.raises(OSError):
            repo.load_importance("structured")

    paths["removed_features"].touch()
    with patch("pathlib.Path.open", side_effect=OSError("Read error")):
        with pytest.raises(OSError):
            repo.load_removed("structured")

    paths["selection_report"].touch()
    with patch("pathlib.Path.open", side_effect=OSError("Read error")):
        with pytest.raises(OSError):
            repo.load_report("structured")


def test_engine_edge_cases(mock_fused_df, temp_dir):
    """Verify other selection engine branches (unhashable unique check, validation anomalies, target details)."""
    mock_fusion_repo = MagicMock()
    mock_fusion_repo.load.return_value = mock_fused_df
    
    # Mock FeatureRepository load to raise Exception for dynamic targets
    mock_feat_repo = MagicMock()
    mock_feat_repo.load_dataframe.side_effect = Exception("DB error")
    
    repo_selection = FeatureSelectionRepository(selection_dir=temp_dir)
    engine = FeatureSelectionEngine(
        fusion_repo=mock_fusion_repo,
        selection_repo=repo_selection,
        feature_repo=mock_feat_repo
    )
    
    # 1. Test empty fused dataset throws ValueError
    mock_fusion_repo.load.return_value = pd.DataFrame()
    with pytest.raises(ValueError, match="Fused dataset.*is empty"):
        engine.select_features(mode="structured", rebuild=True)
    
    # Reset mock fused
    mock_fusion_repo.load.return_value = mock_fused_df
    
    # 2. Test dynamic targets loading failure exception branch (lines 199-201)
    df_selected, report = engine.select_features(
        mode="structured",
        missing_threshold=None,
        correlation_threshold=1.0,
        variance_threshold=-1.0,
        rebuild=True,
        use_lightgbm=False
    )
    assert report.success is True
    
    # 3. Test duplicate columns validation error (line 230)
    mock_df_dup = mock_fused_df.copy()
    # Let's duplicate the 'bill_id' column name
    cols = list(mock_df_dup.columns)
    cols[1] = "record_id"  # Duplicate 'record_id'
    mock_df_dup.columns = cols
    mock_fusion_repo.load.return_value = mock_df_dup
    
    with patch("pandas.DataFrame.to_parquet") as mock_to_parquet:
        df_selected, report = engine.select_features(
            mode="structured",
            rebuild=True,
            use_lightgbm=False
        )
        assert report.no_duplicate_columns is False
        assert report.success is False

    # 4. Test NaN-only columns validation error (line 236)
    # Add a NaN feature column to mock_fused_df and patch nunique/var to bypass constant and low-variance checks
    mock_df_nan = mock_fused_df.copy()
    mock_df_nan["feat_nan_only"] = np.nan
    mock_fusion_repo.load.return_value = mock_df_nan
    
    orig_nunique = pd.Series.nunique
    def mock_nunique(self, *args, **kwargs):
        if self.name == "feat_nan_only":
            return 2
        return orig_nunique(self, *args, **kwargs)
        
    orig_var = pd.Series.var
    def mock_var(self, *args, **kwargs):
        if self.name == "feat_nan_only":
            return 1.0
        return orig_var(self, *args, **kwargs)
        
    with patch("pandas.Series.nunique", mock_nunique), patch("pandas.Series.var", mock_var):
        df_selected, report = engine.select_features(
            mode="structured",
            missing_threshold=None,
            rebuild=True,
            use_lightgbm=False
        )
    assert report.no_nan_only_columns is False
    assert report.success is False

    # 5. Test calculate importance target column edge cases
    # 5.1 target not in data (line 315)
    # We drop a target column
    mock_df_no_target = mock_fused_df.drop(columns=["direction"])
    mock_fusion_repo.load.return_value = mock_df_no_target
    df_selected, report = engine.select_features(
        mode="structured",
        rebuild=True,
        use_lightgbm=False
    )
    assert report.success is True
    
    # 5.2 target has no valid rows (line 321)
    mock_df_nan_target = mock_fused_df.copy()
    mock_df_nan_target["direction"] = np.nan
    mock_fusion_repo.load.return_value = mock_df_nan_target
    df_selected, report = engine.select_features(
        mode="structured",
        rebuild=True,
        use_lightgbm=False
    )
    assert report.success is True

    # 5.3 target has only 1 class (line 335)
    mock_df_one_class = mock_fused_df.copy()
    mock_df_one_class["direction"] = "NEUTRAL"
    mock_fusion_repo.load.return_value = mock_df_one_class
    df_selected, report = engine.select_features(
        mode="structured",
        rebuild=True,
        use_lightgbm=False
    )
    assert report.success is True

    # 5.4 MI exceptions (line 350)
    mock_fusion_repo.load.return_value = mock_fused_df
    with patch("features.selection_engine.mutual_info_classif", side_effect=ValueError("MI calculation failed")):
        df_selected, report = engine.select_features(
            mode="structured",
            rebuild=True,
            use_lightgbm=False
        )
        assert report.success is True

    # 5.5 Tree classifier exception (line 369)
    with patch("sklearn.ensemble.RandomForestClassifier.fit", side_effect=ValueError("Fitting failed")):
        df_selected, report = engine.select_features(
            mode="structured",
            rebuild=True,
            use_lightgbm=False
        )
        assert report.success is True

    # 5.6 Force HAS_LIGHTGBM=False fallback coverage
    with patch("features.selection_engine.HAS_LIGHTGBM", False):
        df_selected, report = engine.select_features(
            mode="structured",
            rebuild=True,
            use_lightgbm=True
        )
        assert report.success is True

