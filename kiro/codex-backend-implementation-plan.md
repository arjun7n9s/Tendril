# SignalGraph Backend Implementation Plan

**Audience:** Backend engineering team  
**Product:** SignalGraph - Autonomous GTM Change Intelligence  
**Track:** Bright Data Web Data UNLOCKED Hackathon, Track 1 GTM Intelligence  
**Goal:** Build a reliable backend that turns live public web evidence into scored GTM signals, account briefs, and human-reviewable outreach drafts.

## 1. Backend Outcome

The backend should support this demo flow end to end:

1. Import seed CRM/ICP data.
2. Select a target account from the dashboard.
3. Trigger a live Bright Data scan.
4. Discover and scrape public evidence sources.
5. Extract structured GTM signals from the scraped content.
6. Store raw evidence, extracted signals, and relationships.
7. Push memory into Cognee.
8. Score the account against fit, timing, relationship, and evidence quality.
9. Generate an account brief and safe outreach draft.
10. Expose all results to the frontend with citations and scan progress.

The MVP must feel live, explainable, and safe. It does not need a full production CRM integration or automated email sending.

## 2. Recommended Stack

Use a Python backend because Cognee, scraping workflows, data extraction, and AI orchestration are easier to move quickly in Python.

- **API framework:** FastAPI
- **App database:** SQLite for local hackathon MVP, PostgreSQL/Supabase if already available
- **ORM:** SQLAlchemy 2.x
- **Validation:** Pydantic v2
- **Background jobs:** FastAPI `BackgroundTasks` or an in-process async job runner for MVP
- **Production-ready queue later:** Celery/RQ + Redis
- **AI model gateway:** AI/ML API, OpenAI-compatible client
- **Web data layer:** Bright Data MCP Server first; SERP API, Unlocker, Browser API, or Web Scraper API as fallback/specialized paths
- **Memory/graph layer:** Cognee
- **Runtime config:** `.env`

For the hackathon, avoid Redis/Celery unless the team already has it wired. A simple jobs table plus an async worker function is easier to deploy and demo.

## 3. Non-Negotiable Product Constraints

- Every generated claim must be backed by at least one evidence URL.
- The system must distinguish facts, inferences, and recommendations.
- Outreach drafts are never auto-sent.
- LinkedIn must not be the single source of truth.
- Prefer account-level triggers over personal surveillance.
- Store raw scraped content or normalized markdown for audit/debug.
- Include a mock mode to avoid burning credits during development.

## 4. System Boundaries

### Backend Owns

- Seed import and normalization.
- Bright Data source discovery and scraping.
- AI extraction into structured JSON.
- App database persistence.
- Cognee ingestion and graph query wrapper.
- Signal scoring.
- Brief and outreach generation.
- Approval workflow state.
- Scan status and progress events.

### Frontend Owns

- Dashboard layout.
- Account selection.
- Scan trigger button.
- Live progress display.
- Signal cards.
- Brief and outreach review UI.
- Approval/rejection actions.

### External Services

- Bright Data: live web access.
- Cognee: memory and graph reasoning.
- AI/ML API: extraction, summarization, and draft generation.
- Triggerware.ai: optional future automation layer.
- Speechmatics: optional voice note ingestion.

## 5. MVP Architecture

```text
Frontend
  |
  | REST API
  v
FastAPI Backend
  |
  |-- App DB: accounts, people, scans, sources, evidence, signals, scores, drafts
  |
  |-- Bright Data Client
  |     |-- SERP / search discovery
  |     |-- scrape_as_markdown or Unlocker
  |     |-- Browser API for JS-heavy fallback
  |
  |-- Extraction Service
  |     |-- AI/ML API strict JSON extraction
  |
  |-- Cognee Service
  |     |-- remember seed data
  |     |-- remember extracted evidence/signals
  |     |-- query graph context
  |
  |-- Scoring Service
  |
  |-- Briefing Service
        |-- account brief
        |-- safe outreach draft
```

## 6. Core Domain Model

