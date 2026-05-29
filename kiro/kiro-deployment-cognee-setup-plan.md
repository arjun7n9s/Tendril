# Tendril Deployment + Local Cognee Setup Plan

## Goal

Get Tendril onto a public URL for the demo with the **lowest risk**, then layer in
local Cognee as a memory backend behind the existing `MemoryService` protocol.

Two independent tracks:

- **Track A — Deployment (priority).** Vercel frontend, local FastAPI backend exposed
  through Cloudflare Tunnel (with ngrok as fallback), routed via `NEXT_PUBLIC_API_BASE_URL`.
- **Track B — Cognee (deferred).** Stand up Cognee locally, prove it works in isolation,
  then drop in a `CogneeMemoryService` behind a feature flag without touching scan logic.

```txt
Vercel Frontend  ──HTTPS──►  Cloudflare/ngrok tunnel  ──►  Local FastAPI (127.0.0.1:8000)
                                                            ├─ JsonlMemoryService (default)
                                                            └─ CogneeMemoryService (Track B)
```

## Operating Principles

- Ship Track A end-to-end before touching Track B. Cognee never blocks the demo.
- The cached blessed-run path stays the safety net. Live Bright Data and Cognee are enhancements.
- Keep `JsonlMemoryService` as the always-available fallback.
- No new product features during deployment, only deployment fixes and the Cognee adapter.
- Never put Bright Data, AI/ML, Triggerware, Speechmatics, or Cognee secrets in Vercel env.

---

# Track A — Deployment

## Phase A0: Freeze & Pre-flight

**Owner:** full team
**Goal:** Confirm the local app is green before exposing it.

Steps:

1. Pull latest, ensure clean working tree.
2. Backend checks (from `backend/`):
   ```cmd
   uv sync
   uv run pytest
   uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
   Then in a second shell:
   ```cmd
   curl http://127.0.0.1:8000/health
   ```
   Expect `status: ok` and `database: ok`.
3. Frontend checks (from `frontend/`):
   ```cmd
   pnpm install
   pnpm sync:seed
   pnpm lint
   pnpm type-check
   pnpm build
   pnpm dev
   ```
   Visit `http://localhost:3000`, confirm `/accounts`, `/imports`, `/outreach`, `/signals`, `/scans` render and `/accounts` auto-primes the demo seed.
4. Run a cached Ramp scan end-to-end. Verify Signals, Brief, Graph, Timeline, Outreach all populate.
5. Confirm `.env`, `signalgraph.db`, `var/`, `.next`, `node_modules`, screenshots are all gitignored. Do not commit secrets.

**Acceptance:** All of the above pass on the demo laptop. Push the branch you intend to deploy.

---

## Phase A1: Backend CORS Hardening

**Owner:** backend
**Goal:** Allow the future Vercel preview and production domains without code changes.

Context: `app/main.py` already reads `settings.cors_origins_list` from
`CORS_ALLOWED_ORIGINS` (comma-separated). No code change needed, only env.

Steps:

1. Edit project root `.env` (do not commit) so the variable lists every origin that will hit the API:
   ```dotenv
   CORS_ALLOWED_ORIGINS=http://localhost:3000,https://<vercel-preview>.vercel.app,https://<vercel-production-domain>
   ```
   Use the actual domains from Phase A4 once known. It is fine to seed it with `http://localhost:3000` for now and append after the first Vercel deploy.
2. Restart uvicorn so the new env is picked up (settings are cached).
3. Sanity check from a Vercel preview later (Phase A6) that there are no `CORS` errors in the browser console.

**Acceptance:** Backend boots with the new origins listed in `CORS_ALLOWED_ORIGINS`, `app.startup` log shows the expected `env`/`mock_mode` values.

**No-go:** Do not switch to `allow_origins=["*"]`. We send credentials and need a real allow-list.

---

## Phase A2: Run Backend Locally for Tunnel

**Owner:** backend / deployment
**Goal:** Have a stable backend on `127.0.0.1:8000` that the tunnel can target.

Steps:

1. Confirm `.env` at project root has at minimum:
   ```dotenv
   APP_ENV=development
   SIGNALGRAPH_MOCK_MODE=true
   DATABASE_URL=sqlite:///./signalgraph.db
   CORS_ALLOWED_ORIGINS=http://localhost:3000
   ```
   Plus the Bright Data + AI/ML keys you already use locally.
2. Start the API:
   ```cmd
   cd backend
   uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
3. Keep this terminal open for the demo. Disable laptop sleep and screen lock for the demo window.

**Acceptance:** `GET http://127.0.0.1:8000/health` returns 200.

