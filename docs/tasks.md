# Tasks: Self-Service Onboarding

## How to Use This File

- Do one task at a time. Complete it, test it, log in `progress.md`, then move to the next.
- Status: `pending` → `in_progress` → `done`

> **Archive**: Detailed definitions for completed tasks (T01-T33) are in `docs/tasks_archive.md`.

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
| **M5.9** | Simplificar Entrevista + SOP Report | T34, T34.1 | DONE |
| **M6** | Deploy + Security Hardening | T35-T37 (+ T36.1-T36.7) | DONE |
| **M7** | Frontend Onboarding (Lovable) | T38-T44 | Moved to `frontend/docs/tasks.md` |
| **M8** | Integracao Directus | T45 | Moved to `frontend/docs/tasks.md` |

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
| T33 | Pesquisa web sobre a empresa no enrichment | M5.8 | `done` |
| T34 | Simplificar entrevista (10→7, remover dinâmicas) | M5.9 | `done` |
| T34.1 | Substituir AgentConfig por OnboardingReport (SOP) | M5.9 | `done` |
| T35 | CORS configuration | M6 | `done` |
| T36 | Dockerfile + Railway config | M6 | `done` |
| T36.1 | API Authentication — X-API-Key | M6 | `done` |
| T36.2 | SSRF Protection on URL Scraping | M6 | `done` |
| T36.3 | Rate Limiting on Expensive Endpoints | M6 | `done` |
| T36.4 | Dockerfile Security Hardening | M6 | `done` |
| T36.5 | Production API Hardening | M6 | `done` |
| T36.7 | Filtrar campos sensíveis no GET /sessions/{id} | M6 | `done` |

---

## Active & Pending Tasks

### T35: CORS configuration (M6)

**Dependencies**: T34.1

**Definition of Done**:
- CORSMiddleware in app/main.py
- Allowed origins: portal.financecrew.ai, localhost:* (via ALLOWED_ORIGINS env var)

**Status**: `done`

---

### T36: Dockerfile + Railway config (M6)

**Dependencies**: T35

**Definition of Done**:
- Dockerfile with Python 3.13 + Playwright dependencies
- docker build + docker run work locally

**Status**: `done`

---

### T36.1: API Authentication — X-API-Key (M6)

**Dependencies**: T36
**Priority**: HIGH (sem isso, qualquer pessoa usa a API e gasta créditos OpenAI/Serper)

**Context**: Todos os endpoints são públicos. Qualquer um que descubra a URL pode criar sessões, rodar enrichment (Playwright + OpenAI + Serper), gerar reports (OpenAI), rodar simulações (OpenAI), e transcrever áudio (OpenAI). Cada chamada custa dinheiro real.

**What to do**:
- Add `API_KEY` field to `Settings` in `app/config.py` (required, no default)
- Create `app/dependencies.py` with a `verify_api_key` dependency that checks `X-API-Key` header
- Apply dependency to ALL routers via `app.include_router(..., dependencies=[Depends(verify_api_key)])`
- `/health` endpoint must remain public (no auth) — it's used for uptime monitoring
- Return `401 Unauthorized` with `{"detail": "Invalid or missing API key"}` on failure
- Update `.env.example` with `API_KEY=your-api-key-here`

**Endpoints protected** (all under `/api/v1/sessions`):
- `POST /` (create session)
- `POST /{id}/enrich` (scraping + OpenAI + Serper — $$)
- `GET /{id}/enrichment`
- `GET /{id}/interview/next`
- `POST /{id}/interview/answer` (may call OpenAI for follow-up eval)
- `GET /{id}/interview/progress`
- `GET/POST /{id}/interview/review`
- `POST /{id}/agent/generate` (OpenAI — $$)
- `GET /{id}/agent`
- `PUT /{id}/agent/adjust` (OpenAI — $$)
- `POST /{id}/simulation/generate` (OpenAI — $$)
- `GET /{id}/simulation`
- `POST /{id}/audio/transcribe` (OpenAI — $$)

**Definition of Done**:
- All `/api/v1/` endpoints require valid `X-API-Key` header
- `/health` remains public
- Invalid/missing key returns 401
- Tests updated (all test requests include the API key header)
- `.env.example` updated

