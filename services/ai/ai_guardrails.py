"""
services/ai/ai_guardrails.py
============================
Deterministic AI Guardrails & Post-Generation Response Validator.

Implements all 20 non-negotiable project guardrails:
1. Grounded strictly in supplied context.
2. Zero invention of missing data.
3. Explicit "unavailable" declarations.
4. Zero fabricated citations or URLs.
5. Zero fabricated statutory provisions.
6. Zero fabricated corporate exposure.
7. Zero fabricated numerical predictions.
8. Zero claim of future market certainty.
9. Zero financial or investment advice.
10. Zero buy / sell / hold recommendations.
11. Forbidden advice keywords banned.
12. Strict Fact vs Interpretation distinction.
13. Explicit model prediction labeling.
14. Zero State market predictions (strictly unavailable).
15. Preservation of academic uncertainty.
16. Strict provenance attribution.
17. Zero insider-trading accusations (use "pricing-in" / "possible anticipation").
18. Refusal of unprovided context.
19. Honest knowledge boundary declaration.
20. Persona adaptation without personalized advice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Optional

from config.logging_config import get_logger
from services.ai.ai_context_builder import AIContext

logger = get_logger(__name__)

# Canonical Personas
PERSONAS: dict[str, str] = {
    "INVESTOR": (
        "Focus on institutional market relevance, regulatory uncertainty, sector sensitivities, "
        "and quantitative risk profiles. Strictly maintain probabilistic, non-advisory language. "
        "Do NOT recommend buying or selling any security."
    ),
    "BUSINESS_OWNER": (
        "Focus on compliance obligations, licensing requirements, operating cost impacts, "
        "and regulatory timelines. Avoid investment speculation."
    ),
    "EMPLOYEE": (
        "Focus on worker protections, wage mechanisms, job security, workplace health and safety, "
        "and statutory dispute redressal."
    ),
    "CONSUMER": (
        "Focus on consumer rights, price transparency, product quality standards, data privacy, "
        "and grievance mechanisms."
    ),
    "FARMER": (
        "Focus on agricultural procurement, crop support, irrigation rights, cooperative regulations, "
        "and credit accessibility."
    ),
    "MSME": (
        "Focus on micro and small enterprise formalization, priority credit, compliance relief, "
        "and dispute resolution mechanisms."
    ),
    "GENERAL_PUBLIC": (
        "Focus on citizen rights, public services, governance transparency, civic obligations, "
        "and practical real-world implications in plain language."
    ),
    "INDUSTRY": (
        "Focus on sectoral capital expenditure, supply chain standards, environmental compliances, "
        "and long-term corporate governance frameworks."
    ),
}

# Regex patterns for safety violations
_FINANCIAL_ADVICE_PATTERNS = [
    re.compile(r"\b(buy|sell)\s+(the\s+)?(stock|shares|securities|equities)\b", re.IGNORECASE),
    re.compile(r"\b(strong\s+buy|strong\s+sell|accumulate|portfolio\s+recommendation)\b", re.IGNORECASE),
    re.compile(r"\b(invest\s+in|divest\s+from)\s+[A-Z0-9]+", re.IGNORECASE),
    re.compile(r"\bguaranteed\s+(return|profit|gain|yield)\b", re.IGNORECASE),
    re.compile(r"\byou\s+should\s+(buy|sell|invest|purchase)\b", re.IGNORECASE),
]

_UNSUPPORTED_CERTAINTY_PATTERNS = [
    re.compile(r"\b(will\s+definitely|certain\s+to\s+rise|certain\s+to\s+fall|undoubtedly\s+will)\b", re.IGNORECASE),
    re.compile(r"\b(100%\s+guarantee|surefire\s+bet|inevitable\s+surge|guaranteed\s+drop)\b", re.IGNORECASE),
]

_INSIDER_TRADING_PATTERNS = [
    re.compile(r"\b(insider\s+trading|insider\s+leak|illegal\s+tipping|front[- ]running)\b", re.IGNORECASE),
    re.compile(r"\b(crooked|corrupt\s+trader|market\s+rigging)\b", re.IGNORECASE),
]

_STATE_PREDICTION_VIOLATION_PATTERNS = [
    re.compile(r"\b(stock\s+price\s+target|predicted\s+car|abnormal\s+return\s+of\s+[-+]?\d+)\b", re.IGNORECASE),
    re.compile(r"\b(shares\s+will\s+(gain|drop|rise|fall)\s+by\s+\d+)\b", re.IGNORECASE),
]

_PERCENTAGE_PATTERN = re.compile(r"\b(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
_DECIMAL_PROB_PATTERN = re.compile(r"\b0\.\d{2,}\b")


@dataclass
class ValidationResult:
    """Result of deterministic AI response audit."""

    is_valid: bool = True
    violations: list[str] = field(default_factory=list)
    sanitized_text: Optional[str] = None
    fallback_message: Optional[str] = None


class AIGuardrails:
    """System guardrails builder and response auditor."""

    @staticmethod
    def get_system_prompt(persona: str = "GENERAL_PUBLIC") -> str:
        """
        Generate the master system prompt with persona instruction and the 20 guardrails.
        """
        norm_persona = persona.upper().replace(" ", "_")
        persona_directive = PERSONAS.get(norm_persona, PERSONAS["GENERAL_PUBLIC"])

        return (
            "You are the official AI Intelligence & Explanation Layer for the India Legislative "
            "Intelligence & Market Impact Platform.\n"
            "You are strictly an explanation and analytical translation interface. You are NOT "
            "a prediction model, NOT a source of truth, and NOT a financial adviser.\n\n"
            "=== AUTHORITATIVE AUDIENCE DIRECTIVE ===\n"
            f"Active Persona Mode: [{norm_persona}]\n"
            f"{persona_directive}\n\n"
            "=== 20 NON-NEGOTIABLE GUARDRAIL RULES ===\n"
            "1. Grounding: Use ONLY the provided verified context. Never invent facts.\n"
            "2. Missing Data: If information is missing or unverified, explicitly state: 'Information is unavailable in project records.'\n"
            "3. Zero Citation Fabrication: Never invent URLs, statutory section numbers, or gazette numbers.\n"
            "4. Zero Provision Fabrication: Never invent statutory provisions not found in the verified text.\n"
            "5. Zero Company Fabrication: Mention only companies explicitly present in the provided context.\n"
            "6. Zero Prediction Invention: Never generate, invent, or adjust numerical predictions.\n"
            "7. No Future Certainty: Preserve uncertainty. Use 'the model estimates', 'the analysis indicates'.\n"
            "8. No Financial Advice: Never provide personalized financial, investment, or legal advice.\n"
            "9. No Trade Recommendations: Never tell users to buy, sell, or hold any security.\n"
            "10. Forbidden Wording: Never use 'buy', 'sell', 'guaranteed profit', or 'target price' as advice.\n"
            "11. Fact vs Derived: Clearly distinguish authoritative statutory facts from system-derived categories.\n"
            "12. Model Predictions: Clearly label quantitative scores as outputs of existing statistical models.\n"
            "13. State Bill Prediction Rule: State legislative bills are strictly isolated from market models. "
            "For State bills, you MUST explicitly state: 'Market prediction is currently unavailable for this State bill.' "
            "Never generate stock market predictions for State bills.\n"
            "14. Uncertainty: Highlight model limitations and data sufficiency boundaries honestly.\n"
            "15. Provenance: Attribute information to official gazettes, PDFs, and repository records.\n"
            "16. Non-Accusatory Anticipation: Never accuse any entity of 'insider trading' or illegal conduct. "
            "Use strictly neutral academic terms: 'pricing-in evidence' or 'possible anticipation dynamics'.\n"
            "17. Bound Query Scope: If a user asks about unprovided bills or external topics, state it is beyond verified project records.\n"
            "18. Provenance Integrity: Use only source URLs provided in context.\n"
            "19. Numerical Fidelity: Any numerical value (percentage, probability, risk score) you cite MUST "
            "originate verbatim from the supplied context. Never compute or round new numbers.\n"
            "20. Persona Boundaries: Tailor tone and focus to the persona without turning into individual consultation."
        )

    @staticmethod
    def validate_response(
        response_text: str,
        context: Optional[AIContext] = None,
    ) -> ValidationResult:
        """
        Deterministically inspect generated response against safety policies.

        Parameters
        ----------
        response_text : str
            Raw text from Groq.
        context : AIContext | None
            Supplied verified context.

        Returns
        -------
        ValidationResult
            Validation verdict with violations and fallback text if invalid.
        """
        if not response_text or not response_text.strip():
            return ValidationResult(
                is_valid=False,
                violations=["Empty response text"],
                fallback_message="AI explanation is unavailable (empty response returned).",
            )

        violations: list[str] = []

        # 1. Financial advice check
        for pat in _FINANCIAL_ADVICE_PATTERNS:
            match = pat.search(response_text)
            if match:
                violations.append(f"Financial advice pattern detected: '{match.group(0)}'")

        # 2. Unsupported certainty check
        for pat in _UNSUPPORTED_CERTAINTY_PATTERNS:
            match = pat.search(response_text)
            if match:
                violations.append(f"Unsupported certainty detected: '{match.group(0)}'")

        # 3. Insider trading language check
        for pat in _INSIDER_TRADING_PATTERNS:
            match = pat.search(response_text)
            if match:
                violations.append(f"Accusatory or illicit trading language detected: '{match.group(0)}'")

        # 4. State bill prediction violation
        if context and context.is_state:
            for pat in _STATE_PREDICTION_VIOLATION_PATTERNS:
                match = pat.search(response_text)
                if match:
                    violations.append(f"State bill market prediction violation: '{match.group(0)}'")

        # 5. Numerical integrity check
        if context:
            context_raw = context.format_prompt_block()
            # Extract numbers like 85% or 0.65 from response
            found_pcts = _PERCENTAGE_PATTERN.findall(response_text)
            for pct in found_pcts:
                # Check if this percentage exists in context_raw
                if f"{pct}%" not in context_raw and f"{pct} %" not in context_raw:
                    # Allow 0% or 100% if discussing complete absence or general concepts
                    if pct not in {"0", "100"}:
                        violations.append(f"Fabricated percentage detected: '{pct}%' not in context.")

        if violations:
            logger.warning("AI response failed guardrails validation: %s", violations)
            fallback = (
                "The AI-generated explanation was intercepted by the project's compliance guardrails "
                "because it contained language that violates analytical standards "
                f"({', '.join(violations[:2])}). "
                "The verified statutory metadata, policy categories, and model indicators remain authoritative above."
            )
            return ValidationResult(
                is_valid=False,
                violations=violations,
                fallback_message=fallback,
            )

        return ValidationResult(is_valid=True, sanitized_text=response_text)
