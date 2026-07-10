"""
tests/test_services.py
======================
Unit tests for the root Service Layer.
"""

from __future__ import annotations

from pathlib import Path
import pytest
import unittest.mock as mock

from schemas.bill import Bill, BillHouse, BillStatus
from schemas.prediction import ImpactLabel, Prediction
from services import IngestionService, PredictionService, ExplanationService, LLMProvider
from storage.bill_repository import BillRepository


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------


class DummyLLMProvider(LLMProvider):
    """
    Fake LLM provider returning mock responses for testing.
    """

    async def generate_summary(self, bill_title: str, bill_text: str) -> str:
        return f"Summary of {bill_title}: {bill_text[:20]}"

    async def generate_explanation(
        self,
        bill_title: str,
        company_name: str,
        sector: str,
        predicted_impact: str,
    ) -> str:
        return (
            f"Explanation for {company_name} ({sector}) impacted {predicted_impact} by {bill_title}"
        )

    async def chat_response(self, query: str, context: str) -> str:
        return f"Answer to query: '{query}' based on context length: {len(context)}"


# ---------------------------------------------------------------------------
# Tests for IngestionService
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingestion_service_delegation() -> None:
    # Set up mocks
    mock_parliament = mock.AsyncMock()
    mock_parliament.ingest_bills.return_value = {"discovered": 5, "inserted": 3}

    service = IngestionService(parliament_service=mock_parliament)
    res = await service.ingest_bills(source="prs", year=2024, dry_run=True)

    assert res["discovered"] == 5
    assert res["inserted"] == 3
    mock_parliament.ingest_bills.assert_called_once_with(
        source="prs",
        year=2024,
        latest_only=False,
        dry_run=True,
        bill_id_filter=None,
    )


@pytest.mark.asyncio
async def test_ingestion_service_stubs() -> None:
    service = IngestionService()
    res_companies = await service.ingest_companies(dry_run=True)
    res_market = await service.ingest_market_prices(dry_run=True)

    assert res_companies == {"processed": 50, "validation_passed": 50, "errors": 0, "warnings": 0}
    assert res_market == {"inserted": 0, "updated": 0, "skipped": 0, "failed": 0}


# ---------------------------------------------------------------------------
# Tests for PredictionService
# ---------------------------------------------------------------------------


def test_prediction_service_impact(tmp_path: Path) -> None:
    repo = BillRepository()
    repo._metadata_dir = tmp_path / "metadata"
    repo._metadata_dir.mkdir(parents=True, exist_ok=True)

    bill = Bill(
        bill_id="test-pred-bill",
        title="Test Prediction Bill",
        year=2024,
        ministry="Ministry of Corporate Affairs",
        status=BillStatus.INTRODUCED,
        house=BillHouse.LOK_SABHA,
        url="https://prsindia.org/bill/test-pred-bill",
        full_text="This is a test corporate bill to predict market reactions.",
    )
    repo.save(bill)

    service = PredictionService(bill_repository=repo)
    prediction = service.predict_impact("test-pred-bill", "INE001A01036")

    assert isinstance(prediction, Prediction)
    assert prediction.bill_id == "test-pred-bill"
    assert prediction.overall_impact == ImpactLabel.NEUTRAL
    assert prediction.companies[0].isin == "INE001A01036"
    assert prediction.companies[0].top_features == ["bill_length"]


def test_prediction_service_missing_bill(tmp_path: Path) -> None:
    repo = BillRepository()
    repo._metadata_dir = tmp_path / "metadata"
    repo._metadata_dir.mkdir(parents=True, exist_ok=True)

    service = PredictionService(bill_repository=repo)
    with pytest.raises(ValueError, match="Bill not found in repository"):
        service.predict_impact("nonexistent", "INE001A01036")


# ---------------------------------------------------------------------------
# Tests for ExplanationService
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_explanation_service_summary(tmp_path: Path) -> None:
    repo = BillRepository()
    repo._metadata_dir = tmp_path / "metadata"
    repo._metadata_dir.mkdir(parents=True, exist_ok=True)

    bill = Bill(
        bill_id="test-explain-bill",
        title="Finance Bill",
        year=2024,
        ministry="Ministry of Finance",
        status=BillStatus.INTRODUCED,
        house=BillHouse.LOK_SABHA,
        url="https://prsindia.org/bill/test-explain-bill",
        full_text="Budget proposals for the next fiscal year.",
    )
    repo.save(bill)

    provider = DummyLLMProvider()
    service = ExplanationService(llm_provider=provider, bill_repository=repo)

    summary = await service.summarize_bill("test-explain-bill", save_back=True)

    assert summary == "Summary of Finance Bill: Budget proposals for"

    # Verify updated summary is saved back to repo
    updated_bill = repo.get("test-explain-bill")
    assert updated_bill is not None
    assert updated_bill.summary == summary


@pytest.mark.asyncio
async def test_explanation_service_impact(tmp_path: Path) -> None:
    repo = BillRepository()
    repo._metadata_dir = tmp_path / "metadata"
    repo._metadata_dir.mkdir(parents=True, exist_ok=True)

    bill = Bill(
        bill_id="test-explain-bill",
        title="Telecom Reform Bill",
        year=2024,
        ministry="Ministry of Communications",
        status=BillStatus.INTRODUCED,
        house=BillHouse.LOK_SABHA,
        url="https://prsindia.org/bill/test-explain-bill",
    )
    repo.save(bill)

    provider = DummyLLMProvider()
    service = ExplanationService(llm_provider=provider, bill_repository=repo)

    explanation = await service.explain_market_impact(
        bill_id="test-explain-bill",
        company_name="Bharti Airtel",
        sector="Telecom",
        predicted_impact="Positive",
    )

    assert "Bharti Airtel" in explanation
    assert "Telecom" in explanation
    assert "Positive" in explanation
    assert "Telecom Reform Bill" in explanation


@pytest.mark.asyncio
async def test_explanation_service_qa(tmp_path: Path) -> None:
    repo = BillRepository()
    repo._metadata_dir = tmp_path / "metadata"
    repo._metadata_dir.mkdir(parents=True, exist_ok=True)

    bill1 = Bill(
        bill_id="bill-1",
        title="First Bill",
        year=2024,
        ministry="Ministry of Home Affairs",
        status=BillStatus.INTRODUCED,
        house=BillHouse.LOK_SABHA,
        url="https://prsindia.org/bill/bill-1",
        full_text="Context block 1",
    )
    bill2 = Bill(
        bill_id="bill-2",
        title="Second Bill",
        year=2024,
        ministry="Ministry of Finance",
        status=BillStatus.INTRODUCED,
        house=BillHouse.LOK_SABHA,
        url="https://prsindia.org/bill/bill-2",
        full_text="Context block 2",
    )
    repo.save(bill1)
    repo.save(bill2)

    provider = DummyLLMProvider()
    service = ExplanationService(llm_provider=provider, bill_repository=repo)

    answer = await service.ask_question(
        query="What is the context of these bills?",
        context_bill_ids=["bill-1", "bill-2"],
    )

    assert "First Bill" in answer or "Answer to query" in answer
    assert "Context block 1" in answer or "context length" in answer
