# Tendril — Quality Hardening Plan (LIVING DOCUMENT)

This is a **living artifact**. It is updated as work proceeds so progress is
always visible. Each phase is small, verified (tests / typecheck / build),
committed, and pushed before the next begins.

Status legend: ⬜ not started · 🟡 in progress · ✅ done · ⏭️ deferred

Last updated: initial draft.

---

## Goal

Close the concept-integrity gaps and land the highest-leverage premium UX
moments identified in `product-analysis-and-ux-review.md`, without breaking the
existing build (120+ tests green, frontend builds clean) and without risky
destructive migrations.

Guiding constraints:
- Additive schema changes only (new tables / `ADD COLUMN`); no destructive
  column rewrites on the live SQLite DB. New columns are backfilled by an
  idempotent `ensure_schema` helper at startup.
- Mock-first: everything must run and be demonstrable offline.
- Every phase: verify → commit → push. Update this doc each phase.

---

## Phases

### Phase 0 — Plan artifact ✅
- This document. Commit + push.

### Phase 1 — True content-addressable dedup (CAS) ✅
**Why:** `product-analysis §3.1`. Hash was URL+duration, so the same episode at
two URLs got transcribed twice — defeating the feature's core cost premise.

**Done:**
- `media_resolution._content_hash` now hashes a normalized transcript-content
  fingerprint (lowercased, whitespace-collapsed spoken words), falling back to
  URL identity only when no cheap transcript content exists. Two URLs for the
  same episode → same `media_hash` → cache hit → transcription skipped.
- Added a duplicate-episode mock source (same content, different URL/publisher).
- Added `ensure_schema()` in `db.py` for safe additive ADD COLUMN migrations on
  the existing SQLite DB (needed by later phases).

**Verified:** new `test_cas_content_dedup_across_different_urls` proves two
different URLs resolve to one asset and the second is a cache hit; all 7 media
tests pass.

### Phase 2 — Budget ceiling + cost telemetry ✅
**Why:** `product-analysis §3.3`. The feature is *about* cost; we had soft caps
but no spend guardrail or dollar telemetry.

**Done:**
- `services/cost.py`: labeled per-unit estimates (`estimate_transcription_usd`,
  `estimate_llm_calls_usd`, `would_exceed_budget`) driven by settings.
- `MediaScanJob.cost_estimate_usd` column (additive via `ensure_schema`).
- Runner accrues estimated cost per stage and, before transcription, projects
  ASR + extraction cost for not-yet-cached sources; if it would exceed
  `MEDIA_SCAN_BUDGET_USD` (default $25, 0 = off) it hard-stops with a clear,
  resumable reason. Cache hits accrue nothing.
- `cost_estimate_usd` surfaced in `MediaScanRead`.

**Verified:** `test_cost.py` (estimation + ceiling) and runner tests for budget
stop (scan fails before transcribe, resumable) and cost telemetry on completion.
13/13 pass.

### Phase 3 — Unified account score (conversation evidence moves the number) ✅
**Why:** `product-analysis §3.4`. Conversation delta was siloed on the job; the
headline score never moved.

**Done (migration-safe, no nullability change on `scores`):**
- New additive table `account_score_snapshots` holding the account's *current*
  modality-aware actionability score (source = web_scan | media_scan, plus an
  optional `conversation_delta`).
- `services/account_scoring.py`: `record_web_snapshot`, `record_media_snapshot`
  (layers the conversation delta on the prior snapshot), `latest_snapshot`.
- Web scan runner writes a snapshot after scoring; media runner writes one in
  `score_account` applying the delta.
- Account detail returns `latest_score_snapshot` as the headline score.

**Verified:** `test_media_scan_moves_unified_account_score` — a media scan raises
the account's latest snapshot total over the web baseline, attributed to spoken
evidence. Full suite 134/134.

### Phase 4 — Score-move UX moment ✅
**Why:** `product-analysis §4.2.B`. The signature premium moment.

**Done:**
- `AnimatedNumber` primitive (ease-out count, reduced-motion aware).
- `AccountScoreStrip` now reads the unified snapshot, animates the headline
  total, and shows a "+N from spoken evidence" chip when a media scan moved it.
  The `ScoreRing` already animates its arc and pulses on the sales-ready
  crossing.

**Verified:** tsc clean; production build clean.

### Phase 5 — "Today" home feed 🟡
**Why:** `product-analysis §4.2.D`. The product promises a daily queue; the app
opens to a table.

**Plan:**
- Backend `/api/v1/today`: accounts that became actionable recently (new
  sales-ready, score jumps, fresh high-value signals) ranked with one-line why.
- New `/` route with an opinionated, prioritized feed; sidebar default.

**Verify:** endpoint test; tsc + build.

### Phase 6 — Evidence drawer elevation ⬜
**Why:** `product-analysis §4.2.E`. Make "proof" the signature interaction.

**Plan:**
- Waveform/timeline strip with the quote region highlighted (conversation).
- One-click "copy quote with citation".
- Privacy status as a trust micro-explainer ("N identifiers redacted").

**Verify:** tsc + build.

### Phase 7 — Shared motion + elevation vocabulary ⏭️ (stretch)
Define named transitions + a strict elevation scale; apply app-wide.

---

## Progress log

- (init) Plan created.
- Phase 1 done: true content-addressable dedup (transcript-content hashing),
  duplicate-episode fixture, `ensure_schema` migration helper. 7/7 media tests
  green.
- Phase 2 done: cost estimation service, per-scan budget ceiling that hard-stops
  before transcription, cost telemetry on the job + API. 13/13 cost+media tests
  green.
- Phase 3 done: unified `account_score_snapshots` written by both pipelines;
  account detail returns the modality-aware headline score. 134/134 suite green.
- Phase 4 done: `AnimatedNumber` + score-strip reads the snapshot, animates the
  total, shows "+N from spoken evidence". tsc + build clean.
