"""
ingestion/market/market_loader.py
================================
Historical market data loader using Yahoo Finance (yfinance).
"""

from __future__ import annotations

import datetime
from typing import Any, Optional

import pandas as pd
import yfinance as yf

from config.logging_config import get_logger
from storage.company_repository import CompanyRepository
from storage.market_repository import MarketRepository

logger = get_logger(__name__)


class MarketLoader:
    """
    Historical market data loader for equities and indices.
    """

    # Supported indices mapping (Index name -> yfinance ticker)
    SUPPORTED_INDICES = {
        "NIFTY 50": "^NSEI",
        "NIFTY Bank": "^NSEBANK",
        "NIFTY IT": "^CNXIT",
        "NIFTY Pharma": "^CNXPHARMA",
        "NIFTY Auto": "^CNXAUTO",
        "NIFTY FMCG": "^CNXFMCG",
        "NIFTY Energy": "^CNXENERGY",
        "NIFTY Infrastructure": "^CNXINFRA",
    }

    def __init__(
        self,
        market_repository: Optional[MarketRepository] = None,
        company_repository: Optional[CompanyRepository] = None,
    ) -> None:
        self.market_repo = market_repository or MarketRepository()
        self.company_repo = company_repository or CompanyRepository()
        logger.debug("MarketLoader initialised")

    def resolve_ticker(self, company: Any) -> Optional[str]:
        """
        Resolve the yfinance ticker for a given company.
        Prefers NSE ticker with '.NS' suffix, falls back to BSE with '.BO'.
        """
        if company.ticker_nse and company.ticker_nse.strip():
            return f"{company.ticker_nse.strip().upper()}.NS"
        if company.ticker_bse and company.ticker_bse.strip():
            # If ticker_bse is numeric (BSE code), use that. Otherwise use symbol.
            ticker = company.ticker_bse.strip().upper()
            return f"{ticker}.BO"
        if company.bse_code and company.bse_code.strip():
            return f"{company.bse_code.strip()}.BO"
        return None

    def download_symbol(
        self, symbol: str, start_date: str, end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Download daily historical OHLCV data from Yahoo Finance and normalize it.
        """
        std_cols = ["Date", "Open", "High", "Low", "Close", "Adjusted Close", "Volume"]
        try:
            logger.info(
                "Downloading historical data for symbol '%s' from %s to %s",
                symbol,
                start_date,
                end_date or "present",
            )

            # yfinance expects end_date to be exclusive.
            # If end_date is today, passing it as string is fine.
            ticker = yf.Ticker(symbol)
            hist = ticker.history(
                start=start_date,
                end=end_date,
                interval="1d",
                auto_adjust=False,
            )

            if hist.empty:
                logger.warning("No data returned from yfinance for symbol '%s'", symbol)
                return pd.DataFrame(columns=std_cols)

            # Reset index to get Date column
            df = hist.reset_index()

            # Normalize column names
            # Find the date column
            date_col = None
            for col in df.columns:
                if col.lower() in ["date", "datetime"]:
                    date_col = col
                    break

            if date_col is None:
                logger.error("Could not find Date column in yfinance output for '%s'", symbol)
                return pd.DataFrame(columns=std_cols)

            df = df.rename(columns={date_col: "Date"})
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

            # Map Adj Close to Adjusted Close
            col_mapping = {
                "Open": "Open",
                "High": "High",
                "Low": "Low",
                "Close": "Close",
                "Volume": "Volume",
                "Adj Close": "Adjusted Close",
                "adj_close": "Adjusted Close",
                "adjusted_close": "Adjusted Close",
            }
            df = df.rename(columns=col_mapping)

            if "Adjusted Close" not in df.columns:
                # If Adj Close not returned, copy Close
                df["Adjusted Close"] = df["Close"]

            # Retain only required columns
            for col in std_cols:
                if col not in df.columns:
                    df[col] = None

            df = df[std_cols].copy()
            # Drop rows where Close is missing
            df.dropna(subset=["Close"], inplace=True)
            df.sort_values("Date", inplace=True)
            df.reset_index(drop=True, inplace=True)

            return df
        except Exception as e:
            logger.error("Failed to download data for symbol '%s': %s", symbol, e)
            return pd.DataFrame(columns=std_cols)

    def sync_symbol(
        self,
        symbol: str,
        start_date: str,
        end_date: Optional[str] = None,
        force_refresh: bool = False,
    ) -> int:
        """
        Incrementally sync historical data for a symbol.
        Checks existing data range and only downloads missing dates.
        """
        # Determine actual end date
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        actual_end = end_date or today_str

        # Parse dates to compare
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(actual_end, "%Y-%m-%d")

        if start_dt > end_dt:
            logger.warning(
                "Start date %s is after end date %s. Skipping symbol %s.",
                start_date,
                actual_end,
                symbol,
            )
            return 0

        # Check existing data in repository
        date_range = self.market_repo.get_date_range(symbol)

        if date_range and not force_refresh:
            min_date, max_date = date_range
            max_dt = datetime.datetime.strptime(max_date, "%Y-%m-%d")

            # Check if we already have data up to the requested end date
            if max_dt >= end_dt:
                logger.info(
                    "Symbol '%s' already up-to-date (data exists up to %s)", symbol, max_date
                )
                return 0

            # Incremental start date is max_date + 1 day
            inc_start_dt = max_dt + datetime.timedelta(days=1)
            inc_start = inc_start_dt.strftime("%Y-%m-%d")

            logger.info(
                "Symbol '%s' has existing data up to %s. Performing incremental sync from %s",
                symbol,
                max_date,
                inc_start,
            )
            df = self.download_symbol(symbol, inc_start, actual_end)
        else:
            logger.info(
                "No existing data or force_refresh=True for symbol '%s'. "
                "Downloading full range from %s",
                symbol,
                start_date,
            )
            df = self.download_symbol(symbol, start_date, actual_end)

        if df.empty:
            return 0

        # Validate before upserting
        from validation.validator import Validator

        validator = Validator()
        report = validator.validate_market_df(df)
        if not report.is_valid:
            logger.error(
                "Validation failed for downloaded data of symbol '%s': %s", symbol, report.errors
            )
            # Skip if there are actual schema errors, warning is okay.
            has_critical_error = any(
                "Missing required column" in err or "Non-numeric" in err for err in report.errors
            )
            if has_critical_error:
                logger.error(
                    "Skipping save for symbol '%s' due to critical validation errors.", symbol
                )
                return 0

        new_rows = self.market_repo.upsert_prices(symbol, df)
        logger.info("Upserted %d new rows for symbol '%s'", new_rows, symbol)
        return new_rows

    def sync_all(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        symbol_filter: Optional[str] = None,
        index_only: bool = False,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Sync all supported assets (indices and active companies).
        """
        targets = []

        # 1. Resolve Indices
        indices_list = list(self.SUPPORTED_INDICES.values())
        if symbol_filter:
            filter_symbols = {s.strip().upper() for s in symbol_filter.split(",")}
            # Keep only indices in filter
            targets.extend([idx for idx in indices_list if idx.upper() in filter_symbols])
        else:
            targets.extend(indices_list)

        # 2. Resolve Companies
        if not index_only:
            companies = self.company_repo.get_all()
            for comp in companies:
                if not comp.is_active:
                    continue
                symbol = self.resolve_ticker(comp)
                if not symbol:
                    logger.warning(
                        "Could not resolve ticker for company: %s (ISIN: %s)",
                        comp.company_name,
                        comp.isin,
                    )
                    continue

                if symbol_filter:
                    if (
                        symbol.upper() in filter_symbols
                        or comp.ticker_nse.upper() in filter_symbols
                    ):
                        targets.append(symbol)
                else:
                    targets.append(symbol)

        logger.info("Resolved %d targets to sync", len(targets))

        # Perform sync
        stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "rows_added": 0,
            "errors": {},
        }

        for symbol in targets:
            stats["processed"] += 1
            try:
                rows = self.sync_symbol(symbol, start_date, end_date, force_refresh)
                stats["succeeded"] += 1
                stats["rows_added"] += rows
            except Exception as e:
                logger.exception("Failed to sync symbol '%s'", symbol)
                stats["failed"] += 1
                stats["errors"][symbol] = str(e)

        logger.info(
            "Sync completed | succeeded=%d failed=%d total_rows_added=%d",
            stats["succeeded"],
            stats["failed"],
            stats["rows_added"],
        )
        return stats
