"""
storage/state_knowledge_repository.py
=====================================
Repository for Indian State legislative bill knowledge records.

Manages persistence, retrieval, and multi-attribute search for
`StateBillKnowledge` records in `data/state_bills/knowledge/`.
Maintains strict isolation from Central Government knowledge storage.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Optional

from config.logging_config import get_logger
from schemas.state_knowledge import StateBillKnowledge, StateBillSummary
from utils.file_utils import ensure_dir, file_exists, list_files, load_json, save_json
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)


class StateKnowledgeRepository:
    """
    Repository for storing, retrieving, and searching StateBillKnowledge records.
    """

    def __init__(self, knowledge_dir: Optional[Path] = None) -> None:
        """
        Initialize the State knowledge repository.

        Parameters
        ----------
        knowledge_dir : Path | None
            Directory to store knowledge records.
            Defaults to settings.STATE_BILLS_DIR / "knowledge".
        """
        from config.settings import settings

        if knowledge_dir is None:
            self._knowledge_dir = settings.STATE_BILLS_DIR / "knowledge"
        else:
            self._knowledge_dir = Path(knowledge_dir)

        ensure_dir(self._knowledge_dir)
        logger.debug("StateKnowledgeRepository initialized | dir=%s", self._knowledge_dir)

    @property
    def knowledge_dir(self) -> Path:
        return self._knowledge_dir

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, record: StateBillKnowledge) -> None:
        """Persist a single StateBillKnowledge record as JSON."""
        dest_path = self._knowledge_dir / f"{record.bill_id}.json"
        save_json(record.to_dict(), dest_path)
        logger.info("Saved state knowledge record: %s", record.bill_id)

    def save_many(self, records: list[StateBillKnowledge]) -> None:
        """Persist multiple StateBillKnowledge records."""
        for r in records:
            self.save(r)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, bill_id: str) -> Optional[StateBillKnowledge]:
        """Retrieve a StateBillKnowledge record by bill_id."""
        src_path = self._knowledge_dir / f"{bill_id}.json"
        if not file_exists(src_path):
            logger.debug("State knowledge record not found: %s", src_path)
            return None
        try:
            data = load_json(src_path)
            return StateBillKnowledge.from_dict(data)
        except Exception as exc:
            logger.error("Failed to load state knowledge record '%s': %s", bill_id, exc)
            return None

    def get_all(self) -> list[StateBillKnowledge]:
        """Return all stored StateBillKnowledge records."""
        records: list[StateBillKnowledge] = []
        try:
            files = list_files(self._knowledge_dir, "*.json")
            for f in files:
                rec = self.get(f.stem)
                if rec:
                    records.append(rec)
        except Exception as exc:
            logger.error("Failed to list state knowledge records: %s", exc)
        return records

    def get_by_state(self, state: str) -> list[StateBillKnowledge]:
        """Filter records by State name (case-insensitive, normalized)."""
        target_norm = normalize_state(state) or state.strip().lower()
        results = []
        for r in self.get_all():
            r_norm = normalize_state(r.state) or r.state.strip().lower()
            if r_norm.lower() == target_norm.lower():
                results.append(r)
        return results

    def get_by_category(self, category: str) -> list[StateBillKnowledge]:
        """Filter records by policy category (case-insensitive)."""
        c_lower = category.strip().lower()
        return [r for r in self.get_all() if r.policy_category.strip().lower() == c_lower]

    def get_by_stakeholder(self, stakeholder: str) -> list[StateBillKnowledge]:
        """Filter records by affected stakeholder group (case-insensitive substring match)."""
        sh_lower = stakeholder.strip().lower()
        results = []
        for r in self.get_all():
            if any(sh_lower in sh.lower() for sh in r.affected_stakeholders):
                results.append(r)
        return results

    # ------------------------------------------------------------------
    # Search & Discovery (Task 8.4 Part 10)
    # ------------------------------------------------------------------

    def search(
        self,
        query: str = "",
        state: Optional[str | list[str]] = None,
        chamber: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
        policy_category: Optional[str] = None,
        stakeholder: Optional[str] = None,
        keyword: Optional[str] = None,
        states: Optional[list[str]] = None,
        primary_sector: Optional[str] = None,
        secondary_sector: Optional[str] = None,
        business_type: Optional[str] = None,
        company_readiness: Optional[str] = None,
        geographic_scope: Optional[str] = None,
        impact_mechanism: Optional[str] = None,
        company_id: Optional[str] = None,
        company_ticker: Optional[str] = None,
        has_corporate_exposure: Optional[bool] = None,
        economic_strength: Optional[str] = None,
        economic_direction: Optional[str] = None,
        market_relevance: Optional[str] = None,
        modeling_eligibility: Optional[str] = None,
        data_sufficiency: Optional[str] = None,
        economic_mechanism: Optional[str] = None,
    ) -> list[StateBillKnowledge]:
        """
        Multi-attribute search across State knowledge records.
        Supports sector, stakeholder, corporate exposure, and economic/market impact filters.
        """
        all_records = self.get_all()
        results: list[StateBillKnowledge] = []

        q = query.strip().lower() if query else ""

        # Normalize state filter(s)
        target_states: set[str] = set()
        if states:
            for s in states:
                ns = (normalize_state(s) or s).strip().lower()
                if ns:
                    target_states.add(ns)
        elif state:
            if isinstance(state, list):
                for s in state:
                    ns = (normalize_state(s) or s).strip().lower()
                    if ns:
                        target_states.add(ns)
            else:
                ns = (normalize_state(state) or state).strip().lower()
                if ns:
                    target_states.add(ns)

        # Detect implicit state filter in natural query if not provided
        if not target_states and q:
            for known_st in ["andhra pradesh", "karnataka", "kerala", "telangana"]:
                if f"in {known_st}" in q or f"{known_st} " in q or q.endswith(known_st) or f"{known_st} bills" in q:
                    norm = (normalize_state(known_st) or known_st).strip().lower()
                    target_states.add(norm)
                    break

        # Detect natural language concepts for Task 8.8
        target_estrength = economic_strength.strip().lower() if economic_strength else None
        target_edirection = economic_direction.strip().lower() if economic_direction else None
        target_mrelevance = market_relevance.strip().lower() if market_relevance else None
        target_eligibility = modeling_eligibility.strip().lower() if modeling_eligibility else None
        target_dsufficiency = data_sufficiency.strip().lower() if data_sufficiency else None
        target_emech = economic_mechanism.strip().lower() if economic_mechanism else None
        target_has_corp = has_corporate_exposure

        if q:
            if "high economic impact" in q:
                target_estrength = "high"
                q = q.replace("high economic impact", "").strip()
            if "listed-company exposure" in q:
                target_has_corp = True
                q = q.replace("listed-company exposure", "").strip()
            elif "corporate exposure" in q:
                target_has_corp = True
                q = q.replace("corporate exposure", "").strip()
            if "eligible for future market modeling" in q:
                target_eligibility = "eligible"
                q = q.replace("eligible for future market modeling", "").strip()
            elif "eligible for market modeling" in q:
                target_eligibility = "eligible"
                q = q.replace("eligible for market modeling", "").strip()
            elif "eligible for modeling" in q:
                target_eligibility = "eligible"
                q = q.replace("eligible for modeling", "").strip()
            if "insufficient market data" in q:
                target_dsufficiency = "insufficient"
                q = q.replace("insufficient market data", "").strip()
            elif "insufficient data" in q:
                target_dsufficiency = "insufficient"
                q = q.replace("insufficient data", "").strip()
            if "high market relevance" in q:
                target_mrelevance = "high"
                q = q.replace("high market relevance", "").strip()
            if "economic-only" in q:
                target_mrelevance = "none"
                q = q.replace("economic-only", "").strip()
            elif "economic only" in q:
                target_mrelevance = "none"
                q = q.replace("economic only", "").strip()

        target_chamber = chamber.strip().lower() if chamber else None
        target_status = status.strip().lower() if status else None
        target_cat = policy_category.strip().lower() if policy_category else None
        target_sh = stakeholder.strip().lower() if stakeholder else None
        target_kw = keyword.strip().lower() if keyword else None
        target_psec = primary_sector.strip().lower() if primary_sector else None
        target_ssec = secondary_sector.strip().lower() if secondary_sector else None
        target_btype = business_type.strip().lower() if business_type else None
        target_readiness = company_readiness.strip().lower() if company_readiness else None
        target_geo = geographic_scope.strip().lower() if geographic_scope else None
        target_mech = impact_mechanism.strip().lower() if impact_mechanism else None

        # Stopwords for conceptual queries
        query_stopwords = {"bill", "bills", "in", "across", "states", "state", "the", "of", "and", "affecting", "for", "with"}
        query_terms = [t for t in re.findall(r"\w+", q) if t not in query_stopwords] if q else []

        for r in all_records:
            # 1. State filter (multi-state support)
            r_state = (normalize_state(r.state) or r.state).strip().lower()
            if target_states and r_state not in target_states:
                continue

            # 2. Chamber filter
            if target_chamber and r.chamber.strip().lower() != target_chamber:
                continue

            # 3. Year filter
            if year is not None and r.year != year:
                continue

            # 4. Status filter
            if target_status and r.status.strip().lower() != target_status:
                continue

            # 5. Category filter
            if target_cat and r.policy_category.strip().lower() != target_cat:
                continue

            # 6. Stakeholder filter
            if target_sh:
                has_sh = any(target_sh in sh.lower() for sh in r.affected_stakeholders)
                if not has_sh and r.economic_profile:
                    ep_sh = [s.stakeholder.lower() if hasattr(s, "stakeholder") else s.get("stakeholder", "").lower() for s in (r.economic_profile.stakeholders if hasattr(r.economic_profile, "stakeholders") else r.economic_profile.get("stakeholders", []))]
                    has_sh = any(target_sh in sh for sh in ep_sh)
                if not has_sh:
                    continue

            # 7. Keyword filter
            if target_kw:
                text_to_search = (
                    f"{r.title} {r.bill_number} {' '.join(r.key_provisions)} "
                    f"{' '.join(r.amended_acts)} {r.objective or ''}"
                ).lower()
                if target_kw not in text_to_search:
                    continue

            # 8. Economic Profile attribute filters
            ep = r.economic_profile
            ep_dict = ep.to_dict() if hasattr(ep, "to_dict") else (ep if isinstance(ep, dict) else {})

            if target_psec:
                p_sec = (ep_dict.get("primary_sector") or "").lower()
                if target_psec not in p_sec:
                    continue

            if target_ssec:
                s_secs = [s.lower() for s in ep_dict.get("secondary_sectors", [])]
                if not any(target_ssec in s for s in s_secs):
                    continue

            if target_btype:
                b_types = [b.lower() for b in ep_dict.get("business_types", [])]
                if not any(target_btype in b for b in b_types):
                    continue

            if target_readiness:
                r_val = (ep_dict.get("company_exposure_readiness") or "").lower()
                if target_readiness != r_val:
                    continue

            if target_geo:
                g_val = (ep_dict.get("geographic_scope") or "").lower()
                if target_geo not in g_val:
                    continue

            if target_mech:
                mechs = [m.lower() for m in ep_dict.get("impact_mechanisms", [])]
                if not any(target_mech in m for m in mechs):
                    continue

            # 9. Corporate Exposure filters (Task 8.7)
            exps = r.corporate_exposures or []
            if has_corporate_exposure is True and not exps:
                continue
            if has_corporate_exposure is False and exps:
                continue
            if target_has_corp is True and not exps:
                continue
            if target_has_corp is False and exps:
                continue
            if company_id:
                cid = company_id.strip().lower()
                if not any(
                    (e.company_id.lower() == cid if hasattr(e, "company_id") else e.get("company_id", "").lower() == cid)
                    for e in exps
                ):
                    continue
            if company_ticker:
                ctick = company_ticker.strip().upper()
                if not any(
                    (e.ticker.upper() == ctick if hasattr(e, "ticker") else e.get("ticker", "").upper() == ctick)
                    for e in exps
                ):
                    continue

            # 10. Impact Assessment attribute filters (Task 8.8)
            ia = r.impact_assessment
            ia_dict = ia.to_dict() if hasattr(ia, "to_dict") else (ia if isinstance(ia, dict) else {})

            if target_estrength:
                i_str = (ia_dict.get("economic_strength") or "").lower()
                if target_estrength != i_str:
                    continue

            if target_edirection:
                i_dir = (ia_dict.get("economic_direction") or "").lower()
                if target_edirection != i_dir:
                    continue

            if target_mrelevance:
                i_rel = (ia_dict.get("market_relevance") or "").lower()
                if target_mrelevance != i_rel:
                    continue

            if target_eligibility:
                i_elig = (ia_dict.get("modeling_eligibility") or "").lower()
                if target_eligibility == "eligible":
                    if i_elig not in ["eligible", "conditionally_eligible"]:
                        continue
                elif target_eligibility != i_elig:
                    continue

            if target_dsufficiency:
                i_suff = (ia_dict.get("data_sufficiency") or "").lower()
                if target_dsufficiency != i_suff:
                    continue

            if target_emech:
                i_mechs = [m.lower() for m in ia_dict.get("economic_mechanisms", [])]
                if not any(target_emech in m for m in i_mechs):
                    continue

            # 11. Free text query
            if query_terms:
                summary_text = (
                    f"{r.summary.what_is_bill} {r.summary.what_it_changes} "
                    f"{r.summary.why_it_matters} {r.summary.who_is_affected}"
                ) if isinstance(r.summary, StateBillSummary) or hasattr(r.summary, "what_is_bill") else str(r.summary)

                ep_text = ""
                if ep_dict:
                    ep_sh_names = " ".join(
                        s.get("stakeholder", "") if isinstance(s, dict) else (s.stakeholder if hasattr(s, "stakeholder") else str(s))
                        for s in ep_dict.get("stakeholders", [])
                    )
                    ep_text = (
                        f"{ep_dict.get('primary_sector', '')} {' '.join(ep_dict.get('secondary_sectors', []))} "
                        f"{' '.join(ep_dict.get('sub_sectors', []))} {' '.join(ep_dict.get('business_types', []))} "
                        f"{ep_dict.get('geographic_scope', '')} {ep_dict.get('company_exposure_readiness', '')} "
                        f"{ep_sh_names} {' '.join(ep_dict.get('direct_impacts', []))} {' '.join(ep_dict.get('indirect_impacts', []))}"
                    )

                corp_text = ""
                if exps:
                    corp_text = " ".join(
                        f"{e.company_name} {e.ticker} {e.business_activity} {e.exposure_type}"
                        if hasattr(e, "company_name")
                        else f"{e.get('company_name', '')} {e.get('ticker', '')} {e.get('business_activity', '')} {e.get('exposure_type', '')}"
                        for e in exps
                    )

                ia_text = ""
                if ia_dict:
                    ia_text = (
                        f"economic impact {ia_dict.get('economic_strength', '')} "
                        f"direction {ia_dict.get('economic_direction', '')} "
                        f"market relevance {ia_dict.get('market_relevance', '')} "
                        f"modeling eligibility {ia_dict.get('modeling_eligibility', '')} "
                        f"{' '.join(ia_dict.get('economic_mechanisms', []))} "
                        f"data sufficiency {ia_dict.get('data_sufficiency', '')}"
                    )

                searchable_corpus = (
                    f"{r.title} {r.bill_number} {r.bill_id} {r.state} {r.policy_category} "
                    f"{r.objective or ''} {' '.join(r.key_provisions)} "
                    f"{' '.join(r.amended_acts)} {' '.join(r.affected_stakeholders)} "
                    f"{summary_text} {ep_text} {corp_text} {ia_text}"
                ).lower()

                # Direct substring match
                if q and q in searchable_corpus:
                    results.append(r)
                    continue

                # Conceptual multi-term match
                if all(term in searchable_corpus for term in query_terms):
                    results.append(r)
                    continue

                # Stemmed stakeholder match (e.g. 'farmers' -> 'farmer', 'employers' -> 'employer')
                stemmed_terms = [t.rstrip("s") for t in query_terms]
                if all(st in searchable_corpus for st in stemmed_terms):
                    results.append(r)
                    continue

                continue

            results.append(r)

        return results

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def exists(self, bill_id: str) -> bool:
        """Return True if a knowledge record for bill_id exists."""
        return file_exists(self._knowledge_dir / f"{bill_id}.json")

    def delete(self, bill_id: str) -> None:
        """Delete a knowledge record."""
        p = self._knowledge_dir / f"{bill_id}.json"
        if file_exists(p):
            os.remove(p)
            logger.info("Deleted state knowledge record: %s", bill_id)

    def count(self) -> int:
        """Return the count of stored state knowledge records."""
        try:
            return len(list_files(self._knowledge_dir, "*.json"))
        except Exception:
            return 0

    def __repr__(self) -> str:
        return f"<StateKnowledgeRepository dir={self._knowledge_dir!r} count={self.count()}>"
