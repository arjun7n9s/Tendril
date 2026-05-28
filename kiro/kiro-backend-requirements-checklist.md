# SignalGraph Backend - Requirements Checklist

**Purpose:** Gather everything needed before we start coding the backend described in `codex-backend-implementation-plan.md`.
**Status legend:** [ ] pending  · [x] decided  · [~] default assumed, confirm if different

> Updated after your answers in `codex-backend-implementation-plan.md` Section 19. Locked decisions are marked. Open items have safe defaults so we are not blocked.

---

## A. Decisions & Inputs From You

### A1. Core stack confirmations

- [~] **Python version** — `3.11` (default; override anytime)
- [x] **MVP database** — SQLite, SQLAlchemy in place so we can move to Supabase/Postgres later
- [~] **Dev/demo OS** — Windows local for development; deploy decision deferred (default: run locally for demo)
- [~] **Frontend stack** — Next.js per blueprint (default; override anytime)
- [~] **Repo layout** — backend at `./backend/` inside this `BrightData` folder (default)
- [~] **Package manager** — `uv` (default; override anytime)

### A2. API keys & accounts you must obtain

Full list moved to `kiro-external-credentials-required.md`. Mock mode covers build phase if any are missing.

Quick tracking:
- [ ] Bright Data API key + zones (1.2, 1.4, 1.5)
- [ ] Bright Data MCP setup (1.3)
- [ ] AI/ML API key + 3 model IDs (2.2, 2.4–2.6)
- [ ] Cognee key or self-hosted setup (3.1, 3.2)
- [ ] Speechmatics key (optional)
- [ ] Triggerware access (optional)

### A3. Demo content decisions

- [~] **Final fictional vendor name** — `VectorLake` (default; override anytime)
- [ ] **5 real public companies** for target accounts — I'll seed plausible defaults; replace before live demo
- [ ] **3 prior champion identities** — I'll seed defaults; replace with real public engineers before live demo
- [ ] **ICP rules** — I'll seed defaults; you can tune any time
  - [ ] industries
  - [ ] company sizes
  - [ ] regions
  - [ ] target roles
  - [ ] tech keywords
  - [ ] pain keywords
  - [ ] competitor keywords
- [~] **Source policy** — LinkedIn optional-only; prioritize company sites, careers, eng blogs, GitHub, news, docs (default)

### A4. Scope toggles

- [x] **Champion Mobility loop** — Phase 2/3
- [x] **Lookalike Discovery** — Phase 2/3
- [x] **Live progress** — polling every 1.5–2s; SSE later
- [x] **Auth** — none for hackathon single-user demo
- [x] **CRM writeback / webhooks** — out of scope for MVP

### A5. Demo logistics

- [~] **Internet reliability** — cache one "blessed" live scan as fallback (default: yes, will add)
- [ ] **Demo slot duration** — confirm when you know

---

## B. From The Internet (I'll Fetch During Build)

These I'll pull myself, flagging so you know what I'll reference:

- [ ] Bright Data MCP Server tool list — https://docs.brightdata.com/ai/mcp-server/tools
- [ ] Bright Data SERP API request shape + zone semantics
- [ ] Bright Data Web Unlocker API payload + auth
- [ ] Bright Data Scraping Browser WebSocket pattern (Playwright/Puppeteer)
- [ ] Cognee `remember()` + dataset/query APIs — https://docs.cognee.ai/core-concepts/main-operations/remember
- [ ] AI/ML API OpenAI-compatible endpoints + current model IDs — https://docs.aimlapi.com
- [ ] Speechmatics (only if voice notes added)

Will verify Python SDK compatibility at install time.

---

## C. To Download / Install (Dev Environment)

### C1. System-level

- [ ] **Python 3.11+** — I'll check during scaffold
- [ ] **Git** — assumed installed
- [~] **uv** — default; will install if missing
- [ ] **(Optional) Docker Desktop** — only for containerized Postgres or container deploy
- [ ] **(Optional) Node.js 20+** — needed if MCP runs via `npx @brightdata/mcp`

### C2. Python packages (planned `requirements.txt`)

**Core**
- `fastapi`
- `uvicorn[standard]`
- `pydantic` (v2)
- `pydantic-settings`
- `sqlalchemy` (v2.x)
- `alembic`
- `python-multipart`
- `httpx`
- `python-dotenv`
- `tenacity`
- `structlog`

**AI / data**
- `openai` (AI/ML API is OpenAI-compatible)
- `cognee`
- `markdownify` or `readability-lxml`
- `tldextract`, `urlcanon`

**Bright Data**
- MCP server runs as separate process (`npx @brightdata/mcp` or similar) via stdio/HTTP — wrap in thin client
- SERP / Unlocker called via REST with `httpx`, no SDK needed

**Dev**
- `pytest`, `pytest-asyncio`, `respx`
- `ruff`, `mypy` (optional)

### C3. Fixtures to seed before build

I'll author all of these from the demo story; you can edit anytime.

- [ ] `fixtures/seed_demo.csv` — 5 accounts, 3 champions, 2 ICP examples
- [ ] `fixtures/mock_serp_results.json` — synthetic SERP responses
- [ ] `fixtures/mock_scraped_pages/` — 5–10 markdown files (careers, blog, news, GitHub README, docs)
- [ ] `fixtures/mock_extracted_signals.json` — pre-computed signals for fully offline runs

---

## D. Open Risks To Flag

1. **Bright Data MCP version drift** — tool names evolve. Lock to specific MCP version once installed.
2. **Cognee local vs hosted** — wrap behind circuit breaker so backend keeps working with `graph_update` warnings if hosted is flaky.
3. **AI/ML API model availability** — model IDs change. Pick at install time, store in env.
4. **Live demo failure** — caching a "good run" so we can fall back mid-demo invisibly.
5. **LinkedIn scraping** — out of scope unless Bright Data zone with terms-compliant access is confirmed. Default: skip.

---

## E. Locked Decisions Summary (from your Section 19)

- Task queue: FastAPI `BackgroundTasks`, no Celery/Redis
- DB: SQLite + SQLAlchemy
- Mock mode first, real integrations layered in
- Bright Data priority: MCP → SERP → scrape_as_markdown / Unlocker → Browser API → Web Scraper API
- Cognee behind a wrapper, soft-fail with `graph_update_warning`
- Polling at 1.5–2s
- Sales-ready: total ≥ 70 AND ≥ 2 signals at conf ≥ 0.65 AND ≥ 2 unique evidence URLs; near-miss 55–69
- Outreach drafts only, never sent
- Credentials list maintained separately at `kiro-external-credentials-required.md`

---

## F. Unblocked-To-Start Status

I have everything I need to start scaffolding right now, in mock mode, using the defaults above. As you fill in `kiro-external-credentials-required.md`, we wire live integrations one at a time without blocking.

Say the word and I'll begin Phase 1.
