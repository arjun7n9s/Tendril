# SignalGraph Frontend Architecture And Product UI Plan

**Audience:** Frontend engineering, product, and design  
**Product:** SignalGraph - Autonomous GTM Change Intelligence  
**Goal:** Build a premium enterprise dashboard that makes live web intelligence feel trustworthy, explainable, and immediately actionable.

## 1. Product Experience North Star

SignalGraph should not feel like a hackathon table UI. It should feel like the command center a revenue team would pay for: calm, dense, fast, evidence-backed, and executive-ready.

The interface must communicate four things within the first 10 seconds:

1. This system is actively monitoring the live web.
2. Every recommendation is grounded in cited evidence.
3. The AI understands account context over time, not just one scraped page.
4. Humans remain in control before any outreach leaves the system.

The best mental model is:

> Bloomberg Terminal meets Gong/Clay/Attio, purpose-built for GTM intelligence.

Not a landing page. Not a chatbot. Not a generic CRM clone.

## 2. Product Context For The Frontend Team

### What SignalGraph Actually Does

SignalGraph is a GTM intelligence workspace. A sales or revenue team uploads a small seed CRM file, chooses a target account, and asks the system to scan the live web. The backend uses Bright Data to discover and fetch public evidence, AI/ML API to extract signals, and a memory layer to preserve account context. The frontend turns that backend work into a clear decision:

> "Is this account worth acting on right now, and what evidence supports that?"

The user should never feel like they are looking at raw scraping output. They should feel like they are looking at an analyst-grade account intelligence brief that happened to be generated live.

### The Hackathon Demo Story

The frontend should be built around one polished demo path:

1. Start in the Accounts Command Center with 5 seeded accounts.
2. One account looks promising but not fully sales-ready yet.
3. Open the account into the Account Intelligence Room.
4. Click `Run Live Scan`.
5. Watch Bright Data source discovery and scraping happen in a live scan panel.
6. See evidence-backed signals appear.
7. See score move into `Sales-ready`.
8. Open the evidence drawer to prove the AI has receipts.
9. Show the knowledge graph/timeline to prove memory and relationships.
10. Review a safe outreach draft.
11. Approve the draft as human-in-the-loop.

If a screen does not support this demo path, it is secondary.

### Primary Users

**Revenue Leader**
- Wants to know which accounts deserve attention today.
- Cares about score, evidence, timing, and pipeline impact.
- Needs confidence that AI is not hallucinating.

**Sales Rep / Account Executive**
- Wants a fast account brief and a safe first message.
- Cares about "why now" and what to say next.
- Needs citations so they can trust the recommendation.

**RevOps / GTM Ops**
- Cares about data quality, source traceability, repeatable workflow, and CRM-readiness.
- Wants imports, scan health, guardrails, and integration status.

### Emotional Design Target

The UI should feel:
- Calm, not flashy.
- Intelligent, not magical.
- Premium, not decorative.
- Operational, not marketing-heavy.
- Trustworthy, not surveillance-heavy.

The best user reaction is:

> "I can see exactly why this account matters, where the evidence came from, and what I should do next."

## 3. Product And Visual Inspiration

Use these as directional references, not clones.

### Clay

Inspiration:
- Powerful GTM workflow feel.
- Dense data enrichment interfaces.
- Rows and columns with clear enrichment status.
- Strong sense of "data is being worked on."

What to borrow:
- Account table density.
- Enrichment/source status chips.
- Clear per-row actionability.

What not to copy:
- Do not make SignalGraph feel like a spreadsheet-first product. Our hero screen is account intelligence, not a giant grid.

### Attio

Inspiration:
- Clean CRM primitives.
- Beautiful object pages.
- Calm, modern SaaS polish.
- Strong balance of table + record detail.

What to borrow:
- Account object page quality.
- Subtle borders, clean spacing, restrained type.
- Relationship-aware CRM feel.

What not to copy:
- Do not become a generic CRM. Our differentiator is live evidence and signal reasoning.

### Gong / Clari

Inspiration:
- Revenue intelligence seriousness.
- Executive-grade summaries.
- Clear next-best action framing.

What to borrow:
- Confidence in business value.
- Deal/account health presentation.
- Executive summary language.

What not to copy:
- Avoid sales coaching clutter. SignalGraph is about live market/account signals.

### Bloomberg Terminal / Linear

