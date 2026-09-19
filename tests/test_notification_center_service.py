"""
tests/test_notification_center_service.py
=========================================
Comprehensive test suite for NotificationCenterService.

Covers:
- Read state management (mark_read, mark_unread, mark_all_read, unread_count).
- Archive operations (archive, unarchive, exclusion from active list, archived filter).
- Soft deletion and historical preservation.
- Filtering (unread/read, archived, type, severity, date range, entity).
- Deterministic ordering and pagination.
- Strict tenant and user isolation.
- Notification center summary metrics and recent alerts.

Task 8.13.6 — Notification Dispatch & In-App Notification Center API.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from schemas.alert import (
    AlertSeverity,
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from services.notification_center_service import (
    NotificationCenterService,
    NotificationCenterSummary,
)
from services.notification_service import NotificationService
from storage.notification_repository import NotificationRepository


@pytest.fixture
def temp_notif_repo(tmp_path: Path) -> NotificationRepository:
    return NotificationRepository(root_dir=tmp_path / "notifications")


@pytest.fixture
def notif_service(temp_notif_repo: NotificationRepository) -> NotificationService:
    return NotificationService(notification_repo=temp_notif_repo)


@pytest.fixture
def center_service(
    notif_service: NotificationService, temp_notif_repo: NotificationRepository
) -> NotificationCenterService:
    return NotificationCenterService(
        notification_service=notif_service,
        notification_repo=temp_notif_repo,
    )


# ---------------------------------------------------------------------------
# 3. READ STATE (Tests 11–14)
# ---------------------------------------------------------------------------


class TestReadStateManagement:
    """Tests 11 through 14: Read/unread toggling, mark all read, and unread counts."""

    def test_11_mark_read(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        notif = Notification(
            notification_id="n_read_1",
            tenant_id="t_read",
            user_id="u_read",
            alert_event_id="ev_r1",
            status=NotificationStatus.DELIVERED,
            is_read=False,
        )
        temp_notif_repo.create(notif)
        assert not notif.is_read

        success = center_service.mark_read("n_read_1", tenant_id="t_read", user_id="u_read")
        assert success is True

        updated = center_service.get_notification("n_read_1", tenant_id="t_read", user_id="u_read")
        assert updated is not None
        assert updated.is_read is True
        assert updated.status == NotificationStatus.READ
        assert updated.read_at is not None

    def test_12_mark_unread(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        notif = Notification(
            notification_id="n_unread_1",
            tenant_id="t_read",
            user_id="u_read",
            alert_event_id="ev_r2",
            status=NotificationStatus.READ,
            is_read=True,
            read_at="2026-09-17T10:00:00Z",
        )
        temp_notif_repo.create(notif)

        success = center_service.mark_unread("n_unread_1", tenant_id="t_read", user_id="u_read")
        assert success is True

        updated = center_service.get_notification("n_unread_1", tenant_id="t_read", user_id="u_read")
        assert updated is not None
        assert updated.is_read is False
        assert updated.status == NotificationStatus.DELIVERED
        assert updated.read_at is None

    def test_13_mark_all_read(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        for i in range(5):
            temp_notif_repo.create(
                Notification(
                    notification_id=f"n_bulk_read_{i}",
                    tenant_id="t_read",
                    user_id="u_bulk_user",
                    alert_event_id=f"ev_b{i}",
                    status=NotificationStatus.DELIVERED,
                    is_read=False,
                )
            )
        # Another user's notification should NOT be affected
        temp_notif_repo.create(
            Notification(
                notification_id="n_other_user",
                tenant_id="t_read",
                user_id="u_other_user",
                alert_event_id="ev_other",
                status=NotificationStatus.DELIVERED,
                is_read=False,
            )
        )

        updated_count = center_service.mark_all_read(user_id="u_bulk_user", tenant_id="t_read")
        assert updated_count == 5

        # Verify all 5 are read
        user_notifs = center_service.list_notifications("u_bulk_user", "t_read")
        assert all(n.is_read for n in user_notifs)

        # Verify other user's notification remains unread
        other = center_service.get_notification("n_other_user", tenant_id="t_read", user_id="u_other_user")
        assert other is not None
        assert other.is_read is False

    def test_14_unread_count_correct(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        # 3 unread, 1 read, 1 archived unread
        temp_notif_repo.create(
            Notification(notification_id="c_1", tenant_id="t_cnt", user_id="u_cnt", alert_event_id="e1", is_read=False)
        )
        temp_notif_repo.create(
            Notification(notification_id="c_2", tenant_id="t_cnt", user_id="u_cnt", alert_event_id="e2", is_read=False)
        )
        temp_notif_repo.create(
            Notification(notification_id="c_3", tenant_id="t_cnt", user_id="u_cnt", alert_event_id="e3", is_read=False)
        )
        temp_notif_repo.create(
            Notification(notification_id="c_4", tenant_id="t_cnt", user_id="u_cnt", alert_event_id="e4", is_read=True, status=NotificationStatus.READ)
        )
        temp_notif_repo.create(
            Notification(notification_id="c_5", tenant_id="t_cnt", user_id="u_cnt", alert_event_id="e5", is_read=False, is_archived=True)
        )

        # Default excludes archived
        assert center_service.get_unread_count("u_cnt", "t_cnt", include_archived=False) == 3
        # Including archived
        assert center_service.get_unread_count("u_cnt", "t_cnt", include_archived=True) == 4


# ---------------------------------------------------------------------------
# 4. ARCHIVE (Tests 15–17)
# ---------------------------------------------------------------------------


class TestArchiveLifecycle:
    """Tests 15 through 17: Archive, unarchive, and active list exclusion."""

    def test_15_archive_notification(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        temp_notif_repo.create(
            Notification(notification_id="n_arc_1", tenant_id="t_arc", user_id="u_arc", alert_event_id="e1")
        )
        success = center_service.archive("n_arc_1", tenant_id="t_arc", user_id="u_arc")
        assert success is True

        notif = center_service.get_notification("n_arc_1", tenant_id="t_arc", user_id="u_arc")
        assert notif is not None
        assert notif.is_archived is True
        assert notif.archived_at is not None

    def test_16_unarchive_notification(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        temp_notif_repo.create(
            Notification(
                notification_id="n_arc_2",
                tenant_id="t_arc",
                user_id="u_arc",
                alert_event_id="e2",
                is_archived=True,
                archived_at="2026-09-17T08:00:00Z",
            )
        )
        success = center_service.unarchive("n_arc_2", tenant_id="t_arc", user_id="u_arc")
        assert success is True

        notif = center_service.get_notification("n_arc_2", tenant_id="t_arc", user_id="u_arc")
        assert notif is not None
        assert notif.is_archived is False
        assert notif.archived_at is None

    def test_17_archived_notification_excluded_from_default_active_list(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        temp_notif_repo.create(
            Notification(notification_id="n_act", tenant_id="t_arc", user_id="u_arc", alert_event_id="e1", is_archived=False)
        )
        temp_notif_repo.create(
            Notification(notification_id="n_arc", tenant_id="t_arc", user_id="u_arc", alert_event_id="e2", is_archived=True)
        )

        # Default active list excludes archived
        active = center_service.list_notifications("u_arc", "t_arc")
        assert len(active) == 1
        assert active[0].notification_id == "n_act"

        # Explicit archived list returns only archived
        archived = center_service.list_notifications("u_arc", "t_arc", is_archived=True)
        assert len(archived) == 1
        assert archived[0].notification_id == "n_arc"


# ---------------------------------------------------------------------------
# 5. FILTERING (Tests 18–23)
# ---------------------------------------------------------------------------


class TestNotificationFiltering:
    """Tests 18 through 23: Multi-criteria deterministic filtering."""

    @pytest.fixture(autouse=True)
    def setup_sample_notifications(self, temp_notif_repo: NotificationRepository):
        base_time = datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)
        items = [
            # 1. Unread, active, BILL_UPDATE, HIGH, Central bill
            Notification(
                notification_id="f_1",
                tenant_id="t_filt",
                user_id="u_filt",
                alert_event_id="e1",
                title="Finance Bill Passed",
                notification_type=NotificationType.BILL_UPDATE,
                severity=AlertSeverity.HIGH,
                created_at=(base_time - timedelta(hours=5)).isoformat(),
                is_read=False,
                entity_type="BILL",
                entity_id="central-finance-2024",
                jurisdiction="central",
            ),
            # 2. Read, active, COMPANY_EXPOSURE, CRITICAL, Reliance
            Notification(
                notification_id="f_2",
                tenant_id="t_filt",
                user_id="u_filt",
                alert_event_id="e2",
                title="Reliance Exposure High",
                notification_type=NotificationType.COMPANY_EXPOSURE,
                severity=AlertSeverity.CRITICAL,
                created_at=(base_time - timedelta(hours=4)).isoformat(),
                is_read=True,
                status=NotificationStatus.READ,
                entity_type="COMPANY",
                entity_id="INE002A01018",
                metadata={"company_id": "INE002A01018"},
            ),
            # 3. Unread, active, STATE_UPDATE, MEDIUM, Karnataka
            Notification(
                notification_id="f_3",
                tenant_id="t_filt",
                user_id="u_filt",
                alert_event_id="e3",
                title="Karnataka Gig Act",
                notification_type=NotificationType.STATE_UPDATE,
                severity=AlertSeverity.MEDIUM,
                created_at=(base_time - timedelta(hours=3)).isoformat(),
                is_read=False,
                state="karnataka",
                jurisdiction="state",
            ),
            # 4. Unread, archived, DIGEST, INFO
            Notification(
                notification_id="f_4",
                tenant_id="t_filt",
                user_id="u_filt",
                alert_event_id="e4",
                title="Daily Digest",
                notification_type=NotificationType.DIGEST,
                severity=AlertSeverity.INFO,
                created_at=(base_time - timedelta(hours=2)).isoformat(),
                is_read=False,
                is_archived=True,
            ),
            # 5. Unread, active, LEGISLATIVE_UPDATE, LOW
            Notification(
                notification_id="f_5",
                tenant_id="t_filt",
                user_id="u_filt",
                alert_event_id="e5",
                title="Gazette Notification Published",
                notification_type=NotificationType.LEGISLATIVE_UPDATE,
                severity=AlertSeverity.LOW,
                created_at=(base_time - timedelta(hours=1)).isoformat(),
                is_read=False,
            ),
        ]
        for it in items:
            temp_notif_repo.create(it)

    def test_18_filter_unread(self, center_service: NotificationCenterService):
        # Among active notifications (f_1, f_2, f_3, f_5), f_1, f_3, f_5 are unread
        res = center_service.list_notifications("u_filt", "t_filt", is_read=False)
        assert len(res) == 3
        ids = {n.notification_id for n in res}
        assert ids == {"f_1", "f_3", "f_5"}

        # Read only
        res_read = center_service.list_notifications("u_filt", "t_filt", is_read=True)
        assert len(res_read) == 1
        assert res_read[0].notification_id == "f_2"

    def test_19_filter_archived(self, center_service: NotificationCenterService):
        res = center_service.list_notifications("u_filt", "t_filt", is_archived=True)
        assert len(res) == 1
        assert res[0].notification_id == "f_4"

    def test_20_filter_notification_type(self, center_service: NotificationCenterService):
        res = center_service.list_notifications(
            "u_filt", "t_filt", notification_type=NotificationType.COMPANY_EXPOSURE
        )
        assert len(res) == 1
        assert res[0].notification_id == "f_2"

    def test_21_filter_severity(self, center_service: NotificationCenterService):
        res = center_service.list_notifications("u_filt", "t_filt", severity=AlertSeverity.HIGH)
        assert len(res) == 1
        assert res[0].notification_id == "f_1"

    def test_22_filter_date_range(self, center_service: NotificationCenterService):
        base_time = datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)
        start = (base_time - timedelta(hours=3, minutes=30)).isoformat()
        end = (base_time - timedelta(minutes=30)).isoformat()

        res = center_service.list_notifications(
            "u_filt", "t_filt", start_time=start, end_time=end, is_archived=None
        )
        ids = {n.notification_id for n in res}
        assert ids == {"f_3", "f_4", "f_5"}

    def test_23_filter_entity_and_source(self, center_service: NotificationCenterService):
        # By bill_id
        res_bill = center_service.list_notifications("u_filt", "t_filt", bill_id="central-finance-2024")
        assert len(res_bill) == 1
        assert res_bill[0].notification_id == "f_1"

        # By company_id
        res_comp = center_service.list_notifications("u_filt", "t_filt", company_id="INE002A01018")
        assert len(res_comp) == 1
        assert res_comp[0].notification_id == "f_2"

        # By state
        res_state = center_service.list_notifications("u_filt", "t_filt", state="karnataka")
        assert len(res_state) == 1
        assert res_state[0].notification_id == "f_3"

        # By jurisdiction
        res_jur = center_service.list_notifications("u_filt", "t_filt", jurisdiction="state")
        assert len(res_jur) == 1
        assert res_jur[0].notification_id == "f_3"


# ---------------------------------------------------------------------------
# 6. PAGINATION & ORDERING (Tests 24–26)
# ---------------------------------------------------------------------------


class TestPaginationAndOrdering:
    """Tests 24 through 26: Deterministic sorting, limit, and offset pagination."""

    @pytest.fixture(autouse=True)
    def setup_paged_notifications(self, temp_notif_repo: NotificationRepository):
        base = datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)
        # Create 10 items spaced by 10 minutes
        for i in range(10):
            ts = (base + timedelta(minutes=i * 10)).isoformat()
            temp_notif_repo.create(
                Notification(
                    notification_id=f"page_notif_{i:02d}",
                    tenant_id="t_page",
                    user_id="u_page",
                    alert_event_id=f"ev_p_{i}",
                    created_at=ts,
                    title=f"Paged Item {i}",
                )
            )

    def test_24_limit_works(self, center_service: NotificationCenterService):
        res = center_service.list_notifications("u_page", "t_page", limit=4)
        assert len(res) == 4

    def test_25_offset_works(self, center_service: NotificationCenterService):
        # Order is created_at desc: item 09 (newest), 08, 07, 06, 05, 04, 03, 02, 01, 00
        page1 = center_service.list_notifications("u_page", "t_page", limit=3, offset=0)
        page2 = center_service.list_notifications("u_page", "t_page", limit=3, offset=3)

        assert [n.notification_id for n in page1] == ["page_notif_09", "page_notif_08", "page_notif_07"]
        assert [n.notification_id for n in page2] == ["page_notif_06", "page_notif_05", "page_notif_04"]

    def test_26_ordering_deterministic(self, center_service: NotificationCenterService):
        all_items = center_service.list_notifications("u_page", "t_page", limit=100)
        expected_ids = [f"page_notif_{i:02d}" for i in reversed(range(10))]
        assert [n.notification_id for n in all_items] == expected_ids


# ---------------------------------------------------------------------------
# 7. ISOLATION (Tests 27–30)
# ---------------------------------------------------------------------------


class TestTenantAndUserIsolation:
    """Tests 27 through 30: User A vs User B and Tenant A vs Tenant B isolation."""

    @pytest.fixture(autouse=True)
    def setup_multi_tenant_notifications(self, temp_notif_repo: NotificationRepository):
        temp_notif_repo.create(
            Notification(
                notification_id="iso_t1_u1",
                tenant_id="tenant_1",
                user_id="user_1",
                alert_event_id="ev_1",
                title="T1 U1 Secret Policy Alert",
            )
        )
        temp_notif_repo.create(
            Notification(
                notification_id="iso_t1_u2",
                tenant_id="tenant_1",
                user_id="user_2",
                alert_event_id="ev_2",
                title="T1 U2 Corporate Notice",
            )
        )
        temp_notif_repo.create(
            Notification(
                notification_id="iso_t2_u1",
                tenant_id="tenant_2",
                user_id="user_1",
                alert_event_id="ev_3",
                title="T2 U1 Internal Regulatory Alert",
            )
        )

    def test_27_user_a_cannot_read_user_b_notification(
        self, center_service: NotificationCenterService
    ):
        # user_1 in tenant_1 requests user_2's notification
        notif = center_service.get_notification("iso_t1_u2", tenant_id="tenant_1", user_id="user_1")
        assert notif is None

    def test_28_user_a_cannot_modify_user_b_notification(
        self, center_service: NotificationCenterService
    ):
        # user_1 cannot mark user_2's notification as read
        success = center_service.mark_read("iso_t1_u2", tenant_id="tenant_1", user_id="user_1")
        assert success is False

        # user_1 cannot archive user_2's notification
        arc_success = center_service.archive("iso_t1_u2", tenant_id="tenant_1", user_id="user_1")
        assert arc_success is False

        # user_1 cannot delete user_2's notification
        del_success = center_service.delete("iso_t1_u2", tenant_id="tenant_1", user_id="user_1")
        assert del_success is False

    def test_29_tenant_a_cannot_read_tenant_b_notification(
        self, center_service: NotificationCenterService
    ):
        # tenant_1 requests tenant_2's notification
        notif = center_service.get_notification("iso_t2_u1", tenant_id="tenant_1", user_id="user_1")
        assert notif is None

    def test_30_tenant_a_cannot_modify_tenant_b_notification(
        self, center_service: NotificationCenterService
    ):
        # tenant_1 cannot modify tenant_2's notification
        success = center_service.mark_read("iso_t2_u1", tenant_id="tenant_1", user_id="user_1")
        assert success is False

        del_success = center_service.delete("iso_t2_u1", tenant_id="tenant_1", user_id="user_1")
        assert del_success is False


# ---------------------------------------------------------------------------
# SUMMARY, RECENT & BULK OPERATIONS
# ---------------------------------------------------------------------------


class TestNotificationCenterSummaryAndBulk:
    """Additional notification center capabilities: summary metrics, recent alerts, bulk archive/delete."""

    def test_summary_metrics(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        # 2 active unread alerts
        temp_notif_repo.create(
            Notification(
                notification_id="s_1",
                tenant_id="t_sum",
                user_id="u_sum",
                alert_event_id="e1",
                notification_type=NotificationType.BILL_UPDATE,
                severity=AlertSeverity.HIGH,
                is_read=False,
            )
        )
        temp_notif_repo.create(
            Notification(
                notification_id="s_2",
                tenant_id="t_sum",
                user_id="u_sum",
                alert_event_id="e2",
                notification_type=NotificationType.COMPANY_EXPOSURE,
                severity=AlertSeverity.MEDIUM,
                is_read=True,
                status=NotificationStatus.READ,
            )
        )
        temp_notif_repo.create(
            Notification(
                notification_id="s_3",
                tenant_id="t_sum",
                user_id="u_sum",
                alert_event_id="e3",
                notification_type=NotificationType.DIGEST,
                severity=AlertSeverity.INFO,
                is_read=False,
            )
        )
        temp_notif_repo.create(
            Notification(
                notification_id="s_4",
                tenant_id="t_sum",
                user_id="u_sum",
                alert_event_id="e4",
                notification_type=NotificationType.ALERT,
                is_archived=True,
            )
        )

        summary = center_service.get_notification_center_summary("u_sum", "t_sum")
        assert isinstance(summary, NotificationCenterSummary)
        assert summary.total_active == 3
        assert summary.unread_count == 2
        assert summary.archived_count == 1
        assert summary.digest_count == 1
        assert summary.alert_count == 2
        assert summary.counts_by_type[NotificationType.BILL_UPDATE.value] == 1
        assert summary.counts_by_type[NotificationType.COMPANY_EXPOSURE.value] == 1
        assert summary.counts_by_type[NotificationType.DIGEST.value] == 1

        summary_dict = summary.to_dict()
        assert summary_dict["total_active"] == 3
        assert summary_dict["unread_count"] == 2

    def test_recent_notifications(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        base = datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)
        for i in range(15):
            temp_notif_repo.create(
                Notification(
                    notification_id=f"rec_{i:02d}",
                    tenant_id="t_rec",
                    user_id="u_rec",
                    alert_event_id=f"e_{i}",
                    created_at=(base + timedelta(minutes=i)).isoformat(),
                )
            )

        recent = center_service.get_recent_notifications("u_rec", "t_rec", limit=5)
        assert len(recent) == 5
        # Most recent first
        assert recent[0].notification_id == "rec_14"

    def test_bulk_archive_and_delete(
        self, center_service: NotificationCenterService, temp_notif_repo: NotificationRepository
    ):
        for i in range(4):
            temp_notif_repo.create(
                Notification(
                    notification_id=f"bulk_{i}",
                    tenant_id="t_blk",
                    user_id="u_blk",
                    alert_event_id=f"e_{i}",
                )
            )

        # Archive bulk_0 and bulk_1
        archived = center_service.archive_multiple(["bulk_0", "bulk_1"], "u_blk", "t_blk")
        assert archived == 2

        active = center_service.list_notifications("u_blk", "t_blk")
        assert len(active) == 2
        assert {n.notification_id for n in active} == {"bulk_2", "bulk_3"}

        # Delete bulk_2 and bulk_3
        deleted = center_service.delete_multiple(["bulk_2", "bulk_3"], "u_blk", "t_blk", soft=True)
        assert deleted == 2

        active_after_del = center_service.list_notifications("u_blk", "t_blk")
        assert len(active_after_del) == 0
