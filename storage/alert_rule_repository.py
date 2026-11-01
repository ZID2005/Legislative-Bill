"""
storage/alert_rule_repository.py
================================
Repository for AlertRule persistence supporting tenant isolation.

Storage layout:
  storage/alerts/rules/{tenant_id}/{user_id}/rule_{alert_rule_id}.json

Task 8.13.2 — Watchlist & Alert Schemas and Storage Foundation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.alert import AlertRule
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


def _get_default_rules_dir() -> Path:
    root = settings.ALERTS_DIR / "rules"
    ensure_dir(root)
    return root


class AlertRuleRepository:
    """
    Repository for managing alert rules with tenant and user isolation.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root_dir = root_dir or _get_default_rules_dir()
        ensure_dir(self._root_dir)

    def _get_db(self) -> Any:
        if self._root_dir != _get_default_rules_dir():
            return None
        try:
            from storage.database.provider import get_database_provider
            db = get_database_provider()
            if db and db.status in ("READY", "CONFIGURED"):
                return db
        except Exception:
            pass
        return None

    def _user_rules_dir(self, tenant_id: str, user_id: str) -> Path:
        path = self._root_dir / tenant_id / user_id
        ensure_dir(path)
        return path

    def create(self, rule: AlertRule) -> AlertRule:
        """
        Create and persist a new AlertRule.
        """
        rule.validate()
        r_dir = self._user_rules_dir(rule.tenant_id, rule.user_id)
        path = r_dir / f"rule_{rule.alert_rule_id}.json"
        if path.is_file():
            raise ValueError(
                f"Alert rule '{rule.alert_rule_id}' already exists for user '{rule.user_id}'"
            )

        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    """
                    INSERT INTO alert_rules (
                        rule_id, tenant_id, user_id, watchlist_id, name, rule_type,
                        minimum_severity, conditions, enabled, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """,
                    (
                        rule.alert_rule_id,
                        rule.tenant_id,
                        rule.user_id,
                        rule.watchlist_id,
                        f"Rule {rule.alert_rule_id[:8]}",
                        rule.alert_type.value if hasattr(rule.alert_type, "value") else str(rule.alert_type),
                        rule.minimum_severity.value if hasattr(rule.minimum_severity, "value") else str(rule.minimum_severity),
                        "{}",
                        rule.enabled,
                        rule.created_at,
                        rule.updated_at,
                    ),
                    tenant_id=rule.tenant_id,
                )
            except Exception as e:
                logger.debug("DB insert alert_rule failed: %s", e)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(rule.to_dict(), f, indent=2)
        logger.debug("Created alert rule %s for user %s", rule.alert_rule_id, rule.user_id)
        return rule

    def get(
        self,
        alert_rule_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[AlertRule]:
        """
        Retrieve an alert rule by ID, enforcing tenant/user scoping when supplied.
        """
        db = self._get_db()
        if db:
            try:
                query = "SELECT rule_id, tenant_id, user_id, watchlist_id, name, rule_type, minimum_severity, conditions, enabled, created_at, updated_at FROM alert_rules WHERE rule_id = %s"
                params: list[Any] = [alert_rule_id]
                if tenant_id:
                    query += " AND tenant_id = %s"
                    params.append(tenant_id)
                if user_id:
                    query += " AND user_id = %s"
                    params.append(user_id)
                rows = db.execute_query(query, tuple(params), tenant_id=tenant_id)
                if rows:
                    r = rows[0]
                    from schemas.alert import AlertType, AlertSeverity
                    at = AlertType(r["rule_type"]) if r["rule_type"] in AlertType._value2member_map_ else AlertType.BILL_STATUS_CHANGE
                    sev = AlertSeverity(r["minimum_severity"]) if r["minimum_severity"] in AlertSeverity._value2member_map_ else AlertSeverity.MEDIUM
                    return AlertRule(
                        alert_rule_id=r["rule_id"],
                        tenant_id=r["tenant_id"],
                        user_id=r["user_id"],
                        watchlist_id=r.get("watchlist_id"),
                        alert_type=at,
                        minimum_severity=sev,
                        enabled=bool(r.get("enabled", True)),
                        created_at=str(r.get("created_at")),
                        updated_at=str(r.get("updated_at")),
                    )
            except Exception as e:
                logger.debug("DB get alert_rule failed: %s", e)

        if tenant_id and user_id:
            path = self._user_rules_dir(tenant_id, user_id) / f"rule_{alert_rule_id}.json"
            if not path.is_file():
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return AlertRule.from_dict(json.load(f))
            except Exception as e:
                logger.error("Failed to load alert rule %s: %s", alert_rule_id, e)
                return None

        pattern = f"*/*/rule_{alert_rule_id}.json" if not tenant_id else f"{tenant_id}/*/rule_{alert_rule_id}.json"
        matches = list(self._root_dir.glob(pattern))
        for f in matches:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    rule = AlertRule.from_dict(json.load(fh))
                if tenant_id and rule.tenant_id != tenant_id:
                    continue
                if user_id and rule.user_id != user_id:
                    continue
                return rule
            except Exception:
                pass
        return None

    def update(self, rule: AlertRule) -> AlertRule:
        """
        Update an existing alert rule. Bumps updated_at.
        """
        rule.validate()
        from datetime import datetime, timezone
        rule.updated_at = datetime.now(timezone.utc).isoformat()

        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    """
                    UPDATE alert_rules
                    SET enabled = %s, minimum_severity = %s, updated_at = %s
                    WHERE rule_id = %s AND tenant_id = %s;
                    """,
                    (
                        rule.enabled,
                        rule.minimum_severity.value if hasattr(rule.minimum_severity, "value") else str(rule.minimum_severity),
                        rule.updated_at,
                        rule.alert_rule_id,
                        rule.tenant_id,
                    ),
                    tenant_id=rule.tenant_id,
                )
            except Exception as e:
                logger.debug("DB update alert_rule failed: %s", e)

        path = self._user_rules_dir(rule.tenant_id, rule.user_id) / f"rule_{rule.alert_rule_id}.json"
        if not path.is_file() and not db:
            raise ValueError(
                f"Cannot update non-existent alert rule '{rule.alert_rule_id}'"
            )

        if path.parent.is_dir():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rule.to_dict(), f, indent=2)
        return rule

    def enable(
        self,
        alert_rule_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Enable an alert rule."""
        rule = self.get(alert_rule_id, tenant_id=tenant_id, user_id=user_id)
        if not rule:
            return False
        rule.enabled = True
        self.update(rule)
        return True

    def disable(
        self,
        alert_rule_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Disable an alert rule."""
        rule = self.get(alert_rule_id, tenant_id=tenant_id, user_id=user_id)
        if not rule:
            return False
        rule.enabled = False
        self.update(rule)
        return True

    def list_by_watchlist(
        self,
        watchlist_id: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[AlertRule]:
        """
        List alert rules that apply to a specific watchlist.
        """
        if tenant_id and user_id:
            r_dir = self._user_rules_dir(tenant_id, user_id)
            target_files = list(r_dir.glob("rule_*.json"))
        elif tenant_id:
            target_files = list((self._root_dir / tenant_id).glob("*/rule_*.json"))
        else:
            target_files = list(self._root_dir.glob("*/*/rule_*.json"))

        rules: list[AlertRule] = []
        for f in target_files:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    rule = AlertRule.from_dict(json.load(fh))
                if rule.watchlist_id == watchlist_id:
                    if tenant_id and rule.tenant_id != tenant_id:
                        continue
                    if user_id and rule.user_id != user_id:
                        continue
                    rules.append(rule)
            except Exception:
                pass
        return sorted(rules, key=lambda r: r.created_at)

    def list_by_user(
        self,
        user_id: str,
        tenant_id: str = "default_tenant",
    ) -> list[AlertRule]:
        """
        List all alert rules created by a specific user within a tenant.
        """
        r_dir = self._user_rules_dir(tenant_id, user_id)
        rules: list[AlertRule] = []
        for f in r_dir.glob("rule_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    rule = AlertRule.from_dict(json.load(fh))
                    rules.append(rule)
            except Exception:
                pass
        return sorted(rules, key=lambda r: r.created_at)

    def list_by_tenant(
        self,
        tenant_id: str,
    ) -> list[AlertRule]:
        """List all alert rules for all users within a tenant."""
        tdir = self._root_dir / tenant_id
        if not tdir.is_dir():
            return []
        rules: list[AlertRule] = []
        for f in tdir.glob("*/rule_*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    rules.append(AlertRule.from_dict(json.load(fh)))
            except Exception:
                pass
        return sorted(rules, key=lambda r: r.created_at)

    list_rules = list_by_tenant

    def delete(
        self,
        alert_rule_id: str,
        tenant_id: str = "default_tenant",
        user_id: str = "default_user",
    ) -> bool:
        """Delete an alert rule."""
        db = self._get_db()
        if db:
            try:
                db.execute_mutation(
                    "DELETE FROM alert_rules WHERE rule_id = %s AND tenant_id = %s;",
                    (alert_rule_id, tenant_id),
                    tenant_id=tenant_id,
                )
            except Exception as e:
                logger.debug("DB delete alert_rule failed: %s", e)

        path = self._user_rules_dir(tenant_id, user_id) / f"rule_{alert_rule_id}.json"
        if path.is_file():
            path.unlink()
            return True
        return db is not None
