"""
api/routers/bills.py
====================
REST API router for Legislative Bills discovery and dossiers.
"""

from __future__ import annotations

import math
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    get_anticipation_repository,
    get_cached_predictions,
    get_company_intelligence_service,
    get_discovery_service,
)
from api.errors import NotFoundError
from api.schemas import (
    BillCompanyExposureSchema,
    BillDetailResponse,
    BillPredictionStatusResponse,
    BillSummaryItem,
    CorporateExposureEvidenceSchema,
    PaginatedResponse,
)
from schemas.unified_bill_record import UnifiedBillRecord
from services.company_intelligence_service import CompanyIntelligenceService
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from storage.anticipation_repository import AnticipationRepository

router = APIRouter(prefix="/bills", tags=["Bills"])


def _to_bill_summary(b: UnifiedBillRecord) -> BillSummaryItem:
    return BillSummaryItem(
        bill_id=b.bill_id,
        jurisdiction=b.jurisdiction,
        state=b.state,
        title=b.title,
        short_title=b.short_title or b.title,
        bill_number=b.bill_number,
        legislature=b.legislature,
        house=b.house,
        year=b.year,
        introduction_date=b.introduction_date,
        assent_date=b.assent_date,
        status=b.status,
        policy_domain=b.policy_domain,
        economic_sectors=list(b.economic_sectors),
        secondary_sectors=list(b.secondary_sectors),
        stakeholders=list(b.stakeholders),
        summary=b.summary,
        company_exposure_count=b.company_exposure_count,
        listed_company_exposure_count=b.listed_company_exposure_count,
        market_relevance=b.market_relevance,
        modeling_eligibility=b.modeling_eligibility,
        data_sufficiency=b.data_sufficiency,
        source_url=b.source_url,
        pdf_url=b.pdf_url,
        data_quality=b.data_quality,
    )


@router.get(
    "",
    response_model=PaginatedResponse[BillSummaryItem],
    summary="List and filter legislative bills",
    description="Retrieve a paginated list of unified Central and State legislative bills with comprehensive multi-attribute filtering.",
)
def list_bills(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Free text or token search query"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction: central | state | all"),
    state: Optional[str] = Query(None, description="Filter by Indian state (e.g. Kerala, Karnataka)"),
    house: Optional[str] = Query(None, description="Filter by house or chamber"),
    year: Optional[int] = Query(None, description="Filter by legislative year"),
    status: Optional[str] = Query(None, description="Filter by status (introduced, passed, etc.)"),
    policy_domain: Optional[str] = Query(None, description="Filter by policy domain"),
    sector: Optional[str] = Query(None, description="Filter by economic sector"),
    stakeholder: Optional[str] = Query(None, description="Filter by affected stakeholder"),
    market_relevance: Optional[str] = Query(None, description="Filter by market relevance (HIGH, MEDIUM, LOW, NONE)"),
    modeling_eligibility: Optional[str] = Query(None, description="Filter by modeling eligibility (ELIGIBLE, NOT_ELIGIBLE)"),
    data_sufficiency: Optional[str] = Query(None, description="Filter by data sufficiency (COMPLETE, INSUFFICIENT)"),
    has_company_exposure: Optional[bool] = Query(None, description="Filter bills having verified corporate exposures"),
    sort_by: str = Query("introduction_date", description="Field to sort by: introduction_date | title | year"),
    sort_order: str = Query("desc", description="Sort order: asc | desc"),
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
) -> PaginatedResponse[BillSummaryItem]:
    # Call underlying domain search/filter service
    if search:
        records = discovery_service.search(
            query=search,
            jurisdiction=jurisdiction,
            state=state,
            sector=sector,
            stakeholder=stakeholder,
            status=status,
            has_company_exposure=has_company_exposure,
            market_relevance=market_relevance,
            modeling_eligibility=modeling_eligibility,
        )
    else:
        records = discovery_service.filter_bills(
            jurisdiction=jurisdiction,
            state=state,
            policy_domain=policy_domain,
            sector=sector,
            stakeholder=stakeholder,
            status=status,
            house=house,
            year=year,
            has_company_exposure=has_company_exposure,
            market_relevance=market_relevance,
            modeling_eligibility=modeling_eligibility,
            data_sufficiency=data_sufficiency,
        )

    # Sort if requested
    reverse = sort_order.lower() == "desc"
    if sort_by == "title":
        records = sorted(records, key=lambda b: b.title.lower(), reverse=reverse)
    elif sort_by == "year":
        records = sorted(records, key=lambda b: b.year, reverse=reverse)
    elif sort_by == "introduction_date":
        def _sort_date_key(b: UnifiedBillRecord) -> tuple[int, str]:
            if b.introduction_date:
                return (1, b.introduction_date)
            return (0, "")
        records = sorted(records, key=_sort_date_key, reverse=reverse)

    total = len(records)
    total_pages = math.ceil(total / limit) if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit
    page_items = [_to_bill_summary(b) for b in records[start:end]]

    return PaginatedResponse[BillSummaryItem](
        items=page_items,
        total=total,
        page=page,
        limit=limit,
        pages=total_pages,
    )


