"""
knowledge/state_economic_taxonomy.py
====================================
Comprehensive economic and stakeholder taxonomy for Indian State legislative bills.

Designed specifically for State-level economic impact analysis:
- Broader than Central company-only sector taxonomies.
- Preserves existing policy-domain classification separately.
- Supports hierarchical classification (PRIMARY, SECONDARY, NONE, UNKNOWN).
- Structured, extensible stakeholder taxonomy across PEOPLE, BUSINESSES,
  INSTITUTIONS, and ECONOMIC GROUPS.
- Provides closed vocabularies for roles, impact mechanisms, impact directions,
  direct vs indirect effects, geographic scopes, and corporate exposure readiness.

Strictly separated from Central Government taxonomy and market prediction systems.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional


# ==============================================================================
# 1. State Economic Sectors Taxonomy
# ==============================================================================

class SectorLevel(str, Enum):
    """Classification level for an economic sector."""
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


STATE_ECONOMIC_SECTORS: list[str] = [
    "Agriculture",
    "Fisheries",
    "Livestock",
    "Food Processing",
    "Manufacturing",
    "Construction",
    "Real Estate",
    "Infrastructure",
    "Roads & Transport",
    "Logistics",
    "Ports & Maritime",
    "Tourism",
    "Hospitality",
    "Retail",
    "Wholesale",
    "MSME",
    "Banking & Finance",
    "Insurance",
    "Healthcare",
    "Pharmaceuticals",
    "Education",
    "IT & Digital Services",
    "Telecommunications",
    "Energy",
    "Electricity",
    "Renewable Energy",
    "Mining",
    "Metals",
    "Chemicals",
    "Textiles",
    "Labour & Employment",
    "Gig Economy",
    "Public Administration",
    "Municipal Services",
    "Urban Development",
    "Rural Development",
    "Environment",
    "Water",
    "Housing",
    "Consumer Services",
    "Professional Services",
    "Other",
]

# Set for fast lookup and validation
VALID_ECONOMIC_SECTORS: set[str] = set(STATE_ECONOMIC_SECTORS)


# Sub-sectors and typical economic activities mapping
SECTOR_HIERARCHY: dict[str, dict[str, list[str]]] = {
    "Agriculture": {
        "sub_sectors": ["Farming", "Horticulture", "Seed Production", "Agrochemicals", "Agricultural Marketing"],
        "activities": ["Crop cultivation", "Agricultural produce trading", "Mandi operations", "Farm mechanization"],
    },
    "Fisheries": {
        "sub_sectors": ["Aquaculture", "Inland Fisheries", "Marine Fisheries", "Fish Processing", "Hatcheries"],
        "activities": ["Shrimp and prawn farming", "Fish cultivation", "Aquaculture licensing", "Seafood export processing"],
    },
    "Livestock": {
        "sub_sectors": ["Dairy Farming", "Bovine Breeding", "Poultry", "Veterinary Services", "Animal Husbandry"],
        "activities": ["Semen station management", "Livestock breeding", "Veterinary care", "Dairy production"],
    },
    "Food Processing": {
        "sub_sectors": ["Grain Milling", "Dairy Processing", "Meat & Seafood Processing", "Packaged Foods"],
        "activities": ["Food preservation", "Packaging", "Cold chain logistics", "Quality grading"],
    },
    "Manufacturing": {
        "sub_sectors": ["Heavy Engineering", "Automotive", "Electronics", "Chemicals", "Industrial Goods"],
        "activities": ["Factory production", "Industrial assembly", "Machinery manufacturing", "Equipment fabrication"],
    },
    "Construction": {
        "sub_sectors": ["Civil Infrastructure", "Commercial Building", "Residential Construction", "Contracting"],
        "activities": ["Building erection", "Public works contracting", "Site preparation", "Structural engineering"],
    },
    "Real Estate": {
        "sub_sectors": ["Residential Real Estate", "Commercial Real Estate", "Land Development", "Property Broking"],
        "activities": ["Property registration", "Plot layout development", "Stamp duty valuation", "Tenancy management"],
    },
    "Infrastructure": {
        "sub_sectors": ["Urban Infrastructure", "Industrial Corridors", "Irrigation Works", "Water Supply"],
        "activities": ["Canal construction", "Water distribution works", "Industrial park setup", "Civic asset creation"],
    },
    "Roads & Transport": {
        "sub_sectors": ["Passenger Road Transport", "Commercial Freight", "Motor Vehicle Regulation", "Automotive Fleet"],
        "activities": ["Motor vehicle taxation", "Stage carriage operations", "Fleet ownership", "Vehicle registration"],
    },
    "Logistics": {
        "sub_sectors": ["Warehousing", "Freight Forwarding", "Cold Storage", "Last-Mile Delivery"],
        "activities": ["Goods carriage", "Parcel delivery", "Storage operations", "Cargo handling"],
    },
    "Ports & Maritime": {
        "sub_sectors": ["Coastal Shipping", "Port Terminals", "Shipyard & Repair", "Inland Waterways"],
        "activities": ["Vessel docking", "Cargo stevedoring", "Maritime transport", "Port fee collection"],
    },
    "Tourism": {
        "sub_sectors": ["Eco-tourism", "Heritage Tourism", "Pilgrimage Tourism", "Tour Operations"],
        "activities": ["Tourist destination management", "Travel booking", "Guided tours", "Monument preservation"],
    },
    "Hospitality": {
        "sub_sectors": ["Hotels & Resorts", "Restaurants & Food Service", "Homestays", "Catering"],
        "activities": ["Guest accommodation", "Food & beverage service", "Hospitality licensing", "Commercial dining"],
    },
    "Retail": {
        "sub_sectors": ["Departmental Stores", "Shops & Commercial Outlets", "E-Commerce", "Specialty Retail"],
        "activities": ["Over-the-counter retail", "Shop establishment registration", "Merchandise sales", "Store operations"],
    },
    "Wholesale": {
        "sub_sectors": ["Commodity Wholesale", "Agricultural Wholesale", "B2B Trade", "Wholesale Markets"],
        "activities": ["Bulk goods trading", "Wholesale distribution", "Market yard operations", "B2B invoicing"],
    },
    "MSME": {
        "sub_sectors": ["Micro Enterprises", "Small Enterprises", "Medium Enterprises", "Artisanal Units"],
        "activities": ["Small-scale fabrication", "Job-work manufacturing", "Cottage production", "Speed of business facilitation"],
    },
    "Banking & Finance": {
        "sub_sectors": ["Commercial Banking", "Cooperative Credit", "NBFCs", "Microfinance"],
        "activities": ["Lending", "Deposit mobilization", "Financial intermediation", "Debt recovery"],
    },
    "Insurance": {
        "sub_sectors": ["General Insurance", "Life Insurance", "Health Insurance", "Crop Insurance"],
        "activities": ["Underwriting", "Claims settlement", "Policy distribution", "Risk pooling"],
    },
    "Healthcare": {
        "sub_sectors": ["Hospitals & Clinics", "Diagnostic Laboratories", "Medical Devices", "Public Health"],
        "activities": ["Clinical consultations", "Inpatient hospital care", "Diagnostic testing", "Epidemic prevention"],
    },
    "Pharmaceuticals": {
        "sub_sectors": ["Formulations", "APIs", "Biotechnology", "Traditional Medicine / AYUSH"],
        "activities": ["Drug manufacturing", "Clinical research", "Pharmacy retail", "Medicine formulation"],
    },
    "Education": {
        "sub_sectors": ["Higher Education", "Private Universities", "Schools", "Vocational Training"],
        "activities": ["Degree granting", "Curriculum instruction", "Campus administration", "Accreditation compliance"],
    },
    "IT & Digital Services": {
        "sub_sectors": ["Software Development", "ITeS / BPO", "Cybersecurity", "Spatial & GIS Data"],
        "activities": ["Software engineering", "Digital infrastructure management", "Cyber resilience", "GIS mapping"],
    },
    "Telecommunications": {
        "sub_sectors": ["Mobile Network Operations", "Broadband & Fiber", "Tower Infrastructure", "Data Centers"],
        "activities": ["Right of way deployment", "Fiber cabling", "Network transmission", "Telecom operations"],
    },
    "Energy": {
        "sub_sectors": ["Power Generation", "Power Transmission", "Electricity Distribution", "Conventional Fuels"],
        "activities": ["Energy generation", "Power wheeling", "Electricity billing", "Energy duty payment"],
    },
    "Electricity": {
        "sub_sectors": ["Discom Operations", "Tariff Regulation", "High Tension Supply", "Captive Power"],
        "activities": ["Electricity duty compliance", "Power grid connection", "Metering and billing", "Open access"],
    },
    "Renewable Energy": {
        "sub_sectors": ["Solar Power", "Wind Energy", "Green Hydrogen", "Bio-Energy"],
        "activities": ["Clean power generation", "Green energy export", "Solar farm installation", "Renewable wheeling"],
    },
    "Mining": {
        "sub_sectors": ["Mineral Extraction", "Quarrying", "Sand Mining", "Mineral Exploration"],
        "activities": ["Mining lease operations", "Extraction of minor minerals", "Royalty compliance", "Ore haulage"],
    },
    "Metals": {
        "sub_sectors": ["Iron & Steel", "Aluminum & Non-Ferrous", "Foundries", "Metal Processing"],
        "activities": ["Metal smelting", "Casting and rolling", "Fabrication", "Scrap processing"],
    },
    "Chemicals": {
        "sub_sectors": ["Specialty Chemicals", "Fertilizers", "Industrial Gases", "Petrochemicals"],
        "activities": ["Chemical synthesis", "Toxic substance handling", "Industrial processing", "Pollution prevention"],
    },
    "Textiles": {
        "sub_sectors": ["Spinning & Weaving", "Garment Manufacturing", "Handlooms", "Apparel Export"],
        "activities": ["Yarn production", "Fabric dyeing", "Garment stitching", "Apparel retail"],
    },
    "Labour & Employment": {
        "sub_sectors": ["Industrial Labour", "Commercial Labour", "Welfare Boards", "Staffing & Contracting"],
        "activities": ["Working-hours compliance", "Overtime administration", "Welfare fund contribution", "Safety protocols"],
    },
    "Gig Economy": {
        "sub_sectors": ["App-Based Delivery", "Ride Hailing", "Platform Services", "Logistics Aggregation"],
        "activities": ["Platform work delivery", "Aggregator commission fee collection", "Welfare board registration", "Social security tracking"],
    },
    "Public Administration": {
        "sub_sectors": ["State Secretariat", "District Administration", "Statutory Boards", "Electoral Governance"],
        "activities": ["Statute enforcement", "Disqualification administration", "Public record keeping", "Administrative procedure"],
    },
    "Municipal Services": {
        "sub_sectors": ["Urban Civic Bodies", "Town Planning", "Solid Waste Management", "Civic Licensing"],
        "activities": ["Municipal taxation", "Building plan approvals", "Property assessment", "Local civic maintenance"],
    },
    "Urban Development": {
        "sub_sectors": ["Metropolitan Planning", "Zoning Authorities", "Smart Cities", "Urban Transit"],
        "activities": ["Master planning", "Zoning compliance", "Development authority approvals", "Urban redevelopment"],
    },
    "Rural Development": {
        "sub_sectors": ["Panchayati Raj", "Rural Infrastructure", "Gram Panchayats", "Village Commons"],
        "activities": ["Panchayat governance", "Rural taxation", "Village civic administration", "Rural public works"],
    },
    "Environment": {
        "sub_sectors": ["Pollution Control", "Forest & Wildlife", "Waste Management", "Ecology"],
        "activities": ["Environmental clearances", "Emission compliance", "Wildlife protection", "Cruelty prevention"],
    },
    "Water": {
        "sub_sectors": ["Irrigation & Canals", "Groundwater Regulation", "Drinking Water Supply", "Water Resources"],
        "activities": ["Canal water management", "Irrigation cess collection", "Water extraction licensing", "Water resource development"],
    },
    "Housing": {
        "sub_sectors": ["Affordable Housing", "Tenancy & Rent Control", "Housing Boards", "Cooperative Societies"],
        "activities": ["Residential allotment", "Building tax compliance", "Tenancy enforcement", "Housing maintenance"],
    },
    "Consumer Services": {
        "sub_sectors": ["Personal Services", "Entertainment & Cultural Activism", "Consumer Retail", "Repair Services"],
        "activities": ["Cultural production", "Consumer transaction", "Cine artist welfare", "Service delivery"],
    },
    "Professional Services": {
        "sub_sectors": ["Legal Services", "Accounting & Audit", "Medical Practice", "Engineering & Architecture"],
        "activities": ["Medical practitioner registration", "Professional practice licensing", "Partnership firm registration", "Consultancy"],
    },
    "Other": {
        "sub_sectors": ["General Statutory Provisions", "Repealing & Saving", "Miscellaneous Administration"],
        "activities": ["Obsolete statute repeal", "General statutory amendments", "Procedural adjustments"],
    },
}


# ==============================================================================
# 2. Structured Stakeholder Taxonomy (Extensible)
# ==============================================================================

STAKEHOLDER_CATEGORIES = ["people", "businesses", "institutions", "economic_groups"]

STAKEHOLDER_BRANCHES: dict[str, list[str]] = {
    "people": [
        "Farmers",
        "Agricultural workers",
        "Gig workers",
        "Employees",
        "Employers",
        "Consumers",
        "Students",
        "Patients",
        "Tenants",
        "Homeowners",
        "Property buyers",
        "Senior citizens",
        "Women",
        "Children",
        "Rural residents",
        "Urban residents",
        "Cine and cultural activists",
        "Doctors and medical practitioners",
        "Non-resident workers",
    ],
    "businesses": [
        "MSMEs",
        "Startups",
        "Large enterprises",
        "Retailers",
        "Wholesalers",
        "Manufacturers",
        "Contractors",
        "Transport operators",
        "Aggregators",
        "Developers",
        "Hotels",
        "Restaurants",
        "Hospitals",
        "Schools",
        "Colleges",
        "Professional firms",
        "Aquaculture operators",
        "Power generation companies",
        "Commercial establishments",
        "Partnership firms",
    ],
    "institutions": [
        "State Government",
        "Local Government",
        "Municipal bodies",
        "Panchayats",
        "Regulators",
        "Courts/tribunals",
        "Public authorities",
        "Trade unions",
        "Industry associations",
        "Welfare boards",
        "State universities",
        "Police and law enforcement",
    ],
    "economic_groups": [
        "Investors",
        "Taxpayers",
        "Landowners",
        "Exporters",
        "Importers",
        "Service providers",
        "Labour force",
        "Electricity consumers",
        "Water users",
    ],
}

# Reverse lookup map: stakeholder -> branch
STAKEHOLDER_TO_BRANCH: dict[str, str] = {}
for branch, items in STAKEHOLDER_BRANCHES.items():
    for item in items:
        STAKEHOLDER_TO_BRANCH[item.lower()] = branch


# ==============================================================================
# 3. Stakeholder Impact Classification Enums
# ==============================================================================

class StakeholderRole(str, Enum):
    """Specific role of the stakeholder in relation to the legislative bill."""
    AFFECTED = "affected"
    PRIMARY_AFFECTED = "primary_affected"
    SECONDARY_AFFECTED = "secondary_affected"
    POTENTIAL_BENEFICIARY = "potential_beneficiary"
    POTENTIAL_COST_BEARER = "potential_cost_bearer"
    REGULATOR_IMPLEMENTER = "regulator/implementer"
    INDIRECTLY_AFFECTED = "indirectly_affected"


class ImpactDirection(str, Enum):
    """Direction of estimated economic/operational impact on the stakeholder."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    MIXED = "mixed"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


