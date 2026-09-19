"""
ingestion/state/normalizer.py
==============================
Data normalization service for Indian State legislative bills.

Maps raw scraped state metadata to the canonical Bill schema with:
- jurisdiction = BillJurisdiction.STATE
- Normalized Indian state name
- Chamber (Vidhan Sabha or Vidhan Parishad)
- Complete provenance audit recording
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from config.logging_config import get_logger
from ingestion.state.deduplicator import StateBillDeduplicator
from ingestion.state.provenance import (
    BillProvenanceRecord,
    ProvenanceLevel,
)
from schemas.bill import Bill, BillHouse, BillJurisdiction, BillStatus
from utils.date_utils import parse_date
from utils.state_normalizer import normalize_state
from utils.text_utils import clean_text, extract_bill_year

logger = get_logger(__name__)


class StateBillNormalizer:
    """
    Normalizes raw scraped State legislative dictionaries into standard Bill models
    with full provenance tracking.
    """

    def __init__(self, deduplicator: Optional[StateBillDeduplicator] = None) -> None:
        self.deduplicator = deduplicator or StateBillDeduplicator()

    def normalize(
        self,
        raw_data: dict[str, Any],
        default_state: Optional[str] = None,
        default_legislature: Optional[str] = None,
    ) -> tuple[Bill, BillProvenanceRecord]:
        """
        Normalize raw State bill metadata into a canonical Bill instance
        and accompanying BillProvenanceRecord.
        """
        # 1. State Normalization
        raw_state = raw_data.get("state") or default_state or ""
        norm_state = normalize_state(str(raw_state))
        if not norm_state:
            norm_state = clean_text(str(raw_state)) or "Unknown State"

        # 2. Title Normalization
        raw_title = raw_data.get("title", "")
        title = clean_text(str(raw_title)) or "Untitled State Bill"

        # 3. Bill Number
        raw_bill_no = raw_data.get("bill_number")
        bill_number = clean_text(str(raw_bill_no)) if raw_bill_no else None

        # 4. Dates & Year
        intro_date = parse_date(raw_data.get("introduction_date", ""))
        assent_date = parse_date(raw_data.get("assent_date", ""))
        gazette_date = parse_date(raw_data.get("gazette_date", ""))
        last_updated = parse_date(raw_data.get("last_updated", ""))

        year_val = raw_data.get("year")
        year: Optional[int] = None
        if year_val is not None:
            try:
                year = int(year_val)
            except (ValueError, TypeError):
                pass
        if year is None:
            year = extract_bill_year(
                title=title,
                introduction_date=intro_date,
                metadata=raw_data,
                url=str(raw_data.get("url", "")),
            )

        # 5. House / Chamber Normalization
        raw_house = str(raw_data.get("house", "")).strip().lower()
        house = self._normalize_house(raw_house)

        # 6. Status Normalization
        raw_status = str(raw_data.get("status", "")).strip().lower()
        status = self._normalize_status(raw_status)

        # 7. Department / Ministry — None if unavailable, no fabrication
        raw_dept = raw_data.get("department") or raw_data.get("ministry")
        ministry = clean_text(str(raw_dept)) if raw_dept else ""

        # 8. URLs
        url = str(raw_data.get("url") or raw_data.get("source_url") or "").strip()
        pdf_url_raw = raw_data.get("pdf_url") or raw_data.get("document_url")
        pdf_url = str(pdf_url_raw).strip() if pdf_url_raw else None
        pdf_path = raw_data.get("pdf_path")

        # 9. Summary and Text
        summary = clean_text(str(raw_data.get("summary", "")))
        full_text = raw_data.get("full_text", "")
        session = clean_text(str(raw_data.get("session", "")))

        # 10. Canonical Bill ID
        bill_id = self.deduplicator.generate_canonical_id(
            state=norm_state,
            title=title,
            bill_number=bill_number,
            year=year,
            house=house,
        )

        source_name = raw_data.get("source_name") or raw_data.get("source") or f"{norm_state.lower()}_portal"
        legislature = raw_data.get("legislature") or default_legislature or f"{norm_state} Legislature"

        bill = Bill(
            bill_id=bill_id,
            title=title,
            year=year,
            ministry=ministry,
            house=house,
            status=status,
            url=url,
            bill_number=bill_number or "",
            introduction_date=intro_date,
            assent_date=assent_date,
            gazette_date=gazette_date,
            last_updated=last_updated,
            pdf_url=pdf_url,
            pdf_path=pdf_path,
            summary=summary,
            full_text=full_text,
            session=session,
            sponsor=clean_text(str(raw_data.get("sponsor", ""))),
            related_bills=list(raw_data.get("related_bills", [])),
            related_acts=list(raw_data.get("related_acts", [])),
            language=clean_text(str(raw_data.get("language", "English"))) or "English",
            sectors=[],  # Reserved for future state taxonomy task
            keywords=[],
            source=source_name,
            jurisdiction=BillJurisdiction.STATE,
            state=norm_state,
            ingested_at=date.today(),
        )

        # 11. Compile Provenance Record
        prov = BillProvenanceRecord(
            bill_id=bill_id,
            state=norm_state,
            legislature=legislature,
            source_url=url,
        )

        prov.add_field("title", ProvenanceLevel.AUTHORITATIVE, title, "Official bill listing/detail")
        prov.add_field("jurisdiction", ProvenanceLevel.AUTHORITATIVE, "state", "State legislative source")
        prov.add_field("state", ProvenanceLevel.AUTHORITATIVE, norm_state, "Authoritative state attribution")

        if bill_number:
            prov.add_field("bill_number", ProvenanceLevel.AUTHORITATIVE, bill_number, "Official legislature bill number")
        else:
            prov.add_field("bill_number", ProvenanceLevel.UNAVAILABLE, None, "Not specified in listing")

        if house != BillHouse.UNKNOWN:
            prov.add_field("house", ProvenanceLevel.AUTHORITATIVE, house.value, "Chamber specification in portal")
        else:
            prov.add_field("house", ProvenanceLevel.UNAVAILABLE, "unknown", "Chamber not distinguished")

        if intro_date:
            prov.add_field("introduction_date", ProvenanceLevel.AUTHORITATIVE, intro_date, "Listing date column")
        else:
            prov.add_field("introduction_date", ProvenanceLevel.UNAVAILABLE, None, "Introduction date omitted in listing")

        if assent_date:
            prov.add_field("assent_date", ProvenanceLevel.AUTHORITATIVE, assent_date, "Official assent date recorded")
        else:
            prov.add_field("assent_date", ProvenanceLevel.UNAVAILABLE, None, "Assent date unavailable")

        if pdf_url:
            prov.add_field("pdf_url", ProvenanceLevel.AUTHORITATIVE, pdf_url, "Official document download link")
        else:
            prov.add_field("pdf_url", ProvenanceLevel.UNAVAILABLE, None, "No official PDF URL")

        if status:
            prov.add_field("status", ProvenanceLevel.AUTHORITATIVE, status.value, "Official portal status/remarks")
        else:
            prov.add_field("status", ProvenanceLevel.UNAVAILABLE, None, "Status not explicitly documented")

        if ministry:
            prov.add_field("department", ProvenanceLevel.AUTHORITATIVE, ministry, "Department specified in record")
        else:
            prov.add_field("department", ProvenanceLevel.UNAVAILABLE, None, "Department not listed")

        prov.add_field("year", ProvenanceLevel.DERIVED, year, "Extracted deterministically from bill title/date")
        prov.add_field("bill_id", ProvenanceLevel.DERIVED, bill_id, "Deterministic canonical slug")

        return bill, prov

    def _normalize_house(self, raw_house: str) -> BillHouse:
        """Map house string to BillHouse enum for State legislatures."""
        if not raw_house:
            return BillHouse.VIDHAN_SABHA  # State legislative assembly default

        cleaned = raw_house.strip().lower()
        if "parishad" in cleaned or "council" in cleaned or cleaned in {"lc", "v_p", "vp"}:
            return BillHouse.VIDHAN_PARISHAD
        elif "sabha" in cleaned or "assembly" in cleaned or cleaned in {"la", "v_s", "vs"}:
            return BillHouse.VIDHAN_SABHA

        return BillHouse.VIDHAN_SABHA

    def _normalize_status(self, raw_status: str) -> BillStatus:
        """Map raw status string to BillStatus enum."""
        if not raw_status:
            return BillStatus.INTRODUCED

        s = raw_status.strip().lower()
        if "assent" in s or "act" in s:
            return BillStatus.ASSENTED
        elif "passed" in s:
            return BillStatus.PASSED_BOTH
        elif "committee" in s or "referred" in s:
            return BillStatus.IN_COMMITTEE
        elif "withdrawn" in s:
            return BillStatus.WITHDRAWN
        elif "pending" in s:
            return BillStatus.PENDING

        return BillStatus.INTRODUCED
