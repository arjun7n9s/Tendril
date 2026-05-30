# Tendril Product Expansion Blueprint

## Product Direction

Tendril should evolve from a scan-and-table tool into an operator-grade GTM workspace.

The product should answer two questions every time a rep opens it:

- What changed in my market, accounts, and pipeline?
- What should I do next?

Two product pillars move Tendril in that direction:

1. **Tendril Home: GTM Operator Cockpit**  
   A judgment-first home screen with an LLM command center, daily priorities,
   signal stream, watchtower alerts, and suggested actions.

2. **Multimodal Signal Discovery Engine**  
   A backend intelligence layer that reads the public web and listens to public
   conversations: podcasts, earnings calls, webinars, conference talks, YouTube
   sessions, and panels.

The key product shift:

> Tendril should not open as a database. It should open as a decision layer.

---

# Pillar 1: Tendril Home

## Product Thesis

Going directly into the Accounts page makes Tendril feel like a CRM table. That is
useful, but it is not the strongest first impression.

The first screen should make the user feel:

- Tendril understands their accounts.
- Tendril knows what changed.
- Tendril can explain why it matters.
- Tendril can guide the next action.

This page is not a marketing landing page. It is the working home for the product:

> A GTM Operator Cockpit that turns account intelligence into daily judgment.

## Design Principle

Open with judgment, not inventory.

The Accounts page should remain the database view. The Home page should be the
intelligence view.

Accounts page:

- browse all accounts
- filter by score, status, industry, signal type
- inspect one account deeply

Home page:

- summarize what changed
- prioritize what matters
- let the user ask questions
- suggest actions
- route the user into the right workflow

## First Screen Narrative

The ideal first screen should feel like:

> Good morning. 7 accounts changed while you were away.

Then immediately give the user a command box:

> Ask Tendril what changed, who to contact, or where to scan next.

The page should not explain features. It should perform useful work.

## Core Layout

### 1. Context-Aware Command Center

The command center is the primary object on the page.

It should be a large, calm input area that understands the current workspace:

- accounts
- account scores
- web scan results
- media scan results
- watchtower alerts
- outreach drafts
- Cognee memory
- recent changes
- provider health

Example prompts:

- Which accounts became sales-ready this week?
- What changed since my last scan?
- Which accounts need outreach today?
- Show accounts with new migration or vendor-evaluation signals.
- Find accounts with weak evidence but high potential.
- Scan Stripe for spoken signals from podcasts and webinars.
- Summarize Acme's newest evidence into a sales brief.
- Which outreach drafts are ready for approval?

The response should not be a generic chatbot answer. It should return structured,
actionable output:

- account references
- evidence links
- confidence levels
- recommended next actions
- buttons to open account, run scan, review evidence, or draft outreach

### 2. Today's Priority Accounts

A focused list of accounts that require action now.

Priority reasons:

- score crossed the sales-ready threshold
- high-confidence signal appeared
- new stakeholder or champion was detected
- account has a material score jump
- competitor/vendor mention appeared
- recent media source produced useful evidence
- outreach draft is ready
- previous scan failed or needs attention

Each item should show:

- account name
- score and score delta
- reason for prioritization
- strongest evidence snippet
- recommended action

Example:

> Acme +14  
> New CTO podcast mention confirms Kafka migration timeline.  
> Action: review evidence and generate outreach.

### 3. Multimodal Signal Stream

A chronological feed of meaningful changes across the workspace.

Signal types:

- web article
- job post
- funding event
- product launch
- leadership change
- podcast
- YouTube talk
- webinar
- earnings call
- conference panel
- competitor/vendor mention

Each signal should include:

- source type
- account
- short summary
- confidence
- timestamp or source date
- evidence link
- privacy status where relevant

This stream is not a raw log. It should be filtered for signals that matter.

### 4. Watchtower Alerts

Watchtower is the autonomous monitoring layer.

Alerts should surface things that happened without the user manually clicking scan:

- new public conversation found for a tracked account
- media transcript completed
- account score changed materially
- source failed to resolve
- Speechmatics or LLM provider failed
- Cognee memory write failed
- new sales-ready account detected

The alert panel should support:

- acknowledge
- open account
- open scan
- retry failed workflow
- view provider details

### 5. Suggested Actions

This is the action queue. It should be small, opinionated, and directly useful.

Examples:

- Approve outreach draft for Ramp
- Review Acme podcast evidence
- Run media scan for Stripe
- Retry failed transcript for Box
- Add Databricks as competitor keyword for Vercel
- Open sales brief for Snowflake

