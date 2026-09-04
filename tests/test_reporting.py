"""
tests/test_reporting.py
========================
Comprehensive tests for the Stakeholder Reporting & Presentation Layer (Task 7.3).

Coverage target: >95%

Test categories:
- Investor report generation
- Business report generation
- Public report generation
- Bill-level aggregation (all formula paths)
- Company-level aggregation
- Probability formatting edge cases
- Score formatting
- Anticipation explanation variations
- Disclaimer generation
- Report formatter (JSON / Markdown / CSV)
- Report validator
- Repository CRUD (save, get, exists, load_all, get_by_bill, get_by_company)
- Incremental execution (skip unchanged, regenerate on version change)
- Force refresh override
- Deterministic report IDs
- Invalid inputs / validation failures
"""

from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from reporting.bill_aggregator import BillAggregator
from reporting.business_reporter import BusinessReporter
from reporting.company_aggregator import CompanyAggregator
from reporting.formatter import ReportFormatter
from reporting.investor_reporter import InvestorReporter
from reporting.public_reporter import PublicReporter
from reporting.validator import ReportValidator
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company, MarketCapCategory
from schemas.decision import DecisionSupportRecord
from schemas.mapping_record import BillCompanyMapping
from schemas.report import (
    REPORT_DISCLAIMER,
    REPORT_METHODOLOGY_NOTE,
    REPORT_VERSION,
    BillLevelReport,
    CompanyLevelReport,
    ReportValidationReport,
    StakeholderReport,
    StakeholderType,
    make_bill_report_id,
    make_company_report_id,
    make_report_id,
    make_validation_report_id,
)
from storage.report_repository import ReportRepository


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_decision() -> DecisionSupportRecord:
    """A complete, valid DecisionSupportRecord for testing."""
    return DecisionSupportRecord(
        decision_id="dec_the-telecom-act-2024_INE002A01018_-20_p20",
        bill_id="the-telecom-act-2024",
        company_isin="INE002A01018",
        company_name="Reliance Industries Limited",
        company_symbol="RELIANCE",
        sector="Energy",
        event_window="[-20,+20]",
        predicted_direction="POSITIVE",
        direction_probability={"POSITIVE": 0.82, "NEGATIVE": 0.08, "NEUTRAL": 0.10},
        market_moving_probability=0.75,
        predicted_impact_strength="HIGH",
        impact_probabilities={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.65, "VERY_HIGH": 0.15},
        predicted_confidence="HIGH",
        confidence_probability={"LOW": 0.05, "MEDIUM": 0.15, "HIGH": 0.80},
        confidence_score=0.78,
        anticipation_class="MODERATE_EVIDENCE",
        anticipation_score=0.55,
        impact_score=0.72,
        impact_category="HIGH",
        risk_score=0.45,
        risk_category="MODERATE",
        pricing_in_risk="MODERATE",
        pricing_in_score=0.48,
        investor_summary="Investor perspective.",
        business_summary="Business perspective.",
        public_summary="Public perspective.",
        decision_reason="Test decision reason. [disclaimer]",
        model_version="v1.0",
        feature_version="v1.0",
        decision_version="v1.0",
        generation_timestamp="2026-08-17T10:00:00Z",
        data_quality_status="VALID",
    )


@pytest.fixture
def negative_decision() -> DecisionSupportRecord:
    """A DecisionSupportRecord with NEGATIVE direction."""
    return DecisionSupportRecord(
        decision_id="dec_finance-bill-2024_INE009A01021_-20_p20",
        bill_id="finance-bill-2024",
        company_isin="INE009A01021",
        company_name="Infosys Limited",
        company_symbol="INFY",
        sector="Technology",
        event_window="[-20,+20]",
        predicted_direction="NEGATIVE",
        direction_probability={"POSITIVE": 0.10, "NEGATIVE": 0.78, "NEUTRAL": 0.12},
        market_moving_probability=0.68,
        predicted_impact_strength="MEDIUM",
        impact_probabilities={"LOW": 0.10, "MEDIUM": 0.60, "HIGH": 0.25, "VERY_HIGH": 0.05},
        predicted_confidence="MEDIUM",
        confidence_probability={"LOW": 0.20, "MEDIUM": 0.60, "HIGH": 0.20},
        confidence_score=0.52,
        anticipation_class="STRONG_EVIDENCE",
        anticipation_score=0.82,
        impact_score=0.54,
        impact_category="MEDIUM",
        risk_score=0.65,
        risk_category="HIGH",
        pricing_in_risk="HIGH",
        pricing_in_score=0.71,
        investor_summary="Negative signal.",
        business_summary="Regulatory headwind.",
        public_summary="Law may affect IT sector.",
        decision_reason="Negative reason. [disclaimer]",
        model_version="v1.0",
        feature_version="v1.0",
        decision_version="v1.0",
        generation_timestamp="2026-08-17T10:00:00Z",
        data_quality_status="VALID",
    )


@pytest.fixture
def neutral_decision() -> DecisionSupportRecord:
    """A DecisionSupportRecord with NEUTRAL direction."""
    return DecisionSupportRecord(
        decision_id="dec_env-bill-2023_INE040A01034_-5_p5",
        bill_id="environment-protection-bill-2023",
        company_isin="INE040A01034",
        company_name="Hindustan Unilever Limited",
        company_symbol="HINDUNILVR",
        sector="Consumer Goods",
        event_window="[-5,+5]",
        predicted_direction="NEUTRAL",
        direction_probability={"POSITIVE": 0.20, "NEGATIVE": 0.15, "NEUTRAL": 0.65},
        market_moving_probability=0.28,
        predicted_impact_strength="LOW",
        impact_probabilities={"LOW": 0.65, "MEDIUM": 0.25, "HIGH": 0.08, "VERY_HIGH": 0.02},
        predicted_confidence="LOW",
        confidence_probability={"LOW": 0.55, "MEDIUM": 0.35, "HIGH": 0.10},
        confidence_score=0.28,
        anticipation_class="NO_EVIDENCE",
        anticipation_score=0.05,
        impact_score=0.25,
        impact_category="LOW",
        risk_score=0.30,
        risk_category="LOW",
        pricing_in_risk="VERY_LOW",
        pricing_in_score=0.08,
        investor_summary="Neutral signal.",
        business_summary="Minimal impact.",
        public_summary="Minor effect expected.",
        decision_reason="Neutral reason.",
        model_version="v1.0",
        feature_version="v1.0",
        decision_version="v1.0",
        generation_timestamp="2026-08-17T10:00:00Z",
        data_quality_status="VALID",
    )


@pytest.fixture
def sample_bill() -> Bill:
    return Bill(
        bill_id="the-telecom-act-2024",
        title="The Telecommunications Act, 2024",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.PASSED_BOTH,
        url="https://prsindia.org/bills/telecom-2024",
        bill_number="7/2024",
        year=2024,
        ministry="Ministry of Communications",
        session="Budget Session, 2024",
        sponsor="Minister of Communications",
        introduction_date=date(2024, 2, 5),
        summary=(
            "This bill aims to overhaul India's telecommunications regulatory framework, "
            "introducing updated licensing norms, spectrum management, and consumer protection measures."
        ),
        sectors=["Telecommunications", "Technology", "Broadcasting"],
        keywords=["spectrum", "licensing", "5G", "consumer protection"],
        related_acts=["Indian Telegraph Act, 1885", "TRAI Act, 1997"],
    )


@pytest.fixture
def sample_company() -> Company:
    return Company(
        isin="INE002A01018",
        company_name="Reliance Industries Limited",
        ticker_nse="RELIANCE",
        ticker_bse="RELIANCE",
        bse_code="500325",
        sector="Energy",
        industry="Diversified",
        sub_industry="Conglomerate",
        market_cap_category=MarketCapCategory.LARGE_CAP,
        market_cap_cr=1950000.0,
        hq_city="Mumbai",
        hq_state="Maharashtra",
    )


@pytest.fixture
def sample_mapping() -> BillCompanyMapping:
    m = MagicMock(spec=BillCompanyMapping)
    m.bill_id = "the-telecom-act-2024"
    m.company_isin = "INE002A01018"
    m.mapping_confidence = 0.92
    m.mapping_reason = "Reliance Jio is a major telecom operator directly regulated by this bill."
    m.candidate_companies = []
    return m


@pytest.fixture
def tmp_reports_dir(tmp_path: Path) -> Path:
    return tmp_path / "reports"


@pytest.fixture
def report_repo(tmp_reports_dir: Path) -> ReportRepository:
    return ReportRepository(reports_dir=tmp_reports_dir)


# ---------------------------------------------------------------------------
# SECTION 1 — Deterministic Report IDs
# ---------------------------------------------------------------------------