class ImpactMechanism(str, Enum):
    """Underlying statutory mechanism through which the bill affects the stakeholder."""
    COMPLIANCE = "compliance"
    TAXATION = "taxation"
    SUBSIDY = "subsidy"
    LICENSING = "licensing"
    LABOUR_REQUIREMENT = "labour_requirement"
    PRICING = "pricing"
    LAND_USE = "land_use"
    ENVIRONMENTAL_REQUIREMENT = "environmental_requirement"
    REGISTRATION = "registration"
    REPORTING = "reporting"
    PROCUREMENT = "procurement"
    ACCESS = "access"
    ELIGIBILITY = "eligibility"
    PUBLIC_SERVICE = "public_service"
    REGULATION = "regulation"
    INFRASTRUCTURE = "infrastructure"
    ENFORCEMENT = "enforcement"
    OTHER = "other"


class ImpactType(str, Enum):
    """Degree of proximity of the legislative effect."""
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"
    UNKNOWN = "UNKNOWN"


# ==============================================================================
# 4. State Economic Geography Enums
# ==============================================================================

class GeographicScope(str, Enum):
    """Geographic relevance and coverage of the bill."""
    STATE_WIDE = "state-wide"
    DISTRICT_LEVEL = "district-level"
    CITY_MUNICIPAL = "city/municipal"
    RURAL = "rural"
    URBAN = "urban"
    REGIONAL = "regional"
    SECTOR_SPECIFIC = "sector-specific geography"
    UNKNOWN = "unknown"


