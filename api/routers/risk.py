"""
api/routers/risk.py
===================
REST API router for Decision Support Risk Scoring, Risk Band Aggregations,
and Portfolio-Level Risk Diagnostics (Task 8.14.7).

Guarantees:
- Strict mathematical fidelity to frozen DecisionSupportRecord outputs.
- No client-side recalculation of risk scores or thresholds.
- Non-political research orientation: financial/econometric risk only.
- State legislation risk remains strictly qualitative with 0 stock risk models.
- Institutional disclaimer on all payloads.
"""

from __future__ import annotations

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    CurrentUser,
    get_cached_decisions_by_id,
    get_company_intelligence_service,
    get_current_user,
    get_watchlist_service,
)
from api.schemas import (
    BillRiskSummary,
    CompanyRiskSummary,
    EventWindowRiskSummary,
    PortfolioCompanyRiskItem,
    PortfolioRiskRequest,
    PortfolioRiskResponse,
    RiskBandDistribution,
    RiskSummaryResponse,
    SectorRiskSummary,
)
from services.company_intelligence_service import CompanyIntelligenceService
from services.watchlist_service import WatchlistService

router = APIRouter(prefix="/risk", tags=["Risk Analytics"])

DISCLAIMER = "This is a model-derived risk indicator, not a recommendation."


def _classify_band(score: float) -> str:
    if score < 0.20:
        return "VERY_LOW"
    elif score < 0.40:
        return "LOW"
    elif score < 0.60:
        return "MODERATE"
    elif score < 0.80:
        return "HIGH"
    else:
        return "VERY_HIGH"


