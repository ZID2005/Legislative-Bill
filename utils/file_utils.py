"""
utils/file_utils.py
===================
File I/O helper utilities.

Provides thin wrappers around common file operations so that the rest of
the codebase:

*  Never hard-codes path construction (use ``pathlib.Path``).
*  Always creates parent directories before writing.
*  Has consistent error handling for missing files.
*  Uses atomic writes where possible to prevent data corruption.

All functions accept both ``str`` and ``pathlib.Path`` arguments via the
``PathLike`` type alias.
"""

from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterator

from config.logging_config import get_logger

logger = get_logger(__name__)

# Type alias for path-like arguments
PathLike = str | os.PathLike


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------


def ensure_dir(path: PathLike) -> Path:
    """
    Create *path* (and all intermediate parents) if it does not exist.

    Parameters
    ----------
    path : PathLike
        Directory path to create.

    Returns
    -------
    Path
        The resolved, now-existing directory path.
    """
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    logger.debug("Directory ensured: %s", p)
    return p


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------


def save_json(data: Any, path: PathLike, indent: int = 2) -> Path:
    """
    Serialise *data* to a JSON file at *path*.

    Uses an atomic write pattern: data is first written to a temporary file
    in the same directory, then renamed, to avoid leaving a corrupt file on
    disk if the process is interrupted.

    Parameters
    ----------
    data : Any
        JSON-serialisable Python object.
    path : PathLike
        Destination file path (including ``.json`` extension).
    indent : int
        JSON indentation level for human-readable output.

    Returns
    -------
    Path
        Resolved path to the written file.
    """
    dest = Path(path).resolve()
    ensure_dir(dest.parent)

    # Atomic write via temp file
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=dest.parent,
        prefix=f".{dest.stem}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        shutil.move(tmp_path, dest)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    logger.debug("JSON saved: %s", dest)
    return dest


def load_json(path: PathLike) -> Any:
    """
    Deserialise a JSON file and return the Python object.

    Parameters
    ----------
    path : PathLike
        Path to the ``.json`` file.

    Returns
    -------
    Any
        Deserialised Python object.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    json.JSONDecodeError
        If the file is not valid JSON.
    """
    src = Path(path).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"JSON file not found: {src}")
    with src.open("r", encoding="utf-8") as f:
        data = json.load(f)
    logger.debug("JSON loaded: %s", src)
    return data


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def save_csv(
    rows: list[dict[str, Any]],
    path: PathLike,
    fieldnames: list[str] | None = None,
) -> Path:
    """
    Write a list of dicts to a CSV file.

    Parameters
    ----------
    rows : list[dict[str, Any]]
        Data rows; each dict must have the same keys.
    path : PathLike
        Destination file path.
    fieldnames : list[str] | None
        Column order.  If ``None``, keys of the first row are used.

    Returns
    -------
    Path
        Resolved path to the written file.
    """
    dest = Path(path).resolve()
    ensure_dir(dest.parent)
    if not rows:
        logger.warning("save_csv called with empty rows; writing header only to %s", dest)
    _fieldnames = fieldnames or (list(rows[0].keys()) if rows else [])
    with dest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    logger.debug("CSV saved: %s (%d rows)", dest, len(rows))
    return dest


def iter_csv(path: PathLike) -> Iterator[dict[str, str]]:
    """
    Lazily iterate over rows of a CSV file as dicts.

    Parameters
    ----------
    path : PathLike
        Path to the CSV file.

    Yields
    ------
    dict[str, str]
        One row per iteration.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    src = Path(path).resolve()
    if not src.is_file():
        raise FileNotFoundError(f"CSV file not found: {src}")
    with src.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def file_exists(path: PathLike) -> bool:
    """Return ``True`` if *path* points to an existing file."""
    return Path(path).is_file()


def list_files(directory: PathLike, pattern: str = "*") -> list[Path]:
    """
    Return a sorted list of files matching *pattern* inside *directory*.

    Parameters
    ----------
    directory : PathLike
        Directory to search (non-recursive).
    pattern : str
        Glob pattern, e.g. ``'*.pdf'`` or ``'bill_*.json'``.

    Returns
    -------
    list[Path]
        Sorted list of matching file paths.
    """
    d = Path(directory)
    if not d.is_dir():
        raise NotADirectoryError(f"Not a directory: {d}")
    return sorted(d.glob(pattern))
