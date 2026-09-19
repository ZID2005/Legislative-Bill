"""
storage/notification_repository.py
==================================
Repository for Notification delivery records supporting tenant isolation,
deduplication indexing, lifecycle state management, and multi-criteria queries.

Storage layout:
  storage/alerts/notifications/
    notif_index.json
    {tenant_id}/{user_id}/
      notif_{notification_id}.json

Task 8.13.2 & Task 8.13.6 — Notification Dispatch & In-App Notification Center.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.alert import (
    AlertSeverity,
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_notifications_dir() -> Path:
    root = settings.ALERTS_DIR / "notifications"
    ensure_dir(root)
    return root


class NotificationRepository:
    """
    Repository for managing alert notification delivery state records and in-app inbox.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_notifications_dir()
        ensure_dir(self._root_dir)
        self._dedup_file = self._root_dir / "notif_index.json"
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
            logger.warning("Could not read notification dedup index: %s", e)
            return {}

    def _save_dedup_index(self) -> None:
        """Persist dedup index to disk."""
        try:
            with open(self._dedup_file, "w", encoding="utf-8") as f:
                json.dump(self._dedup_index, f, indent=2)
        except Exception as e:
            logger.error("Could not save notification dedup index: %s", e)

    def _user_notifs_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._root_dir / tenant_id / user_id
        ensure_dir(path)
        return path

    def find_by_dedup_key(
        self,
        dedup_key: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Locate an existing Notification by its deterministic dedup_key.
        """
        if not dedup_key:
            return None
        meta = self._dedup_index.get(dedup_key)
        if not meta:
            return None
        notif_id = meta.get("notification_id")
        t_id = meta.get("tenant_id")
        u_id = meta.get("user_id")

        if tenant_id and t_id != tenant_id:
            return None
        if user_id and u_id != user_id:
            return None

        if notif_id and t_id and u_id:
            return self.get(notif_id, tenant_id=t_id, user_id=u_id)
        return None

    def create(self, notification: Notification) -> Notification:
        """
        Create and persist a new Notification record.
        Raises ValueError if notification_id already exists.
        """
        notification.validate()
        n_dir = self._user_notifs_dir(notification.tenant_id, notification.user_id)
        path = n_dir / f"notif_{notification.notification_id}.json"
        if path.is_file():
            raise ValueError(
                f"Notification '{notification.notification_id}' already exists."
            )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(notification.to_dict(), f, indent=2)

        if notification.dedup_key:
            self._dedup_index[notification.dedup_key] = {
                "notification_id": notification.notification_id,
                "tenant_id": notification.tenant_id,
                "user_id": notification.user_id,
            }
            self._save_dedup_index()

        logger.debug(
            "Created notification %s for user %s",
            notification.notification_id,
            notification.user_id,
        )
        return notification

    def save(self, notification: Notification) -> Notification:
        """
        Persist or update an existing Notification record.
        """
        notification.validate()
        n_dir = self._user_notifs_dir(notification.tenant_id, notification.user_id)
        path = n_dir / f"notif_{notification.notification_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(notification.to_dict(), f, indent=2)

        if notification.dedup_key:
            self._dedup_index[notification.dedup_key] = {
                "notification_id": notification.notification_id,
                "tenant_id": notification.tenant_id,
                "user_id": notification.user_id,
            }
            self._save_dedup_index()
        return notification

    def update(self, notification: Notification) -> Notification:
        """Alias for save."""
        return self.save(notification)

    def get(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Retrieve a Notification by ID, enforcing tenant/user scoping when supplied.
        """
        if tenant_id and user_id:
            path = self._user_notifs_dir(tenant_id, user_id) / f"notif_{notification_id}.json"
            if not path.is_file():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return Notification.from_dict(json.load(f))
            except Exception as e:
                logger.error("Failed to load notification %s: %s", notification_id, e)
                return None

        pattern = f"*/*/notif_{notification_id}.json" if not tenant_id else f"{tenant_id}/*/notif_{notification_id}.json"
        matches = list(self._root_dir.glob(pattern))
        for f in matches:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    notif = Notification.from_dict(json.load(fh))
                if tenant_id and notif.tenant_id != tenant_id:
                    continue
                if user_id and notif.user_id != user_id:
                    continue
                return notif
            except Exception:
                pass
        return None

    def list_by_user(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        limit: int = 100,
        offset: int = 0,
        is_read: Optional[bool] = None,
        is_archived: Optional[bool] = None,
        is_deleted: bool = False,
        notification_type: Optional[str | NotificationType] = None,
        severity: Optional[str | AlertSeverity] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        bill_id: Optional[str] = None,
        company_id: Optional[str] = None,
        state: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> list[Notification]:
        """
        List notifications for a specific tenant/user with deterministic sorting
        (created_at descending, notification_id descending) and multi-criteria filtering.
        """
        n_dir = self._user_notifs_dir(tenant_id, user_id)
        if not n_dir.is_dir():
            return []

        all_notifs: list[Notification] = []
        files = list(n_dir.glob("notif_*.json"))
        for f in files:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    notif = Notification.from_dict(json.load(fh))
                # Strict tenant and user isolation verification
                if notif.tenant_id != tenant_id or notif.user_id != user_id:
                    continue
                all_notifs.append(notif)
            except Exception:
                pass

        # Deterministic ordering: created_at descending, notification_id descending
        all_notifs.sort(
            key=lambda n: (n.created_at or "", n.notification_id or ""),
            reverse=True,
        )

        filtered: list[Notification] = []
        for n in all_notifs:
            # Soft delete filter
            if not is_deleted and n.is_deleted:
                continue
            if is_deleted and not n.is_deleted:
                continue

            # Suppressed notifications are delivery failures/filtered out of center
            if n.status == NotificationStatus.SUPPRESSED:
                continue

            # Read filter
            if is_read is not None:
                if is_read and not n.is_read:
                    continue
                if not is_read and n.is_read:
                    continue

            # Archived filter
            if is_archived is not None:
                if is_archived and not n.is_archived:
                    continue
                if not is_archived and n.is_archived:
                    continue

            # Notification type filter
            if notification_type is not None:
                target_type = (
                    notification_type.value
                    if isinstance(notification_type, NotificationType)
                    else str(notification_type).strip().upper()
                )
                curr_type = (
                    n.notification_type.value
                    if isinstance(n.notification_type, NotificationType)
                    else str(n.notification_type).strip().upper()
                )
                if curr_type != target_type:
                    continue

            # Severity filter
            if severity is not None:
                target_sev = (
                    severity.value
                    if isinstance(severity, AlertSeverity)
                    else str(severity).strip().upper()
                )
                curr_sev = (
                    n.severity.value
                    if isinstance(n.severity, AlertSeverity)
                    else (str(n.severity).strip().upper() if n.severity else "")
                )
                if curr_sev != target_sev:
                    continue

            # Date range filter
            if start_time and (not n.created_at or n.created_at < start_time):
                continue
            if end_time and (not n.created_at or n.created_at > end_time):
                continue

            # Entity type filter
            if entity_type:
                target_et = entity_type.strip().upper()
                curr_et = (n.entity_type or "").strip().upper()
                if curr_et != target_et:
                    continue

            # Entity ID filter
            if entity_id:
                target_ei = entity_id.strip().lower()
                curr_ei = (n.entity_id or "").strip().lower()
                if curr_ei != target_ei:
                    continue

            # Specific Bill ID filter
            if bill_id:
                b_target = bill_id.strip().lower()
                curr_bid = (
                    (n.entity_id or "") if (n.entity_type or "").upper() == "BILL"
                    else str(n.metadata.get("bill_id", ""))
                ).strip().lower()
                if curr_bid != b_target:
                    continue

            # Specific Company ID filter
            if company_id:
                c_target = company_id.strip().upper()
                curr_cid = (
                    (n.entity_id or "") if (n.entity_type or "").upper() == "COMPANY"
                    else str(n.metadata.get("company_id", ""))
                ).strip().upper()
                if curr_cid != c_target:
                    continue

            # State filter
            if state:
                s_target = state.strip().lower()
                curr_state = (n.state or str(n.metadata.get("state", ""))).strip().lower()
                if curr_state != s_target:
                    continue

            # Jurisdiction filter
            if jurisdiction:
                j_target = jurisdiction.strip().lower()
                curr_jur = (n.jurisdiction or str(n.metadata.get("jurisdiction", ""))).strip().lower()
                if curr_jur != j_target:
                    continue

            # Source type filter
            if source_type:
                st_target = source_type.strip().upper()
                curr_st = (n.source_type or "").strip().upper()
                if curr_st != st_target:
                    continue

            # Source ID filter
            if source_id:
                si_target = source_id.strip()
                curr_si = (n.source_id or n.alert_event_id or n.alert_group_id or n.digest_id or "").strip()
                if curr_si != si_target:
                    continue

            filtered.append(n)

        # Pagination
        start = max(0, offset)
        end = start + limit if limit > 0 else len(filtered)
        return filtered[start:end]

    def count_unread(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        include_archived: bool = False,
    ) -> int:
        """
        Deterministic unread count calculation strictly for the requesting tenant and user.
        Excludes deleted, suppressed, and (by default) archived notifications.
        """
        n_dir = self._user_notifs_dir(tenant_id, user_id)
        if not n_dir.is_dir():
            return 0

        count = 0
        for f in n_dir.glob("notif_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    notif = Notification.from_dict(json.load(fh))
                if notif.tenant_id != tenant_id or notif.user_id != user_id:
                    continue
                if notif.is_deleted:
                    continue
                if notif.status == NotificationStatus.SUPPRESSED:
                    continue
                if not include_archived and notif.is_archived:
                    continue
                if not notif.is_read and notif.status != NotificationStatus.READ:
                    count += 1
            except Exception:
                pass
        return count

    def mark_delivered(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Mark notification as DELIVERED.
        """
        notif = self.get(notification_id, tenant_id=tenant_id, user_id=user_id)
        if not notif:
            return False
        notif.mark_delivered()
        self.save(notif)
        return True

    def mark_read(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Mark notification as READ.
        """
        notif = self.get(notification_id, tenant_id=tenant_id, user_id=user_id)
        if not notif:
            return False
        notif.mark_read()
        self.save(notif)
        return True

    def mark_unread(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Mark notification as UNREAD (DELIVERED, is_read=False).
        """
        notif = self.get(notification_id, tenant_id=tenant_id, user_id=user_id)
        if not notif:
            return False
        notif.mark_unread()
        self.save(notif)
        return True

    def mark_all_read(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
    ) -> int:
        """
        Mark all eligible active notifications for user and tenant as READ.
        Does not affect deleted or archived records.
        """
        n_dir = self._user_notifs_dir(tenant_id, user_id)
        if not n_dir.is_dir():
            return 0

        updated_count = 0
        for f in n_dir.glob("notif_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    notif = Notification.from_dict(json.load(fh))
                if notif.tenant_id != tenant_id or notif.user_id != user_id:
                    continue
                if notif.is_deleted or notif.is_archived:
                    continue
                if notif.status == NotificationStatus.SUPPRESSED:
                    continue
                if not notif.is_read:
                    notif.mark_read()
                    self.save(notif)
                    updated_count += 1
            except Exception:
                pass
        return updated_count

    def archive(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Mark notification as ARCHIVED.
        """
        notif = self.get(notification_id, tenant_id=tenant_id, user_id=user_id)
        if not notif:
            return False
        notif.archive()
        self.save(notif)
        return True

    def unarchive(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Unarchive notification.
        """
        notif = self.get(notification_id, tenant_id=tenant_id, user_id=user_id)
        if not notif:
            return False
        notif.unarchive()
        self.save(notif)
        return True

    def archive_multiple(
        self,
        notification_ids: list[str],
        user_id: str,
        tenant_id: str = "default_tenant",
    ) -> int:
        """
        Archive multiple notifications belonging to the specified user and tenant.
        """
        archived_count = 0
        for nid in notification_ids:
            if self.archive(nid, tenant_id=tenant_id, user_id=user_id):
                archived_count += 1
        return archived_count

    def delete(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        soft: bool = True,
    ) -> bool:
        """
        Delete a notification.
        Soft delete preserves record with is_deleted=True.
        Hard delete unlinks file and cleans index.
        """
        notif = self.get(notification_id, tenant_id=tenant_id, user_id=user_id)
        if not notif:
            return False

        if soft:
            notif.soft_delete()
            self.save(notif)
            return True

        # Hard delete
        path = self._user_notifs_dir(notif.tenant_id, notif.user_id) / f"notif_{notification_id}.json"
        if path.is_file():
            path.unlink()
        if notif.dedup_key in self._dedup_index:
            del self._dedup_index[notif.dedup_key]
            self._save_dedup_index()
        return True

    def delete_multiple(
        self,
        notification_ids: list[str],
        user_id: str,
        tenant_id: str = "default_tenant",
        soft: bool = True,
    ) -> int:
        """
        Delete multiple notifications belonging to the specified user and tenant.
        """
        deleted_count = 0
        for nid in notification_ids:
            if self.delete(nid, tenant_id=tenant_id, user_id=user_id, soft=soft):
                deleted_count += 1
        return deleted_count
