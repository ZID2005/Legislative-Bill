"""
knowledge/state_company_universe.py
===================================
Curated Controlled State Corporate Universe for Indian State Legislative Exposure.

Manages candidate companies (listed and unlisted) with verified, grounded operational
presence across Andhra Pradesh, Karnataka, Kerala, and Telangana.

Reuses the Central 47 production companies enriched with verified State operations,
plus carefully selected State-relevant companies with authoritative provenance.

Guarantees:
- ZERO fabricated companies
- ZERO fabricated tickers
- ZERO fabricated facilities or State presences
- ZERO stock price predictions
- Strict listed vs unlisted status
"""

from __future__ import annotations

from typing import Any, Optional
from schemas.company import Company, MarketCapCategory
from schemas.state_corporate_exposure import StatePresenceRecord


def _build_state_companies() -> list[Company]:
    """
    Construct the verified, controlled State company universe.
    """
    companies: list[Company] = []

    # --------------------------------------------------------------------------
    # 1. CENTRAL COMPANIES ENRICHED WITH GROUNDED STATE PRESENCE
    # --------------------------------------------------------------------------

    # Reliance Industries Limited
    companies.append(
        Company(
            isin="INE002A01018",
            company_name="Reliance Industries Limited",
            ticker_nse="RELIANCE",
            ticker_bse="RELIANCE",
            bse_code="500325",
            sector="Energy",
            industry="Oil Gas & Fuels",
            sub_industry="Refining & Marketing",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=1800000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.ril.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Integrated energy, petrochemicals, telecommunications, and retail conglomerate.",
            state_presences=[
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["plant", "infrastructure", "retail", "logistics"],
                    facility_locations=["Kakinada", "Visakhapatnam", "Vijayawada"],
                    description="KG-D6 onshore gas terminal and processing plant at Gadimoga, Kakinada; statewide retail and Jio telecom infrastructure.",
                    evidence_source="Annual Report 2023-24 (Oil & Gas operations / Jio network disclosure)",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["retail", "logistics", "office", "infrastructure"],
                    facility_locations=["Hyderabad", "Warangal"],
                    description="Reliance Retail fulfillment centres, digital hubs, and telecom infrastructure.",
                    evidence_source="Investor Presentation & Official Website",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["retail", "logistics", "office", "infrastructure"],
                    facility_locations=["Bengaluru", "Mangaluru", "Mysuru"],
                    description="Extensive retail stores, regional logistics hubs, and technology centres.",
                    evidence_source="Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["retail", "logistics", "infrastructure"],
                    facility_locations=["Kochi", "Thiruvananthapuram", "Kozhikode"],
                    description="Retail distribution networks, petroleum retail outlets, and Jio circles.",
                    evidence_source="Annual Report 2023-24",
                ),
            ],
            business_activities=["Gas processing", "Petroleum retailing", "Retail distribution", "Telecommunications"],
        )
    )

    # Tata Consultancy Services Limited
    companies.append(
        Company(
            isin="INE467B01029",
            company_name="Tata Consultancy Services Limited",
            ticker_nse="TCS",
            ticker_bse="TCS",
            bse_code="532540",
            sector="Technology",
            industry="IT Services",
            sub_industry="Software Services",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=1400000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.tcs.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Global IT services, consulting, and business solutions provider.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Bengaluru"],
                    description="Multiple software development campuses in Whitefield and Electronic City.",
                    evidence_source="TCS Annual Report (Facility Disclosures)",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Hyderabad"],
                    description="Major technology development centres at HITEC City and Adibatla SEZ.",
                    evidence_source="TCS Annual Report (Facility Disclosures)",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Kochi", "Thiruvananthapuram"],
                    description="Development operations at Infopark Kochi and Peepul Park Thiruvananthapuram.",
                    evidence_source="TCS Annual Report",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Visakhapatnam"],
                    description="IT development centre in Visakhapatnam.",
                    evidence_source="TCS State Operations Filings",
                ),
            ],
            business_activities=["IT services", "Software development", "BPO services", "Consulting"],
        )
    )

    # Infosys Limited
    companies.append(
        Company(
            isin="INE009A01021",
            company_name="Infosys Limited",
            ticker_nse="INFY",
            ticker_bse="INFY",
            bse_code="500209",
            sector="Technology",
            industry="IT Services",
            sub_industry="Software Services",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=650000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://www.infosys.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Next-generation digital services and consulting multinational.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "office", "service_operation"],
                    facility_locations=["Bengaluru", "Mysuru", "Mangaluru"],
                    description="Global corporate headquarters at Electronic City Bengaluru; Global Education Centre in Mysuru.",
                    evidence_source="Infosys Annual Report 2023-24 (Form 20-F / Registered Office)",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Hyderabad"],
                    description="SEZ campuses at Pocharam and Gachibowli.",
                    evidence_source="Infosys Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Thiruvananthapuram"],
                    description="Development campus at Technopark Thiruvananthapuram.",
                    evidence_source="Infosys Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Visakhapatnam"],
                    description="Development facility at Rushikonda, Visakhapatnam.",
                    evidence_source="Infosys Annual Report 2023-24",
                ),
            ],
            business_activities=["Software consulting", "Cloud services", "Digital transformation", "IT operations"],
        )
    )

    # Wipro Limited
    companies.append(
        Company(
            isin="INE075A01022",
            company_name="Wipro Limited",
            ticker_nse="WIPRO",
            ticker_bse="WIPRO",
            bse_code="507685",
            sector="Technology",
            industry="IT Services",
            sub_industry="Software Services",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=240000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://www.wipro.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Global information technology, consulting, and business process services company.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "office", "service_operation"],
                    facility_locations=["Bengaluru"],
                    description="Global corporate headquarters at Sarjapur Road, Bengaluru.",
                    evidence_source="Wipro Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Hyderabad"],
                    description="Major development centre at Gachibowli, Hyderabad.",
                    evidence_source="Wipro Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Kochi"],
                    description="Software development centre at Infopark, Kochi.",
                    evidence_source="Wipro Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["office", "service_operation"],
                    facility_locations=["Visakhapatnam"],
                    description="IT development facility in Visakhapatnam.",
                    evidence_source="Wipro Annual Report 2023-24",
                ),
            ],
            business_activities=["IT services", "Enterprise application services", "Consulting"],
        )
    )

    # Dr. Reddy's Laboratories Limited
    companies.append(
        Company(
            isin="INE089A01023",
            company_name="Dr. Reddy's Laboratories Limited",
            ticker_nse="DRREDDY",
            ticker_bse="DRREDDY",
            bse_code="500124",
            sector="Healthcare & Pharmaceuticals",
            industry="Pharmaceuticals",
            sub_industry="Formulations & APIs",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=110000.0,
            hq_state="Telangana",
            hq_city="Hyderabad",
            website="https://www.drreddys.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Global pharmaceutical company providing active ingredients, generics, biosimilars, and APIs.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["headquarters", "manufacturing", "plant", "office"],
                    facility_locations=["Hyderabad", "Bachupally", "Bollaram", "Medak"],
                    description="Global headquarters and multiple formulation and API manufacturing facilities in Hyderabad and Medak.",
                    evidence_source="Dr. Reddy's Annual Report 2023-24 (Form 20-F Plant Locations)",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Srikakulam", "Visakhapatnam"],
                    description="Major active pharmaceutical ingredient (API) manufacturing plants in Pydibhimavaram (Srikakulam) and Duvvada (Visakhapatnam SEZ).",
                    evidence_source="Dr. Reddy's Annual Report 2023-24 (Manufacturing Locations)",
                ),
            ],
            business_activities=["Pharmaceutical manufacturing", "API synthesis", "Generic drug formulation", "Clinical research"],
        )
    )

    # UltraTech Cement Limited
    companies.append(
        Company(
            isin="INE481G01011",
            company_name="Ultratech Cement Limited",
            ticker_nse="ULTRACEMCO",
            ticker_bse="ULTRACEMCO",
            bse_code="532538",
            sector="Infrastructure",
            industry="Cement & Construction Materials",
            sub_industry="Cement",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=290000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.ultratechcement.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="India's largest cement and ready-mix concrete manufacturer.",
            state_presences=[
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["manufacturing", "plant", "mining"],
                    facility_locations=["Tadipatri (Anantapur)", "Dachepalli (Palnadu)"],
                    description="Integrated cement plants at Andhra Pradesh Cement Works (Tadipatri) and Balaji Cement Works, with captive limestone mines.",
                    evidence_source="UltraTech Annual Report 2023-24 (Manufacturing Unit Footprint)",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["manufacturing", "plant", "mining"],
                    facility_locations=["Sedam (Kalaburagi)"],
                    description="Rajashree Cement Works integrated plant at Malkhed, Sedam.",
                    evidence_source="UltraTech Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Mellacheruvu (Suryapet)"],
                    description="Cement manufacturing and grinding units in Telangana.",
                    evidence_source="UltraTech Annual Report 2023-24",
                ),
            ],
            business_activities=["Cement manufacturing", "Clinker production", "Limestone mining", "Ready-mix concrete"],
        )
    )

    # JSW Steel Limited
    companies.append(
        Company(
            isin="INE019A01030",
            company_name="Jsw Steel Limited",
            ticker_nse="JSWSTEEL",
            ticker_bse="JSWSTEEL",
            bse_code="500228",
            sector="Metals & Mining",
            industry="Iron & Steel",
            sub_industry="Steel Products",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=220000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.jsw.in/steel",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading integrated steel producer in India.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["manufacturing", "plant", "power_generation", "mining"],
                    facility_locations=["Vijayanagar (Ballari)"],
                    description="Flagship integrated steel manufacturing plant with 12+ MTPA capacity at Toranagallu, Ballari, with captive power and iron ore beneficiation.",
                    evidence_source="JSW Steel Integrated Annual Report 2023-24",
                ),
            ],
            business_activities=["Steel manufacturing", "Hot rolled coils", "Cold rolling", "Captive power generation"],
        )
    )

    # NTPC Limited
    companies.append(
        Company(
            isin="INE733E01010",
            company_name="NTPC Limited",
            ticker_nse="NTPC",
            ticker_bse="NTPC",
            bse_code="532555",
            sector="Energy",
            industry="Power Generation",
            sub_industry="Thermal & Renewable Power",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=380000.0,
            hq_state="Delhi",
            hq_city="New Delhi",
            website="https://www.ntpc.co.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="India's largest power utility corporation.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["power_generation", "plant"],
                    facility_locations=["Ramagundam (Peddapalli)"],
                    description="Ramagundam Super Thermal Power Station (2,600 MW) and Telangana Super Thermal Power Project (1,600 MW).",
                    evidence_source="NTPC Annual Report 2023-24 (Installed Capacity Schedule)",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["power_generation", "plant"],
                    facility_locations=["Simhadri (Visakhapatnam)"],
                    description="Simhadri Super Thermal Power Station (2,000 MW) and solar facilities.",
                    evidence_source="NTPC Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["power_generation", "plant"],
                    facility_locations=["Kudgi (Vijayapura)"],
                    description="Kudgi Super Thermal Power Station (2,400 MW).",
                    evidence_source="NTPC Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["power_generation", "plant"],
                    facility_locations=["Kayamkulam (Alappuzha)"],
                    description="Rajiv Gandhi Combined Cycle Power Project (359 MW) and floating solar plant.",
                    evidence_source="NTPC Annual Report 2023-24",
                ),
            ],
            business_activities=["Thermal power generation", "Solar power generation", "Power utility supply"],
        )
    )

    # Tata Power Company Limited
    companies.append(
        Company(
            isin="INE245A01021",
            company_name="Tata Power Company Limited",
            ticker_nse="TATAPOWER",
            ticker_bse="TATAPOWER",
            bse_code="500400",
            sector="Energy",
            industry="Power Generation & Distribution",
            sub_industry="Renewable & Thermal Energy",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=135000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.tatapower.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Integrated power company with solar, wind, hydro, and thermal generation assets.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["power_generation", "plant", "infrastructure"],
                    facility_locations=["Pavagada (Tumakuru)", "Bengaluru"],
                    description="Solar power plants in Pavagada Solar Park; EV charging infrastructure and rooftop solar in Bengaluru.",
                    evidence_source="Tata Power Integrated Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["power_generation", "plant"],
                    facility_locations=["Ananthapuramu"],
                    description="Utility-scale solar power generation plants.",
                    evidence_source="Tata Power Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["power_generation", "infrastructure"],
                    facility_locations=["Kayamkulam", "Kochi"],
                    description="Floating solar projects and residential rooftop solar distribution.",
                    evidence_source="Tata Power Official Project Announcements",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["infrastructure", "retail"],
                    facility_locations=["Hyderabad"],
                    description="Commercial rooftop solar and EV charging infrastructure.",
                    evidence_source="Tata Power Investor Disclosures",
                ),
            ],
            business_activities=["Solar power generation", "Renewable energy", "EV charging infrastructure"],
        )
    )

    # Apollo Hospitals Enterprise Limited
    companies.append(
        Company(
            isin="INE437A01024",
            company_name="Apollo Hospitals Enterprise Limited",
            ticker_nse="APOLLOHOSP",
            ticker_bse="APOLLOHOSP",
            bse_code="508869",
            sector="Healthcare & Pharmaceuticals",
            industry="Healthcare Providers",
            sub_industry="Hospitals & Clinics",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=95000.0,
            hq_state="Tamil Nadu",
            hq_city="Chennai",
            website="https://www.apollohospitals.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading integrated healthcare services provider operating hospitals, pharmacies, and digital health clinics.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["plant", "service_operation", "retail"],
                    facility_locations=["Hyderabad (Jubilee Hills, Hyderguda, Secunderabad)"],
                    description="Major multi-specialty tertiary care hospitals, cancer centres, and pharmacy network.",
                    evidence_source="Apollo Hospitals Annual Report 2023-24 (Hospital Bed Capacity Schedule)",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["plant", "service_operation", "retail"],
                    facility_locations=["Bengaluru (Bannerghatta Road, Jayanagar, Sheshadripuram)", "Mysuru"],
                    description="Tertiary multi-specialty hospitals and pharmacy retail chain.",
                    evidence_source="Apollo Hospitals Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["plant", "service_operation", "retail"],
                    facility_locations=["Visakhapatnam", "Nellore", "Chittoor"],
                    description="Apollo Hospitals Visakhapatnam, Nellore, and Apollo Knowledge City Chittoor.",
                    evidence_source="Apollo Hospitals Annual Report 2023-24",
                ),
            ],
            business_activities=["Hospital services", "Clinical treatments", "Pharmacy retailing", "Diagnostic services"],
        )
    )

    # ITC Limited
    companies.append(
        Company(
            isin="INE154A01025",
            company_name="ITC Limited",
            ticker_nse="ITC",
            ticker_bse="ITC",
            bse_code="500875",
            sector="Consumer Goods & FMCG",
            industry="Diversified Consumer Products",
            sub_industry="FMCG & Paperboards",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=580000.0,
            hq_state="West Bengal",
            hq_city="Kolkata",
            website="https://www.itcportal.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Multi-business conglomerate spanning FMCG, Hotels, Paperboards & Packaging, and Agri-Business.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["manufacturing", "plant", "logistics"],
                    facility_locations=["Bhadrachalam", "Hyderabad"],
                    description="India's largest integrated paperboards and packaging facility at Bhadrachalam; ITC Kohenur hotel in Hyderabad.",
                    evidence_source="ITC Annual Report 2023-24 (Paperboards & Specialty Papers Division)",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["manufacturing", "plant", "supplier_relationship"],
                    facility_locations=["Chirala", "Guntur", "Rajahmundry"],
                    description="Agri-business procurement centres, leaf tobacco processing plants in Chirala and Guntur.",
                    evidence_source="ITC Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["manufacturing", "plant", "office"],
                    facility_locations=["Bengaluru", "Mysuru"],
                    description="Integrated foods manufacturing facility in Mysuru; luxury hotels in Bengaluru.",
                    evidence_source="ITC Annual Report 2023-24",
                ),
            ],
            business_activities=["Paperboard manufacturing", "Agricultural trading", "Food manufacturing", "Hotel operations"],
        )
    )

    # State Bank of India
    companies.append(
        Company(
            isin="INE062A01020",
            company_name="State Bank of India",
            ticker_nse="SBIN",
            ticker_bse="SBIN",
            bse_code="500112",
            sector="Banking & Financial Services",
            industry="Public Sector Bank",
            sub_industry="Commercial Banking",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=740000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.sbi.co.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="India's largest public sector commercial banking and financial services institution.",
            state_presences=[
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["branch", "service_operation"],
                    facility_locations=["Statewide (Amaravati Circle)"],
                    description="Over 1,400 commercial branches and administrative regional offices across Andhra Pradesh.",
                    evidence_source="SBI Annual Report 2023-24 (Circle Network Disclosures)",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["branch", "service_operation"],
                    facility_locations=["Statewide (Bengaluru Circle)"],
                    description="Extensive branch and treasury network across Karnataka.",
                    evidence_source="SBI Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["branch", "service_operation"],
                    facility_locations=["Statewide (Thiruvananthapuram Circle)"],
                    description="Over 1,200 branches across Kerala following merger with State Bank of Travancore.",
                    evidence_source="SBI Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["branch", "service_operation"],
                    facility_locations=["Statewide (Hyderabad Circle)"],
                    description="Extensive commercial banking network across all districts of Telangana.",
                    evidence_source="SBI Annual Report 2023-24",
                ),
            ],
            business_activities=["Commercial banking", "Retail lending", "Agricultural credit", "MSME finance"],
        )
    )

    # HDFC Bank Limited
    companies.append(
        Company(
            isin="INE040A01034",
            company_name="HDFC Bank Limited",
            ticker_nse="HDFCBANK",
            ticker_bse="HDFCBANK",
            bse_code="500180",
            sector="Banking & Financial Services",
            industry="Private Sector Bank",
            sub_industry="Commercial Banking",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=1250000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.hdfcbank.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="India's largest private sector bank providing comprehensive retail and wholesale banking.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["branch", "service_operation", "office"],
                    facility_locations=["Bengaluru", "Mysuru", "Hubballi", "Mangaluru"],
                    description="Over 500 retail branches and processing operations in Karnataka.",
                    evidence_source="HDFC Bank Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["branch", "service_operation"],
                    facility_locations=["Hyderabad", "Warangal", "Nizamabad"],
                    description="Over 350 branches and wholesale lending units in Telangana.",
                    evidence_source="HDFC Bank Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["branch", "service_operation"],
                    facility_locations=["Kochi", "Thiruvananthapuram", "Kozhikode"],
                    description="Over 300 commercial branches and gold loan hubs in Kerala.",
                    evidence_source="HDFC Bank Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["branch", "service_operation"],
                    facility_locations=["Visakhapatnam", "Vijayawada", "Guntur"],
                    description="Over 350 branches serving agri and commercial sectors in AP.",
                    evidence_source="HDFC Bank Annual Report 2023-24",
                ),
            ],
            business_activities=["Retail banking", "Wholesale lending", "Mortgage financing", "Vehicle financing"],
        )
    )

    # ICICI Bank Limited
    companies.append(
        Company(
            isin="INE090A01021",
            company_name="ICICI Bank Limited",
            ticker_nse="ICICIBANK",
            ticker_bse="ICICIBANK",
            bse_code="532174",
            sector="Banking & Financial Services",
            industry="Private Sector Bank",
            sub_industry="Commercial Banking",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=750000.0,
            hq_state="Gujarat",
            hq_city="Vadodara",
            website="https://www.icicibank.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading private sector bank offering diverse financial services.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["branch", "office", "service_operation"],
                    facility_locations=["Hyderabad (Financial District)"],
                    description="Major regional processing hub at Financial District Hyderabad, plus retail branch network.",
                    evidence_source="ICICI Bank Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["branch", "service_operation"],
                    facility_locations=["Bengaluru"],
                    description="Extensive branch network across urban and semi-urban Karnataka.",
                    evidence_source="ICICI Bank Annual Report 2023-24",
                ),
            ],
            business_activities=["Commercial banking", "Retail lending", "Corporate banking"],
        )
    )

    # Bharti Airtel Limited
    companies.append(
        Company(
            isin="INE397D01024",
            company_name="Bharti Airtel Limited",
            ticker_nse="BHARTIARTL",
            ticker_bse="BHARTIARTL",
            bse_code="532454",
            sector="Telecommunications",
            industry="Telecom Services",
            sub_industry="Cellular & Broadband",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=850000.0,
            hq_state="Delhi",
            hq_city="New Delhi",
            website="https://www.airtel.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading global telecommunications company with operations across India.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["infrastructure", "service_operation", "office"],
                    facility_locations=["Bengaluru"],
                    description="Karnataka telecom circle operations, mobile tower infrastructure, and broadband network.",
                    evidence_source="Bharti Airtel Annual Report 2023-24 (Circle Disclosures)",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["infrastructure", "service_operation"],
                    facility_locations=["Hyderabad"],
                    description="AP & Telangana circle wireless and fiber network operations.",
                    evidence_source="Bharti Airtel Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["infrastructure", "service_operation"],
                    facility_locations=["Visakhapatnam", "Vijayawada"],
                    description="Statewide 5G and fiber network infrastructure.",
                    evidence_source="Bharti Airtel Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["infrastructure", "service_operation"],
                    facility_locations=["Kochi"],
                    description="Kerala circle operations and submarine cable landing station.",
                    evidence_source="Bharti Airtel Annual Report 2023-24",
                ),
            ],
            business_activities=["Wireless telecommunications", "Broadband internet", "Enterprise data services"],
        )
    )

    # Larsen & Toubro Limited
    companies.append(
        Company(
            isin="INE018A01030",
            company_name="Larsen & Toubro Limited",
            ticker_nse="LT",
            ticker_bse="LT",
            bse_code="500510",
            sector="Infrastructure",
            industry="Engineering & Construction",
            sub_industry="Civil & Heavy Engineering",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=490000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.larsentoubro.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Major engineering, procurement, and construction conglomerate.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["project", "infrastructure", "office"],
                    facility_locations=["Hyderabad"],
                    description="Concessionaire and builder of Hyderabad Metro Rail (L&T Metro Rail Hyderabad Limited); major engineering projects.",
                    evidence_source="L&T Annual Report 2023-24 (Development Projects / Metro Concession)",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["manufacturing", "project", "office"],
                    facility_locations=["Bengaluru", "Mysuru"],
                    description="Heavy engineering units in Bengaluru; Bengaluru Metro (Namma Metro) and suburban rail construction packages.",
                    evidence_source="L&T Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["project", "infrastructure"],
                    facility_locations=["Amaravati", "Visakhapatnam"],
                    description="Government complex buildings in Amaravati, irrigation pumping and water supply projects.",
                    evidence_source="L&T Annual Report 2023-24",
                ),
            ],
            business_activities=["EPC contracting", "Metro rail transit operation", "Heavy civil construction"],
        )
    )

    # Britannia Industries Limited
    companies.append(
        Company(
            isin="INE216A01030",
            company_name="Britannia Industries Limited",
            ticker_nse="BRITANNIA",
            ticker_bse="BRITANNIA",
            bse_code="500825",
            sector="Consumer Goods & FMCG",
            industry="Food Products",
            sub_industry="Bakery & Dairy",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=125000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://www.britannia.co.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="India's leading food and bakery company.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "manufacturing", "office"],
                    facility_locations=["Bengaluru", "Bidadi (Ramanagara)"],
                    description="Executive corporate headquarters and major R&D and manufacturing facility in Bidadi.",
                    evidence_source="Britannia Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Chittoor"],
                    description="Food processing and manufacturing unit in Chittoor district.",
                    evidence_source="Britannia Annual Report 2023-24",
                ),
            ],
            business_activities=["Bakery manufacturing", "Food processing", "Dairy distribution"],
        )
    )

    # Abb India Limited
    companies.append(
        Company(
            isin="INE117A01022",
            company_name="Abb India Limited",
            ticker_nse="ABB",
            ticker_bse="ABB",
            bse_code="500002",
            sector="Manufacturing",
            industry="Electrical Equipment",
            sub_industry="Power Equipment & Automation",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=160000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://new.abb.com/in",
            listing_status="Listed",
            exchange="NSE",
            business_description="Pioneering technology leader in electrification, automation, and robotics.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "manufacturing", "plant", "office"],
                    facility_locations=["Bengaluru (Peenya, Nelamangala)"],
                    description="Corporate headquarters and major manufacturing plants in Peenya Industrial Area and Nelamangala.",
                    evidence_source="ABB India Annual Report 2023 (Manufacturing Units Schedule)",
                ),
            ],
            business_activities=["Switchgear manufacturing", "Industrial automation", "Transformers"],
        )
    )

    # --------------------------------------------------------------------------
    # 2. STATE-SPECIFIC CURATED LISTED COMPANIES
    # --------------------------------------------------------------------------

    # Zomato Limited (Platform Aggregator / Gig Economy)
    companies.append(
        Company(
            isin="INE758T01015",
            company_name="Zomato Limited",
            ticker_nse="ZOMATO",
            ticker_bse="ZOMATO",
            bse_code="543320",
            sector="Labour & Employment",
            industry="Internet & E-Commerce",
            sub_industry="Online Food Delivery & Quick Commerce",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=210000.0,
            hq_state="Haryana",
            hq_city="Gurugram",
            website="https://www.zomato.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading online platform aggregator connecting consumers, restaurant partners, and gig delivery partners across India.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["service_operation", "logistics", "office"],
                    facility_locations=["Hyderabad", "Warangal", "Karimnagar"],
                    description="Extensive app-based delivery operations, dark stores (Blinkit), and thousands of active platform gig delivery workers.",
                    evidence_source="Zomato Annual Report 2023-24 (Operational Footprint & Delivery Network)",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["service_operation", "logistics", "office"],
                    facility_locations=["Bengaluru", "Mysuru", "Mangaluru"],
                    description="Extensive platform delivery operations, quick-commerce fulfillment hubs, and regional operations.",
                    evidence_source="Zomato Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["service_operation", "logistics"],
                    facility_locations=["Kochi", "Thiruvananthapuram", "Kozhikode"],
                    description="Food delivery aggregator network across Kerala municipal cities.",
                    evidence_source="Zomato Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["service_operation", "logistics"],
                    facility_locations=["Visakhapatnam", "Vijayawada", "Guntur", "Tirupati"],
                    description="App-based platform delivery network operating across AP urban centres.",
                    evidence_source="Zomato Annual Report 2023-24",
                ),
            ],
            business_activities=["Online food delivery", "Platform work aggregation", "Quick-commerce logistics", "Welfare cess remittance"],
        )
    )

    # Swiggy Limited (Platform Aggregator / Gig Economy)
    companies.append(
        Company(
            isin="INE00H001014",
            company_name="Swiggy Limited",
            ticker_nse="SWIGGY",
            ticker_bse="SWIGGY",
            bse_code="544280",
            sector="Labour & Employment",
            industry="Internet & E-Commerce",
            sub_industry="Food Delivery & Hyperlocal Logistics",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=98000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://www.swiggy.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Consumer tech platform aggregating on-demand food delivery, dining out, and grocery delivery through gig delivery partners.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "service_operation", "logistics", "office"],
                    facility_locations=["Bengaluru", "Mysuru", "Hubballi"],
                    description="Registered corporate headquarters in Bengaluru; vast network of gig delivery partners and Instamart pods.",
                    evidence_source="Swiggy Limited IPO Prospectus (DRHP) / Annual Filings",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["service_operation", "logistics", "office"],
                    facility_locations=["Hyderabad", "Secunderabad"],
                    description="Major food delivery, Instamart dark stores, and platform worker fleet in Hyderabad.",
                    evidence_source="Swiggy DRHP Operational Metrics",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["service_operation", "logistics"],
                    facility_locations=["Kochi", "Thiruvananthapuram", "Kozhikode"],
                    description="Delivery aggregator operations across Kerala urban areas.",
                    evidence_source="Swiggy DRHP",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["service_operation", "logistics"],
                    facility_locations=["Visakhapatnam", "Vijayawada", "Guntur"],
                    description="App-based platform delivery operations across AP.",
                    evidence_source="Swiggy DRHP",
                ),
            ],
            business_activities=["Food ordering aggregation", "Gig delivery operations", "Hyperlocal quick commerce"],
        )
    )

    # Divi's Laboratories Limited (Pharma Manufacturing / APIs)
    companies.append(
        Company(
            isin="INE361B01024",
            company_name="Divi's Laboratories Limited",
            ticker_nse="DIVISLAB",
            ticker_bse="DIVISLAB",
            bse_code="532488",
            sector="Healthcare & Pharmaceuticals",
            industry="Pharmaceuticals",
            sub_industry="Active Pharmaceutical Ingredients (APIs)",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=115000.0,
            hq_state="Telangana",
            hq_city="Hyderabad",
            website="https://www.divislabs.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading global manufacturer of active pharmaceutical ingredients (APIs) and custom synthesis.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["headquarters", "manufacturing", "plant", "office"],
                    facility_locations=["Hyderabad", "Choutuppal (Yadadri Bhuvanagiri)"],
                    description="Corporate headquarters in Hyderabad and major API Manufacturing Unit 1 at Lingojigudem, Choutuppal.",
                    evidence_source="Divi's Laboratories Annual Report 2023-24 (Manufacturing Facilities)",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Chippada (Visakhapatnam)"],
                    description="Major export-oriented API Manufacturing Unit 2 at Chippada, Bheemunipatnam mandal, Visakhapatnam.",
                    evidence_source="Divi's Laboratories Annual Report 2023-24 (Unit 2 Disclosures)",
                ),
            ],
            business_activities=["Active pharmaceutical ingredients", "Custom synthesis", "Nutraceutical ingredients", "Chemical synthesis"],
        )
    )

    # Aurobindo Pharma Limited (Pharma Manufacturing)
    companies.append(
        Company(
            isin="INE406A01037",
            company_name="Aurobindo Pharma Limited",
            ticker_nse="AUROPHARMA",
            ticker_bse="AUROPHARMA",
            bse_code="524804",
            sector="Healthcare & Pharmaceuticals",
            industry="Pharmaceuticals",
            sub_industry="Generic Formulations & APIs",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=68000.0,
            hq_state="Telangana",
            hq_city="Hyderabad",
            website="https://www.aurobindo.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Vertically integrated pharmaceutical manufacturing company.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["headquarters", "manufacturing", "plant"],
                    facility_locations=["Hyderabad (HITEC City)", "Pashamylaram", "Jedcherla"],
                    description="Global headquarters and multiple formulation/injectable manufacturing plants in Pashamylaram and Mahbubnagar.",
                    evidence_source="Aurobindo Pharma Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Pydibhimavaram (Srikakulam)", "Visakhapatnam"],
                    description="Large-scale API synthesis facilities at Pydibhimavaram and SEZ plants in Visakhapatnam.",
                    evidence_source="Aurobindo Pharma Annual Report 2023-24",
                ),
            ],
            business_activities=["Generic formulation", "API synthesis", "Injectables manufacturing"],
        )
    )

    # Amara Raja Energy & Mobility Limited (Industrial Batteries / Manufacturing)
    companies.append(
        Company(
            isin="INE885A01032",
            company_name="Amara Raja Energy & Mobility Limited",
            ticker_nse="ARE&M",
            ticker_bse="ARE&M",
            bse_code="500008",
            sector="Manufacturing",
            industry="Auto Components",
            sub_industry="Lead-Acid & Lithium-Ion Batteries",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=24000.0,
            hq_state="Andhra Pradesh",
            hq_city="Tirupati",
            website="https://www.amararaja.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading manufacturer of lead-acid and advanced lithium-ion energy storage products (Amaron).",
            state_presences=[
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["headquarters", "manufacturing", "plant"],
                    facility_locations=["Tirupati", "Karakambadi", "Nunegundlapalli (Chittoor)"],
                    description="Corporate headquarters and major integrated battery manufacturing complexes in Tirupati and Chittoor.",
                    evidence_source="Amara Raja Annual Report 2023-24 (Operational Plants Schedule)",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["plant", "infrastructure", "project"],
                    facility_locations=["Divitipally (Mahbubnagar)", "Hyderabad"],
                    description="Lithium-ion Gigafactory and E-Positive Energy Labs project at Divitipally.",
                    evidence_source="Amara Raja Official Project Disclosures & Stock Exchange Filings",
                ),
            ],
            business_activities=["Automotive battery manufacturing", "Industrial battery manufacturing", "Lithium-ion cell manufacturing"],
        )
    )

    # Cochin Shipyard Limited (Maritime & Shipbuilding / Public-Sector)
    companies.append(
        Company(
            isin="INE704P01017",
            company_name="Cochin Shipyard Limited",
            ticker_nse="COCHINSHIP",
            ticker_bse="COCHINSHIP",
            bse_code="540678",
            sector="Ports & Maritime",
            industry="Shipbuilding & Marine Engineering",
            sub_industry="Defense & Commercial Vessels",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=46000.0,
            hq_state="Kerala",
            hq_city="Kochi",
            website="https://www.cochinshipyard.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="Premier shipbuilding, ship repair, and marine engineering enterprise under Government of India.",
            state_presences=[
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["headquarters", "manufacturing", "plant", "infrastructure"],
                    facility_locations=["Kochi"],
                    description="Premier shipbuilding yard, international ship repair facility (ISRF), and dry docks at Willingdon Island, Kochi.",
                    evidence_source="Cochin Shipyard Annual Report 2023-24 (Facilities Footprint)",
                ),
            ],
            business_activities=["Shipbuilding", "Ship repair", "Marine defense vessel manufacturing", "Water metro vessel construction"],
        )
    )

    # Federal Bank Limited (Private Banking / Kerala-centric)
    companies.append(
        Company(
            isin="INE171A01029",
            company_name="Federal Bank Limited",
            ticker_nse="FEDERALBNK",
            ticker_bse="FEDERALBNK",
            bse_code="500469",
            sector="Banking & Financial Services",
            industry="Private Sector Bank",
            sub_industry="Commercial Banking",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=48000.0,
            hq_state="Kerala",
            hq_city="Aluva",
            website="https://www.federalbank.co.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="Major private commercial bank headquartered in Kerala with extensive pan-India branches.",
            state_presences=[
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["headquarters", "branch", "office", "service_operation"],
                    facility_locations=["Aluva (Ernakulam)", "Statewide"],
                    description="Registered office and corporate centre in Aluva; dominant branch network of over 600 branches across Kerala.",
                    evidence_source="Federal Bank Annual Report 2023-24 (Branch Distribution)",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["branch", "service_operation"],
                    facility_locations=["Bengaluru", "Mangaluru"],
                    description="Commercial and retail branches in Karnataka.",
                    evidence_source="Federal Bank Annual Report 2023-24",
                ),
            ],
            business_activities=["Commercial banking", "NRI remittances", "MSME lending", "Gold loans"],
        )
    )

    # Muthoot Finance Limited (Gold Loans / NBFC)
    companies.append(
        Company(
            isin="INE414G01012",
            company_name="Muthoot Finance Limited",
            ticker_nse="MUTHOOTFIN",
            ticker_bse="MUTHOOTFIN",
            bse_code="533398",
            sector="Banking & Financial Services",
            industry="Non-Banking Financial Company (NBFC)",
            sub_industry="Gold Loans",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=75000.0,
            hq_state="Kerala",
            hq_city="Kochi",
            website="https://www.muthootfinance.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="India's largest gold financing company by loan portfolio.",
            state_presences=[
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["headquarters", "branch", "office"],
                    facility_locations=["Kochi", "Statewide"],
                    description="Registered headquarters in Kochi; extensive branch network throughout Kerala.",
                    evidence_source="Muthoot Finance Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["branch"],
                    facility_locations=["Bengaluru", "Statewide"],
                    description="Over 400 branches in Karnataka.",
                    evidence_source="Muthoot Finance Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["branch"],
                    facility_locations=["Hyderabad", "Statewide"],
                    description="Over 350 branches in Telangana.",
                    evidence_source="Muthoot Finance Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["branch"],
                    facility_locations=["Visakhapatnam", "Vijayawada", "Statewide"],
                    description="Over 450 branches in Andhra Pradesh.",
                    evidence_source="Muthoot Finance Annual Report 2023-24",
                ),
            ],
            business_activities=["Gold loans", "Microfinance", "Foreign exchange", "Money transfer"],
        )
    )

    # Manappuram Finance Limited (NBFC / Kerala-centric)
    companies.append(
        Company(
            isin="INE522D01027",
            company_name="Manappuram Finance Limited",
            ticker_nse="MANAPPURAM",
            ticker_bse="MANAPPURAM",
            bse_code="531213",
            sector="Banking & Financial Services",
            industry="Non-Banking Financial Company (NBFC)",
            sub_industry="Gold Loans & Vehicle Finance",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=16000.0,
            hq_state="Kerala",
            hq_city="Valapad",
            website="https://www.manappuram.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading non-banking financial company specializing in gold loans and microfinance.",
            state_presences=[
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["headquarters", "branch", "office"],
                    facility_locations=["Valapad (Thrissur)", "Statewide"],
                    description="Corporate head office in Valapad, Thrissur; extensive network across Kerala.",
                    evidence_source="Manappuram Finance Annual Report 2023-24",
                ),
            ],
            business_activities=["Gold loans", "Vehicle loans", "MSME finance"],
        )
    )

    # Sobha Limited (Real Estate & Urban Development)
    companies.append(
        Company(
            isin="INE671H01015",
            company_name="Sobha Limited",
            ticker_nse="SOBHA",
            ticker_bse="SOBHA",
            bse_code="532784",
            sector="Real Estate",
            industry="Real Estate Development",
            sub_industry="Residential & Commercial Projects",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=17000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://www.sobha.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading residential and contractual real estate developer in India.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "project", "manufacturing", "office"],
                    facility_locations=["Bengaluru"],
                    description="Corporate headquarters and flagship residential developments and manufacturing units (glazing, interiors) in Bengaluru.",
                    evidence_source="Sobha Limited Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["project", "office"],
                    facility_locations=["Kochi", "Thrissur", "Kozhikode", "Thiruvananthapuram"],
                    description="Extensive residential township and apartment projects across Kerala.",
                    evidence_source="Sobha Limited Annual Report 2023-24",
                ),
            ],
            business_activities=["Residential property development", "Contractual civil construction", "Urban real estate"],
        )
    )

    # Prestige Estates Projects Limited (Real Estate & Municipal Governance)
    companies.append(
        Company(
            isin="INE811K01011",
            company_name="Prestige Estates Projects Limited",
            ticker_nse="PRESTIGE",
            ticker_bse="PRESTIGE",
            bse_code="533274",
            sector="Real Estate",
            industry="Real Estate Development",
            sub_industry="Commercial & Residential Projects",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=65000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://www.prestigeconstructions.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading real estate developer spanning residential, commercial office, retail malls, and hospitality.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "project", "retail", "office"],
                    facility_locations=["Bengaluru"],
                    description="Corporate headquarters in Bengaluru; vast portfolio of tech parks, luxury malls, and residential communities.",
                    evidence_source="Prestige Estates Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["project", "office"],
                    facility_locations=["Hyderabad"],
                    description="Major commercial IT parks and residential projects in Hyderabad.",
                    evidence_source="Prestige Estates Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["project", "retail"],
                    facility_locations=["Kochi", "Kozhikode"],
                    description="Forum Mall Kochi and residential projects.",
                    evidence_source="Prestige Estates Annual Report 2023-24",
                ),
            ],
            business_activities=["Commercial real estate development", "Residential property construction", "Mall operations"],
        )
    )

    # Biocon Limited (Biopharmaceuticals)
    companies.append(
        Company(
            isin="INE376G01013",
            company_name="Biocon Limited",
            ticker_nse="BIOCON",
            ticker_bse="BIOCON",
            bse_code="532523",
            sector="Healthcare & Pharmaceuticals",
            industry="Biotechnology",
            sub_industry="Biopharmaceuticals & Biosimilars",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=42000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://www.biocon.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Global biopharmaceutical company focused on diabetes, oncology, and immunology biosimilars.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "manufacturing", "plant", "office"],
                    facility_locations=["Bengaluru (Electronic City, Jigani)"],
                    description="Corporate headquarters and integrated biologics manufacturing and R&D campuses at Biocon Park, Bengaluru.",
                    evidence_source="Biocon Integrated Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Visakhapatnam"],
                    description="API manufacturing facility at Jawaharlal Nehru Pharma City, Visakhapatnam.",
                    evidence_source="Biocon Integrated Annual Report 2023-24",
                ),
            ],
            business_activities=["Biopharmaceutical manufacturing", "Insulin production", "Biosimilar development"],
        )
    )

    # Aster DM Healthcare Limited (Healthcare & Clinical Establishments)
    companies.append(
        Company(
            isin="INE914M01019",
            company_name="Aster DM Healthcare Limited",
            ticker_nse="ASTERDM",
            ticker_bse="ASTERDM",
            bse_code="540975",
            sector="Healthcare",
            industry="Healthcare Providers",
            sub_industry="Hospitals & Clinics",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=22000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://www.asterdmhealthcare.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Integrated healthcare network operating hospitals, clinics, and diagnostic centres.",
            state_presences=[
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["plant", "service_operation"],
                    facility_locations=["Kochi (Aster Medcity)", "Kozhikode (Aster MIMS)", "Kottakkal", "Wayanad", "Kannur"],
                    description="Major multi-specialty tertiary quaternary care hospitals including Aster Medcity Kochi and Aster MIMS network.",
                    evidence_source="Aster DM Healthcare Annual Report 2023-24 (Hospital Facilities Schedule)",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "plant", "service_operation"],
                    facility_locations=["Bengaluru (Hebbal, Whitefield)"],
                    description="Corporate administrative headquarters and multi-specialty hospitals in Bengaluru.",
                    evidence_source="Aster DM Healthcare Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["plant", "service_operation"],
                    facility_locations=["Tirupati"],
                    description="Multi-specialty hospital in Tirupati.",
                    evidence_source="Aster DM Healthcare Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["service_operation"],
                    facility_locations=["Hyderabad"],
                    description="Aster Prime Hospital at Ameerpet, Hyderabad.",
                    evidence_source="Aster DM Healthcare Annual Report 2023-24",
                ),
            ],
            business_activities=["Hospital clinical operations", "Tertiary medical care", "Diagnostic laboratories"],
        )
    )

    # Apex Frozen Foods Limited (Aquaculture / AP-centric)
    companies.append(
        Company(
            isin="INE346W01013",
            company_name="Apex Frozen Foods Limited",
            ticker_nse="APEX",
            ticker_bse="APEX",
            bse_code="540692",
            sector="Fisheries",
            industry="Aquaculture & Processing",
            sub_industry="Shrimp Farming & Exports",
            market_cap_category=MarketCapCategory.SMALL_CAP,
            market_cap_cr=750.0,
            hq_state="Andhra Pradesh",
            hq_city="Kakinada",
            website="https://www.apexfrozenfoods.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="Integrated producer and exporter of processed aquaculture shrimp products.",
            state_presences=[
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["headquarters", "manufacturing", "plant", "supplier_relationship"],
                    facility_locations=["Kakinada", "Raparru (Kakinada district)"],
                    description="Corporate headquarters, shrimp processing facilities, hatcheries, and farmer procurement networks in coastal AP.",
                    evidence_source="Apex Frozen Foods Annual Report 2023-24 (Operations Review)",
                ),
            ],
            business_activities=["Aquaculture shrimp processing", "Hatchery operations", "Seafood export", "Farmer feed distribution"],
        )
    )

    # Avanti Feeds Limited (Aquaculture Feeds & Processing / AP-centric)
    companies.append(
        Company(
            isin="INE731F01041",
            company_name="Avanti Feeds Limited",
            ticker_nse="AVANTIFEED",
            ticker_bse="AVANTIFEED",
            bse_code="512573",
            sector="Fisheries",
            industry="Aquaculture",
            sub_industry="Shrimp Feed & Processing",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=8500.0,
            hq_state="Andhra Pradesh",
            hq_city="Visakhapatnam",
            website="https://www.avantifeeds.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading manufacturer of shrimp feeds and processor/exporter of value-added shrimp products.",
            state_presences=[
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["headquarters", "manufacturing", "plant"],
                    facility_locations=["Kovvur (West Godavari)", "Vemuluru", "Visakhapatnam"],
                    description="Shrimp feed manufacturing plants at Kovvur and Vemuluru; processing and cold storage facilities in AP.",
                    evidence_source="Avanti Feeds Annual Report 2023-24 (Manufacturing Locations)",
                ),
            ],
            business_activities=["Shrimp feed manufacturing", "Aquaculture processing", "Hatchery feed supply"],
        )
    )

    # KNR Constructions Limited (Infrastructure / Telangana & AP)
    companies.append(
        Company(
            isin="INE634I01029",
            company_name="KNR Constructions Limited",
            ticker_nse="KNRCON",
            ticker_bse="KNRCON",
            bse_code="532942",
            sector="Infrastructure",
            industry="Construction",
            sub_industry="Highways & Irrigation",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=8800.0,
            hq_state="Telangana",
            hq_city="Hyderabad",
            website="https://www.knrcl.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Infrastructure project development company with expertise in roads, highways, and irrigation projects.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["headquarters", "project", "office"],
                    facility_locations=["Hyderabad"],
                    description="Corporate headquarters; major highway and irrigation canal construction projects in Telangana.",
                    evidence_source="KNR Constructions Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["project"],
                    facility_locations=["Statewide"],
                    description="State highway and expressway construction packages.",
                    evidence_source="KNR Constructions Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["project"],
                    facility_locations=["Bengaluru", "Statewide"],
                    description="Highway expansion and road development projects.",
                    evidence_source="KNR Constructions Annual Report 2023-24",
                ),
            ],
            business_activities=["Road and highway construction", "Irrigation civil works", "Flyover and bridge engineering"],
        )
    )

    # NCC Limited (Infrastructure / AP & Telangana)
    companies.append(
        Company(
            isin="INE868B01028",
            company_name="NCC Limited",
            ticker_nse="NCC",
            ticker_bse="NCC",
            bse_code="500294",
            sector="Infrastructure",
            industry="Construction",
            sub_industry="Civil Infrastructure & Buildings",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=19000.0,
            hq_state="Telangana",
            hq_city="Hyderabad",
            website="https://www.ncclimited.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Major construction and infrastructure development conglomerate.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["headquarters", "project", "office"],
                    facility_locations=["Hyderabad (Madhapur)"],
                    description="Corporate headquarters and ongoing urban infrastructure, water supply, and housing contracts.",
                    evidence_source="NCC Limited Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["project"],
                    facility_locations=["Visakhapatnam", "Amaravati"],
                    description="Government building construction and municipal water pipelines.",
                    evidence_source="NCC Limited Annual Report 2023-24",
                ),
            ],
            business_activities=["Civil construction", "Water pipelines", "Roads and bridges", "Electrical grid contracting"],
        )
    )

    # Page Industries Limited (Apparel Manufacturing / Karnataka)
    companies.append(
        Company(
            isin="INE761H01023",
            company_name="Page Industries Limited",
            ticker_nse="PAGEIND",
            ticker_bse="PAGEIND",
            bse_code="532827",
            sector="Textiles",
            industry="Textiles & Apparel",
            sub_industry="Innerwear & Leisurewear",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=51000.0,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://www.pageind.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Exclusive licensee of Jockey International in India, operating extensive garment manufacturing plants.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "manufacturing", "plant", "office"],
                    facility_locations=["Bengaluru", "Hassan", "Mysuru", "Tiptur"],
                    description="Corporate headquarters in Bengaluru; multiple integrated garment manufacturing facilities employing thousands of workers in Hassan and Bengaluru.",
                    evidence_source="Page Industries Annual Report 2023-24 (Manufacturing Locations Schedule)",
                ),
            ],
            business_activities=["Garment manufacturing", "Textile stitching", "Apparel retail distribution"],
        )
    )

    # Mahindra & Mahindra Limited (Automotive & Manufacturing)
    companies.append(
        Company(
            isin="INE101A01026",
            company_name="Mahindra & Mahindra Limited",
            ticker_nse="M&M",
            ticker_bse="M&M",
            bse_code="500520",
            sector="Manufacturing",
            industry="Automobiles",
            sub_industry="Commercial Vehicles & Tractors",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=350000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.mahindra.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Global leader in utility vehicles, commercial vehicles, and agricultural tractors.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Zaheerabad (Sangareddy)"],
                    description="Major automotive and tractor manufacturing plant in Zaheerabad producing commercial vehicles and electric 3-wheelers.",
                    evidence_source="M&M Integrated Annual Report 2023-24 (Manufacturing Locations)",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["office", "service_operation", "retail"],
                    facility_locations=["Bengaluru"],
                    description="Mahindra Electric Mobility design centre and state dealership network.",
                    evidence_source="M&M Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["retail", "service_operation"],
                    facility_locations=["Vijayawada", "Visakhapatnam"],
                    description="Commercial vehicle dealership networks and logistics depots.",
                    evidence_source="M&M Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["retail", "service_operation"],
                    facility_locations=["Kochi", "Kozhikode"],
                    description="Passenger and commercial vehicle distribution and service network.",
                    evidence_source="M&M Annual Report 2023-24",
                ),
            ],
            business_activities=["Commercial vehicle manufacturing", "Tractor assembly", "Automotive retailing", "Fleet distribution"],
        )
    )

    # Tata Motors Limited (Automotive & Transport Fleets)
    companies.append(
        Company(
            isin="INE155A01022",
            company_name="Tata Motors Limited",
            ticker_nse="TATAMOTORS",
            ticker_bse="TATAMOTORS",
            bse_code="500570",
            sector="Manufacturing",
            industry="Automobiles",
            sub_industry="Commercial Vehicles & Passenger Cars",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=340000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.tatamotors.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading global automobile manufacturer producing commercial vehicles, buses, trucks, and passenger cars.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["manufacturing", "plant", "service_operation"],
                    facility_locations=["Dharwad", "Bengaluru"],
                    description="Small commercial vehicle (Tata Ace) manufacturing plant at Dharwad; major EV bus supply to Bengaluru Metropolitan Transport Corporation (BMTC).",
                    evidence_source="Tata Motors Annual Report 2023-24 (Plant Footprint)",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["retail", "service_operation", "project"],
                    facility_locations=["Hyderabad"],
                    description="Commercial vehicle dealerships and electric transit bus supply contracts.",
                    evidence_source="Tata Motors Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["retail", "service_operation"],
                    facility_locations=["Vijayawada", "Visakhapatnam"],
                    description="Commercial freight truck distribution and authorized workshop facilities.",
                    evidence_source="Tata Motors Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["retail", "service_operation"],
                    facility_locations=["Kochi", "Thiruvananthapuram"],
                    description="Passenger vehicle dealerships and KSRTC bus chassis maintenance.",
                    evidence_source="Tata Motors Annual Report 2023-24",
                ),
            ],
            business_activities=["Commercial vehicle assembly", "Chassis fabrication", "Bus transit supply", "Fleet servicing"],
        )
    )

    # Hindustan Unilever Limited (Consumer Goods & FMCG)
    companies.append(
        Company(
            isin="INE030A01027",
            company_name="Hindustan Unilever Limited",
            ticker_nse="HINDUNILVR",
            ticker_bse="HINDUNILVR",
            bse_code="500696",
            sector="Consumer Goods & FMCG",
            industry="Diversified FMCG",
            sub_industry="Home & Personal Care, Foods",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=600000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.hul.co.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="India's largest fast-moving consumer goods company with vast distribution and manufacturing.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["manufacturing", "plant", "logistics"],
                    facility_locations=["Khammam"],
                    description="Personal care manufacturing facility at Bhadrachalam Road, Khammam district.",
                    evidence_source="HUL Annual Report 2023-24 (Supply Chain & Factory Footprint)",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["manufacturing", "plant", "office"],
                    facility_locations=["Mysuru", "Bengaluru"],
                    description="Beverages and foods manufacturing at Mysuru; regional business operations in Bengaluru.",
                    evidence_source="HUL Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["logistics", "retail"],
                    facility_locations=["Vijayawada", "Visakhapatnam"],
                    description="Depots and redistribution logistics networks across coastal and Rayalaseema AP.",
                    evidence_source="HUL Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["manufacturing", "logistics"],
                    facility_locations=["Kochi"],
                    description="Factory operations and FMCG redistribution depots.",
                    evidence_source="HUL Annual Report 2023-24",
                ),
            ],
            business_activities=["Personal care manufacturing", "FMCG supply chain", "Packaged foods distribution"],
        )
    )

    # Nestle India Limited (FMCG / Food Processing)
    companies.append(
        Company(
            isin="INE239A01016",
            company_name="Nestle India Limited",
            ticker_nse="NESTLEIND",
            ticker_bse="NESTLEIND",
            bse_code="500790",
            sector="Consumer Goods & FMCG",
            industry="Food Products",
            sub_industry="Packaged Foods & Confectionery",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=240000.0,
            hq_state="Haryana",
            hq_city="Gurugram",
            website="https://www.nestle.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading food and beverage manufacturing company.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Nanjangud (Mysuru)"],
                    description="Major manufacturing facility at Nanjangud Industrial Area, Mysuru producing coffee, noodles, and infant nutrition.",
                    evidence_source="Nestlé India Annual Report 2023 (Manufacturing Facilities Schedule)",
                ),
            ],
            business_activities=["Food processing", "Coffee extraction", "Culinary products manufacturing"],
        )
    )

    # Asian Paints Limited (Manufacturing / Consumer Goods)
    companies.append(
        Company(
            isin="INE021A01026",
            company_name="Asian Paints Limited",
            ticker_nse="ASIANPAINT",
            ticker_bse="ASIANPAINT",
            bse_code="500820",
            sector="Consumer Goods & FMCG",
            industry="Consumer Durables",
            sub_industry="Paints & Coatings",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=280000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.asianpaints.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="India's leading paint and coatings manufacturer.",
            state_presences=[
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Visakhapatnam"],
                    description="Mega decorative paints manufacturing facility at Pudi, Rambilli mandal, Visakhapatnam district.",
                    evidence_source="Asian Paints Annual Report 2023-24 (Manufacturing Locations)",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Patancheru (Sangareddy)"],
                    description="Paints manufacturing unit at Patancheru Industrial Estate.",
                    evidence_source="Asian Paints Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["plant", "retail", "logistics"],
                    facility_locations=["Bengaluru", "Mysuru"],
                    description="Regional distribution centres and Color Idea decor stores.",
                    evidence_source="Asian Paints Annual Report 2023-24",
                ),
            ],
            business_activities=["Paint manufacturing", "Industrial coatings production", "Chemical processing"],
        )
    )

    # Hindalco Industries Limited (Metals & Mining)
    companies.append(
        Company(
            isin="INE038A01020",
            company_name="Hindalco Industries Limited",
            ticker_nse="HINDALCO",
            ticker_bse="HINDALCO",
            bse_code="500440",
            sector="Metals & Mining",
            industry="Non-Ferrous Metals",
            sub_industry="Aluminium & Copper",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=150000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.hindalco.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading global aluminum and copper manufacturing company of Aditya Birla Group.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["manufacturing", "plant"],
                    facility_locations=["Belagavi"],
                    description="Alumina plant and major research & development centre in Belagavi (Belgaum).",
                    evidence_source="Hindalco Annual Report 2023-24 (Operational Plants Schedule)",
                ),
            ],
            business_activities=["Alumina refining", "Specialty chemicals", "Metallurgical R&D"],
        )
    )

    # Cipla Limited (Pharmaceuticals)
    companies.append(
        Company(
            isin="INE059A01026",
            company_name="Cipla Limited",
            ticker_nse="CIPLA",
            ticker_bse="CIPLA",
            bse_code="500087",
            sector="Healthcare & Pharmaceuticals",
            industry="Pharmaceuticals",
            sub_industry="Respiratory & Generic Formulations",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=120000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.cipla.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="Global pharmaceutical company specialized in respiratory therapies, anti-retrovirals, and generics.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["manufacturing", "plant", "office"],
                    facility_locations=["Bengaluru (Virgonagar, Bommasandra)"],
                    description="Formulation and R&D manufacturing units at Virgonagar and Bommasandra Industrial Area, Bengaluru.",
                    evidence_source="Cipla Integrated Annual Report 2023-24 (Manufacturing Locations)",
                ),
            ],
            business_activities=["Inhalation formulation manufacturing", "Generic pharmaceutical production", "Tablets and capsules packaging"],
        )
    )

    # GMR Airports Infrastructure Limited (Infrastructure / Aviation)
    companies.append(
        Company(
            isin="INE976G01028",
            company_name="GMR Airports Infrastructure Limited",
            ticker_nse="GMRINFRA",
            ticker_bse="GMRINFRA",
            bse_code="532754",
            sector="Infrastructure",
            industry="Airport Infrastructure & Operations",
            sub_industry="Aviation Utilities",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=68000.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.gmrgroup.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="Leading airport operator and infrastructure company.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["infrastructure", "project", "service_operation"],
                    facility_locations=["Hyderabad (Shamshabad)"],
                    description="Concessionaire and operator of Rajiv Gandhi International Airport (GMR Hyderabad International Airport Limited - GHIAL).",
                    evidence_source="GMR Airports Annual Report 2023-24 (Airport Assets Footprint)",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["infrastructure", "project"],
                    facility_locations=["Bhogapuram (Vizianagaram)"],
                    description="Developer and concessionaire for the greenfield Bhogapuram International Airport near Visakhapatnam.",
                    evidence_source="GMR Official Regulatory & Stock Exchange Disclosures",
                ),
            ],
            business_activities=["Airport management", "Terminal operations", "Aeronautical commercial services", "Cargo handling"],
        )
    )

    # Container Corporation of India Limited (Logistics & Rail Freight / PSU)
    companies.append(
        Company(
            isin="INE111A01025",
            company_name="Container Corporation of India Limited",
            ticker_nse="CONCOR",
            ticker_bse="CONCOR",
            bse_code="531349",
            sector="Logistics",
            industry="Logistics & Rail Freight",
            sub_industry="Multimodal Transportation",
            market_cap_category=MarketCapCategory.LARGE_CAP,
            market_cap_cr=55000.0,
            hq_state="Delhi",
            hq_city="New Delhi",
            website="https://concor.co.in",
            listing_status="Listed",
            exchange="NSE",
            business_description="Navratna CPSE under Ministry of Railways operating multi-modal logistics terminals and container freight stations.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["infrastructure", "logistics"],
                    facility_locations=["Bengaluru (Whitefield)"],
                    description="Inland Container Depot (ICD) Whitefield, Bengaluru handling export-import and domestic container cargo.",
                    evidence_source="CONCOR Annual Report 2023-24 (Terminal Network Map)",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["infrastructure", "logistics"],
                    facility_locations=["Hyderabad (Sanathnagar)"],
                    description="Major Inland Container Depot at Sanathnagar, Hyderabad.",
                    evidence_source="CONCOR Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["infrastructure", "logistics"],
                    facility_locations=["Visakhapatnam", "Guntur"],
                    description="Container freight stations and rail terminals in Visakhapatnam and Guntur.",
                    evidence_source="CONCOR Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["infrastructure", "logistics"],
                    facility_locations=["Kochi (Vallarpadam)"],
                    description="Container handling depot serving Cochin Port Vallarpadam ICTT.",
                    evidence_source="CONCOR Annual Report 2023-24",
                ),
            ],
            business_activities=["Rail container haulage", "Inland container depot management", "Warehousing logistics"],
        )
    )

    # Blue Dart Express Limited (Logistics / Express Freight)
    companies.append(
        Company(
            isin="INE233B01017",
            company_name="Blue Dart Express Limited",
            ticker_nse="BLUEDART",
            ticker_bse="BLUEDART",
            bse_code="526612",
            sector="Logistics",
            industry="Logistics",
            sub_industry="Express Air & Surface Logistics",
            market_cap_category=MarketCapCategory.MID_CAP,
            market_cap_cr=16500.0,
            hq_state="Maharashtra",
            hq_city="Mumbai",
            website="https://www.bluedart.com",
            listing_status="Listed",
            exchange="NSE",
            business_description="South Asia's premier express air and integrated transportation and distribution logistics company.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["logistics", "infrastructure", "office"],
                    facility_locations=["Bengaluru"],
                    description="South regional express freight hub and air express facility at Kempegowda International Airport.",
                    evidence_source="Blue Dart Annual Report 2023-24 (Aviation & Hub Network)",
                ),
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["logistics", "infrastructure"],
                    facility_locations=["Hyderabad"],
                    description="Air and surface transshipment hub at Shamshabad Hyderabad.",
                    evidence_source="Blue Dart Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["logistics"],
                    facility_locations=["Kochi"],
                    description="Express distribution centres across Kerala commercial centres.",
                    evidence_source="Blue Dart Annual Report 2023-24",
                ),
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["logistics"],
                    facility_locations=["Visakhapatnam", "Vijayawada"],
                    description="Regional surface transport hubs and e-commerce distribution depots.",
                    evidence_source="Blue Dart Annual Report 2023-24",
                ),
            ],
            business_activities=["Air express package transport", "Surface parcel logistics", "E-commerce order fulfillment"],
        )
    )

    # Andhra Pradesh Power Generation Corporation Limited (Unlisted Public-Sector Utility)
    companies.append(
        Company(
            isin="UNLISTED-AP-GENCO",
            company_name="Andhra Pradesh Power Generation Corporation Limited",
            ticker_nse="",
            ticker_bse="",
            bse_code="",
            sector="Electricity",
            industry="Electric Utilities",
            sub_industry="Thermal & Hydro Power Generation",
            market_cap_category=MarketCapCategory.UNKNOWN,
            market_cap_cr=None,
            hq_state="Andhra Pradesh",
            hq_city="Vijayawada",
            website="https://www.apgenco.gov.in",
            listing_status="Unlisted",
            exchange="",
            business_description="State-owned power generation utility of the Government of Andhra Pradesh.",
            state_presences=[
                StatePresenceRecord(
                    state="Andhra Pradesh",
                    presence_types=["headquarters", "power_generation", "plant"],
                    facility_locations=["Vijayawada (Dr NTTPS)", "Muddanur (RTPP - YSR Kadapa)", "Krishnapatnam (SDSTPS)"],
                    description="Major thermal power stations including Dr Narla Tata Rao TPS (Vijayawada), Rayalaseema TPS (Muddanur), and Sri Damodaram Sanjeevaiah TPS (Nellore).",
                    evidence_source="Official APGENCO Operational Capacity Reports & APERC Filings",
                ),
            ],
            business_activities=["Thermal power generation", "Hydroelectric generation", "State electricity dispatch"],
        )
    )

    # Kerala State Road Transport Corporation (Unlisted Public Transport)
    companies.append(
        Company(
            isin="UNLISTED-KL-RTC",
            company_name="Kerala State Road Transport Corporation",
            ticker_nse="",
            ticker_bse="",
            bse_code="",
            sector="Roads & Transport",
            industry="Public Passenger Transport",
            sub_industry="State Road Transit",
            market_cap_category=MarketCapCategory.UNKNOWN,
            market_cap_cr=None,
            hq_state="Kerala",
            hq_city="Thiruvananthapuram",
            website="https://keralartc.com",
            listing_status="Unlisted",
            exchange="",
            business_description="State public transport undertaking operating passenger buses and fleet workshops across Kerala.",
            state_presences=[
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["headquarters", "infrastructure", "service_operation", "logistics"],
                    facility_locations=["Thiruvananthapuram", "Kochi", "Kozhikode", "Statewide"],
                    description="Central bus station at Thampanoor, Thiruvananthapuram; operating fleet of over 5,000 passenger buses across all Kerala districts.",
                    evidence_source="Official KSRTC Administrative Reports",
                ),
            ],
            business_activities=["Public passenger transportation", "Inter-district bus operations", "Vehicle fleet maintenance"],
        )
    )

    # --------------------------------------------------------------------------
    # 3. UNLISTED STATE-OWNED & PUBLIC-SECTOR ENTITIES
    # --------------------------------------------------------------------------

    # Kerala State Electricity Board Limited (Unlisted Public-Sector Utility)
    companies.append(
        Company(
            isin="UNLISTED-KL-KSEB",
            company_name="Kerala State Electricity Board Limited",
            ticker_nse="",
            ticker_bse="",
            bse_code="",
            sector="Electricity",
            industry="Electric Utilities",
            sub_industry="Power Transmission & Distribution",
            market_cap_category=MarketCapCategory.UNKNOWN,
            market_cap_cr=None,
            hq_state="Kerala",
            hq_city="Thiruvananthapuram",
            website="https://www.kseb.in",
            listing_status="Unlisted",
            exchange="",
            business_description="State-owned public utility corporation responsible for generation, transmission, and distribution of electricity across Kerala.",
            state_presences=[
                StatePresenceRecord(
                    state="Kerala",
                    presence_types=["headquarters", "power_generation", "infrastructure", "service_operation"],
                    facility_locations=["Thiruvananthapuram", "Idukki", "Statewide"],
                    description="Sole state public distribution licensee and transmission utility; hydro generation plants at Idukki, Sabarigiri.",
                    evidence_source="Official KSEB Annual Accounts & Kerala State Regulatory Commission Filings",
                ),
            ],
            business_activities=["Power transmission", "Electricity distribution", "Hydro power generation", "Tariff administration"],
        )
    )

    # Telangana State Power Generation Corporation Limited (Unlisted Public-Sector)
    companies.append(
        Company(
            isin="UNLISTED-TS-GENCO",
            company_name="Telangana State Power Generation Corporation Limited",
            ticker_nse="",
            ticker_bse="",
            bse_code="",
            sector="Electricity",
            industry="Electric Utilities",
            sub_industry="Thermal & Hydro Power Generation",
            market_cap_category=MarketCapCategory.UNKNOWN,
            market_cap_cr=None,
            hq_state="Telangana",
            hq_city="Hyderabad",
            website="https://www.tsgenco.co.in",
            listing_status="Unlisted",
            exchange="",
            business_description="State power generation undertaking owned by the Government of Telangana.",
            state_presences=[
                StatePresenceRecord(
                    state="Telangana",
                    presence_types=["headquarters", "power_generation", "plant"],
                    facility_locations=["Hyderabad", "Kothagudem (Bhadradri)", "Manuguru", "Srisailam"],
                    description="Thermal power stations at Kothagudem (KTPS) and Bhadradri (BTPS); hydro stations at Srisailam and Nagarjuna Sagar.",
                    evidence_source="TSGENCO Official Disclosures & TSERC Tariff Petitions",
                ),
            ],
            business_activities=["Thermal power generation", "Hydro power generation", "Station maintenance"],
        )
    )

    # Karnataka State Road Transport Corporation (Unlisted Public Undertaking)
    companies.append(
        Company(
            isin="UNLISTED-KA-RTC",
            company_name="Karnataka State Road Transport Corporation",
            ticker_nse="",
            ticker_bse="",
            bse_code="",
            sector="Roads & Transport",
            industry="Public Passenger Transport",
            sub_industry="Inter-city Bus Transit",
            market_cap_category=MarketCapCategory.UNKNOWN,
            market_cap_cr=None,
            hq_state="Karnataka",
            hq_city="Bengaluru",
            website="https://ksrtc.karnataka.gov.in",
            listing_status="Unlisted",
            exchange="",
            business_description="State-owned road transport corporation providing passenger transit services in Karnataka and neighboring states.",
            state_presences=[
                StatePresenceRecord(
                    state="Karnataka",
                    presence_types=["headquarters", "infrastructure", "service_operation", "logistics"],
                    facility_locations=["Bengaluru (Shantinagar)", "Mysuru", "Mangaluru", "Hubballi"],
                    description="Central administrative offices, major bus terminals, workshops, and commercial transport fleet across Karnataka.",
                    evidence_source="Official KSRTC Annual Administrative Reports",
                ),
            ],
            business_activities=["Passenger road transportation", "Intercity bus operation", "Fleet workshop maintenance"],
        )
    )

    return companies


