# Technical Design: Self-Service Onboarding Backend MVP

## Document Info

| Field | Value |
|-------|-------|
| **Status** | Draft |
| **Created** | 2026-02-19 |
| **PRD Reference** | `docs/PRD.md` |
| **Research Reference** | `pesquisa_onboarding_self_service_v2.md` |

---

## 1. Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **Framework** | FastAPI (Python 3.12+) | Async, auto OpenAPI docs, Pydantic native |
| **Database** | SQLite (MVP) | Zero setup, runs locally, swappable to PostgreSQL later |
| **LLM API** | OpenAI (GPT-4.1-mini) | Best cost/quality for structured output, current model in use |
| **Audio Transcription** | OpenAI Whisper / GPT-4o-mini-transcribe | Cheapest option at $0.003/min |
| **Web Scraping** | Playwright | Headless browser, handles JS-rendered sites |
| **Agent Orchestration** | LangGraph | State persistence for interview flow, model-agnostic, recommended in research |
| **CNPJ Lookup** | None (stored as reference only) | No API needed — user provides name, site does the rest |
| **Package Manager** | uv | Fastest Python package manager, simple, modern |
| **Testing** | pytest + httpx | Standard for FastAPI testing |

### Why NOT Docker for MVP

The MVP runs locally on macOS for validation. Setup should be:
```
uv sync
uv run uvicorn app.main:app --reload
```

Docker Compose (PostgreSQL + Redis + RabbitMQ) is for production — the dev team handles that later.

### External API Keys Required

| Service | Key | Where to get |
|---------|-----|-------------|
| **OpenAI** | `OPENAI_API_KEY` | platform.openai.com |

---

## 2. Project Structure

```
backend/
├── pyproject.toml                 # Dependencies (uv/pip)
├── .env.example                   # Template for environment variables
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app initialization, middleware, routers
│   ├── config.py                  # Settings from env vars (pydantic-settings)
│   ├── database.py                # SQLite setup, session management
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── orm.py                 # SQLAlchemy ORM models (Session table)
│   │   └── schemas.py             # Pydantic schemas (request/response/agent config)
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── sessions.py            # POST /sessions, GET /sessions/{id}
│   │   ├── enrichment.py          # POST /enrich, GET /enrichment
│   │   ├── interview.py           # POST /answer, GET /next, GET /progress
│   │   ├── audio.py               # POST /transcribe
│   │   ├── agent.py               # POST /generate, GET /agent, PUT /adjust
│   │   └── simulation.py          # POST /generate, GET /simulation
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── enrichment.py          # Website scraping + CNPJ + LLM extraction
│   │   ├── interview_agent.py     # LangGraph interview orchestration
│   │   ├── agent_generator.py     # Agent config generation via LLM
│   │   ├── simulation.py          # Simulation generation via LLM
│   │   └── transcription.py       # Whisper audio transcription
│   │
│   └── prompts/
│       ├── __init__.py
│       ├── enrichment.py          # Website data extraction prompt
│       ├── interview.py           # Follow-up generation + dynamic question prompts
│       ├── agent_generator.py     # Agent config generation prompt (structured output)
│       └── simulation.py          # Simulation conversation generation prompt
│
└── tests/
    ├── __init__.py
    ├── conftest.py                # Fixtures (test client, test DB, mock OpenAI)
    ├── test_sessions.py
    ├── test_enrichment.py
    ├── test_interview.py
    ├── test_audio.py
    ├── test_agent_generator.py
    └── test_simulation.py
```

---

## 3. Data Model

### Single Table: `onboarding_sessions`

