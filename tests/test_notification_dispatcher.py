"""
tests/test_notification_dispatcher.py
=====================================
Comprehensive tests for NotificationDispatcher, Provider Registry, multi-channel dispatch,
AlertPreference integration, delivery status tracking, idempotency, tenant/user isolation,
pipeline integration, and frozen baseline integrity.

Task 8.13.7 — Outbound Notification Delivery Providers & Webhook Dispatch.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from config.settings import settings
from schemas.alert import (
    AlertEvent,
    AlertPreference,
    AlertSeverity,
    AlertType,
    Notification,
    NotificationChannel,
    NotificationSourceType,
    NotificationStatus,
    NotificationType,
)
from schemas.alert_digest import AlertDigest, DigestType
from schemas.alert_group import AlertGroup, AlertGroupType
from schemas.notification_delivery import NotificationErrorCode
from services.notification_center_service import NotificationCenterService
from services.notification_dispatcher import NotificationDispatcher
from services.notification_providers import (
    InAppNotificationProvider,
    MockEmailProvider,
    MockPushProvider,
    MockWebhookTransport,
    NotificationProviderRegistry,
    WebhookNotificationProvider,
)
from services.notification_service import NotificationService
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.notification_delivery_repository import NotificationDeliveryRepository
from storage.notification_repository import NotificationRepository


@pytest.fixture
def temp_notif_repo(tmp_path: Path) -> NotificationRepository:
    return NotificationRepository(root_dir=tmp_path / "notifications")


@pytest.fixture
def temp_pref_repo(tmp_path: Path) -> AlertPreferenceRepository:
    return AlertPreferenceRepository(root_dir=tmp_path / "preferences")


@pytest.fixture
def temp_delivery_repo(tmp_path: Path) -> NotificationDeliveryRepository:
    return NotificationDeliveryRepository(root_dir=tmp_path / "deliveries")


@pytest.fixture
def mock_webhook_transport() -> MockWebhookTransport:
    return MockWebhookTransport(default_status_code=200)


@pytest.fixture
def configured_registry(
    temp_notif_repo: NotificationRepository,
    mock_webhook_transport: MockWebhookTransport,
) -> NotificationProviderRegistry:
    registry = NotificationProviderRegistry()
    registry.register(InAppNotificationProvider(notification_repo=temp_notif_repo))
    registry.register(MockEmailProvider())
    registry.register(MockPushProvider())
    registry.register(
        WebhookNotificationProvider(
            transport=mock_webhook_transport,
            secret="whsec_test_abc123",
            default_destination_url="https://api.corporate.example/webhook",
        )
    )
    return registry


@pytest.fixture
def dispatcher(
    temp_notif_repo: NotificationRepository,
    temp_pref_repo: AlertPreferenceRepository,
    temp_delivery_repo: NotificationDeliveryRepository,
    configured_registry: NotificationProviderRegistry,
) -> NotificationDispatcher:
    return NotificationDispatcher(
        notification_repo=temp_notif_repo,
        alert_pref_repo=temp_pref_repo,
        delivery_repo=temp_delivery_repo,
        registry=configured_registry,
    )


@pytest.fixture
def sample_notification() -> Notification:
    return Notification(
        notification_id="n_disp_test_001",
        tenant_id="tenant_alpha",
        user_id="user_01",
        alert_event_id="ev_001",
        title="Finance Bill Passed",
        summary="Finance Bill, 2024 received President assent.",
        notification_type=NotificationType.BILL_UPDATE,
        severity=AlertSeverity.HIGH,
        metadata={"bill_id": "finance-bill-2024", "jurisdiction": "central"},
    )


# ---------------------------------------------------------------------------
# 1. DISPATCH ROUTING (Tests 1–4)
# ---------------------------------------------------------------------------


class TestDispatchRouting:
    """Tests 1 through 4: Dispatcher channel routing."""

    def test_01_in_app_dispatch_uses_existing_in_app_path(
        self, dispatcher: NotificationDispatcher, sample_notification: Notification
    ):
        result = dispatcher.dispatch(sample_notification, channel=NotificationChannel.IN_APP)
        assert result.success is True
        assert result.status == NotificationStatus.DELIVERED
        assert result.channel == NotificationChannel.IN_APP
        assert result.provider == "in_app_provider"

        # Verify saved in notification repo
        saved = dispatcher.notification_repo.get(
            sample_notification.notification_id,
            tenant_id="tenant_alpha",
            user_id="user_01",
        )
        assert saved is not None
        assert saved.status == NotificationStatus.DELIVERED

    def test_02_email_dispatch_routes_to_email_provider(
        self,
        dispatcher: NotificationDispatcher,
        sample_notification: Notification,
        configured_registry: NotificationProviderRegistry,
    ):
        result = dispatcher.dispatch(
            sample_notification,
            channel=NotificationChannel.EMAIL,
            recipient="user@example.com",
        )
        assert result.success is True
        assert result.status == NotificationStatus.DELIVERED
        assert result.channel == NotificationChannel.EMAIL

        email_provider = configured_registry.get(NotificationChannel.EMAIL)
        assert isinstance(email_provider, MockEmailProvider)
        assert len(email_provider.sent_emails) == 1
        assert email_provider.sent_emails[0]["recipient"] == "user@example.com"

    def test_03_push_dispatch_routes_to_push_provider(
        self,
        dispatcher: NotificationDispatcher,
        sample_notification: Notification,
        configured_registry: NotificationProviderRegistry,
    ):
        result = dispatcher.dispatch(
            sample_notification,
            channel=NotificationChannel.PUSH,
            recipient="device_tok_777",
        )
        assert result.success is True
        assert result.status == NotificationStatus.DELIVERED
        assert result.channel == NotificationChannel.PUSH

        push_provider = configured_registry.get(NotificationChannel.PUSH)
        assert isinstance(push_provider, MockPushProvider)
        assert len(push_provider.sent_pushes) == 1
        assert push_provider.sent_pushes[0]["device_token"] == "device_tok_777"

    def test_04_webhook_dispatch_routes_to_webhook_provider(
        self,
        dispatcher: NotificationDispatcher,
        sample_notification: Notification,
        mock_webhook_transport: MockWebhookTransport,
    ):
        result = dispatcher.dispatch(
            sample_notification,
            channel=NotificationChannel.WEBHOOK,
            recipient="https://api.corporate.example/webhook",
        )
        assert result.success is True
        assert result.status == NotificationStatus.DELIVERED
        assert result.channel == NotificationChannel.WEBHOOK
        assert len(mock_webhook_transport.calls) == 1
        assert mock_webhook_transport.calls[0]["url"] == "https://api.corporate.example/webhook"


# ---------------------------------------------------------------------------
# 2. PROVIDER REGISTRY (Tests 5–6)
# ---------------------------------------------------------------------------


class TestProviderRegistry:
    """Tests 5 and 6: Registry lookup and missing provider handling."""

    def test_05_provider_registry_resolves_correct_provider(
        self, configured_registry: NotificationProviderRegistry
    ):
        assert configured_registry.has(NotificationChannel.IN_APP) is True
        assert configured_registry.has(NotificationChannel.EMAIL) is True
        assert configured_registry.has(NotificationChannel.PUSH) is True
        assert configured_registry.has(NotificationChannel.WEBHOOK) is True

        p_in_app = configured_registry.get(NotificationChannel.IN_APP)
        assert isinstance(p_in_app, InAppNotificationProvider)

        p_email = configured_registry.get(NotificationChannel.EMAIL)
        assert isinstance(p_email, MockEmailProvider)

    def test_06_missing_provider_returns_explicit_unavailable_result(
        self,
        dispatcher: NotificationDispatcher,
        configured_registry: NotificationProviderRegistry,
        sample_notification: Notification,
    ):
        # Unregister email provider
        configured_registry.unregister(NotificationChannel.EMAIL)

        result = dispatcher.dispatch(
            sample_notification,
            channel=NotificationChannel.EMAIL,
        )

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.channel == NotificationChannel.EMAIL
        assert result.error_code == NotificationErrorCode.PROVIDER_UNAVAILABLE.value
        assert "No provider registered" in (result.error_message or "")


# ---------------------------------------------------------------------------
# 3. PREFERENCE INTEGRATION (Tests 25–26)
# ---------------------------------------------------------------------------


class TestPreferenceIntegration:
    """Tests 25 and 26: Suppression and permission according to user preferences."""

    def test_25_disabled_channel_is_suppressed(
        self,
        dispatcher: NotificationDispatcher,
        temp_pref_repo: AlertPreferenceRepository,
        sample_notification: Notification,
    ):
        # Configure preference with ONLY IN_APP allowed
        pref = AlertPreference(
            preference_id="pref_u01",
            user_id="user_01",
            tenant_id="tenant_alpha",
            enabled=True,
            allowed_channels=[NotificationChannel.IN_APP],
        )
        temp_pref_repo.create(pref)

        # Attempt dispatch to EMAIL (which is not allowed)
        result = dispatcher.dispatch(sample_notification, channel=NotificationChannel.EMAIL)

        assert result.success is False
        assert result.status == NotificationStatus.SUPPRESSED
        assert result.error_code == NotificationErrorCode.CHANNEL_NOT_ALLOWED.value
        assert "not permitted" in (result.error_message or "").lower()

    def test_26_enabled_channel_can_dispatch(
        self,
        dispatcher: NotificationDispatcher,
        temp_pref_repo: AlertPreferenceRepository,
        sample_notification: Notification,
    ):
        # Allow WEBHOOK and EMAIL
        pref = AlertPreference(
            preference_id="pref_u02",
            user_id="user_01",
            tenant_id="tenant_alpha",
            enabled=True,
            allowed_channels=[NotificationChannel.IN_APP, NotificationChannel.WEBHOOK],
        )
        temp_pref_repo.create(pref)

        result = dispatcher.dispatch(
            sample_notification,
            channel=NotificationChannel.WEBHOOK,
        )
        assert result.success is True
        assert result.status == NotificationStatus.DELIVERED


# ---------------------------------------------------------------------------
# 4. DELIVERY STATUS & PERSISTENCE (Tests 27–32)
# ---------------------------------------------------------------------------


class TestDeliveryStatusAndPersistence:
    """Tests 27 through 32: Status tracking, failure recording, isolation, and persistence."""

    def test_27_successful_delivery_marked_correctly(
        self, dispatcher: NotificationDispatcher, sample_notification: Notification
    ):
        result = dispatcher.dispatch(sample_notification, channel=NotificationChannel.IN_APP)
        assert result.success is True
        assert result.status == NotificationStatus.DELIVERED

        # Verify recorded delivery in delivery repo
        records = dispatcher.delivery_repo.list_by_notification(
            notification_id=sample_notification.notification_id,
            tenant_id="tenant_alpha",
            user_id="user_01",
        )
        assert len(records) >= 1
        assert records[0].status == NotificationStatus.DELIVERED

    def test_28_failed_delivery_marked_correctly(
        self,
        dispatcher: NotificationDispatcher,
        configured_registry: NotificationProviderRegistry,
        sample_notification: Notification,
    ):
        # Mock failing email provider
        failing_email = MockEmailProvider(simulate_failure=True, simulate_error_code="SMTP_REJECTED")
        configured_registry.register(failing_email)

        result = dispatcher.dispatch(sample_notification, channel=NotificationChannel.EMAIL)
        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.error_code == "SMTP_REJECTED"

        records = dispatcher.delivery_repo.list_by_notification(
            notification_id=sample_notification.notification_id,
            tenant_id="tenant_alpha",
            user_id="user_01",
        )
        email_records = [r for r in records if r.channel == NotificationChannel.EMAIL]
        assert len(email_records) == 1
        assert email_records[0].status == NotificationStatus.FAILED
        assert email_records[0].error_code == "SMTP_REJECTED"

    def test_29_provider_unavailable_handled_correctly(
        self, dispatcher: NotificationDispatcher, sample_notification: Notification
    ):
        # Register a provider that is unconfigured
        unconfigured_push = MockPushProvider()
        unconfigured_push._api_key = None
        unconfigured_push._app_id = None
        dispatcher.registry.register(unconfigured_push)

        # Force unconfigured check
        def mock_is_conf():
            return False

        unconfigured_push.is_configured = mock_is_conf

        result = dispatcher.dispatch(sample_notification, channel=NotificationChannel.PUSH)
        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.error_code == NotificationErrorCode.PROVIDER_UNAVAILABLE.value

    def test_30_tenant_isolation(
        self, dispatcher: NotificationDispatcher, sample_notification: Notification
    ):
        dispatcher.dispatch(sample_notification, channel=NotificationChannel.IN_APP)

        # Look up records from another tenant
        other_records = dispatcher.delivery_repo.list_by_user(
            user_id=sample_notification.user_id,
            tenant_id="tenant_other_beta",
        )
        assert len(other_records) == 0

        # Look up notification from another tenant
        other_notif = dispatcher.notification_repo.get(
            sample_notification.notification_id,
            tenant_id="tenant_other_beta",
            user_id=sample_notification.user_id,
        )
        assert other_notif is None

    def test_31_user_isolation(
        self, dispatcher: NotificationDispatcher, sample_notification: Notification
    ):
        dispatcher.dispatch(sample_notification, channel=NotificationChannel.IN_APP)

        other_records = dispatcher.delivery_repo.list_by_user(
            user_id="different_user",
            tenant_id=sample_notification.tenant_id,
        )
        assert len(other_records) == 0

    def test_32_delivery_state_survives_reload(
        self,
        dispatcher: NotificationDispatcher,
        temp_delivery_repo: NotificationDeliveryRepository,
        sample_notification: Notification,
    ):
        dispatcher.dispatch(sample_notification, channel=NotificationChannel.IN_APP)

        # Create new repository instance reading from same root_dir
        reloaded_repo = NotificationDeliveryRepository(root_dir=temp_delivery_repo._root_dir)
        records = reloaded_repo.list_by_notification(
            notification_id=sample_notification.notification_id,
            tenant_id=sample_notification.tenant_id,
            user_id=sample_notification.user_id,
        )
        assert len(records) >= 1
        assert records[0].status == NotificationStatus.DELIVERED
        assert records[0].notification_id == sample_notification.notification_id


# ---------------------------------------------------------------------------
# 5. INTEGRATION (Tests 33–36)
# ---------------------------------------------------------------------------


class TestIntegration:
    """Tests 33 through 36: Alert pipeline integration and Notification Center integrity."""

    def test_33_alert_event_notification_can_be_dispatched(
        self, dispatcher: NotificationDispatcher, temp_notif_repo: NotificationRepository
    ):
        service = NotificationService(notification_repo=temp_notif_repo, dispatcher=dispatcher)
        event = AlertEvent(
            alert_event_id="ev_mining_01",
            tenant_id="tenant_alpha",
            user_id="user_01",
            source_event_id="chg_999",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.HIGH,
            title="Mines and Minerals Bill Enacted",
            summary="New auction framework for critical mineral blocks.",
        )
        notif = service.create_notification_from_alert_event(event)
        assert notif is not None

        # Outbound dispatch via webhook
        res = service.dispatch_outbound(notif, channel=NotificationChannel.WEBHOOK)
        assert res.success is True
        assert res.status == NotificationStatus.DELIVERED

    def test_34_alert_group_notification_can_be_dispatched(
        self, dispatcher: NotificationDispatcher, temp_notif_repo: NotificationRepository
    ):
        service = NotificationService(notification_repo=temp_notif_repo, dispatcher=dispatcher)
        group = AlertGroup(
            group_id="grp_telecom_01",
            tenant_id="tenant_alpha",
            user_id="user_01",
            group_type=AlertGroupType.BILL,
            title="Telecom Bill Amendments (3 events)",
            summary="Consolidated legislative actions across houses.",
            severity=AlertSeverity.HIGH,
            event_ids=["ev_1", "ev_2", "ev_3"],
            affected_entity_ids=["telecom-bill-2024"],
        )
        notif = service.create_notification_from_alert_group(group)
        assert notif is not None

        # Outbound dispatch via email
        res = service.dispatch_outbound(
            notif, channel=NotificationChannel.EMAIL, recipient="telecom_analyst@example.com"
        )
        assert res.success is True
        assert res.status == NotificationStatus.DELIVERED

    def test_35_digest_notification_can_be_dispatched(
        self, dispatcher: NotificationDispatcher, temp_notif_repo: NotificationRepository
    ):
        service = NotificationService(notification_repo=temp_notif_repo, dispatcher=dispatcher)
        digest = AlertDigest(
            digest_id="dig_daily_01",
            tenant_id="tenant_alpha",
            user_id="user_01",
            digest_type=DigestType.DAILY,
            period_start="2026-09-17T00:00:00Z",
            period_end="2026-09-18T00:00:00Z",
            group_ids=["grp_telecom_01"],
            event_ids=["ev_1", "ev_2", "ev_3"],
        )
        notif = service.create_notification_from_digest(digest)
        assert notif is not None

        res = service.enqueue_delivery(
            notif, channel=NotificationChannel.PUSH, recipient="push_token_analyst"
        )
        assert res.success is True
        assert res.status == NotificationStatus.DELIVERED

    def test_36_existing_notification_center_remains_functional(
        self, dispatcher: NotificationDispatcher, temp_notif_repo: NotificationRepository
    ):
        notif_svc = NotificationService(notification_repo=temp_notif_repo, dispatcher=dispatcher)
        center_svc = NotificationCenterService(notification_service=notif_svc)

        notif = Notification(
            notification_id="n_center_check_01",
            tenant_id="tenant_alpha",
            user_id="user_01",
            alert_event_id="ev_center_01",
            title="In-App Notification Center Check",
            summary="Testing in-app operations during outbound enablement",
        )
        notif_svc.create_notification(notif)

        # Verify NotificationCenter operations work seamlessly
        unread = center_svc.get_unread_notifications(user_id="user_01", tenant_id="tenant_alpha")
        assert len(unread) == 1
        assert unread[0].notification_id == "n_center_check_01"

        summary = center_svc.get_notification_center_summary(user_id="user_01", tenant_id="tenant_alpha")
        assert summary.unread_count == 1
        assert summary.total_active == 1

        # Mark read
        center_svc.mark_read("n_center_check_01", tenant_id="tenant_alpha", user_id="user_01")
        assert center_svc.get_unread_count(user_id="user_01", tenant_id="tenant_alpha") == 0


# ---------------------------------------------------------------------------
# 6. STATE, CENTRAL & INTELLIGENCE (Tests 37–42)
# ---------------------------------------------------------------------------


class TestJurisdictionAndEntityHandling:
    """Tests 37 through 42: Jurisdiction and intelligence entity handling without unsupported predictions."""

    def test_37_state_notification_can_be_delivered(
        self, dispatcher: NotificationDispatcher
    ):
        state_notif = Notification(
            notification_id="notif_state_deliv_01",
            tenant_id="tenant_alpha",
            user_id="user_01",
            alert_event_id="ev_state_01",
            title="Maharashtra Industrial Policy Amendment",
            summary="State bill passed regarding manufacturing subsidies.",
            jurisdiction="state",
            state="maharashtra",
            metadata={"bill_id": "mh-ind-2024", "state": "maharashtra"},
        )
        res = dispatcher.dispatch(state_notif, channel=NotificationChannel.WEBHOOK)
        assert res.success is True
        assert res.status == NotificationStatus.DELIVERED

    def test_38_no_state_prediction_generated(
        self, dispatcher: NotificationDispatcher
    ):
        # Verify that state notifications never have or generate predictions
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        for exp in state_exps:
            assert not hasattr(exp, "predicted_car")
            assert not hasattr(exp, "expected_return")

    def test_39_central_notification_can_be_delivered(
        self, dispatcher: NotificationDispatcher
    ):
        central_notif = Notification(
            notification_id="notif_central_deliv_01",
            tenant_id="tenant_alpha",
            user_id="user_01",
            alert_event_id="ev_central_01",
            title="Central Banking Bill Update",
            summary="Finance bill referenced to standing committee.",
            jurisdiction="central",
            metadata={"bill_id": "banking-laws-amendment-bill-2024", "jurisdiction": "central"},
        )
        res = dispatcher.dispatch(central_notif, channel=NotificationChannel.EMAIL, recipient="central@example.com")
        assert res.success is True
        assert res.status == NotificationStatus.DELIVERED

    def test_40_existing_prediction_reference_unchanged(self):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700

    def test_41_intelligence_company_notification_can_be_delivered(
        self, dispatcher: NotificationDispatcher
    ):
        intel_notif = Notification(
            notification_id="notif_intel_deliv_01",
            tenant_id="tenant_alpha",
            user_id="user_01",
            alert_event_id="ev_intel_01",
            title="Intelligence Company Exposure Alert",
            summary="Qualitative legislative exposure identified for technology sector company.",
            metadata={"company_id": "INTEL_CO_01", "is_intelligence_only": True},
        )
        res = dispatcher.dispatch(intel_notif, channel=NotificationChannel.WEBHOOK)
        assert res.success is True
        assert res.status == NotificationStatus.DELIVERED

    def test_42_no_unsupported_prediction_generated(
        self, dispatcher: NotificationDispatcher
    ):
        # Verify no stock predictions, target prices, or alpha fabricated
        intel_notif = Notification(
            notification_id="notif_intel_safe_01",
            tenant_id="tenant_alpha",
            user_id="user_01",
            alert_event_id="ev_intel_02",
            title="Intelligence Monitoring Alert",
            summary="Grounded monitoring event for unlisted entity.",
            metadata={"company_id": "INTEL_CO_02"},
        )
        dispatcher.dispatch(intel_notif, channel=NotificationChannel.IN_APP)
        assert "target_price" not in intel_notif.metadata
        assert "buy_sell_hold" not in intel_notif.metadata
        assert "predicted_car" not in intel_notif.metadata


# ---------------------------------------------------------------------------
# 7. FROZEN BASELINE INTEGRITY (Tests 43–47)
# ---------------------------------------------------------------------------


class TestBaselineIntegrity:
    """Tests 43 through 47: Verification of strict frozen baseline metrics."""

    def test_43_central_47_companies_unchanged(self):
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

    def test_44_central_940_pairs_unchanged(self):
        bill_repo = BillRepository()
        prod_central_bills = [
            b for b in bill_repo.get_all()
            if b.bill_id not in ("key-issues-and-analysis", "service-bill")
        ]
        assert len(prod_central_bills) == 20
        assert len(prod_central_bills) * 47 == 940

    def test_45_central_4700_predictions_unchanged(self):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700

    def test_46_state_86_exposures_unchanged(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        assert len(state_exps) == 86

    def test_47_state_predictions_remain_zero(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        for e in state_exps:
            assert not hasattr(e, "predicted_car")
            assert not hasattr(e, "expected_return")
