# 28-State Legislative Coverage & Readiness Registry

This registry provides the machine-verifiable and human-readable readiness status for all 28 Indian States within the Legislative Intelligence Platform.

---

## 1. System Coverage Status Summary

| Metric | Value |
|---|---|
| **Total Indian States** | 28 |
| **Fully Implemented States** | 4 (Andhra Pradesh, Karnataka, Kerala, Telangana) |
| **Ready for Adapter** | 3 (Goa, Rajasthan, Uttar Pradesh) |
| **Researched / In Evaluation** | 3 (Himachal Pradesh, Maharashtra, Tamil Nadu) |
| **Source Found (Unprocessed)** | 11 (Assam, Bihar, Chhattisgarh, Gujarat, Haryana, Jharkhand, MP, Meghalaya, Odisha, Punjab, Uttarakhand, West Bengal) |
| **Source Limited / Intermittent** | 7 (Arunachal Pradesh, Manipur, Mizoram, Nagaland, Sikkim, Tripura) |
| **Active Pilot Bills** | 44 (12 AP, 11 KA, 11 KL, 10 TS) |
| **Verified PDFs** | 44 (100% SHA-256 verified) |
| **Knowledge Records** | 44 (100% plain-language summary & policy classification) |

---

## 2. All 28 Indian States Coverage Table

| # | State | Official Legislative Source | Adapter Status | Ingestion Status | Bills | PDFs | Languages | Feasibility | Notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **Andhra Pradesh** | AP Legislative Assembly (`aplegislature.org`) | **IMPLEMENTED** | PILOT_INGESTED | 12 | 12 | English, Telugu | HIGH | Official portal; direct PDF links on `legislation.aplegislature.org` |
| 2 | Arunachal Pradesh | Arunachal Pradesh Assembly (`arunachalassembly.gov.in`) | **SOURCE_LIMITED** | NOT_STARTED | 0 | 0 | English | LOW | Limited digital bills repository; periodic PDF uploads |
| 3 | Assam | Assam Legislative Assembly (`assambidhansabha.org`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | English, Assamese | MEDIUM | Bilingual English/Assamese; legislative business listed per session |
| 4 | Bihar | Bihar Vidhan Sabha (`vidhansabha.bih.nic.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | Hindi | MEDIUM | Hindi-primary portal; session business papers accessible |
| 5 | Chhattisgarh | Chhattisgarh Vidhan Sabha (`cgvidhansabha.gov.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | Hindi | MEDIUM | Session debates and bills in Hindi |
| 6 | Goa | Goa Legislative Assembly (`goavidhansabha.gov.in`) | **READY_FOR_ADAPTER** | RESEARCHED | 0 | 0 | English | HIGH | English-first portal with clear session bills and acts listings |
| 7 | Gujarat | Gujarat Legislative Assembly (`gujaratassembly.gov.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | English, Gujarati | MEDIUM | Bilingual Gujarati/English legislative business |
| 8 | Haryana | Haryana Vidhan Sabha (`haryanaassembly.gov.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | English, Hindi | MEDIUM | Bills and acts uploaded per session |
| 9 | Himachal Pradesh | Himachal Pradesh Vidhan Sabha (`hpvidhansabha.nic.in`) | **RESEARCHED** | RESEARCHED | 0 | 0 | English, Hindi | MEDIUM | Pioneer of eVidhan paperless initiative. Currently network timeouts observed |
| 10 | Jharkhand | Jharkhand Vidhan Sabha (`jharkhandvidhansabha.nic.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | Hindi | MEDIUM | Session business and bills listed in Hindi |
| 11 | **Karnataka** | Karnataka Legislative Assembly (`kla.kar.nic.in`) | **IMPLEMENTED** | PILOT_INGESTED | 11 | 11 | English, Kannada | HIGH | Official NIC portal with session-wise bill listings and direct PDF downloads |
| 12 | **Kerala** | Kerala Legislative Assembly (`niyamasabha.nic.in`) | **IMPLEMENTED** | PILOT_INGESTED | 11 | 11 | English, Malayalam | HIGH | Official Niyamasabha portal with comprehensive bill tracking (Introduced, Passed, Assented) |
| 13 | Madhya Pradesh | MP Vidhan Sabha (`mpvidhansabha.nic.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | Hindi | MEDIUM | Hindi-language legislative business |
| 14 | Maharashtra | Maharashtra Legislature (`mls.org.in`) | **RESEARCHED** | RESEARCHED | 0 | 0 | Marathi, English | MEDIUM | Bicameral legislature (MLS). Primary language Marathi with high translation overhead |
| 15 | Manipur | Manipur Legislative Assembly (`manipurassembly.nic.in`) | **SOURCE_LIMITED** | NOT_STARTED | 0 | 0 | English, Manipuri | LOW | Intermittent updates on assembly portal |
| 16 | Meghalaya | Meghalaya Legislative Assembly (`megassembly.gov.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | English | MEDIUM | English-language bills listed per session |
| 17 | Mizoram | Mizoram Legislative Assembly (`mizoramassembly.gov.in`) | **SOURCE_LIMITED** | NOT_STARTED | 0 | 0 | English, Mizo | LOW | Limited digital bills documentation |
| 18 | Nagaland | Nagaland Legislative Assembly (`nagaland.gov.in/nla`) | **SOURCE_LIMITED** | NOT_STARTED | 0 | 0 | English | LOW | English-primary; limited structured bills archive |
| 19 | Odisha | Odisha Legislative Assembly (`odishaassembly.nic.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | English, Odia | MEDIUM | Odia and English legislative business |
| 20 | Punjab | Punjab Vidhan Sabha (`punjabassembly.nic.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | English, Punjabi | MEDIUM | Session bills and acts listed in Punjabi and English |
| 21 | Rajasthan | Rajasthan Legislative Assembly (`rajasthanassembly.nic.in`) | **READY_FOR_ADAPTER** | RESEARCHED | 0 | 0 | Hindi, English | HIGH | Well-structured session bills portal with PDF links |
| 22 | Sikkim | Sikkim Legislative Assembly (`sikkimassembly.gov.in`) | **SOURCE_LIMITED** | NOT_STARTED | 0 | 0 | English, Nepali | LOW | Limited historical bills digitized |
| 23 | Tamil Nadu | Tamil Nadu Legislative Assembly (`assembly.tn.gov.in`) | **RESEARCHED** | RESEARCHED | 0 | 0 | English, Tamil | MEDIUM | Digital repository (TNLAS) and Government Gazette archive. Tamil and English |
| 24 | **Telangana** | Telangana Legislature (`legislature.telangana.gov.in`) | **IMPLEMENTED** | PILOT_INGESTED | 10 | 10 | English, Telugu, Urdu | HIGH | Official government portal with Assembly and Council legislative business |
| 25 | Tripura | Tripura Legislative Assembly (`tripuraassembly.nic.in`) | **SOURCE_LIMITED** | NOT_STARTED | 0 | 0 | English, Bengali | LOW | Limited structured digital documentation |
| 26 | Uttar Pradesh | UP Vidhan Sabha (`upvidhansabhaproceedings.gov.in`) | **READY_FOR_ADAPTER** | RESEARCHED | 0 | 0 | Hindi, English | HIGH | Large volume bicameral legislature; session bills repository active |
| 27 | Uttarakhand | Uttarakhand Vidhan Sabha (`vidhansabha.uk.gov.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | Hindi | MEDIUM | Hindi-language session business |
| 28 | West Bengal | West Bengal Legislative Assembly (`wbassembly.gov.in`) | **SOURCE_FOUND** | NOT_STARTED | 0 | 0 | English, Bengali | MEDIUM | Session bills published in English and Bengali |

---

## 3. Implementation Status Definitions

- **IMPLEMENTED**: Active source configuration in `config/state_sources.json`, custom adapter subclassing `BaseStateSourceAdapter`, verified bill ingestion, text extraction, plain-language knowledge summaries, and multi-state search support.
- **READY_FOR_ADAPTER**: Authoritative, stable HTML/PDF source identified with predictable URL schema; ready for adapter creation in subsequent milestones.
- **RESEARCHED**: Source surveyed and assessed for accessibility, language complexity, rendering architecture, and data quality.
- **SOURCE_FOUND**: Official legislative domain and basic structure identified; detailed extraction patterns pending validation.
- **SOURCE_LIMITED**: Portal updates are sporadic, document links frequently broken, or PDF digitalization incomplete.
- **UNAVAILABLE**: No dedicated legislative assembly web portal identified.
