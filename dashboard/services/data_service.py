"""
dashboard/services/data_service.py
==================================
Clean data access layer for the Decision-Support Dashboard.

Decouples UI components from underlying storage repositories, implements
deterministic in-memory caching, and enriches decision records with master
bill and company metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from config.logging_config import get_logger
from dashboard.utils.cache import cached_data
from schemas.bill import Bill
from schemas.company import Company
from schemas.decision import DecisionSupportRecord
from schemas.report import BillLevelReport, CompanyLevelReport, StakeholderReport
from storage.backtest_repository import BacktestRepository
from storage.bill_repository import BillRepository
from storage.company_repository import CompanyRepository
from storage.decision_repository import DecisionRepository
from storage.explainability_repository import ExplainabilityRepository
from storage.mapping_repository import MappingRepository
from storage.report_repository import ReportRepository

logger = get_logger(__name__)


class DashboardDataService:
    """
    Centralized, thread-safe data access service for the dashboard layer.

    Parameters
    ----------
    bill_repo : BillRepository, optional
    company_repo : CompanyRepository, optional
    decision_repo : DecisionRepository, optional
    report_repo : ReportRepository, optional
    mapping_repo : MappingRepository, optional
    explainability_repo : ExplainabilityRepository, optional
    backtest_repo : BacktestRepository, optional
    """

    def __init__(
        self,
        bill_repo: Optional[BillRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        decision_repo: Optional[DecisionRepository] = None,
        report_repo: Optional[ReportRepository] = None,
        mapping_repo: Optional[MappingRepository] = None,
        explainability_repo: Optional[ExplainabilityRepository] = None,
        backtest_repo: Optional[BacktestRepository] = None,
    ) -> None:
        self.bill_repo = bill_repo or BillRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.decision_repo = decision_repo or DecisionRepository()
        self.report_repo = report_repo or ReportRepository()
        self.mapping_repo = mapping_repo or MappingRepository()
        self.explainability_repo = explainability_repo or ExplainabilityRepository()
        self.backtest_repo = backtest_repo or BacktestRepository()

        # In-memory local caches
        self._cached_decisions: Optional[list[DecisionSupportRecord]] = None
        self._cached_dataframe: Optional[pd.DataFrame] = None
        self._cached_bills: Optional[list[Bill]] = None
        self._cached_companies: Optional[list[Company]] = None

    # ------------------------------------------------------------------
    # Master Metadata Loading
    # ------------------------------------------------------------------

    def get_bills(self) -> list[Bill]:
        """Return all bills from BillRepository."""
        if self._cached_bills is None:
            self._cached_bills = self.bill_repo.get_all()
        return self._cached_bills

    def get_production_bills(self) -> list[Bill]:
        """Return only valid production legislative bills (excluding test stubs)."""
        test_ids = {"key-issues-and-analysis", "service-bill"}
        return [b for b in self.get_bills() if b.bill_id not in test_ids]

    def get_companies(self) -> list[Company]:
        """Return all companies from CompanyRepository."""
        if self._cached_companies is None:
            self._cached_companies = self.company_repo.get_all()
        return self._cached_companies

    def get_company_by_isin(self, isin: str) -> Optional[Company]:
        """Return company record by ISIN."""
        for c in self.get_companies():
            if c.isin == isin:
                return c
        return None

    def get_bill_by_id(self, bill_id: str) -> Optional[Bill]:
        """Return bill record by bill_id."""
        for b in self.get_bills():
            if b.bill_id == bill_id:
                return b
        return None

    # ------------------------------------------------------------------
    # Decision Records & DataFrame
    # ------------------------------------------------------------------

    def get_decision_records(self) -> list[DecisionSupportRecord]:
        """Return all DecisionSupportRecord objects from DecisionRepository."""
        if self._cached_decisions is None:
            self._cached_decisions = self.decision_repo.load_all()
        return self._cached_decisions

    def get_decision_dataframe(self) -> pd.DataFrame:
        """
        Build and cache an enriched pandas DataFrame representing all decisions.

        Enriches decision records with company sector, sub-industry, name,
        and bill ministry / policy domain.
        """
        if self._cached_dataframe is not None:
            return self._cached_dataframe

        records = self.get_decision_records()
        if not records:
            empty_cols = [
                "decision_id",
                "bill_id",
                "company_isin",
                "event_window",
                "predicted_direction",
                "confidence",
                "market_moving_probability",
                "impact_score",
                "risk_score",
                "risk_category",
                "anticipation_evidence",
                "pricing_in_risk",
                "company_name",
                "ticker",
                "sector",
                "industry",
                "bill_title",
                "ministry",
                "policy_domain",
            ]
            self._cached_dataframe = pd.DataFrame(columns=empty_cols)
            return self._cached_dataframe

        # Create quick lookup dicts
        comp_map = {c.isin: c for c in self.get_companies()}
        bill_map = {b.bill_id: b for b in self.get_bills()}

        rows: list[dict[str, Any]] = []
        for r in records:
            c = comp_map.get(r.company_isin)
            b = bill_map.get(r.bill_id)

            pred_dir = getattr(r, "predicted_direction", "NEUTRAL")
            if hasattr(pred_dir, "value"):
                pred_dir = pred_dir.value

            conf = getattr(r, "predicted_confidence", getattr(r, "confidence", "LOW"))
            if hasattr(conf, "value"):
                conf = conf.value

            risk_sc = getattr(r, "risk_score", getattr(r, "composite_risk_score", 0.0))

            risk_cat = getattr(r, "risk_category", "MODERATE")
            if hasattr(risk_cat, "value"):
                risk_cat = risk_cat.value

            ant_ev = getattr(r, "anticipation_class", getattr(r, "anticipation_evidence", "NO_EVIDENCE"))
            if hasattr(ant_ev, "value"):
                ant_ev = ant_ev.value

            pr_risk = getattr(r, "pricing_in_risk", "MODERATE")
            if hasattr(pr_risk, "value"):
                pr_risk = pr_risk.value

            imp_str = getattr(r, "predicted_impact_strength", getattr(r, "impact_strength", "MEDIUM"))
            if hasattr(imp_str, "value"):
                imp_str = imp_str.value

            rows.append({
                "decision_id": r.decision_id,
                "bill_id": r.bill_id,
                "company_isin": r.company_isin,
                "event_window": r.event_window,
                "predicted_direction": str(pred_dir),
                "confidence": str(conf),
                "market_moving_probability": float(getattr(r, "market_moving_probability", 0.0)),
                "impact_score": float(getattr(r, "impact_score", 0.0)),
                "risk_score": float(risk_sc),
                "risk_category": str(risk_cat),
                "anticipation_evidence": str(ant_ev),
                "pricing_in_risk": str(pr_risk),
                "impact_strength": str(imp_str),
                # Enriched metadata
                "company_name": c.company_name if c else r.company_isin,
                "ticker": getattr(c, "ticker_nse", getattr(c, "ticker", "")) if c else "",
                "sector": c.sector if c else "Unknown",
                "industry": getattr(c, "industry", "Unknown") if c else "Unknown",
                "bill_title": b.title if b else r.bill_id,
                "ministry": getattr(b, "ministry", "Unknown") if b else "Unknown",
                "policy_domain": getattr(b, "policy_domain", (b.sectors[0] if getattr(b, "sectors", None) else "General")) if b else "Unknown",
            })

        df = pd.DataFrame(rows)
        self._cached_dataframe = df
        logger.info("Enriched decision dataframe assembled with %d rows", len(df))
        return df

    # ------------------------------------------------------------------
    # Reports Retrieval
    # ------------------------------------------------------------------

    def get_bill_report(self, bill_id: str) -> Optional[BillLevelReport]:
        """Load aggregated BillLevelReport."""
        try:
            if hasattr(self.report_repo, "load_bill_report"):
                return self.report_repo.load_bill_report(bill_id)
        except Exception:
            pass
        try:
            if hasattr(self.report_repo, "get_bill_report"):
                rpt_id = bill_id if bill_id.startswith("bill_rpt_") else f"bill_rpt_{bill_id}"
                return self.report_repo.get_bill_report(rpt_id)
        except Exception as exc:
            logger.debug("Failed to load bill report %s: %s", bill_id, exc)
        return None

    def get_company_report(self, company_isin: str) -> Optional[CompanyLevelReport]:
        """Load aggregated CompanyLevelReport."""
        try:
            if hasattr(self.report_repo, "load_company_report"):
                return self.report_repo.load_company_report(company_isin)
        except Exception:
            pass
        try:
            if hasattr(self.report_repo, "get_company_report"):
                rpt_id = company_isin if company_isin.startswith("co_rpt_") else f"co_rpt_{company_isin}"
                return self.report_repo.get_company_report(rpt_id)
        except Exception as exc:
            logger.debug("Failed to load company report %s: %s", company_isin, exc)
        return None

    def get_stakeholder_report(
        self, bill_id: str, company_isin: str, event_window: str, stakeholder_type: str
    ) -> Optional[StakeholderReport]:
        """Load specific StakeholderReport."""
        from schemas.report import StakeholderType
        try:
            stk_str = stakeholder_type.value if hasattr(stakeholder_type, "value") else str(stakeholder_type).upper()
            st_enum = StakeholderType(stk_str)
        except Exception:
            return None

        try:
            if hasattr(self.report_repo, "get"):
                try:
                    res = self.report_repo.get(bill_id, company_isin, event_window, st_enum)
                    if res is not None:
                        return res
                except (TypeError, ValueError):
                    pass
            if hasattr(self.report_repo, "get_by_key"):
                return self.report_repo.get_by_key(bill_id, company_isin, event_window, st_enum.value)
        except Exception as exc:
            logger.debug("Failed to fetch stakeholder report: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Explainability & Backtesting Retrieval
    # ------------------------------------------------------------------

    def get_global_explainability(self) -> dict[str, Any]:
        """Load global feature importance and summary from Task 6.3."""
        try:
            return self.explainability_repo.load_global_summary()
        except Exception as exc:
            logger.warning("Global explainability summary not found: %s", exc)
            return {}

    def get_model_comparison_explainability(self) -> dict[str, Any]:
        """Load model comparison data from Task 6.3."""
        try:
            return self.explainability_repo.load_model_comparison()
        except Exception as exc:
            logger.warning("Model comparison explainability not found: %s", exc)
            return {}

    def get_backtest_runs(self) -> list[str]:
        """List available historical backtest runs."""
        try:
            return self.backtest_repo.list_runs()
        except Exception as exc:
            logger.warning("Failed to list backtest runs: %s", exc)
            return []

    def get_backtest_data(self, run_id: str) -> dict[str, Any]:
        """Load all backtest artefacts for a given run ID."""
        try:
            return self.backtest_repo.load(run_id)
        except Exception as exc:
            logger.warning("Failed to load backtest run '%s': %s", run_id, exc)
            return {}

    def clear_cache(self) -> None:
        """Clear local in-memory caches."""
        self._cached_decisions = None
        self._cached_dataframe = None
        self._cached_bills = None
        self._cached_companies = None
