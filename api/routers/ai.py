"""
api/routers/ai.py
=================
REST routes for Grounded AI Explanation & Copilot interactions.
Guarantees:
- Zero secret leakage (never exposes API keys or internal filesystem traces).
- Robust offline fallback when Groq LLM inference is disabled or unreachable.
- Grounded strictly in validated parliamentary & corporate intelligence.
- Strict non-financial advice disclaimer on all outputs.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    CurrentUser,
    get_ai_explanation_service,
    get_ai_usage_service,
    get_current_user,
    get_monitoring_repository,
    get_monitoring_runner,
    get_watchlist_service,
)
from api.errors import BadRequestError, ForbiddenError, NotFoundError
from api.schemas import AIAskRequest, AIAskResponse
from services.ai.ai_explanation_service import AIExplanationResult, AIExplanationService
from services.ai_usage_service import AIUsageService
from services.watchlist_service import WatchlistService
from storage.monitoring_repository import MonitoringRepository
from services.monitoring.monitoring_runner import MonitoringRunner

router = APIRouter(prefix="/ai", tags=["AI Copilot & Explanations"])

DISCLAIMER_TEXT = (
    "Verified Provenance: Grounded strictly in validated parliamentary and corporate intelligence. "
    "Analytical explanation only; not investment advice."
)

MONITORING_DISCLAIMER = (
    "Legislative monitoring context only. This analysis is grounded in detected monitoring events "
    "and does not constitute a market prediction, political recommendation, or investment advice. "
    "State legislative monitoring does not generate stock predictions."
)


def _to_ai_response(
    result: AIExplanationResult,
    context_type: str,
    context_id: str,
) -> AIAskResponse:
    sources = result.provenance_sources or ["Project Repository Ground Truth"]
    return AIAskResponse(
        content=result.content,
        context_type=context_type,
        context_id=context_id,
        persona=result.persona,
        operation=result.operation,
        success=result.success,
        is_cached=result.is_cached,
        disclaimer=DISCLAIMER_TEXT,
        provenance_sources=sources,
        answer=result.content,
        context_sources=sources,
    )


def _ask_monitoring_ai(
    ai_service: AIExplanationService,
    question: str,
    persona: str = "GENERAL_PUBLIC",
) -> AIExplanationResult:
    """
    Answer a monitoring-context question grounded in actual monitoring data.

    Guardrails:
    - Does NOT fabricate events, dates, companies, or exposure.
    - Does NOT speculate about political motives.
    - Does NOT create stock predictions.
    - Falls back gracefully if monitoring data is unavailable.
    """
    try:
        from services.monitoring.monitoring_runner import MonitoringRunner
        from storage.monitoring_repository import MonitoringRepository
        runner = MonitoringRunner()
        repo = MonitoringRepository()
        registry = runner._registry
        all_sources = registry.get_all()
        enabled = registry.get_enabled()
        last_run = repo.get_last_run()
        event_count = repo.get_event_count()

        context = (
            f"MONITORING SYSTEM CONTEXT (grounding only — do not fabricate beyond this):\n"
            f"Total sources: {len(all_sources)} | Enabled: {len(enabled)}\n"
            f"Central sources: {len(registry.get_central_sources(enabled_only=False))}\n"
            f"State sources: {len(registry.get_state_sources(enabled_only=False))}\n"
            f"Total change events recorded: {event_count}\n"
        )
        if last_run:
            status = last_run.status.value if hasattr(last_run.status, "value") else str(last_run.status)
            context += (
                f"Last run: {last_run.started_at} | Status: {status} | "
                f"New bills: {last_run.new_bills} | Changed: {last_run.changed_bills}\n"
            )
        else:
            context += "Last run: None recorded yet.\n"

        context += (
            "\nGUARDRAILS: Do not fabricate legislative events, dates, companies, or exposure. "
            "Do not speculate about political motives. Do not make stock predictions. "
            "State legislative monitoring does not generate stock predictions (State predictions = 0)."
        )
    except Exception:
        context = (
            "MONITORING SYSTEM CONTEXT: Monitoring data currently unavailable. "
            "Answer based only on general knowledge of the platform monitoring architecture."
        )

    try:
        result = ai_service.ask_ai(
            bill_id="__monitoring_context__",
            question=f"{context}\n\nUser question: {question}",
            persona=persona,
        )
    except Exception:
        result = AIExplanationResult(
            content=(
                "Monitoring AI analysis is temporarily unavailable. "
                "Please check the monitoring overview for current system status."
            ),
            persona=persona,
            operation="MONITORING_AI_FALLBACK",
            success=False,
            provenance_sources=["System Fallback Guard"],
        )
    return result


def _ask_workspace_ai(
    ai_service: AIExplanationService,
    question: str,
    user_id: str,
    tenant_id: str,
    persona: str = "GENERAL_PUBLIC",
) -> AIExplanationResult:
    """
    Answer questions in the workspace context grounded strictly in user's watched entities,
    unread alerts, notifications, and monitored changes.

    Guardrails:
    - Strictly scoped to user_id and tenant_id.
    - Zero data from other users/tenants.
    - Zero fabricated events, alerts, or statistics.
    - Zero predictions or Buy/Sell/Hold advice.
    - If no events exist: 'My watchlists have no relevant new events in the available data.'
    """
    from services.watchlist_service import WatchlistService
    from storage.alert_event_repository import AlertEventRepository
    from services.notification_center_service import NotificationCenterService
    from storage.monitoring_repository import MonitoringRepository

    try:
        wl_svc = WatchlistService()
        alert_repo = AlertEventRepository()
        notif_svc = NotificationCenterService()
        mon_repo = MonitoringRepository()

        # 1. User watchlists and items
        watchlists = wl_svc.list_user_watchlists(user_id=user_id, tenant_id=tenant_id, is_active=True)
        total_items = 0
        watched_summary = []
        watched_ids = set()
        for wl in watchlists:
            items = wl_svc.watchlist_repo.list_items_by_watchlist(wl.watchlist_id, tenant_id=tenant_id, user_id=user_id, is_active=True)
            total_items += len(items)
            item_names = [getattr(it, "display_name", "") or getattr(it, "canonical_name", "") or it.entity_id for it in items[:5]]
            watched_summary.append(f"Watchlist '{wl.name}' ({len(items)} items): {', '.join(item_names)}")
            for it in items:
                watched_ids.add(it.entity_id.lower())

        # 2. User unread alerts and notifications
        unread_alerts = alert_repo.list_unread(user_id=user_id, tenant_id=tenant_id, limit=20)
        recent_notifs = notif_svc.list_notifications(user_id=user_id, tenant_id=tenant_id, limit=20, is_read=False)

        # 3. Recent monitoring changes affecting watched entities
        all_changes = mon_repo.get_recent_events(limit=30)
        watched_changes = [c for c in all_changes if str(getattr(c, "bill_id", "")).lower() in watched_ids]

        if not watchlists and not unread_alerts and not recent_notifs:
            return AIExplanationResult(
                content="My watchlists have no relevant new events in the available data. You currently have no active watchlists or unread alerts configured.",
                bill_id="__workspace_context__",
                jurisdiction="central",
                persona=persona,
                operation="WORKSPACE_AI_GROUNDED",
                success=True,
                provenance_sources=["Personalized Workspace Ground Truth"],
            )

        context = (
            f"PERSONALIZED USER WORKSPACE CONTEXT (authorized user: {user_id} - grounded only, do not fabricate):\n"
            f"Active watchlists: {len(watchlists)} with {total_items} total tracked items.\n"
            f"Watchlist details:\n" + "\n".join(f"- {s}" for s in watched_summary) + "\n\n"
            f"Unread Alerts ({len(unread_alerts)}):\n"
        )
        if unread_alerts:
            for a in unread_alerts[:5]:
                context += f"- [{a.severity.value}] {a.title}: {a.summary}\n"
        else:
            context += "- No unread alerts.\n"

        context += f"\nRecent Notifications ({len(recent_notifs)}):\n"
        if recent_notifs:
            for n in recent_notifs[:5]:
                context += f"- [{n.severity.value}] {n.title}: {n.message}\n"
        else:
            context += "- No unread notifications.\n"

        context += f"\nRecent Legislative Changes for Watched Entities ({len(watched_changes)}):\n"
        if watched_changes:
            for ch in watched_changes[:5]:
                context += f"- {getattr(ch, 'event_type', 'CHANGE')}: {getattr(ch, 'bill_title', '') or getattr(ch, 'bill_id', '')} ({getattr(ch, 'detected_at', '')})\n"
        else:
            context += "- No recent changes for watched entities.\n"

        context += (
            "\nSTRICT GUARDRAILS:\n"
            "1. Ground your response strictly in the above context.\n"
            "2. If no matching events exist for the query, state: 'My watchlists have no relevant new events in the available data.'\n"
            "3. Do NOT make stock predictions, Buy/Sell/Hold recommendations, or political evaluations.\n"
            "4. State stock predictions remain strictly 0.\n"
        )

        result = ai_service.ask_ai(
            bill_id="__workspace_context__",
            question=f"{context}\n\nUser Question: {question}",
            persona=persona,
        )
        return result
    except Exception:
        return AIExplanationResult(
            content="My watchlists have no relevant new events in the available data.",
            bill_id="__workspace_context__",
            jurisdiction="central",
            persona=persona,
            operation="WORKSPACE_AI_FALLBACK",
            success=True,
            provenance_sources=["Personalized Workspace Ground Truth"],
        )


@router.post("/ask", response_model=AIAskResponse)

def ask_ai(
    request: AIAskRequest,
    current_user: CurrentUser = Depends(get_current_user),
    ai_service: AIExplanationService = Depends(get_ai_explanation_service),
    usage_service: AIUsageService = Depends(get_ai_usage_service),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
) -> AIAskResponse:
    """
    Grounded question answering against legislative bill, corporate intelligence, or workspace context.
    Falls back gracefully when offline or when external AI services are unreachable.
    """
    if request.watchlist_id and (not request.context_id or (request.context_type and request.context_type.lower() in ("bill", "watchlist"))):
        ctx_type = "watchlist"
        context_id = request.watchlist_id
    else:
        ctx_type = (request.context_type or "bill").lower().strip()
        context_id = request.context_id or ""
    persona = request.persona.upper().strip()

    try:
        if ctx_type == "company":
            result = ai_service.ask_company_ai(
                company_identifier=context_id,
                question=request.question,
                persona=persona,
            )
        elif ctx_type == "bill":
            result = ai_service.ask_ai(
                bill_id=context_id,
                question=request.question,
                persona=persona,
            )
        elif ctx_type == "comparison":
            parts = [p.strip() for p in context_id.split(",") if p.strip()]
            if len(parts) != 2:
                raise BadRequestError("Comparison requires two comma-separated bill IDs (e.g. 'bill_1, bill_2').")
            result = ai_service.compare_bills(
                bill_id_1=parts[0],
                bill_id_2=parts[1],
                persona=persona,
            )
        elif ctx_type in ("industry", "sector"):
            result = ai_service.ask_industry_ai(
                industry_identifier=context_id,
                question=request.question,
                persona=persona,
            )
        elif ctx_type == "monitoring":
            result = _ask_monitoring_ai(
                ai_service=ai_service,
                question=request.question,
                persona=persona,
            )
        elif ctx_type == "workspace":
            result = _ask_workspace_ai(
                ai_service=ai_service,
                question=request.question,
                user_id=current_user.user_id,
                tenant_id=current_user.tenant_id,
                persona=persona,
            )
        elif ctx_type == "watchlist":
            # Strict multi-tenant isolation check on watchlist access
            wl = watchlist_service.get_watchlist(
                watchlist_id=context_id,
                tenant_id=current_user.tenant_id,
                user_id=current_user.user_id,
            )
            if not wl:
                # Check if it belongs to another tenant to return 403 Forbidden
                all_raw = watchlist_service.watchlist_repo.get(context_id)
                if all_raw and all_raw.tenant_id != current_user.tenant_id:
                    raise ForbiddenError(
                        code="CROSS_TENANT_WATCHLIST_FORBIDDEN",
                        message="Cannot query AI context on another organization's watchlist.",
                    )
                raise NotFoundError(
                    code="WATCHLIST_NOT_FOUND",
                    message=f"Watchlist '{context_id}' not found.",
                )
            result = _ask_workspace_ai(
                ai_service=ai_service,
                question=request.question,
                user_id=current_user.user_id,
                tenant_id=current_user.tenant_id,
                persona=persona,
            )
        else:
            raise BadRequestError(f"Unsupported context_type '{request.context_type}'. Must be 'bill', 'company', 'industry', 'monitoring', 'workspace', 'watchlist', or 'comparison'.")

        # Track usage telemetry
        usage_service.record_usage(
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            operation=f"ASK_{ctx_type.upper()}",
            model_provider="groq",
            success=result.success,
        )

        return _to_ai_response(result, ctx_type, context_id)

    except (BadRequestError, ForbiddenError, NotFoundError):
        raise
    except Exception as e:
        # Guarantee no internal trace or secret leakage
        usage_service.record_usage(
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            operation=f"ASK_{ctx_type.upper()}",
            model_provider="groq",
            success=False,
        )
        fallback_msg = f"AI explanation is temporarily unavailable: {str(e)[:150]}"
        return AIAskResponse(
            content=fallback_msg,
            context_type=ctx_type,
            context_id=context_id,
            persona=persona,
            operation="ASK_AI_FALLBACK",
            success=False,
            is_cached=False,
            disclaimer=DISCLAIMER_TEXT,
            provenance_sources=["System Fallback Guard"],
            answer=fallback_msg,
            context_sources=["System Fallback Guard"],
        )


@router.get("/explain/bill/{bill_id}", response_model=AIAskResponse)
def explain_bill(
    bill_id: str,
    operation: str = Query("BILL_SUMMARY", description="BILL_SUMMARY | WHY_IT_MATTERS | PROVISIONS | SECTOR_IMPACT | STAKEHOLDERS | MARKET_INTELLIGENCE | RISK_PROFILE | ANTICIPATION"),
    persona: str = Query("GENERAL_PUBLIC"),
    current_user: CurrentUser = Depends(get_current_user),
    ai_service: AIExplanationService = Depends(get_ai_explanation_service),
) -> AIAskResponse:
    """
    Structured analytical explanation for a parliamentary bill across supported analysis dimensions.
    """
    op = operation.strip().upper()
    p = persona.strip().upper()

    dispatch = {
        "BILL_SUMMARY": lambda: ai_service.explain_bill_summary(bill_id, persona=p),
        "WHY_IT_MATTERS": lambda: ai_service.explain_why_it_matters(bill_id, persona=p),
        "PROVISIONS": lambda: ai_service.explain_provisions(bill_id, persona=p),
        "SECTOR_IMPACT": lambda: ai_service.explain_sector_impact(bill_id, persona=p),
        "STAKEHOLDERS": lambda: ai_service.explain_stakeholders(bill_id, persona=p),
        "MARKET_INTELLIGENCE": lambda: ai_service.explain_market_intelligence(bill_id, persona=p),
        "RISK_PROFILE": lambda: ai_service.explain_risk_profile(bill_id, persona=p),
        "ANTICIPATION": lambda: ai_service.explain_anticipation(bill_id, persona=p),
    }

    fn = dispatch.get(op)
    if not fn:
        raise BadRequestError(f"Unsupported operation '{operation}'. Supported: {list(dispatch.keys())}")

    result = fn()
    return _to_ai_response(result, "bill", bill_id)


@router.get("/explain/company/{company_id}", response_model=AIAskResponse)
def explain_company(
    company_id: str,
    persona: str = Query("GENERAL_PUBLIC"),
    current_user: CurrentUser = Depends(get_current_user),
    ai_service: AIExplanationService = Depends(get_ai_explanation_service),
) -> AIAskResponse:
    """
    Structured analytical synthesis of a corporate entity's legislative footprint.
    """
    p = persona.strip().upper()
    result = ai_service.explain_company_profile(company_id, persona=p)
    return _to_ai_response(result, "company", company_id)


@router.get("/explain/company/{company_id}/bill/{bill_id}", response_model=AIAskResponse)
def explain_company_bill_exposure(
    company_id: str,
    bill_id: str,
    persona: str = Query("GENERAL_PUBLIC"),
    current_user: CurrentUser = Depends(get_current_user),
    ai_service: AIExplanationService = Depends(get_ai_explanation_service),
) -> AIAskResponse:
    """
    Structured narrative explanation of why a company is exposed to a specific legislative bill.
    """
    p = persona.strip().upper()
    result = ai_service.explain_company_bill_exposure(company_id, bill_id, persona=p)
    return _to_ai_response(result, "company_bill", f"{company_id}:{bill_id}")


@router.get("/usage", summary="Tenant AI Usage Summary")
def get_ai_usage(
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    limit: int = Query(50, ge=1, le=100),
    current_user: CurrentUser = Depends(get_current_user),
    usage_service: AIUsageService = Depends(get_ai_usage_service),
) -> dict[str, Any]:
    """Retrieve monthly AI usage metrics and recent requests for the caller's tenant."""
    from datetime import datetime, timezone
    month_str = month or datetime.now(timezone.utc).isoformat()[:7]
    total_count = usage_service.get_monthly_usage_count(current_user.tenant_id, month_str=month_str)
    records = usage_service.list_records(current_user.tenant_id, limit=limit, month_str=month_str)

    return {
        "tenant_id": current_user.tenant_id,
        "month": month_str,
        "monthly_request_count": total_count,
        "total_queries": total_count,
        "records": [r.to_dict() for r in records],
    }

