"""
storage/database/provider.py
============================
Production SaaS Database Abstraction & Persistence Boundary (Task 8.20).

Establishes a strict separation between:
1. PUBLIC / FROZEN: Read-only econometric & statutory baselines (Central 4,700 predictions,
   4,700 decisions, 940 anticipation scores, 14,100 reports, 20 production bills,
   44 State acts, 44 knowledge records, 86 state corporate exposures, 70 company master).
   Never rewritten or mutated.
2. TENANT-OWNED / MUTABLE: Scoped by tenant_id (tenants, memberships, watchlists,
   watchlist items, alert rules, alert events, notifications, notification preferences,
   account lifecycle state).
3. USER-OWNED / PRIVATE: PII and auth credentials (users, password hashes, user preferences,
   personal device/notification tokens).
4. SYSTEM / OPERATIONAL: Operational telemetry (audit logs, AI token usage metering,
   scheduler locks, background jobs, monitoring run history).

Guarantees:
- DatabaseProvider: Base abstract class.
- DevelopmentDatabaseProvider: Uses local file/JSON repository storage.
- ProductionDatabaseProvider: Production PostgreSQL adapter architecture.
- If real PostgreSQL credentials are absent: DATABASE_STATUS = NOT_CONFIGURED.
  Never fabricate a connected database.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import os
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)


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
# PostgreSQL Schema DDL Definition for Tenant Data
# ---------------------------------------------------------------------------

POSTGRES_SCHEMA_DDL = """
-- ============================================================================
-- LEGISLATIVE INTELLIGENCE PLATFORM — PRODUCTION POSTGRESQL SCHEMA (TASK 8.20)
-- Strict separation: Public analytical data remains frozen on disk/object store;
-- PostgreSQL houses strictly tenant-owned, user-owned, and operational data.
-- ============================================================================

-- 1. Users table (User-Owned / Private)
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    external_idp_sub VARCHAR(255) UNIQUE,
    idp_provider VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_external_sub ON users(external_idp_sub);

-- 2. Tenants table (Tenant-Owned / Mutable)
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan_tier VARCHAR(32) DEFAULT 'FREE', -- FREE, PRO, TEAM, ENTERPRISE
    status VARCHAR(32) DEFAULT 'ACTIVE',  -- ACTIVE, SUSPENDED, DEACTIVATED, TRIAL
    billing_customer_id VARCHAR(128),
    subscription_id VARCHAR(128),
    subscription_status VARCHAR(32) DEFAULT 'NONE',
    seats_limit INT DEFAULT 5,
    max_watchlists INT DEFAULT 5,
    max_rules INT DEFAULT 20,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tenants_plan ON tenants(plan_tier);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);

