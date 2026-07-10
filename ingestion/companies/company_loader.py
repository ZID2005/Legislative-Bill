"""
ingestion/companies/company_loader.py
=====================================
Company master data loader.
Loads, normalizes, and enriches NSE/BSE listed companies.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from datetime import date
from typing import Any
import urllib.request

from config.logging_config import get_logger
from config.settings import settings
from schemas.company import Company, MarketCapCategory
from storage.company_repository import CompanyRepository

logger = get_logger(__name__)

# Standard NSE listed equities URL
DEFAULT_NSE_URL = "https://archives.nseindia.com/content/equities/EQUITY_L_CO_ME.csv"

# Pre-defined, curated seed database of major Indian companies for enrichment and offline fallback
SEED_COMPANIES = [
    {
        "isin": "INE002A01018",
        "company_name": "Reliance Industries Limited",
        "ticker_nse": "RELIANCE",
        "ticker_bse": "RELIANCE",
        "bse_code": "500325",
        "sector": "Energy",
        "industry": "Oil Gas & Fuels",
        "sub_industry": "Refining & Marketing",
        "market_cap_category": "large_cap",
        "market_cap_cr": 1800000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.ril.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE467B01029",
        "company_name": "Tata Consultancy Services Limited",
        "ticker_nse": "TCS",
        "ticker_bse": "TCS",
        "bse_code": "532540",
        "sector": "Technology",
        "industry": "IT Services",
        "sub_industry": "Software Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 1400000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.tcs.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE040A01034",
        "company_name": "HDFC Bank Limited",
        "ticker_nse": "HDFCBANK",
        "ticker_bse": "HDFCBANK",
        "bse_code": "500180",
        "sector": "Banking & Financial Services",
        "industry": "Private Sector Bank",
        "sub_industry": "Commercial Banking",
        "market_cap_category": "large_cap",
        "market_cap_cr": 1100000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.hdfcbank.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE009A01021",
        "company_name": "Infosys Limited",
        "ticker_nse": "INFY",
        "ticker_bse": "INFY",
        "bse_code": "500209",
        "sector": "Technology",
        "industry": "IT Services",
        "sub_industry": "Software Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 650000.0,
        "hq_state": "Karnataka",
        "hq_city": "Bengaluru",
        "website": "https://www.infosys.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE090A01021",
        "company_name": "ICICI Bank Limited",
        "ticker_nse": "ICICIBANK",
        "ticker_bse": "ICICIBANK",
        "bse_code": "532174",
        "sector": "Banking & Financial Services",
        "industry": "Private Sector Bank",
        "sub_industry": "Commercial Banking",
        "market_cap_category": "large_cap",
        "market_cap_cr": 750000.0,
        "hq_state": "Gujarat",
        "hq_city": "Vadodara",
        "website": "https://www.icicibank.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE397D01024",
        "company_name": "Bharti Airtel Limited",
        "ticker_nse": "BHARTIARTL",
        "ticker_bse": "BHARTIARTL",
        "bse_code": "532454",
        "sector": "Telecommunications",
        "industry": "Telecom Services",
        "sub_industry": "Mobile Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 700000.0,
        "hq_state": "Delhi",
        "hq_city": "New Delhi",
        "website": "https://www.airtel.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE062A01020",
        "company_name": "State Bank of India",
        "ticker_nse": "SBIN",
        "ticker_bse": "SBIN",
        "bse_code": "500112",
        "sector": "Banking & Financial Services",
        "industry": "Public Sector Bank",
        "sub_industry": "Commercial Banking",
        "market_cap_category": "large_cap",
        "market_cap_cr": 680000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.sbi.co.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE018A01030",
        "company_name": "Larsen & Toubro Limited",
        "ticker_nse": "LT",
        "ticker_bse": "LT",
        "bse_code": "500510",
        "sector": "Infrastructure",
        "industry": "Engineering & Construction",
        "sub_industry": "Heavy Engineering",
        "market_cap_category": "large_cap",
        "market_cap_cr": 450000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.larsentoubro.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE154A01025",
        "company_name": "ITC Limited",
        "ticker_nse": "ITC",
        "ticker_bse": "ITC",
        "bse_code": "500875",
        "sector": "Consumer Goods & FMCG",
        "industry": "FMCG",
        "sub_industry": "Tobacco & Diversified",
        "market_cap_category": "large_cap",
        "market_cap_cr": 520000.0,
        "hq_state": "West Bengal",
        "hq_city": "Kolkata",
        "website": "https://www.itcportal.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE030A01027",
        "company_name": "Hindustan Unilever Limited",
        "ticker_nse": "HINDUNILVR",
        "ticker_bse": "HINDUNILVR",
        "bse_code": "500696",
        "sector": "Consumer Goods & FMCG",
        "industry": "FMCG",
        "sub_industry": "Personal Care & Home Care",
        "market_cap_category": "large_cap",
        "market_cap_cr": 580000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.hul.co.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE423A01024",
        "company_name": "Adani Enterprises Limited",
        "ticker_nse": "ADANIENT",
        "ticker_bse": "ADANIENT",
        "bse_code": "512599",
        "sector": "Infrastructure",
        "industry": "Diversified Conglomerate",
        "sub_industry": "Mining & Trading",
        "market_cap_category": "large_cap",
        "market_cap_cr": 350000.0,
        "hq_state": "Gujarat",
        "hq_city": "Ahmedabad",
        "website": "https://www.adanienterprises.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE155A01022",
        "company_name": "Tata Motors Limited",
        "ticker_nse": "TATAMOTORS",
        "ticker_bse": "TATAMOTORS",
        "bse_code": "500570",
        "sector": "Manufacturing",
        "industry": "Automobiles",
        "sub_industry": "Commercial & Passenger Vehicles",
        "market_cap_category": "large_cap",
        "market_cap_cr": 380000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.tatamotors.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE044A01045",
        "company_name": "Sun Pharmaceutical Industries Limited",
        "ticker_nse": "SUNPHARMA",
        "ticker_bse": "SUNPHARMA",
        "bse_code": "524715",
        "sector": "Healthcare & Pharmaceuticals",
        "industry": "Pharmaceuticals",
        "sub_industry": "Generics & Formulations",
        "market_cap_category": "large_cap",
        "market_cap_cr": 360000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.sunpharma.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE733E01010",
        "company_name": "NTPC Limited",
        "ticker_nse": "NTPC",
        "ticker_bse": "NTPC",
        "bse_code": "532555",
        "sector": "Energy",
        "industry": "Power Generation",
        "sub_industry": "Thermal Power",
        "market_cap_category": "large_cap",
        "market_cap_cr": 320000.0,
        "hq_state": "Delhi",
        "hq_city": "New Delhi",
        "website": "https://www.ntpc.co.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE213A01029",
        "company_name": "Oil and Natural Gas Corporation Limited",
        "ticker_nse": "ONGC",
        "ticker_bse": "ONGC",
        "bse_code": "500312",
        "sector": "Energy",
        "industry": "Oil Exploration & Production",
        "sub_industry": "Upstream Oil & Gas",
        "market_cap_category": "large_cap",
        "market_cap_cr": 340000.0,
        "hq_state": "Delhi",
        "hq_city": "New Delhi",
        "website": "https://www.ongcindia.com",
        "listing_status": "Listed",
    },
    # --- Additional NIFTY 50 & Sector Leaders (Task 2.2 Expansion) ---
    {
        "isin": "INE238A01034",
        "company_name": "Axis Bank Limited",
        "ticker_nse": "AXISBANK",
        "ticker_bse": "AXISBANK",
        "bse_code": "532215",
        "sector": "Banking & Financial Services",
        "industry": "Private Sector Bank",
        "sub_industry": "Commercial Banking",
        "market_cap_category": "large_cap",
        "market_cap_cr": 340000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.axisbank.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE237A01028",
        "company_name": "Kotak Mahindra Bank Limited",
        "ticker_nse": "KOTAKBANK",
        "ticker_bse": "KOTAKBANK",
        "bse_code": "500247",
        "sector": "Banking & Financial Services",
        "industry": "Private Sector Bank",
        "sub_industry": "Commercial Banking",
        "market_cap_category": "large_cap",
        "market_cap_cr": 350000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.kotak.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE075A01022",
        "company_name": "Wipro Limited",
        "ticker_nse": "WIPRO",
        "ticker_bse": "WIPRO",
        "bse_code": "507685",
        "sector": "Technology",
        "industry": "IT Services",
        "sub_industry": "Software Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 260000.0,
        "hq_state": "Karnataka",
        "hq_city": "Bengaluru",
        "website": "https://www.wipro.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE860A01027",
        "company_name": "HCL Technologies Limited",
        "ticker_nse": "HCLTECH",
        "ticker_bse": "HCLTECH",
        "bse_code": "532281",
        "sector": "Technology",
        "industry": "IT Services",
        "sub_industry": "Software Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 420000.0,
        "hq_state": "Uttar Pradesh",
        "hq_city": "Noida",
        "website": "https://www.hcltech.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE585B01010",
        "company_name": "Maruti Suzuki India Limited",
        "ticker_nse": "MARUTI",
        "ticker_bse": "MARUTI",
        "bse_code": "532500",
        "sector": "Manufacturing",
        "industry": "Automobiles",
        "sub_industry": "Passenger Vehicles",
        "market_cap_category": "large_cap",
        "market_cap_cr": 380000.0,
        "hq_state": "Delhi",
        "hq_city": "New Delhi",
        "website": "https://www.marutisuzuki.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE101A01026",
        "company_name": "Mahindra & Mahindra Limited",
        "ticker_nse": "M&M",
        "ticker_bse": "M&M",
        "bse_code": "500520",
        "sector": "Manufacturing",
        "industry": "Automobiles",
        "sub_industry": "Passenger & Utility Vehicles",
        "market_cap_category": "large_cap",
        "market_cap_cr": 310000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.mahindra.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE081A01020",
        "company_name": "Tata Steel Limited",
        "ticker_nse": "TATASTEEL",
        "ticker_bse": "TATASTEEL",
        "bse_code": "500470",
        "sector": "Metals & Mining",
        "industry": "Iron & Steel",
        "sub_industry": "Steel Products",
        "market_cap_category": "large_cap",
        "market_cap_cr": 210000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.tatasteel.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE019A01030",
        "company_name": "JSW Steel Limited",
        "ticker_nse": "JSWSTEEL",
        "ticker_bse": "JSWSTEEL",
        "bse_code": "500228",
        "sector": "Metals & Mining",
        "industry": "Iron & Steel",
        "sub_industry": "Steel Products",
        "market_cap_category": "large_cap",
        "market_cap_cr": 200000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.jsw.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE038A01020",
        "company_name": "Hindalco Industries Limited",
        "ticker_nse": "HINDALCO",
        "ticker_bse": "HINDALCO",
        "bse_code": "500440",
        "sector": "Metals & Mining",
        "industry": "Aluminium",
        "sub_industry": "Aluminium Products",
        "market_cap_category": "large_cap",
        "market_cap_cr": 130000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.hindalco.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE522F01014",
        "company_name": "Coal India Limited",
        "ticker_nse": "COALINDIA",
        "ticker_bse": "COALINDIA",
        "bse_code": "533278",
        "sector": "Metals & Mining",
        "industry": "Coal",
        "sub_industry": "Coal Extraction",
        "market_cap_category": "large_cap",
        "market_cap_cr": 280000.0,
        "hq_state": "West Bengal",
        "hq_city": "Kolkata",
        "website": "https://www.coalindia.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE481G01011",
        "company_name": "UltraTech Cement Limited",
        "ticker_nse": "ULTRACEMCO",
        "ticker_bse": "ULTRACEMCO",
        "bse_code": "532538",
        "sector": "Infrastructure",
        "industry": "Cement",
        "sub_industry": "Cement & Cement Products",
        "market_cap_category": "large_cap",
        "market_cap_cr": 290000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.ultratechcement.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE047A01021",
        "company_name": "Grasim Industries Limited",
        "ticker_nse": "GRASIM",
        "ticker_bse": "GRASIM",
        "bse_code": "500300",
        "sector": "Manufacturing",
        "industry": "Diversified",
        "sub_industry": "Viscose & Chemicals",
        "market_cap_category": "large_cap",
        "market_cap_cr": 160000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.grasim.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE239A01016",
        "company_name": "Nestle India Limited",
        "ticker_nse": "NESTLEIND",
        "ticker_bse": "NESTLEIND",
        "bse_code": "500790",
        "sector": "Consumer Goods & FMCG",
        "industry": "FMCG",
        "sub_industry": "Food Products",
        "market_cap_category": "large_cap",
        "market_cap_cr": 240000.0,
        "hq_state": "Haryana",
        "hq_city": "Gurgaon",
        "website": "https://www.nestle.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE216A01030",
        "company_name": "Britannia Industries Limited",
        "ticker_nse": "BRITANNIA",
        "ticker_bse": "BRITANNIA",
        "bse_code": "500825",
        "sector": "Consumer Goods & FMCG",
        "industry": "FMCG",
        "sub_industry": "Bakery Products",
        "market_cap_category": "large_cap",
        "market_cap_cr": 120000.0,
        "hq_state": "Karnataka",
        "hq_city": "Bengaluru",
        "website": "https://www.britannia.co.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE192A01025",
        "company_name": "Tata Consumer Products Limited",
        "ticker_nse": "TATACONSUM",
        "ticker_bse": "TATACONSUM",
        "bse_code": "500800",
        "sector": "Consumer Goods & FMCG",
        "industry": "FMCG",
        "sub_industry": "Tea, Coffee & Foods",
        "market_cap_category": "large_cap",
        "market_cap_cr": 110000.0,
        "hq_state": "West Bengal",
        "hq_city": "Kolkata",
        "website": "https://www.tataconsumer.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE021A01026",
        "company_name": "Asian Paints Limited",
        "ticker_nse": "ASIANPAINT",
        "ticker_bse": "ASIANPAINT",
        "bse_code": "500820",
        "sector": "Consumer Goods & FMCG",
        "industry": "Paints",
        "sub_industry": "Decorative Paints",
        "market_cap_category": "large_cap",
        "market_cap_cr": 280000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.asianpaints.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE059A01026",
        "company_name": "Cipla Limited",
        "ticker_nse": "CIPLA",
        "ticker_bse": "CIPLA",
        "bse_code": "500087",
        "sector": "Healthcare & Pharmaceuticals",
        "industry": "Pharmaceuticals",
        "sub_industry": "Generics & Formulations",
        "market_cap_category": "large_cap",
        "market_cap_cr": 110000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.cipla.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE089A01023",
        "company_name": "Dr. Reddy's Laboratories Limited",
        "ticker_nse": "DRREDDY",
        "ticker_bse": "DRREDDY",
        "bse_code": "500124",
        "sector": "Healthcare & Pharmaceuticals",
        "industry": "Pharmaceuticals",
        "sub_industry": "Generics & Formulations",
        "market_cap_category": "large_cap",
        "market_cap_cr": 100000.0,
        "hq_state": "Telangana",
        "hq_city": "Hyderabad",
        "website": "https://www.drreddys.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE437A01024",
        "company_name": "Apollo Hospitals Enterprise Limited",
        "ticker_nse": "APOLLOHOSP",
        "ticker_bse": "APOLLOHOSP",
        "bse_code": "508869",
        "sector": "Healthcare & Pharmaceuticals",
        "industry": "Healthcare Services",
        "sub_industry": "Hospitals",
        "market_cap_category": "large_cap",
        "market_cap_cr": 95000.0,
        "hq_state": "Tamil Nadu",
        "hq_city": "Chennai",
        "website": "https://www.apollohospitals.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE752E01010",
        "company_name": "Power Grid Corporation of India Limited",
        "ticker_nse": "POWERGRID",
        "ticker_bse": "POWERGRID",
        "bse_code": "532898",
        "sector": "Energy",
        "industry": "Power Transmission",
        "sub_industry": "Transmission & Distribution",
        "market_cap_category": "large_cap",
        "market_cap_cr": 250000.0,
        "hq_state": "Haryana",
        "hq_city": "Gurgaon",
        "website": "https://www.powergrid.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE245A01021",
        "company_name": "Tata Power Company Limited",
        "ticker_nse": "TATAPOWER",
        "ticker_bse": "TATAPOWER",
        "bse_code": "500400",
        "sector": "Energy",
        "industry": "Power Utilities",
        "sub_industry": "Integrated Power",
        "market_cap_category": "large_cap",
        "market_cap_cr": 120000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.tatapower.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE364U01010",
        "company_name": "Adani Green Energy Limited",
        "ticker_nse": "ADANIGREEN",
        "ticker_bse": "ADANIGREEN",
        "bse_code": "541450",
        "sector": "Energy",
        "industry": "Renewable Power",
        "sub_industry": "Solar & Wind Power",
        "market_cap_category": "large_cap",
        "market_cap_cr": 280000.0,
        "hq_state": "Gujarat",
        "hq_city": "Ahmedabad",
        "website": "https://www.adanigreenenergy.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE814H01011",
        "company_name": "Adani Power Limited",
        "ticker_nse": "ADANIPOWER",
        "ticker_bse": "ADANIPOWER",
        "bse_code": "533096",
        "sector": "Energy",
        "industry": "Power Generation",
        "sub_industry": "Thermal Power",
        "market_cap_category": "large_cap",
        "market_cap_cr": 230000.0,
        "hq_state": "Gujarat",
        "hq_city": "Ahmedabad",
        "website": "https://www.adanipower.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE296A01024",
        "company_name": "Bajaj Finance Limited",
        "ticker_nse": "BAJFINANCE",
        "ticker_bse": "BAJFINANCE",
        "bse_code": "500034",
        "sector": "Banking & Financial Services",
        "industry": "NBFC",
        "sub_industry": "Consumer Finance",
        "market_cap_category": "large_cap",
        "market_cap_cr": 450000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Pune",
        "website": "https://www.bajajfinserv.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE918I01018",
        "company_name": "Bajaj Finserv Limited",
        "ticker_nse": "BAJAJFINSV",
        "ticker_bse": "BAJAJFINSV",
        "bse_code": "532978",
        "sector": "Banking & Financial Services",
        "industry": "NBFC",
        "sub_industry": "Holding Company",
        "market_cap_category": "large_cap",
        "market_cap_cr": 260000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Pune",
        "website": "https://www.bajajfinserv.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE00LIC01010",
        "company_name": "Life Insurance Corporation of India",
        "ticker_nse": "LICI",
        "ticker_bse": "LICI",
        "bse_code": "543526",
        "sector": "Banking & Financial Services",
        "industry": "Life Insurance",
        "sub_industry": "Life Insurance Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 480000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.licindia.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE123W01016",
        "company_name": "SBI Life Insurance Company Limited",
        "ticker_nse": "SBILIFE",
        "ticker_bse": "SBILIFE",
        "bse_code": "540719",
        "sector": "Banking & Financial Services",
        "industry": "Life Insurance",
        "sub_industry": "Life Insurance Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 140000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.sbilife.co.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE795G01014",
        "company_name": "HDFC Life Insurance Company Limited",
        "ticker_nse": "HDFCLIFE",
        "ticker_bse": "HDFCLIFE",
        "bse_code": "540777",
        "sector": "Banking & Financial Services",
        "industry": "Life Insurance",
        "sub_industry": "Life Insurance Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 130000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.hdfclife.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE066A01021",
        "company_name": "Eicher Motors Limited",
        "ticker_nse": "EICHERMOT",
        "ticker_bse": "EICHERMOT",
        "bse_code": "505200",
        "sector": "Manufacturing",
        "industry": "Automobiles",
        "sub_industry": "Two Wheelers",
        "market_cap_category": "large_cap",
        "market_cap_cr": 110000.0,
        "hq_state": "Delhi",
        "hq_city": "New Delhi",
        "website": "https://www.eicher.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE158A01026",
        "company_name": "Hero MotoCorp Limited",
        "ticker_nse": "HEROMOTOCO",
        "ticker_bse": "HEROMOTOCO",
        "bse_code": "500182",
        "sector": "Manufacturing",
        "industry": "Automobiles",
        "sub_industry": "Two Wheelers",
        "market_cap_category": "large_cap",
        "market_cap_cr": 85000.0,
        "hq_state": "Delhi",
        "hq_city": "New Delhi",
        "website": "https://www.heromotocorp.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE917I01010",
        "company_name": "Bajaj Auto Limited",
        "ticker_nse": "BAJAJ-AUTO",
        "ticker_bse": "BAJAJ-AUTO",
        "bse_code": "532977",
        "sector": "Manufacturing",
        "industry": "Automobiles",
        "sub_industry": "Two & Three Wheelers",
        "market_cap_category": "large_cap",
        "market_cap_cr": 220000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Pune",
        "website": "https://www.bajajauto.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE669C01036",
        "company_name": "Tech Mahindra Limited",
        "ticker_nse": "TECHM",
        "ticker_bse": "TECHM",
        "bse_code": "532755",
        "sector": "Technology",
        "industry": "IT Services",
        "sub_industry": "Software Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 120000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Pune",
        "website": "https://www.techmahindra.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE214G01026",
        "company_name": "LTIMindtree Limited",
        "ticker_nse": "LTIM",
        "ticker_bse": "LTIM",
        "bse_code": "540005",
        "sector": "Technology",
        "industry": "IT Services",
        "sub_industry": "Software Services",
        "market_cap_category": "large_cap",
        "market_cap_cr": 150000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.ltimindtree.com",
        "listing_status": "Listed",
    },
    {
        "isin": "INE003A01024",
        "company_name": "Siemens Limited",
        "ticker_nse": "SIEMENS",
        "ticker_bse": "SIEMENS",
        "bse_code": "500550",
        "sector": "Manufacturing",
        "industry": "Capital Goods",
        "sub_industry": "Industrial Machinery",
        "market_cap_category": "large_cap",
        "market_cap_cr": 170000.0,
        "hq_state": "Maharashtra",
        "hq_city": "Mumbai",
        "website": "https://www.siemens.co.in",
        "listing_status": "Listed",
    },
    {
        "isin": "INE117A01022",
        "company_name": "ABB India Limited",
        "ticker_nse": "ABB",
        "ticker_bse": "ABB",
        "bse_code": "500002",
        "sector": "Manufacturing",
        "industry": "Capital Goods",
        "sub_industry": "Heavy Electrical Equipment",
        "market_cap_category": "large_cap",
        "market_cap_cr": 150000.0,
        "hq_state": "Karnataka",
        "hq_city": "Bengaluru",
        "website": "https://new.abb.com/in",
        "listing_status": "Listed",
    },
]


class CompanyLoader:
    """
    Ingests and normalizes listed companies from NSE/BSE and seed tables.
    """

    def __init__(self, repository: CompanyRepository | None = None) -> None:
        self.repo = repository or CompanyRepository()

    def normalize_company_name(self, name: str) -> str:
        """Clean and normalize corporate endings to standard title case."""
        if not name:
            return ""

        clean_name = name.strip()

        # Casing normalization
        import re

        # Remove redundant spaces
        clean_name = re.sub(r"\s+", " ", clean_name)

        # Title case standard endings
        endings = {
            # Dot patterns first
            r"\bLTD\.(?=\s|$)": "Limited",
            r"\bCORP\.(?=\s|$)": "Corporation",
            r"\bINC\.(?=\s|$)": "Incorporated",
            r"\bPVT\.(?=\s|$)": "Private",
            r"\bCO\.(?=\s|$)": "Company",
            # Non-dot patterns second
            r"\bLTD\b": "Limited",
            r"\bLIMITED\b": "Limited",
            r"\bCORP\b": "Corporation",
            r"\bCORPORATION\b": "Corporation",
            r"\bINC\b": "Incorporated",
            r"\bINCORPORATED\b": "Incorporated",
            r"\bPVT\b": "Private",
            r"\bPRIVATE\b": "Private",
            r"\bCO\b": "Company",
            r"\bCOMPANY\b": "Company",
        }

        upper_name = clean_name.upper()
        for pattern, replacement in endings.items():
            upper_name = re.sub(pattern, replacement, upper_name)

        # Standard words capitalisation
        words = []
        for word in upper_name.split(" "):
            # If word is in endings values, keep it as is
            if word in ["Limited", "Corporation", "Incorporated", "Private", "Company"]:
                words.append(word)
            elif word.upper() in ["AND", "OF", "IN", "FOR", "&"]:
                words.append(word.lower())
            elif word.upper() in [
                "TCS",
                "ITC",
                "RIL",
                "HDFC",
                "ICICI",
                "SBI",
                "LIC",
                "L&T",
                "ONGC",
                "NTPC",
            ]:
                words.append(word.upper())
            else:
                words.append(word.capitalize())

        result = " ".join(words)
        # Capitalize first letter always
        if result:
            result = result[0].upper() + result[1:]
        return result

    def normalize_state(self, state: str) -> str:
        """Map state names to canonical Indian states."""
        if not state:
            return ""
        st_clean = state.strip().lower()

        mappings = {
            "mah": "Maharashtra",
            "maharashtra": "Maharashtra",
            "mumbai": "Maharashtra",
            "kar": "Karnataka",
            "karnataka": "Karnataka",
            "bangalore": "Karnataka",
            "bengaluru": "Karnataka",
            "tn": "Tamil Nadu",
            "tamilnadu": "Tamil Nadu",
            "tamil nadu": "Tamil Nadu",
            "del": "Delhi",
            "delhi": "Delhi",
            "new delhi": "Delhi",
            "guj": "Gujarat",
            "gujarat": "Gujarat",
            "ahmedabad": "Gujarat",
            "wb": "West Bengal",
            "west bengal": "West Bengal",
            "kolkata": "West Bengal",
            "telangana": "Telangana",
            "hyderabad": "Telangana",
            "ap": "Andhra Pradesh",
            "andhra pradesh": "Andhra Pradesh",
            "up": "Uttar Pradesh",
            "uttar pradesh": "Uttar Pradesh",
            "haryana": "Haryana",
            "gurgaon": "Haryana",
        }
        return mappings.get(st_clean, state.strip().title())

    def load_company_master(
        self, source_url: str | None = None, dry_run: bool = False
    ) -> list[Company]:
        """
        Load and normalize BSE/NSE company list.
        If connection fails, returns enriched seed data list.
        """
        url = source_url or DEFAULT_NSE_URL
        companies = []

        # Setup lookup index for seed data to easily merge enrichment
        seed_lookup = {item["isin"].upper(): item for item in SEED_COMPANIES}
        seed_symbol_lookup = {item["ticker_nse"].upper(): item for item in SEED_COMPANIES}

        logger.info("Attempting to fetch company list from %s", url)
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode("utf-8")

            csv_reader = csv.reader(io.StringIO(content))
            header = next(csv_reader)

            # Normalize headers
            headers = [h.strip().upper() for h in header]

            # Map index
            idx_symbol = -1
            idx_name = -1
            idx_isin = -1

            for i, h in enumerate(headers):
                if "SYMBOL" in h:
                    idx_symbol = i
                elif "NAME OF COMPANY" in h or "COMPANY NAME" in h:
                    idx_name = i
                elif "ISIN" in h:
                    idx_isin = i

            if idx_symbol == -1 or idx_isin == -1:
                raise ValueError("Required CSV headers not found in NSE file")

            for row in csv_reader:
                if not row or len(row) <= max(idx_symbol, idx_isin):
                    continue

                sym = row[idx_symbol].strip().upper()
                name = row[idx_name].strip() if idx_name != -1 else ""
                isin = row[idx_isin].strip().upper()

                if not isin or not sym:
                    continue

                # Check for seed enrichment matching ISIN or Symbol
                seed_data = seed_lookup.get(isin) or seed_symbol_lookup.get(sym)

                if seed_data:
                    company = Company(
                        isin=isin,
                        company_name=self.normalize_company_name(seed_data["company_name"]),
                        sector=seed_data["sector"],
                        ticker_nse=sym,
                        ticker_bse=seed_data["ticker_bse"],
                        bse_code=seed_data["bse_code"],
                        industry=seed_data["industry"],
                        sub_industry=seed_data["sub_industry"],
                        market_cap_category=MarketCapCategory(seed_data["market_cap_category"]),
                        market_cap_cr=seed_data.get("market_cap_cr"),
                        hq_state=self.normalize_state(seed_data["hq_state"]),
                        hq_city=seed_data["hq_city"],
                        website=seed_data["website"],
                        listing_status=seed_data["listing_status"],
                        is_active=True,
                    )
                else:
                    company = Company(
                        isin=isin,
                        company_name=self.normalize_company_name(name),
                        sector="Unknown Sector",
                        ticker_nse=sym,
                        listing_status="Listed",
                        is_active=True,
                    )
                companies.append(company)

            logger.info("Successfully loaded %d companies from NSE live feed", len(companies))

        except Exception as e:
            logger.warning("Failed to fetch from live exchange feed: %s. Using seed fallback.", e)
            # Use seed fallback directly
            companies = []
            for item in SEED_COMPANIES:
                company = Company(
                    isin=item["isin"],
                    company_name=self.normalize_company_name(item["company_name"]),
                    sector=item["sector"],
                    ticker_nse=item["ticker_nse"],
                    ticker_bse=item["ticker_bse"],
                    bse_code=item["bse_code"],
                    industry=item["industry"],
                    sub_industry=item["sub_industry"],
                    market_cap_category=MarketCapCategory(item["market_cap_category"]),
                    market_cap_cr=item.get("market_cap_cr"),
                    hq_state=self.normalize_state(item["hq_state"]),
                    hq_city=item["hq_city"],
                    website=item["website"],
                    listing_status=item["listing_status"],
                    is_active=True,
                )
                companies.append(company)
            logger.info("Loaded %d companies from local seed fallback", len(companies))

        # Write to repository
        if companies and not dry_run:
            self.repo.save_many(companies)

        return companies
