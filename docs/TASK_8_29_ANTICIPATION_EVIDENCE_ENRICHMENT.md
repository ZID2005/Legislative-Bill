# Task 8.29 — Anticipation Evidence Enrichment & Media Diffusion Intelligence

**Status**: Production Validated & Authoritative  
**Date**: October 2026  
**Document**: Architectural Specification, Research Integrity Framework, and Integration Guide  

---

## 1. Research Motivation

In econometric event-study analysis of legislative impacts on financial markets, pre-event abnormal returns and cumulative abnormal returns (CAR) often display directional trends prior to official bill introduction dates. Prior iterations of the platform detected these pre-event price anomalies with high statistical rigor. 

However, previous research-integrity audits identified an epistemic limitation: **when external public media and regulatory publication records were unavailable, a strong anticipation classification could be driven purely by econometric price drift**. Equating market price drift alone with pre-event awareness creates severe scientific and compliance risks. Without independent public-information verification, researchers and analysts risk confusing organic price dynamics, sector-wide momentum, or liquidity fluctuations with information diffusion.

Task 8.29 implements an additive **Anticipation Evidence Enrichment & Media Diffusion Intelligence Layer** that decouples quantitative market signals from public information signals. The platform strictly answers:
1. *"Was there observable public information about this legislative event before the official event date?"*
2. *"How strong is the evidence that the market may have been reacting to public information before the official legislative event?"*

This architecture explicitly safeguards against allegations of insider trading, market manipulation, unlawful disclosures, or information leakage. The system output is strictly defined as **Public Information Diffusion Intelligence**.

---

## 2. The Anticipation Paradox

The **Anticipation Paradox** refers to the empirical reality that highly consequential economic legislation is rarely formulated in total secrecy. Months before formal introduction in Parliament or a State Legislative Assembly, governments issue public draft bills, invite stakeholder consultations, conduct inter-ministerial reviews, and release regulatory white papers. Mainstream financial journalism routinely covers these developments.

As a result:
- **Efficient Information Diffusion**: Capital markets price in legislative expectations ahead of official introduction dates based on openly available reporting and public notices.
- **The Epistemic Pitfall**: Treating pre-event abnormal returns as "leakage" or "illicit trading" misinterprets standard market price discovery.
- **The Resolution**: By systematically gathering, verifying, and attributing public news, gazette notifications, ministry press releases, and search-trend spikes, the platform provides verifiable context proving that public information preceded market adjustments.

---

## 3. Existing Market-Signal Methodology

The central quantitative foundation remains frozen and immutable:
- **Central Production Bills**: 20 bills
- **Quantitative Companies**: 47 companies
- **Evaluated Pairs**: 940 pairs
- **Authoritative Event Horizons**: `[-1,+1]`, `[-3,+3]`, `[-5,+5]`, `[-5,+10]`, `[-10,+10]`
- **Pre-Event Estimation Windows**: `[-30,-21]`, `[-30,-11]`, `[-30,-6]`, `[-30,-1]`

The market signal captures econometric indicators derived from market-model residuals:
- Pre-event Cumulative Abnormal Returns ($CAR$)
- Directional persistence (ratio of directional daily abnormal returns to total window days)
- $Z$-score of abnormal returns relative to pre-event estimation standard error
- Daily abnormal return acceleration and volatility
- Institutional concentration ratio

Under Task 8.29, these metrics are preserved verbatim as the **Market Signal Dimension** and are never modified or re-estimated.

---

## 4. Public-Information Evidence Model

Task 8.29 establishes the additive domain model `PublicInformationEvidence`:

```python
@dataclass
class PublicInformationEvidence:
    evidence_id: str
    bill_id: str
    jurisdiction: str
    source_type: PublicInformationSourceType
    source_name: str
    source_url: str
    publication_timestamp: Optional[str]
    discovery_timestamp: str
    event_reference: str
    headline: str
    summary: str
    relevance: float
    evidence_strength: EvidenceStrength
    temporal_relation: TemporalRelation
    source_credibility: SourceCredibilityTier
    entity_matches: list[str]
    sector_matches: list[str]
    keywords: list[str]
    hash: str
    provenance: dict[str, Any]
    verification_status: VerificationStatus
    created_at: str
    duplicate_of: Optional[str] = None
    is_canonical: bool = True
```

