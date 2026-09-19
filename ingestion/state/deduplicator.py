"""
ingestion/state/deduplicator.py
===============================
Deduplication logic for Indian State legislative bills.

Enforces stable identity using official State bill numbers, chambers, and
session years, with title slug fallback. Prevents duplication across listing pages,
detail pages, and separate PDF document links.
"""

from __future__ import annotations

import re
from typing import Any, Optional
import urllib.parse

from config.logging_config import get_logger
from schemas.bill import Bill, BillHouse
from utils.state_normalizer import normalize_state
from utils.text_utils import clean_text, slugify

logger = get_logger(__name__)


class StateBillDeduplicator:
    """
    Manages State bill deduplication and canonical ID resolution.
    """

    def __init__(self) -> None:
        # Maps canonical_id -> bill_id
        self._seen_canonical_keys: dict[str, str] = {}
        # Maps normalized URL -> bill_id
        self._seen_urls: dict[str, str] = {}

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL preserving query string for URLs differentiated by query parameters."""
        if not url:
            return ""
        parsed = urllib.parse.urlparse(url.strip())
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{parsed.scheme}://{parsed.netloc.lower()}{parsed.path.rstrip('/')}{query}"

    @staticmethod
    def _extract_clean_bill_number(bill_number: str) -> str:
        """Extract purely numerical or alphanumeric identifier from bill number string."""
        if not bill_number:
            return ""
        # Match pattern like "L.A. Bill No. 29 of 2026" or "29" or "Bill No. 29"
        m = re.search(r"(\d+)", bill_number)
        if m:
            return m.group(1)
        return slugify(bill_number)

    def generate_canonical_id(
        self,
        state: str,
        title: str,
        bill_number: Optional[str] = None,
        year: Optional[int] = None,
        house: Optional[BillHouse | str] = None,
    ) -> str:
        """
        Generate a stable, predictable canonical ID for a State bill.

        Priority 1: state + chamber + official bill_number + year (e.g. 'ap-vs-bill-21-2026')
        Priority 2: state + slugified title (e.g. 'ap-the-andhra-pradesh-omnibus-bill-2026')
        """
        norm_state = normalize_state(state) or state
        state_prefix = slugify(norm_state)

        # Chamber code
        chamber_code = "vs"
        if house:
            h_str = house.value if isinstance(house, BillHouse) else str(house).lower()
            if "parishad" in h_str:
                chamber_code = "vp"

        clean_num = self._extract_clean_bill_number(bill_number or "")
        if clean_num and year:
            return f"{state_prefix}-{chamber_code}-bill-{clean_num}-{year}"

        # Fallback to title-based slug
        clean_title_slug = slugify(title)
        # Ensure state prefix is present once
        if clean_title_slug.startswith(state_prefix):
            return clean_title_slug
        return f"{state_prefix}-{clean_title_slug}"

    def check_duplicate(self, raw_data: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Check if a bill has already been registered or encountered.

        Returns
        -------
        (is_duplicate, canonical_id)
        """
        state = raw_data.get("state", "")
        title = raw_data.get("title", "")
        bill_number = raw_data.get("bill_number")
        year = raw_data.get("year")
        house = raw_data.get("house")

        canonical_id = self.generate_canonical_id(
            state=state,
            title=title,
            bill_number=bill_number,
            year=year,
            house=house,
        )

        if canonical_id in self._seen_canonical_keys:
            return True, canonical_id

        # Check unique document / detail URL matching
        urls_to_check = [
            raw_data.get("detail_url", ""),
            raw_data.get("pdf_url", ""),
            raw_data.get("document_url", ""),
        ]
        for u in urls_to_check:
            if u:
                norm_u = self._normalize_url(u)
                if norm_u and norm_u in self._seen_urls:
                    return True, self._seen_urls[norm_u]

        return False, canonical_id

    def register_bill(self, bill_id: str, raw_data: dict[str, Any]) -> None:
        """Register a bill and its associated URLs in the deduplication index."""
        state = raw_data.get("state", "")
        title = raw_data.get("title", "")
        bill_number = raw_data.get("bill_number")
        year = raw_data.get("year")
        house = raw_data.get("house")

        canonical_id = self.generate_canonical_id(
            state=state,
            title=title,
            bill_number=bill_number,
            year=year,
            house=house,
        )

        self._seen_canonical_keys[canonical_id] = bill_id

        for key in ("detail_url", "pdf_url", "document_url"):
            val = raw_data.get(key)
            if val:
                norm_u = self._normalize_url(str(val))
                if norm_u:
                    self._seen_urls[norm_u] = bill_id
