"""
tests/test_webhook_provider.py
==============================
Unit and contract tests for WebhookNotificationProvider, payload versioning,
HMAC-SHA256 signing, URL validation, timeout/retry mechanics, and secret redaction.

Tests required by Task 8.13.7:
14. Valid webhook payload generated
15. Payload schema version present
16. HMAC signature deterministic
17. Signature changes when payload changes
18. Invalid URL rejected
19. Mock webhook transport succeeds
20. HTTP failure handled
21. Timeout handled
22. Retry limit respected
23. Secrets not logged
24. Idempotency key deterministic
"""

from __future__ import annotations

import json
import logging
import pytest

from schemas.alert import (
    AlertSeverity,
    Notification,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
)
from schemas.notification_delivery import (
    NotificationErrorCode,
    compute_delivery_key,
)
from services.notification_providers import (
    MockWebhookTransport,
    WebhookNotificationProvider,
    format_webhook_payload,
    generate_hmac_sha256_signature,
    validate_webhook_url,
)


@pytest.fixture
def sample_notification() -> Notification:
    return Notification(
        notification_id="notif_webhook_test_01",
        tenant_id="tenant_gamma",
        user_id="user_fin_analyst",
        alert_event_id="ev_bill_901",
        source_type="ALERT_EVENT",
        source_id="ev_bill_901",
        title="Banking Laws Amendment Bill Tabled",
        summary="Union Finance Minister introduced bill to amend RBI and Banking Regulation Acts.",
        notification_type=NotificationType.BILL_UPDATE,
        severity=AlertSeverity.HIGH,
        metadata={
            "bill_id": "banking-laws-amendment-bill-2024",
            "jurisdiction": "central",
            "webhook_secret_key_internal": "TOP_SECRET_WEBHOOK_KEY_12345",
        },
    )


