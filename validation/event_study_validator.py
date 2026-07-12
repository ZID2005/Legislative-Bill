"""
validation/event_study_validator.py
===================================
Validator for verifying input data quality and completeness for Event Studies.
"""

from __future__ import annotations

from typing import Any, Optional
import pandas as pd

from schemas.bill import Bill
from schemas.company import Company
from schemas.market_model import MarketModelRecord
from validation.validator import ValidationReport


class EventStudyValidator:
    """
    Validation logic for checking event-study feasibility, data sufficiency, and completeness.
    """

    def validate_inputs(
        self,
        company: Company,
        bill: Bill,
        market_model: Optional[MarketModelRecord],
        company_prices: pd.DataFrame,
        benchmark_prices: pd.DataFrame,
    ) -> ValidationReport:
        """
        Validate basic database dependencies and preconditions.
        """
        report = ValidationReport()

        if not market_model:
            report.add_error(f"Market Model missing for bill '{bill.bill_id}' and company '{company.isin}'.")

        if company_prices.empty:
            report.add_error(f"Company prices missing for ISIN '{company.isin}'.")

        if benchmark_prices.empty:
            report.add_error("Benchmark prices missing.")

        if not bill.introduction_date:
            report.add_error(f"Bill '{bill.bill_id}' is missing introduction_date.")

        return report

    def validate_event_data(
        self,
        start_idx: int,
        end_idx: int,
        total_trading_dates: int,
        expected_size: int,
        observed_company_dates: list[str],
    ) -> ValidationReport:
        """
        Validate completeness of the event window and sufficiency of company price observations.
        """
        report = ValidationReport()

        # Check if event window overflows benchmark calendar bounds
        if start_idx < 0 or end_idx >= total_trading_dates:
            report.add_error(
                f"Event window incomplete. Window bounds (indices {start_idx} to {end_idx}) "
                f"fall outside benchmark calendar range (0 to {total_trading_dates - 1})."
            )
            return report

        # Check if company has sufficient trading observations in the window
        actual_obs = len(observed_company_dates)
        if actual_obs < expected_size:
            report.add_error(
                f"Less than required observations. Event window requires {expected_size} trading days, "
                f"but company has only {actual_obs} valid trading day observations."
            )

        return report
