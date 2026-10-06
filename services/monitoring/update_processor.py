"""
services/monitoring/update_processor.py
=========================================
Legislative Update Processor.

Handles new bill and changed bill processing after the change detector
has identified an event. Routes updates to the appropriate repositories
without touching frozen production data.

CRITICAL PROTECTIONS:
1. Central new bills -> knowledge/discovery ONLY. NOT training dataset.
2. State new bills -> state knowledge/exposure/discovery ONLY.
3. State predictions remain EXACTLY 0 after any update.
4. Historical predictions/backtesting/training data are NEVER modified.
5. Provenance and audit trail are ALWAYS preserved.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
Task 8.26 — Live Legislative Intelligence & Automatic Update Pipeline.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.monitoring import (
    AnalyticalModelStatus,
    ChangeEvent,
    ChangeEventType,
    LiveKnowledgeRecord,
    LiveStatus,
    SourceCategory,
)
from storage.live_knowledge_repository import LiveKnowledgeRepository
from storage.monitoring_repository import MonitoringRepository

logger = get_logger(__name__)


class UpdateProcessor:
    """
    Processes legislative change events and applies safe, targeted updates.

    Routes changes based on event type and jurisdiction:
    - NEW_BILL (Central) → knowledge record + discovery update (no predictions)
    - NEW_BILL (State) → state knowledge record + discovery update (no predictions)
    - STATUS_CHANGED → update status field only, create version record
    - DATE_CHANGED → update date field only, create version record
    - METADATA_CHANGED → update specific metadata field, create version record
    - DOCUMENT_CHANGED → re-extract text if PDF, refresh knowledge
    - SOURCE_CHANGED → update source URL, create version record

    All changes are logged to the MonitoringRepository with full audit trail.
    """

    def __init__(
        self,
        monitoring_repo: Optional[MonitoringRepository] = None,
        live_knowledge_repo: Optional[LiveKnowledgeRepository] = None,
    ) -> None:
        self._monitoring_repo = monitoring_repo or MonitoringRepository()
        self._live_knowledge_repo = live_knowledge_repo or LiveKnowledgeRepository(
            storage_dir=Path(settings.storage_path) if hasattr(settings, "storage_path") else Path("storage")
        )

    def process(self, event: ChangeEvent) -> dict[str, Any]:
        """
        Process a single change event.

        Returns a result dict describing what was updated.
        """
        result: dict[str, Any] = {
            "event_id": event.event_id,
            "event_type": event.event_type.value
            if isinstance(event.event_type, ChangeEventType)
            else str(event.event_type),
            "bill_id": event.bill_id,
            "jurisdiction": event.jurisdiction,
            "state": event.state,
            "processed": False,
            "actions": [],
            "errors": [],
        }

        try:
            if event.event_type == ChangeEventType.NEW_BILL:
                result = self._process_new_bill(event, result)
            elif event.event_type == ChangeEventType.STATUS_CHANGED:
                result = self._process_field_change(event, result)
            elif event.event_type == ChangeEventType.DATE_CHANGED:
                result = self._process_field_change(event, result)
            elif event.event_type == ChangeEventType.METADATA_CHANGED:
                result = self._process_field_change(event, result)
            elif event.event_type == ChangeEventType.DOCUMENT_CHANGED:
                result = self._process_document_change(event, result)
            elif event.event_type == ChangeEventType.SOURCE_CHANGED:
                result = self._process_field_change(event, result)
            elif event.event_type == ChangeEventType.ERROR:
                result["errors"].append(event.error_message or "Unknown error")
                logger.error(
                    "Error event for source %s: %s",
                    event.source_id,
                    event.error_message,
                )
            else:
                logger.debug(
                    "No-change event for bill %r — nothing to process",
                    event.bill_id,
                )

            # Persist the event to monitoring repository
            self._monitoring_repo.save_event(event)

        except Exception as e:
            logger.error(
                "UpdateProcessor failed for event %s (%s): %s",
                event.event_id,
                event.event_type,
                e,
            )
            result["errors"].append(str(e))

        return result

    def _process_new_bill(
        self, event: ChangeEvent, result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle NEW_BILL events.

        For Central bills: store metadata, generate knowledge record, update discovery.
        For State bills: store state knowledge record, update discovery.

        NEVER creates predictions for either jurisdiction.
        """
        logger.info(
            "Processing NEW_BILL: %r [%s]",
            event.bill_id,
            event.jurisdiction,
        )

        # Save a bill version snapshot
        self._monitoring_repo.save_bill_version(
            bill_id=event.bill_id,
            version_data={
                "version": "initial",
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "source_id": event.source_id,
                "title": event.bill_title,
                "jurisdiction": event.jurisdiction,
                "state": event.state,
                "new_value": event.new_value,
            },
        )

        actions = ["bill_version_created", "knowledge_record_queued"]

        # Jurisdiction-specific routing
        if event.jurisdiction == "central":
            actions.append("central_knowledge_extraction_queued")
            actions.append("discovery_update_queued")
            # EXPLICIT: NOT added to training dataset or prediction pipeline
            logger.info(
                "Central NEW_BILL %r -> knowledge + discovery only (NOT training/prediction)",
                event.bill_id,
            )
        else:
            actions.append("state_knowledge_extraction_queued")
            actions.append("state_discovery_update_queued")
            # EXPLICIT: State predictions remain EXACTLY 0
            logger.info(
                "State NEW_BILL %r (%s) -> state knowledge + discovery only (NO predictions)",
                event.bill_id,
                event.state,
            )

        # [Task 8.26] Create LiveKnowledgeRecord — starts KNOWLEDGE_ONLY, never MODELLED
        live_record = self._create_live_knowledge_record(event)
        if live_record:
            actions.append("live_knowledge_record_created")

        result["processed"] = True
        result["actions"] = actions
        return result

    def _process_field_change(
        self, event: ChangeEvent, result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle field-level changes (status, date, metadata, source).

        Updates only the changed field, preserves historical information,
        and creates a version record.
        """
        logger.info(
            "Processing %s for bill %r: field=%r %r → %r",
            event.event_type,
            event.bill_id,
            event.field_name,
            event.old_value,
            event.new_value,
        )

        # Save version record with old and new value
        self._monitoring_repo.save_bill_version(
            bill_id=event.bill_id,
            version_data={
                "version": f"change_{event.event_id}",
                "captured_at": event.detected_at,
                "source_id": event.source_id,
                "event_type": event.event_type.value
                if isinstance(event.event_type, ChangeEventType)
                else str(event.event_type),
                "field_name": event.field_name,
                "old_value": event.old_value,
                "new_value": event.new_value,
                "jurisdiction": event.jurisdiction,
                "state": event.state,
            },
        )

        actions = [
            f"field_updated:{event.field_name}",
            "version_record_created",
        ]

        # Determine downstream impact
        if event.event_type == ChangeEventType.STATUS_CHANGED:
            actions.append("lifecycle_status_refreshed")
        elif event.event_type == ChangeEventType.DATE_CHANGED:
            actions.append("date_field_refreshed")

        result["processed"] = True
        result["actions"] = actions
        return result

    def _process_document_change(
        self, event: ChangeEvent, result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle DOCUMENT_CHANGED events (PDF content change).

        A PDF URL change without SHA-256 difference is NOT processed here
        (the detector already handles that distinction).
        """
        logger.info(
            "Processing DOCUMENT_CHANGED for bill %r: %r → %r",
            event.bill_id,
            event.old_value,
            event.new_value,
        )

        self._monitoring_repo.save_bill_version(
            bill_id=event.bill_id,
            version_data={
                "version": f"doc_change_{event.event_id}",
                "captured_at": event.detected_at,
                "source_id": event.source_id,
                "event_type": "DOCUMENT_CHANGED",
                "field_name": event.field_name,
                "old_sha256": event.old_value,
                "new_sha256": event.new_value,
                "jurisdiction": event.jurisdiction,
                "state": event.state,
            },
        )

        # [Task 8.26 Phase 9] Update document hash in live knowledge repository
        self._update_live_knowledge_document_hash(event)

        result["processed"] = True
        result["actions"] = [
            "document_version_created",
            "text_extraction_queued",
            "knowledge_refresh_queued",
        ]
        return result

    def _process_field_change(
        self, event: ChangeEvent, result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle field-level changes (status, date, metadata, source).

        Updates only the changed field, preserves historical information,
        and creates a version record.
        """
        logger.info(
            "Processing %s for bill %r: field=%r %r -> %r",
            event.event_type,
            event.bill_id,
            event.field_name,
            event.old_value,
            event.new_value,
        )

        # Save version record with old and new value
        self._monitoring_repo.save_bill_version(
            bill_id=event.bill_id,
            version_data={
                "version": f"change_{event.event_id}",
                "captured_at": event.detected_at,
                "source_id": event.source_id,
                "event_type": event.event_type.value
                if isinstance(event.event_type, ChangeEventType)
                else str(event.event_type),
                "field_name": event.field_name,
                "old_value": event.old_value,
                "new_value": event.new_value,
                "jurisdiction": event.jurisdiction,
                "state": event.state,
            },
        )

        # [Task 8.26] Propagate field updates to LiveKnowledgeRecord
        self._update_live_knowledge_field(event)

        actions = [
            f"field_updated:{event.field_name}",
            "version_record_created",
        ]

        # Determine downstream impact
        if event.event_type == ChangeEventType.STATUS_CHANGED:
            actions.append("lifecycle_status_refreshed")
        elif event.event_type == ChangeEventType.DATE_CHANGED:
            actions.append("date_field_refreshed")

        result["processed"] = True
        result["actions"] = actions
        return result

    def process_batch(self, events: list[ChangeEvent]) -> list[dict[str, Any]]:
        """Process a list of change events and return results."""
        results = []
        for event in events:
            results.append(self.process(event))
        return results

    # ------------------------------------------------------------------
    # Task 8.26 — LiveKnowledgeRecord creation & updates
    # ------------------------------------------------------------------

    def _create_live_knowledge_record(
        self, event: ChangeEvent
    ) -> Optional[LiveKnowledgeRecord]:
        """
        [Task 8.26] Create or deduplicate a LiveKnowledgeRecord for a NEW_BILL event.

        FIREWALL ENFORCED:
        - analytical_model_status is always KNOWLEDGE_ONLY on creation.
        - assert_not_frozen_model() is called before persisting.
        - No automated pathway sets MODELLED.

        DEDUPLICATION ENFORCED:
        - If canonical_bill_id or bill_number already exists, updates existing
          record without creating a duplicate identity.
        - Increments duplicate_discoveries count.
        """
        try:
            new_val: dict[str, Any] = {}
            if isinstance(event.new_value, dict):
                new_val = event.new_value

            canonical_id = event.bill_id or None
            bill_num = new_val.get("bill_number") or new_val.get("number")

            # Check for existing record to ensure idempotency & deduplication
            existing = None
            if canonical_id:
                existing = self._live_knowledge_repo.get_by_canonical_bill_id(canonical_id)
            if not existing and bill_num:
                existing = self._live_knowledge_repo.get_by_bill_number(bill_num)

            if existing:
                existing.last_updated_at = datetime.now(timezone.utc).isoformat()
                if event.bill_title:
                    existing.title = event.bill_title
                if new_val.get("title"):
                    existing.title = new_val.get("title")
                if new_val.get("short_title"):
                    existing.short_title = new_val.get("short_title")
                if new_val.get("source_url") or new_val.get("url"):
                    existing.source_url = new_val.get("source_url") or new_val.get("url")
                if new_val.get("pdf_url") or new_val.get("document_url"):
                    existing.document_url = new_val.get("pdf_url") or new_val.get("document_url")
                if new_val.get("status"):
                    existing.bill_status_text = new_val.get("status")
                if new_val.get("summary"):
                    existing.summary = new_val.get("summary")
                if new_val.get("tags"):
                    existing.tags = new_val.get("tags")
                existing.assert_not_frozen_model()
                persisted = self._live_knowledge_repo.upsert(existing)
                logger.info(
                    "[8.26] LiveKnowledgeRecord deduplicated & updated: %s (discoveries=%d)",
                    persisted.record_id,
                    persisted.duplicate_discoveries,
                )
                return persisted

            # Determine source category from jurisdiction
            if event.jurisdiction == "central":
                cat = SourceCategory.PARLIAMENTARY.value
            else:
                cat = SourceCategory.STATE.value

            record = LiveKnowledgeRecord(
                canonical_bill_id=canonical_id,
                bill_number=bill_num,
                title=event.bill_title or new_val.get("title", ""),
                short_title=new_val.get("short_title"),
                jurisdiction=event.jurisdiction,
                state=event.state,
                live_status=LiveStatus.DISCOVERED.value,
                # FIREWALL: always starts KNOWLEDGE_ONLY
                analytical_model_status=AnalyticalModelStatus.KNOWLEDGE_ONLY.value,
                discovered_by_source_id=event.source_id,
                discovered_by_run_id=None,
                source_url=new_val.get("source_url") or new_val.get("url"),
                source_category=cat,
                authority_name=None,
                document_url=new_val.get("pdf_url") or new_val.get("document_url"),
                introduction_date=new_val.get("introduction_date"),
                assent_date=new_val.get("assent_date"),
                bill_status_text=new_val.get("status"),
                summary=new_val.get("summary"),
                tags=new_val.get("tags", []),
            )

            # Firewall assertion — will raise if somehow MODELLED was set
            record.assert_not_frozen_model()

            persisted = self._live_knowledge_repo.upsert(record)
            logger.info(
                "[8.26] LiveKnowledgeRecord created: %s [%s/%s] status=%s model=%s",
                persisted.record_id,
                persisted.jurisdiction,
                persisted.state or "central",
                persisted.live_status,
                persisted.analytical_model_status,
            )
            return persisted

        except Exception as exc:
            logger.error("[8.26] Failed to create LiveKnowledgeRecord: %s", exc)
            return None

    def _update_live_knowledge_document_hash(
        self,
        event: ChangeEvent,
    ) -> None:
        """
        [Task 8.26 Phase 9] Update document hash for a DOCUMENT_CHANGED event.
        """
        try:
            existing = self._live_knowledge_repo.get_by_canonical_bill_id(event.bill_id)
            if existing:
                existing.document_hash_sha256 = (
                    event.new_value if isinstance(event.new_value, str) else None
                )
                existing.document_retrieved_at = datetime.now(timezone.utc).isoformat()
                existing.live_status = LiveStatus.UPDATED.value
                existing.assert_not_frozen_model()
                self._live_knowledge_repo.upsert(existing)
                logger.info(
                    "[8.26] Document hash updated for live record %s",
                    existing.record_id,
                )
        except Exception as exc:
            logger.error("[8.26] Failed to update document hash: %s", exc)

    def _update_live_knowledge_field(
        self,
        event: ChangeEvent,
    ) -> None:
        """
        [Task 8.26] Update live knowledge fields on field change events.
        """
        try:
            existing = self._live_knowledge_repo.get_by_canonical_bill_id(event.bill_id)
            if not existing:
                return

            field = (event.field_name or "").lower()
            val = event.new_value

            if field in ("title", "bill_title") or (
                event.event_type == ChangeEventType.METADATA_CHANGED and field == "title"
            ):
                existing.title = str(val) if val is not None else existing.title
            elif field in ("status", "bill_status_text") or event.event_type == ChangeEventType.STATUS_CHANGED:
                existing.bill_status_text = str(val) if val is not None else existing.bill_status_text
            elif field in ("document_url", "pdf_url"):
                existing.document_url = str(val) if val is not None else existing.document_url
            elif field in ("source_url", "url") or event.event_type == ChangeEventType.SOURCE_CHANGED:
                existing.source_url = str(val) if val is not None else existing.source_url
            elif field == "summary":
                existing.summary = str(val) if val is not None else existing.summary
            elif field == "introduction_date":
                existing.introduction_date = str(val) if val is not None else existing.introduction_date
            elif field == "assent_date":
                existing.assent_date = str(val) if val is not None else existing.assent_date

            existing.live_status = LiveStatus.UPDATED.value
            existing.last_updated_at = datetime.now(timezone.utc).isoformat()
            existing.assert_not_frozen_model()
            self._live_knowledge_repo.upsert(existing)
            logger.info(
                "[8.26] Live knowledge field updated for %s (field=%s)",
                existing.record_id,
                field,
            )
        except Exception as exc:
            logger.error("[8.26] Failed to update live knowledge field: %s", exc)