class TestWebhookProvider:
    """Tests 14 through 24: Comprehensive webhook provider testing."""

    def test_14_valid_webhook_payload_generated(self, sample_notification: Notification):
        payload = format_webhook_payload(sample_notification)

        assert isinstance(payload, dict)
        assert payload["notification_id"] == "notif_webhook_test_01"
        assert payload["tenant_id"] == "tenant_gamma"
        assert payload["user_id"] == "user_fin_analyst"
        assert payload["source_type"] == "ALERT_EVENT"
        assert payload["source_id"] == "ev_bill_901"
        assert payload["title"] == sample_notification.title
        assert payload["summary"] == sample_notification.summary
        assert payload["severity"] == "HIGH"
        assert "created_at" in payload
        assert "deep_link" in payload
        # Secret metadata terms must be stripped
        assert "webhook_secret_key_internal" not in payload["metadata"]

    def test_15_payload_schema_version_present(self, sample_notification: Notification):
        payload = format_webhook_payload(sample_notification)
        assert "schema_version" in payload
        assert payload["schema_version"] == "1"

    def test_16_hmac_signature_deterministic(self):
        secret = "corp_secret_key_999"
        payload_str = '{"event_type":"notification.bill_update","notification_id":"notif_001"}'

        sig1 = generate_hmac_sha256_signature(secret, payload_str)
        sig2 = generate_hmac_sha256_signature(secret, payload_str)

        assert isinstance(sig1, str)
        assert len(sig1) == 64  # SHA256 hex digest length
        assert sig1 == sig2

    def test_17_signature_changes_when_payload_changes(self):
        secret = "corp_secret_key_999"
        payload1 = '{"title":"Bill Passed Committee"}'
        payload2 = '{"title":"Bill Rejected by Committee"}'

        sig1 = generate_hmac_sha256_signature(secret, payload1)
        sig2 = generate_hmac_sha256_signature(secret, payload2)

        assert sig1 != sig2

    def test_18_invalid_url_rejected(self, sample_notification: Notification):
        transport = MockWebhookTransport()
        provider = WebhookNotificationProvider(transport=transport, allow_http=False)

        # Empty URL
        res1 = provider.send(sample_notification, recipient="")
        assert res1.success is False
        assert res1.error_code == NotificationErrorCode.INVALID_DESTINATION.value

        # Non-HTTP protocol
        res2 = provider.send(sample_notification, recipient="ftp://example.com/webhook")
        assert res2.success is False
        assert res2.error_code == NotificationErrorCode.INVALID_DESTINATION.value

        # HTTP when allow_http=False
        res3 = provider.send(sample_notification, recipient="http://insecure.example.com/webhook")
        assert res3.success is False
        assert res3.error_code == NotificationErrorCode.INVALID_DESTINATION.value

        # Malformed URL
        res4 = provider.send(sample_notification, recipient="not_a_valid_url")
        assert res4.success is False
        assert res4.error_code == NotificationErrorCode.INVALID_DESTINATION.value

        # Transport was never called for invalid destinations
        assert len(transport.calls) == 0

    def test_19_mock_webhook_transport_succeeds(self, sample_notification: Notification):
        transport = MockWebhookTransport(default_status_code=200)
        provider = WebhookNotificationProvider(
            transport=transport,
            secret="whsec_123456789",
            default_destination_url="https://api.corporate.example/webhooks/incoming",
        )

        result = provider.send(sample_notification)

        assert result.success is True
        assert result.status == NotificationStatus.DELIVERED
        assert result.channel == NotificationChannel.WEBHOOK
        assert result.response_code == 200
        assert result.retry_count == 0
        assert len(transport.calls) == 1

        call = transport.calls[0]
        assert call["url"] == "https://api.corporate.example/webhooks/incoming"
        assert "X-Notification-Signature" in call["headers"]
        assert call["headers"]["X-Notification-Signature"].startswith("sha256=")
        assert "X-Notification-Idempotency-Key" in call["headers"]
        assert "X-Notification-Timestamp" in call["headers"]
        assert call["headers"]["X-Notification-Schema-Version"] == "1"

    def test_20_http_failure_handled(self, sample_notification: Notification):
        # 404 Not Found is a non-retryable client error
        transport = MockWebhookTransport(default_status_code=404)
        provider = WebhookNotificationProvider(
            transport=transport,
            default_destination_url="https://api.corporate.example/webhooks/not-found",
            max_retries=3,
        )

        result = provider.send(sample_notification)

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.response_code == 404
        assert result.error_code == NotificationErrorCode.HTTP_FAILURE.value
        # Client 404 error should not perform retries
        assert len(transport.calls) == 1

    def test_21_timeout_handled(self, sample_notification: Notification):
        transport = MockWebhookTransport(simulate_timeout=True)
        provider = WebhookNotificationProvider(
            transport=transport,
            default_destination_url="https://slow.corporate.example/webhooks",
            timeout=2,
            max_retries=2,
            retry_backoff=0.01,
        )

        result = provider.send(sample_notification)

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.error_code == NotificationErrorCode.TIMEOUT.value
        assert "timed out" in (result.error_message or "").lower()
        # Should have attempted 2 times (initial + 1 retry)
        assert len(transport.calls) == 2

    def test_22_retry_limit_respected(self, sample_notification: Notification):
        # 500 Internal Server Error retryable
        transport = MockWebhookTransport(default_status_code=500)
        provider = WebhookNotificationProvider(
            transport=transport,
            default_destination_url="https://failing.corporate.example/webhooks",
            max_retries=3,
            retry_backoff=0.01,
        )

        result = provider.send(sample_notification)

        assert result.success is False
        assert result.status == NotificationStatus.FAILED
        assert result.response_code == 500
        # Must exactly respect max_retries limit
        assert len(transport.calls) == 3
        assert result.retry_count == 2

    def test_23_secrets_not_logged(
        self, sample_notification: Notification, caplog: pytest.LogCaptureFixture
    ):
        secret_signing_key = "sensitive_hmac_secret_abcdef123456"
        transport = MockWebhookTransport(default_status_code=500)
        provider = WebhookNotificationProvider(
            transport=transport,
            secret=secret_signing_key,
            default_destination_url="https://api.corporate.example/webhooks",
            max_retries=1,
        )

        with caplog.at_level(logging.DEBUG):
            result = provider.send(sample_notification)

        # Verify secret signing key is never in log records
        for record in caplog.records:
            assert secret_signing_key not in record.message

        # Verify secret signing key is not in DeliveryResult
        assert secret_signing_key not in (result.error_message or "")
        for val in result.metadata.values():
            assert secret_signing_key not in str(val)

    def test_24_idempotency_key_deterministic(self, sample_notification: Notification):
        key1 = compute_delivery_key(
            tenant_id=sample_notification.tenant_id,
            user_id=sample_notification.user_id,
            notification_id=sample_notification.notification_id,
            channel=NotificationChannel.WEBHOOK,
        )
        key2 = compute_delivery_key(
            tenant_id=sample_notification.tenant_id,
            user_id=sample_notification.user_id,
            notification_id=sample_notification.notification_id,
            channel=NotificationChannel.WEBHOOK,
        )

        assert isinstance(key1, str)
        assert len(key1) == 64
        assert key1 == key2

        # Different channel produces different key
        key_email = compute_delivery_key(
            tenant_id=sample_notification.tenant_id,
            user_id=sample_notification.user_id,
            notification_id=sample_notification.notification_id,
            channel=NotificationChannel.EMAIL,
        )
        assert key1 != key_email
