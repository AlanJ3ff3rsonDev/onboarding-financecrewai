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
| 2026-02-20 | T13 uses async helper functions instead of formal LangGraph nodes for dynamic question generation and completeness evaluation | Matches T12 pattern (follow-up evaluation). Adding async nodes to synchronous LangGraph graphs would require significant refactoring. Helpers achieve identical functionality. | Task DoD says "adds nodes" but `generate_dynamic_question()` and `evaluate_interview_completeness()` serve the same purpose as nodes would. |

---

## Known Issues

Track bugs or problems that need attention but aren't blocking current work.

| # | Description | Found in | Severity | Status |
|---|-------------|----------|----------|--------|
| | | | | |

---

## Development Log

### 2026-02-20 — T15: Smart defaults confirmation endpoint

**Status**: completed

**What was done**:
- Added `GET /api/v1/sessions/{id}/interview/defaults` to `app/routers/interview.py`:
  - Returns `SMART_DEFAULTS` (pre-filled) if no confirmation yet (`confirmed: false`)
  - Returns `session.smart_defaults` if already confirmed (`confirmed: true`)
  - 400 if interview not started, 404 if session not found
- Added `POST /api/v1/sessions/{id}/interview/defaults` to `app/routers/interview.py`:
  - Accepts `SmartDefaults` as request body (Pydantic auto-validates ge/le/Literal constraints → 422 on invalid)
  - Phase gate: requires `"defaults"` or `"complete"` phase, 400 if `"core"` or `"dynamic"`
  - Custom validation for `contact_hours_weekday` and `contact_hours_saturday`: HH:MM-HH:MM format, 06:00-22:00 legal range, start < end
  - Stores confirmed defaults in `session.smart_defaults`, transitions phase to `"complete"`, sets status to `"interviewed"`
- Added `_validate_contact_hours()` helper with regex + range checks
- Added 8 tests to `tests/test_interview.py` + `_session_in_defaults_phase()` helper

**Tests**:
- [x] Automated: `test_get_defaults` — session in defaults phase → all 11 defaults with correct values (PASSED)
- [x] Automated: `test_get_defaults_not_started` — no interview_state → 400 (PASSED)
- [x] Automated: `test_confirm_defaults` — POST defaults → stored in DB, phase → "complete", GET returns confirmed=true (PASSED)
- [x] Automated: `test_adjust_defaults` — POST with modified values (interval=5, attempts=15, strategy=proactive) → stored correctly (PASSED)
- [x] Automated: `test_defaults_validation_pydantic` — negative installment, bad strategy, pct>50 → 422 (PASSED)
- [x] Automated: `test_defaults_validation_hours` — hours before 06:00, after 22:00, bad format → 400 (PASSED)
- [x] Automated: `test_confirm_defaults_wrong_phase` — POST when phase="core" → 400 (PASSED)
- [x] Automated: `test_defaults_session_not_found` — GET/POST on nonexistent session → 404 (PASSED)
- [x] Full suite: 71/71 tests passing (no regressions)
- [x] Manual: Full flow via curl on uvicorn (port 8000):
  - POST /sessions → created session
  - GET /interview/defaults before interview → 400 "Interview not started" ✓
  - GET /interview/next → initialized interview (core_1)
  - Fast-forwarded session to phase="defaults" via DB
  - GET /interview/defaults → 11 pre-filled values, confirmed=false ✓
  - POST /interview/defaults during core phase → 400 "não concluída" ✓
  - POST /interview/defaults with adjusted values (interval=5, attempts=15, strategy=proactive, hours=09:00-18:00) → confirmed=true, phase=complete ✓
  - GET /interview/defaults after confirmation → confirmed=true with saved values ✓
  - GET /sessions/{id} → status="interviewed", phase="complete", smart_defaults populated ✓
  - POST with hours < 06:00 → 400 "horário deve estar entre 06:00 e 22:00" ✓
  - POST with negative min_installment → 422 Pydantic validation ✓
  - GET/POST on nonexistent session → 404 ✓

**Issues found**:
- None

**Next steps**:
- Move to T16: Audio transcription service

---

### 2026-02-20 — T14: Interview progress endpoint + completion

**Status**: completed

