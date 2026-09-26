"""
schemas/tenant.py
=================
Multi-tenant Organization data model for SaaS launch readiness (Task 8.19).

Enforces:
1. Stable tenant identifier.
2. Organization status lifecycle (ACTIVE, INACTIVE, TRIAL, SUSPENDED, DELETED).
3. Non-functional billing boundary placeholder (BILLING_NOT_CONNECTED / PLAN_NOT_CONFIGURED).
4. Ownership attribution to an authoritative user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Tenant:
    """
    Tenant (Organization) entity representing an isolated tenant workspace.

    Attributes
    ----------
    tenant_id : str
        Unique organization identifier (e.g., 'org_acme', 'tenant_alpha').
    name : str
        Human-readable organization name.
    status : str
        Lifecycle status: 'ACTIVE', 'INACTIVE', 'TRIAL', 'SUSPENDED', 'DELETED'.
    plan_tier : str
        Plan level: 'FREE', 'PRO', 'TEAM', 'ENTERPRISE', or 'PLAN_NOT_CONFIGURED'.
    billing_status : str
        Billing connectivity: 'BILLING_NOT_CONNECTED' or 'PLAN_CONFIGURED'.
    owner_user_id : str
        User ID of the organization primary owner.
    created_at : str
        UTC ISO-8601 creation timestamp.
    updated_at : str
        UTC ISO-8601 last update timestamp.
    metadata : dict[str, Any]
        Arbitrary organization configuration and preference metadata.
    """

    tenant_id: str
    name: str
    status: str = "ACTIVE"
    plan_tier: str = "PLAN_NOT_CONFIGURED"
    billing_status: str = "BILLING_NOT_CONNECTED"
    owner_user_id: str = "default_user"
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate tenant invariants."""
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be empty or blank")
        if not self.name or not self.name.strip():
            raise ValueError("name cannot be empty or blank")
        if self.status not in ("ACTIVE", "INACTIVE", "TRIAL", "SUSPENDED", "DELETED"):
            raise ValueError(f"Invalid tenant status: {self.status}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize Tenant to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "status": self.status,
            "plan_tier": self.plan_tier,
            "billing_status": self.billing_status,
            "owner_user_id": self.owner_user_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Tenant":
        """Deserialize Tenant from dictionary with safe fallbacks."""
        tenant = cls(
            tenant_id=data.get("tenant_id", "default_tenant"),
            name=data.get("name", "Default Organization"),
            status=data.get("status", "ACTIVE"),
            plan_tier=data.get("plan_tier", "PLAN_NOT_CONFIGURED"),
            billing_status=data.get("billing_status", "BILLING_NOT_CONNECTED"),
            owner_user_id=data.get("owner_user_id", "default_user"),
            created_at=data.get("created_at", _utcnow_iso()),
            updated_at=data.get("updated_at", _utcnow_iso()),
            metadata=data.get("metadata", {}),
        )
        tenant.validate()
        return tenant
