import os
import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from schemas.company import Company, MarketCapCategory
from ingestion.companies.company_loader import CompanyLoader
from storage.company_repository import CompanyRepository
from validation.validator import Validator, ValidationReport


def test_company_schema_serialization():
    # Verify Company schema serialization and deserialization
    c = Company(
        isin="INE002A01018",
        company_name="Reliance Industries Limited",
        sector="Energy",
        ticker_nse="RELIANCE",
        ticker_bse="RELIANCE",
        bse_code="500325",
        industry="Oil Gas & Fuels",
        sub_industry="Refining & Marketing",
        market_cap_category=MarketCapCategory.LARGE_CAP,
        market_cap_cr=1800000.0,
        hq_state="Maharashtra",
        hq_city="Mumbai",
        website="https://www.ril.com",
        listing_status="Listed",
    )

    data = c.to_dict()
    assert data["isin"] == "INE002A01018"
    assert data["company_name"] == "Reliance Industries Limited"
    assert data["sub_industry"] == "Refining & Marketing"
    assert data["hq_state"] == "Maharashtra"
    assert data["website"] == "https://www.ril.com"
    assert data["listing_status"] == "Listed"

    deserialized = Company.from_dict(data)
    assert deserialized.isin == c.isin
    assert deserialized.company_name == c.company_name
    assert deserialized.sub_industry == c.sub_industry
    assert deserialized.hq_state == c.hq_state
    assert deserialized.website == c.website
    assert deserialized.listing_status == c.listing_status


def test_company_normalization():
    loader = CompanyLoader()

    # Name normalization test
    assert loader.normalize_company_name("RELIANCE INDUSTRIES LTD") == "Reliance Industries Limited"
    assert (
        loader.normalize_company_name("tata consultancy services limited")
        == "Tata Consultancy Services Limited"
    )
    assert loader.normalize_company_name("HDFC BANK PVT LTD") == "HDFC Bank Private Limited"
    assert loader.normalize_company_name("INFOSYS CO.") == "Infosys Company"

    # State normalization test
    assert loader.normalize_state("mah") == "Maharashtra"
    assert loader.normalize_state("mumbai") == "Maharashtra"
    assert loader.normalize_state("BANGALORE") == "Karnataka"
    assert loader.normalize_state("kar") == "Karnataka"
    assert loader.normalize_state("delhi") == "Delhi"
    assert loader.normalize_state("new delhi") == "Delhi"
    assert loader.normalize_state("haryana") == "Haryana"


def test_company_validation():
    v = Validator()

    # 1. Valid Company
    valid_c = Company(
        isin="INE002A01018",
        company_name="Reliance Industries Limited",
        sector="Energy",
        hq_state="Maharashtra",
        website="https://www.ril.com",
    )
    report = v.validate_company(valid_c)
    assert report.is_valid
    assert len(report.errors) == 0

    # 2. Missing Name
    invalid_c = Company(isin="INE002A01018", company_name="", sector="Energy")
    report = v.validate_company(invalid_c)
    assert not report.is_valid
    assert "Missing company name" in report.errors

    # 3. Missing Sector
    warn_c = Company(isin="INE002A01018", company_name="Reliance", sector="")
    report = v.validate_company(warn_c)
    assert report.is_valid  # Sector is warning only
    assert "Missing sector" in report.warnings

    # 4. Invalid Website
    bad_web = Company(
        isin="INE002A01018", company_name="Reliance", sector="Energy", website="www.ril.com"
    )
    report = v.validate_company(bad_web)
    assert not report.is_valid
    assert "Invalid website" in report.errors[0]

    # 5. Invalid State
    bad_state = Company(
        isin="INE002A01018", company_name="Reliance", sector="Energy", hq_state="California"
    )
    report = v.validate_company(bad_state)
    assert not report.is_valid
    assert "Invalid state" in report.errors[0]

    # 6. Invalid input type
    report = v.validate_company(12345)
    assert not report.is_valid
    assert "Invalid company input type" in report.errors[0]


def test_companies_list_duplicate_validation():
    v = Validator()

    c1 = Company(
        isin="INE002A01018", company_name="Reliance", sector="Energy", ticker_nse="RELIANCE"
    )
    c2 = Company(isin="INE467B01029", company_name="TCS", sector="Technology", ticker_nse="TCS")

    # Valid unique list
    report = v.validate_companies_list([c1, c2])
    assert report.is_valid

    # Duplicate ISIN
    c3 = Company(
        isin="INE002A01018", company_name="Reliance Dupe", sector="Energy", ticker_nse="REL-DUPE"
    )
    report = v.validate_companies_list([c1, c2, c3])
    assert not report.is_valid
    assert any("Duplicate ISIN detected" in err for err in report.errors)

    # Duplicate Symbol
    c4 = Company(
        isin="INE999A01019", company_name="TCS Dupe", sector="Technology", ticker_nse="TCS"
    )
    report = v.validate_companies_list([c1, c2, c4])
    assert not report.is_valid
    assert any("Duplicate NSE symbol detected" in err for err in report.errors)

    # Dictionary validation
    d1 = {
        "isin": "INE123",
        "company_name": "Dict Company",
        "sector": "Energy",
        "ticker_nse": "DICT",
    }
    d2 = {
        "isin": "INE123",
        "company_name": "Dict Company 2",
        "sector": "Energy",
        "ticker_nse": "DICT2",
    }
    report = v.validate_companies_list([d1, d2])
    assert not report.is_valid
    assert any("Duplicate ISIN detected" in err for err in report.errors)


