"""
storage/audit_log_repository.py
===============================
Repository for persisting and querying tenant audit logs (Task 8.19).

Enforces:
1. Append-only JSONL files partitioned by tenant and date:
   storage/audit/{tenant_id}/audit_{YYYY-MM-DD}.jsonl
2. Deterministic tenant isolation — Tenant A cannot read Tenant B audit trails.
3. Fast retrieval with filtering by user, action, and resource.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.audit_log import AuditLogEntry
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_audit_dir() -> Path:
    root = settings.AUDIT_DIR
    ensure_dir(root)
    return root


class AuditLogRepository:
    """
    Append-only repository for security and administrative audit events.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_audit_dir()
        ensure_dir(self._root_dir)

    def _tenant_audit_dir(self, tenant_id: str) -> Path:
        tdir = self._root_dir / tenant_id
        ensure_dir(tdir)
        return tdir

    def log(self, entry: AuditLogEntry) -> AuditLogEntry:
        """Append an audit log entry deterministically."""
        entry.validate()
        tdir = self._tenant_audit_dir(entry.tenant_id)
        date_str = entry.timestamp[:10]  # YYYY-MM-DD
        log_file = tdir / f"audit_{date_str}.jsonl"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

        logger.debug(
            "Audit event recorded: action=%s resource=%s tenant=%s user=%s",
            entry.action,
            entry.resource,
            entry.tenant_id,
            entry.user_id,
        )
        return entry

    def list_entries(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLogEntry]:
        """
        Query audit entries for a tenant in reverse chronological order.
        Strictly enforces tenant scoping.
        """
        tdir = self._root_dir / tenant_id
        if not tdir.is_dir():
            return []

        files = sorted(tdir.glob("audit_*.jsonl"), reverse=True)
        entries: list[AuditLogEntry] = []

        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8") as fh:
                    lines = fh.readlines()
                    for line in reversed(lines):
                        if not line.strip():
                            continue
                        data = json.loads(line)
                        if user_id and data.get("user_id") != user_id:
                            continue
                        if action and data.get("action") != action:
                            continue
                        if resource and data.get("resource") != resource:
                            continue
                        entries.append(AuditLogEntry.from_dict(data))
                        if len(entries) >= offset + limit:
                            break
            except Exception as e:
                logger.error("Error reading audit file %s: %s", fpath, e)

            if len(entries) >= offset + limit:
                break

        return entries[offset : offset + limit]
