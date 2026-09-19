"""
knowledge/state_stakeholder_engine.py
=====================================
Stakeholder knowledge mapping engine for Indian State legislative bills.

Associates State bills with grounded stakeholder groups based strictly on
bill text, policy category, and extracted legal provisions.
Pure knowledge-layer relationships with zero stock-market predictions.
"""

from __future__ import annotations

import re
from typing import Optional

from config.logging_config import get_logger
from knowledge.state_taxonomy import CATEGORY_STAKEHOLDERS, StateTaxonomyEngine
from schemas.bill import Bill

logger = get_logger(__name__)

# Keyword cues for specific stakeholder groups
_STAKEHOLDER_CUES: list[tuple[str, list[str]]] = [
    (
        "Platform & Gig Workers",
        ["gig worker", "platform worker", "delivery worker", "aggregator", "app-based"],
    ),
    (
        "App-based Aggregators / Platform Companies",
        ["aggregator", "platform company", "digital platform", "ride-hailing"],
    ),
    (
        "Vehicle Owners & Motorists",
        ["motor vehicle", "vehicle owner", "two-wheeler", "four-wheeler", "chassis"],
    ),
    (
        "Transport Operators & Fleet Owners",
        ["transport operator", "stage carriage", "contract carriage", "goods carriage", "fleet"],
    ),
    (
        "Aquaculture Operators & Fishers",
        ["aquaculture", "prawn", "shrimp", "hatchery", "aqua farm", "fish farmer"],
    ),
    (
        "Farmers & Agricultural Landowners",
        ["agricultural land", "ceiling on agricultural", "tenant farmer", "cultivator", "crop"],
    ),
    (
        "Property Owners & Real Estate Buyers",
        ["property tax", "registration", "stamp duty", "sale deed", "plot", "building permit"],
    ),
    (
        "Builders & Real Estate Developers",
        ["town planning", "layout", "development authority", "zoning", "building plan"],
    ),
    (
        "Industrial Units & MSMEs",
        ["industrial undertaking", "factory", "speed of doing business", "single window", "msme", "small enterprise"],
    ),
    (
        "Factory & Industrial Workers",
        ["factory worker", "overtime", "working hours", "occupational safety", "worker"],
    ),
    (
        "Commercial Establishments & Retailers",
        ["shops and establishments", "commercial establishment", "retail", "trader"],
    ),
    (
        "Electricity Consumers & Industrial Power Users",
        ["electricity consumer", "power tariff", "high tension", "low tension", "captive power"],
    ),
    (
        "Renewable Energy Developers & Power Generators",
        ["renewable energy", "generating company", "solar power", "wind power", "open access"],
    ),
    (
        "Government Contractors & Bidders",
        ["tender", "procuring entity", "bidder", "contractor", "public procurement"],
    ),
    (
        "IT & Cyber Infrastructure Operators",
        ["cyber security", "critical information infrastructure", "computer system", "network operator"],
    ),
    (
        "Municipal Corporations & Urban Local Bodies",
        ["municipal corporation", "municipality", "ward committee", "municipal commissioner"],
    ),
    (
        "Taxpayers & Commercial Merchants",
        ["goods and services tax", "vat", "input tax credit", "registered person", "dealer"],
    ),
    (
        "Elected Representatives & Legislators",
        ["prevention of disqualification", "member of legislative", "office of profit"],
    ),
]


class StateStakeholderEngine:
    """
    Identifies and maps relevant stakeholder groups for State bills.
    """

    def __init__(self, taxonomy_engine: Optional[StateTaxonomyEngine] = None) -> None:
        self.taxonomy_engine = taxonomy_engine or StateTaxonomyEngine()

    def identify_stakeholders(
        self,
        bill: Bill,
        text: str = "",
        policy_category: str = "",
    ) -> list[str]:
        """
        Identify stakeholder groups affected by a State bill.

        Parameters
        ----------
        bill : Bill
            The state bill record.
        text : str
            Extracted document corpus text.
        policy_category : str
            Classified policy category.

        Returns
        -------
        list[str]
            Deduplicated list of affected stakeholder groups.
        """
        stakeholders: list[str] = []

        # 1. Start with default baseline stakeholders for the category
        defaults = self.taxonomy_engine.get_default_stakeholders(policy_category)
        stakeholders.extend(defaults)

        # 2. Check for explicit text matches across cues
        combined = f"{bill.title.lower()} {(bill.bill_number or '').lower()} {text.lower()}"

        for group_name, kws in _STAKEHOLDER_CUES:
            for kw in kws:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, combined):
                    if group_name not in stakeholders:
                        stakeholders.append(group_name)
                    break

        # 3. Deduplicate preserving order
        deduped = list(dict.fromkeys(stakeholders))
        logger.debug("Identified %d stakeholders for bill '%s'", len(deduped), bill.bill_id)
        return deduped
