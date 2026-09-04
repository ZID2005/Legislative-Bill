"""
backtesting/metrics.py
======================
Classification and financial metrics calculation for the Historical Backtesting Engine
(Task 6.4 / 6.4.1).

Task 6.4.1 Corrections
-----------------------
* ``ClassificationMetricsCalculator.compute_metrics()`` — adds majority-class baseline
  accuracy, per-class report, confusion matrix, and class distribution.
* ``FinancialMetricsCalculator.compute_metrics()`` — rewritten to use
  ``PortfolioAccountant`` snapshots for compounded returns, wealth-relative drawdown,
  and event-frequency Sharpe. Also reports Wilson CI for hit ratio, actual trade count
  vs total observations, and total TC paid.

Classes
-------
* ``ClassificationMetricsCalculator``
* ``FinancialMetricsCalculator``
"""

from __future__ import annotations

import math
import warnings
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)

from config.logging_config import get_logger
from schemas.backtest_record import (
    BacktestRecord,
    ClassificationMetrics,
    FinancialMetrics,
    PortfolioSnapshot,
)

logger = get_logger(__name__)

_NEUTRAL_THRESHOLD = 1e-6


class ClassificationMetricsCalculator:
    """
    Computes statistical classification performance metrics on backtest predictions.
    """

    def compute_metrics(
        self,
        y_true: list[Any] | np.ndarray | pd.Series,
        y_pred: list[Any] | np.ndarray | pd.Series,
        y_prob: Optional[list[dict[str, float]] | np.ndarray] = None,
    ) -> ClassificationMetrics:
        """
        Calculate full set of classification metrics including majority-class baseline.
        """
        y_true_str = np.array([str(x).strip() for x in y_true])
        y_pred_str = np.array([str(x).strip() for x in y_pred])

        if len(y_true_str) == 0:
            return ClassificationMetrics(
                accuracy=0.0,
                precision_macro=0.0,
                precision_weighted=0.0,
                recall_macro=0.0,
                recall_weighted=0.0,
                macro_f1=0.0,
                weighted_f1=0.0,
                balanced_accuracy=0.0,
                mcc=0.0,
                majority_class_baseline_accuracy=0.0,
                per_class_report=None,
                confusion_matrix=None,
                class_distribution=None,
            )

        # Majority-class baseline
        classes, counts = np.unique(y_true_str, return_counts=True)
        majority_class_acc = float(counts.max() / len(y_true_str))

        # Class distribution
        class_dist = {str(c): int(n) for c, n in zip(classes, counts)}

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            acc = float(accuracy_score(y_true_str, y_pred_str))
            prec_m = float(precision_score(y_true_str, y_pred_str, average="macro", zero_division=0))
            prec_w = float(precision_score(y_true_str, y_pred_str, average="weighted", zero_division=0))
            rec_m = float(recall_score(y_true_str, y_pred_str, average="macro", zero_division=0))
            rec_w = float(recall_score(y_true_str, y_pred_str, average="weighted", zero_division=0))
            f1_m = float(f1_score(y_true_str, y_pred_str, average="macro", zero_division=0))
            f1_w = float(f1_score(y_true_str, y_pred_str, average="weighted", zero_division=0))
            bal_acc = float(balanced_accuracy_score(y_true_str, y_pred_str))
            mcc_val = float(matthews_corrcoef(y_true_str, y_pred_str))

        # Per-class report
        per_class = self._compute_per_class_report(y_true_str, y_pred_str, classes)

        # Confusion matrix
        cm = self._build_confusion_matrix(y_true_str, y_pred_str, classes)

        # Probabilistic metrics
        roc_auc_val: Optional[float] = None
        brier_val: Optional[float] = None
        ece_val: Optional[float] = None

        if y_prob is not None and len(y_prob) == len(y_true_str):
            roc_auc_val, brier_val, ece_val = self._compute_probabilistic_metrics(
                y_true_str, y_pred_str, y_prob
            )

        return ClassificationMetrics(
            accuracy=acc,
            precision_macro=prec_m,
            precision_weighted=prec_w,
            recall_macro=rec_m,
            recall_weighted=rec_w,
            macro_f1=f1_m,
            weighted_f1=f1_w,
            balanced_accuracy=bal_acc,
            mcc=mcc_val,
            roc_auc=roc_auc_val,
            brier_score=brier_val,
            calibration_error=ece_val,
            majority_class_baseline_accuracy=majority_class_acc,
            per_class_report=per_class,
            confusion_matrix=cm,
            class_distribution=class_dist,
        )

    def _compute_per_class_report(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        classes: np.ndarray,
    ) -> dict[str, Any]:
        """Compute per-class precision, recall, F1, support."""
        report: dict[str, Any] = {}
        for cls in classes:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                tp = int(np.sum((y_true == cls) & (y_pred == cls)))
                fp = int(np.sum((y_true != cls) & (y_pred == cls)))
                fn = int(np.sum((y_true == cls) & (y_pred != cls)))
                support = int(np.sum(y_true == cls))
                prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
                rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
                f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
                report[str(cls)] = {
                    "precision": round(prec, 4),
                    "recall": round(rec, 4),
                    "f1": round(f1, 4),
                    "support": support,
                }
        return report

    def _build_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        classes: np.ndarray,
    ) -> list[list[int]]:
        """Build raw confusion matrix as list[list[int]]."""
        n = len(classes)
        cls_to_idx = {c: i for i, c in enumerate(classes)}
        matrix = [[0] * n for _ in range(n)]
        for yt, yp in zip(y_true, y_pred):
            i = cls_to_idx.get(yt, -1)
            j = cls_to_idx.get(yp, -1)
            if 0 <= i < n and 0 <= j < n:
                matrix[i][j] += 1
        return matrix

    def _compute_probabilistic_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_prob: Any,
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """Compute ROC-AUC, Brier score, and Expected Calibration Error (ECE)."""
        classes = sorted(np.unique(y_true))
        n_classes = len(classes)
        if n_classes < 2:
            return None, None, None

        if isinstance(y_prob, list) and len(y_prob) > 0 and isinstance(y_prob[0], dict):
            prob_matrix = np.zeros((len(y_true), n_classes))
            for i, p_dict in enumerate(y_prob):
                for j, cls in enumerate(classes):
                    prob_matrix[i, j] = p_dict.get(cls, 0.0)
        elif isinstance(y_prob, np.ndarray):
            prob_matrix = y_prob
        else:
            return None, None, None

        row_sums = prob_matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        prob_matrix = prob_matrix / row_sums

        roc_auc: Optional[float] = None
        brier: Optional[float] = None
        ece: Optional[float] = None

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            try:
                if n_classes == 2:
                    pos_cls = classes[1]
                    y_true_bin = (y_true == pos_cls).astype(int)
                    roc_auc = float(roc_auc_score(y_true_bin, prob_matrix[:, 1]))
                else:
                    roc_auc = float(roc_auc_score(y_true, prob_matrix, multi_class="ovr", average="macro"))
            except Exception:
                roc_auc = None

            try:
                if n_classes == 2:
                    pos_cls = classes[1]
                    y_true_bin = (y_true == pos_cls).astype(int)
                    brier = float(brier_score_loss(y_true_bin, prob_matrix[:, 1]))
                else:
                    one_hot = np.zeros_like(prob_matrix)
                    for i, cls in enumerate(classes):
                        one_hot[y_true == cls, i] = 1.0
                    brier = float(np.mean(np.sum((prob_matrix - one_hot) ** 2, axis=1)))
            except Exception:
                brier = None

            try:
                confidences = np.max(prob_matrix, axis=1)
                predictions = np.array([classes[idx] for idx in np.argmax(prob_matrix, axis=1)])
                accuracies = (predictions == y_true).astype(float)

                n_bins = 10
                bin_boundaries = np.linspace(0, 1, n_bins + 1)
                ece_sum = 0.0

                for i in range(n_bins):
                    in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
                    prop_in_bin = np.mean(in_bin)
                    if prop_in_bin > 0:
                        accuracy_in_bin = np.mean(accuracies[in_bin])
                        avg_confidence_in_bin = np.mean(confidences[in_bin])
                        ece_sum += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin

                ece = float(ece_sum)
            except Exception:
                ece = None

        return roc_auc, brier, ece


