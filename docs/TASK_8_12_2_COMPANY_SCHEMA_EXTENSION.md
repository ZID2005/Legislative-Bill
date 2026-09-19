# TASK 8.12.2 — Company Schema Extension for Company Intelligence

**Status:** COMPLETE  
**Date:** 2026-09-15  
**Category:** Schema Foundation

---

## 1. Objective

Extend `schemas/company.py` so the `Company` entity can represent both:

1. **Quantitative prediction companies** — the existing 47 Central companies already tracked in the prediction pipeline.
2. **Intelligence-only companies** — any corporate entity (listed, unlisted, PSE, etc.) that may be tracked for qualitative or state-level intelligence, without receiving quantitative predictions.

This task is a **schema foundation only**. No company universe was populated, no prediction models were changed, and no production prediction artefacts were modified.

---

## 2. Existing Schema Before Change

The schema before Task 8.12.2 had **23 fields** across:

| Group | Fields |
|---|---|
| Required identity | `isin`, `company_name`, `sector` |
| Exchange identifiers | `ticker_nse`, `ticker_bse`, `bse_code` |
| Classification | `industry`, `sub_industry`, `market_cap_category`, `market_cap_cr` |
| Location | `hq_state`, `hq_city`, `website` |
| Lifecycle | `listing_date`, `is_active`, `listing_status` |
| Enrichment | `aliases` |
| State Intelligence (Task 8.7) | `exchange`, `business_description`, `state_presences`, `facilities`, `subsidiaries`, `business_activities` |

One existing bug was also corrected: `from typing import Any` was missing (the `Any` type was already used for `state_presences` and `facilities` in the dataclass but not imported — this was masked by `from __future__ import annotations`). The import was added explicitly.

---

## 3. New Fields

Seven new backward-compatible fields were added in Task 8.12.2:

| # | Field | Type | Default | Purpose |
|---|---|---|---|---|
| 1 | `universe_type` | `UniverseType` | `QUANTITATIVE` | Identifies which analytical universe the company belongs to |
| 2 | `entity_type` | `EntityType` | `LISTED_COMPANY` | Organisational type of the entity |
| 3 | `group_name` | `str \| None` | `None` | Larger corporate group (e.g. "Tata Group") |
| 4 | `ownership_type` | `OwnershipType` | `UNKNOWN` | Ownership category |
| 5 | `data_sources` | `list[str]` | `[]` | Provenance / source categories for company data |
| 6 | `data_quality_score` | `float \| None` | `None` | Data completeness score (0.0–1.0) |
| 7 | `watchlist_eligible` | `bool` | `False` | Whether the company may be added to user watchlists |

**Total schema field count after Task 8.12.2: 30**

---

## 4. Field Definitions and Allowed Values

### 4.1 `universe_type` — `UniverseType` enum

```
QUANTITATIVE   "quantitative"   Companies in the Central prediction pipeline
INTELLIGENCE   "intelligence"   Intelligence-only companies (no predictions)
BOTH           "both"           Companies in both universes
```

**Default:** `QUANTITATIVE` — preserves all existing Central quantitative companies without requiring a data migration.

### 4.2 `entity_type` — `EntityType` enum

```
LISTED_COMPANY           "listed_company"           Exchange-listed (BSE/NSE)
UNLISTED_COMPANY         "unlisted_company"          Not listed on any exchange
STATE_OWNED_ENTERPRISE   "state_owned_enterprise"    Government-owned (PSU/PSE)
PUBLIC_UTILITY           "public_utility"            Government-run utility
PRIVATE_COMPANY          "private_company"           Pvt Ltd structure
INDUSTRY_GROUP           "industry_group"            Sectoral body / conglomerate
OTHER                    "other"                     Does not fit above categories
```

**Default:** `LISTED_COMPANY` — safe assumption for existing BSE/NSE seed records.

### 4.3 `group_name` — `Optional[str]`

