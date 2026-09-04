"""
tests/test_anticipation.py
==========================
Comprehensive test suite for Task 6.5: Anticipation Bias / Pre-Event Information Analysis.

Targeting >95% code coverage across all anticipation modules.
"""

from __future__ import annotations

import datetime
from pathlib import Path
import math
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
import pytest

from schemas.bill import Bill, BillHouse, BillStatus
from schemas.company import Company, MarketCapCategory
from schemas.market_model import MarketModelRecord
from schemas.anticipation import (
    AnticipationClassification,
    AnticipationScore,
    AnticipationValidationReport,
    BillAnticipationRecord,
    EvidenceConfidence,
    EvidenceType,
    InformationEvidence,
    PreEventWindowStats,
)
from storage.anticipation_repository import AnticipationRepository, sanitize_id
from validation.anticipation_validator import AnticipationValidator
from anticipation.market_analyzer import PreEventMarketAnalyzer, parse_window_offsets
from anticipation.signal_detector import PreEventSignalDetector
from anticipation.scorer import AnticipationScorer
from anticipation.engine import AnticipationBiasEngine
from services.anticipation_service import AnticipationService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_bill() -> Bill:
    return Bill(
        bill_id="test-finance-bill-2024",
        title="The Test Finance Bill, 2024",
        bill_number="101/2024",
        year=2024,
        ministry="Ministry of Finance",
        house=BillHouse.LOK_SABHA,
        status=BillStatus.INTRODUCED,
        introduction_date=datetime.date(2024, 2, 1),
        url="https://prsindia.org/bills/test-finance-bill-2024",
        sectors=["Banking", "Financial Services"],
    )


@pytest.fixture
def sample_company() -> Company:
    return Company(
        isin="INE002A01018",
        company_name="State Bank of India",
        ticker_nse="SBIN",
        ticker_bse="500112",
        sector="Financial Services",
        industry="Public Sector Bank",
        market_cap_cr=650000.0,
        market_cap_category=MarketCapCategory.LARGE_CAP,
    )


@pytest.fixture
def sample_company_bse_only() -> Company:
    return Company(
        isin="INE999B01099",
        company_name="BSE Only Company",
        ticker_nse="",
        ticker_bse="599999",
        sector="Industrials",
        industry="Machinery",
        market_cap_cr=5000.0,
        market_cap_category=MarketCapCategory.SMALL_CAP,
    )


@pytest.fixture
def sample_company_no_ticker() -> Company:
    return Company(
        isin="INE000X01000",
        company_name="No Ticker Company",
        ticker_nse="",
        ticker_bse="",
        sector="Unknown",
        industry="Unknown",
        market_cap_cr=100.0,
        market_cap_category=MarketCapCategory.SMALL_CAP,
    )


@pytest.fixture
def sample_market_model() -> MarketModelRecord:
    return MarketModelRecord(
        company_isin="INE002A01018",
        company_symbol="SBIN",
        bill_id="test-finance-bill-2024",
        alpha=0.0005,
        beta=1.15,
        r_squared=0.45,
        residual_variance=0.00015,
        standard_error=0.0122,
        beta_stderr=0.08,
        alpha_stderr=0.0004,
        n_observations=250,
        estimation_window={"start_date": "2023-01-01", "end_date": "2023-12-15"},
        estimation_date="2024-01-01T00:00:00Z",
        benchmark_symbol="^NSEI",
    )


@pytest.fixture
def mock_trading_data() -> tuple[list[str], pd.Series, pd.Series]:
    """Generate 100 trading days of simulated returns around 2024-02-01."""
    date_range = pd.date_range("2023-10-01", "2024-03-01", freq="B")
    trading_dates = [d.strftime("%Y-%m-%d") for d in date_range]

    np.random.seed(42)
    n = len(date_range)
    bmk_ret = np.random.normal(0.0005, 0.010, n)
    cmp_ret = 0.0005 + 1.15 * bmk_ret + np.random.normal(0.0, 0.008, n)

    t0_dt = pd.to_datetime("2024-02-01")
    for i, dt in enumerate(date_range):
        if dt < t0_dt and (t0_dt - dt).days <= 40:
            cmp_ret[i] += 0.004

    bmk_series = pd.Series(bmk_ret, index=date_range)
    cmp_series = pd.Series(cmp_ret, index=date_range)

    return trading_dates, cmp_series, bmk_series


# ---------------------------------------------------------------------------
# 1. Schema Tests
# ---------------------------------------------------------------------------


