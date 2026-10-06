"""
services/monitoring/source_url_validator.py
============================================
Task 8.26 Phase 14 — SSRF Protection for the live-fetch pipeline.

Validates that a source URL is:
1. A well-formed HTTP/HTTPS URL (no file://, ftp://, etc.)
2. Not pointing to a private/reserved IP (localhost, 127.x, 10.x, 172.16-31.x, 192.168.x)
3. Not pointing to a cloud metadata endpoint (169.254.169.254, etc.)
4. In the configured allowlist of legislative authority domains (if allowlist is set)

Usage::

    from services.monitoring.source_url_validator import SourceURLValidator, URLValidationError

    validator = SourceURLValidator()
    try:
        safe_url = validator.validate("https://loksabha.nic.in/bills/list.html")
    except URLValidationError as exc:
        # Reject the source — log, not raise to user
        logger.error("SSRF block: %s", exc)
"""

from __future__ import annotations

import ipaddress
import logging
import re
import urllib.parse
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Blocked schemes — only http and https are permitted
_ALLOWED_SCHEMES = frozenset({"http", "https"})

# Cloud metadata endpoints (GCP, AWS, Azure, Oracle)
_METADATA_HOSTS = frozenset(
    {
        "169.254.169.254",      # AWS / GCP / Azure IMDS
        "metadata.google.internal",
        "metadata.azure.com",
        "100.100.100.200",      # Alibaba ECS metadata
    }
)

# Regex to catch embedded credentials in URL
_CREDENTIALS_RE = re.compile(r"https?://[^@]+@")

