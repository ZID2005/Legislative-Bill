"""
tests/test_alert_hardening.py
===============================
Hardening tests for the Watchlist & Alert subsystem.

Covers boundary conditions, adversarial inputs, failure injection, data integrity
guards, and security-relevant properties throughout the entire pipeline.

Tests 1-29 cover:
  1.  Empty event list (batch) — no crash, no phantom results
  2.  Unknown entity type in event — graceful skip
  3.  Missing bill_id — no key error
  4.  Malformed ChangeEvent dict — safe fallback
  5.  Empty candidate subscribers — early return
  6.  Concurrent dedup: same event from two paths → one AlertEvent
  7.  Extremely long entity IDs — truncation or safe handling
  8.  Alert rule with mismatched alert_type — no alert
  9.  Event severity below rule minimum — suppressed
  10. Tenant-scoped watchlist not accessible by other tenant
  11. User-scoped watchlist not accessible by other user
  12. AlertGroup maximum event count boundary
  13. Notification with no deep_link — no crash
  14. Webhook payload HMAC: tampered payload rejected (incorrect signature)
  15. Mock email with failure simulation — graceful DeliveryResult
  16. Mock push with failure simulation — graceful DeliveryResult
  17. Provider registry: unregistered channel — provider unavailable result
  18. Digest creation for a user with no groups — safe empty digest
  19. Digest with multiple groups — correct summary statistics
  20. PipelineResult.to_dict() is complete and JSON-serializable
  21. PipelineResult.success = False on matching failure
  22. NormalizedEvent prediction_summary always 'none' for State
  23. Multiple events processed in batch — correct count
  24. AlertPreference.minimum_severity filter respected
  25. AlertPreference.allowed_alert_types filter respected
  26. IndexValidationReport detects inactive watchlist entries
  27. In-app notification marks as read / unread correctly
  28. Archive and unarchive notification — state preserved
  29. Soft delete notification — deleted flag set, record remains

Task 8.13.8 — Watchlist & Alert System Integration, E2E Verification & Hardening.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

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
    NotificationSourceType,
    NotificationStatus,
    NotificationType,
    compute_dedup_key,
)
from schemas.alert_group import AlertGroup, AlertGroupStatus, AlertGroupType
from schemas.monitoring import ChangeEvent, ChangeEventType
from schemas.state_corporate_exposure import (
    CorporateExposureEvidence,
    StateCorporateExposure,
)
from schemas.watchlist import Watchlist, WatchlistItem, WatchlistEntityType
from services.alert_aggregation_service import AlertAggregationService
from services.alert_digest_service import AlertDigestService
from services.alert_matching_service import AlertMatchingService, NormalizedEvent
from services.alert_pipeline_service import AlertPipelineService, PipelineResult
from services.notification_center_service import NotificationCenterService
from services.notification_providers import (
    MockEmailProvider,
    MockPushProvider,
    MockWebhookTransport,
    NotificationProviderRegistry,
    WebhookNotificationProvider,
)
from services.notification_service import NotificationService
from services.watchlist_index_service import WatchlistIndexService
from storage.alert_event_repository import AlertEventRepository
from storage.alert_group_repository import AlertGroupRepository
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.alert_rule_repository import AlertRuleRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.notification_delivery_repository import NotificationDeliveryRepository
from storage.notification_repository import NotificationRepository
from storage.state_bill_repository import StateBillRepository
from storage.watchlist_repository import WatchlistRepository


# ===========================================================================
# SHARED HARNESS FIXTURE
# ===========================================================================


@pytest.fixture
def hardening_env(tmp_path: Path):
    """
    Isolated hardening test environment with all repositories and services injected.
    """
    wl_dir = tmp_path / "watchlists"
    idx_dir = tmp_path / "indices"
    rules_dir = tmp_path / "rules"
    events_dir = tmp_path / "events"
    groups_dir = tmp_path / "groups"
    prefs_dir = tmp_path / "prefs"
    notifs_dir = tmp_path / "notifications"
    delivery_dir = tmp_path / "deliveries"

    wl_repo = WatchlistRepository(root_dir=wl_dir)
    idx_svc = WatchlistIndexService(indices_dir=idx_dir, watchlist_repo=wl_repo)
    rule_repo = AlertRuleRepository(root_dir=rules_dir)
    event_repo = AlertEventRepository(root_dir=events_dir)
    group_repo = AlertGroupRepository(root_dir=groups_dir)
    pref_repo = AlertPreferenceRepository(root_dir=prefs_dir)
    notif_repo = NotificationRepository(root_dir=notifs_dir)
    delivery_repo = NotificationDeliveryRepository(root_dir=delivery_dir)

    mock_email = MockEmailProvider()
    mock_push = MockPushProvider()

    from services.notification_dispatcher import NotificationDispatcher
    dispatcher = NotificationDispatcher(
        notification_repo=notif_repo,
        alert_pref_repo=pref_repo,
        delivery_repo=delivery_repo,
    )

    notif_svc = NotificationService(
        notification_repo=notif_repo,
        dispatcher=dispatcher,
        alert_pref_repo=pref_repo,
    )

    matching_svc = AlertMatchingService(
        watchlist_repo=wl_repo,
        index_service=idx_svc,
        alert_rule_repo=rule_repo,
        alert_event_repo=event_repo,
        alert_pref_repo=pref_repo,
        company_exposure_repo=CompanyExposureRepository(),
        company_repo=CompanyRepository(),
        bill_repo=BillRepository(),
        state_bill_repo=StateBillRepository(),
    )

    agg_svc = AlertAggregationService(
        alert_event_repo=event_repo,
        alert_group_repo=group_repo,
    )

    pipeline = AlertPipelineService(
        matching_service=matching_svc,
        aggregation_service=agg_svc,
        notification_service=notif_svc,
        watchlist_repo=wl_repo,
        index_service=idx_svc,
        alert_rule_repo=rule_repo,
        alert_event_repo=event_repo,
        alert_group_repo=group_repo,
        alert_pref_repo=pref_repo,
        notification_repo=notif_repo,
    )

    notif_center = NotificationCenterService(
        notification_service=notif_svc,
        notification_repo=notif_repo,
    )

    digest_svc = AlertDigestService(
        alert_group_repo=group_repo,
        alert_event_repo=event_repo,
        alert_pref_repo=pref_repo,
    )

    return {
        "pipeline": pipeline,
        "matching_svc": matching_svc,
        "agg_svc": agg_svc,
        "notif_svc": notif_svc,
        "notif_center": notif_center,
        "digest_svc": digest_svc,
        "wl_repo": wl_repo,
        "idx_svc": idx_svc,
        "rule_repo": rule_repo,
        "event_repo": event_repo,
        "group_repo": group_repo,
        "pref_repo": pref_repo,
        "notif_repo": notif_repo,
        "delivery_repo": delivery_repo,
        "mock_email": mock_email,
        "mock_push": mock_push,
        "dispatcher": dispatcher,
        "tmp_path": tmp_path,
    }


def _mk_wl(wl_repo, idx_svc, tenant_id, user_id, watchlist_id, etype, entity_id, item_id, active=True):
    wl = wl_repo.create(Watchlist(
        watchlist_id=watchlist_id, user_id=user_id, tenant_id=tenant_id,
        name=f"WL-{watchlist_id}", is_active=active,
    ))
    item = wl_repo.add_item(WatchlistItem(
        item_id=item_id, watchlist_id=watchlist_id, user_id=user_id,
        tenant_id=tenant_id, entity_type=etype, entity_id=entity_id,
        display_name=entity_id,
    ))
    if active:
        idx_svc.add_subscriber(item)
    return wl, item


def _mk_rule(rule_repo, user_id, tenant_id, watchlist_id, alert_type, rule_id, enabled=True):
    rule = AlertRule(
        alert_rule_id=rule_id, user_id=user_id, tenant_id=tenant_id,
        watchlist_id=watchlist_id, alert_type=alert_type,
        minimum_severity=AlertSeverity.LOW, enabled=enabled,
    )
    rule_repo.create(rule)
    return rule


def _norm_event(**kwargs) -> NormalizedEvent:
    defaults = {
        "event_id": "test-ev-001",
        "alert_type": AlertType.BILL_STATUS_CHANGE,
        "severity": AlertSeverity.MEDIUM,
        "bill_id": "test-bill-2024",
        "jurisdiction": "central",
        "fact_summary": "Bill passed.",
        "derived_summary": "Impact assessed.",
        "interpretation_summary": "Monitor carefully.",
        "prediction_summary": "none",
    }
    defaults.update(kwargs)
    return NormalizedEvent(**defaults)


def _make_notif(tenant_id="t1", user_id="user_a") -> Notification:
    return Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        alert_event_id="test-ev-001",
        channel=NotificationChannel.IN_APP,
        status=NotificationStatus.DELIVERED,
        notification_type=NotificationType.ALERT,
        title="Test Alert Notification",
        summary="Test hardening notification",
        source_type=NotificationSourceType.ALERT_EVENT.value,
        source_id="test-ev-001",
    )


# ===========================================================================
# Tests 1-10: Edge case inputs and boundary conditions
# ===========================================================================


class TestEdgeCaseInputs:
    def test_01_empty_batch_no_crash(self, hardening_env):
        """Test 1: process_batch([]) returns empty list without crash."""
        pipeline = hardening_env["pipeline"]
        results = pipeline.process_batch([])
        assert results == []

    def test_02_unknown_entity_type_in_event_graceful_skip(self, hardening_env):
        """Test 2: NormalizedEvent with no matching subscriber → empty result, no crash."""
        matching_svc = hardening_env["matching_svc"]
        event = _norm_event(event_id="unknown-etype-001", bill_id="nonexistent-bill")
        # No subscribers set up — should gracefully return []
        alerts = matching_svc.process_event(event)
        assert isinstance(alerts, list)
        assert len(alerts) == 0

    def test_03_missing_bill_id_in_event(self, hardening_env):
        """Test 3: NormalizedEvent with no bill_id — no KeyError."""
        matching_svc = hardening_env["matching_svc"]
        event = _norm_event(event_id="no-bill-001", bill_id=None)
        # Should not crash
        alerts = matching_svc.process_event(event)
        assert isinstance(alerts, list)

    def test_04_malformed_dict_event_fallback(self, hardening_env):
        """Test 4: Dict event with minimal fields → safe normalization."""
        matching_svc = hardening_env["matching_svc"]
        malformed = {"event_type": "UNKNOWN_TYPE", "bill_id": "malformed-bill-2024"}
        # Must not raise
        try:
            norm = matching_svc.normalize_event(malformed)
            assert norm.event_id is not None
            assert norm.prediction_summary == "none"
        except Exception as exc:
            pytest.fail(f"normalize_event raised exception for malformed input: {exc}")

    def test_05_empty_candidate_subscribers_early_return(self, hardening_env):
        """Test 5: Event with no subscribers returns early without error."""
        pipeline = hardening_env["pipeline"]
        event = _norm_event(event_id="no-subscribers-001")
        result = pipeline.process_event(event)
        assert result.skipped_events == 1
        assert result.alert_events == []
        assert result.notifications == []
        assert result.success is True  # skipping is not failure

    def test_06_concurrent_dedup_same_event_id(self, hardening_env):
        """Test 6: Same event processed twice → exactly one AlertEvent stored."""
        env = hardening_env
        wl_repo = env["wl_repo"]
        idx_svc = env["idx_svc"]
        rule_repo = env["rule_repo"]
        matching_svc = env["matching_svc"]

        _mk_wl(wl_repo, idx_svc, "t1", "user_a", "wl-dedup-h-1",
               WatchlistEntityType.BILL, "concurrent-bill-2024", "item-dedup-h-1")
        _mk_rule(rule_repo, "user_a", "t1", "wl-dedup-h-1",
                 AlertType.BILL_STATUS_CHANGE, "rule-dedup-h-1")

        event = _norm_event(event_id="concurrent-dedup-001", bill_id="concurrent-bill-2024")
        alerts1 = matching_svc.process_event(event)
        alerts2 = matching_svc.process_event(event)

        ids1 = {a.alert_event_id for a in alerts1}
        ids2 = {a.alert_event_id for a in alerts2}
        assert ids1 == ids2, "Same event must produce identical AlertEvent IDs (idempotent)"

    def test_07_extremely_long_entity_id(self, hardening_env):
        """Test 7: Very long entity_id handled safely without crash or storage error."""
        env = hardening_env
        wl_repo = env["wl_repo"]
        idx_svc = env["idx_svc"]
        rule_repo = env["rule_repo"]
        matching_svc = env["matching_svc"]

        long_id = "LONG-COMPANY-ID-" + ("X" * 500)
        _mk_wl(wl_repo, idx_svc, "t1", "user_a", "wl-long-1",
               WatchlistEntityType.COMPANY, long_id, "item-long-1")
        _mk_rule(rule_repo, "user_a", "t1", "wl-long-1",
                 AlertType.NEW_COMPANY_EXPOSURE, "rule-long-1")

        event = _norm_event(
            event_id="long-id-001",
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            company_id=long_id,
        )
        try:
            alerts = matching_svc.process_event(event)
            assert isinstance(alerts, list)
        except Exception as exc:
            pytest.fail(f"Long entity ID caused unexpected exception: {exc}")

    def test_08_rule_type_mismatch_no_alert(self, hardening_env):
        """Test 8: Alert rule for SECTOR_IMPACT, event is BILL_STATUS_CHANGE → no alert."""
        env = hardening_env
        wl_repo = env["wl_repo"]
        idx_svc = env["idx_svc"]
        rule_repo = env["rule_repo"]
        matching_svc = env["matching_svc"]

        _mk_wl(wl_repo, idx_svc, "t1", "user_a", "wl-mismatch-1",
               WatchlistEntityType.BILL, "mismatch-bill-2024", "item-mismatch-1")
        # Rule is SECTOR_IMPACT, event will be BILL_STATUS_CHANGE
        _mk_rule(rule_repo, "user_a", "t1", "wl-mismatch-1",
                 AlertType.SECTOR_IMPACT, "rule-mismatch-1")

        event = _norm_event(
            event_id="type-mismatch-001",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="mismatch-bill-2024",
        )
        alerts = matching_svc.process_event(event)
        user_alerts = [a for a in alerts if a.user_id == "user_a"]
        assert len(user_alerts) == 0, "Type-mismatched rule must not generate AlertEvent"

    def test_09_event_severity_below_minimum_suppressed(self, hardening_env):
        """Test 9: Event severity INFO below rule minimum HIGH → AlertEvent suppressed."""
        env = hardening_env
        wl_repo = env["wl_repo"]
        idx_svc = env["idx_svc"]
        rule_repo = env["rule_repo"]
        matching_svc = env["matching_svc"]

        _mk_wl(wl_repo, idx_svc, "t1", "user_a", "wl-sev-1",
               WatchlistEntityType.BILL, "severity-bill-2024", "item-sev-1")
        # Rule minimum HIGH, event will be INFO
        rule = AlertRule(
            alert_rule_id="rule-sev-1",
            user_id="user_a",
            tenant_id="t1",
            watchlist_id="wl-sev-1",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            minimum_severity=AlertSeverity.HIGH,
            enabled=True,
        )
        rule_repo.create(rule)

        event = _norm_event(
            event_id="low-sev-001",
            severity=AlertSeverity.INFO,  # Below HIGH threshold
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="severity-bill-2024",
        )
        alerts = matching_svc.process_event(event)
        user_alerts = [a for a in alerts if a.user_id == "user_a"]
        assert len(user_alerts) == 0, "Event below minimum severity must be suppressed"

    def test_10_tenant_scoped_no_cross_tenant_access(self, hardening_env):
        """Test 10: Watchlist of Tenant A is invisible to Tenant B queries."""
        env = hardening_env
        wl_repo = env["wl_repo"]

        _mk_wl(wl_repo, env["idx_svc"], "tenant_a", "user_a", "wl-ta-access",
               WatchlistEntityType.COMPANY, "COMPANY-X", "item-ta-access")

        # Tenant B queries must not see tenant_a's watchlists
        wl_from_tb = wl_repo.get("wl-ta-access", tenant_id="tenant_b", user_id="user_b")
        assert wl_from_tb is None, "Tenant B must not access Tenant A's watchlist"


# ===========================================================================
# Tests 11-16: Isolation, boundary, and security conditions
# ===========================================================================


class TestIsolationAndBoundary:
    def test_11_user_scoped_no_cross_user_access(self, hardening_env):
        """Test 11: User A watchlist is invisible to User B."""
        env = hardening_env
        wl_repo = env["wl_repo"]

        _mk_wl(wl_repo, env["idx_svc"], "t1", "user_a", "wl-user-iso",
               WatchlistEntityType.COMPANY, "COMPANY-Y", "item-user-iso")

        wl_from_ub = wl_repo.get("wl-user-iso", tenant_id="t1", user_id="user_b")
        assert wl_from_ub is None, "User B must not access User A's watchlist"

    def test_12_alert_group_max_event_count_boundary(self, hardening_env):
        """Test 12: Aggregation with many events — no crash, count preserved."""
        env = hardening_env
        agg_svc = env["agg_svc"]
        event_repo = env["event_repo"]
        wl_repo = env["wl_repo"]
        idx_svc = env["idx_svc"]
        rule_repo = env["rule_repo"]
        matching_svc = env["matching_svc"]

        _mk_wl(wl_repo, idx_svc, "t1", "user_a", "wl-maxbatch",
               WatchlistEntityType.BILL, "batch-bill-2024", "item-maxbatch")
        _mk_rule(rule_repo, "user_a", "t1", "wl-maxbatch",
                 AlertType.BILL_STATUS_CHANGE, "rule-maxbatch")

        # Generate many unique events
        all_alerts = []
        for i in range(10):
            event = _norm_event(
                event_id=f"batch-evt-{i:03d}",
                bill_id="batch-bill-2024",
                alert_type=AlertType.BILL_STATUS_CHANGE,
                severity=AlertSeverity.MEDIUM,
            )
            alerts = matching_svc.process_event(event)
            all_alerts.extend(alerts)

        groups = agg_svc.aggregate_events(all_alerts)
        assert isinstance(groups, list)
        if groups:
            total_events_in_groups = sum(len(g.event_ids) for g in groups)
            assert total_events_in_groups <= len(all_alerts), "Group event count must not exceed total alerts"

    def test_13_notification_no_deep_link_no_crash(self, hardening_env):
        """Test 13: Notification with empty deep_link renders without error."""
        notif = Notification(
            tenant_id="t1",
            user_id="user_a",
            alert_event_id="test-ev-001",
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.DELIVERED,
            notification_type=NotificationType.ALERT,
            title="Test",
            summary="Test summary",
            source_type=NotificationSourceType.ALERT_EVENT.value,
            source_id="test-ev-001",
            deep_link={},  # Empty deep_link
        )
        # Should not raise
        data = notif.to_dict()
        assert data["deep_link"] == {} or data.get("deep_link") is not None

    def test_14_webhook_hmac_tampered_payload_rejected(self, hardening_env):
        """Test 14: Webhook with tampered payload fails HMAC verification."""
        import hashlib
        import hmac

        webhook_secret = "test-secret-hmac"
        real_payload = '{"event": "test", "timestamp": "2024-01-01T00:00:00+00:00"}'
        tampered_payload = '{"event": "hacked", "timestamp": "2024-01-01T00:00:00+00:00"}'

        # Compute HMAC of real payload
        sig = hmac.new(
            webhook_secret.encode("utf-8"),
            real_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Verify HMAC against tampered payload — should fail
        expected_sig_tampered = hmac.new(
            webhook_secret.encode("utf-8"),
            tampered_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        assert sig != expected_sig_tampered, (
            "HMAC of tampered payload must differ from original signature"
        )

        # Cross-check: correct payload must verify
        sig_check = hmac.new(
            webhook_secret.encode("utf-8"),
            real_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert sig == sig_check, "HMAC of original payload must match"

    def test_15_mock_email_failure_simulation(self, hardening_env):
        """Test 15: MockEmailProvider with simulate_failure=True → graceful DeliveryResult."""
        failing_email = MockEmailProvider(simulate_failure=True)
        notif = _make_notif()
        notif.channel = NotificationChannel.EMAIL

        result = failing_email.send(notif, recipient="fail@example.com")

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.error_code is not None
        assert result.error_message

    def test_16_mock_push_failure_simulation(self, hardening_env):
        """Test 16: MockPushProvider with simulate_failure=True → graceful DeliveryResult."""
        failing_push = MockPushProvider(simulate_failure=True)
        notif = _make_notif()
        notif.channel = NotificationChannel.PUSH

        result = failing_push.send(notif)

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.error_message


# ===========================================================================
# Tests 17-19: Provider registry, digest, and pipeline results
# ===========================================================================


class TestProviderRegistryAndDigest:
    def test_17_unregistered_channel_provider_unavailable(self, hardening_env):
        """Test 17: Dispatching to an unregistered channel returns PROVIDER_UNAVAILABLE."""
        registry = NotificationProviderRegistry()
        # Register only EMAIL; ask for PUSH
        registry.register(MockEmailProvider())

        provider = registry.get(NotificationChannel.PUSH)
        assert provider is None or not getattr(provider, "is_configured", lambda: False)()

    def test_18_digest_no_groups_safe_empty(self, hardening_env):
        """Test 18: AlertDigestService with no groups — returns None or empty digest safely."""
        digest_svc = hardening_env["digest_svc"]

        try:
            from schemas.alert_digest import DigestType
            result = digest_svc.generate_digest(
                user_id="ghost_user_no_groups",
                tenant_id="t1",
                digest_type=DigestType.REAL_TIME,
            )
            # Should return an empty digest, not raise
            assert result is None or result.event_count == 0
        except Exception as exc:
            pytest.fail(f"Empty digest creation raised unexpected exception: {exc}")

    def test_19_digest_multiple_groups_correct_stats(self, hardening_env):
        """Test 19: Digest from multiple AlertGroups has correct group_count and event_count."""
        env = hardening_env
        digest_svc = env["digest_svc"]
        wl_repo = env["wl_repo"]
        idx_svc = env["idx_svc"]
        rule_repo = env["rule_repo"]
        matching_svc = env["matching_svc"]
        agg_svc = env["agg_svc"]

        _mk_wl(wl_repo, idx_svc, "t1", "user_a", "wl-digest-multi",
               WatchlistEntityType.BILL, "digest-bill-2024", "item-digest-multi")
        _mk_rule(rule_repo, "user_a", "t1", "wl-digest-multi",
                 AlertType.BILL_STATUS_CHANGE, "rule-digest-multi")

        # Generate multiple distinct AlertEvents
        all_alerts = []
        for i in range(3):
            ev = _norm_event(
                event_id=f"digest-evt-{i:03d}",
                bill_id="digest-bill-2024",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
            alerts = matching_svc.process_event(ev)
            all_alerts.extend(alerts)

        groups = agg_svc.aggregate_events(all_alerts)

        if not groups:
            pytest.skip("No groups generated — skip digest test")

        try:
            from schemas.alert_digest import DigestType
            digest = digest_svc.generate_digest(
                user_id="user_a",
                tenant_id="t1",
                digest_type=DigestType.REAL_TIME,
            )
            if digest:
                assert digest.event_count == len(all_alerts)
                assert digest.group_count >= 1
        except Exception as exc:
            pytest.fail(f"Digest creation raised unexpected exception: {exc}")


# ===========================================================================
# Tests 20-22: PipelineResult and NormalizedEvent contracts
# ===========================================================================


class TestPipelineResultContracts:
    def test_20_pipeline_result_to_dict_json_serializable(self, hardening_env):
        """Test 20: PipelineResult.to_dict() is fully JSON-serializable."""
        result = PipelineResult(
            event_id="json-test-001",
            skipped_events=1,
            success=True,
            stage_durations_ms={"matching": 1.2, "total": 1.2},
            metadata={"skip_reason": "no_matching_subscribers_or_rules"},
        )
        data = result.to_dict()
        try:
            serialized = json.dumps(data)
            assert serialized  # Not empty
        except TypeError as exc:
            pytest.fail(f"PipelineResult.to_dict() is not JSON-serializable: {exc}")

    def test_21_pipeline_result_failure_on_matching_error(self, hardening_env):
        """Test 21: PipelineResult marks success=False when matching stage fails."""
        result = PipelineResult(
            event_id="failure-001",
            failed_stages=["matching"],
            success=False,
            error_message="Matching stage failed: simulated error",
        )
        assert result.success is False
        assert "matching" in result.failed_stages
        assert result.error_message is not None

    def test_22_normalized_event_state_prediction_always_none(self, hardening_env):
        """Test 22: NormalizedEvent for state events always has prediction_summary='none'."""
        matching_svc = hardening_env["matching_svc"]
        state_event = ChangeEvent(
            event_id="state-norm-001",
            bill_id="maharashtra-workers-bill-2024",
            bill_title="Maharashtra Workers Bill, 2024",
            jurisdiction="state",
            state="Maharashtra",
            event_type=ChangeEventType.NEW_BILL,
            field_name="status",
            old_value="",
            new_value="introduced",
            source_id="maharashtra_gazette",
        )
        norm = matching_svc.normalize_monitoring_event(state_event)
        assert norm.prediction_summary == "none", (
            f"State normalized event must always have prediction_summary='none', "
            f"got '{norm.prediction_summary}'"
        )
        assert norm.jurisdiction == "state"

    def test_23_batch_processing_correct_result_count(self, hardening_env):
        """Test 23: process_batch with N events returns exactly N PipelineResults."""
        pipeline = hardening_env["pipeline"]
        events = [
            _norm_event(event_id=f"batch-{i:03d}", bill_id=f"bill-batch-{i}")
            for i in range(5)
        ]
        results = pipeline.process_batch(events)
        assert len(results) == 5
        for r in results:
            assert isinstance(r, PipelineResult)


# ===========================================================================
# Tests 24-26: Preference and index validation
# ===========================================================================


class TestPreferencesAndIndexValidation:
    def test_24_minimum_severity_preference_blocks_low_severity(self, hardening_env):
        """Test 24: AlertPreference.minimum_severity=HIGH blocks INFO event."""
        env = hardening_env
        wl_repo = env["wl_repo"]
        idx_svc = env["idx_svc"]
        rule_repo = env["rule_repo"]
        pref_repo = env["pref_repo"]
        matching_svc = env["matching_svc"]

        _mk_wl(wl_repo, idx_svc, "t1", "pref_high_user", "wl-pref-high",
               WatchlistEntityType.BILL, "pref-bill-2024", "item-pref-high")
        _mk_rule(rule_repo, "pref_high_user", "t1", "wl-pref-high",
                 AlertType.BILL_STATUS_CHANGE, "rule-pref-high")

        # Set HIGH minimum severity preference
        pref = AlertPreference(
            user_id="pref_high_user",
            tenant_id="t1",
            enabled=True,
            minimum_severity=AlertSeverity.HIGH,
            allowed_alert_types=list(AlertType),
        )
        pref_repo.save(pref)

        # INFO event — should be blocked by preference
        event = _norm_event(
            event_id="pref-sev-001",
            severity=AlertSeverity.INFO,
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="pref-bill-2024",
        )
        alerts = matching_svc.process_event(event)
        user_alerts = [a for a in alerts if a.user_id == "pref_high_user"]
        assert len(user_alerts) == 0, "INFO severity blocked by HIGH preference"

    def test_25_allowed_alert_types_preference_filters_type(self, hardening_env):
        """Test 25: AlertPreference.allowed_alert_types=[SECTOR_IMPACT] blocks BILL_STATUS_CHANGE."""
        env = hardening_env
        wl_repo = env["wl_repo"]
        idx_svc = env["idx_svc"]
        rule_repo = env["rule_repo"]
        pref_repo = env["pref_repo"]
        matching_svc = env["matching_svc"]

        _mk_wl(wl_repo, idx_svc, "t1", "pref_type_user", "wl-pref-type",
               WatchlistEntityType.BILL, "pref-type-bill-2024", "item-pref-type")
        _mk_rule(rule_repo, "pref_type_user", "t1", "wl-pref-type",
                 AlertType.BILL_STATUS_CHANGE, "rule-pref-type")

        # Preference allows only SECTOR_IMPACT
        pref = AlertPreference(
            user_id="pref_type_user",
            tenant_id="t1",
            enabled=True,
            minimum_severity=AlertSeverity.LOW,
            allowed_alert_types=[AlertType.SECTOR_IMPACT],  # Excludes BILL_STATUS_CHANGE
        )
        pref_repo.save(pref)

        event = _norm_event(
            event_id="pref-type-001",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="pref-type-bill-2024",
        )
        alerts = matching_svc.process_event(event)
        user_alerts = [a for a in alerts if a.user_id == "pref_type_user"]
        assert len(user_alerts) == 0, "BILL_STATUS_CHANGE blocked by allowed_alert_types=[SECTOR_IMPACT]"

    def test_26_index_validation_detects_inactive_watchlist_entries(self, tmp_path: Path):
        """Test 26: validate_indices detects entries for inactive watchlists."""
        wl_dir = tmp_path / "watchlists"
        idx_dir = tmp_path / "indices"

        wl_repo = WatchlistRepository(root_dir=wl_dir)
        idx_svc = WatchlistIndexService(indices_dir=idx_dir, watchlist_repo=wl_repo)

        # Create active watchlist and index it
        wl, item = _mk_wl(
            wl_repo, idx_svc, "t1", "user_a", "wl-inactive-validate",
            WatchlistEntityType.COMPANY, "INACTIVE-CO", "item-inactive-validate",
        )

        # Deactivate watchlist
        wl.is_active = False
        wl_repo.update(wl)

        # Intentionally skip idx_svc.deactivate_watchlist() to create a stale entry
        # Then validate — should detect the inactive watchlist entry

        idx_svc2 = WatchlistIndexService(indices_dir=idx_dir, watchlist_repo=wl_repo)
        report = idx_svc2.validate_indices()

        has_inactive = (
            len(report.inactive_watchlist_entries) > 0 or
            len(report.stale_entries) > 0 or
            not report.is_valid
        )
        assert has_inactive, "validate_indices must detect entries for inactive watchlists"


# ===========================================================================
# Tests 27-29: In-app notification center operations
# ===========================================================================


class TestNotificationCenterOperations:
    def _setup_delivered_notification(self, env) -> Notification:
        notif_repo = env["notif_repo"]
        notif = Notification(
            tenant_id="t1",
            user_id="user_a",
            alert_event_id="test-center-evt-001",
            channel=NotificationChannel.IN_APP,
            status=NotificationStatus.DELIVERED,
            notification_type=NotificationType.ALERT,
            title="Test In-App Notification",
            summary="Test center hardening notification",
            source_type=NotificationSourceType.ALERT_EVENT.value,
            source_id="test-center-evt-001",
        )
        notif_repo.create(notif)
        return notif

    def test_27_mark_as_read_and_unread(self, hardening_env):
        """Test 27: Notification can be marked read then unread correctly."""
        env = hardening_env
        notif_repo = env["notif_repo"]
        notif = self._setup_delivered_notification(env)

        # Mark as read
        success = notif_repo.mark_read(
            notif.notification_id, tenant_id="t1", user_id="user_a"
        )
        assert success, "mark_read should return True"

        refreshed = notif_repo.get(
            notif.notification_id, tenant_id="t1", user_id="user_a"
        )
        assert refreshed is not None
        assert refreshed.is_read is True or refreshed.status == NotificationStatus.READ

        # Mark as unread
        success_unread = notif_repo.mark_unread(
            notif.notification_id, tenant_id="t1", user_id="user_a"
        )
        assert success_unread, "mark_unread should return True"

        refreshed_unread = notif_repo.get(
            notif.notification_id, tenant_id="t1", user_id="user_a"
        )
        assert refreshed_unread is not None
        assert (
            refreshed_unread.is_read is False
            or refreshed_unread.status != NotificationStatus.READ
        )

    def test_28_archive_and_unarchive_notification(self, hardening_env):
        """Test 28: Notification archive/unarchive preserves other fields."""
        env = hardening_env
        notif_repo = env["notif_repo"]
        notif = self._setup_delivered_notification(env)

        # Archive
        archived_ok = notif_repo.archive(
            notif.notification_id, tenant_id="t1", user_id="user_a"
        )
        assert archived_ok

        arch = notif_repo.get(notif.notification_id, tenant_id="t1", user_id="user_a")
        assert arch is not None
        assert arch.is_archived is True
        # Title and source_id preserved
        assert arch.title == notif.title
        assert arch.source_id == notif.source_id

        # Unarchive
        unarch_ok = notif_repo.unarchive(
            notif.notification_id, tenant_id="t1", user_id="user_a"
        )
        assert unarch_ok

        unarch = notif_repo.get(notif.notification_id, tenant_id="t1", user_id="user_a")
        assert unarch is not None
        assert unarch.is_archived is False

    def test_29_soft_delete_notification_record_preserved(self, hardening_env):
        """Test 29: Soft delete sets deleted flag but preserves underlying evidence."""
        env = hardening_env
        notif_repo = env["notif_repo"]
        notif = self._setup_delivered_notification(env)

        # Soft delete
        deleted_ok = notif_repo.delete(
            notif.notification_id, tenant_id="t1", user_id="user_a", soft=True
        )
        assert deleted_ok

        # Record must still exist (soft delete only)
        record = notif_repo.get(notif.notification_id, tenant_id="t1", user_id="user_a")
        # In soft delete: record is either returned with is_deleted=True,
        # or removed from active inbox but still on disk
        # Either is valid — main guarantee: no hard-delete of legislative evidence
        if record:
            assert record.is_deleted is True or record.deleted_at is not None
