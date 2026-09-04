"""
anticipation/market_analyzer.py
===============================
Market analysis engine for Task 6.5 — Anticipation Bias Engine.

Calculates pre-event window statistics using trading-day alignment:
- Windows: [-30, -21], [-20, -11], [-10, -6], [-5, -3], [-2, -1], [-30, -1]
- Mean Abnormal Return (MAR)
- Cumulative Abnormal Return (CAR)
- Volatility of Abnormal Returns
- AR z-score using market model residual variance
- Percentage of positive / negative abnormal return trading days
- Statistical significance (t-test / z-test p-values)
"""

from __future__ import annotations

import math
from typing import Optional
import numpy as np
import pandas as pd
import scipy.stats as stats

from config.logging_config import get_logger
from config.settings import settings
from schemas.anticipation import PreEventWindowStats
from schemas.bill import Bill
from schemas.company import Company
from schemas.market_model import MarketModelRecord

logger = get_logger(__name__)


def parse_window_offsets(window_str: str) -> tuple[int, int]:
    """
    Parse a window string like '[-30,-21]' or '[-2,-1]' into (start_offset, end_offset).
    """
    clean = window_str.replace("[", "").replace("]", "").strip()
    parts = clean.split(",")
    if len(parts) != 2:
        raise ValueError(f"Invalid window string format: '{window_str}'")
    start = int(parts[0].strip())
    end = int(parts[1].strip())
    if start > end:
        raise ValueError(f"Start offset {start} must be <= end offset {end} in '{window_str}'.")
    return start, end


