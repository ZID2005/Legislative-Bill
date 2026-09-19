"""
schemas/watchlist.py
====================
Watchlist and WatchlistItem schemas for entity monitoring.

Supported entity types:
- COMPANY: BSE/NSE ISIN or synthetic company ID (e.g. 'PRIV-BUNDL-SWIGGY', 'INE009A01021')
- BILL: Canonical Central or State bill identifier (e.g. 'the-coastal-shipping-bill-2024')
- SECTOR: Canonical sector classification (e.g. 'Technology', 'Financials')
- INDUSTRY: Granular industry group (e.g. 'Food Delivery & Quick Commerce')
- STATE: Normalized Indian State name (e.g. 'Kerala', 'Karnataka')
- JURISDICTION: 'central' or 'state'

Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid

from utils.state_normalizer import normalize_state


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WatchlistEntityType(str, Enum):
    """Supported entity categories that can be monitored in a watchlist."""

    COMPANY = "COMPANY"
    BILL = "BILL"
    SECTOR = "SECTOR"
    INDUSTRY = "INDUSTRY"
    STATE = "STATE"
    JURISDICTION = "JURISDICTION"


_VALID_JURISDICTIONS = {"central", "state"}


def validate_entity_reference(
    entity_type: WatchlistEntityType | str,
    entity_id: str,
) -> str:
    """
    Validate that an entity reference conforms to canonical platform identifiers.

    Returns the normalized entity_id or raises ValueError if invalid.
    """
    if not entity_id or not entity_id.strip():
        raise ValueError("entity_id cannot be empty or blank")

    raw_id = entity_id.strip()

    # Normalize entity type
    if isinstance(entity_type, WatchlistEntityType):
        etype = entity_type
    else:
        try:
            etype = WatchlistEntityType(str(entity_type).strip().upper())
        except ValueError:
            raise ValueError(f"Unsupported watchlist entity type: {entity_type}")

    if etype == WatchlistEntityType.JURISDICTION:
        norm_j = raw_id.lower()
        if norm_j not in _VALID_JURISDICTIONS:
            raise ValueError(
                f"Invalid jurisdiction '{raw_id}'. Must be one of {_VALID_JURISDICTIONS}"
            )
        return norm_j

    elif etype == WatchlistEntityType.STATE:
        norm_s = normalize_state(raw_id)
        if not norm_s:
            # Check if it's already a recognized state name
            if len(raw_id) < 2:
                raise ValueError(f"Invalid state identifier '{raw_id}'")
            return raw_id.title()
        return norm_s

    elif etype == WatchlistEntityType.COMPANY:
        # Avoid unvalidated arbitrary symbols (minimum sanity check: alphanumeric + hyphens/underscores)
        clean = raw_id.upper()
        if len(clean) < 3 or not any(c.isalnum() for c in clean):
            raise ValueError(f"Invalid company identifier '{raw_id}'")
        return clean

    elif etype == WatchlistEntityType.BILL:
        clean = raw_id.strip().lower()
        if len(clean) < 3 or not any(c.isalnum() for c in clean):
            raise ValueError(f"Invalid bill identifier '{raw_id}'")
        return clean

    elif etype in (WatchlistEntityType.SECTOR, WatchlistEntityType.INDUSTRY):
        if len(raw_id) < 2:
            raise ValueError(f"Invalid {etype.value} identifier '{raw_id}'")
        return raw_id.strip()

    return raw_id


@dataclass
class Watchlist:
    """
    User collection of watched legislative and corporate entities.

    Attributes
    ----------
    watchlist_id : str
        Unique watchlist ID.
    user_id : str
        Owner user ID.
    tenant_id : str
        Tenant identifier for multi-tenant isolation.
    name : str
        Watchlist title.
    description : Optional[str]
        Optional user notes or description.
    is_default : bool
        Whether this is the user's primary/default watchlist.
    is_active : bool
        Active status flag.
    created_at : str
        UTC ISO timestamp.
    updated_at : str
        UTC ISO timestamp.
    """

    watchlist_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    name: str = "Default Watchlist"
    description: Optional[str] = None
    is_default: bool = False
    is_active: bool = True
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        """Validate watchlist invariants."""
        if not self.watchlist_id or not self.watchlist_id.strip():
            raise ValueError("watchlist_id cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Watchlist name cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize Watchlist to dictionary."""
        return {
            "watchlist_id": self.watchlist_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Watchlist":
        """Deserialize Watchlist from dictionary."""
        obj = cls(
            watchlist_id=data.get("watchlist_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "default_user"),
            tenant_id=data.get("tenant_id", "default_tenant"),
            name=data.get("name", "Default Watchlist"),
            description=data.get("description"),
            is_default=data.get("is_default", False),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", _utcnow_iso()),
            updated_at=data.get("updated_at", _utcnow_iso()),
        )
        obj.validate()
        return obj


@dataclass
class WatchlistItem:
    """
    An individual watched entity item belonging to a specific Watchlist.

    Attributes
    ----------
    item_id : str
        Unique item record ID.
    watchlist_id : str
        Foreign key referencing parent Watchlist.
    user_id : str
        Owner user ID.
    tenant_id : str
        Tenant identifier for multi-tenant isolation.
    entity_type : WatchlistEntityType
        Category of entity (COMPANY, BILL, SECTOR, INDUSTRY, STATE, JURISDICTION).
    entity_id : str
        Canonical, stable identifier for the entity.
    display_name : str
        Human-readable snapshot label (e.g. 'Swiggy Limited', 'Kerala Gig Workers Bill').
    notes : Optional[str]
        Optional custom user notes for this item.
    custom_tags : list[str]
        Optional user tags.
    is_active : bool
        Active status flag.
    created_at : str
        UTC ISO timestamp.
    """

    watchlist_id: str
    entity_type: WatchlistEntityType
    entity_id: str
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    display_name: str = ""
    notes: Optional[str] = None
    custom_tags: list[str] = field(default_factory=list)
    is_active: bool = True
    created_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        """Validate item integrity and entity reference."""
        if not self.item_id or not self.item_id.strip():
            raise ValueError("item_id cannot be empty")
        if not self.watchlist_id or not self.watchlist_id.strip():
            raise ValueError("watchlist_id cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty")
        if not isinstance(self.entity_type, WatchlistEntityType):
            try:
                self.entity_type = WatchlistEntityType(str(self.entity_type).strip().upper())
            except ValueError:
                raise ValueError(f"Invalid entity_type: {self.entity_type}")
        # Normalize and validate entity reference
        self.entity_id = validate_entity_reference(self.entity_type, self.entity_id)

    def to_dict(self) -> dict[str, Any]:
        """Serialize WatchlistItem to dictionary."""
        return {
            "item_id": self.item_id,
            "watchlist_id": self.watchlist_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "entity_type": self.entity_type.value
            if isinstance(self.entity_type, WatchlistEntityType)
            else str(self.entity_type),
            "entity_id": self.entity_id,
            "display_name": self.display_name,
            "notes": self.notes,
            "custom_tags": self.custom_tags,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WatchlistItem":
        """Deserialize WatchlistItem from dictionary."""
        raw_type = data.get("entity_type", WatchlistEntityType.COMPANY.value)
        if isinstance(raw_type, WatchlistEntityType):
            etype = raw_type
        else:
            try:
                etype = WatchlistEntityType(str(raw_type).strip().upper())
            except ValueError:
                etype = WatchlistEntityType.COMPANY

        obj = cls(
            item_id=data.get("item_id", str(uuid.uuid4())),
            watchlist_id=data.get("watchlist_id", ""),
            user_id=data.get("user_id", "default_user"),
            tenant_id=data.get("tenant_id", "default_tenant"),
            entity_type=etype,
            entity_id=data.get("entity_id", ""),
            display_name=data.get("display_name", ""),
            notes=data.get("notes"),
            custom_tags=data.get("custom_tags", []),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", _utcnow_iso()),
        )
        obj.validate()
        return obj
