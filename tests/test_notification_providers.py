"""
tests/test_notification_providers.py
====================================
Unit and contract tests for Email and Push notification providers.

Tests required by Task 8.13.7:
7. Mock email provider succeeds
8. Email provider failure handled
9. Email credentials are not logged
10. Unconfigured email provider does not claim success
11. Mock push provider succeeds
12. Push failure handled
13. Unconfigured push provider does not claim success
"""

from __future__ import annotations

import logging
import pytest

from schemas.alert import (
    AlertSeverity,
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from schemas.notification_delivery import NotificationErrorCode
from services.notification_providers import (
    EmailNotificationProvider,
    MockEmailProvider,
    MockPushProvider,
    PushNotificationProvider,
)


@pytest.fixture
def sample_notification() -> Notification:
    return Notification(
        notification_id="notif_test_provider_01",
        tenant_id="tenant_alpha",
        user_id="user_test_01",
        alert_event_id="event_123",
        title="Telecom Regulatory Policy Update",
        summary="Draft guidelines released for spectrum allocation.",
        notification_type=NotificationType.LEGISLATIVE_UPDATE,
        severity=AlertSeverity.HIGH,
        metadata={"category": "telecom", "confidential_api_token": "SUPER_SECRET_TOKEN_DO_NOT_LOG"},
    )


class TestEmailNotificationProvider:
    """Tests 7 through 10: Email provider behavior and safety."""

    def test_07_mock_email_provider_succeeds(self, sample_notification: Notification):
        provider = MockEmailProvider()
        assert provider.is_configured() is True
        assert provider.channel == NotificationChannel.EMAIL

        result = provider.send(
            sample_notification,
            recipient="analyst@example.com",
        )

        assert result.success is True
        assert result.status == NotificationStatus.DELIVERED
        assert result.channel == NotificationChannel.EMAIL
        assert result.response_code == 250
        assert result.error_code is None
        assert result.error_message is None
        assert len(provider.sent_emails) == 1
        assert provider.sent_emails[0]["recipient"] == "analyst@example.com"
        assert provider.sent_emails[0]["notification_id"] == sample_notification.notification_id

    def test_08_email_provider_failure_handled(self, sample_notification: Notification):
        provider = MockEmailProvider(
            simulate_failure=True,
            simulate_error_code=NotificationErrorCode.HTTP_FAILURE.value,
            simulate_error_message="SMTP 550 Mailbox unavailable",
        )

        result = provider.send(sample_notification, recipient="bad_address@example.com")

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.channel == NotificationChannel.EMAIL
        assert result.error_code == NotificationErrorCode.HTTP_FAILURE.value
        assert "SMTP 550" in (result.error_message or "")
        assert len(provider.sent_emails) == 0

    def test_09_email_credentials_are_not_logged(
        self, sample_notification: Notification, caplog: pytest.LogCaptureFixture
    ):
        secret_password = "very_secret_smtp_password_xyz999"
        provider = EmailNotificationProvider(
            smtp_host="smtp.sendgrid.net",
            smtp_port=587,
            api_key=secret_password,
            sender_email="alerts@legisintel.com",
        )

        with caplog.at_level(logging.DEBUG):
            result = provider.send(sample_notification, recipient="user@example.com")

        # Verify password/key is not in log messages
        for record in caplog.records:
            assert secret_password not in record.message

        # Verify password/key is not in result error message or metadata
        assert secret_password not in (result.error_message or "")
        for v in result.metadata.values():
            assert secret_password not in str(v)

    def test_10_unconfigured_email_provider_does_not_claim_success(
        self, sample_notification: Notification
    ):
        # Empty provider with no host or credentials
        provider = EmailNotificationProvider()
        assert provider.is_configured() is False

        result = provider.send(sample_notification, recipient="user@example.com")

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.channel == NotificationChannel.EMAIL
        assert result.error_code == NotificationErrorCode.PROVIDER_UNAVAILABLE.value
        assert "not configured" in (result.error_message or "").lower()
        # Never fabricate success message
        assert "sent successfully" not in (result.error_message or "").lower()


class TestPushNotificationProvider:
    """Tests 11 through 13: Push provider behavior and safety."""

    def test_11_mock_push_provider_succeeds(self, sample_notification: Notification):
        provider = MockPushProvider()
        assert provider.is_configured() is True
        assert provider.channel == NotificationChannel.PUSH

        result = provider.send(
            sample_notification,
            recipient="device_token_abc_123",
        )

        assert result.success is True
        assert result.status == NotificationStatus.DELIVERED
        assert result.channel == NotificationChannel.PUSH
        assert result.response_code == 200
        assert len(provider.sent_pushes) == 1
        assert provider.sent_pushes[0]["device_token"] == "device_token_abc_123"

    def test_12_push_failure_handled(self, sample_notification: Notification):
        provider = MockPushProvider(
            simulate_failure=True,
            simulate_error_code=NotificationErrorCode.AUTHENTICATION_FAILURE.value,
            simulate_error_message="Invalid device registration token",
        )

        result = provider.send(sample_notification, recipient="invalid_token")

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.channel == NotificationChannel.PUSH
        assert result.error_code == NotificationErrorCode.AUTHENTICATION_FAILURE.value
        assert "Invalid device registration token" in (result.error_message or "")
        assert len(provider.sent_pushes) == 0

    def test_13_unconfigured_push_provider_does_not_claim_success(
        self, sample_notification: Notification
    ):
        provider = PushNotificationProvider()
        assert provider.is_configured() is False

        result = provider.send(sample_notification, recipient="token_123")

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.channel == NotificationChannel.PUSH
        assert result.error_code == NotificationErrorCode.PROVIDER_UNAVAILABLE.value
        assert "not configured" in (result.error_message or "").lower()
