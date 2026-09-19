# TASK 8.12.4 — EVIDENCE-BASED COMPANY EXPOSURE INTELLIGENCE EXPANSION

**Status:** COMPLETE  
**Date:** 2026-09-16  
**Category:** Company Exposure Intelligence & Cross-Jurisdiction Modeling  
**Dependencies:** Task 8.12.1 (Company Intelligence Audit), Task 8.12.2 (Schema Extension), Task 8.12.3 (Intelligence Universe Expansion)

---

## 1. Objective

Task 8.12.4 extends company exposure intelligence across the India Legislative Intelligence & Market Impact Prediction Platform. It connects newly curated intelligence-universe companies (20 entities across 7 sensitive sectors) to relevant Central Government and Indian State legislation through a transparent, evidence-grounded exposure chain.

> [!IMPORTANT]
> **Strict Intelligence Boundary:**
> This task is exclusively an **INTELLIGENCE & EXPOSURE** expansion. It is strictly **NON-PREDICTIVE**.
> - Market relevance is qualitative (`HIGH`, `MEDIUM`, `LOW`, `NONE`, `UNKNOWN`), NOT a stock prediction.
> - Zero expected returns, abnormal returns, CAR, price targets, or trading signals are generated for intelligence entities.
> - The frozen Central quantitative baseline (47 companies, 940 pairs, 4,700 predictions) and State prediction zero-invariant (`STATE_PREDICTIONS = 0`) are 100% preserved.

---

## 2. Existing Exposure Architecture

Before implementing expansion, the system's corporate exposure architecture was inspected:

```
+----------------------------------------------------------------------------------------------------+
|                                    PLATFORM EXPOSURE ARCHITECTURE                                  |
+---------------------------------------------------+------------------------------------------------+
|                   CENTRAL GOVERNMENT              |                  STATE GOVERNMENTS             |
+---------------------------------------------------+------------------------------------------------+
| - 20 Production Bills (+2 non-modeled)            | - 44 State Bills (AP, KA, KL, TS)              |
| - 47 Central Quantitative Companies (Frozen)      | - 51 State Universe Companies                  |
| - 940 Central Bill-Company Pairs (data/mappings/) | - 86 Validated Corporate Exposures (Task 8.7)   |
| - 4,700 Predictions (data/predictions/)           | - StateCorporateExposureEngine                 |
| - Strictly Quantitative Baseline                  | - State predictions: EXACTLY 0                 |
+---------------------------------------------------+------------------------------------------------+
                                                    |
                                                    v
+----------------------------------------------------------------------------------------------------+
|                             TASK 8.12.4 EXPANDED EXPOSURE LAYER                                    |
|   - schemas/company_exposure.py (CompanyExposureRecord = StateCorporateExposure)                   |
|   - knowledge/state_corporate_exposure_engine.py (Central & State exposure evaluation)             |
|   - storage/company_exposure_repository.py (Multi-jurisdictional queries A through H)              |
|   - data/central_bills/corporate_exposure/ (18 evidence-grounded Central exposures)                |
|   - data/state_bills/corporate_exposure/ (86 validated State exposures 100% preserved)             |
+----------------------------------------------------------------------------------------------------+
```

### Key Reused Components
1. **`schemas/state_corporate_exposure.py` & `schemas/company_exposure.py`**:
   Extended `StateCorporateExposure` with backward-compatible defaults: `jurisdiction: str = "state"` and `market_relevance: str = "UNKNOWN"`. Exported alias `CompanyExposureRecord = StateCorporateExposure`.
2. **`knowledge/state_corporate_exposure_engine.py`**:
   Enhanced with `analyze_central_bill_exposure()`, `_evaluate_central_company_exposure()`, and `explain_exposure()`, preventing architectural fragmentation.
3. **`storage/company_exposure_repository.py`**:
   Unified repository wrapping Central exposure files (`data/central_bills/corporate_exposure/`) and State exposure files (`data/state_bills/corporate_exposure/`), with full alias matching.

