"""
services/ai/ai_explanation_service.py
=====================================
High-level AI Explanation Orchestration Service.

Coordinates:
- AIContextBuilder (deterministic verified context)
- AIGuardrails (system prompt, persona adaptation, and post-audit validation)
- GroqClient (isolated inference provider)
- Context-hashed deterministic caching
- Standardized AIExplanationResult container
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from config.logging_config import get_logger
from config.settings import settings
from services.ai.ai_context_builder import (
    AIComparisonContext,
    AICompanyContext,
    AIContext,
    AIContextBuilder,
)
from services.ai.ai_guardrails import AIGuardrails, PERSONAS, ValidationResult
from services.ai.groq_client import AIResponse, GroqClient
from utils.file_utils import ensure_dir, file_exists, load_json, save_json

logger = get_logger(__name__)


@dataclass
class AIExplanationResult:
    """Standardized result container for all AI explanation operations."""

    content: str
    bill_id: str = ""
    operation: str = "EXPLANATION"
    persona: str = "GENERAL_PUBLIC"
    jurisdiction: str = "central"
    success: bool = True
    is_cached: bool = False
    context_hash: str = ""
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    provenance_sources: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)

    @property
    def display_markdown(self) -> str:
        """Render markdown with lightweight provenance footer."""
        out = self.content.strip()
        if self.provenance_sources:
            sources_str = ", ".join(self.provenance_sources)
            footer = f"\n\n---\n*Verified Provenance: Based on authoritative project data ({sources_str}). Explanation only; not investment advice.*"
            if not out.endswith(footer):
                out += footer
        return out


class AIExplanationService:
    """
    Orchestration service for AI-powered legislative intelligence explanations.
    """

    def __init__(
        self,
        groq_client: Optional[GroqClient] = None,
        context_builder: Optional[AIContextBuilder] = None,
        guardrails: Optional[AIGuardrails] = None,
        cache_dir: Optional[Path] = None,
        enable_cache: bool = True,
    ) -> None:
        self.client = groq_client or GroqClient()
        self.context_builder = context_builder or AIContextBuilder()
        self.guardrails = guardrails or AIGuardrails()
        self.cache_dir = cache_dir or getattr(settings, "AI_CACHE_DIR", settings.DATA_DIR / "ai_cache")
        self.enable_cache = enable_cache
        self._memory_cache: dict[str, dict[str, Any]] = {}

        if self.enable_cache:
            ensure_dir(self.cache_dir)

    def _compute_cache_key(
        self,
        context_hash: str,
        operation: str,
        persona: str,
        query: str = "",
        model: str = "",
    ) -> str:
        """Compute SHA256 cache key combining context hash and operation metadata."""
        raw = f"{context_hash}:{operation}:{persona.upper()}:{query.strip()}:{model}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[dict[str, Any]]:
        """Retrieve cached result from memory or disk."""
        if not self.enable_cache:
            return None
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]
        disk_file = self.cache_dir / f"{cache_key}.json"
        if file_exists(disk_file):
            try:
                data = load_json(disk_file)
                self._memory_cache[cache_key] = data
                return data
            except Exception as exc:
                logger.debug("Failed reading AI cache file %s: %s", disk_file, exc)
        return None

    def _save_to_cache(self, cache_key: str, data: dict[str, Any]) -> None:
        """Persist result to memory and disk cache."""
        if not self.enable_cache:
            return
        self._memory_cache[cache_key] = data
        disk_file = self.cache_dir / f"{cache_key}.json"
        try:
            save_json(data, disk_file)
        except Exception as exc:
            logger.debug("Failed saving AI cache to disk: %s", exc)

    def clear_cache(self) -> None:
        """Clear in-memory and disk AI explanation caches."""
        self._memory_cache.clear()
        if self.cache_dir.is_dir():
            for p in self.cache_dir.glob("*.json"):
                try:
                    p.unlink()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Core Pipeline Orchestrator
    # ------------------------------------------------------------------

    def _execute_explanation(
        self,
        context: AIContext,
        operation: str,
        user_prompt: str,
        persona: str = "GENERAL_PUBLIC",
        max_tokens: Optional[int] = None,
    ) -> AIExplanationResult:
        """
        Execute grounded generation through context, guardrails, Groq, and validation.
        """
        norm_persona = persona.upper().replace(" ", "_")
        b_id = getattr(context, "bill_id", None) or getattr(context, "company_id", None) or getattr(context, "industry_id", "UNKNOWN")
        j_scope = getattr(context, "jurisdiction", getattr(context, "universe_type", "central"))
        cache_key = self._compute_cache_key(
            context_hash=context.context_hash,
            operation=operation,
            persona=norm_persona,
            query=user_prompt,
            model=self.client.model,
        )

        # Check Cache
        cached = self._get_from_cache(cache_key)
        if cached:
            return AIExplanationResult(
                content=cached["content"],
                bill_id=b_id,
                operation=operation,
                persona=norm_persona,
                jurisdiction=j_scope,
                success=True,
                is_cached=True,
                context_hash=context.context_hash,
                provenance_sources=cached.get("provenance_sources", []),
            )

        # Build messages
        system_prompt = self.guardrails.get_system_prompt(norm_persona)
        context_block = context.format_prompt_block()

        full_user_content = f"{context_block}\n\nUSER REQUEST / OPERATION: [{operation}]\n{user_prompt}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_user_content},
        ]

        # Call Groq
        response = self.client.chat_completion(messages, max_tokens=max_tokens)
        if not response.success:
            b_id = getattr(context, "bill_id", None) or getattr(context, "company_id", "UNKNOWN")
            j_scope = getattr(context, "jurisdiction", getattr(context, "universe_type", "central"))
            p_source = context.provenance.get("source_url") or context.provenance.get("sources") or "Project Repository"
            return AIExplanationResult(
                content=response.fallback_message or "AI explanation is temporarily unavailable.",
                bill_id=b_id,
                operation=operation,
                persona=norm_persona,
                jurisdiction=j_scope,
                success=False,
                is_cached=False,
                context_hash=context.context_hash,
                error_code=response.error_code,
                error_message=response.error_message,
                provenance_sources=[p_source],
            )

        # Post-generation guardrails validation
        validation: ValidationResult = self.guardrails.validate_response(response.content, context=context)

        # Attempt 1 controlled retry if validation failed
        if not validation.is_valid:
            logger.info("Retrying AI explanation with strict corrective prompt for %s", context.bill_id)
            retry_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_user_content},
                {"role": "assistant", "content": response.content},
                {
                    "role": "user",
                    "content": (
                        f"CORRECTION DIRECTIVE: Your previous response violated safety policies ({', '.join(validation.violations)}). "
                        "Regenerate your response immediately, strictly removing all forbidden financial advice, unsupported certainty, "
                        "or unverified numerical values. Use only verified facts from the context block."
                    ),
                },
            ]
            retry_resp = self.client.chat_completion(retry_messages, max_tokens=max_tokens)
            if retry_resp.success:
                validation = self.guardrails.validate_response(retry_resp.content, context=context)
                if validation.is_valid:
                    response = retry_resp

        # If still invalid, return safe fallback
        if not validation.is_valid:
            b_id = getattr(context, "bill_id", None) or getattr(context, "company_id", "UNKNOWN")
            j_scope = getattr(context, "jurisdiction", getattr(context, "universe_type", "central"))
            p_source = context.provenance.get("source_url") or context.provenance.get("sources") or "Project Repository"
            return AIExplanationResult(
                content=validation.fallback_message or "AI explanation unavailable due to policy restrictions.",
                bill_id=b_id,
                operation=operation,
                persona=norm_persona,
                jurisdiction=j_scope,
                success=False,
                is_cached=False,
                context_hash=context.context_hash,
                error_code="VALIDATION_FAILED",
                error_message="; ".join(validation.violations),
                violations=validation.violations,
                provenance_sources=[p_source],
            )

        final_content = response.content
        sources = []
        if context.provenance.get("source_url"):
            sources.append(context.provenance["source_url"])
        if context.provenance.get("pdf_url"):
            sources.append(context.provenance["pdf_url"])
        if context.provenance.get("sources"):
            sources.append(context.provenance["sources"])
        if not sources:
            sources.append("Official Legislative / Corporate Record")

        # Save to Cache
        cache_data = {
            "content": final_content,
            "provenance_sources": sources,
            "bill_id": context.bill_id,
            "operation": operation,
            "persona": norm_persona,
        }
        self._save_to_cache(cache_key, cache_data)

        return AIExplanationResult(
            content=final_content,
            bill_id=context.bill_id,
            operation=operation,
            persona=norm_persona,
            jurisdiction=context.jurisdiction,
            success=True,
            is_cached=False,
            context_hash=context.context_hash,
            provenance_sources=sources,
        )

    # ------------------------------------------------------------------
    # Public Explanation Operations
    # ------------------------------------------------------------------

    def explain_bill_summary(
        self,
        bill_id: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """A. BILL SUMMARY: Explain this bill in simple language."""
        ctx = self.context_builder.build_context(bill_id)
        prompt = "Explain this legislative bill in plain, easy-to-understand language. Summarize what it is and what changes it introduces."
        return self._execute_explanation(ctx, "BILL_SUMMARY", prompt, persona=persona)

    def explain_why_it_matters(
        self,
        bill_id: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """B. WHY IT MATTERS: Why does this bill matter?"""
        ctx = self.context_builder.build_context(bill_id)
        prompt = "Explain why this bill matters in practice. Detail its broader economic, governance, and institutional significance."
        return self._execute_explanation(ctx, "WHY_IT_MATTERS", prompt, persona=persona)

    def explain_provisions(
        self,
        bill_id: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """C. PROVISIONS: Explain the important provisions."""
        ctx = self.context_builder.build_context(bill_id)
        prompt = "Explain the key statutory provisions of this bill clearly and systematically, based strictly on the verified facts."
        return self._execute_explanation(ctx, "PROVISIONS", prompt, persona=persona)

    def explain_sector_impact(
        self,
        bill_id: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """D. SECTOR IMPACT: Which sectors may be affected and why?"""
        ctx = self.context_builder.build_context(bill_id)
        prompt = "Which economic sectors are affected by this bill and through what specific mechanisms? Ground your answer in the verified sector mappings."
        return self._execute_explanation(ctx, "SECTOR_IMPACT", prompt, persona=persona)

    def explain_stakeholders(
        self,
        bill_id: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """E. STAKEHOLDERS: Who may be affected?"""
        ctx = self.context_builder.build_context(bill_id)
        prompt = "Who are the key affected stakeholders (e.g. workers, consumers, industry, government) and what are the practical implications for each?"
        return self._execute_explanation(ctx, "STAKEHOLDERS", prompt, persona=persona)

    def explain_company_exposure(
        self,
        bill_id: str,
        company_isin: Optional[str] = None,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """F. COMPANY EXPOSURE: Why are these companies considered exposed?"""
        ctx = self.context_builder.build_context(bill_id)
        sub_filter = f"Specifically address company ISIN/ticker: {company_isin}." if company_isin else ""
        prompt = (
            f"Explain why specific companies are identified as exposed in the verified records. "
            f"Detail the exposure mechanisms (direct/indirect regulatory impact). {sub_filter} "
            "Do NOT speculate on unmapped companies or give investment advice."
        )
        return self._execute_explanation(ctx, "COMPANY_EXPOSURE", prompt, persona=persona)

    def explain_market_intelligence(
        self,
        bill_id: str,
        persona: str = "INVESTOR",
    ) -> AIExplanationResult:
        """G. MARKET INTELLIGENCE: Explain the existing market assessment."""
        ctx = self.context_builder.build_context(bill_id)
        if ctx.is_state:
            return AIExplanationResult(
                content=(
                    "**Market prediction is currently unavailable for this State bill.**\n\n"
                    "State legislative bills are part of the State Knowledge & Economic Layer and are strictly isolated "
                    "from Central stock-market prediction models. Quantitative stock price predictions remain **strictly 0**."
                ),
                bill_id=bill_id,
                operation="MARKET_INTELLIGENCE",
                persona=persona,
                jurisdiction="state",
                success=True,
                is_cached=False,
                context_hash=ctx.context_hash,
                provenance_sources=[ctx.provenance.get("source_url", "State Legislative Repository")],
            )

        prompt = (
            "Explain the existing quantitative market impact model outputs (predicted direction, market-moving probability, "
            "and confidence) provided in the context. Explain what the model drivers signify without recalculating or modifying the numbers."
        )
        return self._execute_explanation(ctx, "MARKET_INTELLIGENCE", prompt, persona=persona)

    def explain_risk_profile(
        self,
        bill_id: str,
        persona: str = "INVESTOR",
    ) -> AIExplanationResult:
        """H. RISK: Why is the risk classified this way?"""
        ctx = self.context_builder.build_context(bill_id)
        if ctx.is_state:
            return AIExplanationResult(
                content=(
                    "**Quantitative risk scoring is currently unavailable for this State bill.**\n\n"
                    "State statutes are assessed through qualitative compliance and economic mechanism indicators. "
                    "Central composite risk scoring models apply exclusively to Central parliamentary bills."
                ),
                bill_id=bill_id,
                operation="RISK_PROFILE",
                persona=persona,
                jurisdiction="state",
                success=True,
                is_cached=False,
                context_hash=ctx.context_hash,
                provenance_sources=[ctx.provenance.get("source_url", "State Legislative Repository")],
            )

        prompt = (
            "Explain the composite risk evaluation score and tier (e.g. LOW, MODERATE, HIGH) from the context. "
            "Explain the balance of regulatory uncertainty, policy scope, and tail exposure indicated by the existing model."
        )
        return self._execute_explanation(ctx, "RISK_PROFILE", prompt, persona=persona)

    def explain_anticipation(
        self,
        bill_id: str,
        persona: str = "INVESTOR",
    ) -> AIExplanationResult:
        """I. ANTICIPATION: Explain the pricing-in/anticipation assessment."""
        ctx = self.context_builder.build_context(bill_id)
        if ctx.is_state:
            return AIExplanationResult(
                content=(
                    "**Pre-event anticipation modeling is currently unavailable for this State bill.**\n\n"
                    "State bills are not subjected to pre-event market diffusion studies. "
                    "Pre-event pricing-in analysis is conducted exclusively for Central production bills."
                ),
                bill_id=bill_id,
                operation="ANTICIPATION",
                persona=persona,
                jurisdiction="state",
                success=True,
                is_cached=False,
                context_hash=ctx.context_hash,
                provenance_sources=[ctx.provenance.get("source_url", "State Legislative Repository")],
            )

        prompt = (
            "Explain the pre-event pricing-in and anticipation evidence from the verified context. "
            "Use strictly neutral, non-accusatory academic terminology (e.g. 'information diffusion', 'pricing-in dynamics'). "
            "Never accuse any party of illegal trading."
        )
        return self._execute_explanation(ctx, "ANTICIPATION", prompt, persona=persona)

    def compare_bills(
        self,
        bill_id_1: str,
        bill_id_2: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """J. COMPARE BILLS: Compare two bills side-by-side."""
        comparison_ctx: AIComparisonContext = self.context_builder.build_comparison_context(bill_id_1, bill_id_2)
        norm_persona = persona.upper().replace(" ", "_")

        cache_key = self._compute_cache_key(
            context_hash=comparison_ctx.context_hash,
            operation="COMPARE_BILLS",
            persona=norm_persona,
            query=f"{bill_id_1} vs {bill_id_2}",
            model=self.client.model,
        )

        cached = self._get_from_cache(cache_key)
        if cached:
            return AIExplanationResult(
                content=cached["content"],
                bill_id=f"{bill_id_1}_vs_{bill_id_2}",
                operation="COMPARE_BILLS",
                persona=norm_persona,
                jurisdiction="comparative",
                success=True,
                is_cached=True,
                context_hash=comparison_ctx.context_hash,
                provenance_sources=cached.get("provenance_sources", []),
            )

        system_prompt = self.guardrails.get_system_prompt(norm_persona)
        context_block = comparison_ctx.format_prompt_block()
        prompt = (
            f"Compare these two bills ({bill_id_1} and {bill_id_2}) across:\n"
            "1. Policy domain, purpose, and key statutory provisions\n"
            "2. Economic sectors and affected stakeholders\n"
            "3. Corporate exposure and compliance implications\n"
            "4. Jurisdictional scope (Central vs State differences where applicable)\n"
            "5. Market relevance and modeling availability\n"
            "Do NOT fabricate new predictions. Ground everything in the supplied context."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context_block}\n\nUSER REQUEST: {prompt}"},
        ]

        response = self.client.chat_completion(messages)
        if not response.success:
            return AIExplanationResult(
                content=response.fallback_message or "AI bill comparison is temporarily unavailable.",
                bill_id=f"{bill_id_1}_vs_{bill_id_2}",
                operation="COMPARE_BILLS",
                persona=norm_persona,
                jurisdiction="comparative",
                success=False,
                is_cached=False,
                context_hash=comparison_ctx.context_hash,
                error_code=response.error_code,
                error_message=response.error_message,
            )

        # Validate
        validation = self.guardrails.validate_response(response.content)
        if not validation.is_valid:
            return AIExplanationResult(
                content=validation.fallback_message or "Comparison unavailable due to policy restrictions.",
                bill_id=f"{bill_id_1}_vs_{bill_id_2}",
                operation="COMPARE_BILLS",
                persona=norm_persona,
                jurisdiction="comparative",
                success=False,
                is_cached=False,
                context_hash=comparison_ctx.context_hash,
                error_code="VALIDATION_FAILED",
                error_message="; ".join(validation.violations),
            )

        sources = [
            comparison_ctx.bill_1.provenance.get("source_url", "Bill 1 Record"),
            comparison_ctx.bill_2.provenance.get("source_url", "Bill 2 Record"),
        ]
        self._save_to_cache(
            cache_key,
            {
                "content": response.content,
                "provenance_sources": sources,
                "bill_id": f"{bill_id_1}_vs_{bill_id_2}",
                "operation": "COMPARE_BILLS",
                "persona": norm_persona,
            },
        )

        return AIExplanationResult(
            content=response.content,
            bill_id=f"{bill_id_1}_vs_{bill_id_2}",
            operation="COMPARE_BILLS",
            persona=norm_persona,
            jurisdiction="comparative",
            success=True,
            is_cached=False,
            context_hash=comparison_ctx.context_hash,
            provenance_sources=sources,
        )

    def ask_ai(
        self,
        bill_id: str,
        question: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """K. ASK AI: Free-form natural-language questions restricted to verified bill context."""
        ctx = self.context_builder.build_context(bill_id)
        if not question or not question.strip():
            return AIExplanationResult(
                content="Please ask a specific question about this bill.",
                bill_id=bill_id,
                operation="ASK_AI",
                persona=persona,
                jurisdiction=ctx.jurisdiction,
                success=False,
                context_hash=ctx.context_hash,
            )

        prompt = (
            f"User Question: \"{question.strip()}\"\n\n"
            "Answer the question strictly using the verified bill context above. "
            "If the answer cannot be determined from the verified context, state honestly: "
            "'This information is unavailable in verified project records.'"
        )
        return self._execute_explanation(ctx, "ASK_AI", prompt, persona=persona)

    def explain_company_profile(
        self,
        company_identifier: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """Explain a corporate entity's business activities, sector presence, and legislative exposure scope."""
        ctx = self.context_builder.build_company_context(company_identifier)
        prompt = (
            f"Provide a structured, plain-language synthesis of {ctx.company_name}'s profile, "
            "core business activities, and exposure across Central and State legislation. "
            "Explain what regulatory mechanisms and sector areas affect this entity. "
            "Do NOT provide stock price predictions, investment advice, or trade recommendations."
        )
        return self._execute_explanation(ctx, "COMPANY_PROFILE_EXPLANATION", prompt, persona=persona)

    def explain_company_bill_exposure(
        self,
        company_identifier: str,
        bill_id: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """Explain why a specific company is exposed to a specific legislative bill."""
        ctx = self.context_builder.build_company_bill_context(company_identifier, bill_id)
        prompt = (
            f"Explain specifically why {ctx.company_name} is affected by bill '{ctx.bill_title or bill_id}'. "
            "Detail the specific business activities, statutory mechanisms (e.g. compliance, licensing, taxation), "
            "geographic operational scope, and evidence citations that establish this exposure. "
            "Do NOT speculate on unmapped provisions or provide financial return forecasts."
        )
        return self._execute_explanation(ctx, "COMPANY_BILL_EXPOSURE", prompt, persona=persona)

    def ask_company_ai(
        self,
        company_identifier: str,
        question: str,
        bill_id: Optional[str] = None,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """Free-form natural-language questions restricted to verified company context."""
        if bill_id:
            ctx = self.context_builder.build_company_bill_context(company_identifier, bill_id)
        else:
            ctx = self.context_builder.build_company_context(company_identifier)

        if not question or not question.strip():
            return AIExplanationResult(
                content="Please ask a specific question about this company and its legislative exposures.",
                bill_id=getattr(ctx, "bill_id", "") or getattr(ctx, "company_id", ""),
                operation="ASK_COMPANY_AI",
                persona=persona,
                jurisdiction=getattr(ctx, "jurisdiction", getattr(ctx, "universe_type", "central")),
                success=False,
                context_hash=ctx.context_hash,
            )

        prompt = (
            f"User Question: \"{question.strip()}\"\n\n"
            f"Answer the question strictly using the verified company intelligence context for {ctx.company_name} above. "
            "If the answer cannot be determined from the verified context, state honestly: "
            "'This information is unavailable in verified project records.' "
            "Under no circumstances should you generate stock price predictions, trading signals, or target prices."
        )
        return self._execute_explanation(ctx, "ASK_COMPANY_AI", prompt, persona=persona)

    def ask_industry_ai(
        self,
        industry_identifier: str,
        question: str,
        persona: str = "GENERAL_PUBLIC",
    ) -> AIExplanationResult:
        """Free-form natural-language questions restricted to verified industry context."""
        ctx = self.context_builder.build_industry_context(industry_identifier)

        if not question or not question.strip():
            return AIExplanationResult(
                content="Please ask a specific question about this industry sector and its legislative exposures.",
                bill_id=getattr(ctx, "industry_id", ""),
                operation="ASK_INDUSTRY_AI",
                persona=persona,
                jurisdiction="unified",
                success=False,
                context_hash=ctx.context_hash,
            )

        prompt = (
            f"User Question: \"{question.strip()}\"\n\n"
            f"Answer the question strictly using the verified industry intelligence context for '{ctx.industry_name}' ({ctx.sector}) above. "
            "Address legislative drivers, affected companies, transmission mechanisms, and market analysis availability as documented. "
            "If the answer cannot be determined from the verified context, state honestly: "
            "'This information is unavailable in verified project records.' "
            "Under no circumstances should you generate speculative industry price targets, trading advice, or Buy/Sell/Hold recommendations."
        )
        return self._execute_explanation(ctx, "ASK_INDUSTRY_AI", prompt, persona=persona)