class StateCompanyUniverse:
    """
    Registry and provider for the Controlled State Company Universe.
    """

    def __init__(self) -> None:
        self._companies: list[Company] = _build_state_companies()
        self._by_id: dict[str, Company] = {c.isin: c for c in self._companies}
        self._by_ticker: dict[str, Company] = {
            c.ticker_nse.upper(): c for c in self._companies if c.ticker_nse
        }

    def get_all(self) -> list[Company]:
        """Return all candidate companies in the controlled universe."""
        return list(self._companies)

    def count(self) -> int:
        """Return count of candidate companies."""
        return len(self._companies)

    def get_by_id(self, company_id: str) -> Optional[Company]:
        """Lookup company by ISIN or ID."""
        return self._by_id.get(company_id)

    def get_by_ticker(self, ticker: str) -> Optional[Company]:
        """Lookup company by trading ticker."""
        return self._by_ticker.get(ticker.strip().upper())

    def get_by_state(self, state: str) -> list[Company]:
        """Return companies having verified operational presence in the given State."""
        st_lower = state.strip().lower()
        results = []
        for c in self._companies:
            for sp in c.state_presences:
                if sp.state.strip().lower() == st_lower:
                    results.append(c)
                    break
        return results

    def get_by_sector(self, sector: str) -> list[Company]:
        """Return companies operating in or providing services to the given sector."""
        sec_lower = sector.strip().lower()
        return [
            c for c in self._companies
            if sec_lower in c.sector.strip().lower() or sec_lower in c.industry.strip().lower()
        ]

    def get_listed(self) -> list[Company]:
        """Return all listed companies."""
        return [c for c in self._companies if c.listing_status.lower() == "listed"]

    def get_unlisted(self) -> list[Company]:
        """Return all unlisted / public-sector entities."""
        return [c for c in self._companies if c.listing_status.lower() != "listed"]
