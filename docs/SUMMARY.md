# Project Summary — CollectAI Self-Service Onboarding

> **Read this FIRST every session.** Only go to the full docs when you need detail for a specific section.

## Current State

- **Completed**: M0-M5.9 (T01-T34.1) — 122 tests passing
- **Next task**: T35 (M6) — CORS configuration
- **After that**: T36-T37 (M6 Deploy), T38-T44 (M7 Frontend), T45 (M8 Directus)

## Architecture (10-line summary)

- **Stack**: FastAPI + SQLite + OpenAI GPT-4.1-mini + LangGraph + Playwright + uv
- **Flow**: Create session → Enrich (scrape + web research) → Interview (7 core + follow-ups + review) → Generate OnboardingReport (SOP) → Simulate 2 conversations
- **Interview**: 7 core questions (1 text process + 4 select sim/não policies + 2 text optional). No dynamic questions, no enrichment pre-fill.
- **Follow-ups**: core_1 (process) → LLM-evaluated max 1; core_2-5 (policies) → deterministic on "sim"; core_0/core_6 → none
- **Defaults**: Escalation triggers, guardrails, and tone are hardcoded defaults (previously collected via core_7/core_8/core_4)
- **Web research**: Serper API → 3 parallel queries → deduplicate → GPT consolidation → `enrichment_data["web_research"]`
- **Audio**: GPT-4o-mini-transcribe, 11 formats, Portuguese
- **DB**: Single table `onboarding_sessions` with JSON columns for state
- **Frontend**: Lovable (React/TS) at `portal.financecrew.ai` — 6 screens (pending M7)
- **Deploy**: Railway/Render with Docker (pending M6)

## Section Index — Where to Find What

| Need | Read |
|------|------|
| **Next task details** | `tasks.md` → "Active & Pending Tasks" section |
| **What happened recently** | `progress.md` (last 2-3 tasks only) |
| **API endpoints** | `tech_design.md` → Section 4 |
| **JSON response schemas** | `tech_design.md` → Section 5 |
| **Service architecture** | `tech_design.md` → Section 6 |
| **Project structure / files** | `tech_design.md` → Section 2 |
| **Data model (ORM)** | `tech_design.md` → Section 3 |
| **Deploy / Docker / CORS** | `tech_design.md` → Section 7 |
| **Frontend screens / API calls** | `tech_design.md` → Section 8 |
| **Core questions table** | `PRD.md` → Section 6, FR-2 |
| **User flow** | `PRD.md` → Section 5 |
| **Product vision / success metrics** | `PRD.md` → Section 1 |
| **Non-functional requirements** | `PRD.md` → Section 7 |
| **Old task definitions (T01-T33)** | `tasks_archive.md` |
| **Old progress entries (T01-T31)** | `progress_archive.md` |

## Core Questions (quick reference)

| ID | Topic | Type | Follow-up |
|----|-------|------|-----------|
| core_0 | Agent name | text (optional) | None |
| core_1 | Collection process | text | LLM-evaluated (max 1) |
| core_2 | Juros por atraso | select sim/não | Deterministic on "sim" |
| core_3 | Desconto pagamento | select sim/não | Deterministic on "sim" |
| core_4 | Parcelamento | select sim/não | Deterministic on "sim" |
| core_5 | Multa por atraso | select sim/não | Deterministic on "sim" |
| core_6 | Escalação humano | text (optional) | None |
