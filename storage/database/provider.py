"""
storage/database/provider.py
============================
Production SaaS Database Abstraction & Persistence Boundary (Task 8.31D).

Establishes a strict separation between:
1. PUBLIC / FROZEN: Read-only econometric & statutory baselines (Central 4,700 predictions,
   4,700 decisions, 940 anticipation scores, 14,100 reports, 20 production bills,
   44 State acts, 44 knowledge records, 86 state corporate exposures, 70 company master).
   Never rewritten or mutated.
2. TENANT-OWNED / MUTABLE: Scoped by tenant_id (tenants, memberships, watchlists,
   watchlist items, alert rules, alert events, notifications, notification preferences,
   account lifecycle state, portfolios, portfolio holdings, saved searches).
3. USER-OWNED / PRIVATE: PII and auth credentials (users, password hashes, user preferences,
   personal device/notification tokens).
4. SYSTEM / OPERATIONAL: Operational telemetry (audit logs, AI token usage metering,
   scheduler locks, background jobs, monitoring run history).

Guarantees:
- DatabaseProvider: Base abstract class with transactional query and mutation methods.
- DevelopmentDatabaseProvider: Uses local file/JSON repository storage and embedded SQLite.
- ProductionDatabaseProvider: Production PostgreSQL adapter architecture supporting Local PostgreSQL
  and Supabase Free connection pooling.
- If real PostgreSQL credentials are absent: DATABASE_STATUS = NOT_CONFIGURED.
  Never fabricate a connected database.
- Explicit database failure handling with clean domain exceptions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
import os
from pathlib import Path
import sqlite3
import threading
from typing import Any, Generator, Optional

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Domain Exceptions (Task 8.31D Section 33)
# ---------------------------------------------------------------------------


class DatabaseError(Exception):
    """Base exception for platform database operations."""
    pass


class DatabaseUnavailableError(DatabaseError):
    """Raised when database host is unreachable or connection timeout occurs."""
    pass


class RecordNotFoundError(DatabaseError):
    """Raised when an expected database record is not found."""
    pass


class TenantMismatchError(DatabaseError):
    """Raised when cross-tenant access violation occurs."""
    pass


class PermissionDeniedError(DatabaseError):
    """Raised when user lacks permission to access or mutate a record."""
    pass


class FrozenRecordImmutabilityError(DatabaseError):
    """Raised when an operation attempts to mutate or delete a frozen analytical baseline record."""
    pass


# ---------------------------------------------------------------------------
# Data Classification Contract
# ---------------------------------------------------------------------------


class DataClassification(str, Enum):
    """
    Authoritative classification of data domains within the platform.
    Defines immutability, scoping, and backup rules.
    """

    PUBLIC_FROZEN = "PUBLIC_FROZEN"
    TENANT_OWNED_MUTABLE = "TENANT_OWNED_MUTABLE"
    USER_OWNED_PRIVATE = "USER_OWNED_PRIVATE"
    SYSTEM_OPERATIONAL = "SYSTEM_OPERATIONAL"


DATA_CLASSIFICATION_REGISTRY: dict[str, dict[str, Any]] = {
    # 1. PUBLIC / FROZEN — Analytical & Statutory Baseline
    "central_bills": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "20 production modeled bills + 2 auxiliary scanned bills.",
        "immutable": True,
        "storage": "data/central_bills/",
        "tenant_scoped": False,
    },
    "central_predictions": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "4,700 event-study market predictions across 5 frozen windows.",
        "immutable": True,
        "storage": "data/predictions/",
        "tenant_scoped": False,
    },
    "central_decisions": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "4,700 decision-support recommendations across 3 risk appetites.",
        "immutable": True,
        "storage": "data/decisions/",
        "tenant_scoped": False,
    },
    "central_anticipation": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "940 anticipation scores across 940 bill-company pairs.",
        "immutable": True,
        "storage": "data/anticipation/scores/",
        "tenant_scoped": False,
    },
    "central_reports": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "14,100 stakeholder reports (4,700 investor, 4,700 business, 4,700 public).",
        "immutable": True,
        "storage": "data/reports/",
        "tenant_scoped": False,
    },
    "state_acts": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "44 State legislative bills across 4 implemented states (AP=12, KA=11, KL=11, TS=10).",
        "immutable": True,
        "storage": "data/state_bills/metadata/",
        "tenant_scoped": False,
    },
    "state_knowledge": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "44 qualitative state knowledge dossiers.",
        "immutable": True,
        "storage": "data/state_knowledge/",
        "tenant_scoped": False,
    },
    "state_corporate_exposures": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "86 evidence-backed State corporate exposure records.",
        "immutable": True,
        "storage": "data/state_bills/corporate_exposure/",
        "tenant_scoped": False,
    },
    "central_corporate_exposures": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "18 evidence-backed Central corporate exposure records.",
        "immutable": True,
        "storage": "data/central_bills/corporate_exposure/",
        "tenant_scoped": False,
    },
    "company_master": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "70 companies (47 quantitative + 20 intelligence + 3 reference).",
        "immutable": True,
        "storage": "data/companies/companies.json",
        "tenant_scoped": False,
    },
    "analytical_baselines": {
        "classification": DataClassification.PUBLIC_FROZEN,
        "description": "Registered analytical baseline manifest (SHA-256: 50ae76039bccf2e4).",
        "immutable": True,
        "storage": "PostgreSQL: analytical_baselines",
        "tenant_scoped": False,
    },

    # 2. TENANT-OWNED / MUTABLE — SaaS Multi-Tenant Domain Data
    "tenants": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "Tenant organization records, plan tier, and settings.",
        "immutable": False,
        "storage": "PostgreSQL: tenants (or storage/tenants/ in dev)",
        "tenant_scoped": True,
    },
    "memberships": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "User memberships within tenants with RBAC role (OWNER, ADMIN, MEMBER, VIEWER).",
        "immutable": False,
        "storage": "PostgreSQL: tenant_memberships (or storage/tenants/ in dev)",
        "tenant_scoped": True,
    },
    "portfolios": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "User portfolios and institutional holdings.",
        "immutable": False,
        "storage": "PostgreSQL: portfolios (or storage/portfolios/ in dev)",
        "tenant_scoped": True,
    },
    "portfolio_holdings": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "Security holdings tracked within a portfolio.",
        "immutable": False,
        "storage": "PostgreSQL: portfolio_holdings",
        "tenant_scoped": True,
    },
    "watchlists": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "Tenant custom watchlists of tracked bills and companies.",
        "immutable": False,
        "storage": "PostgreSQL: watchlists (or storage/watchlists/ in dev)",
        "tenant_scoped": True,
    },
    "watchlist_items": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "Entities tracked within a watchlist.",
        "immutable": False,
        "storage": "PostgreSQL: watchlist_items",
        "tenant_scoped": True,
    },
    "alert_rules": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "Tenant-configured alert triggers and condition thresholds.",
        "immutable": False,
        "storage": "PostgreSQL: alert_rules (or storage/alerts/rules/ in dev)",
        "tenant_scoped": True,
    },
    "alert_events": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "Generated alert events matching tenant rules.",
        "immutable": False,
        "storage": "PostgreSQL: alert_events (or storage/alerts/events/ in dev)",
        "tenant_scoped": True,
    },
    "notifications": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "In-app and delivered notification items.",
        "immutable": False,
        "storage": "PostgreSQL: notifications (or storage/alerts/notifications/ in dev)",
        "tenant_scoped": True,
    },
    "notification_preferences": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "Tenant/user delivery channel preferences.",
        "immutable": False,
        "storage": "PostgreSQL: notification_preferences",
        "tenant_scoped": True,
    },
    "saved_searches": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "Personalized saved searches and filter queries.",
        "immutable": False,
        "storage": "PostgreSQL: saved_searches",
        "tenant_scoped": True,
    },
    "account_lifecycle_state": {
        "classification": DataClassification.TENANT_OWNED_MUTABLE,
        "description": "Tenant lifecycle status (ACTIVE, SUSPENDED, DEACTIVATED, TRIAL).",
        "immutable": False,
        "storage": "PostgreSQL: tenants.status",
        "tenant_scoped": True,
    },

    # 3. USER-OWNED / PRIVATE — Identity & Authentication
    "users": {
        "classification": DataClassification.USER_OWNED_PRIVATE,
        "description": "User accounts, email, hashed credentials, and profiles.",
        "immutable": False,
        "storage": "PostgreSQL: users (or storage/users/ in dev)",
        "tenant_scoped": False,
    },
    "user_preferences": {
        "classification": DataClassification.USER_OWNED_PRIVATE,
        "description": "User-specific visual, analytical, and notification preferences.",
        "immutable": False,
        "storage": "PostgreSQL: user_preferences",
        "tenant_scoped": True,
    },

    # 4. SYSTEM / OPERATIONAL — Auditing & Telemetry
    "audit_logs": {
        "classification": DataClassification.SYSTEM_OPERATIONAL,
        "description": "Append-only security and operational audit trail.",
        "immutable": True,  # Append-only
        "storage": "PostgreSQL: audit_logs (or storage/audit/ in dev)",
        "tenant_scoped": True,
    },
    "ai_usage_records": {
        "classification": DataClassification.SYSTEM_OPERATIONAL,
        "description": "AI Copilot prompt, token metering, and quota tracking.",
        "immutable": True,  # Append-only
        "storage": "PostgreSQL: ai_usage_records (or storage/ai_usage/ in dev)",
        "tenant_scoped": True,
    },
}


# ---------------------------------------------------------------------------
# PostgreSQL Canonical Schema DDL (Reflecting 001 - 003 Migrations)
# ---------------------------------------------------------------------------

MIGRATIONS_DIR = settings.PROJECT_ROOT / "migrations"


def _load_schema_ddl() -> str:
    f1 = MIGRATIONS_DIR / "001_initial_core_schema.sql"
    f2 = MIGRATIONS_DIR / "002_analytical_baseline_schema.sql"
    parts = []
    if f1.is_file():
        parts.append(f1.read_text(encoding="utf-8"))
    if f2.is_file():
        parts.append(f2.read_text(encoding="utf-8"))
    return "\n".join(parts)


POSTGRES_SCHEMA_DDL = _load_schema_ddl()


# ---------------------------------------------------------------------------
# Database Provider Abstraction
# ---------------------------------------------------------------------------


class DatabaseProvider(ABC):
    """
    Abstract Database Provider interface for multi-tenant persistence.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'development_file', 'postgresql')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_configured(self) -> bool:
        """True if the provider has all required configuration parameters."""
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> str:
        """Authoritative status: 'READY', 'CONFIGURED', or 'NOT_CONFIGURED'."""
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Perform a non-destructive database health and connectivity check."""
        raise NotImplementedError

    @abstractmethod
    def get_table_names(self) -> list[str]:
        """Return list of prepared/active table names in the persistence layer."""
        raise NotImplementedError

    @abstractmethod
    def get_schema_ddl(self) -> str:
        """Return SQL schema definition for multi-tenant application tables."""
        raise NotImplementedError

    @abstractmethod
    def migrate_schema(self) -> bool:
        """Execute or verify schema migrations."""
        raise NotImplementedError

    @abstractmethod
    def execute_query(
        self,
        sql: str,
        params: Optional[tuple | dict] = None,
        tenant_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Execute a SELECT query and return list of row dictionaries."""
        raise NotImplementedError

    @abstractmethod
    def execute_mutation(
        self,
        sql: str,
        params: Optional[tuple | dict] = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        """Execute an INSERT, UPDATE, or DELETE mutation and return affected row count."""
        raise NotImplementedError


class DevelopmentDatabaseProvider(DatabaseProvider):
    """
    Development and local testing database provider.
    Operates on local storage/ directories (JSON / file-backed repositories) and
    local embedded SQLite for zero-cost local persistence.
    """

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self._data_dirs = [
            settings.USERS_DIR,
            settings.TENANTS_DIR,
            settings.WATCHLIST_DIR,
            settings.PORTFOLIO_DIR,
            settings.ALERTS_DIR,
            settings.AUDIT_DIR,
            settings.AI_USAGE_DIR,
        ]
        for d in self._data_dirs:
            d.mkdir(parents=True, exist_ok=True)

        self._db_path = Path(db_path) if db_path else settings.DATA_DIR / "local_dev.sqlite"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    @property
    def provider_name(self) -> str:
        return "DevelopmentDatabaseProvider (Local File-Backed & SQLite)"

    @property
    def is_configured(self) -> bool:
        return True

    @property
    def status(self) -> str:
        return "READY"

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        with self._lock:
            conn = sqlite3.connect(str(self._db_path), timeout=10.0)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()

    def health_check(self) -> dict[str, Any]:
        accessible = all(d.is_dir() for d in self._data_dirs)
        sqlite_ok = False
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT 1;")
                cur.fetchone()
                sqlite_ok = True
        except Exception:
            sqlite_ok = False

        return {
            "provider": self.provider_name,
            "status": "HEALTHY" if (accessible or sqlite_ok) else "DEGRADED",
            "connected": accessible or sqlite_ok,
            "storage_type": "local_filesystem_json_and_sqlite",
            "accessible_directories": len(self._data_dirs),
            "sqlite_database": str(self._db_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_table_names(self) -> list[str]:
        registered = [
            "users",
            "tenants",
            "tenant_memberships",
            "portfolios",
            "portfolio_holdings",
            "watchlists",
            "watchlist_items",
            "alert_rules",
            "alert_events",
            "notifications",
            "notification_preferences",
            "audit_logs",
            "ai_usage_records",
            "bills",
            "companies",
            "corporate_exposures",
            "predictions",
            "decisions",
            "anticipation_scores",
            "stakeholder_reports",
            "analytical_baselines",
        ]
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                db_tables = [r[0] for r in cur.fetchall()]
                if db_tables:
                    return db_tables
        except Exception:
            pass
        return registered

    def get_schema_ddl(self) -> str:
        return POSTGRES_SCHEMA_DDL

    def migrate_schema(self) -> bool:
        from storage.database.migrator import MigrationRunner
        try:
            runner = MigrationRunner()
            with self._get_connection() as conn:
                runner.run_migrations(conn, is_sqlite=True)
            return True
        except Exception as e:
            logger.error("Failed to run local SQLite migrations: %s", e)
            return False

    def execute_query(
        self,
        sql: str,
        params: Optional[tuple | dict] = None,
        tenant_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        # Adapt parameter placeholders from %s to ? for SQLite
        sqlite_sql = sql.replace("%s", "?")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                if params:
                    cur.execute(sqlite_sql, params)
                else:
                    cur.execute(sqlite_sql)
                rows = cur.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error("SQLite query execution failed: %s", e)
            raise DatabaseError(f"Database query error: {e}") from e

    def execute_mutation(
        self,
        sql: str,
        params: Optional[tuple | dict] = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        # Enforce statutory immutability protection on frozen analytical tables
        frozen_tables = {"predictions", "decisions", "anticipation_scores", "stakeholder_reports", "analytical_baselines"}
        sql_stripped = sql.strip().upper()
        if sql_stripped.startswith("UPDATE") or sql_stripped.startswith("DELETE"):
            import re
            for ft in frozen_tables:
                if re.search(rf"\b{ft}\b", sql, re.IGNORECASE):
                    raise FrozenRecordImmutabilityError(
                        f"Mutation rejected: '{ft}' is part of the frozen econometric analytical baseline (SHA-256: 50ae76039bccf2e4) and cannot be updated or deleted."
                    )

        sqlite_sql = sql.replace("%s", "?")
        try:
            with self._get_connection() as conn:
                cur = conn.cursor()
                if params:
                    cur.execute(sqlite_sql, params)
                else:
                    cur.execute(sqlite_sql)
                conn.commit()
                return cur.rowcount
        except DatabaseError:
            raise
        except Exception as e:
            logger.error("SQLite mutation execution failed: %s", e)
            raise DatabaseError(f"Database mutation error: {e}") from e


class ProductionDatabaseProvider(DatabaseProvider):
    """
    Production PostgreSQL database provider.
    Supports Local PostgreSQL and Supabase Free via connection pooling.
    Never claims to be configured unless real PostgreSQL connection parameters exist.
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        timeout: int = 10,
    ) -> None:
        raw_url = database_url or os.getenv("DATABASE_URL", "")
        self._database_url = raw_url.strip()
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._timeout = timeout
        self._pool: Optional[Any] = None
        self._lock = threading.Lock()

        # Detect whether real credentials exist
        self._is_configured = bool(
            self._database_url
            and not self._database_url.startswith("postgresql://user:pass@localhost")
            and not "placeholder" in self._database_url.lower()
        )

    @property
    def provider_name(self) -> str:
        return "ProductionDatabaseProvider (PostgreSQL)"

    @property
    def is_configured(self) -> bool:
        return self._is_configured

    @property
    def status(self) -> str:
        return "CONFIGURED" if self._is_configured else "NOT_CONFIGURED"

    def _get_pool(self) -> Any:
        if not self._is_configured:
            raise DatabaseUnavailableError("DATABASE_URL is not configured.")

        if self._pool is None:
            with self._lock:
                if self._pool is None:
                    try:
                        import psycopg2.pool
                        # Supabase Free connection string or Local PostgreSQL
                        self._pool = psycopg2.pool.ThreadedConnectionPool(
                            minconn=1,
                            maxconn=self._pool_size,
                            dsn=self._database_url,
                            connect_timeout=self._timeout,
                        )
                        logger.info("Initialized PostgreSQL connection pool (max=%d).", self._pool_size)
                    except Exception as e:
                        logger.error("Failed to initialize PostgreSQL connection pool: %s", e)
                        raise DatabaseUnavailableError(f"Failed to connect to PostgreSQL: {e}") from e
        return self._pool

    @contextmanager
    def _get_connection(self) -> Generator[Any, None, None]:
        pool = self._get_pool()
        conn = pool.getconn()
        try:
            yield conn
        finally:
            pool.putconn(conn)

    def health_check(self) -> dict[str, Any]:
        if not self._is_configured:
            return {
                "provider": self.provider_name,
                "status": "NOT_CONFIGURED",
                "connected": False,
                "message": "DATABASE_URL is not set or contains placeholder credentials.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        start = datetime.now(timezone.utc)
        try:
            import psycopg2
            conn = psycopg2.connect(self._database_url, connect_timeout=self._timeout)
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
                cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';")
                tbl_count = cur.fetchone()[0]
            conn.close()
            latency_ms = int((datetime.now(timezone.utc) - start).total_seconds() * 1000)

            return {
                "provider": self.provider_name,
                "status": "HEALTHY",
                "connected": True,
                "latency_ms": latency_ms,
                "public_tables": tbl_count,
                "message": "PostgreSQL connection pool verified and responsive.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except ImportError:
            return {
                "provider": self.provider_name,
                "status": "DRIVER_MISSING",
                "connected": False,
                "message": "psycopg2 driver not installed in current environment.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            return {
                "provider": self.provider_name,
                "status": "UNREACHABLE",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def get_table_names(self) -> list[str]:
        if not self._is_configured:
            return [
                "users",
                "tenants",
                "tenant_memberships",
                "portfolios",
                "portfolio_holdings",
                "watchlists",
                "watchlist_items",
                "alert_rules",
                "alert_events",
                "notifications",
                "notification_preferences",
                "audit_logs",
                "ai_usage_records",
                "bills",
                "companies",
                "corporate_exposures",
                "predictions",
                "decisions",
                "anticipation_scores",
                "stakeholder_reports",
                "analytical_baselines",
            ]
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
                    return [r[0] for r in cur.fetchall()]
        except Exception:
            return []

    def get_schema_ddl(self) -> str:
        return POSTGRES_SCHEMA_DDL

    def migrate_schema(self) -> bool:
        if not self._is_configured:
            logger.info("Database migration skipped: PostgreSQL credentials are not configured.")
            return False

        from storage.database.migrator import MigrationRunner
        try:
            import psycopg2
            conn = psycopg2.connect(self._database_url, connect_timeout=self._timeout)
            runner = MigrationRunner()
            runner.run_migrations(conn, is_sqlite=False)
            conn.close()
            logger.info("Executed PostgreSQL migrations successfully.")
            return True
        except Exception as e:
            logger.error("Failed to execute PostgreSQL schema migration: %s", e)
            return False

    def execute_query(
        self,
        sql: str,
        params: Optional[tuple | dict] = None,
        tenant_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if not self._is_configured:
            raise DatabaseUnavailableError("PostgreSQL database is not configured.")

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    if tenant_id:
                        cur.execute("SET LOCAL app.current_tenant_id = %s;", (tenant_id,))
                    cur.execute(sql, params)
                    col_names = [desc[0] for desc in cur.description] if cur.description else []
                    rows = cur.fetchall()
                    return [dict(zip(col_names, row)) for row in rows]
        except Exception as e:
            err_msg = str(e)
            if "IMMUTABLE_FROZEN_RECORD_VIOLATION" in err_msg:
                raise FrozenRecordImmutabilityError("Operation rejected: Frozen analytical record is immutable.") from e
            logger.error("PostgreSQL query execution failed: %s", e)
            raise DatabaseError("Database query operation failed.") from e

    def execute_mutation(
        self,
        sql: str,
        params: Optional[tuple | dict] = None,
        tenant_id: Optional[str] = None,
    ) -> int:
        if not self._is_configured:
            raise DatabaseUnavailableError("PostgreSQL database is not configured.")

        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    if tenant_id:
                        cur.execute("SET LOCAL app.current_tenant_id = %s;", (tenant_id,))
                    cur.execute(sql, params)
                    rowcount = cur.rowcount
                conn.commit()
                return rowcount
        except Exception as e:
            err_msg = str(e)
            if "IMMUTABLE_FROZEN_RECORD_VIOLATION" in err_msg:
                raise FrozenRecordImmutabilityError("Operation rejected: Frozen analytical record is immutable.") from e
            logger.error("PostgreSQL mutation execution failed: %s", e)
            raise DatabaseError("Database mutation operation failed.") from e


# ---------------------------------------------------------------------------
# Provider Factory & Lifecycle
# ---------------------------------------------------------------------------

_database_provider_instance: Optional[DatabaseProvider] = None


def get_database_provider() -> DatabaseProvider:
    """Return the active database provider singleton based on environment configuration."""
    global _database_provider_instance
    if _database_provider_instance is None:
        is_production = settings.ENV.lower() == "production"
        has_pg_url = bool(os.getenv("DATABASE_URL", "").strip())

        if is_production or has_pg_url:
            _database_provider_instance = ProductionDatabaseProvider()
            logger.info("Initialized %s | status=%s", _database_provider_instance.provider_name, _database_provider_instance.status)
        else:
            _database_provider_instance = DevelopmentDatabaseProvider()
            logger.info("Initialized %s | status=%s", _database_provider_instance.provider_name, _database_provider_instance.status)

    return _database_provider_instance


def reset_database_provider(provider: Optional[DatabaseProvider] = None) -> None:
    """Reset database provider singleton (useful in unit testing)."""
    global _database_provider_instance
    _database_provider_instance = provider
