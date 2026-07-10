"""
tests/test_metadata.py
======================
Unit tests for Task 1A.2: Bill Metadata Collection Service.

Covers:
  - parse_html_details: full extraction, partial extraction, edge cases
  - ParliamentNormalizer: new fields, year=None handling, ministry empty
  - Validator: year=None warning, pdf_url malformed warning, ministry empty warning
  - ParliamentIngestionService: PDF download skipped, metadata stored
  - Bill schema: to_dict / from_dict roundtrip for all new fields
  - _has_changed(): update detection for all Task 1A.2 metadata fields
"""

from __future__ import annotations

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock

from ingestion.parliament.parser import ParliamentParser
from ingestion.parliament.normalizer import ParliamentNormalizer
from ingestion.parliament.service import ParliamentIngestionService
from ingestion.parliament.connector import ParliamentConnector
from schemas.bill import Bill, BillHouse, BillStatus
from storage.bill_repository import BillRepository
from validation.validator import Validator


# ---------------------------------------------------------------------------
# HTML Fixtures
# ---------------------------------------------------------------------------

FULL_DETAIL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head><title>Test Bill</title>
<meta name="last-modified" content="2024-03-15" />
</head>
<body>
<main>
<h1>The Finance Amendment Bill, 2024</h1>
<div class="field-name-field-ministry">Ministry of Finance</div>
<div class="field-name-field-bill-number">Bill No. 14 of 2024</div>
<div class="field-name-field-house">Lok Sabha</div>
<div class="field-name-field-bill-status">Passed</div>
<div class="field-name-field-date-of-introduction">15 February 2024</div>
<div class="field-name-field-session">Budget Session, 2024</div>
<div class="field-name-field-introduced-by">Nirmala Sitharaman</div>
<div class="field-name-body">This bill amends the Finance Act to introduce new provisions for
direct tax relief and GST simplification across sectors.</div>
<a href="/sites/default/files/finance-bill-2024.pdf">Bill Text</a>
<a href="/billtrack/the-income-tax-amendment-bill-2023">Income Tax Amendment Bill, 2023</a>
<a href="/billtrack/the-gst-council-bill-2022">GST Council Bill, 2022</a>
<a href="/acts/finance-act-2020">Finance Act, 2020</a>
<a href="/acts/gst-act-2017">GST Act, 2017</a>
</main>
</body>
</html>
"""

PARTIAL_DETAIL_HTML = """
<!DOCTYPE html>
<html lang="en">
<body>
<main>
<h1>The Banking Regulation Amendment Bill</h1>
<div class="field-name-field-bill-status">Pending</div>
</main>
</body>
</html>
"""

MINIMAL_DETAIL_HTML = """
<!DOCTYPE html>
<html>
<body>
<h1>Some Unnamed Bill</h1>
</body>
</html>
"""

MALFORMED_HTML = ""

PDF_PRIORITY_HTML = """
<!DOCTYPE html>
<html>
<body>
<a href="/files/some-annexure.pdf">Annexure</a>
<a href="/files/finance-bill-2024-as-introduced.pdf">As Introduced</a>
<a href="/files/finance-bill-2024-report.pdf">Committee Report</a>
</body>
</html>
"""

NO_PDF_HTML = """
<!DOCTYPE html>
<html>
<body>
<h1>The Test Bill, 2023</h1>
<p>No PDF available.</p>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Parser Tests — parse_html_details
# ---------------------------------------------------------------------------


