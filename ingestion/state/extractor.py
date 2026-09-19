"""
ingestion/state/extractor.py
============================
State legislative bill PDF text extraction engine.

Extracts text from downloaded State legislative PDF documents into plain-text
corpus files stored in `data/state_bills/corpus/`.
Handles bilingual documents (English, Kannada, Telugu), normalizes Unicode,
detects scanned PDFs (flagging OCR_REQUIRED without hallucinating missing text),
computes text quality metrics, and maintains complete isolation from Central data.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from schemas.bill import Bill
from utils.file_utils import ensure_dir
from utils.language_utils import detect_language

logger = get_logger(__name__)

_SCANNED_THRESHOLD_CHARS: int = 50
_HEADER_FOOTER_FREQ_THRESHOLD: float = 0.50
_HEADER_FOOTER_MAX_CHARS: int = 120


@dataclass
class StateExtractionResult:
    """Carries outputs and quality metrics produced by one State extraction run."""

    bill_id: str
    text_status: str  # "success" | "ocr_required" | "missing_pdf" | "failed" | "empty"
    extraction_method: str  # "pdfplumber" | "pypdf2" | "none"
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
    detected_language: str = "English"
    is_multilingual: bool = False
    languages_detected: list[str] = field(default_factory=lambda: ["English"])
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def quality_metrics(self) -> dict[str, Any]:
        return {
            "char_count": self.char_count,
            "word_count": self.word_count,
            "avg_chars_per_page": round(self.avg_chars_per_page, 2),
            "empty_page_count": self.empty_page_count,
            "page_count": self.page_count,
            "extraction_success": self.text_status == "success",
            "ocr_required": self.text_status == "ocr_required",
            "detected_language": self.detected_language,
            "is_multilingual": self.is_multilingual,
        }


class StateTextExtractor:
    """
    Extracts, normalizes, and packages text from State legislative bill PDFs.
    """

    def __init__(self, corpus_dir: Optional[Path] = None) -> None:
        """
        Initialize the State text extractor.

        Parameters
        ----------
        corpus_dir : Path | None
            Directory to store extracted .txt files. Defaults to settings.STATE_BILLS_DIR / "corpus".
        """
        if corpus_dir is None:
            self._corpus_dir = settings.STATE_BILLS_DIR / "corpus"
        else:
            self._corpus_dir = Path(corpus_dir)

        ensure_dir(self._corpus_dir)

    @property
    def corpus_dir(self) -> Path:
        return self._corpus_dir

    def extract_from_pdf(
        self,
        pdf_path: Path,
        bill_id: str,
        force: bool = False,
    ) -> StateExtractionResult:
        """
        Extract text from a State PDF file.

        Parameters
        ----------
        pdf_path : Path
            Path to the local PDF file.
        bill_id : str
            Identifier of the bill.
        force : bool
            Whether to overwrite an existing corpus file.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        out_path = self._corpus_dir / f"{bill_id}.txt"

        if not pdf_path or not pdf_path.is_file():
            logger.warning("PDF file missing for extraction: %s", pdf_path)
            return StateExtractionResult(
                bill_id=bill_id,
                text_status="missing_pdf",
                extraction_method="none",
                extracted_text="",
                page_count=0,
                char_count=0,
                word_count=0,
                avg_chars_per_page=0.0,
                empty_page_count=0,
                extraction_timestamp=now_iso,
                errors=[f"PDF file does not exist: {pdf_path}"],
            )

        # Idempotent check
        if not force and out_path.is_file() and out_path.stat().st_size > 0:
            content = out_path.read_text(encoding="utf-8")
            checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
            size = out_path.stat().st_size
            words = len(content.split())
            lang_info = detect_language(content)
            logger.info("Using cached State corpus text: %s", out_path.name)
            return StateExtractionResult(
                bill_id=bill_id,
                text_status="success",
                extraction_method="cached",
                extracted_text=content,
                page_count=1,
                char_count=len(content),
                word_count=words,
                avg_chars_per_page=float(len(content)),
                empty_page_count=0,
                extraction_timestamp=now_iso,
                text_path=str(out_path.resolve()),
                text_checksum=checksum,
                text_size=size,
                detected_language=lang_info["primary_language"],
                is_multilingual=lang_info["is_multilingual"],
                languages_detected=lang_info["languages_detected"],
            )

        raw_pages: list[str] = []
        method = "none"
        errors: list[str] = []
        warnings: list[str] = []

        # 1. Try pdfplumber
        try:
            import pdfplumber

            with pdfplumber.open(pdf_path) as pdf:
                for idx, page in enumerate(pdf.pages):
                    try:
                        text = page.extract_text() or ""
                    except Exception as e:
                        warnings.append(f"pdfplumber failed on page {idx}: {e}")
                        text = ""
                    raw_pages.append(text)
            method = "pdfplumber"
        except ImportError:
            logger.debug("pdfplumber not installed; falling back to PyPDF2")
        except Exception as exc:
            warnings.append(f"pdfplumber extraction error: {exc}")

        # 2. Fallback to PyPDF2 if pdfplumber failed or yielded negligible text
        total_preliminary = sum(len(p.strip()) for p in raw_pages)
        if total_preliminary < _SCANNED_THRESHOLD_CHARS:
            try:
                import PyPDF2

                pypdf_pages: list[str] = []
                with pdf_path.open("rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for idx, page in enumerate(reader.pages):
                        try:
                            text = page.extract_text() or ""
                        except Exception as e:
                            warnings.append(f"PyPDF2 failed on page {idx}: {e}")
                            text = ""
                        pypdf_pages.append(text)
                if sum(len(p.strip()) for p in pypdf_pages) > total_preliminary:
                    raw_pages = pypdf_pages
                    method = "pypdf2"
            except Exception as exc:
                warnings.append(f"PyPDF2 extraction error: {exc}")

        page_count = len(raw_pages)
        empty_page_count = sum(1 for p in raw_pages if not p.strip())
        total_extracted_raw = sum(len(p.strip()) for p in raw_pages)

        # 3. Check for scanned / image PDF
        if total_extracted_raw < _SCANNED_THRESHOLD_CHARS:
            logger.info("Flagged State bill as OCR_REQUIRED (< 50 chars extracted): %s", bill_id)
            warnings.append(
                f"Scanned document detected: only {total_extracted_raw} characters extracted. OCR required."
            )
            return StateExtractionResult(
                bill_id=bill_id,
                text_status="ocr_required",
                extraction_method=method if method != "none" else "scanned",
                extracted_text="",
                page_count=page_count,
                char_count=0,
                word_count=0,
                avg_chars_per_page=0.0,
                empty_page_count=empty_page_count,
                extraction_timestamp=now_iso,
                errors=errors,
                warnings=warnings,
            )

        # 4. Clean & Normalize Pages
        normalized_pages: list[str] = []
        for p in raw_pages:
            norm = unicodedata.normalize("NFKC", p)
            norm = norm.replace("\r\n", "\n").replace("\r", "\n")
            norm = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", norm)
            normalized_pages.append(norm)

        # 5. Remove confident repeating headers and footers (>50% pages)
        cleaned_pages = self._remove_headers_footers(normalized_pages)

        # 6. Join pages with page boundary indicator
        full_text = "\n\n".join(p.strip() for p in cleaned_pages if p.strip())
        char_count = len(full_text)
        word_count = len(full_text.split())
        avg_chars = round(char_count / max(1, page_count), 2)

        # 7. Write corpus file
        out_path.write_text(full_text, encoding="utf-8")
        text_bytes = full_text.encode("utf-8")
        checksum = hashlib.sha256(text_bytes).hexdigest()
        size = len(text_bytes)

        logger.info(
            "Extracted State text: %s | pages=%d | chars=%d | method=%s",
            bill_id,
            page_count,
            char_count,
            method,
        )

        lang_info = detect_language(full_text)
        return StateExtractionResult(
            bill_id=bill_id,
            text_status="success",
            extraction_method=method,
            extracted_text=full_text,
            page_count=page_count,
            char_count=char_count,
            word_count=word_count,
            avg_chars_per_page=avg_chars,
            empty_page_count=empty_page_count,
            extraction_timestamp=now_iso,
            text_path=str(out_path.resolve()),
            text_checksum=checksum,
            text_size=size,
            detected_language=lang_info["primary_language"],
            is_multilingual=lang_info["is_multilingual"],
            languages_detected=lang_info["languages_detected"],
            errors=errors,
            warnings=warnings,
        )

    def extract_bill(self, bill: Bill, force: bool = False) -> StateExtractionResult:
        """
        Extract text for a State Bill and update its model fields.
        """
        pdf_path = Path(bill.pdf_path) if bill.pdf_path else (
            settings.STATE_BILLS_DIR / "pdfs" / f"{bill.bill_id}.pdf"
        )
        result = self.extract_from_pdf(pdf_path=pdf_path, bill_id=bill.bill_id, force=force)

        # Update bill record
        bill.text_status = result.text_status
        bill.extraction_method = result.extraction_method
        bill.extraction_timestamp = result.extraction_timestamp
        bill.page_count = result.page_count
        bill.quality_metrics = result.quality_metrics

        if result.text_status == "success":
            bill.text_path = result.text_path
            bill.text_checksum = result.text_checksum
            bill.text_size = result.text_size
            bill.full_text = result.extracted_text
            bill.language = result.detected_language

        return result

    def _remove_headers_footers(self, pages: list[str]) -> list[str]:
        """Detect and remove lines that repeat across > 50% of pages."""
        if len(pages) < 3:
            return pages

        line_page_counts: dict[str, int] = {}
        for p in pages:
            seen_in_page: set[str] = set()
            for line in p.split("\n"):
                s = line.strip()
                if s and len(s) <= _HEADER_FOOTER_MAX_CHARS:
                    # Ignore pure page numbers or tiny numbers
                    if s.isdigit():
                        continue
                    seen_in_page.add(s)
            for s in seen_in_page:
                line_page_counts[s] = line_page_counts.get(s, 0) + 1

        threshold = len(pages) * _HEADER_FOOTER_FREQ_THRESHOLD
        repeating_lines = {l for l, c in line_page_counts.items() if c >= threshold}

        cleaned_pages: list[str] = []
        for p in pages:
            lines = [l for l in p.split("\n") if l.strip() not in repeating_lines]
            cleaned_pages.append("\n".join(lines))

        return cleaned_pages