---

## 3. Companies Assessed

All 70 companies in the platform repository were evaluated, with primary focus on the **20 newly curated intelligence universe entities**:

| # | Company Name | Legal Entity | Identifier | Sector | Primary Central Exposure | Primary State Exposure |
|---|---|---|---|---|---|---|
| 1 | Zomato Limited | Zomato Limited | `INE758T01015` | Consumer / Digital | NONE | Telangana Gig Worker Bill (DIRECT, HIGH) |
| 2 | Swiggy / Bundl | Bundl Technologies Pvt Ltd | `PRIV-BUNDL-SWIGGY` | Consumer / Digital | NONE | Telangana Gig Worker Bill (DIRECT, HIGH) |
| 3 | Flipkart | Flipkart Private Limited | `PRIV-FLIPKART-IND` | Consumer / Digital | NONE | NONE (No matching state/central bill in corpus) |
| 4 | Amazon India | Amazon Seller Services Pvt Ltd | `PRIV-AMAZON-IND` | Consumer / Digital | NONE | NONE (No matching state/central bill in corpus) |
| 5 | Delhivery Limited | Delhivery Limited | `INE201M01025` | Logistics & Transport | Bills of Lading Bill (INDIRECT, MED) | NONE |
| 6 | Blue Dart Express | Blue Dart Express Limited | `INE233B01017` | Logistics & Transport | Bharatiya Vayuyan Vidheyak (DIRECT, HIGH) | Telangana Motor Vehicles Tax (INDIRECT, LOW) |
| 7 | Adani Ports & SEZ | Adani Ports and SEZ Limited | `INE742F01042` | Infrastructure | Shipping & Maritime Bills (4 Bills, DIRECT, HIGH) | NONE (No AP/KL port regulatory bills in corpus) |
| 8 | CONCOR | Container Corp of India Ltd | `INE399C01030` | Logistics & Transport | Maritime & Railways (4 Bills, DIRECT, HIGH/MED) | NONE |
| 9 | BSNL | Bharat Sanchar Nigam Limited | `SOE-BSNL-UNLISTED` | Telecommunications | Telecom Policy Framework (DIRECT, HIGH) | NONE |
| 10 | Vodafone Idea | Vodafone Idea Limited | `INE669E01016` | Telecommunications | Telecom Policy Framework (DIRECT, HIGH) | NONE |
| 11 | Fortis Healthcare | Fortis Healthcare Limited | `INE061F01013` | Healthcare | Water Pollution Consent (DIRECT, LOW) | Karnataka Medical Registration (DIRECT, HIGH) |
| 12 | Max Healthcare | Max Healthcare Institute Ltd | `INE027H01010` | Healthcare | Water Pollution Consent (DIRECT, LOW) | NONE (No hospital presence in 4 focus states) |
| 13 | APGENCO | AP Power Generation Corp Ltd | `UNLISTED-AP-GENCO` | Energy | Boilers Bill (DIRECT, MED) | AP Electricity Duty & Factories (3 Bills, DIRECT) |
| 14 | KSEB | Kerala State Electricity Board | `UNLISTED-KL-KSEB` | Energy | NONE | NONE (No matching KL electricity duty bill in corpus) |
| 15 | TSGENCO | Telangana State Power Gen Corp | `UNLISTED-TS-GENCO` | Energy | Boilers Bill (DIRECT, MED) | Telangana Electricity Duty Bill (DIRECT, HIGH) |
| 16 | IREDA | Indian Renewable Energy Dev | `INE202E01016` | Energy Finance | NONE | NONE (No dedicated RE finance bill in corpus) |
| 17 | KSRTC-KL | Kerala State Road Transport | `UNLISTED-KL-RTC` | Public Transport | NONE | NONE (No KL transit tax bill in corpus) |
| 18 | KSRTC-KA | Karnataka State Road Transport| `UNLISTED-KA-RTC` | Public Transport | NONE | NONE (No KA transit tax bill in corpus) |
| 19 | GMR Airports | GMR Airports Infra Limited | `INE043D01016` | Infrastructure | Bharatiya Vayuyan Vidheyak (DIRECT, HIGH) | NONE |
| 20 | IRFC | Indian Railway Finance Corp | `INE053F01010` | Railway Finance | Railways Amendment Bill (DIRECT, HIGH) | NONE |

