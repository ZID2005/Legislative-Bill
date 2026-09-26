"""
api/routers/predictions.py
==========================
REST API router for Central Market Impact Predictions, Decisions,
Anticipation Analysis, and Stakeholder Reports.
"""

from __future__ import annotations

import math
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    get_anticipation_repository,
    get_cached_decisions_by_id,
    get_cached_predictions,
    get_decision_repository,
    get_prediction_repository,
    get_report_repository,
)
from api.errors import NotFoundError
from api.schemas import (
    AnticipationScoreResponse,
    DecisionRecordResponse,
    PaginatedResponse,
    PredictionItem,
    StakeholderReportResponse,
)
from schemas.decision import DecisionSupportRecord, make_decision_id
from schemas.prediction import PredictionRecord
from schemas.report import StakeholderType
from storage.anticipation_repository import AnticipationRepository
from storage.decision_repository import DecisionRepository
from storage.prediction_repository import PredictionRepository
from storage.report_repository import ReportRepository

router = APIRouter(tags=["Predictions"])


def _to_prediction_item(p: PredictionRecord) -> PredictionItem:
    return PredictionItem(
        prediction_id=p.prediction_id,
        bill_id=p.bill_id,
        company_isin=p.company_isin,
        company_name=p.company_name or None,
        company_symbol=p.company_symbol or None,
        event_window=p.event_window,
        predicted_direction=str(p.predicted_direction),
        predicted_market_moving=bool(p.predicted_market_moving),
        market_moving_probability=round(float(p.market_moving_probability), 4),
        predicted_impact_strength=str(p.predicted_impact_strength),
        predicted_confidence=str(p.predicted_confidence),
        confidence_score=round(float(p.model_confidence), 4),
        model_version=p.model_version,
        created_at=p.prediction_timestamp,
    )


@router.get(
    "/predictions",
    response_model=PaginatedResponse[PredictionItem],
    summary="List Central market predictions",
    description="Retrieve paginated, filterable predictions from the 4,700 frozen production records across 5 event windows.",
)
def list_predictions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    bill_id: Optional[str] = Query(None, description="Filter by bill ID"),
    company_isin: Optional[str] = Query(None, description="Filter by company ISIN"),
    event_window: Optional[str] = Query(None, description="Filter by event window (e.g. [-1,+1], [-5,+5])"),
    direction: Optional[str] = Query(None, description="Filter by direction (POSITIVE, NEGATIVE, NEUTRAL)"),
    market_moving: Optional[bool] = Query(None, description="Filter: market moving probability >= 0.5"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score threshold"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction (central, state)"),
) -> PaginatedResponse[PredictionItem]:
    if jurisdiction and jurisdiction.strip().lower() == "state":
        return PaginatedResponse[PredictionItem](items=[], total=0, page=page, limit=limit, pages=0)

    all_preds, _ = get_cached_predictions()

    filtered: list[PredictionRecord] = []
    b_id_lower = bill_id.strip().lower() if bill_id else None
    isin_upper = company_isin.strip().upper() if company_isin else None
    ew_clean = event_window.strip().replace(" ", "+") if event_window else None
    dir_upper = direction.strip().upper() if direction else None

    for p in all_preds:
        if b_id_lower and p.bill_id.lower() != b_id_lower:
            continue
        if isin_upper and p.company_isin.upper() != isin_upper:
            continue
        if ew_clean and p.event_window != ew_clean:
            continue
        if dir_upper and str(p.predicted_direction).upper() != dir_upper:
            continue
        if market_moving is not None:
            is_mm = p.market_moving_probability >= 0.5
            if is_mm != market_moving:
                continue
        if min_confidence is not None and p.model_confidence < min_confidence:
            continue

        filtered.append(p)

    total = len(filtered)
    total_pages = math.ceil(total / limit) if total > 0 else 0
    start = (page - 1) * limit
    end = start + limit
    items = [_to_prediction_item(p) for p in filtered[start:end]]

    return PaginatedResponse[PredictionItem](
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=total_pages,
    )


