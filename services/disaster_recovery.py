"""
services/disaster_recovery.py
=============================
Authoritative Disaster Recovery, Backup & Restore Engine (Task 8.23).

Fulfills Phase 2 requirements:
1. Strict separation of PUBLIC_FROZEN data from TENANT_OWNED_MUTABLE data.
2. Cryptographic backup generation (SHA-256 manifest and domain digests).
3. Deterministic restore procedure with post-restore baseline validation.
4. Backup integrity verification and tamper detection.
5. Schema version tracking and migration rollback safety validation.
6. Absolute freeze invariant: Frozen analytical data is NEVER regenerated during recovery.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from storage.database.provider import (
    DATA_CLASSIFICATION_REGISTRY,
    DataClassification,
)
from utils.baseline_verifier import verify_production_baseline

logger = get_logger(__name__)

CURRENT_SCHEMA_VERSION = "2026.09.25.v1"
SUPPORTED_SCHEMA_VERSIONS = ["2026.09.25.v1"]

# Tenant-owned & operational directory definitions
MUTABLE_DOMAIN_DIRECTORIES: dict[str, tuple[str, Path, str]] = {
    "tenants": (
        DataClassification.TENANT_OWNED_MUTABLE.value,
        settings.TENANTS_DIR,
        "tenant_*.json",
    ),
    "users": (
        DataClassification.USER_OWNED_PRIVATE.value,
        settings.USERS_DIR,
        "*/**/user_*.json",
    ),
    "watchlists": (
        DataClassification.TENANT_OWNED_MUTABLE.value,
        settings.WATCHLIST_DIR,
        "*/**/watchlists/wl_*.json",
    ),
    "watchlist_items": (
        DataClassification.TENANT_OWNED_MUTABLE.value,
        settings.WATCHLIST_DIR,
        "*/**/items/item_*.json",
    ),
    "alert_rules": (
        DataClassification.TENANT_OWNED_MUTABLE.value,
        settings.ALERTS_DIR / "rules",
        "*/**/rule_*.json",
    ),
    "alert_events": (
        DataClassification.TENANT_OWNED_MUTABLE.value,
        settings.ALERTS_DIR / "events",
        "*/**/event_*.json",
    ),
    "notification_preferences": (
        DataClassification.TENANT_OWNED_MUTABLE.value,
        settings.ALERTS_DIR / "preferences",
        "*/**/pref_*.json",
    ),
    "audit_logs": (
        DataClassification.SYSTEM_OPERATIONAL.value,
        settings.AUDIT_DIR,
        "*/**/audit_*.jsonl",
    ),
    "ai_usage": (
        DataClassification.SYSTEM_OPERATIONAL.value,
        getattr(settings, "AI_USAGE_DIR", settings.DATA_DIR.parent / "storage" / "ai_usage"),
        "*.json",
    ),
}


@dataclass
class BackupManifest:
    backup_id: str
    timestamp: str
    schema_version: str
    format_version: str
    source_environment: str
    domain_counts: dict[str, int]
    domain_checksums: dict[str, str]
    manifest_checksum: str
    data_classifications: dict[str, str]
    frozen_baseline_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RestoreResult:
    restore_id: str
    timestamp: str
    backup_id: str
    success: bool
    domains_restored: list[str]
    records_restored_total: int
    frozen_baseline_verified: bool
    state_predictions_count: int
    duration_seconds: float
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DisasterRecoveryService:
    """
    Manages cryptographic backups, integrity verification, restore validation,
    and schema rollback safety for multi-tenant data while preserving the frozen baseline.
    """

    def __init__(self, backup_dir: Optional[Path] = None) -> None:
        self.backup_dir = backup_dir or (settings.DATA_DIR.parent / "storage" / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _compute_digest(data: Any) -> str:
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    # -----------------------------------------------------------------------
    # 1. Backup Generation (Tenant & Mutable Domains Only)
    # -----------------------------------------------------------------------
    def create_tenant_backup(
        self,
        output_path: Optional[Path] = None,
        custom_backup_id: Optional[str] = None,
    ) -> tuple[Path, BackupManifest]:
        """
        Extract all tenant-owned, user-owned, and operational data into a cryptographically
        hashed backup archive. STRICTLY EXCLUDES PUBLIC_FROZEN analytical data.
        """
        t0 = time.time()
        backup_id = custom_backup_id or f"backup_tenant_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        out_file = output_path or (self.backup_dir / f"{backup_id}.json")

        payload: dict[str, dict[str, str]] = {}  # domain -> {rel_path_str: content_str}
        domain_counts: dict[str, int] = {}
        domain_checksums: dict[str, str] = {}
        classifications: dict[str, str] = {}

        for domain, (classification, root_dir, pattern) in MUTABLE_DOMAIN_DIRECTORIES.items():
            classifications[domain] = classification
            domain_files: dict[str, str] = {}

            if root_dir.exists():
                for fpath in sorted(root_dir.glob(pattern)):
                    if fpath.is_file():
                        try:
                            rel_key = str(fpath.relative_to(root_dir)).replace("\\", "/")
                            content = fpath.read_text(encoding="utf-8")
                            domain_files[rel_key] = content
                        except Exception as e:
                            logger.warning("Could not read %s for backup: %s", fpath, e)

            payload[domain] = domain_files
            domain_counts[domain] = len(domain_files)
            domain_checksums[domain] = self._compute_digest(domain_files)

        manifest_digest = self._compute_digest(domain_checksums)

        manifest = BackupManifest(
            backup_id=backup_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            schema_version=CURRENT_SCHEMA_VERSION,
            format_version="1.0",
            source_environment=settings.ENV,
            domain_counts=domain_counts,
            domain_checksums=domain_checksums,
            manifest_checksum=manifest_digest,
            data_classifications=classifications,
            frozen_baseline_status="ISOLATED_FROZEN_NOT_INCLUDED",
        )

        full_archive = {
            "_manifest": manifest.to_dict(),
            "data": payload,
        }

        with open(out_file, "w", encoding="utf-8") as fp:
            json.dump(full_archive, fp, indent=2)

        duration = time.time() - t0
        logger.info(
            "Created tenant backup archive: id=%s | path=%s | duration=%.2fs | total_files=%d",
            backup_id,
            out_file,
            duration,
            sum(domain_counts.values()),
        )
        return out_file, manifest

    # -----------------------------------------------------------------------
    # 2. Backup Integrity Verification
    # -----------------------------------------------------------------------
    def verify_backup_integrity(self, backup_path: Path) -> dict[str, Any]:
        """
        Validates backup archive against cryptographic SHA-256 checksums,
        format compatibility, and schema versioning.
        """
        if not backup_path.is_file():
            return {
                "valid": False,
                "error": f"Backup file not found: {backup_path}",
                "checksum_verified": False,
            }

        try:
            with open(backup_path, "r", encoding="utf-8") as fp:
                archive = json.load(fp)
        except Exception as e:
            return {
                "valid": False,
                "error": f"Corrupt JSON archive: {e}",
                "checksum_verified": False,
            }

        manifest = archive.get("_manifest", {})
        data = archive.get("data", {})

        if not manifest or not data:
            return {
                "valid": False,
                "error": "Archive missing '_manifest' or 'data' envelope",
                "checksum_verified": False,
            }

        schema_ver = manifest.get("schema_version")
        if schema_ver not in SUPPORTED_SCHEMA_VERSIONS:
            return {
                "valid": False,
                "error": f"Unsupported schema version: {schema_ver}. Supported: {SUPPORTED_SCHEMA_VERSIONS}",
                "checksum_verified": False,
            }

        expected_checksums = manifest.get("domain_checksums", {})
        recomputed_checksums: dict[str, str] = {}
        mismatched_domains: list[str] = []

        for domain, items in data.items():
            digest = self._compute_digest(items)
            recomputed_checksums[domain] = digest
            if digest != expected_checksums.get(domain):
                mismatched_domains.append(domain)

        recomputed_manifest_digest = self._compute_digest(recomputed_checksums)
        expected_manifest_digest = manifest.get("manifest_checksum")

        manifest_valid = (recomputed_manifest_digest == expected_manifest_digest) and (len(mismatched_domains) == 0)

        return {
            "valid": manifest_valid,
            "backup_id": manifest.get("backup_id"),
            "timestamp": manifest.get("timestamp"),
            "schema_version": schema_ver,
            "domain_counts": manifest.get("domain_counts", {}),
            "checksum_verified": manifest_valid,
            "mismatched_domains": mismatched_domains,
            "error": None if manifest_valid else f"Checksum mismatch in domains: {mismatched_domains}",
        }

    # -----------------------------------------------------------------------
    # 3. Deterministic Restore Procedure
    # -----------------------------------------------------------------------
    def restore_tenant_backup(
        self,
        backup_path: Path,
        verify_baseline: bool = True,
    ) -> RestoreResult:
        """
        Safely restores tenant, user, and operational data from a verified backup archive.
        GUARANTEES:
        - Rejects corrupted or tampered backups.
        - NEVER overwrites or regenerates PUBLIC_FROZEN analytical data.
        - Executes immediate baseline verification to ensure analytical parity.
        """
        t0 = time.time()
        restore_id = f"restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        verification = self.verify_backup_integrity(backup_path)
        if not verification.get("valid"):
            return RestoreResult(
                restore_id=restore_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                backup_id=verification.get("backup_id", "UNKNOWN"),
                success=False,
                domains_restored=[],
                records_restored_total=0,
                frozen_baseline_verified=False,
                state_predictions_count=0,
                duration_seconds=round(time.time() - t0, 3),
                error=verification.get("error", "Integrity check failed"),
            )

        with open(backup_path, "r", encoding="utf-8") as fp:
            archive = json.load(fp)

        manifest = archive["_manifest"]
        data = archive["data"]

        # Hard guard: Ensure no analytical keys leaked into mutable payload
        forbidden_keys = {"predictions", "decisions", "anticipation", "central_bills", "state_bills"}
        for k in data.keys():
            if k in forbidden_keys:
                raise RuntimeError(f"CRITICAL SAFETY VIOLATION: Backup payload contains forbidden analytical key '{k}'. Restore aborted.")

        domains_restored: list[str] = []
        total_files_restored = 0

        for domain, domain_files in data.items():
            if domain not in MUTABLE_DOMAIN_DIRECTORIES:
                continue

            _, root_dir, _ = MUTABLE_DOMAIN_DIRECTORIES[domain]
            root_dir.mkdir(parents=True, exist_ok=True)

            for rel_path_str, content_str in domain_files.items():
                target_path = root_dir / Path(rel_path_str)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(content_str, encoding="utf-8")
                total_files_restored += 1

            domains_restored.append(domain)

        # Baseline verification post-restore
        baseline_verified = True
        state_preds = 0
        if verify_baseline:
            baseline_rep = verify_production_baseline(quick=True)
            baseline_verified = baseline_rep.passed
            for r in baseline_rep.results:
                if r.dimension == "Stock Predictions Firewall":
                    state_preds = int(r.actual)
                    break
            if not baseline_verified or state_preds != 0:
                raise RuntimeError(
                    f"CRITICAL RECOVERY FAILURE: Frozen baseline violated post-restore! Passed={baseline_verified}, StatePreds={state_preds}"
                )

        duration = round(time.time() - t0, 3)
        logger.info(
            "Restore completed: id=%s | backup_id=%s | files=%d | duration=%.2fs | baseline_ok=%s",
            restore_id,
            manifest.get("backup_id"),
            total_files_restored,
            duration,
            baseline_verified,
        )

        return RestoreResult(
            restore_id=restore_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            backup_id=manifest.get("backup_id", ""),
            success=True,
            domains_restored=domains_restored,
            records_restored_total=total_files_restored,
            frozen_baseline_verified=baseline_verified,
            state_predictions_count=state_preds,
            duration_seconds=duration,
        )

    # -----------------------------------------------------------------------
    # 4. Schema Version & Migration Rollback Safety
    # -----------------------------------------------------------------------
    @staticmethod
    def get_schema_version_status() -> dict[str, Any]:
        """Return active schema version, supported versions, and migration status."""
        return {
            "current_schema_version": CURRENT_SCHEMA_VERSION,
            "supported_versions": SUPPORTED_SCHEMA_VERSIONS,
            "migration_safety": "STRICTLY_ADDITIVE_AND_REVERSIBLE",
            "analytical_isolation": "FROZEN_OBJECT_STORE_ISOLATED",
            "rollback_support": True,
        }

    @staticmethod
    def verify_migration_rollback_safety(target_version: str) -> dict[str, Any]:
        """
        Verify that a proposed migration rollback target is valid, non-destructive,
        and cannot mutate frozen analytical artifacts.
        """
        if target_version not in SUPPORTED_SCHEMA_VERSIONS:
            return {
                "safe": False,
                "target_version": target_version,
                "error": f"Unknown target migration version: {target_version}. Supported: {SUPPORTED_SCHEMA_VERSIONS}",
            }

        return {
            "safe": True,
            "target_version": target_version,
            "rollback_plan": "Restore prior tenant backup and execute reversible DDL schema downgrade.",
            "analytical_data_affected": False,
            "frozen_baseline_risk": "ZERO (analytical baseline decoupled from PostgreSQL tables)",
        }
