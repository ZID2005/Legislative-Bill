"""
services/notification_service.py
================================
Core business service managing in-app alert notifications.

Transforms upstream AlertEvents, AlertGroups, and AlertDigests into
presentation-ready Notification records, coordinates deterministic deduplication,
and manages notification lifecycle state (read/unread, archive, delete).

Task 8.13.6 — Notification Dispatch & In-App Notification Center API.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.alert import (
    AlertEvent,
    AlertSeverity,
    AlertType,
    Notification,
    NotificationChannel,
    NotificationSourceType,
    NotificationStatus,
    NotificationType,
    compute_notification_dedup_key,
    build_deep_link,
)
from schemas.alert_digest import AlertDigest
from schemas.alert_group import AlertGroup, AlertGroupType
from schemas.notification_delivery import DeliveryResult
from services.notification_dispatcher import NotificationDispatcher
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.notification_repository import NotificationRepository

logger = get_logger(__name__)


def _map_alert_type_to_notification_type(alert_type: AlertType | str) -> NotificationType:
    """Map AlertType to appropriate user-facing NotificationType."""
    if isinstance(alert_type, str):
        try:
            alert_type = AlertType(alert_type.strip().upper())
        except ValueError:
            return NotificationType.ALERT

    if alert_type in (
        AlertType.NEW_BILL,
        AlertType.BILL_STATUS_CHANGE,
        AlertType.BILL_VERSION_CHANGE,
        AlertType.BILL_DOCUMENT_CHANGE,
    ):
        return NotificationType.BILL_UPDATE
    elif alert_type in (AlertType.NEW_COMPANY_EXPOSURE, AlertType.EXPOSURE_CHANGE):
        return NotificationType.COMPANY_EXPOSURE
    elif alert_type in (AlertType.STATE_IMPACT,):
        return NotificationType.STATE_UPDATE
    elif alert_type in (AlertType.LEGISLATIVE_MONITORING_CHANGE,):
        return NotificationType.LEGISLATIVE_UPDATE
    elif alert_type in (AlertType.SECTOR_IMPACT,):
        return NotificationType.ALERT
    return NotificationType.ALERT


def _map_group_type_to_notification_type(group_type: AlertGroupType | str) -> NotificationType:
    """Map AlertGroupType to appropriate user-facing NotificationType."""
    if isinstance(group_type, str):
        try:
            group_type = AlertGroupType(group_type.strip().upper())
        except ValueError:
            return NotificationType.ALERT

    if group_type == AlertGroupType.BILL:
        return NotificationType.BILL_UPDATE
    elif group_type == AlertGroupType.COMPANY:
        return NotificationType.COMPANY_EXPOSURE
    elif group_type in (AlertGroupType.STATE, AlertGroupType.JURISDICTION):
        return NotificationType.STATE_UPDATE
    elif group_type == AlertGroupType.EVENT:
        return NotificationType.LEGISLATIVE_UPDATE
    return NotificationType.ALERT


class NotificationService:
    """
    Business service for creating, managing, and retrieving in-app notifications.
    """

    def __init__(
        self,
        notification_repo: Optional[NotificationRepository] = None,
        dispatcher: Optional[NotificationDispatcher] = None,
        alert_pref_repo: Optional[AlertPreferenceRepository] = None,
    ) -> None:
        self.repo = notification_repo or NotificationRepository()
        self.alert_pref_repo = alert_pref_repo or AlertPreferenceRepository()
        self.dispatcher = dispatcher or NotificationDispatcher(
            notification_repo=self.repo,
            alert_pref_repo=self.alert_pref_repo,
        )

    # -----------------------------------------------------------------------
    # Core In-App CRUD & Lifecycle Operations
    # -----------------------------------------------------------------------

    def create_notification(
        self,
        notification: Notification,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Notification:
        """
        Create and dispatch a notification record with deduplication.
        """
        if tenant_id:
            notification.tenant_id = tenant_id
        if user_id:
            notification.user_id = user_id

        return self.dispatcher.dispatch_in_app(notification)

    def dispatch_outbound(
        self,
        notification: Notification,
        channel: NotificationChannel,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        """
        Dispatch a notification to an outbound channel (EMAIL, PUSH, WEBHOOK).
        """
        return self.dispatcher.dispatch(
            notification=notification,
            channel=channel,
            recipient=recipient,
            **kwargs,
        )

    def enqueue_delivery(
        self,
        notification: Notification,
        channel: NotificationChannel,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        """
        Lightweight delivery queue abstraction per Task 8.13.7 Section 23.
        """
        return self.dispatcher.enqueue_delivery(
            notification=notification,
            channel=channel,
            recipient=recipient,
            **kwargs,
        )

    def get_notification(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Retrieve a notification ensuring tenant and user isolation.
        """
        return self.repo.get(notification_id, tenant_id=tenant_id, user_id=user_id)

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
        List notifications with deterministic ordering, pagination, and multi-criteria filters.
        """
        return self.repo.list_by_user(
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

    def get_unread_notifications(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        limit: int = 50,
    ) -> list[Notification]:
        """
        List active unread notifications.
        """
        return self.list_notifications(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=limit,
            is_read=False,
            is_archived=False,
            is_deleted=False,
        )

    def get_unread_count(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        include_archived: bool = False,
    ) -> int:
        """
        Count active unread notifications strictly for the user and tenant.
        """
        return self.repo.count_unread(
            user_id=user_id,
            tenant_id=tenant_id,
            include_archived=include_archived,
        )

    def mark_as_read(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Mark notification as read enforcing tenant and user ownership."""
        return self.repo.mark_read(notification_id, tenant_id=tenant_id, user_id=user_id)

    def mark_as_unread(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Mark notification as unread enforcing tenant and user ownership."""
        return self.repo.mark_unread(notification_id, tenant_id=tenant_id, user_id=user_id)

    def archive_notification(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Archive notification enforcing ownership."""
        return self.repo.archive(notification_id, tenant_id=tenant_id, user_id=user_id)

    def unarchive_notification(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Unarchive notification enforcing ownership."""
        return self.repo.unarchive(notification_id, tenant_id=tenant_id, user_id=user_id)

    def delete_notification(
        self,
        notification_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        soft: bool = True,
    ) -> bool:
        """Delete notification preserving underlying legislative evidence."""
        return self.repo.delete(notification_id, tenant_id=tenant_id, user_id=user_id, soft=soft)

    # -----------------------------------------------------------------------
    # Transformation Pipelines (Event / Group / Digest -> Notification)
    # -----------------------------------------------------------------------

    def create_notification_from_alert_event(
        self,
        event: AlertEvent,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Transform an AlertEvent into a deduplicated user-facing Notification record.

        - Preserves source event ID, tenant, user, watchlist.
        - Preserves alert type, severity, grounded headline and summary.
        - Preserves prediction references for Central bills without recalculation.
        - Preserves State and intelligence entity references without fabricating stock predictions.
        """
        t_id = tenant_id or event.tenant_id
        u_id = user_id or event.user_id

        notif_type = _map_alert_type_to_notification_type(event.alert_type)
        dedup_key = compute_notification_dedup_key(
            tenant_id=t_id,
            user_id=u_id,
            source_type=NotificationSourceType.ALERT_EVENT.value,
            source_id=event.alert_event_id,
            channel=NotificationChannel.IN_APP.value,
        )

        # Check existing notification
        existing = self.repo.find_by_dedup_key(dedup_key, tenant_id=t_id, user_id=u_id)
        if existing:
            return existing

        entity_type_str = event.entity_type.value if event.entity_type else None
        deep_link = build_deep_link(
            entity_type=entity_type_str,
            entity_id=event.entity_id,
            source_type=NotificationSourceType.ALERT_EVENT.value,
            source_id=event.alert_event_id,
            metadata=event.metadata,
        )

        metadata = dict(event.metadata)
        metadata["alert_type"] = event.alert_type.value if isinstance(event.alert_type, AlertType) else str(event.alert_type)
        if event.watchlist_id:
            metadata["watchlist_id"] = event.watchlist_id
        if event.alert_rule_id:
            metadata["alert_rule_id"] = event.alert_rule_id
        if event.source_event_id:
            metadata["source_event_id"] = event.source_event_id

        notif = Notification(
            notification_id=str(uuid.uuid4()),
            tenant_id=t_id,
            user_id=u_id,
            alert_event_id=event.alert_event_id,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.DELIVERED,
            notification_type=notif_type,
            title=event.title,
            summary=event.summary,
            severity=event.severity,
            source_type=NotificationSourceType.ALERT_EVENT.value,
            source_id=event.alert_event_id,
            entity_type=entity_type_str,
            entity_id=event.entity_id,
            state=metadata.get("state"),
            jurisdiction=metadata.get("jurisdiction"),
            deep_link=deep_link,
            dedup_key=dedup_key,
            metadata=metadata,
        )

        return self.dispatcher.dispatch_in_app(notif)

    def create_notifications_from_alert_events(
        self,
        events: list[AlertEvent],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[Notification]:
        """Batch process AlertEvents into notifications."""
        results: list[Notification] = []
        for ev in events:
            notif = self.create_notification_from_alert_event(ev, tenant_id=tenant_id, user_id=user_id)
            if notif:
                results.append(notif)
        return results

    def create_notification_from_alert_group(
        self,
        group: AlertGroup,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Transform an AlertGroup into an aggregated in-app Notification.

        - Preserves group ID and underlying event IDs without duplicating separate alerts.
        - Uses maximum group severity.
        - Preserves primary entity dimensions.
        """
        t_id = tenant_id or group.tenant_id
        u_id = user_id or group.user_id

        notif_type = _map_group_type_to_notification_type(group.group_type)
        dedup_key = compute_notification_dedup_key(
            tenant_id=t_id,
            user_id=u_id,
            source_type=NotificationSourceType.ALERT_GROUP.value,
            source_id=group.group_id,
            channel=NotificationChannel.IN_APP.value,
        )

        existing = self.repo.find_by_dedup_key(dedup_key, tenant_id=t_id, user_id=u_id)
        if existing:
            return existing

        primary_entity_id = group.affected_entity_ids[0] if group.affected_entity_ids else None
        first_event_id = group.event_ids[0] if group.event_ids else ""

        deep_link = build_deep_link(
            entity_type=group.group_type.value,
            entity_id=primary_entity_id,
            source_type=NotificationSourceType.ALERT_GROUP.value,
            source_id=group.group_id,
            destination_type="ALERT_GROUP_DETAIL",
            metadata=group.metadata,
        )

        metadata = dict(group.metadata)
        metadata["group_id"] = group.group_id
        metadata["group_type"] = group.group_type.value
        metadata["alert_count"] = group.alert_count
        metadata["event_ids"] = list(group.event_ids)
        metadata["affected_entity_ids"] = list(group.affected_entity_ids)
        if group.watchlist_id:
            metadata["watchlist_id"] = group.watchlist_id

        notif = Notification(
            notification_id=str(uuid.uuid4()),
            tenant_id=t_id,
            user_id=u_id,
            alert_event_id=first_event_id,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.DELIVERED,
            notification_type=notif_type,
            title=group.title,
            summary=group.summary,
            severity=group.severity,
            source_type=NotificationSourceType.ALERT_GROUP.value,
            source_id=group.group_id,
            alert_group_id=group.group_id,
            entity_type=group.group_type.value,
            entity_id=primary_entity_id,
            state=metadata.get("state"),
            jurisdiction=metadata.get("jurisdiction"),
            deep_link=deep_link,
            dedup_key=dedup_key,
            metadata=metadata,
        )

        return self.dispatcher.dispatch_in_app(notif)

    def create_notifications_from_alert_groups(
        self,
        groups: list[AlertGroup],
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[Notification]:
        """Batch process AlertGroups into notifications."""
        results: list[Notification] = []
        for grp in groups:
            notif = self.create_notification_from_alert_group(grp, tenant_id=tenant_id, user_id=user_id)
            if notif:
                results.append(notif)
        return results

    def create_notification_from_digest(
        self,
        digest: AlertDigest,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Notification]:
        """
        Transform an AlertDigest into a structured notification record.

        References the underlying digest without sending external emails/push.
        """
        t_id = tenant_id or digest.tenant_id
        u_id = user_id or digest.user_id

        dedup_key = compute_notification_dedup_key(
            tenant_id=t_id,
            user_id=u_id,
            source_type=NotificationSourceType.DIGEST.value,
            source_id=digest.digest_id,
            channel=NotificationChannel.IN_APP.value,
        )

        existing = self.repo.find_by_dedup_key(dedup_key, tenant_id=t_id, user_id=u_id)
        if existing:
            return existing

        first_event_id = digest.event_ids[0] if digest.event_ids else ""
        cadence_str = digest.digest_type.value.capitalize()
        title = f"{cadence_str} Legislative Alert Digest ({digest.group_count} groups, {digest.event_count} alerts)"

        summary_parts = [
            f"Digest period: {digest.period_start[:10]} to {digest.period_end[:10]}."
        ]
        if digest.affected_bills:
            summary_parts.append(f"Bills: {len(digest.affected_bills)}.")
        if digest.affected_companies:
            summary_parts.append(f"Companies: {len(digest.affected_companies)}.")
        if digest.affected_states:
            summary_parts.append(f"States: {len(digest.affected_states)}.")
        summary = " ".join(summary_parts)

        deep_link = build_deep_link(
            entity_type="DIGEST",
            entity_id=digest.digest_id,
            source_type=NotificationSourceType.DIGEST.value,
            source_id=digest.digest_id,
            destination_type="DIGEST_DETAIL",
            metadata=digest.metadata,
        )

        metadata = dict(digest.metadata)
        metadata["digest_id"] = digest.digest_id
        metadata["digest_type"] = digest.digest_type.value
        metadata["group_count"] = digest.group_count
        metadata["event_count"] = digest.event_count
        metadata["group_ids"] = list(digest.group_ids)
        metadata["event_ids"] = list(digest.event_ids)
        metadata["affected_companies"] = list(digest.affected_companies)
        metadata["affected_bills"] = list(digest.affected_bills)
        metadata["affected_states"] = list(digest.affected_states)
        metadata["jurisdictions"] = list(digest.jurisdictions)

        notif = Notification(
            notification_id=str(uuid.uuid4()),
            tenant_id=t_id,
            user_id=u_id,
            alert_event_id=first_event_id,
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.DELIVERED,
            notification_type=NotificationType.DIGEST,
            title=title,
            summary=summary,
            severity=AlertSeverity.INFO,
            source_type=NotificationSourceType.DIGEST.value,
            source_id=digest.digest_id,
            digest_id=digest.digest_id,
            entity_type="DIGEST",
            entity_id=digest.digest_id,
            deep_link=deep_link,
            dedup_key=dedup_key,
            metadata=metadata,
        )

        return self.dispatcher.dispatch_in_app(notif)
