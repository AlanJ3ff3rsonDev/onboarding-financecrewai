# PRD: Self-Service Onboarding — Backend MVP

## Document Info

| Field | Value |
|-------|-------|
| **Feature** | Self-service onboarding for CollectAI |
| **Owner** | Francisco (Co-founder) |
| **Status** | Draft |
| **Created** | 2026-02-19 |
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

## 3. MVP Scope

### In Scope

| Component | Description |
|-----------|-------------|
| **Enrichment** | Website scraping + LLM extraction → understand the business automatically |
| **Wizard/Interview** | Structured SOP questions + free text + audio + AI follow-ups |
| **Agent Generation** | Generate complete agent config JSON from interview data |
| **Simulation** | Generate 2 simulated collection conversations based on the agent config |
| **Audio Transcription** | Accept audio uploads, transcribe via Whisper, return text |

### Out of Scope (for this MVP)

| Component | Reason |
|-----------|--------|
| Authentication | Existing platform handles auth |
| Payment/Billing | Separate feature, will be built later |
| Campaign Launch | Existing mechanism in platform, will be coupled later |
| Frontend (Lovable) | Will be built separately after backend is validated |
| WhatsApp Integration | Existing system, agent config will be plugged into it |
| Production Infrastructure | Dev team takes over if MVP validates |

---

## 4. User Flow (MVP)

```
[1] Enter website URL + CNPJ
         ↓
[2] System enriches (scraping + CNPJ) — shows what it learned
         ↓
[3] User confirms/corrects enriched data
         ↓
[4] Select agent type (compliant vs non-compliant)
         ↓
[5] Wizard: Business questions (SOP) — text or audio, AI deepens
         ↓
[6] Wizard: Agent configuration questions — policies, tone, rules
         ↓
[7] System generates agent config JSON
         ↓
[8] System generates 2 simulated conversations
         ↓
[9] User reviews simulation and can request adjustments
```

---

## 5. Functional Requirements

### FR-1: Enrichment

**Input**: Company name + website URL + CNPJ (stored as reference, not queried)

**Processing**:
- Scrape website with headless browser (Playwright)
- Extract structured data via LLM: what the company does, products/services, target audience, communication tone, payment methods mentioned
- CNPJ is stored in the session for future use (platform integration) but NOT queried against any API

**Output**: CompanyProfile JSON containing:
- Company name (as provided by user)
- Segment/industry (extracted from website)
- What they sell (products/services description)
- Target audience (B2B, B2C, both)
- Communication tone detected from website
- Payment methods mentioned on site
- Any collection-relevant context found

**Requirements**:
- Must complete in < 30 seconds
- If website scraping fails, return empty profile — user fills info manually in interview
- No external API costs (no CNPJ lookup APIs)

### FR-2: Wizard / Interview

**Core concept**: An AI-driven interview that collects everything needed to create a collection agent. The approach is **adaptive, not exhaustive**: a small set of core questions everyone answers, then the AI decides which follow-ups are relevant for THAT specific business.

**Design principle**: The interview should take **5-8 minutes**, not 15-20. The AI achieves depth through smart follow-ups, not through quantity of fixed questions. Many configuration values have sensible defaults that the user just confirms.

All questions support **text input + audio upload**. Each question with options also has a free-text "Other" option.

#### Layer 1: Core Questions (8-10, mandatory for everyone)

These are the absolute minimum to generate a decent agent. Every client answers these.

| # | Question | Type | Options | Why it's core |
|---|----------|------|---------|---------------|
| 1 | What does your company sell or provide? | text/audio | (pre-filled from enrichment, user confirms/edits) | Defines the context for the entire agent |
| 2 | How do your customers typically pay? | multiselect | PIX, Boleto, Credit card, Bank transfer, Cash, Other | Determines what payment options the agent can offer |
| 3 | When do you consider an account past-due? | select + text | D+0, D+1, D+5, D+15, D+30, Other | Defines when the agent should start acting |
| 4 | Describe your current collection flow — from first delay to resolution | text/audio | (open-ended) | The single most important SOP question — captures the entire process |
| 5 | What tone should the agent use? | select + text | Formal, Friendly but firm, Empathetic, Direct/assertive, Depends (explain) | Sets the entire communication style |
| 6 | Max discount for immediate full payment? | slider | 0% to 50% (default: 10%) | Critical guardrail — agent can't exceed this |
| 7 | Max number of installments? | select | 2x, 3x, 4x, 6x, 10x, 12x, 18x, 24x | Critical guardrail |
| 8 | When should the agent escalate to a human? | multiselect + text | Debtor requests human, Debt above X value, Lawsuit mentioned, After N failed attempts, Debtor aggressive, Fraud/unrecognized debt, Other | Safety guardrail |
| 9 | Things the agent should NEVER do or say | text/audio | (open-ended) | Critical guardrail — what to absolutely avoid |
| 10 | What are the most common reasons debtors give for not paying? | text/audio | (open-ended) | Prepares the agent for real scenarios |

