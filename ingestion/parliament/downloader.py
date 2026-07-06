"""
ingestion/parliament/downloader.py
==================================
Service for downloading bill PDF documents and extracting text.

Saves PDFs to data/bills/pdfs/ and extracts plain text using pdfplumber/PyPDF2.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from ingestion.parliament.exceptions import PDFDownloadError
from storage.catalog import compute_md5
from utils.file_utils import ensure_dir
from utils.text_utils import clean_text

logger = get_logger(__name__)


class ParliamentDownloader:
    """
    Downloads bill PDF documents and extracts their plain text content.
    """

    def __init__(self, pdfs_dir: Optional[Path] = None) -> None:
        """
        Initialize the downloader.

        Parameters
        ----------
        pdfs_dir : Path | None
            Directory to store PDFs. If None, loaded from settings.
        """
        if pdfs_dir is None:
            from config.settings import settings
            self._pdfs_dir = settings.BILLS_DIR / "pdfs"
        else:
            self._pdfs_dir = pdfs_dir

        ensure_dir(self._pdfs_dir)

    async def download_pdf(
        self,
        document_url: str,
        bill_id: str,
        connector: Any,
    ) -> str:
        """
        Download PDF from document_url and save it.

        Parameters
        ----------
        document_url : str
            The URL to download the PDF from.
        bill_id : str
            The target bill ID.
        connector : ParliamentConnector
            The connector instance to use for fetching.

        Returns
        -------
        str
            The absolute path of the saved PDF.
        """
        try:
            logger.info("Downloading PDF from %s for bill %s", document_url, bill_id)
            pdf_bytes = await connector.fetch(document_url, is_binary=True)

            pdf_path = self._pdfs_dir / f"{bill_id}.pdf"
            pdf_path.write_bytes(pdf_bytes)

            md5_hash = compute_md5(pdf_path)
            logger.info("PDF saved to %s (MD5: %s)", pdf_path, md5_hash)
            return str(pdf_path.resolve())

        except Exception as e:
            logger.error("Failed to download PDF from %s: %s", document_url, e)
            raise PDFDownloadError(f"Failed to download PDF from {document_url}: {e}") from e

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract plain text from a downloaded PDF file.
        Attempts to use pdfplumber, falling back to PyPDF2.

        Parameters
        ----------
        pdf_path : str
            Path to the PDF file.

        Returns
        -------
        str
            The extracted plain text.
        """
        p = Path(pdf_path)
        if not p.is_file():
            raise PDFDownloadError(f"PDF file does not exist: {pdf_path}")

        extracted_text = ""

        # 1. Try pdfplumber
        try:
            import pdfplumber
            logger.debug("Attempting text extraction with pdfplumber: %s", pdf_path)
            with pdfplumber.open(p) as pdf:
                pages_text = []
                for _, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                extracted_text = "\n".join(pages_text)
        except ImportError:
            logger.debug("pdfplumber not installed. Falling back to PyPDF2.")
        except Exception as e:
            logger.warning("pdfplumber extraction failed on %s: %s. Falling back to PyPDF2.", pdf_path, e)

        # 2. Try PyPDF2 fallback if text is still empty
        if not extracted_text.strip():
            try:
                import PyPDF2
                logger.debug("Attempting text extraction with PyPDF2: %s", pdf_path)
                with p.open("rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    pages_text = []
                    for idx in range(len(reader.pages)):
                        page = reader.pages[idx]
                        text = page.extract_text()
                        if text:
                            pages_text.append(text)
                    extracted_text = "\n".join(pages_text)
            except Exception as e:
                logger.error("PyPDF2 extraction failed on %s: %s", pdf_path, e)
                raise PDFDownloadError(f"All PDF text extraction libraries failed for {pdf_path}: {e}") from e

        # Clean the extracted text using text_utils
        cleaned = clean_text(extracted_text)
        logger.info("Successfully extracted %d characters of text from %s", len(cleaned), pdf_path)
        return cleaned