---

## Phase A3: Expose Backend via Tunnel

**Owner:** deployment
**Goal:** Public HTTPS URL pointing at `127.0.0.1:8000`.

**Primary: Cloudflare Tunnel (free, no signup required for quick mode).**

Quick mode (ephemeral URL, simplest):
```cmd
cloudflared tunnel --url http://localhost:8000
```
Cloudflared prints something like `https://<random-words>.trycloudflare.com`.
Copy that URL — this becomes `NEXT_PUBLIC_API_BASE_URL`.

Stable mode (named tunnel, URL survives restarts) — only do this if you have a Cloudflare account and a domain on Cloudflare:
```cmd
cloudflared tunnel login
cloudflared tunnel create tendril-demo
cloudflared tunnel route dns tendril-demo tendril-demo.<your-domain>
cloudflared tunnel run tendril-demo
```

**Fallback: ngrok.**
```cmd
ngrok http 8000
```
Use the printed `https://...ngrok-free.app` URL.

Verify from any browser:
```
https://<tunnel-url>/health
```
Expect the same JSON as the local `/health`.

**Acceptance:** Public URL returns the backend health JSON over HTTPS.

**Risks & mitigations:**
- Quick-mode Cloudflared URL changes on every restart. Have the named-tunnel command ready as a fallback. Keep a sticky note with the current URL.
- Free ngrok has rate limits and an interstitial warning page on the first hit. If that becomes a problem mid-demo, switch to Cloudflared.

---

## Phase A4: Vercel Project Setup

**Owner:** frontend / deployment
**Goal:** Frontend on a public URL, building from the `frontend/` subdirectory.

Steps:

1. Push the branch to GitHub.
2. In Vercel:
   - **New Project** → import the repo.
   - **Root Directory** → `frontend`.
   - **Framework Preset** → Next.js (auto).
   - **Install Command** → `pnpm install`.
   - **Build Command** → `pnpm build`.
   - **Output** → leave default (Next.js).
   - **Node version** → 20.x (matches `.nvmrc`).
3. **Environment Variables** (Production + Preview):
   ```
   NEXT_PUBLIC_API_BASE_URL=<placeholder for now, e.g. http://localhost:8000>
   ```
   You will overwrite this in Phase A5 once the tunnel URL is final. Setting a placeholder now avoids a build-time crash and gives you a working surface to validate the routes load.
4. Trigger the first deploy.
5. After deploy, capture both URLs:
   - Production: `https://<project>.vercel.app`
   - Preview (per-branch): `https://<project>-git-<branch>-<team>.vercel.app`

**Acceptance:** All static routes render on the Vercel URL: `/`, `/accounts`, `/imports`, `/outreach`, `/signals`, `/scans`. Data calls will fail until Phase A5 — that is expected.

---

## Phase A5: Wire Frontend → Backend

**Owner:** frontend / deployment
**Goal:** Vercel frontend talks to the local backend through the tunnel.

Steps:

1. In Vercel project settings, set:
   ```
   NEXT_PUBLIC_API_BASE_URL=https://<tunnel-url>
   ```
   No trailing slash. `lib/api/client.ts` strips one if present, but keep it clean.
2. Redeploy (Vercel does this automatically on env change for the next build, or trigger a manual redeploy of the latest commit).
3. Update project root `.env` on the demo laptop:
   ```dotenv
   CORS_ALLOWED_ORIGINS=http://localhost:3000,https://<vercel-production>.vercel.app,https://<vercel-preview>.vercel.app
   ```
   Restart uvicorn.

**Acceptance:** From the Vercel URL:
- `/accounts` loads seeded accounts (no CORS errors in DevTools).
- Account detail loads.
- `/imports` page works.

---

## Phase A6: End-to-End Smoke on Vercel

**Owner:** full team
**Goal:** Validate the demo path on the live URL.

Demo flow against the Vercel URL:

1. Open `/accounts`. Seed auto-primes if empty.
2. Open Ramp.
3. Trigger a cached scan.
4. Watch the live scan panel reach **completed**.
5. Confirm counters: sources, evidence fetched, signals, AI calls, memory writes.
6. Inspect Signals tab — cards show evidence and snippets.
7. Open the Graph tab and the Timeline tab.
8. Open the Account Brief.
9. Open `/outreach`, review a draft.
10. Visit `/health` on the tunnel URL: confirm `database: ok` and integrations show `configured` for the ones you expect.

