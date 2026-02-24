# Project Summary — CollectAI Self-Service Onboarding

> **Read this FIRST every session.** Only go to the full docs when you need detail for a specific section.

## Current State

- **Completed**: M0-M5.8 (T01-T33) — 134 tests passing
- **Next task**: T34 (M5.9) — Substituir AgentConfig por Relatório SOP estruturado
- **After that**: T35-T37 (M6 Deploy), T38-T44 (M7 Frontend), T45 (M8 Directus)

## Architecture (10-line summary)

- **Stack**: FastAPI + SQLite + OpenAI GPT-4.1-mini + LangGraph + Playwright + uv
- **Flow**: Create session → Enrich (scrape + web research) → Interview (10 core + follow-ups + 3 dynamic + review) → Generate report → Simulate 2 conversations
- **Interview**: 10 core questions (2 text optional, 2 text required, 3 select, 3 multiselect), enrichment pre-fills core_1/core_3/core_4
- **Dynamic**: max 3 questions from 4 categories, no follow-ups, confidence >= 7 stops
- **Output**: OnboardingReport SOP (T34, replaces AgentConfig) — structured JSON for downstream consumption
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

| ID | Topic | Type |
|----|-------|------|
| core_0 | Agent name | text (optional) |
| core_1 | Products/services | text (pre-filled) |
| core_2 | PF/PJ/ambos | select |
| core_3 | Payment methods | multiselect (pre-filled) |
| core_4 | Tone | select (pre-filled) |
| core_5 | Collection process | text |
| core_6 | Discount policy | select |
| core_7 | Escalation triggers | multiselect |
| core_8 | Never-do list | multiselect |
| core_9 | Business-specific info | text (optional) |
