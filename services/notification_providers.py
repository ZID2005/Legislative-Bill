"""
services/notification_providers.py
===================================
Outbound notification delivery providers, channel adapters, and provider registry.

Supports:
- NotificationProvider: Abstract base contract for all channel providers.
- InAppNotificationProvider: Adapts in-app notification center persistence.
- EmailNotificationProvider & MockEmailProvider: Email delivery abstraction.
- PushNotificationProvider & MockPushProvider: Mobile/web push delivery abstraction.
- WebhookNotificationProvider & WebhookTransport: Secure HMAC-SHA256 signed webhook dispatch.
- NotificationProviderRegistry: Pluggable registry resolving providers per channel.

Task 8.13.7 — Outbound Notification Delivery Providers & Webhook Dispatch.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import hashlib
import hmac
import json
import time
from typing import Any, Optional
import urllib.parse

from config.logging_config import get_logger
from config.settings import settings
from schemas.alert import (
    AlertSeverity,
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from schemas.notification_delivery import (
    DeliveryResult,
    NotificationErrorCode,
    compute_delivery_key,
)
from storage.notification_repository import NotificationRepository

logger = get_logger(__name__)

WEBHOOK_SCHEMA_VERSION = "1"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Base Provider Contract
# ---------------------------------------------------------------------------


class NotificationProvider(ABC):
    """
    Abstract base class for all notification delivery providers.
    Decouples core notification dispatching from concrete vendor implementations.
    """

    @property
    @abstractmethod
    def channel(self) -> NotificationChannel:
        """The delivery channel supported by this provider."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Descriptive identifier for the provider implementation."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """True if the provider has all credentials and settings needed to operate."""
        ...

    @abstractmethod
    def send(
        self,
        notification: Notification,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        """
        Execute dispatch of the notification to the target recipient.

        Must return a structured DeliveryResult.
        Must NOT raise uncaught network exceptions or leak secrets.
        """
        ...


# ---------------------------------------------------------------------------
# In-App Provider Adapter
# ---------------------------------------------------------------------------


class InAppNotificationProvider(NotificationProvider):
    """
    Adapter routing IN_APP notifications through the existing NotificationRepository
    and In-App Notification Center infrastructure established in Task 8.13.6.
    """

    def __init__(self, notification_repo: Optional[NotificationRepository] = None) -> None:
        self.repo = notification_repo or NotificationRepository()

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.IN_APP

    @property
    def name(self) -> str:
        return "in_app_provider"

    def is_configured(self) -> bool:
        return True

    def send(
        self,
        notification: Notification,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        attempted_at = _utcnow_iso()
        notification.validate()

        notification.status = NotificationStatus.DELIVERED
        notification.delivered_at = _utcnow_iso()

        try:
            # Persist or update via repo
            try:
                self.repo.create(notification)
            except ValueError:
                self.repo.save(notification)

            return DeliveryResult(
                success=True,
                status=NotificationStatus.DELIVERED,
                channel=NotificationChannel.IN_APP,
                provider=self.name,
                response_code=200,
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
                metadata={"notification_id": notification.notification_id},
            )
        except Exception as e:
            logger.error("In-app delivery failed for %s: %s", notification.notification_id, e)
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=NotificationChannel.IN_APP,
                provider=self.name,
                error_code=NotificationErrorCode.CONFIGURATION_ERROR.value,
                error_message=str(e),
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )


# ---------------------------------------------------------------------------
# Email Provider Abstraction
# ---------------------------------------------------------------------------


class EmailNotificationProvider(NotificationProvider):
    """
    Email notification provider abstraction.

    Configured via environment/settings. If unconfigured, explicitly returns
    a PROVIDER_UNAVAILABLE result without claiming delivery or making network calls.
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        api_key: Optional[str] = None,
        sender_email: Optional[str] = None,
    ) -> None:
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._api_key = api_key
        self._sender_email = sender_email

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL

    @property
    def name(self) -> str:
        return "email_provider"

    def is_configured(self) -> bool:
        """True only if required email credentials/endpoints are set."""
        return bool(self._smtp_host or self._api_key)

    def send(
        self,
        notification: Notification,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        attempted_at = _utcnow_iso()

        # Explicit failure when unconfigured — never claim delivery
        if not self.is_configured():
            logger.info("Email dispatch requested but email provider is not configured.")
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=NotificationChannel.EMAIL,
                provider=self.name,
                error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
                error_message="Email provider is not configured. Outbound email delivery unavailable.",
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        # In production, a real transport integration (SMTP / SendGrid / SES) would execute here.
        # Credential variables are never logged.
        return DeliveryResult(
            success=False,
            status=NotificationStatus.FAILED,
            channel=NotificationChannel.EMAIL,
            provider=self.name,
            error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
            error_message="Production email transport not enabled in current environment.",
            attempted_at=attempted_at,
            completed_at=_utcnow_iso(),
            retry_count=0,
        )


class MockEmailProvider(EmailNotificationProvider):
    """
    In-memory mock email provider for deterministic, offline automated testing.
    Records dispatches without performing real network calls.
    """

    def __init__(
        self,
        simulate_failure: bool = False,
        simulate_error_code: Optional[str] = None,
        simulate_error_message: Optional[str] = None,
    ) -> None:
        super().__init__(smtp_host="mock.smtp.local", api_key="mock_key")
        self.simulate_failure = simulate_failure
        self.simulate_error_code = simulate_error_code or NotificationErrorCode.HTTP_FAILURE.value
        self.simulate_error_message = simulate_error_message or "Simulated email provider failure"
        self.sent_emails: list[dict[str, Any]] = []

    def is_configured(self) -> bool:
        return True

    def send(
        self,
        notification: Notification,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        attempted_at = _utcnow_iso()
        target_recipient = recipient or f"{notification.user_id}@example.com"

        if not self.is_configured():
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=NotificationChannel.EMAIL,
                provider=self.name,
                error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
                error_message="Email provider is not configured.",
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        if self.simulate_failure:
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=NotificationChannel.EMAIL,
                provider=self.name,
                error_code=self.simulate_error_code,
                error_message=self.simulate_error_message,
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        # Record sent email record (excluding any credentials)
        record = {
            "notification_id": notification.notification_id,
            "recipient": target_recipient,
            "title": notification.title,
            "summary": notification.summary,
            "timestamp": attempted_at,
        }
        self.sent_emails.append(record)

        return DeliveryResult(
            success=True,
            status=NotificationStatus.DELIVERED,
            channel=NotificationChannel.EMAIL,
            provider=self.name,
            response_code=250,
            attempted_at=attempted_at,
            completed_at=_utcnow_iso(),
            retry_count=0,
            metadata={"recipient": target_recipient},
        )


# ---------------------------------------------------------------------------
# Push Provider Abstraction
# ---------------------------------------------------------------------------


class PushNotificationProvider(NotificationProvider):
    """
    Push notification provider abstraction suitable for future mobile/web push.

    If unconfigured, explicitly returns PROVIDER_UNAVAILABLE.
    Does not require Firebase / APNs credentials during development.
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self._app_id = app_id
        self._api_key = api_key

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.PUSH

    @property
    def name(self) -> str:
        return "push_provider"

    def is_configured(self) -> bool:
        return bool(self._app_id and self._api_key)

    def send(
        self,
        notification: Notification,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        attempted_at = _utcnow_iso()

        if not self.is_configured():
            logger.info("Push dispatch requested but push provider is not configured.")
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=NotificationChannel.PUSH,
                provider=self.name,
                error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
                error_message="Push provider is not configured. Mobile/web push unavailable.",
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        return DeliveryResult(
            success=False,
            status=NotificationStatus.FAILED,
            channel=NotificationChannel.PUSH,
            provider=self.name,
            error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
            error_message="Production push transport not enabled in current environment.",
            attempted_at=attempted_at,
            completed_at=_utcnow_iso(),
            retry_count=0,
        )


class MockPushProvider(PushNotificationProvider):
    """
    In-memory mock push provider for offline automated testing.
    """

    def __init__(
        self,
        simulate_failure: bool = False,
        simulate_error_code: Optional[str] = None,
        simulate_error_message: Optional[str] = None,
    ) -> None:
        super().__init__(app_id="mock_app", api_key="mock_key")
        self.simulate_failure = simulate_failure
        self.simulate_error_code = simulate_error_code or NotificationErrorCode.HTTP_FAILURE.value
        self.simulate_error_message = simulate_error_message or "Simulated push provider failure"
        self.sent_pushes: list[dict[str, Any]] = []

    def is_configured(self) -> bool:
        return True

    def send(
        self,
        notification: Notification,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        attempted_at = _utcnow_iso()
        target_token = recipient or kwargs.get("device_token") or f"device_{notification.user_id}"

        if not self.is_configured():
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=NotificationChannel.PUSH,
                provider=self.name,
                error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
                error_message="Push provider is not configured.",
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        if self.simulate_failure:
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=NotificationChannel.PUSH,
                provider=self.name,
                error_code=self.simulate_error_code,
                error_message=self.simulate_error_message,
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        record = {
            "notification_id": notification.notification_id,
            "device_token": target_token,
            "title": notification.title,
            "summary": notification.summary,
            "timestamp": attempted_at,
        }
        self.sent_pushes.append(record)

        return DeliveryResult(
            success=True,
            status=NotificationStatus.DELIVERED,
            channel=NotificationChannel.PUSH,
            provider=self.name,
            response_code=200,
            attempted_at=attempted_at,
            completed_at=_utcnow_iso(),
            retry_count=0,
            metadata={"device_token": target_token},
        )


# ---------------------------------------------------------------------------
# Webhook Transport Abstraction & Mock Transport
# ---------------------------------------------------------------------------


class WebhookTransport(ABC):
    """
    Transport interface for executing HTTP POST requests for webhooks.
    Decoupled to ensure tests never make external network calls.
    """

    @abstractmethod
    def post(
        self,
        url: str,
        data: str,
        headers: dict[str, str],
        timeout: float,
    ) -> tuple[int, str]:
        """
        Execute HTTP POST.
        Returns tuple of (status_code, response_body).
        Raises TimeoutError on timeout, ConnectionError on network issue.
        """
        ...


class MockWebhookTransport(WebhookTransport):
    """
    In-memory mock transport for deterministic, offline testing of Webhook dispatch.
    Supports status code configuration, failure simulation, and retry sequences.
    """

    def __init__(
        self,
        default_status_code: int = 200,
        default_response_body: str = '{"status":"received"}',
        simulate_timeout: bool = False,
        simulate_connection_error: bool = False,
        status_code_sequence: Optional[list[int]] = None,
    ) -> None:
        self.default_status_code = default_status_code
        self.default_response_body = default_response_body
        self.simulate_timeout = simulate_timeout
        self.simulate_connection_error = simulate_connection_error
        self.status_code_sequence = list(status_code_sequence) if status_code_sequence else []
        self.calls: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        data: str,
        headers: dict[str, str],
        timeout: float,
    ) -> tuple[int, str]:
        # Record invocation
        self.calls.append({
            "url": url,
            "data": data,
            "headers": dict(headers),
            "timeout": timeout,
            "timestamp": _utcnow_iso(),
        })

        if self.simulate_timeout:
            raise TimeoutError(f"Connection to {url} timed out after {timeout} seconds")

        if self.simulate_connection_error:
            raise ConnectionError(f"Failed to connect to {url}")

        if self.status_code_sequence:
            code = self.status_code_sequence.pop(0)
            return code, f'{{"status":"code_{code}"}}'

        return self.default_status_code, self.default_response_body


# ---------------------------------------------------------------------------
# Webhook Security, Formatting & Provider
# ---------------------------------------------------------------------------


def generate_hmac_sha256_signature(secret: str, canonical_payload: str) -> str:
    """
    Compute cryptographic HMAC-SHA256 signature over the canonical webhook payload.
    """
    return hmac.new(
        secret.encode("utf-8"),
        canonical_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def format_webhook_payload(
    notification: Notification,
    schema_version: str = WEBHOOK_SCHEMA_VERSION,
) -> dict[str, Any]:
    """
    Construct a deterministic, minimised webhook payload adhering to Task 8.13.7 specs.
    Never includes internal model internals or credentials.
    """
    sev_str = (
        notification.severity.value
        if isinstance(notification.severity, AlertSeverity)
        else (str(notification.severity) if notification.severity else None)
    )

    clean_meta: dict[str, Any] = {}
    for k, v in (notification.metadata or {}).items():
        # Exclude internal/secret keys
        if any(secret_term in k.lower() for secret_term in ("secret", "token", "key", "password", "auth")):
            continue
        clean_meta[k] = v

    return {
        "schema_version": schema_version,
        "event_type": f"notification.{notification.notification_type.value.lower()}",
        "notification_id": notification.notification_id,
        "source_type": notification.source_type,
        "source_id": notification.source_id,
        "tenant_id": notification.tenant_id,
        "user_id": notification.user_id,
        "title": notification.title,
        "summary": notification.summary,
        "severity": sev_str,
        "created_at": notification.created_at,
        "deep_link": notification.deep_link or {},
        "metadata": clean_meta,
    }


def validate_webhook_url(url: str, allow_http: bool = False) -> tuple[bool, str]:
    """
    Validate webhook destination URL.
    Enforces HTTPS by default. Rejects malformed, non-HTTP, and blank destinations.

    Note on SSRF Considerations:
    In production SaaS environments, destination URLs should additionally be checked
    against private/loopback IP address ranges (e.g. 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16,
    127.0.0.0/8) or routed through a dedicated egress isolation proxy.
    """
    if not url or not url.strip():
        return False, "Destination URL cannot be empty."

    parsed = urllib.parse.urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        return False, "Destination URL must be a valid, fully qualified URL."

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return False, f"Unsupported URL scheme '{scheme}'. Must be http or https."

    if scheme == "http" and not allow_http:
        return False, "Insecure HTTP destination rejected. HTTPS is required for webhook delivery."

    return True, ""


class WebhookNotificationProvider(NotificationProvider):
    """
    Safe Webhook notification provider.

    Features:
    - URL validation (HTTPS default).
    - Deterministic JSON payload with schema_version="1".
    - HMAC-SHA256 signature header (X-Notification-Signature).
    - Idempotency key header (X-Notification-Idempotency-Key).
    - Timestamp header (X-Notification-Timestamp).
    - Configurable retry engine (WEBHOOK_TIMEOUT, WEBHOOK_MAX_RETRIES, WEBHOOK_RETRY_BACKOFF).
    - Pluggable WebhookTransport ensuring 100% offline safety in tests.
    - Strict secret redaction in logs and errors.
    """

    def __init__(
        self,
        default_destination_url: Optional[str] = None,
        secret: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_backoff: Optional[float] = None,
        allow_http: bool = False,
        transport: Optional[WebhookTransport] = None,
    ) -> None:
        self.default_destination_url = default_destination_url
        self._secret = secret
        self.timeout = timeout if timeout is not None else settings.WEBHOOK_TIMEOUT
        self.max_retries = max_retries if max_retries is not None else settings.WEBHOOK_MAX_RETRIES
        self.retry_backoff = retry_backoff if retry_backoff is not None else settings.WEBHOOK_RETRY_BACKOFF
        self.allow_http = allow_http
        self.transport = transport or MockWebhookTransport()

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.WEBHOOK

    @property
    def name(self) -> str:
        return "webhook_provider"

    def is_configured(self) -> bool:
        return bool(self.default_destination_url or self._secret)

    def send(
        self,
        notification: Notification,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        attempted_at = _utcnow_iso()

        # Destination URL resolution
        dest_url = (
            recipient
            or kwargs.get("destination_url")
            or kwargs.get("url")
            or notification.metadata.get("webhook_url")
            or self.default_destination_url
        )

        # Validate destination URL
        valid, err_msg = validate_webhook_url(dest_url, allow_http=self.allow_http)
        if not valid:
            logger.warning("Webhook delivery rejected: %s", err_msg)
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=NotificationChannel.WEBHOOK,
                provider=self.name,
                error_code=NotificationErrorCode.INVALID_DESTINATION.value,
                error_message=f"Invalid webhook destination: {err_msg}",
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        # Format deterministic canonical payload
        payload_dict = format_webhook_payload(notification)
        canonical_body = json.dumps(payload_dict, sort_keys=True, separators=(",", ":"))

        # Compute idempotency key
        delivery_key = compute_delivery_key(
            tenant_id=notification.tenant_id,
            user_id=notification.user_id,
            notification_id=notification.notification_id,
            channel=NotificationChannel.WEBHOOK,
        )

        # Build headers
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "LegislativeIntel-Webhook/1.0",
            "X-Notification-Idempotency-Key": delivery_key,
            "X-Notification-Timestamp": attempted_at,
            "X-Notification-Schema-Version": WEBHOOK_SCHEMA_VERSION,
        }

        # Signing secret resolution
        secret = kwargs.get("secret") or self._secret or notification.metadata.get("webhook_secret")
        if secret:
            sig = generate_hmac_sha256_signature(secret, canonical_body)
            headers["X-Notification-Signature"] = f"sha256={sig}"

        # Execute dispatch with retry engine
        attempt = 0
        last_error_code: str = NotificationErrorCode.HTTP_FAILURE.value
        last_error_msg: str = "Unknown error"
        last_status_code: Optional[int] = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                status_code, body = self.transport.post(
                    url=dest_url,
                    data=canonical_body,
                    headers=headers,
                    timeout=float(self.timeout),
                )
                last_status_code = status_code

                # 2xx Success
                if 200 <= status_code < 300:
                    logger.debug(
                        "Webhook delivered to %s (status %d, attempt %d)",
                        dest_url,
                        status_code,
                        attempt,
                    )
                    return DeliveryResult(
                        success=True,
                        status=NotificationStatus.DELIVERED,
                        channel=NotificationChannel.WEBHOOK,
                        provider=self.name,
                        response_code=status_code,
                        attempted_at=attempted_at,
                        completed_at=_utcnow_iso(),
                        retry_count=attempt - 1,
                        metadata={
                            "destination_url": dest_url,
                            "idempotency_key": delivery_key,
                            "schema_version": WEBHOOK_SCHEMA_VERSION,
                        },
                    )

                # 4xx Client error (except 429 Too Many Requests): non-retryable
                if 400 <= status_code < 500 and status_code != 429:
                    last_error_code = (
                        NotificationErrorCode.AUTHENTICATION_FAILURE.value
                        if status_code in (401, 403)
                        else NotificationErrorCode.HTTP_FAILURE.value
                    )
                    last_error_msg = f"HTTP {status_code} client error response from webhook endpoint"
                    break

                # 5xx or 429: transient retryable server error
                last_error_code = NotificationErrorCode.HTTP_FAILURE.value
                last_error_msg = f"HTTP {status_code} transient error from webhook endpoint"

            except TimeoutError as te:
                last_error_code = NotificationErrorCode.TIMEOUT.value
                last_error_msg = f"Request timed out: {te}"
            except ConnectionError as ce:
                last_error_code = NotificationErrorCode.HTTP_FAILURE.value
                last_error_msg = f"Connection error: {ce}"
            except Exception as e:
                last_error_code = NotificationErrorCode.CONFIGURATION_ERROR.value
                last_error_msg = f"Unexpected webhook error: {e}"

            # Retry backoff sleep (only if further retries remain and backoff > 0)
            if attempt < self.max_retries and self.retry_backoff > 0:
                time.sleep(self.retry_backoff * (2 ** (attempt - 1)))

        logger.warning(
            "Webhook delivery failed to %s after %d attempts: %s",
            dest_url,
            attempt,
            last_error_msg,
        )
        return DeliveryResult(
            success=False,
            status=NotificationStatus.FAILED,
            channel=NotificationChannel.WEBHOOK,
            provider=self.name,
            response_code=last_status_code,
            error_code=last_error_code,
            error_message=last_error_msg,
            attempted_at=attempted_at,
            completed_at=_utcnow_iso(),
            retry_count=attempt - 1,
            metadata={"destination_url": dest_url},
        )


# ---------------------------------------------------------------------------
# Provider Registry
# ---------------------------------------------------------------------------


class NotificationProviderRegistry:
    """
    Registry for notification channel providers.
    Allows runtime replacement of providers with test doubles or alternate vendors
    without coupling business logic to specific external APIs.
    """

    def __init__(self) -> None:
        self._providers: dict[NotificationChannel, NotificationProvider] = {}

    def register(self, provider: NotificationProvider) -> None:
        """Register or replace the provider for a channel."""
        self._providers[provider.channel] = provider
        logger.debug("Registered notification provider %s for channel %s", provider.name, provider.channel)

    def get(self, channel: NotificationChannel | str) -> Optional[NotificationProvider]:
        """Retrieve provider configured for the channel."""
        ch = (
            channel
            if isinstance(channel, NotificationChannel)
            else NotificationChannel(str(channel).strip().upper())
        )
        return self._providers.get(ch)

    def has(self, channel: NotificationChannel | str) -> bool:
        """Check whether a provider is registered for the channel."""
        return self.get(channel) is not None

    def unregister(self, channel: NotificationChannel | str) -> Optional[NotificationProvider]:
        """Unregister provider for a channel."""
        ch = (
            channel
            if isinstance(channel, NotificationChannel)
            else NotificationChannel(str(channel).strip().upper())
        )
        return self._providers.pop(ch, None)

    @classmethod
    def create_default(
        cls,
        notification_repo: Optional[NotificationRepository] = None,
    ) -> NotificationProviderRegistry:
        """
        Construct a default registry pre-populated with safe providers.
        """
        registry = cls()
        registry.register(InAppNotificationProvider(notification_repo=notification_repo))
        registry.register(EmailNotificationProvider())
        registry.register(PushNotificationProvider())
        registry.register(WebhookNotificationProvider())
        return registry