class TestAnticipationSchemas:
    def test_pre_event_window_stats_roundtrip(self):
        stats = PreEventWindowStats(
            window="[-30,-21]",
            start_offset=-30,
            end_offset=-21,
            start_date="2023-12-15",
            end_date="2023-12-28",
            mean_abnormal_return=0.0025,
            cumulative_abnormal_return=0.0250,
            volatility=0.0085,
            ar_z_score=2.15,
            observation_count=10,
            pct_positive_ar=0.70,
            pct_negative_ar=0.30,
            daily_dates=["2023-12-15", "2023-12-18"],
            daily_ar=[0.002, 0.003],
            daily_car=[0.002, 0.005],
            is_statistically_significant=True,
            p_value=0.0315,
        )
        d = stats.to_dict()
        assert d["window"] == "[-30,-21]"
        assert d["is_statistically_significant"] is True
        assert d["daily_dates"] == ["2023-12-15", "2023-12-18"]

        restored = PreEventWindowStats.from_dict(d)
        assert restored.window == stats.window
        assert restored.mean_abnormal_return == stats.mean_abnormal_return
        assert restored.observation_count == 10
        assert restored.is_statistically_significant is True

    def test_information_evidence_roundtrip(self):
        ev = InformationEvidence(
            bill_id="test-finance-bill-2024",
            source="Economic Times",
            publication_date="2024-01-15",
            headline="Govt mulls major banking reforms ahead of Budget session",
            source_url="https://economictimes.com/news/123",
            relevance_score=0.92,
            evidence_type=EvidenceType.NEWS.value,
            evidence_timestamp="2024-01-15T08:30:00Z",
            confidence=EvidenceConfidence.HIGH.value,
        )
        d = ev.to_dict()
        assert d["source"] == "Economic Times"
        assert d["relevance_score"] == 0.92

        restored = InformationEvidence.from_dict(d)
        assert restored.headline == ev.headline
        assert restored.confidence == "HIGH"

    def test_anticipation_score_roundtrip(self):
        win_stat = PreEventWindowStats(
            window="[-30,-1]",
            start_offset=-30,
            end_offset=-1,
            start_date="2023-12-15",
            end_date="2024-01-31",
            mean_abnormal_return=0.0015,
            cumulative_abnormal_return=0.0450,
            volatility=0.0090,
            ar_z_score=2.65,
            observation_count=30,
            pct_positive_ar=0.7333,
            pct_negative_ar=0.2667,
            daily_dates=[],
            daily_ar=[],
            daily_car=[],
            is_statistically_significant=True,
            p_value=0.008,
        )
        score = AnticipationScore(
            bill_id="test-finance-bill-2024",
            company_isin="INE002A01018",
            company_symbol="SBIN",
            official_introduction_date="2024-02-01",
            market_signal_score=0.78,
            information_signal_score=0.65,
            anticipation_score=0.728,
            classification=AnticipationClassification.MODERATE_EVIDENCE.value,
            anticipation_flag=True,
            confidence="HIGH",
            evidence_count=2,
            media_data_available=True,
            decision_reason="Strong pre-event drift observed",
            window_stats={"[-30,-1]": win_stat},
            detected_signals=["STATISTICAL_SIGNIFICANCE_PRE_EVENT"],
        )
        d = score.to_dict()
        assert d["anticipation_score"] == 0.728
        assert "[-30,-1]" in d["window_stats"]

        restored = AnticipationScore.from_dict(d)
        assert restored.bill_id == score.bill_id
        assert restored.classification == AnticipationClassification.MODERATE_EVIDENCE.value
        assert "[-30,-1]" in restored.window_stats

    def test_bill_anticipation_record_roundtrip(self):
        bill_rec = BillAnticipationRecord(
            bill_id="test-finance-bill-2024",
            bill_title="The Test Finance Bill, 2024",
            official_introduction_date="2024-02-01",
            overall_anticipation_score=0.685,
            overall_classification=AnticipationClassification.MODERATE_EVIDENCE.value,
            overall_anticipation_flag=True,
            overall_confidence="HIGH",
            total_companies_analyzed=5,
            companies_with_anticipation_flag=4,
            pct_companies_flagged=0.80,
            mean_market_signal_score=0.70,
            mean_info_signal_score=0.65,
            total_evidence_count=3,
            media_data_available=True,
            decision_reason="80% of companies exhibited pre-event anticipation signals.",
        )
        d = bill_rec.to_dict()
        assert d["pct_companies_flagged"] == 0.80
        restored = BillAnticipationRecord.from_dict(d)
        assert restored.bill_id == bill_rec.bill_id
        assert restored.overall_classification == "MODERATE_EVIDENCE"

    def test_validation_report_methods(self):
        rep = AnticipationValidationReport(bill_id="test-bill")
        assert rep.is_valid is True

        rep.add_warning("Test warning")
        assert rep.is_valid is True
        assert len(rep.warnings) == 1

        rep.add_error("Test error")
        assert rep.is_valid is False
        assert len(rep.errors) == 1

        ev = InformationEvidence(
            bill_id="test-bill",
            source="News",
            publication_date="2024-02-05",
            headline="Future news",
            source_url="http://example.com",
            relevance_score=0.8,
            evidence_type="NEWS",
            evidence_timestamp="2024-02-05T00:00:00Z",
        )
        rep.add_rejected_evidence(ev, "Future date")
        assert rep.rejected_evidence_count == 1
        assert len(rep.rejected_evidence_details) == 1

        other = AnticipationValidationReport(bill_id="test-bill")
        other.add_error("Second error")
        rep.merge(other)
        assert len(rep.errors) == 2

        d = rep.to_dict()
        restored = AnticipationValidationReport.from_dict(d)
        assert restored.rejected_evidence_count == 1
        assert len(restored.errors) == 2


# ---------------------------------------------------------------------------
# 2. Market Analyzer Tests
# ---------------------------------------------------------------------------


class TestPreEventMarketAnalyzer:
    def test_parse_window_offsets(self):
        start, end = parse_window_offsets("[-30,-21]")
        assert start == -30
        assert end == -21

        start, end = parse_window_offsets("[-2, -1]")
        assert start == -2
        assert end == -1

        with pytest.raises(ValueError):
            parse_window_offsets("invalid")

        with pytest.raises(ValueError):
            parse_window_offsets("[-10,-20]")

    def test_analyze_company_bill_success(
        self, sample_bill, sample_company, sample_market_model, mock_trading_data
    ):
        trading_dates, cmp_series, bmk_series = mock_trading_data
        analyzer = PreEventMarketAnalyzer()

        stats_map = analyzer.analyze_company_bill(
            bill=sample_bill,
            company=sample_company,
            market_model=sample_market_model,
            company_returns=cmp_series,
            benchmark_returns=bmk_series,
            trading_calendar=trading_dates,
        )

        assert "[-30,-21]" in stats_map
        assert "[-20,-11]" in stats_map
        assert "[-10,-6]" in stats_map
        assert "[-5,-3]" in stats_map
        assert "[-2,-1]" in stats_map
        assert "[-30,-1]" in stats_map

        cum = stats_map["[-30,-1]"]
        assert cum.observation_count >= 20
        assert cum.cumulative_abnormal_return > 0.0
        assert cum.mean_abnormal_return > 0.0
        assert cum.ar_z_score > 0.0
        assert cum.pct_positive_ar > 0.50
        assert len(cum.daily_dates) == cum.observation_count

    def test_window_clamping_and_zero_obs(
        self, sample_bill, sample_company, sample_market_model
    ):
        short_calendar = ["2024-01-30", "2024-01-31", "2024-02-01"]
        cmp_series = pd.Series([0.01, 0.02, 0.01], index=pd.to_datetime(short_calendar))
        bmk_series = pd.Series([0.005, 0.01, 0.005], index=pd.to_datetime(short_calendar))

        analyzer = PreEventMarketAnalyzer(windows=["[-30,-21]", "[-2, 0]", "[-100,-80]"])
        stats_map = analyzer.analyze_company_bill(
            bill=sample_bill,
            company=sample_company,
            market_model=sample_market_model,
            company_returns=cmp_series,
            benchmark_returns=bmk_series,
            trading_calendar=short_calendar,
        )
        assert "[-100,-80]" in stats_map
        assert stats_map["[-100,-80]"].observation_count == 0

        # Window with valid calendar dates but no overlapping returns
        empty_cmp = pd.Series([], dtype=float, index=pd.to_datetime([]))
        stats_map_empty = analyzer.analyze_company_bill(
            bill=sample_bill,
            company=sample_company,
            market_model=sample_market_model,
            company_returns=empty_cmp,
            benchmark_returns=bmk_series,
            trading_calendar=short_calendar,
        )
        assert stats_map_empty["[-2, 0]"].observation_count == 0

    def test_missing_introduction_date_raises(
        self, sample_company, sample_market_model, mock_trading_data
    ):
        trading_dates, cmp_series, bmk_series = mock_trading_data
        bill_no_date = Bill(
            bill_id="no-date-bill",
            title="No Date Bill",
            bill_number="1/2024",
            year=2024,
            ministry="M",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            introduction_date=None,
            url="http://example.com",
            sectors=[],
        )
        analyzer = PreEventMarketAnalyzer()
        with pytest.raises(ValueError, match="missing introduction_date"):
            analyzer.analyze_company_bill(
                bill=bill_no_date,
                company=sample_company,
                market_model=sample_market_model,
                company_returns=cmp_series,
                benchmark_returns=bmk_series,
                trading_calendar=trading_dates,
            )

    def test_event_date_beyond_calendar_raises(
        self, sample_company, sample_market_model, mock_trading_data
    ):
        trading_dates, cmp_series, bmk_series = mock_trading_data
        future_bill = Bill(
            bill_id="future-bill",
            title="Future Bill",
            bill_number="1/2030",
            year=2030,
            ministry="M",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            introduction_date=datetime.date(2030, 1, 1),
            url="http://example.com",
            sectors=[],
        )
        analyzer = PreEventMarketAnalyzer()
        with pytest.raises(ValueError, match="after latest benchmark trading date"):
            analyzer.analyze_company_bill(
                bill=future_bill,
                company=sample_company,
                market_model=sample_market_model,
                company_returns=cmp_series,
                benchmark_returns=bmk_series,
                trading_calendar=trading_dates,
            )


