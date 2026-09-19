"""
ingestion/state/registry.py
===========================
Registry and configuration manager for Indian State legislative bill sources.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from schemas.state_source import StateBillSource
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "state_sources.json"


class StateSourceRegistry:
    """
    Manages configured State legislative bill sources.

    Provides lookup by source name, filtering by state and active status,
    and runtime registration of new state sources.
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._sources: dict[str, StateBillSource] = {}
        self.config_path = config_path or _DEFAULT_CONFIG_PATH
        self._load_sources()

    def _load_sources(self) -> None:
        """Load sources from JSON configuration if present."""
        if not self.config_path.is_file():
            logger.warning("State sources configuration not found at %s", self.config_path)
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                source = StateBillSource.from_dict(item)
                self._sources[source.source_name] = source
            logger.info("Loaded %d state bill sources from %s", len(self._sources), self.config_path)
        except Exception as e:
            logger.error("Failed to load state sources from %s: %s", self.config_path, e)

    def register(self, source: StateBillSource) -> None:
        """Register or update a State bill source."""
        self._sources[source.source_name] = source
        logger.debug("Registered state bill source: %s", source.source_name)

    def get(self, source_name: str) -> Optional[StateBillSource]:
        """Retrieve a source by its unique name."""
        return self._sources.get(source_name)

    def get_by_state(self, state: str, active_only: bool = False) -> list[StateBillSource]:
        """
        Return all sources matching a given state name (normalized).

        Parameters
        ----------
        state : str
            Target state name or alias (e.g. 'Karnataka', 'KA', 'Andhra Pradesh').
        active_only : bool
            If True, only return sources marked as active.
        """
        norm = normalize_state(state) or state.strip().lower()
        target_norm = norm.lower() if isinstance(norm, str) else ""

        results = []
        for s in self._sources.values():
            s_norm = (normalize_state(s.state) or s.state).lower()
            if s_norm == target_norm:
                if not active_only or s.active:
                    results.append(s)
        return results

    def get_active_sources(self) -> list[StateBillSource]:
        """Return all active state bill sources."""
        return [s for s in self._sources.values() if s.active]

    def get_all_sources(self) -> list[StateBillSource]:
        """Return all registered sources."""
        return list(self._sources.values())

    def count(self) -> int:
        """Return total number of registered sources."""
        return len(self._sources)

    def __repr__(self) -> str:
        return f"<StateSourceRegistry count={len(self._sources)} active={len(self.get_active_sources())}>"
