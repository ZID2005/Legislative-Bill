"""
scripts/benchmark_task_8_20_performance.py
=========================================
Performance benchmark measuring latency across required Task 8.20 endpoints:
- /auth/login
- /auth/me
- /workspace
- /watchlists
- /notifications
- /search
- /ai/ask
- /bills/{id}
- /companies/{id}

Compares against Task 8.19 performance measurements and reports diff.
"""

from __future__ import annotations

import statistics
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from api.app import create_app
from api.auth.provider import create_session_token

# Reference Task 8.19 Baselines (median ms)
TASK_8_19_BASELINES = {
    "/auth/login": 12.5,
    "/auth/me": 4.8,
    "/workspace": 8.5,
    "/watchlists": 6.2,
    "/notifications": 5.9,
    "/search": 42.0,
    "/ai/ask": 28.5,
    "/bills/{id}": 8.2,
    "/companies/{id}": 11.4,
}

def benchmark():
    print("=" * 70)
    print("TASK 8.20 PERFORMANCE LATENCY BENCHMARK & REGRESSION COMPARISON")
    print("=" * 70)

    app = create_app()
    client = TestClient(app)

    # Prepare auth token
    token = create_session_token(user_id="perf_user", tenant_id="perf_tenant", role="MEMBER")
    headers = {"Authorization": f"Bearer {token}"}

    # Warm-up request
    client.get("/health")

    endpoints = [
        ("/auth/login", "POST", "/api/v1/auth/login", {"email": "perf_user@example.com", "password": "password123"}, {}),
        ("/auth/me", "GET", "/api/v1/auth/me", None, headers),
        ("/workspace", "GET", "/api/v1/workspace", None, headers),
        ("/watchlists", "GET", "/api/v1/watchlists", None, headers),
        ("/notifications", "GET", "/api/v1/notifications", None, headers),
        ("/search", "GET", "/api/v1/search?q=Energy", None, headers),
        ("/ai/ask", "POST", "/api/v1/ai/ask", {"question": "What is the scope?", "context_type": "bill", "context_id": "the-banking-laws-amendment-bill-2024", "persona": "INVESTOR"}, headers),
        ("/bills/{id}", "GET", "/api/v1/bills/the-banking-laws-amendment-bill-2024", None, headers),
        ("/companies/{id}", "GET", "/api/v1/companies/INE002A01018", None, headers),
    ]

    results = []

    print(f"\n{'Endpoint':<20} | {'T8.19 (ms)':<10} | {'T8.20 (ms)':<10} | {'Diff (ms)':<10} | {'Status':<10}")
    print("-" * 70)

    for label, method, path, payload, req_headers in endpoints:
        latencies = []
        for _ in range(7):
            t0 = time.perf_counter()
            if method == "POST":
                resp = client.post(path, json=payload, headers=req_headers)
            else:
                resp = client.get(path, headers=req_headers)
            t1 = time.perf_counter()
            assert resp.status_code in (200, 201), f"Endpoint {path} failed: {resp.status_code} {resp.text}"
            latencies.append((t1 - t0) * 1000)

        # Drop first warm-up iteration and take median
        durations = latencies[1:]
        median_ms = round(statistics.median(durations), 2)
        prev_ms = TASK_8_19_BASELINES.get(label, 10.0)
        diff_ms = round(median_ms - prev_ms, 2)
        status = "PASSED" if diff_ms < 50.0 else "INVESTIGATE"

        print(f"{label:<20} | {prev_ms:<10.2f} | {median_ms:<10.2f} | {diff_ms:+<10.2f} | {status:<10}")
        results.append({
            "endpoint": label,
            "previous_ms": prev_ms,
            "current_ms": median_ms,
            "diff_ms": diff_ms,
            "status": status,
        })

    print("-" * 70)
    print("ALL ENDPOINT LATENCY MEASUREMENTS COMPLETED SUCCESSFULLY.")
    return results

if __name__ == "__main__":
    benchmark()
