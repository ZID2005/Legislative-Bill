"""
ingestion/parliament/connector.py
==================================
Polite and resilient HTTP client connector for Parliament ingestion.

Handles rate-limiting, respects robots.txt, processes retries with exponential
backoff, and supports mock mode for offline testing.
"""

from __future__ import annotations

import asyncio
import urllib.parse
from urllib.robotparser import RobotFileParser
from typing import Optional, Union

import httpx

from config.logging_config import get_logger
from ingestion.parliament.exceptions import ConnectorError

logger = get_logger(__name__)


class ParliamentConnector:
    """
    HTTP client wrapper that enforces politeness policies and resilience.
    """

    def __init__(
        self,
        user_agent: str = "LegislativeIntelligenceBot/0.1 (+https://github.com/your-org/legislative-bill)",
        timeout_seconds: int = 30,
        delay_seconds: float = 1.5,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        mock_responses: Optional[dict[str, Union[str, bytes]]] = None,
    ) -> None:
        """
        Initialize the connector.

        Parameters
        ----------
        user_agent : str
            The HTTP User-Agent header value.
        timeout_seconds : int
            HTTP timeout limit in seconds.
        delay_seconds : float
            Mandatory wait delay between successive requests (rate limiting).
        max_retries : int
            Number of retries for failures before giving up.
        backoff_factor : float
            Multiplier applied to delay after each retry attempt.
        mock_responses : dict | None
            A mapping of URL string -> HTML string or PDF bytes for mock mode.
        """
        self.user_agent = user_agent
        self.timeout = timeout_seconds
        self.delay = delay_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.mock_responses = mock_responses or {}

        # Cache RobotFileParser per base domain to avoid re-fetching
        self._robots_parsers: dict[str, RobotFileParser] = {}
        self._last_request_lock = asyncio.Lock()
        self._last_request_time = 0.0

    def register_mock_response(self, url: str, response: Union[str, bytes]) -> None:
        """Register a mock response for offline testing."""
        self.mock_responses[url] = response

    def _get_base_url(self, url: str) -> str:
        """Extract base URL (scheme + netloc) from a full URL."""
        parsed = urllib.parse.urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _check_robots(self, url: str) -> bool:
        """
        Check if robots.txt permits crawling the URL.
        Uses cached robot parsers. Returns True if permitted.
        """
        # If in mock mode, bypass robots.txt fetch
        if self.mock_responses:
            return True

        base_url = self._get_base_url(url)
        if base_url not in self._robots_parsers:
            parser = RobotFileParser()
            parser.set_url(f"{base_url}/robots.txt")
            try:
                # Synchronous read since RobotFileParser is sync
                parser.read()
                self._robots_parsers[base_url] = parser
            except Exception as e:
                logger.warning(
                    "Could not fetch robots.txt for %s: %s. Assuming allowed.", base_url, e
                )
                # Store a dummy parser that allows all
                dummy = RobotFileParser()
                self._robots_parsers[base_url] = dummy

        parser = self._robots_parsers.get(base_url)
        if parser:
            # If robots.txt was missing or empty, parser.can_fetch returns True by default
            return parser.can_fetch(self.user_agent, url)
        return True

    async def _enforce_delay(self) -> None:
        """Enforce request delay to respect host rate limits."""
        if self.mock_responses:
            return  # No delay for mocks

        async with self._last_request_lock:
            loop = asyncio.get_event_loop()
            now = loop.time()
            elapsed = now - self._last_request_time
            if elapsed < self.delay:
                wait_time = self.delay - elapsed
                logger.debug("Enforcing delay of %.2f seconds", wait_time)
                await asyncio.sleep(wait_time)
            self._last_request_time = loop.time()

    async def fetch(self, url: str, is_binary: bool = False) -> Union[str, bytes]:
        """
        Fetch HTML text or binary bytes from the target URL.

        Parameters
        ----------
        url : str
            The URL to fetch.
        is_binary : bool
            True if requesting binary payload (e.g. PDF), False for text.

        Returns
        -------
        str or bytes
            Fetched response body.

        Raises
        ------
        ConnectorError
            If robots.txt blocks access, or HTTP error happens after all retries.
        """
        # 1. Mock mode lookup
        if url in self.mock_responses:
            logger.info("Serving mock response for URL: %s", url)
            return self.mock_responses[url]

        # 2. robots.txt check
        if not self._check_robots(url):
            raise ConnectorError(f"Access to URL blocked by robots.txt: {url}")

        # 3. Delay enforcement
        await self._enforce_delay()

        # 4. Ingest headers
        headers = {"User-Agent": self.user_agent}

        # 5. Retry loop with exponential backoff
        retries = 0
        current_delay = self.delay

        while True:
            try:
                logger.info("Fetching URL: %s (attempt %d/%d)", url, retries + 1, self.max_retries)
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()

                    if is_binary:
                        return response.content
                    else:
                        return response.text

            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as e:
                retries += 1
                if retries >= self.max_retries:
                    logger.error(
                        "Failed to fetch URL %s after %d attempts. Error: %s", url, retries, e
                    )
                    raise ConnectorError(
                        f"Failed to fetch {url} after {self.max_retries} attempts: {e}"
                    ) from e

                logger.warning(
                    "Error fetching %s. Retrying in %.2f seconds (attempt %d/%d). Error: %s",
                    url,
                    current_delay,
                    retries,
                    self.max_retries,
                    e,
                )
                await asyncio.sleep(current_delay)
                current_delay *= self.backoff_factor
