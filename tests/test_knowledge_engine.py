"""
tests/test_knowledge_engine.py
==============================
Unit tests for the Legislative Knowledge Layer.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from knowledge.engine import RuleEngine, count_keyword_hits
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.knowledge_record import KnowledgeRecord
from services.knowledge_service import KnowledgeService
from storage.knowledge_repository import KnowledgeRepository
from validation.validator import Validator, ValidationReport


class TestRuleEngine:
    """Tests for RuleEngine class."""

    def test_count_keyword_hits(self) -> None:
        text = "This is a bank statement. Another bank is here."
        keywords = ["bank", "nonexistent"]
        assert count_keyword_hits(text, keywords) == 2
        assert count_keyword_hits("", keywords) == 0
        assert count_keyword_hits(text, []) == 0

    def test_init_loads_rules(self) -> None:
        engine = RuleEngine()
        assert len(engine.ministry_mappings) > 0
        assert len(engine.sector_domain_mapping) > 0
        assert len(engine.geographic_scope_rules) > 0
        assert len(engine.bill_type_rules) > 0
        assert len(engine.department_rules) > 0
        assert len(engine.taxonomy_hierarchy) > 0

    def test_traverse_hierarchy_finance(self) -> None:
        engine = RuleEngine()
        nodes = engine.traverse_hierarchy("Ministry of Finance")
        assert "Financial Services" in nodes
        assert "Banking" in nodes
        assert "NBFC" in nodes
        assert "Insurance" in nodes
        assert "Capital Markets" in nodes

    def test_traverse_hierarchy_environment(self) -> None:
        engine = RuleEngine()
        nodes = engine.traverse_hierarchy("Environment")
        assert "Mining" in nodes
        assert "Energy" in nodes
        assert "Steel" in nodes
        assert "Cement" in nodes

    def test_generate_record_banking_bill(self) -> None:
        engine = RuleEngine()
        bill = Bill(
            bill_id="test-banking-bill",
            title="The Banking Laws (Amendment) Bill, 2024",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Finance",
            year=2024,
            summary="A bill to amend the Reserve Bank of India Act, 1934 and Banking Regulation Act, 1949.",
            full_text="This bill regulates banking and cooperative banks. Under the RBI Act, we impose rules.",
        )

        record = engine.generate_record(bill)

        assert record.bill_id == "test-banking-bill"
        assert record.ministry == "Ministry of Finance"
        assert record.department == "Department of Financial Services"
        assert record.primary_sector == "Banking & Financial Services"
        assert "Capital Markets" in record.secondary_sectors
        assert "Insurance" in record.secondary_sectors
        assert record.policy_domain == "Financial Regulation"
        assert record.economic_domain == "Financial Services"
        assert record.regulatory_authority == "Reserve Bank of India (RBI)"
        assert record.geographic_scope == "National"
        assert record.bill_type == "Amendment Bill"
        assert "bank" in record.keywords
        assert "RBI" in record.keywords
        # Matches Reserve Bank of India Act, 1934
        assert any("Reserve Bank of India Act, 1934" in act for act in record.related_acts)
        assert record.confidence_score > 0.5
        assert "sector:Banking & Financial Services" in record.searchable_tags
        assert "ministry:Ministry of Finance" in record.searchable_tags

    def test_generate_record_geographic_state_scope(self) -> None:
        engine = RuleEngine()
        bill = Bill(
            bill_id="goa-bill",
            title="The Goa Assembly Constituencies Bill, 2024",
            house=BillHouse.RAJYA_SABHA,
            status=BillStatus.PENDING,
            url="http://test.com/goa",
            ministry="Law and Justice",
            year=2024,
        )
        record = engine.generate_record(bill)
        assert record.geographic_scope == "Goa"

    def test_generate_record_empty_ministry_and_no_category(self) -> None:
        engine = RuleEngine()
        # Bill with unknown ministry, not matching any bill category keywords
        bill = Bill(
            bill_id="unknown-bill",
            title="Silly Regulation Regulations",
            house=BillHouse.UNKNOWN,
            status=BillStatus.INTRODUCED,
            url="http://test.com/silly",
            ministry="",
            summary="Something completely random about steel production and energy consumption.",
            full_text="Steel and mining and energy are mentioned multiple times here to trigger keywords.",
        )
        record = engine.generate_record(bill)
        assert record.ministry == "Unknown Ministry"
        # Primary sector resolved via keyword frequencies
        assert record.primary_sector in ["Manufacturing", "Energy", "Infrastructure", "All Sectors"]

    def test_generate_record_file_read_error(self) -> None:
        engine = RuleEngine()
        bill = Bill(
            bill_id="file-error-bill",
            title="Boilers Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Commerce and Industry",
            text_path="nonexistent_file_path_123.txt",
            full_text="Boiler regulation text.",
        )
        record = engine.generate_record(bill)
        assert record.primary_sector == "Trade & Manufacturing"


class TestKnowledgeRepository:
    """Tests for KnowledgeRepository class."""

    @pytest.fixture
    def temp_repo(self) -> KnowledgeRepository:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("config.settings.settings.BILLS_DIR", Path(temp_dir)):
                repo = KnowledgeRepository()
                yield repo

    def test_save_and_get(self, temp_repo: KnowledgeRepository) -> None:
        record = KnowledgeRecord(
            bill_id="test-bill",
            ministry="Ministry of Finance",
            department="Department of Financial Services",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            confidence_score=0.8,
            searchable_tags=["ministry:Ministry of Finance"],
        )
        temp_repo.save(record)
        assert temp_repo.exists("test-bill")
        assert temp_repo.count() == 1

        loaded = temp_repo.get("test-bill")
        assert loaded is not None
        assert loaded.bill_id == "test-bill"
        assert loaded.ministry == "Ministry of Finance"
        assert loaded.confidence_score == 0.8
        assert "ministry:Ministry of Finance" in loaded.searchable_tags

    def test_get_all(self, temp_repo: KnowledgeRepository) -> None:
        r1 = KnowledgeRecord(
            bill_id="b1",
            ministry="Ministry of Finance",
            department="Dept1",
            policy_domain="Dom1",
            economic_domain="Eco1",
            primary_sector="Banking & Financial Services",
            secondary_sectors=["Capital Markets"],
            searchable_tags=["tag1", "tag2"],
        )
        r2 = KnowledgeRecord(
            bill_id="b2",
            ministry="Ministry of Power",
            department="Dept2",
            policy_domain="Dom2",
            economic_domain="Eco2",
            primary_sector="Energy",
            searchable_tags=["tag2"],
        )
        temp_repo.save_many([r1, r2])
        all_records = temp_repo.get_all()
        assert len(all_records) == 2

        # Test query filters
        assert len(temp_repo.get_by_ministry("Ministry of Finance")) == 1
        assert len(temp_repo.get_by_ministry("Ministry of Magic")) == 0
        assert len(temp_repo.get_by_sector("Energy")) == 1
        assert len(temp_repo.get_by_sector("Capital Markets")) == 1
        assert len(temp_repo.get_by_policy_domain("Dom1")) == 1
        assert len(temp_repo.get_by_tag("tag2")) == 2

        # Delete
        temp_repo.delete("b1")
        assert temp_repo.count() == 1
        assert temp_repo.get("b1") is None

    def test_get_raises_exception(self, temp_repo: KnowledgeRepository) -> None:
        # Mock load_json to raise exception
        with patch("storage.knowledge_repository.load_json", side_effect=Exception("Read error")):
            record = KnowledgeRecord(
                bill_id="error-bill",
                ministry="Ministry of Finance",
                department="Dept",
                policy_domain="Dom",
                economic_domain="Eco",
                primary_sector="Banking",
            )
            temp_repo.save(record)
            assert temp_repo.get("error-bill") is None

    def test_get_all_raises_exception(self, temp_repo: KnowledgeRepository) -> None:
        with patch("storage.knowledge_repository.list_files", side_effect=Exception("List error")):
            assert temp_repo.get_all() == []

    def test_delete_nonexistent(self, temp_repo: KnowledgeRepository) -> None:
        # Deleting non-existent does not raise
        temp_repo.delete("nonexistent-bill")

    def test_delete_with_file_deletion(self, temp_repo: KnowledgeRepository) -> None:
        record = KnowledgeRecord(
            bill_id="del-bill",
            ministry="Ministry of Finance",
            department="Dept",
            policy_domain="Dom",
            economic_domain="Eco",
            primary_sector="Banking & Financial Services",
        )
        temp_repo.save(record)
        assert temp_repo.exists("del-bill")
        temp_repo.delete("del-bill")
        assert not temp_repo.exists("del-bill")


class TestKnowledgeValidation:
    """Tests for KnowledgeRecord validation rules."""

    def test_validation_invalid_type(self) -> None:
        validator = Validator()
        report = validator.validate_knowledge_record("not a record")
        assert not report.is_valid
        assert "Expected KnowledgeRecord object" in report.errors[0]

    def test_validation_valid_record(self) -> None:
        validator = Validator()
        record = KnowledgeRecord(
            bill_id="test-bill",
            ministry="Ministry of Finance",
            department="Department of Financial Services",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            secondary_sectors=["Capital Markets"],
            keywords=["bank", "deposit"],
        )
        report = validator.validate_knowledge_record(record)
        assert report.is_valid
        assert len(report.errors) == 0

    def test_validation_unknown_ministry(self) -> None:
        validator = Validator()
        record = KnowledgeRecord(
            bill_id="test-bill",
            ministry="Ministry of Magic",
            department="Department of Financial Services",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
        )
        report = validator.validate_knowledge_record(record)
        assert not report.is_valid
        assert any("Unknown ministry" in err for err in report.errors)

    def test_validation_unknown_policy_domain(self) -> None:
        validator = Validator()
        record = KnowledgeRecord(
            bill_id="test-bill",
            ministry="Ministry of Finance",
            department="Department of Financial Services",
            policy_domain="Magical Law",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
        )
        report = validator.validate_knowledge_record(record)
        assert not report.is_valid
        assert any("Unknown policy domain" in err for err in report.errors)

    def test_validation_conflicting_mapping(self) -> None:
        validator = Validator()
        # Sponsoring Ministry is Power, but primary sector is Banking & Financial Services
        record = KnowledgeRecord(
            bill_id="test-bill",
            ministry="Ministry of Power",
            department="Department of Power",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
        )
        report = validator.validate_knowledge_record(record)
        assert not report.is_valid
        assert any("Conflicting mapping" in err for err in report.errors)

    def test_validation_duplicate_keywords(self) -> None:
        validator = Validator()
        record = KnowledgeRecord(
            bill_id="test-bill",
            ministry="Ministry of Finance",
            department="Department of Financial Services",
            policy_domain="Financial Regulation",
            economic_domain="Financial Services",
            primary_sector="Banking & Financial Services",
            keywords=["bank", "bank", "deposit"],
        )
        report = validator.validate_knowledge_record(record)
        assert report.is_valid
        assert len(report.warnings) > 0
        assert any("Duplicate keywords" in warn for warn in report.warnings)


class TestKnowledgeService:
    """Tests for KnowledgeService."""

    def test_generate_knowledge_orchestration(self) -> None:
        # Mock dependencies
        bill = Bill(
            bill_id="mock-bill-1",
            title="Mock Bill Title",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://mock.com",
            ministry="Finance",
            year=2024,
        )

        mock_bill_repo = MagicMock()
        mock_bill_repo.get_all.return_value = [bill]
        mock_bill_repo.get.return_value = bill
        mock_bill_repo.get_by_year.return_value = [bill]

        mock_knowledge_repo = MagicMock()

        service = KnowledgeService(
            bill_repository=mock_bill_repo,
            knowledge_repository=mock_knowledge_repo,
        )

        stats = service.generate_knowledge(dry_run=False)

        assert stats["processed"] == 1
        assert stats["saved"] == 1
        assert stats["validation_passed"] == 1
        assert stats["validation_failed"] == 0

        # Verify repo calls
        mock_knowledge_repo.save.assert_called_once()

    def test_generate_knowledge_dry_run(self) -> None:
        bill = Bill(
            bill_id="mock-bill-2",
            title="Mock Bill 2",
            house=BillHouse.RAJYA_SABHA,
            status=BillStatus.PENDING,
            url="http://mock2.com",
            ministry="Power",
            year=2023,
        )
        mock_bill_repo = MagicMock()
        mock_bill_repo.get_by_year.return_value = [bill]
        mock_knowledge_repo = MagicMock()

        service = KnowledgeService(
            bill_repository=mock_bill_repo,
            knowledge_repository=mock_knowledge_repo,
        )

        stats = service.generate_knowledge(year=2023, dry_run=True)
        assert stats["processed"] == 1
        assert stats["saved"] == 0
        mock_knowledge_repo.save.assert_not_called()

    def test_generate_knowledge_validation_failure(self) -> None:
        bill = Bill(
            bill_id="mock-bill-3",
            title="Mock Bill 3",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://mock3.com",
            ministry="UnknownMinistryXYZ",
            year=2024,
        )
        mock_bill_repo = MagicMock()
        mock_bill_repo.get_all.return_value = [bill]
        mock_knowledge_repo = MagicMock()

        service = KnowledgeService(
            bill_repository=mock_bill_repo,
            knowledge_repository=mock_knowledge_repo,
        )

        stats = service.generate_knowledge(dry_run=True)
        assert stats["processed"] == 1
        assert stats["validation_failed"] == 1

    def test_generate_knowledge_exception_during_processing(self) -> None:
        bill = Bill(
            bill_id="mock-bill-4",
            title="Mock Bill 4",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://mock4.com",
            ministry="Finance",
            year=2024,
        )
        mock_bill_repo = MagicMock()
        mock_bill_repo.get_all.return_value = [bill]
        mock_knowledge_repo = MagicMock()

        # Mock engine to raise exception
        mock_engine = MagicMock()
        mock_engine.generate_record.side_effect = Exception("Engine crash")

        service = KnowledgeService(
            bill_repository=mock_bill_repo,
            knowledge_repository=mock_knowledge_repo,
            rule_engine=mock_engine,
        )

        stats = service.generate_knowledge()
        assert stats["processed"] == 1
        assert stats["saved"] == 0
        assert stats["validation_passed"] == 0

    def test_generate_knowledge_empty_filter(self) -> None:
        mock_bill_repo = MagicMock()
        mock_bill_repo.get_all.return_value = []
        service = KnowledgeService(bill_repository=mock_bill_repo)
        stats = service.generate_knowledge()
        assert stats["processed"] == 0

    def test_generate_knowledge_bill_id_filter(self) -> None:
        bill = Bill(
            bill_id="specific-bill",
            title="Specific Bill",
            house=BillHouse.RAJYA_SABHA,
            status=BillStatus.PENDING,
            url="http://mock.com",
            ministry="Power",
            year=2024,
        )
        mock_bill_repo = MagicMock()
        mock_bill_repo.get.return_value = bill
        mock_knowledge_repo = MagicMock()

        service = KnowledgeService(
            bill_repository=mock_bill_repo,
            knowledge_repository=mock_knowledge_repo,
        )

        stats = service.generate_knowledge(bill_id_filter="specific-bill")
        assert stats["processed"] == 1
        mock_bill_repo.get.assert_called_with("specific-bill")

    def test_generate_record_comprehensive_coverage(self) -> None:
        # 1. Test missing file warning in _read_csv
        with patch("pathlib.Path.is_file", return_value=False):
            engine = RuleEngine()
            assert len(engine.ministry_mappings) == 0

        # 2. Test rule engine coverage with full features
        engine = RuleEngine()
        bill = Bill(
            bill_id="comp-coverage-bill",
            title="Banking Regulation Finance Rules",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Finance",
            year=2024,
            summary="A bill to provide support and subsidy for banking systems.",
            # Trigger Insurance secondary sector with >= 3 keywords (NOT mentioning Insurance directly)
            # Trigger Energy secondary sector with >= 3 keywords (NOT mentioning Energy directly)
            # Mention Ministry of Power to test related ministries
            # Match geographic scope (Assam) inside corpus text only
            # Trigger invalid related acts (Pronouns, unbalanced parentheses, etc.)
            full_text=(
                "This text contains premium, claim, and policyholders keywords. "
                "Also contains coal, grid, and electricity keywords for Energy. "
                "Also mentions Ministry of Power, Reserve Bank of India (RBI), and CERC. "
                "The Geographic Scope of the project is Assam. "
                "We mention This Act and Amending Act and Act and RBI) Act as well."
            ),
        )

        record = engine.generate_record(bill)

        assert record.ministry == "Ministry of Finance"
        assert record.department == "Department of Financial Services"
        assert record.primary_sector == "Banking & Financial Services"
        # Activated via keyword counts:
        assert "Insurance" in record.secondary_sectors
        # Sponsoring ministries of secondary sectors:
        assert "Ministry of Power" in record.related_ministries
        # Geographic scope matched in corpus text:
        assert record.geographic_scope == "Assam"
        # Policy keyword matched:
        assert "subsidy" in record.keywords
        # Regulated authority in text:
        assert record.regulatory_authority == "Reserve Bank of India (RBI)"
        # Confidence score:
        assert record.confidence_score > 0.6

    def test_department_wildcard_fallback(self) -> None:
        engine = RuleEngine()
        bill = Bill(
            bill_id="wildcard-dept-bill",
            title="Electricity Rules",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Power",
            year=2024,
        )
        record = engine.generate_record(bill)
        assert record.ministry == "Ministry of Power"
        assert record.department == "Department of Power"  # wildcard sector matches *

    def test_department_unknown_ministry(self) -> None:
        engine = RuleEngine()
        bill = Bill(
            bill_id="unknown-dept-bill",
            title="Magical Rules",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Ministry of Magic",
            year=2024,
        )
        record = engine.generate_record(bill)
        assert record.department == "Unknown Department"

    def test_generate_record_file_read_io_error(self) -> None:
        engine = RuleEngine()
        bill = Bill(
            bill_id="io-error-bill",
            title="Silly Boilers Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Finance",
            text_path="dummy_path.txt",
        )
        # Mock open to raise IOError and exists to return True
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", side_effect=IOError("Permission Denied")),
        ):
            record = engine.generate_record(bill)
            assert record.bill_id == "io-error-bill"

    def test_metadata_checksum_exception(self) -> None:
        engine = RuleEngine()
        bill = Bill(
            bill_id="checksum-error-bill",
            title="Simple Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Finance",
        )
        # Mock Path.is_file to return True and open to raise Exception
        with (
            patch("pathlib.Path.is_file", return_value=True),
            patch("builtins.open", side_effect=Exception("Lock error")),
        ):
            record = engine.generate_record(bill)
            assert record.source_metadata_checksum is None

    def test_rule_refinements_governance_simultaneous_elections(self) -> None:
        engine = RuleEngine()
        bill = Bill(
            bill_id="sim-elections-bill",
            title="The Constitution (Amendment) Bill, 2024",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Law and Justice",
            year=2024,
            summary="A bill about simultaneous elections in the country.",
        )
        record = engine.generate_record(bill)
        assert record.primary_sector == "Governance & Public Administration"
        assert record.policy_domain == "Governance & Public Administration"
        assert record.regulatory_authority == "Election Commission of India (ECI)"

    def test_rule_refinements_governance_waqf(self) -> None:
        engine = RuleEngine()
        bill = Bill(
            bill_id="waqf-bill",
            title="The Waqf (Amendment) Bill, 2024",
            house=BillHouse.RAJYA_SABHA,
            status=BillStatus.PENDING,
            url="http://test.com",
            ministry="Minority Affairs",
            year=2024,
            summary="A bill to amend Waqf laws.",
            full_text="This act amends Waqf board properties.",
        )
        record = engine.generate_record(bill)
        assert record.primary_sector == "Governance & Public Administration"
        assert record.policy_domain == "Governance & Public Administration"
        assert record.regulatory_authority == "Central Waqf Council"

    def test_rule_refinements_aviation_and_shipping(self) -> None:
        engine = RuleEngine()

        # 1. Aviation
        bill_avi = Bill(
            bill_id="aviation-bill",
            title="Directorate of Civil Aviation Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Civil Aviation",
            year=2024,
        )
        rec_avi = engine.generate_record(bill_avi)
        assert rec_avi.primary_sector == "Aviation"
        assert rec_avi.regulatory_authority == "Directorate General of Civil Aviation (DGCA)"

        # 2. Ports and Shipping
        bill_ship = Bill(
            bill_id="shipping-bill",
            title="Coastal Vessels Bill",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Ports Shipping and Waterways",
            year=2024,
        )
        rec_ship = engine.generate_record(bill_ship)
        assert rec_ship.primary_sector == "Ports & Shipping"
        assert rec_ship.regulatory_authority == "Ministry of Ports Shipping and Waterways"

    def test_rule_refinements_confidence_penalties(self) -> None:
        engine = RuleEngine()
        # Bill with unknown ministry, unknown sector, unknown policy domain
        bill = Bill(
            bill_id="low-confidence-bill",
            title="Unrelated Arbitrary Rules",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="http://test.com",
            ministry="Ministry of Magic",
            year=2024,
        )
        record = engine.generate_record(bill)
        # Should have fallback penalties applied
        assert record.confidence_score <= 0.3

    def test_rule_refinements_comprehensive_dynamic_authorities(self) -> None:
        engine = RuleEngine()

        # 1. NDMA
        rec = engine.generate_record(
            Bill(
                bill_id="b1",
                title="Disaster Bill",
                house=BillHouse.LOK_SABHA,
                status=BillStatus.INTRODUCED,
                url="http://t.com",
                ministry="Ministry of Home Affairs",
                year=2024,
                summary="Disaster management.",
            )
        )
        assert rec.regulatory_authority == "National Disaster Management Authority (NDMA)"

        # 2. Home Affairs Normal
        rec = engine.generate_record(
            Bill(
                bill_id="b2",
                title="Security Guidelines",
                house=BillHouse.LOK_SABHA,
                status=BillStatus.INTRODUCED,
                url="http://t.com",
                ministry="Ministry of Home Affairs",
                year=2024,
                summary="Police protocol.",
            )
        )
        assert rec.regulatory_authority == "Ministry of Home Affairs"

        # 3. Law and Justice Normal
        rec = engine.generate_record(
            Bill(
                bill_id="b3",
                title="Courts Bill",
                house=BillHouse.LOK_SABHA,
                status=BillStatus.INTRODUCED,
                url="http://t.com",
                ministry="Ministry of Law and Justice",
                year=2024,
                summary="Judicial rules.",
            )
        )
        assert rec.regulatory_authority == "Ministry of Law and Justice"

        # 4. Minority Affairs Normal
        rec = engine.generate_record(
            Bill(
                bill_id="b4",
                title="Minority Welfare Scheme",
                house=BillHouse.LOK_SABHA,
                status=BillStatus.INTRODUCED,
                url="http://t.com",
                ministry="Ministry of Minority Affairs",
                year=2024,
                summary="Scholarships.",
            )
        )
        assert rec.regulatory_authority == "Ministry of Minority Affairs"

        # 5. Personnel Normal
        rec = engine.generate_record(
            Bill(
                bill_id="b5",
                title="Civil Services Bill",
                house=BillHouse.LOK_SABHA,
                status=BillStatus.INTRODUCED,
                url="http://t.com",
                ministry="Ministry of Personnel Public Grievances and Pensions",
                year=2024,
                summary="Admn.",
            )
        )
        assert rec.regulatory_authority == "Ministry of Personnel, Public Grievances and Pensions"