@router.get(
    "/summary",
    response_model=RiskSummaryResponse,
    summary="Get platform-wide risk analytics summary",
    description="Returns pre-aggregated risk distribution, sector breakdown, horizon breakdown, and bill/company risk metrics.",
)
def get_risk_summary() -> RiskSummaryResponse:
    decisions_cache = get_cached_decisions_by_id()
    all_decisions = list(decisions_cache.values())

    if not all_decisions:
        return RiskSummaryResponse(
            total_decisions=0,
            avg_overall_risk=0.0,
            risk_band_distribution=RiskBandDistribution(),
            pricing_in_distribution={},
            risk_by_sector=[],
            risk_by_event_window=[],
            risk_by_bill=[],
            risk_by_company=[],
            disclaimer=DISCLAIMER,
        )

    # 1. Overall Distribution & Pricing-in
    band_dist = {"VERY_LOW": 0, "LOW": 0, "MODERATE": 0, "HIGH": 0, "VERY_HIGH": 0}
    pricing_dist: dict[str, int] = {}
    total_risk = 0.0

    # Groupings
    by_sector: dict[str, list[float]] = {}
    sector_bands: dict[str, dict[str, int]] = {}
    by_window: dict[str, list[float]] = {}
    window_bands: dict[str, dict[str, int]] = {}
    by_bill: dict[str, list[dict]] = {}
    by_company: dict[str, list[dict]] = {}

    for d in all_decisions:
        r_score = float(d.risk_score)
        total_risk += r_score
        band = d.risk_category if d.risk_category in band_dist else _classify_band(r_score)
        band_dist[band] = band_dist.get(band, 0) + 1

        p_risk = str(d.pricing_in_risk)
        pricing_dist[p_risk] = pricing_dist.get(p_risk, 0) + 1

        # Sector
        sec = d.sector or "General"
        by_sector.setdefault(sec, []).append(r_score)
        sector_bands.setdefault(sec, {"VERY_LOW": 0, "LOW": 0, "MODERATE": 0, "HIGH": 0, "VERY_HIGH": 0})
        sector_bands[sec][band] = sector_bands[sec].get(band, 0) + 1

        # Event Window
        ew = d.event_window
        by_window.setdefault(ew, []).append(r_score)
        window_bands.setdefault(ew, {"VERY_LOW": 0, "LOW": 0, "MODERATE": 0, "HIGH": 0, "VERY_HIGH": 0})
        window_bands[ew][band] = window_bands[ew].get(band, 0) + 1

        # Bill
        by_bill.setdefault(d.bill_id, []).append({
            "risk_score": r_score,
            "risk_category": band,
        })

        # Company
        by_company.setdefault(d.company_isin, []).append({
            "company_name": d.company_name,
            "company_symbol": d.company_symbol,
            "sector": sec,
            "risk_score": r_score,
            "risk_category": band,
        })

    avg_overall = round(total_risk / len(all_decisions), 4)

    # Build sector summaries
    sector_summaries = [
        SectorRiskSummary(
            sector=sec,
            avg_risk_score=round(sum(scores) / len(scores), 4),
            record_count=len(scores),
            band_distribution=RiskBandDistribution(**sector_bands[sec]),
        )
        for sec, scores in sorted(by_sector.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)
    ]

    # Build window summaries
    window_order = ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"]
    window_summaries = [
        EventWindowRiskSummary(
            event_window=ew,
            avg_risk_score=round(sum(by_window[ew]) / len(by_window[ew]), 4) if ew in by_window else 0.0,
            record_count=len(by_window.get(ew, [])),
            band_distribution=RiskBandDistribution(**window_bands.get(ew, {})),
        )
        for ew in window_order if ew in by_window
    ]

    # Build bill summaries
    bill_summaries = []
    for b_id, items in by_bill.items():
        scores = [it["risk_score"] for it in items]
        high_count = sum(1 for it in items if it["risk_category"] in {"HIGH", "VERY_HIGH"})
        avg_r = round(sum(scores) / len(scores), 4)
        bill_summaries.append(
            BillRiskSummary(
                bill_id=b_id,
                bill_title=b_id.replace("-", " ").title(),
                jurisdiction="central",
                avg_risk_score=avg_r,
                max_risk_score=round(max(scores), 4),
                high_risk_count=high_count,
                record_count=len(scores),
                dominant_risk_band=_classify_band(avg_r),
            )
        )
    bill_summaries.sort(key=lambda x: x.avg_risk_score, reverse=True)

    # Build company summaries
    company_summaries = []
    for isin, items in by_company.items():
        scores = [it["risk_score"] for it in items]
        avg_r = round(sum(scores) / len(scores), 4)
        company_summaries.append(
            CompanyRiskSummary(
                company_isin=isin,
                company_name=items[0]["company_name"] or isin,
                company_symbol=items[0]["company_symbol"] or isin[:6],
                sector=items[0]["sector"],
                universe_type="quantitative",
                avg_risk_score=avg_r,
                max_risk_score=round(max(scores), 4),
                record_count=len(scores),
                dominant_risk_band=_classify_band(avg_r),
                market_prediction_available=True,
            )
        )
    company_summaries.sort(key=lambda x: x.avg_risk_score, reverse=True)

    return RiskSummaryResponse(
        total_decisions=len(all_decisions),
        avg_overall_risk=avg_overall,
        risk_band_distribution=RiskBandDistribution(**band_dist),
        pricing_in_distribution=pricing_dist,
        risk_by_sector=sector_summaries,
        risk_by_event_window=window_summaries,
        risk_by_bill=bill_summaries,
        risk_by_company=company_summaries,
        disclaimer=DISCLAIMER,
    )


@router.get(
    "/bills",
    response_model=list[BillRiskSummary],
    summary="List bill risk profiles",
)
def list_risk_bills(
    q: Optional[str] = Query(None, description="Search bill title or ID"),
) -> list[BillRiskSummary]:
    summary = get_risk_summary()
    bills = summary.risk_by_bill
    if q:
        q_clean = q.strip().lower()
        bills = [b for b in bills if q_clean in b.bill_id.lower() or q_clean in b.bill_title.lower()]
    return bills


