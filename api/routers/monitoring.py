"""
api/routers/monitoring.py
=========================
REST API router for Legislative Monitoring operations, runs, and change feeds.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    get_monitoring_repository,
    get_monitoring_runner,
)
from api.schemas import (
    MonitoringCheckResponse,
    MonitoringEventResponse,
    MonitoringRunResponse,
    MonitoringStatusResponse,
)
from services.monitoring.monitoring_runner import MonitoringRunner
from storage.monitoring_repository import MonitoringRepository

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get(
    "/status",
    response_model=MonitoringStatusResponse,
    summary="Get legislative monitoring health status",
    description="Operational status of parliamentary and assembly scrapers, enabled sources, and last check timestamp.",
)
def get_monitoring_status(
    monitoring_runner: MonitoringRunner = Depends(get_monitoring_runner),
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> MonitoringStatusResponse:
    registry = monitoring_runner._registry
    enabled = registry.get_enabled()
    all_sources = registry.get_all()
    runs = monitoring_repo.list_runs(limit=1)
    last_run = runs[0] if runs else None

    summary_items = [
        {
            "source_id": s.source_id,
            "name": getattr(s, "source_name", getattr(s, "name", s.source_id)),
            "jurisdiction": s.jurisdiction,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "last_checked_at": s.last_checked_at,
            "last_success_at": s.last_success_at,
            "error_count": getattr(s, "error_count", (1 if s.last_error else 0)),
        }
        for s in all_sources
    ]

    return MonitoringStatusResponse(
        system_status="OPERATIONAL",
        total_sources=len(all_sources),
        enabled_sources=len(enabled),
        last_run_id=last_run.run_id if last_run else None,
        last_run_timestamp=last_run.start_time if last_run else None,
        sources_summary=summary_items,
    )


@router.get(
    "/runs",
    response_model=list[MonitoringRunResponse],
    summary="List past monitoring runs",
    description="Retrieve historical scraper execution runs and change detection statistics.",
)
def list_monitoring_runs(
    limit: int = Query(20, ge=1, le=100, description="Max runs to return"),
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> list[MonitoringRunResponse]:
    runs = monitoring_repo.list_runs(limit=limit)
    return [
        MonitoringRunResponse(
            run_id=r.run_id,
            trigger=r.trigger,
            start_time=r.start_time,
            end_time=r.end_time,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            sources_checked=r.sources_checked,
            sources_succeeded=r.sources_succeeded,
            sources_failed=r.sources_failed,
            changes_detected=len(r.changes_detected),
            error_summary=None,
        )
        for r in runs
    ]


@router.get(
    "/events",
    response_model=list[MonitoringEventResponse],
    summary="List legislative change events",
    description="Feed of authoritative legislative change events (new introductions, status changes) detected by monitors.",
)
def list_monitoring_events(
    limit: int = Query(50, ge=1, le=100, description="Max events to return"),
    bill_id: Optional[str] = Query(None, description="Filter by bill ID"),
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> list[MonitoringEventResponse]:
    events = monitoring_repo.list_events(bill_id=bill_id, limit=limit)
    return [
        MonitoringEventResponse(
            event_id=e.event_id,
            event_type=e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
            bill_id=e.bill_id,
            bill_title=e.bill_title,
            jurisdiction=e.jurisdiction,
            state=e.state,
            detected_at=e.detected_at,
            description=e.description,
            severity=e.severity.value if hasattr(e.severity, "value") else str(e.severity),
        )
        for e in events
    ]


@router.post(
    "/check",
    response_model=MonitoringCheckResponse,
    summary="Safe manual monitoring poll",
    description="Trigger a safe, controlled poll across enabled legislative sources without filesystem or shell execution risks.",
)
def trigger_manual_check(
    monitoring_runner: MonitoringRunner = Depends(get_monitoring_runner),
) -> MonitoringCheckResponse:
    res = monitoring_runner.run_once(trigger="manual_api")
    return MonitoringCheckResponse(
        run_id=res["run_id"],
        status=res["status"],
        trigger=res["trigger"],
        sources_checked=res["sources_checked"],
        sources_succeeded=res["sources_succeeded"],
        sources_failed=res["sources_failed"],
        changes_detected=res["changes_detected"],
    )
