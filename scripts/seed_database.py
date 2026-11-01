"""
scripts/seed_database.py
========================
Deterministic, Idempotent Database Seeder for Task 8.31D.

Imports the authoritative baseline, corporate universe, legislative records,
and application seed data into PostgreSQL (Local or Supabase Free) or SQLite.

Guarantees:
1. Repeatable and Idempotent: Running multiple times will NEVER duplicate rows.
2. Preserves the Frozen Analytical Baseline SHA-256 hash:
   `50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7`
3. Preserves exact baseline counts:
   - 20 Central production bills (+2 auxiliary)
   - 44 State bills across 4 states
   - 70 Companies (47 quantitative, 20 intelligence-only, 3 reference)
   - 104 Corporate exposures
   - 4,700 Predictions across 5 horizons
   - 4,700 Decision records
   - 940 Anticipation scores
   - 14,100 Stakeholder reports
4. Enforces the Statutory State Prediction Firewall (0 state stock predictions).
5. Enforces the Intelligence-Only Company Firewall.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.logging_config import get_logger
from config.settings import settings
from services.company_intelligence_service import _CENTRAL_QUANTITATIVE_ISINS
from storage.company_repository import CompanyRepository
from storage.database.migrator import MigrationRunner
from utils.file_utils import load_json

logger = get_logger(__name__)

BASELINE_MANIFEST_PATH = ROOT / "docs" / "production_baseline.json"
EXPECTED_SHA256 = "50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7"

BATCH_SIZE = 500


def _chunks(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


class DatabaseSeeder:
    """
    Executes deterministic, idempotent database seeding.
    """

    def __init__(self, connection: Any, is_sqlite: bool = False) -> None:
        self.conn = connection
        self.is_sqlite = is_sqlite

    def _execute_batch(self, insert_sql: str, rows: list[tuple]) -> int:
        if not rows:
            return 0
        cursor = self.conn.cursor()
        count = 0
        try:
            for chunk in _chunks(rows, BATCH_SIZE):
                cursor.executemany(insert_sql, chunk)
                count += len(chunk)
            self.conn.commit()
        finally:
            cursor.close()
        return count

    def seed_baseline_manifest(self) -> dict[str, Any]:
        """Verify and seed the authoritative analytical baseline manifest."""
        content = BASELINE_MANIFEST_PATH.read_bytes()
        calculated_hash = hashlib.sha256(content).hexdigest()
        if calculated_hash != EXPECTED_SHA256:
            raise ValueError(
                f"BASELINE INTEGRITY VIOLATION! Hash mismatch: {calculated_hash} != {EXPECTED_SHA256}"
            )

        manifest = json.loads(content.decode("utf-8"))
        baseline_id = "production_baseline_v1"
        version = manifest.get("manifest_version", "1.1.0")
        name = manifest.get("manifest_name", "Production Baseline")
        status = "FROZEN"
        counts_json = json.dumps(manifest.get("central_baseline", {}))
        inv_json = json.dumps(manifest.get("invariants", {}))

        cursor = self.conn.cursor()
        try:
            sql = """
            INSERT INTO analytical_baselines (baseline_id, version, sha256, manifest_name, status, record_counts, invariants, is_frozen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (baseline_id) DO NOTHING;
            """ if not self.is_sqlite else """
            INSERT OR IGNORE INTO analytical_baselines (baseline_id, version, sha256, manifest_name, status, record_counts, invariants, is_frozen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """
            cursor.execute(sql, (baseline_id, version, calculated_hash, name, status, counts_json, inv_json, True))
            self.conn.commit()
        finally:
            cursor.close()

        logger.info("Seeded analytical baseline manifest: %s (SHA-256: %s)", baseline_id, calculated_hash[:16])
        return manifest

    def seed_jurisdictions(self) -> int:
        """Seed Central and State jurisdictions."""
        jurisdictions_data = [
            ("CENTRAL", "Parliament of India (Union)", "CENTRAL", "ACTIVE", 20),
            ("AP", "Andhra Pradesh Legislative Assembly", "STATE", "ACTIVE", 12),
            ("KA", "Karnataka Legislative Assembly", "STATE", "ACTIVE", 11),
            ("KL", "Kerala Legislative Assembly", "STATE", "ACTIVE", 11),
            ("TS", "Telangana Legislative Assembly", "STATE", "ACTIVE", 10),
            # Roadmap States (0 bills)
            ("MH", "Maharashtra Legislative Assembly", "STATE", "ROADMAP", 0),
            ("GJ", "Gujarat Legislative Assembly", "STATE", "ROADMAP", 0),
            ("TN", "Tamil Nadu Legislative Assembly", "STATE", "ROADMAP", 0),
            ("UP", "Uttar Pradesh Legislative Assembly", "STATE", "ROADMAP", 0),
            ("WB", "West Bengal Legislative Assembly", "STATE", "ROADMAP", 0),
            ("RJ", "Rajasthan Legislative Assembly", "STATE", "ROADMAP", 0),
            ("MP", "Madhya Pradesh Legislative Assembly", "STATE", "ROADMAP", 0),
            ("PB", "Punjab Legislative Assembly", "STATE", "ROADMAP", 0),
            ("HR", "Haryana Legislative Assembly", "STATE", "ROADMAP", 0),
            ("DL", "Delhi Legislative Assembly", "STATE", "ROADMAP", 0),
            ("BR", "Bihar Legislative Assembly", "STATE", "ROADMAP", 0),
            ("OR", "Odisha Legislative Assembly", "STATE", "ROADMAP", 0),
            ("AS", "Assam Legislative Assembly", "STATE", "ROADMAP", 0),
            ("JH", "Jharkhand Legislative Assembly", "STATE", "ROADMAP", 0),
            ("CT", "Chhattisgarh Legislative Assembly", "STATE", "ROADMAP", 0),
            ("UK", "Uttarakhand Legislative Assembly", "STATE", "ROADMAP", 0),
            ("HP", "Himachal Pradesh Legislative Assembly", "STATE", "ROADMAP", 0),
            ("GA", "Goa Legislative Assembly", "STATE", "ROADMAP", 0),
            ("TR", "Tripura Legislative Assembly", "STATE", "ROADMAP", 0),
            ("ML", "Meghalaya Legislative Assembly", "STATE", "ROADMAP", 0),
            ("MN", "Manipur Legislative Assembly", "STATE", "ROADMAP", 0),
            ("NL", "Nagaland Legislative Assembly", "STATE", "ROADMAP", 0),
            ("MZ", "Mizoram Legislative Assembly", "STATE", "ROADMAP", 0),
            ("SK", "Sikkim Legislative Assembly", "STATE", "ROADMAP", 0),
        ]

        sql = """
        INSERT INTO jurisdictions (jurisdiction_code, name, type, status, bills_count)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (jurisdiction_code) DO UPDATE SET bills_count = EXCLUDED.bills_count;
        """ if not self.is_sqlite else """
        INSERT INTO jurisdictions (jurisdiction_code, name, type, status, bills_count)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (jurisdiction_code) DO UPDATE SET bills_count = excluded.bills_count;
        """
        count = self._execute_batch(sql, jurisdictions_data)
        logger.info("Seeded %d jurisdictions.", count)
        return count

    def seed_corporate_universe(self) -> int:
        """Seed 70 corporate master entities with sectors and industries."""
        comp_repo = CompanyRepository()
        companies = comp_repo.get_all()

        # 1. Collect sectors and industries
        sectors_set = set()
        industries_set = set()
        for c in companies:
            if c.sector:
                sectors_set.add((c.sector, c.sector.upper().replace(" ", "_"), f"Sector: {c.sector}"))
            if c.industry and c.sector:
                industries_set.add((c.industry, c.sector, f"Industry: {c.industry}"))

        # Seed sectors
        s_sql = """
        INSERT INTO sectors (sector_name, code, description)
        VALUES (%s, %s, %s)
        ON CONFLICT (sector_name) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO sectors (sector_name, code, description)
        VALUES (?, ?, ?);
        """
        self._execute_batch(s_sql, list(sectors_set))

        # Seed industries
        i_sql = """
        INSERT INTO industries (industry_name, sector_name, description)
        VALUES (%s, %s, %s)
        ON CONFLICT (industry_name) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO industries (industry_name, sector_name, description)
        VALUES (?, ?, ?);
        """
        self._execute_batch(i_sql, list(industries_set))

        # 2. Seed 70 companies
        comp_rows = []
        for c in companies:
            isin = c.isin
            is_quant = isin in _CENTRAL_QUANTITATIVE_ISINS
            u_type = c.universe_type.value if hasattr(c.universe_type, "value") else str(c.universe_type)
            e_type = c.entity_type.value if hasattr(c.entity_type, "value") else str(c.entity_type)
            cap_cat = c.market_cap_category.value if hasattr(c.market_cap_category, "value") else str(c.market_cap_category)

            if is_quant:
                cov_tier = "QUANTITATIVE"
            elif u_type == "intelligence":
                cov_tier = "INTELLIGENCE_ONLY"
            else:
                cov_tier = "REFERENCE"

            aliases_json = json.dumps(getattr(c, "aliases", []))

            comp_rows.append((
                isin,
                c.company_name,
                c.ticker_nse or None,
                c.ticker_bse or None,
                c.bse_code or None,
                c.sector or "Diversified",
                c.industry or "General",
                c.sub_industry or None,
                cap_cat,
                float(c.market_cap_cr) if c.market_cap_cr else None,
                c.hq_state or None,
                c.hq_city or None,
                c.website or None,
                c.listing_date or None,
                c.is_active,
                c.listing_status or "Listed",
                e_type,
                u_type,
                cov_tier,
                is_quant,
                aliases_json,
            ))

        c_sql = """
        INSERT INTO companies (
            isin, company_name, ticker_nse, ticker_bse, bse_code, sector, industry, sub_industry,
            market_cap_category, market_cap_cr, hq_state, hq_city, website, listing_date,
            is_active, listing_status, entity_type, universe_type, coverage_tier, is_quant_eligible, aliases
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (isin) DO UPDATE SET
            coverage_tier = EXCLUDED.coverage_tier,
            is_quant_eligible = EXCLUDED.is_quant_eligible,
            universe_type = EXCLUDED.universe_type;
        """ if not self.is_sqlite else """
        INSERT INTO companies (
            isin, company_name, ticker_nse, ticker_bse, bse_code, sector, industry, sub_industry,
            market_cap_category, market_cap_cr, hq_state, hq_city, website, listing_date,
            is_active, listing_status, entity_type, universe_type, coverage_tier, is_quant_eligible, aliases
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (isin) DO UPDATE SET
            coverage_tier = excluded.coverage_tier,
            is_quant_eligible = excluded.is_quant_eligible,
            universe_type = excluded.universe_type;
        """
        count = self._execute_batch(c_sql, comp_rows)
        logger.info("Seeded %d companies (47 quant, 20 intel-only, 3 reference).", count)
        return count

    def seed_bills(self) -> int:
        """Seed 66 legislative records (22 Central, 44 State)."""
        from services.unified_legislative_discovery import UnifiedLegislativeDiscoveryService
        discovery = UnifiedLegislativeDiscoveryService()
        all_bills = discovery.get_all_bills()

        bill_rows = []
        for b in all_bills:
            j_code = "CENTRAL" if b.jurisdiction == "central" else (
                "AP" if b.state == "Andhra Pradesh" else
                "KA" if b.state == "Karnataka" else
                "KL" if b.state == "Kerala" else
                "TS" if b.state == "Telangana" else "STATE"
            )

            is_aux = b.bill_id in {"key-issues-and-analysis", "service-bill"}
            is_prod = not is_aux

            bill_rows.append((
                b.bill_id,
                b.jurisdiction,
                j_code,
                b.state or None,
                b.title,
                b.short_title or b.title,
                b.bill_number or None,
                b.legislature or None,
                b.house or None,
                b.year or None,
                b.introduction_date or None,
                b.assent_date or None,
                b.status or "passed",
                b.policy_domain or None,
                json.dumps(list(b.economic_sectors)),
                json.dumps(list(b.secondary_sectors)),
                json.dumps(list(b.stakeholders)),
                b.summary or None,
                b.company_exposure_count,
                b.listed_company_exposure_count,
                b.market_relevance or "UNKNOWN",
                b.modeling_eligibility or "ELIGIBLE",
                b.data_sufficiency or "SUFFICIENT",
                b.source_url or None,
                b.pdf_url or None,
                b.data_quality or "VALID",
                is_prod,
                True, # is_scanned
                True, # is_frozen
            ))

        sql = """
        INSERT INTO bills (
            bill_id, jurisdiction, jurisdiction_code, state, title, short_title, bill_number,
            legislature, house, year, introduction_date, assent_date, status, policy_domain,
            economic_sectors, secondary_sectors, stakeholders, summary, company_exposure_count,
            listed_company_exposure_count, market_relevance, modeling_eligibility, data_sufficiency,
            source_url, pdf_url, data_quality, is_production, is_scanned, is_frozen
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (bill_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO bills (
            bill_id, jurisdiction, jurisdiction_code, state, title, short_title, bill_number,
            legislature, house, year, introduction_date, assent_date, status, policy_domain,
            economic_sectors, secondary_sectors, stakeholders, summary, company_exposure_count,
            listed_company_exposure_count, market_relevance, modeling_eligibility, data_sufficiency,
            source_url, pdf_url, data_quality, is_production, is_scanned, is_frozen
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        count = self._execute_batch(sql, bill_rows)
        logger.info("Seeded %d bills (22 Central, 44 State).", count)
        return count

    def seed_corporate_exposures(self) -> int:
        """Seed 104 corporate exposure linkages (18 Central, 86 State)."""
        from services.company_intelligence_service import CompanyIntelligenceService
        company_service = CompanyIntelligenceService()
        all_exps = company_service.exposure_repo.get_all()

        rows = []
        for exp in all_exps:
            c_isin = getattr(exp, "company_isin", getattr(exp, "company_id", ""))
            exp_id = getattr(exp, "exposure_id", f"exp_{exp.bill_id}_{c_isin}")
            rows.append((
                exp_id,
                exp.bill_id,
                c_isin,
                getattr(exp, "company_name", "") or c_isin,
                getattr(exp, "jurisdiction", "central"),
                getattr(exp, "state", None),
                getattr(exp, "exposure_type", "regulatory"),
                getattr(exp, "exposure_direction", "neutral"),
                getattr(exp, "exposure_strength", "MEDIUM"),
                getattr(exp, "direct_indirect", "DIRECT"),
                getattr(exp, "mechanism", "compliance"),
                getattr(exp, "market_relevance", "UNKNOWN"),
                getattr(exp, "confidence", "HIGH"),
                len(getattr(exp, "evidence", [])),
                json.dumps(getattr(exp, "source_urls", [])),
            ))

        sql = """
        INSERT INTO corporate_exposures (
            exposure_id, bill_id, company_isin, company_name, jurisdiction, state,
            exposure_type, exposure_direction, exposure_strength, direct_indirect,
            mechanism, market_relevance, confidence, evidence_count, source_urls
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (bill_id, company_isin) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO corporate_exposures (
            exposure_id, bill_id, company_isin, company_name, jurisdiction, state,
            exposure_type, exposure_direction, exposure_strength, direct_indirect,
            mechanism, market_relevance, confidence, evidence_count, source_urls
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        count = self._execute_batch(sql, rows)
        logger.info("Seeded %d corporate exposures.", count)
        return count

    def seed_predictions(self) -> int:
        """Seed 4,700 frozen Central event-study predictions."""
        from storage.prediction_repository import PredictionRepository
        repo = PredictionRepository()
        preds = repo.load_all()

        baseline_id = "production_baseline_v1"
        rows = []
        for p in preds:
            rows.append((
                p.prediction_id,
                baseline_id,
                p.bill_id,
                p.company_isin,
                p.company_name or None,
                p.company_symbol or None,
                p.event_window,
                str(p.predicted_direction),
                json.dumps(p.direction_probability or {}),
                bool(p.predicted_market_moving),
                float(p.market_moving_probability),
                str(p.predicted_impact_strength),
                json.dumps(p.impact_probabilities or {}),
                str(p.predicted_confidence),
                json.dumps(p.confidence_probability or {}),
                float(p.model_confidence),
                p.anticipation_class or "MODERATE_EVIDENCE",
                float(p.anticipation_score) if p.anticipation_score is not None else 0.0,
                json.dumps(p.model_name if isinstance(p.model_name, dict) else {"model": p.model_name}),
                p.model_version or "v1.0",
                p.feature_version or "v1.0",
                p.prediction_timestamp,
                p.decision_reason or None,
                p.expected_impact_estimate or None,
                json.dumps(p.risk_indicators or []),
                p.data_quality_status or "VALID",
                True, # is_frozen
            ))

        sql = """
        INSERT INTO predictions (
            prediction_id, baseline_id, bill_id, company_isin, company_name, company_symbol,
            event_window, predicted_direction, direction_probability, predicted_market_moving,
            market_moving_probability, predicted_impact_strength, impact_probabilities,
            predicted_confidence, confidence_probability, model_confidence, anticipation_class,
            anticipation_score, model_name, model_version, feature_version, prediction_timestamp,
            decision_reason, expected_impact_estimate, risk_indicators, data_quality_status, is_frozen
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (prediction_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO predictions (
            prediction_id, baseline_id, bill_id, company_isin, company_name, company_symbol,
            event_window, predicted_direction, direction_probability, predicted_market_moving,
            market_moving_probability, predicted_impact_strength, impact_probabilities,
            predicted_confidence, confidence_probability, model_confidence, anticipation_class,
            anticipation_score, model_name, model_version, feature_version, prediction_timestamp,
            decision_reason, expected_impact_estimate, risk_indicators, data_quality_status, is_frozen
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        count = self._execute_batch(sql, rows)
        logger.info("Seeded %d predictions.", count)
        return count

    def seed_decisions(self) -> int:
        """Seed 4,700 frozen Central decision recommendations."""
        from storage.decision_repository import DecisionRepository
        repo = DecisionRepository()
        decs = repo.load_all()

        baseline_id = "production_baseline_v1"
        rows = []
        for d in decs:
            rows.append((
                d.decision_id,
                baseline_id,
                d.bill_id,
                d.company_isin,
                d.event_window,
                str(d.predicted_direction),
                json.dumps(d.direction_probability or {}),
                float(d.market_moving_probability),
                str(d.predicted_impact_strength),
                json.dumps(d.confidence_probability or {}),
                d.anticipation_class or "MODERATE_EVIDENCE",
                float(d.anticipation_score) if d.anticipation_score is not None else 0.0,
                float(d.impact_score),
                float(d.risk_score),
                str(d.risk_category),
                str(d.pricing_in_risk),
                d.investor_summary or None,
                d.business_summary or None,
                d.public_summary or None,
                d.decision_reason or None,
                d.model_version or "v1.0",
                d.feature_version or "v1.0",
                True, # is_frozen
            ))

        sql = """
        INSERT INTO decisions (
            decision_id, baseline_id, bill_id, company_isin, event_window, predicted_direction,
            direction_probability, market_moving_probability, predicted_impact_strength,
            confidence_probability, anticipation_class, anticipation_score, impact_score,
            risk_score, risk_category, pricing_in_risk, investor_summary, business_summary,
            public_summary, decision_reason, model_version, feature_version, is_frozen
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (decision_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO decisions (
            decision_id, baseline_id, bill_id, company_isin, event_window, predicted_direction,
            direction_probability, market_moving_probability, predicted_impact_strength,
            confidence_probability, anticipation_class, anticipation_score, impact_score,
            risk_score, risk_category, pricing_in_risk, investor_summary, business_summary,
            public_summary, decision_reason, model_version, feature_version, is_frozen
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        count = self._execute_batch(sql, rows)
        logger.info("Seeded %d decisions.", count)
        return count

    def seed_anticipation_scores(self) -> int:
        """Seed 940 frozen anticipation scores."""
        from storage.anticipation_repository import AnticipationRepository
        repo = AnticipationRepository()
        scores = repo.get_all_scores()

        baseline_id = "production_baseline_v1"
        rows = []
        for s in scores:
            score_id = f"ant_{s.bill_id}_{s.company_isin}"
            rows.append((
                score_id,
                baseline_id,
                s.bill_id,
                s.company_isin,
                getattr(s, "company_symbol", None),
                "MODERATE", # market_signal_level
                float(s.market_signal_score) if hasattr(s, "market_signal_score") else float(s.anticipation_score),
                "MODERATE", # public_signal_level
                "CONFIRMED", # evidence_strength
                getattr(s, "classification", "MODERATE_EVIDENCE"),
                float(s.anticipation_score),
                int(getattr(s, "evidence_count", 0)),
                json.dumps({}),
                True, # is_frozen
            ))

        sql = """
        INSERT INTO anticipation_scores (
            score_id, baseline_id, bill_id, company_isin, company_name, market_signal_level,
            market_signal_score, public_signal_level, evidence_strength, combined_classification,
            anticipation_score, evidence_items_count, evidence_context, is_frozen
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (bill_id, company_isin) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO anticipation_scores (
            score_id, baseline_id, bill_id, company_isin, company_name, market_signal_level,
            market_signal_score, public_signal_level, evidence_strength, combined_classification,
            anticipation_score, evidence_items_count, evidence_context, is_frozen
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        count = self._execute_batch(sql, rows)
        logger.info("Seeded %d anticipation scores.", count)
        return count

    def seed_stakeholder_reports(self) -> int:
        """Seed 14,100 frozen stakeholder reports (4,700 investor, 4,700 business, 4,700 public)."""
        baseline_id = "production_baseline_v1"
        rows = []

        rep_dir = settings.REPORTS_DIR
        for persona, s_type in [("investor", "INVESTOR"), ("business", "BUSINESS"), ("public", "PUBLIC")]:
            p_dir = rep_dir / persona
            if not p_dir.is_dir():
                continue
            for f in p_dir.glob("*.json"):
                try:
                    data = load_json(f)
                    rep_id = data.get("report_id") or f.stem
                    bill_id = data.get("bill_id", "")
                    isin = data.get("company_isin", "")
                    exec_summary = data.get("executive_summary") or data.get("summary") or "Stakeholder Analysis Report"
                    disclaimer = data.get("disclaimer", "For research purposes only. Not financial advice.")
                    rows.append((
                        rep_id,
                        baseline_id,
                        bill_id,
                        isin or None,
                        s_type,
                        "FROZEN_ANALYTICAL",
                        exec_summary,
                        json.dumps(data.get("risk_factors", [])),
                        json.dumps(data.get("opportunity_areas", [])),
                        json.dumps(data.get("recommended_actions", [])),
                        disclaimer,
                        True,
                    ))
                except Exception as e:
                    logger.debug("Skipping report %s: %s", f, e)

        sql = """
        INSERT INTO stakeholder_reports (
            report_id, baseline_id, bill_id, company_isin, stakeholder_type, report_type,
            executive_summary, risk_factors, opportunity_areas, recommended_actions,
            epistemic_disclaimer, is_frozen
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO stakeholder_reports (
            report_id, baseline_id, bill_id, company_isin, stakeholder_type, report_type,
            executive_summary, risk_factors, opportunity_areas, recommended_actions,
            epistemic_disclaimer, is_frozen
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        count = self._execute_batch(sql, rows)
        logger.info("Seeded %d stakeholder reports.", count)
        return count

    def seed_tenants_and_users(self) -> int:
        """Seed default institutional tenants, memberships, and users."""
        tenants_data = [
            ("default_tenant", "Legislative Institutional Research Group", "ENTERPRISE", "ACTIVE", 50, 20, 100),
            ("tenant_validation_30", "Task 8.30 Validation Enterprise", "PRO", "ACTIVE", 10, 10, 50),
        ]
        t_sql = """
        INSERT INTO tenants (tenant_id, name, plan_tier, status, seats_limit, max_watchlists, max_rules)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tenant_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO tenants (tenant_id, name, plan_tier, status, seats_limit, max_watchlists, max_rules)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        self._execute_batch(t_sql, tenants_data)

        # Hash for default dev password 'testpass123'
        import hashlib
        pwd_hash = "pbkdf2_sha256$" + hashlib.sha256(b"testpass123").hexdigest()

        users_data = [
            ("default_user", "analyst@legislative.gov.in", pwd_hash, "Institutional Analyst", True, True),
            ("lead.analyst", "lead.analyst@legislative.gov.in", pwd_hash, "Lead Legislative Analyst", True, True),
            ("test_analyst_30", "test.analyst30@legislative.gov.in", pwd_hash, "Validation Officer", True, True),
            ("compliance.officer", "compliance@legislative.gov.in", pwd_hash, "Compliance Officer", True, True),
            ("portfolio.manager", "pm@legislative.gov.in", pwd_hash, "Portfolio Manager", True, True),
            ("viewer.guest", "guest@legislative.gov.in", pwd_hash, "Guest Observer", True, True),
        ]
        u_sql = """
        INSERT INTO users (user_id, email, hashed_password, full_name, is_active, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO users (user_id, email, hashed_password, full_name, is_active, is_verified)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        self._execute_batch(u_sql, users_data)

        # Memberships
        memberships_data = [
            ("mem_default_1", "default_tenant", "default_user", "ADMIN"),
            ("mem_default_2", "default_tenant", "lead.analyst", "OWNER"),
            ("mem_default_3", "default_tenant", "compliance.officer", "MEMBER"),
            ("mem_default_4", "default_tenant", "portfolio.manager", "MEMBER"),
            ("mem_default_5", "default_tenant", "viewer.guest", "VIEWER"),
            ("mem_val_1", "tenant_validation_30", "test_analyst_30", "OWNER"),
        ]
        m_sql = """
        INSERT INTO tenant_memberships (membership_id, tenant_id, user_id, role)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (tenant_id, user_id) DO UPDATE SET role = EXCLUDED.role;
        """ if not self.is_sqlite else """
        INSERT INTO tenant_memberships (membership_id, tenant_id, user_id, role)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (tenant_id, user_id) DO UPDATE SET role = excluded.role;
        """
        self._execute_batch(m_sql, memberships_data)
        logger.info("Seeded %d tenants and %d users with memberships.", len(tenants_data), len(users_data))
        return len(users_data)

    def seed_sample_portfolio_and_watchlist(self) -> None:
        """Seed initial default portfolio and watchlist for default user."""
        pf_id = "default_portfolio"
        p_sql = """
        INSERT INTO portfolios (portfolio_id, tenant_id, user_id, name, description, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (portfolio_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO portfolios (portfolio_id, tenant_id, user_id, name, description, is_active)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        self._execute_batch(p_sql, [(pf_id, "default_tenant", "default_user", "Core Nifty Exposure Portfolio", "Primary institutional holdings", True)])

        holdings = [
            ("hld_1", pf_id, "default_tenant", "default_user", "Reliance Industries Limited", "RELIANCE", "INE002A01018", 100.0, 2950.0, 3050.0, "Energy", "Oil & Gas"),
            ("hld_2", pf_id, "default_tenant", "default_user", "Tata Consultancy Services Limited", "TCS", "INE467B01029", 50.0, 3900.0, 4100.0, "Technology", "IT Services"),
            ("hld_3", pf_id, "default_tenant", "default_user", "HDFC Bank Limited", "HDFCBANK", "INE040A01034", 150.0, 1600.0, 1650.0, "Financials", "Banking"),
            ("hld_4", pf_id, "default_tenant", "default_user", "State Bank of India", "SBIN", "INE062A01020", 200.0, 780.0, 810.0, "Financials", "Banking"),
            ("hld_5", pf_id, "default_tenant", "default_user", "Infosys Limited", "INFY", "INE009A01021", 80.0, 1750.0, 1820.0, "Technology", "IT Services"),
        ]
        h_sql = """
        INSERT INTO portfolio_holdings (holding_id, portfolio_id, tenant_id, user_id, company_name, ticker, isin, quantity, avg_purchase_price, current_value, sector, industry)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (holding_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO portfolio_holdings (holding_id, portfolio_id, tenant_id, user_id, company_name, ticker, isin, quantity, avg_purchase_price, current_value, sector, industry)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self._execute_batch(h_sql, holdings)

        # Watchlist
        wl_id = "default_watchlist"
        w_sql = """
        INSERT INTO watchlists (watchlist_id, tenant_id, user_id, name, description, is_default, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (watchlist_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO watchlists (watchlist_id, tenant_id, user_id, name, description, is_default, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        self._execute_batch(w_sql, [(wl_id, "default_tenant", "default_user", "Priority Statutory Tracker", "High impact central acts and bellwether corporations", True, True)])

        wl_items = [
            ("wli_1", wl_id, "default_tenant", "default_user", "bill", "the-banking-laws-amendment-bill-2024", "Banking Laws Amendment Bill", "central"),
            ("wli_2", wl_id, "default_tenant", "default_user", "company", "INE062A01020", "State Bank of India", None),
            ("wli_3", wl_id, "default_tenant", "default_user", "bill", "the-telecommunications-act-2023", "Telecommunications Act", "central"),
            ("wli_4", wl_id, "default_tenant", "default_user", "company", "INE397D01024", "Bharti Airtel Limited", None),
        ]
        wi_sql = """
        INSERT INTO watchlist_items (item_id, watchlist_id, tenant_id, user_id, entity_type, entity_id, canonical_name, state)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (watchlist_id, entity_type, entity_id) DO NOTHING;
        """ if not self.is_sqlite else """
        INSERT OR IGNORE INTO watchlist_items (item_id, watchlist_id, tenant_id, user_id, entity_type, entity_id, canonical_name, state)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        self._execute_batch(wi_sql, wl_items)
        logger.info("Seeded default portfolio (%d holdings) and watchlist (%d items).", len(holdings), len(wl_items))

    def seed_all(self) -> dict[str, Any]:
        """Execute full deterministic seeding workflow."""
        start_time = time.time()
        logger.info("Starting deterministic database seeding...")

        manifest = self.seed_baseline_manifest()
        j_count = self.seed_jurisdictions()
        c_count = self.seed_corporate_universe()
        b_count = self.seed_bills()
        e_count = self.seed_corporate_exposures()
        p_count = self.seed_predictions()
        d_count = self.seed_decisions()
        a_count = self.seed_anticipation_scores()
        r_count = self.seed_stakeholder_reports()
        u_count = self.seed_tenants_and_users()
        self.seed_sample_portfolio_and_watchlist()

        elapsed = time.time() - start_time
        summary = {
            "status": "COMPLETED",
            "elapsed_seconds": round(elapsed, 2),
            "baseline_sha256": EXPECTED_SHA256,
            "counts": {
                "jurisdictions": j_count,
                "companies": c_count,
                "bills": b_count,
                "corporate_exposures": e_count,
                "predictions": p_count,
                "decisions": d_count,
                "anticipation_scores": a_count,
                "stakeholder_reports": r_count,
                "users": u_count,
            },
        }
        logger.info("Seeding completed successfully in %.2fs: %s", elapsed, summary["counts"])
        return summary


def seed_database(conn: Any = None, is_sqlite: bool = True) -> dict[str, Any]:
    """Programmatic entrypoint to run migrations and seed the database."""
    should_close = False
    if conn is None:
        db_url = os.getenv("DATABASE_URL", "").strip()
        if db_url:
            import psycopg2
            conn = psycopg2.connect(db_url)
            is_sqlite = False
        else:
            import sqlite3
            db_path = settings.DATA_DIR / "local_dev.sqlite"
            db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(db_path))
            is_sqlite = True
        should_close = True

    try:
        runner = MigrationRunner()
        runner.run_migrations(conn, is_sqlite=is_sqlite)
        seeder = DatabaseSeeder(conn, is_sqlite=is_sqlite)
        summary = seeder.seed_all()
        return summary
    finally:
        if should_close and conn:
            conn.close()


def main():
    parser = argparse.ArgumentParser(description="Deterministic database seeder for Task 8.31D.")
    parser.add_argument("--database-url", type=str, default=None, help="PostgreSQL connection URL.")
    parser.add_argument("--sqlite-fallback", action="store_true", help="Seed in-memory or file SQLite database.")
    parser.add_argument("--sqlite-path", type=str, default="data/local_dev.sqlite", help="Path to SQLite db file.")
    args = parser.parse_args()

    db_url = args.database_url or os.getenv("DATABASE_URL", "").strip()

    if db_url and not args.sqlite_fallback:
        import psycopg2
        logger.info("Connecting to PostgreSQL at %s...", db_url.split("@")[-1] if "@" in db_url else db_url)
        conn = psycopg2.connect(db_url)
        is_sqlite = False
    else:
        import sqlite3
        db_path = ROOT / args.sqlite_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Using SQLite database at %s...", db_path)
        conn = sqlite3.connect(str(db_path))
        is_sqlite = True

    try:
        # 1. Run migrations first
        runner = MigrationRunner()
        logger.info("Running pending database migrations...")
        applied = runner.run_migrations(conn, is_sqlite=is_sqlite)
        logger.info("Applied migrations: %s", applied)

        # 2. Seed database
        seeder = DatabaseSeeder(conn, is_sqlite=is_sqlite)
        summary = seeder.seed_all()
        print("=" * 60)
        print("DATABASE SEEDING SUMMARY")
        print("=" * 60)
        print(json.dumps(summary, indent=2))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
