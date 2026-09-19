"""
tests/test_watchlist_service.py
===============================
Comprehensive test suite for Task 8.13.3 — Watchlist Service & Inverted Indices.

Validates all required test areas:
WATCHLIST CRUD:
 1. Create watchlist
 2. Retrieve watchlist
 3. Update watchlist
 4. Deactivate watchlist
 5. List active watchlists

ITEMS:
 6. Add company (eligible)
 7. Add bill
 8. Add sector
 9. Add industry
 10. Add State
 11. Add jurisdiction
 12. Remove item
 13. Reject duplicate item
 14. Reject invalid entity

OWNERSHIP:
 15. User A cannot access User B watchlist
 16. Tenant A cannot access Tenant B watchlist
 17. User A cannot modify User B watchlist

INDICES:
 18. Company index updated
 19. Bill index updated
 20. Sector index updated
 21. Industry index updated
 22. State index updated
 23. Jurisdiction index updated
 24. Subscriber resolution works
 25. Rebuild produces correct index
 26. Rebuild is idempotent
 27. Corrupt/stale index can be detected
 28. Inactive watchlists excluded

ALERT RULES:
 29. Create rule
 30. Enable/disable rule
 31. List rules

PREFERENCES:
 32. Get preferences
 33. Update preferences

SUMMARIES:
 34. Watchlist summary
 35. User watchlist summary

ELIGIBILITY:
 36. Non-watchlist-eligible company rejected & explicit bypass verification

INTEGRATION:
 37. Company exposure can resolve company subscribers
 38. Bill can resolve bill subscribers
 39. State event can resolve State subscribers
 40. Jurisdiction event can resolve jurisdiction subscribers

CRITICAL FROZEN BASELINE:
 41. Central 47 companies unchanged
 42. Central 940 pairs unchanged
 43. Central 4,700 predictions unchanged
 44. State 86 exposures unchanged
 45. State predictions remain 0
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from config.settings import settings
from schemas.alert import (
    AlertPreference,
    AlertRule,
    AlertSeverity,
    AlertType,
    DigestFrequency,
)
from schemas.watchlist import Watchlist, WatchlistItem, WatchlistEntityType
from services.watchlist_index_service import (
    WatchlistIndexService,
    WatchlistSubscriber,
)
from services.watchlist_service import WatchlistService
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.alert_rule_repository import AlertRuleRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.state_bill_repository import StateBillRepository
from storage.watchlist_repository import WatchlistRepository


# Canonical 47 Central quantitative ISINs
CENTRAL_47_ISINS = frozenset([
    "INE002A01018", "INE467B01029", "INE040A01034", "INE009A01021", "INE090A01021",
    "INE397D01024", "INE062A01020", "INE018A01030", "INE154A01025", "INE030A01027",
    "INE423A01024", "INE155A01022", "INE044A01045", "INE733E01010", "INE213A01029",
    "INE238A01034", "INE237A01028", "INE075A01022", "INE860A01027", "INE585B01010",
    "INE101A01026", "INE081A01020", "INE019A01030", "INE038A01020", "INE522F01014",
    "INE481G01011", "INE047A01021", "INE239A01016", "INE216A01030", "INE192A01025",
    "INE021A01026", "INE059A01026", "INE089A01023", "INE437A01024", "INE752E01010",
    "INE245A01021", "INE364U01010", "INE814H01011", "INE296A01024", "INE918I01018",
    "INE00LIC01010", "INE123W01016", "INE795G01014", "INE066A01021", "INE158A01026",
    "INE917I01010", "INE669C01036",
])


@pytest.fixture
def svc_context(tmp_path: Path):
    """Provide fully isolated service and repositories for testing."""
    w_repo = WatchlistRepository(root_dir=tmp_path / "watchlists")
    idx_svc = WatchlistIndexService(indices_dir=tmp_path / "indices", watchlist_repo=w_repo)
    rule_repo = AlertRuleRepository(root_dir=tmp_path / "rules")
    pref_repo = AlertPreferenceRepository(root_dir=tmp_path / "preferences")

    # Production read-only stores for entity validation
    comp_repo = CompanyRepository()
    bill_repo = BillRepository()
    state_bill_repo = StateBillRepository()
    exp_repo = CompanyExposureRepository()

    svc = WatchlistService(
        watchlist_repo=w_repo,
        index_service=idx_svc,
        alert_rule_repo=rule_repo,
        alert_pref_repo=pref_repo,
        company_repo=comp_repo,
        bill_repo=bill_repo,
        state_bill_repo=state_bill_repo,
        company_exposure_repo=exp_repo,
    )
    return svc, w_repo, idx_svc, rule_repo, pref_repo


# ==============================================================================
# WATCHLIST CRUD (1–5)
# ==============================================================================


class TestWatchlistCRUD:
    def test_1_create_watchlist(self, svc_context):
        svc, w_repo, _, _, _ = svc_context
        wl = svc.create_watchlist(
            tenant_id="org_alpha",
            user_id="user_1",
            name="Alpha Tech Portfolio",
            description="Tech and retail monitoring",
            is_default=True,
        )
        assert wl.watchlist_id is not None
        assert wl.name == "Alpha Tech Portfolio"
        assert wl.tenant_id == "org_alpha"
        assert wl.user_id == "user_1"
        assert wl.is_active is True

    def test_2_retrieve_watchlist(self, svc_context):
        svc, _, _, _, _ = svc_context
        created = svc.create_watchlist(
            tenant_id="org_alpha",
            user_id="user_1",
            name="Alpha Monitor",
        )
        fetched = svc.get_watchlist(created.watchlist_id, tenant_id="org_alpha", user_id="user_1")
        assert fetched is not None
        assert fetched.watchlist_id == created.watchlist_id

    def test_3_update_watchlist(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(
            tenant_id="org_alpha",
            user_id="user_1",
            name="Initial Name",
        )
        wl.name = "Updated Name"
        wl.description = "Updated description"
        updated = svc.update_watchlist(wl, tenant_id="org_alpha", user_id="user_1")
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"

    def test_4_deactivate_watchlist(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(
            tenant_id="org_alpha",
            user_id="user_1",
            name="Deactivate Target",
        )
        # Add an eligible item (INE758T01015 - Zomato Limited) to test index synchronization
        svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
            tenant_id="org_alpha",
            user_id="user_1",
        )
        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 1

        success = svc.deactivate_watchlist(wl.watchlist_id, tenant_id="org_alpha", user_id="user_1")
        assert success is True

        refetched = svc.get_watchlist(wl.watchlist_id, tenant_id="org_alpha", user_id="user_1")
        assert refetched.is_active is False

        # Inactive watchlist must be purged from active subscriber index
        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 0

    def test_5_list_active_watchlists(self, svc_context):
        svc, _, _, _, _ = svc_context
        svc.create_watchlist(tenant_id="org_alpha", user_id="user_list", name="Active 1", is_active=True)
        w2 = svc.create_watchlist(tenant_id="org_alpha", user_id="user_list", name="Active 2", is_active=True)
        svc.deactivate_watchlist(w2.watchlist_id, tenant_id="org_alpha", user_id="user_list")

        all_lists = svc.list_user_watchlists(user_id="user_list", tenant_id="org_alpha")
        assert len(all_lists) == 2

        active_only = svc.list_user_watchlists(user_id="user_list", tenant_id="org_alpha", is_active=True)
        assert len(active_only) == 1
        assert active_only[0].name == "Active 1"


# ==============================================================================
# ITEMS & ENTITY VALIDATION (6–14)
# ==============================================================================


class TestWatchlistItemsAndValidation:
    def test_6_add_company(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        # INE758T01015 (Zomato Limited) is verified watchlist_eligible=True
        item = svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
            tenant_id="t1",
            user_id="u1",
        )
        assert item.entity_type == WatchlistEntityType.COMPANY
        assert item.entity_id == "INE758T01015"
        assert item.display_name == "Zomato Limited"
        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 1

    def test_7_add_bill(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        # Valid Central bill
        item = svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.BILL,
            entity_id="the-coastal-shipping-bill-2024",
            tenant_id="t1",
            user_id="u1",
        )
        assert item.entity_type == WatchlistEntityType.BILL
        assert item.entity_id == "the-coastal-shipping-bill-2024"
        assert "Coastal Shipping" in item.display_name
        assert len(idx_svc.get_subscribers_for_bill("the-coastal-shipping-bill-2024")) == 1

    def test_8_add_sector(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        item = svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.SECTOR,
            entity_id="Technology",
            tenant_id="t1",
            user_id="u1",
        )
        assert item.entity_type == WatchlistEntityType.SECTOR
        assert item.entity_id.lower() == "technology"
        assert len(idx_svc.get_subscribers_for_sector("Technology")) == 1

    def test_9_add_industry(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        item = svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.INDUSTRY,
            entity_id="Food Delivery & Quick Commerce",
            tenant_id="t1",
            user_id="u1",
        )
        assert item.entity_type == WatchlistEntityType.INDUSTRY
        assert "Food Delivery" in item.display_name
        assert len(idx_svc.get_subscribers_for_industry("Food Delivery & Quick Commerce")) == 1

    def test_10_add_state(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        item = svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.STATE,
            entity_id="kerala",
            tenant_id="t1",
            user_id="u1",
        )
        assert item.entity_type == WatchlistEntityType.STATE
        assert item.entity_id == "Kerala"
        assert len(idx_svc.get_subscribers_for_state("Kerala")) == 1

    def test_11_add_jurisdiction(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        item = svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.JURISDICTION,
            entity_id="central",
            tenant_id="t1",
            user_id="u1",
        )
        assert item.entity_type == WatchlistEntityType.JURISDICTION
        assert item.entity_id == "central"
        assert len(idx_svc.get_subscribers_for_jurisdiction("central")) == 1

    def test_12_remove_item(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        item = svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
            tenant_id="t1",
            user_id="u1",
        )
        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 1

        success = svc.remove_item(item.item_id, tenant_id="t1", user_id="u1")
        assert success is True
        # Must be removed from index
        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 0

    def test_13_reject_duplicate_item(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
            tenant_id="t1",
            user_id="u1",
        )
        with pytest.raises(ValueError, match="already exists in watchlist"):
            svc.add_item(
                watchlist_id=wl.watchlist_id,
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="INE758T01015",
                tenant_id="t1",
                user_id="u1",
            )

    def test_14_reject_invalid_entity(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")

        # Fake non-existent company
        with pytest.raises(ValueError, match="not found in company master"):
            svc.add_item(
                watchlist_id=wl.watchlist_id,
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="NON_EXISTENT_COMPANY_XYZ",
                tenant_id="t1",
                user_id="u1",
            )

        # Fake non-existent bill
        with pytest.raises(ValueError, match="not found in Central or State bill repository"):
            svc.add_item(
                watchlist_id=wl.watchlist_id,
                entity_type=WatchlistEntityType.BILL,
                entity_id="fake-bill-id-9999",
                tenant_id="t1",
                user_id="u1",
            )

        # Fake non-existent state
        with pytest.raises(ValueError, match="Invalid Indian State"):
            svc.add_item(
                watchlist_id=wl.watchlist_id,
                entity_type=WatchlistEntityType.STATE,
                entity_id="Atlantis State",
                tenant_id="t1",
                user_id="u1",
            )


# ==============================================================================
# OWNERSHIP & TENANT ISOLATION (15–17)
# ==============================================================================


class TestOwnershipAndTenantIsolation:
    def test_15_user_a_cannot_access_user_b_watchlist(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl_b = svc.create_watchlist(tenant_id="org1", user_id="user_b", name="B List")

        # Scoped to user_a must return None
        accessed = svc.get_watchlist(wl_b.watchlist_id, tenant_id="org1", user_id="user_a")
        assert accessed is None

        # Listing items of user_b watchlist by user_a must be blocked
        with pytest.raises(PermissionError):
            svc.list_items(wl_b.watchlist_id, tenant_id="org1", user_id="user_a")

    def test_16_tenant_a_cannot_access_tenant_b_watchlist(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl_t2 = svc.create_watchlist(tenant_id="tenant_2", user_id="u1", name="Tenant 2 List")

        accessed = svc.get_watchlist(wl_t2.watchlist_id, tenant_id="tenant_1", user_id="u1")
        assert accessed is None

    def test_17_user_a_cannot_modify_user_b_watchlist(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl_b = svc.create_watchlist(tenant_id="org1", user_id="user_b", name="B Secret")

        # Modification attempt by user_a
        wl_b.name = "Hacked Name"
        with pytest.raises(PermissionError):
            svc.update_watchlist(wl_b, tenant_id="org1", user_id="user_a")

        # Deactivation attempt by user_a
        with pytest.raises(PermissionError):
            svc.deactivate_watchlist(wl_b.watchlist_id, tenant_id="org1", user_id="user_a")

        # Add item attempt by user_a
        with pytest.raises(PermissionError):
            svc.add_item(
                watchlist_id=wl_b.watchlist_id,
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="INE758T01015",
                tenant_id="org1",
                user_id="user_a",
            )


# ==============================================================================
# INVERTED INDICES & SUBSCRIBER RESOLUTION (18–28)
# ==============================================================================


class TestInvertedIndicesAndResolution:
    def test_18_through_23_all_indices_updated(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")

        svc.add_item(wl.watchlist_id, WatchlistEntityType.COMPANY, "INE758T01015", tenant_id="t1", user_id="u1")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.BILL, "the-coastal-shipping-bill-2024", tenant_id="t1", user_id="u1")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.SECTOR, "Technology", tenant_id="t1", user_id="u1")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.INDUSTRY, "Food Delivery & Quick Commerce", tenant_id="t1", user_id="u1")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.STATE, "Kerala", tenant_id="t1", user_id="u1")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.JURISDICTION, "central", tenant_id="t1", user_id="u1")

        # Verify all 6 indices have the subscriber
        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 1
        assert len(idx_svc.get_subscribers_for_bill("the-coastal-shipping-bill-2024")) == 1
        assert len(idx_svc.get_subscribers_for_sector("Technology")) == 1
        assert len(idx_svc.get_subscribers_for_industry("Food Delivery & Quick Commerce")) == 1
        assert len(idx_svc.get_subscribers_for_state("Kerala")) == 1
        assert len(idx_svc.get_subscribers_for_jurisdiction("central")) == 1

        # Check subscriber properties
        sub = idx_svc.get_subscribers_for_company("INE758T01015")[0]
        assert sub.tenant_id == "t1"
        assert sub.user_id == "u1"
        assert sub.watchlist_id == wl.watchlist_id
        assert sub.entity_type == "COMPANY"
        assert sub.entity_id == "INE758T01015"

    def test_24_subscriber_resolution_works(self, svc_context):
        svc, _, _, _, _ = svc_context
        w1 = svc.create_watchlist(tenant_id="t1", user_id="user_1", name="W1")
        w2 = svc.create_watchlist(tenant_id="t1", user_id="user_2", name="W2")

        svc.add_item(w1.watchlist_id, WatchlistEntityType.COMPANY, "INE758T01015", tenant_id="t1", user_id="user_1")
        svc.add_item(w2.watchlist_id, WatchlistEntityType.COMPANY, "INE758T01015", tenant_id="t1", user_id="user_2")

        subs = svc.resolve_subscribers(WatchlistEntityType.COMPANY, "INE758T01015")
        assert len(subs) == 2
        user_ids = {s.user_id for s in subs}
        assert user_ids == {"user_1", "user_2"}

    def test_25_rebuild_produces_correct_index(self, svc_context):
        svc, w_repo, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.COMPANY, "INE758T01015", tenant_id="t1", user_id="u1")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.STATE, "Kerala", tenant_id="t1", user_id="u1")

        # Corrupt memory index
        idx_svc.idx_company.clear()
        idx_svc.idx_state.clear()
        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 0

        # Rebuild
        result = svc.rebuild_indices()
        assert result["status"] == "SUCCESS"
        assert result["total_subscribers_indexed"] == 2

        # Verify indices restored
        assert len(idx_svc.get_subscribers_for_company("INE758T01015")) == 1
        assert len(idx_svc.get_subscribers_for_state("Kerala")) == 1

    def test_26_rebuild_is_idempotent(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.COMPANY, "INE758T01015", tenant_id="t1", user_id="u1")

        # Rebuild 1
        svc.rebuild_indices()
        path = idx_svc._index_path(WatchlistEntityType.COMPANY)
        with open(path, "r", encoding="utf-8") as f:
            dump1 = f.read()

        # Rebuild 2
        svc.rebuild_indices()
        with open(path, "r", encoding="utf-8") as f:
            dump2 = f.read()

        # Both dumps should have identical subscriber entries
        d1 = json.loads(dump1)["entries"]
        d2 = json.loads(dump2)["entries"]
        assert d1 == d2

    def test_27_corrupt_or_stale_index_detected(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        item = svc.add_item(wl.watchlist_id, WatchlistEntityType.COMPANY, "INE758T01015", tenant_id="t1", user_id="u1")

        # Fresh validation should pass
        report1 = svc.validate_indices()
        assert report1.is_valid is True

        # Inject stale entry pointing to non-existent item
        fake_sub = WatchlistSubscriber(
            tenant_id="t1",
            user_id="u1",
            watchlist_id=wl.watchlist_id,
            item_id="ghost_item_999",
            entity_type="COMPANY",
            entity_id="INE758T01015",
        )
        idx_svc.idx_company["INE758T01015"].append(fake_sub)

        report2 = svc.validate_indices()
        assert report2.is_valid is False
        assert len(report2.stale_entries) >= 1

    def test_28_inactive_watchlists_excluded_from_resolution(self, svc_context):
        svc, _, idx_svc, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="Active WL")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.COMPANY, "INE758T01015", tenant_id="t1", user_id="u1")
        assert len(svc.resolve_subscribers(WatchlistEntityType.COMPANY, "INE758T01015")) == 1

        # Deactivate
        svc.deactivate_watchlist(wl.watchlist_id, tenant_id="t1", user_id="u1")

        # Must not return inactive watchlist as active subscriber
        assert len(svc.resolve_subscribers(WatchlistEntityType.COMPANY, "INE758T01015")) == 0


# ==============================================================================
# ALERT RULES (29–31)
# ==============================================================================


class TestAlertRulesIntegration:
    def test_29_create_rule(self, svc_context):
        svc, _, _, rule_repo, _ = svc_context
        rule = svc.create_alert_rule(
            user_id="u1",
            tenant_id="t1",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            minimum_severity=AlertSeverity.HIGH,
            enabled=True,
        )
        assert rule.alert_rule_id is not None
        assert rule.alert_type == AlertType.BILL_STATUS_CHANGE
        assert rule.minimum_severity == AlertSeverity.HIGH
        assert rule.enabled is True

    def test_30_enable_disable_rule(self, svc_context):
        svc, _, _, rule_repo, _ = svc_context
        rule = svc.create_alert_rule(user_id="u1", tenant_id="t1", enabled=True)

        svc.disable_alert_rule(rule.alert_rule_id, tenant_id="t1", user_id="u1")
        assert rule_repo.get(rule.alert_rule_id).enabled is False

        svc.enable_alert_rule(rule.alert_rule_id, tenant_id="t1", user_id="u1")
        assert rule_repo.get(rule.alert_rule_id).enabled is True

    def test_31_list_rules(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        svc.create_alert_rule(user_id="u1", tenant_id="t1", watchlist_id=wl.watchlist_id)
        svc.create_alert_rule(user_id="u1", tenant_id="t1", watchlist_id=None)

        all_rules = svc.list_alert_rules(user_id="u1", tenant_id="t1")
        assert len(all_rules) == 2

        wl_rules = svc.list_alert_rules(user_id="u1", tenant_id="t1", watchlist_id=wl.watchlist_id)
        assert len(wl_rules) == 1


# ==============================================================================
# PREFERENCES (32–33)
# ==============================================================================


class TestAlertPreferencesIntegration:
    def test_32_get_preferences(self, svc_context):
        svc, _, _, _, _ = svc_context
        pref = svc.get_user_preferences(user_id="user_p", tenant_id="t1")
        assert pref is not None
        assert pref.user_id == "user_p"
        assert pref.digest_frequency == DigestFrequency.REAL_TIME
        assert pref.enabled is True

    def test_33_update_preferences(self, svc_context):
        svc, _, _, _, _ = svc_context
        svc.get_user_preferences(user_id="user_p", tenant_id="t1")
        updated = svc.update_user_preferences(
            user_id="user_p",
            tenant_id="t1",
            digest_frequency=DigestFrequency.DAILY_DIGEST,
            minimum_severity=AlertSeverity.HIGH,
        )
        assert updated.digest_frequency == DigestFrequency.DAILY_DIGEST
        assert updated.minimum_severity == AlertSeverity.HIGH


# ==============================================================================
# SUMMARIES (34–35)
# ==============================================================================


class TestSummaries:
    def test_34_watchlist_summary(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="Executive Watchlist")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.COMPANY, "INE758T01015", tenant_id="t1", user_id="u1")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.BILL, "the-coastal-shipping-bill-2024", tenant_id="t1", user_id="u1")
        svc.create_alert_rule(user_id="u1", tenant_id="t1", watchlist_id=wl.watchlist_id, enabled=True)

        summary = svc.get_watchlist_summary(wl.watchlist_id, tenant_id="t1", user_id="u1")
        assert summary["watchlist_id"] == wl.watchlist_id
        assert summary["name"] == "Executive Watchlist"
        assert summary["item_count"] == 2
        assert "INE758T01015" in summary["companies_watched"]
        assert "the-coastal-shipping-bill-2024" in summary["bills_watched"]
        assert summary["enabled_alert_rules_count"] == 1

    def test_35_user_watchlist_summary(self, svc_context):
        svc, _, _, _, _ = svc_context
        w1 = svc.create_watchlist(tenant_id="t1", user_id="u_dash", name="W1")
        w2 = svc.create_watchlist(tenant_id="t1", user_id="u_dash", name="W2")
        svc.add_item(w1.watchlist_id, WatchlistEntityType.COMPANY, "INE758T01015", tenant_id="t1", user_id="u_dash")
        svc.add_item(w2.watchlist_id, WatchlistEntityType.STATE, "Kerala", tenant_id="t1", user_id="u_dash")

        u_summary = svc.get_user_watchlist_summary(user_id="u_dash", tenant_id="t1")
        assert u_summary["total_watchlists"] == 2
        assert u_summary["active_watchlists"] == 2
        assert u_summary["total_items"] == 2
        assert u_summary["total_watched_companies"] == 1
        assert u_summary["total_watched_states"] == 1


# ==============================================================================
# ELIGIBILITY ENFORCEMENT (36)
# ==============================================================================


class TestEligibilityEnforcement:
    def test_36_non_watchlist_eligible_company_rejected(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")

        # INE002A01018 (Reliance Industries Limited) has watchlist_eligible=False
        with pytest.raises(ValueError, match="not eligible for watchlists"):
            svc.add_item(
                watchlist_id=wl.watchlist_id,
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="INE002A01018",
                tenant_id="t1",
                user_id="u1",
            )

        # PRIV-BUNDL-SWIGGY also has watchlist_eligible=False in master data
        with pytest.raises(ValueError, match="not eligible for watchlists"):
            svc.add_item(
                watchlist_id=wl.watchlist_id,
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="PRIV-BUNDL-SWIGGY",
                tenant_id="t1",
                user_id="u1",
            )

        # Explicit bypass allows adding when explicitly authorized
        item_bypassed = svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="PRIV-BUNDL-SWIGGY",
            tenant_id="t1",
            user_id="u1",
            bypass_eligibility=True,
        )
        assert item_bypassed.entity_id == "PRIV-BUNDL-SWIGGY"


# ==============================================================================
# INTEGRATION & EVENT RESOLUTION PRIMITIVES (37–40)
# ==============================================================================


class TestIntegrationResolutionPrimitives:
    def test_37_company_exposure_can_resolve_subscribers(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        # INE758T01015 (Zomato) is verified exposed to telangana-vs-bill-11-2024
        svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
            tenant_id="t1",
            user_id="u1",
        )

        # Multi-hop primitive: Bill X -> Company Exposure -> Zomato Subscribers
        exposed_subs = svc.resolve_subscribers_by_company_exposure("telangana-vs-bill-11-2024")
        assert "INE758T01015" in exposed_subs
        assert len(exposed_subs["INE758T01015"]) == 1
        assert exposed_subs["INE758T01015"][0].user_id == "u1"

    def test_38_bill_direct_subscribers(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u1", name="WL")
        svc.add_item(
            watchlist_id=wl.watchlist_id,
            entity_type=WatchlistEntityType.BILL,
            entity_id="the-coastal-shipping-bill-2024",
            tenant_id="t1",
            user_id="u1",
        )

        subs = svc.resolve_subscribers_for_bill_change("the-coastal-shipping-bill-2024")
        assert len(subs) == 1
        assert subs[0].user_id == "u1"

    def test_39_state_event_resolution(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u_kerala", name="Kerala Watch")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.STATE, "Kerala", tenant_id="t1", user_id="u_kerala")

        subs = svc.resolve_subscribers(WatchlistEntityType.STATE, "kerala")
        assert len(subs) == 1
        assert subs[0].user_id == "u_kerala"

    def test_40_jurisdiction_event_resolution(self, svc_context):
        svc, _, _, _, _ = svc_context
        wl = svc.create_watchlist(tenant_id="t1", user_id="u_central", name="Central Watch")
        svc.add_item(wl.watchlist_id, WatchlistEntityType.JURISDICTION, "central", tenant_id="t1", user_id="u_central")

        subs = svc.resolve_subscribers(WatchlistEntityType.JURISDICTION, "central")
        assert len(subs) == 1
        assert subs[0].user_id == "u_central"


# ==============================================================================
# CRITICAL FROZEN BASELINE (41–45)
# ==============================================================================


class TestCriticalFrozenBaseline:
    def test_41_central_47_companies_unchanged(self):
        comp_repo = CompanyRepository()
        all_comps = comp_repo.get_all()
        quant_comps = [c for c in all_comps if c.isin in CENTRAL_47_ISINS]
        assert len(quant_comps) == 47

    def test_42_central_940_pairs_unchanged(self):
        bill_repo = BillRepository()
        prod_central_bills = [
            b for b in bill_repo.get_all()
            if b.bill_id not in ("key-issues-and-analysis", "service-bill")
        ]
        assert len(prod_central_bills) == 20
        assert len(prod_central_bills) * len(CENTRAL_47_ISINS) == 940

    def test_43_central_4700_predictions_unchanged(self):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700

    def test_44_state_86_exposures_unchanged(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        assert len(state_exps) == 86

    def test_45_state_predictions_remain_zero(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        for e in state_exps:
            assert not hasattr(e, "predicted_car")
            assert not hasattr(e, "expected_return")
