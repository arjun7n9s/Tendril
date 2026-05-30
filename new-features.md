# Tendril Multimodal Signal Discovery Engine

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

This is not an "audio scraping" feature. It is a **Multimodal Signal Discovery Engine**.

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

- **Near-term**: database-backed jobs table plus worker loop, because the current app is
  small and SQLite/Postgres migration is still in progress.
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

This gives us Content Addressable Storage (CAS):

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
- `source_type` (`youtube`, `podcast`, `earnings_call`, `webinar`, `conference`, `other`)
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
- `provider` (`speechmatics`, `captions`, `existing_transcript`)
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

The existing `signals` table can be reused if we add enough metadata:

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

