# Tasks: Frontend Onboarding

## How to Use This File

- Do one task at a time. Complete it, test it, log in `progress.md`, then move to the next.
- Status: `pending` → `in_progress` → `done`

---

## Milestone Overview

| Milestone | Description | Tasks | Status |
|-----------|-------------|-------|--------|
| **M7** | Frontend Onboarding (Lovable) | T38-T44 | Pending |
| **M8** | Integracao Directus | T45 | Future |

---

## Active & Pending Tasks

### T37.5: Setup + Infraestrutura do Onboarding (M7)

**Dependencies**: T37 (backend deploy) — DONE

**Definition of Done**:
- Branch `feat/onboarding` criada no repo `crew-ai-dashboard`
- Env vars adicionadas: `VITE_ONBOARDING_API_URL`, `VITE_ONBOARDING_API_KEY`
- Feature flag `"onboarding"` adicionada ao FeatureFlagContext (default: false)
- `hideLayout` pattern estendido no App.tsx para rotas `/onboarding`
- API client criado (`src/features/onboarding/api/client.ts`) com X-API-Key header
- TypeScript types criados (`src/features/onboarding/api/types.ts`) espelhando schemas do backend
- API function files criados (sessions, enrichment, interview, audio, agent, simulation)
- OnboardingContext criado com session recovery logic
- OnboardingLayout + StepIndicator criados
- Rotas `/onboarding/*` adicionadas ao App.tsx (condicionais ao feature flag)
- Chaves i18n base adicionadas ao `pt-BR.json`
- Feature flag OFF = plataforma funciona exatamente como antes

**Status**: `done`

---

### T38: Tela de boas-vindas (M7)

**Dependencies**: T37.5

**Definition of Done**:
- Screen with fields: company name (required), website (required), CNPJ (optional)
- Calls `POST /api/v1/sessions` on submit
- Stores `session_id` in localStorage
- Navigates to enrichment screen on success
- All text in Portuguese

**Status**: `done`

---

### T39: Tela de enriquecimento (M7)

**Dependencies**: T37.5, T38

**Definition of Done**:
- Calls `POST /sessions/{id}/enrich` on mount
- Animated loading screen (~15s): cycling icons (Globe→Search→FileText→Sparkles), spinning dashed ring, ping radar, step dots, gradient progress bar
- Handles 409 Conflict (already enriched) → falls back to GET
- Handles session recovery: polls `GET /sessions/{id}` until enriched
- StrictMode double-mount guard with `useRef`
- Auto-navigates to `/onboarding/interview` when enrichment completes (no results screen)
- Error phase with retry button
- Removed `type="url"` from welcome screen website input (was blocking valid URLs)

**Status**: `done`

---

### T40: Tela de entrevista — wizard (M7)

**Dependencies**: T39

**Definition of Done**:
- Renders questions by type: text input, select (radio), multiselect (checkboxes)
- Progress bar showing answered / total
- Audio recording button on text questions (MediaRecorder API)
- Handles follow-up questions inline
- Forward-only navigation (no back button)
- Shows `context_hint` as helper text
- Skippable questions when `is_required` is false
- Navigates to review when `next_question` is null

**Status**: `pending`

---

### T41: Tela de revisao da entrevista (M7)

**Dependencies**: T40

**Definition of Done**:
- Calls `GET /sessions/{id}/interview/review` on mount
- Displays all Q&A pairs in readable format
- Optional "Notas adicionais" text area
- "Confirmar e gerar relatorio" button calls `POST /interview/review`
- Navigates to report screen after confirmation

**Status**: `pending`

---

### T42: Tela do relatorio SOP (M7)

**Dependencies**: T41

**Definition of Done**:
- Calls `POST /sessions/{id}/agent/generate` on mount (~15s loading)
- Displays OnboardingReport sections: expert_recommendations, collection_profile, collection_policies, communication, guardrails
- Structured layout with collapsible or tabbed sections
- "Continuar para simulacao" button

**Status**: `pending`

---

### T43: Tela de simulacao (M7)

**Dependencies**: T42

**Definition of Done**:
- Calls `POST /sessions/{id}/simulation/generate` on mount (~20s loading)
- Displays 2 conversations (cooperative + resistant) as chat bubbles
- Shows debtor profile above each conversation
- Shows outcome and metrics below
- "Aprovar" button completes onboarding
- "Regenerar" button triggers new simulation
- After approval: redirect to platform dashboard

**Status**: `pending`

---

### T44: Integracao de fluxo completo (M7)

**Dependencies**: T43

**Definition of Done**:
- All 6 screens connected end-to-end
- Session recovery works (refresh/return to correct screen based on status)
- Error handling on all API calls (user-friendly messages, retry options)
- Loading states on all slow operations
- Mobile responsive
- Tested with a real backend session (not mocked)
- Restore `ProtectedRoute` on all `/onboarding` routes (requires Directus login)
- Add redirect logic: after login, if user has not completed onboarding → force redirect to `/onboarding`
- After onboarding complete → redirect to dashboard

**Status**: `pending`

---

## M8: Integracao Directus (Future) — T45

### T45: Salvar OnboardingReport no Directus

**Dependencies**: T44

**Definition of Done**:
- OnboardingReport mapped to Directus "agents" collection
- Agent appears in platform agents screen after onboarding completion

**Status**: `pending`

> **Note**: M8 will be defined in detail when M7 is complete.
