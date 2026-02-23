# CLAUDE.md — Coding Agent Instructions

## Project Overview

CollectAI self-service onboarding: a client enters their website, answers structured questions (text or audio), and the system generates a complete, well-configured collection agent (JSON config).

**Stack**: FastAPI + SQLite + OpenAI API + LangGraph + Playwright + uv
**Status**: Backend MVP complete (M0-M5, 120 tests). Next: Deploy (M6), Frontend via Lovable (M7).

## Key Files

| File | Purpose |
|------|---------|
| `docs/tech_design.md` | Source of truth — architecture, data model, endpoints, services |
| `docs/tasks.md` | Task breakdown — find the next `pending` task here |
| `docs/progress.md` | Development log — read this FIRST every session |
| `docs/PRD.md` | Product requirements — what to build and why |
| `backend/` | All source code |

## Commands

```bash
cd backend && uv sync                                          # Install deps
cd backend && uv run playwright install chromium               # Browser for scraping
cd backend && uv run uvicorn app.main:app --reload --port 8000 # Run server
cd backend && uv run pytest                                    # All tests
cd backend && uv run pytest tests/test_enrichment.py -v        # Specific file
cd backend && uv run pytest -m integration -v                  # Integration test (real OpenAI API)
lsof -ti :8000 | xargs kill -9 2>/dev/null                    # Free port before starting server
```

## Workflow

Every session, follow this exact order:

1. **Read `docs/progress.md` FIRST** — even if you have a plan. Catches bugs, fixes, and context from prior sessions.
2. **Read `docs/tasks.md`** — find the next `pending` task (follow milestone order)
3. **Read the task** — understand objective, dependencies, Definition of Done
4. **Check dependencies** — all prerequisite tasks must be `done`
5. **Mark `in_progress`** in tasks.md
6. **Implement** — follow `docs/tech_design.md` for architecture decisions
7. **Run task tests** then **full suite** — catch regressions
8. **Manual test** — run the feature end-to-end with realistic input, show output to user
9. **Log result** in `docs/progress.md` — what was done, test results, issues
10. **Mark `done`** in tasks.md (only if ALL DoD criteria pass)
11. **Git commit & push**

## Rules

### One Task at a Time
Complete fully before starting the next. Never leave a task half-done without logging what happened.

### Follow the Design
`docs/tech_design.md` is the source of truth. Don't silently deviate — propose changes explicitly.

### Testing
- Run full test suite after each task
- **Test with real-world inputs.** Mocks and toy data hide real bugs. Always verify with production-like conditions (real websites, real API responses, real file formats).
- **Don't approve your own work.** If a task produces visible output, present it to the user before marking `done`.

### Log Everything (but keep it minimal)
Every task gets a progress.md entry — even failures. Log bugs with severity. Log design decisions in the Decisions Log. **Keep entries short**: only what's needed to understand what was done and why when reading later. No verbose descriptions — bullet points, not paragraphs.

### Code
- Type hints on all function signatures, Pydantic models for all schemas
- All code in English, all agent output (prompts, questions) in Portuguese
- No unnecessary abstractions — this is an MVP

### Errors
- Failures should not block the flow — return partial data, user fills gaps
- LLM calls: retry once on failure, then return clear error message

## Lessons Learned

These rules were learned from real bugs across 25 tasks. Follow them.

- **Never trust LLM output.** Always validate + auto-correct against business rules. LLMs underdeliver on numeric constraints — be emphatic in prompts ("CRITICAL: minimum X") and add sanity checks.
- **Playwright: don't use `networkidle`.** Real sites never go idle (analytics, websockets). Use `domcontentloaded` + explicit short wait instead.
- **Always patch external APIs in unit tests.** If `OPENAI_API_KEY` is in env, unpatched code paths will make real API calls and break tests.
- **Validate real-world formats.** When building allowlists (file types, MIME types), check what real users produce (phone recorders, browsers), not just what the spec says.
- **Integration test assertions must be structural** — status codes, required fields, valid enums. Never assert on specific LLM-generated content.
- **Don't filter on a single field when objects share it.** Dynamically generated objects (follow-ups, dynamic questions) can inherit field values like `is_required=False` from their parent context. Always combine multiple fields (e.g., `is_required is False AND phase == "core"`) to target exactly what you mean.
- **Design web searches for the end goal, not generic info.** Reclame Aqui/reputation searches don't help configure a collection agent. Queries should target: what the company sells, who their clients are, and the collection dynamics of the sector (inadimplência, perfil devedor). Use enrichment data (e.g. segment) to make queries sector-specific.
- **Serper (serper.dev) vs SerpApi (serpapi.com) are different services.** Serper: POST, X-API-KEY header, `organic` key. SerpApi: GET, api_key param, `organic_results` key. Don't confuse them.
