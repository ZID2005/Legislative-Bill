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


def cmd_validate(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Placeholder: will trigger data validation (Task 3)."""
    logger.warning("Validation pipeline not yet implemented.  See Task 3.")
    return 1


def cmd_train(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Placeholder: will trigger model training (Task 8)."""
    logger.warning("Training pipeline not yet implemented.  See Task 8.")
    return 1


def cmd_predict(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Placeholder: will serve predictions for a new bill (Task 9)."""
    logger.warning("Prediction pipeline not yet implemented.  See Task 9.")
    return 1


def cmd_serve(args: argparse.Namespace) -> int:  # noqa: ARG001
    """Placeholder: will start the dashboard server (Task 10)."""
    logger.warning("Dashboard not yet implemented.  See Task 10.")
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

    # train
    train_parser = subparsers.add_parser(
        "train",
        help="[Task 8] Train the market impact prediction model.",
    )
    train_parser.add_argument(
        "--experiment",
        type=str,
        default="default",
        help="MLflow experiment name.",
    )
    train_parser.set_defaults(func=cmd_train)

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

    # serve
    serve_parser = subparsers.add_parser(
        "serve",
        help="[Task 10] Start the knowledge dashboard.",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port to serve the dashboard on (default: 8501).",
    )
    serve_parser.set_defaults(func=cmd_serve)

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
