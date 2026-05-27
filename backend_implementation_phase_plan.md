# SignalGraph Backend - Phase Plan (Final)

**Inputs used:** `backend_implementation_plan.md`, `engineered_product_blueprint.md`, `external_credentials_usage_guide.md`, `.env`.
**State of credentials:** Bright Data (REST + Browser), AI/ML API (key + model IDs), Triggerware (key, stubbed), Speechmatics (key, deferred). **Cognee deferred.** Mock mode default.
**Status:** Approved with refinements 1-13.

---

## 1. Tool Reality Check

What each tool actually accepts so we don't waste time during the build.

### Bright Data - REST (`https://api.brightdata.com/request`)
- Same endpoint for SERP and Web Unlocker. Only the `zone` differs.
- Auth: `Authorization: Bearer ${BRIGHT_DATA_API_KEY}`.
- Payload: `{ "zone": "<zone-name>", "url": "<target>", "format": "raw" }`.
- SERP zone (`champion_serp_api`): `url` is a Google search URL. Returns rendered SERP HTML when `format=raw`.
- Web Unlocker zone (`champion_unlocker_api`): `url` is the actual page to scrape.
- `format: "raw"` returns content body. `format: "json"` returns wrapped object with status/headers/body.
- Reference: docs.brightdata.com REST API. Content rephrased for compliance.

### Bright Data - Browser API (Playwright over CDP)
- Endpoint: `BRIGHT_DATA_BROWSER_WS` (already in `.env`).
- Pattern: `playwright.chromium.connect_over_cdp(ws)`, then `page.goto(...)`.
- Heavier and slower than Unlocker. **Fallback only**, used when Unlocker returns thin/blocked content on JS-heavy pages.
- Reference: brightdata.com Scraping Browser docs.

### Bright Data - MCP
- `BRIGHT_DATA_MCP_URL` empty. Skipped for MVP. SERP + Unlocker covers Track 1 product-usage requirements.

### AI/ML API
- OpenAI-compatible. Base URL `https://api.aimlapi.com/v1`.
- Use the `openai` Python SDK with `base_url=AIML_API_BASE_URL`, `api_key=AIML_API_KEY`.
- 400+ model IDs available. Locked picks below.
- Reference: docs.aimlapi.com model database. Content rephrased.

### Speechmatics
- Batch base URL: `https://eu1.asr.api.speechmatics.com/v2`.
- Bearer auth from `SPEECHMATICS_API_KEY`. SDK: `speechmatics-batch` (PyPI).
- **Out of MVP path. Only attempted in Phase 8 if Phases 0-7 are stable.**
- Reference: docs.speechmatics.com.

### Triggerware.ai
- Public docs sparse. Key held in `.env`. Wrapped behind feature flag, stubbed. Not on critical path.

### Cognee
- Deferred. Every service writes through a `MemoryService` interface from Phase 2 onward. Initial implementation writes JSONL packets to disk. Cognee implementation slots in later without touching the scan pipeline.

---

## 2. Architectural Anchors (locked from Section 19)

- FastAPI + `BackgroundTasks` for async pipeline. **Critical rule: every phase transition persists to DB before yielding. Never keep critical progress only in memory.**
- SQLAlchemy 2.x against SQLite for MVP.
- Mock mode default; live and cached layered in.
- Polling at 1.5-2s for scan progress.
- Sales-ready: total >= 70 AND >= 2 signals at conf >= 0.65 AND >= 2 unique evidence URLs.
- Outreach: drafts only.
- Cognee behind `MemoryService` wrapper, soft-fail.

---

## 3. Locked Decisions From Refinement Round

