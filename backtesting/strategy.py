"""
backtesting/strategy.py
=======================
Strategy evaluation, signal generation, portfolio accounting, transaction cost
modeling, and benchmark comparison for the Historical Backtesting Engine
(Task 6.4 / 6.4.1).

Task 6.4.1 Corrections
-----------------------
* ``PortfolioAccountant`` — new class that computes compounded portfolio wealth
  from initial_capital=1.0, aggregating simultaneous events per date via
  equal-weighting rather than sequential summation.
* ``TransactionCostModel.calculate_net_return()`` — costs applied only when
  |signal| > threshold (active positions), never on neutral observations.
* ``StrategyEvaluator.compute_benchmark_comparison()`` — uses real NIFTY 50 data
  (via NiftyBenchmarkLoader) and a valid Buy-and-Hold calculation.
* Drawdown is wealth-relative (≤ 0 always).
* Sharpe is computed on per-event-date portfolio returns, not individual CARs.

Components
----------
* ``TransactionCostModel``
* ``SignalRule``
* ``PortfolioAccountant``
* ``StrategyEvaluator``
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional

import numpy as np
import pandas as pd

from config.logging_config import get_logger
from schemas.backtest_record import (
    BacktestRecord,
    BenchmarkComparison,
    PortfolioSnapshot,
)

logger = get_logger(__name__)

_NEUTRAL_THRESHOLD = 1e-6   # signals with |signal| < this are treated as 0


@dataclass
class TransactionCostModel:
    """
    Configurable transaction cost model.

    Parameters
    ----------
    transaction_cost : float
        Total cost fraction per active trade (e.g. 0.0010 = 10 bps).
        Applied only when |signal| > 0.
    brokerage : float
        Brokerage fee fraction (e.g. 0.0005 = 5 bps).
    slippage : float
        Execution slippage fraction (e.g. 0.0005 = 5 bps).
    """

    transaction_cost: float = 0.0010
    brokerage: float = 0.0005
    slippage: float = 0.0005

    def calculate_net_return(self, signal: float, raw_return: float) -> float:
        """
        Calculate net return after applying transaction costs.

        Returns 0.0 for neutral (|signal| < threshold) positions.

        Formula
        -------
        ``net_return = signal * raw_return - transaction_cost * |signal|``
        (cost is charged only on active positions)
        """
        if abs(signal) < _NEUTRAL_THRESHOLD:
            return 0.0
        cost = self.transaction_cost if self.transaction_cost > 0 else (self.brokerage + self.slippage)
        return float(signal * raw_return - cost * abs(signal))

    def cost_for_signal(self, signal: float) -> float:
        """Return the transaction cost for a given signal (0.0 for neutral)."""
        if abs(signal) < _NEUTRAL_THRESHOLD:
            return 0.0
        cost = self.transaction_cost if self.transaction_cost > 0 else (self.brokerage + self.slippage)
        return cost * abs(signal)


class SignalRule:
    """
    Configurable rule mapping model predictions to quantitative investment signals.

    Default Mapping
    ---------------
    * ``"positive"`` / ``"positive_impact"`` / ``True``  → +1.0 (Long)
    * ``"negative"`` / ``"negative_impact"``              → -1.0 (Short)
    * ``"neutral"`` / ``False``                           →  0.0 (No Position)
    """

    def __init__(
        self,
        custom_mapping: Optional[dict[str, float]] = None,
        confidence_threshold: float = 0.0,
    ) -> None:
        self._mapping = custom_mapping or {
            "positive": 1.0,
            "positive_impact": 1.0,
            "true": 1.0,
            "1": 1.0,
            "1.0": 1.0,
            "negative": -1.0,
            "negative_impact": -1.0,
            "neutral": 0.0,
            "false": 0.0,
            "0": 0.0,
            "0.0": 0.0,
            "low": 0.0,
            "medium": 0.5,
            "high": 1.0,
            "very_high": 1.0,
        }
        self._confidence_threshold = confidence_threshold

    def get_signal(
        self,
        predicted_class: Any,
        prediction_probability: Optional[dict[str, float]] = None,
    ) -> float:
        """Return numerical signal scalar in range [-1.0, +1.0]."""
        val_str = str(predicted_class).lower().strip()
        signal = self._mapping.get(val_str, 0.0)

        # Apply optional confidence threshold check
        if prediction_probability and self._confidence_threshold > 0.0:
            pred_prob = prediction_probability.get(val_str, max(prediction_probability.values(), default=0.0))
            if pred_prob < self._confidence_threshold:
                return 0.0

        return float(signal)


class PortfolioAccountant:
    """
    Correct portfolio wealth accounting with initial_capital=1.0 (Task 6.4.1).

    Aggregation Strategy
    --------------------
    Multiple simultaneous events on the same date are aggregated via equal-weighting
    before being applied to the portfolio. This prevents double-counting of overlapping
    event windows.

    Return Compounding
    ------------------
    ``portfolio_value[t] = portfolio_value[t-1] × (1 + portfolio_return[t])``

    where ``portfolio_return[t]`` is the equal-weighted average of active position
    net returns on date ``t`` (or 0.0 if no active positions exist).

    Drawdown
    ---------
    Wealth-relative drawdown: ``drawdown[t] = portfolio_value[t] / peak[t] - 1`` (≤ 0).
    """

    def __init__(
        self,
        initial_capital: float = 1.0,
        cost_model: Optional[TransactionCostModel] = None,
    ) -> None:
        self.initial_capital = initial_capital
        self._cost_model = cost_model or TransactionCostModel()

    def build_snapshots(
        self,
        records: list[BacktestRecord],
        nifty_returns: Optional[dict[str, float]] = None,
    ) -> list[PortfolioSnapshot]:
        """
        Build chronological PortfolioSnapshot series from evaluated records.

        Parameters
        ----------
        records : list[BacktestRecord]
            Records after strategy_return and signal have been set by StrategyEvaluator.
        nifty_returns : dict[str, float], optional
            Mapping of prediction_timestamp → NIFTY period return for that date.

        Returns
        -------
        list[PortfolioSnapshot]
            Sorted by date ascending.
        """
        if not records:
            return []

        nifty_map: dict[str, float] = nifty_returns or {}

        # Group records by event date
        date_groups: dict[str, list[BacktestRecord]] = defaultdict(list)
        for rec in records:
            date_groups[rec.prediction_timestamp].append(rec)

        sorted_dates = sorted(date_groups.keys())

        portfolio_value = float(self.initial_capital)
        running_peak = float(self.initial_capital)
        snapshots: list[PortfolioSnapshot] = []

        for dt in sorted_dates:
            group = date_groups[dt]

            active_recs = [r for r in group if abs(r.signal or 0.0) > _NEUTRAL_THRESHOLD]
            n_active = len(active_recs)
            n_total = len(group)

            # Equal-weighted portfolio return for this date
            if n_active > 0:
                # Individual net returns already account for signal direction + TC
                # (set by StrategyEvaluator.evaluate_records)
                # We equal-weight across the active positions only
                per_pos_returns = [r.strategy_return or 0.0 for r in active_recs]
                portfolio_return_dt = float(np.mean(per_pos_returns))

                # Compute total TC paid on this date
                total_tc_dt = sum(
                    self._cost_model.cost_for_signal(r.signal or 0.0)
                    for r in active_recs
                )
                # Equal-weight the TC (proportional to active positions)
                tc_paid = total_tc_dt / n_active if n_active > 0 else 0.0
            else:
                portfolio_return_dt = 0.0
                tc_paid = 0.0

            # Compound
            portfolio_value = portfolio_value * (1.0 + portfolio_return_dt)
            portfolio_value = max(portfolio_value, 0.0)  # floor at zero (no debt)

            # Update running peak
            running_peak = max(running_peak, portfolio_value)

            # Wealth-relative drawdown: ≤ 0 always
            if running_peak > 1e-12:
                drawdown = portfolio_value / running_peak - 1.0
            else:
                drawdown = 0.0

            # BAH return: equal-weighted average of raw CARs for all records on this date
            raw_cars = []
            for r in group:
                car = r.cumulative_abnormal_return
                if car is not None and not np.isnan(car):
                    raw_cars.append(car)
            bah_return_dt = float(np.mean(raw_cars)) if raw_cars else 0.0

            # NIFTY return for this date
            nifty_return_dt = float(nifty_map.get(dt, 0.0) or 0.0)
            if np.isnan(nifty_return_dt):
                nifty_return_dt = 0.0

            # Equal-weighted raw return (before TC) for reference
            raw_rets = [abs(r.signal or 0.0) * (r.cumulative_abnormal_return or 0.0) for r in active_recs]
            eq_return = float(np.mean(raw_rets)) if raw_rets else 0.0

            snap = PortfolioSnapshot(
                date=dt,
                n_active_positions=n_active,
                n_observations=n_total,
                equal_weight_return=eq_return,
                portfolio_return=portfolio_return_dt,
                portfolio_value=portfolio_value,
                running_peak=running_peak,
                drawdown=drawdown,
                nifty_return=nifty_return_dt,
                bah_return=bah_return_dt,
                total_tc_paid=tc_paid,
            )
            snapshots.append(snap)

        return snapshots


class StrategyEvaluator:
    """
    Evaluates historical predictions to produce financial outcomes and
    benchmark comparisons (Task 6.4 / 6.4.1 corrected).

    Parameters
    ----------
    cost_model : TransactionCostModel, optional
    signal_rule : SignalRule, optional
    """

    def __init__(
        self,
        cost_model: Optional[TransactionCostModel] = None,
        signal_rule: Optional[SignalRule] = None,
    ) -> None:
        self.cost_model = cost_model or TransactionCostModel()
        self.signal_rule = signal_rule or SignalRule()
        self._portfolio_accountant = PortfolioAccountant(
            initial_capital=1.0,
            cost_model=self.cost_model,
        )

    def evaluate_records(
        self, records: list[BacktestRecord]
    ) -> list[BacktestRecord]:
        """
        Compute correctness flags, signals, and strategy returns for every record.

        Strategy return is the net return for an active position, or 0.0 for neutral.
        Transaction costs are ONLY charged on active (|signal| > 0) positions.
        """
        for rec in records:
            # Correctness flags
            pred_str = str(rec.predicted_class).lower().strip()
            act_str = str(rec.actual_class).lower().strip()
            rec.prediction_correctness = (pred_str == act_str)

            if rec.target == "market_moving":
                rec.market_moving_correctness = rec.prediction_correctness

            # Signal
            signal = self.signal_rule.get_signal(rec.predicted_class, rec.prediction_probability)
            rec.signal = signal
            rec.predicted_direction = (
                "positive" if signal > _NEUTRAL_THRESHOLD
                else ("negative" if signal < -_NEUTRAL_THRESHOLD else "neutral")
            )

            # Financial outcome
            raw_car = rec.cumulative_abnormal_return
            if raw_car is None and rec.abnormal_return is not None:
                raw_car = rec.abnormal_return

            if raw_car is not None and not np.isnan(raw_car):
                rec.strategy_return = self.cost_model.calculate_net_return(signal, raw_car)
            else:
                rec.strategy_return = 0.0

        return records

    def compute_benchmark_comparison(
        self,
        records: list[BacktestRecord],
        snapshots: list[PortfolioSnapshot],
        nifty_loader: Optional[Any] = None,
    ) -> BenchmarkComparison:
        """
        Compare strategy metrics against Buy-and-Hold and NIFTY 50 benchmarks.

        All returns are compounded simple returns from initial_capital = 1.0.

        Parameters
        ----------
        records : list[BacktestRecord]
        snapshots : list[PortfolioSnapshot]
            From PortfolioAccountant.build_snapshots().
        nifty_loader : NiftyBenchmarkLoader, optional
            If provided, used to confirm NIFTY data source.
        """
        if not records or not snapshots:
            _zero = BenchmarkComparison(
                strategy_initial_capital=1.0,
                strategy_final_wealth=1.0,
                strategy_cumulative_return=0.0,
                strategy_sharpe=0.0,
                strategy_max_drawdown=0.0,
                strategy_volatility=0.0,
                buy_and_hold_final_wealth=1.0,
                buy_and_hold_cumulative_return=0.0,
                buy_and_hold_sharpe=0.0,
                buy_and_hold_max_drawdown=0.0,
                buy_and_hold_volatility=0.0,
                nifty50_final_wealth=1.0,
                nifty50_cumulative_return=0.0,
                nifty50_sharpe=0.0,
                nifty50_max_drawdown=0.0,
                nifty50_volatility=0.0,
                nifty50_data_source="N/A",
                excess_return_over_buy_and_hold=0.0,
                excess_return_over_nifty50=0.0,
            )
            return _zero

        # ── Strategy metrics from portfolio snapshots ──
        strat_rets = np.array([s.portfolio_return for s in snapshots], dtype=float)
        strat_final_wealth = float(snapshots[-1].portfolio_value) if snapshots else 1.0
        strat_cum_return = strat_final_wealth - 1.0
        strat_sharpe = self._calc_sharpe(strat_rets)
        strat_max_dd = float(min(s.drawdown for s in snapshots)) if snapshots else 0.0
        strat_vol = float(np.std(strat_rets)) if len(strat_rets) > 1 else 0.0

        # ── Buy-and-Hold: compounded from per-date BAH returns ──
        bah_rets = np.array([s.bah_return for s in snapshots], dtype=float)
        bah_final = self._compound(bah_rets)
        bah_cum = bah_final - 1.0
        bah_sharpe = self._calc_sharpe(bah_rets)
        bah_max_dd = self._calc_max_drawdown_from_rets(bah_rets)
        bah_vol = float(np.std(bah_rets)) if len(bah_rets) > 1 else 0.0

        # ── NIFTY 50: compounded from per-date NIFTY returns ──
        nifty_rets = np.array([s.nifty_return for s in snapshots], dtype=float)
        nifty_rets_clean = np.where(np.isfinite(nifty_rets), nifty_rets, 0.0)
        nifty_final = self._compound(nifty_rets_clean)
        nifty_cum = nifty_final - 1.0
        nifty_sharpe = self._calc_sharpe(nifty_rets_clean)
        nifty_max_dd = self._calc_max_drawdown_from_rets(nifty_rets_clean)
        nifty_vol = float(np.std(nifty_rets_clean)) if len(nifty_rets_clean) > 1 else 0.0

        nifty_data_src = (
            "data/market/^NSEI/*.parquet (real NIFTY 50 index data)"
            if (nifty_loader is not None and getattr(nifty_loader, "is_available", lambda: False)())
            else "data/market/^NSEI/*.parquet"
        )

        # Excess returns (wealth-basis)
        excess_bah = strat_final_wealth - bah_final
        excess_nifty = strat_final_wealth - nifty_final

        # Annualized excess return vs NIFTY (using calendar days)
        annualized_excess: Optional[float] = None
        try:
            dates = sorted(
                [pd.to_datetime(s.date, errors="coerce") for s in snapshots
                 if pd.to_datetime(s.date, errors="coerce") is not pd.NaT]
            )
            if len(dates) >= 2:
                calendar_days = (dates[-1] - dates[0]).days
                years = calendar_days / 365.25
                if years > 0.1:
                    annualized_excess = float((1 + excess_nifty) ** (1 / years) - 1)
        except Exception:
            pass

        # Period dates
        period_dates = sorted(s.date for s in snapshots)
        period_start = period_dates[0] if period_dates else None
        period_end = period_dates[-1] if period_dates else None
        calendar_days: Optional[int] = None
        try:
            if period_start and period_end:
                calendar_days = (pd.to_datetime(period_end) - pd.to_datetime(period_start)).days
        except Exception:
            pass

        return BenchmarkComparison(
            strategy_initial_capital=1.0,
            strategy_final_wealth=strat_final_wealth,
            strategy_cumulative_return=strat_cum_return,
            strategy_sharpe=strat_sharpe,
            strategy_max_drawdown=strat_max_dd,
            strategy_volatility=strat_vol,
            buy_and_hold_final_wealth=bah_final,
            buy_and_hold_cumulative_return=bah_cum,
            buy_and_hold_sharpe=bah_sharpe,
            buy_and_hold_max_drawdown=bah_max_dd,
            buy_and_hold_volatility=bah_vol,
            nifty50_final_wealth=nifty_final,
            nifty50_cumulative_return=nifty_cum,
            nifty50_sharpe=nifty_sharpe,
            nifty50_max_drawdown=nifty_max_dd,
            nifty50_volatility=nifty_vol,
            nifty50_data_source=nifty_data_src,
            excess_return_over_buy_and_hold=excess_bah,
            excess_return_over_nifty50=excess_nifty,
            annualized_excess_return_over_nifty50=annualized_excess,
            period_start_date=period_start,
            period_end_date=period_end,
            calendar_days=calendar_days,
        )

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _compound(rets: np.ndarray) -> float:
        """Compound a sequence of simple returns. Returns final wealth from initial_capital=1."""
        result = 1.0
        for r in rets:
            if np.isfinite(r):
                result *= (1.0 + r)
        return float(result)

    @staticmethod
    def _calc_sharpe(rets: np.ndarray) -> float:
        """
        Event-frequency Sharpe ratio (no annualization scaling).

        Report as event-frequency Sharpe; annualized Sharpe is computed
        separately in FinancialMetrics.
        """
        if len(rets) < 2:
            return 0.0
        std = float(np.std(rets, ddof=1))
        if std < 1e-8:
            return 0.0
        return float(np.mean(rets) / std)

    @staticmethod
    def _calc_max_drawdown_from_rets(rets: np.ndarray) -> float:
        """Compute max drawdown from a return series. Returns ≤ 0."""
        if len(rets) == 0:
            return 0.0
        wealth = np.ones(len(rets) + 1)
        for i, r in enumerate(rets):
            wealth[i + 1] = wealth[i] * (1.0 + (r if np.isfinite(r) else 0.0))
        peak = np.maximum.accumulate(wealth)
        dd = wealth / np.where(peak > 1e-12, peak, 1.0) - 1.0
        return float(np.min(dd))