#### Layer 2: AI-Driven Dynamic Questions (variable, context-dependent)

After the core questions, the **Interview Agent** (LLM) analyzes:
- The core answers
- The enrichment data (what the website says about the business)
- What's MISSING that would significantly improve agent quality

Then it generates **3-8 additional targeted questions**, specific to that business. The AI picks from a question bank AND can create new questions on the fly.

**Question bank the AI draws from** (not all will be asked — AI picks the relevant ones):

| Category | Example Questions | Trigger (when AI asks this) |
|----------|-------------------|---------------------------|
| **Business model** | "Is billing recurring or one-time?", "What's the typical ticket value?" | Always useful, but AI skips if enrichment already answered |
| **Debtor profile** | "Are debtors individuals or companies?", "Is there an ongoing relationship (churn risk)?" | If not clear from core answers |
| **Negotiation depth** | "Should discounts be proactive or only when resisted?", "Max discount for installments?" | If user indicated flexible discount policy |
| **Scenario handling** | "How should the agent handle 'I already paid'?", "How to handle 'I don't recognize this debt'?" | AI picks the 2-3 most relevant scenarios for the segment |
| **Legal/judicial** | "Do you have a legal collection process for larger debts?", "Above what value?" | If high-value debts or user mentioned legal |
| **Communication** | "How should the agent open the conversation?", "Words to avoid?" | If user chose nuanced tone or has brand-specific language |
| **Segmentation** | "Do you segment by debt amount or aging?", "Different rules for different segments?" | If user has diverse debt portfolio |
| **Current pain** | "What frustrates you most about your current collection process?", "What would success look like?" | To capture intent and expectations |

**AI follow-up deepening** (within any question):
- Short answer → "Can you tell me more? The more detail, the better your agent will perform."
- Ambiguous answer → "Can you give me a specific example? For a R$5,000 debt that's 30 days late, what would you do?"
- Domain-specific triggers → "You mentioned construction financing — do debtors have property as collateral? Does that change how you collect?"

#### Layer 3: Smart Defaults (confirm or adjust)

These values have sensible defaults based on Brazilian collection regulations and best practices. They're shown as a **confirmation screen** after the interview — user just reviews and tweaks if needed.

| Setting | Default | Basis |
|---------|---------|-------|
| Contact hours (weekdays) | 08:00-20:00 | CDC legal requirement |
| Contact hours (Saturday) | 08:00-14:00 | Industry standard |
| Contact on Sundays | No | CDC recommendation |
| Follow-up interval | Every 3 days | Industry best practice |
| Max contact attempts | 10 | Reasonable before pause |
| Use debtor's first name | Yes | Higher engagement |
| Identify as AI | Yes | PL 2338/2023 compliance |
| Min installment value | R$50 | Practical minimum |
| Discount strategy | Only when debtor resists | Better margins |
| Payment link generation | Yes (PIX + Boleto) | Standard in Brazil |
| Max discount for installments | 5% | Conservative default |

**Total interview time**: ~5-8 minutes (10 core + 3-8 dynamic + 30s default review)

### FR-3: Audio Transcription

**Input**: Audio file (webm, mp4, wav, mpeg) up to 25MB

**Processing**: Send to OpenAI Whisper API (or GPT-4o-mini Transcribe for cost savings)

**Output**: Transcribed text in the original language (Portuguese)

**Requirements**:
- Transcription < 5 seconds for typical answers (30s-2min audio)
- Return text to be used as the answer to the wizard question
- Support Portuguese (primary) and English

### FR-4: Agent Generation

**Input**: CompanyProfile (from enrichment) + all wizard responses (structured + free text)

**Processing**:
- Combine all context using context engineering principles
- Send to LLM with structured output schema
- Validate output against schema (Pydantic)
- Apply sanity checks (discounts within limits, valid hours, etc.)

**Output**: AgentConfig JSON containing:

