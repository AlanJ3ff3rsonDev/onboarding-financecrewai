# Tasks: Self-Service Onboarding Backend MVP

## How to Use This File

- Tasks are organized by **milestones** (M0-M5)
- Each task has a unique ID (T01, T02, etc.)
- **Do one task at a time**. Complete it, test it, log it in `progress.md`, then move to the next
- Tasks within a milestone are ordered — follow the order unless blocked
- Status: `pending` → `in_progress` → `done` (or `blocked`)

---

## Milestone Overview

| Milestone | Description | Tasks | Value Delivered |
|-----------|-------------|-------|----------------|
| **M0** | Project Setup | T01-T04 | FastAPI running, can create sessions, DB works |
| **M1** | Enrichment | T05-T07 | Given a website URL, system extracts structured company data |
| **M2** | Interview (Wizard) | T08-T17 | AI-driven interview collects all SOP data via text/audio |
| **M3** | Agent Generation | T18-T22 | System generates complete agent config JSON from interview data |
| **M4** | Simulation | T23-T24 | System generates 2 realistic simulated conversations |
| **M5** | Integration | T25 | Full end-to-end flow works from session creation to simulation |

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

**Status**: `pending`

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

**Status**: `pending`

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

**Status**: `pending`

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

**Status**: `pending`

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

**Status**: `pending`

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

**Status**: `pending`

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

**Status**: `pending`

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

**Status**: `pending`

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
| T17 | Audio upload endpoint | M2 | T04, T16 | `pending` |
| T18 | AgentConfig Pydantic schema | M3 | — | `pending` |
| T19 | Agent generation prompt | M3 | T18 | `pending` |
| T20 | Agent generation service + sanity checks | M3 | T19 | `pending` |
| T21 | Agent generation endpoint | M3 | T04, T20 | `pending` |
| T22 | Agent adjustment endpoint | M3 | T21 | `pending` |
| T23 | Simulation prompt + service | M4 | T18 | `pending` |
| T24 | Simulation endpoint | M4 | T21, T23 | `pending` |
| T25 | End-to-end integration test | M5 | T24 | `pending` |