# ---------------------------------------------------------------------------
# 3. Signal Detector Tests
# ---------------------------------------------------------------------------


class TestPreEventSignalDetector:
    def test_signal_detection_positive_drift(self):
        detector = PreEventSignalDetector(
            z_threshold=1.96,
            car_magnitude_threshold=0.02,
            sustained_direction_ratio=0.70,
            immediate_car_threshold=0.015,
        )

        window_stats = {
            "[-30,-21]": PreEventWindowStats(
                window="[-30,-21]",
                start_offset=-30,
                end_offset=-21,
                start_date="2024-01-01",
                end_date="2024-01-10",
                mean_abnormal_return=0.003,
                cumulative_abnormal_return=0.025,
                volatility=0.008,
                ar_z_score=2.1,
                observation_count=8,
                pct_positive_ar=0.75,
                pct_negative_ar=0.25,
                is_statistically_significant=True,
                p_value=0.03,
            ),
            "[-20,-11]": PreEventWindowStats(
                window="[-20,-11]",
                start_offset=-20,
                end_offset=-11,
                start_date="2024-01-11",
                end_date="2024-01-20",
                mean_abnormal_return=0.002,
                cumulative_abnormal_return=0.018,
                volatility=0.007,
                ar_z_score=1.8,
                observation_count=8,
                pct_positive_ar=0.75,
                pct_negative_ar=0.25,
                is_statistically_significant=False,
                p_value=0.08,
            ),
            "[-10,-6]": PreEventWindowStats(
                window="[-10,-6]",
                start_offset=-10,
                end_offset=-6,
                start_date="2024-01-21",
                end_date="2024-01-25",
                mean_abnormal_return=0.0025,
                cumulative_abnormal_return=0.0125,
                volatility=0.006,
                ar_z_score=1.9,
                observation_count=5,
                pct_positive_ar=0.80,
                pct_negative_ar=0.20,
                is_statistically_significant=False,
                p_value=0.06,
            ),
            "[-5,-3]": PreEventWindowStats(
                window="[-5,-3]",
                start_offset=-5,
                end_offset=-3,
                start_date="2024-01-26",
                end_date="2024-01-28",
                mean_abnormal_return=0.006,
                cumulative_abnormal_return=0.018,
                volatility=0.005,
                ar_z_score=2.4,
                observation_count=3,
                pct_positive_ar=1.0,
                pct_negative_ar=0.0,
                is_statistically_significant=True,
                p_value=0.02,
            ),
            "[-2,-1]": PreEventWindowStats(
                window="[-2,-1]",
                start_offset=-2,
                end_offset=-1,
                start_date="2024-01-29",
                end_date="2024-01-31",
                mean_abnormal_return=0.009,
                cumulative_abnormal_return=0.018,
                volatility=0.004,
                ar_z_score=2.8,
                observation_count=2,
                pct_positive_ar=1.0,
                pct_negative_ar=0.0,
                is_statistically_significant=True,
                p_value=0.01,
            ),
            "[-30,-1]": PreEventWindowStats(
                window="[-30,-1]",
                start_offset=-30,
                end_offset=-1,
                start_date="2024-01-01",
                end_date="2024-01-31",
                mean_abnormal_return=0.0035,
                cumulative_abnormal_return=0.0915,
                volatility=0.007,
                ar_z_score=3.85,
                observation_count=26,
                pct_positive_ar=0.807,
                pct_negative_ar=0.193,
                is_statistically_significant=True,
                p_value=0.0002,
            ),
        }

        signals, details = detector.detect_signals(window_stats)

        assert "STATISTICAL_SIGNIFICANCE_PRE_EVENT" in signals
        assert "HIGH_MAGNITUDE_PRE_EVENT_RETURN" in signals
        assert "SUSTAINED_POSITIVE_DRIFT" in signals
        assert "IMMEDIATE_PRE_T0_ACCELERATION" in signals
        assert "MULTI_WINDOW_PERSISTENT_POSITIVE_DRIFT" in signals

    def test_signal_detection_negative_persistence(self):
        detector = PreEventSignalDetector()
        neg_stats = {
            "[-30,-21]": PreEventWindowStats(
                window="[-30,-21]",
                start_offset=-30,
                end_offset=-21,
                start_date="2024-01-01",
                end_date="2024-01-10",
                mean_abnormal_return=-0.004,
                cumulative_abnormal_return=-0.03,
                volatility=0.007,
                ar_z_score=-2.5,
                observation_count=8,
                pct_positive_ar=0.2,
                pct_negative_ar=0.8,
                is_statistically_significant=True,
                p_value=0.01,
            ),
            "[-20,-11]": PreEventWindowStats(
                window="[-20,-11]",
                start_offset=-20,
                end_offset=-11,
                start_date="2024-01-11",
                end_date="2024-01-20",
                mean_abnormal_return=-0.003,
                cumulative_abnormal_return=-0.024,
                volatility=0.006,
                ar_z_score=-2.1,
                observation_count=8,
                pct_positive_ar=0.2,
                pct_negative_ar=0.8,
                is_statistically_significant=True,
                p_value=0.03,
            ),
            "[-10,-6]": PreEventWindowStats(
                window="[-10,-6]",
                start_offset=-10,
                end_offset=-6,
                start_date="2024-01-21",
                end_date="2024-01-25",
                mean_abnormal_return=-0.003,
                cumulative_abnormal_return=-0.015,
                volatility=0.005,
                ar_z_score=-2.0,
                observation_count=5,
                pct_positive_ar=0.1,
                pct_negative_ar=0.9,
                is_statistically_significant=True,
                p_value=0.04,
            ),
            "[-30,-1]": PreEventWindowStats(
                window="[-30,-1]",
                start_offset=-30,
                end_offset=-1,
                start_date="2024-01-01",
                end_date="2024-01-31",
                mean_abnormal_return=-0.003,
                cumulative_abnormal_return=-0.08,
                volatility=0.007,
                ar_z_score=-3.5,
                observation_count=25,
                pct_positive_ar=0.2,
                pct_negative_ar=0.8,
                is_statistically_significant=True,
                p_value=0.0005,
            ),
        }
        signals, details = detector.detect_signals(neg_stats)
        assert "SUSTAINED_NEGATIVE_DRIFT" in signals
        assert "MULTI_WINDOW_PERSISTENT_NEGATIVE_DRIFT" in signals

    def test_signal_detection_no_signals(self):
        detector = PreEventSignalDetector()
        zero_stats = {
            "[-30,-1]": PreEventWindowStats(
                window="[-30,-1]",
                start_offset=-30,
                end_offset=-1,
                start_date="2024-01-01",
                end_date="2024-01-31",
                mean_abnormal_return=0.0001,
                cumulative_abnormal_return=0.002,
                volatility=0.008,
                ar_z_score=0.15,
                observation_count=25,
                pct_positive_ar=0.52,
                pct_negative_ar=0.48,
                is_statistically_significant=False,
                p_value=0.88,
            )
        }
        signals, _ = detector.detect_signals(zero_stats)
        assert len(signals) == 0


