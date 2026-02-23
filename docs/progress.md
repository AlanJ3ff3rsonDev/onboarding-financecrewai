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
| 2026-02-22 | Refactored financial questions from select to open-ended text (core_6/7/8/9). Removed SmartDefaults entirely. Replaced NegotiationPolicies numeric fields with text descriptions. Replaced "defaults" interview phase with "review" phase. | Specific financial values (discount %, interest rate, penalty %, installment count) are campaign-level configuration, not onboarding-level. Onboarding captures the company's macro collection methodology. | 10 tests removed (SmartDefaults/numeric), 8 tests added (review/text-based). 120→116 total tests. All schemas, prompts, services, routers, and tests updated. |
| 2026-02-22 | M5.5: Refactored question system. Core 12→14 questions. Max dynamic 8→3. Follow-ups disabled for dynamic phase. Frustration detection added. Question bank cleaned up. Agent generator now instructs LLM that agent is expert. | Agent already knows collection best practices — onboarding should only capture company-specific information. Generic questions and aggressive follow-ups were making the experience frustrating. | 116→118 tests. Tasks renumbered: old T26-T36 → T29-T39. |
| 2026-02-20 | Removed contact hours from SmartDefaults and AgentConfig (contact_hours_weekday, contact_hours_saturday, contact_sunday, ContactHours schema) | In the final solution, messages are always available — timing is user-controlled, not agent-controlled. These fields would be unnecessary questions. | SmartDefaults: 11→8 fields. Guardrails: removed contact_hours. Removed _validate_contact_hours(). Removed test_defaults_validation_hours. 85→84 tests. |
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

### 2026-02-22 — M5.5 (T26-T28): Refatoração do Sistema de Perguntas

**Status**: completed

**What was done**:

**T26 — Refatorar perguntas core e sistema de follow-up**:
- **core_12 reformulada**: "Quais são as razões mais comuns..." → "Existe alguma objeção ou situação específica do seu negócio..." (foco em objeções business-specific, não genéricas)
- **core_13 adicionada**: "Como vocês sabem se um cliente pagou? Como ele pode comprovar o pagamento?" (informação operacional que o agente precisa)
- **core_14 adicionada**: "Existe alguma regulamentação específica do seu setor que impacta a cobrança?" (guardrails setoriais)
- **FOLLOW_UP_EVALUATION_PROMPT melhorado**: adicionado "NÃO aprofunde conhecimento padrão de cobrança" + "se cliente sinaliza frustração, retorne needs_follow_up: false"
- **Detecção de frustração hardcoded**: lista FRUSTRATION_SIGNALS com 13 frases ("isso vocês que sabem", "cansei", "chega de perguntas", etc.) — check antes do LLM call em evaluate_and_maybe_follow_up()

**T27 — Refatorar sistema de perguntas dinâmicas**:
- **max_dynamic_questions: 8 → 3** (em initialize(), create_interview(), deserialize_state())
- **Follow-ups desabilitados na fase dinâmica**: condição `not is_dynamic_phase` adicionada em submit_answer()
- **DYNAMIC_QUESTION_BANK reescrito**: removido scenario_handling, communication, current_pain (genéricos). Mantido business_model, debtor_profile, negotiation_depth, legal_judicial, segmentation. Adicionado brand_language, payment_operations. Total: 8→7 categorias
- **DYNAMIC_QUESTION_PROMPT reescrito**: "NUNCA pergunte o que um agente especialista em cobrança já sabe"
- **INTERVIEW_COMPLETENESS_PROMPT ajustado**: critérios mais generosos — "o agente já é ESPECIALISTA, avalie apenas informações ESPECÍFICAS DA EMPRESA"

**T28 — Atualizar prompt de geração do agente**:
- **SYSTEM_PROMPT reformulado**: "The collection agent is ALREADY AN EXPERT. Use your expertise to generate comprehensive scenario_responses and fill gaps with BEST PRACTICES adapted to the company's tone and policies."
- **build_prompt adaptado**: core_13 em "Operações e Cenários" (verificação de pagamento), core_14 em "Guardrails e Escalação" (regulamentação setorial). Seção 8 renomeada de "Tratamento de Cenários" → "Operações e Cenários"
- **ADJUSTMENT_SYSTEM_PROMPT**: mesma filosofia adicionada

**Files modified** (5):
- `app/prompts/interview.py` — core_12 reformulada, core_13/14 adicionadas, question bank reescrito, prompts melhorados
- `app/services/interview_agent.py` — FRUSTRATION_SIGNALS, frustration detection, max_dynamic 8→3, follow-up skip for dynamic
- `app/prompts/agent_generator.py` — SYSTEM_PROMPT expert philosophy, build_prompt for core_13/14, ADJUSTMENT_SYSTEM_PROMPT
- `tests/test_interview.py` — All counts updated (12→14, 8→3), 2 new tests
- `tests/test_agent_generator.py` — Fixtures updated with core_12/13/14 answers, assertions updated