1. **Memory packets ship from Phase 2.** Every mock/live/cached scan writes through `MemoryService`.
2. **`scan_events` table added** for chronological trace ("SERP returned 6 results", "Unlocker fetched careers page", etc.).
3. **`scans.mode` enum is `mock | live | cached`** from day one. Cached is demo insurance, not afterthought.
4. **DB after every phase.** `BackgroundTasks` is fine for MVP, but progress must be durable.
5. **HTML parser:** `selectolax` (fast, simple) plus `beautifulsoup4` as fallback for tricky pages.
6. **AI/ML model picks (locked, with fallback rule):**
   - `AIML_EXTRACTION_MODEL=openai/gpt-4o-mini`
   - `AIML_BRIEFING_MODEL=openai/gpt-4o`
   - `AIML_DRAFT_MODEL=openai/gpt-4o-mini`
   - **Availability probe:** at first live use, run a tiny completion (1-2 token max output) against each configured model. Only fall back to `models.list()` if the gateway supports it. If a model rejects the probe, swap to the nearest GPT-4o-mini-compatible chat model for extraction/draft, and the strongest available reasoning/chat model for briefing. Logged at startup of first live scan, not at app boot.
7. **Bright Data smoke test** against `https://geo.brdtest.com/welcome.txt`. Runs **on first `mode=live` scan request** and via `make smoke` / `uv run smoke`. Not on every boot.
8. **Browser API fallback only.** Default path: SERP -> Unlocker.
9. **Speechmatics deferred** to Phase 8 only if Phases 0-7 are fully stable.
10. **Triggerware stays stubbed** behind feature flag.
11. **Cognee swap is implementation-only.** When key arrives, replace the inside of `MemoryService`. Pipeline does not change.
12. **Demo companies must have rich public careers/blog/docs pages.** No login walls. No LinkedIn.
13. **Definition of Done extras:** no secrets in logs or frontend responses; mock/cached/live use identical API contracts.
14. **HTTP client:** `httpx` async client for Bright Data calls so the runner doesn't block the event loop. Sync `requests` not used. The retry layer (`tenacity`) wraps async calls.
15. **Scan resume / staleness rule:** if a scan stays in any non-terminal phase for more than `SIGNALGRAPH_SCAN_PHASE_TIMEOUT_SECONDS` (default 300s), a watchdog marks it `failed` with `error_message="phase_timeout:<phase>"`. A `force_refresh=true` body field on `POST /accounts/{id}/scans` cancels and supersedes any in-flight scan for the same account. Resume picks up from the last persisted phase only on explicit operator action; default behavior is fail-fast.
16. **Sanitized event metadata:** `scan_events.metadata_json` may include zone name, target host, http status, ms, content-length. **Never** stores Browser WS URLs, query strings with auth, full target URLs with embedded credentials, bearer tokens, or proxy passwords.
17. **Cached mode honesty:** events emitted in `mode=cached` use `event_type` values like `bright_data_call_replayed`, `aiml_call_replayed`, `memory_write_replayed` and include `"replayed": true` in metadata. API response *shape* matches live, but the trace is honest.
18. **No SSE for MVP:** `GET /scans/{id}/events` returns plain JSON list. SSE only if Phases 0-7 are fully stable.

---

## 4. Repo Layout

```text
backend/
  pyproject.toml          # uv-managed
  .env                    # symlinked or copied from project root .env
  app/
    main.py
    config.py
    db.py
    deps.py
    models/               # SQLAlchemy ORM
      account.py
      person.py
      icp.py
      scan.py
      scan_event.py       # new: chronological trace
      source.py
      evidence.py
      signal.py
      score.py
      brief.py
      outreach.py
    schemas/              # Pydantic
    api/
      health.py
      imports.py
      accounts.py
      scans.py
      signals.py
      briefs.py
      outreach.py
    services/
      seed_importer.py
      source_discovery.py
      brightdata_client.py    # SERP + Unlocker REST
      browser_client.py       # Playwright CDP fallback
      scraper.py              # SERP -> Unlocker -> Browser fallback
      extractor.py            # AI/ML API JSON extraction
      memory_service.py       # MemoryService interface; JSONL impl now, Cognee later
      scorer.py
      briefing.py             # brief + outreach
      guardrails.py
      mock_fixtures.py
      cache_runner.py         # blessed-run cache replay
    jobs/
      scan_runner.py          # orchestrator, durable per-phase
    prompts/
      extract_signals.md
      generate_brief.md
      generate_outreach.md
  fixtures/
    seed_demo.csv
    mock_serp_results.json
    mock_scraped_pages/
    mock_extracted_signals.json
    blessed_runs/             # cached real scans for demo insurance
  var/
    memory/                   # JSONL packets per scan (MemoryService stub)
  tests/
```

