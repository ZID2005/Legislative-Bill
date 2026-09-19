"""
services/alert_digest_service.py
================================
Alert Digest Pipeline for building presentation-ready alert digests.

Transforms AlertGroups and AlertEvents into structured digest packages
for real-time delivery, daily summaries, and weekly reports according to
user AlertPreferences and multi-tenant isolation.

This service strictly prepares and structures digest content.
It does NOT deliver notifications externally.

Task 8.13.5 — Alert Aggregation & Digest Pipeline.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any, Optional
import uuid

from config.logging_config import get_logger
from config.settings import settings
from schemas.alert import (
    AlertEvent,
    AlertPreference,
    AlertSeverity,
    AlertType,
    DigestFrequency,
)
from schemas.alert_digest import AlertDigest, DigestType
from schemas.alert_group import (
    AlertGroup,
    AlertGroupStatus,
    AlertGroupType,
    severity_rank,
)
from storage.alert_event_repository import AlertEventRepository
from storage.alert_group_repository import AlertGroupRepository
from storage.alert_preference_repository import AlertPreferenceRepository
from utils.file_utils import ensure_dir

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


class AlertDigestService:
    """
    Engine for creating presentation-ready digests from AlertGroups and AlertEvents.
    """

    def __init__(
        self,
        alert_group_repo: Optional[AlertGroupRepository] = None,
        alert_event_repo: Optional[AlertEventRepository] = None,
        alert_pref_repo: Optional[AlertPreferenceRepository] = None,
        digests_dir: Optional[Path] = None,
    ) -> None:
        self.group_repo = alert_group_repo or AlertGroupRepository()
        self.event_repo = alert_event_repo or AlertEventRepository()
        self.pref_repo = alert_pref_repo or AlertPreferenceRepository()
        self._digests_dir = digests_dir or settings.ALERT_DIGESTS_DIR
        ensure_dir(self._digests_dir)

    def _user_digest_dir(self, tenant_id: str, user_id: str) -> Path:
        p = self._digests_dir / tenant_id / user_id
        ensure_dir(p)
        return p

    def save_digest(self, digest: AlertDigest) -> AlertDigest:
        """Persist a generated digest to disk."""
        digest.validate()
        p = self._user_digest_dir(digest.tenant_id, digest.user_id) / f"digest_{digest.digest_id}.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(digest.to_dict(), f, indent=2)
        return digest

    def get_digest(
        self,
        digest_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> Optional[AlertDigest]:
        """Load a persisted digest by ID enforcing isolation."""
        p = self._user_digest_dir(tenant_id, user_id) / f"digest_{digest_id}.json"
        if not p.is_file():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                return AlertDigest.from_dict(json.load(f))
        except Exception as e:
            logger.error("Failed to load digest %s: %s", digest_id, e)
            return None

    def _resolve_period_bounds(
        self,
        digest_type: DigestType,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        reference_time: Optional[datetime] = None,
    ) -> tuple[str, str]:
        """Compute start and end ISO timestamps for digest period."""
        ref = reference_time or datetime.now(timezone.utc)
        if end_time:
            end_dt = _parse_iso(end_time)
        else:
            end_dt = ref

        if start_time:
            start_dt = _parse_iso(start_time)
        else:
            if digest_type == DigestType.REAL_TIME:
                start_dt = end_dt - timedelta(hours=1)
            elif digest_type == DigestType.DAILY:
                start_dt = end_dt - timedelta(hours=24)
            elif digest_type == DigestType.WEEKLY:
                start_dt = end_dt - timedelta(days=7)
            else:
                start_dt = end_dt - timedelta(hours=24)

        return start_dt.isoformat(), end_dt.isoformat()

    def _sort_groups_deterministically(self, groups: list[AlertGroup]) -> list[AlertGroup]:
        """
        Sort groups using strict deterministic ordering:
        1. Severity rank descending (CRITICAL -> INFO)
        2. Latest event timestamp descending
        3. Stable group_id ascending
        """
        return sorted(
            groups,
            key=lambda g: (-severity_rank(g.severity), g.latest_event_at, g.group_id),
            reverse=False,
        )

    def generate_digest(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        digest_type: DigestType = DigestType.DAILY,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        reference_time: Optional[datetime] = None,
        groups: Optional[list[AlertGroup]] = None,
        save: bool = True,
    ) -> AlertDigest:
        """
        Generate a structured AlertDigest for a user and period.

        Enforces:
        - User AlertPreferences (suppresses or filters if disabled/unsupported).
        - Severity filtering.
        - Allowed alert type filtering.
        - Deterministic sorting.
        - Pure factual/derived/interpretive grounding (no AI fabrication).
        - Valid empty digest if no qualifying alerts exist.
        """
        period_start, period_end = self._resolve_period_bounds(
            digest_type=digest_type,
            start_time=start_time,
            end_time=end_time,
            reference_time=reference_time,
        )

        freq_map = {
            DigestType.REAL_TIME: DigestFrequency.REAL_TIME,
            DigestType.DAILY: DigestFrequency.DAILY_DIGEST,
            DigestType.WEEKLY: DigestFrequency.WEEKLY_DIGEST,
        }
        frequency = freq_map.get(digest_type, DigestFrequency.DAILY_DIGEST)

        # 1. Check user preferences
        pref = self.pref_repo.get_by_user(user_id, tenant_id=tenant_id)
        if pref and not pref.enabled:
            logger.debug("Alerts disabled for user %s. Returning empty digest.", user_id)
            empty = AlertDigest(
                digest_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                digest_type=digest_type,
                frequency=frequency,
                period_start=period_start,
                period_end=period_end,
                group_ids=[],
                event_ids=[],
                group_count=0,
                event_count=0,
                affected_companies=[],
                affected_bills=[],
                affected_sectors=[],
                affected_states=[],
                jurisdictions=[],
                groups=[],
                generated_at=_utcnow_iso(),
                metadata={"suppressed_by_preference": True},
            )
            if save:
                self.save_digest(empty)
            return empty

        # 2. Gather eligible groups
        if groups is None:
            raw_groups = self.group_repo.list_by_period(
                user_id=user_id,
                tenant_id=tenant_id,
                start_time=period_start,
                end_time=period_end,
                limit=200,
            )
        else:
            # Enforce user and tenant boundary on passed groups
            raw_groups = [
                g for g in groups
                if g.user_id == user_id and g.tenant_id == tenant_id
            ]
            if start_time or end_time:
                raw_groups = [
                    g for g in raw_groups
                    if (not start_time or g.latest_event_at >= start_time)
                    and (not end_time or g.first_event_at <= end_time)
                ]

        # 3. Filter by preferences if configured
        filtered_groups: list[AlertGroup] = []
        for grp in raw_groups:
            if grp.status == AlertGroupStatus.ARCHIVED:
                continue

            # Minimum severity filter
            if pref:
                if severity_rank(grp.severity) < severity_rank(pref.minimum_severity):
                    continue

                # Filter by allowed alert types if available from underlying events
                # Inspect underlying events
                if pref.allowed_alert_types:
                    has_allowed = False
                    for eid in grp.event_ids:
                        ev = self.event_repo.get(eid, tenant_id=tenant_id, user_id=user_id)
                        if ev and ev.alert_type in pref.allowed_alert_types:
                            has_allowed = True
                            break
                    if grp.event_ids and not has_allowed:
                        continue

            filtered_groups.append(grp)

        # 4. Sort groups deterministically
        sorted_groups = self._sort_groups_deterministically(filtered_groups)

        # 5. Extract entity references and all member event IDs
        all_event_ids: list[str] = []
        affected_companies: list[str] = []
        affected_bills: list[str] = []
        affected_sectors: list[str] = []
        affected_states: list[str] = []
        jurisdictions: list[str] = []

        serialized_groups: list[dict[str, Any]] = []

        for grp in sorted_groups:
            serialized_groups.append(grp.to_dict())

            for eid in grp.event_ids:
                if eid not in all_event_ids:
                    all_event_ids.append(eid)
                ev = self.event_repo.get(eid, tenant_id=tenant_id, user_id=user_id)
                if ev:
                    src = ev.metadata.get("source_event", {})
                    # Companies
                    cid = src.get("company_id") or (ev.entity_id if grp.group_type == AlertGroupType.COMPANY else None)
                    if cid and cid not in affected_companies:
                        affected_companies.append(cid)

                    # Bills
                    bid = src.get("bill_id") or (ev.entity_id if grp.group_type == AlertGroupType.BILL else None)
                    if bid and bid not in affected_bills:
                        affected_bills.append(bid)

                    # Sectors
                    sec = src.get("sector_id") or (ev.entity_id if grp.group_type == AlertGroupType.SECTOR else None)
                    if sec and sec not in affected_sectors:
                        affected_sectors.append(sec)

                    # States
                    st = src.get("state_id") or (ev.entity_id if grp.group_type == AlertGroupType.STATE else None)
                    if st and st not in affected_states:
                        affected_states.append(st)

                    # Jurisdictions
                    jur = src.get("jurisdiction") or (ev.entity_id if grp.group_type == AlertGroupType.JURISDICTION else None)
                    if jur and jur not in jurisdictions:
                        jurisdictions.append(jur)

            # Also check group's direct affected entity IDs
            if grp.group_type == AlertGroupType.COMPANY:
                for cid in grp.affected_entity_ids:
                    if cid not in affected_companies:
                        affected_companies.append(cid)
            elif grp.group_type == AlertGroupType.BILL:
                for bid in grp.affected_entity_ids:
                    if bid not in affected_bills:
                        affected_bills.append(bid)
            elif grp.group_type == AlertGroupType.STATE:
                for st in grp.affected_entity_ids:
                    if st not in affected_states:
                        affected_states.append(st)
            elif grp.group_type == AlertGroupType.SECTOR:
                for sec in grp.affected_entity_ids:
                    if sec not in affected_sectors:
                        affected_sectors.append(sec)

        digest = AlertDigest(
            digest_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            digest_type=digest_type,
            frequency=frequency,
            period_start=period_start,
            period_end=period_end,
            group_ids=[g.group_id for g in sorted_groups],
            event_ids=all_event_ids,
            group_count=len(sorted_groups),
            event_count=len(all_event_ids),
            affected_companies=sorted(affected_companies),
            affected_bills=sorted(affected_bills),
            affected_sectors=sorted(affected_sectors),
            affected_states=sorted(affected_states),
            jurisdictions=sorted(jurisdictions),
            groups=serialized_groups,
            generated_at=_utcnow_iso(),
            metadata={
                "total_candidates": len(raw_groups),
                "filtered_count": len(sorted_groups),
            },
        )

        if save:
            self.save_digest(digest)

        return digest

    def prepare_real_time_digest(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        groups: Optional[list[AlertGroup]] = None,
        save: bool = True,
    ) -> AlertDigest:
        """Construct immediate real-time digest of eligible alert groups."""
        return self.generate_digest(
            user_id=user_id,
            tenant_id=tenant_id,
            digest_type=DigestType.REAL_TIME,
            groups=groups,
            save=save,
        )

    def prepare_daily_digest(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        groups: Optional[list[AlertGroup]] = None,
        reference_time: Optional[datetime] = None,
        save: bool = True,
    ) -> AlertDigest:
        """Construct daily digest of alert groups covering the last 24 hours."""
        return self.generate_digest(
            user_id=user_id,
            tenant_id=tenant_id,
            digest_type=DigestType.DAILY,
            groups=groups,
            reference_time=reference_time,
            save=save,
        )

    def prepare_weekly_digest(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        groups: Optional[list[AlertGroup]] = None,
        reference_time: Optional[datetime] = None,
        save: bool = True,
    ) -> AlertDigest:
        """Construct weekly digest of alert groups covering the last 7 days."""
        return self.generate_digest(
            user_id=user_id,
            tenant_id=tenant_id,
            digest_type=DigestType.WEEKLY,
            groups=groups,
            reference_time=reference_time,
            save=save,
        )
