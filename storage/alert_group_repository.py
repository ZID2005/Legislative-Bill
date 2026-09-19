"""
storage/alert_group_repository.py
=================================
Repository for AlertGroup persistence, aggregation indexing, and tenant isolation.

Storage layout:
  storage/alerts/groups/
    group_index.json
    {tenant_id}/{user_id}/
      group_{group_id}.json

Task 8.13.5 — Alert Aggregation & Digest Pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.alert_group import AlertGroup, AlertGroupStatus, AlertGroupType
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_groups_dir() -> Path:
    root = settings.ALERT_GROUPS_DIR
    ensure_dir(root)
    return root


class AlertGroupRepository:
    """
    Repository managing persistent AlertGroup records with deterministic aggregation indexing.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_groups_dir()
        ensure_dir(self._root_dir)
        self._index_file = self._root_dir / "group_index.json"
        self._group_index: dict[str, dict[str, Any]] = self._load_group_index()

    def _load_group_index(self) -> dict[str, dict[str, Any]]:
        """Load persistent aggregation key index from disk."""
        if not self._index_file.is_file():
            return {}
        try:
            with open(self._index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("Could not read group index: %s", e)
            return {}

    def _save_group_index(self) -> None:
        """Persist aggregation key index to disk."""
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(self._group_index, f, indent=2)
        except Exception as e:
            logger.error("Could not save group index: %s", e)

    def _user_groups_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._root_dir / tenant_id / user_id
        ensure_dir(path)
        return path

    def find_by_aggregation_key(
        self,
        aggregation_key: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[AlertGroup]:
        """
        Locate an existing AlertGroup by its deterministic aggregation_key.
        """
        meta = self._group_index.get(aggregation_key)
        if not meta:
            return None
        group_id = meta.get("group_id")
        t_id = meta.get("tenant_id")
        u_id = meta.get("user_id")

        if tenant_id and t_id != tenant_id:
            return None
        if user_id and u_id != user_id:
            return None

        if group_id and t_id and u_id:
            return self.get(group_id, tenant_id=t_id, user_id=u_id)
        return None

    def create(self, group: AlertGroup) -> AlertGroup:
        """
        Create and persist a new AlertGroup.
        Raises ValueError if group already exists.
        """
        group.validate()

        # Check existing aggregation key
        if group.aggregation_key and group.aggregation_key in self._group_index:
            raise ValueError(
                f"Duplicate alert group: aggregation_key '{group.aggregation_key}' already exists."
            )

        g_dir = self._user_groups_dir(group.tenant_id, group.user_id)
        path = g_dir / f"group_{group.group_id}.json"
        if path.is_file():
            raise ValueError(f"Alert group '{group.group_id}' already exists.")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(group.to_dict(), f, indent=2)

        # Index by aggregation key
        if group.aggregation_key:
            self._group_index[group.aggregation_key] = {
                "group_id": group.group_id,
                "tenant_id": group.tenant_id,
                "user_id": group.user_id,
                "created_at": group.created_at,
            }
            self._save_group_index()

        logger.debug("Created alert group %s (key: %s)", group.group_id, group.aggregation_key)
        return group

    def update(self, group: AlertGroup) -> AlertGroup:
        """
        Update an existing AlertGroup on disk.
        """
        group.validate()
        from datetime import datetime, timezone
        group.updated_at = datetime.now(timezone.utc).isoformat()

        g_dir = self._user_groups_dir(group.tenant_id, group.user_id)
        path = g_dir / f"group_{group.group_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(group.to_dict(), f, indent=2)

        # Ensure index has the key
        if group.aggregation_key:
            self._group_index[group.aggregation_key] = {
                "group_id": group.group_id,
                "tenant_id": group.tenant_id,
                "user_id": group.user_id,
                "created_at": group.created_at,
            }
            self._save_group_index()

        return group

    def save(self, group: AlertGroup) -> AlertGroup:
        """
        Idempotent save: creates if not existing, updates if existing.
        """
        existing = self.get(group.group_id, tenant_id=group.tenant_id, user_id=group.user_id)
        if not existing and group.aggregation_key:
            existing = self.find_by_aggregation_key(
                group.aggregation_key,
                tenant_id=group.tenant_id,
                user_id=group.user_id,
            )

        if existing:
            return self.update(group)
        return self.create(group)

    def get(
        self,
        group_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[AlertGroup]:
        """
        Retrieve an AlertGroup by ID, enforcing tenant/user scoping when supplied.
        """
        if tenant_id and user_id:
            path = self._user_groups_dir(tenant_id, user_id) / f"group_{group_id}.json"
            if not path.is_file():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return AlertGroup.from_dict(json.load(f))
            except Exception as e:
                logger.error("Failed to load alert group %s: %s", group_id, e)
                return None

        pattern = f"*/*/group_{group_id}.json" if not tenant_id else f"{tenant_id}/*/group_{group_id}.json"
        matches = list(self._root_dir.glob(pattern))
        for f in matches:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    grp = AlertGroup.from_dict(json.load(fh))
                if tenant_id and grp.tenant_id != tenant_id:
                    continue
                if user_id and grp.user_id != user_id:
                    continue
                return grp
            except Exception:
                pass
        return None

    def list_by_user(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        watchlist_id: Optional[str] = None,
        group_type: Optional[AlertGroupType] = None,
        status: Optional[AlertGroupStatus] = None,
        limit: int = 100,
    ) -> list[AlertGroup]:
        """
        List alert groups belonging to a user, sorted descending by latest_event_at.
        """
        g_dir = self._user_groups_dir(tenant_id, user_id)
        groups: list[AlertGroup] = []
        files = sorted(g_dir.glob("group_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        for f in files:
            if len(groups) >= limit:
                break
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    grp = AlertGroup.from_dict(json.load(fh))
                if watchlist_id is not None and grp.watchlist_id != watchlist_id:
                    continue
                if group_type is not None and grp.group_type != group_type:
                    continue
                if status is not None and grp.status != status:
                    continue
                groups.append(grp)
            except Exception:
                pass
        return groups

    def list_by_watchlist(
        self,
        watchlist_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[AlertGroup]:
        """
        List alert groups associated with a specific watchlist.
        """
        if tenant_id and user_id:
            g_dir = self._user_groups_dir(tenant_id, user_id)
            target_files = list(g_dir.glob("group_*.json"))
        elif tenant_id:
            target_files = list((self._root_dir / tenant_id).glob("*/group_*.json"))
        else:
            target_files = list(self._root_dir.glob("*/*/group_*.json"))

        groups: list[AlertGroup] = []
        for f in sorted(target_files, key=lambda f: f.stat().st_mtime, reverse=True):
            if len(groups) >= limit:
                break
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    grp = AlertGroup.from_dict(json.load(fh))
                if grp.watchlist_id == watchlist_id:
                    groups.append(grp)
            except Exception:
                pass
        return groups

    def list_by_period(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> list[AlertGroup]:
        """
        List alert groups active within a specified timestamp window.
        """
        user_groups = self.list_by_user(user_id=user_id, tenant_id=tenant_id, limit=limit * 2)
        filtered: list[AlertGroup] = []
        for g in user_groups:
            if start_time and g.latest_event_at < start_time:
                continue
            if end_time and g.first_event_at > end_time:
                continue
            filtered.append(g)
            if len(filtered) >= limit:
                break
        return filtered

    def archive(
        self,
        group_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Archive an alert group.
        """
        group = self.get(group_id, tenant_id=tenant_id, user_id=user_id)
        if not group:
            return False
        group.mark_as_archived()
        self.update(group)
        return True
