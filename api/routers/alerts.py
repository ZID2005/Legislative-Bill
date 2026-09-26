"""
api/routers/alerts.py
=====================
REST routes for Alert Inbox events and read/archive tracking.
Enforces multi-tenant isolation (user_id, tenant_id).
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    CurrentUser,
    get_alert_event_repository,
    get_alert_preference_repository,
    get_current_user,
)
from api.errors import NotFoundError
from api.schemas import (
    AlertEventResponse,
    AlertPreferenceResponse,
    AlertPreferenceUpdateRequest,
    PaginatedResponse,
    UnreadCountResponse,
)
from schemas.alert import (
    AlertEvent,
    AlertPreference,
    AlertSeverity,
    AlertType,
    DigestFrequency,
    NotificationChannel,
)
from storage.alert_event_repository import AlertEventRepository
from storage.alert_preference_repository import AlertPreferenceRepository

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _to_alert_response(e: AlertEvent) -> AlertEventResponse:
    entity_type_str = None
    if e.entity_type is not None:
        entity_type_str = e.entity_type.value if hasattr(e.entity_type, "value") else str(e.entity_type)

    alert_type_str = e.alert_type.value if hasattr(e.alert_type, "value") else str(e.alert_type)
    severity_str = e.severity.value if hasattr(e.severity, "value") else str(e.severity)

    deep_link = None
    if isinstance(e.metadata, dict):
        dl = e.metadata.get("deep_link")
        if isinstance(dl, str):
            deep_link = dl
        elif isinstance(dl, dict):
            deep_link = dl.get("route")

    if not deep_link and e.entity_id:
        if entity_type_str == "BILL":
            deep_link = f"/bills/{e.entity_id}"
        elif entity_type_str == "COMPANY":
            deep_link = f"/companies/{e.entity_id}"

    return AlertEventResponse(
        alert_event_id=e.alert_event_id,
        user_id=e.user_id,
        tenant_id=e.tenant_id,
        watchlist_id=e.watchlist_id,
        alert_type=alert_type_str,
        severity=severity_str,
        title=e.title,
        summary=e.summary,
        entity_type=entity_type_str,
        entity_id=e.entity_id,
        created_at=e.created_at,
        is_read=e.is_read,
        is_archived=e.is_archived,
        deep_link=deep_link,
    )


@router.get("", response_model=PaginatedResponse[AlertEventResponse])
def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = Query(None),
    watchlist_id: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    alert_repo: AlertEventRepository = Depends(get_alert_event_repository),
) -> PaginatedResponse[AlertEventResponse]:
    """
    List user alert inbox events with optional filtering.
    Enforces user and tenant isolation.
    """
    if watchlist_id:
        events = alert_repo.list_by_watchlist(
            watchlist_id=watchlist_id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            limit=500,
        )
    else:
        events = alert_repo.list_by_user(
            user_id=current_user.user_id,
            tenant_id=current_user.tenant_id,
            limit=500,
        )

    if severity:
        sev_upper = severity.strip().upper()
        events = [e for e in events if (e.severity.value if hasattr(e.severity, "value") else str(e.severity)).upper() == sev_upper]

    if is_read is not None:
        events = [e for e in events if e.is_read == is_read]

    total = len(events)
    offset = (page - 1) * limit
    paged = events[offset : offset + limit]

    return PaginatedResponse(
        items=[_to_alert_response(e) for e in paged],
        total=total,
        page=page,
        limit=limit,
        pages=max(1, (total + limit - 1) // limit) if total > 0 else 1,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_alerts_count(
    current_user: CurrentUser = Depends(get_current_user),
    alert_repo: AlertEventRepository = Depends(get_alert_event_repository),
) -> UnreadCountResponse:
    """
    Get unread alert count for the authenticated user.
    """
    unread = alert_repo.list_unread(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        limit=1000,
    )
    return UnreadCountResponse(
        unread_count=len(unread),
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
    )


@router.get("/preferences", response_model=AlertPreferenceResponse)
def get_alert_preferences(
    current_user: CurrentUser = Depends(get_current_user),
    pref_repo: AlertPreferenceRepository = Depends(get_alert_preference_repository),
) -> AlertPreferenceResponse:
    """Retrieve user alert preferences. Creates defaults if not yet saved."""
    pref = pref_repo.get(user_id=current_user.user_id, tenant_id=current_user.tenant_id)
    if not pref:
        pref = AlertPreference(
            user_id=current_user.user_id,
            tenant_id=current_user.tenant_id,
            enabled=True,
            minimum_severity=AlertSeverity.LOW,
            digest_frequency=DigestFrequency.REAL_TIME,
        )
        pref_repo.save(pref)
    return AlertPreferenceResponse(**pref.to_dict())


@router.patch("/preferences", response_model=AlertPreferenceResponse)
@router.put("/preferences", response_model=AlertPreferenceResponse)
def update_alert_preferences(
    req: AlertPreferenceUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    pref_repo: AlertPreferenceRepository = Depends(get_alert_preference_repository),
) -> AlertPreferenceResponse:
    """Update user alert preferences."""
    pref = pref_repo.get(user_id=current_user.user_id, tenant_id=current_user.tenant_id)
    if not pref:
        pref = AlertPreference(
            user_id=current_user.user_id,
            tenant_id=current_user.tenant_id,
        )
    if req.enabled is not None:
        pref.enabled = req.enabled
    if req.minimum_severity is not None:
        pref.minimum_severity = AlertSeverity(req.minimum_severity.strip().upper())
    if req.allowed_alert_types is not None:
        pref.allowed_alert_types = [AlertType(a.strip().upper()) for a in req.allowed_alert_types]
    if req.allowed_channels is not None:
        pref.allowed_channels = [NotificationChannel(c.strip().upper()) for c in req.allowed_channels]
    if req.digest_frequency is not None:
        pref.digest_frequency = DigestFrequency(req.digest_frequency.strip().upper())
    pref_repo.save(pref)
    return AlertPreferenceResponse(**pref.to_dict())


@router.post("/read-all")
@router.patch("/read-all")
def mark_all_alerts_read(
    current_user: CurrentUser = Depends(get_current_user),
    alert_repo: AlertEventRepository = Depends(get_alert_event_repository),
) -> dict[str, int]:
    """Mark all unread alert events as read for the authenticated user."""
    count = alert_repo.mark_all_read(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
    )
    return {"marked_count": count}


@router.get("/{alert_id}", response_model=AlertEventResponse)
def get_alert_detail(
    alert_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    alert_repo: AlertEventRepository = Depends(get_alert_event_repository),
) -> AlertEventResponse:
    """
    Retrieve single alert event by ID.
    Enforces user and tenant isolation.
    """
    event = alert_repo.get(
        alert_event_id=alert_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not event:
        raise NotFoundError(f"Alert event '{alert_id}' not found.")
    return _to_alert_response(event)


@router.post("/{alert_id}/read")
def mark_alert_read(
    alert_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    alert_repo: AlertEventRepository = Depends(get_alert_event_repository),
) -> dict[str, bool]:
    """
    Mark alert event as read.
    """
    success = alert_repo.mark_read(
        alert_event_id=alert_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise NotFoundError(f"Alert event '{alert_id}' not found.")
    return {"success": True, "is_read": True}


@router.post("/{alert_id}/archive")
def archive_alert(
    alert_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    alert_repo: AlertEventRepository = Depends(get_alert_event_repository),
) -> dict[str, bool]:
    """
    Archive alert event.
    """
    success = alert_repo.archive(
        alert_event_id=alert_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not success:
        raise NotFoundError(f"Alert event '{alert_id}' not found.")
    return {"success": True, "is_archived": True}
