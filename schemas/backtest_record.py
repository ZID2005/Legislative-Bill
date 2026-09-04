"""
schemas/backtest_record.py
===========================
Typed data models for the Historical Backtesting Engine (Task 6.4 / 6.4.1).

Task 6.4.1 Additions
--------------------
* ``PortfolioSnapshot`` — per-date portfolio wealth, return, and drawdown.
* Extended ``FinancialMetrics`` — initial_capital, final_wealth, actual_trades,
  hit_ratio CI, annualized excess return, majority-class baseline.
* ``OverlapReport`` — event-window overlap audit.
* ``FinancialValidationReport`` — financial data integrity checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class BacktestRecord:
    """
    Historical prediction and financial evaluation record for one observation.

    Attributes
    ----------
    bill_id : str
    company_isin : str
    event_window : str
    prediction_timestamp : str
    model_name : str
    target : str
    predicted_class : str
    actual_class : str
    prediction_probability : dict[str, float]
    model_version : str
    feature_version : str
    training_cutoff_date : str
    data_cutoff_date : str
    predicted_direction : Optional[str]
    actual_direction : Optional[str]
    abnormal_return : Optional[float]
        Event-window abnormal return (CAR from research dataset).
    cumulative_abnormal_return : Optional[float]
        Alias for abnormal_return (CAR over the full event window).
    prediction_correctness : Optional[bool]
    market_moving_correctness : Optional[bool]
    strategy_return : Optional[float]
        Net position return after transaction costs for this signal.
        = 0.0 for neutral signals.
    signal : Optional[float]
        Raw signal value: +1.0 Long, -1.0 Short, 0.0 Neutral.
    nifty_period_return : Optional[float]
        NIFTY 50 return over the same event window period.
    """

    bill_id: str
    company_isin: str
    event_window: str
    prediction_timestamp: str
    model_name: str
    target: str
    predicted_class: str
    actual_class: str
    prediction_probability: dict[str, float] = field(default_factory=dict)
    model_version: str = "v1.0.0"
    feature_version: str = "v1.0.0"
    training_cutoff_date: str = ""
    data_cutoff_date: str = ""
    predicted_direction: Optional[str] = None
    actual_direction: Optional[str] = None
    abnormal_return: Optional[float] = None
    cumulative_abnormal_return: Optional[float] = None
    prediction_correctness: Optional[bool] = None
    market_moving_correctness: Optional[bool] = None
    strategy_return: Optional[float] = None
    signal: Optional[float] = None
    nifty_period_return: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise the record to a dictionary."""
        return {
            "bill_id": self.bill_id,
            "company_isin": self.company_isin,
            "event_window": self.event_window,
            "prediction_timestamp": self.prediction_timestamp,
            "model_name": self.model_name,
            "target": self.target,
            "predicted_class": str(self.predicted_class),
            "actual_class": str(self.actual_class),
            "prediction_probability": self.prediction_probability,
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "training_cutoff_date": self.training_cutoff_date,
            "data_cutoff_date": self.data_cutoff_date,
            "predicted_direction": self.predicted_direction,
            "actual_direction": self.actual_direction,
            "abnormal_return": self.abnormal_return,
            "cumulative_abnormal_return": self.cumulative_abnormal_return,
            "prediction_correctness": self.prediction_correctness,
            "market_moving_correctness": self.market_moving_correctness,
            "strategy_return": self.strategy_return,
            "signal": self.signal,
            "nifty_period_return": self.nifty_period_return,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BacktestRecord:
        """Deserialise from a dictionary."""
        return cls(
            bill_id=data["bill_id"],
            company_isin=data["company_isin"],
            event_window=data["event_window"],
            prediction_timestamp=data["prediction_timestamp"],
            model_name=data["model_name"],
            target=data["target"],
            predicted_class=str(data["predicted_class"]),
            actual_class=str(data["actual_class"]),
            prediction_probability=data.get("prediction_probability", {}),
            model_version=data.get("model_version", "v1.0.0"),
            feature_version=data.get("feature_version", "v1.0.0"),
            training_cutoff_date=data.get("training_cutoff_date", ""),
            data_cutoff_date=data.get("data_cutoff_date", ""),
            predicted_direction=data.get("predicted_direction"),
            actual_direction=data.get("actual_direction"),
            abnormal_return=data.get("abnormal_return"),
            cumulative_abnormal_return=data.get("cumulative_abnormal_return"),
            prediction_correctness=data.get("prediction_correctness"),
            market_moving_correctness=data.get("market_moving_correctness"),
            strategy_return=data.get("strategy_return"),
            signal=data.get("signal"),
            nifty_period_return=data.get("nifty_period_return"),
        )


@dataclass
class PortfolioSnapshot:
    """
    Per-event-date portfolio state snapshot (Task 6.4.1).

    Attributes
    ----------
    date : str
        Event date (ISO string).
    n_active_positions : int
        Number of non-neutral signals on this date.
    n_observations : int
        Total observations on this date.
    equal_weight_return : float
        Equal-weighted average raw CAR across active positions on this date.
    portfolio_return : float
        Net portfolio return (after transaction costs) for this date.
        = 0.0 if no active positions.
    portfolio_value : float
        Compounded portfolio wealth from initial_capital=1.0 up to this date.
    running_peak : float
        Maximum portfolio_value observed up to and including this date.
    drawdown : float
        Wealth-relative drawdown: portfolio_value / running_peak - 1 (≤ 0).
    nifty_return : float
        NIFTY 50 return for the event window of this date.
    bah_return : float
        Equal-weighted buy-and-hold return for this date's active companies.
    total_tc_paid : float
        Total transaction cost paid on this date.
    """

    date: str
    n_active_positions: int
    n_observations: int
    equal_weight_return: float
    portfolio_return: float
    portfolio_value: float
    running_peak: float
    drawdown: float
    nifty_return: float = 0.0
    bah_return: float = 0.0
    total_tc_paid: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date,
            "n_active_positions": self.n_active_positions,
            "n_observations": self.n_observations,
            "equal_weight_return": round(self.equal_weight_return, 6),
            "portfolio_return": round(self.portfolio_return, 6),
            "portfolio_value": round(self.portfolio_value, 6),
            "running_peak": round(self.running_peak, 6),
            "drawdown": round(self.drawdown, 6),
            "nifty_return": round(self.nifty_return, 6),
            "bah_return": round(self.bah_return, 6),
            "total_tc_paid": round(self.total_tc_paid, 6),
        }


