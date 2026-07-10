"""
tests/test_extractor.py
========================
Unit tests for Task 1A.4: Legislative Text Extraction & Corpus Generation.

Covers:
  - Successful text extraction (pdfplumber path)
  - PyPDF2 fallback when pdfplumber yields nothing
  - Scanned PDF detection (< 50 chars total)
  - Corrupted PDF (bad magic bytes)
  - Missing PDF (path not set / file absent)
  - Empty PDF (all pages blank)
  - Checksum-based skip logic
  - Quality metrics computation
  - Repository field update (bill object mutation)
  - Header / footer repeated-line removal
  - Unicode normalisation
  - Dry-run mode (no files written)
#   - Service-layer orchestration (extract_bill_text via IngestionService)
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingestion.parliament.extractor import LegislativeTextExtractor
from schemas.bill import Bill, BillHouse, BillStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bill(
    bill_id: str = "test-bill-2024",
    document_path: str | None = None,
    document_checksum: str | None = None,
    text_path: str | None = None,
    text_checksum: str | None = None,
    download_status: str = "success",
    year: int = 2024,
) -> Bill:
    return Bill(
        bill_id=bill_id,
        title="Test Bill, 2024",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://prsindia.org/billtrack/test-bill-2024",
        year=year,
        source="prs",
        download_status=download_status,
        document_path=document_path,
        document_checksum=document_checksum,
        text_path=text_path,
        text_checksum=text_checksum,
    )


def _minimal_pdf_bytes() -> bytes:
    """Return a tiny but structurally valid PDF with one page."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        b"/MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 44 >>\nstream\nBT /F1 12 Tf 100 700 Td "
        b"(Hello World) Tj ET\nendstream\nendobj\n"
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 "
        b"/BaseFont /Helvetica >>\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000058 00000 n \n"
        b"0000000115 00000 n \n0000000266 00000 n \n"
        b"0000000360 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n441\n%%EOF\n"
    )


# ---------------------------------------------------------------------------
# 1. Successful extraction via pdfplumber mock
# ---------------------------------------------------------------------------


class TestSuccessfulExtraction:

    def test_pdfplumber_primary_path(self, tmp_path: Path) -> None:
        """Extractor produces a success result when pdfplumber returns text."""
        corpus_dir = tmp_path / "corpus"
        extractor = LegislativeTextExtractor(corpus_dir=corpus_dir)

        pdf_path = tmp_path / "test-bill-2024.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        fake_page_text = "CLAUSE 1. This Act may be cited as the Test Act, 2024."

        mock_page = MagicMock()
        mock_page.extract_text.return_value = fake_page_text
        mock_page.extract_tables.return_value = []

        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = [mock_page]

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber:
            mock_plumber.open.return_value = mock_doc

            result = extractor.extract(
                bill_id="test-bill-2024",
                pdf_path=str(pdf_path),
                year=2024,
            )

        assert result.text_status == "success"
        assert result.extraction_method == "pdfplumber"
        assert fake_page_text in result.extracted_text
        assert result.char_count > 0
        assert result.word_count > 0
        assert result.page_count == 1
        assert result.text_path is not None
        assert Path(result.text_path).is_file()

    def test_corpus_file_content_matches_extracted_text(self, tmp_path: Path) -> None:
        """The written .txt file must contain the extracted text."""
        corpus_dir = tmp_path / "corpus"
        extractor = LegislativeTextExtractor(corpus_dir=corpus_dir)

        pdf_path = tmp_path / "bill.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        expected = "Section 1. The Government shall enact this provision."

        mock_page = MagicMock()
        mock_page.extract_text.return_value = expected
        mock_page.extract_tables.return_value = []

        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = [mock_page]

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber:
            mock_plumber.open.return_value = mock_doc
            result = extractor.extract("bill-2024", str(pdf_path), 2024)

        assert result.text_path is not None
        written = Path(result.text_path).read_text(encoding="utf-8")
        assert expected in written


# ---------------------------------------------------------------------------
# 2. PyPDF2 fallback
# ---------------------------------------------------------------------------


