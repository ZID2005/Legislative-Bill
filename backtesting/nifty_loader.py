"""
backtesting/nifty_loader.py
============================
NiftyBenchmarkLoader — loads NIFTY 50 (^NSEI) period returns from persisted
daily parquet files and maps them to backtest event records (Task 6.4.1).

Design
------
* Reads ``data/market/^NSEI/{year}.parquet`` for all years spanning the event dates.
* Returns are computed as the price-relative change between the trading day that
  falls on or just after the event start date and the day that falls on or just
  before the event window end date.
* Event window string format: e.g. ``"[-5,+5]"``, ``"[-1,+1]"``, ``"[-10,+10]"``.
* If market data is unavailable for a date, returns ``np.nan`` for that event.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from config.logging_config import get_logger

logger = get_logger(__name__)

_NSEI_DIR = Path("data/market/^NSEI")


def _parse_window_days(window_str: str) -> tuple[int, int]:
    """
    Parse event window string ``"[-5,+5]"`` -> ``(-5, 5)``.

    Returns (pre_days, post_days) where post_days >= 0.
    """
    m = re.match(r"\[(-?\d+),\s*\+?(-?\d+)\]", str(window_str).strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 20  # fallback


class NiftyBenchmarkLoader:
    """
    Loads and caches NIFTY 50 daily price data and computes event-window
    period returns for benchmark comparison.

    Parameters
    ----------
    data_dir : Path, optional
        Root directory for ``^NSEI`` parquet files. Defaults to ``data/market/^NSEI``.
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir: Path = data_dir or _NSEI_DIR
        self._prices: Optional[pd.Series] = None  # cached date -> close price
        logger.debug("NiftyBenchmarkLoader initialised | dir=%s", self._data_dir)

    def _load_prices(self) -> pd.Series:
        """Load and concatenate all available ^NSEI parquet files into a date-indexed series."""
        if self._prices is not None:
            return self._prices

        if not self._data_dir.is_dir():
            logger.warning("NIFTY data directory not found: %s. Benchmark returns will be NaN.", self._data_dir)
            self._prices = pd.Series(dtype=float)
            return self._prices

        frames: list[pd.DataFrame] = []
        for fp in sorted(self._data_dir.glob("*.parquet")):
            try:
                df = pd.read_parquet(fp)
                # Normalise column names
                df.columns = [c.strip() for c in df.columns]
                close_col = next(
                    (c for c in df.columns if c.lower() in ("adjusted close", "adj close", "close")),
                    None,
                )
                date_col = next((c for c in df.columns if c.lower() == "date"), None)
                if close_col is None or date_col is None:
                    logger.warning("Skipping %s — cannot find Date/Close columns.", fp)
                    continue
                tmp = df[[date_col, close_col]].copy()
                tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
                tmp = tmp.dropna(subset=[date_col])
                tmp = tmp.set_index(date_col)[close_col]
                frames.append(tmp)
            except Exception as exc:
                logger.warning("Could not read %s: %s", fp, exc)

        if not frames:
            logger.warning("No ^NSEI parquet files readable. Benchmark returns will be NaN.")
            self._prices = pd.Series(dtype=float)
        else:
            combined = pd.concat(frames).sort_index()
            combined = combined[~combined.index.duplicated(keep="last")]
            self._prices = combined.astype(float)
            logger.info(
                "Loaded NIFTY 50 prices: %d trading days from %s to %s.",
                len(self._prices),
                self._prices.index.min().date() if len(self._prices) else "N/A",
                self._prices.index.max().date() if len(self._prices) else "N/A",
            )

        return self._prices

    def get_period_return(
        self,
        event_date: str,
        event_window: str,
    ) -> float:
        """
        Compute NIFTY 50 return over the event window centred on ``event_date``.

        Returns ``np.nan`` if prices are unavailable.

        Formula
        -------
        ``return = (P_end / P_start) - 1``

        where ``P_start`` is the close price on the trading day at or just before
        ``event_date + pre_days`` and ``P_end`` is the close on the trading day at
        or just after ``event_date + post_days``.
        """
        prices = self._load_prices()
        if prices.empty:
            return float("nan")

        pre_days, post_days = _parse_window_days(event_window)

        try:
            dt_event = pd.to_datetime(event_date)
        except Exception:
            return float("nan")

        dt_start = dt_event + pd.Timedelta(days=pre_days)
        dt_end = dt_event + pd.Timedelta(days=post_days)

        # Find nearest available trading day
        idx_arr = prices.index

        # Start price: last trading day at or before dt_start
        candidates_start = idx_arr[idx_arr <= dt_start]
        if len(candidates_start) == 0:
            candidates_start = idx_arr[idx_arr >= dt_start]
            if len(candidates_start) == 0:
                return float("nan")
        p_start = float(prices.loc[candidates_start[-1]])

        # End price: first trading day at or after dt_end
        candidates_end = idx_arr[idx_arr >= dt_end]
        if len(candidates_end) == 0:
            candidates_end = idx_arr[idx_arr <= dt_end]
            if len(candidates_end) == 0:
                return float("nan")
        p_end = float(prices.loc[candidates_end[0]])

        if p_start <= 0:
            return float("nan")

        return (p_end / p_start) - 1.0

    def get_period_returns_batch(
        self,
        event_dates: list[str],
        event_windows: list[str],
    ) -> list[float]:
        """
        Compute period returns for a list of (event_date, event_window) pairs.

        Returns
        -------
        list[float] of same length as input.
        """
        if len(event_dates) != len(event_windows):
            raise ValueError("event_dates and event_windows must have the same length.")
        return [
            self.get_period_return(date, window)
            for date, window in zip(event_dates, event_windows)
        ]

    def is_available(self) -> bool:
        """Return True if NIFTY 50 price data is accessible."""
        prices = self._load_prices()
        return len(prices) > 0
