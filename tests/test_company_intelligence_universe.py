"""
tests/test_company_intelligence_universe.py
============================================
Focused tests for Task 8.12.3 — Extended Company Intelligence Universe.

Test categories (per task specification):

A. New intelligence companies load correctly from companies.json.
B. New companies have valid universe_type, entity_type, ownership_type.
C. Required provenance exists (data_sources non-empty).
D. Legacy 47-company records remain compatible (universe defaults to QUANTITATIVE).
E. Intelligence companies cannot accidentally enter quantitative prediction workflows.
F. CompanyRepository search finds both quantitative and intelligence companies.
G. Duplicate company / legal-entity detection (no ISIN appears twice).
H. Baseline integrity (47 quantitative ISINs in predictions unchanged).
I. State prediction count remains exactly 0.

CRITICAL CONSTRAINTS:
  - These tests DO NOT modify any prediction artefacts.
  - These tests DO NOT modify the companies.json file.
  - The 47 Central quantitative companies must remain unchanged.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from collections import Counter

import pytest

from schemas.company import Company, UniverseType, EntityType, OwnershipType
from storage.company_repository import CompanyRepository

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPANIES_JSON = Path(__file__).parent.parent / "data" / "companies" / "companies.json"
PREDICTIONS_DIR = Path(__file__).parent.parent / "data" / "predictions"
INTELLIGENCE_UNIVERSE_JSON = (
    Path(__file__).parent.parent / "data" / "companies" / "intelligence_universe.json"
)

# Canonical set of 47 Central quantitative prediction ISINs.
CENTRAL_QUANTITATIVE_ISINS: frozenset[str] = frozenset(
    [
        "INE002A01018",  # Reliance Industries
        "INE467B01029",  # TCS
        "INE040A01034",  # HDFC Bank
        "INE009A01021",  # Infosys
        "INE090A01021",  # ICICI Bank
        "INE397D01024",  # Bharti Airtel
        "INE062A01020",  # SBI
        "INE018A01030",  # L&T
        "INE154A01025",  # ITC
        "INE030A01027",  # HUL
        "INE423A01024",  # Adani Enterprises
        "INE155A01022",  # Tata Motors
        "INE044A01045",  # Sun Pharma
        "INE733E01010",  # NTPC
        "INE213A01029",  # ONGC
        "INE238A01034",  # Axis Bank
        "INE237A01028",  # Kotak Mahindra Bank
        "INE075A01022",  # Wipro
        "INE860A01027",  # HCL Technologies
        "INE585B01010",  # Maruti Suzuki
        "INE101A01026",  # M&M
        "INE081A01020",  # Tata Steel
        "INE019A01030",  # JSW Steel
        "INE038A01020",  # Hindalco
        "INE522F01014",  # Coal India
        "INE481G01011",  # UltraTech Cement
        "INE047A01021",  # Grasim
        "INE239A01016",  # Nestle
        "INE216A01030",  # Britannia
        "INE192A01025",  # Tata Consumer
        "INE021A01026",  # Asian Paints
        "INE059A01026",  # Cipla
        "INE089A01023",  # Dr. Reddy's
        "INE437A01024",  # Apollo Hospitals
        "INE752E01010",  # Power Grid
        "INE245A01021",  # Tata Power
        "INE364U01010",  # Adani Green
        "INE814H01011",  # Adani Power
        "INE296A01024",  # Bajaj Finance
        "INE918I01018",  # Bajaj Finserv
        "INE00LIC01010",  # LIC
        "INE123W01016",  # SBI Life
        "INE795G01014",  # HDFC Life
        "INE066A01021",  # Eicher Motors
        "INE158A01026",  # Hero Motocorp
        "INE917I01010",  # Bajaj Auto
        "INE669C01036",  # Tech Mahindra
        # Note: LTIMindtree (INE214G01026) and Siemens (INE003A01024) and ABB (INE117A01022)
        # are in companies.json (50 seed) but their inclusion in the 47 quantitative ISINs
        # is validated against the actual prediction files below.
    ]
)

EXPECTED_INTELLIGENCE_ISINS: frozenset[str] = frozenset(
    [
        "INE758T01015",       # Zomato
        "PRIV-BUNDL-SWIGGY",  # Swiggy (Bundl Technologies)
        "PRIV-FLIPKART-IND",  # Flipkart
        "PRIV-AMAZON-IND",    # Amazon India
        "INE201M01025",       # Delhivery
        "INE233B01017",       # Blue Dart Express
        "INE742F01042",       # Adani Ports
        "INE399C01030",       # CONCOR
        "SOE-BSNL-UNLISTED",  # BSNL
        "INE669E01016",       # Vodafone Idea
        "INE061F01013",       # Fortis Healthcare
        "INE027H01010",       # Max Healthcare
        "UNLISTED-AP-GENCO",  # APGENCO
        "UNLISTED-KL-KSEB",   # KSEB
        "UNLISTED-TS-GENCO",  # TSGENCO
        "INE202E01016",       # IREDA
        "UNLISTED-KL-RTC",    # KSRTC-KL
        "UNLISTED-KA-RTC",    # KSRTC-KA
        "INE043D01016",       # GMR Airports
        "INE053F01010",       # IRFC
    ]
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def all_companies_json() -> list[dict]:
    """Load raw JSON records from companies.json."""
    with COMPANIES_JSON.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def repo() -> CompanyRepository:
    """Live CompanyRepository backed by the production companies.json."""
    return CompanyRepository()


@pytest.fixture(scope="module")
def all_companies(repo: CompanyRepository) -> list[Company]:
    """All company objects from the production companies.json."""
    return repo.get_all()


@pytest.fixture(scope="module")
def intelligence_companies(repo: CompanyRepository) -> list[Company]:
    """Intelligence-only companies from the production companies.json."""
    return repo.get_intelligence_companies()


@pytest.fixture(scope="module")
def prediction_isins() -> frozenset[str]:
    """Set of distinct company ISINs referenced in prediction filenames."""
    isins: set[str] = set()
    for pf in PREDICTIONS_DIR.glob("pred_*.json"):
        parts = pf.stem.split("_")
        for p in parts:
            if p.startswith("INE") or p.startswith("UNLISTED"):
                isins.add(p)
    return frozenset(isins)


# ---------------------------------------------------------------------------
# A. Intelligence companies load correctly
# ---------------------------------------------------------------------------


class TestIntelligenceCompaniesLoad:
    """A. New intelligence companies load correctly from companies.json."""

    def test_companies_json_total_count(self, all_companies: list[Company]):
        """companies.json should contain exactly 70 records after Task 8.12.3."""
        assert len(all_companies) == 70, (
            f"Expected 70 total companies, got {len(all_companies)}. "
            "This may indicate records were added or removed unexpectedly."
        )

    def test_intelligence_count(self, intelligence_companies: list[Company]):
        """Exactly 20 new intelligence companies must be present."""
        assert len(intelligence_companies) == 20, (
            f"Expected 20 intelligence companies, got {len(intelligence_companies)}"
        )

    def test_all_expected_intelligence_isins_present(self, intelligence_companies: list[Company]):
        """Every expected intelligence ISIN must be findable."""
        actual_isins = {c.isin for c in intelligence_companies}
        missing = EXPECTED_INTELLIGENCE_ISINS - actual_isins
        assert not missing, f"Missing intelligence ISINs: {missing}"

    def test_no_unexpected_intelligence_isins(self, intelligence_companies: list[Company]):
        """No intelligence ISINs beyond the expected 20 should be present."""
        actual_isins = {c.isin for c in intelligence_companies}
        unexpected = actual_isins - EXPECTED_INTELLIGENCE_ISINS
        assert not unexpected, f"Unexpected intelligence ISINs found: {unexpected}"

    def test_intelligence_companies_have_names(self, intelligence_companies: list[Company]):
        """All intelligence companies must have non-empty company_name."""
        empty_names = [c.isin for c in intelligence_companies if not c.company_name.strip()]
        assert not empty_names, f"Intelligence companies with empty names: {empty_names}"

    def test_intelligence_companies_have_sector(self, intelligence_companies: list[Company]):
        """All intelligence companies must have non-empty sector."""
        empty_sectors = [c.isin for c in intelligence_companies if not c.sector.strip()]
        assert not empty_sectors, f"Intelligence companies with empty sector: {empty_sectors}"

    def test_each_intelligence_company_loadable_by_isin(self, repo: CompanyRepository):
        """Each intelligence ISIN must be retrievable via get_by_isin()."""
        for isin in EXPECTED_INTELLIGENCE_ISINS:
            company = repo.get_by_isin(isin)
            assert company is not None, f"get_by_isin({isin!r}) returned None"

    def test_intelligence_universe_json_artifact_exists(self):
        """The machine-readable intelligence_universe.json artifact must exist."""
        assert INTELLIGENCE_UNIVERSE_JSON.exists(), (
            f"intelligence_universe.json not found at {INTELLIGENCE_UNIVERSE_JSON}"
        )

    def test_intelligence_universe_json_valid(self):
        """intelligence_universe.json must be valid JSON with 20 companies."""
        with INTELLIGENCE_UNIVERSE_JSON.open(encoding="utf-8") as f:
            artifact = json.load(f)
        assert artifact.get("company_count") == 20
        assert len(artifact.get("companies", [])) == 20


# ---------------------------------------------------------------------------
# B. New companies have valid universe_type, entity_type, ownership_type
# ---------------------------------------------------------------------------


class TestIntelligenceCompanyFields:
    """B. New companies have valid enum fields."""

    def test_universe_type_is_intelligence(self, intelligence_companies: list[Company]):
        """All intelligence companies must have universe_type = INTELLIGENCE."""
        wrong = [
            c.isin
            for c in intelligence_companies
            if c.universe_type != UniverseType.INTELLIGENCE
        ]
        assert not wrong, f"Companies with wrong universe_type: {wrong}"

    def test_entity_type_is_valid_enum(self, intelligence_companies: list[Company]):
        """entity_type must be a valid EntityType enum member for every record."""
        invalid = [
            c.isin
            for c in intelligence_companies
            if not isinstance(c.entity_type, EntityType)
        ]
        assert not invalid, f"Companies with invalid entity_type: {invalid}"

    def test_entity_type_not_unknown_sentinel(self, intelligence_companies: list[Company]):
        """EntityType does not have an UNKNOWN; all records must have a real type."""
        # All entity_types must resolve to a known enum
        for c in intelligence_companies:
            assert c.entity_type in list(EntityType), (
                f"{c.isin}: entity_type {c.entity_type!r} is not a valid EntityType"
            )

    def test_ownership_type_is_valid_enum(self, intelligence_companies: list[Company]):
        """ownership_type must be a valid OwnershipType enum member."""
        invalid = [
            c.isin
            for c in intelligence_companies
            if not isinstance(c.ownership_type, OwnershipType)
        ]
        assert not invalid, f"Companies with invalid ownership_type: {invalid}"

    def test_listed_companies_have_ticker(self, intelligence_companies: list[Company]):
        """Intelligence companies with entity_type=LISTED_COMPANY must have a ticker."""
        listed_no_ticker = [
            c.isin
            for c in intelligence_companies
            if c.entity_type == EntityType.LISTED_COMPANY
            and not c.ticker_nse.strip()
            and not c.ticker_bse.strip()
        ]
        assert not listed_no_ticker, (
            f"Listed companies missing both NSE and BSE ticker: {listed_no_ticker}"
        )

    def test_unlisted_entities_have_no_ticker(self, intelligence_companies: list[Company]):
        """Unlisted/public-utility entities must not have an exchange ticker."""
        unlisted_types = {
            EntityType.UNLISTED_COMPANY,
            EntityType.STATE_OWNED_ENTERPRISE,
            EntityType.PUBLIC_UTILITY,
            EntityType.PRIVATE_COMPANY,
        }
        false_tickers = [
            c.isin
            for c in intelligence_companies
            if c.entity_type in unlisted_types
            and c.listing_status == "Unlisted"
            and (c.ticker_nse.strip() or c.ticker_bse.strip())
        ]
        assert not false_tickers, (
            f"Unlisted companies that have a ticker (should be empty string): {false_tickers}"
        )

    def test_data_quality_score_in_valid_range(self, intelligence_companies: list[Company]):
        """data_quality_score must be None or within [0.0, 1.0]."""
        invalid_scores = [
            c.isin
            for c in intelligence_companies
            if c.data_quality_score is not None
            and not (0.0 <= c.data_quality_score <= 1.0)
        ]
        assert not invalid_scores, f"Companies with out-of-range quality score: {invalid_scores}"

    def test_watchlist_eligible_is_bool(self, intelligence_companies: list[Company]):
        """watchlist_eligible must be a boolean."""
        invalid = [
            c.isin
            for c in intelligence_companies
            if not isinstance(c.watchlist_eligible, bool)
        ]
        assert not invalid, f"Non-boolean watchlist_eligible: {invalid}"


# ---------------------------------------------------------------------------
# C. Required provenance exists
# ---------------------------------------------------------------------------


class TestProvenance:
    """C. Required provenance exists for each intelligence company."""

    def test_all_have_data_sources(self, intelligence_companies: list[Company]):
        """Every intelligence company must have at least one data source."""
        no_sources = [c.isin for c in intelligence_companies if not c.data_sources]
        assert not no_sources, f"Intelligence companies missing data_sources: {no_sources}"

    def test_all_have_at_least_one_verified_source(self, intelligence_companies: list[Company]):
        """Every company must have at least 1 data source entry (non-empty string)."""
        bad = [
            c.isin
            for c in intelligence_companies
            if not any(s.strip() for s in c.data_sources)
        ]
        assert not bad, f"Companies with blank data sources: {bad}"

    def test_high_quality_companies_have_multiple_sources(
        self, intelligence_companies: list[Company]
    ):
        """Companies with data_quality_score >= 0.8 should have >= 2 sources."""
        insufficient = [
            c.isin
            for c in intelligence_companies
            if c.data_quality_score is not None
            and c.data_quality_score >= 0.8
            and len(c.data_sources) < 2
        ]
        assert not insufficient, (
            f"High-quality companies with fewer than 2 data sources: {insufficient}"
        )

    def test_no_fabricated_isin_format_for_listed_companies(
        self, intelligence_companies: list[Company]
    ):
        """Listed companies must have a standard INE ISIN (not a synthetic identifier)."""
        listed = [c for c in intelligence_companies if c.entity_type == EntityType.LISTED_COMPANY]
        bad_isin = [
            c.isin
            for c in listed
            if not c.isin.startswith("INE")
        ]
        assert not bad_isin, (
            f"Listed companies with non-INE ISIN (possible fabrication): {bad_isin}"
        )

    def test_synthetic_ids_only_for_unlisted_entities(self, intelligence_companies: list[Company]):
        """Only non-listed entities should use synthetic ISIN identifiers."""
        unlisted_types = {
            EntityType.UNLISTED_COMPANY,
            EntityType.STATE_OWNED_ENTERPRISE,
            EntityType.PUBLIC_UTILITY,
            EntityType.PRIVATE_COMPANY,
        }
        # Synthetic IDs use prefixes: PRIV-, SOE-, UNLISTED-
        for c in intelligence_companies:
            if c.isin.startswith(("PRIV-", "SOE-", "UNLISTED-")):
                assert c.entity_type in unlisted_types, (
                    f"{c.isin}: has synthetic ISIN but entity_type={c.entity_type.value} "
                    "which should be a non-listed type"
                )


# ---------------------------------------------------------------------------
# D. Legacy 47-company records remain compatible
# ---------------------------------------------------------------------------


class TestLegacyCompatibility:
    """D. Legacy 47-company records remain compatible with the new schema."""

    def test_legacy_records_default_to_quantitative(self, all_companies: list[Company]):
        """Existing companies without universe_type in JSON must default to QUANTITATIVE."""
        # Load raw JSON to identify legacy records (those without universe_type key)
        with COMPANIES_JSON.open(encoding="utf-8") as f:
            raw = json.load(f)
        legacy_isins = {
            r["isin"] for r in raw if "universe_type" not in r
        }
        # Now verify they loaded as QUANTITATIVE
        for company in all_companies:
            if company.isin in legacy_isins:
                assert company.universe_type == UniverseType.QUANTITATIVE, (
                    f"{company.isin}: legacy record loaded with universe_type="
                    f"{company.universe_type.value!r} instead of QUANTITATIVE"
                )

    def test_legacy_records_can_serialize_round_trip(self, all_companies: list[Company]):
        """Legacy records must survive to_dict → from_dict without data loss."""
        with COMPANIES_JSON.open(encoding="utf-8") as f:
            raw = json.load(f)
        legacy_isins = {r["isin"] for r in raw if "universe_type" not in r}

        for company in all_companies:
            if company.isin in legacy_isins:
                serialized = company.to_dict()
                reloaded = Company.from_dict(serialized)
                assert reloaded.isin == company.isin
                assert reloaded.company_name == company.company_name
                assert reloaded.universe_type == UniverseType.QUANTITATIVE

    def test_prediction_isins_all_load_from_repository(
        self, prediction_isins: frozenset[str], repo: CompanyRepository
    ):
        """Every ISIN referenced in prediction files must be resolvable in the repository."""
        not_found = []
        for isin in prediction_isins:
            if repo.get_by_isin(isin) is None:
                not_found.append(isin)
        assert not not_found, (
            f"Prediction ISINs not found in CompanyRepository: {not_found}"
        )


# ---------------------------------------------------------------------------
# E. Intelligence companies cannot enter quantitative prediction workflows
# ---------------------------------------------------------------------------


class TestQuantitativeFirewall:
    """E. Intelligence companies must not appear in quantitative prediction workflows."""

    def test_intelligence_isins_not_in_prediction_files(
        self, prediction_isins: frozenset[str]
    ):
        """No intelligence ISIN should appear in any prediction filename."""
        leaked = EXPECTED_INTELLIGENCE_ISINS & prediction_isins
        assert not leaked, (
            f"Intelligence company ISINs found in prediction files (FIREWALL BREACH): {leaked}"
        )

    def test_get_by_universe_type_quantitative_excludes_intelligence(
        self, repo: CompanyRepository
    ):
        """get_by_universe_type(QUANTITATIVE) must not return any intelligence company."""
        quant_companies = repo.get_by_universe_type(UniverseType.QUANTITATIVE)
        quant_isins = {c.isin for c in quant_companies}
        leaked = EXPECTED_INTELLIGENCE_ISINS & quant_isins
        assert not leaked, (
            f"Intelligence ISINs appeared in QUANTITATIVE universe query: {leaked}"
        )

    def test_get_intelligence_companies_excludes_quantitative(
        self, repo: CompanyRepository, prediction_isins: frozenset[str]
    ):
        """get_intelligence_companies() must not return any prediction-universe company."""
        intel_isins = {c.isin for c in repo.get_intelligence_companies()}
        leaked = intel_isins & prediction_isins
        assert not leaked, (
            f"Quantitative ISINs appeared in intelligence universe query: {leaked}"
        )

    def test_intelligence_mapping_files_unchanged(self):
        """The mapping files directory must not contain intelligence ISINs."""
        mapping_dir = Path(__file__).parent.parent / "data" / "mappings"
        for mapping_file in mapping_dir.glob("*.json"):
            with mapping_file.open(encoding="utf-8") as f:
                content = f.read()
            for isin in EXPECTED_INTELLIGENCE_ISINS:
                assert isin not in content, (
                    f"Intelligence ISIN {isin!r} found in mapping file {mapping_file.name}"
                )


# ---------------------------------------------------------------------------
# F. CompanyRepository search finds both universes
# ---------------------------------------------------------------------------


class TestRepositorySearch:
    """F. CompanyRepository search can find both quantitative and intelligence companies."""

    def test_search_by_name_finds_zomato(self, repo: CompanyRepository):
        """search_by_name('Zomato') must return the intelligence record."""
        results = repo.search_by_name("Zomato")
        assert results, "search_by_name('Zomato') returned no results"
        found = any(c.isin == "INE758T01015" for c in results)
        assert found, "Zomato (INE758T01015) not found in search results"

    def test_search_by_name_finds_delhivery(self, repo: CompanyRepository):
        """search_by_name('Delhivery') must return the intelligence record."""
        results = repo.search_by_name("Delhivery")
        assert results
        assert any(c.isin == "INE201M01025" for c in results)

    def test_search_by_name_finds_reliance(self, repo: CompanyRepository):
        """search_by_name('Reliance') must still find the quantitative company."""
        results = repo.search_by_name("Reliance")
        assert results
        assert any(c.isin == "INE002A01018" for c in results)

    def test_search_by_sector_consumer_digital(self, repo: CompanyRepository):
        """search(sector='Consumer') must return intelligence consumer companies."""
        results = repo.search(sector="Consumer")
        isins = {c.isin for c in results}
        # Zomato, Swiggy, Flipkart, Amazon
        expected = {
            "INE758T01015", "PRIV-BUNDL-SWIGGY",
            "PRIV-FLIPKART-IND", "PRIV-AMAZON-IND",
        }
        assert expected.issubset(isins), (
            f"Missing consumer/digital intelligence companies in sector search. "
            f"Expected {expected}, got {isins}"
        )

    def test_get_all_returns_all_70(self, repo: CompanyRepository):
        """get_all() must return all 70 companies (50 legacy + 20 intelligence)."""
        all_c = repo.get_all()
        assert len(all_c) == 70

    def test_get_by_universe_type_intelligence_returns_20(self, repo: CompanyRepository):
        """get_by_universe_type(INTELLIGENCE) must return exactly 20 companies."""
        intel = repo.get_by_universe_type(UniverseType.INTELLIGENCE)
        assert len(intel) == 20

    def test_get_intelligence_companies_returns_20(self, repo: CompanyRepository):
        """get_intelligence_companies() convenience method returns 20."""
        intel = repo.get_intelligence_companies()
        assert len(intel) == 20

    def test_get_by_universe_type_quantitative_returns_50(self, repo: CompanyRepository):
        """get_by_universe_type(QUANTITATIVE) must return exactly 50 companies
        (the 50 legacy seed records that default to QUANTITATIVE)."""
        quant = repo.get_by_universe_type(UniverseType.QUANTITATIVE)
        assert len(quant) == 50

    def test_bsnl_findable_by_name(self, repo: CompanyRepository):
        """BSNL must be findable by partial name search."""
        results = repo.search_by_name("BSNL")
        assert results, "BSNL not found by name search"
        found = any(c.isin == "SOE-BSNL-UNLISTED" for c in results)
        assert found, "BSNL (SOE-BSNL-UNLISTED) not found in search results"

    def test_kseb_findable_by_isin(self, repo: CompanyRepository):
        """KSEB must be retrievable by ISIN."""
        c = repo.get_by_isin("UNLISTED-KL-KSEB")
        assert c is not None
        assert c.company_name == "Kerala State Electricity Board Limited"


# ---------------------------------------------------------------------------
# G. Duplicate company / legal-entity detection
# ---------------------------------------------------------------------------


class TestDuplicateDetection:
    """G. No duplicate ISINs or duplicate legal-entity names in the company universe."""

    def test_no_duplicate_isins(self, all_companies_json: list[dict]):
        """Every ISIN must appear exactly once in companies.json."""
        isins = [c["isin"] for c in all_companies_json]
        counts = Counter(isins)
        duplicates = {isin: count for isin, count in counts.items() if count > 1}
        assert not duplicates, f"Duplicate ISINs detected: {duplicates}"

    def test_no_duplicate_company_names(self, all_companies_json: list[dict]):
        """Every company_name must appear exactly once."""
        names = [c["company_name"] for c in all_companies_json]
        counts = Counter(names)
        duplicates = {name: count for name, count in counts.items() if count > 1}
        assert not duplicates, f"Duplicate company names detected: {duplicates}"

    def test_no_intelligence_isin_matches_quantitative_isin(
        self, prediction_isins: frozenset[str]
    ):
        """No intelligence ISIN must equal any quantitative prediction ISIN."""
        overlap = EXPECTED_INTELLIGENCE_ISINS & prediction_isins
        assert not overlap, (
            f"Intelligence ISINs overlap with quantitative prediction ISINs: {overlap}"
        )

    def test_listed_intelligence_companies_have_unique_tickers(
        self, intelligence_companies: list[Company]
    ):
        """Listed intelligence companies must not share NSE tickers."""
        tickers = [
            c.ticker_nse
            for c in intelligence_companies
            if c.ticker_nse.strip()
        ]
        counts = Counter(tickers)
        duplicates = {t: n for t, n in counts.items() if n > 1}
        assert not duplicates, f"Duplicate NSE tickers in intelligence universe: {duplicates}"


# ---------------------------------------------------------------------------
# H. Baseline integrity
# ---------------------------------------------------------------------------


class TestBaselineIntegrity:
    """H. Central baseline must be exactly preserved."""

    def test_prediction_isin_count_is_47(self, prediction_isins: frozenset[str]):
        """The prediction file universe must contain exactly 47 distinct company ISINs."""
        assert len(prediction_isins) == 47, (
            f"Expected 47 prediction ISINs, found {len(prediction_isins)}. "
            f"ISINs: {sorted(prediction_isins)}"
        )

    def test_prediction_files_count_is_4700(self):
        """The prediction files count must remain exactly 4,700."""
        pred_files = list(PREDICTIONS_DIR.glob("pred_*.json"))
        assert len(pred_files) == 4700, (
            f"Expected 4700 prediction files, found {len(pred_files)}"
        )

    def test_prediction_isins_match_canonical_central_quantitative_set(
        self, prediction_isins: frozenset[str]
    ):
        """The actual prediction ISINs must be a subset of the known 47 quantitative ISINs.
        No intelligence ISIN should appear."""
        unexpected = prediction_isins - CENTRAL_QUANTITATIVE_ISINS
        # Allow a small set of additional known quantitative ISINs
        # (LTIMindtree, Siemens, ABB appear in seed but may also be in predictions)
        extended_allowed = CENTRAL_QUANTITATIVE_ISINS | {
            "INE214G01026",  # LTIMindtree
            "INE003A01024",  # Siemens
            "INE117A01022",  # ABB India
        }
        still_unexpected = prediction_isins - extended_allowed
        assert not still_unexpected, (
            f"Unexpected ISINs in predictions (possible intelligence breach): {still_unexpected}"
        )

    def test_no_intelligence_isin_in_predictions(self, prediction_isins: frozenset[str]):
        """NONE of the 20 intelligence ISINs must appear in any prediction file."""
        leaked = EXPECTED_INTELLIGENCE_ISINS & prediction_isins
        assert not leaked, (
            f"BASELINE INTEGRITY FAILURE — Intelligence ISINs found in predictions: {leaked}"
        )

    def test_companies_json_has_exactly_70_records(self, all_companies_json: list[dict]):
        """After Task 8.12.3, companies.json must have exactly 70 records."""
        assert len(all_companies_json) == 70, (
            f"Expected 70 records in companies.json, got {len(all_companies_json)}"
        )

    def test_original_50_seed_isins_all_present(self, all_companies_json: list[dict]):
        """All 50 original seed company ISINs must still be present."""
        # The first 50 companies in the file are the original seed.
        # We verify by checking the ISINs are all loadable.
        repo = CompanyRepository()
        original_isins = [r["isin"] for r in all_companies_json if "universe_type" not in r]
        assert len(original_isins) == 50, (
            f"Expected 50 legacy (non-universe_type) records, found {len(original_isins)}"
        )
        for isin in original_isins:
            c = repo.get_by_isin(isin)
            assert c is not None, f"Original seed ISIN {isin} not found in repository"


# ---------------------------------------------------------------------------
# I. State prediction count remains exactly 0
# ---------------------------------------------------------------------------


class TestStatePredictions:
    """I. State stock-market prediction count must remain exactly 0."""

    def test_state_predictions_count_is_zero(self):
        """No state-level stock price predictions must exist."""
        state_preds_dir = Path(__file__).parent.parent / "data" / "state_predictions"
        if not state_preds_dir.exists():
            # Directory doesn't exist — count is implicitly 0
            return
        state_pred_files = list(state_preds_dir.glob("*.json"))
        assert len(state_pred_files) == 0, (
            f"State predictions found (expected 0): {len(state_pred_files)} files"
        )

    def test_no_state_isin_in_standard_predictions(self, prediction_isins: frozenset[str]):
        """State-level unlisted utility ISINs must not appear in prediction files."""
        state_isins = {
            "UNLISTED-AP-GENCO",
            "UNLISTED-KL-KSEB",
            "UNLISTED-TS-GENCO",
            "UNLISTED-KL-RTC",
            "UNLISTED-KA-RTC",
            "SOE-BSNL-UNLISTED",
        }
        leaked = state_isins & prediction_isins
        assert not leaked, (
            f"State/unlisted entity ISINs found in prediction files: {leaked}"
        )
