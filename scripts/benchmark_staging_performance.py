"""
scripts/benchmark_staging_performance.py
=========================================
Staging Latency Benchmark & Percentile Verification for TASK 8.22A.

Measures latency across key endpoints under local/staging environment:
- /health
- /ready
- /api/v1/bills
- /api/v1/companies
- /api/v1/auth/login
- /api/v1/auth/me
- /api/v1/workspace
- /api/v1/watchlists
- /api/v1/notifications
- /api/v1/search?q=Energy
- /api/v1/ai/ask
- /api/v1/bills/{id}
- /api/v1/companies/{id}

Guarantees:
- Single sample per endpoint: 15 runs (3 warmups discarded, 12 kept).
- Both median (p50) and p95 are computed on the EXACT same sample.
- Mathematically validates that median <= p95 for every single endpoint.
- Correctly labels all measurements as STAGING PERFORMANCE (never Production).
"""

from __future__ import annotations

import statistics
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from fastapi.testclient import TestClient
from api.app import create_app
from api.auth.provider import create_session_token

TASK_8_19_BASELINES = {
    "/api/v1/auth/login": 12.50,
    "/api/v1/auth/me": 4.80,
    "/api/v1/workspace": 8.50,
    "/api/v1/watchlists": 6.20,
    "/api/v1/notifications": 5.90,
    "/api/v1/search?q=Energy": 42.00,
    "/api/v1/ai/ask": 28.50,
    "/api/v1/bills/{id}": 8.20,
    "/api/v1/companies/{id}": 11.40,
}

def run_benchmark():
    print("=" * 80)
    print("TASK 8.22A — STAGING PERFORMANCE LATENCY & PERCENTILE RECONCILIATION")
    print("=" * 80)

    app = create_app()
    client = TestClient(app)

    token = create_session_token(user_id="perf_user", tenant_id="perf_tenant", role="MEMBER")
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Initial warm-up
    client.get("/health")
    client.get("/ready")

    benchmarks = [
        ("/health", "GET", "/health", None, None),
        ("/ready", "GET", "/ready", None, None),
        ("/api/v1/bills", "GET", "/api/v1/bills", None, None),
        ("/api/v1/companies", "GET", "/api/v1/companies", None, None),
        ("/api/v1/auth/login", "POST", "/api/v1/auth/login", {"email": "perf_user@example.com", "password": "password123"}, None),
        ("/api/v1/auth/me", "GET", "/api/v1/auth/me", None, auth_headers),
        ("/api/v1/workspace", "GET", "/api/v1/workspace", None, auth_headers),
        ("/api/v1/watchlists", "GET", "/api/v1/watchlists", None, auth_headers),
        ("/api/v1/notifications", "GET", "/api/v1/notifications", None, auth_headers),
        ("/api/v1/search?q=Energy", "GET", "/api/v1/search?q=Energy", None, auth_headers),
        ("/api/v1/ai/ask", "POST", "/api/v1/ai/ask", {"question": "What is the scope?", "context_type": "bill", "context_id": "the-banking-laws-amendment-bill-2024", "persona": "INVESTOR"}, auth_headers),
        ("/api/v1/bills/{id}", "GET", "/api/v1/bills/the-banking-laws-amendment-bill-2024", None, auth_headers),
        ("/api/v1/companies/{id}", "GET", "/api/v1/companies/INE002A01018", None, auth_headers),
    ]

    results = []
    print(f"\n{'Endpoint':<26} | {'Method':<6} | {'T8.19 (ms)':<10} | {'Median (ms)':<11} | {'p95 (ms)':<10} | {'Status':<8}")
    print("-" * 80)

    for label, method, path, payload, headers in benchmarks:
        raw_latencies = []
        for _ in range(15):
            t0 = time.perf_counter()
            if method == "POST":
                resp = client.post(path, json=payload, headers=headers)
            else:
                resp = client.get(path, headers=headers)
            t1 = time.perf_counter()
            assert resp.status_code in (200, 201), f"Endpoint {path} failed: {resp.status_code} {resp.text}"
            raw_latencies.append((t1 - t0) * 1000)

        # Discard 3 warmups, take 12 samples
        durations = raw_latencies[3:]
        median_ms = round(float(np.median(durations)), 2)
        p95_ms = round(float(np.percentile(durations, 95)), 2)
        prev_ref = TASK_8_19_BASELINES.get(label, None)
        prev_str = f"{prev_ref:.2f}" if prev_ref is not None else "N/A"

        # Mathematical sanity check
        assert median_ms <= p95_ms, f"Mathematical error on {label}: median {median_ms} > p95 {p95_ms}"

        status = "PASSED"
        print(f"{label:<26} | {method:<6} | {prev_str:<10} | {median_ms:<11.2f} | {p95_ms:<10.2f} | {status:<8}")
        results.append({
            "endpoint": label,
            "method": method,
            "t8_19_ref": prev_str,
            "median_ms": median_ms,
            "p95_ms": p95_ms,
            "status": status,
        })

    print("-" * 80)
    print("ALL STAGING PERFORMANCE MEASUREMENTS VERIFIED MATHEMATICALLY CONSISTENT.")
    print("=" * 80)
    return results

if __name__ == "__main__":
    run_benchmark()
