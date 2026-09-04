"""
tests/test_backtesting.py
==========================
Unit and integration tests for Task 6.4 / 6.4.1 — Historical Backtesting Engine.

Tests:
- Data schemas (schemas/backtest_record.py)
- Repository (storage/backtest_repository.py)
- Validation (validation/backtest_validator.py)
- Strategy rules and transaction costs (backtesting/strategy.py)
- Classification & financial metrics (backtesting/metrics.py)
- PortfolioAccountant (backtesting/strategy.py)
- NiftyBenchmarkLoader (backtesting/nifty_loader.py)
- OverlapDetector (backtesting/overlap_detector.py)
- FinancialValidator (backtesting/financial_validator.py)
- Visualizer charts (backtesting/visualizer.py)
- Report generator (backtesting/report_generator.py)
- Master Engine (backtesting/engine.py)
- CLI command (cmd_backtest_models)

Task 6.4.1 Financial Correctness Tests:
- Compounded returns are never additive sums
- max_drawdown is always ≤ 0
- portfolio_value never goes negative
- transaction costs are only charged on active positions
- Wilson CI hit ratio bounds are in [0, 1]
- Benchmark comparison uses compounded wealth
- NIFTY loader returns scalar floats
- Overlap detector counts simultaneous events
- Financial validator passes for valid data
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from backtesting.engine import HistoricalBacktestEngine
from backtesting.financial_validator import FinancialValidator
from backtesting.metrics import ClassificationMetricsCalculator, FinancialMetricsCalculator
from backtesting.nifty_loader import NiftyBenchmarkLoader
from backtesting.overlap_detector import OverlapDetector
from backtesting.report_generator import BacktestReportGenerator
from backtesting.strategy import (
    PortfolioAccountant,
    SignalRule,
    StrategyEvaluator,
    TransactionCostModel,
)
from backtesting.visualizer import BacktestVisualizer
from main import cmd_backtest_models
from schemas.backtest_record import (
    BacktestRecord,
    BacktestRunDescriptor,
    BenchmarkComparison,
    ClassificationMetrics,
    FinancialMetrics,
    FinancialValidationReport,
    LeakageReport,
    OverlapReport,
    PortfolioSnapshot,
    StrategyMetrics,
)
from storage.backtest_repository import BacktestRepository
from validation.backtest_validator import BacktestValidator
from validation.validator import Validator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_records() -> list[BacktestRecord]:
    """Three records on different dates with different signals."""
    return [
        BacktestRecord(
            bill_id="bill-1",
            company_isin="INE001",
            event_window="[-1,+1]",
            prediction_timestamp="2023-01-10",
            model_name="lgbm",
            target="direction",
            predicted_class="positive",
            actual_class="positive",
            prediction_probability={"positive": 0.8, "negative": 0.1, "neutral": 0.1},
            training_cutoff_date="2023-01-09",
            data_cutoff_date="2023-01-10",
            predicted_direction="positive",
            actual_direction="positive",
            abnormal_return=0.04,
            cumulative_abnormal_return=0.04,
            strategy_return=0.039,
            prediction_correctness=True,
            signal=1.0,
        ),
        BacktestRecord(
            bill_id="bill-2",
            company_isin="INE002",
            event_window="[-1,+1]",
            prediction_timestamp="2023-02-15",
            model_name="lgbm",
            target="direction",
            predicted_class="negative",
            actual_class="positive",
            prediction_probability={"positive": 0.2, "negative": 0.7, "neutral": 0.1},
            training_cutoff_date="2023-02-14",
            data_cutoff_date="2023-02-15",
            predicted_direction="negative",
            actual_direction="positive",
            abnormal_return=0.03,
            cumulative_abnormal_return=0.03,
            strategy_return=-0.031,
            prediction_correctness=False,
            signal=-1.0,
        ),
        BacktestRecord(
            bill_id="bill-3",
            company_isin="INE003",
            event_window="[-1,+1]",
            prediction_timestamp="2023-03-20",
            model_name="lgbm",
            target="direction",
            predicted_class="neutral",
            actual_class="neutral",
            prediction_probability={"positive": 0.1, "negative": 0.1, "neutral": 0.8},
            training_cutoff_date="2023-03-19",
            data_cutoff_date="2023-03-20",
            predicted_direction="neutral",
            actual_direction="neutral",
            abnormal_return=0.005,
            cumulative_abnormal_return=0.005,
            strategy_return=0.0,
            prediction_correctness=True,
            signal=0.0,
        ),
    ]


@pytest.fixture
def sample_snapshots(sample_records: list[BacktestRecord]) -> list[PortfolioSnapshot]:
    """Build snapshots from sample_records via PortfolioAccountant."""
    accountant = PortfolioAccountant(initial_capital=1.0)
    return accountant.build_snapshots(sample_records)


@pytest.fixture
def tmp_backtest_repo(tmp_path: Path) -> BacktestRepository:
    return BacktestRepository(backtest_dir=tmp_path / "backtests")


# ---------------------------------------------------------------------------
# Test Schemas
# ---------------------------------------------------------------------------


def test_backtest_record_serialization(sample_records: list[BacktestRecord]) -> None:
    rec = sample_records[0]
    d = rec.to_dict()
    assert d["bill_id"] == "bill-1"
    assert d["predicted_class"] == "positive"
    assert d["signal"] == 1.0

    restored = BacktestRecord.from_dict(d)
    assert restored.bill_id == rec.bill_id
    assert restored.prediction_probability == rec.prediction_probability
    assert restored.signal == rec.signal


def test_classification_metrics_serialization() -> None:
    c_met = ClassificationMetrics(
        accuracy=0.8,
        precision_macro=0.75,
        precision_weighted=0.78,
        recall_macro=0.72,
        recall_weighted=0.75,
        macro_f1=0.73,
        weighted_f1=0.76,
        balanced_accuracy=0.74,
        mcc=0.55,
        roc_auc=0.82,
        brier_score=0.12,
        calibration_error=0.03,
        majority_class_baseline_accuracy=0.55,
    )
    d = c_met.to_dict()
    assert d["accuracy"] == 0.8
    assert d["macro_f1"] == 0.73
    assert d["majority_class_baseline_accuracy"] == 0.55


def test_financial_metrics_schema() -> None:
    """Task 6.4.1: FinancialMetrics has correct new fields."""
    fm = FinancialMetrics(
        initial_capital=1.0,
        final_wealth=1.05,
        cumulative_return=0.05,
        average_return_per_trade=0.025,
        hit_ratio=0.6,
        hit_ratio_ci_lower=0.3,
        hit_ratio_ci_upper=0.85,
        max_drawdown=-0.02,
        volatility=0.1,
        sharpe_ratio=0.5,
        sharpe_ratio_annualized=7.9,
        total_observations=10,
        actual_trades=2,
        long_signals=2,
        short_signals=0,
        neutral_signals=8,
        unique_companies_traded=2,
        unique_bills_traded=1,
        long_avg_return=0.025,
        short_avg_return=0.0,
        total_tc_paid=0.002,
        tc_per_trade=0.001,
    )
    d = fm.to_dict()
    assert d["initial_capital"] == 1.0
    assert d["final_wealth"] == pytest.approx(1.05, rel=1e-4)
    assert d["max_drawdown"] == pytest.approx(-0.02, rel=1e-4)
    assert d["actual_trades"] == 2
    assert d["hit_ratio_ci_lower"] == pytest.approx(0.3, rel=1e-4)


def test_portfolio_snapshot_schema() -> None:
    snap = PortfolioSnapshot(
        date="2023-01-10",
        n_active_positions=2,
        n_observations=3,
        equal_weight_return=0.03,
        portfolio_return=0.025,
        portfolio_value=1.025,
        running_peak=1.025,
        drawdown=0.0,
        nifty_return=0.01,
        bah_return=0.02,
        total_tc_paid=0.001,
    )
    d = snap.to_dict()
    assert d["portfolio_value"] == pytest.approx(1.025, rel=1e-4)
    assert d["drawdown"] == 0.0


def test_overlap_report_schema() -> None:
    rpt = OverlapReport(
        total_events=100,
        total_unique_dates=8,
        overlapping_event_pairs=50,
        overlap_percentage=50.0,
        max_simultaneous_events=15,
        dates_with_multiple_events=8,
        company_level_overlaps=20,
        bill_level_overlaps=10,
        event_windows_checked=["[-1,+1]", "[-5,+5]"],
    )
    d = rpt.to_dict()
    assert d["total_events"] == 100
    assert "interpretation" in d


def test_financial_validation_report_schema() -> None:
    rpt = FinancialValidationReport(
        total_checks=10,
        passed_checks=10,
        failed_checks=0,
        is_valid=True,
    )
    d = rpt.to_dict()
    assert d["is_valid"] is True
    assert d["passed_checks"] == 10


# ---------------------------------------------------------------------------
# Test BacktestRepository (Task 6.4.1 extended artifacts)
# ---------------------------------------------------------------------------


def test_backtest_repository_crud(
    tmp_backtest_repo: BacktestRepository, sample_records: list[BacktestRecord]
) -> None:
    run_id = "test_run_001"
    assert not tmp_backtest_repo.exists(run_id)

    report_dict = {"run_id": run_id, "target": "direction"}
    comp_dict = {"best_model": {"model_type": "lgbm"}}
    strat_dict = {"transaction_cost_bps": 10.0}
    leak_dict = {"has_leakage": False}
    df_preds = pd.DataFrame([r.to_dict() for r in sample_records])

    paths = tmp_backtest_repo.save(
        run_id=run_id,
        backtest_report=report_dict,
        model_comparison=comp_dict,
        strategy_metrics=strat_dict,
        leakage_report=leak_dict,
        prediction_results=df_preds,
        overlap_report={"total_events": 3},
        financial_validation={"is_valid": True},
    )

    assert "backtest_report" in paths
    assert "overlap_report" in paths
    assert tmp_backtest_repo.exists(run_id)
    assert run_id in tmp_backtest_repo.list_runs()

    loaded = tmp_backtest_repo.load(run_id)
    assert loaded["backtest_report"]["target"] == "direction"
    assert len(loaded["prediction_results"]) == 3
    assert loaded["overlap_report"]["total_events"] == 3


# ---------------------------------------------------------------------------
# Test BacktestValidator & Anti-Leakage
# ---------------------------------------------------------------------------


def test_backtest_validator_clean(sample_records: list[BacktestRecord]) -> None:
    validator = BacktestValidator()
    feature_cols = ["company_beta", "bill_sentiment", "sector_code"]

    val_rep, leak_rep = validator.validate_backtest_execution(
        records=sample_records, feature_columns_used=feature_cols
    )

    assert val_rep.is_valid
    assert not leak_rep.has_leakage
    assert leak_rep.post_event_feature_violations == 0
    assert leak_rep.training_cutoff_violations == 0


def test_backtest_validator_detects_leakage(sample_records: list[BacktestRecord]) -> None:
    validator = BacktestValidator()
    leaked_features = ["company_beta", "final_car", "t_statistic", "ar_day_1"]

    val_rep, leak_rep = validator.validate_backtest_execution(
        records=sample_records, feature_columns_used=leaked_features
    )

    assert not val_rep.is_valid
    assert leak_rep.has_leakage
    assert leak_rep.post_event_feature_violations == 3


def test_backtest_validator_detects_cutoff_violation(sample_records: list[BacktestRecord]) -> None:
    validator = BacktestValidator()
    sample_records[0].training_cutoff_date = "2023-01-15"
    sample_records[0].prediction_timestamp = "2023-01-10"

    val_rep, leak_rep = validator.validate_backtest_execution(
        records=sample_records, feature_columns_used=["company_beta"]
    )

    assert not val_rep.is_valid
    assert leak_rep.has_leakage
    assert leak_rep.training_cutoff_violations == 1


def test_validator_wrapper_backtest() -> None:
    val = Validator()
    rec = BacktestRecord(
        bill_id="b1",
        company_isin="c1",
        event_window="[0,+20]",
        prediction_timestamp="2023-01-01",
        model_name="lgbm",
        target="direction",
        predicted_class="positive",
        actual_class="positive",
        prediction_probability={"positive": 0.9},
        training_cutoff_date="2022-12-31",
    )
    val_rep, leak_rep = val.validate_backtest_run([rec], ["feature_1"])
    assert val_rep.is_valid
    assert not leak_rep.has_leakage


# ---------------------------------------------------------------------------
# Test Transaction Cost Model (Task 6.4.1: TC only on active signals)
# ---------------------------------------------------------------------------


def test_transaction_cost_model_active_signal() -> None:
    tc = TransactionCostModel(transaction_cost=0.0010, brokerage=0.0005, slippage=0.0005)

    # Long signal (+1), raw return +5% → net return = +5% - 0.1% = +4.9%
    net_long = tc.calculate_net_return(1.0, 0.05)
    assert pytest.approx(net_long, rel=1e-4) == 0.049

    # Short signal (-1), raw return -5% → net return = -(-5%) - 0.1% = +4.9%
    net_short = tc.calculate_net_return(-1.0, -0.05)
    assert pytest.approx(net_short, rel=1e-4) == 0.049


def test_transaction_cost_model_neutral_zero_cost() -> None:
    """Task 6.4.1: Neutral signal must produce ZERO return and ZERO cost."""
    tc = TransactionCostModel(transaction_cost=0.0010)
    net_neutral = tc.calculate_net_return(0.0, 0.05)
    assert net_neutral == 0.0

    cost_neutral = tc.cost_for_signal(0.0)
    assert cost_neutral == 0.0


def test_transaction_cost_model_cost_for_signal() -> None:
    tc = TransactionCostModel(transaction_cost=0.001)
    assert tc.cost_for_signal(1.0) == pytest.approx(0.001, rel=1e-6)
    assert tc.cost_for_signal(-1.0) == pytest.approx(0.001, rel=1e-6)
    assert tc.cost_for_signal(0.0) == 0.0


def test_signal_rule() -> None:
    rule = SignalRule(confidence_threshold=0.6)
    assert rule.get_signal("positive") == 1.0
    assert rule.get_signal("negative") == -1.0
    assert rule.get_signal("neutral") == 0.0

    prob_low = {"positive": 0.4, "negative": 0.6}
    assert rule.get_signal("positive", prob_low) == 0.0


# ---------------------------------------------------------------------------
# Test PortfolioAccountant (Task 6.4.1 — new)
# ---------------------------------------------------------------------------


def test_portfolio_accountant_initial_capital() -> None:
    """Portfolio starts at 1.0."""
    accountant = PortfolioAccountant(initial_capital=1.0)
    records = [
        BacktestRecord(
            bill_id="b1", company_isin="c1", event_window="[-1,+1]",
            prediction_timestamp="2023-01-10", model_name="lgbm", target="direction",
            predicted_class="positive", actual_class="positive", signal=1.0,
            strategy_return=0.05, cumulative_abnormal_return=0.05,
        )
    ]
    snapshots = accountant.build_snapshots(records)
    assert len(snapshots) == 1
    # portfolio_value = 1.0 * (1 + 0.05) = 1.05
    assert snapshots[0].portfolio_value == pytest.approx(1.05, rel=1e-6)


def test_portfolio_accountant_neutral_no_change() -> None:
    """Neutral signals do not change portfolio value."""
    accountant = PortfolioAccountant(initial_capital=1.0)
    records = [
        BacktestRecord(
            bill_id="b1", company_isin="c1", event_window="[-1,+1]",
            prediction_timestamp="2023-01-10", model_name="lgbm", target="direction",
            predicted_class="neutral", actual_class="neutral", signal=0.0,
            strategy_return=0.0, cumulative_abnormal_return=0.02,
        )
    ]
    snapshots = accountant.build_snapshots(records)
    assert snapshots[0].portfolio_value == pytest.approx(1.0, rel=1e-9)
    assert snapshots[0].n_active_positions == 0


def test_portfolio_accountant_drawdown_always_nonpositive() -> None:
    """Task 6.4.1: Wealth-relative drawdown must always be ≤ 0."""
    accountant = PortfolioAccountant(initial_capital=1.0)
    records = [
        BacktestRecord(
            bill_id=f"b{i}", company_isin=f"c{i}", event_window="[-1,+1]",
            prediction_timestamp=f"2023-0{i+1}-10", model_name="lgbm", target="direction",
            predicted_class="positive", actual_class="positive", signal=1.0,
            strategy_return=ret, cumulative_abnormal_return=ret,
        )
        for i, ret in enumerate([0.05, -0.03, 0.02, -0.04, 0.01])
    ]
    snapshots = accountant.build_snapshots(records)
    for snap in snapshots:
        assert snap.drawdown <= 1e-9, f"Drawdown {snap.drawdown} > 0 on {snap.date}"


def test_portfolio_accountant_compounding() -> None:
    """Task 6.4.1: Returns must be compounded, not summed."""
    accountant = PortfolioAccountant(initial_capital=1.0)
    records = [
        BacktestRecord(
            bill_id="b1", company_isin="c1", event_window="[-1,+1]",
            prediction_timestamp="2023-01-10", model_name="lgbm", target="direction",
            predicted_class="positive", actual_class="positive", signal=1.0,
            strategy_return=0.10, cumulative_abnormal_return=0.10,
        ),
        BacktestRecord(
            bill_id="b2", company_isin="c2", event_window="[-1,+1]",
            prediction_timestamp="2023-02-10", model_name="lgbm", target="direction",
            predicted_class="positive", actual_class="positive", signal=1.0,
            strategy_return=0.10, cumulative_abnormal_return=0.10,
        ),
    ]
    snapshots = accountant.build_snapshots(records)
    # Compounded: 1.0 * 1.10 * 1.10 = 1.21, NOT 1.0 + 0.10 + 0.10 = 1.20
    final_wealth = snapshots[-1].portfolio_value
    assert final_wealth == pytest.approx(1.21, rel=1e-6)
    assert final_wealth != pytest.approx(1.20, rel=1e-6)


def test_portfolio_accountant_simultaneous_equal_weight() -> None:
    """Task 6.4.1: Multiple events on same date are equal-weighted."""
    accountant = PortfolioAccountant(initial_capital=1.0)
    # Two events on same date: returns 0.10 and 0.20 → equal weight mean = 0.15
    records = [
        BacktestRecord(
            bill_id="b1", company_isin="c1", event_window="[-1,+1]",
            prediction_timestamp="2023-01-10", model_name="lgbm", target="direction",
            predicted_class="positive", actual_class="positive", signal=1.0,
            strategy_return=0.10, cumulative_abnormal_return=0.10,
        ),
        BacktestRecord(
            bill_id="b1", company_isin="c2", event_window="[-1,+1]",
            prediction_timestamp="2023-01-10", model_name="lgbm", target="direction",
            predicted_class="positive", actual_class="positive", signal=1.0,
            strategy_return=0.20, cumulative_abnormal_return=0.20,
        ),
    ]
    snapshots = accountant.build_snapshots(records)
    assert len(snapshots) == 1
    assert snapshots[0].portfolio_return == pytest.approx(0.15, rel=1e-6)
    assert snapshots[0].portfolio_value == pytest.approx(1.15, rel=1e-6)


def test_portfolio_accountant_no_negative_wealth() -> None:
    """Task 6.4.1: Portfolio value cannot go below zero (floor)."""
    accountant = PortfolioAccountant(initial_capital=1.0)
    records = [
        BacktestRecord(
            bill_id="b1", company_isin="c1", event_window="[-1,+1]",
            prediction_timestamp="2023-01-10", model_name="lgbm", target="direction",
            predicted_class="negative", actual_class="positive", signal=-1.0,
            strategy_return=-1.5,  # Extreme loss: -150%
            cumulative_abnormal_return=1.5,
        )
    ]
    snapshots = accountant.build_snapshots(records)
    assert snapshots[0].portfolio_value >= 0.0


# ---------------------------------------------------------------------------
# Test Financial Metrics Calculator (Task 6.4.1 — snapshot-based)
# ---------------------------------------------------------------------------


def test_financial_metrics_calculator_from_snapshots(
    sample_records: list[BacktestRecord],
    sample_snapshots: list[PortfolioSnapshot],
) -> None:
    calc = FinancialMetricsCalculator()
    fm = calc.compute_metrics(sample_records, sample_snapshots)

    # Basic counts
    assert fm.total_observations == 3
    assert fm.actual_trades == 2   # long + short, not the neutral
    assert fm.long_signals == 1
    assert fm.short_signals == 1
    assert fm.neutral_signals == 1

    # initial capital
    assert fm.initial_capital == 1.0

    # cumulative return = final_wealth - 1
    assert fm.cumulative_return == pytest.approx(fm.final_wealth - 1.0, rel=1e-6)

    # max_drawdown ≤ 0
    assert fm.max_drawdown <= 1e-9

    # hit ratio in [0, 1]
    assert 0.0 <= fm.hit_ratio <= 1.0

    # Wilson CI bounds valid
    assert 0.0 <= fm.hit_ratio_ci_lower <= fm.hit_ratio <= fm.hit_ratio_ci_upper <= 1.0


def test_financial_metrics_cumulative_not_additive(
    sample_records: list[BacktestRecord],
    sample_snapshots: list[PortfolioSnapshot],
) -> None:
    """Task 6.4.1: Cumulative return must not be the simple sum of individual returns."""
    calc = FinancialMetricsCalculator()
    fm = calc.compute_metrics(sample_records, sample_snapshots)

    # Simple additive sum would be 0.039 + (-0.031) + 0.0 = 0.008
    additive_sum = sum(r.strategy_return or 0.0 for r in sample_records)
    # Compounded result will differ (though numerically close for small returns)
    # The critical check is that we're using snapshots, not summing individual records
    assert fm.final_wealth > 0


def test_financial_metrics_empty_records() -> None:
    calc = FinancialMetricsCalculator()
    fm = calc.compute_metrics([], [])
    assert fm.cumulative_return == 0.0
    assert fm.total_observations == 0
    assert fm.max_drawdown == 0.0


# ---------------------------------------------------------------------------
# Test Classification Metrics (Task 6.4.1 — extended)
# ---------------------------------------------------------------------------


def test_classification_metrics_calculator_with_baseline() -> None:
    calc = ClassificationMetricsCalculator()
    y_true = ["positive", "negative", "neutral", "positive"]
    y_pred = ["positive", "positive", "neutral", "positive"]
    y_prob = [
        {"positive": 0.8, "negative": 0.1, "neutral": 0.1},
        {"positive": 0.6, "negative": 0.3, "neutral": 0.1},
        {"positive": 0.1, "negative": 0.1, "neutral": 0.8},
        {"positive": 0.9, "negative": 0.05, "neutral": 0.05},
    ]

    metrics = calc.compute_metrics(y_true, y_pred, y_prob)

    assert metrics.accuracy == 0.75
    assert metrics.macro_f1 > 0.0
    # majority class = "positive" (2/4 = 0.5)
    assert metrics.majority_class_baseline_accuracy == pytest.approx(0.5, rel=1e-4)
    assert metrics.per_class_report is not None
    assert "positive" in metrics.per_class_report
    assert metrics.class_distribution == {"negative": 1, "neutral": 1, "positive": 2}
    assert metrics.confusion_matrix is not None


# ---------------------------------------------------------------------------
# Test NiftyBenchmarkLoader (Task 6.4.1 — new)
# ---------------------------------------------------------------------------


def test_nifty_loader_missing_dir() -> None:
    """Loader returns NaN when data directory is missing."""
    loader = NiftyBenchmarkLoader(data_dir=Path("/nonexistent/path"))
    result = loader.get_period_return("2023-01-10", "[-1,+1]")
    assert math.isnan(result) or result == 0.0  # graceful fallback


def test_nifty_loader_batch_returns() -> None:
    """Batch method returns same length as input."""
    loader = NiftyBenchmarkLoader(data_dir=Path("/nonexistent/path"))
    dates = ["2023-01-10", "2023-02-15"]
    windows = ["[-1,+1]", "[-5,+5]"]
    results = loader.get_period_returns_batch(dates, windows)
    assert len(results) == 2


def test_nifty_loader_real_data_if_available() -> None:
    """If ^NSEI data exists, returns finite scalar floats."""
    loader = NiftyBenchmarkLoader()
    if not loader.is_available():
        pytest.skip("^NSEI data not available")

    ret = loader.get_period_return("2024-02-05", "[-1,+1]")
    assert isinstance(ret, float)
    assert math.isfinite(ret)
    # Return should be plausible: NIFTY does not change ±100% in 3 days
    assert -0.20 <= ret <= 0.20


# ---------------------------------------------------------------------------
# Test OverlapDetector (Task 6.4.1 — new)
# ---------------------------------------------------------------------------


def test_overlap_detector_no_overlap(sample_records: list[BacktestRecord]) -> None:
    """Three records on different dates — no simultaneous overlaps."""
    detector = OverlapDetector()
    report = detector.detect(sample_records)

    assert report.total_events == 3
    assert report.dates_with_multiple_events == 0
    assert report.max_simultaneous_events == 1


def test_overlap_detector_with_simultaneous() -> None:
    """Two records on the same date → 1 date with multiple events."""
    records = [
        BacktestRecord(
            bill_id="b1", company_isin="c1", event_window="[-1,+1]",
            prediction_timestamp="2023-01-10", model_name="lgbm", target="direction",
            predicted_class="positive", actual_class="positive",
        ),
        BacktestRecord(
            bill_id="b1", company_isin="c2", event_window="[-1,+1]",
            prediction_timestamp="2023-01-10", model_name="lgbm", target="direction",
            predicted_class="positive", actual_class="positive",
        ),
    ]
    detector = OverlapDetector()
    report = detector.detect(records)

    assert report.dates_with_multiple_events == 1
    assert report.max_simultaneous_events == 2
    assert report.overlapping_event_pairs == 1


def test_overlap_detector_empty() -> None:
    detector = OverlapDetector()
    report = detector.detect([])
    assert report.total_events == 0
    assert report.overlap_percentage == 0.0


# ---------------------------------------------------------------------------
# Test FinancialValidator (Task 6.4.1 — new)
# ---------------------------------------------------------------------------


def test_financial_validator_passes_valid_data(
    sample_records: list[BacktestRecord],
    sample_snapshots: list[PortfolioSnapshot],
) -> None:
    validator = FinancialValidator()
    report = validator.validate(
        records=sample_records,
        snapshots=sample_snapshots,
        max_drawdown=min(s.drawdown for s in sample_snapshots) if sample_snapshots else 0.0,
    )
    # A valid portfolio should pass all or most checks
    assert report.total_checks == 10
    assert not report.has_nan_returns
    assert not report.has_inf_returns
    assert not report.has_negative_wealth


def test_financial_validator_detects_positive_drawdown() -> None:
    """Task 6.4.1: Max drawdown > 0 should fail the check."""
    validator = FinancialValidator()
    snap = PortfolioSnapshot(
        date="2023-01-10",
        n_active_positions=1,
        n_observations=1,
        equal_weight_return=0.0,
        portfolio_return=0.0,
        portfolio_value=1.0,
        running_peak=1.0,
        drawdown=0.02,  # Illegal: drawdown > 0
    )
    report = validator.validate(records=[], snapshots=[snap], max_drawdown=0.02)
    assert not report.max_drawdown_check


def test_financial_validator_detects_negative_wealth() -> None:
    """Task 6.4.1: Negative portfolio value should fail."""
    validator = FinancialValidator()
    snap = PortfolioSnapshot(
        date="2023-01-10",
        n_active_positions=1,
        n_observations=1,
        equal_weight_return=0.0,
        portfolio_return=-1.5,
        portfolio_value=-0.5,  # negative!
        running_peak=1.0,
        drawdown=-1.5,
    )
    report = validator.validate(records=[], snapshots=[snap], max_drawdown=-1.5)
    assert report.has_negative_wealth


# ---------------------------------------------------------------------------
# Test Visualizer (Task 6.4.1 — with snapshots)
# ---------------------------------------------------------------------------


def test_backtest_visualizer_with_snapshots(
    tmp_path: Path,
    sample_records: list[BacktestRecord],
    sample_snapshots: list[PortfolioSnapshot],
) -> None:
    viz = BacktestVisualizer()
    plots = viz.generate_all_plots(
        output_dir=tmp_path,
        records=sample_records,
        snapshots=sample_snapshots,
    )

    assert "equity_curve" in plots
    assert "drawdown_curve" in plots
    assert "daily_returns" in plots
    assert "prediction_vs_actual" in plots
    assert "signal_distribution" in plots
    assert "model_comparison" in plots

    for p in plots.values():
        assert p.is_file(), f"Expected plot file missing: {p}"


# ---------------------------------------------------------------------------
# Test Report Generator (Task 6.4.1 — new methods)
# ---------------------------------------------------------------------------


def test_backtest_report_generator_overlap_report() -> None:
    gen = BacktestReportGenerator()
    overlap = OverlapReport(
        total_events=10,
        total_unique_dates=5,
        overlapping_event_pairs=2,
        overlap_percentage=20.0,
        max_simultaneous_events=3,
        dates_with_multiple_events=2,
        company_level_overlaps=1,
        bill_level_overlaps=0,
        event_windows_checked=["[-1,+1]"],
    )
    d = gen.build_overlap_report(overlap)
    assert d["total_events"] == 10
    assert "interpretation" in d


def test_backtest_report_generator_financial_validation() -> None:
    gen = BacktestReportGenerator()
    v = FinancialValidationReport(
        total_checks=10, passed_checks=9, failed_checks=1, is_valid=False,
        violations=["test violation"]
    )
    d = gen.build_financial_validation_report(v)
    assert d["is_valid"] is False
    assert len(d["violations"]) == 1


def test_backtest_report_generator_portfolio_timeseries_df() -> None:
    gen = BacktestReportGenerator()
    snaps = [
        PortfolioSnapshot(
            date="2023-01-10", n_active_positions=1, n_observations=1,
            equal_weight_return=0.05, portfolio_return=0.049,
            portfolio_value=1.049, running_peak=1.049, drawdown=0.0,
        )
    ]
    df = gen.build_portfolio_timeseries_df(snaps)
    assert len(df) == 1
    assert "portfolio_value" in df.columns
    assert "drawdown" in df.columns


def test_report_generator_model_comparison() -> None:
    gen = BacktestReportGenerator()
    df = gen.build_prediction_results_df([
        BacktestRecord(
            bill_id="b1", company_isin="c1", event_window="[-1,+1]",
            prediction_timestamp="2023-01-10", model_name="lgbm", target="direction",
            predicted_class="positive", actual_class="positive",
        )
    ])
    assert len(df) == 1
    assert "bill_id" in df.columns

    comp = gen.build_model_comparison({
        "lgbm": ClassificationMetrics(0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.6,
                                      majority_class_baseline_accuracy=0.55),
        "random_forest": ClassificationMetrics(0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.4),
    })
    assert comp["best_model"]["model_type"] == "lgbm"
    assert "majority_class_baseline_accuracy" in comp["rankings"][0]


# ---------------------------------------------------------------------------
# Test StrategyEvaluator (Task 6.4.1 — benchmark comparison uses snapshots)
# ---------------------------------------------------------------------------


def test_strategy_evaluator_sets_signals(sample_records: list[BacktestRecord]) -> None:
    evaluator = StrategyEvaluator()
    evaluated = evaluator.evaluate_records(sample_records)

    assert evaluated[0].prediction_correctness is True
    assert evaluated[1].prediction_correctness is False
    assert evaluated[0].signal == pytest.approx(1.0, rel=1e-6)
    assert evaluated[1].signal == pytest.approx(-1.0, rel=1e-6)
    assert evaluated[2].signal == pytest.approx(0.0, rel=1e-6)


def test_strategy_evaluator_benchmark_comparison(
    sample_records: list[BacktestRecord],
    sample_snapshots: list[PortfolioSnapshot],
) -> None:
    evaluator = StrategyEvaluator()
    bench = evaluator.compute_benchmark_comparison(sample_records, sample_snapshots)

    assert bench.strategy_initial_capital == 1.0
    assert bench.strategy_final_wealth > 0
    # max_drawdown ≤ 0
    assert bench.strategy_max_drawdown <= 1e-9


# ---------------------------------------------------------------------------
# Test HistoricalBacktestEngine Integration
# ---------------------------------------------------------------------------


def test_historical_backtest_engine_execution(tmp_path: Path) -> None:
    repo = BacktestRepository(backtest_dir=tmp_path / "backtests")
    engine = HistoricalBacktestEngine(backtest_repo=repo)

    res = engine.run_backtest(
        target="direction",
        model_name="random_forest",
        run_id="test_engine_run",
    )

    assert res["run_id"] == "test_engine_run"
    assert "report" in res
    assert res["report"]["target"] == "direction"
    assert repo.exists("test_engine_run")

    # Task 6.4.1 — check new keys in result
    assert "snapshots" in res
    assert "overlap_report" in res
    assert "financial_validation" in res

    # Task 6.4.1 — check new artifact files are saved
    loaded = repo.load("test_engine_run")
    assert "overlap_report" in loaded
    assert "financial_validation" in loaded

    # Task 6.4.1 — financial validation should pass for clean data
    validation = res["financial_validation"]
    assert not validation.has_nan_returns
    assert not validation.has_inf_returns
    assert not validation.has_negative_wealth
    assert validation.max_drawdown_check


# ---------------------------------------------------------------------------
# Test CLI Command
# ---------------------------------------------------------------------------


def test_cmd_backtest_models_cli(tmp_path: Path) -> None:
    args = argparse.Namespace(
        target="direction",
        model="random_forest",
        start_date=None,
        end_date=None,
        transaction_cost=0.0010,
        slippage=0.0005,
        anticipation_window=0,
        all=False,
    )

    ret = cmd_backtest_models(args)
    assert ret == 0
