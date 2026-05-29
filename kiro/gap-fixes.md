# Gap Fixes — Reviewer Findings Addressed

This records how each gap raised in review was resolved, cross-checked against
the current code (some had been partially addressed during the hardening
phases). All fixes are additive and migration-safe; the full backend suite is
green (142 tests).

## 1. Durability was only partial ✅

**Findings:** stage state written at completion (failures point at the previous
stage); no durable reclaim if the process dies mid-stage.

**Fixes:**
- `_begin_stage()` now writes `current_stage` and a `last_heartbeat_at`
  heartbeat *before* each stage runs, so a crash/timeout points at the stage
  that was actually executing — not the previously completed one.
- New `services/media_reclaimer.py`: finds non-terminal jobs whose heartbeat is
  older than the stage timeout (a healthy worker refreshes it each stage) and
  re-enqueues them. Wired to run (a) once at startup via
  `reclaim_orphaned_media_scans()` in the app lifespan, and (b) every watchtower
  tick. Because every stage is idempotent and resumes from `stage_state_json`,
  re-enqueue is safe.

> Note on scope: this makes single-node restart/crash recovery automatic. A
> true multi-worker durable queue (Temporal/Celery + Postgres) remains the
> production end-state; the heartbeat + reclaimer is the correct bridge for the
> current DB-backed architecture.

## 2. Speechmatics double-billing risk ✅

**Finding:** job submitted then waited on; a crash after submit could resubmit
on resume.

**Fix:** `_speechmatics_transcribe` now persists the provider `job_id` to the
`MediaAsset` with an **immediate commit right after submit, before waiting**,
and sets `transcription_status = in_progress`. On resume, if the asset already
has a `speechmatics_job_id`, it **polls that existing job instead of
resubmitting** — so a crash during the wait never double-bills.

## 3. CAS was not real media CAS ⚠️→✅ (content-based; bytes are the future step)

**Finding:** hashing used url + duration.

**Fix (done earlier, Phase 1):** hashing now uses a normalized
transcript-content fingerprint (lowercased, whitespace-collapsed spoken words),
so the same episode at different URLs (YouTube vs. RSS re-release) dedups to one
asset. URL identity is only a last-resort fallback when no transcript content
can be resolved cheaply. True audio-byte / perceptual hashing is the documented
next step for the live download path; the function boundary isolates that swap.

## 4. Cache metrics could be retroactively misleading ✅

**Finding:** scan cache-hit counts derived from the shared, mutable
`MediaAsset.transcription_status`, so a later scan could flip an older scan's
counts.

**Fix:** `_compute_counts` now reads `transcripts` and `cache_hits` from the
job's own `stage_state_json` (recorded at the time that scan ran) — an
immutable, per-scan record. A later scan can no longer change an earlier scan's
reported numbers. Covered by `test_cache_hits_not_retroactively_attributed`.

## 5. `max_sources` accepted but ignored ✅

**Finding:** request schema had it; runner used global settings only.

**Fix:** `max_sources` is persisted on `MediaScanJob` at create time and the
runner uses `job.max_sources or settings.media_scan_max_sources`. Covered by
`test_max_sources_request_is_honored`.

## 6. Privacy good but not airtight ✅

**Finding:** sensitive transcripts/signals were still persisted and returnable
with only a `privacy_status` flag.

**Fixes:**
- `GET /accounts/{id}/conversation-signals` **excludes** `sensitive_blocked`
  signals by default; an explicit `include_sensitive=true` is required to see
  them, and even then their free text (quote/summary/fact/inference/action) is
  **masked** via `_redact_signal` so sensitive content never reaches outreach.
- `GET /transcripts/{id}` **withholds the body** (`scrubbed_text`,
  `segments_json`) for `sensitive_blocked` transcripts unless
  `include_sensitive=true`, while still returning status/findings so the UI can
  explain why it's withheld.
- Covered by `test_sensitive_signal_suppressed_by_default`.

## 7. Conversation scoring not wired into core score flows ✅

**Finding:** media scan computed a delta on the job but list flows
(`sales_ready`/`near_miss`) read the old `scores` table, so spoken signals
didn't move them.

**Fix:** the account list filters now read the unified
`account_score_snapshots` table (written by **both** web and media scans) via
`_latest_snapshot_subquery`. Combined with the Phase 3 snapshot writes and the
Phase 4 headline animation, conversation evidence now flows all the way through:
account detail headline, the Today feed, **and** the sales-ready/near-miss list
filters.
