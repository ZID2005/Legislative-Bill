"""
storage/tenant_repository.py
============================
Repository for Tenant (Organization) entities supporting SaaS isolation (Task 8.19).

Persists tenant master records deterministically to:
  storage/tenants/tenant_{tenant_id}.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.tenant import Tenant
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_tenants_dir() -> Path:
    root = settings.TENANTS_DIR
    ensure_dir(root)
    return root


class TenantRepository:
    """
    Repository managing Tenant entities with dual DB and JSON persistence.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_tenants_dir()
        ensure_dir(self._root_dir)

    def _get_db(self) -> Any:
        if self._root_dir != _get_default_tenants_dir():
            return None
        try:
            from storage.database.provider import get_database_provider
            db = get_database_provider()
            if db and db.status in ("READY", "CONFIGURED"):
                return db
        except Exception:
            pass
        return None

    def _tenant_path(self, tenant_id: str) -> Path:
        return self._root_dir / f"tenant_{tenant_id}.json"

    def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant record. Raises ValueError if tenant already exists."""
        tenant.validate()
        path = self._tenant_path(tenant.tenant_id)
        if path.is_file():
            raise ValueError(f"Tenant '{tenant.tenant_id}' already exists")

        # 1. Database Persistence
        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    """
                    INSERT INTO tenants (tenant_id, name, plan_tier, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        plan_tier = EXCLUDED.plan_tier,
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at;
                    """,
                    (
                        tenant.tenant_id,
                        tenant.name,
                        tenant.plan_tier or "FREE",
                        tenant.status or "ACTIVE",
                        tenant.created_at,
                        tenant.updated_at,
                    ),
                    tenant_id=tenant.tenant_id,
                )
            except Exception as e:
                logger.debug("DB insert for tenant %s failed: %s", tenant.tenant_id, e)

        # 2. File Persistence
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tenant.to_dict(), f, indent=2)
        logger.info("Created tenant '%s' (owner: %s)", tenant.tenant_id, tenant.owner_user_id)
        return tenant

    def get(self, tenant_id: str) -> Optional[Tenant]:
        """Retrieve a tenant by tenant_id."""
        db = self._get_db()
        if db:
            try:
                rows = db.execute_query(
                    """
                    SELECT tenant_id, name, plan_tier, status, created_at, updated_at
                    FROM tenants
                    WHERE tenant_id = %s;
                    """,
                    (tenant_id,),
                    tenant_id=tenant_id,
                )
                if rows:
                    r = rows[0]
                    return Tenant(
                        tenant_id=r["tenant_id"],
                        name=r["name"],
                        status=r.get("status") or "ACTIVE",
                        plan_tier=r.get("plan_tier") or "FREE",
                        created_at=str(r.get("created_at")),
                        updated_at=str(r.get("updated_at")),
                    )
            except Exception as e:
                logger.debug("DB get for tenant %s failed: %s", tenant_id, e)

        path = self._tenant_path(tenant_id)
        if not path.is_file():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Tenant.from_dict(data)
        except Exception as e:
            logger.error("Failed to load tenant %s: %s", tenant_id, e)
            return None

    def update(self, tenant: Tenant) -> Tenant:
        """Update an existing tenant record."""
        tenant.validate()
        from datetime import datetime, timezone
        tenant.updated_at = datetime.now(timezone.utc).isoformat()

        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    """
                    UPDATE tenants
                    SET name = %s, plan_tier = %s, status = %s, updated_at = %s
                    WHERE tenant_id = %s;
                    """,
                    (
                        tenant.name,
                        tenant.plan_tier or "FREE",
                        tenant.status or "ACTIVE",
                        tenant.updated_at,
                        tenant.tenant_id,
                    ),
                    tenant_id=tenant.tenant_id,
                )
            except Exception as e:
                logger.debug("DB update for tenant %s failed: %s", tenant.tenant_id, e)

        path = self._tenant_path(tenant.tenant_id)
        if path.is_file():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(tenant.to_dict(), f, indent=2)
        elif not db:
            raise ValueError(f"Cannot update non-existent tenant '{tenant.tenant_id}'")
        logger.debug("Updated tenant '%s'", tenant.tenant_id)
        return tenant

    def soft_delete(self, tenant_id: str) -> bool:
        """
        Soft-delete a tenant by setting status to 'DELETED'.
        Never deletes frozen analytical or public legislative datasets.
        """
        tenant = self.get(tenant_id)
        if not tenant:
            return False
        tenant.status = "DELETED"
        self.update(tenant)
        logger.warning("Soft-deleted tenant '%s'", tenant_id)
        return True

    def list(self, status: Optional[str] = None) -> list[Tenant]:
        """List tenants, optionally filtered by status."""
        db = self._get_db()
        if db:
            try:
                query = "SELECT tenant_id, name, plan_tier, status, created_at, updated_at FROM tenants"
                params: list[Any] = []
                if status:
                    query += " WHERE status = %s"
                    params.append(status)
                rows = db.execute_query(query, tuple(params))
                if rows:
                    res = [
                        Tenant(
                            tenant_id=r["tenant_id"],
                            name=r["name"],
                            status=r.get("status") or "ACTIVE",
                            plan_tier=r.get("plan_tier") or "FREE",
                            created_at=str(r.get("created_at")),
                            updated_at=str(r.get("updated_at")),
                        )
                        for r in rows
                    ]
                    return sorted(res, key=lambda t: t.created_at)
            except Exception as e:
                logger.debug("DB list tenants failed: %s", e)

        tenants: list[Tenant] = []
        for f in self._root_dir.glob("tenant_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                tenant = Tenant.from_dict(data)
                if status and tenant.status != status:
                    continue
                tenants.append(tenant)
            except Exception:
                pass
        return sorted(tenants, key=lambda t: t.created_at)