@dataclass
class ClassificationMetrics:
    """Statistical classification evaluation metrics (Task 6.4 / 6.4.1)."""

    accuracy: float
    precision_macro: float
    precision_weighted: float
    recall_macro: float
    recall_weighted: float
    macro_f1: float
    weighted_f1: float
    balanced_accuracy: float
    mcc: float
    roc_auc: Optional[float] = None
    brier_score: Optional[float] = None
    calibration_error: Optional[float] = None
    # Task 6.4.1 additions
    majority_class_baseline_accuracy: Optional[float] = None
    per_class_report: Optional[dict[str, Any]] = None
    confusion_matrix: Optional[list[list[int]]] = None
    class_distribution: Optional[dict[str, int]] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision_macro": round(self.precision_macro, 4),
            "precision_weighted": round(self.precision_weighted, 4),
            "recall_macro": round(self.recall_macro, 4),
            "recall_weighted": round(self.recall_weighted, 4),
            "macro_f1": round(self.macro_f1, 4),
            "weighted_f1": round(self.weighted_f1, 4),
            "balanced_accuracy": round(self.balanced_accuracy, 4),
            "mcc": round(self.mcc, 4),
            "roc_auc": round(self.roc_auc, 4) if self.roc_auc is not None else None,
            "brier_score": round(self.brier_score, 4) if self.brier_score is not None else None,
            "calibration_error": round(self.calibration_error, 4) if self.calibration_error is not None else None,
            "majority_class_baseline_accuracy": (
                round(self.majority_class_baseline_accuracy, 4)
                if self.majority_class_baseline_accuracy is not None else None
            ),
            "per_class_report": self.per_class_report,
            "confusion_matrix": self.confusion_matrix,
            "class_distribution": self.class_distribution,
        }


