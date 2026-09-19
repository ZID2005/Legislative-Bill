"""
ingestion/state/adapters/karnataka.py
=====================================
Source adapter for the Karnataka Legislative Assembly (kla.kar.nic.in).
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


class KarnatakaSourceAdapter(BaseStateSourceAdapter):
    """
    Adapter for scraping and parsing bills from the official Karnataka Legislative Assembly portal.
    """

    def __init__(
        self,
        source: Optional[StateBillSource] = None,
        connector: Optional[ParliamentConnector] = None,
    ) -> None:
        if source is None:
            source = StateBillSource(
                state="Karnataka",
                legislature="Karnataka Legislative Assembly",
                source_name="karnataka_assembly",
                base_url="https://kla.kar.nic.in",
                listing_url="https://kla.kar.nic.in/assembly/bills/allbills.htm",
                detail_url_pattern="https://kla.kar.nic.in/assembly/bills/{session_file}",
                document_url_pattern="https://kla.kar.nic.in/assembly/bills/{pdf_file}",
                source_type="session_list",
                house=BillHouse.VIDHAN_SABHA,
            )
        super().__init__(source=source, connector=connector)

    async def discover_bills(
        self,
        year: Optional[int] = None,
        limit: Optional[int] = None,
        session_url: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Discover Karnataka bills by fetching the session bill listing.
        """
        target_url = session_url or "https://kla.kar.nic.in/assembly/bills/bills1640.htm"
        logger.info("Discovering Karnataka bills from %s", target_url)

        content = await self.connector.fetch(target_url)
        if not content or not isinstance(content, str):
            logger.warning("Empty response received from %s", target_url)
            return []

        return self.parse_session_html(content, source_url=target_url, target_year=year, limit=limit)

    def parse_session_html(
        self,
        html_content: str,
        source_url: str,
        target_year: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Parse table rows from a Karnataka session bills HTML page.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        bills: list[dict[str, Any]] = []

        # Find tables containing bill rows
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for tr in rows:
                cols = tr.find_all("td")
                if len(cols) < 3:
                    continue

                col0_text = clean_text(cols[0].get_text())
                # Must start with a number (Bill No)
                if not col0_text.isdigit():
                    continue

                bill_no = col0_text
                title_col = cols[1]
                title_text = clean_text(title_col.get_text())

                # PDF link
                pdf_anchor = title_col.find("a")
                pdf_url = None
                if pdf_anchor and pdf_anchor.get("href"):
                    raw_href = pdf_anchor.get("href").strip()
                    if raw_href.startswith("http"):
                        pdf_url = raw_href
                    else:
                        pdf_url = urllib.parse.urljoin(source_url, raw_href)

                intro_date_raw = clean_text(cols[2].get_text()) if len(cols) > 2 else ""
                assembly_pass_raw = clean_text(cols[3].get_text()) if len(cols) > 3 else ""
                council_pass_raw = clean_text(cols[4].get_text()) if len(cols) > 4 else ""
                assent_raw = clean_text(cols[5].get_text()) if len(cols) > 5 else ""
                remarks = clean_text(cols[6].get_text()) if len(cols) > 6 else ""

                # Format introduction date (DD.MM.YYYY -> YYYY-MM-DD)
                intro_date = self._format_date(intro_date_raw)
                assent_date = self._format_date(assent_raw)

                # Determine status
                if assent_date:
                    status = "passed_both"
                elif assembly_pass_raw and council_pass_raw:
                    status = "passed_both"
                elif assembly_pass_raw:
                    status = "passed_assembly"
                elif intro_date:
                    status = "introduced"
                else:
                    status = "pending"

                # Extract year
                year_match = re.search(r"\b(20\d\d)\b", title_text)
                if not year_match and intro_date:
                    year_match = re.search(r"^(20\d\d)", intro_date)
                bill_year = int(year_match.group(1)) if year_match else None

                if target_year and bill_year and bill_year != target_year:
                    continue

                record = {
                    "title": title_text,
                    "bill_number": f"Bill No. {bill_no} of {bill_year}" if bill_year else f"Bill No. {bill_no}",
                    "year": bill_year,
                    "state": self.source.state,
                    "legislature": self.source.legislature,
                    "house": self.source.house.value,
                    "url": source_url,
                    "source_url": source_url,
                    "pdf_url": pdf_url,
                    "introduction_date": intro_date,
                    "assent_date": assent_date,
                    "status": status,
                    "remarks": remarks,
                    "source_name": self.source.source_name,
                }

                bills.append(record)
                if limit and len(bills) >= limit:
                    break

            if bills:
                break

        logger.info("Extracted %d bills from Karnataka session listing", len(bills))
        return bills

    @staticmethod
    def _format_date(raw_date: str) -> Optional[str]:
        """Convert DD.MM.YYYY or DD/MM/YYYY into YYYY-MM-DD."""
        if not raw_date:
            return None
        m = re.search(r"(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})", raw_date)
        if m:
            d, mth, y = m.groups()
            return f"{y}-{int(mth):02d}-{int(d):02d}"
        return None
