"""
storage/database/migrator.py
============================
Deterministic, Idempotent PostgreSQL & SQLite-Compatible Schema Migration Runner.

Manages versioned SQL schema migrations located in the `migrations/` directory:
- 001_initial_core_schema.sql
- 002_analytical_baseline_schema.sql
- 003_row_level_security.sql

Guarantees:
1. Repeatable and idempotent execution.
2. Checksum validation (SHA-256) on all migration scripts.
3. Tracking in `schema_migrations` ledger table.
4. Clean rollback on statement failure without partial state corruption.
5. Works on PostgreSQL (Local & Supabase Free) and local SQLite fallback.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

MIGRATIONS_DIR = settings.PROJECT_ROOT / "migrations"


def get_migration_files() -> list[Path]:
    """Return all SQL migration files sorted lexicographically by version number."""
    if not MIGRATIONS_DIR.is_dir():
        return []
    return sorted([f for f in MIGRATIONS_DIR.glob("*.sql") if f.is_file()])


def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA-256 checksum of migration file content."""
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


class MigrationRunner:
    """
    Executes and tracks SQL schema migrations.
    """

    def __init__(self, migrations_dir: Optional[Path] = None) -> None:
        self.migrations_dir = migrations_dir or MIGRATIONS_DIR

    def ensure_migrations_table(self, cursor: Any, is_sqlite: bool = False) -> None:
        """Create the schema_migrations tracking table if it does not already exist."""
        timestamp_type = "TEXT" if is_sqlite else "TIMESTAMPTZ"
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(64) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                applied_at {timestamp_type} DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

    def get_applied_migrations(self, cursor: Any) -> dict[str, str]:
        """Return dict of {version: checksum} for previously applied migrations."""
        cursor.execute("SELECT version, checksum FROM schema_migrations ORDER BY version ASC;")
        rows = cursor.fetchall()
        return {r[0]: r[1] for r in rows}

    def run_migrations(self, connection: Any = None, is_sqlite: Optional[bool] = None) -> list[str]:
        """
        Execute all pending migrations against the provided database connection.
        If connection is None, auto-acquires a connection from the active DatabaseProvider.
        Returns list of newly applied migration names.
        """
        if connection is None:
            from storage.database.provider import get_database_provider, DevelopmentDatabaseProvider
            provider = get_database_provider()
            if isinstance(provider, DevelopmentDatabaseProvider):
                with provider._get_connection() as conn:
                    return self._execute_migration_flow(conn, is_sqlite=True)
            else:
                with provider._get_connection() as conn:
                    return self._execute_migration_flow(conn, is_sqlite=False)

        if is_sqlite is None:
            is_sqlite = "sqlite" in type(connection).__module__.lower() or "sqlite" in type(connection).__name__.lower()
        return self._execute_migration_flow(connection, is_sqlite=is_sqlite)

    def _execute_migration_flow(self, connection: Any, is_sqlite: bool = False) -> list[str]:
        applied: list[str] = []
        files = get_migration_files()
        if not files:
            logger.warning("No migration files found in %s", self.migrations_dir)
            return applied

        cursor = connection.cursor()
        try:
            self.ensure_migrations_table(cursor, is_sqlite=is_sqlite)
            existing = self.get_applied_migrations(cursor)

            for mf in files:
                version = mf.name.split("_")[0]
                name = mf.stem
                checksum = compute_file_checksum(mf)

                if version in existing:
                    # Checksum verification against tampering
                    if existing[version] != checksum:
                        logger.warning(
                            "Migration %s checksum mismatch! Expected: %s, Found: %s",
                            name, existing[version], checksum
                        )
                    continue

                logger.info("Executing database migration: %s (version=%s)...", name, version)
                sql_content = mf.read_text(encoding="utf-8")

                if is_sqlite:
                    # Strip or adapt PostgreSQL specific features for SQLite testing fallback
                    statements = self._adapt_pg_to_sqlite(sql_content)
                    for stmt in statements:
                        stmt_clean = stmt.strip()
                        if stmt_clean:
                            cursor.execute(stmt_clean)
                else:
                    cursor.execute(sql_content)

                cursor.execute(
                    """
                    INSERT INTO schema_migrations (version, name, checksum)
                    VALUES (%s, %s, %s);
                    """ if not is_sqlite else
                    """
                    INSERT INTO schema_migrations (version, name, checksum)
                    VALUES (?, ?, ?);
                    """,
                    (version, name, checksum),
                )
                connection.commit()
                applied.append(name)
                logger.info("Migration %s successfully applied.", name)

        except Exception as e:
            connection.rollback()
            logger.error("Database migration failed during execution: %s", e)
            raise
        finally:
            cursor.close()

        return applied

    def _adapt_pg_to_sqlite(self, sql_content: str) -> list[str]:
        """
        Adapt PostgreSQL DDL for in-memory SQLite compatibility during unit tests.
        Removes PostgreSQL-specific procedural constructs, triggers, and JSONB casts.
        """
        cleaned = sql_content
        # Replace TIMESTAMPTZ with TEXT
        cleaned = cleaned.replace("TIMESTAMPTZ", "TEXT")
        # Replace JSONB with TEXT
        cleaned = cleaned.replace("JSONB", "TEXT")
        # Replace NUMERIC(x, y) with REAL
        import re
        cleaned = re.sub(r"NUMERIC\(\d+,\s*\d+\)", "REAL", cleaned)
        # Remove '::jsonb'
        cleaned = cleaned.replace("::jsonb", "")
        # Remove plpgsql function & trigger blocks which SQLite cannot parse
        cleaned = re.sub(
            r"CREATE\s+OR\s+REPLACE\s+FUNCTION.*?\$\$.*?\$\$\s*LANGUAGE\s+\w+.*?;",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )
        cleaned = re.sub(
            r"DROP\s+TRIGGER\s+IF\s+EXISTS.*?;",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )
        cleaned = re.sub(
            r"CREATE\s+TRIGGER.*?;",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )
        cleaned = re.sub(
            r"ALTER\s+TABLE\s+\w+\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY\s*;",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )
        cleaned = re.sub(
            r"CREATE\s+POLICY.*?;",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )
        cleaned = re.sub(
            r"DROP\s+POLICY\s+IF\s+EXISTS.*?;",
            "",
            cleaned,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Split on semicolon
        stmts = [s.strip() for s in cleaned.split(";") if s.strip()]
        return stmts