This model is completely additive, non-destructive, and decoupled from historical statistical scores.

---

## 5. Source Hierarchy & Credibility Tiers

Sources are categorized using an extensible, deterministic taxonomy and graded across five credibility tiers:

| Tier | Source Category | Description | Weight |
|---|---|---|---|
| **TIER_1** | `OFFICIAL_LEGISLATIVE`, `OFFICIAL_GOVERNMENT`, `PARLIAMENTARY`, `MINISTRY`, `REGULATOR` | Official Gazette notifications, Lok Sabha/Rajya Sabha parliamentary bulletins, ministry draft policy releases, RBI/SEBI/CCI consultative circulars. | 1.00 |
| **TIER_2** | `NEWS`, `BUSINESS_MEDIA`, `FINANCIAL_MEDIA` | Established national financial dailies, Tier-1 news organizations (Economic Times, Business Standard, Mint, Reuters, Bloomberg). | 0.80 |
| **TIER_3** | `PUBLIC_DOCUMENT` | Recognized trade association submissions (FICCI, CII, NASSCOM), policy think-tank reports (PRS Legislative Research, Vidhi Centre for Legal Policy). | 0.60 |
| **TIER_4** | `SEARCH_TREND` | Aggregated search-interest indicators (Google Trends index, regional query volume). Classified strictly as `PUBLIC_ATTENTION_SIGNAL`. | 0.40 |
| **TIER_5** | `OTHER` | Unverified blogs, social aggregators, or low-confidence sources. | 0.20 |

*Note: These tiers reflect evidentiary provenance and auditability under institutional research standards; they are not political rankings.*

---

## 6. Temporal Anti-Leakage Logic

To preserve scientific validity, all evidence records must strictly satisfy temporal ordering against the authoritative bill event timestamp:

$$\Delta t = t_{\text{publication}} - t_{\text{official\_event}}$$

1. **`PRE_EVENT`**:
   - Condition: $t_{\text{publication}} < t_{\text{official\_event}}$ with verifiable hour/minute precision, or published at least 1 calendar day prior.
   - Only `PRE_EVENT` records are allowed to contribute to pre-event public information scoring.
2. **`SAME_DAY`**:
   - Condition: $t_{\text{publication}}$ matches the calendar date of the official event, but hour/minute timestamp is identical or later than the official event.
   - Same-day evidence **MUST NOT** be treated as pre-event evidence.
3. **`POST_EVENT`**:
   - Condition: $t_{\text{publication}} > t_{\text{official\_event}}$.
   - Post-event reporting is strictly excluded from anticipation calculations.
4. **`UNKNOWN`**:
   - Condition: Publication timestamp is missing, malformed, or lacks the necessary temporal resolution to prove pre-event release.
   - The system **never guesses** or interpolates timestamps.

---

## 7. Evidence Relevance & Scoring

### Relevance Evaluation
Relevance is evaluated deterministically by `EvidenceValidator.evaluate_relevance`:
- **Bill Title Match**: Exact title or normalized key phrase overlap ($\ge 60\%$ token ratio).
- **Bill Number Match**: Reference to bill identifier (e.g., "Bill No. 120 of 2024").
- **Nodal Ministry Match**: Explicit citation of sponsoring ministry or department.
- **Affected Sector Match**: Coverage of sectors matching bill taxonomy.
- **Corporate Entity Match**: Mention of tracked company name, NSE/BSE ticker symbol, or statutory ISIN.
- **Match Reason**: Every evaluation generates an audit trail (e.g., *"Direct mention of bill title 'The Banking Laws (Amendment) Bill, 2024'; References affected sector(s): Banking, Financial Services"*).

### Public Information Evidence Score Formulation
The normalized score ($0.0 \to 1.0$) is calculated as:

$$\text{Score} = \min\left(1.0, \, 0.35 \cdot C_{\text{avg}} + 0.25 \cdot T_{\text{prox}} + 0.20 \cdot R_{\text{avg}} + 0.10 \cdot S_{\text{count\_norm}} + 0.10 \cdot D_{\text{ratio}}\right)$$

