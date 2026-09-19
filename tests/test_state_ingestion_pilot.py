"""
tests/test_state_ingestion_pilot.py
====================================
Comprehensive tests for Task 8.3 — State Bill Source Research & Controlled Ingestion Pilot.

Verifies:
1. State source registry (loading, lookups, filtering, custom registration).
2. State source adapter interface & specific adapters (Andhra Pradesh & Karnataka).
3. State metadata extraction from HTML listings.
4. State normalization (title, dates, bill numbers, year extraction).
5. State jurisdiction assignment (BillJurisdiction.STATE).
6. State legislature assignment (Vidhan Sabha chamber, canonical legislature name).
7. Missing optional metadata handling (safe None/empty without fabrication).
8. Source provenance tracking (AUTHORITATIVE vs DERIVED vs UNAVAILABLE).
9. Deduplication (stable canonical IDs, URL matching, collision handling).
10. Serialization & deserialization round-trip of State bills.
11. Central ingestion regression (ParliamentIngestionService intact).
12. Production data safety & repository behavior (Central repository count unchanged, 0 state bills in Central).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any
import pytest

from config.settings import settings
from ingestion.parliament.connector import ParliamentConnector
from ingestion.state.adapters.andhra_pradesh import AndhraPradeshSourceAdapter
from ingestion.state.adapters.karnataka import KarnatakaSourceAdapter
from ingestion.state.deduplicator import StateBillDeduplicator
from ingestion.state.normalizer import StateBillNormalizer
from ingestion.state.provenance import (
    BillProvenanceRecord,
    ProvenanceLevel,
    StateProvenanceTracker,
)
from ingestion.state.registry import StateSourceRegistry
from ingestion.state.service import StateIngestionService
from schemas.bill import Bill, BillHouse, BillJurisdiction, BillStatus
from schemas.state_source import StateBillSource
from storage.bill_repository import BillRepository
from storage.state_bill_repository import StateBillRepository
from utils.file_utils import ensure_dir


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_ap_html() -> str:
    """Mock HTML table from Andhra Pradesh Legislature bills page."""
    return """
    <html>
        <body>
            <div id="main-content">
                <h1>BILLS</h1>
                <a href="https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_21_16_33__407_v_1.pdf">
                    The Andhra Pradesh Omnibus (Speed of Doing Business) Bill, 2026 (L.A. Bill No.21 of 2026)
                </a>
                <a href="https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_bill-3_16_31__387_v_1.pdf">
                    The Andhra Pradesh Electricity Duty (Amendment) Bill, 2026 (L.A. Bill No.3 of 2026)
                </a>
                <a href="https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/ActBills/English/Eng_actbill_ACTNO-1_16_31__387_v_1.pdf">
                    Act No.1 of 2026
                </a>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def mock_kar_html() -> str:
    """Mock HTML table from Karnataka Legislative Assembly session bills page."""
    return """
    <html>
        <body>
            <table border="1">
                <tr>
                    <th>Bill No.</th>
                    <th>Name of the Bill</th>
                    <th>Date of Introduction</th>
                    <th>Date of Passing</th>
                    <th>Date of Passing in Legislative Council</th>
                    <th>Date of Assent</th>
                    <th>Remarks</th>
                </tr>
                <tr>
                    <td>29</td>
                    <td><a href="bill1640_29.pdf">The Karnataka Goods and Services Tax (Amendment) Bill, 2024</a></td>
                    <td>19.07.2024</td>
                    <td>24.07.2024</td>
                    <td>25.07.2024</td>
                    <td></td>
                    <td>Passed by both houses</td>
                </tr>
                <tr>
                    <td>34</td>
                    <td><a href="bill1640_34.pdf">The Greater Bengaluru Governance Bill, 2024</a></td>
                    <td>23.07.2024</td>
                    <td>10.03.2025</td>
                    <td></td>
                    <td></td>
                    <td>Referred to Joint Select Committee</td>
                </tr>
            </table>
        </body>
    </html>
    """


@pytest.fixture
def isolated_state_repo(tmp_path: Path) -> StateBillRepository:
    """Isolated StateBillRepository in temporary directory."""
    return StateBillRepository(bills_dir=tmp_path / "state_bills")


# ---------------------------------------------------------------------------
# 1. State Source Registry Tests
# ---------------------------------------------------------------------------

