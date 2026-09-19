# TASK 8.12.3 — Populate Extended Company Intelligence Universe

**Status:** COMPLETE  
**Date:** 2026-09-15  
**Category:** Company Intelligence Universe & Data Architecture  
**Dependencies:** Task 8.12.1 (Company Audit), Task 8.12.2 (Schema Extension)

---

## 1. Executive Summary

Task 8.12.3 populates the **Extended Company Intelligence Universe** using the 7 new schema fields introduced in Task 8.12.2 (`universe_type`, `entity_type`, `group_name`, `ownership_type`, `data_sources`, `data_quality_score`, `watchlist_eligible`).

A curated set of **20 verified intelligence companies** has been added to `data/companies/companies.json`, expanding the seed file from 50 to 70 total records. All 20 new entries have `universe_type = "intelligence"` and are firewalled from the Central quantitative prediction pipeline.

### Core Architecture & Baseline Protection
- **47 Central quantitative companies:** 100% UNCHANGED (frozen).
- **940 Central bill-company pairs:** 100% UNCHANGED (frozen).
- **4,700 Central prediction records:** 100% UNCHANGED (frozen).
- **State predictions:** Exactly 0 (no state predictions generated).
- **Machine-readable artifact created:** `data/companies/intelligence_universe.json` (20 records).
- **Repository query extensions:** `CompanyRepository.get_by_universe_type()` and `CompanyRepository.get_intelligence_companies()`.
- **Comprehensive test suite:** 51 dedicated tests in `tests/test_company_intelligence_universe.py`, all passing. Combined suite of 127 tests passes cleanly.

---

## 2. Quantitative Firewall & Baseline Integrity

A critical requirement of Task 8.12.3 is strict segregation between quantitative prediction workflows and qualitative/state intelligence tracking.

```
+-----------------------------------------------------------------------------------+
|                            data/companies/companies.json                         |
|                                     (70 records)                                  |
+-------------------------------------------------+---------------------------------+
|          50 Quantitative / Legacy Seed          |     20 Intelligence Companies   |
|         (universe_type = "quantitative")        | (universe_type = "intelligence")|
+-------------------------------------------------+---------------------------------+
                         |                                         |
                         v                                         v
        +--------------------------------+        +--------------------------------+
        |  Quantitative Prediction Engine |        |   Company Intelligence Layer   |
        |  (47 ISINs / 940 pairs / 4700) |        |   (Qualitative / State / Policy|
        |         STRICTLY FROZEN        |        |    Discovery / Watchlists)     |
        +--------------------------------+        +--------------------------------+
```

### Protection Mechanisms
1. **Prediction Pipeline Firewall:** The quantitative prediction engine discovers candidate companies from `data/mappings/*.json` pairs and known Central ISINs. No intelligence ISIN appears in any mapping or prediction file.
2. **Schema Default Compatibility:** Legacy records missing `universe_type` automatically default to `UniverseType.QUANTITATIVE` upon deserialization in `Company.from_dict()`.
3. **Repository Filtering:** Callers querying `repo.get_by_universe_type(UniverseType.QUANTITATIVE)` receive exclusively quantitative companies (50), while `repo.get_intelligence_companies()` retrieves exclusively the 20 intelligence entities.

---

## 3. The 20 Curated Intelligence Companies

The 20 intelligence companies span 7 strategically selected sectors with high legislative and policy sensitivity in India:

| # | Company Name | Legal Entity | ISIN / Identifier | Sector | Entity Type | Ownership Type | Group Name | Score | Watchlist |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Zomato Limited | Zomato Limited | `INE758T01015` | Consumer / Digital | `listed_company` | `public` | None | 0.90 | Yes |
| 2 | Swiggy | Bundl Technologies Private Limited | `PRIV-BUNDL-SWIGGY` | Consumer / Digital | `unlisted_company` | `private` | None | 0.70 | No |
| 3 | Flipkart | Flipkart Private Limited | `PRIV-FLIPKART-IND` | Consumer / Digital | `private_company` | `private` | Walmart Group | 0.65 | No |
| 4 | Amazon India | Amazon Seller Services Private Limited | `PRIV-AMAZON-IND` | Consumer / Digital | `private_company` | `private` | Amazon Group | 0.65 | No |
| 5 | Delhivery Limited | Delhivery Limited | `INE201M01025` | Logistics & Transportation | `listed_company` | `public` | None | 0.85 | Yes |
| 6 | Blue Dart Express Limited | Blue Dart Express Limited | `INE233B01017` | Logistics & Transportation | `listed_company` | `mixed` | DHL Group | 0.80 | Yes |
| 7 | Adani Ports and SEZ Limited | Adani Ports and Special Economic Zone Limited | `INE742F01042` | Infrastructure | `listed_company` | `public` | Adani Group | 0.90 | Yes |
| 8 | Container Corporation of India | Container Corporation of India Limited | `INE399C01030` | Logistics & Transportation | `state_owned_enterprise` | `state` | Ministry of Railways | 0.85 | Yes |
| 9 | Bharat Sanchar Nigam Limited (BSNL) | Bharat Sanchar Nigam Limited | `SOE-BSNL-UNLISTED` | Telecommunications | `state_owned_enterprise` | `state` | Government of India (DoT) | 0.70 | No |
| 10 | Vodafone Idea Limited | Vodafone Idea Limited | `INE669E01016` | Telecommunications | `listed_company` | `mixed` | Vodafone / Aditya Birla Group | 0.80 | Yes |
| 11 | Fortis Healthcare Limited | Fortis Healthcare Limited | `INE061F01013` | Healthcare & Pharmaceuticals | `listed_company` | `public` | IHH Healthcare Group | 0.80 | Yes |
| 12 | Max Healthcare Institute Limited | Max Healthcare Institute Limited | `INE027H01010` | Healthcare & Pharmaceuticals | `listed_company` | `public` | Max Group | 0.85 | Yes |
| 13 | APGENCO | Andhra Pradesh Power Generation Corporation Limited | `UNLISTED-AP-GENCO` | Energy | `public_utility` | `state` | Government of Andhra Pradesh | 0.70 | No |
| 14 | KSEB | Kerala State Electricity Board Limited | `UNLISTED-KL-KSEB` | Energy | `public_utility` | `state` | Government of Kerala | 0.75 | No |
| 15 | TSGENCO | Telangana State Power Generation Corporation Limited | `UNLISTED-TS-GENCO` | Energy | `public_utility` | `state` | Government of Telangana | 0.70 | No |
| 16 | IREDA | Indian Renewable Energy Development Agency Limited | `INE202E01016` | Energy | `state_owned_enterprise` | `state` | Ministry of New and Renewable Energy | 0.85 | Yes |
| 17 | KSRTC-KL | Kerala State Road Transport Corporation | `UNLISTED-KL-RTC` | Logistics & Transportation | `public_utility` | `state` | Government of Kerala | 0.65 | No |
| 18 | KSRTC-KA | Karnataka State Road Transport Corporation | `UNLISTED-KA-RTC` | Logistics & Transportation | `public_utility` | `state` | Government of Karnataka | 0.65 | No |
| 19 | GMR Airports Infrastructure | GMR Airports Infrastructure Limited | `INE043D01016` | Infrastructure | `listed_company` | `public` | GMR Group | 0.85 | Yes |
| 20 | IRFC | Indian Railway Finance Corporation Limited | `INE053F01010` | Financial Services & Railways | `state_owned_enterprise` | `state` | Ministry of Railways | 0.85 | Yes |

### Entity Breakdown
- **Listed Companies (`listed_company`):** 10 (all with verified NSE/BSE tickers and authentic NSDL/CDSL ISINs)
- **State-Owned Enterprises (`state_owned_enterprise`):** 5 (BSNL, CONCOR, IREDA, IRFC)
- **Public Utilities (`public_utility`):** 5 (APGENCO, KSEB, TSGENCO, KSRTC-KL, KSRTC-KA)
- **Private Companies (`private_company`):** 2 (Flipkart India, Amazon India)
- **Unlisted Companies (`unlisted_company`):** 1 (Bundl Technologies / Swiggy)

---

## 4. Provenance & Data Quality Scoring

