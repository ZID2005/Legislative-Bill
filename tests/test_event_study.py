"""
tests/test_event_study.py
==========================
Unit and integration tests for the Advanced Event Study Engine.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest

from schemas.bill import Bill, BillStatus, BillHouse
from schemas.company import Company, MarketCapCategory
from schemas.market_model import MarketModelRecord
from schemas.event_study import EventStudyRecord
from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.market_model_repository import MarketModelRepository
from storage.market_repository import MarketRepository
from storage.event_study_repository import EventStudyRepository, sanitize_window
from validation.event_study_validator import EventStudyValidator
from services.event_study_service import EventStudyService, parse_window_string


@pytest.fixture
def temp_study_dir(tmp_path: Path) -> Path:
    """Fixture for isolated event study directory."""
    d = tmp_path / "event_studies"
    d.mkdir()
    return d


@pytest.fixture
def event_study_repo(temp_study_dir: Path) -> EventStudyRepository:
    """Fixture for EventStudyRepository."""
    return EventStudyRepository(study_dir=temp_study_dir)


@pytest.fixture
def mock_company_repo(tmp_path: Path) -> CompanyRepository:
    """Fixture for isolated CompanyRepository."""
    db_file = tmp_path / "companies.json"
    repo = CompanyRepository(database_path=db_file)
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
        )
    ]
    repo._save_data(companies)
    return repo


@pytest.fixture
def mock_bill_repo(tmp_path: Path) -> BillRepository:
    """Fixture for isolated BillRepository."""
    meta_dir = tmp_path / "metadata"
    corpus_dir = tmp_path / "corpus"
    meta_dir.mkdir(parents=True)
    corpus_dir.mkdir(parents=True)
    repo = BillRepository()
    repo._meta_dir = meta_dir
    repo._corpus_dir = corpus_dir
    bill = Bill(
        bill_id="the-banking-laws-amendment-bill-2024",
        title="The Banking Laws (Amendment) Bill, 2024",
        bill_number="",
        year=2024,
        ministry="Finance",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.PASSED_BOTH,
        introduction_date=datetime.date(2024, 8, 9),
        url="https://prsindia.org/billtrack/the-banking-laws-amendment-bill-2024",
    )
    repo.save(bill)
    return repo


@pytest.fixture
def mock_market_repo(tmp_path: Path) -> MarketRepository:
    """Fixture for isolated MarketRepository."""
    market_dir = tmp_path / "market"
    repo = MarketRepository(market_dir=market_dir)

    # Add mock prices for benchmark and company
    dates = pd.date_range("2024-08-01", "2024-08-20").strftime("%Y-%m-%d").tolist()
    prices = [100.0 + idx for idx, _ in enumerate(dates)]

    # Benchmark prices
    df_mkt = pd.DataFrame(
        {
            "Date": dates,
            "Open": [p - 1 for p in prices],
            "High": [p + 1 for p in prices],
            "Low": [p - 2 for p in prices],
            "Close": prices,
            "Adjusted Close": prices,
            "Volume": [100000] * len(dates),
        }
    )
    repo.save_prices("^NSEI", df_mkt)

    # Company prices
    df_comp = pd.DataFrame(
        {
            "Date": dates,
            "Open": [p - 2 for p in prices],
            "High": [p + 2 for p in prices],
            "Low": [p - 3 for p in prices],
            "Close": [p * 1.5 for p in prices],
            "Adjusted Close": [p * 1.5 for p in prices],
            "Volume": [200000] * len(dates),
        }
    )
    repo.save_prices("RELIANCE.NS", df_comp)

    return repo


@pytest.fixture
def mock_market_model_repo(tmp_path: Path) -> MarketModelRepository:
    """Fixture for isolated MarketModelRepository."""
    model_dir = tmp_path / "market_models"
    repo = MarketModelRepository(model_dir=model_dir)
    record = MarketModelRecord(
        company_isin="INE002A01018",
        company_symbol="RELIANCE",
        bill_id="the-banking-laws-amendment-bill-2024",
        alpha=0.001,
        beta=1.2,
        r_squared=0.45,
        residual_variance=0.0001,
        standard_error=0.01,
        beta_stderr=0.05,
        alpha_stderr=0.002,
        n_observations=111,
        estimation_window={"start_date": "2024-01-01", "end_date": "2024-07-31"},
        estimation_date="2026-07-10T12:00:00Z",
        benchmark_symbol="^NSEI",
    )
    repo.save(record)
    return repo


class TestEventStudySchema:
    """Tests schema serialization and representation."""

    def test_schema_serialization_roundtrip(self):
        record = EventStudyRecord(
            bill_id="bill-123",
            company_isin="INE000A01010",
            company_symbol="TEST",
            event_date="2024-08-09",
            benchmark_symbol="^NSEI",
            event_window="[-1,+1]",
            dates=["2024-08-08", "2024-08-09", "2024-08-10"],
            offsets=[-1, 0, 1],
            expected_returns=[0.001, 0.002, 0.0015],
            actual_returns=[0.002, 0.001, 0.003],
            daily_ar=[0.001, -0.001, 0.0015],
            running_car=[0.001, 0.000, 0.0015],
            final_car=0.0015,
            avg_ar=0.0005,
            max_ar=0.0015,
            min_ar=-0.001,
            peak_ar_day=1,
            peak_car_day=1,
            observation_count=3,
            market_model_id="bill-123_INE000A01010",
            calculation_timestamp="2026-07-10T12:00:00Z",
        )

        d = record.to_dict()
        assert d["bill_id"] == "bill-123"
        assert d["final_car"] == 0.0015

        roundtrip = EventStudyRecord.from_dict(d)
        assert roundtrip.company_symbol == "TEST"
        assert roundtrip.offsets == [-1, 0, 1]
        assert repr(record) == "<EventStudyRecord bill='bill-123' isin='INE000A01010' window='[-1,+1]' final_car=0.0015>"


class TestEventStudyRepository:
    """Tests EventStudyRepository CRUD operations and filtering."""

    def test_repository_crud_and_exists(self, event_study_repo: EventStudyRepository):
        record = EventStudyRecord(
            bill_id="test-bill",
            company_isin="INE002A01018",
            company_symbol="RELIANCE",
            event_date="2024-08-09",
            benchmark_symbol="^NSEI",
            event_window="[-5,+5]",
            dates=["2024-08-09"],
            offsets=[0],
            expected_returns=[0.01],
            actual_returns=[0.02],
            daily_ar=[0.01],
            running_car=[0.01],
            final_car=0.01,
            avg_ar=0.01,
            max_ar=0.01,
            min_ar=0.01,
            peak_ar_day=0,
            peak_car_day=0,
            observation_count=1,
            market_model_id="model-1",
            calculation_timestamp="2026-07-10T12:00:00Z",
        )

        assert not event_study_repo.exists("test-bill", "INE002A01018", "[-5,+5]")

        event_study_repo.save(record)
        assert event_study_repo.exists("test-bill", "INE002A01018", "[-5,+5]")

        retrieved = event_study_repo.get("test-bill", "INE002A01018", "[-5,+5]")
        assert retrieved is not None
        assert retrieved.company_symbol == "RELIANCE"
        assert retrieved.final_car == 0.01

        # Test save_many and get_all
        record2 = EventStudyRecord(
            bill_id="test-bill",
            company_isin="INE002A01018",
            company_symbol="RELIANCE",
            event_date="2024-08-09",
            benchmark_symbol="^NSEI",
            event_window="[-1,+1]",
            dates=["2024-08-09"],
            offsets=[0],
            expected_returns=[0.01],
            actual_returns=[0.02],
            daily_ar=[0.01],
            running_car=[0.01],
            final_car=0.01,
            avg_ar=0.01,
            max_ar=0.01,
            min_ar=0.01,
            peak_ar_day=0,
            peak_car_day=0,
            observation_count=1,
            market_model_id="model-1",
            calculation_timestamp="2026-07-10T12:00:00Z",
        )
        event_study_repo.save_many([record2])

        all_records = event_study_repo.get_all()
        assert len(all_records) == 2

    def test_repository_search_filters(self, event_study_repo: EventStudyRepository):
        record1 = EventStudyRecord(
            bill_id="bill-a",
            company_isin="INE002A01018",
            company_symbol="RELIANCE",
            event_date="2024-08-09",
            benchmark_symbol="^NSEI",
            event_window="[-5,+5]",
            dates=["2024-08-09"],
            offsets=[0],
            expected_returns=[0.01],
            actual_returns=[0.02],
            daily_ar=[0.01],
            running_car=[0.01],
            final_car=0.01,
            avg_ar=0.01,
            max_ar=0.01,
            min_ar=0.01,
            peak_ar_day=0,
            peak_car_day=0,
            observation_count=1,
            market_model_id="model-1",
            calculation_timestamp="2026-07-10T12:00:00Z",
        )
        record2 = EventStudyRecord(
            bill_id="bill-b",
            company_isin="INE002A01018",
            company_symbol="RELIANCE",
            event_date="2024-08-09",
            benchmark_symbol="^NSEI",
            event_window="[-5,+5]",
            dates=["2024-08-09"],
            offsets=[0],
            expected_returns=[0.01],
            actual_returns=[0.02],
            daily_ar=[0.01],
            running_car=[0.01],
            final_car=0.01,
            avg_ar=0.01,
            max_ar=0.01,
            min_ar=0.01,
            peak_ar_day=0,
            peak_car_day=0,
            observation_count=1,
            market_model_id="model-1",
            calculation_timestamp="2026-07-10T12:00:00Z",
        )
        event_study_repo.save_many([record1, record2])

        by_bill = event_study_repo.get_by_bill("bill-a")
        assert len(by_bill) == 1
        assert by_bill[0].bill_id == "bill-a"

        by_company = event_study_repo.get_by_company("INE002A01018")
        assert len(by_company) == 2

    def test_repository_read_errors(self, temp_study_dir: Path, event_study_repo: EventStudyRepository):
        # Create a corrupted JSON file
        corrupt_file = temp_study_dir / "corrupted_file_INE123_m1_p1.json"
        with open(corrupt_file, "w") as f:
            f.write("invalid json")

        # Repository load errors should log and return None/empty
        assert event_study_repo.get("corrupted", "file", "[-1,+1]") is None
        assert len(event_study_repo.get_all()) == 0


class TestEventStudyValidator:
    """Tests Validator bounds checking and requirements."""

    def test_validate_inputs(self):
        validator = EventStudyValidator()
        company = Company(isin="INE002A01018", company_name="RIL", sector="Energy", is_active=True)
        bill = Bill(
            bill_id="test",
            title="test",
            year=2024,
            introduction_date=datetime.date(2024, 8, 9),
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://example.com"
        )

        # Missing market model
        rep = validator.validate_inputs(company, bill, None, pd.DataFrame({"Date": [1]}), pd.DataFrame({"Date": [1]}))
        assert not rep.is_valid
        assert any("Market Model missing" in err for err in rep.errors)

        # Missing prices
        model = MarketModelRecord("INE002A01018", "RIL", "test", 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1, {}, "", "")
        rep2 = validator.validate_inputs(company, bill, model, pd.DataFrame(), pd.DataFrame())
        assert not rep2.is_valid
        assert any("Company prices missing" in err for err in rep2.errors)
        assert any("Benchmark prices missing" in err for err in rep2.errors)

        # Missing introduction date
        bill_no_date = Bill(
            bill_id="test",
            title="test",
            year=2024,
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://example.com"
        )
        rep3 = validator.validate_inputs(company, bill_no_date, model, pd.DataFrame({"Date": [1]}), pd.DataFrame({"Date": [1]}))
        assert not rep3.is_valid
        assert any("missing introduction_date" in err for err in rep3.errors)

    def test_validate_event_data_bounds(self):
        validator = EventStudyValidator()

        # Overflow bounds
        rep = validator.validate_event_data(start_idx=-1, end_idx=10, total_trading_dates=100, expected_size=12, observed_company_dates=[])
        assert not rep.is_valid
        assert any("Event window incomplete" in err for err in rep.errors)

        # Insufficient observations
        rep2 = validator.validate_event_data(start_idx=1, end_idx=10, total_trading_dates=100, expected_size=10, observed_company_dates=["2024-08-01"])
        assert not rep2.is_valid
        assert any("Less than required observations" in err for err in rep2.errors)


class TestEventStudyService:
    """Tests EventStudyService calculation logic and orchestration."""

    def test_parse_window_string(self):
        assert parse_window_string("[-5,+5]") == (-5, 5)
        assert parse_window_string("[-10, 10]") == (-10, 10)
        with pytest.raises(ValueError, match="Invalid window format"):
            parse_window_string("[-5]")

    def test_run_single_study_success(
        self,
        mock_bill_repo,
        mock_company_repo,
        mock_market_repo,
        mock_market_model_repo,
        event_study_repo,
    ):
        service = EventStudyService(
            bill_repo=mock_bill_repo,
            company_repo=mock_company_repo,
            market_repo=mock_market_repo,
            market_model_repo=mock_market_model_repo,
            event_study_repo=event_study_repo,
        )

        model = mock_market_model_repo.get("the-banking-laws-amendment-bill-2024", "INE002A01018")
        record, report = service.run_single_study(model, "[-1,+1]")

        assert report.is_valid
        assert record is not None
        assert record.observation_count == 3
        # Expected return = alpha + beta * Rm
        # Daily AR = Actual Return - Expected Return
        # Check running CAR logic
        assert len(record.expected_returns) == 3
        assert len(record.daily_ar) == 3
        assert len(record.running_car) == 3
        assert record.final_car == record.running_car[-1]
        assert record.peak_ar_day in [-1, 0, 1]
        assert record.peak_car_day in [-1, 0, 1]

        # Verify record was persisted
        assert event_study_repo.exists("the-banking-laws-amendment-bill-2024", "INE002A01018", "[-1,+1]")

    def test_run_all_studies_orchestration(
        self,
        mock_bill_repo,
        mock_company_repo,
        mock_market_repo,
        mock_market_model_repo,
        event_study_repo,
    ):
        service = EventStudyService(
            bill_repo=mock_bill_repo,
            company_repo=mock_company_repo,
            market_repo=mock_market_repo,
            market_model_repo=mock_market_model_repo,
            event_study_repo=event_study_repo,
        )

        stats = service.run_all_studies(window_filter="[-1,+1],[-2,+2]")
        assert stats["processed"] == 2
        assert stats["succeeded"] == 2
        assert stats["failed"] == 0

        # Incremental skip check
        stats_inc = service.run_all_studies(window_filter="[-1,+1],[-2,+2]")
        assert stats_inc["skipped"] == 2
        assert stats_inc["succeeded"] == 0
