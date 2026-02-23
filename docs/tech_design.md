# Technical Design: Self-Service Onboarding

## Document Info

| Field | Value |
|-------|-------|
| **Status** | Active |
| **Created** | 2026-02-19 |
| **Updated** | 2026-02-23 |
| **PRD Reference** | `docs/PRD.md` |

---

## 1. Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Backend Framework** | FastAPI (Python 3.13) | Async, auto OpenAPI docs, Pydantic native |
| **Database** | SQLite (MVP) → PostgreSQL (production) | Zero setup locally, swappable |
| **LLM API** | OpenAI GPT-4.1-mini | Best cost/quality for structured output |
| **Audio Transcription** | OpenAI GPT-4o-mini-transcribe | $0.003/min, Portuguese |
| **Web Scraping** | Playwright (headless Chromium) | Handles JS-rendered sites |
| **Interview Engine** | LangGraph | State machine for interview flow |
| **Package Manager** | uv | Fastest Python package manager |
| **Testing** | pytest + httpx | Standard for FastAPI |
| **Frontend** | Lovable (React/TypeScript) | Existing platform at `portal.financecrew.ai` |
| **Platform Backend** | Directus | REST/GraphQL CMS for users, campaigns, agents |
| **Deploy** | Railway or Render | Python + Playwright support |

### External API Keys Required

| Service | Key | Purpose |
|---------|-----|---------|
| **OpenAI** | `OPENAI_API_KEY` | All LLM calls + transcription |
| **Search** | `SEARCH_API_KEY` | Web search API (Serper/Google CSE) — company research (T33) |

---

## 2. Project Structure

```
backend/
├── pyproject.toml                 # Dependencies (uv)
├── .env.example                   # Template for environment variables
├── cli_test.py                    # Interactive CLI for manual testing
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, middleware, routers
│   ├── config.py                  # Settings from env vars (pydantic-settings)
│   ├── database.py                # SQLite setup, session management
│   │
│   ├── models/
│   │   ├── orm.py                 # SQLAlchemy ORM (OnboardingSession table)
│   │   └── schemas.py             # Pydantic schemas (50+ models)
│   │
│   ├── routers/
│   │   ├── sessions.py            # POST /sessions, GET /sessions/{id}
│   │   ├── enrichment.py          # POST /enrich, GET /enrichment
│   │   ├── interview.py           # GET /next, POST /answer, GET /progress, GET/POST /review
│   │   ├── audio.py               # POST /transcribe
│   │   ├── agent.py               # POST /generate, GET /agent, PUT /adjust
│   │   └── simulation.py          # POST /generate, GET /simulation
│   │
│   ├── services/
│   │   ├── enrichment.py          # scrape_website() + extract_company_profile()
│   │   ├── web_research.py        # search_company() — web search enrichment (T33)
│   │   ├── interview_agent.py     # LangGraph state machine (InterviewState)
│   │   ├── report_generator.py    # generate_report() — OnboardingReport SOP (T34, replaces agent_generator)
│   │   ├── simulation.py          # generate_simulation()
│   │   └── transcription.py       # transcribe_audio()
│   │
│   └── prompts/
│       ├── enrichment.py          # Website extraction prompt
│       ├── interview.py           # Core questions, dynamic bank, follow-up prompts
│       ├── report_generator.py    # OnboardingReport SOP generation prompt (T34, replaces agent_generator)
│       └── simulation.py          # Simulation conversation prompt
│
└── tests/
    ├── conftest.py                # Fixtures (test client, test DB)
    ├── test_sessions.py           # 6 tests
    ├── test_enrichment.py         # 10 tests
    ├── test_interview.py          # 51 tests
    ├── test_audio.py              # 11 tests
    ├── test_agent_config.py       # 3 tests
    ├── test_agent_generator.py    # 17 tests
    ├── test_avatar.py             # 7 tests (to be removed in T32)
    ├── test_simulation.py         # 12 tests
    └── test_integration.py        # 1 test (real OpenAI API, @pytest.mark.integration)
```

**Total: 130 tests passing** (122 unit + 1 integration + 7 avatar — avatar tests removed in T32)

---

## 3. Data Model