```
{
  "agent_type": "compliant" | "non_compliant",
  "company_context": {
    "name": "...",
    "segment": "...",
    "products": "...",
    "target_audience": "..."
  },
  "system_prompt": "Complete, detailed system prompt for the collection agent...",
  "tone": {
    "style": "formal" | "friendly" | "empathetic" | "assertive",
    "use_first_name": true | false,
    "prohibited_words": [...],
    "preferred_words": [...],
    "opening_message_template": "..."
  },
  "negotiation_policies": {
    "max_discount_full_payment_pct": 15,
    "max_discount_installment_pct": 5,
    "max_installments": 12,
    "min_installment_value_brl": 50,
    "discount_strategy": "only_when_resisted" | "proactive" | "escalating",
    "payment_methods": ["pix", "boleto", "credit_card"],
    "can_generate_payment_link": true
  },
  "guardrails": {
    "never_do": [...],
    "never_say": [...],
    "escalation_triggers": [...],
    "contact_hours": { "weekday": "08:00-20:00", "saturday": "08:00-14:00", "sunday": null },
    "follow_up_interval_days": 3,
    "max_attempts_before_stop": 10,
    "must_identify_as_ai": true
  },
  "scenario_responses": {
    "already_paid": "...",
    "dont_recognize_debt": "...",
    "cant_pay_now": "...",
    "aggressive_debtor": "..."
  },
  "tools": [
    "send_whatsapp_message",
    "generate_pix_payment_link",
    "generate_boleto",
    "check_payment_status",
    "escalate_to_human",
    "schedule_follow_up"
  ],
  "metadata": {
    "version": 1,
    "generated_at": "2026-02-19T...",
    "onboarding_session_id": "...",
    "generation_model": "gpt-4.1-mini"
  }
}
```

**Requirements**:
- Generation < 15 seconds
- Output must pass schema validation
- Sanity check: discount percentages within slider range, hours within legal limits (08-20 weekdays)
- Store with versioning (user can adjust and re-generate)

### FR-5: Simulation

**Input**: AgentConfig JSON (from agent generation)

**Processing**:
- Single LLM call with a prompt that generates 2 complete simulated collection conversations
- Scenario 1: Cooperative debtor (wants to pay, needs conditions)
- Scenario 2: Resistant debtor (contests, demands big discount, needs convincing)
- Each conversation: 8-15 messages back and forth
- Conversations must reflect the specific agent config (tone, discounts, policies, guardrails)

**Output**: SimulationResult JSON containing:

```
{
  "scenarios": [
    {
      "id": 1,
      "name": "Cooperative Debtor",
      "description": "Debtor who wants to pay but needs payment conditions",
      "conversation": [
        { "role": "agent", "message": "..." },
        { "role": "debtor", "message": "..." },
        ...
      ],
      "outcome": "agreement_reached",
      "discount_offered_pct": 10,
      "payment_method": "pix",
      "installments": 1,
      "conversation_duration_minutes": 6
    },
    {
      "id": 2,
      "name": "Resistant Debtor",
      ...
    }
  ],
  "metadata": {
    "generated_at": "...",
    "model": "gpt-4.1-mini",
    "agent_config_version": 1
  }
}
```

**Requirements**:
- Generation < 20 seconds (single LLM call for both scenarios)
- Conversations must feel realistic (not robotic)
- Agent messages must follow the configured tone and policies
- If agent config says max 10% discount, simulation shouldn't show 20%
- Portuguese language

---

## 6. Non-Functional Requirements

| Requirement | Target |
|------------|--------|
| **Runs locally** | macOS, no Docker required, minimal setup |
| **Enrichment latency** | < 30 seconds |
| **Agent generation latency** | < 15 seconds |
| **Simulation generation latency** | < 20 seconds |
| **Audio transcription latency** | < 5 seconds for 2-min audio |
| **Data persistence** | SQLite (local), easily swappable to PostgreSQL |
| **API documentation** | Auto-generated OpenAPI/Swagger |
| **Error handling** | Graceful degradation (enrichment partial, LLM fallback) |
| **Language** | Code in English, agent output in Portuguese |

---

## 7. Out of Scope Details

| What | Why |
|------|-----|
| User registration/login | Platform already has auth. MVP tested via API directly |
| Stripe/payment integration | Separate feature, built later by dev team |
| Campaign creation/launch | Existing mechanism in platform |
| WhatsApp message sending | Existing system, agent config plugs into it |
| Frontend UI | Built separately with Lovable after backend validates |
| Multi-tenant isolation | MVP is single-user validation |
| Rate limiting | Not needed for local validation |
| Logging/monitoring | Not needed for MVP |
| Agent deployment to production | Dev team handles after validation |

---

## 8. Open Questions

| # | Question | Impact | Decision |
|---|----------|--------|----------|
| 1 | Should the wizard questions be hardcoded or configurable? | Flexibility vs simplicity | Start hardcoded, make configurable later |
| 2 | Should enrichment auto-detect the website from CNPJ? | UX convenience | Nice-to-have, not MVP |
| 3 | Should the simulation allow re-generation with adjustments? | User satisfaction | Yes, but limit to 2 re-generations in MVP |
| 4 | What LLM model for generation and simulation? | Cost vs quality | GPT-4.1-mini (good balance). Can test with 4o for quality comparison |
