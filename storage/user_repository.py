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

    def _get_db(self) -> Any:
        if self._root_dir != _get_default_users_dir():
            return None
        try:
            from storage.database.provider import get_database_provider
            db = get_database_provider()
            if db and db.status in ("READY", "CONFIGURED"):
                return db
        except Exception:
            pass
        return None

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

        # 1. Database Persistence
        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    """
                    INSERT INTO users (
                        user_id, email, hashed_password, full_name, is_active, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE SET
                        email = EXCLUDED.email,
                        hashed_password = COALESCE(EXCLUDED.hashed_password, users.hashed_password),
                        full_name = EXCLUDED.full_name,
                        is_active = EXCLUDED.is_active,
                        updated_at = EXCLUDED.updated_at;
                    """,
                    (
                        user.user_id,
                        user.email or f"{user.user_id}@platform.local",
                        user.password_hash or "",
                        user.display_name or user.user_id,
                        user.is_active,
                        user.created_at,
                        user.updated_at,
                    ),
                    tenant_id=user.tenant_id,
                )
                membership_id = f"mem_{user.tenant_id}_{user.user_id}"
                db.execute_mutation(
                    """
                    INSERT INTO tenant_memberships (
                        membership_id, tenant_id, user_id, role, created_at
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id, user_id) DO UPDATE SET
                        role = EXCLUDED.role;
                    """,
                    (
                        membership_id,
                        user.tenant_id,
                        user.user_id,
                        user.role,
                        user.created_at,
                    ),
                    tenant_id=user.tenant_id,
                )
            except Exception as e:
                logger.debug("DB insert for user %s failed: %s", user.user_id, e)

        # 2. File Persistence
        with open(path, "w", encoding="utf-8") as f:
            json.dump(user.to_dict(include_sensitive=True), f, indent=2)
        logger.debug("Created user %s in tenant %s", user.user_id, user.tenant_id)
        return user

    def get(self, user_id: str, tenant_id: str = "default_tenant") -> Optional[User]:
        """
        Retrieve a user by user_id and tenant_id. Enforces tenant scoping.
        """
        db = self._get_db()
        if db:
            try:
                rows = db.execute_query(
                    """
                    SELECT u.user_id, m.tenant_id, u.full_name, u.email, m.role, u.is_active,
                           u.hashed_password, u.created_at, u.updated_at
                    FROM users u
                    JOIN tenant_memberships m ON u.user_id = m.user_id
                    WHERE u.user_id = %s AND m.tenant_id = %s;
                    """,
                    (user_id, tenant_id),
                    tenant_id=tenant_id,
                )
                if rows:
                    r = rows[0]
                    return User(
                        user_id=r["user_id"],
                        tenant_id=r["tenant_id"],
                        display_name=r.get("full_name") or r["user_id"],
                        email=r.get("email"),
                        role=r.get("role") or "MEMBER",
                        is_active=bool(r.get("is_active", True)),
                        password_hash=r.get("hashed_password"),
                        created_at=str(r.get("created_at")),
                        updated_at=str(r.get("updated_at")),
                    )
            except Exception as e:
                logger.debug("DB get for user %s failed: %s", user_id, e)

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

    def get_by_email(self, email: str, tenant_id: str = "default_tenant") -> Optional[User]:
        """
        Find a user by email within a tenant.
        """
        if not email:
            return None
        email_clean = email.strip().lower()

        db = self._get_db()
        if db:
            try:
                rows = db.execute_query(
                    """
                    SELECT u.user_id, m.tenant_id, u.full_name, u.email, m.role, u.is_active,
                           u.hashed_password, u.created_at, u.updated_at
                    FROM users u
                    JOIN tenant_memberships m ON u.user_id = m.user_id
                    WHERE LOWER(u.email) = %s AND m.tenant_id = %s;
                    """,
                    (email_clean, tenant_id),
                    tenant_id=tenant_id,
                )
                if rows:
                    r = rows[0]
                    return User(
                        user_id=r["user_id"],
                        tenant_id=r["tenant_id"],
                        display_name=r.get("full_name") or r["user_id"],
                        email=r.get("email"),
                        role=r.get("role") or "MEMBER",
                        is_active=bool(r.get("is_active", True)),
                        password_hash=r.get("hashed_password"),
                        created_at=str(r.get("created_at")),
                        updated_at=str(r.get("updated_at")),
                    )
            except Exception as e:
                logger.debug("DB get_by_email for %s failed: %s", email, e)

        users = self.list(tenant_id=tenant_id)
        for u in users:
            if u.email and u.email.strip().lower() == email_clean:
                return u
        return None

    def update(self, user: User) -> User:
        """
        Update an existing user's attributes. Bumps updated_at timestamp.
        """
        user.validate()
        from datetime import datetime, timezone
        user.updated_at = datetime.now(timezone.utc).isoformat()

        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    """
                    UPDATE users
                    SET full_name = %s, email = COALESCE(%s, email), is_active = %s, updated_at = %s
                    WHERE user_id = %s;
                    """,
                    (user.display_name, user.email, user.is_active, user.updated_at, user.user_id),
                    tenant_id=user.tenant_id,
                )
                db.execute_mutation(
                    """
                    UPDATE tenant_memberships
                    SET role = %s
                    WHERE user_id = %s AND tenant_id = %s;
                    """,
                    (user.role, user.user_id, user.tenant_id),
                    tenant_id=user.tenant_id,
                )
            except Exception as e:
                logger.debug("DB update for user %s failed: %s", user.user_id, e)

        path = self._user_path(user.user_id, user.tenant_id)
        if path.is_file():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(user.to_dict(include_sensitive=True), f, indent=2)
        elif not db:
            raise ValueError(
                f"Cannot update non-existent user '{user.user_id}' in tenant '{user.tenant_id}'"
            )
        return user

    def update_last_active(self, user_id: str, tenant_id: str = "default_tenant") -> Optional[User]:
        """Bump last_active_at timestamp for the user."""
        user = self.get(user_id, tenant_id)
        if not user:
            return None
        from datetime import datetime, timezone
        user.last_active_at = datetime.now(timezone.utc).isoformat()
        return self.update(user)

    def soft_delete(self, user_id: str, tenant_id: str = "default_tenant") -> bool:
        """Soft delete a user by marking status as DELETED."""
        user = self.get(user_id, tenant_id)
        if not user:
            return False
        user.status = "DELETED"
        user.is_active = False
        self.update(user)
        return True

    def list(
        self,
        tenant_id: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> list[User]:
        """
        List users, optionally filtered by tenant_id or is_active.
        """
        db = self._get_db()
        if db:
            try:
                query = """
                    SELECT u.user_id, m.tenant_id, u.full_name, u.email, m.role, u.is_active,
                           u.hashed_password, u.created_at, u.updated_at
                    FROM users u
                    JOIN tenant_memberships m ON u.user_id = m.user_id
                """
                params: list[Any] = []
                where_clauses: list[str] = []
                if tenant_id:
                    where_clauses.append("m.tenant_id = %s")
                    params.append(tenant_id)
                if is_active is not None:
                    where_clauses.append("u.is_active = %s")
                    params.append(is_active)
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
                rows = db.execute_query(query, tuple(params), tenant_id=tenant_id)
                if rows:
                    res = [
                        User(
                            user_id=r["user_id"],
                            tenant_id=r["tenant_id"],
                            display_name=r.get("full_name") or r["user_id"],
                            email=r.get("email"),
                            role=r.get("role") or "MEMBER",
                            is_active=bool(r.get("is_active", True)),
                            password_hash=r.get("hashed_password"),
                            created_at=str(r.get("created_at")),
                            updated_at=str(r.get("updated_at")),
                        )
                        for r in rows
                    ]
                    return sorted(res, key=lambda u: u.created_at)
            except Exception as e:
                logger.debug("DB list users failed: %s", e)

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