Use relational tables for app state and Cognee for memory/graph reasoning. Do not make the frontend query Cognee directly.

### `accounts`

Represents companies being tracked.

Fields:
- `id`
- `name`
- `domain`
- `industry`
- `company_size`
- `region`
- `status`: `target`, `customer`, `former_customer`, `competitor`, `ignored`
- `metadata_json`
- `created_at`
- `updated_at`

### `people`

Represents champions, contacts, or public authors.

Fields:
- `id`
- `full_name`
- `current_company_id`
- `previous_company_id`
- `title`
- `email`
- `public_profile_url`
- `github_url`
- `personal_site_url`
- `role_type`: `champion`, `buyer`, `technical_user`, `unknown`
- `metadata_json`
- `created_at`
- `updated_at`

### `icp_profiles`

Represents ideal-customer rules used for fit scoring.

Fields:
- `id`
- `name`
- `industries_json`
- `company_sizes_json`
- `regions_json`
- `target_roles_json`
- `tech_keywords_json`
- `pain_keywords_json`
- `competitor_keywords_json`
- `created_at`
- `updated_at`

### `scans`

Represents a live or cached intelligence run.

Fields:
- `id`
- `account_id`
- `scan_type`: `account_watchtower`, `champion_mobility`, `lookalike_discovery`
- `status`: `queued`, `discovering`, `scraping`, `extracting`, `graphing`, `scoring`, `briefing`, `completed`, `failed`
- `mode`: `live`, `mock`
- `progress_percent`
- `error_message`
- `started_at`
- `completed_at`
- `created_at`
- `updated_at`

### `sources`

Candidate URLs discovered for a scan.

Fields:
- `id`
- `scan_id`
- `account_id`
- `url`
- `source_type`: `company_site`, `careers`, `blog`, `news`, `github`, `docs`, `serp_result`, `review`, `public_profile`, `other`
- `discovery_query`
- `rank`
- `selected_for_scrape`
- `created_at`

### `evidence_documents`

Fetched content from a source.

Fields:
- `id`
- `scan_id`
- `source_id`
- `account_id`
- `url`
- `title`
- `content_markdown`
- `content_hash`
- `fetched_at`
- `fetch_status`: `success`, `failed`, `skipped`
- `fetch_method`: `brightdata_mcp`, `serp_api`, `unlocker`, `browser_api`, `web_scraper_api`, `mock`
- `http_status`
- `metadata_json`

### `signals`

Structured GTM findings extracted from evidence.

Fields:
- `id`
- `scan_id`
- `account_id`
- `person_id`
- `signal_type`: `hiring`, `tech_stack`, `migration`, `funding`, `product_launch`, `leadership_change`, `competitor_mention`, `champion_move`, `market_event`, `other`
- `title`
- `summary`
- `fact_text`
- `inference_text`
- `recommended_action`
- `evidence_url`
- `evidence_document_id`
- `observed_at`
- `confidence`: float `0.0-1.0`
- `recency_days`
- `metadata_json`
- `created_at`

### `scores`

Computed actionability score for an account scan.

Fields:
- `id`
- `scan_id`
- `account_id`
- `fit_score`: integer `0-30`
- `timing_score`: integer `0-30`
- `relationship_score`: integer `0-20`
- `evidence_score`: integer `0-20`
- `total_score`: integer `0-100`
- `sales_ready`: boolean
- `score_reasoning_json`
- `created_at`

### `briefs`

AI-generated account brief.

Fields:
- `id`
- `scan_id`
- `account_id`
- `title`
- `executive_summary`
- `why_now`
- `key_evidence_json`
- `risks_json`
- `recommended_next_steps_json`
- `created_at`

### `outreach_drafts`

Human-reviewable outreach copy.

Fields:
- `id`
- `scan_id`
- `account_id`
- `person_id`
- `subject`
- `body`
- `tone`: `warm`, `technical`, `executive`, `concise`
- `status`: `pending_review`, `approved`, `rejected`, `edited`
- `guardrail_notes_json`
- `reviewer_feedback`
- `created_at`
- `updated_at`

