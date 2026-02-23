# Tasks: Self-Service Onboarding Backend MVP

## How to Use This File

- Tasks are organized by **milestones** (M0-M5)
- Each task has a unique ID (T01, T02, etc.)
- **Do one task at a time**. Complete it, test it, log it in `progress.md`, then move to the next
- Tasks within a milestone are ordered — follow the order unless blocked
- Status: `pending` → `in_progress` → `done` (or `blocked`)

---

## Milestone Overview

| Milestone | Description | Tasks | Status |
|-----------|-------------|-------|--------|
| **M0** | Project Setup | T01-T04 | DONE |
| **M1** | Enrichment | T05-T07 | DONE |
| **M2** | Interview (Wizard) | T08-T17 | DONE |
| **M3** | Agent Generation | T18-T22 | DONE |
| **M4** | Simulation | T23-T24 | DONE |
| **M5** | Integration Test | T25 | DONE |
| **M5.5** | Refatoração Perguntas | T26-T28 | DONE |
| **M6** | Deploy | T29-T31 | Pending |
| **M7** | Frontend Onboarding (Lovable) | T32-T38 | Pending |
| **M8** | Integração Directus | T39 | Future |

---

## M0: Project Setup

### T01: Initialize project structure

**Objective**: Create the project skeleton with all folders, dependencies, and configuration.

**Problem it solves**: We need a working Python project before we can build anything.

**Dependencies**: None

**Definition of Done**:
- `backend/` directory exists with the folder structure from tech_design.md
- `pyproject.toml` has all dependencies listed (fastapi, uvicorn, sqlalchemy, openai, langgraph, playwright, httpx, python-multipart, pydantic-settings, pytest, pytest-asyncio)
- `.env.example` exists with `OPENAI_API_KEY=your-key-here`
- `app/config.py` loads settings from `.env` via pydantic-settings
- `uv sync` completes without errors
- `uv run playwright install chromium` completes

**Automated tests**: None yet (no code to test)

**Manual tests**:
- Run `uv sync` — should install all deps
- Verify folder structure matches tech_design.md

**Status**: `done`

---

### T02: FastAPI app with health endpoint

**Objective**: Have a running FastAPI server with a health check endpoint.

**Problem it solves**: Validates the framework is working and we can serve HTTP requests.

**Dependencies**: T01

**Definition of Done**:
- `app/main.py` creates a FastAPI app
- `GET /health` returns `{ "status": "ok" }`
- Server starts with `uv run uvicorn app.main:app --reload`
- Swagger UI accessible at `http://localhost:8000/docs`

**Automated tests**:
- `test_health`: GET /health returns 200 with `{ "status": "ok" }`

**Manual tests**:
- Open http://localhost:8000/docs — Swagger UI loads
- Click "Try it out" on /health — returns OK

**Status**: `done`

---

### T03: Database setup + session model

**Objective**: SQLite database with the `onboarding_sessions` table and basic CRUD operations.

**Problem it solves**: We need persistence to store onboarding session data across API calls.

**Dependencies**: T02

**Definition of Done**:
- `app/database.py` sets up SQLite with SQLAlchemy (async or sync)
- `app/models/orm.py` defines `OnboardingSession` model with all columns from tech_design.md (id, status, company_name, company_website, company_cnpj, enrichment_data, interview_state, interview_responses, smart_defaults, agent_config, simulation_result, created_at, updated_at)
- JSON columns use SQLAlchemy's `JSON` type
- Database file created automatically on first run (`onboarding.db`)
- Tables created on startup via `Base.metadata.create_all()`

**Automated tests**:
- `test_create_session`: Can create a session in DB and read it back
- `test_session_json_fields`: Can store and retrieve JSON data in enrichment_data column

**Manual tests**:
- Start server, check that `onboarding.db` file is created
- Use `sqlite3 onboarding.db ".tables"` to verify table exists

**Status**: `done`

---

### T04: Session API endpoints

**Objective**: API endpoints to create and retrieve onboarding sessions.

**Problem it solves**: Frontend (or Swagger) needs to create a session to start the onboarding flow.

**Dependencies**: T03

**Definition of Done**:
- `app/models/schemas.py` defines Pydantic schemas: `CreateSessionRequest` (company_name, website, cnpj optional), `SessionResponse` (id, status, all fields)
- `app/routers/sessions.py` implements:
  - `POST /api/v1/sessions` — creates session with status `created`, returns session ID
  - `GET /api/v1/sessions/{id}` — returns full session data
- Proper error handling: 404 if session not found, 422 if invalid input
- Router registered in `app/main.py`

**Automated tests**:
- `test_create_session_api`: POST /sessions with valid data returns 201 + session_id
- `test_get_session_api`: GET /sessions/{id} returns session data
- `test_get_session_not_found`: GET /sessions/{bad_id} returns 404
- `test_create_session_missing_fields`: POST without company_name returns 422

**Manual tests**:
- In Swagger UI: create a session, then retrieve it by ID
- Verify all fields are returned correctly

**Status**: `done`

---

## M1: Enrichment

### T05: Website scraping service

**Objective**: Given a URL, scrape the website content using Playwright and return clean text.

**Problem it solves**: We need raw website content to extract company information via LLM.

**Dependencies**: T01 (Playwright installed)

**Definition of Done**:
- `app/services/enrichment.py` has a function `scrape_website(url: str) -> str`
- Uses Playwright headless Chromium to load the page
- Waits for page to be fully loaded (networkidle or timeout)
- Extracts visible text content (not raw HTML)
- Handles errors gracefully: timeout (30s max), invalid URL, blocked by site
- Returns clean text or empty string on failure

**Automated tests**:
- `test_scrape_real_website`: Scrape a known public website (e.g., a simple test site), verify text is returned
- `test_scrape_invalid_url`: Invalid URL returns empty string, no crash
- `test_scrape_timeout`: Very slow site returns empty string within timeout

**Manual tests**:
- Scrape a real Brazilian company website and check the output makes sense

**Status**: `done`

---

### T06: LLM extraction service

**Objective**: Given raw website text + company name, use LLM to extract a structured CompanyProfile.

**Problem it solves**: Raw website text is unstructured. We need a clean JSON profile of the company.

**Dependencies**: T01 (OpenAI API key configured)

**Definition of Done**:
- `app/models/schemas.py` defines `CompanyProfile` Pydantic schema (company_name, segment, products_description, target_audience, communication_tone, payment_methods_mentioned, collection_relevant_context)
- `app/prompts/enrichment.py` has the extraction prompt that instructs LLM to output CompanyProfile JSON
- `app/services/enrichment.py` has a function `extract_company_profile(company_name: str, website_text: str) -> CompanyProfile`
- Uses OpenAI GPT-4.1-mini with structured output (response_format=json)
- If website_text is empty, returns a minimal profile with just the company_name
- Handles OpenAI API errors (retry once, then return minimal profile)

**Automated tests**:
- `test_extract_profile_with_content`: Given sample website text, returns valid CompanyProfile
- `test_extract_profile_empty_content`: Empty text returns minimal profile with company name
- `test_profile_schema_validation`: Output always matches Pydantic schema

**Manual tests**:
- Run extraction on real scraped content from a known company, verify quality of extracted data

**Status**: `done`

---

### T07: Enrichment API endpoint

**Objective**: API endpoint that triggers enrichment and returns results.

**Problem it solves**: Connects the scraping + extraction services to the HTTP API.

**Dependencies**: T04, T05, T06

**Definition of Done**:
- `app/routers/enrichment.py` implements:
  - `POST /api/v1/sessions/{id}/enrich` — triggers scraping + LLM extraction, stores result in session, updates status to `enriching` then `enriched`
  - `GET /api/v1/sessions/{id}/enrichment` — returns CompanyProfile from session
- Session status transitions: `created` → `enriching` → `enriched`
- Returns 404 if session not found
- Returns 409 if session already enriched (prevent duplicate runs)
- Stores CompanyProfile JSON in `enrichment_data` column

