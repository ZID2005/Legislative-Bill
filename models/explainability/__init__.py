"""
models/explainability/__init__.py
==================================
Explainability sub-package — Task 6.3.

Provides SHAP-based global and local explanations for every trained model.

Public symbols
--------------
ExplainabilityEngine
    Orchestrates SHAP computation, visualization, and persistence.
ExplainabilityVisualizer
    Wraps matplotlib / SHAP plotting for all chart types.
"""

# Lazy imports — visualizer has optional dependencies (matplotlib, shap)
# that may not be installed in all environments.


def __getattr__(name: str):  # type: ignore[misc]
    if name == "ExplainabilityEngine":
        from models.explainability.engine import ExplainabilityEngine
        return ExplainabilityEngine
    if name == "ExplainabilityVisualizer":
        from models.explainability.visualizer import ExplainabilityVisualizer
        return ExplainabilityVisualizer
    raise AttributeError(f"module 'models.explainability' has no attribute {name!r}")


__all__ = [
    "ExplainabilityEngine",
    "ExplainabilityVisualizer",
]
