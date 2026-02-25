# Technical Design: Frontend Onboarding

This document contains everything needed to build the frontend against the backend API.

---

## 1. API Endpoints

**Base URL**: `{BACKEND_URL}/api/v1`
- Production: TBD (after T37 deploy)
- Local dev: `http://localhost:8000/api/v1`

**CORS**: Already configured for `portal.financecrew.ai`, `localhost:3000`, `localhost:5173`

**Interactive docs**: Swagger UI at `{BACKEND_URL}/docs`

### Sessions

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| `POST` | `/sessions` | Create session | `{ "company_name": "str", "website": "str", "cnpj": "str (optional)" }` | `201 { "session_id": "uuid", "status": "created" }` |
| `GET` | `/sessions/{id}` | Get full session | — | Full session state JSON |

### Enrichment

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `POST` | `/sessions/{id}/enrich` | Trigger scraping + web research | `{ "status": "enriched", "enrichment_data": CompanyProfile }` |
| `GET` | `/sessions/{id}/enrichment` | Get enrichment results | CompanyProfile JSON |

**Note**: `POST /enrich` takes ~15 seconds. Show loading state.

### Interview

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| `GET` | `/sessions/{id}/interview/next` | Get next question | — | InterviewQuestion or `{ "phase": "str", "message": "str" }` |
| `POST` | `/sessions/{id}/interview/answer` | Submit answer | `{ "question_id": "str", "answer": "str", "source": "text\|audio" }` | AnswerResponse |
| `GET` | `/sessions/{id}/interview/progress` | Get progress | — | InterviewProgressResponse |
| `GET` | `/sessions/{id}/interview/review` | Get review summary | — | `{ "summary": {}, "confirmed": false }` |
| `POST` | `/sessions/{id}/interview/review` | Confirm review | `{ "additional_notes": "str (optional)" }` | `{ "confirmed": true, "phase": "complete" }` |

### Audio

| Method | Path | Description | Request | Response |
|--------|------|-------------|---------|----------|
| `POST` | `/sessions/{id}/audio/transcribe` | Transcribe audio | Multipart form-data, field `file` | `{ "text": "str", "duration_seconds": float }` |

### Agent (Report)

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `POST` | `/sessions/{id}/agent/generate` | Generate SOP report (~15s) | `{ "status": "generated", "onboarding_report": OnboardingReport }` |
| `GET` | `/sessions/{id}/agent` | Get report | OnboardingReport JSON |

### Simulation

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| `POST` | `/sessions/{id}/simulation/generate` | Generate 2 conversations (~20s) | `{ "status": "completed", "simulation_result": SimulationResult }` |
| `GET` | `/sessions/{id}/simulation` | Get results | SimulationResult JSON |

---

## 2. API Response Schemas

These are the exact JSON shapes returned by the API. Use these field names and types.

### InterviewQuestion

```json
{
  "question_id": "core_1",
  "question_text": "Como funciona o processo de cobranca na sua empresa hoje?",
  "question_type": "text | select | multiselect",
  "options": [
    { "value": "sim", "label": "Sim" },
    { "value": "nao", "label": "Nao" }
  ],
  "pre_filled_value": "string or null",
  "is_required": true,
  "supports_audio": true,
  "phase": "core | follow_up | review",
  "context_hint": "string or null"
}
```

**Notes**:
- `options` is `null` for `text` type, array of `{value, label}` for `select`/`multiselect`
- `pre_filled_value`: only set when enrichment data matches the question
- For `select`: answer = single `value` (e.g. `"sim"`)
- For `multiselect`: answer = comma-separated `value`s (e.g. `"pix,boleto,cartao_credito"`)
- For `text`: answer = free text string

### AnswerResponse (POST /interview/answer)

When `next_question` exists:
```json
{
  "received": true,
  "next_question": { /* InterviewQuestion */ },
  "follow_up": { /* InterviewQuestion, only if next is a follow-up */ }
}
```

When no next question (interview done):
```json
{
  "received": true,
  "next_question": null,
  "phase": "review",
  "message": "Entrevista concluida. Prossiga para revisao."
}
```

### InterviewProgressResponse

```json
{
  "phase": "not_started | core | review | complete",
  "total_answered": 7,
  "core_answered": 5,
  "core_total": 7,
  "estimated_remaining": 2,
  "is_complete": false
}
```

### CompanyProfile (from enrichment)