# Known Indian legislative authority domain fragments (allowlist hints)
# These are checked with ``endswith`` so subdomains are covered.
KNOWN_LEGISLATIVE_DOMAINS: tuple[str, ...] = (
    "nic.in",
    "gov.in",
    "parliament.in",
    "rajyasabha.in",
    "rajyasabha.nic.in",
    "loksabha.nic.in",
    "egazette.nic.in",
    "egazette.gov.in",
    "indiacode.nic.in",
    "indiacode.gov.in",
    "legislative.gov.in",
    "prsindia.org",
    "lawmin.gov.in",
    "mca.gov.in",
    "sebi.gov.in",
    "rbi.org.in",
    "cbic.gov.in",
    "cbdt.gov.in",
    "irdai.gov.in",
    "trai.gov.in",
    "pib.gov.in",
    "finmin.nic.in",
    "mof.gov.in",
    # State-specific portals (partial list)
    "aponline.gov.in",
    "karnataka.gov.in",
    "kerala.gov.in",
    "telangana.gov.in",
    "ap.gov.in",
    "tamilnadu.gov.in",
    "maharashtra.gov.in",
    "delhi.gov.in",
    "gujleg.gov.in",
    "rajasthan.gov.in",
    "mpvidhansabha.mp.gov.in",
    "vidhansabha.uk.gov.in",
    "punjabassembly.org",
    "haryana.gov.in",
    "jharkhandassembly.gov.in",
    "biharlegislature.gov.in",
    "odishaassembly.nic.in",
    "assamassembly.gov.in",
    "manipurassembly.nic.in",
    "nagalandlegislature.gov.in",
    "sikkim.nic.in",
    "himachal.nic.in",
    "jklegislativeassembly.nic.in",
)


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class URLValidationError(ValueError):
    """Raised when a source URL fails SSRF/allowlist validation."""


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class SourceURLValidator:
    """
    SSRF-protective URL validator for the live legislative fetch pipeline.

    Parameters
    ----------
    allowlist_domains:
        Optional tuple of domain suffixes. If provided, the URL's hostname
        must end with one of these suffixes. If None, domain allowlist is
        not enforced (only SSRF rules apply).
    enforce_allowlist:
        If True and allowlist_domains is set, reject URLs not in the list.
        Defaults to False — log a warning but do not block unknown domains.
    """

    def __init__(
        self,
        allowlist_domains: Optional[tuple[str, ...]] = None,
        enforce_allowlist: bool = False,
    ) -> None:
        self._allowlist = allowlist_domains or KNOWN_LEGISLATIVE_DOMAINS
        self._enforce_allowlist = enforce_allowlist

    def validate(self, url: str) -> str:
        """
        Validate ``url`` against SSRF rules and optional domain allowlist.

        Returns the original URL if valid.
        Raises URLValidationError with a descriptive message if invalid.
        """
        if not url or not isinstance(url, str):
            raise URLValidationError("URL must be a non-empty string.")

        url = url.strip()

        # 1. Embedded credentials
        if _CREDENTIALS_RE.match(url):
            raise URLValidationError(
                f"URL contains embedded credentials — rejected for SSRF safety: {url[:60]!r}"
            )

        # 2. Parse
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception as exc:
            raise URLValidationError(f"Could not parse URL: {exc}") from exc

        # 3. Scheme
        if parsed.scheme not in _ALLOWED_SCHEMES:
            raise URLValidationError(
                f"URL scheme {parsed.scheme!r} is not permitted. "
                f"Only {sorted(_ALLOWED_SCHEMES)} are allowed."
            )

        # 4. Hostname presence
        hostname = parsed.hostname or ""
        if not hostname:
            raise URLValidationError("URL has no hostname.")

        # 5. Metadata endpoint block
        if hostname in _METADATA_HOSTS:
            raise URLValidationError(
                f"URL targets a cloud metadata endpoint ({hostname!r}) — SSRF blocked."
            )

        # 6. Private / reserved IP block
        # NOTE: URLValidationError inherits from ValueError, so we MUST NOT put
        # the raise inside the try/except ValueError block — it would be swallowed.
        _is_private_ip = False
        try:
            addr = ipaddress.ip_address(hostname)
            _is_private_ip = (
                addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved
            )
        except ValueError:
            # Not an IP address literal — hostname is a domain name; proceed
            pass
        if _is_private_ip:
            raise URLValidationError(
                f"URL resolves to a private/reserved IP address ({hostname!r}) — SSRF blocked."
            )

        # 7. Localhost / numeric loopback patterns
        lower_host = hostname.lower()
        if lower_host in ("localhost", "ip6-localhost", "::1", "0.0.0.0"):
            raise URLValidationError(
                f"URL targets localhost ({hostname!r}) — SSRF blocked."
            )

        # 8. Domain allowlist (warn or block)
        in_allowlist = any(lower_host.endswith(domain) for domain in self._allowlist)
        if not in_allowlist:
            msg = (
                f"URL hostname {hostname!r} is not in the known legislative authority "
                f"domain allowlist."
            )
            if self._enforce_allowlist:
                raise URLValidationError(msg + " SSRF enforcement active — rejected.")
            else:
                logger.warning("[8.26 SSRF] %s (enforcement off — allowed but flagged)", msg)

        return url

    def is_valid(self, url: str) -> bool:
        """Return True if the URL passes validation, False otherwise."""
        try:
            self.validate(url)
            return True
        except URLValidationError:
            return False

    def classify_domain(self, url: str) -> str:
        """
        Return a domain classification string for telemetry:
        'KNOWN_LEGISLATIVE' | 'UNKNOWN' | 'INVALID'
        """
        try:
            parsed = urllib.parse.urlparse(url.strip())
            hostname = (parsed.hostname or "").lower()
            if any(hostname.endswith(d) for d in self._allowlist):
                return "KNOWN_LEGISLATIVE"
            return "UNKNOWN"
        except Exception:
            return "INVALID"


# Module-level singleton with defaults (no enforcement)
_default_validator = SourceURLValidator(enforce_allowlist=False)


def validate_source_url(url: str) -> str:
    """Convenience wrapper using the default validator."""
    return _default_validator.validate(url)


def is_valid_source_url(url: str) -> bool:
    """Convenience boolean check using the default validator."""
    return _default_validator.is_valid(url)
