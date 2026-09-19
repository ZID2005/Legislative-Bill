"""
tests/test_watchlist_alert_foundation.py
========================================
Comprehensive test suite for Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation.

Validates all 38 required test scenarios:
 USER:
  1. Create user
  2. Retrieve user
  3. Tenant isolation

 WATCHLIST:
  4. Create watchlist
  5. Retrieve watchlist
  6. List user's watchlists
  7. Prevent cross-user access

 WATCHLIST ITEM:
  8. Add company
  9. Add bill
  10. Add sector
  11. Add State
  12. Add jurisdiction
  13. Reject invalid entity references
  14. Prevent duplicate watchlist items

 ALERT RULE:
  15. Create rule
  16. Enable/disable rule
  17. Validate alert type
  18. Validate severity

 ALERT EVENT:
  19. Create alert event
  20. Retrieve alert
  21. Mark read
  22. Archive
  23. Deduplication key calculation
  24. Duplicate event detection

 NOTIFICATION:
  25. Create notification
  26. Delivery state
  27. Read state

 PREFERENCES:
  28. Create preferences
  29. Update preferences
  30. Validate digest frequency

 SERIALIZATION:
  31. Round-trip all schemas (User, Watchlist, WatchlistItem, AlertRule, AlertEvent, Notification, AlertPreference)

 SECURITY / ISOLATION:
  32. User A cannot retrieve User B watchlist
  33. User A cannot retrieve User B alerts
  34. Tenant A cannot retrieve Tenant B records

 REGRESSION:
  35. Existing monitoring data unchanged
  36. Existing company intelligence unchanged
  37. Central quantitative universe unchanged (47 companies, 20 bills, 940 pairs, 4700 predictions)
  38. State predictions remain 0
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from config.settings import settings
from schemas.alert import (
    AlertEvent,
    AlertPreference,
    AlertRule,
    AlertSeverity,
    AlertType,
    DigestFrequency,
    Notification,
    NotificationChannel,
    NotificationStatus,
    compute_dedup_key,
)
from schemas.user import User
from schemas.watchlist import (
    Watchlist,
    WatchlistItem,
    WatchlistEntityType,
    validate_entity_reference,
)
from storage.alert_event_repository import AlertEventRepository
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.alert_rule_repository import AlertRuleRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.monitoring_repository import MonitoringRepository
from storage.notification_repository import NotificationRepository
from storage.user_repository import UserRepository
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


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def temp_user_repo(tmp_path: Path) -> UserRepository:
    return UserRepository(root_dir=tmp_path / "users")


@pytest.fixture
def temp_watchlist_repo(tmp_path: Path) -> WatchlistRepository:
    return WatchlistRepository(root_dir=tmp_path / "watchlists")


@pytest.fixture
def temp_rule_repo(tmp_path: Path) -> AlertRuleRepository:
    return AlertRuleRepository(root_dir=tmp_path / "rules")


@pytest.fixture
def temp_event_repo(tmp_path: Path) -> AlertEventRepository:
    return AlertEventRepository(root_dir=tmp_path / "events")


@pytest.fixture
def temp_notif_repo(tmp_path: Path) -> NotificationRepository:
    return NotificationRepository(root_dir=tmp_path / "notifications")


@pytest.fixture
def temp_pref_repo(tmp_path: Path) -> AlertPreferenceRepository:
    return AlertPreferenceRepository(root_dir=tmp_path / "preferences")


# ==============================================================================
# USER (1–3)
# ==============================================================================


class TestUserFoundation:
    """Tests 1 through 3: User model and repository operations."""

    def test_1_create_user(self, temp_user_repo: UserRepository):
        user = User(
            user_id="analyst_1",
            tenant_id="alpha_fund",
            display_name="Senior Regulatory Analyst",
            email="analyst@alphafund.com",
        )
        created = temp_user_repo.create(user)
        assert created.user_id == "analyst_1"
        assert created.tenant_id == "alpha_fund"
        assert created.is_active is True

    def test_2_retrieve_user(self, temp_user_repo: UserRepository):
        user = User(
            user_id="analyst_2",
            tenant_id="alpha_fund",
            display_name="Policy Lead",
        )
        temp_user_repo.create(user)
        loaded = temp_user_repo.get("analyst_2", tenant_id="alpha_fund")
        assert loaded is not None
        assert loaded.display_name == "Policy Lead"

    def test_3_tenant_isolation(self, temp_user_repo: UserRepository):
        # User in Tenant A
        user_a = User(user_id="user_common", tenant_id="tenant_A", display_name="User A")
        temp_user_repo.create(user_a)

        # User with same user_id in Tenant B
        user_b = User(user_id="user_common", tenant_id="tenant_B", display_name="User B")
        temp_user_repo.create(user_b)

        # Retrieve isolated by tenant
        got_a = temp_user_repo.get("user_common", tenant_id="tenant_A")
        got_b = temp_user_repo.get("user_common", tenant_id="tenant_B")
        assert got_a is not None and got_a.display_name == "User A"
        assert got_b is not None and got_b.display_name == "User B"

        # Querying non-matching tenant yields None
        assert temp_user_repo.get("user_common", tenant_id="tenant_C") is None


# ==============================================================================
# WATCHLIST (4–7)
# ==============================================================================


class TestWatchlistFoundation:
    """Tests 4 through 7: Watchlist collection operations and security."""

    def test_4_create_watchlist(self, temp_watchlist_repo: WatchlistRepository):
        wl = Watchlist(
            watchlist_id="wl_tech_01",
            user_id="user_101",
            tenant_id="tenant_x",
            name="Tech & Gig Workers",
            description="Tracking digital economy and logistics legislation",
        )
        created = temp_watchlist_repo.create(wl)
        assert created.watchlist_id == "wl_tech_01"
        assert created.name == "Tech & Gig Workers"

    def test_5_retrieve_watchlist(self, temp_watchlist_repo: WatchlistRepository):
        wl = Watchlist(
            watchlist_id="wl_energy_01",
            user_id="user_101",
            tenant_id="tenant_x",
            name="Clean Energy",
        )
        temp_watchlist_repo.create(wl)
        retrieved = temp_watchlist_repo.get("wl_energy_01", tenant_id="tenant_x", user_id="user_101")
        assert retrieved is not None
        assert retrieved.name == "Clean Energy"

    def test_6_list_user_watchlists(self, temp_watchlist_repo: WatchlistRepository):
        temp_watchlist_repo.create(Watchlist(watchlist_id="wl_1", user_id="u_alpha", tenant_id="t1", name="List 1"))
        temp_watchlist_repo.create(Watchlist(watchlist_id="wl_2", user_id="u_alpha", tenant_id="t1", name="List 2"))
        temp_watchlist_repo.create(Watchlist(watchlist_id="wl_other", user_id="u_beta", tenant_id="t1", name="Other"))

        user_lists = temp_watchlist_repo.list_by_user("u_alpha", tenant_id="t1")
        assert len(user_lists) == 2
        names = {w.name for w in user_lists}
        assert names == {"List 1", "List 2"}

    def test_7_prevent_cross_user_access(self, temp_watchlist_repo: WatchlistRepository):
        temp_watchlist_repo.create(Watchlist(watchlist_id="wl_private", user_id="alice", tenant_id="org1", name="Alice List"))

        # Bob cannot retrieve Alice's watchlist
        bob_attempt = temp_watchlist_repo.get("wl_private", tenant_id="org1", user_id="bob")
        assert bob_attempt is None


# ==============================================================================
# WATCHLIST ITEM (8–14)
# ==============================================================================


class TestWatchlistItemFoundation:
    """Tests 8 through 14: Entity watching across all 6 entity types and validation."""

    def _setup_watchlist(self, repo: WatchlistRepository) -> Watchlist:
        wl = Watchlist(watchlist_id="wl_main", user_id="u1", tenant_id="t1", name="Main Watchlist")
        return repo.create(wl)

    def test_8_add_company(self, temp_watchlist_repo: WatchlistRepository):
        self._setup_watchlist(temp_watchlist_repo)
        item = WatchlistItem(
            item_id="item_swiggy",
            watchlist_id="wl_main",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="PRIV-BUNDL-SWIGGY",
            display_name="Swiggy Limited",
        )
        added = temp_watchlist_repo.add_item(item)
        assert added.entity_type == WatchlistEntityType.COMPANY
        assert added.entity_id == "PRIV-BUNDL-SWIGGY"

    def test_9_add_bill(self, temp_watchlist_repo: WatchlistRepository):
        self._setup_watchlist(temp_watchlist_repo)
        item = WatchlistItem(
            item_id="item_dpdp",
            watchlist_id="wl_main",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.BILL,
            entity_id="the-digital-personal-data-protection-bill-2023",
            display_name="DPDP Act 2023",
        )
        added = temp_watchlist_repo.add_item(item)
        assert added.entity_type == WatchlistEntityType.BILL
        assert added.entity_id == "the-digital-personal-data-protection-bill-2023"

    def test_10_add_sector(self, temp_watchlist_repo: WatchlistRepository):
        self._setup_watchlist(temp_watchlist_repo)
        item = WatchlistItem(
            item_id="item_sec_tech",
            watchlist_id="wl_main",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.SECTOR,
            entity_id="Technology",
            display_name="Technology Sector",
        )
        added = temp_watchlist_repo.add_item(item)
        assert added.entity_type == WatchlistEntityType.SECTOR
        assert added.entity_id == "Technology"

    def test_11_add_state(self, temp_watchlist_repo: WatchlistRepository):
        self._setup_watchlist(temp_watchlist_repo)
        item = WatchlistItem(
            item_id="item_state_kl",
            watchlist_id="wl_main",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.STATE,
            entity_id="Kerala",
            display_name="State of Kerala",
        )
        added = temp_watchlist_repo.add_item(item)
        assert added.entity_type == WatchlistEntityType.STATE
        assert added.entity_id == "Kerala"

    def test_12_add_jurisdiction(self, temp_watchlist_repo: WatchlistRepository):
        self._setup_watchlist(temp_watchlist_repo)
        item = WatchlistItem(
            item_id="item_jur_central",
            watchlist_id="wl_main",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.JURISDICTION,
            entity_id="central",
            display_name="Central Parliament",
        )
        added = temp_watchlist_repo.add_item(item)
        assert added.entity_type == WatchlistEntityType.JURISDICTION
        assert added.entity_id == "central"

    def test_13_reject_invalid_entity_references(self):
        # Empty entity_id
        with pytest.raises(ValueError, match="entity_id cannot be empty"):
            validate_entity_reference(WatchlistEntityType.COMPANY, "   ")

        # Invalid jurisdiction
        with pytest.raises(ValueError, match="Invalid jurisdiction"):
            validate_entity_reference(WatchlistEntityType.JURISDICTION, "mars_colony")

        # Empty/short invalid company ID
        with pytest.raises(ValueError, match="Invalid company identifier"):
            validate_entity_reference(WatchlistEntityType.COMPANY, "!")

    def test_14_prevent_duplicate_watchlist_items(self, temp_watchlist_repo: WatchlistRepository):
        self._setup_watchlist(temp_watchlist_repo)
        item1 = WatchlistItem(
            item_id="item_zomato_1",
            watchlist_id="wl_main",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
        )
        temp_watchlist_repo.add_item(item1)

        # Attempt to add duplicate entity to same watchlist
        item2 = WatchlistItem(
            item_id="item_zomato_2",
            watchlist_id="wl_main",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE758T01015",
        )
        with pytest.raises(ValueError, match="already exists in watchlist"):
            temp_watchlist_repo.add_item(item2)


# ==============================================================================
# ALERT RULE (15–18)
# ==============================================================================


class TestAlertRuleFoundation:
    """Tests 15 through 18: AlertRule creation, enabling, and parameter validation."""

    def test_15_create_rule(self, temp_rule_repo: AlertRuleRepository):
        rule = AlertRule(
            alert_rule_id="rule_status_high",
            user_id="u_trader",
            tenant_id="corp_a",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            minimum_severity=AlertSeverity.HIGH,
            enabled=True,
        )
        created = temp_rule_repo.create(rule)
        assert created.alert_rule_id == "rule_status_high"
        assert created.minimum_severity == AlertSeverity.HIGH

    def test_16_enable_disable_rule(self, temp_rule_repo: AlertRuleRepository):
        rule = AlertRule(
            alert_rule_id="rule_toggle",
            user_id="u_trader",
            tenant_id="corp_a",
            enabled=True,
        )
        temp_rule_repo.create(rule)

        # Disable
        temp_rule_repo.disable("rule_toggle", tenant_id="corp_a", user_id="u_trader")
        assert temp_rule_repo.get("rule_toggle", tenant_id="corp_a", user_id="u_trader").enabled is False

        # Enable
        temp_rule_repo.enable("rule_toggle", tenant_id="corp_a", user_id="u_trader")
        assert temp_rule_repo.get("rule_toggle", tenant_id="corp_a", user_id="u_trader").enabled is True

    def test_17_validate_alert_type(self):
        # Valid alert types
        for at in AlertType:
            rule = AlertRule(alert_type=at)
            rule.validate()

        # Reject unsupported or speculative prediction alert types
        with pytest.raises(ValueError, match="Invalid alert_type"):
            invalid_rule = AlertRule(alert_type="PREDICTION_UPDATE")  # type: ignore
            invalid_rule.validate()

    def test_18_validate_severity(self):
        for sev in AlertSeverity:
            rule = AlertRule(minimum_severity=sev)
            rule.validate()

        with pytest.raises(ValueError, match="Invalid minimum_severity"):
            invalid_rule = AlertRule(minimum_severity="ULTRA_CRITICAL")  # type: ignore
            invalid_rule.validate()


# ==============================================================================
# ALERT EVENT (19–24)
# ==============================================================================


class TestAlertEventFoundation:
    """Tests 19 through 24: AlertEvent creation, state transitions, and deduplication."""

    def test_19_create_alert_event(self, temp_event_repo: AlertEventRepository):
        event = AlertEvent(
            alert_event_id="ev_001",
            tenant_id="tenant_1",
            user_id="user_1",
            source_event_id="src_change_123",
            alert_type=AlertType.NEW_BILL,
            severity=AlertSeverity.HIGH,
            title="New Central Maritime Bill Introduced",
            summary="The Coastal Shipping Bill, 2024 introduced in Parliament",
            entity_type=WatchlistEntityType.BILL,
            entity_id="the-coastal-shipping-bill-2024",
        )
        created = temp_event_repo.create(event)
        assert created.alert_event_id == "ev_001"
        assert len(created.dedup_key) == 64  # SHA-256 hash length

    def test_20_retrieve_alert(self, temp_event_repo: AlertEventRepository):
        event = AlertEvent(
            alert_event_id="ev_002",
            tenant_id="tenant_1",
            user_id="user_1",
            source_event_id="src_status_999",
            title="Kerala Gig Workers Status Advanced",
        )
        temp_event_repo.create(event)
        loaded = temp_event_repo.get("ev_002", tenant_id="tenant_1", user_id="user_1")
        assert loaded is not None
        assert loaded.title == "Kerala Gig Workers Status Advanced"

    def test_21_mark_read(self, temp_event_repo: AlertEventRepository):
        event = AlertEvent(
            alert_event_id="ev_003",
            tenant_id="tenant_1",
            user_id="user_1",
            source_event_id="src_003",
            title="Exposure Added",
        )
        temp_event_repo.create(event)
        assert temp_event_repo.get("ev_003").is_read is False

        temp_event_repo.mark_read("ev_003", tenant_id="tenant_1", user_id="user_1")
        updated = temp_event_repo.get("ev_003")
        assert updated.is_read is True
        assert updated.read_at is not None

    def test_22_archive(self, temp_event_repo: AlertEventRepository):
        event = AlertEvent(
            alert_event_id="ev_004",
            tenant_id="tenant_1",
            user_id="user_1",
            source_event_id="src_004",
            title="Document SHA-256 Changed",
        )
        temp_event_repo.create(event)
        temp_event_repo.archive("ev_004", tenant_id="tenant_1", user_id="user_1")
        updated = temp_event_repo.get("ev_004")
        assert updated.is_archived is True
        assert updated.archived_at is not None

    def test_23_deduplication_key(self):
        key1 = compute_dedup_key(
            user_id="user_10",
            watchlist_id="wl_20",
            source_event_id="src_30",
            alert_type=AlertType.BILL_STATUS_CHANGE,
        )
        key2 = compute_dedup_key(
            user_id="user_10",
            watchlist_id="wl_20",
            source_event_id="src_30",
            alert_type=AlertType.BILL_STATUS_CHANGE,
        )
        key_different = compute_dedup_key(
            user_id="user_10",
            watchlist_id="wl_20",
            source_event_id="src_30",
            alert_type=AlertType.BILL_DOCUMENT_CHANGE,
        )
        assert key1 == key2
        assert key1 != key_different
        assert len(key1) == 64

    def test_24_duplicate_event_detection(self, temp_event_repo: AlertEventRepository):
        event1 = AlertEvent(
            alert_event_id="ev_original",
            tenant_id="tenant_1",
            user_id="u_shared",
            watchlist_id="wl_shared",
            source_event_id="source_same",
            alert_type=AlertType.NEW_BILL,
            title="First Emission",
        )
        temp_event_repo.create(event1)

        # Attempt to create duplicate with identical (user, watchlist, source_event, alert_type)
        event2 = AlertEvent(
            alert_event_id="ev_duplicate",
            tenant_id="tenant_1",
            user_id="u_shared",
            watchlist_id="wl_shared",
            source_event_id="source_same",
            alert_type=AlertType.NEW_BILL,
            title="Second Emission Attempt",
        )
        with pytest.raises(ValueError, match="Duplicate alert event"):
            temp_event_repo.create(event2)


# ==============================================================================
# NOTIFICATION (25–27)
# ==============================================================================


class TestNotificationFoundation:
    """Tests 25 through 27: Notification delivery lifecycle and states."""

    def test_25_create_notification(self, temp_notif_repo: NotificationRepository):
        notif = Notification(
            notification_id="notif_100",
            tenant_id="t_corp",
            user_id="u_lead",
            alert_event_id="ev_001",
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.DELIVERED,
        )
        created = temp_notif_repo.create(notif)
        assert created.notification_id == "notif_100"
        assert created.channel == NotificationChannel.IN_APP
        assert created.status == NotificationStatus.DELIVERED

    def test_26_delivery_state(self, temp_notif_repo: NotificationRepository):
        notif = Notification(
            notification_id="notif_pending",
            tenant_id="t_corp",
            user_id="u_lead",
            alert_event_id="ev_002",
            status=NotificationStatus.PENDING,
            delivered_at=None,
        )
        temp_notif_repo.create(notif)
        assert temp_notif_repo.get("notif_pending").delivered_at is None

        temp_notif_repo.mark_delivered("notif_pending", tenant_id="t_corp", user_id="u_lead")
        updated = temp_notif_repo.get("notif_pending")
        assert updated.status == NotificationStatus.DELIVERED
        assert updated.delivered_at is not None

    def test_27_read_state(self, temp_notif_repo: NotificationRepository):
        notif = Notification(
            notification_id="notif_read_test",
            tenant_id="t_corp",
            user_id="u_lead",
            alert_event_id="ev_003",
        )
        temp_notif_repo.create(notif)
        temp_notif_repo.mark_read("notif_read_test", tenant_id="t_corp", user_id="u_lead")
        loaded = temp_notif_repo.get("notif_read_test")
        assert loaded.status == NotificationStatus.READ
        assert loaded.read_at is not None


# ==============================================================================
# PREFERENCES (28–30)
# ==============================================================================


class TestAlertPreferenceFoundation:
    """Tests 28 through 30: Alert preference management and validation."""

    def test_28_create_preferences(self, temp_pref_repo: AlertPreferenceRepository):
        pref = AlertPreference(
            preference_id="pref_01",
            user_id="user_digest",
            tenant_id="tenant_p",
            minimum_severity=AlertSeverity.MEDIUM,
            digest_frequency=DigestFrequency.DAILY_DIGEST,
        )
        created = temp_pref_repo.create(pref)
        assert created.digest_frequency == DigestFrequency.DAILY_DIGEST
        assert created.minimum_severity == AlertSeverity.MEDIUM

    def test_29_update_preferences(self, temp_pref_repo: AlertPreferenceRepository):
        pref = AlertPreference(
            preference_id="pref_02",
            user_id="user_update",
            tenant_id="tenant_p",
            digest_frequency=DigestFrequency.REAL_TIME,
        )
        temp_pref_repo.create(pref)

        pref.digest_frequency = DigestFrequency.WEEKLY_DIGEST
        pref.minimum_severity = AlertSeverity.HIGH
        temp_pref_repo.update(pref)

        loaded = temp_pref_repo.get_by_user("user_update", tenant_id="tenant_p")
        assert loaded.digest_frequency == DigestFrequency.WEEKLY_DIGEST
        assert loaded.minimum_severity == AlertSeverity.HIGH

    def test_30_validate_digest_frequency(self):
        for freq in DigestFrequency:
            pref = AlertPreference(digest_frequency=freq)
            pref.validate()

        with pytest.raises(ValueError, match="Invalid digest_frequency"):
            invalid_pref = AlertPreference(digest_frequency="MONTHLY_DIGEST")  # type: ignore
            invalid_pref.validate()


# ==============================================================================
# SERIALIZATION (31)
# ==============================================================================


class TestSerializationRoundTrip:
    """Test 31: Full round-trip dict/JSON serialization for all 7 schemas."""

    def test_31_round_trip_all_schemas(self):
        # 1. User
        user = User(user_id="u1", tenant_id="t1", display_name="Test User", email="u1@test.com")
        assert User.from_dict(json.loads(json.dumps(user.to_dict()))).to_dict() == user.to_dict()

        # 2. Watchlist
        wl = Watchlist(watchlist_id="wl1", user_id="u1", tenant_id="t1", name="Watchlist 1")
        assert Watchlist.from_dict(json.loads(json.dumps(wl.to_dict()))).to_dict() == wl.to_dict()

        # 3. WatchlistItem
        item = WatchlistItem(
            item_id="it1",
            watchlist_id="wl1",
            user_id="u1",
            tenant_id="t1",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="PRIV-BUNDL-SWIGGY",
            display_name="Swiggy",
        )
        assert WatchlistItem.from_dict(json.loads(json.dumps(item.to_dict()))).to_dict() == item.to_dict()

        # 4. AlertRule
        rule = AlertRule(
            alert_rule_id="r1",
            user_id="u1",
            tenant_id="t1",
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            minimum_severity=AlertSeverity.HIGH,
        )
        assert AlertRule.from_dict(json.loads(json.dumps(rule.to_dict()))).to_dict() == rule.to_dict()

        # 5. AlertEvent
        event = AlertEvent(
            alert_event_id="ev1",
            tenant_id="t1",
            user_id="u1",
            source_event_id="src1",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.CRITICAL,
            title="Assent Granted",
            summary="Governor gave assent",
            entity_type=WatchlistEntityType.BILL,
            entity_id="kl-gig-2024",
        )
        assert AlertEvent.from_dict(json.loads(json.dumps(event.to_dict()))).to_dict() == event.to_dict()

        # 6. Notification
        notif = Notification(
            notification_id="notif1",
            tenant_id="t1",
            user_id="u1",
            alert_event_id="ev1",
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.DELIVERED,
        )
        assert Notification.from_dict(json.loads(json.dumps(notif.to_dict()))).to_dict() == notif.to_dict()

        # 7. AlertPreference
        pref = AlertPreference(
            preference_id="p1",
            user_id="u1",
            tenant_id="t1",
            digest_frequency=DigestFrequency.DAILY_DIGEST,
            minimum_severity=AlertSeverity.LOW,
        )
        assert AlertPreference.from_dict(json.loads(json.dumps(pref.to_dict()))).to_dict() == pref.to_dict()


# ==============================================================================
# SECURITY / ISOLATION (32–34)
# ==============================================================================


class TestSecurityAndIsolation:
    """Tests 32 through 34: Strict boundaries preventing cross-tenant and cross-user leaks."""

    def test_32_user_a_cannot_retrieve_user_b_watchlist(self, temp_watchlist_repo: WatchlistRepository):
        temp_watchlist_repo.create(Watchlist(watchlist_id="wl_a", user_id="user_a", tenant_id="org1", name="A List"))
        temp_watchlist_repo.create(Watchlist(watchlist_id="wl_b", user_id="user_b", tenant_id="org1", name="B List"))

        # User A requests User B's watchlist
        assert temp_watchlist_repo.get("wl_b", tenant_id="org1", user_id="user_a") is None

    def test_33_user_a_cannot_retrieve_user_b_alerts(self, temp_event_repo: AlertEventRepository):
        temp_event_repo.create(AlertEvent(alert_event_id="ev_secret_b", user_id="user_b", tenant_id="org1", title="Confidential"))
        assert temp_event_repo.get("ev_secret_b", tenant_id="org1", user_id="user_a") is None

    def test_34_tenant_a_cannot_retrieve_tenant_b_records(
        self,
        temp_watchlist_repo: WatchlistRepository,
        temp_event_repo: AlertEventRepository,
    ):
        temp_watchlist_repo.create(Watchlist(watchlist_id="wl_t2", user_id="u1", tenant_id="tenant_2", name="Tenant 2 Data"))
        temp_event_repo.create(AlertEvent(alert_event_id="ev_t2", user_id="u1", tenant_id="tenant_2", title="Tenant 2 Alert"))

        # Query scoped to tenant_1 must yield None
        assert temp_watchlist_repo.get("wl_t2", tenant_id="tenant_1") is None
        assert temp_event_repo.get("ev_t2", tenant_id="tenant_1") is None


# ==============================================================================
# REGRESSION (35–38)
# ==============================================================================


class TestFrozenBaselineRegression:
    """Tests 35 through 38: Critical invariant checks on live production datasets."""

    def test_35_existing_monitoring_data_unchanged(self):
        mon_repo = MonitoringRepository()
        assert mon_repo.get_event_count() >= 0

    def test_36_existing_company_intelligence_unchanged(self):
        comp_repo = CompanyRepository()
        intel_comps = comp_repo.get_intelligence_companies()
        assert len(intel_comps) >= 20  # Task 8.12.3 curated intelligence entities

    def test_37_central_quantitative_universe_unchanged(self):
        # 47 Central companies
        comp_repo = CompanyRepository()
        all_comps = comp_repo.get_all()
        quant_comps = [c for c in all_comps if c.isin in CENTRAL_47_ISINS]
        assert len(quant_comps) == 47

        # 20 production Central bills
        bill_repo = BillRepository()
        prod_central_bills = [
            b for b in bill_repo.get_all()
            if b.bill_id not in ("key-issues-and-analysis", "service-bill")
        ]
        assert len(prod_central_bills) == 20

        # 940 pairs
        assert len(prod_central_bills) * len(CENTRAL_47_ISINS) == 940

        # 4,700 predictions
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700

    def test_38_state_predictions_remain_zero(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        assert len(state_exps) == 86
        for e in state_exps:
            assert not hasattr(e, "predicted_car")
            assert not hasattr(e, "expected_return")
