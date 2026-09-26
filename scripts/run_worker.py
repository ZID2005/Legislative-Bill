"""
scripts/run_worker.py
=====================
Production background worker entrypoint for Task 8.20.
Runs pending background jobs (monitoring, alert processing, notification delivery, digests).
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.logging_config import get_logger
from infrastructure.jobs.runner import BackgroundJobRunner, JobExecutionMode, JobType

logger = get_logger("worker")

def main():
    logger.info("Starting Legislative Intelligence Background Worker process...")
    runner = BackgroundJobRunner(mode=JobExecutionMode.WORKER_MODE)

    # Run jobs in loop or single pass
    once = os.getenv("RUN_ONCE", "false").lower() in ("1", "true", "yes")

    while True:
        try:
            logger.info("Executing alert processing cycle...")
            runner.run_alert_processing()

            logger.info("Executing notification delivery cycle...")
            runner.run_notification_delivery()

            logger.info("Executing email dispatch cycle...")
            runner.run_email_dispatch()

        except Exception as exc:
            logger.error("Error during worker execution: %s", exc)

        if once:
            logger.info("Single pass complete; exiting worker.")
            break

        time.sleep(15)

if __name__ == "__main__":
    main()