def test_company_repository_crud_and_search():
    with TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_companies.json"
        repo = CompanyRepository(database_path=db_file)

        c1 = Company(
            isin="INE002A01018",
            company_name="Reliance Industries Limited",
            sector="Energy",
            ticker_nse="RELIANCE",
            ticker_bse="RELIANCE",
            bse_code="500325",
            hq_state="Maharashtra",
            industry="Oil Gas",
            market_cap_category=MarketCapCategory.LARGE_CAP,
        )
        c2 = Company(
            isin="INE467B01029",
            company_name="Tata Consultancy Services Limited",
            sector="Technology",
            ticker_nse="TCS",
            ticker_bse="TCS",
            bse_code="532540",
            hq_state="Maharashtra",
            industry="IT Services",
            market_cap_category=MarketCapCategory.LARGE_CAP,
        )

        # Test save and count
        repo.save(c1)
        assert repo.count() == 1
        assert repo.exists("INE002A01018")
        assert not repo.exists("INE467B01029")

        repo.save(c2)
        assert repo.count() == 2

        # Test get_by_isin
        fetched = repo.get_by_isin("INE002A01018")
        assert fetched is not None
        assert fetched.company_name == "Reliance Industries Limited"
        assert fetched.ticker_bse == "RELIANCE"

        # Test get_by_ticker (NSE)
        fetched_nse = repo.get_by_ticker("TCS", "NSE")
        assert fetched_nse is not None
        assert fetched_nse.isin == "INE467B01029"

        # Test get_by_ticker (BSE)
        fetched_bse = repo.get_by_ticker("500325", "BSE")
        assert fetched_bse is not None
        assert fetched_bse.ticker_nse == "RELIANCE"

        # Test get_by_sector
        energy_list = repo.get_by_sector("Energy")
        assert len(energy_list) == 1
        assert energy_list[0].ticker_nse == "RELIANCE"

        # Test search by name (fuzzy)
        fuzzy_results = repo.search_by_name("Reliance")
        assert len(fuzzy_results) > 0
        assert fuzzy_results[0].ticker_nse == "RELIANCE"

        # Fuzzy search empty
        assert repo.search_by_name("") == []

        # Test general search query fields
        # State
        results = repo.search(state="Maharashtra")
        assert len(results) == 2

        # Symbol
        results = repo.search(nse_symbol="RELIANCE")
        assert len(results) == 1
        assert results[0].isin == "INE002A01018"

        # Industry
        results = repo.search(industry="IT Services")
        assert len(results) == 1
        assert results[0].ticker_nse == "TCS"

        # Upsert
        c1_updated = Company(
            isin="INE002A01018",
            company_name="Reliance Industries Ltd",
            sector="Energy",
            ticker_nse="RELIANCE",
            ticker_bse="RELIANCE",
            bse_code="500325",
            hq_state="Maharashtra",
            industry="Oil Gas",
            market_cap_category=MarketCapCategory.LARGE_CAP,
        )
        repo.upsert_many([c1_updated])
        assert repo.count() == 2
        assert repo.get_by_isin("INE002A01018").company_name == "Reliance Industries Ltd"


def test_company_repository_exceptions():
    with TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "invalid_companies.json"

        # Write corrupted JSON to trigger load Exception
        with open(db_file, "w") as f:
            f.write("{invalid: json}")

        repo = CompanyRepository(database_path=db_file)
        assert repo.get_all() == []
        assert repo.get_by_isin("INE123") is None
        assert repo.get_by_ticker("SYM") is None
        assert repo.get_by_sector("Energy") == []
        assert repo.get_by_market_cap_category("large_cap") == []
        assert repo.search_by_name("name") == []


