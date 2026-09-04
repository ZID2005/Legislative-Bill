"""
main.py
=======
CLI entry point for the Legislative Intelligence & Market Impact Prediction System.

This script serves as the top-level orchestrator.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap: ensure project root is on sys.path when run directly
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import get_logger, settings  # noqa: E402
from services import IngestionService  # noqa: E402

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
__version__ = "0.1.0"


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------


def cmd_status(args: argparse.Namespace) -> int:  # noqa: ARG001
    """
    Verify project setup and print system information.

    Returns
    -------
    int
        Exit code (0 = success).
    """
    logger.info("=== Legislative Intelligence System — Status Check ===")
    logger.info("Version     : %s", __version__)
    logger.info("Environment : %s", settings.ENV)
    logger.info("Project root: %s", settings.PROJECT_ROOT)
    logger.info("Data dir    : %s", settings.DATA_DIR)
    logger.info("Logs dir    : %s", settings.LOGS_DIR)
    logger.info("Log level   : %s", settings.LOG_LEVEL)
    logger.info("Debug mode  : %s", settings.DEBUG)

    # Ensure required directories exist
    logger.info("Ensuring data directories exist...")
    settings.ensure_directories()
    logger.info("All directories OK.")

    logger.info("=== Status check complete ===")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    """
    Trigger the legislative ingestion service.
    """
    logger.info("Initializing IngestionService...")
    service = IngestionService()
    try:
        stats = asyncio.run(
            service.ingest_bills(
                source=args.source,
                year=args.year,
                latest_only=getattr(args, "latest", False),
                dry_run=getattr(args, "dry_run", False),
                bill_id_filter=getattr(args, "bill_id", None),
            )
        )
        print("\n=== Ingestion Stats ===")
        for k, v in stats.items():
            print(f"  {k:<12}: {v}")
        print("=======================\n")
        return 0
    except Exception as e:
        logger.error("Ingestion command failed: %s", e, exc_info=True)
        return 1


def cmd_download_docs(args: argparse.Namespace) -> int:
    """
    Trigger the document downloader to download PDFs.
    """
    logger.info("Initializing IngestionService for document downloading...")
    service = IngestionService()
    try:
        stats = asyncio.run(
            service.download_bill_documents(
                year=args.year,
                dry_run=args.dry_run,
                bill_id_filter=args.bill_id,
            )
        )
        print("\n=== Document Download Stats ===")
        for k, v in stats.items():
            print(f"  {k:<12}: {v}")
        print("================================\n")
        return 0
    except Exception as e:
        logger.error("Download documents command failed: %s", e, exc_info=True)
        return 1


def cmd_extract_text(args: argparse.Namespace) -> int:
    """
    Trigger text extraction and corpus generation for downloaded bill PDFs.
    """
    logger.info("Initializing IngestionService for text extraction...")
    service = IngestionService()
    try:
        stats = asyncio.run(
            service.extract_bill_text(
                year=args.year,
                dry_run=args.dry_run,
                bill_id_filter=args.bill_id,
            )
        )
        print("\n=== Text Extraction Stats ===")
        for k, v in stats.items():
            print(f"  {k:<12}: {v}")
        print("============================\n")
        return 0
    except Exception as e:
        logger.error("Extract text command failed: %s", e, exc_info=True)
        return 1


def cmd_build_knowledge(args: argparse.Namespace) -> int:
    """
    Trigger knowledge generation and validation for bills.
    """
    logger.info("Initializing KnowledgeService for knowledge generation...")
    from services.knowledge_service import KnowledgeService

    service = KnowledgeService()
    try:
        stats = service.generate_knowledge(
            year=args.year,
            bill_id_filter=args.bill_id,
            dry_run=args.dry_run,
        )
        print("\n=== Knowledge Generation Stats ===")
        for k, v in stats.items():
            print(f"  {k:<20}: {v}")
        print("==================================\n")
        return 0
    except Exception as e:
        logger.error("Build knowledge command failed: %s", e, exc_info=True)
        return 1


def cmd_build_mappings(args: argparse.Namespace) -> int:
    """
    Trigger Bill-to-Company mapping generation.
    """
    logger.info("Initializing MappingService for mapping generation...")
    from services.mapping_service import MappingService

    service = MappingService()
    try:
        stats = service.generate_mappings(
            year=args.year,
            bill_id_filter=args.bill_id,
            dry_run=args.dry_run,
        )
        print("\n=== Mapping Generation Stats ===")
        for k, v in stats.items():
            print(f"  {k:<20}: {v}")
        print("================================\n")
        return 0
    except Exception as e:
        logger.error("Build mappings command failed: %s", e, exc_info=True)
        return 1


def cmd_ingest_companies(args: argparse.Namespace) -> int:
    """
    Trigger company master ingestion.
    """
    logger.info("Initializing IngestionService for company master ingestion...")
    service = IngestionService()
    try:
        stats = asyncio.run(service.ingest_companies(dry_run=args.dry_run))
        print("\n=== Company Ingestion Stats ===")
        for k, v in stats.items():
            print(f"  {k:<20}: {v}")
        print("===============================\n")
        return 0
    except Exception as e:
        logger.error("Company ingestion command failed: %s", e, exc_info=True)
        return 1


def cmd_ingest_market(args: argparse.Namespace) -> int:
    """
    Trigger historical market data ingestion.
    """
    import datetime  # noqa: PLC0415

    logger.info("Initializing MarketLoader for market data ingestion...")
    from ingestion.market.market_loader import MarketLoader  # noqa: PLC0415

    loader = MarketLoader()
    try:
        if args.start_date:
            start_date = args.start_date
        else:
            three_years_ago = datetime.date.today() - datetime.timedelta(days=3 * 365)
            start_date = three_years_ago.strftime("%Y-%m-%d")

        end_date = args.end_date

        stats = loader.sync_all(
            start_date=start_date,
            end_date=end_date,
            symbol_filter=args.symbol,
            index_only=args.index,
            force_refresh=args.force_refresh,
        )

        print("\n=== Market Ingestion Stats ===")
        for k, v in stats.items():
            if k == "errors":
                if v:
                    print(f"  {k:<20}: {len(v)} errors")
                    for sym, err in list(v.items())[:5]:
                        print(f"    - {sym}: {err}")
            else:
                print(f"  {k:<20}: {v}")
        print("==============================\n")
        return 0
    except Exception as e:
        logger.error("Market ingestion command failed: %s", e, exc_info=True)
        return 1


def cmd_estimate_market_models(args: argparse.Namespace) -> int:
    """
    Trigger Market Model parameter estimation.
    """
    logger.info("Initializing MarketModelService for expected returns estimation...")
    from services.market_model_service import MarketModelService

    service = MarketModelService()
    try:
        stats = service.run_estimation(
            year=args.year,
            bill_id_filter=args.bill_id,
            benchmark_symbol=args.benchmark,
            force_refresh=args.force_refresh,
        )
        print("\n=== Market Model Estimation Stats ===")
        for k, v in stats.items():
            if k == "errors":
                if v:
                    print(f"  {k:<20}: {len(v)} errors")
                    for key, errs in list(v.items())[:5]:
                        print(f"    - {key}: {errs}")
            else:
                print(f"  {k:<20}: {v}")
        print("=====================================\n")
        return 0
    except Exception as e:
        logger.error("Market model estimation failed: %s", e, exc_info=True)
        return 1


def cmd_run_event_study(args: argparse.Namespace) -> int:
    """
    Trigger Event Study calculations.
    """
    logger.info("Initializing EventStudyService for event study calculations...")
    from services.event_study_service import EventStudyService

    service = EventStudyService()
    try:
        stats = service.run_all_studies(
            year=args.year,
            bill_id_filter=args.bill_id,
            company_isin_filter=args.company_isin,
            window_filter=args.window,
            force_refresh=args.force_refresh,
        )
        print("\n=== Event Study Estimation Stats ===")
        for k, v in stats.items():
            if k == "errors":
                if v:
                    print(f"  {k:<20}: {len(v)} errors")
                    for key, errs in list(v.items())[:5]:
                        print(f"    - {key}: {errs}")
            else:
                print(f"  {k:<20}: {v}")
        print("====================================\n")
        return 0
    except Exception as e:
        logger.error("Event study calculations failed: %s", e, exc_info=True)
        return 1


def cmd_run_statistical_significance(args: argparse.Namespace) -> int:
    """
    Trigger statistical significance calculations for event studies.
    """
    logger.info("Initializing StatisticalSignificanceService for significance calculations...")
    from services.statistical_service import StatisticalSignificanceService

    service = StatisticalSignificanceService()
    try:
        stats = service.run_calculations(
            year=args.year,
            bill_id_filter=args.bill_id,
            company_isin_filter=args.company_isin,
            window_filter=args.window,
            force_refresh=args.force_refresh,
        )
        print("\n=== Statistical Significance Stats ===")
        for k, v in stats.items():
            if k == "errors":
                if v:
                    print(f"  {k:<20}: {len(v)} errors")
                    for key, errs in list(v.items())[:5]:
                        print(f"    - {key}: {errs}")
            else:
                print(f"  {k:<20}: {v}")
        print("=======================================\n")
        return 0
    except Exception as e:
        logger.error("Statistical significance calculations failed: %s", e, exc_info=True)
        return 1


def cmd_validate(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Placeholder: will trigger data validation (Task 3)."""
    logger.warning("Validation pipeline not yet implemented.  See Task 3.")
    return 1


