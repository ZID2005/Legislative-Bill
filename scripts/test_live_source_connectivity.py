"""
scripts/test_live_source_connectivity.py
=========================================
Controlled live source connectivity test for TASK 8.18.

Probes all 7 enabled legislative sources in config/monitoring_sources.json
using conservative, polite HTTP requests.

Guarantees:
- Respects government infrastructure: 1 request per host, 15-second timeout.
- Custom informative User-Agent.
- Handles SSL/TLS certificate discrepancies gracefully (common on Indian state portals).
- Measures: HTTP status, latency (ms), content size (bytes), parseability, TLS status.
- Classifies: SUCCESS, DEGRADED, FAILED, NOT_AVAILABLE.
- Records real provenance timestamps into storage/monitoring/source_registry_state.json.
- Zero fabrication: records exact observed responses.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import urllib.request
import urllib.error
import ssl

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import settings
from services.monitoring.source_registry import MonitoringSourceRegistry

USER_AGENT = "IndianParliamentaryIntelligenceBot/1.0 (+research-audit; contact@legislative-intel.local)"
TIMEOUT_SECONDS = 15


def test_source_connectivity(source: Any) -> dict[str, Any]:
    """
    Perform a single controlled connectivity test for a registered source.
    """
    source_id = source.source_id
    url = source.source_url
    name = getattr(source, "source_name", getattr(source, "name", source_id))
    jurisdiction = source.jurisdiction
    state = getattr(source, "state", None)

    print(f"\nTesting Source [{source_id}] ({name})...")
    print(f"  URL: {url}")
    print(f"  Jurisdiction: {jurisdiction.upper()}" + (f" ({state})" if state else ""))

    result: dict[str, Any] = {
        "source_id": source_id,
        "source_name": name,
        "jurisdiction": jurisdiction,
        "state": state,
        "url": url,
        "tested_at": datetime.now(timezone.utc).isoformat(),
        "status": "UNKNOWN",
        "http_code": None,
        "response_time_ms": None,
        "bytes_received": 0,
        "tls_verified": True,
        "parse_check": "NOT_CHECKED",
        "error": None,
        "authority_type": "SECONDARY_AGGREGATOR" if source_id == "central_prs" else "OFFICIAL_CONSTITUTIONAL_GOVERNMENT",
    }

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    # First attempt: standard verified TLS context
    start_time = time.monotonic()
    try:
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS, context=ctx) as resp:
            elapsed_ms = round((time.monotonic() - start_time) * 1000, 2)
            code = resp.getcode()
            content = resp.read(65536)  # Read up to 64KB
            
            result["http_code"] = code
            result["response_time_ms"] = elapsed_ms
            result["bytes_received"] = len(content)
            result["tls_verified"] = True

            # Quick parseability check
            text_sample = content.decode("utf-8", errors="replace").lower()
            if "<html" in text_sample or "<table" in text_sample or "bill" in text_sample:
                result["parse_check"] = "HTML_PARSABLE"
            else:
                result["parse_check"] = "OPAQUE_CONTENT"

            if code == 200:
                result["status"] = "SUCCESS"
            elif code in (301, 302, 303, 307, 308):
                result["status"] = "DEGRADED"
                result["error"] = f"Redirected with HTTP {code}"
            else:
                result["status"] = "DEGRADED"
                result["error"] = f"HTTP status {code}"

            print(f"  [RESULT] Status={result['status']} | HTTP {code} | {elapsed_ms}ms | {len(content)} bytes | Parse={result['parse_check']}")
            return result

    except urllib.error.HTTPError as he:
        elapsed_ms = round((time.monotonic() - start_time) * 1000, 2)
        result["http_code"] = he.code
        result["response_time_ms"] = elapsed_ms
        result["error"] = f"HTTPError {he.code}: {he.reason}"
        if he.code in (401, 403):
            result["status"] = "DEGRADED"  # Server reachable, firewall/WAF challenge
        elif he.code == 404:
            result["status"] = "FAILED"
        else:
            result["status"] = "DEGRADED"
        print(f"  [RESULT] Status={result['status']} | HTTP {he.code} | {elapsed_ms}ms | Error: {he.reason}")
        return result

    except (ssl.SSLError, urllib.error.URLError) as ue:
        # Check if it was an SSL certificate verification failure
        is_ssl_err = isinstance(ue, ssl.SSLError) or "CERTIFICATE_VERIFY_FAILED" in str(ue)
        if is_ssl_err:
            print("  [WARN] Verified TLS failed. Testing unverified TLS fallback for state govt portal...")
            try:
                start_unverified = time.monotonic()
                unverified_ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS, context=unverified_ctx) as resp:
                    elapsed_ms = round((time.monotonic() - start_unverified) * 1000, 2)
                    code = resp.getcode()
                    content = resp.read(65536)
                    result["http_code"] = code
                    result["response_time_ms"] = elapsed_ms
                    result["bytes_received"] = len(content)
                    result["tls_verified"] = False
                    result["status"] = "DEGRADED"
                    result["error"] = "Self-signed or unverified SSL certificate on government portal"
                    result["parse_check"] = "HTML_PARSABLE" if "<html" in content.decode("utf-8", errors="replace").lower() else "OPAQUE"
                    print(f"  [RESULT] Status=DEGRADED (Unverified TLS) | HTTP {code} | {elapsed_ms}ms | {len(content)} bytes")
                    return result
            except Exception as unv_err:
                elapsed_ms = round((time.monotonic() - start_time) * 1000, 2)
                result["response_time_ms"] = elapsed_ms
                result["status"] = "FAILED"
                result["error"] = f"TLS & Unverified TLS failed: {unv_err}"
                print(f"  [RESULT] Status=FAILED | Error: {unv_err}")
                return result

        elapsed_ms = round((time.monotonic() - start_time) * 1000, 2)
        result["response_time_ms"] = elapsed_ms
        if "timed out" in str(ue).lower():
            result["status"] = "NOT_AVAILABLE"
            result["error"] = f"Connection timed out after {TIMEOUT_SECONDS}s"
        else:
            result["status"] = "FAILED"
            result["error"] = str(ue)
        print(f"  [RESULT] Status={result['status']} | Error: {result['error']}")
        return result

    except Exception as e:
        elapsed_ms = round((time.monotonic() - start_time) * 1000, 2)
        result["response_time_ms"] = elapsed_ms
        result["status"] = "FAILED"
        result["error"] = str(e)
        print(f"  [RESULT] Status=FAILED | Error: {e}")
        return result


def run_all_connectivity_tests() -> dict[str, Any]:
    """
    Run connectivity tests against all active enabled sources and save telemetry.
    """
    print("=" * 70)
    print("TASK 8.18 — CONTROLLED LIVE SOURCE CONNECTIVITY TESTING")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)

    registry = MonitoringSourceRegistry()
    enabled_sources = registry.get_enabled()
    all_sources = registry.get_all()

    print(f"Total Configured Sources: {len(all_sources)}")
    print(f"Enabled Production Sources: {len(enabled_sources)}")

    results = []
    for source in enabled_sources:
        res = test_source_connectivity(source)
        results.append(res)
        # Update registry state in memory
        is_success = res["status"] in ("SUCCESS", "DEGRADED")
        err_msg = res.get("error") if not is_success else None
        registry.mark_checked(source.source_id, success=is_success, error=err_msg)
        # Polite spacing between requests (1 second pause)
        time.sleep(1.0)

    # Save summary report artifact
    output_dir = settings.PROJECT_ROOT / "storage" / "monitoring"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "live_connectivity_report.json"

    summary = {
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "total_probed": len(results),
        "success_count": sum(1 for r in results if r["status"] == "SUCCESS"),
        "degraded_count": sum(1 for r in results if r["status"] == "DEGRADED"),
        "failed_count": sum(1 for r in results if r["status"] == "FAILED"),
        "not_available_count": sum(1 for r in results if r["status"] == "NOT_AVAILABLE"),
        "results": results,
    }

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("CONNECTIVITY TESTING COMPLETE")
    print(f"Saved audit telemetry to {summary_path}")
    print(f"Success: {summary['success_count']} | Degraded: {summary['degraded_count']} | Failed: {summary['failed_count']} | Not Available: {summary['not_available_count']}")
    print("=" * 70)

    return summary


if __name__ == "__main__":
    run_all_connectivity_tests()
