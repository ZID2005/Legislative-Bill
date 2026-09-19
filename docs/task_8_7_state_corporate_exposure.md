# Task 8.7: State Corporate Exposure Intelligence Layer

> **Critical Notice**: This task establishes corporate exposure intelligence and does **not** predict stock-market impact. State market predictions remain strictly **0**.

---

## Executive Summary

Task 8.7 introduces an additive, structured, and factual corporate exposure intelligence layer for Indian State legislative bills within the **India Legislative Intelligence & Market Impact Prediction Platform**.

Operating across all 44 analyzed State bills spanning 4 pilot States (**Andhra Pradesh**, **Karnataka**, **Kerala**, and **Telangana**), this layer provides rigorous, inspectable answers to 10 core corporate exposure questions:
1. **Which companies may have exposure to a State bill?**
2. **Why are they exposed?**
3. **Is the exposure direct or indirect?**
4. **What business activity creates the exposure?**
5. **What State does the exposure relate to?**
6. **What sector/sub-sector is involved?**
7. **Is the company listed or unlisted?**
8. **How strong is the evidence?**
9. **What is the geographic scope?**
10. **What information is missing before market-impact modeling?**

---

## Strict Architectural Isolation & Epistemic Boundaries

```
+----------------------------------------------------------------------------------------------------+
|                                    CENTRAL GOVERNMENT (FROZEN)                                     |
|  22 Metadata Bills | 20 Modelled Bills | 47 Production Companies | 4,700 Predictions               |
|  4,700 Decision Records | 940 Anticipation Records | 14,100 Stakeholder Reports                    |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  | STRICT ISOLATION (ZERO LEAKAGE)
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                STATE LEGISLATIVE INTELLIGENCE                                      |
|  44 Bills (AP: 12, KA: 11, KL: 11, TS: 10) | State Predictions: EXACTLY ZERO                       |
|                                                                                                    |
|  Task 8.4: Knowledge Layer  -->  Task 8.6: Sector & Stakeholder Intelligence Layer                 |
|                                         |                                                          |
|                                         v                                                          |
|  Task 8.7: Corporate Exposure Intelligence Layer                                                   |
|    - StateCorporateExposure Schema                                                                 |
|    - Controlled State Company Universe (51 Companies: 46 Listed, 5 Unlisted)                       |
|    - 6-Stage Exposure Chain: Bill -> Sector -> Activity -> Presence -> Company -> Exposure         |
|    - StateCorporateExposureRepository (CRUD, State/Company/Sector/Strength Search)                 |
+----------------------------------------------------------------------------------------------------+
```

### Tripartite Epistemic Boundary
1. **FACT**:
   - Company operational presence in a State documented in official annual reports, SEBI filings, or government filings.
   - Statutory provisions and regulatory clauses extracted from official State gazette bill texts.
2. **BOUNDED INFERENCE**:
   - Classification of exposure as `DIRECT` vs `INDIRECT`.
   - Classification of exposure strength as `HIGH`, `MEDIUM`, `LOW`, or `UNKNOWN`.
   - Qualitative direction of business exposure (e.g. additional compliance requirements vs operational flexibility).
3. **PREDICTION (STRICTLY PROHIBITED)**:
   - Absolutely no stock price projections, price targets, buy/sell ratings, abnormal returns (CAR/AAR), or equity alpha.
   - State market predictions remain strictly **0**.

---

## Critical Principle: The Headquarters Fallacy

A frequent flaw in naive corporate mapping is equating:
$$\text{Company Headquarters in State} \iff \text{Company Exposed to State Bill}$$

In practice:
- A company headquartered in Maharashtra (e.g. UltraTech Cement, Reliance, Tata Power) operates major factories, power plants, and distribution networks in Andhra Pradesh, Telangana, and Karnataka.
- A company headquartered in Karnataka (e.g. Infosys) is not exposed to a Karnataka Bovine Breeding bill.

Therefore, corporate exposure in Task 8.7 is determined strictly by:
$$\text{Corporate Exposure} = \text{Business Activity} + \text{State Presence} + \text{Bill Provision Grounding}$$

---

## 1. Corporate Exposure Data Model

The `StateCorporateExposure` schema is defined in `schemas/state_corporate_exposure.py`:

| Field | Type | Description |
| :--- | :--- | :--- |
| `bill_id` | `str` | State bill identifier (e.g. `telangana-vs-bill-11-2024`) |
| `state` | `str` | State jurisdiction (`Andhra Pradesh`, `Karnataka`, `Kerala`, `Telangana`) |
| `company_id` | `str` | ISIN or unique corporate entity identifier |
| `company_name` | `str` | Official registered corporate name |
| `ticker` | `str` | Verified NSE trading symbol (empty if unlisted) |
| `exchange` | `str` | Exchange (`NSE`, `BSE`, or empty) |
| `listed_status` | `str` | `listed`, `unlisted`, `subsidiary_of_listed`, `public_sector_entity` |
| `sector` | `str` | Regulated economic sector from State taxonomy |
| `sub_sector` | `str` | Specific industry sub-sector |
| `business_activity` | `str` | Specific company activity creating exposure |
| `state_presence` | `list[str]` | Operational presence types in this State |
| `presence_type` | `str` | Primary presence type (`manufacturing`, `power_generation`, `service_operation`, etc.) |
| `exposure_type` | `str` | `regulatory`, `taxation`, `labour`, `licensing`, `energy`, `transport`, `consumer`, etc. |
| `exposure_direction` | `str` | Qualitative business impact: `positive`, `negative`, `mixed`, `neutral`, `unknown` |
| `exposure_strength` | `str` | `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN` |
| `direct_indirect` | `str` | `DIRECT` vs `INDIRECT` |
| `geographic_scope` | `str` | `state_specific`, `regional`, `national_with_state_operations` |
| `mechanism` | `str` | Statutory mechanism: `compliance`, `taxation`, `labour_requirement`, `regulation` |
| `evidence` | `list[Evidence]` | List of `CorporateExposureEvidence` citing bill text and annual filings |
| `confidence` | `str` | `HIGH`, `MEDIUM`, `LOW` |
| `provenance` | `dict` | Field-level provenance mapping |
| `missing_information` | `list[str]` | Data gaps prior to any future market-impact modeling |
| `verified_at` | `str` | ISO 8601 UTC timestamp |

---

## 2. Controlled State Company Universe

Defined in `knowledge/state_company_universe.py`, the universe contains **51 verified companies**:
- **46 Listed Companies**: High-quality Indian corporate entities across banking, infrastructure, energy, IT, pharmaceuticals, FMCG, retail, real estate, and automotive.
- **5 Unlisted Public Utilities**: KSEB (Kerala State Electricity Board), TSGENCO (Telangana Power Generation), APGENCO (Andhra Pradesh Power Generation), KSRTC (Karnataka State Road Transport), KL-RTC (Kerala State Road Transport).

### State-Wise Presence Distribution:
- **Andhra Pradesh**: 35 companies
- **Karnataka**: 37 companies
- **Kerala**: 25 companies
- **Telangana**: 33 companies

---

## 3. Direct vs. Indirect Exposure Rules

| Classification | Definition | Example |
| :--- | :--- | :--- |
| **DIRECT** | The company itself performs the regulated activity in the State or is directly subject to statutory compliance/taxation/licensing under the bill. | App-based aggregators (Zomato, Swiggy) subject to statutory welfare fee in Telangana Bill 11 of 2024; cement plant operators (UltraTech) paying electricity duty on captive generation. |
| **INDIRECT** | The company is affected through supply chain, contractor relationships, upstream input costs, downstream equipment demand, or macroeconomic ecosystem effects. | Commercial vehicle manufacturers (Tata Motors, M&M) exposed indirectly to motor vehicle tax changes via commercial fleet operator buying behavior. |
| **UNKNOWN** | Evidence is insufficient to ascertain directness. | (Never assigned as direct without proof). |

---

## 4. Exposure Strength Framework

- **HIGH**: Bill explicitly applies to the company's specific business activity AND verified State presence exists (e.g. Gig worker welfare bill $\to$ App-based food aggregators; Aquaculture Authority bill $\to$ Shrimp processors).
- **MEDIUM**: Bill applies to broader economic sector or state-level statutory compliance (e.g. State GST procedural amendments, general factories shifts) AND verified State business presence exists.
- **LOW**: Indirect ecosystem exposure with verified contextual evidence.
- **UNKNOWN**: Insufficient evidence.

---

## 5. Quality Audit Summary

From `data/state_bills/corporate_exposure_quality_report.json`:

| Metric | Result | Target |
| :--- | :--- | :--- |
| **Total Candidate Companies** | **51** | 50–100 |
| **Verified Companies** | **51** | 100% |
| **Listed Companies** | **46** | Explicit |
| **Unlisted Companies** | **5** | Explicit |
| **Total State Bills Analyzed** | **44** | 44 |
| **Bills with Corporate Exposure** | **21** | Empirical |
| **Bills without Corporate Exposure (Rejected/Omitted)** | **23** | Empirical |
| **Total Bill-Company Exposures** | **86** | Empirical |
| **Direct Exposures** | **82** | $\ge 90\%$ |
| **Indirect Exposures** | **4** | Cautious |
| **HIGH Exposure Strength** | **45** | Empirical |
| **MEDIUM Exposure Strength** | **37** | Empirical |
| **LOW Exposure Strength** | **4** | Empirical |
| **HIGH Confidence Mappings** | **82** | Empirical |
| **Mappings with Bill Text Evidence** | **86** | 100% |
| **Mappings with Company Filing Evidence** | **86** | 100% |
| **Mappings with Both Evidences** | **86** | **100%** |
| **Unsupported Mappings** | **0** | **0 (STRICT)** |
| **State Market Predictions Generated** | **0** | **0 (STRICT)** |
| **Central Baseline (Bills / Predictions)** | **22 / 4,700** | **100% FROZEN** |

---

## 6. Examples of Inspectable Corporate Exposure Chains

### Example 1: Telangana Gig & Platform Workers Bill, 2024
```
STATE BILL: The Telangana Gig and Platform Workers (Registration and Welfare) Bill, 2024
  ↓
POLICY DOMAIN: Labour, Employment & Gig Economy
  ↓
ECONOMIC SECTOR: Labour & Employment (Secondary: Gig Economy, IT & Digital Services)
  ↓
BUSINESS ACTIVITY: App-based platform delivery & aggregator operations
  ↓
STATE PRESENCE: Service operations, dark stores, and active gig delivery fleets across Hyderabad & Warangal
  ↓
COMPANY: Zomato Limited (NSE: ZOMATO, Listed)
  ↓
EXPOSURE: DIRECT / HIGH Strength / Negative Direction (Statutory 1-2% welfare cess on platform transactions)
  ↓
EVIDENCE:
  - Bill: Section 3 / Statement of Objects and Reasons (Levy of welfare fee on aggregators)
  - Company: Annual Report 2023-24 (Operational Footprint & Delivery Fleet in Telangana)
  ↓
MISSING INFORMATION:
  - Exact platform gross merchandise value (GMV) originating strictly within Telangana.
  - Welfare cess financial pass-through elasticity to consumers/restaurants.
```

### Example 2: Andhra Pradesh Aquaculture Development Authority Bill, 2025
```
STATE BILL: The Andhra Pradesh State Aquaculture Development Authority (Amendment) Bill, 2025
  ↓
POLICY DOMAIN: Agriculture, Rural & Fisheries
  ↓
ECONOMIC SECTOR: Fisheries (Secondary: Food Processing)
  ↓
BUSINESS ACTIVITY: Shrimp hatchery, farming, and processing operations
  ↓
STATE PRESENCE: Corporate headquarters, hatcheries, and processing plants in Kakinada district, AP
  ↓
COMPANY: Apex Frozen Foods Limited (NSE: APEX, Listed)
  ↓
EXPOSURE: DIRECT / HIGH Strength / Positive Direction (Statutory quality standardisation and export certifications)
  ↓
EVIDENCE:
  - Bill: Regulatory clauses establishing Aquaculture Development Authority standards
  - Company: Annual Report 2023-24 (Kakinada processing plants & hatchery disclosures)
  ↓
MISSING INFORMATION:
  - Proportion of export procurement directly registered with AP Aquaculture Authority.
```

---

## 7. Future Integration with Market-Impact Modeling

When market-impact modeling for State legislation is introduced in future tasks:
1. **Missing Information Must Be Filled**: Facility-level state revenue contributions, local market shares, and statutory cost-pass-through elasticities must be quantified.
2. **Unlisted Entities Must Remain Unpredicted**: Entities such as KSEB, TSGENCO, and KSRTC must not be coerced into equity pricing engines.
3. **Indirect Exposures Must Be Evaluated with Attenuation**: Indirect exposures (such as auto manufacturers on motor vehicle tax changes) must incorporate transmission friction and lower elasticity weights.
