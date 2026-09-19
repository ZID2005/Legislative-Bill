"""
api/routers/search.py
=====================
REST API router for Unified Multi-Attribute Global Search (Cmd+K).
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    get_company_intelligence_service,
    get_discovery_service,
)
from api.schemas import SearchResponse, SearchResultItem
from services.company_intelligence_service import CompanyIntelligenceService
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from utils.state_normalizer import (
    CANONICAL_INDIAN_STATES,
    CANONICAL_UNION_TERRITORIES,
    normalize_state,
)

router = APIRouter(prefix="/search", tags=["Search"])


@router.get(
    "",
    response_model=SearchResponse,
    summary="Unified global search across all platform entities",
    description="Search across Central bills, State bills, listed quantitative companies, intelligence entities, sectors, and states.",
)
def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=50, description="Max results per category"),
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
) -> SearchResponse:
    query_clean = q.strip()
    query_lower = query_clean.lower()

    items: list[SearchResultItem] = []
    category_counts: dict[str, int] = {}

    # 1. Search Bills
    matched_bills = discovery_service.search(query=query_clean)
    for b in matched_bills[:limit]:
        cat = "bills_central" if b.is_central else "bills_state"
        subtitle = (
            f"Central Parliament • {b.policy_domain or 'General'}"
            if b.is_central
            else f"{b.state} Assembly • {b.policy_domain or 'State Legislation'}"
        )
        items.append(
            SearchResultItem(
                id=b.bill_id,
                title=b.title,
                subtitle=subtitle,
                category=cat,
                jurisdiction=b.jurisdiction,
                state=b.state,
                relevance_score=90,
                url=f"/bills/{b.bill_id}",
            )
        )
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # 2. Search Companies
    matched_companies = company_service.search_companies(query_clean, top_k=limit)
    for c in matched_companies:
        is_quant = c.is_quant_eligible
        cat = "companies_quant" if is_quant else "companies_intel"
        subtitle = f"{c.sector} • {c.industry}" if c.industry else c.sector
        if not is_quant:
            subtitle += " (Qualitative Intel Only)"
        items.append(
            SearchResultItem(
                id=c.company_id,
                title=c.company_name,
                subtitle=subtitle,
                category=cat,
                jurisdiction="central" if is_quant else "state",
                state=c.hq_state or None,
                relevance_score=85,
                url=f"/companies/{c.company_id}",
            )
        )
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # 3. Match Explore India Sectors & Categories
    categories = discovery_service.get_explore_categories()
    for cat_name in categories:
        if query_lower in cat_name.lower():
            items.append(
                SearchResultItem(
                    id=cat_name.lower().replace(" ", "-"),
                    title=f"Sector: {cat_name}",
                    subtitle="Explore India Legislative Taxonomy",
                    category="sectors",
                    jurisdiction="all",
                    state=None,
                    relevance_score=70,
                    url=f"/explorer?category={cat_name}",
                )
            )
            category_counts["sectors"] = category_counts.get("sectors", 0) + 1

    # 4. Match States
    all_states = CANONICAL_INDIAN_STATES + CANONICAL_UNION_TERRITORIES
    for st in all_states:
        if query_lower in st.lower() or query_lower == normalize_state(st).lower():
            coverage = discovery_service.get_state_coverage()
            imp_states = {s["state"].lower() for s in coverage.get("implemented_states", [])}
            is_imp = st.lower() in imp_states
            sub = "Active Legislative Pilot (Zero Stock Models)" if is_imp else "Roadmap Expansion (0 bills ingested)"
            items.append(
                SearchResultItem(
                    id=st.lower().replace(" ", "-"),
                    title=f"State: {st}",
                    subtitle=sub,
                    category="states",
                    jurisdiction="state",
                    state=st,
                    relevance_score=75,
                    url=f"/states/{st}",
                )
            )
            category_counts["states"] = category_counts.get("states", 0) + 1

    return SearchResponse(
        query=query_clean,
        total_matches=len(items),
        items=items,
        categories=category_counts,
    )
