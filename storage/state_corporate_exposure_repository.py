"""
storage/state_corporate_exposure_repository.py
==============================================
Repository for Indian State Legislative Bill Corporate Exposure records.

Manages persistence, retrieval, and multi-criteria discovery for
`StateCorporateExposure` records under `data/state_bills/corporate_exposure/`.

Maintains strict isolation from Central Government production data and
guarantees ZERO State stock-market predictions.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.state_corporate_exposure import StateCorporateExposure
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)


class StateCorporateExposureRepository:
    """
    Repository for storing, querying, and searching StateCorporateExposure records.
    """

    def __init__(self, exposure_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        if exposure_dir is None:
            self._exposure_dir = settings.STATE_BILLS_DIR / "corporate_exposure"
        else:
            self._exposure_dir = Path(exposure_dir)

        ensure_dir(self._exposure_dir)
        logger.debug("StateCorporateExposureRepository initialized | dir=%s", self._exposure_dir)

    @property
    def exposure_dir(self) -> Path:
        return self._exposure_dir

    # ------------------------------------------------------------------
    # Write Operations
    # ------------------------------------------------------------------

    def save(self, exposure: StateCorporateExposure) -> None:
        """
        Persist a single corporate exposure record into the bill's exposure store.
        """
        current_exposures = self.get_by_bill(exposure.bill_id)
        # Update if exists, else append
        updated = False
        new_list = []
        for exp in current_exposures:
            if exp.company_id == exposure.company_id:
                new_list.append(exposure)
                updated = True
            else:
                new_list.append(exp)
        if not updated:
            new_list.append(exposure)

        self.save_for_bill(exposure.bill_id, new_list)

    def save_for_bill(self, bill_id: str, exposures: list[StateCorporateExposure]) -> None:
        """
        Persist all corporate exposure records for a single State bill.
        """
        dest_path = self._exposure_dir / f"{bill_id}.json"
        data = [e.to_dict() for e in exposures]
        save_json(data, dest_path)
        logger.debug("Saved %d exposures for bill: %s", len(exposures), bill_id)

    def save_many(self, exposures: list[StateCorporateExposure]) -> None:
        """
        Persist a collection of corporate exposure records grouped by bill_id.
        """
        by_bill: dict[str, list[StateCorporateExposure]] = {}
        for exp in exposures:
            by_bill.setdefault(exp.bill_id, []).append(exp)
        for b_id, b_exps in by_bill.items():
            self.save_for_bill(b_id, b_exps)

    # ------------------------------------------------------------------
    # Read Operations
    # ------------------------------------------------------------------

    def get(self, bill_id: str, company_id: str) -> Optional[StateCorporateExposure]:
        """
        Retrieve a specific exposure record by bill_id and company_id.
        """
        exposures = self.get_by_bill(bill_id)
        for e in exposures:
            if e.company_id == company_id:
                return e
        return None

    def get_by_bill(self, bill_id: str) -> list[StateCorporateExposure]:
        """
        Retrieve all corporate exposure records for a specific State bill.
        """
        src_path = self._exposure_dir / f"{bill_id}.json"
        if not file_exists(src_path):
            return []
        try:
            data = load_json(src_path)
            if not isinstance(data, list):
                return []
            return [StateCorporateExposure.from_dict(item) for item in data]
        except Exception as exc:
            logger.error("Failed to load exposures for bill '%s': %s", bill_id, exc)
            return []

    def get_all(self) -> list[StateCorporateExposure]:
        """
        Return all corporate exposure records across all State bills.
        """
        results: list[StateCorporateExposure] = []
        try:
            files = list_files(self._exposure_dir, "*.json")
            for f in files:
                b_id = f.stem
                results.extend(self.get_by_bill(b_id))
        except Exception as exc:
            logger.error("Failed to list corporate exposure records: %s", exc)
        return results

    def get_by_company(self, company_id: str) -> list[StateCorporateExposure]:
        """
        Retrieve all exposures for a company across all bills (by ISIN or ticker).
        """
        target = company_id.strip().lower()
        return [
            e for e in self.get_all()
            if e.company_id.lower() == target or e.ticker.lower() == target
        ]

    def get_by_state(self, state: str) -> list[StateCorporateExposure]:
        """
        Retrieve all exposures related to a specific State.
        """
        target_norm = (normalize_state(state) or state).strip().lower()
        results = []
        for e in self.get_all():
            e_norm = (normalize_state(e.state) or e.state).strip().lower()
            if e_norm == target_norm:
                results.append(e)
        return results

    def get_by_sector(self, sector: str) -> list[StateCorporateExposure]:
        """
        Retrieve all exposures for a specific economic sector.
        """
        target = sector.strip().lower()
        return [e for e in self.get_all() if target in e.sector.lower()]

    def get_by_exposure_strength(self, strength: str) -> list[StateCorporateExposure]:
        """
        Filter exposures by strength (HIGH, MEDIUM, LOW, UNKNOWN).
        """
        target = strength.strip().upper()
        return [e for e in self.get_all() if e.exposure_strength.upper() == target]

    def get_by_directness(self, directness: str) -> list[StateCorporateExposure]:
        """
        Filter exposures by directness (DIRECT, INDIRECT, UNKNOWN).
        """
        target = directness.strip().upper()
        return [e for e in self.get_all() if e.direct_indirect.upper() == target]

    # ------------------------------------------------------------------
    # Search & Discovery (Phase 13)
    # ------------------------------------------------------------------

    def search(
        self,
        query: str = "",
        state: Optional[str] = None,
        company: Optional[str] = None,
        sector: Optional[str] = None,
        exposure_strength: Optional[str] = None,
        direct_indirect: Optional[str] = None,
        listed_status: Optional[str] = None,
        exposure_type: Optional[str] = None,
    ) -> list[StateCorporateExposure]:
        """
        Multi-attribute search across corporate exposure records.

        Supports combinations such as:
        - "companies exposed to Kerala agriculture bills"
        - "companies exposed to Telangana electricity bills"
        - "high-exposure companies in Karnataka"
        - "companies indirectly exposed to AP transport bills"
        """
        all_exps = self.get_all()
        results: list[StateCorporateExposure] = []

        q = query.strip().lower() if query else ""

        # Normalize state filter
        target_state = (normalize_state(state) or state).strip().lower() if state else None

        # Detect implicit state in natural query if not explicitly passed
        if not target_state and q:
            for s_name in ["andhra pradesh", "karnataka", "kerala", "telangana", "ap"]:
                if f"in {s_name}" in q or f"{s_name} " in q or q.endswith(s_name) or f"to {s_name}" in q:
                    target_state = (normalize_state(s_name) or s_name).strip().lower()
                    break

        # Detect implicit strength in natural query
        target_strength = exposure_strength.strip().upper() if exposure_strength else None
        if not target_strength and q:
            if "high" in q:
                target_strength = "HIGH"
            elif "medium" in q:
                target_strength = "MEDIUM"
            elif "low" in q:
                target_strength = "LOW"

        # Detect implicit directness in natural query
        target_directness = direct_indirect.strip().upper() if direct_indirect else None
        if not target_directness and q:
            if "indirect" in q:
                target_directness = "INDIRECT"
            elif "direct" in q:
                target_directness = "DIRECT"

        target_company = company.strip().lower() if company else None
        target_sector = sector.strip().lower() if sector else None
        target_listed = listed_status.strip().lower() if listed_status else None
        target_etype = exposure_type.strip().lower() if exposure_type else None

        # Stopwords for multi-word conceptual queries
        stopwords = {
            "bill", "bills", "companies", "company", "in", "to", "for", "exposed",
            "and", "the", "across", "state", "states", "with", "of", "high",
            "medium", "low", "exposure", "direct", "indirect",
        }
        query_terms = [t for t in re.findall(r"\w+", q) if t not in stopwords] if q else []

        for e in all_exps:
            # 1. State filter
            if target_state:
                e_state = (normalize_state(e.state) or e.state).strip().lower()
                if e_state != target_state:
                    continue

            # 2. Company filter
            if target_company:
                c_str = f"{e.company_name} {e.company_id} {e.ticker}".lower()
                if target_company not in c_str:
                    continue

            # 3. Sector filter
            if target_sector:
                if target_sector not in e.sector.lower() and target_sector not in e.sub_sector.lower():
                    continue

            # 4. Exposure strength filter
            if target_strength and e.exposure_strength.upper() != target_strength:
                continue

            # 5. Directness filter
            if target_directness and e.direct_indirect.upper() != target_directness:
                continue

            # 6. Listed status filter
            if target_listed and e.listed_status.lower() != target_listed:
                continue

            # 7. Exposure type filter
            if target_etype and e.exposure_type.lower() != target_etype:
                continue

            # 8. Free-text conceptual query matching
            if q:
                evidence_text = " ".join(ev.claim + " " + ev.reference for ev in e.evidence).lower()
                searchable = (
                    f"{e.company_name} {e.ticker} {e.company_id} {e.sector} {e.sub_sector} "
                    f"{e.business_activity} {' '.join(e.state_presence)} {e.presence_type} "
                    f"{e.exposure_type} {e.mechanism} {e.state} {e.bill_id} {evidence_text}"
                ).lower()

                # Direct substring match
                if q in searchable:
                    results.append(e)
                    continue

                # Multi-term conceptual match
                if query_terms and all(term in searchable for term in query_terms):
                    results.append(e)
                    continue

                continue

            results.append(e)

        return results

    # ------------------------------------------------------------------
    # Utility Operations
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return total count of individual corporate exposure records."""
        return len(self.get_all())

    def count_bills_with_exposures(self) -> int:
        """Return count of bills having at least one exposure record."""
        return len(list_files(self._exposure_dir, "*.json"))

    def delete_for_bill(self, bill_id: str) -> None:
        """Delete exposure record file for a bill."""
        p = self._exposure_dir / f"{bill_id}.json"
        if file_exists(p):
            os.remove(p)
            logger.info("Deleted exposures for bill: %s", bill_id)

    def __repr__(self) -> str:
        return (
            f"<StateCorporateExposureRepository dir={self._exposure_dir!r} "
            f"total_exposures={self.count()}>"
        )
