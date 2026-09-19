"""
tests/test_multi_state_expansion.py
===================================
Comprehensive Test Suite for Task 8.5 — Multi-State Expansion & State Knowledge Validation.

Covers all 17 verification categories:
1. Kerala adapter parsing (HTML table extraction)
2. Telangana adapter parsing (Assembly HTML extraction)
3. Inactive upper house handling (Telangana Legislative Council)
4. Multi-state ingestion pipeline (44 total bills across 4 states)
5. Cross-state provenance tracking (AUTHORITATIVE, DERIVED, UNAVAILABLE)
6. Multilingual text detection (English, Malayalam, Telugu, Kannada)
7. OCR detection for scanned documents (ocr_required, no hallucination)
8. 28-State Coverage Registry data structure and metrics
9. Multi-state search across state filter
10. Multi-state search across states list
11. Multi-state search across policy categories
12. Multi-state search across keywords and concept terms
13. State/Central repository isolation
14. Zero State prediction records (count = 0)
15. Central baseline preservation (count = 22, frozen)
16. State plain-language summary grounding
17. State provision extraction
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from config.settings import settings
from ingestion.state.adapters.kerala import KeralaSourceAdapter
from ingestion.state.adapters.telangana import TelanganaSourceAdapter
from ingestion.state.coverage_registry import CoverageStatus, StateCoverageRegistry
from ingestion.state.extractor import StateExtractionResult, StateTextExtractor
from knowledge.state_summary_engine import StateSummaryEngine
from knowledge.state_taxonomy import StateTaxonomyEngine
from schemas.bill import Bill, BillHouse, BillJurisdiction, BillStatus
from schemas.state_knowledge import StateBillKnowledge
from storage.bill_repository import BillRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_knowledge_repository import StateKnowledgeRepository
from utils.language_utils import detect_language, detect_script


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def kerala_sample_html() -> str:
    return """
    <html>
    <body>
    <table class="table">
        <thead>
            <tr>
                <th>Sl No</th>
                <th>Bill No</th>
                <th>Short Title</th>
                <th>Date of Introduction</th>
                <th>Assent Date</th>
                <th>Download</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>1</td>
                <td>250 of 2025</td>
                <td>The Kerala Finance Bill, 2025</td>
                <td>10/02/2025</td>
                <td>-</td>
                <td><a href="/bills/2025/Bill_250_2025.pdf">PDF</a></td>
            </tr>
            <tr>
                <td>2</td>
                <td>167 of 2023</td>
                <td>The Indian Partnership (Kerala Amendment) Bill, 2023</td>
                <td>14/03/2023</td>
                <td>18/08/2023</td>
                <td><a href="/bills/2023/Bill_167_2023.pdf">PDF</a></td>
            </tr>
        </tbody>
    </table>
    </body>
    </html>
    """


@pytest.fixture
def telangana_sample_html() -> str:
    return """
    <html>
    <body>
    <table class="table table-striped">
        <thead>
            <tr>
                <th>Sl.No</th>
                <th>Bill No.</th>
                <th>Title</th>
                <th>Date of Introduction</th>
                <th>Date of Passing</th>
                <th>PDF</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>1</td>
                <td>L.A. Bill No. 1 of 2026</td>
                <td>The Telangana Hate Speech and Hate Crimes (Prevention) Bill, 2026</td>
                <td>02-03-2026</td>
                <td>-</td>
                <td><a href="/legislation/bills/2026/Bill_1_2026.pdf">View PDF</a></td>
            </tr>
            <tr>
                <td>2</td>
                <td>L.A. Bill No. 5 of 2023</td>
                <td>The Telangana Private Universities (Establishment and Regulation) (Amendment) Bill, 2023</td>
                <td>04-08-2023</td>
                <td>15-09-2023</td>
                <td><a href="/legislation/bills/2023/Bill_5_2023.pdf">View PDF</a></td>
            </tr>
        </tbody>
    </table>
    </body>
    </html>
    """


# ---------------------------------------------------------------------------
# 1-3: Adapters and Sources
# ---------------------------------------------------------------------------

class TestStateAdaptersAndSources:
    """Test Kerala and Telangana adapters and source registry configuration."""

    def test_kerala_adapter_parsing(self, kerala_sample_html):
        """1. Verify Kerala adapter parses HTML table correctly."""
        adapter = KeralaSourceAdapter()
        bills = adapter.parse_listing_html(kerala_sample_html, source_url="https://www.niyamasabha.nic.in")
        assert len(bills) == 2

        b1 = bills[0]
        assert b1["title"] == "The Kerala Finance Bill, 2025"
        assert "250" in b1["bill_number"]
        assert b1["state"] == "Kerala"
        assert b1["year"] == 2025
        assert b1["introduction_date"] == "2025-02-10"
        assert b1["pdf_url"] == "https://www.niyamasabha.nic.in/bills/2025/Bill_250_2025.pdf"

        b2 = bills[1]
        assert b2["title"] == "The Indian Partnership (Kerala Amendment) Bill, 2023"
        assert b2["assent_date"] == "2023-08-18"

    def test_telangana_adapter_parsing(self, telangana_sample_html):
        """2. Verify Telangana adapter parses legislative table correctly."""
        adapter = TelanganaSourceAdapter()
        bills = adapter.parse_listing_html(telangana_sample_html, source_url="https://legislature.telangana.gov.in")
        assert len(bills) == 2

        b1 = bills[0]
        assert b1["title"] == "The Telangana Hate Speech and Hate Crimes (Prevention) Bill, 2026"
        assert b1["bill_number"] == "L.A. Bill No. 1 of 2026"
        assert b1["state"] == "Telangana"
        assert b1["year"] == 2026
        assert b1["introduction_date"] == "2026-03-02"

        b2 = bills[1]
        assert b2["status"] == "passed_both"
        assert b2["assent_date"] == "2023-09-15"

    def test_inactive_upper_house_handling(self):
        """3. Verify inactive upper house (Telangana Council) handling in configuration."""
        project_root = Path(__file__).resolve().parent.parent
        sources_path = project_root / "config" / "state_sources.json"
        with open(sources_path, "r", encoding="utf-8") as f:
            sources_data = json.load(f)

        sources = {s["source_name"]: s for s in sources_data}
        assert "telangana_assembly" in sources
        assert sources["telangana_assembly"]["active"] is True
        assert sources["telangana_assembly"]["house"] == "vidhan_sabha"

        assert "telangana_council" in sources
        assert sources["telangana_council"]["active"] is False
        assert sources["telangana_council"]["house"] == "vidhan_parishad"
        assert "upper house" in sources["telangana_council"]["notes"].lower() or "inactive" in sources["telangana_council"]["notes"].lower()


# ---------------------------------------------------------------------------
# 4-5: Multi-State Ingestion and Provenance
# ---------------------------------------------------------------------------

class TestMultiStateIngestionAndProvenance:
    """Verify multi-state repository counts and field-level provenance audit."""

    def test_multi_state_ingestion_counts(self):
        """4. Verify multi-state ingestion contains 44 bills across 4 states."""
        state_repo = StateBillRepository()
        total_bills = state_repo.count()
        assert total_bills == 44, f"Expected 44 State bills, found {total_bills}"

        states = set(b.state for b in state_repo.get_all())
        assert states == {"Andhra Pradesh", "Karnataka", "Kerala", "Telangana"}

        counts_by_state = {}
        for b in state_repo.get_all():
            counts_by_state[b.state] = counts_by_state.get(b.state, 0) + 1

        assert counts_by_state["Andhra Pradesh"] == 12
        assert counts_by_state["Karnataka"] == 11
        assert counts_by_state["Kerala"] == 11
        assert counts_by_state["Telangana"] == 10

    def test_cross_state_provenance_report(self):
        """5. Verify provenance tracking report covers all 44 bills with explicit levels."""
        report_path = settings.STATE_BILLS_DIR / "provenance_report.json"
        assert report_path.is_file()

        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        assert report["total_state_bills"] == 44
        auth = report["field_summary"]["authoritative"]
        derived = report["field_summary"]["derived"]
        unavail = report["field_summary"]["unavailable"]

        # All 44 have authoritative core fields
        assert auth["title"] == 44
        assert auth["jurisdiction"] == 44
        assert auth["state"] == 44
        assert auth["bill_number"] == 44
        assert auth["house"] == 44
        assert auth["pdf_url"] == 44
        assert auth["status"] == 44

        # Derived fields
        assert derived["year"] == 44
        assert derived["bill_id"] == 44

        # Unavailable fields properly segregated
        assert unavail["department"] == 44


# ---------------------------------------------------------------------------
# 6-7: Multilingual and OCR Handling
# ---------------------------------------------------------------------------

class TestMultilingualAndOCRHandling:
    """Verify script detection and scanned PDF / OCR handling."""

    def test_multilingual_text_detection(self):
        """6. Verify script detection for English, Malayalam, Telugu, Kannada."""
        eng_text = "The Kerala Finance Bill, 2025. Be it enacted by the Legislative Assembly."
        res_eng = detect_language(eng_text)
        assert res_eng["primary_language"] == "English"
        assert res_eng["is_multilingual"] is False

        mal_text = "THE KERALA FINANCE BILL, 2025\nകേരള ധനകാര്യ ബിൽ, 2025\nStatement of Objects."
        res_mal = detect_language(mal_text)
        assert "Malayalam" in res_mal["languages_detected"]
        assert res_mal["is_multilingual"] is True

        tel_text = "THE TELANGANA PANCHAYAT RAJ BILL\nతెలంగాణ పంచాయతీ రాజ్ బిల్లు\nStatement of Objects."
        res_tel = detect_language(tel_text)
        assert "Telugu" in res_tel["languages_detected"]
        assert res_tel["is_multilingual"] is True

        kan_text = "THE KARNATAKA GIG WORKERS BILL\nಕರ್ನಾಟಕ ಗಿಗ್ ಕಾರ್ಮಿಕರ ಮಸೂದೆ\nStatement of Objects."
        res_kan = detect_language(kan_text)
        assert "Kannada" in res_kan["languages_detected"]
        assert res_kan["is_multilingual"] is True

    def test_scanned_pdf_ocr_required_flagging(self, tmp_path):
        """7. Verify OCR detection on scanned document (<50 chars flagged as ocr_required, no hallucination)."""
        extractor = StateTextExtractor(corpus_dir=tmp_path / "corpus")
        scanned_pdf = tmp_path / "scanned_dummy.pdf"
        scanned_pdf.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")

        res = extractor.extract_from_pdf(scanned_pdf, bill_id="test-scanned-bill")
        assert res.text_status == "ocr_required"
        assert res.extracted_text == ""
        assert res.char_count < 50


# ---------------------------------------------------------------------------
# 8: 28-State Coverage Registry
# ---------------------------------------------------------------------------

class TestStateCoverageRegistry:
    """Test 28-State registry structure and metrics."""

    def test_28_state_registry_coverage(self):
        """8. Verify all 28 Indian States are recorded and exactly 4 are IMPLEMENTED."""
        registry = StateCoverageRegistry()
        all_states = registry.get_all_states()
        assert len(all_states) == 28

        summary = registry.get_summary_statistics()
        assert summary["total_states"] == 28
        assert summary["implemented_count"] == 4
        assert set(summary["implemented_states"]) == {"Andhra Pradesh", "Karnataka", "Kerala", "Telangana"}
        assert summary["total_state_bills"] == 44
        assert summary["total_state_pdfs"] == 44
        assert summary["total_state_knowledge_records"] == 44

        # Verify documentation exists
        project_root = Path(__file__).resolve().parent.parent
        doc_path = project_root / "docs" / "state_coverage_registry.md"
        assert doc_path.is_file()
        content = doc_path.read_text(encoding="utf-8")
        assert "Andhra Pradesh" in content
        assert "Karnataka" in content
        assert "Kerala" in content
        assert "Telangana" in content


# ---------------------------------------------------------------------------
# 9-12: Multi-State Search and Discovery
# ---------------------------------------------------------------------------

class TestMultiStateSearch:
    """Test multi-state search across state filters, lists, categories, keywords."""

    def test_search_by_single_state(self):
        """9. Search filtering by single state (Kerala, Telangana, Karnataka, AP)."""
        repo = StateKnowledgeRepository()

        kl_bills = repo.search(state="Kerala")
        assert len(kl_bills) == 11
        for b in kl_bills:
            assert b.state == "Kerala"

        ts_bills = repo.search(state="Telangana")
        assert len(ts_bills) == 10
        for b in ts_bills:
            assert b.state == "Telangana"

    def test_search_by_states_list(self):
        """10. Search filtering by multiple states list."""
        repo = StateKnowledgeRepository()
        south_bills = repo.search(states=["Karnataka", "Telangana"])
        assert len(south_bills) == 21  # 11 KA + 10 TS
        states_found = set(b.state for b in south_bills)
        assert states_found == {"Karnataka", "Telangana"}

    def test_search_by_policy_category(self):
        """11. Search filtering across policy categories across states."""
        repo = StateKnowledgeRepository()
        tax_bills = repo.search(policy_category="State Finance / Taxation")
        assert len(tax_bills) >= 5
        # Must span across multiple states
        states = set(b.state for b in tax_bills)
        assert len(states) >= 2

    def test_search_by_keyword_and_concept(self):
        """12. Search by keyword across states (e.g., 'gig' or 'motor' or 'panchayat')."""
        repo = StateKnowledgeRepository()
        gig_bills = repo.search(query="gig workers")
        assert len(gig_bills) >= 1
        for b in gig_bills:
            assert "gig" in b.title.lower() or "worker" in b.title.lower() or "labour" in b.policy_category.lower()


# ---------------------------------------------------------------------------
# 13-15: Isolation and Frozen Baseline
# ---------------------------------------------------------------------------

class TestIsolationAndFrozenBaseline:
    """Verify strict isolation and frozen Central baseline."""

    def test_state_central_repository_isolation(self):
        """13. State and Central repositories operate in separate directories."""
        central_repo = BillRepository()
        state_repo = StateBillRepository()
        state_k_repo = StateKnowledgeRepository()

        assert central_repo._metadata_dir != state_repo._metadata_dir
        assert "state_bills" in str(state_repo._metadata_dir)
        assert "state_bills" not in str(central_repo._metadata_dir)
        assert "state_bills" in str(state_k_repo.knowledge_dir)

    def test_zero_state_market_predictions(self):
        """14. Strict rule: ZERO State stock market predictions generated."""
        quality_path = settings.STATE_BILLS_DIR / "knowledge_quality_report.json"
        assert quality_path.is_file()
        with open(quality_path, "r", encoding="utf-8") as f:
            q = json.load(f)
        assert q["state_predictions_generated"] == 0

    def test_central_baseline_remains_frozen(self):
        """15. Strict rule: Central bills repository count remains frozen at 22."""
        central_repo = BillRepository()
        assert central_repo.count() == 22
        for b in central_repo.get_all():
            assert b.jurisdiction == BillJurisdiction.CENTRAL


# ---------------------------------------------------------------------------
# 16-17: Summary Grounding and Provision Extraction
# ---------------------------------------------------------------------------

class TestSummaryAndProvisionGrounding:
    """Verify summary and provision extraction quality."""

    def test_plain_language_summary_grounding(self):
        """16. Verify plain-language summary contains no stock or market claims."""
        repo = StateKnowledgeRepository()
        records = repo.get_all()
        assert len(records) == 44

        prohibited_patterns = [
            r"\bstock market\b",
            r"\bstock price\b",
            r"\bshares? price\b",
            r"\bticker\b",
            r"\bequity target\b",
            r"\bbuy rating\b",
            r"\bsell rating\b",
            r"\bmarket prediction\b",
        ]
        import re
        for r in records:
            summary_dict = r.summary.to_dict()
            full_summary_text = " ".join(str(v) for v in summary_dict.values()).lower()
            for pattern in prohibited_patterns:
                assert not re.search(pattern, full_summary_text), f"Found prohibited financial pattern '{pattern}' in {r.bill_id}"

    def test_structured_provision_extraction(self):
        """17. Verify provisions extraction identifies amended acts and objectives."""
        repo = StateKnowledgeRepository()
        kerala_finance = repo.get("kerala-vs-bill-250-2025")
        assert kerala_finance is not None
        assert kerala_finance.state == "Kerala"
        assert kerala_finance.policy_category == "State Finance / Taxation"
        assert kerala_finance.objective is not None
        assert len(kerala_finance.affected_stakeholders) > 0
