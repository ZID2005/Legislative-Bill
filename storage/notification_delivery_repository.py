"""
storage/notification_delivery_repository.py
============================================
Repository for NotificationDeliveryRecord tracking outbound delivery attempts,
supporting multi-tenant isolation, idempotency lookup, and audit logs.

Storage layout:
  storage/alerts/deliveries/
    delivery_index.json
    {tenant_id}/{user_id}/
      delivery_{delivery_id}.json

Task 8.13.7 — Outbound Notification Delivery Providers & Webhook Dispatch.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.alert import NotificationChannel, NotificationStatus
from schemas.notification_delivery import NotificationDeliveryRecord
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_deliveries_dir() -> Path:
    root = settings.ALERT_DELIVERIES_DIR
    ensure_dir(root)
    return root


class NotificationDeliveryRepository:
    """
    Repository for persisting and querying notification delivery attempt records.
    Enforces multi-tenant isolation and deterministic idempotency checking.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_deliveries_dir()
        ensure_dir(self._root_dir)
        self._index_file = self._root_dir / "delivery_index.json"
        self._delivery_index: dict[str, dict[str, Any]] = self._load_index()

    def _load_index(self) -> dict[str, dict[str, Any]]:
        """Load persistent delivery index from disk."""
        if not self._index_file.is_file():
            return {}
        try:
            with open(self._index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.warning("Could not read delivery index: %s", e)
            return {}

    def _save_index(self) -> None:
        """Persist delivery index to disk."""
        try:
            with open(self._index_file, "w", encoding="utf-8") as f:
                json.dump(self._delivery_index, f, indent=2)
        except Exception as e:
            logger.error("Could not save delivery index: %s", e)

    def _user_deliveries_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._root_dir / tenant_id / user_id
        ensure_dir(path)
        return path

    def create(self, record: NotificationDeliveryRecord) -> NotificationDeliveryRecord:
        """
        Persist a delivery attempt record and update index.
        """
        d_dir = self._user_deliveries_dir(record.tenant_id, record.user_id)
        path = d_dir / f"delivery_{record.delivery_id}.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2)

        if record.delivery_key:
            self._delivery_index[record.delivery_key] = {
                "delivery_id": record.delivery_id,
                "tenant_id": record.tenant_id,
                "user_id": record.user_id,
                "notification_id": record.notification_id,
                "channel": (
                    record.channel.value
                    if isinstance(record.channel, NotificationChannel)
                    else str(record.channel)
                ),
                "status": (
                    record.status.value
                    if isinstance(record.status, NotificationStatus)
                    else str(record.status)
                ),
                "timestamp": record.timestamp,
            }
            self._save_index()

        logger.debug(
            "Recorded delivery %s for notification %s via %s (status: %s)",
            record.delivery_id,
            record.notification_id,
            record.channel,
            record.status,
        )
        return record

    def get(
        self,
        delivery_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[NotificationDeliveryRecord]:
        """
        Retrieve a delivery record by ID, optionally enforcing tenant/user scoping.
        """
        if tenant_id and user_id:
            path = self._user_deliveries_dir(tenant_id, user_id) / f"delivery_{delivery_id}.json"
            if not path.is_file():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return NotificationDeliveryRecord.from_dict(json.load(f))
            except Exception as e:
                logger.error("Failed to load delivery record %s: %s", delivery_id, e)
                return None

        pattern = f"*/*/delivery_{delivery_id}.json" if not tenant_id else f"{tenant_id}/*/delivery_{delivery_id}.json"
        matches = list(self._root_dir.glob(pattern))
        for f in matches:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    rec = NotificationDeliveryRecord.from_dict(json.load(fh))
                if tenant_id and rec.tenant_id != tenant_id:
                    continue
                if user_id and rec.user_id != user_id:
                    continue
                return rec
            except Exception:
                pass
        return None

    def find_by_delivery_key(
        self,
        delivery_key: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[NotificationDeliveryRecord]:
        """
        Locate the most recent delivery record matching a deterministic delivery key.
        """
        if not delivery_key:
            return None
        meta = self._delivery_index.get(delivery_key)
        if not meta:
            return None

        t_id = meta.get("tenant_id")
        u_id = meta.get("user_id")
        d_id = meta.get("delivery_id")

        if tenant_id and t_id != tenant_id:
            return None
        if user_id and u_id != user_id:
            return None

        if d_id and t_id and u_id:
            return self.get(d_id, tenant_id=t_id, user_id=u_id)
        return None

    def has_successful_delivery(
        self,
        delivery_key: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Check if a notification has already been successfully delivered on the given key.
        """
        rec = self.find_by_delivery_key(delivery_key, tenant_id=tenant_id, user_id=user_id)
        if rec and rec.status == NotificationStatus.DELIVERED:
            return True
        return False

    def list_by_notification(
        self,
        notification_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> list[NotificationDeliveryRecord]:
        """
        List all delivery attempt records for a specific notification.
        """
        u_dir = self._user_deliveries_dir(tenant_id, user_id)
        if not u_dir.is_dir():
            return []

        results: list[NotificationDeliveryRecord] = []
        for f in u_dir.glob("delivery_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    rec = NotificationDeliveryRecord.from_dict(json.load(fh))
                if rec.tenant_id == tenant_id and rec.user_id == user_id and rec.notification_id == notification_id:
                    results.append(rec)
            except Exception:
                pass

        results.sort(key=lambda r: (r.timestamp or "", r.attempt_number), reverse=True)
        return results

    def list_by_user(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        channel: Optional[NotificationChannel] = None,
        limit: int = 50,
    ) -> list[NotificationDeliveryRecord]:
        """
        List delivery records for a user with optional channel filter.
        """
        u_dir = self._user_deliveries_dir(tenant_id, user_id)
        if not u_dir.is_dir():
            return []

        results: list[NotificationDeliveryRecord] = []
        for f in u_dir.glob("delivery_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    rec = NotificationDeliveryRecord.from_dict(json.load(fh))
                if rec.tenant_id != tenant_id or rec.user_id != user_id:
                    continue
                if channel is not None and rec.channel != channel:
                    continue
                results.append(rec)
            except Exception:
                pass

        results.sort(key=lambda r: (r.timestamp or "", r.attempt_number), reverse=True)
        return results[:limit]
