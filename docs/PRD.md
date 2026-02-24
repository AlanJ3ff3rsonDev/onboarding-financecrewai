# PRD: Self-Service Onboarding — CollectAI

## Document Info

| Field | Value |
|-------|-------|
| **Feature** | Self-service onboarding for CollectAI |
| **Owner** | Francisco (Co-founder) |
| **Status** | Active |
| **Created** | 2026-02-19 |
| **Updated** | 2026-02-23 |
| **Reference** | `pesquisa_onboarding_self_service_v2.md` |

---

## 1. Vision & Problem Statement

### The Problem

CollectAI's growth is bottlenecked by manual onboarding. Today, every new client goes through a 1-on-1 call with the founder where:
- Company info is collected (what they do, how they bill, collection policies)
- Agent configuration is manually crafted (prompt, tone, discount rules, guardrails)
- This limits acquisition to **5-10 calls per week**
- Founders work 1-2 hours/day (all have parallel jobs)

### The Vision

Build a **self-service onboarding system** where a client:
1. Enters their website/CNPJ
2. System automatically learns about their business (web scraping + LLM)
3. Answers structured questions about their collection SOP (text or voice)
4. AI asks smart follow-up questions to deepen understanding
5. System generates a complete, well-configured collection agent
6. Client sees a simulated collection conversation as proof of quality

**The key win**: If we can automatically generate a well-configured agent (with guardrails, negotiation policies, correct tone) just from a structured interview — that alone is a massive victory.

### Success Metrics

| Metric | Target |
|--------|--------|
| End-to-end onboarding time | < 20 minutes |
| Agent config quality | Comparable to manually-created agents |
| Enrichment + wizard completion rate | > 70% of started sessions |
| Francisco can validate it works | Runs locally on macOS |

---

## 2. Target User

**Primary**: Business owner or finance manager at a Brazilian SMB (5-200 employees) who:
- Has an existing debt collection problem
- Uses WhatsApp for business communication
- Is not deeply technical
- Values speed and simplicity
- May answer questions by speaking (audio) rather than typing

**Key constraint**: The user doesn't know technical collection terminology. Questions must use plain language with examples.

---

## 3. Project Status & Scope

### Backend API — Core Complete (T01-T28), Enhancements In Progress (T29-T34)

| Component | Status | Details |
|-----------|--------|---------|
| **Enrichment** | Done | Website scraping (Playwright) + LLM extraction (GPT-4.1-mini) |
| **Web Research** | Done (T33) | Serper API → 3 parallel queries → GPT consolidation → WebResearchResult |
| **Wizard/Interview** | Done (T32) | 10 core questions (mostly select/multiselect) + AI follow-ups + dynamic questions (up to 3) |
| **Agent Identity** | Done (T30) | Nome do agente (core_0). Avatar handled in platform (Directus). |
| **Agent Generation** | Done (replacing with SOP in T34) | Currently: AgentConfig + system_prompt. T34 replaces with OnboardingReport SOP. |
| **Simulation** | Done (adapting in T34) | 2 simulated conversations (cooperative + resistant). Will adapt to use SOP data. |
| **Audio Transcription** | Done | GPT-4o-mini-transcribe, supports 11 audio formats, Portuguese |
| **Integration Test** | Done | End-to-end test with real OpenAI API — 134 tests passing |

### Deploy — NEXT (M6)

| Component | Status | Details |
|-----------|--------|---------|
| **CORS** | Pending | Allow `portal.financecrew.ai` to call the API |
| **Containerization** | Pending | Dockerfile with Playwright/Chromium |
| **Cloud Deploy** | Pending | Railway or Render — public URL |

### Frontend Onboarding — NEXT (M7)

| Component | Status | Details |
|-----------|--------|---------|
| **6 telas de onboarding** | Pending | Lovable (React/TypeScript), integrado com backend API |
| **Integração com plataforma** | Pending | Trigger no primeiro login, antes de criar primeiro agent |

### Out of Scope (this initiative)

