"""
validation/anticipation_validator.py
====================================
Validation and anti-leakage audit service for Task 6.5 — Anticipation Bias Engine.

Responsibility
--------------
1. Enforce strict anti-leakage rule: publication_timestamp < official_introduction_timestamp.
2. Reject post-T0 evidence and create structured audit trail.
3. Validate completeness of input entities (bill, company, market model, price data).
4. Verify sanity of pre-event statistics (NaN/Inf detection, observation thresholds).
5. Verify valid ranges and classification consistency for anticipation scores.
"""

from __future__ import annotations

import math
from typing import Any, Optional
import numpy as np
import pandas as pd

from config.logging_config import get_logger
from config.settings import settings
from schemas.anticipation import (
    AnticipationClassification,
    AnticipationScore,
    AnticipationValidationReport,
    EvidenceType,
    InformationEvidence,
    PreEventWindowStats,
)
from schemas.bill import Bill
from schemas.company import Company
from schemas.market_model import MarketModelRecord

logger = get_logger(__name__)


class AnticipationValidator:
    """
    Validator for anticipation bias inputs, external evidence anti-leakage, and calculation sanity.
    """

    def __init__(
        self,
        min_window_obs: Optional[int] = None,
        min_cumulative_obs: Optional[int] = None,
    ) -> None:
        self.min_window_obs = (
            min_window_obs
            if min_window_obs is not None
            else settings.ANTICIPATION_MIN_OBSERVATIONS_PER_WINDOW
        )
        self.min_cumulative_obs = (
            min_cumulative_obs
            if min_cumulative_obs is not None
            else settings.ANTICIPATION_MIN_CUMULATIVE_OBSERVATIONS
        )

    def validate_inputs(
        self,
        bill: Optional[Bill],
        company: Optional[Company],
        market_model: Optional[MarketModelRecord],
        company_prices: pd.DataFrame,
        benchmark_prices: pd.DataFrame,
    ) -> AnticipationValidationReport:
        """
        Validate prerequisite domain entities and price histories.
        """
        bill_id = bill.bill_id if bill else "unknown"
        company_isin = company.isin if company else None
        report = AnticipationValidationReport(bill_id=bill_id, company_isin=company_isin)

        # 1. Bill check
        if not bill:
            report.add_error("Bill record is missing.")
            return report

        if not bill.introduction_date:
            report.add_error(f"Bill '{bill.bill_id}' has no official introduction_date (T0).")

        # 2. Company check
        if not company:
            report.add_error("Company record is missing.")
            return report

        # 3. Market Model check
        if not market_model:
            report.add_error(f"Market model is missing for bill '{bill.bill_id}' and company '{company.isin}'.")
        else:
            if math.isnan(market_model.alpha) or math.isnan(market_model.beta):
                report.add_error("Market model alpha/beta parameters contain NaN.")
            if market_model.residual_variance <= 0 or math.isnan(market_model.residual_variance):
                report.add_error("Market model residual_variance is non-positive or NaN.")

        # 4. Benchmark Prices
        if benchmark_prices.empty or "Date" not in benchmark_prices.columns:
            report.add_error("Benchmark price history is empty or missing 'Date' column.")

        # 5. Company Prices
        if company_prices.empty or "Date" not in company_prices.columns:
            report.add_error(f"Price history is missing for company '{company.isin}'.")

        return report

    def validate_evidence(
        self,
        evidence_items: list[InformationEvidence],
        official_introduction_date: str,
        bill_id: str,
    ) -> tuple[list[InformationEvidence], AnticipationValidationReport]:
        """
        Audit external information evidence against strict anti-leakage rules.

        Enforces:
        1. publication_date < official_introduction_date (strictly before T0).
        2. Deduplication of evidence.
        3. Relevance score in [0.0, 1.0].
        4. Valid evidence_type.

        Returns
        -------
        tuple[list[InformationEvidence], AnticipationValidationReport]
            (valid_pre_event_evidence, validation_report)
        """
        report = AnticipationValidationReport(bill_id=bill_id)
        valid_evidence: list[InformationEvidence] = []
        seen_keys: set[tuple[str, str, str]] = set()

        intro_dt_str = official_introduction_date[:10]

        for ev in evidence_items:
            # 1. Identity / bill_id match check
            if ev.bill_id != bill_id:
                report.add_error(
                    f"Evidence bill_id mismatch: expected '{bill_id}', got '{ev.bill_id}'."
                )
                continue

            pub_dt_str = ev.publication_date[:10] if ev.publication_date else ""

            # 2. Strict Anti-Leakage Audit
            if not pub_dt_str:
                report.add_rejected_evidence(ev, "Missing publication_date.")
                continue

            # Critical anti-leakage rule: MUST be strictly prior to introduction date
            if pub_dt_str >= intro_dt_str:
                reason = (
                    f"LOOK-AHEAD LEAKAGE: Publication date {pub_dt_str} >= "
                    f"Official introduction date {intro_dt_str}."
                )
                report.add_rejected_evidence(ev, reason)
                continue

            # 3. Deduplication check
            dedup_key = (ev.source.strip().lower(), ev.headline.strip().lower(), pub_dt_str)
            if dedup_key in seen_keys:
                report.add_warning(
                    f"DUPLICATE_EVIDENCE: Duplicate item detected from {ev.source}: '{ev.headline}'"
                )
                continue
            seen_keys.add(dedup_key)

            # 4. Relevance score validation
            if not (0.0 <= ev.relevance_score <= 1.0):
                report.add_warning(
                    f"Relevance score {ev.relevance_score} outside [0, 1] for '{ev.headline}'. Clamping."
                )
                ev.relevance_score = max(0.0, min(1.0, ev.relevance_score))

            # 5. Evidence type check
            valid_types = {t.value for t in EvidenceType}
            if ev.evidence_type not in valid_types:
                report.add_warning(
                    f"Unknown evidence_type '{ev.evidence_type}'. Defaulting to 'OTHER'."
                )
                ev.evidence_type = EvidenceType.OTHER.value

            valid_evidence.append(ev)

        return valid_evidence, report

    def validate_window_stats(
        self,
        stats_map: dict[str, PreEventWindowStats],
        bill_id: str,
        company_isin: str,
    ) -> AnticipationValidationReport:
        """
        Validate statistical outputs for pre-event windows.
        """
        report = AnticipationValidationReport(bill_id=bill_id, company_isin=company_isin)

        if not stats_map:
            report.add_error("No pre-event window statistics generated.")
            return report

        for win_name, stats in stats_map.items():
            # NaN / Inf checks
            for field_name, val in [
                ("mean_abnormal_return", stats.mean_abnormal_return),
                ("cumulative_abnormal_return", stats.cumulative_abnormal_return),
                ("volatility", stats.volatility),
                ("ar_z_score", stats.ar_z_score),
                ("pct_positive_ar", stats.pct_positive_ar),
                ("pct_negative_ar", stats.pct_negative_ar),
                ("p_value", stats.p_value),
            ]:
                if math.isnan(val) or math.isinf(val):
                    report.add_error(f"Window {win_name}: {field_name} contains NaN or Inf.")

            # Bounds checks
            if not (0.0 <= stats.pct_positive_ar <= 1.0):
                report.add_error(f"Window {win_name}: pct_positive_ar outside [0, 1].")
            if not (0.0 <= stats.pct_negative_ar <= 1.0):
                report.add_error(f"Window {win_name}: pct_negative_ar outside [0, 1].")
            if not (0.0 <= stats.p_value <= 1.0):
                report.add_error(f"Window {win_name}: p_value outside [0, 1].")

            # Observation count checks
            if "[-30,-1]" in win_name:
                if stats.observation_count < self.min_cumulative_obs:
                    report.add_warning(
                        f"Cumulative window {win_name} has only {stats.observation_count} observations "
                        f"(threshold: {self.min_cumulative_obs})."
                    )
            else:
                if stats.observation_count < self.min_window_obs:
                    report.add_warning(
                        f"Sub-window {win_name} has only {stats.observation_count} observations "
                        f"(threshold: {self.min_window_obs})."
                    )

        return report

    def validate_anticipation_score(
        self, score: AnticipationScore
    ) -> AnticipationValidationReport:
        """
        Validate generated AnticipationScore object for range and enum consistency.
        """
        report = AnticipationValidationReport(
            bill_id=score.bill_id, company_isin=score.company_isin
        )

        for name, val in [
            ("anticipation_score", score.anticipation_score),
            ("market_signal_score", score.market_signal_score),
            ("information_signal_score", score.information_signal_score),
        ]:
            if math.isnan(val) or math.isinf(val):
                report.add_error(f"{name} is NaN or Inf.")
            elif not (0.0 <= val <= 1.0):
                report.add_error(f"{name} value {val:.4f} is outside [0.0, 1.0].")

        valid_classes = {c.value for c in AnticipationClassification}
        if score.classification not in valid_classes:
            report.add_error(f"Invalid classification '{score.classification}'.")

        if score.confidence not in {"LOW", "MEDIUM", "HIGH"}:
            report.add_error(f"Invalid confidence '{score.confidence}'.")

        return report
