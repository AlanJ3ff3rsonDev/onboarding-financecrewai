# Frontend Summary — CollectAI Self-Service Onboarding

> **Read this FIRST every session.** Only go to the full docs when you need detail for a specific section.

## Current State

- **Backend**: M0-M5.9 complete (API ready). M6 deploy in progress (T36-T37).
- **Frontend**: Pending — depends on backend deploy (T37)
- **Stack**: Lovable (React/TypeScript) at `portal.financecrew.ai`

## Architecture (5-line summary)

- **6 screens**: Boas-vindas → Enriquecimento → Entrevista → Revisao → Relatorio SOP → Simulacao
- **Backend API**: FastAPI at `{BACKEND_URL}/api/v1` — all endpoints synchronous (no WebSocket)
- **State**: Frontend only tracks `session_id` + `current_question` + `phase` + `progress`. All answers persisted server-side.
- **Audio**: Optional voice input via MediaRecorder API → backend transcription
- **Integration**: Onboarding runs before first agent creation. Results eventually saved to Directus (M8, future).

## Section Index — Where to Find What

| Need | Read |
|------|------|
| **Next task details** | `tasks.md` → "Active & Pending Tasks" section |
| **What happened recently** | `progress.md` (last 2-3 tasks only) |
| **Screen definitions & UX requirements** | `PRD.md` → Section 2 (Screens) |
| **Platform architecture diagram** | `PRD.md` → Section 1 |
| **All API endpoints** | `tech_design.md` → Section 1 (Endpoints) |
| **JSON response schemas** | `tech_design.md` → Section 2 (Schemas) |
| **Interview flow rules** | `tech_design.md` → Section 3 (Interview Flow) |
| **Audio implementation** | `tech_design.md` → Section 4 (Audio) |
| **State management** | `tech_design.md` → Section 5 (Frontend State) |
| **Screen flow diagram** | `tech_design.md` → Section 6 (Screen Flow) |
| **Backend Swagger UI** | `{BACKEND_URL}/docs` |

## Core Questions (quick reference)

| ID | Topic | Type | Follow-up |
|----|-------|------|-----------|
| core_0 | Nome do agente | text (optional) | None |
| core_1 | Processo de cobranca | text | LLM-evaluated (max 1) |
| core_2 | Juros por atraso | select sim/nao | Deterministic on "sim" |
| core_3 | Desconto pagamento | select sim/nao | Deterministic on "sim" |
| core_4 | Parcelamento | select sim/nao | Deterministic on "sim" |
| core_5 | Multa por atraso | select sim/nao | Deterministic on "sim" |
| core_6 | Escalacao humano | text (optional) | None |
