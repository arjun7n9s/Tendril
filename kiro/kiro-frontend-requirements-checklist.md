# Tendril Frontend — Requirements Checklist

**Purpose:** Lock every decision, asset, dependency, and contract needed before we build the premium dashboard described in `kiro-frontend-architecture.md`.
**Style:** Mirrors `kiro-backend-requirements-checklist.md`.
**Status legend:** `[ ]` pending · `[x]` decided · `[~]` default assumed, confirm if different · `[?]` blocking question for you

---

## 0. Source Of Truth

This checklist is derived from:

- `kiro-frontend-architecture.md` — north star, screens, components, design language
- `kiro-product-blueprint.md` — product positioning and demo story
- `backend/app/api/*.py`, `backend/app/schemas/*.py`, `backend/app/models/enums.py` — exact contracts the frontend must consume

Anything in those files but not echoed here is still binding.

---

## A. Decisions & Inputs From You

### A1. Brand and product name

- [x] **Brand name** — **Tendril**. The `README.md` is canonical. All UI copy, page titles, manifest, favicon, and demo narrative use `Tendril`. `SignalGraph` survives only as the internal codename in the engineering plan documents.
- [x] **Wordmark form** — `Tendril` (capital T, single token).
- [x] **Symbol concept** — abstract tendril/curl mark suggesting reach and connection, drawn as a single-stroke geometric SVG. Pairs with the wordmark in `Inter` semibold, tracking `-1`.
- [x] **Tagline** — `Live GTM change intelligence`.

### A2. Core stack

- [x] **Framework** — Next.js 14, App Router, TypeScript strict.
- [x] **Styling** — Tailwind CSS, custom theme tokens, no CSS-in-JS runtime.
- [x] **Component system** — shadcn/ui (owned source), wrapped into product primitives.
- [x] **Data layer** — TanStack Query for reads + mutations; URL state for filters/tabs.
- [x] **Tables** — TanStack Table headless, paired with shadcn `Table` markup.
- [x] **Charts** — Recharts (Tremor-style wrappers); no D3.
- [x] **Graph** — React Flow.
- [x] **Forms** — React Hook Form + Zod resolvers.
- [x] **Icons** — Lucide React.
- [x] **Markdown** — `react-markdown` with a constrained prose theme + `remark-gfm`.
- [x] **Motion** — Framer Motion for subtle scan/progress transitions only.
- [x] **Notifications** — `sonner` (shadcn-compatible toast).
- [x] **Date/time** — `date-fns` (lightweight, tree-shakeable).
- [x] **Package manager** — `pnpm` (locked). Lockfile is `pnpm-lock.yaml`. README documents `pnpm install` and `pnpm dev` so the team stays aligned.
- [~] **Node version** — `>=20.11`. Pin in `.nvmrc` and `package.json` engines.
- [~] **Linting** — ESLint flat config + Prettier + Tailwind plugin.
- [x] **Testing** — Vitest for unit, Playwright for the demo happy-path E2E (optional polish phase).

### A3. Theme and visual direction

- [x] **Mode** — Light-first. Dark mode is a Phase 4 polish item, not a launch requirement.
- [x] **Palette** — Exactly the values in `kiro-frontend-architecture.md` §6:
  - Canvas `#F7F8F6`
  - Surface `#FFFFFF`
  - Raised surface `#F1F4F2`
  - Text primary `#171A1C`
  - Text secondary `#5D656B`
  - Border `#DDE3E0`
  - Primary accent (signal green) `#0F9F6E`
  - Secondary accent (cobalt) `#3457D5`
  - Evidence accent (amber) `#C47A1D`
  - Risk accent (red) `#C2413A`
  - Graph accent (teal) `#138A8A`
- [x] **Semantic mapping** — green = sales-ready, amber = inferred, red = risk/failed, blue = live process, teal = graph/memory.
- [~] **Typography**
  - UI sans — `Inter` (variable, latin + latin-ext).
  - Display sans — same family; no separate display font (avoids marketing-y feel).
  - Mono — `JetBrains Mono` for raw evidence excerpts only.
