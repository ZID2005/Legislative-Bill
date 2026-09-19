"""
api/routers/notifications.py
============================
REST routes for In-App Notification Center, delivery status, and read/archive operations.
Strictly enforces multi-tenant scoping (tenant_id, user_id).
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    CurrentUser,
    get_current_user,
    get_notification_center_service,
)
from api.errors import NotFoundError
from api.schemas import (
    NotificationResponse,
    NotificationSummaryResponse,
    PaginatedResponse,
    UnreadCountResponse,
)
from schemas.alert import Notification
from services.notification_center_service import NotificationCenterService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _to_notification_response(n: Notification) -> NotificationResponse:
    nt_str = n.notification_type.value if hasattr(n.notification_type, "value") else str(n.notification_type)
    sev_str = n.severity.value if hasattr(n.severity, "value") else str(n.severity)
    status_str = n.status.value if hasattr(n.status, "value") else str(n.status)

    action_url = None
    if isinstance(n.deep_link, dict):
        action_url = n.deep_link.get("route")
    elif isinstance(n.deep_link, str):
        action_url = n.deep_link

    return NotificationResponse(
        notification_id=n.notification_id,
        user_id=n.user_id,
        tenant_id=n.tenant_id,
        notification_type=nt_str,
        severity=sev_str,
        title=n.title,
        message=n.message,
        status=status_str,
        is_read=n.is_read,
        is_archived=n.is_archived,
        created_at=n.created_at,
        delivered_at=n.delivered_at,
        action_url=action_url,
    )


@router.get("", response_model=PaginatedResponse[NotificationResponse])
def list_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    is_read: Optional[bool] = Query(None),
    is_archived: Optional[bool] = Query(False),
    notification_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    notification_center: NotificationCenterService = Depends(get_notification_center_service),
) -> PaginatedResponse[NotificationResponse]:
    """
    List notifications for current user with filtering and pagination.
    """
    offset = (page - 1) * limit
    notifications = notification_center.list_notifications(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        limit=limit,
        offset=offset,
        is_read=is_read,
        is_archived=is_archived,
        notification_type=notification_type,
        severity=severity,
    )

    # For accurate total count under current filters
    all_filtered = notification_center.list_notifications(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        limit=10000,
        offset=0,
        is_read=is_read,
        is_archived=is_archived,
        notification_type=notification_type,
        severity=severity,
    )
    total = len(all_filtered)

    return PaginatedResponse(
        items=[_to_notification_response(n) for n in notifications],
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit) if total > 0 else 1,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: CurrentUser = Depends(get_current_user),
    notification_center: NotificationCenterService = Depends(get_notification_center_service),
) -> UnreadCountResponse:
    """
    Get unread notification count.
    """
    count = notification_center.get_unread_count(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
    )
    return UnreadCountResponse(
        unread_count=count,
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
    )


@router.get("/summary", response_model=NotificationSummaryResponse)
def get_summary(
    current_user: CurrentUser = Depends(get_current_user),
    notification_center: NotificationCenterService = Depends(get_notification_center_service),
) -> NotificationSummaryResponse:
    """
    Consolidated notification center summary counts and breakdown.
    """
    summary = notification_center.get_notification_center_summary(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
    )
    return NotificationSummaryResponse(**summary.to_dict())


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification_detail(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    notification_center: NotificationCenterService = Depends(get_notification_center_service),
) -> NotificationResponse:
    """
    Retrieve a single notification by ID.
    Enforces tenant and user isolation.
    """
    notif = notification_center.get_notification(
        notification_id=notification_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not notif:
        raise NotFoundError(f"Notification '{notification_id}' not found.")
    return _to_notification_response(notif)


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    notification_center: NotificationCenterService = Depends(get_notification_center_service),
) -> dict[str, bool]:
    """
    Mark notification as read.
    """
    success = notification_center.mark_read(
        notification_id=notification_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise NotFoundError(f"Notification '{notification_id}' not found.")
    return {"success": True, "is_read": True}


@router.post("/read-all")
def mark_all_notifications_read(
    current_user: CurrentUser = Depends(get_current_user),
    notification_center: NotificationCenterService = Depends(get_notification_center_service),
) -> dict[str, int]:
    """
    Mark all unread notifications as read.
    """
    count = notification_center.mark_all_read(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
    )
    return {"marked_count": count}


@router.post("/{notification_id}/archive")
def archive_notification(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    notification_center: NotificationCenterService = Depends(get_notification_center_service),
) -> dict[str, bool]:
    """
    Archive a notification.
    """
    success = notification_center.archive(
        notification_id=notification_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise NotFoundError(f"Notification '{notification_id}' not found.")
    return {"success": True, "is_archived": True}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    notification_center: NotificationCenterService = Depends(get_notification_center_service),
) -> dict[str, bool]:
    """
    Soft-delete a notification while preserving evidence.
    """
    success = notification_center.delete(
        notification_id=notification_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        soft=True,
    )
    if not success:
        raise NotFoundError(f"Notification '{notification_id}' not found.")
    return {"success": True, "deleted": True}
