"""
tests/test_task_8_26_live_intelligence.py
==========================================
Task 8.26 — Live Legislative Intelligence & Automatic Update Pipeline.

Test suite covering:
1.  LiveStatus enum completeness
2.  AnalyticalModelStatus enum completeness
3.  SourceCategory enum completeness
4.  LiveKnowledgeRecord default analytical_model_status = KNOWLEDGE_ONLY
5.  LiveKnowledgeRecord.assert_not_frozen_model() raises on MODELLED
6.  LiveKnowledgeRecord.assert_not_frozen_model() passes on KNOWLEDGE_ONLY
7.  LiveKnowledgeRecord to_dict / from_dict round-trip
8.  LiveKnowledgeRecord: from_dict never silently sets MODELLED
9.  LiveKnowledgeRepository.upsert() persists a record
10. LiveKnowledgeRepository: firewall blocks upsert of MODELLED record
11. LiveKnowledgeRepository.get() returns correct record
12. LiveKnowledgeRepository.get_by_canonical_bill_id() index lookup
13. LiveKnowledgeRepository.get_by_bill_number() index lookup
14. LiveKnowledgeRepository.mark_retrieval_failure() increments failures
15. LiveKnowledgeRepository.update_live_status() transitions correctly
16. LiveKnowledgeRepository.list_records() pagination
17. LiveKnowledgeRepository.list_records() filter by live_status
18. LiveKnowledgeRepository.get_stats() returns correct totals
19. SourceURLValidator: blocks localhost
20. SourceURLValidator: blocks private IP range
21. SourceURLValidator: blocks cloud metadata endpoint
22. SourceURLValidator: blocks embedded credentials
23. SourceURLValidator: blocks non-http scheme (ftp://)
24. SourceURLValidator: allows known legislative domain
25. SourceURLValidator: classify_domain() returns KNOWN_LEGISLATIVE
26. MonitoringSource has authority_name and source_category fields
27. UpdateProcessor creates LiveKnowledgeRecord on NEW_BILL (central)
28. UpdateProcessor creates LiveKnowledgeRecord on NEW_BILL (state)
29. UpdateProcessor NEW_BILL result contains 'live_knowledge_record_created'
30. UpdateProcessor: created record is always KNOWLEDGE_ONLY, not MODELLED
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from schemas.monitoring import (
    AnalyticalModelStatus,
    ChangeEvent,
    ChangeEventType,
    LiveKnowledgeRecord,
    LiveStatus,
    MonitoringSource,
    SourceCategory,
    SourceStatus,
)
from services.monitoring.source_url_validator import (
    SourceURLValidator,
    URLValidationError,
)
from storage.live_knowledge_repository import LiveKnowledgeRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_record(**kwargs) -> LiveKnowledgeRecord:
    defaults = {
        "title": "Test Bill 2026",
        "jurisdiction": "central",
        "discovered_by_source_id": "central_lok_sabha",
    }
    defaults.update(kwargs)
    return LiveKnowledgeRecord(**defaults)


def _make_new_bill_event(jurisdiction: str = "central", state=None) -> ChangeEvent:
    return ChangeEvent(
        event_type=ChangeEventType.NEW_BILL,
        bill_id="test_bill_2026",
        bill_title="Test Finance Bill 2026",
        jurisdiction=jurisdiction,
        state=state,
        source_id="central_lok_sabha" if jurisdiction == "central" else "state_kerala",
        new_value={
            "title": "Test Finance Bill 2026",
            "bill_number": "TB-2026-001",
            "status": "Introduced",
            "source_url": "https://loksabha.nic.in/bills/tb2026.html",
        },
    )


# ===========================================================================
# 1–3: Enum completeness
# ===========================================================================


class TestEnumCompleteness(unittest.TestCase):

    # Test 1
    def test_live_status_has_required_values(self):
        required = {"DISCOVERED", "VERIFIED", "UPDATED", "WITHDRAWN",
                    "SUPERSEDED", "UNKNOWN", "KNOWLEDGE_ONLY"}
        actual = {v.value for v in LiveStatus}
        self.assertEqual(required, actual)

    # Test 2
    def test_analytical_model_status_has_required_values(self):
        required = {"MODELLED", "KNOWLEDGE_ONLY", "PENDING_REVIEW", "NOT_ELIGIBLE"}
        actual = {v.value for v in AnalyticalModelStatus}
        self.assertEqual(required, actual)

    # Test 3
    def test_source_category_has_required_values(self):
        required = {"CENTRAL", "STATE", "GAZETTE", "PARLIAMENTARY",
                    "LEGISLATIVE_DEPARTMENT", "OTHER_AUTHORITATIVE", "NEWS_MEDIA"}
        actual = {v.value for v in SourceCategory}
        self.assertEqual(required, actual)


# ===========================================================================
# 4–8: LiveKnowledgeRecord defaults and firewall
# ===========================================================================


class TestLiveKnowledgeRecordFirewall(unittest.TestCase):

    # Test 4
    def test_default_analytical_model_status_is_knowledge_only(self):
        record = _make_record()
        self.assertEqual(record.analytical_model_status, AnalyticalModelStatus.KNOWLEDGE_ONLY.value)

    # Test 5
    def test_assert_not_frozen_model_raises_on_modelled(self):
        record = _make_record(analytical_model_status=AnalyticalModelStatus.MODELLED.value)
        with self.assertRaises(ValueError) as ctx:
            record.assert_not_frozen_model()
        self.assertIn("Task 8.26 firewall violation", str(ctx.exception))

    # Test 6
    def test_assert_not_frozen_model_passes_on_knowledge_only(self):
        record = _make_record()
        # Should not raise
        record.assert_not_frozen_model()

    # Test 7
    def test_to_dict_from_dict_round_trip(self):
        original = _make_record(
            title="Finance Bill 2026",
            bill_number="FB-2026-03",
            jurisdiction="central",
            live_status=LiveStatus.VERIFIED.value,
            document_hash_sha256="abc123",
        )
        restored = LiveKnowledgeRecord.from_dict(original.to_dict())
        self.assertEqual(restored.record_id, original.record_id)
        self.assertEqual(restored.title, original.title)
        self.assertEqual(restored.live_status, original.live_status)
        self.assertEqual(restored.analytical_model_status, AnalyticalModelStatus.KNOWLEDGE_ONLY.value)
        self.assertEqual(restored.document_hash_sha256, "abc123")

    # Test 8
    def test_from_dict_does_not_silently_set_modelled(self):
        # Simulate a corrupt data store that somehow has MODELLED
        data = {
            "record_id": "test-id",
            "title": "Corrupt Record",
            "jurisdiction": "central",
            "discovered_by_source_id": "src1",
            # No analytical_model_status key at all
        }
        record = LiveKnowledgeRecord.from_dict(data)
        # from_dict defaults to KNOWLEDGE_ONLY when key absent
        self.assertEqual(record.analytical_model_status, AnalyticalModelStatus.KNOWLEDGE_ONLY.value)


# ===========================================================================
# 9–18: LiveKnowledgeRepository
# ===========================================================================


class TestLiveKnowledgeRepository(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.repo = LiveKnowledgeRepository(storage_dir=Path(self._tmpdir.name))

    def tearDown(self):
        self._tmpdir.cleanup()

    # Test 9
    def test_upsert_persists_record(self):
        record = _make_record(bill_number="B-001")
        saved = self.repo.upsert(record)
        self.assertEqual(saved.record_id, record.record_id)
        rec_path = self.repo._records_dir / f"{record.record_id}.json"
        self.assertTrue(rec_path.exists())

    # Test 10
    def test_firewall_blocks_upsert_of_modelled_record(self):
        record = _make_record(analytical_model_status=AnalyticalModelStatus.MODELLED.value)
        with self.assertRaises(ValueError):
            self.repo.upsert(record)

    # Test 11
    def test_get_returns_correct_record(self):
        record = _make_record(title="Energy Bill 2026")
        self.repo.upsert(record)
        fetched = self.repo.get(record.record_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Energy Bill 2026")

    # Test 12
    def test_get_by_canonical_bill_id(self):
        record = _make_record(canonical_bill_id="IND-CENTRAL-2026-042")
        self.repo.upsert(record)
        fetched = self.repo.get_by_canonical_bill_id("IND-CENTRAL-2026-042")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.record_id, record.record_id)

    # Test 13
    def test_get_by_bill_number(self):
        record = _make_record(bill_number="LB-2026-007")
        self.repo.upsert(record)
        fetched = self.repo.get_by_bill_number("LB-2026-007")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.record_id, record.record_id)

    # Test 14
    def test_mark_retrieval_failure_increments(self):
        record = _make_record(document_url="https://loksabha.nic.in/doc.pdf")
        self.repo.upsert(record)
        updated = self.repo.mark_retrieval_failure(record.record_id, "HTTP 503")
        self.assertIsNotNone(updated)
        self.assertEqual(updated.document_retrieval_failures, 1)
        self.assertEqual(updated.document_retrieval_last_error, "HTTP 503")
        # Second failure
        updated2 = self.repo.mark_retrieval_failure(record.record_id, "Timeout")
        self.assertEqual(updated2.document_retrieval_failures, 2)

    # Test 15
    def test_update_live_status(self):
        record = _make_record()
        self.repo.upsert(record)
        updated = self.repo.update_live_status(
            record.record_id,
            LiveStatus.VERIFIED,
            verification_source_id="central_lok_sabha",
        )
        self.assertIsNotNone(updated)
        self.assertEqual(updated.live_status, LiveStatus.VERIFIED.value)
        self.assertIsNotNone(updated.verified_at)
        self.assertEqual(updated.verification_source_id, "central_lok_sabha")

    # Test 16
    def test_list_records_pagination(self):
        for i in range(5):
            self.repo.upsert(_make_record(title=f"Bill {i}"))
        records, total = self.repo.list_records(limit=3, offset=0)
        self.assertEqual(total, 5)
        self.assertEqual(len(records), 3)
        records2, total2 = self.repo.list_records(limit=3, offset=3)
        self.assertEqual(total2, 5)
        self.assertEqual(len(records2), 2)

    # Test 17
    def test_list_records_filter_by_live_status(self):
        r1 = _make_record(live_status=LiveStatus.DISCOVERED.value)
        r2 = _make_record(live_status=LiveStatus.VERIFIED.value)
        self.repo.upsert(r1)
        self.repo.upsert(r2)
        discovered, total = self.repo.list_records(live_status=LiveStatus.DISCOVERED.value)
        self.assertEqual(total, 1)
        self.assertEqual(discovered[0].live_status, LiveStatus.DISCOVERED.value)

    # Test 18
    def test_get_stats_returns_correct_totals(self):
        for _ in range(3):
            self.repo.upsert(_make_record())
        stats = self.repo.get_stats()
        self.assertEqual(stats["total_records"], 3)
        self.assertIn("KNOWLEDGE_ONLY", stats.get("by_analytical_model_status", {}))
        self.assertEqual(stats["by_analytical_model_status"]["KNOWLEDGE_ONLY"], 3)


# ===========================================================================
# 19–25: SourceURLValidator / SSRF
# ===========================================================================


class TestSourceURLValidator(unittest.TestCase):

    def setUp(self):
        self.v = SourceURLValidator(enforce_allowlist=False)

    # Test 19
    def test_blocks_localhost(self):
        with self.assertRaises(URLValidationError):
            self.v.validate("http://localhost/exploit")

    # Test 20
    def test_blocks_private_ip(self):
        with self.assertRaises(URLValidationError):
            self.v.validate("http://192.168.1.100/bills")

    # Test 21
    def test_blocks_cloud_metadata_endpoint(self):
        with self.assertRaises(URLValidationError):
            self.v.validate("http://169.254.169.254/latest/meta-data/")

    # Test 22
    def test_blocks_embedded_credentials(self):
        with self.assertRaises(URLValidationError):
            self.v.validate("https://user:pass@loksabha.nic.in/bills")

    # Test 23
    def test_blocks_non_http_scheme(self):
        with self.assertRaises(URLValidationError):
            self.v.validate("ftp://loksabha.nic.in/bills")

    # Test 24
    def test_allows_known_legislative_domain(self):
        url = "https://loksabha.nic.in/bills/billsintroduced.aspx"
        result = self.v.validate(url)
        self.assertEqual(result, url)

    # Test 25
    def test_classify_domain_known_legislative(self):
        result = self.v.classify_domain("https://egazette.nic.in/gazette/default.aspx")
        self.assertEqual(result, "KNOWN_LEGISLATIVE")


# ===========================================================================
# 26: MonitoringSource Task 8.26 fields
# ===========================================================================


class TestMonitoringSourceTask826(unittest.TestCase):

    # Test 26
    def test_monitoring_source_has_8_26_fields(self):
        source = MonitoringSource(
            source_id="test_src",
            jurisdiction="central",
            state=None,
            source_name="Test Source",
            source_url="https://loksabha.nic.in/bills",
            adapter="central_monitor",
            authority_name="Lok Sabha, Parliament of India",
            source_category=SourceCategory.PARLIAMENTARY.value,
            health_status="HEALTHY",
        )
        self.assertEqual(source.authority_name, "Lok Sabha, Parliament of India")
        self.assertEqual(source.source_category, SourceCategory.PARLIAMENTARY.value)
        self.assertEqual(source.health_status, "HEALTHY")

        # Round-trip to_dict / from_dict
        d = source.to_dict()
        self.assertIn("authority_name", d)
        self.assertIn("source_category", d)
        self.assertIn("health_status", d)
        restored = MonitoringSource.from_dict(d)
        self.assertEqual(restored.authority_name, "Lok Sabha, Parliament of India")
        self.assertEqual(restored.source_category, SourceCategory.PARLIAMENTARY.value)


# ===========================================================================
# 27–30: UpdateProcessor integration
# ===========================================================================


class TestUpdateProcessorTask826(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        from storage.monitoring_repository import MonitoringRepository
        from services.monitoring.update_processor import UpdateProcessor
        self._monitoring_repo = MagicMock(spec=MonitoringRepository)
        self._live_repo = LiveKnowledgeRepository(storage_dir=Path(self._tmpdir.name))
        self._processor = UpdateProcessor(
            monitoring_repo=self._monitoring_repo,
            live_knowledge_repo=self._live_repo,
        )

    def tearDown(self):
        self._tmpdir.cleanup()

    # Test 27
    def test_new_bill_central_creates_live_knowledge_record(self):
        event = _make_new_bill_event(jurisdiction="central")
        self._processor.process(event)
        records, total = self._live_repo.list_records()
        self.assertEqual(total, 1)
        self.assertEqual(records[0].jurisdiction, "central")

    # Test 28
    def test_new_bill_state_creates_live_knowledge_record(self):
        event = _make_new_bill_event(jurisdiction="state", state="Kerala")
        self._processor.process(event)
        records, total = self._live_repo.list_records()
        self.assertEqual(total, 1)
        self.assertEqual(records[0].jurisdiction, "state")
        self.assertEqual(records[0].state, "Kerala")

    # Test 29
    def test_new_bill_result_contains_live_record_created_action(self):
        event = _make_new_bill_event(jurisdiction="central")
        result = self._processor.process(event)
        self.assertIn("live_knowledge_record_created", result.get("actions", []))

    # Test 30
    def test_new_bill_live_record_is_always_knowledge_only_not_modelled(self):
        event = _make_new_bill_event(jurisdiction="central")
        self._processor.process(event)
        records, total = self._live_repo.list_records()
        self.assertEqual(total, 1)
        record = records[0]
        self.assertEqual(record.analytical_model_status, AnalyticalModelStatus.KNOWLEDGE_ONLY.value)
        self.assertNotEqual(record.analytical_model_status, AnalyticalModelStatus.MODELLED.value)
        # Firewall assertion must pass (no violation)
        record.assert_not_frozen_model()


if __name__ == "__main__":
    unittest.main(verbosity=2)
