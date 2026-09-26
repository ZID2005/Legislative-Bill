"""
api/routers/companies.py
========================
REST API router for Corporate Universe and Company Intelligence dossiers.
"""

from __future__ import annotations

import math
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    get_cached_predictions,
    get_company_intelligence_service,
)
from api.errors import NotFoundError
from api.schemas import (
    BillCompanyExposureSchema,
    CompanyDetailResponse,
    CompanyExposureExplanationResponse,
    CompanyPredictionStatusResponse,
    CompanySummaryItem,
    CorporateExposureEvidenceSchema,
    PaginatedResponse,
)
from schemas.company import Company, UniverseType
from services.company_intelligence_service import (
    _CENTRAL_QUANTITATIVE_ISINS,
    CompanyIntelligenceService,
)

router = APIRouter(prefix="/companies", tags=["Companies"])


def _to_company_summary(
    c: Company, company_service: CompanyIntelligenceService
) -> CompanySummaryItem:
    u_type = c.universe_type.value if hasattr(c.universe_type, "value") else str(c.universe_type)
    e_type = c.entity_type.value if hasattr(c.entity_type, "value") else str(c.entity_type)
    is_quant = c.isin in _CENTRAL_QUANTITATIVE_ISINS
    has_preds = is_quant and u_type in (UniverseType.QUANTITATIVE.value, UniverseType.BOTH.value)

    # Documented exposures count
    exps = company_service.exposure_repo.get_bills_for_company(c.isin)
    if not exps and c.company_name:
        exps = company_service.exposure_repo.get_bills_for_company(c.company_name)

    return CompanySummaryItem(
        company_id=c.isin,
        company_name=c.company_name,
        ticker_nse=c.ticker_nse or None,
        ticker_bse=c.ticker_bse or None,
        isin=c.isin,
        sector=c.sector,
        industry=c.industry,
        sub_industry=c.sub_industry or None,
        entity_type=e_type,
        universe_type=u_type,
        ownership_type=c.ownership_type.value if hasattr(c.ownership_type, "value") else str(c.ownership_type),
        is_active=c.is_active,
        listing_status=c.listing_status,
        hq_state=c.hq_state or None,
        watchlist_eligible=getattr(c, "watchlist_eligible", False),
        is_quant_eligible=is_quant,
        market_prediction_available=has_preds,
        documented_exposure_count=len(exps),
    )


