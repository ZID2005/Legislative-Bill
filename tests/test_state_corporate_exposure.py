"""
tests/test_state_corporate_exposure.py
======================================
Comprehensive test suite for Task 8.7 — State Corporate Exposure Intelligence.

Covers all 30 required verification scenarios:
 1. Corporate exposure schema
 2. Serialization / deserialization roundtrip
 3. Company identity integrity
 4. Listed / unlisted handling
 5. State presence model
 6. Multiple presence types
 7. Bill-sector-company exposure chain
 8. Direct exposure classification
 9. Indirect exposure classification
10. Exposure strength scoring
11. Confidence scoring
12. Grounded evidence references
13. Field-level provenance
14. Geographic state scope
15. Repository CRUD operations
16. Multi-criteria search
17. State filtering
18. Company filtering
19. Sector filtering
20. Kerala corporate exposure
21. Telangana corporate exposure
22. Karnataka corporate exposure
23. Andhra Pradesh corporate exposure
24. No fabricated company mapping
25. No fabricated ticker
26. No stock prediction
27. State predictions remain zero
28. Central isolation
29. Backward compatibility
30. Processing idempotency
"""

from __future__ import annotations

import os
import json
import pytest
from pathlib import Path

from schemas.bill import Bill, BillStatus, BillHouse, BillJurisdiction
from schemas.company import Company, MarketCapCategory
from schemas.state_corporate_exposure import (
    CorporateExposureEvidence,
    StateCorporateExposure,
    StatePresenceRecord,
    _FORBIDDEN_PREDICTIVE_TERMS,
)
from schemas.state_economic_profile import StateBillEconomicProfile
from schemas.state_knowledge import StateBillKnowledge, StateBillSummary
from knowledge.state_company_universe import StateCompanyUniverse
from knowledge.state_corporate_exposure_engine import StateCorporateExposureEngine
from storage.state_bill_repository import StateBillRepository
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
from storage.state_knowledge_repository import StateKnowledgeRepository
from storage.bill_repository import BillRepository
from config.settings import settings


@pytest.fixture
def sample_company() -> Company:
    return Company(
        isin="INE758T01015",
        company_name="Zomato Limited",
        ticker_nse="ZOMATO",
        ticker_bse="ZOMATO",
        bse_code="543320",
        sector="Labour & Employment",
        industry="Internet & E-Commerce",
        sub_industry="Online Food Delivery",
        market_cap_category=MarketCapCategory.LARGE_CAP,
        market_cap_cr=210000.0,
        hq_state="Haryana",
        hq_city="Gurugram",
        website="https://www.zomato.com",
        listing_status="Listed",
        exchange="NSE",
        business_description="Online food delivery and platform work aggregator.",
        state_presences=[
            StatePresenceRecord(
                state="Telangana",
                presence_types=["service_operation", "logistics", "office"],
                facility_locations=["Hyderabad", "Warangal"],
                description="Food delivery operations and delivery partner network in Telangana.",
                evidence_source="Zomato Annual Report 2023-24",
            ),
        ],
        business_activities=["Online food delivery", "Platform work aggregation"],
    )


@pytest.fixture
def sample_gig_bill() -> Bill:
    return Bill(
        bill_id="telangana-vs-bill-11-2024",
        title="The Telangana Gig and Platform Workers (Registration and Welfare) Bill, 2024",
        bill_number="L.A. Bill No. 11 of 2024",
        state="Telangana",
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        year=2024,
        jurisdiction=BillJurisdiction.STATE,
        url="https://legislature.telangana.gov.in/bills/detail/11-2024",
        full_text="An Act to provide for registration of platform gig workers and levy of a welfare fee on aggregators.",
    )


# ------------------------------------------------------------------------------
# 1. Corporate Exposure Schema
# ------------------------------------------------------------------------------