@dataclass
class FinancialMetrics:
    """
    Strategy performance and financial return metrics (Task 6.4.1 — corrected).

    Return Convention
    -----------------
    All returns are compounded simple returns from initial_capital = 1.0.
    cumulative_return = final_wealth - 1.0
    Drawdown is wealth-relative: drawdown = portfolio_value / peak - 1 (always ≤ 0).
    Sharpe ratio uses per-event-date portfolio returns (not individual observation returns).
    """

    # Portfolio
    initial_capital: float
    final_wealth: float
    cumulative_return: float          # = final_wealth - 1.0
    average_return_per_trade: float   # mean over active-trade dates only
    # Hit ratio
    hit_ratio: float
    hit_ratio_ci_lower: float         # Wilson 95% CI lower
    hit_ratio_ci_upper: float         # Wilson 95% CI upper
    # Risk
    max_drawdown: float               # ≤ 0 always
    volatility: float                 # annualized std of per-date portfolio returns
    sharpe_ratio: float               # per-date Sharpe (event-frequency)
    sharpe_ratio_annualized: Optional[float]  # sqrt(252) scaled with disclaimer
    # Signal counts
    total_observations: int
    actual_trades: int                # non-neutral signals
    long_signals: int
    short_signals: int
    neutral_signals: int
    unique_companies_traded: int
    unique_bills_traded: int
    # Signal return breakdowns
    long_avg_return: float
    short_avg_return: float
    # Transaction costs
    total_tc_paid: float
    tc_per_trade: float
    # Legacy fields kept for backward compatibility
    average_return_per_signal: float = 0.0
    positive_signal_avg_return: float = 0.0
    negative_signal_avg_return: float = 0.0
    neutral_signal_avg_return: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "return_convention": "compounded_simple_return",
            "initial_capital": self.initial_capital,
            "final_wealth": round(self.final_wealth, 6),
            "cumulative_return": round(self.cumulative_return, 6),
            "cumulative_return_pct": round(self.cumulative_return * 100, 4),
            "average_return_per_trade": round(self.average_return_per_trade, 6),
            "hit_ratio": round(self.hit_ratio, 4),
            "hit_ratio_ci_lower": round(self.hit_ratio_ci_lower, 4),
            "hit_ratio_ci_upper": round(self.hit_ratio_ci_upper, 4),
            "max_drawdown": round(self.max_drawdown, 6),
            "max_drawdown_pct": round(self.max_drawdown * 100, 4),
            "volatility": round(self.volatility, 6),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "sharpe_ratio_annualized": (
                round(self.sharpe_ratio_annualized, 4)
                if self.sharpe_ratio_annualized is not None else None
            ),
            "sharpe_disclaimer": (
                "Annualized Sharpe uses sqrt(252) scaling. "
                "With few event dates this may overstate significance."
            ),
            "total_observations": self.total_observations,
            "actual_trades": self.actual_trades,
            "long_signals": self.long_signals,
            "short_signals": self.short_signals,
            "neutral_signals": self.neutral_signals,
            "unique_companies_traded": self.unique_companies_traded,
            "unique_bills_traded": self.unique_bills_traded,
            "long_avg_return": round(self.long_avg_return, 6),
            "short_avg_return": round(self.short_avg_return, 6),
            "total_tc_paid": round(self.total_tc_paid, 6),
            "tc_per_trade": round(self.tc_per_trade, 6),
            # backward compat
            "average_return_per_signal": round(self.average_return_per_signal, 6),
            "positive_signal_avg_return": round(self.positive_signal_avg_return, 6),
            "negative_signal_avg_return": round(self.negative_signal_avg_return, 6),
            "neutral_signal_avg_return": round(self.neutral_signal_avg_return, 6),
        }