@router.get(
    "/predictions/horizons/compare",
    summary="Compare event horizons for a bill-company pair",
    description="Retrieve comparison across all 5 modeled event windows and identify unmodeled horizons.",
)
def compare_prediction_horizons(
    bill_id: str = Query(..., description="Bill ID"),
    company_isin: str = Query(..., description="Company ISIN"),
) -> dict[str, Any]:
    all_preds, _ = get_cached_predictions()
    b_id = bill_id.strip().lower()
    c_isin = company_isin.strip().upper()

    matching = [p for p in all_preds if p.bill_id.lower() == b_id and p.company_isin.upper() == c_isin]
    modeled_windows = ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"]
    unmodeled_windows = [
        {"window": "[0,1]", "note": "Unmodeled horizon; event-study baseline utilizes symmetric pre/post event windows."},
        {"window": "[0,2]", "note": "Unmodeled horizon; event-study baseline utilizes symmetric pre/post event windows."},
        {"window": "[0,5]", "note": "Unmodeled horizon; event-study baseline utilizes symmetric pre/post event windows."},
    ]

    comparisons = []
    for w in modeled_windows:
        pred = next((p for p in matching if p.event_window == w), None)
        comparisons.append({
            "event_window": w,
            "is_modeled": True,
            "direction": str(pred.predicted_direction) if pred else None,
            "confidence": float(pred.model_confidence) if pred else None,
            "note": None,
        })
    for u in unmodeled_windows:
        comparisons.append({
            "event_window": u["window"],
            "is_modeled": False,
            "direction": None,
            "confidence": None,
            "note": u["note"],
        })

    return {
        "bill_id": bill_id,
        "company_isin": company_isin,
        "modeled_windows": modeled_windows,
        "comparisons": comparisons,
    }


@router.get(
    "/predictions/{prediction_id}",
    response_model=PredictionItem,
    summary="Get single prediction record",
    description="Retrieve a single verified Central prediction record by ID.",
)
def get_prediction_detail(
    prediction_id: str,
    pred_repo: PredictionRepository = Depends(get_prediction_repository),
) -> PredictionItem:
    _, by_id = get_cached_predictions()
    pred = by_id.get(prediction_id) or pred_repo.get(prediction_id)
    if not pred:
        raise NotFoundError(
            code="PREDICTION_NOT_FOUND",
            message=f"Prediction '{prediction_id}' not found.",
        )
    return _to_prediction_item(pred)


@router.get(
    "/predictions/{prediction_id}/decision",
    response_model=DecisionRecordResponse,
    summary="Get decision support for prediction",
    description="Retrieve the corresponding institutional decision-support and risk-tier record.",
)
def get_prediction_decision(
    prediction_id: str,
    pred_repo: PredictionRepository = Depends(get_prediction_repository),
    dec_repo: DecisionRepository = Depends(get_decision_repository),
) -> DecisionRecordResponse:
    _, by_id = get_cached_predictions()
    pred = by_id.get(prediction_id) or pred_repo.get(prediction_id)
    if not pred:
        raise NotFoundError(
            code="PREDICTION_NOT_FOUND",
            message=f"Prediction '{prediction_id}' not found.",
        )

    # Resolve decision support record
    dec_id = make_decision_id(pred.bill_id, pred.company_isin, pred.event_window)
    decisions_cache = get_cached_decisions_by_id()
    decision = decisions_cache.get(dec_id) or dec_repo.get(dec_id)

    if not decision:
        raise NotFoundError(
            code="DECISION_NOT_FOUND",
            message=f"Decision record for prediction '{prediction_id}' not found.",
        )

    return DecisionRecordResponse(
        decision_id=decision.decision_id,
        prediction_id=pred.prediction_id,
        bill_id=decision.bill_id,
        company_isin=decision.company_isin,
        event_window=decision.event_window,
        risk_category=decision.risk_category.value if hasattr(decision.risk_category, "value") else str(decision.risk_category),
        pricing_in_risk=decision.pricing_in_risk.value if hasattr(decision.pricing_in_risk, "value") else str(decision.pricing_in_risk),
        impact_category=decision.impact_category.value if hasattr(decision.impact_category, "value") else str(decision.impact_category),
        impact_score=round(float(decision.impact_score), 4),
        risk_score=round(float(decision.risk_score), 4),
        decision_reason=decision.decision_reason,
        investor_summary=decision.investor_summary,
        business_summary=decision.business_summary,
        public_summary=decision.public_summary,
        created_at=decision.generation_timestamp,
    )


