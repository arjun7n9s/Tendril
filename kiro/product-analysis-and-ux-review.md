# Tendril — Product Intent, Concept Integrity & UX Review

A deep, honest analysis of what we set out to build, how well the idea was
shaped into the implementation, where the concept has real flaws, and what it
takes for the product to *feel* like a premium product end to end.

This document is deliberately critical. It calls out weaknesses in the concept
and in the current build — including in code I wrote — because flattering
reviews don't make products better.

---

## Part 1 — What was our intent?

### 1.1 The original thesis (from `kiro-product-blueprint.md`)

The founding intent was tight and defensible:

> Revenue teams don't need more static lead lists. They need a live,
> evidence-backed system that notices meaningful account and champion changes,
> understands *why* they matter, and turns them into reviewable next actions.

Three intent pillars held the whole thing together:

1. **Live, not stale** — beat static data vendors to the buying window using
   Bright Data as the live web layer.
2. **Explainable, not magic** — every signal carries an evidence URL, a
   fact/inference split, a confidence score, and a "why now."
3. **Safe, not creepy** — account-level triggers over personal ones, human
   approval before anything leaves the system, PII and sensitive-attribute
   guardrails.

The wedge was explicitly *narrow*: import a seed, scan one account, extract
structured signals, score against ICP, draft human-safe outreach. The blueprint
even lists "what to avoid" — don't build a generic scraper, don't over-build
lookalike before the core loop works.

### 1.2 The new intent (from `new-features.md`)

The Multimodal Signal Discovery Engine extends the *same* thesis into a new
modality:

> Tendril should not only read the public web. It should listen to the public
> internet — podcasts, earnings calls, webinars, conference talks.

This is a genuinely good strategic instinct. The reasoning holds up:

- **Defensibility.** Text scraping (jobs, blogs, funding) is commoditized.
  Spoken evidence is a harder, more expensive layer that most GTM tools ignore,
  so it's a real moat.
- **Signal quality.** The highest-intent statements a buyer ever makes in
  public — "we're migrating off X," "we have budget approved," "this is our top
  priority" — are spoken on earnings calls and podcasts, not written on a
  careers page.
- **Thesis continuity.** It doesn't pivot the product; it deepens the same
  "live + explainable + safe" promise with timestamped quotes as the new
  evidence primitive.

**Verdict on intent → ideation:** The ideation is strong and on-thesis. The
spec correctly reframed the feature from "audio scraping" (a feature) to a
"Multimodal Signal Discovery Engine" (a layer), and it correctly identified the
hard parts (durable pipelines, dedup, PII, cost) instead of just the glamorous
part (transcription).

---

## Part 2 — Is the implementation justifying the concept?

Mostly **yes**, with a few honest gaps. Here is the scorecard against what the
spec promised.

| Spec promise | Implemented? | Notes |
|---|---|---|
| Persistent multi-stage pipeline | ✅ | 10 durable stages, `stage_state_json`, resume |
| Idempotent / resumable stages | ✅ | Skips completed stages; covered by a resume test |
| Content-addressable dedup (CAS) | ⚠️ Partial | Hash is over URL+duration, **not audio bytes** (see 3.1) |
| PII scrubbing before memory | ✅ | Regex scrubber + sensitive-content blocking, tested |
| Cheap-model gate → strong extraction | ✅ | Featherless ranking/relevance → AIMLAPI extraction |
| Timestamped, evidence-backed signals | ✅ | Quote text + start/end seconds + speaker label |
| Cost controls | ⚠️ Partial | Source cap + cache + relevance filter present; **no budget ceiling** (3.3) |
| Speechmatics batch ASR | ⚠️ Untested live | Adapter written; only the mock/fixture path is verified |
| Proactive watchtower | ✅ | Opt-in, gated, scheduled re-scan + notifications |
| Account conversation surface | ✅ | Conversations tab, evidence drawer, scan panel |
| Score-delta explanation | ✅ | Bounded delta + human-readable reasons |

**Where the implementation genuinely honors the concept:**

- The durable runner is the real differentiator the spec asked for. A 45-minute
  podcast is not an HTTP request, and the build treats it that way.
- The dedicated `conversation_signals` table (instead of overloading the web
  `signals` table) was the right call — it kept conversation-specific evidence
  first-class and avoided a destructive migration.
- The cheap/strong model split is a faithful, cost-disciplined reading of the
  spec rather than "send everything to GPT-4o."
- PII scrubbing actually gates memory writes; sensitive-flagged signals are
  never written. The safety thesis is enforced in code, not just documented.