**What was done**:
- Added `InterviewProgressResponse` Pydantic schema to `app/models/schemas.py` — 7 fields: phase, total_answered, core_answered, core_total, dynamic_answered, estimated_remaining, is_complete
- Added `GET /api/v1/sessions/{id}/interview/progress` to `app/routers/interview.py`:
  - Returns `phase="not_started"` with all zeros if interview not initialized
  - Computes core_answered = core_total - remaining (adjusting for current unanswered question)
  - estimated_remaining: core phase = remaining core + max_dynamic; dynamic phase = max_dynamic - asked; defaults/complete = 0
  - `is_complete=True` when phase is "defaults" or "complete"
  - Side-effect: transitions session.status to "interviewed" when is_complete is True
- Added 4 tests

**Tests**:
- [x] Automated: `test_progress_not_started` — no interview → phase="not_started", all zeros, core_total=12 (PASSED)
- [x] Automated: `test_progress_midway` — after 2 core answers → core_answered=2, estimated_remaining>0 (PASSED)
- [x] Automated: `test_progress_during_follow_up` — current=followup_core_1_1 → core_answered=1 (not 0) (PASSED)
- [x] Automated: `test_progress_defaults_phase` — phase="defaults" → is_complete=True, status="interviewed" (PASSED)
- [x] Automated: `test_progress_session_not_found` — 404 (PASSED)
- [x] Full suite: 63/63 tests passing (no regressions)
- [x] Manual: Full flow via curl with real LLM (GPT-4.1-mini):
  - Created session → answered all 12 core questions (with follow-ups on core_4, core_11, core_12)
  - 5 dynamic questions generated before LLM rated confidence >= 7 → phase="defaults"
  - Progress at each stage verified: not_started(0/12) → core midway(4/12) → core done(12/12) → dynamic(5 asked) → defaults(is_complete=true)
  - Session status correctly transitioned to "interviewed"
  - Total: 33 answers (12 core + 5 dynamic + 16 follow-ups)

**Issues found**:
- **Bug (found in manual test)**: `core_answered` was 0 when current question was a follow-up (e.g., followup_core_1_1). Cause: progress endpoint subtracted 1 from core_answered whenever `current_question` existed in core phase, but follow-up questions were also counted as "current but unanswered core question". **Fix**: only subtract 1 if `current_question.question_id` starts with "core_". Added `test_progress_during_follow_up` to cover this case.

**Next steps**:
- Move to T15: Smart defaults confirmation endpoint

---

### 2026-02-20 — T13: Dynamic question generation

**Status**: completed

**What was done**:
- Added `DYNAMIC_QUESTION_PROMPT` to `app/prompts/interview.py` — given enrichment + all answers + question bank categories, LLM generates the single most important missing question (JSON output: question_text, category, reason)
- Added `INTERVIEW_COMPLETENESS_PROMPT` to `app/prompts/interview.py` — LLM rates confidence 1-10 on having enough data for a good agent (JSON output: confidence, reason, missing_area)
- Added 4 helper functions to `app/services/interview_agent.py`:
  - `_build_enrichment_context()` — formats enrichment dict as labeled bullet list
  - `_build_question_bank_context()` — formats DYNAMIC_QUESTION_BANK as categorized text
  - `generate_dynamic_question(state)` — async, calls GPT-4.1-mini to generate next dynamic question. Returns `(InterviewQuestion, InterviewState)`. On any error/max reached → transitions to "defaults" phase
  - `evaluate_interview_completeness(state)` — async, calls GPT-4.1-mini to rate confidence. Returns `(bool, InterviewState)`. If confidence >= 7 or max reached → complete. On error → returns False (keep asking)
- Modified `get_next_question()` — when phase="dynamic", calls `generate_dynamic_question()` instead of the core question graph. Also handles transition from core to dynamic (when graph sets phase="dynamic" after exhausting core questions)
- Modified `submit_answer()` — after answering a dynamic question (and resolving follow-ups), calls `evaluate_interview_completeness()` then `generate_dynamic_question()` if not complete
- Modified GET `/interview/next` endpoint — handles dynamic phase (generates question if none exists), handles "defaults" phase message
- Modified POST `/interview/answer` response — phase-aware messages ("defaults" → specific completion message)
- Added 7 new tests (all mock OpenAI)

