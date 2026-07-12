"""
schemas/event_study.py
======================
Data schema for an Event Study calculation record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EventStudyRecord:
    """
    Advanced Event Study calculation record for a company-bill-window combination.
    """

    bill_id: str
    company_isin: str
    company_symbol: str
    event_date: str  # YYYY-MM-DD format
    benchmark_symbol: str
    event_window: str  # e.g., "[-5,+5]"
    dates: list[str]  # Calendar dates in the event window
    offsets: list[int]  # Relative trading day offsets (e.g. [-5, -4, ..., 5])
    expected_returns: list[float]  # Expected return for each offset
    actual_returns: list[float]  # Observed return for each offset
    daily_ar: list[float]  # Daily Abnormal Returns (AR)
    running_car: list[float]  # Running Cumulative Abnormal Returns (CAR)
    final_car: float  # Cumulative Abnormal Return at the end of the window
    avg_ar: float  # Mean AR across the window
    max_ar: float  # Max AR across the window
    min_ar: float  # Min AR across the window
    peak_ar_day: int  # Relative offset day of maximum AR
    peak_car_day: int  # Relative offset day of maximum running CAR
    observation_count: int  # Number of valid trading day observations
    market_model_id: str  # Unique identifier for the baseline market model used
    calculation_timestamp: str  # ISO-8601 timestamp

    def to_dict(self) -> dict[str, Any]:
        """Serialise the record to a dictionary."""
        return {
            "bill_id": self.bill_id,
            "company_isin": self.company_isin,
            "company_symbol": self.company_symbol,
            "event_date": self.event_date,
            "benchmark_symbol": self.benchmark_symbol,
            "event_window": self.event_window,
            "dates": self.dates,
            "offsets": self.offsets,
            "expected_returns": self.expected_returns,
            "actual_returns": self.actual_returns,
            "daily_ar": self.daily_ar,
            "running_car": self.running_car,
            "final_car": self.final_car,
            "avg_ar": self.avg_ar,
            "max_ar": self.max_ar,
            "min_ar": self.min_ar,
            "peak_ar_day": self.peak_ar_day,
            "peak_car_day": self.peak_car_day,
            "observation_count": self.observation_count,
            "market_model_id": self.market_model_id,
            "calculation_timestamp": self.calculation_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EventStudyRecord:
        """Deserialise the record from a dictionary."""
        return cls(
            bill_id=data["bill_id"],
            company_isin=data["company_isin"],
            company_symbol=data["company_symbol"],
            event_date=data["event_date"],
            benchmark_symbol=data["benchmark_symbol"],
            event_window=data["event_window"],
            dates=data["dates"],
            offsets=[int(x) for x in data["offsets"]],
            expected_returns=[float(x) for x in data["expected_returns"]],
            actual_returns=[float(x) for x in data["actual_returns"]],
            daily_ar=[float(x) for x in data["daily_ar"]],
            running_car=[float(x) for x in data["running_car"]],
            final_car=float(data["final_car"]),
            avg_ar=float(data["avg_ar"]),
            max_ar=float(data["max_ar"]),
            min_ar=float(data["min_ar"]),
            peak_ar_day=int(data["peak_ar_day"]),
            peak_car_day=int(data["peak_car_day"]),
            observation_count=int(data["observation_count"]),
            market_model_id=data["market_model_id"],
            calculation_timestamp=data["calculation_timestamp"],
        )

    def __repr__(self) -> str:
        return (
            f"<EventStudyRecord bill={self.bill_id!r} "
            f"isin={self.company_isin!r} "
            f"window={self.event_window!r} "
            f"final_car={self.final_car:.4f}>"
        )
