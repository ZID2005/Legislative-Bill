"""
api/routers/search.py
=====================
REST API router for Unified Multi-Attribute Global Search (Cmd+K).
Extended in Task 8.28 to support personalized discovery:
- Bills relevant to user portfolio
- Bills relevant to user watchlist
- Companies exposed to bills
- Sectors exposed to bills
- Recent legislative changes
Preserves epistemic and model status labels:
- LIVE
- FROZEN MODEL
- KNOWLEDGE ONLY
- MODELLED
- NOT ELIGIBLE
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query

from api.dependencies import (
    CurrentUser,
    get_company_intelligence_service,
    get_current_user,
    get_decision_intelligence_service,
    get_discovery_service,
)
from api.schemas import SearchResponse, SearchResultItem
from services.company_intelligence_service import CompanyIntelligenceService
from services.decision_intelligence_service import DecisionIntelligenceService
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
    summary="Unified global search across all platform entities and personalized workspace",
    description="Search across Central bills, State bills, listed companies, sectors, states, and personalized portfolio/watchlist matches.",
)
def global_search(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=50, description="Max results per category"),
    scope: str = Query("all", description="Scope filter: all, portfolio, watchlist, changes"),
    current_user: CurrentUser = Depends(get_current_user),
    discovery_service: UnifiedLegislativeDiscoveryService = Depends(get_discovery_service),
    company_service: CompanyIntelligenceService = Depends(get_company_intelligence_service),
    decision_service: DecisionIntelligenceService = Depends(get_decision_intelligence_service),
) -> SearchResponse:
    query_clean = q.strip()
    query_lower = query_clean.lower()

    items: list[SearchResultItem] = []
    category_counts: dict[str, int] = {}

    # 1. Search Portfolio & Personalized Relevance (Task 8.28)
    if scope in ("all", "portfolio") or "portfolio" in query_lower:
        try:
            exposure = decision_service.get_portfolio_legislative_exposure(
                user_id=current_user.user_id,
                tenant_id=current_user.tenant_id,
            )
            for b_imp in exposure.relevant_bills[:limit]:
                # If query is explicitly 'portfolio', match all relevant bills.
                # Otherwise, match on bill title, affected company, or affected sector.
                is_match = (
                    "portfolio" in query_lower
                    or query_lower in b_imp.bill_title.lower()
                    or any(query_lower in c.lower() for c in b_imp.affected_companies)
                    or any(query_lower in s.lower() for s in b_imp.affected_sectors)
                )
                if is_match:
                    cos_str = ", ".join(b_imp.affected_companies[:2])
                    subtitle = f"Portfolio Exposure: {b_imp.relevance_tier} • Matches: {cos_str}"
                    data_layer = "FROZEN_MODEL" if b_imp.model_status == "MODELLED" else "QUALITATIVE_INTEL"
                    items.append(
                        SearchResultItem(
                            id=f"port_{b_imp.bill_id}",
                            title=b_imp.bill_title,
                            subtitle=subtitle,
                            category="portfolio_relevant",
                            jurisdiction=b_imp.jurisdiction,
                            state=b_imp.state,
                            relevance_score=95,
                            url=f"/bills/{b_imp.bill_id}",
                            data_layer=data_layer,
                            model_status=b_imp.model_status,
                        )
                    )
                    category_counts["portfolio_relevant"] = category_counts.get("portfolio_relevant", 0) + 1
        except Exception:
            pass

    # 2. Search Watchlist Relevance (Task 8.28)
    if scope in ("all", "watchlist") or "watchlist" in query_lower:
        try:
            wl_bills = decision_service.get_watchlist_legislative_exposure(
                user_id=current_user.user_id,
                tenant_id=current_user.tenant_id,
            )
            for b_imp in wl_bills[:limit]:
                is_match = (
                    "watchlist" in query_lower
                    or query_lower in b_imp.bill_title.lower()
                    or any(query_lower in s.lower() for s in b_imp.affected_sectors)
                )
                if is_match:
                    subtitle = f"Watchlist Match • {b_imp.relevance_tier}"
                    data_layer = "FROZEN_MODEL" if b_imp.model_status == "MODELLED" else "QUALITATIVE_INTEL"
                    items.append(
                        SearchResultItem(
                            id=f"wl_{b_imp.bill_id}",
                            title=b_imp.bill_title,
                            subtitle=subtitle,
                            category="watchlist_relevant",
                            jurisdiction=b_imp.jurisdiction,
                            state=b_imp.state,
                            relevance_score=92,
                            url=f"/bills/{b_imp.bill_id}",
                            data_layer=data_layer,
                            model_status=b_imp.model_status,
                        )
                    )
                    category_counts["watchlist_relevant"] = category_counts.get("watchlist_relevant", 0) + 1
        except Exception:
            pass

    # 3. Search Recent Legislative Changes (Task 8.28)
    if scope in ("all", "changes") or any(kw in query_lower for kw in ("change", "recent", "update", "feed")):
        try:
            feed_items = decision_service.get_personalized_change_feed(
                user_id=current_user.user_id,
                tenant_id=current_user.tenant_id,
                limit=limit,
            )
            for ch in feed_items:
                if (
                    any(kw in query_lower for kw in ("change", "recent", "update", "feed"))
                    or query_lower in ch.bill_title.lower()
                    or query_lower in ch.relevance_reason.lower()
                ):
                    items.append(
                        SearchResultItem(
                            id=ch.event_id,
                            title=f"Change: {ch.bill_title}",
                            subtitle=f"{ch.event_type} • {ch.relevance_reason[:80]}",
                            category="recent_changes",
                            jurisdiction=ch.jurisdiction,
                            state=ch.state,
                            relevance_score=88,
                            url=ch.deep_link,
                            data_layer="OBSERVED_FEED",
                            model_status=ch.model_status,
                        )
                    )
                    category_counts["recent_changes"] = category_counts.get("recent_changes", 0) + 1
        except Exception:
            pass

    # 4. Search Bills (Central & State)
    if scope == "all":
        matched_bills = discovery_service.search(query=query_clean)
        for b in matched_bills[:limit]:
            cat = "bills_central" if b.is_central else "bills_state"
            subtitle = (
                f"Central Parliament • {b.policy_domain or 'General'}"
                if b.is_central
                else f"{b.state} Assembly • {b.policy_domain or 'State Legislation'}"
            )
            is_frozen_central = b.is_central and b.modeling_eligibility == "ELIGIBLE"
            data_layer = "FROZEN_MODEL" if is_frozen_central else "QUALITATIVE_INTEL"
            model_status = "MODELLED" if is_frozen_central else "NOT_ELIGIBLE"

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
                    data_layer=data_layer,
                    model_status=model_status,
                )
            )
            category_counts[cat] = category_counts.get(cat, 0) + 1

    # 5. Search Companies
    if scope == "all":
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
                    data_layer="FROZEN_MODEL" if is_quant else "QUALITATIVE_INTEL",
                    model_status="MODELLED" if is_quant else "NOT_ELIGIBLE",
                )
            )
            category_counts[cat] = category_counts.get(cat, 0) + 1

    # 6. Match Explore India Sectors & Categories
    if scope == "all":
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
                        data_layer="TAXONOMY",
                        model_status="NOT_ELIGIBLE",
                    )
                )
                category_counts["sectors"] = category_counts.get("sectors", 0) + 1

    # 7. Match States
    if scope == "all":
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
                        data_layer="QUALITATIVE_INTEL",
                        model_status="NOT_ELIGIBLE",
                    )
                )
                category_counts["states"] = category_counts.get("states", 0) + 1

    return SearchResponse(
        query=query_clean,
        total_matches=len(items),
        items=items,
        categories=category_counts,
    )