**Where it falls short of the concept (and we should be honest):**

- The most expensive, most differentiated stage — **real Speechmatics
  transcription** — has never run end to end in this build. Everything verified
  runs on fixtures. The concept's headline ("we transcribe the spoken web") is
  architecturally ready but not empirically proven.
- CAS dedup is **structural, not true content addressing** (details below).
- There is no actual **budget enforcement**, only soft caps.

---

## Part 3 — Conceptual flaws (where they live)

These are flaws in the *concept*, or in the gap between concept and code, not
cosmetic bugs.

### 3.1 The CAS hash is not content-addressable (medium severity)

**Where:** `backend/app/services/media_resolution.py` → `_compute_media_hash`.

The hash is `sha256(canonical_url + duration)`. The spec's entire dedup premise
is: *the same audio* mentioned across multiple accounts should be transcribed
once. But two URLs pointing at the same episode (a YouTube link and a podcast
RSS enclosure of the same talk) produce **different** hashes and get transcribed
twice — exactly the cost the feature exists to avoid. Conversely, a re-uploaded
file at the same URL with edited content would falsely hit the cache.

This is the difference between "URL dedup" (what we built) and "content
addressing" (what we promised). It's honestly labeled in the code comments, but
the concept's cost story leans on real CAS.

**Fix direction:** hash the normalized downloaded audio bytes (or a perceptual
audio fingerprint / acoustic hash) once the audio is actually fetched. The
function signature already isolates this, so the swap is localized.

### 3.2 "Listening to the public internet" is narrower than it sounds (concept framing)

The pitch implies broad audio discovery. In reality, reliable spoken-source
discovery depends on:

- transcripts/captions already existing (cheap path), or
- a legal, downloadable audio URL (RSS enclosure, earnings audio).

YouTube ToS, podcast host protections, and paywalled investor portals make the
"download-and-transcribe anything" path legally and technically fragile. The
disciplined version of the concept is **"reuse existing transcripts/captions
first, transcribe only when a clean audio URL exists,"** which is what the
resolution order does. The risk is the *marketing* over-promising relative to
what's safely achievable. Keep the narrative honest: we surface signals from
*public, transcribable* conversations, not "all audio everywhere."

### 3.3 No real cost ceiling (medium severity, given the whole feature is about cost)

The spec is emphatic: "configurable daily/monthly provider budgets," "scan-level
cost telemetry." We have **soft** controls (cap 3 sources, prefer cache, cheap
relevance gate) but:

- no per-account, per-day, or per-month spend ceiling that hard-stops a scan;
- no stored cost-per-scan telemetry (we count calls, not dollars);
- the watchtower, once enabled in live mode, could fan out scans on a schedule
  with only `batch_size` as a brake — that's a rate limiter, not a budget.

For a feature whose entire reason-to-exist is "transcription and LLM calls are
expensive, so be disciplined," the absence of an actual budget guardrail is the
sharpest conceptual gap.

### 3.4 Conversation score-delta lives outside the unified score (low-medium)

**Where:** `backend/app/services/media_scoring.py`.

To avoid a destructive migration on the `scores` table (which is `NOT NULL` on
`scan_id`), conversation signals produce a **delta reported on the media scan
job**, not a persisted row in the unified scoring model. Consequence: the
account's headline score in `AccountScoreStrip` does **not** actually move when
a media scan finds a hot spoken signal — the delta is shown in the media panel
instead. The two scoring worlds are siloed. The concept wants one account
actionability number that conversation evidence genuinely influences.

**Fix direction:** make `scores.scan_id` nullable (proper Alembic migration) and
let conversation signals write a real score row, or unify both modalities into a
single scoring pass. This was a deliberate, pragmatic trade-off to avoid a risky
migration mid-build — but it's debt against the concept.

### 3.5 Provider-failure realism is under-proven (medium)

The spec lists exactly the failures that matter: media URL expires, download
drops, Speechmatics times out, provider returns malformed JSON, Cognee hangs.
The code has retry/resume scaffolding and graceful fallbacks, but the live
provider failure paths (especially Speechmatics polling timeouts) are only
reasoned about, not exercised. Until a real job is run and a real failure is
recovered, "resumable" is a design claim, not a verified property.

### 3.6 Single-node durability ceiling (acknowledged, not yet a flaw)

The durable runner is DB-backed, which is correct for the current SQLite app.
But the watchtower runs on background **threads** against SQLite. That's fine for
a demo or single node; under real production load (write locks, multi-worker,
restarts mid-transcription) it will need a true durable queue (Temporal/Celery)
and Postgres. The architecture anticipates this, so it's planned debt rather than
a hidden flaw — worth stating plainly so nobody ships the thread loop to prod.

