# SignalGraph - External Credentials & Setup Required

**Owner:** You (and anyone helping you collect keys)
**Builder:** Backend implementation begins in mock mode immediately. Live integrations are wired in as you deliver each row below.
**Format:** Each row lists the value name, where to get it, the env variable it maps to, and whether it blocks the live demo (mock works without it).

> Mock mode rule: every value below can be left blank during initial development. The backend boots, scans run end-to-end, and the demo flow works using fixtures. Live integration is unlocked row by row as you fill these in.

---

## 1. Bright Data

You'll need a Bright Data account with at least one zone configured. Track 1 typically requires showing one Bright Data product live; we plan to use SERP + scrape_as_markdown via MCP at minimum.

| # | Item | Env variable | How to get it | Required for live? |
|---|---|---|---|---|
| 1.1 | Bright Data account | n/a | Sign up at brightdata.com | Yes |
| 1.2 | API key (account token) | `BRIGHT_DATA_API_KEY` | Account Settings → API token | Yes |
| 1.3 | MCP Server URL or local command | `BRIGHT_DATA_MCP_URL` | Bright Data MCP docs; can also run via `npx @brightdata/mcp` locally | Yes (preferred path) |
| 1.4 | SERP zone name | `BRIGHT_DATA_SERP_ZONE` | Control panel → Proxies & Scrapers → create a SERP API zone, copy zone name | Yes (source discovery) |
| 1.5 | Web Unlocker zone name | `BRIGHT_DATA_UNLOCKER_ZONE` | Control panel → create a Web Unlocker zone | Yes (fallback scraping) |
| 1.6 | Scraping Browser WebSocket endpoint | `BRIGHT_DATA_BROWSER_WS` | Control panel → Scraping Browser zone → connection string | Optional (only for JS-heavy pages) |
| 1.7 | Web Scraper API endpoints (if used) | `BRIGHT_DATA_SCRAPER_*` | Control panel → Web Scraper API marketplace | Optional |
| 1.8 | Allowed monthly budget / spend cap | n/a (note for safety) | Set a hard cap in the dashboard so live testing can't burn credits | Strongly recommended |

**Action items for you:**
- Create the account.
- Provision one SERP zone and one Web Unlocker zone with default settings.
- Enable a small monthly cap so testing is safe.
- Capture the API key, MCP details, and zone names.

---

## 2. AI/ML API (model gateway)

Used for extraction, briefing, and outreach drafts. OpenAI-compatible interface.

| # | Item | Env variable | How to get it | Required for live? |
|---|---|---|---|---|
| 2.1 | AI/ML API account | n/a | Sign up at aimlapi.com | Yes |
| 2.2 | API key | `AIML_API_KEY` | Dashboard → API keys | Yes |
| 2.3 | Base URL | `AIML_API_BASE_URL` | Default `https://api.aimlapi.com/v1` | Yes (default works) |
| 2.4 | Extraction model ID | `AIML_EXTRACTION_MODEL` | Pick a JSON-stable model (e.g. a strong open-weight or GPT-class model from their list) | Yes |
| 2.5 | Briefing model ID | `AIML_BRIEFING_MODEL` | Pick a stronger reasoning model | Yes |
| 2.6 | Draft model ID | `AIML_DRAFT_MODEL` | Pick a fast/cheap model | Yes |
| 2.7 | Spending limit | n/a | Set a per-month cap if available | Recommended |

**Action items for you:**
- Sign up, grab the API key.
- Browse their available models and pick three model IDs (I can suggest defaults from their docs once we hit this step).

---

## 3. Cognee (memory + graph)

Used as graph memory. Backend works without Cognee thanks to the wrapper, but the demo story is much weaker without it.

| # | Item | Env variable | How to get it | Required for live? |
|---|---|---|---|---|
| 3.1 | Hosted account OR self-hosted decision | n/a | cognee.ai (hosted) or run locally via their Python SDK | Yes |
| 3.2 | API key (if hosted) | `COGNEE_API_KEY` | Cognee dashboard | If hosted |
| 3.3 | Base URL (if non-default) | `COGNEE_API_URL` | Cognee docs | Optional |
| 3.4 | Dataset prefix | `COGNEE_DATASET_PREFIX` | Default `signalgraph` | No (default works) |
| 3.5 | Embedding/LLM credentials Cognee may need | varies | Some Cognee setups want their own OpenAI/embedding keys | Depends on chosen mode |

**Action items for you:**
- Decide hosted vs self-hosted (hosted is faster to integrate).
- If hosted, grab the API key.
- If self-hosted, confirm your machine can run their stack and we'll wire it locally.

---

## 4. Database (only if not using SQLite)

Default plan is SQLite, no setup needed.

| # | Item | Env variable | When you'd need it |
|---|---|---|---|
| 4.1 | Postgres connection string | `DATABASE_URL` | Only if you switch from SQLite to Supabase/Postgres |
| 4.2 | Supabase project URL + keys | n/a in backend yet | If we extend to Supabase auth/storage later |

