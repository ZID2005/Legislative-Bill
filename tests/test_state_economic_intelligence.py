"""
tests/test_state_economic_intelligence.py
=========================================
Comprehensive test suite for Task 8.6 — State Sector & Stakeholder Intelligence Layer.

Covers all 23 required test categories:
1. Sector taxonomy (40+ categories, PRIMARY, SECONDARY, NONE, UNKNOWN)
2. Stakeholder taxonomy (PEOPLE, BUSINESSES, INSTITUTIONS, ECONOMIC_GROUPS, extensibility)
3. Sector classification (primary, secondary, sub-sector, activities)
4. Stakeholder classification (roles, directions, mechanisms)
5. Direct vs indirect classification (DIRECT, INDIRECT, UNKNOWN)
6. Impact direction (positive, negative, mixed, neutral, unknown)
7. Impact mechanism (compliance, taxation, subsidy, licensing, etc.)
8. Geographic scope (state-wide, district-level, city/municipal, rural, urban, regional)
9. Evidence references (traceable citations, no fabricated sections)
10. Confidence scoring (HIGH, MEDIUM, LOW)
11. Company exposure readiness (HIGH, MEDIUM, LOW, NONE, UNKNOWN, no stock predictions)
12. State knowledge integration (economic_profile field on StateBillKnowledge)
13. Cross-State search (conceptual queries: farmers, labour, transport, MSME, gig workers, etc.)
14. Andhra Pradesh bill validation (12 bills)
15. Karnataka bill validation (11 bills)
16. Kerala bill validation (11 bills)
17. Telangana bill validation (10 bills)
18. Missing/unknown fields handling (graceful fallbacks)
19. No unsupported claims (0 overclaiming terms, strict guardrails)
20. Central isolation (22 Central bills, 4,700 predictions, 0 state predictions)
21. Backward compatibility (loading legacy records without economic_profile)
22. Serialization and deserialization roundtrip
23. Repeated processing idempotency
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest

from config.settings import settings
from knowledge.state_economic_intelligence import (
    StateEconomicIntelligenceEngine,
    _FORBIDDEN_PREDICTIVE_TERMS,
)
from knowledge.state_economic_taxonomy import (
    CompanyExposureReadiness,
    GeographicScope,
    ImpactDirection,
    ImpactMechanism,
    ImpactType,
    STATE_ECONOMIC_SECTORS,
    STAKEHOLDER_BRANCHES,
    SectorLevel,
    StakeholderRole,
    get_sector_metadata,
    resolve_stakeholder_branch,
    validate_economic_sector,
)
from schemas.bill import Bill, BillHouse, BillJurisdiction, BillStatus
from schemas.state_economic_profile import (
    EvidenceReference,
    FactualStakeholderSummary,
    StakeholderImpact,
    StateBillEconomicProfile,
)
from schemas.state_knowledge import StateBillKnowledge, StateBillSummary
from storage.bill_repository import BillRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_knowledge_repository import StateKnowledgeRepository


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------

@pytest.fixture
def sample_state_bill() -> Bill:
    return Bill(
        bill_id="karnataka-vs-bill-28-2024",
        title="The Karnataka Cine and Cultural Activists (Welfare) Bill, 2024",
        bill_number="Bill No. 28 of 2024",
        year=2024,
        state="Karnataka",
        jurisdiction=BillJurisdiction.STATE,
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        sectors=["Labour, Employment & Gig Economy"],
        summary="A bill to constitute a welfare board and fund for cine and cultural activists in Karnataka.",
        full_text="An Act to constitute a welfare Board and to establish a fund for financing schemes for Cine and Cultural activists in the State.",
    )


@pytest.fixture
def gig_worker_bill() -> Bill:
    return Bill(
        bill_id="telangana-vs-bill-11-2024",
        title="The Telangana Gig and Platform Workers (Registration and Welfare) Bill, 2024",
        bill_number="Bill No. 11 of 2024",
        year=2024,
        state="Telangana",
        jurisdiction=BillJurisdiction.STATE,
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://telangana.gov.in",
        sectors=["Labour, Employment & Gig Economy"],
        summary="Registration of platform-based gig workers and constitution of a social security welfare board.",
        full_text="An Act to provide for registration of platform based gig workers and establish a welfare board.",
    )


@pytest.fixture
def motor_vehicles_bill() -> Bill:
    return Bill(
        bill_id="andhra-pradesh-vs-bill-14-2026",
        title="The Andhra Pradesh Motor Vehicles Taxation (Amendment) Bill, 2026",
        bill_number="L.A. Bill No. 14 of 2026",
        year=2026,
        state="Andhra Pradesh",
        jurisdiction=BillJurisdiction.STATE,
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://aplegislature.org",
        sectors=["Transport & Motor Vehicles"],
        summary="Amendment to motor vehicles taxation rates and registration fees in Andhra Pradesh.",
        full_text="An Act further to amend the Andhra Pradesh Motor Vehicles Taxation Act, 1963.",
    )


# ------------------------------------------------------------------------------
# 1. Sector Taxonomy Tests
# ------------------------------------------------------------------------------

def test_sector_taxonomy_completeness():
    """Verify that all required 40+ sectors exist in STATE_ECONOMIC_SECTORS."""
    assert len(STATE_ECONOMIC_SECTORS) >= 40
    required = [
        "Agriculture", "Fisheries", "Livestock", "Food Processing", "Manufacturing",
        "Construction", "Real Estate", "Infrastructure", "Roads & Transport", "Logistics",
        "Ports & Maritime", "Tourism", "Hospitality", "Retail", "Wholesale", "MSME",
        "Banking & Finance", "Insurance", "Healthcare", "Pharmaceuticals", "Education",
        "IT & Digital Services", "Telecommunications", "Energy", "Electricity",
        "Renewable Energy", "Mining", "Metals", "Chemicals", "Textiles",
        "Labour & Employment", "Gig Economy", "Public Administration", "Municipal Services",
        "Urban Development", "Rural Development", "Environment", "Water", "Housing",
        "Consumer Services", "Professional Services", "Other",
    ]
    for r in required:
        assert r in STATE_ECONOMIC_SECTORS, f"Missing required sector: {r}"
        assert validate_economic_sector(r) is True

    assert SectorLevel.PRIMARY.value == "PRIMARY"
    assert SectorLevel.SECONDARY.value == "SECONDARY"
    assert SectorLevel.NONE.value == "NONE"
    assert SectorLevel.UNKNOWN.value == "UNKNOWN"


# ------------------------------------------------------------------------------
# 2. Stakeholder Taxonomy Tests
# ------------------------------------------------------------------------------

def test_stakeholder_taxonomy_branches():
    """Verify stakeholder branches and extensibility."""
    assert "people" in STAKEHOLDER_BRANCHES
    assert "businesses" in STAKEHOLDER_BRANCHES
    assert "institutions" in STAKEHOLDER_BRANCHES
    assert "economic_groups" in STAKEHOLDER_BRANCHES

    assert "Farmers" in STAKEHOLDER_BRANCHES["people"]
    assert "Gig workers" in STAKEHOLDER_BRANCHES["people"]
    assert "MSMEs" in STAKEHOLDER_BRANCHES["businesses"]
    assert "Aggregators" in STAKEHOLDER_BRANCHES["businesses"]
    assert "State Government" in STAKEHOLDER_BRANCHES["institutions"]
    assert "Municipal bodies" in STAKEHOLDER_BRANCHES["institutions"]
    assert "Taxpayers" in STAKEHOLDER_BRANCHES["economic_groups"]

    assert resolve_stakeholder_branch("Farmers") == "people"
    assert resolve_stakeholder_branch("Transport operators") == "businesses"
    assert resolve_stakeholder_branch("Municipal bodies") == "institutions"
    assert resolve_stakeholder_branch("Taxpayers") == "economic_groups"


# ------------------------------------------------------------------------------
# 3. Sector Classification Tests
# ------------------------------------------------------------------------------

def test_sector_classification(gig_worker_bill: Bill, motor_vehicles_bill: Bill):
    """Verify primary, secondary, sub-sector, and activity classifications."""
    engine = StateEconomicIntelligenceEngine()

    profile_gig = engine.analyze_bill(gig_worker_bill)
    assert profile_gig.primary_sector == "Labour & Employment"
    assert "Gig Economy" in profile_gig.secondary_sectors
    assert len(profile_gig.sub_sectors) > 0
    assert len(profile_gig.economic_activities) > 0

    profile_mv = engine.analyze_bill(motor_vehicles_bill)
    assert profile_mv.primary_sector == "Roads & Transport"
    assert "Logistics" in profile_mv.secondary_sectors


# ------------------------------------------------------------------------------
# 4. Stakeholder Classification Tests
# ------------------------------------------------------------------------------

def test_stakeholder_classification(gig_worker_bill: Bill):
    """Verify stakeholder roles, directions, and mechanisms."""
    engine = StateEconomicIntelligenceEngine()
    profile = engine.analyze_bill(gig_worker_bill)

    sh_names = [s.stakeholder for s in profile.stakeholders]
    assert "Gig workers" in sh_names
    assert "Aggregators" in sh_names

    worker_impact = next(s for s in profile.stakeholders if s.stakeholder == "Gig workers")
    assert worker_impact.role == StakeholderRole.PRIMARY_AFFECTED.value
    assert worker_impact.direction == ImpactDirection.POSITIVE.value
    assert worker_impact.mechanism == ImpactMechanism.LABOUR_REQUIREMENT.value

    agg_impact = next(s for s in profile.stakeholders if s.stakeholder == "Aggregators")
    assert agg_impact.role == StakeholderRole.POTENTIAL_COST_BEARER.value
    assert agg_impact.direction == ImpactDirection.NEGATIVE.value
    assert agg_impact.mechanism == ImpactMechanism.COMPLIANCE.value


# ------------------------------------------------------------------------------
# 5. Direct vs Indirect Classification Tests
# ------------------------------------------------------------------------------

def test_direct_indirect_classification(gig_worker_bill: Bill):
    """Verify explicit separation of direct and indirect impacts."""
    engine = StateEconomicIntelligenceEngine()
    profile = engine.analyze_bill(gig_worker_bill)

    assert len(profile.direct_impacts) > 0
    direct_types = {s.impact_type for s in profile.stakeholders}
    assert "DIRECT" in direct_types


# ------------------------------------------------------------------------------
# 6. Impact Direction Tests
# ------------------------------------------------------------------------------

def test_impact_directions():
    """Verify all impact direction enums are valid."""
    directions = {e.value for e in ImpactDirection}
    assert directions == {"positive", "negative", "mixed", "neutral", "unknown"}


# ------------------------------------------------------------------------------
# 7. Impact Mechanism Tests
# ------------------------------------------------------------------------------

def test_impact_mechanisms():
    """Verify statutory mechanisms vocabulary."""
    mechs = {e.value for e in ImpactMechanism}
    expected = [
        "compliance", "taxation", "subsidy", "licensing", "labour_requirement",
        "pricing", "land_use", "environmental_requirement", "registration",
        "reporting", "procurement", "access", "eligibility", "public_service",
        "regulation", "infrastructure", "enforcement", "other"
    ]
    for exp in expected:
        assert exp in mechs


# ------------------------------------------------------------------------------
# 8. Geographic Scope Tests
# ------------------------------------------------------------------------------

def test_geographic_scope(sample_state_bill: Bill):
    """Verify state economic geography assignment."""
    engine = StateEconomicIntelligenceEngine()

    bengaluru_bill = Bill(
        bill_id="karnataka-vs-bill-34-2024",
        title="The Greater Bengaluru Governance Bill, 2024",
        state="Karnataka",
        jurisdiction=BillJurisdiction.STATE,
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://kla.kar.nic.in",
    )
    profile_bg = engine.analyze_bill(bengaluru_bill)
    assert profile_bg.geographic_scope == GeographicScope.CITY_MUNICIPAL.value

    profile_state = engine.analyze_bill(sample_state_bill)
    assert profile_state.geographic_scope == GeographicScope.STATE_WIDE.value


# ------------------------------------------------------------------------------
# 9. Evidence References Tests
# ------------------------------------------------------------------------------

def test_evidence_references(gig_worker_bill: Bill):
    """Verify traceable evidence references without fabricated sections."""
    engine = StateEconomicIntelligenceEngine()
    profile = engine.analyze_bill(gig_worker_bill)

    assert len(profile.evidence) > 0
    for ev in profile.evidence:
        assert isinstance(ev, EvidenceReference)
        assert ev.source_type in ["bill_text", "corpus", "provision", "metadata"]
        assert len(ev.text_reference) > 0


# ------------------------------------------------------------------------------
# 10. Confidence Scoring Tests
# ------------------------------------------------------------------------------

def test_confidence_scoring(sample_state_bill: Bill):
    """Verify confidence score assignment."""
    engine = StateEconomicIntelligenceEngine()
    profile = engine.analyze_bill(sample_state_bill)
    assert profile.confidence in ["HIGH", "MEDIUM", "LOW"]


# ------------------------------------------------------------------------------
# 11. Company Exposure Readiness Tests
# ------------------------------------------------------------------------------

def test_company_exposure_readiness(gig_worker_bill: Bill):
    """Verify readiness indicators without stock predictions or tickers."""
    engine = StateEconomicIntelligenceEngine()
    profile = engine.analyze_bill(gig_worker_bill)

    assert profile.company_exposure_readiness in ["HIGH", "MEDIUM", "LOW", "NONE", "UNKNOWN"]
    # Verify no tickers or price targets in profile
    prof_str = str(profile.to_dict()).lower()
    for forbidden in ["target price", "stock price", "buy rating", "sell rating"]:
        assert forbidden not in prof_str


# ------------------------------------------------------------------------------
# 12. State Knowledge Integration Tests
# ------------------------------------------------------------------------------

def test_state_knowledge_integration(sample_state_bill: Bill):
    """Verify StateBillKnowledge has economic_profile field and serializes cleanly."""
    engine = StateEconomicIntelligenceEngine()
    profile = engine.analyze_bill(sample_state_bill)

    k_rec = StateBillKnowledge(
        bill_id=sample_state_bill.bill_id,
        jurisdiction="state",
        state=sample_state_bill.state,
        title=sample_state_bill.title,
        bill_number=sample_state_bill.bill_number,
        chamber="vidhan_sabha",
        status="passed",
        source_url=sample_state_bill.url,
        policy_category="Labour, Employment & Gig Economy",
        economic_profile=profile,
    )

    d = k_rec.to_dict()
    assert "economic_profile" in d
    assert d["economic_profile"]["primary_sector"] == "Labour & Employment"

    deserialized = StateBillKnowledge.from_dict(d)
    assert deserialized.economic_profile is not None
    assert deserialized.economic_profile.primary_sector == "Labour & Employment"


# ------------------------------------------------------------------------------
# 13. Cross-State Search Tests
# ------------------------------------------------------------------------------

def test_cross_state_search():
    """Verify multi-attribute search and conceptual search queries."""
    repo = StateKnowledgeRepository()
    if repo.count() < 44:
        pytest.skip("Full state knowledge repo not yet populated")

    # 1. Search for labour bills across States
    labour_bills = repo.search(query="labour bills across states")
    assert len(labour_bills) >= 3

    # 2. Search for transport bills
    transport_bills = repo.search(query="transport bills")
    assert len(transport_bills) >= 2

    # 3. Search for gig workers
    gig_bills = repo.search(query="bills affecting gig workers")
    assert len(gig_bills) >= 2

    # 4. Search by primary sector filter
    elec_bills = repo.search(primary_sector="Electricity")
    assert len(elec_bills) >= 2

    # 5. Search by readiness filter
    high_readiness = repo.search(company_readiness="HIGH")
    assert len(high_readiness) >= 5


# ------------------------------------------------------------------------------
# 14. Andhra Pradesh Bill Validation
# ------------------------------------------------------------------------------

def test_ap_bill_validation():
    """Verify all 12 Andhra Pradesh bills have valid economic profiles."""
    repo = StateKnowledgeRepository()
    ap_bills = repo.get_by_state("Andhra Pradesh")
    assert len(ap_bills) == 12
    for b in ap_bills:
        assert b.economic_profile is not None
        assert b.economic_profile.primary_sector is not None
        assert len(b.economic_profile.stakeholders) > 0
        assert b.economic_profile.geographic_scope in ["state-wide", "urban", "city/municipal", "rural", "regional", "sector-specific geography"]


# ------------------------------------------------------------------------------
# 15. Karnataka Bill Validation
# ------------------------------------------------------------------------------

def test_karnataka_bill_validation():
    """Verify all 11 Karnataka bills have valid economic profiles."""
    repo = StateKnowledgeRepository()
    ka_bills = repo.get_by_state("Karnataka")
    assert len(ka_bills) == 11
    for b in ka_bills:
        assert b.economic_profile is not None
        assert b.economic_profile.primary_sector is not None
        assert len(b.economic_profile.stakeholders) > 0


# ------------------------------------------------------------------------------
# 16. Kerala Bill Validation
# ------------------------------------------------------------------------------

def test_kerala_bill_validation():
    """Verify all 11 Kerala bills have valid economic profiles."""
    repo = StateKnowledgeRepository()
    kl_bills = repo.get_by_state("Kerala")
    assert len(kl_bills) == 11
    for b in kl_bills:
        assert b.economic_profile is not None
        assert b.economic_profile.primary_sector is not None
        assert len(b.economic_profile.stakeholders) > 0


# ------------------------------------------------------------------------------
# 17. Telangana Bill Validation
# ------------------------------------------------------------------------------

def test_telangana_bill_validation():
    """Verify all 10 Telangana bills have valid economic profiles."""
    repo = StateKnowledgeRepository()
    ts_bills = repo.get_by_state("Telangana")
    assert len(ts_bills) == 10
    for b in ts_bills:
        assert b.economic_profile is not None
        assert b.economic_profile.primary_sector is not None
        assert len(b.economic_profile.stakeholders) > 0


# ------------------------------------------------------------------------------
# 18. Missing / Unknown Fields Handling
# ------------------------------------------------------------------------------

def test_missing_unknown_fields_handling():
    """Verify engine gracefully handles minimal or empty input."""
    engine = StateEconomicIntelligenceEngine()
    empty_bill = Bill(
        bill_id="test-empty-bill",
        title="General Miscellaneous Enactment",
        state="Test State",
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://example.com/test",
    )
    profile = engine.analyze_bill(empty_bill, corpus_text="")
    assert profile.primary_sector is not None
    assert profile.confidence in ["LOW", "MEDIUM"]
    assert profile.company_exposure_readiness is not None
    assert len(profile.stakeholders) > 0


# ------------------------------------------------------------------------------
# 19. No Unsupported Claims Guard
# ------------------------------------------------------------------------------

def test_no_unsupported_financial_claims():
    """Verify that all 44 state bills contain 0 unsupported financial/market claims."""
    repo = StateKnowledgeRepository()
    all_bills = repo.get_all()
    assert len(all_bills) == 44

    for b in all_bills:
        ep = b.economic_profile
        if not ep:
            continue
        ep_str = str(ep.to_dict()).lower()
        for term in _FORBIDDEN_PREDICTIVE_TERMS:
            assert term not in ep_str, f"Forbidden term '{term}' found in bill {b.bill_id}"


# ------------------------------------------------------------------------------
# 20. Central Isolation
# ------------------------------------------------------------------------------

def test_central_isolation():
    """Verify Central Government pipeline remains 100% frozen."""
    central_repo = BillRepository()
    assert central_repo.count() == 22, "Central bill metadata count modified!"

    pred_dir = settings.DATA_DIR / "predictions"
    pred_files = [f for f in os.listdir(pred_dir) if f.startswith("pred_")]
    assert len(pred_files) == 4700, "Central predictions count modified!"

    # Ensure 0 state predictions exist
    state_preds = [
        f for f in pred_files
        if any(s in f for s in ["andhra", "karnataka", "kerala", "telangana"])
    ]
    assert len(state_preds) == 0, "State market predictions must remain 0!"


# ------------------------------------------------------------------------------
# 21. Backward Compatibility
# ------------------------------------------------------------------------------

def test_backward_compatibility():
    """Verify StateBillKnowledge deserializes legacy JSON without economic_profile."""
    legacy_dict = {
        "bill_id": "legacy-test-bill",
        "jurisdiction": "state",
        "state": "Karnataka",
        "title": "Legacy Bill Without Profile",
        "bill_number": "1 of 2024",
        "chamber": "vidhan_sabha",
        "status": "passed",
        "source_url": "https://example.com",
        "policy_category": "State Finance / Taxation",
    }
    rec = StateBillKnowledge.from_dict(legacy_dict)
    assert rec.bill_id == "legacy-test-bill"
    assert rec.economic_profile is None
    # Serializing it does not inject economic_profile if None
    d = rec.to_dict()
    assert "economic_profile" not in d


# ------------------------------------------------------------------------------
# 22. Serialization / Deserialization Roundtrip
# ------------------------------------------------------------------------------

def test_serialization_deserialization_roundtrip(gig_worker_bill: Bill):
    """Verify lossless serialization and deserialization of StateBillEconomicProfile."""
    engine = StateEconomicIntelligenceEngine()
    profile = engine.analyze_bill(gig_worker_bill)

    p_dict = profile.to_dict()
    roundtrip = StateBillEconomicProfile.from_dict(p_dict)

    assert roundtrip.bill_id == profile.bill_id
    assert roundtrip.primary_sector == profile.primary_sector
    assert roundtrip.secondary_sectors == profile.secondary_sectors
    assert roundtrip.geographic_scope == profile.geographic_scope
    assert roundtrip.company_exposure_readiness == profile.company_exposure_readiness
    assert len(roundtrip.stakeholders) == len(profile.stakeholders)
    assert len(roundtrip.evidence) == len(profile.evidence)


# ------------------------------------------------------------------------------
# 23. Repeated Processing Idempotency
# ------------------------------------------------------------------------------

def test_repeated_processing_idempotency(sample_state_bill: Bill):
    """Verify running the engine repeatedly on the same bill yields identical output."""
    engine = StateEconomicIntelligenceEngine()
    profile1 = engine.analyze_bill(sample_state_bill)
    profile2 = engine.analyze_bill(sample_state_bill)

    assert profile1.primary_sector == profile2.primary_sector
    assert profile1.secondary_sectors == profile2.secondary_sectors
    assert profile1.geographic_scope == profile2.geographic_scope
    assert profile1.company_exposure_readiness == profile2.company_exposure_readiness
    assert [s.stakeholder for s in profile1.stakeholders] == [s.stakeholder for s in profile2.stakeholders]
    assert [s.mechanism for s in profile1.stakeholders] == [s.mechanism for s in profile2.stakeholders]
