"""
services package
================
Service Layer (orchestration) for the Legislative Intelligence project.

Coordinates business workflows across ingestion, validation, models, and AI.
"""

from __future__ import annotations

from services.ingestion import IngestionService
from services.prediction import PredictionService
from services.explanation import ExplanationService, LLMProvider
from services.knowledge_service import KnowledgeService
from services.mapping_service import MappingService
from services.event_study_service import EventStudyService
from services.market_model_service import MarketModelService
from services.statistical_service import StatisticalSignificanceService
from services.label_service import LabelGenerationService

__all__ = [
    "IngestionService",
    "PredictionService",
    "ExplanationService",
    "LLMProvider",
    "KnowledgeService",
    "MappingService",
    "EventStudyService",
    "MarketModelService",
    "StatisticalSignificanceService",
    "LabelGenerationService",
]
