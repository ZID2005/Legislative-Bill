"""
tests/test_alert_digest_service.py
==================================
Comprehensive test suite for Task 8.13.5 — Alert Digest Pipeline.

Covers:
- Digest generation across cadences (REAL_TIME, DAILY, WEEKLY)
- Empty digest handling and zero fabrication
- User AlertPreference integration (master toggle, minimum severity, allowed types)
- Deterministic ordering by severity, timestamp, and group_id
- Multi-watchlist aggregation at digest level
- Multi-tenant and user isolation
- Persistence and reload integrity
- Critical frozen baseline verification
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from config.settings import settings
from schemas.alert import (
    AlertEvent,
    AlertPreference,
    AlertSeverity,
    AlertType,
    DigestFrequency,
    compute_dedup_key,
)
from schemas.alert_digest import AlertDigest, DigestType
from schemas.alert_group import (
    AlertGroup,
    AlertGroupStatus,
    AlertGroupType,
    compute_aggregation_key,
)
from schemas.watchlist import WatchlistEntityType
from services.alert_digest_service import AlertDigestService
from storage.alert_event_repository import AlertEventRepository
from storage.alert_group_repository import AlertGroupRepository
from storage.alert_preference_repository import AlertPreferenceRepository
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
def digest_env(tmp_path: Path):
    events_dir = tmp_path / "alerts" / "events"
    groups_dir = tmp_path / "alerts" / "groups"
    prefs_dir = tmp_path / "alerts" / "preferences"
    digests_dir = tmp_path / "alerts" / "digests"

    for d in (events_dir, groups_dir, prefs_dir, digests_dir):
        d.mkdir(parents=True, exist_ok=True)

    event_repo = AlertEventRepository(root_dir=events_dir)
    group_repo = AlertGroupRepository(root_dir=groups_dir)
    pref_repo = AlertPreferenceRepository(root_dir=prefs_dir)

    svc = AlertDigestService(
        alert_group_repo=group_repo,
        alert_event_repo=event_repo,
        alert_pref_repo=pref_repo,
        digests_dir=digests_dir,
    )
    return {
        "event_repo": event_repo,
        "group_repo": group_repo,
        "pref_repo": pref_repo,
        "svc": svc,
        "tmp_path": tmp_path,
        "digests_dir": digests_dir,
    }


def _make_event_and_group(
    event_id: str,
    group_id: str,
    user_id: str = "user_1",
    tenant_id: str = "tenant_1",
    watchlist_id: str = "wl_1",
    alert_type: AlertType = AlertType.BILL_STATUS_CHANGE,
    severity: AlertSeverity = AlertSeverity.MEDIUM,
    entity_type: WatchlistEntityType = WatchlistEntityType.BILL,
    entity_id: str = "finance-bill-2024",
    created_at: str = "2026-09-17T10:00:00+00:00",
) -> tuple[AlertEvent, AlertGroup]:
    ev = AlertEvent(
        alert_event_id=event_id,
        tenant_id=tenant_id,
        user_id=user_id,
        watchlist_id=watchlist_id,
        source_event_id=f"src_{event_id}",
        alert_type=alert_type,
        severity=severity,
        title=f"Alert for {entity_id}",
        summary=f"Summary for {entity_id}",
        entity_type=entity_type,
        entity_id=entity_id,
        created_at=created_at,
        metadata={
            "source_event": {
                "bill_id": entity_id if entity_type == WatchlistEntityType.BILL else None,
                "company_id": entity_id if entity_type == WatchlistEntityType.COMPANY else None,
            }
        },
    )

    ag_key = compute_aggregation_key(
        tenant_id=tenant_id,
        user_id=user_id,
        watchlist_id=watchlist_id,
        group_type=AlertGroupType.BILL if entity_type == WatchlistEntityType.BILL else AlertGroupType.COMPANY,
        entity_type=entity_type,
        entity_id=entity_id,
        window_id=f"w_{created_at}",
    )

    grp = AlertGroup(
        group_id=group_id,
        tenant_id=tenant_id,
        user_id=user_id,
        watchlist_id=watchlist_id,
        group_type=AlertGroupType.BILL if entity_type == WatchlistEntityType.BILL else AlertGroupType.COMPANY,
        aggregation_key=ag_key,
        title=f"Group for {entity_id}",
        summary=f"Group summary for {entity_id}",
        alert_count=1,
        first_event_at=created_at,
        latest_event_at=created_at,
        severity=severity,
        event_ids=[event_id],
        affected_entity_ids=[entity_id],
        status=AlertGroupStatus.ACTIVE,
        created_at=created_at,
        updated_at=created_at,
    )
    return ev, grp


# ===========================================================================
# 1. DIGEST PREPARATION & CADENCES (Tests 1-4)
# ===========================================================================


class TestDigestCadences:
    def test_1_real_time_digest_preparation(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]

        t_now = datetime.now(timezone.utc).isoformat()
        ev, grp = _make_event_and_group("ev_rt", "grp_rt", created_at=t_now)
        event_repo.create(ev)
        group_repo.create(grp)

        digest = svc.prepare_real_time_digest(user_id="user_1", tenant_id="tenant_1", groups=[grp])
        assert digest.digest_type == DigestType.REAL_TIME
        assert digest.frequency == DigestFrequency.REAL_TIME
        assert digest.group_count == 1
        assert digest.event_count == 1
        assert "grp_rt" in digest.group_ids

    def test_2_daily_digest_preparation(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]

        ref_dt = datetime(2026, 9, 17, 18, 0, 0, tzinfo=timezone.utc)
        ev, grp = _make_event_and_group("ev_d", "grp_d", created_at="2026-09-17T12:00:00+00:00")
        event_repo.create(ev)
        group_repo.create(grp)

        digest = svc.prepare_daily_digest(
            user_id="user_1",
            tenant_id="tenant_1",
            groups=[grp],
            reference_time=ref_dt,
        )
        assert digest.digest_type == DigestType.DAILY
        assert digest.frequency == DigestFrequency.DAILY_DIGEST
        assert digest.group_count == 1
        assert digest.affected_bills == ["finance-bill-2024"]

    def test_3_weekly_digest_preparation(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]

        ref_dt = datetime(2026, 9, 17, 18, 0, 0, tzinfo=timezone.utc)
        # Event 3 days ago (within 7 days)
        ev, grp = _make_event_and_group("ev_w", "grp_w", created_at="2026-09-14T10:00:00+00:00")
        event_repo.create(ev)
        group_repo.create(grp)

        digest = svc.prepare_weekly_digest(
            user_id="user_1",
            tenant_id="tenant_1",
            groups=[grp],
            reference_time=ref_dt,
        )
        assert digest.digest_type == DigestType.WEEKLY
        assert digest.frequency == DigestFrequency.WEEKLY_DIGEST
        assert digest.group_count == 1

    def test_4_empty_digest_returns_valid_structured_object(self, digest_env):
        svc = digest_env["svc"]
        digest = svc.prepare_daily_digest(user_id="user_empty", tenant_id="tenant_1", groups=[])
        assert digest.group_count == 0
        assert digest.event_count == 0
        assert digest.group_ids == []
        assert digest.event_ids == []
        assert digest.affected_companies == []
        assert digest.affected_bills == []
        assert digest.groups == []
        # Invariant: No fake placeholder content
        assert digest.user_id == "user_empty"


# ===========================================================================
# 2. USER PREFERENCES INTEGRATION (Tests 5-7)
# ===========================================================================


class TestUserPreferences:
    def test_5_digest_respects_disabled_preference(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]
        pref_repo = digest_env["pref_repo"]

        pref_repo.create(
            AlertPreference(
                preference_id="pref_off",
                user_id="user_disabled",
                tenant_id="tenant_1",
                enabled=False,  # Master toggle disabled
            )
        )

        ev, grp = _make_event_and_group("ev_off", "grp_off", user_id="user_disabled")
        event_repo.create(ev)
        group_repo.create(grp)

        digest = svc.prepare_daily_digest(user_id="user_disabled", tenant_id="tenant_1", groups=[grp])
        assert digest.group_count == 0
        assert digest.event_count == 0
        assert digest.metadata.get("suppressed_by_preference") is True

    def test_6_digest_respects_severity_threshold(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]
        pref_repo = digest_env["pref_repo"]

        pref_repo.create(
            AlertPreference(
                preference_id="pref_sev",
                user_id="user_sev",
                tenant_id="tenant_1",
                minimum_severity=AlertSeverity.HIGH,  # Filter out LOW/MEDIUM
            )
        )

        # Low severity group
        ev_low, grp_low = _make_event_and_group("ev_l", "grp_l", user_id="user_sev", severity=AlertSeverity.LOW, entity_id="bill-low-sev")
        # Critical severity group
        ev_crit, grp_crit = _make_event_and_group("ev_c", "grp_c", user_id="user_sev", severity=AlertSeverity.CRITICAL, entity_id="bill-crit-sev")
        for e in (ev_low, ev_crit):
            event_repo.create(e)
        for g in (grp_low, grp_crit):
            group_repo.create(g)

        digest = svc.prepare_daily_digest(user_id="user_sev", tenant_id="tenant_1", groups=[grp_low, grp_crit])
        assert digest.group_count == 1
        assert digest.group_ids == ["grp_c"]
        assert "grp_l" not in digest.group_ids

    def test_7_digest_respects_allowed_alert_types(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]
        pref_repo = digest_env["pref_repo"]

        pref_repo.create(
            AlertPreference(
                preference_id="pref_types",
                user_id="user_allowed",
                tenant_id="tenant_1",
                allowed_alert_types=[AlertType.BILL_STATUS_CHANGE],  # Only BILL_STATUS_CHANGE
            )
        )

        ev_match, grp_match = _make_event_and_group("ev_m", "grp_m", user_id="user_allowed", alert_type=AlertType.BILL_STATUS_CHANGE, entity_id="finance-bill-2024")
        ev_unmatch, grp_unmatch = _make_event_and_group("ev_u", "grp_u", user_id="user_allowed", alert_type=AlertType.NEW_COMPANY_EXPOSURE, entity_id="INE002A01018", entity_type=WatchlistEntityType.COMPANY)
        event_repo.create(ev_match)
        event_repo.create(ev_unmatch)
        group_repo.create(grp_match)
        group_repo.create(grp_unmatch)

        digest = svc.prepare_daily_digest(user_id="user_allowed", tenant_id="tenant_1", groups=[grp_match, grp_unmatch])
        assert digest.group_count == 1
        assert digest.group_ids == ["grp_m"]


# ===========================================================================
# 3. DETERMINISTIC ORDERING & CITATIONS (Tests 8-10)
# ===========================================================================


class TestDigestOrderingAndProvenance:
    def test_8_digest_ordering_is_deterministic(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]

        # 3 groups with different severities and timestamps
        ev1, g1 = _make_event_and_group("e_ord1", "g_ord1", severity=AlertSeverity.LOW, created_at="2026-09-17T10:00:00+00:00")
        ev2, g2 = _make_event_and_group("e_ord2", "g_ord2", severity=AlertSeverity.CRITICAL, created_at="2026-09-17T09:00:00+00:00")
        ev3, g3 = _make_event_and_group("e_ord3", "g_ord3", severity=AlertSeverity.HIGH, created_at="2026-09-17T11:00:00+00:00")

        for e in (ev1, ev2, ev3):
            event_repo.create(e)
        for g in (g1, g2, g3):
            group_repo.create(g)

        # Ordering should be: CRITICAL (g2) -> HIGH (g3) -> LOW (g1)
        digest = svc.prepare_daily_digest(user_id="user_1", tenant_id="tenant_1", groups=[g1, g2, g3])
        assert digest.group_ids == ["g_ord2", "g_ord3", "g_ord1"]

    def test_9_digest_preserves_group_and_event_references(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]

        ev1, grp = _make_event_and_group("e_prov1", "g_prov", created_at="2026-09-17T10:00:00+00:00")
        ev2 = AlertEvent(
            alert_event_id="e_prov2",
            tenant_id="tenant_1",
            user_id="user_1",
            watchlist_id="wl_1",
            source_event_id="src_prov2",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.HIGH,
            title="Second Prov Event",
            created_at="2026-09-17T11:00:00+00:00",
        )
        grp.add_event(ev2)
        event_repo.create(ev1)
        event_repo.create(ev2)
        group_repo.create(grp)

        digest = svc.prepare_daily_digest(user_id="user_1", tenant_id="tenant_1", groups=[grp])
        assert digest.group_ids == ["g_prov"]
        assert "e_prov1" in digest.event_ids
        assert "e_prov2" in digest.event_ids
        assert digest.event_count == 2

    def test_10_user_level_digest_can_reference_multiple_watchlists(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]

        ev_a, g_a = _make_event_and_group("e_wa", "g_wa", watchlist_id="watchlist_alpha", entity_id="the-coastal-shipping-bill-2024")
        ev_b, g_b = _make_event_and_group("e_wb", "g_wb", watchlist_id="watchlist_beta", entity_id="INE002A01018", entity_type=WatchlistEntityType.COMPANY)
        event_repo.create(ev_a)
        event_repo.create(ev_b)
        group_repo.create(g_a)
        group_repo.create(g_b)

        digest = svc.prepare_daily_digest(user_id="user_1", tenant_id="tenant_1", groups=[g_a, g_b])
        assert digest.group_count == 2
        assert set(digest.group_ids) == {"g_wa", "g_wb"}
        assert "the-coastal-shipping-bill-2024" in digest.affected_bills
        assert "INE002A01018" in digest.affected_companies


# ===========================================================================
# 4. ISOLATION & RELOAD (Tests 11-12)
# ===========================================================================


class TestDigestIsolationAndReload:
    def test_11_cross_user_and_cross_tenant_digest_isolation(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]

        # Group belonging to User B
        ev_b, g_b = _make_event_and_group("e_other", "g_other", user_id="user_bob", tenant_id="tenant_1")
        event_repo.create(ev_b)
        group_repo.create(g_b)

        # User A requests digest with passed groups containing User B's group
        digest_a = svc.prepare_daily_digest(user_id="user_alice", tenant_id="tenant_1", groups=[g_b])
        # Invariant: User B's group must be isolated out
        assert digest_a.group_count == 0
        assert "g_other" not in digest_a.group_ids

    def test_12_digest_and_group_references_remain_valid_after_reload(self, digest_env):
        svc = digest_env["svc"]
        event_repo = digest_env["event_repo"]
        group_repo = digest_env["group_repo"]
        digests_dir = digest_env["digests_dir"]

        ev, grp = _make_event_and_group("e_rel", "g_rel")
        event_repo.create(ev)
        group_repo.create(grp)

        digest = svc.prepare_daily_digest(user_id="user_1", tenant_id="tenant_1", groups=[grp], save=True)

        # Reload digest from disk
        reloaded_svc = AlertDigestService(
            alert_group_repo=group_repo,
            alert_event_repo=event_repo,
            digests_dir=digests_dir,
        )
        loaded = reloaded_svc.get_digest(digest.digest_id, tenant_id="tenant_1", user_id="user_1")
        assert loaded is not None
        assert loaded.digest_id == digest.digest_id
        assert loaded.group_ids == ["g_rel"]


# ===========================================================================
# 5. CRITICAL FROZEN BASELINE (Tests 13-17)
# ===========================================================================


class TestCriticalFrozenBaseline:
    def test_13_central_47_companies_unchanged(self):
        comp_repo = CompanyRepository()
        all_comps = comp_repo.get_all()
        quant_comps = [c for c in all_comps if c.isin in CENTRAL_47_ISINS]
        assert len(quant_comps) == 47

    def test_14_central_940_pairs_unchanged(self):
        bill_repo = BillRepository()
        prod_central_bills = [
            b for b in bill_repo.get_all()
            if b.bill_id not in ("key-issues-and-analysis", "service-bill")
        ]
        assert len(prod_central_bills) == 20
        assert len(prod_central_bills) * len(CENTRAL_47_ISINS) == 940

    def test_15_central_4700_predictions_unchanged(self):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700

    def test_16_state_86_exposures_unchanged(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        assert len(state_exps) == 86

    def test_17_state_predictions_remain_zero(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        for e in state_exps:
            assert not hasattr(e, "predicted_car")
            assert not hasattr(e, "expected_return")
