# Dev Environment — Frontend Onboarding

## How it works

Frontend (Vite, port 8080) talks to the **production backend on Railway**. Connection is configured in `crew-ai-dashboard/.env.local` (gitignored). The `.env.local` file is already set up correctly — do not modify it.

## Rules

1. **Do NOT change `.env.local`** — it has the correct Railway URL and API key. Changing it breaks the app.
2. **Do NOT run `vite build`** while the dev server is running — use `tsc --noEmit` for type-checking.
3. **Do NOT start the dev server if it's already running** — check with `curl -s -o /dev/null -w "%{http_code}" http://localhost:8080` first.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "Failed to fetch" | `.env.local` was changed to localhost | Restore Railway URL in `.env.local`, restart Vite |
| CORS "No Access-Control-Allow-Origin" | Railway `ALLOWED_ORIGINS` missing `http://localhost:8080` | Add it on Railway dashboard, redeploy |
| "Invalid or missing API key" | `.env.local` key doesn't match Railway `API_KEY` | Copy `API_KEY` from Railway dashboard to `.env.local` as `VITE_ONBOARDING_API_KEY` |
| Env changes not taking effect | Vite caches env on startup | Restart dev server |
