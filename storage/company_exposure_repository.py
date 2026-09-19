"""
storage/company_exposure_repository.py
======================================
Unified Repository for Evidence-Based Company Exposure Intelligence across
Central Government and Indian State legislative bills.

Manages persistence, retrieval, and multi-criteria discovery for
`StateCorporateExposure` / `CompanyExposureRecord` entities.

Provides comprehensive query support answering:
    A. Which bills affect this company?
    B. Which companies are exposed to this bill?
    C. Why is this company exposed?
    D. What evidence supports the exposure?
    E. What sector/business activity creates the exposure?
    F. Which State is relevant?
    G. Is the exposure direct or indirect?
    H. What economic mechanism is involved?

Guarantees:
- Strict quantitative firewall isolation: zero market prediction integration.
- Complete preservation of validated State corporate exposure records.
- Zero state stock-market predictions.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.state_corporate_exposure import (
    CorporateExposureEvidence,
    StateCorporateExposure,
    CompanyExposureRecord,
)
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)


# Canonical alias & acronym mapping to support natural name/ticker/brand queries
_COMPANY_ALIAS_MAP: dict[str, list[str]] = {
    "INE758T01015": ["zomato", "zomato limited", "eternal limited"],
    "PRIV-BUNDL-SWIGGY": ["swiggy", "bundl", "bundl technologies", "bundl technologies private limited", "swiggy limited", "ine00h001014"],
    "PRIV-FLIPKART-IND": ["flipkart", "flipkart private limited", "flipkart india"],
    "PRIV-AMAZON-IND": ["amazon", "amazon india", "amazon seller services", "amazon seller services private limited"],
    "INE201M01025": ["delhivery", "delhivery limited"],
    "INE233B01017": ["blue dart", "blue dart express", "blue dart express limited"],
    "INE742F01042": ["adani ports", "apsez", "adani ports and special economic zone limited", "adani ports & sez"],
    "INE399C01030": ["concor", "container corporation", "container corporation of india", "container corporation of india limited"],
    "SOE-BSNL-UNLISTED": ["bsnl", "bharat sanchar nigam", "bharat sanchar nigam limited"],
    "INE669E01016": ["vodafone idea", "vodafone idea limited", "vi", "idea"],
    "INE061F01013": ["fortis", "fortis healthcare", "fortis healthcare limited"],
    "INE027H01010": ["max healthcare", "max healthcare institute", "max healthcare institute limited"],
    "UNLISTED-AP-GENCO": ["apgenco", "ap genco", "andhra pradesh power generation corporation limited"],
    "UNLISTED-KL-KSEB": ["kseb", "kerala state electricity board", "kerala state electricity board limited"],
    "UNLISTED-TS-GENCO": ["tsgenco", "ts genco", "telangana state power generation corporation limited"],
    "INE202E01016": ["ireda", "indian renewable energy development agency", "indian renewable energy development agency limited"],
    "UNLISTED-KL-RTC": ["ksrtc-kl", "kerala rtc", "kerala state road transport corporation", "kl-rtc"],
    "UNLISTED-KA-RTC": ["ksrtc-ka", "karnataka rtc", "karnataka state road transport corporation", "ka-rtc"],
    "INE043D01016": ["gmr", "gmr airports", "gmr airports infrastructure limited", "gmr infrastructure"],
    "INE053F01010": ["irfc", "indian railway finance", "indian railway finance corporation limited", "indian railway finance corporation"],
}


class CompanyExposureRepository:
    """
    Unified multi-jurisdictional repository for Central and State corporate exposures.
    """

    def __init__(
        self,
        central_exposure_dir: Optional[Path] = None,
        state_repo: Optional[StateCorporateExposureRepository] = None,
    ) -> None:
        if central_exposure_dir is None:
            self._central_dir = settings.DATA_DIR / "central_bills" / "corporate_exposure"
        else:
            self._central_dir = Path(central_exposure_dir)

        ensure_dir(self._central_dir)
        self._state_repo = state_repo or StateCorporateExposureRepository()
        logger.debug(
            "CompanyExposureRepository initialized | central_dir=%s | state_dir=%s",
            self._central_dir,
            self._state_repo.exposure_dir,
        )

    @property
    def central_dir(self) -> Path:
        return self._central_dir

    @property
    def state_repo(self) -> StateCorporateExposureRepository:
        return self._state_repo

    # ------------------------------------------------------------------
    # Write Operations (Central)
    # ------------------------------------------------------------------

    def save_central(self, exposure: StateCorporateExposure) -> None:
        """Persist a single Central exposure record."""
        current = self.get_central_by_bill(exposure.bill_id)
        updated = False
        new_list: list[StateCorporateExposure] = []
        for exp in current:
            if exp.company_id == exposure.company_id:
                new_list.append(exposure)
                updated = True
            else:
                new_list.append(exp)
        if not updated:
            new_list.append(exposure)
        self.save_central_for_bill(exposure.bill_id, new_list)

    def save_central_for_bill(self, bill_id: str, exposures: list[StateCorporateExposure]) -> None:
        """Persist Central exposures for a specific bill."""
        dest_path = self._central_dir / f"{bill_id}.json"
        data = [e.to_dict() for e in exposures]
        save_json(data, dest_path)
        logger.debug("Saved %d central exposures for bill: %s", len(exposures), bill_id)

    def save_central_many(self, exposures: list[StateCorporateExposure]) -> None:
        """Persist multiple Central exposures grouped by bill."""
        by_bill: dict[str, list[StateCorporateExposure]] = {}
        for exp in exposures:
            by_bill.setdefault(exp.bill_id, []).append(exp)
        for b_id, b_exps in by_bill.items():
            self.save_central_for_bill(b_id, b_exps)

    # ------------------------------------------------------------------
    # Read Operations
    # ------------------------------------------------------------------

    def get_central_by_bill(self, bill_id: str) -> list[StateCorporateExposure]:
        """Retrieve Central corporate exposures for a specific bill."""
        src_path = self._central_dir / f"{bill_id}.json"
        if not file_exists(src_path):
            return []
        try:
            data = load_json(src_path)
            if not isinstance(data, list):
                return []
            return [StateCorporateExposure.from_dict(item) for item in data]
        except Exception as exc:
            logger.error("Failed to load central exposures for bill '%s': %s", bill_id, exc)
            return []

    def get_all_central(self) -> list[StateCorporateExposure]:
        """Return all Central corporate exposures."""
        results: list[StateCorporateExposure] = []
        try:
            files = list_files(self._central_dir, "*.json")
            for f in files:
                results.extend(self.get_central_by_bill(f.stem))
        except Exception as exc:
            logger.error("Failed to list central corporate exposure records: %s", exc)
        return results

    def get_all_state(self) -> list[StateCorporateExposure]:
        """Return all State corporate exposures from the underlying State repository."""
        return self._state_repo.get_all()

    def get_all(self, jurisdiction: Optional[str] = None) -> list[StateCorporateExposure]:
        """
        Return all corporate exposures across all jurisdictions.
        Optionally filter by 'central' or 'state'.
        """
        j = jurisdiction.strip().lower() if jurisdiction else None
        if j == "central":
            return self.get_all_central()
        if j == "state":
            return self.get_all_state()
        return self.get_all_central() + self.get_all_state()

    def get_by_bill(self, bill_id: str) -> list[StateCorporateExposure]:
        """
        Retrieve corporate exposures for a bill across Central and State stores.
        """
        central_results = self.get_central_by_bill(bill_id)
        if central_results:
            return central_results
        return self._state_repo.get_by_bill(bill_id)

    # ------------------------------------------------------------------
    # Canonical Query Support (Queries A through H)
    # ------------------------------------------------------------------

    def resolve_company_identifier(self, identifier: str) -> list[str]:
        """
        Resolve a company name, alias, ticker, or ISIN to a set of matching company_ids.
        """
        target = identifier.strip().lower()
        matched_ids: set[str] = {target.upper()}

        for isin, aliases in _COMPANY_ALIAS_MAP.items():
            if target == isin.lower() or target in aliases or any(target in a for a in aliases):
                matched_ids.add(isin)
                for a in aliases:
                    if a.startswith("ine") or a.startswith("priv-") or a.startswith("soe-") or a.startswith("unlisted-"):
                        matched_ids.add(a.upper())

        return list(matched_ids)

    def get_bills_for_company(self, company_identifier: str) -> list[StateCorporateExposure]:
        """
        QUERY A: Which bills affect this company?
        Resolves company aliases, tickers, and ISINs across both Central and State legislation.
        """
        target_norm = company_identifier.strip().lower()
        matched_ids = {i.lower() for i in self.resolve_company_identifier(company_identifier)}

        results: list[StateCorporateExposure] = []
        for exp in self.get_all():
            c_id = exp.company_id.lower()
            c_name = exp.company_name.lower()
            c_ticker = exp.ticker.lower()

            if (
                c_id in matched_ids
                or target_norm in c_name
                or (c_ticker and target_norm == c_ticker)
                or any(alias in c_name for alias in matched_ids if len(alias) > 3)
            ):
                results.append(exp)

        return results

    def get_companies_for_bill(self, bill_id: str) -> list[StateCorporateExposure]:
        """
        QUERY B: Which companies are exposed to this bill?
        """
        return self.get_by_bill(bill_id)

    def get_exposure_explanation(self, bill_id: str, company_identifier: str) -> str:
        """
        QUERY C: Why is this company exposed?
        Returns a concise, fact-grounded explanation of the statutory and business connection.
        """
        exps = self.get_bills_for_company(company_identifier)
        matching = next((e for e in exps if e.bill_id == bill_id), None)
        if not matching:
            return f"No verified exposure identified between company '{company_identifier}' and bill '{bill_id}'."

        evidence_str = "; ".join(e.claim for e in matching.evidence) if matching.evidence else "No specific evidence recorded"
        return (
            f"{matching.company_name} has {matching.direct_indirect} exposure ({matching.exposure_strength} strength) "
            f"to bill '{matching.bill_id}' in the {matching.sector} ({matching.sub_sector}) sector. "
            f"Operational activity: '{matching.business_activity}'. Statutory mechanism: {matching.mechanism}. "
            f"Evidence: {evidence_str}."
        )

    def get_evidence_for_exposure(
        self, bill_id: str, company_identifier: str
    ) -> list[CorporateExposureEvidence]:
        """
        QUERY D: What evidence supports the exposure?
        """
        exps = self.get_bills_for_company(company_identifier)
        matching = next((e for e in exps if e.bill_id == bill_id), None)
        if matching:
            return list(matching.evidence)
        return []

    def get_activity_and_sector(
        self, bill_id: str, company_identifier: str
    ) -> dict[str, str]:
        """
        QUERY E: What sector/business activity creates the exposure?
        """
        exps = self.get_bills_for_company(company_identifier)
        matching = next((e for e in exps if e.bill_id == bill_id), None)
        if matching:
            return {
                "sector": matching.sector,
                "sub_sector": matching.sub_sector,
                "business_activity": matching.business_activity,
            }
        return {"sector": "UNKNOWN", "sub_sector": "UNKNOWN", "business_activity": "UNKNOWN"}

    def get_relevant_state(self, bill_id: str, company_identifier: str) -> str:
        """
        QUERY F: Which State is relevant?
        Returns the State name, or 'Central' / 'National' for Central bills.
        """
        exps = self.get_bills_for_company(company_identifier)
        matching = next((e for e in exps if e.bill_id == bill_id), None)
        if matching:
            return matching.state or ("Central" if matching.jurisdiction == "central" else "National")
        return "UNKNOWN"

    def is_direct_exposure(self, bill_id: str, company_identifier: str) -> str:
        """
        QUERY G: Is the exposure direct or indirect?
        Returns 'DIRECT', 'INDIRECT', 'NONE', or 'UNKNOWN'.
        """
        exps = self.get_bills_for_company(company_identifier)
        matching = next((e for e in exps if e.bill_id == bill_id), None)
        if matching:
            return matching.direct_indirect
        return "NONE"

    def get_economic_mechanism(self, bill_id: str, company_identifier: str) -> str:
        """
        QUERY H: What economic mechanism is involved?
        """
        exps = self.get_bills_for_company(company_identifier)
        matching = next((e for e in exps if e.bill_id == bill_id), None)
        if matching:
            return matching.mechanism
        return "NONE"

    # ------------------------------------------------------------------
    # Search & Discovery
    # ------------------------------------------------------------------

    def search(
        self,
        query: str = "",
        jurisdiction: Optional[str] = None,
        state: Optional[str] = None,
        company: Optional[str] = None,
        sector: Optional[str] = None,
        exposure_strength: Optional[str] = None,
        direct_indirect: Optional[str] = None,
        exposure_type: Optional[str] = None,
        mechanism: Optional[str] = None,
    ) -> list[StateCorporateExposure]:
        """
        Multi-attribute search across Central and State corporate exposure records.
        """
        all_exps = self.get_all(jurisdiction=jurisdiction)
        results: list[StateCorporateExposure] = []
        q = query.strip().lower() if query else ""

        target_state = (normalize_state(state) or state).strip().lower() if state else None
        target_company = company.strip().lower() if company else None
        target_sector = sector.strip().lower() if sector else None
        target_strength = exposure_strength.strip().upper() if exposure_strength else None
        target_directness = direct_indirect.strip().upper() if direct_indirect else None
        target_etype = exposure_type.strip().lower() if exposure_type else None
        target_mech = mechanism.strip().lower() if mechanism else None

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

            # 6. Exposure type filter
            if target_etype and e.exposure_type.lower() != target_etype:
                continue

            # 7. Mechanism filter
            if target_mech and e.mechanism.lower() != target_mech:
                continue

            # 8. Free-text query matching
            if q:
                evidence_text = " ".join(ev.claim + " " + ev.reference for ev in e.evidence).lower()
                searchable = (
                    f"{e.company_name} {e.ticker} {e.company_id} {e.sector} {e.sub_sector} "
                    f"{e.business_activity} {' '.join(e.state_presence)} {e.presence_type} "
                    f"{e.exposure_type} {e.mechanism} {e.state} {e.bill_id} {evidence_text}"
                ).lower()
                if q not in searchable:
                    continue

            results.append(e)

        return results

    # ------------------------------------------------------------------
    # Integrity & Audit
    # ------------------------------------------------------------------

    def check_duplicates(self) -> list[dict[str, Any]]:
        """
        Check for duplicate (bill_id, company_id) records within repositories.
        """
        duplicates: list[dict[str, Any]] = []
        seen: dict[tuple[str, str], int] = {}
        for exp in self.get_all():
            key = (exp.bill_id, exp.company_id)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] == 2:
                duplicates.append({"bill_id": exp.bill_id, "company_id": exp.company_id})
        return duplicates

    def count(self, jurisdiction: Optional[str] = None) -> int:
        """Return count of exposures across or within jurisdictions."""
        return len(self.get_all(jurisdiction=jurisdiction))

    def __repr__(self) -> str:
        return (
            f"<CompanyExposureRepository central_count={len(self.get_all_central())} "
            f"state_count={len(self.get_all_state())} total={self.count()}>"
        )
