"""
storage/watchlist_repository.py
===============================
Repository for User Watchlists and WatchlistItems supporting multi-tenant isolation.

Storage layout:
  storage/watchlists/{tenant_id}/{user_id}/
    watchlists/
      wl_{watchlist_id}.json
    items/
      item_{item_id}.json

Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.watchlist import Watchlist, WatchlistItem, WatchlistEntityType
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_default_watchlists_dir() -> Path:
    root = settings.WATCHLIST_DIR
    ensure_dir(root)
    return root


class WatchlistRepository:
    """
    Repository for managing user watchlists and watched items with tenant isolation.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_watchlists_dir()
        ensure_dir(self._root_dir)

    def _user_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._root_dir / tenant_id / user_id
        ensure_dir(path)
        return path

    def _watchlists_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._user_dir(tenant_id, user_id) / "watchlists"
        ensure_dir(path)
        return path

    def _items_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._user_dir(tenant_id, user_id) / "items"
        ensure_dir(path)
        return path

    # ------------------------------------------------------------------
    # Watchlist Operations
    # ------------------------------------------------------------------

    def create(self, watchlist: Watchlist) -> Watchlist:
        """
        Create and persist a new Watchlist.
        """
        watchlist.validate()
        w_dir = self._watchlists_dir(watchlist.tenant_id, watchlist.user_id)
        path = w_dir / f"wl_{watchlist.watchlist_id}.json"
        if path.is_file():
            raise ValueError(
                f"Watchlist '{watchlist.watchlist_id}' already exists for user '{watchlist.user_id}'"
            )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(watchlist.to_dict(), f, indent=2)
        logger.debug("Created watchlist %s for user %s", watchlist.watchlist_id, watchlist.user_id)
        return watchlist

    def get(
        self,
        watchlist_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Watchlist]:
        """
        Retrieve a watchlist by ID, scoped by tenant and user when provided.
        If tenant_id or user_id are provided, cross-access is strictly blocked.
        """
        if tenant_id and user_id:
            path = self._watchlists_dir(tenant_id, user_id) / f"wl_{watchlist_id}.json"
            if not path.is_file():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return Watchlist.from_dict(json.load(f))
            except Exception as e:
                logger.error("Failed to load watchlist %s: %s", watchlist_id, e)
                return None

        # Search within tenant if tenant_id provided
        search_pattern = f"*/*/watchlists/wl_{watchlist_id}.json" if not tenant_id else f"{tenant_id}/*/watchlists/wl_{watchlist_id}.json"
        matches = list(self._root_dir.glob(search_pattern))
        if not matches:
            return None

        # Check tenant/user isolation match
        for f in matches:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    wl = Watchlist.from_dict(json.load(fh))
                if tenant_id and wl.tenant_id != tenant_id:
                    continue
                if user_id and wl.user_id != user_id:
                    continue
                return wl
            except Exception:
                pass
        return None

    def update(self, watchlist: Watchlist) -> Watchlist:
        """
        Update an existing Watchlist record. Bumps updated_at.
        """
        watchlist.validate()
        watchlist.updated_at = _utcnow_iso()
        path = self._watchlists_dir(watchlist.tenant_id, watchlist.user_id) / f"wl_{watchlist.watchlist_id}.json"
        if not path.is_file():
            raise ValueError(
                f"Cannot update non-existent watchlist '{watchlist.watchlist_id}'"
            )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(watchlist.to_dict(), f, indent=2)
        return watchlist

    def delete(
        self,
        watchlist_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        hard_delete: bool = False,
    ) -> bool:
        """
        Deactivate (soft delete) or remove (hard delete) a watchlist.
        """
        wl = self.get(watchlist_id, tenant_id=tenant_id, user_id=user_id)
        if not wl:
            return False

        path = self._watchlists_dir(wl.tenant_id, wl.user_id) / f"wl_{watchlist_id}.json"
        if hard_delete:
            if path.is_file():
                path.unlink()
                return True
            return False
        else:
            wl.is_active = False
            self.update(wl)
            return True

    def list_by_user(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        is_active: Optional[bool] = None,
    ) -> list[Watchlist]:
        """
        List all watchlists belonging to a user within a tenant.
        """
        w_dir = self._watchlists_dir(tenant_id, user_id)
        results: list[Watchlist] = []
        for f in w_dir.glob("wl_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    wl = Watchlist.from_dict(json.load(fh))
                if is_active is not None and wl.is_active != is_active:
                    continue
                results.append(wl)
            except Exception:
                pass
        return sorted(results, key=lambda w: w.created_at)

    # ------------------------------------------------------------------
    # WatchlistItem Operations
    # ------------------------------------------------------------------

    def add_item(self, item: WatchlistItem) -> WatchlistItem:
        """
        Add an item to a watchlist.
        Ensures:
        1. Parent watchlist exists and belongs to the same tenant/user.
        2. No duplicate active item with same (watchlist_id, entity_type, entity_id).
        """
        item.validate()
        parent_wl = self.get(item.watchlist_id, tenant_id=item.tenant_id, user_id=item.user_id)
        if not parent_wl:
            raise ValueError(
                f"Parent watchlist '{item.watchlist_id}' not found for user '{item.user_id}' in tenant '{item.tenant_id}'"
            )

        # Check for duplicate entity in this watchlist
        existing_items = self.list_items_by_watchlist(
            item.watchlist_id, tenant_id=item.tenant_id, user_id=item.user_id, is_active=True
        )
        for ex in existing_items:
            if ex.entity_type == item.entity_type and ex.entity_id == item.entity_id:
                raise ValueError(
                    f"Entity '{item.entity_id}' of type '{item.entity_type.value}' already exists in watchlist '{item.watchlist_id}'"
                )

        items_dir = self._items_dir(item.tenant_id, item.user_id)
        path = items_dir / f"item_{item.item_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(item.to_dict(), f, indent=2)

        logger.debug("Added item %s to watchlist %s", item.item_id, item.watchlist_id)
        return item

    def get_item(
        self,
        item_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[WatchlistItem]:
        """
        Retrieve an item by ID, scoped by tenant/user if provided.
        """
        if tenant_id and user_id:
            path = self._items_dir(tenant_id, user_id) / f"item_{item_id}.json"
            if not path.is_file():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return WatchlistItem.from_dict(json.load(f))
            except Exception as e:
                logger.error("Failed to load item %s: %s", item_id, e)
                return None

        # Search with pattern
        pattern = f"*/*/items/item_{item_id}.json" if not tenant_id else f"{tenant_id}/*/items/item_{item_id}.json"
        matches = list(self._root_dir.glob(pattern))
        for f in matches:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    item = WatchlistItem.from_dict(json.load(fh))
                if tenant_id and item.tenant_id != tenant_id:
                    continue
                if user_id and item.user_id != user_id:
                    continue
                return item
            except Exception:
                pass
        return None

    def remove_item(
        self,
        item_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        hard_delete: bool = False,
    ) -> bool:
        """
        Deactivate (soft delete) or remove (hard delete) an item.
        """
        item = self.get_item(item_id, tenant_id=tenant_id, user_id=user_id)
        if not item:
            return False

        path = self._items_dir(item.tenant_id, item.user_id) / f"item_{item_id}.json"
        if hard_delete:
            if path.is_file():
                path.unlink()
                return True
            return False
        else:
            item.is_active = False
            with open(path, "w", encoding="utf-8") as f:
                json.dump(item.to_dict(), f, indent=2)
            return True

    def list_items_by_watchlist(
        self,
        watchlist_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[WatchlistItem]:
        """
        List all items in a watchlist.
        """
        items: list[WatchlistItem] = []
        if tenant_id and user_id:
            items_dir = self._items_dir(tenant_id, user_id)
            target_files = list(items_dir.glob("item_*.json"))
        elif tenant_id:
            target_files = list((self._root_dir / tenant_id).glob("*/items/item_*.json"))
        else:
            target_files = list(self._root_dir.glob("*/*/items/item_*.json"))

        for f in target_files:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    item = WatchlistItem.from_dict(json.load(fh))
                if item.watchlist_id != watchlist_id:
                    continue
                if tenant_id and item.tenant_id != tenant_id:
                    continue
                if user_id and item.user_id != user_id:
                    continue
                if is_active is not None and item.is_active != is_active:
                    continue
                items.append(item)
            except Exception:
                pass
        return sorted(items, key=lambda i: i.created_at)

    def find_by_entity(
        self,
        entity_type: WatchlistEntityType | str,
        entity_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[WatchlistItem]:
        """
        Find watchlist items watching a specific entity.
        """
        etype = (
            entity_type.value
            if isinstance(entity_type, WatchlistEntityType)
            else str(entity_type).strip().upper()
        )
        eid = str(entity_id).strip()

        pattern = "*/*/items/item_*.json"
        if tenant_id and user_id:
            target_files = list(self._items_dir(tenant_id, user_id).glob("item_*.json"))
        elif tenant_id:
            target_files = list((self._root_dir / tenant_id).glob("*/items/item_*.json"))
        else:
            target_files = list(self._root_dir.glob(pattern))

        matches: list[WatchlistItem] = []
        for f in target_files:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    item = WatchlistItem.from_dict(json.load(fh))
                if not item.is_active:
                    continue
                if item.entity_type.value != etype:
                    continue
                if item.entity_id.lower() != eid.lower():
                    continue
                if tenant_id and item.tenant_id != tenant_id:
                    continue
                if user_id and item.user_id != user_id:
                    continue
                matches.append(item)
            except Exception:
                pass
        return matches