Inspiration:
- Dense information architecture.
- Fast scanning.
- Compact metadata.
- Keyboard/command feel.

What to borrow:
- Command-center energy.
- Efficient tables and panels.
- Clear status and event trace.

What not to copy:
- Do not make it visually overwhelming or terminal-like. It still needs modern SaaS clarity.

### Palantir / Datadog / Security Consoles

Inspiration:
- Evidence trails.
- Event timelines.
- Graph relationships.
- Source inspection.

What to borrow:
- Investigation workflow.
- Evidence drawer.
- Timeline and relationship graph.

What not to copy:
- Avoid a cyber/security aesthetic. This is revenue intelligence.

### Final Design Blend

The intended blend:

```text
Attio object elegance
+ Clay enrichment density
+ Gong revenue clarity
+ Datadog evidence/event trace
+ Linear-level interaction polish
```

## 4. Frontend Stack

Use a modern, production-grade Next.js stack.

- **Framework:** Next.js App Router
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Component system:** shadcn/ui, customized heavily
- **Data fetching:** TanStack Query
- **Tables:** TanStack Table
- **Charts:** Recharts or Tremor-style custom charts
- **Graph view:** React Flow for relationship graphs
- **Timeline:** Custom component; avoid overusing chart libraries
- **Icons:** Lucide React
- **Forms:** React Hook Form + Zod
- **Markdown rendering:** `react-markdown` with a constrained prose theme
- **State:** URL state for filters/tabs; local component state for drawers/modals
- **Motion:** Framer Motion for subtle scan/progress transitions

shadcn/ui note: use shadcn as owned source components, not as a visual ceiling. Components should be composed into custom product primitives such as `SignalCard`, `ScoreRing`, `EvidenceDrawer`, `ScanTimeline`, and `AccountIntelligencePanel`.

## 5. Design Principles

### Dense, Not Cramped

Revenue users scan many accounts quickly. Use compact layouts, tight tables, small-but-readable labels, and predictable controls. Avoid oversized marketing sections.

### Evidence First

Every signal card, score, brief, and draft should expose the evidence behind it. Citations are not a footnote; they are a core interaction.

### AI With Receipts

Never present AI output as magic. The UI should show:
- Fact
- Inference
- Confidence
- Evidence URL
- Recommended action

### Human Approval Is A Feature

The approval workflow should look intentional and premium, not like a compliance afterthought.

### Live But Controlled

The live scan experience should feel dynamic, but not chaotic. Use progress phases, source counters, and status chips instead of noisy animation.

## 6. Visual Design Direction

### Overall Feel

SignalGraph should feel expensive, calm, analytical, and sharp. Think serious GTM operations software with a little intelligence-console energy.

Recommended base:
- Light-first interface for readability and enterprise credibility.
- Optional dark mode later, but do not make the whole product dark slate by default.
- Use rich neutrals, crisp borders, and selective accent color.

### Palette

Avoid a one-note blue/slate or purple AI dashboard. Use a balanced palette:

- **Canvas:** near-white `#F7F8F6`
- **Surface:** white `#FFFFFF`
- **Raised surface:** `#F1F4F2`
- **Text primary:** charcoal `#171A1C`
- **Text secondary:** graphite `#5D656B`
- **Border:** cool gray `#DDE3E0`
- **Primary accent:** signal green `#0F9F6E`
- **Secondary accent:** cobalt `#3457D5`
- **Evidence accent:** amber `#C47A1D`
- **Risk accent:** red `#C2413A`
- **Graph accent:** teal `#138A8A`

Use color semantically:
- Green = sales-ready / verified
- Amber = inferred / needs review
- Red = risk / failed / rejected
- Blue = live scan / system process
- Teal = graph relationship / memory

### Typography

- Use Inter, Geist, or similar.
- Keep letter spacing at `0`.
- Use compact, work-focused type:
  - Page title: 24-30px
  - Section title: 16-18px
  - Table text: 13-14px
  - Metadata: 11-12px
- Avoid huge hero typography inside the app.

### Shape And Spacing

- Cards: max `8px` radius.
- Buttons: `6px` radius.
- Inputs: `6px` radius.
- Use 1px borders more than heavy shadows.
- Shadows should be rare and subtle.
- No decorative gradient blobs, orbs, or floating glassmorphism.

## 7. Screen Moodboards In Words

### Accounts Command Center