class TestDeterministicReportIds:
    def test_make_report_id_deterministic(self):
        """Same inputs always produce the same report_id."""
        id1 = make_report_id("bill-a", "INE001", "[-20,+20]", "INVESTOR")
        id2 = make_report_id("bill-a", "INE001", "[-20,+20]", "INVESTOR")
        assert id1 == id2

    def test_make_report_id_differs_by_stakeholder(self):
        id_inv = make_report_id("bill-a", "INE001", "[-20,+20]", "INVESTOR")
        id_bus = make_report_id("bill-a", "INE001", "[-20,+20]", "BUSINESS")
        id_pub = make_report_id("bill-a", "INE001", "[-20,+20]", "PUBLIC")
        assert id_inv != id_bus != id_pub

    def test_make_report_id_differs_by_bill(self):
        id1 = make_report_id("bill-a", "INE001", "[-20,+20]", "INVESTOR")
        id2 = make_report_id("bill-b", "INE001", "[-20,+20]", "INVESTOR")
        assert id1 != id2

    def test_make_bill_report_id_deterministic(self):
        id1 = make_bill_report_id("finance-bill-2024")
        id2 = make_bill_report_id("finance-bill-2024")
        assert id1 == id2
        assert id1.startswith("bill_rpt_")

    def test_make_company_report_id_deterministic(self):
        id1 = make_company_report_id("INE009A01021")
        id2 = make_company_report_id("INE009A01021")
        assert id1 == id2
        assert id1.startswith("co_rpt_")

    def test_make_validation_report_id(self):
        val_id = make_validation_report_id("rpt_bill_isin_win_investor")
        assert val_id.startswith("val_")

    def test_report_id_sanitizes_special_chars(self):
        """Event window brackets and plus signs are safely sanitized."""
        rid = make_report_id("bill/test", "INE:001", "[-20,+20]", "PUBLIC")
        assert "/" not in rid
        assert ":" not in rid
        assert "[" not in rid
        assert "]" not in rid


# ---------------------------------------------------------------------------
# SECTION 2 — Schema Tests
# ---------------------------------------------------------------------------


