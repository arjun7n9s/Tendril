# Tendril Deployment + Local Cognee Setup Plan

## Goal

Deploy Tendril in a demo-safe way while enabling local/self-hosted Cognee as the memory layer.

Recommended setup:

- Frontend: Vercel
- Backend: local FastAPI exposed through Cloudflare Tunnel or ngrok
- Memory: local Cognee first, with current JSONL memory fallback kept intact
- Demo safety: cached blessed-run mode remains available even if live services or Cognee fail

This gives us a public frontend URL for judges while still allowing the backend to use local services such as Cognee.

## Decision

Use the hybrid deployment for the hackathon demo:

```txt
Vercel Frontend
  -> NEXT_PUBLIC_API_BASE_URL
  -> Cloudflare/ngrok public tunnel
  -> Local FastAPI backend
  -> Local Cognee / JSONL fallback
```

Do not block deployment on Cognee. The frontend and backend should remain fully demoable with cached mode and JSONL memory.

## Why This Setup

Cognee can be used locally/self-hosted, so we do not need Cognee Cloud API access for the MVP. Since our backend already writes memory packets through `backend/app/services/memory_service.py`, we can add Cognee behind that boundary instead of changing scan logic everywhere.

Benefits:

- Fastest path to a public demo URL.
- Lets us use local Cognee without waiting for hosted credentials.
- Avoids deploying experimental Cognee infra before the demo.
- Keeps the reliable cached blessed-run demo path.

Tradeoff:

- The backend depends on the demo laptop staying awake and connected.
- Tunnel URL may change unless using a stable Cloudflare Tunnel config.

## Phase 0: Freeze Current Demo

Owner: full team

Checklist:

- Backend tests pass.
- Frontend `pnpm lint`, `pnpm type-check`, and `pnpm build` pass.
- Cached scan works for Ramp.
- `/accounts`, `/accounts/{id}`, `/signals`, `/scans`, `/imports`, `/outreach` work locally.
- `.env`, DB files, runtime logs, `.next`, `node_modules`, and screenshots are not committed.

No new product features during deployment except deployment fixes and Cognee adapter work.

## Phase 1: Deploy Frontend to Vercel

Owner: frontend/deployment

Steps:

1. Push latest code to GitHub.
2. Create a Vercel project from the repo.
3. Set project root to:

```txt
frontend
```

4. Use:

```txt
Install command: pnpm install
Build command: pnpm build
Output: Next.js default
```

5. Add environment variable:

```txt
NEXT_PUBLIC_API_BASE_URL=<public backend tunnel URL>
```

Initially this can be a placeholder until the tunnel is ready.

6. Deploy and confirm these routes load:

```txt
/
/accounts
/imports
/outreach
/signals
/scans
```

Expected result:

Frontend deploys successfully, but data calls may fail until backend tunnel and CORS are configured.

## Phase 2: Expose Local Backend

Owner: backend/deployment

Preferred option: Cloudflare Tunnel.

Alternative: ngrok.

### Backend Local Run

Run the backend locally:

```bash
cd backend
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check:

```txt
http://localhost:8000/health
```

### Cloudflare Tunnel Option

Install and authenticate `cloudflared`, then run:

```bash
cloudflared tunnel --url http://localhost:8000
```

Copy the generated HTTPS URL.

Example:

```txt
https://tendril-demo.trycloudflare.com
```

### ngrok Option

```bash
ngrok http 8000
```

Copy the generated HTTPS URL.

## Phase 3: Backend CORS

Owner: backend

The deployed Vercel frontend must be allowed to call the backend.

Required allowed origins:

```txt
http://localhost:3000
https://<vercel-preview-domain>
https://<vercel-production-domain>
```

If the backend currently hardcodes CORS origins, add an env-driven setting such as:

```txt
BACKEND_CORS_ORIGINS=http://localhost:3000,https://tendril.vercel.app
```

Then parse it in FastAPI startup and pass it to `CORSMiddleware`.

Acceptance check:

From the deployed Vercel frontend, `/accounts` should load real backend data without browser CORS errors.

## Phase 4: Update Vercel Env

Owner: frontend/deployment

Once the tunnel is live, update Vercel:

```txt
NEXT_PUBLIC_API_BASE_URL=https://<backend-tunnel-url>
```

Redeploy frontend.

Acceptance check:

- Vercel `/accounts` loads seeded accounts.
- Opening an account detail page works.
- Cached scan can be triggered.
- Scan panel updates.
- Signals, brief, graph/timeline, and outreach appear.

## Phase 5: Local Cognee Setup

Owner: backend/Cognee

Goal:

Run Cognee locally and prove we can write Tendril memory packets into it.

Suggested local setup path:

1. Create an isolated Cognee environment outside the main repo or under an ignored folder.
2. Install Cognee using its current docs.
3. Configure local storage/model settings.
4. Run a tiny standalone Cognee script first.
5. Only after standalone success, integrate into Tendril backend.

Do not start by wiring Cognee directly into scan runner. First prove Cognee works independently.

### Standalone Smoke Target

Create a temporary local script that does roughly:

```python
import cognee