**Automated tests**:
- `test_enrich_session`: Create session → POST enrich → GET enrichment returns CompanyProfile
- `test_enrich_not_found`: POST enrich for non-existent session returns 404
- `test_enrich_already_done`: POST enrich twice returns 409

**Manual tests**:
- In Swagger: create session with a real website → trigger enrich → check results
- Verify the extracted profile makes sense for that company

**Status**: `done`

---

## M2: Interview (Wizard)

### T08: Core questions data structure

**Objective**: Define the core questions, question bank for dynamic questions, and smart defaults.

**Problem it solves**: The interview agent needs a structured set of questions to draw from.

**Dependencies**: None (data only, no services)

**Definition of Done**:
- `app/models/schemas.py` defines `InterviewQuestion` schema (question_id, question_text, question_type, options, pre_filled_value, is_required, supports_audio, phase, context_hint)
- `app/prompts/interview.py` defines:
  - `CORE_QUESTIONS`: List of 12 core questions as InterviewQuestion objects
  - `DYNAMIC_QUESTION_BANK`: Categories and example questions the AI can draw from
  - `SMART_DEFAULTS`: Default settings with their values and descriptions
- All questions have proper IDs (core_1 through core_12)
- Questions with options include all option values + "Other"

**Automated tests**:
- `test_core_questions_count`: Exactly 12 core questions defined
- `test_core_questions_schema`: All core questions match InterviewQuestion schema
- `test_smart_defaults_complete`: All defaults from PRD are present

**Manual tests**: None (data structure only)

**Status**: `done`

---

### T09: LangGraph interview state + basic graph

**Objective**: Set up the LangGraph state machine for the interview flow with core question cycling.

**Problem it solves**: We need a stateful system that tracks which questions have been asked, stores answers, and knows what to ask next.

**Dependencies**: T08

**Definition of Done**:
- `app/services/interview_agent.py` defines:
  - `InterviewState` TypedDict (enrichment_data, core_questions_remaining, current_question, answers, dynamic_questions_asked, max_dynamic_questions, phase, needs_follow_up, follow_up_question)
  - LangGraph `StateGraph` with nodes: `initialize`, `select_next_core_question`, `present_question`
  - `initialize` node: loads core questions, sets enrichment context, sets phase to "core"
  - `select_next_core_question` node: pops next question from remaining list, applies pre-fill from enrichment if applicable
  - `present_question` node: returns current question (graph pauses here for user input)
- State can be serialized to JSON and deserialized (for DB persistence)
- Function `create_interview(enrichment_data: dict) -> InterviewState` creates a fresh interview
- Function `get_next_question(state: InterviewState) -> tuple[InterviewQuestion, InterviewState]` advances the graph

**Automated tests**:
- `test_create_interview`: Creates interview with 12 core questions remaining
- `test_get_first_question`: Returns first core question
- `test_state_serialization`: State can be dumped to JSON and loaded back
- `test_pre_fill_from_enrichment`: If enrichment has product info, core_1 has pre_filled_value

**Manual tests**: None (service layer, tested via automated tests)

**Status**: `done`

---

### T10: Interview "next question" endpoint

**Objective**: API endpoint that returns the next question the user should answer.

**Problem it solves**: The frontend needs to know what to show the user next.

**Dependencies**: T04, T09

**Definition of Done**:
- `app/routers/interview.py` implements:
  - `GET /api/v1/sessions/{id}/interview/next` — loads interview state from DB, runs graph to get next question, returns InterviewQuestion
- If interview not started yet (no interview_state), initializes it (uses enrichment_data if available)
- If interview is complete, returns `{ "phase": "complete", "message": "Interview is complete" }`
- Session status updates to `interviewing` on first call

**Automated tests**:
- `test_get_first_question`: New session → GET next → returns core_1
- `test_get_next_after_enrichment`: Enriched session → GET next → core_1 has pre_filled_value from enrichment
- `test_interview_not_started`: Returns first question and initializes state

**Manual tests**:
- In Swagger: create session → (optionally enrich) → GET interview/next → see first question with options

**Status**: `done`

---

### T11: Interview "submit answer" endpoint

**Objective**: API endpoint to submit an answer to the current question and advance the interview.

**Problem it solves**: The user answered a question — we need to store it and move forward.

**Dependencies**: T10

**Definition of Done**:
- `app/models/schemas.py` defines `SubmitAnswerRequest` (question_id, answer, source: "text"|"audio")
- `app/routers/interview.py` implements:
  - `POST /api/v1/sessions/{id}/interview/answer` — stores answer in interview state, advances graph to next question