# ==============================================================================
# 5. State Company-Link Readiness Enum
# ==============================================================================

class CompanyExposureReadiness(str, Enum):
    """
    Readiness indicator classifying whether a State bill could later be evaluated
    for listed company corporate exposure.
    Strictly a readiness indicator; does NOT produce stock tickers, predictions, or returns.
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


# ==============================================================================
# 6. Helper Functions & Extensibility
# ==============================================================================

def validate_economic_sector(sector: str) -> bool:
    """Validate if a sector name is part of the recognized state economic taxonomy."""
    return sector.strip() in VALID_ECONOMIC_SECTORS


def get_sector_metadata(sector: str) -> dict[str, list[str]]:
    """Retrieve sub-sectors and economic activities for a recognized sector."""
    return SECTOR_HIERARCHY.get(
        sector.strip(),
        {"sub_sectors": [], "activities": []}
    )


def resolve_stakeholder_branch(stakeholder: str) -> str:
    """Resolve the branch (people, businesses, institutions, economic_groups) for a stakeholder."""
    sh_lower = stakeholder.strip().lower()
    if sh_lower in STAKEHOLDER_TO_BRANCH:
        return STAKEHOLDER_TO_BRANCH[sh_lower]
    # Substring matching fallback
    for known, branch in STAKEHOLDER_TO_BRANCH.items():
        if known in sh_lower or sh_lower in known:
            return branch
    return "other"


# ==============================================================================
# 7. Comprehensive State Economic Mechanism Taxonomy (Task 8.8 Phase 1)
# ==============================================================================

STATE_ECONOMIC_MECHANISMS: list[str] = [
    "taxation",
    "subsidy",
    "compliance_cost",
    "labour_cost",
    "licensing",
    "regulation",
    "pricing",
    "demand",
    "supply",
    "investment",
    "infrastructure",
    "land",
    "electricity_cost",
    "transportation_cost",
    "financing",
    "credit",
    "procurement",
    "market_access",
    "environmental_cost",
    "public_spending",
    "productivity",
    "employment",
    "wages",
    "consumer_cost",
    "other",
    "unknown",
]

VALID_ECONOMIC_MECHANISMS: set[str] = set(STATE_ECONOMIC_MECHANISMS)


def validate_economic_mechanism(mechanism: str) -> bool:
    """Validate if an economic mechanism belongs to the recognized taxonomy."""
    return mechanism.strip().lower() in VALID_ECONOMIC_MECHANISMS


def normalize_economic_mechanism(raw_mechanism: str) -> str:
    """
    Map and normalize ad-hoc statutory mechanism strings into the canonical
    26-mechanism State Economic Taxonomy.
    """
    m = raw_mechanism.strip().lower().replace("-", "_").replace(" ", "_")
    if m in VALID_ECONOMIC_MECHANISMS:
        return m

    # Mappings from statutory or sector terms
    mapping = {
        "compliance": "compliance_cost",
        "tax": "taxation",
        "duties": "taxation",
        "duty": "taxation",
        "cess": "taxation",
        "labour_requirement": "labour_cost",
        "labour": "labour_cost",
        "labor": "labour_cost",
        "workforce": "labour_cost",
        "environmental_requirement": "environmental_cost",
        "environment": "environmental_cost",
        "pollution": "environmental_cost",
        "license": "licensing",
        "permit": "licensing",
        "land_use": "land",
        "property": "land",
        "electricity": "electricity_cost",
        "power": "electricity_cost",
        "transport": "transportation_cost",
        "logistics": "transportation_cost",
        "public_service": "public_spending",
        "enforcement": "regulation",
        "registration": "compliance_cost",
        "reporting": "compliance_cost",
        "access": "market_access",
        "welfare": "public_spending",
    }
    return mapping.get(m, "other" if m else "unknown")

