# TASK 8.31E-A — GROQ AI ASSISTANT FULL FUNCTIONAL INTEGRATION

## 1. Executive Summary & Objective

Task 8.31E-A fully integrates the application's institutional **AI Analyst / AI Assistant** with the **Groq API** (`openai/gpt-oss-120b`), converting the system into an authoritative conversational research assistant backed by real legislative documents, corporate exposures, analytical baselines, and safety firewalls.

The integration strictly enforces:
- **Backend-only Groq access:** Browser/client interfaces call FastAPI exclusively; no API keys or third-party provider calls ever occur in frontend bundles.
- **API Key Security:** `GROQ_API_KEY` is loaded from gitignored `.env`, never printed in logs, never included in responses, and masked in all operational telemetry.
- **Multi-Tenant Isolation:** Portfolio queries enforce tenant scoping and cross-tenant IDOR defense.
- **Analytical Invariance:** 4,700 predictions, 4,700 decisions, 940 anticipation scores, and 14,100 stakeholder reports remain completely frozen and unaltered.
- **Statutory Firewalls:** State legislation strictly produces 0 quantitative predictions (`STATE STOCK PREDICTIONS = 0`); intelligence-only companies produce 0 quantitative price forecasts (`INTELLIGENCE_ONLY = 0 PREDICTIONS`).
- **Investment Safety Guardrails:** Deterministic 0ms interception and refusal for Buy/Sell/Hold advice, stock tips, and speculative price targets.
- **Epistemic Labeling:** Answers delineate `[FACT]`, `[OBSERVED]`, `[DERIVED]`, `[INTERPRETATION]`, `[PREDICTION]`, and `[EVIDENCE]`.

---

## 2. Groq Architecture

```text
+-------------------------------------------------------------+
|                     Next.js Frontend                        |
|  - AIAssistantPanel / MonitoringAIAnalyst / CompanyAIPanel  |
|  - Citation Pills & Evidence Drawer                         |
+-------------------------------------------------------------+
                              |
                     HTTP POST /api/v1/ai/ask
                     HTTP POST /api/v1/ai/chat
                              v
+-------------------------------------------------------------+
|                  FastAPI AI Router & Layer                  |
|  - Authentication & Tenant Scoping Verification             |
|  - Direct Refusal Fast-Path (Buy/Sell, Price Target)        |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                     AI Context Builder                      |
|  - Assembles verified data for Bill, Company, Industry,     |
|    Portfolio, Comparison, Monitoring, or General scope      |
|  - Enforces State Firewall & Intelligence-Only Isolation    |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                      Groq Client Layer                      |
|  - Model: openai/gpt-oss-120b                               |
|  - Timeout: 30.0s | Max Tokens: 1024 | Temp: 0.2            |
|  - Untrusted Content Delimiters & Prompt Defense            |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                     Groq Cloud Engine                       |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                   Output Guardrails Audit                   |
|  - Validates absence of financial advice / guarantees       |
|  - Extracts epistemic tags & attaches structured citations  |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                     Structured Response                     |
|  content, citations, epistemic_labels, warnings, latency_ms |
+-------------------------------------------------------------+
```

---

## 3. Environment Configuration

The system manages Groq configuration strictly on the server:

| Environment Variable | Default Value | Description |
|---|---|---|
| `GROQ_API_KEY` | *(Secret from .env)* | Groq Cloud secret key (starts with `gsk_`). |
| `GROQ_MODEL` | `openai/gpt-oss-120b` | Target LLM model hosted on Groq Cloud. |
| `GROQ_TIMEOUT` | `30.0` | Client timeout in seconds. |
| `GROQ_MAX_TOKENS` | `1024` | Token limit for explanation generation. |
| `GROQ_TEMPERATURE` | `0.2` | Low-temperature sampling for deterministic institutional tone. |

### Security Invariants:
- `.env.example` contains only `GROQ_API_KEY=` (empty placeholder).
- `.gitignore` explicitly prevents `.env` and `.env.*` from being committed.
- Key masking utility converts `gsk_abc...xyz` for audit logs without exposing the payload.

---

## 4. Model Configuration & Replaceability

The model is configured dynamically via `GROQ_MODEL` and resolved in `services/ai/groq_client.py` without requiring code changes.

Verified Available Groq Models:
- `openai/gpt-oss-120b` (Default — highly capable reasoning & statutory analysis)
- `openai/gpt-oss-20b`
- `qwen/qwen3.8-27b`
- `allam-2-7b`

If Groq is unreachable or credentials are missing:
- Returns structured `API_KEY_MISSING` or `API_ERROR`.
- **Zero silent substitution:** The system never redirects to an unconfigured third-party LLM without reporting the state.