**Acceptance:** Every step succeeds. No CORS errors. No 5xx. The cached scan path is bulletproof.

**Rollback:**
- If Vercel build fails: demo from `http://localhost:3000` instead — feature parity.
- If tunnel URL changed (Cloudflared quick mode): rerun the tunnel, copy the new URL, update Vercel env, redeploy. Keep `BACKEND_CORS_ORIGINS` permissive enough to cover both Vercel production and preview hosts.
- If live mode misbehaves: `SIGNALGRAPH_MOCK_MODE=true` in `.env`, restart uvicorn, fall back to cached scans.

---

## Track A Environment Reference

**Vercel (frontend):**
```
NEXT_PUBLIC_API_BASE_URL=https://<tunnel-url>
```

**Backend `.env` at project root (never committed):**
```dotenv
APP_ENV=development
DATABASE_URL=sqlite:///./signalgraph.db
SIGNALGRAPH_MOCK_MODE=true
SIGNALGRAPH_SCAN_PHASE_TIMEOUT_SECONDS=300

CORS_ALLOWED_ORIGINS=http://localhost:3000,https://<vercel-prod>.vercel.app,https://<vercel-preview>.vercel.app

# Bright Data REST
BRIGHT_DATA_API_KEY=...
BRIGHT_DATA_API_ENDPOINT=https://api.brightdata.com/request
BRIGHT_DATA_SERP_ZONE=champion_serp_api
BRIGHT_DATA_UNLOCKER_ZONE=champion_unlocker_api

# AI/ML API
AIML_API_KEY=...
AIML_API_BASE_URL=https://api.aimlapi.com/v1
AIML_EXTRACTION_MODEL=...
AIML_BRIEFING_MODEL=...
AIML_DRAFT_MODEL=...

# Cognee (Track B will use these)
COGNEE_DATASET_PREFIX=tendril
TENDRIL_MEMORY_BACKEND=jsonl
```

---

# Track B — Local Cognee (Independent of Track A)

> Do not start Track B until Track A is green and the demo is reproducible from the
> Vercel URL.

## Phase B0: Install & Standalone Smoke

**Owner:** backend / Cognee
**Goal:** Prove Cognee works on the demo laptop in isolation, with no Tendril coupling.

Steps:

1. Create an isolated venv outside this repo (or under a gitignored folder like `cognee-lab/`):
   ```cmd
   mkdir cognee-lab
   cd cognee-lab
   uv venv
   uv pip install cognee
   ```
2. Configure local storage and an LLM the same way you do for AI/ML API. Use Cognee’s current docs as source of truth for the env var names — they evolve.
3. Write a one-file standalone script `smoke.py`:
   ```python
   import asyncio
   import cognee

   async def main():
       await cognee.add("Ramp acquired Midday and reached a $32B valuation in 2025.")
       await cognee.cognify()
       results = await cognee.search("Why is Ramp relevant now?")
       for r in results:
           print(r)

   asyncio.run(main())
   ```
4. Run it:
   ```cmd
   uv run python smoke.py
   ```

**Acceptance:** Cognee ingests, processes, and returns at least one relevant result. No tracebacks.

**No-go signals (stop and de-risk):**
- API surface differs significantly from above: pin Cognee version in `cognee-lab/pyproject.toml` and adjust the smoke. Do not import Cognee into Tendril until the smoke is repeatable.
- Cognify takes minutes on a small input: tune local model settings before integrating, otherwise scans will time out.

---

## Phase B1: Add Cognee to Tendril Backend (Behind a Flag)

**Owner:** backend
**Goal:** Wire a `CogneeMemoryService` that satisfies the existing `MemoryService` protocol.

Existing seam (already in place):

- `backend/app/services/memory_service.py` defines `MemoryService` protocol and `MemoryPacket` with Cognee-shaped fields (`fact`, `inference`, `relationship`, `evidence_url`, `dataset`, `account_id`, `signal_id`, `observed_at`, `metadata`).
- `backend/app/jobs/scan_runner.py` and `backend/app/services/cache_runner.py` write through this interface only.

Steps:

1. Add config keys in `backend/app/config.py`:
   ```python
   tendril_memory_backend: str = Field(default="jsonl")  # "jsonl" | "cognee"
   cognee_local_db_path: str = Field(default="")        # if Cognee needs it
   ```
   Plus any Cognee-required env (model, storage path) that the standalone smoke relied on.
