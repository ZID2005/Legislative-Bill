# Task 8.10 Technical Documentation: Groq AI Intelligence & Explanation Layer

This document details the architectural design, implementation specifications, security controls, and operational usage of the Groq AI Intelligence & Explanation Layer.

---

## 1. System Role & Architectural Boundaries

The Groq AI Intelligence layer provides natural-language translation, plain-English synthesis, and contextual explanations of Indian legislative measures and existing quantitative market models.

```
┌────────────────────────────────────────────────────────┐
│              Verified Project Repository               │
│  (Central Gazette/PRS Records + State Assembly Data)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                 AI Context Builder                     │
│    Segregates data into FACT, DERIVED, INTERPRETATION, │
│        and PREDICTION with zero value fabrication      │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                   AIGuardrails                         │
│   Injects 20 safety rules & persona-specific directives │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                    GroqClient                          │
│   Executes low-temperature inference via Groq Cloud    │
│   (Sanitizes exceptions & masks API key credentials)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│            Post-Generation Response Auditor            │
│   Regex scanning for advice, certainty, & data leaks   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                 AIExplanationResult                    │
│    Markdown presentation with provenance attribution   │
└────────────────────────────────────────────────────────┘
```

### Core Principles
1. **Explanation, Not Oracle:** Groq is an analytical translation layer, **not** a source of truth.
2. **Zero Model Contamination:** LLM output is never stored into machine learning features, ground-truth label stores, or backtesting sets.
3. **Strict State Isolation:** Indian State legislative bills are strictly isolated from market prediction models. State market predictions remain **strictly 0**.
4. **Numerical Fidelity:** Numerical figures (probabilities, confidence, risk scores) must originate verbatim from provided context. Groq is strictly forbidden from inventing new numbers.

---

## 2. Configuration & API Setup

Configuration is governed by environment variables loaded in `config/settings.py`:

```ini
# Groq Cloud AI Provider Configuration
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TIMEOUT=30.0
GROQ_MAX_TOKENS=1024
GROQ_TEMPERATURE=0.2
AI_CACHE_DIR=data/ai_cache
```

### Absence of Credentials
If `GROQ_API_KEY` is not present:
- The system operates normally without crashing.
- `GroqClient.is_available` evaluates to `False`.
- The UI renders informative advisory badges.
- Underlying data, charts, filters, and tables remain fully functional.

---

## 3. Context Construction Engine (`services/ai/ai_context_builder.py`)

The deterministic context builder extracts grounded information from existing repositories:
- `UnifiedLegislativeDiscoveryService`
- `BillRepository` & `StateBillRepository`
- `KnowledgeRepository` & `StateKnowledgeRepository`
- `MappingRepository` & `StateCorporateExposureRepository`
- `DecisionRepository`

### Category Enforcement
- `[FACTS]`: Statutory titles, bill numbers, gazette dates, chamber of origin, sponsoring ministries, and official bill summaries.
- `[DERIVED INFORMATION]`: System taxonomies, economic sectors, mapped stakeholder groups, and verified corporate exposures.
- `[ECONOMIC INTERPRETATION]`: Qualitative transmission mechanisms (compliance cost, fiscal impact, market access), modeling eligibility, and data sufficiency indicators.
- `[PREDICTIONS]`:
  - **Central:** Direction, confidence, market-moving probability, impact score, risk score, and anticipation evidence.
  - **State:** Explicitly declared: *"State market prediction is currently unavailable. (Model predictions strictly 0)."*

---

## 4. Prompt Engineering & System Guardrails (`services/ai/ai_guardrails.py`)

### Master Guardrail Policies
1. Grounding: Rely strictly on provided context block.
2. Missing Information: Explicitly declare missing items as *"Information is unavailable in project records."*
3. No Citations Fabrication: Never invent URLs or statutory section references.
4. No Provision Fabrication: Extract provisions strictly from verified text.
5. No Unmapped Exposure: Never invent company exposures not present in repository records.
6. Zero Prediction Invention: Never generate, invent, or adjust numerical predictions.
7. Preserve Uncertainty: Use probabilistic phrasing (*"the model estimates"*).
8. No Financial Advice: Never provide investment or legal advice.
9. No Trading Advice: Never advise buying, selling, or holding securities.
10. Banned Words: Prohibit *"buy"*, *"sell"*, *"guaranteed return"* as advisory actions.
11. Fact vs Derived: Clearly distinguish statutory facts from derived taxonomies.
12. Label Model Predictions: Clearly demarcate statistical model estimates.
13. State Bill Isolation: Enforce that State market predictions are strictly unavailable.
14. Uncertainty Preservation: Acknowledge data sufficiency and event-date quality limitations.
15. Attribution: Cite official gazette and PDF provenance sources.
16. Non-Accusatory Anticipation: Never accuse entities of insider trading; use *"pricing-in evidence"*.
17. Scope Bounding: Refuse external or unsupplied matters.
18. URL Integrity: Use only verified URLs provided in context.
19. Numerical Integrity: Any cited percentage or probability must match context verbatim.
20. Persona Adaptation: Adapt tone without providing individualized counsel.