## 7. Seed Import Contract

Support CSV upload first. JSON import can come later.

Required CSV columns:

```csv
record_type,account_name,account_domain,industry,company_size,person_name,title,email,previous_company,role_type,github_url,personal_site_url,tech_keywords,outcome_notes
```

Allowed `record_type` values:
- `target_account`
- `customer_account`
- `champion`
- `icp_example`

Import behavior:
- Create or update accounts by `account_domain` when present, otherwise by normalized name.
- Create or update people by email when present, otherwise by normalized name plus previous/current company.
- Store tech keywords and outcome notes as metadata.
- Push a normalized seed summary into Cognee after relational import succeeds.

## 8. Scan Pipeline

### Step 1: Create Scan

Endpoint creates a `scans` row with `queued` status and returns `scan_id`.

### Step 2: Source Discovery

Generate 4-8 targeted queries per account. Example:

- `{account_name} careers data platform Kafka Snowflake`
- `{account_name} engineering blog data infrastructure`
- `{account_name} migration data platform`
- `{account_name} {competitor_keyword}`
- `site:{account_domain} data platform`
- `site:github.com {account_name} data`

Use Bright Data MCP/search or SERP API to collect candidate URLs.

Selection rules:
- Keep official company pages highest.
- Keep careers, engineering blog, docs, GitHub, and reputable news.
- Deprioritize low-quality aggregators.
- Deduplicate by canonical URL.
- Limit MVP scrape count to 5-10 sources per scan.

### Step 3: Scrape Evidence

Fetch selected sources using this order:

1. Bright Data MCP `scrape_as_markdown` if available.
2. Bright Data Unlocker for blocked/static pages.
3. Bright Data Browser API/Scraping Browser for JavaScript-heavy pages.
4. Mock fixture if `SIGNALGRAPH_MOCK_MODE=true`.

Persist every fetch attempt. Failed fetches should not fail the whole scan unless all selected sources fail.

### Step 4: Extract Signals

Call AI/ML API with strict JSON output. The extraction prompt must require:

- Facts only from provided content.
- Evidence URL on every signal.
- Confidence score.
- Distinction between direct fact and inference.
- No sensitive personal inference.
- No unsupported claims.

Expected extraction JSON:

```json
{
  "signals": [
    {
      "signal_type": "hiring",
      "title": "Hiring for data platform reliability",
      "summary": "The account has open roles mentioning Kafka and Snowflake reliability.",
      "fact_text": "The careers page lists a Senior Data Platform Engineer role requiring Kafka and Snowflake.",
      "inference_text": "This may indicate investment in data platform modernization.",
      "recommended_action": "Send an account-level note offering a reliability migration checklist.",
      "evidence_url": "https://example.com/careers/senior-data-platform-engineer",
      "observed_at": "2026-05-27",
      "confidence": 0.82
    }
  ]
}
```

Reject extracted signals when:
- `evidence_url` is missing.
- `confidence < 0.45`.
- The signal is purely speculative.
- The content references sensitive personal attributes.

### Step 5: Graph Update

Write a concise memory packet into Cognee:

```text
Account: Acme
Signal: Hiring for data platform reliability
Evidence: https://example.com/careers/senior-data-platform-engineer
Observed At: 2026-05-27
Fact: Careers page lists Kafka and Snowflake requirements.
Inference: Possible data platform modernization initiative.
Relationship: Matches ICP keywords Kafka, Snowflake, reliability.
```

Store Cognee dataset names consistently:

- `signalgraph_seed`
- `signalgraph_accounts`
- `signalgraph_people`
- `signalgraph_signals`
- `signalgraph_scan_{scan_id}`

### Step 6: Score Scan

Score out of 100:

- Fit: 30
- Timing: 30
- Relationship: 20
- Evidence: 20

Sales-ready rule:
- `total_score >= 70`
- At least two signals with confidence `>= 0.65`
- At least two unique evidence URLs

For demo purposes, also show `near_miss` accounts scoring `55-69`.

### Step 7: Generate Brief And Outreach

