# Progress Log: Frontend Onboarding

## How to Use This File

Log every task here. Entry format: date, task ID, status, what was done, tests, issues, next steps.

---

## Decisions Log

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|

---

## Known Issues

| # | Description | Found in | Severity | Status |
|---|-------------|----------|----------|--------|

---

## Development Log

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
