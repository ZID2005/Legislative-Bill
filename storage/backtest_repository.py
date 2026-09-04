"""
storage/backtest_repository.py
===============================
BacktestRepository — persistence layer for historical backtest run artefacts (Task 6.4).

Stores backtest runs under subdirectories in `data/backtests/<run_id>/`:
- `backtest_report.json`
- `model_comparison.json`
- `strategy_metrics.json`
- `leakage_report.json`
- `prediction_results.parquet`
- `equity_curve.png`
- `drawdown_curve.png`
- `prediction_vs_actual.png`
- `model_comparison.png`

Supports:
- `save(run_id, ...)`
- `load(run_id)`
- `exists(run_id)`
- `list_runs()`
- `get_latest_run()`
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from config.logging_config import get_logger
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


class BacktestRepository:
    """
    Persistence layer for backtest run output artefacts.

    Parameters
    ----------
    backtest_dir : Path, optional
        Root directory for storing backtest runs.
        Defaults to `settings.BACKTEST_DIR` (`data/backtests/`).
    """

    REPORT_FILE = "backtest_report.json"
    MODEL_COMPARISON_FILE = "model_comparison.json"
    STRATEGY_METRICS_FILE = "strategy_metrics.json"
    LEAKAGE_REPORT_FILE = "leakage_report.json"
    PREDICTION_RESULTS_FILE = "prediction_results.parquet"
    EQUITY_CURVE_FILE = "equity_curve.png"
    DRAWDOWN_CURVE_FILE = "drawdown_curve.png"
    PREDICTION_VS_ACTUAL_FILE = "prediction_vs_actual.png"
    MODEL_COMPARISON_PLOT_FILE = "model_comparison.png"
    # Task 6.4.1 additions
    PORTFOLIO_TIMESERIES_FILE = "portfolio_timeseries.parquet"
    OVERLAP_REPORT_FILE = "overlap_report.json"
    FINANCIAL_VALIDATION_FILE = "financial_validation_report.json"
    BENCHMARK_METRICS_FILE = "benchmark_metrics.json"

    def __init__(self, backtest_dir: Optional[Path] = None) -> None:
        from config.settings import settings

        self._root: Path = backtest_dir or settings.BACKTEST_DIR
        ensure_dir(self._root)
        logger.debug("BacktestRepository initialised | root=%s", self._root)

    def run_dir(self, run_id: str) -> Path:
        """Return and ensure directory path for a run_id."""
        d = self._root / run_id
        ensure_dir(d)
        return d

    # ------------------------------------------------------------------
    # save
    # ------------------------------------------------------------------

    def save(
        self,
        run_id: str,
        backtest_report: dict[str, Any],
        model_comparison: dict[str, Any],
        strategy_metrics: dict[str, Any],
        leakage_report: dict[str, Any],
        prediction_results: pd.DataFrame,
        plots: Optional[dict[str, Path]] = None,
        # Task 6.4.1
        portfolio_timeseries: Optional[pd.DataFrame] = None,
        overlap_report: Optional[dict[str, Any]] = None,
        financial_validation: Optional[dict[str, Any]] = None,
        benchmark_metrics: Optional[dict[str, Any]] = None,
    ) -> dict[str, Path]:
        """
        Persist all backtest run artefacts under `data/backtests/<run_id>/`.

        Returns
        -------
        dict[str, Path]
            Mapping of artefact keys to absolute file paths.
        """
        r_dir = self.run_dir(run_id)
        saved_paths: dict[str, Path] = {}

        # 1. backtest_report.json
        p_report = r_dir / self.REPORT_FILE
        with p_report.open("w", encoding="utf-8") as fh:
            json.dump(backtest_report, fh, indent=2, default=str)
        saved_paths["backtest_report"] = p_report

        # 2. model_comparison.json
        p_comp = r_dir / self.MODEL_COMPARISON_FILE
        with p_comp.open("w", encoding="utf-8") as fh:
            json.dump(model_comparison, fh, indent=2, default=str)
        saved_paths["model_comparison"] = p_comp

        # 3. strategy_metrics.json
        p_strat = r_dir / self.STRATEGY_METRICS_FILE
        with p_strat.open("w", encoding="utf-8") as fh:
            json.dump(strategy_metrics, fh, indent=2, default=str)
        saved_paths["strategy_metrics"] = p_strat

        # 4. leakage_report.json
        p_leak = r_dir / self.LEAKAGE_REPORT_FILE
        with p_leak.open("w", encoding="utf-8") as fh:
            json.dump(leakage_report, fh, indent=2, default=str)
        saved_paths["leakage_report"] = p_leak

        # 5. prediction_results.parquet
        p_parquet = r_dir / self.PREDICTION_RESULTS_FILE
        prediction_results.to_parquet(p_parquet, index=False)
        saved_paths["prediction_results"] = p_parquet

        # 6. Copy plots if provided
        if plots:
            for plot_key, src_path in plots.items():
                if src_path and Path(src_path).is_file():
                    dest_name = f"{plot_key}.png" if not plot_key.endswith(".png") else plot_key
                    dest_path = r_dir / dest_name
                    dest_path.write_bytes(Path(src_path).read_bytes())
                    saved_paths[plot_key] = dest_path

        # 7. Task 6.4.1 artifacts
        if portfolio_timeseries is not None and not portfolio_timeseries.empty:
            p_pt = r_dir / self.PORTFOLIO_TIMESERIES_FILE
            portfolio_timeseries.to_parquet(p_pt, index=False)
            saved_paths["portfolio_timeseries"] = p_pt

        if overlap_report is not None:
            p_ov = r_dir / self.OVERLAP_REPORT_FILE
            with p_ov.open("w", encoding="utf-8") as fh:
                import json as _json
                _json.dump(overlap_report, fh, indent=2, default=str)
            saved_paths["overlap_report"] = p_ov

        if financial_validation is not None:
            p_fv = r_dir / self.FINANCIAL_VALIDATION_FILE
            with p_fv.open("w", encoding="utf-8") as fh:
                import json as _json
                _json.dump(financial_validation, fh, indent=2, default=str)
            saved_paths["financial_validation"] = p_fv

        if benchmark_metrics is not None:
            p_bm = r_dir / self.BENCHMARK_METRICS_FILE
            with p_bm.open("w", encoding="utf-8") as fh:
                import json as _json
                _json.dump(benchmark_metrics, fh, indent=2, default=str)
            saved_paths["benchmark_metrics"] = p_bm

        logger.info("Saved backtest run '%s' to %s", run_id, r_dir)
        return saved_paths

    # ------------------------------------------------------------------
    # load
    # ------------------------------------------------------------------

    def load(self, run_id: str) -> dict[str, Any]:
        """
        Load backtest run artefacts for run_id.

        Returns
        -------
        dict containing:
        - "backtest_report": dict
        - "model_comparison": dict
        - "strategy_metrics": dict
        - "leakage_report": dict
        - "prediction_results": pd.DataFrame
        - "plots": dict[str, Path]
        """
        r_dir = self._root / run_id
        if not r_dir.is_dir():
            raise FileNotFoundError(f"Backtest run directory not found: {r_dir}")

        res: dict[str, Any] = {}

        p_report = r_dir / self.REPORT_FILE
        if p_report.is_file():
            with p_report.open("r", encoding="utf-8") as fh:
                res["backtest_report"] = json.load(fh)

        p_comp = r_dir / self.MODEL_COMPARISON_FILE
        if p_comp.is_file():
            with p_comp.open("r", encoding="utf-8") as fh:
                res["model_comparison"] = json.load(fh)

        p_strat = r_dir / self.STRATEGY_METRICS_FILE
        if p_strat.is_file():
            with p_strat.open("r", encoding="utf-8") as fh:
                res["strategy_metrics"] = json.load(fh)

        p_leak = r_dir / self.LEAKAGE_REPORT_FILE
        if p_leak.is_file():
            with p_leak.open("r", encoding="utf-8") as fh:
                res["leakage_report"] = json.load(fh)

        p_parquet = r_dir / self.PREDICTION_RESULTS_FILE
        if p_parquet.is_file():
            res["prediction_results"] = pd.read_parquet(p_parquet)

        # Task 6.4.1 artifacts
        p_pt = r_dir / self.PORTFOLIO_TIMESERIES_FILE
        if p_pt.is_file():
            res["portfolio_timeseries"] = pd.read_parquet(p_pt)

        import json as _json
        for key, fname in [
            ("overlap_report", self.OVERLAP_REPORT_FILE),
            ("financial_validation", self.FINANCIAL_VALIDATION_FILE),
            ("benchmark_metrics", self.BENCHMARK_METRICS_FILE),
        ]:
            p_extra = r_dir / fname
            if p_extra.is_file():
                with p_extra.open("r", encoding="utf-8") as fh:
                    res[key] = _json.load(fh)

        plots: dict[str, Path] = {}
        for p_file in r_dir.glob("*.png"):
            plots[p_file.stem] = p_file
        res["plots"] = plots

        return res

    # ------------------------------------------------------------------
    # exists
    # ------------------------------------------------------------------

    def exists(self, run_id: str) -> bool:
        """Return True if run_id exists and contains backtest_report.json."""
        r_dir = self._root / run_id
        return r_dir.is_dir() and (r_dir / self.REPORT_FILE).is_file()

    # ------------------------------------------------------------------
    # list_runs
    # ------------------------------------------------------------------

    def list_runs(self) -> list[str]:
        """Return a sorted list of all available run_ids."""
        if not self._root.is_dir():
            return []
        runs = []
        for d in self._root.iterdir():
            if d.is_dir() and (d / self.REPORT_FILE).is_file():
                runs.append(d.name)
        return sorted(runs)

    def get_latest_run(self) -> Optional[str]:
        """Return the run_id of the most recently modified run."""
        runs = self.list_runs()
        if not runs:
            return None
        # Sort by directory modification time
        runs_sorted = sorted(
            runs,
            key=lambda r: (self._root / r / self.REPORT_FILE).stat().st_mtime,
            reverse=True,
        )
        return runs_sorted[0]
