"""
models/embeddings/embedding_engine.py
======================================
NLP Embedding Engine (Task 5.2).

Generates reusable text embeddings for legislative bills using FinBERT or Legal-RoBERTa.
Supports CPU/GPU selection, batching, caching, and pooling configurations.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

from config.logging_config import get_logger
from schemas.bill import Bill
from schemas.embedding_record import EmbeddingRecord, EmbeddingValidationReport
from storage.embedding_repository import EmbeddingRepository

logger = get_logger(__name__)


class EmbeddingEngine:
    """
    Orchestrates tokenisation, transformer inference, pooling, and validation
    to generate reusable text embeddings for legislative bills.

    Parameters
    ----------
    model_name : str, optional
        User-friendly name of the model ('finbert' or 'legal-roberta').
        Defaults to settings.DEFAULT_EMBEDDING_MODEL.
    pooling_strategy : str, optional
        Pooling method ('mean' or 'cls'). Defaults to settings.DEFAULT_POOLING_STRATEGY.
    repository : EmbeddingRepository, optional
        Repository instance for cache and persistence.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        pooling_strategy: Optional[str] = None,
        repository: Optional[EmbeddingRepository] = None,
    ) -> None:
        from config.settings import settings

        self._model_name: str = (model_name or settings.DEFAULT_EMBEDDING_MODEL).strip().lower()
        self._pooling_strategy: str = (pooling_strategy or settings.DEFAULT_POOLING_STRATEGY).strip().lower()

        if self._model_name not in settings.MODEL_MAPPING:
            raise ValueError(
                f"Unsupported model: '{self._model_name}'. "
                f"Choose from: {list(settings.MODEL_MAPPING.keys())}"
            )

        if self._pooling_strategy not in {"mean", "cls"}:
            raise ValueError(f"Unsupported pooling strategy: '{self._pooling_strategy}'. Use 'mean' or 'cls'.")

        self._hf_model_id = settings.MODEL_MAPPING[self._model_name]
        self._expected_dim = settings.EMBEDDING_DIMENSIONS[self._model_name]

        # Init repository
        self._repository = repository or EmbeddingRepository(model_name=self._model_name)

        # PyTorch / Transformers model and tokenizer references (loaded lazily)
        self._tokenizer = None
        self._model = None
        self._device = None

        logger.debug(
            "EmbeddingEngine initialised | model=%s HF_id=%s pooling=%s",
            self._model_name,
            self._hf_model_id,
            self._pooling_strategy,
        )

    def load_model(self) -> None:
        """
        Lazily load the tokenizer and model onto the appropriate device (GPU or CPU fallback).
        """
        if self._model is not None:
            return

        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            logger.error("PyTorch or Hugging Face Transformers is not installed.")
            raise ImportError(
                "PyTorch and Hugging Face Transformers are required for the NLP Embedding Engine. "
                "Ensure 'torch' and 'transformers' are installed in the environment."
            ) from exc

        logger.info("Loading NLP model '%s' (%s)...", self._model_name, self._hf_model_id)

        # Device selection
        if torch.cuda.is_available():
            self._device = torch.device("cuda")
            logger.info("GPU available. Using CUDA device.")
        else:
            self._device = torch.device("cpu")
            logger.info("GPU not available. Falling back to CPU.")

        # Load tokenizer and model
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self._hf_model_id)
            self._model = AutoModel.from_pretrained(self._hf_model_id).to(self._device)
            self._model.eval()  # Set to evaluation mode
        except Exception as exc:
            logger.error("Failed to load model from Hugging Face Hub: %s", exc)
            raise RuntimeError(f"Could not load Hugging Face model: {self._hf_model_id}") from exc

        logger.info("Model '%s' loaded successfully.", self._model_name)

    def select_text(self, bill: Bill) -> Optional[str]:
        """
        Extract text from the bill using priority rules:
        1. Bill Corpus (from local text file, read via bill.text_path)
        2. Full Bill Text (from bill.full_text)
        3. Bill Summary (from bill.summary)

        Parameters
        ----------
        bill : Bill
            The bill record.

        Returns
        -------
        str | None
            The text content to embed, or None if no text is available.
        """
        # 1. Bill Corpus
        if bill.text_path:
            from config.settings import settings
            p = Path(bill.text_path)
            if not p.is_absolute():
                p = settings.PROJECT_ROOT / p

            if p.is_file():
                try:
                    text = p.read_text(encoding="utf-8").strip()
                    if text:
                        logger.debug("Bill '%s': Selected text from Bill Corpus (%s)", bill.bill_id, p)
                        return text
                except Exception as exc:
                    logger.warning("Failed to read bill text from text_path %s: %s", p, exc)

        # 2. Full Bill Text
        if bill.full_text and bill.full_text.strip():
            logger.debug("Bill '%s': Selected text from Full Bill Text", bill.bill_id)
            return bill.full_text.strip()

        # 3. Bill Summary
        if bill.summary and bill.summary.strip():
            logger.debug("Bill '%s': Selected text from Bill Summary", bill.bill_id)
            return bill.summary.strip()

        logger.warning("Bill '%s': No legislative text or summary available.", bill.bill_id)
        return None

    def _validate_vector(
        self, bill_id: str, vector: list[float], token_count: int
    ) -> Optional[EmbeddingValidationReport]:
        """
        Validate the generated embedding vector.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Reject empty embedding
        if not vector:
            return EmbeddingValidationReport(
                bill_id=bill_id,
                rejection_reason="Generated embedding vector is empty",
                timestamp=timestamp,
            )

        # Reject incorrect dimension
        if len(vector) != self._expected_dim:
            return EmbeddingValidationReport(
                bill_id=bill_id,
                rejection_reason=(
                    f"Incorrect embedding dimension: expected {self._expected_dim}, got {len(vector)}"
                ),
                timestamp=timestamp,
            )

        # Reject NaN / Inf values
        for val in vector:
            if math.isnan(val) or math.isinf(val):
                return EmbeddingValidationReport(
                    bill_id=bill_id,
                    rejection_reason="Embedding vector contains NaN or Inf values",
                    timestamp=timestamp,
                )

        return None

    def process_batch(
        self,
        bills: list[Bill],
        force_refresh: bool = False,
        batch_size: int = 16,
    ) -> tuple[list[EmbeddingRecord], list[EmbeddingValidationReport]]:
        """
        Generate embeddings for a batch of bills.
        Skips bills that are already cached in the repository, unless force_refresh is True.

        Parameters
        ----------
        bills : list[Bill]
            Legislative bills to process.
        force_refresh : bool, optional
            Force regeneration, overriding disk cache.
        batch_size : int, optional
            Batch size for model inference.

        Returns
        -------
        tuple[list[EmbeddingRecord], list[EmbeddingValidationReport]]
            Lists of generated EmbeddingRecord and ValidationReport objects.
        """
        import torch
        import torch.nn.functional as F

        all_records: list[EmbeddingRecord] = []
        all_reports: list[EmbeddingValidationReport] = []

        # 1. Filter bills to process (skip cache hits)
        to_process: list[Bill] = []
        for bill in bills:
            if self._repository.exists(bill.bill_id) and not force_refresh:
                logger.debug("Bill '%s': Cache hit. Skipping embedding generation.", bill.bill_id)
                continue
            to_process.append(bill)

        if not to_process:
            logger.info("All bills already cached. No embeddings to generate.")
            return [], []

        # 2. Extract texts and handle missing texts
        bills_with_text: list[tuple[Bill, str]] = []
        for bill in to_process:
            text = self.select_text(bill)
            if not text:
                report = EmbeddingValidationReport(
                    bill_id=bill.bill_id,
                    rejection_reason="Bill legislative text is missing or empty",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
                all_reports.append(report)
                logger.error("Bill '%s' validation failed: text missing.", bill.bill_id)
            else:
                bills_with_text.append((bill, text))

        if not bills_with_text:
            return [], all_reports

        # 3. Load model if we have bills to process
        self.load_model()

        # 4. Batch inference
        num_bills = len(bills_with_text)
        logger.info("Generating embeddings for %d bills in batches of %d...", num_bills, batch_size)

        for i in range(0, num_bills, batch_size):
            batch = bills_with_text[i : i + batch_size]
            batch_bills = [item[0] for item in batch]
            batch_texts = [item[1] for item in batch]

            logger.info("Processing batch %d/%d (size=%d)...", (i // batch_size) + 1, math.ceil(num_bills / batch_size), len(batch))

            try:
                # Tokenize batch
                encoded = self._tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors="pt",
                ).to(self._device)

                input_ids = encoded["input_ids"]
                attention_mask = encoded["attention_mask"]
                token_counts = attention_mask.sum(dim=1).cpu().tolist()

                # Model forward pass
                with torch.no_grad():
                    outputs = self._model(input_ids=input_ids, attention_mask=attention_mask)

                # Pooling
                token_embeddings = outputs[0]  # First element has hidden states

                if self._pooling_strategy == "mean":
                    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
                    sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
                    sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                    pooled = sum_embeddings / sum_mask
                else:
                    # CLS pooling
                    pooled = token_embeddings[:, 0]

                # Normalize (L2)
                normalized = F.normalize(pooled, p=2, dim=1)
                embeddings = normalized.cpu().tolist()

                # Create records & Validate
                timestamp = datetime.now(timezone.utc).isoformat()
                for idx, bill in enumerate(batch_bills):
                    vector = embeddings[idx]
                    token_count = int(token_counts[idx])

                    val_report = self._validate_vector(bill.bill_id, vector, token_count)
                    if val_report:
                        all_reports.append(val_report)
                        logger.error("Bill '%s' validation failed: %s", bill.bill_id, val_report.rejection_reason)
                    else:
                        record = EmbeddingRecord(
                            bill_id=bill.bill_id,
                            embedding_model=self._model_name,
                            embedding_dimension=self._expected_dim,
                            embedding_vector=vector,
                            token_count=token_count,
                            model_version=self._hf_model_id,
                            generation_timestamp=timestamp,
                        )
                        all_records.append(record)

            except Exception as exc:
                logger.error("Failed model inference for batch starting at index %d: %s", i, exc, exc_info=True)
                # Fail batch records gracefully
                for bill in batch_bills:
                    all_reports.append(
                        EmbeddingValidationReport(
                            bill_id=bill.bill_id,
                            rejection_reason=f"Model inference exception: {exc}",
                            timestamp=datetime.now(timezone.utc).isoformat(),
                        )
                    )

        # 5. Save successfully generated records to repository
        if all_records:
            self._repository.save_many(all_records)

        logger.info(
            "Embedding run finished. Generated: %d, Rejected: %d",
            len(all_records),
            len(all_reports),
        )
        return all_records, all_reports

    @property
    def repository(self) -> EmbeddingRepository:
        """The associated embedding repository."""
        return self._repository