**Tests**:
- [x] Automated: 118/118 tests passing (116 existing updated + 2 new)
- [x] New: test_frustration_signal_skips_follow_up — frustration phrase detected, LLM not called, advances normally
- [x] New: test_dynamic_phase_skips_follow_up — dynamic answer skips follow-up evaluation entirely

**Issues found**:
- None

**Next steps**:
- Git commit & push. Next task: T29 (CORS configuration)

---

### 2026-02-22 — Refactor: Financial Questions + SmartDefaults Removal

**Status**: completed

**What was done**:
- **Financial questions (core_6/7/8/9)**: Changed from `select` with specific numeric options to `text` type with `context_hint` examples. Questions now ask "how does it work?" instead of "what percentage/number?"
- **SmartDefaults removed entirely**: Class, constant, import, ORM column, endpoints (GET/POST /interview/defaults), and all references deleted
- **NegotiationPolicies refactored**: Replaced numeric fields (max_discount_full_payment_pct, max_discount_installment_pct, max_installments, min_installment_value_brl, discount_strategy) with text-based descriptions (discount_policy, installment_policy, interest_policy, penalty_policy)
- **Interview phase "defaults" → "review"**: All phase references updated across state machine, router, and tests
- **Review endpoints added**: `GET /interview/review` returns answer summary + enrichment. `POST /interview/review` confirms with optional additional_notes stored as "review_notes" entry
- **Agent generation**: Removed `smart_defaults` parameter, removed `_extract_discount_limit()`, removed numeric sanity checks for discounts/installments. Kept system_prompt quality check and guardrails bounds checks
- **Simulation prompt**: Updated to reference text-based policy descriptions instead of numeric limits
- **Guardrails**: Added defaults (follow_up_interval_days=3, max_attempts_before_stop=10, must_identify_as_ai=True) — populated by LLM during generation
- **All 5 test files rewritten**: test_interview.py, test_agent_generator.py, test_agent_config.py, test_simulation.py, test_integration.py

**Files modified** (13):
- `app/models/schemas.py` — Removed SmartDefaults, refactored NegotiationPolicies, added InterviewReviewRequest
- `app/models/orm.py` — Removed smart_defaults column
- `app/prompts/interview.py` — core_6/7/8/9 to text, removed SMART_DEFAULTS
- `app/prompts/agent_generator.py` — Removed smart_defaults from prompt, updated section labels
- `app/prompts/simulation.py` — Text-based NegotiationPolicies in prompt
- `app/services/interview_agent.py` — "defaults" → "review" phase
- `app/services/agent_generator.py` — Removed _extract_discount_limit, numeric sanity checks, smart_defaults param
- `app/routers/interview.py` — Removed defaults endpoints, added review endpoints
- `app/routers/agent.py` — Removed smart_defaults from generate call
- `tests/test_interview.py` — Rewrote financial/defaults/review tests
- `tests/test_agent_generator.py` — Updated fixtures and assertions
- `tests/test_agent_config.py` — Text-based NegotiationPolicies
- `tests/test_simulation.py` — Text-based NegotiationPolicies
- `tests/test_integration.py` — Text answers for core_6-9, review step replaces defaults

**Tests**:
- [x] Automated: 115/115 unit tests passing (0 failures)
- [x] Tests removed: 10 (SmartDefaults, numeric discount cap, defaults endpoints)
- [x] Tests added: 8 (review endpoints, text-based policies, open text questions)
- [x] Net: 120 → 116 total (115 unit + 1 integration)

**Issues found**:
- None

**Next steps**:
- Manual end-to-end test, then git commit & push

---

### 2026-02-20 — T25: End-to-end integration test

**Status**: completed

**What was done**:
- Created `tests/test_integration.py` with `test_full_onboarding_flow` — single test that walks through the entire onboarding pipeline
- Uses **real OpenAI API calls** (not mocked) and **real Playwright scraping** — marked with `@pytest.mark.integration`
- Test flow: create session → enrich (collectai.com.br) → verify enrichment → start interview → answer 12 core questions → answer dynamic questions → confirm defaults → generate agent → verify agent → generate simulation → verify simulation + final session state
- Helpers:
  - `_answer_question()` — submits answer and handles follow-up loop (up to 3 iterations client-side, server caps at 2)
  - `_answer_dynamic_questions()` — loops through dynamic questions until phase becomes "defaults" (safety limit: 20 iterations)
- Answer strategy: select/multiselect answers avoid "outro"/"depende" to skip follow-up eval; text answers are detailed (2+ sentences) to minimize follow-ups
- Assertions are structural (status codes, required fields, valid enums, min lengths) — never assert on specific LLM-generated content
- Run command: `cd backend && uv run pytest -m integration -v`

**Tests**:
- [x] Automated: `test_full_onboarding_flow` — full pipeline from session creation to simulation verification (PASSED)
- [x] Full suite: 120/120 tests passing (119 existing + 1 new, no regressions)
- [x] Execution time: ~2:35 (well within 3-minute limit)

**Issues found**:
- None

