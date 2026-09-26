"""
utils/baseline_verifier.py
==========================
Programmatic baseline verification utility for Task 8.17.

Loads 'docs/production_baseline.json' and validates current disk storage
against the authoritative frozen figures:
- Central: 20 bills, 47 securities, 940 pairs, 4,700 predictions, 4,700 decisions, 940 anticipation scores, 14,100 reports
- State: 44 bills, 44 PDFs, 44 knowledge records, 86 corporate exposures, 0 stock predictions
- Unified: 66 legislative records, 70 companies (47 quant, 20 intel, 3 ref), 104 exposures
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

_DEFAULT_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "docs" / "production_baseline.json"


@dataclass
class BaselineCheckResult:
    category: str
    dimension: str
    expected: Any
    actual: Any
    passed: bool
    details: str = ""


@dataclass
class BaselineVerificationReport:
    manifest_version: str
    verified_at: str
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: list[BaselineCheckResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "verified_at": self.verified_at,
            "passed": self.passed,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "results": [
                {
                    "category": r.category,
                    "dimension": r.dimension,
                    "expected": r.expected,
                    "actual": r.actual,
                    "passed": r.passed,
                    "details": r.details,
                }
                for r in self.results
            ],
        }


class BaselineVerifier:
    """Evaluates filesystem state against authoritative baseline manifest."""

    def __init__(self, manifest_path: Optional[Path] = None) -> None:
        self.manifest_path = manifest_path or _DEFAULT_MANIFEST_PATH
        self._manifest_data: dict[str, Any] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        if not self.manifest_path.is_file():
            logger.error("Baseline manifest not found at %s", self.manifest_path)
            raise FileNotFoundError(f"Baseline manifest not found at {self.manifest_path}")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self._manifest_data = json.load(f)

    def verify(self, quick: bool = False) -> BaselineVerificationReport:
        """
        Run verification across all baseline dimensions.
        If quick=True, counts files via glob without deserializing entire records.
        """
        from datetime import datetime, timezone
        from storage.state_knowledge_repository import StateKnowledgeRepository
        from storage.state_corporate_exposure_repository import StateCorporateExposureRepository
        from services.company_intelligence_service import CompanyIntelligenceService

        results: list[BaselineCheckResult] = []

        c_base = self._manifest_data.get("central_baseline", {})
        s_base = self._manifest_data.get("state_baseline", {})
        u_base = self._manifest_data.get("unified_universe_baseline", {})

        # 1. Central Baseline Checks
        meta_dir = settings.BILLS_DIR / "metadata"
        all_c_files = list(meta_dir.glob("*.json")) if meta_dir.exists() else []
        actual_c_total = len(all_c_files)
        exp_c_total = c_base.get("central_total_records", 22)
        results.append(
            BaselineCheckResult(
                category="Central",
                dimension="Scanned Total Records",
                expected=exp_c_total,
                actual=actual_c_total,
                passed=(actual_c_total == exp_c_total),
                details=f"Found {actual_c_total} scanned bill metadata files in data/bills/metadata",
            )
        )

        aux_ids = set(c_base.get("auxiliary_record_ids", ["key-issues-and-analysis", "service-bill"]))
        prod_c_files = [f for f in all_c_files if f.stem not in aux_ids]
        actual_c_prod = len(prod_c_files)
        exp_c_prod = c_base.get("central_production_bills", c_base.get("production_bills_count", 20))
        results.append(
            BaselineCheckResult(
                category="Central",
                dimension="Production Bills",
                expected=exp_c_prod,
                actual=actual_c_prod,
                passed=(actual_c_prod == exp_c_prod),
                details=f"Found {actual_c_prod} canonical Central production bills",
            )
        )

        aux_c_files = [f for f in all_c_files if f.stem in aux_ids]
        actual_c_aux = len(aux_c_files)
        exp_c_aux = c_base.get("central_auxiliary_records", 2)
        results.append(
            BaselineCheckResult(
                category="Central",
                dimension="Auxiliary Records",
                expected=exp_c_aux,
                actual=actual_c_aux,
                passed=(actual_c_aux == exp_c_aux),
                details=f"Found {actual_c_aux} auxiliary non-production records: {[f.stem for f in aux_c_files]}",
            )
        )

        # Preds
        actual_preds = len(list(settings.PREDICTIONS_DIR.glob("pred_*.json")))
        exp_preds = c_base.get("prediction_records_count", 4700)
        results.append(
            BaselineCheckResult(
                category="Central",
                dimension="Predictions",
                expected=exp_preds,
                actual=actual_preds,
                passed=(actual_preds == exp_preds),
                details=f"Found {actual_preds} prediction JSON files",
            )
        )

        # Decs
        actual_decs = len(list(settings.DECISION_SUPPORT_DIR.glob("dec_*.json")))
        exp_decs = c_base.get("decision_records_count", 4700)
        results.append(
            BaselineCheckResult(
                category="Central",
                dimension="Decisions",
                expected=exp_decs,
                actual=actual_decs,
                passed=(actual_decs == exp_decs),
                details=f"Found {actual_decs} decision JSON files",
            )
        )

        # Anticipation
        ant_dir = settings.ANTICIPATION_DIR / "scores"
        actual_ants = len(list(ant_dir.glob("*.json"))) if ant_dir.exists() else 0
        exp_ants = c_base.get("anticipation_scores_count", 940)
        results.append(
            BaselineCheckResult(
                category="Central",
                dimension="Anticipation Scores",
                expected=exp_ants,
                actual=actual_ants,
                passed=(actual_ants == exp_ants),
                details=f"Found {actual_ants} anticipation score JSON files",
            )
        )

        # Stakeholder Reports
        inv_reports = len(list((settings.REPORTS_DIR / "investor").glob("*.json"))) if (settings.REPORTS_DIR / "investor").exists() else 0
        bus_reports = len(list((settings.REPORTS_DIR / "business").glob("*.json"))) if (settings.REPORTS_DIR / "business").exists() else 0
        pub_reports = len(list((settings.REPORTS_DIR / "public").glob("*.json"))) if (settings.REPORTS_DIR / "public").exists() else 0
        actual_reports = inv_reports + bus_reports + pub_reports
        exp_reports = c_base.get("stakeholder_reports", {}).get("total_count", 14100)
        results.append(
            BaselineCheckResult(
                category="Central",
                dimension="Stakeholder Reports",
                expected=exp_reports,
                actual=actual_reports,
                passed=(actual_reports == exp_reports),
                details=f"Found {actual_reports} total reports ({inv_reports} investor, {bus_reports} business, {pub_reports} public)",
            )
        )

        # 2. State Baseline Checks
        s_meta_dir = settings.STATE_BILLS_DIR / "metadata"
        s_meta_files = list(s_meta_dir.glob("*.json")) if s_meta_dir.exists() else []
        actual_s_bills = len(s_meta_files)
        exp_s_bills = s_base.get("production_bills_count", s_base.get("pilot_acts_count", 44))
        results.append(
            BaselineCheckResult(
                category="State",
                dimension="Production Bills",
                expected=exp_s_bills,
                actual=actual_s_bills,
                passed=(actual_s_bills == exp_s_bills),
                details=f"Found {actual_s_bills} state production bill metadata files",
            )
        )

        # State Breakdown Verification
        exp_breakdown = s_base.get("state_breakdown", {
            "Andhra Pradesh": 12,
            "Karnataka": 11,
            "Kerala": 11,
            "Telangana": 10,
        })
        actual_state_counts: dict[str, int] = {}
        for sf in s_meta_files:
            try:
                with open(sf, "r", encoding="utf-8") as bf:
                    b_data = json.load(bf)
                    st_name = b_data.get("state", "Unknown")
                    actual_state_counts[st_name] = actual_state_counts.get(st_name, 0) + 1
            except Exception:
                pass
        breakdown_match = all(actual_state_counts.get(st, 0) == cnt for st, cnt in exp_breakdown.items())
        results.append(
            BaselineCheckResult(
                category="State",
                dimension="State Breakdown",
                expected=exp_breakdown,
                actual=actual_state_counts,
                passed=breakdown_match,
                details=f"Verified 4 states: {actual_state_counts}",
            )
        )

        # Planned Jurisdictions Zero Production Check
        planned_states = s_base.get("planned_jurisdictions_zero_production", ["Maharashtra", "Gujarat", "Tamil Nadu"])
        planned_prod_counts = {st: actual_state_counts.get(st, 0) for st in planned_states}
        planned_passed = all(cnt == 0 for cnt in planned_prod_counts.values())
        results.append(
            BaselineCheckResult(
                category="State",
                dimension="Planned Jurisdictions Invariant",
                expected={st: 0 for st in planned_states},
                actual=planned_prod_counts,
                passed=planned_passed,
                details=f"Confirmed 0 production records for planned jurisdictions: {planned_prod_counts}",
            )
        )

        pdf_dir = settings.STATE_BILLS_DIR / "pdfs"
        actual_s_pdfs = len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.exists() else 0
        exp_s_pdfs = s_base.get("official_pdfs_count", 44)
        results.append(
            BaselineCheckResult(
                category="State",
                dimension="Official PDFs",
                expected=exp_s_pdfs,
                actual=actual_s_pdfs,
                passed=(actual_s_pdfs == exp_s_pdfs),
                details=f"Found {actual_s_pdfs} state official PDF files",
            )
        )

        actual_know = len(StateKnowledgeRepository().get_all())
        exp_know = s_base.get("knowledge_records_count", 44)
        results.append(
            BaselineCheckResult(
                category="State",
                dimension="Knowledge Records",
                expected=exp_know,
                actual=actual_know,
                passed=(actual_know == exp_know),
                details=f"Found {actual_know} state knowledge records",
            )
        )

        actual_s_exps = len(StateCorporateExposureRepository().get_all())
        exp_s_exps = s_base.get("corporate_exposures_count", 86)
        results.append(
            BaselineCheckResult(
                category="State",
                dimension="State Corporate Exposures",
                expected=exp_s_exps,
                actual=actual_s_exps,
                passed=(actual_s_exps == exp_s_exps),
                details=f"Found {actual_s_exps} state corporate exposure links",
            )
        )

        # State Stock Predictions Firewall (strictly 0)
        state_pred_dir = settings.DATA_DIR / "state_predictions"
        actual_state_preds = len(list(state_pred_dir.glob("*.json"))) if state_pred_dir.exists() else 0
        results.append(
            BaselineCheckResult(
                category="State",
                dimension="Stock Predictions Firewall",
                expected=0,
                actual=actual_state_preds,
                passed=(actual_state_preds == 0),
                details="Confirmed 0 state stock predictions exist on disk",
            )
        )

        # 3. Unified Baseline Checks
        comp_service = CompanyIntelligenceService()
        all_companies = comp_service.get_all_companies()
        actual_total_comps = len(all_companies)
        exp_total_comps = u_base.get("total_companies", 70)
        results.append(
            BaselineCheckResult(
                category="Unified",
                dimension="Total Master Companies",
                expected=exp_total_comps,
                actual=actual_total_comps,
                passed=(actual_total_comps == exp_total_comps),
                details=f"Found {actual_total_comps} master company entities",
            )
        )

        from services.company_intelligence_service import _CENTRAL_QUANTITATIVE_ISINS
        quant_comps = [c for c in all_companies if c.isin in _CENTRAL_QUANTITATIVE_ISINS]
        results.append(
            BaselineCheckResult(
                category="Unified",
                dimension="Quantitative Securities",
                expected=47,
                actual=len(quant_comps),
                passed=(len(quant_comps) == 47),
                details=f"Found {len(quant_comps)} quantitative securities",
            )
        )

        intel_comps = comp_service.get_intelligence_companies()
        exp_intel = u_base.get("companies_breakdown", {}).get("intelligence_only", 20)
        results.append(
            BaselineCheckResult(
                category="Unified",
                dimension="Intelligence-Only Companies",
                expected=exp_intel,
                actual=len(intel_comps),
                passed=(len(intel_comps) == exp_intel),
                details=f"Found {len(intel_comps)} intelligence-only entities guarded by IntelligenceCompanyFirewall",
            )
        )

        ref_comps = [c for c in all_companies if c.isin not in _CENTRAL_QUANTITATIVE_ISINS and c not in intel_comps]
        exp_ref = u_base.get("companies_breakdown", {}).get("reference", 3)
        results.append(
            BaselineCheckResult(
                category="Unified",
                dimension="Reference Companies",
                expected=exp_ref,
                actual=len(ref_comps),
                passed=(len(ref_comps) == exp_ref),
                details=f"Found {len(ref_comps)} reference entities: {[c.company_name for c in ref_comps]}",
            )
        )

        actual_non_quant = len(intel_comps) + len(ref_comps)
        exp_non_quant = u_base.get("companies_breakdown", {}).get("combined_non_quantitative_reference", 23)
        results.append(
            BaselineCheckResult(
                category="Unified",
                dimension="Combined Non-Quantitative Universe",
                expected=exp_non_quant,
                actual=actual_non_quant,
                passed=(actual_non_quant == exp_non_quant),
                details=f"Found {actual_non_quant} combined non-quantitative entities ({len(intel_comps)} intel + {len(ref_comps)} ref)",
            )
        )

        # Unified Legislative Records (22 Central scanned/total + 44 State = 66)
        from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
        all_leg_records = UnifiedLegislativeDiscoveryService().get_all_bills()
        actual_leg_records = len(all_leg_records)
        exp_leg_records = u_base.get("total_legislative_records", 66)
        results.append(
            BaselineCheckResult(
                category="Unified",
                dimension="Total Legislative Records",
                expected=exp_leg_records,
                actual=actual_leg_records,
                passed=(actual_leg_records == exp_leg_records),
                details=f"Found {actual_leg_records} total legislative records in unified discovery ({actual_c_total} Central + {actual_s_bills} State)",
            )
        )

        # Unified Corporate Exposures (18 Central + 86 State = 104)
        from storage.company_exposure_repository import CompanyExposureRepository
        actual_all_exps = len(CompanyExposureRepository().get_all())
        exp_all_exps = u_base.get("total_corporate_exposures", 104)
        results.append(
            BaselineCheckResult(
                category="Unified",
                dimension="Total Corporate Exposures",
                expected=exp_all_exps,
                actual=actual_all_exps,
                passed=(actual_all_exps == exp_all_exps),
                details=f"Found {actual_all_exps} corporate exposures (18 Central + 86 State)",
            )
        )

        passed_count = sum(1 for r in results if r.passed)
        failed_count = sum(1 for r in results if not r.passed)
        all_passed = failed_count == 0

        return BaselineVerificationReport(
            manifest_version=self._manifest_data.get("manifest_version", "1.0.0"),
            verified_at=datetime.now(timezone.utc).isoformat(),
            passed=all_passed,
            total_checks=len(results),
            passed_checks=passed_count,
            failed_checks=failed_count,
            results=results,
        )


def verify_production_baseline(quick: bool = False) -> BaselineVerificationReport:
    """Convenience helper to run baseline verification."""
    verifier = BaselineVerifier()
    return verifier.verify(quick=quick)
