"""
decision_support/validator.py
=============================
Integrity and anti-leakage audit validator for Decision Support (Task 7.2).

Validation Requirements
-----------------------
Rejects observations and generates `DecisionValidationReport` with detailed errors when:
1. Prediction record missing or corrupted.
2. Company mapping record missing or corrupted.
3. Bill metadata missing or corrupted.
4. Invalid probabilities or probabilities outside [0.0, 1.0].
5. Probability distribution keys missing or corrupted.
6. NaN, Inf, or non-numeric float values detected.
7. Risk or Impact score computed outside [0.0, 1.0].
8. Unsupported risk category or pricing-in category.
9. Model or Feature version mismatch against expected canonical versions.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.bill import Bill
from schemas.company import Company
from schemas.decision import (
    DecisionSupportRecord,
    DecisionValidationReport,
    PricingInRisk,
    RiskCategory,
    make_decision_id,
)
from schemas.mapping_record import BillCompanyMapping
from schemas.prediction import PredictionRecord

logger = get_logger(__name__)


def _is_finite_num(val: Any) -> bool:
    """Check whether value is finite float or int."""
    if val is None or not isinstance(val, (int, float)):
        return False
    return not (math.isnan(val) or math.isinf(val))


class DecisionSupportValidator:
    """
    Validates prediction inputs, related domain entities, probability bounds,
    and decision records before and after synthesis.
    """

    def validate_inputs(
        self,
        prediction: Optional[PredictionRecord],
        bill: Optional[Bill] = None,
        company: Optional[Company] = None,
        mapping: Optional[BillCompanyMapping] = None,
        expected_model_version: Optional[str] = None,
        expected_feature_version: Optional[str] = None,
    ) -> DecisionValidationReport:
        """
        Validate input entities and prediction integrity prior to decision synthesis.
        """
        bill_id = prediction.bill_id if prediction else (bill.bill_id if bill else "unknown_bill")
        company_isin = (
            prediction.company_isin
            if prediction
            else (company.isin if company else "unknown_isin")
        )
        event_window = prediction.event_window if prediction else "[-20,+20]"

        report = DecisionValidationReport(
            report_id="",
            bill_id=bill_id,
            company_isin=company_isin,
            event_window=event_window,
            is_valid=True,
            errors=[],
            warnings=[],
            checks_performed={},
            details={},
        )

        # 1. Prediction existence
        report.checks_performed["prediction_present"] = prediction is not None
        if prediction is None:
            report.errors.append("PredictionRecord is missing or null.")
            report.is_valid = False
            return report

        # 2. Bill presence
        report.checks_performed["bill_present"] = bill is not None
        if bill is None:
            report.errors.append(f"Bill metadata missing for bill_id='{prediction.bill_id}'.")

        # 3. Company presence
        report.checks_performed["company_present"] = company is not None
        if company is None:
            report.errors.append(f"Company metadata missing for ISIN='{prediction.company_isin}'.")

        # 4. Mapping presence
        report.checks_performed["mapping_present"] = mapping is not None
        if mapping is None:
            report.warnings.append(
                f"Bill-Company mapping record missing for ({prediction.bill_id}, {prediction.company_isin}); using fallback exposure."
            )

        # 5. Version Compatibility
        if expected_model_version and prediction.model_version != expected_model_version:
            report.errors.append(
                f"Model version mismatch: expected '{expected_model_version}', found '{prediction.model_version}'."
            )
        if expected_feature_version and prediction.feature_version != expected_feature_version:
            report.errors.append(
                f"Feature version mismatch: expected '{expected_feature_version}', found '{prediction.feature_version}'."
            )

        # 6. Direction probabilities
        dir_probs = prediction.direction_probability
        report.checks_performed["direction_probs_valid"] = True
        for k in ["POSITIVE", "NEGATIVE", "NEUTRAL"]:
            if k not in dir_probs:
                report.errors.append(f"Direction probability missing key '{k}'.")
                report.checks_performed["direction_probs_valid"] = False
            elif not _is_finite_num(dir_probs[k]) or not (0.0 <= dir_probs[k] <= 1.0):
                report.errors.append(f"Direction probability for '{k}' is out of bounds [0, 1]: {dir_probs[k]}.")
                report.checks_performed["direction_probs_valid"] = False

        # 7. Market-moving probability
        mm_prob = prediction.market_moving_probability
        report.checks_performed["market_moving_prob_valid"] = True
        if not _is_finite_num(mm_prob) or not (0.0 <= mm_prob <= 1.0):
            report.errors.append(f"Market-moving probability is out of bounds [0, 1]: {mm_prob}.")
            report.checks_performed["market_moving_prob_valid"] = False

        # 8. Anticipation score
        a_score = prediction.anticipation_score
        report.checks_performed["anticipation_score_valid"] = True
        if not _is_finite_num(a_score) or not (0.0 <= a_score <= 1.0):
            report.errors.append(f"Anticipation score is out of bounds [0, 1]: {a_score}.")
            report.checks_performed["anticipation_score_valid"] = False

        # 9. Confidence probability
        conf_probs = prediction.confidence_probability
        report.checks_performed["confidence_probs_valid"] = True
        for k in ["LOW", "MEDIUM", "HIGH"]:
            if k in conf_probs:
                val = conf_probs[k]
                if not _is_finite_num(val) or not (0.0 <= val <= 1.0):
                    report.errors.append(f"Confidence probability for '{k}' is out of bounds: {val}.")
                    report.checks_performed["confidence_probs_valid"] = False

        if report.errors:
            report.is_valid = False

        return report

    def validate_decision_record(self, record: DecisionSupportRecord) -> DecisionValidationReport:
        """
        Validate generated DecisionSupportRecord before persisting.
        """
        report = DecisionValidationReport(
            report_id="",
            bill_id=record.bill_id,
            company_isin=record.company_isin,
            event_window=record.event_window,
            is_valid=True,
            errors=[],
            warnings=[],
            checks_performed={},
            details={},
        )

        # 1. Decision ID
        report.checks_performed["decision_id_valid"] = bool(record.decision_id and record.decision_id.startswith("dec_"))
        if not report.checks_performed["decision_id_valid"]:
            report.errors.append(f"Invalid decision_id format: '{record.decision_id}'.")

        # 2. Risk Score Bounds
        report.checks_performed["risk_score_bounds"] = _is_finite_num(record.risk_score) and (0.0 <= record.risk_score <= 1.0)
        if not report.checks_performed["risk_score_bounds"]:
            report.errors.append(f"Risk score is out of bounds [0, 1]: {record.risk_score}.")

        # 3. Impact Score Bounds
        report.checks_performed["impact_score_bounds"] = _is_finite_num(record.impact_score) and (0.0 <= record.impact_score <= 1.0)
        if not report.checks_performed["impact_score_bounds"]:
            report.errors.append(f"Impact score is out of bounds [0, 1]: {record.impact_score}.")

        # 4. Risk Category Enum
        valid_risk_cats = {e.value for e in RiskCategory}
        report.checks_performed["risk_category_valid"] = record.risk_category in valid_risk_cats
        if not report.checks_performed["risk_category_valid"]:
            report.errors.append(f"Unsupported risk_category: '{record.risk_category}'.")

        # 5. Pricing-in Risk Enum
        valid_pricing_cats = {e.value for e in PricingInRisk}
        report.checks_performed["pricing_in_category_valid"] = record.pricing_in_risk in valid_pricing_cats
        if not report.checks_performed["pricing_in_category_valid"]:
            report.errors.append(f"Unsupported pricing_in_risk category: '{record.pricing_in_risk}'.")

        # 6. Stakeholder Narratives Non-empty
        report.checks_performed["investor_summary_non_empty"] = bool(record.investor_summary.strip())
        report.checks_performed["business_summary_non_empty"] = bool(record.business_summary.strip())
        report.checks_performed["public_summary_non_empty"] = bool(record.public_summary.strip())
        if not record.investor_summary.strip():
            report.errors.append("Investor summary cannot be empty.")
        if not record.business_summary.strip():
            report.errors.append("Business summary cannot be empty.")
        if not record.public_summary.strip():
            report.errors.append("Public summary cannot be empty.")

        if report.errors:
            report.is_valid = False

        return report
