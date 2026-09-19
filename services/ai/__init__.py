"""
services/ai/__init__.py
=======================
Task 8.10 — Groq AI Intelligence & Explanation Layer.

Exposes:
- GroqClient, AIResponse
- AIContextBuilder, AIContext, AIComparisonContext
- AIGuardrails, ValidationResult, PERSONAS
- AIExplanationService, AIExplanationResult
"""

from services.ai.groq_client import AIResponse, GroqClient
from services.ai.ai_context_builder import (
    AIComparisonContext,
    AIContext,
    AIContextBuilder,
)
from services.ai.ai_guardrails import (
    AIGuardrails,
    PERSONAS,
    ValidationResult,
)
from services.ai.ai_explanation_service import (
    AIExplanationResult,
    AIExplanationService,
)

__all__ = [
    "AIResponse",
    "GroqClient",
    "AIContext",
    "AIComparisonContext",
    "AIContextBuilder",
    "AIGuardrails",
    "ValidationResult",
    "PERSONAS",
    "AIExplanationResult",
    "AIExplanationService",
]
