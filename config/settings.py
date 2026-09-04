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
    STAT_RESULTS_DIR: Path = _env_path("STAT_RESULTS_DIR", str(_PROJECT_ROOT / "data" / "statistical_results"))

    # ------------------------------------------------------------------
    # Feature Engineering (Task 5.1)
    # ------------------------------------------------------------------
    # Root directory for feature dataset artefacts (Parquet + CSV)
    FEATURES_DIR: Path = _env_path("FEATURES_DIR", str(_PROJECT_ROOT / "data" / "features"))
    # Filename (without extension) for the master feature dataset
    FEATURE_DATASET_NAME: str = _env("FEATURE_DATASET_NAME", "master_feature_dataset")
    # Root directory for fused datasets (Task 5.3)
    FUSED_DIR: Path = _env_path("FUSED_DIR", str(_PROJECT_ROOT / "data" / "fused"))

    # ------------------------------------------------------------------
    # NLP Embedding Engine (Task 5.2)
    # ------------------------------------------------------------------
    EMBEDDINGS_DIR: Path = _env_path("EMBEDDINGS_DIR", str(_PROJECT_ROOT / "data" / "embeddings"))
    DEFAULT_EMBEDDING_MODEL: str = os.getenv("DEFAULT_EMBEDDING_MODEL", "finbert")
    DEFAULT_POOLING_STRATEGY: str = os.getenv("DEFAULT_POOLING_STRATEGY", "mean")

    # Model mapping from user-friendly name to Hugging Face model IDs
    MODEL_MAPPING: dict[str, str] = {
        "finbert": "ProsusAI/finbert",
        "legal-roberta": "lexlms/legal-roberta-base"
    }

    # Model dimensions
    EMBEDDING_DIMENSIONS: dict[str, int] = {
        "finbert": 768,
        "legal-roberta": 768
    }

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

    # ------------------------------------------------------------------
    # ML Training Engine (Task 6.1)
    # ------------------------------------------------------------------
    # Root directory for ML-ready datasets (training + research splits)
    ML_DATA_DIR: Path = _env_path("ML_DATA_DIR", str(_PROJECT_ROOT / "data" / "ml"))
    # Root directory for trained model artefacts per target
    ML_MODELS_DIR: Path = _env_path("ML_MODELS_DIR", str(_PROJECT_ROOT / "models"))
    # Feature-selection mode to load as input to training
    ML_DEFAULT_MODE: str = _env("ML_DEFAULT_MODE", "structured")
    # Number of chronological folds for TimeSeriesSplit
    ML_N_SPLITS: int = _env_int("ML_N_SPLITS", 5)
    # Random seed for reproducibility
    ML_RANDOM_SEED: int = _env_int("ML_RANDOM_SEED", 42)
    # Root directory for ML model evaluation reports (Task 6.2)
    ML_EVAL_DIR: Path = _env_path("ML_EVAL_DIR", str(_PROJECT_ROOT / "evaluation"))

    # ------------------------------------------------------------------
    # Explainability Engine (Task 6.3)
    # ------------------------------------------------------------------
    # Root directory for SHAP explanations, feature importance, and plots
    EXPLAINABILITY_DIR: Path = _env_path(
        "EXPLAINABILITY_DIR", str(_PROJECT_ROOT / "explainability")
    )

    # ------------------------------------------------------------------
    # Historical Backtesting Engine (Task 6.4)
    # ------------------------------------------------------------------
    # Root directory for backtest run outputs, metrics, and plots
    BACKTEST_DIR: Path = _env_path(
        "BACKTEST_DIR", str(_PROJECT_ROOT / "data" / "backtests")
    )
    DEFAULT_TRANSACTION_COST: float = float(
        os.getenv("DEFAULT_TRANSACTION_COST", "0.0010")
    )  # 10 bps
    DEFAULT_BROKERAGE: float = float(
        os.getenv("DEFAULT_BROKERAGE", "0.0005")
    )  # 5 bps
    DEFAULT_SLIPPAGE: float = float(
        os.getenv("DEFAULT_SLIPPAGE", "0.0005")
    )  # 5 bps

    # ------------------------------------------------------------------
    # Statistical Significance Settings
    # ------------------------------------------------------------------
    STAT_SIGNIFICANCE_ALPHA: float = float(os.getenv("STAT_SIGNIFICANCE_ALPHA", "0.05"))
    STAT_SIGNIFICANCE_T_THRESHOLD: float = float(os.getenv("STAT_SIGNIFICANCE_T_THRESHOLD", "1.96"))
    EFFECT_SIZE_MEDIUM_THRESHOLD: float = float(os.getenv("EFFECT_SIZE_MEDIUM_THRESHOLD", "0.02"))
    EFFECT_SIZE_LARGE_THRESHOLD: float = float(os.getenv("EFFECT_SIZE_LARGE_THRESHOLD", "0.05"))

    # ------------------------------------------------------------------
    # Label Generation Settings (Task 4.4)
    # ------------------------------------------------------------------

    # Directory where LabelRecord JSON files are persisted
    LABELS_DIR: Path = _env_path("LABELS_DIR", str(_PROJECT_ROOT / "data" / "labels"))

    # Direction label thresholds (fraction, e.g. 0.02 = 2%)
    # CAR > +LABEL_POSITIVE_CAR_THRESHOLD AND significant → POSITIVE
    LABEL_POSITIVE_CAR_THRESHOLD: float = float(os.getenv("LABEL_POSITIVE_CAR_THRESHOLD", "0.02"))
    # CAR < −LABEL_NEGATIVE_CAR_THRESHOLD AND significant → NEGATIVE
    LABEL_NEGATIVE_CAR_THRESHOLD: float = float(os.getenv("LABEL_NEGATIVE_CAR_THRESHOLD", "0.02"))

    # Market-moving label threshold (fraction)
    # True if significant AND |CAR| > threshold
    LABEL_MARKET_MOVING_CAR_THRESHOLD: float = float(
        os.getenv("LABEL_MARKET_MOVING_CAR_THRESHOLD", "0.02")
    )

    # Impact-strength CAR range boundaries (absolute CAR fractions)
    # |CAR| < LOW_MAX                     → LOW
    # LOW_MAX  ≤ |CAR| < MEDIUM_MAX       → MEDIUM
    # MEDIUM_MAX ≤ |CAR| < HIGH_MAX       → HIGH
    # |CAR| ≥ HIGH_MAX                    → VERY_HIGH
    LABEL_STRENGTH_LOW_MAX: float = float(os.getenv("LABEL_STRENGTH_LOW_MAX", "0.01"))
    LABEL_STRENGTH_MEDIUM_MAX: float = float(os.getenv("LABEL_STRENGTH_MEDIUM_MAX", "0.03"))
    LABEL_STRENGTH_HIGH_MAX: float = float(os.getenv("LABEL_STRENGTH_HIGH_MAX", "0.06"))

    # Confidence label p-value thresholds
    # HIGH   : p_value ≤ CONFIDENCE_HIGH_PVALUE  AND effect_size == "Large"
    # MEDIUM : p_value ≤ CONFIDENCE_MEDIUM_PVALUE OR  effect_size in {Medium, Large}
    # LOW    : everything else
    LABEL_CONFIDENCE_HIGH_PVALUE: float = float(
        os.getenv("LABEL_CONFIDENCE_HIGH_PVALUE", "0.01")
    )
    LABEL_CONFIDENCE_MEDIUM_PVALUE: float = float(
        os.getenv("LABEL_CONFIDENCE_MEDIUM_PVALUE", "0.05")
    )

    # ------------------------------------------------------------------
    # Anticipation Bias / Pre-Event Analysis Engine (Task 6.5)
    # ------------------------------------------------------------------
    # Root directory for anticipation scores, statistics, and validation reports
    ANTICIPATION_DIR: Path = _env_path(
        "ANTICIPATION_DIR", str(_PROJECT_ROOT / "data" / "anticipation")
    )
    # Pre-event analysis windows (trading-day offsets)
    ANTICIPATION_WINDOWS: list[str] = [
        "[-30,-21]",
        "[-20,-11]",
        "[-10,-6]",
        "[-5,-3]",
        "[-2,-1]",
    ]
    ANTICIPATION_CUMULATIVE_WINDOW: str = "[-30,-1]"

    # Configurable detection thresholds
    ANTICIPATION_Z_THRESHOLD: float = float(
        os.getenv("ANTICIPATION_Z_THRESHOLD", "1.96")
    )
    ANTICIPATION_CAR_MAGNITUDE_THRESHOLD: float = float(
        os.getenv("ANTICIPATION_CAR_MAGNITUDE_THRESHOLD", "0.02")
    )  # 2.0%
    ANTICIPATION_SUSTAINED_DIRECTION_RATIO: float = float(
        os.getenv("ANTICIPATION_SUSTAINED_DIRECTION_RATIO", "0.70")
    )  # 70%
    ANTICIPATION_IMMEDIATE_CAR_THRESHOLD: float = float(
        os.getenv("ANTICIPATION_IMMEDIATE_CAR_THRESHOLD", "0.015")
    )  # 1.5%
    ANTICIPATION_FLAG_THRESHOLD: float = float(
        os.getenv("ANTICIPATION_FLAG_THRESHOLD", "0.50")
    )

    # Classification thresholds
    ANTICIPATION_STRONG_THRESHOLD: float = float(
        os.getenv("ANTICIPATION_STRONG_THRESHOLD", "0.75")
    )
    ANTICIPATION_MODERATE_THRESHOLD: float = float(
        os.getenv("ANTICIPATION_MODERATE_THRESHOLD", "0.50")
    )
    ANTICIPATION_WEAK_THRESHOLD: float = float(
        os.getenv("ANTICIPATION_WEAK_THRESHOLD", "0.25")
    )

    # Observation thresholds
    ANTICIPATION_MIN_OBSERVATIONS_PER_WINDOW: int = _env_int(
        "ANTICIPATION_MIN_OBSERVATIONS_PER_WINDOW", 2
    )
    ANTICIPATION_MIN_CUMULATIVE_OBSERVATIONS: int = _env_int(
        "ANTICIPATION_MIN_CUMULATIVE_OBSERVATIONS", 15
    )

    # ------------------------------------------------------------------
    # Final Prediction & Decision Engine (Task 7.1)
    # ------------------------------------------------------------------
    PREDICTIONS_DIR: Path = _env_path(
        "PREDICTIONS_DIR", str(_PROJECT_ROOT / "data" / "predictions")
    )
    PREDICTION_DEFAULT_EVENT_WINDOW: str = os.getenv(
        "PREDICTION_DEFAULT_EVENT_WINDOW", "[-20,+20]"
    )

    # ------------------------------------------------------------------
    # Decision Support & Risk Scoring Engine (Task 7.2)
    # ------------------------------------------------------------------
    DECISION_SUPPORT_DIR: Path = _env_path(
        "DECISION_SUPPORT_DIR", str(_PROJECT_ROOT / "data" / "decision_support")
    )
    DECISION_VERSION: str = os.getenv("DECISION_VERSION", "v1.0")

    # ------------------------------------------------------------------
    # Stakeholder Reporting Engine (Task 7.3)
    # ------------------------------------------------------------------
    REPORTS_DIR: Path = _env_path(
        "REPORTS_DIR", str(_PROJECT_ROOT / "data" / "reports")
    )
    REPORT_VERSION: str = os.getenv("REPORT_VERSION", "v1.0")

    # Impact scoring weights & parameters
    DECISION_WEIGHT_DIRECTION_POLARITY: float = float(
        os.getenv("DECISION_WEIGHT_DIRECTION_POLARITY", "0.50")
    )
    DECISION_WEIGHT_IMPACT_STRENGTH: float = float(
        os.getenv("DECISION_WEIGHT_IMPACT_STRENGTH", "0.50")
    )
    DECISION_ANTICIPATION_DISCOUNT_FACTOR: float = float(
        os.getenv("DECISION_ANTICIPATION_DISCOUNT_FACTOR", "0.30")
    )

    # Risk scoring composite component weights (sum to 1.0)
    DECISION_RISK_UNCERTAINTY_WEIGHT: float = float(
        os.getenv("DECISION_RISK_UNCERTAINTY_WEIGHT", "0.30")
    )
    DECISION_RISK_ANTICIPATION_WEIGHT: float = float(
        os.getenv("DECISION_RISK_ANTICIPATION_WEIGHT", "0.25")
    )
    DECISION_RISK_TAIL_MAGNITUDE_WEIGHT: float = float(
        os.getenv("DECISION_RISK_TAIL_MAGNITUDE_WEIGHT", "0.25")
    )
    DECISION_RISK_DIRECTIONAL_CONFLICT_WEIGHT: float = float(
        os.getenv("DECISION_RISK_DIRECTIONAL_CONFLICT_WEIGHT", "0.20")
    )

    # Risk category threshold boundaries
    RISK_THRESHOLD_VERY_LOW: float = float(
        os.getenv("RISK_THRESHOLD_VERY_LOW", "0.20")
    )
    RISK_THRESHOLD_LOW: float = float(
        os.getenv("RISK_THRESHOLD_LOW", "0.40")
    )
    RISK_THRESHOLD_MODERATE: float = float(
        os.getenv("RISK_THRESHOLD_MODERATE", "0.60")
    )
    RISK_THRESHOLD_HIGH: float = float(
        os.getenv("RISK_THRESHOLD_HIGH", "0.80")
    )

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
            self.STAT_RESULTS_DIR,
            self.LABELS_DIR,
            self.FEATURES_DIR,
            self.EMBEDDINGS_DIR,
            self.FUSED_DIR,
            # Task 6.1 — ML Training
            self.ML_DATA_DIR,
            self.ML_MODELS_DIR,
            # Task 6.2 — ML Evaluation
            self.ML_EVAL_DIR,
            # Task 6.3 — Explainability Engine
            self.EXPLAINABILITY_DIR,
            # Task 6.4 — Historical Backtesting Engine
            self.BACKTEST_DIR,
            # Task 6.5 — Anticipation Bias Engine
            self.ANTICIPATION_DIR,
            # Task 7.1 — Final Prediction Engine
            self.PREDICTIONS_DIR,
            # Task 7.2 — Decision Support Engine
            self.DECISION_SUPPORT_DIR,
            # Task 7.3 — Stakeholder Reporting Engine
            self.REPORTS_DIR,
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
