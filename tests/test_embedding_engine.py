"""
tests/test_embedding_engine.py
==============================
Tests for the NLP Embedding Engine (Task 5.2).

Mock-based tests covering schemas, repository, caching, validation, batch
processing, device selection, and CLI execution.
"""

from __future__ import annotations

import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd
import numpy as np

# Import settings globally (does not trigger lazy import gotchas)
from config.settings import settings

# ---------------------------------------------------------------------------
# Mock PyTorch and Transformers BEFORE importing the target modules
# ---------------------------------------------------------------------------

class MockTensor:
    def __init__(self, data):
        self.data = data

    @property
    def shape(self):
        if isinstance(self.data, list):
            if isinstance(self.data[0], list):
                return (len(self.data), len(self.data[0]))
            return (len(self.data),)
        return (1,)

    def to(self, device):
        return self

    def cpu(self):
        return self

    def tolist(self):
        # Handle conversion from 3D mock to 2D mock for pooling
        if isinstance(self.data, list) and len(self.data) > 0 and isinstance(self.data[0], list):
            if isinstance(self.data[0][0], list):
                # 3D -> 2D (batch_size, 768)
                return [[val * 10 for val in seq[0]] for seq in self.data]
            return self.data
        return self.data

    def item(self):
        return self.data

    def unsqueeze(self, dim):
        return self

    def expand(self, *args):
        return self

    def float(self):
        return self

    def size(self):
        if isinstance(self.data, list):
            if len(self.data) > 0 and isinstance(self.data[0], list):
                if isinstance(self.data[0][0], list):
                    return (len(self.data), len(self.data[0]), len(self.data[0][0]))
                return (len(self.data), len(self.data[0]))
            return (len(self.data),)
        return (1,)

    def sum(self, dim=None):
        if dim == 1:
            return MockTensor([10] * len(self.data))
        return MockTensor(10)

    def __mul__(self, other):
        return self

    def __rmul__(self, other):
        return self

    def __truediv__(self, other):
        return self

    def __rtruediv__(self, other):
        return self

    def __getitem__(self, item):
        # support slicing like [:, 0]
        if isinstance(self.data, list) and len(self.data) > 0 and isinstance(self.data[0], list):
            if isinstance(self.data[0][0], list):
                # Extract first token representation for each item in batch
                return MockTensor([seq[0] for seq in self.data])
        return self


# Create Mock modules
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = False

class MockDevice:
    def __init__(self, type_name):
        self.type = type_name
    def __str__(self):
        return self.type
    def __repr__(self):
        return self.type

mock_torch.device.side_effect = MockDevice
mock_torch.Tensor = MockTensor
mock_torch.no_grad = MagicMock

# mock clamp and sum
mock_torch.clamp = lambda tensor, min=None, max=None: tensor
mock_torch.sum = lambda tensor, dim=None: tensor

# mock torch.nn.functional
mock_f = MagicMock()
mock_f.normalize = lambda tensor, p=2, dim=1: tensor
mock_torch.nn.functional = mock_f

# Apply patches to sys.modules
sys.modules['torch'] = mock_torch
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = mock_f

# Mock Transformers
mock_transformers = MagicMock()
mock_tokenizer_inst = MagicMock()

def mock_tokenize_call(texts, **kwargs):
    num_texts = len(texts) if isinstance(texts, list) else 1
    input_ids = MockTensor([[101] * 10] * num_texts)
    attention_mask = MockTensor([[1] * 10] * num_texts)
    
    class MockEncoded:
        def __getitem__(self, key):
            if key == "input_ids":
                return input_ids
            elif key == "attention_mask":
                return attention_mask
            raise KeyError(key)
        def to(self, device):
            return self
    return MockEncoded()

mock_tokenizer_inst.side_effect = mock_tokenize_call
mock_tokenizer_inst.model_max_length = 512

mock_tokenizer_cls = MagicMock()
mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer_inst
mock_transformers.AutoTokenizer = mock_tokenizer_cls

# Mock model class
mock_model_inst = MagicMock()
mock_model_inst.to.return_value = mock_model_inst
def mock_model_call(input_ids, attention_mask):
    num_seqs = len(input_ids.data)
    embeddings = [[[0.1] * 768] * 10] * num_seqs
    return [MockTensor(embeddings)]

mock_model_inst.side_effect = mock_model_call
mock_model_cls = MagicMock()
mock_model_cls.from_pretrained.return_value = mock_model_inst
mock_transformers.AutoModel = mock_model_cls

sys.modules['transformers'] = mock_transformers

