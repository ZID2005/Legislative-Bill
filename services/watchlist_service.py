"""
services/watchlist_service.py
=============================
Watchlist Service layer managing user watchlists, entity validation, ownership enforcement,
and inverted index synchronization for legislative entity monitoring.

Coordinates:
- WatchlistRepository
- AlertRuleRepository
- AlertPreferenceRepository
- CompanyRepository
- BillRepository & StateBillRepository
- CompanyExposureRepository
- WatchlistIndexService

Task 8.13.3 — Watchlist Service & Inverted Indices.
"""

from __future__ import annotations

from typing import Any, Optional
import uuid

from config.logging_config import get_logger
from schemas.alert import (
    AlertPreference,
    AlertRule,
    AlertSeverity,
    AlertType,
    DigestFrequency,
    NotificationChannel,
)
from schemas.company import Company
from schemas.watchlist import (
    Watchlist,
    WatchlistItem,
    WatchlistEntityType,
    validate_entity_reference,
)
from services.watchlist_index_service import (
    IndexValidationReport,
    WatchlistIndexService,
    WatchlistSubscriber,
)
from storage.alert_preference_repository import AlertPreferenceRepository
from storage.alert_rule_repository import AlertRuleRepository
from storage.bill_repository import BillRepository
from storage.company_exposure_repository import CompanyExposureRepository
from storage.company_repository import CompanyRepository
from storage.state_bill_repository import StateBillRepository
from storage.watchlist_repository import WatchlistRepository
from utils.state_normalizer import (
    CANONICAL_INDIAN_STATES,
    CANONICAL_UNION_TERRITORIES,
    normalize_state,
)

logger = get_logger(__name__)


