"""
schemas/market.py
=================
Typed data models for market price records.

Two models are defined:

*  ``PriceRecord`` — a single OHLCV row for one symbol on one date.
*  ``EventWindow`` — the set of price records around a bill event date,
   used as input to the label generator (Task 6).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class PriceRecord:
    """
    A single daily OHLCV price record.

    Attributes
    ----------
    symbol : str
        NSE or BSE ticker symbol.
    date : date
        Trading date.
    open : float
        Opening price.
    high : float
        Intraday high.
    low : float
        Intraday low.
    close : float
        Closing price.
    adj_close : float
        Adjusted closing price (accounts for splits, dividends).
    volume : int
        Total shares traded.
    daily_return : float | None
        Log return: ln(close_t / close_{t-1}).  Populated by market_loader.
    """

    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int
    daily_return: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "date": self.date.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "adj_close": self.adj_close,
            "volume": self.volume,
            "daily_return": self.daily_return,
        }

    def __repr__(self) -> str:
        return f"<PriceRecord symbol={self.symbol!r} date={self.date} " f"close={self.close:.2f}>"


@dataclass
class EventWindow:
    """
    Price records surrounding a bill event date, used for event study.

    Attributes
    ----------
    bill_id : str
        The bill this event window belongs to.
    isin : str
        The company this event window belongs to.
    event_date : date
        T=0 (bill introduction or notification date).
    estimation_window : list[PriceRecord]
        Pre-event data used to fit the market model (T-120 to T-11).
    event_window : list[PriceRecord]
        Data over which CAR is computed (T-1 to T+60 typically).
    benchmark_returns : dict[str, float]
        Market (Nifty 50) daily returns keyed by ISO date string.
        Used for computing expected returns in the market model.
    """

    bill_id: str
    isin: str
    event_date: date
    estimation_window: list[PriceRecord]
    event_window: list[PriceRecord]
    benchmark_returns: dict[str, float]

    def __repr__(self) -> str:
        return (
            f"<EventWindow bill_id={self.bill_id!r} isin={self.isin!r} "
            f"event_date={self.event_date} "
            f"est_days={len(self.estimation_window)} evt_days={len(self.event_window)}>"
        )