- [x] **Radii** — cards `8px`, buttons/inputs `6px`, chips `4px`.
- [x] **Borders over shadows** — 1px hairlines preferred; shadows reserved for floating layers (drawer, popover, command).
- [x] **No** marketing gradients, glass orbs, glow effects, or cyber visuals.

### A4. Backend integration

- [x] **API base URL (dev)** — `http://localhost:8000`. The backend already permits `http://localhost:3000` via `CORS_ALLOWED_ORIGINS`.
- [x] **All routes prefixed** — `/api/v1/...` (with `/health` also exposed at root).
- [~] **Env var** — `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`). Add a single `.env.local` example.
- [x] **Auth** — none for hackathon; do not add login screens.
- [x] **Mock vs live** — backend already coerces `live` to `mock` if Bright Data REST is not configured. Frontend never decides this; it just reads `scan.mode` and the `/health` flags and surfaces them in the top bar.
- [x] **Polling cadence** — active scan `1500ms`. Stop on `completed` or `failed`. Refetch `account`, `signals`, `brief`, and `outreach/pending` on completion.
- [x] **Pagination** — server returns `{items, total, limit, offset}` for accounts/signals; frontend respects this for infinite or paged tables.

### A5. Demo content

- [~] **Vendor in copy** — `VectorLake`, developer data platform.
- [~] **Seeded accounts** — Northstar Bank, Meridian Health Cloud, AtlasPay, OrbitCart, FluxForge (per blueprint §7 / architecture §8).
- [~] **Champion** — Maya Chen (per blueprint §7).
- [x] **Backend already loads seed data** through `/api/v1/import/seed` from `backend/fixtures/seed_demo.csv`. The frontend will not invent its own parallel mock seed; it will either trigger import on first visit or assume the backend has already run import.
- [x] **First-run UX** — auto-prime the demo seed in local/demo mode. On the first paint of `/accounts`, if the response is empty, the frontend POSTs the bundled `public/seed_demo.csv` (copied from `backend/fixtures/seed_demo.csv`) to `/api/v1/import/seed`, then refetches. Toast: `Demo seed loaded`. The `/imports` page remains visible and functional so judges see manual import is supported. Auto-prime never runs more than once per session and is suppressed if the response is non-empty.

### A6. Scope toggles

- [x] **MVP routes** — `/`, `/accounts`, `/accounts/[accountId]`, `/outreach`, `/imports`.
- [x] **Phase 3 routes** — `/signals`, `/scans` (cross-account list), `/settings`.
- [x] **Knowledge graph** — Phase 3 inside `/accounts/[accountId]?tab=graph`.
- [x] **Outreach** — review/approve/reject/edit only. No `Send`. No CRM writeback.
- [x] **Speechmatics voice notes** — out of scope for v1 frontend.
- [x] **Triggerware automations UI** — out of scope; the backend already runs scans on demand.

### A7. Responsive targets

- [x] **Primary** — desktop `1440px`. Must look sharp at `1280px`.
- [x] **Secondary** — tablet `1024px` (collapsible right panel) and mobile `390px` (stacked, full-screen sheets).
- [x] **Tables** may horizontally scroll on mobile; never truncate primary action labels.

### A8. Accessibility

- [x] WCAG AA color contrast everywhere; verified for the chip palette especially (amber/red on white).
- [x] All interactive elements keyboard reachable with visible focus rings.
- [x] Icon-only buttons get `aria-label` and a tooltip.
- [x] Color is paired with text or icon; never the only signal.
- [x] `prefers-reduced-motion` disables Framer transitions.
- [x] Tables use semantic `<table>` markup.

---

## B. Information Architecture (Routes + Tabs)