class PreEventMarketAnalyzer:
    """
    Computes pre-event abnormal returns and multi-window statistics.
    """

    DEFAULT_WINDOWS = [
        "[-30,-21]",
        "[-20,-11]",
        "[-10,-6]",
        "[-5,-3]",
        "[-2,-1]",
        "[-30,-1]",
    ]

    def __init__(
        self,
        windows: Optional[list[str]] = None,
        z_threshold: Optional[float] = None,
    ) -> None:
        self.windows = windows or list(self.DEFAULT_WINDOWS)
        self.z_threshold = (
            z_threshold if z_threshold is not None else settings.ANTICIPATION_Z_THRESHOLD
        )

    def analyze_company_bill(
        self,
        bill: Bill,
        company: Company,
        market_model: MarketModelRecord,
        company_returns: pd.Series,
        benchmark_returns: pd.Series,
        trading_calendar: list[str],
    ) -> dict[str, PreEventWindowStats]:
        """
        Compute pre-event abnormal return statistics across all configured windows.

        Parameters
        ----------
        bill : Bill
            The legislative bill (provides introduction_date as T0).
        company : Company
            The mapped company.
        market_model : MarketModelRecord
            Pre-estimated market model parameters (alpha, beta, residual_variance).
        company_returns : pd.Series
            Daily percentage/fractional returns for company, indexed by pd.Timestamp.
        benchmark_returns : pd.Series
            Daily percentage/fractional returns for benchmark index, indexed by pd.Timestamp.
        trading_calendar : list[str]
            Chronologically sorted list of trading day dates ('YYYY-MM-DD').

        Returns
        -------
        dict[str, PreEventWindowStats]
            Mapping of window label (e.g. '[-30,-1]') -> PreEventWindowStats.
        """
        if not bill.introduction_date:
            raise ValueError(f"Bill '{bill.bill_id}' is missing introduction_date.")

        event_date_str = bill.introduction_date.strftime("%Y-%m-%d")

        # Resolve T0 index on trading calendar (first trading date >= event_date_str)
        t0_idx = None
        for idx, d in enumerate(trading_calendar):
            if d >= event_date_str:
                t0_idx = idx
                break

        if t0_idx is None:
            raise ValueError(
                f"Bill introduction date {event_date_str} is after latest benchmark trading date."
            )

        residual_std = (
            math.sqrt(market_model.residual_variance)
            if market_model.residual_variance > 0
            else 1e-4
        )
        df_deg = max(1, market_model.n_observations - 2)

        results: dict[str, PreEventWindowStats] = {}

        for win_str in self.windows:
            start_offset, end_offset = parse_window_offsets(win_str)

            # Resolve absolute indices in trading calendar
            start_idx = t0_idx + start_offset
            end_idx = t0_idx + end_offset

            if start_idx < 0:
                logger.debug("Window %s exceeds available historical price start (start_idx=%d)", win_str, start_idx)
                start_idx = 0
            if end_idx >= t0_idx:
                # Strictly pre-event: clamp to t0_idx - 1
                end_idx = min(end_idx, t0_idx - 1)

            if start_idx > end_idx or start_idx >= len(trading_calendar):
                # Empty or invalid pre-event window
                results[win_str] = PreEventWindowStats(
                    window=win_str,
                    start_offset=start_offset,
                    end_offset=end_offset,
                    start_date="",
                    end_date="",
                    mean_abnormal_return=0.0,
                    cumulative_abnormal_return=0.0,
                    volatility=0.0,
                    ar_z_score=0.0,
                    observation_count=0,
                    pct_positive_ar=0.0,
                    pct_negative_ar=0.0,
                    daily_dates=[],
                    daily_ar=[],
                    daily_car=[],
                    is_statistically_significant=False,
                    p_value=1.0,
                )
                continue

            window_dates = trading_calendar[start_idx : end_idx + 1]
            if not window_dates:
                continue

            daily_dates: list[str] = []
            daily_ar: list[float] = []
            daily_car: list[float] = []
            running_car = 0.0

            pos_count = 0
            neg_count = 0

            for d_str in window_dates:
                dt = pd.to_datetime(d_str)
                if dt in company_returns.index and dt in benchmark_returns.index:
                    r_i = float(company_returns.loc[dt])
                    r_m = float(benchmark_returns.loc[dt])

                    if not (math.isnan(r_i) or math.isnan(r_m)):
                        exp_r = market_model.alpha + market_model.beta * r_m
                        ar = r_i - exp_r
                        running_car += ar

                        daily_dates.append(d_str)
                        daily_ar.append(ar)
                        daily_car.append(running_car)

                        if ar > 0:
                            pos_count += 1
                        elif ar < 0:
                            neg_count += 1

            n_obs = len(daily_ar)
            if n_obs > 0:
                car = running_car
                mar = float(np.mean(daily_ar))
                vol = float(np.std(daily_ar, ddof=1)) if n_obs > 1 else 0.0
                pct_pos = float(pos_count / n_obs)
                pct_neg = float(neg_count / n_obs)

                # Standard error of CAR: SE(CAR) = sqrt(N) * sigma_epsilon
                car_se = math.sqrt(n_obs) * residual_std
                z_score = float(car / car_se) if car_se > 0 else 0.0

                # Two-tailed p-value from t-distribution
                p_val = float(2.0 * stats.t.sf(abs(z_score), df_deg)) if not math.isnan(z_score) else 1.0
                p_val = max(0.0, min(1.0, p_val))
                is_sig = (abs(z_score) >= self.z_threshold) and (p_val < 0.05)

                start_date_actual = daily_dates[0] if daily_dates else window_dates[0]
                end_date_actual = daily_dates[-1] if daily_dates else window_dates[-1]
            else:
                car = 0.0
                mar = 0.0
                vol = 0.0
                pct_pos = 0.0
                pct_neg = 0.0
                z_score = 0.0
                p_val = 1.0
                is_sig = False
                start_date_actual = window_dates[0]
                end_date_actual = window_dates[-1]

            results[win_str] = PreEventWindowStats(
                window=win_str,
                start_offset=start_offset,
                end_offset=end_offset,
                start_date=start_date_actual,
                end_date=end_date_actual,
                mean_abnormal_return=mar,
                cumulative_abnormal_return=car,
                volatility=vol,
                ar_z_score=z_score,
                observation_count=n_obs,
                pct_positive_ar=pct_pos,
                pct_negative_ar=pct_neg,
                daily_dates=daily_dates,
                daily_ar=daily_ar,
                daily_car=daily_car,
                is_statistically_significant=is_sig,
                p_value=p_val,
            )

        return results