# ---------------------------------------------------------------------------
# 4. Scorer & Classification Tests
# ---------------------------------------------------------------------------


class TestAnticipationScorer:
    def test_market_signal_score_bounds_and_empty(self):
        scorer = AnticipationScorer()
        assert scorer.calculate_market_signal_score({}, []) == 0.0

        cum_stats = PreEventWindowStats(
            window="[-30,-1]",
            start_offset=-30,
            end_offset=-1,
            start_date="2024-01-01",
            end_date="2024-01-31",
            mean_abnormal_return=0.004,
            cumulative_abnormal_return=0.06,
            volatility=0.008,
            ar_z_score=3.5,
            observation_count=25,
            pct_positive_ar=0.80,
            pct_negative_ar=0.20,
            is_statistically_significant=True,
            p_value=0.001,
        )
        imm_stats = PreEventWindowStats(
            window="[-2,-1]",
            start_offset=-2,
            end_offset=-1,
            start_date="2024-01-30",
            end_date="2024-01-31",
            mean_abnormal_return=0.015,
            cumulative_abnormal_return=0.030,
            volatility=0.005,
            ar_z_score=3.0,
            observation_count=2,
            pct_positive_ar=1.0,
            pct_negative_ar=0.0,
            is_statistically_significant=True,
            p_value=0.005,
        )
        win_stats = {"[-30,-1]": cum_stats, "[-2,-1]": imm_stats}
        score = scorer.calculate_market_signal_score(
            win_stats, ["STATISTICAL_SIGNIFICANCE_PRE_EVENT", "HIGH_MAGNITUDE_PRE_EVENT_RETURN"]
        )
        assert 0.0 <= score <= 1.0
        assert score > 0.70

    def test_information_signal_score_and_bad_dates(self):
        scorer = AnticipationScorer()
        evidence = [
            InformationEvidence(
                bill_id="test-bill",
                source="Reuters",
                publication_date="2024-01-25",
                headline="Draft bill finalized for introduction next week",
                source_url="http://reuters.com/1",
                relevance_score=0.95,
                evidence_type="NEWS",
                evidence_timestamp="2024-01-25T10:00:00Z",
                confidence="HIGH",
            ),
            InformationEvidence(
                bill_id="test-bill",
                source="Blog",
                publication_date="bad-date",
                headline="Some headline",
                source_url="http://blog.com/2",
                relevance_score=0.70,
                evidence_type="OTHER",
                evidence_timestamp="bad-date",
                confidence="LOW",
            ),
        ]
        info_score, available = scorer.calculate_information_signal_score(evidence, "2024-02-01")
        assert available is True
        assert 0.0 <= info_score <= 1.0

        empty_score, empty_avail = scorer.calculate_information_signal_score([], "2024-02-01")
        assert empty_avail is False
        assert empty_score == 0.0

    def test_composite_score_and_classification(self):
        scorer = AnticipationScorer()

        comp_nomedia = scorer.calculate_composite_score(0.80, 0.0, False)
        assert comp_nomedia == 0.80
        assert scorer.classify(comp_nomedia) == AnticipationClassification.STRONG_EVIDENCE

        comp_media = scorer.calculate_composite_score(0.80, 0.50, True)
        assert comp_media == 0.68
        assert scorer.classify(comp_media) == AnticipationClassification.MODERATE_EVIDENCE

        assert scorer.classify(0.35) == AnticipationClassification.WEAK_EVIDENCE
        assert scorer.classify(0.15) == AnticipationClassification.NO_EVIDENCE

    def test_confidence_and_decision_reason_tiers(self, sample_market_model):
        scorer = AnticipationScorer()

        conf_high = scorer.determine_confidence(sample_market_model, 25, True)
        assert conf_high == "HIGH"

        conf_med = scorer.determine_confidence(sample_market_model, 12, False)
        assert conf_med == "MEDIUM"

        conf_low = scorer.determine_confidence(sample_market_model, 5, False)
        assert conf_low == "LOW"

        # Decision reason tests
        r_strong = scorer.generate_decision_reason(
            AnticipationClassification.STRONG_EVIDENCE, 0.82, 0.85, 0.75, True, None, ["S1"]
        )
        assert "strongly consistent" in r_strong

        r_mod = scorer.generate_decision_reason(
            AnticipationClassification.MODERATE_EVIDENCE, 0.60, 0.60, 0.0, False, None, []
        )
        assert "moderately consistent" in r_mod

        r_weak = scorer.generate_decision_reason(
            AnticipationClassification.WEAK_EVIDENCE, 0.35, 0.35, 0.0, False, None, []
        )
        assert "Weak or inconclusive" in r_weak

        r_none = scorer.generate_decision_reason(
            AnticipationClassification.NO_EVIDENCE, 0.10, 0.10, 0.0, False, None, []
        )
        assert "No measurable evidence" in r_none


# ---------------------------------------------------------------------------
# 5. Anti-Leakage & Validator Tests
# ---------------------------------------------------------------------------


