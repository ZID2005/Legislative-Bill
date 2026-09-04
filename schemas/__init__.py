"""
schemas package
===============
Typed data models for all core domain entities.

Motivation
----------
Without explicit schemas, data passes between modules as untyped dicts.
This causes:

*  Silent field renames breaking downstream code
*  Missing required fields only discovered at runtime
*  No IDE autocomplete or type-checker support
*  Inconsistent field naming across modules

This package defines the canonical schema for every entity in the system.
All code that reads or writes domain data must use these models.

Current Implementation
----------------------
Task 0: Python ``dataclasses`` with type hints.  Lightweight, zero
dependencies, compatible with the standard library.

Future Migration (Task 3)
--------------------------
Fields will be annotated with ``pydantic`` validators for:
*  Runtime type coercion (e.g. "2024-01-01" → datetime.date)
*  Value-range validation (e.g. year > 1947)
*  Custom error messages

Schemas
-------
bill        : Central Government legislative bill
company     : BSE/NSE listed company
market      : Market price record (OHLCV)
prediction  : Model prediction output for a (bill, company) pair
"""

from schemas.bill import Bill, BillStatus, BillHouse
from schemas.company import Company, MarketCapCategory
from schemas.prediction import (
    Prediction,
    ImpactLabel,
    PredictionRecord,
    PredictionValidationReport,
    DirectionPrediction,
    ImpactStrengthPrediction,
    ConfidencePrediction,
    make_prediction_id,
)
from schemas.knowledge_record import KnowledgeRecord
from schemas.mapping_record import BillCompanyMapping
from schemas.market_model import MarketModelRecord
from schemas.event_study import EventStudyRecord
from schemas.statistical_result import StatisticalResult
from schemas.label_record import LabelRecord, DirectionLabel, ImpactStrength, ConfidenceLabel
from schemas.validation_report import LabelValidationReport
from schemas.feature_record import FeatureRecord, make_record_id
from schemas.feature_validation_report import FeatureValidationReport
from schemas.fusion_validation_report import FusionValidationReport
from schemas.feature_selection_validation_report import FeatureSelectionValidationReport
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
from schemas.decision import (
    DecisionSupportRecord,
    DecisionValidationReport,
    PricingInRisk,
    RiskCategory,
    StakeholderPerspective,
    make_decision_id,
)

__all__ = [
    # Bill
    "Bill",
    "BillStatus",
    "BillHouse",
    # Company
    "Company",
    "MarketCapCategory",
    # Market
    "PriceRecord",
    # Prediction
    "Prediction",
    "ImpactLabel",
    "PredictionRecord",
    "PredictionValidationReport",
    "DirectionPrediction",
    "ImpactStrengthPrediction",
    "ConfidencePrediction",
    "make_prediction_id",
    # Knowledge Record
    "KnowledgeRecord",
    # Mapping Record
    "BillCompanyMapping",
    # Market Model Record
    "MarketModelRecord",
    # Event Study Record
    "EventStudyRecord",
    # Statistical Result
    "StatisticalResult",
    # Label Records
    "LabelRecord",
    "DirectionLabel",
    "ImpactStrength",
    "ConfidenceLabel",
    # Validation Report
    "LabelValidationReport",
    # Feature Engineering (Task 5.1)
    "FeatureRecord",
    "make_record_id",
    "FeatureValidationReport",
    "FusionValidationReport",
    "FeatureSelectionValidationReport",
    # Anticipation Bias (Task 6.5)
    "PreEventWindowStats",
    "InformationEvidence",
    "EvidenceType",
    "EvidenceConfidence",
    "AnticipationClassification",
    "AnticipationScore",
    "BillAnticipationRecord",
    "AnticipationValidationReport",
    # Decision Support (Task 7.2)
    "DecisionSupportRecord",
    "DecisionValidationReport",
    "RiskCategory",
    "PricingInRisk",
    "StakeholderPerspective",
    "make_decision_id",
]

