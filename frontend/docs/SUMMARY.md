# Frontend Summary — Finance Crew AI Self-Service Onboarding

> **Read this FIRST every session.** Only go to the full docs when you need detail for a specific section.

## Current State

- **Backend**: M0-M6 complete. Deployed at `onboarding-financecrewai-production.up.railway.app`
- **Frontend**: In progress — building on branch `feat/onboarding` in `crew-ai-dashboard` repo
- **Completed**: T37.5 (Setup + infra), T38 (Tela de boas-vindas), T39 (Tela de enriquecimento)
- **Next task**: T40 (Tela de entrevista — wizard)

## Platform Stack (crew-ai-dashboard)

- **Stack**: React 18 + TypeScript + Vite 5 + Tailwind CSS 3 + shadcn/ui (51 components)
- **Auth**: Directus SDK (cookie sessions, auto-refresh)
- **State**: React Context (Auth, Company, FeatureFlags) + TanStack Query
- **i18n**: react-i18next (PT-BR, EN, ES)
- **Routing**: React Router DOM v6, routes in `src/App.tsx`
- **Design**: Primary color HSL(84 100% 51%) (verde-limao), dark mode, border-radius 0.75rem
- **Repo**: `financecrew/crew-ai-dashboard` (private, GitHub Sync with Lovable)

## Architecture (5-line summary)

- **6 screens**: Boas-vindas → Enriquecimento → Entrevista → Revisao → Relatorio SOP → Simulacao
- **Onboarding API**: FastAPI at `onboarding-financecrewai-production.up.railway.app/api/v1` (separate from Directus)
- **State**: Frontend only tracks `session_id` (localStorage) + component state. All answers persisted server-side.
- **Feature flag**: `onboarding` flag in FeatureFlagContext controls redirect. `hideLayout` pattern for fullscreen (no sidebar).
- **Audio**: Optional voice input via MediaRecorder API → backend transcription

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
| **Onboarding macro (3 fases)** | `../../docs/PRD_ONBOARDING_MACRO.md` |
| **Platform integration details** | `tech_design.md` → Section 7 (Platform Integration) |
| **Backend Swagger UI** | `https://onboarding-financecrewai-production.up.railway.app/docs` (dev only) |

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
