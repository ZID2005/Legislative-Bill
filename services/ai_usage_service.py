"""
services/ai_usage_service.py
============================
AI telemetry and usage metering service (Task 8.19).

Enforces:
1. Multi-tenant tracking of AI queries without leaking user prompts.
2. Invariant: If token usage is not returned by the inference engine,
   records 'USAGE_NOT_AVAILABLE' without fabricating synthetic counts.
3. Fast aggregation for SaaS quota tracking.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional, Union

from config.logging_config import get_logger
from config.settings import settings
from schemas.ai_usage import AIUsageRecord
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_ai_usage_dir() -> Path:
    root = settings.AI_USAGE_DIR
    ensure_dir(root)
    return root


class AIUsageService:
    """
    Service recording and querying AI model usage per tenant.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_ai_usage_dir()
        ensure_dir(self._root_dir)

    def _tenant_usage_dir(self, tenant_id: str) -> Path:
        tdir = self._root_dir / tenant_id
        ensure_dir(tdir)
        return tdir

    def record_usage(
        self,
        tenant_id: str,
        user_id: str,
        operation: str,
        model_provider: str = "groq",
        success: bool = True,
        prompt_tokens: Union[int, str] = "USAGE_NOT_AVAILABLE",
        completion_tokens: Union[int, str] = "USAGE_NOT_AVAILABLE",
        total_tokens: Union[int, str] = "USAGE_NOT_AVAILABLE",
        latency_ms: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AIUsageRecord:
        """
        Record an AI inference request.
        """
        record = AIUsageRecord(
            tenant_id=tenant_id,
            user_id=user_id,
            operation=operation,
            model_provider=model_provider,
            success=success,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )

        tdir = self._tenant_usage_dir(tenant_id)
        month_str = record.timestamp[:7]  # YYYY-MM
        usage_file = tdir / f"usage_{month_str}.jsonl"

        with open(usage_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

        logger.debug(
            "AI usage logged: tenant=%s user=%s op=%s success=%s",
            tenant_id,
            user_id,
            operation,
            success,
        )
        return record

    def get_monthly_usage_count(self, tenant_id: str, month_str: Optional[str] = None) -> int:
        """Get the total number of AI requests for a tenant in a given month (YYYY-MM)."""
        if not month_str:
            month_str = datetime.now(timezone.utc).isoformat()[:7]

        tdir = self._tenant_usage_dir(tenant_id)
        usage_file = tdir / f"usage_{month_str}.jsonl"
        if not usage_file.is_file():
            return 0

        count = 0
        try:
            with open(usage_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
        except Exception as e:
            logger.error("Failed to read usage file %s: %s", usage_file, e)

        return count

    def list_records(
        self,
        tenant_id: str,
        limit: int = 50,
        month_str: Optional[str] = None,
    ) -> list[AIUsageRecord]:
        """List recent AI usage records for a tenant."""
        if not month_str:
            month_str = datetime.now(timezone.utc).isoformat()[:7]

        tdir = self._tenant_usage_dir(tenant_id)
        usage_file = tdir / f"usage_{month_str}.jsonl"
        if not usage_file.is_file():
            return []

        records: list[AIUsageRecord] = []
        try:
            with open(usage_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if not line.strip():
                        continue
                    data = json.loads(line)
                    records.append(AIUsageRecord.from_dict(data))
                    if len(records) >= limit:
                        break
        except Exception as e:
            logger.error("Failed to read usage records: %s", e)

        return records
