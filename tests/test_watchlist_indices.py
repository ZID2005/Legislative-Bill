"""
tests/test_watchlist_indices.py
================================
Dedicated unit tests for WatchlistIndexService and inverted indices.

Tests:
 1. Initialize empty index directory and files
 2. Add subscriber updates correct index map
 3. Multiple subscribers for single entity (different users/tenants)
 4. Duplicate subscriber ignored in same bucket
 5. Persistence format and schema validation of index files
 6. Remove subscriber by item_id
 7. Deactivate watchlist purges entries across all indices
 8. Rebuild indices from scratch from WatchlistRepository
 9. Rebuild idempotency and deterministic key order
 10. Integrity validation: detect orphaned items
 11. Integrity validation: detect missing items
 12. Integrity validation: detect inactive watchlist subscribers
 13. O(1) resolution across all 6 entity types
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from schemas.watchlist import Watchlist, WatchlistItem, WatchlistEntityType
from services.watchlist_index_service import (
    IndexValidationReport,
    WatchlistIndexService,
    WatchlistSubscriber,
)
from storage.watchlist_repository import WatchlistRepository


@pytest.fixture
def index_env(tmp_path: Path):
    w_repo = WatchlistRepository(root_dir=tmp_path / "watchlists")
    idx_dir = tmp_path / "indices"
    idx_svc = WatchlistIndexService(indices_dir=idx_dir, watchlist_repo=w_repo)
    return idx_svc, w_repo, idx_dir


class TestWatchlistIndexDeep:
    def test_1_init_empty_indices(self, index_env):
        idx_svc, _, idx_dir = index_env
        assert idx_dir.is_dir()
        for etype in WatchlistEntityType:
            assert etype in idx_svc._type_to_map
            assert len(idx_svc._type_to_map[etype]) == 0

    def test_2_add_and_query_subscriber(self, index_env):
        idx_svc, _, _ = index_env
        item = WatchlistItem(
            item_id="item_01",
            watchlist_id="wl_01",
            user_id="user_1",
            tenant_id="tenant_a",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
            display_name="Zomato Limited",
        )
        sub = idx_svc.add_subscriber(item)
        assert sub.item_id == "item_01"
        assert sub.entity_id == "INE758T01015"

        subs = idx_svc.get_subscribers_for_company("INE758T01015")
        assert len(subs) == 1
        assert subs[0].user_id == "user_1"

    def test_3_multiple_subscribers_for_entity(self, index_env):
        idx_svc, _, _ = index_env
        i1 = WatchlistItem(
            item_id="item_1",
            watchlist_id="wl_1",
            user_id="user_1",
            tenant_id="tenant_a",
            entity_type=WatchlistEntityType.STATE,
            entity_id="Kerala",
        )
        i2 = WatchlistItem(
            item_id="item_2",
            watchlist_id="wl_2",
            user_id="user_2",
            tenant_id="tenant_b",
            entity_type=WatchlistEntityType.STATE,
            entity_id="Kerala",
        )
        idx_svc.add_subscriber(i1)
        idx_svc.add_subscriber(i2)

        subs = idx_svc.get_subscribers_for_state("Kerala")
        assert len(subs) == 2
        user_ids = {s.user_id for s in subs}
        assert user_ids == {"user_1", "user_2"}

    def test_4_duplicate_item_prevented_in_bucket(self, index_env):
        idx_svc, _, _ = index_env
        item = WatchlistItem(
            item_id="item_dup",
            watchlist_id="wl_dup",
            user_id="user_1",
            tenant_id="tenant_a",
            entity_type=WatchlistEntityType.SECTOR,
            entity_id="Technology",
        )
        idx_svc.add_subscriber(item)
        idx_svc.add_subscriber(item)  # Call again

        subs = idx_svc.get_subscribers_for_sector("Technology")
        assert len(subs) == 1

    def test_5_persistence_json_structure(self, index_env):
        idx_svc, _, idx_dir = index_env
        item = WatchlistItem(
            item_id="item_json",
            watchlist_id="wl_json",
            user_id="u_json",
            tenant_id="t_json",
            entity_type=WatchlistEntityType.BILL,
            entity_id="the-coastal-shipping-bill-2024",
        )
        idx_svc.add_subscriber(item)

        path = idx_dir / "bill_index.json"
        assert path.is_file()

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["_version"] == "1.0"
        assert data["entity_type"] == "BILL"
        assert data["entry_count"] == 1
        assert "the-coastal-shipping-bill-2024" in data["entries"]
        sub_record = data["entries"]["the-coastal-shipping-bill-2024"][0]
        assert sub_record["item_id"] == "item_json"
        assert sub_record["user_id"] == "u_json"

    def test_6_remove_subscriber(self, index_env):
        idx_svc, _, _ = index_env
        item = WatchlistItem(
            item_id="item_rem",
            watchlist_id="wl_rem",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.INDUSTRY,
            entity_id="Food Delivery & Quick Commerce",
        )
        idx_svc.add_subscriber(item)
        assert len(idx_svc.get_subscribers_for_industry("Food Delivery & Quick Commerce")) == 1

        removed = idx_svc.remove_subscriber("item_rem", WatchlistEntityType.INDUSTRY, "Food Delivery & Quick Commerce")
        assert removed is True
        assert len(idx_svc.get_subscribers_for_industry("Food Delivery & Quick Commerce")) == 0

    def test_7_deactivate_watchlist_purges_across_types(self, index_env):
        idx_svc, _, _ = index_env
        i1 = WatchlistItem(
            item_id="i1",
            watchlist_id="wl_kill",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
        )
        i2 = WatchlistItem(
            item_id="i2",
            watchlist_id="wl_kill",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.STATE,
            entity_id="Kerala",
        )
        idx_svc.add_subscriber(i1)
        idx_svc.add_subscriber(i2)

        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 1
        assert len(idx_svc.get_subscribers_for_state("Kerala")) == 1

        purged_count = idx_svc.deactivate_watchlist("wl_kill")
        assert purged_count == 2

        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 0
        assert len(idx_svc.get_subscribers_for_state("Kerala")) == 0

    def test_8_rebuild_from_canonical_repo(self, index_env):
        idx_svc, w_repo, _ = index_env
        wl1 = w_repo.create(Watchlist(watchlist_id="w_active", user_id="u1", tenant_id="t1", is_active=True))
        wl_dead = w_repo.create(Watchlist(watchlist_id="w_dead", user_id="u1", tenant_id="t1", is_active=False))

        # Add active item to active watchlist
        w_repo.add_item(WatchlistItem(
            item_id="item_alive",
            watchlist_id=wl1.watchlist_id,
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
        ))

        # Add item to dead watchlist (should be excluded on rebuild)
        w_repo.add_item(WatchlistItem(
            item_id="item_in_dead_wl",
            watchlist_id=wl_dead.watchlist_id,
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE201M01025",
        ))

        # Add inactive item to active watchlist (should be excluded)
        w_repo.add_item(WatchlistItem(
            item_id="item_soft_deleted",
            watchlist_id=wl1.watchlist_id,
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.STATE,
            entity_id="Kerala",
            is_active=False,
        ))

        rebuild_report = idx_svc.rebuild_indices(w_repo)
        assert rebuild_report["status"] == "SUCCESS"
        assert rebuild_report["total_subscribers_indexed"] == 1
        assert rebuild_report["active_watchlists"] == 1

        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 1
        assert len(idx_svc.get_subscribers_for_company("INE201M01025")) == 0
        assert len(idx_svc.get_subscribers_for_state("Kerala")) == 0

    def test_9_integrity_validation_comprehensive(self, index_env):
        idx_svc, w_repo, _ = index_env
        wl = w_repo.create(Watchlist(watchlist_id="wl_valid", user_id="u1", tenant_id="t1", is_active=True))
        item = w_repo.add_item(WatchlistItem(
            item_id="item_valid",
            watchlist_id=wl.watchlist_id,
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
        ))
        idx_svc.add_subscriber(item)

        # Baseline: index is valid
        rep1 = idx_svc.validate_indices(w_repo)
        assert rep1.is_valid is True

        # Inject orphaned entry (watchlist doesn't exist)
        ghost_sub = WatchlistSubscriber(
            tenant_id="t1",
            user_id="u1",
            watchlist_id="wl_ghost",
            item_id="item_ghost",
            entity_type="COMPANY",
            entity_id="INE758T01015",
        )
        idx_svc.idx_company["INE758T01015"].append(ghost_sub)

        rep2 = idx_svc.validate_indices(w_repo)
        assert rep2.is_valid is False
        assert len(rep2.orphaned_entries) == 1
