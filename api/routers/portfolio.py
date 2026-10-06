"""
api/routers/portfolio.py
========================
Task 8.28 — REST API Router for Multi-Tenant Portfolios & Legislative Exposure.

Enforces:
- Strict user and tenant scoping on every endpoint.
- Decision support language only — no Buy/Sell/Hold or financial advice.
- Epistemic separation of user-provided holdings vs platform-derived legislative exposure.
- Firewall invariance: 0 State stock predictions, 0 predictions for unmodeled companies.
"""

from __future__ import annotations

from typing import Any, Optional
import uuid
from fastapi import APIRouter, Depends, Query, status

from api.dependencies import (
    CurrentUser,
    get_current_user,
    get_decision_intelligence_service,
    get_portfolio_repository,
)
from api.errors import BadRequestError, ForbiddenError, NotFoundError
from api.schemas import (
    AddHoldingRequest,
    BulkImportHoldingsRequest,
    CreatePortfolioRequest,
    PersonalizedImpactReportResponse,
    PortfolioHoldingSchema,
    PortfolioLegislativeExposureResponse,
    UpdateHoldingRequest,
    UpdatePortfolioRequest,
    UserPortfolioSchema,
)
from schemas.portfolio import PortfolioHolding, UserPortfolio
from services.decision_intelligence_service import DecisionIntelligenceService
from storage.portfolio_repository import PortfolioRepository

router = APIRouter(prefix="/portfolio", tags=["Portfolio & Legislative Exposure"])


