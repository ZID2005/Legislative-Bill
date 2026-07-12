"""
services/event_study_service.py
================================
Service to coordinate calculations for the Advanced Event Study Engine.
"""

from __future__ import annotations

import datetime
from typing import Any, Optional
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from schemas.bill import Bill
from schemas.company import Company
from schemas.market_model import MarketModelRecord
from schemas.event_study import EventStudyRecord
from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.market_model_repository import MarketModelRepository
from storage.market_repository import MarketRepository
from storage.event_study_repository import EventStudyRepository
from validation.event_study_validator import EventStudyValidator
from validation.validator import ValidationReport

logger = get_logger(__name__)


def parse_window_string(win_str: str) -> tuple[int, int]:
    """Parse a window string like '[-5,+5]' into (start_offset, end_offset)."""
    clean = win_str.replace("[", "").replace("]", "").strip()
    parts = clean.split(",")
    if len(parts) != 2:
        raise ValueError(f"Invalid window format: {win_str}")
    start = int(parts[0].strip())
    end = int(parts[1].strip())
    return start, end


class EventStudyService:
    """
    Orchestrator service for computing, validating, and persisting event studies.
    """

    DEFAULT_WINDOWS = ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"]

    def __init__(
        self,
        bill_repo: Optional[BillRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        market_repo: Optional[MarketRepository] = None,
        market_model_repo: Optional[MarketModelRepository] = None,
        event_study_repo: Optional[EventStudyRepository] = None,
        validator: Optional[EventStudyValidator] = None,
    ) -> None:
        self.bill_repo = bill_repo or BillRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.market_repo = market_repo or MarketRepository()
        self.market_model_repo = market_model_repo or MarketModelRepository()
        self.event_study_repo = event_study_repo or EventStudyRepository()
        self.validator = validator or EventStudyValidator()

        # Cache returns to avoid reloading Parquet files
        self._benchmark_returns_cache: dict[str, pd.Series] = {}
        self._company_returns_cache: dict[str, pd.Series] = {}

    def get_benchmark_returns(self, benchmark_symbol: str) -> pd.Series:
        """Retrieve and cache full returns for the benchmark."""
        if benchmark_symbol not in self._benchmark_returns_cache:
            returns = self.market_repo.get_daily_returns(benchmark_symbol, "1900-01-01")
            self._benchmark_returns_cache[benchmark_symbol] = returns
        return self._benchmark_returns_cache[benchmark_symbol]

    def get_company_returns(self, company_ticker: str) -> pd.Series:
        """Retrieve and cache full returns for a company."""
        if company_ticker not in self._company_returns_cache:
            returns = self.market_repo.get_daily_returns(company_ticker, "1900-01-01")
            self._company_returns_cache[company_ticker] = returns
        return self._company_returns_cache[company_ticker]

    def run_single_study(
        self,
        market_model: MarketModelRecord,
        event_window: str,
        force_refresh: bool = False,
    ) -> tuple[Optional[EventStudyRecord], ValidationReport]:
        """
        Run event study for a single market model record and window.
        """
        report = ValidationReport()

        if not force_refresh and self.event_study_repo.exists(
            market_model.bill_id, market_model.company_isin, event_window
        ):
            logger.debug(
                "Event study already exists for bill %s, company %s, window %s. Skipping.",
                market_model.bill_id,
                market_model.company_isin,
                event_window,
            )
            existing = self.event_study_repo.get(
                market_model.bill_id, market_model.company_isin, event_window
            )
            return existing, report

        # 1. Load entities
        bill = self.bill_repo.get(market_model.bill_id)
        if not bill:
            report.add_error(f"Bill '{market_model.bill_id}' not found in repository.")
            return None, report

        company = self.company_repo.get_by_isin(market_model.company_isin)
        if not company:
            report.add_error(f"Company '{market_model.company_isin}' not found in repository.")
            return None, report

        # 2. Get tickers & prices to check existence
        company_symbol = company.ticker_nse or company.ticker_bse or ""
        if company.ticker_nse:
            company_ticker = f"{company.ticker_nse.strip().upper()}.NS"
        elif company.ticker_bse:
            company_ticker = f"{company.ticker_bse.strip().upper()}.BO"
        else:
            company_ticker = ""

        benchmark_prices = self.market_repo.get_prices(market_model.benchmark_symbol, "1900-01-01")
        company_prices = (
            self.market_repo.get_prices(company_ticker, "1900-01-01")
            if company_ticker
            else pd.DataFrame()
        )

        # Validate inputs
        input_report = self.validator.validate_inputs(
            company=company,
            bill=bill,
            market_model=market_model,
            company_prices=company_prices,
            benchmark_prices=benchmark_prices,
        )
        report.merge(input_report)
        if not report.is_valid:
            return None, report

        # 3. Calendar Resolution
        benchmark_prices = benchmark_prices.sort_values("Date").reset_index(drop=True)
        trading_dates = benchmark_prices["Date"].tolist()
        event_date_str = bill.introduction_date.strftime("%Y-%m-%d")

        # Resolve nearest trading date >= event_date
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

        # 4. Resolve Window offsets
        try:
            start_offset, end_offset = parse_window_string(event_window)
        except Exception as e:
            report.add_error(str(e))
            return None, report

        start_idx = event_idx + start_offset
        end_idx = event_idx + end_offset

        # Retrieve full returns
        full_benchmark_returns = self.get_benchmark_returns(market_model.benchmark_symbol)
        full_company_returns = self.get_company_returns(company_ticker)

        # Get window dates
        if start_idx >= 0 and end_idx < len(trading_dates):
            window_dates = trading_dates[start_idx : end_idx + 1]
        else:
            window_dates = []

        # Reindex returns to align on the expected event window dates
        benchmark_window_returns = full_benchmark_returns.reindex(pd.to_datetime(window_dates))
        company_window_returns = full_company_returns.reindex(pd.to_datetime(window_dates))

        # Check for missing benchmark returns
        if not window_dates or benchmark_window_returns.isna().any():
            report.add_error("Benchmark returns are missing/incomplete for dates in the event window.")
            return None, report

        # Validate event data completeness and company observation sufficiency
        observed_company_dates = (
            company_window_returns.dropna().index.strftime("%Y-%m-%d").tolist()
        )
        data_report = self.validator.validate_event_data(
            start_idx=start_idx,
            end_idx=end_idx,
            total_trading_dates=len(trading_dates),
            expected_size=len(window_dates),
            observed_company_dates=observed_company_dates,
        )
        report.merge(data_report)
        if not report.is_valid:
            return None, report

        # 5. Core Computations
        expected_returns = []
        actual_returns = []
        daily_ar = []
        running_car = []

        current_car = 0.0

        for d_str in window_dates:
            dt = pd.to_datetime(d_str)
            act_r = float(company_window_returns.loc[dt])
            mkt_r = float(benchmark_window_returns.loc[dt])

            exp_r = market_model.alpha + market_model.beta * mkt_r
            ar = act_r - exp_r
            current_car += ar

            expected_returns.append(exp_r)
            actual_returns.append(act_r)
            daily_ar.append(ar)
            running_car.append(current_car)

        # Quality Metrics
        avg_ar = float(np.mean(daily_ar))
        max_ar = float(np.max(daily_ar))
        min_ar = float(np.min(daily_ar))

        offsets = list(range(start_offset, end_offset + 1))
        peak_ar_idx = int(np.argmax(daily_ar))
        peak_car_idx = int(np.argmax(running_car))

        peak_ar_day = offsets[peak_ar_idx]
        peak_car_day = offsets[peak_car_idx]

        # 6. Save Record
        record = EventStudyRecord(
            bill_id=bill.bill_id,
            company_isin=company.isin,
            company_symbol=company_symbol,
            event_date=event_date_str,
            benchmark_symbol=market_model.benchmark_symbol,
            event_window=event_window,
            dates=window_dates,
            offsets=offsets,
            expected_returns=expected_returns,
            actual_returns=actual_returns,
            daily_ar=daily_ar,
            running_car=running_car,
            final_car=current_car,
            avg_ar=avg_ar,
            max_ar=max_ar,
            min_ar=min_ar,
            peak_ar_day=peak_ar_day,
            peak_car_day=peak_car_day,
            observation_count=len(daily_ar),
            market_model_id=f"{bill.bill_id}_{company.isin}",
            calculation_timestamp=datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        )

        self.event_study_repo.save(record)
        return record, report

    def run_all_studies(
        self,
        year: Optional[int] = None,
        bill_id_filter: Optional[str] = None,
        company_isin_filter: Optional[str] = None,
        window_filter: Optional[str] = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Run event studies for all combinations matching the filters.
        """
        models = self.market_model_repo.get_all()

        # Filter models
        filtered_models = []
        for m in models:
            if bill_id_filter and m.bill_id != bill_id_filter:
                continue
            if company_isin_filter and m.company_isin != company_isin_filter:
                continue
            if year:
                bill = self.bill_repo.get(m.bill_id)
                if not bill or bill.year != year:
                    continue
            filtered_models.append(m)

        # Resolve windows to process
        if window_filter:
            import re
            windows = re.findall(r'\[[-+\d\s,]+\]', window_filter)
        else:
            windows = self.DEFAULT_WINDOWS

        logger.info(
            "Starting Event Study Engine | models=%d, windows=%d",
            len(filtered_models),
            len(windows),
        )

        stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "errors": {},
        }

        for model in filtered_models:
            for win in windows:
                stats["processed"] += 1
                try:
                    # Check if exists and force_refresh is False to increment skipped count
                    if not force_refresh and self.event_study_repo.exists(
                        model.bill_id, model.company_isin, win
                    ):
                        stats["skipped"] += 1
                        continue

                    record, report = self.run_single_study(model, win, force_refresh)
                    if report.is_valid and record:
                        stats["succeeded"] += 1
                    else:
                        stats["failed"] += 1
                        key = f"{model.bill_id}_{model.company_isin}_{win}"
                        stats["errors"][key] = report.errors
                except Exception as e:
                    stats["failed"] += 1
                    key = f"{model.bill_id}_{model.company_isin}_{win}"
                    stats["errors"][key] = [str(e)]

        logger.info(
            "Event Study completed | processed=%d succeeded=%d failed=%d skipped=%d",
            stats["processed"],
            stats["succeeded"],
            stats["failed"],
            stats["skipped"],
        )
        return stats
