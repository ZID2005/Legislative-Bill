"""
services/state_knowledge_service.py
===================================
Orchestration service for Indian State Bill Knowledge Layer & Document Processing.

Coordinates document downloading, text extraction, policy categorization,
plain-language summarization, provision extraction, stakeholder knowledge mapping,
and isolated repository storage.
Maintains strict isolation from Central Government production data and
guarantees ZERO State stock-market predictions.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from ingestion.state.downloader import StateDocumentDownloader
from ingestion.state.extractor import StateExtractionResult, StateTextExtractor
from knowledge.state_corporate_exposure_engine import StateCorporateExposureEngine
from knowledge.state_economic_intelligence import StateEconomicIntelligenceEngine
from knowledge.state_stakeholder_engine import StateStakeholderEngine
from knowledge.state_summary_engine import StateSummaryEngine
from knowledge.state_taxonomy import StateTaxonomyEngine
from schemas.bill import Bill
from schemas.state_economic_profile import StateBillEconomicProfile
from schemas.state_corporate_exposure import StateCorporateExposure
from schemas.state_knowledge import StateBillKnowledge, StateBillSummary
from storage.state_bill_repository import StateBillRepository
from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
from storage.state_knowledge_repository import StateKnowledgeRepository
from utils.file_utils import ensure_dir, save_json

logger = get_logger(__name__)


class StateKnowledgeService:
    """
    High-level orchestrator for processing State bills into structured knowledge.
    """

    def __init__(
        self,
        bill_repository: Optional[StateBillRepository] = None,
        knowledge_repository: Optional[StateKnowledgeRepository] = None,
        downloader: Optional[StateDocumentDownloader] = None,
        extractor: Optional[StateTextExtractor] = None,
        taxonomy_engine: Optional[StateTaxonomyEngine] = None,
        summary_engine: Optional[StateSummaryEngine] = None,
        stakeholder_engine: Optional[StateStakeholderEngine] = None,
        economic_engine: Optional[StateEconomicIntelligenceEngine] = None,
        corporate_engine: Optional[StateCorporateExposureEngine] = None,
        corporate_repository: Optional[StateCorporateExposureRepository] = None,
    ) -> None:
        self.bill_repo = bill_repository or StateBillRepository()
        self.knowledge_repo = knowledge_repository or StateKnowledgeRepository()
        self.downloader = downloader or StateDocumentDownloader()
        self.extractor = extractor or StateTextExtractor()
        self.taxonomy_engine = taxonomy_engine or StateTaxonomyEngine()
        self.summary_engine = summary_engine or StateSummaryEngine()
        self.stakeholder_engine = stakeholder_engine or StateStakeholderEngine(
            taxonomy_engine=self.taxonomy_engine
        )
        self.economic_engine = economic_engine or StateEconomicIntelligenceEngine()
        self.corporate_engine = corporate_engine or StateCorporateExposureEngine()
        self.corporate_repo = corporate_repository or StateCorporateExposureRepository()

    async def process_bill(
        self,
        bill: Bill,
        force_download: bool = False,
        force_extract: bool = False,
    ) -> StateBillKnowledge:
        """
        Process a single State Bill through the full document and knowledge pipeline.
        """
        logger.info("Processing State bill: %s (%s)", bill.bill_id, bill.state)

        # 1. Download official document
        if bill.pdf_url:
            await self.downloader.download_bill(bill, force=force_download)

        # 2. Extract text into corpus
        pdf_path = Path(bill.pdf_path) if bill.pdf_path else None
        if not pdf_path or not pdf_path.is_file():
            default_pdf = self.downloader.pdfs_dir / f"{bill.bill_id}.pdf"
            if default_pdf.is_file():
                pdf_path = default_pdf
                bill.pdf_path = str(default_pdf.resolve())

        extraction_res: StateExtractionResult = self.extractor.extract_from_pdf(
            pdf_path=pdf_path,
            bill_id=bill.bill_id,
            force=force_extract,
        )

        # Update bill model extraction fields
        bill.text_status = extraction_res.text_status
        bill.extraction_method = extraction_res.extraction_method
        bill.extraction_timestamp = extraction_res.extraction_timestamp
        bill.page_count = extraction_res.page_count
        bill.quality_metrics = extraction_res.quality_metrics
        if extraction_res.detected_language:
            bill.language = extraction_res.detected_language
        if extraction_res.text_status == "success":
            bill.text_path = extraction_res.text_path
            bill.text_checksum = extraction_res.text_checksum
            bill.text_size = extraction_res.text_size
            bill.full_text = extraction_res.extracted_text

        extracted_text = extraction_res.extracted_text or bill.full_text or ""

        # 3. Categorize into State Policy Taxonomy
        category, cat_provenance = self.taxonomy_engine.classify(bill, extracted_text)
        bill.sectors = [category]

        # 4. Extract structured legislative provisions
        provisions = self.summary_engine.extract_provisions(bill, extracted_text)

        # 5. Identify grounded stakeholders
        stakeholders = self.stakeholder_engine.identify_stakeholders(
            bill, extracted_text, policy_category=category
        )

        # 6. Generate grounded plain-language summary
        summary: StateBillSummary = self.summary_engine.generate_summary(
            bill,
            text=extracted_text,
            policy_category=category,
            stakeholders=stakeholders,
            provisions=provisions,
        )
        bill.summary = summary.what_is_bill + " " + summary.what_it_changes

        # 7. Generate State Sector & Stakeholder Economic Profile (Task 8.6)
        economic_profile = self.economic_engine.analyze_bill(
            bill,
            corpus_text=extracted_text,
            provisions=provisions,
        )

        # 8. Generate State Corporate Exposure Intelligence (Task 8.7)
        corporate_exposures = self.corporate_engine.analyze_bill_exposure(
            bill,
            economic_profile=economic_profile,
            corpus_text=extracted_text,
            provisions=provisions,
        )
        self.corporate_repo.save_for_bill(bill.bill_id, corporate_exposures)

        # 9. Compile field-level provenance audit map
        provenance_map: dict[str, str] = {
            "title": "AUTHORITATIVE",
            "bill_number": "AUTHORITATIVE",
            "jurisdiction": "AUTHORITATIVE",
            "state": "AUTHORITATIVE",
            "chamber": "AUTHORITATIVE",
            "status": "AUTHORITATIVE",
            "source_url": "AUTHORITATIVE",
            "pdf_url": "AUTHORITATIVE" if bill.pdf_url else "UNAVAILABLE",
            "introduction_date": "AUTHORITATIVE" if bill.introduction_date else "UNAVAILABLE",
            "assent_date": "AUTHORITATIVE" if bill.assent_date else "UNAVAILABLE",
            "year": "DERIVED" if bill.year else "UNAVAILABLE",
            "bill_id": "DERIVED",
            "policy_category": cat_provenance,
            "document_hash": "DERIVED" if bill.document_checksum else "UNAVAILABLE",
            "corpus_path": "DERIVED" if bill.text_path else "UNAVAILABLE",
            "language": "AUTHORITATIVE" if bill.language else "DERIVED",
            "summary": "SYSTEM_DERIVED",
            "objective": "SYSTEM_DERIVED" if provisions.get("objective") else "UNAVAILABLE",
            "key_provisions": "SYSTEM_DERIVED" if summary.key_provisions else "UNAVAILABLE",
            "amended_acts": "SYSTEM_DERIVED" if provisions.get("amended_acts") else "UNAVAILABLE",
            "affected_stakeholders": "SYSTEM_DERIVED" if stakeholders else "UNAVAILABLE",
            "administrative_authority": "SYSTEM_DERIVED" if provisions.get("administrative_authority") else "UNAVAILABLE",
            "financial_provisions": "SYSTEM_DERIVED" if provisions.get("financial_or_tax_provisions") else "UNAVAILABLE",
            "penalties_provisions": "SYSTEM_DERIVED" if provisions.get("penalties_or_enforcement") else "UNAVAILABLE",
            "economic_profile": "SYSTEM_DERIVED",
            "corporate_exposures": "SYSTEM_DERIVED" if corporate_exposures else "NONE",
        }

        # 10. Assemble canonical StateBillKnowledge record
        knowledge_record = StateBillKnowledge(
            bill_id=bill.bill_id,
            jurisdiction="state",
            state=bill.state or "",
            title=bill.title,
            bill_number=bill.bill_number,
            chamber=bill.house.value if hasattr(bill.house, "value") else str(bill.house),
            status=bill.status.value if hasattr(bill.status, "value") else str(bill.status),
            source_url=bill.url,
            policy_category=category,
            category_provenance=cat_provenance,
            year=bill.year,
            introduction_date=str(bill.introduction_date) if bill.introduction_date else None,
            assent_date=str(bill.assent_date) if bill.assent_date else None,
            pdf_url=bill.pdf_url,
            corpus_path=bill.text_path,
            document_hash=bill.document_checksum,
            summary=summary,
            objective=provisions.get("objective"),
            key_provisions=summary.key_provisions,
            amended_acts=provisions.get("amended_acts", []),
            affected_stakeholders=stakeholders,
            administrative_authority=provisions.get("administrative_authority"),
            financial_provisions=provisions.get("financial_or_tax_provisions"),
            penalties_provisions=provisions.get("penalties_or_enforcement"),
            extraction_status=extraction_res.text_status,
            language=bill.language or "English",
            page_count=extraction_res.page_count,
            character_count=extraction_res.char_count,
            word_count=extraction_res.word_count,
            provenance=provenance_map,
            economic_profile=economic_profile,
            corporate_exposures=corporate_exposures,
        )

        # 11. Persist updated bill metadata and knowledge record
        self.bill_repo.save(bill)
        self.knowledge_repo.save(knowledge_record)

        return knowledge_record

    async def process_all(
        self,
        force_download: bool = False,
        force_extract: bool = False,
    ) -> dict[str, Any]:
        """
        Execute document download, text extraction, and knowledge building
        for all State bills in the repository.
        """
        bills = self.bill_repo.get_all()
        logger.info("Starting State Knowledge processing for %d bills", len(bills))

        processed_records: list[StateBillKnowledge] = []
        stats: dict[str, Any] = {
            "total_bills": len(bills),
            "documents_downloaded": 0,
            "extractions_successful": 0,
            "ocr_required": 0,
            "extractions_failed": 0,
            "categorized_count": 0,
            "summarized_count": 0,
            "stakeholders_mapped_count": 0,
            "total_corporate_exposures": 0,
            "direct_corporate_exposures": 0,
            "indirect_corporate_exposures": 0,
            "high_strength_exposures": 0,
            "bills_with_corporate_exposure": 0,
            "state_predictions_generated": 0,  # MUST REMAIN 0
            "bills": {},
        }

        for bill in bills:
            record = await self.process_bill(
                bill,
                force_download=force_download,
                force_extract=force_extract,
            )
            processed_records.append(record)

            # Accumulate statistics
            if record.document_hash:
                stats["documents_downloaded"] += 1
            if record.extraction_status == "success":
                stats["extractions_successful"] += 1
            elif record.extraction_status == "ocr_required":
                stats["ocr_required"] += 1
            else:
                stats["extractions_failed"] += 1

            if record.policy_category and record.policy_category != "Other / Unclassified":
                stats["categorized_count"] += 1
            if record.summary and record.summary.what_is_bill:
                stats["summarized_count"] += 1
            if record.affected_stakeholders:
                stats["stakeholders_mapped_count"] += 1

            exps = record.corporate_exposures or []
            if exps:
                stats["bills_with_corporate_exposure"] += 1
                stats["total_corporate_exposures"] += len(exps)
                stats["direct_corporate_exposures"] += sum(1 for e in exps if e.direct_indirect == "DIRECT")
                stats["indirect_corporate_exposures"] += sum(1 for e in exps if e.direct_indirect == "INDIRECT")
                stats["high_strength_exposures"] += sum(1 for e in exps if e.exposure_strength == "HIGH")

            stats["bills"][record.bill_id] = {
                "state": record.state,
                "title": record.title,
                "category": record.policy_category,
                "extraction_status": record.extraction_status,
                "character_count": record.character_count,
                "page_count": record.page_count,
                "stakeholders_count": len(record.affected_stakeholders),
                "amended_acts_count": len(record.amended_acts),
                "corporate_exposures_count": len(exps),
            }

        # Calculate coverage percentages
        total = max(1, len(bills))
        stats["download_coverage_pct"] = round((stats["documents_downloaded"] / total) * 100, 1)
        stats["extraction_success_pct"] = round((stats["extractions_successful"] / total) * 100, 1)
        stats["ocr_required_pct"] = round((stats["ocr_required"] / total) * 100, 1)
        stats["summary_coverage_pct"] = round((stats["summarized_count"] / total) * 100, 1)
        stats["stakeholder_coverage_pct"] = round((stats["stakeholders_mapped_count"] / total) * 100, 1)

        # Write quality report to disk
        report_path = settings.STATE_BILLS_DIR / "knowledge_quality_report.json"
        ensure_dir(report_path.parent)
        save_json(stats, report_path)
        logger.info("Saved state knowledge quality report to %s", report_path)

        return stats
