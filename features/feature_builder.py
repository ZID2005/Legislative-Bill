"""
features/feature_builder.py
============================
Thin convenience wrapper that exposes a single entry-point for the
Unified Feature Engineering Engine (Task 5.1).

Rationale
---------
``FeatureBuilder`` is the class originally declared as a placeholder in the
project scaffold.  It now delegates all heavy lifting to
``FeatureEngineeringEngine`` so external callers get a stable API even if
the internal engine is refactored later.

Usage
-----
::

    from features.feature_builder import FeatureBuilder

    builder = FeatureBuilder()
    result = builder.build()                   # incremental (default)
    result = builder.build(incremental=False)  # full rebuild

    path   = builder.export_csv()
    info   = builder.dataset_info()
"""

from __future__ import annotations

from features.feature_engine import FeatureBuildResult, FeatureEngineeringEngine
from pathlib import Path
from typing import Optional


class FeatureBuilder:
    """
    High-level entry-point for the Unified Feature Engineering Engine.

    Wraps :class:`~features.feature_engine.FeatureEngineeringEngine` and
    exposes a stable public API for pipeline orchestration.

    Parameters
    ----------
    engine : FeatureEngineeringEngine, optional
        Pre-configured engine instance.  If ``None``, a default instance
        is created using the module-level repository singletons.
    """

    def __init__(self, engine: Optional[FeatureEngineeringEngine] = None) -> None:
        self._engine = engine or FeatureEngineeringEngine()

    def build(self, incremental: bool = True) -> FeatureBuildResult:
        """
        Build (or incrementally update) the unified feature dataset.

        Parameters
        ----------
        incremental : bool
            When ``True`` (default), existing records are skipped.

        Returns
        -------
        FeatureBuildResult
            Summary counts and any validation reports.
        """
        return self._engine.build(incremental=incremental)

    def rebuild(self) -> FeatureBuildResult:
        """Force a full rebuild from scratch, ignoring existing records."""
        return self._engine.rebuild()

    def export_csv(self) -> Path:
        """
        Export the current feature dataset to CSV.

        Returns
        -------
        Path
            Absolute path of the written CSV file.
        """
        return self._engine.export_csv()

    def dataset_info(self) -> dict:
        """Return metadata about the persisted feature dataset."""
        return self._engine.dataset_info()

    def __repr__(self) -> str:
        info = self._engine.dataset_info()
        return (
            f"<FeatureBuilder records={info.get('record_count', 0)} "
            f"parquet={info.get('parquet_exists', False)}>"
        )