class TestPyPDF2Fallback:

    def test_falls_back_to_pypdf2_when_pdfplumber_empty(self, tmp_path: Path) -> None:
        """If pdfplumber returns no text, PyPDF2 is tried next."""
        corpus_dir = tmp_path / "corpus"
        extractor = LegislativeTextExtractor(corpus_dir=corpus_dir)

        pdf_path = tmp_path / "bill.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        pypdf2_text = (
            "Extracted via PyPDF2 fallback. Section 2 applies. "
            "Extra text padding to ensure character count is above threshold."
        )

        # pdfplumber returns empty text on the page
        mock_page_plumber = MagicMock()
        mock_page_plumber.extract_text.return_value = ""
        mock_page_plumber.extract_tables.return_value = []
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.__enter__ = MagicMock(return_value=mock_plumber_doc)
        mock_plumber_doc.__exit__ = MagicMock(return_value=False)
        mock_plumber_doc.pages = [mock_page_plumber]

        # PyPDF2 returns text
        mock_pypdf2_page = MagicMock()
        mock_pypdf2_page.extract_text.return_value = pypdf2_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_pypdf2_page]

        with (
            patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod,
            patch("ingestion.parliament.extractor.PyPDF2") as mock_pypdf2_mod,
        ):
            mock_plumber_mod.open.return_value = mock_plumber_doc
            mock_pypdf2_mod.PdfReader.return_value = mock_reader

            result = extractor.extract("bill-2024", str(pdf_path), 2024)

        assert result.text_status == "success"
        assert result.extraction_method == "pypdf2"
        assert pypdf2_text in result.extracted_text


# ---------------------------------------------------------------------------
# 3. Scanned PDF detection
# ---------------------------------------------------------------------------


class TestScannedPDFDetection:

    def test_scanned_pdf_flagged_when_both_extractors_return_little_text(
        self, tmp_path: Path
    ) -> None:
        """Bills with < 50 chars total are flagged as scanned_pdf."""
        corpus_dir = tmp_path / "corpus"
        extractor = LegislativeTextExtractor(corpus_dir=corpus_dir)

        pdf_path = tmp_path / "scan.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        # Both extractors yield nothing
        mock_page_empty = MagicMock()
        mock_page_empty.extract_text.return_value = ""
        mock_page_empty.extract_tables.return_value = []
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.__enter__ = MagicMock(return_value=mock_plumber_doc)
        mock_plumber_doc.__exit__ = MagicMock(return_value=False)
        mock_plumber_doc.pages = [mock_page_empty, mock_page_empty]

        mock_pypdf2_page = MagicMock()
        mock_pypdf2_page.extract_text.return_value = ""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_pypdf2_page, mock_pypdf2_page]

        with (
            patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod,
            patch("ingestion.parliament.extractor.PyPDF2") as mock_pypdf2_mod,
        ):
            mock_plumber_mod.open.return_value = mock_plumber_doc
            mock_pypdf2_mod.PdfReader.return_value = mock_reader

            result = extractor.extract("scan-bill-2024", str(pdf_path), 2024)

        assert result.text_status == "scanned_pdf"
        assert result.extracted_text == ""

    def test_scanned_pdf_does_not_write_corpus_file(self, tmp_path: Path) -> None:
        """No corpus .txt file is created when the PDF is scanned."""
        corpus_dir = tmp_path / "corpus"
        extractor = LegislativeTextExtractor(corpus_dir=corpus_dir)
        pdf_path = tmp_path / "scan.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        mock_page_empty = MagicMock()
        mock_page_empty.extract_text.return_value = ""
        mock_page_empty.extract_tables.return_value = []
        mock_plumber_doc = MagicMock()
        mock_plumber_doc.__enter__ = MagicMock(return_value=mock_plumber_doc)
        mock_plumber_doc.__exit__ = MagicMock(return_value=False)
        mock_plumber_doc.pages = [mock_page_empty]

        mock_pypdf2_page = MagicMock()
        mock_pypdf2_page.extract_text.return_value = ""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_pypdf2_page]

        with (
            patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod,
            patch("ingestion.parliament.extractor.PyPDF2") as mock_pypdf2_mod,
        ):
            mock_plumber_mod.open.return_value = mock_plumber_doc
            mock_pypdf2_mod.PdfReader.return_value = mock_reader

            result = extractor.extract("scan-2024", str(pdf_path), 2024)

        assert result.text_path is None
        assert not list(corpus_dir.rglob("*.txt"))


# ---------------------------------------------------------------------------
# 4. Corrupted PDF
# ---------------------------------------------------------------------------


