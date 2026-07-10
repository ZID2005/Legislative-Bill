"""
ingestion/parliament/extractor.py
==================================
Legislative Text Extraction Engine — Task 1A.4

Converts downloaded legislative PDF documents into clean, structured text
forming the legislative corpus.  This module is purely deterministic — no
NLP, no AI, no OCR.

Extraction pipeline per document
---------------------------------
1.  Validate PDF file exists and is not corrupt.
2.  Attempt page-by-page extraction with **pdfplumber** (primary).
    -  Tables are rendered as readable, tab-delimited text.
    -  Page order is preserved.
    -  Empty pages are counted.
3.  Fall back to **PyPDF2** if pdfplumber yields < 50 characters total.
4.  If both extractors return < 50 characters, mark as ``SCANNED_PDF``
    (OCR may be needed in a future task).
5.  Apply Unicode NFKC normalisation.
6.  Preserve paragraph spacing (blank line between pages).
7.  Remove repeated headers / footers confidently detected on > 50 % of pages.
8.  Preserve section numbering and table structure.
9.  Write corpus file to ``data/bills/corpus/{year}/{bill_id}.txt``.
10. Compute quality metrics.

Checksum-based skip logic
--------------------------
If ``bill.document_checksum`` (SHA-256 of the PDF, set by Task 1A.3) has
not changed since the last extraction run, the extraction is skipped and
the existing corpus file is reused.  This enables idempotent incremental
synchronisation.

Scanned PDF detection
----------------------
A PDF is considered scanned if the total extracted character count from ALL
pages is < 50 characters.  ``text_status`` is set to ``scanned_pdf`` and
``extracted_text`` is left empty.  OCR is explicitly out of scope.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.logging_config import get_logger
from config.settings import settings
from utils.file_utils import ensure_dir

try:
    import pdfplumber  # noqa: F401

    _HAS_PDFPLUMBER = True
except ImportError:  # pragma: no cover
    _HAS_PDFPLUMBER = False

try:
    import PyPDF2  # noqa: F401

    _HAS_PYPDF2 = True
except ImportError:  # pragma: no cover
    _HAS_PYPDF2 = False

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Minimum total character count across ALL pages before a PDF is considered
#: to be a scanned/image-only document and is flagged for OCR.
_SCANNED_THRESHOLD_CHARS: int = 50

#: Fraction of pages a line must appear on to be considered a repeating
#: header or footer and removed.
_HEADER_FOOTER_FREQ_THRESHOLD: float = 0.50

#: Maximum characters in a potential header/footer line (longer lines are
#: unlikely to be headers/footers).
_HEADER_FOOTER_MAX_CHARS: int = 120

#: Chunk size for file I/O operations.
_IO_CHUNK_SIZE: int = 8192


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ExtractionResult:
    """
    Carries all outputs and quality metadata produced by one extraction run.

    Attributes
    ----------
    bill_id : str
        Unique bill identifier.
    text_status : str
        One of: ``success``, ``scanned_pdf``, ``failed``, ``missing_pdf``,
        ``empty``.
    extraction_method : str
        Library used: ``pdfplumber``, ``pypdf2``, or ``none``.
    extracted_text : str
        The cleaned, normalised corpus text.  Empty on non-success.
    page_count : int
        Number of pages in the PDF.
    char_count : int
        Character count of ``extracted_text``.
    word_count : int
        Word count of ``extracted_text``.
    avg_chars_per_page : float
        ``char_count / page_count`` (0.0 if page_count == 0).
    empty_page_count : int
        Number of pages that yielded no text at all.
    extraction_timestamp : str
        ISO-8601 UTC timestamp of this extraction run.
    text_path : Optional[str]
        Absolute local path to the written corpus ``.txt`` file.
    text_checksum : Optional[str]
        SHA-256 hex digest of the written ``.txt`` file.
    text_size : Optional[int]
        Byte size of the written ``.txt`` file.
    errors : list[str]
        Validation errors accumulated during extraction.
    warnings : list[str]
        Non-blocking warnings accumulated during extraction.
    """

    bill_id: str
    text_status: str
    extraction_method: str
    extracted_text: str
    page_count: int
    char_count: int
    word_count: int
    avg_chars_per_page: float
    empty_page_count: int
    extraction_timestamp: str
    text_path: Optional[str] = None
    text_checksum: Optional[str] = None
    text_size: Optional[int] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def quality_metrics(self) -> dict:
        """Return quality metrics as a JSON-serialisable dictionary."""
        return {
            "char_count": self.char_count,
            "word_count": self.word_count,
            "avg_chars_per_page": round(self.avg_chars_per_page, 2),
            "empty_page_count": self.empty_page_count,
            "extraction_success": self.text_status == "success",
        }


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------


class LegislativeTextExtractor:
    """
    Extracts and cleans text from downloaded legislative PDFs.

    Parameters
    ----------
    corpus_dir : Path | None
        Root directory for writing corpus ``.txt`` files.
        Defaults to ``settings.BILLS_DIR / "corpus"``.
    """

    def __init__(self, corpus_dir: Optional[Path] = None) -> None:
        if corpus_dir is None:
            self._corpus_dir = settings.BILLS_DIR / "corpus"
        else:
            self._corpus_dir = corpus_dir
        ensure_dir(self._corpus_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self,
        bill_id: str,
        pdf_path: Optional[str],
        year: Optional[int],
        document_checksum: Optional[str] = None,
        existing_text_checksum: Optional[str] = None,
        existing_text_path: Optional[str] = None,
        dry_run: bool = False,
    ) -> ExtractionResult:
        """
        Extract text from the PDF for *bill_id* and write the corpus file.

        Parameters
        ----------
        bill_id : str
        pdf_path : Optional[str]
            Absolute path to the downloaded PDF.
        year : Optional[int]
            Publication year, used to organise the output directory.
        document_checksum : Optional[str]
            SHA-256 of the PDF (from Task 1A.3).  Used for skip detection.
        existing_text_checksum : Optional[str]
            SHA-256 of the previously extracted text.  If equal to the
            stored corpus checksum, extraction can be skipped.
        existing_text_path : Optional[str]
            Path to the previously written corpus file.
        dry_run : bool
            When True, nothing is written to disk; metrics are still computed.

        Returns
        -------
        ExtractionResult
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # 1. Missing PDF ---------------------------------------------------
        if not pdf_path:
            logger.warning("Bill %s has no pdf_path recorded. Skipping.", bill_id)
            return ExtractionResult(
                bill_id=bill_id,
                text_status="missing_pdf",
                extraction_method="none",
                extracted_text="",
                page_count=0,
                char_count=0,
                word_count=0,
                avg_chars_per_page=0.0,
                empty_page_count=0,
                extraction_timestamp=timestamp,
                errors=["pdf_path is not set for this bill"],
            )

        pdf = Path(pdf_path)
        if not pdf.is_file():
            logger.warning("PDF file not found for bill %s: %s", bill_id, pdf_path)
            return ExtractionResult(
                bill_id=bill_id,
                text_status="missing_pdf",
                extraction_method="none",
                extracted_text="",
                page_count=0,
                char_count=0,
                word_count=0,
                avg_chars_per_page=0.0,
                empty_page_count=0,
                extraction_timestamp=timestamp,
                errors=[f"PDF file does not exist: {pdf_path}"],
            )

        # 2. Checksum-based skip logic -------------------------------------
        if self._can_skip(document_checksum, existing_text_checksum, existing_text_path):
            logger.info(
                "Skipping extraction for %s - PDF unchanged, corpus exists.",
                bill_id,
            )
            ep = Path(existing_text_path)  # type: ignore[arg-type]
            size = ep.stat().st_size if ep.is_file() else None
            text = ep.read_text(encoding="utf-8", errors="replace") if ep.is_file() else ""
            return ExtractionResult(
                bill_id=bill_id,
                text_status="success",
                extraction_method="skipped",
                extracted_text=text,
                page_count=0,
                char_count=len(text),
                word_count=len(text.split()),
                avg_chars_per_page=0.0,
                empty_page_count=0,
                extraction_timestamp=timestamp,
                text_path=existing_text_path,
                text_checksum=existing_text_checksum,
                text_size=size,
                warnings=["Extraction skipped — PDF checksum unchanged"],
            )

        # 3. PDF corruption check ------------------------------------------
        try:
            self._validate_pdf_header(pdf)
        except ValueError as exc:
            logger.error("Corrupted PDF for bill %s: %s", bill_id, exc)
            return ExtractionResult(
                bill_id=bill_id,
                text_status="failed",
                extraction_method="none",
                extracted_text="",
                page_count=0,
                char_count=0,
                word_count=0,
                avg_chars_per_page=0.0,
                empty_page_count=0,
                extraction_timestamp=timestamp,
                errors=[str(exc)],
            )

        # 4. Multi-page extraction (pdfplumber, PyPDF2 fallback) -----------
        pages_text, page_count, empty_page_count, method = self._extract_pages(pdf)
        total_raw_chars = sum(len(t) for t in pages_text)

        # 5. Scanned PDF detection -----------------------------------------
        if total_raw_chars < _SCANNED_THRESHOLD_CHARS:
            logger.warning(
                "Bill %s appears to be a scanned PDF (%d chars extracted). "
                "OCR may be required in a future version.",
                bill_id,
                total_raw_chars,
            )
            return ExtractionResult(
                bill_id=bill_id,
                text_status="scanned_pdf",
                extraction_method=method,
                extracted_text="",
                page_count=page_count,
                char_count=0,
                word_count=0,
                avg_chars_per_page=0.0,
                empty_page_count=empty_page_count,
                extraction_timestamp=timestamp,
                warnings=["Scanned PDF detected. OCR required in a future version."],
            )

        # 6. Post-processing -----------------------------------------------
        cleaned_pages = [self._clean_page_text(t) for t in pages_text]
        cleaned_pages = self._remove_repeated_headers_footers(cleaned_pages)

        # Join pages with double newline to preserve paragraph spacing
        full_text = "\n\n".join(p for p in cleaned_pages if p.strip())

        if not full_text.strip():
            return ExtractionResult(
                bill_id=bill_id,
                text_status="empty",
                extraction_method=method,
                extracted_text="",
                page_count=page_count,
                char_count=0,
                word_count=0,
                avg_chars_per_page=0.0,
                empty_page_count=empty_page_count,
                extraction_timestamp=timestamp,
                warnings=["Extraction produced empty text after cleaning."],
            )

        # 7. Quality metrics -----------------------------------------------
        char_count = len(full_text)
        word_count = len(full_text.split())
        avg_chars = char_count / page_count if page_count > 0 else 0.0

        # 8. Write corpus file ---------------------------------------------
        year_folder = str(year) if year else "unknown"
        dest_dir = self._corpus_dir / year_folder
        ensure_dir(dest_dir)
        dest_path = dest_dir / f"{bill_id}.txt"

        text_path: Optional[str] = None
        text_checksum: Optional[str] = None
        text_size: Optional[int] = None

        if not dry_run:
            dest_path.write_text(full_text, encoding="utf-8")
            text_path = str(dest_path.resolve())
            text_checksum = document_checksum or self._sha256_file(pdf)
            text_size = dest_path.stat().st_size
            logger.info(
                "Corpus written for bill %s | method=%s | chars=%d | "
                "words=%d | pages=%d | path=%s",
                bill_id,
                method,
                char_count,
                word_count,
                page_count,
                dest_path.name,
            )
        else:
            logger.info(
                "[Dry Run] Would write corpus for bill %s | chars=%d | " "words=%d",
                bill_id,
                char_count,
                word_count,
            )

        return ExtractionResult(
            bill_id=bill_id,
            text_status="success",
            extraction_method=method,
            extracted_text=full_text,
            page_count=page_count,
            char_count=char_count,
            word_count=word_count,
            avg_chars_per_page=avg_chars,
            empty_page_count=empty_page_count,
            extraction_timestamp=timestamp,
            text_path=text_path,
            text_checksum=text_checksum,
            text_size=text_size,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _can_skip(
        self,
        doc_checksum: Optional[str],
        text_checksum: Optional[str],
        text_path: Optional[str],
    ) -> bool:
        """
        Return True if the PDF is unchanged and a valid corpus file exists.

        Skip conditions (all must be true):
        -  ``doc_checksum`` matches ``text_checksum`` (same PDF content)
        -  ``text_path`` is set and the file exists
        """
        if not doc_checksum or not text_checksum or not text_path:
            return False
        if doc_checksum != text_checksum:
            # Different checksums → PDF changed → must re-extract
            return False
        return Path(text_path).is_file()

    def _validate_pdf_header(self, pdf: Path) -> None:
        """
        Raise ValueError if the file does not start with the PDF magic bytes.
        """
        with pdf.open("rb") as f:
            header = f.read(4)
        if header != b"%PDF":
            raise ValueError(
                f"Invalid PDF signature for {pdf.name}: expected %PDF, " f"got {header!r}"
            )

    def _extract_pages(self, pdf: Path) -> tuple[list[str], int, int, str]:
        """
        Extract text from every page, returning (pages_text, page_count,
        empty_page_count, method).

        Tries pdfplumber first; falls back to PyPDF2 if the total extracted
        text is below the scanned threshold.
        """
        pages_text, page_count, empty_page_count = self._extract_pdfplumber(pdf)
        total = sum(len(t) for t in pages_text)

        if total >= _SCANNED_THRESHOLD_CHARS:
            return pages_text, page_count, empty_page_count, "pdfplumber"

        # Fallback
        logger.info(
            "pdfplumber yielded only %d chars for %s. Trying PyPDF2.",
            total,
            pdf.name,
        )
        fb_pages, fb_count, fb_empty = self._extract_pypdf2(pdf)
        if sum(len(t) for t in fb_pages) > total:
            return fb_pages, fb_count, fb_empty, "pypdf2"

        # Return pdfplumber result even if sparse (caller detects scanned)
        return pages_text, page_count, empty_page_count, "pdfplumber"

    def _extract_pdfplumber(self, pdf: Path) -> tuple[list[str], int, int]:
        """
        Extract using pdfplumber; return (pages_text, page_count, empty_count).
        """
        if not _HAS_PDFPLUMBER:
            logger.debug("pdfplumber not installed.")
            return [], 0, 0

        pages_text: list[str] = []
        empty_count = 0
        try:
            with pdfplumber.open(pdf) as doc:
                page_count = len(doc.pages)
                for page in doc.pages:
                    parts: list[str] = []

                    # Plain text extraction
                    raw = page.extract_text(x_tolerance=3, y_tolerance=3)
                    if raw:
                        parts.append(raw)

                    # Table extraction — render as tab-separated rows
                    tables = page.extract_tables()
                    for table in tables or []:
                        rows = []
                        for row in table:
                            cells = "\t".join(
                                str(cell).strip() if cell is not None else "" for cell in row
                            )
                            rows.append(cells)
                        if rows:
                            parts.append("\n".join(rows))

                    page_text = "\n".join(parts).strip()
                    pages_text.append(page_text)
                    if not page_text:
                        empty_count += 1

            return pages_text, page_count, empty_count

        except Exception as exc:  # noqa: BLE001
            logger.warning("pdfplumber extraction error on %s: %s", pdf.name, exc)
            return [], 0, 0

    def _extract_pypdf2(self, pdf: Path) -> tuple[list[str], int, int]:
        """
        Extract using PyPDF2; return (pages_text, page_count, empty_count).
        """
        if not _HAS_PYPDF2:
            logger.debug("PyPDF2 not installed.")
            return [], 0, 0

        pages_text: list[str] = []
        empty_count = 0
        try:
            with pdf.open("rb") as f:
                reader = PyPDF2.PdfReader(f)
                page_count = len(reader.pages)
                for page in reader.pages:
                    try:
                        raw = page.extract_text() or ""
                    except Exception as page_exc:  # noqa: BLE001
                        logger.debug("PyPDF2 page error on %s: %s", pdf.name, page_exc)
                        raw = ""
                    pages_text.append(raw.strip())
                    if not raw.strip():
                        empty_count += 1
            return pages_text, page_count, empty_count

        except Exception as exc:  # noqa: BLE001
            logger.warning("PyPDF2 extraction error on %s: %s", pdf.name, exc)
            return [], 0, 0

    def _clean_page_text(self, text: str) -> str:
        """
        Apply Unicode NFKC normalisation, whitespace cleanup, and
        page-number stripping to a single page's text.

        Paragraph breaks (blank lines) are preserved.
        """
        if not text:
            return ""

        # Unicode normalisation
        text = unicodedata.normalize("NFKC", text)

        # Remove null bytes and non-printable control characters
        # (keep newlines and tabs for structure)
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\t")

        # Collapse runs of spaces / tabs on a single line (not newlines)
        lines = text.split("\n")
        cleaned_lines: list[str] = []
        for line in lines:
            line = re.sub(r"[ \t]+", " ", line).rstrip()
            cleaned_lines.append(line)

        # Remove lines that are purely a page number
        cleaned_lines = [
            ln
            for ln in cleaned_lines
            if not re.fullmatch(r"\s*[-–]?\s*\d+\s*[-–]?\s*", ln)
            and not re.fullmatch(r"\s*page\s+\d+(\s+of\s+\d+)?\s*", ln, re.IGNORECASE)
        ]

        # Collapse 3+ consecutive blank lines to 2 (preserve paragraph breaks)
        result_lines: list[str] = []
        blank_count = 0
        for ln in cleaned_lines:
            if not ln.strip():
                blank_count += 1
                if blank_count <= 2:
                    result_lines.append("")
            else:
                blank_count = 0
                result_lines.append(ln)

        return "\n".join(result_lines).strip()

    def _remove_repeated_headers_footers(self, pages: list[str]) -> list[str]:
        """
        Detect lines that appear on more than *_HEADER_FOOTER_FREQ_THRESHOLD*
        of all pages (and are short enough to be headers/footers) and remove
        them from every page.

        Only confident matches are removed; long lines or lines containing
        section numbers are left in place.
        """
        if len(pages) < 3:
            # Not enough pages to reliably detect repeating elements
            return pages

        # Collect short lines from each page
        line_page_sets: dict[str, set[int]] = {}
        for page_idx, page_text in enumerate(pages):
            seen_on_this_page: set[str] = set()
            for ln in page_text.split("\n"):
                stripped = ln.strip()
                if not stripped:
                    continue
                if len(stripped) > _HEADER_FOOTER_MAX_CHARS:
                    continue
                # Exclude lines that look like section headings (contain digits
                # that could be section numbers like "1.", "2.1", etc.)
                if re.match(r"^\d+(\.\d+)*\.", stripped):
                    continue
                if stripped not in seen_on_this_page:
                    seen_on_this_page.add(stripped)
                    line_page_sets.setdefault(stripped, set()).add(page_idx)

        # Identify repeating lines above threshold
        total_pages = len(pages)
        threshold = max(3, int(total_pages * _HEADER_FOOTER_FREQ_THRESHOLD))
        repeating = {ln for ln, page_set in line_page_sets.items() if len(page_set) >= threshold}

        if repeating:
            logger.info(
                "Removing %d repeating header/footer lines across %d pages.",
                len(repeating),
                total_pages,
            )

        # Strip repeating lines from every page
        cleaned_pages: list[str] = []
        for page_text in pages:
            new_lines = [ln for ln in page_text.split("\n") if ln.strip() not in repeating]
            cleaned_pages.append("\n".join(new_lines))

        return cleaned_pages

    @staticmethod
    def _sha256_file(path: Path) -> str:
        """Compute the SHA-256 hex digest of a file."""
        sha256 = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(_IO_CHUNK_SIZE):
                sha256.update(chunk)
        return sha256.hexdigest()
