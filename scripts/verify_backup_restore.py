#!/usr/bin/env python3
"""
scripts/verify_backup_restore.py
================================
Task 8.23 — Deterministic Backup, Restore & Disaster Recovery Verification.

Executes:
1. Data classification partitioning audit (PUBLIC_FROZEN vs TENANT_MUTABLE).
2. Cryptographic backup generation with SHA-256 manifest.
3. Backup integrity & tamper detection verification.
4. Simulated corruption / restore test against test directory.
5. Post-restore analytical immutability verification.
6. Schema version & rollback safety checks.
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.logging_config import get_logger
from services.disaster_recovery import DisasterRecoveryService, CURRENT_SCHEMA_VERSION
from utils.baseline_verifier import verify_production_baseline

logger = get_logger("verify_backup_restore")


def main() -> int:
    print("=" * 70)
    print("TASK 8.23 — DETERMINISTIC BACKUP & DISASTER RECOVERY VERIFICATION")
    print("=" * 70)

    t0 = time.time()
    failures: list[str] = []

    # 1. Audit Data Classification
    print("\n[STEP 1] Data Domain Classification Separation Audit...")
    from storage.database.provider import DATA_CLASSIFICATION_REGISTRY, DataClassification

    frozen_domains = [k for k, v in DATA_CLASSIFICATION_REGISTRY.items() if v["classification"] == DataClassification.PUBLIC_FROZEN]
    mutable_domains = [k for k, v in DATA_CLASSIFICATION_REGISTRY.items() if v["classification"] == DataClassification.TENANT_OWNED_MUTABLE]

    print(f"  - Verified {len(frozen_domains)} PUBLIC_FROZEN domains: {', '.join(frozen_domains[:4])}...")
    print(f"  - Verified {len(mutable_domains)} TENANT_OWNED_MUTABLE domains: {', '.join(mutable_domains[:4])}...")

    if len(frozen_domains) < 9 or len(mutable_domains) < 6:
        failures.append("Insufficient data classification mapping")
        print("  [FAIL] Incomplete classification registry")
    else:
        print("  [PASS] Data domains cleanly partitioned")

    # 2. Backup Generation
    print("\n[STEP 2] Cryptographic Tenant Backup Generation...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        dr_service = DisasterRecoveryService(backup_dir=tmp_path)

        backup_file, manifest = dr_service.create_tenant_backup()
        print(f"  - Backup Archive: {backup_file.name}")
        print(f"  - Schema Version: {manifest.schema_version}")
        print(f"  - Manifest SHA-256: {manifest.manifest_checksum[:16]}...")
        print(f"  - Frozen Baseline Status: {manifest.frozen_baseline_status}")

        if not backup_file.exists() or backup_file.stat().st_size == 0:
            failures.append("Backup archive not created or empty")
            print("  [FAIL] Backup generation failed")
        else:
            print("  [PASS] Backup archive created successfully")

        # 3. Integrity Verification
        print("\n[STEP 3] Backup Integrity Verification & Tamper Detection...")
        integrity = dr_service.verify_backup_integrity(backup_file)
        if not integrity.get("valid"):
            failures.append(f"Backup integrity verification failed: {integrity.get('error')}")
            print(f"  [FAIL] Integrity check failed: {integrity.get('error')}")
        else:
            print("  [PASS] Cryptographic integrity verified (all domain digests match)")

        # Test tamper detection
        tampered_file = tmp_path / "tampered_backup.json"
        with open(backup_file, "r", encoding="utf-8") as rf:
            archive_data = json.load(rf)

        # Alter one byte in a payload
        if archive_data.get("data", {}).get("tenants"):
            first_key = next(iter(archive_data["data"]["tenants"].keys()))
            archive_data["data"]["tenants"][first_key] += " "
        else:
            archive_data["data"]["tenants"] = {"dummy_tamper.json": "{}"}

        with open(tampered_file, "w", encoding="utf-8") as wf:
            json.dump(archive_data, wf)

        tampered_integrity = dr_service.verify_backup_integrity(tampered_file)
        if tampered_integrity.get("valid"):
            failures.append("Tamper detection failed: tampered archive was accepted as valid")
            print("  [FAIL] Tampered backup was falsely accepted")
        else:
            print(f"  [PASS] Tampered archive correctly rejected ({tampered_integrity.get('error')})")

        # 4. Restore Simulation & Baseline Invariant Verification
        print("\n[STEP 4] Deterministic Restore & Baseline Invariant Validation...")
        restore_res = dr_service.restore_tenant_backup(backup_file, verify_baseline=True)

        print(f"  - Restore ID: {restore_res.restore_id}")
        print(f"  - Domains Restored: {len(restore_res.domains_restored)}")
        print(f"  - Files Restored: {restore_res.records_restored_total}")
        print(f"  - Frozen Baseline Verified: {restore_res.frozen_baseline_verified}")
        print(f"  - State Predictions Count: {restore_res.state_predictions_count} (Must be exactly 0)")

        if not restore_res.success or not restore_res.frozen_baseline_verified or restore_res.state_predictions_count != 0:
            failures.append("Restore validation failed or frozen baseline violated")
            print("  [FAIL] Restore validation failed")
        else:
            print("  [PASS] Restore succeeded with 100% baseline parity preserved")

        # 5. Schema Version & Rollback Safety Check
        print("\n[STEP 5] Schema Version & Migration Rollback Safety...")
        ver_status = dr_service.get_schema_version_status()
        rollback_check = dr_service.verify_migration_rollback_safety(CURRENT_SCHEMA_VERSION)
        print(f"  - Active Schema: {ver_status['current_schema_version']}")
        print(f"  - Migration Safety: {ver_status['migration_safety']}")
        print(f"  - Analytical Decoupling: {ver_status['analytical_isolation']}")
        print(f"  - Rollback Safe: {rollback_check['safe']}")

        if not rollback_check["safe"]:
            failures.append("Schema rollback safety check failed")
            print("  [FAIL] Schema rollback safety check failed")
        else:
            print("  [PASS] Schema rollback verified non-destructive to frozen baseline")

    duration = time.time() - t0
    print("\n" + "=" * 70)
    if not failures:
        print(f"SUCCESS: ALL DISASTER RECOVERY & BACKUP CHECKS PASSED ({duration:.2f}s)")
        print("=" * 70)
        return 0
    else:
        print(f"FAILED: {len(failures)} DISASTER RECOVERY CHECKS FAILED:")
        for f in failures:
            print(f"  - {f}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
