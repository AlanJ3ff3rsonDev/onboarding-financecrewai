# Technical Design: Self-Service Onboarding

## Document Info

| Field | Value |
|-------|-------|
| **Status** | Active |
| **Created** | 2026-02-19 |
| **Updated** | 2026-02-20 |
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
│   │   ├── interview.py           # GET /next, POST /answer, GET /progress, GET/POST /defaults
│   │   ├── audio.py               # POST /transcribe
│   │   ├── agent.py               # POST /generate, GET /agent, PUT /adjust
│   │   └── simulation.py          # POST /generate, GET /simulation
│   │
│   ├── services/
│   │   ├── enrichment.py          # scrape_website() + extract_company_profile()
│   │   ├── interview_agent.py     # LangGraph state machine (InterviewState)
│   │   ├── agent_generator.py     # generate_agent_config() + adjust_agent_config()
│   │   ├── simulation.py          # generate_simulation()
│   │   └── transcription.py       # transcribe_audio()
│   │
│   └── prompts/
│       ├── enrichment.py          # Website extraction prompt
│       ├── interview.py           # Core questions, dynamic bank, follow-up prompts
│       ├── agent_generator.py     # Agent config generation prompt
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
    ├── test_simulation.py         # 12 tests
    └── test_integration.py        # 1 test (real OpenAI API, @pytest.mark.integration)
```

**Total: 120 tests passing** (119 unit + 1 integration)

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
| `smart_defaults` | JSON | Confirmed default settings (8 fields) |
| `agent_config` | JSON | Generated AgentConfig (versioned) |
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
| `GET` | `/sessions/{id}/interview/defaults` | Get defaults | — | `{ defaults: SmartDefaults, confirmed }` |
| `POST` | `/sessions/{id}/interview/defaults` | Confirm defaults | SmartDefaults | `{ confirmed, defaults, phase: "complete" }` |

### Audio

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions/{id}/audio/transcribe` | Transcribe audio | Multipart file | `{ text, duration_seconds }` |

### Agent

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions/{id}/agent/generate` | Generate config | — | `{ status: "generated", agent_config }` |
| `GET` | `/sessions/{id}/agent` | Get config | — | AgentConfig JSON |
| `PUT` | `/sessions/{id}/agent/adjust` | Adjust + regenerate | `{ adjustments: { "dotted.path": value } }` | `{ status: "adjusted", agent_config }` |

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
  "phase": "core | dynamic | follow_up | defaults",
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
  "phase": "defaults | dynamic",
  "message": "Entrevista concluída. Prossiga para confirmação dos padrões."
}
```

### InterviewProgressResponse

