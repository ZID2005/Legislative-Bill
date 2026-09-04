"""
backtesting/visualizer.py
=========================
Matplotlib plot generators for the Historical Backtesting Engine
(Task 6.4 / 6.4.1).

Task 6.4.1 Updates
-------------------
* ``plot_equity_curve`` — now plots compounded portfolio wealth (initial_capital=1.0)
  rather than cumulative sum of individual CARs.
* ``plot_drawdown_curve`` — uses wealth-relative drawdown from PortfolioSnapshot series.
* New ``plot_daily_returns`` — bar chart of per-date portfolio returns.
* New ``plot_signal_distribution`` — long/short/neutral signal breakdown.
* ``plot_prediction_vs_actual`` — unchanged from Task 6.4.
* ``plot_model_comparison`` — unchanged from Task 6.4.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from schemas.backtest_record import BacktestRecord, PortfolioSnapshot

logger = get_logger(__name__)


class BacktestVisualizer:
    """
    Generates PNG visualisations for backtest run evaluation.
    """

    def generate_all_plots(
        self,
        output_dir: Path,
        records: list[BacktestRecord],
        snapshots: Optional[list[PortfolioSnapshot]] = None,
        model_comparison_data: Optional[dict[str, Any]] = None,
        nifty_returns: Optional[list[float]] = None,
    ) -> dict[str, Path]:
        """
        Generate all backtest PNG plots and return dict mapping plot names to paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        plots: dict[str, Path] = {}

        try:
            p_eq = self.plot_equity_curve(
                output_dir / "equity_curve.png", records, snapshots=snapshots
            )
            plots["equity_curve"] = p_eq
        except Exception as exc:
            logger.error("Failed equity_curve.png: %s", exc)

        try:
            p_dd = self.plot_drawdown_curve(
                output_dir / "drawdown_curve.png", records, snapshots=snapshots
            )
            plots["drawdown_curve"] = p_dd
        except Exception as exc:
            logger.error("Failed drawdown_curve.png: %s", exc)

        try:
            p_dr = self.plot_daily_returns(
                output_dir / "daily_returns.png", snapshots or []
            )
            plots["daily_returns"] = p_dr
        except Exception as exc:
            logger.error("Failed daily_returns.png: %s", exc)

        try:
            p_pa = self.plot_prediction_vs_actual(
                output_dir / "prediction_vs_actual.png", records
            )
            plots["prediction_vs_actual"] = p_pa
        except Exception as exc:
            logger.error("Failed prediction_vs_actual.png: %s", exc)

        try:
            p_sd = self.plot_signal_distribution(
                output_dir / "signal_distribution.png", records
            )
            plots["signal_distribution"] = p_sd
        except Exception as exc:
            logger.error("Failed signal_distribution.png: %s", exc)

        try:
            p_mc = self.plot_model_comparison(
                output_dir / "model_comparison.png", model_comparison_data
            )
            plots["model_comparison"] = p_mc
        except Exception as exc:
            logger.error("Failed model_comparison.png: %s", exc)

        return plots

    def plot_equity_curve(
        self,
        save_path: Path,
        records: list[BacktestRecord],
        snapshots: Optional[list[PortfolioSnapshot]] = None,
        nifty_returns: Optional[list[float]] = None,
    ) -> Path:
        """
        Plot compounded portfolio wealth curve vs Buy-and-Hold and NIFTY 50.

        Uses PortfolioSnapshot series if available (Task 6.4.1 corrected).
        Falls back to cumulative sum of individual records for compatibility.
        """
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)

        if not records and not snapshots:
            ax.text(0.5, 0.5, "No Backtest Records Available", ha="center", va="center")
            fig.savefig(save_path, bbox_inches="tight")
            plt.close(fig)
            return save_path

        if snapshots:
            # Preferred: use portfolio snapshots (correct)
            dates_str = [s.date for s in snapshots]
            try:
                x_axis = pd.to_datetime(dates_str)
                use_dates = True
            except Exception:
                x_axis = np.arange(len(snapshots))
                use_dates = False

            pv = np.array([s.portfolio_value for s in snapshots])
            bah_vals = self._compound_series([s.bah_return for s in snapshots])
            nifty_vals = self._compound_series([s.nifty_return for s in snapshots])

            ax.plot(x_axis, pv, label="Strategy Portfolio (Compounded, net TC)", color="#1f77b4", linewidth=2.0)
            ax.plot(x_axis, bah_vals, label="Buy & Hold (Equal-Weight)", color="#ff7f0e", linestyle="--", linewidth=1.5)
            ax.plot(x_axis, nifty_vals, label="NIFTY 50 Index", color="#2ca02c", linestyle=":", linewidth=1.5)
            ax.axhline(1.0, color="gray", linestyle="-.", alpha=0.5, label="Initial Capital (1.0)")

            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{(y - 1) * 100:.1f}%"))
            if use_dates:
                fig.autofmt_xdate()
        else:
            # Fallback to cumsum
            strat_rets = np.array([r.strategy_return or 0.0 for r in records])
            raw_cars = np.array([
                r.cumulative_abnormal_return if r.cumulative_abnormal_return is not None else 0.0
                for r in records
            ])
            strat_cum = np.cumsum(strat_rets) * 100.0
            bah_cum = np.cumsum(raw_cars) * 100.0
            x_axis = np.arange(len(records))
            ax.plot(x_axis, strat_cum, label="Strategy (Cumulative Sum)", color="#1f77b4", linewidth=2.0)
            ax.plot(x_axis, bah_cum, label="Buy & Hold (CAR Sum)", color="#ff7f0e", linestyle="--", linewidth=1.5)
            ax.axhline(0, color="gray", linestyle="-.", alpha=0.5)
            ax.set_ylabel("Cumulative Return (%)", fontsize=10)

        ax.set_title("Historical Strategy Equity Curve vs Benchmarks\n(Task 6.4.1 — Corrected Compounded Returns)",
                     fontsize=11, fontweight="bold")
        ax.set_xlabel("Event Date", fontsize=10)
        ax.legend(loc="upper left", frameon=True, fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.6)

        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_drawdown_curve(
        self,
        save_path: Path,
        records: list[BacktestRecord],
        snapshots: Optional[list[PortfolioSnapshot]] = None,
    ) -> Path:
        """
        Plot wealth-relative drawdown curve from PortfolioSnapshot series.
        """
        fig, ax = plt.subplots(figsize=(12, 4), dpi=150)

        if not records and not snapshots:
            ax.text(0.5, 0.5, "No Backtest Records Available", ha="center", va="center")
            fig.savefig(save_path, bbox_inches="tight")
            plt.close(fig)
            return save_path

        if snapshots:
            dates_str = [s.date for s in snapshots]
            try:
                x_axis = pd.to_datetime(dates_str)
                use_dates = True
            except Exception:
                x_axis = np.arange(len(snapshots))
                use_dates = False

            drawdowns = np.array([s.drawdown for s in snapshots]) * 100.0  # convert to %

            ax.fill_between(x_axis, 0, drawdowns, color="#d62728", alpha=0.4, label="Strategy Drawdown")
            ax.plot(x_axis, drawdowns, color="#d62728", linewidth=1.2)

            max_dd = float(np.min(drawdowns))
            ax.axhline(max_dd, color="#d62728", linestyle="--", linewidth=0.8, alpha=0.7,
                       label=f"Max Drawdown: {max_dd:.2f}%")

            if use_dates:
                fig.autofmt_xdate()
            ax.set_title(
                "Strategy Drawdown (Wealth-Relative)\nDrawdown = portfolio_value/peak - 1 ≤ 0",
                fontsize=11, fontweight="bold"
            )
        else:
            # Fallback cumsum-based
            strat_rets = np.array([r.strategy_return or 0.0 for r in records])
            cum_curve = np.cumsum(strat_rets) * 100.0
            peak = np.maximum.accumulate(cum_curve)
            drawdown = peak - cum_curve

            x_axis = np.arange(len(records))
            ax.fill_between(x_axis, 0, -drawdown, color="#d62728", alpha=0.4, label="Strategy Drawdown")
            ax.plot(x_axis, -drawdown, color="#d62728", linewidth=1.2)
            ax.set_title("Historical Strategy Drawdown Curve", fontsize=11, fontweight="bold")

        ax.set_xlabel("Event Date", fontsize=10)
        ax.set_ylabel("Drawdown (%)", fontsize=10)
        ax.legend(loc="lower left", frameon=True, fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.6)

        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_daily_returns(
        self,
        save_path: Path,
        snapshots: list[PortfolioSnapshot],
    ) -> Path:
        """
        Bar chart of per-event-date portfolio returns (Task 6.4.1 new plot).
        """
        fig, ax = plt.subplots(figsize=(12, 4), dpi=150)

        if not snapshots:
            ax.text(0.5, 0.5, "No Snapshot Data", ha="center", va="center")
            fig.savefig(save_path, bbox_inches="tight")
            plt.close(fig)
            return save_path

        dates_str = [s.date for s in snapshots]
        rets = np.array([s.portfolio_return * 100.0 for s in snapshots])

        try:
            x_axis = pd.to_datetime(dates_str)
            use_dates = True
        except Exception:
            x_axis = np.arange(len(snapshots))
            use_dates = False

        colors = ["#1f77b4" if r >= 0 else "#d62728" for r in rets]
        if use_dates:
            ax.bar(x_axis, rets, color=colors, width=5, alpha=0.8)
            fig.autofmt_xdate()
        else:
            ax.bar(x_axis, rets, color=colors, alpha=0.8)

        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(
            "Per-Event-Date Portfolio Returns\n(Equal-Weighted Across Active Positions, Net TC)",
            fontsize=11, fontweight="bold"
        )
        ax.set_xlabel("Event Date", fontsize=10)
        ax.set_ylabel("Return (%)", fontsize=10)
        ax.grid(True, linestyle=":", alpha=0.5, axis="y")

        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_prediction_vs_actual(
        self,
        save_path: Path,
        records: list[BacktestRecord],
    ) -> Path:
        """Plot predicted class vs actual outcome distributions and confusion matrix."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=150)

        if not records:
            ax1.text(0.5, 0.5, "No Data", ha="center", va="center")
            fig.savefig(save_path, bbox_inches="tight")
            plt.close(fig)
            return save_path

        df = pd.DataFrame([r.to_dict() for r in records])

        classes = sorted(list(
            set(df["predicted_class"].astype(str)).union(set(df["actual_class"].astype(str)))
        ))
        pred_counts = df["predicted_class"].astype(str).value_counts().reindex(classes, fill_value=0)
        act_counts = df["actual_class"].astype(str).value_counts().reindex(classes, fill_value=0)

        x = np.arange(len(classes))
        width = 0.35

        ax1.bar(x - width / 2, pred_counts, width, label="Predicted", color="#1f77b4", alpha=0.85)
        ax1.bar(x + width / 2, act_counts, width, label="Actual", color="#aec7e8", alpha=0.85)
        ax1.set_xticks(x)
        ax1.set_xticklabels(classes, rotation=15)
        ax1.set_ylabel("Count")
        ax1.set_title("Predicted vs Actual Class Distribution", fontweight="bold")
        ax1.legend()
        ax1.grid(True, linestyle=":", alpha=0.5, axis="y")

        cm = pd.crosstab(
            df["actual_class"].astype(str),
            df["predicted_class"].astype(str),
            rownames=["Actual"], colnames=["Predicted"]
        )
        im = ax2.imshow(cm.values, cmap="Blues", interpolation="nearest")

        ax2.set_xticks(np.arange(len(cm.columns)))
        ax2.set_yticks(np.arange(len(cm.index)))
        ax2.set_xticklabels(cm.columns, rotation=15)
        ax2.set_yticklabels(cm.index)
        ax2.set_xlabel("Predicted Label")
        ax2.set_ylabel("Actual Label")
        ax2.set_title("Confusion Matrix", fontweight="bold")

        for i in range(len(cm.index)):
            for j in range(len(cm.columns)):
                ax2.text(
                    j, i, str(cm.values[i, j]), ha="center", va="center",
                    color="black" if cm.values[i, j] < cm.values.max() / 2 else "white"
                )

        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_signal_distribution(
        self,
        save_path: Path,
        records: list[BacktestRecord],
    ) -> Path:
        """
        Plot long/short/neutral signal breakdown and return distribution (Task 6.4.1 new plot).
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=150)

        if not records:
            ax1.text(0.5, 0.5, "No Data", ha="center", va="center")
            fig.savefig(save_path, bbox_inches="tight")
            plt.close(fig)
            return save_path

        # Signal counts
        signals = [r.predicted_direction or "neutral" for r in records]
        from collections import Counter
        sig_counts = Counter(signals)

        categories = ["positive (long)", "neutral", "negative (short)"]
        values = [
            sig_counts.get("positive", 0),
            sig_counts.get("neutral", 0),
            sig_counts.get("negative", 0),
        ]
        colors = ["#2ca02c", "#7f7f7f", "#d62728"]

        bars = ax1.bar(categories, values, color=colors, alpha=0.85)
        ax1.set_title("Signal Distribution\n(Long / Neutral / Short)", fontweight="bold")
        ax1.set_ylabel("Number of Observations")
        for bar, val in zip(bars, values):
            if val > 0:
                ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                         str(val), ha="center", va="bottom", fontsize=9)
        ax1.grid(True, linestyle=":", alpha=0.5, axis="y")

        # Return distribution for active trades
        active_returns = [
            (r.strategy_return or 0.0) * 100.0
            for r in records
            if abs(r.signal or 0.0) > 1e-6
        ]

        if active_returns:
            ax2.hist(active_returns, bins=min(20, len(active_returns)), color="#1f77b4",
                     alpha=0.75, edgecolor="white")
            ax2.axvline(np.mean(active_returns), color="red", linestyle="--", linewidth=1.5,
                        label=f"Mean: {np.mean(active_returns):.2f}%")
            ax2.axvline(0, color="black", linestyle="-", linewidth=0.8)
            ax2.legend(fontsize=9)
        else:
            ax2.text(0.5, 0.5, "No Active Trades", ha="center", va="center")

        ax2.set_title("Active Trade Return Distribution (%)", fontweight="bold")
        ax2.set_xlabel("Net Strategy Return (%)")
        ax2.set_ylabel("Frequency")
        ax2.grid(True, linestyle=":", alpha=0.5, axis="y")

        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_model_comparison(
        self,
        save_path: Path,
        model_comparison_data: Optional[dict[str, Any]] = None,
    ) -> Path:
        """Plot model comparison bar chart across algorithms."""
        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

        if not model_comparison_data:
            models = ["lgbm", "xgboost", "random_forest"]
            f1_scores = [0.0, 0.0, 0.0]
            ax.bar(models, f1_scores, color=["#1f77b4", "#ff7f0e", "#2ca02c"])
            ax.set_ylim(0, 1.0)
            ax.set_ylabel("Macro F1 Score")
            ax.set_title("Model Comparison Ranking (No Data)", fontweight="bold")
            fig.savefig(save_path, bbox_inches="tight")
            plt.close(fig)
            return save_path

        model_names = []
        f1_scores = []

        if "rankings" in model_comparison_data:
            for item in model_comparison_data["rankings"]:
                model_names.append(str(item.get("model_type", "unknown")))
                f1_scores.append(float(item.get("f1_macro", 0.0)))
        else:
            for target, data in model_comparison_data.items():
                if isinstance(data, dict) and "best_model" in data:
                    bm = data["best_model"]
                    model_names.append(f"{target} ({bm.get('model_type', '')})")
                    f1_scores.append(float(bm.get("f1_macro", 0.0)))

        if not model_names:
            model_names = ["lgbm", "xgboost", "random_forest"]
            f1_scores = [0.0, 0.0, 0.0]

        bar_colors = ["#1f77b4", "#ff7f0e", "#2ca02c"][: len(model_names)]
        if len(bar_colors) < len(model_names):
            bar_colors += ["#9467bd"] * (len(model_names) - len(bar_colors))

        ax.bar(model_names, f1_scores, color=bar_colors, alpha=0.85)
        ax.set_ylim(0, 1.0)
        ax.set_ylabel("Macro F1 Score", fontsize=10)
        ax.set_title("Model Algorithm Comparison (Macro F1)", fontsize=12, fontweight="bold")
        ax.grid(True, linestyle=":", alpha=0.5, axis="y")

        for i, v in enumerate(f1_scores):
            ax.text(i, v + 0.02, f"{v:.4f}", ha="center", fontsize=9)

        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _compound_series(rets: list[float]) -> np.ndarray:
        """Compound a list of returns to build cumulative wealth from 1.0."""
        result = np.ones(len(rets) + 1)
        for i, r in enumerate(rets):
            result[i + 1] = result[i] * (1.0 + (r if np.isfinite(r) else 0.0))
        return result[1:]  # drop the initial 1.0 seed