@router.get(
    "",
    response_model=PaginatedResponse[CompanySummaryItem],
    summary="List and filter corporate universe entities",
    description="Retrieve a paginated list of companies and intelligence entities across Central and State universes.",
)
def list_companies(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, ticker, ISIN, or alias"),
    universe_type: Optional[str] = Query(None, description="Filter: all | quantitative | intelligence"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    state: Optional[str] = Query(None, description="Filter by state presence or HQ"),
    listing_status: Optional[str] = Query(None, description="Filter: Listed | Unlisted"),
    is_quant_eligible: Optional[bool] = Query(None, description="Filter by quantitative modeling eligibility"),
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> PaginatedResponse[CompanySummaryItem]:
    u_norm = universe_type
    if universe_type:
        u_clean = universe_type.strip().lower()
        if u_clean in ("intelligence", "intelligence_only", "intel"):
            u_norm = "intelligence"
        elif u_clean in ("quantitative", "quant"):
            u_norm = "quantitative"

    all_companies = company_service.get_all_companies(universe_type=u_norm)

    filtered: list[Company] = []
    q = search.strip().lower() if search else None

    for c in all_companies:
        # Search query matching
        if q:
            name_match = q in c.company_name.lower() or q in c.isin.lower()
            ticker_match = (c.ticker_nse and q in c.ticker_nse.lower()) or (c.ticker_bse and q in c.ticker_bse.lower())
            alias_match = any(q in al.lower() for al in getattr(c, "aliases", []))
            if not (name_match or ticker_match or alias_match):
                continue

        # Filters
        if entity_type:
            e_val = c.entity_type.value if hasattr(c.entity_type, "value") else str(c.entity_type)
            if e_val.lower() != entity_type.strip().lower():
                continue

        if sector:
            if sector.strip().lower() not in c.sector.lower():
                continue

        if industry:
            if industry.strip().lower() not in c.industry.lower():
                continue

        if listing_status:
            if c.listing_status.lower() != listing_status.strip().lower():
                continue

        if state:
            st_lower = state.strip().lower()
            hq_match = c.hq_state and st_lower in c.hq_state.lower()
            presence_match = any(
                st_lower in (getattr(sp, "state", "") or "").lower()
                for sp in getattr(c, "state_presences", [])
            )
            if not (hq_match or presence_match):
                continue

        if is_quant_eligible is not None:
            is_quant = c.isin in _CENTRAL_QUANTITATIVE_ISINS
            if is_quant != is_quant_eligible:
                continue

        filtered.append(c)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit
    page_items = [_to_company_summary(c, company_service) for c in filtered[start:end]]

    return PaginatedResponse[CompanySummaryItem](
        items=page_items,
        total=total,
        page=page,
        limit=limit,
        pages=total_pages,
    )


@router.get(
    "/{company_id}",
    response_model=CompanyDetailResponse,
    summary="Get single company profile dossier",
    description="Retrieve a complete corporate intelligence dossier including operational presence, quantitative firewall status, and related bills.",
)
@router.get(
    "/{company_id}/dossier",
    response_model=CompanyDetailResponse,
    summary="Get single company profile dossier (alias)",
    description="Alias to retrieve a complete corporate intelligence dossier.",
)
def get_company_detail(
    company_id: str,
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> CompanyDetailResponse:
    profile = company_service.get_company_profile(company_id)
    if not profile:
        raise NotFoundError(
            code="COMPANY_NOT_FOUND",
            message=f"Company '{company_id}' not found.",
        )

    # Convert to schema
    p_dict = profile.to_dict()
    return CompanyDetailResponse(**p_dict)


@router.get(
    "/{company_id}/bills",
    response_model=list[BillCompanyExposureSchema],
    summary="Get bills affecting company",
    description="Retrieve all verified Central and State legislative bills affecting this corporate entity.",
)
def get_company_bills(
    company_id: str,
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> list[BillCompanyExposureSchema]:
    company = company_service.resolve_company(company_id)
    if not company:
        raise NotFoundError(
            code="COMPANY_NOT_FOUND",
            message=f"Company '{company_id}' not found.",
        )

    views = company_service.get_bills_for_company(company.isin)
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
    "/{company_id}/exposures",
    response_model=list[BillCompanyExposureSchema],
    summary="Get verified exposures for company",
    description="Alias for bills affecting company, returning all evidence-backed exposure relations.",
)
def get_company_exposures(
    company_id: str,
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> list[BillCompanyExposureSchema]:
    return get_company_bills(company_id=company_id, company_service=company_service)


@router.get(
    "/{company_id}/exposures/{bill_id}/explain",
    response_model=CompanyExposureExplanationResponse,
    summary="Explain exposure between company and bill",
    description="Retrieve deterministic, evidence-grounded explanation of why a company is exposed to legislation.",
)
def explain_company_exposure(
    company_id: str,
    bill_id: str,
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> CompanyExposureExplanationResponse:
    explanation = company_service.explain_exposure(company_id, bill_id)
    return CompanyExposureExplanationResponse(**explanation.to_dict())


@router.get(
    "/{company_id}/predictions",
    response_model=CompanyPredictionStatusResponse,
    summary="Get market predictions for company",
    description="Retrieve quantitative predictions for Central-modeled companies. Enforces strict firewall for intelligence-only entities.",
)
def get_company_predictions(
    company_id: str,
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> CompanyPredictionStatusResponse:
    company = company_service.resolve_company(company_id)
    if not company:
        raise NotFoundError(
            code="COMPANY_NOT_FOUND",
            message=f"Company '{company_id}' not found.",
        )

    u_type = company.universe_type.value if hasattr(company.universe_type, "value") else str(company.universe_type)
    is_quant = company.isin in _CENTRAL_QUANTITATIVE_ISINS

    # Quantitative Firewall: Intelligence-only or unlisted entities have ZERO predictions
    if not is_quant or u_type == UniverseType.INTELLIGENCE.value:
        return CompanyPredictionStatusResponse(
            available=False,
            has_predictions=False,
            company_id=company.isin,
            status="INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS",
            firewall_status="INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS",
            reason="INTELLIGENCE_ONLY_ENTITY",
            message="Intelligence-only entities are strictly firewalled from market models. Stock predictions remain strictly 0.",
            universe_type=u_type,
            predictions=[],
            items=[],
            total=0,
        )

    # Return predictions from cached index for this company
    all_preds, _ = get_cached_predictions()
    matching = [p.to_dict() for p in all_preds if p.company_isin == company.isin]

    return CompanyPredictionStatusResponse(
        available=True,
        has_predictions=True,
        company_id=company.isin,
        status="AVAILABLE",
        firewall_status=None,
        reason=None,
        universe_type="quantitative",
        predictions=matching,
        items=matching,
        total=len(matching),
    )