@router.get(
    "/predictions/{prediction_id}/anticipation",
    response_model=AnticipationScoreResponse,
    summary="Get anticipation score for prediction pair",
    description="Retrieve pre-event anticipation bias score and diffusion evidence for the underlying (bill, company) pair.",
)
def get_prediction_anticipation(
    prediction_id: str,
    pred_repo: PredictionRepository = Depends(get_prediction_repository),
    anticipation_repo: AnticipationRepository = Depends(get_anticipation_repository),
) -> AnticipationScoreResponse:
    _, by_id = get_cached_predictions()
    pred = by_id.get(prediction_id) or pred_repo.get(prediction_id)
    if not pred:
        raise NotFoundError(
            code="PREDICTION_NOT_FOUND",
            message=f"Prediction '{prediction_id}' not found.",
        )

    score = anticipation_repo.get_score(pred.bill_id, pred.company_isin)
    if not score:
        raise NotFoundError(
            code="ANTICIPATION_NOT_FOUND",
            message=f"Anticipation score for pair ({pred.bill_id}, {pred.company_isin}) not found.",
        )

    ev_claims = list(getattr(score, "detected_signals", []))

    return AnticipationScoreResponse(
        bill_id=score.bill_id,
        company_isin=score.company_isin,
        anticipation_score=round(float(score.anticipation_score), 4),
        anticipation_tier=str(score.classification),
        diffusion_index=round(float(score.information_signal_score), 4),
        pre_event_volume_ratio=round(float(score.market_signal_score), 4),
        pre_event_car=0.0,
        leakage_indicator=bool(score.anticipation_flag),
        evidence_summary=ev_claims,
    )


@router.get(
    "/reports/{bill_id}/{company_isin}/{event_window}/{stakeholder_type}",
    response_model=StakeholderReportResponse,
    summary="Get stakeholder analytical report",
    description="Retrieve an analytical report tailored to an Investor, Business, or Public stakeholder perspective.",
)
def get_stakeholder_report(
    bill_id: str,
    company_isin: str,
    event_window: str,
    stakeholder_type: str,
    report_repo: ReportRepository = Depends(get_report_repository),
) -> StakeholderReportResponse:
    st_clean = stakeholder_type.strip().upper()
    try:
        st_enum = StakeholderType(st_clean)
    except ValueError:
        raise NotFoundError(
            code="INVALID_STAKEHOLDER_TYPE",
            message=f"Invalid stakeholder type '{stakeholder_type}'. Must be investor, business, or public.",
        )

    report = report_repo.get_by_key(
        bill_id=bill_id,
        company_isin=company_isin,
        event_window=event_window,
        stakeholder_type=st_enum.value,
    )
    if not report:
        raise NotFoundError(
            code="REPORT_NOT_FOUND",
            message=f"Report for {bill_id}/{company_isin}/{event_window}/{st_clean.lower()} not found.",
        )

    return StakeholderReportResponse(
        report_id=report.report_id,
        bill_id=report.bill_id,
        company_isin=report.company_isin,
        event_window=report.event_window,
        stakeholder_type=st_clean.lower(),
        executive_summary=report.executive_summary,
        impact_summary=getattr(report, "impact_summary", None),
        risk_summary=getattr(report, "risk_summary", None),
        anticipation_summary=getattr(report, "anticipation_summary", None),
        confidence_summary=getattr(report, "confidence_summary", None),
        key_takeaways=list(getattr(report, "key_factors", []) or []),
        key_factors=list(getattr(report, "key_factors", []) or []),
        transmission_channels=list(getattr(report, "transmission_channels", []) or []),
        methodology_note=getattr(report, "methodology_note", None),
        disclaimer=getattr(report, "disclaimer", None),
        created_at=getattr(report, "generated_timestamp", getattr(report, "created_at", "")),
    )