class FinancialMetricsCalculator:
    """
    Computes corrected quantitative financial metrics from PortfolioSnapshot series
    (Task 6.4.1).

    Key Corrections vs Task 6.4
    ----------------------------
    * Uses ``PortfolioSnapshot`` series — one entry per event date — NOT individual
      observation returns.
    * Cumulative return = compounded (final_wealth - 1.0), not additive sum.
    * Max drawdown is wealth-relative (portfolio_value / peak - 1 ≤ 0).
    * Sharpe is event-frequency (mean / std of per-date returns, no sqrt(252)).
    * Annualized Sharpe uses sqrt(252) but is flagged with disclaimer.
    * Hit ratio uses only actual trade dates (non-neutral signals).
    * Wilson 95% CI for hit ratio.
    """

    def compute_metrics(
        self,
        records: list[BacktestRecord],
        snapshots: list[PortfolioSnapshot],
    ) -> FinancialMetrics:
        """
        Compute financial strategy performance metrics.

        Parameters
        ----------
        records : list[BacktestRecord]
            All backtest records (post-evaluation).
        snapshots : list[PortfolioSnapshot]
            Chronological per-date portfolio snapshots from PortfolioAccountant.
        """
        if not records or not snapshots:
            return self._zero_metrics()

        initial_capital = 1.0

        # Final wealth from last snapshot
        final_wealth = float(snapshots[-1].portfolio_value) if snapshots else initial_capital
        cumulative_return = final_wealth - initial_capital

        # Per-date portfolio returns (event-frequency)
        date_rets = np.array([s.portfolio_return for s in snapshots], dtype=float)

        # Sharpe (event-frequency)
        std_dt = float(np.std(date_rets, ddof=1)) if len(date_rets) > 1 else 0.0
        mean_dt = float(np.mean(date_rets)) if len(date_rets) > 0 else 0.0
        sharpe = (mean_dt / std_dt) if std_dt > 1e-8 else 0.0

        # Annualized Sharpe (sqrt 252 with disclaimer)
        sharpe_ann: Optional[float] = float(sharpe * math.sqrt(252.0)) if std_dt > 1e-8 else None

        # Volatility (annualized std of per-date returns)
        volatility = float(std_dt * math.sqrt(252.0))

        # Wealth-relative max drawdown (≤ 0)
        max_dd = float(min(s.drawdown for s in snapshots)) if snapshots else 0.0

        # Signals
        total_obs = len(records)
        dirs = [r.predicted_direction or "neutral" for r in records]
        signals = [r.signal or 0.0 for r in records]

        long_count = sum(1 for s in signals if s > _NEUTRAL_THRESHOLD)
        short_count = sum(1 for s in signals if s < -_NEUTRAL_THRESHOLD)
        neutral_count = sum(1 for s in signals if abs(s) <= _NEUTRAL_THRESHOLD)
        actual_trades = long_count + short_count  # only active positions

        # Unique entities
        unique_companies = len({r.company_isin for r in records if abs(r.signal or 0.0) > _NEUTRAL_THRESHOLD})
        unique_bills = len({r.bill_id for r in records if abs(r.signal or 0.0) > _NEUTRAL_THRESHOLD})

        # Hit ratio on active trade dates only
        active_rets = [
            r.strategy_return or 0.0
            for r in records
            if abs(r.signal or 0.0) > _NEUTRAL_THRESHOLD
        ]
        if actual_trades > 0:
            wins = sum(1 for r in active_rets if r > 0)
            hit_ratio = wins / actual_trades
            ci_lower, ci_upper = self._wilson_ci(wins, actual_trades, z=1.96)
        else:
            hit_ratio = 0.0
            ci_lower = ci_upper = 0.0

        # Average return per trade (active only)
        avg_trade_ret = float(np.mean(active_rets)) if active_rets else 0.0

        # Long/short return breakdowns
        long_rets = [r.strategy_return or 0.0 for r in records if (r.signal or 0.0) > _NEUTRAL_THRESHOLD]
        short_rets = [r.strategy_return or 0.0 for r in records if (r.signal or 0.0) < -_NEUTRAL_THRESHOLD]
        long_avg = float(np.mean(long_rets)) if long_rets else 0.0
        short_avg = float(np.mean(short_rets)) if short_rets else 0.0

        # Total TC paid (summed across all snapshots)
        total_tc = sum(s.total_tc_paid for s in snapshots)
        tc_per_trade = total_tc / actual_trades if actual_trades > 0 else 0.0

        return FinancialMetrics(
            initial_capital=initial_capital,
            final_wealth=final_wealth,
            cumulative_return=cumulative_return,
            average_return_per_trade=avg_trade_ret,
            hit_ratio=hit_ratio,
            hit_ratio_ci_lower=ci_lower,
            hit_ratio_ci_upper=ci_upper,
            max_drawdown=max_dd,
            volatility=volatility,
            sharpe_ratio=sharpe,
            sharpe_ratio_annualized=sharpe_ann,
            total_observations=total_obs,
            actual_trades=actual_trades,
            long_signals=long_count,
            short_signals=short_count,
            neutral_signals=neutral_count,
            unique_companies_traded=unique_companies,
            unique_bills_traded=unique_bills,
            long_avg_return=long_avg,
            short_avg_return=short_avg,
            total_tc_paid=total_tc,
            tc_per_trade=tc_per_trade,
            # backward compat
            average_return_per_signal=avg_trade_ret,
            positive_signal_avg_return=long_avg,
            negative_signal_avg_return=short_avg,
            neutral_signal_avg_return=0.0,
        )

    @staticmethod
    def _wilson_ci(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
        """Wilson score confidence interval for binomial proportion."""
        if n == 0:
            return 0.0, 0.0
        p = wins / n
        denominator = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denominator
        margin = z * math.sqrt((p * (1 - p) / n) + z**2 / (4 * n**2)) / denominator
        return max(0.0, float(centre - margin)), min(1.0, float(centre + margin))

    def _zero_metrics(self) -> FinancialMetrics:
        return FinancialMetrics(
            initial_capital=1.0,
            final_wealth=1.0,
            cumulative_return=0.0,
            average_return_per_trade=0.0,
            hit_ratio=0.0,
            hit_ratio_ci_lower=0.0,
            hit_ratio_ci_upper=0.0,
            max_drawdown=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            sharpe_ratio_annualized=None,
            total_observations=0,
            actual_trades=0,
            long_signals=0,
            short_signals=0,
            neutral_signals=0,
            unique_companies_traded=0,
            unique_bills_traded=0,
            long_avg_return=0.0,
            short_avg_return=0.0,
            total_tc_paid=0.0,
            tc_per_trade=0.0,
        )