| Route | Purpose | Phase |
|---|---|---|
| `/` | Redirect to `/accounts`. No marketing page. | 1 |
| `/accounts` | Accounts Command Center (table + KPI strip + filters) | 1 |
| `/accounts/[id]` | Account Intelligence Room (header + score strip + signals + brief + outreach) | 1–2 |
| `/accounts/[id]?tab=graph` | Knowledge graph view | 3 |
| `/accounts/[id]?tab=timeline` | Signal timeline (focused, full-width) | 3 |
| `/imports` | Seed CSV upload + import summary | 1 |
| `/outreach` | Draft queue + editor + guardrails | 2 |
| `/signals` | Cross-account signal feed | 3 |
| `/scans` | Cross-account scans list (history + active) | 3 |
| `/settings` | Integration status + display preferences | 4 |
| `/_not-found` | Custom 404 | 4 |

Global shell renders on every route except `/_not-found`.

---

## C. Backend Contracts To Consume

All paths assume the `http://localhost:8000` base URL.

### C1. Health and integration status

- `GET /health` → `{status, database, bright_data_rest, bright_data_browser, bright_data_mcp, aiml_api, cognee, triggerware, speechmatics, mock_mode, app_env}` with each integration as `configured` | `not_configured`. Drives top-bar integration chips.

### C2. Imports

- `POST /api/v1/import/seed` (multipart `file`) → `SeedImportResponse { import_id, accounts_created, accounts_updated, people_created, people_updated, icp_profiles_created, icp_profiles_updated, warnings: string[] }`.

### C3. Accounts

- `GET /api/v1/accounts?status&search&sales_ready&near_miss&limit&offset` → `AccountListResponse { items: AccountRead[], total, limit, offset }`.
- `GET /api/v1/accounts/{id}` → `{account, latest_scan, latest_score, latest_brief, recent_signals[]}`.

### C4. Scans

- `POST /api/v1/accounts/{id}/scans` body `{scan_type, mode, max_sources, force_refresh}` → `{scan_id, status, mode}` (status 201).
- `GET /api/v1/scans/{scan_id}` → `ScanRead` with `counts: {discovered, selected, fetched, failed, signals, bright_data_calls, aiml_calls, memory_writes}`. Used for polling.
- `GET /api/v1/scans/{scan_id}/events?after_sequence&limit` → `ScanEventList` (incremental log, drives the live event stream).
- `GET /api/v1/scans/{scan_id}/sources` → `SourceRead[]`.
- `GET /api/v1/scans/{scan_id}/evidence` → `EvidenceRead[]` (used by the Evidence Drawer for full markdown).

### C5. Signals

- `GET /api/v1/signals?account_id&scan_id&signal_type&min_confidence&sales_ready&limit&offset`.
- `GET /api/v1/accounts/{id}/signals?signal_type&min_confidence&all_history&limit&offset`. Default `all_history=false` returns only the latest scan's signals.

### C6. Briefs

