"""
api/routers/anticipation.py
===========================
REST API router for Pre-Event Information Diffusion and Anticipation Bias Analytics (Task 8.14.7).

Guarantees:
- Strict neutral institutional terminology: never accuses any entity of insider trading or wrongdoing.
- Verbatim institutional disclaimer on all diagnostic payloads.
- Consumes the 940 frozen AnticipationScore records without recalculation.
- State bills and intelligence-only entities are strictly firewalled (0 anticipation diagnostics).
"""

from __future__ import annotations

import math
from typing import Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    get_anticipation_repository,
    get_cached_anticipation_scores,
    get_company_intelligence_service,
    get_discovery_service,
)
from api.errors import NotFoundError
from api.schemas import (
    AnticipationItem,
    AnticipationScoreResponse,
    AnticipationSectorSummary,
    AnticipationSummaryResponse,
    FlaggedAnticipationPair,
    PaginatedResponse,
    PreEventWindowSummary,
)
from schemas.anticipation import AnticipationScore
from services.company_intelligence_service import CompanyIntelligenceService
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from storage.anticipation_repository import AnticipationRepository

router = APIRouter(prefix="/anticipation", tags=["Anticipation Analytics"])

INSTITUTIONAL_DISCLAIMER = (
    "Pre-event diagnostics measure aggregate public information diffusion only. "
    "They do not allege or imply insider trading or illicit market conduct under securities law."
)


def _to_anticipation_item(
    s: AnticipationScore,
    company_service: Optional[CompanyIntelligenceService] = None,
) -> AnticipationItem:
    c_name = None
    c_sym = s.company_symbol
    sec = None

    if company_service:
        comp = company_service.company_repo.get_by_isin(s.company_isin)
        if comp:
            c_name = comp.company_name
            c_sym = comp.ticker_nse or comp.ticker_bse or s.company_symbol
            sec = comp.sector

    return AnticipationItem(
        bill_id=s.bill_id,
        bill_title=s.bill_id.replace("-", " ").title(),
        company_isin=s.company_isin,
        company_name=c_name or s.company_symbol,
        company_symbol=c_sym,
        sector=sec or "General",
        official_introduction_date=s.official_introduction_date,
        anticipation_score=round(float(s.anticipation_score), 4),
        classification=str(s.classification),
        anticipation_flag=bool(s.anticipation_flag),
        confidence=str(s.confidence),
        market_signal_score=round(float(s.market_signal_score), 4),
        information_signal_score=round(float(s.information_signal_score), 4),
        evidence_count=int(s.evidence_count),
        media_data_available=bool(s.media_data_available),
        decision_reason=s.decision_reason,
        detected_signals=list(s.detected_signals),
        calculation_timestamp=getattr(s, "calculation_timestamp", ""),
    )