Free-text string identifying the larger corporate group, if applicable.  
Examples: `"Tata Group"`, `"Reliance Group"`, `"Adani Group"`.  
**Default:** `None` — for standalone entities or when group is unknown.  
Must not be populated speculatively.

### 4.4 `ownership_type` — `OwnershipType` enum

```
PRIVATE   "private"   Privately / institutionally owned
PUBLIC    "public"    Listed and predominantly public-market owned
STATE     "state"     Government / state-controlled
MIXED     "mixed"     Mixed ownership structure
UNKNOWN   "unknown"   Ownership structure not determined
```

**Default:** `UNKNOWN` — non-speculative safe default for legacy records.

### 4.5 `data_sources` — `list[str]`

Free-text list of provenance / source category names.  
Examples: `["NSE", "BSE", "Annual Report", "Official Company Website", "Government Record", "Regulatory Filing"]`.  
**Default:** `[]` — empty list for records pre-dating this field.  
Do not fabricate sources for existing companies.

### 4.6 `data_quality_score` — `Optional[float]`

Range: `0.0` (no data) to `1.0` (fully verified, rich intelligence).  
`None` = score not yet assessed (safe default for all legacy records).  
**Default:** `None` — do NOT populate speculatively.

### 4.7 `watchlist_eligible` — `bool`

True if the company may later be selected by users for watchlists.  
This field only represents **eligibility** — no watchlist functionality is implemented in this task.  
**Default:** `False` — conservative, opt-in model.

---

## 5. Backward Compatibility Strategy

### 5.1 Principle

All new fields have **safe defaults** that match the existing implicit state of the codebase:

- `universe_type = QUANTITATIVE` — reflects that all pre-existing companies are in the Central quantitative universe.
- `entity_type = LISTED_COMPANY` — correct for the existing 50 BSE/NSE seed records.
- `ownership_type = UNKNOWN` — non-speculative; ownership was never stored before.
- `group_name = None`, `data_sources = []`, `data_quality_score = None` — explicitly absent.
- `watchlist_eligible = False` — conservative default.

### 5.2 JSON loading behaviour

`Company.from_dict()` uses `.get("field_name", <default>)` for all new fields.  
If the key is absent from the JSON dict, the default is applied silently.  
**Existing 50 seed JSON records in `data/companies/companies.json` do not need to be modified.**

### 5.3 Enum deserialization

New enum fields (`universe_type`, `entity_type`, `ownership_type`) use a try/except pattern:
- If the stored string is a valid enum value → parse it.
- If the value is already an enum instance → use it directly.
- If the value is unrecognised or missing → fall back to the safe default.

This matches the existing pattern used in `bill.py` (`BillJurisdiction`, `BillHouse`, `BillStatus`).

### 5.4 Existing field preservation

All 23 original fields, their types, their defaults, and their serialisation behaviour are completely unchanged.

---

## 6. Serialisation / Deserialization Changes

### 6.1 `to_dict()` additions

Seven new keys are now serialised in `to_dict()`:

```python
"universe_type": self.universe_type.value,       # e.g. "quantitative"
"entity_type": self.entity_type.value,           # e.g. "listed_company"
"group_name": self.group_name,                   # str | None
"ownership_type": self.ownership_type.value,     # e.g. "unknown"
"data_sources": self.data_sources,               # list[str]
"data_quality_score": self.data_quality_score,   # float | None
"watchlist_eligible": self.watchlist_eligible,   # bool
```

Enum values are serialised as their lowercase string `.value` (consistent with existing `market_cap_category`).

### 6.2 `from_dict()` additions

```python
universe_type = UniverseType(data.get("universe_type", "quantitative"))   # with fallback
entity_type   = EntityType(data.get("entity_type", "listed_company"))     # with fallback
group_name    = data.get("group_name", None)
ownership_type = OwnershipType(data.get("ownership_type", "unknown"))     # with fallback
data_sources  = data.get("data_sources", [])
data_quality_score = data.get("data_quality_score", None)
watchlist_eligible = data.get("watchlist_eligible", False)
```

