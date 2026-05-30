# Stable Tunnel Deploy Runbook (ngrok static domain)

Free, week-long deploy: Vercel frontend → ngrok static domain → local FastAPI.
The laptop is the server; the DB and background workers stay where they work.

**Reserved domain:** `culprit-raider-voter.ngrok-free.dev`

---

## One-time setup

### 1. Backend `.env` (project root, never committed)

Add the Vercel origins to the CORS allow-list:

```dotenv
APP_ENV=development
DATABASE_URL=sqlite:///./signalgraph.db
SIGNALGRAPH_MOCK_MODE=true            # flip to false only for live Bright Data
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://<your-vercel-prod>.vercel.app
# Covers rotating Vercel preview URLs without editing env each deploy:
CORS_ALLOW_ORIGIN_REGEX=^https://.*\.vercel\.app$
```

Restart uvicorn after editing (settings are cached).

### 2. Vercel env (Production + Preview)

```
NEXT_PUBLIC_API_BASE_URL=https://culprit-raider-voter.ngrok-free.dev
```

No trailing slash. Redeploy so the new env is baked into the build.

### 3. Code (already done)

`lib/api/client.ts` sends `ngrok-skip-browser-warning: true` on every request,
so the browser receives JSON instead of ngrok's interstitial HTML.

---

## Daily start sequence

Two terminals on the demo laptop:

```cmd
:: Terminal 1 — backend
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```cmd
:: Terminal 2 — tunnel (reserved domain = stable URL across restarts)
ngrok http --domain=culprit-raider-voter.ngrok-free.dev 8000
```

Disable laptop sleep / screen lock for the demo window.

---

## Verify

1. `https://culprit-raider-voter.ngrok-free.dev/health` → returns JSON
   (`status: ok`, `database: ok`), not an HTML warning page.
2. Open the Vercel URL → `/today` and `/accounts` load with no CORS errors in
   DevTools.
3. Open Ramp → run a scan → panel reaches **completed**.

---

## Notes / gotchas

- The reserved domain is stable, so `NEXT_PUBLIC_API_BASE_URL` is set once and
  never changes for the week.
- Because the backend runs on the laptop, the SQLite DB and `var/` memory dirs
  persist and the watchtower + crash reclaimer keep running — none of the
  free-host ephemerality problems apply.
- If the laptop must sleep, scheduled watchtower scans pause until it's awake;
  manual scans resume normally.
- Keep secrets in the backend `.env` only. Vercel holds only
  `NEXT_PUBLIC_API_BASE_URL`.