Suggested actions should come from real system state, not static cards.

## What The LLM Should Be Allowed To Do

The Home command center should start as an intelligence assistant, not an autonomous
agent with unrestricted write access.

### Phase 1: Read And Explain

Allowed:

- summarize account changes
- list priority accounts
- explain why an account is sales-ready
- compare accounts
- retrieve evidence
- answer dashboard questions

Not allowed:

- mutate account state
- send outreach
- trigger expensive media scans without confirmation
- delete memory or transcripts

### Phase 2: Suggest And Prepare

Allowed:

- prepare outreach drafts
- propose scan targets
- suggest ICP keyword improvements
- create review bundles
- generate sales briefs

Write actions require explicit user confirmation.

### Phase 3: Controlled Actions

Allowed after confirmation:

- run web scan
- run media scan
- mark alert as acknowledged
- create outreach draft
- refresh account score
- retry failed job

Every action should produce an audit event.

## Backend API Surface

### Dashboard Summary

```http
GET /api/v1/dashboard/summary
```

Returns the first-screen state in one fast payload.

Suggested response shape:

```json
{
  "greeting": "Good morning. 7 accounts changed while you were away.",
  "priority_accounts": [],
  "signal_stream": [],
  "watchtower_alerts": [],
  "suggested_actions": [],
  "metrics": {
    "sales_ready_accounts": 0,
    "new_signals_24h": 0,
    "open_outreach_drafts": 0,
    "failed_jobs": 0
  }
}
```

### Command Center

```http
POST /api/v1/dashboard/command
```

Request:

```json
{
  "prompt": "Which accounts need outreach today?"
}
```

Response:

```json
{
  "answer_markdown": "...",
  "cards": [],
  "actions": [],
  "citations": []
}
```

The command endpoint should use retrieval, not a blind database dump.

Recommended context assembly:

1. classify user intent
2. fetch relevant accounts, scans, signals, alerts, drafts
3. fetch Cognee memory snippets where useful
4. send compact structured context to the LLM
5. validate returned actions against an allowlist
6. return answer, cards, citations, and proposed actions

### Action Execution

```http
POST /api/v1/dashboard/actions/{action_id}/execute
```

Used only for confirmed actions.

Examples:

- run media scan
- retry failed job
- create outreach draft
- acknowledge alert
- open account briefing

## Data Model Additions

### `dashboard_actions`

Stores suggested and confirmed actions.

Fields:

- `id`
- `account_id`
- `action_type`
- `title`
- `description`
- `status`
- `priority`
- `source_type`
- `source_id`
- `metadata_json`
- `created_at`
- `updated_at`
- `completed_at`

### `dashboard_command_events`

Audit trail for LLM interactions.

Fields:

- `id`
- `prompt`
- `intent`
- `context_summary_json`
- `response_summary`
- `proposed_actions_json`
- `executed_action_ids_json`
- `model`
- `duration_ms`
- `created_at`

### `watchtower_alerts`

If not already represented by notifications, alerts should have their own operational
state.

Fields:

- `id`
- `account_id`
- `alert_type`
- `severity`
- `title`
- `body`
- `status`
- `source_id`
- `source_url`
- `metadata_json`
- `created_at`
- `acknowledged_at`

## Frontend Product Requirements

The Home page should feel operational, not decorative.

Layout:

- top command center
- compact metrics row
- two-column main area
- priority accounts and suggested actions on the left
- signal stream and watchtower alerts on the right

Interaction details:

- pressing Enter submits the command
- suggested prompts appear only when the command box is empty
- command results render as answer plus structured cards
- action buttons are explicit and confirm expensive operations
- cards link into account detail, scan detail, evidence drawer, or outreach review

Avoid:

- generic marketing hero
- empty decorative cards
- static fake suggestions
- oversized typography inside dense dashboard areas
- landing directly into a table

## MVP Build Order

### Phase 1: Static Home Shell

- create `/home` or make dashboard root use Home
- add command center UI
- add empty states
- add placeholder cards backed by real API shapes
- keep Accounts accessible from nav

### Phase 2: Dashboard Summary API

- aggregate priority accounts
- aggregate latest signals
- aggregate watchtower alerts
- aggregate suggested actions
- return compact metrics

### Phase 3: Command Center Read Mode

- implement `POST /api/v1/dashboard/command`
- support read-only questions
- return cited answers and account cards
- no write actions yet

