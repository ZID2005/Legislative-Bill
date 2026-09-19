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

from schemas.bill import Bill, BillStatus, BillHouse, BillJurisdiction
from schemas.company import (
    Company,
    MarketCapCategory,
    UniverseType,
    EntityType,
    OwnershipType,
)
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
from schemas.state_knowledge import (
    StateBillKnowledge,
    StateBillSummary,
)
from schemas.state_economic_profile import (
    EvidenceReference,
    FactualStakeholderSummary,
    StakeholderImpact,
    StateBillEconomicProfile,
)
from schemas.state_corporate_exposure import (
    CorporateExposureEvidence,
    StateCorporateExposure,
    StatePresenceRecord,
    CompanyExposureRecord,
)
from schemas.unified_bill_record import UnifiedBillRecord
from schemas.user import User
from schemas.watchlist import (
    Watchlist,
    WatchlistItem,
    WatchlistEntityType,
    validate_entity_reference,
)
from schemas.alert import (
    AlertRule,
    AlertEvent,
    Notification,
    AlertPreference,
    AlertType,
    AlertSeverity,
    NotificationChannel,
    NotificationStatus,
    NotificationType,
    NotificationSourceType,
    DigestFrequency,
    compute_dedup_key,
    compute_notification_dedup_key,
    build_deep_link,
)
from schemas.alert_group import (
    AlertGroup,
    AlertGroupType,
    AlertGroupStatus,
    compute_aggregation_key,
)
from schemas.alert_digest import (
    AlertDigest,
    DigestType,
)

__all__ = [
    # Bill
    "Bill",
    "BillStatus",
    "BillHouse",
    "BillJurisdiction",
    # Company
    "Company",
    "MarketCapCategory",
    "UniverseType",
    "EntityType",
    "OwnershipType",
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
    # State Knowledge (Task 8.4)
    "StateBillKnowledge",
    "StateBillSummary",
    # State Economic Intelligence (Task 8.6)
    "EvidenceReference",
    "FactualStakeholderSummary",
    "StakeholderImpact",
    "StateBillEconomicProfile",
    # State Corporate Exposure (Task 8.7)
    "CorporateExposureEvidence",
    "StateCorporateExposure",
    "StatePresenceRecord",
    "CompanyExposureRecord",
    # Unified Discovery (Task 8.9)
    "UnifiedBillRecord",
    # User (Task 8.13.2)
    "User",
    # Watchlist (Task 8.13.2)
    "Watchlist",
    "WatchlistItem",
    "WatchlistEntityType",
    "validate_entity_reference",
    # Alert (Task 8.13.2)
    "AlertRule",
    "AlertEvent",
    "Notification",
    "AlertPreference",
    "AlertType",
    "AlertSeverity",
    "NotificationChannel",
    "NotificationStatus",
    "NotificationType",
    "NotificationSourceType",
    "DigestFrequency",
    "compute_dedup_key",
    "compute_notification_dedup_key",
    "build_deep_link",
    # Alert Group & Digest (Task 8.13.5)
    "AlertGroup",
    "AlertGroupType",
    "AlertGroupStatus",
    "compute_aggregation_key",
    "AlertDigest",
    "DigestType",
]