**Next steps**:
- M5 complete (T25). All milestones M0-M5 done. Backend MVP is complete.

---

### 2026-02-20 — Documentation Update: Frontend + Deploy Phase

**Status**: completed

**What was done**:
- Updated all project docs to reflect backend completion and plan the next phases (deploy + frontend + Directus integration)
- Created `backend/cli_test.py` — interactive CLI script for manual end-to-end testing (httpx, ANSI colors, supports all question types)
- **PRD.md**: Status → Active. Marked backend as COMPLETE. Added FR-6 (Frontend: 6 telas), FR-7 (Deploy). Updated core questions from 10 to 12. Removed contact hours. Added platform architecture diagram. Updated Open Questions.
- **tech_design.md**: Added Lovable/Directus/Railway to stack. Updated project structure with actual test counts (120). Corrected API endpoints to match implementation. Added Deploy section (Dockerfile, CORS). Added Frontend Architecture section. Added Key Design Decisions section.
- **tasks.md**: Added M6 (Deploy: T26-T28), M7 (Frontend: T29-T35 with Lovable prompts), M8 (Directus: T36). Updated Milestone Overview table. Added T26-T36 to Task Summary. Each M7 task includes copy-paste ready Lovable prompts with endpoints, request/response schemas, and Definition of Done.
- **progress.md**: This entry.

