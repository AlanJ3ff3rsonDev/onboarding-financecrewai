# CLAUDE.md — Coding Agent Instructions

## Project Overview

You are building the **backend MVP** for CollectAI's self-service onboarding system. The goal: a client enters their website, answers structured questions (text or audio), and the system generates a complete, well-configured collection agent (JSON config).

**Stack**: FastAPI + SQLite + OpenAI API + LangGraph + Playwright + uv

## Key Files

| File | Purpose |
|------|---------|
| `docs/PRD.md` | Product requirements — what to build and why |
| `docs/tech_design.md` | Technical design — how to build it (architecture, data model, endpoints, services) |
| `docs/tasks.md` | Task breakdown — what to do next, in order |
| `docs/progress.md` | Development log — what was done, issues found |
| `backend/` | All source code lives here |

## Workflow

Every session, follow this exact workflow:

1. **Read `docs/progress.md` FIRST** — even if you already have a plan or know what to do. This catches recent bugs, fixes, and context from prior sessions. Always read the latest entries before writing any code.
2. **Read `docs/tasks.md`** — find the next `pending` task (follow milestone order)
3. **Read the task carefully** — understand objective, dependencies, Definition of Done
4. **Check dependencies** — make sure all prerequisite tasks are `done`
5. **Mark the task as `in_progress`** in tasks.md
6. **Implement the task** — follow `docs/tech_design.md` for architecture decisions
7. **Run automated tests** — `cd backend && uv run pytest` (or specific test file)
8. **Perform manual tests** — as described in the task
9. **Log the result** in `docs/progress.md` — what was done, test results, issues
10. **Mark the task as `done`** in tasks.md (only if ALL DoD criteria are met)
11. **Pick the next task** — repeat from step 3

## Rules

### One Task at a Time
- Complete one task fully before starting the next
- Never leave a task half-done without logging what happened

### Follow the Design
- `docs/tech_design.md` is the source of truth for architecture
- If you think the design needs changes, explain why and propose the change — don't silently deviate
- Use the exact folder structure, naming conventions, and patterns defined in the design

### Testing is Mandatory
- Every task with "Automated tests" must have passing tests before marking as `done`
- Run the full test suite after each task to catch regressions: `cd backend && uv run pytest`
- If a test fails, fix it before moving on
- **Test with real-world inputs, not just trivial/synthetic ones.** Unit tests with mocks and toy data (e.g. example.com for scraping) are not enough. Always include at least one test or manual verification that exercises the code against realistic production-like conditions (real websites, real API responses, real file formats, etc.)
- **Before declaring a task done, manually run the feature end-to-end** with a realistic input and show the output to the user for validation. Passing unit tests ≠ working code — tests are only as good as their inputs.
- **Don't approve your own work.** If a task produces visible output (scraped text, generated JSON, API responses), present the actual output for the user to validate before marking as `done`.

### Log Everything
- Every task attempt gets a progress.md entry — even if it failed
- If you encounter a bug: log it, describe it, indicate severity
- If you make a design decision: log it in the Decisions Log section

### Code Quality
- Python 3.12+, type hints on all function signatures
- Pydantic models for all request/response schemas
- Async endpoints (FastAPI async def)
- Keep functions focused and small
- No unnecessary abstractions — this is an MVP
- Comments only where logic isn't obvious
- All code in English, all agent output (prompts, questions) in Portuguese

### Error Handling
- Enrichment failures should not block the flow — return partial data, user fills gaps in interview
- LLM calls: retry once on timeout, then return error
- Audio transcription: validate file type and size before sending to API
- Always return clear error messages in API responses

### Environment
- Run locally on macOS
- Python managed by `uv`
- All commands run from the `backend/` directory
- Only external API key needed: `OPENAI_API_KEY`
- SQLite database file: `backend/onboarding.db` (auto-created)

## Common Commands

```bash
# Install dependencies
cd backend && uv sync

# Install Playwright browser
cd backend && uv run playwright install chromium

# Run the server
cd backend && uv run uvicorn app.main:app --reload --port 8000

# Run all tests
cd backend && uv run pytest

# Run specific test file
cd backend && uv run pytest tests/test_enrichment.py -v

# Check API docs
# Open http://localhost:8000/docs in browser
```

## Architecture Quick Reference

### Data Model
Single table `onboarding_sessions` — one row per onboarding session. Key JSON fields:
- `enrichment_data`: CompanyProfile from website scraping
- `interview_state`: LangGraph state (current question, answers, follow-ups)
- `agent_config`: Generated AgentConfig JSON
- `simulation_result`: Generated simulation conversations

### API Structure
- `POST /api/v1/sessions` — create session
- `POST /api/v1/sessions/{id}/enrich` — trigger enrichment
- `GET /api/v1/sessions/{id}/interview/next` — get next question
- `POST /api/v1/sessions/{id}/interview/answer` — submit answer
- `POST /api/v1/sessions/{id}/interview/complete` — finalize interview
- `POST /api/v1/sessions/{id}/audio/transcribe` — transcribe audio
- `POST /api/v1/sessions/{id}/agent/generate` — generate agent config
- `POST /api/v1/sessions/{id}/simulate` — generate simulation

### Services
Each major feature is a service in `app/services/`:
- `enrichment.py` — website scraping + LLM extraction
- `interview.py` — LangGraph interview engine
- `transcription.py` — audio → text via Whisper
- `agent_generator.py` — context engineering → AgentConfig JSON
- `simulation.py` — prompt → 2 simulated conversations

### Prompts
All LLM prompts live in `app/prompts/` as Python string constants. Keep them separate from logic.