class TestCorruptedPDF:

    def test_invalid_pdf_signature_returns_failed(self, tmp_path: Path) -> None:
        """Files not starting with %PDF are rejected as corrupted."""
        corpus_dir = tmp_path / "corpus"
        extractor = LegislativeTextExtractor(corpus_dir=corpus_dir)

        corrupt_pdf = tmp_path / "corrupt.pdf"
        corrupt_pdf.write_bytes(b"NOTPDF corrupted content here")

        result = extractor.extract("corrupt-bill", str(corrupt_pdf), 2024)

        assert result.text_status == "failed"
        assert len(result.errors) > 0
        assert "Invalid PDF signature" in result.errors[0]

    def test_corrupted_pdf_does_not_raise(self, tmp_path: Path) -> None:
        """Extraction of a corrupted PDF must not propagate an exception."""
        extractor = LegislativeTextExtractor(corpus_dir=tmp_path / "corpus")
        bad_pdf = tmp_path / "bad.pdf"
        bad_pdf.write_bytes(b"\x00\x01\x02\x03")

        result = extractor.extract("bad-bill", str(bad_pdf), 2024)
        assert result.text_status == "failed"


# ---------------------------------------------------------------------------
# 5. Missing PDF
# ---------------------------------------------------------------------------


class TestMissingPDF:

    def test_no_pdf_path_returns_missing_pdf(self, tmp_path: Path) -> None:
        """If pdf_path is None, result is missing_pdf."""
        extractor = LegislativeTextExtractor(corpus_dir=tmp_path / "corpus")
        result = extractor.extract("no-pdf-bill", None, 2024)
        assert result.text_status == "missing_pdf"
        assert result.text_path is None

    def test_nonexistent_pdf_path_returns_missing_pdf(self, tmp_path: Path) -> None:
        """If pdf_path is missing, result is missing_pdf."""
        extractor = LegislativeTextExtractor(corpus_dir=tmp_path / "corpus")
        result = extractor.extract("ghost-bill", str(tmp_path / "ghost.pdf"), 2024)
        assert result.text_status == "missing_pdf"


# ---------------------------------------------------------------------------
# 6. Checksum skip logic
# ---------------------------------------------------------------------------


class TestChecksumSkipLogic:

    def test_same_checksum_and_existing_corpus_skips_extraction(self, tmp_path: Path) -> None:
        """Extraction is skipped if PDF checksum matches and corpus exists."""
        corpus_dir = tmp_path / "corpus" / "2024"
        corpus_dir.mkdir(parents=True)
        corpus_file = corpus_dir / "skip-bill-2024.txt"
        corpus_file.write_text(
            "Previously extracted text that is longer than fifty characters "
            "to avoid scanned PDF detection.",
            encoding="utf-8",
        )

        pdf_path = tmp_path / "skip-bill-2024.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())
        pdf_checksum = hashlib.sha256(_minimal_pdf_bytes()).hexdigest()

        extractor = LegislativeTextExtractor(corpus_dir=tmp_path / "corpus")
        result = extractor.extract(
            bill_id="skip-bill-2024",
            pdf_path=str(pdf_path),
            year=2024,
            document_checksum=pdf_checksum,
            existing_text_checksum=pdf_checksum,  # same → skip
            existing_text_path=str(corpus_file),
        )

        assert result.text_status == "success"
        assert "skipped" in (result.warnings[0] if result.warnings else "")

    def test_different_checksum_triggers_extraction(self, tmp_path: Path) -> None:
        """If PDF checksum changed, extraction runs even if corpus exists."""
        corpus_dir = tmp_path / "corpus" / "2024"
        corpus_dir.mkdir(parents=True)
        corpus_file = corpus_dir / "changed-bill-2024.txt"
        corpus_file.write_text("Old extracted text.", encoding="utf-8")

        pdf_path = tmp_path / "changed-bill-2024.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        extractor = LegislativeTextExtractor(corpus_dir=tmp_path / "corpus")

        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Fresh new content from updated PDF. This text is long enough "
            "to bypass scanned PDF detection."
        )
        mock_page.extract_tables.return_value = []
        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = [mock_page]

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod:
            mock_plumber_mod.open.return_value = mock_doc

            result = extractor.extract(
                bill_id="changed-bill-2024",
                pdf_path=str(pdf_path),
                year=2024,
                document_checksum="new_checksum_abc123",
                existing_text_checksum="old_checksum_xyz789",
                existing_text_path=str(corpus_file),
            )

        assert result.text_status == "success"
        assert result.extraction_method == "pdfplumber"


# ---------------------------------------------------------------------------
# 7. Quality metrics
# ---------------------------------------------------------------------------


