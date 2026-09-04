"""
storage/anticipation_repository.py
==================================
Repository for persisting and retrieving Anticipation Bias Analysis records.

Manages data within ``data/anticipation/``:
- ``scores/``: Company-bill pair AnticipationScore records.
- ``bill_scores/``: Aggregated BillAnticipationRecord objects.
- ``market_stats/``: Multi-window PreEventWindowStats dictionary mappings.
- ``evidence/``: Raw and validated InformationEvidence items.
- ``reports/``: AnticipationValidationReport audit records.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.anticipation import (
    AnticipationScore,
    AnticipationValidationReport,
    BillAnticipationRecord,
    InformationEvidence,
    PreEventWindowStats,
)
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json

logger = get_logger(__name__)


def sanitize_id(identifier: str) -> str:
    """Sanitize identifier string to make it safe for OS filesystems."""
    return identifier.replace("/", "_").replace("\\", "_").replace(":", "_").replace(" ", "_")


class AnticipationRepository:
    """
    Dedicated repository for storing and querying anticipation bias records.
    """

    def __init__(self, anticipation_dir: Optional[Path] = None) -> None:
        self._anticipation_dir = anticipation_dir or settings.ANTICIPATION_DIR
        self._scores_dir = self._anticipation_dir / "scores"
        self._bill_scores_dir = self._anticipation_dir / "bill_scores"
        self._market_stats_dir = self._anticipation_dir / "market_stats"
        self._evidence_dir = self._anticipation_dir / "evidence"
        self._reports_dir = self._anticipation_dir / "reports"

        for directory in [
            self._anticipation_dir,
            self._scores_dir,
            self._bill_scores_dir,
            self._market_stats_dir,
            self._evidence_dir,
            self._reports_dir,
        ]:
            ensure_dir(directory)

        logger.debug("AnticipationRepository initialised | root=%s", self._anticipation_dir)

    # ------------------------------------------------------------------
    # Path Helpers
    # ------------------------------------------------------------------

    def _score_path(self, bill_id: str, company_isin: str) -> Path:
        sanitized_bill = sanitize_id(bill_id)
        sanitized_isin = sanitize_id(company_isin)
        return self._scores_dir / f"{sanitized_bill}_{sanitized_isin}.json"

    def _bill_score_path(self, bill_id: str) -> Path:
        sanitized_bill = sanitize_id(bill_id)
        return self._bill_scores_dir / f"{sanitized_bill}.json"

    def _market_stats_path(self, bill_id: str, company_isin: str) -> Path:
        sanitized_bill = sanitize_id(bill_id)
        sanitized_isin = sanitize_id(company_isin)
        return self._market_stats_dir / f"{sanitized_bill}_{sanitized_isin}_stats.json"

    def _evidence_path(self, bill_id: str) -> Path:
        sanitized_bill = sanitize_id(bill_id)
        return self._evidence_dir / f"{sanitized_bill}_evidence.json"

    def _report_path(self, report_id: str) -> Path:
        sanitized_rep = sanitize_id(report_id)
        return self._reports_dir / f"{sanitized_rep}.json"

    # ------------------------------------------------------------------
    # Company-Bill Anticipation Scores
    # ------------------------------------------------------------------

    def save_score(self, score: AnticipationScore) -> None:
        """Persist an AnticipationScore record."""
        dest = self._score_path(score.bill_id, score.company_isin)
        save_json(score.to_dict(), dest)
        logger.debug("Saved anticipation score: bill=%s isin=%s", score.bill_id, score.company_isin)

    def save_scores(self, scores: list[AnticipationScore]) -> None:
        """Persist multiple AnticipationScore records."""
        for s in scores:
            self.save_score(s)

    def get_score(self, bill_id: str, company_isin: str) -> Optional[AnticipationScore]:
        """Retrieve an AnticipationScore record."""
        src = self._score_path(bill_id, company_isin)
        if not file_exists(src):
            return None
        try:
            data = load_json(src)
            return AnticipationScore.from_dict(data)
        except Exception as exc:
            logger.error("Failed to load score for bill %s, company %s: %s", bill_id, company_isin, exc)
            return None

    def score_exists(self, bill_id: str, company_isin: str) -> bool:
        """Check if an AnticipationScore record exists."""
        return file_exists(self._score_path(bill_id, company_isin))

    def get_all_scores(self) -> list[AnticipationScore]:
        """Retrieve all stored company-bill anticipation score records."""
        scores = []
        try:
            files = list_files(self._scores_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    scores.append(AnticipationScore.from_dict(data))
                except Exception as exc:
                    logger.error("Failed loading anticipation score file %s: %s", f.name, exc)
        except Exception as exc:
            logger.error("Failed listing anticipation scores: %s", exc)
        return scores

    def get_scores_by_bill(self, bill_id: str) -> list[AnticipationScore]:
        """Retrieve all anticipation scores for a specific bill."""
        sanitized_bill = sanitize_id(bill_id)
        scores = []
        try:
            files = list_files(self._scores_dir, f"{sanitized_bill}_*.json")
            for f in files:
                try:
                    data = load_json(f)
                    scores.append(AnticipationScore.from_dict(data))
                except Exception as exc:
                    logger.error("Failed loading anticipation score file %s: %s", f.name, exc)
        except Exception as exc:
            logger.error("Failed filtering anticipation scores by bill %s: %s", bill_id, exc)
        return scores

    def get_scores_by_company(self, company_isin: str) -> list[AnticipationScore]:
        """Retrieve all anticipation scores for a specific company ISIN."""
        sanitized_isin = sanitize_id(company_isin)
        scores = []
        try:
            files = list_files(self._scores_dir, f"*_{sanitized_isin}.json")
            for f in files:
                try:
                    data = load_json(f)
                    scores.append(AnticipationScore.from_dict(data))
                except Exception as exc:
                    logger.error("Failed loading score file %s: %s", f.name, exc)
        except Exception as exc:
            logger.error("Failed filtering scores by company %s: %s", company_isin, exc)
        return scores

    # ------------------------------------------------------------------
    # Bill-Level Aggregated Scores
    # ------------------------------------------------------------------

    def save_bill_score(self, bill_score: BillAnticipationRecord) -> None:
        """Persist a BillAnticipationRecord."""
        dest = self._bill_score_path(bill_score.bill_id)
        save_json(bill_score.to_dict(), dest)
        logger.debug("Saved bill anticipation record: bill=%s", bill_score.bill_id)

    def get_bill_score(self, bill_id: str) -> Optional[BillAnticipationRecord]:
        """Retrieve a BillAnticipationRecord."""
        src = self._bill_score_path(bill_id)
        if not file_exists(src):
            return None
        try:
            data = load_json(src)
            return BillAnticipationRecord.from_dict(data)
        except Exception as exc:
            logger.error("Failed to load bill anticipation record for %s: %s", bill_id, exc)
            return None

    def bill_score_exists(self, bill_id: str) -> bool:
        """Check if a bill-level anticipation record exists."""
        return file_exists(self._bill_score_path(bill_id))

    def get_all_bill_scores(self) -> list[BillAnticipationRecord]:
        """Retrieve all bill-level anticipation records."""
        records = []
        try:
            files = list_files(self._bill_scores_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    records.append(BillAnticipationRecord.from_dict(data))
                except Exception as exc:
                    logger.error("Failed loading bill anticipation file %s: %s", f.name, exc)
        except Exception as exc:
            logger.error("Failed listing bill anticipation records: %s", exc)
        return records

    # ------------------------------------------------------------------
    # Pre-Event Market Statistics
    # ------------------------------------------------------------------

    def save_market_stats(
        self,
        stats_dict: dict[str, PreEventWindowStats],
        bill_id: str,
        company_isin: str,
    ) -> None:
        """Persist pre-event window statistics mapping for a bill-company pair."""
        dest = self._market_stats_path(bill_id, company_isin)
        payload = {
            "bill_id": bill_id,
            "company_isin": company_isin,
            "windows": {k: v.to_dict() for k, v in stats_dict.items()},
        }
        save_json(payload, dest)
        logger.debug("Saved market stats for bill=%s isin=%s", bill_id, company_isin)

    def get_market_stats(
        self, bill_id: str, company_isin: str
    ) -> Optional[dict[str, PreEventWindowStats]]:
        """Retrieve pre-event window statistics mapping for a bill-company pair."""
        src = self._market_stats_path(bill_id, company_isin)
        if not file_exists(src):
            return None
        try:
            data = load_json(src)
            raw_windows = data.get("windows", {})
            return {
                k: PreEventWindowStats.from_dict(v) for k, v in raw_windows.items()
            }
        except Exception as exc:
            logger.error("Failed loading market stats for %s / %s: %s", bill_id, company_isin, exc)
            return None

    def get_all_market_stats(self) -> dict[str, dict[str, PreEventWindowStats]]:
        """Retrieve all stored market statistics indexed by '{bill_id}_{company_isin}'."""
        all_stats: dict[str, dict[str, PreEventWindowStats]] = {}
        try:
            files = list_files(self._market_stats_dir, "*_stats.json")
            for f in files:
                try:
                    data = load_json(f)
                    b_id = data.get("bill_id")
                    c_isin = data.get("company_isin")
                    if b_id and c_isin:
                        key = f"{b_id}_{c_isin}"
                        raw_windows = data.get("windows", {})
                        all_stats[key] = {
                            k: PreEventWindowStats.from_dict(v) for k, v in raw_windows.items()
                        }
                except Exception as exc:
                    logger.error("Failed loading market stats file %s: %s", f.name, exc)
        except Exception as exc:
            logger.error("Failed listing market stats: %s", exc)
        return all_stats

    # ------------------------------------------------------------------
    # Information Evidence
    # ------------------------------------------------------------------

    def save_evidence(self, evidence_list: list[InformationEvidence], bill_id: str) -> None:
        """Persist external evidence items for a bill."""
        dest = self._evidence_path(bill_id)
        payload = {
            "bill_id": bill_id,
            "evidence_count": len(evidence_list),
            "evidence": [ev.to_dict() for ev in evidence_list],
        }
        save_json(payload, dest)
        logger.debug("Saved %d evidence items for bill=%s", len(evidence_list), bill_id)

    def get_evidence_by_bill(self, bill_id: str) -> list[InformationEvidence]:
        """Retrieve external evidence items for a bill."""
        src = self._evidence_path(bill_id)
        if not file_exists(src):
            return []
        try:
            data = load_json(src)
            raw_ev = data.get("evidence", [])
            return [InformationEvidence.from_dict(item) for item in raw_ev]
        except Exception as exc:
            logger.error("Failed loading evidence for bill %s: %s", bill_id, exc)
            return []

    def get_all_evidence(self) -> list[InformationEvidence]:
        """Retrieve all external evidence across all bills."""
        all_ev = []
        try:
            files = list_files(self._evidence_dir, "*_evidence.json")
            for f in files:
                try:
                    data = load_json(f)
                    for item in data.get("evidence", []):
                        all_ev.append(InformationEvidence.from_dict(item))
                except Exception as exc:
                    logger.error("Failed loading evidence file %s: %s", f.name, exc)
        except Exception as exc:
            logger.error("Failed listing evidence: %s", exc)
        return all_ev

    # ------------------------------------------------------------------
    # Validation Reports
    # ------------------------------------------------------------------

    def save_validation_report(
        self,
        report: AnticipationValidationReport,
        report_id: Optional[str] = None,
    ) -> str:
        """Persist an AnticipationValidationReport."""
        rep_id = report_id or f"{report.bill_id}_{report.company_isin or 'summary'}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        dest = self._report_path(rep_id)
        save_json(report.to_dict(), dest)
        logger.debug("Saved validation report: id=%s", rep_id)
        return rep_id

    def get_validation_report(self, report_id: str) -> Optional[AnticipationValidationReport]:
        """Retrieve a validation report by ID."""
        src = self._report_path(report_id)
        if not file_exists(src):
            return None
        try:
            data = load_json(src)
            return AnticipationValidationReport.from_dict(data)
        except Exception as exc:
            logger.error("Failed loading validation report %s: %s", report_id, exc)
            return None

    def get_all_validation_reports(self) -> list[AnticipationValidationReport]:
        """Retrieve all stored validation reports."""
        reports = []
        try:
            files = list_files(self._reports_dir, "*.json")
            for f in files:
                try:
                    data = load_json(f)
                    reports.append(AnticipationValidationReport.from_dict(data))
                except Exception as exc:
                    logger.error("Failed loading validation report %s: %s", f.name, exc)
        except Exception as exc:
            logger.error("Failed listing validation reports: %s", exc)
        return reports
