"""
labeling package
================
Ground-truth label generation layer — Task 4.4.

Responsibility
--------------
Converts event-study ``StatisticalResult`` records into supervised
machine-learning labels (``LabelRecord`` objects) that serve as the
authoritative training signal for the prediction models (Task 8).

Four label types are produced per (bill, company, event-window) triple:

1.  **DirectionLabel**   — POSITIVE / NEGATIVE / NEUTRAL
2.  **market_moving**    — binary True / False
3.  **ImpactStrength**   — LOW / MEDIUM / HIGH / VERY_HIGH
4.  **ConfidenceLabel**  — HIGH / MEDIUM / LOW

Public API
----------
``LabelGenerator``   — core label computation engine
``LabelConfig``      — configurable threshold container

Out of scope
------------
Feature engineering, embeddings, ML training, and backtesting are
intentionally excluded from this package.
"""

from labeling.label_generator import LabelConfig, LabelGenerator

__all__ = [
    "LabelGenerator",
    "LabelConfig",
]