class TestQualityMetrics:

    def test_quality_metrics_populated_correctly(self, tmp_path: Path) -> None:
        """char_count, word_count, and avg_chars_per_page are computed."""
        extractor = LegislativeTextExtractor(corpus_dir=tmp_path / "corpus")
        pdf_path = tmp_path / "metrics.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        page_text = (
            "One two three four five six seven eight nine ten. "
            "Extra text padding to ensure character count is above threshold."
        )

        mock_page = MagicMock()
        mock_page.extract_text.return_value = page_text
        mock_page.extract_tables.return_value = []
        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = [mock_page]

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod:
            mock_plumber_mod.open.return_value = mock_doc
            result = extractor.extract("metrics-bill", str(pdf_path), 2024)

        assert result.page_count == 1
        assert result.char_count == len(result.extracted_text)
        assert result.word_count == len(result.extracted_text.split())
        assert result.avg_chars_per_page == result.char_count / result.page_count
        metrics = result.quality_metrics
        assert "char_count" in metrics
        assert "word_count" in metrics
        assert "avg_chars_per_page" in metrics
        assert "empty_page_count" in metrics
        assert metrics["extraction_success"] is True

    def test_empty_page_count_tracked(self, tmp_path: Path) -> None:
        """Pages with no text increment empty_page_count."""
        extractor = LegislativeTextExtractor(corpus_dir=tmp_path / "corpus")
        pdf_path = tmp_path / "empty_pages.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        mock_page_full = MagicMock()
        mock_page_full.extract_text.return_value = (
            "This page has content, section 1. Extra text padding to ensure "
            "character count is above fifty characters threshold."
        )
        mock_page_full.extract_tables.return_value = []
        mock_page_empty = MagicMock()
        mock_page_empty.extract_text.return_value = ""
        mock_page_empty.extract_tables.return_value = []
        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = [mock_page_full, mock_page_empty, mock_page_empty]

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod:
            mock_plumber_mod.open.return_value = mock_doc
            result = extractor.extract("empty-pages-bill", str(pdf_path), 2024)

        assert result.empty_page_count == 2
        assert result.page_count == 3


# ---------------------------------------------------------------------------
# 8. Header / footer removal
# ---------------------------------------------------------------------------


class TestHeaderFooterRemoval:

    def test_repeated_lines_removed_from_pages(self, tmp_path: Path) -> None:
        """Lines appearing on >50% of pages are stripped as headers/footers."""
        extractor = LegislativeTextExtractor(corpus_dir=tmp_path / "corpus")
        pdf_path = tmp_path / "hf.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        # Simulate 4 pages; the header appears on all 4
        header = "THE FINANCE BILL 2024"
        pages = [
            f"{header}\nSection {i}. Content of section {i} here. "
            f"Extra text padding to ensure character count is above "
            f"fifty characters threshold.\n"
            for i in range(1, 5)
        ]

        mock_pages = []
        for page_text in pages:
            mp = MagicMock()
            mp.extract_text.return_value = page_text
            mp.extract_tables.return_value = []
            mock_pages.append(mp)
        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = mock_pages

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod:
            mock_plumber_mod.open.return_value = mock_doc
            result = extractor.extract("hf-bill", str(pdf_path), 2024)

        assert result.text_status == "success"
        # Header should have been stripped from the corpus
        assert header not in result.extracted_text


# ---------------------------------------------------------------------------
# 9. Unicode normalisation
# ---------------------------------------------------------------------------


class TestUnicodeNormalisation:

    def test_nfkc_normalisation_applied(self, tmp_path: Path) -> None:
        """NFKC should convert compatibility characters (e.g. \ufb01 → fi)."""
        extractor = LegislativeTextExtractor(corpus_dir=tmp_path / "corpus")
        pdf_path = tmp_path / "unicode.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        # \ufb01 is a ligature (U+FB01) that NFKC normalises to "fi"
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "The bene\ufb01t of this clari\ufb01cation is clear. "
            "Extra text padding to ensure character count is above threshold."
        )
        mock_page.extract_tables.return_value = []
        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = [mock_page]

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod:
            mock_plumber_mod.open.return_value = mock_doc
            result = extractor.extract("unicode-bill", str(pdf_path), 2024)

        assert "\ufb01" not in result.extracted_text
        assert "fi" in result.extracted_text


# ---------------------------------------------------------------------------
# 10. Dry-run mode
# ---------------------------------------------------------------------------


