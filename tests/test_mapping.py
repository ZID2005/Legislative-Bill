"""
tests/test_mapping.py
======================
Unit tests for the Bill-to-Company mapping engine.

Verifies mapping rules, repository CRUD, validation checks, search lookups,
and duplicate company detection.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company, MarketCapCategory
from schemas.knowledge_record import KnowledgeRecord
from schemas.mapping_record import BillCompanyMapping
from storage.company_repository import CompanyRepository
from storage.mapping_repository import MappingRepository
from mapping.sector_mapper import SectorMapper
from validation.validator import Validator, ValidationReport
from services.mapping_service import MappingService


class TestMappingSchema:
    """Tests for BillCompanyMapping schema."""

    def test_schema_serialization_roundtrip(self) -> None:
        mapping = BillCompanyMapping(
            bill_id="test-bill",
            bill_title="Test Bill, 2026",
            ministry="Ministry of Finance",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            secondary_sectors=["Capital Markets"],
            candidate_companies=[
                {
                    "isin": "INE040A01034",
                    "company_name": "HDFC Bank Limited",
                    "ticker_nse": "HDFCBANK",
                    "sector": "Banking & Financial Services",
                    "industry": "Private Sector Bank",
                    "confidence": 0.95,
                    "reason": "Exact match.",
                }
            ],
            mapping_confidence=0.95,
            mapping_reason="One match.",
        )

        data = mapping.to_dict()
        assert data["bill_id"] == "test-bill"
        assert data["mapping_confidence"] == 0.95
        assert len(data["candidate_companies"]) == 1

        deserialized = BillCompanyMapping.from_dict(data)
        assert deserialized.bill_id == "test-bill"
        assert deserialized.bill_title == "Test Bill, 2026"
        assert deserialized.mapping_confidence == 0.95
        assert len(deserialized.candidate_companies) == 1
        assert deserialized.candidate_companies[0]["isin"] == "INE040A01034"

        # Test string representation
        repr_str = repr(mapping)
        assert "test-bill" in repr_str
        assert "Banking & Financial Services" in repr_str


class TestMappingRepository:
    """Tests for MappingRepository CRUD and search."""

    @pytest.fixture
    def temp_repo(self, tmp_path: Path) -> MappingRepository:
        mappings_dir = tmp_path / "mappings"
        mappings_dir.mkdir(parents=True, exist_ok=True)
        return MappingRepository(mappings_dir=mappings_dir)

    def test_crud_operations(self, temp_repo) -> None:
        repo = temp_repo

        mapping = BillCompanyMapping(
            bill_id="test-bill-1",
            bill_title="Test Bill 1",
            ministry="Ministry of Finance",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            secondary_sectors=["Capital Markets"],
            candidate_companies=[],
            mapping_confidence=0.0,
            mapping_reason="No candidates.",
        )

        # Count initially 0
        assert repo.count() == 0
        assert not repo.exists("test-bill-1")

        # Save
        repo.save(mapping)
        assert repo.count() == 1
        assert repo.exists("test-bill-1")

        # Get
        retrieved = repo.get("test-bill-1")
        assert retrieved is not None
        assert retrieved.bill_id == "test-bill-1"
        assert retrieved.primary_sector == "Banking & Financial Services"

        # Get non-existent
        assert repo.get("non-existent") is None

        # Delete
        repo.delete("test-bill-1")
        assert repo.count() == 0
        assert not repo.exists("test-bill-1")

    def test_save_many(self, temp_repo) -> None:
        repo = temp_repo
        m1 = BillCompanyMapping(
            bill_id="bill-1",
            bill_title="Bill 1",
            ministry="Ministry of Finance",
            policy_domain="PD",
            economic_domain="ED",
            primary_sector="Sector A",
        )
        m2 = BillCompanyMapping(
            bill_id="bill-2",
            bill_title="Bill 2",
            ministry="Ministry of Finance",
            policy_domain="PD",
            economic_domain="ED",
            primary_sector="Sector B",
        )

        repo.save_many([m1, m2])
        assert repo.count() == 2

        all_mappings = repo.get_all()
        assert len(all_mappings) == 2

    def test_search_lookups(self, temp_repo) -> None:
        repo = temp_repo

        m1 = BillCompanyMapping(
            bill_id="bill-finance",
            bill_title="The Finance Bill",
            ministry="Ministry of Finance",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            secondary_sectors=["Capital Markets"],
            candidate_companies=[
                {
                    "isin": "INE040A01034",
                    "company_name": "HDFC Bank Limited",
                    "ticker_nse": "HDFCBANK",
                    "sector": "Banking & Financial Services",
                    "industry": "Private Sector Bank",
                }
            ],
            mapping_confidence=0.8,
            mapping_reason="Match.",
        )

        m2 = BillCompanyMapping(
            bill_id="bill-tech",
            bill_title="The Cyber Security Bill",
            ministry="Ministry of Electronics and Information Technology",
            policy_domain="Data Regulation",
            economic_domain="Technology",
            primary_sector="Technology",
            secondary_sectors=["Telecommunications"],
            candidate_companies=[
                {
                    "isin": "INE467B01029",
                    "company_name": "Tata Consultancy Services Limited",
                    "ticker_nse": "TCS",
                    "sector": "Technology",
                    "industry": "IT Services",
                }
            ],
            mapping_confidence=0.9,
            mapping_reason="Match.",
        )

        repo.save_many([m1, m2])

        # Test get_by_bill
        assert repo.get_by_bill("bill-finance").bill_title == "The Finance Bill"

        # Test get_by_company
        # By ISIN
        res_company = repo.get_by_company("INE040A01034")
        assert len(res_company) == 1
        assert res_company[0].bill_id == "bill-finance"

        # By ticker
        res_ticker = repo.get_by_company("TCS")
        assert len(res_ticker) == 1
        assert res_ticker[0].bill_id == "bill-tech"

        # By Name substring (case-insensitive)
        res_name = repo.get_by_company("Consultancy")
        assert len(res_name) == 1
        assert res_name[0].bill_id == "bill-tech"

        # By empty string
        assert repo.get_by_company("") == []

        # Test get_by_sector
        # Primary sector
        assert len(repo.get_by_sector("Banking & Financial Services")) == 1
        # Secondary sector
        assert len(repo.get_by_sector("Telecommunications")) == 1
        # Unknown sector
        assert len(repo.get_by_sector("Agriculture")) == 0
        # Empty sector
        assert len(repo.get_by_sector("")) == 0

        # Test get_by_ministry
        assert len(repo.get_by_ministry("Ministry of Finance")) == 1
        assert len(repo.get_by_ministry("Nonexistent Ministry")) == 0
        assert len(repo.get_by_ministry("")) == 0

        # Test get_by_policy_domain
        assert len(repo.get_by_policy_domain("Financial Regulation")) == 1
        assert len(repo.get_by_policy_domain("Nonexistent Policy Domain")) == 0
        assert len(repo.get_by_policy_domain("")) == 0


class TestSectorMapper:
    """Tests for the core Mapping Engine (SectorMapper)."""

    @pytest.fixture
    def mock_company_repo(self, tmp_path: Path) -> CompanyRepository:
        db_file = tmp_path / "companies.json"
        repo = CompanyRepository(database_path=db_file)

        c1 = Company(
            isin="INE040A01034",
            company_name="HDFC Bank Limited",
            ticker_nse="HDFCBANK",
            sector="Banking & Financial Services",
            industry="Private Sector Bank",
            sub_industry="Commercial Banking",
            is_active=True,
        )
        c2 = Company(
            isin="INE009A01021",
            company_name="Infosys Limited",
            ticker_nse="INFY",
            sector="Technology",  # Database lists sector as Technology, override maps to Technology & IT Services
            industry="IT Services",
            sub_industry="Software Services",
            is_active=True,
            aliases=["Infy"],
        )
        c3 = Company(
            isin="INE001A01036",
            company_name="State Bank of India",
            ticker_nse="SBIN",
            sector="Banking & Financial Services",
            industry="Public Sector Bank",
            is_active=False,  # Inactive company - should be skipped
        )

        repo.save(c1)
        repo.save(c2)
        repo.save(c3)
        return repo

    def test_mapping_generation(self, mock_company_repo) -> None:
        mapper = SectorMapper(company_repository=mock_company_repo)

        bill = Bill(
            bill_id="test-bill",
            title="The Banking Regulation Amendment Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://example.com/bill",
            summary="A bill to amend laws regulating banking companies in India.",
            full_text="This Act may be called the Banking Regulation Amendment Act. It amends HDFC Bank Limited and other private sector banks.",
        )

        kr = KnowledgeRecord(
            bill_id="test-bill",
            ministry="Ministry of Finance",
            department="Department of Financial Services",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            secondary_sectors=["Capital Markets"],
            keywords=["bank", "banking", "HDFC Bank"],
        )

        mapping = mapper.map_bill_to_companies(bill, kr)

        assert mapping.bill_id == "test-bill"
        assert mapping.primary_sector == "Banking & Financial Services"

        # Mapped to HDFC Bank, but State Bank of India is skipped (inactive)
        assert len(mapping.candidate_companies) == 1

        hdfc_mapping = mapping.candidate_companies[0]
        assert hdfc_mapping["isin"] == "INE040A01034"
        assert hdfc_mapping["sector"] == "Banking & Financial Services"

        # Confidence boosts should be applied:
        # Base (primary match) = 0.50
        # Industry matches ("Private Sector Bank") = +0.20
        # Ministry regulates Banking ("Ministry of Finance") = +0.20
        # Company name mentioned in bill text = +0.10
        # Total = 1.0
        assert hdfc_mapping["confidence"] == 1.0
        assert "matches bill primary sector" in hdfc_mapping["reason"]
        assert "Industry matches" in hdfc_mapping["reason"]
        assert "regulates/supports sector" in hdfc_mapping["reason"]
        assert "Company name/alias explicitly mentioned" in hdfc_mapping["reason"]

    def test_secondary_sector_mapping_and_overrides(self, mock_company_repo) -> None:
        mapper = SectorMapper(company_repository=mock_company_repo)

        bill = Bill(
            bill_id="test-bill-2",
            title="The Tech and AI Regulation Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://example.com/bill",
            summary="A bill regulating technology companies and software services.",
            full_text="Focus on IT Services and software development including Infosys.",
        )

        kr = KnowledgeRecord(
            bill_id="test-bill-2",
            ministry="Ministry of Electronics and Information Technology",
            department="DeitY",
            policy_domain="Tech Regulation",
            economic_domain="Technology",
            primary_sector="Governance & Public Administration",  # No companies in Governance
            secondary_sectors=["Technology & IT Services"],  # Company override sector
            keywords=["tech", "software"],
        )

        mapping = mapper.map_bill_to_companies(bill, kr)

        # Technology & IT Services matches Infosys (due to company_sector.csv override)
        assert len(mapping.candidate_companies) == 1
        infy_mapping = mapping.candidate_companies[0]
        assert infy_mapping["isin"] == "INE009A01021"
        assert infy_mapping["sector"] == "Technology & IT Services"

        # Confidence boosts:
        # Base (secondary match) = 0.30
        # Industry match ("IT Services") = +0.20
        # Ministry MeitY regulates Technology & IT Services (MeitY is mapped to Technology in ministry_sector.csv) = +0.20
        # Company alias "Infosys" mentioned = +0.10
        # Total = 0.80
        assert infy_mapping["confidence"] == 0.80


class TestMappingValidator:
    """Tests for BillCompanyMapping validation checks."""

    @pytest.fixture
    def company_repo(self, tmp_path: Path) -> CompanyRepository:
        db_file = tmp_path / "companies_val.json"
        repo = CompanyRepository(database_path=db_file)
        c = Company(
            isin="INE040A01034",
            company_name="HDFC Bank Limited",
            ticker_nse="HDFCBANK",
            sector="Banking & Financial Services",
            industry="Private Sector Bank",
        )
        repo.save(c)
        return repo

    def test_validate_unknown_sector(self, company_repo) -> None:
        validator = Validator()

        mapping = BillCompanyMapping(
            bill_id="bill-1",
            bill_title="Title",
            ministry="Ministry of Finance",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Nonexistent Unknown Sector",
            secondary_sectors=["Another Bad Sector"],
            candidate_companies=[],
        )

        report = validator.validate_mapping_record(mapping, company_repo)
        assert not report.is_valid
        assert any("Unknown primary sector" in err for err in report.errors)
        assert any("Unknown secondary sector" in err for err in report.errors)

    def test_validate_duplicate_companies(self, company_repo) -> None:
        validator = Validator()

        mapping = BillCompanyMapping(
            bill_id="bill-1",
            bill_title="Title",
            ministry="Ministry of Finance",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            candidate_companies=[
                {
                    "isin": "INE040A01034",
                    "company_name": "HDFC Bank Limited",
                    "sector": "Banking & Financial Services",
                },
                {
                    "isin": "INE040A01034",  # Duplicate ISIN
                    "company_name": "HDFC Bank",
                    "sector": "Banking & Financial Services",
                },
            ],
        )

        report = validator.validate_mapping_record(mapping, company_repo)
        assert not report.is_valid
        assert any("Companies mapped twice" in err for err in report.errors)

    def test_validate_missing_companies_warning(self, company_repo) -> None:
        validator = Validator()

        # Banking & Financial Services has HDFC Bank in database, but candidate list is empty
        mapping = BillCompanyMapping(
            bill_id="bill-1",
            bill_title="Title",
            ministry="Ministry of Finance",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            candidate_companies=[],
        )

        report = validator.validate_mapping_record(mapping, company_repo)
        assert report.is_valid  # Warnings are non-blocking, so is_valid remains True
        assert len(report.warnings) == 1
        assert "Missing companies" in report.warnings[0]

    def test_validate_conflicting_mappings(self, company_repo) -> None:
        validator = Validator()

        # Company in sector 'Technology' is mapped to a bill that only affects 'Banking & Financial Services'
        mapping = BillCompanyMapping(
            bill_id="bill-1",
            bill_title="Title",
            ministry="Ministry of Finance",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            candidate_companies=[
                {
                    "isin": "INE009A01021",
                    "company_name": "Infosys Limited",
                    "sector": "Technology",  # Conflict with bill primary sector
                }
            ],
        )

        report = validator.validate_mapping_record(mapping, company_repo)
        assert not report.is_valid
        assert any(
            "Conflicting mapping: Company 'Infosys Limited' in sector 'Technology' is mapped to bill"
            in err
            for err in report.errors
        )

    def test_validate_ministry_sector_conflict_warning(self, company_repo) -> None:
        validator = Validator()

        # Sponsoring ministry is Ministry of Health and Family Welfare (which regulates Healthcare & Pharmaceuticals),
        # but the company mapped is in Banking & Financial Services. The bill lists Banking as primary sector.
        # This is a conflict between ministry and sector.
        mapping = BillCompanyMapping(
            bill_id="bill-1",
            bill_title="Title",
            ministry="Ministry of Health and Family Welfare",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            candidate_companies=[
                {
                    "isin": "INE040A01034",
                    "company_name": "HDFC Bank Limited",
                    "sector": "Banking & Financial Services",
                }
            ],
        )

        report = validator.validate_mapping_record(mapping, company_repo)
        assert report.is_valid  # Sponsoring ministry sector mismatch is a warning
        assert any("Conflicting mapping" in warn for warn in report.warnings)

    def test_validate_mappings_list(self, company_repo) -> None:
        validator = Validator()

        m1 = BillCompanyMapping(
            bill_id="bill-1",
            bill_title="Title",
            ministry="Ministry of Finance",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            candidate_companies=[],  # missing companies warning
        )

        m2 = BillCompanyMapping(
            bill_id="bill-2",
            bill_title="Title",
            ministry="Ministry of Finance",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Bad Sector Name",  # error
            candidate_companies=[],
        )

        report = validator.validate_mappings_list([m1, m2], company_repo)
        assert not report.is_valid
        assert len(report.errors) > 0
        assert len(report.warnings) > 0


class TestMappingService:
    """Tests for the MappingService coordinator."""

    def test_mapping_service_orchestration(self, tmp_path: Path) -> None:
        from storage.bill_repository import BillRepository
        from storage.knowledge_repository import KnowledgeRepository

        bill_repo = BillRepository()
        bill_repo._metadata_dir = tmp_path / "metadata"
        bill_repo._metadata_dir.mkdir(parents=True, exist_ok=True)
        bill_repo._pdfs_dir = tmp_path / "pdfs"
        bill_repo._pdfs_dir.mkdir(parents=True, exist_ok=True)

        knowledge_repo = KnowledgeRepository()
        knowledge_repo._knowledge_dir = tmp_path / "knowledge"
        knowledge_repo._knowledge_dir.mkdir(parents=True, exist_ok=True)

        company_repo = CompanyRepository(database_path=tmp_path / "companies.json")
        mapping_repo = MappingRepository(mappings_dir=tmp_path / "mappings")

        bill = Bill(
            bill_id="service-bill",
            title="Service Bill 2026",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://example.com/bill",
        )
        bill_repo.save(bill)

        kr = KnowledgeRecord(
            bill_id="service-bill",
            ministry="Ministry of Finance",
            department="DFS",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
        )
        knowledge_repo.save(kr)

        c = Company(
            isin="INE040A01034",
            company_name="HDFC Bank Limited",
            sector="Banking & Financial Services",
        )
        company_repo.save(c)

        service = MappingService(
            bill_repository=bill_repo,
            knowledge_repository=knowledge_repo,
            company_repository=company_repo,
            mapping_repository=mapping_repo,
        )

        # Test dry-run
        stats_dry = service.generate_mappings(bill_id_filter="service-bill", dry_run=True)
        assert stats_dry["processed"] == 1
        assert stats_dry["saved"] == 0
        assert stats_dry["validation_passed"] == 1
        assert mapping_repo.count() == 0

        # Test actual run
        stats_run = service.generate_mappings(bill_id_filter="service-bill", dry_run=False)
        assert stats_run["processed"] == 1
        assert stats_run["saved"] == 1
        assert mapping_repo.count() == 1

        # Retrieve and verify
        mapping = mapping_repo.get("service-bill")
        assert mapping is not None
        assert mapping.bill_id == "service-bill"
        assert len(mapping.candidate_companies) == 1
        assert mapping.candidate_companies[0]["isin"] == "INE040A01034"

    def test_additional_coverage_cases(self, tmp_path: Path) -> None:
        # 1. Test SectorMapper _read_csv nonexistent file warning
        mapper = SectorMapper()
        rows = mapper._read_csv("nonexistent_file_xyz.csv")
        assert rows == []

        # 2. Test SectorMapper sub-industry boost (industry doesn't match, but sub-industry matches)
        db_file = tmp_path / "companies_sub.json"
        comp_repo = CompanyRepository(database_path=db_file)
        c = Company(
            isin="INE117A01022",
            company_name="Abb India Limited",
            sector="Manufacturing",
            industry="Different Industry",  # doesn't match
            sub_industry="Heavy Electrical Equipment",  # will match
            is_active=True,
        )
        comp_repo.save(c)
        mapper = SectorMapper(company_repository=comp_repo)
        bill = Bill(
            bill_id="sub-ind-bill",
            title="Electrical Reform Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://example.com",
            summary="A bill regulating Heavy Electrical Equipment systems.",
        )
        kr = KnowledgeRecord(
            bill_id="sub-ind-bill",
            ministry="Ministry of Power",
            department="DOP",
            policy_domain="Power",
            economic_domain="Energy",
            primary_sector="Manufacturing",
        )
        mapping = mapper.map_bill_to_companies(bill, kr)
        assert len(mapping.candidate_companies) == 1
        # Base (primary match) = 0.5
        # Sub-industry match = +0.10
        # Total = 0.60
        assert mapping.candidate_companies[0]["confidence"] == 0.60

        # 3. Test SectorMapper company aliases boost (company name doesn't match, alias matches)
        db_file_alias = tmp_path / "companies_alias.json"
        comp_repo_alias = CompanyRepository(database_path=db_file_alias)
        c_alias = Company(
            isin="INE467B01029",
            company_name="Tata Consultancy Services Limited",
            sector="Technology & IT Services",
            industry="IT Services",
            is_active=True,
            aliases=["TCS"],
        )
        comp_repo_alias.save(c_alias)
        mapper_alias = SectorMapper(company_repository=comp_repo_alias)
        bill_alias = Bill(
            bill_id="alias-bill",
            title="TCS Expansion Guidelines",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://example.com",
            summary="Guideline for TCS in India.",
        )
        kr_alias = KnowledgeRecord(
            bill_id="alias-bill",
            ministry="Ministry of Electronics and Information Technology",
            department="DeitY",
            policy_domain="Tech Regulation",
            economic_domain="Technology",
            primary_sector="Technology & IT Services",
        )
        mapping_alias = mapper_alias.map_bill_to_companies(bill_alias, kr_alias)
        assert len(mapping_alias.candidate_companies) == 1
        # Base = 0.50
        # Alias "TCS" matches text = +0.10
        # Ministry regulations support MeitY -> Technology = +0.20
        # Total = 0.80
        assert mapping_alias.candidate_companies[0]["confidence"] == 0.80

        # 4. Test SectorMapper no candidate companies mapped reason block
        kr_empty = KnowledgeRecord(
            bill_id="empty-bill",
            ministry="Ministry of Law and Justice",
            department="Dept",
            policy_domain="Gov",
            economic_domain="Gov",
            primary_sector="Governance & Public Administration",
        )
        mapping_empty = mapper_alias.map_bill_to_companies(bill_alias, kr_empty)
        assert len(mapping_empty.candidate_companies) == 0
        assert "No candidate companies found" in mapping_empty.mapping_reason

        # 5. Test MappingRepository exceptions
        mapping_repo = MappingRepository(mappings_dir=tmp_path / "mappings_err")
        # Save a corrupted file
        corr_path = tmp_path / "mappings_err" / "corrupt-bill.json"
        corr_path.parent.mkdir(parents=True, exist_ok=True)
        with open(corr_path, "w") as f:
            f.write("{invalid json")
        # Get should return None and log error
        assert mapping_repo.get("corrupt-bill") is None

        # Mock list_files to throw Exception to hit get_all and count exceptions
        from unittest.mock import patch

        with patch(
            "storage.mapping_repository.list_files", side_effect=Exception("mock list error")
        ):
            assert mapping_repo.get_all() == []
            assert mapping_repo.count() == 0

        # 6. Test MappingService exception and missing knowledge record
        from storage.bill_repository import BillRepository
        from storage.knowledge_repository import KnowledgeRepository

        bill_repo = BillRepository()
        bill_repo._metadata_dir = tmp_path / "metadata_svc_err"
        bill_repo._metadata_dir.mkdir(parents=True, exist_ok=True)
        bill_repo._pdfs_dir = tmp_path / "pdfs_svc_err"
        bill_repo._pdfs_dir.mkdir(parents=True, exist_ok=True)

        knowledge_repo = KnowledgeRepository()
        knowledge_repo._knowledge_dir = tmp_path / "knowledge_svc_err"
        knowledge_repo._knowledge_dir.mkdir(parents=True, exist_ok=True)

        # Save bill but NO knowledge record
        bill_no_kr = Bill(
            bill_id="no-kr-bill",
            title="No KR Title",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://x.com",
        )
        bill_repo.save(bill_no_kr)

        service = MappingService(
            bill_repository=bill_repo,
            knowledge_repository=knowledge_repo,
            company_repository=comp_repo,
            mapping_repository=mapping_repo,
        )

        # Runs and skips without throwing, since KR is missing
        stats = service.generate_mappings(bill_id_filter="no-kr-bill")
        assert stats["processed"] == 0

        # Run with no bills matching filters
        stats_empty = service.generate_mappings(bill_id_filter="nonexistent-bill")
        assert stats_empty["processed"] == 0

        # Save bill and KR, but mock mapper to throw exception
        kr_err = KnowledgeRecord(
            bill_id="no-kr-bill",
            ministry="Ministry of Finance",
            department="DFS",
            policy_domain="PD",
            economic_domain="ED",
            primary_sector="Banking & Financial Services",
        )
        knowledge_repo.save(kr_err)
        with patch.object(
            service.sector_mapper,
            "map_bill_to_companies",
            side_effect=Exception("mock mapping exception"),
        ):
            stats_exc = service.generate_mappings(bill_id_filter="no-kr-bill")
            assert stats_exc["processed"] == 1
            assert stats_exc["saved"] == 0

        # Save bill and KR, mock validator to return invalid report
        mock_invalid_report = ValidationReport()
        mock_invalid_report.add_error("mock validation error")
        with patch.object(
            service.validator, "validate_mapping_record", return_value=mock_invalid_report
        ):
            stats_invalid = service.generate_mappings(bill_id_filter="no-kr-bill")
            assert stats_invalid["processed"] == 1
            assert stats_invalid["validation_failed"] == 1
            assert stats_invalid["saved"] == 1

        # Trigger warnings statistic increment in service
        mock_warning_report = ValidationReport()
        mock_warning_report.add_warning("mock warning")
        with patch.object(
            service.validator, "validate_mapping_record", return_value=mock_warning_report
        ):
            stats_warn = service.generate_mappings(bill_id_filter="no-kr-bill")
            assert stats_warn["processed"] == 1
            assert stats_warn["warnings_raised"] == 1
