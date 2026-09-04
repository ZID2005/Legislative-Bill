"""
dashboard/dashboard.py
======================
Interactive knowledge and decision-support dashboard — Task 7.4.

Provides Python API entry point for launching the Streamlit application.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from config.logging_config import get_logger

logger = get_logger(__name__)

_DASHBOARD_APP_PATH = Path(__file__).resolve().parent / "app.py"


def run_dashboard(port: int = 8501, host: str = "localhost") -> int:
    """
    Launch the Streamlit interactive dashboard application.

    Parameters
    ----------
    port : int, optional
        Port to serve the dashboard on (default: 8501).
    host : str, optional
        Host address (default: "localhost").

    Returns
    -------
    int
        Process return code.
    """
    logger.info("Starting Legislative Intelligence Dashboard on %s:%d...", host, port)
    app_path = str(_DASHBOARD_APP_PATH)

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        app_path,
        "--server.port",
        str(port),
        "--server.address",
        host,
        "--browser.gatherUsageStats",
        "false",
    ]

    try:
        proc = subprocess.run(cmd, check=False)
        return proc.returncode
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user.")
        return 0
    except Exception as exc:
        logger.error("Failed to start dashboard: %s", exc)
        return 1