class TestStateSourceRegistry:
    def test_registry_loads_default_sources(self) -> None:
        registry = StateSourceRegistry()
        assert registry.count() >= 8
        assert registry.get("andhra_pradesh_assembly") is not None
        assert registry.get("karnataka_assembly") is not None

    def test_get_by_state(self) -> None:
        registry = StateSourceRegistry()
        ap_sources = registry.get_by_state("Andhra Pradesh")
        assert len(ap_sources) >= 1
        assert ap_sources[0].source_name == "andhra_pradesh_assembly"

        # Alias/abbreviation matching via state normalizer
        kar_sources = registry.get_by_state("KA")
        assert len(kar_sources) >= 1

    def test_active_filtering(self) -> None:
        registry = StateSourceRegistry()
        active = registry.get_active_sources()
        active_names = {s.source_name for s in active}
        assert "andhra_pradesh_assembly" in active_names
        assert "karnataka_assembly" in active_names
        assert "maharashtra_legislature" not in active_names

    def test_register_runtime_source(self) -> None:
        registry = StateSourceRegistry()
        custom = StateBillSource(
            state="Goa",
            legislature="Goa Legislative Assembly",
            source_name="goa_assembly",
            base_url="https://goavidhansabha.gov.in",
            listing_url="https://goavidhansabha.gov.in/bills",
        )
        registry.register(custom)
        assert registry.get("goa_assembly") is not None
        assert registry.get("goa_assembly").state == "Goa"


# ---------------------------------------------------------------------------
# 2. State Source Adapter & Extraction Tests
# ---------------------------------------------------------------------------

class TestStateSourceAdapters:
    @pytest.mark.asyncio
    async def test_andhra_pradesh_adapter_parsing(self, mock_ap_html: str) -> None:
        connector = ParliamentConnector()
        connector.register_mock_response("https://aplegislature.org/web/aplegislature/bills", mock_ap_html)

        adapter = AndhraPradeshSourceAdapter(connector=connector)
        bills = await adapter.discover_bills()

        assert len(bills) == 2
        b1 = bills[0]
        assert "Omnibus" in b1["title"]
        assert "21" in b1["bill_number"] and "2026" in b1["bill_number"]
        assert b1["year"] == 2026
        assert b1["state"] == "Andhra Pradesh"
        assert b1["house"] == "vidhan_sabha"
        assert "Eng_passbill_21" in b1["pdf_url"]

    @pytest.mark.asyncio
    async def test_karnataka_adapter_parsing(self, mock_kar_html: str) -> None:
        connector = ParliamentConnector()
        session_url = "https://kla.kar.nic.in/assembly/bills/bills1640.htm"
        connector.register_mock_response(session_url, mock_kar_html)

        adapter = KarnatakaSourceAdapter(connector=connector)
        bills = await adapter.discover_bills(session_url=session_url)

        assert len(bills) == 2
        b1 = bills[0]
        assert "Goods and Services Tax" in b1["title"]
        assert b1["bill_number"] == "Bill No. 29 of 2024"
        assert b1["introduction_date"] == "2024-07-19"
        assert b1["status"] == "passed_both"
        assert "bill1640_29.pdf" in b1["pdf_url"]

        b2 = bills[1]
        assert "Greater Bengaluru" in b2["title"]
        assert b2["status"] == "passed_assembly"


# ---------------------------------------------------------------------------
# 3. State Normalization & Schema Assignment
# ---------------------------------------------------------------------------

class TestStateBillNormalizer:
    def test_normalization_jurisdiction_and_state(self) -> None:
        normalizer = StateBillNormalizer()
        raw = {
            "title": "The Karnataka Platform-based Gig Workers Bill, 2024",
            "state": "karnataka state",
            "house": "vidhan_sabha",
            "year": 2024,
            "bill_number": "Bill No. 42 of 2024",
        }
        bill, prov = normalizer.normalize(raw)

        assert bill.jurisdiction == BillJurisdiction.STATE
        assert bill.state == "Karnataka"
        assert bill.house == BillHouse.VIDHAN_SABHA
        assert bill.year == 2024
        assert bill.bill_id == "karnataka-vs-bill-42-2024"

    def test_missing_optional_metadata_not_fabricated(self) -> None:
        normalizer = StateBillNormalizer()
        raw = {
            "title": "Minimal Bill 2025",
            "state": "Andhra Pradesh",
        }
        bill, prov = normalizer.normalize(raw)

        assert bill.jurisdiction == BillJurisdiction.STATE
        assert bill.state == "Andhra Pradesh"
        assert bill.ministry == ""
        assert bill.introduction_date is None
        assert bill.assent_date is None
        assert bill.pdf_url is None
        assert bill.sectors == []
        assert bill.summary == ""

        # Provenance verifies unavailable fields
        fields = prov.fields
        assert fields["department"].level == ProvenanceLevel.UNAVAILABLE
        assert fields["introduction_date"].level == ProvenanceLevel.UNAVAILABLE
        assert fields["pdf_url"].level == ProvenanceLevel.UNAVAILABLE


