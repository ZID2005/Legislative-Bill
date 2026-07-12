"""
services/statistical_service.py
===============================
Service to calculate statistical significance of Cumulative Abnormal Returns (CAR).
"""

from __future__ import annotations

import datetime
import math
from typing import Any, Optional

import scipy.stats as stats

from config.logging_config import get_logger
from config.settings import settings
from schemas.event_study import EventStudyRecord
from schemas.statistical_result import StatisticalResult
from storage.bill_repository import BillRepository
from storage.event_study_repository import EventStudyRepository
from storage.market_model_repository import MarketModelRepository
from storage.statistical_repository import StatisticalRepository
from validation.statistical_validator import StatisticalValidator
from validation.validator import ValidationReport

logger = get_logger(__name__)


class StatisticalSignificanceService:
    """
    Service for calculating and analyzing the statistical significance of abnormal returns.
    """

    def __init__(
        self,
        event_study_repo: Optional[EventStudyRepository] = None,
        market_model_repo: Optional[MarketModelRepository] = None,
        statistical_repo: Optional[StatisticalRepository] = None,
        bill_repo: Optional[BillRepository] = None,
        validator: Optional[StatisticalValidator] = None,
    ) -> None:
        self.event_study_repo = event_study_repo or EventStudyRepository()
        self.market_model_repo = market_model_repo or MarketModelRepository()
        self.statistical_repo = statistical_repo or StatisticalRepository()
        self.bill_repo = bill_repo or BillRepository()
        self.validator = validator or StatisticalValidator()

    def calculate_significance(
        self,
        event_study: EventStudyRecord,
        force_refresh: bool = False,
    ) -> tuple[Optional[StatisticalResult], ValidationReport]:
        """
        Compute statistical significance for a single Event Study record.
        """
        report = ValidationReport()

        # Check for cached results if force_refresh is False
        if not force_refresh and self.statistical_repo.exists(
            event_study.bill_id, event_study.company_isin, event_study.event_window
        ):
            logger.debug(
                "Statistical result already exists for bill %s, company %s, window %s. Skipping.",
                event_study.bill_id,
                event_study.company_isin,
                event_study.event_window,
            )
            existing = self.statistical_repo.get(
                event_study.bill_id, event_study.company_isin, event_study.event_window
            )
            return existing, report

        # Load corresponding market model record
        market_model = self.market_model_repo.get(event_study.bill_id, event_study.company_isin)
        if not market_model:
            report.add_error(
                f"Market model record not found for bill {event_study.bill_id} "
                f"and company {event_study.company_isin}."
            )
            return None, report

        # Calculate metrics
        car = event_study.final_car
        N = event_study.observation_count  # Days in event window
        residual_variance = market_model.residual_variance

        # CAR Variance: Var(CAR) = N * residual_variance
        variance = N * residual_variance
        standard_error = math.sqrt(variance) if variance >= 0 else float("nan")
        df = market_model.n_observations - 2

        # Validate
        val_report = self.validator.validate_calculation(car, variance, standard_error, df)
        report.merge(val_report)
        if not report.is_valid:
            return None, report

        # Compute t-statistic, p-value, and confidence interval
        t_statistic = car / standard_error
        p_value = float(2.0 * stats.t.sf(abs(t_statistic), df))

        # 95% Confidence Interval
        t_crit = float(stats.t.ppf(0.975, df))
        margin_of_error = t_crit * standard_error
        confidence_interval = [car - margin_of_error, car + margin_of_error]

        # Determine Significance Flag
        alpha = settings.STAT_SIGNIFICANCE_ALPHA
        t_thresh = settings.STAT_SIGNIFICANCE_T_THRESHOLD
        significant = (abs(t_statistic) > t_thresh) and (p_value < alpha)

        # Determine Significance Level
        # 1%, 5%, 10%, or Not Significant
        if p_value < 0.01:
            confidence_level = "1%"
        elif p_value < 0.05:
            confidence_level = "5%"
        elif p_value < 0.10:
            confidence_level = "10%"
        else:
            confidence_level = "Not Significant"

        # Determine Effect Size
        # Small, Medium, Large based on CAR thresholds
        abs_car = abs(car)
        if abs_car >= settings.EFFECT_SIZE_LARGE_THRESHOLD:
            effect_size = "Large"
        elif abs_car >= settings.EFFECT_SIZE_MEDIUM_THRESHOLD:
            effect_size = "Medium"
        else:
            effect_size = "Small"

        # Decision Reason
        significance_word = "Significant" if significant else "Not significant"
        decision_reason = (
            f"{significance_word} because p={p_value:.4f} and |t|={abs(t_statistic):.2f}"
        )

        # Create result object
        result = StatisticalResult(
            bill_id=event_study.bill_id,
            company=event_study.company_isin,
            company_symbol=event_study.company_symbol,
            event_window=event_study.event_window,
            car=car,
            variance=variance,
            standard_error=standard_error,
            t_statistic=t_statistic,
            p_value=p_value,
            confidence_interval=confidence_interval,
            significant=significant,
            confidence_level=confidence_level,
            effect_size=effect_size,
            decision_reason=decision_reason,
            calculation_timestamp=datetime.datetime.now(datetime.timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
        )

        # Save record
        self.statistical_repo.save(result)
        return result, report

    def run_calculations(
        self,
        year: Optional[int] = None,
        bill_id_filter: Optional[str] = None,
        company_isin_filter: Optional[str] = None,
        window_filter: Optional[str] = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Run statistical significance calculations for all matching event studies.
        """
        event_studies = self.event_study_repo.get_all()

        stats_summary = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
            "errors": {},
        }

        for es in event_studies:
            # Filters
            if bill_id_filter and es.bill_id != bill_id_filter:
                continue
            if company_isin_filter and es.company_isin != company_isin_filter:
                continue
            if window_filter and es.event_window != window_filter:
                continue
            if year:
                bill = self.bill_repo.get(es.bill_id)
                if not bill or bill.year != year:
                    continue

            stats_summary["processed"] += 1

            # Check if exists and force_refresh is False to increment skipped count
            if not force_refresh and self.statistical_repo.exists(
                es.bill_id, es.company_isin, es.event_window
            ):
                stats_summary["skipped"] += 1
                continue

            try:
                result, report = self.calculate_significance(es, force_refresh)
                if report.is_valid and result:
                    stats_summary["succeeded"] += 1
                else:
                    stats_summary["failed"] += 1
                    key = f"{es.bill_id}_{es.company_isin}_{es.event_window}"
                    stats_summary["errors"][key] = report.errors
            except Exception as e:
                stats_summary["failed"] += 1
                key = f"{es.bill_id}_{es.company_isin}_{es.event_window}"
                stats_summary["errors"][key] = [str(e)]
                logger.error(
                    "Error calculating statistical significance for %s - %s - %s: %s",
                    es.bill_id,
                    es.company_isin,
                    es.event_window,
                    e,
                )

        return stats_summary
