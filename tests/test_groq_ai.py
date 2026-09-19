"""
tests/test_groq_ai.py
=====================
Comprehensive Test Suite for Task 8.10 — Groq AI Intelligence & Explanation Layer.

Verifies:
 1. Missing API key handled safely (no crash, controlled fallback).
 2. Configuration loads correctly from environment.
 3. Central context builder works.
 4. State context builder works.
 5. Facts are separated cleanly.
 6. Derived information is separated.
 7. Predictions are explicitly labeled.
 8. State prediction absence is preserved (explicit "unavailable").
 9. Missing dates cannot be invented by context builder.
10. Company exposure cannot be invented by context builder.
11. Market prediction cannot be invented by context builder.
12. Financial advice detection works (flags buy/sell).
13. Unsupported certainty detection works (flags guarantees).
14. Insider-trading language detection works.
15. Timeout handling works.
16. Rate-limit handling works.
17. Invalid response handling works.
18. Cache invalidates when context hash changes.
19. Persona modes alter prompt instruction.
20. Bill comparison context works.
21. Existing Central prediction values remain unchanged.
22. State prediction count remains exactly 0.
23. Dashboard continues loading with AI unavailable.

ALL GROQ API TESTS MUST USE MOCKS. Zero live API keys required.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from config.settings import Settings, settings
from schemas.bill import Bill, BillHouse, BillJurisdiction, BillStatus
from schemas.decision import DecisionSupportRecord
from schemas.state_knowledge import StateBillKnowledge, StateBillSummary
from schemas.unified_bill_record import UnifiedBillRecord
from services.ai.ai_context_builder import AIComparisonContext, AIContext, AIContextBuilder
from services.ai.ai_explanation_service import AIExplanationResult, AIExplanationService
from services.ai.ai_guardrails import AIGuardrails, PERSONAS, ValidationResult
from services.ai.groq_client import AIResponse, GroqClient
from storage.bill_repository import BillRepository
from storage.decision_repository import DecisionRepository
from storage.state_bill_repository import StateBillRepository
from storage.state_knowledge_repository import StateKnowledgeRepository


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_groq_client() -> GroqClient:
    """Fixture providing GroqClient configured with a mock provider."""
    mock_instance = MagicMock()
    # Mock chat completion return object
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "This bill introduces regulatory compliance standards for enterprises across the national economy. "
        "Based on verified project records."
    )
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage.prompt_tokens = 50
    mock_response.usage.completion_tokens = 30
    mock_response.usage.total_tokens = 80
    mock_instance.chat.completions.create.return_value = mock_response

    client = GroqClient(
        api_key="gsk_test_mock_key_for_testing_purposes_only",
        model="llama-3.3-70b-versatile",
        client_instance=mock_instance,
    )
    return client


@pytest.fixture
def context_builder() -> AIContextBuilder:
    """Fixture providing initialized AIContextBuilder."""
    return AIContextBuilder()


@pytest.fixture
def ai_service(mock_groq_client: GroqClient, tmp_path: Path) -> AIExplanationService:
    """Fixture providing initialized AIExplanationService with mock client and temp cache."""
    return AIExplanationService(
        groq_client=mock_groq_client,
        cache_dir=tmp_path / "test_ai_cache",
        enable_cache=True,
    )


# ==============================================================================
# 1 & 2. Configuration & Missing API Key Safety
# ==============================================================================

def test_missing_api_key_handled_safely() -> None:
    """1. Verify missing GROQ_API_KEY does not crash and returns controlled fallback."""
    client = GroqClient(api_key="")
    assert client.is_available is False

    res = client.chat_completion([{"role": "user", "content": "Explain this bill"}])
    assert res.success is False
    assert res.error_code == "API_KEY_MISSING"
    assert "Groq API key is not configured" in res.error_message
    assert "The verified legislative and analytical information remains available" in res.fallback_message
    assert "AI explanation is unavailable" in res.display_text


def test_configuration_loads_correctly_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """2. Verify configuration loads correctly from environment variables."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_custom_key_1234567890")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
    monkeypatch.setenv("GROQ_TIMEOUT", "45.5")
    monkeypatch.setenv("GROQ_MAX_TOKENS", "2048")
    monkeypatch.setenv("GROQ_TEMPERATURE", "0.1")

    client = GroqClient()
    assert client.is_available is True
    assert client.model == "llama-3.1-8b-instant"
    assert client.timeout == 45.5
    assert client.max_tokens == 2048
    assert client.temperature == 0.1


