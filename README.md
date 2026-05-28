# Tendril

Tendril is a live GTM intelligence workspace that helps revenue teams spot the right account at the right moment using public web signals, evidence-backed AI, and human-approved outreach.

It scans public sources, turns account changes into structured signals, explains why an account matters now, and keeps every recommendation tied to evidence.

Built for the **Bright Data Web Data Unlocked Hackathon**.

## What ships

- FastAPI backend with SQLite app state, mock scan runner, signal scoring, and evidence-backed briefs.
- Next.js dashboard with the Accounts command center, Account Intelligence Room (Signals, Timeline, and Knowledge Graph tabs), Live Scan Panel, Evidence Drawer, Outreach Cockpit, Imports, Signal Feed, Live Scans, and Settings.
- Bright Data, AI/ML API, and Cognee integrations behind a single `mock | live | cached` mode flag.
- Human-in-the-loop outreach review (no auto-send, ever).
- WCAG AA palette and 100/100 Lighthouse a11y on the two flagship routes.

## Backend Quick Start

```bash
cd backend
uv sync
uv run pytest
uv run uvicorn app.main:app --reload
```

The backend reads configuration from the project-root `.env`. Use `.env.example` as the safe template.

## Frontend Quick Start

```bash
cd frontend
pnpm install
pnpm sync:seed
pnpm dev
```

Open `http://localhost:3000`. The dashboard auto-primes the demo seed when the workspace is empty so it never opens to a blank state.

## Repository layout

```
backend/   FastAPI service, scan runner, signal extraction, scoring, briefs, outreach
frontend/  Next.js dashboard
kiro/      Planning, architecture, requirements, asset, and credential docs
```

## Planning trail (kiro/)

Every architecture, requirements, asset, and credential doc lives in `kiro/`. Files prefixed `kiro-*` were authored with **Kiro**; the two `codex-*` files were authored with Codex earlier in the build. Start with `kiro/README.md` for the recommended reading order.

## Safety

Do not commit `.env`, local databases, virtual environments, runtime memory files, screenshots, or build output. The repository is configured to ignore those artifacts.
