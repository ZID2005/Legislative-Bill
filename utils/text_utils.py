"""
utils/text_utils.py
===================
Text cleaning, normalisation, and string helper utilities.

These utilities are used across:
*  Bill text pre-processing (before NLP)
*  Company/sector name normalisation
*  Slug generation for file names and URL segments
*  Display truncation

Design Note
-----------
This module intentionally has **no ML or NLP dependencies**.  Heavy NLP
(spaCy, transformers, etc.) belongs in the ``features/`` or ``models/``
packages.  Here we only do deterministic string transformations.
"""

from __future__ import annotations

from datetime import date
import re
from typing import Any, Optional, Union
import unicodedata


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------


def clean_text(text: str) -> str:
    """
    Return a normalised, cleaned version of *text*.

    Transformations applied (in order):
    1. Unicode NFKC normalisation (collapses compatibility characters).
    2. Remove null bytes and other non-printable control characters.
    3. Collapse multiple whitespace sequences into a single space.
    4. Strip leading/trailing whitespace.

    Parameters
    ----------
    text : str
        Raw input string.

    Returns
    -------
    str
        Cleaned string.

    Examples
    --------
    >>> clean_text("  Hello\\n\\nWorld  ")
    'Hello World'
    """
    if not isinstance(text, str):
        return ""
    # Unicode normalisation
    text = unicodedata.normalize("NFKC", text)
    # Remove control characters (keep newlines temporarily)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\t")
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def remove_html_tags(text: str) -> str:
    """
    Strip HTML/XML tags from *text*.

    Parameters
    ----------
    text : str

    Returns
    -------
    str
        Plain text with tags removed.
    """
    return re.sub(r"<[^>]+>", "", text or "")


def remove_page_numbers(text: str) -> str:
    """
    Remove isolated page-number lines common in PDF-extracted text.

    Matches patterns like:
    *  ``Page 1 of 42``
    *  ``- 7 -``
    *  A line containing only digits.

    Parameters
    ----------
    text : str

    Returns
    -------
    str
    """
    text = re.sub(r"(?im)^[\s\-]*page\s+\d+\s*(of\s+\d+)?[\s\-]*$", "", text)
    text = re.sub(r"(?im)^[\s]*[-–]\s*\d+\s*[-–][\s]*$", "", text)
    text = re.sub(r"(?im)^\s*\d+\s*$", "", text)
    return text


def normalise_whitespace(text: str) -> str:
    """Collapse all whitespace sequences to a single space."""
    return re.sub(r"\s+", " ", text or "").strip()


# ---------------------------------------------------------------------------
# Slug / identifier generation
# ---------------------------------------------------------------------------


def slugify(text: str, separator: str = "-", max_length: int = 100) -> str:
    """
    Convert *text* into a URL/filename-safe slug.

    Steps:
    1. Lowercase.
    2. Replace non-alphanumeric characters with *separator*.
    3. Collapse repeated separators.
    4. Strip leading/trailing separators.
    5. Truncate to *max_length*.

    Parameters
    ----------
    text : str
    separator : str
        Character used to replace non-alphanumeric characters.
    max_length : int
        Maximum length of the returned slug.

    Returns
    -------
    str

    Examples
    --------
    >>> slugify("The Finance Bill, 2024")
    'the-finance-bill-2024'
    >>> slugify("Digital Personal Data Protection Act — 2023")
    'digital-personal-data-protection-act-2023'
    """
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = re.sub(r"[^\w\s-]", " ", text)
    text = re.sub(r"[\s_-]+", separator, text)
    text = text.strip(separator)
    return text[:max_length]


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------


def truncate(text: str, max_length: int = 200, ellipsis: str = "…") -> str:
    """
    Truncate *text* to *max_length* characters, appending *ellipsis*.

    Word boundaries are respected; the function will not cut in the middle
    of a word unless a single word exceeds *max_length*.

    Parameters
    ----------
    text : str
    max_length : int
        Maximum number of characters in the result (including ellipsis).
    ellipsis : str
        Appended when truncation occurs.

    Returns
    -------
    str

    Examples
    --------
    >>> truncate("The quick brown fox", max_length=12)
    'The quick…'
    """
    if not text or len(text) <= max_length:
        return text
    cut = max_length - len(ellipsis)
    if cut <= 0:
        return ellipsis[:max_length]
    # Find last word boundary
    boundary = text.rfind(" ", 0, cut)
    if boundary == -1:
        boundary = cut
    return text[:boundary] + ellipsis


# ---------------------------------------------------------------------------
# Bill-specific helpers
# ---------------------------------------------------------------------------


def extract_bill_year(
    title: Optional[str] = None,
    introduction_date: Optional[Union[str, date]] = None,
    metadata: Optional[dict[str, Any]] = None,
    url: Optional[str] = None,
) -> int | None:
    """
    Authoritative single source of year extraction for legislative bills.

    Priority order:
    1. Introduction Date (date object or string containing year)
    2. Metadata (e.g. metadata dict containing 'year', 'pub_date', etc.)
    3. URL (string containing year)
    4. Title (string containing year)
    5. NULL (returns None; never defaults to current year)

    Parameters
    ----------
    title : str | None
    introduction_date : str | date | None
    metadata : dict | None
    url : str | None

    Returns
    -------
    int | None
        Extracted year, or None if not found.
    """
    # Priority 1: Introduction Date
    if introduction_date:
        if isinstance(introduction_date, date):
            return introduction_date.year
        match = re.search(r"\b(19|20)\d{2}\b", str(introduction_date))
        if match:
            return int(match.group())

    # Priority 2: Metadata dict
    if metadata and isinstance(metadata, dict):
        raw_year = metadata.get("year")
        if raw_year is not None:
            try:
                yr = int(raw_year)
                if 1900 <= yr <= 2100:
                    return yr
            except (ValueError, TypeError):
                pass
        for field in ["pub_date", "publication_date", "last_updated"]:
            val = metadata.get(field)
            if val:
                if isinstance(val, date):
                    return val.year
                match = re.search(r"\b(19|20)\d{2}\b", str(val))
                if match:
                    return int(match.group())

    # Priority 3: URL
    if url:
        match = re.search(r"\b(19|20)\d{2}\b", url)
        if match:
            return int(match.group())

    # Priority 4: Title
    if title:
        match = re.search(r"\b(19|20)\d{2}\b", title)
        if match:
            return int(match.group())

    # Priority 5: NULL
    return None


def normalise_company_name(name: str) -> str:
    """
    Normalise a company name for fuzzy matching.

    Removes common suffixes (Ltd, Limited, Pvt, etc.), converts to
    uppercase, and strips punctuation.

    Parameters
    ----------
    name : str

    Returns
    -------
    str

    Examples
    --------
    >>> normalise_company_name("Tata Consultancy Services Limited")
    'TATA CONSULTANCY SERVICES'
    """
    suffixes = (
        r"\bLIMITED\b",
        r"\bLTD\.?",
        r"\bPRIVATE\b",
        r"\bPVT\.?",
        r"\bINC\.?",
        r"\bCORPORATION\b",
        r"\bCORP\.?",
        r"\bCO\.?",
        r"\bLLP\b",
        r"\bLLC\b",
    )
    result = name.upper().strip()
    for suffix in suffixes:
        result = re.sub(suffix, "", result, flags=re.IGNORECASE)
    result = re.sub(r"[^\w\s]", "", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result