class WatchlistService:
    """
    Business service layer managing user watchlists, entity subscriptions,
    and deterministic inverted indices for event subscriber resolution.
    """

    def __init__(
        self,
        watchlist_repo: Optional[WatchlistRepository] = None,
        index_service: Optional[WatchlistIndexService] = None,
        alert_rule_repo: Optional[AlertRuleRepository] = None,
        alert_pref_repo: Optional[AlertPreferenceRepository] = None,
        company_repo: Optional[CompanyRepository] = None,
        bill_repo: Optional[BillRepository] = None,
        state_bill_repo: Optional[StateBillRepository] = None,
        company_exposure_repo: Optional[CompanyExposureRepository] = None,
    ) -> None:
        self.watchlist_repo = watchlist_repo or WatchlistRepository()
        self.index_service = index_service or WatchlistIndexService(
            watchlist_repo=self.watchlist_repo
        )
        self.alert_rule_repo = alert_rule_repo or AlertRuleRepository()
        self.alert_pref_repo = alert_pref_repo or AlertPreferenceRepository()
        self.company_repo = company_repo or CompanyRepository()
        self.bill_repo = bill_repo or BillRepository()
        self.state_bill_repo = state_bill_repo or StateBillRepository()
        self.company_exposure_repo = company_exposure_repo or CompanyExposureRepository()

        # Cache known sectors and industries for validation
        self._known_sectors_cache: Optional[dict[str, str]] = None
        self._known_industries_cache: Optional[dict[str, str]] = None

        logger.debug("WatchlistService initialised")

    # ------------------------------------------------------------------
    # Taxonomy Caching & Helper Methods
    # ------------------------------------------------------------------

    def _get_known_sectors(self) -> dict[str, str]:
        """
        Build and cache case-insensitive mapping of canonical sector names:
        lower_name -> Canonical Name.
        """
        if self._known_sectors_cache is not None:
            return self._known_sectors_cache

        sectors: dict[str, str] = {}

        # 1. From CompanyRepository
        for c in self.company_repo.get_all():
            if c.sector and c.sector.strip():
                name = c.sector.strip()
                sectors[name.lower()] = name

        # 2. From Central Bills
        for b in self.bill_repo.get_all():
            for s in getattr(b, "sectors", []):
                if s and s.strip():
                    name = s.strip()
                    sectors[name.lower()] = name

        # 3. From State Bills
        for sb in self.state_bill_repo.get_all():
            for s in getattr(sb, "sectors", []):
                if s and s.strip():
                    name = s.strip()
                    sectors[name.lower()] = name

        # 4. From Corporate Exposures
        for exp in self.company_exposure_repo.get_all():
            if exp.sector and exp.sector.strip():
                name = exp.sector.strip()
                sectors[name.lower()] = name

        # 5. Core canonical fallback categories
        core_categories = [
            "Technology",
            "Banking & Finance",
            "Banking & Financial Services",
            "Labour",
            "Labour, Employment & Skills",
            "Agriculture",
            "Agriculture, Food & Allied",
            "Healthcare",
            "Energy",
            "Infrastructure",
            "Environment",
            "MSME",
            "Taxation",
            "Industry Regulation",
            "Consumer / Digital",
            "Telecommunications",
            "Transport / Maritime",
            "Transport / Aviation",
            "Transport / Railways",
            "Roads & Highways",
            "Fisheries",
            "Electricity",
        ]
        for c in core_categories:
            if c.lower() not in sectors:
                sectors[c.lower()] = c

        self._known_sectors_cache = sectors
        return self._known_sectors_cache

    def _get_known_industries(self) -> dict[str, str]:
        """
        Build and cache case-insensitive mapping of canonical industry names:
        lower_name -> Canonical Name.
        """
        if self._known_industries_cache is not None:
            return self._known_industries_cache

        industries: dict[str, str] = {}

        for c in self.company_repo.get_all():
            if c.industry and c.industry.strip():
                name = c.industry.strip()
                industries[name.lower()] = name
            if c.sub_industry and c.sub_industry.strip():
                name = c.sub_industry.strip()
                industries[name.lower()] = name

        # Common fallback industries
        fallbacks = [
            "Food Delivery & Quick Commerce",
            "E-Commerce",
            "IT Services",
            "Private Banks",
            "Public Banks",
            "Airports & Aviation",
            "Ports & Shipping",
            "Telecommunications",
            "Automobiles",
            "Pharmaceuticals",
            "Hospital & Healthcare",
            "Power Generation",
            "Renewable Energy",
            "Logistics & Express",
        ]
        for f in fallbacks:
            if f.lower() not in industries:
                industries[f.lower()] = f

        self._known_industries_cache = industries
        return self._known_industries_cache

    # ------------------------------------------------------------------
    # Entity Validation & Normalization
    # ------------------------------------------------------------------

    def validate_and_normalize_entity(
        self,
        entity_type: WatchlistEntityType | str,
        entity_id: str,
        bypass_eligibility: bool = False,
    ) -> tuple[str, str]:
        """
        Validate that referenced entity exists in the canonical project repositories
        and return a tuple of (canonical_entity_id, display_name).

        Enforces:
        - COMPANY: Must exist in CompanyRepository AND must have company.watchlist_eligible == True
                   (unless bypass_eligibility=True is explicitly specified).
        - BILL: Must exist in BillRepository or StateBillRepository.
        - STATE: Must be a valid Indian State/UT from utils.state_normalizer.
        - SECTOR: Must match canonical sector taxonomy.
        - INDUSTRY: Must match canonical industry taxonomy.
        - JURISDICTION: Must be 'central' or 'state'.

        Raises ValueError if invalid, nonexistent, or ineligible.
        """
        if not entity_id or not entity_id.strip():
            raise ValueError("entity_id cannot be empty or blank")

        raw_id = entity_id.strip()

        if isinstance(entity_type, WatchlistEntityType):
            etype = entity_type
        else:
            try:
                etype = WatchlistEntityType(str(entity_type).strip().upper())
            except ValueError:
                raise ValueError(f"Unsupported watchlist entity type: {entity_type}")

        # 1. COMPANY
        if etype == WatchlistEntityType.COMPANY:
            comp: Optional[Company] = None
            # Check ISIN direct
            comp = self.company_repo.get_by_isin(raw_id)
            # Check ticker
            if not comp:
                comp = self.company_repo.get_by_ticker(raw_id, exchange="NSE")
            if not comp:
                comp = self.company_repo.get_by_ticker(raw_id, exchange="BSE")
            # Exact name or alias match
            if not comp:
                raw_lower = raw_id.lower()
                for c in self.company_repo.get_all():
                    if c.isin.lower() == raw_lower or c.company_name.lower() == raw_lower:
                        comp = c
                        break
                    if any(al.lower() == raw_lower for al in getattr(c, "aliases", [])):
                        comp = c
                        break

            if not comp:
                raise ValueError(f"Company '{raw_id}' not found in company master repository")

            # CRITICAL: Watchlist Eligibility Check
            if not bypass_eligibility and not getattr(comp, "watchlist_eligible", False):
                raise ValueError(
                    f"Company '{comp.company_name}' ({comp.isin}) is not eligible for watchlists "
                    f"(watchlist_eligible=False)"
                )

            return comp.isin.upper(), comp.company_name

        # 2. BILL
        elif etype == WatchlistEntityType.BILL:
            bill_norm = raw_id.lower()
            bill = self.bill_repo.get(bill_norm)
            if not bill:
                bill = self.state_bill_repo.get(bill_norm)

            if not bill:
                raise ValueError(f"Bill '{raw_id}' not found in Central or State bill repository")

            return bill.bill_id.lower(), bill.title

        # 3. STATE
        elif etype == WatchlistEntityType.STATE:
            norm_state = normalize_state(raw_id)
            all_canonical = set(CANONICAL_INDIAN_STATES + CANONICAL_UNION_TERRITORIES)
            if not norm_state or norm_state not in all_canonical:
                raise ValueError(f"Invalid Indian State identifier '{raw_id}'")

            return norm_state, norm_state

        # 4. SECTOR
        elif etype == WatchlistEntityType.SECTOR:
            known_sectors = self._get_known_sectors()
            sec_lower = raw_id.lower()
            if sec_lower in known_sectors:
                canonical_name = known_sectors[sec_lower]
                return canonical_name, canonical_name

            # Substring matching for flexible sector aliases
            for k, canonical_name in known_sectors.items():
                if sec_lower in k or k in sec_lower:
                    return canonical_name, canonical_name

            raise ValueError(f"Sector '{raw_id}' not recognized in canonical sector taxonomy")

        # 5. INDUSTRY
        elif etype == WatchlistEntityType.INDUSTRY:
            known_industries = self._get_known_industries()
            ind_lower = raw_id.lower()
            if ind_lower in known_industries:
                canonical_name = known_industries[ind_lower]
                return canonical_name, canonical_name

            for k, canonical_name in known_industries.items():
                if ind_lower in k or k in ind_lower:
                    return canonical_name, canonical_name

            raise ValueError(f"Industry '{raw_id}' not recognized in canonical industry taxonomy")

        # 6. JURISDICTION
        elif etype == WatchlistEntityType.JURISDICTION:
            norm_j = raw_id.lower()
            if norm_j not in ("central", "state"):
                raise ValueError(f"Invalid jurisdiction '{raw_id}'. Must be 'central' or 'state'")

            display = "Central Government" if norm_j == "central" else "State Governments"
            return norm_j, display

        return raw_id, raw_id

    # ------------------------------------------------------------------
    # Watchlist Lifecycle Operations
    # ------------------------------------------------------------------

    def create_watchlist(
        self,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
        name: str = "Default Watchlist",
        description: Optional[str] = None,
        is_default: bool = False,
        is_active: bool = True,
        watchlist_id: Optional[str] = None,
    ) -> Watchlist:
        """
        Create and persist a new Watchlist with multi-tenant scoping.
        """
        wl = Watchlist(
            watchlist_id=watchlist_id or str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            name=name,
            description=description,
            is_default=is_default,
            is_active=is_active,
        )
        return self.watchlist_repo.create(wl)

    def get_watchlist(
        self,
        watchlist_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Watchlist]:
        """
        Retrieve a watchlist by ID, strictly enforcing tenant/user ownership.
        """
        return self.watchlist_repo.get(watchlist_id, tenant_id=tenant_id, user_id=user_id)

    def update_watchlist(
        self,
        watchlist: Watchlist,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Watchlist:
        """
        Update an existing Watchlist record.
        Enforces tenant and user isolation: raises PermissionError if cross-access attempted.
        """
        existing = self.watchlist_repo.get(
            watchlist.watchlist_id,
            tenant_id=tenant_id or watchlist.tenant_id,
            user_id=user_id or watchlist.user_id,
        )
        if not existing:
            raise PermissionError(
                f"Watchlist '{watchlist.watchlist_id}' not found or access denied for user '{user_id or watchlist.user_id}'"
            )

        # If watchlist is being deactivated, purge active index references
        if existing.is_active and not watchlist.is_active:
            self.index_service.deactivate_watchlist(watchlist.watchlist_id)

        return self.watchlist_repo.update(watchlist)

    def deactivate_watchlist(
        self,
        watchlist_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> bool:
        """
        Deactivate a watchlist (soft delete).
        Guarantees that the deactivated watchlist is purged from active inverted indices.
        """
        wl = self.watchlist_repo.get(watchlist_id, tenant_id=tenant_id, user_id=user_id)
        if not wl:
            raise PermissionError(
                f"Watchlist '{watchlist_id}' not found or access denied for user '{user_id}' in tenant '{tenant_id}'"
            )

        wl.is_active = False
        self.watchlist_repo.update(wl)
        self.index_service.deactivate_watchlist(watchlist_id)
        return True

    def list_user_watchlists(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        is_active: Optional[bool] = None,
    ) -> list[Watchlist]:
        """
        List all watchlists belonging to a user within a tenant.
        """
        return self.watchlist_repo.list_by_user(user_id, tenant_id=tenant_id, is_active=is_active)

    # ------------------------------------------------------------------
    # WatchlistItem Operations with Validation & Index Sync
    # ------------------------------------------------------------------

    def add_item(
        self,
        watchlist_id: str,
        entity_type: WatchlistEntityType | str,
        entity_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
        display_name: str = "",
        notes: Optional[str] = None,
        custom_tags: Optional[list[str]] = None,
        item_id: Optional[str] = None,
        bypass_eligibility: bool = False,
    ) -> WatchlistItem:
        """
        Add a verified item to an active watchlist and synchronously update the inverted index.

        Validation Steps:
        1. Enforce parent watchlist exists and belongs to the specified tenant/user.
        2. Enforce parent watchlist is active.
        3. Validate and normalize the entity reference (including company eligibility check).
        4. Prevent duplicate (watchlist_id, entity_type, entity_id) within the watchlist.
        5. Persist item to WatchlistRepository.
        6. Synchronously update WatchlistIndexService.
        """
        # 1. Enforce ownership
        parent_wl = self.watchlist_repo.get(watchlist_id, tenant_id=tenant_id, user_id=user_id)
        if not parent_wl:
            raise PermissionError(
                f"Parent watchlist '{watchlist_id}' not found or access denied for user '{user_id}' in tenant '{tenant_id}'"
            )

        # 2. Check parent is active
        if not parent_wl.is_active:
            raise ValueError(f"Cannot add items to inactive watchlist '{watchlist_id}'")

        # 3. Validate and normalize entity reference
        canonical_id, auto_display = self.validate_and_normalize_entity(
            entity_type, entity_id, bypass_eligibility=bypass_eligibility
        )
        final_display = display_name.strip() if display_name and display_name.strip() else auto_display

        etype = (
            entity_type
            if isinstance(entity_type, WatchlistEntityType)
            else WatchlistEntityType(str(entity_type).strip().upper())
        )

        # 4. Duplicate check within this watchlist
        existing_items = self.watchlist_repo.list_items_by_watchlist(
            watchlist_id, tenant_id=tenant_id, user_id=user_id, is_active=True
        )
        for ex in existing_items:
            if ex.entity_type == etype and ex.entity_id.lower() == canonical_id.lower():
                raise ValueError(
                    f"Entity '{canonical_id}' of type '{etype.value}' already exists in watchlist '{watchlist_id}'"
                )

        # 5. Persist item
        item = WatchlistItem(
            item_id=item_id or str(uuid.uuid4()),
            watchlist_id=watchlist_id,
            user_id=user_id,
            tenant_id=tenant_id,
            entity_type=etype,
            entity_id=canonical_id,
            display_name=final_display,
            notes=notes,
            custom_tags=custom_tags or [],
            is_active=True,
        )
        saved_item = self.watchlist_repo.add_item(item)

        # 6. Synchronously update inverted index
        self.index_service.add_subscriber(saved_item)

        return saved_item

    def remove_item(
        self,
        item_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
        hard_delete: bool = False,
    ) -> bool:
        """
        Deactivate (soft delete) or delete an item and remove it from the inverted index.
        Enforces tenant and user ownership.
        """
        item = self.watchlist_repo.get_item(item_id, tenant_id=tenant_id, user_id=user_id)
        if not item:
            raise PermissionError(
                f"Item '{item_id}' not found or access denied for user '{user_id}' in tenant '{tenant_id}'"
            )

        success = self.watchlist_repo.remove_item(
            item_id, tenant_id=tenant_id, user_id=user_id, hard_delete=hard_delete
        )
        if success:
            self.index_service.remove_subscriber(
                item_id=item_id, entity_type=item.entity_type, entity_id=item.entity_id
            )
        return success

    def list_items(
        self,
        watchlist_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
        is_active: Optional[bool] = None,
    ) -> list[WatchlistItem]:
        """
        List all items in a watchlist, enforcing tenant and user scoping.
        """
        parent_wl = self.watchlist_repo.get(watchlist_id, tenant_id=tenant_id, user_id=user_id)
        if not parent_wl:
            raise PermissionError(
                f"Watchlist '{watchlist_id}' not found or access denied for user '{user_id}'"
            )

        return self.watchlist_repo.list_items_by_watchlist(
            watchlist_id, tenant_id=tenant_id, user_id=user_id, is_active=is_active
        )

    def find_items_by_entity(
        self,
        entity_type: WatchlistEntityType | str,
        entity_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[WatchlistItem]:
        """
        Find all active watchlist items for a specific entity across watchlists.
        """
        return self.watchlist_repo.find_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

    # ------------------------------------------------------------------
    # Subscriber Resolution Primitives
    # ------------------------------------------------------------------

    def resolve_subscribers(
        self,
        entity_type: WatchlistEntityType | str,
        entity_id: str,
    ) -> list[WatchlistSubscriber]:
        """
        Route to the appropriate inverted index to retrieve active subscribers.
        O(1) resolution performance.
        """
        return self.index_service.get_subscribers(entity_type, entity_id)

    def get_subscribers_for_company(self, company_id: str) -> list[WatchlistSubscriber]:
        return self.index_service.get_subscribers_for_company(company_id)

    def get_subscribers_for_bill(self, bill_id: str) -> list[WatchlistSubscriber]:
        return self.index_service.get_subscribers_for_bill(bill_id)

    def get_subscribers_for_sector(self, sector_id: str) -> list[WatchlistSubscriber]:
        return self.index_service.get_subscribers_for_sector(sector_id)

    def get_subscribers_for_industry(self, industry_id: str) -> list[WatchlistSubscriber]:
        return self.index_service.get_subscribers_for_industry(industry_id)

    def get_subscribers_for_state(self, state_id: str) -> list[WatchlistSubscriber]:
        return self.index_service.get_subscribers_for_state(state_id)

    def get_subscribers_for_jurisdiction(self, jurisdiction: str) -> list[WatchlistSubscriber]:
        return self.index_service.get_subscribers_for_jurisdiction(jurisdiction)

    # ------------------------------------------------------------------
    # Multi-Entity Resolution Primitives (Future Event Matching Preparation)
    # ------------------------------------------------------------------

    def resolve_subscribers_by_company_exposure(
        self,
        bill_id: str,
    ) -> dict[str, list[WatchlistSubscriber]]:
        """
        Future preparation primitive:
        Resolve subscribers watching companies that have verified exposure to a given bill.

        Workflow:
        Bill ID -> Company Exposures -> Company IDs -> idx_company Subscribers

        Returns a dict mapping company_id -> list of subscribers.
        DOES NOT generate alerts.
        """
        norm_bill_id = bill_id.strip().lower()
        exposures = self.company_exposure_repo.get_by_bill(norm_bill_id)

        results: dict[str, list[WatchlistSubscriber]] = {}
        for exp in exposures:
            cid = exp.company_id.upper()
            subs = self.get_subscribers_for_company(cid)
            if subs:
                results[cid] = subs

        return results

    def resolve_subscribers_for_bill_change(
        self,
        bill_id: str,
    ) -> list[WatchlistSubscriber]:
        """
        Future preparation primitive:
        Resolve users/watchlists directly watching a bill when a monitoring event occurs.

        DOES NOT generate alerts.
        """
        return self.get_subscribers_for_bill(bill_id.strip().lower())

    # ------------------------------------------------------------------
    # Alert Rule Operations
    # ------------------------------------------------------------------

    def create_alert_rule(
        self,
        user_id: str = "default_user",
        tenant_id: str = "default_tenant",
        watchlist_id: Optional[str] = None,
        alert_type: AlertType | str = AlertType.BILL_STATUS_CHANGE,
        minimum_severity: AlertSeverity | str = AlertSeverity.LOW,
        enabled: bool = True,
        alert_rule_id: Optional[str] = None,
    ) -> AlertRule:
        """
        Create a new AlertRule, optionally linked to a specific watchlist.
        Enforces tenant and user isolation.
        """
        if watchlist_id:
            parent_wl = self.watchlist_repo.get(watchlist_id, tenant_id=tenant_id, user_id=user_id)
            if not parent_wl:
                raise PermissionError(
                    f"Watchlist '{watchlist_id}' not found or access denied for user '{user_id}' in tenant '{tenant_id}'"
                )

        atype = (
            alert_type
            if isinstance(alert_type, AlertType)
            else AlertType(str(alert_type).strip().upper())
        )
        msev = (
            minimum_severity
            if isinstance(minimum_severity, AlertSeverity)
            else AlertSeverity(str(minimum_severity).strip().upper())
        )

        rule = AlertRule(
            alert_rule_id=alert_rule_id or str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            watchlist_id=watchlist_id,
            alert_type=atype,
            minimum_severity=msev,
            enabled=enabled,
        )
        return self.alert_rule_repo.create(rule)

    def get_alert_rule(
        self,
        alert_rule_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[AlertRule]:
        return self.alert_rule_repo.get(alert_rule_id, tenant_id=tenant_id, user_id=user_id)

    def update_alert_rule(
        self,
        rule: AlertRule,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> AlertRule:
        existing = self.alert_rule_repo.get(
            rule.alert_rule_id,
            tenant_id=tenant_id or rule.tenant_id,
            user_id=user_id or rule.user_id,
        )
        if not existing:
            raise PermissionError(
                f"Alert rule '{rule.alert_rule_id}' not found or access denied"
            )
        return self.alert_rule_repo.update(rule)

    def enable_alert_rule(
        self,
        alert_rule_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> bool:
        existing = self.alert_rule_repo.get(alert_rule_id, tenant_id=tenant_id, user_id=user_id)
        if not existing:
            raise PermissionError(
                f"Alert rule '{alert_rule_id}' not found or access denied for user '{user_id}'"
            )
        return self.alert_rule_repo.enable(alert_rule_id, tenant_id=tenant_id, user_id=user_id)

    def disable_alert_rule(
        self,
        alert_rule_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> bool:
        existing = self.alert_rule_repo.get(alert_rule_id, tenant_id=tenant_id, user_id=user_id)
        if not existing:
            raise PermissionError(
                f"Alert rule '{alert_rule_id}' not found or access denied for user '{user_id}'"
            )
        return self.alert_rule_repo.disable(alert_rule_id, tenant_id=tenant_id, user_id=user_id)

    def list_alert_rules(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        watchlist_id: Optional[str] = None,
    ) -> list[AlertRule]:
        if watchlist_id:
            return self.alert_rule_repo.list_by_watchlist(
                watchlist_id=watchlist_id, tenant_id=tenant_id, user_id=user_id
            )
        return self.alert_rule_repo.list_by_user(user_id=user_id, tenant_id=tenant_id)

    # ------------------------------------------------------------------
    # Alert Preference Operations
    # ------------------------------------------------------------------

    def get_user_preferences(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
    ) -> AlertPreference:
        """
        Retrieve a user's AlertPreference. Returns sensible defaults if not yet created.
        """
        pref = self.alert_pref_repo.get_by_user(user_id, tenant_id=tenant_id)
        if not pref:
            # Create default preference
            pref = AlertPreference(
                user_id=user_id,
                tenant_id=tenant_id,
                enabled=True,
                minimum_severity=AlertSeverity.LOW,
                allowed_alert_types=list(AlertType),
                allowed_channels=[NotificationChannel.IN_APP],
                digest_frequency=DigestFrequency.REAL_TIME,
            )
            self.alert_pref_repo.create(pref)
        return pref

    def update_user_preferences(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
        preferences: Optional[AlertPreference] = None,
        **kwargs: Any,
    ) -> AlertPreference:
        """
        Update a user's alert configuration and cadence.
        """
        existing = self.get_user_preferences(user_id, tenant_id=tenant_id)

        if preferences:
            existing.enabled = preferences.enabled
            existing.minimum_severity = preferences.minimum_severity
            existing.allowed_alert_types = preferences.allowed_alert_types
            existing.allowed_channels = preferences.allowed_channels
            existing.digest_frequency = preferences.digest_frequency
        else:
            for k, v in kwargs.items():
                if hasattr(existing, k):
                    setattr(existing, k, v)

        return self.alert_pref_repo.update(existing)

    # ------------------------------------------------------------------
    # Summaries (Watchlist & User-Level)
    # ------------------------------------------------------------------

    def get_watchlist_summary(
        self,
        watchlist_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> dict[str, Any]:
        """
        Provide detailed derived summary for a specific watchlist.
        Enforces tenant and user isolation.
        """
        wl = self.watchlist_repo.get(watchlist_id, tenant_id=tenant_id, user_id=user_id)
        if not wl:
            raise PermissionError(
                f"Watchlist '{watchlist_id}' not found or access denied for user '{user_id}' in tenant '{tenant_id}'"
            )

        items = self.watchlist_repo.list_items_by_watchlist(
            watchlist_id, tenant_id=tenant_id, user_id=user_id, is_active=True
        )
        rules = self.alert_rule_repo.list_by_watchlist(
            watchlist_id, tenant_id=tenant_id, user_id=user_id
        )
        enabled_rules = [r for r in rules if r.enabled]

        companies = [i.entity_id for i in items if i.entity_type == WatchlistEntityType.COMPANY]
        bills = [i.entity_id for i in items if i.entity_type == WatchlistEntityType.BILL]
        sectors = [i.entity_id for i in items if i.entity_type == WatchlistEntityType.SECTOR]
        industries = [i.entity_id for i in items if i.entity_type == WatchlistEntityType.INDUSTRY]
        states = [i.entity_id for i in items if i.entity_type == WatchlistEntityType.STATE]
        jurisdictions = [i.entity_id for i in items if i.entity_type == WatchlistEntityType.JURISDICTION]

        return {
            "watchlist_id": wl.watchlist_id,
            "name": wl.name,
            "description": wl.description,
            "user_id": wl.user_id,
            "tenant_id": wl.tenant_id,
            "is_default": wl.is_default,
            "is_active": wl.is_active,
            "item_count": len(items),
            "companies_watched": sorted(companies),
            "bills_watched": sorted(bills),
            "sectors_watched": sorted(sectors),
            "industries_watched": sorted(industries),
            "states_watched": sorted(states),
            "jurisdictions_watched": sorted(jurisdictions),
            "alert_rules_count": len(rules),
            "enabled_alert_rules_count": len(enabled_rules),
            "created_at": wl.created_at,
            "updated_at": wl.updated_at,
        }

    def get_user_watchlist_summary(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
    ) -> dict[str, Any]:
        """
        Aggregate overview across all watchlists belonging to a user.
        Powers the user intelligence dashboard.
        """
        all_watchlists = self.watchlist_repo.list_by_user(user_id, tenant_id=tenant_id)
        active_watchlists = [w for w in all_watchlists if w.is_active]

        all_items: list[WatchlistItem] = []
        for w in active_watchlists:
            items = self.watchlist_repo.list_items_by_watchlist(
                w.watchlist_id, tenant_id=tenant_id, user_id=user_id, is_active=True
            )
            all_items.extend(items)

        unique_companies = {i.entity_id for i in all_items if i.entity_type == WatchlistEntityType.COMPANY}
        unique_bills = {i.entity_id for i in all_items if i.entity_type == WatchlistEntityType.BILL}
        unique_sectors = {i.entity_id for i in all_items if i.entity_type == WatchlistEntityType.SECTOR}
        unique_industries = {i.entity_id for i in all_items if i.entity_type == WatchlistEntityType.INDUSTRY}
        unique_states = {i.entity_id for i in all_items if i.entity_type == WatchlistEntityType.STATE}
        unique_jurisdictions = {i.entity_id for i in all_items if i.entity_type == WatchlistEntityType.JURISDICTION}

        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "total_watchlists": len(all_watchlists),
            "active_watchlists": len(active_watchlists),
            "total_items": len(all_items),
            "total_watched_companies": len(unique_companies),
            "total_watched_bills": len(unique_bills),
            "total_watched_sectors": len(unique_sectors),
            "total_watched_industries": len(unique_industries),
            "total_watched_states": len(unique_states),
            "total_watched_jurisdictions": len(unique_jurisdictions),
        }

    # ------------------------------------------------------------------
    # Index Maintenance Delegates
    # ------------------------------------------------------------------

    def rebuild_indices(self) -> dict[str, Any]:
        """Rebuild all derived inverted indices from canonical storage."""
        return self.index_service.rebuild_indices(self.watchlist_repo)

    def validate_indices(self) -> IndexValidationReport:
        """Assess consistency and integrity of the inverted indices."""
        return self.index_service.validate_indices(self.watchlist_repo)
