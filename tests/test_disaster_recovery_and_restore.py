"""
tests/test_disaster_recovery_and_restore.py
===========================================
Task 8.23 Phase 2 — Disaster Recovery, Backup & Restore Verification Suite.

Guarantees Verified:
1. Strict separation of PUBLIC_FROZEN vs TENANT_OWNED_MUTABLE data.
2. Cryptographic SHA-256 backup generation and tamper detection.
3. Restore execution preserves 100% frozen analytical baseline parity.
4. State stock predictions invariant remains STRICTLY ZERO.
5. Migration schema versioning and rollback safety verification.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import pytest

from services.disaster_recovery import (
    CURRENT_SCHEMA_VERSION,
    DisasterRecoveryService,
    MUTABLE_DOMAIN_DIRECTORIES,
)
from storage.database.provider import (
    DATA_CLASSIFICATION_REGISTRY,
    DataClassification,
)


@pytest.fixture
def tmp_backup_service(tmp_path):
    return DisasterRecoveryService(backup_dir=tmp_path)


def test_1_data_domain_classification_registry():
    """Verify all platform data domains are classified and partitioned strictly."""
    frozen_keys = [
        k for k, v in DATA_CLASSIFICATION_REGISTRY.items()
        if v["classification"] == DataClassification.PUBLIC_FROZEN
    ]
    mutable_keys = [
        k for k, v in DATA_CLASSIFICATION_REGISTRY.items()
        if v["classification"] == DataClassification.TENANT_OWNED_MUTABLE
    ]

    # Must contain essential analytical domains as frozen
    assert "central_bills" in frozen_keys
    assert "central_predictions" in frozen_keys
    assert "central_decisions" in frozen_keys
    assert "central_anticipation" in frozen_keys
    assert "central_reports" in frozen_keys
    assert "state_acts" in frozen_keys
    assert "state_knowledge" in frozen_keys
    assert "state_corporate_exposures" in frozen_keys
    assert "company_master" in frozen_keys

    # Must contain tenant-scoped domains as mutable
    assert "tenants" in mutable_keys
    assert "memberships" in mutable_keys
    assert "watchlists" in mutable_keys
    assert "watchlist_items" in mutable_keys
    assert "alert_rules" in mutable_keys
    assert "alert_events" in mutable_keys
    assert "notifications" in mutable_keys


def test_2_tenant_backup_creation_and_manifest(tmp_backup_service, tmp_path):
    """Verify tenant backup creates valid manifest with SHA-256 digests and zero analytical data."""
    out_file, manifest = tmp_backup_service.create_tenant_backup()

    assert out_file.is_file()
    assert manifest.schema_version == CURRENT_SCHEMA_VERSION
    assert manifest.format_version == "1.0"
    assert manifest.frozen_baseline_status == "ISOLATED_FROZEN_NOT_INCLUDED"
    assert len(manifest.manifest_checksum) == 64  # SHA-256 hex length
    assert len(manifest.domain_checksums) >= 8

    # Inspect JSON archive
    with open(out_file, "r", encoding="utf-8") as f:
        archive = json.load(f)

    assert "_manifest" in archive
    assert "data" in archive
    data = archive["data"]

    # Verify no analytical data keys leaked into mutable payload
    for forbidden in ["predictions", "decisions", "anticipation", "central_bills", "state_bills"]:
        assert forbidden not in data


def test_3_backup_integrity_and_tamper_detection(tmp_backup_service, tmp_path):
    """Verify cryptographic integrity check passes on valid backup and rejects tampered archive."""
    out_file, manifest = tmp_backup_service.create_tenant_backup()

    # Valid check
    res = tmp_backup_service.verify_backup_integrity(out_file)
    assert res["valid"] is True
    assert res["checksum_verified"] is True
    assert res["schema_version"] == CURRENT_SCHEMA_VERSION
    assert len(res["mismatched_domains"]) == 0

    # Tampered check
    tampered_file = tmp_path / "tampered.json"
    with open(out_file, "r", encoding="utf-8") as rf:
        archive = json.load(rf)

    # Corrupt data in tenants domain
    if "tenants" in archive["data"]:
        archive["data"]["tenants"]["corrupted_key"] = "malicious payload"

    with open(tampered_file, "w", encoding="utf-8") as wf:
        json.dump(archive, wf)

    tampered_res = tmp_backup_service.verify_backup_integrity(tampered_file)
    assert tampered_res["valid"] is False
    assert tampered_res["checksum_verified"] is False
    assert "tenants" in tampered_res["mismatched_domains"]


def test_4_restore_tenant_backup_and_baseline_immutability(tmp_backup_service):
    """Verify restore reproduces tenant data and validates frozen analytical baseline."""
    out_file, manifest = tmp_backup_service.create_tenant_backup()

    restore_res = tmp_backup_service.restore_tenant_backup(out_file, verify_baseline=True)

    assert restore_res.success is True
    assert restore_res.frozen_baseline_verified is True
    assert restore_res.state_predictions_count == 0
    assert len(restore_res.domains_restored) >= 8
    assert restore_res.error is None


def test_5_schema_version_and_rollback_safety(tmp_backup_service):
    """Verify schema version tracking and migration rollback safety."""
    status = tmp_backup_service.get_schema_version_status()
    assert status["current_schema_version"] == CURRENT_SCHEMA_VERSION
    assert status["rollback_support"] is True
    assert status["analytical_isolation"] == "FROZEN_OBJECT_STORE_ISOLATED"

    # Valid rollback check
    valid_rollback = tmp_backup_service.verify_migration_rollback_safety(CURRENT_SCHEMA_VERSION)
    assert valid_rollback["safe"] is True
    assert valid_rollback["analytical_data_affected"] is False

    # Invalid rollback check
    invalid_rollback = tmp_backup_service.verify_migration_rollback_safety("invalid_v999")
    assert invalid_rollback["safe"] is False