```json
{
  "company_name": "CollectAI",
  "segment": "Fintech / SaaS de cobranca",
  "products_description": "Plataforma de cobranca automatizada via WhatsApp",
  "target_audience": "PMEs brasileiras com problemas de inadimplencia",
  "communication_tone": "Profissional e empatico",
  "payment_methods_mentioned": "PIX, boleto, cartao de credito",
  "collection_relevant_context": "Foco em recuperacao amigavel antes de judicial"
}
```

### WebResearchResult (included in enrichment)

```json
{
  "company_description": "CollectAI e uma fintech de cobranca...",
  "products_and_services": "Plataforma SaaS de automacao de cobranca...",
  "sector_context": "Mercado de cobranca digital em crescimento...",
  "reputation_summary": "Avaliacoes positivas no Google, sem reclamacoes no Reclame Aqui...",
  "collection_relevant_insights": "Foco em recuperacao amigavel, sem cobranca judicial..."
}
```

### Interview Review

```json
{
  "summary": {
    "core_0": "Sofia",
    "core_1": "Processo de cobranca via WhatsApp...",
    "core_2": "sim",
    "core_3": "sim",
    "core_4": "nao",
    "core_5": "sim",
    "core_6": "Quando o cliente pede para falar com humano"
  },
  "confirmed": false
}
```

### OnboardingReport

```json
{
  "agent_identity": {
    "name": "Sofia"
  },
  "company": {
    "name": "CollectAI",
    "segment": "Fintech / SaaS de cobranca",
    "products": "Plataforma de cobranca automatizada via WhatsApp",
    "target_audience": "PMEs brasileiras",
    "website": "collectai.com.br"
  },
  "enrichment_summary": {
    "website_analysis": "Resumo do scraping do site...",
    "web_research": "Resumo da pesquisa web..."
  },
  "collection_profile": {
    "debt_type": "Recorrente (mensalidades SaaS)",
    "typical_debtor_profile": "PMEs com faturamento...",
    "business_specific_objections": "Servico nao foi entregue conforme...",
    "payment_verification_process": "Conferimos no ERP...",
    "sector_regulations": "LGPD limita exposicao de dados..."
  },
  "collection_policies": {
    "overdue_definition": "Ate 5 dias lembrete amigavel, 5-30 cobranca firme...",
    "discount_policy": "Ate 10% para pagamento a vista...",
    "installment_policy": "Parcelamos em ate 12x, minimo R$50...",
    "interest_policy": "Juros de 1% ao mes...",
    "penalty_policy": "Multa de 2% sobre o valor...",
    "payment_methods": ["pix", "boleto", "cartao_credito"],
    "escalation_triggers": ["solicita_humano", "acao_judicial", "agressivo"],
    "escalation_custom_rules": "Quando o cliente e empresa parceira...",
    "collection_flow_description": "Primeiro envio de lembrete por WhatsApp..."
  },
  "communication": {
    "tone_style": "friendly",
    "prohibited_actions": ["Ameacar", "Expor a divida a terceiros"],
    "brand_specific_language": "Usar 'parceiro' em vez de 'devedor'..."
  },
  "guardrails": {
    "never_do": ["Ameacar o devedor"],
    "never_say": ["processo", "cadeia"],
    "must_identify_as_ai": true,
    "follow_up_interval_days": 3,
    "max_attempts_before_stop": 10
  },
  "expert_recommendations": "Analise detalhada (300+ palavras) de um especialista em cobranca sobre o processo ideal para esta empresa...",
  "metadata": {
    "generated_at": "2026-02-22T10:30:00",
    "session_id": "uuid",
    "model": "gpt-4.1-mini",
    "version": 1
  }
}
```

### SimulationResult

```json
{
  "scenarios": [
    {
      "scenario_type": "cooperative | resistant",
      "debtor_profile": "Maria, 45 anos, dona de padaria, divida de R$1.200",
      "conversation": [
        { "role": "agent", "content": "Ola Maria! Aqui e a assistente..." },
        { "role": "debtor", "content": "Oi, tudo bem?" }
      ],
      "outcome": "Devedor aceitou parcelamento em 3x de R$400",
      "metrics": {
        "negotiated_discount_pct": 0,
        "final_installments": 3,
        "payment_method": "pix",
        "resolution": "full_payment | installment_plan | escalated | no_resolution"
      }
    }
  ],
  "metadata": {}
}
```

---

## 3. Interview Flow Rules

### Question Sequence

