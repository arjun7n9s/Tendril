# Kiro & Codex Planning Files

Every document in this folder belongs to the planning trail Tendril was built from. The folder lives next to the code so the spec is auditable alongside the implementation.

The two stages of authoring are visible in the filenames:

- **`codex-*.md`** — the early product sketch and the long-form backend implementation plan, both authored with Codex before the Kiro-driven build began.
- **`kiro-*.md`** — every requirements checklist, architecture document, phase plan, and asset inventory used to drive the build, all authored with **Kiro**.

If you want to follow how the product was specified before any code was written, read them in this order.

## Reading order

1. `codex-product-blueprint.md` — the very first sketch of the product.
2. `kiro-product-blueprint.md` — the engineered product positioning, partner story, scoring model, demo narrative.
3. `kiro-backend-requirements-checklist.md` — every backend decision and dependency locked before scaffolding.
4. `codex-backend-implementation-plan.md` — the long-form backend design (services, models, scoring, scan runner, prompts, etc.).
5. `kiro-backend-implementation-phase-plan.md` — the same design split into the phases the backend was actually built in.
6. `kiro-frontend-architecture.md` — the design language, screen-by-screen plan, and visual direction the dashboard was built against.
7. `kiro-frontend-requirements-checklist.md` — all the locked decisions for the frontend before scaffolding.
8. `kiro-frontend-assets-plan.md` — the asset inventory: brand, fonts, icons, illustrations, integration logos, copy library.
9. `kiro-external-credentials-required.md` — the partner credentials Tendril uses (Bright Data, AI/ML API, Cognee, optional Triggerware/Speechmatics).
10. `kiro-external-credentials-usage-guide.md` — how those credentials are wired into the running system.
11. `kiro-deployment-cognee-setup-plan.md` — demo-safe deployment plan plus the local/self-hosted Cognee setup.

## Conventions used across the docs

- **Status legend** — `[ ]` pending, `[x]` decided, `[~]` default assumed, `[?]` blocking question.
- **Brand note** — many of the deeper design docs were written under the working name *SignalGraph*. The shipping product is **Tendril**; treat the two as synonyms inside this folder.
- **Source pointers** — anywhere a code file mirrors a backend or frontend decision (e.g. `lib/copy.ts`, `lib/utils/score.ts`, `components/graph/graph-derive.ts`), the file ends with a comment pointing back to the section in here it was derived from.

These files are read by humans, by Kiro, and by Codex; never by the running app.