class TestAnticipationValidator:
    def test_validate_inputs_all_failure_cases(self, sample_bill, sample_company, sample_market_model):
        validator = AnticipationValidator()
        empty_df = pd.DataFrame()
        valid_df = pd.DataFrame({"Date": ["2024-01-01"], "Close": [100.0]})

        # 1. Missing bill
        rep1 = validator.validate_inputs(None, sample_company, sample_market_model, valid_df, valid_df)
        assert rep1.is_valid is False
        assert "Bill record is missing" in rep1.errors[0]

        # 2. Bill missing introduction date
        bill_no_dt = Bill(
            bill_id="b-nodate", title="T", bill_number="1", year=2024,
            ministry="M", house=BillHouse.LOK_SABHA, status=BillStatus.INTRODUCED,
            introduction_date=None, url="http://", sectors=[]
        )
        rep2 = validator.validate_inputs(bill_no_dt, sample_company, sample_market_model, valid_df, valid_df)
        assert rep2.is_valid is False
        assert "no official introduction_date" in rep2.errors[0]

        # 3. Missing company
        rep3 = validator.validate_inputs(sample_bill, None, sample_market_model, valid_df, valid_df)
        assert rep3.is_valid is False
        assert "Company record is missing" in rep3.errors[0]

        # 4. Missing market model
        rep4 = validator.validate_inputs(sample_bill, sample_company, None, valid_df, valid_df)
        assert rep4.is_valid is False
        assert "Market model is missing" in rep4.errors[0]

        # 5. Corrupted market model (NaN params, non-positive residual variance)
        corrupt_model = MarketModelRecord(
            company_isin="INE002", company_symbol="SBIN", bill_id="b",
            alpha=float("nan"), beta=1.0, r_squared=0.1, residual_variance=-0.05,
            standard_error=0.01, beta_stderr=0.01, alpha_stderr=0.01, n_observations=100,
            estimation_window={}, estimation_date="", benchmark_symbol=""
        )
        rep5 = validator.validate_inputs(sample_bill, sample_company, corrupt_model, valid_df, valid_df)
        assert rep5.is_valid is False
        assert any("NaN" in e for e in rep5.errors)
        assert any("non-positive" in e for e in rep5.errors)

        # 6. Empty prices
        rep6 = validator.validate_inputs(sample_bill, sample_company, sample_market_model, empty_df, valid_df)
        assert rep6.is_valid is False
        assert any("Price history is missing" in e for e in rep6.errors)

        rep7 = validator.validate_inputs(sample_bill, sample_company, sample_market_model, valid_df, empty_df)
        assert rep7.is_valid is False
        assert any("Benchmark price history is empty" in e for e in rep7.errors)

    def test_strict_anti_leakage_rejection(self):
        validator = AnticipationValidator()
        intro_date = "2024-02-01"

        evidence_items = [
            InformationEvidence(
                bill_id="test-bill",
                source="PIB",
                publication_date="2024-01-22",
                headline="Pre-legislative consultation document released",
                source_url="http://pib.gov.in/1",
                relevance_score=1.5,
                evidence_type="CUSTOM_UNKNOWN",
                evidence_timestamp="2024-01-22T00:00:00Z",
                confidence="HIGH",
            ),
            InformationEvidence(
                bill_id="other-bill",
                source="News",
                publication_date="2024-01-20",
                headline="Mismatch",
                source_url="http://news/x",
                relevance_score=0.5,
                evidence_type="NEWS",
                evidence_timestamp="2024-01-20T00:00:00Z",
            ),
            InformationEvidence(
                bill_id="test-bill",
                source="ANI",
                publication_date="",
                headline="No date",
                source_url="http://ani.in/no-date",
                relevance_score=0.5,
                evidence_type="NEWS",
                evidence_timestamp="",
            ),
            InformationEvidence(
                bill_id="test-bill",
                source="ANI",
                publication_date="2024-02-01",
                headline="Bill tabled in Lok Sabha today",
                source_url="http://ani.in/2",
                relevance_score=0.95,
                evidence_type="NEWS",
                evidence_timestamp="2024-02-01T11:00:00Z",
                confidence="HIGH",
            ),
            InformationEvidence(
                bill_id="test-bill",
                source="LiveMint",
                publication_date="2024-02-05",
                headline="Market reacts to newly introduced bill",
                source_url="http://livemint.com/3",
                relevance_score=0.85,
                evidence_type="NEWS",
                evidence_timestamp="2024-02-05T09:00:00Z",
                confidence="MEDIUM",
            ),
        ]

        valid_items, rep = validator.validate_evidence(evidence_items, intro_date, "test-bill")

        assert len(valid_items) == 1
        assert valid_items[0].source == "PIB"
        assert valid_items[0].relevance_score == 1.0
        assert valid_items[0].evidence_type == "OTHER"

        assert rep.rejected_evidence_count == 3
        assert any("mismatch" in e for e in rep.errors)

    def test_duplicate_evidence_handling(self):
        validator = AnticipationValidator()
        intro_date = "2024-02-01"

        evidence_items = [
            InformationEvidence(
                bill_id="test-bill",
                source="PIB",
                publication_date="2024-01-20",
                headline="Identical Headline",
                source_url="http://pib.gov.in/item1",
                relevance_score=0.8,
                evidence_type="OFFICIAL",
                evidence_timestamp="2024-01-20T00:00:00Z",
            ),
            InformationEvidence(
                bill_id="test-bill",
                source="PIB",
                publication_date="2024-01-20",
                headline="Identical Headline",
                source_url="http://pib.gov.in/item1",
                relevance_score=0.8,
                evidence_type="OFFICIAL",
                evidence_timestamp="2024-01-20T00:00:00Z",
            ),
        ]

        valid_items, rep = validator.validate_evidence(evidence_items, intro_date, "test-bill")
        assert len(valid_items) == 1
        assert any("DUPLICATE_EVIDENCE" in w for w in rep.warnings)

    def test_window_stats_and_score_validation(self):
        validator = AnticipationValidator(min_window_obs=3, min_cumulative_obs=20)

        rep_empty = validator.validate_window_stats({}, "b", "i")
        assert rep_empty.is_valid is False

        bad_stats = {
            "[-30,-1]": PreEventWindowStats(
                window="[-30,-1]", start_offset=-30, end_offset=-1,
                start_date="2024-01-01", end_date="2024-01-31",
                mean_abnormal_return=float("nan"), cumulative_abnormal_return=0.1,
                volatility=0.02, ar_z_score=float("inf"), observation_count=5,
                pct_positive_ar=1.5,
                pct_negative_ar=-0.5,
                is_statistically_significant=True, p_value=2.0
            ),
            "[-2,-1]": PreEventWindowStats(
                window="[-2,-1]", start_offset=-2, end_offset=-1,
                start_date="2024-01-30", end_date="2024-01-31",
                mean_abnormal_return=0.01, cumulative_abnormal_return=0.02,
                volatility=0.01, ar_z_score=1.0, observation_count=1,
                pct_positive_ar=0.5, pct_negative_ar=0.5,
                is_statistically_significant=False, p_value=0.5
            ),
        }
        rep_bad = validator.validate_window_stats(bad_stats, "b", "i")
        assert rep_bad.is_valid is False
        assert any("contains NaN or Inf" in e for e in rep_bad.errors)
        assert any("pct_positive_ar outside" in e for e in rep_bad.errors)
        assert any("p_value outside" in e for e in rep_bad.errors)
        assert len(rep_bad.warnings) >= 2

        bad_score = AnticipationScore(
            bill_id="b", company_isin="i", company_symbol="s",
            official_introduction_date="2024-01-01",
            market_signal_score=1.5,
            information_signal_score=float("nan"),
            anticipation_score=-0.2,
            classification="INVALID_CLASS",
            anticipation_flag=False,
            confidence="UNKNOWN_CONF",
            evidence_count=0, media_data_available=False, decision_reason=""
        )
        rep_score = validator.validate_anticipation_score(bad_score)
        assert rep_score.is_valid is False
        assert any("outside [0.0, 1.0]" in e for e in rep_score.errors)
        assert any("is NaN or Inf" in e for e in rep_score.errors)
        assert any("Invalid classification" in e for e in rep_score.errors)
        assert any("Invalid confidence" in e for e in rep_score.errors)


