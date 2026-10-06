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
    CurrentUser,
    get_anticipation_repository,
    get_bill_dossier_service,
    get_cached_predictions,
    get_company_intelligence_service,
    get_current_user,
    get_discovery_service,
)
from api.errors import NotFoundError
from api.schemas import (
    BillChangesResponse,
    BillChangeSummarySchema,
    BillCompanyExposureSchema,
    BillDetailResponse,
    BillDocumentItemSchema,
    BillDocumentsResponse,
    BillModelStatusResponse,
    BillPredictionStatusResponse,
    BillSectorExposureResponse,
    BillStakeholdersResponse,
    BillSummaryItem,
    BillTimelineResponse,
    CorporateExposureEvidenceSchema,
    EnrichedBillDossierResponse,
    PaginatedResponse,
    PlainLanguageExplanationSchema,
    PlainLanguageResponse,
    SectorExposureItemSchema,
    StakeholderPersonaViewSchema,
    TimelineEventSchema,
)
from schemas.unified_bill_record import UnifiedBillRecord
from services.bill_dossier_service import BillDossierService
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
    description="Retrieve a structured dossier for a Central, State, or Live legislative bill, including provisions, provenance, and related bills.",
)
def get_bill_detail(
    bill_id: str,
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
    dossier_service: BillDossierService = Depends(get_bill_dossier_service),
) -> BillDetailResponse:
    bill = discovery_service.get_bill_by_id(bill_id) or dossier_service.resolve_bill(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )

    related = discovery_service.get_related_bills(bill.bill_id, limit=5)
    related_summaries = [_to_bill_summary(r) for r in related]

    _, _, _, prediction_available = dossier_service.get_model_status_info(bill)

    # Gather key provisions from knowledge if available
    provisions: list[str] = []
    if bill.is_central:
        kr = dossier_service.central_knowledge_repo.get(bill.bill_id)
        if kr and hasattr(kr, "key_provisions") and kr.key_provisions:
            provisions = list(kr.key_provisions)
    elif bill.is_state:
        skr = dossier_service.state_knowledge_repo.get(bill.bill_id)
        if skr and skr.economic_profile and hasattr(skr.economic_profile, "key_provisions"):
            provisions = list(skr.economic_profile.key_provisions or [])

    return BillDetailResponse(
        bill=_to_bill_summary(bill),
        provisions=provisions,
        provenance=dict(bill.provenance or {}),
        prediction_available=prediction_available,
        related_bills=related_summaries,
    )


