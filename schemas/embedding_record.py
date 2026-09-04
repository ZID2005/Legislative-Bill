"""
schemas/embedding_record.py
============================
Data models for legislative bill embeddings and embedding validation reports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EmbeddingRecord:
    """
    Representation of generated text embeddings for a legislative bill.

    Attributes
    ----------
    bill_id : str
        Unique identifier of the bill.
    embedding_model : str
        Name or identifier of the transformer model (e.g., 'finbert').
    embedding_dimension : int
        Dimension of the embedding vector (e.g., 768).
    embedding_vector : list[float]
        Dense numeric vector representing the bill text.
    token_count : int
        Number of tokens processed.
    model_version : str
        Model version/checksum or HF model ID.
    generation_timestamp : str
        ISO-8601 UTC timestamp of embedding generation.
    """

    bill_id: str
    embedding_model: str
    embedding_dimension: int
    embedding_vector: list[float]
    token_count: int
    model_version: str
    generation_timestamp: str

    def to_dict(self) -> dict[str, Any]:
        """Serialise the record to a dictionary."""
        return {
            "bill_id": self.bill_id,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "embedding_vector": self.embedding_vector,
            "token_count": self.token_count,
            "model_version": self.model_version,
            "generation_timestamp": self.generation_timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmbeddingRecord:
        """Deserialise the record from a dictionary."""
        return cls(
            bill_id=data["bill_id"],
            embedding_model=data["embedding_model"],
            embedding_dimension=int(data["embedding_dimension"]),
            embedding_vector=list(data["embedding_vector"]),
            token_count=int(data["token_count"]),
            model_version=data["model_version"],
            generation_timestamp=data["generation_timestamp"],
        )

    def __repr__(self) -> str:
        return (
            f"<EmbeddingRecord bill_id={self.bill_id!r} "
            f"model={self.embedding_model!r} "
            f"dimension={self.embedding_dimension} "
            f"tokens={self.token_count}>"
        )


@dataclass
class EmbeddingValidationReport:
    """
    Validation report for bills that fail embedding generation.

    Attributes
    ----------
    bill_id : str
        Unique identifier of the bill.
    rejection_reason : str
        Reason why embedding validation failed (e.g. empty embeddings).
    timestamp : str
        ISO-8601 UTC timestamp of validation.
    severity : str
        Severity of the validation failure (always 'ERROR' as these are rejected).
    """

    bill_id: str
    rejection_reason: str
    timestamp: str
    severity: str = "ERROR"

    def to_dict(self) -> dict[str, Any]:
        """Serialise the report to a dictionary."""
        return {
            "bill_id": self.bill_id,
            "rejection_reason": self.rejection_reason,
            "timestamp": self.timestamp,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmbeddingValidationReport:
        """Deserialise the report from a dictionary."""
        return cls(
            bill_id=data["bill_id"],
            rejection_reason=data["rejection_reason"],
            timestamp=data["timestamp"],
            severity=data.get("severity", "ERROR"),
        )

    def __repr__(self) -> str:
        return (
            f"<EmbeddingValidationReport bill_id={self.bill_id!r} "
            f"reason={self.rejection_reason!r} "
            f"severity={self.severity!r}>"
        )
