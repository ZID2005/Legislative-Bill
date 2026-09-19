# TASK 8.13.7 — OUTBOUND NOTIFICATION DELIVERY PROVIDERS & WEBHOOK DISPATCH

## 1. Objective

Task 8.13.7 introduces the **outbound delivery provider abstraction** and **webhook dispatch infrastructure** for the Legislative Intelligence platform. While Task 8.13.6 established the local in-app notification center and persistence layer, this task provides the extensible architecture necessary to deliver alert events, aggregated groups, and digests to external channels (**EMAIL**, **PUSH**, and **WEBHOOK**) without hardcoding vendor implementations, requiring external credentials, or making live network calls during development and automated tests.

---

## 2. Architecture

The end-to-end notification delivery architecture flows downstream from legislative monitoring through alert matching, aggregation, digest generation, and multi-channel dispatch:

```
Monitoring
    ↓
Alert Matching
    ↓
AlertEvent
    ↓
Alert Aggregation
    ↓
AlertGroup
    ↓
Digest Pipeline
    ↓
Notification
    ↓
NotificationDispatcher
    ├── AlertPreference Check (enabled, allowed channels, severity threshold)
    ├── Idempotency Check (deterministic delivery key)
    └── NotificationProviderRegistry
          ├── IN_APP  → InAppNotificationProvider  → NotificationRepository (In-App Center)
          ├── EMAIL   → EmailNotificationProvider  → Outbound Transport / MockEmailProvider
          ├── PUSH    → PushNotificationProvider   → Mobile/Web Transport / MockPushProvider
          └── WEBHOOK → WebhookNotificationProvider → HMAC-SHA256 Signing + Retry Engine → MockWebhookTransport
                ↓
          DeliveryResult & NotificationDeliveryRecord
```

---

## 3. Dispatcher Abstraction

The core routing layer is encapsulated in `NotificationDispatcher` (`services/notification_dispatcher.py`).

Key methods:
- `dispatch(notification: Notification, channel: NotificationChannel, recipient: Optional[str] = None, **kwargs) -> DeliveryResult`:
  Unified outbound dispatch pipeline. Performs preference evaluation, idempotency checks, provider resolution from the registry, invocation, and audit record generation.
- `dispatch_in_app(notification: Notification) -> Notification`:
  Preserves the exact Task 8.13.6 contract for in-app notification creation and deduplication.
- `enqueue_delivery(notification: Notification, channel: NotificationChannel, recipient: Optional[str] = None, **kwargs) -> DeliveryResult`:
  Lightweight local synchronous queue abstraction (ready for future replacement with distributed message brokers like Celery or Redis Streams).
- `evaluate_preference(notification: Notification, channel: NotificationChannel) -> bool`:
  Evaluates user preferences for the target channel.

---

## 4. Provider Registry

The `NotificationProviderRegistry` (`services/notification_providers.py`) maintains channel-to-provider mappings:

```python
class NotificationProviderRegistry:
    def register(self, provider: NotificationProvider) -> None: ...
    def get(self, channel: NotificationChannel) -> Optional[NotificationProvider]: ...
    def has(self, channel: NotificationChannel) -> bool: ...
    def unregister(self, channel: NotificationChannel) -> Optional[NotificationProvider]: ...
```

By decoupling providers through this registry:
1. Providers can be replaced or mocked at runtime during automated testing.
2. Missing providers return an explicit `PROVIDER_UNAVAILABLE` error rather than crashing or claiming false success.
3. Core notification dispatch logic remains independent of vendor SDKs.

---

## 5. In-App Channel

The `IN_APP` channel is routed through `InAppNotificationProvider`, which delegates directly to `NotificationRepository`.
- Preserves the unread inbox, archiving, filtering, and soft-delete capabilities created in Task 8.13.6.
- Does not call external network services.
- Records delivery status as `DELIVERED` with response code 200 upon successful local storage.

---

## 6. Email Provider

The `EmailNotificationProvider` abstraction supports future email delivery (e.g. SMTP, Amazon SES, SendGrid, Postmark).
- Contract: `send(notification: Notification, recipient: Optional[str] = None, **kwargs) -> DeliveryResult`.
- If credentials or endpoints are unconfigured, `is_configured()` returns `False` and `send()` returns `status=FAILED` with `error_code=PROVIDER_UNAVAILABLE`.
- It never fabricates "Email sent successfully" when unconfigured.
- It never logs passwords, SMTP credentials, or API keys.
- Offline testing utilizes `MockEmailProvider`, which captures sent emails in-memory with recipient, timestamp, and subject line verification.

