# Tasks Archive (M0-M6) — Completed

Archived from `tasks.md`. Full task definitions for all completed milestones.
For active/pending tasks, see `tasks.md`.

---

## M0: Project Setup (T01-T04) — DONE

### T01: Initialize project structure
Create the project skeleton with all folders, dependencies, and configuration.
Status: `done`

### T02: FastAPI app with health endpoint
Running FastAPI server with GET /health.
Status: `done`

### T03: Database setup + session model
SQLite database with onboarding_sessions table and CRUD.
Status: `done`

### T04: Session API endpoints
POST /sessions + GET /sessions/{id} endpoints.
Status: `done`

---

## M1: Enrichment (T05-T07) — DONE

### T05: Website scraping service
Playwright headless Chromium scraping with domcontentloaded + 3s wait.
Status: `done`

### T06: LLM extraction service
GPT-4.1-mini extracts CompanyProfile from website text.
Status: `done`

### T07: Enrichment API endpoint
POST /enrich + GET /enrichment endpoints.
Status: `done`

---

## M2: Interview (T08-T17) — DONE

### T08: Core questions data structure
16 InterviewQuestion objects + DYNAMIC_QUESTION_BANK.
Status: `done`

### T09: LangGraph interview state + basic graph
Two StateGraph instances, enrichment pre-fill for core_1/2/5, serialization.
Status: `done`

### T10: Interview "next question" endpoint
GET /interview/next (idempotent, initializes on first call).
Status: `done`

### T11: Interview "submit answer" endpoint
POST /interview/answer with question_id validation.
Status: `done`

### T12: AI follow-up evaluation + generation
evaluate_and_maybe_follow_up(), max 2 follow-ups per question, text-only.
Status: `done`

### T13: Dynamic question generation
LLM generates dynamic questions + evaluates completeness (confidence >= 7).
Status: `done`

### T14: Interview progress endpoint + completion
GET /interview/progress with phase-aware computation.
Status: `done`

### T15: Smart defaults confirmation endpoint
GET/POST /interview/defaults with validation (now review phase).
Status: `done`

### T16: Audio transcription service
gpt-4o-mini-transcribe, 11 MIME types, 2-attempt retry.
Status: `done`

### T17: Audio upload endpoint
POST /audio/transcribe with multipart file upload.
Status: `done`

---

## M3: Agent Generation (T18-T22) — DONE

### T18: AgentConfig Pydantic schema
8 nested Pydantic models with validation rules.
Status: `done`

### T19: Agent generation prompt
SYSTEM_PROMPT + build_prompt() with 8 organized sections.
Status: `done`

### T20: Agent generation service + sanity checks
generate_agent_config() with structured JSON output, sanity checks, 2-attempt retry.
Status: `done`

### T21: Agent generation endpoint
POST /agent/generate + GET /agent endpoints.
Status: `done`

### T22: Agent adjustment endpoint
PUT /agent/adjust with dotted-path adjustments, LLM regeneration, version incrementing.
Status: `done`

---

## M4: Simulation (T23-T24) — DONE

### T23: Simulation prompt + service
SimulationResult schema, build_simulation_prompt(), generate_simulation().
Status: `done`

### T24: Simulation endpoint
POST /simulation/generate + GET /simulation endpoints.
Status: `done`

---

## M5: Integration (T25) — DONE

### T25: End-to-end integration test
Full pipeline test with real OpenAI API + Playwright. ~2:35 execution.
Status: `done`

---

## M5.5: Refatoracao do Sistema de Perguntas (T26-T28) — DONE

### T26: Refatorar perguntas core + follow-up
core_12 reformulada, core_13/14 adicionadas, frustration detection.
Status: `done`

### T27: Refatorar perguntas dinamicas
max_dynamic 8->3, follow-ups off for dynamic, question bank cleaned.
Status: `done`

### T28: Atualizar prompt de geracao
Agent = expert philosophy in SYSTEM_PROMPT, build_prompt for core_13/14.
Status: `done`

---

## M5.6: Refinamento de Perguntas (T29) — DONE