---

## 5. Updated Domain Model Notes

### `scans.mode` enum
`mock | live | cached`

### `scan_events` (new)
Chronological trace per scan, surfaced via `GET /api/v1/scans/{id}` and `GET /api/v1/scans/{id}/events`.

Fields:
- `id`
- `scan_id`
- `sequence` (monotonic integer per scan)
- `phase` (`discovering`, `scraping`, `extracting`, `graphing`, `scoring`, `briefing`)
- `event_type` (`phase_started`, `phase_completed`, `bright_data_call`, `aiml_call`, `memory_write`, `warning`, `error`)
- `message` (human-readable)
- `metadata_json` (counts, ms, zone used, model ID, etc.)
- `created_at`

Rule: every external call (Bright Data, AI/ML API, MemoryService) writes one event. The frontend live panel renders these in real time.

---

## 6. Execution Phases

Each phase is independently demo-capable.

### Phase 0 - Scaffold & Health (~1-2 hours)

Goal: backend boots, health endpoint reports configured services without leaking secrets.

Deliverables:
- `uv` project with deps:
  - Core: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `alembic`, `python-multipart`, `python-dotenv`, `httpx`, `tenacity`, `structlog`
  - AI/data: `openai`, `markdownify`, `tldextract`, `selectolax`, `beautifulsoup4`
  - Browser fallback: `playwright`
  - Optional later: `speechmatics-batch`
  - Dev: `pytest`, `pytest-asyncio`, `respx`, `ruff`
- `app/config.py` reads `.env` via `pydantic-settings`. Credentials never logged.
- `app/db.py` initializes SQLite + Alembic baseline.
- `GET /health`:
  ```json
  {
    "status": "ok",
    "database": "ok",
    "bright_data_rest": "configured",
    "bright_data_browser": "configured",
    "aiml_api": "configured",
    "cognee": "not_configured",
    "mock_mode": true
  }
  ```
- Structured logging via `structlog`. Secret redaction filter.

Verification: `uvicorn app.main:app --reload` boots, `/health` returns the above.

---

### Phase 1 - Domain Model + Seed Import (~2-3 hours)

Goal: importing the demo CSV creates accounts, people, ICP rows. `scan_events` table exists.

Deliverables:
- ORM models matching Section 6 of `backend_implementation_plan.md` plus the new `scan_events` table and `scans.mode` enum (`mock | live | cached`).
- `fixtures/seed_demo.csv`: 5 target/customer accounts, 3 champions, 1 ICP profile.
- `POST /api/v1/import/seed` (multipart CSV) -> upserts.
- `GET /api/v1/accounts` (filter, paginate).
- `GET /api/v1/accounts/{id}` (detail; signals/brief sections initially empty).

Tests: import is idempotent; account upsert by domain works; people upsert by email works.

---

### Phase 2 - Mock Scan Runner + MemoryService Stub (~3-4 hours)

Goal: full pipeline runs end-to-end with zero external calls. **MemoryService writes packets from day one.**

Deliverables:
- `services/memory_service.py`:
  - Interface: `remember(packet)`, `query(question) -> list`.
  - Default JSONL implementation writes `var/memory/scan_<id>.jsonl`.
  - Each remember call also writes a `memory_write` `scan_event`.
