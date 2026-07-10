"""
storage/market_repository.py
=============================
Repository for historical market price data.

This module is the **single access point** for reading and writing OHLCV
price data, index data, and derived metrics (returns).
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from config.logging_config import get_logger

logger = get_logger(__name__)


class MarketRepository:
    """
    Repository for historical OHLCV market price data and indices.
    """

    def __init__(self, market_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._market_dir = market_dir or settings.MARKET_DIR
        self._market_dir.mkdir(parents=True, exist_ok=True)
        logger.debug("MarketRepository initialised | dir=%s", self._market_dir)

    def get_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str | None = None,
        exchange: str = "NSE",
    ) -> pd.DataFrame:
        """Return OHLCV price DataFrame for a given symbol and date range."""
        symbol_dir = self._market_dir / symbol
        std_cols = ["Date", "Open", "High", "Low", "Close", "Adjusted Close", "Volume"]

        if not symbol_dir.is_dir():
            logger.debug("No price data directory found for symbol '%s'", symbol)
            return pd.DataFrame(columns=std_cols)

        # Filter years to load based on start_date and end_date to avoid reading unnecessary years
        start_year = int(start_date[:4])
        end_year = int(end_date[:4]) if end_date else 9999

        dfs = []
        for file_path in symbol_dir.glob("*.parquet"):
            try:
                year_val = int(file_path.stem)
                if start_year <= year_val <= end_year:
                    dfs.append(pd.read_parquet(file_path))
            except (ValueError, TypeError):
                dfs.append(pd.read_parquet(file_path))

        if not dfs:
            return pd.DataFrame(columns=std_cols)

        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df.sort_values("Date", inplace=True)
        combined_df.reset_index(drop=True, inplace=True)

        mask = combined_df["Date"] >= start_date
        if end_date:
            mask = mask & (combined_df["Date"] <= end_date)

        return combined_df[mask].reset_index(drop=True)

    def get_index(
        self,
        index: str = "NIFTY50",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """Return daily index values for a given benchmark."""
        index_mapping = {
            "NIFTY50": "^NSEI",
            "NIFTY 50": "^NSEI",
            "NIFTY BANK": "^NSEBANK",
            "NIFTY BANK INDEX": "^NSEBANK",
            "NIFTY IT": "^CNXIT",
            "NIFTY PHARMA": "^CNXPHARMA",
            "NIFTY AUTO": "^CNXAUTO",
            "NIFTY FMCG": "^CNXFMCG",
            "NIFTY ENERGY": "^CNXENERGY",
            "NIFTY INFRASTRUCTURE": "^CNXINFRA",
            "NIFTY INFRA": "^CNXINFRA",
        }
        symbol = index_mapping.get(index.strip().upper(), index)
        s_date = start_date or "1900-01-01"
        return self.get_prices(symbol, s_date, end_date)

    def get_daily_returns(
        self, symbol: str, start_date: str, end_date: str | None = None
    ) -> pd.Series:
        """Return daily log-returns for a given symbol."""
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        buffer_start = (start_dt - datetime.timedelta(days=45)).strftime("%Y-%m-%d")

        df = self.get_prices(symbol, buffer_start, end_date)
        if df.empty or len(df) < 2:
            return pd.Series(dtype=float)

        df["Return"] = np.log(df["Close"] / df["Close"].shift(1))
        df.dropna(subset=["Return"], inplace=True)

        mask = df["Date"] >= start_date
        if end_date:
            mask = mask & (df["Date"] <= end_date)

        filtered = df[mask]
        return pd.Series(filtered["Return"].values, index=pd.to_datetime(filtered["Date"]))

    def get_abnormal_returns(
        self,
        symbol: str,
        benchmark: str = "NIFTY50",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> object:
        """
        Return abnormal returns (actual minus expected market-model return).

        Placeholder: Implemented in Task 6.
        """
        raise NotImplementedError(
            "MarketRepository.get_abnormal_returns() — implemented in Task 6."
        )

    def get_rolling_volatility(self, symbol: str, window: int = 20) -> object:
        """
        Return rolling annualised volatility for a given symbol.

        Placeholder: Implemented in Task 7.
        """
        raise NotImplementedError(
            "MarketRepository.get_rolling_volatility() — implemented in Task 7."
        )

    def save_prices(self, symbol: str, df: pd.DataFrame) -> None:
        """Persist a price DataFrame for a symbol (full overwrite)."""
        if df.empty:
            logger.warning("Empty DataFrame provided for symbol '%s'. Skipping save.", symbol)
            return

        symbol_dir = self._market_dir / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)

        if "Date" not in df.columns:
            if df.index.name == "Date" or isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
                df.rename(columns={df.columns[0]: "Date"}, inplace=True)
            elif "date" in df.columns:
                df = df.rename(columns={"date": "Date"})
            else:
                raise ValueError("DataFrame must contain a 'Date' column or index.")

        col_mapping = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
            "adj_close": "Adjusted Close",
            "Adj Close": "Adjusted Close",
            "adjusted_close": "Adjusted Close",
        }
        df = df.rename(columns=col_mapping)

        std_cols = ["Date", "Open", "High", "Low", "Close", "Adjusted Close", "Volume"]
        for col in std_cols:
            if col not in df.columns:
                df[col] = None

        df = df[std_cols].copy()
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

        # Clean existing files to ensure full overwrite
        for file_path in symbol_dir.glob("*.parquet"):
            try:
                file_path.unlink()
            except Exception as e:
                logger.error("Failed to delete %s during full save overwrite: %s", file_path, e)

        df["Year"] = df["Date"].str.slice(0, 4)
        for year, group in df.groupby("Year"):
            year_str = str(year)
            save_group = group.drop(columns=["Year"])
            file_path = symbol_dir / f"{year_str}.parquet"
            save_group.to_parquet(file_path, index=False)

    def upsert_prices(self, symbol: str, df: pd.DataFrame) -> int:
        """Merge new price data with existing; return count of new rows added."""
        if df.empty:
            return 0

        if "Date" not in df.columns:
            if df.index.name == "Date" or isinstance(df.index, pd.DatetimeIndex):
                df = df.reset_index()
                df.rename(columns={df.columns[0]: "Date"}, inplace=True)
            elif "date" in df.columns:
                df = df.rename(columns={"date": "Date"})
            else:
                raise ValueError("DataFrame must contain a 'Date' column or index.")

        col_mapping = {
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
            "adj_close": "Adjusted Close",
            "Adj Close": "Adjusted Close",
            "adjusted_close": "Adjusted Close",
        }
        df = df.rename(columns=col_mapping)

        std_cols = ["Date", "Open", "High", "Low", "Close", "Adjusted Close", "Volume"]
        for col in std_cols:
            if col not in df.columns:
                df[col] = None
        df = df[std_cols].copy()
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")

        symbol_dir = self._market_dir / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)

        df["Year"] = df["Date"].str.slice(0, 4)
        new_rows_added = 0

        for year, group in df.groupby("Year"):
            year_str = str(year)
            file_path = symbol_dir / f"{year_str}.parquet"

            if file_path.is_file():
                existing_df = pd.read_parquet(file_path)
                existing_df["Date"] = pd.to_datetime(existing_df["Date"]).dt.strftime("%Y-%m-%d")

                existing_dates = set(existing_df["Date"])
                new_dates = set(group["Date"])
                added_dates = new_dates - existing_dates
                new_rows_added += len(added_dates)

                combined = pd.concat([existing_df, group.drop(columns=["Year"])], ignore_index=True)
                combined.drop_duplicates(subset=["Date"], keep="last", inplace=True)
                combined.sort_values("Date", inplace=True)
                combined.reset_index(drop=True, inplace=True)
            else:
                combined = group.drop(columns=["Year"]).copy()
                combined.sort_values("Date", inplace=True)
                combined.reset_index(drop=True, inplace=True)
                new_rows_added += len(combined)

            combined.to_parquet(file_path, index=False)

        return new_rows_added

    def get_available_symbols(self) -> list[str]:
        """Return list of symbols that have local price data."""
        if not self._market_dir.is_dir():
            return []
        symbols = []
        for p in self._market_dir.iterdir():
            if p.is_dir() and any(p.glob("*.parquet")):
                symbols.append(p.name)
        return sorted(symbols)

    def get_date_range(self, symbol: str) -> tuple[str, str] | None:
        """Return (min_date, max_date) of locally available data for a symbol."""
        symbol_dir = self._market_dir / symbol
        if not symbol_dir.is_dir():
            return None
        parquet_files = sorted(list(symbol_dir.glob("*.parquet")))
        if not parquet_files:
            return None

        try:
            min_df = pd.read_parquet(parquet_files[0])
            max_df = pd.read_parquet(parquet_files[-1])
            if min_df.empty or max_df.empty:
                return None
            min_date = min_df["Date"].min()
            max_date = max_df["Date"].max()
            return str(min_date), str(max_date)
        except Exception as e:
            logger.error("Failed to read date range for symbol '%s': %s", symbol, e)
            return None

    def has_data(self, symbol: str, date: str) -> bool:
        """Return True if price data exists for symbol on a specific date."""
        year_str = date[:4]
        file_path = self._market_dir / symbol / f"{year_str}.parquet"
        if not file_path.is_file():
            return False
        try:
            df = pd.read_parquet(file_path)
            return date in df["Date"].values
        except Exception:
            return False

    def __repr__(self) -> str:
        return f"<MarketRepository dir={self._market_dir!r}>"