# ==============================================================================
# 3, 4, 5, 6, 7, 8. Context Builder & Categorization
# ==============================================================================

def test_central_context_builder_works(context_builder: AIContextBuilder) -> None:
    """3. Verify Central context builder extracts verified facts, domain, and predictions."""
    ctx = context_builder.build_context("the-boilers-bill-2024")
    assert ctx.is_central is True
    assert ctx.is_state is False
    assert ctx.jurisdiction == "central"
    assert len(ctx.facts) > 0
    assert len(ctx.derived) > 0
    assert len(ctx.predictions) > 0
    assert ctx.context_hash != ""


def test_state_context_builder_works(context_builder: AIContextBuilder) -> None:
    """4. Verify State context builder works with state legislative dossier."""
    ctx = context_builder.build_context("karnataka-vs-bill-27-2024")
    assert ctx.is_state is True
    assert ctx.is_central is False
    assert ctx.jurisdiction == "state"
    assert ctx.state == "Karnataka"
    assert len(ctx.facts) > 0
    assert len(ctx.derived) > 0


def test_facts_are_separated(context_builder: AIContextBuilder) -> None:
    """5. Verify facts are explicitly segregated under [FACTS]."""
    ctx = context_builder.build_context("the-boilers-bill-2024")
    block = ctx.format_prompt_block()
    assert "[FACTS — Authoritative Statutory & Gazette Records]" in block
    assert "Parliament of India" in block


def test_derived_information_is_separated(context_builder: AIContextBuilder) -> None:
    """6. Verify derived taxonomies & exposures are explicitly segregated under [DERIVED INFORMATION]."""
    ctx = context_builder.build_context("the-boilers-bill-2024")
    block = ctx.format_prompt_block()
    assert "[DERIVED INFORMATION — System-Assigned Taxonomies & Mappings]" in block
    assert "Primary Economic Sector:" in block or "Policy Domain:" in block


def test_predictions_are_labelled(context_builder: AIContextBuilder) -> None:
    """7. Verify Central predictions are clearly labeled as model outputs, not certainties."""
    ctx = context_builder.build_context("the-boilers-bill-2024")
    block = ctx.format_prompt_block()
    assert "[PREDICTIONS — Central Model Forecasts" in block
    assert "NOTE: These predictions are generated by existing, frozen quantitative market models" in block


def test_state_prediction_absence_is_preserved(context_builder: AIContextBuilder) -> None:
    """8. Verify State prediction absence is strictly preserved (State market predictions = 0)."""
    ctx = context_builder.build_context("karnataka-vs-bill-27-2024")
    assert ctx.is_state is True
    block = ctx.format_prompt_block()
    assert "State market prediction is currently unavailable." in block
    assert "Model predictions strictly 0" in block


# ==============================================================================
# 9, 10, 11. Zero Invention & Integrity Guarantees
# ==============================================================================

def test_missing_dates_cannot_be_invented_by_context_builder(context_builder: AIContextBuilder) -> None:
    """9. Verify missing introduction dates are rendered as unavailable, never fabricated."""
    # Find a state bill with missing introduction date (e.g. AP_2024_LA_18 or test stub)
    state_k_repo = StateKnowledgeRepository()
    all_k = state_k_repo.get_all()
    missing_date_bills = [k for k in all_k if not k.introduction_date]

    if missing_date_bills:
        sample_bid = missing_date_bills[0].bill_id
        ctx = context_builder.build_context(sample_bid)
        assert ctx.introduction_date is None
        assert "Introduction date unavailable" in ctx.format_prompt_block()
    else:
        # Synthetic check
        ctx = AIContext(bill_id="test-b", title="Test", jurisdiction="state", introduction_date=None)
        assert "Introduction date unavailable" in ctx.format_prompt_block()


def test_company_exposure_cannot_be_invented_by_context_builder(context_builder: AIContextBuilder) -> None:
    """10. Verify that for bills without mapped corporate exposure, zero exposures are invented."""
    # A bill with 0 corporate exposures
    state_k_repo = StateKnowledgeRepository()
    for k in state_k_repo.get_all():
        if not k.corporate_exposures:
            ctx = context_builder.build_context(k.bill_id)
            assert any("Zero mapped commercial securities" in d for d in ctx.derived)
            break