2. Add `backend/app/services/cognee_memory.py`:
   ```python
   class CogneeMemoryService:
       def __init__(self, *, dataset_prefix: str, event_logger=None, replayed=False):
           ...

       def remember(self, packet: MemoryPacket) -> str:
           # Map packet -> Cognee add() with metadata.
           # Catch exceptions, log structured warning, return packet.title.
           # Never raise into the scan pipeline.
           ...

       def query(self, question: str, *, limit: int = 5) -> list[MemoryHit]:
           ...

       def healthy(self) -> bool:
           ...
   ```
3. Build a small factory that the scan runner already calls (or introduce one if the current code instantiates `JsonlMemoryService` directly):
   ```python
   def build_memory_service(...) -> MemoryService:
       if settings.tendril_memory_backend == "cognee":
           try:
               return CogneeMemoryService(...)
           except Exception as e:
               log.warning("memory.cognee_init_failed", err=str(e))
       return JsonlMemoryService(...)
   ```
4. Update `/health` (`backend/app/api/health.py`) to reflect actual Cognee availability:
   - `cognee: configured | not_configured | unhealthy` based on `service.healthy()`.

**Packet → Cognee mapping:**

| MemoryPacket field | Cognee target                      |
| ------------------ | ---------------------------------- |
| `title`            | document title / name              |
| `body`             | main content                       |
| `fact`             | extracted factual statement        |
| `inference`        | AI-derived interpretation          |
| `evidence_url`     | source metadata                    |
| `account_id`       | metadata / dataset partition       |
| `scan_id`          | metadata                           |
| `signal_id`        | metadata                           |
| `dataset`          | dataset / collection name          |
| `observed_at`      | metadata                           |

**Acceptance:**
- With `TENDRIL_MEMORY_BACKEND=jsonl`: behavior identical to today.
- With `TENDRIL_MEMORY_BACKEND=cognee`: a cached Ramp scan completes, `memory_writes` count is non-zero, Cognee receives signal memory, no exceptions surface to the user.
- Killing the Cognee process mid-scan never breaks the scan. Logs show a warning, JSONL fallback engages.
- `/health` reflects Cognee status accurately.

---

## Phase B2: Demo Switchover (Optional)

**Owner:** full team
**Goal:** Run the public demo with Cognee on, JSONL standby.

Steps:

1. Set `TENDRIL_MEMORY_BACKEND=cognee` in the backend `.env`.
2. Restart uvicorn and Cognee.
3. Re-run the Phase A6 smoke against the Vercel URL.
4. Have a hot-rollback ready: a second `.env` line you can flip to `jsonl` and a one-line restart command.

**Acceptance:** Same Phase A6 acceptance, plus Cognee ingestion visible in its dashboard / logs.

**Rollback:** flip `TENDRIL_MEMORY_BACKEND=jsonl`, restart backend. Done.

---

# Cross-Cutting Notes

## Hard Rules

- Frontend env on Vercel contains only `NEXT_PUBLIC_*` and only the API base URL. No backend secrets.
- The scan pipeline must never fail because memory write failed.
- Do not change scan logic to integrate Cognee. The integration point is `MemoryService` only.
- `JsonlMemoryService` stays in the codebase as the fallback forever.

## Decision Tree During the Demo

```
Vercel page blank or 500?
  └─ open https://<tunnel>/health
       ├─ 200 with database ok → frontend issue, hit /accounts on localhost as backup
       └─ unreachable → restart cloudflared, update NEXT_PUBLIC_API_BASE_URL, redeploy
            └─ still failing → use ngrok, repeat env update

Live scan errors?
  └─ set SIGNALGRAPH_MOCK_MODE=true, restart, demo cached path

Cognee misbehaves?
  └─ TENDRIL_MEMORY_BACKEND=jsonl, restart, demo continues
```

## What Not To Do

- Do not deploy the FastAPI backend to Vercel. Vercel’s Python runtime is for serverless; our app uses a long-lived process, SQLite file, and background scan workers. A tunnel is correct here.
- Do not commit the `.env`, `signalgraph.db`, or `var/memory/` directory.
- Do not bake the tunnel URL into the source. It belongs in Vercel env only.
- Do not start Track B before Track A is fully green.

## Final Recommendation

Track A first. Get to a public Vercel URL talking to the local backend through Cloudflared, with cached scans running end-to-end. Treat that as the safe demo. Then build Track B as a pure addition behind `TENDRIL_MEMORY_BACKEND`, using the existing `MemoryService` seam, so Cognee can be toggled on for the impressive moment and toggled off in one breath if it misbehaves.
