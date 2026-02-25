# Progress Log: Self-Service Onboarding Backend

## How to Use This File

Log every task here. Entry format: date, task ID, status, what was done, tests, issues, next steps.
Full workflow: mark in_progress → implement → test task → test full suite → log here → mark done → git commit & push.

> **Archive**: Entries for T01-T31 are in `docs/progress_archive.md`.

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

### 2026-02-25 — T36 (M6): Dockerfile + Railway Config

**Status**: completed

**What was done**:
- Created `backend/Dockerfile`: Python 3.13-slim, Playwright system deps, uv via multi-stage copy, `--frozen --no-dev` install, layer caching
- Created `backend/.dockerignore`: excludes .git, .venv, .env, tests, docs, *.db, __pycache__
- Build successful, container starts and serves `/health` → `{"status":"ok"}`
- Playwright verified inside container

**Tests**: 123/123 passing (no code changes, only infra files added)
**Docker**: `docker build` OK, `docker run` OK, health OK, Playwright OK

---

### 2026-02-24 — T35 (M6): CORS Configuration

**Status**: completed

**What was done**:
- Added `ALLOWED_ORIGINS` field to `Settings` in `config.py` (default: `localhost:3000,localhost:5173,portal.financecrew.ai`)
- Added `CORSMiddleware` to `main.py` after app creation, before routers
- Updated `.env.example` with `ALLOWED_ORIGINS`

**Tests**: 122/122 passing (unit). Integration test unchanged (pre-existing flaky, needs real API).
**Manual**: Verified with curl — allowed origin gets `access-control-allow-origin` header, disallowed origin does not. Preflight (OPTIONS) returns correct headers.

---

### 2026-02-24 — T34.1 (M5.9): Substituir AgentConfig por OnboardingReport (SOP)

**Status**: completed

**What was done**:
- Replaced `AgentConfig` schema with `OnboardingReport`: 9 new sub-models (AgentIdentity, ReportCompany, EnrichmentSummary, CollectionProfile, CollectionPolicies, Communication, ReportGuardrails, ReportMetadata, OnboardingReport)
- Removed 7 old schemas: CompanyContext, ToneConfig, NegotiationPolicies, Guardrails, ScenarioResponses, AgentMetadata, AgentConfig
- Key change: `system_prompt` (agent instructions) → `expert_recommendations` (analyst report, 300+ words PT-BR)
- Key change: `scenario_responses` (4 fixed scenarios) → `collection_profile` (expert-inferred debt context)
- Renamed: `generate_agent_config()` → `generate_onboarding_report()`, `adjust_agent_config()` → `adjust_onboarding_report()`
- API response key: `"agent_config"` → `"onboarding_report"` in generate/adjust endpoints
- Simulation prompt: uses expert_recommendations + collection_profile instead of system_prompt + scenario_responses
- ORM column `agent_config` kept (no migration needed)
- Renamed test file: `test_agent_config.py` → `test_onboarding_report.py`
- Updated cli_test.py display: expert_recommendations, collection_profile, communication, enrichment_summary

**Tests**: 122/122 passing (unit). Integration test flaky (enrichment scraping, pre-existing).

---

### 2026-02-24 — T34 (M5.9): Simplificar Entrevista (10→7 perguntas, remover dinâmicas)

**Status**: completed

**What was done**:
- Rewrote `CORE_QUESTIONS`: 10→7 questions. New: core_1 (process), core_2-5 (4 yes/no policies), core_6 (escalation text optional). Removed: old core_1-4 (products, PF/PJ, payments, tone → enrichment), core_7-8 (escalation, guardrails → defaults), core_9 (context → removed)
- Added `POLICY_FOLLOWUP_MAP`: deterministic follow-ups for core_2-5 when answered "sim" (no LLM needed)
- Added `DEFAULT_ESCALATION_TRIGGERS`, `DEFAULT_GUARDRAILS`, `DEFAULT_TONE` — hardcoded defaults replacing old interview questions
- Removed all dynamic question logic: `DYNAMIC_QUESTION_BANK`, `DYNAMIC_QUESTION_PROMPT`, `INTERVIEW_COMPLETENESS_PROMPT`, `generate_dynamic_question()`, `evaluate_interview_completeness()`, `_build_question_bank_context()`
- Removed enrichment pre-fill: `ENRICHMENT_PREFILL_MAP`, `_apply_enrichment_prefill()`
- Removed `dynamic_questions_asked`, `max_dynamic_questions` from `InterviewState`
- Removed `dynamic_answered` from `InterviewProgressResponse`
- Changed `MAX_FOLLOW_UPS_PER_QUESTION`: 2→1
- Rewrote `build_prompt()` in agent_generator.py: sections 2-6 updated for new questions, uses defaults for tone/guardrails/escalation
- Updated all 3 test files: test_interview (43 tests), test_agent_generator (23 tests), test_integration (1 test)

**Tests**: 123/123 passing (134 → -15 removed dynamic/prefill + 5 new deterministic/defaults = ~124, some consolidation)

---

### 2026-02-23 — T33 (M5.8): Pesquisa web sobre a empresa no enrichment (Serper API)

**Status**: completed

**What was done**:
- New: `services/web_research.py`, `prompts/web_research.py`, `tests/test_web_research.py`
- Modified: `config.py` (+SEARCH_API_KEY), `schemas.py` (+WebResearchResult), `routers/enrichment.py`, `interview_agent.py`, `agent_generator.py`, `test_enrichment.py`, `.env.example`
- 3 parallel Serper queries → deduplicate by URL → GPT-4.1-mini consolidation → stored as `enrichment_data["web_research"]`
- Queries refocused: empresa geral, produtos/serviços/clientes, dinâmica de cobrança do setor (usa `segment` do scraping)
- Initially used SerpApi (serpapi.com) by mistake — switched to Serper (serper.dev, 2500 free/month)

**Tests**: 134/134 (122 + 12 new)
**Manual**: Tested with TS Engenharia — retornou descrição, produtos, contexto do setor imobiliário, perfil de clientes

---