Generate a brief for every completed scan. Generate outreach only if:

- `sales_ready=true`, or
- user explicitly requests draft generation for a near-miss account.

Outreach guardrails:
- Do not say "I saw you..."
- Do not mention competitor usage unless directly public and framed gently.
- Do not expose private customer details.
- Do not fabricate familiarity.
- Use evidence-backed, account-level context.
- Keep the draft short.

## 9. API Endpoints

Base path: `/api/v1`

### Health And Config

`GET /health`

Returns service status and external integration readiness.

Response:

```json
{
  "status": "ok",
  "database": "ok",
  "bright_data": "configured",
  "cognee": "configured",
  "aiml_api": "configured",
  "mock_mode": false
}
```

### Seed Import

`POST /api/v1/import/seed`

Consumes multipart CSV upload.

Response:

```json
{
  "import_id": "imp_123",
  "accounts_created": 5,
  "people_created": 3,
  "icp_profiles_created": 1,
  "warnings": []
}
```

### Accounts

`GET /api/v1/accounts`

Query params:
- `status`
- `search`
- `limit`
- `offset`

`GET /api/v1/accounts/{account_id}`

Returns account details, latest score, latest brief, and recent signals.

### Scans

`POST /api/v1/accounts/{account_id}/scans`

Body:

```json
{
  "scan_type": "account_watchtower",
  "mode": "live",
  "max_sources": 8,
  "force_refresh": false
}
```

Response:

```json
{
  "scan_id": "scan_123",
  "status": "queued"
}
```

`GET /api/v1/scans/{scan_id}`

Returns status, progress, current phase, errors, and counts.

`GET /api/v1/scans/{scan_id}/events`

Server-sent events endpoint if frontend wants live progress. Polling `/scans/{scan_id}` is acceptable for MVP.

### Sources And Evidence

`GET /api/v1/scans/{scan_id}/sources`

`GET /api/v1/scans/{scan_id}/evidence`

Return discovered URLs and fetched documents.

### Signals

`GET /api/v1/signals`

Query params:
- `account_id`
- `scan_id`
- `signal_type`
- `min_confidence`
- `sales_ready`

`GET /api/v1/accounts/{account_id}/signals`

Returns account-specific signal feed.

### Briefs

`GET /api/v1/accounts/{account_id}/brief`

Returns the latest brief by default.

`POST /api/v1/scans/{scan_id}/brief/regenerate`

Regenerates brief from existing stored evidence and graph context. Does not rescrape.

### Outreach

`GET /api/v1/outreach/pending`

`GET /api/v1/outreach/{draft_id}`

`POST /api/v1/outreach/{draft_id}/approve`

`POST /api/v1/outreach/{draft_id}/reject`

Body:

```json
{
  "feedback": "Too personal. Make it account-level."
}
```

`PATCH /api/v1/outreach/{draft_id}`

Allows reviewer edits.

Body:

```json
{
  "subject": "Quick note on your data platform hiring",
  "body": "..."
}
```

## 10. Service Modules

Recommended folder structure:

```text
backend/
  app/
    main.py
    config.py
    db.py
    models/
      account.py
      person.py
      scan.py
      source.py
      evidence.py
      signal.py
      score.py
      brief.py
      outreach.py
    schemas/
      import_seed.py
      scan.py
      signal.py
      brief.py
      outreach.py
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
      brightdata_client.py
      scraper.py
      extractor.py
      cognee_service.py
      scorer.py
      briefing.py
      guardrails.py
      mock_fixtures.py
    jobs/
      scan_runner.py
    prompts/
      extract_signals.md
      generate_brief.md
      generate_outreach.md
  tests/
  fixtures/
    seed_demo.csv
    mock_serp_results.json
    mock_scraped_pages/
```

## 11. Environment Variables

