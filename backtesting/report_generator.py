"""
backtesting/report_generator.py
================================
Report assembly and file generator for the Historical Backtesting Engine
(Task 6.4 / 6.4.1).

Task 6.4.1 Updates
-------------------
* ``build_backtest_report()`` — updated to include corrected financial metrics,
  academic limitations, and Task 6.4.1 validation summary.
* ``build_overlap_report()`` — new; wraps OverlapReport.to_dict().
* ``build_financial_validation_report()`` — new; wraps FinancialValidationReport.to_dict().
* ``build_benchmark_metrics_report()`` — new; standalone BenchmarkComparison serialiser.
* ``build_portfolio_timeseries_df()`` — new; converts PortfolioSnapshot list to DataFrame.
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd

from config.logging_config import get_logger
from schemas.backtest_record import (
    BacktestRecord,
    BacktestRunDescriptor,
    ClassificationMetrics,
    FinancialValidationReport,
    LeakageReport,
    OverlapReport,
    PortfolioSnapshot,
    StrategyMetrics,
)

logger = get_logger(__name__)

ACADEMIC_DISTINCTION_NOTE = (
    "IMPORTANT ACADEMIC DISTINCTION: Predictive classification performance "
    "(e.g., Macro F1, Accuracy) is strictly distinguished from historical "
    "financial strategy performance (e.g., Cumulative Return, Sharpe Ratio). "
    "High classification accuracy does NOT automatically equate to investment "
    "profitability due to transaction costs, market noise, and asymmetric return distributions."
)

ANTICIPATION_PARADOX_NOTE = (
    "ANTICIPATION PARADOX ARCHITECTURE: Primary backtest evaluated at official "
    "bill introduction dates. Anticipation-aware features (Google Trends / GDELT) "
    "are currently recorded as unavailable. Prediction timestamp offsets support "
    "future media features without architectural redesign."
)

ACADEMIC_LIMITATIONS_NOTE = (
    "ACADEMIC LIMITATIONS (Task 6.4.1): "
    "(1) Class imbalance — majority-class baseline accuracy is reported. "
    "(2) Small sample — few unique event dates; all financial metrics should be "
    "interpreted with extreme caution. "
    "(3) Overlapping events — multiple simultaneous events are aggregated per date; "
    "they are NOT independent sequential trades. "
    "(4) Sharpe annualization — sqrt(252) scaling is applied with a disclaimer; "
    "with few event dates per year this may overstate statistical significance. "
    "(5) No claim of profitability is made unless supported by statistically "
    "and economically significant evidence."
)

RETURN_ACCOUNTING_NOTE = (
    "RETURN ACCOUNTING (Task 6.4.1): Returns are compounded simple returns "
    "from initial_capital=1.0. Simultaneous events on the same date are "
    "equal-weighted into one portfolio return. Transaction costs are charged "
    "only on non-neutral (active) positions."
)


class BacktestReportGenerator:
    """
    Assembles structured report dictionaries and DataFrames for backtest output files.
    """

    def build_backtest_report(
        self,
        descriptor: BacktestRunDescriptor,
        classification_metrics: ClassificationMetrics,
        strategy_metrics: StrategyMetrics,
        leakage_report: LeakageReport,
        overlap_report: Optional[OverlapReport] = None,
        financial_validation: Optional[FinancialValidationReport] = None,
    ) -> dict[str, Any]:
        """Build main ``backtest_report.json`` structure."""
        report: dict[str, Any] = {
            "run_id": descriptor.run_id,
            "run_timestamp": descriptor.run_timestamp,
            "target": descriptor.target,
            "model_name": descriptor.model_name,
            "task_version": "6.4.1",
            "date_range": {
                "start_date": descriptor.start_date,
                "end_date": descriptor.end_date,
            },
            "summary_counts": {
                "total_observations": descriptor.total_predictions,
                "unique_bills": descriptor.unique_bills,
                "unique_companies": descriptor.unique_companies,
            },
            "predictive_performance": classification_metrics.to_dict(),
            "financial_performance": strategy_metrics.to_dict(),
            "look_ahead_leakage_audit": leakage_report.to_dict(),
            "academic_distinction_note": ACADEMIC_DISTINCTION_NOTE,
            "anticipation_paradox_note": ANTICIPATION_PARADOX_NOTE,
            "academic_limitations_note": ACADEMIC_LIMITATIONS_NOTE,
            "return_accounting_note": RETURN_ACCOUNTING_NOTE,
        }

        if overlap_report is not None:
            report["event_overlap_summary"] = {
                "total_events": overlap_report.total_events,
                "dates_with_multiple_events": overlap_report.dates_with_multiple_events,
                "max_simultaneous_events": overlap_report.max_simultaneous_events,
                "overlap_percentage": overlap_report.overlap_percentage,
                "interpretation": overlap_report.to_dict().get("interpretation", ""),
            }

        if financial_validation is not None:
            report["financial_validation_summary"] = {
                "is_valid": financial_validation.is_valid,
                "passed_checks": financial_validation.passed_checks,
                "failed_checks": financial_validation.failed_checks,
                "violations": financial_validation.violations,
            }

        return report

    def build_model_comparison(
        self,
        results_by_model: dict[str, ClassificationMetrics],
        primary_metric: str = "macro_f1",
    ) -> dict[str, Any]:
        """Build ``model_comparison.json`` ranking algorithms per metric."""
        rankings = []
        sorted_models = sorted(
            results_by_model.items(),
            key=lambda item: getattr(item[1], primary_metric, 0.0),
            reverse=True,
        )

        for rank, (m_name, metrics) in enumerate(sorted_models, start=1):
            entry: dict[str, Any] = {
                "rank": rank,
                "model_type": m_name,
                "accuracy": round(metrics.accuracy, 4),
                "f1_macro": round(metrics.macro_f1, 4),
                "precision_macro": round(metrics.precision_macro, 4),
                "recall_macro": round(metrics.recall_macro, 4),
                "mcc": round(metrics.mcc, 4),
            }
            if metrics.majority_class_baseline_accuracy is not None:
                entry["majority_class_baseline_accuracy"] = round(
                    metrics.majority_class_baseline_accuracy, 4
                )
            rankings.append(entry)

        best_model = rankings[0] if rankings else {}
        worst_model = rankings[-1] if rankings else {}

        return {
            "primary_selection_metric": primary_metric,
            "best_model": best_model,
            "worst_model": worst_model,
            "rankings": rankings,
            "academic_distinction_note": ACADEMIC_DISTINCTION_NOTE,
        }

    def build_strategy_metrics_report(
        self, strategy_metrics: StrategyMetrics
    ) -> dict[str, Any]:
        """Build ``strategy_metrics.json`` structure."""
        return {
            **strategy_metrics.to_dict(),
            "academic_distinction_note": ACADEMIC_DISTINCTION_NOTE,
            "return_accounting_note": RETURN_ACCOUNTING_NOTE,
        }

    def build_prediction_results_df(self, records: list[BacktestRecord]) -> pd.DataFrame:
        """Convert list of BacktestRecord objects to pandas DataFrame for Parquet save."""
        if not records:
            return pd.DataFrame()
        return pd.DataFrame([r.to_dict() for r in records])

    def build_overlap_report(self, overlap_report: OverlapReport) -> dict[str, Any]:
        """Build ``overlap_report.json`` structure."""
        return overlap_report.to_dict()

    def build_financial_validation_report(
        self, validation: FinancialValidationReport
    ) -> dict[str, Any]:
        """Build ``financial_validation_report.json`` structure."""
        return validation.to_dict()

    def build_benchmark_metrics_report(
        self, strategy_metrics: StrategyMetrics
    ) -> dict[str, Any]:
        """Build standalone ``benchmark_metrics.json`` from BenchmarkComparison."""
        return {
            "target": strategy_metrics.target,
            "model_name": strategy_metrics.model_name,
            "benchmark_comparison": strategy_metrics.benchmark_comparison.to_dict(),
            "return_accounting_note": RETURN_ACCOUNTING_NOTE,
        }

    def build_portfolio_timeseries_df(
        self, snapshots: list[PortfolioSnapshot]
    ) -> pd.DataFrame:
        """Convert PortfolioSnapshot list to DataFrame for ``portfolio_timeseries.parquet``."""
        if not snapshots:
            return pd.DataFrame()
        return pd.DataFrame([s.to_dict() for s in snapshots])
