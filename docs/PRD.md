# PRD: Self-Service Onboarding — CollectAI

## Document Info

| Field | Value |
|-------|-------|
| **Feature** | Self-service onboarding for CollectAI |
| **Owner** | Francisco (Co-founder) |
| **Status** | Active |
| **Created** | 2026-02-19 |
| **Updated** | 2026-02-20 |
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

### Backend API — COMPLETE (T01-T25)

| Component | Status | Details |
|-----------|--------|---------|
| **Enrichment** | Done | Website scraping (Playwright) + LLM extraction (GPT-4.1-mini) |
| **Wizard/Interview** | Done | 12 core questions + AI follow-ups (max 2/question) + dynamic questions (up to 8) + smart defaults |
| **Agent Generation** | Done | Context engineering prompt + structured output + sanity checks + adjustment endpoint |
| **Simulation** | Done | 2 simulated conversations (cooperative + resistant) from AgentConfig |
| **Audio Transcription** | Done | GPT-4o-mini-transcribe, supports 11 audio formats, Portuguese |
| **Integration Test** | Done | End-to-end test with real OpenAI API — 120/120 tests passing |

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
| Directus Integration | Future — save AgentConfig to platform's agent database |

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
[3] Sistema analisa o site (scraping + LLM) — mostra dados extraídos
         ↓
[4] Entrevista: 12 perguntas sobre o negócio — text/audio, com follow-ups da IA
         ↓
[5] Perguntas dinâmicas da IA (2-8 perguntas específicas para o negócio)
         ↓
[6] Confirmação de defaults (intervalo follow-up, max parcelas, estratégia desconto)
         ↓
[7] Sistema gera AgentConfig JSON (system prompt, policies, guardrails)
         ↓
[8] Sistema gera 2 conversas simuladas (cooperativo + resistente)
         ↓
[9] Usuário revisa e pode ajustar/regenerar
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

**Core concept**: AI-driven interview that collects everything needed to create a collection agent. Adaptive approach: 12 core questions → AI follow-ups → dynamic questions → smart defaults.

**Design principle**: ~5-8 minutes. AI achieves depth through smart follow-ups, not quantity.

#### Layer 1: Core Questions (12, mandatory)

| # | Question (Portuguese) | Type | Follow-up? |
|---|----------------------|------|------------|
| 1 | O que sua empresa vende ou oferece? | text | Yes (AI evaluates) |
| 2 | Como seus clientes normalmente pagam? | multiselect | No (unless "outro") |
| 3 | Quando você considera uma conta vencida? | select | No (unless "outro") |
| 4 | Descreva seu fluxo de cobrança atual | text | Yes (AI evaluates) |
| 5 | Qual tom o agente deve usar? | select | No (unless "depende") |
| 6 | Desconto para pagamento integral imediato? | select | No (unless "outro") |
| 7 | Parcelamento — máximo de parcelas? | select | No |
| 8 | Juros por atraso? | select | No (unless "outro") |
| 9 | Multa por atraso? | select | No (unless "outro") |
| 10 | Quando escalar para humano? | multiselect | No (unless "outro") |
| 11 | Coisas que o agente NUNCA deve fazer/dizer | text | Yes (AI evaluates) |
| 12 | Razões mais comuns para não pagar | text | Yes (AI evaluates) |

**Enrichment pre-fill**: core_1 (products), core_2 (payment methods), core_5 (tone) — pre-filled from website data when available.

**AI follow-ups**: Max 2 per question. Text questions are always evaluated. Select/multiselect only evaluated if answer contains "outro" or "depende".

#### Layer 2: AI-Driven Dynamic Questions (2-8, context-dependent)

After core questions, the AI generates targeted questions from 8 categories (business_model, debtor_profile, negotiation_depth, scenario_handling, legal_judicial, communication, segmentation, current_pain). Completeness evaluated after each: confidence >= 7/10 → stops.

#### Layer 3: Smart Defaults (confirm or adjust)

| Setting | Default |
|---------|---------|
| Follow-up interval | Every 3 days |
| Max contact attempts | 10 |
| Use debtor's first name | Yes |
| Identify as AI | Yes |
| Min installment value | R$50 |
| Discount strategy | Only when debtor resists |
| Payment link generation | Yes (PIX + Boleto) |
| Max discount for installments | 5% |

### FR-3: Audio Transcription — IMPLEMENTED

GPT-4o-mini-transcribe, supports 11 formats (webm, mp4, wav, mpeg, ogg, flac, m4a, etc.), max 25MB, Portuguese.

### FR-4: Agent Generation — IMPLEMENTED

Context engineering prompt with all data → GPT-4.1-mini structured output → AgentConfig JSON. Sanity checks auto-correct: discount caps, installment ranges, system prompt quality (>200 chars). Adjustment endpoint for targeted changes + LLM regeneration of text fields.

### FR-5: Simulation — IMPLEMENTED

Single LLM call generates 2 conversations (cooperative + resistant, 8-15 messages each). Agent follows exact config (tone, discounts, guardrails). Scenario responses validated against config constraints.

### FR-6: Frontend Onboarding — PENDING

**6 telas no Lovable** que guiam o usuário pelo fluxo completo:

| # | Tela | Função | API Backend |
|---|------|--------|-------------|
| 1 | **Boas-vindas** | Coleta nome, site, CNPJ (opcional) | `POST /sessions` |
| 2 | **Enriquecimento** | Loading + mostra dados extraídos | `POST /enrich` → `GET /enrichment` |
| 3 | **Entrevista (wizard)** | Pergunta por pergunta, barra de progresso, text/select/multiselect, follow-ups | `GET /interview/next` → `POST /interview/answer` (loop) |
| 4 | **Smart Defaults** | Mostra defaults, toggle/ajustar, confirmar | `GET /interview/defaults` → `POST /interview/defaults` |
| 5 | **Agente gerado** | System prompt, policies, guardrails, cenários. Opção de ajustar. | `POST /agent/generate` → `GET /agent` → `PUT /agent/adjust` |
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
| **Env vars** | `OPENAI_API_KEY`, `ALLOWED_ORIGINS` |
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
