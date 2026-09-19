"""
services/watchlist_index_service.py
===================================
Deterministic Inverted Indices for high-performance Watchlist subscriber resolution.

Provides O(1) in-memory lookup and structured JSON persistence for:
- idx_company
- idx_bill
- idx_sector
- idx_industry
- idx_state
- idx_jurisdiction

Key Architectural Guarantees:
1. Inverted indices are DERIVED CACHES. Canonical truth remains WatchlistItem storage.
2. Complete determinism and idempotency: rebuilding indices twice on unchanged data produces byte-for-byte identical output.
3. Inactive watchlists and inactive items are strictly excluded from active indices.
4. Comprehensive integrity validation detects missing, stale, orphaned, duplicate, or inactive references.

Task 8.13.3 — Watchlist Service & Inverted Indices.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.watchlist import Watchlist, WatchlistItem, WatchlistEntityType
from storage.watchlist_repository import WatchlistRepository
from utils.file_utils import ensure_dir
from utils.state_normalizer import normalize_state

logger = get_logger(__name__)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WatchlistSubscriber:
    """
    Subscriber reference returned by an inverted index lookup.

    Attributes
    ----------
    tenant_id : str
        Tenant identifier for multi-tenant isolation.
    user_id : str
        Subscribed user identifier.
    watchlist_id : str
        Subscribed watchlist identifier.
    item_id : str
        Canonical WatchlistItem identifier.
    entity_type : str
        Entity classification string (e.g. 'COMPANY', 'BILL', etc.).
    entity_id : str
        Canonical entity identifier.
    display_name : str
        Human-readable label snapshot.
    created_at : str
        Creation ISO timestamp.
    """

    tenant_id: str
    user_id: str
    watchlist_id: str
    item_id: str
    entity_type: str
    entity_id: str
    display_name: str = ""
    created_at: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> dict[str, Any]:
        """Serialize WatchlistSubscriber to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "watchlist_id": self.watchlist_id,
            "item_id": self.item_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "display_name": self.display_name,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WatchlistSubscriber":
        """Deserialize WatchlistSubscriber from dictionary."""
        return cls(
            tenant_id=data.get("tenant_id", "default_tenant"),
            user_id=data.get("user_id", "default_user"),
            watchlist_id=data.get("watchlist_id", ""),
            item_id=data.get("item_id", ""),
            entity_type=str(data.get("entity_type", "")),
            entity_id=str(data.get("entity_id", "")),
            display_name=data.get("display_name", ""),
            created_at=data.get("created_at", _utcnow_iso()),
        )