### Single Table: `onboarding_sessions`

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Session identifier |
| `status` | TEXT | `created` → `enriching` → `enriched` → `interviewing` → `interviewed` → `generating` → `generated` → `simulating` → `completed` |
| `company_name` | TEXT | Input from user |
| `company_website` | TEXT | Input from user |
| `company_cnpj` | TEXT (nullable) | Stored as reference, not queried |
| `enrichment_data` | JSON | CompanyProfile from enrichment |
| `interview_state` | JSON | LangGraph state (questions, answers, phase) |
| `interview_responses` | JSON | Clean list of all Q&A pairs |
| `agent_config` | JSON | Generated OnboardingReport SOP (T34, replaces AgentConfig) |
| `simulation_result` | JSON | 2 simulated conversations |
| `created_at` | DATETIME | Session creation timestamp |
| `updated_at` | DATETIME | Last modification timestamp |

---

## 4. API Endpoints

Base path: `/api/v1`

### Sessions

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions` | Create session | `{ company_name, website, cnpj? }` | `201 { session_id, status }` |
| `GET` | `/sessions/{id}` | Get full session | — | Full session state |

### Enrichment

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `POST` | `/sessions/{id}/enrich` | Scrape + extract | `{ status: "enriched", enrichment_data: CompanyProfile }` |
| `GET` | `/sessions/{id}/enrichment` | Get results | CompanyProfile JSON |

### Interview

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `GET` | `/sessions/{id}/interview/next` | Get next question | — | InterviewQuestion or `{ phase, message }` |
| `POST` | `/sessions/{id}/interview/answer` | Submit answer | `{ question_id, answer, source }` | `{ received, next_question, follow_up? }` |
| `GET` | `/sessions/{id}/interview/progress` | Progress status | — | `{ phase, core_answered, dynamic_answered, is_complete }` |
| `GET` | `/sessions/{id}/interview/review` | Get review summary | — | `{ summary, confirmed }` |
| `POST` | `/sessions/{id}/interview/review` | Confirm review | `{ additional_notes? }` | `{ confirmed, phase: "complete" }` |

### Audio

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions/{id}/audio/transcribe` | Transcribe audio | Multipart file | `{ text, duration_seconds }` |

