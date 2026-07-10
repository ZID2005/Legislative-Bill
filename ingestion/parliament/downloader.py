"""
ingestion/parliament/downloader.py
==================================
Service for downloading bill PDF documents and extracting text.

Saves PDFs to data/bills/pdfs/ and extracts plain text using pdfplumber/PyPDF2.
"""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path
from typing import Any, Optional

import httpx

from config.logging_config import get_logger
from ingestion.parliament.exceptions import PDFDownloadError
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
        Preserves backward compatibility with legacy signature.
        """
        dest_path = self._pdfs_dir / f"{bill_id}.pdf"
        success, msg, _, _ = await self.download_document(document_url, dest_path, connector)
        if not success:
            raise PDFDownloadError(f"Failed to download PDF: {msg}")
        return str(dest_path.resolve())

    async def download_document(
        self,
        document_url: str,
        dest_path: Path,
        connector: Any,
    ) -> tuple[bool, str, int, Optional[str]]:
        """
        Downloads a legislative document safely using streaming chunks.
        Supports resuming partial downloads and respects politeness policies.

        Returns
        -------
        tuple[bool, str, int, str | None]
            (success, status_message, file_size, sha256_checksum)
        """
        # 1. robots.txt check
        if hasattr(connector, "_check_robots") and not connector._check_robots(document_url):
            return False, f"Blocked by robots.txt: {document_url}", 0, None

        # 2. Mock mode handling
        if hasattr(connector, "mock_responses") and document_url in connector.mock_responses:
            logger.info("Serving mock response for URL: %s", document_url)
            mock_data = connector.mock_responses[document_url]
            mock_bytes = mock_data.encode("utf-8") if isinstance(mock_data, str) else mock_data
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(mock_bytes)

            sha256 = hashlib.sha256(mock_bytes).hexdigest()
            return True, "Mock download successful", len(mock_bytes), sha256

        # 3. Retry loop with exponential backoff
        retries = 0
        max_retries = getattr(connector, "max_retries", 3)
        delay = getattr(connector, "delay", 1.5)
        backoff_factor = getattr(connector, "backoff_factor", 2.0)
        timeout = getattr(connector, "timeout", 30)
        current_delay = delay

        while True:
            try:
                # Determine if range request is possible
                start_byte = 0
                attempt_range = False
                if dest_path.is_file():
                    start_byte = dest_path.stat().st_size
                    if start_byte > 0:
                        attempt_range = True

                headers = {"User-Agent": connector.user_agent}
                if attempt_range:
                    headers["Range"] = f"bytes={start_byte}-"
                    mode = "ab"
                    logger.info(
                        "Attempting to resume download for URL: %s starting from byte %d",
                        document_url,
                        start_byte,
                    )
                else:
                    mode = "wb"
                    start_byte = 0

                # Politeness delay enforcement
                if hasattr(connector, "_enforce_delay"):
                    await connector._enforce_delay()

                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    async with client.stream("GET", document_url, headers=headers) as response:
                        if response.status_code == 416 and attempt_range:
                            logger.warning(
                                "Range request 416 Not Satisfiable. Restarting fresh download."
                            )
                            attempt_range = False
                            start_byte = 0
                            mode = "wb"
                            # Re-request fresh
                            headers.pop("Range", None)
                            async with client.stream(
                                "GET", document_url, headers=headers
                            ) as fresh_resp:
                                fresh_resp.raise_for_status()
                                return await self._stream_to_file(fresh_resp, dest_path, mode)
                        elif response.status_code == 206:
                            logger.info(
                                "Resuming file download (206 Partial Content) for: %s",
                                dest_path.name,
                            )
                        elif response.status_code == 200:
                            if start_byte > 0:
                                logger.info("Server ignored Range request. Overwriting file.")
                                mode = "wb"
                                start_byte = 0
                        else:
                            response.raise_for_status()

                        return await self._stream_to_file(response, dest_path, mode)

            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
                retries += 1
                if retries >= max_retries:
                    logger.error("Download failed after %d attempts: %s", retries, e)
                    return False, f"Failed after {retries} attempts: {str(e)}", 0, None

                logger.warning(
                    "Error downloading %s. Retrying in %.2f seconds (attempt %d/%d). Error: %s",
                    document_url,
                    current_delay,
                    retries,
                    max_retries,
                    e,
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor

    async def _stream_to_file(
        self, response: httpx.Response, dest_path: Path, mode: str
    ) -> tuple[bool, str, int, str]:
        """Helper to stream response body to file and calculate checksum."""
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with dest_path.open(mode) as f:
            async for chunk in response.aiter_bytes(chunk_size=8192):
                f.write(chunk)

        # Compute SHA-256 checksum of the completed file
        sha256 = hashlib.sha256()
        with dest_path.open("rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)

        checksum = sha256.hexdigest()
        size = dest_path.stat().st_size
        mime = response.headers.get("content-type", "application/pdf")
        return True, f"Success (MIME: {mime})", size, checksum

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
            logger.warning(
                "pdfplumber extraction failed on %s: %s. Falling back to PyPDF2.", pdf_path, e
            )

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
                raise PDFDownloadError(
                    f"All PDF text extraction libraries failed for {pdf_path}: {e}"
                ) from e

        # Clean the extracted text using text_utils
        cleaned = clean_text(extracted_text)
        logger.info("Successfully extracted %d characters of text from %s", len(cleaned), pdf_path)
        return cleaned