### Phase 4: Suggested Actions

- generate actions from real system state
- add action status
- support acknowledge/open/review actions
- add audit events

### Phase 5: Confirmed Operations

- allow confirmed scan triggers
- allow retry failed jobs
- allow outreach draft creation
- record every action execution

### Phase 6: Proactive Experience

- connect watchtower events
- show new alert indicators
- add live refresh or polling
- later: WebSocket or server-sent events

## Success Criteria

The Home page is successful if a user can answer these in under 30 seconds:

- What changed since I last opened Tendril?
- Which accounts deserve attention?
- Why do they matter?
- What evidence supports that?
- What should I do next?

---

# Pillar 2: Multimodal Signal Discovery Engine

## Product Thesis

Tendril should not only read the public web. It should listen to the public internet.

Most GTM intelligence tools can scrape text: job posts, blogs, funding news, changelogs,
press releases, and company pages. The next defensible layer is spoken evidence:
podcasts, earnings calls, webinars, conference talks, customer panels, investor days,
technical interviews, and YouTube sessions.

The product promise:

> Tendril discovers revenue-relevant buying signals buried in public conversations,
> extracts timestamped evidence, updates account memory, and alerts the rep before the
> opportunity goes stale.

This is not an audio scraping feature. It is a **Multimodal Signal Discovery Engine**.

## Strategic Scope

The launch wedge must stay narrow and reliable:

> For one target account, find the top public spoken sources, transcribe or reuse them,
> extract the best GTM signals, and turn those signals into account intelligence.

We should not try to crawl the entire audio web in v1. The first real product version control syustem here....
should answer:

- What public conversations has this account appeared in recently?
- Which sources are worth paying to transcribe?
- What buying triggers, pain points, migrations, vendor mentions, timelines, and
  stakeholder quotes appear in those conversations?
- What changed in the account score or outreach angle because of that spoken evidence?

## Industrial Requirements

This feature only becomes product-grade if the backend is designed for long-running,
expensive, failure-prone work from day one.

### 1. Persistent Multi-Stage Pipelines

Media processing takes minutes. A 45-minute podcast cannot be treated like a normal
HTTP request.

The pipeline must be broken into persisted stages:

1. `discover_sources`
2. `rank_sources`
3. `resolve_media`
4. `download_or_cache_media`
5. `hash_media`
6. `transcribe`
7. `scrub_transcript`
8. `extract_signals`
9. `write_memory`
10. `score_account`
11. `notify`

Each stage must write its state before moving forward. If the server restarts, a network
call drops, or Speechmatics is temporarily unavailable, the job resumes from the last
completed sub-step instead of starting over.

Recommended infrastructure:

- **Near-term**: database-backed jobs table plus worker loop.
- **Product-grade**: Temporal, Celery, BullMQ, or another durable workflow queue.
- **Non-negotiable design**: idempotent stage handlers, persisted inputs/outputs, retry
  counts, error states, and resumability.

### 2. Media Deduplication With Content Addressable Storage

Speechmatics and LLM calls are expensive. The same podcast episode or conference panel
may mention multiple target accounts. Tendril must never transcribe the same audio twice.

The system should implement media hashing:

1. Download or resolve the media payload.
2. Generate a SHA-256 hash of the normalized audio bytes.
3. Check `media_assets` for an existing hash.
4. If the hash exists, reuse the stored transcript.
5. If the hash does not exist, transcribe once and cache the result.

This gives us Content Addressable Storage:

- `media_hash` becomes the durable identity of the audio.
- Multiple accounts can link to the same `media_asset`.
- Transcription cost is paid once.
- Extraction can still run per account, because the same transcript may contain different
  account-specific signals.

### 3. PII And Sensitive Data Scrubbing

Raw transcripts can contain names, phone numbers, emails, casual customer references,
internal anecdotes, or sensitive personal data. Tendril must not blindly write raw
conversation text into Cognee or any long-term memory layer.

Before memory writes, every transcript should pass through a privacy filter:

- redact emails, phone numbers, addresses, and obvious identifiers
- detect sensitive personal attributes where possible
- mark transcript sections that should not be used for outreach
- store raw transcript and scrubbed transcript separately if raw retention is enabled
- write only scrubbed excerpts and structured signals into Cognee

Enterprise posture:

- Default memory writes should use scrubbed text.
- Raw audio/transcript retention should be configurable.
- Every extracted signal should carry evidence metadata and a privacy status.
- Outreach generation must never use sensitive or private details.

