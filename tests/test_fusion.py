"""
tests/test_fusion.py
=====================
Comprehensive test suite for Task 5.3 — Feature Fusion Engine.
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

from features.fusion_engine import FeatureFusionEngine
from main import cmd_build_fusion
from schemas.fusion_validation_report import FusionValidationReport
from storage.fusion_repository import FusionRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_features_df() -> pd.DataFrame:
    """Return a mock master features DataFrame with 2 bills, 2 companies, 1 window."""
    return pd.DataFrame([
        {
            "record_id": "bill-1|isin-1|window-1",
            "bill_id": "bill-1",
            "company_isin": "isin-1",
            "event_window": "window-1",
            "alpha": 0.05,
            "beta": 1.1,
            "r_squared": 0.8,
            "final_car": 0.03,
            "p_value": 0.01,
            "direction": "POSITIVE",
            "market_moving": True,
        },
        {
            "record_id": "bill-2|isin-2|window-1",
            "bill_id": "bill-2",
            "company_isin": "isin-2",
            "event_window": "window-1",
            "alpha": -0.02,
            "beta": 0.9,
            "r_squared": 0.75,
            "final_car": -0.04,
            "p_value": 0.04,
            "direction": "NEGATIVE",
            "market_moving": True,
        }
    ])


@pytest.fixture
def mock_finbert_df() -> pd.DataFrame:
    """Return mock FinBERT embeddings (dim=768) for both bills."""
    v1 = list(np.random.normal(0, 1, 768))
    v2 = list(np.random.normal(0, 1, 768))
    return pd.DataFrame([
        {
            "bill_id": "bill-1",
            "embedding_model": "finbert",
            "embedding_dimension": 768,
            "embedding_vector": v1,
            "token_count": 100,
            "model_version": "1.0",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "bill_id": "bill-2",
            "embedding_model": "finbert",
            "embedding_dimension": 768,
            "embedding_vector": v2,
            "token_count": 120,
            "model_version": "1.0",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ])


@pytest.fixture
def mock_legal_df() -> pd.DataFrame:
    """Return mock Legal-RoBERTa embeddings (dim=768) for both bills."""
    v1 = list(np.random.normal(0, 1, 768))
    v2 = list(np.random.normal(0, 1, 768))
    return pd.DataFrame([
        {
            "bill_id": "bill-1",
            "embedding_model": "legal-roberta",
            "embedding_dimension": 768,
            "embedding_vector": v1,
            "token_count": 150,
            "model_version": "1.0",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "bill_id": "bill-2",
            "embedding_model": "legal-roberta",
            "embedding_dimension": 768,
            "embedding_vector": v2,
            "token_count": 160,
            "model_version": "1.0",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ])


# ---------------------------------------------------------------------------
# Test schemas & serialization
# ---------------------------------------------------------------------------

def test_validation_report_serialization():
    """Verify FusionValidationReport dict round-trips correctly."""
    report = FusionValidationReport(
        mode="hybrid",
        timestamp="2026-07-16T12:00:00Z",
        success=True,
        duplicate_rows_count=0,
        missing_embeddings_count=0,
        nan_values_count=2,
        errors=[],
        warnings=["Some warning"],
        details={"total_rows": 100}
    )
    
    serialized = report.to_dict()
    assert serialized["mode"] == "hybrid"
    assert serialized["success"] is True
    assert serialized["nan_values_count"] == 2
    assert serialized["warnings"] == ["Some warning"]
    
    deserialized = FusionValidationReport.from_dict(serialized)
    assert deserialized.mode == "hybrid"
    assert deserialized.success is True
    assert deserialized.nan_values_count == 2
    assert deserialized.warnings == ["Some warning"]
    assert deserialized.details == {"total_rows": 100}
    
    repr_str = repr(report)
    assert "hybrid" in repr_str
    assert "success=True" in repr_str


# ---------------------------------------------------------------------------
# Test FusionRepository
# ---------------------------------------------------------------------------

def test_fusion_repository(temp_dir):
    """Test saving, loading, existing checks and clearing in FusionRepository."""
    repo = FusionRepository(fused_dir=temp_dir)
    
    # Check initial state
    assert repo.exists("structured") is False
    assert repo.list_modes() == [
        "structured",
        "finbert",
        "legal",
        "structured-finbert",
        "structured-legal",
        "hybrid",
    ]
    
    # Check invalid mode error
    with pytest.raises(ValueError, match="Unsupported fusion mode"):
        repo.save("invalid-mode", pd.DataFrame(), None)
        
    with pytest.raises(ValueError, match="Unsupported fusion mode"):
        repo.load("invalid-mode")

    # Create dummy data & report
    df = pd.DataFrame([{"record_id": "r1", "bill_id": "b1"}])
    report = FusionValidationReport(
        mode="structured",
        timestamp=datetime.now(timezone.utc).isoformat(),
        success=True
    )
    
    # Save structured mode
    parquet_path = repo.save("structured", df, report)
    assert parquet_path.is_file()
    assert repo.exists("structured") is True
    
    # Load and verify
    df_loaded = repo.load("structured")
    assert len(df_loaded) == 1
    assert df_loaded.iloc[0]["record_id"] == "r1"
    
    report_loaded = repo.load_report("structured")
    assert report_loaded is not None
    assert report_loaded.mode == "structured"
    assert report_loaded.success is True
    
    # Test missing report file
    report_path = temp_dir / "validation_report_structured.json"
    report_path.unlink()
    assert repo.load_report("structured") is None
    
    # Clear and verify empty
    repo.clear()
    assert repo.exists("structured") is False
    assert parquet_path.is_file() is False


# ---------------------------------------------------------------------------
# Test FeatureFusionEngine & Fusion Modes
# ---------------------------------------------------------------------------

@patch("features.fusion_engine.FeatureRepository")
@patch("features.fusion_engine.EmbeddingRepository")
def test_fusion_modes(
    mock_emb_class,
    mock_feat_class,
    temp_dir,
    mock_features_df,
    mock_finbert_df,
    mock_legal_df
):
    """Test all six fusion modes with mock datasets and verify outputs."""
    # Setup mocks
    feat_repo = mock_feat_class.return_value
    feat_repo.load_dataframe.return_value = mock_features_df
    
    # Embedding mock handler
    def mock_emb_init(model_name):
        mock_repo = MagicMock()
        if model_name == "finbert":
            mock_repo.load_dataframe.return_value = mock_finbert_df
        elif model_name == "legal-roberta":
            mock_repo.load_dataframe.return_value = mock_legal_df
        else:
            mock_repo.load_dataframe.return_value = pd.DataFrame()
        return mock_repo
        
    mock_emb_class.side_effect = mock_emb_init
    
    fusion_repo = FusionRepository(fused_dir=temp_dir)
    engine = FeatureFusionEngine(feature_repo=feat_repo, fusion_repo=fusion_repo)
    
    # Mode 1: Structured Features Only
    df_structured, report_s = engine.build("structured", rebuild=True)
    assert report_s.success is True
    assert len(df_structured) == 2
    assert "alpha" in df_structured.columns
    assert "finbert_emb_0" not in df_structured.columns
    assert "legal_emb_0" not in df_structured.columns

    # Mode 2: FinBERT Embeddings Only
    df_finbert, report_f = engine.build("finbert", rebuild=True)
    assert report_f.success is True
    assert len(df_finbert) == 2
    assert "alpha" not in df_finbert.columns
    assert "finbert_emb_0" in df_finbert.columns
    assert "finbert_emb_767" in df_finbert.columns
    assert "legal_emb_0" not in df_finbert.columns
    assert len([c for c in df_finbert.columns if c.startswith("finbert_emb_")]) == 768

    # Mode 3: Legal Transformer Embeddings Only
    df_legal, report_l = engine.build("legal", rebuild=True)
    assert report_l.success is True
    assert len(df_legal) == 2
    assert "alpha" not in df_legal.columns
    assert "legal_emb_0" in df_legal.columns
    assert "legal_emb_767" in df_legal.columns
    assert "finbert_emb_0" not in df_legal.columns
    assert len([c for c in df_legal.columns if c.startswith("legal_emb_")]) == 768

    # Mode 4: Structured Features + FinBERT
    df_s_finbert, report_sf = engine.build("structured-finbert", rebuild=True)
    assert report_sf.success is True
    assert len(df_s_finbert) == 2
    assert "alpha" in df_s_finbert.columns
    assert "finbert_emb_0" in df_s_finbert.columns
    assert "legal_emb_0" not in df_s_finbert.columns

    # Mode 5: Structured Features + Legal
    df_s_legal, report_sl = engine.build("structured-legal", rebuild=True)
    assert report_sl.success is True
    assert len(df_s_legal) == 2
    assert "alpha" in df_s_legal.columns
    assert "legal_emb_0" in df_s_legal.columns
    assert "finbert_emb_0" not in df_s_legal.columns

    # Mode 6: Hybrid (Structured + FinBERT + Legal)
    df_hybrid, report_h = engine.build("hybrid", rebuild=True)
    assert report_h.success is True
    assert len(df_hybrid) == 2
    assert "alpha" in df_hybrid.columns
    assert "finbert_emb_0" in df_hybrid.columns
    assert "legal_emb_0" in df_hybrid.columns


# ---------------------------------------------------------------------------
# Test Incremental Rebuilding
# ---------------------------------------------------------------------------

@patch("features.fusion_engine.FeatureRepository")
@patch("features.fusion_engine.EmbeddingRepository")
def test_incremental_rebuild(
    mock_emb_class,
    mock_feat_class,
    temp_dir,
    mock_features_df,
    mock_finbert_df
):
    """Test that incremental build correctly skips unchanged bills and updates new ones."""
    # First build
    feat_repo = mock_feat_class.return_value
    feat_repo.load_dataframe.return_value = mock_features_df
    
    mock_repo = MagicMock()
    mock_repo.load_dataframe.return_value = mock_finbert_df
    mock_emb_class.return_value = mock_repo
    
    fusion_repo = FusionRepository(fused_dir=temp_dir)
    engine = FeatureFusionEngine(feature_repo=feat_repo, fusion_repo=fusion_repo)
    
    df1, report1 = engine.build("structured-finbert", rebuild=True)
    assert len(df1) == 2
    
    # Second build with same features: should do nothing and return existing
    with patch.object(engine, "_fuse_records", return_value=pd.DataFrame()) as mock_fuse:
        df2, report2 = engine.build("structured-finbert", rebuild=False)
        assert len(df2) == 2
        mock_fuse.assert_not_called()
        
    # Now simulate adding a new bill record in features and embeddings
    new_feat_row = {
        "record_id": "bill-3|isin-1|window-1",
        "bill_id": "bill-3",
        "company_isin": "isin-1",
        "event_window": "window-1",
        "alpha": 0.01,
        "beta": 1.0,
        "r_squared": 0.9,
        "final_car": 0.02,
        "p_value": 0.02,
        "direction": "POSITIVE",
        "market_moving": False,
    }
    mock_features_df_extended = pd.concat([mock_features_df, pd.DataFrame([new_feat_row])], ignore_index=True)
    feat_repo.load_dataframe.return_value = mock_features_df_extended
    
    new_emb_row = {
        "bill_id": "bill-3",
        "embedding_model": "finbert",
        "embedding_dimension": 768,
        "embedding_vector": list(np.random.normal(0, 1, 768)),
        "token_count": 80,
        "model_version": "1.0",
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    mock_finbert_df_extended = pd.concat([mock_finbert_df, pd.DataFrame([new_emb_row])], ignore_index=True)
    mock_repo.load_dataframe.return_value = mock_finbert_df_extended
    
    # Run incremental build
    df3, report3 = engine.build("structured-finbert", rebuild=False)
    assert len(df3) == 3
    assert "bill-3|isin-1|window-1" in df3["record_id"].tolist()
    assert report3.success is True


# ---------------------------------------------------------------------------
# Test Validation Checks & Failures
# ---------------------------------------------------------------------------

@patch("features.fusion_engine.FeatureRepository")
@patch("features.fusion_engine.EmbeddingRepository")
def test_validation_errors(
    mock_emb_class,
    mock_feat_class,
    temp_dir,
    mock_features_df,
    mock_finbert_df
):
    """Test that validation correctly catches duplicate rows, NaNs, missing embeddings, and dimension mismatches."""
    feat_repo = mock_feat_class.return_value
    fusion_repo = FusionRepository(fused_dir=temp_dir)
    engine = FeatureFusionEngine(feature_repo=feat_repo, fusion_repo=fusion_repo)
    
    # 1. Empty master features
    feat_repo.load_dataframe.return_value = pd.DataFrame()
    _, report_empty = engine.build("structured", rebuild=True)
    assert report_empty.success is False
    assert "empty" in report_empty.errors[0]
    
    # 2. Missing key column from features
    df_missing_keys = mock_features_df.drop(columns=["record_id"])
    feat_repo.load_dataframe.return_value = df_missing_keys
    _, report_missing_key = engine.build("structured", rebuild=True)
    assert report_missing_key.success is False
    assert "record_id" in report_missing_key.errors[0]

    # 3. Duplicate rows check
    df_duplicates = pd.concat([mock_features_df, mock_features_df.iloc[[0]]], ignore_index=True)
    feat_repo.load_dataframe.return_value = df_duplicates
    _, report_dup = engine.build("structured", rebuild=True)
    assert report_dup.success is False
    assert report_dup.duplicate_rows_count == 1
    assert "duplicate" in report_dup.errors[0]

    # 4. NaN in key columns
    df_nan_key = mock_features_df.copy()
    df_nan_key.loc[0, "bill_id"] = None
    feat_repo.load_dataframe.return_value = df_nan_key
    _, report_nan_key = engine.build("structured", rebuild=True)
    assert report_nan_key.success is False
    assert report_nan_key.nan_values_count == 1
    assert "NaN/null" in report_nan_key.errors[0]

    # 5. Missing / Empty embeddings check
    feat_repo.load_dataframe.return_value = mock_features_df
    mock_repo = MagicMock()
    mock_repo.load_dataframe.return_value = pd.DataFrame()  # Empty embeddings
    mock_emb_class.return_value = mock_repo
    
    _, report_missing_emb = engine.build("finbert", rebuild=True)
    assert report_missing_emb.success is False
    assert report_missing_emb.missing_embeddings_count == 2
    assert "missing/NaN" in report_missing_emb.errors[0]

    # 6. Dimension mismatch check
    mock_finbert_bad_dim = mock_finbert_df.copy()
    mock_finbert_bad_dim.at[0, "embedding_vector"] = [0.1] * 100  # Incorrect dim=100
    mock_repo.load_dataframe.return_value = mock_finbert_bad_dim
    
    _, report_bad_dim = engine.build("finbert", rebuild=True)
    assert report_bad_dim.success is False
    assert "Expected 768" in report_bad_dim.errors[0] or report_bad_dim.missing_embeddings_count > 0

    # 7. Mismatched bill IDs
    mock_repo.load_dataframe.return_value = mock_finbert_df
    # Inject a bill_id in fused df that is not in master features
    df_bad_bill = mock_features_df.copy()
    engine_bad = FeatureFusionEngine(feature_repo=feat_repo, fusion_repo=fusion_repo)
    # Patch _fuse_records to return a fused DataFrame with a mismatched bill
    with patch.object(engine_bad, "_fuse_records") as mock_fuse:
        df_fused_mismatched = mock_features_df.copy()
        df_fused_mismatched.loc[0, "bill_id"] = "bill-mismatched"
        mock_fuse.return_value = df_fused_mismatched
        
        _, report_mismatched = engine_bad.build("structured", rebuild=True)
        assert report_mismatched.success is False
        assert report_mismatched.mismatched_bill_ids_count == 1

    # 8. Mismatched company IDs
    with patch.object(engine_bad, "_fuse_records") as mock_fuse:
        df_fused_mismatched_comp = mock_features_df.copy()
        df_fused_mismatched_comp.loc[0, "company_isin"] = "company-mismatched"
        mock_fuse.return_value = df_fused_mismatched_comp
        
        _, report_mismatched_comp = engine_bad.build("structured", rebuild=True)
        assert report_mismatched_comp.success is False
        assert report_mismatched_comp.mismatched_company_ids_count == 1

    # 9. Unsupported mode error
    with pytest.raises(ValueError, match="Unsupported fusion mode"):
        engine.build("invalid-mode")


# ---------------------------------------------------------------------------
# Test CLI Command
# ---------------------------------------------------------------------------

@patch("features.fusion_engine.FeatureFusionEngine.build")
def test_cli_command(mock_build):
    """Test cmd_build_fusion CLI command validation and behavior."""
    # Mock return value of build
    mock_report = FusionValidationReport(mode="hybrid", timestamp="", success=True)
    mock_build.return_value = (pd.DataFrame(), mock_report)
    
    # Test 1: No mode and no all (should fail with 1)
    args_empty = argparse.Namespace(mode=None, all=False, rebuild=False)
    exit_code = cmd_build_fusion(args_empty)
    assert exit_code == 1
    
    # Test 2: Mode specified
    args_mode = argparse.Namespace(mode="hybrid", all=False, rebuild=False)
    exit_code = cmd_build_fusion(args_mode)
    assert exit_code == 0
    mock_build.assert_called_once_with(mode="hybrid", rebuild=False)
    
    # Test 3: All modes specified
    mock_build.reset_mock()
    args_all = argparse.Namespace(mode=None, all=True, rebuild=True)
    exit_code = cmd_build_fusion(args_all)
    assert exit_code == 0
    assert mock_build.call_count == 6
    mock_build.assert_any_call(mode="structured", rebuild=True)
    mock_build.assert_any_call(mode="hybrid", rebuild=True)
    
    # Test 4: Rebuild failure in build
    mock_build.reset_mock()
    mock_report_fail = FusionValidationReport(mode="structured", timestamp="", success=False, errors=["Error occurred"])
    mock_build.return_value = (pd.DataFrame(), mock_report_fail)
    args_fail = argparse.Namespace(mode="structured", all=False, rebuild=False)
    exit_code = cmd_build_fusion(args_fail)
    assert exit_code == 1

    # Test 5: Exception raised in build
    mock_build.reset_mock()
    mock_build.side_effect = Exception("General error")
    exit_code = cmd_build_fusion(args_fail)
    assert exit_code == 1


def test_fusion_repository_edge_cases(temp_dir):
    repo = FusionRepository(fused_dir=temp_dir)
    assert repo.fused_dir == temp_dir

    # test invalid exists
    assert repo.exists("invalid-mode") is False

    # test save exceptions (parquet failure)
    df = pd.DataFrame([{"record_id": "r1"}])
    report = FusionValidationReport(mode="structured", timestamp="", success=True)
    with patch.object(pd.DataFrame, "to_parquet", side_effect=Exception("Parquet fail")):
        with pytest.raises(Exception, match="Parquet fail"):
            repo.save("structured", df, report)

    # test save exceptions (json failure)
    with patch("json.dump", side_effect=Exception("JSON fail")):
        with pytest.raises(Exception, match="JSON fail"):
            repo.save("structured", df, report)

    # Save successfully first
    repo.save("structured", df, report)

    # test load exceptions
    with patch("pandas.read_parquet", side_effect=Exception("Read fail")):
        with pytest.raises(Exception, match="Read fail"):
            repo.load("structured")

    # test load_report exceptions
    with patch("json.load", side_effect=Exception("JSON read fail")):
        assert repo.load_report("structured") is None

    # test clear exceptions
    with patch.object(Path, "unlink", side_effect=Exception("Unlink fail")):
        # should log but not raise
        repo.clear()


@patch("features.fusion_engine.FeatureRepository")
@patch("features.fusion_engine.EmbeddingRepository")
def test_fusion_engine_edge_cases(
    mock_emb_class,
    mock_feat_class,
    temp_dir,
    mock_features_df,
    mock_finbert_df
):
    feat_repo = mock_feat_class.return_value
    feat_repo.load_dataframe.return_value = mock_features_df
    
    mock_emb_repo = MagicMock()
    mock_emb_repo.load_dataframe.return_value = mock_finbert_df
    mock_emb_class.return_value = mock_emb_repo
    
    fusion_repo = FusionRepository(fused_dir=temp_dir)
    engine = FeatureFusionEngine(feature_repo=feat_repo, fusion_repo=fusion_repo)

    # 1. Incremental build where report is missing but parquet exists
    engine.build("structured-finbert", rebuild=True)
    assert fusion_repo.exists("structured-finbert") is True
    _, report_path = fusion_repo._get_paths("structured-finbert")
    report_path.unlink()
    df_inc, report_inc = engine.build("structured-finbert", rebuild=False)
    assert report_inc.success is True
    assert report_path.is_file()

    # 2. Incremental build where load raises exception (should fall back to full rebuild)
    with patch.object(FusionRepository, "load", side_effect=Exception("Corrupt parquet")):
        df_fallback, report_fallback = engine.build("structured-finbert", rebuild=False)
        assert len(df_fallback) == 2
        assert report_fallback.success is True

    # 3. Embedding loading raises exception
    mock_emb_repo.load_dataframe.side_effect = Exception("Load emb fail")
    df_fail_emb, report_fail_emb = engine.build("structured-finbert", rebuild=True)
    assert report_fail_emb.success is False
    assert report_fail_emb.missing_embeddings_count == 2
    mock_emb_repo.load_dataframe.side_effect = None # reset

    # 4. _expand_vector_column with empty DataFrame
    df_empty_expanded = engine._expand_vector_column(pd.DataFrame(), "vector", "prefix", 768)
    assert df_empty_expanded.empty

    # 5. Mismatched dimensions check
    mock_emb_repo.load_dataframe.return_value = mock_finbert_df
    engine_dim = FeatureFusionEngine(feature_repo=feat_repo, fusion_repo=fusion_repo)
    with patch.object(engine_dim, "_fuse_records") as mock_fuse:
        df_bad_dim = pd.DataFrame([{"record_id": "r1", "bill_id": "b1", "company_isin": "c1", "event_window": "w1", "finbert_emb_0": 0.1}])
        mock_fuse.return_value = df_bad_dim
        _, report_dim_mismatch = engine_dim.build("finbert", rebuild=True)
        assert report_dim_mismatch.success is False
        assert report_dim_mismatch.mismatched_dimensions_count > 0

    # 6. NaN values in structured features (Warning)
    mock_features_nan_structured = mock_features_df.copy()
    mock_features_nan_structured.loc[0, "alpha"] = np.nan
    feat_repo.load_dataframe.return_value = mock_features_nan_structured
    mock_emb_repo.load_dataframe.return_value = mock_finbert_df
    _, report_nan_warning = engine.build("structured-finbert", rebuild=True)
    assert report_nan_warning.success is True
    assert any("NaN values found in structured features" in w for w in report_nan_warning.warnings)

    # 7. Mismatched bill warning when checking embeddings
    mock_features_mismatched_bill = mock_features_df.copy()
    mock_features_mismatched_bill.loc[0, "bill_id"] = "bill-mismatched"
    feat_repo.load_dataframe.return_value = mock_features_mismatched_bill
    mock_emb_repo.load_dataframe.return_value = mock_finbert_df
    _, report_bill_mismatch = engine.build("finbert", rebuild=True)
    assert report_bill_mismatch.success is False