---

## 7. Push Provider

The `PushNotificationProvider` abstraction provides a standardized interface for future mobile (APNs, FCM) and web push.
- Contract: `send(notification: Notification, recipient: Optional[str] = None, **kwargs) -> DeliveryResult`.
- Target device tokens or recipient monikers are accepted via `recipient` or `kwargs["device_token"]`.
- When unconfigured, explicitly returns `PROVIDER_UNAVAILABLE`.
- Offline testing utilizes `MockPushProvider`, tracking dispatched payloads in-memory.

---

## 8. Webhook Provider

The `WebhookNotificationProvider` provides a safe, deterministic HTTP webhook dispatch mechanism.
- Pluggable transport: `WebhookTransport` interface allows dependency injection.
- Tests execute using `MockWebhookTransport`, completely avoiding real internet endpoints.
- Validates URLs against malformed strings and enforces HTTPS by default.
- Emits cryptographic headers (`X-Notification-Signature`, `X-Notification-Timestamp`, `X-Notification-Idempotency-Key`).
- Executes configurable retries on transient errors (5xx, 429, timeouts).

---

## 9. Webhook Payload

Webhook payloads are constructed deterministically with grounded data:

```json
{
  "schema_version": "1",
  "event_type": "notification.bill_update",
  "notification_id": "notif_webhook_test_01",
  "source_type": "ALERT_EVENT",
  "source_id": "ev_bill_901",
  "tenant_id": "tenant_gamma",
  "user_id": "user_fin_analyst",
  "title": "Banking Laws Amendment Bill Tabled",
  "summary": "Union Finance Minister introduced bill to amend RBI and Banking Regulation Acts.",
  "severity": "HIGH",
  "created_at": "2026-09-18T13:40:00.000000+00:00",
  "deep_link": {
    "destination_type": "BILL_DETAIL",
    "entity_type": "BILL",
    "entity_id": "central-banking-2024",
    "route": "/bills/central-banking-2024"
  },
  "metadata": {
    "bill_id": "banking-laws-amendment-bill-2024",
    "jurisdiction": "central"
  }
}
```

Internal tokens, passwords, and model internals are filtered out before payload construction.

---

## 10. Payload Versioning

Every webhook payload includes `"schema_version": "1"`, exposed both within the JSON body and in the `X-Notification-Schema-Version: 1` header. This allows downstream webhook receivers to parse payloads safely and adapt to future schema versions.

---

## 11. HMAC Signing

Webhook requests are cryptographically signed using **HMAC-SHA256**:
1. Canonical payload is generated with sorted JSON keys (`json.dumps(payload, sort_keys=True, separators=(',', ':'))`).
2. Signature is computed:
   $$\text{signature} = \text{HMAC-SHA256}(\text{secret}, \text{canonical\_payload})$$
3. Sent in header: `X-Notification-Signature: sha256={signature}`.
4. Timestamp is sent in `X-Notification-Timestamp: {utc_iso}` to mitigate replay attacks.

---

## 12. Retry Behavior

The webhook engine implements bounded, exponential backoff retries:
- `WEBHOOK_TIMEOUT`: 10 seconds (configurable via environment).
- `WEBHOOK_MAX_RETRIES`: 3 attempts.
- `WEBHOOK_RETRY_BACKOFF`: 0.5s factor ($t_{\text{sleep}} = \text{backoff} \times 2^{\text{attempt}-1}$).
- Non-retryable errors: HTTP 400, 401, 403, 404, 422 (client errors abort immediately).
- Retryable errors: HTTP 429 (Too Many Requests), HTTP 500, 502, 503, 504, `TimeoutError`, and `ConnectionError`.
- Retries are strictly bounded; infinite loops are impossible.

---

## 13. Timeout Behavior

Request timeouts are handled via `TimeoutError` in transport adapters. When timeout limits are exhausted across configured retries, dispatch terminates with `error_code=TIMEOUT` and `status=FAILED`.

---

## 14. Failure Handling

Provider failures are explicitly distinguished using `NotificationErrorCode`:
- `PROVIDER_UNAVAILABLE`: Provider is not configured or missing from registry.
- `TIMEOUT`: Request exceeded timeout threshold after retries.
- `HTTP_FAILURE`: Server returned a 5xx or unhandled HTTP status code.
- `INVALID_DESTINATION`: Webhook URL is malformed, blank, or violates scheme restrictions.
- `AUTHENTICATION_FAILURE`: HTTP 401/403 or invalid device/API credentials.
- `CONFIGURATION_ERROR`: Malformed settings or invalid serialization.
- `CHANNEL_NOT_ALLOWED`: Target channel disabled in user's `AlertPreference`.