@dataclass
class BenchmarkComparison:
    """
    Comparison of strategy performance against market benchmarks (Task 6.4.1 — corrected).

    Return Convention
    -----------------
    All returns are compounded simple returns from initial_capital = 1.0.
    Excess return = strategy_final_wealth - benchmark_final_wealth.
    """

    # Strategy
    strategy_initial_capital: float
    strategy_final_wealth: float
    strategy_cumulative_return: float
    strategy_sharpe: float
    strategy_max_drawdown: float
    strategy_volatility: float
    # Buy-and-Hold
    buy_and_hold_final_wealth: float
    buy_and_hold_cumulative_return: float
    buy_and_hold_sharpe: float
    buy_and_hold_max_drawdown: float
    buy_and_hold_volatility: float
    # NIFTY 50
    nifty50_final_wealth: float
    nifty50_cumulative_return: float
    nifty50_sharpe: float
    nifty50_max_drawdown: float
    nifty50_volatility: float
    nifty50_data_source: str
    # Excess returns
    excess_return_over_buy_and_hold: float
    excess_return_over_nifty50: float
    annualized_excess_return_over_nifty50: Optional[float] = None
    # Period
    period_start_date: Optional[str] = None
    period_end_date: Optional[str] = None
    calendar_days: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "return_convention": "compounded_simple_return_from_initial_capital_1.0",
            "strategy": {
                "initial_capital": self.strategy_initial_capital,
                "final_wealth": round(self.strategy_final_wealth, 6),
                "cumulative_return": round(self.strategy_cumulative_return, 6),
                "cumulative_return_pct": round(self.strategy_cumulative_return * 100, 4),
                "sharpe": round(self.strategy_sharpe, 4),
                "max_drawdown": round(self.strategy_max_drawdown, 6),
                "volatility": round(self.strategy_volatility, 6),
            },
            "buy_and_hold": {
                "final_wealth": round(self.buy_and_hold_final_wealth, 6),
                "cumulative_return": round(self.buy_and_hold_cumulative_return, 6),
                "cumulative_return_pct": round(self.buy_and_hold_cumulative_return * 100, 4),
                "sharpe": round(self.buy_and_hold_sharpe, 4),
                "max_drawdown": round(self.buy_and_hold_max_drawdown, 6),
                "volatility": round(self.buy_and_hold_volatility, 6),
            },
            "nifty50": {
                "final_wealth": round(self.nifty50_final_wealth, 6),
                "cumulative_return": round(self.nifty50_cumulative_return, 6),
                "cumulative_return_pct": round(self.nifty50_cumulative_return * 100, 4),
                "sharpe": round(self.nifty50_sharpe, 4),
                "max_drawdown": round(self.nifty50_max_drawdown, 6),
                "volatility": round(self.nifty50_volatility, 6),
                "data_source": self.nifty50_data_source,
            },
            "excess_returns": {
                "vs_buy_and_hold": round(self.excess_return_over_buy_and_hold, 6),
                "vs_nifty50": round(self.excess_return_over_nifty50, 6),
                "annualized_vs_nifty50": (
                    round(self.annualized_excess_return_over_nifty50, 6)
                    if self.annualized_excess_return_over_nifty50 is not None else None
                ),
            },
            "period": {
                "start_date": self.period_start_date,
                "end_date": self.period_end_date,
                "calendar_days": self.calendar_days,
            },
        }


@dataclass
class StrategyMetrics:
    """Container for strategy metrics and benchmark comparison."""

    target: str
    model_name: str
    financial_metrics: FinancialMetrics
    benchmark_comparison: BenchmarkComparison
    transaction_cost_bps: float
    slippage_bps: float
    brokerage_bps: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "model_name": self.model_name,
            "financial_metrics": self.financial_metrics.to_dict(),
            "benchmark_comparison": self.benchmark_comparison.to_dict(),
            "transaction_cost_bps": self.transaction_cost_bps,
            "slippage_bps": self.slippage_bps,
            "brokerage_bps": self.brokerage_bps,
        }


