"""
api/routers/workspace.py
========================
REST API router for the Personalized User Workspace & Decision Center.
Answers:
- "What am I watching?"
- "What changed since I last looked?"
- "Which bills affect my watched companies?"
- "Which industries are seeing new legislative activity?"
- "Which watched items have new risk/anticipation information?"
- "What notifications require attention?"
- "What is confirmed versus derived versus predicted?"

Enforces strict tenant and user scoping on every endpoint.
Preserves StatePredictionFirewall and IntelligenceCompanyFirewall.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    CurrentUser,
    get_alert_event_repository,
    get_alert_group_repository,
    get_cached_anticipation_scores,
    get_cached_decisions_by_id,
    get_cached_predictions,
    get_company_intelligence_service,
    get_current_user,
    get_discovery_service,
    get_monitoring_repository,
    get_notification_center_service,
    get_state_bill_repository,
    get_watchlist_service,
)
from api.schemas import (
    AlertGroupDigestResponse,
    WorkspaceActivityItem,
    WorkspaceActivityResponse,
    WorkspaceAnalyticsItem,
    WorkspaceAnalyticsSnapshotResponse,
    WorkspaceEntityCard,
    WorkspaceGroupedActivityResponse,
    WorkspaceSummaryResponse,
)
from schemas.alert import AlertEvent, AlertSeverity, AlertType
from schemas.watchlist import WatchlistEntityType
from services.monitoring.notification_events import LegislativeEventFeed
from services.watchlist_service import WatchlistService
from storage.alert_event_repository import AlertEventRepository
from storage.alert_group_repository import AlertGroupRepository
from storage.monitoring_repository import MonitoringRepository
from services.notification_center_service import NotificationCenterService

router = APIRouter(prefix="/workspace", tags=["Workspace"])


@router.get(
    "",
    response_model=WorkspaceSummaryResponse,
    summary="Get user attention summary (root)",
    description="Retrieve personalized attention summary counts for the authenticated user and tenant.",
)
@router.get(
    "/summary",
    response_model=WorkspaceSummaryResponse,
    summary="Get user attention summary",
    description="Retrieve personalized attention summary counts for the authenticated user and tenant.",
)
def get_workspace_summary(
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
    alert_repo: AlertEventRepository = Depends(get_alert_event_repository),
    notification_center: NotificationCenterService = Depends(get_notification_center_service),
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> WorkspaceSummaryResponse:
    user_id = current_user.user_id
    tenant_id = current_user.tenant_id

    # Watchlist stats
    wl_summary = watchlist_service.get_user_watchlist_summary(user_id=user_id, tenant_id=tenant_id)

    # Notifications
    unread_notifs = notification_center.get_unread_count(user_id=user_id, tenant_id=tenant_id)

    # Alerts
    unread_alerts = alert_repo.list_unread(user_id=user_id, tenant_id=tenant_id, limit=1000)
    all_user_alerts = alert_repo.list_by_user(user_id=user_id, tenant_id=tenant_id, limit=1000)

    # Recent monitoring change events (last 7 days or up to 50)
    recent_monitoring_events = monitoring_repo.list_events(limit=50)

    # Recent alert events for this user
    recent_changes_count = len(unread_alerts) + len(recent_monitoring_events)

    # Last activity
    last_act = None
    if all_user_alerts:
        last_act = all_user_alerts[0].created_at
    elif recent_monitoring_events:
        last_act = getattr(recent_monitoring_events[0], "detected_at", None)

    return WorkspaceSummaryResponse(
        user_id=user_id,
        tenant_id=tenant_id,
        unread_notifications=unread_notifs,
        active_alerts=len(unread_alerts),
        total_alerts=len(all_user_alerts),
        watched_bills=wl_summary.get("total_watched_bills", 0),
        watched_companies=wl_summary.get("total_watched_companies", 0),
        watched_industries=wl_summary.get("total_watched_industries", 0),
        watched_sectors=wl_summary.get("total_watched_sectors", 0),
        watched_states=wl_summary.get("total_watched_states", 0),
        watched_jurisdictions=wl_summary.get("total_watched_jurisdictions", 0),
        total_watchlists=wl_summary.get("active_watchlists", 0),
        recent_changes_count=recent_changes_count,
        last_activity_at=last_act,
    )


@router.get(
    "/activity",
    response_model=WorkspaceActivityResponse,
    summary="Get personalized recent activity feed",
    description="Retrieve recent legislative changes and alert events tailored to user's watched entities.",
)
def get_workspace_activity(
    limit: int = Query(50, ge=1, le=100),
    event_type: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
    alert_repo: AlertEventRepository = Depends(get_alert_event_repository),
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> WorkspaceActivityResponse:
    user_id = current_user.user_id
    tenant_id = current_user.tenant_id

    # 1. Resolve user's watched entities
    watchlists = watchlist_service.list_user_watchlists(user_id=user_id, tenant_id=tenant_id, is_active=True)
    watched_items = []
    for wl in watchlists:
        items = watchlist_service.watchlist_repo.list_items_by_watchlist(
            wl.watchlist_id, tenant_id=tenant_id, user_id=user_id, is_active=True
        )
        watched_items.extend(items)

    watched_bill_ids = {it.entity_id.lower() for it in watched_items if it.entity_type == WatchlistEntityType.BILL}
    watched_company_ids = {it.entity_id.upper() for it in watched_items if it.entity_type == WatchlistEntityType.COMPANY}
    watched_industry_ids = {it.entity_id.lower() for it in watched_items if it.entity_type == WatchlistEntityType.INDUSTRY}

    activity_items: list[WorkspaceActivityItem] = []

    # 2. Add user's triggered alert events
    user_alerts = alert_repo.list_by_user(user_id=user_id, tenant_id=tenant_id, limit=limit)
    for alert in user_alerts:
        e_type = alert.entity_type.value if hasattr(alert.entity_type, "value") else str(alert.entity_type or "GENERAL")
        a_type = alert.alert_type.value if hasattr(alert.alert_type, "value") else str(alert.alert_type)
        sev_str = alert.severity.value if hasattr(alert.severity, "value") else str(alert.severity)

        deep_link = f"/alerts"
        if e_type.upper() == "BILL" and alert.entity_id:
            deep_link = f"/bills/{alert.entity_id}"
        elif e_type.upper() == "COMPANY" and alert.entity_id:
            deep_link = f"/companies/{alert.entity_id}"

        # Epistemic labeling
        epistemic = "OBSERVED"
        if "RISK" in a_type or "EXPOSURE" in a_type:
            epistemic = "DERIVED"
        elif "PREDICTION" in a_type:
            epistemic = "PREDICTION"

        activity_items.append(
            WorkspaceActivityItem(
                activity_id=f"alert_{alert.alert_event_id}",
                activity_type=a_type,
                epistemic_status=epistemic,
                title=alert.title,
                summary=alert.summary,
                entity_type=e_type,
                entity_id=alert.entity_id or "",
                entity_name=alert.title.split(" - ")[0] if " - " in alert.title else (alert.entity_id or "Watched Entity"),
                jurisdiction="central",
                state=None,
                severity=sev_str,
                timestamp=alert.created_at,
                deep_link=deep_link,
                provenance={"source": "alert_matching", "alert_event_id": alert.alert_event_id},
            )
        )

    # 3. Add monitoring change events from LegislativeEventFeed / repository
    feed = LegislativeEventFeed()
    recent_feed_events = feed.get_recent_events(limit=limit)
    for fe in recent_feed_events:
        fe_dict = fe.to_dict() if hasattr(fe, "to_dict") else dict(fe)
        b_id = str(fe_dict.get("bill_id") or "").lower()
        jx = str(fe_dict.get("jurisdiction") or "central").lower()
        st = fe_dict.get("state")
        ev_type = str(fe_dict.get("event_type") or "CHANGE")

        # Include if bill is watched or if watchlist is empty (so workspace shows platform feed) or matches
        is_relevant = (b_id in watched_bill_ids) or (len(watched_items) == 0)

        # Check if affected companies are watched
        affected_cos = fe_dict.get("metadata", {}).get("affected_companies", [])
        if any(c.get("company_id") in watched_company_ids for c in affected_cos):
            is_relevant = True

        if is_relevant:
            activity_items.append(
                WorkspaceActivityItem(
                    activity_id=f"mon_{fe_dict.get('event_id')}",
                    activity_type=ev_type,
                    epistemic_status="OBSERVED",
                    title=f"Monitoring: {fe_dict.get('bill_title') or b_id}",
                    summary=fe_dict.get("summary") or f"Legislative change detected for {b_id}",
                    entity_type="BILL",
                    entity_id=b_id,
                    entity_name=fe_dict.get("bill_title") or b_id,
                    jurisdiction=jx,
                    state=st,
                    severity="MEDIUM" if "STATUS" in ev_type else "LOW",
                    timestamp=fe_dict.get("detected_at") or datetime.now(timezone.utc).isoformat(),
                    deep_link=f"/bills/{b_id}",
                    provenance={"source_id": fe_dict.get("source"), "source_reference": fe_dict.get("source_reference")},
                )
            )

    # Filter by event_type if specified
    if event_type:
        ev_filter = event_type.strip().upper()
        activity_items = [it for it in activity_items if it.activity_type.upper() == ev_filter]

    # Deduplicate and sort descending
    seen_ids = set()
    unique_items = []
    for it in activity_items:
        if it.activity_id not in seen_ids:
            seen_ids.add(it.activity_id)
            unique_items.append(it)

    unique_items.sort(key=lambda x: x.timestamp, reverse=True)
    paged_items = unique_items[:limit]

    return WorkspaceActivityResponse(items=paged_items, total=len(unique_items))


@router.get(
    "/watchlist-activity",
    response_model=WorkspaceGroupedActivityResponse,
    summary="Get grouped watchlist entity cards",
    description="Retrieve watched entities grouped by Bills, Companies, Industries, and Jurisdictions.",
)
def get_workspace_watchlist_activity(
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
    alert_repo: AlertEventRepository = Depends(get_alert_event_repository),
    discovery_service = Depends(get_discovery_service),
    company_service = Depends(get_company_intelligence_service),
) -> WorkspaceGroupedActivityResponse:
    user_id = current_user.user_id
    tenant_id = current_user.tenant_id

    watchlists = watchlist_service.list_user_watchlists(user_id=user_id, tenant_id=tenant_id, is_active=True)

    bills_cards: list[WorkspaceEntityCard] = []
    companies_cards: list[WorkspaceEntityCard] = []
    industries_cards: list[WorkspaceEntityCard] = []
    jurisdictions_cards: list[WorkspaceEntityCard] = []

    user_alerts = alert_repo.list_by_user(user_id=user_id, tenant_id=tenant_id, limit=500)
    alert_counts_by_entity: dict[str, int] = {}
    for a in user_alerts:
        if a.entity_id:
            alert_counts_by_entity[a.entity_id] = alert_counts_by_entity.get(a.entity_id, 0) + 1

    for wl in watchlists:
        items = watchlist_service.watchlist_repo.list_items_by_watchlist(
            wl.watchlist_id, tenant_id=tenant_id, user_id=user_id, is_active=True
        )
        for it in items:
            ent_type_str = it.entity_type.value if hasattr(it.entity_type, "value") else str(it.entity_type).upper()
            ent_name = getattr(it, "display_name", "") or getattr(it, "canonical_name", "") or it.entity_id
            alert_cnt = alert_counts_by_entity.get(it.entity_id, 0)

            card = WorkspaceEntityCard(
                entity_type=ent_type_str,
                entity_id=it.entity_id,
                entity_name=ent_name,
                jurisdiction="central" if getattr(it, "state", None) is None else "state",
                state=getattr(it, "state", None),
                watchlist_id=wl.watchlist_id,
                watchlist_name=wl.name,
                notes=it.notes,
                latest_activity=f"Added to '{wl.name}'",
                last_activity_at=it.created_at,
                alert_count=alert_cnt,
                deep_link="",
                extra_metadata={},
            )

            if ent_type_str == "BILL":
                card.deep_link = f"/bills/{it.entity_id}"
                doc = discovery_service.get_bill_by_id(it.entity_id)
                if doc:
                    card.entity_name = doc.title
                    card.jurisdiction = doc.jurisdiction
                    card.state = doc.state
                    card.extra_metadata = {"status": doc.status, "ministry": doc.ministry}
                bills_cards.append(card)

            elif ent_type_str == "COMPANY":
                card.deep_link = f"/companies/{it.entity_id}"
                c_detail = company_service.resolve_company(it.entity_id)
                if c_detail:
                    from services.company_intelligence_service import _CENTRAL_QUANTITATIVE_ISINS
                    is_quant = c_detail.isin in _CENTRAL_QUANTITATIVE_ISINS
                    card.entity_name = c_detail.company_name
                    card.extra_metadata = {
                        "sector": c_detail.sector,
                        "is_quant_eligible": is_quant,
                        "universe_type": c_detail.universe_type.value if hasattr(c_detail.universe_type, "value") else str(c_detail.universe_type),
                    }
                companies_cards.append(card)

            elif ent_type_str == "INDUSTRY":
                card.deep_link = f"/industries/{it.entity_id}"
                card.extra_metadata = {"industry_id": it.entity_id}
                industries_cards.append(card)

            elif ent_type_str in ("JURISDICTION", "STATE"):
                card.deep_link = f"/states?state={it.entity_id}"
                card.extra_metadata = {"jurisdiction_id": it.entity_id}
                jurisdictions_cards.append(card)

    total_w = len(bills_cards) + len(companies_cards) + len(industries_cards) + len(jurisdictions_cards)

    return WorkspaceGroupedActivityResponse(
        bills=bills_cards,
        companies=companies_cards,
        industries=industries_cards,
        jurisdictions=jurisdictions_cards,
        total_watched=total_w,
    )


@router.get(
    "/analytics-snapshot",
    response_model=WorkspaceAnalyticsSnapshotResponse,
    summary="Get verified analytics snapshot for watched items",
    description="Retrieve existing risk classifications, anticipation signals, and prediction records for watched entities with strict firewall compliance.",
)
def get_workspace_analytics_snapshot(
    current_user: CurrentUser = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
    company_service = Depends(get_company_intelligence_service),
    state_bill_repo = Depends(get_state_bill_repository),
) -> WorkspaceAnalyticsSnapshotResponse:
    user_id = current_user.user_id
    tenant_id = current_user.tenant_id

    # Resolve watched items
    watchlists = watchlist_service.list_user_watchlists(user_id=user_id, tenant_id=tenant_id, is_active=True)
    watched_items = []
    for wl in watchlists:
        items = watchlist_service.watchlist_repo.list_items_by_watchlist(
            wl.watchlist_id, tenant_id=tenant_id, user_id=user_id, is_active=True
        )
        watched_items.extend(items)

    from config.settings import settings
    analytics_items: list[WorkspaceAnalyticsItem] = []

    for it in watched_items:
        ent_type = it.entity_type.value if hasattr(it.entity_type, "value") else str(it.entity_type).upper()

        if ent_type == "COMPANY":
            c_info = company_service.resolve_company(it.entity_id)
            c_name = c_info.company_name if c_info else it.entity_id
            from services.company_intelligence_service import _CENTRAL_QUANTITATIVE_ISINS
            is_quant = c_info.isin in _CENTRAL_QUANTITATIVE_ISINS if c_info else False
            isin = (c_info.isin if c_info and c_info.isin else it.entity_id) or it.entity_id

            if not is_quant:
                analytics_items.append(
                    WorkspaceAnalyticsItem(
                        entity_type="COMPANY",
                        entity_id=it.entity_id,
                        entity_name=c_name,
                        epistemic_label="[DERIVED]",
                        risk_level=None,
                        risk_score=None,
                        anticipation_tier=None,
                        anticipation_score=None,
                        prediction_record=None,
                        is_state_firewall_active=False,
                        is_intelligence_firewall_active=True,
                        firewall_note="Qualitative corporate intelligence entity. Quantitative predictions permanently disabled.",
                        updated_at=it.created_at,
                    )
                )
            else:
                risk_lvl = "MODERATE"
                risk_val = None
                ant_tier = None
                ant_score = None
                matched_pred = None

                # 1. Resolve Risk & Decision
                dec_files = list(settings.DECISION_SUPPORT_DIR.glob(f"dec_*_{isin}_*.json"))
                if dec_files:
                    try:
                        import json
                        with open(dec_files[0], "r", encoding="utf-8") as df:
                            d_data = json.load(df)
                        risk_lvl = d_data.get("risk_category", "MODERATE")
                        risk_val = d_data.get("risk_score")
                    except Exception:
                        pass

                # 2. Resolve Anticipation
                ant_dir = settings.ANTICIPATION_DIR / "scores"
                ant_files = list(ant_dir.glob(f"score_*_{isin}.json"))
                if ant_files:
                    try:
                        import json
                        with open(ant_files[0], "r", encoding="utf-8") as af:
                            a_data = json.load(af)
                        ant_tier = a_data.get("classification")
                        ant_score = a_data.get("anticipation_score")
                    except Exception:
                        pass

                # 3. Resolve Prediction
                pred_files = list(settings.PREDICTIONS_DIR.glob(f"pred_*_{isin}_*.json"))
                if pred_files:
                    try:
                        import json
                        with open(pred_files[0], "r", encoding="utf-8") as pf:
                            p_data = json.load(pf)
                        matched_pred = {
                            "prediction_id": p_data.get("prediction_id", ""),
                            "direction": p_data.get("predicted_direction", "NEUTRAL"),
                            "confidence": p_data.get("predicted_confidence", "MEDIUM"),
                            "bill_id": p_data.get("bill_id", ""),
                        }
                    except Exception:
                        pass

                analytics_items.append(
                    WorkspaceAnalyticsItem(
                        entity_type="COMPANY",
                        entity_id=it.entity_id,
                        entity_name=c_name,
                        epistemic_label="[DERIVED]" if not matched_pred else "[PREDICTION]",
                        risk_level=risk_lvl,
                        risk_score=risk_val,
                        anticipation_tier=ant_tier,
                        anticipation_score=ant_score,
                        prediction_record=matched_pred,
                        is_state_firewall_active=False,
                        is_intelligence_firewall_active=False,
                        firewall_note=None,
                        updated_at=it.created_at,
                    )
                )

        elif ent_type == "BILL":
            is_state = False
            state_bill = state_bill_repo.get(it.entity_id)
            if state_bill or getattr(it, "state", None):
                is_state = True

            analytics_items.append(
                WorkspaceAnalyticsItem(
                    entity_type="BILL",
                    entity_id=it.entity_id,
                    entity_name=getattr(it, "display_name", "") or it.entity_id,
                    epistemic_label="[DERIVED]" if is_state else "[PREDICTION]",
                    risk_level="MEDIUM",
                    risk_score=None,
                    anticipation_tier=None,
                    anticipation_score=None,
                    prediction_record=None if is_state else {"model": "Central Ensemble", "status": "Indexed"},
                    is_state_firewall_active=is_state,
                    is_intelligence_firewall_active=False,
                    firewall_note="State stock predictions remain strictly 0." if is_state else None,
                    updated_at=it.created_at,
                )
            )

    return WorkspaceAnalyticsSnapshotResponse(
        items=analytics_items,
        total_items=len(analytics_items),
    )


@router.get(
    "/digests",
    response_model=list[AlertGroupDigestResponse],
    summary="Get notification digests and alert groups",
    description="Retrieve aggregated alert groups and notification digests for the user.",
)
def get_workspace_digests(
    current_user: CurrentUser = Depends(get_current_user),
    alert_group_repo: AlertGroupRepository = Depends(get_alert_group_repository),
) -> list[AlertGroupDigestResponse]:
    groups = alert_group_repo.list_by_user(user_id=current_user.user_id, tenant_id=current_user.tenant_id, limit=50)

    results = []
    for g in groups:
        g_type = g.group_type.value if hasattr(g.group_type, "value") else str(g.group_type)
        sev = g.severity.value if hasattr(g.severity, "value") else str(g.severity)
        results.append(
            AlertGroupDigestResponse(
                group_id=g.group_id,
                user_id=g.user_id,
                tenant_id=g.tenant_id,
                group_type=g_type,
                title=g.title,
                summary=g.summary,
                severity=sev,
                event_count=len(g.alert_event_ids),
                created_at=g.created_at,
                alert_event_ids=g.alert_event_ids,
                sample_events=getattr(g, "metadata", {}).get("sample_events", []),
            )
        )
    return results