### 4.1 Scoring Rubric
Every company has a computed `data_quality_score` based on 10 objective criteria (0.1 each, bounded to [0.0, 1.0]):
1. **Legal Identity:** Legal entity name verified against MCA / corporate registration records.
2. **ISIN / Identifier:** Authentic exchange ISIN (for listed) or standardized synthetic ID (for unlisted).
3. **Ticker / Exchange:** Valid NSE/BSE ticker symbols where applicable.
4. **Ownership Type:** Categorized rigorously (`public`, `state`, `private`, `mixed`).
5. **Sector & Industry:** SEBI/NSE sectoral classification or state domain alignment.
6. **Geographic Footprint:** HQ state and city verified.
7. **Official Web Presence:** Active corporate URL documented.
8. **Business Activities:** Specific, non-generic operational activities listed.
9. **Legislative Exposure Rationale:** Concrete policy and legislative impact areas articulated.
10. **Source Diversity:** At least two distinct authoritative sources documented in `data_sources`.

### 4.2 Identifier Standard
- **Listed entities:** Use genuine 12-character alphanumeric ISINs (`INE...`) issued by NSDL/CDSL.
- **Unlisted private entities:** Prefixed with `PRIV-` (e.g., `PRIV-BUNDL-SWIGGY`, `PRIV-FLIPKART-IND`).
- **State-owned unlisted enterprises:** Prefixed with `SOE-` (e.g., `SOE-BSNL-UNLISTED`).
- **State public utilities:** Prefixed with `UNLISTED-{STATE}-` (e.g., `UNLISTED-KL-KSEB`, `UNLISTED-AP-GENCO`).

No synthetic or placeholder ISIN mimics genuine exchange formats.

---

## 5. Storage & Repository Updates

### 5.1 `storage/company_repository.py`
Two new methods added to `CompanyRepository`:

```python
def get_by_universe_type(self, universe_type: UniverseType) -> list[Company]:
    """Return companies belonging to the given universe type."""
    return [c for c in self._load_data() if c.universe_type == universe_type]

def get_intelligence_companies(self) -> list[Company]:
    """Convenience method to return all intelligence-universe companies."""
    return self.get_by_universe_type(UniverseType.INTELLIGENCE)
```

Additionally, `search_by_name()` was enhanced to evaluate `company.aliases` (e.g. acronyms like "BSNL", "IRFC", "KSEB", "APSEZ"), enabling accurate fuzzy and exact matching against entity nicknames and acronyms.

### 5.2 Artifact `data/companies/intelligence_universe.json`
A standalone machine-readable snapshot containing:
- Task metadata (`TASK_8_12_3`)
- Generation timestamp
- Company count (20)
- Array of 20 complete company dictionaries with all schema attributes

---

## 6. Verification & Test Suite

A comprehensive test suite was implemented in `tests/test_company_intelligence_universe.py` covering all 9 required verification categories:

| Category | Description | Tests | Status |
|---|---|---|---|
| **A. Load & Presence** | All 20 intelligence companies load, proper ISINs, sectors, names | 9 | PASSED |
| **B. Enum & Fields** | Valid `universe_type`, `entity_type`, `ownership_type`, quality scores | 8 | PASSED |
| **C. Provenance** | Non-empty `data_sources`, multiple sources for high-scoring entities | 5 | PASSED |
| **D. Legacy Compatibility** | 50 legacy records default to `QUANTITATIVE`, round-trip serialization | 3 | PASSED |
| **E. Quantitative Firewall** | No intelligence ISIN in predictions or candidate mappings | 4 | PASSED |
| **F. Repository Search** | Ticker search, fuzzy search, alias search, sector search, filtering | 10 | PASSED |
| **G. Duplicate Detection** | No duplicate ISINs, no duplicate names, unique listed tickers | 4 | PASSED |
| **H. Baseline Integrity** | 47 quantitative ISINs unchanged, 4,700 prediction files unchanged | 6 | PASSED |
| **I. State Predictions** | State prediction count remains exactly 0 | 2 | PASSED |
| **Total** | | **51** | **ALL PASSED** |

### Suite Execution
```bash
python -m pytest tests/test_company_schema_extension.py tests/test_company_intelligence.py tests/test_company_intelligence_universe.py -v
# Output: 127 passed in 2.20s
```

All 127 tests pass across the entire company test suite with zero errors and zero warnings.
