# Progress Archive (T01-T31)

Archived from `progress.md`. These entries document completed work from M0-M5.7.
For current progress, see `progress.md`.

---

### 2026-02-23 — T31 (M5.7): Upload de foto do agente

**Status**: completed (later removed in T32)

**What was done**:
- `POST /api/v1/sessions/{id}/agent/avatar/upload` — multipart file upload (PNG/JPG/WebP, max 5MB)
- ORM: added `agent_avatar_path` column. Schema: added to `SessionResponse`
- Static files: mounted `/uploads` via StaticFiles

**Tests**: 130/130 passing
**Issues**: Entire feature removed in T32 (avatar moved to platform scope).

---

### 2026-02-23 — T30 (M5.7): Pergunta de nome do agente (core_0)

**Status**: completed

**What was done**:
- core_0 added as first interview question (optional text)
- `is_optional_question` check in submit_answer() — optional core questions skip follow-up
- build_prompt() conditionally includes "Identidade do Agente" section

**Tests**: 122/122 passing
**Issues**: Bug: follow-up questions also skipped by optional check. Fix: narrowed to `is_required=False AND phase=="core"`.

---

### 2026-02-22 — T29 (M5.6): core_3 texto aberto + core_10_open

**Status**: completed

**What was done**:
- core_3 converted from select to text (captures tiered overdue rules)
- core_10_open added: optional text for business-specific escalation triggers

**Tests**: 120/120 passing
**Issues**: Integration test was missing core_13/core_14 answers from M5.5 refactor. Fixed.

---

### 2026-02-22 — M5.5 (T26-T28): Refatoracao do Sistema de Perguntas

**Status**: completed

**What was done**:

**T26 — Refatorar perguntas core e sistema de follow-up**:
- core_12 reformulada: objecoes especificas do negocio
- core_13 adicionada: verificacao/comprovacao de pagamento
- core_14 adicionada: regulamentacao setorial
- FOLLOW_UP_EVALUATION_PROMPT melhorado: nao aprofunda conhecimento padrao + detecta frustracao
- Deteccao de frustracao hardcoded: lista FRUSTRATION_SIGNALS com 13 frases

**T27 — Refatorar sistema de perguntas dinamicas**:
- max_dynamic_questions: 8 -> 3
- Follow-ups desabilitados na fase dinamica
- DYNAMIC_QUESTION_BANK reescrito: 8->7 categorias
- DYNAMIC_QUESTION_PROMPT e INTERVIEW_COMPLETENESS_PROMPT reescritos

**T28 — Atualizar prompt de geracao do agente**:
- SYSTEM_PROMPT: agente e ESPECIALISTA
- build_prompt adaptado para core_13/14
- ADJUSTMENT_SYSTEM_PROMPT: mesma filosofia

**Tests**: 118/118 passing
**Issues**: None

---

### 2026-02-22 — Refactor: Financial Questions + SmartDefaults Removal

**Status**: completed

**What was done**:
- Financial questions (core_6/7/8/9): select -> text
- SmartDefaults removed entirely
- NegotiationPolicies: numeric -> text-based descriptions
- Interview phase "defaults" -> "review"
- Review endpoints added (GET/POST /interview/review)
- Agent generation: removed smart_defaults parameter, numeric sanity checks
- Guardrails: added defaults (follow_up_interval=3, max_attempts=10, identify_as_ai=True)
- All 5 test files rewritten

**Tests**: 115/115 unit tests passing. Net: 120 -> 116 total.
**Issues**: None

---

### 2026-02-20 — T25: End-to-end integration test

**Status**: completed
- Created `tests/test_integration.py` with `test_full_onboarding_flow`
- Real OpenAI API calls + real Playwright scraping
- Full pipeline: session -> enrich -> interview -> defaults -> generate -> simulate
- Execution time: ~2:35

**Tests**: 120/120 passing
**Issues**: None

---

### 2026-02-20 — Documentation Update: Frontend + Deploy Phase

**Status**: completed
- Updated PRD.md, tech_design.md, tasks.md for post-backend phases
- Created `backend/cli_test.py` for manual testing
- Added M6 (Deploy), M7 (Frontend/Lovable), M8 (Directus) tasks

---

### 2026-02-20 — Documentation Quality Review + Schema Improvements

**Status**: completed
- Added complete JSON response schemas to tech_design.md
- Added audio flow documentation
- Added complete Lovable prompts with schemas to each M7 task

---

### 2026-02-20 — T24: Simulation endpoint

**Status**: completed
- POST /simulation/generate + GET /simulation endpoints
- Status transitions: generated -> simulating -> completed
- Re-generation supported

**Tests**: 119/119 passing (114 + 5 new)
**Issues**: None

---

### 2026-02-20 — T23: Simulation prompt + service

**Status**: completed
- SimulationResult schema (5 Pydantic models)
- build_simulation_prompt() with 8 sections
- generate_simulation() with 2-attempt retry
- Sanity checks for scenario count and conversation length

**Tests**: 114/114 passing (107 + 7 new)
**Issues**: First manual test produced short conversations. Fix: strengthened prompt with "CRITICAL: minimum 10 messages".

---

### 2026-02-20 — T22: Agent adjustment endpoint

**Status**: completed
- PUT /agent/adjust with dotted-path adjustments
- LLM regenerates system_prompt and scenario_responses
- Version incrementing

**Tests**: 107/107 passing (98 + 9 new)
**Issues**: None