Should feel like:
- A revenue operations cockpit.
- A prioritized account queue.
- A place where a manager can instantly see where to focus.

Visual cues:
- Compact KPI strip.
- Dense account table.
- Score bars and signal chips.
- Filters that feel utilitarian, not decorative.

Avoid:
- Large cards for every account.
- Marketing dashboard hero blocks.
- Empty whitespace that makes the product feel underpowered.

### Account Intelligence Room

Should feel like:
- An analyst brief plus live investigation workspace.
- The main "million-dollar product" screen.

Visual cues:
- Strong account header.
- `Why now` strip above the fold.
- Signals in the main column.
- Brief/outreach in a right-side intelligence panel.
- Evidence drawer available from every claim.

Avoid:
- Hiding the brief below the fold.
- Treating signals as generic notification cards.
- Making the graph the whole product. Graph is supporting proof, not the main workflow.

### Live Scan Panel

Should feel like:
- A controlled mission log.
- Bright Data visibly doing real work.

Visual cues:
- Phase stepper.
- Event stream.
- Source domains appearing one by one.
- Integration badges.
- Counts for discovered, fetched, extracted, failed.

Avoid:
- A single spinner.
- Fake sci-fi animation.
- Full raw logs that overwhelm the user.

### Evidence Drawer

Should feel like:
- A citation inspector.
- The place where trust is won.

Visual cues:
- Source URL and fetch method at top.
- Highlighted excerpt.
- Related signals.
- Open original source action.

Avoid:
- Dumping huge raw HTML.
- Making citations tiny.
- Hiding fetch method.

### Outreach Cockpit

Should feel like:
- A careful review station.
- Human-in-the-loop by design.

Visual cues:
- Draft queue on left.
- Editor in middle.
- Evidence/guardrails on right.
- Clear approve/reject state.

Avoid:
- Any primary `Send` button.
- Overly playful email-generation UI.
- Unsupported personalization.

## 8. Demo Data Context For Mock UI

Use fictional product/vendor context so the interface can look real before backend data lands.

Demo vendor:
- `VectorLake`
- Category: developer data platform
- ICP: fintech and data-heavy SaaS teams
- Keywords: Snowflake, Kafka, dbt, Airflow, data reliability, migration, compliance, observability
- Competitors: Databricks, Fivetran, Monte Carlo, Airbyte, Confluent

Example accounts:
- Northstar Bank - fintech, 1,200 employees, target
- Meridian Health Cloud - healthtech, 800 employees, target
- AtlasPay - payments, 450 employees, target
- OrbitCart - retail tech, 600 employees, target
- FluxForge - developer tools, 180 employees, customer

Example signals:
- Hiring for Senior Data Platform Engineer mentioning Kafka and Snowflake.
- Engineering blog post about warehouse migration.
- Public GitHub repo references dbt orchestration.
- Press release about compliance expansion.
- Former champion appears on a public engineering author page.

Example `why now`:
- `Hiring spike + migration content + prior champion overlap`
- `Compliance expansion + Snowflake roles + data reliability language`
- `New platform team hiring + public dbt usage`

These examples are not final business truth. They exist so the frontend can design realistic density and states immediately.

## 9. Premium UI Checklist

Before calling any screen done, check:

- Does the screen answer "why should I care right now?"
- Can the user see evidence for every important claim?
- Is there a clear next action?
- Does the layout still look strong with realistic dense data?
- Are scores explained, not just shown?
- Does the scan state prove Bright Data is being used?
- Are risky/uncertain claims visually separated from verified facts?
- Does the product feel like a tool people use daily, not a demo page?
- Does the UI remain polished at 1440px, 1280px, and mobile width?
- Are empty/loading/error states designed with the same care as happy paths?

## 10. Application Information Architecture

Primary navigation should be a left sidebar with compact labels and icons.

Routes:

```text
/
/accounts
/accounts/[accountId]
/signals
/scans
/outreach
/imports
/settings
```

MVP routes:

```text
/accounts
/accounts/[accountId]
/outreach
/imports
```

### Global Shell

Persistent layout:
- Left sidebar navigation.
- Top command bar.
- Workspace content.
- Right contextual drawer when needed.

Sidebar:
- Accounts
- Signal Feed
- Live Scans
- Outreach Review
- Imports
- Settings

Top command bar:
- Global search: accounts, people, signals, evidence.
- Environment chip: `Mock` / `Live`.
- Integration status chips: Bright Data, Cognee, AI/ML API.
- Primary action: Import CSV or Run Scan depending on context.

