"""
services/alert_matching_service.py
==================================
Alert Matching Engine and Event Generation Layer.

Connects incoming legislative and corporate exposure events to user watchlists
via deterministic inverted indices, evaluates subscriber alert rules, and generates
persisted in-app AlertEvents with strict deduplication and information separation.

Architecture Flow:
  Monitoring / Exposure Event
          ↓
  Event Normalization (ChangeEvent / StateCorporateExposure / Dict)
          ↓
  Affected Entity Resolution (Direct dimensions + Validated Exposure links)
          ↓
  WatchlistIndexService (O(1) Inverted Index Resolution)
          ↓
  Subscriber Resolution & Multi-Dimension Candidate Grouping
          ↓
  AlertRule Evaluation (User/Watchlist scope, AlertType, Severity Threshold)
          ↓
  AlertEvent Generation (Structured FACT / DERIVED / INTERPRETATION / PREDICTION)
          ↓
  Deduplication & Idempotent Persistence (AlertEventRepository + dedup_index)

Key Guarantees:
- Strictly additive: 0 modifications to Central models, predictions, or baselines.
- Zero state market predictions: State alerts contain PREDICTION = none.
- Complete idempotency: Re-processing identical events produces 0 duplicate records.
- Deterministic subscriber resolution via WatchlistIndexService.
- Multi-dimensional candidate deduplication: 1 AlertEvent per watchlist subscription.
- Strict multi-tenant and user isolation.
- NO external notification delivery (email, push, SMS, webhooks deferred).

Task 8.13.4 — Alert Matching Engine & Event Generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional
import uuid

from config.logging_config import get_logger
from schemas.alert import (
    AlertEvent,
    AlertPreference,
    AlertRule,
    AlertSeverity,
    AlertType,
    compute_dedup_key,
)
from schemas.monitoring import ChangeEvent, ChangeEventType, NotificationEvent
from schemas.state_corporate_exposure import StateCorporateExposure
from schemas.watchlist import WatchlistEntityType
from services.watchlist_index_service import (
    WatchlistIndexService,
    WatchlistSubscriber,
)
from storage.alert_event_repository import AlertEventRepository
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.alert_rule_repository import AlertRuleRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.state_bill_repository import StateBillRepository
from storage.watchlist_repository import WatchlistRepository
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_SEVERITY_ORDER: dict[AlertSeverity, int] = {
    AlertSeverity.INFO: 1,
    AlertSeverity.LOW: 2,
    AlertSeverity.MEDIUM: 3,
    AlertSeverity.HIGH: 4,
    AlertSeverity.CRITICAL: 5,
}


def severity_rank(sev: AlertSeverity | str) -> int:
    """Return integer rank (1-5) for severity threshold comparison."""
    if isinstance(sev, AlertSeverity):
        return _SEVERITY_ORDER.get(sev, 2)
    try:
        norm = AlertSeverity(str(sev).strip().upper())
        return _SEVERITY_ORDER.get(norm, 2)
    except ValueError:
        return 2


# ---------------------------------------------------------------------------
# Normalized Event Contract
# ---------------------------------------------------------------------------


@dataclass
class NormalizedEvent:
    """
    Standardized internal event representation for the matching engine.

    Gathers canonical entity identifiers, classification, provenance,
    evidence, and structured factual/derived/interpretation/prediction content.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_type: AlertType = AlertType.BILL_STATUS_CHANGE
    severity: AlertSeverity = AlertSeverity.MEDIUM
    bill_id: Optional[str] = None
    bill_title: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    sector_id: Optional[str] = None
    industry_id: Optional[str] = None
    state_id: Optional[str] = None
    jurisdiction: Optional[str] = None  # "central" | "state" | "all"
    timestamp: str = field(default_factory=_utcnow_iso)
    source: Optional[str] = None
    source_reference: Optional[str] = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    fact_summary: str = ""
    derived_summary: str = ""
    interpretation_summary: str = ""
    prediction_summary: str = "none"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "alert_type": self.alert_type.value
            if isinstance(self.alert_type, AlertType)
            else str(self.alert_type),
            "severity": self.severity.value
            if isinstance(self.severity, AlertSeverity)
            else str(self.severity),
            "bill_id": self.bill_id,
            "bill_title": self.bill_title,
            "company_id": self.company_id,
            "company_name": self.company_name,
            "sector_id": self.sector_id,
            "industry_id": self.industry_id,
            "state_id": self.state_id,
            "jurisdiction": self.jurisdiction,
            "timestamp": self.timestamp,
            "source": self.source,
            "source_reference": self.source_reference,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "fact_summary": self.fact_summary,
            "derived_summary": self.derived_summary,
            "interpretation_summary": self.interpretation_summary,
            "prediction_summary": self.prediction_summary,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NormalizedEvent":
        raw_type = data.get("alert_type", AlertType.BILL_STATUS_CHANGE.value)
        if isinstance(raw_type, AlertType):
            atype = raw_type
        else:
            try:
                atype = AlertType(str(raw_type).strip().upper())
            except ValueError:
                atype = AlertType.BILL_STATUS_CHANGE

        raw_sev = data.get("severity", AlertSeverity.MEDIUM.value)
        if isinstance(raw_sev, AlertSeverity):
            sev = raw_sev
        else:
            try:
                sev = AlertSeverity(str(raw_sev).strip().upper())
            except ValueError:
                sev = AlertSeverity.MEDIUM

        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            alert_type=atype,
            severity=sev,
            bill_id=data.get("bill_id"),
            bill_title=data.get("bill_title"),
            company_id=data.get("company_id"),
            company_name=data.get("company_name"),
            sector_id=data.get("sector_id"),
            industry_id=data.get("industry_id"),
            state_id=data.get("state_id"),
            jurisdiction=data.get("jurisdiction"),
            timestamp=data.get("timestamp", _utcnow_iso()),
            source=data.get("source"),
            source_reference=data.get("source_reference"),
            evidence=data.get("evidence", []),
            metadata=data.get("metadata", {}),
            fact_summary=data.get("fact_summary", ""),
            derived_summary=data.get("derived_summary", ""),
            interpretation_summary=data.get("interpretation_summary", ""),
            prediction_summary=data.get("prediction_summary", "none"),
        )


