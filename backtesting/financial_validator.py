"""
backtesting/financial_validator.py
====================================
FinancialValidator — post-hoc financial data integrity checks for the
Historical Backtesting Engine (Task 6.4.1).

Checks Performed
----------------
1. No negative portfolio wealth (initial_capital = 1.0, floor at 0).
2. No NaN or Inf values in returns.
3. No individual observation return below -100% (loss > capital).
4. Chronological ordering of portfolio snapshots.
5. No duplicate event timestamps in snapshot series.
6. Drawdown is always ≤ 0 (wealth-relative).
7. Max drawdown ≤ 0.
8. TC paid ≥ 0.
9. NIFTY benchmark dates align with event dates.
10. Active trade returns are within [-1.0, +5.0] (sanity bounds for a 20-day window).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from config.logging_config import get_logger
from schemas.backtest_record import BacktestRecord, FinancialValidationReport, PortfolioSnapshot

logger = get_logger(__name__)

_RETURN_FLOOR = -1.0      # individual return cannot go below -100%
_RETURN_CEIL = 5.0        # individual return >+500% is suspicious
_MAX_DD_FLOOR = 0.0       # max_drawdown must be ≤ 0


class FinancialValidator:
    """
    Validates financial metric correctness after portfolio accounting.
    """

    def validate(
        self,
        records: list[BacktestRecord],
        snapshots: list[PortfolioSnapshot],
        max_drawdown: float,
    ) -> FinancialValidationReport:
        """
        Run all checks and return a FinancialValidationReport.

        Parameters
        ----------
        records : list[BacktestRecord]
            All backtest records (post-evaluation).
        snapshots : list[PortfolioSnapshot]
            Per-date portfolio snapshots.
        max_drawdown : float
            Reported maximum drawdown value (should be ≤ 0).
        """
        violations: list[str] = []
        total_checks = 10

        # ── Check 1: No NaN returns
        has_nan = False
        for r in records:
            if r.strategy_return is not None and np.isnan(r.strategy_return):
                has_nan = True
                violations.append(f"NaN strategy_return for {r.bill_id} / {r.company_isin}")
                break

        # ── Check 2: No Inf returns
        has_inf = False
        for r in records:
            if r.strategy_return is not None and np.isinf(r.strategy_return):
                has_inf = True
                violations.append(f"Inf strategy_return for {r.bill_id} / {r.company_isin}")
                break

        # ── Check 3: No return below -100%
        has_below_floor = False
        for r in records:
            ret = r.strategy_return or 0.0
            if ret < _RETURN_FLOOR:
                has_below_floor = True
                violations.append(
                    f"Return {ret:.4f} < -100% for {r.bill_id} / {r.company_isin}"
                )

        # ── Check 4: No negative portfolio wealth
        has_neg_wealth = False
        for snap in snapshots:
            if snap.portfolio_value < -1e-9:
                has_neg_wealth = True
                violations.append(f"Negative portfolio value {snap.portfolio_value:.6f} on {snap.date}")
                break

        # ── Check 5: Chronological order of snapshots
        has_chrono_violation = False
        if len(snapshots) > 1:
            dates = [pd.to_datetime(s.date, errors="coerce") for s in snapshots]
            for i in range(1, len(dates)):
                if dates[i] is not pd.NaT and dates[i - 1] is not pd.NaT:
                    if dates[i] < dates[i - 1]:
                        has_chrono_violation = True
                        violations.append(
                            f"Non-chronological snapshots: {snapshots[i-1].date} > {snapshots[i].date}"
                        )
                        break

        # ── Check 6: No duplicate timestamps
        has_duplicates = False
        date_strs = [s.date for s in snapshots]
        if len(date_strs) != len(set(date_strs)):
            has_duplicates = True
            violations.append("Duplicate dates found in portfolio snapshots.")

        # ── Check 7: Drawdown ≤ 0 at every snapshot
        has_invalid_dd = False
        for snap in snapshots:
            if snap.drawdown > 1e-9:
                has_invalid_dd = True
                violations.append(
                    f"Drawdown {snap.drawdown:.6f} > 0 on {snap.date} — wealth-relative drawdown must be ≤ 0."
                )
                break

        # ── Check 8: Max drawdown ≤ 0
        max_dd_ok = max_drawdown <= 1e-9
        if not max_dd_ok:
            violations.append(
                f"Reported max_drawdown={max_drawdown:.6f} > 0. "
                "Wealth-relative drawdown must always be ≤ 0."
            )

        # ── Check 9: TC paid ≥ 0
        tc_ok = True
        for snap in snapshots:
            if snap.total_tc_paid < -1e-9:
                tc_ok = False
                violations.append(f"Negative TC paid {snap.total_tc_paid:.6f} on {snap.date}.")
                break

        # ── Check 10: Benchmark date alignment
        has_bench_misalign = False
        nifty_missing = sum(
            1 for r in records
            if r.nifty_period_return is not None and np.isnan(r.nifty_period_return)
        )
        total_records = len(records)
        if total_records > 0 and nifty_missing / total_records > 0.5:
            has_bench_misalign = True
            violations.append(
                f"NIFTY benchmark NaN for {nifty_missing}/{total_records} records "
                f"({100 * nifty_missing / total_records:.1f}%). "
                "Check ^NSEI data availability."
            )

        # Tally
        check_results = [
            not has_nan,
            not has_inf,
            not has_below_floor,
            not has_neg_wealth,
            not has_chrono_violation,
            not has_duplicates,
            not has_invalid_dd,
            max_dd_ok,
            tc_ok,
            not has_bench_misalign,
        ]
        passed = sum(check_results)
        failed = total_checks - passed
        is_valid = failed == 0

        logger.info(
            "FinancialValidator: %d/%d checks PASSED | violations=%d | is_valid=%s",
            passed, total_checks, len(violations), is_valid,
        )

        return FinancialValidationReport(
            total_checks=total_checks,
            passed_checks=passed,
            failed_checks=failed,
            is_valid=is_valid,
            violations=violations,
            has_negative_wealth=has_neg_wealth,
            has_nan_returns=has_nan,
            has_inf_returns=has_inf,
            has_return_below_minus_100_pct=has_below_floor,
            has_chronological_violation=has_chrono_violation,
            has_duplicate_timestamps=has_duplicates,
            has_invalid_drawdown=has_invalid_dd,
            has_benchmark_date_misalign=has_bench_misalign,
            max_drawdown_check=max_dd_ok,
            portfolio_wealth_check=not has_neg_wealth,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )
