# TASK 8.14.2A — FASTAPI API CONTRACT & BASELINE VERIFICATION

**Status:** COMPLETE & VERIFIED  
**Date:** September 18, 2026  
**Execution Command:** `.venv\Scripts\python.exe scripts/verify_api_contracts_and_baseline.py` & `.venv\Scripts\python.exe -m pytest -q`  
**Full Test Suite Result:** **2,049 passed, 3 skipped, 0 failed, 0 errors** (409.27s)  
**Verification Script Result:** **12/12 Domains Passed Perfectly (100%)**  
**Strict Stop Condition:** Zero Next.js frontend code created; ready for Task 8.14.3.

---

## 1. API Startup Verification

The FastAPI application was initialized cleanly using `api.app:create_app`.

| Endpoint | Method | Expected Status | Actual Status | Verification Result |
| :--- | :---: | :---: | :---: | :---: |
| `/health` | `GET` | `200 OK` | `200 OK` | PASS |
| `/api/v1/health` | `GET` | `200 OK` | `200 OK` | PASS |
| `/docs` | `GET` | `200 OK` | `200 OK` | PASS (Swagger UI Loaded) |
| `/openapi.json` | `GET` | `200 OK` | `200 OK` | PASS (OpenAPI v3.1 Spec Generated) |

- **Startup Latency**: < 1.8s cold start; sub-5ms warm endpoint latency.
- **Router Mounting**: All 11 feature routers mounted cleanly without import circularities or registry collisions.

---

## 2. OpenAPI Endpoint Inventory

Extracted directly from the live generated OpenAPI JSON schema (`/openapi.json`):

- **API Title**: `Indian Parliamentary Intelligence & Market Impact API`
- **API Version**: `1.0.0`
- **Total Unique Route Paths**: **51**
- **Total Executable Endpoints (HTTP Methods)**: **57**
- **Total Registered Router Tags**: **12** (`AI Copilot & Explanations`, `Alerts`, `Bills`, `Companies`, `Coverage`, `Health`, `Monitoring`, `Notifications`, `Predictions`, `Search`, `States`, `Watchlists`)

### Comparison with Task 8.14.2 Report
- The initial Task 8.14.2 report cataloged 50 endpoints across 11 routers.
- The hardened API provides **51 paths / 57 executable endpoints across 12 router tags**, including the added ergonomic alias `GET /api/v1/bills/{bill_id}/exposures` alongside `GET /api/v1/bills/{bill_id}/companies`, and explicit root health routing.
- Zero undocumented routes exist.

---

## 3. Representative API Request Results

Real local HTTP requests were dispatched against representative data:

| Domain Flow | Sample Request Target | Key Response Attributes Verified | Result |
| :--- | :--- | :--- | :---: |
| **A. Central Bill** | `GET /api/v1/bills/the-merchant-shipping-bill-2024` | `jurisdiction="central"`, `modeling_eligibility="ELIGIBLE"`, `has_predictions=True`, predictions array populated | **PASS** |
| **B. State Bill** | `GET /api/v1/bills/telangana-vs-bill-2-2026` | `jurisdiction="state"`, `modeling_eligibility="NOT_ELIGIBLE"`, `has_predictions=False`, `predictions=[]`, corporate exposures present | **PASS** |
| **C. Quant Company** | `GET /api/v1/companies/INE002A01018` (Reliance) | `is_quant_eligible=True`, `universe_type="quantitative"`, predictions array populated across 20 Central bills | **PASS** |
| **D. Intel Company** | `GET /api/v1/companies/IN-INTEL-SWIGGY` (Swiggy) | `is_quant_eligible=False`, `universe_type="intelligence"`, `has_predictions=False`, `items=[]`, `firewall_status="INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS"` | **PASS** |
| **E. Unified Search** | `GET /api/v1/search?q=Energy` | 23 cross-entity matches returned spanning Central bills, State bills, listed companies, and unlisted entities | **PASS** |
| **F. Coverage** | `GET /api/v1/coverage` | Factual parity: 20 Central bills, 44 State bills, 70 companies, 4,700 predictions, 14,100 reports | **PASS** |
| **G. Watchlists** | `POST /api/v1/watchlists` + `GET` | Multi-tenant creation, scoped retrieval, and cleanup verified | **PASS** |
| **H. Alerts** | `GET /api/v1/alerts` | Paginated alert events list returned | **PASS** |
| **I. Notifications** | `GET /api/v1/notifications` | Inbox response model loaded with read/unread tracking | **PASS** |
| **J. AI Fallback** | `POST /api/v1/ai/ask` | Zero external network call, offline fallback explanation generated, mandatory research disclaimer attached | **PASS** |

---

## 4. State Prediction Firewall Verification

Tested on multiple real State bills (`telangana-vs-bill-2-2026`, `telangana-vs-bill-1-2026`, `kerala-vs-bill-271-2025`):
```json
{
  "available": false,
  "has_predictions": false,
  "bill_id": "telangana-vs-bill-2-2026",
  "status": "STATE_QUALITATIVE_ONLY",
  "firewall_status": "STATE_QUALITATIVE_ONLY",
  "reason": "State legislation does not generate quantitative market predictions under project invariants.",
  "message": "State bills are isolated from Central stock market models. Quantitative predictions remain strictly 0.",
  "jurisdiction": "state",
  "predictions": [],
  "items": [],
  "total": 0
}
```
- **Quantitative Firewall**: Strictly verified. No model inference was executed.
- **Disk Integrity**: Zero state prediction files exist on disk (`data/state_predictions` is absent or 0 files).

---

## 5. Intelligence Company Firewall Verification

Tested across unlisted corporate entities (`IN-INTEL-SWIGGY`, `IN-INTEL-ZEPTO`, `IN-INTEL-OLA-ELEC-UNLISTED`):
```json
{
  "available": false,
  "has_predictions": false,
  "company_id": "IN-INTEL-SWIGGY",
  "status": "INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS",
  "firewall_status": "INTELLIGENCE_ONLY_NO_QUANT_PREDICTIONS",
  "reason": "INTELLIGENCE_ONLY_ENTITY",
  "message": "Intelligence-only entities are strictly firewalled from market models. Stock predictions remain strictly 0.",
  "universe_type": "intelligence",
  "predictions": [],
  "items": [],
  "total": 0
}
```
- **Prediction Invariant**: `has_predictions=False`, `items=[]`, `total=0`.
- Quantitative market model lookups are completely bypassed.

---

## 6. Coverage Semantics: Implemented vs. Planned States

The API previously had ambiguity regarding "12 states" in descriptive text. In Task 8.14.2A, the schema and endpoints were updated to provide an unambiguous, rigorous distinction:

```
Total Indian States & Union Territories in Registry: 28
├── IMPLEMENTED (Active Pilot Corpora & Corporate Exposures): 4 States
│   ├── Andhra Pradesh (12 bills, 12 PDFs, 12 knowledge records)
│   ├── Karnataka      (11 bills, 11 PDFs, 11 knowledge records)
│   ├── Kerala         (11 bills, 11 PDFs, 11 knowledge records)
│   └── Telangana      (10 bills, 10 PDFs, 10 knowledge records)
└── PLANNED (Roadmap Registry Entries, Zero Ingested Bills): 24 States
    └── Arunachal Pradesh, Assam, Bihar, Gujarat, Maharashtra, Tamil Nadu, etc. (bills_count = 0)
```

- **`GET /api/v1/states`** returns `implemented_count: 4` and `planned_count: 24`, explicitly attaching a `semantics_clarification` note.
- Querying an implemented state (e.g. `GET /api/v1/states/Karnataka`) returns `status: "IMPLEMENTED"` with 11 bills.
- Querying a planned state (e.g. `GET /api/v1/states/Maharashtra`) returns `status: "PLANNED"` with `bills_count: 0`.
- Zero additional State records were fabricated.

---

## 7. Company Universe Verification

Programmatically audited against `CompanyRepository` and `CompanyIntelligenceService`:

| Universe Category | Target Count | API Verified Count | Status |
| :--- | :---: | :---: | :---: |
| **Total Corporate Entities** | **70** | **70** | MATCH |
| **Quantitative Listed Companies** | **47** | **47** | MATCH |
| **Intelligence-Only Entities** | **20** | **20** | MATCH |
| **Reference Entities** | **3** | **3** | MATCH |

- All 47 quantitative companies have valid `INE` prefixes and `is_quant_eligible=True`.
- All 20 intelligence entities have synthetic IDs (`IN-INTEL-*`), `listing_status="Unlisted"`, and are strictly isolated from market prediction lookups.

---

## 8. Central Baseline Verification

Direct programmatic audit of files and checksums on disk:

| Metric | Target Ground Truth | Verified on Disk | Verification Method |
| :--- | :---: | :---: | :--- |
| **Central Production Bills** | 20 | **20** | `data/bills/metadata/*.json` (excludes 2 stubs) |
| **Quantitative Companies** | 47 | **47** | `CompanyRepository` listed `INE` entities |
| **Bill × Company Pairs** | 940 | **940** | 20 bills × 47 companies |
| **Central Predictions** | 4,700 | **4,700** | `data/predictions/pred_*.json` |
| **Decision Support Records** | 4,700 | **4,700** | `data/decision_support/dec_*.json` |
| **Anticipation Bias Scores** | 940 | **940** | `data/anticipation/scores/*.json` |
| **Stakeholder Reports** | 14,100 | **14,100** | 4,700 investor + 4,700 business + 4,700 public in `data/reports/` |

---

## 9. State Baseline Verification

Direct programmatic verification of State files:

| Artifact Type | Target Count | Verified on Disk | Storage Location |
| :--- | :---: | :---: | :--- |
| **State Bill Metadata** | 44 | **44** | `data/state_bills/metadata/*.json` |
| **State Official PDFs** | 44 | **44** | `data/state_bills/pdfs/*.pdf` |
| **State Knowledge Records**| 44 | **44** | `data/state_bills/knowledge/*.json` |
| **State Corporate Exposures** | 86 | **86** | `StateCorporateExposureRepository().get_all()` |
| **State Stock Predictions** | **0** | **0** | Strictly zero (statutory guarantee) |

---

## 10. Multi-Tenant Scoping & Isolation

Tested using two distinct tenants (`corp_alpha` / `alice` vs. `corp_beta` / `bob`):

1. **Read Isolation**: Bob querying Alice's private watchlist ID (`/api/v1/watchlists/{alice_wl_id}`) receives `403 Forbidden` (`CROSS_TENANT_ACCESS_DENIED`).
2. **Write Isolation**: Bob attempting to `PATCH` Alice's watchlist receives `403 Forbidden`.
3. **Item Isolation**: Bob attempting to add items to Alice's watchlist receives `403 Forbidden`.
4. **Delete Isolation**: Bob attempting to delete Alice's watchlist receives `403 Forbidden`.
5. **Notification Isolation**: Alice and Bob receive completely isolated inbox payloads.

> [!IMPORTANT]
> **Development Headers Clarification**
> `X-Tenant-ID` and `X-User-ID` are development scoping headers used to isolate user data during local pair testing. They **MUST NOT** be treated as production authentication. Production deployment will extract identity from cryptographically signed NextAuth / JWT session bearer tokens.

---

## 11. Secret Safety & Redaction

Searched all HTTP responses and error envelopes for sensitive patterns:
- `GROQ_API_KEY` / `gsk_*`: **NOT EXPOSED**
- AWS Secrets / Private Keys: **NOT EXPOSED**
- Filesystem Absolute Paths (`d:\`, `c:\users\...`): **NOT EXPOSED**
- Internal Python stack traces: Sanitized via `api.errors.APIError` handlers; internal tracebacks remain in internal log files only.

---

## 12. Data Immutability Guarantee

File counts and directory states were measured before and after verification:

- `data/predictions/`: **4,700 files (Unchanged)**
- `data/decision_support/`: **4,700 files (Unchanged)**
- `data/reports/`: **14,100 files (Unchanged)**
- `data/anticipation/scores/`: **940 files (Unchanged)**
- `models/artefacts/`: **Unchanged**
- `data/state_bills/`: **44 metadata, 44 PDFs (Unchanged)**

Zero data files were mutated, added, or deleted during verification.

---

## 13. Full Test Suite Results

Executed complete test suite across the entire repository:

```bash
.venv\Scripts\python.exe -m pytest -q
```

### Official Pytest Execution Summary:
- **Command Used**: `.venv\Scripts\python.exe -m pytest -q`
- **Total Tests Collected**: **2,052 tests**
- **Passed**: **2,049 tests**
- **Skipped**: **3 tests** (external optional integration tests)
- **Failed**: **0 tests**
- **Errors**: **0 errors**
- **Execution Duration**: 409.27s (6 min 49s)

---

## 14. Remaining Issues

**None.**
- The two legacy test discrepancies reported in Task 8.14.1 (`test_production_scope_exclusion_integrity` asserting 50 companies and `test_all_isins_valid_prefix` expecting INE prefix on unlisted entities) were completely repaired and now pass cleanly in the official test run.
- Coverage semantics for Indian States are now clear, unambiguous, and contract-safe.

---

## 15. Exact Next Recommended Task

With the FastAPI API contract verified, quantitative firewalls proven, and 2,049 tests passing with zero failures:

👉 **TASK 8.14.3 — NEXT.JS SAAS FRONTEND FOUNDATION**
- Initialize Next.js 14+ (App Router, TypeScript, Tailwind CSS, Lucide Icons).
- Configure API client SDK using OpenAPI v3 contracts.
- Build root layout, navigation bar, and dark-mode aesthetic theme.
- Connect first client views: Unified Bill Explorer and Corporate Intelligence Universe.