class TestStakeholderReportSchema:
    def test_round_trip_json(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        d = report.to_dict()
        restored = StakeholderReport.from_dict(d)
        assert restored.report_id == report.report_id
        assert restored.bill_id == report.bill_id
        assert restored.stakeholder_type == report.stakeholder_type

    def test_auto_generates_report_id(self, sample_decision: DecisionSupportRecord):
        report = StakeholderReport(
            report_id="",
            bill_id=sample_decision.bill_id,
            company_isin=sample_decision.company_isin,
            event_window=sample_decision.event_window,
            stakeholder_type="INVESTOR",
            decision_version="v1.0",
            generated_timestamp="",
            report_version="v1.0",
            executive_summary="summary",
            bill_summary="bill",
            company_summary="company",
            impact_summary="impact",
            risk_summary="risk",
            anticipation_summary="anticipation",
            confidence_summary="confidence",
        )
        assert report.report_id.startswith("rpt_")
        assert report.generated_timestamp != ""

    def test_bill_level_report_round_trip(self):
        rpt = BillLevelReport(
            report_id="bill_rpt_test",
            bill_id="test-bill",
            bill_title="Test Bill",
            bill_ministry="Ministry of Test",
            bill_year=2024,
            event_window="[-20,+20]",
            generated_timestamp="2026-08-17T10:00:00Z",
            report_version="v1.0",
            total_companies=3,
            positive_count=2,
            negative_count=1,
            neutral_count=0,
            market_moving_count=2,
            high_impact_count=1,
            avg_impact_score=0.65,
            avg_risk_score=0.45,
            anticipation_distribution={"MODERATE_EVIDENCE": 2, "NO_EVIDENCE": 1},
            risk_distribution={"MODERATE": 2, "LOW": 1},
            sectors_affected=["Banking", "Technology"],
        )
        d = rpt.to_dict()
        restored = BillLevelReport.from_dict(d)
        assert restored.total_companies == 3
        assert restored.avg_impact_score == pytest.approx(0.65, abs=1e-4)
        assert restored.sectors_affected == ["Banking", "Technology"]

    def test_company_level_report_round_trip(self):
        rpt = CompanyLevelReport(
            report_id="co_rpt_INE001",
            company_isin="INE001",
            company_name="Test Co",
            company_sector="Banking",
            generated_timestamp="2026-08-17T10:00:00Z",
            report_version="v1.0",
            total_bills=5,
            positive_bill_count=3,
            negative_bill_count=1,
            neutral_bill_count=1,
            avg_impact_score=0.55,
            avg_risk_score=0.38,
        )
        d = rpt.to_dict()
        restored = CompanyLevelReport.from_dict(d)
        assert restored.total_bills == 5
        assert restored.company_name == "Test Co"


# ---------------------------------------------------------------------------
# SECTION 3 — Investor Reporter
# ---------------------------------------------------------------------------


class TestInvestorReporter:
    def test_builds_report_positive_direction(
        self, sample_decision: DecisionSupportRecord, sample_bill: Bill, sample_company: Company
    ):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision, sample_bill, sample_company)
        assert report.stakeholder_type == StakeholderType.INVESTOR.value
        assert "POSITIVE" in report.bill_id or "Telecommunications" in report.bill_summary
        assert "potential positive" in report.executive_summary.lower()
        assert "Model indicates" in report.executive_summary

    def test_builds_report_negative_direction(self, negative_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(negative_decision)
        assert "negative" in report.executive_summary.lower()

    def test_builds_report_neutral_direction(self, neutral_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(neutral_decision)
        assert "neutral" in report.executive_summary.lower() or "subdued" in report.executive_summary.lower()

    def test_no_trading_recommendations(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        full_text = " ".join([
            report.executive_summary, report.impact_summary, report.risk_summary
        ]).lower()
        assert "buy this stock" not in full_text
        assert "guaranteed return" not in full_text
        assert "will rise" not in full_text
        assert "will fall" not in full_text

    def test_probabilistic_language(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        full_text = report.executive_summary + report.impact_summary
        assert any(w in full_text.lower() for w in [
            "model indicates", "potential", "probability", "estimated"
        ])

    def test_impact_summary_direction_probabilities(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        assert "82" in report.impact_summary  # 82% positive
        assert "75" in report.impact_summary  # 75% market moving

    def test_anticipation_strong_evidence(self, negative_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(negative_decision)
        # Strong evidence: anticipation_score=0.82
        assert "strong" in report.anticipation_summary.lower() or "substantial" in report.anticipation_summary.lower()

    def test_anticipation_no_evidence(self, neutral_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(neutral_decision)
        assert "no" in report.anticipation_summary.lower() or "not analyzed" in report.anticipation_summary.lower() or "no_evidence" in report.anticipation_summary.lower()

    def test_key_factors_from_shap(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        shap_factors = ["feature_a", "feature_b", "feature_c"]
        report = reporter.build(sample_decision, top_factors=shap_factors)
        assert any("feature_a" in f for f in report.key_factors)

    def test_key_factors_fallback_without_shap(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision, top_factors=None)
        assert len(report.key_factors) >= 4

    def test_disclaimer_present(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        assert "academic" in report.disclaimer.lower() or "not" in report.disclaimer.lower()
        assert report.disclaimer != ""

    def test_methodology_note_present(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        assert report.methodology_note != ""
        assert "model" in report.methodology_note.lower()

    def test_confidence_summary_distribution(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        assert "80" in report.confidence_summary  # 80% HIGH confidence
        assert "High" in report.confidence_summary

    def test_report_version_propagated(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter(report_version="v2.0")
        report = reporter.build(sample_decision)
        assert report.report_version == "v2.0"

    def test_company_summary_has_isin(
        self, sample_decision: DecisionSupportRecord, sample_company: Company
    ):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision, company=sample_company)
        assert "INE002A01018" in report.company_summary
        assert "RELIANCE" in report.company_summary

    def test_bill_summary_has_ministry(
        self, sample_decision: DecisionSupportRecord, sample_bill: Bill
    ):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision, bill=sample_bill)
        assert "Ministry of Communications" in report.bill_summary

    def test_builds_without_bill_company(self, sample_decision: DecisionSupportRecord):
        """Should not raise when bill and company are None."""
        reporter = InvestorReporter()
        report = reporter.build(sample_decision, bill=None, company=None)
        assert report.report_id != ""

    def test_probability_formatting_zero(self):
        """Zero probabilities handled gracefully."""
        decision = DecisionSupportRecord(
            decision_id="dec_test",
            bill_id="test-bill",
            company_isin="INE999",
            event_window="[-20,+20]",
            predicted_direction="NEUTRAL",
            direction_probability={"POSITIVE": 0.0, "NEGATIVE": 0.0, "NEUTRAL": 1.0},
            market_moving_probability=0.0,
            predicted_impact_strength="LOW",
            impact_probabilities={"LOW": 1.0, "MEDIUM": 0.0, "HIGH": 0.0, "VERY_HIGH": 0.0},
            predicted_confidence="LOW",
            confidence_probability={"LOW": 1.0, "MEDIUM": 0.0, "HIGH": 0.0},
            confidence_score=0.0,
            anticipation_class="NOT_ANALYZED",
            anticipation_score=0.0,
            impact_score=0.0,
            impact_category="LOW",
            risk_score=0.0,
            risk_category="VERY_LOW",
            pricing_in_risk="VERY_LOW",
            pricing_in_score=0.0,
            investor_summary="",
            business_summary="",
            public_summary="",
            decision_reason="",
            model_version="v1.0",
            feature_version="v1.0",
        )
        reporter = InvestorReporter()
        report = reporter.build(decision)
        assert report is not None


# ---------------------------------------------------------------------------
# SECTION 4 — Business Reporter
# ---------------------------------------------------------------------------


class TestBusinessReporter:
    def test_builds_business_report(
        self,
        sample_decision: DecisionSupportRecord,
        sample_bill: Bill,
        sample_company: Company,
        sample_mapping: BillCompanyMapping,
    ):
        reporter = BusinessReporter()
        report = reporter.build(sample_decision, sample_bill, sample_company, sample_mapping)
        assert report.stakeholder_type == StakeholderType.BUSINESS.value
        assert "Reliance Industries" in report.executive_summary
        assert "Ministry of Communications" in report.bill_summary

    def test_no_trading_language(
        self, sample_decision: DecisionSupportRecord, sample_bill: Bill
    ):
        reporter = BusinessReporter()
        report = reporter.build(sample_decision, sample_bill)
        full_text = " ".join([report.impact_summary, report.executive_summary]).lower()
        assert "buy" not in full_text
        assert "sell" not in full_text
        assert "will rise" not in full_text
        assert "will fall" not in full_text

    def test_regulatory_language(self, sample_decision: DecisionSupportRecord):
        reporter = BusinessReporter()
        report = reporter.build(sample_decision)
        assert any(w in report.impact_summary.lower() for w in [
            "regulatory", "compliance", "operational", "statutory"
        ])

    def test_positive_operational_implications(self, sample_decision: DecisionSupportRecord):
        reporter = BusinessReporter()
        report = reporter.build(sample_decision)
        assert "tailwinds" in report.impact_summary.lower() or "favourable" in report.impact_summary.lower() or "positive" in report.impact_summary.lower()

    def test_negative_operational_implications(self, negative_decision: DecisionSupportRecord):
        reporter = BusinessReporter()
        report = reporter.build(negative_decision)
        assert "headwinds" in report.impact_summary.lower() or "heightened" in report.impact_summary.lower() or "adverse" in report.impact_summary.lower()

    def test_neutral_operational_implications(self, neutral_decision: DecisionSupportRecord):
        reporter = BusinessReporter()
        report = reporter.build(neutral_decision)
        assert "neutral" in report.impact_summary.lower() or "manageable" in report.impact_summary.lower()

    def test_mapping_confidence_included(
        self, sample_decision: DecisionSupportRecord, sample_mapping: BillCompanyMapping
    ):
        reporter = BusinessReporter()
        report = reporter.build(sample_decision, mapping=sample_mapping)
        assert "0.92" in report.impact_summary or "relevance" in report.impact_summary.lower()

    def test_bill_keywords_included(
        self, sample_decision: DecisionSupportRecord, sample_bill: Bill
    ):
        reporter = BusinessReporter()
        report = reporter.build(sample_decision, bill=sample_bill)
        assert any(kw in report.bill_summary for kw in ["spectrum", "5G", "licensing"])

    def test_risk_category_in_risk_summary(self, sample_decision: DecisionSupportRecord):
        reporter = BusinessReporter()
        report = reporter.build(sample_decision)
        assert "Moderate" in report.risk_summary

    def test_anticipation_business_context(self, negative_decision: DecisionSupportRecord):
        reporter = BusinessReporter()
        report = reporter.build(negative_decision)
        assert "proactive" in report.anticipation_summary.lower() or "anticipated" in report.anticipation_summary.lower()


# ---------------------------------------------------------------------------
# SECTION 5 — Public Reporter
# ---------------------------------------------------------------------------


class TestPublicReporter:
    def test_builds_public_report(
        self,
        sample_decision: DecisionSupportRecord,
        sample_bill: Bill,
        sample_company: Company,
    ):
        reporter = PublicReporter()
        report = reporter.build(sample_decision, sample_bill, sample_company)
        assert report.stakeholder_type == StakeholderType.PUBLIC.value

    def test_plain_english_no_jargon(self, sample_decision: DecisionSupportRecord):
        reporter = PublicReporter()
        report = reporter.build(sample_decision)
        full_text = " ".join([
            report.executive_summary, report.impact_summary,
            report.anticipation_summary, report.confidence_summary,
        ]).lower()
        assert "shap" not in full_text
        assert "gradient" not in full_text
        assert "lightgbm" not in full_text
        assert "cumulative abnormal return" not in full_text

    def test_no_investment_advice(self, sample_decision: DecisionSupportRecord):
        reporter = PublicReporter()
        report = reporter.build(sample_decision)
        full_text = (report.executive_summary + report.impact_summary).lower()
        assert "buy" not in full_text
        assert "sell" not in full_text
        # "Guaranteed return" or affirmative guaranteeing language is not allowed.
        # "this is not guaranteed" is acceptable disclaimer phrasing.
        assert "guaranteed return" not in full_text
        assert "guaranteed to rise" not in full_text
        assert "guaranteed to fall" not in full_text

    def test_explains_bill_purpose(
        self, sample_decision: DecisionSupportRecord, sample_bill: Bill
    ):
        reporter = PublicReporter()
        report = reporter.build(sample_decision, bill=sample_bill)
        assert "proposed law" in report.bill_summary.lower() or "bill" in report.bill_summary.lower()
        assert "Telecommunications" in report.bill_summary

    def test_accessible_confidence_language(self, sample_decision: DecisionSupportRecord):
        reporter = PublicReporter()
        report = reporter.build(sample_decision)
        assert "confident" in report.confidence_summary.lower() or "confidence" in report.confidence_summary.lower()

    def test_positive_impact_plain_language(self, sample_decision: DecisionSupportRecord):
        reporter = PublicReporter()
        report = reporter.build(sample_decision)
        assert any(p in report.impact_summary.lower() for p in [
            "good news", "rise", "positive", "might"
        ])

    def test_negative_impact_plain_language(self, negative_decision: DecisionSupportRecord):
        reporter = PublicReporter()
        report = reporter.build(negative_decision)
        assert any(p in report.impact_summary.lower() for p in [
            "challenging", "fall", "negative", "might"
        ])

    def test_neutral_impact_plain_language(self, neutral_decision: DecisionSupportRecord):
        reporter = PublicReporter()
        report = reporter.build(neutral_decision)
        assert "big change" in report.impact_summary.lower() or "small" in report.impact_summary.lower()

    def test_anticipation_strong_evidence_plain(self, negative_decision: DecisionSupportRecord):
        reporter = PublicReporter()
        report = reporter.build(negative_decision)
        assert "anticipated" in report.anticipation_summary.lower() or "expected" in report.anticipation_summary.lower()

    def test_anticipation_no_evidence_plain(self, neutral_decision: DecisionSupportRecord):
        reporter = PublicReporter()
        report = reporter.build(neutral_decision)
        assert "unusual" not in report.anticipation_summary.lower() or "no" in report.anticipation_summary.lower()

    def test_public_disclaimer_plain(self, sample_decision: DecisionSupportRecord):
        reporter = PublicReporter()
        report = reporter.build(sample_decision)
        assert "educational" in report.disclaimer.lower() or "information" in report.disclaimer.lower()


# ---------------------------------------------------------------------------
# SECTION 6 — Bill Aggregator
# ---------------------------------------------------------------------------


class TestBillAggregator:
    def test_aggregates_counts_correctly(
        self,
        sample_decision: DecisionSupportRecord,
        negative_decision: DecisionSupportRecord,
        neutral_decision: DecisionSupportRecord,
    ):
        """Verify all count formulas."""
        agg = BillAggregator()
        # Override bill_id so all appear as same bill
        neg = DecisionSupportRecord(
            **{**negative_decision.__dict__, "bill_id": "test-bill", "event_window": "[-20,+20]"}
        )
        neu = DecisionSupportRecord(
            **{**neutral_decision.__dict__, "bill_id": "test-bill", "event_window": "[-20,+20]"}
        )
        pos = DecisionSupportRecord(
            **{**sample_decision.__dict__, "bill_id": "test-bill", "event_window": "[-20,+20]"}
        )
        records = [pos, neg, neu]
        report = agg.build("test-bill", records)

        assert report.total_companies == 3
        assert report.positive_count == 1
        assert report.negative_count == 1
        assert report.neutral_count == 1

    def test_market_moving_threshold_0_50(
        self, sample_decision: DecisionSupportRecord, neutral_decision: DecisionSupportRecord
    ):
        """market_moving_count uses threshold >= 0.50."""
        agg = BillAggregator()
        high = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "market_moving_probability": 0.75})
        low = DecisionSupportRecord(**{**neutral_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "market_moving_probability": 0.28})
        borderline = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "company_isin": "INE999X", "event_window": "[-20,+20]", "market_moving_probability": 0.50})

        report = agg.build("b", [high, low, borderline])
        assert report.market_moving_count == 2  # 0.75 and 0.50

    def test_high_impact_count_threshold(
        self, sample_decision: DecisionSupportRecord, neutral_decision: DecisionSupportRecord
    ):
        """high_impact_count uses impact_category in {HIGH, VERY_HIGH}."""
        agg = BillAggregator()
        high = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "impact_category": "HIGH"})
        very_high = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "company_isin": "INE002", "event_window": "[-20,+20]", "impact_category": "VERY_HIGH"})
        low = DecisionSupportRecord(**{**neutral_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "impact_category": "LOW"})
        medium = DecisionSupportRecord(**{**neutral_decision.__dict__, "bill_id": "b", "company_isin": "INE003", "event_window": "[-20,+20]", "impact_category": "MEDIUM"})

        report = agg.build("b", [high, very_high, low, medium])
        assert report.high_impact_count == 2

    def test_avg_impact_score_arithmetic_mean(self, sample_decision: DecisionSupportRecord):
        """avg_impact_score = sum(impact_score) / n, NOT probability average."""
        agg = BillAggregator()
        r1 = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "impact_score": 0.60})
        r2 = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "company_isin": "INE002", "event_window": "[-20,+20]", "impact_score": 0.80})
        report = agg.build("b", [r1, r2])
        assert report.avg_impact_score == pytest.approx(0.70, abs=1e-4)

    def test_avg_risk_score_arithmetic_mean(self, sample_decision: DecisionSupportRecord):
        """avg_risk_score = sum(risk_score) / n."""
        agg = BillAggregator()
        r1 = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "risk_score": 0.30})
        r2 = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "company_isin": "INE002", "event_window": "[-20,+20]", "risk_score": 0.70})
        report = agg.build("b", [r1, r2])
        assert report.avg_risk_score == pytest.approx(0.50, abs=1e-4)

    def test_anticipation_distribution(
        self,
        sample_decision: DecisionSupportRecord,
        negative_decision: DecisionSupportRecord,
        neutral_decision: DecisionSupportRecord,
    ):
        """Anticipation distribution counts each class."""
        agg = BillAggregator()
        mod = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "anticipation_class": "MODERATE_EVIDENCE"})
        strong = DecisionSupportRecord(**{**negative_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "anticipation_class": "STRONG_EVIDENCE"})
        no_ev = DecisionSupportRecord(**{**neutral_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "anticipation_class": "NO_EVIDENCE"})
        report = agg.build("b", [mod, strong, no_ev])
        assert report.anticipation_distribution["MODERATE_EVIDENCE"] == 1
        assert report.anticipation_distribution["STRONG_EVIDENCE"] == 1
        assert report.anticipation_distribution["NO_EVIDENCE"] == 1

    def test_sectors_affected_sorted_unique(self, sample_decision: DecisionSupportRecord):
        """sectors_affected is sorted and deduplicated."""
        agg = BillAggregator()
        r1 = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]", "sector": "Technology"})
        r2 = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "company_isin": "X1", "event_window": "[-20,+20]", "sector": "Banking"})
        r3 = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "company_isin": "X2", "event_window": "[-20,+20]", "sector": "Technology"})
        report = agg.build("b", [r1, r2, r3])
        assert report.sectors_affected == ["Banking", "Technology"]
        assert len(report.sectors_affected) == 2

    def test_empty_records_returns_zero_report(self):
        agg = BillAggregator()
        report = agg.build("empty-bill", [])
        assert report.total_companies == 0
        assert report.positive_count == 0
        assert report.avg_impact_score == 0.0

    def test_bill_metadata_included(self, sample_decision, sample_bill):
        agg = BillAggregator()
        d = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": sample_bill.bill_id, "event_window": "[-20,+20]"})
        report = agg.build(sample_bill.bill_id, [d], bill=sample_bill)
        assert report.bill_title == sample_bill.title
        assert report.bill_ministry == sample_bill.ministry
        assert report.bill_year == 2024

    def test_event_window_filter(self, sample_decision: DecisionSupportRecord):
        """Only records matching event_window are aggregated."""
        agg = BillAggregator()
        r1 = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "event_window": "[-20,+20]"})
        r2 = DecisionSupportRecord(**{**sample_decision.__dict__, "bill_id": "b", "company_isin": "X1", "event_window": "[-5,+5]"})
        report = agg.build("b", [r1, r2], event_window="[-5,+5]")
        assert report.total_companies == 1