### 4. Proactive Watchtower, Not Just Manual Scans

A manual `POST /accounts/{id}/media-scan` is useful for development and demos, but it is
not the final product behavior.

Sales reps do not want another button. They want to be told when something meaningful
happens.

The industrial version should include background discovery sources:

- YouTube channel checks
- podcast RSS feeds
- earnings calendar monitoring
- investor relations updates
- event and webinar pages
- SEC/company announcement feeds where relevant

The product should notify reps when:

- a new high-value spoken source appears
- a transcript mentions a tracked account, competitor, vendor, migration, pain point, or
  timeline
- an account score changes materially
- a sales-ready signal emerges

Delivery channels:

- in-app notification center
- WebSocket or server-sent event updates during live processing
- email or Slack later
- Web Push later

## Proposed Data Model

### `media_sources`

Represents a discovered public source before we know whether we will transcribe it.

Suggested fields:

- `id`
- `account_id`
- `source_url`
- `source_type`
- `title`
- `description`
- `publisher`
- `speaker_names_json`
- `published_at`
- `duration_seconds`
- `transcript_available`
- `discovery_query`
- `rank_score`
- `rank_reason`
- `status`
- `created_at`
- `updated_at`

### `media_assets`

Represents the actual media payload or reusable transcript identity.

Suggested fields:

- `id`
- `media_hash`
- `canonical_url`
- `storage_uri`
- `content_type`
- `duration_seconds`
- `byte_size`
- `download_status`
- `transcription_status`
- `speechmatics_job_id`
- `transcript_id`
- `created_at`
- `updated_at`

### `transcripts`

Represents the transcription output.

Suggested fields:

- `id`
- `media_asset_id`
- `provider`
- `language`
- `raw_text`
- `scrubbed_text`
- `segments_json`
- `diarization_json`
- `confidence`
- `pii_status`
- `created_at`
- `updated_at`

### `media_scan_jobs`

Represents the durable pipeline state.

Suggested fields:

- `id`
- `account_id`
- `status`
- `current_stage`
- `stage_state_json`
- `attempt_count`
- `last_error`
- `started_at`
- `completed_at`
- `created_at`
- `updated_at`

### Signals

The existing signals model can be reused if it carries conversation metadata:

- `source_modality = "conversation"`
- `media_source_id`
- `media_asset_id`
- `transcript_id`
- `quote_text`
- `quote_start_seconds`
- `quote_end_seconds`
- `speaker_label`
- `privacy_status`

## Pipeline Blueprint

### Stage 1: Source Discovery

Inputs:

- account name
- domain
- known people
- competitors
- ICP keywords
- existing account context

Discovery methods:

- Bright Data SERP API
- YouTube result search through SERP
- podcast RSS discovery
- investor relations pages
- event/webinar pages

Output:

- candidate `media_sources`

### Stage 2: Source Ranking

Use a cheap model to rank candidates before spending transcription money.

Ranking criteria:

- relevance to account
- recency
- likely technical/business depth
- speaker seniority
- transcript availability
- source credibility
- expected GTM signal density

Output:

- top sources to process
- skipped sources with reasons

### Stage 3: Media Resolution

Prefer the cheapest legal/reliable path:

1. Existing transcript from the source page.
2. Captions or subtitle track.
3. Podcast RSS enclosure audio.
4. Downloadable webinar/earnings audio.
5. Browser-assisted resolution only when necessary.

Output:

- transcript candidate or media URL
- resolution metadata

### Stage 4: Download And Hash

Download media only when needed.

Rules:

- stream to disk/object storage
- compute SHA-256
- reuse `media_asset` if hash already exists
- avoid duplicate transcription
- persist download progress where possible

Output:

- `media_asset`

### Stage 5: Transcription

Use Speechmatics for batch ASR when no transcript/caption is available.

Requirements:

- diarization enabled where useful
- timestamped segments
- provider job ID stored
- retryable provider failures
- no duplicate transcription for existing hashes

Output:

- `transcripts` row

### Stage 6: PII Scrubbing

Scrub transcript before graph memory.

Outputs:

- scrubbed transcript text
- PII findings metadata
- privacy status

### Stage 7: Signal Extraction

Use AIMLAPI or Featherless for extraction.

Model strategy:

- cheap model for chunk classification and relevance filtering
- stronger model for final structured extraction on high-value chunks

Extract:

