"""
schemas/ai_usage.py
===================
AI usage metering schema for SaaS multi-tenant tracking (Task 8.19).

Enforces:
1. Per-request telemetry: tenant_id, user_id, timestamp, operation, model_provider, status.
2. Invariant: If real provider usage is unavailable, explicitly stores "USAGE_NOT_AVAILABLE"
   rather than fabricating token counts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Any, Optional, Union


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AIUsageRecord:
    """
    AI telemetry record for SaaS feature entitlement and metering.

    Attributes
    ----------
    usage_id : str
        Unique usage event identifier.
    tenant_id : str
        Tenant charged for the request.
    user_id : str
        User initiating the request.
    operation : str
        AI capability invoked ('ask', 'explain_bill', 'explain_prediction', 'summarize_watchlist').
    model_provider : str
        Provider/model name ('groq/llama3', 'mock_provider', etc.).
    success : bool
        Whether the AI completion succeeded.
    prompt_tokens : Union[int, str]
        Prompt token count, or 'USAGE_NOT_AVAILABLE'.
    completion_tokens : Union[int, str]
        Completion token count, or 'USAGE_NOT_AVAILABLE'.
    total_tokens : Union[int, str]
        Total token count, or 'USAGE_NOT_AVAILABLE'.
    timestamp : str
        UTC ISO-8601 timestamp.
    latency_ms : Optional[float]
        End-to-end response latency in milliseconds.
    metadata : dict[str, Any]
        Additional context (e.g. context_type, query_length).
    """

    tenant_id: str
    user_id: str
    operation: str
    model_provider: str = "groq"
    success: bool = True
    prompt_tokens: Union[int, str] = "USAGE_NOT_AVAILABLE"
    completion_tokens: Union[int, str] = "USAGE_NOT_AVAILABLE"
    total_tokens: Union[int, str] = "USAGE_NOT_AVAILABLE"
    usage_id: str = field(default_factory=lambda: f"usg_{uuid.uuid4().hex[:12]}")
    timestamp: str = field(default_factory=_utcnow_iso)
    latency_ms: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize usage record."""
        return {
            "usage_id": self.usage_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "operation": self.operation,
            "model_provider": self.model_provider,
            "success": self.success,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "timestamp": self.timestamp,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AIUsageRecord":
        """Deserialize usage record."""
        return cls(
            usage_id=data.get("usage_id", f"usg_{uuid.uuid4().hex[:12]}"),
            tenant_id=data.get("tenant_id", "default_tenant"),
            user_id=data.get("user_id", "default_user"),
            operation=data.get("operation", "ask"),
            model_provider=data.get("model_provider", "groq"),
            success=data.get("success", True),
            prompt_tokens=data.get("prompt_tokens", "USAGE_NOT_AVAILABLE"),
            completion_tokens=data.get("completion_tokens", "USAGE_NOT_AVAILABLE"),
            total_tokens=data.get("total_tokens", "USAGE_NOT_AVAILABLE"),
            timestamp=data.get("timestamp", _utcnow_iso()),
            latency_ms=data.get("latency_ms"),
            metadata=data.get("metadata", {}),
        )