**Key decisions**:
- Updated existing docs instead of creating parallel new ones (user's request)
- M7 tasks include detailed Lovable prompts — user can copy-paste them directly into Lovable for frontend generation
- M8 (Directus integration) marked as "Future" — AgentConfig stays in onboarding backend for now

**Issues found**:
- None

**Next steps**:
- Next task: T26 (CORS configuration) — first task of M6 (Deploy)

---

### 2026-02-20 — Documentation Quality Review + Schema Improvements

**Status**: completed

**What was done**:
- Critical review of all docs for Lovable-readiness. Found 5 gaps.
- **tech_design.md — new Section 5 "API Response Schemas"**: Added complete JSON examples for every response type the frontend needs (InterviewQuestion, CompanyProfile, SmartDefaults, AgentConfig with all nested objects, SimulationResult with nested messages/metrics, AgentAdjustRequest). Each with exact field names, types, and allowed values.
- **tech_design.md — Section 8 "Frontend Architecture"**: Added audio flow documentation (MediaRecorder → POST /audio/transcribe → text → answer with source:"audio"). Added Swagger reference.
- **tech_design.md — section renumbering**: Fixed 5→6→7→8→9→10→11 after inserting new section.
- **tasks.md — T29 (Boas-vindas)**: Added CNPJ mask format, URL validation hint, error 422 response, complete request/response example.
- **tasks.md — T30 (Enriquecimento)**: Added complete CompanyProfile JSON example, field label translations PT, handling of 409 (already enriched).
- **tasks.md — T31 (Entrevista)**: Major rewrite. Added complete InterviewQuestion schema with all fields. Added QuestionOption format (value+label). Added explicit rules for select/multiselect answer format. Added complete audio recording flow (MediaRecorder API → transcribe endpoint → fill textarea). Added phase transition logic diagram. Added InterviewProgressResponse schema.
- **tasks.md — T32 (Smart Defaults)**: Added complete SmartDefaults JSON example. Added table with all 8 fields, their labels PT, input types, and validation rules. Added discount_strategy select options with values ("only_when_resisted"/"proactive"/"escalating") and labels PT.
- **tasks.md — T33 (Agente)**: Added complete AgentConfig JSON example with all nested objects. Added tone.style translation table. Added adjustment flow with PUT /adjust endpoint, dotted-path syntax example, and response schema.
- **tasks.md — T34 (Simulação)**: Added complete SimulationResult JSON example with 2 scenarios, conversation messages, metrics. Added resolution translation table. Added null handling for optional metrics.
- **tasks.md — T35 (Integração)**: Added session restoration on refresh, Swagger reference, explicit error handling guidance.

**Gaps addressed**:
1. Missing response schemas → complete JSON examples inline in every Lovable prompt
2. Missing audio flow → full MediaRecorder + transcribe flow added to T31 + tech_design
3. Missing select values → exact values + labels for all selects (discount_strategy, etc.)
4. Vague adjust flow → complete PUT /adjust example with dotted-path syntax
5. Missing Swagger reference → added to tech_design + T35

**Issues found**:
- None

**Next steps**:
- Next task: T26 (CORS configuration) — first task of M6 (Deploy)

---

### 2026-02-20 — T24: Simulation endpoint

**Status**: completed

**What was done**:
- Implemented `app/routers/simulation.py` with two endpoints:
  - `POST /api/v1/sessions/{id}/simulation/generate` — validates session exists, agent_config exists, status is "generated" or "completed". Transitions status: → "simulating" → calls `generate_simulation()` → stores result → "completed". On failure, reverts status to "generated" and returns 500.
  - `GET /api/v1/sessions/{id}/simulation` — returns stored SimulationResult. 404 if not generated yet.
- Registered simulation router in `app/main.py`
- Supports re-generation: POST again on a "completed" session overwrites previous simulation
- Added 5 endpoint tests to `tests/test_simulation.py` (mocking the service, not OpenAI)

**Tests**:
- [x] Automated: `test_generate_simulation_endpoint` — session with agent_config → POST generate → 200, 2 scenarios returned, GET returns same, status="completed" (PASSED)
- [x] Automated: `test_simulate_before_agent` — POST without agent_config → 400 "not generated yet" (PASSED)
- [x] Automated: `test_simulate_session_not_found` — POST/GET on nonexistent session → 404 (PASSED)
- [x] Automated: `test_get_simulation_not_generated` — GET before simulation → 404 "not generated" (PASSED)
- [x] Automated: `test_re_simulate` — POST generate twice → both succeed, second overwrites first (PASSED)
- [x] Full suite: 119/119 tests passing (114 existing + 5 new, no regressions)
- [x] Manual: Full endpoint test via curl on uvicorn (port 8000):
  - POST simulate without agent_config → 400 "not generated yet" ✓
  - GET simulation before generation → 404 "not generated" ✓
  - POST/GET on nonexistent session → 404 "Session not found" ✓
  - Fast-forwarded session to "generated" with CollectAI agent config
  - POST /simulation/generate with real GPT-4.1-mini → 200, status="completed":
    - Scenario 1 (cooperative, 13 msgs): Joana, R$2,000 → 8x R$237.50 with 5% discount via PIX. Discount within limits (≤5% installment). Tone empathetic, used first name. Resolution: installment_plan ✓
    - Scenario 2 (resistant, 9 msgs): Carlos doesn't recognize debt → agent follows template → Carlos demands 50%/70% → agent caps at 10% → Carlos gets aggressive → agent follows aggressive_debtor template → escalated. No prohibited words used. Resolution: escalated ✓
  - GET /simulation → same 2 scenarios with metadata ✓
  - GET /sessions/{id} → status="completed", simulation_result stored ✓
  - Re-simulation: POST again on completed session → 200, new 2 scenarios generated (11 + 7 msgs) ✓

**Issues found**:
- None

**Next steps**:
- M4 complete (T23-T24). Move to M5: T25 (End-to-end integration test)

---

### 2026-02-20 — T23: Simulation prompt + service

**Status**: completed

**What was done**:
- Added 5 Pydantic schemas to `app/models/schemas.py`: `SimulationMessage` (role: agent/debtor, content), `SimulationMetrics` (negotiated_discount_pct, final_installments, payment_method, resolution), `SimulationScenario` (scenario_type, debtor_profile, conversation, outcome, metrics), `SimulationResult` (scenarios list, metadata dict)
- Implemented `app/prompts/simulation.py` with:
  - `SYSTEM_PROMPT`: English instructions for LLM to generate realistic Portuguese collection conversations following agent config strictly
  - `_SIMULATION_SCHEMA`: JSON Schema from `SimulationResult.model_json_schema()`
  - `build_simulation_prompt(agent_config: AgentConfig) -> str`: Assembles 8 sections — system prompt, company context, tone, negotiation policies, guardrails, scenario templates, scenario instructions, output schema
- Implemented `app/services/simulation.py` with:
  - `generate_simulation(agent_config, session_id) -> SimulationResult`: Async function calling GPT-4.1-mini with structured JSON output, 2-attempt retry, metadata injection
  - `_apply_sanity_checks(data) -> list[str]`: Validates scenario count (2) and conversation length (8-15 msgs). Non-fatal warnings only.
- Added 7 tests to `tests/test_simulation.py`

**Tests**:
- [x] Automated: `test_build_simulation_prompt` — prompt includes company name, tone, discount limits, guardrails, JSON schema (PASSED)
- [x] Automated: `test_prompt_includes_scenario_instructions` — prompt includes cooperative/resistant scenario instructions (PASSED)
- [x] Automated: `test_simulation_schema_valid` — valid data → SimulationResult with 2 scenarios, correct types (PASSED)
- [x] Automated: `test_simulation_schema_invalid_resolution` — invalid resolution value → ValidationError (PASSED)
- [x] Automated: `test_generate_simulation` — mock LLM returns valid JSON → SimulationResult with metadata injected (PASSED)
- [x] Automated: `test_generate_retries_on_failure` — first call fails, second succeeds → returns valid result, 2 calls made (PASSED)
- [x] Automated: `test_generate_both_attempts_fail` — both calls fail → ValueError "2 tentativas" (PASSED)
- [x] Full suite: 114/114 tests passing (107 existing + 7 new, no regressions)
- [x] Manual: Generated simulation with real GPT-4.1-mini using CollectAI agent config:
  - Scenario 1 (cooperative, 13 msgs): Carlos, R$1,800 debt → negotiated 6x R$285 with 5% discount via PIX. Discounts within limits (≤10% full, ≤5% installment). Tone empathetic, used first name. Resolution: installment_plan ✓
  - Scenario 2 (resistant, 9 msgs): Mariana contests debt → agent follows dont_recognize_debt template → Mariana demands 50% discount → agent caps at 10% → Mariana gets aggressive → agent follows aggressive_debtor template → escalated. No prohibited words (SPC/Serasa/processo) used. Resolution: escalated ✓

**Issues found**:
- **First manual test produced short conversations** (7 and 5 messages). Cause: SYSTEM_PROMPT wasn't emphatic enough about message count. **Fix**: Strengthened prompt to say "CRITICAL: minimum 10 messages" and added detailed step-by-step scenario instructions describing the conversation flow. Second test produced 13 and 9 messages (much better).

**Next steps**:
- Move to T24: Simulation endpoint

---

### 2026-02-20 — T22: Agent adjustment endpoint

**Status**: completed

**What was done**:
- Added `AgentAdjustRequest` Pydantic schema to `app/models/schemas.py` — `adjustments: dict[str, Any]` with `min_length=1` (dotted-path keys → new values)
- Added `ADJUSTMENT_SYSTEM_PROMPT` and `build_adjustment_prompt()` to `app/prompts/agent_generator.py`:
  - System prompt instructs LLM to regenerate ONLY `system_prompt` and `scenario_responses` from the full adjusted config
  - User message includes adjustments summary + full config JSON
- Added two functions to `app/services/agent_generator.py`:
  - `_apply_dotted_path_adjustments(config_dict, adjustments)` — pure utility: deepcopy, walk dotted paths, set values, return (updated_dict, summary_lines). Raises ValueError for invalid paths.
  - `adjust_agent_config(current_config, adjustments, session_id)` — applies structural changes, increments version, calls LLM to regenerate text fields, validates via `AgentConfig(**dict)`. 2-attempt retry on LLM failure.
- Added `PUT /api/v1/sessions/{id}/agent/adjust` to `app/routers/agent.py`:
  - Guards: 404 if session not found, 400 if no agent_config
  - Catches ValueError → 400
  - Status stays "generated" (no lifecycle transition)
  - Returns `{"status": "adjusted", "agent_config": ...}`
- Added 9 tests to `tests/test_agent_generator.py`

**Tests**:
- [x] Automated: `test_apply_dotted_path_valid` — valid paths update correctly, deepcopy protects original (PASSED)
- [x] Automated: `test_apply_dotted_path_invalid` — bad path → ValueError "Caminho inválido" (PASSED)
- [x] Automated: `test_adjust_tone` — PUT with tone.style=empathetic → config returned with new tone (PASSED)
- [x] Automated: `test_adjust_discount` — PUT with discount=20 → negotiation_policies updated (PASSED)
- [x] Automated: `test_adjust_version_incremented` — version goes from 1 to 2, GET returns updated version (PASSED)
- [x] Automated: `test_adjust_before_generation` — PUT on session with no agent_config → 400 (PASSED)
- [x] Automated: `test_adjust_session_not_found` — PUT on nonexistent session → 404 (PASSED)
- [x] Automated: `test_adjust_invalid_path` — PUT with bad dotted path → 400 "Caminho inválido" (PASSED)
- [x] Automated: `test_adjust_empty_adjustments` — PUT with empty dict → 422 (Pydantic min_length) (PASSED)
- [x] Full suite: 107/107 tests passing (98 existing + 9 new, no regressions)
- [x] Manual: Full adjustment flow via curl on uvicorn (port 8000):
  - PUT adjust on non-generated session → 400 "not generated yet" ✓
  - Generated agent config with real GPT-4.1-mini (version=1, tone=friendly, discount=10%)
  - PUT adjust `tone.style=empathetic` → version=2, tone=empathetic, system_prompt reflects empathy ✓
  - PUT adjust `negotiation_policies.max_discount_full_payment_pct=20` → version=3, discount=20%, system_prompt mentions 20% ✓
  - PUT with invalid path → 400 "Caminho inválido" ✓
  - GET /agent → final state persisted (version=3, tone=empathetic, discount=20%) ✓
  - Session status stays "generated" after adjustments ✓

**Issues found**:
- None

**Next steps**:
- M3 complete (T18-T22). Move to M4: T23 (Simulation prompt + service)

---

### 2026-02-20 — T21: Agent generation endpoint

**Status**: completed

**What was done**:
- Implemented `app/routers/agent.py` with two endpoints:
  - `POST /api/v1/sessions/{id}/agent/generate` — validates session status is "interviewed" or "generated", transitions to "generating" → calls `generate_agent_config()` → stores result in `agent_config` column → transitions to "generated". On generation failure, reverts status to "interviewed" and returns 500.
  - `GET /api/v1/sessions/{id}/agent` — returns stored AgentConfig. 404 if not generated yet.
- Registered agent router in `app/main.py`
- Status validation: 400 if session not in "interviewed"/"generated" state
- Re-generation supported: calling POST generate on an already-generated session works (overwrites previous config)
- Added 6 endpoint tests to `tests/test_agent_generator.py`

**Tests**:
- [x] Automated: `test_generate_agent_endpoint` — interviewed session → POST generate → 200, agent_config stored, GET returns it, status="generated" (PASSED)
- [x] Automated: `test_generate_before_interview` — POST on non-interviewed session → 400 (PASSED)
- [x] Automated: `test_get_agent_not_generated` — GET before generation → 404 (PASSED)
- [x] Automated: `test_generate_session_not_found` — POST on nonexistent session → 404 (PASSED)
- [x] Automated: `test_get_agent_session_not_found` — GET on nonexistent session → 404 (PASSED)
- [x] Automated: `test_regenerate_agent` — POST generate twice → both succeed (PASSED)
- [x] Full suite: 98/98 tests passing (92 existing + 6 new, no regressions)
- [x] Manual: Full endpoint test via curl on uvicorn (port 8000):
  - POST /agent/generate on "created" session → 400 "Interview must be completed" ✓
  - GET /agent before generation → 404 "not generated yet" ✓
  - POST/GET on nonexistent session → 404 "Session not found" ✓
  - Fast-forwarded session to "interviewed" with real CollectAI data (12 core + 2 dynamic answers)
  - POST /agent/generate with real GPT-4.1-mini → 200, agent_config generated:
    - system_prompt: 1,883 chars, comprehensive, mentions CollectAI, covers all policies
    - Discounts: 10% full / 5% installment (matches interview + defaults)
    - Tone: friendly, use_first_name=true, prohibited words include SPC/Serasa
    - Scenario responses: realistic with {first_name} placeholders
    - Tools: 6 tools including generate_pix_payment_link and generate_boleto
    - Guardrails: never_do/never_say match core_11, escalation matches core_10
  - GET /agent → returns same config ✓
  - GET /sessions/{id} → status="generated", agent_config stored ✓

**Issues found**:
- None

**Next steps**:
- Move to T22: Agent adjustment endpoint

---

### 2026-02-20 — T20: Agent generation service + sanity checks

**Status**: completed

**What was done**:
- Implemented `app/services/agent_generator.py` with:
  - `generate_agent_config(company_profile, interview_responses, smart_defaults, session_id) -> AgentConfig` — async function calling GPT-4.1-mini with structured JSON output
  - 2-attempt retry loop with logging on failures; raises `ValueError` if both fail
  - Auto-injects `metadata` fields (generated_at, onboarding_session_id, generation_model)
  - `_apply_sanity_checks(data, interview_responses, smart_defaults) -> list[str]` — validates and auto-corrects LLM output, returns list of corrections
  - `_extract_discount_limit(interview_responses) -> float | None` — parses core_6 answer to extract max discount
- Sanity checks implemented:
  - `system_prompt` < 200 chars → raises ValueError (fatal, can't auto-correct)
  - `system_prompt` missing company name → logs warning (non-fatal)
  - `max_discount_full_payment_pct` > interview answer → capped to interview limit
  - `max_discount_installment_pct` > smart_defaults → capped to defaults limit
  - Discount ranges clamped to Pydantic-valid bounds (0-100, 0-50)
  - `max_installments` clamped to 0-48
  - `follow_up_interval_days` clamped to 1-30
  - `max_attempts_before_stop` clamped to 1-30
- Note: contact hours sanity check removed (contact hours were removed from schema per Decisions Log)

**Tests**:
- [x] Automated: `test_generate_agent_config` — mock LLM returns valid dict → AgentConfig with correct fields and metadata (PASSED)
- [x] Automated: `test_sanity_check_discount_cap` — LLM returns 50% discount, interview says 10% → capped to 10% (PASSED)
- [x] Automated: `test_sanity_check_system_prompt_quality` — system_prompt < 200 chars → raises ValueError (PASSED)
- [x] Automated: `test_generate_retries_on_failure` — first call fails, second succeeds → returns valid config, 2 calls made (PASSED)
- [x] Automated: `test_generate_both_attempts_fail` — both OpenAI calls fail → raises ValueError "2 tentativas" (PASSED)
- [x] Full suite: 92/92 tests passing (87 existing + 5 new, no regressions)

**Issues found**:
- None

- [x] Manual: Generated agent config with real GPT-4.1-mini using realistic CollectAI data (12 core + 2 dynamic + 1 follow-up). Result:
  - system_prompt: 1,719 chars, comprehensive, mentions CollectAI by name, covers tone/negotiation/escalation/scenarios
  - Discounts: 10% full / 5% installment (correctly matches interview + defaults)
  - Tone: friendly, use_first_name=True, appropriate prohibited/preferred words in Portuguese
  - Scenario responses: realistic and empathetic with {first_name} placeholders
  - Tools: 6 tools including generate_pix_payment_link and generate_boleto (from payment methods)
  - Guardrails: never_do/never_say match interview core_11, escalation matches core_10

**Next steps**:
- Move to T21: Agent generation endpoint

---

### 2026-02-20 — T19: Agent generation prompt

**Status**: completed

**What was done**:
- Implemented `app/prompts/agent_generator.py` with:
  - `SYSTEM_PROMPT`: English-language system message defining the LLM's role as an expert debt collection agent configurator for Brazilian businesses. Emphasizes `system_prompt` field as the crown jewel (300+ words, segment-specific, Portuguese).
  - `build_prompt(company_profile, interview_responses, smart_defaults) -> str`: Assembles all onboarding data into 8 organized sections + mapping hints + full JSON Schema.
  - 5 helper functions: `_get_answer_by_id()`, `_get_followups()`, `_get_dynamic_responses()`, `_format_answer_with_followups()`, `_build_company_section()`, `_build_defaults_section()`
- Prompt sections:
  1. Contexto da Empresa (enrichment data)
  2. Modelo de Negócio e Faturamento (core_1, core_2, core_3)
  3. Perfil do Devedor (core_12)
  4. Processo de Cobrança Atual (core_4)
  5. Tom e Comunicação (core_5, core_11)
  6. Regras de Negociação (core_6-9 + smart defaults)
  7. Guardrails e Escalação (core_10, core_11 + smart defaults)
  8. Tratamento de Cenários (core_12 + dynamic Qs)
  - Contexto Adicional (all dynamic/follow-up answers)
  - Dicas de Mapeamento (tone style mapping, discount mapping, tools guidance)
  - Esquema JSON de Saída (full AgentConfig.model_json_schema())
- Module-level `_AGENT_CONFIG_SCHEMA` constant generated from `AgentConfig.model_json_schema()`
- Graceful handling: None enrichment, empty responses, None defaults all work

**Tests**:
- [x] Automated: `test_build_prompt` — complete data → substantial prompt string with company name and AgentConfig reference (PASSED)
- [x] Automated: `test_prompt_includes_all_sections` — all 8 section headings present, key answers (core_1, core_5, core_10, core_11, core_12), follow-ups, dynamic Qs, smart defaults, mapping hints, JSON schema (PASSED)
- [x] Automated: `test_prompt_handles_missing_data` — None/empty inputs work; partial data (just company_name + 1 answer) works with fallbacks (PASSED)
- [x] Full suite: 87/87 tests passing (84 existing + 3 new, no regressions)
- [x] Manual: Generated prompt with realistic data (CollectAI, 12 core + 3 dynamic + follow-ups). Prompt is 11,266 chars, well-organized, includes all interview context.

**Issues found**:
- None

**Next steps**:
- Move to T20: Agent generation service + sanity checks (when ready)

---

### 2026-02-20 — T18: AgentConfig Pydantic schema

**Status**: completed

**What was done**:
- Added 8 nested Pydantic models to `app/models/schemas.py`:
  - `CompanyContext` (name, segment, products, target_audience)
  - `ContactHours` (weekday, saturday, sunday nullable)
  - `ToneConfig` (style literal, use_first_name, prohibited/preferred words, opening_message_template)
  - `NegotiationPolicies` (discount caps with ge/le validators, installments, strategy literal, payment methods, link generation)
  - `Guardrails` (never_do/say lists, escalation_triggers, contact_hours nested, follow_up_interval, max_attempts, must_identify_as_ai)
  - `ScenarioResponses` (already_paid, dont_recognize_debt, cant_pay_now, aggressive_debtor)
  - `AgentMetadata` (version, generated_at, onboarding_session_id, generation_model)
  - `AgentConfig` (root — agent_type, company_context, system_prompt min_length=200, tone, negotiation_policies, guardrails, scenario_responses, tools, metadata)
- Validation rules: discount full_payment le=100, installment le=50, max_installments le=48, system_prompt min_length=200, follow_up_interval ge=1, max_attempts ge=1
- Created `tests/test_agent_config.py` with 3 tests

**Tests**:
- [x] Automated: `test_agent_config_valid` — full valid instance created without errors (PASSED)
- [x] Automated: `test_agent_config_invalid_discount` — discount >100% and >50% both raise ValidationError (PASSED)
- [x] Automated: `test_agent_config_json_schema` — model_json_schema() returns valid dict with all 9 top-level properties and 7 $defs (PASSED)
- [x] Full suite: 85/85 tests passing (no regressions)
- [x] Post-task cleanup: Removed contact hours fields (user decision) → 84/84 tests passing
- [x] Manual: Verified via curl on uvicorn (port 8000):
  - GET /interview/defaults → 8 fields, no contact_hours_weekday/saturday/sunday ✓
  - POST /interview/defaults with adjusted values → confirmed=true, phase=complete ✓
  - GET /sessions/{id} → status="interviewed", smart_defaults stored correctly ✓
  - POST with negative min_installment → 422 ✓
  - POST with discount > 50% → 422 ✓

**Issues found**:
- Minor: T17 was marked `done` in progress.md but still `pending` in tasks.md summary table. Fixed.
- Contact hours removed from SmartDefaults, Guardrails, and AgentConfig (user decision — see Decisions Log).

**Next steps**:
- Move to T19: Agent generation prompt

---

### 2026-02-20 — T17: Audio upload endpoint

**Status**: completed

**What was done**:
- Created `app/routers/audio.py` with `POST /api/v1/sessions/{id}/audio/transcribe`:
  - Accepts multipart file upload via `UploadFile`
  - Validates session exists (404 if not)
  - Reads file bytes and content type from the upload
  - Calls `transcribe_audio(file_bytes, content_type)` from T16's service
  - Catches `ValueError` → returns 400 with the error message
  - Returns `TranscriptionResponse` (`{ text, duration_seconds }`)
- Registered audio router in `app/main.py`
- Added 4 endpoint tests to `tests/test_audio.py` (mocking the service, not OpenAI)

**Tests**:
- [x] Automated: `test_transcribe_endpoint` — upload valid audio → 200 + text + duration (PASSED)
- [x] Automated: `test_transcribe_bad_format` — upload .txt → 400 "Formato não suportado" (PASSED)
- [x] Automated: `test_transcribe_no_file` — POST without file → 422 (PASSED)
- [x] Automated: `test_transcribe_session_not_found` — nonexistent session → 404 (PASSED)
- [x] Full suite: 82/82 tests passing (no regressions)
- [x] Manual: Full endpoint test via curl on uvicorn (port 8000):
  - POST with real `.ogg` audio file → `"Somos a empresa que faz cobranças e hoje temos 10 pessoas na operação e precisamos reduzir esse número."` ✓
  - POST with `text/plain` file → 400 "Formato não suportado" ✓
  - POST to non-existent session → 404 "Session not found" ✓
  - POST without file → 422 "Field required" ✓

**Issues found**:
- **Bug (found in tests)**: `_create_session()` helper used `company_website` instead of `website` as the field name in the JSON payload. The `CreateSessionRequest` schema uses `website`. Fixed immediately.

**Next steps**:
- M2 complete (T08-T17). Move to M3: T18 (AgentConfig Pydantic schema)

---

### 2026-02-20 — T16: Audio transcription service

**Status**: completed

**What was done**:
- Implemented `app/services/transcription.py` with `transcribe_audio(file_bytes, content_type) -> dict`:
  - Validates file is not empty, not > 25 MB, and has an allowed MIME type
  - Allowed types: audio/webm, audio/mp4, video/mp4, audio/wav, audio/x-wav, audio/mpeg, audio/mp3, audio/ogg, audio/flac, audio/x-m4a, audio/m4a
  - Uses `AsyncOpenAI` with model `gpt-4o-mini-transcribe`, language `"pt"`
  - Retries once on `OpenAIError`, then raises `ValueError` with user-friendly message
  - Returns `{"text": str, "duration_seconds": float}`
- Added `TranscriptionResponse` Pydantic schema to `app/models/schemas.py`
- Created `tests/test_audio.py` with 7 tests (all mock OpenAI)

**Tests**:
- [x] Automated: `test_transcribe_valid_audio` — valid bytes + audio/webm → text + duration returned, correct API params (PASSED)
- [x] Automated: `test_transcribe_invalid_format` — text/plain → ValueError "Formato não suportado" (PASSED)
- [x] Automated: `test_transcribe_too_large` — >25MB → ValueError "excede o limite" (PASSED)
- [x] Automated: `test_transcribe_empty_bytes` — empty bytes → ValueError "vazio" (PASSED)
- [x] Automated: `test_transcribe_api_error_retries` — first call fails, second succeeds → returns text (PASSED)
- [x] Automated: `test_transcribe_api_error_exhausted` — both attempts fail → ValueError "Falha na transcrição" (PASSED)
- [x] Automated: `test_transcribe_all_content_types` — all 11 MIME types accepted, correct file extensions (PASSED)
- [x] Full suite: 78/78 tests passing (no regressions)
- [x] Manual: Transcribed real audio file (`tests/audio to tests.ogg`, 22KB Ogg Opus) with real OpenAI API:
  - Input: Portuguese speech (~10s) about a collections company
  - Output: `"Somos uma empresa que faz cobranças e hoje temos dez pessoas na operação e precisamos reduzir esse número."` ✓
  - Transcription accurate and complete ✓

**Issues found**:
- **Bug (found in manual test)**: `.ogg` format was not in `ALLOWED_CONTENT_TYPES` — user's real audio file (Ogg Opus) would have been rejected with "Formato não suportado". The task spec listed only webm/mp4/wav/mpeg, but OpenAI supports more formats (ogg, flac, m4a). **Fix**: Added `audio/ogg`, `audio/flac`, `audio/x-m4a`, `audio/m4a` to allowed types. Updated error message.
- **Limitation noted**: `gpt-4o-mini-transcribe` does not return `duration` in its response (only `text` + `usage` tokens). The older `whisper-1` model with `verbose_json` does return duration (tested: 9.75s for the same file). Kept `gpt-4o-mini-transcribe` per tech design (cheaper). `duration_seconds` returns `0.0` — acceptable since the frontend already knows recording length.

**Next steps**:
- Move to T17: Audio upload endpoint

---

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