---

## 5. Request Flow & Grounding Architecture

### A. Context Types Supported
1. **`bill`**: Retrieves authoritative parliamentary title, gazette number, key provisions, affected economic sectors, mapped corporate exposures, and frozen model predictions.
2. **`company`**: Retrieves BSE/NSE company profile, sector/industry, corporate exposures, and quantitative status.
3. **`industry` / `sector`**: Retrieves sector profile, core business activities, and impacted companies.
4. **`portfolio`**: Retrieves tenant-authorized portfolio holdings, mapped exposures, and total sectoral exposure.
5. **`general`**: Retrieves statutory catalog, macroeconomic overview, and cross-jurisdictional indices.
6. **`monitoring`**: Retrieves recent statutory revisions, newly introduced acts, and detected gazette changes.

### B. Prompt Injection Defense
- Untrusted user input is passed through `clean_untrusted_input()` which neutralizes prompt injection directives (`"Ignore previous instructions"`, `"System prompt override"`, etc.).
- Retrieved context is enclosed within explicit `=== AUTHORITATIVE RETRIEVED DATA (UNTRUSTED CONTEXT) ===` delimiters.
- Master system prompt explicitly forbids executing directives found in user queries or retrieved documents.

---

## 6. Multi-Tenant Isolation

1. **Portfolio IDOR Protection:**
   - Every portfolio query executes with `user_id` and `tenant_id` from the verified JWT / session context.
   - `PortfolioRepository.get(portfolio_id, tenant_id, user_id)` returns `None` if `tenant_id` does not match.
   - Cross-tenant probes are immediately halted with `403 Forbidden` (`Access denied: Portfolio belongs to another tenant`).
2. **Semantic Probing Neutralization:**
   - User queries attempting to solicit foreign tenant information (`"Show me Tenant B's portfolio"`) are intercepted and refused.

---

## 7. AI Safety & Epistemic Boundaries

### A. Non-Negotiable Refusals
- **Buy / Sell / Hold Advice:** "Should I buy Reliance because of this bill?" -> Direct refusal with institutional explanation of research scope.
- **Price Targets:** "Give me a price target." -> Refusal explaining platform does not issue price targets or return guarantees.
- **State Stock Predictions:** "Give me a stock prediction for this Kerala bill." -> Refusal enforcing `STATE STOCK PREDICTIONS = 0`.
- **Intelligence-Only Entities:** "Give me a market prediction for this intelligence-only company." -> Refusal enforcing quantitative model isolation.

### B. Epistemic Tagging
Responses clearly categorize analytical knowledge:
- `[FACT]`: Authoritative statutory texts, gazette records, dates, and enacted laws.
- `[OBSERVED]`: Historical events, parliamentary sessions, recorded proceedings.
- `[DERIVED]`: System taxonomies, sector mappings, exposure mechanisms.
- `[INTERPRETATION]`: Qualitative economic implications, compliance dynamics.
- `[PREDICTION]`: Output of frozen quantitative models (never fact).
- `[EVIDENCE]`: Public documentation, gazette hashes, pre-event citations.

---

## 8. Citation & Evidence Architecture

Structured citations are returned in the response object and rendered by the frontend citation pill / evidence drawer UI:
```json
{
  "citations": [
    {
      "source_type": "official_bill",
      "title": "The Boilers Bill, 2024",
      "reference": "the-boilers-bill-2024",
      "authority": "Parliament of India"
    }
  ],
  "epistemic_labels": ["[FACT]", "[DERIVED]", "[INTERPRETATION]"],
  "warnings": []
}
```

If evidence is missing, the assistant returns:
> *"The available project data does not contain sufficient evidence to answer this reliably."*

---

## 9. Verification & Analytical Invariance

| Component | Target Baseline | Verified State | Status |
|---|---|---|---|
| Central Predictions | 4,700 | 4,700 | PASS |
| Central Decisions | 4,700 | 4,700 | PASS |
| Anticipation Scores | 940 | 940 | PASS |
| Stakeholder Reports | 14,100 | 14,100 | PASS |
| State Stock Predictions | Strictly 0 | Strictly 0 | PASS |
| State Knowledge Records | 44 | 44 | PASS |
| Integration Tests (`test_task_8_31e_groq_integration.py`) | 20 / 20 | 20 / 20 | PASS |
| Groq AI Suite (`test_groq_ai.py`) | 23 / 23 | 23 / 23 | PASS |
| TypeScript Check (`frontend`) | 0 errors | 0 errors | PASS |