class TestDryRun:

    def test_dry_run_does_not_write_corpus_file(self, tmp_path: Path) -> None:
        """In dry-run mode no .txt corpus file is created."""
        corpus_dir = tmp_path / "corpus"
        extractor = LegislativeTextExtractor(corpus_dir=corpus_dir)
        pdf_path = tmp_path / "dry.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Dry run text content. Extra text padding to ensure character "
            "count is above fifty characters threshold."
        )
        mock_page.extract_tables.return_value = []
        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = [mock_page]

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod:
            mock_plumber_mod.open.return_value = mock_doc
            result = extractor.extract("dry-bill", str(pdf_path), 2024, dry_run=True)

        assert result.text_status == "success"
        assert result.text_path is None  # nothing written
        assert result.text_checksum is None
        assert not list(corpus_dir.rglob("*.txt"))


# ---------------------------------------------------------------------------
# 11. Service-layer orchestration
# ---------------------------------------------------------------------------


class TestServiceOrchestration:

    @pytest.mark.asyncio
    async def test_service_extract_updates_bill_fields(self, tmp_path: Path) -> None:
        """extract_bill_text() updates text_* fields on the bill object."""
        from ingestion.parliament.service import ParliamentIngestionService
        from storage.bill_repository import BillRepository

        pdf_path = tmp_path / "service-bill.pdf"
        pdf_path.write_bytes(_minimal_pdf_bytes())

        bill = _make_bill(
            bill_id="service-bill-2024",
            document_path=str(pdf_path),
            document_checksum="abc123",
            download_status="success",
        )

        mock_repo = MagicMock(spec=BillRepository)
        mock_repo.get_all.return_value = [bill]

        saved_bills: list[Bill] = []
        mock_repo.save.side_effect = saved_bills.append

        service = ParliamentIngestionService(bill_repository=mock_repo)
        service.extractor._corpus_dir = tmp_path / "corpus"

        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Service test text content here. Extra text padding to ensure "
            "character count is above fifty characters threshold."
        )
        mock_page.extract_tables.return_value = []
        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = [mock_page]

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod:
            mock_plumber_mod.open.return_value = mock_doc
            stats = await service.extract_bill_text()

        assert stats["extracted"] >= 1 or stats["skipped"] >= 1
        assert stats["failed"] == 0
        assert len(saved_bills) >= 1
        saved = saved_bills[0]
        assert saved.text_status == "success"
        assert saved.extraction_method in ("pdfplumber", "pypdf2")
        assert saved.quality_metrics is not None

    @pytest.mark.asyncio
    async def test_service_skips_bills_without_successful_download(self, tmp_path: Path) -> None:
        """Bills without download_status='success' are not extracted."""
        from ingestion.parliament.service import ParliamentIngestionService
        from storage.bill_repository import BillRepository

        pending_bill = _make_bill(
            bill_id="pending-bill-2024",
            download_status="failed",
        )

        mock_repo = MagicMock(spec=BillRepository)
        mock_repo.get_all.return_value = [pending_bill]

        service = ParliamentIngestionService(bill_repository=mock_repo)
        stats = await service.extract_bill_text()

        assert stats["total"] == 0
        mock_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_continues_on_individual_failure(self, tmp_path: Path) -> None:
        """Individual failure does not abort remaining bills extraction."""
        from ingestion.parliament.service import ParliamentIngestionService
        from storage.bill_repository import BillRepository

        bad_bill = _make_bill(
            bill_id="bad-bill-2024",
            document_path="/does/not/exist/bad.pdf",
            document_checksum="x",
            download_status="success",
        )
        good_pdf = tmp_path / "good-bill.pdf"
        good_pdf.write_bytes(_minimal_pdf_bytes())
        good_bill = _make_bill(
            bill_id="good-bill-2024",
            document_path=str(good_pdf),
            document_checksum="y",
            download_status="success",
        )

        mock_repo = MagicMock(spec=BillRepository)
        mock_repo.get_all.return_value = [bad_bill, good_bill]

        service = ParliamentIngestionService(bill_repository=mock_repo)
        service.extractor._corpus_dir = tmp_path / "corpus"

        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Valid text content for good bill here. Extra padding to "
            "exceed the 50 characters threshold."
        )
        mock_page.extract_tables.return_value = []
        mock_doc = MagicMock()
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=False)
        mock_doc.pages = [mock_page]

        with patch("ingestion.parliament.extractor.pdfplumber") as mock_plumber_mod:
            mock_plumber_mod.open.return_value = mock_doc
            stats = await service.extract_bill_text()

        assert stats["total"] == 2
        # Good bill should have been extracted; bad one failed
        assert stats["failed"] >= 1
        assert stats["extracted"] >= 1
