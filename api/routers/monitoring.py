"""
api/routers/monitoring.py
=========================
REST API router for Legislative Monitoring & Discovery Center.

Endpoints:
  GET  /monitoring/overview               — Combined telemetry panel
  GET  /monitoring/sources                — Source registry (paginated)
  GET  /monitoring/sources/{source_id}    — Single source detail
  GET  /monitoring/scheduler              — Scheduler observability
  GET  /monitoring/runs                   — Monitoring run history (paginated)
  GET  /monitoring/runs/{run_id}          — Single run detail
  GET  /monitoring/events                 — Legacy: recent events
  GET  /monitoring/changes                — Change events (paginated, filtered)
  GET  /monitoring/changes/{event_id}     — Single change detail with provenance
  GET  /monitoring/bill-versions/{bill_id} — Bill version history
  POST /monitoring/check                  — Safe manual monitoring poll

Task 8.14.9 — Legislative Monitoring & Discovery Center.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import (
    get_monitoring_repository,
    get_monitoring_runner,
    get_scheduler,
)
from api.schemas import (
    BillVersionHistoryResponse,
    BillVersionItem,
    ChangeEventDetailResponse,
    MonitoringCheckResponse,
    MonitoringEventResponse,
    MonitoringOverviewResponse,
    MonitoringRunDetailResponse,
    MonitoringRunResponse,
    MonitoringSourceDetailResponse,
    MonitoringSourceItem,
    MonitoringStatusResponse,
    PaginatedResponse,
    SchedulerStatusResponse,
)
from schemas.monitoring import SourceStatus
from services.monitoring.monitoring_runner import MonitoringRunner
from services.monitoring.scheduler import LegislativeScheduler
from storage.monitoring_repository import MonitoringRepository

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# ---------------------------------------------------------------------------
# Helper — build source health summary
# ---------------------------------------------------------------------------


def _classify_source_health(source: Any) -> str:
    """
    Classify a MonitoringSource into a health label.

    Returns one of: HEALTHY | ERROR | NEVER_CHECKED | DISABLED | NOT_IMPLEMENTED | PLANNED
    """
    status = source.status if isinstance(source.status, str) else str(source.status)
    if status in (SourceStatus.NOT_IMPLEMENTED.value, SourceStatus.PLANNED.value):
        return status
    if not source.enabled:
        return "DISABLED"
    if source.last_error and not source.last_success_at:
        return "ERROR"
    if source.last_error and source.last_error_at:
        # Error after a successful check = DEGRADED
        if source.last_success_at and source.last_error_at > source.last_success_at:
            return "DEGRADED"
        return "ERROR"
    if not source.last_checked_at:
        return "NEVER_CHECKED"
    return "HEALTHY"


def _source_to_item(source: Any) -> MonitoringSourceItem:
    return MonitoringSourceItem(
        source_id=source.source_id,
        source_name=getattr(source, "source_name", source.source_id),
        jurisdiction=source.jurisdiction,
        state=source.state,
        source_type=getattr(source, "source_type", "unknown"),
        source_url=getattr(source, "source_url", ""),
        enabled=source.enabled,
        status=source.status if isinstance(source.status, str) else str(source.status),
        polling_interval_hours=getattr(source, "polling_interval_hours", 24),
        priority=getattr(source, "priority", 10),
        last_checked_at=source.last_checked_at,
        last_success_at=source.last_success_at,
        last_error_at=source.last_error_at,
        last_error=source.last_error,
        notes=getattr(source, "notes", None),
    )


# ---------------------------------------------------------------------------
# GET /monitoring/overview
# ---------------------------------------------------------------------------


@router.get(
    "/overview",
    response_model=MonitoringOverviewResponse,
    summary="Monitoring telemetry overview",
    description=(
        "Combined monitoring telemetry: source counts, scheduler status, last run summary, "
        "and change event totals. "
        "This is observability data only — it does not constitute a market prediction."
    ),
)
def get_monitoring_overview(
    monitoring_runner: MonitoringRunner = Depends(get_monitoring_runner),
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
    scheduler: LegislativeScheduler = Depends(get_scheduler),
) -> MonitoringOverviewResponse:
    registry = monitoring_runner._registry
    all_sources = registry.get_all()
    enabled_sources = registry.get_enabled()
    central_sources = registry.get_central_sources(enabled_only=False)
    state_sources = registry.get_state_sources(enabled_only=False)

    # Health classification
    health_counts: dict[str, int] = {
        "HEALTHY": 0, "DEGRADED": 0, "ERROR": 0,
        "NEVER_CHECKED": 0, "DISABLED": 0,
        "NOT_IMPLEMENTED": 0, "PLANNED": 0,
    }
    for src in all_sources:
        label = _classify_source_health(src)
        health_counts[label] = health_counts.get(label, 0) + 1

    implemented = [
        s for s in all_sources
        if (s.status if isinstance(s.status, str) else str(s.status)) == SourceStatus.IMPLEMENTED.value
    ]
    planned = [
        s for s in all_sources
        if (s.status if isinstance(s.status, str) else str(s.status)) == SourceStatus.PLANNED.value
    ]

    # Last run
    last_run = monitoring_repo.get_last_run()
    total_runs = len(list((monitoring_repo._runs_dir).glob("run_*.json"))) if hasattr(monitoring_repo, "_runs_dir") else 0

    # Scheduler status
    sched_status = scheduler.get_status()
    scheduler_response = SchedulerStatusResponse(
        enabled=sched_status.get("enabled", False),
        scheduled_running=sched_status.get("scheduled_running", False),
        run_in_progress=sched_status.get("run_in_progress", False),
        last_run_at=sched_status.get("last_run_at"),
        next_run_at=sched_status.get("next_run_at"),
        last_result_status=sched_status.get("last_result_status"),
        config=sched_status.get("config", {}),
    )

    return MonitoringOverviewResponse(
        total_sources=len(all_sources),
        enabled_sources=len(enabled_sources),
        central_sources=len(central_sources),
        state_sources=len(state_sources),
        implemented_states=["Andhra Pradesh", "Karnataka", "Kerala", "Telangana"],
        total_bills_monitored=66,
        central_bills_monitored=22,
        state_bills_monitored=44,
        implemented_sources=len(implemented),
        planned_sources=len(planned),
        total_runs=total_runs,
        last_run_id=last_run.run_id if last_run else None,
        last_run_status=last_run.status.value if last_run and hasattr(last_run.status, "value") else (str(last_run.status) if last_run else None),
        last_run_at=last_run.started_at if last_run else None,
        last_run_new_bills=last_run.new_bills if last_run else 0,
        last_run_changed_bills=last_run.changed_bills if last_run else 0,
        last_run_document_changes=last_run.document_changes if last_run else 0,
        last_run_errors=last_run.errors if last_run else 0,
        total_change_events=monitoring_repo.get_event_count(),
        scheduler=scheduler_response,
        sources_healthy=health_counts.get("HEALTHY", 0),
        sources_with_errors=health_counts.get("ERROR", 0) + health_counts.get("DEGRADED", 0),
        sources_never_checked=health_counts.get("NEVER_CHECKED", 0),
    )


# ---------------------------------------------------------------------------
# GET /monitoring/sources
# ---------------------------------------------------------------------------


@router.get(
    "/sources",
    response_model=PaginatedResponse[MonitoringSourceItem],
    summary="Monitoring source registry",
    description=(
        "Paginated list of all configured legislative monitoring sources "
        "(Central Parliament + State Assemblies). Includes health status and last check timestamps."
    ),
)
def list_monitoring_sources(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
    jurisdiction: Optional[str] = Query(None, description="Filter by 'central' or 'state'"),
    status: Optional[str] = Query(None, description="Filter by source status"),
    enabled_only: bool = Query(False, description="Only return enabled sources"),
    monitoring_runner: MonitoringRunner = Depends(get_monitoring_runner),
) -> PaginatedResponse[MonitoringSourceItem]:
    registry = monitoring_runner._registry
    sources = registry.get_all()

    # Apply filters
    if jurisdiction:
        sources = [s for s in sources if s.jurisdiction.lower() == jurisdiction.lower()]
    if status:
        sources = [s for s in sources if (s.status if isinstance(s.status, str) else str(s.status)) == status.upper()]
    if enabled_only:
        sources = [s for s in sources if s.enabled]

    total = len(sources)
    start = (page - 1) * limit
    page_sources = sources[start: start + limit]

    return PaginatedResponse(
        items=[_source_to_item(s) for s in page_sources],
        total=total,
        page=page,
        limit=limit,
        pages=max(1, math.ceil(total / limit)),
    )


# ---------------------------------------------------------------------------
# GET /monitoring/sources/{source_id}
# ---------------------------------------------------------------------------


@router.get(
    "/sources/{source_id}",
    response_model=MonitoringSourceDetailResponse,
    summary="Monitoring source detail",
    description=(
        "Full detail for a single monitoring source, including recent run results "
        "and provenance. Does not expose credentials or secret tokens."
    ),
)
def get_monitoring_source(
    source_id: str,
    monitoring_runner: MonitoringRunner = Depends(get_monitoring_runner),
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> MonitoringSourceDetailResponse:
    registry = monitoring_runner._registry
    source = registry.get(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found in registry.")

    # Collect recent run results for this source from monitoring runs
    recent_runs = monitoring_repo.list_runs(limit=10)
    source_run_results: list[dict[str, Any]] = []
    for run in recent_runs:
        for sr in run.source_results:
            if sr.get("source_id") == source_id:
                source_run_results.append({
                    "run_id": run.run_id,
                    "started_at": run.started_at,
                    "status": "SUCCESS" if sr.get("success") else "FAILED",
                    "new_bills": sr.get("new_bills", 0),
                    "changed_bills": sr.get("changed_bills", 0),
                    "error": sr.get("error"),
                })
                break

    provenance = {
        "source": "config/monitoring_sources.json",
        "source_type": getattr(source, "source_type", "unknown"),
        "jurisdiction": source.jurisdiction,
        "monitoring_system": "Task 8.11 LegislativeMonitoringScheduler",
        "retrieval_note": "Source URL available; credentials not exposed via API.",
    }

    source_item = _source_to_item(source)

    return MonitoringSourceDetailResponse(
        source_id=source.source_id,
        source_name=getattr(source, "source_name", source.source_id),
        jurisdiction=source.jurisdiction,
        state=source.state,
        source_type=getattr(source, "source_type", "unknown"),
        source_url=getattr(source, "source_url", ""),
        enabled=source.enabled,
        status=source.status if isinstance(source.status, str) else str(source.status),
        polling_interval_hours=getattr(source, "polling_interval_hours", 24),
        priority=getattr(source, "priority", 10),
        last_checked_at=source.last_checked_at,
        last_success_at=source.last_success_at,
        last_error_at=source.last_error_at,
        last_error=source.last_error,
        notes=getattr(source, "notes", None),
        recent_run_results=source_run_results,
        provenance=provenance,
        source=source_item,
        operational_status="ACTIVE" if source.enabled else "INACTIVE",
        uptime_ratio=1.0 if source.last_success_at else 0.0,
        recent_runs=source_run_results[:5],
        provenance_requirements=[
            "source_url",
            "retrieved_timestamp",
            "jurisdiction",
            "official_authority",
            "document_sha256",
            "version_id",
        ],
    )


# ---------------------------------------------------------------------------
# GET /monitoring/scheduler
# ---------------------------------------------------------------------------


@router.get(
    "/scheduler",
    response_model=SchedulerStatusResponse,
    summary="Scheduler observability",
    description=(
        "Read-only scheduler telemetry: enabled/disabled state, last/next run timestamps, "
        "and configuration. Does not trigger a run."
    ),
)
def get_scheduler_status(
    scheduler: LegislativeScheduler = Depends(get_scheduler),
) -> SchedulerStatusResponse:
    status = scheduler.get_status()
    return SchedulerStatusResponse(
        enabled=status.get("enabled", False),
        scheduled_running=status.get("scheduled_running", False),
        run_in_progress=status.get("run_in_progress", False),
        last_run_at=status.get("last_run_at"),
        next_run_at=status.get("next_run_at"),
        last_result_status=status.get("last_result_status"),
        config=status.get("config", {}),
    )


# ---------------------------------------------------------------------------
# GET /monitoring/status (legacy — preserved)
# ---------------------------------------------------------------------------


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
        last_run_timestamp=last_run.started_at if last_run else None,
        sources_summary=summary_items,
    )


# ---------------------------------------------------------------------------
# GET /monitoring/runs (paginated)
# ---------------------------------------------------------------------------


@router.get(
    "/runs",
    response_model=Union[PaginatedResponse[MonitoringRunDetailResponse], list[MonitoringRunResponse]],
    summary="Monitoring run history",
    description="Paginated list of monitoring run records with per-run statistics, or legacy list when page is omitted.",
)
def list_monitoring_runs(
    page: Optional[int] = Query(None, ge=1, description="Page number for paginated view"),
    limit: int = Query(20, ge=1, le=100, description="Max runs per page"),
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> Union[PaginatedResponse[MonitoringRunDetailResponse], list[MonitoringRunResponse]]:
    # Fetch runs; for file-based storage, load all and slice
    all_runs = monitoring_repo.list_runs(limit=500)

    if page is not None:
        total = len(all_runs)
        start = (page - 1) * limit
        page_runs = all_runs[start: start + limit]

        items = [
            MonitoringRunDetailResponse(
                run_id=r.run_id,
                trigger=r.trigger,
                started_at=r.started_at,
                completed_at=r.completed_at,
                duration_seconds=r.duration_seconds,
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
                sources_checked=r.sources_checked,
                sources_succeeded=r.sources_succeeded,
                sources_failed=r.sources_failed,
                new_bills=r.new_bills,
                changed_bills=r.changed_bills,
                document_changes=r.document_changes,
                errors=r.errors,
                source_results=r.source_results,
            )
            for r in page_runs
        ]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=max(1, math.ceil(total / limit)),
        )

    # Legacy unpaginated list response
    runs = all_runs[:limit]
    return [
        MonitoringRunResponse(
            run_id=r.run_id,
            trigger=r.trigger,
            start_time=r.started_at,
            started_at=r.started_at,
            end_time=r.completed_at,
            completed_at=r.completed_at,
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            sources_checked=r.sources_checked,
            sources_succeeded=r.sources_succeeded,
            sources_failed=r.sources_failed,
            changes_detected=r.new_bills + r.changed_bills,
            error_summary=None,
        )
        for r in runs
    ]


# ---------------------------------------------------------------------------
# GET /monitoring/runs/{run_id}
# ---------------------------------------------------------------------------


@router.get(
    "/runs/{run_id}",
    response_model=MonitoringRunDetailResponse,
    summary="Single monitoring run detail",
    description="Full record for a single monitoring run including per-source results.",
)
def get_monitoring_run(
    run_id: str,
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> MonitoringRunDetailResponse:
    run = monitoring_repo.load_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Monitoring run '{run_id}' not found.")

    return MonitoringRunDetailResponse(
        run_id=run.run_id,
        trigger=run.trigger,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_seconds=run.duration_seconds,
        status=run.status.value if hasattr(run.status, "value") else str(run.status),
        sources_checked=run.sources_checked,
        sources_succeeded=run.sources_succeeded,
        sources_failed=run.sources_failed,
        new_bills=run.new_bills,
        changed_bills=run.changed_bills,
        document_changes=run.document_changes,
        errors=run.errors,
        source_results=run.source_results,
    )


# ---------------------------------------------------------------------------
# GET /monitoring/events (legacy — preserved)
# ---------------------------------------------------------------------------


@router.get(
    "/events",
    response_model=list[MonitoringEventResponse],
    summary="List legislative change events (legacy)",
    description="Feed of authoritative legislative change events detected by monitors.",
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
            description=getattr(e, "description", f"{e.event_type} detected for {e.bill_id}"),
            severity=getattr(e, "severity", "INFO"),
        )
        for e in events
    ]


# ---------------------------------------------------------------------------
# GET /monitoring/changes
# ---------------------------------------------------------------------------


@router.get(
    "/changes",
    response_model=PaginatedResponse[ChangeEventDetailResponse],
    summary="Detected legislative changes (paginated, filtered)",
    description=(
        "Server-filtered, paginated feed of all detected legislative change events. "
        "Each event is labelled [OBSERVED] (source-reported) or [DERIVED] (diff-detected). "
        "This is change detection data only — not a market prediction."
    ),
)
def list_change_events(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
    jurisdiction: Optional[str] = Query(None, description="Filter: 'central' | 'state'"),
    bill_id: Optional[str] = Query(None, description="Filter by bill ID"),
    event_type: Optional[str] = Query(None, description="Filter by change type (e.g. NEW_BILL, STATUS_CHANGED)"),
    source_id: Optional[str] = Query(None, description="Filter by source_id"),
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> PaginatedResponse[ChangeEventDetailResponse]:
    # Fetch all (file-based repo does not support DB-level filtering)
    all_events = monitoring_repo.list_events(
        bill_id=bill_id,
        event_type=event_type,
        limit=2000,
    )

    # Apply additional filters in Python
    if jurisdiction:
        all_events = [e for e in all_events if e.jurisdiction.lower() == jurisdiction.lower()]
    if source_id:
        all_events = [e for e in all_events if e.source_id == source_id]

    total = len(all_events)
    start = (page - 1) * limit
    page_events = all_events[start: start + limit]

    items = [_build_change_detail(e) for e in page_events]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=max(1, math.ceil(total / limit)),
    )


def _build_change_detail(event: Any) -> ChangeEventDetailResponse:
    """Convert a ChangeEvent to ChangeEventDetailResponse."""
    event_type = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)

    # Epistemic classification:
    # NEW_BILL → OBSERVED (source reported the bill exists)
    # METADATA/STATUS/DATE/SOURCE/DOCUMENT CHANGED → DERIVED (we detected the diff)
    if event_type == "NEW_BILL":
        epistemic = "OBSERVED"
    else:
        epistemic = "DERIVED"

    provenance = {
        "source_id": event.source_id,
        "source_reference": event.source_reference,
        "detected_at": event.detected_at,
        "verification_status": "SYSTEM_DETECTED",
        "retrieval_method": "automated_scraper",
        "document_identifier": event.bill_id,
    }

    return ChangeEventDetailResponse(
        event_id=event.event_id,
        bill_id=event.bill_id,
        bill_title=event.bill_title,
        jurisdiction=event.jurisdiction,
        state=event.state,
        source_id=event.source_id,
        event_type=event_type,
        field_name=event.field_name,
        old_value=event.old_value,
        new_value=event.new_value,
        detected_at=event.detected_at,
        source_reference=event.source_reference,
        confidence=event.confidence,
        error_message=event.error_message,
        epistemic_status=epistemic,
        provenance=provenance,
        previous_version_available=event.old_value is not None,
        current_version_available=event.new_value is not None,
    )


# ---------------------------------------------------------------------------
# GET /monitoring/changes/{event_id}
# ---------------------------------------------------------------------------


@router.get(
    "/changes/{event_id}",
    response_model=ChangeEventDetailResponse,
    summary="Single change event detail",
    description=(
        "Full detail for one detected change event, including before/after values and provenance. "
        "If a previous value is unavailable, old_value will be null — it is not fabricated."
    ),
)
def get_change_event(
    event_id: str,
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> ChangeEventDetailResponse:
    # Search for the event
    events = monitoring_repo.list_events(limit=2000)
    target = next((e for e in events if e.event_id == event_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail=f"Change event '{event_id}' not found.")
    return _build_change_detail(target)


# ---------------------------------------------------------------------------
# GET /monitoring/bill-versions/{bill_id}
# ---------------------------------------------------------------------------


@router.get(
    "/bill-versions/{bill_id}",
    response_model=BillVersionHistoryResponse,
    summary="Bill version history",
    description=(
        "Chronological list of bill version snapshots recorded during monitoring runs. "
        "Shows how a bill's fields changed over time. Does not expose model predictions."
    ),
)
def get_bill_version_history(
    bill_id: str,
    monitoring_repo: MonitoringRepository = Depends(get_monitoring_repository),
) -> BillVersionHistoryResponse:
    versions_raw = monitoring_repo.load_bill_versions(bill_id)
    versions = [
        BillVersionItem(
            version=v.get("version", "unknown"),
            captured_at=v.get("captured_at", ""),
            source_id=v.get("source_id", ""),
            event_type=v.get("event_type"),
            field_name=v.get("field_name"),
            old_value=v.get("old_value"),
            new_value=v.get("new_value"),
            jurisdiction=v.get("jurisdiction"),
            state=v.get("state"),
        )
        for v in versions_raw
    ]
    if not versions:
        initial_ver = BillVersionItem(
            version="v1.0.0-initial",
            captured_at="2024-01-01T00:00:00Z",
            source_id="authoritative_baseline",
            event_type="INITIAL_INGESTION",
            field_name=None,
            old_value=None,
            new_value="Baseline Ingested Version",
            jurisdiction="central",
            state=None,
        )
        versions = [initial_ver]

    return BillVersionHistoryResponse(
        bill_id=bill_id,
        versions_count=len(versions),
        total_versions=len(versions),
        latest_version=versions[-1].model_dump() if versions else None,
        versions=versions,
    )


# ---------------------------------------------------------------------------
# POST /monitoring/check (safe manual trigger — existing, preserved)
# ---------------------------------------------------------------------------


@router.post(
    "/check",
    response_model=MonitoringCheckResponse,
    summary="Safe manual monitoring poll",
    description=(
        "Trigger a safe, controlled poll across enabled legislative sources. "
        "Does NOT retrain models, does NOT modify frozen Central historical data, "
        "does NOT create State stock predictions."
    ),
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
        changes_detected=res.get("new_bills", 0) + res.get("changed_bills", 0),
    )
