"""
storage/alert_preference_repository.py
======================================
Repository for user AlertPreference configurations supporting tenant isolation.

Storage layout:
  storage/alerts/preferences/{tenant_id}/{user_id}/preference.json

Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.alert import AlertPreference
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_preferences_dir() -> Path:
    root = settings.ALERTS_DIR / "preferences"
    ensure_dir(root)
    return root


class AlertPreferenceRepository:
    """
    Repository for managing user alert preferences and digest frequencies.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_preferences_dir()
        ensure_dir(self._root_dir)

    def _user_pref_path(self, tenant_id: str, user_id: str) -> Path:
        path = self._root_dir / tenant_id / user_id
        ensure_dir(path)
        return path / "preference.json"

    def create(self, pref: AlertPreference) -> AlertPreference:
        """
        Create and persist initial AlertPreference for a user.
        """
        pref.validate()
        path = self._user_pref_path(pref.tenant_id, pref.user_id)
        if path.is_file():
            raise ValueError(
                f"Alert preference already exists for user '{pref.user_id}' in tenant '{pref.tenant_id}'"
            )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(pref.to_dict(), f, indent=2)
        logger.debug("Created alert preferences for user %s", pref.user_id)
        return pref

    def get_by_user(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
    ) -> Optional[AlertPreference]:
        """
        Retrieve a user's AlertPreference.
        """
        path = self._user_pref_path(tenant_id, user_id)
        if not path.is_file():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return AlertPreference.from_dict(json.load(f))
        except Exception as e:
            logger.error("Failed to load alert preferences for user %s: %s", user_id, e)
            return None

    get = get_by_user

    def update(self, pref: AlertPreference) -> AlertPreference:
        pref.validate()
        from datetime import datetime, timezone
        pref.updated_at = datetime.now(timezone.utc).isoformat()

        path = self._user_pref_path(pref.tenant_id, pref.user_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(pref.to_dict(), f, indent=2)
        return pref

    def save(self, pref: AlertPreference) -> AlertPreference:
        """
        Upsert an AlertPreference: updates if existing, creates if new.
        """
        path = self._user_pref_path(pref.tenant_id, pref.user_id)
        if path.is_file():
            return self.update(pref)
        return self.create(pref)

