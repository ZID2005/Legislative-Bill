"""
knowledge/loader.py
===================
Functions to load curated knowledge files into memory.

All knowledge CSVs live in the same directory as this module.
Callers import from here rather than reading CSVs directly, so
if we ever move to a database-backed knowledge store, only this
file needs to change.

Usage
-----
    from knowledge.loader import (
        get_ministry_sectors,
        get_sector_keywords,
        get_policy_keywords,
        get_bill_category,
        get_company_sector_override,
    )

    sectors = get_ministry_sectors("Ministry of Finance")
    # → ["Banking & Financial Services", "Capital Markets", "Insurance"]

    keywords = get_sector_keywords("Banking & Financial Services")
    # → ["bank", "RBI", "NBFC", ...]
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

from config.logging_config import get_logger

logger = get_logger(__name__)

_KNOWLEDGE_DIR = Path(__file__).resolve().parent


def _read_csv(filename: str) -> list[dict[str, str]]:
    """Read a knowledge CSV file and return rows as dicts."""
    path = _KNOWLEDGE_DIR / filename
    if not path.is_file():
        logger.warning("Knowledge file not found: %s", path)
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Ministry → Sector
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_ministry_sector() -> dict[str, list[str]]:
    rows = _read_csv("ministry_sector.csv")
    result: dict[str, list[str]] = {}
    for row in rows:
        ministry = row.get("ministry", "").strip()
        primary = row.get("primary_sector", "").strip()
        secondary_raw = row.get("secondary_sectors", "").strip()
        secondary = [s.strip() for s in secondary_raw.split(",") if s.strip()]
        all_sectors = ([primary] if primary else []) + secondary
        if ministry:
            result[ministry] = all_sectors
    return result


def get_ministry_sectors(ministry: str) -> list[str]:
    """
    Return the list of economic sectors regulated by a given ministry.

    Parameters
    ----------
    ministry : str
        Full ministry name, e.g. ``"Ministry of Finance"``.

    Returns
    -------
    list[str]
        Ordered list: primary sector first, then secondary sectors.
        Returns empty list if ministry is not in the knowledge base.
    """
    return _load_ministry_sector().get(ministry, [])


def list_ministries() -> list[str]:
    """Return all ministries in the knowledge base."""
    return list(_load_ministry_sector().keys())


# ---------------------------------------------------------------------------
# Sector → Keywords
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_sector_keywords() -> dict[str, list[str]]:
    rows = _read_csv("sector_keywords.csv")
    result: dict[str, list[str]] = {}
    for row in rows:
        sector = row.get("sector", "").strip()
        keywords_raw = row.get("keywords", "").strip()
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]
        if sector:
            result[sector] = keywords
    return result


def get_sector_keywords(sector: str) -> list[str]:
    """
    Return the list of keywords associated with a sector.

    Parameters
    ----------
    sector : str
        Sector name, e.g. ``"Banking & Financial Services"``.

    Returns
    -------
    list[str]
    """
    return _load_sector_keywords().get(sector, [])


def list_sectors() -> list[str]:
    """Return all sectors in the knowledge base."""
    return list(_load_sector_keywords().keys())


# ---------------------------------------------------------------------------
# Policy keywords
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_policy_keywords() -> list[dict[str, str]]:
    return _read_csv("policy_keywords.csv")


def get_policy_keywords() -> list[dict[str, str]]:
    """
    Return all policy keyword entries.

    Each entry is a dict with keys:
        policy_type, keywords, likely_impact_direction, notes
    """
    return _load_policy_keywords()


# ---------------------------------------------------------------------------
# Bill categories
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_bill_categories() -> list[dict[str, str]]:
    return _read_csv("bill_categories.csv")


def get_bill_category(title: str) -> dict[str, str] | None:
    """
    Match a bill title against known bill categories.

    Performs case-insensitive keyword matching on the title.

    Parameters
    ----------
    title : str
        Bill title, e.g. ``"The Finance Bill, 2024"``.

    Returns
    -------
    dict | None
        The best-matching category row, or None if no match found.
    """
    import re

    title_lower = title.lower()
    for row in _load_bill_categories():
        keywords_raw = row.get("title_keywords", "")
        for keyword in keywords_raw.split(","):
            kw_clean = keyword.strip().lower()
            if kw_clean:
                pattern = r"\b" + re.escape(kw_clean) + r"\b"
                if re.search(pattern, title_lower):
                    logger.debug("Bill title %r matched category %r", title, row.get("bill_type"))
                    return row
    return None


# ---------------------------------------------------------------------------
# Company sector overrides
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_company_sector_overrides() -> dict[str, str]:
    rows = _read_csv("company_sector.csv")
    return {
        row["isin"].strip(): row["override_sector"].strip()
        for row in rows
        if row.get("isin") and row.get("override_sector")
    }


def get_company_sector_override(isin: str) -> str | None:
    """
    Return a manually curated sector for a company by ISIN.

    Used to override the exchange's sector classification when it is
    incorrect or ambiguous (e.g. diversified conglomerates).

    Parameters
    ----------
    isin : str
        ISIN of the company.

    Returns
    -------
    str | None
        Override sector name, or None if no override exists.
    """
    return _load_company_sector_overrides().get(isin)