- `POST /api/v1/accounts/{id}/scans` creates a `scans` row, persists state, then dispatches via `BackgroundTasks`.
- `jobs/scan_runner.py` walks states `queued -> discovering -> scraping -> extracting -> graphing -> scoring -> briefing -> completed`.
  - Durable: every state change is committed before the next phase starts.
  - Every phase emits `phase_started` and `phase_completed` events.
  - In mock mode, fixtures drive each phase.
- `GET /api/v1/scans/{id}` returns status, progress, current phase, counts, errors.
- `GET /api/v1/scans/{id}/events` returns the scan_events list.
- All read endpoints from Section 9 of the plan (`/sources`, `/evidence`, `/signals`, `/brief`, `/outreach/*`).

Verification: trigger a mock scan, poll `/scans/{id}` every 1.5s, observe full lifecycle, confirm signals + brief + outreach + memory packets exist.

---

### Phase 3 - Live Discovery + Live Scraping via Bright Data (~3-4 hours)

Goal: real SERP results and real evidence fetched from public web.

Deliverables:
- `services/brightdata_client.py`:
  - `serp_search(query)` -> POST to `BRIGHT_DATA_API_ENDPOINT` with `BRIGHT_DATA_SERP_ZONE`.
  - `unlock_url(url)` -> same endpoint, `BRIGHT_DATA_UNLOCKER_ZONE`.
  - Retry via `tenacity` (3 attempts, exponential backoff). One `bright_data_call` event per attempt with zone, URL, ms, http status.
- `services/source_discovery.py`:
  - 4-8 queries per account using ICP keywords, competitor keywords, account name.
  - Parses SERP HTML with `selectolax` (BeautifulSoup fallback) to extract candidate URLs.
  - Canonicalizes + dedupes via `tldextract` + URL normalization.
  - Ranks: company-domain first, then careers/blog/docs, then GitHub, then news.
  - Limits to 5-10 sources per scan.
- `services/scraper.py`:
  - For each source: try Web Unlocker first. If response is thin/blocked or content looks JS-required, fall back to Browser API.
  - Convert HTML to markdown via `markdownify`.
  - Store `content_hash` for dedup; record `fetch_method` per row.
  - One source failure does not fail the scan.
- **Smoke test:** an integration test calling `unlock_url("https://geo.brdtest.com/welcome.txt")` to confirm bearer auth without using real-account credits. Run as part of `make smoke` and as a startup-time sanity check when `live` mode is requested.
- Live mode gated by `SIGNALGRAPH_MOCK_MODE=false` and per-scan `mode=live`. Mock mode still works.

Verification: against a seeded real company in `live` mode, SERP returns real Google results and Unlocker fetches at least 3 of them. All recorded in `scan_events`.

---

### Phase 4 - Live AI Extraction + Briefing via AI/ML API (~3 hours)

Goal: real signal extraction, real account briefs, real outreach drafts.

Deliverables:
- `services/extractor.py`:
  - `openai` SDK pointed at `AIML_API_BASE_URL` with `AIML_API_KEY`.
  - `chat.completions.create` with `response_format={"type": "json_object"}` against `AIML_EXTRACTION_MODEL`.
  - Loads `prompts/extract_signals.md`, injects markdown content + account context.
  - Validates JSON via Pydantic. Drops signals missing `evidence_url`, with `confidence < 0.45`, or flagged sensitive.
  - Each call writes one `aiml_call` event with model ID, prompt size, response tokens, ms.
- `services/briefing.py`:
  - `generate_brief` -> `AIML_BRIEFING_MODEL`. Pulls signals + scores + `MemoryService.query()` for graph context (tolerates empty results).
  - `generate_outreach` -> `AIML_DRAFT_MODEL`. Calls `guardrails.check_outreach` before persisting.
- `services/guardrails.py`:
  - Rejects "I saw you...", competitor mentions without supporting evidence URL, sensitive personal claims, fabricated familiarity.
  - Returns warnings persisted to `outreach_drafts.guardrail_notes_json`.
