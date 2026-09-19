"""
knowledge/state_taxonomy.py
===========================
Policy taxonomy and categorization engine for Indian State legislative bills.

Classifies State bills into state-relevant policy domains without forcing them
into inappropriate Central-only economic categories.
Strictly distinguishes between OFFICIAL CLASSIFICATION and SYSTEM-DERIVED categories.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from config.logging_config import get_logger
from schemas.bill import Bill

logger = get_logger(__name__)

# State-specific policy categories
STATE_POLICY_CATEGORIES = [
    "State Finance / Taxation",
    "Electricity / Energy",
    "Transport & Motor Vehicles",
    "Municipal Administration & Urban Development",
    "Land & Property",
    "Agriculture & Allied Sectors",
    "Labour, Employment & Gig Economy",
    "Industrial Development & Business Regulation",
    "Public Procurement",
    "Digital, Technology & Cybersecurity",
    "Governance & Public Administration",
    "Other / Unclassified",
]

# Curated rules mapping keywords (in title, summary, and corpus text) to categories
_TAXONOMY_RULES: list[dict[str, Any]] = [
    {
        "category": "Labour, Employment & Gig Economy",
        "title_keywords": [
            "gig worker", "platform-based", "platform based", "shops and establishments",
            "factories", "labour", "worker", "employment", "gratuity", "minimum wages",
        ],
        "corpus_keywords": [
            "gig worker", "platform worker", "aggregator", "welfare board",
            "social security", "working hours", "inspector", "overtime",
        ],
        "priority": 10,
    },
    {
        "category": "Industrial Development & Business Regulation",
        "title_keywords": [
            "speed of doing business", "omnibus", "industries (facilitation)",
            "industries facilitation", "industrial facilitation", "ease of doing business",
            "industrial infrastructure",
        ],
        "corpus_keywords": [
            "single window", "clearance", "industrial policy", "investment facilitation",
            "industrial undertaking", "speed of doing business",
        ],
        "priority": 9,
    },
    {
        "category": "Public Procurement",
        "title_keywords": [
            "transparency in public procurements", "public procurement", "tender",
            "tenders", "procurement",
        ],
        "corpus_keywords": [
            "tender", "e-procurement", "procuring entity", "bidding", "contract award",
        ],
        "priority": 8,
    },
    {
        "category": "Digital, Technology & Cybersecurity",
        "title_keywords": [
            "cyber security", "cybersecurity", "digital infrastructure",
            "spatial data", "information technology", "data infrastructure",
        ],
        "corpus_keywords": [
            "cyber security", "critical information infrastructure", "spatial data",
            "gis", "cyber attack", "digital protection", "computer system",
        ],
        "priority": 8,
    },
    {
        "category": "Electricity / Energy",
        "title_keywords": [
            "electricity duty", "renewable energy", "electricity", "energy export",
            "power", "solar",
        ],
        "corpus_keywords": [
            "electricity duty", "generating company", "tariff", "transmission",
            "renewable energy export", "discom", "megawatt", "kilowatt",
        ],
        "priority": 7,
    },
    {
        "category": "Transport & Motor Vehicles",
        "title_keywords": [
            "motor vehicles", "motor vehicle", "vehicles taxation",
            "transport", "road tax",
        ],
        "corpus_keywords": [
            "motor vehicle", "taxation", "quarterly tax", "lifetime tax",
            "omnibus", "chassis", "registration mark", "transport authority",
        ],
        "priority": 7,
    },
    {
        "category": "Municipal Administration & Urban Development",
        "title_keywords": [
            "municipal laws", "municipal corporations", "town and country planning",
            "municipalities", "urban development", "greater hyd", "civic",
        ],
        "corpus_keywords": [
            "municipal commissioner", "corporation", "property tax", "building permit",
            "ward committee", "town planning", "urban local body", "zoning",
        ],
        "priority": 6,
    },
    {
        "category": "Agriculture & Allied Sectors",
        "title_keywords": [
            "aquaculture", "fisheries", "agricultural holdings", "agriculture",
            "farmers", "krishi", "crop",
        ],
        "corpus_keywords": [
            "aquaculture", "seed", "prawn", "hatchery", "holding",
            "agricultural land", "ceiling on agricultural", "rythu",
        ],
        "priority": 6,
    },
    {
        "category": "Land & Property",
        "title_keywords": [
            "land reforms", "ceiling on agricultural holdings", "registration (",
            "registration act", "land records", "spatial data infrastructure and land",
            "stamp duty", "stamps",
        ],
        "corpus_keywords": [
            "land reforms", "sub-registrar", "sale deed", "stamp duty",
            "land ceiling", "tenancy", "title deed", "alienation",
        ],
        "priority": 6,
    },
    {
        "category": "State Finance / Taxation",
        "title_keywords": [
            "goods and services tax", "gst", "value added tax", "vat",
            "taxation", "finance", "appropriation", "sales tax", "entry tax",
        ],
        "corpus_keywords": [
            "input tax credit", "sgst", "taxable turnover", "schedule",
            "assessment", "commercial tax", "excise",
        ],
        "priority": 5,
    },
    {
        "category": "Governance & Public Administration",
        "title_keywords": [
            "prevention of disqualification", "legislature", "salaries and pensions",
            "ministers salaries", "official language", "emblem",
        ],
        "corpus_keywords": [
            "office of profit", "disqualification", "legislative assembly",
            "allowances", "member of legislative",
        ],
        "priority": 4,
    },
]

# Stakeholder group mapping by State policy category
CATEGORY_STAKEHOLDERS: dict[str, list[str]] = {
    "State Finance / Taxation": [
        "Taxpayers",
        "Commercial Enterprises",
        "Traders & Merchants",
        "State Revenue Department",
    ],
    "Electricity / Energy": [
        "Electricity Consumers",
        "Power Generation Companies",
        "Distribution Companies (Discoms)",
        "Renewable Energy Developers",
        "State Energy Department",
    ],
    "Transport & Motor Vehicles": [
        "Vehicle Owners",
        "Transport Operators",
        "Commercial Fleet Operators",
        "Automotive Sector",
        "State Transport Department",
    ],
    "Municipal Administration & Urban Development": [
        "Urban Residents",
        "Property Owners",
        "Municipal Corporations & Urban Local Bodies",
        "Builders & Real Estate Developers",
    ],
    "Land & Property": [
        "Landowners",
        "Farmers",
        "Property Buyers & Sellers",
        "Real Estate Developers",
        "Registration & Revenue Authorities",
    ],
    "Agriculture & Allied Sectors": [
        "Farmers",
        "Aquaculture Operators & Fishers",
        "Agricultural Laborers",
        "Agribusinesses",
        "State Agriculture & Fisheries Departments",
    ],
    "Labour, Employment & Gig Economy": [
        "Platform & Gig Workers",
        "App-based Aggregators / Platform Companies",
        "Factory & Industrial Workers",
        "Employers & Commercial Establishments",
        "State Labour Welfare Board",
    ],
    "Industrial Development & Business Regulation": [
        "Industrial Enterprises",
        "MSMEs",
        "Investors",
        "Business Associations",
        "State Industries & Commerce Department",
    ],
    "Public Procurement": [
        "Government Contractors & Bidders",
        "Procuring Entities & Departments",
        "Suppliers",
        "State Finance Department",
    ],
    "Digital, Technology & Cybersecurity": [
        "Tech Companies & IT Service Providers",
        "Critical Infrastructure Operators",
        "Citizens & Internet Users",
        "State IT & Cyber Authorities",
    ],
    "Governance & Public Administration": [
        "Elected Representatives",
        "Legislative Assembly Secretariat",
        "Citizens",
        "State Government Administration",
    ],
    "Other / Unclassified": [
        "Citizens",
        "State Government",
    ],
}


class StateTaxonomyEngine:
    """
    Deterministic categorization engine for Indian State bills.
    """

    def classify(self, bill: Bill, text: str = "") -> tuple[str, str]:
        """
        Determine the policy category for a State bill.

        Returns
        -------
        tuple[str, str]
            (category_name, provenance_label)
            provenance_label is "AUTHORITATIVE" if source provides it,
            otherwise "SYSTEM_DERIVED".
        """
        # 1. Check if bill metadata has official authoritative sector/category
        if bill.sectors and len(bill.sectors) > 0:
            first_sector = bill.sectors[0].strip()
            if first_sector in STATE_POLICY_CATEGORIES:
                return first_sector, "AUTHORITATIVE"

        # 2. Match against curated State taxonomy rules
        title_lower = bill.title.lower()
        bill_num_lower = (bill.bill_number or "").lower()
        combined_text = f"{title_lower} {bill_num_lower} {text.lower()}"

        best_category = "Other / Unclassified"
        highest_score = 0

        # Sort rules by priority descending
        sorted_rules = sorted(_TAXONOMY_RULES, key=lambda r: r["priority"], reverse=True)

        for rule in sorted_rules:
            cat = rule["category"]
            score = 0

            # Title matching (heavily weighted)
            for kw in rule["title_keywords"]:
                if kw in title_lower:
                    score += 50

            # Corpus matching
            if text:
                for kw in rule["corpus_keywords"]:
                    # Word boundary search
                    pattern = r"\b" + re.escape(kw) + r"\b"
                    hits = len(re.findall(pattern, combined_text))
                    if hits > 0:
                        score += min(hits * 2, 20)

            if score > highest_score and score >= 20:
                highest_score = score
                best_category = cat

        logger.debug(
            "Classified bill '%s' -> %s (score=%d, prov=SYSTEM_DERIVED)",
            bill.bill_id,
            best_category,
            highest_score,
        )
        return best_category, "SYSTEM_DERIVED"

    def get_default_stakeholders(self, category: str) -> list[str]:
        """Return the default stakeholder groups for a given State policy category."""
        return CATEGORY_STAKEHOLDERS.get(category, ["Citizens", "State Government"])
