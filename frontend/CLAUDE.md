# CLAUDE.md — Frontend Coding Agent Instructions

## Project Overview

CollectAI self-service onboarding frontend: 6 screens that guide a client through company enrichment, a structured interview, report generation, and conversation simulation.

**Stack**: Lovable / React / TypeScript
**Backend API**: FastAPI at `{BACKEND_URL}/api/v1` — Swagger UI at `{BACKEND_URL}/docs`
**Status**: Pending — depends on backend deploy (T37)

## Key Files

| File | Purpose |
|------|---------|
| `docs/SUMMARY.md` | **Read FIRST** — project state, architecture summary, section index |
| `docs/PRD.md` | Screen definitions, UX requirements, platform architecture |
| `docs/tech_design.md` | **Most important** — all API endpoints, JSON schemas, interview flow, audio, state management |
| `docs/tasks.md` | Task details — pending tasks with full definitions |
| `docs/progress.md` | Development log — last 2-3 tasks only |

## Workflow

Every session, follow this exact order:

1. **Read `docs/SUMMARY.md` FIRST** — project state, what's next, architecture overview
2. **Read the next pending task** in `docs/tasks.md`
3. **Read specific sections** of `tech_design.md` or `PRD.md` via the section index in SUMMARY.md
4. **Implement** — follow `docs/tech_design.md` for API contracts
5. **Test** — verify against real backend API (not mocked)
6. **Log result** in `docs/progress.md`
7. **Mark `done`** in tasks.md

## Rules

### Follow the API Contract
`docs/tech_design.md` has the complete API reference. Use the exact field names and types. When in doubt, check `{BACKEND_URL}/docs` (Swagger UI).

### Language
- All code in English
- All UI text in Portuguese (PT-BR)

### Dev Approach
- UI screens built in Lovable
- Backend integration via Claude Code (branch separada)
- Details TBD after backend deploy (T37)

### One Task at a Time
Complete fully before starting the next. Never leave a task half-done without logging what happened.

### Log Everything
Every task gets a progress.md entry — even failures.