**Status**: `done`

---

### T36.2: SSRF Protection on URL Scraping (M6)

**Dependencies**: T36
**Priority**: HIGH (atacante pode acessar metadados internos do servidor via scraping)

**Context**: `scrape_website()` em `app/services/enrichment.py` recebe URL do usuário e abre no Playwright sem validação. Um atacante pode enviar:
- `http://169.254.169.254/latest/meta-data/` (metadados cloud AWS/GCP)
- `http://localhost:8000/...` (serviços internos)
- `http://10.x.x.x/...` (rede interna)
- `file:///etc/passwd` (leitura de arquivos locais)

**What to do**:
- Create `app/utils/url_validation.py` with function `validate_url(url: str) -> str`
- Validation rules:
  1. Only allow `http://` and `https://` schemes (reject `file://`, `ftp://`, `data:`, etc.)
  2. Resolve hostname to IP and reject private/reserved ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `0.0.0.0`
  3. Reject `localhost` as hostname
  4. Return cleaned URL or raise `ValueError` with clear message
- Call `validate_url()` at the start of `scrape_website()` in `app/services/enrichment.py` BEFORE Playwright launches
- Also validate in `CreateSessionRequest.website` field using Pydantic validator (first line of defense)

**Files to modify**:
- `app/utils/url_validation.py` (new)
- `app/services/enrichment.py` — add `validate_url()` call at top of `scrape_website()`
- `app/models/schemas.py` — add Pydantic validator to `CreateSessionRequest.website`

**Definition of Done**:
- `file://`, `ftp://`, `data:` URLs rejected
- Private IPs (127.x, 10.x, 172.16-31.x, 192.168.x, 169.254.x) rejected
- `localhost` rejected
- Valid public URLs still work normally
- Tests covering all rejection cases + valid URL pass-through

**Status**: `done`

---

### T36.3: Rate Limiting on Expensive Endpoints (M6)

**Dependencies**: T36.1 (auth must exist first — rate limit per API key or per IP)
**Priority**: HIGH (sem isso, mesmo com auth, podem abusar e estourar créditos)

**Context**: Endpoints que chamam OpenAI/Serper/Playwright são caros. Sem rate limit, mesmo um cliente autenticado (ou key vazada) pode fazer milhares de chamadas e gerar custo altíssimo.

**What to do**:
- Install `slowapi` (`uv add slowapi`)
- Configure `Limiter` in `app/main.py` with default limits
- Rate limit tiers (by IP, por ser MVP):
  - **Heavy** ($$$ — OpenAI + Playwright): 5/minute
    - `POST /{id}/enrich`
    - `POST /{id}/agent/generate`
    - `PUT /{id}/agent/adjust`
    - `POST /{id}/simulation/generate`
    - `POST /{id}/audio/transcribe`
  - **Medium** (may call OpenAI for follow-up): 20/minute
    - `POST /{id}/interview/answer`
  - **Light** (reads only, no external calls): 60/minute
    - All GET endpoints, `POST /sessions`
- Return `429 Too Many Requests` with `{"detail": "Rate limit exceeded. Try again in X seconds."}`

**Files to modify**:
- `pyproject.toml` — add `slowapi` dependency
- `app/main.py` — configure `Limiter` + exception handler
- All routers in `app/routers/` — add `@limiter.limit()` decorators to each endpoint

**Definition of Done**:
- All endpoints have rate limits applied
- Returns 429 on excess
- `/health` exempt from rate limiting
- Tests pass (test client must handle rate limiter)

**Status**: `done`

---

### T36.4: Dockerfile Security Hardening (M6)

**Dependencies**: T36
**Priority**: MEDIUM

**Context**: Container roda como root (se hackear, tem acesso total). Tag `uv:latest` é mutável (build pode quebrar sem aviso).

**What to do**:
- Pin uv to specific version: `COPY --from=ghcr.io/astral-sh/uv:0.6.3` (or current latest)
- Add non-root user after system deps install:
  ```dockerfile
  RUN useradd -m -s /bin/bash appuser
  ```
- Install Playwright browser as appuser (or ensure cache is accessible)
- Switch to non-root before running app:
  ```dockerfile
  USER appuser
  ```
