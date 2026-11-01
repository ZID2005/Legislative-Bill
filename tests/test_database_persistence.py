"""
tests/test_database_persistence.py
==================================
Comprehensive automated test suite for Task 8.31D:
PostgreSQL Persistence & Supabase-Free Compatible Architecture.

Validates:
1. Canonical schema, migrations runner, and schema idempotency.
2. Exact frozen analytical baseline counts and SHA-256 integrity.
3. Statutory state prediction firewall (0 state stock predictions).
4. Intelligence-only company firewall (20 companies strictly quarantined).
5. Immutability enforcement on frozen analytical records.
6. Multi-tenant data isolation and IDOR protections.
7. Database provider error handling and resilience.
8. Repositories dual persistence (DB + fallback).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import pytest
import sqlite3
import uuid

from config.settings import settings
from storage.database.migrator import MigrationRunner
from storage.database.provider import (
    get_database_provider,
    DatabaseProvider,
    DevelopmentDatabaseProvider,
    ProductionDatabaseProvider,
    FrozenRecordImmutabilityError,
    RecordNotFoundError,
    TenantMismatchError,
    PermissionDeniedError,
)
from storage.portfolio_repository import PortfolioRepository
from storage.watchlist_repository import WatchlistRepository
from storage.user_repository import UserRepository
from storage.tenant_repository import TenantRepository
from schemas.portfolio import UserPortfolio, PortfolioHolding
from schemas.watchlist import Watchlist, WatchlistItem, WatchlistEntityType
from schemas.user import User
from schemas.tenant import Tenant

CANONICAL_BASELINE_SHA256 = "50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7"

AUTHORITATIVE_EVENT_HORIZONS = ["[-1,+1]", "[-3,+3]", "[-5,+5]", "[-5,+10]", "[-10,+10]"]


@pytest.fixture(scope="module")
def db():
    """Provides active database provider."""
    provider = get_database_provider()
    assert provider is not None
    assert provider.status in ("READY", "CONFIGURED")
    return provider


# ==============================================================================
# 1. SCHEMA AND MIGRATION TESTS
# ==============================================================================

class TestSchemaAndMigrations:
    """Verifies standard PostgreSQL schema migrations and idempotency."""

    def test_01_migrations_applied_and_tracked(self, db):
        rows = db.execute_query("SELECT version, name, checksum, applied_at FROM schema_migrations ORDER BY version;")
        assert len(rows) >= 3, "Expected at least 3 migrations applied"
        versions = [r["version"] for r in rows]
        assert "001" in versions
        assert "002" in versions
        assert "003" in versions

    def test_02_migration_runner_idempotent(self):
        runner = MigrationRunner()
        # Running migrations again must return empty list (no pending migrations)
        applied = runner.run_migrations()
        assert applied == []

    def test_03_all_expected_tables_exist(self, db):
        expected_tables = {
            "tenants", "users", "tenant_memberships", "user_preferences",
            "jurisdictions", "bills", "bill_versions", "official_documents",
            "sources", "source_health", "sectors", "industries", "companies",
            "corporate_exposures", "evidence_sources", "evidence",
            "portfolios", "portfolio_holdings", "watchlists", "watchlist_items",
            "alert_rules", "alert_events", "notifications", "notification_preferences",
            "saved_searches", "audit_logs", "ai_usage_records",
            "analytical_baselines", "predictions", "decisions", "anticipation_scores",
            "stakeholder_reports", "schema_migrations",
        }
        actual_tables = set(db.get_table_names())
        missing = expected_tables - actual_tables
        assert not missing, f"Missing tables in database: {missing}"


# ==============================================================================
# 2. FROZEN ANALYTICAL BASELINE AND EXACT RECORD COUNTS
# ==============================================================================

class TestFrozenBaselineAndRecordCounts:
    """Verifies baseline immutability, exact counts, and SHA-256 hash."""

    def test_04_baseline_manifest_hash(self, db):
        rows = db.execute_query("SELECT baseline_id, version, sha256, status, is_frozen FROM analytical_baselines;")
        assert len(rows) >= 1
        b = rows[0]
        assert b["sha256"] == CANONICAL_BASELINE_SHA256
        assert b["status"] == "FROZEN"
        assert bool(b["is_frozen"]) is True

    def test_05_central_bills_count(self, db):
        # 20 production bills + 2 auxiliary bills = 22 Central bills
        prod_central = db.execute_query("SELECT COUNT(*) as c FROM bills WHERE jurisdiction = 'central' AND is_production = 1;")[0]["c"]
        total_central = db.execute_query("SELECT COUNT(*) as c FROM bills WHERE jurisdiction = 'central';")[0]["c"]
        assert prod_central == 20, f"Expected 20 Central production bills, got {prod_central}"
        assert total_central == 22, f"Expected 22 total Central bills, got {total_central}"

    def test_06_state_bills_count(self, db):
        # 44 state bills across 4 states
        total_state = db.execute_query("SELECT COUNT(*) as c FROM bills WHERE jurisdiction = 'state';")[0]["c"]
        assert total_state == 44, f"Expected 44 state bills, got {total_state}"

        # Per state breakdown
        states = {"Andhra Pradesh": 12, "Karnataka": 11, "Kerala": 11, "Telangana": 10}
        for state, expected_count in states.items():
            cnt = db.execute_query("SELECT COUNT(*) as c FROM bills WHERE state = %s;", (state,))[0]["c"]
            assert cnt == expected_count, f"Expected {expected_count} bills for {state}, got {cnt}"

    def test_07_corporate_universe_counts(self, db):
        # 70 companies: 47 quantitative, 20 intelligence-only, 3 reference
        total = db.execute_query("SELECT COUNT(*) as c FROM companies;")[0]["c"]
        assert total == 70, f"Expected 70 total companies, got {total}"

        quant = db.execute_query("SELECT COUNT(*) as c FROM companies WHERE coverage_tier = 'QUANTITATIVE';")[0]["c"]
        assert quant == 47, f"Expected 47 quantitative companies, got {quant}"

        intel = db.execute_query("SELECT COUNT(*) as c FROM companies WHERE coverage_tier = 'INTELLIGENCE_ONLY';")[0]["c"]
        assert intel == 20, f"Expected 20 intelligence-only companies, got {intel}"

        ref = db.execute_query("SELECT COUNT(*) as c FROM companies WHERE coverage_tier = 'REFERENCE';")[0]["c"]
        assert ref == 3, f"Expected 3 reference companies, got {ref}"

    def test_08_corporate_exposures_count(self, db):
        total_exp = db.execute_query("SELECT COUNT(*) as c FROM corporate_exposures;")[0]["c"]
        assert total_exp == 104, f"Expected 104 corporate exposures, got {total_exp}"

    def test_09_predictions_exact_count_and_horizons(self, db):
        pred_cnt = db.execute_query("SELECT COUNT(*) as c FROM predictions;")[0]["c"]
        assert pred_cnt == 4700, f"Expected 4,700 predictions, got {pred_cnt}"

        # Distinct horizons must match the 5 authoritative horizons
        horizon_rows = db.execute_query("SELECT DISTINCT event_window FROM predictions ORDER BY event_window;")
        horizons = sorted([r["event_window"] for r in horizon_rows])
        assert horizons == sorted(AUTHORITATIVE_EVENT_HORIZONS)

        # 940 pairs per horizon = 4,700 total
        for h in AUTHORITATIVE_EVENT_HORIZONS:
            h_cnt = db.execute_query("SELECT COUNT(*) as c FROM predictions WHERE event_window = %s;", (h,))[0]["c"]
            assert h_cnt == 940, f"Expected 940 predictions for horizon {h}, got {h_cnt}"

    def test_10_decisions_exact_count(self, db):
        dec_cnt = db.execute_query("SELECT COUNT(*) as c FROM decisions;")[0]["c"]
        assert dec_cnt == 4700, f"Expected 4,700 decisions, got {dec_cnt}"

    def test_11_anticipation_scores_exact_count(self, db):
        ant_cnt = db.execute_query("SELECT COUNT(*) as c FROM anticipation_scores;")[0]["c"]
        assert ant_cnt == 940, f"Expected 940 anticipation scores, got {ant_cnt}"

    def test_12_stakeholder_reports_exact_count(self, db):
        rep_cnt = db.execute_query("SELECT COUNT(*) as c FROM stakeholder_reports;")[0]["c"]
        assert rep_cnt == 14100, f"Expected 14,100 stakeholder reports, got {rep_cnt}"


# ==============================================================================
# 3. STATUTORY STATE AND INTELLIGENCE-ONLY FIREWALLS
# ==============================================================================

class TestStatutoryFirewalls:
    """Verifies that state stock predictions and intelligence-only quantitative predictions are strictly blocked."""

    def test_13_state_stock_predictions_remain_zero(self, db):
        # Invariant: STATE STOCK PREDICTIONS = 0
        state_preds = db.execute_query(
            "SELECT COUNT(*) as c FROM predictions WHERE bill_id LIKE 'ap_%' OR bill_id LIKE 'ka_%' OR bill_id LIKE 'kl_%' OR bill_id LIKE 'ts_%';"
        )[0]["c"]
        assert state_preds == 0, f"State prediction breach! Found {state_preds} state predictions"

    def test_14_reject_inserting_state_bill_into_predictions(self, db):
        # Database constraint or application firewall must reject state bill prediction
        with pytest.raises(Exception):
            db.execute_mutation(
                """
                INSERT INTO predictions (
                    prediction_id, baseline_id, bill_id, company_isin, event_window,
                    predicted_direction, is_frozen
                ) VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                ("test_invalid_state_pred", "production_baseline_v1", "kl_bill_001", "INE002A01018", "[-1,+1]", "UP", True),
            )

    def test_15_intelligence_only_companies_quarantined_from_predictions(self, db):
        # Invariant: INTELLIGENCE-ONLY companies must never have quantitative stock predictions
        rows = db.execute_query(
            """
            SELECT COUNT(*) as c
            FROM predictions p
            JOIN companies c ON p.company_isin = c.isin
            WHERE c.coverage_tier = 'INTELLIGENCE_ONLY';
            """
        )
        assert rows[0]["c"] == 0, "Intelligence-only companies found in predictions table!"


