"""
utils/date_utils.py
===================
Date and time utility helpers for the Legislative Intelligence project.

Covers:
*  Parsing date strings in multiple formats commonly found in Indian
   government documents and market data.
*  Generating date strings for file naming conventions.
*  Basic business-day awareness (Indian calendar, NSE/BSE holidays stub).

No third-party holiday libraries are introduced at this stage; a proper
holiday calendar will be added when the market data module matures.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Optional

from config.logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Supported date formats (ordered from most to least specific)
# ---------------------------------------------------------------------------
_DATE_FORMATS: list[str] = [
    "%d-%m-%Y",  # 31-12-2024   (common Indian format)
    "%d/%m/%Y",  # 31/12/2024
    "%Y-%m-%d",  # 2024-12-31   (ISO 8601)
    "%d %B %Y",  # 31 December 2024
    "%d %b %Y",  # 31 Dec 2024
    "%B %d, %Y",  # December 31, 2024
    "%b %d, %Y",  # Dec 31, 2024
    "%Y%m%d",  # 20241231     (compact)
]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_date(raw: str) -> Optional[date]:
    """
    Parse a date string into a :class:`datetime.date` object.

    Tries a list of known formats; returns ``None`` if none match.

    Parameters
    ----------
    raw : str
        Raw date string to parse.

    Returns
    -------
    date | None
        Parsed date, or ``None`` if parsing fails.

    Examples
    --------
    >>> parse_date("31-12-2024")
    datetime.date(2024, 12, 31)
    >>> parse_date("2024-12-31")
    datetime.date(2024, 12, 31)
    """
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    # Remove ordinal suffixes: "1st", "2nd", "3rd", "4th" → "1", "2", "3", "4"
    raw_clean = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", raw, flags=re.IGNORECASE)

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw_clean, fmt).date()
        except ValueError:
            continue

    logger.warning("Could not parse date string: %r", raw)
    return None


def parse_datetime(raw: str) -> Optional[datetime]:
    """
    Parse a datetime string.

    Extends :func:`parse_date` with time components.

    Parameters
    ----------
    raw : str
        Raw datetime string.

    Returns
    -------
    datetime | None
    """
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip()
    datetime_formats = [
        "%Y-%m-%dT%H:%M:%S",  # ISO 8601 without timezone
        "%Y-%m-%dT%H:%M:%SZ",  # ISO 8601 UTC
        "%Y-%m-%d %H:%M:%S",  # Common database format
        "%d-%m-%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    ]
    for fmt in datetime_formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    # Fall back: try date-only
    d = parse_date(raw)
    if d:
        return datetime(d.year, d.month, d.day)
    logger.warning("Could not parse datetime string: %r", raw)
    return None


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def today_str(fmt: str = "%Y-%m-%d") -> str:
    """
    Return today's date as a formatted string.

    Parameters
    ----------
    fmt : str
        ``strftime`` format string.

    Returns
    -------
    str
        Formatted date string.

    Examples
    --------
    >>> today_str()
    '2024-12-31'
    >>> today_str("%d%m%Y")
    '31122024'
    """
    return date.today().strftime(fmt)


def format_date(d: date, fmt: str = "%Y-%m-%d") -> str:
    """Format a :class:`~datetime.date` object as a string."""
    return d.strftime(fmt)


# ---------------------------------------------------------------------------
# Business day logic (stub — Indian market calendar)
# ---------------------------------------------------------------------------

# Known national holidays that fall on weekdays in India.
# This set will be populated from a proper data source in a later task.
_INDIAN_MARKET_HOLIDAYS: set[date] = set()


def is_business_day(d: date) -> bool:
    """
    Return ``True`` if *d* is an NSE/BSE trading day.

    Currently checks only weekends; a full holiday calendar will be
    integrated in the market data module (Task 2).

    Parameters
    ----------
    d : date
        Date to check.

    Returns
    -------
    bool
    """
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return d not in _INDIAN_MARKET_HOLIDAYS


def next_business_day(d: date) -> date:
    """Return the next trading day after *d*."""
    candidate = d + timedelta(days=1)
    while not is_business_day(candidate):
        candidate += timedelta(days=1)
    return candidate


def prev_business_day(d: date) -> date:
    """Return the most recent trading day before *d*."""
    candidate = d - timedelta(days=1)
    while not is_business_day(candidate):
        candidate -= timedelta(days=1)
    return candidate


def date_range(start: date, end: date) -> list[date]:
    """
    Return a list of calendar dates from *start* to *end*, inclusive.

    Parameters
    ----------
    start : date
    end : date

    Returns
    -------
    list[date]
    """
    if start > end:
        raise ValueError(f"start ({start}) must be <= end ({end})")
    result: list[date] = []
    current = start
    while current <= end:
        result.append(current)
        current += timedelta(days=1)
    return result


def business_date_range(start: date, end: date) -> list[date]:
    """Return trading days between *start* and *end*, inclusive."""
    return [d for d in date_range(start, end) if is_business_day(d)]