- Startup model availability check: at first live scan, list models via the SDK and confirm the three configured IDs are reachable. Fall back per the rule in Section 3 #6 with a logged warning.

Verification: live scan returns at least 3 signals with valid `evidence_url`; brief and outreach are coherent and cite signals; guardrails active.

---

### Phase 5 - Scoring + Sales-Ready Logic (~2 hours)

Goal: scores reflect the locked rules.

Deliverables:
- `services/scorer.py`:
  - Fit (0-30): keyword overlap between account metadata and ICP `tech_keywords`, `industries`, `company_sizes`, `regions`.
  - Timing (0-30): based on signal types (`hiring`, `migration`, `funding`, `product_launch`, `leadership_change`) and recency.
  - Relationship (0-20): champion proximity, prior customer pattern.
  - Evidence (0-20): unique source domains, average extraction confidence, source-type quality.
  - `sales_ready = total >= 70 AND signals_with_conf_ge_0.65 >= 2 AND unique_evidence_urls >= 2`.
  - Near-miss band 55-69 surfaced via `/signals?sales_ready=false&min_total_score=55`.
  - Stores `score_reasoning_json` so the brief can quote rationale.

Verification: unit tests on boundary conditions.

---

### Phase 6 - Cached Mode (Blessed-Run Cache) (~2 hours)

Goal: demo insurance. Replay a known-good real scan if live conditions are flaky.

Deliverables:
- `services/cache_runner.py`:
  - When `mode=cached`, reads from `fixtures/blessed_runs/<account_id>.json` and replays sources/evidence/signals/score/brief/outreach into the DB and `scan_events`, with realistic timing.
  - Identical API contracts as `live` and `mock`.
- A small CLI `python -m app.scripts.snapshot_run --scan-id <id>` writes the current scan results into `fixtures/blessed_runs/<account_id>.json`.
- After Phases 3-5 produce a clean live scan, run the snapshot once for each demo account.

Verification: deleting all live integrations, running `mode=cached` returns the same shape responses as `live` did.

---

### Phase 7 - Demo Polish (~3-4 hours)

Goal: demo doesn't fall apart.

Deliverables:
- Per-phase progress messages already covered by `scan_events`. Polish wording so the frontend live panel reads cleanly.
- `POST /api/v1/scans/{id}/brief/regenerate` reuses stored evidence + memory.
- `/scans/{id}` includes summary counts (`bright_data_calls`, `aiml_api_calls`, `memory_writes`) so judges see live integration usage.
- Secret redaction audited: confirm no API keys, no zone passwords, no Browser WS auth in any log line, response, or event payload.
- Mock/cached/live API parity smoke test: hit each mode against the same account and assert response shapes match.

---

### Phase 8 - Stretch (Cognee, Speechmatics, Triggerware, Champion Mobility)

Only attempted if Phases 0-7 are stable.

- **Cognee:** when key arrives, swap the inside of `MemoryService` to write to Cognee datasets `signalgraph_seed`, `signalgraph_signals`, `signalgraph_scan_<id>`. Wrapper preserves soft-fail. Pipeline unchanged.
- **Speechmatics:** `POST /api/v1/notes` accepts an audio file, transcribes via batch API, writes a memory packet, `scan_event` of type `memory_write` with source `voice_note`.
- **Triggerware:** stays stubbed unless API shape becomes clear.
- **Champion Mobility:** dedicated discovery queries targeting champion names + new public-facing pages.

---

## 7. Sequencing Plan

