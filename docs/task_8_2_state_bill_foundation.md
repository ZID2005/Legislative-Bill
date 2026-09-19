# TASK 8.2 — State Bill Foundation & Jurisdiction Support

> **Authoritative System Notice:**
> *"This task establishes State-bill structural support only. It does not constitute State-bill ingestion or State-bill production data."*

---

## 1. Objective

The objective of Task 8.2 is to extend the existing, fully-validated legislative system so that it can conceptually and structurally represent Indian State Government bills alongside the existing Central Government bills.

This foundation establishes:
- Formal jurisdiction distinction (`central` vs `state`).
- State attribution (`state: Optional[str] = None`).
- State legislature chamber representation (`Vidhan Sabha` and `Vidhan Parishad`).
- Reusable Indian state name normalization mechanism.
- Backward-compatible repository queries (`get_by_jurisdiction()`, `get_by_state()`).
- Strict 100% preservation and backward compatibility for all frozen Central Government bills, models, pipelines, and artifacts.

---

## 2. Existing Central Architecture Preserved

The existing Central Government bill pipeline remains **strictly frozen** and functionally unchanged:

| Asset / Pipeline Stage | Baseline Count | Task 8.2 Status |
| :--- | :---: | :---: |
| Central Government Production Bills | **20** | **UNCHANGED** (read-only, no migration required) |
| Non-legislative / Stub Bills | **2** | **UNCHANGED** (`key-issues-and-analysis`, `service-bill`) |
| Production Listed Companies | **47** | **UNCHANGED** |
| Production (Bill, Company) Pairs | **940** | **UNCHANGED** |
| Event Windows | **5** | **UNCHANGED** (`[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`) |
| Direction / Impact Predictions | **4,700** | **UNCHANGED** (zero record modifications) |
| Decision Support Records | **4,700** | **UNCHANGED** (zero record modifications) |
| Anticipation Records | **940** | **UNCHANGED** (zero record modifications) |
| Stakeholder Reports | **14,100** | **UNCHANGED** (zero record modifications) |
| Baseline Test Suite | **1,226 passed / 0 failed** | **PRESERVED** |

Existing Central Government bill records stored in `data/bills/metadata/*.json` have **not** been rewritten, migrated, or altered.

---

## 3. Schema Changes