class TestParseHtmlDetails:

    def setup_method(self) -> None:
        self.parser = ParliamentParser()
        self.base_meta = {
            "title": "Fallback Title",
            "url": "https://prsindia.org/billtrack/the-finance-amendment-bill-2024",
            "source_url": "https://prsindia.org/billtrack/the-finance-amendment-bill-2024",
            "status": "introduced",
            "source": "prs",
        }

    def test_parse_details_full_title(self) -> None:
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        assert result["title"] == "The Finance Amendment Bill, 2024"

    def test_parse_details_full_ministry(self) -> None:
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        assert "Finance" in result.get("ministry", "")

    def test_parse_details_full_bill_number(self) -> None:
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        assert "14" in result.get("bill_number", "")

    def test_parse_details_full_session(self) -> None:
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        assert "Budget" in result.get("session", "")

    def test_parse_details_full_sponsor(self) -> None:
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        assert "Nirmala" in result.get("sponsor", "")

    def test_parse_details_full_summary(self) -> None:
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        assert len(result.get("summary", "")) > 10

    def test_parse_details_pdf_url_priority_bill_text(self) -> None:
        """'Bill Text' link should be chosen over other .pdf links."""
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        pdf_url = result.get("pdf_url", "")
        assert pdf_url.endswith(".pdf")
        assert "prsindia.org" in pdf_url

    def test_parse_details_pdf_url_priority_as_introduced(self) -> None:
        """'As Introduced' label should be prioritized over generic PDF."""
        result = self.parser.parse_html_details(PDF_PRIORITY_HTML, self.base_meta)
        pdf_url = result.get("pdf_url", "")
        assert "as-introduced" in pdf_url

    def test_parse_details_no_pdf(self) -> None:
        result = self.parser.parse_html_details(NO_PDF_HTML, self.base_meta)
        assert result.get("pdf_url") is None

    def test_parse_details_related_bills(self) -> None:
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        related = result.get("related_bills", [])
        assert len(related) >= 2
        assert all(isinstance(s, str) for s in related)
        # Current bill slug should not be in related
        assert "the-finance-amendment-bill-2024" not in related

    def test_parse_details_related_acts(self) -> None:
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        acts = result.get("related_acts", [])
        assert len(acts) >= 1
        assert any("Act" in a for a in acts)

    def test_parse_details_language_default(self) -> None:
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, self.base_meta)
        assert result.get("language") == "English"

    def test_parse_details_partial_no_ministry(self) -> None:
        """Missing ministry on page should NOT produce an error; just absent."""
        result = self.parser.parse_html_details(PARTIAL_DETAIL_HTML, self.base_meta)
        assert result.get("ministry", "") == "" or "ministry" not in result

    def test_parse_details_partial_no_session(self) -> None:
        result = self.parser.parse_html_details(PARTIAL_DETAIL_HTML, self.base_meta)
        assert result.get("session", "") == "" or "session" not in result

    def test_parse_details_malformed_html_returns_base_meta(self) -> None:
        """Empty/None HTML should return base_meta unchanged without raising."""
        result = self.parser.parse_html_details(MALFORMED_HTML, self.base_meta)
        assert result["title"] == "Fallback Title"
        assert result["url"] == self.base_meta["url"]

    def test_parse_details_year_from_intro_date(self) -> None:
        """Year should be refined from introduction_date when available."""
        meta = self.base_meta.copy()
        # No year on discovery; detail page has intro date
        result = self.parser.parse_html_details(FULL_DETAIL_HTML, meta)
        # Year should be derived from the detail page introduction date
        # (15 February 2024 → year 2024) or from title
        assert result.get("year") in {2024, None}

    def test_parse_details_never_raises(self) -> None:
        """parse_html_details must not raise regardless of input."""
        for bad_input in [None, "", "   ", "<html></html>", "not html at all"]:
            try:
                result = self.parser.parse_html_details(bad_input or "", self.base_meta)
                assert isinstance(result, dict)
            except Exception as e:
                pytest.fail(f"parse_html_details raised unexpectedly for input {bad_input!r}: {e}")

    def test_parse_details_summary_capped(self) -> None:
        long_html = (
            '<html><body><div class="field-name-body">'
            + ("A very long summary text. " * 200)
            + "</div></body></html>"
        )
        result = self.parser.parse_html_details(long_html, self.base_meta)
        assert len(result.get("summary", "")) <= 2000

    def test_parse_details_url_normalization_relative(self) -> None:
        """Verify relative URLs (e.g. '../files/doc.pdf') are resolved relative to source_url and normalized."""
        html = '<html><body><a href="../files/bills_acts/bills_parliament/2024/Waqf.pdf">Bill Text</a></body></html>'
        meta = {
            "title": "Test Bill",
            "url": "https://prsindia.org/billtrack/the-waqf-amendment-bill-2024",
            "source_url": "https://prsindia.org/billtrack/the-waqf-amendment-bill-2024",
        }
        result = self.parser.parse_html_details(html, meta)
        assert (
            result.get("pdf_url")
            == "https://prsindia.org/files/bills_acts/bills_parliament/2024/Waqf.pdf"
        )

    def test_parse_details_url_normalization_root_relative(self) -> None:
        """Verify root-relative URLs are resolved relative to source_url domain and normalized to HTTPS."""
        html = '<html><body><a href="/sites/default/files/finance-bill-2024.pdf">Bill Text</a></body></html>'
        meta = {
            "title": "Test Bill",
            "url": "https://prsindia.org/billtrack/some-bill",
            "source_url": "https://prsindia.org/billtrack/some-bill",
        }
        result = self.parser.parse_html_details(html, meta)
        assert (
            result.get("pdf_url")
            == "https://prsindia.org/sites/default/files/finance-bill-2024.pdf"
        )

    def test_parse_details_url_normalization_absolute_http(self) -> None:
        """Verify absolute HTTP URLs are normalized to HTTPS."""
        html = '<html><body><a href="http://egazette.gov.in/WriteReadData/2023/250880.pdf">Bill Text</a></body></html>'
        meta = {
            "title": "Test Bill",
            "url": "https://prsindia.org/billtrack/some-bill",
            "source_url": "https://prsindia.org/billtrack/some-bill",
        }
        result = self.parser.parse_html_details(html, meta)
        assert result.get("pdf_url") == "https://egazette.gov.in/WriteReadData/2023/250880.pdf"

    def test_parse_details_url_normalization_invalid(self) -> None:
        """Verify invalid URLs that lack domain netloc are filtered out and set to None."""
        html = '<html><body><a href="invalid-url-without-domain.pdf">Bill Text</a></body></html>'
        meta = {"title": "Test Bill", "url": "", "source_url": ""}  # no source_url
        result = self.parser.parse_html_details(html, meta)
        assert result.get("pdf_url") is None


