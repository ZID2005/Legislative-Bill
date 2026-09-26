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
    Repository managing Tenant entities with JSON persistence.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_tenants_dir()
        ensure_dir(self._root_dir)

    def _tenant_path(self, tenant_id: str) -> Path:
        return self._root_dir / f"tenant_{tenant_id}.json"

    def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant record. Raises ValueError if tenant already exists."""
        tenant.validate()
        path = self._tenant_path(tenant.tenant_id)
        if path.is_file():
            raise ValueError(f"Tenant '{tenant.tenant_id}' already exists")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(tenant.to_dict(), f, indent=2)
        logger.info("Created tenant '%s' (owner: %s)", tenant.tenant_id, tenant.owner_user_id)
        return tenant

    def get(self, tenant_id: str) -> Optional[Tenant]:
        """Retrieve a tenant by tenant_id."""
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
        path = self._tenant_path(tenant.tenant_id)
        if not path.is_file():
            raise ValueError(f"Cannot update non-existent tenant '{tenant.tenant_id}'")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(tenant.to_dict(), f, indent=2)
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
