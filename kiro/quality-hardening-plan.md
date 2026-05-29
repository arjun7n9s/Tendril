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

### Phase 1 — True content-addressable dedup (CAS) ⬜
**Why:** `product-analysis §3.1`. Hash was URL+duration, so the same episode at
two URLs got transcribed twice — defeating the feature's core cost premise.

**Plan:**
- Hash the *cheap-to-fetch content* before the expensive transcribe stage:
  transcript text for transcript-available sources (and the mock fixture text),
  audio bytes for audio (live, future).
- Two sources that resolve to the same episode → same `media_hash` → second is a
  cache hit → transcription skipped.
- Add a duplicate-episode mock source (same episode, different URL/publisher) to
  prove cross-URL dedup in the demo.

**Verify:** extend `test_media_scan_runner` CAS test to assert the aliased
source reuses the transcript (no second transcript row).

### Phase 2 — Budget ceiling + cost telemetry ⬜
**Why:** `product-analysis §3.3`. The feature is *about* cost; we had soft caps
but no spend guardrail or dollar telemetry.

**Plan:**
- `services/cost.py`: rough, clearly-labeled per-unit estimates (ASR per minute,
  LLM per call) → `estimate_*` helpers.
- `MediaScanJob.cost_estimate_usd` column (additive; `ensure_schema` ADD COLUMN).
- Runner accumulates estimated cost per stage; a per-scan budget
  (`MEDIA_SCAN_BUDGET_USD`) hard-stops before transcribe/extract when exceeded,
  marking the job `failed` with a clear, resumable reason.
- Surface `cost_estimate_usd` in `MediaScanRead` + the scan panel.

**Verify:** unit test for cost estimation; runner test asserting a tiny budget
stops the scan before transcription.

### Phase 3 — Unified account score (conversation evidence moves the number) ⬜
**Why:** `product-analysis §3.4`. Conversation delta was siloed on the job; the
headline score never moved.

**Plan (migration-safe):**
- New additive table `account_score_snapshots`: the *current* account
  actionability score, written by both web scans and media scans, decoupled from
  any single scan row (no nullability change on `scores`).
- Web pipeline writes a snapshot after scoring; media pipeline writes a snapshot
  applying the conversation delta on top of the latest snapshot.
- Account detail returns the latest snapshot as the headline score.

**Verify:** test that a media scan raises the account's latest snapshot total and
records a modality breakdown.

### Phase 4 — Score-move UX moment ⬜
**Why:** `product-analysis §4.2.B`. The signature premium moment.

**Plan:**
- `AccountScoreStrip` reads the unified snapshot; animate the ring + total when
  it changes after a scan; show a "+N from spoken evidence" chip.
- Expandable sub-score reasoning ("show your work").

**Verify:** tsc + build; manual visual reasoning.

### Phase 5 — "Today" home feed ⬜
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