For the MVP, one table stores the entire onboarding state. JSON fields hold flexible/complex data.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Session identifier |
| `status` | TEXT | `created` → `enriching` → `interviewing` → `generating` → `simulating` → `completed` |
| `company_name` | TEXT | Input from user |
| `company_website` | TEXT | Input from user |
| `company_cnpj` | TEXT (nullable) | Stored as reference for platform integration, not queried |
| `enrichment_data` | JSON | CompanyProfile from enrichment pipeline |
| `interview_state` | JSON | LangGraph state: questions asked, answers, what's next |
| `interview_responses` | JSON | Clean list of all Q&A pairs (extracted from state) |
| `smart_defaults` | JSON | Confirmed/adjusted default settings |
| `agent_config` | JSON | Generated AgentConfig (see PRD for schema) |
| `simulation_result` | JSON | Generated SimulationResult (see PRD for schema) |
| `created_at` | DATETIME | Session creation timestamp |
| `updated_at` | DATETIME | Last modification timestamp |

### Why one table?

- MVP simplicity: no joins, no migration complexity
- The session IS the unit of work — everything belongs to one onboarding flow
- JSON fields give flexibility during rapid iteration
- When dev team moves to PostgreSQL, they can normalize if needed (JSONB works great too)

---

## 4. API Endpoints

Base path: `/api/v1`

