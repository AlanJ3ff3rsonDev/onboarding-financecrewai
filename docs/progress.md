# Progress Log: Self-Service Onboarding Backend

## How to Use This File

Log every task here. Entry format: date, task ID, status, what was done, tests, issues, next steps.
Full workflow: mark in_progress → implement → test task → test full suite → log here → mark done → git commit & push.

> **Archive**: Entries for T01-T36.7 are in `docs/progress_archive.md`.

---

## Decisions Log

| Date | Decision | Reason | Impact |
|------|----------|--------|--------|
| 2026-02-25 | Security hardening before deploy: 5 new tasks (T36.1-T36.5) before T37 | Security review found: no auth, SSRF, no rate limit, root container, exposed docs | T37 dependencies updated, M6 expanded |
| 2026-02-23 | Core questions 16→10, avatar removed from scope, financial details → planilha | Simplify onboarding: majority select/multiselect, financial params via spreadsheet, avatar in platform | Docs only, T32 redefined |

---

## Known Issues

| # | Description | Found in | Severity | Status |
|---|-------------|----------|----------|--------|
| | | | | |

---

## Development Log

### 2026-02-26 — T37 (M6): Deploy to Railway + Verify

**Status**: completed

**What was done**:
- Fixed Dockerfile CMD: hardcoded `--port 8000` → `${PORT:-8000}` (shell form for Railway's dynamic PORT)
- Created `railway.toml` in project root: Dockerfile path, health check `/health`, restart on failure
- Updated `docs/tech_design.md` Section 7: replaced PENDING placeholder with actual deployed config

**Tests**: 190/190 passing
**Deploy verified**: `https://onboarding-financecrewai-production.up.railway.app`

---

> All backend milestones (M0-M6) complete. Frontend progress tracked in `frontend/docs/progress.md`.