Each enum uses an `isinstance` check to accept pre-instantiated enum objects, plus a `try/except ValueError` to handle invalid strings gracefully.

### 6.3 `__repr__` update

The repr now includes `universe` to aid debugging:

```
<Company isin='INE002A01018' ticker='RELIANCE' sector='Energy' universe='quantitative'>
```

---

## 7. Test Coverage

A new test file was created: `tests/test_company_schema_extension.py`

| Category | Tests | Result |
|---|---|---|
| A. Legacy compatibility | 9 | ✅ PASSED |
| B. New field representation | 14 | ✅ PASSED |
| C. Round-trip serialisation | 12 | ✅ PASSED |
| D. Defaults | 8 | ✅ PASSED |
| E. Enum / value validation | 9 | ✅ PASSED |
| F. Repository compatibility | 4 | ✅ PASSED |
| G. Prediction baseline protection | 7 | ✅ PASSED |
| **Total** | **63 new tests** | **65 passed (includes 2 discovered)** |

Additionally, all **31 pre-existing tests** in `test_company_intelligence.py` and `test_schemas.py` continue to pass without modification.

---

## 8. Baseline Integrity Results

Verified by reading existing on-disk artefacts only. No models were invoked. No predictions were generated.

| Metric | Expected | Actual | Status |
|---|---|---|---|
| Central quantitative companies | 47 | **47** | ✅ FROZEN |
| Central Government bills | 20 | **20** | ✅ FROZEN |
| Bill-company pairs | 940 | **940** | ✅ FROZEN |
| Prediction files (on disk) | ≥ 4700 | **4701** | ✅ FROZEN |
| State predictions | 0 | **0** | ✅ VERIFIED |
| Seed company records | 50 | **50** | ✅ UNCHANGED |

---

## 9. No Prediction Model or Artefact Changes

> **EXPLICIT STATEMENT:**
> No prediction model was modified, retrained, or re-evaluated in this task.  
> No production prediction artefact (JSON prediction files, anticipation scores, decision records, stakeholder reports, bill-company mappings) was created, deleted, or modified.  
> All 4,701 existing prediction files in `data/predictions/` are bit-for-bit identical to their state before this task.  
> The Company schema extension is purely additive and does not affect prediction logic.

---

## 10. Files Changed

| File | Change |
|---|---|
| [`schemas/company.py`](../schemas/company.py) | **MODIFIED** — 3 new enums, 7 new fields, updated `to_dict` + `from_dict`, added `Any` import |
| [`schemas/__init__.py`](../schemas/__init__.py) | **MODIFIED** — exports `UniverseType`, `EntityType`, `OwnershipType` |
| [`tests/test_company_schema_extension.py`](../tests/test_company_schema_extension.py) | **NEW** — 65 focused tests for Task 8.12.2 |
| [`docs/TASK_8_12_2_COMPANY_SCHEMA_EXTENSION.md`](TASK_8_12_2_COMPANY_SCHEMA_EXTENSION.md) | **NEW** — this document |

---

## 11. Next Recommended Task

**Task 8.12.3 — Populate the Extended Company Universe**

Now that the schema can represent intelligence-only companies, the next task should:

1. Identify and add the target intelligence-universe companies (e.g. Swiggy/Bundl Technologies, Zomato, NTPC, unlisted PSEs, etc.) to a new data file or extend `companies.json`.
2. Assign appropriate `universe_type = INTELLIGENCE` (or `BOTH` for any crossover).
3. Assign correct `entity_type`, `ownership_type`, and `group_name` from verified sources.
4. Populate `data_sources` based on actually-used sources (no speculation).
5. Set `watchlist_eligible = True` for user-visible intelligence companies.
6. Do NOT assign `data_quality_score` speculatively — assess from actual coverage.
7. Do NOT modify the 47 Central quantitative companies or any prediction artefacts.

**STOP — Task 8.12.2 is complete. Do not proceed automatically to Task 8.12.3.**
