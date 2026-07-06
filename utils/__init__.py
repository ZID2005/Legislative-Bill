"""
utils package
=============
Shared helper utilities used across all modules in the project.

Sub-modules
-----------
file_utils  : File I/O helpers, safe directory creation, JSON/CSV wrappers.
date_utils  : Date parsing, formatting, business-day logic.
text_utils  : Text cleaning, normalisation, and basic string helpers.

Usage
-----
    from utils.file_utils import ensure_dir, save_json
    from utils.date_utils import parse_date, today_str
    from utils.text_utils import clean_text, slugify
"""

from utils.file_utils import ensure_dir, load_json, save_json
from utils.date_utils import parse_date, today_str, is_business_day
from utils.text_utils import clean_text, slugify, truncate

__all__ = [
    # file
    "ensure_dir",
    "load_json",
    "save_json",
    # date
    "parse_date",
    "today_str",
    "is_business_day",
    # text
    "clean_text",
    "slugify",
    "truncate",
]