# ---------------------------------------------------------------------------
# Imports of tested components (lazy import helper for coverage)
# ---------------------------------------------------------------------------
from schemas.bill import Bill, BillHouse, BillStatus
from schemas.embedding_record import EmbeddingRecord, EmbeddingValidationReport
from main import cmd_generate_embeddings


def get_embedding_repository(*args, **kwargs):
    from storage.embedding_repository import EmbeddingRepository
    return EmbeddingRepository(*args, **kwargs)


def get_embedding_engine(*args, **kwargs):
    from models.embeddings.embedding_engine import EmbeddingEngine
    return EmbeddingEngine(*args, **kwargs)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestEmbeddingRecordSchema:
    """Test serialisation and deserialisation of EmbeddingRecord and reports."""

    def test_embedding_record_roundtrip(self):
        record = EmbeddingRecord(
            bill_id="test-bill-123",
            embedding_model="finbert",
            embedding_dimension=768,
            embedding_vector=[0.1, 0.2, 0.3],
            token_count=100,
            model_version="ProsusAI/finbert",
            generation_timestamp="2026-07-14T12:00:00Z"
        )
        dct = record.to_dict()
        parsed = EmbeddingRecord.from_dict(dct)

        assert parsed.bill_id == record.bill_id
        assert parsed.embedding_model == record.embedding_model
        assert parsed.embedding_dimension == record.embedding_dimension
        assert parsed.embedding_vector == record.embedding_vector
        assert parsed.token_count == record.token_count
        assert parsed.model_version == record.model_version
        assert parsed.generation_timestamp == record.generation_timestamp
        assert "tokens=100" in repr(record)

    def test_validation_report_roundtrip(self):
        report = EmbeddingValidationReport(
            bill_id="bad-bill",
            rejection_reason="Text is missing",
            timestamp="2026-07-14T12:00:00Z"
        )
        dct = report.to_dict()
        parsed = EmbeddingValidationReport.from_dict(dct)

        assert parsed.bill_id == report.bill_id
        assert parsed.rejection_reason == report.rejection_reason
        assert parsed.timestamp == report.timestamp
        assert parsed.severity == "ERROR"
        assert "reason='Text is missing'" in repr(report)