### Agent

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions/{id}/agent/generate` | Generate SOP report | — | `{ status: "generated", onboarding_report }` |
| `GET` | `/sessions/{id}/agent` | Get report | — | OnboardingReport JSON |

### Simulation

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `POST` | `/sessions/{id}/simulation/generate` | Generate 2 conversations | `{ status: "completed", simulation_result }` |
| `GET` | `/sessions/{id}/simulation` | Get results | SimulationResult JSON |

---

## 5. API Response Schemas (complete reference)

These are the exact JSON shapes returned by the API. The frontend must use these field names and types.

### InterviewQuestion

```json
{
  "question_id": "core_1",
  "question_text": "O que sua empresa vende ou oferece?",
  "question_type": "text | select | multiselect",
  "options": [
    { "value": "pix", "label": "PIX" },
    { "value": "boleto", "label": "Boleto" }
  ],
  "pre_filled_value": "string ou null",
  "is_required": true,
  "supports_audio": true,
  "phase": "core | dynamic | follow_up | review",
  "context_hint": "string ou null"
}
```

Notes:
- `options` is `null` for `text` type, array of `{value, label}` for `select`/`multiselect`
- `pre_filled_value` is only set when enrichment data matches the question
- For `select`: answer = single `value` (e.g. `"d5"`)
- For `multiselect`: answer = comma-separated `value`s (e.g. `"pix,boleto,cartao_credito"`)
- For `text`: answer = free text string

### POST /interview/answer response

When `next_question` exists:
```json
{
  "received": true,
  "next_question": { /* InterviewQuestion */ },
  "follow_up": { /* InterviewQuestion, only if next is a follow-up */ }
}
```

When no next question:
```json
{
  "received": true,
  "next_question": null,
  "phase": "review | dynamic",
  "message": "Entrevista concluída. Prossiga para revisão."
}
```

### InterviewProgressResponse

```json
{
  "phase": "not_started | core | dynamic | review | complete",
  "total_answered": 14,
  "core_answered": 12,
  "core_total": 12,
  "dynamic_answered": 2,
  "estimated_remaining": 6,
  "is_complete": false
}
```

### CompanyProfile

```json
{
  "company_name": "CollectAI",
  "segment": "Fintech / SaaS de cobrança",
  "products_description": "Plataforma de cobrança automatizada via WhatsApp",
  "target_audience": "PMEs brasileiras com problemas de inadimplência",
  "communication_tone": "Profissional e empático",
  "payment_methods_mentioned": "PIX, boleto, cartão de crédito",
  "collection_relevant_context": "Foco em recuperação amigável antes de judicial"
}
```

### Interview Review

```json
{
  "summary": {
    "core_0": "Sofia",
    "core_1": "Plataforma SaaS de cobrança automatizada",
    "core_2": "pix,boleto,cartao_credito",
    "...": "..."
  },
  "confirmed": false
}
```

### OnboardingReport (planned — T34, replaces AgentConfig)

```json
{
  "agent_identity": {
    "name": "Sofia"
  },
  "company": {
    "name": "CollectAI",
    "segment": "Fintech / SaaS de cobrança",
    "products": "Plataforma de cobrança automatizada via WhatsApp",
    "target_audience": "PMEs brasileiras",
    "website": "collectai.com.br"
  },
  "enrichment_summary": {
    "website_analysis": "Resumo do scraping do site...",
    "web_research": "Resumo da pesquisa web..."
  },
  "collection_profile": {
    "debt_type": "Recorrente (mensalidades SaaS)",
    "typical_debtor_profile": "PMEs com faturamento...",
    "business_specific_objections": "Serviço não foi entregue conforme...",
    "payment_verification_process": "Conferimos no ERP...",
    "sector_regulations": "LGPD limita exposição de dados..."
  },
  "collection_policies": {
    "overdue_definition": "Até 5 dias lembrete amigável, 5-30 cobrança firme...",
    "discount_policy": "Até 10% para pagamento à vista...",
    "installment_policy": "Parcelamos em até 12x, mínimo R$50...",
    "interest_policy": "Juros de 1% ao mês...",
    "penalty_policy": "Multa de 2% sobre o valor...",
    "payment_methods": ["pix", "boleto", "cartao_credito"],
    "escalation_triggers": ["solicita_humano", "acao_judicial", "agressivo"],
    "escalation_custom_rules": "Quando o cliente é empresa parceira...",
    "collection_flow_description": "Primeiro envio de lembrete por WhatsApp..."
  },
  "communication": {
    "tone_style": "friendly",
    "prohibited_actions": ["Ameaçar", "Expor a dívida a terceiros"],
    "brand_specific_language": "Usar 'parceiro' em vez de 'devedor'..."
  },
  "guardrails": {
    "never_do": ["Ameaçar o devedor"],
    "never_say": ["processo", "cadeia"],
    "must_identify_as_ai": true,
    "follow_up_interval_days": 3,
    "max_attempts_before_stop": 10
  },
  "expert_recommendations": "Análise detalhada (300+ palavras) de um especialista em cobrança sobre o processo ideal para esta empresa...",
  "metadata": {
    "generated_at": "2026-02-22T10:30:00",
    "session_id": "uuid",
    "model": "gpt-4.1-mini",
    "version": 1
  }
}
```

This replaces the old AgentConfig. Key difference: `expert_recommendations` is a comprehensive SOP analysis, not a system_prompt. A downstream system will use this report to create the actual agent.

### SimulationResult

```json
{
  "scenarios": [
    {
      "scenario_type": "cooperative | resistant",
      "debtor_profile": "Maria, 45 anos, dona de padaria, dívida de R$1.200",
      "conversation": [
        { "role": "agent", "content": "Olá Maria! Aqui é a assistente..." },
        { "role": "debtor", "content": "Oi, tudo bem?" }
      ],
      "outcome": "Devedor aceitou parcelamento em 3x de R$400",
      "metrics": {
        "negotiated_discount_pct": 0,
        "final_installments": 3,
        "payment_method": "pix",
        "resolution": "full_payment | installment_plan | escalated | no_resolution"
      }
    }
  ],
  "metadata": {}
}
```

### WebResearchResult (planned — T33)

```json
{
  "company_description": "CollectAI é uma fintech de cobrança...",
  "products_and_services": "Plataforma SaaS de automação de cobrança...",
  "sector_context": "Mercado de cobrança digital em crescimento...",
  "reputation_summary": "Avaliações positivas no Google, sem reclamações no Reclame Aqui...",
  "collection_relevant_insights": "Foco em recuperação amigável, sem cobrança judicial..."
}
```

### Swagger / OpenAPI

Interactive API docs are auto-generated at `{BACKEND_URL}/docs`. This is the authoritative reference for all schemas and can be used by the frontend team to test endpoints interactively.

---

## 6. Service Architecture

### 6.1 Enrichment Service

```
website URL + company name
  → Playwright scrapes (domcontentloaded + 3s wait, 30s timeout)
  → LLM extracts CompanyProfile (JSON mode)
  → Retry once on failure, fallback to minimal profile
