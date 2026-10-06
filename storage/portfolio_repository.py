"""
storage/portfolio_repository.py
===============================
Task 8.28 — Multi-Tenant User Portfolio Repository.

Storage layout:
  storage/portfolios/{tenant_id}/{user_id}/portfolio_{portfolio_id}.json

Enforces strict tenant isolation and user isolation on all read and write operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional
import uuid

from config.logging_config import get_logger
from config.settings import settings
from schemas.portfolio import PortfolioHolding, UserPortfolio
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_default_portfolios_dir() -> Path:
    root = getattr(settings, "PORTFOLIO_DIR", settings.PROJECT_ROOT / "storage" / "portfolios")
    ensure_dir(root)
    return root


class PortfolioRepository:
    """
    Repository for managing user portfolios and holdings with strict multi-tenant isolation.
    """

    def __init__(self, root_dir: Optional[Path] = None, storage_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or storage_dir or _get_default_portfolios_dir()
        ensure_dir(self._root_dir)

    def _user_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._root_dir / tenant_id / user_id
        ensure_dir(path)
        return path

    def _portfolio_path(self, tenant_id: str, user_id: str, portfolio_id: str) -> Path:
        return self._user_dir(tenant_id, user_id) / f"portfolio_{portfolio_id}.json"

    def create(self, portfolio: UserPortfolio) -> UserPortfolio:
        """Create and persist a new portfolio."""
        portfolio.validate()
        path = self._portfolio_path(portfolio.tenant_id, portfolio.user_id, portfolio.portfolio_id)
        if path.is_file():
            raise ValueError(
                f"Portfolio '{portfolio.portfolio_id}' already exists for user '{portfolio.user_id}' in tenant '{portfolio.tenant_id}'"
            )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(portfolio.to_dict(), f, indent=2)
        logger.debug("Created portfolio %s for user %s", portfolio.portfolio_id, portfolio.user_id)
        return portfolio

    def get(
        self,
        portfolio_id: str,
        tenant_id: str,
        user_id: str,
    ) -> Optional[UserPortfolio]:
        """
        Retrieve portfolio by ID, strictly enforcing tenant and user isolation.
        Returns None if not found or if cross-tenant/user access is attempted.
        """
        path = self._portfolio_path(tenant_id, user_id, portfolio_id)
        if not path.is_file():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            portfolio = UserPortfolio.from_dict(data)
            # Defensive check against IDOR
            if portfolio.tenant_id != tenant_id or portfolio.user_id != user_id:
                logger.warning(
                    "IDOR attempt detected | file_tenant=%s req_tenant=%s file_user=%s req_user=%s",
                    portfolio.tenant_id, tenant_id, portfolio.user_id, user_id,
                )
                return None
            return portfolio
        except Exception as e:
            logger.error("Failed to load portfolio %s: %s", portfolio_id, e)
            return None

    def list_by_user(
        self,
        user_id: str,
        tenant_id: str,
        is_active: Optional[bool] = None,
    ) -> list[UserPortfolio]:
        """List all portfolios belonging strictly to the specified tenant and user."""
        u_dir = self._user_dir(tenant_id, user_id)
        portfolios: list[UserPortfolio] = []

        for p_file in u_dir.glob("portfolio_*.json"):
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                pf = UserPortfolio.from_dict(data)
                if pf.tenant_id == tenant_id and pf.user_id == user_id:
                    if is_active is None or pf.is_active == is_active:
                        portfolios.append(pf)
            except Exception as e:
                logger.warning("Error reading portfolio file %s: %s", p_file, e)

        portfolios.sort(key=lambda x: x.created_at, reverse=True)
        return portfolios

    def update(self, portfolio: UserPortfolio) -> UserPortfolio:
        """Update an existing portfolio."""
        portfolio.validate()
        portfolio.updated_at = _utcnow_iso()
        path = self._portfolio_path(portfolio.tenant_id, portfolio.user_id, portfolio.portfolio_id)
        if not path.is_file():
            raise KeyError(f"Portfolio '{portfolio.portfolio_id}' not found for user '{portfolio.user_id}'")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(portfolio.to_dict(), f, indent=2)
        return portfolio

    def delete(self, portfolio_id: str, tenant_id: str, user_id: str) -> bool:
        """Soft-delete (deactivate) or remove portfolio."""
        path = self._portfolio_path(tenant_id, user_id, portfolio_id)
        if not path.is_file():
            return False
        try:
            path.unlink()
            return True
        except OSError as e:
            logger.error("Failed to delete portfolio %s: %s", portfolio_id, e)
            return False

    def add_holding(
        self,
        portfolio_id: str,
        holding: PortfolioHolding,
        tenant_id: str,
        user_id: str,
    ) -> PortfolioHolding:
        """Add a holding to an existing portfolio."""
        pf = self.get(portfolio_id, tenant_id, user_id)
        if not pf:
            raise KeyError(f"Portfolio '{portfolio_id}' not found for user '{user_id}'")

        # Check duplicate holding by isin or company_name
        existing_ids = {h.holding_id for h in pf.holdings}
        if holding.holding_id in existing_ids:
            holding.holding_id = str(uuid.uuid4())

        holding.created_at = _utcnow_iso()
        holding.updated_at = _utcnow_iso()
        pf.holdings.append(holding)
        self.update(pf)
        return holding

    def remove_holding(
        self,
        portfolio_id: str,
        holding_id: str,
        tenant_id: str,
        user_id: str,
    ) -> bool:
        """Remove a holding from an existing portfolio."""
        pf = self.get(portfolio_id, tenant_id, user_id)
        if not pf:
            return False

        orig_len = len(pf.holdings)
        pf.holdings = [h for h in pf.holdings if h.holding_id != holding_id]
        if len(pf.holdings) == orig_len:
            return False

        self.update(pf)
        return True

    def update_holding(
        self,
        portfolio_id: str,
        holding_id: str,
        tenant_id: str,
        user_id: str,
        updates: dict[str, Any],
    ) -> Optional[PortfolioHolding]:
        """Update fields of an existing holding in a portfolio."""
        pf = self.get(portfolio_id, tenant_id=tenant_id, user_id=user_id)
        if not pf:
            return None

        target = None
        for h in pf.holdings:
            if h.holding_id == holding_id:
                target = h
                break
        if not target:
            return None

        for k, v in updates.items():
            if hasattr(target, k) and v is not None:
                setattr(target, k, v)
        target.updated_at = _utcnow_iso()
        self.update(pf)
        return target

    def get_or_create_default(self, user_id: str, tenant_id: str) -> UserPortfolio:
        """Get the default portfolio for a user, or create one with initial seed data if none exists."""
        existing = self.list_by_user(user_id, tenant_id, is_active=True)
        if existing:
            return existing[0]

        default_pf = UserPortfolio(
            portfolio_id=f"pf_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            tenant_id=tenant_id,
            name="Primary Investment Portfolio",
            description="Default tracking portfolio for legislative and regulatory exposure analysis.",
            holdings=[
                PortfolioHolding(
                    holding_id=f"h_{uuid.uuid4().hex[:8]}",
                    company_name="Reliance Industries",
                    ticker="RELIANCE",
                    isin="INE002A01018",
                    quantity=50,
                    avg_purchase_price=2650.0,
                    current_value=2820.0,
                    sector="Energy",
                    industry="Oil & Gas",
                ),
                PortfolioHolding(
                    holding_id=f"h_{uuid.uuid4().hex[:8]}",
                    company_name="Infosys Limited",
                    ticker="INFY",
                    isin="INE009A01021",
                    quantity=100,
                    avg_purchase_price=1520.0,
                    current_value=1610.0,
                    sector="Technology",
                    industry="IT Services",
                ),
                PortfolioHolding(
                    holding_id=f"h_{uuid.uuid4().hex[:8]}",
                    company_name="ICICI Bank Limited",
                    ticker="ICICIBANK",
                    isin="INE090A01021",
                    quantity=200,
                    avg_purchase_price=950.0,
                    current_value=1020.0,
                    sector="Financials",
                    industry="Banking",
                ),
                PortfolioHolding(
                    holding_id=f"h_{uuid.uuid4().hex[:8]}",
                    company_name="Larsen & Toubro",
                    ticker="LT",
                    isin="INE018A01030",
                    quantity=30,
                    avg_purchase_price=3200.0,
                    current_value=3450.0,
                    sector="Industrials",
                    industry="Construction & Engineering",
                ),
            ],
            is_active=True,
            created_at=_utcnow_iso(),
            updated_at=_utcnow_iso(),
        )
        return self.create(default_pf)

    def import_holdings(
        self,
        portfolio_id: str,
        holdings: list[PortfolioHolding],
        tenant_id: str,
        user_id: str,
        replace: bool = False,
    ) -> UserPortfolio:
        """Import multiple holdings into a portfolio."""
        pf = self.get(portfolio_id, tenant_id, user_id)
        if not pf:
            raise KeyError(f"Portfolio '{portfolio_id}' not found for user '{user_id}'")

        if replace:
            pf.holdings = holdings
        else:
            existing_isins = {h.isin for h in pf.holdings if h.isin}
            existing_names = {h.company_name.lower() for h in pf.holdings}
            for new_h in holdings:
                if (new_h.isin and new_h.isin in existing_isins) or (new_h.company_name.lower() in existing_names):
                    continue
                pf.holdings.append(new_h)

        self.update(pf)
        return pf