| Day | Hours | Phase |
|---|---|---|
| 0 | 1-2 | Phase 0: Scaffold + health |
| 0 | 2-3 | Phase 1: Models + seed import + scan_events table |
| 1 AM | 3-4 | Phase 2: Mock scan runner + MemoryService stub |
| 1 PM | 3-4 | Phase 3: Live Bright Data SERP + Unlocker (with smoke test) |
| 1 PM / 2 AM | 3 | Phase 4: Live AI/ML extraction + briefing |
| 2 AM | 2 | Phase 5: Scoring polish |
| 2 PM | 2 | Phase 6: Cached mode + snapshot CLI |
| 2 PM / 3 | 3-4 | Phase 7: Demo polish + parity tests |
| post | as time | Phase 8: Cognee + Speechmatics + Triggerware + Champion Mobility |

---

## 8. Verification Strategy

- Each phase has a `make demo-phaseN` (or `uv run`) command exercising the relevant flow.
- Unit tests: seed import idempotency, URL canonicalization + dedup, scorer boundaries, guardrail rejections, mock fixture loading, secret-redaction filter.
- Integration smoke for Phase 3: `unlock_url("https://geo.brdtest.com/welcome.txt")`.
- Integration smoke for Phase 4: tiny extraction call against fixed prompt + tiny content, asserting JSON parse.
- Parity test in Phase 7: same account, three modes, assert API response shapes match.

---

## 9. What I Need From You Before Live Mode

Mock mode runs without any of this. To flip to live in Phase 3+:

- [ ] Confirm `.env` has the three locked AI/ML model IDs (I will write defaults and you can edit if your dashboard shows otherwise).
- [ ] Confirm Bright Data zones (`champion_serp_api`, `champion_unlocker_api`, `champion_browser_api`) are active with a spend cap. Smoke test at startup will verify reachability.
- [ ] Five real public companies with rich public careers/blog/docs (no login, no LinkedIn). I can pick public defaults if you'd rather.
- [ ] Decide if Speechmatics endpoint is worth Phase 8 time (default: skip).

Cognee and Triggerware do not block any phase.

---

## 10. Risk Register

| Risk | Mitigation |
|---|---|
| Bright Data SERP HTML parsing fragility | `selectolax` first with multiple selectors; BeautifulSoup fallback; raw-link extraction last |
| AI/ML model deprecation/availability | Startup availability check; fallback rule to nearest GPT-4o-mini and strongest reasoning model |
| Live demo internet failure | `mode=cached` blessed-run replay; identical API contracts |
| Bright Data credit burn during dev | Mock mode default; explicit `mode=live` per scan; spend cap; smoke test against `geo.brdtest.com` |
| Cognee absence weakening pitch story | MemoryService writes JSONL packets visible in logs; brief still cites evidence |
| Triggerware shape unknown | Feature-flagged stub, no critical-path dependency |
| LinkedIn TOS risk | Excluded entirely |
| BackgroundTasks losing in-flight progress | Every phase commits to DB before yielding; runner can resume from last persisted state |
| Secret leakage | structlog redaction filter; Phase 7 audit; no env values returned from API |

---

## 11. Definition Of Done For Hackathon Demo

- `POST /import/seed` loads `seed_demo.csv` end-to-end.
- `POST /accounts/{id}/scans` with `mode=live` triggers a scan that:
  - Calls Bright Data SERP at least once (logged + scan_event).
  - Calls Bright Data Web Unlocker at least 3 times (logged + scan_event).
  - Calls AI/ML API for extraction + briefing + draft (logged + scan_event).
  - Persists >= 3 signals with valid evidence URLs.
  - Produces a brief with citations.
  - Produces an outreach draft in `pending_review` passing guardrails.
  - Writes memory packets via `MemoryService` (visible in logs/disk now, in Cognee later).
- `GET /scans/{id}` reflects progress every 1.5s.
- `GET /scans/{id}/events` returns chronological trace.
- `GET /accounts/{id}/brief` and `GET /outreach/pending` return correct payloads.
- `mode=mock` and `mode=cached` return identical response shapes to `mode=live`.
- No secrets in any log line, response body, or `scan_event` payload.
- `mock` flow works without any external keys.
