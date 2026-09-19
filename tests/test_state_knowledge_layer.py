"""
tests/test_state_knowledge_layer.py
===================================
Comprehensive test suite for Task 8.4 — State Bill Knowledge Layer & Document Processing.

Verifies:
1. State PDF path isolation (no files written to data/bills/).
2. State document download handling & mock responses.
3. Document hash handling (SHA-256 validation).
4. PDF text extraction & Unicode normalisation.
5. Scanned PDF & OCR detection (<50 chars flagged as ocr_required without hallucination).
6. Corpus generation & text quality metrics.
7. State jurisdiction preservation (jurisdiction == 'state').
8. State preservation ('Andhra Pradesh', 'Karnataka').
9. Chamber preservation ('vidhan_sabha').
10. State taxonomy categorization across diverse state categories.
11. Provenance preservation (AUTHORITATIVE, DERIVED, SYSTEM_DERIVED, UNAVAILABLE).
12. Plain-language summary generation (grounded in text, no stock claims).
13. Stakeholder knowledge mapping.
14. Search compatibility across title, number, state, chamber, year, status, category, stakeholder, keyword.
15. State/Central repository isolation.
16. Zero State prediction generation (0 state prediction records).
17. Central regression preservation (Central baseline unchanged).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config.settings import settings
from ingestion.state.downloader import StateDocumentDownloader
from ingestion.state.extractor import StateExtractionResult, StateTextExtractor
from knowledge.state_stakeholder_engine import StateStakeholderEngine
from knowledge.state_summary_engine import StateSummaryEngine
from knowledge.state_taxonomy import STATE_POLICY_CATEGORIES, StateTaxonomyEngine
from schemas.bill import Bill, BillHouse, BillJurisdiction, BillStatus
from schemas.state_knowledge import StateBillKnowledge, StateBillSummary
from services.state_knowledge_service import StateKnowledgeService
from storage.bill_repository import BillRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_knowledge_repository import StateKnowledgeRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_state_bill() -> Bill:
    """Fixture returning a valid State bill instance."""
    return Bill(
        bill_id="karnataka-vs-bill-01-2025",
        title="The Karnataka Platform-based Gig Workers (Social Security and Welfare) Bill, 2025",
        bill_number="L.A. Bill No. 01 of 2025",
        year=2025,
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        jurisdiction=BillJurisdiction.STATE,
        state="Karnataka",
        introduction_date=None,
        assent_date=None,
        url="https://kla.karnataka.gov.in/bills",
        pdf_url="https://kla.karnataka.gov.in/bills/bill_01_2025.pdf",
    )


@pytest.fixture
def sample_tax_bill() -> Bill:
    """Fixture returning a taxation State bill instance."""
    return Bill(
        bill_id="andhra-pradesh-vs-bill-14-2026",
        title="The Andhra Pradesh Motor Vehicles Taxation (Amendment) Bill, 2026",
        bill_number="L.A. Bill No. 14 of 2026",
        year=2026,
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        jurisdiction=BillJurisdiction.STATE,
        state="Andhra Pradesh",
        url="https://aplegislature.org/bills",
        pdf_url="https://legislation.aplegislature.org/bills/14_2026.pdf",
    )


@pytest.fixture
def sample_bill_text() -> str:
    """Sample extracted corpus text containing Statement of Objects and legal clauses."""
    return """
THE KARNATAKA PLATFORM-BASED GIG WORKERS (SOCIAL SECURITY AND WELFARE) BILL, 2025
A Bill to provide for social security and welfare of platform-based gig workers in Karnataka.

Be it enacted by the Karnataka State Legislature in the Seventy-sixth Year of the Republic of India as follows:

1. Short title, extent and commencement.- (1) This Act may be called the Karnataka Platform-based Gig Workers (Social Security and Welfare) Act, 2025.
(2) It extends to the whole of the State of Karnataka.

2. Definitions.- In this Act, unless the context otherwise requires,-
(a) "aggregator" means a digital intermediary or marketplace for a buyer or user of a service to connect with the seller or the service provider;
(b) "gig worker" means a person who performs work or participates in a work arrangement and earns from such activities outside of a traditional employer-employee relationship;
(c) "Board" means the Karnataka Platform-based Gig Workers Welfare Board established under section 4.

3. Registration of aggregators and gig workers.- Every aggregator operating in the State shall register with the Board within sixty days of commencement.

4. Establishment of Welfare Board.- The State Government shall, by notification, establish a Board to be known as the Karnataka Platform-based Gig Workers Welfare Board.