| Component | Reason |
|-----------|--------|
| Authentication | Existing platform (Directus) handles auth |
| Payment/Billing | Separate feature |
| Campaign Launch | Existing mechanism in platform |
| WhatsApp Integration | Existing system, agent config will be plugged into it |
| Directus Integration | Future — save OnboardingReport to platform's agent database |

---

## 4. Platform Architecture

```
┌─────────────────────────────────────────────────────┐
│              USUÁRIO (browser)                       │
│           portal.financecrew.ai                      │
└──────────┬──────────────────────┬───────────────────┘
           │                      │
           ▼                      ▼
┌──────────────────┐   ┌─────────────────────────┐
│  Plataforma      │   │  Telas de Onboarding    │
│  (campanhas,     │   │  (wizard, agent,         │
│   conversas,     │   │   simulação)             │
│   agents)        │   │                          │
└────────┬─────────┘   └────────┬────────────────┘
         │                      │
         ▼                      ▼
┌──────────────────┐   ┌─────────────────────────┐
│    Directus       │   │  Backend Onboarding     │
│  (REST/GraphQL)   │   │  (FastAPI + SQLite)     │
│  users, campaigns │   │  scraping, LLM, agent   │
│  conversations    │   │  generation, simulation │
│  agents (storage) │   │                         │
└──────────────────┘   └───────────┬─────────────┘
                                   │
                                   ▼
                          ┌────────────────┐
                          │   OpenAI API   │
                          │  GPT-4.1-mini  │
                          └────────────────┘
```

**Frontend**: Lovable (React/TypeScript) → `portal.financecrew.ai`
**Backend principal**: Directus — users, campaigns, conversations, agents
**Backend onboarding**: FastAPI — scraping, entrevista, geração de agente, simulação
**Trigger**: Primeiro login do cliente (até criar primeiro agent)

---

## 5. User Flow

```
[1] Primeiro login na plataforma
         ↓
[2] Tela de boas-vindas: nome, site, CNPJ (opcional)
         ↓
[3] Sistema analisa o site (scraping + LLM) + pesquisa web sobre a empresa
         ↓
[4] Entrevista: nome do agente + 9 perguntas sobre o negócio (maioria múltipla escolha), com follow-ups da IA
         ↓
[5] Perguntas dinâmicas da IA (até 3 perguntas específicas para o negócio)
         ↓
[6] Revisão: resumo das respostas + notas opcionais
         ↓
[7] Sistema gera Relatório SOP (análise de especialista, políticas, recomendações)
         ↓
[8] Sistema gera 2 conversas simuladas (cooperativo + resistente)
         ↓
[9] Usuário revisa e aprova
```

---

## 6. Functional Requirements

### FR-1: Enrichment — IMPLEMENTED

**Input**: Company name + website URL + CNPJ (stored as reference, not queried)

**Processing**:
- Scrape website with headless browser (Playwright, domcontentloaded + 3s wait)
- Extract structured data via LLM (GPT-4.1-mini, JSON mode)
- CNPJ is stored in the session for future use but NOT queried against any API

**Output**: CompanyProfile JSON (7 fields: company_name, segment, products_description, target_audience, communication_tone, payment_methods_mentioned, collection_relevant_context)

### FR-2: Wizard / Interview — IMPLEMENTED

**Core concept**: AI-driven interview that collects everything needed to create a collection agent. Adaptive approach: agent name → 9 core questions (mostly select/multiselect) → AI follow-ups → dynamic questions → review.

**Design principle**: ~5 minutes. Majority of questions are multiple choice for speed. AI achieves depth through smart follow-ups, not quantity. The agent is already an expert in debt collection — the interview captures only company-specific information. Detailed financial data (juros, multa, parcelamento, etc.) comes from a separate spreadsheet, not from the onboarding interview.

#### Layer 1: Core Questions (10, mandatory except core_0 and core_9)

