"""
schemas/user.py
===============
User data model supporting multi-tenant isolation, RBAC, and SaaS account lifecycle (Task 8.19).

Enforces:
1. Strict user_id and tenant_id invariants.
2. Canonical RBAC roles: OWNER, ADMIN, MEMBER, VIEWER.
3. Account status lifecycle: ACTIVE, INACTIVE, SUSPENDED, PENDING_INVITE, DELETED.
4. Cryptographic salted password storage (never plaintext).
5. Minimum required IdP mapping without storing extraneous sensitive metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import hmac
import os
from typing import Any, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{key.hex()}"


def verify_password(stored_hash: str, password: str) -> bool:
    """Verify password against stored salt:hash string."""
    try:
        salt_hex, key_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        check_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(key, check_key)
    except Exception:
        return False


VALID_ROLES = ("OWNER", "ADMIN", "MEMBER", "VIEWER")
VALID_STATUSES = ("ACTIVE", "INACTIVE", "SUSPENDED", "PENDING_INVITE", "DELETED")


@dataclass
class User:
    """
    User entity supporting multi-tenant isolation and role-based permissions.

    Attributes
    ----------
    user_id : str
        Stable unique user identifier.
    tenant_id : str
        Organization identifier. Defaults to 'default_tenant' for local dev.
    display_name : str
        Human-readable name or moniker for the user.
    email : Optional[str]
        User contact email address if provided.
    role : str
        User role: 'OWNER', 'ADMIN', 'MEMBER', or 'VIEWER'.
    status : str
        Account status: 'ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING_INVITE', 'DELETED'.
    is_active : bool
        Whether the user account is active (syncs with status == 'ACTIVE').
    last_active_at : Optional[str]
        UTC ISO-8601 timestamp of last user action.
    password_hash : Optional[str]
        Salted PBKDF2 hash (if local credential auth is enabled; never plaintext).
    idp_subject_id : Optional[str]
        External identity provider identifier (e.g., Okta/Auth0 sub claim).
    created_at : str
        UTC ISO-8601 creation timestamp.
    updated_at : str
        UTC ISO-8601 last update timestamp.
    metadata : dict[str, Any]
        User preferences and settings metadata.
    """

    user_id: str = "default_user"
    tenant_id: str = "default_tenant"
    display_name: str = ""
    email: Optional[str] = None
    role: str = "MEMBER"
    status: str = "ACTIVE"
    is_active: bool = True
    last_active_at: Optional[str] = None
    password_hash: Optional[str] = None
    idp_subject_id: Optional[str] = None
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate user invariants deterministically."""
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty or blank")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty or blank")
        role_upper = self.role.upper()
        if role_upper not in VALID_ROLES:
            raise ValueError(f"Invalid user role: {self.role}. Must be one of {VALID_ROLES}")
        self.role = role_upper

        status_upper = self.status.upper()
        if status_upper not in VALID_STATUSES:
            raise ValueError(f"Invalid user status: {self.status}. Must be one of {VALID_STATUSES}")
        self.status = status_upper
        self.is_active = (self.status == "ACTIVE")

    @property
    def is_owner(self) -> bool:
        return self.role == "OWNER"

    @property
    def is_admin(self) -> bool:
        return self.role in ("OWNER", "ADMIN")

    @property
    def is_member(self) -> bool:
        return self.role in ("OWNER", "ADMIN", "MEMBER")

    @property
    def is_viewer(self) -> bool:
        return self.role == "VIEWER"

    def to_dict(self, include_sensitive: bool = False) -> dict[str, Any]:
        """Serialize User to dictionary. By default excludes password_hash."""
        data: dict[str, Any] = {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "display_name": self.display_name,
            "email": self.email,
            "role": self.role,
            "status": self.status,
            "is_active": self.is_active,
            "last_active_at": self.last_active_at,
            "idp_subject_id": self.idp_subject_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
        if include_sensitive and self.password_hash:
            data["password_hash"] = self.password_hash
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        """Deserialize User from dictionary with safe backward-compatible fallbacks."""
        status = data.get("status")
        if not status:
            is_active = data.get("is_active", True)
            status = "ACTIVE" if is_active else "INACTIVE"

        role = data.get("role", "MEMBER")
        # Map legacy analyst role to MEMBER if present
        if role.lower() == "analyst":
            role = "MEMBER"

        user = cls(
            user_id=data.get("user_id", "default_user"),
            tenant_id=data.get("tenant_id", "default_tenant"),
            display_name=data.get("display_name", ""),
            email=data.get("email"),
            role=role,
            status=status,
            is_active=data.get("is_active", True),
            last_active_at=data.get("last_active_at"),
            password_hash=data.get("password_hash"),
            idp_subject_id=data.get("idp_subject_id"),
            created_at=data.get("created_at", _utcnow_iso()),
            updated_at=data.get("updated_at", _utcnow_iso()),
            metadata=data.get("metadata", {}),
        )
        user.validate()
        return user
