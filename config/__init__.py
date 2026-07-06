"""
config package
==============
Centralised configuration for the Legislative Intelligence & Market Impact
Prediction System.

Usage
-----
    from config import settings, get_logger

    logger = get_logger(__name__)
    data_dir = settings.DATA_DIR
"""

from config.settings import Settings, settings
from config.logging_config import get_logger

__all__ = ["Settings", "settings", "get_logger"]
