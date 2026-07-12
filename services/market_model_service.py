"""
services/market_model_service.py
================================
Service to coordinate the estimation of expected stock returns using the market model.
"""

from __future__ import annotations

import datetime
from typing import Any, Optional
import pandas as pd

from config.logging_config import get_logger
from models.market_model_engine import estimate_ols
from schemas.bill import Bill
from schemas.company import Company
from schemas.market_model import MarketModelRecord
from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.market_model_repository import MarketModelRepository
from storage.market_repository import MarketRepository
from validation.market_model_validator import MarketModelValidator
from validation.validator import ValidationReport

logger = get_logger(__name__)


class MarketModelService:
    """
    Orchestrator service for building, validating, and persisting market models.
    """

    def __init__(
        self,
        bill_repo: Optional[BillRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        market_repo: Optional[MarketRepository] = None,
        market_model_repo: Optional[MarketModelRepository] = None,
        validator: Optional[MarketModelValidator] = None,
    ) -> None:
        self.bill_repo = bill_repo or BillRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.market_repo = market_repo or MarketRepository()
        self.market_model_repo = market_model_repo or MarketModelRepository()
        self.validator = validator or MarketModelValidator()

        # Cache for benchmark returns to avoid reloading Parquet files
        self._benchmark_returns_cache: dict[str, pd.Series] = {}

    def get_benchmark_returns(self, benchmark_symbol: str) -> pd.Series:
        """
        Retrieve and cache full returns for the benchmark.
        """
        if benchmark_symbol not in self._benchmark_returns_cache:
            logger.info("Loading and caching benchmark returns for '%s'...", benchmark_symbol)
            # Fetch all daily returns available
            returns = self.market_repo.get_daily_returns(benchmark_symbol, "1900-01-01")
            self._benchmark_returns_cache[benchmark_symbol] = returns
        return self._benchmark_returns_cache[benchmark_symbol]

    def estimate_model(
        self,
        bill: Bill,
        company: Company,
        benchmark_symbol: str = "^NSEI",
        start_offset: int = -120,
        end_offset: int = -10,
        force_refresh: bool = False,
    ) -> tuple[Optional[MarketModelRecord], ValidationReport]:
        """
        Estimate the market model for a single bill-company pair.
        """
        report = ValidationReport()

        if not force_refresh and self.market_model_repo.exists(bill.bill_id, company.isin):
            logger.debug(
                "Market model already exists for bill %s, company %s. Skipping.",
                bill.bill_id,
                company.isin,
            )
            existing = self.market_model_repo.get(bill.bill_id, company.isin)
            return existing, report

        # 1. Validate Basic inputs
        company_symbol = company.ticker_nse or company.ticker_bse or ""
        if company.ticker_nse:
            company_ticker = f"{company.ticker_nse}.NS"
        elif company.ticker_bse:
            company_ticker = f"{company.ticker_bse}.BO"
        else:
            company_ticker = ""

        # Load price DataFrames to verify existence
        benchmark_prices = self.market_repo.get_prices(benchmark_symbol, "1900-01-01")
        company_prices = (
            self.market_repo.get_prices(company_ticker, "1900-01-01")
            if company_ticker
            else pd.DataFrame()
        )

        input_report = self.validator.validate_inputs(
            company=company,
            bill=bill,
            company_prices=company_prices,
            benchmark_prices=benchmark_prices,
        )
        report.merge(input_report)
        if not report.is_valid:
            return None, report

        # Verify event date
        if bill.introduction_date is None:
            report.add_error(f"Bill '{bill.bill_id}' is missing introduction_date.")
            return None, report

        # 2. Resolve Relative Trading Day Windows
        benchmark_prices = benchmark_prices.sort_values("Date").reset_index(drop=True)
        trading_dates = benchmark_prices["Date"].tolist()
        event_date_str = bill.introduction_date.strftime("%Y-%m-%d")

        # Find nearest trading date >= event_date
        event_idx = None
        for idx, d in enumerate(trading_dates):
            if d >= event_date_str:
                event_idx = idx
                break

        if event_idx is None:
            report.add_error(
                f"Bill introduction date {event_date_str} is after latest benchmark trading date."
            )
            return None, report

        # Calculate window indices
        start_idx = event_idx + start_offset
        end_idx = event_idx + end_offset

        if start_idx < 0:
            report.add_error(
                f"Insufficient historical trading days before event (index={event_idx}). "
                f"Need at least {-start_offset} days."
            )
            return None, report

        start_date = trading_dates[start_idx]
        end_date = trading_dates[end_idx]

        # 3. Fetch Returns
        full_benchmark_returns = self.get_benchmark_returns(benchmark_symbol)
        benchmark_window_returns = full_benchmark_returns.loc[start_date:end_date]

        company_window_returns = self.market_repo.get_daily_returns(
            company_ticker, start_date, end_date
        )

        # 4. Validate Estimation Data
        data_report = self.validator.validate_estimation_data(
            company_returns=company_window_returns,
            benchmark_returns=benchmark_window_returns,
        )
        report.merge(data_report)
        if not report.is_valid:
            return None, report

        # Align series on common dates
        common_dates = company_window_returns.index.intersection(benchmark_window_returns.index)
        x = benchmark_window_returns.loc[common_dates].values
        y = company_window_returns.loc[common_dates].values

        # 5. OLS Regression
        try:
            ols_results = estimate_ols(x, y)
        except Exception as e:
            report.add_error(f"OLS Regression failed: {e}")
            return None, report

        # 6. Save Record
        record = MarketModelRecord(
            company_isin=company.isin,
            company_symbol=company_symbol,
            bill_id=bill.bill_id,
            alpha=ols_results["alpha"],
            beta=ols_results["beta"],
            r_squared=ols_results["r_squared"],
            residual_variance=ols_results["residual_variance"],
            standard_error=ols_results["standard_error"],
            beta_stderr=ols_results["beta_stderr"],
            alpha_stderr=ols_results["alpha_stderr"],
            n_observations=ols_results["n_observations"],
            estimation_window={"start_date": start_date, "end_date": end_date},
            estimation_date=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            benchmark_symbol=benchmark_symbol,
        )
        self.market_model_repo.save(record)
        return record, report

    def run_estimation(
        self,
        year: Optional[int] = None,
        bill_id_filter: Optional[str] = None,
        benchmark_symbol: str = "^NSEI",
        start_offset: int = -120,
        end_offset: int = -10,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Run the estimation pipeline for a set of bills and all active companies.
        """
        # Resolve bills
        if bill_id_filter:
            bill = self.bill_repo.get(bill_id_filter)
            bills = [bill] if bill else []
        else:
            bills = self.bill_repo.get_all()
            if year:
                bills = [b for b in bills if b.year == year]

        # Resolve active companies
        companies = [c for c in self.company_repo.get_all() if c.is_active]

        logger.info(
            "Starting Market Model estimation | bills=%d, companies=%d",
            len(bills),
            len(companies),
        )

        stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "errors": {},
        }

        for bill in bills:
            for company in companies:
                stats["processed"] += 1
                try:
                    record, report = self.estimate_model(
                        bill=bill,
                        company=company,
                        benchmark_symbol=benchmark_symbol,
                        start_offset=start_offset,
                        end_offset=end_offset,
                        force_refresh=force_refresh,
                    )
                    if not report.is_valid:
                        stats["failed"] += 1
                        key = f"{bill.bill_id}_{company.isin}"
                        stats["errors"][key] = report.errors
                    elif record is None:
                        # Skipped (already exists)
                        stats["skipped"] += 1
                    else:
                        stats["succeeded"] += 1
                except Exception as e:
                    stats["failed"] += 1
                    key = f"{bill.bill_id}_{company.isin}"
                    stats["errors"][key] = [str(e)]
                    logger.error("Error estimating model for %s - %s: %s", bill.bill_id, company.isin, e)

        return stats
