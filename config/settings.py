"""
config/settings.py
==================
Centralised, environment-aware project settings.

All configuration is loaded from environment variables (via a .env file or
the host OS).  No hardcoded secrets, paths, or API keys appear anywhere else
in the codebase — they must always be sourced from this module.

Usage
-----
    from config.settings import settings

    print(settings.PROJECT_ROOT)
    print(settings.DATA_DIR)
    print(settings.LOG_LEVEL)

Design Notes
------------
*  We use ``python-dotenv`` to load a ``.env`` file at import time so that
   developers never have to set system-wide environment variables manually.
*  All path-type settings are :class:`pathlib.Path` objects so that callers
   can use ``/`` path composition without string concatenation.
*  ``Settings`` is a frozen dataclass-like object (implemented as a plain
   class with properties) so that settings are read-only at runtime.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env **before** reading any os.getenv calls
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=False)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _env(key: str, default: str | None = None) -> str:
    """Return an environment variable or a default; raise if neither exists."""
    value = os.getenv(key, default)
    if value is None:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set.  "
            f"Add it to your .env file (see .env.example)."
        )
    return value


def _env_path(key: str, default: str | None = None) -> Path:
    """Return an environment variable interpreted as an absolute path."""
    raw = _env(key, default)
    p = Path(raw)
    return p if p.is_absolute() else _PROJECT_ROOT / p


def _env_bool(key: str, default: bool = False) -> bool:
    """Return an environment variable interpreted as a boolean."""
    return os.getenv(key, str(default)).strip().lower() in {"1", "true", "yes"}


def _env_int(key: str, default: int = 0) -> int:
    """Return an environment variable interpreted as an integer."""
    return int(os.getenv(key, str(default)))


# ---------------------------------------------------------------------------
# Settings class
# ---------------------------------------------------------------------------

class Settings:
    """
    Singleton-style settings object.

    All attributes are computed once at import time.  Access them via the
    module-level ``settings`` instance::

        from config.settings import settings

    Attributes
    ----------
    PROJECT_ROOT : Path
        Absolute path to the repository root.
    DATA_DIR : Path
        Root directory for all data artefacts.
    RAW_DIR : Path
        Raw (unmodified) source data.
    PROCESSED_DIR : Path
        Cleaned and transformed data ready for modelling.
    BILLS_DIR : Path
        Downloaded bill PDFs and associated metadata.
    COMPANIES_DIR : Path
        BSE/NSE company master records.
    MARKET_DIR : Path
        Historical price/volume data from exchanges.
    EXTERNAL_DIR : Path
        Third-party supplementary datasets.
    LOGS_DIR : Path
        Runtime log files.
    LOG_LEVEL : str
        Python logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    LOG_FORMAT : str
        Log record format string.
    ENV : str
        Runtime environment tag: 'development', 'staging', or 'production'.
    DEBUG : bool
        Convenience flag; True when ENV == 'development'.
    PRS_BASE_URL : str
        Base URL for the PRS Legislative Research website.
    LOK_SABHA_BASE_URL : str
        Base URL for the Lok Sabha website.
    RAJYA_SABHA_BASE_URL : str
        Base URL for the Rajya Sabha website.
    DB_URL : str
        Database connection URL (SQLite by default for MVP).
    REQUEST_TIMEOUT_SECONDS : int
        HTTP request timeout for scrapers.
    REQUEST_DELAY_SECONDS : float
        Polite delay between successive HTTP requests.
    """

    # ------------------------------------------------------------------
    # Core paths
    # ------------------------------------------------------------------
    PROJECT_ROOT: Path = _PROJECT_ROOT

    DATA_DIR: Path = _env_path("DATA_DIR", str(_PROJECT_ROOT / "data"))
    RAW_DIR: Path = _env_path("RAW_DIR", str(_PROJECT_ROOT / "data" / "raw"))
    PROCESSED_DIR: Path = _env_path("PROCESSED_DIR", str(_PROJECT_ROOT / "data" / "processed"))
    BILLS_DIR: Path = _env_path("BILLS_DIR", str(_PROJECT_ROOT / "data" / "bills"))
    COMPANIES_DIR: Path = _env_path("COMPANIES_DIR", str(_PROJECT_ROOT / "data" / "companies"))
    MARKET_DIR: Path = _env_path("MARKET_DIR", str(_PROJECT_ROOT / "data" / "market"))
    EXTERNAL_DIR: Path = _env_path("EXTERNAL_DIR", str(_PROJECT_ROOT / "data" / "external"))
    LOGS_DIR: Path = _env_path("LOGS_DIR", str(_PROJECT_ROOT / "logs"))

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = _env("LOG_LEVEL", "INFO").upper()
    LOG_FORMAT: str = _env(
        "LOG_FORMAT",
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )

    # ------------------------------------------------------------------
    # Runtime environment
    # ------------------------------------------------------------------
    ENV: str = _env("ENV", "development").lower()
    DEBUG: bool = ENV == "development"

    # ------------------------------------------------------------------
    # External data sources (URLs)
    # ------------------------------------------------------------------
    PRS_BASE_URL: str = _env("PRS_BASE_URL", "https://prsindia.org")
    LOK_SABHA_BASE_URL: str = _env("LOK_SABHA_BASE_URL", "https://loksabha.nic.in")
    RAJYA_SABHA_BASE_URL: str = _env("RAJYA_SABHA_BASE_URL", "https://rajyasabha.nic.in")

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DB_URL: str = _env("DB_URL", f"sqlite:///{_PROJECT_ROOT / 'data' / 'legislative_intel.db'}")

    # ------------------------------------------------------------------
    # HTTP / scraping behaviour
    # ------------------------------------------------------------------
    REQUEST_TIMEOUT_SECONDS: int = _env_int("REQUEST_TIMEOUT_SECONDS", 30)
    REQUEST_DELAY_SECONDS: float = float(_env("REQUEST_DELAY_SECONDS", "1.5"))

    # ------------------------------------------------------------------
    # Future: API keys (read from env, never hardcoded)
    # ------------------------------------------------------------------
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    NSE_API_KEY: str = os.getenv("NSE_API_KEY", "")
    BSE_API_KEY: str = os.getenv("BSE_API_KEY", "")

    # ------------------------------------------------------------------
    # Future: Model configuration stubs
    # ------------------------------------------------------------------
    MODEL_DIR: Path = _env_path("MODEL_DIR", str(_PROJECT_ROOT / "models" / "artefacts"))
    RANDOM_SEED: int = _env_int("RANDOM_SEED", 42)
    TEST_SIZE: float = float(_env("TEST_SIZE", "0.2"))

    def ensure_directories(self) -> None:
        """Create all required project directories if they do not already exist."""
        dirs = [
            self.DATA_DIR,
            self.RAW_DIR,
            self.PROCESSED_DIR,
            self.BILLS_DIR,
            self.COMPANIES_DIR,
            self.MARKET_DIR,
            self.EXTERNAL_DIR,
            self.LOGS_DIR,
            self.MODEL_DIR,
        ]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        return (
            f"<Settings env={self.ENV!r} "
            f"project_root={self.PROJECT_ROOT!r} "
            f"log_level={self.LOG_LEVEL!r}>"
        )


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
settings = Settings()