- `GET /api/v1/accounts/{id}/brief` → `BriefRead` (`title`, `executive_summary`, `why_now`, `key_evidence_json`, `risks_json`, `recommended_next_steps_json`).
- `POST /api/v1/scans/{scan_id}/brief/regenerate` → `BriefRead` (used from the brief panel's "Regenerate" action; backend reuses persisted signals so it is cheap).

### C7. Outreach

- `GET /api/v1/outreach/pending?all_history` → `OutreachList`.
- `GET /api/v1/outreach/{draft_id}` → `OutreachRead`.
- `POST /api/v1/outreach/{draft_id}/approve` → `OutreachRead`.
- `POST /api/v1/outreach/{draft_id}/reject` body `{feedback?}` → `OutreachRead`.
- `PATCH /api/v1/outreach/{draft_id}` body `{subject?, body?, tone?}` → `OutreachRead`.

### C8. Enum reference (must match exactly in TS)

From `backend/app/models/enums.py`:

- `AccountStatus`: `target | customer | former_customer | competitor | ignored`
- `ScanType`: `account_watchtower | champion_mobility | lookalike_discovery`
- `ScanStatus`: `queued | discovering | scraping | extracting | graphing | scoring | briefing | completed | failed`
- `ScanMode`: `mock | live | cached`
- `SourceType`: `company_site | careers | blog | news | github | docs | serp_result | review | public_profile | other`
- `FetchStatus`: `success | failed | skipped`
- `FetchMethod`: `brightdata_mcp | serp_api | unlocker | browser_api | web_scraper_api | mock | cached`
- `SignalType`: `hiring | tech_stack | migration | funding | product_launch | leadership_change | competitor_mention | champion_move | market_event | other`
- `OutreachTone`: `warm | technical | executive | concise`
- `OutreachStatus`: `pending_review | approved | rejected | edited`
- `ScanEventType`: `phase_started | phase_completed | bright_data_call | bright_data_call_replayed | aiml_call | aiml_call_replayed | memory_write | memory_write_replayed | warning | error | info`

These are reproduced as TS string-literal unions in `lib/types/`. Backend changes flow into the frontend by hand; we keep a one-line note in each type file pointing at the source enum.

---

## D. Component Inventory

Mirrors the architecture's `components/` tree. Each entry below has a defined purpose, props contract, and acceptance check before it is "done".

### D1. App shell (`components/app-shell/`)

- `AppShell` — fixed sidebar + top bar + main content slot. Persists across routes via root layout.
- `Sidebar` — nav items: Accounts, Outreach, Imports, Signals (Phase 3), Scans (Phase 3), Settings (Phase 4). Active state, compact icon + label, collapsed mode at narrow widths.
- `TopCommandBar` — global `cmdk` search (accounts, signals, evidence), env chip (`Mock` / `Live`), integration chips (Bright Data REST, Bright Data Browser, AI/ML API, Cognee), primary action button (context-aware).
- `IntegrationStatus` — chip group fed by `/health`. Tooltip on hover shows the underlying flag.

### D2. Accounts (`components/accounts/`)

- `AccountTable` — TanStack Table with columns: Account, Fit, Timing, Relationship, Evidence, Total, Top signal, Signals, Last scanned, Next action. Row hover, row click opens detail.
- `AccountScoreStrip` — total score ring + four sub-score bars + sales-ready / near-miss chip + `Why now` one-liner.
- `AccountHeader` — name + domain (with external-link icon), industry/size/region chips, status chip, `Run Live Scan`, `Generate Draft`.
- `AccountPreviewDrawer` — slide-in 480px drawer used from the table for fast peek.
- `AccountFiltersBar` — status, score range, industry, signal type, last scanned, sales-ready toggle, mode toggle.
- `AccountKpiStrip` — five compact metric tiles.

### D3. Scans (`components/scans/`)

- `LiveScanPanel` — slide-over sheet (or in-page panel on detail). Phase stepper + counters + event stream + integration badges + completion state.
- `ScanPhaseStepper` — horizontal stepper bound to `ScanStatus`. Distinguishes terminal `failed` state.
- `ScanSourceStream` — incremental list of sources as they appear, with fetch method badge and status icon.
- `ScanEventList` — paginated/streamed event log. Filters by `event_type`. Replayed events get a small `replayed` chip.

### D4. Signals (`components/signals/`)

- `SignalCard` — type chip, title, fact, inference, recommended action, confidence meter, evidence button, source domain, observed date, secondary actions.
- `SignalTimeline` — chronological vertical timeline with grouping by week.
- `ConfidenceMeter` — 0-1 → 10-segment meter with semantic color.
- `SignalTypeChip` — icon + label per `SignalType`.

### D5. Evidence (`components/evidence/`)

- `EvidenceDrawer` — right-side sheet. Title, URL with copy, fetch method badge, fetched-at, source type, highlighted excerpt, full markdown rendered with `react-markdown`, related signals list, `Open original` button.
- `SourceBadge` — domain favicon (auto-derived) + domain text.
- `CitationButton` — small button that opens the Evidence Drawer for a given evidence id.

### D6. Graph (`components/graph/`)

- `AccountKnowledgeGraph` — React Flow canvas with custom node renderers per `node_type` (account, person, champion, signal, evidence, tech, competitor, icp).
- `GraphNodePanel` — side panel with related facts and citations.
- `GraphControls` — fit, filter by node type, toggle evidence edges, toggle champion path.

### D7. Briefs (`components/briefs/`)

- `AccountBriefPanel` — collapsible sections for Executive Summary, Why Now, Key Evidence (with `SourceBadge` per item), Risks, Recommended Next Steps. `Regenerate` button calls `POST /scans/{id}/brief/regenerate`.
- `CitedBriefSection` — shared section primitive that pairs prose with citation chips.

### D8. Outreach (`components/outreach/`)

- `DraftQueue` — left list; selected row highlights.
- `DraftEditor` — subject + body editors, tone segmented control, `Approve` / `Reject` / `Save` actions, autosave with explicit indicator.
- `GuardrailPanel` — guardrail checklist + claims-with-evidence list + unsupported-claim warnings.
- `RejectFeedbackDialog` — optional feedback capture on reject.

### D9. Imports (`components/imports/`)

- `SeedUploadDropzone` — drag/drop with column checklist.
- `CsvPreviewTable` — first 10 rows preview with column mapping confirmation.
- `ImportSummary` — counters + warnings + link to `/accounts`.

### D10. Primitives (`components/primitives/`)

- `ScoreRing` — total score ring with color thresholding.
- `MetricTile` — KPI strip tile.
- `StatusChip` — semantic chip (variants for account status, scan status, outreach status, fetch status).
- `EmptyState` — icon + title + body + primary action. Each route ships its own copy variant.
- `LoadingSkeleton` — table-row, card, panel, drawer variants.

### D11. shadcn components actually installed

`button, input, textarea, select, checkbox, tabs, badge, table, dialog, sheet, drawer, tooltip, popover, dropdown-menu, command, progress, skeleton, separator, scroll-area, sonner, label, form, segmented (custom), avatar, hover-card, alert, accordion`.

Anything not listed is not installed by default.

---

## E. Frontend Type Contracts

Files live at `lib/types/`. Each file ends with a `// Source: backend/app/...` pointer.

- `account.ts` — `AccountStatus`, `AccountRead`, `AccountListResponse`, `AccountDetail`.
- `scan.ts` — `ScanType`, `ScanStatus`, `ScanMode`, `ScanCreateRequest`, `ScanCreateResponse`, `ScanCounts`, `ScanRead`, `ScanEventType`, `ScanEventRead`, `ScanEventList`.
- `signal.ts` — `SignalType`, `SignalRead`, `SignalList`, `SourceType`, `SourceRead`, `FetchStatus`, `FetchMethod`, `EvidenceRead`.
- `brief.ts` — `BriefRead`, `ScoreRead`.
- `outreach.ts` — `OutreachTone`, `OutreachStatus`, `OutreachRead`, `OutreachList`, `OutreachReject`, `OutreachPatch`.
- `imports.ts` — `SeedImportResponse`.
- `health.ts` — `HealthResponse`.
- `common.ts` — shared `Timestamped`, `Paginated<T>`.

Zod schemas mirror these for inputs (forms and request bodies). API responses are typed but not Zod-parsed at runtime to keep cost low.

---

## F. Data Fetching Strategy

- Single `lib/api/client.ts` thin wrapper around `fetch` with base URL, JSON parsing, error normalization (`ApiError { status, code, message }`), and timeout.
- Per-resource modules under `lib/api/`: `accounts.ts`, `scans.ts`, `signals.ts`, `briefs.ts`, `outreach.ts`, `imports.ts`, `health.ts`.
- Hooks under `lib/hooks/` (e.g., `useAccountsList`, `useAccountDetail`, `useScanStatus`, `useScanEvents`, `useAccountSignals`, `useBrief`, `usePendingDrafts`, `useDraft`, `useHealth`).
- Polling rules:
  - `useScanStatus` — `refetchInterval: 1500ms` while status in non-terminal set; stop on `completed | failed`.
  - `useScanEvents` — incremental fetch via `after_sequence` cursor at the same cadence, using `keepPreviousData`.
  - On scan completion, programmatically `queryClient.invalidateQueries` for the account detail, signals, brief, and pending drafts.
- Mutations:
  - `useStartScan` — optimistic local "queued" state.
  - `useApproveDraft`, `useRejectDraft`, `useEditDraft`, `useRegenerateBrief` — toast on success/error; disable primary button while pending.

---

## G. Demo Flow Coverage Matrix

| Step | Screen | Component | Backend call |
|---|---|---|---|
| 1. Open app | `/accounts` | `AccountTable`, `AccountKpiStrip` | `GET /accounts`, `GET /health` |
| 2. Spot warming account | `/accounts` | row score chip | — |
| 3. Open account | `/accounts/[id]` | `AccountHeader`, `AccountScoreStrip` | `GET /accounts/{id}` |
| 4. Click `Run Live Scan` | overlay | `LiveScanPanel` | `POST /accounts/{id}/scans` |
| 5. Watch sources arrive | overlay | `ScanSourceStream`, `ScanEventList` | `GET /scans/{id}` poll, `GET /scans/{id}/events`, `GET /scans/{id}/sources` |
| 6. Signals appear | detail main | `SignalCard`, `SignalTimeline` | `GET /accounts/{id}/signals` |
| 7. Score updates to sales-ready | detail | `AccountScoreStrip` | `GET /accounts/{id}` |
| 8. Open evidence | drawer | `EvidenceDrawer` | `GET /scans/{id}/evidence` |
| 9. Show graph | tab | `AccountKnowledgeGraph` | derived client-side from signals + recent_signals + people |
| 10. Brief refreshes | right panel | `AccountBriefPanel` | `GET /accounts/{id}/brief` |
| 11. Outreach draft appears | right panel + `/outreach` | `DraftEditor`, `GuardrailPanel` | `GET /outreach/pending`, `GET /outreach/{id}` |
| 12. Approve | inline | `DraftEditor` | `POST /outreach/{id}/approve` |

Required visual states for the rehearsal:

- Empty (`/imports` first run, `/accounts` zero, `/outreach` zero).
- Loading skeletons on every route.
- Active scan with phases moving.
- Completed scan with sales-ready ring.
- Scan with one failed source but otherwise successful.
- Pending draft, approved draft, rejected draft (each with the right toast).

---

## H. Phase Plan

### Phase 1 — Premium shell + accounts surface (must-have)

1. Scaffold Next.js app, TS config, Tailwind, theme tokens, Inter + JetBrains Mono.
2. Install shadcn primitives; create `StatusChip`, `ScoreRing`, `MetricTile`, `EmptyState`, `LoadingSkeleton`.
3. Build `AppShell`, `Sidebar`, `TopCommandBar`, `IntegrationStatus`.
4. Wire `lib/api/client.ts`, `accounts.ts`, `health.ts`, query provider.
5. Build `/accounts`: KPI strip, filters bar, account table, preview drawer.
6. Build `/accounts/[id]` skeleton: header, score strip, two-column layout shell.
7. Build `/imports`: dropzone, preview, submit, summary.

### Phase 2 — Demo flow (must-have)

1. `LiveScanPanel` with phase stepper, counters, event stream.
2. `SignalCard` and basic `SignalTimeline`.
3. `EvidenceDrawer`.
4. `AccountBriefPanel` with regenerate.
5. `/outreach` list + editor + guardrails + approve/reject/edit.

### Phase 3 — Product depth (nice-to-have)

1. `AccountKnowledgeGraph` with React Flow.
2. Full signal timeline grouping.
3. `/signals` cross-account feed.
4. `/scans` cross-account scans page.

### Phase 4 — Polish

1. Responsive QA at 1440 / 1280 / 1024 / 390.
2. `prefers-reduced-motion`.
3. Empty/error/loading designs at parity with happy paths.
4. Microinteractions (Framer fade-and-slide on card mount, ring tween, stepper progress bar).
5. Keyboard tab order and focus rings.
6. Optional dark mode tokens.

---

## I. Required Dependencies

```text
runtime
  next
  react, react-dom
  typescript
  tailwindcss, postcss, autoprefixer
  @tanstack/react-query
  @tanstack/react-table
  recharts
  reactflow
  lucide-react
  react-hook-form, @hookform/resolvers, zod
  react-markdown, remark-gfm
  framer-motion
  date-fns
  sonner
  cmdk
  class-variance-authority, clsx, tailwind-merge
  next-themes (kept for Phase 4 dark mode)

dev
  eslint, eslint-config-next, prettier, prettier-plugin-tailwindcss
  @types/node, @types/react, @types/react-dom
  vitest, @testing-library/react, jsdom (only if we choose to add unit tests later)
  @playwright/test (Phase 4 only)
```

No `bcrypt`, `axios`, `lodash`, `dayjs`, `moment`, or `redux`. We keep the bundle lean.

---

## J. Open Risks

1. **Graph data shape** — Phase 1 derives nodes/edges client-side from `account`, `recent_signals`, and `signals`. Confirmed acceptable for the hackathon. A backend `/accounts/{id}/graph` endpoint is deferred and only added if relationships need server-side ranking.
2. **Server-Sent Events** — backend currently exposes polling only. SSE is on the backend roadmap. We will design the live scan panel for swappable transports (custom hook abstracts polling vs SSE) but ship polling at MVP.
3. **Bundle size for React Flow** — pulled lazily via `next/dynamic` with SSR off, only on the graph tab. Confirmed no impact on first load.
4. **Logos and avatars** — we will not use real third-party brand logos for seeded accounts (trademark risk). We will draw monogram avatars from initials with a deterministic hash-to-color so they look intentional.
5. **Demo network reliability** — even in mock mode, the live scan panel feels live because of artificial phase delays. We must not let actual network blips look like the product is broken. We will add a 3s grace before showing any error toast for `GET /scans/{id}` failures.
6. **Hardcoded demo copy** — vendor name (`VectorLake`), seeded accounts, and champion (`Maya Chen`) are baked into backend fixtures, not the frontend. The frontend should never invent its own. Confirmed and reflected in A5.

---

## K. Definition Of Done (Frontend MVP)

The frontend is "demo-ready" when all of the following are true:

- App opens at `/accounts` and shows seeded data without manual setup.
- Account list loads in under 300ms with the dev backend.
- Detail page renders header, score strip, signals, brief, and outreach panel for any sales-ready seeded account.
- `Run Live Scan` opens the live panel, polls every 1.5s, shows phases moving, and ends in a sales-ready state for at least one demo account.
- Evidence Drawer opens from any signal card or brief citation and renders the full markdown.
- Outreach approval flow updates state immediately and surfaces a toast.
- Mock and live mode are both visible in the top bar and reflect `/health`.
- Layout is sharp at 1440px and 1280px; no layout regressions at 390px on the four MVP routes.
- Lighthouse a11y score >= 95 on `/accounts` and `/accounts/[id]`.
- No console errors during the rehearsed demo path.

---

## L. Unblocked-To-Start Status

All four blocking items from the prior pass are resolved:

- Brand: **Tendril**.
- First-run UX: **auto-prime the demo seed**, manual import remains visible.
- Knowledge graph: **client-derived for Phase 1**.
- Package manager: **pnpm**.

Phase 1 scaffolding starts now.