# ---------------------------------------------------------------------------
# 6. Repository Tests
# ---------------------------------------------------------------------------


class TestAnticipationRepository:
    def test_repository_crud_and_batch_operations(self, tmp_path):
        repo = AnticipationRepository(anticipation_dir=tmp_path)

        score1 = AnticipationScore(
            bill_id="bill-101", company_isin="INE001", company_symbol="TCS",
            official_introduction_date="2024-01-10", market_signal_score=0.65,
            information_signal_score=0.0, anticipation_score=0.65,
            classification="MODERATE_EVIDENCE", anticipation_flag=True,
            confidence="HIGH", evidence_count=0, media_data_available=False, decision_reason="Test 1"
        )
        score2 = AnticipationScore(
            bill_id="bill-101", company_isin="INE002", company_symbol="INFY",
            official_introduction_date="2024-01-10", market_signal_score=0.45,
            information_signal_score=0.0, anticipation_score=0.45,
            classification="WEAK_EVIDENCE", anticipation_flag=False,
            confidence="MEDIUM", evidence_count=0, media_data_available=False, decision_reason="Test 2"
        )

        assert repo.score_exists("bill-101", "INE001") is False
        repo.save_scores([score1, score2])
        assert repo.score_exists("bill-101", "INE001") is True
        assert repo.score_exists("bill-101", "INE002") is True

        retrieved = repo.get_score("bill-101", "INE001")
        assert retrieved is not None
        assert retrieved.anticipation_score == 0.65

        all_scores = repo.get_all_scores()
        assert len(all_scores) == 2

        bill_scores = repo.get_scores_by_bill("bill-101")
        assert len(bill_scores) == 2

        cmp_scores = repo.get_scores_by_company("INE001")
        assert len(cmp_scores) == 1

        assert repo.get_score("none", "none") is None

    def test_market_stats_and_validation_reports_crud(self, tmp_path):
        repo = AnticipationRepository(anticipation_dir=tmp_path)

        win_stat = PreEventWindowStats(
            window="[-30,-1]", start_offset=-30, end_offset=-1,
            start_date="2024-01-01", end_date="2024-01-31",
            mean_abnormal_return=0.002, cumulative_abnormal_return=0.04,
            volatility=0.01, ar_z_score=2.0, observation_count=20,
            pct_positive_ar=0.7, pct_negative_ar=0.3
        )
        repo.save_market_stats({"[-30,-1]": win_stat}, "bill-A", "INE-A")
        loaded_stats = repo.get_market_stats("bill-A", "INE-A")
        assert loaded_stats is not None
        assert "[-30,-1]" in loaded_stats

        all_market_stats = repo.get_all_market_stats()
        assert "bill-A_INE-A" in all_market_stats

        # Bill score CRUD
        b_rec = BillAnticipationRecord(
            bill_id="bill-A", bill_title="Title A", official_introduction_date="2024-01-01",
            overall_anticipation_score=0.5, overall_classification="MODERATE_EVIDENCE",
            overall_anticipation_flag=True, overall_confidence="HIGH", total_companies_analyzed=1,
            companies_with_anticipation_flag=1, pct_companies_flagged=1.0, mean_market_signal_score=0.5,
            mean_info_signal_score=0.0, total_evidence_count=0, media_data_available=False
        )
        repo.save_bill_score(b_rec)
        assert repo.bill_score_exists("bill-A") is True
        assert len(repo.get_all_bill_scores()) == 1

        # Evidence CRUD
        ev = InformationEvidence(
            bill_id="bill-A", source="PIB", publication_date="2024-01-01",
            headline="H", source_url="http://", relevance_score=0.8, evidence_type="OFFICIAL",
            evidence_timestamp="2024-01-01T00:00:00Z"
        )
        repo.save_evidence([ev], "bill-A")
        assert len(repo.get_evidence_by_bill("bill-A")) == 1
        assert len(repo.get_all_evidence()) == 1

        # Validation reports
        v_rep = AnticipationValidationReport(bill_id="bill-A", company_isin="INE-A")
        v_rep.add_error("Sample error")
        rep_id = repo.save_validation_report(v_rep)
        assert rep_id is not None

        loaded_v_rep = repo.get_validation_report(rep_id)
        assert loaded_v_rep is not None
        assert loaded_v_rep.errors == ["Sample error"]

        all_v_reps = repo.get_all_validation_reports()
        assert len(all_v_reps) == 1

        assert repo.get_validation_report("non-existent") is None
        assert repo.get_bill_score("non-existent") is None
        assert repo.get_market_stats("none", "none") is None
        assert repo.get_evidence_by_bill("none") == []

    def test_repository_corrupted_files_and_exceptions(self, tmp_path):
        repo = AnticipationRepository(anticipation_dir=tmp_path)

        # Write corrupted JSON
        bad_score_file = tmp_path / "scores" / "bad.json"
        bad_score_file.write_text("invalid json", encoding="utf-8")
        assert repo.get_all_scores() == []
        assert repo.get_scores_by_bill("bad") == []

        bad_bill_file = tmp_path / "bill_scores" / "bad.json"
        bad_bill_file.write_text("invalid json", encoding="utf-8")
        assert repo.get_all_bill_scores() == []
        assert repo.get_bill_score("bad") is None

        bad_stats_file = tmp_path / "market_stats" / "bad_stats.json"
        bad_stats_file.write_text("invalid json", encoding="utf-8")
        assert repo.get_all_market_stats() == {}
        assert repo.get_market_stats("bad", "bad") is None

        bad_ev_file = tmp_path / "evidence" / "bad_evidence.json"
        bad_ev_file.write_text("invalid json", encoding="utf-8")
        assert repo.get_all_evidence() == []
        assert repo.get_evidence_by_bill("bad") == []

        bad_rep_file = tmp_path / "reports" / "bad.json"
        bad_rep_file.write_text("invalid json", encoding="utf-8")
        assert repo.get_all_validation_reports() == []
        assert repo.get_validation_report("bad") is None

    def test_repository_exception_handlers(self, tmp_path):
        repo = AnticipationRepository(anticipation_dir=tmp_path)

        with patch("storage.anticipation_repository.load_json", side_effect=Exception("Disk read error")):
            with patch("storage.anticipation_repository.file_exists", return_value=True):
                assert repo.get_score("b", "i") is None
                assert repo.get_bill_score("b") is None
                assert repo.get_market_stats("b", "i") is None

        with patch("storage.anticipation_repository.list_files", side_effect=Exception("Disk list error")):
            assert repo.get_all_scores() == []
            assert repo.get_scores_by_bill("b") == []
            assert repo.get_scores_by_company("i") == []
            assert repo.get_all_bill_scores() == []
            assert repo.get_all_market_stats() == {}
            assert repo.get_all_evidence() == []
            assert repo.get_evidence_by_bill("b") == []
            assert repo.get_all_validation_reports() == []

    def test_sanitize_id(self):
        assert sanitize_id("the/finance:bill\\2024 test") == "the_finance_bill_2024_test"


# ---------------------------------------------------------------------------
# 7. Engine & Service Orchestration Tests
# ---------------------------------------------------------------------------


