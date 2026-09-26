#!/usr/bin/env python3
"""
scripts/production_deployment_gate.py
=====================================
Task 8.21 — CI/CD Production Gate

This script is the authoritative production deployment gate.
It verifies all pre-deployment conditions before any cloud release.

Production deployment is BLOCKED if any gate condition fails:
  - pytest failures
  - frontend test / typecheck / build failures
  - baseline changes
  - State predictions != 0
  - Analytical artifacts changed unexpectedly
  - Security tests fail

Usage:
    python scripts/production_deployment_gate.py
    python scripts/production_deployment_gate.py --skip-frontend
    python scripts/production_deployment_gate.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Gate result data structure
# ---------------------------------------------------------------------------

@dataclass
class GateResult:
    gate_name: str
    passed: bool
    duration_seconds: float = 0.0
    output: str = ""
    error: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class DeploymentGateReport:
    timestamp: str
    gates: List[GateResult] = field(default_factory=list)
    overall_pass: bool = False
    blocking_failures: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "overall_pass": self.overall_pass,
            "blocking_failures": self.blocking_failures,
            "gates": [
                {
                    "gate": g.gate_name,
                    "passed": g.passed,
                    "duration_s": round(g.duration_seconds, 2),
                    "error": g.error or None,
                }
                for g in self.gates
            ],
        }


# ---------------------------------------------------------------------------
# Gate runner
# ---------------------------------------------------------------------------

class ProductionDeploymentGate:
    """
    Runs all CI/CD gates required before production deployment.
    Any blocking gate failure prevents deployment.
    """

    def __init__(self, project_root: Path, skip_frontend: bool = False,
                 dry_run: bool = False) -> None:
        self.project_root = project_root
        self.skip_frontend = skip_frontend
        self.dry_run = dry_run
        self.gates: List[GateResult] = []

    # ── Internal helpers ────────────────────────────────────────────────────

    def _run(self, cmd: List[str], cwd: Optional[Path] = None,
             timeout: int = 1800) -> GateResult:
        """Run a subprocess and return gate result."""
        gate_name = " ".join(cmd[:3])
        cwd = cwd or self.project_root
        t0 = time.time()

        if self.dry_run:
            print(f"  [DRY-RUN] Would run: {' '.join(cmd)}")
            return GateResult(gate_name=gate_name, passed=True,
                              duration_seconds=0.0, output="[dry-run]")

        try:
            result = subprocess.run(
                cmd, cwd=str(cwd),
                capture_output=True, text=True, timeout=timeout
            )
            duration = time.time() - t0
            passed = result.returncode == 0
            return GateResult(
                gate_name=gate_name,
                passed=passed,
                duration_seconds=duration,
                output=result.stdout[-3000:] if result.stdout else "",
                error=result.stderr[-2000:] if not passed and result.stderr else "",
            )
        except subprocess.TimeoutExpired:
            return GateResult(gate_name=gate_name, passed=False,
                              duration_seconds=timeout,
                              error=f"TIMEOUT after {timeout}s")
        except Exception as exc:
            return GateResult(gate_name=gate_name, passed=False,
                              error=str(exc))

    def _add(self, result: GateResult) -> None:
        self.gates.append(result)
        status = "[PASS]" if result.passed else "[FAIL]"
        print(f"  {status}  {result.gate_name}  ({result.duration_seconds:.1f}s)")
        if not result.passed and result.error:
            for line in result.error.splitlines()[-10:]:
                print(f"         {line}")

    # ── Gate implementations ────────────────────────────────────────────────

    def gate_git_data_immutability(self) -> GateResult:
        """Verify frozen analytical data has not been modified."""
        print("\n[GATE 1] Frozen data immutability (git status data/)...")
        result = self._run(["git", "status", "--short", "data/"])
        if result.passed and not self.dry_run:
            # Parse output — empty = no modifications
            lines = [l.strip() for l in result.output.splitlines() if l.strip()]
            if lines:
                result.passed = False
                result.error = (
                    f"BLOCKING: {len(lines)} analytical data file(s) modified:\n" +
                    "\n".join(lines)
                )
            else:
                result.output = "0 modifications to analytical data -- CLEAN"
        elif self.dry_run:
            result.output = "[dry-run] Skipped git status parsing"
        return result

    def gate_backend_tests(self) -> GateResult:
        """Run full backend test suite."""
        print("\n[GATE 2] Backend regression: pytest tests/...")
        return self._run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
            timeout=1800,
        )

    def gate_security_tests(self) -> GateResult:
        """Run critical security test suite."""
        print("\n[GATE 3] Security regression suite...")
        security_tests = [
            "tests/test_saas_auth_lifecycle.py",
            "tests/test_security_idor.py",
            "tests/test_saas_multitenant_e2e.py",
            "tests/test_security_headers_ratelimit.py",
            "tests/test_analytical_firewall_regression.py",
            "tests/test_frozen_immutability.py",
        ]
        return self._run(
            [sys.executable, "-m", "pytest"] + security_tests + ["-q", "--tb=short"],
            timeout=600,
        )

    def gate_frozen_baseline_verification(self) -> GateResult:
        """Run authoritative baseline verification."""
        print("\n[GATE 4] Frozen baseline verification...")
        result = self._run(
            [sys.executable, "scripts/verify_frozen_baseline_exact.py"],
            timeout=300,
        )
        # Check for BASELINE_VERIFIED in output
        if result.passed and "BASELINE_VERIFIED" not in result.output:
            # Non-zero return but contains pass signal
            if "FAILED" in result.output or "MISMATCH" in result.output:
                result.passed = False
                result.error = "Baseline mismatch detected — deployment blocked"
        return result

    def gate_state_predictions_zero(self) -> GateResult:
        """Verify State predictions remain exactly 0."""
        print("\n[GATE 5] State Prediction Firewall (must be 0)...")
        baseline_path = self.project_root / "docs" / "production_baseline.json"
        t0 = time.time()
        try:
            with open(baseline_path) as f:
                baseline = json.load(f)
            state_preds = baseline["state_baseline"].get("stock_predictions_count", -1)
            passed = state_preds == 0
            return GateResult(
                gate_name="state_predictions_zero",
                passed=passed,
                duration_seconds=time.time() - t0,
                output=f"State predictions = {state_preds}",
                error="" if passed else f"BLOCKING: State predictions = {state_preds}, must be 0",
            )
        except Exception as exc:
            return GateResult(
                gate_name="state_predictions_zero",
                passed=False,
                duration_seconds=time.time() - t0,
                error=str(exc),
            )

    def gate_frontend_tests(self) -> GateResult:
        """Run frontend unit tests."""
        if self.skip_frontend:
            print("\n[GATE 6] Frontend tests: SKIPPED (--skip-frontend)")
            return GateResult(gate_name="frontend_tests", passed=True,
                              output="SKIPPED", duration_seconds=0)
        print("\n[GATE 6] Frontend unit tests: npm run test...")
        frontend_dir = self.project_root / "frontend"
        return self._run(["npm", "run", "test", "--", "--run"],
                         cwd=frontend_dir, timeout=300)

    def gate_frontend_typecheck(self) -> GateResult:
        """Run TypeScript type check."""
        if self.skip_frontend:
            print("\n[GATE 7] Frontend typecheck: SKIPPED")
            return GateResult(gate_name="frontend_typecheck", passed=True,
                              output="SKIPPED", duration_seconds=0)
        print("\n[GATE 7] Frontend typecheck: npm run typecheck...")
        frontend_dir = self.project_root / "frontend"
        return self._run(["npm", "run", "typecheck"],
                         cwd=frontend_dir, timeout=300)

    def gate_frontend_build(self) -> GateResult:
        """Build production frontend bundle."""
        if self.skip_frontend:
            print("\n[GATE 8] Frontend build: SKIPPED")
            return GateResult(gate_name="frontend_build", passed=True,
                              output="SKIPPED", duration_seconds=0)
        print("\n[GATE 8] Frontend build: npm run build...")
        frontend_dir = self.project_root / "frontend"
        return self._run(["npm", "run", "build"],
                         cwd=frontend_dir, timeout=600)

    # ── Main gate runner ────────────────────────────────────────────────────

    def run_all_gates(self) -> DeploymentGateReport:
        """Execute all gates in sequence; return report."""
        import datetime
        report = DeploymentGateReport(
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

        print("=" * 70)
        print("TASK 8.21 — PRODUCTION DEPLOYMENT GATE")
        print("=" * 70)
        if self.dry_run:
            print("  MODE: DRY-RUN (commands not executed)")
        print()

        gate_methods = [
            self.gate_git_data_immutability,
            self.gate_backend_tests,
            self.gate_security_tests,
            self.gate_frozen_baseline_verification,
            self.gate_state_predictions_zero,
            self.gate_frontend_tests,
            self.gate_frontend_typecheck,
            self.gate_frontend_build,
        ]

        blocking_failures: List[str] = []
        for gate_method in gate_methods:
            result = gate_method()
            self._add(result)
            report.gates.append(result)
            if not result.passed:
                blocking_failures.append(f"{result.gate_name}: {result.error[:200]}")

        report.blocking_failures = blocking_failures
        report.overall_pass = len(blocking_failures) == 0

        # ── Summary ──────────────────────────────────────────────────────────
        print("\n" + "=" * 70)
        if report.overall_pass:
            print("[OK] ALL GATES PASSED -- DEPLOYMENT AUTHORIZED")
        else:
            print("[BLOCKED] DEPLOYMENT BLOCKED -- GATE FAILURES:")
            for failure in blocking_failures:
                print(f"    - {failure[:120]}")
        print("=" * 70)

        return report


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Task 8.21 Production Deployment Gate"
    )
    parser.add_argument("--skip-frontend", action="store_true",
                        help="Skip frontend gates (for backend-only changes)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without executing them")
    parser.add_argument("--output-json", type=str, default=None,
                        help="Write JSON gate report to this file")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    gate = ProductionDeploymentGate(
        project_root=project_root,
        skip_frontend=args.skip_frontend,
        dry_run=args.dry_run,
    )
    report = gate.run_all_gates()

    if args.output_json:
        with open(args.output_json, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n  Report written to: {args.output_json}")

    return 0 if report.overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
