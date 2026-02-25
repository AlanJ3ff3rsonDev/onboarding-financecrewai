# Tasks: Self-Service Onboarding

## How to Use This File

- Do one task at a time. Complete it, test it, log in `progress.md`, then move to the next.
- Status: `pending` → `in_progress` → `done`

> **Archive**: Detailed definitions for completed tasks (T01-T33) are in `docs/tasks_archive.md`.

---

## Milestone Overview

| Milestone | Description | Tasks | Status |
|-----------|-------------|-------|--------|
| **M0** | Project Setup | T01-T04 | DONE |
| **M1** | Enrichment | T05-T07 | DONE |
| **M2** | Interview (Wizard) | T08-T17 | DONE |
| **M3** | Agent Generation | T18-T22 | DONE |
| **M4** | Simulation | T23-T24 | DONE |
| **M5** | Integration Test | T25 | DONE |
| **M5.5** | Refatoracao Perguntas | T26-T28 | DONE |
| **M5.6** | Refinamento de Perguntas | T29 | DONE |
| **M5.7** | Personalizacao do Agente + Reestruturacao Perguntas | T30-T32 | DONE |
| **M5.8** | Enriquecimento Avancado (Pesquisa Web) | T33 | DONE |
| **M5.9** | Simplificar Entrevista + SOP Report | T34, T34.1 | DONE |
| **M6** | Deploy | T35-T37 | Pending |
| **M7** | Frontend Onboarding (Lovable) | T38-T44 | Moved to `frontend/docs/tasks.md` |
| **M8** | Integracao Directus | T45 | Moved to `frontend/docs/tasks.md` |

---

## Completed Tasks (Summary)

| ID | Task | Milestone | Status |
|----|------|-----------|--------|
| T01 | Initialize project structure | M0 | `done` |
| T02 | FastAPI app with health endpoint | M0 | `done` |
| T03 | Database setup + session model | M0 | `done` |
| T04 | Session API endpoints | M0 | `done` |
| T05 | Website scraping service | M1 | `done` |
| T06 | LLM extraction service | M1 | `done` |
| T07 | Enrichment API endpoint | M1 | `done` |
| T08 | Core questions data structure | M2 | `done` |
| T09 | LangGraph interview state + basic graph | M2 | `done` |
| T10 | Interview "next question" endpoint | M2 | `done` |
| T11 | Interview "submit answer" endpoint | M2 | `done` |
| T12 | AI follow-up evaluation + generation | M2 | `done` |
| T13 | Dynamic question generation | M2 | `done` |
| T14 | Interview progress endpoint + completion | M2 | `done` |
| T15 | Smart defaults confirmation endpoint | M2 | `done` |
| T16 | Audio transcription service | M2 | `done` |
| T17 | Audio upload endpoint | M2 | `done` |
| T18 | AgentConfig Pydantic schema | M3 | `done` |
| T19 | Agent generation prompt | M3 | `done` |
| T20 | Agent generation service + sanity checks | M3 | `done` |
| T21 | Agent generation endpoint | M3 | `done` |
| T22 | Agent adjustment endpoint | M3 | `done` |
| T23 | Simulation prompt + service | M4 | `done` |
| T24 | Simulation endpoint | M4 | `done` |
| T25 | End-to-end integration test | M5 | `done` |
| T26 | Refatorar perguntas core + follow-up | M5.5 | `done` |
| T27 | Refatorar perguntas dinamicas | M5.5 | `done` |
| T28 | Atualizar prompt de geracao | M5.5 | `done` |
| T29 | core_3 texto aberto + core_10_open | M5.6 | `done` |
| T30 | Pergunta de nome do agente (core_0) | M5.7 | `done` |
| T31 | ~~Upload de foto do agente~~ | M5.7 | `out_of_scope` |
| T32 | Remover avatar + reestruturar perguntas core (16→10) | M5.7 | `done` |
| T33 | Pesquisa web sobre a empresa no enrichment | M5.8 | `done` |
| T34 | Simplificar entrevista (10→7, remover dinâmicas) | M5.9 | `done` |
| T34.1 | Substituir AgentConfig por OnboardingReport (SOP) | M5.9 | `done` |
| T35 | CORS configuration | M6 | `done` |
| T36 | Dockerfile + Railway config | M6 | `done` |

---

## Active & Pending Tasks

### T35: CORS configuration (M6)

**Dependencies**: T34.1

**Definition of Done**:
- CORSMiddleware in app/main.py
- Allowed origins: portal.financecrew.ai, localhost:* (via ALLOWED_ORIGINS env var)

**Status**: `done`

---

### T36: Dockerfile + Railway config (M6)

**Dependencies**: T35

**Definition of Done**:
- Dockerfile with Python 3.13 + Playwright dependencies
- docker build + docker run work locally

**Status**: `done`

---

### T37: Deploy to Railway + verify (M6)

**Dependencies**: T36

**Definition of Done**:
- Backend accessible via public URL
- GET /health works, POST /sessions works
- OPENAI_API_KEY configured as env var

**Status**: `pending`

---

> **Frontend tasks (M7-M8)** moved to `frontend/docs/tasks.md`.