1. `core_0` — Agent name (text, optional, no follow-up)
2. `core_1` — Collection process (text, LLM-evaluated follow-up, max 1)
3. `core_2` — Juros por atraso (select sim/nao, follow-up on "sim")
4. `core_3` — Desconto pagamento (select sim/nao, follow-up on "sim")
5. `core_4` — Parcelamento (select sim/nao, follow-up on "sim")
6. `core_5` — Multa por atraso (select sim/nao, follow-up on "sim")
7. `core_6` — Escalacao humano (text, optional, no follow-up)

### Follow-up Logic

- **core_2 to core_5**: If user answers "sim", a deterministic follow-up is generated (no LLM call). If "nao", moves to next question.
- **core_1**: LLM evaluates the answer and may generate 1 follow-up question.
- **core_0, core_6**: No follow-ups ever.

### Phase Transitions

```
core → (all core questions answered) → review → (user confirms) → complete
```

No dynamic questions phase in current version.

### Frontend Handling

1. Call `GET /interview/next` to get the first question
2. Display the question based on `question_type`
3. User submits answer → `POST /interview/answer`
4. Response contains `next_question` — display it
5. If `next_question` is null → navigate to review screen
6. Check `phase` field: when `"review"`, interview is done

---

## 4. Audio Implementation

Voice input is an alternative to typing for text questions.

### Flow

1. User taps microphone icon on a text question
2. Browser `MediaRecorder API` starts recording (format: `webm`)
3. User taps stop → recording ends
4. Send audio: `POST /sessions/{id}/audio/transcribe` (multipart/form-data, field `file`)
5. Response: `{ "text": "transcricao em portugues", "duration_seconds": 12.5 }`
6. Display transcribed text in the input field (user can edit before submitting)
7. Submit with `source: "audio"` in the answer payload

### Accepted Formats

`webm`, `mp4`, `wav`, `mpeg`, `ogg`, `flac`, `m4a` — max 25MB

### Notes

- `MediaRecorder` default format is `webm` in most browsers — no need to configure
- Show recording indicator (red dot / timer) while recording
- Allow user to cancel recording before submitting
- Handle permission denial gracefully (show text-only input)

---

## 5. Frontend State Management

### What to Track

| State | Source | Persistence |
|-------|--------|-------------|
| `session_id` | `POST /sessions` response | localStorage (survives refresh) |
| `current_question` | API response (`next_question`) | Component state |
| `phase` | API response | Component state |
| `progress` | `GET /interview/progress` | Component state |
| `current_screen` | Navigation | URL or state (1-6) |

### What NOT to Track

- **Answers**: Backend persists all answers. No need to store locally.
- **Interview state**: Backend manages the full state machine.
- **Enrichment data**: Fetch from API when needed.

### Session Recovery

If the user refreshes or returns:
1. Check localStorage for `session_id`
2. `GET /sessions/{id}` to check `status`
3. Based on status, navigate to the appropriate screen:
   - `created` → Screen 1 or 2
   - `enriched` → Screen 3
   - `interviewing` → Screen 3 (call `GET /interview/next`)
   - `interviewed` → Screen 4
   - `generated` → Screen 5
   - `completed` → Screen 6

---

## 6. Screen Flow Diagram

```
Screen 1: Boas-vindas
  |
  | POST /sessions → session_id
  v
Screen 2: Enriquecimento
  |
  | POST /sessions/{id}/enrich (loading ~15s)
  | GET /sessions/{id}/enrichment
  v
Screen 3: Entrevista
  |
  | GET /sessions/{id}/interview/next
  | POST /sessions/{id}/interview/answer (loop)
  | GET /sessions/{id}/interview/progress (for progress bar)
  v
Screen 4: Revisao
  |
  | GET /sessions/{id}/interview/review
  | POST /sessions/{id}/interview/review (confirm)
  v
Screen 5: Relatorio SOP
  |
  | POST /sessions/{id}/agent/generate (loading ~15s)
  | GET /sessions/{id}/agent
  v
Screen 6: Simulacao
  |
  | POST /sessions/{id}/simulation/generate (loading ~20s)
  | GET /sessions/{id}/simulation
  |
  v
  [Complete — redirect to platform dashboard]
```

### API Call Timing

| Screen | API Call | Expected Latency |
|--------|----------|-------------------|
| 1 | POST /sessions | < 1s |
| 2 | POST /enrich | ~15s |
| 3 | GET /next, POST /answer | < 2s each |
| 4 | GET /review, POST /review | < 1s |
| 5 | POST /agent/generate | ~15s |
| 6 | POST /simulation/generate | ~20s |