@router.get(
    "",
    response_model=PaginatedResponse[AnticipationItem],
    summary="List pre-event anticipation diagnostics",
    description="Paginated, filterable listing of the 940 frozen bill-company anticipation evaluation records.",
)
def list_anticipation_scores(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    bill_id: Optional[str] = Query(None, description="Filter by bill ID"),
    company_isin: Optional[str] = Query(None, description="Filter by company ISIN"),
    classification: Optional[str] = Query(None, description="Filter by tier: NO_EVIDENCE, WEAK_EVIDENCE, MODERATE_EVIDENCE, STRONG_EVIDENCE"),
    flagged_only: Optional[bool] = Query(None, description="Filter flagged anticipation relationships only"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum anticipation score threshold"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction ('central' or 'state')"),
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> PaginatedResponse[AnticipationItem]:
    # State Firewall: State bills strictly have 0 market anticipation models
    if jurisdiction and jurisdiction.strip().lower() in {"state", "state_bill", "states"}:
        return PaginatedResponse[AnticipationItem](
            items=[],
            total=0,
            page=page,
            limit=limit,
            pages=0,
        )

    all_scores = get_cached_anticipation_scores()

    filtered: list[AnticipationScore] = []
    b_clean = bill_id.strip().lower() if bill_id else None
    isin_clean = company_isin.strip().upper() if company_isin else None
    tier_clean = classification.strip().upper() if classification else None
    sec_clean = sector.strip().lower() if sector else None

    # Cache company sectors for fast filtering
    company_sectors: dict[str, str] = {}
    if sec_clean:
        for comp in company_service.company_repo.get_all():
            if comp.isin:
                company_sectors[comp.isin.upper()] = comp.sector.lower()

    for s in all_scores:
        if b_clean and s.bill_id.lower() != b_clean:
            continue
        if isin_clean and s.company_isin.upper() != isin_clean:
            continue
        if tier_clean and str(s.classification).upper() != tier_clean:
            continue
        if flagged_only is not None and bool(s.anticipation_flag) != flagged_only:
            continue
        if min_score is not None and s.anticipation_score < min_score:
            continue
        if sec_clean:
            comp_sec = company_sectors.get(s.company_isin.upper(), "")
            if sec_clean not in comp_sec:
                continue

        filtered.append(s)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit
    items = [_to_anticipation_item(s, company_service) for s in filtered[start:end]]

    return PaginatedResponse[AnticipationItem](
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=total_pages,
    )


@router.get(
    "/summary",
    response_model=AnticipationSummaryResponse,
    summary="Get aggregated anticipation analytics summary",
    description="Returns classification distribution, sector breakdown, multi-window stats, and institutional disclaimer.",
)
def get_anticipation_summary(
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> AnticipationSummaryResponse:
    all_scores = get_cached_anticipation_scores()

    if not all_scores:
        return AnticipationSummaryResponse(
            total_pairs=0,
            flagged_pairs_count=0,
            avg_anticipation_score=0.0,
            avg_market_signal=0.0,
            avg_information_signal=0.0,
            classification_distribution={},
            sector_distribution=[],
            window_stats_distribution=[],
            top_flagged_pairs=[],
            disclaimer=INSTITUTIONAL_DISCLAIMER,
        )

    # Classifications
    tier_counts: dict[str, int] = {
        "NO_EVIDENCE": 0,
        "WEAK_EVIDENCE": 0,
        "MODERATE_EVIDENCE": 0,
        "STRONG_EVIDENCE": 0,
    }
    flagged_count = 0
    total_score = 0.0
    total_market = 0.0
    total_info = 0.0

    # Sector grouping
    by_sector: dict[str, list[AnticipationScore]] = {}

    # Window stats aggregation across [-30,-21], [-20,-11], [-10,-3], [-2,-1], [-30,-1]
    window_mars: dict[str, list[float]] = {}
    window_cars: dict[str, list[float]] = {}
    window_sig_counts: dict[str, int] = {}
    window_obs_counts: dict[str, list[int]] = {}

    for s in all_scores:
        tier = str(s.classification)
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        if s.anticipation_flag:
            flagged_count += 1

        total_score += float(s.anticipation_score)
        total_market += float(s.market_signal_score)
        total_info += float(s.information_signal_score)

        comp = company_service.company_repo.get_by_isin(s.company_isin)
        sec = comp.sector if comp else "General"
        by_sector.setdefault(sec, []).append(s)

        # Aggregate pre-event window statistics if present
        for w_name, w_stat in getattr(s, "window_stats", {}).items():
            window_mars.setdefault(w_name, []).append(float(getattr(w_stat, "mean_abnormal_return", 0.0)))
            window_cars.setdefault(w_name, []).append(float(getattr(w_stat, "cumulative_abnormal_return", 0.0)))
            if getattr(w_stat, "is_statistically_significant", False):
                window_sig_counts[w_name] = window_sig_counts.get(w_name, 0) + 1
            window_obs_counts.setdefault(w_name, []).append(int(getattr(w_stat, "observation_count", 0)))

    n = len(all_scores)
    avg_score = round(total_score / n, 4)
    avg_market = round(total_market / n, 4)
    avg_info = round(total_info / n, 4)

    # Sector summaries
    sector_summaries: list[AnticipationSectorSummary] = []
    for sec, scores in sorted(by_sector.items(), key=lambda x: len(x[1]), reverse=True):
        sec_tiers: dict[str, int] = {}
        for sc in scores:
            sec_tiers[str(sc.classification)] = sec_tiers.get(str(sc.classification), 0) + 1
        sector_summaries.append(
            AnticipationSectorSummary(
                sector=sec,
                pair_count=len(scores),
                avg_anticipation_score=round(sum(float(x.anticipation_score) for x in scores) / len(scores), 4),
                flagged_count=sum(1 for x in scores if x.anticipation_flag),
                classification_counts=sec_tiers,
            )
        )

    # Window summaries
    window_order = ["[-30,-21]", "[-20,-11]", "[-10,-3]", "[-2,-1]", "[-30,-1]"]
    window_summaries: list[PreEventWindowSummary] = []
    for w_name in window_order:
        if w_name in window_cars and window_cars[w_name]:
            cars = window_cars[w_name]
            mars = window_mars.get(w_name, [0.0])
            obs = window_obs_counts.get(w_name, [0])
            window_summaries.append(
                PreEventWindowSummary(
                    window=w_name,
                    mean_mar=round(sum(mars) / len(mars), 6),
                    mean_car=round(sum(cars) / len(cars), 6),
                    significant_pairs_count=window_sig_counts.get(w_name, 0),
                    observation_count=int(sum(obs) / len(obs)) if obs else 0,
                )
            )

    # Top flagged pairs
    flagged_sorted = sorted(all_scores, key=lambda x: x.anticipation_score, reverse=True)[:10]
    top_flagged: list[FlaggedAnticipationPair] = []
    for fl in flagged_sorted:
        comp = company_service.company_repo.get_by_isin(fl.company_isin)
        top_flagged.append(
            FlaggedAnticipationPair(
                bill_id=fl.bill_id,
                bill_title=fl.bill_id.replace("-", " ").title(),
                company_isin=fl.company_isin,
                company_name=comp.company_name if comp else fl.company_symbol,
                company_symbol=comp.ticker_nse or fl.company_symbol if comp else fl.company_symbol,
                sector=comp.sector if comp else "General",
                anticipation_score=round(float(fl.anticipation_score), 4),
                classification=str(fl.classification),
                detected_signals=list(fl.detected_signals),
            )
        )

    return AnticipationSummaryResponse(
        total_pairs=n,
        flagged_pairs_count=flagged_count,
        avg_anticipation_score=avg_score,
        avg_market_signal=avg_market,
        avg_information_signal=avg_info,
        classification_distribution=tier_counts,
        sector_distribution=sector_summaries,
        window_stats_distribution=window_summaries,
        top_flagged_pairs=top_flagged,
        disclaimer=INSTITUTIONAL_DISCLAIMER,
    )


@router.get(
    "/{bill_id}/{company_isin}",
    response_model=AnticipationScoreResponse,
    summary="Get single bill-company anticipation evaluation",
    description="Retrieve anticipation diagnostic detail for a specific Central bill and quantitative company pair.",
)
def get_anticipation_pair_detail(
    bill_id: str,
    company_isin: str,
    anticipation_repo: AnticipationRepository = Depends(get_anticipation_repository),
) -> AnticipationScoreResponse:
    score = anticipation_repo.get_score(bill_id, company_isin)
    if not score:
        raise NotFoundError(
            code="ANTICIPATION_NOT_FOUND",
            message=f"Anticipation diagnostic for pair ({bill_id}, {company_isin}) not found.",
        )

    ev_claims = list(getattr(score, "detected_signals", []))
    car_val = 0.0
    if hasattr(score, "window_stats") and "[-30,-1]" in score.window_stats:
        car_val = round(float(score.window_stats["[-30,-1]"].cumulative_abnormal_return), 4)

    return AnticipationScoreResponse(
        bill_id=score.bill_id,
        company_isin=score.company_isin,
        anticipation_score=round(float(score.anticipation_score), 4),
        anticipation_tier=str(score.classification),
        diffusion_index=round(float(score.information_signal_score), 4),
        pre_event_volume_ratio=round(float(score.market_signal_score), 4),
        pre_event_car=car_val,
        leakage_indicator=bool(score.anticipation_flag),
        evidence_summary=ev_claims,
    )