```json
{
  "phase": "not_started | core | dynamic | defaults | complete",
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

### SmartDefaults

```json
{
  "follow_up_interval_days": 3,
  "max_contact_attempts": 10,
  "use_first_name": true,
  "identify_as_ai": true,
  "min_installment_value": 50.0,
  "discount_strategy": "only_when_resisted | proactive | escalating",
  "payment_link_generation": true,
  "max_discount_installment_pct": 5.0
}
```

Validation: `follow_up_interval_days >= 1`, `max_contact_attempts >= 1`, `min_installment_value >= 0`, `max_discount_installment_pct` 0-50.

### AgentConfig

```json
{
  "agent_type": "compliant | non_compliant",
  "company_context": {
    "name": "string",
    "segment": "string",
    "products": "string",
    "target_audience": "string"
  },
  "system_prompt": "string (>200 chars, full prompt for the collection agent)",
  "tone": {
    "style": "formal | friendly | empathetic | assertive",
    "use_first_name": true,
    "prohibited_words": ["ameaçar", "processar"],
    "preferred_words": ["resolver", "parceria"],
    "opening_message_template": "string"
  },
  "negotiation_policies": {
    "max_discount_full_payment_pct": 10.0,
    "max_discount_installment_pct": 5.0,
    "max_installments": 12,
    "min_installment_value_brl": 50.0,
    "discount_strategy": "only_when_resisted | proactive | escalating",
    "payment_methods": ["pix", "boleto"],
    "can_generate_payment_link": true
  },
  "guardrails": {
    "never_do": ["Ameaçar o devedor", "Revelar dados de terceiros"],
    "never_say": ["processo", "cadeia"],
    "escalation_triggers": ["Devedor solicita humano", "Dívida alta"],
    "follow_up_interval_days": 3,
    "max_attempts_before_stop": 10,
    "must_identify_as_ai": true
  },
  "scenario_responses": {
    "already_paid": "string — como responder quando devedor diz que já pagou",
    "dont_recognize_debt": "string — quando não reconhece a dívida",
    "cant_pay_now": "string — quando não pode pagar agora",
    "aggressive_debtor": "string — quando devedor é agressivo"
  },
  "tools": ["generate_payment_link", "check_payment_status"],
  "metadata": {
    "version": 1,
    "generated_at": "2026-02-20T10:30:00",
    "onboarding_session_id": "uuid",
    "generation_model": "gpt-4.1-mini"
  }
}
```

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

### AgentAdjustRequest

```json
{
  "adjustments": {
    "tone.style": "empathetic",
    "negotiation_policies.max_discount_full_payment_pct": 20,
    "guardrails.must_identify_as_ai": false
  }
}
```

Uses dotted-path notation. Only text-derived fields (`system_prompt`, `scenario_responses`, `tone.opening_message_template`) are regenerated by LLM; all others are applied directly.

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
initialize → 12 core questions (with up to 2 follow-ups each)
  → dynamic phase (LLM generates questions, evaluates completeness)
  → defaults phase (user confirms/adjusts)
  → complete
```

**Enrichment pre-fill**: core_1 (products), core_2 (payment methods), core_5 (tone) — applied at pop time.

### 6.3 Agent Generator

```
CompanyProfile + interview_responses + smart_defaults
  → build_prompt() — 8 sections + mapping hints + JSON schema
  → GPT-4.1-mini structured output → AgentConfig
  → Sanity checks: discount caps, prompt quality (>200 chars), range clamping
  → 2-attempt retry
```

### 6.4 Simulation Service

```
AgentConfig → build_simulation_prompt() — system prompt + 8 config sections + scenario instructions
  → GPT-4.1-mini → SimulationResult (2 scenarios, 8-15 msgs each)
  → Sanity checks (non-fatal): scenario count, conversation length
  → 2-attempt retry
```

### 6.5 Transcription Service

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
| **Env vars** | `OPENAI_API_KEY`, `ALLOWED_ORIGINS`, `DATABASE_URL` (optional) |
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
[Boas-vindas] → [Enriquecimento] → [Entrevista] → [Defaults] → [Agente] → [Simulação]
     POST           POST+GET        GET+POST loop   GET+POST     POST+GET    POST+GET
    /sessions       /enrich         /interview/*     /defaults    /agent/*    /simulation/*
```

### Estado no Frontend

O frontend precisa manter:
- `session_id` — criado no step 1, usado em todos os outros
- `current_question` — recebido da API, apresentado ao usuário
- `phase` — "core" | "dynamic" | "defaults" | "complete"
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
| 12 core questions (expanded from PRD's 10) | Added juros (core_8) and multa (core_9). All financial questions have explicit "none" option. |
| No slider type in questions | Changed core_6 from slider to select for consistency |
| Two LangGraph graphs | Full graph (with initialize) for create_interview(), next-question graph for get_next_question() |
| Enrichment pre-fill at pop time | Not at initialization — allows enrichment to arrive after interview start |
| Contact hours removed from SmartDefaults | Messages are always available — timing is user-controlled |
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
| Agent storage | Backend onboarding DB | Directus (via API or direct DB write) |