def test_loader_live_scrape_success():
    with TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_companies_loader.json"
        repo = CompanyRepository(database_path=db_file)
        loader = CompanyLoader(repository=repo)

        csv_content = (
            "SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING, FACE VALUE, ISIN NUMBER\n"
            "RELIANCE,Reliance Industries Limited,EQ,29-NOV-1995,10,INE002A01018\n"
            "TCS,Tata Consultancy Services Limited,EQ,12-AUG-2004,1,INE467B01029\n"
            "TESTSYM,Test Company Ltd,EQ,01-JAN-2020,10,INE999A01019\n"
        )

        mock_response = MagicMock()
        mock_response.read.return_value = csv_content.encode("utf-8")

        mock_urlopen = MagicMock()
        mock_urlopen.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_urlopen):
            companies = loader.load_company_master()

        assert len(companies) == 3
        assert repo.count() == 3

        # Reliance: enriched from seed
        reliance = repo.get_by_ticker("RELIANCE")
        assert reliance is not None
        assert reliance.sector == "Energy"
        assert reliance.hq_state == "Maharashtra"
        assert reliance.website == "https://www.ril.com"

        # Test Company: not in seed, fallback values
        test_c = repo.get_by_ticker("TESTSYM")
        assert test_c is not None
        assert test_c.company_name == "Test Company Limited"
        assert test_c.sector == "Unknown Sector"
        assert test_c.hq_state == ""
        assert test_c.website == ""


def test_loader_offline_fallback():
    with TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_companies_loader.json"
        repo = CompanyRepository(database_path=db_file)
        loader = CompanyLoader(repository=repo)

        # Trigger with invalid URL to force fallback
        companies = loader.load_company_master(
            source_url="https://invalid-host-name-abc-123.com/none.csv"
        )
        assert len(companies) > 0
        assert repo.count() == len(companies)

        # Validate that Reliance is loaded and normalized correctly
        reliance = repo.get_by_ticker("RELIANCE")
        assert reliance is not None
        assert reliance.company_name == "Reliance Industries Limited"
        assert reliance.sector == "Energy"
        assert reliance.hq_state == "Maharashtra"


def test_company_repository_more_edge_cases():
    with TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_companies_more.json"
        repo = CompanyRepository(database_path=db_file)

        c1 = Company(
            isin="INE002A01018",
            company_name="Reliance Industries Limited",
            sector="Energy",
            ticker_nse="RELIANCE",
            ticker_bse="RELIANCE",
            bse_code="500325",
            hq_state="Maharashtra",
            industry="Oil Gas",
            market_cap_category=MarketCapCategory.LARGE_CAP,
        )
        repo.save(c1)
        # Call save again to test update path for single company
        repo.save(c1)

        # Test search with name and sector
        assert len(repo.search(company_name="Reliance")) == 1
        assert len(repo.search(sector="Energy")) == 1

        # Test get_by_market_cap_category
        large_caps = repo.get_by_market_cap_category("large-cap")
        assert len(large_caps) == 1
        assert large_caps[0].ticker_nse == "RELIANCE"

        # Test get_by_ticker (BSE ticker_bse match)
        bse_match = repo.get_by_ticker("RELIANCE", "BSE")
        assert bse_match is not None

        # Test exists for nonexistent ISIN
        assert not repo.exists("INE000000000")

        # Test load invalid json dict (line 79 check)
        with open(db_file, "w") as f:
            json.dump({"not_a": "list"}, f)
        assert repo.get_all() == []

        # Test save error propagation (line 169-170 check)
        with patch("pathlib.Path.open", side_effect=IOError("Write Forbidden")):
            with pytest.raises(IOError):
                repo.save(c1)


def test_loader_exceptions():
    with TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_companies_loader_err.json"
        repo = CompanyRepository(database_path=db_file)
        loader = CompanyLoader(repository=repo)

        # Test header mismatch on live download (raising ValueError)
        csv_content = "COL1,COL2\nsomething,something"
        mock_response = MagicMock()
        mock_response.read.return_value = csv_content.encode("utf-8")

        mock_urlopen = MagicMock()
        mock_urlopen.__enter__.return_value = mock_response

        with patch("urllib.request.urlopen", return_value=mock_urlopen):
            companies = loader.load_company_master()

        # Should catch ValueError and fall back to seed data list (50 items)
        assert len(companies) == 50


def test_repository_performance_expanded():
    import time

    with TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "test_companies_perf.json"
        repo = CompanyRepository(database_path=db_file)

        # Load and save all 50 seed companies
        loader = CompanyLoader(repository=repo)
        companies = loader.load_company_master()

        # Measure save time
        start_save = time.perf_counter()
        repo.save_many(companies)
        end_save = time.perf_counter()
        save_duration = end_save - start_save

        # Measure search/query times
        start_search = time.perf_counter()
        results_sector = repo.search(sector="Banking & Financial Services")
        results_name = repo.search_by_name("Reliance")
        results_state = repo.search(state="Maharashtra")
        end_search = time.perf_counter()
        search_duration = end_search - start_search

        assert len(results_sector) > 0
        assert len(results_name) > 0
        assert len(results_state) > 0

        # Performance assertions: saves should be sub-100ms, searches sub-50ms
        assert save_duration < 0.100  # <100ms
        assert search_duration < 0.050  # <50ms