Where:
- $C_{\text{avg}}$: Average credibility score of verified pre-event sources.
- $T_{\text{prox}}$: Temporal proximity score (exponential decay rewarding verified disclosures closer to the pre-event window).
- $R_{\text{avg}}$: Average relevance score of matching evidence.
- $S_{\text{count\_norm}}$: Independent source count normalized up to 5 publishers.
- $D_{\text{ratio}}$: Publisher diversity ratio ($\text{unique\_domains} / \text{total\_records}$).

---

## 8. Deduplication & Syndication Control

News articles frequently circulate across syndicated wires (e.g., PTI, ANI) or multiple sub-domains with tracking parameters. `EvidenceDeduplicator` enforces strict hygiene:
- **Canonical URL Normalization**: Stripping tracking tags (`utm_*`, `ref`, `fbclid`).
- **Normalized Title Hashing**: SHA-256 fingerprinting of punctuation-stripped, lowercased titles.
- **Duplicate Linking**: Secondary wire items retain metadata but are marked `is_canonical = False` and record `duplicate_of = canonical_evidence_id`.
- Syndicated duplicates **do not** inflate independent source counts or diversity ratios.

---

## 9. Search-Trend Signal Integration

Search interest data (e.g., Google Trends relative index) is integrated via `SearchTrendAdapter`:
- Tracked metrics: Query string, geographical region, timestamp, index value ($0-100$), baseline moving average, and spike indicator ($\ge 1.5\times$ baseline).
- **Classification Invariant**: Search interest is strictly designated as `PUBLIC_ATTENTION_SIGNAL`.
- It is never represented as proof that the public had advance knowledge of proprietary bill provisions.

---

## 10. News Adapter Architecture & Fallback Boundaries

The media ingestion subsystem adheres to an extensible adapter design:
- `BaseEvidenceAdapter`: Abstract interface declaring `fetch_evidence(bill, ...)`.
- `OfficialSourceAdapter`: Ingests official government, gazette, and parliamentary records.
- `NewsAdapter`: Pluggable media ingestion gateway with graceful fallback. When external network APIs are disabled or unavailable, `NewsAdapter` returns empty sets or designated mock fixtures without raising uncaught exceptions or breaking frozen analytics.
- `SearchTrendAdapter`: Normalized search interest provider.

External provider outages **never impact** frozen econometric records or cause pipeline downtime.

---

## 11. Legislative Monitoring Integration

The Task 8.26 live monitoring pipeline generates `ChangeEvent` records. When a monitoring event (e.g., draft publication or gazette notification) represents an external publication, `AnticipationEvidenceService.promote_monitoring_event_to_evidence` allows controlled promotion:
- `ChangeEvent` $\to$ `PublicInformationEvidence`.
- Invariant: Observed monitoring events remain epistemically distinct from quantitative predictions.
- Full provenance is preserved: Source URL, crawler job ID, timestamp, and verification state.

---

## 12. Combined Anticipation Interpretation Matrix

The system decouples market signals from public information signals and evaluates their conjunction using a deterministic matrix:

| Market Signal | Media Evidence | Classification Result | Institutional Interpretation |
|---|---|---|---|
| **LOW / NONE** | **NONE** | `NO_PRE_EVENT_SIGNAL` | No observable pre-event market anomalies or public disclosures detected. |
| **HIGH** | **NONE** | `MARKET_SIGNAL_ONLY` | Pre-event market price movement observed without verified external public media. (Prevents false leakage attribution). |
| **LOW** | **HIGH** | `PUBLIC_INFORMATION_SUPPORTED` | Observable public reporting preceded event with minimal abnormal price response. |
| **HIGH** | **MEDIUM** | `PUBLIC_INFORMATION_SUPPORTED` | Pre-event market movement coincided with verified public pre-event reporting. |
| **HIGH** | **HIGH** | `MULTI_SOURCE_PUBLIC_INFORMATION` | Pre-event market movement coincided with multiple corroborating, independent public sources. |
| **UNKNOWN** | **HIGH** | `PUBLIC_INFORMATION_SUPPORTED` | Pre-event public documentation verified; quantitative price data unmodelled or unavailable. |
| **UNKNOWN** | **NONE** | `INSUFFICIENT_EVIDENCE` | Insufficient market or public documentation to establish pre-event context. |