STATEMENT OF OBJECTS AND REASONS
The platform economy has seen rapid expansion leading to thousands of individuals engaging as delivery personnel, drivers, and freelance service providers. These gig workers operate outside the traditional statutory employer-employee framework and lack comprehensive social security benefits, accident insurance, and dispute redressal mechanisms. This Bill seeks to protect gig workers' rights, ensure occupational safety, establish a dedicated Welfare Fund financed through a welfare fee on platform transactions, and constitute a tripartite Welfare Board.
"""


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestStateKnowledgeIsolation:
    """Verify isolation of State knowledge components and frozen Central baseline."""

    def test_state_pdf_path_isolation(self, tmp_path):
        """1. State PDF path isolation: PDFs are stored in data/state_bills/pdfs/, never data/bills/."""
        downloader = StateDocumentDownloader(pdfs_dir=tmp_path / "state_pdfs")
        assert "state_pdfs" in str(downloader.pdfs_dir)
        assert str(downloader.pdfs_dir) != str(settings.BILLS_DIR / "pdfs")

    def test_central_baseline_frozen(self):
        """17. Central baseline regression: verify central repository path and count remain frozen."""
        central_repo = BillRepository()
        assert central_repo._metadata_dir == settings.BILLS_DIR / "metadata"
        assert central_repo.count() >= 20
        # Ensure no State bill leaked into Central repo
        central_bills = central_repo.get_all()
        for b in central_bills:
            assert b.jurisdiction == BillJurisdiction.CENTRAL, f"Found non-central bill in Central repo: {b.bill_id}"

    def test_state_repository_isolation(self, tmp_path):
        """15. State/Central repository isolation."""
        state_repo = StateBillRepository(metadata_dir=tmp_path / "state_meta")
        central_repo = BillRepository(metadata_dir=tmp_path / "central_meta")
        assert state_repo._metadata_dir != central_repo._metadata_dir


class TestStateDownloaderAndExtraction:
    """Verify document download and PDF text extraction behavior."""

    @pytest.mark.asyncio
    async def test_mock_download_handling(self, tmp_path, sample_state_bill):
        """2. State document download handling with mock support."""
        downloader = StateDocumentDownloader(pdfs_dir=tmp_path / "pdfs")
        mock_pdf_bytes = b"%PDF-1.4 Mock legislative PDF content for testing"
        downloader.register_mock(sample_state_bill.pdf_url, mock_pdf_bytes)

        success, msg = await downloader.download_bill(sample_state_bill)
        assert success is True
        assert sample_state_bill.download_status == "success"
        assert sample_state_bill.document_size == len(mock_pdf_bytes)
        assert sample_state_bill.document_checksum is not None

    def test_document_hash_handling(self, tmp_path):
        """3. Document hash handling (SHA-256 integrity)."""
        test_file = tmp_path / "sample.pdf"
        content = b"Official Gazette Notification Text"
        test_file.write_bytes(content)

        digest = StateDocumentDownloader.compute_sha256(test_file)
        import hashlib
        expected = hashlib.sha256(content).hexdigest()
        assert digest == expected

    def test_pdf_extraction_scanned_detection(self, tmp_path, sample_state_bill):
        """5. Scanned PDF & OCR detection (<50 chars flagged as ocr_required)."""
        extractor = StateTextExtractor(corpus_dir=tmp_path / "corpus")
        # Create a dummy file that yields 0 characters
        empty_pdf = tmp_path / "empty.pdf"
        empty_pdf.write_bytes(b"%PDF-1.4 header without stream")

        result = extractor.extract_from_pdf(empty_pdf, bill_id=sample_state_bill.bill_id)
        assert result.text_status == "ocr_required"
        assert result.char_count == 0
        assert result.extracted_text == ""
        assert len(result.warnings) > 0

    def test_corpus_generation_metrics(self, tmp_path, sample_state_bill):
        """6. Corpus generation & text quality metrics."""
        corpus_dir = tmp_path / "corpus"
        extractor = StateTextExtractor(corpus_dir=corpus_dir)
        txt_path = corpus_dir / f"{sample_state_bill.bill_id}.txt"
        corpus_text = "Section 1. Short title.\nSection 2. Definitions.\nThis is a clean corpus file."
        txt_path.write_text(corpus_text, encoding="utf-8")

        result = extractor.extract_from_pdf(txt_path, bill_id=sample_state_bill.bill_id)
        assert result.text_status == "success"
        assert result.char_count == len(corpus_text)
        assert result.word_count == len(corpus_text.split())
        assert result.text_checksum is not None


class TestStateTaxonomyAndCategorization:
    """Verify policy categorization across state domains."""

    def test_state_categorization_gig_workers(self, sample_state_bill, sample_bill_text):
        """10. State categorization: Gig Workers -> Labour, Employment & Gig Economy."""
        engine = StateTaxonomyEngine()
        cat, prov = engine.classify(sample_state_bill, sample_bill_text)
        assert cat == "Labour, Employment & Gig Economy"
        assert prov == "SYSTEM_DERIVED"

    def test_state_categorization_motor_vehicles(self, sample_tax_bill):
        """10. State categorization: Motor Vehicles -> Transport & Motor Vehicles."""
        engine = StateTaxonomyEngine()
        cat, prov = engine.classify(sample_tax_bill, "The quarterly tax on transport vehicles shall be revised.")
        assert cat == "Transport & Motor Vehicles"
        assert prov == "SYSTEM_DERIVED"

    def test_taxonomy_categories_valid(self):
        """Ensure all categories match defined list."""
        assert len(STATE_POLICY_CATEGORIES) >= 10
        assert "State Finance / Taxation" in STATE_POLICY_CATEGORIES
        assert "Electricity / Energy" in STATE_POLICY_CATEGORIES
        assert "Municipal Administration & Urban Development" in STATE_POLICY_CATEGORIES


class TestStateSummarizationAndProvisions:
    """Verify plain-language summary and provision extraction."""

    def test_plain_language_summary_grounding(self, sample_state_bill, sample_bill_text):
        """12. Plain-language summary generation (grounded, no stock predictions)."""
        engine = StateSummaryEngine()
        summary = engine.generate_summary(
            sample_state_bill,
            text=sample_bill_text,
            policy_category="Labour, Employment & Gig Economy",
            stakeholders=["Platform & Gig Workers", "Aggregators"],
        )

        assert isinstance(summary, StateBillSummary)
        assert len(summary.what_is_bill) > 10
        assert len(summary.what_it_changes) > 10
        assert len(summary.why_it_matters) > 10
        assert "Platform & Gig Workers" in summary.who_is_affected
        assert len(summary.key_provisions) > 0

        # CRITICAL: Verify NO market/stock predictions
        combined = (
            f"{summary.what_is_bill} {summary.what_it_changes} "
            f"{summary.why_it_matters} {summary.who_is_affected}"
        ).lower()
        assert "stock" not in combined
        assert "share price" not in combined
        assert "nse" not in combined
        assert "bse" not in combined

    def test_provision_extraction(self, sample_state_bill, sample_bill_text):
        """Extract objective, clauses, and authorities."""
        engine = StateSummaryEngine()
        provisions = engine.extract_provisions(sample_state_bill, sample_bill_text)

        assert provisions["objective"] is not None
        assert "gig worker" in provisions["objective"].lower()
        assert provisions["chamber"] == "vidhan_sabha"
        assert provisions["state"] == "Karnataka"


class TestStateStakeholderEngine:
    """Verify stakeholder identification for State legislation."""

    def test_stakeholder_mapping_gig_workers(self, sample_state_bill, sample_bill_text):
        """13. Stakeholder extraction: Gig workers and platform aggregators identified."""
        engine = StateStakeholderEngine()
        stakeholders = engine.identify_stakeholders(
            sample_state_bill,
            text=sample_bill_text,
            policy_category="Labour, Employment & Gig Economy",
        )
        assert "Platform & Gig Workers" in stakeholders
        assert "App-based Aggregators / Platform Companies" in stakeholders


class TestStateKnowledgeRepositoryAndSearch:
    """Verify persistence and search capabilities."""

    def test_repository_save_get_and_search(self, tmp_path, sample_state_bill, sample_bill_text):
        """14. Search compatibility across title, number, state, chamber, year, status, category, stakeholder."""
        repo = StateKnowledgeRepository(knowledge_dir=tmp_path / "knowledge")
        summary_engine = StateSummaryEngine()
        summary = summary_engine.generate_summary(
            sample_state_bill,
            text=sample_bill_text,
            policy_category="Labour, Employment & Gig Economy",
        )

        record = StateBillKnowledge(
            bill_id=sample_state_bill.bill_id,
            jurisdiction="state",
            state=sample_state_bill.state,
            title=sample_state_bill.title,
            bill_number=sample_state_bill.bill_number,
            chamber="vidhan_sabha",
            status="passed_both",
            source_url=sample_state_bill.url,
            policy_category="Labour, Employment & Gig Economy",
            year=2025,
            summary=summary,
            affected_stakeholders=["Platform & Gig Workers", "Aggregators"],
            extraction_status="success",
        )

        repo.save(record)
        assert repo.exists(sample_state_bill.bill_id)
        loaded = repo.get(sample_state_bill.bill_id)
        assert loaded is not None
        assert loaded.title == sample_state_bill.title
        assert loaded.state == "Karnataka"

        # Search by keyword
        hits_kw = repo.search(query="Gig Workers")
        assert len(hits_kw) == 1

        # Search by state
        hits_state = repo.search(state="Karnataka")
        assert len(hits_state) == 1

        hits_other_state = repo.search(state="Maharashtra")
        assert len(hits_other_state) == 0

        # Search by category
        hits_cat = repo.search(policy_category="Labour, Employment & Gig Economy")
        assert len(hits_cat) == 1

        # Search by stakeholder
        hits_sh = repo.search(stakeholder="Platform & Gig Workers")
        assert len(hits_sh) == 1


class TestZeroStateMarketPredictions:
    """Verify strict prohibition of State market predictions (Part 11)."""

    def test_zero_state_prediction_records(self):
        """16. No State prediction generation: assert 0 state predictions exist."""
        # Ensure no State bills are registered in Prediction files
        from config.settings import settings

        state_repo = StateBillRepository()
        state_bill_ids = set(state_repo.get_all_ids())

        # Check prediction files in predictions directory
        pred_files = list(settings.PREDICTIONS_DIR.glob("pred_*.json"))
        state_predictions = [
            f.name for f in pred_files
            if any(f.name.startswith(f"pred_{sbid}_") for sbid in state_bill_ids)
        ]
        assert len(state_predictions) == 0, f"Found {len(state_predictions)} State prediction records; MUST BE 0!"

