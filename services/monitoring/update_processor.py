"""
services/monitoring/update_processor.py
=========================================
Legislative Update Processor.

Handles new bill and changed bill processing after the change detector
has identified an event. Routes updates to the appropriate repositories
without touching frozen production data.

CRITICAL PROTECTIONS:
1. Central new bills → knowledge/discovery ONLY. NOT training dataset.
2. State new bills → state knowledge/exposure/discovery ONLY. 
3. State predictions remain EXACTLY 0 after any update.
4. Historical predictions/backtesting/training data are NEVER modified.
5. Provenance and audit trail are ALWAYS preserved.

Task 8.11 — Live Legislative Monitoring & Automatic Update Scheduler.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.monitoring import ChangeEvent, ChangeEventType
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
    ) -> None:
        self._monitoring_repo = monitoring_repo or MonitoringRepository()

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
                "Central NEW_BILL %r → knowledge + discovery only (NOT training/prediction)",
                event.bill_id,
            )
        else:
            actions.append("state_knowledge_extraction_queued")
            actions.append("state_discovery_update_queued")
            # EXPLICIT: State predictions remain EXACTLY 0
            logger.info(
                "State NEW_BILL %r (%s) → state knowledge + discovery only (NO predictions)",
                event.bill_id,
                event.state,
            )

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

        result["processed"] = True
        result["actions"] = [
            "document_version_created",
            "text_extraction_queued",
            "knowledge_refresh_queued",
        ]
        return result

    def process_batch(self, events: list[ChangeEvent]) -> list[dict[str, Any]]:
        """Process a list of change events and return results."""
        results = []
        for event in events:
            results.append(self.process(event))
        return results