---

## 13. Personalized Workspace Integration (Task 8.28 Extension)

Personalized portfolios and watchlists automatically surface pre-event information context:
- Holdings and watchlist items display pre-event evidence indicators alongside authoritative predictions.
- The `PersonalizedBillImpact` schema exposes `pre_event_public_information` summaries including:
  - Classification badge (`MARKET_SIGNAL_ONLY`, `PUBLIC_INFORMATION_SUPPORTED`, etc.)
  - Verified pre-event source count
  - Independent publisher count
  - Temporal window range
  - Verbatim institutional compliance notice

---

## 14. AI Guardrails & Epistemic Grounding

The AI Assistant and context generator enforce rigorous institutional safety rules:
- **Prohibited Terminology Interception**: Prompts or outputs containing allegations of "insider trading", "market manipulation", "illegal leaks", "confidential disclosures", or financial investment commands ("buy", "sell", "hold") are actively intercepted and redacted by `AIGuardrails`.
- **New Epistemic Label `[EVIDENCE]`**:
  - `[FACT]`: Statutory and entity registry data.
  - `[OBSERVED]`: Authoritative historical price action and trade volume.
  - `[EVIDENCE]`: Externally sourced, provenance-traceable public-information records.
  - `[DERIVED]`: Econometric model projections and $CAR$ calculations.
  - `[INTERPRETATION]`: Analytical commentary and scenario synthesis.
- If evidence is absent or insufficient, the AI outputs: *"Insufficient verified public-information evidence."*

---

## 15. Subnational State Legislation Firewall

Under the constitutional and architectural firewall established in prior tasks:
- **Central Modelled Bills**: 20 bills with quantitative predictions and full anticipation contexts.
- **State Bills**: 44 bills tracked exclusively as knowledge and policy intelligence.
- **State Stock Predictions**: Strictly **0**.
- State bills may receive `PublicInformationEvidence`, news records, and official gazette citations, but **CANNOT** generate econometric $CAR$ forecasts, stock predictions, or quantitative decision matrices.

---

## 16. Frozen Baseline Integrity

The baseline manifest SHA-256 hash must remain exactly unchanged:
```
50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7
```

Audit metrics verified:
- Central Production Bills: **20**
- Quantitative Companies: **47**
- Bill-Company Pairs: **940**
- Prediction Records: **4,700**
- Decision Records: **4,700**
- Frozen Anticipation Records: **940**
- Stakeholder Reports: **14,100**
- State Stock Predictions: **0**

---

## 17. Limitations & Known Data Availability Gaps

1. **Historical Archival Coverage**: Older state legislative proposals may lack digital press archives, resulting in `INSUFFICIENT_EVIDENCE` states.
2. **Intraday Timestamp Precision**: When articles provide publication dates without exact time-of-day timestamps on the official introduction date, the temporal classifier defaults to `UNKNOWN` to avoid false pre-event attribution.
3. **Syndication Latency**: Wire aggregators can republish identical text under multiple publication timestamps; the deduplicator preserves only the earliest verified timestamp.

---

## 18. Verification Protocol & Test Results

The Task 8.29 verification test suite (`tests/test_task_8_29_anticipation_evidence.py`) tests all 30 mandatory scenarios:
- **30/30 unit & integration tests PASSED**.
- Regression test suites:
  - Task 8.28: 24/24 PASSED
  - Task 8.27: 20/20 PASSED
  - Task 8.26: 30/30 PASSED
  - Security IDOR & RBAC: 17/17 PASSED
  - Frontend Vitest Suite: 205/205 PASSED (22 test files)
  - Frontend Typecheck & Build: 0 errors, 31/31 routes compiled
  - Local SaaS Smoke Test: 23/23 critical-path steps PASSED

---

## 19. Future Media Providers & Extensibility Roadmap

The `BaseEvidenceAdapter` interface enables seamless future plug-ins:
- **GDELT 2.0 Global Knowledge Graph**: Real-time geopolitical and legislative sentiment stream.
- **Press Information Bureau (PIB) India API**: Direct ingestion of cabinet decision briefings.
- **BSE/NSE Corporate Announcements Feed**: Regulatory disclosure filings under SEBI LODR Regulation 30.