# ==============================================================================
# 4. IMMUTABILITY ENFORCEMENT
# ==============================================================================

class TestImmutabilityEnforcement:
    """Verifies that frozen analytical records cannot be updated or deleted."""

    def test_16_prevent_updating_frozen_prediction(self, db):
        # Pick an existing frozen prediction
        rows = db.execute_query("SELECT prediction_id FROM predictions LIMIT 1;")
        pred_id = rows[0]["prediction_id"]

        with pytest.raises(FrozenRecordImmutabilityError):
            db.execute_mutation(
                "UPDATE predictions SET predicted_direction = 'DOWN' WHERE prediction_id = %s;",
                (pred_id,)
            )

    def test_17_prevent_deleting_frozen_prediction(self, db):
        rows = db.execute_query("SELECT prediction_id FROM predictions LIMIT 1;")
        pred_id = rows[0]["prediction_id"]

        with pytest.raises(FrozenRecordImmutabilityError):
            db.execute_mutation(
                "DELETE FROM predictions WHERE prediction_id = %s;",
                (pred_id,)
            )

    def test_18_prevent_updating_frozen_baseline(self, db):
        with pytest.raises(FrozenRecordImmutabilityError):
            db.execute_mutation(
                "UPDATE analytical_baselines SET status = 'MUTATED' WHERE baseline_id = 'production_baseline_v1';"
            )


