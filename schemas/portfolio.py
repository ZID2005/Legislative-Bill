"""
schemas/portfolio.py
====================
Task 8.28 — Decision Intelligence & Personalized Impact Workspace.

Multi-tenant Portfolio and PortfolioHolding domain models.
Provides strict user and tenant scoping for personal portfolio management.

Safety Invariants:
1. Decision support only — never automated investment advice.
2. No Buy / Sell / Hold recommendations or price targets.
3. User-provided data is strictly separated from platform-derived data.
4. Tenant and user isolation guaranteed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
import uuid


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PortfolioHolding:
    """A user-owned portfolio holding representing equity or enterprise exposure."""

    holding_id: str
    company_name: str
    ticker: Optional[str] = None
    isin: Optional[str] = None
    quantity: Optional[float] = None
    avg_purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "holding_id": self.holding_id,
            "company_name": self.company_name,
            "ticker": self.ticker,
            "isin": self.isin,
            "quantity": self.quantity,
            "avg_purchase_price": self.avg_purchase_price,
            "current_value": self.current_value,
            "sector": self.sector,
            "industry": self.industry,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PortfolioHolding:
        return cls(
            holding_id=str(data.get("holding_id") or uuid.uuid4()),
            company_name=str(data.get("company_name", "")).strip(),
            ticker=data.get("ticker"),
            isin=data.get("isin"),
            quantity=float(data["quantity"]) if data.get("quantity") is not None else None,
            avg_purchase_price=float(data["avg_purchase_price"]) if data.get("avg_purchase_price") is not None else None,
            current_value=float(data["current_value"]) if data.get("current_value") is not None else None,
            sector=data.get("sector"),
            industry=data.get("industry"),
            notes=data.get("notes"),
            created_at=data.get("created_at") or _utcnow_iso(),
            updated_at=data.get("updated_at") or _utcnow_iso(),
        )


@dataclass
class UserPortfolio:
    """User-scoped portfolio supporting multi-tenant isolation."""

    portfolio_id: str
    user_id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    holdings: list[PortfolioHolding] = field(default_factory=list)
    is_active: bool = True
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        if not self.portfolio_id or not self.portfolio_id.strip():
            raise ValueError("portfolio_id cannot be blank")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be blank")
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be blank")
        if not self.name or not self.name.strip():
            raise ValueError("portfolio name cannot be blank")

    def to_dict(self) -> dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "holdings": [h.to_dict() for h in self.holdings],
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserPortfolio:
        raw_holdings = data.get("holdings", [])
        holdings = [PortfolioHolding.from_dict(h) if isinstance(h, dict) else h for h in raw_holdings]
        return cls(
            portfolio_id=str(data.get("portfolio_id") or uuid.uuid4()),
            user_id=str(data.get("user_id", "")),
            tenant_id=str(data.get("tenant_id", "")),
            name=str(data.get("name", "Default Portfolio")),
            description=data.get("description"),
            holdings=holdings,
            is_active=bool(data.get("is_active", True)),
            created_at=data.get("created_at") or _utcnow_iso(),
            updated_at=data.get("updated_at") or _utcnow_iso(),
        )