@dataclass
class OverlapReport:
    """
    Event-window overlap audit report (Task 6.4.1).

    Purpose
    -------
    Detects when multiple events are simultaneously active so that
    the backtester can correctly avoid treating them as independent sequential trades.
    """

    total_events: int
    total_unique_dates: int
    overlapping_event_pairs: int
    overlap_percentage: float
    max_simultaneous_events: int
    dates_with_multiple_events: int
    company_level_overlaps: int
    bill_level_overlaps: int
    event_windows_checked: list[str]
    overlap_details: list[dict[str, Any]] = field(default_factory=list)
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_events": self.total_events,
            "total_unique_dates": self.total_unique_dates,
            "overlapping_event_pairs": self.overlapping_event_pairs,
            "overlap_percentage": round(self.overlap_percentage, 2),
            "max_simultaneous_events": self.max_simultaneous_events,
            "dates_with_multiple_events": self.dates_with_multiple_events,
            "company_level_overlaps": self.company_level_overlaps,
            "bill_level_overlaps": self.bill_level_overlaps,
            "event_windows_checked": self.event_windows_checked,
            "overlap_details": self.overlap_details[:50],  # cap detail rows
            "checked_at": self.checked_at,
            "interpretation": (
                "Multiple simultaneous events are aggregated into one equal-weighted "
                "portfolio return per date. They are NOT treated as independent sequential trades."
            ),
        }


@dataclass
class FinancialValidationReport:
    """
    Financial data integrity checks (Task 6.4.1).
    """

    total_checks: int
    passed_checks: int
    failed_checks: int
    is_valid: bool
    violations: list[str] = field(default_factory=list)
    # Specific checks
    has_negative_wealth: bool = False
    has_nan_returns: bool = False
    has_inf_returns: bool = False
    has_return_below_minus_100_pct: bool = False
    has_chronological_violation: bool = False
    has_duplicate_timestamps: bool = False
    has_invalid_drawdown: bool = False
    has_benchmark_date_misalign: bool = False
    max_drawdown_check: bool = True   # True means passed
    portfolio_wealth_check: bool = True
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "violations": self.violations,
            "checks": {
                "no_negative_wealth": not self.has_negative_wealth,
                "no_nan_returns": not self.has_nan_returns,
                "no_inf_returns": not self.has_inf_returns,
                "no_return_below_minus_100_pct": not self.has_return_below_minus_100_pct,
                "chronological_ordering": not self.has_chronological_violation,
                "no_duplicate_timestamps": not self.has_duplicate_timestamps,
                "valid_drawdown": not self.has_invalid_drawdown,
                "benchmark_date_aligned": not self.has_benchmark_date_misalign,
                "max_drawdown_lte_zero": self.max_drawdown_check,
                "portfolio_wealth_nonnegative": self.portfolio_wealth_check,
            },
            "checked_at": self.checked_at,
        }


@dataclass
class LeakageReport:
    """Audit log for look-ahead bias and temporal leakage verification."""

    has_leakage: bool
    total_records_checked: int
    training_cutoff_violations: int
    post_event_feature_violations: int
    future_dated_prediction_violations: int
    duplicate_prediction_violations: int
    violations_summary: list[str] = field(default_factory=list)
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_leakage": self.has_leakage,
            "total_records_checked": self.total_records_checked,
            "training_cutoff_violations": self.training_cutoff_violations,
            "post_event_feature_violations": self.post_event_feature_violations,
            "future_dated_prediction_violations": self.future_dated_prediction_violations,
            "duplicate_prediction_violations": self.duplicate_prediction_violations,
            "violations_summary": self.violations_summary,
            "checked_at": self.checked_at,
        }


@dataclass
class BacktestRunDescriptor:
    """Summary metadata descriptor for a backtest run."""

    run_id: str
    run_timestamp: str
    target: str
    model_name: str
    start_date: Optional[str]
    end_date: Optional[str]
    total_predictions: int
    unique_bills: int
    unique_companies: int
    anticipation_window: str
    transaction_cost: float
    brokerage: float
    slippage: float
    macro_f1: float
    accuracy: float
    cumulative_strategy_return: float
    sharpe_ratio: float
    max_drawdown: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "run_timestamp": self.run_timestamp,
            "target": self.target,
            "model_name": self.model_name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_predictions": self.total_predictions,
            "unique_bills": self.unique_bills,
            "unique_companies": self.unique_companies,
            "anticipation_window": self.anticipation_window,
            "transaction_cost": self.transaction_cost,
            "brokerage": self.brokerage,
            "slippage": self.slippage,
            "macro_f1": self.macro_f1,
            "accuracy": self.accuracy,
            "cumulative_strategy_return": self.cumulative_strategy_return,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown": self.max_drawdown,
        }
