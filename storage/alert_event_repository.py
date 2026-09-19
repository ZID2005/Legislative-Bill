"""
storage/alert_event_repository.py
=================================
Repository for AlertEvent persistence, read/archived tracking, and deduplication.

Storage layout:
  storage/alerts/events/
    dedup_index.json
    {tenant_id}/{user_id}/
      event_{alert_event_id}.json

Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.alert import AlertEvent
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_events_dir() -> Path:
    root = settings.ALERTS_DIR / "events"
    ensure_dir(root)
    return root


class AlertEventRepository:
    """
    Repository managing user inbox AlertEvent records with deterministic deduplication.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_events_dir()
        ensure_dir(self._root_dir)
        self._dedup_file = self._root_dir / "dedup_index.json"
        self._dedup_index: dict[str, dict[str, Any]] = self._load_dedup_index()

    def _load_dedup_index(self) -> dict[str, dict[str, Any]]:
        """Load persistent dedup index from disk."""
        if not self._dedup_file.is_file():
            return {}
        try:
            with open(self._dedup_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("Could not read dedup index: %s", e)
            return {}

    def _save_dedup_index(self) -> None:
        """Persist dedup index to disk."""
        try:
            with open(self._dedup_file, "w", encoding="utf-8") as f:
                json.dump(self._dedup_index, f, indent=2)
        except Exception as e:
            logger.error("Could not save dedup index: %s", e)

    def _user_events_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._root_dir / tenant_id / user_id
        ensure_dir(path)
        return path

    def is_duplicate(self, dedup_key: str) -> bool:
        """Check if an alert event with the given dedup_key already exists."""
        return dedup_key in self._dedup_index

    def find_by_dedup_key(
        self,
        dedup_key: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[AlertEvent]:
        """
        Locate an existing AlertEvent by its dedup_key.
        """
        meta = self._dedup_index.get(dedup_key)
        if not meta:
            return None
        event_id = meta.get("alert_event_id")
        t_id = meta.get("tenant_id")
        u_id = meta.get("user_id")

        if tenant_id and t_id != tenant_id:
            return None
        if user_id and u_id != user_id:
            return None

        if event_id and t_id and u_id:
            return self.get(event_id, tenant_id=t_id, user_id=u_id)
        return None

    def create(self, event: AlertEvent) -> AlertEvent:
        """
        Create and persist a new AlertEvent.
        Raises ValueError if dedup_key already exists.
        """
        event.validate()

        # Check deduplication
        if event.dedup_key in self._dedup_index:
            raise ValueError(
                f"Duplicate alert event: dedup_key '{event.dedup_key}' already exists."
            )

        e_dir = self._user_events_dir(event.tenant_id, event.user_id)
        path = e_dir / f"event_{event.alert_event_id}.json"
        if path.is_file():
            raise ValueError(
                f"Alert event '{event.alert_event_id}' already exists."
            )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(event.to_dict(), f, indent=2)

        # Record into dedup index
        self._dedup_index[event.dedup_key] = {
            "alert_event_id": event.alert_event_id,
            "tenant_id": event.tenant_id,
            "user_id": event.user_id,
            "created_at": event.created_at,
        }
        self._save_dedup_index()

        logger.debug("Created alert event %s (dedup: %s)", event.alert_event_id, event.dedup_key)
        return event

    def get(
        self,
        alert_event_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[AlertEvent]:
        """
        Retrieve an AlertEvent by ID, enforcing tenant/user scoping when supplied.
        """
        if tenant_id and user_id:
            path = self._user_events_dir(tenant_id, user_id) / f"event_{alert_event_id}.json"
            if not path.is_file():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return AlertEvent.from_dict(json.load(f))
            except Exception as e:
                logger.error("Failed to load alert event %s: %s", alert_event_id, e)
                return None

        pattern = f"*/*/event_{alert_event_id}.json" if not tenant_id else f"{tenant_id}/*/event_{alert_event_id}.json"
        matches = list(self._root_dir.glob(pattern))
        for f in matches:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    ev = AlertEvent.from_dict(json.load(fh))
                if tenant_id and ev.tenant_id != tenant_id:
                    continue
                if user_id and ev.user_id != user_id:
                    continue
                return ev
            except Exception:
                pass
        return None

    def list_by_user(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        limit: int = 100,
    ) -> list[AlertEvent]:
        """
        List alerts belonging to a user, sorted descending by created_at.
        """
        e_dir = self._user_events_dir(tenant_id, user_id)
        events: list[AlertEvent] = []
        files = sorted(e_dir.glob("event_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        for f in files:
            if len(events) >= limit:
                break
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    events.append(AlertEvent.from_dict(json.load(fh)))
            except Exception:
                pass
        return events

    def list_by_watchlist(
        self,
        watchlist_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[AlertEvent]:
        """
        List alerts associated with a specific watchlist.
        """
        if tenant_id and user_id:
            e_dir = self._user_events_dir(tenant_id, user_id)
            target_files = list(e_dir.glob("event_*.json"))
        elif tenant_id:
            target_files = list((self._root_dir / tenant_id).glob("*/event_*.json"))
        else:
            target_files = list(self._root_dir.glob("*/*/event_*.json"))

        events: list[AlertEvent] = []
        for f in sorted(target_files, key=lambda f: f.stat().st_mtime, reverse=True):
            if len(events) >= limit:
                break
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    ev = AlertEvent.from_dict(json.load(fh))
                if ev.watchlist_id == watchlist_id:
                    events.append(ev)
            except Exception:
                pass
        return events

    def list_unread(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        limit: int = 100,
    ) -> list[AlertEvent]:
        """
        List unread alert events for a user.
        """
        all_events = self.list_by_user(user_id=user_id, tenant_id=tenant_id, limit=limit * 2)
        return [e for e in all_events if not e.is_read][:limit]

    def mark_read(
        self,
        alert_event_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Mark an alert event as read.
        """
        event = self.get(alert_event_id, tenant_id=tenant_id, user_id=user_id)
        if not event:
            return False
        event.mark_as_read()
        path = self._user_events_dir(event.tenant_id, event.user_id) / f"event_{alert_event_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(event.to_dict(), f, indent=2)
        return True

    def archive(
        self,
        alert_event_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Archive an alert event.
        """
        event = self.get(alert_event_id, tenant_id=tenant_id, user_id=user_id)
        if not event:
            return False
        event.mark_as_archived()
        path = self._user_events_dir(event.tenant_id, event.user_id) / f"event_{alert_event_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(event.to_dict(), f, indent=2)
        return True
