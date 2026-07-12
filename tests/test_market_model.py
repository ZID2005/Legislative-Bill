"""
tests/test_market_model.py
==========================
Unit tests for Market Model return calculations, OLS math, validator, repository, and service.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest

from models.market_model_engine import calculate_returns, estimate_ols
from schemas.bill import Bill, BillStatus, BillHouse
from schemas.company import Company
from schemas.market_model import MarketModelRecord
from storage.market_model_repository import MarketModelRepository
from validation.market_model_validator import MarketModelValidator
from services.market_model_service import MarketModelService
from validation.validator import ValidationReport


@pytest.fixture
def temp_model_dir(tmp_path: Path) -> Path:
    d = tmp_path / "market_models"
    d.mkdir()
    return d


@pytest.fixture
def market_model_repo(temp_model_dir: Path) -> MarketModelRepository:
    return MarketModelRepository(model_dir=temp_model_dir)


class TestMarketModelEngine:
    """Test returns calculations and OLS math."""

    def test_calculate_returns_log(self):
        prices = pd.Series([100.0, 102.0, 101.0, 104.0])
        returns = calculate_returns(prices, method="log")
        assert len(returns) == 3
        expected = np.log(prices / prices.shift(1)).dropna()
        pd.testing.assert_series_equal(returns, expected)

    def test_calculate_returns_simple(self):
        prices = pd.Series([100.0, 102.0, 101.0, 104.0])
        returns = calculate_returns(prices, method="simple")
        assert len(returns) == 3
        expected = ((prices - prices.shift(1)) / prices.shift(1)).dropna()
        pd.testing.assert_series_equal(returns, expected)

    def test_calculate_returns_invalid_method(self):
        prices = pd.Series([100.0, 102.0])
        with pytest.raises(ValueError, match="Unknown return calculation method"):
            calculate_returns(prices, method="unknown")

    def test_calculate_returns_empty_and_short(self):
        assert calculate_returns(pd.Series(dtype=float)).empty
        assert calculate_returns(pd.Series([100.0])).empty

    def test_estimate_ols_exact(self):
        x = np.array([0.01, 0.02, -0.01, 0.03, 0.00])
        alpha_true = 0.005
        beta_true = 1.2
        y = alpha_true + beta_true * x

        res = estimate_ols(x, y)
        assert pytest.approx(res["alpha"]) == alpha_true
        assert pytest.approx(res["beta"]) == beta_true
        assert pytest.approx(res["r_squared"]) == 1.0
        assert res["residual_variance"] < 1e-15
        assert res["standard_error"] < 1e-15
        assert res["n_observations"] == 5

    def test_estimate_ols_errors(self):
        # n < 3
        with pytest.raises(ValueError, match="At least 3 observations are required"):
            estimate_ols(np.array([1, 2]), np.array([1, 2]))

        # zero variance of x
        with pytest.raises(ValueError, match="Independent variable .* has zero variance"):
            estimate_ols(np.array([1, 1, 1]), np.array([1, 2, 3]))

        # constant y should result in r_squared = 0.0
        x = np.array([1, 2, 3])
        y = np.array([5, 5, 5])
        res = estimate_ols(x, y)
        assert res["r_squared"] == 0.0


class TestMarketModelRepository:
    """Test MarketModelRepository CRUD."""

    def test_crud_operations(self, market_model_repo: MarketModelRepository):
        record = MarketModelRecord(
            company_isin="INE001A01001",
            company_symbol="MOCK",
            bill_id="mock-bill-2024",
            alpha=0.001,
            beta=1.1,
            r_squared=0.25,
            residual_variance=0.0004,
            standard_error=0.02,
            beta_stderr=0.15,
            alpha_stderr=0.005,
            n_observations=110,
            estimation_window={"start_date": "2024-01-01", "end_date": "2024-06-01"},
            estimation_date="2026-07-10T12:00:00Z",
            benchmark_symbol="^NSEI",
        )

        # Save
        assert not market_model_repo.exists("mock-bill-2024", "INE001A01001")
        market_model_repo.save(record)
        assert market_model_repo.exists("mock-bill-2024", "INE001A01001")
        assert market_model_repo.count() == 1

        # Get
        fetched = market_model_repo.get("mock-bill-2024", "INE001A01001")
        assert fetched is not None
        assert fetched.company_symbol == "MOCK"
        assert fetched.beta == 1.1

        # Get non-existent
        assert market_model_repo.get("non-existent", "INE001A01001") is None

        # Representation
        assert repr(fetched) == "<MarketModelRecord bill_id='mock-bill-2024' symbol='MOCK' beta=1.1000 r2=0.2500>"

        # Get by bill and company
        by_bill = market_model_repo.get_by_bill("mock-bill-2024")
        assert len(by_bill) == 1
        assert by_bill[0].company_isin == "INE001A01001"

        by_company = market_model_repo.get_by_company("INE001A01001")
        assert len(by_company) == 1

        # Save many
        record2 = MarketModelRecord(
            company_isin="INE001A01002",
            company_symbol="MOCK2",
            bill_id="mock-bill-2024",
            alpha=0.002,
            beta=0.9,
            r_squared=0.35,
            residual_variance=0.0003,
            standard_error=0.017,
            beta_stderr=0.12,
            alpha_stderr=0.004,
            n_observations=110,
            estimation_window={"start_date": "2024-01-01", "end_date": "2024-06-01"},
            estimation_date="2026-07-10T12:00:00Z",
            benchmark_symbol="^NSEI",
        )
        market_model_repo.save_many([record2])
        assert market_model_repo.count() == 2

        # Get all
        all_records = market_model_repo.get_all()
        assert len(all_records) == 2

        # Delete
        market_model_repo.delete("mock-bill-2024", "INE001A01001")
        assert not market_model_repo.exists("mock-bill-2024", "INE001A01001")
        assert market_model_repo.count() == 1

    def test_repository_read_errors(self, market_model_repo: MarketModelRepository, temp_model_dir: Path):
        # Corrupt file
        with open(temp_model_dir / "corrupted_record.json", "w") as f:
            f.write("corrupted json")

        # get should return None on load failure
        assert market_model_repo.get("corrupted", "record") is None
        # get_all should skip the corrupted record and not crash
        assert len(market_model_repo.get_all()) == 0

    def test_repository_list_and_count_errors(self, market_model_repo: MarketModelRepository):
        with patch("storage.market_model_repository.list_files", side_effect=Exception("mocked fs error")):
            assert len(market_model_repo.get_all()) == 0
            assert market_model_repo.count() == 0


class TestMarketModelValidator:
    """Test MarketModelValidator constraints."""

    def test_validate_inputs(self):
        validator = MarketModelValidator()
        company = Company(
            isin="INE001A01001",
            company_name="Mock Company",
            sector="Technology",
            ticker_nse="MOCK",
            ticker_bse="",
            is_active=True,
            hq_state="Maharashtra",
        )
        bill = Bill(
            bill_id="mock-bill",
            title="Mock Title",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://example.com",
            bill_number="123/2024",
            year=2024,
            ministry="Ministry of Finance",
            introduction_date=datetime.date(2024, 1, 1),
        )

        # Valid inputs
        idx_prices = pd.DataFrame({"Date": ["2024-01-01"], "Close": [100.0]})
        co_prices = pd.DataFrame({"Date": ["2024-01-01"], "Close": [50.0]})
        report = validator.validate_inputs(company, bill, co_prices, idx_prices)
        assert report.is_valid

        # Missing entities
        report_miss = validator.validate_inputs(None, None, None, None)
        assert not report_miss.is_valid
        assert "Company is missing." in report_miss.errors
        assert "Bill is missing." in report_miss.errors
        assert "Benchmark price data is missing or empty." in report_miss.errors
        assert "Company price data is missing or empty." in report_miss.errors

    def test_validate_estimation_data(self):
        validator = MarketModelValidator()

        # Under 60 observations
        co_ret = pd.Series([0.01] * 50, index=pd.date_range("2024-01-01", periods=50))
        idx_ret = pd.Series([0.02] * 50, index=pd.date_range("2024-01-01", periods=50))
        report_short = validator.validate_estimation_data(co_ret, idx_ret)
        assert not report_short.is_valid
        assert "Fewer than 60 overlapping trading observations exist" in report_short.errors[0]

        # Zero variance of benchmark
        co_ret_long = pd.Series([0.01] * 100, index=pd.date_range("2024-01-01", periods=100))
        idx_ret_zero_var = pd.Series([0.02] * 100, index=pd.date_range("2024-01-01", periods=100))
        report_zero_var = validator.validate_estimation_data(co_ret_long, idx_ret_zero_var)
        assert not report_zero_var.is_valid
        assert "Benchmark returns variance is zero" in report_zero_var.errors[0]


class TestMarketModelService:
    """Test MarketModelService orchestration and date window resolution."""

    @patch("services.market_model_service.MarketRepository")
    @patch("services.market_model_service.CompanyRepository")
    @patch("services.market_model_service.BillRepository")
    def test_estimate_model_success(self, mock_bill_repo, mock_comp_repo, mock_market_repo, market_model_repo):
        # Mock repositories
        bill = Bill(
            bill_id="test-bill-2024",
            title="Test Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://example.com",
            bill_number="1/2024",
            year=2024,
            ministry="Ministry of Finance",
            introduction_date=datetime.date(2024, 6, 20),
        )
        company = Company(
            isin="INE001A01001",
            company_name="Mock Company",
            sector="Technology",
            ticker_nse="MOCK",
            ticker_bse="",
            is_active=True,
            hq_state="Maharashtra",
        )

        # Create mock price histories with 200 trading days
        dates = [d.strftime("%Y-%m-%d") for d in pd.date_range("2024-01-01", periods=200, freq="B")]
        # Event date "2024-06-20" falls on index ~ 122 in trading dates
        benchmark_prices = pd.DataFrame({
            "Date": dates,
            "Close": [1000.0 + idx * 2.0 for idx, _ in enumerate(dates)],
            "Open": [1000.0] * 200,
            "High": [1000.0] * 200,
            "Low": [1000.0] * 200,
            "Volume": [1000] * 200,
            "Adjusted Close": [1000.0] * 200,
        })
        company_prices = pd.DataFrame({
            "Date": dates,
            "Close": [100.0 + idx * 0.5 for idx, _ in enumerate(dates)],
            "Open": [100.0] * 200,
            "High": [100.0] * 200,
            "Low": [100.0] * 200,
            "Volume": [1000] * 200,
            "Adjusted Close": [100.0] * 200,
        })

        mock_market_repo_inst = MagicMock()
        # Mock get_prices
        def mock_get_prices(symbol, start, end=None):
            if "^NSEI" in symbol:
                return benchmark_prices
            return company_prices
        mock_market_repo_inst.get_prices.side_effect = mock_get_prices

        # Mock get_daily_returns with varying series to avoid zero variance
        def mock_get_daily_returns(symbol, start_date, end_date=None):
            if "^NSEI" in symbol:
                return pd.Series(
                    [0.01 if idx % 2 == 0 else -0.01 for idx in range(200)],
                    index=pd.to_datetime(dates)
                )
            else:
                x = np.array([0.01 if idx % 2 == 0 else -0.01 for idx in range(200)])
                y = 1.2 * x
                return pd.Series(y, index=pd.to_datetime(dates))

        mock_market_repo_inst.get_daily_returns.side_effect = mock_get_daily_returns

        service = MarketModelService(
            bill_repo=mock_bill_repo,
            company_repo=mock_comp_repo,
            market_repo=mock_market_repo_inst,
            market_model_repo=market_model_repo,
        )

        # Run OLS model estimation
        record, report = service.estimate_model(bill, company, force_refresh=True)
        assert report.is_valid
        assert record is not None
        assert record.company_symbol == "MOCK"
        assert pytest.approx(record.beta) == 1.2
        assert record.r_squared == 1.0
        assert record.n_observations == 111  # inclusive range -120 to -10

        # Incremental sync check: run again without force_refresh, should return existing
        record_inc, report_inc = service.estimate_model(bill, company, force_refresh=False)
        assert report_inc.is_valid
        assert record_inc == record
        assert market_model_repo.count() == 1

    @patch("services.market_model_service.MarketRepository")
    @patch("services.market_model_service.CompanyRepository")
    @patch("services.market_model_service.BillRepository")
    def test_estimate_model_failures(self, mock_bill_repo, mock_comp_repo, mock_market_repo, market_model_repo):
        # 1. Event date is missing
        bill_no_date = Bill(
            bill_id="test-bill-2024",
            title="Test Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://example.com",
            bill_number="1/2024",
            year=2024,
            ministry="Ministry of Finance",
            introduction_date=None,
        )
        company = Company(
            isin="INE001A01001",
            company_name="Mock Company",
            sector="Technology",
            ticker_nse="MOCK",
            ticker_bse="",
            is_active=True,
            hq_state="Maharashtra",
        )
        service = MarketModelService(
            bill_repo=mock_bill_repo,
            company_repo=mock_comp_repo,
            market_repo=mock_market_repo,
            market_model_repo=market_model_repo,
        )

        # Mock market prices as valid to bypass input validator
        mock_market_repo.get_prices.return_value = pd.DataFrame({"Date": ["2024-01-01"], "Close": [100.0]})

        record, report = service.estimate_model(bill_no_date, company, force_refresh=True)
        assert not report.is_valid
        assert "is missing introduction_date." in report.errors[0]

        # 2. Event date is after available trading dates
        bill_future = Bill(
            bill_id="test-bill-2024",
            title="Test Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://example.com",
            bill_number="1/2024",
            year=2024,
            ministry="Ministry of Finance",
            introduction_date=datetime.date(2025, 1, 1),
        )
        # Mock available dates to only have 2024
        mock_market_repo.get_prices.return_value = pd.DataFrame({
            "Date": ["2024-01-01", "2024-01-02"], "Close": [100.0, 101.0]
        })
        record, report_future = service.estimate_model(bill_future, company, force_refresh=True)
        assert not report_future.is_valid
        assert "is after latest benchmark trading date." in report_future.errors[0]

        # 3. Insufficient history
        bill_early = Bill(
            bill_id="test-bill-2024",
            title="Test Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://example.com",
            bill_number="1/2024",
            year=2024,
            ministry="Ministry of Finance",
            introduction_date=datetime.date(2024, 1, 10),
        )
        dates = [d.strftime("%Y-%m-%d") for d in pd.date_range("2024-01-01", periods=20, freq="B")]
        mock_market_repo.get_prices.return_value = pd.DataFrame({
            "Date": dates, "Close": [100.0] * 20
        })
        record, report_early = service.estimate_model(bill_early, company, force_refresh=True)
        assert not report_early.is_valid
        assert "Insufficient historical trading days before event" in report_early.errors[0]

    @patch("services.market_model_service.MarketRepository")
    @patch("services.market_model_service.CompanyRepository")
    @patch("services.market_model_service.BillRepository")
    def test_run_estimation_orchestration(self, mock_bill_repo, mock_comp_repo, mock_market_repo, market_model_repo):
        # Mock repositories output
        bill = Bill(
            bill_id="test-bill-2024",
            title="Test Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://example.com",
            bill_number="1/2024",
            year=2024,
            ministry="Ministry of Finance",
            introduction_date=datetime.date(2024, 6, 20),
        )
        company1 = Company(isin="INE001A01001", company_name="C1", sector="Technology", ticker_nse="M1", ticker_bse="", is_active=True, hq_state="M")
        company2 = Company(isin="INE001A01002", company_name="C2", sector="Technology", ticker_nse="M2", ticker_bse="", is_active=True, hq_state="M")
        company_inactive = Company(isin="INE001A01003", company_name="C3", sector="Technology", ticker_nse="M3", ticker_bse="", is_active=False, hq_state="M")

        mock_bill_repo.get_all.return_value = [bill]
        mock_comp_repo.get_all.return_value = [company1, company2, company_inactive]

        service = MarketModelService(
            bill_repo=mock_bill_repo,
            company_repo=mock_comp_repo,
            market_repo=mock_market_repo,
            market_model_repo=market_model_repo,
        )

        # Mock estimate_model
        mock_estimate = MagicMock()
        mock_estimate.return_value = (MagicMock(), ValidationReport())
        service.estimate_model = mock_estimate

        # Run batch estimation
        stats = service.run_estimation(year=2024)
        assert stats["processed"] == 2
        assert stats["succeeded"] == 2
        assert stats["failed"] == 0

    @patch("services.market_model_service.MarketRepository")
    @patch("services.market_model_service.CompanyRepository")
    @patch("services.market_model_service.BillRepository")
    def test_run_estimation_extra_paths(self, mock_bill_repo, mock_comp_repo, mock_market_repo, market_model_repo):
        # 1. Test company with bse_ticker only and no nse_ticker
        company_bse = Company(isin="INE001A01004", company_name="C4", sector="Technology", ticker_nse="", ticker_bse="MOCKBSE", is_active=True, hq_state="M")
        # 2. Test company with no tickers
        company_none = Company(isin="INE001A01005", company_name="C5", sector="Technology", ticker_nse="", ticker_bse="", is_active=True, hq_state="M")

        bill = Bill(
            bill_id="test-bill-2024",
            title="Test Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://example.com",
            bill_number="1/2024",
            year=2024,
            ministry="Ministry of Finance",
            introduction_date=datetime.date(2024, 6, 20),
        )

        mock_bill_repo.get.return_value = bill
        mock_comp_repo.get_all.return_value = [company_bse, company_none]

        service = MarketModelService(
            bill_repo=mock_bill_repo,
            company_repo=mock_comp_repo,
            market_repo=mock_market_repo,
            market_model_repo=market_model_repo,
        )

        # Test bill_id filter branch and tickers branches
        stats = service.run_estimation(bill_id_filter="test-bill-2024")
        # Since tickers are empty/invalid, it should fail validation and log as failed
        assert stats["processed"] == 2
        assert stats["failed"] == 2

        # 3. Test duplicate skipping (skipped stat increment) and exception handling
        mock_estimate = MagicMock()
        # First call returns None (skipped), second call raises Exception (failed)
        mock_estimate.side_effect = [(None, ValidationReport()), Exception("regression error")]
        service.estimate_model = mock_estimate

        stats2 = service.run_estimation(bill_id_filter="test-bill-2024")
        assert stats2["skipped"] == 1
        assert stats2["failed"] == 1