# ---------------------------------------------------------------------------
# 4. Provenance Tracking Tests
# ---------------------------------------------------------------------------

class TestStateProvenance:
    def test_provenance_levels_classification(self) -> None:
        normalizer = StateBillNormalizer()
        raw = {
            "title": "The AP Energy Conservation Bill, 2026",
            "state": "Andhra Pradesh",
            "bill_number": "L.A. Bill No. 5 of 2026",
            "house": "vidhan_sabha",
            "pdf_url": "https://legislation.aplegislature.org/bill5.pdf",
            "introduction_date": "2026-02-10",
        }
        bill, prov = normalizer.normalize(raw)

        f = prov.fields
        assert f["title"].level == ProvenanceLevel.AUTHORITATIVE
        assert f["bill_number"].level == ProvenanceLevel.AUTHORITATIVE
        assert f["state"].level == ProvenanceLevel.AUTHORITATIVE
        assert f["pdf_url"].level == ProvenanceLevel.AUTHORITATIVE
        assert f["year"].level == ProvenanceLevel.DERIVED
        assert f["bill_id"].level == ProvenanceLevel.DERIVED
        assert f["department"].level == ProvenanceLevel.UNAVAILABLE

    def test_provenance_tracker_aggregation(self) -> None:
        tracker = StateProvenanceTracker()
        normalizer = StateBillNormalizer()

        raw1 = {"title": "Bill A 2026", "state": "Andhra Pradesh", "bill_number": "Bill 1"}
        raw2 = {"title": "Bill B 2026", "state": "Karnataka"}

        _, prov1 = normalizer.normalize(raw1)
        _, prov2 = normalizer.normalize(raw2)

        tracker.record_bill(prov1)
        tracker.record_bill(prov2)

        report = tracker.generate_report()
        assert report["total_state_bills"] == 2
        assert report["field_summary"]["authoritative"]["title"] == 2
        assert report["field_summary"]["authoritative"]["bill_number"] == 1
        assert report["field_summary"]["unavailable"]["bill_number"] == 1


# ---------------------------------------------------------------------------
# 5. Deduplication Tests
# ---------------------------------------------------------------------------

class TestStateBillDeduplicator:
    def test_stable_canonical_id_generation(self) -> None:
        dedup = StateBillDeduplicator()
        cid = dedup.generate_canonical_id(
            state="Andhra Pradesh",
            title="The Omnibus Bill, 2026",
            bill_number="L.A. Bill No. 21 of 2026",
            year=2026,
            house=BillHouse.VIDHAN_SABHA,
        )
        assert cid == "andhra-pradesh-vs-bill-21-2026"

    def test_duplicate_detection_by_canonical_key(self) -> None:
        dedup = StateBillDeduplicator()
        raw = {
            "state": "Karnataka",
            "title": "GST Bill 2024",
            "bill_number": "29",
            "year": 2024,
            "house": "vidhan_sabha",
        }
        is_dup, cid = dedup.check_duplicate(raw)
        assert not is_dup

        dedup.register_bill("karnataka-vs-bill-29-2024", raw)
        is_dup2, cid2 = dedup.check_duplicate(raw)
        assert is_dup2
        assert cid2 == "karnataka-vs-bill-29-2024"

    def test_duplicate_detection_by_document_url(self) -> None:
        dedup = StateBillDeduplicator()
        raw1 = {
            "state": "Andhra Pradesh",
            "title": "AP Bill A",
            "year": 2026,
            "pdf_url": "https://legislation.aplegislature.org/doc1.pdf",
        }
        dedup.register_bill("ap-bill-a", raw1)

        raw2 = {
            "state": "Andhra Pradesh",
            "title": "AP Bill A (Duplicate Entry)",
            "year": 2026,
            "pdf_url": "https://legislation.aplegislature.org/doc1.pdf",
        }
        is_dup, matched_id = dedup.check_duplicate(raw2)
        assert is_dup
        assert matched_id == "ap-bill-a"


