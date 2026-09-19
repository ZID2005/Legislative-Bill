"""
services/monitoring/source_registry.py
======================================
Unified Monitoring Source Registry for the Legislative Monitoring system.

Loads and manages monitoring sources from config/monitoring_sources.json.
Provides filtering by jurisdiction, state, and enabled status.

Reuses the existing StateSourceRegistry concept but extends it with Central
sources and monitoring-specific metadata fields.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.monitoring import MonitoringSource, SourceStatus
from utils.file_utils import ensure_dir, save_json

logger = get_logger(__name__)

_DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "monitoring_sources.json"
)
_DEFAULT_REGISTRY_SAVE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "storage"
    / "monitoring"
    / "source_registry_state.json"
)


class MonitoringSourceRegistry:
    """
    Unified registry of all legislative monitoring sources (Central + States).

    Loads from config/monitoring_sources.json and persists runtime state
    (last_checked_at, last_success_at, errors) to storage/monitoring/.

    Sources NOT in the four implemented State pilots are marked NOT_IMPLEMENTED
    and will not be polled.
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        state_path: Optional[Path] = None,
    ) -> None:
        self._config_path = config_path or _DEFAULT_CONFIG_PATH
        self._state_path = state_path or _DEFAULT_REGISTRY_SAVE_PATH
        self._sources: dict[str, MonitoringSource] = {}
        self._load()

    def _load(self) -> None:
        """Load sources from config, then overlay persisted runtime state."""
        if not self._config_path.is_file():
            logger.warning(
                "Monitoring sources config not found at %s", self._config_path
            )
            return

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for item in raw:
                src = MonitoringSource.from_dict(item)
                self._sources[src.source_id] = src
            logger.info(
                "Loaded %d monitoring sources from %s",
                len(self._sources),
                self._config_path,
            )
        except Exception as e:
            logger.error("Failed to load monitoring sources: %s", e)

        # Overlay persisted runtime state (timestamps, errors)
        self._load_runtime_state()

    def _load_runtime_state(self) -> None:
        """Overlay persisted last_checked_at / last_error from state file."""
        if not self._state_path.is_file():
            return
        try:
            with open(self._state_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            for source_id, state in state_data.items():
                if source_id in self._sources:
                    src = self._sources[source_id]
                    src.last_checked_at = state.get(
                        "last_checked_at", src.last_checked_at
                    )
                    src.last_success_at = state.get(
                        "last_success_at", src.last_success_at
                    )
                    src.last_error_at = state.get("last_error_at", src.last_error_at)
                    src.last_error = state.get("last_error", src.last_error)
        except Exception as e:
            logger.warning("Could not load monitoring registry state: %s", e)

    def save_state(self) -> None:
        """Persist runtime state (timestamps, errors) to disk."""
        ensure_dir(self._state_path.parent)
        state_data = {
            sid: {
                "last_checked_at": src.last_checked_at,
                "last_success_at": src.last_success_at,
                "last_error_at": src.last_error_at,
                "last_error": src.last_error,
            }
            for sid, src in self._sources.items()
        }
        try:
            save_json(state_data, self._state_path)
        except Exception as e:
            logger.error("Failed to save monitoring registry state: %s", e)

    def get(self, source_id: str) -> Optional[MonitoringSource]:
        """Return a source by its unique source_id."""
        return self._sources.get(source_id)

    def get_all(self) -> list[MonitoringSource]:
        """Return all sources sorted by priority."""
        return sorted(self._sources.values(), key=lambda s: s.priority)

    def get_enabled(self) -> list[MonitoringSource]:
        """Return enabled sources sorted by priority."""
        return [s for s in self.get_all() if s.enabled]

    def get_central_sources(self, enabled_only: bool = True) -> list[MonitoringSource]:
        """Return Central Government sources."""
        sources = [s for s in self.get_all() if s.jurisdiction == "central"]
        if enabled_only:
            sources = [s for s in sources if s.enabled]
        return sources

    def get_state_sources(
        self, state: Optional[str] = None, enabled_only: bool = True
    ) -> list[MonitoringSource]:
        """Return State sources, optionally filtered by state name."""
        sources = [s for s in self.get_all() if s.jurisdiction == "state"]
        if state:
            sources = [s for s in sources if (s.state or "").lower() == state.lower()]
        if enabled_only:
            sources = [s for s in sources if s.enabled]
        return sources

    def get_implemented_states(self) -> list[str]:
        """Return list of state names with IMPLEMENTED status."""
        return [
            s.state
            for s in self._sources.values()
            if s.jurisdiction == "state"
            and s.status == SourceStatus.IMPLEMENTED.value
            and s.state
        ]

    def mark_checked(self, source_id: str, success: bool, error: Optional[str] = None) -> None:
        """Update last check timestamp and error state for a source."""
        src = self._sources.get(source_id)
        if not src:
            return
        now = datetime.now(timezone.utc).isoformat()
        src.last_checked_at = now
        if success:
            src.last_success_at = now
            src.last_error = None
            src.last_error_at = None
        else:
            src.last_error_at = now
            src.last_error = error or "Unknown error"
        self.save_state()

    def count(self) -> int:
        return len(self._sources)

    def __repr__(self) -> str:
        enabled = len(self.get_enabled())
        return f"<MonitoringSourceRegistry total={len(self._sources)} enabled={enabled}>"
