"""
backtesting/engine.py
=====================
HistoricalBacktestEngine — master orchestrator for Task 6.4 / 6.4.1.

Objective
---------
Executes walk-forward backtesting across historical bill events without look-ahead bias.

Task 6.4.1 Updates
-------------------
1. NiftyBenchmarkLoader is used to populate per-record NIFTY 50 period returns.
2. PortfolioAccountant builds a chronological portfolio snapshot series (initial_capital=1.0,
   compounded, equal-weighted per event date) replacing the erroneous cumulative sum.
3. OverlapDetector reports simultaneous event windows.
4. FinancialValidator performs 10 post-hoc financial integrity checks.
5. All new artifacts are persisted via BacktestRepository.

Key Principles
--------------
1. Strict Anti-Leakage: Models trained ONLY on pre-event features at or before cutoff.
2. Temporal Walk-Forward: Chronological expanding window — never shuffles.
3. Compounded Returns: portfolio_value = 1.0 × ∏(1 + per_date_return).
4. Simultaneous Events: multiple events on the same date are equal-weighted.
5. TC Only On Trades: transaction costs charged only when |signal| > 0.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import warnings

import numpy as np
import pandas as pd

from config.logging_config import get_logger
from backtesting.financial_validator import FinancialValidator
from backtesting.metrics import ClassificationMetricsCalculator, FinancialMetricsCalculator
from backtesting.nifty_loader import NiftyBenchmarkLoader
from backtesting.overlap_detector import OverlapDetector
from backtesting.report_generator import BacktestReportGenerator
from backtesting.strategy import PortfolioAccountant, SignalRule, StrategyEvaluator, TransactionCostModel
from backtesting.visualizer import BacktestVisualizer
from models.training.dataset_builder import DatasetBuilder, _TARGET_COLS
from models.training.trainer import MLTrainer, TARGET_COLUMN_MAP
from schemas.backtest_record import BacktestRecord, BacktestRunDescriptor, StrategyMetrics
from storage.backtest_repository import BacktestRepository
from storage.evaluation_repository import EvaluationRepository
from validation.backtest_validator import BacktestValidator

logger = get_logger(__name__)


class HistoricalBacktestEngine:
    """
    Historical Backtesting Engine for Legislative Market Impact System.

    Parameters
    ----------
    dataset_builder : DatasetBuilder, optional
    eval_repo : EvaluationRepository, optional
    backtest_repo : BacktestRepository, optional
    cost_model : TransactionCostModel, optional
    signal_rule : SignalRule, optional
    mode : str, optional
        Feature-selection mode (default: "structured").
    """

    def __init__(
        self,
        dataset_builder: Optional[DatasetBuilder] = None,
        eval_repo: Optional[EvaluationRepository] = None,
        backtest_repo: Optional[BacktestRepository] = None,
        cost_model: Optional[TransactionCostModel] = None,
        signal_rule: Optional[SignalRule] = None,
        mode: str = "structured",
    ) -> None:
        from config.settings import settings

        self._builder = dataset_builder or DatasetBuilder()
        self._eval_repo = eval_repo or EvaluationRepository()
        self._backtest_repo = backtest_repo or BacktestRepository()
        self._cost_model = cost_model or TransactionCostModel(
            transaction_cost=settings.DEFAULT_TRANSACTION_COST,
            brokerage=settings.DEFAULT_BROKERAGE,
            slippage=settings.DEFAULT_SLIPPAGE,
        )
        self._signal_rule = signal_rule or SignalRule()
        self._mode = mode

        self._validator = BacktestValidator()
        self._evaluator = StrategyEvaluator(
            cost_model=self._cost_model,
            signal_rule=self._signal_rule,
        )
        self._portfolio_accountant = PortfolioAccountant(
            initial_capital=1.0,
            cost_model=self._cost_model,
        )
        self._class_calc = ClassificationMetricsCalculator()
        self._fin_calc = FinancialMetricsCalculator()
        self._nifty_loader = NiftyBenchmarkLoader()
        self._overlap_detector = OverlapDetector()
        self._financial_validator = FinancialValidator()
        self._visualizer = BacktestVisualizer()
        self._report_gen = BacktestReportGenerator()

        logger.debug("HistoricalBacktestEngine initialised | mode=%s", self._mode)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_best_model_for_target(self, target: str) -> str:
        """
        Query EvaluationRepository comparison_report.json to select the best model by Macro F1.
        Defaults to 'lgbm' if unavailable.
        """
        try:
            if self._eval_repo.exists():
                report = self._eval_repo.load_comparison_report()
                if target in report and "best_model" in report[target]:
                    best_m = report[target]["best_model"].get("model_type")
                    if best_m:
                        logger.info("Selected best model for '%s': %s", target, best_m)
                        return str(best_m)
        except Exception as exc:
            logger.warning("Could not read EvaluationRepository: %s. Using 'lgbm'.", exc)
        return "lgbm"

    def run_backtest(
        self,
        target: str = "direction",
        model_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        anticipation_window_days: int = 0,
        transaction_cost: Optional[float] = None,
        slippage: Optional[float] = None,
        rebuild_datasets: bool = False,
        run_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Execute walk-forward historical backtest for a target variable.

        Parameters
        ----------
        target : str
        model_name : str, optional
        start_date : str, optional (ISO e.g. "2020-01-01")
        end_date : str, optional
        anticipation_window_days : int, optional
        transaction_cost : float, optional
        slippage : float, optional
        rebuild_datasets : bool, optional
        run_id : str, optional

        Returns
        -------
        dict with keys: run_id, paths, report, metrics, strategy.
        """
        target_col = TARGET_COLUMN_MAP.get(target, target)
        selected_model = model_name or self.select_best_model_for_target(target)

        cost_m = self._cost_model
        if transaction_cost is not None or slippage is not None:
            cost_m = TransactionCostModel(
                transaction_cost=transaction_cost if transaction_cost is not None else self._cost_model.transaction_cost,
                brokerage=self._cost_model.brokerage,
                slippage=slippage if slippage is not None else self._cost_model.slippage,
            )

        logger.info(
            "=== Starting Historical Backtest (6.4.1) | target=%s | model=%s | cost_bps=%.1f ===",
            target, selected_model, cost_m.transaction_cost * 10000.0,
        )

        # 1. Load ML datasets
        df_train_full, df_research_full, train_desc, _ = self._builder.build(
            mode=self._mode, rebuild=rebuild_datasets
        )

        feature_cols = self._builder.get_feature_columns(df_train_full)
        if not feature_cols:
            raise ValueError("No feature columns available for backtesting.")

        df_train_full = self._ensure_sorted(df_train_full)
        df_research_full = self._ensure_sorted(df_research_full)

        df_train_filtered, df_research_filtered = self._filter_date_range(
            df_train_full, df_research_full, start_date, end_date
        )

        if df_train_filtered.empty:
            raise ValueError("No records match the specified date range.")

        # 2. Walk-forward predictions
        records = self._execute_walk_forward(
            df_train=df_train_filtered,
            df_research=df_research_filtered,
            feature_cols=feature_cols,
            target=target,
            target_col=target_col,
            model_name=selected_model,
            anticipation_window_days=anticipation_window_days,
            cost_model=cost_m,
        )

        # 3. Evaluate records (signals, strategy_return)
        evaluator = StrategyEvaluator(cost_model=cost_m, signal_rule=self._signal_rule)
        records = evaluator.evaluate_records(records)

        # 4. NIFTY 50 period returns
        nifty_per_record = self._compute_nifty_returns(records)
        for i, rec in enumerate(records):
            rec.nifty_period_return = nifty_per_record[i]

        # Build per-date NIFTY map for PortfolioAccountant
        nifty_map: dict[str, float] = {}
        for rec in records:
            dt = rec.prediction_timestamp
            nifty_val = rec.nifty_period_return
            if nifty_val is not None and not np.isnan(nifty_val):
                # For multiple records on same date, take mean of NIFTY returns (same index)
                if dt not in nifty_map:
                    nifty_map[dt] = nifty_val
                # (All records on same date share same NIFTY value — it is index-level)

        # 5. Portfolio accounting (Task 6.4.1)
        accountant = PortfolioAccountant(initial_capital=1.0, cost_model=cost_m)
        snapshots = accountant.build_snapshots(records, nifty_returns=nifty_map)

        # 6. Classification metrics
        y_true = [r.actual_class for r in records]
        y_pred = [r.predicted_class for r in records]
        y_prob = [r.prediction_probability for r in records]
        class_metrics = self._class_calc.compute_metrics(y_true, y_pred, y_prob)

        # 7. Financial metrics (from snapshots)
        fin_metrics = self._fin_calc.compute_metrics(records, snapshots)

        # 8. Benchmark comparison
        benchmark_comp = evaluator.compute_benchmark_comparison(
            records, snapshots, nifty_loader=self._nifty_loader
        )

        strategy_metrics = StrategyMetrics(
            target=target,
            model_name=selected_model,
            financial_metrics=fin_metrics,
            benchmark_comparison=benchmark_comp,
            transaction_cost_bps=cost_m.transaction_cost * 10000.0,
            slippage_bps=cost_m.slippage * 10000.0,
            brokerage_bps=cost_m.brokerage * 10000.0,
        )

        # 9. Anti-Leakage Validation
        _, leakage_report = self._validator.validate_backtest_execution(
            records=records,
            feature_columns_used=feature_cols,
        )

        # 10. Overlap detection (Task 6.4.1)
        overlap_report = self._overlap_detector.detect(records)

        # 11. Financial Validation (Task 6.4.1)
        financial_validation = self._financial_validator.validate(
            records=records,
            snapshots=snapshots,
            max_drawdown=fin_metrics.max_drawdown,
        )

        # 12. Model comparison
        all_model_metrics = self._evaluate_all_models_for_target(
            df_train=df_train_filtered,
            df_research=df_research_filtered,
            feature_cols=feature_cols,
            target=target,
            target_col=target_col,
            cost_model=cost_m,
        )
        model_comp_report = self._report_gen.build_model_comparison(all_model_metrics)

        # 13. Build Run ID
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        final_run_id = run_id or f"backtest_{target}_{selected_model}_{timestamp_str}"

        unique_bills = len(set(r.bill_id for r in records))
        unique_comps = len(set(r.company_isin for r in records))

        descriptor = BacktestRunDescriptor(
            run_id=final_run_id,
            run_timestamp=datetime.now(timezone.utc).isoformat(),
            target=target,
            model_name=selected_model,
            start_date=start_date,
            end_date=end_date,
            total_predictions=len(records),
            unique_bills=unique_bills,
            unique_companies=unique_comps,
            anticipation_window=f"[-{anticipation_window_days}, -1] days" if anticipation_window_days > 0 else "None (Official introduction date)",
            transaction_cost=cost_m.transaction_cost,
            brokerage=cost_m.brokerage,
            slippage=cost_m.slippage,
            macro_f1=class_metrics.macro_f1,
            accuracy=class_metrics.accuracy,
            cumulative_strategy_return=fin_metrics.cumulative_return,
            sharpe_ratio=fin_metrics.sharpe_ratio,
            max_drawdown=fin_metrics.max_drawdown,
        )

        # 14. Assemble Reports
        main_report = self._report_gen.build_backtest_report(
            descriptor, class_metrics, strategy_metrics, leakage_report,
            overlap_report=overlap_report,
            financial_validation=financial_validation,
        )
        strat_report = self._report_gen.build_strategy_metrics_report(strategy_metrics)
        pred_df = self._report_gen.build_prediction_results_df(records)
        portfolio_ts_df = self._report_gen.build_portfolio_timeseries_df(snapshots)
        overlap_dict = self._report_gen.build_overlap_report(overlap_report)
        validation_dict = self._report_gen.build_financial_validation_report(financial_validation)
        benchmark_dict = self._report_gen.build_benchmark_metrics_report(strategy_metrics)

        # 15. Generate Plots (Task 6.4.1 — uses snapshots)
        run_dir = self._backtest_repo.run_dir(final_run_id)
        plot_paths = self._visualizer.generate_all_plots(
            output_dir=run_dir,
            records=records,
            snapshots=snapshots,
            model_comparison_data=model_comp_report,
        )

        # 16. Persist
        saved_paths = self._backtest_repo.save(
            run_id=final_run_id,
            backtest_report=main_report,
            model_comparison=model_comp_report,
            strategy_metrics=strat_report,
            leakage_report=leakage_report.to_dict(),
            prediction_results=pred_df,
            plots=plot_paths,
            portfolio_timeseries=portfolio_ts_df,
            overlap_report=overlap_dict,
            financial_validation=validation_dict,
            benchmark_metrics=benchmark_dict,
        )

        logger.info(
            "=== Backtest 6.4.1 Complete: run_id=%s | F1=%.4f | CumReturn=%.4f%% | Sharpe=%.4f | MaxDD=%.4f%% | Trades=%d ===",
            final_run_id,
            class_metrics.macro_f1,
            fin_metrics.cumulative_return * 100,
            fin_metrics.sharpe_ratio,
            fin_metrics.max_drawdown * 100,
            fin_metrics.actual_trades,
        )

        return {
            "run_id": final_run_id,
            "paths": saved_paths,
            "report": main_report,
            "metrics": class_metrics,
            "strategy": strategy_metrics,
            "snapshots": snapshots,
            "overlap_report": overlap_report,
            "financial_validation": financial_validation,
        }

    # ------------------------------------------------------------------
    # Core Walk-Forward Loop
    # ------------------------------------------------------------------

    def _execute_walk_forward(
        self,
        df_train: pd.DataFrame,
        df_research: pd.DataFrame,
        feature_cols: list[str],
        target: str,
        target_col: str,
        model_name: str,
        anticipation_window_days: int,
        cost_model: TransactionCostModel,
    ) -> list[BacktestRecord]:
        """Run chronological expanding-window walk-forward predictions."""
        valid_mask = df_train[target_col].notnull()
        df_tr = df_train[valid_mask].reset_index(drop=True)
        df_rs = df_research[valid_mask].reset_index(drop=True)

        if df_tr.empty:
            return []

        research_map: dict[str, dict[str, Any]] = {}
        for _, row in df_rs.iterrows():
            rec_id = str(row.get(
                "record_id",
                f"{row.get('bill_id')}_{row.get('company_isin')}_{row.get('event_window')}"
            ))
            research_map[rec_id] = row.to_dict()

        if "introduction_date" in df_tr.columns:
            dates = pd.to_datetime(df_tr["introduction_date"], errors="coerce")
            unique_dates = sorted(dates.dropna().unique())
        else:
            unique_dates = []

        min_initial_train = max(10, int(len(df_tr) * 0.2))
        trainer = MLTrainer(n_splits=3, verbose=False)
        records: list[BacktestRecord] = []

        if len(unique_dates) >= 5:
            initial_cutoff_idx = max(2, int(len(unique_dates) * 0.25))

            for d_idx in range(initial_cutoff_idx, len(unique_dates)):
                eval_date = unique_dates[d_idx]
                eval_date_str = str(pd.to_datetime(eval_date).strftime("%Y-%m-%d"))

                train_mask = pd.to_datetime(df_tr["introduction_date"]) < eval_date
                test_mask = pd.to_datetime(df_tr["introduction_date"]) == eval_date

                df_sub_train = df_tr[train_mask].reset_index(drop=True)
                df_sub_test = df_tr[test_mask].reset_index(drop=True)

                if df_sub_train.empty or df_sub_test.empty:
                    continue

                train_cutoff_date = str(
                    pd.to_datetime(df_sub_train["introduction_date"]).max().strftime("%Y-%m-%d")
                )

                sub_records = self._predict_test_batch(
                    df_sub_train=df_sub_train,
                    df_sub_test=df_sub_test,
                    feature_cols=feature_cols,
                    target=target,
                    target_col=target_col,
                    model_name=model_name,
                    eval_date_str=eval_date_str,
                    train_cutoff_date=train_cutoff_date,
                    anticipation_window_days=anticipation_window_days,
                    research_map=research_map,
                    trainer=trainer,
                )
                records.extend(sub_records)
        else:
            for idx in range(min_initial_train, len(df_tr)):
                df_sub_train = df_tr.iloc[:idx].reset_index(drop=True)
                df_sub_test = df_tr.iloc[idx: idx + 1].reset_index(drop=True)

                eval_date_str = str(df_sub_test.iloc[0].get("introduction_date", "2023-01-01"))
                train_cutoff_date = str(df_sub_train.iloc[-1].get("introduction_date", "2022-12-31"))

                sub_records = self._predict_test_batch(
                    df_sub_train=df_sub_train,
                    df_sub_test=df_sub_test,
                    feature_cols=feature_cols,
                    target=target,
                    target_col=target_col,
                    model_name=model_name,
                    eval_date_str=eval_date_str,
                    train_cutoff_date=train_cutoff_date,
                    anticipation_window_days=anticipation_window_days,
                    research_map=research_map,
                    trainer=trainer,
                )
                records.extend(sub_records)

        logger.info("Walk-forward produced %d observation records.", len(records))
        return records

    def _predict_test_batch(
        self,
        df_sub_train: pd.DataFrame,
        df_sub_test: pd.DataFrame,
        feature_cols: list[str],
        target: str,
        target_col: str,
        model_name: str,
        eval_date_str: str,
        train_cutoff_date: str,
        anticipation_window_days: int,
        research_map: dict[str, dict[str, Any]],
        trainer: MLTrainer,
    ) -> list[BacktestRecord]:
        """Fit preprocessor + estimator on df_sub_train and predict on df_sub_test."""
        X_train_raw, y_train_raw, _ = trainer._extract_Xy(df_sub_train, feature_cols, target_col)
        X_test_raw, y_test_raw, _ = trainer._extract_Xy(df_sub_test, feature_cols, target_col)

        if X_train_raw.empty or X_test_raw.empty:
            return []

        from sklearn.preprocessing import LabelEncoder
        preprocessor = trainer._build_preprocessor(X_train_raw)
        X_train_proc = preprocessor.fit_transform(X_train_raw)
        X_test_proc = preprocessor.transform(X_test_raw)

        label_encoder = LabelEncoder()
        y_train_enc = label_encoder.fit_transform(y_train_raw.astype(str))

        estimator = trainer._make_base_estimator(model_name)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            estimator.fit(X_train_proc, y_train_enc)

        y_test_pred_enc = estimator.predict(X_test_proc)
        y_test_pred = label_encoder.inverse_transform(y_test_pred_enc)

        prob_matrix = None
        if hasattr(estimator, "predict_proba"):
            try:
                prob_matrix = estimator.predict_proba(X_test_proc)
            except Exception:
                prob_matrix = None

        batch_records: list[BacktestRecord] = []

        for i, (_, row) in enumerate(df_sub_test.iterrows()):
            rec_id = str(row.get(
                "record_id",
                f"{row.get('bill_id')}_{row.get('company_isin')}_{row.get('event_window')}"
            ))
            res_row = research_map.get(rec_id, {})

            pred_cls = str(y_test_pred[i])
            act_cls = str(row[target_col])

            prob_dict: dict[str, float] = {}
            if prob_matrix is not None and i < len(prob_matrix):
                for cls_idx, cls_label in enumerate(label_encoder.classes_):
                    prob_dict[str(cls_label)] = float(prob_matrix[i, cls_idx])

            final_car = res_row.get("final_car")
            if final_car is not None:
                try:
                    final_car = float(final_car)
                except (ValueError, TypeError):
                    final_car = None

            act_dir = res_row.get("direction", act_cls if target == "direction" else None)

            pred_ts = eval_date_str
            if anticipation_window_days > 0:
                dt_val = pd.to_datetime(eval_date_str) - pd.Timedelta(days=anticipation_window_days)
                pred_ts = dt_val.strftime("%Y-%m-%d")

            b_rec = BacktestRecord(
                bill_id=str(row["bill_id"]),
                company_isin=str(row["company_isin"]),
                event_window=str(row.get("event_window", "[0,+20]")),
                prediction_timestamp=pred_ts,
                model_name=model_name,
                target=target,
                predicted_class=pred_cls,
                actual_class=act_cls,
                prediction_probability=prob_dict,
                model_version="v1.0.0",
                feature_version="v1.0.0",
                training_cutoff_date=train_cutoff_date,
                data_cutoff_date=eval_date_str,
                predicted_direction=None,
                actual_direction=str(act_dir) if act_dir else None,
                abnormal_return=final_car,
                cumulative_abnormal_return=final_car,
                signal=None,
                nifty_period_return=None,
            )
            batch_records.append(b_rec)

        return batch_records

    # ------------------------------------------------------------------
    # NIFTY 50 Integration
    # ------------------------------------------------------------------

    def _compute_nifty_returns(self, records: list[BacktestRecord]) -> list[float]:
        """Compute NIFTY 50 period return for every record using its event window."""
        if not records:
            return []

        event_dates = [r.prediction_timestamp for r in records]
        event_windows = [r.event_window for r in records]

        nifty_returns = self._nifty_loader.get_period_returns_batch(event_dates, event_windows)
        return nifty_returns

    # ------------------------------------------------------------------
    # Model Comparison Helper
    # ------------------------------------------------------------------

    def _evaluate_all_models_for_target(
        self,
        df_train: pd.DataFrame,
        df_research: pd.DataFrame,
        feature_cols: list[str],
        target: str,
        target_col: str,
        cost_model: TransactionCostModel,
    ) -> dict[str, Any]:
        """Run backtest walk-forward for all model types for comparison."""
        from schemas.backtest_record import ClassificationMetrics as CM
        comparison_results: dict[str, CM] = {}

        for m_name in ["lgbm", "xgboost", "random_forest"]:
            try:
                recs = self._execute_walk_forward(
                    df_train=df_train,
                    df_research=df_research,
                    feature_cols=feature_cols,
                    target=target,
                    target_col=target_col,
                    model_name=m_name,
                    anticipation_window_days=0,
                    cost_model=cost_model,
                )
                eval_tmp = StrategyEvaluator(cost_model=cost_model, signal_rule=self._signal_rule)
                recs = eval_tmp.evaluate_records(recs)

                y_true = [r.actual_class for r in recs]
                y_pred = [r.predicted_class for r in recs]
                y_prob = [r.prediction_probability for r in recs]

                metrics = self._class_calc.compute_metrics(y_true, y_pred, y_prob)
                comparison_results[m_name] = metrics
            except Exception as exc:
                logger.warning("Comparison backtest failed for '%s': %s", m_name, exc)

        return comparison_results

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ensure_sorted(df: pd.DataFrame) -> pd.DataFrame:
        if "introduction_date" not in df.columns:
            return df
        df = df.copy()
        df["introduction_date"] = pd.to_datetime(df["introduction_date"], errors="coerce")
        return df.sort_values("introduction_date", ascending=True, na_position="last").reset_index(drop=True)

    @staticmethod
    def _filter_date_range(
        df_train: pd.DataFrame,
        df_research: pd.DataFrame,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        if "introduction_date" not in df_train.columns:
            return df_train, df_research

        dates = pd.to_datetime(df_train["introduction_date"], errors="coerce")
        mask = pd.Series(True, index=df_train.index)

        if start_date:
            mask = mask & (dates >= pd.to_datetime(start_date))
        if end_date:
            mask = mask & (dates <= pd.to_datetime(end_date))

        return df_train[mask].reset_index(drop=True), df_research[mask].reset_index(drop=True)
