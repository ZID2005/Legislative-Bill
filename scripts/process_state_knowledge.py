"""
scripts/process_state_knowledge.py
==================================
CLI script to execute Task 8.4 State Bill Knowledge Layer & Document Processing.

Downloads official PDFs for the 23 pilot State bills into data/state_bills/pdfs/,
extracts text into data/state_bills/corpus/, classifies policy categories,
generates plain-language summaries, extracts provisions, maps stakeholders,
persists StateBillKnowledge records into data/state_bills/knowledge/,
and outputs data/state_bills/knowledge_quality_report.json.

Strict rule: Central Government data in data/bills/ remains frozen.
Strict rule: Zero State stock-market predictions generated.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.state_knowledge_service import StateKnowledgeService
from storage.bill_repository import BillRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_knowledge_repository import StateKnowledgeRepository


async def main() -> None:
    print("=" * 70)
    print("TASK 8.4: STATE BILL KNOWLEDGE LAYER & DOCUMENT PROCESSING")
    print("=" * 70)

    # 1. Verify Central Baseline before starting
    central_repo = BillRepository()
    central_count_pre = central_repo.count()
    print(f"[PRE-CHECK] Central Bill Count in data/bills/: {central_count_pre} (MUST REMAIN FROZEN)")

    state_repo = StateBillRepository()
    state_count = state_repo.count()
    print(f"[INFO] State Bill Count in data/state_bills/: {state_count} bills to process")

    # 2. Run State Knowledge Service
    service = StateKnowledgeService()
    print("[INFO] Starting asynchronous document download and extraction...")
    stats = await service.process_all(force_download=False, force_extract=False)

    print("\n" + "=" * 70)
    print("TASK 8.4 PROCESSING RESULTS")
    print("=" * 70)
    print(f"Total State Bills Processed     : {stats['total_bills']}")
    print(f"Official Documents Downloaded   : {stats['documents_downloaded']} ({stats['download_coverage_pct']}%)")
    print(f"Successful Text Extractions     : {stats['extractions_successful']} ({stats['extraction_success_pct']}%)")
    print(f"OCR Required Documents          : {stats['ocr_required']} ({stats['ocr_required_pct']}%)")
    print(f"Categorization Count            : {stats['categorized_count']}")
    print(f"Plain-Language Summary Count    : {stats['summarized_count']} ({stats['summary_coverage_pct']}%)")
    print(f"Stakeholder Mapping Count       : {stats['stakeholders_mapped_count']} ({stats['stakeholder_coverage_pct']}%)")
    print(f"State Prediction Records        : {stats['state_predictions_generated']} (MUST BE 0)")

    # 3. Verify Central Baseline after processing
    central_count_post = central_repo.count()
    print(f"\n[POST-CHECK] Central Bill Count: {central_count_post} (Delta: {central_count_post - central_count_pre})")
    assert central_count_post == central_count_pre, "Central repository was modified!"
    print("[POST-CHECK] Central baseline remains 100% frozen and intact.")

    knowledge_repo = StateKnowledgeRepository()
    k_count = knowledge_repo.count()
    print(f"[SUCCESS] Total StateBillKnowledge records saved: {k_count}")


if __name__ == "__main__":
    asyncio.run(main())
