"""
knowledge/engine.py
===================
Deterministic Rule Engine for Legislative Knowledge Layer.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from knowledge.loader import (
    get_bill_category,
    get_ministry_sectors,
    get_policy_keywords,
    get_sector_keywords,
    list_ministries,
    list_sectors,
)
from schemas.bill import Bill
from schemas.knowledge_record import KnowledgeRecord

logger = get_logger(__name__)

_KNOWLEDGE_DIR = Path(__file__).resolve().parent


def count_keyword_hits(text: str, keywords: list[str]) -> int:
    """Count the total number of keyword hits in a text."""
    if not text or not keywords:
        return 0
    import re

    text_lower = text.lower()
    count = 0
    for kw in keywords:
        kw_clean = kw.strip().lower()
        if kw_clean:
            # Use word boundaries to match exact keyword as a word
            pattern = r"\b" + re.escape(kw_clean) + r"\b"
            count += len(re.findall(pattern, text_lower))
    return count


class RuleEngine:
    """
    Deterministic rule engine that maps a Bill and its extracted corpus text
    to a structured KnowledgeRecord using human-editable lookup tables.
    """

    def __init__(self) -> None:
        self._load_rules()

    def _read_csv(self, filename: str) -> list[dict[str, str]]:
        path = _KNOWLEDGE_DIR / filename
        if not path.is_file():
            logger.warning("Rule engine file not found: %s", path)
            return []
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def _load_rules(self) -> None:
        # Load ministry mappings
        self.ministry_mappings = {}
        for row in self._read_csv("ministry_mappings.csv"):
            raw = row.get("raw_name", "").strip().lower()
            canonical = row.get("canonical_name", "").strip()
            if raw and canonical:
                self.ministry_mappings[raw] = canonical

        # Load sector domain mapping
        self.sector_domain_mapping = {}
        for row in self._read_csv("sector_domain_mapping.csv"):
            sector = row.get("sector", "").strip()
            if sector:
                stakeholders_raw = row.get("default_stakeholder_groups", "")
                self.sector_domain_mapping[sector.lower()] = {
                    "sector": sector,
                    "policy_domain": row.get("policy_domain", "").strip(),
                    "economic_domain": row.get("economic_domain", "").strip(),
                    "regulatory_authority": row.get("regulatory_authority", "").strip(),
                    "default_stakeholder_groups": [
                        s.strip() for s in stakeholders_raw.split(",") if s.strip()
                    ],
                }

        # Load geographic scope rules
        self.geographic_scope_rules = []
        for row in self._read_csv("geographic_scope_rules.csv"):
            kw = row.get("keyword", "").strip().lower()
            scope = row.get("scope", "").strip()
            if kw and scope:
                self.geographic_scope_rules.append((kw, scope))

        # Load bill type rules
        self.bill_type_rules = []
        for row in self._read_csv("bill_type_rules.csv"):
            kw = row.get("keyword", "").strip().lower()
            b_type = row.get("bill_type", "").strip()
            if kw and b_type:
                self.bill_type_rules.append((kw, b_type))

        # Load department rules
        self.department_rules = []
        for row in self._read_csv("departments.csv"):
            m = row.get("ministry", "").strip().lower()
            s = row.get("sector", "").strip().lower()
            dept = row.get("department", "").strip()
            if m and s and dept:
                self.department_rules.append(
                    {
                        "ministry": m,
                        "sector": s,
                        "department": dept,
                    }
                )

        # Load taxonomy hierarchy
        self.taxonomy_hierarchy = []
        self.hierarchy_children = {}
        for row in self._read_csv("taxonomy_hierarchy.csv"):
            parent = row.get("parent", "").strip()
            child = row.get("child", "").strip()
            level = row.get("level", "").strip()
            if parent and child:
                self.taxonomy_hierarchy.append(
                    {
                        "parent": parent,
                        "child": child,
                        "level": level,
                    }
                )
                self.hierarchy_children.setdefault(parent.lower(), []).append(child)

    def traverse_hierarchy(self, start_node: str) -> list[str]:
        """
        Recursively traverse parent-to-child relationships to find
        all downstream/descendant nodes in the taxonomy.
        """
        visited = []
        stack = [start_node.lower()]
        while stack:
            node = stack.pop()
            children = self.hierarchy_children.get(node, [])
            for child in children:
                child_lower = child.lower()
                if child_lower not in [v.lower() for v in visited]:
                    visited.append(child)
                    stack.append(child_lower)
        return visited

    def generate_record(self, bill: Bill) -> KnowledgeRecord:
        """
        Generate a KnowledgeRecord for a Bill using the rule engine lookup tables.
        """
        logger.debug("Generating knowledge record for bill: %s", bill.bill_id)

        # 1. Sponsoring Ministry normalisation
        raw_ministry = bill.ministry.strip()
        canonical_ministry = self.ministry_mappings.get(raw_ministry.lower(), raw_ministry)
        if not canonical_ministry:
            canonical_ministry = "Unknown Ministry"

        # 2. Extract or load text corpus
        corpus_text = ""
        if bill.text_path and os.path.exists(bill.text_path):
            try:
                with open(bill.text_path, "r", encoding="utf-8") as f:
                    corpus_text = f.read()
            except Exception as e:
                logger.error("Failed to read text from %s: %s", bill.text_path, e)

        if not corpus_text and bill.full_text:
            corpus_text = bill.full_text

        # Combined text for keyword matching (title + summary + full corpus text)
        combined_text = f"{bill.title}\n{bill.summary}\n{corpus_text}"

        # 3. Match Category using bill_categories.csv keyword rules
        category_match = get_bill_category(bill.title)

        # 4. Resolve Primary Sector
        primary_sector = ""
        if category_match:
            primary_sector = category_match.get("primary_sector", "").strip()

        # Fallback to sponsoring ministry default primary sector
        if not primary_sector:
            ministry_sectors = get_ministry_sectors(canonical_ministry)
            if ministry_sectors:
                primary_sector = ministry_sectors[0]

        # Fallback to highest keyword frequency
        if not primary_sector:
            max_hits = -1
            best_sector = "All Sectors"
            for sector in list_sectors():
                kws = get_sector_keywords(sector)
                hits = count_keyword_hits(combined_text, kws)
                if hits > max_hits and hits > 0:
                    max_hits = hits
                    best_sector = sector
            primary_sector = best_sector

        # 5. Resolve Secondary Sector(s)
        secondary_sectors = []

        # Add from category match
        if category_match:
            sec_raw = category_match.get("secondary_sectors", "")
            if sec_raw:
                secondary_sectors.extend([s.strip() for s in sec_raw.split(",") if s.strip()])

        # Add from ministry sectors (excluding primary)
        ministry_sectors = get_ministry_sectors(canonical_ministry)
        if len(ministry_sectors) > 1:
            secondary_sectors.extend(ministry_sectors[1:])

        # Apply rule engine taxonomy chains: traverse hierarchy to find activated nodes
        hierarchy_nodes = []
        # Traverse down from ministry name
        hierarchy_nodes.extend(self.traverse_hierarchy(canonical_ministry))
        # Traverse down from primary sector name
        hierarchy_nodes.extend(self.traverse_hierarchy(primary_sector))

        # Check which hierarchy nodes are mentioned in the text
        for node in hierarchy_nodes:
            node_lower = node.lower()
            is_node_sector = any(s.lower() == node_lower for s in list_sectors())

            node_activated = False
            # Check for direct keyword mention of the node
            if node_lower in combined_text.lower():
                node_activated = True
            # Or if it is a sector, check if it has multiple keyword hits
            elif is_node_sector:
                kws = get_sector_keywords(node)
                if count_keyword_hits(combined_text, kws) >= 3:
                    node_activated = True

            if node_activated:
                if is_node_sector:
                    if node != primary_sector and node not in secondary_sectors:
                        secondary_sectors.append(node)

        # De-duplicate secondary sectors and filter out primary
        secondary_sectors = list(dict.fromkeys(secondary_sectors))
        if primary_sector in secondary_sectors:
            secondary_sectors.remove(primary_sector)

        # 6. Policy Domain, Economic Domain, Regulatory Authority & default stakeholders
        policy_domain = "Unknown Policy Domain"
        economic_domain = "Unknown Economic Domain"
        regulatory_authority = "Unknown Regulatory Authority"
        default_stakeholders = []

        domain_map = self.sector_domain_mapping.get(primary_sector.lower())
        if domain_map:
            policy_domain = domain_map["policy_domain"]
            economic_domain = domain_map["economic_domain"]
            regulatory_authority = domain_map["regulatory_authority"]
            default_stakeholders = domain_map["default_stakeholder_groups"]

        # Dynamic regulatory authority override for Governance & Public Administration
        if primary_sector == "Governance & Public Administration":
            text_lower = combined_text.lower()
            if canonical_ministry == "Ministry of Law and Justice":
                if (
                    "election" in text_lower
                    or "constituencies" in text_lower
                    or "representation" in text_lower
                ):
                    regulatory_authority = "Election Commission of India (ECI)"
                else:
                    regulatory_authority = "Ministry of Law and Justice"
            elif canonical_ministry == "Ministry of Home Affairs":
                if "disaster" in text_lower or "crisis" in text_lower:
                    regulatory_authority = "National Disaster Management Authority (NDMA)"
                else:
                    regulatory_authority = "Ministry of Home Affairs"
            elif canonical_ministry == "Ministry of Minority Affairs":
                if "waqf" in text_lower:
                    regulatory_authority = "Central Waqf Council"
                else:
                    regulatory_authority = "Ministry of Minority Affairs"
            elif canonical_ministry == "Ministry of Tribal Affairs":
                regulatory_authority = "Ministry of Tribal Affairs"
            elif canonical_ministry == "Ministry of Personnel Public Grievances and Pensions":
                regulatory_authority = "Ministry of Personnel, Public Grievances and Pensions"

        # 7. Sponsoring Department
        department = "Unknown Department"
        # Find matching specific ministry & sector rule first
        for rule in self.department_rules:
            if (
                rule["ministry"] == canonical_ministry.lower()
                and rule["sector"] == primary_sector.lower()
            ):
                department = rule["department"]
                break
        else:
            # Fallback to wildcard sector for that ministry
            for rule in self.department_rules:
                if rule["ministry"] == canonical_ministry.lower() and rule["sector"] == "*":
                    department = rule["department"]
                    break

        # 8. Geographic Scope
        geographic_scope = "National"
        # Check title and summary first
        for keyword, scope in self.geographic_scope_rules:
            if keyword in f"{bill.title}\n{bill.summary}".lower():
                geographic_scope = scope
                break
        else:
            # Search entire corpus
            for keyword, scope in self.geographic_scope_rules:
                if keyword in corpus_text.lower():
                    geographic_scope = scope
                    break

        # 9. Bill Type
        bill_type = "Ordinary Bill"
        for keyword, b_type in self.bill_type_rules:
            if keyword in bill.title.lower():
                bill_type = b_type
                break

        # 10. Keyword tagging
        keywords_list = []
        # Policy keywords
        for policy in get_policy_keywords():
            p_kws = [k.strip() for k in policy.get("keywords", "").split(",") if k.strip()]
            for kw in p_kws:
                # Basic substring check with space boundaries to avoid mid-word matches
                if f" {kw.lower()} " in f" {combined_text.lower()} ":
                    keywords_list.append(kw)

        # Sector keywords
        active_sectors = [primary_sector] + secondary_sectors
        for sector in active_sectors:
            s_kws = get_sector_keywords(sector)
            for kw in s_kws:
                if f" {kw.lower()} " in f" {combined_text.lower()} ":
                    keywords_list.append(kw)

        keywords_list = list(dict.fromkeys(keywords_list))

        # 11. Related Acts Extraction (regex + metadata)
        related_acts = list(bill.related_acts)
        act_pattern = re.compile(
            r"\b([A-Z][a-zA-Z0-9\-\(\)]*(?:\s+(?:of|and|for|in|by|to|on|the|a|an)\s+[A-Z][a-zA-Z0-9\-\(\)]*|\s+[A-Z][a-zA-Z0-9\-\(\)]*)*\s+Act(?:,\s+\d{4})?)\b"
        )
        matches = act_pattern.findall(combined_text)
        for match in matches:
            clean_act = " ".join(match.strip().split())
            # Skip invalid matches like pronouns, short strings, or single-word "Act"
            if clean_act.lower().startswith(
                ("this act", "the act", "a act", "an act", "any act", "such act")
            ):
                continue
            if len(clean_act.split()) < 2:
                continue
            if "bill" in clean_act.lower() or "amend" in clean_act.lower():
                continue
            # Discard matches with unbalanced parentheses (e.g. fragments matching inside brackets)
            if clean_act.count("(") != clean_act.count(")"):
                continue
            if clean_act not in related_acts:
                related_acts.append(clean_act)
        related_acts = list(dict.fromkeys(related_acts))

        # 12. Related Ministries
        related_ministries = []
        # Add ministries that regulate secondary sectors
        for sec_sector in secondary_sectors:
            for r_ministry in list_ministries():
                r_sectors = get_ministry_sectors(r_ministry)
                if sec_sector in r_sectors and r_ministry != canonical_ministry:
                    if r_ministry not in related_ministries:
                        related_ministries.append(r_ministry)

        # Scan text for other ministry mentions
        for r_ministry in list_ministries():
            if r_ministry != canonical_ministry and r_ministry.lower() in combined_text.lower():
                if r_ministry not in related_ministries:
                    related_ministries.append(r_ministry)

        # 13. Stakeholder Groups
        stakeholders = list(default_stakeholders)
        # Check text for mentions of secondary sector stakeholders
        for sec_sector in secondary_sectors:
            sec_map = self.sector_domain_mapping.get(sec_sector.lower())
            if sec_map:
                for sh in sec_map["default_stakeholder_groups"]:
                    if sh not in stakeholders and sh.lower() in combined_text.lower():
                        stakeholders.append(sh)
        stakeholders = list(dict.fromkeys(stakeholders))

        # 14. Confidence Score (rule-based)
        confidence = 0.0
        if (
            canonical_ministry != "Unknown Ministry"
            and raw_ministry.lower() in self.ministry_mappings
        ):
            confidence += 0.25
        if category_match:
            confidence += 0.20
        if primary_sector in get_ministry_sectors(canonical_ministry):
            confidence += 0.15
        primary_keywords = get_sector_keywords(primary_sector)
        if count_keyword_hits(combined_text, primary_keywords) >= 3:
            confidence += 0.15
        if (
            regulatory_authority != "Unknown Regulatory Authority"
            and regulatory_authority.lower() in combined_text.lower()
        ):
            confidence += 0.10
        if department != "Unknown Department":
            confidence += 0.05
        if len(related_acts) > 0:
            confidence += 0.10

        # Apply fallback mapping penalties
        if primary_sector in ["All Sectors", "Unknown Sector"]:
            confidence -= 0.15
        if department == "Unknown Department":
            confidence -= 0.05
        if policy_domain in ["Unknown Policy Domain", "Corporate Regulation"]:
            if canonical_ministry != "Ministry of Corporate Affairs":
                confidence -= 0.10

        confidence = max(0.0, min(1.0, round(confidence, 2)))

        # 15. Searchable Tags
        searchable_tags = []
        searchable_tags.append(f"ministry:{canonical_ministry}")
        searchable_tags.append(f"policy_domain:{policy_domain}")
        searchable_tags.append(f"sector:{primary_sector}")
        for s in secondary_sectors:
            searchable_tags.append(f"sector:{s}")
        for sh in stakeholders:
            searchable_tags.append(f"stakeholder:{sh}")
        if bill.year:
            searchable_tags.append(f"year:{bill.year}")
        if bill.status:
            searchable_tags.append(f"status:{bill.status.value}")

        # Traceability metadata: checksums
        metadata_checksum = None
        metadata_path = settings.BILLS_DIR / "metadata" / f"{bill.bill_id}.json"
        if metadata_path.is_file():
            try:
                with open(metadata_path, "rb") as f:
                    metadata_checksum = hashlib.sha256(f.read()).hexdigest()
            except Exception as e:
                logger.warning("Could not calculate checksum for metadata file: %s", e)

        generated_at = datetime.utcnow().isoformat() + "Z"

        return KnowledgeRecord(
            bill_id=bill.bill_id,
            ministry=canonical_ministry,
            department=department,
            policy_domain=policy_domain,
            economic_domain=economic_domain,
            primary_sector=primary_sector,
            secondary_sectors=secondary_sectors,
            stakeholder_groups=stakeholders,
            regulatory_authority=regulatory_authority,
            geographic_scope=geographic_scope,
            bill_type=bill_type,
            keywords=keywords_list,
            related_acts=related_acts,
            related_ministries=related_ministries,
            confidence_score=round(confidence, 2),
            searchable_tags=searchable_tags,
            generated_at=generated_at,
            rules_version="1.0",
            source_metadata_checksum=metadata_checksum,
            source_text_checksum=bill.text_checksum,
        )
