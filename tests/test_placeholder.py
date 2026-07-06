"""
tests/test_placeholder.py
=========================
Smoke tests for the project foundation (Task 0).

These tests verify that the project scaffold is correctly set up:
*  Settings load without error
*  Directory paths are valid Path objects
*  Logger returns a Logger instance
*  Text, date, and file utilities function correctly

Extend this file with unit tests as new modules are implemented.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Settings tests
# ---------------------------------------------------------------------------

class TestSettings:
    """Verify the Settings object initialises correctly."""

    def test_settings_import(self) -> None:
        from config.settings import settings
        assert settings is not None

    def test_project_root_is_path(self) -> None:
        from config.settings import settings
        assert isinstance(settings.PROJECT_ROOT, Path)

    def test_project_root_exists(self) -> None:
        from config.settings import settings
        assert settings.PROJECT_ROOT.is_dir()

    def test_data_dir_is_path(self) -> None:
        from config.settings import settings
        assert isinstance(settings.DATA_DIR, Path)

    def test_log_level_is_string(self) -> None:
        from config.settings import settings
        assert isinstance(settings.LOG_LEVEL, str)
        assert settings.LOG_LEVEL in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    def test_env_has_valid_value(self) -> None:
        from config.settings import settings
        assert settings.ENV in {"development", "staging", "production"}

    def test_request_timeout_positive(self) -> None:
        from config.settings import settings
        assert settings.REQUEST_TIMEOUT_SECONDS > 0

    def test_repr(self) -> None:
        from config.settings import settings
        assert "Settings" in repr(settings)


# ---------------------------------------------------------------------------
# Logger tests
# ---------------------------------------------------------------------------

class TestLogger:
    """Verify the logging system initialises and returns usable loggers."""

    def test_get_logger_returns_logger(self) -> None:
        import logging
        from config.logging_config import get_logger
        logger = get_logger(__name__)
        assert isinstance(logger, logging.Logger)

    def test_logger_name_contains_namespace(self) -> None:
        from config.logging_config import get_logger
        logger = get_logger("test_module")
        assert "legislative_intel" in logger.name

    def test_logger_can_log_info(self) -> None:
        from config.logging_config import get_logger
        logger = get_logger(__name__)
        # Should not raise
        logger.info("Test log message from test suite")


# ---------------------------------------------------------------------------
# Text utils tests
# ---------------------------------------------------------------------------

class TestTextUtils:
    """Verify text utility functions produce correct output."""

    def test_clean_text_strips_whitespace(self) -> None:
        from utils.text_utils import clean_text
        assert clean_text("  hello  world  ") == "hello world"

    def test_clean_text_collapses_newlines(self) -> None:
        from utils.text_utils import clean_text
        assert clean_text("line1\n\nline2") == "line1 line2"

    def test_clean_text_empty_string(self) -> None:
        from utils.text_utils import clean_text
        assert clean_text("") == ""

    def test_slugify_basic(self) -> None:
        from utils.text_utils import slugify
        assert slugify("The Finance Bill, 2024") == "the-finance-bill-2024"

    def test_slugify_special_chars(self) -> None:
        from utils.text_utils import slugify
        result = slugify("Digital Personal Data Protection Act — 2023")
        assert "digital" in result
        assert "2023" in result
        assert " " not in result

    def test_truncate_within_limit(self) -> None:
        from utils.text_utils import truncate
        short = "Hello"
        assert truncate(short, max_length=100) == short

    def test_truncate_exceeds_limit(self) -> None:
        from utils.text_utils import truncate
        long_text = "The quick brown fox jumps over the lazy dog"
        result = truncate(long_text, max_length=15)
        assert len(result) <= 15

    def test_extract_bill_year(self) -> None:
        from utils.text_utils import extract_bill_year
        assert extract_bill_year("The Finance Bill, 2024") == 2024
        assert extract_bill_year("No year here") is None

    def test_normalise_company_name(self) -> None:
        from utils.text_utils import normalise_company_name
        result = normalise_company_name("Tata Consultancy Services Limited")
        assert "LIMITED" not in result
        assert "TATA" in result


# ---------------------------------------------------------------------------
# Date utils tests
# ---------------------------------------------------------------------------

class TestDateUtils:
    """Verify date utility functions."""

    def test_parse_date_iso(self) -> None:
        from utils.date_utils import parse_date
        result = parse_date("2024-12-31")
        assert result == date(2024, 12, 31)

    def test_parse_date_indian_format(self) -> None:
        from utils.date_utils import parse_date
        result = parse_date("31-12-2024")
        assert result == date(2024, 12, 31)

    def test_parse_date_invalid(self) -> None:
        from utils.date_utils import parse_date
        assert parse_date("not-a-date") is None
        assert parse_date("") is None
        assert parse_date(None) is None  # type: ignore[arg-type]

    def test_today_str_format(self) -> None:
        from utils.date_utils import today_str
        result = today_str()
        assert len(result) == 10
        assert result.count("-") == 2

    def test_is_business_day_weekday(self) -> None:
        from utils.date_utils import is_business_day
        monday = date(2024, 12, 30)  # Monday
        assert is_business_day(monday) is True

    def test_is_business_day_weekend(self) -> None:
        from utils.date_utils import is_business_day
        saturday = date(2024, 12, 28)  # Saturday
        sunday = date(2024, 12, 29)    # Sunday
        assert is_business_day(saturday) is False
        assert is_business_day(sunday) is False

    def test_date_range_length(self) -> None:
        from utils.date_utils import date_range
        result = date_range(date(2024, 1, 1), date(2024, 1, 7))
        assert len(result) == 7

    def test_date_range_invalid(self) -> None:
        from utils.date_utils import date_range
        with pytest.raises(ValueError):
            date_range(date(2024, 1, 7), date(2024, 1, 1))


# ---------------------------------------------------------------------------
# File utils tests
# ---------------------------------------------------------------------------

class TestFileUtils:
    """Verify file utility functions."""

    def test_ensure_dir_creates_directory(self, tmp_path: Path) -> None:
        from utils.file_utils import ensure_dir
        new_dir = tmp_path / "nested" / "directory"
        result = ensure_dir(new_dir)
        assert result.is_dir()

    def test_save_and_load_json(self, tmp_path: Path) -> None:
        from utils.file_utils import save_json, load_json
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        dest = tmp_path / "test.json"
        save_json(data, dest)
        loaded = load_json(dest)
        assert loaded == data

    def test_load_json_missing_file(self, tmp_path: Path) -> None:
        from utils.file_utils import load_json
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "nonexistent.json")

    def test_save_csv_and_iter(self, tmp_path: Path) -> None:
        from utils.file_utils import save_csv, iter_csv
        rows = [{"name": "Infosys", "sector": "IT"}, {"name": "HDFC", "sector": "Banking"}]
        dest = tmp_path / "test.csv"
        save_csv(rows, dest)
        loaded = list(iter_csv(dest))
        assert len(loaded) == 2
        assert loaded[0]["name"] == "Infosys"

    def test_file_exists(self, tmp_path: Path) -> None:
        from utils.file_utils import file_exists
        f = tmp_path / "file.txt"
        assert not file_exists(f)
        f.write_text("hello")
        assert file_exists(f)