def test_corporate_exposure_schema_instantiation():
    """Verify that StateCorporateExposure initializes with all required fields."""
    exp = StateCorporateExposure(
        bill_id="test-bill-1",
        state="Karnataka",
        company_id="INE009A01021",
        company_name="Infosys Limited",
        ticker="INFY",
        exchange="NSE",
        listed_status="listed",
        sector="Technology",
        sub_sector="IT Services",
        business_activity="Software development",
        state_presence=["headquarters", "office"],
        presence_type="headquarters",
        exposure_type="regulatory",
        exposure_direction="neutral",
        exposure_strength="MEDIUM",
        direct_indirect="DIRECT",
        geographic_scope="state_specific",
        mechanism="compliance",
        evidence=[
            CorporateExposureEvidence(
                source_type="bill_text",
                reference="Section 5",
                claim="Requires compliance records.",
            )
        ],
        confidence="HIGH",
    )
    assert exp.bill_id == "test-bill-1"
    assert exp.company_name == "Infosys Limited"
    assert exp.ticker == "INFY"
    assert exp.exchange == "NSE"
    assert exp.direct_indirect == "DIRECT"
    assert exp.exposure_strength == "MEDIUM"
    assert len(exp.evidence) == 1


# ------------------------------------------------------------------------------
# 2. Serialization / Deserialization Roundtrip
# ------------------------------------------------------------------------------

def test_serialization_deserialization_roundtrip():
    """Verify lossless serialization to dict and deserialization from dict."""
    exp = StateCorporateExposure(
        bill_id="telangana-vs-bill-11-2024",
        state="Telangana",
        company_id="INE758T01015",
        company_name="Zomato Limited",
        ticker="ZOMATO",
        exchange="NSE",
        listed_status="listed",
        sector="Labour & Employment",
        sub_sector="Gig Economy",
        business_activity="App-based delivery",
        state_presence=["service_operation", "office"],
        presence_type="service_operation",
        exposure_type="labour",
        exposure_direction="negative",
        exposure_strength="HIGH",
        direct_indirect="DIRECT",
        geographic_scope="state_specific",
        mechanism="labour_requirement",
        evidence=[
            CorporateExposureEvidence(
                source_type="bill_text",
                reference="Section 3",
                claim="Mandatory welfare fee on aggregators.",
            )
        ],
        confidence="HIGH",
        missing_information=["Local GMV contribution in Telangana"],
    )
    d = exp.to_dict()
    roundtrip = StateCorporateExposure.from_dict(d)

    assert roundtrip.bill_id == exp.bill_id
    assert roundtrip.company_id == exp.company_id
    assert roundtrip.company_name == exp.company_name
    assert roundtrip.ticker == exp.ticker
    assert roundtrip.exposure_type == exp.exposure_type
    assert roundtrip.exposure_strength == exp.exposure_strength
    assert roundtrip.direct_indirect == exp.direct_indirect
    assert len(roundtrip.evidence) == len(exp.evidence)
    assert roundtrip.evidence[0].claim == exp.evidence[0].claim
    assert roundtrip.missing_information == exp.missing_information


# ------------------------------------------------------------------------------
# 3. Company Identity Integrity
# ------------------------------------------------------------------------------

def test_company_identity_integrity():
    """Verify all companies in StateCompanyUniverse have valid ISIN, name, and sector."""
    universe = StateCompanyUniverse()
    for c in universe.get_all():
        assert c.isin, f"Company {c.company_name} missing ISIN"
        assert c.company_name, "Company missing company_name"
        assert c.sector, f"Company {c.company_name} missing sector"
        assert len(c.state_presences) > 0, f"Company {c.company_name} missing state presence"


# ------------------------------------------------------------------------------
# 4. Listed / Unlisted Handling
# ------------------------------------------------------------------------------

def test_listed_unlisted_handling():
    """Verify clear distinction between listed and unlisted entities."""
    universe = StateCompanyUniverse()
    listed = universe.get_listed()
    unlisted = universe.get_unlisted()

    assert len(listed) >= 40
    assert len(unlisted) >= 3

    for c in listed:
        assert c.ticker_nse or c.ticker_bse, f"Listed company {c.company_name} missing ticker"
        assert c.listing_status.lower() == "listed"

    for c in unlisted:
        assert c.listing_status.lower() != "listed"
        assert c.ticker_nse == "", f"Unlisted entity {c.company_name} must have empty ticker"


# ------------------------------------------------------------------------------
# 5. State Presence Model
# ------------------------------------------------------------------------------