@router.get(
    "/{bill_id}/dossier",
    response_model=EnrichedBillDossierResponse,
    summary="Get enriched bill dossier 2.0",
    description="Retrieve comprehensive legislative intelligence dossier 2.0 including identity, status, timeline, what changed, plain-language analysis, stakeholder perspectives, sector and corporate exposures, documents, and model boundaries.",
)
def get_enriched_bill_dossier(
    bill_id: str,
    dossier_service: BillDossierService = Depends(get_bill_dossier_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> EnrichedBillDossierResponse:
    dossier = dossier_service.get_dossier(bill_id)
    if not dossier:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )
    return EnrichedBillDossierResponse(**dossier.to_dict())


@router.get(
    "/{bill_id}/timeline",
    response_model=BillTimelineResponse,
    summary="Get bill procedural and change timeline",
    description="Retrieve chronological timeline of meaningful legislative events supported strictly by evidence.",
)
def get_bill_timeline(
    bill_id: str,
    dossier_service: BillDossierService = Depends(get_bill_dossier_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> BillTimelineResponse:
    bill = dossier_service.resolve_bill(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )
    timeline = dossier_service.build_timeline(bill)
    return BillTimelineResponse(
        bill_id=bill.bill_id,
        total_events=len(timeline),
        events=[TimelineEventSchema(**t.to_dict()) for t in timeline],
    )


@router.get(
    "/{bill_id}/changes",
    response_model=BillChangesResponse,
    summary="Get structured 'What Changed?' summary",
    description="Retrieve structured change summary distinguishing DOCUMENT CHANGE from LEGISLATIVE STATUS CHANGE.",
)
def get_bill_changes(
    bill_id: str,
    dossier_service: BillDossierService = Depends(get_bill_dossier_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> BillChangesResponse:
    bill = dossier_service.resolve_bill(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )
    changes = dossier_service.build_change_summary(bill)
    return BillChangesResponse(
        bill_id=bill.bill_id,
        changes=BillChangeSummarySchema(**changes.to_dict()),
    )


@router.get(
    "/{bill_id}/plain-language",
    response_model=PlainLanguageResponse,
    summary="Get plain-language non-expert explanation",
    description="Retrieve clear plain-language section answering What is this bill, What does it change, Who could be affected, Why could it matter economically, and What is still unknown.",
)
def get_bill_plain_language(
    bill_id: str,
    dossier_service: BillDossierService = Depends(get_bill_dossier_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> PlainLanguageResponse:
    dossier = dossier_service.get_dossier(bill_id)
    if not dossier:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )
    return PlainLanguageResponse(
        bill_id=dossier.identity.bill_id,
        plain_language=PlainLanguageExplanationSchema(**dossier.content.plain_language.to_dict()),
    )


@router.get(
    "/{bill_id}/stakeholders",
    response_model=BillStakeholdersResponse,
    summary="Get multi-persona stakeholder views",
    description="Retrieve factual stakeholder views for Investor, Business Owner, Employee / Professional, Common Citizen, and Researcher with strict Fact/Interpretation/Prediction separation.",
)
def get_bill_stakeholders(
    bill_id: str,
    dossier_service: BillDossierService = Depends(get_bill_dossier_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> BillStakeholdersResponse:
    dossier = dossier_service.get_dossier(bill_id)
    if not dossier:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )
    views = {
        k: StakeholderPersonaViewSchema(**v.to_dict())
        for k, v in dossier.stakeholder_views.items()
    }
    return BillStakeholdersResponse(
        bill_id=dossier.identity.bill_id,
        stakeholder_views=views,
    )


@router.get(
    "/{bill_id}/sectors",
    response_model=BillSectorExposureResponse,
    summary="Get affected sectors and industries",
    description="Retrieve affected sectors, industries, business activities, and exposure types connected to Macro Sector Directory.",
)
def get_bill_sectors(
    bill_id: str,
    dossier_service: BillDossierService = Depends(get_bill_dossier_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> BillSectorExposureResponse:
    bill = dossier_service.resolve_bill(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )
    sec_exp = dossier_service.build_sector_exposures(bill)
    return BillSectorExposureResponse(
        bill_id=bill.bill_id,
        sector_exposures=[SectorExposureItemSchema(**s.to_dict()) for s in sec_exp],
    )


@router.get(
    "/{bill_id}/documents",
    response_model=BillDocumentsResponse,
    summary="Get official supporting documents and metadata",
    description="Retrieve official documents, URLs, SHA-256 hashes, retrieval status, and provenance.",
)
def get_bill_documents(
    bill_id: str,
    dossier_service: BillDossierService = Depends(get_bill_dossier_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> BillDocumentsResponse:
    bill = dossier_service.resolve_bill(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )
    docs = dossier_service.build_documents(bill)
    return BillDocumentsResponse(
        bill_id=bill.bill_id,
        total_documents=len(docs),
        documents=[BillDocumentItemSchema(**d.to_dict()) for d in docs],
    )


@router.get(
    "/{bill_id}/model-status",
    response_model=BillModelStatusResponse,
    summary="Get analytical model status and firewall boundary",
    description="Retrieve analytical status (MODELLED, KNOWLEDGE_ONLY, PENDING_REVIEW, NOT_ELIGIBLE) and firewall verification.",
)
def get_bill_model_status(
    bill_id: str,
    dossier_service: BillDossierService = Depends(get_bill_dossier_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> BillModelStatusResponse:
    bill = dossier_service.resolve_bill(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Bill with ID '{bill_id}' not found.",
        )
    model_status, label, desc, pred_avail = dossier_service.get_model_status_info(bill)
    return BillModelStatusResponse(
        bill_id=bill.bill_id,
        model_status=model_status,
        model_status_label=label,
        model_status_description=desc,
        prediction_available=pred_avail,
        is_central=bill.is_central,
        is_state=bill.is_state,
        jurisdiction=bill.jurisdiction,
        state=bill.state,
        firewall_active=not pred_avail or bill.is_state,
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
