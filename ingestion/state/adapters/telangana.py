"""
ingestion/state/adapters/telangana.py
=====================================
Source adapter for the Telangana Legislature (Assembly & Council).
Official portal: https://legislature.telangana.gov.in.
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


class TelanganaSourceAdapter(BaseStateSourceAdapter):
    """
    Adapter for scraping and parsing bills from the official Telangana Legislature portal.
    """

    def __init__(
        self,
        source: Optional[StateBillSource] = None,
        connector: Optional[ParliamentConnector] = None,
        house: BillHouse = BillHouse.VIDHAN_SABHA,
    ) -> None:
        if source is None:
            source = StateBillSource(
                state="Telangana",
                legislature="Telangana Legislative Assembly" if house == BillHouse.VIDHAN_SABHA else "Telangana Legislative Council",
                source_name="telangana_assembly" if house == BillHouse.VIDHAN_SABHA else "telangana_council",
                base_url="https://legislature.telangana.gov.in",
                listing_url="https://legislature.telangana.gov.in/billsActs",
                detail_url_pattern="https://legislature.telangana.gov.in/assembly",
                document_url_pattern="https://legislature.telangana.gov.in/documents/{file_name}",
                source_type="html_table",
                house=house,
            )
        super().__init__(source=source, connector=connector)

    async def discover_bills(
        self,
        year: Optional[int] = None,
        limit: Optional[int] = None,
        session_url: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Discover Telangana bills by fetching the legislative business page.
        """
        target_url = session_url or self.source.listing_url
        logger.info("Discovering Telangana bills from %s", target_url)

        content = await self.connector.fetch(target_url)
        if not content or not isinstance(content, str):
            logger.warning("Empty response received from %s", target_url)
            return []

        return self.parse_listing_html(content, source_url=target_url, target_year=year, limit=limit)

    def parse_listing_html(
        self,
        html_content: str,
        source_url: Optional[str] = None,
        target_year: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Parse table rows or bill items from Telangana Legislature HTML.
        """
        url = source_url or self.source.listing_url
        soup = BeautifulSoup(html_content, "html.parser")
        bills: list[dict[str, Any]] = []

        # 1. Look for structured table
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for tr in rows:
                cols = tr.find_all("td")
                if len(cols) < 2:
                    continue

                col0_text = clean_text(cols[0].get_text())
                col1_text = clean_text(cols[1].get_text())

                # Skip non-bill rows
                text_block = f"{col0_text} {col1_text}"
                if "bill" not in text_block.lower():
                    continue

                # Bill number may be in col 0 or col 1
                bill_no = None
                title_text = col1_text
                if re.search(r"\b(?:L\.A\.|L\.C\.|Bill\s*No\.?)\b", col0_text, re.IGNORECASE):
                    bill_no = col0_text
                    title_text = col1_text
                elif re.search(r"\b(?:L\.A\.|L\.C\.|Bill\s*No\.?)\b", col1_text, re.IGNORECASE):
                    # Title might be in col0 or col2
                    if len(cols) > 2 and "bill" in clean_text(cols[2].get_text()).lower():
                        bill_no = col1_text
                        title_text = clean_text(cols[2].get_text())

                # Find document link
                pdf_url = None
                for c in cols:
                    anchor = c.find("a")
                    if anchor and anchor.get("href"):
                        raw_href = anchor.get("href").strip()
                        if raw_href and not raw_href.startswith("javascript"):
                            pdf_url = (
                                raw_href
                                if raw_href.startswith("http")
                                else urllib.parse.urljoin(url, raw_href)
                            )
                            break

                dates_found = []
                for c in cols:
                    txt = clean_text(c.get_text())
                    d_parsed = self._format_date(txt)
                    if d_parsed:
                        dates_found.append(d_parsed)

                intro_date = dates_found[0] if len(dates_found) > 0 else None
                assent_date = dates_found[1] if len(dates_found) > 1 else None

                # Extract year
                year_match = re.search(r"\b(20\d\d)\b", title_text)
                if not year_match and bill_no:
                    year_match = re.search(r"\b(20\d\d)\b", bill_no)
                if not year_match and intro_date:
                    year_match = re.search(r"^(20\d\d)", intro_date)
                bill_year = int(year_match.group(1)) if year_match else None

                if target_year and bill_year and bill_year != target_year:
                    continue

                status = "passed_both" if assent_date or "passed" in text_block.lower() else "introduced"

                record = {
                    "title": title_text,
                    "bill_number": bill_no or f"L.A. Bill of {bill_year}" if bill_year else "L.A. Bill",
                    "year": bill_year,
                    "state": self.source.state,
                    "legislature": self.source.legislature,
                    "house": self.source.house.value,
                    "url": url,
                    "source_url": url,
                    "pdf_url": pdf_url,
                    "introduction_date": intro_date,
                    "assent_date": assent_date,
                    "status": status,
                    "source_name": self.source.source_name,
                }

                if not any(b["title"] == record["title"] for b in bills):
                    bills.append(record)
                    if limit and len(bills) >= limit:
                        return bills

        # 2. Fallback: Parse anchors
        if not bills:
            anchors = soup.find_all("a")
            for a in anchors:
                text = clean_text(a.get_text())
                href = a.get("href", "").strip()

                if "bill" not in text.lower():
                    continue

                # Pattern: The [Name] Bill, [Year] (L.A. Bill No. [N] of [Year])
                m = re.search(
                    r"^(.*?Bill(?:,\s*\d{4})?)\s*(?:\(((?:L\.[AC]\.\s*)?Bill\s*No\.?\s*(\d+)\s*(?:of\s*(\d{4}))?)\))?",
                    text,
                    re.IGNORECASE,
                )
                if not m:
                    continue

                title_clean = clean_text(m.group(1))
                full_bill_no = clean_text(m.group(2)) if m.group(2) else None
                raw_year = m.group(4) if m.group(4) else None

                if not raw_year:
                    ym = re.search(r"\b(20\d\d)\b", title_clean)
                    raw_year = ym.group(1) if ym else None

                bill_year = int(raw_year) if raw_year else None
                if target_year and bill_year and bill_year != target_year:
                    continue

                doc_url = None
                if href and not href.startswith("javascript"):
                    doc_url = href if href.startswith("http") else urllib.parse.urljoin(url, href)

                record = {
                    "title": title_clean,
                    "bill_number": full_bill_no or (f"L.A. Bill No. {m.group(3)}" if m.group(3) else None),
                    "year": bill_year,
                    "state": self.source.state,
                    "legislature": self.source.legislature,
                    "house": self.source.house.value,
                    "url": url,
                    "source_url": url,
                    "pdf_url": doc_url,
                    "status": "passed_both" if "passed" in text.lower() or "passed" in url.lower() else "introduced",
                    "source_name": self.source.source_name,
                }

                if not any(b["title"] == record["title"] for b in bills):
                    bills.append(record)
                    if limit and len(bills) >= limit:
                        break

        logger.info("Extracted %d bills from Telangana Legislature listing", len(bills))
        return bills

    @staticmethod
    def _format_date(raw_date: str) -> Optional[str]:
        """Convert DD.MM.YYYY or DD/MM/YYYY or DD-MM-YYYY into YYYY-MM-DD."""
        if not raw_date:
            return None
        m = re.search(r"(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})", raw_date)
        if m:
            d, mth, y = m.groups()
            return f"{y}-{int(mth):02d}-{int(d):02d}"
        return None
