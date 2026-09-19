"""
storage/monitoring_repository.py
==================================
Repository for legislative monitoring runs, change events, and bill version history.

Persists to storage/monitoring/ directory tree:
  monitoring_runs/   — MonitoringRun records (one JSON per run)
  change_events/     — ChangeEvent records (one JSON per event)
  bill_versions/     — Bill snapshot history (one dir per bill_id)

Provides deduplication checks to prevent duplicate events/runs.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.monitoring import ChangeEvent, MonitoringRun, RunStatus
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_monitoring_root() -> Path:
    """Return the monitoring storage root, creating it if needed."""
    root = settings.PROJECT_ROOT / "storage" / "monitoring"
    ensure_dir(root)
    return root


class MonitoringRepository:
    """
    Repository for monitoring runs, change events, and bill version history.

    Storage layout:
      storage/monitoring/
        monitoring_runs/   — run_{run_id}.json
        change_events/     — event_{event_id}.json
        bill_versions/
          {bill_id}/       — version_{timestamp}.json
    """

    def __init__(self, monitoring_root: Optional[Path] = None) -> None:
        self._root = monitoring_root or _get_monitoring_root()
        self._runs_dir = self._root / "monitoring_runs"
        self._events_dir = self._root / "change_events"
        self._versions_dir = self._root / "bill_versions"
        ensure_dir(self._runs_dir)
        ensure_dir(self._events_dir)
        ensure_dir(self._versions_dir)

        # In-memory deduplication indices
        self._seen_event_ids: set[str] = self._load_seen_event_ids()
        self._seen_run_ids: set[str] = self._load_seen_run_ids()

    # ------------------------------------------------------------------
    # MonitoringRun
    # ------------------------------------------------------------------

    def save_run(self, run: MonitoringRun) -> None:
        """Persist a MonitoringRun record. Idempotent (overwrites if exists)."""
        path = self._runs_dir / f"run_{run.run_id}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(run.to_dict(), f, indent=2, default=str)
            self._seen_run_ids.add(run.run_id)
            logger.debug("Saved monitoring run %s", run.run_id)
        except Exception as e:
            logger.error("Failed to save monitoring run %s: %s", run.run_id, e)

    def load_run(self, run_id: str) -> Optional[MonitoringRun]:
        """Load a MonitoringRun by run_id."""
        path = self._runs_dir / f"run_{run_id}.json"
        if not path.is_file():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return MonitoringRun.from_dict(data)
        except Exception as e:
            logger.error("Failed to load monitoring run %s: %s", run_id, e)
            return None

    def list_runs(self, limit: int = 50) -> list[MonitoringRun]:
        """Return monitoring runs sorted by start time descending."""
        runs: list[MonitoringRun] = []
        files = sorted(
            self._runs_dir.glob("run_*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        for f in files[:limit]:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                runs.append(MonitoringRun.from_dict(data))
            except Exception:
                pass
        return runs

    def get_last_run(self) -> Optional[MonitoringRun]:
        """Return the most recently completed monitoring run."""
        runs = self.list_runs(limit=1)
        return runs[0] if runs else None

    # ------------------------------------------------------------------
    # ChangeEvent
    # ------------------------------------------------------------------

    def save_event(self, event: ChangeEvent) -> bool:
        """
        Persist a ChangeEvent. Returns False if event_id already exists.
        """
        if event.event_id in self._seen_event_ids:
            logger.debug("Duplicate event skipped: %s", event.event_id)
            return False

        path = self._events_dir / f"event_{event.event_id}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(event.to_dict(), f, indent=2, default=str)
            self._seen_event_ids.add(event.event_id)
            return True
        except Exception as e:
            logger.error("Failed to save change event %s: %s", event.event_id, e)
            return False

    def event_exists(self, event_id: str) -> bool:
        """Check whether a change event has already been persisted."""
        return event_id in self._seen_event_ids

    def list_events(
        self,
        bill_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> list[ChangeEvent]:
        """Return change events, optionally filtered by bill_id or event_type."""
        events: list[ChangeEvent] = []
        files = sorted(
            self._events_dir.glob("event_*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        for f in files:
            if len(events) >= limit:
                break
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if bill_id and data.get("bill_id") != bill_id:
                    continue
                if event_type and data.get("event_type") != event_type:
                    continue
                events.append(ChangeEvent.from_dict(data))
            except Exception:
                pass
        return events

    def get_event_count(self) -> int:
        """Return total number of persisted change events."""
        try:
            return len(list(self._events_dir.glob("event_*.json")))
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Bill Version History
    # ------------------------------------------------------------------

    def save_bill_version(self, bill_id: str, version_data: dict[str, Any]) -> None:
        """Persist a bill version snapshot."""
        if not bill_id:
            return
        safe_id = _safe_dirname(bill_id)
        bill_dir = self._versions_dir / safe_id
        ensure_dir(bill_dir)

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        path = bill_dir / f"version_{ts}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(version_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(
                "Failed to save bill version for %s: %s", bill_id, e
            )

    def load_bill_versions(self, bill_id: str) -> list[dict[str, Any]]:
        """Return all version snapshots for a bill, sorted chronologically."""
        safe_id = _safe_dirname(bill_id)
        bill_dir = self._versions_dir / safe_id
        if not bill_dir.is_dir():
            return []

        versions: list[dict[str, Any]] = []
        for f in sorted(bill_dir.glob("version_*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    versions.append(json.load(fh))
            except Exception:
                pass
        return versions

    # ------------------------------------------------------------------
    # Deduplication helpers
    # ------------------------------------------------------------------

    def _load_seen_event_ids(self) -> set[str]:
        seen: set[str] = set()
        try:
            for f in self._events_dir.glob("event_*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    eid = data.get("event_id")
                    if eid:
                        seen.add(eid)
                except Exception:
                    pass
        except Exception:
            pass
        return seen

    def _load_seen_run_ids(self) -> set[str]:
        seen: set[str] = set()
        try:
            for f in self._runs_dir.glob("run_*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    rid = data.get("run_id")
                    if rid:
                        seen.add(rid)
                except Exception:
                    pass
        except Exception:
            pass
        return seen


def _safe_dirname(bill_id: str) -> str:
    """Convert a bill_id to a safe filesystem directory name."""
    return "".join(
        c if c.isalnum() or c in "-_." else "_" for c in bill_id
    )[:120]
