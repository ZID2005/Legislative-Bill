"""
ingestion/state/adapters/kerala.py
==================================
Source adapter for the Kerala Legislative Assembly (Niyamasabha).
Official portal: https://niyamasabha.nic.in (and legacy https://niyamasabha.org).
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


class KeralaSourceAdapter(BaseStateSourceAdapter):
    """
    Adapter for scraping and parsing bills from the official Kerala Legislative Assembly portal.
    """

    def __init__(
        self,
        source: Optional[StateBillSource] = None,
        connector: Optional[ParliamentConnector] = None,
    ) -> None:
        if source is None:
            source = StateBillSource(
                state="Kerala",
                legislature="Kerala Legislative Assembly",
                source_name="kerala_niyamasabha",
                base_url="https://niyamasabha.nic.in",
                listing_url="https://niyamasabha.nic.in/index.php/bills/billview/4",
                detail_url_pattern="https://niyamasabha.nic.in/index.php/bills/billview/{category_id}",
                document_url_pattern="https://niyamasabha.nic.in/index.php/bills/viewfile/{file_id}",
                source_type="html_table",
                house=BillHouse.VIDHAN_SABHA,
            )
        super().__init__(source=source, connector=connector)

    async def discover_bills(
        self,
        year: Optional[int] = None,
        limit: Optional[int] = None,
        category_url: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Discover Kerala bills by fetching the bill listing page.
        """
        target_url = category_url or self.source.listing_url
        logger.info("Discovering Kerala bills from %s", target_url)

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
        Parse table rows or anchor listings from Kerala Legislative Assembly HTML.
        """
        url = source_url or self.source.listing_url
        soup = BeautifulSoup(html_content, "html.parser")
        bills: list[dict[str, Any]] = []

        # 1. First attempt: Look for structured table (id='billsinformation' or class='table')
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for tr in rows:
                cols = tr.find_all("td")
                if len(cols) < 3:
                    continue

                # Col 0: Sl No, Col 1: Bill No, Col 2: Short Title
                col0_text = clean_text(cols[0].get_text())
                col1_text = clean_text(cols[1].get_text())

                # Skip header / empty details
                if "no details" in col0_text.lower() or "no details" in col1_text.lower():
                    continue

                bill_no_raw = col1_text if col1_text else col0_text
                title_col = cols[2] if len(cols) > 2 else cols[1]
                title_text = clean_text(title_col.get_text())

                if not title_text or "bill" not in title_text.lower():
                    continue

                # Col 3: Date of Introduction, Col 4: Assent Date
                intro_raw = clean_text(cols[3].get_text()) if len(cols) > 3 else ""
                assent_raw = clean_text(cols[4].get_text()) if len(cols) > 4 else ""

                intro_date = self._format_date(intro_raw)
                assent_date = self._format_date(assent_raw)

                # PDF Link in Bill column (col 5) or title column
                pdf_url = None
                for col_idx in [5, 2, 1]:
                    if len(cols) > col_idx:
                        anchor = cols[col_idx].find("a")
                        if anchor and anchor.get("href"):
                            raw_href = anchor.get("href").strip()
                            if raw_href and not raw_href.startswith("javascript"):
                                pdf_url = (
                                    raw_href
                                    if raw_href.startswith("http")
                                    else urllib.parse.urljoin(url, raw_href)
                                )
                                break

                # Extract year
                year_match = re.search(r"\b(20\d\d)\b", title_text)
                if not year_match and intro_date:
                    year_match = re.search(r"^(20\d\d)", intro_date)
                bill_year = int(year_match.group(1)) if year_match else None

                if target_year and bill_year and bill_year != target_year:
                    continue

                status = "passed_both"
                if assent_date:
                    status = "assented"
                elif "billview/2" in url:
                    status = "introduced"
                elif "billview/5" in url:
                    status = "assented"

                formatted_bill_no = f"Bill No. {bill_no_raw}" if bill_no_raw.isdigit() else bill_no_raw
                if bill_year and formatted_bill_no and " of " not in formatted_bill_no:
                    formatted_bill_no = f"{formatted_bill_no} of {bill_year}"

                record = {
                    "title": title_text,
                    "bill_number": formatted_bill_no,
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

        # 2. Fallback: Parse anchor links or list items
        if not bills:
            anchors = soup.find_all("a")
            for a in anchors:
                text = clean_text(a.get_text())
                href = a.get("href", "").strip()

                if "bill" not in text.lower():
                    continue

                # Pattern: The [Name] Bill, [Year] (Bill No. [N] of [Year])
                m = re.search(
                    r"^(.*?Bill(?:,\s*\d{4})?)\s*(?:\((.*?Bill\s*No\.?\s*(\d+)\s*(?:of\s*(\d{4}))?)\))?",
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
                    "bill_number": full_bill_no or (f"Bill No. {m.group(3)}" if m.group(3) else None),
                    "year": bill_year,
                    "state": self.source.state,
                    "legislature": self.source.legislature,
                    "house": self.source.house.value,
                    "url": url,
                    "source_url": url,
                    "pdf_url": doc_url,
                    "status": "passed_both" if "passed" in url.lower() or "passed" in text.lower() else "introduced",
                    "source_name": self.source.source_name,
                }

                if not any(b["title"] == record["title"] for b in bills):
                    bills.append(record)
                    if limit and len(bills) >= limit:
                        break

        logger.info("Extracted %d bills from Kerala Niyamasabha portal listing", len(bills))
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