# ---------------------------------------------------------------------------
# SECTION 7 — Company Aggregator
# ---------------------------------------------------------------------------


class TestCompanyAggregator:
    def test_aggregates_bills_for_company(
        self,
        sample_decision: DecisionSupportRecord,
        negative_decision: DecisionSupportRecord,
    ):
        """All bills for a company are correctly counted."""
        agg = CompanyAggregator()
        isin = sample_decision.company_isin
        r1 = DecisionSupportRecord(**{**sample_decision.__dict__, "company_isin": isin})
        r2 = DecisionSupportRecord(**{
            **negative_decision.__dict__,
            "company_isin": isin,
            "bill_id": "another-bill",
        })
        report = agg.build(isin, [r1, r2])
        assert report.total_bills == 2
        assert report.positive_bill_count == 1
        assert report.negative_bill_count == 1

    def test_avg_scores_arithmetic_mean(self, sample_decision: DecisionSupportRecord):
        agg = CompanyAggregator()
        isin = "INE_TEST"
        r1 = DecisionSupportRecord(**{**sample_decision.__dict__, "company_isin": isin, "bill_id": "bill1", "impact_score": 0.40, "risk_score": 0.20})
        r2 = DecisionSupportRecord(**{**sample_decision.__dict__, "company_isin": isin, "bill_id": "bill2", "impact_score": 0.60, "risk_score": 0.40})
        report = agg.build(isin, [r1, r2])
        assert report.avg_impact_score == pytest.approx(0.50, abs=1e-4)
        assert report.avg_risk_score == pytest.approx(0.30, abs=1e-4)

    def test_high_impact_bills_list(self, sample_decision: DecisionSupportRecord):
        agg = CompanyAggregator()
        isin = sample_decision.company_isin
        high = DecisionSupportRecord(**{**sample_decision.__dict__, "company_isin": isin, "impact_category": "HIGH"})
        very_high = DecisionSupportRecord(**{**sample_decision.__dict__, "company_isin": isin, "bill_id": "vhigh-bill", "impact_category": "VERY_HIGH"})
        low = DecisionSupportRecord(**{**sample_decision.__dict__, "company_isin": isin, "bill_id": "low-bill", "impact_category": "LOW"})
        report = agg.build(isin, [high, very_high, low])
        assert sample_decision.bill_id in report.high_impact_bills
        assert "vhigh-bill" in report.high_impact_bills
        assert "low-bill" not in report.high_impact_bills

    def test_empty_records_zero_report(self):
        agg = CompanyAggregator()
        report = agg.build("INE_EMPTY", [])
        assert report.total_bills == 0
        assert report.avg_impact_score == 0.0

    def test_company_metadata_included(
        self, sample_decision: DecisionSupportRecord, sample_company: Company
    ):
        agg = CompanyAggregator()
        report = agg.build(sample_company.isin, [sample_decision], company=sample_company)
        assert report.company_name == sample_company.company_name
        assert report.company_sector == sample_company.sector


# ---------------------------------------------------------------------------
# SECTION 8 — Report Formatter
# ---------------------------------------------------------------------------


class TestReportFormatter:
    @pytest.fixture
    def investor_report(self, sample_decision: DecisionSupportRecord) -> StakeholderReport:
        return InvestorReporter().build(sample_decision)

    def test_to_json_valid(self, investor_report: StakeholderReport):
        fmt = ReportFormatter()
        json_str = fmt.to_json(investor_report)
        data = json.loads(json_str)
        assert data["bill_id"] == investor_report.bill_id
        assert data["stakeholder_type"] == "INVESTOR"

    def test_to_json_indent(self, investor_report: StakeholderReport):
        fmt = ReportFormatter()
        json_str = fmt.to_json(investor_report, indent=4)
        assert "    " in json_str

    def test_to_markdown_stakeholder(self, investor_report: StakeholderReport):
        fmt = ReportFormatter()
        md = fmt.to_markdown(investor_report)
        assert "# Legislative Market Impact Report" in md
        assert "## Executive Summary" in md
        assert "## Bill Overview" in md
        assert "## Risk Assessment" in md
        assert "## Disclaimer" in md

    def test_to_markdown_bill_report(self, sample_decision: DecisionSupportRecord):
        agg = BillAggregator()
        bill_rpt = agg.build("test", [sample_decision])
        fmt = ReportFormatter()
        md = fmt.to_markdown(bill_rpt)
        assert "# Bill-Level Market Impact Summary" in md
        assert "| Metric | Value |" in md

    def test_to_markdown_company_report(self, sample_decision: DecisionSupportRecord):
        agg = CompanyAggregator()
        co_rpt = agg.build(sample_decision.company_isin, [sample_decision])
        fmt = ReportFormatter()
        md = fmt.to_markdown(co_rpt)
        assert "# Company Legislative Exposure Report" in md
        assert "| Metric | Value |" in md

    def test_to_csv_stakeholder(self, investor_report: StakeholderReport):
        fmt = ReportFormatter()
        csv_str = fmt.to_csv_summary([investor_report], report_type="stakeholder")
        assert "report_id" in csv_str
        assert investor_report.report_id in csv_str

    def test_to_csv_bill(self, sample_decision: DecisionSupportRecord):
        agg = BillAggregator()
        bill_rpt = agg.build("test", [sample_decision])
        fmt = ReportFormatter()
        csv_str = fmt.to_csv_summary([bill_rpt], report_type="bill")
        assert "bill_id" in csv_str
        assert "test" in csv_str

    def test_to_csv_company(self, sample_decision: DecisionSupportRecord):
        agg = CompanyAggregator()
        co_rpt = agg.build(sample_decision.company_isin, [sample_decision])
        fmt = ReportFormatter()
        csv_str = fmt.to_csv_summary([co_rpt], report_type="company")
        assert "company_isin" in csv_str

    def test_to_csv_empty_list(self):
        fmt = ReportFormatter()
        result = fmt.to_csv_summary([], report_type="stakeholder")
        assert result == ""


