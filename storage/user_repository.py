"""
storage/user_repository.py
==========================
Repository for User master profiles supporting tenant isolation.

Persists user records deterministically to:
  storage/users/{tenant_id}/user_{user_id}.json

Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.user import User
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_users_dir() -> Path:
    root = settings.USERS_DIR
    ensure_dir(root)
    return root


class UserRepository:
    """
    Repository managing User entities with tenant-scoped persistence.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_users_dir()
        ensure_dir(self._root_dir)

    def _user_path(self, user_id: str, tenant_id: str) -> Path:
        tenant_dir = self._root_dir / tenant_id
        ensure_dir(tenant_dir)
        return tenant_dir / f"user_{user_id}.json"

    def create(self, user: User) -> User:
        """
        Create a new user. Raises ValueError if user already exists in the given tenant.
        """
        user.validate()
        path = self._user_path(user.user_id, user.tenant_id)
        if path.is_file():
            raise ValueError(
                f"User '{user.user_id}' already exists in tenant '{user.tenant_id}'"
            )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(user.to_dict(), f, indent=2)
        logger.debug("Created user %s in tenant %s", user.user_id, user.tenant_id)
        return user

    def get(self, user_id: str, tenant_id: str = "default_tenant") -> Optional[User]:
        """
        Retrieve a user by user_id and tenant_id. Enforces tenant scoping.
        """
        path = self._user_path(user_id, tenant_id)
        if not path.is_file():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return User.from_dict(data)
        except Exception as e:
            logger.error("Failed to load user %s: %s", user_id, e)
            return None

    def update(self, user: User) -> User:
        """
        Update an existing user's attributes. Bumps updated_at timestamp.
        """
        user.validate()
        from datetime import datetime, timezone
        user.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._user_path(user.user_id, user.tenant_id)
        if not path.is_file():
            raise ValueError(
                f"Cannot update non-existent user '{user.user_id}' in tenant '{user.tenant_id}'"
            )

        with open(path, "w", encoding="utf-8") as f:
            json.dump(user.to_dict(), f, indent=2)
        return user

    def list(
        self,
        tenant_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[User]:
        """
        List users, optionally filtered by tenant_id or is_active.
        """
        users: list[User] = []
        tenant_dirs = (
            [self._root_dir / tenant_id]
            if tenant_id
            else [d for d in self._root_dir.iterdir() if d.is_dir()]
        )

        for tdir in tenant_dirs:
            if not tdir.is_dir():
                continue
            for f in tdir.glob("user_*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                    user = User.from_dict(data)
                    if is_active is not None and user.is_active != is_active:
                        continue
                    users.append(user)
                except Exception:
                    pass
        return sorted(users, key=lambda u: u.created_at)
