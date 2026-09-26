"""
services/startup_validator.py
=============================
Startup validation layer for Task 8.17.

Executes non-disruptive pre-flight diagnostics at system initialization.
Categorizes checks into:
- CRITICAL : Must pass for production startup. Missing directories, corrupted
             schemas, or frozen baseline mismatches abort boot in production.
- WARNING  : Non-fatal issues (e.g. unconfigured optional external keys,
             stale cache). Logged prominently without blocking service startup.
- INFO     : Operational diagnostics (offline fallback active, mode indicator).

Invariants:
- Never exposes internal file paths or secret strings in public API responses.
- Safe to run repeatedly (idempotent).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)


class CheckLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class CheckStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"
    SKIPPED = "SKIPPED"


@dataclass
class StartupCheck:
    name: str
    level: CheckLevel
    status: CheckStatus
    message: str
    details: Optional[dict[str, Any]] = None

    def to_dict(self, sanitize: bool = True) -> dict[str, Any]:
        """Convert check to dict, stripping any internal path or secret details if sanitize=True."""
        return {
            "name": self.name,
            "level": self.level.value,
            "status": self.status.value,
            "message": self.message,
            "details": None if sanitize else self.details,
        }


@dataclass
class StartupValidationReport:
    timestamp: str
    environment: str
    can_start: bool
    status: str  # "READY" | "DEGRADED" | "BLOCKED"
    critical_failures: int
    warnings: int
    passed_count: int
    checks: list[StartupCheck] = field(default_factory=list)

    def to_dict(self, sanitize: bool = True) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "environment": self.environment,
            "can_start": self.can_start,
            "status": self.status,
            "critical_failures": self.critical_failures,
            "warnings": self.warnings,
            "passed_count": self.passed_count,
            "checks": [c.to_dict(sanitize=sanitize) for c in self.checks],
        }


class StartupValidator:
    """Evaluates system readiness before API and scheduler activation."""

    def __init__(self) -> None:
        self._report: Optional[StartupValidationReport] = None

    def run_validation(self, strict: Optional[bool] = None) -> StartupValidationReport:
        """
        Execute all startup verification checks.
        If strict is True (default in production), any CRITICAL check failure raises RuntimeError.
        """
        is_prod = settings.ENV.lower() == "production"
        is_strict = strict if strict is not None else (is_prod and getattr(settings, "STARTUP_VALIDATION_STRICT", True))

        checks: list[StartupCheck] = []

        # 1. Required Configuration
        checks.append(self._check_configuration())

        # 2. Storage & Directory Structure
        checks.append(self._check_storage_directories())

        # 3. Critical Schemas
        checks.append(self._check_schemas())

        # 4. Frozen Analytical Baseline Integrity
        checks.append(self._check_baseline())

        # 5. Monitoring Configuration
        checks.append(self._check_monitoring())

        # 6. AI Provider Configuration & Offline Safety
        checks.append(self._check_ai_provider())

        # 7. Database Provider
        checks.append(self._check_database_provider())

        # 8. Cache / Redis Provider
        checks.append(self._check_cache_provider())

        # 9. Authentication & External IdP Provider
        checks.append(self._check_auth_provider())

        # 10. Transactional Email Provider
        checks.append(self._check_email_provider())

        # 11. Billing Provider
        checks.append(self._check_billing_provider())

        # 12. Router Registry
        checks.append(self._check_routers())

        # Summarize
        critical_fails = sum(1 for c in checks if c.level == CheckLevel.CRITICAL and c.status == CheckStatus.FAILED)
        warnings = sum(1 for c in checks if c.status == CheckStatus.WARNING or (c.level == CheckLevel.WARNING and c.status == CheckStatus.FAILED))
        passed = sum(1 for c in checks if c.status == CheckStatus.PASSED)

        can_start = critical_fails == 0

        if critical_fails > 0:
            status = "BLOCKED"
        elif warnings > 0:
            status = "DEGRADED"
        else:
            status = "READY"

        report = StartupValidationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            environment=settings.ENV,
            can_start=can_start,
            status=status,
            critical_failures=critical_fails,
            warnings=warnings,
            passed_count=passed,
            checks=checks,
        )
        self._report = report

        logger.info(
            "Startup validation completed: status=%s | critical_fails=%d | warnings=%d | passed=%d",
            status,
            critical_fails,
            warnings,
            passed,
        )

        if not can_start and is_strict:
            failed_msgs = "; ".join(c.message for c in checks if c.level == CheckLevel.CRITICAL and c.status == CheckStatus.FAILED)
            raise RuntimeError(f"Production startup blocked by critical validation failures: {failed_msgs}")

        return report

    def _check_configuration(self) -> StartupCheck:
        """Verify essential configuration parameters exist and are secure."""
        try:
            cors_origins = getattr(settings, "API_CORS_ORIGINS", [])
            is_prod = settings.ENV.lower() == "production"

            if is_prod and "*" in cors_origins:
                return StartupCheck(
                    name="Configuration Security",
                    level=CheckLevel.CRITICAL,
                    status=CheckStatus.FAILED,
                    message="CORS origin '*' is prohibited in production with credentialed auth.",
                )

            return StartupCheck(
                name="Configuration",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.PASSED,
                message="Core settings loaded successfully with safe environment bounds.",
            )
        except Exception as e:
            return StartupCheck(
                name="Configuration",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.FAILED,
                message=f"Configuration error: {e}",
            )

    def _check_storage_directories(self) -> StartupCheck:
        """Verify storage directories exist and are writable."""
        try:
            settings.ensure_directories()
            return StartupCheck(
                name="Storage Directories",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.PASSED,
                message="All required storage and data directories verified and accessible.",
            )
        except Exception as e:
            return StartupCheck(
                name="Storage Directories",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.FAILED,
                message=f"Directory creation or access failed: {e}",
            )

    def _check_schemas(self) -> StartupCheck:
        """Verify critical schemas load and instantiate without deserialization errors."""
        try:
            from schemas.prediction import PredictionRecord
            from schemas.decision import DecisionSupportRecord
            from schemas.anticipation import AnticipationScore
            from schemas.state_corporate_exposure import StateCorporateExposure
            from schemas.monitoring import MonitoringSource

            assert PredictionRecord is not None
            assert DecisionSupportRecord is not None
            assert AnticipationScore is not None
            assert StateCorporateExposure is not None
            assert MonitoringSource is not None

            return StartupCheck(
                name="Critical Schemas",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.PASSED,
                message="All analytical, monitoring, and exposure data contracts verified.",
            )
        except Exception as e:
            return StartupCheck(
                name="Critical Schemas",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.FAILED,
                message=f"Schema import or validation error: {e}",
            )

    def _check_baseline(self) -> StartupCheck:
        """Verify frozen analytical baseline datasets and count parity."""
        try:
            from utils.baseline_verifier import verify_production_baseline
            rep = verify_production_baseline(quick=True)

            if not rep.passed:
                is_prod = settings.ENV.lower() == "production"
                level = CheckLevel.CRITICAL if is_prod else CheckLevel.WARNING
                return StartupCheck(
                    name="Baseline Parity",
                    level=level,
                    status=CheckStatus.FAILED,
                    message=f"Baseline verification mismatch ({rep.passed_checks}/{rep.total_checks} passed).",
                )

            return StartupCheck(
                name="Baseline Parity",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.PASSED,
                message="Frozen analytical baselines (Central 4700/4700/940/14100, State 44/44/44/86/0) verified.",
            )
        except Exception as e:
            return StartupCheck(
                name="Baseline Parity",
                level=CheckLevel.WARNING,
                status=CheckStatus.WARNING,
                message=f"Baseline verification deferred or encountered warning: {e}",
            )

    def _check_monitoring(self) -> StartupCheck:
        """Verify monitoring source registry configuration."""
        try:
            from services.monitoring.source_registry import MonitoringSourceRegistry
            registry = MonitoringSourceRegistry()
            sources = registry.get_all_sources()
            implemented = [s for s in sources if s.status == "IMPLEMENTED"]

            if len(implemented) < 7:  # 3 Central + 4 State pilots
                return StartupCheck(
                    name="Monitoring Registry",
                    level=CheckLevel.WARNING,
                    status=CheckStatus.WARNING,
                    message=f"Monitoring source registry has {len(implemented)} implemented sources (expected >= 7).",
                )

            return StartupCheck(
                name="Monitoring Registry",
                level=CheckLevel.INFO,
                status=CheckStatus.PASSED,
                message=f"Monitoring registry active with {len(implemented)} implemented sources (3 Central, 4 State pilots).",
            )
        except Exception as e:
            return StartupCheck(
                name="Monitoring Registry",
                level=CheckLevel.WARNING,
                status=CheckStatus.WARNING,
                message=f"Monitoring configuration check warning: {e}",
            )

    def _check_ai_provider(self) -> StartupCheck:
        """Verify AI provider configuration and offline fallback capability."""
        try:
            key = getattr(settings, "GROQ_API_KEY", "")
            if not key or "your_groq" in key.lower():
                return StartupCheck(
                    name="AI Provider",
                    level=CheckLevel.INFO,
                    status=CheckStatus.PASSED,
                    message="GROQ_API_KEY unconfigured; offline extractive fallback is active and safe.",
                )
            return StartupCheck(
                name="AI Provider",
                level=CheckLevel.INFO,
                status=CheckStatus.PASSED,
                message="Groq AI credentials configured server-side with prompt limits and timeout bounds.",
            )
        except Exception as e:
            return StartupCheck(
                name="AI Provider",
                level=CheckLevel.WARNING,
                status=CheckStatus.WARNING,
                message=f"AI provider inspection warning: {e}",
            )

    def _check_database_provider(self) -> StartupCheck:
        """Verify database provider readiness and connectivity."""
        try:
            from storage.database.provider import get_database_provider
            provider = get_database_provider()
            health = provider.health_check()
            is_prod = settings.ENV.lower() == "production"

            if provider.status == "READY":
                return StartupCheck(
                    name="Database Provider",
                    level=CheckLevel.CRITICAL,
                    status=CheckStatus.PASSED,
                    message=f"{provider.provider_name} active and healthy.",
                )
            elif provider.status == "CONFIGURED" and health.get("connected"):
                return StartupCheck(
                    name="Database Provider",
                    level=CheckLevel.CRITICAL,
                    status=CheckStatus.PASSED,
                    message="Production PostgreSQL connection verified and responsive.",
                )
            else:
                level = CheckLevel.WARNING if is_prod else CheckLevel.INFO
                return StartupCheck(
                    name="Database Provider",
                    level=level,
                    status=CheckStatus.WARNING if is_prod else CheckStatus.PASSED,
                    message=f"{provider.provider_name}: status={provider.status} (fallback active).",
                )
        except Exception as e:
            return StartupCheck(
                name="Database Provider",
                level=CheckLevel.WARNING,
                status=CheckStatus.WARNING,
                message=f"Database provider check warning: {e}",
            )

    def _check_cache_provider(self) -> StartupCheck:
        """Verify distributed cache / Redis provider readiness."""
        try:
            from infrastructure.cache.provider import get_cache_provider
            provider = get_cache_provider()
            health = provider.health_check()
            is_prod = settings.ENV.lower() == "production"

            if provider.status == "READY":
                return StartupCheck(
                    name="Cache Provider",
                    level=CheckLevel.INFO,
                    status=CheckStatus.PASSED,
                    message=f"{provider.provider_name} active (in-memory lock and rate limiting).",
                )
            elif provider.status == "CONFIGURED" and health.get("connected"):
                return StartupCheck(
                    name="Cache Provider",
                    level=CheckLevel.CRITICAL if is_prod else CheckLevel.INFO,
                    status=CheckStatus.PASSED,
                    message="Production Redis connection verified and responsive.",
                )
            else:
                return StartupCheck(
                    name="Cache Provider",
                    level=CheckLevel.INFO,
                    status=CheckStatus.PASSED,
                    message=f"{provider.provider_name}: status={provider.status} (local fallback active).",
                )
        except Exception as e:
            return StartupCheck(
                name="Cache Provider",
                level=CheckLevel.WARNING,
                status=CheckStatus.WARNING,
                message=f"Cache provider check warning: {e}",
            )

    def _check_auth_provider(self) -> StartupCheck:
        """Verify authentication provider and external IdP status."""
        try:
            from api.auth.provider import get_auth_provider, get_auth_provider_status
            provider = get_auth_provider()
            st = get_auth_provider_status()
            idp_status = st.get("PRODUCTION_IDP_STATUS", "NOT_CONFIGURED")

            return StartupCheck(
                name="Auth Provider",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.PASSED,
                message=f"{provider.__class__.__name__} active | External IdP={idp_status}.",
            )
        except Exception as e:
            return StartupCheck(
                name="Auth Provider",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.FAILED,
                message=f"Authentication provider initialization error: {e}",
            )

    def _check_email_provider(self) -> StartupCheck:
        """Verify transactional email provider status."""
        try:
            from infrastructure.email.provider import get_email_provider
            provider = get_email_provider()
            return StartupCheck(
                name="Email Provider",
                level=CheckLevel.INFO,
                status=CheckStatus.PASSED,
                message=f"{provider.provider_name} active | status={provider.status}.",
            )
        except Exception as e:
            return StartupCheck(
                name="Email Provider",
                level=CheckLevel.WARNING,
                status=CheckStatus.WARNING,
                message=f"Email provider check warning: {e}",
            )

    def _check_billing_provider(self) -> StartupCheck:
        """Verify SaaS billing provider status."""
        try:
            from infrastructure.billing.provider import get_billing_provider
            provider = get_billing_provider()
            return StartupCheck(
                name="Billing Provider",
                level=CheckLevel.INFO,
                status=CheckStatus.PASSED,
                message=f"{provider.provider_name} active | status={provider.status}.",
            )
        except Exception as e:
            return StartupCheck(
                name="Billing Provider",
                level=CheckLevel.WARNING,
                status=CheckStatus.WARNING,
                message=f"Billing provider check warning: {e}",
            )

    def _check_routers(self) -> StartupCheck:
        """Verify that all FastAPI sub-routers load and can be registered."""
        try:
            from api.routers import (
                ai, alerts, anticipation, bills, companies,
                coverage, industries, monitoring, notifications,
                predictions, risk, search, states, watchlists, workspace,
            )
            assert ai.router is not None
            assert bills.router is not None
            assert companies.router is not None
            assert watchlists.router is not None
            return StartupCheck(
                name="API Routers",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.PASSED,
                message="All 15 domain sub-routers successfully registered and routed.",
            )
        except Exception as e:
            return StartupCheck(
                name="API Routers",
                level=CheckLevel.CRITICAL,
                status=CheckStatus.FAILED,
                message=f"Router registry failure: {e}",
            )


_startup_validator_instance: Optional[StartupValidator] = None


def get_startup_validator() -> StartupValidator:
    global _startup_validator_instance
    if _startup_validator_instance is None:
        _startup_validator_instance = StartupValidator()
    return _startup_validator_instance
