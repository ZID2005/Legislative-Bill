"""
ingestion/parliament/normalizer.py
==================================
Data normalization service for legislative bills.

Maps parsed metadata dictionaries to the canonical Bill schema model.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.bill import Bill, BillHouse, BillStatus
from utils.date_utils import parse_date
from utils.text_utils import clean_text, slugify

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

        # Normalize year — None is preferable to an invented year
        year_val = raw_data.get("year")
        year: Optional[int] = None
        if year_val is not None:
            try:
                year = int(year_val)
            except (ValueError, TypeError):
                pass

        # Normalize ministry — empty string if unavailable; do NOT invent a value
        raw_ministry = raw_data.get("ministry", "")
        ministry = clean_text(str(raw_ministry)) if raw_ministry else ""

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
        last_updated = parse_date(raw_data.get("last_updated", ""))

        # If year is still None, use the authoritative source
        if year is None:
            from utils.text_utils import extract_bill_year

            year = extract_bill_year(
                title=title, introduction_date=intro_date, metadata=raw_data, url=url
            )

        # Populate optional/derived fields
        bill_number = clean_text(str(raw_data.get("bill_number", "")))

        # pdf_url: URL to the official PDF document (NOT a local path)
        pdf_url_raw = raw_data.get("pdf_url") or raw_data.get("document_url")
        pdf_url: Optional[str] = str(pdf_url_raw).strip() if pdf_url_raw else None

        pdf_path = raw_data.get("pdf_path")
        summary = clean_text(raw_data.get("summary", ""))
        full_text = raw_data.get("full_text", "")
        session = clean_text(str(raw_data.get("session", "")))
        sponsor = clean_text(str(raw_data.get("sponsor", "")))
        related_bills = list(raw_data.get("related_bills", []))
        related_acts = list(raw_data.get("related_acts", []))
        language = clean_text(str(raw_data.get("language", "English"))) or "English"
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
            last_updated=last_updated,
            pdf_url=pdf_url,
            pdf_path=pdf_path,
            summary=summary,
            full_text=full_text,
            session=session,
            sponsor=sponsor,
            related_bills=related_bills,
            related_acts=related_acts,
            language=language,
            sectors=sectors,
            keywords=keywords,
            source=source,
            ingested_at=date.today(),
        )
        return bill

    def _normalize_house(self, raw_house: str) -> BillHouse:
        """Map raw house string to BillHouse enum."""
        if not raw_house:
            logger.warning("House of introduction is empty. Defaulting to UNKNOWN.")
            return BillHouse.UNKNOWN

        cleaned = raw_house.strip().lower()
        if "rajya" in cleaned or cleaned in {"rs", "rajya sabha"}:
            return BillHouse.RAJYA_SABHA
        elif "lok" in cleaned or cleaned in {"ls", "lok sabha"}:
            return BillHouse.LOK_SABHA

        # Unrecognized house value
        logger.warning(
            "Unrecognized house of introduction value: %r. Defaulting to UNKNOWN.", raw_house
        )
        return BillHouse.UNKNOWN

    def _normalize_status(self, raw_status: str) -> BillStatus:
        """Map raw status string to BillStatus enum."""
        if not raw_status:
            return BillStatus.INTRODUCED

        # NOTE: ordering matters — more specific patterns must precede general ones.
        # e.g. "introduced - infructuous" contains "introduced" so we check
        # "infructuous" / "lapsed" first.
        if "draft" in raw_status:
            return BillStatus.DRAFT
        elif "ordinance" in raw_status:
            return BillStatus.ORDINANCE
        elif "negatived" in raw_status or "rejected" in raw_status:
            return BillStatus.NEGATIVED
        elif "infructuous" in raw_status or "lapsed" in raw_status:
            return BillStatus.LAPSED
        elif "committee" in raw_status:
            return BillStatus.IN_COMMITTEE
        elif "withdrawn" in raw_status:
            return BillStatus.WITHDRAWN
        elif "pending" in raw_status:
            return BillStatus.PENDING
        elif "assented" in raw_status or ("act" in raw_status and "enacted" in raw_status):
            return BillStatus.ASSENTED
        elif "passed" in raw_status:
            if "lok sabha" in raw_status:
                return BillStatus.PASSED_LOK_SABHA
            elif "rajya sabha" in raw_status:
                return BillStatus.PASSED_RAJYA_SABHA
            else:
                return BillStatus.PASSED_BOTH
        elif "introduced" in raw_status:
            return BillStatus.INTRODUCED

        # Default fallback
        return BillStatus.INTRODUCED
