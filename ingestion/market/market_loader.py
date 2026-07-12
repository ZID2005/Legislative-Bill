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
        Supports both backward expansion and forward incremental updates.
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

        # Import Validator here
        from validation.validator import Validator

        validator = Validator()

        # Check existing data in repository
        date_range = self.market_repo.get_date_range(symbol)
        symbol_dir = self.market_repo._market_dir / symbol
        metadata_path = symbol_dir / ".earliest_sync"

        total_rows_added = 0

        if date_range and not force_refresh:
            min_date, max_date = date_range
            min_dt = datetime.datetime.strptime(min_date, "%Y-%m-%d")
            max_dt = datetime.datetime.strptime(max_date, "%Y-%m-%d")

            # Check if we need to sync backward
            needs_backward = start_dt < min_dt
            if needs_backward and metadata_path.exists():
                try:
                    earliest_sync = metadata_path.read_text().strip()
                    earliest_sync_dt = datetime.datetime.strptime(earliest_sync, "%Y-%m-%d")
                    if start_dt >= earliest_sync_dt:
                        # Already tried syncing back to at least start_dt
                        needs_backward = False
                except Exception:
                    pass

            # 1. Sync backward if needed
            if needs_backward:
                back_end_dt = min_dt - datetime.timedelta(days=1)
                back_end = back_end_dt.strftime("%Y-%m-%d")
                logger.info(
                    "Symbol '%s' has missing historical data. Syncing backward from %s to %s",
                    symbol,
                    start_date,
                    back_end,
                )
                df_back = self.download_symbol(symbol, start_date, back_end)
                if not df_back.empty:
                    report = validator.validate_market_df(df_back)
                    has_critical_error = any(
                        "Missing required column" in err or "Non-numeric" in err for err in report.errors
                    )
                    if not has_critical_error:
                        added = self.market_repo.upsert_prices(symbol, df_back)
                        total_rows_added += added
                        logger.info("Backward sync added %d rows for symbol '%s'", added, symbol)
                # Write marker to avoid re-syncing this range
                try:
                    symbol_dir.mkdir(parents=True, exist_ok=True)
                    metadata_path.write_text(start_date)
                except Exception as e:
                    logger.error("Failed to write .earliest_sync metadata: %s", e)

            # 2. Sync forward if needed
            if max_dt < end_dt:
                inc_start_dt = max_dt + datetime.timedelta(days=1)
                inc_start = inc_start_dt.strftime("%Y-%m-%d")
                logger.info(
                    "Symbol '%s' has missing forward data. Syncing forward from %s to %s",
                    symbol,
                    inc_start,
                    actual_end,
                )
                df_forward = self.download_symbol(symbol, inc_start, actual_end)
                if not df_forward.empty:
                    report = validator.validate_market_df(df_forward)
                    has_critical_error = any(
                        "Missing required column" in err or "Non-numeric" in err for err in report.errors
                    )
                    if not has_critical_error:
                        added = self.market_repo.upsert_prices(symbol, df_forward)
                        total_rows_added += added
                        logger.info("Forward sync added %d rows for symbol '%s'", added, symbol)

            if not needs_backward and max_dt >= end_dt:
                logger.info(
                    "Symbol '%s' already fully synchronized from %s to %s (existing range: %s to %s)",
                    symbol,
                    start_date,
                    actual_end,
                    min_date,
                    max_date,
                )
        else:
            # Full download or force refresh
            logger.info(
                "No existing data or force_refresh=True for symbol '%s'. Downloading full range from %s to %s",
                symbol,
                start_date,
                actual_end,
            )
            df = self.download_symbol(symbol, start_date, actual_end)
            if not df.empty:
                report = validator.validate_market_df(df)
                has_critical_error = any(
                    "Missing required column" in err or "Non-numeric" in err for err in report.errors
                )
                if not has_critical_error:
                    added = self.market_repo.upsert_prices(symbol, df)
                    total_rows_added += added
                    logger.info("Full sync added %d rows for symbol '%s'", added, symbol)
            # Write marker
            try:
                symbol_dir.mkdir(parents=True, exist_ok=True)
                metadata_path.write_text(start_date)
            except Exception as e:
                logger.error("Failed to write .earliest_sync metadata: %s", e)

        return total_rows_added

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
        import time  # noqa: PLC0415

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
                time.sleep(0.5)  # Respect rate limit
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