async def main():
    await cognee.add("Ramp acquired Midday and reached a $32B valuation.")
    await cognee.cognify()
    results = await cognee.search("Why is Ramp relevant now?")
    print(results)
```

Exact API may differ based on Cognee version. Use Cognee docs as source of truth.

Acceptance check:

- Cognee can ingest one short text.
- Cognee can run processing.
- Cognee can return a useful search result.

## Phase 6: Tendril Cognee Adapter

Owner: backend

Current backend memory boundary:

```txt
backend/app/services/memory_service.py
```

Current scan usage:

```txt
backend/app/jobs/scan_runner.py
backend/app/services/cache_runner.py
```

Implementation approach:

1. Keep `JsonlMemoryService` as fallback.
2. Add a new `CogneeMemoryService`.
3. Use config to choose memory service:

```txt
TENDRIL_MEMORY_BACKEND=jsonl | cognee
COGNEE_DATASET_PREFIX=tendril
```

4. If Cognee fails, log a warning and fall back to JSONL for the demo.
5. Never fail the whole scan just because memory write failed.

Suggested adapter shape:

```python
class CogneeMemoryService(MemoryService):
    def __init__(self, event_logger=None):
        ...

    def remember(self, packet: MemoryPacket) -> None:
        ...

    def healthy(self) -> bool:
        ...
```

Memory packet mapping:

```txt
packet.title -> Cognee document title/name
packet.body -> main content
packet.fact -> factual evidence text
packet.inference -> AI-derived interpretation
packet.evidence_url -> source metadata
packet.account_id / scan_id / signal_id -> metadata
packet.dataset -> dataset/collection name
```

Acceptance check:

- A cached Ramp scan completes.
- `memory_writes` count still appears in scan counts.
- Cognee receives signal memory.
- JSONL fallback still works when Cognee is disabled.
- `/health` shows Cognee configured/available if we expose that status.

## Phase 7: Full Deployed Demo Check

Owner: full team

Use Vercel frontend URL.

Demo flow:

1. Open `/accounts`.
2. Confirm seeded accounts load.
3. Open Ramp.
4. Run cached scan.
5. Confirm scan panel reaches completed.
6. Show counters:
   - sources
   - evidence fetched
   - signals
   - AI calls
   - memory writes
7. Show signal cards with evidence.
8. Open graph tab.
9. Open timeline tab.
10. Show account brief.
11. Show outreach review.

Acceptance:

- Public frontend works.
- Backend tunnel works.
- Cached scan works.
- Cognee does not break the scan.
- If Cognee is not stable, switch memory backend back to JSONL and continue demo.

## Required Environment Variables

Frontend on Vercel:

```txt
NEXT_PUBLIC_API_BASE_URL=https://<backend-tunnel-url>
```

Backend local `.env`:

```txt
SIGNALGRAPH_MOCK_MODE=true
BRIGHT_DATA_API_KEY=<already configured locally>
BRIGHT_DATA_SERP_ZONE=champion_serp_api
BRIGHT_DATA_UNLOCKER_ZONE=champion_unlocker_api
AIML_API_KEY=<already configured locally>
AIML_EXTRACTION_MODEL=<configured model>
AIML_BRIEFING_MODEL=<configured model>
AIML_DRAFT_MODEL=<configured model>
COGNEE_DATASET_PREFIX=tendril
TENDRIL_MEMORY_BACKEND=jsonl
```

When Cognee is ready:

```txt
TENDRIL_MEMORY_BACKEND=cognee
```

If we add CORS env:

```txt
BACKEND_CORS_ORIGINS=http://localhost:3000,https://<vercel-domain>
```

## Rollback Plan

If frontend deploy fails:

- Use local frontend at `http://localhost:3000`.

If tunnel fails:

- Restart Cloudflare/ngrok tunnel.
- Update Vercel env if URL changed.
- Redeploy Vercel.

If Cognee fails:

- Set:

```txt
TENDRIL_MEMORY_BACKEND=jsonl
```

- Restart backend.
- Continue with cached demo.

If live Bright Data/API calls fail:

- Use cached mode.

If Vercel cannot reach backend:

- Check CORS.
- Check tunnel URL.
- Check backend health:

```txt
https://<backend-tunnel-url>/health
```

## What Not To Do

- Do not deploy new product features during this phase.
- Do not remove JSONL memory fallback.
- Do not make Cognee mandatory for scan completion.
- Do not expose `.env` or secrets through frontend env vars.
- Do not put Bright Data, AI/ML, Triggerware, or Speechmatics keys in Vercel frontend env.
- Do not rely on live mode for the only demo path.

## Final Recommendation

Deploy frontend first, tunnel backend second, then integrate Cognee locally behind the existing memory interface. Treat Cognee as a demo enhancement, not a dependency. The MVP should remain fully functional with cached mode and JSONL memory at all times.