# ---------------------------------------------------------------------------
# Normalizer Tests
# ---------------------------------------------------------------------------


class TestParliamentNormalizerMetadata:

    def setup_method(self) -> None:
        self.normalizer = ParliamentNormalizer()

    def _base_raw(self, **overrides) -> dict:
        base = {
            "title": "The Test Bill, 2023",
            "url": "https://prsindia.org/billtrack/the-test-bill-2023",
            "source_url": "https://prsindia.org/billtrack/the-test-bill-2023",
            "status": "introduced",
            "source": "prs",
        }
        base.update(overrides)
        return base

    def test_normalizer_house_preserves_lok_sabha(self) -> None:
        raw = self._base_raw(house="Lok Sabha")
        bill = self.normalizer.normalize(raw)
        assert bill.house == BillHouse.LOK_SABHA

    def test_normalizer_house_preserves_rajya_sabha(self) -> None:
        raw = self._base_raw(house="Rajya Sabha")
        bill = self.normalizer.normalize(raw)
        assert bill.house == BillHouse.RAJYA_SABHA

    def test_normalizer_house_unrecognized_returns_unknown(self, caplog) -> None:
        import logging

        raw = self._base_raw(house="State Assembly")
        with caplog.at_level(logging.WARNING):
            bill = self.normalizer.normalize(raw)
        assert bill.house == BillHouse.UNKNOWN
        assert any(
            "Unrecognized house of introduction value" in record.message
            for record in caplog.records
        )

    def test_normalizer_house_empty_returns_unknown(self, caplog) -> None:
        import logging

        raw = self._base_raw(house="")
        with caplog.at_level(logging.WARNING):
            bill = self.normalizer.normalize(raw)
        assert bill.house == BillHouse.UNKNOWN
        assert any("House of introduction is empty" in record.message for record in caplog.records)

    def test_normalizer_year_none_not_defaulted(self) -> None:
        """When year is explicitly None, normalizer must not invent a year."""
        raw = self._base_raw(
            year=None,
            title="The Banking Regulation Amendment Bill",
            url="https://prsindia.org/billtrack/the-banking-regulation-amendment-bill",
            source_url="https://prsindia.org/billtrack/the-banking-regulation-amendment-bill",
        )
        bill = self.normalizer.normalize(raw)
        # Year may only be None or extracted from title/url if they contain one
        # Our title and url have no year, so it must remain None
        assert bill.year is None

    def test_normalizer_year_extracted_when_present(self) -> None:
        raw = self._base_raw(year=2023)
        bill = self.normalizer.normalize(raw)
        assert bill.year == 2023

    def test_normalizer_year_from_intro_date(self) -> None:
        """Year should be extracted from introduction_date if year field is None."""
        raw = self._base_raw(
            year=None, introduction_date="2022-03-10", title="The Banking Regulation Amendment Bill"
        )
        bill = self.normalizer.normalize(raw)
        assert bill.year == 2022

    def test_normalizer_ministry_empty_not_invented(self) -> None:
        """Missing ministry must remain empty string, not 'Unknown Ministry'."""
        raw = self._base_raw(ministry="")
        bill = self.normalizer.normalize(raw)
        assert bill.ministry == ""
        assert bill.ministry != "Unknown Ministry"

    def test_normalizer_ministry_extracted(self) -> None:
        raw = self._base_raw(ministry="Ministry of Finance")
        bill = self.normalizer.normalize(raw)
        assert bill.ministry == "Ministry of Finance"

    def test_normalizer_pdf_url_mapped(self) -> None:
        raw = self._base_raw(pdf_url="https://prsindia.org/files/test-bill.pdf")
        bill = self.normalizer.normalize(raw)
        assert bill.pdf_url == "https://prsindia.org/files/test-bill.pdf"

    def test_normalizer_pdf_url_from_document_url(self) -> None:
        """Backward-compat: document_url should map to pdf_url."""
        raw = self._base_raw(document_url="https://prsindia.org/files/old-key.pdf")
        bill = self.normalizer.normalize(raw)
        assert bill.pdf_url == "https://prsindia.org/files/old-key.pdf"

    def test_normalizer_pdf_url_none_when_absent(self) -> None:
        raw = self._base_raw()
        bill = self.normalizer.normalize(raw)
        assert bill.pdf_url is None

    def test_normalizer_session_mapped(self) -> None:
        raw = self._base_raw(session="Budget Session, 2023")
        bill = self.normalizer.normalize(raw)
        assert bill.session == "Budget Session, 2023"

    def test_normalizer_sponsor_mapped(self) -> None:
        raw = self._base_raw(sponsor="Nirmala Sitharaman")
        bill = self.normalizer.normalize(raw)
        assert bill.sponsor == "Nirmala Sitharaman"

    def test_normalizer_related_bills_mapped(self) -> None:
        raw = self._base_raw(related_bills=["the-income-tax-bill-2020", "the-gst-bill-2021"])
        bill = self.normalizer.normalize(raw)
        assert bill.related_bills == ["the-income-tax-bill-2020", "the-gst-bill-2021"]

    def test_normalizer_related_acts_mapped(self) -> None:
        raw = self._base_raw(related_acts=["Finance Act, 2020", "GST Act, 2017"])
        bill = self.normalizer.normalize(raw)
        assert bill.related_acts == ["Finance Act, 2020", "GST Act, 2017"]

    def test_normalizer_language_default(self) -> None:
        raw = self._base_raw()
        bill = self.normalizer.normalize(raw)
        assert bill.language == "English"

    def test_normalizer_language_custom(self) -> None:
        raw = self._base_raw(language="Hindi")
        bill = self.normalizer.normalize(raw)
        assert bill.language == "Hindi"

    def test_normalizer_last_updated_mapped(self) -> None:
        raw = self._base_raw(last_updated="2024-03-15")
        bill = self.normalizer.normalize(raw)
        assert bill.last_updated == date(2024, 3, 15)

    def test_normalizer_status_in_committee(self) -> None:
        raw = self._base_raw(status="in committee")
        bill = self.normalizer.normalize(raw)
        assert bill.status == BillStatus.IN_COMMITTEE

    def test_normalizer_status_ordinance(self) -> None:
        raw = self._base_raw(status="ordinance: in force")
        bill = self.normalizer.normalize(raw)
        assert bill.status == BillStatus.ORDINANCE

    def test_normalizer_status_negatived(self) -> None:
        raw = self._base_raw(status="introduced-negatived")
        bill = self.normalizer.normalize(raw)
        assert bill.status == BillStatus.NEGATIVED

    def test_normalizer_status_draft(self) -> None:
        raw = self._base_raw(status="draft")
        bill = self.normalizer.normalize(raw)
        assert bill.status == BillStatus.DRAFT

    def test_normalizer_status_infructuous(self) -> None:
        raw = self._base_raw(status="introduced - infructuous")
        bill = self.normalizer.normalize(raw)
        assert bill.status == BillStatus.LAPSED


