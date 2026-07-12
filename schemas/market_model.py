"""
schemas/market_model.py
=======================
Data schema for a Market Model estimation record.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MarketModelRecord:
    """
    Market Model parameter estimation record for a company-bill pair.
    """

    company_isin: str
    company_symbol: str
    bill_id: str
    alpha: float
    beta: float
    r_squared: float
    residual_variance: float
    standard_error: float
    beta_stderr: float
    alpha_stderr: float
    n_observations: int
    estimation_window: dict[str, str]  # {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}
    estimation_date: str  # ISO timestamp
    benchmark_symbol: str

    def to_dict(self) -> dict[str, Any]:
        """Serialise the record to a dictionary."""
        return {
            "company_isin": self.company_isin,
            "company_symbol": self.company_symbol,
            "bill_id": self.bill_id,
            "alpha": self.alpha,
            "beta": self.beta,
            "r_squared": self.r_squared,
            "residual_variance": self.residual_variance,
            "standard_error": self.standard_error,
            "beta_stderr": self.beta_stderr,
            "alpha_stderr": self.alpha_stderr,
            "n_observations": self.n_observations,
            "estimation_window": self.estimation_window,
            "estimation_date": self.estimation_date,
            "benchmark_symbol": self.benchmark_symbol,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketModelRecord:
        """Deserialise the record from a dictionary."""
        return cls(
            company_isin=data["company_isin"],
            company_symbol=data["company_symbol"],
            bill_id=data["bill_id"],
            alpha=float(data["alpha"]),
            beta=float(data["beta"]),
            r_squared=float(data["r_squared"]),
            residual_variance=float(data["residual_variance"]),
            standard_error=float(data["standard_error"]),
            beta_stderr=float(data["beta_stderr"]),
            alpha_stderr=float(data["alpha_stderr"]),
            n_observations=int(data["n_observations"]),
            estimation_window=data["estimation_window"],
            estimation_date=data["estimation_date"],
            benchmark_symbol=data["benchmark_symbol"],
        )

    def __repr__(self) -> str:
        return (
            f"<MarketModelRecord bill_id={self.bill_id!r} "
            f"symbol={self.company_symbol!r} "
            f"beta={self.beta:.4f} "
            f"r2={self.r_squared:.4f}>"
        )
