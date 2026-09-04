"""
models/evaluation package
==========================
Model evaluation and backtesting (Task 6.2).

Exports:
- `ModelEvaluator` — core evaluation orchestration and error analysis
- `compute_metrics` — unified classification metrics calculator
"""

from models.evaluation.evaluator import ModelEvaluator
from models.evaluation.metrics import compute_metrics

__all__ = ["ModelEvaluator", "compute_metrics"]
