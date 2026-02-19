# Progress Log: Self-Service Onboarding Backend MVP

## How to Use This File

This file tracks all development progress across sessions. Every time you work on a task, log it here.

### Entry Format

```
### [DATE] — [TASK_ID]: [TASK_TITLE]

**Status**: completed | in_progress | blocked
**Time spent**: approximate

**What was done**:
- Bullet points describing what was implemented

**Tests**:
- [ ] Automated: describe test results
- [ ] Manual: describe manual verification

**Issues found**:
- Any bugs, edge cases, or surprises (or "None")
- **If a test fails / bug is found**: describe the bug, what caused it, and how it was fixed BEFORE moving to the next task
- Never skip logging a bug — even if fixed immediately

**Next steps**:
- What to do next (or "Move to [TASK_ID]")
```

### Workflow per Task

1. Mark task as `in_progress` in tasks.md
2. Implement the task
3. Run tests **for that specific task** (`uv run pytest tests/test_<file>.py -v`)
4. If tests fail → fix the bug → **log the bug in this entry** → re-run tests
5. Run **full test suite** (`uv run pytest tests/ -v`) to check for regressions
6. Log the result in this file (progress.md)
7. Only mark as `done` if ALL tests pass (task-specific + full suite)
8. After completing a milestone, run full suite one more time as final validation

---

## Decisions Log

Track important decisions made during development that deviate from or clarify the design docs.

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| 2026-02-19 | Expanded core questions from 10 to 12: added juros (core_8) and multa (core_9) | User feedback: not all businesses charge interest/fines — need explicit "none" option | All task refs updated (T09, T25). core_6 changed from slider to select. IDs renumbered: old 8/9/10 → 10/11/12 |

---

## Known Issues

Track bugs or problems that need attention but aren't blocking current work.

| # | Description | Found in | Severity | Status |
|---|-------------|----------|----------|--------|
| | | | | |

---

## Development Log

### 2026-02-19 — T10: Interview "next question" endpoint

**Status**: completed

**What was done**:
- Created `app/routers/interview.py` with `GET /api/v1/sessions/{id}/interview/next` endpoint
  - If `interview_state` is None (first call): initializes via `create_interview()`, stores state in DB, updates status to `"interviewing"`
  - If interview_state exists: deserializes and returns `current_question`
  - If `phase == "complete"`: returns completion message
  - Idempotent GET — does not advance questions; advancement happens on answer submission (T11)
- Registered interview router in `app/main.py`
- Added 4 route-level tests to `tests/test_interview.py`

**Tests**:
- [x] Automated: `test_get_first_question_endpoint` — new session → GET next → core_1 returned, status = "interviewing" (PASSED)
- [x] Automated: `test_get_next_after_enrichment_endpoint` — enriched session → core_1 has pre_filled_value from enrichment (PASSED)
- [x] Automated: `test_interview_state_persisted` — state stored in DB, repeated GET returns same question (PASSED)
- [x] Automated: `test_interview_next_session_not_found` — 404 on nonexistent session (PASSED)
- [x] Full suite: 35/35 tests passing (no regressions)

**Issues found**:
- None

**Next steps**:
- Manual verification with Swagger, then move to T11: Interview "submit answer" endpoint

---

### 2026-02-19 — T09: LangGraph interview state + basic graph

**Status**: completed

**What was done**:
- Implemented `app/services/interview_agent.py` with:
  - `InterviewState` TypedDict — 9 fields matching tech_design.md spec
  - Two LangGraph `StateGraph` instances: full graph (initialize + select + present) for `create_interview()`, and next-question graph (select + present) for `get_next_question()`
  - 3 graph nodes: `initialize` (loads 12 core questions), `select_next_core_question` (pops next, applies enrichment pre-fill), `present_question` (no-op passthrough)
  - Conditional routing: `route_after_select` sends to `present_question` if a question was selected, otherwise `END`
  - Enrichment pre-fill for 3 questions: core_1 (products), core_2 (payment methods), core_5 (tone)
  - `serialize_state()` / `deserialize_state()` for JSON round-trip to DB
  - `create_interview(enrichment_data)` — returns state with core_1 as current question
  - `get_next_question(state)` — advances to next core question, returns `(InterviewQuestion, state)`
