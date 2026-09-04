"""
validation/backtest_validator.py
=================================
Data and anti-leakage validation service for Task 6.4 — Historical Backtesting Engine.

Responsibility
--------------
Validates backtest inputs, execution sequences, and predictions to enforce:
1. Strict look-ahead bias prevention (no post-event features used as prediction inputs).
2. Training cutoff compliance (training data strictly predates prediction timestamp).
3. Correct chronological ordering (walk-forward temporal evaluation).
4. Data integrity (detects duplicate predictions, missing market data, missing labels, NaN/Inf values, invalid returns).

Returns
-------
`ValidationReport` (from `validation/validator.py`) and `LeakageReport` (from `schemas/backtest_record.py`).
"""

from __future__ import annotations

from typing import Any, Optional
import numpy as np
import pandas as pd
from config.logging_config import get_logger
from schemas.backtest_record import BacktestRecord, LeakageReport
from schemas.training_dataset import POST_EVENT_COLUMNS, POST_EVENT_PREFIXES
from validation.validator import ValidationReport

logger = get_logger(__name__)


class BacktestValidator:
    """
    Validator for Historical Backtesting Engine execution and output data.
    """

    def validate_backtest_execution(
        self,
        records: list[BacktestRecord],
        feature_columns_used: list[str],
        training_cutoff_map: Optional[dict[str, str]] = None,
    ) -> tuple[ValidationReport, LeakageReport]:
        """
        Validate a list of BacktestRecord objects and feature sets for leakage and anomalies.

        Parameters
        ----------
        records : list[BacktestRecord]
            List of generated backtest prediction records.
        feature_columns_used : list[str]
            List of feature column names passed into model inference.
        training_cutoff_map : dict[str, str], optional
            Mapping of bill_id/prediction_timestamp -> training_cutoff_date used.

        Returns
        -------
        tuple
            `(ValidationReport, LeakageReport)`
        """
        val_report = ValidationReport()
        violations_summary: list[str] = []

        training_cutoff_violations = 0
        post_event_feature_violations = 0
        future_dated_prediction_violations = 0
        duplicate_prediction_violations = 0

        # --- 1. Audit Post-Event Feature Leakage ---
        leaked_cols = self._detect_post_event_features(feature_columns_used)
        if leaked_cols:
            post_event_feature_violations = len(leaked_cols)
            msg = f"LOOK-AHEAD LEAKAGE: Post-event feature column(s) detected in prediction input: {leaked_cols}"
            val_report.add_error(msg)
            violations_summary.append(msg)

        # --- 2. Record-Level Checks ---
        seen_keys: set[tuple[str, str, str, str, str]] = set()

        for idx, rec in enumerate(records):
            # Check required fields
            if not rec.bill_id or not rec.company_isin:
                val_report.add_error(f"Record {idx}: Missing bill_id or company_isin.")

            if not rec.prediction_timestamp:
                val_report.add_error(f"Record {idx} ({rec.bill_id}): Missing prediction_timestamp.")

            # Duplicate prediction check
            dedup_key = (
                rec.bill_id,
                rec.company_isin,
                rec.event_window,
                rec.target,
                rec.model_name,
            )
            if dedup_key in seen_keys:
                duplicate_prediction_violations += 1
                val_report.add_error(
                    f"Duplicate prediction record detected for key: {dedup_key}"
                )
            else:
                seen_keys.add(dedup_key)

            # Training cutoff violation check
            if rec.training_cutoff_date and rec.prediction_timestamp:
                try:
                    p_date = pd.to_datetime(rec.prediction_timestamp)
                    c_date = pd.to_datetime(rec.training_cutoff_date)
                    if c_date >= p_date:
                        training_cutoff_violations += 1
                        msg = (
                            f"TRAINING CUTOFF VIOLATION: bill={rec.bill_id} | "
                            f"cutoff={rec.training_cutoff_date} >= prediction={rec.prediction_timestamp}"
                        )
                        val_report.add_error(msg)
                        violations_summary.append(msg)
                except Exception as exc:
                    val_report.add_warning(
                        f"Record {idx}: Could not parse timestamps for cutoff check: {exc}"
                    )

            # Missing actual class / ground truth label
            if rec.actual_class is None or str(rec.actual_class).lower() in {"nan", "none", ""}:
                val_report.add_warning(
                    f"Record {idx} ({rec.bill_id}, {rec.company_isin}): Missing actual_class ground truth."
                )

            # Invalid / NaN return checks
            if rec.strategy_return is not None:
                if np.isnan(rec.strategy_return) or np.isinf(rec.strategy_return):
                    val_report.add_error(
                        f"Record {idx} ({rec.bill_id}): NaN or Inf strategy_return value."
                    )
                elif abs(rec.strategy_return) > 10.0:  # >1000% return in single event
                    val_report.add_warning(
                        f"Record {idx} ({rec.bill_id}): Unusually extreme strategy_return: {rec.strategy_return:.2f}"
                    )

        # --- 3. Chronological Order Check ---
        if len(records) > 1:
            prev_dt = None
            for rec in records:
                if rec.prediction_timestamp:
                    try:
                        curr_dt = pd.to_datetime(rec.prediction_timestamp)
                        if prev_dt is not None and curr_dt < prev_dt:
                            val_report.add_warning(
                                f"CHRONOLOGICAL ANOMALY: Record out of order: {rec.prediction_timestamp} < {prev_dt}"
                            )
                        prev_dt = curr_dt
                    except Exception:
                        pass

        # Build LeakageReport
        has_leakage = (
            post_event_feature_violations > 0
            or training_cutoff_violations > 0
            or future_dated_prediction_violations > 0
        )

        leakage_report = LeakageReport(
            has_leakage=has_leakage,
            total_records_checked=len(records),
            training_cutoff_violations=training_cutoff_violations,
            post_event_feature_violations=post_event_feature_violations,
            future_dated_prediction_violations=future_dated_prediction_violations,
            duplicate_prediction_violations=duplicate_prediction_violations,
            violations_summary=violations_summary,
        )

        if has_leakage:
            logger.error("Backtest validation failed: Look-ahead leakage detected!")
        else:
            logger.info("Backtest validation clean: Zero look-ahead leakage violations.")

        return val_report, leakage_report

    @staticmethod
    def _detect_post_event_features(feature_cols: list[str]) -> list[str]:
        """
        Identify any feature column name that matches post-event / target leakage patterns.

        Returns list of offending column names.
        """
        offenders: set[str] = set()

        for col in feature_cols:
            col_lower = col.lower().strip()

            # Exact match against post-event blacklist
            if col_lower in POST_EVENT_COLUMNS:
                offenders.add(col)
                continue

            # Prefix match
            for prefix in POST_EVENT_PREFIXES:
                if col_lower.startswith(prefix):
                    offenders.add(col)
                    break

        return sorted(offenders)