-- 3. Tenant Memberships (Tenant-Owned / RBAC)
CREATE TABLE IF NOT EXISTS tenant_memberships (
    membership_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL DEFAULT 'MEMBER', -- OWNER, ADMIN, MEMBER, VIEWER
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_memberships_tenant ON tenant_memberships(tenant_id);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON tenant_memberships(user_id);

-- 4. Watchlists (Tenant-Owned / Scoped)
CREATE TABLE IF NOT EXISTS watchlists (
    watchlist_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_watchlists_tenant ON watchlists(tenant_id);

-- 5. Watchlist Items (Tenant-Owned / Scoped)
CREATE TABLE IF NOT EXISTS watchlist_items (
    item_id VARCHAR(64) PRIMARY KEY,
    watchlist_id VARCHAR(64) NOT NULL REFERENCES watchlists(watchlist_id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    entity_type VARCHAR(32) NOT NULL, -- 'bill' | 'company' | 'sector'
    entity_id VARCHAR(128) NOT NULL,
    added_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (watchlist_id, entity_type, entity_id)
);
CREATE INDEX IF NOT EXISTS idx_watchlist_items_entity ON watchlist_items(tenant_id, entity_type, entity_id);

-- 6. Alert Rules (Tenant-Owned / Scoped)
CREATE TABLE IF NOT EXISTS alert_rules (
    rule_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(64) NOT NULL,
    conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_alert_rules_tenant ON alert_rules(tenant_id, is_active);

-- 7. Alert Events (Tenant-Owned / Scoped)
CREATE TABLE IF NOT EXISTS alert_events (
    event_id VARCHAR(64) PRIMARY KEY,
    rule_id VARCHAR(64) REFERENCES alert_rules(rule_id) ON DELETE SET NULL,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    bill_id VARCHAR(128),
    company_id VARCHAR(64),
    severity VARCHAR(32) DEFAULT 'MEDIUM',
    event_type VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_alert_events_tenant ON alert_events(tenant_id, created_at DESC);

-- 8. Notifications (Tenant-Owned / Delivery State)
CREATE TABLE IF NOT EXISTS notifications (
    notification_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    channel VARCHAR(32) DEFAULT 'IN_APP', -- IN_APP, EMAIL, WEBHOOK
    status VARCHAR(32) DEFAULT 'UNREAD',  -- UNREAD, READ, DELIVERED, FAILED
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(tenant_id, user_id, status);

-- 9. Notification Preferences (Tenant-Owned / User-Scoped)
CREATE TABLE IF NOT EXISTS notification_preferences (
    preference_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL,
    email_enabled BOOLEAN DEFAULT TRUE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    webhook_url VARCHAR(512),
    digest_frequency VARCHAR(32) DEFAULT 'DAILY', -- REALTIME, DAILY, WEEKLY
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, user_id)
);

-- 10. Audit Logs (System / Operational — Append-Only)
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    action VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id, created_at DESC);

-- 11. AI Usage Records (System / Operational — Metering)
CREATE TABLE IF NOT EXISTS ai_usage_records (
    record_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    model_name VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_ai_usage_tenant ON ai_usage_records(tenant_id, created_at DESC);
"""


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


class DevelopmentDatabaseProvider(DatabaseProvider):
    """
    Development and local testing database provider.
    Operates on local storage/ directories (JSON / file-backed repositories),
    preserving the existing repository contracts without requiring an external PostgreSQL instance.
    """

    def __init__(self) -> None:
        self._data_dirs = [
            settings.USERS_DIR,
            settings.TENANTS_DIR,
            settings.WATCHLIST_DIR,
            settings.ALERTS_DIR,
            settings.AUDIT_DIR,
            settings.AI_USAGE_DIR,
        ]
        for d in self._data_dirs:
            d.mkdir(parents=True, exist_ok=True)

    @property
    def provider_name(self) -> str:
        return "DevelopmentDatabaseProvider (Local File-Backed)"

    @property
    def is_configured(self) -> bool:
        return True

    @property
    def status(self) -> str:
        return "READY"

    def health_check(self) -> dict[str, Any]:
        accessible = all(d.is_dir() for d in self._data_dirs)
        return {
            "provider": self.provider_name,
            "status": "HEALTHY" if accessible else "DEGRADED",
            "connected": accessible,
            "storage_type": "local_filesystem_json",
            "accessible_directories": len(self._data_dirs),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_table_names(self) -> list[str]:
        return [
            "users",
            "tenants",
            "tenant_memberships",
            "watchlists",
            "watchlist_items",
            "alert_rules",
            "alert_events",
            "notifications",
            "notification_preferences",
            "audit_logs",
            "ai_usage_records",
        ]

    def get_schema_ddl(self) -> str:
        return POSTGRES_SCHEMA_DDL

    def migrate_schema(self) -> bool:
        # In development, verifying directories and JSON repositories are initialized
        for d in self._data_dirs:
            d.mkdir(parents=True, exist_ok=True)
        return True


class ProductionDatabaseProvider(DatabaseProvider):
    """
    Production PostgreSQL database provider.
    Establishes connection pool boundaries and executes migration scripts.
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

    def health_check(self) -> dict[str, Any]:
        if not self._is_configured:
            return {
                "provider": self.provider_name,
                "status": "NOT_CONFIGURED",
                "connected": False,
                "message": "DATABASE_URL is not set or contains placeholder credentials.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # If configured, attempt connection probe safely
        try:
            import psycopg2  # type: ignore
            conn = psycopg2.connect(self._database_url, connect_timeout=self._timeout)
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
            conn.close()
            return {
                "provider": self.provider_name,
                "status": "HEALTHY",
                "connected": True,
                "message": "PostgreSQL connection pool verified and responsive.",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except ImportError:
            return {
                "provider": self.provider_name,
                "status": "DRIVER_MISSING",
                "connected": False,
                "message": "psycopg2 / asyncpg driver not installed in current environment.",
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
        return [
            "users",
            "tenants",
            "tenant_memberships",
            "watchlists",
            "watchlist_items",
            "alert_rules",
            "alert_events",
            "notifications",
            "notification_preferences",
            "audit_logs",
            "ai_usage_records",
        ]

    def get_schema_ddl(self) -> str:
        return POSTGRES_SCHEMA_DDL

    def migrate_schema(self) -> bool:
        if not self._is_configured:
            logger.info("Database migration skipped: PostgreSQL credentials are not configured.")
            return False

        try:
            import psycopg2  # type: ignore
            conn = psycopg2.connect(self._database_url, connect_timeout=self._timeout)
            with conn.cursor() as cur:
                cur.execute(POSTGRES_SCHEMA_DDL)
            conn.commit()
            conn.close()
            logger.info("Executed PostgreSQL schema migration successfully.")
            return True
        except Exception as e:
            logger.error("Failed to execute PostgreSQL schema migration: %s", e)
            return False


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
