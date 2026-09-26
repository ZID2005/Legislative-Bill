"""
scripts/run_scheduler.py
========================
Production scheduler entrypoint for Task 8.20.
Dispatches scheduled recurring jobs (legislative monitoring, digests, maintenance).
Uses distributed locks to prevent duplicate execution across multiple scheduler replicas.
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.logging_config import get_logger
from infrastructure.jobs.runner import BackgroundJobRunner, JobExecutionMode

logger = get_logger("scheduler")

def main():
    logger.info("Starting Legislative Intelligence Scheduler process...")
    runner = BackgroundJobRunner(mode=JobExecutionMode.SCHEDULER_MODE)

    once = os.getenv("RUN_ONCE", "false").lower() in ("1", "true", "yes")

    while True:
        try:
            logger.info("Running scheduled monitoring check...")
            runner.run_legislative_monitoring()

            logger.info("Running scheduled digest generation...")
            runner.run_digest_generation()

            logger.info("Running scheduled maintenance...")
            runner.run_scheduled_maintenance()

        except Exception as exc:
            logger.error("Error during scheduler execution: %s", exc)

        if once:
            logger.info("Single pass complete; exiting scheduler.")
            break

        time.sleep(60)

if __name__ == "__main__":
    main()