| # | ID | Question (Portuguese) | Type | Follow-up? |
|---|-----|----------------------|------|------------|
| 1 | core_0 | Quer dar um nome ao seu agente de cobrança? | text (optional) | No |
| 2 | core_1 | O que sua empresa vende ou oferece? | text (pre-filled) | Yes (AI evaluates) |
| 3 | core_2 | Seus clientes são pessoa física, jurídica ou ambos? | select | No |
| 4 | core_3 | Como seus clientes normalmente pagam? | multiselect (pre-filled) | No (unless "outro") |
| 5 | core_4 | Qual tom o agente deve usar nas conversas? | select (pre-filled) | No (unless "depende") |
| 6 | core_5 | Como funciona o processo de cobrança hoje? | text | Yes (AI evaluates) |
| 7 | core_6 | O agente pode oferecer desconto ou condição especial? | select | No (unless "sim_com_regras") |
| 8 | core_7 | Quando o agente deve passar a cobrança para um humano? | multiselect | No (unless "outro") |
| 9 | core_8 | O que o agente NUNCA deve fazer ou dizer? | multiselect | No (unless "outro") |
| 10 | core_9 | Tem algo específico do seu negócio que o agente precisa saber? | text (optional) | Yes (AI evaluates) |

**Enrichment pre-fill**: core_1 (products), core_3 (payment methods), core_4 (tone) — pre-filled from website data + web research when available.

**AI follow-ups**: Max 2 per question. Text questions are always evaluated. Select/multiselect only evaluated if answer contains "outro", "depende", or "sim_com_regras". Follow-ups disabled in dynamic phase. Frustration detection skips follow-up automatically.

**Data split — onboarding vs planilha**: The onboarding interview captures company-specific operational context (how they work, what tone to use, what to never do). Detailed financial parameters (juros, multa, parcelamento, desconto %, limites) are provided via a separate spreadsheet that the client fills. This avoids overloading the conversational interview with numeric details.

#### Layer 2: AI-Driven Dynamic Questions (up to 3, context-dependent)

After core questions, the AI generates targeted questions from 4 categories (business_model, debtor_profile, negotiation_depth, brand_language). Completeness evaluated after each: confidence >= 7/10 → stops. No follow-ups on dynamic questions.

#### Layer 3: Review (confirm answers + optional notes)

User reviews a summary of all answers and can add additional notes before proceeding to agent generation. Guardrail defaults (follow_up_interval_days=3, max_attempts=10, must_identify_as_ai=true) are populated by the LLM during report generation.

### FR-3: Audio Transcription — IMPLEMENTED

GPT-4o-mini-transcribe, supports 11 formats (webm, mp4, wav, mpeg, ogg, flac, m4a, etc.), max 25MB, Portuguese.

### FR-4: Report/SOP Generation — REFACTORING (T34)

**Current**: Context engineering prompt → AgentConfig JSON with system_prompt.

**Planned (T34)**: Replace AgentConfig with `OnboardingReport` — a structured JSON SOP (Standard Operating Procedure) that:
- Describes the company, collection policies, tone, guardrails
- Includes `expert_recommendations`: 300+ word analysis from a collection expert on the ideal process for this company
- Includes `agent_identity`: name + avatar URL
- Includes `enrichment_summary`: combined website analysis + web research
- Is consumed by a downstream system to create the actual agent system_prompt

### FR-5: Simulation — IMPLEMENTED (adapting in T34)

Single LLM call generates 2 conversations (cooperative + resistant, 8-15 messages each). Will be adapted to use OnboardingReport data instead of AgentConfig.

### FR-8: Web Research — IMPLEMENTED (T33)

Serper API → 3 parallel queries (empresa geral, produtos/clientes, setor+cobrança) → deduplicate by URL → GPT-4.1-mini consolidation → WebResearchResult (company description, products/services, sector context, reputation summary, collection-relevant insights). Data feeds into enrichment pre-fills and the final SOP report. Graceful skip if no SEARCH_API_KEY.

### FR-9: Agent Personalization — IMPLEMENTED (T30)

The client can personalize their agent with:
- **Name** (T30): Optional question at the start of the interview (core_0). Examples: "Sofia", "Carlos".
- **Avatar**: Out of scope for onboarding. Avatar upload/selection will be handled directly in the platform (Directus).

