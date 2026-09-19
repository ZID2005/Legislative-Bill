"""
schemas/user.py
===============
Minimal future-compatible User data model for multi-tenant Watchlists and Alerts.

Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class User:
    """
    User entity supporting future-compatible tenant isolation.

    Attributes
    ----------
    user_id : str
        Stable unique user identifier.
    tenant_id : str
        Organization or tenant identifier. Defaults to 'default_tenant' for local dev.
    display_name : str
        Human-readable name or moniker for the user.
    email : Optional[str]
        User contact email address if provided.
    is_active : bool
        Whether the user account is active.
    created_at : str
        UTC ISO-8601 creation timestamp.
    updated_at : str
        UTC ISO-8601 last update timestamp.
    """

    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    display_name: str = ""
    email: Optional[str] = None
    is_active: bool = True
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        """Validate user invariants deterministically."""
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty or blank")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty or blank")

    def to_dict(self) -> dict[str, Any]:
        """Serialize User to dictionary."""
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "display_name": self.display_name,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Deserialize User from dictionary with safe fallbacks."""
        user = cls(
            user_id=data.get("user_id", "default_user"),
            tenant_id=data.get("tenant_id", "default_tenant"),
            display_name=data.get("display_name", ""),
            email=data.get("email"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", _utcnow_iso()),
            updated_at=data.get("updated_at", _utcnow_iso()),
        )
        user.validate()
        return user
