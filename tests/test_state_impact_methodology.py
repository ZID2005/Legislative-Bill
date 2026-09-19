"""
tests/test_state_impact_methodology.py
======================================
Comprehensive test suite for Task 8.8 — State Economic & Market Impact Methodology.

Covers all required verification scenarios:
 1. Economic taxonomy (26 mechanisms defined & validated)
 2. Economic mechanism extraction
 3. Economic direction logic (positive, negative, mixed, neutral, unknown)
 4. Economic strength scoring (HIGH, MEDIUM, LOW, UNKNOWN)
 5. Market relevance classification (HIGH, MEDIUM, LOW, NONE, UNKNOWN)
 6. Strict 10-point modeling eligibility scorecard
 7. 14-dimension data sufficiency assessment
 8. Event-date quality scoring (HIGH, MEDIUM, LOW, NONE)
 9. Primary vs alternative event date resolution
10. Anticipation readiness audit
11. Market data readiness audit
12. StateImpactAssessment schema validation
13. Serialization / deserialization roundtrip
14. Guardrails rejecting forbidden predictive terms
15. 44-bill assessment coverage (100%)
16. Andhra Pradesh assessments (12 bills)
17. Karnataka assessments (11 bills)
18. Kerala assessments (11 bills)
19. Telangana assessments (10 bills)
20. Impact repository CRUD operations
21. StateKnowledgeRepository search filtering by impact
22. Natural language query resolution
23. Missing data / date handling
24. Zero unsupported claims verification
25. State market predictions remain strictly zero
26. Central production system isolation
27. Backward compatibility for legacy JSON files
28. Deterministic processing idempotency
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import pytest

from config.settings import settings
from knowledge.state_economic_taxonomy import (
    STATE_ECONOMIC_MECHANISMS,
    VALID_ECONOMIC_MECHANISMS,
    normalize_economic_mechanism,
    validate_economic_mechanism,
)
from knowledge.state_impact_engine import StateImpactMethodologyEngine
from schemas.bill import Bill, BillHouse, BillJurisdiction, BillStatus
from schemas.state_corporate_exposure import StateCorporateExposure
from schemas.state_economic_profile import StakeholderImpact, StateBillEconomicProfile
from schemas.state_impact_assessment import (
    _FORBIDDEN_PREDICTIVE_TERMS,
    AnticipationReadiness,
    DataSufficiency,
    EconomicImpactDirection,
    EconomicImpactStrength,
    EconomicMechanism,
    EligibilityScorecard,
    EventDateQuality,
    EventDateRecord,
    EventDateRole,
    MarketDataReadinessSummary,
    MarketRelevance,
    ModelingEligibility,
    StateImpactAssessment,
)
from schemas.state_knowledge import StateBillKnowledge, StateBillSummary
from storage.bill_repository import BillRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
from storage.state_impact_repository import StateImpactRepository
from storage.state_knowledge_repository import StateKnowledgeRepository


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_bill() -> Bill:
    return Bill(
        bill_id="telangana-vs-bill-11-2024",
        jurisdiction=BillJurisdiction.STATE,
        state="Telangana",
        title="The Telangana Gig and Platform Workers (Registration and Welfare) Bill, 2024",
        bill_number="L.A. Bill No. 11 of 2024",
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        year=2024,
        introduction_date="2024-07-26",
        url="https://legislature.telangana.gov.in/bills/detail/11-2024",
        sectors=["Labour & Employment"],
        summary="A bill providing social security, registration, and welfare fee levy of 1-2% on platform aggregators.",
    )


@pytest.fixture
def sample_economic_profile() -> StateBillEconomicProfile:
    return StateBillEconomicProfile(
        bill_id="telangana-vs-bill-11-2024",
        state="Telangana",
        policy_domain="Labour, Employment & Gig Economy",
        primary_sector="Labour & Employment",
        impact_mechanisms=["labour_requirement", "compliance", "taxation"],
        stakeholders=[
            StakeholderImpact(
                stakeholder="Gig Workers",
                category="people",
                role="primary_affected",
                direction="positive",
                mechanism="labour_requirement",
            ),
            StakeholderImpact(
                stakeholder="Platform Aggregators",
                category="businesses",
                role="potential_cost_bearer",
                direction="negative",
                mechanism="compliance",
            ),
        ],
    )


@pytest.fixture
def sample_exposures() -> list[StateCorporateExposure]:
    return [
        StateCorporateExposure(
            bill_id="telangana-vs-bill-11-2024",
            state="Telangana",
            company_id="INE758T01015",
            company_name="Zomato Limited",
            ticker="ZOMATO",
            exchange="NSE",
            listed_status="listed",
            sector="Labour & Employment",
            sub_sector="Gig Economy & Platform Services",
            business_activity="App-based platform delivery",
            exposure_type="labour",
            exposure_direction="negative",
            exposure_strength="HIGH",
            direct_indirect="DIRECT",
            mechanism="labour_requirement",
        ),
        StateCorporateExposure(
            bill_id="telangana-vs-bill-11-2024",
            state="Telangana",
            company_id="INE00H001014",
            company_name="Swiggy Limited",
            ticker="SWIGGY",
            exchange="NSE",
            listed_status="listed",
            sector="Labour & Employment",
            sub_sector="Gig Economy & Platform Services",
            business_activity="App-based platform delivery",
            exposure_type="labour",
            exposure_direction="negative",
            exposure_strength="HIGH",
            direct_indirect="DIRECT",
            mechanism="labour_requirement",
        ),
    ]


# ==============================================================================
# 1. Economic Taxonomy & Validation
# ==============================================================================

def test_economic_taxonomy():
    """Verify that all 26 specified economic mechanisms are defined and validated."""
    expected_mechanisms = [
        "taxation", "subsidy", "compliance_cost", "labour_cost", "licensing",
        "regulation", "pricing", "demand", "supply", "investment",
        "infrastructure", "land", "electricity_cost", "transportation_cost",
        "financing", "credit", "procurement", "market_access",
        "environmental_cost", "public_spending", "productivity", "employment",
        "wages", "consumer_cost", "other", "unknown",
    ]
    for m in expected_mechanisms:
        assert m in STATE_ECONOMIC_MECHANISMS
        assert validate_economic_mechanism(m) is True

    assert validate_economic_mechanism("invalid_fake_mech") is False
    assert normalize_economic_mechanism("tax") == "taxation"
    assert normalize_economic_mechanism("labour_requirement") == "labour_cost"
    assert normalize_economic_mechanism("electricity") == "electricity_cost"


# ==============================================================================
# 2. Economic Mechanism Extraction
# ==============================================================================

def test_economic_mechanism_extraction(
    sample_bill: Bill,
    sample_economic_profile: StateBillEconomicProfile,
    sample_exposures: list[StateCorporateExposure],
):
    """Verify multi-mechanism extraction combining profile, exposures, and bill text."""
    engine = StateImpactMethodologyEngine()
    mechs = engine.extract_economic_mechanisms(sample_bill, sample_economic_profile, sample_exposures)
    assert isinstance(mechs, list)
    assert len(mechs) > 0
    assert "compliance_cost" in mechs
    assert "labour_cost" in mechs
    assert "taxation" in mechs


# ==============================================================================
# 3. Economic Direction Logic
# ==============================================================================

def test_economic_direction_logic(
    sample_bill: Bill,
    sample_economic_profile: StateBillEconomicProfile,
    sample_exposures: list[StateCorporateExposure],
):
    """Verify that economic direction is distinct from stock direction and correctly identifies mixed impact."""
    engine = StateImpactMethodologyEngine()
    mechs = engine.extract_economic_mechanisms(sample_bill, sample_economic_profile, sample_exposures)
    direction = engine.determine_economic_direction(sample_bill, mechs, sample_economic_profile, sample_exposures)
    # Since gig workers are positive beneficiaries and aggregators are cost bearers, composite direction is mixed
    assert direction == EconomicImpactDirection.MIXED.value

    # Test purely repealing bill -> neutral
    repeal_bill = Bill(
        bill_id="repeal-test-bill",
        jurisdiction=BillJurisdiction.STATE,
        state="Karnataka",
        title="The Karnataka Repealing and Amending Bill, 2024",
        bill_number="L.A. Bill No. 99 of 2024",
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://example.com/repeal",
        summary="A bill to repeal obsolete laws.",
    )
    assert engine.determine_economic_direction(repeal_bill, ["regulation"]) == EconomicImpactDirection.NEUTRAL.value


# ==============================================================================
# 4. Economic Strength Scoring
# ==============================================================================

def test_economic_strength_scoring(
    sample_bill: Bill,
    sample_economic_profile: StateBillEconomicProfile,
    sample_exposures: list[StateCorporateExposure],
):
    """Verify transparent deterministic economic impact strength scoring."""
    engine = StateImpactMethodologyEngine()
    mechs = engine.extract_economic_mechanisms(sample_bill, sample_economic_profile, sample_exposures)
    strength = engine.determine_economic_strength(sample_bill, mechs, sample_economic_profile, sample_exposures)
    assert strength == EconomicImpactStrength.HIGH.value

    # Bill without summary/text -> UNKNOWN
    empty_bill = Bill(
        bill_id="empty-test-bill",
        jurisdiction=BillJurisdiction.STATE,
        state="Kerala",
        title="Empty Bill",
        bill_number="1 of 2024",
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PENDING,
        url="https://example.com/empty",
    )
    assert engine.determine_economic_strength(empty_bill, []) == EconomicImpactStrength.UNKNOWN.value


# ==============================================================================
# 5. Market Relevance Classification
# ==============================================================================

def test_market_relevance_classification(sample_exposures: list[StateCorporateExposure]):
    """Verify Market Relevance is distinct from stock prediction."""
    engine = StateImpactMethodologyEngine()
    # Direct high-strength listed exposures -> HIGH
    rel = engine.determine_market_relevance(sample_exposures)
    assert rel == MarketRelevance.HIGH.value

    # Empty exposures -> NONE
    assert engine.determine_market_relevance([]) == MarketRelevance.NONE.value

    # Unlisted entities only -> NONE
    unlisted_exp = StateCorporateExposure(
        bill_id="test-bill",
        state="Kerala",
        company_id="UNLISTED-KL-KSEB",
        company_name="Kerala State Electricity Board",
        listed_status="unlisted",
        ticker="",
    )
    assert engine.determine_market_relevance([unlisted_exp]) == MarketRelevance.NONE.value


# ==============================================================================
# 6. Strict 10-Point Scorecard & Eligibility
# ==============================================================================

def test_eligibility_scorecard(
    sample_bill: Bill,
    sample_economic_profile: StateBillEconomicProfile,
    sample_exposures: list[StateCorporateExposure],
):
    """Verify the 10-point transparent eligibility scorecard."""
    engine = StateImpactMethodologyEngine()
    assessment = engine.assess_bill(sample_bill, sample_economic_profile, sample_exposures)

    scorecard = assessment.scorecard
    assert isinstance(scorecard, EligibilityScorecard)
    assert scorecard.bill_identity_verified is True
    assert scorecard.state_jurisdiction_verified is True
    assert scorecard.event_date_verified is True
    assert scorecard.economic_mechanism_identified is True
    assert scorecard.corporate_exposure_verified is True
    assert scorecard.listed_company_verified is True
    assert scorecard.benchmark_data_available is True
    # Zomato & Swiggy historical parquets not in Central store -> conditioning factor
    assert scorecard.result == ModelingEligibility.CONDITIONALLY_ELIGIBLE.value

    # Formatted scorecard text output
    text = scorecard.format_text(sample_bill.bill_id)
    assert "Result: CONDITIONALLY_ELIGIBLE" in text
    assert "Bill identity verified: YES" in text


# ==============================================================================
# 7. 14-Dimension Data Sufficiency Assessment
# ==============================================================================

def test_data_sufficiency_assessment(
    sample_bill: Bill,
    sample_economic_profile: StateBillEconomicProfile,
    sample_exposures: list[StateCorporateExposure],
):
    """Verify data sufficiency evaluates data gaps and compiles missing requirements."""
    engine = StateImpactMethodologyEngine()
    assessment = engine.assess_bill(sample_bill, sample_economic_profile, sample_exposures)

    assert assessment.data_sufficiency in [DataSufficiency.PARTIAL.value, DataSufficiency.INSUFFICIENT.value]
    assert len(assessment.missing_requirements) > 0
    # Checks that missing live crawlers are noted
    assert any("anticipation" in r.lower() for r in assessment.missing_requirements)


# ==============================================================================
# 8. Event Date Quality & Role Resolution
# ==============================================================================

def test_event_date_quality_and_roles(sample_bill: Bill):
    """Verify primary and alternative event date determination without date fabrication."""
    engine = StateImpactMethodologyEngine()
    primary, alts, quality = engine.resolve_event_dates(sample_bill)

    assert primary is not None
    assert primary.role == EventDateRole.INTRODUCTION.value
    assert primary.date == "2024-07-26"
    assert primary.is_primary is True
    assert quality == EventDateQuality.MEDIUM.value

    # Bill with both intro and assent -> HIGH quality
    sample_bill.assent_date = "2024-08-30"
    primary, alts, quality = engine.resolve_event_dates(sample_bill)
    assert quality == EventDateQuality.HIGH.value
    assert len(alts) == 1
    assert alts[0].role == EventDateRole.ASSENT.value
    assert alts[0].date == "2024-08-30"


# ==============================================================================
# 9. Anticipation Readiness Audit
# ==============================================================================

def test_anticipation_readiness_audit(sample_bill: Bill):
    """Verify anticipation audit records channels without invoking live crawlers."""
    engine = StateImpactMethodologyEngine()
    primary, _, _ = engine.resolve_event_dates(sample_bill)
    status, channels = engine.assess_anticipation_readiness(sample_bill, primary)

    assert status == AnticipationReadiness.PARTIAL.value
    assert "public_announcements" in channels
    assert "legislative_leaks" in channels


# ==============================================================================
# 10. Market Data Readiness Audit
# ==============================================================================

def test_market_data_readiness_audit(sample_exposures: list[StateCorporateExposure]):
    """Verify auditing of local parquet store and benchmarks."""
    engine = StateImpactMethodologyEngine()
    primary = EventDateRecord(role="introduction", date="2024-07-26", is_primary=True)
    mkt = engine.audit_market_data_readiness(sample_exposures, primary)

    assert isinstance(mkt, MarketDataReadinessSummary)
    assert mkt.candidate_companies_count == 2
    assert mkt.listed_companies_count == 2
    assert mkt.benchmark_available is True
    assert mkt.benchmark_ticker == "^NSEI"


# ==============================================================================
# 11. StateImpactAssessment Schema & Serialization Roundtrip
# ==============================================================================

def test_schema_serialization_roundtrip(
    sample_bill: Bill,
    sample_economic_profile: StateBillEconomicProfile,
    sample_exposures: list[StateCorporateExposure],
):
    """Verify that StateImpactAssessment serializes and deserializes losslessly."""
    engine = StateImpactMethodologyEngine()
    assessment = engine.assess_bill(sample_bill, sample_economic_profile, sample_exposures)

    d = assessment.to_dict()
    assert isinstance(d, dict)
    assert d["bill_id"] == sample_bill.bill_id
    assert d["economic_direction"] == assessment.economic_direction
    assert d["modeling_eligibility"] == assessment.modeling_eligibility

    reloaded = StateImpactAssessment.from_dict(d)
    assert reloaded.bill_id == assessment.bill_id
    assert reloaded.economic_mechanisms == assessment.economic_mechanisms
    assert reloaded.scorecard.result == assessment.scorecard.result


# ==============================================================================
# 12. Forbidden Predictive Terms Guardrails
# ==============================================================================

def test_forbidden_predictive_terms_guardrail():
    """Verify that attempting to inject financial predictions triggers strict validation error."""
    for forbidden in _FORBIDDEN_PREDICTIVE_TERMS:
        with pytest.raises(ValueError, match="Forbidden predictive term"):
            StateImpactAssessment(
                bill_id="test-bill",
                state="Telangana",
                title=f"Bill with {forbidden} in title",
            )


# ==============================================================================
# 13. 44-Bill Assessment Coverage
# ==============================================================================

def test_44_bill_assessment_coverage():
    """Verify all 44 state bills have been assessed and persisted."""
    repo = StateImpactRepository()
    all_assessments = repo.get_all()
    assert len(all_assessments) == 44, f"Expected 44 assessments, got {len(all_assessments)}"

    # Check distribution between corporate exposure and economic-only
    corp_bills = [a for a in all_assessments if a.exposure_count > 0]
    non_corp_bills = [a for a in all_assessments if a.exposure_count == 0]

    assert len(corp_bills) == 21, f"Expected 21 bills with corporate exposure, got {len(corp_bills)}"
    assert len(non_corp_bills) == 23, f"Expected 23 bills without corporate exposure, got {len(non_corp_bills)}"

    # All non-corporate bills must be NOT_ELIGIBLE and have market_relevance NONE
    for a in non_corp_bills:
        assert a.modeling_eligibility == ModelingEligibility.NOT_ELIGIBLE.value
        assert a.market_relevance == MarketRelevance.NONE.value

    # All 21 corporate exposure bills must be CONDITIONALLY_ELIGIBLE
    for a in corp_bills:
        assert a.modeling_eligibility == ModelingEligibility.CONDITIONALLY_ELIGIBLE.value
        assert a.market_relevance in [
            MarketRelevance.HIGH.value,
            MarketRelevance.MEDIUM.value,
            MarketRelevance.LOW.value,
        ]


# ==============================================================================
# 14. State-Wise Analysis (AP, KA, KL, TS)
# ==============================================================================

def test_state_wise_assessments():
    """Verify state-wise counts and classifications."""
    repo = StateImpactRepository()

    ap_bills = repo.get_by_state("Andhra Pradesh")
    ka_bills = repo.get_by_state("Karnataka")
    kl_bills = repo.get_by_state("Kerala")
    ts_bills = repo.get_by_state("Telangana")

    assert len(ap_bills) == 12
    assert len(ka_bills) == 11
    assert len(kl_bills) == 11
    assert len(ts_bills) == 10

    # Andhra Pradesh: 7 corporate, 5 non-corporate
    assert sum(1 for a in ap_bills if a.exposure_count > 0) == 7
    assert sum(1 for a in ap_bills if a.exposure_count == 0) == 5

    # Karnataka: 5 corporate, 6 non-corporate
    assert sum(1 for a in ka_bills if a.exposure_count > 0) == 5
    assert sum(1 for a in ka_bills if a.exposure_count == 0) == 6

    # Kerala: 2 corporate, 9 non-corporate
    assert sum(1 for a in kl_bills if a.exposure_count > 0) == 2
    assert sum(1 for a in kl_bills if a.exposure_count == 0) == 9

    # Telangana: 7 corporate, 3 non-corporate
    assert sum(1 for a in ts_bills if a.exposure_count > 0) == 7
    assert sum(1 for a in ts_bills if a.exposure_count == 0) == 3


# ==============================================================================
# 15. StateImpactRepository CRUD
# ==============================================================================

def test_impact_repository_crud():
    """Verify repository save, get, query, and existence checks."""
    repo = StateImpactRepository()
    test_assessment = StateImpactAssessment(
        bill_id="crud-test-bill",
        state="Karnataka",
        title="CRUD Test Bill",
        economic_strength=EconomicImpactStrength.MEDIUM.value,
        market_relevance=MarketRelevance.NONE.value,
        modeling_eligibility=ModelingEligibility.NOT_ELIGIBLE.value,
    )

    repo.save(test_assessment)
    assert repo.exists("crud-test-bill") is True

    fetched = repo.get("crud-test-bill")
    assert fetched is not None
    assert fetched.title == "CRUD Test Bill"

    by_elig = repo.get_by_eligibility("NOT_ELIGIBLE")
    assert any(a.bill_id == "crud-test-bill" for a in by_elig)

    repo.delete("crud-test-bill")
    assert repo.exists("crud-test-bill") is False


# ==============================================================================
# 16. StateKnowledgeRepository Search Integration
# ==============================================================================

def test_knowledge_search_integration():
    """Verify that StateKnowledgeRepository searches by impact attributes."""
    repo = StateKnowledgeRepository()

    # Filter by market_relevance
    high_rel = repo.search(market_relevance="HIGH")
    assert len(high_rel) > 0
    for r in high_rel:
        assert r.impact_assessment is not None
        assert r.impact_assessment.market_relevance == "HIGH"

    # Filter by economic_strength
    high_strength = repo.search(economic_strength="HIGH")
    assert len(high_strength) > 0

    # Filter by modeling_eligibility
    cond_elig = repo.search(modeling_eligibility="CONDITIONALLY_ELIGIBLE")
    assert len(cond_elig) == 21


# ==============================================================================
# 17. Natural Language Conceptual Queries
# ==============================================================================

def test_natural_language_queries():
    """Verify required natural-language queries resolve accurately."""
    repo = StateKnowledgeRepository()

    # "State bills with high economic impact"
    q1_results = repo.search(query="State bills with high economic impact")
    assert len(q1_results) > 0
    for r in q1_results:
        assert r.impact_assessment.economic_strength == "HIGH"

    # "Kerala bills with listed-company exposure"
    q2_results = repo.search(query="Kerala bills with listed-company exposure")
    assert len(q2_results) == 2  # Exactly 2 Kerala bills have listed exposure

    # "Telangana bills eligible for future market modeling"
    q3_results = repo.search(query="Telangana bills eligible for future market modeling")
    assert len(q3_results) == 7  # Exactly 7 Telangana bills with corporate exposure

    # "economic-only State bills"
    q4_results = repo.search(query="economic-only State bills")
    assert len(q4_results) == 23


# ==============================================================================
# 18. Zero Unsupported Claims & Quality Report
# ==============================================================================

def test_quality_report_and_zero_unsupported_claims():
    """Verify that quality report exists, validates, and has 0 unsupported claims."""
    report_path = settings.STATE_BILLS_DIR / "state_impact_methodology_quality_report.json"
    assert report_path.exists() is True

    with open(report_path, encoding="utf-8") as f:
        rep = json.load(f)

    assert rep["executive_summary"]["total_bills_assessed"] == 44
    assert rep["executive_summary"]["unsupported_claims_count"] == 0
    assert rep["executive_summary"]["state_predictions_generated"] == 0
    assert rep["validation_status"]["overall_status"] == "PASS"


# ==============================================================================
# 19. State Market Predictions Remain Zero
# ==============================================================================

def test_state_market_predictions_remain_zero():
    """Verify strict invariant: state market predictions remain exactly 0."""
    pred_dir = settings.DATA_DIR / "predictions"
    pred_files = [f for f in os.listdir(pred_dir) if f.startswith("pred_")]
    state_preds = [
        f for f in pred_files
        if any(s in f for s in ["andhra", "karnataka", "kerala", "telangana"])
    ]
    assert len(state_preds) == 0, "State market predictions must remain strictly 0!"


# ==============================================================================
# 20. Central Frozen Baseline Isolation
# ==============================================================================

def test_central_isolation():
    """Verify Central production system is 100% frozen."""
    central_repo = BillRepository()
    assert central_repo.count() == 22, "Central bill metadata count modified!"

    pred_dir = settings.DATA_DIR / "predictions"
    pred_files = [f for f in os.listdir(pred_dir) if f.startswith("pred_")]
    assert len(pred_files) == 4700, "Central predictions count modified!"


# ==============================================================================
# 21. Backward Compatibility
# ==============================================================================

def test_backward_compatibility():
    """Verify StateBillKnowledge deserializes legacy JSON lacking impact_assessment."""
    legacy_json = {
        "bill_id": "legacy-test-bill-no-impact",
        "jurisdiction": "state",
        "state": "Kerala",
        "title": "Legacy Bill Without Impact",
        "bill_number": "99 of 2024",
        "chamber": "vidhan_sabha",
        "status": "passed",
        "source_url": "https://example.com",
        "policy_category": "State Finance / Taxation",
    }
    rec = StateBillKnowledge.from_dict(legacy_json)
    assert rec.bill_id == "legacy-test-bill-no-impact"
    assert rec.impact_assessment is None
    d = rec.to_dict()
    assert "impact_assessment" not in d


# ==============================================================================
# 22. Deterministic Processing Idempotency
# ==============================================================================

def test_idempotency(
    sample_bill: Bill,
    sample_economic_profile: StateBillEconomicProfile,
    sample_exposures: list[StateCorporateExposure],
):
    """Verify that repeatedly executing the engine produces identical assessments."""
    engine = StateImpactMethodologyEngine()
    a1 = engine.assess_bill(sample_bill, sample_economic_profile, sample_exposures)
    a2 = engine.assess_bill(sample_bill, sample_economic_profile, sample_exposures)

    assert a1.economic_mechanisms == a2.economic_mechanisms
    assert a1.economic_direction == a2.economic_direction
    assert a1.economic_strength == a2.economic_strength
    assert a1.market_relevance == a2.market_relevance
    assert a1.modeling_eligibility == a2.modeling_eligibility
    assert a1.scorecard.result == a2.scorecard.result