### 3.7 The original loops are still half-built (scope honesty)

Stepping back to the *whole* product: the blueprint promised three loops —
Account Watchtower (A), Champion Mobility (B), Lookalike Discovery (C). The
build (web + media) is essentially a very strong **Loop A**. Loops B and C
barely exist (`Person` model has previous/current company, but no champion-move
detection or lookalike ranking pipeline). The multimodal engine deepened Loop A
rather than widening to B/C. That's a *defensible* prioritization — depth over
breadth — but the product narrative should not imply B and C are done.

---

## Part 4 — UI / UX review: making it feel like a premium product

The design system is genuinely good: restrained Zinc-based palette, semantic
accent tokens (signal/cobalt/evidence/risk/graph), tight type scale, real focus
rings, reduced-motion handling, skip links, a11y attention. This is already
above hackathon average. The gap to *premium* is about **information
architecture, motion choreography, depth, and the moments of delight** — not
about adding more color.

### 4.1 Strengths to preserve

- Coherent token system; one source of truth in `globals.css`.
- Evidence-first interaction model (drawers, citations, fact/inference split).
- Accessibility is treated as a feature, not an afterthought.
- The live-scan and media-scan panels already tell a "watch the agent work"
  story, which is the emotional core of the product.

### 4.2 High-impact upgrades (ranked by perceived-premium-per-effort)

**A. Unify the two scan panels into one "Agent Activity" language.**
Right now the web `LiveScanPanel` and the `MediaScanPanel` are visually similar
but separate, with slightly different steppers, metric tiles, and event icon
sets. Premium products have *one* unmistakable "the agent is working" surface.
Extract a shared `AgentRunPanel` with a consistent stepper, consistent metric
row, and a shared event-log component themed per modality. Consistency reads as
craft.

**B. Make the headline score actually move, and animate the delta.**
The single most premium GTM moment is: a scan completes, and the account's score
visibly ticks up from 64 → 78 with the ring animating and a "+14 from spoken
evidence" chip sliding in. Today the conversation delta is siloed (see 3.4), so
this moment doesn't happen on the main score ring. Fixing 3.4 unlocks the single
highest-value piece of UX delight in the product.

**C. Choreograph signal arrival, don't just render it.**
When a scan finishes, signals currently appear via a simple `MotionFade` stagger.
Premium feel comes from *sequenced* reveals tied to the pipeline: as each stage
completes in the panel, the corresponding artifact (source found → source row;
signal extracted → signal card) animates into place in the main view in real
time. The data is already polled; the choreography is the missing layer.

**D. Add a global "Today" / command surface, not just account-by-account.**
The product's promise is "a daily queue of account changes." There is no
home/"Today" view that says: *here are the 5 accounts that became actionable
since yesterday, ranked, with the one-line why-now.* The sidebar opens to
Accounts (a table). A premium GTM tool opens to a prioritized, opinionated feed.
This is both a UX and a product-positioning upgrade.

**E. Elevate the evidence drawer into the signature "proof" moment.**
The conversation evidence drawer is good (quote, speaker, timecode, scrubbed
transcript with the cited line highlighted). To make it *signature*:
- Add a faux waveform/timeline scrubber with the quote region highlighted, even
  if non-interactive at first — it sells "we listened to this."
- Add a one-click "copy quote with citation" that yields
  `"…quote…" — Speaker, Source Title (mm:ss), URL`. Reps will live in this.