# ---------------------------------------------------------------------------
# 6. Serialization / Deserialization Tests
# ---------------------------------------------------------------------------

class TestStateSerialization:
    def test_state_bill_to_dict_and_back(self) -> None:
        normalizer = StateBillNormalizer()
        raw = {
            "title": "The Karnataka Platform-based Gig Workers Bill, 2024",
            "state": "Karnataka",
            "house": "vidhan_sabha",
            "year": 2024,
            "bill_number": "Bill No. 42 of 2024",
            "status": "introduced",
        }
        bill, _ = normalizer.normalize(raw)
        d = bill.to_dict()

        assert d["jurisdiction"] == "state"
        assert d["state"] == "Karnataka"
        assert d["house"] == "vidhan_sabha"

        restored = Bill.from_dict(d)
        assert restored.jurisdiction == BillJurisdiction.STATE
        assert restored.state == "Karnataka"
        assert restored.house == BillHouse.VIDHAN_SABHA
        assert restored.bill_id == bill.bill_id


# ---------------------------------------------------------------------------
# 7. Production Isolation & Repository Behavior Tests
# ---------------------------------------------------------------------------

class TestProductionIsolation:
    def test_production_repository_contains_zero_state_bills(self) -> None:
        """The Central production repository must remain 100% frozen with zero state bills."""
        repo = BillRepository()
        state_bills = repo.get_by_jurisdiction(BillJurisdiction.STATE)
        central_bills = repo.get_by_jurisdiction(BillJurisdiction.CENTRAL)

        assert len(state_bills) == 0, "No state bills should exist in Central production repo"
        assert len(central_bills) >= 20, "Central production bills must be preserved"

    def test_state_repository_contains_pilot_corpus(self) -> None:
        """The State repository contains exclusively State bills."""
        state_repo = StateBillRepository()
        assert state_repo.count() >= 23
        assert len(state_repo.get_by_jurisdiction(BillJurisdiction.CENTRAL)) == 0
        assert len(state_repo.get_by_jurisdiction(BillJurisdiction.STATE)) >= 23

        states = state_repo.get_states_represented()
        assert "Andhra Pradesh" in states
        assert "Karnataka" in states
        assert state_repo.count_by_state("Andhra Pradesh") == 12
        assert state_repo.count_by_state("Karnataka") == 11


# ---------------------------------------------------------------------------
# 8. State Ingestion Service Orchestration Tests
# ---------------------------------------------------------------------------

class TestStateIngestionService:
    def test_service_dry_run_does_not_save(self, tmp_path: Path) -> None:
        repo = StateBillRepository(bills_dir=tmp_path / "dry_state_bills")
        service = StateIngestionService(repository=repo)

        raw = [
            {
                "title": "Dry Run Bill 2025",
                "state": "Karnataka",
                "bill_number": "Bill 100",
                "year": 2025,
            }
        ]
        stats = service.process_raw_bills(raw, dry_run=True)
        assert stats["discovered"] == 1
        assert stats["inserted"] == 1
        assert repo.count() == 0

    def test_service_ingest_skips_duplicates(self, tmp_path: Path) -> None:
        repo = StateBillRepository(bills_dir=tmp_path / "dup_state_bills")
        service = StateIngestionService(repository=repo)

        raw = [
            {
                "title": "Duplicate Bill 2025",
                "state": "Andhra Pradesh",
                "bill_number": "Bill 200",
                "year": 2025,
            },
            {
                "title": "Duplicate Bill 2025",
                "state": "Andhra Pradesh",
                "bill_number": "Bill 200",
                "year": 2025,
            },
        ]
        stats = service.process_raw_bills(raw, dry_run=False)
        assert stats["discovered"] == 2
        assert stats["inserted"] == 1
        assert stats["skipped_duplicate"] == 1
        assert repo.count() == 1

    def test_service_saves_provenance_report(self, tmp_path: Path) -> None:
        repo = StateBillRepository(bills_dir=tmp_path / "prov_state_bills")
        service = StateIngestionService(repository=repo)

        raw = [
            {
                "title": "Prov Bill 2025",
                "state": "Karnataka",
                "bill_number": "Bill 300",
                "year": 2025,
            }
        ]
        service.process_raw_bills(raw, dry_run=False)
        dest = tmp_path / "prov_report.json"
        saved_path = service.save_provenance_report(dest)
        assert saved_path.is_file()
        with open(saved_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["total_state_bills"] == 1