## 11. Core Screens

## 11.1 Accounts Command Center

Route: `/accounts`

Purpose:
Give the revenue team a portfolio-level view of which accounts are heating up and why.

Layout:
- Header with title, account count, last scan time, and import/run controls.
- KPI strip with compact metrics.
- Filter bar.
- Account intelligence table.
- Optional right drawer for selected account preview.

KPI strip:
- Sales-ready accounts
- New signals today
- Average evidence confidence
- Live scans running
- Pending outreach drafts

Filters:
- Status
- Score range
- Industry
- Signal type
- Last scanned
- Sales-ready only
- Mock/live mode

Account table columns:
- Account
- Fit
- Timing
- Relationship
- Evidence
- Total score
- Top signal
- Signal count
- Last scanned
- Next action

Premium UI details:
- Total score shown as a compact segmented score bar, not just a number.
- Top signal row includes a semantic icon and confidence chip.
- Clicking an account opens the Account Intelligence Room.
- Hovering a score reveals mini breakdown tooltip.
- Empty state should invite seed import, not explain the whole product.

## 11.2 Account Intelligence Room

Route: `/accounts/[accountId]`

Purpose:
This is the flagship demo screen. It must show why SignalGraph is valuable.

Recommended layout:

```text
Account Header
Score / Why Now Strip
------------------------------------------------
Left Main Column                 Right Column
Signal Timeline                  Account Brief
Evidence-backed Signal Cards     Outreach Draft
Source Discovery Results         Score Breakdown
------------------------------------------------
Bottom / Drawer
Knowledge Graph + Evidence Drawer
```

### Account Header

Content:
- Account name and domain
- Industry, company size, region
- Status chip
- Last scanned timestamp
- Primary button: `Run Live Scan`
- Secondary button: `Generate Draft` if eligible

Use icons:
- Play or Radar icon for scan
- Upload icon for import
- ExternalLink for domain
- ShieldCheck for evidence verified

### Score / Why Now Strip

A horizontal intelligence summary:
- Total score ring
- Fit score
- Timing score
- Relationship score
- Evidence score
- Sales-ready status
- "Why now" one-liner

Example:
> Hiring spike + data migration content + prior champion overlap.

This should be visible above the fold.

### Signal Timeline

A chronological view of extracted changes:
- Hiring
- Tech stack
- Product launch
- Competitor mention
- Champion move
- Market event

Each timeline item shows:
- Signal type icon
- Date observed
- Confidence
- Source domain
- Expand/collapse details

Use the timeline to show "change over time", not just isolated cards.

### Signal Cards

Each `SignalCard` must contain:
- Signal type chip
- Signal title
- Fact text
- Inference text
- Recommended action
- Confidence meter
- Evidence citation button
- Source domain
- Observed date

Card actions:
- View evidence
- Add to brief
- Generate outreach angle
- Dismiss signal

Do not hide citations behind tiny links. Evidence access is part of the trust experience.

### Account Brief Panel

A right-column panel with:
- Executive summary
- Why now
- Key evidence bullets
- Risks / uncertainty
- Recommended next steps

Design:
- Keep it compact and scannable.
- Use collapsible sections.
- Every bullet with a citation should show a small source badge.

### Outreach Draft Panel

Human-reviewable draft:
- Subject input
- Body textarea
- Tone segmented control: Warm, Technical, Executive, Concise
- Guardrail checklist
- Evidence chips used in draft
- Buttons: Approve, Edit, Reject

Guardrail checklist:
- Uses public evidence
- Avoids creepy phrasing
- No unsupported claims
- Human approval required

## 11.3 Live Scan Experience

Can appear as an in-page module or slide-over drawer after clicking `Run Live Scan`.

Purpose:
Make Bright Data usage and agent progress visible.

Phases:
1. Queued
2. Discovering sources
3. Scraping with Bright Data
4. Extracting signals
5. Updating Cognee memory
6. Scoring account
7. Generating brief
8. Completed

UI elements:
- Horizontal phase stepper.
- Current phase status.
- Source counter: discovered, selected, fetched, failed.
- Evidence stream showing URLs as they complete.
- Integration badges showing Bright Data, Cognee, AI/ML API.
- Final "Intelligence ready" completion state.

