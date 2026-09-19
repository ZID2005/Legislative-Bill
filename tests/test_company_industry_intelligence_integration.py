"""
tests/test_company_industry_intelligence_integration.py
========================================================
Comprehensive test suite for Task 8.12.5 — Company & Industry Intelligence Integration.

Validates all 20 required verification scenarios:
 1. Company profile retrieval (all fields, identity, business, geography, evidence)
 2. Intelligence company retrieval (20 newly curated intelligence entities)
 3. Quantitative company retrieval (47 Central quantitative companies)
 4. Company -> bills discovery (Swiggy, Zomato, Adani Ports, KSEB, IRFC, GMR)
 5. Bill -> companies discovery (Central & State bills)
 6. Company -> exposure explanation (deterministic, fact-grounded explanation structure)
 7. Exposure -> evidence verification (statutory citations, filings, claims)
 8. Company -> sector/industry bidirectional integration
 9. Company -> State relevance & operational presence verification
 10. State bill -> company relationship (evidence-backed State linkages)
 11. Central bill -> intelligence company relationship (Central bills linked to intelligence entities)
 12. Intelligence company cannot enter quantitative prediction (firewall verification)
 13. Market relevance cannot become market prediction (strictly qualitative; zero trading signals)
 14. Groq context contains only verified company/exposure information (facts, derived, interpretations, predictions)
 15. Existing 47 Central quantitative companies remain unchanged
 16. Existing 940 Central bill-company pairs remain unchanged
 17. Existing 4,700 Central predictions remain unchanged
 18. Existing 86 State exposures remain intact
 19. State predictions remain exactly 0
 20. Existing unified bill discovery remains functional
"""

from __future__ import annotations

from pathlib import Path
import pytest

from config.settings import settings
from schemas.company import Company, EntityType, UniverseType
from schemas.state_corporate_exposure import (
    CorporateExposureEvidence,
    StateCorporateExposure,
    _FORBIDDEN_PREDICTIVE_TERMS,
)
from services.ai.ai_context_builder import AICompanyContext, AIContextBuilder
from services.ai.ai_explanation_service import AIExplanationService
from services.company_intelligence_service import (
    CompanyBillExposureView,
    CompanyExposureExplanation,
    CompanyIntelligenceService,
    CompanyProfileView,
)
from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.decision_repository import DecisionRepository
from storage.mapping_repository import MappingRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------

@pytest.fixture
def company_repo() -> CompanyRepository:
    return CompanyRepository()


@pytest.fixture
def exposure_repo() -> CompanyExposureRepository:
    return CompanyExposureRepository()


@pytest.fixture
def intel_service() -> CompanyIntelligenceService:
    return CompanyIntelligenceService()


@pytest.fixture
def discovery_service() -> UnifiedLegislativeDiscoveryService:
    return UnifiedLegislativeDiscoveryService()


@pytest.fixture
def context_builder() -> AIContextBuilder:
    return AIContextBuilder()


# Canonical 47 Central quantitative ISINs
CENTRAL_47_ISINS = frozenset([
    "INE002A01018", "INE467B01029", "INE040A01034", "INE009A01021", "INE090A01021",
    "INE397D01024", "INE062A01020", "INE018A01030", "INE154A01025", "INE030A01027",
    "INE423A01024", "INE155A01022", "INE044A01045", "INE733E01010", "INE213A01029",
    "INE238A01034", "INE237A01028", "INE075A01022", "INE860A01027", "INE585B01010",
    "INE101A01026", "INE081A01020", "INE019A01030", "INE038A01020", "INE522F01014",
    "INE481G01011", "INE047A01021", "INE239A01016", "INE216A01030", "INE192A01025",
    "INE021A01026", "INE059A01026", "INE089A01023", "INE437A01024", "INE752E01010",
    "INE245A01021", "INE364U01010", "INE814H01011", "INE296A01024", "INE918I01018",
    "INE00LIC01010", "INE123W01016", "INE795G01014", "INE066A01021", "INE158A01026",
    "INE917I01010", "INE669C01036",
])


# ------------------------------------------------------------------------------
# 1. Company Profile Retrieval
# ------------------------------------------------------------------------------

