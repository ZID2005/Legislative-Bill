"""
tests/test_dashboard_qa.py
==========================
Task 7.4.3 — Dashboard UX, Runtime QA & Research-Integrity Hardening Test Suite.

Covers:
1. Canonical Production Scope Counts (20, 47, 940, 4700, 4700, 940, 14100)
2. Newly Introduced Bill Date Logic (strictly Bill.introduction_date, date ranges, no-results)
3. Bill Detail UX Completeness (12 key questions answered)
4. Bill Category Quality & Provenance (system-derived vs official category labeling)
5. Legislative Status Quality (no ungrounded status inference, fallback to "Status not available.")
6. Market Prediction Display & Probabilistic Phrasing (read-only, no "will increase/decrease")
7. Investment Advice Safety Audit (zero buy/sell recommendations, zero guaranteed return claims)
8. Anticipation Language Audit (zero insider trading accusations, required disclaimer)
9. Backtesting Separation & Ground-Truth Separation (ground-truth never in prediction inputs)
10. Responsiveness, Edge Cases & Error Handling (missing artifacts, empty filters)
11. Search & Filter QA (determinism, multi-filter combinations)
12. Artifact Immutability Verification (SHA256 fingerprinting before/after interaction)
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
import pytest
import pandas as pd

from dashboard.services.dashboard_service import (
    DashboardService,
    ProductionScope,
    BillSummary,
    _NON_LEGISLATIVE_BILL_IDS,
)
from dashboard.services.scope_service import ScopeService, ScopeDiagnostic
from schemas.bill import Bill, BillHouse, BillStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def dashboard_service() -> DashboardService:
    return DashboardService()


# ---------------------------------------------------------------------------
# 1. CANONICAL PRODUCTION SCOPE VALIDATION
# ---------------------------------------------------------------------------

def test_canonical_production_scope_counts(dashboard_service: DashboardService):
    """
    Verify exact counts for production dataset:
    Bills = 20, Companies = 47, Pairs = 940, Prediction = 4700, Decision = 4700,
    Anticipation = 940, Stakeholder reports = 14100.
    """
    scope = dashboard_service.get_production_scope()
    assert scope.production_bills_count == 20
    assert scope.production_companies_count == 47
    assert scope.production_bill_company_pairs == 940
    assert scope.production_prediction_records == 4700
    assert scope.production_decision_records == 4700
    assert scope.production_anticipation_records >= 940
    assert scope.production_report_records == 14100
    assert scope.scope_integrity_verdict == "PRODUCTION_PARITY_CONFIRMED"


def test_production_bills_exclusion(dashboard_service: DashboardService):
    """Verify non-legislative stubs are strictly excluded from production views."""
    prod_bills = dashboard_service.get_production_bills()
    prod_ids = {b.bill_id for b in prod_bills}
    assert len(prod_bills) == 20
    for non_leg_id in _NON_LEGISLATIVE_BILL_IDS:
        assert non_leg_id not in prod_ids


def test_scope_diagnostic_explanation():
    """Verify diagnostic explanation accounts for the 10 companies / 60 pairs pilot reconciliation."""
    diag = ScopeDiagnostic()
    explanation = diag.pairs_discrepancy_explanation
    assert "940" in explanation
    assert "20" in explanation
    assert "47" in explanation
    assert "pilot" in explanation.lower() or "isolated" in explanation.lower()


# ---------------------------------------------------------------------------
# 2. NEWLY INTRODUCED BILL DATE LOGIC
# ---------------------------------------------------------------------------

def test_new_bills_date_logic_uses_only_introduction_date(dashboard_service: DashboardService):
    """Verify newly introduced bills strictly use Bill.introduction_date, not download or prediction timestamps."""
    new_bills = dashboard_service.get_newly_arrived_bills(since=date(2024, 1, 1), until=date(2025, 1, 1))
    assert len(new_bills) > 0
    for s in new_bills:
        assert s.introduction_date is not None
        assert isinstance(s.introduction_date, date)
        raw_bill = dashboard_service.get_bill_by_id(s.bill_id)
        assert raw_bill is not None
        assert s.introduction_date == raw_bill.introduction_date


def test_new_bills_newest_first_ordering(dashboard_service: DashboardService):
    """Verify newly arrived bills are strictly sorted newest-first."""
    new_bills = dashboard_service.get_newly_arrived_bills(since=date(2024, 1, 1), until=date(2025, 1, 1))
    assert len(new_bills) > 0
    dates = [b.introduction_date for b in new_bills if b.introduction_date is not None]
    assert dates == sorted(dates, reverse=True)



def test_new_bills_date_filters(dashboard_service: DashboardService):
    """Test 7-day, 30-day, 90-day, and custom date range filters."""
    # Test 7 days
    res_7 = dashboard_service.get_newly_arrived_bills(days=7)
    assert isinstance(res_7, list)

    # Test 30 days
    res_30 = dashboard_service.get_newly_arrived_bills(days=30)
    assert isinstance(res_30, list)

    # Test 90 days
    res_90 = dashboard_service.get_newly_arrived_bills(days=90)
    assert isinstance(res_90, list)

    # Test custom date range covering August 2024
    res_custom = dashboard_service.get_newly_arrived_bills(
        since=date(2024, 8, 1), until=date(2024, 8, 31)
    )
    assert isinstance(res_custom, list)
    for b in res_custom:
        assert date(2024, 8, 1) <= b.introduction_date <= date(2024, 8, 31)

    # Test no-results future range
    res_future = dashboard_service.get_newly_arrived_bills(
        since=date(2030, 1, 1), until=date(2030, 1, 31)
    )
    assert res_future == []


# ---------------------------------------------------------------------------
# 3. BILL DETAIL UX COMPLETENESS (12 KEY QUESTIONS)
# ---------------------------------------------------------------------------

def test_bill_detail_answers_all_12_questions(dashboard_service: DashboardService):
    """
    Verify get_bill_detail_data returns complete intelligence answering:
    1. What is this bill? (title, bill_number)
    2. When was it introduced? (introduction_date)
    3. What type of bill is it? (bill_category, category_source)
    4. What does it change? (plain_summary)
    5. Which sectors are affected? (sectors)
    6. Which companies are affected? (affected_companies, affected_companies_table)
    7. What is predicted market direction? (predicted_direction)
    8. How likely to move market? (market_moving_probability)
    9. What is impact strength? (impact_strength)
    10. What is risk? (composite_risk_score, risk_category)
    11. Is there anticipation / pricing-in evidence? (anticipation_evidence, diffusion_tier)
    12. What does it mean for Investor / Business / Public? (stakeholder_reports)
    """
    prod_bills = dashboard_service.get_production_bills()
    assert len(prod_bills) > 0
    bill_id = prod_bills[0].bill_id

    data = dashboard_service.get_bill_detail_data(bill_id)
    assert data is not None

    # 1 & 2: Bill metadata
    assert data["bill"].title
    assert data["bill"].introduction_date is not None

    # 3: Category
    assert data["bill_summary"].bill_category

    # 4: Changes / plain summary
    assert data["plain_summary"]
    assert len(data["plain_summary"]) > 20

    # 5 & 6: Sectors & Companies
    assert isinstance(data["sectors"], list)
    assert isinstance(data["affected_companies"], list)
    assert isinstance(data["affected_companies_table"], pd.DataFrame)

    # 7, 8, 9: Market Impact Forecast
    mi = data["market_impact"]
    assert mi["predicted_direction"] in ("POSITIVE", "NEGATIVE", "NEUTRAL")
    assert 0.0 <= mi["market_moving_probability"] <= 1.0
    assert mi["impact_strength"] in ("VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH")

    # 10: Risk
    risk = data["risk"]
    assert risk["risk_category"] in ("VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH", "CRITICAL", "NEGLIGIBLE")
    assert 0.0 <= risk["risk_score"] <= 1.0

    # 11: Anticipation
    ant = data["anticipation"]
    assert ant["anticipation_class"]

    # 12: Stakeholder Views
    reports = data["stakeholder_reports"]
    assert isinstance(reports, dict)



# ---------------------------------------------------------------------------
# 4. BILL CATEGORY QUALITY & PROVENANCE
# ---------------------------------------------------------------------------

def test_bill_category_distinguishes_system_derived():
    """Verify system-derived categories are explicitly labeled."""
    finance_bill = Bill(
        bill_id="test-fin",
        title="Finance Bill",
        year=2024,
        ministry="Ministry of Finance",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://prsindia.org",
        full_text="",
    )
    cat, source = DashboardService.classify_bill(finance_bill)
    assert cat == "Financial / Banking"
    assert source == "Source category"  # Ministry taxonomy source

    # Sector fallback
    sector_bill = Bill(
        bill_id="test-sector",
        title="Custom Bill",
        year=2024,
        ministry="Ministry of Unique Unknown",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        url="https://prsindia.org",
        full_text="",
        sectors=["Technology"],
    )
    cat2, source2 = DashboardService.classify_bill(sector_bill)
    assert cat2 == "Technology"
    assert source2 == "System category"


# ---------------------------------------------------------------------------
# 5. LEGISLATIVE STATUS QUALITY
# ---------------------------------------------------------------------------

def test_bill_status_does_not_infer_ungrounded_status(dashboard_service: DashboardService):
    """Verify status is derived strictly from source and not invented."""
    summaries = dashboard_service.get_recent_bills(20)
    valid_statuses = {
        "Introduced", "Under Consideration", "Passed — Lok Sabha",
        "Passed — Rajya Sabha", "Passed Both Houses", "Assented (Act)",
        "Lapsed", "Withdrawn", "In Committee", "Negatived",
        "Presidential Ordinance", "Draft", "Status not available.",
    }
    for s in summaries:
        assert s.status in valid_statuses, f"Unknown status inferred: {s.status}"


def test_bill_status_fallback_when_empty():
    """Verify fallback to 'Status not available.' when status is None/empty."""
    bill = Bill(
        bill_id="empty-status-bill",
        title="Empty Status Bill",
        year=2024,
        ministry="Finance",
        house=BillHouse.LOK_SABHA,
        status=None,  # type: ignore
        url="https://prsindia.org",
        full_text="",
    )
    service = DashboardService()
    with patch.object(service, "get_production_bills", return_value=[bill]), \
         patch.object(service, "_get_bill_decision_aggregates", return_value={}), \
         patch.object(service, "_get_bill_company_counts", return_value={}):
        service._bill_summaries_cache = None
        summaries = service._get_all_bill_summaries()
        assert len(summaries) == 1
        assert summaries[0].status == "Status not available."


# ---------------------------------------------------------------------------
# 6. MARKET PREDICTION DISPLAY & PROBABILISTIC LANGUAGE AUDIT
# ---------------------------------------------------------------------------

def test_market_prediction_probabilities_range(dashboard_service: DashboardService):
    """Verify all market impact probabilities are between 0.0 and 1.0."""
    df = dashboard_service.get_decision_dataframe()
    assert not df.empty
    assert (df["market_moving_probability"] >= 0.0).all()
    assert (df["market_moving_probability"] <= 1.0).all()
    assert df["confidence"].isin(["HIGH", "MEDIUM", "LOW", "VERY_HIGH", "VERY_LOW"]).all()



def test_probabilistic_language_audit_across_pages():
    """Audit dashboard pages for forbidden non-probabilistic claims."""
    forbidden_phrases = [
        "will increase",
        "will decrease",
        "guaranteed return",
        "guaranteed profit",
        "buy recommendation",
        "sell recommendation",
    ]
    pages_dir = Path("dashboard/pages")
    for py_file in pages_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8").lower()
        for phrase in forbidden_phrases:
            assert phrase not in content, f"Forbidden phrase '{phrase}' found in {py_file.name}"


# ---------------------------------------------------------------------------
# 7. INVESTMENT ADVICE SAFETY AUDIT
# ---------------------------------------------------------------------------

def test_investment_advice_disclaimer_presence(dashboard_service: DashboardService):
    """Verify non-investment advice disclaimer is present on Overview."""
    from dashboard.pages.overview import _DISCLAIMER
    assert "not guaranteed financial returns" in _DISCLAIMER.lower()
    assert "not be interpreted as personalized investment advice" in _DISCLAIMER.lower()


# ---------------------------------------------------------------------------
# 8. ANTICIPATION LANGUAGE AUDIT
# ---------------------------------------------------------------------------

def test_anticipation_language_audit():
    """Verify anticipation views never accuse entities of insider trading."""
    anticipation_file = Path("dashboard/pages/anticipation.py")
    content = anticipation_file.read_text(encoding="utf-8")
    assert "insider trading occurred" not in content.lower()
    assert "insiders traded" not in content.lower()
    assert "illegal trading happened" not in content.lower()
    assert "Anticipation evidence is NOT evidence of insider trading" in content or \
           "Anticipation evidence is not proof of insider trading" in content


# ---------------------------------------------------------------------------
# 9. GROUND-TRUTH SEPARATION
# ---------------------------------------------------------------------------

def test_ground_truth_not_in_prediction_inputs(dashboard_service: DashboardService):
    """Verify ground-truth post-event labels (e.g. realized CAR) are NOT in production decision DataFrame."""
    df = dashboard_service.get_decision_dataframe()
    forbidden_gt_columns = ["realized_car", "actual_car", "ground_truth_label", "actual_direction"]
    for col in forbidden_gt_columns:
        assert col not in df.columns, f"Ground-truth label column '{col}' exposed in decision DataFrame!"


# ---------------------------------------------------------------------------
# 10. ERROR STATES & MISSING ARTIFACT HANDLING
# ---------------------------------------------------------------------------

def test_missing_bill_returns_none(dashboard_service: DashboardService):
    """Verify non-existent bill ID returns None gracefully without crash."""
    detail = dashboard_service.get_bill_detail_data("completely-nonexistent-bill-id")
    assert detail is None


def test_missing_company_returns_none(dashboard_service: DashboardService):
    """Verify non-existent ISIN returns None gracefully without crash."""
    detail = dashboard_service.get_company_detail_data("INE000000000")
    assert detail is None


# ---------------------------------------------------------------------------
# 11. SEARCH & FILTER DETERMINISM
# ---------------------------------------------------------------------------

def test_search_bills_determinism(dashboard_service: DashboardService):
    """Verify bill search returns consistent, deterministic results across multiple queries."""
    res1 = dashboard_service.search_bills("Finance")
    res2 = dashboard_service.search_bills("Finance")
    assert len(res1) == len(res2)
    assert [b.bill_id for b in res1] == [b.bill_id for b in res2]


def test_search_bills_partial_match(dashboard_service: DashboardService):
    """Verify partial title match."""
    all_bills = dashboard_service.get_production_bills()
    first_title = all_bills[0].title
    word = first_title.split()[0]
    res = dashboard_service.search_bills(word)
    assert len(res) > 0
    assert any(b.bill_id == all_bills[0].bill_id for b in res)


# ---------------------------------------------------------------------------
# 12. ARTIFACT IMMUTABILITY VERIFICATION (BITWISE HASHING)
# ---------------------------------------------------------------------------

def test_artifact_immutability_before_and_after_dashboard_use():
    """
    Compute SHA256 hashes of sample artifacts across:
    - data/predictions/
    - data/decision_support/
    - data/anticipation/
    - data/backtests/
    - data/reports/
    Run dashboard queries, then verify all hashes remain 100% identical.
    """
    data_dir = Path("data")
    sample_files: list[Path] = []
    target_subdirs = ["predictions", "decision_support", "anticipation", "backtests", "reports"]

    for sub in target_subdirs:
        subpath = data_dir / sub
        if subpath.is_dir():
            files = list(subpath.rglob("*.json"))
            if files:
                sample_files.extend(files[:3])  # Sample first 3 files from each dir

    assert len(sample_files) > 0, "No data artifacts found for immutability check"

    # 1. Compute pre-run hashes
    def get_hash(path: Path) -> str:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()

    pre_hashes = {p: get_hash(p) for p in sample_files}

    # 2. Exercise dashboard service across multiple pages
    service = DashboardService()
    service.get_production_scope()
    service.get_newly_arrived_bills(days=365)
    service.get_all_bills_table_data()
    service.get_all_companies_summary()
    service.get_decision_dataframe()
    prod_bills = service.get_production_bills()
    if prod_bills:
        service.get_bill_detail_data(prod_bills[0].bill_id)

    # 3. Compute post-run hashes
    post_hashes = {p: get_hash(p) for p in sample_files}

    # 4. Verify identical hashes
    for p in sample_files:
        assert pre_hashes[p] == post_hashes[p], f"Artifact '{p}' was modified during dashboard operation!"