- Added 7 tests to `tests/test_interview.py` (existing 6 T08 tests untouched)

**Tests**:
- [x] Automated: `test_create_interview` — 11 remaining + core_1 current = 12 total (PASSED)
- [x] Automated: `test_get_first_question` — core_1 returned as valid InterviewQuestion (PASSED)
- [x] Automated: `test_state_serialization` — JSON round-trip preserves all fields (PASSED)
- [x] Automated: `test_pre_fill_from_enrichment` — core_1 gets pre_filled_value from products_description (PASSED)
- [x] Automated: `test_get_next_question_advances` — advances to core_2, 10 remaining (PASSED)
- [x] Automated: `test_no_enrichment_no_prefill` — no enrichment = no pre_filled_value (PASSED)
- [x] Automated: `test_enrichment_prefill_core_5_tone` — tone pre-fills core_5 after advancing (PASSED)
- [x] Full suite: 31/31 tests passing (no regressions)

**Issues found**:
- None

**Next steps**:
- Move to T10: Interview "next question" endpoint

---

### 2026-02-19 — T08: Core questions data structure

**Status**: completed

**What was done**:
- Added 4 Pydantic schemas to `app/models/schemas.py`: `QuestionOption`, `SliderOptions`, `InterviewQuestion`, `SmartDefaults`
- Implemented `app/prompts/interview.py` with:
  - `CORE_QUESTIONS`: 12 `InterviewQuestion` objects (Portuguese text, correct types, all select-based)
  - `DYNAMIC_QUESTION_BANK`: 8 categories with 2-3 example questions each (Portuguese)
  - `SMART_DEFAULTS`: Pre-filled `SmartDefaults` instance with all 11 PRD values
- Created `tests/test_interview.py` with 6 tests

**Design change (user feedback)**: Expanded from 10 to 12 core questions. Added core_8 (juros por atraso) and core_9 (multa por atraso) as new questions. Changed core_6 (desconto) from slider to select. All 4 financial questions (desconto, parcelas, juros, multa) now have explicit "Não oferecemos/cobramos" option for businesses that don't use them.

**Tests**:
- [x] Automated: `test_core_questions_count` — exactly 12 questions (PASSED)
- [x] Automated: `test_core_questions_schema` — all match InterviewQuestion, IDs core_1..core_12 (PASSED)
- [x] Automated: `test_core_questions_unique_ids` — no duplicates (PASSED)
- [x] Automated: `test_financial_questions_have_none_option` — core_6/7/8/9 all have "nenhum" option (PASSED)
- [x] Automated: `test_smart_defaults_complete` — all 11 defaults present with correct values (PASSED)
- [x] Automated: `test_dynamic_question_bank_categories` — all 8 categories present (PASSED)
- [x] Full suite: 24/24 tests passing (no regressions)

**Issues found**:
- **User feedback**: Original design had only 10 questions and assumed all businesses charge interest, fines, offer discounts, and installments. Fixed by adding explicit "none" options and 2 new questions (juros/multa).

**Next steps**:
- Move to T09: LangGraph interview state + basic graph

---

### 2026-02-19 — T07: Enrichment API endpoint

**Status**: completed

**What was done**:
- Implemented `app/routers/enrichment.py` with two endpoints:
  - `POST /api/v1/sessions/{id}/enrich` — triggers scraping + LLM extraction, stores result, status transitions created → enriching → enriched. Returns 404 (not found), 409 (already enriched).
  - `GET /api/v1/sessions/{id}/enrichment` — returns stored CompanyProfile. Returns 404 if not found or not enriched.
- Registered enrichment router in `app/main.py`
- Added 5 endpoint tests to `tests/test_enrichment.py` (mocked scraping/LLM for unit tests)