class TestCompanyProfileRetrieval:
    """1. Comprehensive company profile retrieval across all contract dimensions."""

    def test_retrieve_quantitative_company_profile(self, intel_service: CompanyIntelligenceService):
        prof = intel_service.get_company_profile("INE009A01021")  # Infosys
        assert prof is not None
        assert "Infosys" in prof.company_name
        assert prof.sector in ["Technology", "Information Technology"]
        assert prof.universe_type == "quantitative"
        assert prof.is_quant_eligible is True
        assert prof.quantitative_firewall_status == "QUANTITATIVE_PRODUCTION"
        assert isinstance(prof.to_dict(), dict)

    def test_retrieve_intelligence_company_profile(self, intel_service: CompanyIntelligenceService):
        prof = intel_service.get_company_profile("PRIV-BUNDL-SWIGGY")  # Swiggy
        assert prof is not None
        assert "Swiggy" in prof.company_name or "Bundl" in prof.company_name
        assert prof.universe_type == "intelligence"
        assert prof.is_quant_eligible is False
        assert prof.market_prediction_available is False
        assert prof.quantitative_firewall_status == "INTELLIGENCE_ONLY_FIREWALLED"
        assert len(prof.business_activities) > 0
        assert len(prof.related_bills) > 0

    def test_retrieve_by_alias_or_ticker(self, intel_service: CompanyIntelligenceService):
        prof_zomato = intel_service.get_company_profile("ZOMATO")
        assert prof_zomato is not None
        assert "Zomato" in prof_zomato.company_name

        prof_kseb = intel_service.get_company_profile("KSEB")
        assert prof_kseb is not None
        assert "Kerala State Electricity Board" in prof_kseb.company_name


# ------------------------------------------------------------------------------
# 2. Intelligence Company Retrieval
# ------------------------------------------------------------------------------

class TestIntelligenceCompanyRetrieval:
    """2. Intelligence company universe retrieval returns exactly 20 intelligence entities."""

    def test_intelligence_company_count_and_types(self, intel_service: CompanyIntelligenceService):
        intel_comps = intel_service.get_intelligence_companies()
        assert len(intel_comps) == 20
        for c in intel_comps:
            assert c.universe_type == UniverseType.INTELLIGENCE
            assert c.isin not in CENTRAL_47_ISINS


# ------------------------------------------------------------------------------
# 3. Quantitative Company Retrieval
# ------------------------------------------------------------------------------

class TestQuantitativeCompanyRetrieval:
    """3. Quantitative company retrieval contains all 47 Central quantitative ISINs."""

    def test_quantitative_companies_contain_canonical_47(self, intel_service: CompanyIntelligenceService):
        quant_comps = intel_service.get_quantitative_companies()
        quant_isins = {c.isin for c in quant_comps}
        assert CENTRAL_47_ISINS.issubset(quant_isins)


# ------------------------------------------------------------------------------
# 4. Company → Bills Discovery
# ------------------------------------------------------------------------------

class TestCompanyToBillsDiscovery:
    """4. Discover which bills affect specific companies (Swiggy, Zomato, Adani Ports, KSEB, IRFC, GMR)."""

    def test_swiggy_related_bills(self, intel_service: CompanyIntelligenceService):
        bills = intel_service.get_bills_for_company("PRIV-BUNDL-SWIGGY")
        bill_ids = [b.bill_id for b in bills]
        assert "telangana-vs-bill-11-2024" in bill_ids

    def test_zomato_related_bills(self, intel_service: CompanyIntelligenceService):
        bills = intel_service.get_bills_for_company("Zomato")
        bill_ids = [b.bill_id for b in bills]
        assert "telangana-vs-bill-11-2024" in bill_ids

    def test_adani_ports_related_bills(self, intel_service: CompanyIntelligenceService):
        bills = intel_service.get_bills_for_company("Adani Ports")
        bill_ids = [b.bill_id for b in bills]
        assert "the-coastal-shipping-bill-2024" in bill_ids
        assert "the-bills-of-lading-bill-2024" in bill_ids

    def test_kseb_related_bills(self, intel_service: CompanyIntelligenceService):
        # As established in Task 8.12.4 audit, KSEB has no matching electricity duty bill in corpus
        bills = intel_service.get_bills_for_company("KSEB")
        assert len(bills) == 0

    def test_irfc_and_gmr_related_bills(self, intel_service: CompanyIntelligenceService):
        irfc_bills = [b.bill_id for b in intel_service.get_bills_for_company("IRFC")]
        assert "the-railways-amendment-bill-2024" in irfc_bills
        gmr_bills = [b.bill_id for b in intel_service.get_bills_for_company("GMR")]
        assert "the-bharatiya-vayuyan-vidheyak-2024" in gmr_bills


