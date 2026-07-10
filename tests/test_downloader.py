"""
tests/test_downloader.py
========================
Unit tests for Task 1A.3: Official Bill Document Collection Service.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from ingestion.parliament.connector import ParliamentConnector
from ingestion.parliament.downloader import ParliamentDownloader
from schemas.bill import Bill, BillHouse, BillStatus
from storage.bill_repository import BillRepository
from validation.validator import Validator


# Helper to mock streams in HTTPX
class MockAsyncIterator:
    def __init__(self, chunks):
        self.chunks = list(chunks)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.chunks:
            raise StopAsyncIteration
        return self.chunks.pop(0)


class MockResponse:
    def __init__(self, status_code, content_chunks, headers=None):
        self.status_code = status_code
        self._chunks = content_chunks
        self.headers = headers or {"content-type": "application/pdf"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def aiter_bytes(self, chunk_size=8192):
        return MockAsyncIterator(self._chunks)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"Error {self.status_code}",
                request=MagicMock(),
                response=MagicMock(status_code=self.status_code),
            )


@pytest.fixture
def temp_dir(tmp_path) -> Path:
    return tmp_path


@pytest.fixture
def mock_connector() -> ParliamentConnector:
    connector = ParliamentConnector(max_retries=2, delay_seconds=0.01, backoff_factor=1.1)
    connector._check_robots = MagicMock(return_value=True)
    connector._enforce_delay = AsyncMock()
    return connector


# ---------------------------------------------------------------------------
# Downloader Tests
# ---------------------------------------------------------------------------


class TestDownloaderService:

    @pytest.mark.asyncio
    async def test_successful_download(self, temp_dir, mock_connector) -> None:
        downloader = ParliamentDownloader(pdfs_dir=temp_dir)
        dest_path = temp_dir / "test.pdf"

        content = b"%PDF-1.4 Mock valid PDF content with some structural metadata"
        response = MockResponse(200, [content])

        with patch("httpx.AsyncClient.stream", return_value=response):
            success, msg, size, checksum = await downloader.download_document(
                "https://test.url/doc.pdf", dest_path, mock_connector
            )

        assert success is True
        assert dest_path.is_file()
        assert size == len(content)
        assert checksum == hashlib.sha256(content).hexdigest()

    @pytest.mark.asyncio
    async def test_download_via_mock_responses(self, temp_dir, mock_connector) -> None:
        downloader = ParliamentDownloader(pdfs_dir=temp_dir)
        dest_path = temp_dir / "mock_test.pdf"

        content = b"%PDF-mock-bytes"
        mock_connector.register_mock_response("https://mock.url/doc.pdf", content)

        success, msg, size, checksum = await downloader.download_document(
            "https://mock.url/doc.pdf", dest_path, mock_connector
        )

        assert success is True
        assert dest_path.is_file()
        assert size == len(content)
        assert checksum == hashlib.sha256(content).hexdigest()

    @pytest.mark.asyncio
    async def test_retry_behaviour_on_failure(self, temp_dir, mock_connector) -> None:
        downloader = ParliamentDownloader(pdfs_dir=temp_dir)
        dest_path = temp_dir / "retry_test.pdf"

        # Mock sleep to avoid actual waiting
        sleep_mock = AsyncMock()

        # Fail with RequestError, then succeed
        failures = [0]

        def mock_stream(*args, **kwargs):
            if failures[0] < 1:
                failures[0] += 1
                raise httpx.RequestError("Temporary network failure")
            return MockResponse(200, [b"%PDF-success"])

        with (
            patch("httpx.AsyncClient.stream", side_effect=mock_stream),
            patch("asyncio.sleep", sleep_mock),
        ):
            success, msg, size, checksum = await downloader.download_document(
                "https://retry.url/doc.pdf", dest_path, mock_connector
            )

        assert success is True
        assert failures[0] == 1
        sleep_mock.assert_called_once_with(mock_connector.delay)

    @pytest.mark.asyncio
    async def test_resume_support_append(self, temp_dir, mock_connector) -> None:
        downloader = ParliamentDownloader(pdfs_dir=temp_dir)
        dest_path = temp_dir / "resume_append.pdf"

        # Write initial part of PDF (10 bytes)
        initial_part = b"%PDF-init-"
        dest_path.write_bytes(initial_part)

        # Mock server supporting range (returning 206 Partial Content)
        append_part = b"appended-tail-content"
        response = MockResponse(206, [append_part])

        headers_captured = []

        def mock_stream(method, url, headers=None, **kwargs):
            headers_captured.append(headers)
            return response

        with patch("httpx.AsyncClient.stream", side_effect=mock_stream):
            success, msg, size, checksum = await downloader.download_document(
                "https://resume.url/doc.pdf", dest_path, mock_connector
            )

        assert success is True
        assert headers_captured[0].get("Range") == "bytes=10-"
        final_content = dest_path.read_bytes()
        assert final_content == initial_part + append_part
        assert size == 10 + len(append_part)
        assert checksum == hashlib.sha256(final_content).hexdigest()

    @pytest.mark.asyncio
    async def test_resume_support_overwrite(self, temp_dir, mock_connector) -> None:
        downloader = ParliamentDownloader(pdfs_dir=temp_dir)
        dest_path = temp_dir / "resume_overwrite.pdf"

        # Write initial part (10 bytes)
        dest_path.write_bytes(b"%PDF-init-")

        # Mock server ignoring range (returning 200 OK)
        full_content = b"%PDF-fresh-content-overwriting-completely"
        response = MockResponse(200, [full_content])

        headers_captured = []

        def mock_stream(method, url, headers=None, **kwargs):
            headers_captured.append(headers)
            return response

        with patch("httpx.AsyncClient.stream", side_effect=mock_stream):
            success, msg, size, checksum = await downloader.download_document(
                "https://resume.url/doc.pdf", dest_path, mock_connector
            )

        assert success is True
        assert headers_captured[0].get("Range") == "bytes=10-"
        final_content = dest_path.read_bytes()
        assert final_content == full_content
        assert size == len(full_content)


# ---------------------------------------------------------------------------
# Validator Document Tests
# ---------------------------------------------------------------------------


class TestDocumentValidator:

    def test_validate_nonexistent_file(self) -> None:
        validator = Validator()
        report = validator.validate_document(Path("nonexistent.pdf"))
        assert not report.is_valid
        assert any("does not exist" in err.lower() for err in report.errors)

    def test_validate_invalid_extension(self, temp_dir) -> None:
        validator = Validator()
        bad_file = temp_dir / "test.txt"
        bad_file.write_text("Not a pdf")
        report = validator.validate_document(bad_file)
        assert not report.is_valid
        assert any("extension" in err.lower() for err in report.errors)

    def test_validate_file_too_small(self, temp_dir) -> None:
        validator = Validator()
        small_file = temp_dir / "small.pdf"
        small_file.write_bytes(b"%PDF-")  # 5 bytes
        report = validator.validate_document(small_file, min_size_bytes=100)
        assert not report.is_valid
        assert any("size too small" in err.lower() for err in report.errors)

    def test_validate_invalid_signature(self, temp_dir) -> None:
        validator = Validator()
        bad_sig = temp_dir / "badsig.pdf"
        bad_sig.write_bytes(b"HTML content masquerading as PDF" * 10)
        report = validator.validate_document(bad_sig, min_size_bytes=10)
        assert not report.is_valid
        assert any("signature" in err.lower() for err in report.errors)

    def test_validate_corrupted_pdf_structure(self, temp_dir) -> None:
        validator = Validator()
        corrupted = temp_dir / "corrupted.pdf"
        corrupted.write_bytes(b"%PDF-1.4 but containing binary garbage that PyPDF2 cannot parse")
        report = validator.validate_document(corrupted, min_size_bytes=10)
        assert not report.is_valid
        assert any(
            "corrupted" in err.lower() or "structure" in err.lower() for err in report.errors
        )

    def test_validate_valid_pdf_structure(self, temp_dir) -> None:
        validator = Validator()
        valid_pdf = temp_dir / "valid.pdf"

        # Generate minimal parseable PDF mock bytes
        # Just enough to look like a PDF to PyPDF2
        minimal_pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
            b"2 0 obj <</Type /Pages /Kids [] /Count 0>> endobj\n"
            b"xref\n"
            b"0 3\n"
            b"0000000000 65535 f\n"
            b"0000000009 00000 n\n"
            b"0000000056 00000 n\n"
            b"trailer <</Size 3 /Root 1 0 R>>\n"
            b"startxref\n"
            b"111\n"
            b"%%EOF"
        )
        valid_pdf.write_bytes(minimal_pdf_bytes)

        report = validator.validate_document(valid_pdf, min_size_bytes=10)
        assert report.is_valid


# ---------------------------------------------------------------------------
# Ingestion Service Integration Tests
# ---------------------------------------------------------------------------


class TestServiceDocumentIntegration:

    def _make_service(self, bill: Bill) -> tuple[Any, MagicMock]:
        from ingestion.parliament.service import ParliamentIngestionService

        mock_repo = MagicMock(spec=BillRepository)
        mock_repo.get_all.return_value = [bill]
        mock_repo.save = MagicMock()

        mock_connector = MagicMock(spec=ParliamentConnector)
        mock_connector._check_robots.return_value = True
        mock_connector._enforce_delay = AsyncMock()
        mock_connector.mock_responses = {}

        service = ParliamentIngestionService(
            bill_repository=mock_repo,
            connector=mock_connector,
        )
        return service, mock_repo

    @pytest.mark.asyncio
    async def test_service_skips_when_no_pdf_url(self) -> None:
        bill = Bill(
            bill_id="no-pdf-bill",
            title="Bill with no PDF",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://test.url/no-pdf",
            year=2024,
            pdf_url=None,
        )

        service, repo = self._make_service(bill)
        service.downloader.download_document = AsyncMock()

        stats = await service.download_bill_documents()
        assert stats["total"] == 0
        service.downloader.download_document.assert_not_called()
        repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_duplicate_skipped(self, temp_dir) -> None:
        bill_id = "duplicate-skip-bill"
        dest_path = temp_dir / "documents" / "2024" / f"{bill_id}.pdf"
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        content = b"%PDF-duplicate-skip"
        dest_path.write_bytes(content)
        checksum = hashlib.sha256(content).hexdigest()

        bill = Bill(
            bill_id=bill_id,
            title="Bill with duplicate PDF",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://test.url/duplicate",
            year=2024,
            pdf_url="https://test.url/duplicate.pdf",
            document_checksum=checksum,
        )

        service, repo = self._make_service(bill)
        # Mock downloader so we check if it is bypassed
        service.downloader.download_document = AsyncMock()

        with patch("config.settings.settings.BILLS_DIR", temp_dir):
            stats = await service.download_bill_documents()

        assert stats["total"] == 1
        assert stats["skipped"] == 1
        assert stats["downloaded"] == 0
        service.downloader.download_document.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_successful_download_persists(self, temp_dir) -> None:
        bill_id = "successful-persist-bill"
        bill = Bill(
            bill_id=bill_id,
            title="Bill to download",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://test.url/download",
            year=2024,
            pdf_url="https://test.url/download.pdf",
        )

        service, repo = self._make_service(bill)

        # Mock download_document success
        content = b"%PDF-valid"
        checksum = hashlib.sha256(content).hexdigest()

        async def mock_download(document_url, dest_path, connector):
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(content)
            return True, "Mock successful", len(content), checksum

        service.downloader.download_document = AsyncMock(side_effect=mock_download)

        # Stub validator to return true
        mock_report = MagicMock()
        mock_report.is_valid = True
        service.validator.validate_document = MagicMock(return_value=mock_report)

        with patch("config.settings.settings.BILLS_DIR", temp_dir):
            stats = await service.download_bill_documents()

        assert stats["total"] == 1
        assert stats["downloaded"] == 1
        assert stats["failed"] == 0

        # Verify repo save was called with updated fields
        repo.save.assert_called_once()
        saved_bill = repo.save.call_args[0][0]
        assert saved_bill.document_size == len(content)
        assert saved_bill.document_checksum == checksum
        assert saved_bill.download_status == "success"
        assert saved_bill.document_path is not None
        assert saved_bill.pdf_path == saved_bill.document_path

        # Verify no metadata fields modified
        assert saved_bill.title == "Bill to download"
        assert saved_bill.house == BillHouse.LOK_SABHA
        assert saved_bill.status == BillStatus.INTRODUCED

    @pytest.mark.asyncio
    async def test_service_failed_validation_deletes_file(self, temp_dir) -> None:
        bill_id = "validation-fail-bill"
        bill = Bill(
            bill_id=bill_id,
            title="Bill with bad doc",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://test.url/bad-doc",
            year=2024,
            pdf_url="https://test.url/bad-doc.pdf",
        )

        service, repo = self._make_service(bill)

        # Mock successful download bytes, but it's corrupted HTML
        content = b"<html><body>Not a PDF</body></html>"
        checksum = hashlib.sha256(content).hexdigest()

        async def mock_download(document_url, dest_path, connector):
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(content)
            return True, "Mock successful", len(content), checksum

        service.downloader.download_document = AsyncMock(side_effect=mock_download)

        # Stub validator to return false (validation fails)
        mock_report = MagicMock()
        mock_report.is_valid = False
        mock_report.errors = ["Invalid signature"]
        service.validator.validate_document = MagicMock(return_value=mock_report)

        with patch("config.settings.settings.BILLS_DIR", temp_dir):
            stats = await service.download_bill_documents()

        assert stats["total"] == 1
        assert stats["failed"] == 1
        assert stats["downloaded"] == 0

        # Verifies corrupted file got deleted
        dest_path = temp_dir / "documents" / "2024" / f"{bill_id}.pdf"
        assert not dest_path.exists()

        # Verifies repo saved with failed status
        repo.save.assert_called_once()
        saved_bill = repo.save.call_args[0][0]
        assert saved_bill.download_status == "failed"