### T29: core_3 texto aberto + core_10_open
core_3 select->text, core_10_open optional escalation question added. 14->15 core questions.
Status: `done`

---

## M5.7: Personalizacao do Agente + Reestruturacao Perguntas (T30-T32) — DONE

### T30: Pergunta de nome do agente (core_0)
core_0 as first optional question. is_optional_question check skips follow-up. build_prompt() conditional identity section.
Status: `done`

### T31: Upload de foto do agente
Out of scope — avatar moved to platform (Directus).
Status: `out_of_scope`

### T32: Remover avatar + reestruturar perguntas core (16→10)
Removed avatar (endpoints, ORM, schema, tests, uploads dir). Redesigned core questions from 16 to 10 (2 text optional, 2 text required, 3 select, 3 multiselect). Updated ENRICHMENT_PREFILL_MAP (core_1, core_3, core_4). Updated DYNAMIC_QUESTION_BANK (7→4 categories). Rewrote build_prompt() (9→7 sections). Financial details (juros, multa, parcelamento) moved to separate spreadsheet.
Status: `done`

---

## M5.8: Enriquecimento Avancado — Pesquisa Web (T33) — DONE

### T33: Pesquisa web sobre a empresa no enrichment
Serper API → 3 parallel queries (empresa geral, produtos/clientes, setor+cobrança) → deduplicate by URL → GPT-4.1-mini consolidation → WebResearchResult stored as `enrichment_data["web_research"]`. New files: services/web_research.py, prompts/web_research.py, tests/test_web_research.py. Graceful skip if no SEARCH_API_KEY.
Status: `done`

---

## M5.9: Simplificar Entrevista + SOP Report (T34, T34.1) — DONE

### T34: Simplificar entrevista (10→7 perguntas, remover dinâmicas)
Core questions 10→7, removed dynamic questions entirely, added deterministic follow-ups for policy questions, hardcoded defaults for tone/guardrails/escalation.
Status: `done`

### T34.1: Substituir AgentConfig por OnboardingReport (SOP)
Replaced AgentConfig with OnboardingReport (9 sub-models). system_prompt → expert_recommendations, scenario_responses → collection_profile. ORM column `agent_config` kept (no migration).
Status: `done`

---

## M6: Deploy + Security Hardening (T35-T37) — DONE

### T35: CORS configuration
CORSMiddleware with ALLOWED_ORIGINS env var. Default: localhost:3000,localhost:5173,localhost:8080,portal.financecrew.ai.
Status: `done`

### T36: Dockerfile + Railway config
Python 3.13-slim, Playwright deps, uv multi-stage copy, --frozen --no-dev, layer caching. .dockerignore.
Status: `done`

### T36.1: API Authentication — X-API-Key
APIKeyHeader + secrets.compare_digest in dependencies.py. Applied to all routers via main.py. /health stays public.
Status: `done`

### T36.2: SSRF Protection on URL Scraping
Two-layer validation: validate_url_scheme() (no DNS) + validate_url() (with DNS). Pydantic field_validator on CreateSessionRequest.website.
Status: `done`

### T36.3: Rate Limiting on Expensive Endpoints
slowapi: Heavy 5/min (enrich, generate, simulate, transcribe), Medium 20/min (answer), Light 60/min (reads). /health exempt.
Status: `done`

### T36.4: Dockerfile Security Hardening
Pinned uv 0.6.3, non-root appuser, PLAYWRIGHT_BROWSERS_PATH with chown.
Status: `done`

### T36.5: Production API Hardening
ENVIRONMENT setting, conditional /docs, restricted CORS methods/headers, generic 500 errors, chunked audio upload (25MB limit).
Status: `done`

### T36.7: Filtrar campos sensíveis no GET /sessions/{id}
SessionPublicResponse excludes enrichment_data and interview_state. Regression test added.
Status: `done`

### T37: Deploy to Railway + verify
Dockerfile CMD with ${PORT:-8000}, railway.toml, deployed at onboarding-financecrewai-production.up.railway.app.
Status: `done`