class TestAnticipationEngineAndService:
    def test_analyze_single_pair_bse_only(
        self, sample_bill, sample_company_bse_only, mock_trading_data, tmp_path
    ):
        trading_dates, cmp_series, bmk_series = mock_trading_data
        repo = AnticipationRepository(anticipation_dir=tmp_path)

        bse_market_model = MarketModelRecord(
            company_isin=sample_company_bse_only.isin,
            company_symbol="599999",
            bill_id=sample_bill.bill_id,
            alpha=0.0002, beta=0.85, r_squared=0.25, residual_variance=0.0002,
            standard_error=0.014, beta_stderr=0.1, alpha_stderr=0.001, n_observations=200,
            estimation_window={}, estimation_date="", benchmark_symbol="^NSEI"
        )

        class MockBillRepo:
            def get(self, bill_id):
                return sample_bill

        class MockCompanyRepo:
            def get_by_isin(self, isin):
                return sample_company_bse_only

        class MockMarketRepo:
            def get_prices(self, symbol, start_date, end_date=None):
                return pd.DataFrame({"Date": trading_dates, "Close": [50.0] * len(trading_dates)})

            def get_daily_returns(self, symbol, start_date, end_date=None):
                return bmk_series if symbol == "^NSEI" else cmp_series

        engine = AnticipationBiasEngine(
            bill_repo=MockBillRepo(),
            company_repo=MockCompanyRepo(),
            market_repo=MockMarketRepo(),
            anticipation_repo=repo,
        )

        score, rep = engine.analyze_single_pair(bse_market_model, force_refresh=True)
        assert rep.is_valid is True
        assert score is not None
        assert score.company_symbol == "599999"

    def test_analyze_single_pair_no_ticker_and_missing_entities(
        self, sample_bill, sample_company_no_ticker, sample_market_model, tmp_path
    ):
        repo = AnticipationRepository(anticipation_dir=tmp_path)

        class MockBillRepo:
            def get(self, bill_id):
                return None  # missing bill

        class MockCompanyRepo:
            def get_by_isin(self, isin):
                return None  # missing company

        class MockMarketRepo:
            def get_prices(self, symbol, start_date, end_date=None):
                return pd.DataFrame()

            def get_daily_returns(self, symbol, start_date, end_date=None):
                return pd.Series(dtype=float)

        engine = AnticipationBiasEngine(
            bill_repo=MockBillRepo(),
            company_repo=MockCompanyRepo(),
            market_repo=MockMarketRepo(),
            anticipation_repo=repo,
        )

        score1, rep1 = engine.analyze_single_pair(sample_market_model)
        assert score1 is None
        assert "Bill" in rep1.errors[0]

        # Missing company
        class MockBillRepoOk:
            def get(self, bill_id):
                return sample_bill

        engine2 = AnticipationBiasEngine(
            bill_repo=MockBillRepoOk(),
            company_repo=MockCompanyRepo(),
            market_repo=MockMarketRepo(),
            anticipation_repo=repo,
        )
        score2, rep2 = engine2.analyze_single_pair(sample_market_model)
        assert score2 is None
        assert "Company" in rep2.errors[0]

    def test_analyze_bill_rollup_multiple_companies(
        self, sample_bill, sample_company, sample_company_bse_only, sample_market_model, mock_trading_data, tmp_path
    ):
        trading_dates, cmp_series, bmk_series = mock_trading_data
        repo = AnticipationRepository(anticipation_dir=tmp_path)

        model2 = MarketModelRecord(
            company_isin=sample_company_bse_only.isin,
            company_symbol="599999",
            bill_id=sample_bill.bill_id,
            alpha=0.0, beta=1.0, r_squared=0.30, residual_variance=0.0001,
            standard_error=0.01, beta_stderr=0.05, alpha_stderr=0.001, n_observations=200,
            estimation_window={}, estimation_date="", benchmark_symbol="^NSEI"
        )

        class MockBillRepo:
            def get(self, bill_id):
                return sample_bill if bill_id == sample_bill.bill_id else None

        class MockCompanyRepo:
            def get_by_isin(self, isin):
                if isin == sample_company.isin:
                    return sample_company
                return sample_company_bse_only

        class MockMarketModelRepo:
            def get_all(self):
                return [sample_market_model, model2]

            def get_by_bill(self, bill_id):
                return [sample_market_model, model2] if bill_id == sample_bill.bill_id else []

        class MockMarketRepo:
            def get_prices(self, symbol, start_date, end_date=None):
                return pd.DataFrame({"Date": trading_dates, "Close": [100.0] * len(trading_dates)})

            def get_daily_returns(self, symbol, start_date, end_date=None):
                return bmk_series if symbol == "^NSEI" else cmp_series

        engine = AnticipationBiasEngine(
            bill_repo=MockBillRepo(),
            company_repo=MockCompanyRepo(),
            market_repo=MockMarketRepo(),
            market_model_repo=MockMarketModelRepo(),
            anticipation_repo=repo,
        )

        bill_rec, rep = engine.analyze_bill(sample_bill.bill_id, force_refresh=True)
        assert rep.is_valid is True
        assert bill_rec is not None
        assert bill_rec.total_companies_analyzed == 2
        assert len(bill_rec.company_scores) == 2
        assert bill_rec.overall_confidence in {"HIGH", "MEDIUM"}

        # Failure cases for analyze_bill
        b_none, rep_none = engine.analyze_bill("non-existent-bill")
        assert b_none is None
        assert any("not found" in e for e in rep_none.errors)

        bill_nodate = Bill(
            bill_id="b-nodate", title="T", bill_number="1", year=2024,
            ministry="M", house=BillHouse.LOK_SABHA, status=BillStatus.INTRODUCED,
            introduction_date=None, url="http://", sectors=[]
        )
        with patch.object(MockBillRepo, "get", return_value=bill_nodate):
            b_nd, rep_nd = engine.analyze_bill("b-nodate")
            assert b_nd is None
            assert any("no introduction date" in e for e in rep_nd.errors)

        # Bill with no models
        with patch.object(MockMarketModelRepo, "get_by_bill", return_value=[]):
            b_nomod, rep_nomod = engine.analyze_bill(sample_bill.bill_id)
            assert b_nomod is None
            assert any("No market models found" in e for e in rep_nomod.errors)

    def test_run_all_filtering_and_skip(
        self, sample_bill, sample_company, sample_market_model, mock_trading_data, tmp_path
    ):
        trading_dates, cmp_series, bmk_series = mock_trading_data
        repo = AnticipationRepository(anticipation_dir=tmp_path)

        class MockBillRepo:
            def get(self, bill_id):
                return sample_bill if bill_id == sample_bill.bill_id else None

        class MockCompanyRepo:
            def get_by_isin(self, isin):
                return sample_company if isin == sample_company.isin else None

        class MockMarketModelRepo:
            def get_all(self):
                return [sample_market_model]

            def get_by_bill(self, bill_id):
                return [sample_market_model] if bill_id == sample_bill.bill_id else []

        class MockMarketRepo:
            def get_prices(self, symbol, start_date, end_date=None):
                return pd.DataFrame({"Date": trading_dates, "Close": [100.0] * len(trading_dates)})

            def get_daily_returns(self, symbol, start_date, end_date=None):
                return bmk_series if symbol == "^NSEI" else cmp_series

        engine = AnticipationBiasEngine(
            bill_repo=MockBillRepo(),
            company_repo=MockCompanyRepo(),
            market_repo=MockMarketRepo(),
            market_model_repo=MockMarketModelRepo(),
            anticipation_repo=repo,
        )
        service = AnticipationService(engine=engine)

        # 1. Run with mismatch filters -> processed = 0
        stats_mismatch = service.run_analysis(year=1999)
        assert stats_mismatch["models_processed"] == 0

        # 2. Run with matching bill_id
        stats_match = service.run_analysis(bill_id_filter=sample_bill.bill_id, force_refresh=True)
        assert stats_match["models_processed"] == 1
        assert stats_match["models_succeeded"] == 1

        # 3. Incremental run -> skipped
        stats_skip = service.run_analysis(bill_id_filter=sample_bill.bill_id, force_refresh=False, skip_existing=True)
        assert stats_skip["models_skipped"] == 1

        # 4. Service get_bill_summary
        b_sum = service.get_bill_summary(sample_bill.bill_id)
        assert b_sum is not None
        assert b_sum.bill_id == sample_bill.bill_id

        # 5. Service get_bill_summary when not yet computed
        with patch.object(repo, "get_bill_score", return_value=None):
            b_sum2 = service.get_bill_summary(sample_bill.bill_id)
            assert b_sum2 is not None
            assert b_sum2.bill_id == sample_bill.bill_id

    def test_engine_edge_cases_and_error_handling(
        self, sample_bill, sample_company, sample_company_no_ticker, sample_market_model, mock_trading_data, tmp_path
    ):
        trading_dates, cmp_series, bmk_series = mock_trading_data
        repo = AnticipationRepository(anticipation_dir=tmp_path)

        class MockBillRepo:
            def get(self, bill_id):
                return sample_bill if bill_id == sample_bill.bill_id else None

        class MockCompanyRepo:
            def get_by_isin(self, isin):
                if isin == sample_company_no_ticker.isin:
                    return sample_company_no_ticker
                return sample_company

        class MockMarketModelRepo:
            def get_all(self):
                return [sample_market_model]

            def get_by_bill(self, bill_id):
                return [sample_market_model]

        class MockMarketRepo:
            def get_prices(self, symbol, start_date, end_date=None):
                if symbol == "EMPTY":
                    return pd.DataFrame()
                return pd.DataFrame({"Date": trading_dates, "Close": [100.0] * len(trading_dates)})

            def get_daily_returns(self, symbol, start_date, end_date=None):
                return bmk_series if symbol == "^NSEI" else cmp_series

        engine = AnticipationBiasEngine(
            bill_repo=MockBillRepo(),
            company_repo=MockCompanyRepo(),
            market_repo=MockMarketRepo(),
            market_model_repo=MockMarketModelRepo(),
            anticipation_repo=repo,
        )

        # 1. get_trading_calendar empty
        empty_cal = engine.get_trading_calendar("EMPTY")
        assert empty_cal == []

        # 2. analyze_single_pair company with no ticker
        model_no_ticker = MarketModelRecord(
            company_isin=sample_company_no_ticker.isin, company_symbol="", bill_id=sample_bill.bill_id,
            alpha=0.0, beta=1.0, r_squared=0.1, residual_variance=0.001, standard_error=0.01,
            beta_stderr=0.01, alpha_stderr=0.01, n_observations=100, estimation_window={},
            estimation_date="", benchmark_symbol="^NSEI"
        )
        score_nt, rep_nt = engine.analyze_single_pair(model_no_ticker)
        assert score_nt is None
        assert rep_nt.is_valid is False

        # 3. Market analyzer exception handling in single pair
        with patch.object(engine.analyzer, "analyze_company_bill", side_effect=RuntimeError("Simulated math error")):
            score_err, rep_err = engine.analyze_single_pair(sample_market_model, force_refresh=True)
            assert score_err is None
            assert "Simulated math error" in rep_err.errors[0]

        # 4. Stats report invalid in single pair
        with patch.object(engine.validator, "validate_window_stats", return_value=AnticipationValidationReport(bill_id=sample_bill.bill_id, errors=["Invalid stats"])):
            score_inv, rep_inv = engine.analyze_single_pair(sample_market_model, force_refresh=True)
            assert score_inv is None
            assert "Invalid stats" in rep_inv.errors

        # 5. analyze_bill with no valid company scores (all fail)
        with patch.object(engine, "analyze_single_pair", return_value=(None, AnticipationValidationReport(bill_id=sample_bill.bill_id, errors=["Fail"]))):
            b_rec_fail, rep_fail = engine.analyze_bill(sample_bill.bill_id)
            assert b_rec_fail is None
            assert any("No company scores" in e for e in rep_fail.errors)

        # 6. analyze_bill with low confidence scores
        low_conf_score = AnticipationScore(
            bill_id=sample_bill.bill_id, company_isin=sample_company.isin, company_symbol="SBIN",
            official_introduction_date="2024-02-01", market_signal_score=0.2, information_signal_score=0.0,
            anticipation_score=0.2, classification="NO_EVIDENCE", anticipation_flag=False,
            confidence="LOW", evidence_count=0, media_data_available=False, decision_reason=""
        )
        with patch.object(engine, "analyze_single_pair", return_value=(low_conf_score, AnticipationValidationReport(bill_id=sample_bill.bill_id))):
            b_rec_low, _ = engine.analyze_bill(sample_bill.bill_id, force_refresh=True)
            assert b_rec_low is not None
            assert b_rec_low.overall_confidence == "LOW"

        # 7. run_all with company_isin filter, year filter, failed single pair, exception in analyze_bill
        res_filter = engine.run_all(company_isin_filter=sample_company.isin, year=2024, force_refresh=True)
        assert res_filter["models_succeeded"] == 1

        # Run with year mismatch bill
        bill_2020 = Bill(
            bill_id="b-2020", title="Old Bill", bill_number="1", year=2020,
            ministry="M", house=BillHouse.LOK_SABHA, status=BillStatus.INTRODUCED,
            introduction_date=datetime.date(2020, 1, 1), url="http://", sectors=[]
        )
        with patch.object(MockBillRepo, "get", return_value=bill_2020):
            res_year = engine.run_all(year=2024)
            assert res_year["models_processed"] == 0

        # run_all single pair failure and analyze_bill failure
        with patch.object(engine, "analyze_single_pair", return_value=(None, AnticipationValidationReport(bill_id=sample_bill.bill_id, errors=["Pair failed"]))):
            with patch.object(engine, "analyze_bill", side_effect=Exception("Rollup exception")):
                res_all_fail = engine.run_all(force_refresh=True)
                assert res_all_fail["models_failed"] == 1