def test_state_presence_model():
    """Verify state presence records have valid state, locations, and source."""
    universe = StateCompanyUniverse()
    valid_states = {"Andhra Pradesh", "Karnataka", "Kerala", "Telangana"}
    for c in universe.get_all():
        for sp in c.state_presences:
            assert sp.state in valid_states, f"Invalid state {sp.state} for {c.company_name}"
            assert len(sp.presence_types) > 0, f"Empty presence types for {c.company_name} in {sp.state}"
            assert sp.evidence_source, f"Missing evidence source for {c.company_name} in {sp.state}"


# ------------------------------------------------------------------------------
# 6. Multiple Presence Types
# ------------------------------------------------------------------------------

def test_multiple_presence_types():
    """Verify that companies can possess multiple verified presence types in a State."""
    universe = StateCompanyUniverse()
    multi_presences = [
        c for c in universe.get_all()
        if any(len(sp.presence_types) > 1 for sp in c.state_presences)
    ]
    assert len(multi_presences) > 20, "Should support multi-presence classifications"


# ------------------------------------------------------------------------------
# 7. Bill-Sector-Company Chain
# ------------------------------------------------------------------------------

def test_bill_sector_company_chain(sample_gig_bill: Bill):
    """Verify full inspection of Bill -> Policy Domain -> Sector -> Activity -> Company chain."""
    engine = StateCorporateExposureEngine()
    exposures = engine.analyze_bill_exposure(sample_gig_bill)
    assert len(exposures) > 0
    exp = exposures[0]
    assert exp.sector == "Labour & Employment"
    assert exp.business_activity != ""
    assert exp.state == sample_gig_bill.state
    assert exp.bill_id == sample_gig_bill.bill_id


# ------------------------------------------------------------------------------
# 8. Direct Exposure Classification
# ------------------------------------------------------------------------------

def test_direct_exposure_classification(sample_gig_bill: Bill):
    """Verify that regulated operating entities are labeled as DIRECT exposure."""
    engine = StateCorporateExposureEngine()
    exposures = engine.analyze_bill_exposure(sample_gig_bill)
    for e in exposures:
        if e.company_name in ["Zomato Limited", "Swiggy Limited"]:
            assert e.direct_indirect == "DIRECT"


# ------------------------------------------------------------------------------
# 9. Indirect Exposure Classification
# ------------------------------------------------------------------------------

def test_indirect_exposure_classification():
    """Verify that downstream/upstream ecosystem effects are labeled as INDIRECT."""
    b_repo = StateBillRepository()
    k_repo = StateKnowledgeRepository()
    engine = StateCorporateExposureEngine()

    mv_bill = b_repo.get("telangana-vs-bill-8-2024")
    if not mv_bill:
        pytest.skip("Telangana MV taxation bill not found")

    k_rec = k_repo.get("telangana-vs-bill-8-2024")
    exposures = engine.analyze_bill_exposure(mv_bill, k_rec.economic_profile if k_rec else None)

    indirect_exps = [e for e in exposures if e.direct_indirect == "INDIRECT"]
    assert len(indirect_exps) > 0, "Automakers affected via downstream fleet tax should be INDIRECT"
    for ie in indirect_exps:
        assert ie.direct_indirect != "DIRECT"


# ------------------------------------------------------------------------------
# 10. Exposure Strength Scoring
# ------------------------------------------------------------------------------

def test_exposure_strength_scoring():
    """Verify HIGH, MEDIUM, LOW exposure strength distinctions."""
    repo = StateCorporateExposureRepository()
    highs = repo.get_by_exposure_strength("HIGH")
    mediums = repo.get_by_exposure_strength("MEDIUM")
    lows = repo.get_by_exposure_strength("LOW")

    assert len(highs) > 0
    assert len(mediums) > 0
    assert len(lows) > 0

    for h in highs:
        assert h.exposure_strength == "HIGH"
    for m in mediums:
        assert m.exposure_strength == "MEDIUM"
    for l in lows:
        assert l.exposure_strength == "LOW"


# ------------------------------------------------------------------------------
# 11. Confidence Scoring
# ------------------------------------------------------------------------------

