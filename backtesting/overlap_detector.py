"""
backtesting/overlap_detector.py
================================
OverlapDetector — detects simultaneous and overlapping event windows in the
backtest record set (Task 6.4.1).

Purpose
-------
In an event-study backtesting context, multiple (bill, company, window) triples
can be active at the same calendar date. These CANNOT be treated as independent
sequential trades. The OverlapDetector:

1. Finds all dates that have more than one observation record.
2. Reports pairs of records whose event windows overlap temporally.
3. Summarises overlap statistics for inclusion in the audit report.
4. The backtesting engine uses this information to aggregate returns by date
   (equal-weighted portfolio per date) instead of summing them sequentially.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from config.logging_config import get_logger
from schemas.backtest_record import BacktestRecord, OverlapReport

logger = get_logger(__name__)


def _parse_window(window_str: str) -> tuple[int, int]:
    """Parse ``"[-5,+5]"`` → ``(-5, +5)``."""
    m = re.match(r"\[(-?\d+),\s*\+?(-?\d+)\]", str(window_str).strip())
    if m:
        return int(m.group(1)), int(m.group(2))
    return 0, 20


class OverlapDetector:
    """
    Detects event-window overlaps across all backtest records.

    Parameters
    ----------
    records : list[BacktestRecord]
        All records from the backtest run.
    """

    def detect(self, records: list[BacktestRecord]) -> OverlapReport:
        """
        Analyse all records and return an OverlapReport.

        Returns
        -------
        OverlapReport
        """
        if not records:
            return OverlapReport(
                total_events=0,
                total_unique_dates=0,
                overlapping_event_pairs=0,
                overlap_percentage=0.0,
                max_simultaneous_events=0,
                dates_with_multiple_events=0,
                company_level_overlaps=0,
                bill_level_overlaps=0,
                event_windows_checked=[],
            )

        # Group records by prediction_timestamp (event date)
        date_groups: dict[str, list[BacktestRecord]] = defaultdict(list)
        for rec in records:
            date_groups[rec.prediction_timestamp].append(rec)

        unique_dates = sorted(date_groups.keys())
        dates_with_multiple = sum(1 for v in date_groups.values() if len(v) > 1)
        max_simultaneous = max(len(v) for v in date_groups.values())

        # Per-company overlaps: same company, overlapping calendar windows
        company_groups: dict[str, list[BacktestRecord]] = defaultdict(list)
        bill_groups: dict[str, list[BacktestRecord]] = defaultdict(list)
        for rec in records:
            company_groups[rec.company_isin].append(rec)
            bill_groups[rec.bill_id].append(rec)

        company_overlaps = self._count_overlapping_pairs(company_groups)
        bill_overlaps = self._count_overlapping_pairs(bill_groups)

        # Total overlapping pairs (same date → overlapping)
        total_overlapping = sum(
            len(v) * (len(v) - 1) // 2  # C(n,2)
            for v in date_groups.values()
            if len(v) > 1
        )

        overlap_pct = (total_overlapping / max(1, len(records))) * 100.0

        # Collect detail sample (first 50 multi-event dates)
        overlap_details: list[dict[str, Any]] = []
        for dt in unique_dates[:50]:
            grp = date_groups[dt]
            if len(grp) > 1:
                overlap_details.append({
                    "date": dt,
                    "n_simultaneous_events": len(grp),
                    "bills": list({r.bill_id for r in grp}),
                    "companies": list({r.company_isin for r in grp}),
                    "windows": list({r.event_window for r in grp}),
                })

        windows_checked = sorted({r.event_window for r in records})

        logger.info(
            "OverlapDetector: %d events | %d unique dates | %d dates with multiple events "
            "| max simultaneous=%d | overlap pairs=%d",
            len(records), len(unique_dates), dates_with_multiple,
            max_simultaneous, total_overlapping,
        )

        return OverlapReport(
            total_events=len(records),
            total_unique_dates=len(unique_dates),
            overlapping_event_pairs=total_overlapping,
            overlap_percentage=round(overlap_pct, 2),
            max_simultaneous_events=max_simultaneous,
            dates_with_multiple_events=dates_with_multiple,
            company_level_overlaps=company_overlaps,
            bill_level_overlaps=bill_overlaps,
            event_windows_checked=windows_checked,
            overlap_details=overlap_details,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def _count_overlapping_pairs(
        self, groups: dict[str, list[BacktestRecord]]
    ) -> int:
        """Count record pairs within the same entity (company or bill) that have
        overlapping calendar date ranges."""
        count = 0
        for _entity, recs in groups.items():
            if len(recs) < 2:
                continue
            # Build list of (start_dt, end_dt) for each record
            intervals: list[tuple[pd.Timestamp, pd.Timestamp]] = []
            for r in recs:
                try:
                    base = pd.to_datetime(r.prediction_timestamp)
                    pre, post = _parse_window(r.event_window)
                    start = base + pd.Timedelta(days=pre)
                    end = base + pd.Timedelta(days=post)
                    intervals.append((start, end))
                except Exception:
                    pass

            for i in range(len(intervals)):
                for j in range(i + 1, len(intervals)):
                    s1, e1 = intervals[i]
                    s2, e2 = intervals[j]
                    # Overlap: start of one is before end of other
                    if s1 <= e2 and s2 <= e1:
                        count += 1
        return count
