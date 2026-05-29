# Multimodal Signal Discovery Engine — Build Plan

This plan adapts `new-features.md` to the actual SignalGraph/Tendril codebase. It
explains where the feature fits, strengthens the weak spots in the original
proposal, and lays out a phasewise build that ships an end-to-end vertical slice.

## How it fits the existing architecture

The web scan pipeline is the proven template:

- `jobs/scan_runner.py` walks phases (`discovering → … → briefing`) committing
  between each, and `services/scan_events.py` writes a sanitized event trace.
- `services/aiml_client.py` is an OpenAI-compatible wrapper with model slots and
  a probe/fallback chain.
- `services/memory_service.py` is a pluggable JSONL/Cognee memory layer.
- `models/*` use a `TimestampMixin`, `gen_id(prefix)` ids, and register on
  `Base.metadata`. `db.init_db()` creates **missing tables** at startup.

The media engine mirrors this template with its own durable runner, its own
event logger, and its own tables. The web pipeline is left untouched.

## Strengthened decisions (vs. the original proposal)

1. **Do not reuse the `signals` table.** `signals.scan_id` is `NOT NULL` and the
   app has no migrations (it relies on `create_all`, which never alters existing
   tables). Reusing it would require a destructive rebuild on SQLite. We add a
   dedicated **`conversation_signals`** table instead. New tables are created
   automatically with zero migration risk.

2. **Real durable stages.** The existing runner is not sub-step resumable. The
   media runner persists `current_stage`, `stage_state_json`, `attempt_count`,
   and `last_error`. Each stage is idempotent and skipped if already recorded,
   so a restart resumes from the last incomplete stage.

3. **Content-addressable dedup (CAS).** `media_assets.media_hash` is unique. The
   resolve/hash stage reuses an existing asset+transcript when the hash matches,
   so the same episode is never transcribed twice. Extraction still runs
   per-account because account-specific signals differ.

4. **PII scrubbing before memory.** New `services/pii_scrubber.py` redacts
   emails, phones, addresses, and obvious identifiers. Raw and scrubbed text are
   stored separately; only scrubbed excerpts + structured signals reach memory.

5. **Cost discipline with the right model for the job.**
   - **Featherless** (cheap, open models) ranks candidate sources and runs
     chunk-level relevance filtering. This is the deliberate, justified use of
     `FEATHERLESS_API_KEY`.
   - **AIMLAPI** (default LLM provider) performs the final structured signal
     extraction and any narrative generation.
   - Sources are capped per account, transcripts/captions are preferred over
     paid ASR, and media is hashed before transcription.

6. **Mock-first, same safety gate as web scans.** Media scans default to `mock`
   unless `SIGNALGRAPH_MOCK_MODE=false` and the required providers are
   configured. Mock fixtures drive the whole pipeline so it runs without
   spending Speechmatics/LLM credits.

## Data model (new tables)

- `media_sources` — discovered public conversations (pre-transcription).
- `media_assets` — CAS identity of the media payload / reusable transcript.
- `transcripts` — raw + scrubbed text, segments, diarization, pii status.
- `media_scan_jobs` — durable pipeline state.
- `media_scan_events` — sanitized stage trace (mirrors `scan_events`).
- `conversation_signals` — timestamped, evidence-backed spoken signals.
- `notifications` — in-app notification center entries.

## Pipeline stages (durable, idempotent)

`discover_sources → rank_sources → resolve_media → hash_media → transcribe →
scrub_transcript → extract_signals → write_memory → score_account → notify`

Each stage reads prior outputs from `stage_state_json`, writes its own results
to the DB, and records completion before the runner advances.

## API surface

```
POST /api/v1/accounts/{account_id}/media-scans
GET  /api/v1/media-scans/{scan_id}
GET  /api/v1/media-scans/{scan_id}/events
POST /api/v1/media-scans/{scan_id}/resume
GET  /api/v1/accounts/{account_id}/media-sources
GET  /api/v1/accounts/{account_id}/conversation-signals
GET  /api/v1/transcripts/{transcript_id}
GET  /api/v1/notifications
POST /api/v1/notifications/{id}/read
```

## Phasewise build order

- **Phase 1 — Durable skeleton:** config, enums, models, event logger, durable
  runner with mock fixtures, API + router registration.
- **Phase 2 — Discovery & ranking:** SERP/YouTube/podcast discovery (mock +
  Bright Data), Featherless ranking, cap top sources.
- **Phase 3 — Resolution & CAS:** transcript/caption/RSS resolution, SHA-256
  hashing, transcript cache reuse.
- **Phase 4 — Transcription:** Speechmatics batch adapter (diarization,
  timestamps), retry/resume, mock transcript path.
- **Phase 5 — Privacy & extraction:** PII scrubbing, chunk relevance filter
  (Featherless), structured extraction (AIMLAPI), timestamped evidence.
- **Phase 6 — Product surface:** account Conversations tab, media-scan progress
  panel, conversation evidence drawer, score-delta explanation.
- **Phase 7 (scaffold) — Watchtower:** notifications center + hooks for
  scheduled refresh and proactive alerts.

## Verification

- Backend: `pytest` durable-runner mock e2e, CAS dedup, PII scrubber, resume.
- `ruff` clean. App imports and starts.
- Frontend: `tsc`/build passes; Conversations tab + media panel render.
