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

import re
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

def extract_bill_year(title: str) -> int | None:
    """
    Extract a four-digit year from a bill title string.

    Parameters
    ----------
    title : str
        E.g. ``"The Finance Bill, 2024"`` or ``"Digital Data Protection Act 2023"``.

    Returns
    -------
    int | None
        Extracted year, or ``None`` if not found.

    Examples
    --------
    >>> extract_bill_year("The Finance Bill, 2024")
    2024
    """
    match = re.search(r"\b(19|20)\d{2}\b", title or "")
    return int(match.group()) if match else None


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
        r"\bLIMITED\b", r"\bLTD\.?", r"\bPRIVATE\b", r"\bPVT\.?",
        r"\bINC\.?", r"\bCORPORATION\b", r"\bCORP\.?", r"\bCO\.?",
        r"\bLLP\b", r"\bLLC\b",
    )
    result = name.upper().strip()
    for suffix in suffixes:
        result = re.sub(suffix, "", result, flags=re.IGNORECASE)
    result = re.sub(r"[^\w\s]", "", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result
