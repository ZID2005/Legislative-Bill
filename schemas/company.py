"""
schemas/company.py
==================
Typed data model for a BSE/NSE listed company.

This is the canonical company representation used across ingestion,
storage, mapping, and feature engineering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class MarketCapCategory(str, Enum):
    """
    Market capitalisation category as defined by SEBI.

    SEBI defines:
    *  Large-cap  : Top 100 companies by market cap
    *  Mid-cap    : 101st–250th companies by market cap
    *  Small-cap  : 251st and below
    """
    LARGE_CAP = "large_cap"
    MID_CAP = "mid_cap"
    SMALL_CAP = "small_cap"
    UNKNOWN = "unknown"


@dataclass
class Company:
    """
    Canonical representation of a BSE/NSE listed company.

    Attributes
    ----------
    isin : str
        International Securities Identification Number.
        Format: 2-char country code + 9 alphanumeric + 1 check digit.
        E.g. ``"INE009A01021"`` (Infosys).
    company_name : str
        Official registered name.
    ticker_nse : str
        NSE trading symbol (e.g. ``"INFY"``).
    ticker_bse : str
        BSE trading symbol (often same as NSE).
    bse_code : str
        BSE numeric scrip code (e.g. ``"500209"``).
    sector : str
        NSE/SEBI sector classification (e.g. ``"Technology"``, ``"Banking"``).
    industry : str
        More granular industry group (e.g. ``"IT Services"``).
    market_cap_category : MarketCapCategory
        Large / mid / small cap classification.
    market_cap_cr : float | None
        Market capitalisation in Indian Rupees (crore), at last update.
    listing_date : date | None
        Date of first listing on BSE or NSE.
    is_active : bool
        False if the company has been delisted or suspended.
    """

    # Required
    isin: str
    company_name: str
    sector: str

    # Exchange identifiers
    ticker_nse: str = ""
    ticker_bse: str = ""
    bse_code: str = ""

    # Classification
    industry: str = ""
    market_cap_category: MarketCapCategory = MarketCapCategory.UNKNOWN
    market_cap_cr: Optional[float] = None

    # Lifecycle
    listing_date: Optional[date] = None
    is_active: bool = True

    # Enrichment (populated by later pipeline stages)
    aliases: list[str] = field(default_factory=list)  # normalised name variants

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            "isin": self.isin,
            "company_name": self.company_name,
            "ticker_nse": self.ticker_nse,
            "ticker_bse": self.ticker_bse,
            "bse_code": self.bse_code,
            "sector": self.sector,
            "industry": self.industry,
            "market_cap_category": self.market_cap_category.value,
            "market_cap_cr": self.market_cap_cr,
            "listing_date": self.listing_date.isoformat() if self.listing_date else None,
            "is_active": self.is_active,
            "aliases": self.aliases,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Company":
        """Deserialise from a dictionary."""
        from utils.date_utils import parse_date  # noqa: PLC0415
        return cls(
            isin=data["isin"],
            company_name=data["company_name"],
            ticker_nse=data.get("ticker_nse", ""),
            ticker_bse=data.get("ticker_bse", ""),
            bse_code=data.get("bse_code", ""),
            sector=data.get("sector", ""),
            industry=data.get("industry", ""),
            market_cap_category=MarketCapCategory(
                data.get("market_cap_category", "unknown")
            ),
            market_cap_cr=data.get("market_cap_cr"),
            listing_date=parse_date(data.get("listing_date", "")),
            is_active=data.get("is_active", True),
            aliases=data.get("aliases", []),
        )

    def __repr__(self) -> str:
        return (
            f"<Company isin={self.isin!r} ticker={self.ticker_nse!r} "
            f"sector={self.sector!r}>"
        )