---

## 4. Exposure Methodology & Conceptual Chain

Every company exposure record strictly follows the required 10-step conceptual chain:

```
    1. LEGISLATIVE BILL
           ↓
    2. LEGISLATIVE DOMAIN / SECTOR
           ↓
    3. BUSINESS ACTIVITY
           ↓
    4. GEOGRAPHIC / STATE PRESENCE
           ↓
    5. CORPORATE ENTITY
           ↓
    6. DUAL-GROUNDED EVIDENCE (Statutory Text + Authoritative Company Source)
           ↓
    7. EXPOSURE TYPE (DIRECT / INDIRECT / NONE / UNKNOWN)
           ↓
    8. EXPOSURE STRENGTH (HIGH / MEDIUM / LOW / UNKNOWN)
           ↓
    9. ECONOMIC MECHANISM (Statutory Channel)
           ↓
   10. MARKET RELEVANCE (HIGH / MEDIUM / LOW / NONE / UNKNOWN — Non-Predictive)
```

No exposure is generated based on mere sector membership, brand popularity, or general market cap. A positive link requires:
1. Grounding in specific statutory clauses of the bill.
2. Verified company business operations directly or indirectly governed by those provisions.
3. For State legislation: verified physical or operational presence within the enacting State's territory.

---

## 5. Evidence Requirements & Provenance Standards

Every positive exposure retains a dual-grounded `evidence` array containing at least two distinct authoritative sources:
1. **Legislative Evidence (`source_type="bill_text"`):** Direct reference to clauses, sections, or official Statement of Objects and Reasons.
2. **Company / Public Enterprise Evidence:**
   - Listed entities: Annual Report disclosures, SEBI DRHP disclosures, or NSE/BSE regulatory filings.
   - Public sector undertakings / utilities: Official government administrative accounts, regulatory tariff filings, or audited financial disclosures.

Unsubstantiated search snippets, speculative news articles, and ungrounded blog posts are rejected.

---

## 6. Central Exposure Results

The Central bill analysis connected candidate intelligence companies to 9 Central bills, producing **18 verified corporate exposures**:

1. **The Bharatiya Vayuyan Vidheyak, 2024 (Civil Aviation):**
   - `GMR Airports Infrastructure Limited` (`INE043D01016`): DIRECT | HIGH | Mechanism: `regulation` | Market Relevance: `HIGH`
   - `Blue Dart Express Limited` (`INE233B01017`): DIRECT | HIGH | Mechanism: `compliance_cost` | Market Relevance: `MEDIUM`
2. **The Bills of Lading Bill, 2024 (Ports & Shipping):**
   - `Adani Ports and SEZ Limited` (`INE742F01042`): DIRECT | HIGH | Mechanism: `regulation` | Market Relevance: `HIGH`
   - `Container Corporation of India Limited` (`INE399C01030`): DIRECT | HIGH | Mechanism: `regulation` | Market Relevance: `HIGH`
   - `Delhivery Limited` (`INE201M01025`): INDIRECT | MEDIUM | Mechanism: `supply_chain` | Market Relevance: `LOW`
3. **The Carriage of Goods by Sea Bill, 2024 (Ports & Shipping):**
   - `Adani Ports and SEZ Limited` (`INE742F01042`): DIRECT | HIGH | Mechanism: `regulation` | Market Relevance: `HIGH`
   - `Container Corporation of India Limited` (`INE399C01030`): DIRECT | MEDIUM | Mechanism: `supply_chain` | Market Relevance: `MEDIUM`