**Action items for you:** none unless you want Postgres now.

---

## 5. Optional Integrations

Only chase these if there's spare time. They make the pitch fuller but are not on the critical path.

| # | Item | Env variable | Why we'd use it |
|---|---|---|---|
| 5.1 | Speechmatics API key | `SPEECHMATICS_API_KEY` | Voice-note ingestion → Cognee account memory |
| 5.2 | Triggerware.ai access | `TRIGGERWARE_API_KEY` | Scheduled scans + threshold-based notifications |

---

## 6. Repo / Deploy Settings (only if we deploy)

Default plan: run locally during development and demo.

| # | Item | Env variable | When you'd need it |
|---|---|---|---|
| 6.1 | Hosting platform decision | n/a | If we deploy: Render, Fly, Railway, or a VPS |
| 6.2 | CORS allowed origins | `CORS_ALLOWED_ORIGINS` | Once frontend has a deployed URL |
| 6.3 | Public backend URL | n/a | Frontend `NEXT_PUBLIC_API_URL` value, set on the frontend side |

---

## 7. Demo Content You Need To Pick (not credentials but blocks live polish)

| # | Item | Notes |
|---|---|---|
| 7.1 | Final fictional vendor name | Default `VectorLake`. Override anytime. |
| 7.2 | 5 real public companies for live scraping targets | Mix of fintech / dev-tools / retail-tech / healthtech preferred |
| 7.3 | 3 real public engineers as champions | Need public GitHub or blog to give Bright Data something to find |
| 7.4 | ICP rule values (industries, sizes, regions, roles, tech keywords, pain keywords, competitor keywords) | 5–10 each |
| 7.5 | Source policy confirmation | Default: LinkedIn off, prioritize company sites, careers, eng blogs, GitHub, news, docs |

> If you don't pick these, I'll seed the fixtures with plausible defaults so mock mode works. You swap them when you're ready.

---

## 8. Single Master `.env` Template

Once you start collecting keys, drop them into this file at `backend/.env`:

```env
APP_ENV=development
DATABASE_URL=sqlite:///./signalgraph.db
SIGNALGRAPH_MOCK_MODE=true

# Bright Data
BRIGHT_DATA_API_KEY=
BRIGHT_DATA_MCP_URL=
BRIGHT_DATA_SERP_ZONE=
BRIGHT_DATA_UNLOCKER_ZONE=
BRIGHT_DATA_BROWSER_WS=

# AI/ML API
AIML_API_KEY=
AIML_API_BASE_URL=https://api.aimlapi.com/v1
AIML_EXTRACTION_MODEL=
AIML_BRIEFING_MODEL=
AIML_DRAFT_MODEL=

# Cognee
COGNEE_API_KEY=
COGNEE_API_URL=
COGNEE_DATASET_PREFIX=signalgraph

# Optional
SPEECHMATICS_API_KEY=
TRIGGERWARE_API_KEY=

# CORS (set once frontend exists)
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

Flip `SIGNALGRAPH_MOCK_MODE=false` only after the relevant keys for the path you're testing are filled.

---

## 9. Suggested Order Of Acquisition

To unblock live demo fastest, collect in this order:

1. Bright Data API key + SERP zone + Unlocker zone (1.2, 1.4, 1.5)
2. AI/ML API key + 3 model IDs (2.2, 2.4–2.6)
3. Cognee key (or local setup confirmation) (3.1, 3.2)
4. Bright Data MCP setup (1.3) — if MCP is finicky, we can skip it and call SERP/Unlocker directly
5. Bright Data Browser WS (1.6) — only if a target page truly needs JS rendering
6. Optional: Speechmatics, Triggerware

---

## 10. Status Tracking

Mark each row as you complete it. Send me the values via your secure channel of choice (don't paste in chat unless you're okay with that).

- [ ] 1.1 Bright Data account
- [ ] 1.2 `BRIGHT_DATA_API_KEY`
- [ ] 1.3 `BRIGHT_DATA_MCP_URL`
- [ ] 1.4 `BRIGHT_DATA_SERP_ZONE`
- [ ] 1.5 `BRIGHT_DATA_UNLOCKER_ZONE`
- [ ] 1.6 `BRIGHT_DATA_BROWSER_WS` (optional)
- [ ] 1.8 Spend cap configured
- [ ] 2.1 AI/ML API account
- [ ] 2.2 `AIML_API_KEY`
- [ ] 2.4 `AIML_EXTRACTION_MODEL`
- [ ] 2.5 `AIML_BRIEFING_MODEL`
- [ ] 2.6 `AIML_DRAFT_MODEL`
- [ ] 3.1 Cognee mode chosen (hosted/self-hosted)
- [ ] 3.2 `COGNEE_API_KEY` (if hosted)
- [ ] 4.1 `DATABASE_URL` (only if not SQLite)
- [ ] 5.1 `SPEECHMATICS_API_KEY` (optional)
- [ ] 5.2 `TRIGGERWARE_API_KEY` (optional)
- [ ] 7.x Demo content picks
