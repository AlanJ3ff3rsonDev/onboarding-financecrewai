# Tasks: Self-Service Onboarding

## How to Use This File

- Do one task at a time. Complete it, test it, log in `progress.md`, then move to the next.
- Status: `pending` → `in_progress` → `done`

> **Archive**: Detailed definitions for completed tasks (T01-T29) are in `docs/tasks_archive.md`.

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
| **M5.5** | Refatoracao Perguntas | T26-T28 | DONE |
| **M5.6** | Refinamento de Perguntas | T29 | DONE |
| **M5.7** | Personalizacao do Agente + Reestruturacao Perguntas | T30-T32 | DONE |
| **M5.8** | Enriquecimento Avancado (Pesquisa Web) | T33 | DONE |
| **M5.9** | Relatorio SOP (substituir AgentConfig) | T34 | Pending |
| **M6** | Deploy | T35-T37 | Pending |
| **M7** | Frontend Onboarding (Lovable) | T38-T44 | Pending |
| **M8** | Integracao Directus | T45 | Future |

---

## Completed Tasks (Summary)

| ID | Task | Milestone | Status |
|----|------|-----------|--------|
| T01 | Initialize project structure | M0 | `done` |
| T02 | FastAPI app with health endpoint | M0 | `done` |
| T03 | Database setup + session model | M0 | `done` |
| T04 | Session API endpoints | M0 | `done` |
| T05 | Website scraping service | M1 | `done` |
| T06 | LLM extraction service | M1 | `done` |
| T07 | Enrichment API endpoint | M1 | `done` |
| T08 | Core questions data structure | M2 | `done` |
| T09 | LangGraph interview state + basic graph | M2 | `done` |
| T10 | Interview "next question" endpoint | M2 | `done` |
| T11 | Interview "submit answer" endpoint | M2 | `done` |
| T12 | AI follow-up evaluation + generation | M2 | `done` |
| T13 | Dynamic question generation | M2 | `done` |
| T14 | Interview progress endpoint + completion | M2 | `done` |
| T15 | Smart defaults confirmation endpoint | M2 | `done` |
| T16 | Audio transcription service | M2 | `done` |
| T17 | Audio upload endpoint | M2 | `done` |
| T18 | AgentConfig Pydantic schema | M3 | `done` |
| T19 | Agent generation prompt | M3 | `done` |
| T20 | Agent generation service + sanity checks | M3 | `done` |
| T21 | Agent generation endpoint | M3 | `done` |
| T22 | Agent adjustment endpoint | M3 | `done` |
| T23 | Simulation prompt + service | M4 | `done` |
| T24 | Simulation endpoint | M4 | `done` |
| T25 | End-to-end integration test | M5 | `done` |
| T26 | Refatorar perguntas core + follow-up | M5.5 | `done` |
| T27 | Refatorar perguntas dinamicas | M5.5 | `done` |
| T28 | Atualizar prompt de geracao | M5.5 | `done` |
| T29 | core_3 texto aberto + core_10_open | M5.6 | `done` |
| T30 | Pergunta de nome do agente (core_0) | M5.7 | `done` |
| T31 | ~~Upload de foto do agente~~ | M5.7 | `out_of_scope` |
| T32 | Remover avatar + reestruturar perguntas core (16→10) | M5.7 | `done` |

---

## Active & Pending Tasks

### T32: Remover avatar + reestruturar perguntas core (16→10) (M5.7)

**Objective**: Remover toda a funcionalidade de avatar do codigo e redesenhar as perguntas core de 16 para 10 (maioria multipla escolha). Dados financeiros detalhados (juros, multa, parcelamento) saem do onboarding — virao via planilha separada.

**Dependencies**: T30, T31

**Files to modify**:
- `backend/app/routers/agent.py` — remover endpoints de avatar (upload, generate, select)
- `backend/app/models/orm.py` — remover coluna `agent_avatar_path`
- `backend/app/models/schemas.py` — remover `agent_avatar_path` de `SessionResponse`
- `backend/app/main.py` — remover StaticFiles mount `/uploads`
- `backend/app/config.py` — remover `GOOGLE_API_KEY`
- `backend/app/prompts/interview.py` — redesenhar `CORE_QUESTIONS` (10 perguntas), atualizar `ENRICHMENT_PREFILL_MAP`, atualizar `DYNAMIC_QUESTION_BANK`
- `backend/app/services/interview_agent.py` — ajustar para novos IDs
- `backend/app/prompts/agent_generator.py` — atualizar `build_prompt()` para novos IDs
- `backend/tests/test_avatar.py` — deletar
- `backend/tests/test_interview.py` — atualizar para 10 perguntas
- `backend/tests/test_integration.py` — atualizar para 10 perguntas
- `backend/tests/test_agent_generator.py` — atualizar para novos IDs

**Files to delete**:
- `backend/tests/test_avatar.py`
- `backend/app/uploads/` (diretorio inteiro)

**Changes**:

1. **Remover avatar**:
   - Endpoints: `POST .../avatar/upload`, `POST .../avatar/generate`, `POST .../avatar/select`
   - ORM: coluna `agent_avatar_path`
   - Schema: campo `agent_avatar_path` em `SessionResponse`
   - Main: `StaticFiles` mount de `/uploads`
   - Config: `GOOGLE_API_KEY`
   - .env.example: `GOOGLE_API_KEY`