4. **The Coastal Shipping Bill, 2024 (Ports & Shipping):**
   - `Adani Ports and SEZ Limited` (`INE742F01042`): DIRECT | HIGH | Mechanism: `market_access` | Market Relevance: `HIGH`
   - `Container Corporation of India Limited` (`INE399C01030`): DIRECT | MEDIUM | Mechanism: `supply_chain` | Market Relevance: `MEDIUM`
5. **The Merchant Shipping Bill, 2024 (Ports & Marine Services):**
   - `Adani Ports and SEZ Limited` (`INE742F01042`): DIRECT | HIGH | Mechanism: `compliance_cost` | Market Relevance: `HIGH`
6. **The Railways (Amendment) Bill, 2024 (Railways):**
   - `Indian Railway Finance Corporation Limited` (`INE053F01010`): DIRECT | HIGH | Mechanism: `financing` | Market Relevance: `HIGH`
   - `Container Corporation of India Limited` (`INE399C01030`): DIRECT | HIGH | Mechanism: `infrastructure_access` | Market Relevance: `HIGH`
7. **The Boilers Bill, 2024 (Thermal Power / Manufacturing):**
   - `APGENCO` (`UNLISTED-AP-GENCO`): DIRECT | MEDIUM | Mechanism: `compliance_cost` | Market Relevance: `LOW`
   - `TSGENCO` (`UNLISTED-TS-GENCO`): DIRECT | MEDIUM | Mechanism: `compliance_cost` | Market Relevance: `LOW`
8. **The Water (Prevention and Control of Pollution) Amendment Bill, 2024 (Healthcare Services):**
   - `Fortis Healthcare Limited` (`INE061F01013`): DIRECT | LOW | Mechanism: `compliance_cost` | Market Relevance: `LOW`
   - `Max Healthcare Institute Limited` (`INE027H01010`): DIRECT | LOW | Mechanism: `compliance_cost` | Market Relevance: `LOW`
9. **Key Issues and Analysis (Telecommunications Policy):**
   - `Vodafone Idea Limited` (`INE669E01016`): DIRECT | HIGH | Mechanism: `licensing` | Market Relevance: `HIGH`
   - `Bharat Sanchar Nigam Limited` (`SOE-BSNL-UNLISTED`): DIRECT | HIGH | Mechanism: `procurement` | Market Relevance: `MEDIUM`

---

## 7. State Exposure Results

The existing State corporate exposure baseline was completely preserved:
- **Total State corporate exposure records:** Exactly 86
- **Andhra Pradesh:** 47 exposures across 7 bills
- **Karnataka:** 16 exposures across 5 bills
- **Kerala:** 3 exposures across 2 bills
- **Telangana:** 20 exposures across 7 bills
- **Bills with exposure:** 21 bills
- **Bills without exposure:** 23 bills

---

## 8. Direct vs Indirect Methodology

The classification adheres to strict definitions:
- **`DIRECT` (99 exposures across platform):**
  Legislation directly regulates, licenses, taxes, governs, or alters operational mandates for activities conducted by the company.
  *Examples:* Adani Ports under coastal shipping cabotage reform; IRFC under railway financing; Swiggy under gig-worker welfare levy.
- **`INDIRECT` (5 exposures across platform):**
  Legislation affects an important supplier, customer, downstream freight demand, or operating cost structure without regulating the company directly.
  *Examples:* Delhivery under bills of lading title reform (freight forwarding downstream impact); Tata Motors under motor vehicles registration tax (vehicle buyer demand).
- **`NONE`:**
  No evidence establishes an operational or statutory connection between the company and the bill.
- **`UNKNOWN`:**
  Insufficient data to confirm exposure.

---

## 9. Economic Mechanisms