def cmd_generate_labels(args: argparse.Namespace) -> int:
    """
    Generate ground-truth ML labels from statistical significance results (Task 4.4).
    """
    logger.info("Initializing LabelGenerationService...")
    from services.label_service import LabelGenerationService

    service = LabelGenerationService()
    try:
        summary = service.run(
            year=getattr(args, "year", None),
            bill_id=getattr(args, "bill_id", None),
            event_window=getattr(args, "window", None),
            force_refresh=getattr(args, "force_refresh", False),
        )
        print("\n=== Label Generation Summary ===")
        print(f"  {'processed':<20}: {summary['processed']}")
        print(f"  {'generated':<20}: {summary['generated']}")
        print(f"  {'skipped':<20}: {summary['skipped']}")
        print(f"  {'rejected':<20}: {summary['rejected']}")
        if summary["rejections"]:
            print("\n  Rejected records:")
            for report in summary["rejections"][:10]:  # Show first 10
                print(
                    f"    - bill={report.bill_id} company={report.company} "
                    f"window={report.event_window}: {report.rejection_reason}"
                )
        print("================================\n")
        return 0
    except Exception as exc:
        logger.error("Label generation failed: %s", exc, exc_info=True)
        return 1


def cmd_train(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Placeholder: will trigger model training (Task 8)."""
    logger.warning("Training pipeline not yet implemented.  See Task 8.")
    return 1


def cmd_predict(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Placeholder: will serve predictions for a new bill (Task 9)."""
    logger.warning("Prediction pipeline not yet implemented.  See Task 9.")
    return 1


def cmd_serve(args: argparse.Namespace) -> int:
    """Launch the interactive Decision-Support Dashboard — Task 7.4."""
    from dashboard.dashboard import run_dashboard

    port = getattr(args, "port", 8501)
    host = getattr(args, "host", "localhost")
    logger.info("Serving interactive dashboard on http://%s:%d", host, port)
    return run_dashboard(port=port, host=host)


def cmd_build_features(args: argparse.Namespace) -> int:
    """
    Build (or incrementally update) the unified ML feature dataset — Task 5.1.

    Merges all upstream repositories (Bill, Knowledge, Company, Market Model,
    Event Study, Statistical, Label) into a single Parquet file stored under
    ``data/features/``.
    """
    logger.info("Initializing FeatureBuilder...")
    from features.feature_builder import FeatureBuilder

    builder = FeatureBuilder()
    incremental = not getattr(args, "rebuild", False)
    export_csv = getattr(args, "export_csv", False)

    try:
        if incremental:
            logger.info("Running incremental feature build (skipping existing records).")
        else:
            logger.info("Running FULL feature rebuild (all records will be reprocessed).")

        result = builder.build(incremental=incremental)

        print("\n=== Feature Engineering Summary ===")
        print(f"  {'records_written':<24}: {result.records_written}")
        print(f"  {'records_skipped':<24}: {result.records_skipped}")
        print(f"  {'records_rejected':<24}: {result.records_rejected}")
        print(f"  {'total_in_dataset':<24}: {result.total_in_dataset}")
        print(f"  {'duration_seconds':<24}: {result.build_duration_seconds:.2f}s")

        if result.validation_reports:
            errors = [r for r in result.validation_reports if r.severity == "ERROR"]
            warnings = [r for r in result.validation_reports if r.severity == "WARNING"]
            print(f"\n  Validation: {len(errors)} error(s), {len(warnings)} warning(s)")
            for report in errors[:5]:
                print(f"    [ERROR] {report.record_id}: {report.failed_checks}")

        info = builder.dataset_info()
        print(f"\n  Dataset path : {info['parquet_path']}")
        print(f"  Parquet size : {info.get('parquet_size_bytes', 'N/A')} bytes")

        if export_csv:
            csv_path = builder.export_csv()
            print(f"  CSV export   : {csv_path}")

        print("====================================\n")
        return 0

    except Exception as exc:
        logger.error("Feature build failed: %s", exc, exc_info=True)
        return 1


def cmd_generate_embeddings(args: argparse.Namespace) -> int:
    """
    Generate NLP text embeddings for bills — Task 5.2.
    """
    logger.info("Initializing EmbeddingEngine...")
    from models.embeddings.embedding_engine import EmbeddingEngine
    from storage.bill_repository import BillRepository
    import pandas as pd

    model_name = getattr(args, "model", "finbert")
    pooling_strategy = getattr(args, "pooling", "mean")
    force_refresh = getattr(args, "force_refresh", False)
    batch_size = getattr(args, "batch_size", 16)

    try:
        engine = EmbeddingEngine(model_name=model_name, pooling_strategy=pooling_strategy)

        # Primary input: master_feature_dataset.parquet
        from config.settings import settings
        parquet_path = settings.FEATURES_DIR / f"{settings.FEATURE_DATASET_NAME}.parquet"
        if not parquet_path.is_file():
            logger.error("Primary input dataset '%s' does not exist. Run 'build-features' first.", parquet_path)
            return 1

        df_features = pd.read_parquet(parquet_path)
        if df_features.empty or "bill_id" not in df_features.columns:
            logger.warning("No bills found in master feature dataset.")
            print("\n=== Embedding Generation Summary ===")
            print("  No bills found in feature dataset.")
            print("====================================\n")
            return 0

        # Unique bill IDs from the dataset
        bill_ids = sorted(df_features["bill_id"].unique())
        logger.info("Found %d unique bill IDs in the feature dataset.", len(bill_ids))

        # Retrieve Bill objects from BillRepository
        bill_repo = BillRepository()
        bills = []
        for bid in bill_ids:
            bill = bill_repo.get(bid)
            if bill:
                bills.append(bill)
            else:
                logger.warning("Bill '%s' referenced in features dataset but not found in BillRepository.", bid)

        if not bills:
            logger.warning("No matching bills found in BillRepository.")
            print("\n=== Embedding Generation Summary ===")
            print("  No matching bills found in BillRepository.")
            print("====================================\n")
            return 0

        # Run embedding engine
        records, reports = engine.process_batch(
            bills=bills,
            force_refresh=force_refresh,
            batch_size=batch_size,
        )

        print("\n=== Embedding Generation Summary ===")
        print(f"  {'model':<20}: {model_name} ({engine._hf_model_id})")
        print(f"  {'pooling':<20}: {pooling_strategy}")
        print(f"  {'total_bills':<20}: {len(bills)}")
        print(f"  {'generated':<20}: {len(records)}")
        print(f"  {'rejected':<20}: {len(reports)}")

        if reports:
            print("\n  Rejection reports:")
            for r in reports[:10]:
                print(f"    - bill={r.bill_id}: {r.rejection_reason}")
            if len(reports) > 10:
                print(f"    ... and {len(reports) - 10} more rejections.")

        print("====================================\n")
        return 0
    except Exception as exc:
        logger.error("Embedding generation failed: %s", exc, exc_info=True)
        return 1


def cmd_build_fusion(args: argparse.Namespace) -> int:
    """
    Build fused datasets combining structured features and embeddings (Task 5.3).
    """
    logger.info("Initializing FeatureFusionEngine...")
    from features.fusion_engine import FeatureFusionEngine

    if not args.mode and not args.all:
        logger.error("Please specify either --mode <mode> or --all.")
        print("\n[ERROR] Please specify either --mode <mode> or --all.\n")
        return 1

    engine = FeatureFusionEngine()
    rebuild = getattr(args, "rebuild", False)

    # Determine modes to run
    if args.all:
        modes = ["structured", "finbert", "legal", "structured-finbert", "structured-legal", "hybrid"]
    else:
        modes = [args.mode]

    logger.info("Running fusion for modes: %s (rebuild=%s)", modes, rebuild)

    success = True
    print("\n=== Feature Fusion Summary ===")
    for mode in modes:
        try:
            df, report = engine.build(mode=mode, rebuild=rebuild)
            
            print(f"\n  Mode: {mode}")
            print(f"    {'Status':<16}: {'SUCCESS' if report.success else 'FAILED'}")
            print(f"    {'Rows':<16}: {len(df)}")
            print(f"    {'Errors':<16}: {len(report.errors)}")
            print(f"    {'Warnings':<16}: {len(report.warnings)}")
            
            if report.errors:
                print("    Errors:")
                for err in report.errors[:5]:
                    print(f"      - {err}")
                if len(report.errors) > 5:
                    print(f"      - ... and {len(report.errors) - 5} more errors.")
                    
            if not report.success:
                success = False
        except Exception as exc:
            logger.error("Fusion build failed for mode '%s': %s", mode, exc, exc_info=True)
            print(f"\n  Mode: {mode}")
            print(f"    {'Status':<16}: FAILED")
            print(f"    {'Error':<16}: {exc}")
            success = False

    print("\n==============================\n")
    return 0 if success else 1


def cmd_select_features(args: argparse.Namespace) -> int:
    """
    Run feature selection on fused datasets (Task 5.4).
    """
    logger.info("Initializing FeatureSelectionEngine...")
    from features.selection_engine import FeatureSelectionEngine

    if not args.mode and not args.all:
        logger.error("Please specify either --mode <mode> or --all.")
        print("\n[ERROR] Please specify either --mode <mode> or --all.\n")
        return 1

    engine = FeatureSelectionEngine()
    rebuild = getattr(args, "rebuild", False)
    use_lightgbm = not getattr(args, "use_random_forest", False)

    # Determine modes to run
    if args.all:
        modes = ["structured", "finbert", "legal", "structured-finbert", "structured-legal", "hybrid"]
    else:
        modes = [args.mode]

    logger.info("Running feature selection for modes: %s (rebuild=%s)", modes, rebuild)

    success = True
    print("\n=== Feature Selection Summary ===")
    for mode in modes:
        try:
            df, report = engine.select_features(
                mode=mode,
                missing_threshold=args.missing_threshold,
                correlation_threshold=args.correlation_threshold,
                variance_threshold=args.variance_threshold,
                rebuild=rebuild,
                use_lightgbm=use_lightgbm,
            )
            
            print(f"\n  Mode: {mode}")
            print(f"    {'Status':<24}: {'SUCCESS' if report.success else 'FAILED'}")
            print(f"    {'Original Columns':<24}: {report.details.get('original_columns_count', 'N/A')}")
            print(f"    {'Selected Columns':<24}: {report.details.get('selected_columns_count', 'N/A')}")
            
            summary = report.details.get("removed_features_summary", {})
            print(f"    {'Removed Features':<24}: {sum(summary.values())}")
            for reason, count in summary.items():
                print(f"      - {reason:<22}: {count}")
            print(f"    {'Errors':<24}: {len(report.errors)}")
            print(f"    {'Warnings':<24}: {len(report.warnings)}")
            
            if report.errors:
                print("    Errors:")
                for err in report.errors:
                    print(f"      - {err}")
                    
            if not report.success:
                success = False
        except Exception as exc:
            logger.error("Feature selection failed for mode '%s': %s", mode, exc, exc_info=True)
            print(f"\n  Mode: {mode}")
            print(f"    {'Status':<24}: FAILED")
            print(f"    {'Error':<24}: {exc}")
            success = False

    print("\n=================================\n")
    return 0 if success else 1


# ---------------------------------------------------------------------------
# Task 6.1 — ML Training Engine
# ---------------------------------------------------------------------------


def cmd_train(args: argparse.Namespace) -> int:
    """
    Train supervised ML classifiers to predict legislative market impact.

    Trains up to 12 models (4 targets × 3 algorithms) using chronological
    TimeSeriesSplit validation.  Post-event features are automatically
    stripped to prevent target leakage.

    Returns
    -------
    int
        Exit code (0 = success, 1 = partial/total failure).
    """
    from models.training.trainer import MLTrainer

    mode = getattr(args, "mode", None) or settings.ML_DEFAULT_MODE
    target = getattr(args, "target", None)
    model_type = getattr(args, "model_type", None)
    rebuild_datasets = getattr(args, "rebuild_datasets", False)
    skip_existing = getattr(args, "skip_existing", False)
    n_splits = getattr(args, "n_splits", None)

    logger.info(
        "Initialising MLTrainer | mode=%s target=%s model_type=%s "
        "rebuild_datasets=%s skip_existing=%s",
        mode, target or "all", model_type or "all",
        rebuild_datasets, skip_existing,
    )

    trainer = MLTrainer(mode=mode, n_splits=n_splits)

    print("\n=== Legislative ML Training Engine ===")
    print(f"  Feature mode   : {mode}")
    print(f"  Target         : {target or 'all (4 classifiers)'}")
    print(f"  Model type     : {model_type or 'all (lgbm, xgboost, random_forest)'}")
    print(f"  Rebuild data   : {rebuild_datasets}")
    print(f"  Skip existing  : {skip_existing}")
    print("")

    success = True

    try:
        if target and model_type:
            # Train a single (target, model_type) pair
            report = trainer.train_target(
                target=target,
                model_type=model_type,
                rebuild_datasets=rebuild_datasets,
            )
            all_reports = {target: {model_type: report}}
        else:
            # Train all (target × model_type) combinations
            all_reports = trainer.train_all(
                rebuild_datasets=rebuild_datasets,
                skip_existing=skip_existing,
            )
    except Exception as exc:
        logger.error("ML Training failed: %s", exc, exc_info=True)
        print(f"\n[ERROR] Training failed: {exc}")
        return 1

    # Print summary table
    print("=== Training Results ===")
    print(f"  {'Target':<20} {'Model':<15} {'Val Acc':>8} {'Val F1':>8} {'Samples':>8}")
    print("  " + "-" * 63)
    for tgt, models in all_reports.items():
        for mtype, rep in models.items():
            print(
                f"  {tgt:<20} {mtype:<15} "
                f"{rep.mean_val_accuracy:>8.4f} "
                f"{rep.mean_val_f1_macro:>8.4f} "
                f"{rep.training_samples:>8d}"
            )
    print("  " + "-" * 63)
    n_trained = sum(len(v) for v in all_reports.values())
    print(f"\n  Total models trained : {n_trained}")
    print("  Artefacts saved to   : models/<target>/<model_type>/")
    print("  Datasets saved to    : data/ml/")
    print("==============================\n")

    return 0 if success else 1


# ---------------------------------------------------------------------------
# Task 6.2 — Model Evaluation Engine
# ---------------------------------------------------------------------------


def cmd_evaluate_models(args: argparse.Namespace) -> int:
    """
    Evaluate every trained model and compare their performance (Task 6.2).

    Loads the training dataset and all serialized models from target subdirectories,
    performs predictions, computes metrics, and produces rankings and error reports.

    Returns
    -------
    int
        Exit code (0 = success, 1 = failure).
    """
    from models.evaluation.evaluator import ModelEvaluator

    mode = getattr(args, "mode", None) or settings.ML_DEFAULT_MODE
    rebuild_dataset = getattr(args, "rebuild_dataset", False)

    logger.info("Running model evaluation | mode=%s rebuild=%s", mode, rebuild_dataset)

    print("\n=== Legislative Model Evaluation Engine ===")
    print(f"  Feature Mode: {mode}")
    print(f"  Rebuild Data: {rebuild_dataset}\n")

    try:
        evaluator = ModelEvaluator(mode=mode)
        results = evaluator.evaluate_all(rebuild_dataset=rebuild_dataset)
    except Exception as exc:
        logger.error("Model evaluation failed: %s", exc, exc_info=True)
        print(f"\n[ERROR] Evaluation failed: {exc}")
        return 1

    comparison = results.get("comparison", {})
    if not comparison:
        print("[WARNING] No trained models were found to evaluate. Run training first.")
        return 0

    print("=== Model Comparison & Rankings ===")
    for target, comparison_data in comparison.items():
        print(f"\nTarget: {target.upper()}")
        best = comparison_data.get("best_model", {})
        worst = comparison_data.get("worst_model", {})
        avg = comparison_data.get("average_performance", {})

        print(f"  Best Model  : {best.get('model_type', 'N/A').upper()} (Acc: {best.get('accuracy', 0.0):.4f}, F1-macro: {best.get('f1_macro', 0.0):.4f})")
        print(f"  Worst Model : {worst.get('model_type', 'N/A').upper()} (Acc: {worst.get('accuracy', 0.0):.4f}, F1-macro: {worst.get('f1_macro', 0.0):.4f})")
        print(f"  Average Perf: Acc: {avg.get('accuracy', 0.0):.4f}, F1-macro: {avg.get('f1_macro', 0.0):.4f}")

        print("\n  Full Rankings:")
        print(f"    {'Rank':<5} {'Model':<15} {'Accuracy':>10} {'F1-macro':>10} {'Log Loss':>10}")
        print("    " + "-" * 56)
        for r in comparison_data.get("rankings", []):
            log_loss_str = f"{r.get('log_loss'):.4f}" if r.get("log_loss") is not None else "N/A"
            print(f"    {r.get('rank'):<5} {r.get('model_type'):<15} {r.get('accuracy'):>10.4f} {r.get('f1_macro'):>10.4f} {log_loss_str:>10}")
    print("\n===========================================")
    print("Reports successfully generated and persisted under evaluation/")
    return 0


# ---------------------------------------------------------------------------
# Task 6.3 — Explainability Engine
# ---------------------------------------------------------------------------


def cmd_explain_models(args: argparse.Namespace) -> int:
    """
    Generate SHAP-based global and local explanations for trained models (Task 6.3).

    Loads trained model artefacts from ``models/`` and persists SHAP values,
    feature importance tables, visualizations, and local explanations to
    ``explainability/``.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Exit code (0 = success, 1 = failure).
    """
    from models.explainability.engine import ExplainabilityEngine

    target = getattr(args, "target", None)
    model = getattr(args, "model", None)
    mode = getattr(args, "mode", None) or settings.ML_DEFAULT_MODE
    run_all = getattr(args, "all", False)

    # --all is the default; --target or --model narrow it down
    if run_all:
        target = None
        model = None

    logger.info(
        "Running explainability engine | mode=%s target=%s model=%s",
        mode, target or "all", model or "all",
    )

    print("\n=== Legislative Explainability Engine (Task 6.3) ===")
    print(f"  Feature Mode : {mode}")
    print(f"  Target       : {target or 'all'}")
    print(f"  Model        : {model or 'all'}")
    print("")

    try:
        engine = ExplainabilityEngine(mode=mode)
        results = engine.explain_all(
            target_filter=target,
            model_filter=model,
        )
    except ImportError as exc:
        logger.error("Missing dependency for explainability: %s", exc)
        print(f"\n[ERROR] Missing dependency: {exc}")
        print("Install with: pip install shap")
        return 1
    except Exception as exc:
        logger.error("Explainability engine failed: %s", exc, exc_info=True)
        print(f"\n[ERROR] Explainability failed: {exc}")
        return 1

    if not results:
        print("[WARNING] No trained models were found. Run training first.")
        return 0

    # Print summary
    print("=== Explainability Results ===")
    print(f"  {'Target':<20} {'Model':<15} {'Samples':>8} {'Features':>9} {'Top Feature':<30}")
    print("  " + "-" * 88)
    for tgt, models in sorted(results.items()):
        for mtype, res in sorted(models.items()):
            top = res.get("top_features", ["N/A"])[0] if res.get("top_features") else "N/A"
            print(
                f"  {tgt:<20} {mtype:<15} "
                f"{res.get('n_samples', 0):>8d} "
                f"{res.get('n_features', 0):>9d} "
                f"{top:<30}"
            )
    print("  " + "-" * 88)
    n_done = sum(len(v) for v in results.values())
    print(f"\n  Total models explained : {n_done}")
    print("  SHAP values saved to   : explainability/<target>/<model_type>/shap_values.parquet")
    print("  Feature importance at  : explainability/<target>/<model_type>/feature_importance.csv")
    print("  Global summary at      : explainability/global_summary.json")
    print("  Model comparison at    : explainability/model_comparison.json")
    print("  Visualizations at      : explainability/<target>/<model_type>/")
    print("==========================================\n")
    return 0


# ---------------------------------------------------------------------------
# Task 6.4 — Historical Backtesting Engine
# ---------------------------------------------------------------------------


def cmd_backtest_models(args: argparse.Namespace) -> int:
    """
    Run walk-forward historical backtesting for legislative impact prediction models (Task 6.4).

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Exit code (0 = success, 1 = failure).
    """
    from backtesting.engine import HistoricalBacktestEngine

    target = getattr(args, "target", None)
    model = getattr(args, "model", None)
    start_date = getattr(args, "start_date", None)
    end_date = getattr(args, "end_date", None)
    transaction_cost = getattr(args, "transaction_cost", None)
    slippage = getattr(args, "slippage", None)
    anticipation_window = getattr(args, "anticipation_window", 0) or 0
    run_all = getattr(args, "all", False)

    targets_to_run = ["direction", "market_moving", "impact_strength", "confidence"]
    if target:
        targets_to_run = [target]

    print("\n=== Historical Backtesting Engine (Task 6.4) ===")
    print(f"  Target(s)           : {', '.join(targets_to_run)}")
    print(f"  Model Selection     : {model or 'Auto-select best per target by Macro F1'}")
    print(f"  Date Range          : {start_date or 'Earliest'} to {end_date or 'Latest'}")
    print(f"  Anticipation Window : [-{anticipation_window}, -1] days" if anticipation_window > 0 else "  Anticipation Window : None (Official introduction date)")
    if transaction_cost is not None:
        print(f"  Transaction Cost    : {transaction_cost * 10000.0:.1f} bps")
    else:
        print(f"  Transaction Cost    : Default ({settings.DEFAULT_TRANSACTION_COST * 10000.0:.1f} bps)")
    print("=================================================\n")

    try:
        engine = HistoricalBacktestEngine()
        results = []

        for tgt in targets_to_run:
            res = engine.run_backtest(
                target=tgt,
                model_name=model,
                start_date=start_date,
                end_date=end_date,
                anticipation_window_days=anticipation_window,
                transaction_cost=transaction_cost,
                slippage=slippage,
            )
            results.append(res)

        print("\n=== Backtest Performance Summary ===")
        print(f"  {'Target':<18} {'Model':<12} {'Macro F1':>9} {'Accuracy':>9} {'Strategy CumRet':>16} {'Sharpe':>8} {'MaxDD':>8}")
        print("  " + "-" * 88)

        for res in results:
            rep = res["report"]
            tgt = rep["target"]
            m_name = rep["model_name"]
            f1 = rep["predictive_performance"]["macro_f1"]
            acc = rep["predictive_performance"]["accuracy"]
            fin = rep["financial_performance"]["financial_metrics"]
            cum_ret = fin["cumulative_return"]
            sharpe = fin["sharpe_ratio"]
            max_dd = fin["max_drawdown"]

            print(
                f"  {tgt:<18} {m_name:<12} "
                f"{f1:>9.4f} {acc:>9.4f} "
                f"{cum_ret * 100.0:>15.2f}% "
                f"{sharpe:>8.2f} "
                f"{max_dd * 100.0:>7.2f}%"
            )

        print("  " + "-" * 88)
        print("\n  Outputs saved under data/backtests/<run_id>/")
        print("  - backtest_report.json")
        print("  - model_comparison.json")
        print("  - strategy_metrics.json")
        print("  - leakage_report.json")
        print("  - prediction_results.parquet")
        print("  - equity_curve.png, drawdown_curve.png, prediction_vs_actual.png, model_comparison.png")
        print("\n=================================================\n")
        return 0

    except Exception as exc:
        logger.error("Backtesting engine execution failed: %s", exc, exc_info=True)
        print(f"\n[ERROR] Backtesting failed: {exc}")
        return 1


# ---------------------------------------------------------------------------
# Task 6.5 — Anticipation Bias / Pre-Event Information Analysis
# ---------------------------------------------------------------------------


def cmd_analyze_anticipation(args: argparse.Namespace) -> int:
    """
    Execute Anticipation Bias & Pre-Event Information Analysis (Task 6.5).

    Analyzes multi-window pre-event market abnormal returns, evaluates external
    evidence under strict anti-leakage rules, and assigns anticipation scores.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Exit code (0 = success, 1 = failure).
    """
    from services.anticipation_service import AnticipationService
    from storage.anticipation_repository import AnticipationRepository

    year = getattr(args, "year", None)
    bill_id = getattr(args, "bill_id", None)
    company_isin = getattr(args, "company_isin", None)
    force_refresh = getattr(args, "force_refresh", False) or getattr(args, "rebuild", False)
    skip_existing = not force_refresh

    logger.info(
        "Running Anticipation Bias Analysis | year=%s bill_id=%s company_isin=%s force_refresh=%s",
        year,
        bill_id,
        company_isin,
        force_refresh,
    )

    print("\n=== Anticipation Bias & Pre-Event Analysis Engine (Task 6.5) ===")
    print(f"  Year Filter         : {year or 'All'}")
    print(f"  Bill ID Filter      : {bill_id or 'All'}")
    print(f"  Company Filter      : {company_isin or 'All'}")
    print(f"  Force Refresh       : {force_refresh}")
    print(f"  Incremental Skip    : {skip_existing}")
    print("================================================================\n")

    try:
        service = AnticipationService()
        stats = service.run_analysis(
            year=year,
            bill_id_filter=bill_id,
            company_isin_filter=company_isin,
            force_refresh=force_refresh,
            skip_existing=skip_existing,
        )

        print("\n=== Anticipation Analysis Summary ===")
        print(f"  {'Models Processed':<28}: {stats['models_processed']}")
        print(f"  {'Models Succeeded':<28}: {stats['models_succeeded']}")
        print(f"  {'Models Skipped (Cached)':<28}: {stats['models_skipped']}")
        print(f"  {'Models Failed':<28}: {stats['models_failed']}")
        print(f"  {'Bills Analyzed':<28}: {stats['bills_analyzed']}")
        print(f"  {'Flagged Bill-Company Pairs':<28}: {stats['flagged_pairs']}")
        print(f"  {'Flagged Bills (Overall)':<28}: {stats['flagged_bills']}")

        print("\n=== Classification Breakdown ===")
        print(f"  {'Classification Tier':<24} {'Count':>8}")
        print("  " + "-" * 34)
        for tier, cnt in stats["classifications"].items():
            print(f"  {tier:<24} {cnt:>8d}")
        print("  " + "-" * 34)

        # Retrieve and display top bill-level anticipation profiles
        repo = AnticipationRepository()
        all_bill_records = repo.get_all_bill_scores()
        if all_bill_records:
            all_bill_records.sort(key=lambda x: x.overall_anticipation_score, reverse=True)
            print("\n=== Top Evaluated Bills by Anticipation Score ===")
            print(
                f"  {'Bill ID':<40} {'Score':>7} {'Class':<18} {'Flagged %':>10} {'Companies':>10}"
            )
            print("  " + "-" * 90)
            for b_rec in all_bill_records[:10]:
                print(
                    f"  {b_rec.bill_id:<40} "
                    f"{b_rec.overall_anticipation_score:>7.4f} "
                    f"{b_rec.overall_classification:<18} "
                    f"{b_rec.pct_companies_flagged * 100.0:>9.1f}% "
                    f"{b_rec.total_companies_analyzed:>10d}"
                )
            print("  " + "-" * 90)

        print("\n  Outputs saved under data/anticipation/")
        print("  - scores/<bill_id>_<company_isin>.json")
        print("  - bill_scores/<bill_id>.json")
        print("  - market_stats/<bill_id>_<company_isin>_stats.json")
        print("  - reports/<report_id>.json")
        print("\n  [ACADEMIC NOTE] This component operates as a quantitative diagnostic layer.")
        print("  Pre-event abnormal returns reflect market anticipation patterns, not proof of")
        print("  non-public information leakage or insider trading.")
        print("================================================================\n")
        return 0

    except Exception as exc:
        logger.error("Anticipation analysis execution failed: %s", exc, exc_info=True)
        print(f"\n[ERROR] Anticipation analysis failed: {exc}")
        return 1


# ---------------------------------------------------------------------------
# Task 7.1 — Final Prediction & Decision Engine
# ---------------------------------------------------------------------------


def cmd_generate_predictions(args: argparse.Namespace) -> int:
    """
    Generate forward-looking predictions and decision-support interpretations (Task 7.1).

    Parameters
    ----------
    args : argparse.Namespace

    Returns
    -------
    int
        0 on success, 1 on failure.
    """
    from services.prediction import PredictionService

    year = getattr(args, "year", None)
    bill_id = getattr(args, "bill_id", None)
    company_isin = getattr(args, "company_isin", None)
    event_window = getattr(args, "event_window", None)
    force_refresh = getattr(args, "force_refresh", False) or getattr(args, "rebuild", False)
    mode = getattr(args, "mode", "structured") or "structured"

    logger.info(
        "Running Generate Predictions | year=%s bill=%s isin=%s window=%s force=%s mode=%s",
        year,
        bill_id,
        company_isin,
        event_window,
        force_refresh,
        mode,
    )

    print("\n=== Final Prediction & Decision Engine (Task 7.1) ===")
    print(f"  Year Filter         : {year or 'All'}")
    print(f"  Bill ID Filter      : {bill_id or 'All'}")
    print(f"  Company Filter      : {company_isin or 'All'}")
    print(f"  Event Window Filter : {event_window or 'Default ([-20,+20])'}")
    print(f"  Feature Mode        : {mode}")
    print(f"  Force Refresh       : {force_refresh}")
    print("=======================================================\n")

    try:
        service = PredictionService()
        stats = service.generate_predictions(
            bill_id=bill_id,
            company_isin=company_isin,
            year=year,
            event_window=event_window,
            force_refresh=force_refresh,
            mode=mode,
        )

        print("\n=== Prediction Run Summary ===")
        print(f"  {'Total Candidates':<28}: {stats['total_candidates']}")
        print(f"  {'Predictions Generated':<28}: {stats['predictions_generated']}")
        print(f"  {'Predictions Cached/Skipped':<28}: {stats['predictions_skipped']}")
        print(f"  {'Predictions Failed':<28}: {stats['predictions_failed']}")

        print("\n=== Models Selected & Used ===")
        for tgt, m_name in stats.get("models_used", {}).items():
            print(f"  {tgt:<24}: {m_name}")

        print("\n=== Target Distributions ===")
        print("  Direction:")
        for k, v in stats["target_distributions"]["direction"].items():
            print(f"    {k:<16}: {v:>6d}")
        print("  Market Moving:")
        for k, v in stats["target_distributions"]["market_moving"].items():
            print(f"    {k:<16}: {v:>6d}")
        print("  Impact Strength:")
        for k, v in stats["target_distributions"]["impact_strength"].items():
            print(f"    {k:<16}: {v:>6d}")
        print("  Confidence:")
        for k, v in stats["target_distributions"]["confidence"].items():
            print(f"    {k:<16}: {v:>6d}")

        # Display Top Generated Predictions
        records = stats.get("records", [])
        if records:
            print("\n=== Sample Generated Prediction Records ===")
            print(
                f"  {'Bill ID':<30} {'Company':<18} {'Dir (Prob)':<14} {'Mkt-Mov':<8} {'Strength':<10} {'Conf':<6} {'Anticipation':<16}"
            )
            print("  " + "-" * 110)
            for rec in records[:10]:
                d_prob = rec.direction_probability.get(rec.predicted_direction, 0.0)
                dir_str = f"{rec.predicted_direction} ({d_prob*100:.0f}%)"
                comp_label = rec.company_symbol or rec.company_isin[:12]
                print(
                    f"  {rec.bill_id[:28]:<30} "
                    f"{comp_label:<18} "
                    f"{dir_str:<14} "
                    f"{str(rec.predicted_market_moving):<8} "
                    f"{rec.predicted_impact_strength:<10} "
                    f"{rec.predicted_confidence:<6} "
                    f"{rec.anticipation_class:<16}"
                )
            print("  " + "-" * 110)

        print("\n  Outputs persisted under data/predictions/")
        print("  - data/predictions/pred_<bill_id>_<company_isin>_<event_window>.json")
        print("  - data/predictions/reports/val_<bill_id>_<company_isin>_<event_window>.json")
        print("\n  [DISCLAIMER] Output predictions represent quantitative decision-support models,")
        print("  NOT guaranteed stock price movements or investment advice.")
        print("=======================================================\n")
        return 0

    except Exception as exc:
        logger.error("Prediction generation failed: %s", exc, exc_info=True)
        print(f"\n[ERROR] Prediction generation failed: {exc}")
        return 1


def cmd_generate_decision_support(args: argparse.Namespace) -> int:
    """
    Trigger the Decision Support & Risk Scoring Engine (Task 7.2).

    Parameters
    ----------
    args : argparse.Namespace

    Returns
    -------
    int
        0 on success, 1 on failure.
    """
    from services.decision_service import DecisionSupportService

    year = getattr(args, "year", None)
    bill_id = getattr(args, "bill_id", None)
    company_isin = getattr(args, "company_isin", None)
    event_window = getattr(args, "event_window", None)
    force_refresh = getattr(args, "force_refresh", False) or getattr(args, "rebuild", False)

    logger.info(
        "Running Generate Decision Support | year=%s bill=%s isin=%s window=%s force=%s",
        year,
        bill_id,
        company_isin,
        event_window,
        force_refresh,
    )

    print("\n=== Decision Support & Risk Scoring Engine (Task 7.2) ===")
    print(f"  Year Filter         : {year or 'All'}")
    print(f"  Bill ID Filter      : {bill_id or 'All'}")
    print(f"  Company Filter      : {company_isin or 'All'}")
    print(f"  Event Window Filter : {event_window or 'All Windows'}")
    print(f"  Force Refresh       : {force_refresh}")
    print("=========================================================\n")

    try:
        service = DecisionSupportService()
        stats = service.generate_decision_support(
            bill_id=bill_id,
            company_isin=company_isin,
            year=year,
            event_window=event_window,
            force_refresh=force_refresh,
        )

        print("\n=== Decision Support Run Summary ===")
        print(f"  {'Total Candidates':<30}: {stats['total_candidates']}")
        print(f"  {'Decisions Generated':<30}: {stats['decisions_generated']}")
        print(f"  {'Decisions Cached/Skipped':<30}: {stats['decisions_skipped']}")
        print(f"  {'Decisions Failed':<30}: {stats['decisions_failed']}")

        print("\n=== Risk Category Distribution ===")
        for k, v in stats.get("risk_distribution", {}).items():
            print(f"  {k:<16}: {v:>6d}")

        print("\n=== Pricing-In Risk Distribution ===")
        for k, v in stats.get("pricing_in_distribution", {}).items():
            print(f"  {k:<16}: {v:>6d}")

        # Display Top Generated Decisions
        records = stats.get("records", [])
        if records:
            print("\n=== Sample Decision Support Records ===")
            print(
                f"  {'Bill ID':<30} {'Company':<16} {'Direction':<10} {'Impact':<8} {'Risk':<8} {'Risk Tier':<12} {'Pricing-In':<12}"
            )
            print("  " + "-" * 110)
            for rec in records[:10]:
                comp_label = rec.company_symbol or rec.company_isin[:12]
                print(
                    f"  {rec.bill_id[:28]:<30} "
                    f"{comp_label:<16} "
                    f"{rec.predicted_direction:<10} "
                    f"{rec.impact_score:<8.2f} "
                    f"{rec.risk_score:<8.2f} "
                    f"{rec.risk_category:<12} "
                    f"{rec.pricing_in_risk:<12}"
                )
            print("  " + "-" * 110)

        print("\n  Outputs persisted under data/decision_support/")
        print("  - data/decision_support/dec_<bill_id>_<company_isin>_<event_window>.json")
        print("  - data/decision_support/reports/val_dec_<bill_id>_<company_isin>_<event_window>.json")
        print("\n  [DISCLAIMER] Decision support outputs represent probabilistic quantitative research,")
        print("  NOT guaranteed stock price movements or financial investment advice.")
        print("=========================================================\n")
        return 0

    except Exception as exc:
        logger.error("Decision support generation failed: %s", exc, exc_info=True)
        print(f"\n[ERROR] Decision support generation failed: {exc}")
        return 1


# ---------------------------------------------------------------------------
# Task 7.3 — Stakeholder Reporting Engine
# ---------------------------------------------------------------------------


def cmd_generate_reports(args: argparse.Namespace) -> int:
    """
    Trigger the Stakeholder Reporting & Presentation Layer (Task 7.3).

    Generates structured, readable reports from DecisionSupportRecord outputs
    for Investors, Businesses, and the General Public.

    This command does NOT modify predictions, risk scores, or model outputs.
    It is a pure presentation layer.

    Returns
    -------
    int
        0 on success, 1 on failure.
    """
    from services.reporting_service import ReportingService

    bill_id = getattr(args, "bill_id", None)
    company_isin = getattr(args, "company_isin", None)
    stakeholder = getattr(args, "stakeholder", None)
    event_window = getattr(args, "event_window", None)
    output_format = (getattr(args, "format", None) or "json").upper()
    force_refresh = getattr(args, "force_refresh", False) or getattr(args, "rebuild", False)
    generate_bill = getattr(args, "generate_bill", False)
    generate_company = getattr(args, "generate_company", False)

    logger.info(
        "Running Generate Reports | bill=%s isin=%s stakeholder=%s format=%s force=%s",
        bill_id, company_isin, stakeholder, output_format, force_refresh,
    )

    print("\n=== Stakeholder Reporting & Presentation Engine (Task 7.3) ===")
    print(f"  Bill ID Filter      : {bill_id or 'All'}")
    print(f"  Company Filter      : {company_isin or 'All'}")
    print(f"  Stakeholder Type    : {stakeholder or 'All (INVESTOR / BUSINESS / PUBLIC)'}")
    print(f"  Event Window Filter : {event_window or 'All Windows'}")
    print(f"  Output Format       : {output_format}")
    print(f"  Force Refresh       : {force_refresh}")
    print("=============================================================\n")

    try:
        service = ReportingService()

        # Bill-level aggregation report
        if generate_bill and bill_id:
            print(f"Generating bill-level aggregation report for {bill_id}...")
            bill_report = service.generate_bill_report(bill_id, event_window or "", output_format)
            print(f"  Bill Report: {bill_report.report_id}")
            print(f"  Companies Affected: {bill_report.total_companies}")
            print(f"  Positive: {bill_report.positive_count} | Negative: {bill_report.negative_count} | Neutral: {bill_report.neutral_count}")
            print(f"  Avg Impact Score: {bill_report.avg_impact_score:.4f}")
            print("")

        # Company-level aggregation report
        if generate_company and company_isin:
            print(f"Generating company-level aggregation report for {company_isin}...")
            company_report = service.generate_company_report(company_isin, output_format)
            print(f"  Company Report: {company_report.report_id}")
            print(f"  Total Bills: {company_report.total_bills}")
            print(f"  Positive Bills: {company_report.positive_bill_count} | Negative Bills: {company_report.negative_bill_count}")
            print(f"  Avg Impact Score: {company_report.avg_impact_score:.4f}")
            print("")

        # Stakeholder reports
        stats = service.generate_reports(
            bill_id=bill_id,
            company_isin=company_isin,
            stakeholder=stakeholder,
            event_window=event_window,
            output_format=output_format,
            force_refresh=force_refresh,
        )

        print("\n=== Stakeholder Report Generation Summary ===")
        print(f"  {'Total Candidates':<30}: {stats['total_candidates']}")
        print(f"  {'Stakeholder Types':<30}: {', '.join(stats.get('stakeholder_types', []))}")
        print(f"  {'Reports Generated':<30}: {stats['reports_generated']}")
        print(f"  {'Reports Skipped (cached)':<30}: {stats['reports_skipped']}")
        print(f"  {'Reports Failed':<30}: {stats['reports_failed']}")
        print(f"  {'Validation Failures':<30}: {stats['validation_failures']}")

        # Sample reports
        reports = stats.get("reports", [])
        if reports:
            print("\n=== Sample Generated Reports ===")
            print(
                f"  {'Report ID':<50} {'Type':<10} {'Bill':<25} {'ISIN':<15}"
            )
            print("  " + "-" * 105)
            for r in reports[:5]:
                print(
                    f"  {r.report_id[:48]:<50} "
                    f"{r.stakeholder_type:<10} "
                    f"{r.bill_id[:23]:<25} "
                    f"{r.company_isin:<15}"
                )
            print("  " + "-" * 105)

        print("\n  Outputs persisted under data/reports/")
        print("    investor/  — Investor-perspective JSON/Markdown/CSV reports")
        print("    business/  — Business/regulatory-perspective reports")
        print("    public/    — Plain-English public reports")
        print("    bill_reports/    — Bill-level aggregation reports")
        print("    company_reports/ — Company-level aggregation reports")
        print("\n  [DISCLAIMER] Reports are academic decision-support outputs.")
        print("  They do NOT constitute investment advice, financial recommendations,")
        print("  or guarantees of future price movements.")
        print("=============================================================\n")
        return 0

    except Exception as exc:
        logger.error("Report generation failed: %s", exc, exc_info=True)
        print(f"\n[ERROR] Report generation failed: {exc}")
        return 1


# ---------------------------------------------------------------------------
# CLI setup
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Construct and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="legislative-intel",
        description=(
            "Legislative Intelligence & Market Impact Prediction System\n"
            "An AI-powered platform for understanding Indian legislative bills\n"
            "and predicting their impact on stock markets and businesses."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # status
    status_parser = subparsers.add_parser(
        "status",
        help="Verify project setup and print system information.",
    )
    status_parser.set_defaults(func=cmd_status)

    # scrape / ingest
    for cmd_name in ["scrape", "ingest"]:
        p = subparsers.add_parser(
            cmd_name,
            help="Ingest/scrape legislative bills from central government portals.",
        )
        p.add_argument(
            "--source",
            choices=["prs", "lok-sabha", "rajya-sabha"],
            default="prs",
            help="Data source to scrape (default: prs).",
        )
        p.add_argument(
            "--year",
            type=int,
            default=None,
            help="Ingest bills from a specific year only.",
        )
        p.add_argument(
            "--latest",
            action="store_true",
            help="Ingest only the latest active bills.",
        )
        p.add_argument(
            "--bill-id",
            type=str,
            default=None,
            help="Limit ingestion to a specific bill ID.",
        )
        p.add_argument(
            "--dry-run",
            action="store_true",
            help="Perform all discovery, parsing, and validation without persisting.",
        )
        p.set_defaults(func=cmd_ingest)

    # validate
    validate_parser = subparsers.add_parser(
        "validate",
        help="[Task 3] Run data validation checks on ingested data.",
    )
    validate_parser.set_defaults(func=cmd_validate)

    # download-docs
    download_parser = subparsers.add_parser(
        "download-docs",
        help="Download official PDF documents for ingested bills.",
    )
    download_parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Limit downloading to bills from a specific year.",
    )
    download_parser.add_argument(
        "--bill-id",
        type=str,
        default=None,
        help="Limit downloading to a specific bill ID.",
    )
    download_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate URLs and files without performing new downloads or saving to repository.",
    )
    download_parser.set_defaults(func=cmd_download_docs)

    # extract-text
    extract_parser = subparsers.add_parser(
        "extract-text",
        help="Extract text from downloaded PDFs and generate the legislative corpus.",
    )
    extract_parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Limit extraction to bills from a specific year.",
    )
    extract_parser.add_argument(
        "--bill-id",
        type=str,
        default=None,
        help="Limit extraction to a specific bill ID.",
    )
    extract_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute metrics without writing corpus files or updating the repository.",
    )
    extract_parser.set_defaults(func=cmd_extract_text)

    # build-knowledge
    knowledge_parser = subparsers.add_parser(
        "build-knowledge",
        help="Generate structured domain knowledge records for bills.",
    )
    knowledge_parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Limit knowledge generation to bills from a specific year.",
    )
    knowledge_parser.add_argument(
        "--bill-id",
        type=str,
        default=None,
        help="Limit knowledge generation to a specific bill ID.",
    )
    knowledge_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run knowledge generation and validation without saving records to repository.",
    )
    knowledge_parser.set_defaults(func=cmd_build_knowledge)

    # build-mappings
    mappings_parser = subparsers.add_parser(
        "build-mappings",
        help="Generate Bill-to-Company mappings for bills.",
    )
    mappings_parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Limit mapping generation to bills from a specific year.",
    )
    mappings_parser.add_argument(
        "--bill-id",
        type=str,
        default=None,
        help="Limit mapping generation to a specific bill ID.",
    )
    mappings_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run mapping generation and validation without saving records to repository.",
    )
    mappings_parser.set_defaults(func=cmd_build_mappings)

    # ingest-companies
    company_parser = subparsers.add_parser(
        "ingest-companies",
        help="Ingest and normalize listed companies from NSE and seed data.",
    )
    company_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate companies without saving to repository.",
    )
    company_parser.set_defaults(func=cmd_ingest_companies)

    # ingest-market
    market_parser = subparsers.add_parser(
        "ingest-market",
        help="Ingest and sync historical market price data for indices and companies.",
    )
    market_parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date for ingestion in YYYY-MM-DD format (defaults to 3 years ago).",
    )
    market_parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="End date for ingestion in YYYY-MM-DD format (defaults to today).",
    )
    market_parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Comma-separated list of yfinance symbols or tickers to ingest (e.g. INFY,RELIANCE.NS,^NSEI).",
    )
    market_parser.add_argument(
        "--index",
        action="store_true",
        help="Ingest only index price data, skipping companies.",
    )
    market_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force download full history instead of incremental syncing.",
    )
    market_parser.set_defaults(func=cmd_ingest_market)

    # estimate-market-models
    est_parser = subparsers.add_parser(
        "estimate-market-models",
        help="Estimate expected returns parameters using OLS market model.",
    )
    est_parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year of bills to process.",
    )
    est_parser.add_argument(
        "--bill-id",
        type=str,
        default=None,
        help="Specific Bill ID slug to filter on.",
    )
    est_parser.add_argument(
        "--benchmark",
        type=str,
        default="^NSEI",
        help="Benchmark yfinance symbol (default: ^NSEI for NIFTY 50).",
    )
    est_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force recomputation of OLS models, overwriting existing records.",
    )
    est_parser.set_defaults(func=cmd_estimate_market_models)

    # run-event-study
    es_parser = subparsers.add_parser(
        "run-event-study",
        help="Run advanced event study calculations for bill-company pairs.",
    )
    es_parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year of bills to process.",
    )
    es_parser.add_argument(
        "--bill-id",
        type=str,
        default=None,
        help="Specific Bill ID slug to filter on.",
    )
    es_parser.add_argument(
        "--company-isin",
        type=str,
        default=None,
        help="Specific Company ISIN to filter on.",
    )
    es_parser.add_argument(
        "--window",
        type=str,
        default=None,
        help="Comma-separated list of event windows to run (default: all standard windows).",
    )
    es_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force recomputation of event studies, overwriting existing records.",
    )
    es_parser.set_defaults(func=cmd_run_event_study)

    # run-statistical-significance
    stat_parser = subparsers.add_parser(
        "run-statistical-significance",
        help="Compute statistical significance of event study CARs (Task 4.3).",
    )
    stat_parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year of bills to process.",
    )
    stat_parser.add_argument(
        "--bill-id",
        type=str,
        default=None,
        help="Specific Bill ID slug to filter on.",
    )
    stat_parser.add_argument(
        "--company-isin",
        type=str,
        default=None,
        help="Specific Company ISIN to filter on.",
    )
    stat_parser.add_argument(
        "--window",
        type=str,
        default=None,
        help="Specific event window to filter on (e.g. [-5,+5]).",
    )
    stat_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force recalculation, overwriting existing records.",
    )
    stat_parser.set_defaults(func=cmd_run_statistical_significance)

    # generate-labels
    label_parser = subparsers.add_parser(
        "generate-labels",
        help="Generate ground-truth ML labels from event-study results (Task 4.4).",
    )
    label_parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Year of bills to process.",
    )
    label_parser.add_argument(
        "--bill-id",
        type=str,
        default=None,
        help="Specific Bill ID slug to filter on.",
    )
    label_parser.add_argument(
        "--window",
        type=str,
        default=None,
        help="Specific event window to filter on (e.g. [-5,+5]).",
    )
    label_parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Regenerate labels, overwriting any existing records.",
    )
    label_parser.set_defaults(func=cmd_generate_labels)

    # train subparser is defined below under Task 6.1 section

    # predict
    predict_parser = subparsers.add_parser(
        "predict",
        help="[Task 9] Generate predictions for a bill.",
    )
    predict_parser.add_argument(
        "--bill-id",
        type=str,
        required=False,
        help="Bill ID or path to bill PDF.",
    )
    predict_parser.set_defaults(func=cmd_predict)

    # serve / dashboard (Task 7.4)
    serve_parser = subparsers.add_parser(
        "serve",
        aliases=["dashboard"],
        help="[Task 7.4] Start the interactive Decision-Support Dashboard.",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to serve the dashboard on (default: 8501).",
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind the dashboard server to (default: localhost).",
    )
    serve_parser.set_defaults(func=cmd_serve)

    # build-features  (Task 5.1)
    features_parser = subparsers.add_parser(
        "build-features",
        help="[Task 5.1] Build the unified ML feature dataset (Parquet + optional CSV).",
    )
    features_parser.add_argument(
        "--rebuild",
        action="store_true",
        default=False,
        help="Force full rebuild, ignoring any existing feature records.",
    )
    features_parser.add_argument(
        "--export-csv",
        action="store_true",
        default=False,
        help="Export the feature dataset to CSV after building.",
    )
    features_parser.set_defaults(func=cmd_build_features)

    # generate-embeddings  (Task 5.2)
    embeddings_parser = subparsers.add_parser(
        "generate-embeddings",
        help="[Task 5.2] Generate reusable NLP text embeddings for legislative bills.",
    )
    embeddings_parser.add_argument(
        "--model",
        choices=["finbert", "legal-roberta"],
        default="finbert",
        help="Embedding model selection (default: finbert).",
    )
    embeddings_parser.add_argument(
        "--pooling",
        choices=["mean", "cls"],
        default="mean",
        help="Pooling strategy for token hidden states (default: mean).",
    )
    embeddings_parser.add_argument(
        "--force-refresh",
        action="store_true",
        default=False,
        help="Force full rebuild, ignoring any cached embeddings.",
    )
    embeddings_parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for model inference (default: 16).",
    )
    embeddings_parser.set_defaults(func=cmd_generate_embeddings)

    # build-fusion  (Task 5.3)
    fusion_parser = subparsers.add_parser(
        "build-fusion",
        help="[Task 5.3] Build fused datasets combining structured features and embeddings.",
    )
    fusion_parser.add_argument(
        "--mode",
        choices=["structured", "finbert", "legal", "structured-finbert", "structured-legal", "hybrid"],
        help="Specific fusion mode to build.",
    )
    fusion_parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Build all six fusion modes.",
    )
    fusion_parser.add_argument(
        "--rebuild",
        action="store_true",
        default=False,
        help="Force full rebuild, ignoring any existing records.",
    )
    fusion_parser.set_defaults(func=cmd_build_fusion)

    # select-features (Task 5.4)
    select_parser = subparsers.add_parser(
        "select-features",
        help="[Task 5.4] Run feature selection on fused datasets.",
    )
    select_parser.add_argument(
        "--mode",
        choices=["structured", "finbert", "legal", "structured-finbert", "structured-legal", "hybrid"],
        help="Specific fusion mode to run feature selection on.",
    )
    select_parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Run feature selection on all six fusion modes.",
    )
    select_parser.add_argument(
        "--missing-threshold",
        type=float,
        default=0.5,
        help="Threshold of missingness above which columns are removed (default: 0.5, set to 1.0 or None to disable).",
    )
    select_parser.add_argument(
        "--correlation-threshold",
        type=float,
        default=0.95,
        help="Threshold of Pearson correlation above which one of the pair is removed (default: 0.95).",
    )
    select_parser.add_argument(
        "--variance-threshold",
        type=float,
        default=0.01,
        help="Threshold of variance below which features are removed (default: 0.01).",
    )
    select_parser.add_argument(
        "--rebuild",
        action="store_true",
        default=False,
        help="Force rebuild feature selection even if selected datasets already exist.",
    )
    select_parser.add_argument(
        "--use-random-forest",
        action="store_true",
        default=False,
        help="Force use of Random Forest classifier instead of LightGBM (useful for testing fallback path).",
    )
    select_parser.set_defaults(func=cmd_select_features)

    # train (Task 6.1)
    train_parser = subparsers.add_parser(
        "train",
        help="[Task 6.1] Train ML classifiers to predict legislative market impact.",
    )
    train_parser.add_argument(
        "--mode",
        choices=["structured", "finbert", "legal", "structured-finbert", "structured-legal", "hybrid"],
        default=None,
        help="Feature-selection mode to use as training input (default: from settings).",
    )
    train_parser.add_argument(
        "--target",
        choices=["direction", "market_moving", "impact_strength", "confidence"],
        default=None,
        help="Train a specific target only (default: all four).",
    )
    train_parser.add_argument(
        "--model-type",
        dest="model_type",
        choices=["lgbm", "xgboost", "random_forest"],
        default=None,
        help="Train a specific model type only (default: all three).",
    )
    train_parser.add_argument(
        "--rebuild-datasets",
        dest="rebuild_datasets",
        action="store_true",
        default=False,
        help="Force rebuild of training/research datasets even if they already exist.",
    )
    train_parser.add_argument(
        "--skip-existing",
        dest="skip_existing",
        action="store_true",
        default=False,
        help="Skip (target, model_type) pairs that already have saved models.",
    )
    train_parser.add_argument(
        "--n-splits",
        dest="n_splits",
        type=int,
        default=None,
        help="Number of TimeSeriesSplit folds (default: from settings, typically 5).",
    )
    train_parser.set_defaults(func=cmd_train)

    # evaluate-models (Task 6.2)
    evaluate_parser = subparsers.add_parser(
        "evaluate-models",
        help="[Task 6.2] Evaluate every trained model and compare their performance.",
    )
    evaluate_parser.add_argument(
        "--mode",
        choices=["structured", "finbert", "legal", "structured-finbert", "structured-legal", "hybrid"],
        default=None,
        help="Feature-selection mode to evaluate (default: from settings).",
    )
    evaluate_parser.add_argument(
        "--rebuild-dataset",
        dest="rebuild_dataset",
        action="store_true",
        default=False,
        help="Force rebuild of training/research datasets before evaluation.",
    )
    evaluate_parser.set_defaults(func=cmd_evaluate_models)

    # explain-models (Task 6.3)
    explain_parser = subparsers.add_parser(
        "explain-models",
        help="[Task 6.3] Generate SHAP global and local explanations for trained models.",
    )
    explain_parser.add_argument(
        "--target",
        choices=["direction", "market_moving", "impact_strength", "confidence"],
        default=None,
        help="Explain a single prediction target (default: all four).",
    )
    explain_parser.add_argument(
        "--model",
        choices=["lgbm", "xgboost", "random_forest"],
        default=None,
        help="Explain a single model type (default: all three).",
    )
    explain_parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Explain all target × model_type combinations (default behaviour).",
    )
    explain_parser.add_argument(
        "--mode",
        choices=["structured", "finbert", "legal", "structured-finbert", "structured-legal", "hybrid"],
        default=None,
        help="Feature-selection mode to load (default: from settings).",
    )
    explain_parser.set_defaults(func=cmd_explain_models)

    # backtest-models (Task 6.4)
    backtest_parser = subparsers.add_parser(
        "backtest-models",
        help="[Task 6.4] Execute walk-forward historical backtests without look-ahead bias.",
    )
    backtest_parser.add_argument(
        "--target",
        choices=["direction", "market_moving", "impact_strength", "confidence"],
        default=None,
        help="Target target to backtest (default: all four).",
    )
    backtest_parser.add_argument(
        "--model",
        choices=["lgbm", "xgboost", "random_forest"],
        default=None,
        help="Model algorithm to backtest (default: auto-select best per target).",
    )
    backtest_parser.add_argument(
        "--start-date",
        dest="start_date",
        type=str,
        default=None,
        help="Start date filter (YYYY-MM-DD).",
    )
    backtest_parser.add_argument(
        "--end-date",
        dest="end_date",
        type=str,
        default=None,
        help="End date filter (YYYY-MM-DD).",
    )
    backtest_parser.add_argument(
        "--transaction-cost",
        dest="transaction_cost",
        type=float,
        default=None,
        help="Override total transaction cost fraction (e.g. 0.0010 = 10 bps, 0.0 for raw).",
    )
    backtest_parser.add_argument(
        "--slippage",
        dest="slippage",
        type=float,
        default=None,
        help="Override slippage fraction (e.g. 0.0005 = 5 bps).",
    )
    backtest_parser.add_argument(
        "--anticipation-window",
        dest="anticipation_window",
        type=int,
        default=0,
        help="Offset prediction timestamp by N days prior to bill introduction (default: 0).",
    )
    backtest_parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Run backtest across all four targets.",
    )
    backtest_parser.set_defaults(func=cmd_backtest_models)

    # analyze-anticipation (Task 6.5)
    anticipation_parser = subparsers.add_parser(
        "analyze-anticipation",
        help="[Task 6.5] Execute pre-event anticipation bias and information leakage analysis.",
    )
    anticipation_parser.add_argument(
        "--year",
        dest="year",
        type=int,
        default=None,
        help="Filter analysis by bill introduction year (e.g. 2024).",
    )
    anticipation_parser.add_argument(
        "--bill-id",
        dest="bill_id",
        type=str,
        default=None,
        help="Analyze a specific bill ID only.",
    )
    anticipation_parser.add_argument(
        "--company-isin",
        dest="company_isin",
        type=str,
        default=None,
        help="Analyze a specific company ISIN only.",
    )
    anticipation_parser.add_argument(
        "--force-refresh",
        dest="force_refresh",
        action="store_true",
        default=False,
        help="Force recomputation of existing anticipation records.",
    )
    anticipation_parser.add_argument(
        "--rebuild",
        dest="rebuild",
        action="store_true",
        default=False,
        help="Alias for --force-refresh.",
    )
    anticipation_parser.set_defaults(func=cmd_analyze_anticipation)

    # generate-predictions (Task 7.1)
    prediction_parser = subparsers.add_parser(
        "generate-predictions",
        help="[Task 7.1] Generate forward-looking market impact predictions and decision-support interpretations.",
    )
    prediction_parser.add_argument(
        "--year",
        dest="year",
        type=int,
        default=None,
        help="Filter predictions by bill introduction year (e.g. 2024).",
    )
    prediction_parser.add_argument(
        "--bill-id",
        dest="bill_id",
        type=str,
        default=None,
        help="Generate predictions for a specific bill ID only.",
    )
    prediction_parser.add_argument(
        "--company-isin",
        dest="company_isin",
        type=str,
        default=None,
        help="Generate predictions for a specific company ISIN only.",
    )
    prediction_parser.add_argument(
        "--event-window",
        dest="event_window",
        type=str,
        default=None,
        help="Filter by specific event window (default: '[-20,+20]').",
    )
    prediction_parser.add_argument(
        "--mode",
        dest="mode",
        choices=["structured", "finbert", "legal", "structured-finbert", "structured-legal", "hybrid"],
        default="structured",
        help="Feature-selection mode to use as input (default: 'structured').",
    )
    prediction_parser.add_argument(
        "--force-refresh",
        dest="force_refresh",
        action="store_true",
        default=False,
        help="Force regeneration of predictions even if existing versions match.",
    )
    prediction_parser.add_argument(
        "--rebuild",
        dest="rebuild",
        action="store_true",
        default=False,
        help="Alias for --force-refresh.",
    )
    prediction_parser.set_defaults(func=cmd_generate_predictions)

    # generate-decision-support (Task 7.2)
    decision_parser = subparsers.add_parser(
        "generate-decision-support",
        help="[Task 7.2] Generate qualitative stakeholder decision interpretations and composite risk scores.",
    )
    decision_parser.add_argument(
        "--year",
        dest="year",
        type=int,
        default=None,
        help="Filter decision support by bill introduction year (e.g. 2024).",
    )
    decision_parser.add_argument(
        "--bill-id",
        dest="bill_id",
        type=str,
        default=None,
        help="Generate decision support for a specific bill ID only.",
    )
    decision_parser.add_argument(
        "--company-isin",
        dest="company_isin",
        type=str,
        default=None,
        help="Generate decision support for a specific company ISIN only.",
    )
    decision_parser.add_argument(
        "--event-window",
        dest="event_window",
        type=str,
        default=None,
        help="Filter by specific event window.",
    )
    decision_parser.add_argument(
        "--force-refresh",
        dest="force_refresh",
        action="store_true",
        default=False,
        help="Force regeneration of decision records even if existing versions match.",
    )
    decision_parser.add_argument(
        "--rebuild",
        dest="rebuild",
        action="store_true",
        default=False,
        help="Alias for --force-refresh.",
    )
    decision_parser.set_defaults(func=cmd_generate_decision_support)

    # generate-reports (Task 7.3)
    reports_parser = subparsers.add_parser(
        "generate-reports",
        help="[Task 7.3] Generate structured stakeholder reports from decision-support outputs.",
    )
    reports_parser.add_argument(
        "--bill-id",
        dest="bill_id",
        type=str,
        default=None,
        help="Generate reports for a specific bill ID only.",
    )
    reports_parser.add_argument(
        "--company-isin",
        dest="company_isin",
        type=str,
        default=None,
        help="Generate reports for a specific company ISIN only.",
    )
    reports_parser.add_argument(
        "--stakeholder",
        dest="stakeholder",
        choices=["investor", "business", "public"],
        default=None,
        help="Stakeholder type filter: investor, business, or public (default: all three).",
    )
    reports_parser.add_argument(
        "--event-window",
        dest="event_window",
        type=str,
        default=None,
        help="Filter by specific event window (e.g. '[-20,+20]').",
    )
    reports_parser.add_argument(
        "--format",
        dest="format",
        choices=["json", "markdown", "csv"],
        default="json",
        help="Output format: json, markdown, or csv (default: json).",
    )
    reports_parser.add_argument(
        "--force-refresh",
        dest="force_refresh",
        action="store_true",
        default=False,
        help="Force regeneration of reports even if decision_version unchanged.",
    )
    reports_parser.add_argument(
        "--generate-bill-report",
        dest="generate_bill",
        action="store_true",
        default=False,
        help="Generate bill-level aggregation report (requires --bill-id).",
    )
    reports_parser.add_argument(
        "--generate-company-report",
        dest="generate_company",
        action="store_true",
        default=False,
        help="Generate company-level aggregation report (requires --company-isin).",
    )
    reports_parser.set_defaults(func=cmd_generate_reports)

    return parser



# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """
    Main CLI entry point.

    Returns
    -------
    int
        Process exit code.
    """
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        # Default behaviour: run status check
        logger.info("No command specified.  Running status check.")
        return cmd_status(args)

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