```env
APP_ENV=development
DATABASE_URL=sqlite:///./signalgraph.db
SIGNALGRAPH_MOCK_MODE=true

BRIGHT_DATA_API_KEY=
BRIGHT_DATA_MCP_URL=
BRIGHT_DATA_SERP_ZONE=
BRIGHT_DATA_UNLOCKER_ZONE=
BRIGHT_DATA_BROWSER_WS=

AIML_API_KEY=
AIML_API_BASE_URL=https://api.aimlapi.com/v1
AIML_EXTRACTION_MODEL=
AIML_BRIEFING_MODEL=
AIML_DRAFT_MODEL=

COGNEE_API_KEY=
COGNEE_DATASET_PREFIX=signalgraph
```

Keep the app bootable when external keys are missing if `SIGNALGRAPH_MOCK_MODE=true`.

## 12. Mock Mode

Mock mode is required.

Behavior:
- Source discovery reads `fixtures/mock_serp_results.json`.
- Scraping reads files from `fixtures/mock_scraped_pages/`.
- Extraction can either call the model on fixture content or return `fixtures/mock_extracted_signals.json`.
- Cognee calls can be skipped or logged if unavailable.

The frontend demo should support switching between:
- `mock`: reliable rehearsed path.
- `live`: real Bright Data path for judging.

## 13. Error Handling

Scan-level failures should be recoverable and visible.

Rules:
- One failed source does not fail the scan.
- All sources failing marks scan as `failed`.
- AI extraction failure on one document marks that evidence as failed and continues.
- Cognee failure should not delete relational data; mark graph update warning.
- Brief generation failure should still return signals and score.

Store errors in:
- `scans.error_message` for scan-level error.
- `evidence_documents.metadata_json.error` for fetch errors.
- `signals.metadata_json.extraction_warning` for partial extraction issues.

## 14. Logging And Observability

Log structured events:

- `scan.created`
- `scan.discovery_started`
- `scan.sources_selected`
- `scan.scrape_started`
- `scan.evidence_fetched`
- `scan.extraction_completed`
- `scan.graph_updated`
- `scan.scored`
- `scan.brief_generated`
- `scan.completed`
- `scan.failed`

Each log should include:
- `scan_id`
- `account_id`
- `phase`
- `duration_ms`
- `count`
- `error` when applicable

## 15. Testing Checklist

Minimum backend tests:

- Seed CSV import creates accounts and people.
- Discovery deduplicates URLs.
- Scraper stores successful and failed evidence documents.
- Extractor rejects signals without evidence URLs.
- Scorer enforces score maximums and sales-ready threshold.
- Guardrails reject unsupported outreach claims.
- Scan runner completes a full mock scan.
- API returns expected shapes for account detail, scan status, signals, brief, and outreach.

## 16. Implementation Priority

### Phase 1: Demo-Critical Backend

- FastAPI app shell.
- SQLite/Postgres models.
- Seed CSV import.
- Mock scan runner.
- Bright Data client interface with mock implementation.
- Evidence and signal persistence.
- Scoring service.
- API endpoints for accounts, scans, signals, briefs, outreach.

### Phase 2: Live Bright Data Path

- Real source discovery with Bright Data MCP/SERP.
- Real scrape path with Bright Data MCP/Unlocker.
- Extraction through AI/ML API.
- Live scan progress updates.

### Phase 3: Cognee Integration

- Seed data memory ingestion.
- Evidence/signal memory ingestion.
- Graph context retrieval for brief generation.
- Graceful fallback if Cognee is unavailable during demo.

### Phase 4: Polish

- Outreach guardrail tests.
- Better score explanations.
- SSE scan events.
- Regenerate brief endpoint.
- Optional Triggerware/Speechmatics hooks.

## 17. Backend Definition Of Done

The backend is ready for frontend integration when:

- `POST /import/seed` loads the demo CSV.
- `GET /accounts` returns imported accounts.
- `POST /accounts/{id}/scans` starts a scan.
- `GET /scans/{id}` shows progress and completion.
- `GET /accounts/{id}/signals` returns evidence-backed signals.
- `GET /accounts/{id}/brief` returns an account brief with citations.
- `GET /outreach/pending` returns at least one safe draft for review.
- The entire flow works in mock mode without external keys.
- The live path demonstrates at least one Bright Data product.

