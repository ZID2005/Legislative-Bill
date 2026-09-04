"""
prediction package
==================
Final Prediction & Decision Engine for Task 7.1.

Components
----------
- ``FinalPredictionEngine`` : Master inference and prediction orchestrator.
- ``ModelSelector``          : Automated multi-metric model selection backed by Task 6.2 evaluation.
- ``PredictionValidator``    : Pre-inference data integrity, feature dimensions, and compatibility validator.
- ``DecisionEngine``         : Qualitative synthesis separating model probabilities from decision support.
"""

from prediction.decision_engine import DecisionEngine
from prediction.engine import (
    CURRENT_FEATURE_VERSION,
    CURRENT_MODEL_VERSION,
    FinalPredictionEngine,
)
from prediction.model_selector import DEFAULT_BEST_MODELS, ModelSelector
from prediction.validator import PredictionValidator

__all__ = [
    "FinalPredictionEngine",
    "ModelSelector",
    "PredictionValidator",
    "DecisionEngine",
    "CURRENT_MODEL_VERSION",
    "CURRENT_FEATURE_VERSION",
    "DEFAULT_BEST_MODELS",
]
