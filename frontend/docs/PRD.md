# PRD: Frontend Onboarding — CollectAI

## 1. Context

CollectAI's self-service onboarding lets a client enter their website, answer structured questions (text or audio), and receive a complete onboarding report (SOP) for their collection agent.

The **backend API** is complete — it handles enrichment, interview, report generation, and simulation. The frontend is a set of 6 screens that guide the user through this flow.

**Trigger**: First login on `portal.financecrew.ai` — before the user can create their first collection agent, they must complete the onboarding wizard.

### Platform Architecture

```
+---------------------------------------------------------+
|              USUARIO (browser)                           |
|           portal.financecrew.ai                          |
+----------+----------------------+-----------------------+
           |                      |
           v                      v
+------------------+   +-------------------------+
|  Plataforma      |   |  Telas de Onboarding    |
|  (campanhas,     |   |  (wizard, agent,         |
|   conversas,     |   |   simulacao)             |
|   agents)        |   |                          |
+--------+---------+   +--------+----------------+
         |                      |
         v                      v
+------------------+   +-------------------------+
|    Directus       |   |  Backend Onboarding     |
|  (REST/GraphQL)   |   |  (FastAPI + SQLite)     |
|  users, campaigns |   |  scraping, LLM, agent   |
|  conversations    |   |  generation, simulation |
|  agents (storage) |   |                         |
+------------------+   +-----------+-------------+
                                   |
                                   v
                          +----------------+
                          |   OpenAI API   |
                          |  GPT-4.1-mini  |
                          +----------------+
```

---

## 2. Screens

### Screen 1: Boas-vindas

**Purpose**: Collect company info and create a session.

**Fields**:
- Nome da empresa (required)
- Website (required)
- CNPJ (optional)

**API call**: `POST /api/v1/sessions` → receives `session_id`

**UX**:
- Clean, welcoming layout
- Brief explanation of what the onboarding process involves (~3 sentences)
- "Comecar" button — creates session and navigates to Screen 2
- Persist `session_id` (localStorage or state) for all subsequent calls

---

### Screen 2: Enriquecimento

**Purpose**: Show loading while backend analyzes the company, then display the extracted profile.

**API calls**:
1. `POST /api/v1/sessions/{id}/enrich` — triggers scraping + web research (~15s)
2. `GET /api/v1/sessions/{id}/enrichment` — returns CompanyProfile + WebResearchResult

**UX**:
- Loading state with progress indicators (scraping website, researching company, extracting profile)
- After completion: display key extracted data (segment, products, target audience, communication tone)
- "Continuar" button to proceed to interview
- If enrichment fails partially: show what was found, allow user to continue anyway

---

### Screen 3: Entrevista (wizard)

**Purpose**: Guide user through 7 core questions with possible follow-ups.

**API calls** (loop):
1. `GET /api/v1/sessions/{id}/interview/next` — get first/next question
2. `POST /api/v1/sessions/{id}/interview/answer` — submit answer, receive next question
3. `GET /api/v1/sessions/{id}/interview/progress` — progress bar data

**Question rendering by type**:
- `text`: Text input (multiline) with optional audio button
- `select`: Radio buttons with label for each option
- `multiselect`: Checkboxes with label for each option

**Interview rules**:
- 7 core questions: core_0 (name, optional), core_1 (process), core_2-5 (4 yes/no policies), core_6 (escalation, optional)
- core_2-5 answered "sim" → automatic follow-up question (deterministic)
- core_1 → possible LLM-evaluated follow-up (max 1)
- core_0, core_6 → no follow-ups
- Navigation is forward-only (no going back to previous questions)

**UX**:
- Progress bar showing core_answered / total questions
- One question at a time (card-style)
- Audio recording button (microphone icon) on text questions
- `context_hint` displayed as helper text when present
- `is_required` determines if "Pular" (skip) button is shown
- Show follow-up questions inline after the parent question
- When `next_question` is null, navigate to Screen 4

---

### Screen 4: Revisao

**Purpose**: Show summary of all answers for user review before generating the report.

**API calls**:
1. `GET /api/v1/sessions/{id}/interview/review` — get summary
2. `POST /api/v1/sessions/{id}/interview/review` — confirm (with optional `additional_notes`)

**UX**:
- Display all Q&A pairs in a readable list
- Optional "Notas adicionais" text area
- "Confirmar e gerar relatorio" button
- Read-only — user cannot edit individual answers (forward-only flow)

---

### Screen 5: Relatorio SOP

**Purpose**: Display the generated onboarding report (expert analysis + policies).

**API calls**:
1. `POST /api/v1/sessions/{id}/agent/generate` — generate report (~15s)
2. `GET /api/v1/sessions/{id}/agent` — get OnboardingReport

**Display sections**:
- **Recomendacoes do Especialista** (`expert_recommendations`): 300+ word analysis — main highlight
- **Perfil de Cobranca** (`collection_profile`): debt type, debtor profile, objections, sector regulations
- **Politicas** (`collection_policies`): overdue, discount, installment, interest, penalty policies
- **Comunicacao** (`communication`): tone, prohibited actions, brand language
- **Guardrails** (`guardrails`): never do/say, identification, follow-up rules

**UX**:
- Loading state during generation (~15s)
- Structured display with collapsible sections
- "Continuar para simulacao" button

---

### Screen 6: Simulacao

**Purpose**: Show 2 simulated collection conversations as proof of agent quality.

**API calls**:
1. `POST /api/v1/sessions/{id}/simulation/generate` — generate simulations (~20s)
2. `GET /api/v1/sessions/{id}/simulation` — get SimulationResult

**Display**:
- Two tabs or side-by-side panels:
  - **Cooperativo**: debtor who wants to pay
  - **Resistente**: debtor who pushes back
- Each conversation as a chat interface (agent messages vs debtor messages)
- Show debtor profile above each conversation
- Show outcome and metrics below each conversation

**UX**:
- Loading state during generation (~20s)
- Chat-bubble style for messages
- "Aprovar" button to complete onboarding
- "Regenerar" button to generate new simulations (POST again)
- After approval: onboarding is complete, redirect to platform dashboard

---

## 3. UX Requirements (cross-cutting)

| Requirement | Details |
|-------------|---------|
| **Language** | All UI text in Portuguese (PT-BR) |
| **Progress indicator** | Visible during interview (Screen 3) |
| **Loading states** | Required for: enrichment (~15s), report generation (~15s), simulation (~20s) |
| **Audio support** | MediaRecorder API for voice answers on text questions |
| **Navigation** | Forward-only during interview. No browser back button handling needed for MVP. |
| **Responsive** | Mobile-friendly — many SMB owners use mobile |
| **Error handling** | Show user-friendly error messages. Never block flow completely — allow "skip" or "retry" |

---

## 4. Out of Scope

| Item | Reason |
|------|--------|
| Authentication | Platform (Directus) handles auth — onboarding screens are behind login |
| Payment/Billing | Separate feature |
| Agent avatar | Handled in platform (Directus), not during onboarding |
| Edit/redo answers | Forward-only for MVP |
| Directus integration | Future (M8) — save OnboardingReport to platform agent database |