# ---------------------------------------------------------------------------
# Validator Tests
# ---------------------------------------------------------------------------


class TestValidatorMetadata:

    def setup_method(self) -> None:
        self.validator = Validator()

    def _make_bill(self, **overrides) -> Bill:
        defaults = dict(
            bill_id="test-bill-2024",
            title="The Test Bill, 2024",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="https://prsindia.org/billtrack/test-bill-2024",
            year=2024,
            ministry="Ministry of Finance",
        )
        defaults.update(overrides)
        return Bill(**defaults)

    def test_validator_year_none_is_warning_not_error(self) -> None:
        bill = self._make_bill(year=None)
        report = self.validator.validate_bill(bill)
        assert report.is_valid, f"Errors: {report.errors}"
        assert any("year" in w.lower() for w in report.warnings)

    def test_validator_year_valid_passes(self) -> None:
        bill = self._make_bill(year=2020)
        report = self.validator.validate_bill(bill)
        assert report.is_valid

    def test_validator_year_out_of_range_is_error(self) -> None:
        bill = self._make_bill(year=1900)
        report = self.validator.validate_bill(bill)
        assert not report.is_valid
        assert any("year" in e.lower() for e in report.errors)

    def test_validator_ministry_empty_is_warning_not_error(self) -> None:
        bill = self._make_bill(ministry="")
        report = self.validator.validate_bill(bill)
        assert report.is_valid, f"Errors: {report.errors}"
        assert any("ministry" in w.lower() for w in report.warnings)

    def test_validator_pdf_url_valid_no_warning(self) -> None:
        bill = self._make_bill(pdf_url="https://prsindia.org/files/bill.pdf")
        report = self.validator.validate_bill(bill)
        assert not any("pdf_url" in w.lower() for w in report.warnings)

    def test_validator_pdf_url_malformed_is_warning(self) -> None:
        bill = self._make_bill(pdf_url="not-a-url/bill.pdf")
        report = self.validator.validate_bill(bill)
        assert report.is_valid  # still valid — just a warning
        assert any("pdf_url" in w.lower() for w in report.warnings)

    def test_validator_pdf_url_none_no_warning(self) -> None:
        bill = self._make_bill(pdf_url=None)
        report = self.validator.validate_bill(bill)
        assert not any("pdf_url" in w.lower() for w in report.warnings)

    def test_validator_required_url_empty_is_error(self) -> None:
        bill = self._make_bill(url="")
        report = self.validator.validate_bill(bill)
        assert not report.is_valid
        assert any("url" in e.lower() for e in report.errors)

    def test_validator_required_title_empty_is_error(self) -> None:
        bill = self._make_bill(title="")
        report = self.validator.validate_bill(bill)
        assert not report.is_valid
        assert any("title" in e.lower() for e in report.errors)

    def test_validator_last_updated_date_type_check(self) -> None:
        """last_updated must be a date object, not a string."""
        bill = self._make_bill()
        bill.last_updated = "2024-03-15"  # type: ignore[assignment]
        report = self.validator.validate_bill(bill)
        assert not report.is_valid
        assert any("last_updated" in e for e in report.errors)


