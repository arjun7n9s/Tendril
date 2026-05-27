# Tendril

Tendril is a live GTM intelligence workspace that helps revenue teams spot the right account at the right moment using public web signals, evidence-backed AI, and human-approved outreach.

It scans public sources, turns account changes into structured signals, explains why an account matters now, and keeps every recommendation tied to evidence.

## Current Build

- FastAPI backend scaffold
- SQLite app state
- Seed CSV import
- Account APIs
- Mock scan runner
- Signal scoring
- Evidence-backed briefs
- Human-reviewable outreach drafts
- Scan event trace
- JSONL memory stub for future Cognee integration

## Backend Quick Start

```bash
cd backend
uv sync
uv run pytest
uv run uvicorn app.main:app --reload
```

The backend reads configuration from the project-root `.env`. Use `.env.example` as the safe template.

## Safety

Do not commit `.env`, local databases, virtual environments, or runtime memory files. The repository is configured to ignore those artifacts.

