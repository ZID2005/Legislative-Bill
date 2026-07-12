"""
validation/market_model_validator.py
====================================
Data validation for Market Model estimations.
"""

from __future__ import annotations

from typing import Any
import pandas as pd

from validation.validator import ValidationReport


class MarketModelValidator:
    """
    Validator to enforce data completeness and statistical validity on Market Model estimations.
    """

    def validate_inputs(
        self,
        company: Any | None,
        bill: Any | None,
        company_prices: pd.DataFrame | None,
        benchmark_prices: pd.DataFrame | None,
    ) -> ValidationReport:
        """
        Validate data inputs before running regression.
        """
        report = ValidationReport()

        if company is None:
            report.add_error("Company is missing.")
        if bill is None:
            report.add_error("Bill is missing.")

        if benchmark_prices is None or benchmark_prices.empty:
            report.add_error("Benchmark price data is missing or empty.")
        if company_prices is None or company_prices.empty:
            report.add_error("Company price data is missing or empty.")

        return report

    def validate_estimation_data(
        self,
        company_returns: pd.Series,
        benchmark_returns: pd.Series,
    ) -> ValidationReport:
        """
        Validate overlapping returns series before running regression.
        """
        report = ValidationReport()

        # Find overlapping dates
        common_idx = company_returns.index.intersection(benchmark_returns.index)
        n_obs = len(common_idx)

        if n_obs < 60:
            report.add_error(
                f"Fewer than 60 overlapping trading observations exist (got {n_obs})."
            )

        if n_obs >= 2:
            # Check for zero variance in benchmark returns
            x_var = benchmark_returns.loc[common_idx].var()
            if x_var < 1e-9 or pd.isna(x_var):
                report.add_error("Benchmark returns variance is zero; regression cannot be run.")

        return report
