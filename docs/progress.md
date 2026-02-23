# Progress Log: Self-Service Onboarding Backend

## How to Use This File

Log every task here. Entry format: date, task ID, status, what was done, tests, issues, next steps.
Full workflow: mark in_progress → implement → test task → test full suite → log here → mark done → git commit & push.

> **Archive**: Entries for T01-T28 are in `docs/progress_archive.md`.

---

## Decisions Log

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| 2026-02-23 | Core questions 16→10, avatar removed from scope, financial details → planilha | Simplify onboarding: majority select/multiselect, financial params via spreadsheet, avatar in platform | Docs only, T32 redefined |
| 2026-02-22 | Financial questions → open text, SmartDefaults removed, NegotiationPolicies → text, "defaults" → "review" phase | Specific financial values are campaign-level config, not onboarding-level | 120→116 tests |
| 2026-02-22 | M5.5: Core 12→14, dynamic 8→3, follow-ups off for dynamic, frustration detection, agent=expert | Onboarding captures only company-specific info | 116→118 tests |
| 2026-02-22 | Planned M5.6-M5.9: 6 new tasks (T29-T34). Old T29-T39 → T35-T45 | User feedback: SOP report, agent identity, web research | Task renumbering |
| 2026-02-20 | Removed contact hours from SmartDefaults and AgentConfig | Messages are always available — timing is user-controlled | SmartDefaults 11→8 fields |
| 2026-02-19 | Expanded core questions 10→12: added juros (core_8) and multa (core_9) | Not all businesses charge interest/fines | IDs renumbered |
| 2026-02-20 | T13 uses async helpers instead of formal LangGraph nodes for dynamic questions | Matches T12 pattern, avoids async→sync graph refactor | No architectural impact |

---

## Known Issues

| # | Description | Found in | Severity | Status |
|---|-------------|----------|----------|--------|
| | | | | |

---

## Development Log

### 2026-02-23 — T32 (M5.7): Remover avatar + reestruturar perguntas core (16→10)

**Status**: completed

**What was done**:

Part A — Remove Avatar:
- Deleted `upload_avatar` endpoint from `routers/agent.py` (+ ALLOWED_AVATAR_TYPES, MAX_AVATAR_SIZE, UPLOADS_DIR, UploadFile import)
- Removed `agent_avatar_path` from ORM model and `SessionResponse` schema
- Removed StaticFiles mount from `main.py` (+ Path, StaticFiles imports)
- Deleted `tests/test_avatar.py` (7 tests) and `app/uploads/` directory

Part B — Restructure Core Questions (16→10):
- Rewrote `CORE_QUESTIONS` in `interview.py`: 10 questions (2 text optional, 2 text required, 3 select, 3 multiselect)
- New questions: core_2 (PF/PJ select), core_6 (desconto select), core_8 (never-do multiselect), core_9 (business-specific text optional)
- Removed: core_3 (overdue), core_6-9 (financial details → spreadsheet), core_10/core_10_open, core_11-14
- Updated `DYNAMIC_QUESTION_BANK`: 7→4 categories (removed legal_judicial, segmentation, payment_operations, "B2C ou B2B?" from business_model)
- Updated `ENRICHMENT_PREFILL_MAP`: core_2→core_3 (payment), core_5→core_4 (tone)
- Rewrote `build_prompt()` in `agent_generator.py`: 9→7 sections, new ID mapping, conditional core_9 section

Part C — Update Tests:
- Updated all counts in test_interview.py (16→10), test_agent_generator.py (16→10 responses), test_integration.py (16→10)
- Deleted 3 obsolete tests (test_financial_questions_are_open_text, test_core_3_is_text_question, test_core_10_open_exists)
- Added 2 new tests (test_select_questions_have_options, test_multiselect_questions_have_options)
- Updated _dynamic_state helper, _session_in_review_phase helper, all progress tests, follow-up tests, enrichment pre-fill tests

**Tests**: 122/122 passing (130 - 7 avatar - 3 obsolete + 2 new = 122)
**Issues**: None

---

### 2026-02-23 — Doc Update: Simplificar onboarding (16→10 perguntas, remover avatar)

**Status**: completed (docs only)

**What was done**:
- PRD.md: Updated core questions table (16→10), removed avatar from features/user flow, added planilha vs onboarding data split
- tech_design.md: Removed Gemini API, avatar endpoints, agent_avatar_path, avatar_generator.py. Updated questions, pre-fill map, service architecture
- tasks.md: T31 marked out_of_scope, T32 redefined as "remove avatar + restructure core questions", T33/T34 simplified

**New core questions** (10, majority select/multiselect):
- core_0: agent name (text, optional)
- core_1: products (text, pre-filled)
- core_2: PF/PJ/ambos (select)
- core_3: payment methods (multiselect, pre-filled)
- core_4: tone (select, pre-filled)
- core_5: collection process (text)
- core_6: discount/special conditions (select)
- core_7: escalation triggers (multiselect)
- core_8: never-do list (multiselect)
- core_9: business-specific info (text, optional)

**Removed from scope**: avatar upload (T31), avatar generation (old T32), Gemini API
**Moved to planilha**: juros, multa, parcelamento, desconto %, payment verification, regulations

---

### 2026-02-23 — T31 (M5.7): Upload de foto do agente

**Status**: completed

**What was done**:
- `POST /api/v1/sessions/{id}/agent/avatar/upload` — multipart file upload (PNG/JPG/WebP, max 5MB)
- Validations: format (400), size (400), session existence (404)
- File storage: `app/uploads/avatars/{session_id}.{ext}`, removes previous on overwrite
- ORM: added `agent_avatar_path` column. Schema: added to `SessionResponse`
- Static files: mounted `/uploads` via StaticFiles

**Tests**: 130/130 passing (122 existing + 1 integration + 7 new avatar tests)
**Issues**: DB schema mismatch on production DB (recreated). Not an issue for tests.

---

### 2026-02-23 — T30 (M5.7): Pergunta de nome do agente (core_0)

**Status**: completed

**What was done**:
- core_0 added as first interview question (optional text)
- Total core questions: 15 → 16
- `is_optional_question` check in submit_answer() — optional core questions skip follow-up
- build_prompt() conditionally includes "Identidade do Agente" section

**Tests**: 122/122 passing (2 new: test_core_0_is_first_question, test_core_0_optional_skips_follow_up)
**Issues**: Bug: follow-up questions also skipped by optional check (both have is_required=False). Fix: narrowed to `is_required=False AND phase=="core"`.

---

### 2026-02-22 — T29 (M5.6): core_3 texto aberto + core_10_open

**Status**: completed

**What was done**:
- core_3 converted from select to text (captures tiered overdue rules)
- core_10_open added: optional text for business-specific escalation triggers
- Total core questions: 14 → 15
- Integration test: added missing core_13/core_14/core_10_open answers, rewrote loop

**Tests**: 120/120 passing (2 new: test_core_3_is_text_question, test_core_10_open_exists)
**Issues**: Integration test was missing core_13/core_14 answers from M5.5 refactor. Fixed.
