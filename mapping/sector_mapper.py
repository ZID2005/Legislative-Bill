"""
mapping/sector_mapper.py
========================
Sector and company mapping module.

This module bridges the gap between legislative text and financial market entities.
It maps a legislative bill (via its Knowledge Record) to potentially affected listed companies.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.bill import Bill
from schemas.company import Company
from schemas.knowledge_record import KnowledgeRecord
from schemas.mapping_record import BillCompanyMapping
from storage.company_repository import CompanyRepository

logger = get_logger(__name__)

_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


class SectorMapper:
    """
    Deterministic rule engine that maps a Bill and its KnowledgeRecord
    to potentially affected listed companies using sector taxonomies and lookup tables.
    """

    def __init__(self, company_repository: Optional[CompanyRepository] = None) -> None:
        self.company_repo = company_repository or CompanyRepository()
        self._load_rules()

    def _read_csv(self, filename: str) -> list[dict[str, str]]:
        path = _KNOWLEDGE_DIR / filename
        if not path.is_file():
            logger.warning("Mapping rules file not found: %s", path)
            return []
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def _load_rules(self) -> None:
        # Load company sector overrides
        self.company_overrides = {}
        for row in self._read_csv("company_sector.csv"):
            isin = row.get("isin", "").strip().upper()
            override_sector = row.get("override_sector", "").strip()
            if isin and override_sector:
                self.company_overrides[isin] = override_sector

        # Load ministry sector regulation maps
        self.ministry_sectors = {}
        for row in self._read_csv("ministry_sector.csv"):
            m = row.get("ministry", "").strip().lower()
            if m:
                primary = row.get("primary_sector", "").strip()
                sec_raw = row.get("secondary_sectors", "").strip()
                sec_list = []
                if sec_raw:
                    # Remove quotes and split by comma
                    clean_sec = sec_raw.strip('"').strip("'")
                    sec_list = [s.strip() for s in clean_sec.split(",") if s.strip()]

                all_sectors = []
                if primary:
                    all_sectors.append(primary.lower())
                for s in sec_list:
                    all_sectors.append(s.lower())

                self.ministry_sectors[m] = all_sectors

    def _sectors_match(self, s1: str, s2: str) -> bool:
        """Check if two sector names match (case-insensitive, allows substring matching for longer names)."""
        clean1 = s1.strip().lower()
        clean2 = s2.strip().lower()
        if clean1 == clean2:
            return True
        if len(clean1) > 4 and clean1 in clean2:
            return True
        if len(clean2) > 4 and clean2 in clean1:
            return True
        return False

    def map_bill_to_companies(
        self, bill: Bill, knowledge_record: KnowledgeRecord
    ) -> BillCompanyMapping:
        """
        Deterministically map a bill to candidate companies.
        """
        logger.info("Mapping bill to companies: %s", bill.bill_id)

        primary_sector = knowledge_record.primary_sector.strip()
        secondary_sectors = [s.strip() for s in knowledge_record.secondary_sectors]
        bill_ministry = knowledge_record.ministry.strip()

        # Combined text for keyword scanning
        bill_text = f"{bill.title}\n{bill.summary}\n{bill.full_text}"
        bill_text_lower = bill_text.lower()
        keywords_lower = [k.strip().lower() for k in knowledge_record.keywords]

        # Get all active companies
        all_companies = self.company_repo.get_all()
        candidate_companies = []

        for company in all_companies:
            if not company.is_active:
                continue

            # Determine company sector (with override support)
            company_isin = company.isin.strip().upper()
            comp_sector = self.company_overrides.get(company_isin, company.sector).strip()

            # Check if company's sector matches primary or secondary sectors of the bill
            is_primary_match = self._sectors_match(comp_sector, primary_sector)
            is_secondary_match = any(self._sectors_match(comp_sector, s) for s in secondary_sectors)

            if not (is_primary_match or is_secondary_match):
                continue

            # Calculate deterministic confidence
            confidence = 0.0
            reasons = []

            # 1. Sector match base score
            if is_primary_match:
                confidence += 0.50
                reasons.append(
                    f"Company sector '{comp_sector}' matches bill primary sector exactly"
                )
            else:
                confidence += 0.30
                reasons.append(f"Company sector '{comp_sector}' matches bill secondary sector")

            # 2. Industry / Sub-industry matches
            industry_matched = False
            if company.industry and company.industry.strip():
                ind_clean = company.industry.strip().lower()
                # Check for exact word or phrase mention (with optional plural 's')
                pattern = r"\b" + re.escape(ind_clean) + r"s?\b"
                if re.search(pattern, bill_text_lower) or any(
                    ind_clean in kw for kw in keywords_lower
                ):
                    confidence += 0.20
                    reasons.append(f"Industry matches ('{company.industry}')")
                    industry_matched = True

            if not industry_matched and company.sub_industry and company.sub_industry.strip():
                sub_clean = company.sub_industry.strip().lower()
                pattern = r"\b" + re.escape(sub_clean) + r"s?\b"
                if re.search(pattern, bill_text_lower) or any(
                    sub_clean in kw for kw in keywords_lower
                ):
                    confidence += 0.10
                    reasons.append(f"Sub-industry matches ('{company.sub_industry}')")

            # 3. Ministry support matching
            if bill_ministry:
                m_lower = bill_ministry.lower()
                regulated_sectors = self.ministry_sectors.get(m_lower, [])
                if any(self._sectors_match(comp_sector, reg_sec) for reg_sec in regulated_sectors):
                    confidence += 0.20
                    reasons.append(
                        f"Ministry ({bill_ministry}) regulates/supports sector '{comp_sector}'"
                    )

            # 4. Direct company name or alias mention
            name_clean = company.company_name.lower()
            # Simple normalisation: strip trailing "limited", "ltd", "corporation"
            name_normalized = re.sub(
                r"\b(limited|ltd|co|company|corp|corporation)\b", "", name_clean
            ).strip()

            name_mentioned = False
            if name_normalized and len(name_normalized) > 3:
                # Use boundary check for normalized name
                pattern = r"\b" + re.escape(name_normalized) + r"\b"
                if re.search(pattern, bill_text_lower):
                    name_mentioned = True

            # Check aliases
            if not name_mentioned:
                for alias in company.aliases:
                    alias_clean = alias.strip().lower()
                    if alias_clean and len(alias_clean) > 2:
                        pattern = r"\b" + re.escape(alias_clean) + r"\b"
                        if re.search(pattern, bill_text_lower):
                            name_mentioned = True
                            break

            if name_mentioned:
                confidence += 0.10
                reasons.append(f"Company name/alias explicitly mentioned in bill text")

            # Finalize score
            confidence = max(0.0, min(1.0, round(confidence, 2)))
            reason_str = "; ".join(reasons) + "."

            candidate_companies.append(
                {
                    "isin": company.isin,
                    "company_name": company.company_name,
                    "ticker_nse": company.ticker_nse,
                    "sector": comp_sector,
                    "industry": company.industry,
                    "confidence": confidence,
                    "reason": reason_str,
                }
            )

        # Sort candidate companies: confidence descending, then name ascending
        candidate_companies.sort(key=lambda x: (-x["confidence"], x["company_name"]))

        max_confidence = (
            max([c["confidence"] for c in candidate_companies]) if candidate_companies else 0.0
        )

        if candidate_companies:
            mapping_reason = (
                f"Mapped to {len(candidate_companies)} candidate companies in primary sector '{primary_sector}' "
                f"and secondary sectors. Maximum confidence: {max_confidence:.2f}."
            )
        else:
            mapping_reason = (
                f"No candidate companies found in the database matching primary sector '{primary_sector}' "
                f"or secondary sectors."
            )

        return BillCompanyMapping(
            bill_id=bill.bill_id,
            bill_title=bill.title,
            ministry=bill_ministry,
            policy_domain=knowledge_record.policy_domain,
            economic_domain=knowledge_record.economic_domain,
            primary_sector=primary_sector,
            secondary_sectors=secondary_sectors,
            candidate_companies=candidate_companies,
            mapping_confidence=max_confidence,
            mapping_reason=mapping_reason,
        )
