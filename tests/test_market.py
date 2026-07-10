"""
tests/test_market.py
====================
Unit tests for Historical Market Data Ingestion Service and Market Repository.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from ingestion.market.market_loader import MarketLoader
from schemas.company import Company, MarketCapCategory
from storage.company_repository import CompanyRepository
from storage.market_repository import MarketRepository
from validation.validator import Validator


@pytest.fixture
def temp_market_dir(tmp_path: Path) -> Path:
    """Fixture for isolated market directory."""
    d = tmp_path / "market"
    d.mkdir()
    return d


@pytest.fixture
def market_repo(temp_market_dir: Path) -> MarketRepository:
    """Fixture for isolated MarketRepository."""
    return MarketRepository(market_dir=temp_market_dir)


@pytest.fixture
def mock_company_repo(tmp_path: Path) -> CompanyRepository:
    """Fixture for isolated and populated CompanyRepository."""
    db_file = tmp_path / "companies.json"
    repo = CompanyRepository(database_path=db_file)

    # Save some mock companies
    companies = [
        Company(
            isin="INE002A01018",
            company_name="Reliance Industries Limited",
            ticker_nse="RELIANCE",
            ticker_bse="RELIANCE",
            bse_code="500325",
            sector="Energy",
            industry="Oil Gas & Fuels",
            sub_industry="Refining & Marketing",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=1800000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.ril.com",
            listing_date=None,
            is_active=True,
            listing_status="Listed",
            aliases=[],
        ),
        Company(
            isin="INE040A01034",
            company_name="HDFC Bank Limited",
            ticker_nse="",
            ticker_bse="HDFCBANK",
            bse_code="500180",
            sector="Banking",
            industry="Private Sector Bank",
            sub_industry="Commercial Banking",
            is_active=True,
            aliases=[],
        ),
        Company(
            isin="INE123A01011",
            company_name="Inactive Company",
            ticker_nse="INACTIVE",
            ticker_bse="",
            bse_code="",
            sector="Energy",
            is_active=False,
            aliases=[],
        ),
        Company(
            isin="INE000000000",
            company_name="No Ticker Company",
            ticker_nse="",
            ticker_bse="",
            bse_code="",
            sector="None",
            is_active=True,
            aliases=[],
        ),
    ]
    repo._save_data(companies)
    return repo


@pytest.fixture
def market_loader(
    market_repo: MarketRepository, mock_company_repo: CompanyRepository
) -> MarketLoader:
    """Fixture for MarketLoader with mock repos."""
    return MarketLoader(market_repository=market_repo, company_repository=mock_company_repo)


def create_mock_df(dates: list[str], prices: list[float], add_nans: bool = False) -> pd.DataFrame:
    """Helper to create standard test price DataFrame."""
    df = pd.DataFrame(
        {
            "Date": dates,
            "Open": [p - 1.0 for p in prices],
            "High": [p + 2.0 for p in prices],
            "Low": [p - 2.0 for p in prices],
            "Close": prices,
            "Adjusted Close": prices,
            "Volume": [50000.0] * len(prices),
        }
    )
    if add_nans:
        df.loc[0, "Close"] = np.nan
    return df


class TestMarketRepository:
    """Test suite for MarketRepository CRUD and derived methods."""

    def test_save_and_get_prices(self, market_repo: MarketRepository):
        dates = ["2024-01-01", "2024-01-02", "2025-01-01"]
        prices = [100.0, 101.0, 102.0]
        df = create_mock_df(dates, prices)

        # Full save
        market_repo.save_prices("MOCK_STOCK", df)

        # Retrieve all
        retrieved = market_repo.get_prices("MOCK_STOCK", "2024-01-01")
        assert len(retrieved) == 3
        assert list(retrieved["Date"]) == dates
        assert list(retrieved["Close"]) == prices

        # Range filtering
        retrieved_range = market_repo.get_prices("MOCK_STOCK", "2024-01-01", "2024-12-31")
        assert len(retrieved_range) == 2
        assert list(retrieved_range["Date"]) == ["2024-01-01", "2024-01-02"]

    def test_empty_save_handling(self, market_repo: MarketRepository):
        # Empty df
        empty_df = pd.DataFrame()
        market_repo.save_prices("MOCK_STOCK", empty_df)
        assert len(market_repo.get_available_symbols()) == 0

    def test_save_invalid_no_date(self, market_repo: MarketRepository):
        df = pd.DataFrame({"Close": [100.0]})
        with pytest.raises(ValueError, match="DataFrame must contain a 'Date' column or index"):
            market_repo.save_prices("MOCK_STOCK", df)

    def test_save_with_index_as_date(self, market_repo: MarketRepository):
        df = pd.DataFrame(
            {"Close": [100.0, 101.0]}, index=pd.to_datetime(["2024-01-01", "2024-01-02"])
        )
        df.index.name = "Date"
        market_repo.save_prices("MOCK_STOCK", df)

        res = market_repo.get_prices("MOCK_STOCK", "2024-01-01")
        assert len(res) == 2
        assert list(res["Date"]) == ["2024-01-01", "2024-01-02"]

    def test_upsert_prices(self, market_repo: MarketRepository):
        dates1 = ["2024-01-01", "2024-01-02"]
        prices1 = [100.0, 101.0]
        df1 = create_mock_df(dates1, prices1)

        # Initial upsert
        added1 = market_repo.upsert_prices("MOCK_STOCK", df1)
        assert added1 == 2

        # Upsert overlapping & new
        dates2 = ["2024-01-02", "2024-01-03"]
        prices2 = [101.5, 103.0]  # updated price for Jan 2nd
        df2 = create_mock_df(dates2, prices2)

        added2 = market_repo.upsert_prices("MOCK_STOCK", df2)
        assert added2 == 1  # only Jan 3rd is new

        # Check merged results
        retrieved = market_repo.get_prices("MOCK_STOCK", "2024-01-01")
        assert len(retrieved) == 3
        assert list(retrieved["Date"]) == ["2024-01-01", "2024-01-02", "2024-01-03"]
        # Jan 2nd should have the last updated price
        assert retrieved.loc[retrieved["Date"] == "2024-01-02", "Close"].values[0] == 101.5

    def test_get_index(self, market_repo: MarketRepository):
        dates = ["2024-01-01", "2024-01-02"]
        prices = [22000.0, 22100.0]
        df = create_mock_df(dates, prices)

        market_repo.save_prices("^NSEI", df)

        # Test index lookup using human name
        res = market_repo.get_index("NIFTY50", "2024-01-01")
        assert len(res) == 2
        assert res.loc[0, "Close"] == 22000.0

    def test_get_daily_returns(self, market_repo: MarketRepository):
        dates = ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
        prices = [100.0, 102.0, 101.0, 103.0]
        df = create_mock_df(dates, prices)
        market_repo.save_prices("MOCK_STOCK", df)

        returns = market_repo.get_daily_returns("MOCK_STOCK", "2024-01-02")
        assert len(returns) == 3
        # log return Jan 2nd = ln(102/100) = 0.0198
        assert np.isclose(returns.iloc[0], np.log(102.0 / 100.0))
        # log return Jan 3rd = ln(101/102) = -0.0098
        assert np.isclose(returns.iloc[1], np.log(101.0 / 102.0))

    def test_metadata_helpers(self, market_repo: MarketRepository):
        assert market_repo.get_date_range("MOCK_STOCK") is None
        assert not market_repo.has_data("MOCK_STOCK", "2024-01-01")

        dates = ["2024-01-01", "2024-01-05"]
        prices = [100.0, 105.0]
        df = create_mock_df(dates, prices)
        market_repo.save_prices("MOCK_STOCK", df)

        assert market_repo.get_available_symbols() == ["MOCK_STOCK"]
        assert market_repo.get_date_range("MOCK_STOCK") == ("2024-01-01", "2024-01-05")
        assert market_repo.has_data("MOCK_STOCK", "2024-01-01")
        assert not market_repo.has_data("MOCK_STOCK", "2024-01-02")

    def test_derived_methods_not_implemented(self, market_repo: MarketRepository):
        with pytest.raises(NotImplementedError):
            market_repo.get_abnormal_returns("MOCK_STOCK")
        with pytest.raises(NotImplementedError):
            market_repo.get_rolling_volatility("MOCK_STOCK")


class TestMarketValidator:
    """Test suite for Validator market dataframe validation."""

    def test_validate_valid_market_df(self):
        validator = Validator()
        dates = ["2024-01-01", "2024-01-02", "2024-01-03"]
        prices = [100.0, 101.0, 102.0]
        df = create_mock_df(dates, prices)

        report = validator.validate_market_df(df)
        assert report.is_valid
        assert len(report.errors) == 0

    def test_validate_none_and_invalid_type(self):
        validator = Validator()
        assert "DataFrame is None" in validator.validate_market_df(None).errors
        assert any(
            "Input is not a pandas DataFrame" in err
            for err in validator.validate_market_df("not_a_df").errors
        )
        assert "DataFrame is empty" in validator.validate_market_df(pd.DataFrame()).warnings

    def test_validate_missing_columns(self):
        validator = Validator()
        df = pd.DataFrame({"Close": [100.0]})
        report = validator.validate_market_df(df)
        assert not report.is_valid
        assert any("Missing required column" in err for err in report.errors)

    def test_validate_duplicate_dates(self):
        validator = Validator()
        df = create_mock_df(["2024-01-01", "2024-01-01"], [100.0, 101.0])
        report = validator.validate_market_df(df)
        assert not report.is_valid
        assert any("Duplicate row for date" in err for err in report.errors)

    def test_validate_invalid_and_negative_prices(self):
        validator = Validator()
        # Non-numeric
        df_invalid = create_mock_df(["2024-01-01"], [100.0])
        df_invalid["Close"] = df_invalid["Close"].astype(object)
        df_invalid.loc[0, "Close"] = "invalid_price"
        report = validator.validate_market_df(df_invalid)
        assert not report.is_valid
        assert any("Non-numeric value in column" in err for err in report.errors)

        # Negative price
        df_neg = create_mock_df(["2024-01-01"], [-5.0])
        report_neg = validator.validate_market_df(df_neg)
        assert not report_neg.is_valid
        assert any("Negative or zero price in column" in err for err in report_neg.errors)

        # Negative volume
        df_vol = create_mock_df(["2024-01-01"], [100.0])
        df_vol.loc[0, "Volume"] = -100
        report_vol = validator.validate_market_df(df_vol)
        assert not report_vol.is_valid
        assert any("Negative volume in column" in err for err in report_vol.errors)

        # Missing values
        df_nan = create_mock_df(["2024-01-01"], [100.0], add_nans=True)
        report_nan = validator.validate_market_df(df_nan)
        assert not report_nan.is_valid
        assert any("Missing value in column" in err for err in report_nan.errors)

    def test_validate_gaps_in_dates(self):
        validator = Validator()
        # 10 days gap
        df = create_mock_df(["2024-01-01", "2024-01-11"], [100.0, 101.0])
        report = validator.validate_market_df(df)
        assert report.is_valid  # gaps are warnings, not blocking errors
        assert len(report.warnings) == 1
        assert "Potential gap in trading days" in report.warnings[0]


class TestMarketLoader:
    """Test suite for MarketLoader yfinance integration and incremental sync."""

    def test_resolve_tickers(self, market_loader: MarketLoader):
        comp_nse = Company(
            isin="1",
            company_name="C1",
            ticker_nse="RELIANCE",
            ticker_bse="",
            bse_code="",
            sector="",
        )
        comp_bse = Company(
            isin="2",
            company_name="C2",
            ticker_nse="",
            ticker_bse="HDFCBANK",
            bse_code="500180",
            sector="",
        )
        comp_bse_code = Company(
            isin="3", company_name="C3", ticker_nse="", ticker_bse="", bse_code="500123", sector=""
        )
        comp_none = Company(
            isin="4", company_name="C4", ticker_nse="", ticker_bse="", bse_code="", sector=""
        )

        assert market_loader.resolve_ticker(comp_nse) == "RELIANCE.NS"
        assert market_loader.resolve_ticker(comp_bse) == "HDFCBANK.BO"
        assert market_loader.resolve_ticker(comp_bse_code) == "500123.BO"
        assert market_loader.resolve_ticker(comp_none) is None

    @patch("yfinance.Ticker")
    def test_download_symbol_success(self, mock_ticker, market_loader: MarketLoader):
        # Set up mock yfinance output
        mock_instance = MagicMock()
        dates = pd.to_datetime(["2024-01-01", "2024-01-02"])
        mock_hist = pd.DataFrame(
            {
                "Open": [99.0, 100.0],
                "High": [102.0, 103.0],
                "Low": [98.0, 99.0],
                "Close": [100.0, 101.0],
                "Adj Close": [100.0, 101.0],
                "Volume": [1000.0, 1100.0],
            },
            index=dates,
        )
        mock_hist.index.name = "Date"
        mock_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_instance

        df = market_loader.download_symbol("RELIANCE.NS", "2024-01-01", "2024-01-02")
        assert len(df) == 2
        assert list(df["Date"]) == ["2024-01-01", "2024-01-02"]
        assert list(df["Adjusted Close"]) == [100.0, 101.0]

    @patch("yfinance.Ticker")
    def test_download_symbol_empty_or_failure(self, mock_ticker, market_loader: MarketLoader):
        mock_instance = MagicMock()
        mock_instance.history.return_value = pd.DataFrame()
        mock_ticker.return_value = mock_instance

        df = market_loader.download_symbol("EMPTY", "2024-01-01")
        assert df.empty

        # Test failure
        mock_instance.history.side_effect = Exception("API Error")
        df_fail = market_loader.download_symbol("FAIL", "2024-01-01")
        assert df_fail.empty

    @patch("yfinance.Ticker")
    def test_sync_symbol_new_vs_existing(
        self, mock_ticker, market_loader: MarketLoader, market_repo: MarketRepository
    ):
        mock_instance = MagicMock()

        # Scenario 1: No existing data (full sync)
        dates1 = pd.to_datetime(["2024-01-01", "2024-01-02"])
        mock_hist1 = pd.DataFrame(
            {
                "Open": [99.0, 100.0],
                "High": [102.0, 103.0],
                "Low": [98.0, 99.0],
                "Close": [100.0, 101.0],
                "Adj Close": [100.0, 101.0],
                "Volume": [1000, 1100],
            },
            index=dates1,
        )
        mock_hist1.index.name = "Date"
        mock_instance.history.return_value = mock_hist1
        mock_ticker.return_value = mock_instance

        rows_added = market_loader.sync_symbol("RELIANCE.NS", "2024-01-01")
        assert rows_added == 2

        # Verify in repo
        assert market_repo.get_date_range("RELIANCE.NS") == ("2024-01-01", "2024-01-02")

        # Scenario 2: Incremental sync (data exists up to 2024-01-02, sync up to 2024-01-03)
        dates2 = pd.to_datetime(["2024-01-03"])
        mock_hist2 = pd.DataFrame(
            {
                "Open": [101.0],
                "High": [104.0],
                "Low": [100.0],
                "Close": [102.0],
                "Adj Close": [102.0],
                "Volume": [1200],
            },
            index=dates2,
        )
        mock_hist2.index.name = "Date"
        mock_instance.history.return_value = mock_hist2

        # Sync with end_date Jan 3rd
        rows_added_inc = market_loader.sync_symbol("RELIANCE.NS", "2024-01-01", "2024-01-03")
        assert rows_added_inc == 1

        # Check call parameters (start="2024-01-03", i.e. max_date + 1 day)
        mock_instance.history.assert_called_with(
            start="2024-01-03", end="2024-01-03", interval="1d", auto_adjust=False
        )

        assert market_repo.get_date_range("RELIANCE.NS") == ("2024-01-01", "2024-01-03")

    @patch("yfinance.Ticker")
    def test_sync_all_and_cli_orchestration(self, mock_ticker, market_loader: MarketLoader):
        # Mock yfinance return
        mock_instance = MagicMock()
        dates = pd.to_datetime(["2024-01-01"])
        mock_hist = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [102.0],
                "Low": [98.0],
                "Close": [101.0],
                "Adj Close": [101.0],
                "Volume": [1000],
            },
            index=dates,
        )
        mock_hist.index.name = "Date"
        mock_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_instance

        # Sync only index
        stats = market_loader.sync_all(start_date="2024-01-01", index_only=True)
        # Should have synced the 8 supported index symbols
        assert stats["processed"] == 8
        assert stats["succeeded"] == 8
        assert stats["failed"] == 0

        # Sync with symbol filter
        stats_filtered = market_loader.sync_all(
            start_date="2024-01-01", symbol_filter="^NSEI,RELIANCE.NS"
        )
        assert stats_filtered["processed"] == 2

    @patch("yfinance.Ticker")
    def test_additional_market_coverage(
        self,
        mock_ticker,
        market_loader: MarketLoader,
        market_repo: MarketRepository,
        temp_market_dir: Path,
    ):
        # 1. Sync symbol start_date > end_date
        added = market_loader.sync_symbol("RELIANCE.NS", "2024-01-02", "2024-01-01")
        assert added == 0

        # 2. Sync symbol already up-to-date
        df = create_mock_df(["2024-01-01"], [100.0])
        market_repo.save_prices("RELIANCE.NS", df)
        added_up_to_date = market_loader.sync_symbol("RELIANCE.NS", "2024-01-01", "2024-01-01")
        assert added_up_to_date == 0

        # 3. Download symbol with no date column
        mock_instance = MagicMock()
        mock_hist_no_date = pd.DataFrame({"Close": [100.0]})
        mock_hist_no_date.index.name = "Unknown"
        mock_instance.history.return_value = mock_hist_no_date
        mock_ticker.return_value = mock_instance
        df_no_date = market_loader.download_symbol("NODATE", "2024-01-01")
        assert df_no_date.empty

        # 3b. Download symbol with lowercase date column
        mock_hist_lc = pd.DataFrame(
            {"Open": [100.0], "High": [100.0], "Low": [100.0], "Close": [100.0], "Volume": [1000]},
            index=["2024-01-01"],
        )
        mock_hist_lc.index.name = "date"
        mock_instance.history.return_value = mock_hist_lc
        df_lc = market_loader.download_symbol("LOWERCASE", "2024-01-01")
        assert len(df_lc) == 1
        assert "Date" in df_lc.columns

        # 4. Sync symbol validation critical error (Volume is non-numeric)
        dates = ["2024-01-01"]
        mock_hist_nan = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [100.0],
                "Low": [100.0],
                "Close": [100.0],
                "Adj Close": [100.0],
                "Volume": ["invalid_vol"],
            },
            index=pd.to_datetime(dates),
        )
        mock_hist_nan.index.name = "Date"
        mock_instance.history.return_value = mock_hist_nan

        rows_added_invalid = market_loader.sync_symbol("INVALID_CO", "2024-01-01")
        assert rows_added_invalid == 0

        # 5. Sync symbol exception caught
        with patch.object(market_loader, "download_symbol", side_effect=Exception("API Error")):
            stats_all_error = market_loader.sync_all(start_date="2024-01-01", symbol_filter="^NSEI")
            assert stats_all_error["failed"] == 1
            assert "^NSEI" in stats_all_error["errors"]

        # 5b. Sync all with inactive company and index_only=False
        stats_all = market_loader.sync_all(start_date="2024-01-01", index_only=False)
        assert stats_all["processed"] > 0

        # 6. Repository get_prices with no directory
        res_no_dir = market_repo.get_prices("NON_EXISTENT", "2024-01-01")
        assert res_no_dir.empty

        # 6b. Repository get_prices with no parquet files in directory
        empty_dir = temp_market_dir / "EMPTY_DIR"
        empty_dir.mkdir(parents=True, exist_ok=True)
        res_empty_dir = market_repo.get_prices("EMPTY_DIR", "2024-01-01")
        assert res_empty_dir.empty

        # 6c. Repository get_prices with year_val conversion ValueError (invalid file name)
        symbol_dir = temp_market_dir / "RELIANCE.NS"
        symbol_dir.mkdir(parents=True, exist_ok=True)
        df_valid = create_mock_df(["2024-01-01"], [100.0])
        df_valid.to_parquet(symbol_dir / "invalid_name.parquet")
        res_invalid_stem = market_repo.get_prices("RELIANCE.NS", "2024-01-01")
        assert len(res_invalid_stem) > 0

        # 7. Repository get_index with unmapped index name
        df_unmapped = create_mock_df(["2024-01-01"], [100.0])
        market_repo.save_prices("UNMAPPED", df_unmapped)
        res_unmapped = market_repo.get_index("UNMAPPED", "2024-01-01")
        assert len(res_unmapped) == 1

        # 8. Repository save_prices unlinking exception
        with patch.object(Path, "unlink", side_effect=OSError("Permission Denied")):
            market_repo.save_prices("RELIANCE.NS", df_valid)

        # 9. Repository upsert_prices with Date as index
        df_idx = create_mock_df(["2024-01-01"], [100.0])
        df_idx.set_index("Date", inplace=True)
        added_idx = market_repo.upsert_prices("RELIANCE.NS", df_idx)
        assert added_idx == 0

        # 9b. Repository upsert_prices with lowercase date column
        df_lc_col = pd.DataFrame({"date": ["2024-01-05"], "Close": [100.0]})
        added_lc_col = market_repo.upsert_prices("RELIANCE.NS", df_lc_col)
        assert added_lc_col == 1

        # 9c. Repository upsert_prices with no Date raises ValueError
        df_no_d = pd.DataFrame({"Close": [100.0]})
        with pytest.raises(ValueError, match="DataFrame must contain a 'Date'"):
            market_repo.upsert_prices("RELIANCE.NS", df_no_d)

        # 9d. Repository upsert_prices missing some standard columns (will fill with None)
        df_missing_col = pd.DataFrame({"Date": ["2024-01-06"], "Close": [100.0]})
        added_missing = market_repo.upsert_prices("RELIANCE.NS", df_missing_col)
        assert added_missing == 1

        # 10. Repository get_available_symbols when dir is not a directory
        non_existent_repo = MarketRepository(market_dir=temp_market_dir / "NON_EXISTENT")
        assert non_existent_repo.get_available_symbols() == []

        # 10b. Repository get_date_range when empty directory or empty dataframe
        assert market_repo.get_date_range("EMPTY_DIR") is None
        empty_parquet_df = pd.DataFrame(columns=["Date", "Close"])
        empty_parquet_df.to_parquet(empty_dir / "2024.parquet")
        assert market_repo.get_date_range("EMPTY_DIR") is None

        # 10c. Repository get_date_range exception handling
        with open(symbol_dir / "2024.parquet", "w") as f:
            f.write("corrupted")
        assert market_repo.get_date_range("RELIANCE.NS") is None

        # 10d. Repository has_data exception handling
        assert not market_repo.has_data("RELIANCE.NS", "2024-01-01")

        try:
            (symbol_dir / "2024.parquet").unlink()
        except Exception:
            pass
