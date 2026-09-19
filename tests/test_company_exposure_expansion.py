"""
tests/test_company_exposure_expansion.py
========================================
Comprehensive test suite for Task 8.12.4 — Evidence-Based Company Exposure Intelligence Expansion.

Validates all 15 required verification scenarios:
 1. Intelligence company -> bill exposure
 2. Bill -> intelligence company reverse lookup
 3. Mandatory evidence verification
 4. Rejection of unsupported exposure (marked NONE / UNKNOWN)
 5. Direct vs indirect classification
 6. Exposure strength validation
 7. Economic mechanism validation
 8. State presence requirement for State-specific exposure
 9. Intelligence companies cannot enter quantitative prediction workflows
 10. Existing 47 Central quantitative companies remain unchanged
 11. Existing validated State exposure records remain intact
 12. State predictions remain exactly 0
 13. Duplicate exposure detection
 14. Company alias matching
 15. Provenance survives serialization / deserialization roundtrip
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from config.settings import settings
from knowledge.state_corporate_exposure_engine import StateCorporateExposureEngine, CompanyExposureEngine
from schemas.bill import Bill, BillJurisdiction
from schemas.company import Company, UniverseType
from schemas.state_corporate_exposure import (
    CorporateExposureEvidence,
    StateCorporateExposure,
    CompanyExposureRecord,
    _FORBIDDEN_PREDICTIVE_TERMS,
)
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.mapping_repository import MappingRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository


@pytest.fixture
def company_repo() -> CompanyRepository:
    return CompanyRepository()


@pytest.fixture
def exposure_repo() -> CompanyExposureRepository:
    return CompanyExposureRepository()


@pytest.fixture
def engine() -> StateCorporateExposureEngine:
    return StateCorporateExposureEngine()


@pytest.fixture
def intelligence_companies(company_repo: CompanyRepository) -> list[Company]:
    return company_repo.get_intelligence_companies()


# ------------------------------------------------------------------------------
# 1. Intelligence Company -> Bill Exposure
# ------------------------------------------------------------------------------

class TestIntelligenceCompanyToBillExposure:
    """1. Intelligence company connects to relevant Central/State legislation."""

    def test_gmr_airports_exposed_to_aviation_bill(self, exposure_repo: CompanyExposureRepository):
        exps = exposure_repo.get_bills_for_company("GMR Airports")
        bill_ids = [e.bill_id for e in exps]
        assert "the-bharatiya-vayuyan-vidheyak-2024" in bill_ids

    def test_adani_ports_exposed_to_maritime_bills(self, exposure_repo: CompanyExposureRepository):
        exps = exposure_repo.get_bills_for_company("Adani Ports")
        bill_ids = [e.bill_id for e in exps]
        assert "the-coastal-shipping-bill-2024" in bill_ids
        assert "the-bills-of-lading-bill-2024" in bill_ids
        assert "the-carriage-of-goods-by-sea-bill-2024" in bill_ids
        assert "the-merchant-shipping-bill-2024" in bill_ids

    def test_irfc_exposed_to_railways_bill(self, exposure_repo: CompanyExposureRepository):
        exps = exposure_repo.get_bills_for_company("IRFC")
        bill_ids = [e.bill_id for e in exps]
        assert "the-railways-amendment-bill-2024" in bill_ids

    def test_bsnl_and_vodafone_exposed_to_telecom_policy(self, exposure_repo: CompanyExposureRepository):
        bsnl_exps = exposure_repo.get_bills_for_company("BSNL")
        assert any(e.bill_id == "key-issues-and-analysis" for e in bsnl_exps)

        vi_exps = exposure_repo.get_bills_for_company("Vodafone Idea")
        assert any(e.bill_id == "key-issues-and-analysis" for e in vi_exps)

    def test_swiggy_exposed_to_telangana_gig_bill(self, exposure_repo: CompanyExposureRepository):
        exps = exposure_repo.get_bills_for_company("Swiggy")
        bill_ids = [e.bill_id for e in exps]
        assert "telangana-vs-bill-11-2024" in bill_ids


# ------------------------------------------------------------------------------
# 2. Bill -> Intelligence Company Reverse Lookup
# ------------------------------------------------------------------------------

class TestBillToIntelligenceCompanyReverseLookup:
    """2. Querying a bill retrieves exposed intelligence companies."""

    def test_bills_of_lading_reverse_lookup(self, exposure_repo: CompanyExposureRepository):
        comps = exposure_repo.get_companies_for_bill("the-bills-of-lading-bill-2024")
        company_ids = [c.company_id for c in comps]
        # Must include Adani Ports, CONCOR, Delhivery
        assert "INE742F01042" in company_ids
        assert "INE399C01030" in company_ids
        assert "INE201M01025" in company_ids

    def test_aviation_bill_reverse_lookup(self, exposure_repo: CompanyExposureRepository):
        comps = exposure_repo.get_companies_for_bill("the-bharatiya-vayuyan-vidheyak-2024")
        company_ids = [c.company_id for c in comps]
        assert "INE043D01016" in company_ids  # GMR Airports
        assert "INE233B01017" in company_ids  # Blue Dart

    def test_railways_bill_reverse_lookup(self, exposure_repo: CompanyExposureRepository):
        comps = exposure_repo.get_companies_for_bill("the-railways-amendment-bill-2024")
        company_ids = [c.company_id for c in comps]
        assert "INE053F01010" in company_ids  # IRFC
        assert "INE399C01030" in company_ids  # CONCOR


# ------------------------------------------------------------------------------
# 3. Evidence Mandatory for Positive Exposure
# ------------------------------------------------------------------------------

class TestEvidenceMandatoryForPositiveExposure:
    """3. Positive exposures must contain verifiable statutory and corporate evidence."""

    def test_all_central_exposures_have_evidence(self, exposure_repo: CompanyExposureRepository):
        for exp in exposure_repo.get_all_central():
            assert len(exp.evidence) >= 2, f"Central exposure {exp.company_name} in {exp.bill_id} lacks sufficient evidence"
            source_types = [ev.source_type for ev in exp.evidence]
            assert "bill_text" in source_types
            assert any(st in ["company_filing", "annual_report", "government_record", "official_website"] for st in source_types)

    def test_evidence_claims_are_substantial(self, exposure_repo: CompanyExposureRepository):
        for exp in exposure_repo.get_all_central():
            for ev in exp.evidence:
                assert len(ev.reference.strip()) > 5
                assert len(ev.claim.strip()) > 20


# ------------------------------------------------------------------------------
# 4. Rejection of Unsupported Exposure
# ------------------------------------------------------------------------------

class TestUnsupportedExposureRejectedOrUnknown:
    """4. Companies with no relevant activity receive NONE or is_exposed=False."""

    def test_swiggy_not_exposed_to_boilers_bill(self, engine: StateCorporateExposureEngine, company_repo: CompanyRepository):
        bill_repo = BillRepository()
        swiggy = company_repo.get_by_isin("PRIV-BUNDL-SWIGGY")
        boilers_bill = bill_repo.get("the-boilers-bill-2024")
        assert boilers_bill is not None
        explanation = engine.explain_exposure(bill=boilers_bill, company=swiggy)
        assert explanation["is_exposed"] is False
        assert explanation["conceptual_chain"]["exposure_type"] == "NONE"

    def test_ireda_not_exposed_to_shipping_bill(self, engine: StateCorporateExposureEngine, company_repo: CompanyRepository):
        bill_repo = BillRepository()
        ireda = company_repo.get_by_isin("INE202E01016")
        shipping_bill = bill_repo.get("the-coastal-shipping-bill-2024")
        assert shipping_bill is not None
        explanation = engine.explain_exposure(bill=shipping_bill, company=ireda)
        assert explanation["is_exposed"] is False


# ------------------------------------------------------------------------------
# 5. Direct vs Indirect Classification
# ------------------------------------------------------------------------------

class TestDirectVsIndirectClassification:
    """5. Direct and indirect exposures must be cleanly distinguished."""

    def test_direct_exposure_cases(self, exposure_repo: CompanyExposureRepository):
        assert exposure_repo.is_direct_exposure("the-coastal-shipping-bill-2024", "Adani Ports") == "DIRECT"
        assert exposure_repo.is_direct_exposure("the-railways-amendment-bill-2024", "IRFC") == "DIRECT"
        assert exposure_repo.is_direct_exposure("the-bharatiya-vayuyan-vidheyak-2024", "GMR Airports") == "DIRECT"

    def test_indirect_exposure_cases(self, exposure_repo: CompanyExposureRepository):
        assert exposure_repo.is_direct_exposure("the-bills-of-lading-bill-2024", "Delhivery") == "INDIRECT"

    def test_all_exposures_have_valid_directness(self, exposure_repo: CompanyExposureRepository):
        for exp in exposure_repo.get_all():
            assert exp.direct_indirect in ["DIRECT", "INDIRECT"]


# ------------------------------------------------------------------------------
# 6. Exposure Strength Validation
# ------------------------------------------------------------------------------

class TestExposureStrengthValidation:
    """6. Exposure strength must be evidence-based (HIGH, MEDIUM, LOW)."""

    def test_high_strength_examples(self, exposure_repo: CompanyExposureRepository):
        irfc_exp = next(e for e in exposure_repo.get_by_bill("the-railways-amendment-bill-2024") if "IRFC" in e.company_name or e.company_id == "INE053F01010")
        assert irfc_exp.exposure_strength == "HIGH"

    def test_medium_strength_examples(self, exposure_repo: CompanyExposureRepository):
        delhivery_exp = next(e for e in exposure_repo.get_by_bill("the-bills-of-lading-bill-2024") if "Delhivery" in e.company_name)
        assert delhivery_exp.exposure_strength == "MEDIUM"

    def test_low_strength_examples(self, exposure_repo: CompanyExposureRepository):
        fortis_exp = next(e for e in exposure_repo.get_by_bill("the-water-prevention-and-control-of-pollution-amendment-bill-2024") if "Fortis" in e.company_name)
        assert fortis_exp.exposure_strength == "LOW"

    def test_strength_values_bounded(self, exposure_repo: CompanyExposureRepository):
        for exp in exposure_repo.get_all():
            assert exp.exposure_strength in ["HIGH", "MEDIUM", "LOW", "UNKNOWN"]


# ------------------------------------------------------------------------------
# 7. Economic Mechanism Validation
# ------------------------------------------------------------------------------

class TestEconomicMechanismValidation:
    """7. Mechanisms must belong to approved project taxonomy."""

    ALLOWED_MECHANISMS = {
        "compliance", "compliance_cost", "taxation", "regulation", "licensing",
        "labour_requirement", "labour_cost", "infrastructure_access", "procurement",
        "market_access", "supply_chain", "consumer_demand", "financing", "land", "energy", "pricing"
    }

    def test_mechanisms_conform_to_taxonomy(self, exposure_repo: CompanyExposureRepository):
        for exp in exposure_repo.get_all():
            assert exp.mechanism in self.ALLOWED_MECHANISMS, f"Invalid mechanism: {exp.mechanism} in {exp.company_name}"

    def test_specific_mechanism_mappings(self, exposure_repo: CompanyExposureRepository):
        assert exposure_repo.get_economic_mechanism("the-railways-amendment-bill-2024", "IRFC") == "financing"
        assert exposure_repo.get_economic_mechanism("key-issues-and-analysis", "BSNL") == "procurement"
        assert exposure_repo.get_economic_mechanism("key-issues-and-analysis", "Vodafone Idea") == "licensing"
        assert exposure_repo.get_economic_mechanism("the-coastal-shipping-bill-2024", "Adani Ports") == "market_access"


# ------------------------------------------------------------------------------
# 8. State Presence Requirement for State Exposure
# ------------------------------------------------------------------------------

class TestStatePresenceRequirement:
    """8. State bills require verified operational presence in that State."""

    def test_fortis_not_exposed_to_kerala_clinical_bill_due_to_no_presence(
        self, engine: StateCorporateExposureEngine, company_repo: CompanyRepository
    ):
        state_bill_repo = StateBillRepository()
        fortis = company_repo.get_by_isin("INE061F01013")
        kerala_bill = state_bill_repo.get("kerala-vs-bill-223-2024")
        assert kerala_bill is not None
        explanation = engine.explain_exposure(bill=kerala_bill, company=fortis)
        # Fortis has no verified presence in Kerala
        assert explanation["is_exposed"] is False

    def test_apgenco_has_andhra_presence(self, exposure_repo: CompanyExposureRepository):
        ap_exps = exposure_repo.state_repo.get_by_company("UNLISTED-AP-GENCO")
        assert len(ap_exps) > 0
        for exp in ap_exps:
            assert exp.state == "Andhra Pradesh"


# ------------------------------------------------------------------------------
# 9. Intelligence Companies Cannot Enter Quantitative Predictions
# ------------------------------------------------------------------------------

class TestQuantitativeFirewallIsolation:
    """9. Intelligence companies are strictly excluded from prediction pipelines."""

    def test_no_intelligence_isin_in_prediction_files(self, intelligence_companies: list[Company]):
        intel_isins = {c.isin for c in intelligence_companies}
        pred_dir = settings.DATA_DIR / "predictions"
        if pred_dir.exists():
            for pf in pred_dir.glob("pred_*.json"):
                for isin in intel_isins:
                    assert isin not in pf.name, f"Firewall breach: {isin} found in {pf.name}"

    def test_no_intelligence_isin_in_central_mappings(self, intelligence_companies: list[Company]):
        intel_isins = {c.isin for c in intelligence_companies}
        mapping_repo = MappingRepository()
        for mapping in mapping_repo.get_all():
            for c in mapping.candidate_companies:
                c_isin = c.get("isin", "")
                assert c_isin not in intel_isins, f"Firewall breach: {c_isin} in mapping {mapping.bill_id}"


# ------------------------------------------------------------------------------
# 10. Central Quantitative Baseline Unchanged
# ------------------------------------------------------------------------------

class TestCentralQuantitativeBaselineUnchanged:
    """10. Central baseline (47 companies, 940 pairs, 4700 predictions) is frozen."""

    def test_central_prediction_files_count(self):
        pred_dir = settings.DATA_DIR / "predictions"
        files = list(pred_dir.glob("pred_*.json"))
        assert len(files) == 4700

    def test_central_mapping_records_count(self):
        mapping_repo = MappingRepository()
        mappings = mapping_repo.get_all()
        assert len(mappings) == 22


# ------------------------------------------------------------------------------
# 11. Existing State Exposure Records Remain Intact
# ------------------------------------------------------------------------------

class TestStateExposureBaselinePreserved:
    """11. The 86 validated State corporate exposure records are preserved intact."""

    def test_state_exposure_count_is_86(self, exposure_repo: CompanyExposureRepository):
        state_exps = exposure_repo.get_all_state()
        assert len(state_exps) == 86

    def test_state_breakdown_matches_validated_baseline(self, exposure_repo: CompanyExposureRepository):
        state_exps = exposure_repo.get_all_state()
        ap = sum(1 for e in state_exps if e.state == "Andhra Pradesh")
        ka = sum(1 for e in state_exps if e.state == "Karnataka")
        kl = sum(1 for e in state_exps if e.state == "Kerala")
        ts = sum(1 for e in state_exps if e.state == "Telangana")

        assert ap == 47
        assert ka == 16
        assert kl == 3
        assert ts == 20


# ------------------------------------------------------------------------------
# 12. State Predictions Strictly Zero
# ------------------------------------------------------------------------------

class TestStatePredictionsRemainZero:
    """12. State stock market predictions must remain exactly 0."""

    def test_state_prediction_directory_empty_or_absent(self):
        state_pred_dir = settings.DATA_DIR / "state_predictions"
        if state_pred_dir.exists():
            files = list(state_pred_dir.glob("*.json"))
            assert len(files) == 0

    def test_no_forbidden_predictive_terms_in_any_exposure(self, exposure_repo: CompanyExposureRepository):
        import re
        for exp in exposure_repo.get_all():
            full_text = f"{exp.company_name} {exp.business_activity} {exp.exposure_type} {exp.mechanism} {exp.market_relevance}".lower()
            for ev in exp.evidence:
                full_text += f" {ev.claim} {ev.reference}".lower()
            for forbidden in _FORBIDDEN_PREDICTIVE_TERMS:
                pattern = rf"\b{re.escape(forbidden)}\b"
                assert not re.search(pattern, full_text), f"Forbidden term '{forbidden}' found in {exp.company_name}"


# ------------------------------------------------------------------------------
# 13. Duplicate Exposure Detection
# ------------------------------------------------------------------------------

class TestDuplicateExposureDetection:
    """13. No duplicate (bill_id, company_id) exposure records."""

    def test_zero_duplicate_exposures(self, exposure_repo: CompanyExposureRepository):
        duplicates = exposure_repo.check_duplicates()
        assert len(duplicates) == 0, f"Duplicate exposures detected: {duplicates}"


# ------------------------------------------------------------------------------
# 14. Company Alias Matching
# ------------------------------------------------------------------------------

class TestCompanyAliasMatching:
    """14. System resolves company nicknames, brand names, and acronyms."""

    def test_swiggy_alias_resolves(self, exposure_repo: CompanyExposureRepository):
        exps = exposure_repo.get_bills_for_company("Swiggy")
        assert len(exps) >= 1

    def test_bsnl_alias_resolves(self, exposure_repo: CompanyExposureRepository):
        exps = exposure_repo.get_bills_for_company("BSNL")
        assert any(e.bill_id == "key-issues-and-analysis" for e in exps)

    def test_apsez_alias_resolves(self, exposure_repo: CompanyExposureRepository):
        exps = exposure_repo.get_bills_for_company("APSEZ")
        assert len(exps) >= 4

    def test_concor_alias_resolves(self, exposure_repo: CompanyExposureRepository):
        exps = exposure_repo.get_bills_for_company("CONCOR")
        assert len(exps) >= 4

    def test_irfc_alias_resolves(self, exposure_repo: CompanyExposureRepository):
        exps = exposure_repo.get_bills_for_company("IRFC")
        assert len(exps) >= 1


# ------------------------------------------------------------------------------
# 15. Provenance and Serialization Roundtrip
# ------------------------------------------------------------------------------

class TestProvenanceAndRoundtripSerialization:
    """15. Serialization and deserialization preserves all fields and provenance."""

    def test_roundtrip_central_record(self, exposure_repo: CompanyExposureRepository):
        central_exps = exposure_repo.get_all_central()
        assert len(central_exps) > 0
        sample = central_exps[0]

        d = sample.to_dict()
        reconstructed = StateCorporateExposure.from_dict(d)

        assert reconstructed.bill_id == sample.bill_id
        assert reconstructed.company_id == sample.company_id
        assert reconstructed.company_name == sample.company_name
        assert reconstructed.jurisdiction == sample.jurisdiction
        assert reconstructed.market_relevance == sample.market_relevance
        assert reconstructed.direct_indirect == sample.direct_indirect
        assert reconstructed.mechanism == sample.mechanism
        assert len(reconstructed.evidence) == len(sample.evidence)
        assert reconstructed.provenance == sample.provenance