**Tests**:
- [x] Automated: `test_dynamic_phase_starts` — after core_12, submit_answer generates dynamic_1 (PASSED)
- [x] Automated: `test_dynamic_question_generated` — generate_dynamic_question returns valid InterviewQuestion with phase="dynamic", id="dynamic_1" (PASSED)
- [x] Automated: `test_dynamic_question_contextual` — prompt sent to LLM includes business-specific context from answers and enrichment (PASSED)
- [x] Automated: `test_max_dynamic_reached` — dynamic_questions_asked=8 → transitions to "defaults" without LLM call (PASSED)
- [x] Automated: `test_early_completion` — confidence=8 → evaluate_interview_completeness returns (True, state_with_defaults) (PASSED)
- [x] Automated: `test_low_confidence_continues` — confidence=5 → returns (False, state) unchanged (PASSED)
- [x] Automated: `test_dynamic_answer_triggers_completeness_eval` — answering dynamic question triggers completeness eval then generates next dynamic (PASSED)
- [x] Full suite: 58/58 tests passing (no regressions)
- [x] Manual: Full flow via curl with real LLM (GPT-4.1-mini):
  - Created session → answered all 12 core questions (with follow-ups)
  - 8 dynamic questions generated — all contextual: desconto negotiation, segmentation by value/time, opening messages, ticket médio, high-priority debts, "já paguei" scenario, "não posso pagar" scenario, "não reconheço" scenario
  - Follow-ups triggered on dynamic questions too (same T12 pattern, max 2 per question)
  - After dynamic_8's follow-ups resolved → phase="defaults", message="Entrevista concluída"
  - GET /interview/next in defaults phase → "Fase de perguntas concluída. Confirme os padrões."
  - Total: 44 answers (12 core + ~12 core follow-ups + 8 dynamic + ~12 dynamic follow-ups)

**Issues found**:
- None. Existing 51 tests continued passing. Dynamic phase integrates seamlessly with the T12 follow-up system.

**Next steps**:
- Move to T14: Interview progress endpoint + completion

---

### 2026-02-19 — T12: AI follow-up evaluation + generation

**Status**: completed

**What was done**:
- Added `FOLLOW_UP_EVALUATION_PROMPT` to `app/prompts/interview.py` — single LLM call evaluates answer quality AND generates follow-up (JSON output: needs_follow_up, follow_up_question, reason)
- Updated `InterviewState` in `app/services/interview_agent.py` with `follow_up_count: int` field
- Added `evaluate_and_maybe_follow_up(state, question_id, answer)` async function:
  - Skips evaluation if `follow_up_count >= 2` (MAX_FOLLOW_UPS_PER_QUESTION)
  - Skips if no `OPENAI_API_KEY` configured (graceful degradation)
  - Calls GPT-4.1-mini with formatted prompt, returns `(bool, dict | None)`
  - On any error (OpenAI, JSON parse, etc): returns `(False, None)` — never blocks the flow
- Added `_build_answers_context()` and `_get_parent_question_id()` helpers
- Modified `submit_answer()`:
  - Only evaluates text-type answers (select/multiselect skip evaluation entirely)
  - If follow-up needed: sets current_question to follow-up, increments follow_up_count
  - If no follow-up: resets follow_up_count to 0, advances to next core question
- Modified POST /answer response: includes `follow_up` field when `needs_follow_up=True`
- Updated 4 existing T11 tests to mock `evaluate_and_maybe_follow_up` (needed because real API key in env triggers actual follow-ups)
- Added 6 new T12 tests (all mock OpenAI via `unittest.mock.patch`)

**Tests**:
- [x] Automated: `test_short_answer_triggers_follow_up` — "sim" → followup_core_1_1 with phase="follow_up" (PASSED)
- [x] Automated: `test_detailed_answer_no_follow_up` — detailed text → advances to core_2 (PASSED)
- [x] Automated: `test_follow_up_answer_stored` — both original + follow-up answers in state (PASSED)
- [x] Automated: `test_max_follow_ups` — after 2 follow-ups, advances to core_2 without LLM call (PASSED)
- [x] Automated: `test_select_question_no_follow_up` — multiselect/select skip evaluation entirely (PASSED)
- [x] Automated: `test_follow_up_endpoint_response` — response has both next_question and follow_up fields (PASSED)
- [x] Full suite: 49/49 tests passing (no regressions)
- [x] Manual: Full flow via curl:
  - POST /sessions → created session
  - GET /interview/next → core_1 (text)
  - POST /answer "sim" → followup_core_1_1 ("Você pode descrever quais produtos...") with follow_up field
  - POST /answer followup_core_1_1 (detailed) → followup_core_1_2 (LLM wanted more detail on automation)
  - POST /answer followup_core_1_2 → core_2 (max follow-ups reached, advanced normally)
  - Session state: 3 answers stored, follow_up_count reset to 0, current=core_2

