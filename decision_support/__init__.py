"""
decision_support package
========================
Task 7.2: Decision Support & Risk Scoring Engine.

Exports:
- DecisionSupportEngine: Master orchestrator for decision interpretation and composite risk scoring.
- RiskScorer: Deterministic mathematical scoring engine.
- StakeholderSynthesizer: Multi-stakeholder qualitative perspectives generator.
- DecisionSupportValidator: Data integrity and validation report builder.
"""

from decision_support.engine import (
    CURRENT_DECISION_VERSION,
    CURRENT_FEATURE_VERSION,
    CURRENT_MODEL_VERSION,
    DecisionSupportEngine,
)
from decision_support.risk_scorer import RiskScorer
from decision_support.stakeholder_synthesizer import (
    DISCLAIMER_TEXT,
    StakeholderSynthesizer,
)
from decision_support.validator import DecisionSupportValidator

__all__ = [
    "DecisionSupportEngine",
    "RiskScorer",
    "StakeholderSynthesizer",
    "DecisionSupportValidator",
    "CURRENT_MODEL_VERSION",
    "CURRENT_FEATURE_VERSION",
    "CURRENT_DECISION_VERSION",
    "DISCLAIMER_TEXT",
]
