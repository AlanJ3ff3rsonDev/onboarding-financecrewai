# Tasks Archive (M0-M5.6) — Completed

Archived from `tasks.md` on 2026-02-23. Full task definitions for all completed milestones.
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