@router.get(
    "/{bill_id}",
    response_model=BillDetailResponse,
    summary="Get single bill dossier",
    description="Retrieve a structured dossier for a Central or State legislative bill, including provisions, provenance, and related bills.",
)
def get_bill_detail(
    bill_id: str,
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
) -> BillDetailResponse:
    bill = discovery_service.get_bill_by_id(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )

    related = discovery_service.get_related_bills(bill_id, limit=5)
    related_summaries = [_to_bill_summary(r) for r in related]

    prediction_available = bill.is_central and bill.modeling_eligibility == "ELIGIBLE"

    return BillDetailResponse(
        bill=_to_bill_summary(bill),
        provisions=[],
        provenance=dict(bill.provenance or {}),
        prediction_available=prediction_available,
        related_bills=related_summaries,
    )


@router.get(
    "/{bill_id}/companies",
    response_model=list[BillCompanyExposureSchema],
    summary="Get corporate exposures for bill",
    description="Retrieve evidence-backed corporate exposure records associated with this bill.",
)
def get_bill_companies(
    bill_id: str,
    company_intel_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
) -> list[BillCompanyExposureSchema]:
    bill = discovery_service.get_bill_by_id(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )

    views = company_intel_service.get_companies_for_bill(bill_id)
    results: list[BillCompanyExposureSchema] = []
    for v in views:
        ev_schemas = [
            CorporateExposureEvidenceSchema(
                claim=ev.claim,
                reference=ev.reference,
                url=getattr(ev, "url", None),
                statutory_section=getattr(ev, "statutory_section", None),
            )
            for ev in v.evidence
        ]
        results.append(
            BillCompanyExposureSchema(
                bill_id=v.bill_id,
                bill_title=v.bill_title,
                company_id=v.company_id,
                company_name=v.company_name,
                bill_number=v.bill_number,
                jurisdiction=v.jurisdiction,
                state=v.state,
                bill_status=v.bill_status,
                sector=v.sector,
                sub_sector=v.sub_sector,
                business_activity=v.business_activity,
                exposure_type=v.exposure_type,
                exposure_direction=v.exposure_direction,
                exposure_strength=v.exposure_strength,
                direct_indirect=v.direct_indirect,
                geographic_scope=v.geographic_scope,
                mechanism=v.mechanism,
                market_relevance=v.market_relevance,
                confidence=v.confidence,
                has_evidence=v.has_evidence,
                evidence=ev_schemas,
                source_urls=list(v.source_urls),
            )
        )
    return results


@router.get(
    "/{bill_id}/exposures",
    response_model=list[BillCompanyExposureSchema],
    summary="Get corporate exposures for bill (alias)",
    description="Retrieve evidence-backed corporate exposure records associated with this bill.",
)
def get_bill_exposures(
    bill_id: str,
    company_intel_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
) -> list[BillCompanyExposureSchema]:
    return get_bill_companies(bill_id=bill_id, company_intel_service=company_intel_service, discovery_service=discovery_service)


@router.get(
    "/{bill_id}/predictions",
    response_model=BillPredictionStatusResponse,
    summary="Get market predictions for bill",
    description="Retrieve verified production predictions for Central bills. For State bills, returns a firewalled response with predictions strictly empty.",
)
def get_bill_predictions(
    bill_id: str,
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
) -> BillPredictionStatusResponse:
    bill = discovery_service.get_bill_by_id(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )

    # State bills prediction firewall
    if bill.is_state:
        return BillPredictionStatusResponse(
            available=False,
            has_predictions=False,
            bill_id=bill_id,
            status="STATE_QUALITATIVE_ONLY",
            firewall_status="STATE_QUALITATIVE_ONLY",
            reason="State legislation does not generate quantitative market predictions under project invariants.",
            message="State bills are isolated from Central stock market models. Quantitative predictions remain strictly 0.",
            jurisdiction="state",
            predictions=[],
            items=[],
            total=0,
        )

    # Non-modeled Central bill
    if bill.modeling_eligibility != "ELIGIBLE":
        return BillPredictionStatusResponse(
            available=False,
            has_predictions=False,
            bill_id=bill_id,
            status="CENTRAL_NON_MODELLED_BILL",
            firewall_status="CENTRAL_NON_MODELLED_BILL",
            reason="CENTRAL_NON_MODELLED_BILL",
            message="Bill is not part of the frozen 20 quantitative production set.",
            jurisdiction="central",
            predictions=[],
            items=[],
            total=0,
        )

    # Central modeled bill: load from cached predictions index
    all_preds, _ = get_cached_predictions()
    matching = [p.to_dict() for p in all_preds if p.bill_id == bill_id]

    return BillPredictionStatusResponse(
        available=True,
        has_predictions=True,
        bill_id=bill_id,
        status="AVAILABLE",
        firewall_status=None,
        reason=None,
        jurisdiction="central",
        predictions=matching,
        items=matching,
        total=len(matching),
    )


@router.get(
    "/{bill_id}/anticipation",
    summary="Get pre-event anticipation data for bill",
    description="Retrieve pre-event anticipation bias scores and diffusion evidence for a Central bill.",
)
def get_bill_anticipation(
    bill_id: str,
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
    anticipation_repo: AnticipationRepository = Depends(get_anticipation_repository),
) -> dict[str, Any]:
    bill = discovery_service.get_bill_by_id(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )

    if bill.is_state:
        return {
            "available": False,
            "bill_id": bill_id,
            "reason": "STATE_ANTICIPATION_NOT_APPLICABLE",
            "scores": [],
        }

    scores = anticipation_repo.get_scores_by_bill(bill_id)
    bill_record = anticipation_repo.get_bill_score(bill_id)

    return {
        "available": True,
        "bill_id": bill_id,
        "bill_record": bill_record.to_dict() if bill_record else None,
        "scores": [s.to_dict() for s in scores],
    }
