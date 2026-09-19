"""
tests/test_notification_service.py
==================================
Comprehensive test suite for NotificationService, NotificationDispatcher,
transformation pipelines, deduplication, preferences, traceability, and baseline integrity.

Task 8.13.6 — Notification Dispatch & In-App Notification Center API.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from config.settings import settings
from schemas.alert import (
    AlertEvent,
    AlertPreference,
    AlertSeverity,
    AlertType,
    DigestFrequency,
    Notification,
    NotificationChannel,
    NotificationSourceType,
    NotificationStatus,
    NotificationType,
)
from schemas.alert_digest import AlertDigest, DigestType
from schemas.alert_group import AlertGroup, AlertGroupType
from schemas.watchlist import WatchlistEntityType
from services.notification_dispatcher import NotificationDispatcher
from services.notification_service import NotificationService
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.notification_repository import NotificationRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_notif_repo(tmp_path: Path) -> NotificationRepository:
    return NotificationRepository(root_dir=tmp_path / "notifications")


@pytest.fixture
def temp_pref_repo(tmp_path: Path) -> AlertPreferenceRepository:
    return AlertPreferenceRepository(root_dir=tmp_path / "preferences")


@pytest.fixture
def temp_dispatcher(
    temp_notif_repo: NotificationRepository,
    temp_pref_repo: AlertPreferenceRepository,
) -> NotificationDispatcher:
    return NotificationDispatcher(
        notification_repo=temp_notif_repo,
        alert_pref_repo=temp_pref_repo,
    )


@pytest.fixture
def notif_service(
    temp_notif_repo: NotificationRepository,
    temp_dispatcher: NotificationDispatcher,
    temp_pref_repo: AlertPreferenceRepository,
) -> NotificationService:
    return NotificationService(
        notification_repo=temp_notif_repo,
        dispatcher=temp_dispatcher,
        alert_pref_repo=temp_pref_repo,
    )


# ---------------------------------------------------------------------------
# 1. NOTIFICATION CREATION (Tests 1–6)
# ---------------------------------------------------------------------------


class TestNotificationCreation:
    """Tests 1 through 6: Core notification creation and source transformations."""

    def test_01_create_notification(self, notif_service: NotificationService):
        notif = Notification(
            notification_id="n_001",
            tenant_id="t_alpha",
            user_id="u_01",
            alert_event_id="ev_001",
            title="Energy Bill Update",
            summary="Solar energy bill passed committee",
            notification_type=NotificationType.BILL_UPDATE,
            severity=AlertSeverity.HIGH,
        )
        created = notif_service.create_notification(notif)
        assert created.notification_id == "n_001"
        assert created.status == NotificationStatus.DELIVERED
        assert created.delivered_at is not None

    def test_02_retrieve_notification(self, notif_service: NotificationService):
        notif = Notification(
            notification_id="n_002",
            tenant_id="t_alpha",
            user_id="u_01",
            alert_event_id="ev_002",
            title="Telecom Policy Amendment",
            summary="New spectrum allocation guidelines",
        )
        notif_service.create_notification(notif)
        loaded = notif_service.get_notification("n_002", tenant_id="t_alpha", user_id="u_01")
        assert loaded is not None
        assert loaded.title == "Telecom Policy Amendment"
        assert loaded.user_id == "u_01"

    def test_03_persist_and_reload_notification(
        self, temp_notif_repo: NotificationRepository, notif_service: NotificationService
    ):
        notif = Notification(
            notification_id="n_003",
            tenant_id="t_alpha",
            user_id="u_01",
            alert_event_id="ev_003",
            title="Persist Test",
            summary="Checking disk serialization round-trip",
            notification_type=NotificationType.SYSTEM,
            severity=AlertSeverity.LOW,
            metadata={"source_test": True},
        )
        notif_service.create_notification(notif)

        # Fresh repository instance reading same directory
        reloaded_repo = NotificationRepository(root_dir=temp_notif_repo._root_dir)
        reloaded = reloaded_repo.get("n_003", tenant_id="t_alpha", user_id="u_01")
        assert reloaded is not None
        assert reloaded.title == "Persist Test"
        assert reloaded.metadata.get("source_test") is True

    def test_04_alert_event_to_notification(self, notif_service: NotificationService):
        event = AlertEvent(
            alert_event_id="ev_bill_10",
            tenant_id="t_alpha",
            user_id="u_01",
            watchlist_id="wl_energy",
            source_event_id="src_event_99",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.HIGH,
            title="Electricity Act Amendment Introduced",
            summary="Bill introduced in Lok Sabha",
            entity_type=WatchlistEntityType.BILL,
            entity_id="central-bill-001",
            metadata={"jurisdiction": "central", "bill_id": "central-bill-001"},
        )
        notif = notif_service.create_notification_from_alert_event(event)
        assert notif is not None
        assert notif.alert_event_id == "ev_bill_10"
        assert notif.source_type == NotificationSourceType.ALERT_EVENT.value
        assert notif.source_id == "ev_bill_10"
        assert notif.title == "Electricity Act Amendment Introduced"
        assert notif.severity == AlertSeverity.HIGH
        assert notif.notification_type == NotificationType.BILL_UPDATE
        assert notif.deep_link.get("destination_type") == "BILL_DETAIL"

    def test_05_alert_group_to_notification(self, notif_service: NotificationService):
        group = AlertGroup(
            group_id="grp_bill_001",
            tenant_id="t_alpha",
            user_id="u_01",
            group_type=AlertGroupType.BILL,
            title="Grouped Bill Actions for Electricity Amendment",
            summary="3 actions recorded across status and document changes",
            severity=AlertSeverity.CRITICAL,
            event_ids=["ev_1", "ev_2", "ev_3"],
            affected_entity_ids=["central-bill-001"],
            metadata={"bill_id": "central-bill-001"},
        )
        notif = notif_service.create_notification_from_alert_group(group)
        assert notif is not None
        assert notif.alert_group_id == "grp_bill_001"
        assert notif.source_type == NotificationSourceType.ALERT_GROUP.value
        assert notif.source_id == "grp_bill_001"
        assert notif.alert_event_id == "ev_1"  # References first underlying event
        assert notif.severity == AlertSeverity.CRITICAL
        assert notif.notification_type == NotificationType.BILL_UPDATE
        assert notif.deep_link.get("destination_type") == "ALERT_GROUP_DETAIL"
        assert notif.metadata.get("alert_count") == 3

    def test_06_digest_to_notification(self, notif_service: NotificationService):
        digest = AlertDigest(
            digest_id="dig_daily_01",
            tenant_id="t_alpha",
            user_id="u_01",
            digest_type=DigestType.DAILY,
            frequency=DigestFrequency.DAILY_DIGEST,
            period_start="2026-09-16T00:00:00Z",
            period_end="2026-09-17T00:00:00Z",
            group_ids=["grp_1", "grp_2"],
            event_ids=["ev_1", "ev_2", "ev_3"],
            affected_bills=["central-bill-001", "central-bill-002"],
            affected_companies=["INE002A01018"],
        )
        notif = notif_service.create_notification_from_digest(digest)
        assert notif is not None
        assert notif.digest_id == "dig_daily_01"
        assert notif.source_type == NotificationSourceType.DIGEST.value
        assert notif.source_id == "dig_daily_01"
        assert notif.notification_type == NotificationType.DIGEST
        assert "Daily Legislative Alert Digest" in notif.title
        assert notif.deep_link.get("destination_type") == "DIGEST_DETAIL"


# ---------------------------------------------------------------------------
# 2. DEDUPLICATION (Tests 7–10)
# ---------------------------------------------------------------------------


class TestNotificationDeduplication:
    """Tests 7 through 10: Deterministic deduplication across events, groups, and digests."""

    def test_07_same_alert_event_does_not_create_duplicate(self, notif_service: NotificationService):
        event = AlertEvent(
            alert_event_id="ev_dedup_01",
            tenant_id="t_alpha",
            user_id="u_01",
            title="Repeated Alert Event",
            summary="Original event summary",
            alert_type=AlertType.NEW_BILL,
            severity=AlertSeverity.INFO,
        )
        first = notif_service.create_notification_from_alert_event(event)
        second = notif_service.create_notification_from_alert_event(event)
        assert first is not None
        assert second is not None
        assert first.notification_id == second.notification_id

        # Verify only 1 notification in user list
        notifs = notif_service.list_notifications(user_id="u_01", tenant_id="t_alpha")
        assert len(notifs) == 1

    def test_08_same_alert_group_does_not_create_duplicate(self, notif_service: NotificationService):
        group = AlertGroup(
            group_id="grp_dedup_01",
            tenant_id="t_alpha",
            user_id="u_01",
            title="Group Dedup Title",
            summary="Group Dedup Summary",
            group_type=AlertGroupType.COMPANY,
            event_ids=["ev_10"],
            affected_entity_ids=["INE002A01018"],
        )
        first = notif_service.create_notification_from_alert_group(group)
        second = notif_service.create_notification_from_alert_group(group)
        assert first is not None
        assert second is not None
        assert first.notification_id == second.notification_id

        notifs = notif_service.list_notifications(user_id="u_01", tenant_id="t_alpha")
        assert len(notifs) == 1

    def test_09_same_digest_does_not_create_duplicate(self, notif_service: NotificationService):
        digest = AlertDigest(
            digest_id="dig_dedup_01",
            tenant_id="t_alpha",
            user_id="u_01",
            digest_type=DigestType.WEEKLY,
            group_ids=["grp_1"],
            event_ids=["ev_1"],
        )
        first = notif_service.create_notification_from_digest(digest)
        second = notif_service.create_notification_from_digest(digest)
        assert first is not None
        assert second is not None
        assert first.notification_id == second.notification_id

        notifs = notif_service.list_notifications(user_id="u_01", tenant_id="t_alpha")
        assert len(notifs) == 1

    def test_10_different_users_remain_separate(self, notif_service: NotificationService):
        event_u1 = AlertEvent(
            alert_event_id="ev_shared",
            tenant_id="t_alpha",
            user_id="u_user1",
            title="Shared Event Title",
            summary="Shared event body",
            alert_type=AlertType.NEW_BILL,
        )
        event_u2 = AlertEvent(
            alert_event_id="ev_shared",
            tenant_id="t_alpha",
            user_id="u_user2",
            title="Shared Event Title",
            summary="Shared event body",
            alert_type=AlertType.NEW_BILL,
        )
        n1 = notif_service.create_notification_from_alert_event(event_u1)
        n2 = notif_service.create_notification_from_alert_event(event_u2)
        assert n1 is not None and n2 is not None
        assert n1.notification_id != n2.notification_id
        assert n1.user_id == "u_user1"
        assert n2.user_id == "u_user2"

        # Check inboxes
        u1_notifs = notif_service.list_notifications("u_user1", "t_alpha")
        u2_notifs = notif_service.list_notifications("u_user2", "t_alpha")
        assert len(u1_notifs) == 1
        assert len(u2_notifs) == 1
        assert u1_notifs[0].notification_id == n1.notification_id
        assert u2_notifs[0].notification_id == n2.notification_id


# ---------------------------------------------------------------------------
# 8. PREFERENCES (Tests 31–32)
# ---------------------------------------------------------------------------


class TestNotificationPreferences:
    """Tests 31 and 32: Respecting user alert preferences and suppression semantics."""

    def test_31_in_app_preference_respected(
        self, notif_service: NotificationService, temp_pref_repo: AlertPreferenceRepository
    ):
        pref = AlertPreference(
            preference_id="pref_u1",
            user_id="u_pref_test",
            tenant_id="t_pref",
            enabled=True,
            allowed_channels=[NotificationChannel.IN_APP],
            minimum_severity=AlertSeverity.LOW,
        )
        temp_pref_repo.create(pref)

        notif = Notification(
            notification_id="n_pref_ok",
            tenant_id="t_pref",
            user_id="u_pref_test",
            alert_event_id="ev_pref_1",
            severity=AlertSeverity.HIGH,
            title="Passed Filter",
            summary="Should be delivered",
        )
        created = notif_service.create_notification(notif)
        assert created.status == NotificationStatus.DELIVERED

    def test_32_disabled_in_app_behavior_follows_suppression_semantics(
        self, notif_service: NotificationService, temp_pref_repo: AlertPreferenceRepository
    ):
        # Preference disables in-app notifications
        pref = AlertPreference(
            preference_id="pref_u2",
            user_id="u_pref_suppressed",
            tenant_id="t_pref",
            enabled=True,
            allowed_channels=[NotificationChannel.EMAIL],  # IN_APP not allowed
            minimum_severity=AlertSeverity.LOW,
        )
        temp_pref_repo.create(pref)

        notif = Notification(
            notification_id="n_suppressed",
            tenant_id="t_pref",
            user_id="u_pref_suppressed",
            alert_event_id="ev_pref_2",
            severity=AlertSeverity.HIGH,
            title="Suppressed Notification",
            summary="Should be suppressed",
        )
        created = notif_service.create_notification(notif)
        assert created.status == NotificationStatus.SUPPRESSED

        # Suppressed notifications do not appear in user's active notification center list
        active_list = notif_service.list_notifications(
            user_id="u_pref_suppressed",
            tenant_id="t_pref",
        )
        assert len(active_list) == 0


# ---------------------------------------------------------------------------
# 9. TRACEABILITY & DEEP-LINKS (Tests 33–36)
# ---------------------------------------------------------------------------


class TestNotificationTraceability:
    """Tests 33 through 36: Source traceability and deep-link routing metadata."""

    def test_33_notification_references_alert_event(self, notif_service: NotificationService):
        event = AlertEvent(
            alert_event_id="ev_trace_01",
            tenant_id="t_trace",
            user_id="u_trace",
            source_event_id="change_event_123",
            title="Traceable Event",
            summary="Checking traceability",
            entity_type=WatchlistEntityType.BILL,
            entity_id="bill_123",
        )
        notif = notif_service.create_notification_from_alert_event(event)
        assert notif is not None
        assert notif.source_type == "ALERT_EVENT"
        assert notif.source_id == "ev_trace_01"
        assert notif.alert_event_id == "ev_trace_01"
        assert notif.metadata.get("source_event_id") == "change_event_123"

    def test_34_notification_references_alert_group(self, notif_service: NotificationService):
        group = AlertGroup(
            group_id="grp_trace_01",
            tenant_id="t_trace",
            user_id="u_trace",
            group_type=AlertGroupType.SECTOR,
            event_ids=["ev_10", "ev_20"],
            title="Telecom Sector Impact",
            summary="Multiple bills impacted telecom",
        )
        notif = notif_service.create_notification_from_alert_group(group)
        assert notif is not None
        assert notif.source_type == "ALERT_GROUP"
        assert notif.source_id == "grp_trace_01"
        assert notif.alert_group_id == "grp_trace_01"
        assert notif.metadata.get("event_ids") == ["ev_10", "ev_20"]

    def test_35_notification_references_digest(self, notif_service: NotificationService):
        digest = AlertDigest(
            digest_id="dig_trace_01",
            tenant_id="t_trace",
            user_id="u_trace",
            digest_type=DigestType.DAILY,
            group_ids=["grp_10"],
            event_ids=["ev_10"],
        )
        notif = notif_service.create_notification_from_digest(digest)
        assert notif is not None
        assert notif.source_type == "DIGEST"
        assert notif.source_id == "dig_trace_01"
        assert notif.digest_id == "dig_trace_01"

    def test_36_deep_link_metadata_preserved(self, notif_service: NotificationService):
        event = AlertEvent(
            alert_event_id="ev_route_01",
            tenant_id="t_trace",
            user_id="u_trace",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="INE002A01018",
            title="Reliance Industries Policy Notice",
            summary="Exposure notification",
        )
        notif = notif_service.create_notification_from_alert_event(event)
        assert notif is not None
        assert "destination_type" in notif.deep_link
        assert notif.deep_link["destination_type"] == "COMPANY_DETAIL"
        assert notif.deep_link["route"] == "/companies/INE002A01018"


# ---------------------------------------------------------------------------
# 10. STATE NOTIFICATIONS (Tests 37–38)
# ---------------------------------------------------------------------------


class TestStateNotifications:
    """Tests 37 and 38: State notification handling and zero prediction guarantee."""

    def test_37_state_notification_works(self, notif_service: NotificationService):
        event = AlertEvent(
            alert_event_id="ev_state_01",
            tenant_id="t_state",
            user_id="u_state",
            alert_type=AlertType.STATE_IMPACT,
            severity=AlertSeverity.HIGH,
            title="Karnataka Platform Workers Act Update",
            summary="Social security fund established",
            entity_type=WatchlistEntityType.STATE,
            entity_id="karnataka",
            metadata={"jurisdiction": "state", "state": "karnataka"},
        )
        notif = notif_service.create_notification_from_alert_event(event)
        assert notif is not None
        assert notif.state == "karnataka"
        assert notif.jurisdiction == "state"
        assert notif.notification_type == NotificationType.STATE_UPDATE

    def test_38_state_notification_creates_no_prediction(self, notif_service: NotificationService):
        event = AlertEvent(
            alert_event_id="ev_state_02",
            tenant_id="t_state",
            user_id="u_state",
            alert_type=AlertType.STATE_IMPACT,
            severity=AlertSeverity.MEDIUM,
            title="Maharashtra Renewable Subsidy",
            summary="Subsidy policy amended",
            entity_type=WatchlistEntityType.STATE,
            entity_id="maharashtra",
            metadata={"jurisdiction": "state", "state": "maharashtra"},
        )
        notif = notif_service.create_notification_from_alert_event(event)
        assert notif is not None
        assert "predicted_car" not in notif.metadata
        assert "expected_return" not in notif.metadata
        assert "prediction_id" not in notif.metadata


# ---------------------------------------------------------------------------
# 11. CENTRAL NOTIFICATIONS (Tests 39–40)
# ---------------------------------------------------------------------------


class TestCentralNotifications:
    """Tests 39 and 40: Central notification handling and preservation of existing prediction references."""

    def test_39_central_notification_preserves_existing_prediction_reference(
        self, notif_service: NotificationService
    ):
        event = AlertEvent(
            alert_event_id="ev_central_01",
            tenant_id="t_central",
            user_id="u_central",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.HIGH,
            title="Central Digital Personal Data Protection Bill",
            summary="Status moved to passed in Parliament",
            entity_type=WatchlistEntityType.BILL,
            entity_id="dpdp-2023",
            metadata={
                "jurisdiction": "central",
                "prediction_id": "pred_dpdp_tcs_5d",
                "predicted_car": -0.0125,
            },
        )
        notif = notif_service.create_notification_from_alert_event(event)
        assert notif is not None
        assert notif.metadata.get("prediction_id") == "pred_dpdp_tcs_5d"
        assert notif.metadata.get("predicted_car") == -0.0125

    def test_40_central_prediction_artifacts_unchanged(self):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700


# ---------------------------------------------------------------------------
# 12. INTELLIGENCE-ONLY COMPANIES (Tests 41–42)
# ---------------------------------------------------------------------------


class TestIntelligenceCompanyNotifications:
    """Tests 41 and 42: Intelligence-only companies receive exposure updates without fabricated stock predictions."""

    def test_41_intelligence_only_company_notification_works(self, notif_service: NotificationService):
        event = AlertEvent(
            alert_event_id="ev_intel_01",
            tenant_id="t_intel",
            user_id="u_intel",
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            severity=AlertSeverity.MEDIUM,
            title="Unlisted Swiggy Exposed to Karnataka Gig Bill",
            summary="Direct legislative exposure identified",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="PRIV-BUNDL-SWIGGY",
            metadata={"company_id": "PRIV-BUNDL-SWIGGY", "is_intelligence_only": True},
        )
        notif = notif_service.create_notification_from_alert_event(event)
        assert notif is not None
        assert notif.entity_id == "PRIV-BUNDL-SWIGGY"
        assert notif.notification_type == NotificationType.COMPANY_EXPOSURE

    def test_42_no_unsupported_prediction_created(self, notif_service: NotificationService):
        event = AlertEvent(
            alert_event_id="ev_intel_02",
            tenant_id="t_intel",
            user_id="u_intel",
            alert_type=AlertType.EXPOSURE_CHANGE,
            title="Zomato State Exposure",
            summary="Exposure updated",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="PRIV-BUNDL-SWIGGY",
            metadata={"company_id": "PRIV-BUNDL-SWIGGY"},
        )
        notif = notif_service.create_notification_from_alert_event(event)
        assert notif is not None
        assert "target_price" not in notif.metadata
        assert "buy_sell_hold" not in notif.metadata
        assert "alpha" not in notif.metadata


# ---------------------------------------------------------------------------
# 13. DISPATCH (Tests 43–44)
# ---------------------------------------------------------------------------


class TestDispatchAbstraction:
    """Tests 43 and 44: In-app delivery and external channel isolation."""

    def test_43_in_app_dispatch_works(self, temp_dispatcher: NotificationDispatcher):
        notif = Notification(
            notification_id="n_dispatch_01",
            tenant_id="t_disp",
            user_id="u_disp",
            alert_event_id="ev_disp_01",
            channel=NotificationChannel.IN_APP,
            title="Dispatch Test",
            summary="Dispatch body",
        )
        res = temp_dispatcher.dispatch_in_app(notif)
        assert res.status == NotificationStatus.DELIVERED
        assert res.delivered_at is not None

    def test_44_external_channels_are_not_called(self, temp_dispatcher: NotificationDispatcher):
        notif = Notification(
            notification_id="n_dispatch_ext",
            tenant_id="t_disp",
            user_id="u_disp",
            alert_event_id="ev_disp_02",
        )
        with pytest.raises(NotImplementedError):
            temp_dispatcher.dispatch_email(notif)
        with pytest.raises(NotImplementedError):
            temp_dispatcher.dispatch_push(notif)
        with pytest.raises(NotImplementedError):
            temp_dispatcher.dispatch_webhook(notif)


# ---------------------------------------------------------------------------
# 14. PIPELINE INTEGRATION (Tests 45–47)
# ---------------------------------------------------------------------------


class TestPipelineIntegration:
    """Tests 45 through 47: Pipeline output transformation to in-app notifications."""

    def test_45_alert_matching_output_can_become_notification(self, notif_service: NotificationService):
        # AlertMatching produces AlertEvent
        matched_event = AlertEvent(
            alert_event_id="ev_matched_100",
            tenant_id="t_corp",
            user_id="u_analyst",
            watchlist_id="wl_banking",
            alert_rule_id="rule_bank_status",
            source_event_id="chg_event_555",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.HIGH,
            title="Banking Laws Bill Clears Rajya Sabha",
            summary="All amendments approved by upper house",
            entity_type=WatchlistEntityType.BILL,
            entity_id="central-banking-2024",
            metadata={"bill_id": "central-banking-2024", "jurisdiction": "central"},
        )
        notif = notif_service.create_notification_from_alert_event(matched_event)
        assert notif is not None
        assert notif.status == NotificationStatus.DELIVERED
        assert notif.title == "Banking Laws Bill Clears Rajya Sabha"

    def test_46_alert_aggregation_output_can_become_notification(self, notif_service: NotificationService):
        # AlertAggregation produces AlertGroup
        group = AlertGroup(
            group_id="grp_aggregated_200",
            tenant_id="t_corp",
            user_id="u_analyst",
            group_type=AlertGroupType.BILL,
            title="Central Banking Bill 3 Events",
            summary="Consolidated legislative actions",
            severity=AlertSeverity.HIGH,
            event_ids=["ev_101", "ev_102", "ev_103"],
            affected_entity_ids=["central-banking-2024"],
        )
        notif = notif_service.create_notification_from_alert_group(group)
        assert notif is not None
        assert notif.status == NotificationStatus.DELIVERED
        assert notif.alert_group_id == "grp_aggregated_200"

    def test_47_digest_output_can_become_notification(self, notif_service: NotificationService):
        # AlertDigestService produces AlertDigest
        digest = AlertDigest(
            digest_id="dig_pipeline_300",
            tenant_id="t_corp",
            user_id="u_analyst",
            digest_type=DigestType.DAILY,
            period_start="2026-09-16T00:00:00Z",
            period_end="2026-09-17T00:00:00Z",
            group_ids=["grp_aggregated_200"],
            event_ids=["ev_101", "ev_102", "ev_103"],
            affected_bills=["central-banking-2024"],
        )
        notif = notif_service.create_notification_from_digest(digest)
        assert notif is not None
        assert notif.status == NotificationStatus.DELIVERED
        assert notif.digest_id == "dig_pipeline_300"


# ---------------------------------------------------------------------------
# 15. BASELINE INTEGRITY (Tests 48–52)
# ---------------------------------------------------------------------------


class TestBaselineIntegrity:
    """Tests 48 through 52: Verification that frozen baseline remains intact."""

    def test_48_central_47_companies_unchanged(self):
        comp_repo = CompanyRepository()
        all_comps = comp_repo.get_all()
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
        quant_comps = [c for c in all_comps if c.isin in CENTRAL_47_ISINS]
        assert len(quant_comps) == 47

    def test_49_central_940_pairs_unchanged(self):
        bill_repo = BillRepository()
        prod_central_bills = [
            b for b in bill_repo.get_all()
            if b.bill_id not in ("key-issues-and-analysis", "service-bill")
        ]
        assert len(prod_central_bills) == 20
        assert len(prod_central_bills) * 47 == 940

    def test_50_central_4700_predictions_unchanged(self):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700

    def test_51_state_86_exposures_unchanged(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        assert len(state_exps) == 86

    def test_52_state_predictions_remain_zero(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        for e in state_exps:
            assert not hasattr(e, "predicted_car")
            assert not hasattr(e, "expected_return")
