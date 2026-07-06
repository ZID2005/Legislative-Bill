"""
ingestion/parliament/normalizer.py
==================================
Data normalization service for legislative bills.

Maps parsed metadata dictionaries to the canonical Bill schema model.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from config.logging_config import get_logger
from schemas.bill import Bill, BillHouse, BillStatus
from utils.date_utils import parse_date
from utils.text_utils import clean_text, slugify, extract_bill_year

logger = get_logger(__name__)


class ParliamentNormalizer:
    """
    Normalizes raw scraped legislative dictionaries into standard Bill models.
    """

    def normalize(self, raw_data: dict[str, Any]) -> Bill:
        """
        Normalize a raw dictionary to a Bill object.

        Parameters
        ----------
        raw_data : dict
            Raw metadata dictionary from scraping/parsing.

        Returns
        -------
        Bill
            The normalized Bill instance.
        """
        raw_title = raw_data.get("title", "")
        title = clean_text(raw_title)
        if not title:
            # We will let validation catch empty titles later
            title = "Untitled Bill"

        # Generate bill_id slug
        bill_id = slugify(title)

        # Normalize year
        year_val = raw_data.get("year")
        year = None
        if year_val is not None:
            try:
                year = int(year_val)
            except (ValueError, TypeError):
                pass

        if year is None:
            year = extract_bill_year(title) or date.today().year

        # Normalize ministry
        raw_ministry = raw_data.get("ministry", "")
        ministry = clean_text(raw_ministry)
        if not ministry:
            ministry = "Unknown Ministry"

        # Normalize house of introduction
        raw_house = str(raw_data.get("house", "")).strip().lower()
        house = self._normalize_house(raw_house)

        # Normalize status
        raw_status = str(raw_data.get("status", "")).strip().lower()
        status = self._normalize_status(raw_status)

        # Normalize URL
        url = str(raw_data.get("url", "")).strip()

        # Parse date fields
        intro_date = parse_date(raw_data.get("introduction_date", ""))
        assent_date = parse_date(raw_data.get("assent_date", ""))
        gazette_date = parse_date(raw_data.get("gazette_date", ""))

        # Populate optional/derived fields
        bill_number = clean_text(str(raw_data.get("bill_number", "")))
        pdf_path = raw_data.get("pdf_path")
        summary = clean_text(raw_data.get("summary", ""))
        full_text = raw_data.get("full_text", "")
        sectors = raw_data.get("sectors", [])
        keywords = raw_data.get("keywords", [])
        source = raw_data.get("source", "prs")

        bill = Bill(
            bill_id=bill_id,
            title=title,
            year=year,
            ministry=ministry,
            house=house,
            status=status,
            url=url,
            bill_number=bill_number,
            introduction_date=intro_date,
            assent_date=assent_date,
            gazette_date=gazette_date,
            pdf_path=pdf_path,
            summary=summary,
            full_text=full_text,
            sectors=sectors,
            keywords=keywords,
            source=source,
            ingested_at=date.today(),
        )
        return bill

    def _normalize_house(self, raw_house: str) -> BillHouse:
        """Map raw house string to BillHouse enum."""
        if "rajya" in raw_house or "rs" == raw_house:
            return BillHouse.RAJYA_SABHA
        # Default/fall back to Lok Sabha
        return BillHouse.LOK_SABHA

    def _normalize_status(self, raw_status: str) -> BillStatus:
        """Map raw status string to BillStatus enum."""
        if not raw_status:
            return BillStatus.INTRODUCED

        if "introduced" in raw_status:
            return BillStatus.INTRODUCED
        elif "pending" in raw_status:
            return BillStatus.PENDING
        elif "withdrawn" in raw_status:
            return BillStatus.WITHDRAWN
        elif "lapsed" in raw_status:
            return BillStatus.LAPSED
        elif "assented" in raw_status or "act" in raw_status:
            return BillStatus.ASSENTED
        elif "passed by both" in raw_status or "passed" in raw_status:
            if "lok sabha" in raw_status:
                return BillStatus.PASSED_LOK_SABHA
            elif "rajya sabha" in raw_status:
                return BillStatus.PASSED_RAJYA_SABHA
            else:
                return BillStatus.PASSED_BOTH

        # Default fallback
        return BillStatus.INTRODUCED
