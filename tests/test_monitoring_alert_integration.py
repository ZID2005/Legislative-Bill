"""
tests/test_monitoring_alert_integration.py
==========================================
Integration test verifying the connection between legislative monitoring events
and the alert pipeline:
Monitoring Event -> Alert Matching -> AlertEvent -> Notification -> Workspace
"""

import pytest
from schemas.monitoring import ChangeEvent, ChangeEventType
from services.alert_pipeline_service import AlertPipelineService
from services.watchlist_service import WatchlistService
from storage.alert_event_repository import AlertEventRepository
from storage.notification_repository import NotificationRepository


def test_monitoring_event_generates_alert_and_notification():
    """Verify monitoring change event automatically triggers alert matching and in-app notification."""
    user_id = "user_mon_pipe_test"
    tenant_id = "tenant_mon_pipe_test"
    bill_id = "the-coastal-shipping-bill-2024"

    wl_service = WatchlistService()
    alert_repo = AlertEventRepository()
    notif_repo = NotificationRepository()

    # 1. User watches bill_1
    wl = wl_service.create_watchlist(tenant_id=tenant_id, user_id=user_id, name="Test Watchlist")
    wl_service.add_item(
        watchlist_id=wl.watchlist_id,
        entity_type="BILL",
        entity_id=bill_id,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    # 2. Add an alert rule for bill status changes
    wl_service.create_alert_rule(
        user_id=user_id,
        tenant_id=tenant_id,
        watchlist_id=wl.watchlist_id,
        alert_type="BILL_STATUS_CHANGE",
        minimum_severity="LOW",
        enabled=True,
    )

    # 3. Simulate incoming monitoring ChangeEvent
    change_event = ChangeEvent(
        source_id="prs_india",
        event_type=ChangeEventType.STATUS_CHANGED,
        bill_id=bill_id,
        bill_title="Electricity (Amendment) Bill, 2023",
        jurisdiction="central",
        field_name="status",
        old_value="introduced",
        new_value="passed_lok_sabha",
    )

    # 4. Process via AlertPipelineService
    pipeline = AlertPipelineService()
    result = pipeline.process_event(change_event)

    assert result.success is True
    # At least one alert event generated
    assert len(result.alert_events) >= 1
    # Check that notification was generated
    assert len(result.notifications) >= 1

    # Cleanup
    try:
        wl_service.deactivate_watchlist(wl.watchlist_id, tenant_id=tenant_id, user_id=user_id)
        for ae in result.alert_events:
            alert_repo.delete(ae.alert_event_id, tenant_id=tenant_id, user_id=user_id)
        for n in result.notifications:
            notif_repo.delete(n.notification_id)
    except Exception:
        pass
