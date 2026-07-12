"""
validation package
==================
Data quality and schema validation layer.

Responsibility
--------------
Ensure that all data entering the processing pipeline conforms to expected
schemas, value ranges, and business rules before it is persisted or consumed
by downstream modules.
"""

from validation.validator import Validator, ValidationReport
from validation.event_study_validator import EventStudyValidator
from validation.market_model_validator import MarketModelValidator
from validation.statistical_validator import StatisticalValidator

__all__ = [
    "Validator",
    "ValidationReport",
    "EventStudyValidator",
    "MarketModelValidator",
    "StatisticalValidator",
]