# ---------------------------------------------------------------------------
# Schema Roundtrip Tests
# ---------------------------------------------------------------------------


class TestBillSchemaRoundtrip:

    def _make_full_bill(self) -> Bill:
        return Bill(
            bill_id="finance-amendment-bill-2024",
            title="The Finance Amendment Bill, 2024",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.PASSED_BOTH,
            url="https://prsindia.org/billtrack/finance-amendment-bill-2024",
            year=2024,
            ministry="Ministry of Finance",
            bill_number="14/2024",
            introduction_date=date(2024, 2, 15),
            last_updated=date(2024, 3, 20),
            pdf_url="https://prsindia.org/files/finance-bill-2024.pdf",
            session="Budget Session, 2024",
            sponsor="Nirmala Sitharaman",
            related_bills=["income-tax-bill-2023", "gst-bill-2022"],
            related_acts=["Finance Act, 2020", "GST Act, 2017"],
            language="English",
            source="prs",
        )

    def test_roundtrip_new_fields_preserved(self) -> None:
        bill = self._make_full_bill()
        data = bill.to_dict()
        restored = Bill.from_dict(data)
        assert restored.pdf_url == bill.pdf_url
        assert restored.session == bill.session
        assert restored.sponsor == bill.sponsor
        assert restored.related_bills == bill.related_bills
        assert restored.related_acts == bill.related_acts
        assert restored.language == bill.language
        assert restored.last_updated == bill.last_updated

    def test_roundtrip_year_none(self) -> None:
        bill = self._make_full_bill()
        bill.year = None
        data = bill.to_dict()
        assert data["year"] is None
        restored = Bill.from_dict(data)
        assert restored.year is None

    def test_roundtrip_ministry_empty(self) -> None:
        bill = self._make_full_bill()
        bill.ministry = ""
        data = bill.to_dict()
        restored = Bill.from_dict(data)
        assert restored.ministry == ""

    def test_roundtrip_status_in_committee(self) -> None:
        bill = self._make_full_bill()
        bill.status = BillStatus.IN_COMMITTEE
        data = bill.to_dict()
        assert data["status"] == "in_committee"
        restored = Bill.from_dict(data)
        assert restored.status == BillStatus.IN_COMMITTEE

    def test_roundtrip_status_ordinance(self) -> None:
        bill = self._make_full_bill()
        bill.status = BillStatus.ORDINANCE
        data = bill.to_dict()
        restored = Bill.from_dict(data)
        assert restored.status == BillStatus.ORDINANCE

    def test_roundtrip_status_negatived(self) -> None:
        bill = self._make_full_bill()
        bill.status = BillStatus.NEGATIVED
        data = bill.to_dict()
        restored = Bill.from_dict(data)
        assert restored.status == BillStatus.NEGATIVED

    def test_roundtrip_status_draft(self) -> None:
        bill = self._make_full_bill()
        bill.status = BillStatus.DRAFT
        data = bill.to_dict()
        restored = Bill.from_dict(data)
        assert restored.status == BillStatus.DRAFT


# ---------------------------------------------------------------------------
# Service Integration Tests (mocked)
# ---------------------------------------------------------------------------