def test_market_prediction_cannot_be_invented_by_context_builder(context_builder: AIContextBuilder) -> None:
    """11. Verify context builder never manufactures market predictions for State bills."""
    for state_bid in ["karnataka-vs-bill-27-2024", "andhra-pradesh-vs-bill-1-2026", "kerala-vs-bill-167-2023", "telangana-vs-bill-1-2026"]:
        ctx = context_builder.build_context(state_bid)
        for pred in ctx.predictions:
            p_lower = pred.lower()
            assert any(term in p_lower for term in ["unavailable", "isolated", "strictly 0", "no quantitative stock price"])


# ==============================================================================
# 12, 13, 14. Guardrails & Safety Auditing
# ==============================================================================

def test_financial_advice_detection_works() -> None:
    """12. Verify detector flags prohibited financial advice keywords (buy/sell)."""
    bad_responses = [
        "Investors should buy the stock of BHEL immediately for high returns.",
        "We recommend you sell shares before the bill passes.",
        "This is a strong buy opportunity with a guaranteed return.",
    ]
    for text in bad_responses:
        val = AIGuardrails.validate_response(text)
        assert val.is_valid is False
        assert any("Financial advice" in v for v in val.violations)
        assert "compliance guardrails" in val.fallback_message


def test_unsupported_certainty_detection_works() -> None:
    """13. Verify detector flags unwarranted certainty."""
    bad_responses = [
        "The market will definitely surge by 15% upon parliamentary passage.",
        "This is a 100% guarantee that renewable energy stocks will boom.",
        "Stock prices are certain to rise without doubt.",
    ]
    for text in bad_responses:
        val = AIGuardrails.validate_response(text)
        assert val.is_valid is False
        assert any("Unsupported certainty" in v for v in val.violations)


def test_insider_trading_language_detection_works() -> None:
    """14. Verify detector flags accusatory or illegal insider trading language."""
    bad_responses = [
        "Pre-event price drift is clear evidence of insider trading and corrupt leaks.",
        "There is illicit front-running by crooked market operators ahead of the tabling.",
    ]
    for text in bad_responses:
        val = AIGuardrails.validate_response(text)
        assert val.is_valid is False
        assert any("Accusatory or illicit trading language" in v for v in val.violations)


# ==============================================================================
# 15, 16, 17. Provider Error & Fault Tolerance
# ==============================================================================

def test_timeout_handling_works() -> None:
    """15. Verify APITimeoutError / Timeout is handled gracefully with safe fallback."""
    mock_instance = MagicMock()
    mock_instance.chat.completions.create.side_effect = TimeoutError("Request timed out after 30s")

    client = GroqClient(
        api_key="gsk_mock_key_for_timeout",
        client_instance=mock_instance,
    )
    res = client.chat_completion([{"role": "user", "content": "Test"}])
    assert res.success is False
    assert res.error_code == "TIMEOUT"
    assert "timed out" in res.fallback_message.lower()


def test_rate_limit_handling_works() -> None:
    """16. Verify RateLimitError is caught and converted to safe user fallback."""
    class MockRateLimitError(Exception):
        pass

    mock_instance = MagicMock()
    mock_instance.chat.completions.create.side_effect = MockRateLimitError("Rate limit exceeded: 30 RPM")

    client = GroqClient(
        api_key="gsk_mock_key_for_ratelimit",
        client_instance=mock_instance,
    )
    res = client.chat_completion([{"role": "user", "content": "Test"}])
    assert res.success is False
    assert res.error_code == "RATE_LIMIT"
    assert "rate limit" in res.fallback_message.lower()


def test_invalid_response_handling_works() -> None:
    """17. Verify empty or malformed provider response is handled gracefully."""
    mock_instance = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = []  # Empty choices
    mock_instance.chat.completions.create.return_value = mock_resp

    client = GroqClient(
        api_key="gsk_mock_key_for_empty",
        client_instance=mock_instance,
    )
    res = client.chat_completion([{"role": "user", "content": "Test"}])
    assert res.success is False
    assert res.error_code == "EMPTY_RESPONSE"
    assert "empty provider response" in res.fallback_message


# ==============================================================================
# 18, 19, 20. Caching, Personas, & Bill Comparison
# ==============================================================================

