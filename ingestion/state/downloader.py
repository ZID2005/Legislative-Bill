"""
ingestion/state/downloader.py
=============================
State legislative bill document downloader.

Downloads and caches official State legislative bill documents (PDFs)
into the isolated directory `data/state_bills/pdfs/`.
Computes SHA-256 checksums, enforces politeness, handles retries,
and maintains complete isolation from Central Government production data.
"""

from __future__ import annotations

import asyncio
import hashlib
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import httpx

from config.logging_config import get_logger
from config.settings import settings
from schemas.bill import Bill
from utils.file_utils import ensure_dir

logger = get_logger(__name__)


class StateDocumentDownloader:
    """
    Downloads and caches official State legislative PDF documents.
    """

    def __init__(
        self,
        pdfs_dir: Optional[Path] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        user_agent: Optional[str] = None,
        mock_responses: Optional[dict[str, bytes | str]] = None,
    ) -> None:
        """
        Initialize the State document downloader.

        Parameters
        ----------
        pdfs_dir : Path | None
            Directory to store downloaded PDFs. Defaults to settings.STATE_BILLS_DIR / "pdfs".
        timeout : int
            HTTP request timeout in seconds.
        max_retries : int
            Maximum number of download retry attempts.
        backoff_factor : float
            Exponential backoff factor.
        user_agent : str | None
            Custom User-Agent header string.
        mock_responses : dict[str, bytes | str] | None
            Mapping of document URLs to mock bytes/strings for offline testing.
        """
        if pdfs_dir is None:
            self._pdfs_dir = settings.STATE_BILLS_DIR / "pdfs"
        else:
            self._pdfs_dir = Path(pdfs_dir)

        ensure_dir(self._pdfs_dir)
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36 Legislative-Intelligence-State/1.0"
        )
        self.mock_responses: dict[str, bytes | str] = mock_responses or {}

    @property
    def pdfs_dir(self) -> Path:
        return self._pdfs_dir

    def register_mock(self, url: str, content: bytes | str) -> None:
        """Register a mock response for offline/test execution."""
        self.mock_responses[url] = content

    async def download_document(
        self,
        document_url: str,
        dest_path: Path,
        force: bool = False,
    ) -> tuple[bool, str, int, Optional[str]]:
        """
        Download a document from document_url to dest_path.

        Returns
        -------
        tuple[bool, str, int, Optional[str]]
            (success, message, file_size, sha256_checksum)
        """
        if not document_url:
            return False, "Empty or missing document URL", 0, None

        # 1. Check local cache
        if not force and dest_path.is_file() and dest_path.stat().st_size > 0:
            sha256 = self.compute_sha256(dest_path)
            size = dest_path.stat().st_size
            logger.info("Using cached State PDF: %s (size=%d, sha256=%s)", dest_path.name, size, sha256[:8])
            return True, "Loaded from cache", size, sha256

        # 2. Mock mode handling
        if document_url in self.mock_responses:
            logger.info("Serving mock response for State PDF: %s", document_url)
            mock_data = self.mock_responses[document_url]
            mock_bytes = mock_data.encode("utf-8") if isinstance(mock_data, str) else mock_data
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(mock_bytes)
            sha256 = hashlib.sha256(mock_bytes).hexdigest()
            return True, "Mock download successful", len(mock_bytes), sha256

        # 3. Live streaming download with retries
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/pdf,*/*",
        }
        retries = 0
        current_delay = 1.0

        # State legislature portals often use custom SSL/TLS configurations
        while retries < self.max_retries:
            try:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                async with httpx.AsyncClient(
                    timeout=self.timeout,
                    follow_redirects=True,
                    verify=False,  # Allow state government portals with self-signed / expired chains
                ) as client:
                    async with client.stream("GET", document_url, headers=headers) as response:
                        response.raise_for_status()
                        with dest_path.open("wb") as f:
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                f.write(chunk)

                size = dest_path.stat().st_size
                sha256 = self.compute_sha256(dest_path)
                logger.info(
                    "Successfully downloaded State PDF: %s | size=%d | sha256=%s",
                    dest_path.name,
                    size,
                    sha256[:8],
                )
                return True, "Download successful", size, sha256

            except Exception as exc:
                retries += 1
                logger.warning(
                    "Error downloading State PDF %s (attempt %d/%d): %s",
                    document_url,
                    retries,
                    self.max_retries,
                    exc,
                )
                if retries >= self.max_retries:
                    # Clean up partial file
                    if dest_path.is_file():
                        try:
                            dest_path.unlink()
                        except Exception:
                            pass
                    return False, f"Failed after {retries} attempts: {exc}", 0, None

                await asyncio.sleep(current_delay)
                current_delay *= self.backoff_factor

        return False, "Max retries exceeded", 0, None

    async def download_bill(
        self,
        bill: Bill,
        force: bool = False,
    ) -> tuple[bool, str]:
        """
        Download official PDF for a State Bill and update the bill's metadata fields.

        Parameters
        ----------
        bill : Bill
            The state bill record to update.
        force : bool
            If True, re-download even if already cached.

        Returns
        -------
        tuple[bool, str]
            (success, message)
        """
        if not bill.pdf_url:
            bill.download_status = "missing_url"
            return False, f"Bill {bill.bill_id} has no pdf_url"

        dest_path = self._pdfs_dir / f"{bill.bill_id}.pdf"
        success, msg, size, checksum = await self.download_document(
            document_url=bill.pdf_url,
            dest_path=dest_path,
            force=force,
        )

        now_iso = datetime.now(timezone.utc).isoformat()
        if success:
            bill.pdf_path = str(dest_path.resolve())
            bill.document_path = str(dest_path.resolve())
            bill.document_size = size
            bill.document_checksum = checksum
            bill.download_timestamp = now_iso
            bill.download_status = "success"
        else:
            bill.download_status = "download_failed"
            bill.download_timestamp = now_iso

        return success, msg

    @staticmethod
    def compute_sha256(path: Path) -> str:
        """Compute SHA-256 hex digest of a local file."""
        hasher = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
