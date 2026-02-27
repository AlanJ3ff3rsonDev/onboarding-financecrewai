# CLAUDE.md — Frontend Coding Agent Instructions

## Project Overview

CollectAI self-service onboarding frontend: 6 screens that guide a client through company enrichment, a structured interview, report generation, and conversation simulation.

**Platform repo**: `financecrew/crew-ai-dashboard` (cloned at `../../crew-ai-dashboard/`)
**Stack**: React 18 + TypeScript + Vite 5 + Tailwind CSS + shadcn/ui
**Backend API**: FastAPI at `https://onboarding-financecrewai-production.up.railway.app/api/v1`
**Branch**: `feat/onboarding` (Lovable deploys from `main` — do NOT merge until fully tested)

## Key Files

| File | Purpose |
|------|---------|
| `docs/SUMMARY.md` | **Read FIRST** — project state, architecture summary, section index |
| `docs/PRD.md` | Screen definitions, UX requirements, platform architecture |
| `docs/tech_design.md` | **Most important** — API endpoints, JSON schemas, interview flow, audio, platform integration |
| `docs/tasks.md` | Task details — pending tasks with full definitions |
| `docs/progress.md` | Development log — last 2-3 tasks only |
| `../../docs/PRD_ONBOARDING_MACRO.md` | Macro vision — 3 phases of onboarding (Interview, WhatsApp, Payment) |

## Workflow

Every session, follow this exact order:

1. **Read `docs/SUMMARY.md` FIRST** — project state, what's next, architecture overview
2. **Read the next pending task** in `docs/tasks.md`
3. **Read specific sections** of `tech_design.md` or `PRD.md` via the section index in SUMMARY.md
4. **Implement** in the platform repo (`crew-ai-dashboard/`, branch `feat/onboarding`)
5. **Test** — verify against real backend API (not mocked)
6. **Log result** in `docs/progress.md`
7. **Mark `done`** in tasks.md

## Rules

### Follow the API Contract
`docs/tech_design.md` has the complete API reference. Use the exact field names and types. Swagger UI at `https://onboarding-financecrewai-production.up.railway.app/docs` (dev only).

### Follow the Platform Patterns
- Use existing shadcn/ui components from `src/components/ui/`
- Use `@/` path alias for imports
- Use `cn()` utility from `@/lib/utils` for conditional classes
- Use `useTranslation()` from `react-i18next` for all UI text
- Use existing design tokens from `src/index.css` (HSL variables)
- Use existing animations: `fade-in`, `fade-in-up`, `slide-in-right`, `scale-in`

### Language
- All code in English
- All UI text in Portuguese (PT-BR) via i18n translation keys

### Dev Approach
- All code lives in `src/features/onboarding/` (or `src/pages/onboarding/` if repo uses flat structure)
- Onboarding API client is SEPARATE from Directus (different backend, different auth)
- Feature flag `"onboarding"` in FeatureFlagContext controls visibility
- `hideLayout` pattern in App.tsx hides sidebar/header for onboarding routes

### One Task at a Time
Complete fully before starting the next. Never leave a task half-done without logging what happened.

### Log Everything
Every task gets a progress.md entry — even failures.