Use polling every 1.5-2 seconds for MVP. Add SSE only if backend finishes it early.

Important demo detail:
Show fetch method metadata when available:
- `brightdata_mcp`
- `unlocker`
- `browser_api`
- `web_scraper_api`
- `mock`

This makes the partner integration obvious to judges.

## 11.4 Evidence Drawer

Opened from any citation or evidence button.

Purpose:
Show exactly what the AI saw.

Content:
- Source title
- URL
- Fetch method
- Fetched timestamp
- Source type
- Highlighted relevant excerpt
- Full markdown preview
- Signals extracted from this evidence
- Open source button

Design:
- Right-side drawer, 420-560px wide on desktop.
- Full-screen sheet on mobile.
- Monospace only for raw snippets, not whole UI.

## 11.5 Knowledge Graph View

Route section inside `/accounts/[accountId]` or tab: `Graph`

Purpose:
Make Cognee's memory visible.

Use React Flow for a focused graph, not a sprawling spiderweb.

Node types:
- Account
- Person
- Champion
- Signal
- Evidence
- Tech keyword
- Competitor
- ICP profile

Edge labels:
- works_at
- previously_used
- mentions
- matches_icp
- evidenced_by
- triggered_by

Graph controls:
- Fit to view
- Filter node types
- Show evidence edges
- Show champion path

Premium detail:
When a user clicks a node, open a side panel with related facts and citations.

## 11.6 Signal Feed

Route: `/signals`

Purpose:
Cross-account intelligence feed for reps and GTM leads.

Layout:
- Filterable feed/table hybrid.
- Left filters.
- Main feed grouped by date or account.
- Right preview drawer.

Filters:
- Signal type
- Score range
- Confidence
- Source type
- Account status
- Sales-ready

This route is optional for the hackathon if `/accounts` and `/accounts/[id]` are excellent.

## 11.7 Outreach Review Cockpit

Route: `/outreach`

Purpose:
Human-in-the-loop approval station.

Layout:

```text
Draft Queue        Draft Review + Editor        Evidence / Guardrails
```

Draft queue:
- Account
- Recipient/person if available
- Score
- Tone
- Status
- Created time

Draft review:
- Editable subject
- Editable body
- Regenerate controls
- Tone segmented control
- Approve / Reject buttons

Evidence/guardrail panel:
- Evidence used
- Claims made in draft
- Unsupported claim warnings
- Guardrail checklist

Approval UX:
- Approve should change state to `approved` and show a clear "Logged for export" state.
- Reject should require optional feedback.
- Edit should autosave or have explicit save state.

Do not include a "Send email" primary action in the MVP.

## 11.8 Imports

Route: `/imports`

Purpose:
Load seed CSV and show import health.

UI:
- Drag/drop CSV upload.
- Required column checklist.
- Preview first 10 rows.
- Import summary:
  - accounts created
  - people created
  - ICP profiles created
  - warnings
- Link to Accounts after success.

Premium detail:
Show import mapping in a compact review table before final submit.

## 12. Component Architecture

Recommended structure:

```text
frontend/
  app/
    layout.tsx
    accounts/
      page.tsx
      [accountId]/
        page.tsx
    outreach/
      page.tsx
    imports/
      page.tsx
  components/
    app-shell/
      sidebar.tsx
      top-command-bar.tsx
      integration-status.tsx
    accounts/
      account-table.tsx
      account-score-strip.tsx
      account-header.tsx
      account-preview-drawer.tsx
    scans/
      live-scan-panel.tsx
      scan-phase-stepper.tsx
      scan-source-stream.tsx
    signals/
      signal-card.tsx
      signal-timeline.tsx
      confidence-meter.tsx
      signal-type-chip.tsx
    evidence/
      evidence-drawer.tsx
      source-badge.tsx
      citation-button.tsx
    graph/
      account-knowledge-graph.tsx
      graph-node-panel.tsx
    briefs/
      account-brief-panel.tsx
      cited-brief-section.tsx
    outreach/
      draft-queue.tsx
      draft-editor.tsx
      guardrail-panel.tsx
    imports/
      seed-upload-dropzone.tsx
      csv-preview-table.tsx
    primitives/
      score-ring.tsx
      metric-tile.tsx
      status-chip.tsx
      empty-state.tsx
      loading-skeleton.tsx
  components/ui/
    shadcn generated components
  lib/
    api/
      client.ts
      accounts.ts
      scans.ts
      signals.ts
      briefs.ts
      outreach.ts
      imports.ts
    hooks/
      use-scan-status.ts
      use-account-detail.ts
      use-signal-feed.ts
    types/
      account.ts
      scan.ts
      signal.ts
      evidence.ts
      brief.ts
      outreach.ts
    utils/
      score.ts
      dates.ts
      citations.ts
```

