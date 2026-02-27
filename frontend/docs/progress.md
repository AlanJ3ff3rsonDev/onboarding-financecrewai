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

---

## Known Issues

| # | Description | Found in | Severity | Status |
|---|-------------|----------|----------|--------|

---

## Development Log

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