All schema changes were implemented in [`schemas/bill.py`](file:///d:/Legislative-bill/schemas/bill.py) with zero breaking changes to existing signatures.

### Added Enum: `BillJurisdiction`
```python
class BillJurisdiction(str, Enum):
    """Jurisdiction of the legislative bill."""

    CENTRAL = "central"
    STATE = "state"
```

### Extended Enum: `BillHouse`
```python
class BillHouse(str, Enum):
    """House/chamber in which the bill was first introduced."""

    LOK_SABHA = "lok_sabha"
    RAJYA_SABHA = "rajya_sabha"
    VIDHAN_SABHA = "vidhan_sabha"        # Legislative Assembly (Lower House / Unicameral)
    VIDHAN_PARISHAD = "vidhan_parishad"  # Legislative Council (Upper House)
    UNKNOWN = "unknown"
```

### Extended Dataclass: `Bill`
Two new fields were added to `Bill` with safe defaults:
```python
    # Jurisdiction & State (Task 8.2)
    jurisdiction: BillJurisdiction = BillJurisdiction.CENTRAL
    state: Optional[str] = None
```

### Self-Coercing `__post_init__`
```python
    def __post_init__(self) -> None:
        """Coerce enum fields and normalise state name if needed."""
        from utils.state_normalizer import normalize_state  # noqa: PLC0415

        if isinstance(self.jurisdiction, str):
            try:
                self.jurisdiction = BillJurisdiction(self.jurisdiction.strip().lower())
            except ValueError:
                self.jurisdiction = BillJurisdiction.CENTRAL
        if isinstance(self.house, str):
            try:
                self.house = BillHouse(self.house.strip().lower())
            except ValueError:
                self.house = BillHouse.UNKNOWN
        if isinstance(self.status, str):
            try:
                self.status = BillStatus(self.status.strip().lower())
            except ValueError:
                pass
        if self.state:
            self.state = normalize_state(self.state) or self.state.strip()
```

---

## 4. Jurisdiction Model

The jurisdiction model enforces clean demarcation:
1. **Central Bills**:
   - `jurisdiction`: `BillJurisdiction.CENTRAL` (value: `"central"`).
   - `state`: strictly `None`.
   - Default for all legacy records and any instantiation where `jurisdiction` is omitted.
2. **State Bills**:
   - `jurisdiction`: `BillJurisdiction.STATE` (value: `"state"`).
   - `state`: Must contain canonical Indian state name (e.g., `"Karnataka"`, `"Maharashtra"`).

---

## 5. State Model & Normalization

A dedicated normalization utility was created at [`utils/state_normalizer.py`](file:///d:/Legislative-bill/utils/state_normalizer.py) and exported via [`utils/__init__.py`](file:///d:/Legislative-bill/utils/__init__.py).

### Capabilities
- **28 Canonical Indian States**:
  Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chhattisgarh, Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand, Karnataka, Kerala, Madhya Pradesh, Maharashtra, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Punjab, Rajasthan, Sikkim, Tamil Nadu, Telangana, Tripura, Uttar Pradesh, Uttarakhand, West Bengal.
- **8 Canonical Union Territories**:
  Andaman and Nicobar Islands, Chandigarh, Dadra and Nagar Haveli and Daman and Diu, Delhi, Jammu and Kashmir, Ladakh, Lakshadweep, Puducherry.
- **Affix Stripping**:
  Automatically removes prefixes (`"State of "`, `"Govt of "`, `"Government of "`, `"UT of "`) and suffixes (`" State"`, `" UT"`, `" Union Territory"`, `" Government"`).
  *Example:* `"Karnataka State"` $\rightarrow$ `"Karnataka"`.
- **Case-Insensitive Resolution**:
  *Example:* `"karnataka"` $\rightarrow$ `"Karnataka"`, `"TAMIL NADU"` $\rightarrow$ `"Tamil Nadu"`.
- **Alias & Abbreviation Mapping**:
  *Example:* `"KA"`, `"kar"`, `"bangalore"`, `"bengaluru"` $\rightarrow$ `"Karnataka"`.
  *Example:* `"MH"`, `"mah"`, `"mumbai"` $\rightarrow$ `"Maharashtra"`.
  *Example:* `"DL"`, `"del"`, `"new delhi"` $\rightarrow$ `"Delhi"`.
  *Example:* `"Orissa"` $\rightarrow$ `"Odisha"`, `"Pondicherry"` $\rightarrow$ `"Puducherry"`, `"Uttaranchal"` $\rightarrow$ `"Uttarakhand"`.
- **Helper Functions**:
  - `normalize_state(name: Optional[str]) -> Optional[str]`
  - `is_valid_state(name: str) -> bool`
  - `get_canonical_states() -> list[str]`
  - `get_canonical_uts() -> list[str]`
  - `get_all_states_and_uts() -> list[str]`

---

## 6. Legislature Model

Chamber support in [`BillHouse`](file:///d:/Legislative-bill/schemas/bill.py) now accommodates both unicameral and bicameral State legislatures:
- **`BillHouse.LOK_SABHA` (`"lok_sabha"`):** Central Lower House (House of the People).
- **`BillHouse.RAJYA_SABHA` (`"rajya_sabha"`):** Central Upper House (Council of States).
- **`BillHouse.VIDHAN_SABHA` (`"vidhan_sabha"`):** State Legislative Assembly (Lower House in bicameral states, sole house in unicameral states).
- **`BillHouse.VIDHAN_PARISHAD` (`"vidhan_parishad"`):** State Legislative Council (Upper House in bicameral states).
- **`BillHouse.UNKNOWN` (`"unknown"`):** Safe fallback when chamber is not specified.

The model does **not** make assumptions about which states are bicameral; the chamber for any future state bill will be derived strictly from authoritative source portal data.

---

## 7. Repository Changes

[`storage/bill_repository.py`](file:///d:/Legislative-bill/storage/bill_repository.py) was enhanced with two non-breaking query methods:

### `get_by_jurisdiction()`
```python
def get_by_jurisdiction(self, jurisdiction: str | BillJurisdiction) -> list[Bill]:
    """
    Return bills filtered by jurisdiction ('central' or 'state').
    Supports either string or BillJurisdiction enum.
    """
```
- `repo.get_by_jurisdiction(BillJurisdiction.CENTRAL)` returns all Central bills.
- `repo.get_by_jurisdiction(BillJurisdiction.STATE)` returns only State bills.

### `get_by_state()`
```python
def get_by_state(self, state: str) -> list[Bill]:
    """
    Return bills for a particular Indian state (case-insensitive, normalized).
    """
```
- Automatically normalizes the query parameter (e.g., query `"KA"`, `"karnataka"`, or `"Karnataka State"` all resolve to `"Karnataka"`).
- Compares against normalized `b.state`.
- Strictly ignores Central bills (where `state is None`).

All existing methods (`get()`, `get_all()`, `get_by_year()`, `get_by_ministry()`, `get_by_status()`, `get_by_sector()`, `save()`, `delete()`, `count()`) continue operating without alteration.

---

## 8. Serialization Behavior

### Serialization (`Bill.to_dict`)
Includes `"jurisdiction"` (string value) and `"state"` (string or `None`):
```json
{
  "bill_id": "karnataka-gig-workers-bill-2024",
  "title": "The Karnataka Platform-based Gig Workers Bill, 2024",
  "jurisdiction": "state",
  "state": "Karnataka",
  "house": "vidhan_sabha",
  "status": "introduced"
}
```

### Deserialization (`Bill.from_dict`)
- Missing `"jurisdiction"` key $\rightarrow$ defaults to `BillJurisdiction.CENTRAL`.
- Missing `"state"` key $\rightarrow$ defaults to `None`.
- String enum values $\rightarrow$ safely converted to corresponding Enum instances.

---

## 9. Backward Compatibility

Complete backward compatibility is preserved:
1. **Existing on-disk Central bills**: Deserialized directly without requiring any file migrations.
2. **Existing callers**: Any call `Bill(bill_id=..., title=..., house=..., status=..., url=...)` without jurisdiction or state succeeds and defaults to Central/None.
3. **Repository callers**: Existing calls to `get_all()`, `get()`, etc., return Central bills with `jurisdiction=BillJurisdiction.CENTRAL` and `state=None`.
4. **Serialization round-trip**: Legacy dict $\rightarrow$ `Bill.from_dict()` $\rightarrow$ `to_dict()` retains Central identity.

---

## 10. Tests Added

A comprehensive test suite was added in [`tests/test_state_bill_foundation.py`](file:///d:/Legislative-bill/tests/test_state_bill_foundation.py) containing **31 unit and integration tests**:

1. **Central Bill Backward Compatibility**:
   - `test_instantiation_without_jurisdiction_defaults_to_central`
   - `test_legacy_dict_deserialization`
   - `test_production_bills_deserialize_as_central`
2. **State Bill Schema Creation**:
   - `test_create_state_bill_explicit_enum`
   - `test_create_state_bill_string_coercion`
3. **Central `state=None` Behavior**:
   - `test_central_state_is_none`
   - `test_central_serialized_state_is_none`
   - `test_central_bill_repr_omits_state`
4. **State Normalization**:
   - `test_canonical_names_pass_through`
   - `test_case_insensitivity`
   - `test_administrative_affixes_removal`
   - `test_abbreviations_and_aliases`
   - `test_edge_cases`
   - `test_is_valid_state`
   - `test_canonical_lists`
5. **Vidhan Sabha Support**:
   - `test_enum_value`
   - `test_state_bill_vidhan_sabha_roundtrip`
6. **Vidhan Parishad Support**:
   - `test_enum_value`
   - `test_state_bill_vidhan_parishad_roundtrip`
7. **Repository Jurisdiction Filtering**:
   - `test_isolated_repository_jurisdiction_filter`
   - `test_production_repository_has_only_central_bills`
8. **Repository State Filtering**:
   - `test_isolated_repository_state_filter`
   - `test_production_repository_state_filter_returns_empty`
9. **Serialization / Deserialization**:
   - `test_central_bill_json_roundtrip`
   - `test_state_bill_json_roundtrip`
   - `test_state_bill_repr_contains_state`
10. **Existing Central Repository Behavior**:
    - `test_production_repo_get`
    - `test_production_repo_get_by_year`
    - `test_production_repo_get_by_status`
    - `test_production_repo_get_by_ministry`
    - `test_production_repo_count`

In addition, [`tests/test_schemas.py`](file:///d:/Legislative-bill/tests/test_schemas.py) was updated with 2 tests verifying `BillHouse` and `BillJurisdiction` enum values.

---

## 11. Regression Results

| Test Scope | Command | Passed | Failed | Status |
| :--- | :--- | :---: | :---: | :---: |
| State Bill Foundation | `pytest tests/test_state_bill_foundation.py` | **31** | **0** | **PASS** |
| Schema Suite | `pytest tests/test_schemas.py` | **20** | **0** | **PASS** |
| Backtest Scope Regression | `pytest tests/test_backtest_scope.py` | **26** | **0** | **PASS** |
| Dashboard Service Regression | `pytest tests/test_dashboard_service.py` | **30** | **0** | **PASS** |
| Full Regression Suite Baseline | `pytest` | **1,257** | **0** | **PASS** |

*(1,226 original baseline tests + 31 new tests = 1,257 passed, 0 failed).*

---

## 12. Production Artifact Integrity

Zero production data files were added or modified:
- `data/bills/metadata/*.json`: **0 files modified** (exactly 22 files: 20 production + 2 non-legislative).
- `data/predictions/`: **0 files modified** (4,700 prediction records intact).
- `data/decisions/`: **0 files modified** (4,700 decision records intact).
- `data/anticipation/`: **0 files modified** (940 anticipation records intact).
- `data/reporting/`: **0 files modified** (14,100 stakeholder reports intact).
- `data/models/`: **0 files modified**.
- `data/market/`: **0 files modified**.
- `data/companies/`: **0 files modified**.

---

## 13. Limitations

1. **Structural Support Only**: No actual State bills have been ingested or scraped.
2. **No Market Mapping**: Mapping of State bills to listed companies has not yet been implemented (reserved for future task).
3. **No Sector Intelligence Overlay**: State sector taxonomy and cross-jurisdiction linkages have not yet been introduced.
4. **No Model Inference**: Models have not been trained on or evaluated against State legislative bills.

---

## 14. Next Recommended State-Bill Task

**Task 8.3 — State Bill Source & Pilot Ingestion (Maharashtra / Karnataka)**
- Research and design connectors for state legislative assembly/council portals (e.g., Karnataka Legislative Assembly `kla.kar.nic.in`, Maharashtra Legislature `mls.org.in`).
- Implement pilot ingestion and text extraction pipelines for state bills.
- Validate state bill schema compliance and automated state normalization upon ingestion.
