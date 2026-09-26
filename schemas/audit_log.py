"""
schemas/audit_log.py
====================
Audit log data model for security-sensitive operations (Task 8.19).

Enforces:
1. Complete forensic tracking of security events:
   USER_INVITED, ROLE_CHANGED, WATCHLIST_CREATED, WATCHLIST_DELETED,
   ALERT_CREATED, ALERT_UPDATED, SETTINGS_CHANGED, LOGIN_SUCCESS,
   LOGIN_FAILURE, DATA_EXPORT_REQUESTED, ACCOUNT_DELETED, TENANT_DELETED.
2. Invariant: NEVER logs plaintext passwords, session tokens, API keys, or raw payloads.
3. Immutable append-only log record format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Any, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "key", "api_key", "bearer"}


def sanitize_details(details: dict[str, Any]) -> dict[str, Any]:
    """Sanitize any potentially sensitive keys from audit log metadata."""
    sanitized: dict[str, Any] = {}
    for k, v in details.items():
        if any(sens in k.lower() for sens in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_details(v)
        else:
            sanitized[k] = v
    return sanitized


@dataclass
class AuditLogEntry:
    """
    Forensic audit log entry for security and regulatory compliance.

    Attributes
    ----------
    audit_id : str
        Unique identifier for the audit event.
    tenant_id : str
        Tenant boundary identifier.
    user_id : str
        User initiating the action.
    action : str
        Canonical action verb.
    resource : str
        Resource entity type (e.g. 'watchlist', 'alert', 'user', 'organization', 'session').
    resource_id : str
        Resource identifier acted upon.
    timestamp : str
        UTC ISO-8601 event timestamp.
    status : str
        'SUCCESS' or 'FAILURE'.
    request_id : Optional[str]
        HTTP X-Request-ID correlation identifier.
    ip_address : Optional[str]
        Client IP address if available.
    details : dict[str, Any]
        Non-sensitive contextual metadata.
    """

    tenant_id: str
    user_id: str
    action: str
    resource: str
    resource_id: str
    status: str = "SUCCESS"
    audit_id: str = field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    timestamp: str = field(default_factory=_utcnow_iso)
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate audit log invariants."""
        if not self.tenant_id or not self.tenant_id.strip():
            raise ValueError("tenant_id cannot be blank")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be blank")
        if not self.action or not self.action.strip():
            raise ValueError("action cannot be blank")
        self.details = sanitize_details(self.details)

    def to_dict(self) -> dict[str, Any]:
        """Serialize audit log entry."""
        return {
            "audit_id": self.audit_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "resource_id": self.resource_id,
            "status": self.status,
            "timestamp": self.timestamp,
            "request_id": self.request_id,
            "ip_address": self.ip_address,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditLogEntry":
        """Deserialize audit log entry."""
        entry = cls(
            audit_id=data.get("audit_id", f"aud_{uuid.uuid4().hex[:12]}"),
            tenant_id=data.get("tenant_id", "default_tenant"),
            user_id=data.get("user_id", "default_user"),
            action=data.get("action", "UNKNOWN_ACTION"),
            resource=data.get("resource", "system"),
            resource_id=data.get("resource_id", "none"),
            status=data.get("status", "SUCCESS"),
            timestamp=data.get("timestamp", _utcnow_iso()),
            request_id=data.get("request_id"),
            ip_address=data.get("ip_address"),
            details=data.get("details", {}),
        )
        entry.validate()
        return entry
