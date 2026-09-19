"""
services/notification_dispatcher.py
===================================
Outbound Notification Dispatcher abstraction for routing, evaluating preferences,
enforcing idempotency, and dispatching alert notifications across multiple channels
(IN_APP, EMAIL, PUSH, WEBHOOK).

Enforces:
- In-App delivery via NotificationRepository persistence and in-app inbox.
- Outbound delivery via pluggable NotificationProvider implementations.
- User preference filtering via AlertPreferenceRepository (master toggle, allowed channels, severity threshold).
- Deterministic idempotency tracking via NotificationDeliveryRepository.
- Multi-tenant and user isolation.
- Offline test isolation and safe credential handling.

Task 8.13.6 & Task 8.13.7 — Outbound Notification Delivery Providers & Webhook Dispatch.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.alert import (
    AlertPreference,
    AlertSeverity,
    AlertType,
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from schemas.alert_group import severity_rank
from schemas.notification_delivery import (
    DeliveryResult,
    NotificationDeliveryRecord,
    NotificationErrorCode,
    compute_delivery_key,
)
from services.notification_providers import (
    InAppNotificationProvider,
    NotificationProvider,
    NotificationProviderRegistry,
)
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.notification_delivery_repository import NotificationDeliveryRepository
from storage.notification_repository import NotificationRepository

logger = get_logger(__name__)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class NotificationDispatcher:
    """
    Dispatcher abstraction managing in-app delivery and outbound channel routing policies.
    """

    def __init__(
        self,
        notification_repo: Optional[NotificationRepository] = None,
        alert_pref_repo: Optional[AlertPreferenceRepository] = None,
        delivery_repo: Optional[NotificationDeliveryRepository] = None,
        registry: Optional[NotificationProviderRegistry] = None,
    ) -> None:
        self.notification_repo = notification_repo or NotificationRepository()
        self.alert_pref_repo = alert_pref_repo or AlertPreferenceRepository()
        self.delivery_repo = delivery_repo or NotificationDeliveryRepository()
        self.registry = registry or NotificationProviderRegistry.create_default(
            notification_repo=self.notification_repo
        )

    def evaluate_preference(
        self,
        notification: Notification,
        channel: NotificationChannel = NotificationChannel.IN_APP,
    ) -> bool:
        """
        Evaluate if notification passes recipient's AlertPreference rules for a given channel.

        Returns True if eligible for delivery, False if suppressed.
        """
        pref: Optional[AlertPreference] = self.alert_pref_repo.get_by_user(
            user_id=notification.user_id,
            tenant_id=notification.tenant_id,
        )
        if not pref:
            # Default policy: permit in-app delivery, permit configured outbound channels
            return True

        # Master toggle
        if not pref.enabled:
            logger.info(
                "Notification %s suppressed: Master alert toggle disabled for user %s",
                notification.notification_id,
                notification.user_id,
            )
            return False

        # Channel check
        target_channel = (
            channel
            if isinstance(channel, NotificationChannel)
            else NotificationChannel(str(channel).strip().upper())
        )
        if target_channel not in pref.allowed_channels:
            logger.info(
                "Notification %s suppressed: %s channel not permitted for user %s",
                notification.notification_id,
                target_channel.value,
                notification.user_id,
            )
            return False

        # Severity threshold check
        if notification.severity:
            notif_rank = severity_rank(notification.severity)
            pref_rank = severity_rank(pref.minimum_severity)
            if notif_rank < pref_rank:
                logger.info(
                    "Notification %s suppressed: Severity %s below user minimum threshold %s",
                    notification.notification_id,
                    notification.severity,
                    pref.minimum_severity,
                )
                return False

        # Alert type check if present in metadata
        raw_type = notification.metadata.get("alert_type")
        if raw_type:
            try:
                a_type = AlertType(str(raw_type).strip().upper())
                if a_type not in pref.allowed_alert_types:
                    logger.info(
                        "Notification %s suppressed: AlertType %s disallowed for user %s",
                        notification.notification_id,
                        a_type,
                        notification.user_id,
                    )
                    return False
            except ValueError:
                pass

        return True

    def dispatch_in_app(self, notification: Notification) -> Notification:
        """
        Dispatch notification via IN_APP channel.

        Maintains exact Task 8.13.6 semantics:
        1. Evaluates deduplication against existing records.
        2. Evaluates recipient alert preferences.
        3. Updates status to DELIVERED or SUPPRESSED.
        4. Persists the notification record to the user's directory.
        """
        notification.validate()

        # Check deduplication first
        if notification.dedup_key:
            existing = self.notification_repo.find_by_dedup_key(
                dedup_key=notification.dedup_key,
                tenant_id=notification.tenant_id,
                user_id=notification.user_id,
            )
            if existing:
                logger.debug(
                    "Notification already exists for dedup_key %s (id: %s)",
                    notification.dedup_key,
                    existing.notification_id,
                )
                return existing

        # Evaluate preference
        allowed = self.evaluate_preference(notification, channel=NotificationChannel.IN_APP)
        if not allowed:
            notification.status = NotificationStatus.SUPPRESSED
        else:
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = _utcnow_iso()

        # Persist notification
        try:
            saved = self.notification_repo.create(notification)
        except ValueError:
            saved = self.notification_repo.save(notification)

        # Log delivery record for in-app channel
        delivery_key = compute_delivery_key(
            tenant_id=notification.tenant_id,
            user_id=notification.user_id,
            notification_id=notification.notification_id,
            channel=NotificationChannel.IN_APP,
        )
        self.delivery_repo.create(
            NotificationDeliveryRecord(
                notification_id=notification.notification_id,
                tenant_id=notification.tenant_id,
                user_id=notification.user_id,
                channel=NotificationChannel.IN_APP,
                status=saved.status,
                provider="in_app_provider",
                delivery_key=delivery_key,
                response_code=200 if saved.status == NotificationStatus.DELIVERED else None,
            )
        )

        return saved

    def dispatch(
        self,
        notification: Notification,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        """
        Dispatch notification to a specific channel through the provider abstraction.

        1. Validates notification.
        2. Evaluates recipient alert preferences (suppressed if disallowed).
        3. Checks idempotency: if already delivered, returns cached success.
        4. Resolves channel provider from registry.
        5. Executes delivery and records structured audit log.
        """
        attempted_at = _utcnow_iso()
        notification.validate()

        target_channel = (
            channel
            if isinstance(channel, NotificationChannel)
            else NotificationChannel(str(channel).strip().upper())
        )

        delivery_key = compute_delivery_key(
            tenant_id=notification.tenant_id,
            user_id=notification.user_id,
            notification_id=notification.notification_id,
            channel=target_channel,
        )

        # 1. Preference evaluation
        allowed = self.evaluate_preference(notification, channel=target_channel)
        if not allowed:
            # Record suppression
            self.delivery_repo.create(
                NotificationDeliveryRecord(
                    notification_id=notification.notification_id,
                    tenant_id=notification.tenant_id,
                    user_id=notification.user_id,
                    channel=target_channel,
                    status=NotificationStatus.SUPPRESSED,
                    provider="dispatcher_preference",
                    delivery_key=delivery_key,
                    error_code=NotificationErrorCode.CHANNEL_NOT_ALLOWED.value,
                    error_message=f"Channel {target_channel.value} is not permitted in user preferences.",
                )
            )
            return DeliveryResult(
                success=False,
                status=NotificationStatus.SUPPRESSED,
                channel=target_channel,
                provider="dispatcher_preference",
                error_code=NotificationErrorCode.CHANNEL_NOT_ALLOWED.value,
                error_message=f"Channel {target_channel.value} is not permitted in user preferences.",
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        # 2. Idempotency check: avoid uncontrolled duplicate outbound deliveries
        if self.delivery_repo.has_successful_delivery(
            delivery_key=delivery_key,
            tenant_id=notification.tenant_id,
            user_id=notification.user_id,
        ):
            logger.debug(
                "Idempotent skip: notification %s already delivered via %s",
                notification.notification_id,
                target_channel.value,
            )
            return DeliveryResult(
                success=True,
                status=NotificationStatus.DELIVERED,
                channel=target_channel,
                provider="idempotency_cache",
                response_code=200,
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
                metadata={"idempotent": True, "delivery_key": delivery_key},
            )

        # 3. Provider resolution
        provider = self.registry.get(target_channel)
        if not provider:
            error_msg = f"No provider registered for channel {target_channel.value}"
            logger.warning(error_msg)
            self.delivery_repo.create(
                NotificationDeliveryRecord(
                    notification_id=notification.notification_id,
                    tenant_id=notification.tenant_id,
                    user_id=notification.user_id,
                    channel=target_channel,
                    status=NotificationStatus.FAILED,
                    provider="unregistered",
                    delivery_key=delivery_key,
                    error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
                    error_message=error_msg,
                )
            )
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=target_channel,
                provider="unregistered",
                error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
                error_message=error_msg,
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        if not provider.is_configured():
            error_msg = f"Provider {provider.name} for channel {target_channel.value} is not configured."
            logger.info(error_msg)
            self.delivery_repo.create(
                NotificationDeliveryRecord(
                    notification_id=notification.notification_id,
                    tenant_id=notification.tenant_id,
                    user_id=notification.user_id,
                    channel=target_channel,
                    status=NotificationStatus.FAILED,
                    provider=provider.name,
                    delivery_key=delivery_key,
                    error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
                    error_message=error_msg,
                )
            )
            return DeliveryResult(
                success=False,
                status=NotificationStatus.FAILED,
                channel=target_channel,
                provider=provider.name,
                error_code=NotificationErrorCode.PROVIDER_UNAVAILABLE.value,
                error_message=error_msg,
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
            )

        # 4. Route IN_APP specifically through dispatch_in_app for full lifecycle consistency
        if target_channel == NotificationChannel.IN_APP:
            notif_res = self.dispatch_in_app(notification)
            success = notif_res.status == NotificationStatus.DELIVERED
            return DeliveryResult(
                success=success,
                status=notif_res.status,
                channel=NotificationChannel.IN_APP,
                provider=provider.name,
                response_code=200 if success else None,
                attempted_at=attempted_at,
                completed_at=_utcnow_iso(),
                retry_count=0,
                metadata={"notification_id": notif_res.notification_id},
            )

        # 5. Outbound provider dispatch (EMAIL, PUSH, WEBHOOK)
        result = provider.send(
            notification=notification,
            recipient=recipient,
            **kwargs,
        )

        # 6. Audit logging of delivery attempt
        self.delivery_repo.create(
            NotificationDeliveryRecord(
                notification_id=notification.notification_id,
                tenant_id=notification.tenant_id,
                user_id=notification.user_id,
                channel=target_channel,
                status=result.status,
                provider=result.provider,
                delivery_key=delivery_key,
                response_code=result.response_code,
                error_code=result.error_code,
                error_message=result.error_message,
                response_metadata=result.metadata,
            )
        )

        return result

    def enqueue_delivery(
        self,
        notification: Notification,
        channel: NotificationChannel,
        recipient: Optional[str] = None,
        **kwargs: Any,
    ) -> DeliveryResult:
        """
        Lightweight delivery queue abstraction per Task 8.13.7 Section 23.
        Executes synchronous local dispatch; future SaaS queue infrastructure can swap this out.
        """
        return self.dispatch(
            notification=notification,
            channel=channel,
            recipient=recipient,
            **kwargs,
        )

    # -----------------------------------------------------------------------
    # Legacy Channel Stubs (Preserved for Task 8.13.6 test_44 backwards compatibility)
    # -----------------------------------------------------------------------

    def dispatch_email(self, notification: Notification) -> Notification:
        """Legacy stub from Task 8.13.6. For outbound provider delivery, use dispatch(notification, NotificationChannel.EMAIL)."""
        raise NotImplementedError("Direct dispatch_email stub is deprecated. Use dispatch(notification, NotificationChannel.EMAIL)")

    def dispatch_push(self, notification: Notification) -> Notification:
        """Legacy stub from Task 8.13.6. For outbound provider delivery, use dispatch(notification, NotificationChannel.PUSH)."""
        raise NotImplementedError("Direct dispatch_push stub is deprecated. Use dispatch(notification, NotificationChannel.PUSH)")

    def dispatch_webhook(self, notification: Notification) -> Notification:
        """Legacy stub from Task 8.13.6. For outbound provider delivery, use dispatch(notification, NotificationChannel.WEBHOOK)."""
        raise NotImplementedError("Direct dispatch_webhook stub is deprecated. Use dispatch(notification, NotificationChannel.WEBHOOK)")