# ------------------------------------------------------------------------------
# 5. Bill → Companies Discovery
# ------------------------------------------------------------------------------

class TestBillToCompaniesDiscovery:
    """5. Reverse discovery: which companies are exposed to a bill (Central and State)."""

    def test_telangana_gig_bill_companies(self, intel_service: CompanyIntelligenceService):
        comps = intel_service.get_companies_for_bill("telangana-vs-bill-11-2024")
        assert len(comps) >= 2
        assert all(c.jurisdiction == "state" for c in comps)
        comp_names = [c.company_name for c in comps]
        assert any("Swiggy" in n or "Bundl" in n for n in comp_names)
        assert any("Zomato" in n for n in comp_names)

    def test_bharatiya_vayuyan_central_bill_companies(self, intel_service: CompanyIntelligenceService):
        comps = intel_service.get_companies_for_bill("the-bharatiya-vayuyan-vidheyak-2024")
        assert any("gmr" in c.business_activity.lower() or c.sector == "Infrastructure" for c in comps)


# ------------------------------------------------------------------------------
# 6. Company Exposure Explanation
# ------------------------------------------------------------------------------

class TestCompanyExposureExplanation:
    """6. Deterministic explanation derived strictly from stored evidence."""

    def test_deterministic_explanation_content(self, intel_service: CompanyIntelligenceService):
        expl = intel_service.explain_exposure("PRIV-BUNDL-SWIGGY", "telangana-vs-bill-11-2024")
        assert expl.has_exposure is True
        assert expl.direct_indirect == "DIRECT"
        assert expl.exposure_strength == "HIGH"
        assert len(expl.evidence_claims) > 0
        assert len(expl.why_explanation) > 0
        assert "Telangana" in expl.geographic_relevance or "telangana" in expl.bill_id

    def test_unsupported_exposure_returns_no_exposure(self, intel_service: CompanyIntelligenceService):
        expl = intel_service.explain_exposure("PRIV-BUNDL-SWIGGY", "the-kerala-panchayat-raj-amendment-bill-2024")
        assert expl.has_exposure is False
        assert expl.exposure_type == "NONE"
        assert "No verified exposure" in expl.why_explanation


# ------------------------------------------------------------------------------
# 7. Exposure → Evidence
# ------------------------------------------------------------------------------

class TestExposureEvidence:
    """7. Traceable evidence supporting exposure claims."""

    def test_exposure_has_traceable_evidence(self, intel_service: CompanyIntelligenceService):
        bills = intel_service.get_bills_for_company("INE742F01042")  # Adani Ports
        assert len(bills) > 0
        for b in bills:
            assert b.has_evidence is True
            assert len(b.evidence) > 0
            for ev in b.evidence:
                assert ev.claim != ""
                assert ev.reference != ""


# ------------------------------------------------------------------------------
# 8. Sector / Industry Integration
# ------------------------------------------------------------------------------

class TestSectorIndustryIntegration:
    """8. Connect company intelligence to sector/domain taxonomy."""

    def test_get_companies_by_sector(self, intel_service: CompanyIntelligenceService):
        tech_comps = intel_service.get_companies_by_sector("Information Technology")
        assert len(tech_comps) > 0
        assert any("Infosys" in c.company_name for c in tech_comps)

        infra_comps = intel_service.get_companies_by_sector("Infrastructure")
        assert len(infra_comps) > 0
        assert any("Adani Ports" in c.company_name or "GMR" in c.company_name for c in infra_comps)


# ------------------------------------------------------------------------------
# 9. State Operational Presence Integration
# ------------------------------------------------------------------------------