### Sessions

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions` | Create new onboarding session | `{ company_name: str, website: str, cnpj?: str }` | `{ session_id: uuid, status }` |
| `GET` | `/sessions/{id}` | Get session status and summary | — | Full session state |

### Enrichment

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions/{id}/enrich` | Start enrichment process | — (uses session's website/cnpj) | `{ status: "enriching" }` |
| `GET` | `/sessions/{id}/enrichment` | Get enrichment results | — | `CompanyProfile` JSON |

Enrichment is synchronous for MVP (< 30s). If too slow, can be made async later.

### Interview

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `GET` | `/sessions/{id}/interview/next` | Get next question to ask | — | `InterviewQuestion` (see below) |
| `POST` | `/sessions/{id}/interview/answer` | Submit answer to current question | `{ question_id: str, answer: str, source: "text"\|"audio" }` | `{ received: true, follow_up?: InterviewQuestion }` |
| `GET` | `/sessions/{id}/interview/progress` | Get interview completion status | — | `{ phase: "core"\|"dynamic"\|"defaults", answered: N, estimated_remaining: N }` |
| `POST` | `/sessions/{id}/interview/defaults` | Confirm/adjust smart defaults | `{ defaults: SmartDefaults }` | `{ confirmed: true }` |

**InterviewQuestion schema:**

```json
{
  "question_id": "core_1",
  "question_text": "What does your company sell or provide?",
  "question_type": "text",
  "options": null,
  "pre_filled_value": "Software de gestão para construtoras",
  "is_required": true,
  "supports_audio": true,
  "phase": "core",
  "context_hint": "Based on your website, it looks like you sell construction management software. Is this correct?"
}
```

For questions with options:
```json
{
  "question_id": "core_3",
  "question_text": "When do you consider an account past-due?",
  "question_type": "select",
  "options": [
    { "value": "d0", "label": "On the due date (D+0)" },
    { "value": "d1", "label": "1 day after (D+1)" },
    { "value": "d5", "label": "5 days after (D+5)" },
    { "value": "d15", "label": "15 days after (D+15)" },
    { "value": "d30", "label": "30 days after (D+30)" },
    { "value": "other", "label": "Other" }
  ],
  "pre_filled_value": null,
  "is_required": true,
  "supports_audio": true,
  "phase": "core",
  "context_hint": null
}
```

**Answer submission with follow-up:**

When the user submits an answer, the Interview Agent evaluates it. If it needs deepening, the response includes a `follow_up` question immediately:

```json
// POST /interview/answer
// Request:
{ "question_id": "core_4", "answer": "A gente liga e manda WhatsApp", "source": "text" }

// Response:
{
  "received": true,
  "follow_up": {
    "question_id": "followup_core4_1",
    "question_text": "Can you walk me through the steps? For example: when a payment is 5 days late, what happens first? Then what?",
    "question_type": "text",
    "options": null,
    "is_required": false,
    "supports_audio": true,
    "phase": "follow_up",
    "context_hint": "The more detail you provide about your current process, the better your agent will replicate it."
  }
}
```

### Audio

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions/{id}/audio/transcribe` | Transcribe audio to text | Multipart: `file` (audio) | `{ text: str, duration_seconds: float }` |

Accepted formats: webm, mp4, wav, mpeg. Max 25MB.

### Agent Generation

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions/{id}/agent/generate` | Generate agent config | — (uses session data) | `AgentConfig` JSON (see PRD) |
| `GET` | `/sessions/{id}/agent` | Get current agent config | — | `AgentConfig` JSON |
| `PUT` | `/sessions/{id}/agent/adjust` | Adjust config and re-generate | `{ adjustments: { tone?: str, max_discount?: int, ... } }` | Updated `AgentConfig` JSON |

### Simulation

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions/{id}/simulation/generate` | Generate simulated conversations | — (uses agent config) | `SimulationResult` JSON (see PRD) |
| `GET` | `/sessions/{id}/simulation` | Get simulation results | — | `SimulationResult` JSON |

---

## 5. Service Architecture

### 5.1 Enrichment Service

```
Input: website URL + company name
    ↓
Playwright scrapes website → raw HTML/text
    ↓
LLM (GPT-4.1-mini) receives:
  - Company name (provided by user)
  - Raw website content
  - Extraction prompt (structured output)
    ↓
Output: CompanyProfile JSON
```

**Key decisions:**
- Playwright runs headless Chromium to handle JS-rendered sites
- LLM extraction uses structured output (JSON mode) to ensure consistent schema
- CNPJ is stored in session for future platform integration but NOT queried
- If website scraping fails → return empty profile, user fills info manually in interview
- No external API costs

### 5.2 Interview Agent (LangGraph)

The Interview Agent is a **LangGraph state machine** that manages the conversational interview flow.

**State schema:**

```python
class InterviewState(TypedDict):
    enrichment_data: dict           # CompanyProfile from enrichment
    core_questions_remaining: list   # Core questions not yet asked
    current_question: dict | None    # Question currently being asked
    answers: list[dict]              # All Q&A pairs collected so far
    dynamic_questions_asked: int     # Count of AI-generated questions
    max_dynamic_questions: int       # Limit (default: 8)
    phase: str                       # "core" | "dynamic" | "defaults" | "complete"
    needs_follow_up: bool            # Whether current answer needs deepening
    follow_up_question: dict | None  # Generated follow-up if needed
```

**Graph nodes:**

```
START
  ↓
[initialize] → Load core questions, set enrichment context
  ↓
[select_next_question] → Pick next core question, or generate dynamic question
  ↓
[present_question] → Return question to user (pre-fill from enrichment if possible)
  ↓
  ... (user answers via API call) ...
  ↓
[process_answer] → Store answer, evaluate quality
  ↓
[evaluate_need_follow_up] → LLM decides if answer needs deepening
  ├── YES → [generate_follow_up] → Return follow-up question
  └── NO → [check_completion]
           ├── Core questions remain → [select_next_question]
           ├── Core done, dynamic budget remaining → [generate_dynamic_question]
           └── Interview complete → [present_defaults] → END
```

**How it works with the API:**

1. `GET /interview/next` → Runs graph until it reaches a "present question" state → returns question
2. `POST /interview/answer` → Feeds answer into graph → graph processes, evaluates → returns follow-up or signals "get next"
3. `GET /interview/progress` → Reads state → returns phase + count

**LangGraph state is persisted as JSON in the `interview_state` column of the session table.** This means the interview survives server restarts, context resets, etc.

**Dynamic question generation prompt (simplified):**

```
You are an expert debt collection consultant conducting an onboarding interview.

You have already collected these answers:
{answers_so_far}

You know this about the company from their website:
{enrichment_data}

Based on what you know so far, what is the SINGLE most important question
you still need answered to create a great collection agent for this company?

Consider:
- What's still unclear about their collection process?
- What scenarios might their agent face that we haven't covered?
- What policies or rules are missing?

Return a JSON question object.
```

### 5.3 Agent Generator

```
Input: CompanyProfile + all interview responses + confirmed defaults
    ↓
Build context prompt with ALL data organized in sections:
  - Company context (from enrichment)
  - Business model and billing (from interview)
  - Debtor profile (from interview)
  - Current collection process (from interview)
  - Tone and communication preferences (from interview)
  - Negotiation policies (from interview + defaults)
  - Guardrails and escalation rules (from interview + defaults)
  - Scenario handling (from interview)
    ↓
LLM (GPT-4.1-mini) with structured output → AgentConfig JSON
    ↓
Pydantic validation + sanity checks:
  - Discounts within configured limits
  - Hours within legal limits (08-20)
  - Required fields present
  - System prompt is coherent and complete
    ↓
Output: Validated AgentConfig JSON (stored in session)
```

**The system prompt generation is the most important part.** The LLM receives ALL context and generates a detailed, segment-specific system prompt that captures:
- Who the company is and what they sell
- How to address debtors (tone, formality, name usage)
- Negotiation rules (discounts, installments, when to offer)
- Escalation rules (when to pass to human)
- Prohibited actions and words
- Specific scenario handling
- Payment instructions

### 5.4 Simulation Service

```
Input: AgentConfig JSON
    ↓
Single LLM call with prompt:
  "Generate 2 realistic debt collection conversations in Portuguese.

   Scenario 1: Cooperative debtor (wants to pay, needs conditions)
   Scenario 2: Resistant debtor (contests debt, demands big discount)

   The collection agent follows these rules exactly:
   {agent_config}

   Each conversation: 8-15 messages.
   The agent MUST follow the configured tone, discount limits, and guardrails.
   Output as JSON with the SimulationResult schema."
    ↓
Output: SimulationResult JSON with 2 conversations
```

**Simple by design**: No real-time agent-to-agent simulation. Just a well-prompted LLM generating realistic conversations. This is fast (single call, < 20s) and sufficient for the AHA Moment.

### 5.5 Transcription Service

```
Input: Audio file (from user upload)
    ↓
Send to OpenAI Audio API:
  - Model: gpt-4o-mini-transcribe (cheapest at $0.003/min)
  - Language: "pt" (Portuguese)
    ↓
Output: { text: str, duration_seconds: float }
```

---

## 6. Prompt Architecture

All prompts live in `app/prompts/` as Python files with template strings. This makes them:
- Version-controlled
- Easy to iterate on
- Testable (can unit test prompt generation)

### Prompt files:

| File | Purpose | Input | Output |
|------|---------|-------|--------|
| `enrichment.py` | Extract structured company data from raw website content | Raw HTML/text + CNPJ data | CompanyProfile JSON |
| `interview.py` | Generate follow-up questions, evaluate answer quality, generate dynamic questions | Interview state + answers | InterviewQuestion JSON |
| `agent_generator.py` | Generate complete agent config from all collected data | CompanyProfile + all answers + defaults | AgentConfig JSON |
| `simulation.py` | Generate 2 simulated collection conversations | AgentConfig | SimulationResult JSON |

Each prompt file exports:
- `build_prompt(**kwargs) -> str` — Constructs the full prompt from inputs
- `SYSTEM_PROMPT: str` — The system message (if applicable)

---

## 7. LangGraph Interview Agent Detail

### Why LangGraph (not just sequential logic)?

A simple sequential questionnaire (ask Q1, Q2, Q3...) won't work because:
1. **Follow-ups are conditional**: Some answers need deepening, others don't
2. **Dynamic questions depend on ALL previous answers**: The AI needs to see the full picture to ask the right next question
3. **State must persist across API calls**: The interview spans multiple HTTP requests
4. **The flow is a graph, not a line**: Core → follow-up → back to core → dynamic → follow-up → defaults

LangGraph gives us:
- **State management**: TypedDict with all interview data, persisted as JSON
- **Conditional edges**: "If answer needs deepening, go to follow-up node; else go to next question"
- **Checkpointing**: State saved after every node, survives crashes
- **Clear flow visualization**: The graph IS the documentation

### State Persistence

For the SQLite MVP, LangGraph state is serialized to JSON and stored in the `interview_state` column. On each API call:

1. Load state from DB
2. Create LangGraph with loaded state
3. Run until next "waiting for user" point
4. Serialize state back to DB

For production (PostgreSQL), LangGraph has native PostgreSQL checkpointing via `langgraph-checkpoint-postgres`.

### Interview Completion Criteria

The interview is "complete" when:
1. All core questions are answered (10 questions)
2. AI determines no critical gaps remain, OR dynamic question budget exhausted (max 8)
3. Smart defaults are confirmed by user

The AI evaluates completeness with a prompt:

```
Given all the information collected so far, rate from 1-10 how confident
you are that we can generate a high-quality collection agent.

If below 7: what single question would increase confidence the most?
If 7+: the interview is complete.
```

---

## 8. Error Handling

| Scenario | Handling |
|----------|----------|
| Website scraping fails (timeout, blocked) | Continue with CNPJ data only. Return partial enrichment. |
| CNPJ not found in BrasilAPI | Continue with website data only. |
| Both enrichment sources fail | Return empty profile. User fills info manually in interview. |
| OpenAI API error (rate limit, timeout) | Retry once with exponential backoff. If still fails, return error to user. |
| Audio file too large (>25MB) | Reject with clear error message. |
| Audio transcription fails | Return error, suggest user type the answer instead. |
| LLM returns invalid JSON (structured output) | Retry once. If still invalid, log error and return generic error. |
| Agent config fails sanity check | Log specific failures, attempt auto-correction (e.g., cap discount at limit). |

---

## 9. How to Run Locally

### Prerequisites

- macOS (or Linux)
- Python 3.12+
- An OpenAI API key

### Setup

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to backend
cd onboarding_initiative/backend

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run the server
uv run uvicorn app.main:app --reload --port 8000
```

### Access

- **Swagger UI**: http://localhost:8000/docs (interactive API testing)
- **OpenAPI spec**: http://localhost:8000/openapi.json

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_enrichment.py -v

# Run with coverage
uv run pytest --cov=app
```

---

## 10. Key Dependencies

| Package | Purpose | Version |
|---------|---------|---------|
| `fastapi` | Web framework | latest |
| `uvicorn` | ASGI server | latest |
| `sqlalchemy` | ORM (SQLite) | latest |
| `pydantic` | Data validation, schemas | v2 (bundled with FastAPI) |
| `pydantic-settings` | Environment config | latest |
| `openai` | OpenAI API client | latest |
| `langgraph` | Interview agent orchestration | latest |
| `playwright` | Web scraping (headless browser) | latest |
| `httpx` | HTTP client (async requests) | latest |
| `python-multipart` | File upload support (audio) | latest |
| `pytest` | Testing | latest |
| `pytest-asyncio` | Async test support | latest |

### Playwright Setup Note

Playwright requires browser binaries. After `uv sync`:
```bash
uv run playwright install chromium
```

This downloads a headless Chromium (~150MB). Only needed once.

---

## 11. Future Production Considerations (dev team)

When the dev team takes this to production, they'll likely need to:

| Change | From (MVP) | To (Production) |
|--------|-----------|-----------------|
| Database | SQLite | PostgreSQL + JSONB |
| State persistence | JSON in SQLite column | LangGraph PostgreSQL checkpointer |
| Audio processing | Sync (< 5s) | Async via task queue |
| Auth | None | JWT (existing platform) |
| Deployment | `uvicorn` local | Docker + ECS Fargate |
| Monitoring | None | OpenTelemetry + LangSmith |
| Rate limiting | None | Redis-based |
| File storage | Local filesystem | S3 |
| CORS | Open | Restricted to Lovable + production domains |

The MVP code is structured to make these swaps easy:
- Database layer is abstracted via SQLAlchemy (swap engine URL)
- Services are injected via FastAPI dependencies (swap implementations)
- Config via environment variables (same code, different `.env`)
