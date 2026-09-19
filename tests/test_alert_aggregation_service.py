"""
tests/test_alert_aggregation_service.py
=======================================
Comprehensive test suite for Task 8.13.5 — Alert Aggregation Engine.

Covers:
- Alert grouping across dimensions (BILL, COMPANY, SECTOR, INDUSTRY, STATE, JURISDICTION, EVENT)
- Event preservation and immutability
- Configurable deterministic aggregation windowing
- Deduplication and idempotency
- Multi-watchlist isolation
- Multi-tenant and user isolation
- State alert aggregation with 0 predictions
- Central alert aggregation preserving existing predictions
- Intelligence-only company exposure aggregation
- Repository persistence and reload
- Task 8.13.4 integration and baseline invariants
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from config.settings import settings
from schemas.alert import (
    AlertEvent,
    AlertSeverity,
    AlertType,
    compute_dedup_key,
)
from schemas.alert_group import (
    AlertGroup,
    AlertGroupStatus,
    AlertGroupType,
    compute_aggregation_key,
)
from schemas.watchlist import WatchlistEntityType
from services.alert_aggregation_service import AlertAggregationService
from storage.alert_event_repository import AlertEventRepository
from storage.alert_group_repository import AlertGroupRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository

# Canonical 47 Central quantitative ISINs
CENTRAL_47_ISINS = frozenset([
    "INE002A01018", "INE467B01029", "INE040A01034", "INE009A01021", "INE090A01021",
    "INE397D01024", "INE062A01020", "INE018A01030", "INE154A01025", "INE030A01027",
    "INE423A01024", "INE155A01022", "INE044A01045", "INE733E01010", "INE213A01029",
    "INE238A01034", "INE237A01028", "INE075A01022", "INE860A01027", "INE585B01010",
    "INE101A01026", "INE081A01020", "INE019A01030", "INE038A01020", "INE522F01014",
    "INE481G01011", "INE047A01021", "INE239A01016", "INE216A01030", "INE192A01025",
    "INE021A01026", "INE059A01026", "INE089A01023", "INE437A01024", "INE752E01010",
    "INE245A01021", "INE364U01010", "INE814H01011", "INE296A01024", "INE918I01018",
    "INE00LIC01010", "INE123W01016", "INE795G01014", "INE066A01021", "INE158A01026",
    "INE917I01010", "INE669C01036",
])


@pytest.fixture
def test_env(tmp_path: Path):
    events_dir = tmp_path / "alerts" / "events"
    groups_dir = tmp_path / "alerts" / "groups"
    events_dir.mkdir(parents=True, exist_ok=True)
    groups_dir.mkdir(parents=True, exist_ok=True)

    event_repo = AlertEventRepository(root_dir=events_dir)
    group_repo = AlertGroupRepository(root_dir=groups_dir)
    svc = AlertAggregationService(
        alert_event_repo=event_repo,
        alert_group_repo=group_repo,
        window_hours=24,
    )
    return {
        "event_repo": event_repo,
        "group_repo": group_repo,
        "svc": svc,
        "tmp_path": tmp_path,
    }


def _make_event(
    event_id: str,
    user_id: str = "user_1",
    tenant_id: str = "tenant_1",
    watchlist_id: str = "wl_1",
    alert_type: AlertType = AlertType.BILL_STATUS_CHANGE,
    severity: AlertSeverity = AlertSeverity.MEDIUM,
    title: str = "Test Alert",
    entity_type: WatchlistEntityType = WatchlistEntityType.BILL,
    entity_id: str = "finance-bill-2024",
    created_at: str = "2026-09-17T10:00:00+00:00",
    prediction: str = "none",
    jurisdiction: str = "central",
) -> AlertEvent:
    dedup = compute_dedup_key(user_id, watchlist_id, event_id, alert_type)
    return AlertEvent(
        alert_event_id=event_id,
        tenant_id=tenant_id,
        user_id=user_id,
        watchlist_id=watchlist_id,
        source_event_id=f"src_{event_id}",
        alert_type=alert_type,
        severity=severity,
        title=title,
        summary="FACT: Legislative update\nDERIVED: Impact noticed\nINTERPRETATION: Keep monitoring\nPREDICTION: " + prediction,
        entity_type=entity_type,
        entity_id=entity_id,
        created_at=created_at,
        dedup_key=dedup,
        metadata={
            "source_event": {
                "event_id": f"src_{event_id}",
                "bill_id": entity_id if entity_type == WatchlistEntityType.BILL else None,
                "company_id": entity_id if entity_type == WatchlistEntityType.COMPANY else None,
                "jurisdiction": jurisdiction,
            },
            "structured_content": {
                "fact": f"Fact about {entity_id}",
                "derived": "Derived impact",
                "interpretation": "Regulatory observation",
                "prediction": prediction,
            },
        },
    )


# ===========================================================================
# 1. ALERT GROUPING TESTS (Tests 1-7)
# ===========================================================================


class TestAlertGrouping:
    def test_1_create_group_from_alert_event(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]
        ev = _make_event("ev_1", title="Single Bill Event")
        event_repo.create(ev)

        groups = svc.aggregate_events([ev])
        assert len(groups) == 1
        grp = groups[0]
        assert grp.group_type == AlertGroupType.BILL
        assert grp.alert_count == 1
        assert grp.event_ids == ["ev_1"]
        assert grp.user_id == "user_1"
        assert grp.tenant_id == "tenant_1"

    def test_2_group_related_bill_events(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev1 = _make_event("ev_b1", alert_type=AlertType.NEW_BILL, title="New Bill Published", created_at="2026-09-17T10:00:00+00:00")
        ev2 = _make_event("ev_b2", alert_type=AlertType.BILL_STATUS_CHANGE, title="Status Passed", created_at="2026-09-17T12:00:00+00:00")
        ev3 = _make_event("ev_b3", alert_type=AlertType.BILL_DOCUMENT_CHANGE, title="Document Updated", created_at="2026-09-17T14:00:00+00:00")
        for e in (ev1, ev2, ev3):
            event_repo.create(e)

        groups = svc.aggregate_events([ev1, ev2, ev3])
        assert len(groups) == 1
        grp = groups[0]
        assert grp.group_type == AlertGroupType.BILL
        assert grp.alert_count == 3
        assert grp.event_ids == ["ev_b1", "ev_b2", "ev_b3"]
        assert "finance-bill-2024" in grp.affected_entity_ids

    def test_3_group_related_company_events(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev1 = _make_event("ev_c1", entity_type=WatchlistEntityType.COMPANY, entity_id="INE002A01018", alert_type=AlertType.NEW_COMPANY_EXPOSURE)
        ev2 = _make_event("ev_c2", entity_type=WatchlistEntityType.COMPANY, entity_id="INE002A01018", alert_type=AlertType.EXPOSURE_CHANGE)
        event_repo.create(ev1)
        event_repo.create(ev2)

        groups = svc.aggregate_events([ev1, ev2])
        assert len(groups) == 1
        grp = groups[0]
        assert grp.group_type == AlertGroupType.COMPANY
        assert grp.alert_count == 2
        assert "ine002a01018" in [x.lower() for x in grp.affected_entity_ids]

    def test_4_group_sector_events(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev1 = _make_event("ev_s1", entity_type=WatchlistEntityType.SECTOR, entity_id="Technology", alert_type=AlertType.SECTOR_IMPACT)
        ev2 = _make_event("ev_s2", entity_type=WatchlistEntityType.SECTOR, entity_id="Technology", alert_type=AlertType.SECTOR_IMPACT)
        event_repo.create(ev1)
        event_repo.create(ev2)

        groups = svc.aggregate_events([ev1, ev2])
        assert len(groups) == 1
        assert groups[0].group_type == AlertGroupType.SECTOR
        assert groups[0].alert_count == 2

    def test_5_group_industry_events(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev1 = _make_event("ev_i1", entity_type=WatchlistEntityType.INDUSTRY, entity_id="Quick Commerce", alert_type=AlertType.SECTOR_IMPACT)
        ev2 = _make_event("ev_i2", entity_type=WatchlistEntityType.INDUSTRY, entity_id="Quick Commerce", alert_type=AlertType.SECTOR_IMPACT)
        event_repo.create(ev1)
        event_repo.create(ev2)

        groups = svc.aggregate_events([ev1, ev2])
        assert len(groups) == 1
        assert groups[0].group_type == AlertGroupType.INDUSTRY
        assert groups[0].alert_count == 2

    def test_6_group_state_events(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev1 = _make_event("ev_st1", entity_type=WatchlistEntityType.STATE, entity_id="Karnataka", alert_type=AlertType.STATE_IMPACT, jurisdiction="state")
        ev2 = _make_event("ev_st2", entity_type=WatchlistEntityType.STATE, entity_id="Karnataka", alert_type=AlertType.STATE_IMPACT, jurisdiction="state")
        event_repo.create(ev1)
        event_repo.create(ev2)

        groups = svc.aggregate_events([ev1, ev2])
        assert len(groups) == 1
        assert groups[0].group_type == AlertGroupType.STATE
        assert groups[0].alert_count == 2

    def test_7_group_jurisdiction_events(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev1 = _make_event("ev_j1", entity_type=WatchlistEntityType.JURISDICTION, entity_id="central", alert_type=AlertType.BILL_STATUS_CHANGE)
        ev2 = _make_event("ev_j2", entity_type=WatchlistEntityType.JURISDICTION, entity_id="central", alert_type=AlertType.NEW_BILL)
        event_repo.create(ev1)
        event_repo.create(ev2)

        groups = svc.aggregate_events([ev1, ev2])
        assert len(groups) == 1
        assert groups[0].group_type == AlertGroupType.JURISDICTION
        assert groups[0].alert_count == 2


# ===========================================================================
# 2. EVENT PRESERVATION & IMMUTABILITY (Tests 8-10)
# ===========================================================================


class TestEventPreservation:
    def test_8_underlying_alert_events_remain_unchanged(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev = _make_event("ev_imm", title="Original Headline", severity=AlertSeverity.LOW)
        event_repo.create(ev)
        original_dict = ev.to_dict()

        svc.aggregate_events([ev])

        reloaded = event_repo.get("ev_imm", tenant_id="tenant_1", user_id="user_1")
        assert reloaded is not None
        assert reloaded.to_dict() == original_dict

    def test_9_group_references_correct_event_ids(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev1 = _make_event("ev_ref1", created_at="2026-09-17T09:00:00+00:00")
        ev2 = _make_event("ev_ref2", created_at="2026-09-17T11:00:00+00:00")
        event_repo.create(ev1)
        event_repo.create(ev2)

        groups = svc.aggregate_events([ev1, ev2])
        assert groups[0].event_ids == ["ev_ref1", "ev_ref2"]

    def test_10_multiple_events_can_belong_to_one_group(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        events = [
            _make_event(f"ev_multi_{i}", created_at=f"2026-09-17T1{i}:00:00+00:00")
            for i in range(5)
        ]
        for e in events:
            event_repo.create(e)

        groups = svc.aggregate_events(events)
        assert len(groups) == 1
        assert groups[0].alert_count == 5
        assert len(groups[0].event_ids) == 5


# ===========================================================================
# 3. AGGREGATION WINDOW (Tests 11-13)
# ===========================================================================


class TestAggregationWindow:
    def test_11_events_inside_window_aggregate(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        t0 = "2026-09-17T08:00:00+00:00"
        t1 = "2026-09-17T20:00:00+00:00"  # 12 hours later (within 24h window)
        ev1 = _make_event("ev_win1", created_at=t0)
        ev2 = _make_event("ev_win2", created_at=t1)
        event_repo.create(ev1)
        event_repo.create(ev2)

        groups = svc.aggregate_events([ev1, ev2])
        assert len(groups) == 1
        assert groups[0].alert_count == 2

    def test_12_events_outside_window_remain_separate(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        t0 = "2026-09-17T08:00:00+00:00"
        t_outside = "2026-09-18T10:00:00+00:00"  # 26 hours later (> 24h window)
        ev1 = _make_event("ev_sep1", created_at=t0)
        ev2 = _make_event("ev_sep2", created_at=t_outside)
        event_repo.create(ev1)
        event_repo.create(ev2)

        groups = svc.aggregate_events([ev1, ev2])
        assert len(groups) == 2
        assert groups[0].group_id != groups[1].group_id
        assert groups[0].alert_count == 1
        assert groups[1].alert_count == 1

    def test_13_window_boundary_is_deterministic(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        t_base = datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)
        # Event exactly at 24 hours boundary
        ev_start = _make_event("ev_bound_start", created_at=t_base.isoformat())
        ev_exact = _make_event("ev_bound_exact", created_at=(t_base + timedelta(hours=24)).isoformat())
        # Event 1 second beyond boundary
        ev_beyond = _make_event("ev_bound_beyond", created_at=(t_base + timedelta(hours=24, seconds=1)).isoformat())

        for e in (ev_start, ev_exact, ev_beyond):
            event_repo.create(e)

        groups = svc.aggregate_events([ev_start, ev_exact, ev_beyond])
        # ev_start and ev_exact should be in group 1 (<= 24h), ev_beyond should be in group 2
        assert len(groups) == 2
        assert "ev_bound_start" in groups[0].event_ids
        assert "ev_bound_exact" in groups[0].event_ids
        assert "ev_bound_beyond" in groups[1].event_ids


# ===========================================================================
# 4. DEDUPLICATION & IDEMPOTENCY (Tests 14-16)
# ===========================================================================


class TestDeduplicationAndIdempotency:
    def test_14_reprocessing_same_events_does_not_duplicate_group(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]
        group_repo = test_env["group_repo"]

        ev1 = _make_event("ev_rep1")
        ev2 = _make_event("ev_rep2")
        event_repo.create(ev1)
        event_repo.create(ev2)

        run1 = svc.aggregate_events([ev1, ev2])
        assert len(run1) == 1
        initial_id = run1[0].group_id

        # Reprocess
        run2 = svc.aggregate_events([ev1, ev2])
        assert len(run2) == 1
        assert run2[0].group_id == initial_id

        # Verify disk has only 1 group
        persisted = group_repo.list_by_user("user_1", "tenant_1")
        assert len(persisted) == 1

    def test_15_group_membership_remains_unique(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev = _make_event("ev_uniq")
        event_repo.create(ev)

        svc.aggregate_events([ev])
        svc.aggregate_events([ev])
        groups = svc.aggregate_events([ev])

        assert groups[0].event_ids == ["ev_uniq"]
        assert groups[0].alert_count == 1

    def test_16_aggregation_key_remains_deterministic(self, test_env):
        k1 = compute_aggregation_key(
            tenant_id="t1",
            user_id="u1",
            watchlist_id="w1",
            group_type=AlertGroupType.BILL,
            entity_type=WatchlistEntityType.BILL,
            entity_id="bill-x",
            window_id="anchor_2026-09-17T00:00:00+00:00",
        )
        k2 = compute_aggregation_key(
            tenant_id="t1",
            user_id="u1",
            watchlist_id="w1",
            group_type=AlertGroupType.BILL,
            entity_type=WatchlistEntityType.BILL,
            entity_id="bill-x",
            window_id="anchor_2026-09-17T00:00:00+00:00",
        )
        assert k1 == k2


# ===========================================================================
# 5. MULTI-WATCHLIST & ISOLATION (Tests 17-19)
# ===========================================================================


class TestMultiWatchlistAndIsolation:
    def test_17_same_company_in_two_watchlists_remains_isolated(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev_wl_a = _make_event("ev_wla", watchlist_id="wl_a", entity_type=WatchlistEntityType.COMPANY, entity_id="INE002A01018")
        ev_wl_b = _make_event("ev_wlb", watchlist_id="wl_b", entity_type=WatchlistEntityType.COMPANY, entity_id="INE002A01018")
        event_repo.create(ev_wl_a)
        event_repo.create(ev_wl_b)

        groups = svc.aggregate_events([ev_wl_a, ev_wl_b])
        assert len(groups) == 2
        wl_ids = {g.watchlist_id for g in groups}
        assert wl_ids == {"wl_a", "wl_b"}

    def test_18_user_a_cannot_see_user_b_groups(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]
        group_repo = test_env["group_repo"]

        ev_u1 = _make_event("ev_u1", user_id="user_alpha")
        ev_u2 = _make_event("ev_u2", user_id="user_beta")
        event_repo.create(ev_u1)
        event_repo.create(ev_u2)

        svc.aggregate_events([ev_u1, ev_u2])

        u1_groups = group_repo.list_by_user("user_alpha", "tenant_1")
        u2_groups = group_repo.list_by_user("user_beta", "tenant_1")

        assert len(u1_groups) == 1
        assert len(u2_groups) == 1
        assert u1_groups[0].user_id == "user_alpha"
        assert u2_groups[0].user_id == "user_beta"

    def test_19_tenant_a_cannot_see_tenant_b_groups(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]
        group_repo = test_env["group_repo"]

        ev_t1 = _make_event("ev_t1", tenant_id="tenant_alpha")
        ev_t2 = _make_event("ev_t2", tenant_id="tenant_beta")
        event_repo.create(ev_t1)
        event_repo.create(ev_t2)

        svc.aggregate_events([ev_t1, ev_t2])

        t1_groups = group_repo.list_by_user("user_1", "tenant_alpha")
        t2_groups = group_repo.list_by_user("user_1", "tenant_beta")

        assert len(t1_groups) == 1
        assert len(t2_groups) == 1
        assert t1_groups[0].tenant_id == "tenant_alpha"
        assert t2_groups[0].tenant_id == "tenant_beta"


# ===========================================================================
# 6. STATE & CENTRAL ALERTS & INTELLIGENCE COMPANIES (Tests 20-25)
# ===========================================================================


class TestStateCentralAndIntelligence:
    def test_20_state_alerts_aggregate_correctly(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev = _make_event("ev_state1", entity_type=WatchlistEntityType.STATE, entity_id="Kerala", jurisdiction="state")
        event_repo.create(ev)

        groups = svc.aggregate_events([ev])
        assert len(groups) == 1
        assert groups[0].group_type == AlertGroupType.STATE
        assert "kerala" in [x.lower() for x in groups[0].affected_entity_ids]

    def test_21_state_aggregation_creates_no_prediction(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev = _make_event("ev_state2", entity_type=WatchlistEntityType.STATE, entity_id="Karnataka", jurisdiction="state", prediction="none")
        event_repo.create(ev)

        groups = svc.aggregate_events([ev])
        assert "PREDICTION: none" in groups[0].summary
        assert "predicted_car" not in groups[0].metadata

    def test_22_central_alerts_aggregate_correctly(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev1 = _make_event("ev_cent1", entity_type=WatchlistEntityType.BILL, entity_id="the-coastal-shipping-bill-2024", jurisdiction="central")
        ev2 = _make_event("ev_cent2", entity_type=WatchlistEntityType.BILL, entity_id="the-coastal-shipping-bill-2024", jurisdiction="central")
        event_repo.create(ev1)
        event_repo.create(ev2)

        groups = svc.aggregate_events([ev1, ev2])
        assert len(groups) == 1
        assert groups[0].group_type == AlertGroupType.BILL
        assert groups[0].alert_count == 2

    def test_23_existing_central_prediction_references_remain_unchanged(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev = _make_event(
            "ev_cent_pred",
            entity_type=WatchlistEntityType.BILL,
            entity_id="the-coastal-shipping-bill-2024",
            prediction="Direction: POSITIVE, Strength: HIGH, Conf: 0.88",
            jurisdiction="central",
        )
        event_repo.create(ev)

        groups = svc.aggregate_events([ev])
        assert "Direction: POSITIVE" in groups[0].summary
        # Verify prediction is preserved without tampering
        assert "PREDICTION: Direction: POSITIVE, Strength: HIGH, Conf: 0.88" in groups[0].summary

    def test_24_intelligence_company_alerts_can_aggregate(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev = _make_event(
            "ev_intel1",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="PRIV-BUNDL-SWIGGY",  # Non-quant intelligence company
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
        )
        event_repo.create(ev)

        groups = svc.aggregate_events([ev])
        assert len(groups) == 1
        assert groups[0].group_type == AlertGroupType.COMPANY
        assert "priv-bundl-swiggy" in [x.lower() for x in groups[0].affected_entity_ids]

    def test_25_no_prediction_is_generated_for_intelligence_only_company(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]

        ev = _make_event(
            "ev_intel2",
            entity_type=WatchlistEntityType.COMPANY,
            entity_id="PRIV-BUNDL-SWIGGY",
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            prediction="none",
        )
        event_repo.create(ev)

        groups = svc.aggregate_events([ev])
        assert "PREDICTION: none" in groups[0].summary
        assert "predicted_car" not in groups[0].metadata


# ===========================================================================
# 7. PERSISTENCE & INTEGRATION (Tests 26-28)
# ===========================================================================


class TestPersistenceAndIntegration:
    def test_26_groups_survive_repository_reload(self, test_env):
        svc = test_env["svc"]
        event_repo = test_env["event_repo"]
        tmp_path = test_env["tmp_path"]

        ev = _make_event("ev_reload")
        event_repo.create(ev)
        svc.aggregate_events([ev])

        # Instantiate fresh repository from same directory
        groups_dir = tmp_path / "alerts" / "groups"
        reloaded_repo = AlertGroupRepository(root_dir=groups_dir)
        user_groups = reloaded_repo.list_by_user("user_1", "tenant_1")
        assert len(user_groups) == 1
        assert "ev_reload" in user_groups[0].event_ids

    def test_27_alert_events_from_task_8_13_4_can_be_consumed(self, test_env):
        svc = test_env["svc"]
        # Standard AlertEvent structure from AlertMatchingService
        ev = AlertEvent(
            alert_event_id="t8134_event_1",
            tenant_id="default_tenant",
            user_id="default_user",
            watchlist_id="wl_default",
            alert_rule_id="r_default",
            source_event_id="src_match_1",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.HIGH,
            title="[Bill Status Change] The Finance Bill 2024",
            summary="FACT: Passed Lok Sabha\nDERIVED: Financial sector impact\nINTERPRETATION: Ready for enactment\nPREDICTION: none",
            entity_type=WatchlistEntityType.BILL,
            entity_id="finance-bill-2024",
            created_at="2026-09-17T12:00:00+00:00",
            metadata={"source": "test_matching"},
        )
        test_env["event_repo"].create(ev)

        groups = svc.aggregate_events([ev])
        assert len(groups) == 1
        assert groups[0].group_type == AlertGroupType.BILL
        assert groups[0].event_ids == ["t8134_event_1"]

    def test_28_existing_alert_event_dedup_remains_intact(self, test_env):
        event_repo = test_env["event_repo"]
        ev = _make_event("ev_dedup_intact")
        event_repo.create(ev)
        assert event_repo.is_duplicate(ev.dedup_key)
        # Re-adding raises ValueError
        with pytest.raises(ValueError):
            event_repo.create(ev)


# ===========================================================================
# 8. FROZEN BASELINE INVARIANTS (Tests 29-33)
# ===========================================================================


class TestFrozenBaselineInvariants:
    def test_29_central_47_companies_unchanged(self):
        comp_repo = CompanyRepository()
        all_comps = comp_repo.get_all()
        quant_comps = [c for c in all_comps if c.isin in CENTRAL_47_ISINS]
        assert len(quant_comps) == 47

    def test_30_central_940_pairs_unchanged(self):
        bill_repo = BillRepository()
        prod_central_bills = [
            b for b in bill_repo.get_all()
            if b.bill_id not in ("key-issues-and-analysis", "service-bill")
        ]
        assert len(prod_central_bills) == 20
        assert len(prod_central_bills) * len(CENTRAL_47_ISINS) == 940

    def test_31_central_4700_predictions_unchanged(self):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700

    def test_32_state_86_exposures_unchanged(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        assert len(state_exps) == 86

    def test_33_state_predictions_remain_zero(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        for e in state_exps:
            assert not hasattr(e, "predicted_car")
            assert not hasattr(e, "expected_return")