## 13. shadcn/ui Components To Use

Install only what is needed.

Core:
- Button
- Input
- Textarea
- Select
- Checkbox
- Tabs
- Badge
- Table
- Dialog
- Sheet
- Drawer if available
- Tooltip
- Popover
- Dropdown Menu
- Command
- Progress
- Skeleton
- Separator
- Scroll Area
- Toast/Sonner

Use custom wrappers for domain-specific behavior:
- `StatusChip`
- `SourceBadge`
- `ConfidenceMeter`
- `ScoreRing`
- `CitationButton`
- `RunScanButton`

## 14. Data Fetching Strategy

Use TanStack Query for all backend reads and mutations.

Recommended query keys:

```ts
["accounts", filters]
["account", accountId]
["account-signals", accountId, filters]
["account-brief", accountId]
["scan", scanId]
["scan-sources", scanId]
["scan-evidence", scanId]
["outreach-pending"]
["outreach", draftId]
```

Polling:
- Poll active scan every 1.5-2 seconds.
- Stop polling when status is `completed` or `failed`.
- Refetch account detail, signals, brief, and pending outreach after scan completes.

Mutation UX:
- Optimistic state for starting scans.
- Toast on scan started, import complete, draft approved, draft rejected.
- Disable primary actions while mutation is pending.

## 15. Frontend Type Contracts

Mirror backend types in TypeScript.

### Account Summary

```ts
type AccountSummary = {
  id: string
  name: string
  domain?: string
  industry?: string
  company_size?: string
  region?: string
  status: "target" | "customer" | "former_customer" | "competitor" | "ignored"
  latest_score?: Score
  top_signal?: SignalSummary
  last_scanned_at?: string
}
```

### Score

```ts
type Score = {
  fit_score: number
  timing_score: number
  relationship_score: number
  evidence_score: number
  total_score: number
  sales_ready: boolean
  score_reasoning_json?: Record<string, unknown>
}
```

### Scan

```ts
type Scan = {
  id: string
  account_id: string
  scan_type: "account_watchtower" | "champion_mobility" | "lookalike_discovery"
  status: "queued" | "discovering" | "scraping" | "extracting" | "graphing" | "scoring" | "briefing" | "completed" | "failed"
  mode: "live" | "mock" | "cached"
  progress_percent: number
  error_message?: string
  started_at?: string
  completed_at?: string
}
```

### Signal

```ts
type Signal = {
  id: string
  scan_id: string
  account_id: string
  person_id?: string
  signal_type:
    | "hiring"
    | "tech_stack"
    | "migration"
    | "funding"
    | "product_launch"
    | "leadership_change"
    | "competitor_mention"
    | "champion_move"
    | "market_event"
    | "other"
  title: string
  summary: string
  fact_text: string
  inference_text?: string
  recommended_action?: string
  evidence_url: string
  confidence: number
  observed_at?: string
  recency_days?: number
}
```

### Scan Event

```ts
type ScanEvent = {
  id: string
  scan_id: string
  sequence: number
  phase:
    | "discovering"
    | "scraping"
    | "extracting"
    | "graphing"
    | "scoring"
    | "briefing"
  event_type:
    | "phase_started"
    | "phase_completed"
    | "bright_data_call"
    | "bright_data_call_replayed"
    | "aiml_call"
    | "aiml_call_replayed"
    | "memory_write"
    | "memory_write_replayed"
    | "warning"
    | "error"
  message: string
  metadata_json?: Record<string, unknown>
  created_at: string
}
```

Use `ScanEvent` to power the live scan panel. Do not show raw secrets or auth-bearing URLs even if a backend bug sends them.

## 16. Interaction Design Details

### Running A Scan

User flow:
1. User clicks `Run Live Scan`.
2. Button changes to loading state.
3. Live scan panel opens.
4. Phase stepper starts moving.
5. Source stream populates.
6. Signals appear as they become available if backend supports it; otherwise reveal at completion.
7. Account score updates.
8. Brief panel refreshes.
9. Outreach draft appears if sales-ready.