**Issues found**:
- **Old T11 tests broke**: Because `OPENAI_API_KEY` is in the env, `submit_answer` now triggers real follow-up evaluation. Fixed by patching `evaluate_and_maybe_follow_up` to return `(False, None)` in old tests that test answer advancement (not follow-up behavior).
- **User feedback**: Select/multiselect questions with "Outro" or "Depende" option also need follow-up evaluation, since the user is writing free text that could be vague. Added `"outro" in answer` / `"depende" in answer` check to the evaluation condition. Added 2 new tests (`test_select_outro_triggers_follow_up`, `test_multiselect_with_outro_triggers_follow_up`).
- **Full manual test (all 12 questions)**: Verified end-to-end with real LLM. 24 total answers (12 core + 12 follow-ups). "outro"/"depende" correctly triggered evaluation. Standard select options correctly skipped. Max 2 follow-ups respected. Phase transitioned to "dynamic" after core_12. 51/51 automated tests passing.

**Next steps**:
- Move to T13: Dynamic question generation

---

### 2026-02-19 — T11: Interview "submit answer" endpoint

**Status**: completed

**What was done**:
- Added `SubmitAnswerRequest` Pydantic schema to `app/models/schemas.py` (question_id, answer, source)
- Added `submit_answer(state, question_id, answer, source)` to `app/services/interview_agent.py`
  - Validates question_id matches current_question (raises ValueError on mismatch)
  - Appends answer to state's `answers` list (with question_text for context)
  - Advances to next question via `get_next_question()`
- Added `POST /api/v1/sessions/{id}/interview/answer` to `app/routers/interview.py`
  - Stores answer in both `interview_state.answers` and `interview_responses` (clean list for agent generation)
  - Returns `{ received: true, next_question: InterviewQuestion }` or phase info when core questions exhausted
  - 400 on question_id mismatch, interview not started, or interview already complete
  - 404 on session not found
- Added 7 new tests (2 service-level, 5 endpoint-level)

**Tests**:
- [x] Automated: `test_submit_answer_service` — stores answer, advances to core_2 (PASSED)
- [x] Automated: `test_submit_answer_wrong_question_id` — ValueError on mismatch (PASSED)
- [x] Automated: `test_submit_answer_endpoint` — POST answer → next question returned (PASSED)
- [x] Automated: `test_submit_answer_chain` — 3 answers in sequence → each returns correct next (PASSED)
- [x] Automated: `test_answer_stored_in_session` — answer in both interview_responses and interview_state (PASSED)
- [x] Automated: `test_wrong_question_id_endpoint` — 400 on mismatch (PASSED)
- [x] Automated: `test_submit_answer_session_not_found` — 404 (PASSED)
- [x] Automated: `test_submit_answer_interview_not_started` — 400 (PASSED)
- [x] Full suite: 43/43 tests passing (no regressions)
- [x] Manual: Started server → full flow via curl:
  - POST /sessions → created session for "CollectAI"
  - GET /interview/next → core_1 returned, status → "interviewing"
  - POST /interview/answer core_1 → received=true, next=core_2 (multiselect with payment options)
  - POST /interview/answer core_2 → next=core_3
  - POST /interview/answer core_3 → next=core_4
  - GET /sessions/{id} → 3 answers in interview_responses AND interview_state.answers, current=core_4, remaining=8
  - POST answer with wrong question_id → 400 "expected 'core_4', got 'core_10'"
  - POST answer for nonexistent session → 404
  - GET /interview/next (idempotent) → still returns core_4 without advancing

**Issues found**:
- None

**Next steps**:
- Move to T12: AI follow-up evaluation + generation

---

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
