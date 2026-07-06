"""
tests/test_catalog.py
=====================
Unit tests for the data catalog (storage.catalog).

Tests cover:
*  CatalogManager loads the real catalog JSON files correctly
*  DatasetEntry returns correct types and values
*  Staleness logic (is_stale, age_days)
*  update() writes and persists changes (using tmp_path fixture)
*  compute_md5() produces a valid hex digest
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# DatasetEntry tests
# ---------------------------------------------------------------------------

class TestDatasetEntry:
    """Tests for the DatasetEntry value object."""

    def _make_entry(self, **overrides) -> object:
        from storage.catalog import DatasetEntry
        data = {
            "dataset_id": "test_dataset",
            "description": "A test dataset",
            "source": "test_source",
            "record_count": 100,
            "is_complete": True,
            "last_ingested_at": None,
            "last_checked_at": None,
            "checksum_md5": None,
            **overrides,
        }
        return DatasetEntry(data)

    def test_dataset_id(self) -> None:
        entry = self._make_entry()
        assert entry.dataset_id == "test_dataset"

    def test_record_count(self) -> None:
        entry = self._make_entry(record_count=42)
        assert entry.record_count == 42

    def test_is_complete_true(self) -> None:
        entry = self._make_entry(is_complete=True)
        assert entry.is_complete is True

    def test_is_complete_false(self) -> None:
        entry = self._make_entry(is_complete=False)
        assert entry.is_complete is False

    def test_last_ingested_at_none(self) -> None:
        entry = self._make_entry(last_ingested_at=None)
        assert entry.last_ingested_at is None

    def test_last_ingested_at_parsed(self) -> None:
        ts = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        entry = self._make_entry(last_ingested_at=ts.isoformat())
        assert entry.last_ingested_at is not None
        assert entry.last_ingested_at.year == 2024

    def test_age_days_none_when_never_ingested(self) -> None:
        entry = self._make_entry(last_ingested_at=None)
        assert entry.age_days() is None

    def test_age_days_recent(self) -> None:
        recent = (datetime.now(tz=timezone.utc) - timedelta(hours=2)).isoformat()
        entry = self._make_entry(last_ingested_at=recent)
        age = entry.age_days()
        assert age is not None
        assert age < 1.0

    def test_is_stale_never_ingested(self) -> None:
        entry = self._make_entry(last_ingested_at=None)
        assert entry.is_stale(max_age_days=7) is True

    def test_is_stale_old_data(self) -> None:
        old = (datetime.now(tz=timezone.utc) - timedelta(days=30)).isoformat()
        entry = self._make_entry(last_ingested_at=old)
        assert entry.is_stale(max_age_days=7) is True

    def test_is_not_stale_recent_data(self) -> None:
        recent = (datetime.now(tz=timezone.utc) - timedelta(hours=3)).isoformat()
        entry = self._make_entry(last_ingested_at=recent)
        assert entry.is_stale(max_age_days=7) is False

    def test_to_dict_returns_copy(self) -> None:
        entry = self._make_entry()
        d = entry.to_dict()
        assert isinstance(d, dict)
        assert d["dataset_id"] == "test_dataset"

    def test_repr_contains_id(self) -> None:
        entry = self._make_entry()
        assert "test_dataset" in repr(entry)


# ---------------------------------------------------------------------------
# CatalogManager tests — using real catalog files
# ---------------------------------------------------------------------------

class TestCatalogManagerRealFiles:
    """Tests using the actual catalog JSON files in data/catalog/."""

    def test_bills_catalog_loads(self) -> None:
        from storage.catalog import CatalogManager
        cm = CatalogManager("bills")
        assert cm is not None
        assert len(cm.list_ids()) > 0

    def test_companies_catalog_loads(self) -> None:
        from storage.catalog import CatalogManager
        cm = CatalogManager("companies")
        assert len(cm.list_ids()) > 0

    def test_market_catalog_loads(self) -> None:
        from storage.catalog import CatalogManager
        cm = CatalogManager("market")
        assert len(cm.list_ids()) > 0

    def test_bills_catalog_has_prs_entry(self) -> None:
        from storage.catalog import CatalogManager
        cm = CatalogManager("bills")
        entry = cm.get("bills_prs")
        assert entry is not None
        assert entry.dataset_id == "bills_prs"

    def test_company_master_unified_exists(self) -> None:
        from storage.catalog import CatalogManager
        cm = CatalogManager("companies")
        entry = cm.get("company_master_unified")
        assert entry is not None

    def test_nifty50_entry_exists(self) -> None:
        from storage.catalog import CatalogManager
        cm = CatalogManager("market")
        entry = cm.get("prices_nifty50")
        assert entry is not None

    def test_fresh_catalog_is_stale(self) -> None:
        """All entries in a fresh catalog have never been ingested → stale."""
        from storage.catalog import CatalogManager
        cm = CatalogManager("bills")
        # bills_prs has never been ingested (record_count=0, last_ingested_at=null)
        assert cm.is_stale("bills_prs") is True

    def test_invalid_dataset_id_returns_none(self) -> None:
        from storage.catalog import CatalogManager
        cm = CatalogManager("bills")
        assert cm.get("nonexistent_dataset_xyz") is None

    def test_invalid_group_raises(self) -> None:
        from storage.catalog import CatalogManager
        with pytest.raises(ValueError, match="Unknown catalog group"):
            CatalogManager("nonexistent_group")

    def test_repr_contains_group(self) -> None:
        from storage.catalog import CatalogManager
        cm = CatalogManager("bills")
        assert "bills" in repr(cm)


# ---------------------------------------------------------------------------
# CatalogManager tests — using tmp_path (isolated, no side effects)
# ---------------------------------------------------------------------------

class TestCatalogManagerUpdate:
    """Tests for update() using a temporary catalog directory."""

    def _make_temp_catalog(self, tmp_path: Path, group: str = "bills") -> object:
        """Create a minimal catalog JSON in tmp_path and return a CatalogManager for it."""
        from storage.catalog import CatalogManager, _GROUP_FILENAME
        filename_prefix = _GROUP_FILENAME[group]
        catalog_file = tmp_path / f"{filename_prefix}_catalog.json"
        catalog_data = {
            "catalog_version": "1.0",
            "dataset_group": group,
            "last_updated": None,
            "datasets": {
                "test_ds": {
                    "dataset_id": "test_ds",
                    "description": "Test dataset",
                    "source": "test",
                    "record_count": 0,
                    "is_complete": False,
                    "last_ingested_at": None,
                    "last_checked_at": None,
                    "checksum_md5": None,
                }
            },
        }
        catalog_file.write_text(json.dumps(catalog_data, indent=2), encoding="utf-8")
        return CatalogManager(group, catalog_dir=tmp_path)

    def test_update_record_count(self, tmp_path: Path) -> None:
        cm = self._make_temp_catalog(tmp_path)
        cm.update("test_ds", record_count=500)
        entry = cm.get("test_ds")
        assert entry.record_count == 500

    def test_update_sets_last_ingested_at(self, tmp_path: Path) -> None:
        cm = self._make_temp_catalog(tmp_path)
        cm.update("test_ds", record_count=1)
        entry = cm.get("test_ds")
        assert entry.last_ingested_at is not None

    def test_update_is_complete(self, tmp_path: Path) -> None:
        cm = self._make_temp_catalog(tmp_path)
        cm.update("test_ds", is_complete=True)
        assert cm.is_complete("test_ds") is True

    def test_update_persists_to_disk(self, tmp_path: Path) -> None:
        """Changes must survive a fresh CatalogManager load."""
        from storage.catalog import _GROUP_FILENAME
        cm = self._make_temp_catalog(tmp_path)
        cm.update("test_ds", record_count=999, is_complete=True)

        catalog_file = tmp_path / f"{_GROUP_FILENAME['bills']}_catalog.json"
        raw = json.loads(catalog_file.read_text())
        assert raw["datasets"]["test_ds"]["record_count"] == 999
        assert raw["datasets"]["test_ds"]["is_complete"] is True

    def test_update_not_stale_after_update(self, tmp_path: Path) -> None:
        cm = self._make_temp_catalog(tmp_path)
        assert cm.is_stale("test_ds") is True  # never ingested
        cm.update("test_ds", record_count=10)
        assert cm.is_stale("test_ds", max_age_days=1) is False

    def test_update_unknown_dataset_raises(self, tmp_path: Path) -> None:
        cm = self._make_temp_catalog(tmp_path)
        with pytest.raises(KeyError):
            cm.update("nonexistent_ds", record_count=1)

    def test_update_checksum(self, tmp_path: Path) -> None:
        cm = self._make_temp_catalog(tmp_path)
        cm.update("test_ds", checksum_md5="d41d8cd98f00b204e9800998ecf8427e")
        entry = cm.get("test_ds")
        assert entry.checksum_md5 == "d41d8cd98f00b204e9800998ecf8427e"

    def test_touch_updates_checked_at(self, tmp_path: Path) -> None:
        from storage.catalog import _GROUP_FILENAME
        cm = self._make_temp_catalog(tmp_path)
        cm.touch("test_ds")
        catalog_file = tmp_path / f"{_GROUP_FILENAME['bills']}_catalog.json"
        raw = json.loads(catalog_file.read_text())
        assert raw["datasets"]["test_ds"]["last_checked_at"] is not None


# ---------------------------------------------------------------------------
# compute_md5 tests
# ---------------------------------------------------------------------------

class TestComputeMd5:
    """Tests for the compute_md5 helper."""

    def test_md5_empty_file(self, tmp_path: Path) -> None:
        from storage.catalog import compute_md5
        f = tmp_path / "empty.bin"
        f.write_bytes(b"")
        digest = compute_md5(f)
        assert digest == "d41d8cd98f00b204e9800998ecf8427e"  # known MD5 of empty file

    def test_md5_known_content(self, tmp_path: Path) -> None:
        from storage.catalog import compute_md5
        f = tmp_path / "test.txt"
        f.write_bytes(b"hello world")
        digest = compute_md5(f)
        # Known MD5 of "hello world"
        assert digest == "5eb63bbbe01eeed093cb22bb8f5acdc3"

    def test_md5_returns_32_char_hex(self, tmp_path: Path) -> None:
        from storage.catalog import compute_md5
        f = tmp_path / "data.bin"
        f.write_bytes(b"some test data for md5")
        digest = compute_md5(f)
        assert len(digest) == 32
        assert all(c in "0123456789abcdef" for c in digest)
