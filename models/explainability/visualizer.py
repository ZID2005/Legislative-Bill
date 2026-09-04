"""
models/explainability/visualizer.py
=====================================
ExplainabilityVisualizer — Task 6.3.

Generates and saves all SHAP-based visualizations using matplotlib and the
SHAP library.  All plots use the non-interactive ``Agg`` backend so this
module is safe for server / CI environments.

Charts produced
---------------
Per (target, model_type):
  * ``summary_plot.png``         — SHAP beeswarm summary plot
  * ``bar_plot.png``             — Mean |SHAP| bar chart (top 20 features)
  * ``dependence_plots/``        — One scatter per top-10 feature

Global:
  * ``feature_comparison.png``   — Grouped bar chart comparing top-20 features
                                    across all model types for every target
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from config.logging_config import get_logger

logger = get_logger(__name__)

# Use non-interactive backend before importing pyplot
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.cm
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    plt = None  # type: ignore[assignment]
    logger.warning("matplotlib not installed. Visualizations will be skipped.")

# SHAP is optional at import time — guarded at call sites
try:
    import shap as _shap  # noqa: F401
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    logger.warning("shap not installed. SHAP visualizations will be skipped.")

_DPI = 150
_FIGSIZE_LARGE = (14, 8)
_FIGSIZE_MEDIUM = (12, 6)

# Palette for cross-model comparison
_MODEL_COLORS: dict[str, str] = {
    "lgbm": "#4C72B0",
    "xgboost": "#DD8452",
    "random_forest": "#55A868",
}


class ExplainabilityVisualizer:
    """
    Generates and saves SHAP visualizations.

    Parameters
    ----------
    repo : ExplainabilityRepository
        Repository that provides directory paths for saving plots.
    top_n_features : int, optional
        Number of top features to show in summary / bar plots (default: 20).
    top_n_dependence : int, optional
        Number of top features for which dependence plots are generated
        (default: 10).
    """

    def __init__(
        self,
        repo: Any,
        top_n_features: int = 20,
        top_n_dependence: int = 10,
    ) -> None:
        self._repo = repo
        self._top_n = top_n_features
        self._top_dep = top_n_dependence

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def save_summary_plot(
        self,
        target: str,
        model_type: str,
        shap_values: np.ndarray,
        feature_matrix: np.ndarray,
        feature_names: list[str],
    ) -> Path:
        """
        Generate and save the SHAP beeswarm summary plot.

        Parameters
        ----------
        target, model_type : str
            Used to resolve the output directory.
        shap_values : np.ndarray
            Shape (n_samples, n_features) for binary/multiclass (first class
            or mean across classes is accepted).
        feature_matrix : np.ndarray
            Original feature values (n_samples, n_features).
        feature_names : list[str]
            Ordered feature names matching columns.

        Returns
        -------
        Path
            Absolute path of the saved PNG.
        """
        out_path = self._repo.model_dir(target, model_type) / "summary_plot.png"

        if not HAS_SHAP:
            logger.warning("SHAP not available. Skipping summary plot.")
            return out_path

        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib not available. Skipping summary plot.")
            return out_path

        import shap

        sv = self._coerce_2d(shap_values)

        try:
            fig, ax = plt.subplots(figsize=_FIGSIZE_LARGE)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                shap.summary_plot(
                    sv,
                    feature_matrix,
                    feature_names=feature_names,
                    max_display=self._top_n,
                    show=False,
                    plot_type="dot",
                )
            plt.title(
                f"SHAP Summary Plot — {target.replace('_', ' ').title()} / {model_type.upper()}",
                fontsize=13,
                pad=12,
            )
            plt.tight_layout()
            plt.savefig(out_path, dpi=_DPI, bbox_inches="tight")
            plt.close("all")
            logger.info("Saved summary plot: %s", out_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Summary plot failed for %s/%s: %s", target, model_type, exc)
            plt.close("all")

        return out_path

    def save_bar_plot(
        self,
        target: str,
        model_type: str,
        feature_importance_df: pd.DataFrame,
    ) -> Path:
        """
        Generate and save the mean |SHAP| bar chart.

        Parameters
        ----------
        feature_importance_df : pd.DataFrame
            Must have columns ``feature`` and ``mean_abs_shap``, sorted
            descending.

        Returns
        -------
        Path
            Absolute path of the saved PNG.
        """
        out_path = self._repo.model_dir(target, model_type) / "bar_plot.png"

        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib not available. Skipping bar plot.")
            return out_path

        top_df = feature_importance_df.head(self._top_n)

        fig, ax = plt.subplots(figsize=_FIGSIZE_LARGE)
        colors = plt.cm.viridis(
            np.linspace(0.15, 0.85, len(top_df))[::-1]  # type: ignore[arg-type]
        )
        ax.barh(
            top_df["feature"][::-1],
            top_df["mean_abs_shap"][::-1],
            color=colors,
            edgecolor="white",
            linewidth=0.5,
        )
        ax.set_xlabel("Mean |SHAP value|", fontsize=11)
        ax.set_title(
            f"Global Feature Importance — {target.replace('_', ' ').title()} / {model_type.upper()}",
            fontsize=13,
            pad=12,
        )
        ax.tick_params(axis="y", labelsize=9)
        ax.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig(out_path, dpi=_DPI, bbox_inches="tight")
        plt.close("all")
        logger.info("Saved bar plot: %s", out_path)
        return out_path

    def save_dependence_plots(
        self,
        target: str,
        model_type: str,
        shap_values: np.ndarray,
        feature_matrix: np.ndarray,
        feature_names: list[str],
        feature_importance_df: pd.DataFrame,
    ) -> list[Path]:
        """
        Generate and save SHAP dependence plots for the top-N features.

        Returns
        -------
        list[Path]
            Paths of all saved PNG files.
        """
        if not HAS_SHAP:
            logger.warning("SHAP not available. Skipping dependence plots.")
            return []

        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib not available. Skipping dependence plots.")
            return []

        import shap

        dep_dir = self._repo.dependence_dir(target, model_type)
        sv = self._coerce_2d(shap_values)

        top_features = feature_importance_df["feature"].head(self._top_dep).tolist()
        paths: list[Path] = []

        for feat in top_features:
            if feat not in feature_names:
                continue
            feat_idx = feature_names.index(feat)
            safe_name = feat.replace("/", "_").replace(" ", "_")
            out_path = dep_dir / f"{safe_name}_dependence.png"

            try:
                fig, ax = plt.subplots(figsize=_FIGSIZE_MEDIUM)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    shap.dependence_plot(
                        feat_idx,
                        sv,
                        feature_matrix,
                        feature_names=feature_names,
                        ax=ax,
                        show=False,
                    )
                ax.set_title(
                    f"SHAP Dependence: {feat}\n"
                    f"{target.replace('_', ' ').title()} / {model_type.upper()}",
                    fontsize=11,
                    pad=8,
                )
                plt.tight_layout()
                plt.savefig(out_path, dpi=_DPI, bbox_inches="tight")
                plt.close("all")
                paths.append(out_path)
                logger.debug("Saved dependence plot: %s", out_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Dependence plot failed for feature=%s: %s", feat, exc
                )
                plt.close("all")

        logger.info(
            "Saved %d dependence plots for %s/%s in %s",
            len(paths), target, model_type, dep_dir,
        )
        return paths

    def save_feature_comparison(
        self,
        comparison_data: dict[str, dict[str, dict[str, float]]],
        out_path: Path,
        top_n: int = 20,
    ) -> Path:
        """
        Generate and save the cross-model feature importance comparison chart.

        Parameters
        ----------
        comparison_data : dict
            Structure: ``{target: {model_type: {feature: mean_abs_shap}}}``
        out_path : Path
            Destination path for the PNG.
        top_n : int
            Number of top features to show per target panel.

        Returns
        -------
        Path
            Absolute path of the saved PNG.
        """
        targets = sorted(comparison_data.keys())
        n_targets = len(targets)

        if n_targets == 0:
            logger.warning("No comparison data supplied — skipping feature_comparison.png.")
            return out_path

        if not HAS_MATPLOTLIB:
            logger.warning("matplotlib not available. Skipping feature_comparison.png.")
            return out_path

        fig, axes = plt.subplots(
            n_targets,
            1,
            figsize=(14, 6 * n_targets),
            squeeze=False,
        )

        for row_idx, target in enumerate(targets):
            ax = axes[row_idx][0]
            model_importances = comparison_data[target]
            model_types = sorted(model_importances.keys())

            # Union of all features ranked by their maximum importance across models
            all_features: dict[str, float] = {}
            for model_type, fi in model_importances.items():
                for feat, val in fi.items():
                    all_features[feat] = max(all_features.get(feat, 0.0), val)

            top_features = sorted(all_features, key=all_features.get, reverse=True)[:top_n]  # type: ignore[arg-type]
            if not top_features:
                ax.set_visible(False)
                continue

            x = np.arange(len(top_features))
            bar_width = 0.8 / max(len(model_types), 1)

            for m_idx, model_type in enumerate(model_types):
                fi = model_importances.get(model_type, {})
                values = [fi.get(feat, 0.0) for feat in top_features]
                offset = (m_idx - len(model_types) / 2 + 0.5) * bar_width
                ax.bar(
                    x + offset,
                    values,
                    bar_width * 0.9,
                    label=model_type.upper(),
                    color=_MODEL_COLORS.get(model_type, f"C{m_idx}"),
                    alpha=0.85,
                    edgecolor="white",
                    linewidth=0.4,
                )

            ax.set_xticks(x)
            ax.set_xticklabels(top_features, rotation=45, ha="right", fontsize=8)
            ax.set_ylabel("Mean |SHAP value|", fontsize=10)
            ax.set_title(
                f"Feature Importance Comparison — {target.replace('_', ' ').title()}",
                fontsize=12,
                pad=10,
            )
            ax.legend(fontsize=9)
            ax.grid(axis="y", alpha=0.3)

        plt.suptitle(
            "Cross-Model Feature Importance Comparison (SHAP)",
            fontsize=14,
            fontweight="bold",
            y=1.002,
        )
        plt.tight_layout()
        plt.savefig(out_path, dpi=_DPI, bbox_inches="tight")
        plt.close("all")
        logger.info("Saved feature comparison plot: %s", out_path)
        return out_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _coerce_2d(shap_values: np.ndarray) -> np.ndarray:
        """
        Reduce SHAP arrays to 2-D (n_samples × n_features).

        For multiclass models shap_values may be a 3-D array
        (n_classes × n_samples × n_features) or a list of 2-D arrays.
        We take the absolute-mean across classes so we can display
        global importance as a single 2-D matrix.
        """
        if isinstance(shap_values, list):
            # List of per-class arrays → average absolute values
            stacked = np.stack([np.abs(sv) for sv in shap_values], axis=0)
            return stacked.mean(axis=0)

        if shap_values.ndim == 3:
            # (n_classes, n_samples, n_features) → mean |shap| across classes
            return np.abs(shap_values).mean(axis=0)

        return shap_values
