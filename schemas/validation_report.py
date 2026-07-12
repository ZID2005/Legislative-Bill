"""
schemas/validation_report.py
=============================
Data schema for label validation failure reports produced by the
Label Generation Engine (Task 4.4).

When the ``LabelGenerator`` cannot produce a valid label — because the
source ``StatisticalResult`` is missing, the CAR is NaN, or the
p-value is undefined — it emits a ``LabelValidationReport`` instead of
a ``LabelRecord``.

These reports are returned to the caller and can be logged, stored, or
surfaced in a data-quality dashboard.  They do NOT block the pipeline;
valid (bill, company, window) triples continue to be processed.

Design note
-----------
The validation report intentionally has a minimal schema.  Downstream
quality pipelines can join it back to bill / company metadata as needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LabelValidationReport:
    """
    Audit record for a rejected label.

    Attributes
    ----------
    bill_id : str
        Bill slug of the failing record.
    company : str
        Company ISIN of the failing record.
    event_window : str
        Event window that failed validation.
    rejection_reason : str
        Human-readable explanation of why label generation was rejected.
    timestamp : str
        ISO-8601 UTC timestamp of the rejection.
    """

    bill_id: str
    company: str
    event_window: str
    rejection_reason: str
    timestamp: str

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialise the report to a JSON-compatible dictionary."""
        return {
            "bill_id": self.bill_id,
            "company": self.company,
            "event_window": self.event_window,
            "rejection_reason": self.rejection_reason,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LabelValidationReport":
        """Deserialise the report from a dictionary."""
        return cls(
            bill_id=data["bill_id"],
            company=data["company"],
            event_window=data["event_window"],
            rejection_reason=data["rejection_reason"],
            timestamp=data["timestamp"],
        )

    def __repr__(self) -> str:
        return (
            f"<LabelValidationReport bill={self.bill_id!r} "
            f"company={self.company!r} "
            f"window={self.event_window!r} "
            f"reason={self.rejection_reason!r}>"
        )