**Tests**:
- [x] Automated: `test_enrich_session` — create → enrich → GET enrichment returns CompanyProfile (PASSED)
- [x] Automated: `test_enrich_not_found` — non-existent session → 404 (PASSED)
- [x] Automated: `test_enrich_already_done` — enrich twice → 409 (PASSED)
- [x] Automated: `test_get_enrichment_not_enriched` — GET before enriching → 404 (PASSED)
- [x] Automated: `test_get_enrichment_session_not_found` — GET non-existent → 404 (PASSED)
- [x] Full suite: 18/18 tests passing (no regressions)
- [x] Manual: Created session for collectai.com.br → POST enrich → real scraping + GPT-4.1-mini extraction → all 7 CompanyProfile fields populated with accurate Portuguese data. GET enrichment returned same data. 409 on duplicate enrich, 404 on bad session ID — all correct.

**Issues found**:
- None

**Next steps**:
- M1 complete. Move to M2: T08 (Core questions data structure)

---

### 2026-02-19 — T06: LLM extraction service

**Status**: completed

**What was done**:
- Added `CompanyProfile` Pydantic schema to `app/models/schemas.py` — 7 fields (company_name required, rest default to `""`)
- Created `app/prompts/enrichment.py` with `SYSTEM_PROMPT` and `build_prompt()` — instructs GPT-4.1-mini to extract structured company data from raw website text
- Added `extract_company_profile(company_name, website_text) -> CompanyProfile` to `app/services/enrichment.py`
  - Returns minimal profile if text is empty (no LLM call)
  - Uses `response_format={"type": "json_object"}` for structured output
  - Retries once on OpenAI/JSON errors, then falls back to minimal profile
  - Uses `OPENAI_API_KEY` from environment via `app.config.settings`

**Tests**:
- [x] Automated: `test_extract_profile_empty_content` — empty text returns minimal profile without LLM call (PASSED)
- [x] Automated: `test_extract_profile_with_content` — mocked OpenAI returns populated CompanyProfile (PASSED)
- [x] Automated: `test_profile_schema_validation` — Pydantic validates correct data, rejects missing company_name (PASSED)
- [x] Full suite: 13/13 tests passing (no regressions)
- [x] Manual: scraped collectai.com.br (6,582 chars) → extracted CompanyProfile with real GPT-4.1-mini call — all fields populated with accurate, Portuguese-language data. Output validated by user.

**Issues found**:
- None. The `OPENAI_API_KEY` was already set in the shell environment (not in `.env`), so `pydantic-settings` picked it up automatically.

**Next steps**:
- Move to T07: Enrichment API endpoint

---

### 2026-02-19 — T05: Website scraping service

**Status**: completed

**What was done**:
- Implemented `app/services/enrichment.py` with `scrape_website(url: str) -> str`
- Uses Playwright headless Chromium with `networkidle` wait strategy
- Auto-prepends `https://` if URL has no scheme
- Truncates text to 15,000 chars (sufficient for LLM extraction, avoids token waste)
- All errors return empty string gracefully (PlaywrightError, TimeoutError, etc.)
- 30s navigation timeout

**Tests**:
- [x] Automated: `test_scrape_real_website` — scrapes example.com, verifies "Example Domain" in text (PASSED)
- [x] Automated: `test_scrape_invalid_url` — invalid URL returns empty string (PASSED)
- [x] Automated: `test_scrape_timeout` — mocked timeout returns empty string (PASSED)
- [x] Full suite: 10/10 tests passing (no regressions)

**Issues found**:
- **Bug**: `networkidle` wait strategy caused 30s timeout on real sites (e.g. collectai.com.br) due to persistent connections (analytics, Webflow). **Fixed**: switched to `domcontentloaded` + 3s wait for JS rendering. Confirmed working on collectai.com.br (6,582 chars extracted).

**Next steps**:
- Move to T06: LLM extraction service

---

### 2026-02-19 — T04: Session API endpoints

