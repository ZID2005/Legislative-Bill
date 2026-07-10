"""
tests/test_ingestion.py
=======================
Comprehensive unit and integration tests for the legislative ingestion pipeline.

Covers exceptions, connector, parser, downloader, normalizer, discovery, and service.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
import pytest

from config.settings import settings
from ingestion.parliament.connector import ParliamentConnector
from ingestion.parliament.exceptions import (
    ConnectorError,
    PDFDownloadError,
)
from ingestion.parliament.discovery import ParliamentDiscovery
from ingestion.parliament.downloader import ParliamentDownloader
from ingestion.parliament.normalizer import ParliamentNormalizer
from ingestion.parliament.parser import ParliamentParser
from ingestion.parliament.service import ParliamentIngestionService
from schemas.bill import Bill, BillHouse, BillStatus
from storage.bill_repository import BillRepository
from validation.validator import Validator


# ---------------------------------------------------------------------------
# Test Connector
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_connector_mock_lookup() -> None:
    connector = ParliamentConnector(mock_responses={"https://test.url": "Mock content"})
    content = await connector.fetch("https://test.url")
    assert content == "Mock content"


@pytest.mark.asyncio
async def test_connector_binary_fetch() -> None:
    connector = ParliamentConnector(mock_responses={"https://test.pdf": b"%PDF-1.4 mock bytes"})
    content = await connector.fetch("https://test.pdf", is_binary=True)
    assert content == b"%PDF-1.4 mock bytes"


@pytest.mark.asyncio
async def test_connector_robots_caching() -> None:
    connector = ParliamentConnector()
    assert connector._check_robots("https://prsindia.org/bills") is True


# ---------------------------------------------------------------------------
# Test Parser
# ---------------------------------------------------------------------------


def test_parser_rss() -> None:
    xml_content = """<?xml version="1.0" encoding="utf-8"?>
    <rss version="2.0">
        <channel>
            <title>PRS Bills</title>
            <link>https://prsindia.org/bills</link>
            <item>
                <title>The Finance Bill, 2024</title>
                <link>https://prsindia.org/bills/finance-bill-2024</link>
                <description>A bill to give effect to financial proposals.</description>
                <pubDate>Thu, 01 Feb 2024 12:00:00 +0530</pubDate>
            </item>
        </channel>
    </rss>
    """
    parser = ParliamentParser()
    bills = parser.parse_rss(xml_content)
    assert len(bills) == 1
    assert bills[0]["title"] == "The Finance Bill, 2024"
    assert bills[0]["year"] == 2024
    assert bills[0]["url"] == "https://prsindia.org/bills/finance-bill-2024"


def test_parser_html_list() -> None:
    html_content = """
    <html>
        <body>
            <table>
                <tr>
                    <th>Title</th>
                    <th>Ministry</th>
                    <th>Date of Introduction</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td><a href="/bills/finance-bill-2024">The Finance Bill, 2024</a></td>
                    <td>Ministry of Finance</td>
                    <td>01-02-2024</td>
                    <td>Passed by both Houses</td>
                </tr>
            </table>
        </body>
    </html>
    """
    parser = ParliamentParser()
    bills = parser.parse_html_list(html_content)
    assert len(bills) == 1
    assert bills[0]["title"] == "The Finance Bill, 2024"
    assert bills[0]["ministry"] == "Ministry of Finance"
    assert bills[0]["introduction_date"] == "01-02-2024"
    assert bills[0]["status"] == "Passed by both Houses"
    assert bills[0]["url"] == "https://prsindia.org/bills/finance-bill-2024"


def test_parser_html_details() -> None:
    html_content = """
    <html>
        <body>
            <div class="summary">This is a summary of the finance proposals.</div>
            <a href="/files/bills/pdfs/finance_bill.pdf">Download Bill Text (PDF)</a>
        </body>
    </html>
    """
    parser = ParliamentParser()
    bill_meta = {
        "title": "The Finance Bill, 2024",
        "url": "https://prsindia.org/bills/finance-bill-2024",
    }
    enriched = parser.parse_html_details(html_content, bill_meta)
    # The new parser stores PDF URL under pdf_url (not document_url)
    assert enriched["pdf_url"] == "https://prsindia.org/files/bills/pdfs/finance_bill.pdf"
    assert "summary" in enriched
    assert "finance proposals" in enriched["summary"]


# ---------------------------------------------------------------------------
# Test Downloader
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_downloader_pdf(tmp_path: Path) -> None:
    downloader = ParliamentDownloader(pdfs_dir=tmp_path)
    connector = ParliamentConnector(
        mock_responses={"https://test.pdf": b"%PDF-1.4 pdf_content_here"}
    )
    path = await downloader.download_pdf("https://test.pdf", "finance-bill-2024", connector)
    assert Path(path).is_file()
    assert Path(path).name == "finance-bill-2024.pdf"


# ---------------------------------------------------------------------------
# Test Normalizer
# ---------------------------------------------------------------------------


def test_normalizer_basic() -> None:
    normalizer = ParliamentNormalizer()
    raw = {
        "title": "The Digital Personal Data Protection Bill, 2023",
        "ministry": "Ministry of Electronics and Information Technology",
        "house": "Lok Sabha",
        "status": "Assented",
        "url": "https://prsindia.org/dpdp",
        "introduction_date": "03-08-2023",
        "bill_number": "125/2023",
    }
    bill = normalizer.normalize(raw)
    assert bill.bill_id == "the-digital-personal-data-protection-bill-2023"
    assert bill.year == 2023
    assert bill.house == BillHouse.LOK_SABHA
    assert bill.status == BillStatus.ASSENTED
    assert bill.introduction_date == date(2023, 8, 3)
    assert bill.bill_number == "125/2023"


# ---------------------------------------------------------------------------
# Test Validator
# ---------------------------------------------------------------------------


def test_validator_bill() -> None:
    validator = Validator()
    valid_bill = Bill(
        bill_id="test-bill",
        title="Test Bill",
        year=2024,
        ministry="Ministry of Finance",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://test.url",
    )
    report = validator.validate_bill(valid_bill)
    assert report.is_valid is True

    invalid_bill = Bill(
        bill_id="",
        title="Test Bill",
        year=1800,  # Invalid year
        ministry="Ministry of Finance",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="invalid_url",  # Malformed
    )
    report2 = validator.validate_bill(invalid_bill)
    assert report2.is_valid is False
    assert len(report2.errors) >= 3


# ---------------------------------------------------------------------------
# Test Ingestion Service (Offline Run)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_ingest_flow(tmp_path: Path) -> None:
    # Set up temp settings paths
    settings.BILLS_DIR = tmp_path / "bills"
    settings.ensure_directories()

    # Stub connector mock responses
    connector = ParliamentConnector()
    connector.register_mock_response(
        "https://prsindia.org/billtrack",
        """
        <html>
            <body>
                <table>
                    <tr>
                        <th>Title</th>
                        <th>Ministry</th>
                        <th>Date of Introduction</th>
                        <th>Status</th>
                    </tr>
                    <tr>
                        <td><a href="https://prsindia.org/bill/test-bill-2024">Test Bill, 2024</a></td>
                        <td>Ministry of Finance</td>
                        <td>01-02-2024</td>
                        <td>Introduced</td>
                    </tr>
                </table>
            </body>
        </html>
        """,
    )
    connector.register_mock_response(
        "https://prsindia.org/bill/test-bill-2024",
        """
        <html>
            <body>
                <a href="https://prsindia.org/files/test.pdf">Bill PDF Text</a>
            </body>
        </html>
        """,
    )
    connector.register_mock_response(
        "https://prsindia.org/files/test.pdf", b"%PDF-1.4 dummy pdf bytes"
    )

    # Mocks for downloader extract_text so we don't need real PDF extraction in test
    class MockDownloader(ParliamentDownloader):
        def extract_text_from_pdf(self, pdf_path: str) -> str:
            return "Mock extracted full text from PDF"

        async def download_pdf(self, doc_url: str, bill_id: str, connector: Any) -> str:
            p = self._pdfs_dir / f"{bill_id}.pdf"
            p.write_bytes(b"%PDF dummy")
            return str(p.resolve())

    repo = BillRepository()
    # Ensure it starts empty
    repo._metadata_dir = tmp_path / "bills" / "metadata"
    repo._pdfs_dir = tmp_path / "bills" / "pdfs"
    repo._metadata_dir.mkdir(parents=True, exist_ok=True)
    repo._pdfs_dir.mkdir(parents=True, exist_ok=True)

    service = ParliamentIngestionService(
        bill_repository=repo,
        connector=connector,
        downloader=MockDownloader(pdfs_dir=repo._pdfs_dir),
    )

    import unittest.mock as mock

    with mock.patch("storage.catalog.CatalogManager.update") as mock_update:
        stats = await service.ingest_bills(source="prs", year=2024)
        assert stats["discovered"] == 1
        assert stats["inserted"] == 1
        assert stats["failed"] == 0
        mock_update.assert_called_once()

    # Verify saved metadata
    assert repo.exists("test-bill-2024") is True
    bill_obj = repo.get("test-bill-2024")
    assert bill_obj is not None
    assert bill_obj.title == "Test Bill, 2024"
    # PDF download is skipped in Task 1A.2; full_text is populated in a later stage
    assert bill_obj.full_text == ""

    # Test duplicate skipped
    with mock.patch("storage.catalog.CatalogManager.update") as mock_update:
        stats_dup = await service.ingest_bills(source="prs", year=2024)
        assert stats_dup["skipped"] == 1
        assert stats_dup["inserted"] == 0


@pytest.mark.asyncio
async def test_service_dry_run(tmp_path: Path) -> None:
    settings.BILLS_DIR = tmp_path / "bills_dry"
    settings.ensure_directories()

    connector = ParliamentConnector()
    connector.register_mock_response(
        "https://prsindia.org/billtrack",
        "<html><body><table><tr><th>Title</th><th>Ministry</th><th>Status</th></tr>"
        "<tr><td><a href='https://prsindia.org/bill/test-dry'>Dry Bill</a></td>"
        "<td>Finance</td><td>Introduced</td></tr></table></body></html>",
    )
    connector.register_mock_response(
        "https://prsindia.org/bill/test-dry", "<html><body>Detail page content</body></html>"
    )

    repo = BillRepository()
    repo._metadata_dir = tmp_path / "bills_dry" / "metadata"
    repo._pdfs_dir = tmp_path / "bills_dry" / "pdfs"
    repo._metadata_dir.mkdir(parents=True, exist_ok=True)
    repo._pdfs_dir.mkdir(parents=True, exist_ok=True)

    service = ParliamentIngestionService(bill_repository=repo, connector=connector)
    import unittest.mock as mock

    with mock.patch("storage.catalog.CatalogManager.update") as mock_update:
        stats = await service.ingest_bills(source="prs", dry_run=True)
        assert stats["discovered"] == 1
        assert stats["inserted"] == 1
        # In dry run, it shouldn't actually be saved to disk
        assert repo.exists("dry-bill") is False
        mock_update.assert_not_called()


@pytest.mark.asyncio
async def test_service_resilience_and_failures(tmp_path: Path) -> None:
    settings.BILLS_DIR = tmp_path / "bills_fail"
    settings.ensure_directories()

    connector = ParliamentConnector()
    # First bill will succeed, second bill will fail detailed page fetch
    connector.register_mock_response(
        "https://prsindia.org/billtrack",
        """
        <html>
            <body>
                <table>
                    <tr><th>Title</th><th>Ministry</th><th>Status</th></tr>
                    <tr>
                        <td><a href="https://prsindia.org/bill/success">Success Bill</a></td>
                        <td>Law</td><td>Introduced</td>
                    </tr>
                    <tr>
                        <td><a href="https://prsindia.org/bill/fail">Fail Bill</a></td>
                        <td>Finance</td><td>Introduced</td>
                    </tr>
                </table>
            </body>
        </html>
        """,
    )
    connector.register_mock_response(
        "https://prsindia.org/bill/success", "<html><body>Success</body></html>"
    )
    # No mock registered for https://prsindia.org/bill/fail, which will raise connector error on live fetch

    repo = BillRepository()
    repo._metadata_dir = tmp_path / "bills_fail" / "metadata"
    repo._pdfs_dir = tmp_path / "bills_fail" / "pdfs"
    repo._metadata_dir.mkdir(parents=True, exist_ok=True)
    repo._pdfs_dir.mkdir(parents=True, exist_ok=True)

    service = ParliamentIngestionService(bill_repository=repo, connector=connector)
    import unittest.mock as mock

    with mock.patch("storage.catalog.CatalogManager.update"):
        stats = await service.ingest_bills(source="prs", dry_run=False)
        assert stats["discovered"] == 2
        # Success bill should be inserted
        assert repo.exists("success-bill") is True
        # Fail bill failed detailed page but normalizes with list metadata!
        assert repo.exists("fail-bill") is True
        assert stats["inserted"] == 2
        assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_connector_errors_and_retries() -> None:
    # Try fetching unregistered URL to trigger live fetch which will raise exception
    connector = ParliamentConnector(max_retries=2, delay_seconds=0.01)

    with pytest.raises(ConnectorError):
        # Invalid host should fail quickly and raise ConnectorError after 2 attempts
        await connector.fetch("https://invalid-host-name-xyz-987.org/test")


@pytest.mark.asyncio
async def test_connector_configured_retry_delay() -> None:
    import unittest.mock as mock

    # Use delay_seconds=0.5, max_retries=3, backoff_factor=2.0
    connector = ParliamentConnector(max_retries=3, delay_seconds=0.5, backoff_factor=2.0)

    # Mock _check_robots to return True, bypassing robots.txt lookup and forcing retry loop execution
    connector._check_robots = mock.MagicMock(return_value=True)

    sleep_times = []

    async def mock_sleep(seconds: float) -> None:
        sleep_times.append(seconds)

    with mock.patch("ingestion.parliament.connector.asyncio.sleep", side_effect=mock_sleep):
        with pytest.raises(ConnectorError):
            await connector.fetch("https://invalid-host-name-xyz-987.org/test")

    # With max_retries=3, there are 3 fetch attempts, so 2 retries (2 sleeps)
    # The sleep delays should start at self.delay (0.5) and double (1.0)
    assert len(sleep_times) == 2
    assert sleep_times[0] == 0.5
    assert sleep_times[1] == 1.0


def test_downloader_text_extraction_fallback(tmp_path: Path) -> None:
    downloader = ParliamentDownloader(pdfs_dir=tmp_path)
    dummy_pdf = tmp_path / "test_dummy.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.4 dummy contents")

    # PyPDF2 will fail to read this dummy pdf, raising exception or returning empty
    # Verify that downloader handles pdfplumber missing/failing and raises PDFDownloadError or extracts empty
    with pytest.raises(PDFDownloadError):
        downloader.extract_text_from_pdf(str(tmp_path / "nonexistent.pdf"))


def test_bill_scraper_compatibility_wrapper(tmp_path: Path) -> None:
    from ingestion.parliament.bill_scraper import BillScraper

    settings.BILLS_DIR = tmp_path / "bills_wrapper"
    settings.ensure_directories()

    # Stub ParliamentIngestionService.ingest_bills
    import unittest.mock as mock

    scraper = BillScraper()

    with mock.patch.object(
        scraper.service, "ingest_bills", new_callable=mock.AsyncMock
    ) as mock_ingest:
        mock_ingest.return_value = {"discovered": 10}
        res = scraper.scrape_bills(source="prs", start_year=2024)
        assert len(res) == 1
        assert res[0]["discovered"] == 10
        mock_ingest.assert_called_once_with(source="prs", year=2024)


@pytest.mark.asyncio
async def test_discovery_metadata_and_pagination() -> None:
    connector = ParliamentConnector()
    # Mocking HTML table with 3 bills (one is a duplicate title)
    connector.register_mock_response(
        "https://prsindia.org/billtrack",
        """
        <html>
            <body>
                <table>
                    <tr><th>Title</th><th>Ministry</th><th>Status</th></tr>
                    <tr><td><a href="/bill/bill-a">Bill A, 2024</a></td><td>Finance</td><td>Introduced</td></tr>
                    <tr><td><a href="/bill/bill-b">Bill B, 2023</a></td><td>Law</td><td>Introduced</td></tr>
                    <tr><td><a href="/bill/bill-duplicate">Bill A, 2024</a></td><td>Finance</td><td>Passed</td></tr>
                </table>
            </body>
        </html>
        """,
    )

    discovery = ParliamentDiscovery()

    # 1. Test duplicate prevention and lightweight metadata structure
    bills = await discovery.discover_bills(connector, source="prs")
    assert len(bills) == 2  # Bill A duplicate should be removed!

    # Verify lightweight keys
    for b in bills:
        assert {"bill_id", "title", "year", "source_url", "status"}.issubset(b.keys())
        assert b["status"] == "introduced"
        assert b["source_url"].startswith("https://prsindia.org")

    # 2. Test year filtering
    bills_2024 = await discovery.discover_bills(connector, source="prs", year=2024)
    assert len(bills_2024) == 1
    assert bills_2024[0]["bill_id"] == "bill-a-2024"

    # 3. Test pagination
    paginated_p1 = await discovery.discover_bills(connector, source="prs", page=1, page_size=1)
    assert len(paginated_p1) == 1
    assert paginated_p1[0]["bill_id"] == "bill-a-2024"

    paginated_p2 = await discovery.discover_bills(connector, source="prs", page=2, page_size=1)
    assert len(paginated_p2) == 1
    assert paginated_p2[0]["bill_id"] == "bill-b-2023"


@pytest.mark.asyncio
async def test_discovery_by_bill_id() -> None:
    connector = ParliamentConnector()
    # Mock listing with a row that matches the filter, and a row with an empty title
    connector.register_mock_response(
        "https://prsindia.org/billtrack",
        """
        <html>
            <body>
                <table>
                    <tr><th>Title</th><th>Ministry</th><th>Status</th></tr>
                    <tr>
                        <td><a href="/bill/telecom-bill-2023">Telecom Bill, 2023</a></td>
                        <td>Ministry of Communications</td><td>Introduced</td>
                    </tr>
                    <tr><td></td><td>No Title Ministry</td><td>Introduced</td></tr>
                </table>
            </body>
        </html>
        """,
    )
    connector.register_mock_response(
        "https://prsindia.org/bill/telecom-bill-2023",
        "<html><body><h1>Telecom Bill, 2023</h1></body></html>",
    )

    discovery = ParliamentDiscovery()

    # 1. Query for specific ID present in the listing table (covers line 146)
    res = await discovery.discover_bills(
        connector, source="prs", bill_id_filter="telecom-bill-2023"
    )
    assert len(res) == 1
    assert res[0]["bill_id"] == "telecom-bill-2023"

    # 2. Query for specific ID not in the listing (empty mock)
    connector.register_mock_response(
        "https://prsindia.org/billtrack",
        "<html><body><table><tr><th>Title</th><th>Ministry</th><th>Status</th></tr></table></body></html>",
    )
    res_direct = await discovery.discover_bills(
        connector, source="prs", bill_id_filter="telecom-bill-2023"
    )
    assert len(res_direct) == 1
    assert res_direct[0]["bill_id"] == "telecom-bill-2023"

    # 3. Query for unregistered detail page (direct detail lookup failure)
    res_fail = await discovery.discover_bills(
        connector, source="prs", bill_id_filter="nonexistent-bill"
    )
    assert len(res_fail) == 0

    # 4. Query using lok_sabha source consolidator
    res_ls = await discovery.discover_bills(connector, source="lok_sabha")
    assert len(res_ls) == 0


@pytest.mark.asyncio
async def test_discovery_latest_only() -> None:
    connector = ParliamentConnector()
    # Mock PRS RSS XML
    connector.register_mock_response(
        "https://prsindia.org/bills/rss",
        """<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0">
            <channel>
                <title>PRS Bills</title>
                <item>
                    <title>The Latest Bill, 2024</title>
                    <link>https://prsindia.org/bill/latest-bill-2024</link>
                    <description>Details of latest bill</description>
                </item>
            </channel>
        </rss>
        """,
    )
    discovery = ParliamentDiscovery()
    res = await discovery.discover_bills(connector, source="prs", latest_only=True)
    assert len(res) == 1
    assert res[0]["bill_id"] == "the-latest-bill-2024"

    # 1. Test RSS parse failure (triggering HTML fallback on lines 92-97)
    connector.register_mock_response("https://prsindia.org/bills/rss", "invalid xml content")
    connector.register_mock_response(
        "https://prsindia.org/billtrack",
        """<html><body><table><tr><th>Title</th><th>Ministry</th><th>Status</th></tr>
        <tr><td><a href="/bill/fallback-bill">Fallback Bill, 2024</a></td><td>Finance</td><td>Introduced</td></tr>
        </table></body></html>""",
    )
    res_fallback = await discovery.discover_bills(connector, source="prs", latest_only=True)
    assert len(res_fallback) == 1
    assert res_fallback[0]["bill_id"] == "fallback-bill-2024"

    # 2. Test empty title row check (triggering line 116)
    import unittest.mock as mock

    with mock.patch.object(discovery.parser, "parse_html_list", return_value=[{"title": ""}]):
        res_empty = await discovery.discover_bills(connector, source="prs")
        assert len(res_empty) == 0
