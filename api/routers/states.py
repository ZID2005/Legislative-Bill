"""
api/routers/states.py
=====================
REST API router for Indian State Legislative & Economic Intelligence.
Maintains strict firewall: State stock price predictions = 0.
"""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Depends

from api.dependencies import (
    get_discovery_service,
    get_state_corporate_repository,
    get_state_knowledge_repository,
)
from api.errors import NotFoundError
from api.schemas import (
    BillCompanyExposureSchema,
    BillSummaryItem,
    CorporateExposureEvidenceSchema,
    StateCoverageItem,
    StateCoverageResponse,
    StateDetailResponse,
)
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
from storage.state_knowledge_repository import StateKnowledgeRepository
from utils.state_normalizer import normalize_state

router = APIRouter(prefix="/states", tags=["States"])


@router.get(
    "",
    response_model=StateCoverageResponse,
    summary="List Indian States coverage",
    description="Retrieve implementation and roadmap status across all 28 Indian States (4 active pilots, 24 planned).",
)
def list_states(
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
) -> StateCoverageResponse:
    cov = discovery_service.get_state_coverage()
    imp_items = [
        StateCoverageItem(
            state=it.get("state", ""),
            bills_count=it.get("bills_count", 0),
            status="IMPLEMENTED",
            authority=it.get("authority", "AUTHORITATIVE"),
            legislative_source=it.get("source") or it.get("legislative_source", ""),
        )
        for it in cov.get("implemented_states", [])
    ]
    plan_items = [
        StateCoverageItem(
            state=it.get("state", ""),
            bills_count=0,
            status="PLANNED",
            authority="Official Portal",
            legislative_source=it.get("source") or it.get("legislative_source", ""),
            feasibility=it.get("feasibility"),
            notes=it.get("notes"),
        )
        for it in cov.get("planned_states", [])
    ]
    return StateCoverageResponse(
        total_states_in_union=cov.get("total_states_in_union", 28),
        implemented_count=len(imp_items),
        planned_count=len(plan_items),
        implemented_states_list=[it.state for it in imp_items],
        implemented_states=imp_items,
        planned_states=plan_items,
    )


@router.get(
    "/{state}",
    response_model=StateDetailResponse,
    summary="Get State legislative & economic intelligence profile",
    description="Retrieve State assembly coverage, active economic sectors, and corporate exposures. Reaffirms zero stock predictions.",
)
def get_state_detail(
    state: str,
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
    state_corp_repo: StateCorporateExposureRepository = Depends(get_state_corporate_repository),
) -> StateDetailResponse:
    norm_state = normalize_state(state)
    if not norm_state:
        raise NotFoundError(
            code="STATE_NOT_FOUND",
            message=f"State '{state}' is not a recognized Indian State or Union Territory.",
        )

    coverage = discovery_service.get_state_coverage()
    implemented_map = {item["state"].lower(): item for item in coverage.get("implemented_states", [])}

    is_implemented = norm_state.lower() in implemented_map
    info = implemented_map.get(norm_state.lower(), {})

    # Sector calculation from state bills
    state_bills = discovery_service.get_state_bills(state=norm_state)
    active_sectors = sorted(
        list(
            {
                sec
                for b in state_bills
                for sec in (b.economic_sectors + b.secondary_sectors)
                if sec
            }
        )
    )

    exposures = state_corp_repo.get_by_state(norm_state)

    status_str = "IMPLEMENTED" if is_implemented else "PLANNED"
    source = info.get("source", f"{norm_state} Legislative Assembly Gazette")
    authority = info.get("authority", "Official State Gazette")
    bills_cnt = len(state_bills)

    return StateDetailResponse(
        state=norm_state,
        status=status_str,
        bills_count=bills_cnt,
        legislative_source=source,
        authority=authority,
        assembly_chamber=f"{norm_state} Legislative Assembly (Vidhan Sabha)",
        statutory_guarantee="STATE_STOCK_PREDICTIONS_STRICTLY_ZERO",
        economic_sectors_active=active_sectors,
        total_corporate_exposures=len(exposures),
    )


@router.get(
    "/{state}/bills",
    response_model=list[BillSummaryItem],
    summary="Get bills for State",
    description="Retrieve all validated legislative bills enacted or introduced in the specified State assembly.",
)
def get_state_bills(
    state: str,
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
) -> list[BillSummaryItem]:
    norm_state = normalize_state(state)
    if not norm_state:
        raise NotFoundError(
            code="STATE_NOT_FOUND",
            message=f"State '{state}' is not a recognized Indian State.",
        )

    bills = discovery_service.get_state_bills(state=norm_state)
    from api.routers.bills import _to_bill_summary
    return [_to_bill_summary(b) for b in bills]


@router.get(
    "/{state}/exposures",
    response_model=list[BillCompanyExposureSchema],
    summary="Get corporate exposures for State",
    description="Retrieve evidence-backed corporate exposure records originating from State legislation.",
)
def get_state_exposures(
    state: str,
    state_corp_repo: StateCorporateExposureRepository = Depends(get_state_corporate_repository),
) -> list[BillCompanyExposureSchema]:
    norm_state = normalize_state(state)
    if not norm_state:
        raise NotFoundError(
            code="STATE_NOT_FOUND",
            message=f"State '{state}' is not a recognized Indian State.",
        )

    exposures = state_corp_repo.get_by_state(norm_state)
    results: list[BillCompanyExposureSchema] = []
    for e in exposures:
        ev_schemas = [
            CorporateExposureEvidenceSchema(
                claim=ev.claim,
                reference=ev.reference,
                url=getattr(ev, "url", None),
                statutory_section=getattr(ev, "statutory_section", None),
            )
            for ev in e.evidence
        ]
        results.append(
            BillCompanyExposureSchema(
                bill_id=e.bill_id,
                bill_title=getattr(e, "bill_title", None) or e.bill_id.replace("-", " ").title(),
                company_id=e.company_id,
                company_name=e.company_name,
                bill_number=None,
                jurisdiction="state",
                state=e.state,
                bill_status="introduced",
                sector=e.sector,
                sub_sector=e.sub_sector,
                business_activity=e.business_activity,
                exposure_type=e.exposure_type,
                exposure_direction=e.exposure_direction,
                exposure_strength=e.exposure_strength,
                direct_indirect=e.direct_indirect,
                geographic_scope=e.geographic_scope,
                mechanism=e.mechanism,
                market_relevance=e.market_relevance,
                confidence=e.confidence,
                has_evidence=len(e.evidence) > 0,
                evidence=ev_schemas,
                source_urls=list(e.source_urls),
            )
        )
    return results
