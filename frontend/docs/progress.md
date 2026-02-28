# Progress Log: Frontend Onboarding

## How to Use This File

Log every task here. Entry format: date, task ID, status, what was done, tests, issues, next steps.

---

## Decisions Log

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| 2026-02-27 | Onboarding requires Directus login (ProtectedRoute). Temporarily public during dev, restored in T44 | Directus is the auth backend. Onboarding is mandatory for new users — they can't access the platform until they complete it. Kept public now to avoid login friction during screen-by-screen testing | T44: restore ProtectedRoute + add forced redirect (login → not onboarded → /onboarding → complete → dashboard) |
| 2026-02-27 | Branding: "Finance Crew AI" (not "CollectAI") | Company was renamed | Updated OnboardingLayout header + welcome title i18n keys |
| 2026-02-27 | Optional badge/skip only for follow-up questions | Core questions core_0 and core_6 have `is_required=false` but should not show as optional/skippable in UI. Only follow-ups are truly skippable | Check `!is_required && phase === "follow_up"` — not just `!is_required` |
| 2026-02-27 | Canvas-based audio visualizer (not React DOM) | Using `setState` at 60fps for div-based bars caused React batching — bars filled/dropped "all at once". Canvas with direct 2D context draws every frame smoothly | Audio visualizer must use `<canvas>` + `requestAnimationFrame`, never React state for per-frame updates |
| 2026-02-27 | Skip sends `"-"` (not empty string) | Backend `SubmitAnswerRequest.answer` has `min_length=1` — empty string `""` returns 422. Dash is a sentinel value for "no answer" | All non-required questions auto-fill `"-"` if submitted empty |
| 2026-02-27 | Audio transcription appends, not replaces | User records multiple segments — each transcription should add to existing text, not overwrite | `setAnswer(prev => prev ? prev + " " + text : text)` |
| 2026-02-28 | Review screen removed, report simplified | Review screen added friction without value (forward-only, read-only, user just answered everything). Report simplified from full SOP with collapsible sections to scannable bullet-point cards. Interview auto-confirms via `POST /interview/review` (no UI). Tasks renumbered: T41=Report, T42=Simulação, T43=Integração | 5 screens instead of 6. T41 DoD completely rewritten. PRD, tech_design, tasks.md, SUMMARY.md all updated |
| 2026-02-28 | Loading animations: darker green for contrast | Primary verde-limão `hsl(84 100% 51%)` is too light on white background — icons/ring/progress barely visible. Use darker green `hsl(84 100% 35%)` for loading animation elements. Apply to both enrichment (existing) and report (new) screens | T41: implement + backport to enrichment screen |
| 2026-02-28 | Report not shown to user | Client doesn't need to see the report — it's only used by backend for simulation. Report screen is just a loading transition that auto-navigates to simulation | Removed report cards/CTA from T41, simplified to loading-only |
| 2026-02-28 | Step indicator: only interactive screens count | Loading/transition screens (enrichment, report) shouldn't be steps — user thinks there are more steps than there are. Only 3 real steps: Dados, Entrevista, Simulação | Reduced from 6→5→3 steps |
| 2026-02-28 | Tailwind arbitrary HSL + opacity doesn't work | `border-[hsl(84_100%_35%)]/20` generates no CSS — Tailwind can't combine arbitrary values with opacity modifier. Must use CSS variable + tailwind config instead | Added `--primary-dark` CSS var + `primary.dark` in tailwind.config.ts → use `bg-primary-dark/10` |
| 2026-02-28 | Simulation: no Outcome/Metrics in UI | User sees only debtor profile + chat conversation. Resolution type, discount %, installments are internal metadata — showing them adds no value and can confuse | Removed Outcome card + Metrics badges from SimulationScenarioCard |
| 2026-02-28 | Simulation prompt: only mention benefits proactively | Discounts/installments: mention if offered (benefit to client), never say "we don't offer" unprompted. Fines/interest: mention if NOT charged (benefit to client), never bring up if charged. WhatsApp-based collection, payment links via WhatsApp not email | Updated SYSTEM_PROMPT + scenario instructions in backend simulation.py |

---

## Known Issues

| # | Description | Found in | Severity | Status |
|---|-------------|----------|----------|--------|

---

