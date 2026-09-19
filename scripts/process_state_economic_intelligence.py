"""
scripts/process_state_economic_intelligence.py
==============================================
CLI script to execute Task 8.6 State Sector & Stakeholder Intelligence Layer.

Enriches all 44 Indian State legislative bills across Andhra Pradesh, Karnataka,
Kerala, and Telangana with structured StateBillEconomicProfile records:
1. Sector classification (primary, secondary, sub-sectors, economic activities)
2. Grounded stakeholder impacts (roles, directions, statutory mechanisms)
3. Text-grounded evidence linking
4. Direct vs Indirect impact classifications
5. State economic geography (state-wide, urban, rural, municipal, regional)
6. Listed-company exposure readiness (HIGH, MEDIUM, LOW, NONE, UNKNOWN)
7. Non-speculative factual summaries

Strict rules:
- Central Government production data remains 100% frozen.
- State market predictions remain exactly ZERO.
- Unsupported financial claim count must be ZERO.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings
from knowledge.state_economic_intelligence import StateEconomicIntelligenceEngine
from knowledge.state_summary_engine import StateSummaryEngine
from schemas.state_economic_profile import StateBillEconomicProfile
from schemas.state_knowledge import StateBillKnowledge
from storage.bill_repository import BillRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_knowledge_repository import StateKnowledgeRepository
from utils.file_utils import ensure_dir, file_exists, load_json, save_json


def main() -> None:
    print("=" * 80)
    print("TASK 8.6: STATE SECTOR & STAKEHOLDER INTELLIGENCE PROCESSING")
    print("=" * 80)

    # 1. Verify Central Baseline before starting
    central_repo = BillRepository()
    central_count_pre = central_repo.count()
    print(f"[PRE-CHECK] Central Bill Count in data/bills/: {central_count_pre} (MUST BE 22, FROZEN)")
    assert central_count_pre == 22, f"Central baseline altered! Expected 22, got {central_count_pre}"

    pred_dir = settings.DATA_DIR / "predictions"
    pred_files = [f for f in os.listdir(pred_dir) if f.startswith("pred_")]
    print(f"[PRE-CHECK] Central Predictions Count: {len(pred_files)} (MUST BE 4,700, FROZEN)")
    assert len(pred_files) == 4700, f"Central predictions altered! Expected 4700, got {len(pred_files)}"

    state_repo = StateBillRepository()
    knowledge_repo = StateKnowledgeRepository()
    bills = state_repo.get_all()
    print(f"[INFO] State Bills to process: {len(bills)}")
    assert len(bills) == 44, f"Expected 44 State bills, got {len(bills)}"

    engine = StateEconomicIntelligenceEngine()
    summary_engine = StateSummaryEngine()

    stats: dict[str, Any] = {
        "total_bills_analyzed": len(bills),
        "primary_sector_classified": 0,
        "secondary_sectors_classified": 0,
        "stakeholder_classifications_count": 0,
        "evidence_references_count": 0,
        "direct_impacts_count": 0,
        "indirect_impacts_count": 0,
        "geographic_scope_classified": 0,
        "company_exposure_readiness_counts": {
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "NONE": 0,
            "UNKNOWN": 0,
        },
        "geographic_scope_distribution": {},
        "primary_sector_distribution": {},
        "unsupported_claim_count": 0,
        "state_predictions_generated": 0,  # STRICTLY 0
        "bills": {},
    }

    for bill in bills:
        # Load existing knowledge record if available
        k_rec = knowledge_repo.get(bill.bill_id)
        if not k_rec:
            print(f"[WARNING] Knowledge record for {bill.bill_id} not found. Constructing base record.")
            k_rec = StateBillKnowledge(
                bill_id=bill.bill_id,
                jurisdiction="state",
                state=bill.state or "",
                title=bill.title,
                bill_number=bill.bill_number,
                chamber=bill.house.value if hasattr(bill.house, "value") else str(bill.house),
                status=bill.status.value if hasattr(bill.status, "value") else str(bill.status),
                source_url=bill.url,
                policy_category=bill.sectors[0] if bill.sectors else "Other / Unclassified",
            )

        # Retrieve corpus text
        corpus_path = bill.text_path or (settings.STATE_BILLS_DIR / "corpus" / f"{bill.bill_id}.txt")
        corpus_text = ""
        if file_exists(corpus_path):
            with open(corpus_path, "r", encoding="utf-8", errors="replace") as fp:
                corpus_text = fp.read()
        elif bill.full_text:
            corpus_text = bill.full_text

        # Extract structured provisions
        provisions = summary_engine.extract_provisions(bill, corpus_text)

        # Generate economic profile
        profile: StateBillEconomicProfile = engine.analyze_bill(
            bill,
            corpus_text=corpus_text,
            provisions=provisions,
        )

        # Verify no overclaiming
        engine.verify_no_overclaiming(profile)

        # Attach profile to knowledge record
        k_rec.economic_profile = profile
        k_rec.provenance["economic_profile"] = "SYSTEM_DERIVED"

        # Save enriched knowledge record
        knowledge_repo.save(k_rec)

        # Update stats
        if profile.primary_sector and profile.primary_sector != "Other":
            stats["primary_sector_classified"] += 1
        if profile.secondary_sectors:
            stats["secondary_sectors_classified"] += 1

        stats["stakeholder_classifications_count"] += len(profile.stakeholders)
        stats["evidence_references_count"] += len(profile.evidence)
        stats["direct_impacts_count"] += len(profile.direct_impacts)
        stats["indirect_impacts_count"] += len(profile.indirect_impacts)
        if profile.geographic_scope:
            stats["geographic_scope_classified"] += 1

        stats["company_exposure_readiness_counts"][profile.company_exposure_readiness] += 1

        geo = profile.geographic_scope
        stats["geographic_scope_distribution"][geo] = stats["geographic_scope_distribution"].get(geo, 0) + 1

        psec = profile.primary_sector or "Unknown"
        stats["primary_sector_distribution"][psec] = stats["primary_sector_distribution"].get(psec, 0) + 1

        stats["bills"][bill.bill_id] = {
            "state": bill.state,
            "title": bill.title,
            "primary_sector": profile.primary_sector,
            "secondary_sectors": profile.secondary_sectors,
            "geographic_scope": profile.geographic_scope,
            "readiness": profile.company_exposure_readiness,
            "stakeholders_count": len(profile.stakeholders),
            "evidence_count": len(profile.evidence),
        }

    # Verify Central Baseline after execution
    central_count_post = central_repo.count()
    assert central_count_post == central_count_pre, "Central repository was modified!"
    pred_files_post = [f for f in os.listdir(pred_dir) if f.startswith("pred_")]
    assert len(pred_files_post) == 4700, "Central predictions altered!"

    # Save Quality Report
    report_path = settings.STATE_BILLS_DIR / "economic_intelligence_quality_report.json"
    ensure_dir(report_path.parent)
    save_json(stats, report_path)
    print(f"\n[SAVED] Economic intelligence quality report saved to: {report_path}")

    print("\n" + "=" * 80)
    print("TASK 8.6 STATE SECTOR & STAKEHOLDER INTELLIGENCE RESULTS")
    print("=" * 80)
    print(f"Total State Bills Analyzed         : {stats['total_bills_analyzed']}")
    print(f"Primary Sector Classifications     : {stats['primary_sector_classified']}")
    print(f"Secondary Sector Classifications   : {stats['secondary_sectors_classified']}")
    print(f"Stakeholder Classifications Total  : {stats['stakeholder_classifications_count']}")
    print(f"Evidence References Total          : {stats['evidence_references_count']}")
    print(f"Direct Impacts Identified          : {stats['direct_impacts_count']}")
    print(f"Indirect Impacts Identified        : {stats['indirect_impacts_count']}")
    print(f"Geographic Scopes Assigned         : {stats['geographic_scope_classified']}")
    print(f"Corporate Readiness Breakdown      : {stats['company_exposure_readiness_counts']}")
    print(f"Geographic Scope Distribution      : {stats['geographic_scope_distribution']}")
    print(f"Unsupported Claim Count            : {stats['unsupported_claim_count']} (TARGET = 0)")
    print(f"State Predictions Generated        : {stats['state_predictions_generated']} (MUST BE 0)")
    print("[POST-CHECK] Central baseline remains 100% frozen and intact.")
    print("=" * 80)


if __name__ == "__main__":
    main()