---

## 5. Stakeholder Persona Modes

| Persona | Primary Focus & Tone | Guardrail Boundaries |
| :--- | :--- | :--- |
| **Investor** | Market relevance, regulatory uncertainty, sector sensitivities, and quantitative risk profiles. | Probabilistic only; zero trade recommendations. |
| **Business Owner** | Compliance obligations, licensing requirements, operating cost impacts, and regulatory timelines. | Practical operational focus; zero speculation. |
| **Employee** | Worker protections, wage mechanisms, job security, and safety provisions. | Statutory labor rights focus. |
| **Consumer** | Consumer rights, price transparency, product quality, and grievance redressal. | Practical consumer welfare focus. |
| **Farmer** | Agricultural procurement, crop support, irrigation rights, and cooperative regulations. | Agrarian policy focus. |
| **MSME** | Priority credit access, compliance relief, formalization, and dispute settlement. | Small enterprise administrative focus. |
| **General Public** | Citizen rights, public services, civic obligations, and practical meaning in plain language. | Accessible, non-technical terminology. |
| **Industry** | Sectoral capital expenditure, supply chain standards, and compliance frameworks. | Macro-industrial strategy focus. |

---

## 6. Deterministic Response Validation

After generation, the `AIGuardrails.validate_response` function executes deterministic pattern scanning:
1. **Financial Advice Filter:** Blocks calls to buy/sell stocks or allocate capital.
2. **Unsupported Certainty Filter:** Blocks claims of guaranteed stock moves or absolute returns.
3. **Accusatory Language Filter:** Blocks accusations of insider trading, leaks, or market rigging.
4. **State Prediction Audit:** Blocks numerical return predictions for State bills.
5. **Numerical Integrity Audit:** Cross-checks any percentages or decimal probabilities in the output against the input context; flags unverified numbers.

If validation fails, the service attempts one controlled regeneration with strict negative constraints. If it fails again, it returns a safe fallback message.

---

## 7. Caching & Deterministic Invalidation

To guarantee low latency and prevent redundant API costs:
- **Cache Key:** `SHA256(context_hash : operation : persona : query : model)`
- **Storage:** Stored as JSON files in `settings.AI_CACHE_DIR` with in-memory caching.
- **Context Hashing:** If statutory text, provisions, or model scores update, `context_hash` changes automatically, rendering old cached responses inaccessible.

---

## 8. Frontend-Agnostic Design & Future SaaS Integration

The `AIExplanationService` is designed to be completely decoupled from Streamlit:
- All methods (`explain_bill_summary`, `explain_provisions`, `ask_ai`, `compare_bills`) accept strings and return strongly-typed `AIExplanationResult` dataclasses.
- In future tasks, a FastAPI router can wrap this service directly to serve a React/Next.js commercial SaaS frontend:

```python
# Future FastAPI endpoint example:
@router.post("/api/v1/bills/{bill_id}/explain")
async def explain_bill_endpoint(bill_id: str, request: ExplainRequest) -> AIExplanationResponse:
    service = AIExplanationService()
    result = service.explain_bill_summary(bill_id, persona=request.persona)
    return AIExplanationResponse(
        content=result.content,
        provenance=result.provenance_sources,
        is_cached=result.is_cached
    )
```

---

## 9. Security & Secret Protection

- `GROQ_API_KEY` is sourced solely from environment variables and is never hardcoded.
- All logs filter out API key patterns via regex pattern matching (`gsk_[a-zA-Z0-9]+`).
- Exception handlers catch and mask provider errors to prevent leaking authentication headers.
- `.env` is explicitly ignored by version control.