@router.get(
    "/companies",
    response_model=list[CompanyRiskSummary],
    summary="List company risk profiles",
)
def list_risk_companies(
    q: Optional[str] = Query(None, description="Search company name, symbol, or ISIN"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
) -> list[CompanyRiskSummary]:
    summary = get_risk_summary()
    comps = summary.risk_by_company
    if q:
        q_clean = q.strip().lower()
        comps = [
            c for c in comps
            if q_clean in c.company_name.lower() or q_clean in c.company_symbol.lower() or q_clean in c.company_isin.lower()
        ]
    if sector:
        sec_clean = sector.strip().lower()
        comps = [c for c in comps if sec_clean in c.sector.lower()]
    return comps


@router.post(
    "/portfolio",
    response_model=PortfolioRiskResponse,
    summary="Portfolio-level risk analysis across selected or watchlist companies",
    description="Calculates composite risk metrics using only actual Central decision support records. Returns 'Insufficient data' if no quantitative companies match.",
)
def analyze_portfolio_risk(
    req: PortfolioRiskRequest,
    current_user: Optional[CurrentUser] = Depends(get_current_user),
    watchlist_service: WatchlistService = Depends(get_watchlist_service),
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> PortfolioRiskResponse:
    target_isins: set[str] = {isin.strip().upper() for isin in req.company_isins if isin.strip()}

    # Resolve watchlist if requested
    if req.watchlist_id:
        try:
            tenant_id = current_user.tenant_id if current_user else "default_tenant"
            user_id = current_user.user_id if current_user else "default_user"
            items = watchlist_service.watchlist_repo.list_items_by_watchlist(
                req.watchlist_id, tenant_id=tenant_id, user_id=user_id, is_active=True
            )
            for it in items:
                # Could be company ISIN or ticker or ID
                comp = company_service.company_repo.get_by_isin(it.entity_id) or company_service.company_repo.get_by_ticker(it.entity_id)
                if comp and comp.isin:
                    target_isins.add(comp.isin.upper())
                elif it.entity_id.startswith("INE"):
                    target_isins.add(it.entity_id.upper())
        except Exception:
            pass

    if not target_isins:
        return PortfolioRiskResponse(
            selected_companies_count=0,
            modeled_companies_count=0,
            unmodeled_companies_count=0,
            total_exposure_records=0,
            avg_portfolio_risk_score=None,
            portfolio_risk_band=None,
            has_sufficient_data=False,
            data_status="INSUFFICIENT_DATA",
            risk_band_distribution=RiskBandDistribution(),
            sector_breakdown=[],
            jurisdiction_breakdown={"central": 0, "state": 0},
            companies=[],
            message="No companies were selected or found in the specified criteria.",
        )

    decisions_cache = get_cached_decisions_by_id()
    all_decisions = list(decisions_cache.values())

    modeled_decisions = [d for d in all_decisions if d.company_isin.upper() in target_isins]

    # Map companies detail
    company_items: list[PortfolioCompanyRiskItem] = []
    modeled_isins_found: set[str] = set()

    # Group decisions by company
    company_decs: dict[str, list[float]] = {}
    company_meta: dict[str, dict] = {}
    for d in modeled_decisions:
        isin = d.company_isin.upper()
        modeled_isins_found.add(isin)
        company_decs.setdefault(isin, []).append(float(d.risk_score))
        if isin not in company_meta:
            company_meta[isin] = {
                "name": d.company_name or isin,
                "symbol": d.company_symbol or isin[:6],
                "sector": d.sector or "General",
            }

    for isin in sorted(target_isins):
        if isin in modeled_isins_found:
            scores = company_decs[isin]
            avg_s = round(sum(scores) / len(scores), 4)
            company_items.append(
                PortfolioCompanyRiskItem(
                    company_isin=isin,
                    company_name=company_meta[isin]["name"],
                    company_symbol=company_meta[isin]["symbol"],
                    sector=company_meta[isin]["sector"],
                    universe_type="quantitative",
                    is_modeled=True,
                    record_count=len(scores),
                    avg_risk_score=avg_s,
                    dominant_risk_band=_classify_band(avg_s),
                )
            )
        else:
            # Check company service
            comp_obj = company_service.company_repo.get_by_isin(isin)
            c_name = comp_obj.company_name if comp_obj else isin
            c_sym = comp_obj.ticker_nse or isin[:6] if comp_obj else isin[:6]
            c_sec = comp_obj.sector if comp_obj else "Unspecified"
            u_type = comp_obj.universe_type.value if comp_obj and hasattr(comp_obj.universe_type, "value") else (str(comp_obj.universe_type) if comp_obj else "intelligence")

            company_items.append(
                PortfolioCompanyRiskItem(
                    company_isin=isin,
                    company_name=c_name,
                    company_symbol=c_sym,
                    sector=c_sec,
                    universe_type=u_type,
                    is_modeled=False,
                    record_count=0,
                    avg_risk_score=None,
                    dominant_risk_band=None,
                )
            )

    modeled_count = len(modeled_isins_found)
    unmodeled_count = len(target_isins) - modeled_count

    if not modeled_decisions:
        return PortfolioRiskResponse(
            selected_companies_count=len(target_isins),
            modeled_companies_count=0,
            unmodeled_companies_count=unmodeled_count,
            total_exposure_records=0,
            avg_portfolio_risk_score=None,
            portfolio_risk_band=None,
            has_sufficient_data=False,
            data_status="INSUFFICIENT_DATA",
            risk_band_distribution=RiskBandDistribution(),
            sector_breakdown=[],
            jurisdiction_breakdown={"central": 0, "state": 0},
            companies=company_items,
            message="Insufficient data: None of the selected entities have quantitative equity prediction models.",
        )

    all_scores = [float(d.risk_score) for d in modeled_decisions]
    avg_portfolio_risk = round(sum(all_scores) / len(all_scores), 4)

    # Risk band distribution
    band_dist = {"VERY_LOW": 0, "LOW": 0, "MODERATE": 0, "HIGH": 0, "VERY_HIGH": 0}
    by_sec_scores: dict[str, list[float]] = {}
    by_sec_bands: dict[str, dict[str, int]] = {}

    for d in modeled_decisions:
        s = float(d.risk_score)
        b = d.risk_category if d.risk_category in band_dist else _classify_band(s)
        band_dist[b] = band_dist.get(b, 0) + 1

        sec = d.sector or "General"
        by_sec_scores.setdefault(sec, []).append(s)
        by_sec_bands.setdefault(sec, {"VERY_LOW": 0, "LOW": 0, "MODERATE": 0, "HIGH": 0, "VERY_HIGH": 0})
        by_sec_bands[sec][b] = by_sec_bands[sec].get(b, 0) + 1

    sector_summaries = [
        SectorRiskSummary(
            sector=sec,
            avg_risk_score=round(sum(scores) / len(scores), 4),
            record_count=len(scores),
            band_distribution=RiskBandDistribution(**by_sec_bands[sec]),
        )
        for sec, scores in sorted(by_sec_scores.items(), key=lambda x: sum(x[1]) / len(x[1]), reverse=True)
    ]

    return PortfolioRiskResponse(
        selected_companies_count=len(target_isins),
        modeled_companies_count=modeled_count,
        unmodeled_companies_count=unmodeled_count,
        total_exposure_records=len(modeled_decisions),
        avg_portfolio_risk_score=avg_portfolio_risk,
        portfolio_risk_band=_classify_band(avg_portfolio_risk),
        has_sufficient_data=True,
        data_status="SUFFICIENT_DATA",
        risk_band_distribution=RiskBandDistribution(**band_dist),
        sector_breakdown=sector_summaries,
        jurisdiction_breakdown={"central": len(modeled_decisions), "state": 0},
        companies=company_items,
        message=f"Aggregated across {modeled_count} quantitative securities ({len(modeled_decisions)} observation records).",
    )
