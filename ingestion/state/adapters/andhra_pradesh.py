"""
ingestion/state/adapters/andhra_pradesh.py
==========================================
Source adapter for the Andhra Pradesh Legislature (aplegislature.org).
"""

from __future__ import annotations

import re
from typing import Any, Optional
import urllib.parse
from bs4 import BeautifulSoup

from config.logging_config import get_logger
from ingestion.parliament.connector import ParliamentConnector
from ingestion.state.base_adapter import BaseStateSourceAdapter
from schemas.bill import BillHouse
from schemas.state_source import StateBillSource
from utils.text_utils import clean_text

logger = get_logger(__name__)


class AndhraPradeshSourceAdapter(BaseStateSourceAdapter):
    """
    Adapter for scraping and parsing bills from the official Andhra Pradesh Legislature portal.
    """

    def __init__(
        self,
        source: Optional[StateBillSource] = None,
        connector: Optional[ParliamentConnector] = None,
    ) -> None:
        if source is None:
            source = StateBillSource(
                state="Andhra Pradesh",
                legislature="Andhra Pradesh Legislative Assembly",
                source_name="andhra_pradesh_assembly",
                base_url="https://aplegislature.org",
                listing_url="https://aplegislature.org/web/aplegislature/bills",
                document_url_pattern="https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName={file_name}",
                house=BillHouse.VIDHAN_SABHA,
            )
        super().__init__(source=source, connector=connector)

    async def discover_bills(
        self,
        year: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch the bills listing page and extract bill metadata dictionaries.
        """
        logger.info("Discovering Andhra Pradesh bills from %s", self.source.listing_url)
        content = await self.connector.fetch(self.source.listing_url)
        if not content or not isinstance(content, str):
            logger.warning("Empty response received from %s", self.source.listing_url)
            return []

        return self.parse_listing_html(content, target_year=year, limit=limit)

    def parse_listing_html(
        self,
        html_content: str,
        target_year: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Parse bill entries from HTML content.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        bills: list[dict[str, Any]] = []

        # Find all anchors that match the bill pattern
        anchors = soup.find_all("a")
        for a in anchors:
            text = clean_text(a.get_text())
            href = a.get("href", "").strip()

            # Pattern: The [Name] Bill, [Year] (L.A. Bill No.[N] of [Year])
            if "Bill" not in text:
                continue

            bill_match = re.search(
                r"^(.*?Bill(?:,\s*\d{4})?)\s*\((.*?Bill\s*No\.?\s*(\d+)\s*(?:of\s*(\d{4}))?)\)",
                text,
                re.IGNORECASE,
            )

            if bill_match:
                title_clean = clean_text(bill_match.group(1))
                full_bill_no = clean_text(bill_match.group(2))
                raw_year = bill_match.group(4)
                bill_year = int(raw_year) if raw_year else None
            else:
                # Less strict pattern for titles like: "The Factories (Andhra Pradesh Amendment) Bill, 2025"
                m2 = re.search(r"Bill,\s*(\d{4})", text)
                if not m2 and not ("Bill" in text and ("202" in text or "201" in text)):
                    continue
                title_clean = text
                full_bill_no = None
                bill_year = int(m2.group(1)) if m2 else None

            # Filter by target_year if requested
            if target_year and bill_year and bill_year != target_year:
                continue

            # Resolve document URL
            doc_url = None
            if href:
                if href.startswith("http"):
                    doc_url = href
                else:
                    doc_url = urllib.parse.urljoin(self.source.base_url, href)

            record = {
                "title": title_clean,
                "bill_number": full_bill_no,
                "year": bill_year,
                "state": self.source.state,
                "legislature": self.source.legislature,
                "house": self.source.house.value,
                "url": self.source.listing_url,
                "source_url": self.source.listing_url,
                "pdf_url": doc_url,
                "status": "passed_both" if "passedbills" in href.lower() or "act" in text.lower() else "introduced",
                "source_name": self.source.source_name,
            }

            # Avoid duplicates within the same page parse
            if not any(b["title"] == record["title"] for b in bills):
                bills.append(record)
                if limit and len(bills) >= limit:
                    break

        logger.info("Extracted %d bills from Andhra Pradesh portal listing", len(bills))
        return bills
