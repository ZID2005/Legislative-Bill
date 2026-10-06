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
    get_anticipation_evidence_repository,
    get_anticipation_evidence_service,
    get_anticipation_repository,
    get_cached_anticipation_scores,
    get_company_intelligence_service,
    get_discovery_service,
)
from api.errors import NotFoundError
from api.schemas import (
    AnticipationEvidenceContextResponse,
    AnticipationItem,
    AnticipationScoreResponse,
    AnticipationSectorSummary,
    AnticipationSummaryResponse,
    CombinedContextSummaryResponse,
    FlaggedAnticipationPair,
    MarketSignalSummaryResponse,
    PaginatedResponse,
    PreEventWindowSummary,
    PublicInformationEvidenceResponse,
    PublicInformationSignalSummaryResponse,
    SearchTrendItemResponse,
)
from schemas.anticipation import AnticipationScore
from services.anticipation_evidence.evidence_repository import AnticipationEvidenceRepository
from services.anticipation_evidence.evidence_service import AnticipationEvidenceService
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
    "/evidence",
    response_model=PaginatedResponse[PublicInformationEvidenceResponse],
    summary="List public information evidence records",
    description="Query verified, provenance-traceable public information records surrounding legislative measures.",
)
def list_evidence(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(25, ge=1, le=100, description="Items per page"),
    bill_id: Optional[str] = Query(None, description="Filter by bill ID"),
    company_isin: Optional[str] = Query(None, description="Filter by company ISIN"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    credibility_tier: Optional[str] = Query(None, description="Filter by credibility tier"),
    temporal_relation: Optional[str] = Query(None, description="Filter by temporal status (PRE_EVENT, SAME_DAY, etc.)"),
    verification_status: Optional[str] = Query(None, description="Filter by verification status"),
    evidence_repo: AnticipationEvidenceRepository = Depends(get_anticipation_evidence_repository),
) -> PaginatedResponse[PublicInformationEvidenceResponse]:
    all_ev = evidence_repo.get_all_evidence()

    filtered = []
    for ev in all_ev:
        if bill_id and ev.bill_id != bill_id:
            continue
        if company_isin and company_isin.upper() not in [e.upper() for e in ev.entity_matches]:
            continue
        if source_type and (ev.source_type.value if hasattr(ev.source_type, "value") else str(ev.source_type)) != source_type:
            continue
        if credibility_tier and (ev.source_credibility.value if hasattr(ev.source_credibility, "value") else str(ev.source_credibility)) != credibility_tier:
            continue
        if temporal_relation and (ev.temporal_relation.value if hasattr(ev.temporal_relation, "value") else str(ev.temporal_relation)) != temporal_relation:
            continue
        if verification_status and (ev.verification_status.value if hasattr(ev.verification_status, "value") else str(ev.verification_status)) != verification_status:
            continue
        filtered.append(ev)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    end = start + limit
    page_items = [
        PublicInformationEvidenceResponse(
            evidence_id=e.evidence_id,
            bill_id=e.bill_id,
            jurisdiction=e.jurisdiction,
            source_type=e.source_type.value if hasattr(e.source_type, "value") else str(e.source_type),
            source_name=e.source_name,
            source_url=e.source_url,
            publication_timestamp=e.publication_timestamp,
            discovery_timestamp=e.discovery_timestamp,
            event_reference=e.event_reference,
            headline=e.headline,
            summary=e.summary,
            relevance=round(float(e.relevance), 4),
            evidence_strength=e.evidence_strength.value if hasattr(e.evidence_strength, "value") else str(e.evidence_strength),
            temporal_relation=e.temporal_relation.value if hasattr(e.temporal_relation, "value") else str(e.temporal_relation),
            source_credibility=e.source_credibility.value if hasattr(e.source_credibility, "value") else str(e.source_credibility),
            entity_matches=list(e.entity_matches),
            sector_matches=list(e.sector_matches),
            keywords=list(e.keywords),
            hash=e.hash,
            provenance=dict(e.provenance),
            verification_status=e.verification_status.value if hasattr(e.verification_status, "value") else str(e.verification_status),
            duplicate_of=e.duplicate_of,
            canonical_evidence_id=e.canonical_evidence_id,
            match_reason=e.match_reason,
        )
        for e in filtered[start:end]
    ]

    return PaginatedResponse[PublicInformationEvidenceResponse](
        items=page_items,
        total=total,
        page=page,
        limit=limit,
        pages=total_pages,
    )


@router.get(
    "/evidence/{evidence_id}",
    response_model=PublicInformationEvidenceResponse,
    summary="Get single evidence record by ID",
    description="Retrieve detailed public information evidence record with provenance, hash, and match explanation.",
)
def get_evidence_item(
    evidence_id: str,
    evidence_repo: AnticipationEvidenceRepository = Depends(get_anticipation_evidence_repository),
) -> PublicInformationEvidenceResponse:
    ev = evidence_repo.get_evidence_by_id(evidence_id)
    if not ev:
        raise NotFoundError(
            code="EVIDENCE_NOT_FOUND",
            message=f"Public information evidence item '{evidence_id}' not found.",
        )
    return PublicInformationEvidenceResponse(
        evidence_id=ev.evidence_id,
        bill_id=ev.bill_id,
        jurisdiction=ev.jurisdiction,
        source_type=ev.source_type.value if hasattr(ev.source_type, "value") else str(ev.source_type),
        source_name=ev.source_name,
        source_url=ev.source_url,
        publication_timestamp=ev.publication_timestamp,
        discovery_timestamp=ev.discovery_timestamp,
        event_reference=ev.event_reference,
        headline=ev.headline,
        summary=ev.summary,
        relevance=round(float(ev.relevance), 4),
        evidence_strength=ev.evidence_strength.value if hasattr(ev.evidence_strength, "value") else str(ev.evidence_strength),
        temporal_relation=ev.temporal_relation.value if hasattr(ev.temporal_relation, "value") else str(ev.temporal_relation),
        source_credibility=ev.source_credibility.value if hasattr(ev.source_credibility, "value") else str(ev.source_credibility),
        entity_matches=list(ev.entity_matches),
        sector_matches=list(ev.sector_matches),
        keywords=list(ev.keywords),
        hash=ev.hash,
        provenance=dict(ev.provenance),
        verification_status=ev.verification_status.value if hasattr(ev.verification_status, "value") else str(ev.verification_status),
        duplicate_of=ev.duplicate_of,
        canonical_evidence_id=ev.canonical_evidence_id,
        match_reason=ev.match_reason,
    )


@router.get(
    "/context",
    response_model=AnticipationEvidenceContextResponse,
    summary="Get combined anticipation evidence context",
    description="Synthesize pre-event market signals with verified public information evidence.",
)
def get_anticipation_context(
    bill_id: str = Query(..., description="Legislative bill ID"),
    company_isin: Optional[str] = Query(None, description="Company ISIN (optional)"),
    evidence_service: AnticipationEvidenceService = Depends(get_anticipation_evidence_service),
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> AnticipationEvidenceContextResponse:
    bill = discovery_service.get_bill_by_id(bill_id)
    if not bill:
        raise NotFoundError(
            code="BILL_NOT_FOUND",
            message=f"Legislative bill '{bill_id}' not found.",
        )

    company_sym = None
    company_nm = None
    if company_isin:
        comp = company_service.company_repo.get_by_isin(company_isin)
        if comp:
            company_sym = comp.ticker_nse or comp.ticker_bse or comp.isin
            company_nm = comp.company_name

    ctx = evidence_service.build_evidence_context(
        bill=bill,
        company_isin=company_isin,
        company_symbol=company_sym,
        company_name=company_nm,
    )

    ev_resp_items = [
        PublicInformationEvidenceResponse(
            evidence_id=e.evidence_id,
            bill_id=e.bill_id,
            jurisdiction=e.jurisdiction,
            source_type=e.source_type.value if hasattr(e.source_type, "value") else str(e.source_type),
            source_name=e.source_name,
            source_url=e.source_url,
            publication_timestamp=e.publication_timestamp,
            discovery_timestamp=e.discovery_timestamp,
            event_reference=e.event_reference,
            headline=e.headline,
            summary=e.summary,
            relevance=round(float(e.relevance), 4),
            evidence_strength=e.evidence_strength.value if hasattr(e.evidence_strength, "value") else str(e.evidence_strength),
            temporal_relation=e.temporal_relation.value if hasattr(e.temporal_relation, "value") else str(e.temporal_relation),
            source_credibility=e.source_credibility.value if hasattr(e.source_credibility, "value") else str(e.source_credibility),
            entity_matches=list(e.entity_matches),
            sector_matches=list(e.sector_matches),
            keywords=list(e.keywords),
            hash=e.hash,
            provenance=dict(e.provenance),
            verification_status=e.verification_status.value if hasattr(e.verification_status, "value") else str(e.verification_status),
            duplicate_of=e.duplicate_of,
            canonical_evidence_id=e.canonical_evidence_id,
            match_reason=e.match_reason,
        )
        for e in ctx.evidence_items
    ]

    return AnticipationEvidenceContextResponse(
        bill_id=ctx.bill_id,
        company_isin=ctx.company_isin,
        company_symbol=ctx.company_symbol,
        jurisdiction=ctx.jurisdiction,
        market_signal=MarketSignalSummaryResponse(
            level=ctx.market_signal.level.value if hasattr(ctx.market_signal.level, "value") else str(ctx.market_signal.level),
            market_signal_score=round(float(ctx.market_signal.market_signal_score), 4),
            car_magnitude=round(float(ctx.market_signal.car_magnitude), 4),
            z_score=round(float(ctx.market_signal.z_score), 4),
            directional_persistence=round(float(ctx.market_signal.directional_persistence), 4),
            volatility=round(float(ctx.market_signal.volatility), 4),
            signals_detected=list(ctx.market_signal.signals_detected),
        ),
        public_information_signal=PublicInformationSignalSummaryResponse(
            level=ctx.public_information_signal.level.value if hasattr(ctx.public_information_signal.level, "value") else str(ctx.public_information_signal.level),
            public_information_evidence_score=round(float(ctx.public_information_signal.public_information_evidence_score), 4),
            verified_pre_event_count=int(ctx.public_information_signal.verified_pre_event_count),
            independent_sources_count=int(ctx.public_information_signal.independent_sources_count),
            source_diversity_ratio=round(float(ctx.public_information_signal.source_diversity_ratio), 4),
            credibility_tier_summary=dict(ctx.public_information_signal.credibility_tier_summary),
            earliest_evidence_date=ctx.public_information_signal.earliest_evidence_date,
            latest_evidence_date=ctx.public_information_signal.latest_evidence_date,
            evidence_window_trading_days=ctx.public_information_signal.evidence_window_trading_days,
        ),
        combined_context=CombinedContextSummaryResponse(
            classification=ctx.combined_context.classification.value if hasattr(ctx.combined_context.classification, "value") else str(ctx.combined_context.classification),
            interpretation=ctx.combined_context.interpretation,
            market_signal=ctx.combined_context.market_signal.value if hasattr(ctx.combined_context.market_signal, "value") else str(ctx.combined_context.market_signal),
            information_signal=ctx.combined_context.information_signal.value if hasattr(ctx.combined_context.information_signal, "value") else str(ctx.combined_context.information_signal),
            epistemic_tag=ctx.combined_context.epistemic_tag,
            non_accusatory_disclaimer=ctx.combined_context.non_accusatory_disclaimer,
        ),
        evidence_items=ev_resp_items,
        search_trend_items=[st.to_dict() for st in ctx.search_trend_items],
        created_at=ctx.created_at,
    )


@router.get(
    "/trends",
    response_model=list[SearchTrendItemResponse],
    summary="Get search-trend attention signals",
    description="Retrieve public attention and search-index signals for a legislative measure.",
)
def get_search_trends(
    bill_id: str = Query(..., description="Legislative bill ID"),
    evidence_repo: AnticipationEvidenceRepository = Depends(get_anticipation_evidence_repository),
) -> list[SearchTrendItemResponse]:
    trends = evidence_repo.get_trends_by_bill(bill_id)
    return [
        SearchTrendItemResponse(
            query=t.query,
            region=t.region,
            timestamp=t.timestamp,
            trend_value=t.trend_value,
            baseline_value=t.baseline_value,
            spike_indicator=t.spike_indicator,
            source=t.source,
            classification=t.classification,
            provenance=dict(t.provenance),
        )
        for t in trends
    ]


@router.get(
    "/pair",
    response_model=AnticipationScoreResponse,
    summary="Get single bill-company anticipation evaluation by query params",
    description="Retrieve anticipation diagnostic detail for a specific Central bill and quantitative company pair.",
)
@router.get(
    "/pair-detail",
    response_model=AnticipationScoreResponse,
    summary="Get single bill-company anticipation evaluation detail by query params",
    description="Retrieve anticipation diagnostic detail for a specific Central bill and quantitative company pair.",
)
def get_anticipation_pair_query(
    bill_id: str = Query(..., description="Legislative bill ID"),
    company_isin: str = Query(..., description="Company ISIN"),
    anticipation_repo: AnticipationRepository = Depends(get_anticipation_repository),
) -> AnticipationScoreResponse:
    return get_anticipation_pair_detail(bill_id=bill_id, company_isin=company_isin, anticipation_repo=anticipation_repo)


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
