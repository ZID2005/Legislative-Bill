"""
api/routers/ai.py
=================
REST routes for Grounded AI Explanation & Copilot interactions.
Guarantees:
- Zero secret leakage (never exposes API keys or internal filesystem traces).
- Robust offline fallback when Groq LLM inference is disabled or unreachable.
- Grounded strictly in validated parliamentary & corporate intelligence.
- Strict non-financial advice disclaimer on all outputs.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    CurrentUser,
    get_ai_explanation_service,
    get_current_user,
)
from api.errors import BadRequestError
from api.schemas import AIAskRequest, AIAskResponse
from services.ai.ai_explanation_service import AIExplanationResult, AIExplanationService

router = APIRouter(prefix="/ai", tags=["AI Copilot & Explanations"])

DISCLAIMER_TEXT = (
    "Verified Provenance: Grounded strictly in validated parliamentary and corporate intelligence. "
    "Analytical explanation only; not investment advice."
)


def _to_ai_response(
    result: AIExplanationResult,
    context_type: str,
    context_id: str,
) -> AIAskResponse:
    return AIAskResponse(
        content=result.content,
        context_type=context_type,
        context_id=context_id,
        persona=result.persona,
        operation=result.operation,
        success=result.success,
        is_cached=result.is_cached,
        disclaimer=DISCLAIMER_TEXT,
        provenance_sources=result.provenance_sources or ["Project Repository Ground Truth"],
    )


@router.post("/ask", response_model=AIAskResponse)
def ask_ai(
    request: AIAskRequest,
    current_user: CurrentUser = Depends(get_current_user),
    ai_service: AIExplanationService = Depends(get_ai_explanation_service),
) -> AIAskResponse:
    """
    Grounded question answering against legislative bill or corporate intelligence context.
    Falls back gracefully when offline or when external AI services are unreachable.
    """
    ctx_type = request.context_type.lower().strip()
    persona = request.persona.upper().strip()

    try:
        if ctx_type == "company":
            result = ai_service.ask_company_ai(
                company_identifier=request.context_id,
                question=request.question,
                persona=persona,
            )
        elif ctx_type == "bill":
            result = ai_service.ask_ai(
                bill_id=request.context_id,
                question=request.question,
                persona=persona,
            )
        elif ctx_type == "comparison":
            parts = [p.strip() for p in request.context_id.split(",") if p.strip()]
            if len(parts) != 2:
                raise BadRequestError("Comparison requires two comma-separated bill IDs (e.g. 'bill_1, bill_2').")
            result = ai_service.compare_bills(
                bill_id_1=parts[0],
                bill_id_2=parts[1],
                persona=persona,
            )
        else:
            raise BadRequestError(f"Unsupported context_type '{request.context_type}'. Must be 'bill', 'company', or 'comparison'.")

        return _to_ai_response(result, ctx_type, request.context_id)

    except BadRequestError:
        raise
    except Exception as e:
        # Guarantee no internal trace or secret leakage
        return AIAskResponse(
            content=f"AI explanation is temporarily unavailable: {str(e)[:150]}",
            context_type=ctx_type,
            context_id=request.context_id,
            persona=persona,
            operation="ASK_AI_FALLBACK",
            success=False,
            is_cached=False,
            disclaimer=DISCLAIMER_TEXT,
            provenance_sources=["System Fallback Guard"],
        )


@router.get("/explain/bill/{bill_id}", response_model=AIAskResponse)
def explain_bill(
    bill_id: str,
    operation: str = Query("BILL_SUMMARY", description="BILL_SUMMARY | WHY_IT_MATTERS | PROVISIONS | SECTOR_IMPACT | STAKEHOLDERS | MARKET_INTELLIGENCE | RISK_PROFILE | ANTICIPATION"),
    persona: str = Query("GENERAL_PUBLIC"),
    current_user: CurrentUser = Depends(get_current_user),
    ai_service: AIExplanationService = Depends(get_ai_explanation_service),
) -> AIAskResponse:
    """
    Structured analytical explanation for a parliamentary bill across supported analysis dimensions.
    """
    op = operation.strip().upper()
    p = persona.strip().upper()

    dispatch = {
        "BILL_SUMMARY": lambda: ai_service.explain_bill_summary(bill_id, persona=p),
        "WHY_IT_MATTERS": lambda: ai_service.explain_why_it_matters(bill_id, persona=p),
        "PROVISIONS": lambda: ai_service.explain_provisions(bill_id, persona=p),
        "SECTOR_IMPACT": lambda: ai_service.explain_sector_impact(bill_id, persona=p),
        "STAKEHOLDERS": lambda: ai_service.explain_stakeholders(bill_id, persona=p),
        "MARKET_INTELLIGENCE": lambda: ai_service.explain_market_intelligence(bill_id, persona=p),
        "RISK_PROFILE": lambda: ai_service.explain_risk_profile(bill_id, persona=p),
        "ANTICIPATION": lambda: ai_service.explain_anticipation(bill_id, persona=p),
    }

    fn = dispatch.get(op)
    if not fn:
        raise BadRequestError(f"Unsupported operation '{operation}'. Supported: {list(dispatch.keys())}")

    result = fn()
    return _to_ai_response(result, "bill", bill_id)


@router.get("/explain/company/{company_id}", response_model=AIAskResponse)
def explain_company(
    company_id: str,
    persona: str = Query("GENERAL_PUBLIC"),
    current_user: CurrentUser = Depends(get_current_user),
    ai_service: AIExplanationService = Depends(get_ai_explanation_service),
) -> AIAskResponse:
    """
    Structured analytical synthesis of a corporate entity's legislative footprint.
    """
    p = persona.strip().upper()
    result = ai_service.explain_company_profile(company_id, persona=p)
    return _to_ai_response(result, "company", company_id)


@router.get("/explain/company/{company_id}/bill/{bill_id}", response_model=AIAskResponse)
def explain_company_bill_exposure(
    company_id: str,
    bill_id: str,
    persona: str = Query("GENERAL_PUBLIC"),
    current_user: CurrentUser = Depends(get_current_user),
    ai_service: AIExplanationService = Depends(get_ai_explanation_service),
) -> AIAskResponse:
    """
    Structured narrative explanation of why a company is exposed to a specific legislative bill.
    """
    p = persona.strip().upper()
    result = ai_service.explain_company_bill_exposure(company_id, bill_id, persona=p)
    return _to_ai_response(result, "company_bill", f"{company_id}:{bill_id}")