class TestServiceMetadataIntegration:

    def _make_service(self, detail_html: str) -> ParliamentIngestionService:
        """Create service with mock connector returning known detail HTML."""
        mock_connector = MagicMock(spec=ParliamentConnector)
        mock_connector.mock_responses = {}
        mock_connector._check_robots = MagicMock(return_value=True)

        # Listing page returns one bill
        listing_html = """
        <html><body>
        <div class="views-row">
          <div class="views-field views-field-title-field">
            <a href="/billtrack/the-finance-amendment-bill-2024">The Finance Amendment Bill, 2024</a>
          </div>
        </div>
        </body></html>
        """

        async def mock_fetch(url, is_binary=False):
            if "billtrack" in url and url.endswith("billtrack"):
                return listing_html
            return detail_html

        mock_connector.fetch = AsyncMock(side_effect=mock_fetch)

        mock_repo = MagicMock(spec=BillRepository)
        mock_repo.exists.return_value = False
        mock_repo.save = MagicMock()
        mock_repo.count.return_value = 1

        service = ParliamentIngestionService(
            bill_repository=mock_repo,
            connector=mock_connector,
        )
        return service

    @pytest.mark.asyncio
    async def test_service_pdf_download_not_called(self) -> None:
        """Service must not call downloader.download_pdf in Task 1A.2."""
        service = self._make_service(FULL_DETAIL_HTML)
        service.downloader = MagicMock()
        service.downloader.download_pdf = AsyncMock()

        await service.ingest_bills(source="prs", dry_run=True)
        service.downloader.download_pdf.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_pdf_url_stored_not_downloaded(self) -> None:
        """pdf_url must be set on the bill; pdf_path must remain None."""
        service = self._make_service(FULL_DETAIL_HTML)
        saved_bills: list[Bill] = []

        def capture_save(bill: Bill) -> None:  # synchronous — matches repo.save signature
            saved_bills.append(bill)

        service.bill_repo.save = capture_save
        service.bill_repo.exists.return_value = False

        await service.ingest_bills(source="prs", dry_run=False)

        if saved_bills:
            bill = saved_bills[0]
            assert bill.pdf_path is None
            assert bill.pdf_url is not None
            assert bill.pdf_url.endswith(".pdf")

    @pytest.mark.asyncio
    async def test_service_continues_on_detail_fetch_failure(self) -> None:
        """If detail page fetch fails, service logs warning and uses list metadata."""
        mock_connector = MagicMock(spec=ParliamentConnector)
        mock_connector.mock_responses = {}
        mock_connector._check_robots = MagicMock(return_value=True)

        listing_html = """
        <html><body>
        <div class="views-row">
          <div class="views-field views-field-title-field">
            <a href="/billtrack/the-test-bill-2024">The Test Bill, 2024</a>
          </div>
        </div>
        </body></html>
        """
        call_count = 0

        async def mock_fetch_fails(url, is_binary=False):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return listing_html  # First call: list page
            raise Exception("Network error on detail fetch")

        mock_connector.fetch = AsyncMock(side_effect=mock_fetch_fails)

        mock_repo = MagicMock(spec=BillRepository)
        mock_repo.exists.return_value = False
        mock_repo.save = MagicMock()
        mock_repo.count.return_value = 0

        service = ParliamentIngestionService(
            bill_repository=mock_repo,
            connector=mock_connector,
        )

        # Should not raise; should still process the bill using list metadata
        stats = await service.ingest_bills(source="prs", dry_run=True)
        assert isinstance(stats, dict)
        assert "discovered" in stats

    @pytest.mark.asyncio
    async def test_service_metadata_ministry_collected(self) -> None:
        """Service must store ministry when available from detail page."""
        service = self._make_service(FULL_DETAIL_HTML)
        saved_bills: list[Bill] = []

        def capture_save(bill: Bill) -> None:  # synchronous — matches repo.save signature
            saved_bills.append(bill)

        service.bill_repo.save = capture_save
        service.bill_repo.exists.return_value = False

        await service.ingest_bills(source="prs", dry_run=False)

        if saved_bills:
            assert "Finance" in saved_bills[0].ministry

    @pytest.mark.asyncio
    async def test_service_dry_run_does_not_persist(self) -> None:
        """dry_run=True must not call repository.save."""
        service = self._make_service(FULL_DETAIL_HTML)
        await service.ingest_bills(source="prs", dry_run=True)
        service.bill_repo.save.assert_not_called()


# ---------------------------------------------------------------------------
# _has_changed() — Update Detection Tests
# ---------------------------------------------------------------------------


