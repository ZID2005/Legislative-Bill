"""
storage/portfolio_repository.py
===============================
Task 8.28 & Task 8.31D — Persistent Multi-Tenant User Portfolio Repository.

Storage layout:
  Database: PostgreSQL / SQLite `portfolios` and `portfolio_holdings` tables
  Filesystem: storage/portfolios/{tenant_id}/{user_id}/portfolio_{portfolio_id}.json

Enforces strict tenant isolation and user isolation on all read and write operations.
Operates with canonical database persistence while maintaining filesystem cache/fallback.
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
    Persists to canonical PostgreSQL / SQLite database with filesystem fallback.
    """

    def __init__(self, root_dir: Optional[Path] = None, storage_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or storage_dir or _get_default_portfolios_dir()
        ensure_dir(self._root_dir)

    def _get_db(self) -> Any:
        if self._root_dir != _get_default_portfolios_dir():
            return None
        try:
            from storage.database.provider import get_database_provider
            db = get_database_provider()
            if db and db.status in ("READY", "CONFIGURED"):
                return db
        except Exception:
            pass
        return None

    def _user_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._root_dir / tenant_id / user_id
        ensure_dir(path)
        return path

    def _portfolio_path(self, tenant_id: str, user_id: str, portfolio_id: str) -> Path:
        return self._user_dir(tenant_id, user_id) / f"portfolio_{portfolio_id}.json"

    def save(self, portfolio: UserPortfolio) -> UserPortfolio:
        """Create or overwrite a portfolio."""
        portfolio.validate()
        path = self._portfolio_path(portfolio.tenant_id, portfolio.user_id, portfolio.portfolio_id)
        if path.is_file():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(portfolio.to_dict(), f, indent=2)
            return portfolio
        return self.create(portfolio)

    def create(self, portfolio: UserPortfolio) -> UserPortfolio:
        """Create and persist a new portfolio."""
        portfolio.validate()
        path = self._portfolio_path(portfolio.tenant_id, portfolio.user_id, portfolio.portfolio_id)
        if path.is_file():
            raise ValueError(
                f"Portfolio '{portfolio.portfolio_id}' already exists for user '{portfolio.user_id}' in tenant '{portfolio.tenant_id}'"
            )

        # 1. Database Persistence
        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    """
                    INSERT INTO portfolios (portfolio_id, tenant_id, user_id, name, description, is_active, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        portfolio.portfolio_id,
                        portfolio.tenant_id,
                        portfolio.user_id,
                        portfolio.name,
                        portfolio.description,
                        portfolio.is_active,
                        portfolio.created_at,
                        portfolio.updated_at,
                    ),
                    tenant_id=portfolio.tenant_id,
                )
                for h in portfolio.holdings:
                    db.execute_mutation(
                        """
                        INSERT INTO portfolio_holdings (
                            holding_id, portfolio_id, tenant_id, user_id, company_name, ticker, isin,
                            quantity, avg_purchase_price, current_value, sector, industry, notes, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """,
                        (
                            h.holding_id,
                            portfolio.portfolio_id,
                            portfolio.tenant_id,
                            portfolio.user_id,
                            h.company_name,
                            h.ticker or "",
                            h.isin or "",
                            float(h.quantity or 1.0),
                            float(h.avg_purchase_price or 0.0),
                            float(h.current_value or 0.0),
                            h.sector,
                            h.industry,
                            h.notes,
                            h.created_at,
                            h.updated_at,
                        ),
                        tenant_id=portfolio.tenant_id,
                    )
            except Exception as e:
                logger.debug("DB insert for portfolio %s skipped/failed: %s", portfolio.portfolio_id, e)

        # 2. File Persistence
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
        # 1. Try DB first
        db = self._get_db()
        if db:
            try:
                p_rows = db.execute_query(
                    """
                    SELECT portfolio_id, tenant_id, user_id, name, description, is_active, created_at, updated_at
                    FROM portfolios
                    WHERE portfolio_id = %s AND tenant_id = %s AND user_id = %s;
                    """,
                    (portfolio_id, tenant_id, user_id),
                    tenant_id=tenant_id,
                )
                if p_rows:
                    p_data = p_rows[0]
                    h_rows = db.execute_query(
                        """
                        SELECT holding_id, company_name, ticker, isin, quantity, avg_purchase_price, current_value, sector, industry, notes, created_at, updated_at
                        FROM portfolio_holdings
                        WHERE portfolio_id = %s AND tenant_id = %s AND user_id = %s;
                        """,
                        (portfolio_id, tenant_id, user_id),
                        tenant_id=tenant_id,
                    )
                    holdings = [PortfolioHolding.from_dict(h) for h in h_rows]
                    return UserPortfolio(
                        portfolio_id=p_data["portfolio_id"],
                        user_id=p_data["user_id"],
                        tenant_id=p_data["tenant_id"],
                        name=p_data["name"],
                        description=p_data.get("description"),
                        holdings=holdings,
                        is_active=bool(p_data.get("is_active", True)),
                        created_at=str(p_data.get("created_at")),
                        updated_at=str(p_data.get("updated_at")),
                    )
            except Exception as e:
                logger.debug("DB get for portfolio %s failed: %s", portfolio_id, e)

        # 2. Fallback to file storage
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

    def get_any_tenant(self, portfolio_id: str) -> Optional[UserPortfolio]:
        """
        Look up a portfolio across all tenants strictly to detect cross-tenant unauthorized access attempts.
        """
        db = self._get_db()
        if db:
            try:
                p_rows = db.execute_query(
                    """
                    SELECT portfolio_id, tenant_id, user_id, name, description, is_active, created_at, updated_at
                    FROM portfolios
                    WHERE portfolio_id = %s;
                    """,
                    (portfolio_id,),
                )
                if p_rows:
                    p_data = p_rows[0]
                    return UserPortfolio(
                        portfolio_id=p_data["portfolio_id"],
                        user_id=p_data["user_id"],
                        tenant_id=p_data["tenant_id"],
                        name=p_data["name"],
                        description=p_data.get("description"),
                        holdings=[],
                        is_active=bool(p_data.get("is_active", True)),
                        created_at=str(p_data.get("created_at")),
                        updated_at=str(p_data.get("updated_at")),
                    )
            except Exception as e:
                logger.debug("DB get_any_tenant failed for %s: %s", portfolio_id, e)

        # File scan fallback across tenant dirs
        if self._root_dir.is_dir():
            for t_dir in self._root_dir.iterdir():
                if t_dir.is_dir():
                    for u_dir in t_dir.iterdir():
                        if u_dir.is_dir():
                            p_file = u_dir / f"portfolio_{portfolio_id}.json"
                            if p_file.is_file():
                                try:
                                    with open(p_file, "r", encoding="utf-8") as f:
                                        data = json.load(f)
                                    return UserPortfolio.from_dict(data)
                                except Exception:
                                    pass
        return None

    def list_by_user(
        self,
        user_id: str,
        tenant_id: str,
        is_active: Optional[bool] = None,
    ) -> list[UserPortfolio]:
        """List all portfolios belonging strictly to the specified tenant and user."""
        # 1. Try DB first
        db = self._get_db()
        if db:
            try:
                where_clauses = ["tenant_id = %s", "user_id = %s"]
                params: list[Any] = [tenant_id, user_id]
                if is_active is not None:
                    where_clauses.append("is_active = %s")
                    params.append(is_active)

                sql = f"""
                SELECT portfolio_id, tenant_id, user_id, name, description, is_active, created_at, updated_at
                FROM portfolios
                WHERE {' AND '.join(where_clauses)}
                ORDER BY created_at DESC;
                """
                p_rows = db.execute_query(sql, tuple(params), tenant_id=tenant_id)
                if p_rows:
                    portfolios = []
                    for p_data in p_rows:
                        pid = p_data["portfolio_id"]
                        h_rows = db.execute_query(
                            """
                            SELECT holding_id, company_name, ticker, isin, quantity, avg_purchase_price, current_value, sector, industry, notes, created_at, updated_at
                            FROM portfolio_holdings
                            WHERE portfolio_id = %s AND tenant_id = %s AND user_id = %s;
                            """,
                            (pid, tenant_id, user_id),
                            tenant_id=tenant_id,
                        )
                        holdings = [PortfolioHolding.from_dict(h) for h in h_rows]
                        portfolios.append(
                            UserPortfolio(
                                portfolio_id=pid,
                                user_id=p_data["user_id"],
                                tenant_id=p_data["tenant_id"],
                                name=p_data["name"],
                                description=p_data.get("description"),
                                holdings=holdings,
                                is_active=bool(p_data.get("is_active", True)),
                                created_at=str(p_data.get("created_at")),
                                updated_at=str(p_data.get("updated_at")),
                            )
                        )
                    return portfolios
            except Exception as e:
                logger.debug("DB list_by_user failed: %s", e)

        # 2. Fallback to file storage
        u_dir = self._user_dir(tenant_id, user_id)
        portfolios = []

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

        # 1. Update DB
        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    """
                    UPDATE portfolios
                    SET name = %s, description = %s, is_active = %s, updated_at = %s
                    WHERE portfolio_id = %s AND tenant_id = %s AND user_id = %s;
                    """,
                    (
                        portfolio.name,
                        portfolio.description,
                        portfolio.is_active,
                        portfolio.updated_at,
                        portfolio.portfolio_id,
                        portfolio.tenant_id,
                        portfolio.user_id,
                    ),
                    tenant_id=portfolio.tenant_id,
                )
                # Resync holdings
                db.execute_mutation(
                    "DELETE FROM portfolio_holdings WHERE portfolio_id = %s AND tenant_id = %s AND user_id = %s;",
                    (portfolio.portfolio_id, portfolio.tenant_id, portfolio.user_id),
                    tenant_id=portfolio.tenant_id,
                )
                for h in portfolio.holdings:
                    db.execute_mutation(
                        """
                        INSERT INTO portfolio_holdings (
                            holding_id, portfolio_id, tenant_id, user_id, company_name, ticker, isin,
                            quantity, avg_purchase_price, current_value, sector, industry, notes, created_at, updated_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                        """,
                        (
                            h.holding_id,
                            portfolio.portfolio_id,
                            portfolio.tenant_id,
                            portfolio.user_id,
                            h.company_name,
                            h.ticker or "",
                            h.isin or "",
                            float(h.quantity or 1.0),
                            float(h.avg_purchase_price or 0.0),
                            float(h.current_value or 0.0),
                            h.sector,
                            h.industry,
                            h.notes,
                            h.created_at,
                            h.updated_at,
                        ),
                        tenant_id=portfolio.tenant_id,
                    )
            except Exception as e:
                logger.debug("DB update for portfolio %s failed: %s", portfolio.portfolio_id, e)

        # 2. Update File
        with open(path, "w", encoding="utf-8") as f:
            json.dump(portfolio.to_dict(), f, indent=2)
        return portfolio

    def delete(self, portfolio_id: str, tenant_id: str, user_id: str) -> bool:
        """Soft-delete (deactivate) or remove portfolio."""
        path = self._portfolio_path(tenant_id, user_id, portfolio_id)
        deleted = False

        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    "DELETE FROM portfolio_holdings WHERE portfolio_id = %s AND tenant_id = %s AND user_id = %s;",
                    (portfolio_id, tenant_id, user_id),
                    tenant_id=tenant_id,
                )
                cnt = db.execute_mutation(
                    "DELETE FROM portfolios WHERE portfolio_id = %s AND tenant_id = %s AND user_id = %s;",
                    (portfolio_id, tenant_id, user_id),
                    tenant_id=tenant_id,
                )
                if cnt > 0:
                    deleted = True
            except Exception as e:
                logger.debug("DB delete for portfolio %s failed: %s", portfolio_id, e)

        if path.is_file():
            try:
                path.unlink()
                deleted = True
            except OSError as e:
                logger.error("Failed to delete portfolio file %s: %s", portfolio_id, e)

        return deleted

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