2. **Redesenhar CORE_QUESTIONS** (10 perguntas):

| # | ID | Pergunta | Tipo |
|---|-----|----------|------|
| 1 | core_0 | Quer dar um nome ao seu agente de cobranca? | text (opcional) |
| 2 | core_1 | O que sua empresa vende ou oferece? | text (pre-filled) |
| 3 | core_2 | Seus clientes sao pessoa fisica, juridica ou ambos? | select |
| 4 | core_3 | Como seus clientes normalmente pagam? | multiselect (pre-filled) |
| 5 | core_4 | Qual tom o agente deve usar nas conversas? | select (pre-filled) |
| 6 | core_5 | Como funciona o processo de cobranca hoje? | text |
| 7 | core_6 | O agente pode oferecer desconto ou condicao especial? | select |
| 8 | core_7 | Quando o agente deve passar a cobranca para um humano? | multiselect |
| 9 | core_8 | O que o agente NUNCA deve fazer ou dizer? | multiselect |
| 10 | core_9 | Tem algo especifico do seu negocio que o agente precisa saber? | text (opcional) |

3. **Atualizar ENRICHMENT_PREFILL_MAP**: core_1 (products), core_3 (payment methods), core_4 (tone)

4. **Atualizar DYNAMIC_QUESTION_BANK**: remover categorias que agora sao cobertas pelas novas perguntas core. Manter: business_model, debtor_profile, negotiation_depth, brand_language.

5. **Atualizar build_prompt()** em agent_generator.py para mapear novos IDs de perguntas.

6. **Atualizar testes**: test_interview.py, test_integration.py, test_agent_generator.py para 10 perguntas.

**Automated tests**:
- test_core_questions_count: 10 perguntas
- test_core_0_is_optional: core_0 e core_9 sao opcionais
- test_enrichment_prefill_core_1: products pre-filled
- test_enrichment_prefill_core_3: payment methods pre-filled
- test_enrichment_prefill_core_4: tone pre-filled
- test_select_questions_have_options: core_2, core_4, core_6 sao select
- test_multiselect_questions_have_options: core_3, core_7, core_8 sao multiselect
- test_full_interview_flow: 10 core → dynamic → review
- All existing tests updated and passing

**Definition of Done**:
- Avatar completamente removido (endpoints, ORM, schema, files, tests)
- 10 core questions funcionando (select/multiselect com opcoes)
- Enrichment pre-fill funciona para core_1, core_3, core_4
- build_prompt() gera prompt correto com novos IDs
- Dynamic questions atualizadas
- Todos os testes passam (exceto test_avatar.py que foi deletado)
- Integration test passa com 10 perguntas

**Status**: `done`

---

### T33: Pesquisa web sobre a empresa no enrichment (M5.8)

**Objective**: Alem do scraping do site, fazer buscas na web sobre a empresa (Serper API) para enriquecer o contexto. Resultados alimentam pre-fills e o relatorio SOP.

**Dependencies**: T32

**Status**: `done`

---

### T34: Substituir AgentConfig por Relatorio SOP estruturado (M5.9)

**Objective**: Substituir AgentConfig/system_prompt por um relatorio SOP (Standard Operating Procedure) em JSON. OnboardingReport com: agent_identity, company, collection_policies, communication, guardrails, expert_recommendations (300+ words).

**Dependencies**: T32, T33

**Status**: `pending` — detalhar antes de implementar

---

### T35: CORS configuration (M6)

**Dependencies**: T34

**Definition of Done**:
- CORSMiddleware in app/main.py
- Allowed origins: portal.financecrew.ai, localhost:* (via ALLOWED_ORIGINS env var)

**Status**: `pending`

---

### T36: Dockerfile + Railway config (M6)

**Dependencies**: T35

**Definition of Done**:
- Dockerfile with Python 3.13 + Playwright dependencies
- docker build + docker run work locally

**Status**: `pending`

---

### T37: Deploy to Railway + verify (M6)

**Dependencies**: T36

**Definition of Done**:
- Backend accessible via public URL
- GET /health works, POST /sessions works
- OPENAI_API_KEY configured as env var

**Status**: `pending`

---

## M7: Frontend Onboarding (Lovable) — T38-T44

> Lovable prompts for each screen are in `docs/tasks_archive.md` (to be moved here when M7 starts).

| ID | Task | Dependencies | Status |
|----|------|-------------|--------|
| T38 | Tela de boas-vindas | T37 | `pending` |
| T39 | Tela de enriquecimento | T38 | `pending` |
| T40 | Tela de entrevista (wizard) | T39 | `pending` |
| T41 | Tela de revisao da entrevista | T40 | `pending` |
| T42 | Tela do relatorio SOP | T41 | `pending` |
| T43 | Tela de simulacao | T42 | `pending` |
| T44 | Integracao de fluxo completo | T43 | `pending` |

---

## M8: Integracao Directus (Future) — T45

### T45: Salvar OnboardingReport no Directus

**Dependencies**: T44

**Definition of Done**:
- OnboardingReport mapped to Directus "agents" collection
- Agent appears in platform agents screen

**Status**: `pending`
