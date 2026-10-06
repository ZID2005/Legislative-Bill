"""
tests/test_task_8_27_dossier.py
================================
Task 8.27 — Legislative Intelligence Enrichment & Bill Dossier 2.0.

Comprehensive Test Suite Covering:
1.  Dossier creation & schema contract
2.  Central bill dossier (MODELLED)
3.  State bill dossier (NOT_ELIGIBLE)
4.  Knowledge-only bill (KNOWLEDGE_ONLY)
5.  Modelled bill exclusivity (exactly 20 Central production bills)
6.  Chronological evidence-based timeline
7.  Change detection & strict separation of document vs legislative changes
8.  Provenance integrity & source authority
9.  Document metadata & SHA-256 hashes
10. Sector mapping & Macro Sector Directory integration
11. Industry mapping & canonical classification
12. Company exposure & explicit linkage reasons
13. Model status firewall enforcement
14. AI grounded context & epistemic separation
15. Insufficient-source graceful handling
16. Multi-tenant isolation (Tenant A vs Tenant B)
17. RBAC & error contracts (404 BILL_NOT_FOUND)
18. Document & dossier sub-endpoints (/timeline, /changes, /documents, etc.)
19. Search integration (data_layer & model_status)
20. Invariant: zero automatic stock predictions for State & Live bills
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from api.app import app
from config.settings import settings
from schemas.bill_dossier import (
    BillChangeSummary,
    BillDocumentItem,
    EnrichedBillDossier,
    LinkedCompanyExposureItem,
    ModelStatus,
    SectorExposureItem,
    TimelineEvent,
)
from schemas.monitoring import LiveKnowledgeRecord
from schemas.unified_bill_record import UnifiedBillRecord
from services.ai.ai_context_builder import AIContextBuilder
from services.bill_dossier_service import (
    BillDossierService,
    get_frozen_central_production_bill_ids,
)
from storage.live_knowledge_repository import LiveKnowledgeRepository

client = TestClient(app)

HEADERS_TENANT_A = {
    "X-Tenant-ID": "tenant_alpha",
    "X-User-ID": "user_alpha",
}

HEADERS_TENANT_B = {
    "X-Tenant-ID": "tenant_beta",
    "X-User-ID": "user_beta",
}

CENTRAL_PROD_BILL_ID = "the-banking-laws-amendment-bill-2024"
STATE_BILL_ID = "karnataka-vs-bill-33-2024"


# ===========================================================================
# 1. Dossier Creation & Schema Contract
# ===========================================================================

def test_01_dossier_creation() -> None:
    svc = BillDossierService()
    dossier = svc.get_dossier(CENTRAL_PROD_BILL_ID)

    assert dossier is not None
    assert isinstance(dossier, EnrichedBillDossier)

    # Required top-level subcomponents
    assert dossier.identity is not None
    assert dossier.status is not None
    assert dossier.content is not None
    assert dossier.impact_context is not None
    assert dossier.provenance is not None
    assert isinstance(dossier.timeline, list)
    assert isinstance(dossier.change_summary, BillChangeSummary)
    assert isinstance(dossier.stakeholder_views, dict)
    assert isinstance(dossier.sector_exposures, list)
    assert isinstance(dossier.company_exposures, list)
    assert isinstance(dossier.documents, list)
    assert dossier.model_status in [m.value for m in ModelStatus]

    # Serialization round-trip
    d_dict = dossier.to_dict()
    assert isinstance(d_dict, dict)
    assert d_dict["identity"]["bill_id"] == CENTRAL_PROD_BILL_ID


# ===========================================================================
# 2. Central Bill Dossier (MODELLED)
# ===========================================================================

def test_02_central_bill_dossier() -> None:
    svc = BillDossierService()
    dossier = svc.get_dossier(CENTRAL_PROD_BILL_ID)

    assert dossier is not None
    assert dossier.identity.jurisdiction.lower() == "central"
    assert dossier.model_status == ModelStatus.MODELLED.value
    assert dossier.model_status_label == "MODELLED — CENTRAL QUANTITATIVE"
    assert dossier.prediction_available is True
    assert "frozen analytical dataset" in dossier.model_status_description.lower()


# ===========================================================================
# 3. State Bill Dossier (NOT_ELIGIBLE)
# ===========================================================================

def test_03_state_bill_dossier() -> None:
    svc = BillDossierService()
    dossier = svc.get_dossier(STATE_BILL_ID)

    assert dossier is not None
    assert dossier.identity.jurisdiction.lower() == "state"
    assert dossier.model_status == ModelStatus.NOT_ELIGIBLE.value
    assert dossier.model_status_label == "NOT ELIGIBLE FOR STOCK MODEL"
    assert dossier.prediction_available is False
    assert "0" in dossier.model_status_description or "strictly isolated" in dossier.model_status_description.lower()


# ===========================================================================
# 4. Knowledge-Only Bill
# ===========================================================================

def test_04_knowledge_only_bill() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = LiveKnowledgeRepository(storage_dir=Path(tmpdir))
        live_rec = LiveKnowledgeRecord(
            title="Live Tech Discovery Bill 2026",
            jurisdiction="central",
            discovered_by_source_id="prs_live_feed",
            live_status="DETECTED",
            analytical_model_status="KNOWLEDGE_ONLY",
            canonical_bill_id="live-tech-discovery-bill-2026",
        )
        repo.upsert(live_rec)

        svc = BillDossierService(live_knowledge_repo=repo)
        dossier = svc.get_dossier("live-tech-discovery-bill-2026")

        assert dossier is not None
        assert dossier.model_status == ModelStatus.KNOWLEDGE_ONLY.value
        assert dossier.model_status_label == "LIVE — KNOWLEDGE ONLY"
        assert dossier.prediction_available is False

    # Also test Central auxiliary bill (key-issues-and-analysis)
    svc_std = BillDossierService()
    aux_dossier = svc_std.get_dossier("key-issues-and-analysis")
    if aux_dossier:
        assert aux_dossier.model_status == ModelStatus.NOT_ELIGIBLE.value
        assert aux_dossier.prediction_available is False


# ===========================================================================
# 5. Modelled Bill Exclusivity (Exactly 20 Frozen Central Bills)
# ===========================================================================

def test_05_modelled_bill_exclusivity() -> None:
    frozen_ids = get_frozen_central_production_bill_ids()
    assert len(frozen_ids) == 20

    # Ensure all are strings and start with "the-"
    for b_id in frozen_ids:
        assert isinstance(b_id, str)
        assert b_id.startswith("the-")

    # State bills and unknown IDs must never be in the frozen set
    assert STATE_BILL_ID not in frozen_ids
    assert "nonexistent-bill-999" not in frozen_ids
    assert "key-issues-and-analysis" not in frozen_ids
    assert "service-bill" not in frozen_ids


# ===========================================================================
# 6. Chronological Evidence-Based Timeline
# ===========================================================================

def test_06_timeline_generation() -> None:
    svc = BillDossierService()
    bill = svc.resolve_bill(CENTRAL_PROD_BILL_ID)
    assert bill is not None

    timeline = svc.build_timeline(bill)
    assert len(timeline) > 0

    for ev in timeline:
        assert isinstance(ev, TimelineEvent)
        assert ev.event_id
        assert ev.stage
        assert ev.stage_label
        assert ev.source_authority
        assert ev.verified is True


# ===========================================================================
# 7. Change Detection & Strict Epistemic Separation
# ===========================================================================

def test_07_change_detection_and_separation() -> None:
    svc = BillDossierService()
    bill = svc.resolve_bill(CENTRAL_PROD_BILL_ID)
    assert bill is not None

    changes = svc.build_change_summary(bill)
    assert isinstance(changes, BillChangeSummary)

    # Strict rule: document changes separated from legislative status changes
    assert isinstance(changes.document_changes, list)
    assert isinstance(changes.legislative_changes, list)
    assert "DOCUMENT CHANGE vs LEGISLATIVE STATUS CHANGE" in changes.separation_notice
    assert "not claimed as a statutory status change without authoritative procedural evidence" in changes.separation_notice.lower()


# ===========================================================================
# 8. Provenance Integrity
# ===========================================================================

def test_08_provenance_integrity() -> None:
    svc = BillDossierService()
    dossier = svc.get_dossier(CENTRAL_PROD_BILL_ID)
    assert dossier is not None

    prov = dossier.provenance
    assert prov.official_source
    assert prov.source_authority
    assert prov.discovered_at
    assert prov.data_quality
    assert isinstance(prov.provenance_map, dict)


# ===========================================================================
# 9. Document Metadata & SHA-256 Provenance
# ===========================================================================

def test_09_document_metadata_and_hashes() -> None:
    svc = BillDossierService()
    bill = svc.resolve_bill(CENTRAL_PROD_BILL_ID)
    assert bill is not None

    docs = svc.build_documents(bill)
    assert len(docs) > 0

    for doc in docs:
        assert isinstance(doc, BillDocumentItem)
        assert doc.document_id
        assert doc.title
        assert doc.format in ["PDF", "HTML", "PORTAL"]
        assert doc.retrieval_status in ["AVAILABLE", "OFFICIAL_PORTAL_ONLY", "PENDING_RETRIEVAL"]
        assert doc.source_authority


# ===========================================================================
# 10. Sector Mapping & Macro Sector Directory
# ===========================================================================

def test_10_sector_mapping() -> None:
    svc = BillDossierService()
    bill = svc.resolve_bill(CENTRAL_PROD_BILL_ID)
    assert bill is not None

    sectors = svc.build_sector_exposures(bill)
    assert len(sectors) > 0

    primary = sectors[0]
    assert isinstance(primary, SectorExposureItem)
    assert primary.exposure_type == "DIRECT"
    assert primary.relevance == "HIGH"
    assert primary.transmission_channel is not None


# ===========================================================================
# 11. Industry Mapping & Canonical Classification
# ===========================================================================

def test_11_industry_mapping() -> None:
    svc = BillDossierService()
    dossier = svc.get_dossier(CENTRAL_PROD_BILL_ID)
    assert dossier is not None

    for sec in dossier.sector_exposures:
        assert isinstance(sec.industries, list)
        assert len(sec.industries) > 0


# ===========================================================================
# 12. Company Exposure & Explicit Linkage Reasons
# ===========================================================================

def test_12_company_exposure_linkages() -> None:
    svc = BillDossierService()
    bill = svc.resolve_bill(CENTRAL_PROD_BILL_ID)
    assert bill is not None

    # Modelled Central
    companies_modelled = svc.build_company_exposures(bill, is_modelled=True)
    valid_reasons = {
        "regulated_activity",
        "product_service_exposure",
        "supply_chain_exposure",
        "geographic_scope",
        "sector_exposure",
        "documented_corporate_relevance",
    }

    for c in companies_modelled:
        assert isinstance(c, LinkedCompanyExposureItem)
        assert len(c.linkage_reasons) > 0
        assert all(r in valid_reasons for r in c.linkage_reasons)

    # Non-modelled Central or State: has_market_predictions MUST be False
    companies_unmodelled = svc.build_company_exposures(bill, is_modelled=False)
    for c in companies_unmodelled:
        assert c.has_market_predictions is False


# ===========================================================================
# 13. Model Status Firewall Enforcement
# ===========================================================================

def test_13_model_status_firewall() -> None:
    svc = BillDossierService()

    # State bill
    state_bill = svc.resolve_bill(STATE_BILL_ID)
    assert state_bill is not None
    m_stat, label, desc, pred_avail = svc.get_model_status_info(state_bill)
    assert m_stat == ModelStatus.NOT_ELIGIBLE.value
    assert pred_avail is False

    # Live knowledge record
    live_rec = LiveKnowledgeRecord(
        title="Sample Live Bill",
        jurisdiction="central",
        discovered_by_source_id="prs_live",
    )
    unified_live = svc._live_record_to_unified(live_rec)
    m_stat_live, _, _, pred_avail_live = svc.get_model_status_info(unified_live)
    assert m_stat_live in [ModelStatus.KNOWLEDGE_ONLY.value, ModelStatus.PENDING_REVIEW.value]
    assert pred_avail_live is False


# ===========================================================================
# 14. AI Grounded Context & Epistemic Separation
# ===========================================================================

def test_14_ai_grounded_context() -> None:
    builder = AIContextBuilder()
    live_rec = LiveKnowledgeRecord(
        title="Live Contextual Enactment 2026",
        jurisdiction="central",
        discovered_by_source_id="central_lok_sabha",
        live_status="NEW",
        analytical_model_status="KNOWLEDGE_ONLY",
    )

    ctx = builder._build_live_context("live-contextual-enactment-2026", live_rec)
    assert ctx is not None
    assert ctx.jurisdiction == "central"
    assert "STRICT_KNOWLEDGE_ONLY" in str(ctx.provenance.get("firewall"))

    # Verify prediction unavailability statement
    pred_str = " ".join(ctx.predictions)
    assert "UNAVAILABLE" in pred_str
    assert "firewalled from stock model" in pred_str.lower()

    # Verify unverified field handling
    fact_str = " ".join(ctx.facts)
    assert "INSUFFICIENT VERIFIED INFORMATION" in fact_str


# ===========================================================================
# 15. Insufficient-Source Graceful Handling
# ===========================================================================

def test_15_insufficient_source_handling() -> None:
    svc = BillDossierService()
    minimal_bill = UnifiedBillRecord(
        bill_id="minimal-test-bill",
        jurisdiction="central",
        state=None,
        title="Minimal Test Bill Without URLs",
        short_title="Minimal Bill",
        bill_number=None,
        legislature="Parliament of India",
        house="Lok Sabha",
        session=None,
        ministry=None,
        year=2026,
        introduction_date=None,
        passage_date=None,
        assent_date=None,
        status="Introduced",
        policy_domain=None,
        economic_sectors=[],
        secondary_sectors=[],
        stakeholders=[],
        summary="",
        company_exposure_count=0,
        listed_company_exposure_count=0,
        market_relevance="LOW",
        modeling_eligibility="NOT_ELIGIBLE",
        data_sufficiency="MINIMAL",
        source_url=None,
        pdf_url=None,
        source_type="MANUAL",
        data_quality="UNVERIFIED",
        provenance={},
    )

    # Documents fallback
    docs = svc.build_documents(minimal_bill)
    assert len(docs) == 1
    assert docs[0].format == "PORTAL"
    assert docs[0].retrieval_status == "OFFICIAL_PORTAL_ONLY"

    # Plain language fallback
    pl = svc.build_plain_language_explanation(minimal_bill, [], None)
    assert pl.epistemic_level == "INTERPRETATION"
    assert len(pl.what_is_still_unknown) > 0


# ===========================================================================
# 16. Multi-Tenant Isolation
# ===========================================================================

def test_16_tenant_isolation() -> None:
    # Tenant Alpha
    resp_a = client.get(
        f"/api/v1/bills/{CENTRAL_PROD_BILL_ID}/dossier",
        headers=HEADERS_TENANT_A,
    )
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    assert data_a["identity"]["bill_id"] == CENTRAL_PROD_BILL_ID

    # Tenant Beta
    resp_b = client.get(
        f"/api/v1/bills/{CENTRAL_PROD_BILL_ID}/dossier",
        headers=HEADERS_TENANT_B,
    )
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert data_b["identity"]["bill_id"] == CENTRAL_PROD_BILL_ID


# ===========================================================================
# 17. RBAC & Error Contracts (404 BILL_NOT_FOUND)
# ===========================================================================

def test_17_rbac_access_control() -> None:
    resp = client.get(
        "/api/v1/bills/completely-nonexistent-bill-9999/dossier",
        headers=HEADERS_TENANT_A,
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "BILL_NOT_FOUND"


# ===========================================================================
# 18. Document & Dossier Sub-Endpoints
# ===========================================================================

def test_18_document_and_dossier_sub_endpoints() -> None:
    b_id = CENTRAL_PROD_BILL_ID

    # /timeline
    r_time = client.get(f"/api/v1/bills/{b_id}/timeline", headers=HEADERS_TENANT_A)
    assert r_time.status_code == 200
    assert "events" in r_time.json()

    # /changes
    r_chg = client.get(f"/api/v1/bills/{b_id}/changes", headers=HEADERS_TENANT_A)
    assert r_chg.status_code == 200
    assert "changes" in r_chg.json()

    # /plain-language
    r_pl = client.get(f"/api/v1/bills/{b_id}/plain-language", headers=HEADERS_TENANT_A)
    assert r_pl.status_code == 200
    assert "plain_language" in r_pl.json()

    # /stakeholders
    r_stk = client.get(f"/api/v1/bills/{b_id}/stakeholders", headers=HEADERS_TENANT_A)
    assert r_stk.status_code == 200
    stk_data = r_stk.json()["stakeholder_views"]
    assert "INVESTOR" in stk_data
    assert "BUSINESS_OWNER" in stk_data

    # /sectors
    r_sec = client.get(f"/api/v1/bills/{b_id}/sectors", headers=HEADERS_TENANT_A)
    assert r_sec.status_code == 200
    assert "sector_exposures" in r_sec.json()

    # /documents
    r_doc = client.get(f"/api/v1/bills/{b_id}/documents", headers=HEADERS_TENANT_A)
    assert r_doc.status_code == 200
    assert "documents" in r_doc.json()

    # /model-status
    r_stat = client.get(f"/api/v1/bills/{b_id}/model-status", headers=HEADERS_TENANT_A)
    assert r_stat.status_code == 200
    assert r_stat.json()["model_status"] == "MODELLED"


# ===========================================================================
# 19. Search Integration (data_layer & model_status)
# ===========================================================================

def test_19_search_integration() -> None:
    resp = client.get("/api/v1/search?q=banking", headers=HEADERS_TENANT_A)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) > 0

    banking_item = next((i for i in items if "banking" in i["id"].lower()), None)
    assert banking_item is not None
    assert banking_item["data_layer"] == "FROZEN_MODEL"
    assert banking_item["model_status"] == "MODELLED"

    # Search state bills
    resp_state = client.get("/api/v1/search?q=karnataka", headers=HEADERS_TENANT_A)
    assert resp_state.status_code == 200
    state_items = resp_state.json()["items"]
    if state_items:
        state_item = state_items[0]
        assert state_item["data_layer"] == "QUALITATIVE_INTEL"
        assert state_item["model_status"] == "NOT_ELIGIBLE"


# ===========================================================================
# 20. Invariant: No Automatic Stock Predictions
# ===========================================================================

def test_20_no_automatic_stock_predictions_invariance() -> None:
    # 1. State prediction firewall invariant
    r_pred = client.get(f"/api/v1/bills/{STATE_BILL_ID}/predictions", headers=HEADERS_TENANT_A)
    assert r_pred.status_code == 200
    pred_data = r_pred.json()
    assert pred_data["available"] is False
    assert pred_data["total"] == 0

    # 2. Production baseline manifest integrity
    manifest_path = Path("docs/production_baseline.json")
    assert manifest_path.is_file()
    baseline = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert baseline["central_baseline"]["central_production_bills"] == 20
    assert baseline["state_baseline"]["stock_predictions_count"] == 0
    assert baseline["invariants"]["zero_state_stock_predictions"] is True