- Verify `docker build` + `docker run` + `/health` still work
- Verify Playwright still works inside container as non-root

**Files to modify**:
- `backend/Dockerfile`

**Definition of Done**:
- Container runs as `appuser` (not root)
- uv version pinned
- `docker build` + `docker run` + `/health` work
- Playwright works inside container

**Status**: `done`

---

### T36.5: Production API Hardening (M6)

**Dependencies**: T36
**Priority**: MEDIUM

**Context**: Vários ajustes menores de segurança para produção.

**What to do**:

1. **Disable OpenAPI docs in production**:
   - Add `ENVIRONMENT` field to `Settings` (default: `"production"`)
   - In `main.py`: `docs_url=None, redoc_url=None` when `ENVIRONMENT == "production"`
   - In dev: `ENVIRONMENT=development` in `.env` enables `/docs`

2. **Restrict CORS methods/headers**:
   - In `main.py`, change `allow_methods=["*"]` → `allow_methods=["GET", "POST", "PUT", "OPTIONS"]`
   - Change `allow_headers=["*"]` → `allow_headers=["Content-Type", "Accept", "X-API-Key"]`

3. **Generic error messages**:
   - In routers that expose `str(exc)` (e.g., `agent.py:41`, `simulation.py:44`), replace with generic message
   - `raise HTTPException(status_code=500, detail="Internal server error")` — log full error server-side
   - Only `400` errors can keep specific messages (they're user-input validation)

4. **Limit upload body size**:
   - Add middleware or check in `audio.py` to reject requests before reading full body into memory
   - Alternative: read in chunks up to 25MB, reject early

**Files to modify**:
- `app/config.py` — add `ENVIRONMENT` field
- `app/main.py` — conditional docs, restrict CORS
- `app/routers/agent.py` — generic 500 errors
- `app/routers/simulation.py` — generic 500 errors
- `app/routers/audio.py` — body size limit
- `.env.example` — add `ENVIRONMENT=development`

**Definition of Done**:
- `/docs` and `/redoc` return 404 when `ENVIRONMENT=production`
- CORS methods/headers restricted
- 500 errors return generic message (full error only in server logs)
- Audio upload rejects oversized bodies before reading into memory
- All tests pass

**Status**: `done`

---

### T36.7: Filtrar campos sensíveis no GET /sessions/{id} (M6)

**Dependencies**: T36.1
**Priority**: LOW (T36.1 já protege com auth, mas é defesa em profundidade)

**Context**: `GET /sessions/{session_id}` retorna o objeto inteiro do banco: `interview_state`, `interview_responses`, `agent_config`, `enrichment_data`, `simulation_result`. Mesmo com autenticação, se um session_id vazar, expõe todos os dados da empresa. Defesa em profundidade: retornar apenas o necessário.

**What to do**:
- Criar um `SessionPublicResponse` em `app/models/schemas.py` com apenas os campos necessários para o frontend:
  - `id`, `company_name`, `company_website`, `status`, `created_at`
  - Excluir: `interview_state` (interno), `enrichment_data` (interno)
  - Incluir `interview_responses`, `agent_config`, `simulation_result` apenas se existirem
- Usar `SessionPublicResponse` como `response_model` no `GET /sessions/{id}`
- Manter o objeto completo acessível internamente (para os outros endpoints que precisam)

**Files to modify**:
- `app/models/schemas.py` — novo modelo `SessionPublicResponse`
- `app/routers/sessions.py` — usar novo response model

**Definition of Done**:
- `GET /sessions/{id}` não retorna `interview_state` nem dados internos desnecessários
- Frontend continua funcionando normalmente
- Tests updated

**Status**: `done`

---

### T37: Deploy to Railway + verify (M6)

**Dependencies**: T36.1, T36.2, T36.3, T36.4, T36.5, T36.7

**Definition of Done**:
- Backend accessible via public URL
- GET /health works, POST /sessions works (with API key)
- OPENAI_API_KEY, SEARCH_API_KEY, API_KEY configured as env vars

**Status**: `done`

---

> **Frontend tasks (M7-M8)** moved to `frontend/docs/tasks.md`.
