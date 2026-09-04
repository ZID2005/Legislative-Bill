"""
models/training/__init__.py
============================
Training sub-package for the Legislative Intelligence ML engine (Task 6.1).

Public exports:
  * ``MLTrainer``     — Main training orchestrator
  * ``DatasetBuilder`` — Training/research dataset construction
"""

from models.training.dataset_builder import DatasetBuilder
from models.training.trainer import MLTrainer

__all__ = ["MLTrainer", "DatasetBuilder"]
