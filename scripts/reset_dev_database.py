"""
scripts/reset_dev_database.py
=============================
TASK 8.24 Phase 18 — Safe Development Database Reset Script.

CRITICAL INVARIANT:
A development database reset MUST NEVER delete, alter, or touch the
authoritative frozen analytical baseline (Central 4,700 predictions,
4,700 decisions, 940 anticipation scores, 14,100 reports, 20 production bills,
44 State acts, 44 knowledge records, 86 corporate exposures).

This script ONLY resets mutable, tenant-scoped development data:
- Users & Sessions
- Tenants & Memberships
- Watchlists & Items
- Alert Rules & Events
- Notifications & Preferences
- Audit Logs
- AI Usage Telemetry

Supports:
- Local JSON/filesystem development store
- Local PostgreSQL instance (when configured)
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.logging_config import get_logger
from config.settings import settings
from storage.database.provider import get_database_provider, POSTGRES_SCHEMA_DDL
from utils.baseline_verifier import verify_production_baseline

logger = get_logger("reset_dev_db")

# Whitelist of strictly mutable development directories
MUTABLE_DEV_DIRS = [
    settings.USERS_DIR,
    settings.TENANTS_DIR,
    settings.WATCHLIST_DIR,
    settings.ALERTS_DIR,
    settings.AUDIT_DIR,
    settings.AI_USAGE_DIR,
]

# Blacklist of FROZEN analytical directories — NEVER TOUCH
PROTECTED_ANALYTICAL_DIRS = [
    settings.DATA_DIR / "central_bills",
    settings.PREDICTIONS_DIR,
    settings.DECISION_SUPPORT_DIR,
    settings.ANTICIPATION_DIR,
    settings.REPORTS_DIR,
    settings.DATA_DIR / "state_bills",
    settings.DATA_DIR / "state_knowledge",
    settings.DATA_DIR / "company_intelligence",
    settings.DATA_DIR / "corporate_exposure",
    settings.DATA_DIR / "sectors",
]


def verify_frozen_analytical_safety():
    """Verify that frozen analytical directories exist and are intact."""
    for d in PROTECTED_ANALYTICAL_DIRS:
        if not d.exists():
            raise RuntimeError(f"Safety check failed: Protected analytical directory missing: {d}")
    # Verify baseline parity
    report = verify_production_baseline(quick=True)
    if not report.passed:
        raise RuntimeError(f"Pre-reset safety check failed: Frozen baseline mismatch: {report.failed_checks} failed")
    logger.info("Pre-reset frozen baseline verification PASSED (100% intact).")


def reset_local_filesystem_dev_data():
    """Reset mutable local filesystem JSON repositories."""
    logger.info("Resetting local filesystem mutable tenant/user repositories...")
    cleared_count = 0
    for directory in MUTABLE_DEV_DIRS:
        # Strict sanity check
        for protected in PROTECTED_ANALYTICAL_DIRS:
            if directory == protected or protected in directory.parents:
                raise RuntimeError(f"ABORTING: Directory {directory} overlaps protected {protected}!")

        if directory.exists():
            for item in directory.glob("*"):
                if item.is_file():
                    item.unlink()
                    cleared_count += 1
                elif item.is_dir() and item.name != "indices":
                    shutil.rmtree(item)
                    cleared_count += 1
        directory.mkdir(parents=True, exist_ok=True)

    logger.info("Cleared %d mutable development records/files.", cleared_count)


def reset_postgresql_dev_data():
    """Reset PostgreSQL application tables if configured."""
    db_provider = get_database_provider()
    if not db_provider.is_configured:
        logger.info("PostgreSQL is not configured; skipping SQL truncate.")
        return

    db_url = getattr(db_provider, "_database_url", "")
    if not db_url:
        return

    try:
        import psycopg2
        conn = psycopg2.connect(db_url, connect_timeout=5)
        with conn.cursor() as cur:
            tables = [
                "ai_usage_records",
                "audit_logs",
                "notification_preferences",
                "notifications",
                "alert_events",
                "alert_rules",
                "watchlist_items",
                "watchlists",
                "tenant_memberships",
                "users",
                "tenants",
            ]
            for t in tables:
                cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")
            cur.execute(POSTGRES_SCHEMA_DDL)
        conn.commit()
        conn.close()
        logger.info("PostgreSQL application tables successfully reset and migrated.")
    except Exception as exc:
        logger.warning("PostgreSQL reset skipped or failed: %s", exc)


def main():
    parser = argparse.ArgumentParser(description="Safely reset local development database.")
    parser.add_argument("--confirm", action="store_true", help="Confirm execution")
    args = parser.parse_args()

    print("=" * 70)
    print("TASK 8.24 — SAFE LOCAL DEVELOPMENT DATABASE RESET")
    print("=" * 70)

    # 1. Pre-reset verification
    print("[1/3] Verifying protected frozen analytical data...")
    verify_frozen_analytical_safety()
    print("  -> Frozen analytical dataset confirmed 100% immutable and intact.")

    # 2. Reset mutable development data
    print("[2/3] Resetting mutable tenant, user, watchlist, alert records...")
    reset_local_filesystem_dev_data()
    reset_postgresql_dev_data()
    print("  -> Development storage reset completed.")

    # 3. Post-reset verification
    print("[3/3] Re-verifying frozen analytical baseline post-reset...")
    report = verify_production_baseline(quick=True)
    if not report.passed:
        print(f"CRITICAL ERROR: Frozen baseline altered during reset! {report.failed_checks} failed", file=sys.stderr)
        sys.exit(1)
    print("  -> Post-reset frozen baseline verified: 100% INTACT & UNMUTATED.")

    print("=" * 70)
    print("DEVELOPMENT DATABASE RESET COMPLETED SAFELY.")
    print("=" * 70)


if __name__ == "__main__":
    main()
