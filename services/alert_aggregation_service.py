"""
services/alert_aggregation_service.py
=====================================
Alert Aggregation Engine for grouping related AlertEvents into structured AlertGroups.

Consumes immutable AlertEvents, partitions events across deterministic entity dimensions
(BILL, COMPANY, SECTOR, INDUSTRY, STATE, JURISDICTION, WATCHLIST, EVENT) within a
configurable time window, and produces persistent AlertGroup records while maintaining
zero state predictions, frozen baseline integrity, and multi-tenant isolation.

Task 8.13.5 — Alert Aggregation & Digest Pipeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.alert import AlertEvent, AlertSeverity
from schemas.alert_group import (
    AlertGroup,
    AlertGroupStatus,
    AlertGroupType,
    compute_aggregation_key,
    severity_rank,
)
from schemas.watchlist import WatchlistEntityType
from storage.alert_event_repository import AlertEventRepository
from storage.alert_group_repository import AlertGroupRepository

logger = get_logger(__name__)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(dt_str: str) -> datetime:
    """Parse ISO UTC timestamp safely."""
    try:
        clean = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception:
        return datetime.now(timezone.utc)


class AlertAggregationService:
    """
    Engine for grouping AlertEvents into persistent, deterministic AlertGroups.
    """

    def __init__(
        self,
        alert_event_repo: Optional[AlertEventRepository] = None,
        alert_group_repo: Optional[AlertGroupRepository] = None,
        window_hours: Optional[int] = None,
    ) -> None:
        self.event_repo = alert_event_repo or AlertEventRepository()
        self.group_repo = alert_group_repo or AlertGroupRepository()
        self.window_hours = (
            window_hours
            if window_hours is not None
            else settings.ALERT_AGGREGATION_WINDOW_HOURS
        )
        self.window_seconds = self.window_hours * 3600

    def resolve_group_dimension(
        self,
        event: AlertEvent,
        group_by: Optional[AlertGroupType] = None,
    ) -> tuple[AlertGroupType, Optional[WatchlistEntityType], str]:
        """
        Determine the grouping type, entity type, and canonical entity ID for an event.

        Returns: (group_type, entity_type, canonical_entity_id)
        """
        source_event = event.metadata.get("source_event", {})

        if group_by is not None:
            gt = group_by
            if gt == AlertGroupType.BILL:
                bid = source_event.get("bill_id") or (
                    event.entity_id if event.entity_type == WatchlistEntityType.BILL else None
                )
                return AlertGroupType.BILL, WatchlistEntityType.BILL, (bid or "unknown_bill")

            elif gt == AlertGroupType.COMPANY:
                cid = source_event.get("company_id") or (
                    event.entity_id if event.entity_type == WatchlistEntityType.COMPANY else None
                )
                return AlertGroupType.COMPANY, WatchlistEntityType.COMPANY, (cid or "unknown_company")

            elif gt == AlertGroupType.SECTOR:
                sid = source_event.get("sector_id") or (
                    event.entity_id if event.entity_type == WatchlistEntityType.SECTOR else None
                )
                return AlertGroupType.SECTOR, WatchlistEntityType.SECTOR, (sid or "unknown_sector")

            elif gt == AlertGroupType.INDUSTRY:
                iid = source_event.get("industry_id") or (
                    event.entity_id if event.entity_type == WatchlistEntityType.INDUSTRY else None
                )
                return AlertGroupType.INDUSTRY, WatchlistEntityType.INDUSTRY, (iid or "unknown_industry")

            elif gt == AlertGroupType.STATE:
                stid = source_event.get("state_id") or (
                    event.entity_id if event.entity_type == WatchlistEntityType.STATE else None
                )
                return AlertGroupType.STATE, WatchlistEntityType.STATE, (stid or "unknown_state")

            elif gt == AlertGroupType.JURISDICTION:
                jid = source_event.get("jurisdiction") or (
                    event.entity_id if event.entity_type == WatchlistEntityType.JURISDICTION else None
                )
                return AlertGroupType.JURISDICTION, WatchlistEntityType.JURISDICTION, (jid or "unknown_jurisdiction")

            elif gt == AlertGroupType.WATCHLIST:
                wid = event.watchlist_id or "global"
                return AlertGroupType.WATCHLIST, None, wid

            elif gt == AlertGroupType.EVENT:
                eid = event.source_event_id or event.alert_event_id
                return AlertGroupType.EVENT, None, eid

        # Automatic dimension resolution based on primary entity_type
        if event.entity_type == WatchlistEntityType.BILL:
            return AlertGroupType.BILL, WatchlistEntityType.BILL, (event.entity_id or "unknown_bill")
        elif event.entity_type == WatchlistEntityType.COMPANY:
            return AlertGroupType.COMPANY, WatchlistEntityType.COMPANY, (event.entity_id or "unknown_company")
        elif event.entity_type == WatchlistEntityType.SECTOR:
            return AlertGroupType.SECTOR, WatchlistEntityType.SECTOR, (event.entity_id or "unknown_sector")
        elif event.entity_type == WatchlistEntityType.INDUSTRY:
            return AlertGroupType.INDUSTRY, WatchlistEntityType.INDUSTRY, (event.entity_id or "unknown_industry")
        elif event.entity_type == WatchlistEntityType.STATE:
            return AlertGroupType.STATE, WatchlistEntityType.STATE, (event.entity_id or "unknown_state")
        elif event.entity_type == WatchlistEntityType.JURISDICTION:
            return AlertGroupType.JURISDICTION, WatchlistEntityType.JURISDICTION, (event.entity_id or "unknown_jurisdiction")

        # Fallback to source event references or EVENT
        if source_event.get("bill_id"):
            return AlertGroupType.BILL, WatchlistEntityType.BILL, source_event["bill_id"]
        if source_event.get("company_id"):
            return AlertGroupType.COMPANY, WatchlistEntityType.COMPANY, source_event["company_id"]

        return AlertGroupType.EVENT, None, (event.source_event_id or event.alert_event_id)

    def _build_group_title(
        self,
        group_type: AlertGroupType,
        entity_id: str,
        events: list[AlertEvent],
    ) -> str:
        """Construct a clean, professional headline for an alert group."""
        if not events:
            return f"[{group_type.value}] {entity_id}"

        count = len(events)
        if count == 1:
            return f"[{group_type.value}] {events[0].title}"

        # Multiple events
        return f"[{group_type.value}] {entity_id.upper()} ({count} updates)"

    def _build_group_summary(self, events: list[AlertEvent]) -> str:
        """
        Synthesize combined structured summary preserving:
        FACT | DERIVED | INTERPRETATION | PREDICTION
        Zero predictions for State alerts, immutable prediction references for Central.
        """
        facts: list[str] = []
        derived: list[str] = []
        interpretations: list[str] = []
        predictions: list[str] = []

        is_state = False
        for ev in events:
            sc = ev.metadata.get("structured_content", {})
            if sc.get("fact") and sc["fact"] not in facts:
                facts.append(sc["fact"])
            if sc.get("derived") and sc["derived"] not in derived:
                derived.append(sc["derived"])
            if sc.get("interpretation") and sc["interpretation"] not in interpretations:
                interpretations.append(sc["interpretation"])

            # Check if state
            src = ev.metadata.get("source_event", {})
            if src.get("jurisdiction") == "state" or ev.entity_type == WatchlistEntityType.STATE or src.get("state_id"):
                is_state = True

            p = sc.get("prediction")
            if p and p != "none" and p not in predictions:
                predictions.append(p)

        # Invariant: State predictions MUST remain exactly 0 / none
        pred_text = "none"
        if not is_state and predictions:
            pred_text = "; ".join(predictions)

        fact_text = "; ".join(facts) if facts else "Aggregated legislative/exposure updates."
        derived_text = "; ".join(derived) if derived else "Impact consolidated across event window."
        interp_text = "; ".join(interpretations) if interpretations else "Monitor developments."

        return (
            f"FACT: {fact_text}\n"
            f"DERIVED: {derived_text}\n"
            f"INTERPRETATION: {interp_text}\n"
            f"PREDICTION: {pred_text}"
        )

    def aggregate_events(
        self,
        events: list[AlertEvent],
        group_by: Optional[AlertGroupType] = None,
        save: bool = True,
    ) -> list[AlertGroup]:
        """
        Group a collection of AlertEvents into deterministic AlertGroups.

        Guarantees:
        - Underlying AlertEvents are never mutated.
        - Events within the aggregation window merge into a single group.
        - Events outside the window establish separate groups.
        - Repeated calls are completely idempotent.
        - Watchlist, tenant, and user isolation are strictly preserved.
        """
        if not events:
            return []

        # 1. Deterministic sort by (created_at, alert_event_id)
        sorted_events = sorted(events, key=lambda e: (e.created_at, e.alert_event_id))

        # 2. Partition events by logical identity:
        # partition_key = (tenant_id, user_id, watchlist_id, group_type, entity_type, entity_id)
        partitions: dict[tuple, list[AlertEvent]] = {}
        for ev in sorted_events:
            gt, et, eid = self.resolve_group_dimension(ev, group_by=group_by)
            pkey = (ev.tenant_id, ev.user_id, ev.watchlist_id, gt, et, eid.strip().lower())
            if pkey not in partitions:
                partitions[pkey] = []
            partitions[pkey].append(ev)

        result_groups: list[AlertGroup] = []

        # 3. Process each partition with chronological windowing
        for (t_id, u_id, w_id, gt, et, eid_norm), part_events in partitions.items():
            # Check existing groups in repo for this partition to allow incremental additions
            existing_user_groups = self.group_repo.list_by_user(
                user_id=u_id,
                tenant_id=t_id,
                watchlist_id=w_id,
                group_type=gt,
            )

            # Filter existing groups matching this entity
            matching_existing: list[AlertGroup] = [
                g for g in existing_user_groups
                if eid_norm in [x.lower() for x in g.affected_entity_ids]
                or g.metadata.get("primary_entity_id", "").lower() == eid_norm
            ]
            matching_existing.sort(key=lambda g: (g.first_event_at, g.group_id))

            # Cluster events into window buckets anchored to the earliest event in each cluster
            # active_group represents the current open group in this partition
            current_group: Optional[AlertGroup] = None

            for ev in part_events:
                ev_dt = _parse_iso(ev.created_at)

                # Check if this event joins an existing matching group from disk
                joined_existing = False
                for eg in matching_existing:
                    first_dt = _parse_iso(eg.first_event_at)
                    diff = (ev_dt - first_dt).total_seconds()
                    if 0 <= diff <= self.window_seconds:
                        # Joins existing group
                        eg.add_event(ev)
                        current_group = eg
                        joined_existing = True
                        if current_group not in result_groups:
                            result_groups.append(current_group)
                        break

                if joined_existing:
                    continue

                # Check if this event joins current_group created in this run
                if current_group is not None:
                    first_dt = _parse_iso(current_group.first_event_at)
                    diff = (ev_dt - first_dt).total_seconds()
                    if 0 <= diff <= self.window_seconds:
                        current_group.add_event(ev)
                        if current_group not in result_groups:
                            result_groups.append(current_group)
                        continue

                # If we reach here, this event starts a new window cluster
                window_anchor = ev.created_at
                window_id = f"anchor_{window_anchor}"
                ag_key = compute_aggregation_key(
                    tenant_id=t_id,
                    user_id=u_id,
                    watchlist_id=w_id,
                    group_type=gt,
                    entity_type=et,
                    entity_id=eid_norm,
                    window_id=window_id,
                )
                group_id = f"grp_{ag_key[:16]}"

                # Check if already in repository by aggregation key
                existing_by_key = self.group_repo.find_by_aggregation_key(ag_key, tenant_id=t_id, user_id=u_id)
                if existing_by_key:
                    current_group = existing_by_key
                    current_group.add_event(ev)
                else:
                    current_group = AlertGroup(
                        group_id=group_id,
                        tenant_id=t_id,
                        user_id=u_id,
                        watchlist_id=w_id,
                        group_type=gt,
                        aggregation_key=ag_key,
                        title="",
                        summary="",
                        alert_count=0,
                        first_event_at=ev.created_at,
                        latest_event_at=ev.created_at,
                        severity=ev.severity,
                        event_ids=[],
                        affected_entity_ids=[eid_norm],
                        status=AlertGroupStatus.ACTIVE,
                        created_at=ev.created_at,
                        updated_at=ev.created_at,
                        metadata={
                            "primary_entity_type": et.value if et else None,
                            "primary_entity_id": eid_norm,
                            "window_anchor": window_anchor,
                        },
                    )
                    current_group.add_event(ev)
                    matching_existing.append(current_group)

                if current_group not in result_groups:
                    result_groups.append(current_group)

        # 4. Finalize titles, summaries, and persistence for all affected groups
        for grp in result_groups:
            # Resolve actual events belonging to this group
            grp_events = [self.event_repo.get(eid, tenant_id=grp.tenant_id, user_id=grp.user_id) for eid in grp.event_ids]
            valid_events = [e for e in grp_events if e is not None]
            if not valid_events:
                # If events are in memory from the input list
                id_map = {e.alert_event_id: e for e in events}
                valid_events = [id_map[eid] for eid in grp.event_ids if eid in id_map]

            entity_label = grp.metadata.get("primary_entity_id") or (
                grp.affected_entity_ids[0] if grp.affected_entity_ids else "alert"
            )
            grp.title = self._build_group_title(grp.group_type, entity_label, valid_events)
            grp.summary = self._build_group_summary(valid_events)

            if save:
                self.group_repo.save(grp)

        return result_groups

    def aggregate_user_inbox(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        group_by: Optional[AlertGroupType] = None,
        save: bool = True,
    ) -> list[AlertGroup]:
        """
        Aggregate all unarchived AlertEvents in a user's inbox.
        """
        events = self.event_repo.list_by_user(user_id=user_id, tenant_id=tenant_id, limit=500)
        active_events = [e for e in events if not e.is_archived]
        return self.aggregate_events(active_events, group_by=group_by, save=save)

    def aggregate_watchlist(
        self,
        watchlist_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        group_by: Optional[AlertGroupType] = None,
        save: bool = True,
    ) -> list[AlertGroup]:
        """
        Aggregate all AlertEvents triggered by a specific watchlist.
        """
        events = self.event_repo.list_by_watchlist(
            watchlist_id=watchlist_id,
            tenant_id=tenant_id,
            user_id=user_id,
            limit=500,
        )
        return self.aggregate_events(events, group_by=group_by, save=save)

    def get_group(
        self,
        group_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[AlertGroup]:
        """Retrieve an AlertGroup by ID enforcing isolation."""
        return self.group_repo.get(group_id, tenant_id=tenant_id, user_id=user_id)

    def list_groups(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        watchlist_id: Optional[str] = None,
        group_type: Optional[AlertGroupType] = None,
        status: Optional[AlertGroupStatus] = None,
        limit: int = 100,
    ) -> list[AlertGroup]:
        """List groups for a user with optional filters."""
        return self.group_repo.list_by_user(
            user_id=user_id,
            tenant_id=tenant_id,
            watchlist_id=watchlist_id,
            group_type=group_type,
            status=status,
            limit=limit,
        )