def test_confidence_scoring():
    """Verify confidence values are HIGH or MEDIUM based on authoritative filings."""
    repo = StateCorporateExposureRepository()
    all_exps = repo.get_all()
    for e in all_exps:
        assert e.confidence in ["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
        if e.confidence == "HIGH":
            assert len(e.evidence) >= 2, "HIGH confidence requires both statutory and corporate evidence"


# ------------------------------------------------------------------------------
# 12. Grounded Evidence References
# ------------------------------------------------------------------------------

def test_grounded_evidence_references():
    """Verify all corporate exposures contain grounded statutory and filing evidence."""
    repo = StateCorporateExposureRepository()
    all_exps = repo.get_all()
    for e in all_exps:
        assert len(e.evidence) > 0
        for ev in e.evidence:
            assert ev.source_type in ["bill_text", "company_filing", "annual_report", "official_website", "government_record"]
            assert len(ev.reference) > 0
            assert len(ev.claim) > 0


# ------------------------------------------------------------------------------
# 13. Field-Level Provenance
# ------------------------------------------------------------------------------

def test_field_level_provenance():
    """Verify structured provenance map is attached to each exposure."""
    repo = StateCorporateExposureRepository()
    all_exps = repo.get_all()
    for e in all_exps:
        assert "bill_applicability" in e.provenance
        assert "company_presence" in e.provenance
        assert "exposure_chain" in e.provenance


# ------------------------------------------------------------------------------
# 14. Geographic State Scope
# ------------------------------------------------------------------------------

def test_geographic_state_scope():
    """Verify geographic_scope captures local vs national-with-state-operations."""
    repo = StateCorporateExposureRepository()
    all_exps = repo.get_all()
    scopes = {e.geographic_scope for e in all_exps}
    assert "state_specific" in scopes
    assert "national_with_state_operations" in scopes


# ------------------------------------------------------------------------------
# 15. Repository CRUD Operations
# ------------------------------------------------------------------------------

def test_repository_crud_operations(tmp_path: Path):
    """Verify save, get, save_for_bill, and get_by_bill CRUD operations."""
    repo = StateCorporateExposureRepository(exposure_dir=tmp_path)
    assert repo.count() == 0

    exp = StateCorporateExposure(
        bill_id="crud-bill-1",
        state="Karnataka",
        company_id="INE009A01021",
        company_name="Infosys Limited",
        ticker="INFY",
        exchange="NSE",
        listed_status="listed",
        sector="Technology",
        sub_sector="IT Services",
        business_activity="Software consulting",
        state_presence=["headquarters", "office"],
        presence_type="headquarters",
        exposure_type="regulatory",
        exposure_direction="neutral",
        exposure_strength="MEDIUM",
        direct_indirect="DIRECT",
        geographic_scope="state_specific",
        mechanism="compliance",
        evidence=[],
    )

    repo.save(exp)
    assert repo.count() == 1

    fetched = repo.get("crud-bill-1", "INE009A01021")
    assert fetched is not None
    assert fetched.company_name == "Infosys Limited"

    bill_exps = repo.get_by_bill("crud-bill-1")
    assert len(bill_exps) == 1


# ------------------------------------------------------------------------------
# 16. Multi-Criteria Search
# ------------------------------------------------------------------------------

def test_multi_criteria_search():
    """Verify multi-criteria conceptual and filtered search in repository."""
    repo = StateCorporateExposureRepository()
    if repo.count() == 0:
        pytest.skip("Exposure repository not populated")

    # 1. Search for electricity bills in Telangana
    ts_elec = repo.search(query="companies exposed to Telangana electricity bills")
    assert len(ts_elec) > 0

    # 2. Search for high-exposure companies in Karnataka
    ka_high = repo.search(state="Karnataka", exposure_strength="HIGH")
    assert len(ka_high) > 0

    # 3. Search for gig workers
    gig = repo.search(query="gig and platform delivery aggregators")
    assert len(gig) > 0


# ------------------------------------------------------------------------------
# 17. State Filtering
# ------------------------------------------------------------------------------

def test_state_filtering():
    """Verify exact state-wise retrieval across all 4 pilot states."""
    repo = StateCorporateExposureRepository()
    for state in ["Andhra Pradesh", "Karnataka", "Kerala", "Telangana"]:
        exps = repo.get_by_state(state)
        assert len(exps) > 0, f"No exposures found for {state}"
        for e in exps:
            assert e.state.lower() == state.lower()


# ------------------------------------------------------------------------------
# 18. Company Filtering
# ------------------------------------------------------------------------------

def test_company_filtering():
    """Verify filtering by company ISIN or ticker."""
    repo = StateCorporateExposureRepository()
    zomato_exps = repo.get_by_company("ZOMATO")
    assert len(zomato_exps) > 0
    for e in zomato_exps:
        assert e.ticker == "ZOMATO"


# ------------------------------------------------------------------------------
# 19. Sector Filtering
# ------------------------------------------------------------------------------

def test_sector_filtering():
    """Verify filtering by economic sector."""
    repo = StateCorporateExposureRepository()
    elec_exps = repo.get_by_sector("Electricity")
    assert len(elec_exps) > 0
    for e in elec_exps:
        assert "electricity" in e.sector.lower()


# ------------------------------------------------------------------------------
# 20. Kerala Corporate Exposure
# ------------------------------------------------------------------------------

def test_kerala_corporate_exposure():
    """Verify Kerala exposures include clinical establishments and state utilities."""
    repo = StateCorporateExposureRepository()
    kl_exps = repo.get_by_state("Kerala")
    assert len(kl_exps) >= 1
    companies = {e.company_name for e in kl_exps}
    assert "Aster DM Healthcare Limited" in companies


# ------------------------------------------------------------------------------
# 21. Telangana Corporate Exposure
# ------------------------------------------------------------------------------

def test_telangana_corporate_exposure():
    """Verify Telangana exposures cover gig workers, electricity, and pharma."""
    repo = StateCorporateExposureRepository()
    ts_exps = repo.get_by_state("Telangana")
    assert len(ts_exps) >= 10
    companies = {e.company_name for e in ts_exps}
    assert "Zomato Limited" in companies
    assert "NTPC Limited" in companies


# ------------------------------------------------------------------------------
# 22. Karnataka Corporate Exposure
# ------------------------------------------------------------------------------

def test_karnataka_corporate_exposure():
    """Verify Karnataka exposures cover heavy industry, real estate, and GST."""
    repo = StateCorporateExposureRepository()
    ka_exps = repo.get_by_state("Karnataka")
    assert len(ka_exps) >= 10
    companies = {e.company_name for e in ka_exps}
    assert any("Prestige" in c or "Sobha" in c or "HDFC" in c or "State Bank" in c for c in companies)


# ------------------------------------------------------------------------------
# 23. Andhra Pradesh Corporate Exposure
# ------------------------------------------------------------------------------

def test_andhra_pradesh_corporate_exposure():
    """Verify AP exposures cover aquaculture, electricity duty, and factories."""
    repo = StateCorporateExposureRepository()
    ap_exps = repo.get_by_state("Andhra Pradesh")
    assert len(ap_exps) >= 20
    companies = {e.company_name for e in ap_exps}
    assert "Apex Frozen Foods Limited" in companies
    assert "Avanti Feeds Limited" in companies
    assert "Ultratech Cement Limited" in companies


# ------------------------------------------------------------------------------
# 24. No Fabricated Company Mapping
# ------------------------------------------------------------------------------

def test_no_fabricated_company_mapping():
    """Verify that administrative/penal bills (readiness=NONE) generate exactly ZERO exposures."""
    engine = StateCorporateExposureEngine()
    disqualification_bill = Bill(
        bill_id="karnataka-vs-bill-27-2024",
        title="The Karnataka Legislature (Prevention of Disqualification) (Amendment) Bill, 2024",
        bill_number="L.A. Bill No. 27 of 2024",
        state="Karnataka",
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.PASSED_BOTH,
        year=2024,
        jurisdiction=BillJurisdiction.STATE,
        url="https://kla.kar.nic.in/bills/detail/27-2024",
    )
    profile = StateBillEconomicProfile(
        bill_id="karnataka-vs-bill-27-2024",
        state="Karnataka",
        policy_domain="Public Administration & Governance",
        company_exposure_readiness="NONE",
    )
    exposures = engine.analyze_bill_exposure(disqualification_bill, economic_profile=profile)
    assert len(exposures) == 0, "Bill with readiness=NONE must produce 0 corporate exposures"


# ------------------------------------------------------------------------------
# 25. No Fabricated Ticker
# ------------------------------------------------------------------------------

def test_no_fabricated_ticker():
    """Verify unlisted companies have empty tickers and are never given false tickers."""
    repo = StateCorporateExposureRepository()
    all_exps = repo.get_all()
    for e in all_exps:
        if e.listed_status == "unlisted":
            assert e.ticker == "", f"Unlisted entity {e.company_name} must have empty ticker"
            assert e.exchange == ""


# ------------------------------------------------------------------------------
# 26. No Stock Prediction
# ------------------------------------------------------------------------------

def test_no_stock_prediction():
    """Verify strict prohibition of stock price predictions in exposure records."""
    repo = StateCorporateExposureRepository()
    all_exps = repo.get_all()
    for e in all_exps:
        text = str(e.to_dict()).lower()
        for forbidden in _FORBIDDEN_PREDICTIVE_TERMS:
            assert forbidden not in text, f"Forbidden predictive term '{forbidden}' found in {e.company_name}"


# ------------------------------------------------------------------------------
# 27. State Predictions Remain Zero
# ------------------------------------------------------------------------------

def test_state_predictions_remain_zero():
    """Verify invariant: state market predictions remain exactly 0."""
    pred_dir = settings.DATA_DIR / "predictions"
    pred_files = [f for f in os.listdir(pred_dir) if f.startswith("pred_")]
    state_preds = [
        f for f in pred_files
        if any(s in f for s in ["andhra", "karnataka", "kerala", "telangana"])
    ]
    assert len(state_preds) == 0, "State market predictions must remain strictly 0!"


# ------------------------------------------------------------------------------
# 28. Central Isolation
# ------------------------------------------------------------------------------

def test_central_isolation():
    """Verify Central production system is 100% frozen."""
    central_repo = BillRepository()
    assert central_repo.count() == 22, "Central bill metadata count modified!"

    pred_dir = settings.DATA_DIR / "predictions"
    pred_files = [f for f in os.listdir(pred_dir) if f.startswith("pred_")]
    assert len(pred_files) == 4700, "Central predictions count modified!"


# ------------------------------------------------------------------------------
# 29. Backward Compatibility
# ------------------------------------------------------------------------------

def test_backward_compatibility():
    """Verify StateBillKnowledge deserializes legacy JSON lacking corporate_exposures."""
    legacy_json = {
        "bill_id": "legacy-test-bill",
        "jurisdiction": "state",
        "state": "Kerala",
        "title": "Legacy Bill Without Exposures",
        "bill_number": "1 of 2024",
        "chamber": "vidhan_sabha",
        "status": "passed",
        "source_url": "https://example.com",
        "policy_category": "State Finance / Taxation",
    }
    rec = StateBillKnowledge.from_dict(legacy_json)
    assert rec.bill_id == "legacy-test-bill"
    assert rec.corporate_exposures == []
    d = rec.to_dict()
    assert "corporate_exposures" not in d


# ------------------------------------------------------------------------------
# 30. Processing Idempotency
# ------------------------------------------------------------------------------

def test_processing_idempotency(sample_gig_bill: Bill):
    """Verify that repeatedly executing the engine produces identical corporate exposures."""
    engine = StateCorporateExposureEngine()
    exps1 = engine.analyze_bill_exposure(sample_gig_bill)
    exps2 = engine.analyze_bill_exposure(sample_gig_bill)

    assert len(exps1) == len(exps2)
    assert [e.company_id for e in exps1] == [e.company_id for e in exps2]
    assert [e.exposure_type for e in exps1] == [e.exposure_type for e in exps2]
    assert [e.exposure_strength for e in exps1] == [e.exposure_strength for e in exps2]
    assert [e.direct_indirect for e in exps1] == [e.direct_indirect for e in exps2]