- Show the privacy status as a reassuring micro-explainer ("3 identifiers
  redacted before this was stored"), turning a compliance detail into a trust
  signal.

**F. Notifications → a real activity feed with grouping and affordances.**
The bell popover is a solid start. Premium notification centers: group by
account, show an avatar/monogram, support hover-preview, distinguish
"new high-value source" from "scan completed," and offer an inline "View
evidence" action. Right now every media scan emits a generic completion
notification (3.x), so the feed will feel noisy at scale. Differentiate event
types and let users mute per-account.

**G. Depth and material.**
The palette is clean but flat. Premium B2B tools (Linear, Vercel, Stripe) earn
"depth" through: a single consistent elevation scale, hairline borders that
brighten on hover, subtle inner-glows on active/live elements, and *one*
signature gradient used sparingly (e.g., the live-pulse). The codebase already
has `shadow-flat/raised/overlay` and glow utilities — apply them with a stricter
elevation hierarchy (canvas → surface → raised → overlay) and stop mixing
ad-hoc `backdrop-blur` with flat cards.

**H. Empty and loading states that teach.**
Skeletons exist, which is great. Level up by making first-run empty states
*narrate the value*: the Conversations empty state could show a tiny animated
"discover → transcribe → extract" mini-pipeline so users understand what a media
scan will do before they run one. Loading is an opportunity to build
anticipation, not just fill space.

**I. Dark mode is defined but unproven.**
Tokens for `.dark` exist and the theme switcher is wired, but the build/QA notes
only claim a11y on light-mode flagship routes. Premium products nail dark mode.
Do a real dark-mode pass on the media surfaces (the glow/blur effects especially
need re-tuning on dark canvas) before calling it done.

**J. Motion system, not motion instances.**
Framer Motion is used per-component with hand-tuned springs. Premium feel comes
from a *shared* motion vocabulary: define 3–4 named transitions (enter, exit,
emphasis, live-pulse) as constants and use them everywhere so timing/easing is
identical across the app. Inconsistent easing is the most common "almost
premium" tell.

### 4.3 Specific component-level notes

- **`AccountHeader`**: the only action is "Run scan." Add a watch toggle and a
  "last spoken signal" micro-stat here so the header summarizes both modalities
  at a glance.
- **`AccountScoreStrip`**: the four sub-scores (Fit/Timing/Relationship/
  Evidence) are bars without interactivity. Make each expandable to show the
  reasoning JSON we already compute — "show your work" is a premium trust move.
- **`AccountKpiStrip`**: four separate `useAccountsList` calls (one per tile) is
  wasteful and will flash inconsistent numbers. Back it with one `/metrics`
  endpoint. Premium = numbers that appear together, instantly, and never
  disagree.
- **Conversations vs Intelligence tabs**: media signals live in a separate
  section below web signals. Consider a unified "Signals" stream with a modality
  filter (web / spoken) so the rep sees one ranked timeline, with spoken signals
  visually distinguished by the `Mic`/waveform motif. Two parallel signal lists
  is the kind of seam users feel.
- **Timecodes/monospace**: good use of `font-mono` for timecodes. Extend that
  discipline — all IDs, durations, scores, and counts in monospace tabular
  figures so numbers never jitter.

### 4.4 The "premium" litmus test

A product feels premium when **every state is designed, every number agrees,
every motion shares a vocabulary, and the core value moment is choreographed.**
Tendril is ~70% there on aesthetics and ~40% there on choreography and IA. The
highest-leverage work is not more components — it's (1) unifying the two scan/
signal experiences, (2) making the score visibly move, and (3) adding the
opinionated "Today" home that matches the product's daily-queue promise.

---

## Part 5 — Prioritized recommendations

**Concept integrity (do these to make the build match the pitch):**
1. Real content hashing for CAS (3.1) — protects the core cost story.
2. Budget ceiling + per-scan cost telemetry (3.3) — the feature is *about* cost.
3. Unify conversation signals into the headline score via a proper migration
   (3.4) — also unlocks the best UX moment.
4. Run one real Speechmatics job and recover one real failure (3.2/3.5) — turn
   "resumable" from claim to fact.

**Premium UX (do these to make it feel like a product):**
5. Unify the scan/activity experience into one `AgentRunPanel` (4.2.A).
6. Animate the score delta on completion (4.2.B) — depends on #3.
7. Add the opinionated "Today" home feed (4.2.D).
8. Elevate the evidence drawer with waveform + copy-with-citation (4.2.E).
9. Establish a shared motion + elevation vocabulary (4.2.G, 4.2.J).
10. Real dark-mode pass on media surfaces (4.2.I).

**Narrative honesty (do these so we don't over-claim):**
11. Frame the audio layer as "public, transcribable conversations," not "all
    audio" (3.2).
12. Be explicit that Loops B (Champion Mobility) and C (Lookalike) are future
    work; the product today is a deep Loop A across two modalities (3.7).

---

## Closing assessment

The intent was sharp, and the new-feature ideation deepened it intelligently
rather than chasing a shiny tangent. The implementation is genuinely strong on
the *hard* parts the spec called out — durability, PII safety, model-cost
discipline — and that's exactly where most teams cut corners. The honest gaps
are: CAS is structural not true content addressing, there's no hard budget,
conversation evidence doesn't yet move the headline score, and the live
transcription path is architected but unproven. None of these are fatal; all are
localized and fixable.

On UX, the foundation (tokens, a11y, evidence-first interaction) is above
average. The distance to *premium* is choreography, information architecture, and
a single unmistakable "watch the agent work, then watch the number move" moment —
not more surface decoration.
