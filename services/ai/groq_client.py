"""
services/ai/groq_client.py
==========================
Dedicated Groq Cloud AI inference provider wrapper for India Legislative Intelligence.

Guarantees:
1. Environment-driven configuration (never hardcodes secrets).
2. Never crashes if GROQ_API_KEY is missing (graceful unavailable state).
3. Sanitizes all exceptions to prevent API credential leaks.
4. Provides deterministic failure fallbacks.
5. Easily mockable for test suites without requiring live API calls.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)

_DEFAULT_MODEL = "llama-3.3-70b-versatile"
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_MAX_TOKENS = 1024
_DEFAULT_TEMPERATURE = 0.2

_API_KEY_MASK_PATTERN = re.compile(r"gsk_[a-zA-Z0-9]{20,}", re.IGNORECASE)


@dataclass
class AIResponse:
    """Standardized response container for LLM generation."""

    content: str = ""
    success: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    fallback_message: Optional[str] = None
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def display_text(self) -> str:
        """Return generated content if successful, else safe fallback message."""
        if self.success and self.content:
            return self.content
        return self.fallback_message or "AI explanation is temporarily unavailable."


class GroqClient:
    """
    Dedicated client wrapper for Groq Cloud API.
    Decoupled from application runtime so missing credentials never crash the service.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        client_instance: Optional[Any] = None,
    ) -> None:
        env_key = os.getenv("GROQ_API_KEY")
        self._api_key = (
            api_key
            if api_key is not None
            else (env_key if env_key is not None else getattr(settings, "GROQ_API_KEY", ""))
        ).strip()

        env_model = os.getenv("GROQ_MODEL")
        self._model = (
            model
            if model is not None
            else (env_model if env_model is not None else getattr(settings, "GROQ_MODEL", _DEFAULT_MODEL))
        )

        env_timeout = os.getenv("GROQ_TIMEOUT")
        self._timeout = float(
            timeout
            if timeout is not None
            else (env_timeout if env_timeout is not None else getattr(settings, "GROQ_TIMEOUT", str(_DEFAULT_TIMEOUT)))
        )

        env_max_tok = os.getenv("GROQ_MAX_TOKENS")
        self._max_tokens = int(
            max_tokens
            if max_tokens is not None
            else (env_max_tok if env_max_tok is not None else getattr(settings, "GROQ_MAX_TOKENS", str(_DEFAULT_MAX_TOKENS)))
        )

        env_temp = os.getenv("GROQ_TEMPERATURE")
        self._temperature = float(
            temperature
            if temperature is not None
            else (env_temp if env_temp is not None else getattr(settings, "GROQ_TEMPERATURE", str(_DEFAULT_TEMPERATURE)))
        )

        self._client: Optional[Any] = client_instance

    @property
    def is_available(self) -> bool:
        """Return True if an API key is configured and not a placeholder."""
        if not self._api_key:
            return False
        if self._api_key in {"your_groq_api_key_here", "dummy_key", "none"}:
            return False
        return len(self._api_key) > 5

    @property
    def model(self) -> str:
        return self._model

    @property
    def timeout(self) -> float:
        return self._timeout

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @property
    def temperature(self) -> float:
        return self._temperature

    def _get_underlying_client(self) -> Any:
        """Lazy-initialize groq.Groq client."""
        if self._client is None:
            try:
                import groq
                self._client = groq.Groq(
                    api_key=self._api_key,
                    timeout=self._timeout,
                )
            except ImportError:
                logger.error("groq package not installed.")
                raise RuntimeError("groq library is required for GroqClient.")
        return self._client

    def _sanitize_string(self, text: str) -> str:
        """Remove any potential API key or secret occurrences."""
        if not text:
            return ""
        sanitized = _API_KEY_MASK_PATTERN.sub("[REDACTED_API_KEY]", text)
        if self._api_key and len(self._api_key) > 6:
            sanitized = sanitized.replace(self._api_key, "[REDACTED_API_KEY]")
        return sanitized

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """
        Send a chat completion request to Groq Cloud.

        Parameters
        ----------
        messages : list[dict[str, str]]
            Chat messages formatted as [{"role": "system"|"user"|"assistant", "content": "..."}].
        model : str | None
            Override target model.
        temperature : float | None
            Override sampling temperature.
        max_tokens : int | None
            Override max tokens.

        Returns
        -------
        AIResponse
            Standardized response with content or safe error fallback.
        """
        if not self.is_available:
            return AIResponse(
                content="",
                success=False,
                error_code="API_KEY_MISSING",
                error_message="AI explanation is unavailable because the Groq API key is not configured.",
                fallback_message=(
                    "AI explanation is unavailable because the Groq API key is not configured. "
                    "The verified legislative and analytical information remains available."
                ),
                model=model or self._model,
            )

        active_model = model or self._model
        active_temp = temperature if temperature is not None else self._temperature
        active_max_tok = max_tokens if max_tokens is not None else self._max_tokens

        try:
            client = self._get_underlying_client()
            response = client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=active_temp,
                max_tokens=active_max_tok,
                timeout=self._timeout,
            )

            if not response or not getattr(response, "choices", None):
                return AIResponse(
                    content="",
                    success=False,
                    error_code="EMPTY_RESPONSE",
                    error_message="Groq returned an empty response.",
                    fallback_message="AI explanation is temporarily unavailable (empty provider response).",
                    model=active_model,
                )

            choice = response.choices[0]
            content = getattr(choice.message, "content", "") or ""
            content = content.strip()

            usage = getattr(response, "usage", None)
            ptokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            ctokens = getattr(usage, "completion_tokens", 0) if usage else 0
            ttokens = getattr(usage, "total_tokens", 0) if usage else 0

            return AIResponse(
                content=content,
                success=True,
                model=active_model,
                prompt_tokens=ptokens,
                completion_tokens=ctokens,
                total_tokens=ttokens,
            )

        except Exception as exc:
            raw_err = str(exc)
            sanitized_err = self._sanitize_string(raw_err)
            err_type = type(exc).__name__
            logger.warning("Groq completion failed [%s]: %s", err_type, sanitized_err)

            err_code = "API_ERROR"
            fallback = (
                "AI explanation is temporarily unavailable. "
                "The verified legislative and analytical information remains available."
            )

            if "RateLimit" in err_type or "rate_limit" in sanitized_err.lower():
                err_code = "RATE_LIMIT"
                fallback = "AI explanation is temporarily unavailable due to rate limits. Please retry shortly."
            elif "Timeout" in err_type or "timed out" in sanitized_err.lower():
                err_code = "TIMEOUT"
                fallback = "AI explanation timed out. The verified legislative data remains available."
            elif "Authentication" in err_type or "api_key" in sanitized_err.lower():
                err_code = "AUTHENTICATION_FAILED"
                fallback = "AI explanation is unavailable due to invalid API credentials."

            return AIResponse(
                content="",
                success=False,
                error_code=err_code,
                error_message=sanitized_err,
                fallback_message=fallback,
                model=active_model,
            )
