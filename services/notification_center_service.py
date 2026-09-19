"""
services/notification_center_service.py
=======================================
In-App Notification Center Service API layer.

Provides an API-ready contract for future SaaS frontend consumption:
- List notifications with pagination and multi-parameter filtering.
- Retrieve notification detail.
- Read/unread toggle and mark-all-read.
- Archive, unarchive, and bulk archive.
- Soft-deletion with source evidence preservation.
- Deterministic ordering (created_at desc, notification_id desc).
- Notification center summary metrics.

Task 8.13.6 — Notification Dispatch & In-App Notification Center API.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.alert import (
    AlertSeverity,
    Notification,
    NotificationStatus,
    NotificationType,
)
from services.notification_service import NotificationService
from storage.notification_repository import NotificationRepository

logger = get_logger(__name__)


@dataclass
class NotificationCenterSummary:
    """
    Consolidated metrics and counts for the in-app notification center.
    """

    tenant_id: str
    user_id: str
    total_active: int = 0
    unread_count: int = 0
    archived_count: int = 0
    alert_count: int = 0
    digest_count: int = 0
    latest_notification_at: Optional[str] = None
    counts_by_type: dict[str, int] = field(default_factory=dict)
    counts_by_severity: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize summary to API-ready dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "total_active": self.total_active,
            "unread_count": self.unread_count,
            "archived_count": self.archived_count,
            "alert_count": self.alert_count,
            "digest_count": self.digest_count,
            "latest_notification_at": self.latest_notification_at,
            "counts_by_type": dict(self.counts_by_type),
            "counts_by_severity": dict(self.counts_by_severity),
        }


class NotificationCenterService:
    """
    In-App Notification Center API layer handling client requests and operations.
    """

    def __init__(
        self,
        notification_service: Optional[NotificationService] = None,
        notification_repo: Optional[NotificationRepository] = None,
    ) -> None:
        self.notification_service = notification_service or NotificationService(
            notification_repo=notification_repo
        )
        self.repo = self.notification_service.repo

    # -----------------------------------------------------------------------
    # API Contract Endpoints (GET /notifications)
    # -----------------------------------------------------------------------

    def list_notifications(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        limit: int = 50,
        offset: int = 0,
        is_read: Optional[bool] = None,
        is_archived: Optional[bool] = False,
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
        API handler for GET /notifications.

        By default returns active notifications (is_archived=False, is_deleted=False).
        Supports deterministic pagination (limit, offset) and filtering.
        """
        return self.notification_service.list_notifications(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=limit,
            offset=offset,
            is_read=is_read,
            is_archived=is_archived,
            is_deleted=is_deleted,
            notification_type=notification_type,
            severity=severity,
            start_time=start_time,
            end_time=end_time,
            entity_type=entity_type,
            entity_id=entity_id,
            bill_id=bill_id,
            company_id=company_id,
            state=state,
            jurisdiction=jurisdiction,
            source_type=source_type,
            source_id=source_id,
        )

    def get_notification(
        self,
        notification_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> Optional[Notification]:
        """
        API handler for GET /notifications/{notification_id}.
        Enforces tenant and user isolation.
        """
        return self.notification_service.get_notification(
            notification_id=notification_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

    def get_unread_notifications(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        limit: int = 50,
    ) -> list[Notification]:
        """
        API handler for GET /notifications/unread.
        """
        return self.notification_service.get_unread_notifications(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=limit,
        )

    def get_unread_count(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        include_archived: bool = False,
    ) -> int:
        """
        API handler for GET /notifications/unread-count.
        """
        return self.notification_service.get_unread_count(
            user_id=user_id,
            tenant_id=tenant_id,
            include_archived=include_archived,
        )

    def get_recent_notifications(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        limit: int = 10,
    ) -> list[Notification]:
        """
        API handler for GET /notifications/recent.
        Returns up to `limit` active notifications in deterministic reverse-chronological order.
        """
        safe_limit = max(1, min(limit, 100))
        return self.list_notifications(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=safe_limit,
            offset=0,
            is_archived=False,
            is_deleted=False,
        )

    # -----------------------------------------------------------------------
    # State Management Endpoints (POST /notifications/...)
    # -----------------------------------------------------------------------

    def mark_read(
        self,
        notification_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> bool:
        """
        API handler for POST /notifications/{notification_id}/read.
        """
        return self.notification_service.mark_as_read(
            notification_id=notification_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

    def mark_unread(
        self,
        notification_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> bool:
        """
        API handler for POST /notifications/{notification_id}/unread.
        """
        return self.notification_service.mark_as_unread(
            notification_id=notification_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

    def mark_all_read(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
    ) -> int:
        """
        API handler for POST /notifications/read-all.
        Marks all active unread notifications for tenant/user as read.
        """
        return self.repo.mark_all_read(user_id=user_id, tenant_id=tenant_id)

    def archive(
        self,
        notification_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> bool:
        """
        API handler for POST /notifications/{notification_id}/archive.
        """
        return self.notification_service.archive_notification(
            notification_id=notification_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

    def unarchive(
        self,
        notification_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> bool:
        """
        API handler for POST /notifications/{notification_id}/unarchive.
        """
        return self.notification_service.unarchive_notification(
            notification_id=notification_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

    def archive_multiple(
        self,
        notification_ids: list[str],
        user_id: str,
        tenant_id: str = "default_tenant",
    ) -> int:
        """
        API handler for POST /notifications/archive-multiple.
        """
        return self.repo.archive_multiple(
            notification_ids=notification_ids,
            user_id=user_id,
            tenant_id=tenant_id,
        )

    def delete(
        self,
        notification_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
        soft: bool = True,
    ) -> bool:
        """
        API handler for DELETE /notifications/{notification_id}.
        Default soft delete preserves underlying evidence.
        """
        return self.notification_service.delete_notification(
            notification_id=notification_id,
            tenant_id=tenant_id,
            user_id=user_id,
            soft=soft,
        )

    def delete_multiple(
        self,
        notification_ids: list[str],
        user_id: str,
        tenant_id: str = "default_tenant",
        soft: bool = True,
    ) -> int:
        """
        API handler for bulk deletion.
        """
        return self.repo.delete_multiple(
            notification_ids=notification_ids,
            user_id=user_id,
            tenant_id=tenant_id,
            soft=soft,
        )

    # -----------------------------------------------------------------------
    # Summary Metrics (GET /notifications/summary)
    # -----------------------------------------------------------------------

    def get_notification_center_summary(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
    ) -> NotificationCenterSummary:
        """
        API handler for GET /notifications/summary.

        Returns high-level counts and breakdown by type and severity
        for the authenticated user and tenant.
        """
        # Load active notifications (non-deleted, non-archived)
        active = self.repo.list_by_user(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=10000,
            is_archived=False,
            is_deleted=False,
        )
        # Load archived notifications (non-deleted)
        archived = self.repo.list_by_user(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=10000,
            is_archived=True,
            is_deleted=False,
        )

        unread_count = sum(1 for n in active if not n.is_read and n.status != NotificationStatus.READ)
        latest_ts: Optional[str] = active[0].created_at if active else None

        counts_by_type: dict[str, int] = {}
        counts_by_severity: dict[str, int] = {}
        alert_count = 0
        digest_count = 0

        for n in active:
            nt = (
                n.notification_type.value
                if isinstance(n.notification_type, NotificationType)
                else str(n.notification_type)
            )
            counts_by_type[nt] = counts_by_type.get(nt, 0) + 1

            if nt == NotificationType.DIGEST.value:
                digest_count += 1
            else:
                alert_count += 1

            if n.severity:
                sev = (
                    n.severity.value
                    if isinstance(n.severity, AlertSeverity)
                    else str(n.severity)
                )
                counts_by_severity[sev] = counts_by_severity.get(sev, 0) + 1

        return NotificationCenterSummary(
            tenant_id=tenant_id,
            user_id=user_id,
            total_active=len(active),
            unread_count=unread_count,
            archived_count=len(archived),
            alert_count=alert_count,
            digest_count=digest_count,
            latest_notification_at=latest_ts,
            counts_by_type=counts_by_type,
            counts_by_severity=counts_by_severity,
        )
