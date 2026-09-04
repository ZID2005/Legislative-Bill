"""
features package
================
Unified Feature Engineering Engine — Task 5.1

Responsibility
--------------
Combine every upstream repository (bill, knowledge, company, mapping,
market model, event study, statistical, label) into a single master
ML feature table and persist it in Parquet.

Public API
----------
``FeatureBuilder``         — high-level entry-point (thin wrapper)
``FeatureEngineeringEngine`` — core engine (merge, validate, persist)
``FeatureBuildResult``     — summary dataclass returned by build()
"""

from features.feature_engine import FeatureBuildResult, FeatureEngineeringEngine
from features.feature_builder import FeatureBuilder
from features.fusion_engine import FeatureFusionEngine
from features.selection_engine import FeatureSelectionEngine

__all__ = [
    "FeatureBuilder",
    "FeatureEngineeringEngine",
    "FeatureBuildResult",
    "FeatureFusionEngine",
    "FeatureSelectionEngine",
]