# ---------------------------------------------------------------------------
# SECTION 9 — Report Validator
# ---------------------------------------------------------------------------


class TestReportValidator:
    def test_valid_report_passes(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        validator = ReportValidator()
        val = validator.validate(report)
        assert val.is_valid
        assert val.errors == []

    def test_missing_bill_id_fails(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        report.bill_id = ""
        validator = ReportValidator()
        val = validator.validate(report)
        assert not val.is_valid
        assert any("bill_id" in e.lower() or "required" in e.lower() or "missing" in e.lower() for e in val.errors)

    def test_invalid_stakeholder_type_fails(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        report.stakeholder_type = "TRADER"
        validator = ReportValidator()
        val = validator.validate(report)
        assert not val.is_valid
        assert any("stakeholder" in e.lower() for e in val.errors)

    def test_invalid_event_window_fails(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        report.event_window = "bad_window"
        validator = ReportValidator()
        val = validator.validate(report)
        assert not val.is_valid
        assert any("event_window" in e.lower() for e in val.errors)

    def test_valid_event_window_formats(self, sample_decision: DecisionSupportRecord):
        """Various valid event window formats should pass."""
        reporter = InvestorReporter()
        valid_windows = ["[-20,+20]", "[-5,+5]", "[-10,+10]", "[-1,+1]"]
        for win in valid_windows:
            report = reporter.build(sample_decision)
            report.event_window = win
            validator = ReportValidator()
            val = validator.validate(report)
            assert "event_window" not in " ".join(val.errors).lower(), f"Failed for window: {win}"

    def test_duplicate_report_id_warning(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        validator = ReportValidator()
        report = reporter.build(sample_decision)
        validator.validate(report)  # First: registers ID
        val2 = validator.validate(report)  # Second: duplicate
        assert any("duplicate" in w.lower() for w in val2.warnings)

    def test_reset_clears_seen_ids(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        validator = ReportValidator()
        report = reporter.build(sample_decision)
        validator.validate(report)
        validator.reset()
        val3 = validator.validate(report)
        assert not any("duplicate" in w.lower() for w in val3.warnings)

    def test_checks_performed_documented(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        validator = ReportValidator()
        val = validator.validate(report)
        assert "required_fields_present" in val.checks_performed
        assert "valid_stakeholder_type" in val.checks_performed
        assert "valid_event_window" in val.checks_performed

    def test_validation_report_schema(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        validator = ReportValidator()
        val = validator.validate(report)
        d = val.to_dict()
        restored = ReportValidationReport.from_dict(d)
        assert restored.is_valid == val.is_valid
        assert restored.report_id == val.report_id


# ---------------------------------------------------------------------------
# SECTION 10 — Report Repository
# ---------------------------------------------------------------------------


class TestReportRepository:
    def test_save_and_get(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        report = InvestorReporter().build(sample_decision)
        report_repo.save(report)
        loaded = report_repo.get(report.report_id, "INVESTOR")
        assert loaded is not None
        assert loaded.report_id == report.report_id

    def test_save_many(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        reports = [
            InvestorReporter().build(sample_decision),
            BusinessReporter().build(sample_decision),
            PublicReporter().build(sample_decision),
        ]
        paths = report_repo.save_many(reports)
        assert len(paths) == 3
        assert all(p.exists() for p in paths)

    def test_exists_true(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        report = InvestorReporter().build(sample_decision)
        report_repo.save(report)
        assert report_repo.exists(
            sample_decision.bill_id,
            sample_decision.company_isin,
            sample_decision.event_window,
            "INVESTOR",
        )

    def test_exists_false(self, report_repo: ReportRepository):
        assert not report_repo.exists("no-bill", "NO_ISIN", "[-20,+20]", "INVESTOR")

    def test_get_returns_none_for_missing(self, report_repo: ReportRepository):
        result = report_repo.get("nonexistent_id", "INVESTOR")
        assert result is None

    def test_get_by_bill(
        self,
        report_repo: ReportRepository,
        sample_decision: DecisionSupportRecord,
        negative_decision: DecisionSupportRecord,
    ):
        r1 = InvestorReporter().build(sample_decision)
        r2 = InvestorReporter().build(negative_decision)
        report_repo.save(r1)
        report_repo.save(r2)
        results = report_repo.get_by_bill(sample_decision.bill_id)
        assert any(r.bill_id == sample_decision.bill_id for r in results)

    def test_get_by_company(
        self,
        report_repo: ReportRepository,
        sample_decision: DecisionSupportRecord,
        negative_decision: DecisionSupportRecord,
    ):
        r1 = InvestorReporter().build(sample_decision)
        r2 = InvestorReporter().build(negative_decision)
        report_repo.save(r1)
        report_repo.save(r2)
        results = report_repo.get_by_company(sample_decision.company_isin)
        assert any(r.company_isin == sample_decision.company_isin for r in results)

    def test_load_all(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        reports = [
            InvestorReporter().build(sample_decision),
            BusinessReporter().build(sample_decision),
            PublicReporter().build(sample_decision),
        ]
        for r in reports:
            report_repo.save(r)
        all_reports = report_repo.load_all()
        assert len(all_reports) >= 3

    def test_load_all_by_stakeholder_type(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        inv = InvestorReporter().build(sample_decision)
        bus = BusinessReporter().build(sample_decision)
        report_repo.save(inv)
        report_repo.save(bus)
        investor_only = report_repo.load_all(stakeholder_type="INVESTOR")
        assert all(r.stakeholder_type == "INVESTOR" for r in investor_only)

    def test_save_and_load_bill_report(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        agg = BillAggregator()
        bill_rpt = agg.build("test-bill", [sample_decision])
        report_repo.save_bill_report(bill_rpt)
        loaded = report_repo.get_bill_report(bill_rpt.report_id)
        assert loaded is not None
        assert loaded.bill_id == "test-bill"

    def test_save_and_load_company_report(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        agg = CompanyAggregator()
        co_rpt = agg.build(sample_decision.company_isin, [sample_decision])
        report_repo.save_company_report(co_rpt)
        loaded = report_repo.get_company_report(co_rpt.report_id)
        assert loaded is not None
        assert loaded.company_isin == sample_decision.company_isin

    def test_save_validation_report(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        report = InvestorReporter().build(sample_decision)
        validator = ReportValidator()
        val = validator.validate(report)
        report_repo.save_validation_report(val)
        loaded = report_repo.load_all_validation_reports()
        assert any(v.report_id == val.report_id for v in loaded)

    def test_load_all_bill_reports(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        agg = BillAggregator()
        bill_rpt = agg.build("bill-1", [sample_decision])
        report_repo.save_bill_report(bill_rpt)
        all_bill_rpts = report_repo.load_all_bill_reports()
        assert len(all_bill_rpts) >= 1

    def test_load_all_company_reports(
        self, report_repo: ReportRepository, sample_decision: DecisionSupportRecord
    ):
        agg = CompanyAggregator()
        co_rpt = agg.build(sample_decision.company_isin, [sample_decision])
        report_repo.save_company_report(co_rpt)
        all_co_rpts = report_repo.load_all_company_reports()
        assert len(all_co_rpts) >= 1


# ---------------------------------------------------------------------------
# SECTION 11 — Incremental Execution
# ---------------------------------------------------------------------------


class TestIncrementalExecution:
    def test_skips_when_version_unchanged(
        self,
        tmp_reports_dir: Path,
        sample_decision: DecisionSupportRecord,
    ):
        """If decision_version unchanged, engine returns SKIPPED."""
        from reporting.engine import ReportingEngine
        from storage.report_repository import ReportRepository

        repo = ReportRepository(reports_dir=tmp_reports_dir)

        # Pre-save a report
        report = InvestorReporter().build(sample_decision)
        repo.save(report)

        engine = ReportingEngine(
            report_repo=repo,
        )

        from schemas.report import StakeholderType
        result = engine._generate_single(
            decision=sample_decision,
            stakeholder_type=StakeholderType.INVESTOR,
            bill=None,
            company=None,
            top_factors=None,
            output_format="JSON",
            force_refresh=False,
        )
        assert result == "SKIPPED"

    def test_regenerates_when_force_refresh(
        self,
        tmp_reports_dir: Path,
        sample_decision: DecisionSupportRecord,
    ):
        """force_refresh=True regenerates even when version unchanged."""
        from reporting.engine import ReportingEngine
        from storage.report_repository import ReportRepository

        repo = ReportRepository(reports_dir=tmp_reports_dir)
        report = InvestorReporter().build(sample_decision)
        repo.save(report)

        engine = ReportingEngine(report_repo=repo)
        result = engine._generate_single(
            decision=sample_decision,
            stakeholder_type=StakeholderType.INVESTOR,
            bill=None,
            company=None,
            top_factors=None,
            output_format="JSON",
            force_refresh=True,
        )
        assert isinstance(result, StakeholderReport)

    def test_regenerates_when_version_changes(
        self,
        tmp_reports_dir: Path,
        sample_decision: DecisionSupportRecord,
    ):
        """If decision_version changes, engine regenerates."""
        from reporting.engine import ReportingEngine
        from storage.report_repository import ReportRepository

        repo = ReportRepository(reports_dir=tmp_reports_dir)

        # Save a report with old version
        old_report = InvestorReporter().build(sample_decision)
        old_report.decision_version = "v0.9"
        repo.save(old_report)

        # Now decision has a newer version
        new_decision = DecisionSupportRecord(
            **{**sample_decision.__dict__, "decision_version": "v1.1"}
        )

        engine = ReportingEngine(report_repo=repo)
        result = engine._generate_single(
            decision=new_decision,
            stakeholder_type=StakeholderType.INVESTOR,
            bill=None,
            company=None,
            top_factors=None,
            output_format="JSON",
            force_refresh=False,
        )
        assert isinstance(result, StakeholderReport)

    def test_generates_when_not_exists(
        self,
        tmp_reports_dir: Path,
        sample_decision: DecisionSupportRecord,
    ):
        """When no cached report, generates fresh."""
        from reporting.engine import ReportingEngine

        repo = ReportRepository(reports_dir=tmp_reports_dir)
        engine = ReportingEngine(report_repo=repo)

        result = engine._generate_single(
            decision=sample_decision,
            stakeholder_type=StakeholderType.INVESTOR,
            bill=None,
            company=None,
            top_factors=None,
            output_format="JSON",
            force_refresh=False,
        )
        assert isinstance(result, StakeholderReport)


# ---------------------------------------------------------------------------
# SECTION 12 — Disclaimer Generation
# ---------------------------------------------------------------------------


class TestDisclaimerGeneration:
    def test_investor_disclaimer_present_and_correct(
        self, sample_decision: DecisionSupportRecord
    ):
        report = InvestorReporter().build(sample_decision)
        assert REPORT_DISCLAIMER in report.disclaimer or "academic" in report.disclaimer.lower()

    def test_business_disclaimer_present(self, sample_decision: DecisionSupportRecord):
        report = BusinessReporter().build(sample_decision)
        assert report.disclaimer != ""

    def test_public_disclaimer_present_and_plain(self, sample_decision: DecisionSupportRecord):
        report = PublicReporter().build(sample_decision)
        assert report.disclaimer != ""
        # Public disclaimer should be more accessible
        assert "educational" in report.disclaimer.lower() or "information" in report.disclaimer.lower()

    def test_methodology_note_in_all_reporters(self, sample_decision: DecisionSupportRecord):
        for reporter_cls in [InvestorReporter, BusinessReporter, PublicReporter]:
            report = reporter_cls().build(sample_decision)
            assert report.methodology_note != ""


# ---------------------------------------------------------------------------
# SECTION 13 — Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_score_at_boundary_zero(self, sample_decision: DecisionSupportRecord):
        """Scores at 0.0 should not cause errors."""
        d = DecisionSupportRecord(**{
            **sample_decision.__dict__,
            "impact_score": 0.0,
            "risk_score": 0.0,
            "anticipation_score": 0.0,
            "confidence_score": 0.0,
        })
        report = InvestorReporter().build(d)
        assert "0.0000" in report.impact_summary or "0.00" in report.impact_summary

    def test_score_at_boundary_one(self, sample_decision: DecisionSupportRecord):
        """Scores at 1.0 should not cause errors."""
        d = DecisionSupportRecord(**{
            **sample_decision.__dict__,
            "impact_score": 1.0,
            "risk_score": 1.0,
            "anticipation_score": 1.0,
            "confidence_score": 1.0,
            "market_moving_probability": 1.0,
        })
        report = InvestorReporter().build(d)
        assert "1.0000" in report.impact_summary or "100" in report.impact_summary

    def test_very_high_risk_category(self, sample_decision: DecisionSupportRecord):
        d = DecisionSupportRecord(**{
            **sample_decision.__dict__,
            "risk_category": "VERY_HIGH",
        })
        report = BusinessReporter().build(d)
        assert "significant" in report.risk_summary.lower() or "high" in report.risk_summary.lower()

    def test_not_analyzed_anticipation(self, sample_decision: DecisionSupportRecord):
        d = DecisionSupportRecord(**{
            **sample_decision.__dict__,
            "anticipation_class": "NOT_ANALYZED",
            "anticipation_score": 0.0,
        })
        report = InvestorReporter().build(d)
        assert "not analyzed" in report.anticipation_summary.lower() or "not performed" in report.anticipation_summary.lower()

    def test_weak_evidence_anticipation(self, sample_decision: DecisionSupportRecord):
        d = DecisionSupportRecord(**{
            **sample_decision.__dict__,
            "anticipation_class": "WEAK_EVIDENCE",
            "anticipation_score": 0.30,
        })
        report = InvestorReporter().build(d)
        assert "weak" in report.anticipation_summary.lower() or "limited" in report.anticipation_summary.lower()

    def test_missing_company_metadata_graceful(self, sample_decision: DecisionSupportRecord):
        """Missing company (None) does not crash any reporter."""
        for reporter_cls in [InvestorReporter, BusinessReporter, PublicReporter]:
            report = reporter_cls().build(sample_decision, company=None)
            assert report.company_summary != ""

    def test_missing_bill_metadata_graceful(self, sample_decision: DecisionSupportRecord):
        """Missing bill (None) does not crash any reporter."""
        for reporter_cls in [InvestorReporter, BusinessReporter, PublicReporter]:
            report = reporter_cls().build(sample_decision, bill=None)
            assert report.bill_summary != ""

    def test_report_id_is_prefix_rpt(self, sample_decision: DecisionSupportRecord):
        report = InvestorReporter().build(sample_decision)
        assert report.report_id.startswith("rpt_")

    def test_stakeholder_type_is_uppercase(self, sample_decision: DecisionSupportRecord):
        for reporter_cls, expected in [
            (InvestorReporter, "INVESTOR"),
            (BusinessReporter, "BUSINESS"),
            (PublicReporter, "PUBLIC"),
        ]:
            report = reporter_cls().build(sample_decision)
            assert report.stakeholder_type == expected

    def test_probability_formatting_no_key_missing(self):
        """Empty direction_probability dict handled gracefully."""
        decision = DecisionSupportRecord(
            decision_id="dec_test2",
            bill_id="test-bill",
            company_isin="INE_X",
            event_window="[-20,+20]",
            predicted_direction="POSITIVE",
            direction_probability={},  # Empty — all get() return 0.0
            market_moving_probability=0.50,
            predicted_impact_strength="LOW",
            impact_probabilities={},
            predicted_confidence="LOW",
            confidence_probability={},
            confidence_score=0.0,
            anticipation_class="NO_EVIDENCE",
            anticipation_score=0.0,
            impact_score=0.0,
            impact_category="LOW",
            risk_score=0.0,
            risk_category="VERY_LOW",
            pricing_in_risk="VERY_LOW",
            pricing_in_score=0.0,
            investor_summary="",
            business_summary="",
            public_summary="",
            decision_reason="",
            model_version="v1.0",
            feature_version="v1.0",
        )
        report = InvestorReporter().build(decision)
        assert report is not None
        # Impact summary should still render (with 0% values)
        assert "0%" in report.impact_summary or "0.0%" in report.impact_summary


# ---------------------------------------------------------------------------
# SECTION 14 — ReportingEngine full API coverage
# ---------------------------------------------------------------------------


class TestReportingEngineAPI:
    """
    Tests for the ReportingEngine generate_all, generate_for_decision,
    generate_bill_report, generate_company_report, and format_report paths.
    Uses mocked repositories to avoid needing real data.
    """

    @pytest.fixture
    def mock_engine(
        self,
        sample_decision: DecisionSupportRecord,
        tmp_reports_dir: Path,
    ):
        """Engine with mocked decision_repo returning one sample decision."""
        from reporting.engine import ReportingEngine
        from storage.report_repository import ReportRepository

        mock_decision_repo = MagicMock()
        mock_decision_repo.load_all.return_value = [sample_decision]
        mock_decision_repo.get_by_bill.return_value = [sample_decision]
        mock_decision_repo.get_by_company.return_value = [sample_decision]

        mock_bill_repo = MagicMock()
        mock_bill_repo.get.return_value = None

        mock_company_repo = MagicMock()
        mock_company_repo.get_by_isin.return_value = None

        mock_mapping_repo = MagicMock()
        mock_mapping_repo.get.return_value = None

        repo = ReportRepository(reports_dir=tmp_reports_dir)

        engine = ReportingEngine(
            decision_repo=mock_decision_repo,
            bill_repo=mock_bill_repo,
            company_repo=mock_company_repo,
            mapping_repo=mock_mapping_repo,
            report_repo=repo,
        )
        return engine

    def test_generate_all_returns_stats(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        stats = mock_engine.generate_all()
        assert "total_candidates" in stats
        assert "reports_generated" in stats
        assert stats["total_candidates"] == 1

    def test_generate_all_with_bill_filter(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        stats = mock_engine.generate_all(
            bill_id_filter=sample_decision.bill_id
        )
        assert stats["total_candidates"] == 1

    def test_generate_all_with_mismatched_bill_filter(
        self, mock_engine
    ):
        """Filter that matches nothing produces 0 candidates."""
        stats = mock_engine.generate_all(bill_id_filter="nonexistent-bill")
        assert stats["total_candidates"] == 0
        assert stats["reports_generated"] == 0

    def test_generate_all_with_isin_filter(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        stats = mock_engine.generate_all(
            company_isin_filter=sample_decision.company_isin
        )
        assert stats["total_candidates"] == 1

    def test_generate_all_with_event_window_filter(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        stats = mock_engine.generate_all(
            event_window_filter=sample_decision.event_window
        )
        assert stats["total_candidates"] == 1

    def test_generate_all_with_event_window_mismatch(
        self, mock_engine
    ):
        stats = mock_engine.generate_all(event_window_filter="[-99,+99]")
        assert stats["total_candidates"] == 0

    def test_generate_all_single_stakeholder(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        stats = mock_engine.generate_all(stakeholder_filter="INVESTOR")
        assert stats["stakeholder_types"] == ["INVESTOR"]

    def test_generate_all_business_stakeholder(
        self, mock_engine
    ):
        stats = mock_engine.generate_all(stakeholder_filter="BUSINESS")
        assert stats["stakeholder_types"] == ["BUSINESS"]

    def test_generate_all_public_stakeholder(
        self, mock_engine
    ):
        stats = mock_engine.generate_all(stakeholder_filter="PUBLIC")
        assert stats["stakeholder_types"] == ["PUBLIC"]

    def test_generate_all_unknown_stakeholder_generates_all(
        self, mock_engine
    ):
        """Unknown stakeholder_filter falls back to generating all three types."""
        stats = mock_engine.generate_all(stakeholder_filter="UNKNOWN_TYPE")
        assert len(stats["stakeholder_types"]) == 3

    def test_generate_all_markdown_format(
        self, mock_engine
    ):
        stats = mock_engine.generate_all(
            stakeholder_filter="INVESTOR", output_format="MARKDOWN"
        )
        assert stats["total_candidates"] == 1

    def test_generate_all_csv_format(
        self, mock_engine
    ):
        stats = mock_engine.generate_all(
            stakeholder_filter="INVESTOR", output_format="CSV"
        )
        assert stats["total_candidates"] == 1

    def test_generate_all_force_refresh(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        """force_refresh=True should still generate (not skip)."""
        # First call — generates
        stats1 = mock_engine.generate_all(stakeholder_filter="INVESTOR")
        assert stats1["reports_generated"] >= 1
        # Second call — force refresh, so it should generate again not skip
        stats2 = mock_engine.generate_all(
            stakeholder_filter="INVESTOR", force_refresh=True
        )
        assert stats2["reports_generated"] >= 1
        assert stats2["reports_skipped"] == 0

    def test_generate_all_skip_on_second_run(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        """Second run without force_refresh should skip cached reports."""
        stats1 = mock_engine.generate_all(stakeholder_filter="INVESTOR")
        assert stats1["reports_generated"] == 1
        stats2 = mock_engine.generate_all(stakeholder_filter="INVESTOR")
        assert stats2["reports_skipped"] == 1
        assert stats2["reports_generated"] == 0

    def test_generate_for_decision_investor(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        report = mock_engine.generate_for_decision(
            sample_decision, StakeholderType.INVESTOR
        )
        assert isinstance(report, StakeholderReport)
        assert report.stakeholder_type == "INVESTOR"

    def test_generate_for_decision_business(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        report = mock_engine.generate_for_decision(
            sample_decision, StakeholderType.BUSINESS
        )
        assert isinstance(report, StakeholderReport)
        assert report.stakeholder_type == "BUSINESS"

    def test_generate_for_decision_public(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        report = mock_engine.generate_for_decision(
            sample_decision, StakeholderType.PUBLIC
        )
        assert isinstance(report, StakeholderReport)
        assert report.stakeholder_type == "PUBLIC"

    def test_generate_bill_report(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        bill_rpt = mock_engine.generate_bill_report(sample_decision.bill_id)
        assert isinstance(bill_rpt, BillLevelReport)
        assert bill_rpt.bill_id == sample_decision.bill_id

    def test_generate_company_report(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        co_rpt = mock_engine.generate_company_report(sample_decision.company_isin)
        assert isinstance(co_rpt, CompanyLevelReport)
        assert co_rpt.company_isin == sample_decision.company_isin

    def test_format_report_json(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        report = InvestorReporter().build(sample_decision)
        result = mock_engine.format_report(report, "JSON")
        data = json.loads(result)
        assert "bill_id" in data

    def test_format_report_markdown(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        report = InvestorReporter().build(sample_decision)
        result = mock_engine.format_report(report, "MARKDOWN")
        assert "# Legislative Market Impact Report" in result

    def test_format_report_csv(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        report = InvestorReporter().build(sample_decision)
        result = mock_engine.format_report(report, "CSV")
        assert "report_id" in result

    def test_format_report_unknown_format_defaults_json(
        self, mock_engine, sample_decision: DecisionSupportRecord
    ):
        """Unknown format should fall back to JSON."""
        report = InvestorReporter().build(sample_decision)
        result = mock_engine.format_report(report, "XLSX")
        data = json.loads(result)
        assert "bill_id" in data

    def test_get_top_factors_with_explainability_repo(
        self, tmp_reports_dir, sample_decision: DecisionSupportRecord
    ):
        """ExplainabilityRepository mock returns SHAP features."""
        from reporting.engine import ReportingEngine

        mock_explainability = MagicMock()
        mock_explainability.load_global_summary.return_value = {
            "top_features": [
                {"feature": "sector_exposure", "importance": 0.30},
                {"feature": "bill_complexity", "importance": 0.20},
            ]
        }

        mock_decision_repo = MagicMock()
        mock_decision_repo.load_all.return_value = [sample_decision]

        engine = ReportingEngine(
            decision_repo=mock_decision_repo,
            report_repo=ReportRepository(reports_dir=tmp_reports_dir),
            explainability_repo=mock_explainability,
        )

        factors = engine._get_top_factors(sample_decision.company_isin, {})
        assert factors is not None
        assert "sector_exposure" in factors

    def test_get_top_factors_without_explainability_repo(
        self, tmp_reports_dir
    ):
        """Without explainability repo, returns None."""
        from reporting.engine import ReportingEngine
        engine = ReportingEngine(
            report_repo=ReportRepository(reports_dir=tmp_reports_dir),
            explainability_repo=None,
        )
        result = engine._get_top_factors("INE001", {})
        assert result is None

    def test_get_top_factors_repo_exception_returns_none(
        self, tmp_reports_dir
    ):
        """When explainability repo raises, returns None gracefully."""
        from reporting.engine import ReportingEngine

        mock_explainability = MagicMock()
        mock_explainability.load_global_summary.side_effect = RuntimeError("io error")

        engine = ReportingEngine(
            report_repo=ReportRepository(reports_dir=tmp_reports_dir),
            explainability_repo=mock_explainability,
        )
        result = engine._get_top_factors("INE001", {})
        assert result is None

    def test_get_top_factors_cached(
        self, tmp_reports_dir
    ):
        """Second call returns cached result without hitting repo again."""
        from reporting.engine import ReportingEngine

        mock_explainability = MagicMock()
        mock_explainability.load_global_summary.return_value = {
            "top_features": [{"feature": "f1"}, {"feature": "f2"}]
        }
        engine = ReportingEngine(
            report_repo=ReportRepository(reports_dir=tmp_reports_dir),
            explainability_repo=mock_explainability,
        )
        cache: dict = {}
        engine._get_top_factors("INE001", cache)
        engine._get_top_factors("INE001", cache)
        # Should only be called once (cache hit on second call)
        mock_explainability.load_global_summary.assert_called_once()

    def test_generate_single_returns_none_on_validation_failure(
        self, tmp_reports_dir
    ):
        """When validation fails (empty fields), _generate_single returns None."""
        from reporting.engine import ReportingEngine

        engine = ReportingEngine(
            report_repo=ReportRepository(reports_dir=tmp_reports_dir),
        )

        # Build a minimal decision that will pass generation but fail validator
        bad_decision = DecisionSupportRecord(
            decision_id="",
            bill_id="",  # missing — validator will error
            company_isin="INE001",
            event_window="bad_format",
            predicted_direction="POSITIVE",
            direction_probability={"POSITIVE": 0.80},
            market_moving_probability=0.70,
            predicted_impact_strength="HIGH",
            impact_probabilities={},
            predicted_confidence="HIGH",
            confidence_probability={},
            confidence_score=0.70,
            anticipation_class="NO_EVIDENCE",
            anticipation_score=0.0,
            impact_score=0.60,
            impact_category="HIGH",
            risk_score=0.40,
            risk_category="MODERATE",
            pricing_in_risk="LOW",
            pricing_in_score=0.20,
            investor_summary="",
            business_summary="",
            public_summary="",
            decision_reason="",
            model_version="v1.0",
            feature_version="v1.0",
        )

        result = engine._generate_single(
            decision=bad_decision,
            stakeholder_type=StakeholderType.INVESTOR,
            bill=None,
            company=None,
            top_factors=None,
            output_format="JSON",
            force_refresh=True,
        )
        assert result is None


# ---------------------------------------------------------------------------
# SECTION 15 — Formatter additional branch coverage
# ---------------------------------------------------------------------------


class TestFormatterAdditionalCoverage:
    def test_to_json_bill_report(self, sample_decision: DecisionSupportRecord):
        agg = BillAggregator()
        bill_rpt = agg.build("test-bill", [sample_decision])
        fmt = ReportFormatter()
        json_str = fmt.to_json(bill_rpt)
        data = json.loads(json_str)
        assert data["bill_id"] == "test-bill"

    def test_to_json_company_report(self, sample_decision: DecisionSupportRecord):
        agg = CompanyAggregator()
        co_rpt = agg.build(sample_decision.company_isin, [sample_decision])
        fmt = ReportFormatter()
        json_str = fmt.to_json(co_rpt)
        data = json.loads(json_str)
        assert data["company_isin"] == sample_decision.company_isin

    def test_to_markdown_company_with_high_impact_bills(
        self, sample_decision: DecisionSupportRecord
    ):
        high = DecisionSupportRecord(**{
            **sample_decision.__dict__,
            "impact_category": "VERY_HIGH",
        })
        agg = CompanyAggregator()
        co_rpt = agg.build(sample_decision.company_isin, [high])
        fmt = ReportFormatter()
        md = fmt.to_markdown(co_rpt)
        assert "## High-Impact Bills" in md

    def test_to_csv_bill_with_sectors(self, sample_decision: DecisionSupportRecord):
        r = DecisionSupportRecord(**{**sample_decision.__dict__, "sector": "Banking"})
        agg = BillAggregator()
        bill_rpt = agg.build("b", [r])
        fmt = ReportFormatter()
        csv_str = fmt.to_csv_summary([bill_rpt], report_type="bill")
        assert "Banking" in csv_str

    def test_to_markdown_unknown_type_falls_back_to_json(self):
        """Unknown report type passed to to_markdown returns JSON-like output."""
        fmt = ReportFormatter()
        # Create a mock object that has a to_dict method but isn't any of the three types
        mock_rpt = MagicMock()
        mock_rpt.to_dict.return_value = {"test": "data"}
        # Should not raise, should return something
        result = fmt.to_markdown(mock_rpt)
        assert result is not None


# ---------------------------------------------------------------------------
# SECTION 16 — Validator additional edge cases
# ---------------------------------------------------------------------------


class TestValidatorEdgeCases:
    def test_version_mismatch_produces_warning(
        self, sample_decision: DecisionSupportRecord
    ):
        """Version mismatch between report and engine produces a warning."""
        reporter = InvestorReporter(report_version="v9.9")
        report = reporter.build(sample_decision)
        validator = ReportValidator(current_report_version="v1.0")
        val = validator.validate(report)
        # Version mismatch → warning, not error
        assert any("version" in w.lower() for w in val.warnings)

    def test_empty_key_factors_warning(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        report.key_factors = []
        validator = ReportValidator()
        val = validator.validate(report)
        assert any("key_factors" in w.lower() for w in val.warnings)

    def test_missing_disclaimer_warning(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        report.disclaimer = ""
        validator = ReportValidator()
        val = validator.validate(report)
        assert any("disclaimer" in w.lower() for w in val.warnings)

    def test_missing_methodology_note_warning(
        self, sample_decision: DecisionSupportRecord
    ):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        report.methodology_note = ""
        validator = ReportValidator()
        val = validator.validate(report)
        assert any("methodology" in w.lower() for w in val.warnings)

    def test_short_bill_summary_warning(self, sample_decision: DecisionSupportRecord):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        report.bill_summary = "short"
        validator = ReportValidator()
        val = validator.validate(report)
        assert any("bill_summary" in w.lower() or "short" in w.lower() for w in val.warnings)

    def test_validation_report_to_dict_from_dict_roundtrip(
        self, sample_decision: DecisionSupportRecord
    ):
        reporter = InvestorReporter()
        report = reporter.build(sample_decision)
        validator = ReportValidator()
        val = validator.validate(report)
        d = val.to_dict()
        assert isinstance(d["is_valid"], bool)
        restored = ReportValidationReport.from_dict(d)
        assert restored.validation_id == val.validation_id
        assert restored.is_valid == val.is_valid
        assert restored.errors == val.errors


# ---------------------------------------------------------------------------
# SECTION 17 — ReportingService & CLI Tests
# ---------------------------------------------------------------------------


class TestReportingServiceAndCLI:
    def test_reporting_service_methods(
        self, sample_decision: DecisionSupportRecord, tmp_reports_dir: Path
    ):
        from reporting.engine import ReportingEngine
        from services.reporting_service import ReportingService
        from storage.report_repository import ReportRepository

        mock_decision_repo = MagicMock()
        mock_decision_repo.load_all.return_value = [sample_decision]
        mock_decision_repo.get_by_bill.return_value = [sample_decision]
        mock_decision_repo.get_by_company.return_value = [sample_decision]

        repo = ReportRepository(reports_dir=tmp_reports_dir)
        engine = ReportingEngine(
            decision_repo=mock_decision_repo,
            report_repo=repo,
        )
        service = ReportingService(engine=engine)

        stats = service.generate_reports(
            bill_id=sample_decision.bill_id,
            company_isin=sample_decision.company_isin,
            stakeholder="investor",
            event_window="[-20,+20]",
            output_format="json",
            force_refresh=True,
        )
        assert stats["reports_generated"] == 1

        bill_rpt = service.generate_bill_report(sample_decision.bill_id)
        assert bill_rpt.bill_id == sample_decision.bill_id

        co_rpt = service.generate_company_report(sample_decision.company_isin)
        assert co_rpt.company_isin == sample_decision.company_isin

        formatted = service.format_report(bill_rpt, "markdown")
        assert "Bill-Level Market Impact Summary" in formatted

    def test_cmd_generate_reports_cli(
        self, sample_decision: DecisionSupportRecord, tmp_reports_dir: Path
    ):
        import argparse
        from main import cmd_generate_reports

        with patch("services.reporting_service.ReportingEngine") as MockEngineCls:
            mock_engine = MagicMock()
            MockEngineCls.return_value = mock_engine
            mock_engine.generate_all.return_value = {
                "total_candidates": 1,
                "stakeholder_types": ["INVESTOR"],
                "reports_generated": 1,
                "reports_skipped": 0,
                "reports_failed": 0,
                "validation_failures": 0,
                "reports": [InvestorReporter().build(sample_decision)],
            }
            mock_engine.generate_bill_report.return_value = BillAggregator().build(
                sample_decision.bill_id, [sample_decision]
            )
            mock_engine.generate_company_report.return_value = CompanyAggregator().build(
                sample_decision.company_isin, [sample_decision]
            )

            args = argparse.Namespace(
                bill_id=sample_decision.bill_id,
                company_isin=sample_decision.company_isin,
                stakeholder="investor",
                event_window="[-20,+20]",
                format="json",
                force_refresh=True,
                rebuild=False,
                generate_bill=True,
                generate_company=True,
            )

            exit_code = cmd_generate_reports(args)
            assert exit_code == 0

    def test_cmd_generate_reports_cli_failure(self):
        import argparse
        from main import cmd_generate_reports

        with patch("services.reporting_service.ReportingEngine") as MockEngineCls:
            mock_engine = MagicMock()
            MockEngineCls.return_value = mock_engine
            mock_engine.generate_all.side_effect = RuntimeError("Fatal engine error")

            args = argparse.Namespace(
                bill_id="bad_bill",
                company_isin=None,
                stakeholder=None,
                event_window=None,
                format="json",
                force_refresh=False,
                rebuild=False,
                generate_bill=False,
                generate_company=False,
            )

            exit_code = cmd_generate_reports(args)
            assert exit_code == 1

    def test_report_repository_corrupt_files_handled(self, tmp_reports_dir: Path):
        from storage.report_repository import ReportRepository

        repo = ReportRepository(reports_dir=tmp_reports_dir)
        # Write corrupted json files
        inv_dir = tmp_reports_dir / "investor"
        inv_dir.mkdir(parents=True, exist_ok=True)
        bad_file = inv_dir / "rpt_corrupted.json"
        bad_file.write_text("invalid json content")

        reports = repo.load_all(stakeholder_type="INVESTOR")
        assert reports == []

        res = repo.get("rpt_corrupted", "INVESTOR")
        assert res is None

        bill_dir = tmp_reports_dir / "bill_reports"
        bill_dir.mkdir(parents=True, exist_ok=True)
        (bill_dir / "bill_rpt_bad.json").write_text("{bad json")
        assert repo.get_bill_report("bill_rpt_bad") is None
        assert repo.load_all_bill_reports() == []

        co_dir = tmp_reports_dir / "company_reports"
        co_dir.mkdir(parents=True, exist_ok=True)
        (co_dir / "co_rpt_bad.json").write_text("{bad json")
        assert repo.get_company_report("co_rpt_bad") is None
        assert repo.load_all_company_reports() == []

        val_dir = tmp_reports_dir / "validation"
        val_dir.mkdir(parents=True, exist_ok=True)
        (val_dir / "val_bad.json").write_text("{bad json")
        assert repo.load_all_validation_reports() == []