```

### 6.2 Interview Agent (LangGraph)

**State**: `InterviewState` TypedDict with 10 fields (enrichment_data, core_questions_remaining, current_question, answers, dynamic_questions_asked, max_dynamic_questions, phase, needs_follow_up, follow_up_question, follow_up_count)

**Two graphs**:
- Full graph (initialize + select + present) for `create_interview()`
- Next-question graph (select + present) for `get_next_question()`

**Flow**:
```
initialize → 10 core questions (with up to 2 follow-ups each, no follow-ups on dynamic)
  → dynamic phase (LLM generates up to 3 questions, evaluates completeness)
  → review phase (user confirms answers + optional notes)
  → complete
```

**Enrichment pre-fill**: core_1 (products), core_3 (payment methods), core_4 (tone) — applied at pop time.

**Frustration detection**: Hardcoded signals (13 Portuguese phrases) skip follow-up without LLM call.

### 6.3 Web Research Service (planned — T33)

```
company_name + website
  → Search API (Serper) — 2-3 queries about the company
  → Collect top snippets
  → LLM consolidation → WebResearchResult
  → Combined with CompanyProfile in enrichment_data
```

### 6.4 Report Generator (planned — T34, replaces Agent Generator)

```
CompanyProfile + WebResearchResult + interview_responses + agent_name
  → build_prompt() — enrichment sections + all interview answers
  → GPT-4.1-mini structured output → OnboardingReport (SOP)
  → Includes expert_recommendations (300+ words)
  → 2-attempt retry
```

### 6.5 Simulation Service

```
OnboardingReport → build_simulation_prompt() — SOP data + scenario instructions
  → GPT-4.1-mini → SimulationResult (2 scenarios, 8-15 msgs each)
  → Sanity checks (non-fatal): scenario count, conversation length
  → 2-attempt retry
```

### 6.6 Transcription Service

```
audio bytes + content_type → validate (format, size <25MB)
  → GPT-4o-mini-transcribe (language="pt")
  → { text, duration_seconds }
  → Retry once on failure
```

---

## 7. Deploy Architecture — PENDING

### Requirements

| Item | Details |
|------|---------|
| **CORS** | `portal.financecrew.ai` + `localhost:*` (dev) |
| **Runtime** | Python 3.13 + Playwright Chromium |
| **Env vars** | `OPENAI_API_KEY`, `SEARCH_API_KEY`, `ALLOWED_ORIGINS`, `DATABASE_URL` (optional) |
| **Database** | SQLite (MVP) → PostgreSQL (production) |
| **Platform** | Railway (recommended) or Render |

### Dockerfile (planned)

```dockerfile
FROM python:3.13-slim
# Install system deps for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 \
    libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 libgtk-3-0
# Install uv + project
COPY . /app
WORKDIR /app
RUN pip install uv && uv sync --frozen
RUN uv run playwright install chromium
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### CORS Config (planned)

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. Frontend Architecture — PENDING

### Overview

6 telas no Lovable que conectam com o backend onboarding via REST API.

### Tela Flow