def _to_portfolio_schema(p: UserPortfolio) -> UserPortfolioSchema:
    return UserPortfolioSchema(
        portfolio_id=p.portfolio_id,
        user_id=p.user_id,
        tenant_id=p.tenant_id,
        name=p.name,
        description=p.description,
        holdings=[
            PortfolioHoldingSchema(
                holding_id=h.holding_id,
                company_name=h.company_name,
                ticker=h.ticker,
                isin=h.isin,
                quantity=h.quantity,
                avg_purchase_price=h.avg_purchase_price,
                current_value=h.current_value,
                sector=h.sector,
                industry=h.industry,
                notes=h.notes,
                created_at=h.created_at,
                updated_at=h.updated_at,
            )
            for h in p.holdings
        ],
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get(
    "",
    response_model=list[UserPortfolioSchema],
    summary="List all portfolios for current user",
    description="Retrieve all portfolios scoped strictly to the authenticated user and tenant.",
)
def list_portfolios(
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> list[UserPortfolioSchema]:
    pfs = portfolio_repo.list_by_user(user_id=current_user.user_id, tenant_id=current_user.tenant_id)
    if not pfs:
        # Create initial default portfolio for smooth first-time experience
        default_pf = portfolio_repo.get_or_create_default(user_id=current_user.user_id, tenant_id=current_user.tenant_id)
        pfs = [default_pf]
    return [_to_portfolio_schema(p) for p in pfs]


@router.post(
    "",
    response_model=UserPortfolioSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new portfolio",
    description="Create a new user portfolio with tenant isolation.",
)
def create_portfolio(
    req: CreatePortfolioRequest,
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> UserPortfolioSchema:
    holdings = []
    for h_data in req.holdings:
        holdings.append(PortfolioHolding.from_dict(h_data))

    new_p = UserPortfolio(
        portfolio_id=f"pf_{uuid.uuid4().hex[:12]}",
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        name=req.name.strip(),
        description=req.description,
        holdings=holdings,
    )
    saved = portfolio_repo.create(new_p)
    return _to_portfolio_schema(saved)


@router.get(
    "/default",
    response_model=UserPortfolioSchema,
    summary="Get or create default portfolio",
)
def get_default_portfolio(
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> UserPortfolioSchema:
    p = portfolio_repo.get_or_create_default(user_id=current_user.user_id, tenant_id=current_user.tenant_id)
    return _to_portfolio_schema(p)


@router.get(
    "/exposure",
    response_model=PortfolioLegislativeExposureResponse,
    summary="Get portfolio legislative exposure summary (default portfolio)",
    description="Analyze user portfolio against Central and State legislative developments with explainable relevance tiers.",
)
def get_default_portfolio_exposure(
    current_user: CurrentUser = Depends(get_current_user),
    decision_service: DecisionIntelligenceService = Depends(get_decision_intelligence_service),
) -> PortfolioLegislativeExposureResponse:
    summary = decision_service.get_portfolio_legislative_exposure(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
    )
    return PortfolioLegislativeExposureResponse(**summary.to_dict())


@router.get(
    "/{portfolio_id}",
    response_model=UserPortfolioSchema,
    summary="Get specific portfolio",
)
def get_portfolio(
    portfolio_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> UserPortfolioSchema:
    p = portfolio_repo.get(portfolio_id=portfolio_id, tenant_id=current_user.tenant_id, user_id=current_user.user_id)
    if not p:
        raise NotFoundError("PORTFOLIO_NOT_FOUND", f"Portfolio '{portfolio_id}' not found or access denied.")
    return _to_portfolio_schema(p)


@router.put(
    "/{portfolio_id}",
    response_model=UserPortfolioSchema,
    summary="Update portfolio details",
)
def update_portfolio(
    portfolio_id: str,
    req: UpdatePortfolioRequest,
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> UserPortfolioSchema:
    p = portfolio_repo.get(portfolio_id=portfolio_id, tenant_id=current_user.tenant_id, user_id=current_user.user_id)
    if not p:
        raise NotFoundError("PORTFOLIO_NOT_FOUND", f"Portfolio '{portfolio_id}' not found.")

    if req.name is not None:
        p.name = req.name.strip()
    if req.description is not None:
        p.description = req.description
    if req.is_active is not None:
        p.is_active = req.is_active

    saved = portfolio_repo.update(p)
    return _to_portfolio_schema(saved)


@router.delete(
    "/{portfolio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete portfolio",
)
def delete_portfolio(
    portfolio_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
):
    deleted = portfolio_repo.delete(portfolio_id=portfolio_id, tenant_id=current_user.tenant_id, user_id=current_user.user_id)
    if not deleted:
        raise NotFoundError("PORTFOLIO_NOT_FOUND", f"Portfolio '{portfolio_id}' not found.")
    return None


@router.post(
    "/{portfolio_id}/holdings",
    response_model=PortfolioHoldingSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Add a holding to portfolio",
)
def add_holding(
    portfolio_id: str,
    req: AddHoldingRequest,
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> PortfolioHoldingSchema:
    h = PortfolioHolding(
        holding_id=f"h_{uuid.uuid4().hex[:8]}",
        company_name=req.company_name.strip(),
        ticker=req.ticker,
        isin=req.isin,
        quantity=req.quantity,
        avg_purchase_price=req.avg_purchase_price,
        current_value=req.current_value,
        sector=req.sector,
        industry=req.industry,
        notes=req.notes,
    )
    try:
        saved_h = portfolio_repo.add_holding(
            portfolio_id=portfolio_id,
            holding=h,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
        )
        return PortfolioHoldingSchema(**saved_h.to_dict())
    except KeyError:
        raise NotFoundError("PORTFOLIO_NOT_FOUND", f"Portfolio '{portfolio_id}' not found.")


@router.put(
    "/{portfolio_id}/holdings/{holding_id}",
    response_model=PortfolioHoldingSchema,
    summary="Update holding in portfolio",
)
def update_holding(
    portfolio_id: str,
    holding_id: str,
    req: UpdateHoldingRequest,
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> PortfolioHoldingSchema:
    updated = portfolio_repo.update_holding(
        portfolio_id=portfolio_id,
        holding_id=holding_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        updates=req.model_dump(exclude_unset=True),
    )
    if not updated:
        raise NotFoundError("HOLDING_NOT_FOUND", f"Holding '{holding_id}' not found in portfolio '{portfolio_id}'.")
    return PortfolioHoldingSchema(
        holding_id=updated.holding_id,
        company_name=updated.company_name,
        ticker=updated.ticker,
        isin=updated.isin,
        quantity=updated.quantity,
        avg_purchase_price=updated.avg_purchase_price,
        current_value=updated.current_value,
        sector=updated.sector,
        industry=updated.industry,
        notes=updated.notes,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete(
    "/{portfolio_id}/holdings/{holding_id}",
    summary="Remove holding from portfolio",
)
def remove_holding(
    portfolio_id: str,
    holding_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> dict[str, Any]:
    removed = portfolio_repo.remove_holding(
        portfolio_id=portfolio_id,
        holding_id=holding_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    if not removed:
        raise NotFoundError("HOLDING_NOT_FOUND", f"Holding '{holding_id}' not found in portfolio '{portfolio_id}'.")
    return {"success": True, "holding_id": holding_id}


@router.post(
    "/{portfolio_id}/import",
    response_model=UserPortfolioSchema,
    summary="Bulk import holdings into portfolio",
)
def import_holdings(
    portfolio_id: str,
    req: BulkImportHoldingsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repository),
) -> UserPortfolioSchema:
    import csv
    import io

    holdings: list[PortfolioHolding] = []

    if req.csv_content and req.csv_content.strip():
        reader = csv.DictReader(io.StringIO(req.csv_content.strip()))
        for row in reader:
            c_name = row.get("company_name", "").strip()
            if not c_name:
                continue
            qty = None
            if row.get("quantity"):
                try:
                    qty = float(row["quantity"])
                except ValueError:
                    pass
            price = None
            if row.get("avg_purchase_price"):
                try:
                    price = float(row["avg_purchase_price"])
                except ValueError:
                    pass
            holdings.append(
                PortfolioHolding(
                    holding_id=f"h_{uuid.uuid4().hex[:8]}",
                    company_name=c_name,
                    ticker=row.get("ticker") or None,
                    isin=row.get("isin") or None,
                    quantity=qty,
                    avg_purchase_price=price,
                    sector=row.get("sector") or None,
                    industry=row.get("industry") or None,
                    notes=row.get("notes") or None,
                )
            )
    elif req.holdings:
        holdings = [
            PortfolioHolding(
                holding_id=f"h_{uuid.uuid4().hex[:8]}",
                company_name=h.company_name.strip(),
                ticker=h.ticker,
                isin=h.isin,
                quantity=h.quantity,
                avg_purchase_price=h.avg_purchase_price,
                current_value=h.current_value,
                sector=h.sector,
                industry=h.industry,
                notes=h.notes,
            )
            for h in req.holdings
        ]

    should_replace = req.replace or bool(req.replace_existing)

    try:
        updated_p = portfolio_repo.import_holdings(
            portfolio_id=portfolio_id,
            holdings=holdings,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            replace=should_replace,
        )
        return _to_portfolio_schema(updated_p)
    except KeyError:
        raise NotFoundError("PORTFOLIO_NOT_FOUND", f"Portfolio '{portfolio_id}' not found.")


@router.get(
    "/{portfolio_id}/exposure",
    response_model=PortfolioLegislativeExposureResponse,
    summary="Get legislative exposure for specific portfolio",
)
def get_portfolio_exposure(
    portfolio_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    decision_service: DecisionIntelligenceService = Depends(get_decision_intelligence_service),
) -> PortfolioLegislativeExposureResponse:
    summary = decision_service.get_portfolio_legislative_exposure(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        portfolio_id=portfolio_id,
    )
    return PortfolioLegislativeExposureResponse(**summary.to_dict())


@router.get(
    "/{portfolio_id}/report",
    response_model=PersonalizedImpactReportResponse,
    summary="Generate or retrieve 'MY LEGISLATIVE IMPACT REPORT' for portfolio",
)
@router.post(
    "/{portfolio_id}/report",
    response_model=PersonalizedImpactReportResponse,
    summary="Generate 'MY LEGISLATIVE IMPACT REPORT' for portfolio",
)
def generate_portfolio_report(
    portfolio_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    decision_service: DecisionIntelligenceService = Depends(get_decision_intelligence_service),
) -> PersonalizedImpactReportResponse:
    report_data = decision_service.generate_personalized_report(
        user_id=current_user.user_id,
        tenant_id=current_user.tenant_id,
        portfolio_id=portfolio_id,
    )
    return PersonalizedImpactReportResponse(**report_data.to_dict())