class TestEmbeddingRepository:
    """Test EmbeddingRepository CRUD, disk cache, Parquet and NumPy outputs."""

    def test_repository_save_load_clear(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")

        # Empty repo assertions
        assert repo.count() == 0
        assert repo.load_all() == []
        assert repo.load_numpy() is None

        # Create sample records
        rec1 = EmbeddingRecord(
            bill_id="bill-b",
            embedding_model="finbert",
            embedding_dimension=3,
            embedding_vector=[0.4, 0.5, 0.6],
            token_count=50,
            model_version="v1",
            generation_timestamp="2026-07-14"
        )
        rec2 = EmbeddingRecord(
            bill_id="bill-a",
            embedding_model="finbert",
            embedding_dimension=3,
            embedding_vector=[0.1, 0.2, 0.3],
            token_count=40,
            model_version="v1",
            generation_timestamp="2026-07-14"
        )

        # Save records - should automatically sort by bill_id (bill-a first, then bill-b)
        repo.save_many([rec1, rec2])

        assert repo.count() == 2
        assert repo.exists("bill-a")
        assert repo.exists("bill-b")
        assert not repo.exists("bill-c")

        # Verify sorted load
        loaded = repo.load_all()
        assert loaded[0].bill_id == "bill-a"
        assert loaded[1].bill_id == "bill-b"

        # Verify get
        fetched = repo.get("bill-a")
        assert fetched is not None
        assert fetched.bill_id == "bill-a"
        assert fetched.embedding_vector == [0.1, 0.2, 0.3]
        
        # Verify get non-existent
        assert repo.get("bill-c") is None

        # Verify NumPy output shape and alignment
        np_arr = repo.load_numpy()
        assert np_arr is not None
        assert np_arr.shape == (2, 3)
        # bill-a vector should be first (sorted)
        assert np.allclose(np_arr[0], [0.1, 0.2, 0.3])
        assert np.allclose(np_arr[1], [0.4, 0.5, 0.6])

        # Verify DataFrame output
        df = repo.load_dataframe()
        assert not df.empty
        assert list(df["bill_id"].values) == ["bill-a", "bill-b"]

        # Save empty list - should do nothing
        cnt = repo.save_many([])
        assert cnt == 2

        # Test clear and properties
        assert "finbert" in repr(repo)
        assert repo.model_dir.is_dir()
        repo.clear()
        assert repo.count() == 0
        assert not repo.parquet_path.is_file()
        assert not repo.npy_path.is_file()

    def test_repository_load_index_corrupt(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")
        # Write corrupted JSON to index.json
        index_file = repo.model_dir / "index.json"
        index_file.write_text("invalid json string", encoding="utf-8")
        # Loader should catch exception, log warning, and return empty set
        idx = repo._load_index()
        assert len(idx) == 0

    def test_repository_save_index_exception(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")
        repo._index = {"bill-a"}
        with patch("json.dump") as mock_dump:
            mock_dump.side_effect = IOError("Index write error")
            # Should not raise exception (caught internally and logged)
            repo._save_index()

    def test_repository_save_many_parquet_exception(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")
        rec = EmbeddingRecord(
            bill_id="bill-x",
            embedding_model="finbert",
            embedding_dimension=3,
            embedding_vector=[0.1, 0.2, 0.3],
            token_count=10,
            model_version="v1",
            generation_timestamp="now"
        )
        with patch("pandas.DataFrame.to_parquet") as mock_to_parquet:
            mock_to_parquet.side_effect = RuntimeError("Parquet write error")
            with pytest.raises(RuntimeError, match="Parquet write error"):
                repo.save_many([rec])

    def test_repository_save_many_numpy_exception(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")
        rec = EmbeddingRecord(
            bill_id="bill-x",
            embedding_model="finbert",
            embedding_dimension=3,
            embedding_vector=[0.1, 0.2, 0.3],
            token_count=10,
            model_version="v1",
            generation_timestamp="now"
        )
        with patch("numpy.save") as mock_np_save:
            mock_np_save.side_effect = IOError("NumPy save error")
            with pytest.raises(IOError, match="NumPy save error"):
                repo.save_many([rec])

    def test_repository_get_exception(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")
        repo._index = {"bill-x"}  # Mock index hit so it tries to read Parquet
        with patch("pandas.read_parquet") as mock_read_parquet:
            mock_read_parquet.side_effect = ValueError("read error")
            assert repo.get("bill-x") is None

    def test_repository_load_all_exception(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")
        # Write dummy file so load_all executes the parquet read block
        repo.parquet_path.write_text("dummy")
        with patch("pandas.read_parquet") as mock_read_parquet:
            mock_read_parquet.side_effect = ValueError("read error")
            assert repo.load_all() == []

    def test_repository_load_dataframe_exception(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")
        repo.parquet_path.write_text("dummy")
        with patch("pandas.read_parquet") as mock_read_parquet:
            mock_read_parquet.side_effect = ValueError("read error")
            df = repo.load_dataframe()
            assert df.empty

    def test_repository_load_numpy_exception(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")
        repo.npy_path.write_text("dummy")
        with patch("numpy.load") as mock_np_load:
            mock_np_load.side_effect = RuntimeError("numpy load error")
            assert repo.load_numpy() is None

    def test_repository_clear_delete_exception(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path, model_name="finbert")
        repo.parquet_path.write_text("dummy")
        with patch("pathlib.Path.unlink") as mock_unlink:
            mock_unlink.side_effect = PermissionError("Delete permission denied")
            # Should not raise exception (caught internally and logged)
            repo.clear()


class TestEmbeddingEngine:
    """Test text prioritization, device selection, pooling strategies, validation, and batching."""

    def test_init_validation(self):
        with pytest.raises(ValueError, match="Unsupported model"):
            get_embedding_engine(model_name="unsupported-model")

        with pytest.raises(ValueError, match="Unsupported pooling strategy"):
            get_embedding_engine(pooling_strategy="sum")

    def test_text_prioritization(self, tmp_path):
        engine = get_embedding_engine()
        bill = Bill(
            bill_id="test-bill",
            title="Title",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="url",
            summary="This is summary text",
            full_text="",
        )

        # Scenario 1: Only summary is available
        assert engine.select_text(bill) == "This is summary text"

        # Scenario 2: Full text and summary are available
        bill.full_text = "This is full text"
        assert engine.select_text(bill) == "This is full text"

        # Scenario 3: Bill Corpus (text_path), Full text, and summary are available
        temp_file = tmp_path / "bill_corpus.txt"
        temp_file.write_text("This is corpus text", encoding="utf-8")
        bill.text_path = str(temp_file)
        assert engine.select_text(bill) == "This is corpus text"

        # Scenario 4: None are available
        bill.summary = ""
        bill.full_text = ""
        bill.text_path = "non_existent_file.txt"
        assert engine.select_text(bill) is None

    def test_load_model_device_selection(self):
        engine = get_embedding_engine()
        
        # Test GPU selection
        with patch("torch.cuda.is_available") as mock_cuda:
            mock_cuda.return_value = True
            engine.load_model()
            assert str(engine._device) == "cuda"
        
        # Test CPU selection
        engine._model = None # Reset
        with patch("torch.cuda.is_available") as mock_cuda:
            mock_cuda.return_value = False
            engine.load_model()
            assert str(engine._device) == "cpu"

    def test_validation_rejects(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path)
        engine = get_embedding_engine(repository=repo)

        # 1. Missing text validation
        bill_missing_text = Bill(
            bill_id="bill-no-text",
            title="Title",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="url",
        )
        records, reports = engine.process_batch([bill_missing_text])
        assert len(records) == 0
        assert len(reports) == 1
        assert "missing or empty" in reports[0].rejection_reason

        # 2. Dimensions mismatch validation
        # Create a mock vector validation error by manually calling _validate_vector
        # settings.EMBEDDING_DIMENSIONS["finbert"] is 768. Pass a 3-dim vector.
        report = engine._validate_vector("test-bill", [0.1, 0.2, 0.3], 10)
        assert report is not None
        assert "dimension" in report.rejection_reason

        # 3. Empty vector validation
        report = engine._validate_vector("test-bill", [], 10)
        assert report is not None
        assert "empty" in report.rejection_reason

        # 4. NaN / Inf validation
        report = engine._validate_vector("test-bill", [float("nan")] * 768, 10)
        assert report is not None
        assert "NaN" in report.rejection_reason

        report = engine._validate_vector("test-bill", [float("inf")] * 768, 10)
        assert report is not None
        assert "Inf" in report.rejection_reason

    def test_process_batch_e2e_caching(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path)
        engine = get_embedding_engine(repository=repo, pooling_strategy="mean")

        bill = Bill(
            bill_id="bill-1",
            title="Title",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="url",
            summary="Legislative summary description for bill 1.",
        )

        # First run: Generates and caches
        records, reports = engine.process_batch([bill])
        assert len(records) == 1
        assert len(reports) == 0
        assert records[0].bill_id == "bill-1"
        assert len(records[0].embedding_vector) == 768
        assert repo.exists("bill-1")

        # Second run: Cache hit, skips generation (returns empty, but still in repo)
        records_cached, reports_cached = engine.process_batch([bill])
        assert len(records_cached) == 0
        assert len(reports_cached) == 0

        # Third run with force_refresh: Overwrites cache
        records_refreshed, reports_refreshed = engine.process_batch([bill], force_refresh=True)
        assert len(records_refreshed) == 1
        assert len(reports_refreshed) == 0

    def test_pooling_cls_strategy(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path)
        engine = get_embedding_engine(repository=repo, pooling_strategy="cls")

        bill = Bill(
            bill_id="bill-cls",
            title="Title",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="url",
            summary="Legislative summary description.",
        )

        records, reports = engine.process_batch([bill])
        assert len(records) == 1
        assert len(reports) == 0
        assert records[0].embedding_dimension == 768

    def test_load_model_exception(self):
        engine = get_embedding_engine()
        with patch("transformers.AutoModel.from_pretrained") as mock_from_pretrained:
            mock_from_pretrained.side_effect = RuntimeError("HF unreachable")
            with pytest.raises(RuntimeError, match="Could not load Hugging Face model"):
                engine.load_model()

    def test_repository_property(self):
        engine = get_embedding_engine()
        assert engine.repository is not None

    def test_batch_inference_exception(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path)
        engine = get_embedding_engine(repository=repo)

        bill = Bill(
            bill_id="bill-exception",
            title="Title",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="url",
            summary="This summary triggers batch inference.",
        )

        # Force forward pass to raise exception
        mock_model_inst.side_effect = RuntimeError("Batch inference failed")

        records, reports = engine.process_batch([bill])
        assert len(records) == 0
        assert len(reports) == 1
        assert "inference exception" in reports[0].rejection_reason

        # Restore side effect
        def mock_model_call(input_ids, attention_mask):
            num_seqs = len(input_ids.data)
            embeddings = [[[0.1] * 768] * 10] * num_seqs
            return [MockTensor(embeddings)]
        mock_model_inst.side_effect = mock_model_call

    def test_batch_validation_fails(self, tmp_path):
        repo = get_embedding_repository(embeddings_dir=tmp_path)
        engine = get_embedding_engine(repository=repo)

        bill = Bill(
            bill_id="bill-bad-vector",
            title="Title",
            house=BillHouse.LOK_SABHA,
            status=BillStatus.INTRODUCED,
            url="url",
            summary="Summary to generate NaN vector.",
        )

        # Force mock model forward pass to return embeddings with NaN
        def mock_model_call_nan(input_ids, attention_mask):
            num_seqs = len(input_ids.data)
            # 3D list (batch_size, 10, 768) filled with float('nan')
            embeddings = [[[float('nan')] * 768] * 10] * num_seqs
            return [MockTensor(embeddings)]
        
        mock_model_inst.side_effect = mock_model_call_nan

        records, reports = engine.process_batch([bill])
        assert len(records) == 0
        assert len(reports) == 1
        assert "NaN or Inf" in reports[0].rejection_reason

        # Restore side effect
        def mock_model_call(input_ids, attention_mask):
            num_seqs = len(input_ids.data)
            embeddings = [[[0.1] * 768] * 10] * num_seqs
            return [MockTensor(embeddings)]
        mock_model_inst.side_effect = mock_model_call


class TestCLIIntegration:
    """Test CLI execution and handling of missing features dataset."""

    def test_cmd_generate_embeddings_missing_parquet(self, tmp_path):
        with patch("models.embeddings.embedding_engine.EmbeddingEngine") as mock_engine_cls:
            # Temporarily point settings.FEATURES_DIR to a dummy dir
            original_dir = settings.FEATURES_DIR
            settings.FEATURES_DIR = tmp_path

            class Args:
                model = "finbert"
                pooling = "mean"
                force_refresh = False
                batch_size = 16

            args = Args()
            res = cmd_generate_embeddings(args)
            assert res == 1  # Fails because Parquet dataset is missing

            # Restore
            settings.FEATURES_DIR = original_dir

    def test_cmd_generate_embeddings_success(self, tmp_path):
        with patch("models.embeddings.embedding_engine.EmbeddingEngine") as mock_engine_cls, \
             patch("pandas.read_parquet") as mock_read_parquet, \
             patch("storage.bill_repository.BillRepository") as mock_bill_repo_cls:

            # Mock features dataset dataframe
            df = pd.DataFrame({"bill_id": ["bill-1", "bill-2"]})
            mock_read_parquet.return_value = df

            # Mock BillRepository
            mock_bill_repo = MagicMock()
            bill_obj = Bill(
                bill_id="bill-1",
                title="Title",
                house=BillHouse.LOK_SABHA,
                status=BillStatus.INTRODUCED,
                url="url",
                summary="Text summary",
            )
            mock_bill_repo.get.side_effect = lambda bid: bill_obj if bid == "bill-1" else None
            mock_bill_repo_cls.return_value = mock_bill_repo

            # Mock EmbeddingEngine
            mock_engine = MagicMock()
            mock_engine._hf_model_id = "ProsusAI/finbert"
            # Mock process_batch output
            records = [
                EmbeddingRecord(
                    bill_id="bill-1",
                    embedding_model="finbert",
                    embedding_dimension=768,
                    embedding_vector=[0.1] * 768,
                    token_count=10,
                    model_version="v1",
                    generation_timestamp="now"
                )
            ]
            reports = [
                EmbeddingValidationReport(
                    bill_id="bill-2",
                    rejection_reason="Missing bill metadata",
                    timestamp="now"
                )
            ]
            mock_engine.process_batch.return_value = (records, reports)
            mock_engine_cls.return_value = mock_engine

            # Mock path check
            original_dir = settings.FEATURES_DIR
            settings.FEATURES_DIR = tmp_path
            # Create dummy parquet file to bypass check
            dummy_parquet = tmp_path / f"{settings.FEATURE_DATASET_NAME}.parquet"
            dummy_parquet.write_text("dummy")

            class Args:
                model = "finbert"
                pooling = "mean"
                force_refresh = False
                batch_size = 16

            args = Args()
            res = cmd_generate_embeddings(args)
            assert res == 0

            # Restore
            settings.FEATURES_DIR = original_dir

    def test_cmd_generate_embeddings_empty_dataset(self, tmp_path):
        with patch("pandas.read_parquet") as mock_read_parquet:
            # Mock empty features dataset
            df = pd.DataFrame()
            mock_read_parquet.return_value = df

            original_dir = settings.FEATURES_DIR
            settings.FEATURES_DIR = tmp_path
            dummy_parquet = tmp_path / f"{settings.FEATURE_DATASET_NAME}.parquet"
            dummy_parquet.write_text("dummy")

            class Args:
                model = "finbert"
                pooling = "mean"
                force_refresh = False
                batch_size = 16

            args = Args()
            res = cmd_generate_embeddings(args)
            assert res == 0

            # Restore
            settings.FEATURES_DIR = original_dir