def test_cache_invalidates_when_context_hash_changes(tmp_path: Path) -> None:
    """18. Verify cache is invalidated if the underlying context hash changes."""
    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Explanation 1"
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_resp

    client = GroqClient(api_key="gsk_mock", client_instance=mock_client)
    svc = AIExplanationService(groq_client=client, cache_dir=tmp_path / "cache", enable_cache=True)

    ctx1 = AIContext(bill_id="b1", title="Title 1", jurisdiction="central", facts=["Fact A"])
    res1 = svc._execute_explanation(ctx1, "BILL_SUMMARY", "Prompt", persona="GENERAL_PUBLIC")
    assert res1.is_cached is False
    assert mock_client.chat.completions.create.call_count == 1

    # Same context -> should hit cache
    res2 = svc._execute_explanation(ctx1, "BILL_SUMMARY", "Prompt", persona="GENERAL_PUBLIC")
    assert res2.is_cached is True
    assert mock_client.chat.completions.create.call_count == 1

    # Modified context (new fact) -> hash changes -> cache miss
    ctx2 = AIContext(bill_id="b1", title="Title 1", jurisdiction="central", facts=["Fact A", "Fact B"])
    assert ctx1.context_hash != ctx2.context_hash
    res3 = svc._execute_explanation(ctx2, "BILL_SUMMARY", "Prompt", persona="GENERAL_PUBLIC")
    assert res3.is_cached is False
    assert mock_client.chat.completions.create.call_count == 2


def test_persona_modes_work(ai_service: AIExplanationService) -> None:
    """19. Verify persona modes alter the system prompt instruction appropriately."""
    for p in ["INVESTOR", "BUSINESS_OWNER", "EMPLOYEE", "CONSUMER", "FARMER", "MSME", "GENERAL_PUBLIC", "INDUSTRY"]:
        sys_prompt = AIGuardrails.get_system_prompt(persona=p)
        assert f"Active Persona Mode: [{p}]" in sys_prompt
        assert PERSONAS[p][:25] in sys_prompt


def test_bill_comparison_context_works(context_builder: AIContextBuilder) -> None:
    """20. Verify bill comparison constructs side-by-side context for two bills."""
    comp_ctx = context_builder.build_comparison_context("the-boilers-bill-2024", "karnataka-vs-bill-27-2024")
    assert comp_ctx.bill_1.bill_id == "the-boilers-bill-2024"
    assert comp_ctx.bill_2.bill_id == "karnataka-vs-bill-27-2024"
    prompt_block = comp_ctx.format_prompt_block()
    assert "=== VERIFIED BILL COMPARISON CONTEXT ===" in prompt_block
    assert "--- BILL 1 ---" in prompt_block
    assert "--- BILL 2 ---" in prompt_block
    assert comp_ctx.context_hash != ""


# ==============================================================================
# 21, 22, 23. Regression Protection & Dashboard Usability
# ==============================================================================

def test_existing_central_prediction_values_remain_unchanged() -> None:
    """21. Verify existing Central production prediction counts remain exactly 4,700."""
    dec_repo = DecisionRepository()
    files = [f for f in dec_repo._root.glob("dec_*.json")]
    assert len(files) == 4700, f"Expected 4,700 decision records, got {len(files)}"


def test_state_prediction_count_remains_exactly_zero() -> None:
    """22. Verify State predictions remain EXACTLY 0."""
    state_k_repo = StateKnowledgeRepository()
    records = state_k_repo.get_all()
    assert len(records) == 44

    # Ensure no prediction records exist for state bills
    dec_repo = DecisionRepository()
    for rec in records:
        state_decs = dec_repo.get_by_bill(rec.bill_id)
        assert len(state_decs) == 0, f"State bill {rec.bill_id} must have 0 predictions!"


def test_dashboard_continues_loading_with_ai_unavailable() -> None:
    """23. Verify dashboard modules still load cleanly without crashing when AI is unavailable."""
    try:
        import dashboard.app
    except ImportError:
        pytest.skip("streamlit not installed in test environment")
    from dashboard.components.ai_explanation_panel import get_ai_service

    svc = get_ai_service()
    # Even if client is unavailable, it does not throw
    is_avail = svc.client.is_available
    assert isinstance(is_avail, bool)

    # Explanation service returns controlled fallback
    res = svc.explain_market_intelligence("karnataka-vs-bill-27-2024")
    assert res.success is True
    assert "Market prediction is currently unavailable for this State bill" in res.content
