"""
storage/exceptions.py
=====================
Custom exceptions for storage and dataset immutability safeguards.
"""

from __future__ import annotations


class StorageError(Exception):
    """Base exception for storage layer operations."""


class FrozenDatasetImmutableError(StorageError):
    """
    Raised when an operation attempts to write, modify, or delete records
    in a frozen production dataset (Central predictions, decisions,
    anticipation scores, or stakeholder reports).
    """

    def __init__(
        self,
        dataset_name: str,
        message: str = "Dataset is frozen and immutable in production.",
    ) -> None:
        self.dataset_name = dataset_name
        super().__init__(f"[{dataset_name}] {message}")
