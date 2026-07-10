"""
services/explanation.py
=======================
Orchestration service for generating AI-powered summaries and explanations.

Defines the pluggable LLMProvider extension interface so Groq can be integrated later.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from config.logging_config import get_logger
from storage.bill_repository import BillRepository

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# LLM Provider Abstract Interface (Extension Point for Groq)
# ---------------------------------------------------------------------------


class LLMProvider(ABC):
    """
    Abstract interface for LLM operations.
    Future tasks (e.g. Groq implementation) will subclass this.
    """

    @abstractmethod
    async def generate_summary(self, bill_title: str, bill_text: str) -> str:
        """
        Generate a plain-language summary of a bill.
        """
        pass

    @abstractmethod
    async def generate_explanation(
        self,
        bill_title: str,
        company_name: str,
        sector: str,
        predicted_impact: str,
    ) -> str:
        """
        Explain the predicted market impact on a company and sector.
        """
        pass

    @abstractmethod
    async def chat_response(self, query: str, context: str) -> str:
        """
        Respond to conversational user queries about bills or market reactions.
        """
        pass


# ---------------------------------------------------------------------------
# Explanation Service
# ---------------------------------------------------------------------------


class ExplanationService:
    """
    Orchestration service for AI explanations, summaries, and chat features.
    """

    def __init__(
        self,
        llm_provider: LLMProvider,
        bill_repository: Optional[BillRepository] = None,
    ) -> None:
        """
        Initialize the service. Uses Dependency Injection.

        Parameters
        ----------
        llm_provider : LLMProvider
            The LLM implementation (e.g., Groq provider).
        bill_repository : BillRepository | None
            Data access layer for bills.
        """
        self.llm = llm_provider
        self.bill_repo = bill_repository or BillRepository()

    async def summarize_bill(self, bill_id: str, save_back: bool = True) -> str:
        """
        Generate and persist a plain-language summary of a bill.

        Parameters
        ----------
        bill_id : str
        save_back : bool
            True to update the bill record in the repository with the generated summary.
        """
        logger.info("ExplanationService: summarizing bill=%s", bill_id)
        bill = self.bill_repo.get(bill_id)
        if not bill:
            raise ValueError(f"Bill not found: {bill_id}")

        # Call the pluggable LLM provider
        summary = await self.llm.generate_summary(bill.title, bill.full_text)

        if save_back:
            bill.summary = summary
            self.bill_repo.save(bill)
            logger.info("Saved generated summary back to bill repository: %s", bill_id)

        return summary

    async def explain_market_impact(
        self,
        bill_id: str,
        company_name: str,
        sector: str,
        predicted_impact: str,
    ) -> str:
        """
        Explain the market reaction for a specific (bill, company) prediction.
        """
        logger.info(
            "ExplanationService: explaining impact for bill=%s | company=%s | sector=%s",
            bill_id,
            company_name,
            sector,
        )
        bill = self.bill_repo.get(bill_id)
        if not bill:
            raise ValueError(f"Bill not found: {bill_id}")

        return await self.llm.generate_explanation(
            bill_title=bill.title,
            company_name=company_name,
            sector=sector,
            predicted_impact=predicted_impact,
        )

    async def ask_question(self, query: str, context_bill_ids: list[str]) -> str:
        """
        Provide conversational QA answers based on legislative context.
        """
        logger.info(
            "ExplanationService: answering query with context of %d bills", len(context_bill_ids)
        )
        contexts = []
        for bid in context_bill_ids:
            bill = self.bill_repo.get(bid)
            if bill:
                contexts.append(
                    f"Bill: {bill.title}\n"
                    f"Status: {bill.status.value}\n"
                    f"Ministry: {bill.ministry}\n"
                    f"Text: {bill.full_text[:500]}..."
                )

        merged_context = "\n\n".join(contexts)
        return await self.llm.chat_response(query, merged_context)
