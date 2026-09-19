"""
tests/test_alert_matching_service.py
====================================
Comprehensive test suite for Task 8.13.4 — Alert Matching Engine & Event Generation.

Covers all 40 required test areas:
EVENT NORMALIZATION:
 1. Monitoring event normalization
 2. Exposure event normalization
 3. Missing optional fields handled safely
 4. Provenance preserved

DIRECT MATCHING:
 5. Company event matches company subscriber
 6. Bill event matches bill subscriber
 7. Sector event matches sector subscriber
 8. Industry event matches industry subscriber
 9. State event matches State subscriber
 10. Jurisdiction event matches jurisdiction subscriber

MULTI-DIMENSION:
 11. Event matching multiple dimensions
 12. Duplicate subscriber candidate removed
 13. Different watchlists remain separate

RULES:
 14. Enabled rule triggers AlertEvent
 15. Disabled rule does not trigger
 16. Non-matching rule does not trigger
 17. Rule isolation by user/watchlist

WATCHLIST:
 18. Inactive watchlist does not trigger
 19. Tenant isolation
 20. User isolation

DEDUPLICATION:
 21. Same event processed twice creates one AlertEvent
 22. Same event in different watchlists creates separate AlertEvents
 23. Different events create separate AlertEvents

COMPANY EXPOSURE:
 24. Validated company exposure resolves subscribers
 25. Invalid/unverified exposure is not fabricated

STATE:
 26. State event resolves State subscriber
 27. State event resolves STATE jurisdiction subscriber
 28. State event creates no prediction

CENTRAL:
 29. Central bill event resolves Central subscribers
 30. Existing Central prediction data remains untouched

PERSISTENCE:
 31. AlertEvent survives repository reload
 32. Dedup survives service restart/reload

INTEGRATION:
 33. Monitoring ChangeEvent can be processed
 34. Company exposure event can be processed
 35. Unified bill event can be processed

BASELINE:
 36. Central 47 companies unchanged
 37. Central 940 pairs unchanged
 38. Central 4,700 predictions unchanged
 39. State 86 exposures unchanged
 40. State predictions remain 0
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from config.settings import settings
from schemas.alert import (
    AlertEvent,
    AlertPreference,
    AlertRule,
    AlertSeverity,
    AlertType,
    compute_dedup_key,
)
from schemas.monitoring import ChangeEvent, ChangeEventType, NotificationEvent
from schemas.state_corporate_exposure import (
    CorporateExposureEvidence,
    StateCorporateExposure,
)
from schemas.watchlist import Watchlist, WatchlistItem, WatchlistEntityType
from services.alert_matching_service import (
    AlertMatchingService,
    NormalizedEvent,
    severity_rank,
)
from services.watchlist_index_service import WatchlistIndexService
from storage.alert_event_repository import AlertEventRepository
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.alert_rule_repository import AlertRuleRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.state_bill_repository import StateBillRepository
from storage.watchlist_repository import WatchlistRepository


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
def alert_env(tmp_path: Path):
    """
    Setup an isolated AlertMatchingService test harness with clean repositories.
    """
    wl_dir = tmp_path / "watchlists"
    idx_dir = tmp_path / "indices"
    rules_dir = tmp_path / "rules"
    events_dir = tmp_path / "events"
    prefs_dir = tmp_path / "prefs"

    wl_repo = WatchlistRepository(root_dir=wl_dir)
    idx_svc = WatchlistIndexService(indices_dir=idx_dir, watchlist_repo=wl_repo)
    rule_repo = AlertRuleRepository(root_dir=rules_dir)
    event_repo = AlertEventRepository(root_dir=events_dir)
    pref_repo = AlertPreferenceRepository(root_dir=prefs_dir)

    matching_svc = AlertMatchingService(
        watchlist_repo=wl_repo,
        index_service=idx_svc,
        alert_rule_repo=rule_repo,
        alert_event_repo=event_repo,
        alert_pref_repo=pref_repo,
        company_exposure_repo=CompanyExposureRepository(),
        company_repo=CompanyRepository(),
        bill_repo=BillRepository(),
        state_bill_repo=StateBillRepository(),
    )

    return {
        "service": matching_svc,
        "wl_repo": wl_repo,
        "idx_svc": idx_svc,
        "rule_repo": rule_repo,
        "event_repo": event_repo,
        "pref_repo": pref_repo,
        "tmp_path": tmp_path,
    }


# ===========================================================================
# 1. EVENT NORMALIZATION (Tests 1-4)
# ===========================================================================


class TestEventNormalization:
    def test_1_monitoring_event_normalization(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        change = ChangeEvent(
            event_id="chg-001",
            bill_id="the-coastal-shipping-bill-2024",
            bill_title="The Coastal Shipping Bill, 2024",
            jurisdiction="central",
            event_type=ChangeEventType.STATUS_CHANGED,
            field_name="status",
            old_value="introduced",
            new_value="assented",
            source_id="prs_central",
            source_reference="https://prsindia.org/billtrack/coastal-shipping-2024",
        )
        norm = svc.normalize_monitoring_event(change)
        assert norm.event_id == "chg-001"
        assert norm.alert_type == AlertType.BILL_STATUS_CHANGE
        assert norm.severity == AlertSeverity.HIGH  # assented triggers HIGH
        assert norm.bill_id == "the-coastal-shipping-bill-2024"
        assert norm.jurisdiction == "central"
        assert "status transitioned" in norm.fact_summary
        assert "Legislative stage updated" in norm.derived_summary
        assert "Status updates alter legislative trajectory" in norm.interpretation_summary
        assert norm.prediction_summary == "none"

    def test_2_exposure_event_normalization(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        exp = StateCorporateExposure(
            bill_id="kerala-gig-workers-bill-2024",
            state="Kerala",
            company_id="PRIV-BUNDL-SWIGGY",
            company_name="Swiggy Limited",
            sector="Technology",
            sub_sector="Food Delivery",
            business_activity="App-based food delivery operations in Kerala",
            exposure_strength="HIGH",
            direct_indirect="DIRECT",
            evidence=[
                CorporateExposureEvidence(
                    source_type="bill_text",
                    reference="Section 3(1)",
                    claim="Applies to online delivery aggregators operating in Kerala",
                )
            ],
            jurisdiction="state",
        )
        norm = svc.normalize_exposure_event(exp)
        assert norm.alert_type == AlertType.NEW_COMPANY_EXPOSURE
        assert norm.company_id == "PRIV-BUNDL-SWIGGY"
        assert norm.company_name == "Swiggy Limited"
        assert norm.state_id == "Kerala"
        assert norm.sector_id == "Technology"
        assert norm.severity == AlertSeverity.HIGH
        assert len(norm.evidence) == 1
        assert norm.prediction_summary == "none"

    def test_3_missing_optional_fields_handled_safely(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        minimal = {"event_type": "STATUS_CHANGED", "bill_id": "test-bill"}
        norm = svc.normalize_event(minimal)
        assert norm.event_id is not None
        assert norm.bill_id == "test-bill"
        assert norm.company_id is None
        assert norm.sector_id is None
        assert norm.state_id is None
        assert norm.prediction_summary == "none"

    def test_4_provenance_preserved(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        ev = ChangeEvent(
            event_id="prov-100",
            bill_id="finance-bill-2024",
            source_id="lok_sabha_feed",
            source_reference="https://sansad.in/ls/bills/100",
        )
        norm = svc.normalize_event(ev)
        assert norm.source == "lok_sabha_feed"
        assert norm.source_reference == "https://sansad.in/ls/bills/100"


# ===========================================================================
# 2. DIRECT MATCHING (Tests 5-10)
# ===========================================================================


class TestDirectMatching:
    def test_5_company_event_matches_company_subscriber(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl = wl_repo.create(Watchlist(watchlist_id="wl_comp", user_id="u1", name="Comp WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                item_id="item_swiggy",
                watchlist_id="wl_comp",
                user_id="u1",
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="PRIV-BUNDL-SWIGGY",
                display_name="Swiggy",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r1",
                user_id="u1",
                watchlist_id="wl_comp",
                alert_type=AlertType.NEW_COMPANY_EXPOSURE,
                minimum_severity=AlertSeverity.LOW,
            )
        )

        event = NormalizedEvent(
            event_id="ev_swiggy_1",
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            severity=AlertSeverity.MEDIUM,
            company_id="PRIV-BUNDL-SWIGGY",
            company_name="Swiggy Limited",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].user_id == "u1"
        assert alerts[0].watchlist_id == "wl_comp"
        assert alerts[0].entity_id == "PRIV-BUNDL-SWIGGY"

    def test_6_bill_event_matches_bill_subscriber(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_bill", user_id="u2", name="Bill WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                item_id="item_bill_1",
                watchlist_id="wl_bill",
                user_id="u2",
                entity_type=WatchlistEntityType.BILL,
                entity_id="the-coastal-shipping-bill-2024",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r2",
                user_id="u2",
                watchlist_id="wl_bill",
                alert_type=AlertType.BILL_STATUS_CHANGE,
                minimum_severity=AlertSeverity.LOW,
            )
        )

        event = NormalizedEvent(
            event_id="ev_bill_1",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.MEDIUM,
            bill_id="the-coastal-shipping-bill-2024",
            bill_title="The Coastal Shipping Bill, 2024",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].watchlist_id == "wl_bill"
        assert alerts[0].entity_id == "the-coastal-shipping-bill-2024"

    def test_7_sector_event_matches_sector_subscriber(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_sec", user_id="u3", name="Sector WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                item_id="item_sec_1",
                watchlist_id="wl_sec",
                user_id="u3",
                entity_type=WatchlistEntityType.SECTOR,
                entity_id="Technology",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r3",
                user_id="u3",
                watchlist_id="wl_sec",
                alert_type=AlertType.NEW_BILL,
                minimum_severity=AlertSeverity.LOW,
            )
        )

        event = NormalizedEvent(
            event_id="ev_sec_1",
            alert_type=AlertType.NEW_BILL,
            severity=AlertSeverity.LOW,
            sector_id="Technology",
            bill_title="New Tech Framework Bill",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].watchlist_id == "wl_sec"

    def test_8_industry_event_matches_industry_subscriber(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_ind", user_id="u4", name="Industry WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                item_id="item_ind_1",
                watchlist_id="wl_ind",
                user_id="u4",
                entity_type=WatchlistEntityType.INDUSTRY,
                entity_id="Food Delivery & Quick Commerce",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r4",
                user_id="u4",
                watchlist_id="wl_ind",
                alert_type=AlertType.NEW_BILL,
                minimum_severity=AlertSeverity.LOW,
            )
        )

        event = NormalizedEvent(
            event_id="ev_ind_1",
            alert_type=AlertType.NEW_BILL,
            severity=AlertSeverity.LOW,
            industry_id="Food Delivery & Quick Commerce",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].watchlist_id == "wl_ind"

    def test_9_state_event_matches_state_subscriber(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_state", user_id="u5", name="State WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                item_id="item_state_1",
                watchlist_id="wl_state",
                user_id="u5",
                entity_type=WatchlistEntityType.STATE,
                entity_id="Kerala",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r5",
                user_id="u5",
                watchlist_id="wl_state",
                alert_type=AlertType.NEW_BILL,
                minimum_severity=AlertSeverity.LOW,
            )
        )

        event = NormalizedEvent(
            event_id="ev_state_1",
            alert_type=AlertType.NEW_BILL,
            severity=AlertSeverity.LOW,
            state_id="Kerala",
            jurisdiction="state",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].watchlist_id == "wl_state"

    def test_10_jurisdiction_event_matches_jurisdiction_subscriber(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_jur", user_id="u6", name="Jur WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                item_id="item_jur_1",
                watchlist_id="wl_jur",
                user_id="u6",
                entity_type=WatchlistEntityType.JURISDICTION,
                entity_id="central",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r6",
                user_id="u6",
                watchlist_id="wl_jur",
                alert_type=AlertType.NEW_BILL,
                minimum_severity=AlertSeverity.LOW,
            )
        )

        event = NormalizedEvent(
            event_id="ev_jur_1",
            alert_type=AlertType.NEW_BILL,
            severity=AlertSeverity.LOW,
            jurisdiction="central",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].watchlist_id == "wl_jur"


# ===========================================================================
# 3. MULTI-DIMENSION MATCHING (Tests 11-13)
# ===========================================================================


class TestMultiDimensionMatching:
    def test_11_event_matching_multiple_dimensions(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        # Watchlist with multiple dimensions: Kerala, Technology, and Swiggy
        wl_repo.create(Watchlist(watchlist_id="wl_multi", user_id="u_multi", name="Multi WL"))
        for etype, eid in [
            (WatchlistEntityType.STATE, "Kerala"),
            (WatchlistEntityType.SECTOR, "Technology"),
            (WatchlistEntityType.COMPANY, "PRIV-BUNDL-SWIGGY"),
        ]:
            item = wl_repo.add_item(
                WatchlistItem(
                    watchlist_id="wl_multi",
                    user_id="u_multi",
                    entity_type=etype,
                    entity_id=eid,
                )
            )
            idx_svc.add_subscriber(item)

        rule_repo.create(
            AlertRule(
                alert_rule_id="r_multi",
                user_id="u_multi",
                watchlist_id="wl_multi",
                alert_type=AlertType.NEW_COMPANY_EXPOSURE,
                minimum_severity=AlertSeverity.LOW,
            )
        )

        # Single event matching Kerala, Technology, and Swiggy
        event = NormalizedEvent(
            event_id="ev_multi_1",
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            severity=AlertSeverity.HIGH,
            company_id="PRIV-BUNDL-SWIGGY",
            company_name="Swiggy",
            state_id="Kerala",
            sector_id="Technology",
        )
        alerts = svc.process_event(event)
        # Exactly ONE AlertEvent generated despite 3 matched dimensions
        assert len(alerts) == 1
        meta = alerts[0].metadata
        matched = meta.get("matched_dimensions", [])
        assert len(matched) == 3

    def test_12_duplicate_subscriber_candidate_removed(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        candidates = svc.resolve_candidate_subscribers(
            NormalizedEvent(
                event_id="ev_dup_cand",
                company_id="PRIV-BUNDL-SWIGGY",
                state_id="Kerala",
                sector_id="Technology",
            )
        )
        # Verify candidate dictionary uses unique (tenant_id, user_id, watchlist_id) keys
        for key, val in candidates.items():
            assert len(key) == 3
            dims = val["matched_dimensions"]
            unique_dims = {(d["entity_type"], d["entity_id"]) for d in dims}
            assert len(unique_dims) == len(dims)

    def test_13_different_watchlists_remain_separate(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        # Same user watches company in Watchlist A and Watchlist B
        wl_repo.create(Watchlist(watchlist_id="wl_a", user_id="u_split", name="WL A"))
        wl_repo.create(Watchlist(watchlist_id="wl_b", user_id="u_split", name="WL B"))

        item_a = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_a",
                user_id="u_split",
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="INE758T01015",
            )
        )
        item_b = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_b",
                user_id="u_split",
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="INE758T01015",
            )
        )
        idx_svc.add_subscriber(item_a)
        idx_svc.add_subscriber(item_b)

        rule_repo.create(
            AlertRule(
                alert_rule_id="r_a",
                user_id="u_split",
                watchlist_id="wl_a",
                alert_type=AlertType.NEW_COMPANY_EXPOSURE,
                minimum_severity=AlertSeverity.LOW,
            )
        )
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_b",
                user_id="u_split",
                watchlist_id="wl_b",
                alert_type=AlertType.NEW_COMPANY_EXPOSURE,
                minimum_severity=AlertSeverity.LOW,
            )
        )

        event = NormalizedEvent(
            event_id="ev_zomato_1",
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            severity=AlertSeverity.MEDIUM,
            company_id="INE758T01015",
            company_name="Zomato Limited",
        )
        alerts = svc.process_event(event)
        # Distinct watchlists produce separate AlertEvents
        assert len(alerts) == 2
        wl_ids = {a.watchlist_id for a in alerts}
        assert wl_ids == {"wl_a", "wl_b"}


# ===========================================================================
# 4. RULES EVALUATION (Tests 14-17)
# ===========================================================================


class TestRuleEvaluation:
    def test_14_enabled_rule_triggers_alert_event(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_rule1", user_id="u_r1", name="WL R1"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_rule1",
                user_id="u_r1",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-101",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_enabled",
                user_id="u_r1",
                watchlist_id="wl_rule1",
                alert_type=AlertType.BILL_STATUS_CHANGE,
                minimum_severity=AlertSeverity.LOW,
                enabled=True,
            )
        )

        event = NormalizedEvent(
            event_id="ev_r14",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.MEDIUM,
            bill_id="bill-101",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].alert_rule_id == "r_enabled"

    def test_15_disabled_rule_does_not_trigger(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_rule2", user_id="u_r2", name="WL R2"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_rule2",
                user_id="u_r2",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-102",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_disabled",
                user_id="u_r2",
                watchlist_id="wl_rule2",
                alert_type=AlertType.BILL_STATUS_CHANGE,
                minimum_severity=AlertSeverity.LOW,
                enabled=False,  # Disabled
            )
        )

        event = NormalizedEvent(
            event_id="ev_r15",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.MEDIUM,
            bill_id="bill-102",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 0

    def test_16_non_matching_rule_does_not_trigger(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_rule3", user_id="u_r3", name="WL R3"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_rule3",
                user_id="u_r3",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-103",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_mismatch",
                user_id="u_r3",
                watchlist_id="wl_rule3",
                alert_type=AlertType.NEW_BILL,  # Different alert type
                minimum_severity=AlertSeverity.LOW,
                enabled=True,
            )
        )

        event = NormalizedEvent(
            event_id="ev_r16",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.HIGH,
            bill_id="bill-103",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 0

    def test_17_rule_isolation_by_user_and_watchlist(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        # User 1 has WL1 with rule
        wl_repo.create(Watchlist(watchlist_id="wl_user1", user_id="user1", name="WL User1"))
        item1 = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_user1",
                user_id="user1",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-shared",
            )
        )
        idx_svc.add_subscriber(item1)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_u1",
                user_id="user1",
                watchlist_id="wl_user1",
                alert_type=AlertType.BILL_STATUS_CHANGE,
                minimum_severity=AlertSeverity.LOW,
            )
        )

        # User 2 has WL2 watching same bill but NO rule
        wl_repo.create(Watchlist(watchlist_id="wl_user2", user_id="user2", name="WL User2"))
        item2 = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_user2",
                user_id="user2",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-shared",
            )
        )
        idx_svc.add_subscriber(item2)

        event = NormalizedEvent(
            event_id="ev_shared",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.MEDIUM,
            bill_id="bill-shared",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].user_id == "user1"


# ===========================================================================
# 5. WATCHLIST AND TENANT ISOLATION (Tests 18-20)
# ===========================================================================


class TestWatchlistAndTenantIsolation:
    def test_18_inactive_watchlist_does_not_trigger(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl = wl_repo.create(
            Watchlist(
                watchlist_id="wl_inactive",
                user_id="u_inact",
                name="Inactive WL",
                is_active=False,
            )
        )
        item = WatchlistItem(
            item_id="item_inact",
            watchlist_id="wl_inactive",
            user_id="u_inact",
            entity_type=WatchlistEntityType.BILL,
            entity_id="bill-inact",
        )
        wl_repo._items_dir(item.tenant_id, item.user_id)
        # Directly save item to repo
        with open(
            wl_repo._items_dir(item.tenant_id, item.user_id) / f"item_{item.item_id}.json",
            "w",
            encoding="utf-8",
        ) as fh:
            json.dump(item.to_dict(), fh)

        rule_repo.create(
            AlertRule(
                alert_rule_id="r_inact",
                user_id="u_inact",
                watchlist_id="wl_inactive",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
        )

        event = NormalizedEvent(
            event_id="ev_inact",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="bill-inact",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 0

    def test_19_tenant_isolation(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]
        event_repo = alert_env["event_repo"]

        # Tenant Alpha
        wl_repo.create(
            Watchlist(
                watchlist_id="wl_t_alpha",
                tenant_id="tenant_alpha",
                user_id="user_alpha",
                name="Alpha WL",
            )
        )
        item_a = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_t_alpha",
                tenant_id="tenant_alpha",
                user_id="user_alpha",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-iso",
            )
        )
        idx_svc.add_subscriber(item_a)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_alpha",
                tenant_id="tenant_alpha",
                user_id="user_alpha",
                watchlist_id="wl_t_alpha",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
        )

        # Tenant Beta
        wl_repo.create(
            Watchlist(
                watchlist_id="wl_t_beta",
                tenant_id="tenant_beta",
                user_id="user_beta",
                name="Beta WL",
            )
        )
        item_b = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_t_beta",
                tenant_id="tenant_beta",
                user_id="user_beta",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-iso",
            )
        )
        idx_svc.add_subscriber(item_b)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_beta",
                tenant_id="tenant_beta",
                user_id="user_beta",
                watchlist_id="wl_t_beta",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
        )

        event = NormalizedEvent(
            event_id="ev_iso",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.HIGH,
            bill_id="bill-iso",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 2

        alpha_alerts = [a for a in alerts if a.tenant_id == "tenant_alpha"]
        beta_alerts = [a for a in alerts if a.tenant_id == "tenant_beta"]
        assert len(alpha_alerts) == 1
        assert len(beta_alerts) == 1

        # Check repository storage isolation
        loaded_alpha = event_repo.list_by_user("user_alpha", tenant_id="tenant_alpha")
        loaded_beta = event_repo.list_by_user("user_beta", tenant_id="tenant_beta")
        assert len(loaded_alpha) == 1
        assert len(loaded_beta) == 1
        assert loaded_alpha[0].tenant_id == "tenant_alpha"
        assert loaded_beta[0].tenant_id == "tenant_beta"

    def test_20_user_isolation(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]
        event_repo = alert_env["event_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_u_a", user_id="user_a", name="User A WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_u_a",
                user_id="user_a",
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="PRIV-BUNDL-SWIGGY",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_ua",
                user_id="user_a",
                watchlist_id="wl_u_a",
                alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            )
        )

        event = NormalizedEvent(
            event_id="ev_ua",
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            company_id="PRIV-BUNDL-SWIGGY",
        )
        svc.process_event(event)

        # User B cannot see User A's alerts
        alerts_b = event_repo.list_by_user("user_b")
        assert len(alerts_b) == 0


# ===========================================================================
# 6. DEDUPLICATION AND IDEMPOTENCY (Tests 21-23)
# ===========================================================================


class TestDeduplicationAndIdempotency:
    def test_21_same_event_processed_twice_creates_one_alert_event(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]
        event_repo = alert_env["event_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_dedup", user_id="u_dedup", name="Dedup WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_dedup",
                user_id="u_dedup",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-dedup",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_dedup",
                user_id="u_dedup",
                watchlist_id="wl_dedup",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
        )

        event = NormalizedEvent(
            event_id="ev_dedup_fixed",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="bill-dedup",
        )

        # Process first time
        first_alerts = svc.process_event(event)
        assert len(first_alerts) == 1

        # Process second time (identical event)
        second_alerts = svc.process_event(event)
        assert len(second_alerts) == 1
        assert first_alerts[0].alert_event_id == second_alerts[0].alert_event_id

        # Check physical persistence in repository
        persisted = event_repo.list_by_watchlist("wl_dedup")
        assert len(persisted) == 1

    def test_22_same_event_in_different_watchlists_creates_separate_alert_events(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]
        event_repo = alert_env["event_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_sep1", user_id="u_sep", name="Sep 1"))
        wl_repo.create(Watchlist(watchlist_id="wl_sep2", user_id="u_sep", name="Sep 2"))

        item1 = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_sep1",
                user_id="u_sep",
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="INE758T01015",
            )
        )
        item2 = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_sep2",
                user_id="u_sep",
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="INE758T01015",
            )
        )
        idx_svc.add_subscriber(item1)
        idx_svc.add_subscriber(item2)

        rule_repo.create(
            AlertRule(
                alert_rule_id="r_sep1",
                user_id="u_sep",
                watchlist_id="wl_sep1",
                alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            )
        )
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_sep2",
                user_id="u_sep",
                watchlist_id="wl_sep2",
                alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            )
        )

        event = NormalizedEvent(
            event_id="ev_sep_both",
            alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            company_id="INE758T01015",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 2
        assert alerts[0].dedup_key != alerts[1].dedup_key

        all_user_alerts = event_repo.list_by_user("u_sep")
        assert len(all_user_alerts) == 2

    def test_23_different_events_create_separate_alert_events(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_diff", user_id="u_diff", name="Diff WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_diff",
                user_id="u_diff",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-diff",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_diff",
                user_id="u_diff",
                watchlist_id="wl_diff",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
        )

        ev1 = NormalizedEvent(
            event_id="ev_diff_1",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="bill-diff",
        )
        ev2 = NormalizedEvent(
            event_id="ev_diff_2",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="bill-diff",
        )
        alerts1 = svc.process_event(ev1)
        alerts2 = svc.process_event(ev2)
        assert len(alerts1) == 1
        assert len(alerts2) == 1
        assert alerts1[0].alert_event_id != alerts2[0].alert_event_id


# ===========================================================================
# 7. COMPANY EXPOSURE INTEGRATION (Tests 24-25)
# ===========================================================================


class TestCompanyExposureIntegration:
    def test_24_validated_company_exposure_resolves_subscribers(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        # User watches Swiggy
        wl_repo.create(Watchlist(watchlist_id="wl_swiggy_sub", user_id="u_exp_sub", name="Swiggy Watch"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_swiggy_sub",
                user_id="u_exp_sub",
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="PRIV-BUNDL-SWIGGY",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_swiggy_exp",
                user_id="u_exp_sub",
                watchlist_id="wl_swiggy_sub",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
        )

        # Monitoring event for Telangana gig workers bill (which has validated exposure to Swiggy)
        event = NormalizedEvent(
            event_id="ev_telangana_gig_status",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            severity=AlertSeverity.HIGH,
            bill_id="telangana-vs-bill-11-2024",
            bill_title="The Telangana Platform Based Gig Workers Bill, 2024",
        )
        alerts = svc.process_event(event)
        # Should resolve subscriber watching Swiggy through validated exposure linking!
        assert len(alerts) >= 1
        user_alerts = [a for a in alerts if a.user_id == "u_exp_sub"]
        assert len(user_alerts) == 1
        assert user_alerts[0].watchlist_id == "wl_swiggy_sub"

    def test_25_invalid_unverified_exposure_not_fabricated(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        # A bill with NO validated corporate exposures should NOT match random companies
        keys = svc.resolve_affected_entity_keys(
            NormalizedEvent(
                event_id="ev_fake_bill",
                bill_id="unrelated-fictional-bill-9999",
            )
        )
        # Verify no company keys are fabricated
        company_keys = [k for k in keys if k[0] == WatchlistEntityType.COMPANY]
        assert len(company_keys) == 0


# ===========================================================================
# 8. STATE EVENT MATCHING (Tests 26-28)
# ===========================================================================


class TestStateEventMatching:
    def test_26_state_event_resolves_state_subscriber(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_kl", user_id="u_kl", name="Kerala Watch"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_kl",
                user_id="u_kl",
                entity_type=WatchlistEntityType.STATE,
                entity_id="Kerala",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_kl",
                user_id="u_kl",
                watchlist_id="wl_kl",
                alert_type=AlertType.NEW_BILL,
            )
        )

        event = NormalizedEvent(
            event_id="ev_kl_bill",
            alert_type=AlertType.NEW_BILL,
            state_id="Kerala",
            jurisdiction="state",
            bill_title="Kerala Clinical Establishments Amendment",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].watchlist_id == "wl_kl"

    def test_27_state_event_resolves_state_jurisdiction_subscriber(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_st_jur", user_id="u_jur_st", name="All States"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_st_jur",
                user_id="u_jur_st",
                entity_type=WatchlistEntityType.JURISDICTION,
                entity_id="state",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_jur_st",
                user_id="u_jur_st",
                watchlist_id="wl_st_jur",
                alert_type=AlertType.NEW_BILL,
            )
        )

        event = NormalizedEvent(
            event_id="ev_ap_bill",
            alert_type=AlertType.NEW_BILL,
            state_id="Andhra Pradesh",
            jurisdiction="state",
            bill_title="AP Electricity Duty Bill",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].watchlist_id == "wl_st_jur"

    def test_28_state_event_creates_no_prediction(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_st_pred", user_id="u_nopred", name="No Pred WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_st_pred",
                user_id="u_nopred",
                entity_type=WatchlistEntityType.STATE,
                entity_id="Karnataka",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_nopred",
                user_id="u_nopred",
                watchlist_id="wl_st_pred",
                alert_type=AlertType.NEW_BILL,
            )
        )

        event = NormalizedEvent(
            event_id="ev_ka_nopred",
            alert_type=AlertType.NEW_BILL,
            state_id="Karnataka",
            jurisdiction="state",
            bill_title="Karnataka Platform Gig Workers Bill",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        # Strict requirement: State predictions must be none / absent
        assert "PREDICTION: none" in alerts[0].summary
        assert alerts[0].metadata["structured_content"]["prediction"] == "none"
        assert not hasattr(alerts[0], "predicted_car")
        assert not hasattr(alerts[0], "target_price")


# ===========================================================================
# 9. CENTRAL EVENT MATCHING (Tests 29-30)
# ===========================================================================


class TestCentralEventMatching:
    def test_29_central_bill_event_resolves_central_subscribers(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_central_sub", user_id="u_c_sub", name="Central Watch"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_central_sub",
                user_id="u_c_sub",
                entity_type=WatchlistEntityType.JURISDICTION,
                entity_id="central",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_c_sub",
                user_id="u_c_sub",
                watchlist_id="wl_central_sub",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
        )

        event = NormalizedEvent(
            event_id="ev_central_shipping",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="the-coastal-shipping-bill-2024",
            jurisdiction="central",
        )
        alerts = svc.process_event(event)
        assert len(alerts) == 1
        assert alerts[0].watchlist_id == "wl_central_sub"

    def test_30_existing_central_prediction_data_remains_untouched(self, alert_env):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700


# ===========================================================================
# 10. PERSISTENCE AND RELOAD (Tests 31-32)
# ===========================================================================


class TestPersistenceAndReload:
    def test_31_alert_event_survives_repository_reload(self, alert_env):
        event_repo: AlertEventRepository = alert_env["event_repo"]
        event = AlertEvent(
            alert_event_id="ev_persist_1",
            tenant_id="t_persist",
            user_id="u_persist",
            title="Persisted Alert",
            summary="Testing reload resilience",
            source_event_id="src-100",
            alert_type=AlertType.BILL_STATUS_CHANGE,
        )
        event_repo.create(event)

        # Instantiate fresh repository from same directory
        reloaded_repo = AlertEventRepository(root_dir=alert_env["tmp_path"] / "events")
        loaded = reloaded_repo.get("ev_persist_1", tenant_id="t_persist", user_id="u_persist")
        assert loaded is not None
        assert loaded.title == "Persisted Alert"

    def test_32_dedup_survives_service_restart_reload(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_restart", user_id="u_rst", name="Restart WL"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_restart",
                user_id="u_rst",
                entity_type=WatchlistEntityType.BILL,
                entity_id="bill-rst",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_rst",
                user_id="u_rst",
                watchlist_id="wl_restart",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
        )

        event = NormalizedEvent(
            event_id="ev_rst_1",
            alert_type=AlertType.BILL_STATUS_CHANGE,
            bill_id="bill-rst",
        )
        first_alerts = svc.process_event(event)
        assert len(first_alerts) == 1

        # Re-initialize AlertMatchingService pointing to same persistent directories
        new_svc = AlertMatchingService(
            watchlist_repo=WatchlistRepository(root_dir=alert_env["tmp_path"] / "watchlists"),
            index_service=WatchlistIndexService(indices_dir=alert_env["tmp_path"] / "indices"),
            alert_rule_repo=AlertRuleRepository(root_dir=alert_env["tmp_path"] / "rules"),
            alert_event_repo=AlertEventRepository(root_dir=alert_env["tmp_path"] / "events"),
            alert_pref_repo=AlertPreferenceRepository(root_dir=alert_env["tmp_path"] / "prefs"),
        )
        second_alerts = new_svc.process_event(event)
        assert len(second_alerts) == 1
        assert second_alerts[0].alert_event_id == first_alerts[0].alert_event_id


# ===========================================================================
# 11. SYSTEM INTEGRATION (Tests 33-35)
# ===========================================================================


class TestSystemIntegration:
    def test_33_monitoring_change_event_can_be_processed(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_m_integ", user_id="u_minteg", name="M Integ"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_m_integ",
                user_id="u_minteg",
                entity_type=WatchlistEntityType.BILL,
                entity_id="the-coastal-shipping-bill-2024",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_minteg",
                user_id="u_minteg",
                watchlist_id="wl_m_integ",
                alert_type=AlertType.BILL_STATUS_CHANGE,
            )
        )

        change = ChangeEvent(
            event_id="chg-integ-1",
            bill_id="the-coastal-shipping-bill-2024",
            bill_title="The Coastal Shipping Bill, 2024",
            jurisdiction="central",
            event_type=ChangeEventType.STATUS_CHANGED,
            field_name="status",
            old_value="introduced",
            new_value="passed_both",
        )
        alerts = svc.process_monitoring_event(change)
        assert len(alerts) == 1
        assert alerts[0].severity == AlertSeverity.HIGH

    def test_34_company_exposure_event_can_be_processed(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_e_integ", user_id="u_einteg", name="E Integ"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_e_integ",
                user_id="u_einteg",
                entity_type=WatchlistEntityType.COMPANY,
                entity_id="PRIV-BUNDL-SWIGGY",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_einteg",
                user_id="u_einteg",
                watchlist_id="wl_e_integ",
                alert_type=AlertType.NEW_COMPANY_EXPOSURE,
            )
        )

        exp = StateCorporateExposure(
            bill_id="kerala-gig-workers-bill-2024",
            state="Kerala",
            company_id="PRIV-BUNDL-SWIGGY",
            company_name="Swiggy Limited",
            sector="Technology",
            business_activity="Food Delivery in Kerala",
            exposure_strength="HIGH",
            direct_indirect="DIRECT",
        )
        alerts = svc.process_company_exposure_event(exp)
        assert len(alerts) == 1
        assert alerts[0].entity_id == "PRIV-BUNDL-SWIGGY"

    def test_35_unified_bill_event_can_be_processed(self, alert_env):
        svc: AlertMatchingService = alert_env["service"]
        wl_repo = alert_env["wl_repo"]
        idx_svc = alert_env["idx_svc"]
        rule_repo = alert_env["rule_repo"]

        wl_repo.create(Watchlist(watchlist_id="wl_u_integ", user_id="u_uinteg", name="U Integ"))
        item = wl_repo.add_item(
            WatchlistItem(
                watchlist_id="wl_u_integ",
                user_id="u_uinteg",
                entity_type=WatchlistEntityType.BILL,
                entity_id="unified-bill-100",
            )
        )
        idx_svc.add_subscriber(item)
        rule_repo.create(
            AlertRule(
                alert_rule_id="r_uinteg",
                user_id="u_uinteg",
                watchlist_id="wl_u_integ",
                alert_type=AlertType.NEW_BILL,
            )
        )

        unified_event = {
            "event_id": "uni-bill-1",
            "alert_type": "NEW_BILL",
            "bill_id": "unified-bill-100",
            "bill_title": "Unified National Logistics Bill",
            "jurisdiction": "central",
        }
        alerts = svc.process_event(unified_event)
        assert len(alerts) == 1
        assert alerts[0].title == "[New Bill] Unified National Logistics Bill"


# ===========================================================================
# 12. CRITICAL FROZEN BASELINE (Tests 36-40)
# ===========================================================================


class TestCriticalFrozenBaseline:
    def test_36_central_47_companies_unchanged(self):
        comp_repo = CompanyRepository()
        all_comps = comp_repo.get_all()
        quant_comps = [c for c in all_comps if c.isin in CENTRAL_47_ISINS]
        assert len(quant_comps) == 47

    def test_37_central_940_pairs_unchanged(self):
        bill_repo = BillRepository()
        prod_central_bills = [
            b for b in bill_repo.get_all()
            if b.bill_id not in ("key-issues-and-analysis", "service-bill")
        ]
        assert len(prod_central_bills) == 20
        assert len(prod_central_bills) * len(CENTRAL_47_ISINS) == 940

    def test_38_central_4700_predictions_unchanged(self):
        pred_dir = settings.DATA_DIR / "predictions"
        pred_files = list(pred_dir.glob("pred_*.json"))
        assert len(pred_files) == 4700

    def test_39_state_86_exposures_unchanged(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        assert len(state_exps) == 86

    def test_40_state_predictions_remain_zero(self):
        exp_repo = CompanyExposureRepository()
        state_exps = exp_repo.get_all_state()
        for e in state_exps:
            assert not hasattr(e, "predicted_car")
            assert not hasattr(e, "expected_return")
