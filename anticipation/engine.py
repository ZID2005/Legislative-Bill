"""
anticipation/engine.py
======================
Top-level orchestration engine for Task 6.5 — Anticipation Bias / Pre-Event Information Analysis.

Coordinates:
- Pre-event market window calculations across trading days.
- External information evidence loading and strict anti-leakage filtering.
- Deterministic signal detection and scoring.
- Classification into NO_EVIDENCE, WEAK, MODERATE, STRONG.
- Bill-level rollup aggregation across companies.
- Persistence and incremental execution.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.settings import settings
from schemas.anticipation import (
    AnticipationClassification,
    AnticipationScore,
    AnticipationValidationReport,
    BillAnticipationRecord,
    InformationEvidence,
    PreEventWindowStats,
)
from schemas.bill import Bill
from schemas.company import Company
from schemas.market_model import MarketModelRecord
from storage.anticipation_repository import AnticipationRepository
from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.market_model_repository import MarketModelRepository
from storage.market_repository import MarketRepository
from validation.anticipation_validator import AnticipationValidator
from anticipation.market_analyzer import PreEventMarketAnalyzer
from anticipation.signal_detector import PreEventSignalDetector
from anticipation.scorer import AnticipationScorer

logger = get_logger(__name__)


class AnticipationBiasEngine:
    """
    Orchestration engine for analyzing pre-event anticipation bias.
    """

    def __init__(
        self,
        bill_repo: Optional[BillRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        market_repo: Optional[MarketRepository] = None,
        market_model_repo: Optional[MarketModelRepository] = None,
        anticipation_repo: Optional[AnticipationRepository] = None,
        validator: Optional[AnticipationValidator] = None,
        analyzer: Optional[PreEventMarketAnalyzer] = None,
        signal_detector: Optional[PreEventSignalDetector] = None,
        scorer: Optional[AnticipationScorer] = None,
    ) -> None:
        self.bill_repo = bill_repo or BillRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.market_repo = market_repo or MarketRepository()
        self.market_model_repo = market_model_repo or MarketModelRepository()
        self.anticipation_repo = anticipation_repo or AnticipationRepository()
        self.validator = validator or AnticipationValidator()
        self.analyzer = analyzer or PreEventMarketAnalyzer()
        self.signal_detector = signal_detector or PreEventSignalDetector()
        self.scorer = scorer or AnticipationScorer()

        # Cache returns & calendars to optimize batch processing
        self._benchmark_returns_cache: dict[str, pd.Series] = {}
        self._company_returns_cache: dict[str, pd.Series] = {}
        self._trading_calendar_cache: dict[str, list[str]] = {}

    def get_benchmark_returns(self, benchmark_symbol: str) -> pd.Series:
        """Retrieve and cache benchmark returns."""
        if benchmark_symbol not in self._benchmark_returns_cache:
            self._benchmark_returns_cache[benchmark_symbol] = self.market_repo.get_daily_returns(
                benchmark_symbol, "1900-01-01"
            )
        return self._benchmark_returns_cache[benchmark_symbol]

    def get_company_returns(self, company_ticker: str) -> pd.Series:
        """Retrieve and cache company returns."""
        if company_ticker not in self._company_returns_cache:
            self._company_returns_cache[company_ticker] = self.market_repo.get_daily_returns(
                company_ticker, "1900-01-01"
            )
        return self._company_returns_cache[company_ticker]

    def get_trading_calendar(self, benchmark_symbol: str) -> list[str]:
        """Retrieve and cache sorted benchmark trading day calendar."""
        if benchmark_symbol not in self._trading_calendar_cache:
            prices = self.market_repo.get_prices(benchmark_symbol, "1900-01-01")
            if not prices.empty and "Date" in prices.columns:
                dates = sorted(prices["Date"].unique().tolist())
                self._trading_calendar_cache[benchmark_symbol] = dates
            else:
                self._trading_calendar_cache[benchmark_symbol] = []
        return self._trading_calendar_cache[benchmark_symbol]

    def analyze_single_pair(
        self,
        market_model: MarketModelRecord,
        force_refresh: bool = False,
        external_evidence: Optional[list[InformationEvidence]] = None,
    ) -> tuple[Optional[AnticipationScore], AnticipationValidationReport]:
        """
        Compute anticipation score and diagnostics for a single bill-company pair.
        """
        bill_id = market_model.bill_id
        company_isin = market_model.company_isin

        val_report = AnticipationValidationReport(bill_id=bill_id, company_isin=company_isin)

        # Check existing score for incremental execution
        if not force_refresh and self.anticipation_repo.score_exists(bill_id, company_isin):
            logger.debug("Anticipation score already exists for %s / %s. Skipping.", bill_id, company_isin)
            existing = self.anticipation_repo.get_score(bill_id, company_isin)
            return existing, val_report

        # 1. Load entities
        bill = self.bill_repo.get(bill_id)
        company = self.company_repo.get_by_isin(company_isin)

        if not bill:
            val_report.add_error(f"Bill '{bill_id}' not found in BillRepository.")
            return None, val_report

        if not company:
            val_report.add_error(f"Company '{company_isin}' not found in CompanyRepository.")
            return None, val_report

        # Resolve tickers
        company_symbol = company.ticker_nse or company.ticker_bse or ""
        if company.ticker_nse:
            company_ticker = f"{company.ticker_nse.strip().upper()}.NS"
        elif company.ticker_bse:
            company_ticker = f"{company.ticker_bse.strip().upper()}.BO"
        else:
            company_ticker = ""

        # 2. Input validation
        benchmark_prices = self.market_repo.get_prices(market_model.benchmark_symbol, "1900-01-01")
        company_prices = (
            self.market_repo.get_prices(company_ticker, "1900-01-01")
            if company_ticker
            else pd.DataFrame()
        )

        input_report = self.validator.validate_inputs(
            bill=bill,
            company=company,
            market_model=market_model,
            company_prices=company_prices,
            benchmark_prices=benchmark_prices,
        )
        val_report.merge(input_report)
        if not val_report.is_valid:
            return None, val_report

        # 3. Market Analysis
        trading_calendar = self.get_trading_calendar(market_model.benchmark_symbol)
        benchmark_returns = self.get_benchmark_returns(market_model.benchmark_symbol)
        company_returns = self.get_company_returns(company_ticker)

        try:
            window_stats = self.analyzer.analyze_company_bill(
                bill=bill,
                company=company,
                market_model=market_model,
                company_returns=company_returns,
                benchmark_returns=benchmark_returns,
                trading_calendar=trading_calendar,
            )
        except Exception as exc:
            val_report.add_error(f"Market analysis calculation failed: {exc}")
            return None, val_report

        # Validate window stats
        stats_report = self.validator.validate_window_stats(window_stats, bill_id, company_isin)
        val_report.merge(stats_report)
        if not val_report.is_valid:
            return None, val_report

        # 4. External Evidence & Anti-Leakage Audit
        intro_date_str = bill.introduction_date.strftime("%Y-%m-%d")
        if external_evidence is None:
            raw_evidence = self.anticipation_repo.get_evidence_by_bill(bill_id)
        else:
            raw_evidence = external_evidence

        valid_evidence, evidence_report = self.validator.validate_evidence(
            evidence_items=raw_evidence,
            official_introduction_date=intro_date_str,
            bill_id=bill_id,
        )
        val_report.merge(evidence_report)

        # 5. Signal Detection
        detected_signals, signal_details = self.signal_detector.detect_signals(window_stats)

        # 6. Scoring & Classification
        market_score = self.scorer.calculate_market_signal_score(window_stats, detected_signals)
        info_score, media_available = self.scorer.calculate_information_signal_score(
            valid_evidence, intro_date_str
        )
        composite_score = self.scorer.calculate_composite_score(
            market_score, info_score, media_available
        )

        classification = self.scorer.classify(composite_score)
        anticipation_flag = composite_score >= self.scorer.flag_threshold

        cum_stats = window_stats.get("[-30,-1]")
        obs_count = cum_stats.observation_count if cum_stats else 0
        confidence = self.scorer.determine_confidence(market_model, obs_count, media_available)

        decision_reason = self.scorer.generate_decision_reason(
            classification=classification,
            anticipation_score=composite_score,
            market_score=market_score,
            info_score=info_score,
            media_data_available=media_available,
            cum_stats=cum_stats,
            detected_signals=detected_signals,
        )

        score_record = AnticipationScore(
            bill_id=bill_id,
            company_isin=company_isin,
            company_symbol=company_symbol,
            official_introduction_date=intro_date_str,
            market_signal_score=market_score,
            information_signal_score=info_score,
            anticipation_score=composite_score,
            classification=classification.value,
            anticipation_flag=anticipation_flag,
            confidence=confidence,
            evidence_count=len(valid_evidence),
            media_data_available=media_available,
            decision_reason=decision_reason,
            window_stats=window_stats,
            detected_signals=detected_signals,
            calculation_timestamp=datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        )

        # Score validation
        score_val_report = self.validator.validate_anticipation_score(score_record)
        val_report.merge(score_val_report)

        # Persist outputs
        self.anticipation_repo.save_score(score_record)
        self.anticipation_repo.save_market_stats(window_stats, bill_id, company_isin)
        if val_report.errors or val_report.warnings or val_report.rejected_evidence_count > 0:
            self.anticipation_repo.save_validation_report(val_report)

        return score_record, val_report

    def analyze_bill(
        self, bill_id: str, force_refresh: bool = False
    ) -> tuple[Optional[BillAnticipationRecord], AnticipationValidationReport]:
        """
        Aggregate anticipation evaluations across all companies associated with a bill.
        """
        report = AnticipationValidationReport(bill_id=bill_id)

        bill = self.bill_repo.get(bill_id)
        if not bill:
            report.add_error(f"Bill '{bill_id}' not found.")
            return None, report

        if not bill.introduction_date:
            report.add_error(f"Bill '{bill_id}' has no introduction date.")
            return None, report

        intro_date_str = bill.introduction_date.strftime("%Y-%m-%d")

        # Get all market models for this bill
        models = self.market_model_repo.get_by_bill(bill_id)
        if not models:
            report.add_error(f"No market models found for bill '{bill_id}'.")
            return None, report

        company_scores: list[AnticipationScore] = []
        for model in models:
            score, pair_report = self.analyze_single_pair(model, force_refresh=force_refresh)
            report.merge(pair_report)
            if score:
                company_scores.append(score)

        if not company_scores:
            report.add_error(f"No company scores successfully computed for bill '{bill_id}'.")
            return None, report

        # Aggregate metrics
        n_total = len(company_scores)
        flagged_count = sum(1 for cs in company_scores if cs.anticipation_flag)
        pct_flagged = float(flagged_count / n_total) if n_total > 0 else 0.0

        scores_arr = np.array([cs.anticipation_score for cs in company_scores])
        market_arr = np.array([cs.market_signal_score for cs in company_scores])
        info_arr = np.array([cs.information_signal_score for cs in company_scores])

        # Overall bill score: weighted 70% mean, 30% max company score
        mean_score = float(np.mean(scores_arr))
        max_score = float(np.max(scores_arr))
        overall_score = round(0.70 * mean_score + 0.30 * max_score, 4)

        overall_classification = self.scorer.classify(overall_score).value
        overall_flag = overall_score >= self.scorer.flag_threshold

        # Confidence: High if >= 3 companies and majority High/Med
        high_conf_count = sum(1 for cs in company_scores if cs.confidence == "HIGH")
        med_conf_count = sum(1 for cs in company_scores if cs.confidence == "MEDIUM")
        if high_conf_count >= 2:
            overall_confidence = "HIGH"
        elif (high_conf_count + med_conf_count) >= 1:
            overall_confidence = "MEDIUM"
        else:
            overall_confidence = "LOW"

        media_data_available = any(cs.media_data_available for cs in company_scores)
        total_evidence_count = sum(cs.evidence_count for cs in company_scores)

        decision_reason = (
            f"Bill-level anticipation score {overall_score:.4f} ({overall_classification}). "
            f"{flagged_count}/{n_total} associated companies flagged ({pct_flagged * 100.0:.1f}%). "
            f"Mean score: {mean_score:.4f}, Peak company score: {max_score:.4f}."
        )

        bill_record = BillAnticipationRecord(
            bill_id=bill_id,
            bill_title=bill.title,
            official_introduction_date=intro_date_str,
            overall_anticipation_score=overall_score,
            overall_classification=overall_classification,
            overall_anticipation_flag=overall_flag,
            overall_confidence=overall_confidence,
            total_companies_analyzed=n_total,
            companies_with_anticipation_flag=flagged_count,
            pct_companies_flagged=pct_flagged,
            mean_market_signal_score=float(np.mean(market_arr)),
            mean_info_signal_score=float(np.mean(info_arr)),
            total_evidence_count=total_evidence_count,
            media_data_available=media_data_available,
            company_scores=company_scores,
            decision_reason=decision_reason,
            calculation_timestamp=datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        )

        self.anticipation_repo.save_bill_score(bill_record)
        return bill_record, report

    def run_all(
        self,
        year: Optional[int] = None,
        bill_id_filter: Optional[str] = None,
        company_isin_filter: Optional[str] = None,
        force_refresh: bool = False,
        skip_existing: bool = True,
    ) -> dict[str, Any]:
        """
        Execute full anticipation bias analysis across matching market models and bills.
        """
        models = self.market_model_repo.get_all()

        filtered_models: list[MarketModelRecord] = []
        for m in models:
            if bill_id_filter and m.bill_id != bill_id_filter:
                continue
            if company_isin_filter and m.company_isin != company_isin_filter:
                continue
            if year:
                b = self.bill_repo.get(m.bill_id)
                if not b or b.year != year:
                    continue
            filtered_models.append(m)

        logger.info(
            "Starting Anticipation Bias Engine | models=%d force_refresh=%s skip_existing=%s",
            len(filtered_models),
            force_refresh,
            skip_existing,
        )

        stats_summary: dict[str, Any] = {
            "models_processed": 0,
            "models_succeeded": 0,
            "models_skipped": 0,
            "models_failed": 0,
            "bills_analyzed": 0,
            "flagged_pairs": 0,
            "flagged_bills": 0,
            "classifications": {
                AnticipationClassification.NO_EVIDENCE.value: 0,
                AnticipationClassification.WEAK_EVIDENCE.value: 0,
                AnticipationClassification.MODERATE_EVIDENCE.value: 0,
                AnticipationClassification.STRONG_EVIDENCE.value: 0,
            },
            "errors": {},
        }

        bills_seen: set[str] = set()

        for model in filtered_models:
            stats_summary["models_processed"] += 1
            key = f"{model.bill_id}_{model.company_isin}"

            if not force_refresh and skip_existing and self.anticipation_repo.score_exists(model.bill_id, model.company_isin):
                stats_summary["models_skipped"] += 1
                existing_score = self.anticipation_repo.get_score(model.bill_id, model.company_isin)
                if existing_score:
                    if existing_score.anticipation_flag:
                        stats_summary["flagged_pairs"] += 1
                    stats_summary["classifications"][existing_score.classification] = (
                        stats_summary["classifications"].get(existing_score.classification, 0) + 1
                    )
                bills_seen.add(model.bill_id)
                continue

            try:
                score, rep = self.analyze_single_pair(model, force_refresh=force_refresh)
                if score and rep.is_valid:
                    stats_summary["models_succeeded"] += 1
                    if score.anticipation_flag:
                        stats_summary["flagged_pairs"] += 1
                    stats_summary["classifications"][score.classification] = (
                        stats_summary["classifications"].get(score.classification, 0) + 1
                    )
                    bills_seen.add(model.bill_id)
                else:
                    stats_summary["models_failed"] += 1
                    stats_summary["errors"][key] = rep.errors
            except Exception as exc:
                stats_summary["models_failed"] += 1
                stats_summary["errors"][key] = [str(exc)]

        # Aggregate across distinct bills
        for b_id in sorted(bills_seen):
            try:
                bill_rec, b_rep = self.analyze_bill(b_id, force_refresh=force_refresh)
                if bill_rec:
                    stats_summary["bills_analyzed"] += 1
                    if bill_rec.overall_anticipation_flag:
                        stats_summary["flagged_bills"] += 1
            except Exception as exc:
                logger.error("Failed bill-level rollup for %s: %s", b_id, exc)

        logger.info(
            "Anticipation analysis complete | processed=%d succeeded=%d skipped=%d failed=%d flagged_pairs=%d",
            stats_summary["models_processed"],
            stats_summary["models_succeeded"],
            stats_summary["models_skipped"],
            stats_summary["models_failed"],
            stats_summary["flagged_pairs"],
        )

        return stats_summary
