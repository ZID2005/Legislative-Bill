"""
decision_support/engine.py
==========================
Master orchestrator for the Decision Support & Risk Scoring Engine (Task 7.2).

Coordinates:
1. Retrieval of existing prediction outputs from `PredictionRepository`.
2. Integration with Task 6.5 `AnticipationRepository` for pricing-in context.
3. Enrichment with domain knowledge from `BillRepository`, `CompanyRepository`, and `MappingRepository`.
4. Pre-synthesis integrity and compatibility audit via `DecisionSupportValidator`.
5. Deterministic mathematical scoring via `RiskScorer`.
6. Synthesis of Investor, Business, and Public perspectives via `StakeholderSynthesizer`.
7. Post-synthesis validation and persistence of `DecisionSupportRecord` and `DecisionValidationReport`.
8. Incremental caching execution (skips unchanged records unless `--force-refresh` is specified).

Zero-Retraining & Anti-Leakage
------------------------------
- Never retrains machine learning estimators.
- Never generates new model predictions.
- Never consumes post-event market prices, CAR, or ground-truth labels.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from decision_support.risk_scorer import RiskScorer
from decision_support.stakeholder_synthesizer import StakeholderSynthesizer
from decision_support.validator import DecisionSupportValidator
from schemas.decision import (
    DecisionSupportRecord,
    DecisionValidationReport,
    make_decision_id,
)
from schemas.prediction import PredictionRecord
from storage.anticipation_repository import AnticipationRepository
from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.decision_repository import DecisionRepository
from storage.mapping_repository import MappingRepository
from storage.prediction_repository import PredictionRepository

logger = get_logger(__name__)

CURRENT_MODEL_VERSION = "v1.0"
CURRENT_FEATURE_VERSION = "v1.0"
CURRENT_DECISION_VERSION = "v1.0"


class DecisionSupportEngine:
    """
    Master engine synthesizing qualitative multi-stakeholder decision interpretations
    and deterministic composite risk scores from validated Task 7.1 predictions.

    Parameters
    ----------
    prediction_repo : PredictionRepository, optional
    anticipation_repo : AnticipationRepository, optional
    decision_repo : DecisionRepository, optional
    bill_repo : BillRepository, optional
    company_repo : CompanyRepository, optional
    mapping_repo : MappingRepository, optional
    risk_scorer : RiskScorer, optional
    synthesizer : StakeholderSynthesizer, optional
    validator : DecisionSupportValidator, optional
    """

    def __init__(
        self,
        prediction_repo: Optional[PredictionRepository] = None,
        anticipation_repo: Optional[AnticipationRepository] = None,
        decision_repo: Optional[DecisionRepository] = None,
        bill_repo: Optional[BillRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        mapping_repo: Optional[MappingRepository] = None,
        risk_scorer: Optional[RiskScorer] = None,
        synthesizer: Optional[StakeholderSynthesizer] = None,
        validator: Optional[DecisionSupportValidator] = None,
    ) -> None:
        self.prediction_repo = prediction_repo or PredictionRepository()
        self.anticipation_repo = anticipation_repo or AnticipationRepository()
        self.decision_repo = decision_repo or DecisionRepository()
        self.bill_repo = bill_repo or BillRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.mapping_repo = mapping_repo or MappingRepository()

        self.risk_scorer = risk_scorer or RiskScorer()
        self.synthesizer = synthesizer or StakeholderSynthesizer()
        self.validator = validator or DecisionSupportValidator()

        logger.debug("DecisionSupportEngine initialised.")

    def run_all(
        self,
        bill_id_filter: Optional[str] = None,
        company_isin_filter: Optional[str] = None,
        year_filter: Optional[int] = None,
        event_window_filter: Optional[str] = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """
        Execute decision-support generation across matching predictions.

        Parameters
        ----------
        bill_id_filter : str, optional
        company_isin_filter : str, optional
        year_filter : int, optional
        event_window_filter : str, optional
        force_refresh : bool, optional

        Returns
        -------
        dict[str, Any]
            Execution summary statistics and list of generated DecisionSupportRecords.
        """
        all_predictions = self.prediction_repo.load_all()
        logger.info("Loaded %d candidate prediction records from disk.", len(all_predictions))

        bill_year_cache: dict[str, Optional[int]] = {}
        candidates: list[PredictionRecord] = []
        for pred in all_predictions:
            if bill_id_filter and pred.bill_id != bill_id_filter:
                continue
            if company_isin_filter and pred.company_isin != company_isin_filter:
                continue
            if event_window_filter and pred.event_window != event_window_filter:
                continue
            if year_filter is not None:
                if pred.bill_id not in bill_year_cache:
                    b = self.bill_repo.get(pred.bill_id)
                    bill_year_cache[pred.bill_id] = b.year if b else None
                if bill_year_cache[pred.bill_id] != year_filter:
                    continue
            candidates.append(pred)

        logger.info("Filtered down to %d candidate predictions to process.", len(candidates))

        stats: dict[str, Any] = {
            "total_candidates": len(candidates),
            "decisions_generated": 0,
            "decisions_skipped": 0,
            "decisions_failed": 0,
            "risk_distribution": {
                "VERY_LOW": 0,
                "LOW": 0,
                "MODERATE": 0,
                "HIGH": 0,
                "VERY_HIGH": 0,
            },
            "pricing_in_distribution": {
                "VERY_LOW": 0,
                "LOW": 0,
                "MODERATE": 0,
                "HIGH": 0,
            },
            "records": [],
            "reports": [],
        }

        bill_cache: dict[str, Optional[Bill]] = {}
        company_cache: dict[str, Optional[Company]] = {}
        mapping_cache: dict[str, Optional[BillCompanyMapping]] = {}
        anticip_cache: dict[tuple[str, str], Any] = {}

        for idx, pred in enumerate(candidates, start=1):
            dec_id = make_decision_id(pred.bill_id, pred.company_isin, pred.event_window)

            # Incremental Execution Check
            if not force_refresh and self.decision_repo.exists(
                pred.bill_id, pred.company_isin, pred.event_window
            ):
                existing = self.decision_repo.get(dec_id)
                if (
                    existing is not None
                    and existing.model_version == CURRENT_MODEL_VERSION
                    and existing.feature_version == CURRENT_FEATURE_VERSION
                    and existing.decision_version == CURRENT_DECISION_VERSION
                ):
                    stats["decisions_skipped"] += 1
                    stats["records"].append(existing)
                    stats["risk_distribution"][existing.risk_category] = (
                        stats["risk_distribution"].get(existing.risk_category, 0) + 1
                    )
                    stats["pricing_in_distribution"][existing.pricing_in_risk] = (
                        stats["pricing_in_distribution"].get(existing.pricing_in_risk, 0) + 1
                    )
                    continue

            # Cache Lookups
            if pred.bill_id not in bill_cache:
                bill_cache[pred.bill_id] = self.bill_repo.get(pred.bill_id)
            bill = bill_cache[pred.bill_id]

            if pred.company_isin not in company_cache:
                if hasattr(self.company_repo, "get_by_isin"):
                    company_cache[pred.company_isin] = self.company_repo.get_by_isin(pred.company_isin)
                else:
                    company_cache[pred.company_isin] = getattr(self.company_repo, "get", lambda _: None)(pred.company_isin)
            company = company_cache[pred.company_isin]

            if pred.bill_id not in mapping_cache:
                mapping_cache[pred.bill_id] = self.mapping_repo.get(pred.bill_id)
            mapping = mapping_cache[pred.bill_id]

            # Process Candidate
            record, report = self.generate_decision_for_prediction(
                prediction=pred,
                bill=bill,
                company=company,
                mapping=mapping,
                anticip_cache=anticip_cache,
                force_refresh=force_refresh,
            )

            if report:
                self.decision_repo.save_validation_report(report)
                stats["reports"].append(report)

            if record is not None and report is not None and report.is_valid:
                self.decision_repo.save(record)
                stats["decisions_generated"] += 1
                stats["records"].append(record)
                stats["risk_distribution"][record.risk_category] = (
                    stats["risk_distribution"].get(record.risk_category, 0) + 1
                )
                stats["pricing_in_distribution"][record.pricing_in_risk] = (
                    stats["pricing_in_distribution"].get(record.pricing_in_risk, 0) + 1
                )
            else:
                stats["decisions_failed"] += 1

            if idx % 50 == 0 or idx == len(candidates):
                logger.info("Processed decision support candidate %d/%d...", idx, len(candidates))

        logger.info(
            "DecisionSupportEngine run complete: generated=%d skipped=%d failed=%d",
            stats["decisions_generated"],
            stats["decisions_skipped"],
            stats["decisions_failed"],
        )
        return stats

    def generate_decision_for_prediction(
        self,
        prediction: PredictionRecord,
        bill: Optional[Bill] = None,
        company: Optional[Company] = None,
        mapping: Optional[BillCompanyMapping] = None,
        anticip_cache: Optional[dict[tuple[str, str], Any]] = None,
        force_refresh: bool = False,
    ) -> tuple[Optional[DecisionSupportRecord], Optional[DecisionValidationReport]]:
        """
        Synthesize a DecisionSupportRecord for a single PredictionRecord.
        """
        if bill is None:
            bill = self.bill_repo.get(prediction.bill_id)
        if company is None:
            if hasattr(self.company_repo, "get_by_isin"):
                company = self.company_repo.get_by_isin(prediction.company_isin)
            else:
                company = getattr(self.company_repo, "get", lambda _: None)(prediction.company_isin)
        if mapping is None:
            mapping = self.mapping_repo.get(prediction.bill_id)

        # 1. Validate Inputs
        pre_val_report = self.validator.validate_inputs(
            prediction=prediction,
            bill=bill,
            company=company,
            mapping=mapping,
            expected_model_version=CURRENT_MODEL_VERSION,
            expected_feature_version=CURRENT_FEATURE_VERSION,
        )

        if not pre_val_report.is_valid:
            logger.warning(
                "Pre-decision validation failed for (%s, %s): %s",
                prediction.bill_id,
                prediction.company_isin,
                pre_val_report.errors,
            )
            return None, pre_val_report

        # 2. Enrich with Anticipation if not present in prediction
        a_score = prediction.anticipation_score
        a_class = prediction.anticipation_class
        if a_score == 0.0 or a_class == "NOT_ANALYZED":
            key = (prediction.bill_id, prediction.company_isin)
            if anticip_cache is not None and key in anticip_cache:
                anticip_rec = anticip_cache[key]
            else:
                anticip_rec = self.anticipation_repo.get_score(
                    prediction.bill_id, prediction.company_isin
                )
                if anticip_cache is not None:
                    anticip_cache[key] = anticip_rec

            if anticip_rec is not None:
                a_score = float(anticip_rec.anticipation_score)
                a_class = str(anticip_rec.classification)

        # 3. Compute Composite Confidence & Pricing-In
        conf_scalar, conf_cat = self.risk_scorer.compute_confidence_score(
            confidence_probs=prediction.confidence_probability,
            model_confidence=prediction.model_confidence,
        )
        pricing_in_score, pricing_in_risk = self.risk_scorer.compute_pricing_in_risk(
            anticipation_score=a_score,
            anticipation_class=a_class,
        )

        # 4. Compute Impact Score and Risk Score
        impact_score, impact_cat = self.risk_scorer.compute_impact_score(
            direction_probs=prediction.direction_probability,
            market_moving_prob=prediction.market_moving_probability,
            impact_probs=prediction.impact_probabilities,
            confidence_scalar=conf_scalar,
            anticipation_score=a_score,
            predicted_direction=prediction.predicted_direction,
        )
        risk_score, risk_cat = self.risk_scorer.compute_risk_score(
            confidence_scalar=conf_scalar,
            anticipation_score=a_score,
            market_moving_prob=prediction.market_moving_probability,
            impact_probs=prediction.impact_probabilities,
            direction_probs=prediction.direction_probability,
        )

        # 5. Synthesize Stakeholder Perspectives
        investor_summary = self.synthesizer.generate_investor_summary(
            prediction=prediction,
            impact_score=impact_score,
            risk_score=risk_score,
            risk_category=risk_cat,
            pricing_in_risk=pricing_in_risk,
        )
        business_summary = self.synthesizer.generate_business_summary(
            prediction=prediction,
            company=company,
            bill=bill,
            mapping=mapping,
        )
        public_summary = self.synthesizer.generate_public_summary(
            bill=bill,
            prediction=prediction,
        )
        decision_reason = self.synthesizer.synthesize_decision_reason(
            prediction=prediction,
            impact_score=impact_score,
            risk_score=risk_score,
            risk_category=risk_cat,
            pricing_in_risk=pricing_in_risk,
            investor_summary=investor_summary,
        )

        # 6. Build DecisionSupportRecord
        company_name = (company.company_name if company else None) or prediction.company_name or ""
        company_symbol = (company.ticker_nse if company else None) or prediction.company_symbol or ""
        sector = (company.sector if company else None) or ""

        record = DecisionSupportRecord(
            decision_id="",
            bill_id=prediction.bill_id,
            company_isin=prediction.company_isin,
            company_name=company_name,
            company_symbol=company_symbol,
            sector=sector,
            event_window=prediction.event_window,
            predicted_direction=prediction.predicted_direction,
            direction_probability=prediction.direction_probability,
            market_moving_probability=prediction.market_moving_probability,
            predicted_impact_strength=prediction.predicted_impact_strength,
            impact_probabilities=prediction.impact_probabilities,
            predicted_confidence=prediction.predicted_confidence,
            confidence_probability=prediction.confidence_probability,
            confidence_score=conf_scalar,
            anticipation_class=a_class,
            anticipation_score=a_score,
            impact_score=impact_score,
            impact_category=impact_cat,
            risk_score=risk_score,
            risk_category=risk_cat,
            pricing_in_risk=pricing_in_risk,
            pricing_in_score=pricing_in_score,
            investor_summary=investor_summary,
            business_summary=business_summary,
            public_summary=public_summary,
            decision_reason=decision_reason,
            model_version=prediction.model_version,
            feature_version=prediction.feature_version,
            decision_version=CURRENT_DECISION_VERSION,
            generation_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            data_quality_status=prediction.data_quality_status,
        )

        # 7. Post-Validation
        post_val_report = self.validator.validate_decision_record(record)
        if not post_val_report.is_valid:
            logger.error(
                "Post-decision validation failed for (%s, %s): %s",
                prediction.bill_id,
                prediction.company_isin,
                post_val_report.errors,
            )
            return None, post_val_report

        return record, post_val_report
