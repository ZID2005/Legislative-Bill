"""
services/label_service.py
==========================
Service layer orchestrating the Label Generation Engine (Task 4.4).

Responsibility
--------------
Coordinates the full label-generation pipeline:

1.  Load all ``StatisticalResult`` records from ``StatisticalRepository``.
2.  Optionally filter by bill ID and/or event window.
3.  Delegate to ``LabelGenerator`` for label computation (with
    configurable thresholds via ``LabelConfig``).
4.  Skip already-labelled records when ``force_refresh=False``
    (incremental execution).
5.  Persist valid ``LabelRecord`` objects to ``LabelRepository``.
6.  Collect ``LabelValidationReport`` objects for rejected records.
7.  Return a structured summary dictionary.

Usage
-----
::

    from services.label_service import LabelGenerationService

    service = LabelGenerationService()
    summary = service.run(year=2024)
    print(summary)
    # {'processed': 120, 'generated': 108, 'skipped': 8, 'rejected': 4,
    #  'rejections': [...]}
"""

from __future__ import annotations

from typing import Optional

from config.logging_config import get_logger
from labeling.label_generator import LabelConfig, LabelGenerator
from schemas.label_record import LabelRecord
from schemas.validation_report import LabelValidationReport
from storage.label_repository import LabelRepository
from storage.statistical_repository import StatisticalRepository

logger = get_logger(__name__)


class LabelGenerationService:
    """
    Orchestrates the end-to-end label generation pipeline.

    Parameters
    ----------
    stat_repo : StatisticalRepository, optional
        Source of statistical results.  Defaults to the module-level
        singleton from ``storage``.
    label_repo : LabelRepository, optional
        Destination for generated labels.  Defaults to the module-level
        singleton from ``storage``.
    label_config : LabelConfig, optional
        Custom label thresholds.  Defaults to settings-driven values.
    """

    def __init__(
        self,
        stat_repo: Optional[StatisticalRepository] = None,
        label_repo: Optional[LabelRepository] = None,
        label_config: Optional[LabelConfig] = None,
    ) -> None:
        from storage import label_repo as _label_repo, statistical_repo as _stat_repo

        self._stat_repo: StatisticalRepository = stat_repo or _stat_repo
        self._label_repo: LabelRepository = label_repo or _label_repo
        self._generator: LabelGenerator = LabelGenerator(config=label_config)
        logger.debug("LabelGenerationService initialised.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        year: Optional[int] = None,
        bill_id: Optional[str] = None,
        event_window: Optional[str] = None,
        force_refresh: bool = False,
    ) -> dict:
        """
        Execute the label generation pipeline.

        Parameters
        ----------
        year : int, optional
            Filter statistical results to bills from a specific year.
            Requires the bill_id format to contain the year (e.g. ``2024``).
        bill_id : str, optional
            Limit processing to a single bill ID.
        event_window : str, optional
            Limit processing to a specific event window (e.g. ``[-5,+5]``).
        force_refresh : bool
            If ``True``, regenerate and overwrite existing labels.
            If ``False`` (default), skip already-generated labels.

        Returns
        -------
        dict
            Summary with keys:
            ``processed``, ``generated``, ``skipped``, ``rejected``,
            ``rejections`` (list of ``LabelValidationReport``).
        """
        logger.info(
            "LabelGenerationService.run | year=%s bill_id=%s window=%s force=%s",
            year,
            bill_id,
            event_window,
            force_refresh,
        )

        # --- 1. Load statistical results ------------------------------------
        stat_results = self._load_stat_results(
            bill_id=bill_id,
            event_window=event_window,
            year=year,
        )
        logger.info("Loaded %d statistical results.", len(stat_results))

        # --- 2. Build incremental skip callable ----------------------------
        skip_fn = None if force_refresh else self._label_repo.exists

        # --- 3. Delegate to LabelGenerator ---------------------------------
        valid_labels, rejected_reports = self._generator.generate_many(
            stat_results=stat_results,
            skip_if_exists=skip_fn,
        )

        # --- 4. Persist valid labels ----------------------------------------
        self._label_repo.save_many(valid_labels)

        # --- 5. Compute summary --------------------------------------------
        n_processed = len(stat_results)
        n_generated = len(valid_labels)
        n_rejected = len(rejected_reports)
        # Skipped = processed - generated - rejected (records that existed)
        n_skipped = n_processed - n_generated - n_rejected

        summary = {
            "processed": n_processed,
            "generated": n_generated,
            "skipped": max(n_skipped, 0),
            "rejected": n_rejected,
            "rejections": rejected_reports,
        }

        logger.info(
            "Label generation complete | processed=%d generated=%d "
            "skipped=%d rejected=%d",
            n_processed,
            n_generated,
            max(n_skipped, 0),
            n_rejected,
        )

        if rejected_reports:
            for report in rejected_reports:
                logger.warning(
                    "Rejected label: bill=%s company=%s window=%s | %s",
                    report.bill_id,
                    report.company,
                    report.event_window,
                    report.rejection_reason,
                )

        return summary

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_stat_results(
        self,
        bill_id: Optional[str],
        event_window: Optional[str],
        year: Optional[int],
    ):
        """Load and filter statistical results based on CLI parameters."""
        if bill_id:
            results = self._stat_repo.get_by_bill(bill_id)
        else:
            results = self._stat_repo.get_all()

        # Window filter
        if event_window:
            results = [r for r in results if r.event_window == event_window]

        # Year filter — bill IDs conventionally contain the year as a 4-digit
        # substring (e.g. "finance-bill-2024") so we filter by string match.
        if year is not None:
            year_str = str(year)
            results = [r for r in results if year_str in r.bill_id]

        return results