All positive exposures map to the established project taxonomy:
- `regulation`: Statutory operational standards and mandates (Adani Ports, CONCOR, GMR)
- `licensing`: Spectrum and operational concession licenses (Vodafone Idea, GMR)
- `compliance_cost`: Overhaul standards, safety audits, SPCB permits (Boilers, Water Act, Blue Dart)
- `market_access`: Cabotage relaxations and intermodal access (Coastal Shipping)
- `supply_chain`: Intermodal freight documentation transfer (CONCOR, Delhivery)
- `infrastructure_access`: Track access and railway land licenses (CONCOR)
- `financing`: Sovereign borrowing and rolling stock leasing (IRFC)
- `procurement`: Public sector connectivity projects and BharatNet (BSNL)
- `labour_requirement`: Statutory platform worker registration and welfare cess (Swiggy, Zomato)
- `taxation`: State electricity duty and motor vehicle quarterly tax schedules

---

## 10. Market Relevance Boundary vs Market Prediction

The platform enforces a strict epistemic boundary:

$$\text{MARKET\_RELEVANCE} \neq \text{MARKET\_PREDICTION}$$

- **Market Relevance** indicates whether the legislative event is substantively relevant to financial market participants assessing corporate operating risk. Labels are qualitative: `HIGH`, `MEDIUM`, `LOW`, `NONE`, `UNKNOWN`.
- **Market Prediction** (price targets, return percentages, alpha forecasts, CAR, buy/sell ratings) is strictly forbidden for intelligence companies and State legislation.
- Guardrail: All records pass `__post_init__` regex filtering against `_FORBIDDEN_PREDICTIVE_TERMS`.

---

## 11. Central Quantitative Firewall

The quantitative firewall guarantees complete isolation of quantitative prediction models:
1. **ISIN Segregation:** Zero intelligence ISINs appear in `data/predictions/` or `data/mappings/*.json`.
2. **Repository Separation:** `CompanyRepository.get_by_universe_type(UniverseType.QUANTITATIVE)` retrieves only the 50 quantitative records, excluding all 20 intelligence companies.
3. **Zero State Predictions:** `data/state_predictions/` contains exactly 0 files.
4. **Baseline Invariants:**
   - Central Quantitative Companies: 47
   - Central Bill-Company Pairs: 940
   - Central Predictions: 4,700
   - Central Baseline Changed: `False`

---

## 12. Quality Metrics Audit

Machine-readable report stored at `data/company_exposures/exposure_expansion_quality_report.json`:

```json
{
  "companies_assessed": {
    "total_companies_assessed": 70,
    "new_intelligence_companies_assessed": 20,
    "quantitative_companies": 50
  },
  "exposure_counts": {
    "central_exposures": 18,
    "state_exposures": 86,
    "total_exposures": 104,
    "direct_exposures": 99,
    "indirect_exposures": 5,
    "unknown_directness": 0
  },
  "exposure_strength": {
    "high_strength": 56,
    "medium_strength": 42,
    "low_strength": 6,
    "unknown_strength": 0,
    "none_strength": 0
  },
  "evidence_audit": {
    "exposures_with_company_evidence": 104,
    "exposures_with_legislative_evidence": 104,
    "exposures_with_both": 104,
    "exposures_missing_evidence": 0,
    "unsupported_mappings": 0
  },
  "company_coverage": {
    "intelligence_companies_with_exposure_count": 14,
    "intelligence_companies_without_exposure_count": 6
  },
  "integrity_audit": {
    "duplicates_found": 0,
    "duplicate_details": []
  },
  "quantitative_firewall_and_baseline": {
    "central_quantitative_companies": 47,
    "central_bill_company_pairs": 940,
    "central_predictions": 4700,
    "state_predictions": 0,
    "central_baseline_changed": false
  }
}
```

---

## 13. Test Results

Comprehensive testing was executed covering all 15 required scenarios:

```
python -m pytest tests/test_state_corporate_exposure.py tests/test_company_intelligence_universe.py tests/test_company_schema_extension.py tests/test_company_intelligence.py tests/test_company_exposure_expansion.py -v
```

### Results Summary
- `tests/test_company_exposure_expansion.py`: 38 passed
- `tests/test_state_corporate_exposure.py`: 30 passed
- `tests/test_company_intelligence_universe.py`: 51 passed
- `tests/test_company_schema_extension.py`: 43 passed
- `tests/test_company_intelligence.py`: 33 passed
- **Total Passed:** **195 passed in 5.45s (100% clean, 0 failures, 0 warnings)**

---

## 14. Known Limitations

1. **Corpus Scope:** The Central bill corpus contains 20 parliamentary bills introduced in the 2024 session. As a result, e-commerce/retail platforms (Flipkart, Amazon) and dedicated RE financing entities (IREDA) receive `NONE` exposure for Central legislation because no relevant central bill exists in the active corpus.
2. **Unlisted Corporate Disclosures:** State public undertakings (APGENCO, TSGENCO, KSEB, KSRTC) do not file annual reports with stock exchanges; their evidence relies on official state gazettes and regulatory commission tariff filings.
3. **State Geofence:** State bills strictly require physical/operational presence in that state. Companies without facilities in a state (e.g. Max Healthcare in Kerala) are strictly unexposed.

---

## 15. Examples of Evidence-Backed Exposure Chains

### Example 1: Central Maritime Legislation -> Port Terminal Operator
```
Bill: The Coastal Shipping Bill, 2024 (the-coastal-shipping-bill-2024)
 ↓
Legislative Domain: Shipping & Ports / Infrastructure Development
 ↓
Business Activity: Coastal container terminal operations & transhipment handling
 ↓
Geographic Scope: National coastal seaboard
 ↓
Company: Adani Ports and Special Economic Zone Limited (INE742F01042)
 ↓
Evidence:
  1. [bill_text] Clauses 3-12: Relaxes cabotage licensing for coastal trade and mandates port berthing priority for coastal cargo.
  2. [company_filing] APSEZ Annual Report 2023-24: Operates commercial ports across Indian coastline (Mundra, Krishnapatnam, Gangavaram, Vizhinjam).
 ↓
Exposure Type: DIRECT
 ↓
Exposure Strength: HIGH
 ↓
Economic Mechanism: market_access
 ↓
Market Relevance: HIGH (Non-predictive qualitative indicator)
```

### Example 2: State Platform Worker Legislation -> Gig Economy Operator
```
Bill: The Telangana Gig and Platform Workers (Registration and Welfare) Bill, 2024 (telangana-vs-bill-11-2024)
 ↓
Legislative Domain: Labour & Employment
 ↓
Business Activity: App-based platform delivery & aggregator operations
 ↓
Geographic Presence: Telangana (Hyderabad, Secunderabad, Warangal)
 ↓
Company: Bundl Technologies Private Limited / Swiggy (PRIV-BUNDL-SWIGGY)
 ↓
Evidence:
  1. [bill_text] Section 3 / Statement of Objects and Reasons: Mandates aggregator registration and 1-2% welfare fee on app transactions.
  2. [company_filing] Swiggy DRHP 2024: Operates extensive gig delivery partner fleet across Telangana urban centres.
 ↓
Exposure Type: DIRECT
 ↓
Exposure Strength: HIGH
 ↓
Economic Mechanism: labour_requirement
 ↓
Market Relevance: HIGH (Non-predictive qualitative indicator)
```

---

## 16. Recommended Next Task

**TASK 8.12.5 — CORPORATE EXPOSURE DISCOVERY UI INTEGRATION**
- Integrate `CompanyExposureRepository` and query methods (A through H) into the Unified Legislative Discovery Explorer and SaaS company intelligence dashboard pages.
- Provide interactive company exposure graph views linking bills, sectors, activities, mechanisms, and evidence chains.