## 18. Key Engineering Decisions

- Use SQLite for speed unless Supabase/Postgres is already provisioned.
- Use a jobs table and in-process background runner for hackathon simplicity.
- Keep Cognee behind a service wrapper so the backend remains functional if graph calls fail.
- Make Bright Data usage explicit in logs and response metadata so judges can see it.
- Build toward evidence-backed account intelligence, not generic lead scraping.

## 19. Backend Checklist Answers

I went through the open backend decisions and this is what I want us to follow for the MVP.

### Task Queue

For the hackathon MVP, use FastAPI `BackgroundTasks` or a simple in-process async job runner.

Do not spend time setting up Celery + Redis unless it is already ready. The scan pipeline is simple enough for now:

```text
queued -> discovering -> scraping -> extracting -> graphing -> scoring -> briefing -> completed
```

The important part is that every phase updates the `scans` table so the frontend can poll scan progress properly.

### Primary Database

Use SQLite for local MVP speed unless Supabase/Postgres is already provisioned and easy to use.

Please keep SQLAlchemy in place so we can move from SQLite to Postgres/Supabase later without rewriting everything.

### Mock Mode

Yes, please build mock mode first.

This is important so frontend can build the full UI flow without waiting on live Bright Data, Cognee, or model calls every time.

Use:

```env
SIGNALGRAPH_MOCK_MODE=true
```

Mock mode should support:
- Mock source discovery results.
- Mock scraped markdown/content.
- Mock extracted signals.
- Mock account score.
- Mock brief.
- Mock outreach draft.
- Cognee calls skipped or logged if keys/setup are not ready.

### Bright Data Priority

Use Bright Data in this order:

1. Bright Data MCP Server if it is easiest to wire.
2. SERP/search for source discovery.
3. `scrape_as_markdown` / Unlocker for public pages.
4. Browser API only if a page really needs JavaScript rendering.
5. Web Scraper API only where a structured scraper is clearly useful.

For the demo, we do not need to scrape everything. Around 5-10 strong sources for one account is enough if the evidence is clear.

### Cognee Priority

Please keep Cognee behind a wrapper service.

The scan should not fully fail just because Cognee is unavailable. If Cognee fails:
- Save relational data.
- Save evidence.
- Save extracted signals.
- Save score.
- Add a graph update warning.
- Generate the brief from stored evidence if needed.

Cognee is very important for the story, but it should not become a single point of demo failure.

### Frontend Scan Updates

Frontend can poll scan status every 1.5-2 seconds.

So for MVP we mainly need:

```http
GET /api/v1/scans/{scan_id}
```

This response should include:
- Status.
- Progress percent.
- Current phase.
- Counts for discovered/selected/fetched/failed sources.
- Error message if failed.

SSE can be added later if we have time.

### Sales-Ready Rule

Use this rule for MVP:

```text
sales_ready = total_score >= 70
AND at least 2 signals have confidence >= 0.65
AND at least 2 unique evidence URLs exist
```

Also return near-miss accounts from `55-69`, so frontend can show something like `Needs one more signal`.

### Outreach

Do not send emails from the backend.

Only create drafts with:

```text
status = pending_review
```

Approve means approved/logged for export, not sent.

### API Keys And External Requirements

Please make a separate list of every API key, credential, account, dashboard setting, zone name, callback URL, environment variable, and service setup needed from my side.

Send that list to me as early as possible so I can collect all the keys and access details and give them to the team.

At minimum, I expect we may need:
- Bright Data API key.
- Bright Data MCP setup details.
- Bright Data SERP zone if used.
- Bright Data Unlocker zone if used.
- Bright Data Browser API/WebSocket endpoint if used.
- AI/ML API key.
- Selected AI/ML API model names.
- Cognee API key or local setup instructions.
- Any Supabase/Postgres URL if we decide not to use SQLite.
- Any deployment environment variable names.

Please do not block implementation waiting for all live keys. Build mock mode first, then wire live integrations as keys become available.
