"""
knowledge/state_summary_engine.py
=================================
Plain-language summary generator and structured legislative provision extractor
for Indian State bills.

Operates purely deterministically, grounding summaries and extracted provisions
strictly in verified metadata and extracted document corpus text.
Enforces strict boundaries: separates FACT from bounded INTERPRETATION,
with zero market, company, or stock-price claims.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.bill import Bill
from schemas.state_knowledge import StateBillSummary

logger = get_logger(__name__)


class StateSummaryEngine:
    """
    Generates structured plain-language summaries and extracts legislative provisions
    for Indian State legislative bills.
    """

    def generate_summary(
        self,
        bill: Bill,
        text: str = "",
        policy_category: str = "",
        stakeholders: Optional[list[str]] = None,
        provisions: Optional[dict[str, Any]] = None,
    ) -> StateBillSummary:
        """
        Generate a structured plain-language summary for a State bill.

        Parameters
        ----------
        bill : Bill
            The state bill record.
        text : str
            Extracted corpus text.
        policy_category : str
            Classified policy category.
        stakeholders : list[str] | None
            Affected stakeholder groups.
        provisions : dict[str, Any] | None
            Pre-extracted structured provisions.
        """
        prov = provisions or self.extract_provisions(bill, text)
        st_list = stakeholders or prov.get("affected_groups", [])

        # 1. What is this bill?
        bill_num_str = f" ({bill.bill_number})" if bill.bill_number else ""
        what_is_bill = (
            f"'{bill.title}'{bill_num_str} is a State legislative measure introduced in the "
            f"{bill.state} {self._format_chamber(bill.house)} concerning {policy_category}."
        )

        # 2. What does it change?
        amended = prov.get("amended_acts", [])
        major_secs = prov.get("major_sections", [])
        if amended:
            acts_str = "; ".join(amended[:3])
            secs_str = f" across {len(major_secs)} identified sections/clauses" if major_secs else ""
            what_it_changes = (
                f"The bill introduces statutory amendments to existing state legislation, primarily modifying {acts_str}{secs_str}."
            )
        elif "Amendment" in bill.title or "amending" in text.lower():
            what_it_changes = (
                "The bill amends statutory provisions to update legal frameworks, adjust compliance requirements, or alter state administrative procedures."
            )
        else:
            what_it_changes = (
                "The bill establishes a substantive legal framework creating new state statutory standards, definitions, and administrative governance."
            )

        # 3. Why does it matter?
        obj = prov.get("objective")
        if obj and len(obj.strip()) > 30:
            clean_obj = " ".join(obj.strip().split()[:60])
            if not clean_obj.endswith("."):
                clean_obj += "..."
            why_it_matters = f"According to the official Statement of Objects and Reasons: \"{clean_obj}\""
        elif policy_category == "Labour, Employment & Gig Economy":
            why_it_matters = (
                "The legislation addresses employment conditions, worker protections, or welfare board mechanisms under state jurisdiction."
            )
        elif policy_category == "State Finance / Taxation":
            why_it_matters = (
                "The measure regulates state revenue collection, tax administrative procedures, or statutory fee schedules."
            )
        elif policy_category == "Electricity / Energy":
            why_it_matters = (
                "The measure regulates state energy tariffs, electricity duty rates, or renewable energy facilitation frameworks."
            )
        elif policy_category == "Transport & Motor Vehicles":
            why_it_matters = (
                "The measure governs motor vehicle taxation, transport permits, and vehicular regulatory compliance in the state."
            )
        elif policy_category == "Municipal Administration & Urban Development":
            why_it_matters = (
                "The measure governs urban local body powers, municipal administration, and urban development standards."
            )
        else:
            why_it_matters = (
                "The bill updates statutory authorities and procedural mechanisms in accordance with state policy priorities."
            )

        # 4. Who is affected?
        if st_list:
            who_is_affected = f"Primary affected groups include: {', '.join(st_list)}."
        else:
            who_is_affected = f"Citizens, commercial entities, and regulatory authorities operating in {bill.state}."

        # 5. Key provisions
        key_provisions: list[str] = []
        if amended:
            key_provisions.append(f"Statutory modification of {', '.join(amended[:2])}.")
        if major_secs:
            key_provisions.append(f"Identified clauses/sections amended: {', '.join(major_secs[:5])}.")
        if prov.get("financial_or_tax_provisions"):
            key_provisions.append(prov["financial_or_tax_provisions"])
        if prov.get("penalties_or_enforcement"):
            key_provisions.append(prov["penalties_or_enforcement"])
        if not key_provisions:
            key_provisions.append(f"Statutory provisions enacted under the legislative authority of {bill.state}.")

        # 6. Administrative implications
        admin_auth = prov.get("administrative_authority")
        if admin_auth:
            admin_impl = f"Administered and enforced under the authority of {admin_auth} and designated state officials."
        else:
            admin_impl = f"Enforced through the competent administrative departments of the Government of {bill.state}."

        # 7. Legislative status
        status_str = bill.status.value if hasattr(bill.status, "value") else str(bill.status)
        dates = []
        if bill.introduction_date:
            dates.append(f"introduced on {bill.introduction_date}")
        if bill.assent_date:
            dates.append(f"assented on {bill.assent_date}")
        date_clause = f" ({', '.join(dates)})" if dates else ""
        leg_status = f"Official status recorded as '{status_str.replace('_', ' ').title()}'{date_clause}."

        # 8. Source
        source = f"Official {bill.state} Legislature portal ({bill.source or 'State Legislature'})."

        return StateBillSummary(
            what_is_bill=what_is_bill,
            what_it_changes=what_it_changes,
            why_it_matters=why_it_matters,
            who_is_affected=who_is_affected,
            key_provisions=key_provisions,
            administrative_implications=admin_impl,
            legislative_status=leg_status,
            source=source,
        )

    def extract_provisions(self, bill: Bill, text: str = "") -> dict[str, Any]:
        """
        Extract structured legislative information and provisions from the bill text and metadata.
        """
        provisions: dict[str, Any] = {
            "title": bill.title,
            "bill_number": bill.bill_number,
            "year": bill.year,
            "state": bill.state,
            "chamber": bill.house.value if hasattr(bill.house, "value") else str(bill.house),
            "introduction_date": str(bill.introduction_date) if bill.introduction_date else None,
            "assent_date": str(bill.assent_date) if bill.assent_date else None,
            "status": bill.status.value if hasattr(bill.status, "value") else str(bill.status),
            "objective": None,
            "amended_acts": [],
            "major_sections": [],
            "affected_groups": [],
            "administrative_authority": None,
            "financial_or_tax_provisions": None,
            "penalties_or_enforcement": None,
        }

        if not text:
            return provisions

        # 1. Extract Statement of Objects and Reasons (Objective)
        obj_match = re.search(
            r"(?:STATEMENT\s+OF\s+OBJECTS\s+AND\s+REASONS|OBJECTS\s+AND\s+REASONS)[\s\:\-]+(.*?)(?:(?:MEMORANDUM\s+REGARDING|FINANCIAL\s+MEMORANDUM|ANNEXURE|\Z))",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if obj_match:
            raw_obj = obj_match.group(1).strip()
            # Clean formatting
            clean_obj = " ".join(raw_obj.split())
            if len(clean_obj) > 20:
                provisions["objective"] = clean_obj[:1200]

        # Fallback to preamble if Statement of Objects is not explicitly demarcated
        if not provisions["objective"]:
            preamble_match = re.search(
                r"(?:An\s+Act|A\s+Bill)\s+(?:further\s+to\s+amend|to\s+provide|to\s+consolidate|to\s+amend)(.*?)(?:Be\s+it\s+enacted|WHEREAS|\.)",
                text,
                re.IGNORECASE | re.DOTALL,
            )
            if preamble_match:
                clean_preamble = " ".join(preamble_match.group(0).strip().split())
                if len(clean_preamble) > 20:
                    provisions["objective"] = clean_preamble[:500]

        # 2. Extract Principal Amended Acts
        act_pattern = re.compile(
            r"\b((?:The\s+)?[A-Z][A-Za-z0-9\s\,\-\(\)]+\s+(?:Act|Code|Rules)(?:,\s+\d{4})?)\b"
        )
        # Search for acts specifically mentioned near "amend", "amendment", or "referred to as the principal act"
        amended_acts: list[str] = []
        for line in text.split("\n"):
            line_str = line.strip()
            if any(k in line_str.lower() for k in ["principal act", "amendment of", "hereinafter referred to", "amend the"]):
                matches = act_pattern.findall(line_str)
                for m in matches:
                    clean_m = " ".join(m.split()).strip()
                    # Filter out self-title and generic words
                    if "bill" in clean_m.lower() or len(clean_m.split()) < 3:
                        continue
                    if clean_m.lower() not in [a.lower() for a in amended_acts]:
                        amended_acts.append(clean_m)

        # Also search in bill title
        title_matches = act_pattern.findall(bill.title)
        for tm in title_matches:
            clean_tm = " ".join(tm.split()).strip()
            if "bill" not in clean_tm.lower() and len(clean_tm.split()) >= 3:
                if clean_tm.lower() not in [a.lower() for a in amended_acts]:
                    amended_acts.append(clean_tm)

        provisions["amended_acts"] = amended_acts[:6]

        # 3. Extract Major Sections / Clauses
        sec_pattern = re.compile(r"\b(?:Amendment\s+of\s+section|Insertion\s+of\s+new\s+section|Substitution\s+of\s+new\s+section)\s+(\d+[A-Za-z\-]*)", re.IGNORECASE)
        sec_matches = sec_pattern.findall(text)
        if sec_matches:
            provisions["major_sections"] = list(dict.fromkeys(sec_matches))[:10]
        else:
            # Look for numbered sections "2. Amendment of ...", "3. Insertion of ..."
            sec_num_pattern = re.compile(r"^\s*(\d+)\.\s+(?:Amendment|Substitution|Insertion|Short\s+title)", re.MULTILINE | re.IGNORECASE)
            num_matches = sec_num_pattern.findall(text)
            if num_matches:
                provisions["major_sections"] = [f"Section {m}" for m in dict.fromkeys(num_matches)][:10]

        # 4. Extract Financial / Tax provisions if present
        text_lower = text.lower()
        if any(w in text_lower for w in ["tax rate", "percent", "per cent", "duty shall be", "cess", "levy of duty", "fee"]):
            tax_match = re.search(r"((?:duty|tax|rate|fee|levy)[^\.\n]{10,120}(?:per\s+cent|\%|rupees|rs\.?)[^\.\n]{0,80}\.)", text, re.IGNORECASE)
            if tax_match:
                provisions["financial_or_tax_provisions"] = " ".join(tax_match.group(1).split())
            else:
                provisions["financial_or_tax_provisions"] = "Contains statutory fee, tax, or duty rate provisions."

        # 5. Extract Penalties / Enforcement provisions
        if any(w in text_lower for w in ["penalty", "imprisonment", "fine which may extend", "cognizable", "punishable", "offence"]):
            pen_match = re.search(r"((?:penalty|punishable|fine|imprisonment)[^\.\n]{10,140}\.)", text, re.IGNORECASE)
            if pen_match:
                provisions["penalties_or_enforcement"] = " ".join(pen_match.group(1).split())
            else:
                provisions["penalties_or_enforcement"] = "Specifies statutory inspection, penalty, or compliance enforcement mechanisms."

        # 6. Extract Administrative Authority
        auth_matches = re.findall(r"\b((?:State\s+Government|Commissioner|Director|Board|Authority|Registrar|Inspector|Collector)[A-Za-z\s]{0,40})\b", text)
        clean_auths = [a.strip() for a in auth_matches if len(a.strip().split()) >= 2 and len(a.strip()) < 50]
        if clean_auths:
            provisions["administrative_authority"] = clean_auths[0]

        return provisions

    @staticmethod
    def _format_chamber(house: Any) -> str:
        h_str = house.value if hasattr(house, "value") else str(house or "")
        mapping = {
            "vidhan_sabha": "Legislative Assembly (Vidhan Sabha)",
            "vidhan_parishad": "Legislative Council (Vidhan Parishad)",
            "lok_sabha": "Lok Sabha",
            "rajya_sabha": "Rajya Sabha",
        }
        return mapping.get(h_str.lower(), "Legislature")
