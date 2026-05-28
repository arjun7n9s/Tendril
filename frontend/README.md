# Tendril Frontend

The Next.js dashboard for **Tendril**, a live GTM change intelligence workspace. Tendril scans the public web with Bright Data, turns account changes into evidence-backed signals via AI/ML API, and explains why an account matters now using a Cognee-backed memory graph.

This package is the user-facing surface. The FastAPI backend lives at `../backend` and owns scans, scoring, briefs, and outreach.

> Naming note: the codebase predates the brand decision and you may still see `SignalGraph` in deeper engineering docs (`kiro/kiro-product-blueprint.md`, `kiro/kiro-frontend-architecture.md`). The product name is **Tendril**.

## Stack

- Next.js 16 (App Router, Turbopack)
- TypeScript strict
- Tailwind CSS v4 with `@theme` design tokens
- TanStack Query + Table
- Radix primitives wrapped into custom shadcn-style UI in `components/ui`
- React Flow (lazy-loaded for the Phase 3 graph view)
- Recharts, Framer Motion, lucide-react, sonner, react-hook-form + zod

## Requirements

- Node `>= 20.11`
- pnpm `>= 11` (the workspace standardizes on pnpm; do not use npm or yarn)
- The Tendril FastAPI backend running on `http://localhost:8000`

If pnpm is not yet on your path:

```bash
npm install -g pnpm
```

## Setup

```bash
pnpm install
cp .env.local.example .env.local           # adjusts NEXT_PUBLIC_API_BASE_URL if needed
pnpm sync:seed                              # copies backend/fixtures/seed_demo.csv into public/
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000). The root `/` redirects directly into `/accounts` — there is no marketing landing page.

## Common scripts

| Script             | What it does                                                                 |
| ------------------ | ---------------------------------------------------------------------------- |
| `pnpm dev`         | Next 16 dev server with Turbopack on `http://localhost:3000`                 |
| `pnpm build`       | Production build (Turbopack)                                                 |
| `pnpm start`       | Serve the production build                                                   |
| `pnpm lint`        | ESLint (Next core-web-vitals + React 19 hooks rules)                         |
| `pnpm type-check`  | `tsc --noEmit` — same TypeScript settings as the build                       |
| `pnpm sync:seed`   | Copy `backend/fixtures/seed_demo.csv` into `public/seed_demo.csv`            |

## First-run experience

The first time `/accounts` loads against an empty backend, the frontend auto-primes by POSTing the bundled `public/seed_demo.csv` to `/api/v1/import/seed` and toasts "Demo seed loaded". A session flag prevents re-priming. The `/imports` page remains available so you can drop your own CSV at any time, including a "Load demo seed" button that mirrors the auto-prime behavior.

## Environment

| Variable                   | Default                  | Purpose                                  |
| -------------------------- | ------------------------ | ---------------------------------------- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000`  | Where the FastAPI backend is reachable   |

The backend already permits `http://localhost:3000` via `CORS_ALLOWED_ORIGINS`, so no additional CORS setup is needed for local development.

## Project layout

```
app/                  # Next.js App Router routes
  (app)/              # product routes that render inside AppShell
    accounts/         # accounts command center + detail
    imports/          # seed CSV import
    outreach/         # human-in-the-loop draft cockpit (Phase 2)
  layout.tsx          # root layout with fonts, providers, toaster
  page.tsx            # redirect to /accounts

components/
  app-shell/          # sidebar, top command bar, integration chips
  accounts/           # table, score strip, header, filters
  signals/            # SignalCard
  briefs/             # AccountBriefPanel
  imports/            # SeedUploadDropzone
  primitives/         # Tendril-specific reusables (ScoreRing, MonogramTile, …)
  ui/                 # base shadcn-style primitives over Radix

lib/
  api/                # one module per backend resource
  hooks/              # TanStack Query hooks
  types/              # TS contracts mirroring backend Pydantic schemas
  providers/          # QueryProvider
  utils/              # cn, score, dates, initials
  copy.ts             # single source of truth for product copy
```

## Conventions

- **Design tokens only.** Tailwind v4 exposes the palette through `@theme` in `app/globals.css`. Components reference them via CSS variables (`var(--color-signal)`, `bg-[color:var(--color-raised)]`, …). Never introduce raw hex.
- **Types mirror the backend.** Anything in `lib/types/` ends with a `// Source: backend/app/...` pointer. When the backend schema or enum set changes, update the matching TS file.
- **API access goes through `lib/api/client.ts`.** No raw `fetch` in components; the client centralizes timeouts, JSON parsing, and `ApiError` normalization.
- **Copy lives in `lib/copy.ts`.** Edit there, not inline.

## Backend integration cheat sheet

| Frontend area              | Backend route                                              |
| -------------------------- | ---------------------------------------------------------- |
| Top bar mode + chips       | `GET /health`                                              |
| Accounts list              | `GET /api/v1/accounts`                                     |
| Account detail             | `GET /api/v1/accounts/{id}`                                |
| Account signals            | `GET /api/v1/accounts/{id}/signals`                        |
| Account brief              | `GET /api/v1/accounts/{id}/brief`                          |
| Run scan                   | `POST /api/v1/accounts/{id}/scans`                         |
| Scan poll + events         | `GET /api/v1/scans/{id}` and `/events`, `/sources`, `/evidence` |
| Outreach queue + actions   | `GET /api/v1/outreach/pending`, approve/reject/edit        |
| Seed import                | `POST /api/v1/import/seed` (multipart `file`)              |

## Status

All three planned phases have shipped. The product surfaces from `kiro/kiro-frontend-architecture.md` are live: Accounts command center, Account Intelligence Room (with Signals / Timeline / Graph tabs), Live Scan Panel, Evidence Drawer, Outreach Cockpit, Imports, Signal Feed, Live Scans. Settings is also live as of the polish pass. See `../kiro/kiro-frontend-requirements-checklist.md` for the locked decisions and `../kiro/kiro-frontend-assets-plan.md` for the asset inventory.