### FR-6: Frontend Onboarding — PENDING

**6 telas no Lovable** que guiam o usuário pelo fluxo completo:

| # | Tela | Função | API Backend |
|---|------|--------|-------------|
| 1 | **Boas-vindas** | Coleta nome, site, CNPJ (opcional) | `POST /sessions` |
| 2 | **Enriquecimento** | Loading + mostra dados extraídos (site + pesquisa web) | `POST /enrich` → `GET /enrichment` |
| 3 | **Entrevista (wizard)** | Nome do agente + perguntas (maioria múltipla escolha), barra de progresso | `GET /interview/next` → `POST /interview/answer` (loop) |
| 4 | **Revisão** | Resumo das respostas + notas opcionais | `GET /interview/review` → `POST /interview/review` |
| 5 | **Relatório SOP** | Relatório de especialista, políticas, recomendações. | `POST /agent/generate` → `GET /agent` |
| 6 | **Simulação** | 2 conversas como chat (cooperativo + resistente). Aprovar ou regenerar. | `POST /simulation/generate` → `GET /simulation` |

**UX requirements**:
- Progress bar durante a entrevista
- Loading states durante chamadas de API (enrichment ~15s, generation ~15s, simulation ~20s)
- Todas as perguntas em português
- Support para respostas em áudio (microfone no browser)
- Navegação: só para frente (sem voltar para perguntas anteriores)
- Responsivo (mobile-friendly — muitos SMB owners usam celular)

### FR-7: Deploy — PENDING

Backend acessível via URL pública para o frontend chamar.

| Requisito | Detalhes |
|-----------|----------|
| **CORS** | Permitir `portal.financecrew.ai` + `localhost` (dev) |
| **Hosting** | Railway ou Render (Python + Playwright suportados) |
| **Env vars** | `OPENAI_API_KEY`, `SEARCH_API_KEY`, `ALLOWED_ORIGINS` |
| **Chromium** | Playwright Chromium instalado no container |
| **Database** | SQLite para MVP (PostgreSQL quando escalar) |

---

## 7. Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| **Backend runs locally** | macOS, `uv run uvicorn` |
| **Backend runs in cloud** | Railway/Render, URL pública |
| **Frontend** | Lovable (React/TS), integrado com plataforma existente |
| **Enrichment latency** | < 30 seconds |
| **Agent generation latency** | < 15 seconds |
| **Simulation generation latency** | < 20 seconds |
| **Audio transcription latency** | < 5 seconds for 2-min audio |
| **End-to-end onboarding time** | < 20 minutes |
| **Data persistence** | SQLite (MVP), PostgreSQL (production) |
| **API documentation** | Auto-generated OpenAPI/Swagger |
| **Error handling** | Graceful degradation (enrichment partial, LLM fallback) |
| **Language** | Code in English, all UI/agent output in Portuguese |

---

## 8. Open Questions

| # | Question | Impact | Decision |
|---|----------|--------|----------|
| 1 | ~~Should wizard questions be hardcoded or configurable?~~ | ~~Flexibility~~ | **Decided**: Hardcoded for MVP. 12 core questions defined. |
| 2 | ~~Should enrichment auto-detect website from CNPJ?~~ | ~~UX~~ | **Decided**: No. User provides website directly. |
| 3 | ~~Should simulation allow re-generation?~~ | ~~Satisfaction~~ | **Decided**: Yes. POST again overwrites previous. |
| 4 | ~~What LLM model?~~ | ~~Cost/quality~~ | **Decided**: GPT-4.1-mini for all calls. ~$0.10-0.30 per onboarding. |
| 5 | Where to save AgentConfig permanently? | Integration | **Pending**: Backend onboarding stores it. Directus integration later. |
| 6 | How does onboarding trigger in the platform? | UX | **Pending**: First login → redirect to onboarding. Discuss with team. |
| 7 | Audio recording in browser — which API? | Frontend | **Pending**: MediaRecorder API or third-party. Lovable decision. |
