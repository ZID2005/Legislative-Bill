"""
ingestion/state/service.py
==========================
Orchestration service for Indian State legislative bill ingestion workflows.

Coordinates source registry, state adapters, normalization, deduplication,
provenance tracking, and isolated storage in StateBillRepository.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from ingestion.parliament.connector import ParliamentConnector
from ingestion.state.adapters.andhra_pradesh import AndhraPradeshSourceAdapter
from ingestion.state.adapters.karnataka import KarnatakaSourceAdapter
from ingestion.state.adapters.kerala import KeralaSourceAdapter
from ingestion.state.adapters.telangana import TelanganaSourceAdapter
from ingestion.state.base_adapter import BaseStateSourceAdapter
from ingestion.state.deduplicator import StateBillDeduplicator
from ingestion.state.normalizer import StateBillNormalizer
from ingestion.state.provenance import StateProvenanceTracker
from ingestion.state.registry import StateSourceRegistry
from schemas.bill import Bill
from schemas.state_source import StateBillSource
from storage.state_bill_repository import StateBillRepository
from utils.file_utils import ensure_dir, save_json
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)


class StateIngestionService:
    """
    Coordinates State legislative bill ingestion across official state sources.
    """

    def __init__(
        self,
        registry: Optional[StateSourceRegistry] = None,
        repository: Optional[StateBillRepository] = None,
        connector: Optional[ParliamentConnector] = None,
        normalizer: Optional[StateBillNormalizer] = None,
        deduplicator: Optional[StateBillDeduplicator] = None,
        provenance_tracker: Optional[StateProvenanceTracker] = None,
    ) -> None:
        self.registry = registry or StateSourceRegistry()
        self.repository = repository or StateBillRepository()
        self.connector = connector or ParliamentConnector()
        self.deduplicator = deduplicator or StateBillDeduplicator()
        self.normalizer = normalizer or StateBillNormalizer(deduplicator=self.deduplicator)
        self.provenance_tracker = provenance_tracker or StateProvenanceTracker()

    def get_adapter_for_source(self, source: StateBillSource) -> Optional[BaseStateSourceAdapter]:
        """Factory method to instantiate the appropriate adapter for a state source."""
        if source.source_name == "andhra_pradesh_assembly" or source.state == "Andhra Pradesh":
            return AndhraPradeshSourceAdapter(source=source, connector=self.connector)
        elif source.source_name == "karnataka_assembly" or source.state == "Karnataka":
            return KarnatakaSourceAdapter(source=source, connector=self.connector)
        elif source.source_name == "kerala_niyamasabha" or source.state == "Kerala":
            return KeralaSourceAdapter(source=source, connector=self.connector)
        elif "telangana" in source.source_name or source.state == "Telangana":
            return TelanganaSourceAdapter(source=source, connector=self.connector)
        else:
            logger.warning("No specialized adapter implemented for source: %s", source.source_name)
            return None

    async def ingest_from_source(
        self,
        source_name: str,
        year: Optional[int] = None,
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Ingest bills from a single registered State bill source.
        """
        source = self.registry.get(source_name)
        if not source:
            raise ValueError(f"State source '{source_name}' not found in registry.")

        adapter = self.get_adapter_for_source(source)
        if not adapter:
            raise NotImplementedError(f"No adapter available for state source '{source_name}'.")

        logger.info(
            "StateIngestionService: starting ingestion | source=%s | dry_run=%s",
            source_name,
            dry_run,
        )

        raw_bills = await adapter.discover_bills(year=year, limit=limit)
        return self.process_raw_bills(raw_bills, source=source, dry_run=dry_run)

    def process_raw_bills(
        self,
        raw_bills: list[dict[str, Any]],
        source: Optional[StateBillSource] = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Normalize, deduplicate, track provenance, and persist raw State bill records.
        """
        stats = {
            "discovered": len(raw_bills),
            "inserted": 0,
            "skipped_duplicate": 0,
            "bills": [],
        }

        default_state = source.state if source else None
        default_leg = source.legislature if source else None

        for raw in raw_bills:
            is_dup, dup_id = self.deduplicator.check_duplicate(raw)
            if is_dup:
                logger.debug("Skipping duplicate State bill: %s (matched: %s)", raw.get("title"), dup_id)
                stats["skipped_duplicate"] += 1
                continue

            bill, prov = self.normalizer.normalize(
                raw,
                default_state=default_state,
                default_legislature=default_leg,
            )

            # Register in deduplicator
            self.deduplicator.register_bill(bill.bill_id, raw)

            # Track provenance
            self.provenance_tracker.record_bill(prov)

            if not dry_run:
                self.repository.save(bill)

            stats["inserted"] += 1
            stats["bills"].append(bill.bill_id)

        logger.info(
            "Processed State bills | discovered=%d | inserted=%d | skipped_dup=%d",
            stats["discovered"],
            stats["inserted"],
            stats["skipped_duplicate"],
        )
        return stats

    def get_provenance_report(self) -> dict[str, Any]:
        """Return the compiled provenance audit report."""
        return self.provenance_tracker.generate_report()

    def save_provenance_report(self, dest_path: Optional[Path] = None) -> Path:
        """Persist provenance audit report to disk as JSON."""
        from config.settings import settings

        target_path = dest_path or (settings.STATE_BILLS_DIR / "provenance_report.json")
        ensure_dir(target_path.parent)
        save_json(self.get_provenance_report(), target_path)
        logger.info("Saved state provenance report to %s", target_path)
        return target_path