## Development Log

### 2026-02-28 — T42 (M7): Tela de Simulação

**Status**: done

**What was done**:
- Fixed `simulation.ts`: POST path `/simulate` → `/simulation/generate`, GET return type `GenerateSimulationResponse` → `SimulationResult`
- Created `ChatBubble.tsx`: WhatsApp-style bubbles — agent left (white #FFF), debtor right (light green #D9FDD3), role label above, shadow-sm
- Created `SimulationScenarioCard.tsx`: debtor profile banner + ScrollArea chat (h-[400px]) with WhatsApp background
- Created `whatsapp-bg.svg`: tiled doodle pattern (15 icons: chat, clock, phone, smiley, etc.) at 30% opacity on beige #ECE5DD
- Rewrote `OnboardingSimulation.tsx` (~300 lines): 3-phase state machine (loading/error/ready)
  - Loading: same hub animation as report/enrichment (MessageSquareText → Users → MessagesSquare → BarChart3), step dots, progress bar, primary-dark color
  - Ready: Tabs (Cooperativo/Resistente), SimulationScenarioCard per tab, Aprovar + Regenerar buttons
  - Session recovery: `generated` → POST generate; `simulating` → poll; `completed` → GET results
  - Aprovar: `clearSession()` + `navigate("/")` (no API call)
  - Regenerar: POST again, toast feedback, keeps old results visible until replaced
- Added `onboarding.simulation.*` i18n keys (~25 keys) to pt-BR, en, es

**Post-review changes** (user feedback):
- Removed Outcome card and Metrics badges from `SimulationScenarioCard.tsx` — user doesn't need to see resolution/discount/installments metadata
- Removed unused i18n keys (outcome, metrics, resolution*, discount, installments, paymentMethod) from all 3 locale files
- Updated backend simulation prompt (`backend/app/prompts/simulation.py`):
  - Added WhatsApp collection context (payment links via WhatsApp, not email)
  - Added policy mention rules: only proactively mention things that BENEFIT the client
  - Discounts/installments: only mention if company offers them; never say "we don't offer X" unprompted
  - Fines/interest: only mention if company does NOT charge (it's a benefit); if they charge, don't bring up unless asked
  - Updated scenario instructions to reinforce these rules

**Tests**:
- `tsc --noEmit` — 0 errors
- Backend: 12/12 simulation tests passing
- Dev server: simulation route loads (200)
- Pending: manual browser test with real backend session

---

### 2026-02-28 — T41 (M7): Tela do Relatório (loading-only)

**Status**: done

**What was done**:
- Built `OnboardingReport.tsx`: auto-confirms review, generates report, navigates to simulation
- State machine: `loading` | `error` (no "ready" phase — report not shown to user)
- Mount logic: `interviewed` → confirmReview + generateReport → navigate to simulation; `generating` → poll; `generated` → navigate
- Loading animation: same hub pattern as enrichment (cycling icons, step dots, progress bar)
- Darker green (`primary-dark` via CSS variable) for all loading animations (report + enrichment backport)
- Added `--primary-dark: 84 100% 35%` to `index.css` + `primary.dark` to `tailwind.config.ts`
- Step indicator: reduced to 3 steps (Dados, Entrevista, Simulação) — loading screens are transitions, not steps
- Bug fixes: `agent.ts` endpoint paths (missing `/agent/` segment), `STATUS_ROUTE_MAP` (`interviewed` → `/report`), interview navigation target
- Removed unused review step from `StepIndicator.tsx`
- Added `onboarding.report.*` i18n keys (loading steps, subtitle, error) to pt-BR, en, es
- Created `docs/DEV_ENVIRONMENT.md` — env setup reference for new devs

**Tests**:
- `tsc --noEmit` — 0 errors
- Manual: loading animation plays, report generates, navigates to simulation stub

**Bugs found & fixed**:
- `agent.ts` had wrong paths: `/sessions/{id}/generate` → `/sessions/{id}/agent/generate` (same for GET/PUT)
- Tailwind `border-[hsl(84_100%_35%)]/20` doesn't generate CSS — arbitrary values don't combine with opacity modifier. Fixed by using CSS variable + tailwind config
- `.env.local` was pointing to `localhost:8000` (backend not running) — restored to Railway URL
- Railway `ALLOWED_ORIGINS` env var was missing `http://localhost:8080` — added
- Railway `API_KEY` value had changed — updated `.env.local`

**Environment lessons** (added to `DEV_ENVIRONMENT.md` + `CLAUDE.md`):
- Never run `vite build` while dev server is running — use `tsc --noEmit`
- Never change `.env.local` — must always point to Railway
- Always check if dev server is already running before starting
- Railway env vars (`API_KEY`, `ALLOWED_ORIGINS`) are the source of truth for API access

---

### 2026-02-27 — T40 (M7): Tela de Entrevista

**Status**: done

**What was done**:
- Built full interview wizard in `OnboardingInterview.tsx` (~500 lines) replacing stub
- Question rendering by type: `<Textarea>` for text, `<RadioGroup>` for select, `<Checkbox>` group for multiselect
- Progress bar: `<Progress>` component updated after each answer via `getProgress()`
- Audio recording: `MediaRecorder API` (webm), `transcribeAudio()` sends to backend
- Auto-stop on silence: `AnalyserNode` + `getByteTimeDomainData()` computes RMS every 200ms, stops after 3s below threshold
- Audio transcription appends to existing text (not replaces) — user can record multiple segments
- Canvas-based audio visualizer: volume envelope approach (RMS per 50ms sample), scrolling bars drawn on `<canvas>` with `requestAnimationFrame`, HiDPI support via `devicePixelRatio`
- Optional/skip logic: only follow-up questions (`!is_required && phase === "follow_up"`) show "Opcional" badge and "Pular" button
- Non-required core questions auto-fill `"-"` when submitted empty (backend requires `min_length=1`)
- `animate-fade-in-up` transitions between questions
- Fixed `audio.ts`: endpoint path `/interview/transcribe` → `/audio/transcribe`
- Added `onboarding.interview.*` i18n keys (18 keys) to pt-BR, en, es

**Tests**:
- `tsc --noEmit` — 0 errors
- Manual: user tested full flow — all 7 core questions, follow-ups on "sim", audio recording with visualizer, skip on follow-ups, redirect to review at end
- Audio visualizer: real-time flowing bars confirmed working (canvas approach)
- Session recovery: refresh mid-interview resumes at correct question

**Bugs found & fixed**:
- `audio.ts` wrong endpoint path (was `/interview/transcribe`, should be `/audio/transcribe`)
- Backend rejects empty answer string (`min_length=1`) — skip now sends `"-"`
- `AudioContext` suspended state (browser autoplay policy) — added `await audioCtx.resume()`
- All questions showing as optional — fixed: only `follow_up` phase questions are skippable
- Audio visualizer with `setState` at 60fps caused batched/laggy updates — rewrote to canvas-based rendering

**Iterations on audio visualizer**:
1. Div-based bars with `setState` → React batching killed smooth animation
2. Frequency-domain (`getByteFrequencyData`) → voice concentrated in low bins, most bars stayed flat
3. Time-domain waveform → sensitivity too low for laptop mics
4. Final: Canvas + volume envelope (RMS) + scrolling history → smooth, responsive, like WhatsApp/Wispr Flow

---

### 2026-02-27 — T39 (M7): Tela de Enriquecimento

**Status**: done

**What was done**:
- Fixed `getEnrichment()` return type: `EnrichResponse` → `CompanyProfile` (backend GET returns flat object)
- Built animated loading screen: cycling icons (Globe→Search→FileText→Sparkles) every 4s, spinning dashed ring, ping radar effect, step dots indicator, gradient progress bar
- Added 5 custom Tailwind animations: `spin-slow`, `ping-ring`, `icon-swap`, `slide-up-fade`, `progress-fill`
- Auto-navigates to `/onboarding/interview` on success (no results screen — enrichment data used only by backend for report generation)
- Edge cases: 409 Conflict fallback, StrictMode double-mount guard, session recovery polling, retry on error
- Removed `type="url"` from welcome screen website input (browser rejected valid URLs like `https.www.site.com`)
- Added `onboarding.enrichment.*` i18n keys to pt-BR, en, es (loading steps, field labels, error messages)

**Tests**:
- `tsc --noEmit` — 0 errors
- Backend: 190/190 tests passing
- Manual: user tested full flow in browser — loading animation → auto-redirect to interview confirmed

---

### 2026-02-27 — T38 (M7): Tela de Boas-Vindas

**Status**: done

**What was done**:
- Replaced `OnboardingWelcome.tsx` stub with full welcome form: hero section, 3 fields with icon prefixes (Building2, Globe, Hash), submit button with loading state
- Fields: company name (required), website (required), CNPJ (optional with mask placeholder)
- Integration: `createSession()` API → `setSessionId()` + `setStatus()` in context → navigate to `/onboarding/enrichment`
- Validation: toast error on empty required fields, API error handling with toast
- Recovery state: shows spinner while `isRecovering` (session restoration from localStorage)
- Staggered `animate-fade-in-up` entrance animations
- Added `onboarding.welcome.*` i18n keys (13 keys) to pt-BR, en, es
- Removed `ProtectedRoute` from all onboarding routes — onboarding is public (no Directus login needed)
- Updated branding: "CollectAI" → "Finance Crew AI" in header and title
- Added `http://localhost:8080` to backend CORS default origins (`config.py`)
- Fixed `railway.toml`: `[build.builder] type = "DOCKERFILE"` → `builder = "DOCKERFILE"` (Railway config format change)

**Tests**:
- `tsc --noEmit` — 0 errors
- Backend: 190/190 tests passing
- API: `POST /sessions` returns 201 with valid session_id
- CORS preflight: `access-control-allow-origin: http://localhost:8080` confirmed
- Manual: user verified form renders correctly in browser

**Bugs found & fixed**:
- Onboarding routes wrapped in `ProtectedRoute` blocked access — removed (onboarding is public)
- Railway deploy failing with `build.builder: Invalid input` — config format changed, fixed
- i18n showing English — expected behavior (browser language detection), not a bug

---

### 2026-02-27 — T37.5 (M7): Setup + Infraestrutura do Onboarding

**Status**: done

**What was done**:
- Created branch `feat/onboarding` from `main` in `crew-ai-dashboard` repo
- Created `.env.local` (gitignored via `*.local`) with `VITE_ONBOARDING_API_URL` and `VITE_ONBOARDING_API_KEY`
- Added feature flag `"onboarding": false` to `FeatureFlagContext.tsx`
- Created `src/features/onboarding/` directory structure:
  - `api/`: client.ts (fetch + X-API-Key, 60s timeout), types.ts (all backend schemas), 7 endpoint files
  - `context/OnboardingContext.tsx`: session state + localStorage recovery + status-to-route mapping
  - `components/OnboardingLayout.tsx` + `StepIndicator.tsx` (6 steps with i18n)
  - `pages/`: 6 placeholder stubs (Welcome, Enrichment, Interview, Review, Report, Simulation)
  - `hooks/`: empty (.gitkeep)
- Extended `hideLayout` in App.tsx for `/onboarding` routes (no sidebar/header)
- Added 6 `/onboarding/*` routes with `ProtectedRoute` + `OnboardingProvider`
- Added i18n keys (`onboarding.steps.*`, `onboarding.common.*`) to pt-BR, en, es
- Committed and pushed to `origin/feat/onboarding`

**Tests**:
- `tsc --noEmit` — 0 errors
- `npm run build` — clean build (2765 modules)
- Dev server routes: all 6 `/onboarding/*` + `/login` + `/` return 200
- All Vite module resolution: 200

**Learnings**:
- Frontend repo `crew-ai-dashboard` has no `node_modules` by default (not committed) — must run `npm install` first
- Vite dev server runs on port **8080** (not 5173) — configured in `vite.config.ts`
- `.env` is NOT gitignored but `*.local` is — use `.env.local` for secrets
- `package-lock.json` changes from `npm install` — left uncommitted (not relevant to onboarding changes)
- Backend `API_KEY` found in `backend/.env`: `KJmNbGTQ8mH7WuvYVBu20vFLDuZR9g6kp-K6Yisw5cU`
- TypeScript is a dev dependency (no global `tsc`) — access via `node_modules/.bin/tsc`
- The `hideLayout` login redirect logic needed adjustment: `isAuthenticated` check was redirecting ALL hideLayout routes, fixed to only redirect when `location.pathname === "/login"`

---