- buying trigger
- pain point
- migration or implementation detail
- vendor/competitor mention
- stakeholder/person
- timeline
- urgency
- quote
- timestamp
- confidence
- recommended sales angle

Output:

- structured signals with timestamped evidence

### Stage 8: Memory Write

Write only scrubbed, structured, evidence-backed content to memory.

Rules:

- Cognee writes must be timeout-bounded
- fallback to JSONL if Cognee fails
- every memory packet should include source URL, transcript ID, quote timestamp, and
  privacy status

### Stage 9: Account Score Refresh

Conversation signals should influence score when they include:

- active project timeline
- vendor migration
- budget/procurement language
- executive priority
- repeated pain
- competitor dissatisfaction
- named initiative

Output:

- refreshed score
- score delta explanation

### Stage 10: Notification

If a meaningful signal emerges, notify the user.

Initial version:

- in-app scan result and account activity feed

Later:

- WebSocket progress
- Web Push
- Slack/email alerts

## API Surface

Manual trigger remains useful for demos and debugging:

```http
POST /api/v1/accounts/{account_id}/media-scans
```

Status:

```http
GET /api/v1/media-scans/{scan_id}
GET /api/v1/media-scans/{scan_id}/events
```

Account media intelligence:

```http
GET /api/v1/accounts/{account_id}/media-sources
GET /api/v1/accounts/{account_id}/conversation-signals
```

Transcript evidence:

```http
GET /api/v1/transcripts/{transcript_id}
```

The manual endpoints should be built first, but the architecture should assume autonomous
scheduled jobs later.

## Frontend Product Surface

### Account Page: Conversation Signals

Add a dedicated section or tab:

- discovered media sources
- processing status
- extracted spoken signals
- quote snippets
- speaker label
- timestamp
- source link
- score impact

### Scan Progress UI

Media scans take longer than normal scans. The UI needs stage-aware progress:

- discovering public conversations
- ranking sources
- resolving media
- checking transcript cache
- transcribing
- scrubbing transcript
- extracting signals
- updating account memory

### Evidence Drawer

Conversation evidence should show:

- source title
- publisher
- speaker
- timestamped quote
- scrubbed transcript excerpt
- link to original media
- privacy status

## Cost Controls

Non-negotiable controls:

- cap processed sources per account
- prefer existing transcripts/captions
- hash media before transcription
- cache transcripts by media hash
- chunk transcript before LLM extraction
- run cheap relevance filters before expensive extraction
- configurable daily/monthly provider budgets
- scan-level cost telemetry

## Failure Handling

Every stage should be retryable and idempotent.

Failure examples:

- media URL expires
- download drops
- Speechmatics job times out
- provider returns malformed JSON
- Cognee memory write hangs
- database write lock occurs

Expected behavior:

- persist failure state
- retry with backoff where safe
- resume from last completed stage
- never double-bill transcription for cached media
- show useful scan events in the UI

## Compliance And Trust

Enterprise trust requirements:

- source URL and timestamp on every signal
- no unsourced claim generation
- PII scrubbing before memory writes
- sensitive-content guardrails before outreach
- configurable raw transcript retention
- audit trail of provider calls
- ability to delete transcripts and memory packets for an account

## MVP Build Order

### Phase 1: Durable Media Scan Skeleton

- add media tables
- add media scan job table
- implement persisted stages
- add scan events
- add manual API trigger
- use mock media fixtures first

### Phase 2: Discovery And Ranking

- Bright Data SERP media queries
- candidate source storage
- LLM ranking
- cap to top 3 sources

### Phase 3: Transcript Acquisition

- existing transcript/caption path
- podcast RSS enclosure path
- media hashing
- transcript cache

### Phase 4: Speechmatics Integration

- batch transcription
- diarization
- timestamped segments
- retry/resume behavior

### Phase 5: Privacy And Extraction

- PII scrubbing
- transcript chunking
- structured signal extraction
- timestamped evidence

### Phase 6: Product Surface

- account conversation signals
- media scan progress
- transcript evidence drawer
- score delta explanation

### Phase 7: Autonomous Watchtower

- scheduled source refresh
- YouTube/RSS/investor page monitors
- proactive alerts
- notification center

## Final Product Direction

This feature is the bridge from project to product.

The disciplined version is not:

> Tendril downloads audio and transcribes it.

The disciplined version is:

> Tendril finds hidden spoken buying signals, proves them with timestamped evidence,
> deduplicates expensive media processing, protects sensitive transcript data, and
> proactively alerts reps when an account becomes actionable.