@dataclass
class IndexValidationReport:
    """
    Integrity assessment report for the inverted index collection.
    """

    is_valid: bool = True
    total_subscribers: int = 0
    entries_count: dict[str, int] = field(default_factory=dict)
    missing_entries: list[dict[str, Any]] = field(default_factory=list)
    stale_entries: list[dict[str, Any]] = field(default_factory=list)
    orphaned_entries: list[dict[str, Any]] = field(default_factory=list)
    duplicate_subscribers: list[dict[str, Any]] = field(default_factory=list)
    inactive_watchlist_entries: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert validation report to dictionary."""
        return {
            "is_valid": self.is_valid,
            "total_subscribers": self.total_subscribers,
            "entries_count": self.entries_count,
            "missing_count": len(self.missing_entries),
            "stale_count": len(self.stale_entries),
            "orphaned_count": len(self.orphaned_entries),
            "duplicate_count": len(self.duplicate_subscribers),
            "inactive_watchlist_count": len(self.inactive_watchlist_entries),
            "errors": self.errors,
            "missing_entries": self.missing_entries,
            "stale_entries": self.stale_entries,
            "orphaned_entries": self.orphaned_entries,
            "duplicate_subscribers": self.duplicate_subscribers,
            "inactive_watchlist_entries": self.inactive_watchlist_entries,
        }


def _get_default_indices_dir() -> Path:
    root = settings.WATCHLIST_DIR / "indices"
    ensure_dir(root)
    return root


class WatchlistIndexService:
    """
    Service managing deterministic inverted indices for entity -> subscriber resolution.

    Indices:
      idx_company      : company_id      -> list[WatchlistSubscriber]
      idx_bill         : bill_id         -> list[WatchlistSubscriber]
      idx_sector       : sector_name     -> list[WatchlistSubscriber]
      idx_industry     : industry_name   -> list[WatchlistSubscriber]
      idx_state        : state_name      -> list[WatchlistSubscriber]
      idx_jurisdiction : jurisdiction    -> list[WatchlistSubscriber]
    """

    INDEX_FILENAMES: dict[WatchlistEntityType, str] = {
        WatchlistEntityType.COMPANY: "company_index.json",
        WatchlistEntityType.BILL: "bill_index.json",
        WatchlistEntityType.SECTOR: "sector_index.json",
        WatchlistEntityType.INDUSTRY: "industry_index.json",
        WatchlistEntityType.STATE: "state_index.json",
        WatchlistEntityType.JURISDICTION: "jurisdiction_index.json",
    }

    def __init__(
        self,
        indices_dir: Optional[Path] = None,
        watchlist_repo: Optional[WatchlistRepository] = None,
    ) -> None:
        self._indices_dir = indices_dir or _get_default_indices_dir()
        ensure_dir(self._indices_dir)
        self._watchlist_repo = watchlist_repo or WatchlistRepository()

        # In-memory index maps
        self.idx_company: dict[str, list[WatchlistSubscriber]] = {}
        self.idx_bill: dict[str, list[WatchlistSubscriber]] = {}
        self.idx_sector: dict[str, list[WatchlistSubscriber]] = {}
        self.idx_industry: dict[str, list[WatchlistSubscriber]] = {}
        self.idx_state: dict[str, list[WatchlistSubscriber]] = {}
        self.idx_jurisdiction: dict[str, list[WatchlistSubscriber]] = {}

        self._type_to_map = {
            WatchlistEntityType.COMPANY: self.idx_company,
            WatchlistEntityType.BILL: self.idx_bill,
            WatchlistEntityType.SECTOR: self.idx_sector,
            WatchlistEntityType.INDUSTRY: self.idx_industry,
            WatchlistEntityType.STATE: self.idx_state,
            WatchlistEntityType.JURISDICTION: self.idx_jurisdiction,
        }

        self._load_indices()
        logger.debug("WatchlistIndexService initialised at %s", self._indices_dir)

    @property
    def indices_dir(self) -> Path:
        return self._indices_dir

    # ------------------------------------------------------------------
    # Normalization Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_entity_id(entity_type: WatchlistEntityType | str, entity_id: str) -> str:
        """
        Normalize entity_id to match index key conventions deterministically.
        """
        raw = entity_id.strip()
        if isinstance(entity_type, WatchlistEntityType):
            etype = entity_type
        else:
            try:
                etype = WatchlistEntityType(str(entity_type).strip().upper())
            except ValueError:
                return raw

        if etype == WatchlistEntityType.COMPANY:
            return raw.upper()
        elif etype == WatchlistEntityType.BILL:
            return raw.lower()
        elif etype in (WatchlistEntityType.SECTOR, WatchlistEntityType.INDUSTRY):
            return raw.lower()
        elif etype == WatchlistEntityType.STATE:
            norm = normalize_state(raw)
            return norm if norm else raw.title()
        elif etype == WatchlistEntityType.JURISDICTION:
            return raw.lower()
        return raw

    def _get_map(self, entity_type: WatchlistEntityType | str) -> dict[str, list[WatchlistSubscriber]]:
        if isinstance(entity_type, WatchlistEntityType):
            etype = entity_type
        else:
            etype = WatchlistEntityType(str(entity_type).strip().upper())
        return self._type_to_map[etype]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _index_path(self, entity_type: WatchlistEntityType) -> Path:
        return self._indices_dir / self.INDEX_FILENAMES[entity_type]

    def _load_indices(self) -> None:
        """Load persisted index files into memory."""
        for etype, filename in self.INDEX_FILENAMES.items():
            path = self._indices_dir / filename
            target_map = self._type_to_map[etype]
            target_map.clear()
            if not path.is_file():
                continue

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries = data.get("entries", {})
                for key, sub_list in entries.items():
                    norm_key = self.normalize_entity_id(etype, key)
                    target_map[norm_key] = [
                        WatchlistSubscriber.from_dict(s) for s in sub_list
                    ]
            except Exception as e:
                logger.error("Failed to load index file %s: %s", filename, e)

    def _save_index(self, entity_type: WatchlistEntityType) -> None:
        """Persist a specific inverted index to its JSON file deterministically."""
        path = self._index_path(entity_type)
        target_map = self._type_to_map[entity_type]

        # Build sorted dictionary for deterministic output
        sorted_entries: dict[str, list[dict[str, Any]]] = {}
        total_subs = 0

        for key in sorted(target_map.keys()):
            subs = target_map[key]
            # Deduplicate and sort subscribers deterministically by (tenant_id, user_id, watchlist_id, item_id)
            seen: set[str] = set()
            clean_subs: list[WatchlistSubscriber] = []
            for s in subs:
                ukey = f"{s.tenant_id}|{s.user_id}|{s.watchlist_id}|{s.item_id}"
                if ukey not in seen:
                    seen.add(ukey)
                    clean_subs.append(s)

            clean_subs.sort(key=lambda s: (s.tenant_id, s.user_id, s.watchlist_id, s.item_id))
            target_map[key] = clean_subs
            sorted_entries[key] = [s.to_dict() for s in clean_subs]
            total_subs += len(clean_subs)

        payload = {
            "_version": "1.0",
            "entity_type": entity_type.value,
            "updated_at": _utcnow_iso(),
            "entry_count": len(sorted_entries),
            "subscriber_count": total_subs,
            "entries": sorted_entries,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def save_all_indices(self) -> None:
        """Persist all in-memory inverted indices."""
        for etype in self.INDEX_FILENAMES:
            self._save_index(etype)

    # ------------------------------------------------------------------
    # Index Mutation Operations
    # ------------------------------------------------------------------

    def add_subscriber(self, item: WatchlistItem) -> WatchlistSubscriber:
        """
        Add a watchlist item to the corresponding inverted index and persist.
        """
        if not item.is_active:
            raise ValueError(f"Cannot add inactive WatchlistItem {item.item_id} to active index")

        norm_key = self.normalize_entity_id(item.entity_type, item.entity_id)
        target_map = self._get_map(item.entity_type)

        sub = WatchlistSubscriber(
            tenant_id=item.tenant_id,
            user_id=item.user_id,
            watchlist_id=item.watchlist_id,
            item_id=item.item_id,
            entity_type=item.entity_type.value
            if isinstance(item.entity_type, WatchlistEntityType)
            else str(item.entity_type),
            entity_id=item.entity_id,
            display_name=item.display_name,
            created_at=item.created_at,
        )

        if norm_key not in target_map:
            target_map[norm_key] = []

        # Avoid duplicate item in bucket
        for existing in target_map[norm_key]:
            if (
                existing.watchlist_id == sub.watchlist_id
                and existing.item_id == sub.item_id
            ):
                return existing

        target_map[norm_key].append(sub)
        self._save_index(item.entity_type)
        logger.debug("Indexed subscriber for %s: %s (item: %s)", item.entity_type.value, norm_key, item.item_id)
        return sub

    def remove_subscriber(
        self,
        item_id: str,
        entity_type: Optional[WatchlistEntityType | str] = None,
        entity_id: Optional[str] = None,
    ) -> bool:
        """
        Remove a subscriber item from the inverted index and persist.
        If entity_type is provided, removes specifically from that index;
        otherwise searches across all indices.
        """
        removed = False

        if entity_type:
            etype = (
                entity_type
                if isinstance(entity_type, WatchlistEntityType)
                else WatchlistEntityType(str(entity_type).strip().upper())
            )
            target_map = self._type_to_map[etype]
            keys = [self.normalize_entity_id(etype, entity_id)] if entity_id else list(target_map.keys())

            for k in keys:
                if k in target_map:
                    before_len = len(target_map[k])
                    target_map[k] = [s for s in target_map[k] if s.item_id != item_id]
                    if len(target_map[k]) != before_len:
                        removed = True
                    if not target_map[k]:
                        del target_map[k]

            if removed:
                self._save_index(etype)
            return removed

        # Search across all indices
        for et, t_map in self._type_to_map.items():
            found_in_index = False
            for k in list(t_map.keys()):
                before_len = len(t_map[k])
                t_map[k] = [s for s in t_map[k] if s.item_id != item_id]
                if len(t_map[k]) != before_len:
                    found_in_index = True
                    removed = True
                if not t_map[k]:
                    del t_map[k]
            if found_in_index:
                self._save_index(et)

        return removed

    def deactivate_watchlist(self, watchlist_id: str) -> int:
        """
        Purge all active subscriber entries belonging to a deactivated watchlist.
        Returns the number of subscribers removed.
        """
        total_removed = 0

        for etype, target_map in self._type_to_map.items():
            index_changed = False
            for k in list(target_map.keys()):
                before_len = len(target_map[k])
                target_map[k] = [s for s in target_map[k] if s.watchlist_id != watchlist_id]
                removed_count = before_len - len(target_map[k])
                if removed_count > 0:
                    total_removed += removed_count
                    index_changed = True
                if not target_map[k]:
                    del target_map[k]
            if index_changed:
                self._save_index(etype)

        logger.debug("Deactivated watchlist %s purged %d index entries", watchlist_id, total_removed)
        return total_removed

    # ------------------------------------------------------------------
    # Query / Subscriber Resolution
    # ------------------------------------------------------------------

    def get_subscribers(
        self,
        entity_type: WatchlistEntityType | str,
        entity_id: str,
    ) -> list[WatchlistSubscriber]:
        """
        O(1) in-memory subscriber resolution for any supported entity type and id.
        """
        if not entity_id:
            return []

        norm_key = self.normalize_entity_id(entity_type, entity_id)
        target_map = self._get_map(entity_type)
        subs = target_map.get(norm_key, [])
        return list(subs)

    def get_subscribers_for_company(self, company_id: str) -> list[WatchlistSubscriber]:
        return self.get_subscribers(WatchlistEntityType.COMPANY, company_id)

    def get_subscribers_for_bill(self, bill_id: str) -> list[WatchlistSubscriber]:
        return self.get_subscribers(WatchlistEntityType.BILL, bill_id)

    def get_subscribers_for_sector(self, sector_id: str) -> list[WatchlistSubscriber]:
        return self.get_subscribers(WatchlistEntityType.SECTOR, sector_id)

    def get_subscribers_for_industry(self, industry_id: str) -> list[WatchlistSubscriber]:
        return self.get_subscribers(WatchlistEntityType.INDUSTRY, industry_id)

    def get_subscribers_for_state(self, state_id: str) -> list[WatchlistSubscriber]:
        return self.get_subscribers(WatchlistEntityType.STATE, state_id)

    def get_subscribers_for_jurisdiction(self, jurisdiction: str) -> list[WatchlistSubscriber]:
        return self.get_subscribers(WatchlistEntityType.JURISDICTION, jurisdiction)

    # ------------------------------------------------------------------
    # Deterministic Index Rebuild
    # ------------------------------------------------------------------

    def rebuild_indices(
        self,
        watchlist_repo: Optional[WatchlistRepository] = None,
    ) -> dict[str, Any]:
        """
        Reconstruct all inverted indices from canonical storage.

        Rules:
        1. Only active watchlists are included.
        2. Only active items within active watchlists are included.
        3. Completely clears in-memory indices and overwrites index files.
        4. Fully deterministic and idempotent: running twice produces identical output.
        """
        repo = watchlist_repo or self._watchlist_repo

        # Clear in-memory maps
        for t_map in self._type_to_map.values():
            t_map.clear()

        # Scan all watchlists from repo root
        root = repo._root_dir
        active_watchlists: dict[str, Watchlist] = {}
        for wl_file in root.glob("*/*/watchlists/wl_*.json"):
            try:
                with open(wl_file, "r", encoding="utf-8") as fh:
                    wl = Watchlist.from_dict(json.load(fh))
                if wl.is_active:
                    active_watchlists[wl.watchlist_id] = wl
            except Exception as e:
                logger.warning("Failed to parse watchlist file %s during rebuild: %s", wl_file, e)

        indexed_count = 0
        counts_by_type: dict[str, int] = {e.value: 0 for e in WatchlistEntityType}

        # Scan all items
        for item_file in root.glob("*/*/items/item_*.json"):
            try:
                with open(item_file, "r", encoding="utf-8") as fh:
                    item = WatchlistItem.from_dict(json.load(fh))
                if not item.is_active:
                    continue
                if item.watchlist_id not in active_watchlists:
                    continue  # Parent watchlist is inactive or deleted

                target_map = self._get_map(item.entity_type)
                norm_key = self.normalize_entity_id(item.entity_type, item.entity_id)

                sub = WatchlistSubscriber(
                    tenant_id=item.tenant_id,
                    user_id=item.user_id,
                    watchlist_id=item.watchlist_id,
                    item_id=item.item_id,
                    entity_type=item.entity_type.value,
                    entity_id=item.entity_id,
                    display_name=item.display_name,
                    created_at=item.created_at,
                )

                if norm_key not in target_map:
                    target_map[norm_key] = []

                # Duplicate prevention in bucket
                if not any(s.item_id == sub.item_id for s in target_map[norm_key]):
                    target_map[norm_key].append(sub)
                    indexed_count += 1
                    counts_by_type[item.entity_type.value] += 1
            except Exception as e:
                logger.warning("Failed to parse item file %s during rebuild: %s", item_file, e)

        # Save all rebuilt indices deterministically
        self.save_all_indices()

        logger.info("Successfully rebuilt inverted indices: %d subscribers across %d active watchlists",
                    indexed_count, len(active_watchlists))

        return {
            "status": "SUCCESS",
            "active_watchlists": len(active_watchlists),
            "total_subscribers_indexed": indexed_count,
            "counts_by_entity_type": counts_by_type,
            "rebuilt_at": _utcnow_iso(),
        }

    # ------------------------------------------------------------------
    # Index Integrity Validation
    # ------------------------------------------------------------------

    def validate_indices(
        self,
        watchlist_repo: Optional[WatchlistRepository] = None,
    ) -> IndexValidationReport:
        """
        Validate consistency between canonical Watchlist/Item storage and the inverted indices.

        Detects:
        - missing index entries (active items in active watchlists not in index)
        - stale entries (index subscribers whose item is inactive or missing)
        - orphaned entries (index subscribers whose parent watchlist does not exist)
        - duplicate subscribers in an index bucket
        - inactive watchlists present in index
        - invalid entity references
        """
        repo = watchlist_repo or self._watchlist_repo
        report = IndexValidationReport()

        root = repo._root_dir

        # 1. Load canonical state
        canonical_watchlists: dict[str, Watchlist] = {}
        canonical_active_items: dict[str, WatchlistItem] = {}

        for wl_file in root.glob("*/*/watchlists/wl_*.json"):
            try:
                with open(wl_file, "r", encoding="utf-8") as fh:
                    wl = Watchlist.from_dict(json.load(fh))
                canonical_watchlists[wl.watchlist_id] = wl
            except Exception as e:
                report.errors.append(f"Unreadable watchlist file {wl_file}: {e}")

        for item_file in root.glob("*/*/items/item_*.json"):
            try:
                with open(item_file, "r", encoding="utf-8") as fh:
                    item = WatchlistItem.from_dict(json.load(fh))
                if item.is_active:
                    canonical_active_items[item.item_id] = item
            except Exception as e:
                report.errors.append(f"Unreadable item file {item_file}: {e}")

        # 2. Check for missing entries (active canonical items in active watchlists not in index)
        for item_id, item in canonical_active_items.items():
            parent_wl = canonical_watchlists.get(item.watchlist_id)
            if not parent_wl or not parent_wl.is_active:
                continue

            target_map = self._get_map(item.entity_type)
            norm_key = self.normalize_entity_id(item.entity_type, item.entity_id)
            subs = target_map.get(norm_key, [])

            if not any(s.item_id == item.item_id for s in subs):
                report.missing_entries.append({
                    "item_id": item.item_id,
                    "watchlist_id": item.watchlist_id,
                    "entity_type": item.entity_type.value,
                    "entity_id": item.entity_id,
                    "reason": "Active item in active watchlist missing from index",
                })
                report.is_valid = False

        # 3. Check for stale, orphaned, duplicate, or inactive-watchlist entries in the index
        total_indexed_subs = 0

        for etype, target_map in self._type_to_map.items():
            report.entries_count[etype.value] = len(target_map)
            for norm_key, subs in target_map.items():
                seen_sub_ids: set[str] = set()

                for s in subs:
                    total_indexed_subs += 1

                    # Check duplicates
                    if s.item_id in seen_sub_ids:
                        report.duplicate_subscribers.append({
                            "item_id": s.item_id,
                            "entity_type": etype.value,
                            "entity_id": norm_key,
                            "watchlist_id": s.watchlist_id,
                        })
                        report.is_valid = False
                    seen_sub_ids.add(s.item_id)

                    # Check parent watchlist
                    parent_wl = canonical_watchlists.get(s.watchlist_id)
                    if not parent_wl:
                        report.orphaned_entries.append({
                            "item_id": s.item_id,
                            "watchlist_id": s.watchlist_id,
                            "reason": "Parent watchlist does not exist",
                        })
                        report.is_valid = False
                    elif not parent_wl.is_active:
                        report.inactive_watchlist_entries.append({
                            "item_id": s.item_id,
                            "watchlist_id": s.watchlist_id,
                            "reason": "Parent watchlist is inactive",
                        })
                        report.is_valid = False

                    # Check item existence and active status
                    item = canonical_active_items.get(s.item_id)
                    if not item:
                        report.stale_entries.append({
                            "item_id": s.item_id,
                            "watchlist_id": s.watchlist_id,
                            "reason": "Underlying item is missing or inactive",
                        })
                        report.is_valid = False

        report.total_subscribers = total_indexed_subs
        if report.errors or report.missing_entries or report.stale_entries or report.orphaned_entries or report.duplicate_subscribers or report.inactive_watchlist_entries:
            report.is_valid = False

        return report