# ---------------------------------------------------------------------------
# Alert Matching Service
# ---------------------------------------------------------------------------


class AlertMatchingService:
    """
    Core matching engine that receives normalized legislative and corporate exposure events,
    resolves affected entity dimensions, locates active subscribers via inverted indices,
    evaluates alert rules, applies deduplication, and persists AlertEvents.
    """

    def __init__(
        self,
        watchlist_repo: Optional[WatchlistRepository] = None,
        index_service: Optional[WatchlistIndexService] = None,
        alert_rule_repo: Optional[AlertRuleRepository] = None,
        alert_event_repo: Optional[AlertEventRepository] = None,
        alert_pref_repo: Optional[AlertPreferenceRepository] = None,
        company_exposure_repo: Optional[CompanyExposureRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        bill_repo: Optional[BillRepository] = None,
        state_bill_repo: Optional[StateBillRepository] = None,
    ) -> None:
        self.watchlist_repo = watchlist_repo or WatchlistRepository()
        self.index_service = index_service or WatchlistIndexService(
            watchlist_repo=self.watchlist_repo
        )
        self.alert_rule_repo = alert_rule_repo or AlertRuleRepository()
        self.alert_event_repo = alert_event_repo or AlertEventRepository()
        self.alert_pref_repo = alert_pref_repo or AlertPreferenceRepository()
        self.company_exposure_repo = company_exposure_repo or CompanyExposureRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.bill_repo = bill_repo or BillRepository()
        self.state_bill_repo = state_bill_repo or StateBillRepository()

        logger.debug("AlertMatchingService initialized")

    # ------------------------------------------------------------------
    # Event Normalization Layer
    # ------------------------------------------------------------------

    def normalize_monitoring_event(
        self, event: ChangeEvent | NotificationEvent | dict[str, Any]
    ) -> NormalizedEvent:
        """
        Deterministically convert a ChangeEvent, NotificationEvent, or raw monitoring dict
        into a canonical NormalizedEvent.
        """
        if isinstance(event, ChangeEvent):
            data = event.to_dict()
        elif isinstance(event, NotificationEvent):
            data = event.to_dict()
        elif isinstance(event, dict):
            data = dict(event)
        else:
            raise TypeError(f"Unsupported monitoring event type: {type(event)}")

        event_id = str(data.get("event_id") or uuid.uuid4())
        raw_type = str(data.get("event_type", "NO_CHANGE")).strip().upper()
        bill_id = str(data.get("bill_id", "")).strip().lower() or None
        bill_title = str(data.get("bill_title", "")).strip() or None
        jurisdiction = str(data.get("jurisdiction", "central")).strip().lower() or "central"
        raw_state = data.get("state")
        state_id = normalize_state(str(raw_state)) if raw_state else None
        source_id = data.get("source_id") or data.get("source")
        timestamp = data.get("detected_at") or _utcnow_iso()
        source_ref = data.get("source_reference")
        metadata = dict(data.get("metadata", {}))

        # Map ChangeEventType to AlertType and assess deterministic baseline severity
        if raw_type == ChangeEventType.NEW_BILL.value:
            alert_type = AlertType.NEW_BILL
            severity = AlertSeverity.LOW
        elif raw_type == ChangeEventType.STATUS_CHANGED.value:
            alert_type = AlertType.BILL_STATUS_CHANGE
            new_val = str(data.get("new_value", "")).lower()
            if new_val in ("assented", "passed_both"):
                severity = AlertSeverity.HIGH
            elif new_val in ("passed_lok_sabha", "passed_rajya_sabha", "in_committee", "lapsed", "withdrawn", "negatived"):
                severity = AlertSeverity.MEDIUM
            else:
                severity = AlertSeverity.LOW
        elif raw_type == ChangeEventType.DOCUMENT_CHANGED.value:
            alert_type = AlertType.BILL_DOCUMENT_CHANGE
            severity = AlertSeverity.LOW
        elif raw_type in (ChangeEventType.METADATA_CHANGED.value, ChangeEventType.DATE_CHANGED.value):
            alert_type = AlertType.BILL_VERSION_CHANGE
            severity = AlertSeverity.LOW
        else:
            alert_type = AlertType.LEGISLATIVE_MONITORING_CHANGE
            severity = AlertSeverity.INFO

        # Enrich verified bill attributes if available in repos without inventing
        sector_id = None
        if bill_id:
            b = self.bill_repo.get(bill_id) or self.state_bill_repo.get(bill_id)
            if b:
                if not bill_title and b.title:
                    bill_title = b.title
                if not state_id and getattr(b, "state", None):
                    state_id = normalize_state(b.state)
                if getattr(b, "sectors", None) and len(b.sectors) > 0:
                    sector_id = b.sectors[0]

        # Check validated company exposures for this bill
        exposed_companies = []
        if bill_id:
            exps = self.company_exposure_repo.get_companies_for_bill(bill_id)
            for exp in exps:
                exposed_companies.append({
                    "company_id": exp.company_id,
                    "company_name": exp.company_name,
                    "sector": exp.sector,
                    "exposure_strength": exp.exposure_strength,
                    "direct_indirect": exp.direct_indirect,
                })
            if exposed_companies:
                metadata["validated_exposed_companies"] = exposed_companies

        # Formulate structured information separation
        if alert_type == AlertType.NEW_BILL:
            fact = f"New bill introduced: '{bill_title or bill_id}' in {jurisdiction.capitalize()} jurisdiction."
            derived = f"Classified under {sector_id} sector." if sector_id else f"Legislative jurisdiction: {jurisdiction.capitalize()}."
            interpretation = "Introduction marks the start of parliamentary/legislative consideration."
        elif alert_type == AlertType.BILL_STATUS_CHANGE:
            old_s = data.get("old_value", "unknown")
            new_s = data.get("new_value", "unknown")
            fact = f"Bill '{bill_title or bill_id}' status transitioned from '{old_s}' to '{new_s}'."
            derived = f"Legislative stage updated for jurisdiction: {jurisdiction.capitalize()}."
            interpretation = "Status updates alter legislative trajectory and operational compliance lead time."
        elif alert_type == AlertType.BILL_DOCUMENT_CHANGE:
            fact = f"Official PDF document updated for bill '{bill_title or bill_id}'."
            derived = "Document hash verification indicated modified content."
            interpretation = "Review amended statutory provisions for revised clauses."
        else:
            fact = f"Legislative change detected for '{bill_title or bill_id}': {raw_type}."
            derived = f"Monitored source {source_id or 'unknown'} reported updates."
            interpretation = "Administrative or scheduling change recorded."

        # Strict predictive boundary: Central only if valid production prediction explicitly exists, State is strictly "none"
        prediction = "none"

        return NormalizedEvent(
            event_id=event_id,
            alert_type=alert_type,
            severity=severity,
            bill_id=bill_id,
            bill_title=bill_title,
            company_id=None,
            company_name=None,
            sector_id=sector_id,
            industry_id=None,
            state_id=state_id,
            jurisdiction=jurisdiction,
            timestamp=timestamp,
            source=source_id,
            source_reference=source_ref,
            evidence=[],
            metadata=metadata,
            fact_summary=fact,
            derived_summary=derived,
            interpretation_summary=interpretation,
            prediction_summary=prediction,
        )

    def normalize_exposure_event(
        self,
        event: StateCorporateExposure | dict[str, Any],
        alert_type: AlertType = AlertType.NEW_COMPANY_EXPOSURE,
    ) -> NormalizedEvent:
        """
        Deterministically convert a validated corporate exposure record into a NormalizedEvent.
        """
        if isinstance(event, StateCorporateExposure):
            data = event.to_dict()
            if hasattr(event, "event_id"):
                data["event_id"] = getattr(event, "event_id")
        elif isinstance(event, dict):
            data = dict(event)
        else:
            raise TypeError(f"Unsupported exposure event type: {type(event)}")

        event_id = str(data.get("event_id") or uuid.uuid4())
        bill_id = str(data.get("bill_id", "")).strip().lower() or None
        company_id = str(data.get("company_id", "")).strip().upper() or None
        company_name = str(data.get("company_name", "")).strip() or None
        sector = str(data.get("sector", "")).strip() or None
        sub_sector = str(data.get("sub_sector", "")).strip() or None
        raw_state = data.get("state")
        state_id = normalize_state(str(raw_state)) if raw_state else None
        jurisdiction = str(data.get("jurisdiction", "central" if not state_id else "state")).strip().lower()
        strength = str(data.get("exposure_strength", "MEDIUM")).strip().upper()
        directness = str(data.get("direct_indirect", "DIRECT")).strip().upper()
        activity = str(data.get("business_activity", "")).strip()
        mechanism = str(data.get("mechanism", "compliance")).strip()

        # Deterministic severity assessment based on exposure relevance
        if strength == "HIGH" and directness == "DIRECT":
            severity = AlertSeverity.HIGH
        elif strength == "HIGH" or directness == "DIRECT":
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW

        # Format evidence
        raw_evidence = data.get("evidence", [])
        evidence_list: list[dict[str, Any]] = []
        for e in raw_evidence:
            if hasattr(e, "to_dict"):
                evidence_list.append(e.to_dict())
            elif isinstance(e, dict):
                evidence_list.append(e)

        claims = [e.get("claim", "") for e in evidence_list if e.get("claim")]
        claim_str = "; ".join(claims) if claims else "Grounded in statutory provisions and verified business activities."

        fact = f"Verified corporate exposure identified linking {company_name or company_id} to bill '{bill_id}'."
        derived = (
            f"Sector: {sector or 'Unclassified'}"
            + (f" ({sub_sector})" if sub_sector else "")
            + f" | Directness: {directness} | Strength: {strength}."
        )
        interpretation = (
            f"Operational exposure in {activity} via {mechanism} mechanism. Evidence: {claim_str}"
        )
        prediction = "none"  # Guarantees ZERO predictions for State exposures and intelligence companies

        return NormalizedEvent(
            event_id=event_id,
            alert_type=alert_type,
            severity=severity,
            bill_id=bill_id,
            bill_title=None,
            company_id=company_id,
            company_name=company_name,
            sector_id=sector,
            industry_id=sub_sector,
            state_id=state_id,
            jurisdiction=jurisdiction,
            timestamp=data.get("verified_at") or _utcnow_iso(),
            source=data.get("source", "corporate_exposure_intelligence"),
            source_reference=f"{bill_id}:{company_id}",
            evidence=evidence_list,
            metadata={
                "direct_indirect": directness,
                "exposure_strength": strength,
                "exposure_type": data.get("exposure_type", "regulatory"),
                "mechanism": mechanism,
                "business_activity": activity,
                "market_relevance": data.get("market_relevance", "UNKNOWN"),
                "provenance": data.get("provenance", {}),
            },
            fact_summary=fact,
            derived_summary=derived,
            interpretation_summary=interpretation,
            prediction_summary=prediction,
        )

    def normalize_legislative_event(self, data: dict[str, Any]) -> NormalizedEvent:
        """
        Normalize general legislative event dictionaries.
        """
        return self.normalize_event(data)

    def normalize_event(self, event: Any) -> NormalizedEvent:
        """
        Polymorphic normalization dispatcher.
        """
        if isinstance(event, NormalizedEvent):
            return event
        if isinstance(event, (ChangeEvent, NotificationEvent)):
            return self.normalize_monitoring_event(event)
        if isinstance(event, StateCorporateExposure):
            return self.normalize_exposure_event(event)
        if isinstance(event, dict):
            # Check if it resembles a corporate exposure record
            if "company_id" in event and ("business_activity" in event or "exposure_type" in event):
                return self.normalize_exposure_event(event)
            # Check if it resembles a monitoring change event
            if "event_type" in event and ("field_name" in event or "old_value" in event or "new_value" in event):
                return self.normalize_monitoring_event(event)
            # Otherwise parse generic normalized event fields safely
            return NormalizedEvent.from_dict(event)

        raise TypeError(f"Cannot normalize unrecognized event object of type {type(event)}")

    # ------------------------------------------------------------------
    # Affected Entity Resolution & Index Lookup
    # ------------------------------------------------------------------

    def resolve_affected_entity_keys(
        self, event: NormalizedEvent
    ) -> list[tuple[WatchlistEntityType, str]]:
        """
        Determine all canonical (entity_type, entity_id) pairs impacted by an event.

        Combines:
        1. Direct event attributes (company, bill, sector, industry, state, jurisdiction).
        2. Validated exposure links for bills (Bill -> Company Exposures -> Company IDs).
        3. Validated bill taxonomy (Bill -> State, Bill -> Sectors).
        """
        keys: list[tuple[WatchlistEntityType, str]] = []
        seen: set[tuple[WatchlistEntityType, str]] = set()

        def _add(etype: WatchlistEntityType, raw_val: Optional[str]) -> None:
            if not raw_val or not str(raw_val).strip():
                return
            clean_val = str(raw_val).strip()
            pair = (etype, clean_val)
            if pair not in seen:
                seen.add(pair)
                keys.append(pair)

        # 1. Direct Dimensions
        if event.company_id:
            _add(WatchlistEntityType.COMPANY, event.company_id.upper())
            for alias_id in self.company_exposure_repo.resolve_company_identifier(event.company_id):
                _add(WatchlistEntityType.COMPANY, alias_id.upper())
        if event.bill_id:
            _add(WatchlistEntityType.BILL, event.bill_id.lower())
        if event.sector_id:
            _add(WatchlistEntityType.SECTOR, event.sector_id)
        if event.industry_id:
            _add(WatchlistEntityType.INDUSTRY, event.industry_id)
        if event.state_id:
            _add(WatchlistEntityType.STATE, event.state_id)
        if event.jurisdiction:
            j_clean = event.jurisdiction.lower()
            _add(WatchlistEntityType.JURISDICTION, j_clean)

        # 2. Linked Dimensions for Bill Events
        if event.bill_id:
            norm_bill_id = event.bill_id.lower()

            # Bill taxonomy from repositories
            b = self.bill_repo.get(norm_bill_id) or self.state_bill_repo.get(norm_bill_id)
            if b:
                if getattr(b, "jurisdiction", None):
                    j_val = b.jurisdiction.value if hasattr(b.jurisdiction, "value") else str(b.jurisdiction)
                    _add(WatchlistEntityType.JURISDICTION, j_val.lower())
                if getattr(b, "state", None):
                    norm_s = normalize_state(b.state)
                    if norm_s:
                        _add(WatchlistEntityType.STATE, norm_s)
                for s in getattr(b, "sectors", []):
                    _add(WatchlistEntityType.SECTOR, s)

            # Validated corporate exposures (without fabricating unverified links)
            exposures = self.company_exposure_repo.get_by_bill(norm_bill_id)
            for exp in exposures:
                _add(WatchlistEntityType.COMPANY, exp.company_id.upper())
                for alias_id in self.company_exposure_repo.resolve_company_identifier(exp.company_id):
                    _add(WatchlistEntityType.COMPANY, alias_id.upper())
                if exp.sector:
                    _add(WatchlistEntityType.SECTOR, exp.sector)
                if exp.sub_sector:
                    _add(WatchlistEntityType.INDUSTRY, exp.sub_sector)
                if exp.state:
                    norm_es = normalize_state(exp.state)
                    if norm_es:
                        _add(WatchlistEntityType.STATE, norm_es)

        return keys

    # ------------------------------------------------------------------
    # Candidate Subscriber Resolution & Multi-Dimension Deduplication
    # ------------------------------------------------------------------

    def resolve_candidate_subscribers(
        self, event: NormalizedEvent
    ) -> dict[tuple[str, str, str], dict[str, Any]]:
        """
        Query inverted indices for all affected entity dimensions and aggregate candidates.

        Deduplication rule:
        Multiple dimensions matching the same (tenant_id, user_id, watchlist_id) are grouped
        into ONE candidate holding all matched dimensions.
        Separate watchlists belonging to the same user remain separate candidates.

        Returns a dictionary mapping:
          (tenant_id, user_id, watchlist_id) -> {
              "tenant_id": ...,
              "user_id": ...,
              "watchlist_id": ...,
              "matched_dimensions": list[dict],
              "primary_entity_type": ...,
              "primary_entity_id": ...,
          }
        """
        entity_keys = self.resolve_affected_entity_keys(event)
        candidates: dict[tuple[str, str, str], dict[str, Any]] = {}

        for etype, entity_val in entity_keys:
            subscribers: list[WatchlistSubscriber] = self.index_service.get_subscribers(
                etype, entity_val
            )
            for sub in subscribers:
                group_key = (sub.tenant_id, sub.user_id, sub.watchlist_id)

                if group_key not in candidates:
                    candidates[group_key] = {
                        "tenant_id": sub.tenant_id,
                        "user_id": sub.user_id,
                        "watchlist_id": sub.watchlist_id,
                        "matched_dimensions": [],
                        "primary_entity_type": sub.entity_type,
                        "primary_entity_id": sub.entity_id,
                    }

                # Record matched dimension avoiding duplicates
                dim_entry = {
                    "entity_type": sub.entity_type,
                    "entity_id": sub.entity_id,
                    "item_id": sub.item_id,
                    "display_name": sub.display_name,
                }
                existing_dims = candidates[group_key]["matched_dimensions"]
                if not any(
                    d["entity_type"] == dim_entry["entity_type"]
                    and d["entity_id"].lower() == dim_entry["entity_id"].lower()
                    for d in existing_dims
                ):
                    existing_dims.append(dim_entry)

        return candidates

    # ------------------------------------------------------------------
    # Alert Rule & Preference Evaluation
    # ------------------------------------------------------------------

    def evaluate_rules_for_candidate(
        self,
        tenant_id: str,
        user_id: str,
        watchlist_id: str,
        event: NormalizedEvent,
    ) -> Optional[AlertRule]:
        """
        Evaluate user preferences and alert rules for a specific watchlist subscription.

        Enforces:
        1. Parent watchlist must exist and be active.
        2. User master alert preferences (if enabled=False, suppresses alert).
        3. User preference minimum severity and allowed alert types.
        4. Matching enabled AlertRule (scoped to watchlist or user-wide).
        5. Rule minimum severity threshold <= event severity.

        Returns the matching AlertRule, or None if suppressed / non-matching.
        """
        # 1. Verify parent watchlist is active
        wl = self.watchlist_repo.get(watchlist_id, tenant_id=tenant_id, user_id=user_id)
        if not wl or not wl.is_active:
            logger.debug("Candidate %s watchlist is inactive or deleted", watchlist_id)
            return None

        # 2. Check user alert preference master controls
        pref = self.alert_pref_repo.get_by_user(user_id, tenant_id=tenant_id)
        if pref:
            if not pref.enabled:
                logger.debug("User %s has disabled global alert preferences", user_id)
                return None
            if severity_rank(event.severity) < severity_rank(pref.minimum_severity):
                logger.debug(
                    "Event severity %s below user %s preference threshold %s",
                    event.severity,
                    user_id,
                    pref.minimum_severity,
                )
                return None
            if event.alert_type not in pref.allowed_alert_types:
                logger.debug(
                    "Event alert type %s not permitted by user %s preferences",
                    event.alert_type,
                    user_id,
                )
                return None

        # 3. Retrieve applicable alert rules
        # Watchlist-specific rules have highest precedence
        watchlist_rules = self.alert_rule_repo.list_by_watchlist(
            watchlist_id, tenant_id=tenant_id, user_id=user_id
        )
        user_rules = [
            r
            for r in self.alert_rule_repo.list_by_user(user_id, tenant_id=tenant_id)
            if r.watchlist_id is None
        ]

        # Prioritize watchlist-specific rules, fallback to user-wide rules
        applicable_rules = [r for r in watchlist_rules if r.enabled]
        if not applicable_rules:
            applicable_rules = [r for r in user_rules if r.enabled]

        event_sev_rank = severity_rank(event.severity)

        # 4. Find matching rule
        for rule in applicable_rules:
            if rule.alert_type == event.alert_type:
                rule_sev_rank = severity_rank(rule.minimum_severity)
                if event_sev_rank >= rule_sev_rank:
                    return rule

        # No matching enabled rule found
        return None

    # ------------------------------------------------------------------
    # AlertEvent Generation & Formatting
    # ------------------------------------------------------------------

    def _build_alert_title(self, event: NormalizedEvent, primary_id: Optional[str]) -> str:
        """Construct a concise, human-readable alert headline."""
        type_str = event.alert_type.value.replace("_", " ").title()
        if event.company_name and event.bill_id:
            return f"[{type_str}] {event.company_name} — {event.bill_id}"
        if event.bill_title:
            return f"[{type_str}] {event.bill_title}"
        if event.company_name:
            return f"[{type_str}] {event.company_name}"
        if primary_id:
            return f"[{type_str}] {primary_id}"
        return f"[{type_str}] Legislative Update"

    def _build_alert_summary(self, event: NormalizedEvent) -> str:
        """
        Build structured summary adhering to strict Information Separation:
        FACT | DERIVED | INTERPRETATION | PREDICTION
        """
        parts = [
            f"FACT: {event.fact_summary or 'Legislative change detected.'}",
            f"DERIVED: {event.derived_summary or 'Impact assessed through verified indices.'}",
            f"INTERPRETATION: {event.interpretation_summary or 'Monitor regulatory developments.'}",
            f"PREDICTION: {event.prediction_summary or 'none'}",
        ]
        return "\n".join(parts)

    def generate_alert_event(
        self,
        candidate_meta: dict[str, Any],
        matching_rule: AlertRule,
        event: NormalizedEvent,
    ) -> AlertEvent:
        """
        Construct a fully formed AlertEvent dataclass instance.
        """
        tenant_id = candidate_meta["tenant_id"]
        user_id = candidate_meta["user_id"]
        watchlist_id = candidate_meta["watchlist_id"]
        matched_dims = candidate_meta["matched_dimensions"]
        primary_etype_raw = candidate_meta.get("primary_entity_type")
        primary_id = candidate_meta.get("primary_entity_id")

        primary_etype = None
        if primary_etype_raw:
            try:
                primary_etype = WatchlistEntityType(str(primary_etype_raw).strip().upper())
            except ValueError:
                primary_etype = None

        dedup_key = compute_dedup_key(
            user_id=user_id,
            watchlist_id=watchlist_id,
            source_event_id=event.event_id,
            alert_type=event.alert_type,
        )

        title = self._build_alert_title(event, primary_id)
        summary = self._build_alert_summary(event)

        metadata = {
            "matched_dimensions": matched_dims,
            "source_event": event.to_dict(),
            "source": event.source,
            "source_reference": event.source_reference,
            "evidence": event.evidence,
            "structured_content": {
                "fact": event.fact_summary,
                "derived": event.derived_summary,
                "interpretation": event.interpretation_summary,
                "prediction": event.prediction_summary,
            },
            "rule_id": matching_rule.alert_rule_id,
        }

        return AlertEvent(
            alert_event_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            watchlist_id=watchlist_id,
            alert_rule_id=matching_rule.alert_rule_id,
            source_event_id=event.event_id,
            alert_type=event.alert_type,
            severity=event.severity,
            title=title,
            summary=summary,
            entity_type=primary_etype,
            entity_id=primary_id,
            created_at=_utcnow_iso(),
            dedup_key=dedup_key,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Main Event Processing Engine
    # ------------------------------------------------------------------

    def process_event(self, event: Any) -> list[AlertEvent]:
        """
        Process a single incoming event through the complete matching and generation pipeline.

        Idempotent: Re-processing identical events produces existing AlertEvents
        without creating duplicate database files.
        """
        norm_event = self.normalize_event(event)

        # 1. Resolve candidate subscribers across all impacted entity dimensions
        candidates = self.resolve_candidate_subscribers(norm_event)
        if not candidates:
            logger.debug("No active subscribers found for event %s", norm_event.event_id)
            return []

        generated_events: list[AlertEvent] = []

        # 2. Evaluate rules and generate AlertEvents per candidate
        for group_key, candidate_meta in candidates.items():
            tenant_id, user_id, watchlist_id = group_key

            # Check deduplication first
            dedup_key = compute_dedup_key(
                user_id=user_id,
                watchlist_id=watchlist_id,
                source_event_id=norm_event.event_id,
                alert_type=norm_event.alert_type,
            )

            # If already processed, retrieve existing (idempotency guarantee)
            if self.alert_event_repo.is_duplicate(dedup_key):
                existing_ev = self.alert_event_repo.find_by_dedup_key(
                    dedup_key, tenant_id=tenant_id, user_id=user_id
                )
                if existing_ev:
                    logger.debug("Event %s already processed for %s (idempotent)", norm_event.event_id, group_key)
                    generated_events.append(existing_ev)
                    continue

            # Evaluate alert rules
            matching_rule = self.evaluate_rules_for_candidate(
                tenant_id=tenant_id,
                user_id=user_id,
                watchlist_id=watchlist_id,
                event=norm_event,
            )
            if not matching_rule:
                continue

            # Generate and persist AlertEvent
            alert_event = self.generate_alert_event(
                candidate_meta=candidate_meta,
                matching_rule=matching_rule,
                event=norm_event,
            )

            try:
                saved = self.alert_event_repo.create(alert_event)
                generated_events.append(saved)
                logger.info(
                    "Generated AlertEvent %s for user %s (watchlist: %s, rule: %s)",
                    saved.alert_event_id,
                    saved.user_id,
                    saved.watchlist_id,
                    saved.alert_rule_id,
                )
            except ValueError as e:
                # In case of concurrent race or duplicate index race
                existing = self.alert_event_repo.find_by_dedup_key(
                    dedup_key, tenant_id=tenant_id, user_id=user_id
                )
                if existing:
                    generated_events.append(existing)
                else:
                    logger.warning("Could not persist alert event: %s", e)

        return generated_events

    def process_monitoring_event(
        self, event: ChangeEvent | NotificationEvent | dict[str, Any]
    ) -> list[AlertEvent]:
        """Convenience wrapper for processing legislative monitoring events."""
        norm = self.normalize_monitoring_event(event)
        return self.process_event(norm)

    def process_company_exposure_event(
        self, event: StateCorporateExposure | dict[str, Any]
    ) -> list[AlertEvent]:
        """Convenience wrapper for processing corporate exposure events."""
        norm = self.normalize_exposure_event(event)
        return self.process_event(norm)

    def process_batch(self, events: list[Any]) -> list[AlertEvent]:
        """Process a sequence of events, aggregating all generated AlertEvents."""
        all_generated: list[AlertEvent] = []
        for ev in events:
            all_generated.extend(self.process_event(ev))
        return all_generated