**Status**: completed

**What was done**:
- Implemented `app/models/schemas.py` with `CreateSessionRequest`, `SessionResponse`, and `CreateSessionResponse` Pydantic schemas
- Implemented `app/routers/sessions.py` with `POST /api/v1/sessions` (201) and `GET /api/v1/sessions/{id}` (200/404)
- Registered sessions router in `app/main.py`
- Proper error handling: 404 for not found, 422 for invalid input

**Tests**:
- [x] Automated: `test_create_session_api` — POST returns 201 + session_id (PASSED)
- [x] Automated: `test_get_session_api` — GET returns full session data (PASSED)
- [x] Automated: `test_get_session_not_found` — GET with bad ID returns 404 (PASSED)
- [x] Automated: `test_create_session_missing_fields` — POST without company_name returns 422 (PASSED)
- [x] Automated: All 7 tests passing (no regressions)

**Issues found**:
- None

**Next steps**:
- Move to M1: T05 (Website scraping service)

---

### 2026-02-19 — T03: Database setup + session model

**Status**: completed

**What was done**:
- Implemented `app/database.py` with SQLAlchemy engine, sessionmaker, Base, and `get_db` dependency
- Implemented `app/models/orm.py` with `OnboardingSession` model — all columns from tech_design.md (id UUID, status, company_name, company_website, company_cnpj, enrichment_data JSON, interview_state JSON, interview_responses JSON, smart_defaults JSON, agent_config JSON, simulation_result JSON, created_at, updated_at)
- Updated `app/main.py` with lifespan handler to auto-create tables on startup
- Updated `tests/conftest.py` with test DB (sqlite test.db), `setup_db` autouse fixture, `db_session` fixture, and `client` fixture with DB override

**Tests**:
- [x] Automated: `test_create_session` — creates session in DB and reads it back (PASSED)
- [x] Automated: `test_session_json_fields` — stores and retrieves JSON data in enrichment_data (PASSED)
- [x] Automated: `test_health` — still passes (no regression)

**Issues found**:
- None

**Next steps**:
- Move to T04: Session API endpoints

---

### 2026-02-19 — T02: FastAPI app with health endpoint

**Status**: completed

**What was done**:
- Implemented `app/main.py` with FastAPI app and `GET /health` returning `{"status": "ok"}`
- Created `tests/conftest.py` with `client` fixture using FastAPI TestClient
- Created `tests/test_health.py` with health check test

**Tests**:
- [x] Automated: `test_health` — GET /health returns 200 with `{"status": "ok"}` (PASSED)

**Issues found**:
- None

**Next steps**:
- Move to T03: Database setup + session model

---

### 2026-02-19 — T01: Initialize project structure

**Status**: completed

**What was done**:
- Created full `backend/` directory structure matching tech_design.md Section 2
- Created `pyproject.toml` with all dependencies (fastapi, uvicorn, sqlalchemy, pydantic, pydantic-settings, openai, langgraph, playwright, httpx, python-multipart, pytest, pytest-asyncio)
- Created `.env.example` with `OPENAI_API_KEY=your-key-here`
- Implemented `app/config.py` with pydantic-settings loading from `.env`
- Created placeholder files for all modules: models/, routers/, services/, prompts/, tests/
- Installed `uv` (was not previously installed)
- Ran `uv sync` — installed 53 packages successfully (Python 3.13.3)
- Ran `uv run playwright install chromium` — downloaded Chromium v1208 + FFmpeg

**Tests**:
- [x] Manual: `uv sync` completed without errors
- [x] Manual: `uv run playwright install chromium` completed
- [x] Manual: `uv run python -c "from app.config import settings"` — config loads correctly
- [x] Manual: Verified folder structure matches tech_design.md

**Issues found**:
- `uv` was not installed on the machine — installed via official installer script
- Python 3.13.3 was used (>= 3.12 required, so OK)

**Next steps**:
- Move to T02: FastAPI app with health endpoint
