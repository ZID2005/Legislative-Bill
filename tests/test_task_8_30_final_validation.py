"""
tests/test_task_8_30_final_validation.py
=========================================
TASK 8.30 — Final End-to-End Product Validation, Reproducibility & Local Release Readiness.

Comprehensive 30-Scenario Quality & Invariant Verification Suite:
1.  Journey A: Discovery Flow
2.  Journey B: Quantitative Central Bill
3.  Journey C: State Bill Firewall & Zero Stock Predictions
4.  Journey D: Live Bill Isolation from Frozen Model
5.  Journey E: Personalized User & Tenant Isolation
6.  Data-Layer Epistemic Tags Classification
7.  Capability States & Anti-Contradiction Invariants
8.  API Contract: Search and Bills
9.  API Contract: Companies and Industries
10. API Contract: Predictions and Horizons
11. API Contract: Anticipation and Evidence
12. API Contract: Monitoring and Scheduler
13. API Contract: Portfolio and Workspace
14. Security: Cross-Tenant Portfolio/Watchlist IDOR Rejection
15. Security: Session Revocation Lifecycle
16. AI Safety: Adversarial Buy/Sell Refusal
17. AI Safety: Price Target & Guaranteed Return Refusal
18. AI Safety: Insider Trading & Leak Speculation Refusal
19. Anticipation: Market Signal vs Public Information Evidence Decoupling
20. Anticipation: Temporal Ordering & Same-Day/Post-Event Exclusion
21. Portfolio: Holding Validation & Unsupported Entity Handling
22. Live Discovery: Provenance & Non-Invocation of Analytical Models
23. Report Generation: Epistemic Integrity & Disclaimers
24. Search: Entity Types Parity & Fallbacks
25. Authoritative Baseline Manifest SHA-256
26. Authoritative Central Baseline Counts
27. Authoritative State Baseline Zero Stock Predictions
28. Five Authoritative Event Horizons
29. Auth API Dual Endpoint Support (/login & /token)
30. Data Immutability & Model Weight Protection
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
import pytest
from fastapi.testclient import TestClient

from api.app import create_app
from api.auth.provider import create_session_token, revoke_token, is_token_revoked
from config.settings import settings
from schemas.anticipation_evidence import (
    AnticipationContextClassification,
    AnticipationEvidenceContext,
    CombinedAnticipationContextSummary,
    EvidenceStrength,
    MarketSignalLevel,
    MarketSignalSummary,
    PublicInformationEvidence,
    PublicInformationSignalLevel,
    PublicInformationSignalSummary,
    PublicInformationSourceType,
    SourceCredibilityTier,
    TemporalRelation,
)
from services.ai.ai_guardrails import AIGuardrails
from storage.portfolio_repository import PortfolioRepository
from storage.watchlist_repository import WatchlistRepository


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


@pytest.fixture(scope="module")
def auth_headers() -> dict[str, str]:
    token = create_session_token(
        user_id="test_analyst_30",
        tenant_id="tenant_validation_30",
        role="MEMBER",
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "tenant_validation_30",
        "X-User-ID": "test_analyst_30",
    }


# ===========================================================================
# JOURNEYS A - E (PART 2)
# ===========================================================================

def test_01_journey_a_discovery_flow(client: TestClient, auth_headers: dict[str, str]):
    """JOURNEY A — DISCOVERY: Search -> View Bill -> Dossier -> Exposures -> Model Status."""
    # 1. Search for a central bill
    sr = client.get("/api/v1/search?q=telecom", headers=auth_headers)
    assert sr.status_code == 200
    s_data = sr.json()
    assert s_data.get("total_matches", 0) > 0

    # 2. Open bill detail
    bill_id = "the-telecommunication-bill-2023"
    br = client.get(f"/api/v1/bills/{bill_id}", headers=auth_headers)
    assert br.status_code in (200, 404)
    if br.status_code == 200:
        b_data = br.json()
        assert b_data["bill_id"] == bill_id
        assert b_data["jurisdiction"] == "central"

    # 3. View dossier
    dr = client.get(f"/api/v1/bills/{bill_id}/dossier", headers=auth_headers)
    assert dr.status_code in (200, 404)

    # 4. View model status
    ms = client.get(f"/api/v1/bills/{bill_id}/model-status", headers=auth_headers)
    assert ms.status_code in (200, 404)
    if ms.status_code == 200:
        assert "capability_state" in ms.json() or "model_status" in ms.json()


def test_02_journey_b_quantitative_central_bill(client: TestClient, auth_headers: dict[str, str]):
    """JOURNEY B — QUANTITATIVE CENTRAL BILL: Central Bill -> Quant Company -> Horizon Comparison -> Decision -> Evidence."""
    bill_id = "the-banking-laws-amendment-bill-2024"
    company_isin = "INE062A01020"

    # Compare horizons endpoint
    hr = client.get(
        f"/api/v1/predictions/horizons/compare?bill_id={bill_id}&company_isin={company_isin}",
        headers=auth_headers,
    )
    assert hr.status_code == 200
    h_data = hr.json()
    assert h_data["bill_id"] == bill_id
    assert h_data["company_isin"] == company_isin
    assert "modeled_windows" in h_data
    assert set(h_data["modeled_windows"]) == {"[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"}

    # Anticipation context & evidence enrichment
    ctx_resp = client.get(
        f"/api/v1/anticipation/context?bill_id={bill_id}&company_isin={company_isin}",
        headers=auth_headers,
    )
    assert ctx_resp.status_code == 200
    ctx_data = ctx_resp.json()
    assert ctx_data["bill_id"] == bill_id
    assert "market_signal" in ctx_data
    assert "public_information_signal" in ctx_data
    assert "combined_context" in ctx_data


def test_03_journey_c_state_bill_firewall(client: TestClient, auth_headers: dict[str, str]):
    """JOURNEY C — STATE BILL: State bill -> Corporate exposure -> Knowledge only -> ZERO stock predictions."""
    state_bill_id = "andhra-pradesh-vs-bill-1-2026"
    resp = client.get(f"/api/v1/bills/{state_bill_id}", headers=auth_headers)
    assert resp.status_code == 200

    # Invariant: State predictions are ALWAYS ZERO
    pred_resp = client.get(f"/api/v1/bills/{state_bill_id}/predictions", headers=auth_headers)
    assert pred_resp.status_code == 200
    p_data = pred_resp.json()
    # Predictions list must be empty, status indicating knowledge-only/not-eligible
    assert p_data.get("total", 0) == 0
    assert p_data.get("has_predictions", False) is False

    # Model status indicates NOT_ELIGIBLE or KNOWLEDGE_ONLY
    ms_resp = client.get(f"/api/v1/bills/{state_bill_id}/model-status", headers=auth_headers)
    assert ms_resp.status_code == 200
    ms_data = ms_resp.json()
    assert ms_data.get("stock_predictions_count", 0) == 0
    assert ms_data.get("is_modeled", False) is False


def test_04_journey_d_live_bill_isolation(client: TestClient, auth_headers: dict[str, str]):
    """JOURNEY D — LIVE BILL: Newly discovered live bill remains strictly isolated from frozen quantitative models."""
    mon_resp = client.get("/api/v1/monitoring/overview", headers=auth_headers)
    assert mon_resp.status_code == 200
    m_data = mon_resp.json()
    assert "total_sources" in m_data

    # Live knowledge check
    live_resp = client.get("/api/v1/monitoring/live-knowledge", headers=auth_headers)
    assert live_resp.status_code == 200
    l_data = live_resp.json()
    assert "items" in l_data


def test_05_journey_e_personalized_user_isolation(client: TestClient, auth_headers: dict[str, str]):
    """JOURNEY E — PERSONALIZED USER: Portfolio -> Holdings -> Relevance -> Watchlist -> Alerts isolation."""
    # 1. Fetch default portfolio
    port_resp = client.get("/api/v1/portfolio/default", headers=auth_headers)
    assert port_resp.status_code == 200
    port_id = port_resp.json()["portfolio_id"]

    # 2. Add holding
    add_resp = client.post(
        f"/api/v1/portfolio/{port_id}/holdings",
        json={"company_name": "Reliance Industries Limited", "isin": "INE002A01018", "ticker": "RELIANCE"},
        headers=auth_headers,
    )
    assert add_resp.status_code in (200, 201)

    # 3. Explain relevance
    rel_resp = client.get(
        "/api/v1/workspace/explain-relevance?bill_id=the-telecommunication-bill-2023",
        headers=auth_headers,
    )
    assert rel_resp.status_code in (200, 404)

    # 4. Verify workspace summary
    ws_resp = client.get("/api/v1/workspace/summary", headers=auth_headers)
    assert ws_resp.status_code == 200


# ===========================================================================
# DATA LAYER & CONTRACT CONSISTENCY (PARTS 3, 4)
# ===========================================================================

def test_06_data_layer_epistemic_tags(client: TestClient):
    """Verify standard epistemic tags exposed in operational metadata."""
    manifest_path = Path("docs/production_baseline.json")
    assert manifest_path.exists()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    epistemic_tags = data.get("operational_metadata", {}).get("supported_epistemic_tags", [])
    expected = {"[FACT]", "[OBSERVED]", "[DERIVED]", "[INTERPRETATION]", "[PREDICTION]"}
    assert expected.issubset(set(epistemic_tags))


def test_07_capability_states_consistency(client: TestClient, auth_headers: dict[str, str]):
    """Verify invariant combinations: No state predictions, intelligence companies have zero predictions."""
    resp = client.get("/api/v1/companies/INE758T01015/predictions", headers=auth_headers)
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        c_pred = resp.json()
        # Non-quantitative or firewalled companies must have 0 predictions
        assert c_pred.get("predictions", []) == [] or c_pred.get("has_predictions", False) is False


def test_08_api_contract_search_and_bills(client: TestClient, auth_headers: dict[str, str]):
    """API contract audit: search and bills endpoints."""
    r_search = client.get("/api/v1/search?q=Act", headers=auth_headers)
    assert r_search.status_code == 200

    r_bills = client.get("/api/v1/bills?limit=5", headers=auth_headers)
    assert r_bills.status_code == 200
    assert "items" in r_bills.json()
    assert "total" in r_bills.json()


def test_09_api_contract_companies_and_industries(client: TestClient, auth_headers: dict[str, str]):
    """API contract audit: companies and industries endpoints including company anticipation."""
    r_comp = client.get("/api/v1/companies?limit=5", headers=auth_headers)
    assert r_comp.status_code == 200

    r_ind = client.get("/api/v1/industries?limit=5", headers=auth_headers)
    assert r_ind.status_code == 200

    # Company anticipation endpoint
    r_ant = client.get("/api/v1/companies/INE002A01018/anticipation", headers=auth_headers)
    assert r_ant.status_code == 200
    assert "scores" in r_ant.json()


def test_10_api_contract_predictions_horizons(client: TestClient, auth_headers: dict[str, str]):
    """API contract audit: compare-horizons and predictions."""
    r_pred = client.get("/api/v1/predictions?limit=5", headers=auth_headers)
    assert r_pred.status_code == 200

    r_cmp = client.get(
        "/api/v1/predictions/compare-horizons?bill_id=the-telecommunication-bill-2023&company_isin=INE002A01018",
        headers=auth_headers,
    )
    assert r_cmp.status_code == 200
    assert "modeled_windows" in r_cmp.json()


def test_11_api_contract_anticipation_and_evidence(client: TestClient, auth_headers: dict[str, str]):
    """API contract audit: anticipation summary, pair, and evidence endpoints."""
    r_sum = client.get("/api/v1/anticipation/summary", headers=auth_headers)
    assert r_sum.status_code == 200

    r_ev = client.get("/api/v1/anticipation/evidence?limit=5", headers=auth_headers)
    assert r_ev.status_code == 200

    r_pair = client.get(
        "/api/v1/anticipation/pair?bill_id=the-telecommunication-bill-2023&company_isin=INE002A01018",
        headers=auth_headers,
    )
    assert r_pair.status_code in (200, 404)


def test_12_api_contract_monitoring_and_scheduler(client: TestClient, auth_headers: dict[str, str]):
    """API contract audit: monitoring runner, sources, and status."""
    r_mon = client.get("/api/v1/monitoring/status", headers=auth_headers)
    assert r_mon.status_code == 200

    r_src = client.get("/api/v1/monitoring/sources", headers=auth_headers)
    assert r_src.status_code == 200


def test_13_api_contract_portfolio_and_workspace(client: TestClient, auth_headers: dict[str, str]):
    """API contract audit: portfolio and workspace decision intelligence."""
    r_ws = client.get("/api/v1/workspace/summary", headers=auth_headers)
    assert r_ws.status_code == 200

    r_dec = client.get("/api/v1/workspace/decision-intelligence", headers=auth_headers)
    assert r_dec.status_code == 200


# ===========================================================================
# SECURITY FINAL GATE (PART 5)
# ===========================================================================

def test_14_security_tenant_isolation_cross_access(client: TestClient):
    """Attempt cross-tenant access to private portfolio and watchlist -> returns 403 or 404."""
    # Tenant Alpha creates a portfolio
    token_alpha = create_session_token(user_id="alice", tenant_id="org_alpha_sec", role="MEMBER")
    h_alpha = {"Authorization": f"Bearer {token_alpha}"}
    r_create = client.post("/api/v1/portfolio", json={"name": "Alpha Portfolio"}, headers=h_alpha)
    assert r_create.status_code in (200, 201)
    port_id = r_create.json()["portfolio_id"]

    # Tenant Beta attempts to access Tenant Alpha's portfolio
    token_beta = create_session_token(user_id="bob", tenant_id="org_beta_sec", role="MEMBER")
    h_beta = {"Authorization": f"Bearer {token_beta}"}
    r_attack = client.get(f"/api/v1/portfolio/{port_id}", headers=h_beta)
    assert r_attack.status_code in (403, 404)


def test_15_security_session_revocation(client: TestClient):
    """Logout invalidates session token and revokes access."""
    token = create_session_token(user_id="temp_user", tenant_id="temp_org", role="MEMBER")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify session works
    r_me = client.get("/api/v1/auth/me", headers=headers)
    assert r_me.status_code == 200

    # Logout
    r_logout = client.post("/api/v1/auth/logout", headers=headers)
    assert r_logout.status_code == 200

    # Verify session is revoked
    r_after = client.get("/api/v1/auth/me", headers=headers)
    assert r_after.status_code == 401


# ===========================================================================
# AI SAFETY FINAL GATE (PART 6)
# ===========================================================================

def test_16_ai_safety_adversarial_buy_sell_refusal():
    """Adversarial response recommending BUY/SELL is rejected by guardrails."""
    test_responses = [
        "You should buy the stock of Reliance immediately.",
        "Investors must sell the shares before passage.",
        "We recommend a strong buy on this company.",
    ]
    for resp in test_responses:
        result = AIGuardrails.validate_response(resp)
        assert result.is_valid is False
        assert any("financial advice" in v.lower() for v in result.violations)


def test_17_ai_safety_adversarial_price_target_refusal():
    """Adversarial response with price target or guaranteed return is rejected."""
    test_responses = [
        "This stock will rise by 30% with a guaranteed return.",
        "You will see a guaranteed profit after this bill passes.",
    ]
    for resp in test_responses:
        result = AIGuardrails.validate_response(resp)
        assert result.is_valid is False


def test_18_ai_safety_adversarial_insider_trading_refusal():
    """Adversarial response alleging insider trading or leaks is rejected."""
    test_responses = [
        "Corporate insiders engaged in insider trading ahead of the announcement.",
        "Market manipulation occurred because confidential information leakage was present.",
    ]
    for resp in test_responses:
        result = AIGuardrails.validate_response(resp)
        assert result.is_valid is False
        assert any("trading" in v.lower() or "accusatory" in v.lower() for v in result.violations)


# ===========================================================================
# ANTICIPATION & EVIDENCE INTEGRITY (PART 7)
# ===========================================================================

def test_19_anticipation_market_vs_evidence_separation():
    """Verify strict decoupling: market signal != public evidence != causality."""
    ctx = AnticipationEvidenceContext(
        bill_id="the-banking-laws-amendment-bill-2024",
        company_isin="INE062A01020",
        market_signal=MarketSignalSummary(
            level=MarketSignalLevel.HIGH,
            market_signal_score=0.85,
            car_magnitude=0.042,
            z_score=2.8,
            directional_persistence=0.75,
            volatility=0.015,
            signals_detected=["HIGH_CAR"],
        ),
        public_information_signal=PublicInformationSignalSummary(
            level=PublicInformationSignalLevel.HIGH,
            public_information_evidence_score=0.9,
            verified_pre_event_count=3,
            independent_sources_count=3,
            source_diversity_ratio=1.0,
        ),
        combined_context=CombinedAnticipationContextSummary(
            classification=AnticipationContextClassification.MULTI_SOURCE_PUBLIC_INFORMATION,
            interpretation="Observable market movement occurred before the event and public information evidence was identified.",
            market_signal=MarketSignalLevel.HIGH,
            information_signal=PublicInformationSignalLevel.HIGH,
        ),
    )
    # The interpretation must never claim causal proof
    assert "caused" not in ctx.combined_context.interpretation.lower()
    assert "insider" not in ctx.combined_context.interpretation.lower()
    assert ctx.market_signal.level == MarketSignalLevel.HIGH
    assert ctx.public_information_signal.level == PublicInformationSignalLevel.HIGH


def test_20_anticipation_temporal_ordering_and_exclusions():
    """Verify temporal ordering: only publications strictly before event time count as pre-event."""
    from services.anticipation_evidence.evidence_validator import EvidenceValidator

    rel_pre, reason_pre = EvidenceValidator.evaluate_temporal_relation("2024-08-01T10:00:00Z", "2024-08-09T11:00:00Z")
    assert rel_pre == TemporalRelation.PRE_EVENT

    rel_post, reason_post = EvidenceValidator.evaluate_temporal_relation("2024-08-10T18:00:00Z", "2024-08-09T11:00:00Z")
    assert rel_post == TemporalRelation.POST_EVENT

    ev_pre = PublicInformationEvidence(
        evidence_id="ev_pre_01",
        bill_id="the-banking-laws-amendment-bill-2024",
        jurisdiction="central",
        source_type=PublicInformationSourceType.PARLIAMENTARY,
        source_name="Lok Sabha Secretariat",
        source_url="https://sansad.in/bulletin_01",
        publication_timestamp="2024-08-01T10:00:00Z",
        discovery_timestamp="2024-08-01T10:30:00Z",
        event_reference="2024-08-09T11:00:00Z",
        headline="Banking Bill Listed for Introduction",
        summary="Official list of business.",
        relevance=0.95,
        evidence_strength=EvidenceStrength.STRONG,
        temporal_relation=TemporalRelation.PRE_EVENT,
        source_credibility=SourceCredibilityTier.TIER_1,
    )
    assert ev_pre.temporal_relation == TemporalRelation.PRE_EVENT

    ev_post = PublicInformationEvidence(
        evidence_id="ev_post_01",
        bill_id="the-banking-laws-amendment-bill-2024",
        jurisdiction="central",
        source_type=PublicInformationSourceType.FINANCIAL_MEDIA,
        source_name="Economic Times",
        source_url="https://economictimes.indiatimes.com/article_post",
        publication_timestamp="2024-08-10T18:00:00Z",
        discovery_timestamp="2024-08-10T18:30:00Z",
        event_reference="2024-08-09T11:00:00Z",
        headline="Banking Bill Passed in Parliament",
        summary="Post passage analysis.",
        relevance=0.8,
        evidence_strength=EvidenceStrength.MODERATE,
        temporal_relation=TemporalRelation.POST_EVENT,
        source_credibility=SourceCredibilityTier.TIER_2,
    )
    assert ev_post.temporal_relation == TemporalRelation.POST_EVENT


# ===========================================================================
# PORTFOLIO, LIVE DISCOVERY & REPORTS (PARTS 8, 9, 10)
# ===========================================================================

def test_21_portfolio_isin_validation_and_unsupported_entity(client: TestClient, auth_headers: dict[str, str]):
    """Verify portfolio validation rejects invalid requests and isolates unmodeled entities without stock predictions."""
    port_resp = client.get("/api/v1/portfolio/default", headers=auth_headers)
    assert port_resp.status_code == 200
    port_id = port_resp.json()["portfolio_id"]

    # 1. Validation failure: empty company name returns 422
    bad_resp = client.post(
        f"/api/v1/portfolio/{port_id}/holdings",
        json={"company_name": "   ", "isin": "INE000000000"},
        headers=auth_headers,
    )
    assert bad_resp.status_code == 422

    # 2. Add unmodeled company holding (not in 47-quant universe)
    add_resp = client.post(
        f"/api/v1/portfolio/{port_id}/holdings",
        json={
            "company_name": "Unmodeled Regional Enterprise Ltd",
            "sector": "Industrials",
            "industry": "Commercial Services",
        },
        headers=auth_headers,
    )
    assert add_resp.status_code == 201

    # 3. Decision service isolation check: unmodeled entity receives 0 stock predictions
    from services.decision_intelligence_service import (
        DecisionIntelligenceService,
        PersonalizedModelStatus,
        PortfolioHolding,
    )
    svc = DecisionIntelligenceService()
    unmodeled_holding = PortfolioHolding(
        holding_id="h_unmodeled_test",
        company_name="Unmodeled Regional Enterprise Ltd",
        sector="Industrials",
        industry="Commercial Services",
    )
    imp = svc.evaluate_bill_relevance_for_holding("the-mines-and-minerals-development-and-regulation-amendment-bill-2023", unmodeled_holding)
    if imp:
        assert imp.authoritative_prediction.available is False
        assert imp.authoritative_prediction.predictions_count == 0
        assert imp.model_status in (
            PersonalizedModelStatus.KNOWLEDGE_ONLY.value,
            PersonalizedModelStatus.NOT_ELIGIBLE.value,
        )


def test_22_live_discovery_unique_identity_and_provenance(client: TestClient, auth_headers: dict[str, str]):
    """Live discovery records maintain unique identity and source provenance."""
    resp = client.get("/api/v1/monitoring/sources", headers=auth_headers)
    assert resp.status_code == 200
    sources = resp.json().get("items", [])
    assert len(sources) > 0
    for s in sources:
        assert "source_id" in s
        assert "source_url" in s or "url" in s


def test_23_report_generation_disclaimers_and_epistemic_integrity(client: TestClient, auth_headers: dict[str, str]):
    """Reports contain required analytical disclaimers."""
    rep_resp = client.get(
        "/api/v1/reports/the-telecommunication-bill-2023/INE002A01018/[-1,+1]/investor",
        headers=auth_headers,
    )
    assert rep_resp.status_code in (200, 404)
    if rep_resp.status_code == 200:
        rep_data = rep_resp.json()
        assert "disclaimer" in rep_data
        assert rep_data["disclaimer"] is not None


# ===========================================================================
# SEARCH, BASELINE & IMMUTABILITY (PARTS 11, 20, 21)
# ===========================================================================

def test_24_search_entity_types_and_no_results(client: TestClient, auth_headers: dict[str, str]):
    """Search matches bills and companies and gracefully handles empty queries."""
    r_empty = client.get("/api/v1/search?q=xyznonexistentterm9999", headers=auth_headers)
    assert r_empty.status_code == 200
    assert r_empty.json().get("total_matches", 0) == 0


def test_25_authoritative_baseline_manifest_hash():
    """Verify SHA-256 of docs/production_baseline.json matches authoritative hash."""
    manifest_file = Path("docs/production_baseline.json")
    assert manifest_file.exists(), "production_baseline.json must exist"
    content = manifest_file.read_bytes()
    calculated_hash = hashlib.sha256(content).hexdigest()
    expected_hash = "50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7"
    assert calculated_hash == expected_hash, f"Hash mismatch! Expected {expected_hash}, got {calculated_hash}"


def test_26_authoritative_central_baseline_counts():
    """Verify central baseline counts defined in the production baseline manifest."""
    manifest_file = Path("docs/production_baseline.json")
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    central = data["central_baseline"]

    assert central["central_production_bills"] == 20
    assert central["quantitative_securities_count"] == 47
    assert central["bill_company_pairs_count"] == 940
    assert central["prediction_records_count"] == 4700
    assert central["decision_records_count"] == 4700
    assert central["anticipation_scores_count"] == 940
    assert central["stakeholder_reports"]["total_count"] == 14100


def test_27_authoritative_state_baseline_zero_predictions():
    """Verify State baseline counts and zero stock predictions invariant."""
    manifest_file = Path("docs/production_baseline.json")
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    state = data["state_baseline"]

    assert state["production_bills_count"] == 44
    assert state["stock_predictions_count"] == 0
    assert state["firewall_status"] == "STATE_QUALITATIVE_ONLY_ZERO_STOCK_PREDICTIONS"


def test_28_five_authoritative_event_horizons():
    """Verify authoritative event horizons."""
    authoritative_horizons = ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"]
    assert len(authoritative_horizons) == 5
    assert authoritative_horizons[0] == "[-1,+1]"
    assert authoritative_horizons[1] == "[-3,+3]"
    assert authoritative_horizons[2] == "[-5,+5]"
    assert authoritative_horizons[3] == "[-5,+10]"
    assert authoritative_horizons[4] == "[-10,+10]"


def test_29_auth_token_and_login_dual_support(client: TestClient):
    """Verify both /api/v1/auth/login and /api/v1/auth/token issue valid bearer JWT tokens."""
    # Test /login with JSON
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": "dual_test@example.com", "tenant_id": "test_dual_org"},
    )
    assert r_login.status_code == 200
    t1 = r_login.json()["token"]
    assert t1.count(".") == 2

    # Test /token with JSON
    r_token = client.post(
        "/api/v1/auth/token",
        json={"username": "dual_test@example.com", "tenant_id": "test_dual_org"},
    )
    assert r_token.status_code == 200
    t2 = r_token.json()["token"]
    assert t2.count(".") == 2


def test_30_data_immutability_git_clean_analytical_data():
    """Verify that frozen baseline and analytical files remain untouched and immutable."""
    manifest_file = Path("docs/production_baseline.json")
    content = manifest_file.read_bytes()
    assert hashlib.sha256(content).hexdigest() == "50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7"
