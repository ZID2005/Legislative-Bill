# Task 8.6: State Sector & Stakeholder Intelligence Layer

## Executive Summary

Task 8.6 introduces an additive, structured, and factual economic-sector and stakeholder intelligence layer for Indian State legislative bills within the **India Legislative Intelligence & Market Impact Prediction Platform**.

Operating across all 44 analyzed State bills spanning 4 pilot States (**Andhra Pradesh**, **Karnataka**, **Kerala**, and **Telangana**), this layer provides comprehensive answers to 10 foundational economic questions:
1. **Which sectors does this State bill affect?**
2. **Which industries and sub-industries are affected?**
3. **Which types of businesses are affected?**
4. **Which occupations and groups of people are affected?**
5. **Which economic activities are affected?**
6. **Which stakeholders benefit?**
7. **Which stakeholders may face additional costs or compliance requirements?**
8. **Is the effect direct or indirect?**
9. **Is the impact primarily State/local rather than national?**
10. **Is there enough evidence to associate the bill with a listed company?**

---

## Strict Architectural Boundaries

```
+-----------------------------------------------------------------------------------+
|                           CENTRAL GOVERNMENT (FROZEN)                             |
|  22 Metadata Bills | 20 Modelled Bills | 47 Listed Companies | 4,700 Predictions   |
|  4,700 Decision Records | 940 Anticipation Records | 14,100 Stakeholder Reports   |
+-----------------------------------------------------------------------------------+
                                         |
                                         | STRICT ISOLATION (ZERO LEAKAGE)
                                         v
+-----------------------------------------------------------------------------------+
|                        STATE LEGISLATIVE INTELLIGENCE                             |
|  44 Bills (AP: 12, KA: 11, KL: 11, TS: 10) | State Predictions: EXACTLY ZERO       |
|  Task 8.4: Knowledge Layer  -->  Task 8.6: Sector & Stakeholder Intelligence      |
|  StateBillEconomicProfile (Fact & Bounded Interpretation, NO Predictions)         |
+-----------------------------------------------------------------------------------+
```

### Tripartite Epistemic Boundary
1. **FACT**:
   Statutory mandates explicitly laid down in the bill text, such as:
   - Registration requirements with the State Welfare Board.
   - Specific duty adjustments on electricity consumption.
   - Statutory fee schedules for motor vehicle chassis and carriage permits.
2. **BOUNDED INTERPRETATION**:
   Cautious, non-speculative qualitative assessment:
   - *"May increase compliance requirements for covered commercial employers."*
   - *"Eligible gig workers may benefit from social security safety-net schemes."*
3. **PREDICTION (PROHIBITED)**:
   - Absolutely no stock price projections, price targets, buy/sell ratings, equity returns, or market alpha.
   - State market predictions remain strictly **0**.

---

## 1. State Economic Sector Taxonomy

The State sector taxonomy comprises 42 curated economic sectors, providing broader coverage than Central corporate-only classifications:

| Category Group | Sectors Included |
| :--- | :--- |
| **Primary & Natural Resources** | Agriculture, Fisheries, Livestock, Mining, Metals, Water, Environment |
| **Industry & Secondary** | Manufacturing, Food Processing, Chemicals, Textiles, Construction, Infrastructure |
| **Transport & Movement** | Roads & Transport, Logistics, Ports & Maritime |
| **Energy & Utilities** | Energy, Electricity, Renewable Energy |
| **Commerce & Finance** | Retail, Wholesale, MSME, Banking & Finance, Insurance |
| **Technology & Media** | IT & Digital Services, Telecommunications |
| **Social & Services** | Healthcare, Pharmaceuticals, Education, Hospitality, Tourism, Housing, Consumer Services, Professional Services |
| **Work & Governance** | Labour & Employment, Gig Economy, Public Administration, Municipal Services, Urban Development, Rural Development, Other |

### Classification Levels
- `PRIMARY`: The dominant regulated economic sector.
- `SECONDARY`: Secondary or downstream regulated sectors.
- `NONE`: No economic sector regulated (e.g. parliamentary disqualification procedures).
- `UNKNOWN`: Insufficient evidence to classify.

---

## 2. Extensible Stakeholder Taxonomy

Stakeholders are organized across four extensible branches:

1. **PEOPLE**:
   Farmers, Agricultural workers, Gig workers, Employees, Employers, Consumers, Students, Patients, Tenants, Homeowners, Property buyers, Senior citizens, Women, Children, Rural residents, Urban residents, Cine and cultural activists, Doctors and medical practitioners, Non-resident workers.
2. **BUSINESSES**:
   MSMEs, Startups, Large enterprises, Retailers, Wholesalers, Manufacturers, Contractors, Transport operators, Aggregators, Developers, Hotels, Restaurants, Hospitals, Schools, Colleges, Professional firms, Aquaculture operators, Power generation companies, Commercial establishments, Partnership firms.
3. **INSTITUTIONS**:
   State Government, Local Government, Municipal bodies, Panchayats, Regulators, Courts/tribunals, Public authorities, Trade unions, Industry associations, Welfare boards, State universities, Police and law enforcement.
4. **ECONOMIC GROUPS**:
   Investors, Taxpayers, Landowners, Exporters, Importers, Service providers, Labour force, Electricity consumers, Water users.

---

## 3. Grounded Stakeholder Impact & Evidence Linking

Each stakeholder is evaluated with:
- `role`: `affected`, `primary_affected`, `secondary_affected`, `potential_beneficiary`, `potential_cost_bearer`, `regulator/implementer`, `indirectly_affected`
- `direction`: `positive`, `negative`, `mixed`, `neutral`, `unknown`
- `mechanism`: `compliance`, `taxation`, `subsidy`, `licensing`, `labour_requirement`, `pricing`, `land_use`, `environmental_requirement`, `registration`, `reporting`, `procurement`, `access`, `eligibility`, `public_service`, `regulation`, `infrastructure`, `enforcement`, `other`
- `impact_type`: `DIRECT` vs `INDIRECT`
- `evidence`: Structured `EvidenceReference` citing actual sections, clauses, or corpus locations without fabricating section numbers.

---

## 4. State Economic Geography

State legislation is categorized by geographic relevance:
- `state-wide`: Applicable across the entire state jurisdiction.
- `city/municipal`: Focused on a specific urban municipal corporation (e.g. Greater Bengaluru Governance Bill).
- `urban`: Applicable to all urban local bodies and municipal towns.
- `rural`: Applicable to village administration and Gram Panchayats.
- `regional`: Applicable to specific river basins, irrigation command areas, or geographic zones.
- `sector-specific geography`: Applicable to designated geographic belts (e.g. coastal aquaculture zones).

---

## 5. Listed-Company Exposure Readiness

A readiness classification evaluates whether a bill could later be considered for corporate exposure mapping:
- `HIGH`: Major regulated industry with substantial listed corporate participation in the State (e.g. GST amendments, Electricity duty, Gig worker platform regulations, Commercial vehicle taxation).
- `MEDIUM`: Sectors with moderate corporate presence or large unlisted sector with listed supply chains (e.g. Private universities, Aquaculture exports, Clinical establishments, Agricultural mandis).
- `LOW`: Localized or fragmented sectors with negligible direct listed corporate footprint (e.g. Bovine breeding, Partnership firm registration, Ancient monuments).
- `NONE`: Purely administrative, electoral, or penal measures with zero corporate exposure (e.g. Prevention of MLA disqualification, Hate speech prevention, Public records administration, Obsolete statute repeals).
- `UNKNOWN`: Insufficient evidence.

> [!NOTE]
> This is strictly a readiness indicator. It produces **no** company names, stock tickers, returns, target prices, or recommendations.

---

## 6. Schema Specification

The `StateBillEconomicProfile` model is defined in `schemas/state_economic_profile.py` and embedded in `StateBillKnowledge`:

```json
{
  "bill_id": "telangana-vs-bill-11-2024",
  "state": "Telangana",
  "policy_domain": "Labour, Employment & Gig Economy",
  "primary_sector": "Labour & Employment",
  "secondary_sectors": ["Gig Economy", "Consumer Services", "IT & Digital Services"],
  "sub_sectors": ["App-Based Delivery", "Platform Services"],
  "economic_activities": ["Platform work delivery", "Aggregator commission fee collection", "Welfare board registration"],
  "business_types": ["Commercial establishments", "App-based aggregators", "Digital platform companies"],
  "stakeholders": [
    {
      "stakeholder": "Gig workers",
      "category": "people",
      "role": "primary_affected",
      "direction": "positive",
      "mechanism": "labour_requirement",
      "impact_type": "DIRECT",
      "evidence": {
        "source_type": "bill_text",
        "section": "Section 3 / Statement of Objects",
        "text_reference": "Requires registration of platform-based gig workers and aggregator welfare cess contribution."
      },
      "description": "The bill establishes statutory social security and welfare board protections for platform workers."
    },
    {
      "stakeholder": "Aggregators",
      "category": "businesses",
      "role": "potential_cost_bearer",
      "direction": "negative",
      "mechanism": "compliance",
      "impact_type": "DIRECT",
      "evidence": {
        "source_type": "bill_text",
        "section": "Aggregator Compliance Clauses",
        "text_reference": "Obligates app-based platform companies to register and remit statutory welfare fee."
      },
      "description": "Digital platform operators face new registration, reporting, and statutory contribution obligations."
    }
  ],
  "geographic_scope": "state-wide",
  "direct_impacts": [
    "Direct statutory labour_requirement requirement affecting Gig workers.",
    "Direct statutory compliance requirement affecting Aggregators."
  ],
  "indirect_impacts": [
    "Secondary economic or pricing effect on State Government."
  ],
  "impact_mechanisms": ["labour_requirement", "compliance", "regulation"],
  "company_exposure_readiness": "HIGH",
  "confidence": "HIGH",
  "factual_summary": {
    "who_may_be_affected": ["Gig workers", "Aggregators", "State Government"],
    "how_affected": [
      "The bill introduces statutory working-condition, registration, or welfare provisions.",
      "Establishes updated compliance, record-keeping, and reporting obligations."
    ],
    "who_may_benefit": ["Gig workers"],
    "who_may_bear_costs": ["Aggregators"]
  },
  "provenance": {
    "primary_sector": "SYSTEM_DERIVED",
    "evidence": "AUTHORITATIVE_CORPUS_GROUNDED",
    "company_exposure_readiness": "SYSTEM_DERIVED"
  },
  "schema_version": "1.0.0"
}
```

---

## 7. Quality Audit Summary

From `data/state_bills/economic_intelligence_quality_report.json`:

| Metric | Result | Target |
| :--- | :--- | :--- |
| **Total State Bills Analyzed** | **44** | 44 (100%) |
| **Primary Sector Classified** | **44** | 44 (100%) |
| **Secondary Sectors Classified** | **44** | 44 (100%) |
| **Stakeholder Impacts Mapped** | **100** | >= 88 (avg >= 2 per bill) |
| **Evidence References Linked** | **46** | >= 44 |
| **Direct Impacts Identified** | **75** | >= 44 |
| **Indirect Impacts Identified** | **44** | >= 44 |
| **Geographic Scopes Assigned** | **44** | 44 (100%) |
| **Unsupported Financial Claims** | **0** | **0 (STRICT)** |
| **State Predictions Generated** | **0** | **0 (STRICT)** |
| **Central Baseline Records** | **22 metadata, 4,700 predictions** | **100% Frozen** |

### Corporate Exposure Readiness Breakdown
- **HIGH**: 7 bills (GST, VAT, Electricity Duty, Platform/Gig Workers, Motor Vehicle Taxation)
- **MEDIUM**: 24 bills (Factories, Shops & Establishments, Building Tax, Private Universities, Mandi Markets, Aquaculture)
- **LOW**: 8 bills (Municipal Administration, Panchayat Raj, Veterinary Universities, Partnership Firms)
- **NONE**: 5 bills (Legislative Disqualification, Hate Speech Prevention, Public Records, Repealing & Saving, Historical Monuments)

---

## 8. Verification & Validation

All 23 focused unit and integration tests passed in `tests/test_state_economic_intelligence.py`:
- Sector taxonomy & stakeholder taxonomy coverage
- Grounded evidence linking & direct/indirect distinction
- Cross-state conceptual search
- All 4 State cohorts (AP: 12, KA: 11, KL: 11, TS: 10) validated
- Zero unsupported claims confirmed
- Backward compatibility & Central frozen baseline verified
