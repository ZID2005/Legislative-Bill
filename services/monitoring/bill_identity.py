"""
services/monitoring/bill_identity.py
====================================
Deterministic Bill Identity & Deduplication Engine.

Audit & Hardening for TASK 8.18 (Section 5):
1. A bill must not be duplicated merely because:
   - PDF URL changes
   - Page URL changes
   - Title formatting changes
   - Whitespace changes
   - Document version changes
2. Uses stable identity signals where available:
   - bill number
   - year
   - house
   - jurisdiction
   - state
   - normalized official title
   - sponsoring authority / department
   - official document identifier
3. Does NOT invent stable IDs where official identifiers are unavailable.
4. When uncertain: marks status as IDENTITY_UNCERTAIN rather than creating a duplicate.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from config.logging_config import get_logger
from utils.text_utils import slugify
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)


class IdentityMatchStatus(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    STRONG_MATCH = "STRONG_MATCH"
    IDENTITY_UNCERTAIN = "IDENTITY_UNCERTAIN"
    NEW_BILL = "NEW_BILL"


@dataclass
class BillIdentityMatch:
    """Result of attempting to match a candidate bill against known bills."""

    status: IdentityMatchStatus
    matched_bill_id: Optional[str] = None
    confidence: float = 0.0
    signals_matched: list[str] = field(default_factory=list)
    reason: str = ""

    @property
    def is_duplicate(self) -> bool:
        """True if the candidate bill is an existing known bill."""
        return self.status in (IdentityMatchStatus.EXACT_MATCH, IdentityMatchStatus.STRONG_MATCH)

    @property
    def is_uncertain(self) -> bool:
        """True if identity could not be disambiguated with high confidence."""
        return self.status == IdentityMatchStatus.IDENTITY_UNCERTAIN

    @property
    def should_create_new(self) -> bool:
        """True only if confidently classified as a genuinely new bill."""
        return self.status == IdentityMatchStatus.NEW_BILL


_PUNCTUATION_RE = re.compile(r"[\.,;:\'\"\(\)\[\]\{\}\-_/\\|]")
_WHITESPACE_RE = re.compile(r"\s+")
_PREFIX_THE_RE = re.compile(r"^the\s+", re.IGNORECASE)
_BILL_ACT_SUFFIX_RE = re.compile(r",?\s*(?:bill|act)(?:,?\s*\d{4})?$", re.IGNORECASE)


def normalize_bill_title(title: Optional[str]) -> str:
    """
    Produce a canonical normalized representation of a legislative bill title.

    Transforms:
    - "The Finance Bill, 2024" -> "finance"
    - "  THE   BANKING LAWS (AMENDMENT) BILL,   2024  " -> "banking laws amendment"
    - Strips whitespace, accents, casing, and standard statutory boilerplate.
    """
    if not title:
        return ""

    # Normalize unicode (decompose accents, NFKD)
    normalized = unicodedata.normalize("NFKD", str(title))
    normalized = normalized.strip().lower()

    # Strip leading "The"
    normalized = _PREFIX_THE_RE.sub("", normalized)

    # Remove standard punctuation
    normalized = _PUNCTUATION_RE.sub(" ", normalized)

    # Strip bill/act and year suffix
    normalized = _BILL_ACT_SUFFIX_RE.sub("", normalized)

    # Collapse whitespace
    normalized = _WHITESPACE_RE.sub(" ", normalized).strip()

    return normalized


def extract_identity_signals(record: dict[str, Any]) -> dict[str, Any]:
    """
    Extract and normalize the core identity signals from a bill record.
    """
    raw_num = str(record.get("bill_number") or record.get("number") or "").strip()
    # Normalize bill number: extract digit patterns if formatted like "Bill No. 12 of 2024"
    num_match = re.search(r"(\d+)", raw_num)
    clean_num = num_match.group(1) if num_match else raw_num.lower()

    year_val = record.get("year")
    if not year_val and record.get("introduction_date"):
        try:
            year_val = int(str(record["introduction_date"])[:4])
        except (ValueError, TypeError):
            year_val = None

    raw_jurisdiction = (record.get("jurisdiction") or "central").lower().strip()
    raw_state = record.get("state")
    clean_state = normalize_state(raw_state) if raw_state else None

    raw_title = record.get("title") or record.get("bill_title") or ""
    norm_title = normalize_bill_title(raw_title)

    house_val = (record.get("house") or "").lower().strip()

    return {
        "bill_id": record.get("bill_id") or record.get("id"),
        "bill_number": clean_num if clean_num else None,
        "year": int(year_val) if year_val else None,
        "jurisdiction": raw_jurisdiction,
        "state": clean_state,
        "house": house_val if house_val else None,
        "raw_title": raw_title.strip(),
        "norm_title": norm_title,
        "official_doc_id": record.get("official_document_id") or record.get("doc_id"),
        "sponsoring_authority": record.get("sponsoring_authority") or record.get("department") or record.get("sponsor"),
    }


class BillIdentityService:
    """
    Authoritative identity matching and deduplication service.

    Audits incoming candidates against a catalog of known bills to prevent
    duplicate creation when documents change, URLs change, or minor typographical
    variations occur.
    """

    def __init__(self, known_bills: Optional[dict[str, dict[str, Any]]] = None) -> None:
        self._known_bills: dict[str, dict[str, Any]] = known_bills or {}
        # Pre-indexed lookup maps for sub-millisecond candidate matching
        self._id_index: dict[str, str] = {}
        self._number_year_jurisdiction_index: dict[tuple[str, int, str, Optional[str]], str] = {}
        self._norm_title_year_index: dict[tuple[str, int, str], str] = {}
        self._rebuild_indices()

    def set_known_bills(self, known_bills: dict[str, dict[str, Any]]) -> None:
        self._known_bills = known_bills
        self._rebuild_indices()

    def _rebuild_indices(self) -> None:
        self._id_index.clear()
        self._number_year_jurisdiction_index.clear()
        self._norm_title_year_index.clear()

        for b_id, rec in self._known_bills.items():
            sig = extract_identity_signals(rec)
            self._id_index[b_id.lower()] = b_id

            if sig["bill_number"] and sig["year"]:
                key = (sig["bill_number"], sig["year"], sig["jurisdiction"], sig["state"])
                self._number_year_jurisdiction_index[key] = b_id

            if sig["norm_title"] and sig["year"]:
                t_key = (sig["norm_title"], sig["year"], sig["jurisdiction"])
                self._norm_title_year_index[t_key] = b_id

    def match_candidate(self, candidate: dict[str, Any]) -> BillIdentityMatch:
        """
        Evaluate a candidate bill record against all known bills.

        Returns a BillIdentityMatch indicating whether it matches an existing bill,
        is a new bill, or is uncertain.
        """
        c_sig = extract_identity_signals(candidate)
        c_id = c_sig["bill_id"]

        # Signal 1: Direct Canonical bill_id Match
        if c_id and c_id.lower() in self._id_index:
            matched_id = self._id_index[c_id.lower()]
            return BillIdentityMatch(
                status=IdentityMatchStatus.EXACT_MATCH,
                matched_bill_id=matched_id,
                confidence=1.0,
                signals_matched=["bill_id"],
                reason=f"Exact match on canonical bill_id '{matched_id}'",
            )

        # Signal 2: Official Bill Number + Year + Jurisdiction + State
        if c_sig["bill_number"] and c_sig["year"]:
            num_key = (c_sig["bill_number"], c_sig["year"], c_sig["jurisdiction"], c_sig["state"])
            if num_key in self._number_year_jurisdiction_index:
                matched_id = self._number_year_jurisdiction_index[num_key]
                return BillIdentityMatch(
                    status=IdentityMatchStatus.EXACT_MATCH,
                    matched_bill_id=matched_id,
                    confidence=0.98,
                    signals_matched=["bill_number", "year", "jurisdiction", "state"],
                    reason=f"Exact match on official bill number '{c_sig['bill_number']}' and year {c_sig['year']}",
                )

        # Signal 3: Normalized Title + Year + Jurisdiction
        if c_sig["norm_title"] and c_sig["year"]:
            title_key = (c_sig["norm_title"], c_sig["year"], c_sig["jurisdiction"])
            if title_key in self._norm_title_year_index:
                matched_id = self._norm_title_year_index[title_key]
                return BillIdentityMatch(
                    status=IdentityMatchStatus.STRONG_MATCH,
                    matched_bill_id=matched_id,
                    confidence=0.90,
                    signals_matched=["norm_title", "year", "jurisdiction"],
                    reason=f"Strong match on normalized title '{c_sig['norm_title']}' and year {c_sig['year']}",
                )

        # Signal 4: Ambiguity & Uncertainty Checks
        # If candidate has a title but NO bill_number and NO year, check if title matches multiple or any known bill
        if c_sig["norm_title"] and not c_sig["year"]:
            matches = [
                b_id for (t, y, j), b_id in self._norm_title_year_index.items()
                if t == c_sig["norm_title"] and j == c_sig["jurisdiction"]
            ]
            if len(matches) == 1:
                return BillIdentityMatch(
                    status=IdentityMatchStatus.IDENTITY_UNCERTAIN,
                    matched_bill_id=matches[0],
                    confidence=0.50,
                    signals_matched=["norm_title_only"],
                    reason="Title matches known bill but year is missing from candidate — flagged IDENTITY_UNCERTAIN to prevent duplicate",
                )
            elif len(matches) > 1:
                return BillIdentityMatch(
                    status=IdentityMatchStatus.IDENTITY_UNCERTAIN,
                    matched_bill_id=None,
                    confidence=0.30,
                    signals_matched=["norm_title_multiple"],
                    reason=f"Title matches {len(matches)} historical bills across different years — flagged IDENTITY_UNCERTAIN",
                )

        # Signal 5: If title is empty or completely missing critical fields
        if not c_sig["norm_title"] and not c_sig["bill_number"]:
            return BillIdentityMatch(
                status=IdentityMatchStatus.IDENTITY_UNCERTAIN,
                matched_bill_id=None,
                confidence=0.0,
                signals_matched=[],
                reason="Insufficient identity signals: neither title nor bill number provided",
            )

        # Signal 6: Candidate has valid signals and does NOT match any known bill -> NEW_BILL
        return BillIdentityMatch(
            status=IdentityMatchStatus.NEW_BILL,
            matched_bill_id=None,
            confidence=0.95,
            signals_matched=["distinct_bill_number_or_title"],
            reason="Distinct authoritative signals confirm new legislative entity",
        )