```
[Boas-vindas] → [Enriquecimento] → [Entrevista] → [Revisão] → [Relatório SOP] → [Simulação]
     POST           POST+GET        GET+POST loop   GET+POST     POST+GET        POST+GET
    /sessions       /enrich         /interview/*     /review      /agent/*        /simulation/*
```

### Estado no Frontend

O frontend precisa manter:
- `session_id` — criado no step 1, usado em todos os outros
- `current_question` — recebido da API, apresentado ao usuário
- `phase` — "core" | "dynamic" | "review" | "complete"
- `progress` — core_answered, dynamic_answered, estimated_remaining

**Não precisa manter**: answers (backend persiste), interview_state (backend gerencia).

### Chamadas de API

O frontend chama `{BACKEND_URL}/api/v1/...` com JSON. Todos os endpoints são síncronos (sem WebSocket). Loading states são necessários para chamadas lentas (enrich ~15s, generate ~15s, simulate ~20s).

**Referência completa**: Swagger UI em `{BACKEND_URL}/docs` — todos os schemas e endpoints interativos. Ver também Section 5 deste documento para os schemas de resposta completos com exemplos JSON.

### Áudio (transcription)

O frontend pode oferecer gravação de áudio como alternativa ao texto. Fluxo:
1. Usuário clica no ícone de microfone → `MediaRecorder API` (browser nativo)
2. Grava áudio em formato `webm` (default do MediaRecorder)
3. Ao parar, envia para: `POST {BACKEND_URL}/api/v1/sessions/{id}/audio/transcribe` (multipart/form-data, campo `file`)
4. Resposta: `{ "text": "transcrição em português", "duration_seconds": 12.5 }`
5. O texto transcrito é usado como `answer` no `POST /interview/answer` com `source: "audio"`
6. Formatos aceitos: webm, mp4, wav, mpeg, ogg, flac, m4a. Limite: 25MB.

---

## 9. How to Run

### Backend (local)

```bash
cd backend && uv sync
uv run playwright install chromium
cp .env.example .env  # Add OPENAI_API_KEY
uv run uvicorn app.main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

### Interactive CLI Test

```bash
cd backend && uv run python cli_test.py
# Walks through the full flow in the terminal
```

### Run Tests

```bash
cd backend
uv run pytest                           # All tests (including integration)
uv run pytest -m "not integration"      # Unit tests only (~5s)
uv run pytest -m integration -v         # Integration test only (~2.5min, needs OpenAI key)
```

---

## 10. Key Design Decisions (from development)

| Decision | Reason |
|----------|--------|
| 10 core questions (simplified from 16) | Financial details (juros, multa, parcelamento) come from a separate spreadsheet. Interview focuses on operational context with mostly select/multiselect for speed. |
| Max 3 dynamic questions (reduced from 8) | Agent is already expert — fewer but better targeted questions needed |
| No follow-ups on dynamic phase | Reduces interview fatigue; dynamic answers are already contextual |
| Frustration detection (hardcoded signals) | 13 Portuguese phrases skip follow-up without LLM call |
| OnboardingReport SOP replaces AgentConfig | Output is a structured report for downstream consumption, not a ready-to-use system_prompt |
| Web research in enrichment | Website alone doesn't capture full context; search adds reputation, sector info |
| Avatar removed from onboarding | Avatar upload/selection handled in the platform (Directus), not during onboarding |
| Two LangGraph graphs | Full graph (with initialize) for create_interview(), next-question graph for get_next_question() |
| Enrichment pre-fill at pop time | Not at initialization — allows enrichment to arrive after interview start |
| Max 2 follow-ups per question | Prevents infinite loops while allowing meaningful deepening |
| Confidence threshold >= 7 for completion | Balances thoroughness with brevity |

---

## 11. Future Production Considerations

| Change | From (MVP) | To (Production) |
|--------|-----------|-----------------|
| Database | SQLite | PostgreSQL (Railway built-in) |
| Auth | None (platform handles) | JWT validation from Directus |
| Deployment | `uvicorn` local | Docker on Railway/Render |
| CORS | Open | Restricted to `portal.financecrew.ai` |
| Monitoring | None | OpenTelemetry + LangSmith |
| Rate limiting | None | Redis-based |
| Report storage | Backend onboarding DB | Directus (via API or direct DB write) |