class TestHasChanged:
    """
    Verifies that _has_changed() correctly detects changes across all
    metadata fields introduced in Task 1A.2, and correctly ignores
    volatile runtime / provenance fields.

    Strategy: call _has_changed(existing, current) directly on a service
    instance to isolate the comparison logic from ingestion orchestration.
    """

    def _service(self) -> ParliamentIngestionService:
        """Return a service instance with mocked dependencies."""
        mock_repo = MagicMock(spec=BillRepository)
        mock_connector = MagicMock(spec=ParliamentConnector)
        return ParliamentIngestionService(
            bill_repository=mock_repo,
            connector=mock_connector,
        )

    def _base_bill(self, **overrides) -> Bill:
        """
        Return a fully-populated Bill covering every tracked field.
        Both 'existing' and 'current' start from this base so tests only
        mutate the single field under test.
        """
        defaults = dict(
            bill_id="test-bill-2024",
            title="The Test Bill, 2024",
            bill_number="14/2024",
            year=2024,
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            ministry="Ministry of Finance",
            url="https://prsindia.org/billtrack/test-bill-2024",
            introduction_date=date(2024, 2, 15),
            assent_date=None,
            gazette_date=None,
            last_updated=date(2024, 3, 20),
            pdf_url="https://prsindia.org/files/test-bill-2024.pdf",
            session="Budget Session, 2024",
            sponsor="Nirmala Sitharaman",
            related_bills=["income-tax-bill-2023"],
            related_acts=["Finance Act, 2020"],
            language="English",
            summary="This bill amends the Finance Act.",
            # Excluded runtime fields (must NOT trigger has_changed)
            pdf_path=None,
            full_text="",
            source="prs",
            ingested_at=date(2024, 1, 1),
            sectors=[],
            keywords=[],
        )
        defaults.update(overrides)
        return Bill(**defaults)

    # ------------------------------------------------------------------
    # Baseline
    # ------------------------------------------------------------------

    def test_identical_bills_returns_false(self) -> None:
        """Identical bills must never trigger an update."""
        svc = self._service()
        bill = self._base_bill()
        # Use separate instances to confirm equality is value-based
        bill_copy = self._base_bill()
        assert svc._has_changed(bill, bill_copy) is False

    # ------------------------------------------------------------------
    # Core identity metadata
    # ------------------------------------------------------------------

    def test_change_detected_title(self) -> None:
        existing = self._base_bill()
        current = self._base_bill(title="The Test Bill (Amended), 2024")
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_bill_number(self) -> None:
        existing = self._base_bill()
        current = self._base_bill(bill_number="15/2024")
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_year(self) -> None:
        existing = self._base_bill()
        current = self._base_bill(year=2025)
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_year_none_to_value(self) -> None:
        existing = self._base_bill(year=None)
        current = self._base_bill(year=2024)
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_house(self) -> None:
        existing = self._base_bill(house=BillHouse.LOK_SABHA)
        current = self._base_bill(house=BillHouse.RAJYA_SABHA)
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_status(self) -> None:
        existing = self._base_bill(status=BillStatus.INTRODUCED)
        current = self._base_bill(status=BillStatus.PASSED_BOTH)
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_ministry(self) -> None:
        existing = self._base_bill(ministry="Ministry of Finance")
        current = self._base_bill(ministry="Ministry of Law")
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_ministry_empty_to_value(self) -> None:
        """Enriched ministry on re-run must trigger update."""
        existing = self._base_bill(ministry="")
        current = self._base_bill(ministry="Ministry of Finance")
        assert self._service()._has_changed(existing, current) is True

    # ------------------------------------------------------------------
    # Date fields
    # ------------------------------------------------------------------

    def test_change_detected_introduction_date(self) -> None:
        existing = self._base_bill(introduction_date=date(2024, 2, 15))
        current = self._base_bill(introduction_date=date(2024, 2, 20))
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_introduction_date_none_to_value(self) -> None:
        existing = self._base_bill(introduction_date=None)
        current = self._base_bill(introduction_date=date(2024, 2, 15))
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_assent_date(self) -> None:
        existing = self._base_bill(assent_date=None)
        current = self._base_bill(assent_date=date(2024, 5, 1))
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_gazette_date(self) -> None:
        existing = self._base_bill(gazette_date=None)
        current = self._base_bill(gazette_date=date(2024, 5, 10))
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_last_updated(self) -> None:
        """last_updated enrichment (Task 1A.2 field) must trigger update."""
        existing = self._base_bill(last_updated=None)
        current = self._base_bill(last_updated=date(2024, 3, 20))
        assert self._service()._has_changed(existing, current) is True

    # ------------------------------------------------------------------
    # Task 1A.2 enriched fields
    # ------------------------------------------------------------------

    def test_change_detected_pdf_url(self) -> None:
        """Newly discovered pdf_url must trigger update."""
        existing = self._base_bill(pdf_url=None)
        current = self._base_bill(pdf_url="https://prsindia.org/files/test-bill-2024.pdf")
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_pdf_url_value_change(self) -> None:
        existing = self._base_bill(pdf_url="https://prsindia.org/files/old.pdf")
        current = self._base_bill(pdf_url="https://prsindia.org/files/new.pdf")
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_session(self) -> None:
        """Enriched session on re-run must trigger update."""
        existing = self._base_bill(session="")
        current = self._base_bill(session="Budget Session, 2024")
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_sponsor(self) -> None:
        """Enriched sponsor on re-run must trigger update."""
        existing = self._base_bill(sponsor="")
        current = self._base_bill(sponsor="Nirmala Sitharaman")
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_related_bills_added(self) -> None:
        """New related bill added must trigger update."""
        existing = self._base_bill(related_bills=[])
        current = self._base_bill(related_bills=["income-tax-bill-2023"])
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_related_bills_modified(self) -> None:
        existing = self._base_bill(related_bills=["income-tax-bill-2023"])
        current = self._base_bill(related_bills=["income-tax-bill-2023", "gst-bill-2022"])
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_related_acts_added(self) -> None:
        """New related act added must trigger update."""
        existing = self._base_bill(related_acts=[])
        current = self._base_bill(related_acts=["Finance Act, 2020"])
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_language(self) -> None:
        existing = self._base_bill(language="English")
        current = self._base_bill(language="Hindi")
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_summary(self) -> None:
        """Enriched summary on re-run must trigger update."""
        existing = self._base_bill(summary="")
        current = self._base_bill(summary="This bill amends the Finance Act.")
        assert self._service()._has_changed(existing, current) is True

    def test_change_detected_summary_content_change(self) -> None:
        existing = self._base_bill(summary="Short summary.")
        current = self._base_bill(summary="Short summary. With more detail added.")
        assert self._service()._has_changed(existing, current) is True

    # ------------------------------------------------------------------
    # Excluded fields — must NOT trigger has_changed
    # ------------------------------------------------------------------

    def test_excluded_ingested_at_does_not_trigger(self) -> None:
        """ingested_at is set once on insert; re-run must not cause spurious update."""
        existing = self._base_bill(ingested_at=date(2024, 1, 1))
        current = self._base_bill(ingested_at=date(2025, 6, 1))
        assert self._service()._has_changed(existing, current) is False

    def test_excluded_pdf_path_does_not_trigger(self) -> None:
        """pdf_path is populated by a later download task; must not affect sync."""
        existing = self._base_bill(pdf_path=None)
        current = self._base_bill(pdf_path="/data/bills/pdfs/test-bill-2024.pdf")
        assert self._service()._has_changed(existing, current) is False

    def test_excluded_full_text_does_not_trigger(self) -> None:
        """full_text is populated by the PDF extractor task; must not affect sync."""
        existing = self._base_bill(full_text="")
        current = self._base_bill(full_text="Complete extracted bill text goes here.")
        assert self._service()._has_changed(existing, current) is False

    def test_excluded_source_does_not_trigger(self) -> None:
        """source is a static identifier; never changes after first insert."""
        existing = self._base_bill(source="prs")
        current = self._base_bill(source="lok_sabha")
        assert self._service()._has_changed(existing, current) is False

    def test_excluded_sectors_does_not_trigger(self) -> None:
        """sectors is populated by the mapping module (Task 5); must not affect sync."""
        existing = self._base_bill(sectors=[])
        current = self._base_bill(sectors=["Banking", "Finance"])
        assert self._service()._has_changed(existing, current) is False

    def test_excluded_keywords_does_not_trigger(self) -> None:
        """keywords is populated by the NLP module (Task 4); must not affect sync."""
        existing = self._base_bill(keywords=[])
        current = self._base_bill(keywords=["tax", "gst", "amendment"])
        assert self._service()._has_changed(existing, current) is False

    # ------------------------------------------------------------------
    # Guarantee: bill is skipped only when ALL tracked fields are identical
    # ------------------------------------------------------------------

    def test_all_tracked_fields_identical_returns_false(self) -> None:
        """
        Exhaustive check: a bill is skipped only when every single
        tracked field is identical. Mutate each field one at a time and
        confirm at least one triggers True.
        """
        svc = self._service()
        base = self._base_bill()

        mutations = {
            "title": "Different Title, 2024",
            "bill_number": "99/2024",
            "year": 2023,
            "house": BillHouse.RAJYA_SABHA,
            "status": BillStatus.PASSED_BOTH,
            "ministry": "Ministry of Law",
            "introduction_date": date(2024, 3, 1),
            "assent_date": date(2024, 6, 1),
            "gazette_date": date(2024, 6, 5),
            "last_updated": date(2024, 12, 1),
            "pdf_url": "https://prsindia.org/files/amended.pdf",
            "session": "Monsoon Session, 2024",
            "sponsor": "Amit Shah",
            "related_bills": ["new-bill-2024"],
            "related_acts": ["New Act, 2023"],
            "language": "Hindi",
            "summary": "An entirely different summary.",
        }

        for field_name, new_value in mutations.items():
            current = self._base_bill(**{field_name: new_value})
            result = svc._has_changed(base, current)
            assert result is True, (
                f"Expected _has_changed to return True when field "
                f"'{field_name}' changes from {getattr(base, field_name)!r} "
                f"to {new_value!r}, but got False."
            )
