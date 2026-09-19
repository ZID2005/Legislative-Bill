"""
scripts/ingest_pilot_state_bills.py
===================================
Script to run the Task 8.3 State Bill Controlled Ingestion Pilot.

Ingests 23 authoritative State bills (12 from Andhra Pradesh, 11 from Karnataka)
into the isolated StateBillRepository (data/state_bills/metadata/) and produces
a full provenance audit report.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from ingestion.state.service import StateIngestionService
from storage.state_bill_repository import StateBillRepository

PILOT_ANDHRA_PRADESH_BILLS = [
    {
        "title": "The Andhra Pradesh Omnibus (Speed of Doing Business) Bill, 2026",
        "bill_number": "L.A. Bill No. 21 of 2026",
        "year": 2026,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_21_16_33__407_v_1.pdf",
        "status": "passed_both",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh Electricity Duty (Amendment) Bill, 2026",
        "bill_number": "L.A. Bill No. 3 of 2026",
        "year": 2026,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_bill-3_16_31__387_v_1.pdf",
        "status": "passed_both",
        "assent_date": "2026-03-23",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh Motor Vehicles Taxation (Amendment) Bill, 2026",
        "bill_number": "L.A. Bill No. 14 of 2026",
        "year": 2026,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_bill-14_16_31__398_v_1.pdf",
        "status": "passed_both",
        "assent_date": "2026-03-26",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh Value Added Tax (Amendment) Bill, 2026",
        "bill_number": "L.A. Bill No. 18 of 2026",
        "year": 2026,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_bill-18_16_31__402_v_1.pdf",
        "status": "passed_both",
        "assent_date": "2026-04-01",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh Municipal Laws (Amendment) Bill, 2026",
        "bill_number": "L.A. Bill No. 1 of 2026",
        "year": 2026,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_bill-1_16_31__385_v_1.pdf",
        "status": "passed_both",
        "assent_date": "2026-03-26",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh Goods and Services Tax (Amendment) Bill, 2025",
        "bill_number": "L.A. Bill No. 32 of 2025",
        "year": 2025,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_BillNo_16_30__384_v_1.pdf",
        "status": "passed_both",
        "assent_date": "2025-10-31",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh Shops and Establishments (Amendment) Bill, 2025",
        "bill_number": "L.A. Bill No. 11 of 2025",
        "year": 2025,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_BillNo_16_30__364_v_1.pdf",
        "status": "passed_both",
        "assent_date": "2025-10-21",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Factories (Andhra Pradesh Amendment) Bill, 2025",
        "bill_number": "L.A. Bill No. 14 of 2025",
        "year": 2025,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_BillNo_16_30__367_v_1.pdf",
        "status": "passed_both",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh State Aquaculture Development Authority (Amendment) Bill, 2025",
        "bill_number": "L.A. Bill No. 20 of 2025",
        "year": 2025,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_BillNo_16_30__373_v_1.pdf",
        "status": "passed_both",
        "assent_date": "2025-11-07",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh Private Universities (Establishment and Regulation) (Amendment) Bill, 2026",
        "bill_number": "L.A. Bill No. 23 of 2026",
        "year": 2026,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_23_16_33__409_v_1.pdf",
        "status": "passed_both",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh Panchayat Raj (Second Amendment) Bill, 2026",
        "bill_number": "L.A. Bill No. 29 of 2026",
        "year": 2026,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_29_16_33__415_v_1.pdf",
        "status": "passed_both",
        "source_name": "andhra_pradesh_assembly",
    },
    {
        "title": "The Andhra Pradesh Jan Vishwas (Amendment of Provisions) Bill, 2026",
        "bill_number": "L.A. Bill No. 13 of 2026",
        "year": 2026,
        "state": "Andhra Pradesh",
        "legislature": "Andhra Pradesh Legislative Assembly",
        "house": "vidhan_sabha",
        "url": "https://aplegislature.org/web/aplegislature/bills",
        "pdf_url": "https://legislation.aplegislature.org/PreviewPage.do?filePath=basePath&fileName=Bills/PassedBills/English/Eng_passbill_bill-13_16_31__397_v_1.pdf",
        "status": "passed_both",
        "assent_date": "2026-03-24",
        "source_name": "andhra_pradesh_assembly",
    },
]

PILOT_KARNATAKA_BILLS = [
    {
        "title": "The Karnataka Goods and Services Tax (Amendment) Bill, 2024",
        "bill_number": "Bill No. 29 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-19",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_29.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Karnataka Legislature (Prevention of Disqualification) (Second Amendment) Bill, 2024",
        "bill_number": "Bill No. 27 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-19",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_27.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Karnataka Cine and Cultural Activists (Welfare) Bill, 2024",
        "bill_number": "Bill No. 28 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-19",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_28.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Karnataka Irrigation (Amendment) Bill, 2024",
        "bill_number": "Bill No. 32 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-22",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_32.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Karnataka Municipalities and Certain Other Law (Amendment) Bill, 2024",
        "bill_number": "Bill No. 31 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-22",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_31.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Greater Bengaluru Governance Bill, 2024",
        "bill_number": "Bill No. 34 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-23",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_34.pdf",
        "status": "passed_assembly",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Karnataka Appropriation (No. 4) Bill, 2024",
        "bill_number": "Bill No. 33 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-24",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_33.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Karnataka Land Revenue (Second Amendment) Bill, 2024",
        "bill_number": "Bill No. 35 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-24",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_35.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Karnataka Ancient and Historical Monuments and Archaeological Sites and Remains (Amendment) Bill, 2024",
        "bill_number": "Bill No. 36 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-24",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_36.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Karnataka Medical Registration and Certain Other Law (Amendment) Bill, 2024",
        "bill_number": "Bill No. 37 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-24",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_37.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
    {
        "title": "The Karnataka Scheduled Castes, Scheduled Tribes and Other Backward Classes (Reservation of Appointments, etc.) (Amendment) Bill, 2024",
        "bill_number": "Bill No. 39 of 2024",
        "year": 2024,
        "state": "Karnataka",
        "legislature": "Karnataka Legislative Assembly",
        "house": "vidhan_sabha",
        "introduction_date": "2024-07-24",
        "url": "https://kla.kar.nic.in/assembly/bills/bills1640.htm",
        "pdf_url": "https://kla.kar.nic.in/assembly/bills/bill1640_39.pdf",
        "status": "passed_both",
        "source_name": "karnataka_assembly",
    },
]


def run_pilot_ingestion() -> None:
    print("Initializing StateIngestionService...")
    repo = StateBillRepository()
    service = StateIngestionService(repository=repo)

    ap_source = service.registry.get("andhra_pradesh_assembly")
    kar_source = service.registry.get("karnataka_assembly")

    print(f"\n--- Ingesting Andhra Pradesh Pilot Bills ({len(PILOT_ANDHRA_PRADESH_BILLS)}) ---")
    ap_stats = service.process_raw_bills(PILOT_ANDHRA_PRADESH_BILLS, source=ap_source)
    print(f"AP Stats: {ap_stats}")

    print(f"\n--- Ingesting Karnataka Pilot Bills ({len(PILOT_KARNATAKA_BILLS)}) ---")
    kar_stats = service.process_raw_bills(PILOT_KARNATAKA_BILLS, source=kar_source)
    print(f"Karnataka Stats: {kar_stats}")

    report_path = service.save_provenance_report()
    print(f"\nSaved State Provenance Report to: {report_path}")

    print(f"\nTotal State Bills in Repository: {repo.count()}")
    print(f"States Represented: {repo.get_states_represented()}")
    print("Pilot Ingestion Completed Successfully!")


if __name__ == "__main__":
    run_pilot_ingestion()
