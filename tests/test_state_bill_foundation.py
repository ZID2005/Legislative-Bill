"""
tests/test_state_bill_foundation.py
===================================
Unit and integration tests for Task 8.2 — State Bill Foundation & Jurisdiction Support.

Verifies:
1. Central bill backward compatibility (instantiation without jurisdiction/state).
2. State bill schema creation (explicit jurisdiction=STATE, state="Karnataka").
3. Central state=None behavior (default value and serialization).
4. State normalization (canonical naming, case variants, affixes, aliases, edge cases).
5. Vidhan Sabha support (enum, serialization, round-trip).
6. Vidhan Parishad support (enum, serialization, round-trip).
7. Repository jurisdiction filtering (get_by_jurisdiction on Central and State).
8. Repository state filtering (get_by_state with normalization and isolation from Central).
9. Serialization/deserialization round-trip (with and without new fields).
10. Existing Central repository behavior intact against production data.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from schemas.bill import Bill, BillHouse, BillJurisdiction, BillStatus
from storage.bill_repository import BillRepository
from utils.file_utils import ensure_dir, save_json
from utils.state_normalizer import (
    CANONICAL_INDIAN_STATES,
    CANONICAL_UNION_TERRITORIES,
    get_all_states_and_uts,
    get_canonical_states,
    get_canonical_uts,
    is_valid_state,
    normalize_state,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_central_bill() -> Bill:
    """Sample Central Government bill instantiated with legacy fields."""
    return Bill(
        bill_id="the-finance-bill-2024",
        title="The Finance Bill, 2024",
        year=2024,
        ministry="Ministry of Finance",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://prsindia.org/bills/the-finance-bill-2024",
        introduction_date=date(2024, 2, 1),
    )


@pytest.fixture
def sample_state_bill_assembly() -> Bill:
    """Sample State bill introduced in Vidhan Sabha (Legislative Assembly)."""
    return Bill(
        bill_id="karnataka-platform-based-gig-workers-bill-2024",
        title="The Karnataka Platform-based Gig Workers Bill, 2024",
        year=2024,
        ministry="Department of Labour",
        house=BillHouse.VIDHAN_SABHA,
        status=BillStatus.INTRODUCED,
        jurisdiction=BillJurisdiction.STATE,
        state="Karnataka",
        url="https://kla.kar.nic.in/bills/gig-workers-2024",
        introduction_date=date(2024, 7, 4),
    )


@pytest.fixture
def sample_state_bill_council() -> Bill:
    """Sample State bill introduced in Vidhan Parishad (Legislative Council)."""
    return Bill(
        bill_id="maharashtra-special-public-security-bill-2024",
        title="The Maharashtra Special Public Security Bill, 2024",
        year=2024,
        ministry="Home Department",
        house=BillHouse.VIDHAN_PARISHAD,
        status=BillStatus.INTRODUCED,
        jurisdiction=BillJurisdiction.STATE,
        state="Maharashtra",
        url="https://mls.org.in/bills/sps-2024",
        introduction_date=date(2024, 7, 11),
    )


@pytest.fixture
def isolated_bill_repo(tmp_path: Path) -> BillRepository:
    """Isolated BillRepository rooted in a temporary directory with test bills."""
    repo = BillRepository()
    repo._metadata_dir = tmp_path / "metadata"
    repo._pdfs_dir = tmp_path / "pdfs"
    ensure_dir(repo._metadata_dir)
    ensure_dir(repo._pdfs_dir)
    return repo


# ---------------------------------------------------------------------------
# 1. Central Bill Backward Compatibility
# ---------------------------------------------------------------------------


class TestCentralBillBackwardCompatibility:
    """Verify that existing Central bills remain 100% backward compatible."""

    def test_instantiation_without_jurisdiction_defaults_to_central(
        self, sample_central_bill: Bill
    ) -> None:
        """Instantiating a bill without jurisdiction or state defaults safely."""
        assert sample_central_bill.jurisdiction == BillJurisdiction.CENTRAL
        assert sample_central_bill.state is None

    def test_legacy_dict_deserialization(self) -> None:
        """A dictionary lacking 'jurisdiction' and 'state' deserializes to Central/None."""
        legacy_dict = {
            "bill_id": "legacy-central-bill",
            "title": "Legacy Central Bill",
            "year": 2023,
            "ministry": "Ministry of Power",
            "house": "lok_sabha",
            "status": "introduced",
            "url": "https://prsindia.org/bills/legacy",
        }
        bill = Bill.from_dict(legacy_dict)
        assert bill.bill_id == "legacy-central-bill"
        assert bill.jurisdiction == BillJurisdiction.CENTRAL
        assert bill.state is None

    def test_production_bills_deserialize_as_central(self) -> None:
        """Production bills loaded from repository default to CENTRAL with state=None."""
        repo = BillRepository()
        all_bills = repo.get_all()
        assert len(all_bills) >= 20, "Expected at least 20 production bills"
        for bill in all_bills:
            assert bill.jurisdiction == BillJurisdiction.CENTRAL
            assert bill.state is None


# ---------------------------------------------------------------------------
# 2. State Bill Schema Creation
# ---------------------------------------------------------------------------


class TestStateBillSchemaCreation:
    """Verify creation and attributes of State bills."""

    def test_create_state_bill_explicit_enum(
        self, sample_state_bill_assembly: Bill
    ) -> None:
        assert sample_state_bill_assembly.jurisdiction == BillJurisdiction.STATE
        assert sample_state_bill_assembly.state == "Karnataka"
        assert sample_state_bill_assembly.house == BillHouse.VIDHAN_SABHA
        assert sample_state_bill_assembly.status == BillStatus.INTRODUCED

    def test_create_state_bill_string_coercion(self) -> None:
        """String inputs for jurisdiction and house are coerced safely."""
        bill = Bill(
            bill_id="karnataka-test-bill",
            title="Karnataka Test Bill",
            house="vidhan_sabha",
            status="introduced",
            url="https://example.com/bill",
            jurisdiction="state",
            state="karnataka",
        )
        assert bill.jurisdiction == BillJurisdiction.STATE
        assert bill.house == BillHouse.VIDHAN_SABHA
        assert bill.state == "Karnataka"  # normalized


# ---------------------------------------------------------------------------
# 3. Central state=None Behavior
# ---------------------------------------------------------------------------


class TestCentralStateNoneBehavior:
    """Verify that Central bills strictly maintain state=None."""

    def test_central_state_is_none(self, sample_central_bill: Bill) -> None:
        assert sample_central_bill.state is None

    def test_central_serialized_state_is_none(self, sample_central_bill: Bill) -> None:
        d = sample_central_bill.to_dict()
        assert d["jurisdiction"] == "central"
        assert d["state"] is None

    def test_central_bill_repr_omits_state(self, sample_central_bill: Bill) -> None:
        rep = repr(sample_central_bill)
        assert "jurisdiction='central'" in rep
        assert "state=" not in rep


# ---------------------------------------------------------------------------
# 4. State Normalization
# ---------------------------------------------------------------------------


class TestStateNormalization:
    """Verify Indian State normalization mechanism."""

    def test_canonical_names_pass_through(self) -> None:
        assert normalize_state("Karnataka") == "Karnataka"
        assert normalize_state("Maharashtra") == "Maharashtra"
        assert normalize_state("Delhi") == "Delhi"

    def test_case_insensitivity(self) -> None:
        assert normalize_state("karnataka") == "Karnataka"
        assert normalize_state("KARNATAKA") == "Karnataka"
        assert normalize_state("maharashtra") == "Maharashtra"
        assert normalize_state("TAMIL NADU") == "Tamil Nadu"

    def test_administrative_affixes_removal(self) -> None:
        assert normalize_state("Karnataka State") == "Karnataka"
        assert normalize_state("State of Karnataka") == "Karnataka"
        assert normalize_state("Maharashtra Government") == "Maharashtra"
        assert normalize_state("Govt of Maharashtra") == "Maharashtra"
        assert normalize_state("UT of Delhi") == "Delhi"
        assert normalize_state("Delhi UT") == "Delhi"

    def test_abbreviations_and_aliases(self) -> None:
        assert normalize_state("KA") == "Karnataka"
        assert normalize_state("kar") == "Karnataka"
        assert normalize_state("bangalore") == "Karnataka"
        assert normalize_state("MH") == "Maharashtra"
        assert normalize_state("mah") == "Maharashtra"
        assert normalize_state("mumbai") == "Maharashtra"
        assert normalize_state("DL") == "Delhi"
        assert normalize_state("del") == "Delhi"
        assert normalize_state("TN") == "Tamil Nadu"
        assert normalize_state("WB") == "West Bengal"
        assert normalize_state("Orissa") == "Odisha"
        assert normalize_state("Pondicherry") == "Puducherry"
        assert normalize_state("Uttaranchal") == "Uttarakhand"

    def test_edge_cases(self) -> None:
        assert normalize_state(None) is None
        assert normalize_state("") is None
        assert normalize_state("   ") is None

    def test_is_valid_state(self) -> None:
        assert is_valid_state("Karnataka") is True
        assert is_valid_state("karnataka") is True
        assert is_valid_state("KA") is True
        assert is_valid_state("InvalidStateName123") is False

    def test_canonical_lists(self) -> None:
        states = get_canonical_states()
        assert len(states) == 28
        assert "Karnataka" in states
        assert "Maharashtra" in states

        uts = get_canonical_uts()
        assert len(uts) == 8
        assert "Delhi" in uts
        assert "Chandigarh" in uts

        all_regions = get_all_states_and_uts()
        assert len(all_regions) == 36


# ---------------------------------------------------------------------------
# 5. Vidhan Sabha Support
# ---------------------------------------------------------------------------


class TestVidhanSabhaSupport:
    """Verify Vidhan Sabha (Legislative Assembly) chamber support."""

    def test_enum_value(self) -> None:
        assert BillHouse.VIDHAN_SABHA.value == "vidhan_sabha"

    def test_state_bill_vidhan_sabha_roundtrip(
        self, sample_state_bill_assembly: Bill
    ) -> None:
        d = sample_state_bill_assembly.to_dict()
        assert d["house"] == "vidhan_sabha"
        restored = Bill.from_dict(d)
        assert restored.house == BillHouse.VIDHAN_SABHA


# ---------------------------------------------------------------------------
# 6. Vidhan Parishad Support
# ---------------------------------------------------------------------------


class TestVidhanParishadSupport:
    """Verify Vidhan Parishad (Legislative Council) chamber support."""

    def test_enum_value(self) -> None:
        assert BillHouse.VIDHAN_PARISHAD.value == "vidhan_parishad"

    def test_state_bill_vidhan_parishad_roundtrip(
        self, sample_state_bill_council: Bill
    ) -> None:
        d = sample_state_bill_council.to_dict()
        assert d["house"] == "vidhan_parishad"
        restored = Bill.from_dict(d)
        assert restored.house == BillHouse.VIDHAN_PARISHAD


# ---------------------------------------------------------------------------
# 7. Repository Jurisdiction Filtering
# ---------------------------------------------------------------------------


class TestRepositoryJurisdictionFiltering:
    """Verify repository jurisdiction filtering."""

    def test_isolated_repository_jurisdiction_filter(
        self,
        isolated_bill_repo: BillRepository,
        sample_central_bill: Bill,
        sample_state_bill_assembly: Bill,
        sample_state_bill_council: Bill,
    ) -> None:
        isolated_bill_repo.save(sample_central_bill)
        isolated_bill_repo.save(sample_state_bill_assembly)
        isolated_bill_repo.save(sample_state_bill_council)

        central_bills = isolated_bill_repo.get_by_jurisdiction(BillJurisdiction.CENTRAL)
        assert len(central_bills) == 1
        assert central_bills[0].bill_id == sample_central_bill.bill_id

        central_bills_str = isolated_bill_repo.get_by_jurisdiction("central")
        assert len(central_bills_str) == 1

        state_bills = isolated_bill_repo.get_by_jurisdiction(BillJurisdiction.STATE)
        assert len(state_bills) == 2
        state_ids = {b.bill_id for b in state_bills}
        assert sample_state_bill_assembly.bill_id in state_ids
        assert sample_state_bill_council.bill_id in state_ids

        state_bills_str = isolated_bill_repo.get_by_jurisdiction("state")
        assert len(state_bills_str) == 2

    def test_production_repository_has_only_central_bills(self) -> None:
        repo = BillRepository()
        central_bills = repo.get_by_jurisdiction(BillJurisdiction.CENTRAL)
        state_bills = repo.get_by_jurisdiction(BillJurisdiction.STATE)

        assert len(central_bills) >= 20
        assert len(state_bills) == 0, "No state bills should exist in production repo yet"


# ---------------------------------------------------------------------------
# 8. Repository State Filtering
# ---------------------------------------------------------------------------


class TestRepositoryStateFiltering:
    """Verify repository filtering by state."""

    def test_isolated_repository_state_filter(
        self,
        isolated_bill_repo: BillRepository,
        sample_central_bill: Bill,
        sample_state_bill_assembly: Bill,
        sample_state_bill_council: Bill,
    ) -> None:
        isolated_bill_repo.save(sample_central_bill)
        isolated_bill_repo.save(sample_state_bill_assembly)
        isolated_bill_repo.save(sample_state_bill_council)

        kar_bills = isolated_bill_repo.get_by_state("Karnataka")
        assert len(kar_bills) == 1
        assert kar_bills[0].bill_id == sample_state_bill_assembly.bill_id

        # Case and affix robustness
        kar_bills_lower = isolated_bill_repo.get_by_state("karnataka")
        assert len(kar_bills_lower) == 1

        kar_bills_affix = isolated_bill_repo.get_by_state("Karnataka State")
        assert len(kar_bills_affix) == 1

        kar_bills_code = isolated_bill_repo.get_by_state("KA")
        assert len(kar_bills_code) == 1

        mah_bills = isolated_bill_repo.get_by_state("Maharashtra")
        assert len(mah_bills) == 1
        assert mah_bills[0].bill_id == sample_state_bill_council.bill_id

        # Non-existent state returns empty list
        tn_bills = isolated_bill_repo.get_by_state("Tamil Nadu")
        assert len(tn_bills) == 0

    def test_production_repository_state_filter_returns_empty(self) -> None:
        repo = BillRepository()
        assert len(repo.get_by_state("Karnataka")) == 0
        assert len(repo.get_by_state("Maharashtra")) == 0


# ---------------------------------------------------------------------------
# 9. Serialization / Deserialization
# ---------------------------------------------------------------------------


class TestSerializationDeserialization:
    """Verify serialization and deserialization integrity."""

    def test_central_bill_json_roundtrip(self, sample_central_bill: Bill) -> None:
        d = sample_central_bill.to_dict()
        serialized = json.dumps(d)
        loaded_dict = json.loads(serialized)
        restored = Bill.from_dict(loaded_dict)

        assert restored.bill_id == sample_central_bill.bill_id
        assert restored.jurisdiction == BillJurisdiction.CENTRAL
        assert restored.state is None
        assert restored.house == BillHouse.LOK_SABHA

    def test_state_bill_json_roundtrip(
        self, sample_state_bill_assembly: Bill
    ) -> None:
        d = sample_state_bill_assembly.to_dict()
        assert d["jurisdiction"] == "state"
        assert d["state"] == "Karnataka"
        assert d["house"] == "vidhan_sabha"

        serialized = json.dumps(d)
        loaded_dict = json.loads(serialized)
        restored = Bill.from_dict(loaded_dict)

        assert restored.bill_id == sample_state_bill_assembly.bill_id
        assert restored.jurisdiction == BillJurisdiction.STATE
        assert restored.state == "Karnataka"
        assert restored.house == BillHouse.VIDHAN_SABHA

    def test_state_bill_repr_contains_state(
        self, sample_state_bill_assembly: Bill
    ) -> None:
        rep = repr(sample_state_bill_assembly)
        assert "jurisdiction='state'" in rep
        assert "state='Karnataka'" in rep


# ---------------------------------------------------------------------------
# 10. Existing Central Repository Behavior
# ---------------------------------------------------------------------------


class TestExistingCentralRepositoryBehavior:
    """Verify all existing Central query methods continue functioning unchanged."""

    def test_production_repo_get(self) -> None:
        repo = BillRepository()
        bill = repo.get("the-merchant-shipping-bill-2024")
        assert bill is not None
        assert bill.bill_id == "the-merchant-shipping-bill-2024"
        assert bill.jurisdiction == BillJurisdiction.CENTRAL
        assert bill.state is None
        assert bill.year == 2024

    def test_production_repo_get_by_year(self) -> None:
        repo = BillRepository()
        bills_2024 = repo.get_by_year(2024)
        assert len(bills_2024) > 0
        for b in bills_2024:
            assert b.year == 2024
            assert b.jurisdiction == BillJurisdiction.CENTRAL

    def test_production_repo_get_by_status(self) -> None:
        repo = BillRepository()
        passed_bills = repo.get_by_status("passed_both")
        assert len(passed_bills) > 0
        for b in passed_bills:
            assert b.status == BillStatus.PASSED_BOTH

    def test_production_repo_get_by_ministry(self) -> None:
        repo = BillRepository()
        shipping_bills = repo.get_by_ministry("Shipping")
        assert len(shipping_bills) > 0
        for b in shipping_bills:
            assert b.ministry.lower() == "shipping"

    def test_production_repo_count(self) -> None:
        repo = BillRepository()
        assert repo.count() >= 20
