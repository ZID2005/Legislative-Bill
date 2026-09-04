"""
features/selection_engine.py
============================
Feature Selection Engine for filter-based and model-based feature pruning (Task 5.4).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pandas as pd
from config.logging_config import get_logger
from schemas.feature_selection_validation_report import FeatureSelectionValidationReport
from storage.feature_repository import FeatureRepository
from storage.feature_selection_repository import FeatureSelectionRepository
from storage.fusion_repository import FusionRepository

logger = get_logger(__name__)

try:
    from lightgbm import LGBMClassifier
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif


class FeatureSelectionEngine:
    """
    Feature Selection Engine.

    Prunes uninformative, redundant, or constant features from fused datasets
    to avoid overfitting and improve model training performance.
    """

    def __init__(
        self,
        fusion_repo: Optional[FusionRepository] = None,
        selection_repo: Optional[FeatureSelectionRepository] = None,
        feature_repo: Optional[FeatureRepository] = None,
    ) -> None:
        self._fusion_repo = fusion_repo or FusionRepository()
        self._selection_repo = selection_repo or FeatureSelectionRepository()
        self._feature_repo = feature_repo or FeatureRepository()

    def select_features(
        self,
        mode: str,
        missing_threshold: Optional[float] = 0.5,
        correlation_threshold: float = 0.95,
        variance_threshold: float = 0.01,
        rebuild: bool = False,
        use_lightgbm: bool = True,
    ) -> tuple[pd.DataFrame, FeatureSelectionValidationReport]:
        """
        Run the feature selection pipeline on the fused dataset for the given mode.

        Parameters
        ----------
        mode : str
            The fusion mode to run selection on.
        missing_threshold : float, optional
            Threshold above which columns with missing values are removed (e.g. 0.5).
            If None, missing-value pruning is skipped.
        correlation_threshold : float
            Pearson correlation threshold above which one of the pair is removed (default 0.95).
        variance_threshold : float
            Near-zero variance threshold. Columns with variance <= this are removed (default 0.01).
        rebuild : bool
            Force full rebuild even if selection files exist.
        use_lightgbm : bool
            If True, uses LightGBM if installed. Otherwise falls back to Random Forest.

        Returns
        -------
        tuple[pd.DataFrame, FeatureSelectionValidationReport]
            Selected feature DataFrame and its validation report.
        """
        if rebuild is False and self._selection_repo.exists(mode):
            logger.info("Feature selection output already exists for mode '%s'. Loading.", mode)
            df_selected = self._selection_repo.load(mode)
            report = self._selection_repo.load_report(mode)
            if report is not None:
                return df_selected, report

        logger.info("Starting feature selection pipeline | mode=%s", mode)

        # 1. Load the fused dataset
        df_fused = self._fusion_repo.load(mode)
        if df_fused.empty:
            raise ValueError(f"Fused dataset for mode '{mode}' is empty.")

        # 2. Identify key metadata and target columns
        metadata_cols = [
            "record_id", "bill_id", "company_isin", "event_window",
            "bill_title", "company_name", "nse_symbol", "isin",
            "introduction_date", "feature_version", "built_at"
        ]
        target_cols = ["direction", "market_moving", "impact_strength", "confidence_label"]
        preserved_cols = [c for c in df_fused.columns if c in metadata_cols or c in target_cols]
        feature_cols = [c for c in df_fused.columns if c not in metadata_cols and c not in target_cols]

        logger.info(
            "Initial columns: total=%d, features=%d, preserved=%d",
            len(df_fused.columns), len(feature_cols), len(preserved_cols)
        )

        removed_features: dict[str, list[str]] = {
            "constant": [],
            "duplicate": [],
            "missing_values": [],
            "low_variance": [],
            "high_correlation": []
        }

        # Step A: Missing-value analysis & optional pruning
        missing_pcts = df_fused[feature_cols].isnull().mean().to_dict()
        if missing_threshold is not None:
            for col, pct in missing_pcts.items():
                if pct >= missing_threshold:
                    removed_features["missing_values"].append(col)
            # Filter remaining features
            feature_cols = [c for c in feature_cols if c not in removed_features["missing_values"]]
            logger.info("Removed %d feature(s) exceeding missing threshold.", len(removed_features["missing_values"]))

        # Step B: Remove constant features (0 std or unique values <= 1)
        for col in feature_cols:
            try:
                unique_vals = df_fused[col].nunique(dropna=False)
            except TypeError:
                unique_vals = 2  # Treat unhashable columns (e.g. lists) as non-constant
            
            if unique_vals <= 1:
                removed_features["constant"].append(col)
            elif pd.api.types.is_numeric_dtype(df_fused[col]) and df_fused[col].std() == 0:
                removed_features["constant"].append(col)
        feature_cols = [c for c in feature_cols if c not in removed_features["constant"]]
        logger.info("Removed %d constant feature(s).", len(removed_features["constant"]))

        # Step C: Remove duplicate features
        seen_hashes = {}
        for col in feature_cols:
            try:
                # Use standard hash of values with filled NaNs to avoid float hashing issues
                val_tuple = tuple(df_fused[col].fillna(-999999.9).tolist())
                if val_tuple in seen_hashes:
                    removed_features["duplicate"].append(col)
                else:
                    seen_hashes[val_tuple] = col
            except Exception:
                # Slower fallback using pandas equals
                is_dup = False
                for seen_col in seen_hashes.values():
                    if df_fused[col].equals(df_fused[seen_col]):
                        removed_features["duplicate"].append(col)
                        is_dup = True
                        break
                if not is_dup:
                    seen_hashes[col] = col
        feature_cols = [c for c in feature_cols if c not in removed_features["duplicate"]]
        logger.info("Removed %d duplicate feature(s).", len(removed_features["duplicate"]))

        # Step D: Variance Threshold (remove low/zero variance features)
        for col in feature_cols:
            if pd.api.types.is_numeric_dtype(df_fused[col]):
                var = df_fused[col].var(ddof=0)
                if pd.isnull(var) or var <= variance_threshold:
                    removed_features["low_variance"].append(col)
        feature_cols = [c for c in feature_cols if c not in removed_features["low_variance"]]
        logger.info("Removed %d near-zero variance feature(s).", len(removed_features["low_variance"]))

        # Step E: Pearson Correlation Analysis (remove one feature from highly correlated pairs)
        numeric_features = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df_fused[c])]
        if len(numeric_features) > 1:
            corr_matrix = df_fused[numeric_features].corr(method="pearson").abs()
            correlated_set = set()
            for i in range(len(numeric_features)):
                col1 = numeric_features[i]
                if col1 in correlated_set:
                    continue
                for j in range(i + 1, len(numeric_features)):
                    col2 = numeric_features[j]
                    if col2 in correlated_set:
                        continue
                    if corr_matrix.loc[col1, col2] >= correlation_threshold:
                        correlated_set.add(col2)
            removed_features["high_correlation"] = list(correlated_set)
            feature_cols = [c for c in feature_cols if c not in correlated_set]
            logger.info("Removed %d highly correlated feature(s).", len(removed_features["high_correlation"]))

        # Final selected features
        selected_cols = preserved_cols + feature_cols
        df_selected = df_fused[selected_cols].copy()

        # Step F: Mutual Information & Tree-based Importance
        # Dynamically load targets from master feature dataset if missing
        try:
            df_master = self._feature_repo.load_dataframe()
        except Exception as exc:
            logger.warning("Could not load master features for dynamic label retrieval: %s", exc)
            df_master = pd.DataFrame()

        # Merge targets into temporary copy if missing
        df_temp_analysis = df_fused.copy()
        for col in target_cols:
            if col not in df_temp_analysis.columns and not df_master.empty and "record_id" in df_master.columns:
                if col in df_master.columns:
                    df_temp_analysis = pd.merge(
                        df_temp_analysis,
                        df_master[["record_id", col]],
                        on="record_id",
                        how="left"
                    )

        importance_df = self._calculate_importance(
            df=df_temp_analysis,
            features=feature_cols,
            targets=target_cols,
            use_lightgbm=use_lightgbm
        )

        # Validation
        timestamp_str = datetime.now(timezone.utc).isoformat()
        validation_errors = []
        validation_warnings = []

        # 1. No duplicate columns
        no_duplicate_columns = len(df_selected.columns) == len(set(df_selected.columns))
        if not no_duplicate_columns:
            validation_errors.append("Selected dataset contains duplicate columns.")

        # 2. No NaN-only columns
        nan_only_cols = []
        for i in range(df_selected.shape[1]):
            col_name = df_selected.columns[i]
            if col_name in metadata_cols or col_name in target_cols:
                continue
            col_data = df_selected.iloc[:, i]
            if col_data.isnull().all():
                nan_only_cols.append(col_name)
        no_nan_only_columns = len(nan_only_cols) == 0
        if not no_nan_only_columns:
            validation_errors.append(f"NaN-only columns found in output: {nan_only_cols}")

        # 3. Selected features exist
        # Check if there's at least one feature column (outside preserved keys/targets)
        features_in_selected = [c for c in df_selected.columns if c not in metadata_cols and c not in target_cols]
        selected_features_exist = len(features_in_selected) > 0
        if not selected_features_exist:
            validation_errors.append("No feature columns were selected.")

        # 4. Ranking generated
        ranking_generated = not importance_df.empty
        if not ranking_generated:
            validation_warnings.append("Feature importance ranking was not generated successfully.")

        success = len(validation_errors) == 0

        # Construct selection validation report
        details = {
            "original_columns_count": len(df_fused.columns),
            "selected_columns_count": len(df_selected.columns),
            "original_features_count": len(fused_cols := [c for c in df_fused.columns if c not in metadata_cols and c not in target_cols]),
            "selected_features_count": len(feature_cols),
            "missing_percentages": missing_pcts,
            "removed_features_summary": {k: len(v) for k, v in removed_features.items()}
        }

        report = FeatureSelectionValidationReport(
            mode=mode,
            timestamp=timestamp_str,
            success=success,
            no_duplicate_columns=no_duplicate_columns,
            no_nan_only_columns=no_nan_only_columns,
            selected_features_exist=selected_features_exist,
            ranking_generated=ranking_generated,
            errors=validation_errors,
            warnings=validation_warnings,
            details=details
        )

        # Save results to repository
        self._selection_repo.save(
            mode=mode,
            df=df_selected,
            importance=importance_df,
            removed=removed_features,
            report=report
        )

        return df_selected, report

    def _calculate_importance(
        self,
        df: pd.DataFrame,
        features: list[str],
        targets: list[str],
        use_lightgbm: bool
    ) -> pd.DataFrame:
        """Calculate ranked feature importance (Mutual Information and Tree-based)."""
        if not features:
            logger.warning("No features provided for importance calculation.")
            return pd.DataFrame()

        # Initialize importance dictionary
        importance_data: dict[str, list] = {"feature": features}
        for target in targets:
            importance_data[f"mi_{target}"] = [0.0] * len(features)
            importance_data[f"tree_{target}"] = [0.0] * len(features)

        # Impute missing values and encode categoricals for importance estimators
        df_clean = df.copy()
        for col in features:
            if pd.api.types.is_numeric_dtype(df_clean[col]):
                mean_val = df_clean[col].mean()
                df_clean[col] = df_clean[col].fillna(0.0 if pd.isnull(mean_val) else mean_val)
            else:
                df_clean[col] = df_clean[col].fillna("missing").astype(str).astype("category").cat.codes

        for target in targets:
            if target not in df_clean.columns:
                logger.debug("Target '%s' not present in data. Skipping importance.", target)
                continue

            # Drop missing targets for analysis
            valid_idx = df_clean[target].notnull()
            if not valid_idx.any():
                logger.debug("No valid non-null rows for target '%s'. Skipping.", target)
                continue

            X = df_clean.loc[valid_idx, features]
            # Convert target to category codes if not numeric
            y_raw = df_clean.loc[valid_idx, target]
            if pd.api.types.is_numeric_dtype(y_raw):
                # If target is binary float or integer, convert to int
                y = y_raw.astype(int)
            else:
                y = y_raw.astype(str).astype("category").cat.codes

            # Skip if target has only one unique class
            if len(np.unique(y)) <= 1:
                logger.debug("Target '%s' has <= 1 class. Skipping importance.", target)
                continue

            # 1. Mutual Information
            try:
                # Determine discrete features (e.g. integer or boolean features)
                discrete_features = [
                    not pd.api.types.is_float_dtype(X[col]) for col in X.columns
                ]
                mi_scores = mutual_info_classif(
                    X, y,
                    discrete_features=discrete_features,
                    random_state=42
                )
                importance_data[f"mi_{target}"] = list(mi_scores)
            except Exception as exc:
                logger.warning("Failed to calculate Mutual Information for target '%s': %s", target, exc)

            # 2. Tree-based Importance
            try:
                if use_lightgbm and HAS_LIGHTGBM:
                    model = LGBMClassifier(
                        n_estimators=50,
                        random_state=42,
                        verbose=-1
                    )
                else:
                    model = RandomForestClassifier(
                        n_estimators=50,
                        random_state=42,
                        n_jobs=-1
                    )
                model.fit(X, y)
                importance_data[f"tree_{target}"] = list(model.feature_importances_)
            except Exception as exc:
                logger.warning("Failed to calculate tree importance for target '%s': %s", target, exc)

        # Assemble DataFrame
        importance_df = pd.DataFrame(importance_data)

        # Normalize and calculate overall mean importance
        mi_cols = [c for c in importance_df.columns if c.startswith("mi_")]
        tree_cols = [c for c in importance_df.columns if c.startswith("tree_")]
        all_score_cols = mi_cols + tree_cols

        norm_df = importance_df.copy()
        for col in all_score_cols:
            col_sum = norm_df[col].sum()
            if col_sum > 0:
                norm_df[col] = norm_df[col] / col_sum
            else:
                norm_df[col] = 0.0

        importance_df["mean_importance"] = norm_df[all_score_cols].mean(axis=1)
        importance_df = importance_df.sort_values(by="mean_importance", ascending=False)

        return importance_df
