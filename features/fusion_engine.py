"""
features/fusion_engine.py
==========================
Feature Fusion Engine for combining structured features and embeddings (Task 5.3).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
from config.logging_config import get_logger
from schemas.fusion_validation_report import FusionValidationReport
from storage.embedding_repository import EmbeddingRepository
from storage.feature_repository import FeatureRepository
from storage.fusion_repository import FusionRepository

logger = get_logger(__name__)


class FeatureFusionEngine:
    """
    Feature Fusion Engine.

    Combines structured features and transformer embeddings (FinBERT and Legal)
    into machine-learning-ready datasets. Supports incremental rebuilding and
    performs data-quality validation.

    Parameters
    ----------
    feature_repo : FeatureRepository, optional
    fusion_repo : FusionRepository, optional
    """

    def __init__(
        self,
        feature_repo: Optional[FeatureRepository] = None,
        fusion_repo: Optional[FusionRepository] = None,
    ) -> None:
        self._feature_repo = feature_repo or FeatureRepository()
        self._fusion_repo = fusion_repo or FusionRepository()

    def build(self, mode: str, rebuild: bool = False) -> tuple[pd.DataFrame, FusionValidationReport]:
        """
        Build a fused dataset for a specific fusion mode.

        Parameters
        ----------
        mode : str
            Fusion mode to run.
        rebuild : bool
            If True, forces a full rebuild. If False, runs incrementally if possible.

        Returns
        -------
        tuple[pd.DataFrame, FusionValidationReport]
            The fused DataFrame and its validation report.
        """
        if mode not in self._fusion_repo.list_modes():
            raise ValueError(
                f"Unsupported fusion mode: '{mode}'. "
                f"Must be one of {self._fusion_repo.list_modes()}"
            )

        logger.info("Starting feature fusion | mode=%s rebuild=%s", mode, rebuild)

        # 1. Load the master feature dataset
        df_features = self._feature_repo.load_dataframe()
        if df_features.empty:
            logger.error("Master feature dataset is empty. Cannot perform fusion.")
            report = FusionValidationReport(
                mode=mode,
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=False,
                errors=["Master feature dataset is empty."],
            )
            return pd.DataFrame(), report

        # Ensure all key columns exist
        key_cols = ["record_id", "bill_id", "company_isin", "event_window"]
        for col in key_cols:
            if col not in df_features.columns:
                logger.error("Key column '%s' missing from features dataset.", col)
                report = FusionValidationReport(
                    mode=mode,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    success=False,
                    errors=[f"Key column '{col}' missing from features dataset."],
                )
                return pd.DataFrame(), report

        # 2. Check if we can run incrementally
        if not rebuild and self._fusion_repo.exists(mode):
            try:
                df_existing = self._fusion_repo.load(mode)
                if not df_existing.empty and "record_id" in df_existing.columns:
                    # Identify records in source features that are not in the existing fused dataset
                    existing_records = set(df_existing["record_id"].tolist())
                    source_records = set(df_features["record_id"].tolist())
                    new_record_ids = source_records - existing_records

                    if not new_record_ids:
                        logger.info("Incremental build: no new records to fuse for mode '%s'.", mode)
                        report = self._fusion_repo.load_report(mode)
                        if report is None:
                            # Re-run validation just in case report was missing
                            report = self._validate(mode, df_existing, df_features)
                            self._fusion_repo.save(mode, df_existing, report)
                        return df_existing, report

                    logger.info("Incremental build: found %d new records to fuse.", len(new_record_ids))
                    df_new_features = df_features[df_features["record_id"].isin(new_record_ids)].copy()

                    # Fuse only the new records
                    df_new_fused = self._fuse_records(mode, df_new_features)

                    # Concatenate with existing
                    df_fused = pd.concat([df_existing, df_new_fused], ignore_index=True)

                    # Run validation on the final combined dataset
                    report = self._validate(mode, df_fused, df_features)

                    # Save to repository
                    self._fusion_repo.save(mode, df_fused, report)
                    return df_fused, report
            except Exception as exc:
                logger.warning(
                    "Failed to load existing fused dataset for incremental update. "
                    "Running full rebuild instead. Reason: %s",
                    exc,
                )

        # 3. Full rebuild path
        logger.info("Running full rebuild for fusion mode '%s'.", mode)
        df_fused = self._fuse_records(mode, df_features.copy())

        # Run validation
        report = self._validate(mode, df_fused, df_features)

        # Save to repository
        self._fusion_repo.save(mode, df_fused, report)
        return df_fused, report

    def _fuse_records(self, mode: str, df_base: pd.DataFrame) -> pd.DataFrame:
        """Helper to join features and embeddings for a given subset of records."""
        # 1. Separate keys and structured features
        key_cols = ["record_id", "bill_id", "company_isin", "event_window"]

        # Determine which features to include
        include_structured = "structured" in mode or mode == "hybrid"
        include_finbert = "finbert" in mode or mode == "hybrid"
        include_legal = "legal" in mode or mode == "hybrid"

        if include_structured:
            # Keep all columns from features
            df_result = df_base
        else:
            # Keep only the key columns
            df_result = df_base[key_cols].copy()

        # 2. Join FinBERT embeddings if required
        if include_finbert:
            df_result = self._join_embeddings(df_result, "finbert", "finbert_emb")

        # 3. Join Legal embeddings if required
        if include_legal:
            df_result = self._join_embeddings(df_result, "legal-roberta", "legal_emb")

        return df_result

    def _join_embeddings(self, df_target: pd.DataFrame, model_name: str, prefix: str) -> pd.DataFrame:
        """Load embeddings from EmbeddingRepository, join on bill_id, and expand dimensions."""
        from config.settings import settings

        try:
            emb_repo = EmbeddingRepository(model_name=model_name)
            df_emb = emb_repo.load_dataframe()
        except Exception as exc:
            logger.error("Failed to load embeddings for model '%s': %s", model_name, exc)
            df_emb = pd.DataFrame()

        dimension = settings.EMBEDDING_DIMENSIONS.get(model_name, 768)

        if df_emb.empty or "bill_id" not in df_emb.columns:
            logger.warning("Embedding repository for model '%s' is empty or missing bill_id.", model_name)
            # Create NaN columns for embeddings to keep schema consistent
            nan_df = pd.DataFrame(np.nan, index=df_target.index, columns=[f"{prefix}_{i}" for i in range(dimension)])
            return pd.concat([df_target, nan_df], axis=1)

        # We only need bill_id and the embedding_vector column
        df_emb_subset = df_emb[["bill_id", "embedding_vector"]].copy()

        # Perform left join on bill_id
        df_joined = pd.merge(df_target, df_emb_subset, on="bill_id", how="left")

        # Expand the embedding vector column into individual dimensions
        df_joined = self._expand_vector_column(df_joined, "embedding_vector", prefix, dimension)

        return df_joined

    @staticmethod
    def _expand_vector_column(df: pd.DataFrame, vector_col: str, prefix: str, dimension: int) -> pd.DataFrame:
        """Expand a column of lists into individual numeric columns."""
        if df.empty or vector_col not in df.columns:
            return df

        vectors = df[vector_col].tolist()
        col_names = [f"{prefix}_{i}" for i in range(dimension)]

        expanded_rows = []
        for vec in vectors:
            if isinstance(vec, (list, np.ndarray)) and len(vec) == dimension:
                expanded_rows.append(vec)
            else:
                expanded_rows.append([np.nan] * dimension)

        expanded_df = pd.DataFrame(expanded_rows, columns=col_names, index=df.index)

        # Drop the original list column and concatenate expanded dimensions
        df_dropped = df.drop(columns=[vector_col])
        return pd.concat([df_dropped, expanded_df], axis=1)

    def _validate(
        self,
        mode: str,
        df_fused: pd.DataFrame,
        df_features: pd.DataFrame,
    ) -> FusionValidationReport:
        """Run validation rules on the fused dataset and generate a report."""
        from config.settings import settings

        errors = []
        warnings = []

        duplicate_rows_count = 0
        missing_embeddings_count = 0
        nan_values_count = 0
        mismatched_dimensions_count = 0
        mismatched_bill_ids_count = 0
        mismatched_company_ids_count = 0

        # Check 1: Duplicate rows (by record_id)
        if "record_id" in df_fused.columns:
            duplicates = df_fused.duplicated(subset=["record_id"])
            duplicate_rows_count = int(duplicates.sum())
            if duplicate_rows_count > 0:
                errors.append(f"Found {duplicate_rows_count} duplicate row(s) based on record_id.")
        else:
            errors.append("Key column 'record_id' is missing from fused dataset.")

        # Check 2: Missing embeddings & Nan values in keys / embeddings
        key_cols = ["record_id", "bill_id", "company_isin", "event_window"]
        for col in key_cols:
            if col in df_fused.columns:
                nan_keys = int(df_fused[col].isnull().sum())
                if nan_keys > 0:
                    nan_values_count += nan_keys
                    errors.append(f"Found {nan_keys} row(s) with NaN/null value in key column '{col}'.")

        # Determine expected embedding columns based on mode
        check_finbert = "finbert" in mode or mode == "hybrid"
        check_legal = "legal" in mode or mode == "hybrid"

        if check_finbert:
            finbert_dim = settings.EMBEDDING_DIMENSIONS.get("finbert", 768)
            finbert_cols = [f"finbert_emb_{i}" for i in range(finbert_dim)]
            
            # Check dimensions present
            present_finbert_cols = [c for c in df_fused.columns if c.startswith("finbert_emb_")]
            if len(present_finbert_cols) != finbert_dim:
                mismatched_dimensions_count += 1
                errors.append(f"Expected {finbert_dim} FinBERT columns, found {len(present_finbert_cols)}.")
            
            # Check for NaNs/missing values
            if present_finbert_cols:
                missing_rows = int(df_fused[present_finbert_cols].isnull().any(axis=1).sum())
                if missing_rows > 0:
                    missing_embeddings_count += missing_rows
                    nan_values_count += int(df_fused[present_finbert_cols].isnull().sum().sum())
                    errors.append(f"Found {missing_rows} row(s) with missing/NaN FinBERT embeddings.")

        if check_legal:
            legal_dim = settings.EMBEDDING_DIMENSIONS.get("legal-roberta", 768)
            legal_cols = [f"legal_emb_{i}" for i in range(legal_dim)]
            
            # Check dimensions present
            present_legal_cols = [c for c in df_fused.columns if c.startswith("legal_emb_")]
            if len(present_legal_cols) != legal_dim:
                mismatched_dimensions_count += 1
                errors.append(f"Expected {legal_dim} Legal columns, found {len(present_legal_cols)}.")
            
            # Check for NaNs/missing values
            if present_legal_cols:
                missing_rows = int(df_fused[present_legal_cols].isnull().any(axis=1).sum())
                if missing_rows > 0:
                    missing_embeddings_count += missing_rows
                    nan_values_count += int(df_fused[present_legal_cols].isnull().sum().sum())
                    errors.append(f"Found {missing_rows} row(s) with missing/NaN Legal embeddings.")

        # Check 3: NaN values in structured columns (reported as Warnings)
        emb_cols = [c for c in df_fused.columns if c.startswith("finbert_emb_") or c.startswith("legal_emb_")]
        structured_cols = [c for c in df_fused.columns if c not in key_cols and c not in emb_cols]

        nan_structured_summary = {}
        for col in structured_cols:
            nulls = int(df_fused[col].isnull().sum())
            if nulls > 0:
                nan_structured_summary[col] = nulls

        if nan_structured_summary:
            warnings.append(f"NaN values found in structured features: {nan_structured_summary}")

        # Check 4: Matching Bill IDs
        if "bill_id" in df_fused.columns:
            fused_bills = set(df_fused["bill_id"].dropna().unique())
            feature_bills = set(df_features["bill_id"].dropna().unique())
            
            mismatched_bills = fused_bills - feature_bills
            mismatched_bill_ids_count = len(mismatched_bills)
            if mismatched_bill_ids_count > 0:
                errors.append(f"Found {mismatched_bill_ids_count} bill ID(s) in fused dataset that do not exist in master features.")

        # Check 5: Matching Company IDs
        if "company_isin" in df_fused.columns:
            fused_companies = set(df_fused["company_isin"].dropna().unique())
            feature_companies = set(df_features["company_isin"].dropna().unique())
            
            mismatched_companies = fused_companies - feature_companies
            mismatched_company_ids_count = len(mismatched_companies)
            if mismatched_company_ids_count > 0:
                errors.append(f"Found {mismatched_company_ids_count} company ISIN(s) in fused dataset that do not exist in master features.")

        success = len(errors) == 0

        # Construct details dictionary
        details = {
            "total_rows": len(df_fused),
            "columns_count": len(df_fused.columns),
            "nan_structured_columns": nan_structured_summary,
        }

        return FusionValidationReport(
            mode=mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=success,
            duplicate_rows_count=duplicate_rows_count,
            missing_embeddings_count=missing_embeddings_count,
            nan_values_count=nan_values_count,
            mismatched_dimensions_count=mismatched_dimensions_count,
            mismatched_bill_ids_count=mismatched_bill_ids_count,
            mismatched_company_ids_count=mismatched_company_ids_count,
            errors=errors,
            warnings=warnings,
            details=details,
        )
