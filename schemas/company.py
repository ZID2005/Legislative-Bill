"""
schemas/company.py
==================
Typed data model for a company entity.

This is the canonical company representation used across ingestion,
storage, mapping, and feature engineering.

Task 8.12.2 Extension
---------------------
Extended to support both the quantitative prediction universe and the
broader intelligence universe.  All new fields are backward compatible:
existing JSON company records that omit these fields will load
successfully using safe defaults.

Schema field count: 30 (was 23 before Task 8.12.2)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Existing enums
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# New enums (Task 8.12.2)
# ---------------------------------------------------------------------------


class UniverseType(str, Enum):
    """
    Explicitly identifies which analytical universe(s) a company belongs to.

    QUANTITATIVE
        Companies used in the Central prediction pipeline.  Their presence,
        bill-company mappings, and quantitative predictions are production
        artefacts and must not be altered.

    INTELLIGENCE
        Companies tracked for qualitative / state-level intelligence only.
        These do NOT receive quantitative predictions.

    BOTH
        Companies that appear in both universes.

    Default for legacy records: ``QUANTITATIVE`` (preserves existing
    Central quantitative companies without requiring record updates).
    """

    QUANTITATIVE = "quantitative"
    INTELLIGENCE = "intelligence"
    BOTH = "both"


class EntityType(str, Enum):
    """
    Identifies the organisational type of the entity.

    LISTED_COMPANY       : Exchange-listed corporation (BSE / NSE)
    UNLISTED_COMPANY     : Incorporated company not listed on any exchange
    STATE_OWNED_ENTERPRISE : Government-owned corporate entity (PSU / PSE)
    PUBLIC_UTILITY       : Government-run utility (electricity boards, etc.)
    PRIVATE_COMPANY      : Privately-held company (Pvt Ltd structure)
    INDUSTRY_GROUP       : Sectoral body, association, or conglomerate group
    OTHER                : Any entity that does not fit the above categories

    Default for legacy records: ``LISTED_COMPANY`` (safe assumption for
    existing BSE/NSE records).
    """

    LISTED_COMPANY = "listed_company"
    UNLISTED_COMPANY = "unlisted_company"
    STATE_OWNED_ENTERPRISE = "state_owned_enterprise"
    PUBLIC_UTILITY = "public_utility"
    PRIVATE_COMPANY = "private_company"
    INDUSTRY_GROUP = "industry_group"
    OTHER = "other"


class OwnershipType(str, Enum):
    """
    Represents the ownership category of the entity.

    PRIVATE  : Privately / institutionally owned
    PUBLIC   : Listed and predominantly public-market owned
    STATE    : Government / state-controlled
    MIXED    : Mixed public and state / private ownership
    UNKNOWN  : Ownership structure not determined

    Default for legacy records: ``UNKNOWN`` (non-speculative safe default).
    """

    PRIVATE = "private"
    PUBLIC = "public"
    STATE = "state"
    MIXED = "mixed"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Company dataclass
# ---------------------------------------------------------------------------


@dataclass
class Company:
    """
    Canonical representation of a company entity.

    Supports both quantitative-prediction companies (Central universe) and
    intelligence-only companies (broader intelligence universe added in
    Task 8.12.2).

    Attributes
    ----------
    isin : str
        International Securities Identification Number.
        Format: 2-char country code + 9 alphanumeric + 1 check digit.
        E.g. ``"INE009A01021"`` (Infosys).
        For unlisted / non-ISIN entities, a stable synthetic identifier
        may be used (e.g. ``"PRIV-RELIANCE-GRP"``).
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

    --- Task 8.12.2 new fields ---

    universe_type : UniverseType
        Identifies which analytical universe the company belongs to.
        Default: ``UniverseType.QUANTITATIVE`` — preserves existing Central
        quantitative companies without requiring record updates.

    entity_type : EntityType
        Organisational type of the entity.
        Default: ``EntityType.LISTED_COMPANY`` — safe for existing BSE/NSE records.

    group_name : str | None
        Larger corporate group, e.g. ``"Tata Group"``, ``"Adani Group"``.
        Optional; ``None`` if not applicable or not known.

    ownership_type : OwnershipType
        Ownership category.
        Default: ``OwnershipType.UNKNOWN`` — non-speculative safe default
        for existing records where ownership is not explicitly stored.

    data_sources : list[str]
        Provenance / source categories used to establish company information.
        Examples: ``["NSE", "BSE", "Annual Report", "Official Company Website"]``.
        Empty list for legacy records that pre-date this field.

    data_quality_score : float | None
        Completeness/quality score for company intelligence data.
        Scale: 0.0 (no data) to 1.0 (fully verified, rich data).
        ``None`` means the score has not been assessed; this is the safe
        default for legacy records.  Do NOT populate speculatively.

    watchlist_eligible : bool
        True if the company may later be selected by users for watchlists.
        This field only represents *eligibility*; watchlist functionality
        itself is not implemented in this task.
        Default: ``False`` — conservative, opt-in model.
    """

    # -----------------------------------------------------------------------
    # Required
    # -----------------------------------------------------------------------
    isin: str
    company_name: str
    sector: str

    # -----------------------------------------------------------------------
    # Exchange identifiers
    # -----------------------------------------------------------------------
    ticker_nse: str = ""
    ticker_bse: str = ""
    bse_code: str = ""

    # -----------------------------------------------------------------------
    # Classification
    # -----------------------------------------------------------------------
    industry: str = ""
    sub_industry: str = ""
    market_cap_category: MarketCapCategory = MarketCapCategory.UNKNOWN
    market_cap_cr: Optional[float] = None

    # -----------------------------------------------------------------------
    # Location & Information
    # -----------------------------------------------------------------------
    hq_state: str = ""
    hq_city: str = ""
    website: str = ""

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------
    listing_date: Optional[date] = None
    is_active: bool = True
    listing_status: str = "Listed"

    # -----------------------------------------------------------------------
    # Enrichment (populated by later pipeline stages)
    # -----------------------------------------------------------------------
    aliases: list[str] = field(default_factory=list)  # normalised name variants

    # -----------------------------------------------------------------------
    # Extended State Intelligence (Task 8.7 — backward compatible)
    # -----------------------------------------------------------------------
    exchange: str = ""
    business_description: str = ""
    state_presences: list[Any] = field(default_factory=list)  # list[StatePresenceRecord]
    facilities: list[dict[str, Any]] = field(default_factory=list)
    subsidiaries: list[str] = field(default_factory=list)
    business_activities: list[str] = field(default_factory=list)

    # -----------------------------------------------------------------------
    # Company Intelligence Universe (Task 8.12.2 — backward compatible)
    # -----------------------------------------------------------------------

    universe_type: UniverseType = UniverseType.QUANTITATIVE
    """Universe membership.  QUANTITATIVE is the default so that all
    existing Central companies retain their current behaviour without
    requiring a data migration."""

    entity_type: EntityType = EntityType.LISTED_COMPANY
    """Organisational type.  LISTED_COMPANY is the default; appropriate
    for the existing BSE/NSE seed records."""

    group_name: Optional[str] = None
    """Larger corporate group, if applicable (e.g. "Tata Group").
    None for standalone entities or when group affiliation is unknown."""

    ownership_type: OwnershipType = OwnershipType.UNKNOWN
    """Ownership category.  UNKNOWN is the safe default for legacy
    records where ownership has not been explicitly determined."""

    data_sources: list[str] = field(default_factory=list)
    """Provenance / source categories that establish this company's data.
    Examples: ["NSE", "BSE", "Annual Report", "Official Company Website",
    "Government Record", "Regulatory Filing"].
    Empty list for records pre-dating this field."""

    data_quality_score: Optional[float] = None
    """Completeness/quality score. Range: 0.0 to 1.0.
    None = score not yet assessed (safe default for legacy records).
    0.0 = no usable data; 1.0 = fully verified, rich intelligence.
    Do NOT populate speculatively."""

    watchlist_eligible: bool = False
    """True if this company may be selected by users for watchlists in a
    future task.  False is the conservative default; eligibility must
    be explicitly granted.  This field does NOT implement watchlist
    functionality."""

    # -----------------------------------------------------------------------
    # Serialisation
    # -----------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a JSON-compatible dict."""
        return {
            # Original fields
            "isin": self.isin,
            "company_name": self.company_name,
            "ticker_nse": self.ticker_nse,
            "ticker_bse": self.ticker_bse,
            "bse_code": self.bse_code,
            "sector": self.sector,
            "industry": self.industry,
            "sub_industry": self.sub_industry,
            "market_cap_category": self.market_cap_category.value,
            "market_cap_cr": self.market_cap_cr,
            "hq_state": self.hq_state,
            "hq_city": self.hq_city,
            "website": self.website,
            "listing_date": self.listing_date.isoformat() if self.listing_date else None,
            "is_active": self.is_active,
            "listing_status": self.listing_status,
            "aliases": self.aliases,
            "exchange": self.exchange,
            "business_description": self.business_description,
            "state_presences": [
                sp.to_dict() if hasattr(sp, "to_dict") else sp for sp in self.state_presences
            ],
            "facilities": self.facilities,
            "subsidiaries": self.subsidiaries,
            "business_activities": self.business_activities,
            # Task 8.12.2 new fields
            "universe_type": self.universe_type.value,
            "entity_type": self.entity_type.value,
            "group_name": self.group_name,
            "ownership_type": self.ownership_type.value,
            "data_sources": self.data_sources,
            "data_quality_score": self.data_quality_score,
            "watchlist_eligible": self.watchlist_eligible,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Company":
        """
        Deserialise from a dictionary.

        Backward compatible: any missing new field falls back to its safe
        default so that legacy JSON records load without modification.
        """
        from utils.date_utils import parse_date  # noqa: PLC0415
        from schemas.state_corporate_exposure import StatePresenceRecord  # noqa: PLC0415

        # --- Existing state_presences handling ---
        presences = []
        for sp in data.get("state_presences", []):
            if isinstance(sp, dict):
                presences.append(StatePresenceRecord.from_dict(sp))
            elif isinstance(sp, StatePresenceRecord):
                presences.append(sp)

        # --- Task 8.12.2: robust enum deserialization with safe defaults ---
        raw_universe = data.get("universe_type", UniverseType.QUANTITATIVE.value)
        if isinstance(raw_universe, UniverseType):
            universe_type = raw_universe
        else:
            try:
                universe_type = UniverseType(str(raw_universe).strip().lower())
            except ValueError:
                universe_type = UniverseType.QUANTITATIVE

        raw_entity = data.get("entity_type", EntityType.LISTED_COMPANY.value)
        if isinstance(raw_entity, EntityType):
            entity_type = raw_entity
        else:
            try:
                entity_type = EntityType(str(raw_entity).strip().lower())
            except ValueError:
                entity_type = EntityType.LISTED_COMPANY

        raw_ownership = data.get("ownership_type", OwnershipType.UNKNOWN.value)
        if isinstance(raw_ownership, OwnershipType):
            ownership_type = raw_ownership
        else:
            try:
                ownership_type = OwnershipType(str(raw_ownership).strip().lower())
            except ValueError:
                ownership_type = OwnershipType.UNKNOWN

        return cls(
            # Original fields
            isin=data["isin"],
            company_name=data["company_name"],
            ticker_nse=data.get("ticker_nse", ""),
            ticker_bse=data.get("ticker_bse", ""),
            bse_code=data.get("bse_code", ""),
            sector=data.get("sector", ""),
            industry=data.get("industry", ""),
            sub_industry=data.get("sub_industry", ""),
            market_cap_category=MarketCapCategory(data.get("market_cap_category", "unknown")),
            market_cap_cr=data.get("market_cap_cr"),
            hq_state=data.get("hq_state", ""),
            hq_city=data.get("hq_city", ""),
            website=data.get("website", ""),
            listing_date=parse_date(data.get("listing_date", "")),
            is_active=data.get("is_active", True),
            listing_status=data.get("listing_status", "Listed"),
            aliases=data.get("aliases", []),
            exchange=data.get("exchange", "NSE" if data.get("ticker_nse") else ""),
            business_description=data.get("business_description", ""),
            state_presences=presences,
            facilities=data.get("facilities", []),
            subsidiaries=data.get("subsidiaries", []),
            business_activities=data.get("business_activities", []),
            # Task 8.12.2 new fields — all have safe defaults for legacy records
            universe_type=universe_type,
            entity_type=entity_type,
            group_name=data.get("group_name", None),
            ownership_type=ownership_type,
            data_sources=data.get("data_sources", []),
            data_quality_score=data.get("data_quality_score", None),
            watchlist_eligible=data.get("watchlist_eligible", False),
        )

    def __repr__(self) -> str:
        return (
            f"<Company isin={self.isin!r} ticker={self.ticker_nse!r} "
            f"sector={self.sector!r} universe={self.universe_type.value!r}>"
        )
