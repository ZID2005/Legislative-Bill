"""
api/routers/watchlists.py
=========================
REST API router for User Watchlists, Entity Subscriptions, and Alert Rules.
Enforces multi-tenant and user isolation on every operation.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends

from api.dependencies import (
    CurrentUser,
    get_current_user,
    get_watchlist_service,
)
from api.errors import BadRequestError, ForbiddenError, NotFoundError
from api.schemas import (
    AlertRuleCreateRequest,
    AlertRuleResponse,
    AlertRuleUpdateRequest,
    SuccessStatusResponse,
    WatchlistCreateRequest,
    WatchlistItemCreateRequest,
    WatchlistItemResponse,
    WatchlistResponse,
    WatchlistUpdateRequest,
)
from schemas.alert import AlertSeverity, AlertType
from schemas.watchlist import Watchlist, WatchlistItem, WatchlistEntityType
from services.watchlist_service import WatchlistService

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


def _to_watchlist_response(
    wl: Watchlist,
    service: WatchlistService,
    user: CurrentUser,
) -> WatchlistResponse:
    items = service.watchlist_repo.list_items_by_watchlist(
        wl.watchlist_id, tenant_id=user.tenant_id, user_id=user.user_id, is_active=True
    )
    rules = service.alert_rule_repo.list_by_watchlist(
        watchlist_id=wl.watchlist_id, tenant_id=user.tenant_id, user_id=user.user_id
    )

    item_responses = [
        WatchlistItemResponse(
            item_id=it.item_id,
            watchlist_id=it.watchlist_id,
            entity_type=it.entity_type.value if hasattr(it.entity_type, "value") else str(it.entity_type),
            entity_id=it.entity_id,
            canonical_name=getattr(it, "display_name", "") or getattr(it, "canonical_name", "") or it.entity_id,
            state=getattr(it, "state", None),
            notes=it.notes,
            is_active=it.is_active,
            created_at=it.created_at,
        )
        for it in items
    ]

    rule_responses = [
        AlertRuleResponse(
            alert_rule_id=r.alert_rule_id,
            user_id=r.user_id,
            tenant_id=r.tenant_id,
            watchlist_id=r.watchlist_id,
            alert_type=r.alert_type.value if hasattr(r.alert_type, "value") else str(r.alert_type),
            minimum_severity=r.minimum_severity.value if hasattr(r.minimum_severity, "value") else str(r.minimum_severity),
            enabled=r.enabled,
            created_at=r.created_at,
        )
        for r in rules
    ]

    return WatchlistResponse(
        watchlist_id=wl.watchlist_id,
        user_id=wl.user_id,
        tenant_id=wl.tenant_id,
        name=wl.name,
        description=wl.description,
        is_default=wl.is_default,
        is_active=wl.is_active,
        created_at=wl.created_at,
        updated_at=wl.updated_at,
        items_count=len(items),
        items=item_responses,
        rules=rule_responses,
    )


@router.get(
    "",
    response_model=list[WatchlistResponse],
    summary="List watchlists for current user",
    description="Retrieve all active watchlists belonging to the authenticated user and tenant.",
)
def list_watchlists(
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> list[WatchlistResponse]:
    watchlists = watchlist_service.list_user_watchlists(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        is_active=True,
    )
    return [_to_watchlist_response(wl, watchlist_service, current_user) for wl in watchlists]


@router.post(
    "",
    response_model=WatchlistResponse,
    status_code=201,
    summary="Create a new watchlist",
    description="Create a new named watchlist for the current tenant and user.",
)
def create_watchlist(
    body: WatchlistCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistResponse:
    wl = watchlist_service.create_watchlist(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        name=body.name,
        description=body.description,
        is_default=body.is_default,
    )
    return _to_watchlist_response(wl, watchlist_service, current_user)


@router.get(
    "/{watchlist_id}",
    response_model=WatchlistResponse,
    summary="Get single watchlist by ID",
    description="Retrieve watchlist details, items, and alert rules. Enforces tenant ownership.",
)
def get_watchlist(
    watchlist_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistResponse:
    wl = watchlist_service.get_watchlist(
        watchlist_id=watchlist_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not wl or not wl.is_active:
        # Check if exists in another tenant to raise Forbidden vs NotFound
        other_wl = watchlist_service.watchlist_repo.get(watchlist_id)
        if other_wl and other_wl.tenant_id != current_user.tenant_id:
            raise ForbiddenError(
                code="CROSS_TENANT_ACCESS_DENIED",
                message="Access to this watchlist is prohibited under multi-tenant isolation.",
            )
        raise NotFoundError(
            code="WATCHLIST_NOT_FOUND",
            message=f"Watchlist '{watchlist_id}' not found.",
        )

    return _to_watchlist_response(wl, watchlist_service, current_user)


@router.patch(
    "/{watchlist_id}",
    response_model=WatchlistResponse,
    summary="Update watchlist details",
    description="Update name or description of an existing watchlist.",
)
def update_watchlist(
    watchlist_id: str,
    body: WatchlistUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistResponse:
    wl = watchlist_service.get_watchlist(
        watchlist_id=watchlist_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not wl or not wl.is_active:
        other_wl = watchlist_service.watchlist_repo.get(watchlist_id)
        if other_wl and other_wl.tenant_id != current_user.tenant_id:
            raise ForbiddenError(
                code="CROSS_TENANT_ACCESS_DENIED",
                message="Access to this watchlist is prohibited under multi-tenant isolation.",
            )
        raise NotFoundError(
            code="WATCHLIST_NOT_FOUND",
            message=f"Watchlist '{watchlist_id}' not found.",
        )

    if body.name is not None:
        wl.name = body.name
    if body.description is not None:
        wl.description = body.description
    if body.is_active is not None:
        wl.is_active = body.is_active

    try:
        updated = watchlist_service.update_watchlist(
            wl, tenant_id=current_user.tenant_id, user_id=current_user.user_id
        )
    except PermissionError as e:
        raise ForbiddenError(code="ACCESS_DENIED", message=str(e))

    return _to_watchlist_response(updated, watchlist_service, current_user)


@router.delete(
    "/{watchlist_id}",
    response_model=SuccessStatusResponse,
    summary="Delete/deactivate a watchlist",
    description="Deactivate a watchlist and purge all associated entries from inverted indices.",
)
def delete_watchlist(
    watchlist_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> SuccessStatusResponse:
    wl = watchlist_service.get_watchlist(
        watchlist_id=watchlist_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not wl or not wl.is_active:
        other_wl = watchlist_service.watchlist_repo.get(watchlist_id)
        if other_wl and other_wl.tenant_id != current_user.tenant_id:
            raise ForbiddenError(
                code="CROSS_TENANT_ACCESS_DENIED",
                message="Access to this watchlist is prohibited under multi-tenant isolation.",
            )
        raise NotFoundError(
            code="WATCHLIST_NOT_FOUND",
            message=f"Watchlist '{watchlist_id}' not found.",
        )

    try:
        watchlist_service.deactivate_watchlist(
            watchlist_id=watchlist_id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
        )
    except PermissionError:
        other_wl = watchlist_service.watchlist_repo.get(watchlist_id)
        if other_wl and other_wl.tenant_id != current_user.tenant_id:
            raise ForbiddenError(
                code="CROSS_TENANT_ACCESS_DENIED",
                message="Access to this watchlist is prohibited under multi-tenant isolation.",
            )
        raise NotFoundError(
            code="WATCHLIST_NOT_FOUND",
            message=f"Watchlist '{watchlist_id}' not found.",
        )

    return SuccessStatusResponse(success=True, message="Watchlist deactivated.")


# ---------------------------------------------------------------------------
# Watchlist Items
# ---------------------------------------------------------------------------


@router.post(
    "/{watchlist_id}/items",
    response_model=WatchlistItemResponse,
    status_code=201,
    summary="Add entity to watchlist",
    description="Subscribe a company, bill, state, sector, or industry to the watchlist. Automatically synchronizes inverted subscriber index.",
)
def add_watchlist_item(
    watchlist_id: str,
    body: WatchlistItemCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistItemResponse:
    try:
        item = watchlist_service.add_item(
            watchlist_id=watchlist_id,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            display_name=body.display_name,
            notes=body.notes,
        )
    except PermissionError as e:
        raise ForbiddenError(code="ACCESS_DENIED", message=str(e))
    except ValueError as e:
        raise BadRequestError(code="INVALID_ENTITY", message=str(e))

    return WatchlistItemResponse(
        item_id=item.item_id,
        watchlist_id=item.watchlist_id,
        entity_type=item.entity_type.value if hasattr(item.entity_type, "value") else str(item.entity_type),
        entity_id=item.entity_id,
        canonical_name=getattr(item, "display_name", "") or getattr(item, "canonical_name", "") or item.entity_id,
        state=getattr(item, "state", None),
        notes=item.notes,
        is_active=item.is_active,
        created_at=item.created_at,
    )


@router.delete(
    "/{watchlist_id}/items/{item_id}",
    response_model=SuccessStatusResponse,
    summary="Remove entity item from watchlist",
    description="Remove an entity from the watchlist and unbind subscriber index.",
)
def remove_watchlist_item(
    watchlist_id: str,
    item_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> SuccessStatusResponse:
    wl = watchlist_service.get_watchlist(
        watchlist_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not wl:
        raise NotFoundError(code="WATCHLIST_NOT_FOUND", message=f"Watchlist '{watchlist_id}' not found.")

    try:
        watchlist_service.remove_item(
            item_id=item_id,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
        )
    except PermissionError as e:
        raise ForbiddenError(code="ACCESS_DENIED", message=str(e))
    except ValueError as e:
        raise NotFoundError(code="ITEM_NOT_FOUND", message=str(e))

    return SuccessStatusResponse(success=True, message="Item removed from watchlist.")


# ---------------------------------------------------------------------------
# Watchlist Alert Rules
# ---------------------------------------------------------------------------


@router.get(
    "/{watchlist_id}/rules",
    response_model=list[AlertRuleResponse],
    summary="List alert rules for watchlist",
    description="Retrieve all alert rules configured for this watchlist.",
)
def list_watchlist_rules(
    watchlist_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> list[AlertRuleResponse]:
    # Verify watchlist ownership
    wl = watchlist_service.get_watchlist(
        watchlist_id, tenant_id=current_user.tenant_id, user_id=current_user.user_id
    )
    if not wl:
        raise NotFoundError(code="WATCHLIST_NOT_FOUND", message=f"Watchlist '{watchlist_id}' not found.")

    rules = watchlist_service.list_alert_rules(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        watchlist_id=watchlist_id,
    )
    return [
        AlertRuleResponse(
            alert_rule_id=r.alert_rule_id,
            user_id=r.user_id,
            tenant_id=r.tenant_id,
            watchlist_id=r.watchlist_id,
            alert_type=r.alert_type.value if hasattr(r.alert_type, "value") else str(r.alert_type),
            minimum_severity=r.minimum_severity.value if hasattr(r.minimum_severity, "value") else str(r.minimum_severity),
            enabled=r.enabled,
            created_at=r.created_at,
        )
        for r in rules
    ]


@router.post(
    "/{watchlist_id}/rules",
    response_model=AlertRuleResponse,
    status_code=201,
    summary="Create alert rule for watchlist",
    description="Add an alert threshold rule to this watchlist.",
)
def create_watchlist_rule(
    watchlist_id: str,
    body: AlertRuleCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> AlertRuleResponse:
    try:
        rule = watchlist_service.create_alert_rule(
            user_id=current_user.user_id,
            tenant_id=current_user.tenant_id,
            watchlist_id=watchlist_id,
            alert_type=body.alert_type,
            minimum_severity=body.minimum_severity,
            enabled=body.enabled,
        )
    except PermissionError as e:
        raise ForbiddenError(code="ACCESS_DENIED", message=str(e))
    except ValueError as e:
        raise BadRequestError(code="INVALID_RULE", message=str(e))

    return AlertRuleResponse(
        alert_rule_id=rule.alert_rule_id,
        user_id=rule.user_id,
        tenant_id=rule.tenant_id,
        watchlist_id=rule.watchlist_id,
        alert_type=rule.alert_type.value if hasattr(rule.alert_type, "value") else str(rule.alert_type),
        minimum_severity=rule.minimum_severity.value if hasattr(rule.minimum_severity, "value") else str(rule.minimum_severity),
        enabled=rule.enabled,
        created_at=rule.created_at,
    )


@router.patch(
    "/{watchlist_id}/rules/{rule_id}",
    response_model=AlertRuleResponse,
    summary="Update an alert rule",
    description="Modify severity threshold or enabled status of an alert rule.",
)
def update_watchlist_rule(
    watchlist_id: str,
    rule_id: str,
    body: AlertRuleUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> AlertRuleResponse:
    rule = watchlist_service.get_alert_rule(
        rule_id, tenant_id=current_user.tenant_id, user_id=current_user.user_id
    )
    if not rule or rule.watchlist_id != watchlist_id:
        raise NotFoundError(code="RULE_NOT_FOUND", message=f"Alert rule '{rule_id}' not found.")

    if body.alert_type:
        rule.alert_type = AlertType(body.alert_type.upper())
    if body.minimum_severity:
        rule.minimum_severity = AlertSeverity(body.minimum_severity.upper())
    if body.enabled is not None:
        rule.enabled = body.enabled

    try:
        updated = watchlist_service.update_alert_rule(
            rule, tenant_id=current_user.tenant_id, user_id=current_user.user_id
        )
    except PermissionError as e:
        raise ForbiddenError(code="ACCESS_DENIED", message=str(e))

    return AlertRuleResponse(
        alert_rule_id=updated.alert_rule_id,
        user_id=updated.user_id,
        tenant_id=updated.tenant_id,
        watchlist_id=updated.watchlist_id,
        alert_type=updated.alert_type.value if hasattr(updated.alert_type, "value") else str(updated.alert_type),
        minimum_severity=updated.minimum_severity.value if hasattr(updated.minimum_severity, "value") else str(updated.minimum_severity),
        enabled=updated.enabled,
        created_at=updated.created_at,
    )


@router.delete(
    "/{watchlist_id}/rules/{rule_id}",
    response_model=SuccessStatusResponse,
    summary="Delete an alert rule",
    description="Remove an alert rule from the watchlist.",
)
def delete_watchlist_rule(
    watchlist_id: str,
    rule_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> SuccessStatusResponse:
    rule = watchlist_service.get_alert_rule(
        rule_id, tenant_id=current_user.tenant_id, user_id=current_user.user_id
    )
    if not rule or rule.watchlist_id != watchlist_id:
        raise NotFoundError(code="RULE_NOT_FOUND", message=f"Alert rule '{rule_id}' not found.")

    deleted = watchlist_service.alert_rule_repo.delete(
        rule_id, tenant_id=current_user.tenant_id, user_id=current_user.user_id
    )
    if not deleted:
        raise NotFoundError(code="RULE_NOT_FOUND", message=f"Alert rule '{rule_id}' could not be deleted.")

    return SuccessStatusResponse(success=True, message="Alert rule deleted.")