### Viewing Evidence

User flow:
1. User clicks citation/evidence button.
2. Evidence drawer opens.
3. Relevant excerpt is highlighted.
4. User can inspect full markdown or open original URL.
5. Related signals are listed at bottom.

### Reviewing Outreach

User flow:
1. User opens pending draft.
2. Draft editor shows subject/body.
3. Guardrail panel shows claims and evidence.
4. User edits or changes tone.
5. User approves or rejects.
6. Queue updates immediately.

## 17. Responsive Design

Desktop is primary for hackathon demo and enterprise use.

Breakpoints:
- Desktop `>= 1280px`: full three-column layouts.
- Tablet `768-1279px`: main content plus collapsible right panels.
- Mobile `< 768px`: stacked pages, bottom sheet drawers, horizontally scrollable tables.

Rules:
- Tables may horizontally scroll on mobile.
- Drawers become full-screen sheets on mobile.
- Score strip wraps into two rows.
- Buttons must not truncate important action labels.
- No text may overlap or escape fixed cards.

## 18. Accessibility

Minimum:
- Keyboard reachable sidebar, tables, tabs, drawers, dialogs.
- Visible focus states.
- Proper labels for icon buttons.
- Tooltips for unfamiliar icons.
- Color is never the only signal; pair with text or icons.
- Tables use semantic table markup.
- Motion respects reduced-motion preference.

## 19. Demo Polish Requirements

The demo should have a rehearsed "wow path":

1. Start on `/accounts` with 5 seeded accounts.
2. One account is clearly warming up but not fully sales-ready.
3. Open the account.
4. Click `Run Live Scan`.
5. Live panel shows Bright Data fetching sources.
6. Signal cards populate with citations.
7. Score changes to sales-ready.
8. Graph view shows ICP + champion + evidence relationship.
9. Brief updates.
10. Outreach draft appears with guardrail checklist.
11. User approves the draft.

Required visual states:
- Empty import state.
- Loading skeletons.
- Active scan state.
- Completed scan state.
- Failed source, successful scan state.
- Sales-ready state.
- Pending review state.
- Approved state.

## 20. Implementation Priority

### Phase 1: Premium Shell And Mock Data

- App shell with sidebar and top command bar.
- Theme tokens and typography.
- Mock API layer.
- Accounts command center.
- Account detail layout.
- Signal cards.
- Score strip.

### Phase 2: Demo Flow

- Import page.
- Run scan action.
- Live scan panel with polling.
- Evidence drawer.
- Account brief panel.
- Outreach draft panel.

### Phase 3: Product Depth

- React Flow knowledge graph.
- Signal timeline.
- Outreach cockpit.
- CSV preview.
- Better filters and table controls.

### Phase 4: Polish

- Responsive QA.
- Reduced-motion support.
- Empty/error states.
- Microinteractions.
- Keyboard and focus checks.

## 21. Frontend Definition Of Done

The frontend is ready for demo when:

- The app opens directly into the product dashboard.
- Seed import is possible or mock seed data is already loaded.
- Accounts can be filtered and opened.
- Account detail shows score, signals, evidence, brief, and outreach draft.
- Live scan progress is visible and tied to backend status.
- Evidence drawer proves every AI claim is grounded.
- Outreach approval flow is complete.
- Mock mode works without backend instability.
- Live mode can demonstrate at least one Bright Data-powered scan.
- Layout looks polished at 1440px, 1280px, and 390px widths.

## 22. What To Avoid

- Do not build a marketing homepage.
- Do not make the UI a chatbot-first experience.
- Do not make the app mostly empty cards.
- Do not hide evidence behind tiny links.
- Do not rely on a single dark slate palette.
- Do not use giant decorative gradients or abstract AI visuals.
- Do not auto-send outreach.
- Do not make scan progress a vague spinner.
- Do not present unsupported AI conclusions as facts.

## 23. Suggested Product Copy

Primary scan button:
- `Run Live Scan`

Sales-ready badge:
- `Sales-ready`

Near-miss badge:
- `Needs one more signal`

Evidence button:
- `View evidence`

Brief heading:
- `Why now`

Outreach guardrail heading:
- `Human approval required`

Scan completion toast:
- `New account intelligence is ready`

Approved draft toast:
- `Draft approved and logged`

Rejected draft toast:
- `Draft rejected`