- Answer is appended to `answers` list in state AND to `interview_responses` in session (clean list)
- Response includes the next question (so frontend doesn't need a separate GET call)
- If the answered question was the last core question, phase transitions to "dynamic" (or "defaults" if no dynamic questions needed)

**Automated tests**:
- `test_submit_answer`: Submit answer to core_1 → answer stored, next question returned
- `test_submit_answer_chain`: Submit answers to core_1 through core_3 → each returns next question
- `test_answer_stored_in_session`: After submitting, answer appears in session's interview_responses
- `test_wrong_question_id`: Submit answer for wrong question_id → returns 400

**Manual tests**:
- In Swagger: cycle through a few questions submitting answers, verify the flow advances correctly

**Status**: `done`

---

### T12: AI follow-up evaluation + generation

**Objective**: After an answer is submitted, the AI evaluates whether it needs deepening and generates a follow-up question if so.

**Problem it solves**: Short or vague answers produce poor agents. The AI should ask for more detail when needed.

**Dependencies**: T11

**Definition of Done**:
- `app/prompts/interview.py` defines `FOLLOW_UP_EVALUATION_PROMPT` — given a question + answer + context, LLM decides (yes/no) if follow-up is needed and generates one if yes
- `app/services/interview_agent.py` adds nodes: `evaluate_answer`, `generate_follow_up`
  - `evaluate_answer`: Sends answer to LLM for evaluation. If follow-up needed, transitions to `generate_follow_up`
  - `generate_follow_up`: LLM generates a contextual follow-up question
- The `POST /interview/answer` response now may include a `follow_up` InterviewQuestion
- Follow-up answers are stored alongside the parent question
- Graph handles: answer → evaluate → (follow-up → answer → evaluate)* → next question

**Automated tests**:
- `test_short_answer_triggers_follow_up`: Submit "sim" to an open question → follow_up is returned
- `test_detailed_answer_no_follow_up`: Submit a detailed paragraph → no follow_up
- `test_follow_up_answer_stored`: Answer to follow-up is stored linked to parent question
- `test_max_follow_ups`: After 2 follow-ups on same question, moves to next (prevent infinite loop)

**Manual tests**:
- In Swagger: answer a question briefly → see AI follow-up. Then answer in detail → see it move to next question

**Status**: `done`

---

### T13: Dynamic question generation

**Objective**: After core questions are done, AI generates 3-8 additional questions specific to the business.

**Problem it solves**: Every business is different. The AI identifies what's still missing for a great agent and asks targeted questions.

**Dependencies**: T12

**Definition of Done**:
- `app/prompts/interview.py` defines `DYNAMIC_QUESTION_PROMPT` — given all answers so far + enrichment, LLM generates the single most important missing question
- `app/services/interview_agent.py` adds nodes: `check_core_complete`, `generate_dynamic_question`, `evaluate_interview_completeness`
  - `check_core_complete`: When all core questions answered, transition to dynamic phase
  - `generate_dynamic_question`: LLM generates next most important question based on context
  - `evaluate_interview_completeness`: LLM rates confidence 1-10. If >= 7 or max dynamic questions reached, transition to defaults phase
- Phase transitions: "core" → "dynamic" → "defaults"
- Max dynamic questions: 8 (configurable)

**Automated tests**:
- `test_dynamic_phase_starts`: After all core answered, phase becomes "dynamic"
- `test_dynamic_question_generated`: In dynamic phase, GET next returns AI-generated question
- `test_dynamic_question_contextual`: Given answers about construction, dynamic question relates to construction
- `test_max_dynamic_reached`: After 8 dynamic questions, transitions to "defaults"
- `test_early_completion`: If LLM rates confidence >= 7 after 3 dynamic questions, transitions early

**Manual tests**:
- Complete all core questions for a specific business type → see what dynamic questions the AI generates. Are they relevant? Are they different from the core questions?

**Status**: `done`

---

### T14: Interview progress endpoint + completion

**Objective**: API endpoint showing interview progress and completion status.

**Problem it solves**: Frontend needs to show a progress indicator and know when the interview is done.

**Dependencies**: T13

**Definition of Done**:
- `app/routers/interview.py` implements:
  - `GET /api/v1/sessions/{id}/interview/progress` — returns phase, questions answered, estimated remaining
- Response schema: `{ phase: str, total_answered: int, core_answered: int, core_total: int, dynamic_answered: int, estimated_remaining: int, is_complete: bool }`
- When `is_complete: true`, session status transitions to `interviewed`

**Automated tests**:
- `test_progress_initial`: New interview → core_answered=0, core_total=10
- `test_progress_midway`: After 5 answers → core_answered=5, estimated_remaining=5+
- `test_progress_complete`: After all questions + defaults → is_complete=true

**Manual tests**:
- Check progress at various points during an interview flow

**Status**: `done`

---

### T15: Smart defaults confirmation endpoint

**Objective**: API endpoint to present smart defaults and accept user confirmations/adjustments.

**Problem it solves**: Many agent settings have sensible defaults. User just reviews and tweaks.

**Dependencies**: T14

**Definition of Done**:
- `app/routers/interview.py` implements:
  - `GET /api/v1/sessions/{id}/interview/defaults` — returns current smart defaults (pre-filled)
  - `POST /api/v1/sessions/{id}/interview/defaults` — accepts user's confirmed/adjusted defaults
- `SmartDefaults` schema includes: contact_hours_weekday, contact_hours_saturday, contact_sunday, follow_up_interval_days, max_contact_attempts, use_first_name, identify_as_ai, min_installment_value, discount_strategy, payment_link_generation, max_discount_installment_pct
- Defaults are pre-filled based on PRD values (08:00-20:00, every 3 days, etc.)
- Some defaults may be adjusted based on interview answers (e.g., if user said tone is "assertive", suggest shorter follow-up interval)
- After confirmation, phase transitions to "complete", interview_state updated

**Automated tests**:
- `test_get_defaults`: Returns all default values
- `test_confirm_defaults`: POST defaults → stored in session, phase becomes "complete"
- `test_adjust_defaults`: POST with modified values → new values stored
- `test_defaults_validation`: Invalid values (hours outside 08-20, negative installment) rejected

**Manual tests**:
- In Swagger: GET defaults → see pre-filled values → POST with some adjustments → verify stored correctly

**Status**: `done`

---

### T16: Audio transcription service

**Objective**: Accept an audio file and return transcribed text using OpenAI Whisper.

**Problem it solves**: Users may prefer speaking their answers instead of typing.

**Dependencies**: T01 (OpenAI API key)

**Definition of Done**:
- `app/services/transcription.py` has a function `transcribe_audio(file_bytes: bytes, content_type: str) -> dict` returning `{ text: str, duration_seconds: float }`
- Uses OpenAI `audio.transcriptions.create` with model `gpt-4o-mini-transcribe` (cheapest)
- Language hint: "pt" (Portuguese)
- Validates file type (webm, mp4, wav, mpeg) and size (< 25MB)
- Handles API errors gracefully

**Automated tests**:
- `test_transcribe_valid_audio`: Transcribe a short test audio file → returns text (requires a test fixture audio file, or mock the OpenAI call)
- `test_transcribe_invalid_format`: Non-audio file → raises error
- `test_transcribe_too_large`: >25MB file → raises error

**Manual tests**:
- Record a short audio on your phone saying an answer in Portuguese → upload → verify transcription is accurate

**Status**: `done`

---

### T17: Audio upload endpoint

**Objective**: API endpoint to upload audio and get transcription back.

**Problem it solves**: Connects the transcription service to the HTTP API.

**Dependencies**: T04, T16

**Definition of Done**:
- `app/routers/audio.py` implements:
  - `POST /api/v1/sessions/{id}/audio/transcribe` — accepts multipart file upload, returns transcribed text
- Validates session exists (404 if not)
- Validates file type and size before sending to Whisper
- Returns `{ text: str, duration_seconds: float }`

**Automated tests**:
- `test_transcribe_endpoint`: Upload test audio → get text back
- `test_transcribe_bad_format`: Upload .txt file → 400 error
- `test_transcribe_no_file`: POST without file → 422 error

**Manual tests**:
- In Swagger: upload an audio file → see the transcription

**Status**: `done`

---

## M3: Agent Generation

### T18: AgentConfig Pydantic schema

**Objective**: Define the complete AgentConfig schema that the generator will output.

**Problem it solves**: We need a strict, validated schema for the generated agent configuration.

**Dependencies**: None (data only)

**Definition of Done**:
- `app/models/schemas.py` defines `AgentConfig` with all nested schemas:
  - `CompanyContext` (name, segment, products, target_audience)
  - `ToneConfig` (style, use_first_name, prohibited_words, preferred_words, opening_message_template)
  - `NegotiationPolicies` (max_discount_full_payment_pct, max_discount_installment_pct, max_installments, min_installment_value_brl, discount_strategy, payment_methods, can_generate_payment_link)
  - `Guardrails` (never_do, never_say, escalation_triggers, contact_hours, follow_up_interval_days, max_attempts_before_stop, must_identify_as_ai)
  - `ScenarioResponses` (already_paid, dont_recognize_debt, cant_pay_now, aggressive_debtor)
  - `AgentConfig` (agent_type, company_context, system_prompt, tone, negotiation_policies, guardrails, scenario_responses, tools, metadata)
- All fields have descriptions and examples
- Schema can be exported as JSON Schema (for LLM structured output)

**Automated tests**:
- `test_agent_config_valid`: Create a valid AgentConfig instance → no errors
- `test_agent_config_invalid_discount`: Discount > 100% → validation error
- `test_agent_config_json_schema`: Export JSON schema → valid JSON Schema

**Manual tests**: None (data structure only)

**Status**: `done`

---

### T19: Agent generation prompt

**Objective**: Create the context engineering prompt that generates a complete AgentConfig from all collected data.

**Problem it solves**: This is the core IP — turning interview data into a well-configured agent.

**Dependencies**: T18

**Definition of Done**:
- `app/prompts/agent_generator.py` defines:
  - `SYSTEM_PROMPT`: Instructions for the LLM on how to generate agent configs
  - `build_prompt(company_profile, interview_responses, smart_defaults) -> str`: Assembles all context into a structured prompt
- Prompt includes:
  - Company context section (from enrichment)
  - Business model and billing section (from interview)
  - Debtor profile section (from interview)
  - Collection process section (from interview)
  - Tone preferences section (from interview)
  - Negotiation rules section (from interview + defaults)
  - Guardrails section (from interview + defaults)
  - Scenario handling section (from interview)
- Prompt instructs LLM to generate a complete, detailed system prompt for the collection agent
- Prompt specifies the AgentConfig JSON Schema for structured output

**Automated tests**:
- `test_build_prompt`: Given sample data, prompt is built without errors
- `test_prompt_includes_all_sections`: All interview answers appear in the prompt
- `test_prompt_handles_missing_data`: Missing optional fields don't break the prompt

**Manual tests**:
- Print a generated prompt, read it, verify it would produce a good agent config

**Status**: `done`

---

### T20: Agent generation service + sanity checks

**Objective**: Service that calls LLM with the prompt and validates the output.

**Problem it solves**: Turns all the collected data into an actual agent configuration.

**Dependencies**: T19

**Definition of Done**:
- `app/services/agent_generator.py` has a function `generate_agent_config(company_profile, interview_responses, smart_defaults) -> AgentConfig`
- Calls OpenAI GPT-4.1-mini with structured output (response_format with JSON Schema)
- Parses response into AgentConfig Pydantic model
- Applies sanity checks:
  - Discount percentages <= configured max from interview
  - Contact hours within legal limits (08:00-20:00 weekdays)
  - System prompt is not empty and is at least 200 chars
  - All required fields present
- If sanity check fails: auto-correct where possible (e.g., cap discount), log the correction
- Retries once on LLM failure

**Automated tests**:
- `test_generate_agent_config`: Given complete interview data, returns valid AgentConfig
- `test_sanity_check_discount_cap`: If LLM returns discount > configured max, it's capped
- `test_sanity_check_hours`: If LLM returns hours outside 08-20, they're corrected
- `test_system_prompt_quality`: Generated system prompt is > 200 chars and mentions company name

**Manual tests**:
- Generate an agent config with real interview data → read the system_prompt → does it sound like a good collection agent for that specific business?

**Status**: `done`

---

### T21: Agent generation endpoint

**Objective**: API endpoint to trigger agent generation and retrieve the result.

**Problem it solves**: Connects the generation service to the HTTP API.

**Dependencies**: T04, T20

**Definition of Done**:
- `app/routers/agent.py` implements:
  - `POST /api/v1/sessions/{id}/agent/generate` — triggers generation, stores result in session
  - `GET /api/v1/sessions/{id}/agent` — returns stored AgentConfig
- Validates that interview is complete before allowing generation (400 if not)
- Session status transitions: `interviewed` → `generating` → `generated`
- Stores AgentConfig JSON in `agent_config` column with version metadata

**Automated tests**:
- `test_generate_agent`: Complete session → POST generate → GET agent returns AgentConfig
- `test_generate_before_interview`: POST generate on non-interviewed session → 400
- `test_get_agent_not_generated`: GET agent before generation → 404

**Manual tests**:
- Full flow in Swagger: create → enrich → interview (complete) → generate agent → inspect the JSON

**Status**: `done`

---

### T22: Agent adjustment endpoint

**Objective**: Allow user to adjust the generated agent config and re-generate parts of it.

**Problem it solves**: User sees the simulation and wants to tweak tone, discount limits, or other settings.

**Dependencies**: T21

**Definition of Done**:
- `app/routers/agent.py` implements:
  - `PUT /api/v1/sessions/{id}/agent/adjust` — accepts partial adjustments, re-generates affected parts
- Accepts adjustments like: `{ "tone.style": "empathetic", "negotiation_policies.max_discount_full_payment_pct": 20 }`
- Re-generates the system_prompt and scenario_responses to reflect the changes
- Increments version in metadata
- Stores updated config

**Automated tests**:
- `test_adjust_tone`: Change tone → system_prompt updated to reflect new tone
- `test_adjust_discount`: Change max discount → negotiation_policies updated
- `test_adjust_version_incremented`: Version goes from 1 to 2 after adjustment
- `test_adjust_before_generation`: PUT adjust on non-generated session → 400

**Manual tests**:
- Generate agent → adjust tone → re-read system_prompt → verify it changed

**Status**: `done`

---

## M4: Simulation

### T23: Simulation prompt + service

**Objective**: Given an AgentConfig, generate 2 realistic simulated collection conversations.

**Problem it solves**: The AHA Moment — user sees their agent in action before committing.

**Dependencies**: T18 (needs AgentConfig schema)

**Definition of Done**:
- `app/models/schemas.py` defines `SimulationResult` schema (scenarios list with conversation messages, outcome, metrics, metadata)
- `app/prompts/simulation.py` defines `build_simulation_prompt(agent_config: AgentConfig) -> str`
  - Instructs LLM to generate 2 conversations (cooperative + resistant debtor)
  - Each conversation: 8-15 messages
  - Agent follows the exact config (tone, discounts, guardrails)
  - Output as SimulationResult JSON
- `app/services/simulation.py` has a function `generate_simulation(agent_config: AgentConfig) -> SimulationResult`
  - Single LLM call (GPT-4.1-mini)
  - Parses response into SimulationResult
  - Validates conversations are not empty and have correct structure

**Automated tests**:
- `test_generate_simulation`: Given valid AgentConfig → returns SimulationResult with 2 scenarios
- `test_simulation_follows_config`: If config says max 10% discount, simulation discount <= 10%
- `test_simulation_conversation_length`: Each conversation has 8-15 messages
- `test_simulation_schema_valid`: Output matches SimulationResult Pydantic schema

**Manual tests**:
- Generate simulation for a real agent config → read the conversations → do they feel realistic? Does the agent follow the configured tone and rules?

**Status**: `done`

---

### T24: Simulation endpoint

**Objective**: API endpoint to trigger simulation generation and retrieve results.

**Problem it solves**: Connects the simulation service to the HTTP API.

**Dependencies**: T21, T23

**Definition of Done**:
- `app/routers/simulation.py` implements:
  - `POST /api/v1/sessions/{id}/simulation/generate` — triggers simulation, stores result
  - `GET /api/v1/sessions/{id}/simulation` — returns stored SimulationResult
- Validates that agent config exists before allowing simulation (400 if not)
- Session status transitions: `generated` → `simulating` → `completed`
- Supports re-generation (after agent adjustment): POST again overwrites previous simulation

**Automated tests**:
- `test_generate_simulation_endpoint`: Full flow → POST simulate → GET simulation returns result
- `test_simulate_before_agent`: POST simulate without agent config → 400
- `test_re_simulate`: Generate simulation twice → second one overwrites first

**Manual tests**:
- Full flow in Swagger: create → enrich → interview → generate → simulate → read conversations

**Status**: `done`

---

## M5: Integration

### T25: End-to-end integration test

**Objective**: A single test that walks through the entire onboarding flow from start to finish.

**Problem it solves**: Validates that all components work together as a complete system.

**Dependencies**: T24 (all previous tasks)

**Definition of Done**:
- `tests/test_integration.py` has a test `test_full_onboarding_flow` that:
  1. Creates a session (POST /sessions with a real company name + website)
  2. Triggers enrichment (POST /enrich)
  3. Gets enrichment results (GET /enrichment) — verifies CompanyProfile
  4. Starts interview (GET /interview/next) — gets first question
  5. Answers all core questions (POST /interview/answer × 12)
  6. Answers some dynamic questions (POST /interview/answer × 2-3)
  7. Confirms defaults (POST /interview/defaults)
  8. Generates agent config (POST /agent/generate)
  9. Verifies agent config (GET /agent) — checks system_prompt, guardrails, policies
  10. Generates simulation (POST /simulation/generate)
  11. Verifies simulation (GET /simulation) — checks 2 conversations exist
- Test uses real OpenAI API calls (not mocked) — marked as `@pytest.mark.integration`
- Separate from unit tests (run with `pytest -m integration`)
- Total execution time < 3 minutes

**Automated tests**: This IS the test

**Manual tests**:
- Walk through the entire flow manually in Swagger UI:
  1. Create a session for a real company you know
  2. Enrich it
  3. Answer all interview questions as if you were that company
  4. Generate the agent
  5. Read the system_prompt — would this work as a collection agent?
  6. Generate simulation — do the conversations feel real?
  7. **This is the ultimate validation**: if Francisco reads the agent config and simulation and says "this is good enough to use", the MVP is validated

**Status**: `done`

---

## M5.5: Refatoração do Sistema de Perguntas

### T26: Refatorar perguntas core e sistema de follow-up

**Objective**: Reformular perguntas para capturar apenas o que é específico da empresa. O agente já é especialista em cobrança.

**Dependencies**: T25

**Definition of Done**:
- core_12 reformulada: objeções específicas do negócio (não genéricas)
- core_13 adicionada: verificação/comprovação de pagamento
- core_14 adicionada: regulamentação setorial
- FOLLOW_UP_EVALUATION_PROMPT atualizado: não aprofunda conhecimento padrão + detecta frustração
- Detecção hardcoded de sinais de parada (frustração) em evaluate_and_maybe_follow_up()
- Testes atualizados (14 core questions, novos testes de frustração)

**Status**: `done`

---

### T27: Refatorar sistema de perguntas dinâmicas

**Objective**: Reduzir perguntas dinâmicas, remover follow-ups em fase dinâmica, focar em informação específica da empresa.

**Dependencies**: T26

**Definition of Done**:
- max_dynamic_questions: 8 → 3
- Follow-ups desabilitados na fase dinâmica
- DYNAMIC_QUESTION_BANK: removido scenario_handling, communication, current_pain; adicionado brand_language, payment_operations
- DYNAMIC_QUESTION_PROMPT: "NUNCA pergunte o que um agente especialista já sabe"
- INTERVIEW_COMPLETENESS_PROMPT: critérios mais generosos
- Testes atualizados (novo teste de skip de follow-up em dynamic)

**Status**: `done`

---

### T28: Atualizar prompt de geração do agente

**Objective**: Agente usa expertise própria para preencher gaps; prompt adaptado para core_13/14.

**Dependencies**: T27

**Definition of Done**:
- SYSTEM_PROMPT: agente é ESPECIALISTA, usa best practices para scenario_responses
- build_prompt: inclui core_13 (verificação de pagamento) e core_14 (regulamentação)
- ADJUSTMENT_SYSTEM_PROMPT: mesma filosofia de expertise
- Testes atualizados (fixtures com core_13/14)

**Status**: `done`

---

## M6: Deploy

### T29: Adicionar CORS no FastAPI

**Objective**: Backend aceita requests do frontend Lovable.

**Dependencies**: T28

**Definition of Done**:
- `CORSMiddleware` adicionado em `app/main.py`
- Origens permitidas: `portal.financecrew.ai`, `localhost:*` (via `ALLOWED_ORIGINS` env var)
- Teste manual: request cross-origin funciona

**Status**: `pending`

---

### T30: Criar Dockerfile + config Railway

**Objective**: Backend pode ser deployado num container com Playwright/Chromium.

**Dependencies**: T29

**Definition of Done**:
- `Dockerfile` na raiz de `backend/` com Python 3.13 + dependências Playwright
- `railway.toml` (ou equivalente) para config de deploy
- Build local funciona: `docker build -t onboarding .`
- Container roda localmente: `docker run -p 8000:8000 -e OPENAI_API_KEY=... onboarding`

**Status**: `pending`

---

### T31: Deploy no Railway + testar URL pública

**Objective**: Backend acessível via URL pública na internet.

**Dependencies**: T30

**Definition of Done**:
- Backend deployado no Railway (ou Render)
- URL pública funciona: `GET /health` retorna `{"status": "ok"}`
- `POST /sessions` funciona da URL pública
- `OPENAI_API_KEY` configurado como variável de ambiente
- Swagger UI acessível via URL pública

**Status**: `pending`

---

## M7: Frontend Onboarding (Lovable)

> Cada task abaixo inclui um **prompt para o Lovable** com objetivo, endpoints, e Definition of Done. Copie o prompt inteiro para o Lovable.

### T32: Tela de boas-vindas

**Objective**: Primeira tela do onboarding — coleta dados da empresa e cria sessão no backend.

**Dependencies**: T31

**Lovable Prompt**:
```
Crie uma tela de boas-vindas para o onboarding de cobrança.

Contexto: Esta é a primeira tela do fluxo de onboarding. O usuário acabou de
fazer login na plataforma pela primeira vez e precisa configurar seu agente
de cobrança.

Layout:
- Título: "Vamos configurar seu agente de cobrança"
- Subtítulo: "Em poucos minutos, vamos criar um agente personalizado para sua empresa"
- Campo: "Nome da empresa" (obrigatório, min 1 char)
- Campo: "Site da empresa" (obrigatório, min 1 char, placeholder: "exemplo.com.br")
- Campo: "CNPJ" (opcional, placeholder: "XX.XXX.XXX/XXXX-XX", máscara de formatação)
- Botão: "Começar" (desabilitado até nome e site preenchidos)

Validação no frontend:
- Nome: obrigatório, não pode ser vazio
- Site: obrigatório, deve parecer uma URL (com ou sem https://)
- CNPJ: opcional, se preenchido formatar com máscara XX.XXX.XXX/XXXX-XX

Ao clicar "Começar":
1. POST para {BACKEND_URL}/api/v1/sessions
   Content-Type: application/json
   Body: { "company_name": "Padaria do João", "website": "padariasjoao.com.br", "cnpj": "12.345.678/0001-99" }
   Resposta 201: { "session_id": "550e8400-e29b-41d4-a716-446655440000", "status": "created" }
   Erro 422: { "detail": [ { "msg": "...", "type": "..." } ] } — campo inválido
2. Salvar session_id no estado da aplicação (Context, Zustand, ou localStorage)
3. Navegar para a próxima tela (enriquecimento)

BACKEND_URL: configurar como variável de ambiente no Lovable.

Estilo: limpo, moderno, cards com sombra suave. Cores da marca CollectAI.
```

**Definition of Done**:
- Tela renderiza com os 3 campos
- POST para backend cria sessão com sucesso
- session_id salvo e disponível para próximas telas
- Navega para tela de enriquecimento

**Status**: `pending`

---

### T33: Tela de enriquecimento

**Objective**: Mostra loading enquanto analisa o site, depois mostra dados extraídos.

**Dependencies**: T32

**Lovable Prompt**:
```
Crie a tela de enriquecimento do onboarding.

Contexto: O usuário acabou de informar o nome e site da empresa. Agora o
backend está analisando o site com IA para extrair informações.

Fluxo:
1. Ao montar a tela, fazer POST para {BACKEND_URL}/api/v1/sessions/{session_id}/enrich
   Content-Type: application/json (sem body — o backend já tem o site da sessão)

   Resposta 200:
   {
     "status": "enriched",
     "enrichment_data": {
       "company_name": "CollectAI",
       "segment": "Fintech / SaaS de cobrança",
       "products_description": "Plataforma de cobrança automatizada via WhatsApp",
       "target_audience": "PMEs brasileiras com problemas de inadimplência",
       "communication_tone": "Profissional e empático",
       "payment_methods_mentioned": "PIX, boleto, cartão de crédito",
       "collection_relevant_context": "Foco em recuperação amigável"
     }
   }

   Erro 409: { "detail": "Session already enriched" } — já foi feito, pode seguir
   Erro 404: { "detail": "Session not found" }

2. Enquanto espera (~15 segundos):
   - Mostrar animação de loading com mensagem: "Analisando o site da sua empresa..."
   - Texto motivacional: "Estamos usando IA para entender melhor seu negócio"

3. Quando retornar:
   - Mostrar card com dados extraídos
   - Labels em português para cada campo:
     - company_name → "Empresa"
     - segment → "Segmento"
     - products_description → "Produtos/Serviços"
     - target_audience → "Público-alvo"
     - communication_tone → "Tom de comunicação"
     - payment_methods_mentioned → "Métodos de pagamento"
     - collection_relevant_context → "Contexto de cobrança"
   - Campos com valor vazio ("") não são mostrados
   - Botão: "Continuar para a entrevista"

4. Se der erro (status != 200 e != 409):
   - Mostrar mensagem: "Não conseguimos analisar o site, mas você pode continuar normalmente"
   - Botão: "Continuar mesmo assim"
   - O fluxo continua normalmente sem enriquecimento

Ao clicar "Continuar": navegar para tela de entrevista.

Estilo: cards informativos, ícones por campo (empresa, produtos, público), cores suaves.
```

**Definition of Done**:
- Loading state aparece durante a chamada
- Dados extraídos são exibidos corretamente
- Erro é tratado graciosamente (não trava)
- Navega para entrevista

**Status**: `pending`

---

### T34: Tela de entrevista — wizard de perguntas

**Objective**: Apresenta perguntas uma por uma, coleta respostas, mostra progresso. Esta é a tela mais complexa.

**Dependencies**: T33

**Lovable Prompt**:
```
Crie a tela de entrevista (wizard) do onboarding.

Contexto: O usuário vai responder perguntas sobre seu negócio de cobrança.
As perguntas vêm do backend uma por uma. Existem 3 tipos: text, select, multiselect.
Algumas respostas geram follow-ups da IA pedindo mais detalhes.
O usuário pode responder digitando texto OU gravando áudio (microfone).

## Layout

- Barra de progresso no topo (core_answered / 12 para fase core, dinâmica mostra "Pergunta adicional X")
- Indicador de fase: "Pergunta X de 12" (core) ou "Pergunta adicional" (dynamic)
- Card central com a pergunta:
  - Texto da pergunta (grande, negrito)
  - Dica de contexto (context_hint, se não null — texto menor abaixo da pergunta)
  - Se tem pre_filled_value (não null): mostrar como sugestão com "Confirmamos do seu site: [valor]"
    O campo já vem pré-preenchido, usuário pode aceitar ou editar
  - Input baseado no question_type:
    - "text": textarea multilinha + botão de microfone para gravar áudio
    - "select": lista de radio buttons com as opções (label visível, value enviado)
    - "multiselect": lista de checkboxes com as opções (labels visíveis, values enviados)
  - Se a pergunta é um follow-up (question_id começa com "followup_"):
    Destacar visualmente: "A IA quer saber mais:" antes da pergunta
- Botão "Próxima" (desabilitado até ter resposta)

## Schema: InterviewQuestion (resposta da API)

{
  "question_id": "core_1",           // ID único — "core_X", "dynamic_X", ou "followup_X_Y"
  "question_text": "O que sua empresa vende?",  // Texto da pergunta em português
  "question_type": "text",           // "text" | "select" | "multiselect"
  "options": [                       // null para "text", array para select/multiselect
    { "value": "pix", "label": "PIX" },
    { "value": "boleto", "label": "Boleto" },
    { "value": "outro", "label": "Outro" }
  ],
  "pre_filled_value": "string ou null",  // Dado extraído do site, pode pré-preencher
  "is_required": true,
  "supports_audio": true,            // Se true, mostrar botão de microfone
  "phase": "core",                   // "core" | "dynamic" | "follow_up"
  "context_hint": "string ou null"   // Dica de contexto para mostrar abaixo da pergunta
}

IMPORTANTE sobre options:
- Cada opção tem "value" (enviado ao backend) e "label" (mostrado ao usuário)
- Para select: enviar o value da opção selecionada (ex: "d5", NÃO "5 dias após")
- Para multiselect: enviar values separados por vírgula (ex: "pix,boleto,cartao_credito")
- Para text: enviar o texto digitado

## Fluxo da API

1. Ao montar: GET {BACKEND_URL}/api/v1/sessions/{session_id}/interview/next

   Se é pergunta normal, resposta = InterviewQuestion (schema acima)

   Se a entrevista já acabou:
   { "phase": "defaults", "message": "Fase de perguntas concluída. Confirme os padrões." }
   → navegar para tela de smart defaults

   Se phase == "complete":
   { "phase": "complete", "message": "Entrevista completa" }

2. Ao clicar "Próxima":
   POST {BACKEND_URL}/api/v1/sessions/{session_id}/interview/answer
   Content-Type: application/json
   Body: { "question_id": "core_1", "answer": "texto da resposta", "source": "text" }

   O campo "source" deve ser "text" para respostas digitadas ou "audio" se veio de transcrição.

   Resposta quando tem próxima pergunta:
   {
     "received": true,
     "next_question": { /* InterviewQuestion completo */ }
   }

   Resposta quando NÃO tem próxima pergunta:
   {
     "received": true,
     "next_question": null,
     "phase": "defaults",
     "message": "Entrevista concluída. Prossiga para confirmação dos padrões."
   }

3. Lógica após receber resposta do POST /answer:

   SE next_question NÃO é null:
     - Se question_id começa com "followup_": é follow-up da IA
       Mostrar com destaque visual: "A IA quer saber mais sobre sua resposta:"
     - Senão: é a próxima pergunta normal
     - Renderizar a nova pergunta

   SE next_question É null:
     - Se phase == "defaults": navegar para tela de smart defaults
     - Se phase == "dynamic": fazer GET /interview/next para buscar próxima dinâmica
       (perguntas dinâmicas são geradas uma por vez pelo backend)

4. Barra de progresso — chamar após cada resposta:
   GET {BACKEND_URL}/api/v1/sessions/{session_id}/interview/progress
   Resposta:
   {
     "phase": "core",             // "not_started" | "core" | "dynamic" | "defaults" | "complete"
     "total_answered": 5,
     "core_answered": 5,
     "core_total": 12,
     "dynamic_answered": 0,
     "estimated_remaining": 15,
     "is_complete": false
   }

## Fluxo de áudio (alternativa ao texto)

Para perguntas do tipo "text" com supports_audio == true:
1. Mostrar ícone de microfone ao lado do textarea
2. Ao clicar: iniciar gravação com MediaRecorder API do browser (formato webm)
3. Mostrar indicador visual de gravação (pulsing red dot, duração)
4. Ao parar gravação:
   - Enviar arquivo para: POST {BACKEND_URL}/api/v1/sessions/{session_id}/audio/transcribe
     Content-Type: multipart/form-data
     Campo: "file" (o blob de áudio)
   - Resposta: { "text": "transcrição em português", "duration_seconds": 12.5 }
   - Preencher o textarea com o texto transcrito
   - Usuário pode revisar/editar antes de enviar
5. Ao clicar "Próxima": enviar com source: "audio"

Estilo: wizard limpo, uma pergunta por vez, transições suaves entre perguntas.
Microfone discreto mas acessível ao lado do campo de texto.
```

**Definition of Done**:
- Perguntas aparecem uma por uma com tipo correto (text/select/multiselect)
- Respostas são enviadas e próxima pergunta aparece
- Follow-ups da IA são apresentados corretamente
- Barra de progresso atualiza
- Transição para defaults quando entrevista completa

**Status**: `pending`

---

### T35: Tela de smart defaults

**Objective**: Mostra configurações pré-preenchidas para confirmação/ajuste.

**Dependencies**: T34

**Lovable Prompt**:
```
Crie a tela de smart defaults do onboarding.

Contexto: A entrevista terminou. Agora mostramos configurações padrão que o
usuário pode aceitar ou ajustar antes de gerar o agente.

Fluxo:
1. Ao montar: GET {BACKEND_URL}/api/v1/sessions/{session_id}/interview/defaults

   Resposta:
   {
     "defaults": {
       "follow_up_interval_days": 3,
       "max_contact_attempts": 10,
       "use_first_name": true,
       "identify_as_ai": true,
       "min_installment_value": 50.0,
       "discount_strategy": "only_when_resisted",
       "payment_link_generation": true,
       "max_discount_installment_pct": 5.0
     },
     "confirmed": false
   }

   Se "confirmed": true → já foi confirmado antes, pode mostrar como read-only ou permitir re-editar.

2. Mostrar cada configuração como um item editável:

   | Campo | Label PT | Tipo de input | Validação |
   |-------|----------|---------------|-----------|
   | follow_up_interval_days | "Intervalo entre follow-ups (dias)" | input numérico | mínimo 1 |
   | max_contact_attempts | "Máximo de tentativas de contato" | input numérico | mínimo 1 |
   | use_first_name | "Usar primeiro nome do devedor" | toggle on/off | — |
   | identify_as_ai | "Identificar como IA" | toggle on/off | — |
   | min_installment_value | "Valor mínimo da parcela (R$)" | input monetário | mínimo 0 |
   | discount_strategy | "Estratégia de desconto" | select | ver opções abaixo |
   | payment_link_generation | "Gerar link de pagamento (PIX + Boleto)" | toggle on/off | — |
   | max_discount_installment_pct | "Desconto máximo para parcelamento (%)" | input percentual | 0 a 50 |

   Opções do select "discount_strategy" (value → label):
   - "only_when_resisted" → "Apenas quando o devedor resiste"
   - "proactive" → "Oferecer proativamente"
   - "escalating" → "Escalonado (aumenta com o tempo)"

   IMPORTANTE: enviar o value ("only_when_resisted"), NÃO o label.

3. Botão: "Confirmar e gerar agente"
   POST {BACKEND_URL}/api/v1/sessions/{session_id}/interview/defaults
   Content-Type: application/json
   Body (todos os 8 campos):
   {
     "follow_up_interval_days": 3,
     "max_contact_attempts": 10,
     "use_first_name": true,
     "identify_as_ai": true,
     "min_installment_value": 50.0,
     "discount_strategy": "only_when_resisted",
     "payment_link_generation": true,
     "max_discount_installment_pct": 5.0
   }

   Resposta 200: { "confirmed": true, "defaults": {...}, "phase": "complete" }
   Erro 400: { "detail": "Entrevista ainda não concluída..." } — se entrevista não terminou
   Erro 422: validação falhou (campo fora do range)

4. Navegar para tela de geração do agente.

Estilo: formulário organizado em cards, valores padrão já preenchidos,
dicas contextuais sobre cada configuração (ex: "O agente tentará cobrar
no máximo X vezes antes de parar").
```

**Definition of Done**:
- Defaults carregam e mostram corretamente
- Usuário pode editar qualquer valor
- POST salva os defaults confirmados
- Navega para geração do agente

**Status**: `pending`

---

### T36: Tela do agente gerado

**Objective**: Mostra o AgentConfig gerado — system prompt, policies, guardrails. Opção de ajustar.

**Dependencies**: T35

**Lovable Prompt**:
```
Crie a tela de visualização do agente gerado no onboarding.

Contexto: O backend vai gerar um agente de cobrança completo baseado nas
respostas da entrevista. A geração leva ~15 segundos.

Fluxo:
1. Ao montar: POST {BACKEND_URL}/api/v1/sessions/{session_id}/agent/generate
   Content-Type: application/json (sem body)

   Resposta 200:
   {
     "status": "generated",
     "agent_config": {
       "agent_type": "compliant",
       "company_context": {
         "name": "Padaria do João",
         "segment": "Alimentação",
         "products": "Pães, bolos e confeitaria",
         "target_audience": "Consumidores locais"
       },
       "system_prompt": "Você é um agente de cobrança da Padaria do João... (texto longo, >200 chars)",
       "tone": {
         "style": "friendly",         // "formal" | "friendly" | "empathetic" | "assertive"
         "use_first_name": true,
         "prohibited_words": ["ameaçar", "processar"],
         "preferred_words": ["resolver", "parceria"],
         "opening_message_template": "Olá {nome}! Aqui é a assistente da Padaria do João..."
       },
       "negotiation_policies": {
         "max_discount_full_payment_pct": 10.0,
         "max_discount_installment_pct": 5.0,
         "max_installments": 12,
         "min_installment_value_brl": 50.0,
         "discount_strategy": "only_when_resisted",
         "payment_methods": ["pix", "boleto"],
         "can_generate_payment_link": true
       },
       "guardrails": {
         "never_do": ["Ameaçar o devedor", "Revelar dados de terceiros"],
         "never_say": ["processo", "cadeia", "Serasa"],
         "escalation_triggers": ["Devedor solicita humano", "Dívida acima de R$5.000"],
         "follow_up_interval_days": 3,
         "max_attempts_before_stop": 10,
         "must_identify_as_ai": true
       },
       "scenario_responses": {
         "already_paid": "Texto descrevendo como responder quando devedor diz que já pagou",
         "dont_recognize_debt": "Texto para quando não reconhece a dívida",
         "cant_pay_now": "Texto para quando não pode pagar agora",
         "aggressive_debtor": "Texto para quando devedor é agressivo"
       },
       "tools": ["generate_payment_link", "check_payment_status"],
       "metadata": {
         "version": 1,
         "generated_at": "2026-02-20T10:30:00",
         "onboarding_session_id": "uuid",
         "generation_model": "gpt-4.1-mini"
       }
     }
   }

   Erro 400: { "detail": "Interview must be completed before generating agent config" }
   Erro 500: { "detail": "Failed to generate agent config" } — erro na LLM

2. Enquanto espera (~15s):
   - Loading: "Gerando seu agente de cobrança personalizado..."
   - Texto: "Estamos configurando tom, regras de negociação, e cenários"

3. Quando retornar, mostrar em seções colapsáveis (accordion/tabs):

   a) "Prompt do Agente" — system_prompt completo (área de texto expandível, read-only)
   b) "Tom e Comunicação" — tone.style (traduzir: friendly→"Amigável", formal→"Formal",
      empathetic→"Empático", assertive→"Assertivo"), use_first_name, prohibited_words
      como tags, preferred_words como tags, opening_message_template
   c) "Políticas de Negociação" — max_discount_full_payment_pct (%), max_installments,
      min_installment_value_brl (R$), discount_strategy (traduzir), payment_methods como tags
   d) "Guardrails" — never_do como lista, never_say como lista/tags,
      escalation_triggers como lista, follow_up_interval_days, max_attempts_before_stop
   e) "Cenários" — 4 cards: "Já pagou", "Não reconhece", "Não pode pagar", "Agressivo"
      cada um com o texto da resposta
   f) "Ferramentas" — tools como lista

4. Botão principal: "Gerar simulação" → navegar para tela de simulação
5. Botão secundário: "Ajustar agente" — abre modal com campos editáveis:
   - Tom (select: formal/friendly/empathetic/assertive)
   - Desconto máximo (input numérico)
   - Parcelas máximas (input numérico)
   Ao salvar:
   PUT {BACKEND_URL}/api/v1/sessions/{session_id}/agent/adjust
   Content-Type: application/json
   Body: { "adjustments": { "tone.style": "empathetic", "negotiation_policies.max_discount_full_payment_pct": 20 } }
   Resposta 200: { "status": "adjusted", "agent_config": { /* AgentConfig atualizado */ } }
   Atualizar a tela com o novo config.

Estilo: dashboard informativo, seções com ícones, collapsible cards.
```

**Definition of Done**:
- Loading durante geração
- AgentConfig exibido em seções organizadas
- System prompt legível e completo
- Botão navega para simulação

**Status**: `pending`

---

### T37: Tela de simulação

**Objective**: Mostra 2 conversas simuladas como chat — o "AHA Moment" do onboarding.

**Dependencies**: T36

**Lovable Prompt**:
```
Crie a tela de simulação do onboarding — esta é a tela mais impactante.

Contexto: O backend gera 2 conversas simuladas realistas entre o agente de
cobrança e devedores. Uma com devedor cooperativo, outra com resistente.
A geração leva ~20 segundos.

Fluxo:
1. Ao montar: POST {BACKEND_URL}/api/v1/sessions/{session_id}/simulation/generate
   Content-Type: application/json (sem body)

   Resposta 200:
   {
     "status": "completed",
     "simulation_result": {
       "scenarios": [
         {
           "scenario_type": "cooperative",
           "debtor_profile": "Maria, 45 anos, dona de padaria, dívida de R$1.200, 15 dias de atraso",
           "conversation": [
             { "role": "agent", "content": "Olá Maria! Aqui é a assistente da Padaria do João..." },
             { "role": "debtor", "content": "Oi, tudo bem? Eu sei que estou devendo..." },
             { "role": "agent", "content": "Entendo, Maria. Que bom que podemos resolver..." }
           ],
           "outcome": "Devedor aceitou parcelamento em 3x de R$400 via PIX",
           "metrics": {
             "negotiated_discount_pct": 0,
             "final_installments": 3,
             "payment_method": "pix",
             "resolution": "installment_plan"
           }
         },
         {
           "scenario_type": "resistant",
           "debtor_profile": "Carlos, 38 anos, empresário, dívida de R$3.500, 45 dias de atraso",
           "conversation": [
             { "role": "agent", "content": "Olá Carlos! Aqui é a assistente..." },
             { "role": "debtor", "content": "Não reconheço essa dívida!" },
             { "role": "agent", "content": "Entendo sua preocupação, Carlos..." }
           ],
           "outcome": "Devedor escalado para atendimento humano após insistir",
           "metrics": {
             "negotiated_discount_pct": null,
             "final_installments": null,
             "payment_method": null,
             "resolution": "escalated"
           }
         }
       ],
       "metadata": {}
     }
   }

   Erro 400: { "detail": "Agent config not generated yet..." }
   Erro 500: { "detail": "Failed to generate simulation" }

   Nota: cada conversa tem 8-15 mensagens. O array acima está resumido.

2. Enquanto espera (~20s):
   - Loading: "Simulando conversas do seu agente..."
   - Texto: "Gerando cenários realistas com devedor cooperativo e resistente"

3. Quando retornar, mostrar 2 tabs ou cards lado a lado:
   - Tab 1: "Devedor Cooperativo" (ícone verde, badge "cooperative")
   - Tab 2: "Devedor Resistente" (ícone vermelho/laranja, badge "resistant")

   Cada tab mostra:
   - Perfil do devedor: debtor_profile como texto descritivo no topo
   - Conversa como chat bubbles:
     - Mensagens com role "agent": alinhadas à direita, cor da marca, avatar de robô
     - Mensagens com role "debtor": alinhadas à esquerda, cor cinza, avatar de pessoa
   - Card de resultado no final:
     - resolution traduzido: "full_payment" → "Pagamento integral",
       "installment_plan" → "Parcelamento", "escalated" → "Escalado para humano",
       "no_resolution" → "Sem resolução"
     - negotiated_discount_pct: "Desconto negociado: X%" (omitir se null)
     - final_installments: "Parcelas: Nx" (omitir se null)
     - payment_method: método de pagamento (omitir se null)

4. Botões:
   - "Aprovar agente" (principal) → mostra mensagem de sucesso, onboarding completo
   - "Regenerar simulação" → chama POST /simulation/generate novamente, mostra loading
   - "Voltar e ajustar" → volta para tela do agente

Estilo: interface de chat moderna (como WhatsApp), bolhas de mensagem,
avatar para agente e devedor, cores distintas por role, scroll suave.
```

**Definition of Done**:
- Loading durante geração
- 2 cenários mostrados como chat
- Mensagens formatadas como bolhas (agent vs debtor)
- Resultado/métricas visíveis
- Botões de ação funcionam

**Status**: `pending`

---

### T38: Integração de fluxo + estado global

**Objective**: Conectar todas as 6 telas com navegação e estado compartilhado (session_id).

**Dependencies**: T32-T37

**Lovable Prompt**:
```
Integre as 6 telas de onboarding num fluxo único com navegação e estado global.

Contexto: As telas já existem individualmente. Agora precisamos:

1. Estado global: session_id deve ser acessível em todas as telas.
   Pode usar Context, Zustand, ou URL params (recomendado: Context + localStorage
   para sobreviver refresh).

2. Navegação sequencial:
   Boas-vindas → Enriquecimento → Entrevista → Defaults → Agente → Simulação
   - Navegação só para frente (sem botão "voltar" nas telas de entrevista)
   - Se refresh com session_id salvo: pode restaurar continuando do ponto atual
     (o backend mantém o estado da entrevista, então GET /interview/next retorna
     a pergunta atual)
   - Se refresh sem session_id: recomeçar do início

3. Trigger de onboarding: quando o usuário logado não tem nenhum agente criado,
   redirecionar para o onboarding ao invés do dashboard.

4. Conclusão: quando o usuário aprova a simulação na última tela, marcar onboarding
   como completo e redirecionar para o dashboard normal da plataforma.

5. Error handling global: se qualquer chamada de API falhar, mostrar toast/banner
   com mensagem amigável em português e opção de tentar novamente.
   Nunca travar o app — sempre dar saída ao usuário.

6. BACKEND_URL como variável de ambiente no Lovable.
   Todos os endpoints usam o padrão: {BACKEND_URL}/api/v1/sessions/{session_id}/...

7. Documentação interativa da API disponível em {BACKEND_URL}/docs (Swagger UI).
   Pode ser usada para testar endpoints manualmente durante o desenvolvimento.
```

**Definition of Done**:
- Fluxo completo funciona do início ao fim
- session_id persiste entre telas
- Erro em qualquer ponto não trava o app
- Onboarding trigger funciona no primeiro login
- Conclusão redireciona para dashboard

**Status**: `pending`

---

## M8: Integração Directus (futuro)

### T39: Salvar AgentConfig no Directus

**Objective**: Quando onboarding completa, salvar o AgentConfig na collection de agents do Directus.

**Dependencies**: T38

**Definition of Done**:
- Mapear campos do AgentConfig para a collection "agents" no Directus
- Endpoint ou lógica que envia o AgentConfig para o Directus
- Agent aparece na tela de agents da plataforma

**Status**: `pending`

---

## Task Summary

| ID | Task | Milestone | Dependencies | Status |
|----|------|-----------|-------------|--------|
| T01 | Initialize project structure | M0 | — | `done` |
| T02 | FastAPI app with health endpoint | M0 | T01 | `done` |
| T03 | Database setup + session model | M0 | T02 | `done` |
| T04 | Session API endpoints | M0 | T03 | `done` |
| T05 | Website scraping service | M1 | T01 | `done` |
| T06 | LLM extraction service | M1 | T01 | `done` |
| T07 | Enrichment API endpoint | M1 | T04, T05, T06 | `done` |
| T08 | Core questions data structure | M2 | — | `done` |
| T09 | LangGraph interview state + basic graph | M2 | T08 | `done` |
| T10 | Interview "next question" endpoint | M2 | T04, T09 | `done` |
| T11 | Interview "submit answer" endpoint | M2 | T10 | `done` |
| T12 | AI follow-up evaluation + generation | M2 | T11 | `done` |
| T13 | Dynamic question generation | M2 | T12 | `done` |
| T14 | Interview progress endpoint + completion | M2 | T13 | `done` |
| T15 | Smart defaults confirmation endpoint | M2 | T14 | `done` |
| T16 | Audio transcription service | M2 | T01 | `done` |
| T17 | Audio upload endpoint | M2 | T04, T16 | `done` |
| T18 | AgentConfig Pydantic schema | M3 | — | `done` |
| T19 | Agent generation prompt | M3 | T18 | `done` |
| T20 | Agent generation service + sanity checks | M3 | T19 | `done` |
| T21 | Agent generation endpoint | M3 | T04, T20 | `done` |
| T22 | Agent adjustment endpoint | M3 | T21 | `done` |
| T23 | Simulation prompt + service | M4 | T18 | `done` |
| T24 | Simulation endpoint | M4 | T21, T23 | `done` |
| T25 | End-to-end integration test | M5 | T24 | `done` |
| T26 | Refatorar perguntas core + follow-up | M5.5 | T25 | `done` |
| T27 | Refatorar perguntas dinâmicas | M5.5 | T26 | `done` |
| T28 | Atualizar prompt de geração | M5.5 | T27 | `done` |
| T29 | CORS configuration | M6 | T28 | `pending` |
| T30 | Dockerfile + Railway config | M6 | T29 | `pending` |
| T31 | Deploy to Railway + verify | M6 | T30 | `pending` |
| T32 | Tela de Boas-vindas | M7 | T31 | `pending` |
| T33 | Tela de Enriquecimento | M7 | T32 | `pending` |
| T34 | Tela de Entrevista (wizard) | M7 | T33 | `pending` |
| T35 | Tela de Smart Defaults | M7 | T34 | `pending` |
| T36 | Tela do Agente Gerado | M7 | T35 | `pending` |
| T37 | Tela de Simulação | M7 | T36 | `pending` |
| T38 | Integração de fluxo completo | M7 | T37 | `pending` |
| T39 | Salvar AgentConfig no Directus | M8 | T38 | `pending` |