---

### 2026-02-20 — T21: Agent generation endpoint

**Status**: completed
- POST /agent/generate + GET /agent endpoints
- Status transitions: interviewed -> generating -> generated

**Tests**: 98/98 passing (92 + 6 new)
**Issues**: None

---

### 2026-02-20 — T20: Agent generation service + sanity checks

**Status**: completed
- generate_agent_config() with structured JSON output
- Sanity checks: system_prompt quality, discount caps, range clamping
- 2-attempt retry

**Tests**: 92/92 passing (87 + 5 new)
**Issues**: None

---

### 2026-02-20 — T19: Agent generation prompt

**Status**: completed
- SYSTEM_PROMPT + build_prompt() with 8 organized sections
- 5 helper functions for data formatting
- Graceful handling of None/empty inputs

**Tests**: 87/87 passing (84 + 3 new)
**Issues**: None

---

### 2026-02-20 — T18: AgentConfig Pydantic schema

**Status**: completed
- 8 nested Pydantic models (CompanyContext, ToneConfig, NegotiationPolicies, Guardrails, etc.)
- Validation rules for discounts, installments, system_prompt length

**Tests**: 85/85 -> 84/84 (after contact hours removal)
**Issues**: Contact hours removed from SmartDefaults/Guardrails/AgentConfig per user decision.

---

### 2026-02-20 — T17: Audio upload endpoint

**Status**: completed
- POST /audio/transcribe endpoint with multipart file upload

**Tests**: 82/82 passing
**Issues**: Bug: _create_session() helper used wrong field name. Fixed.

---

### 2026-02-20 — T16: Audio transcription service

**Status**: completed
- transcribe_audio() with gpt-4o-mini-transcribe, 11 MIME types
- 2-attempt retry

**Tests**: 78/78 passing
**Issues**: Bug: .ogg format missing from allowed types. Fixed. Limitation: duration_seconds returns 0.0.

---

### 2026-02-20 — T15: Smart defaults confirmation endpoint

**Status**: completed
- GET/POST /interview/defaults endpoints with validation

**Tests**: 71/71 passing
**Issues**: None

---

### 2026-02-20 — T14: Interview progress endpoint + completion

**Status**: completed
- GET /interview/progress with phase-aware computation

**Tests**: 63/63 passing
**Issues**: Bug: core_answered was 0 during follow-ups. Fixed with question_id prefix check.

---

### 2026-02-20 — T13: Dynamic question generation

**Status**: completed
- Dynamic question generation + completeness evaluation via LLM
- Phase transitions: core -> dynamic -> defaults

**Tests**: 58/58 passing
**Issues**: None

---

### 2026-02-19 — T12: AI follow-up evaluation + generation

**Status**: completed
- evaluate_and_maybe_follow_up() with max 2 follow-ups per question
- Text-only evaluation (select/multiselect skip)

**Tests**: 49/49 -> 51/51 passing
**Issues**: Old T11 tests broke (needed mock). "outro"/"depende" answers now trigger follow-up.

---

### 2026-02-19 — T11: Interview "submit answer" endpoint

**Status**: completed
- POST /interview/answer with question_id validation

**Tests**: 43/43 passing
**Issues**: None

---

### 2026-02-19 — T10: Interview "next question" endpoint

**Status**: completed
- GET /interview/next (idempotent, initializes on first call)

**Tests**: 35/35 passing
**Issues**: None

---

### 2026-02-19 — T09: LangGraph interview state + basic graph

**Status**: completed
- Two StateGraph instances (full + next-question)
- Enrichment pre-fill for core_1, core_2, core_5
- State serialization/deserialization

**Tests**: 31/31 passing
**Issues**: None

---

### 2026-02-19 — T08: Core questions data structure

**Status**: completed
- 12 InterviewQuestion objects + DYNAMIC_QUESTION_BANK + SMART_DEFAULTS

**Tests**: 24/24 passing
**Issues**: Expanded from 10 to 12 core questions per user feedback.

---

### 2026-02-19 — T07: Enrichment API endpoint

**Status**: completed
- POST /enrich + GET /enrichment endpoints

**Tests**: 18/18 passing
**Issues**: None

---

### 2026-02-19 — T06: LLM extraction service

**Status**: completed
- extract_company_profile() with GPT-4.1-mini structured output

**Tests**: 13/13 passing
**Issues**: None

---

### 2026-02-19 — T05: Website scraping service

**Status**: completed
- scrape_website() with Playwright headless Chromium

**Tests**: 10/10 passing
**Issues**: Bug: networkidle timeout on real sites. Fixed: switched to domcontentloaded + 3s wait.

---

### 2026-02-19 — T04: Session API endpoints

**Status**: completed
- POST /sessions + GET /sessions/{id}

**Tests**: 7/7 passing
**Issues**: None

---

### 2026-02-19 — T03: Database setup + session model

**Status**: completed
- SQLAlchemy setup + OnboardingSession ORM model

**Tests**: 3/3 passing
**Issues**: None

---

### 2026-02-19 — T02: FastAPI app with health endpoint

**Status**: completed
- GET /health endpoint

**Tests**: 1/1 passing
**Issues**: None

---

### 2026-02-19 — T01: Initialize project structure

**Status**: completed
- Project skeleton, pyproject.toml, config, Playwright

**Tests**: Manual only
**Issues**: uv was not installed. Fixed.