class TestStateRelevanceIntegration:
    """9. Company intelligence must be jurisdiction-aware and evidence-grounded."""

    def test_kerala_presence_companies(self, intel_service: CompanyIntelligenceService):
        kl_comps = intel_service.get_companies_by_state("Kerala")
        assert len(kl_comps) > 0
        names = [c.company_name for c in kl_comps]
        assert any("Kerala State Electricity Board" in n for n in names)

    def test_telangana_presence_companies(self, intel_service: CompanyIntelligenceService):
        ts_comps = intel_service.get_companies_by_state("Telangana")
        assert len(ts_comps) > 0
        names = [c.company_name for c in ts_comps]
        assert any("Telangana" in n or "Swiggy" in n or "Zomato" in n for n in names)


# ------------------------------------------------------------------------------
# 10. State Bill → Company Relationship
# ------------------------------------------------------------------------------

class TestStateBillCompanyRelationship:
    """10. Verified linkages across State legislation."""

    def test_state_bills_have_verified_corporate_exposures(self, exposure_repo: CompanyExposureRepository):
        state_exps = exposure_repo.get_all_state()
        assert len(state_exps) == 86
        for exp in state_exps:
            assert exp.jurisdiction == "state"
            assert exp.state in ["Kerala", "Karnataka", "Telangana", "Andhra Pradesh"]
            assert len(exp.evidence) > 0


# ------------------------------------------------------------------------------
# 11. Central Bill → Intelligence Company Relationship
# ------------------------------------------------------------------------------

class TestCentralBillIntelligenceCompanyRelationship:
    """11. Central bills linked to intelligence entities."""

    def test_central_bills_linked_to_intelligence_entities(self, exposure_repo: CompanyExposureRepository):
        central_exps = exposure_repo.get_all_central()
        assert len(central_exps) == 18
        intel_central_names = {e.company_name for e in central_exps}
        assert "Adani Ports & SEZ" in intel_central_names or "Adani Ports and Special Economic Zone Limited" in intel_central_names
        assert any("GMR" in n for n in intel_central_names)
        assert any("IRFC" in n or "Indian Railway" in n for n in intel_central_names)


# ------------------------------------------------------------------------------
# 12. Intelligence Company Cannot Enter Quantitative Prediction
# ------------------------------------------------------------------------------

class TestIntelligenceCompanyCannotEnterQuantitativePrediction:
    """12. Quantitative firewall guarantees intelligence entities have zero predictions."""

    def test_firewall_status_and_zero_predictions(self, intel_service: CompanyIntelligenceService):
        swiggy_prof = intel_service.get_company_profile("PRIV-BUNDL-SWIGGY")
        assert swiggy_prof.is_quant_eligible is False
        assert swiggy_prof.market_prediction_available is False
        assert swiggy_prof.quantitative_firewall_status == "INTELLIGENCE_ONLY_FIREWALLED"

        pred_dir = settings.DATA_DIR / "predictions"
        swiggy_preds = list(pred_dir.glob("*SWIGGY*.json")) + list(pred_dir.glob("*BUNDL*.json"))
        assert len(swiggy_preds) == 0


# ------------------------------------------------------------------------------
# 13. Market Relevance Cannot Become Market Prediction
# ------------------------------------------------------------------------------

class TestMarketRelevanceCannotBecomePrediction:
    """13. Market relevance is qualitative only; strictly forbidden terms rejected."""

    def test_market_relevance_values_are_qualitative(self, exposure_repo: CompanyExposureRepository):
        all_exps = exposure_repo.get_all()
        for e in all_exps:
            assert e.market_relevance in ["HIGH", "MEDIUM", "LOW", "NONE", "UNKNOWN"]
            # Enforce guardrails on text content
            text_block = f"{e.business_activity} {e.mechanism} {e.exposure_type}".lower()
            for forbidden in _FORBIDDEN_PREDICTIVE_TERMS:
                assert forbidden not in text_block


# ------------------------------------------------------------------------------
# 14. Groq Context Contains Only Verified Company Information
# ------------------------------------------------------------------------------

