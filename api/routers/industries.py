"""
api/routers/industries.py
=========================
REST API router for Industry and Sector Intelligence Layer (Task 8.14.8).
"""

from __future__ import annotations

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import get_industry_intelligence_service
from api.errors import NotFoundError
from api.schemas import (
    IndustryBillItemResponse,
    IndustryCompanyItemResponse,
    IndustryDossierResponse,
    IndustrySummaryResponse,
    PaginatedResponse,
)
from services.industry_intelligence_service import (
    IndustryIntelligenceService,
)

router = APIRouter(prefix="/industries", tags=["Industries & Sectors"])


@router.get(
    "",
    response_model=PaginatedResponse[IndustrySummaryResponse],
    summary="List and filter industry sector intelligence profiles",
    description="Retrieve a paginated list of canonical industries across Central and State legislative frameworks.",
)
def list_industries(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    sector: Optional[str] = Query(None, description="Filter by broad economic sector"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction: central | state"),
    universe_type: Optional[str] = Query(None, description="Filter: quantitative | intelligence"),
    has_market_predictions: Optional[bool] = Query(None, description="Filter by market prediction availability"),
    search: Optional[str] = Query(None, description="Search across industry name, sector, or economic mechanism"),
    sort_by: str = Query("bills_desc", description="Sorting: bills_desc | companies_desc | name_asc | level_asc"),
    industry_service: IndustryIntelligenceService = Depends(get_industry_intelligence_service),
) -> PaginatedResponse[IndustrySummaryResponse]:
    all_industries = industry_service.list_industries(
        sector=sector,
        jurisdiction=jurisdiction,
        universe_type=universe_type,
        has_market_predictions=has_market_predictions,
        search=search,
        sort_by=sort_by,
    )

    total = len(all_industries)
    start = (page - 1) * limit
    end = start + limit
    page_items = all_industries[start:end]

    items = [
        IndustrySummaryResponse(
            industry_id=ind.industry_id,
            name=ind.name,
            sector=ind.sector,
            coverage_level=ind.coverage_level,
            related_bills_count=ind.related_bills_count,
            exposed_companies_count=ind.exposed_companies_count,
            central_exposures_count=ind.central_exposures_count,
            state_exposures_count=ind.state_exposures_count,
            quantitative_companies_count=ind.quantitative_companies_count,
            intelligence_companies_count=ind.intelligence_companies_count,
            market_analysis_available=ind.market_analysis_available,
            economic_mechanisms=ind.economic_mechanisms,
            latest_legislative_activity=ind.latest_legislative_activity,
            sub_industries=ind.sub_industries,
        )
        for ind in page_items
    ]

    return PaginatedResponse[IndustrySummaryResponse](
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if limit > 0 else 1,
    )


@router.get(
    "/{industry_id}",
    response_model=IndustryDossierResponse,
    summary="Get complete industry sector intelligence dossier",
    description="Retrieve factual metadata, executive overview, legislative footprint, corporate exposure, transmission chain, market intelligence, state intelligence, risk, anticipation, and provenance.",
)
def get_industry_dossier(
    industry_id: str,
    industry_service: IndustryIntelligenceService = Depends(get_industry_intelligence_service),
) -> IndustryDossierResponse:
    dossier = industry_service.get_industry_dossier(industry_id)
    if not dossier:
        raise NotFoundError(
            code="INDUSTRY_NOT_FOUND",
            message=f"Industry '{industry_id}' was not found in corporate or legislative records.",
        )
    return IndustryDossierResponse(**dossier.to_dict())


@router.get(
    "/{industry_id}/bills",
    response_model=PaginatedResponse[IndustryBillItemResponse],
    summary="Get bills affecting this industry",
    description="Retrieve all Central and State bills impacting companies in this industry with policy domains and economic mechanisms.",
)
def get_industry_bills(
    industry_id: str,
    jurisdiction: Optional[str] = Query(None, description="central | state"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    industry_service: IndustryIntelligenceService = Depends(get_industry_intelligence_service),
) -> PaginatedResponse[IndustryBillItemResponse]:
    bills = industry_service.get_industry_bills(industry_id, jurisdiction=jurisdiction)
    total = len(bills)
    start = (page - 1) * limit
    end = start + limit
    page_items = bills[start:end]

    items = [IndustryBillItemResponse(**b.to_dict()) for b in page_items]

    return PaginatedResponse[IndustryBillItemResponse](
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if limit > 0 else 1,
    )


@router.get(
    "/{industry_id}/companies",
    response_model=PaginatedResponse[IndustryCompanyItemResponse],
    summary="Get companies operating in this industry",
    description="Retrieve companies in this industry grouped by quantitative modeling, corporate intelligence, or reference status.",
)
def get_industry_companies(
    industry_id: str,
    universe_type: Optional[str] = Query(None, description="quantitative | intelligence | reference"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    industry_service: IndustryIntelligenceService = Depends(get_industry_intelligence_service),
) -> PaginatedResponse[IndustryCompanyItemResponse]:
    companies = industry_service.get_industry_companies(industry_id, universe_type=universe_type)
    total = len(companies)
    start = (page - 1) * limit
    end = start + limit
    page_items = companies[start:end]

    items = [IndustryCompanyItemResponse(**c.to_dict()) for c in page_items]

    return PaginatedResponse[IndustryCompanyItemResponse](
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if limit > 0 else 1,
    )