---

## 15. Delivery Status

Notifications and delivery records map to the existing `NotificationStatus` enum:
- `DELIVERED`: Provider accepted or completed dispatch.
- `FAILED`: Provider error, invalid destination, timeout, or unavailable provider.
- `SUPPRESSED`: User preference rules disabled channel or alert type.
- `PENDING`: Queued for dispatch.

---

## 16. Idempotency

To prevent accidental duplicate outbound deliveries:
1. Deterministic delivery key generated:
   $$\text{delivery\_key} = \text{SHA-256}(\text{tenant\_id} \parallel \text{user\_id} \parallel \text{notification\_id} \parallel \text{channel})$$
2. Webhook header includes `X-Notification-Idempotency-Key: {delivery_key}`.
3. `NotificationDeliveryRepository` checks if a successful delivery record already exists for the key. If found, it returns cached success without triggering repeat external requests.

---

## 17. Preference Integration

Before dispatching to any channel, `NotificationDispatcher.evaluate_preference(notification, channel)` checks:
1. Master user toggle (`pref.enabled`).
2. Allowed channels (`channel in pref.allowed_channels`).
3. Severity threshold (`severity_rank(notification.severity) >= severity_rank(pref.minimum_severity)`).
4. Allowed alert types (`alert_type in pref.allowed_alert_types`).

If disallowed, dispatch is suppressed and logged with status `SUPPRESSED`.

---

## 18. Secret Management

- Secrets (API keys, webhook signing secrets, SMTP passwords) are never stored in source code.
- Loaded exclusively from environment variables or settings (`config/settings.py`).
- Secrets and tokens are filtered from log statements and error messages.
- Test suites use mock secrets (`whsec_test_abc123`).

---

## 19. Security & SSRF Considerations

- Webhook destination URLs must be HTTPS by default. Insecure `http://` is rejected unless explicitly enabled for local development.
- Production SaaS recommendation: Implement IP egress filtering or an egress proxy to prevent SSRF against internal subnets (e.g., 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.169.254).

---

## 20. Test Strategy & Offline Isolation

All tests are strictly offline and deterministic:
- `tests/test_notification_dispatcher.py`: Channel routing, provider registry, preference suppression, delivery status tracking, idempotency, tenant/user isolation, pipeline integration, and baseline integrity.
- `tests/test_notification_providers.py`: Email and Push providers, unconfigured provider handling, and secret non-logging.
- `tests/test_webhook_provider.py`: Payload formatting, versioning, HMAC-SHA256 signing, URL validation, timeout/retry logic, and idempotency keys.

---

## 21. Baseline Integrity

The Central quantitative baseline and State jurisdictional isolation remain 100% frozen:
- Central quantitative companies = **47**
- Central bill-company pairs = **940**
- Central predictions = **4,700**
- State corporate exposures = **86**
- State predictions = **0**
- Central baseline changed = **False**

---

## 22. Strict Non-Goals

The following were strictly excluded in Task 8.13.7:
- Real production email/SMS/Push provider deployment.
- Real external HTTP calls during automated tests.
- Distributed message brokers (Celery, Kafka, RabbitMQ).
- Frontend UI components (React, Next.js).
- User authentication or signup flows.
- LLM / Groq AI summary generation.
- Retraining ML models or altering quantitative predictions.

---

## 23. Future Provider Integration

To add a new delivery provider (e.g. Twilio SMS, AWS SES, Firebase Cloud Messaging):
1. Implement `NotificationProvider` interface in `services/notification_providers.py`.
2. Configure credentials in `config/settings.py`.
3. Register the provider with `dispatcher.registry.register(NewProvider())`.
4. The core dispatching pipeline, idempotency, and preference checks will manage it automatically.

---

## 24. Recommended Next Task

**Task 8.13.8 — Watchlist & Alert System Integration, E2E Verification & Hardening**:
- End-to-end integration across the full pipeline:
  $$\text{Legislative Ingestion} \to \text{Alert Matching} \to \text{Aggregation} \to \text{Digests} \to \text{In-App Center} \to \text{Outbound Webhooks}$$
- Production deployment checklists, secret rotation guidelines, and delivery telemetry metrics.