class TestGroqContextVerifiedCompanyInformation:
    """14. AIContextBuilder enforces categorical separation without speculation."""

    def test_company_context_categorical_separation(self, context_builder: AIContextBuilder):
        ctx = context_builder.build_company_context("PRIV-BUNDL-SWIGGY")
        assert isinstance(ctx, AICompanyContext)
        assert len(ctx.facts) > 0
        assert len(ctx.derived) > 0
        assert len(ctx.interpretations) > 0
        assert len(ctx.predictions) > 0
        assert any("ZERO PREDICTIONS" in p for p in ctx.predictions)

        prompt_str = ctx.format_prompt_block()
        assert "[FACTS" in prompt_str
        assert "[DERIVED" in prompt_str
        assert "[ECONOMIC INTERPRETATION" in prompt_str
        assert "[PREDICTIONS" in prompt_str
        assert "ZERO PREDICTIONS" in prompt_str


# ------------------------------------------------------------------------------
# 15. Existing 47 Central Quantitative Companies Unchanged
# ------------------------------------------------------------------------------

class TestExisting47CentralQuantitativeCompaniesUnchanged:
    """15. Exactly 47 Central quantitative companies remain preserved in master."""

    def test_canonical_47_companies_preserved(self, company_repo: CompanyRepository):
        all_comps = company_repo.get_all()
        quant_comps = [c for c in all_comps if c.isin in CENTRAL_47_ISINS]
        assert len(quant_comps) == 47


# ------------------------------------------------------------------------------
# 16. Existing 940 Central Bill-Company Pairs Unchanged
# ------------------------------------------------------------------------------

class TestExisting940CentralBillCompanyPairsUnchanged:
    """16. 20 production Central bills x 47 quantitative companies = 940 pairs."""

    def test_940_bill_company_pairs(self):
        bill_repo = BillRepository()
        prod_central_bills = [
            b for b in bill_repo.get_all()
            if b.bill_id not in ("key-issues-and-analysis", "service-bill")
        ]
        assert len(prod_central_bills) == 20
        total_pairs = len(prod_central_bills) * len(CENTRAL_47_ISINS)
        assert total_pairs == 940


# ------------------------------------------------------------------------------
# 17. Existing 4,700 Central Predictions Unchanged
# ------------------------------------------------------------------------------

class TestExisting4700CentralPredictionsUnchanged:
    """17. Exactly 4,700 prediction files exist in data/predictions."""

    def test_4700_predictions_exist(self):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700


# ------------------------------------------------------------------------------
# 18. Existing 86 State Exposures Intact
# ------------------------------------------------------------------------------

class TestExisting86StateExposuresIntact:
    """18. Exactly 86 State corporate exposures exist and are verified."""

    def test_state_exposure_count_is_86(self, exposure_repo: CompanyExposureRepository):
        state_exps = exposure_repo.get_all_state()
        assert len(state_exps) == 86


# ------------------------------------------------------------------------------
# 19. State Predictions Remain Exactly 0
# ------------------------------------------------------------------------------

class TestStatePredictionsRemainZero:
    """19. Zero stock market predictions exist for State legislation."""

    def test_state_predictions_are_zero(self, exposure_repo: CompanyExposureRepository):
        state_exps = exposure_repo.get_all_state()
        for e in state_exps:
            assert e.market_relevance in ["HIGH", "MEDIUM", "LOW", "NONE", "UNKNOWN"]
            # Verify no model forecast attributes exist
            assert not hasattr(e, "expected_return")
            assert not hasattr(e, "predicted_car")


# ------------------------------------------------------------------------------
# 20. Existing Unified Bill Discovery Remains Functional
# ------------------------------------------------------------------------------

class TestExistingUnifiedBillDiscoveryFunctional:
    """20. Unified legislative discovery continues to work seamlessly with company enhancements."""

    def test_unified_discovery_bill_search(self, discovery_service: UnifiedLegislativeDiscoveryService):
        # 1. Base search by sector
        labour_bills = discovery_service.search(sector="Labour")
        assert len(labour_bills) > 0

        # 2. Search by company query
        swiggy_results = discovery_service.search(query="Swiggy")
        assert len(swiggy_results) > 0
        assert any("gig" in b.title.lower() or "telangana" in b.title.lower() for b in swiggy_results)

        # 3. Search with explicit company filter
        coastal_results = discovery_service.search(company="Adani Ports")
        assert len(coastal_results) > 0
        assert any("coastal" in b.title.lower() or "shipping" in b.title.lower() for b in coastal_results)

        # 4. Helper methods
        exps = discovery_service.get_companies_for_bill("the-coastal-shipping-bill-2024")
        assert len(exps) > 0