# ==============================================================================
# 5. MULTI-TENANCY AND IDOR ISOLATION
# ==============================================================================

class TestMultiTenancyAndIsolation:
    """Verifies that tenant data is strictly partitioned and IDOR attempts are rejected."""

    def test_19_tenant_isolation_on_portfolios(self, db):
        repo = PortfolioRepository()
        t1 = "tenant_alpha_test"
        u1 = "user_alpha_test"
        t2 = "tenant_beta_test"
        u2 = "user_beta_test"

        p1_id = f"port_{uuid.uuid4().hex[:8]}"
        p1 = UserPortfolio(
            portfolio_id=p1_id,
            tenant_id=t1,
            user_id=u1,
            name="Alpha Tech Portfolio",
            holdings=[
                PortfolioHolding(
                    holding_id=f"h_{uuid.uuid4().hex[:8]}",
                    company_name="Reliance Industries",
                    isin="INE002A01018",
                    ticker="RELIANCE",
                    quantity=100.0,
                    avg_purchase_price=2500.0,
                    current_value=260000.0,
                )
            ]
        )
        repo.create(p1)

        # 1. Tenant Alpha reads its own portfolio -> ALLOW
        res_alpha = repo.get(p1_id, tenant_id=t1, user_id=u1)
        assert res_alpha is not None
        assert res_alpha.portfolio_id == p1_id
        assert len(res_alpha.holdings) == 1

        # 2. Tenant Beta attempts to access Tenant Alpha's portfolio -> DENY (returns None)
        res_beta = repo.get(p1_id, tenant_id=t2, user_id=u2)
        assert res_beta is None, "IDOR breach: Tenant Beta accessed Tenant Alpha's portfolio!"

        # 3. Clean up
        repo.delete(p1_id, tenant_id=t1, user_id=u1)

    def test_20_tenant_isolation_on_watchlists(self, db):
        repo = WatchlistRepository()
        t1 = "tenant_alpha_wl"
        u1 = "user_alpha_wl"
        t2 = "tenant_beta_wl"
        u2 = "user_beta_wl"

        wl_id = f"wl_{uuid.uuid4().hex[:8]}"
        wl = Watchlist(
            watchlist_id=wl_id,
            tenant_id=t1,
            user_id=u1,
            name="Alpha Watchlist",
        )
        repo.create(wl)

        # 1. Tenant Alpha reads its own watchlist -> ALLOW
        res_alpha = repo.get(wl_id, tenant_id=t1, user_id=u1)
        assert res_alpha is not None
        assert res_alpha.watchlist_id == wl_id

        # 2. Tenant Beta attempts to access Tenant Alpha's watchlist -> DENY (returns None)
        res_beta = repo.get(wl_id, tenant_id=t2, user_id=u2)
        assert res_beta is None, "IDOR breach: Tenant Beta accessed Tenant Alpha's watchlist!"

        # 3. Clean up
        repo.delete(wl_id, tenant_id=t1, user_id=u1, hard_delete=True)

    def test_21_tenant_repository_dual_persistence(self, db):
        repo = TenantRepository()
        tid = f"org_{uuid.uuid4().hex[:8]}"
        t = Tenant(
            tenant_id=tid,
            name="Test Research Corp",
            plan_tier="FREE",
            status="ACTIVE",
        )
        repo.create(t)

        fetched = repo.get(tid)
        assert fetched is not None
        assert fetched.tenant_id == tid
        assert fetched.name == "Test Research Corp"

        # Update
        fetched.name = "Test Research Corp Updated"
        repo.update(fetched)
        updated = repo.get(tid)
        assert updated.name == "Test Research Corp Updated"

        # Soft delete
        repo.soft_delete(tid)
        deleted = repo.get(tid)
        assert deleted.status == "DELETED"

    def test_22_user_repository_dual_persistence(self, db):
        repo = UserRepository()
        uid = f"usr_{uuid.uuid4().hex[:8]}"
        tid = "default_tenant"
        u = User(
            user_id=uid,
            tenant_id=tid,
            display_name="Persistence Tester",
            email=f"{uid}@example.com",
            role="MEMBER",
            status="ACTIVE",
        )
        repo.create(u)

        fetched = repo.get(uid, tenant_id=tid)
        assert fetched is not None
        assert fetched.user_id == uid
        assert fetched.email == f"{uid}@example.com"

        # Lookup by email
        by_email = repo.get_by_email(f"{uid}@example.com", tenant_id=tid)
        assert by_email is not None
        assert by_email.user_id == uid


# ==============================================================================
# 6. DATABASE PROVIDER RESILIENCE
# ==============================================================================

class TestDatabaseProviderResilience:
    """Verifies provider status, health check, and error handling."""

    def test_23_health_check_healthy(self, db):
        health = db.health_check()
        assert health["status"] in ("HEALTHY", "READY")
        assert health["connected"] is True

    def test_24_missing_record_handling(self, db):
        # Non-existent ID query returns empty list without crashing
        res = db.execute_query("SELECT * FROM portfolios WHERE portfolio_id = %s;", ("non_existent_12345",))
        assert res == []

    def test_25_invalid_sql_raises_database_error_without_leaking_credentials(self, db):
        with pytest.raises(Exception) as exc_info:
            db.execute_query("SELECT * FROM completely_fake_nonexistent_table_xyz;")
        err_msg = str(exc_info.value)
        # Verify no credentials leaked in error message
        assert "password" not in err_msg.lower()
