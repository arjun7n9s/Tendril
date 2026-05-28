# Tendril Frontend — Assets Plan

**Purpose:** Enumerate every visual asset, font, icon, illustration, fixture, and copy file the premium UI needs, where it comes from, and the license posture. Paired with `frontend_requirements_checklist.md`.

**Rule of thumb:** if a file lives under `frontend/public/` or `frontend/assets/`, it must be listed here with a clear source.

---

## 0. Licensing Posture

- **No third-party brand logos for fictional or seeded accounts.** Even though the seed company names happen to match no real company, we paint monograms generated from initials, not real brand marks. This avoids trademark and accidental-impersonation risk.
- **Bright Data, AI/ML API, Cognee, Triggerware, Speechmatics logos** appear only in the integration-status chips inside the top bar and in the credits area of `/settings`. Each is rendered as their official 1-color SVG mark, sourced from their public press kits or `/brand` pages. We download them once into `public/brand/` and never modify their proportions.
- **Fonts** are Google Fonts (Inter and JetBrains Mono), self-hosted via `next/font` to avoid third-party CDN coupling.
- **Icons** are Lucide (ISC license), shipped as React components, no SVG download needed.
- **Illustrations** are custom-drawn SVG, abstract, no recognizable people or trademarked shapes.

---

## 1. Brand Identity

| Asset | Format | Location | Source |
|---|---|---|---|
| Wordmark `Tendril` | SVG, monochrome dark | `public/brand/tendril-wordmark.svg` | Custom, drawn in code |
| Wordmark inverse | SVG, monochrome light | `public/brand/tendril-wordmark-inverse.svg` | Same |
| Symbol mark (tendril/curl glyph) | SVG | `public/brand/tendril-mark.svg` | Custom |
| Favicon set | `favicon.ico`, `icon.svg`, `apple-touch-icon.png` | `app/favicon.ico`, `app/icon.svg`, `app/apple-icon.png` | Generated from the symbol mark |
| OG image | `1200x630` PNG | `public/og.png` | Server-rendered via `next/og` from the symbol mark and tagline |
| Web manifest | JSON | `app/manifest.ts` | Generated programmatically |

The logo concept is a single-stroke geometric mark suggesting a tendril or curl: it reads as reach, growth, and connection without any literal botanical detail. It pairs with the wordmark in `Inter` semibold, tracking `-1`. All marks are single-color (charcoal `#171A1C` on light surface, white on dark surface). No gradients, no glow, no orbital decorations.

---

## 2. Typography

Self-hosted via `next/font/google` to keep the bundle predictable and avoid runtime CDN calls.

| Font | Weights | Use |
|---|---|---|
| Inter (Variable) | 400, 500, 600, 700 | All UI prose, table text, labels, buttons |
| JetBrains Mono | 400, 500 | Monospace excerpts in the Evidence Drawer only |

Tailwind theme exposes them as `font-sans` (Inter) and `font-mono` (JetBrains Mono). No third-party display font.

---

## 3. Icons

**Library:** [`lucide-react`](https://lucide.dev/) (ISC license).

Locked icon mapping per concept (so visual language stays consistent):

| Concept | Icon |
|---|---|
| Run scan | `Radar` |
| Live mode | `Radio` |
| Mock mode | `FlaskConical` |
| Evidence | `FileSearch` |
| Citation | `Quote` |
| Verified | `ShieldCheck` |
| Risk | `TriangleAlert` |
| Sales-ready | `Sparkles` |
| Near-miss | `Asterisk` |
| Approve | `Check` |
| Reject | `X` |
| Edit | `Pencil` |
| Account | `Building2` |
| Person / Champion | `User` / `UserStar` |
| Hiring | `Briefcase` |
| Tech stack | `Cpu` |
| Migration | `ArrowRightLeft` |
| Funding | `Banknote` |
| Product launch | `Rocket` |
| Leadership change | `Users` |
| Competitor mention | `Crosshair` |
| Champion move | `Compass` |
| Market event | `Flame` |
| Bright Data integration | custom SVG, see §6 |
| AI/ML API | custom SVG |
| Cognee | custom SVG |

If Lucide adds a better fit later, we update this table. We do not mix and match icon libraries.

---

## 4. Iconography For Signal Types

`SignalTypeChip` reads `signal_type` and renders the icon from §3 in `text-emerald-700` (sales-ready/verified), `text-amber-700` (inferred), or `text-zinc-600` (other). Icon size is fixed at 14px in chips and 16px in cards.

---

## 5. Illustrations

We need a small set of empty/error/loading illustrations. All are flat, abstract, single-accent-color line art on canvas. Drawn as SVG inline in `components/illustrations/`. No human figures, no faces, no devices. Pure geometric shapes.

| Asset | Location | Use |
|---|---|---|
| `EmptyAccounts` | `components/illustrations/empty-accounts.tsx` | `/accounts` zero state |
| `EmptyOutreach` | `components/illustrations/empty-outreach.tsx` | `/outreach` zero state |
| `EmptySignals` | `components/illustrations/empty-signals.tsx` | `/signals` zero state |
| `EmptyImport` | `components/illustrations/empty-import.tsx` | `/imports` first run |
| `ErrorState` | `components/illustrations/error-state.tsx` | Generic recoverable error |
| `ScanComplete` | `components/illustrations/scan-complete.tsx` | Live scan completion banner |
| `ScanFailed` | `components/illustrations/scan-failed.tsx` | Live scan failure banner |

Each illustration is rendered with the active accent token so it shifts with theme. They never include the wordmark.

---

## 6. Integration Marks

Stored in `public/brand/integrations/`. Each is the official 1-color SVG sourced once from the partner's brand page. Download URLs are tracked in this section so we can regenerate.

| Partner | File | Source |
|---|---|---|
| Bright Data | `bright-data.svg` | `https://brightdata.com/` brand assets, single-color treatment |
| AI/ML API | `aiml-api.svg` | `https://aimlapi.com/` brand kit |
| Cognee | `cognee.svg` | `https://cognee.ai/` brand kit |
| Triggerware | `triggerware.svg` | `https://triggerware.ai/` brand kit (only if used in v1) |
| Speechmatics | `speechmatics.svg` | `https://speechmatics.com/` brand kit (only if used in v1) |

If the partner restricts logo use, we fall back to a typeset name in `Inter` semibold and a generic chip.

---

## 7. Avatars

For seeded people (champions, contacts) we render a `MonogramAvatar` primitive:

- 32x32 or 40x40, rounded, hairline border.
- Two-letter initials in `Inter` 600.
- Background color from a deterministic hash of the person id, palette restricted to muted tones (no neon).
- No third-party headshots, no Gravatar, no DiceBear remote calls.

For account "logos" in the table, we render a `MonogramTile`:

- 24x24 rounded square.
- Two-letter initials.
- Background derived from `account.id` hash; foreground always charcoal.

---

## 8. Mock Data Fixtures (Frontend)

The backend already owns demo data via `backend/fixtures/seed_demo.csv` and `backend/fixtures/mock_*.json`. The frontend only needs:

| File | Purpose |
|---|---|
| `public/seed_demo.csv` | Static copy of the backend's seed CSV, used when the user clicks `Load demo seed` on `/imports`. Single source of truth: copied from `backend/fixtures/seed_demo.csv` at build time via a small npm script. |
| `lib/mock/demo-mode.ts` | Optional client-side fallback that mirrors the demo accounts if the backend is unreachable. Phase 4 only, gated behind a `?demo` URL flag, never on by default. |

We do not duplicate signals, briefs, or outreach drafts on the client. Anything dynamic comes from the backend.

---

## 9. Sound and Haptics

None. The product never plays a sound. No completion bell, no error chime. Not a chat product.

---

## 10. Animations

All driven by Framer Motion. The complete vocabulary:

| Token | Curve | Duration | Use |
|---|---|---|---|
| `fadeUp` | `[0.22, 1, 0.36, 1]` | 220ms | Card mount, panel mount, drawer body |
| `fadeIn` | `easeOut` | 160ms | Toasts, tooltips |
| `ringTween` | `linear` | 600ms | Score ring update on scan completion |
| `stepperProgress` | `easeInOut` | 280ms | Phase stepper advance |
| `chipPulse` | `easeOut` | 1.2s loop, only while live | Live mode chip in top bar |

`prefers-reduced-motion: reduce` removes all of the above except `fadeIn` (which becomes instant).

---

## 11. Copy Library

Centralized in `lib/copy.ts` so we can edit demo wording in one place. Locked phrases from the architecture §23:

```ts
export const COPY = {
  scan: {
    primary: "Run Live Scan",
    completionToast: "New account intelligence is ready",
  },
  badges: {
    salesReady: "Sales-ready",
    nearMiss: "Needs one more signal",
  },
  evidence: {
    button: "View evidence",
  },
  brief: {
    whyNow: "Why now",
  },
  outreach: {
    guardrailHeading: "Human approval required",
    approvedToast: "Draft approved and logged",
    rejectedToast: "Draft rejected",
  },
};
```

Anything user-facing that is not in `COPY` should be added here so we can audit tone in one pass.

---

## 12. Color Tokens (CSS Variables)

Defined in `app/globals.css` and exposed to Tailwind via `theme.extend.colors`:

```css
:root {
  --color-canvas: #F7F8F6;
  --color-surface: #FFFFFF;
  --color-raised: #F1F4F2;
  --color-text-primary: #171A1C;
  --color-text-secondary: #5D656B;
  --color-border: #DDE3E0;
  --color-accent-signal: #0F9F6E;
  --color-accent-cobalt: #3457D5;
  --color-accent-evidence: #C47A1D;
  --color-accent-risk: #C2413A;
  --color-accent-graph: #138A8A;
}
```

Tailwind config maps these to `bg-canvas`, `bg-surface`, `text-primary`, `text-secondary`, `border-default`, `text-signal`, `text-cobalt`, `text-evidence`, `text-risk`, `text-graph`. Anything outside these tokens is forbidden in component code.

---

## 13. Public Folder Layout

```
frontend/public/
  brand/
    tendril-wordmark.svg
    tendril-wordmark-inverse.svg
    tendril-mark.svg
    integrations/
      bright-data.svg
      aiml-api.svg
      cognee.svg
      triggerware.svg
      speechmatics.svg
  seed_demo.csv
  og.png
  robots.txt
```

```
frontend/app/
  favicon.ico
  icon.svg
  apple-icon.png
  manifest.ts
```

```
frontend/components/illustrations/
  empty-accounts.tsx
  empty-outreach.tsx
  empty-signals.tsx
  empty-import.tsx
  error-state.tsx
  scan-complete.tsx
  scan-failed.tsx
```

---

## 14. Acquisition Plan

What to do, in order, before Phase 1 implementation:

1. ~~Confirm brand name~~ — locked to **Tendril**.
2. Generate the wordmark SVG, mark SVG, and favicon set. Drop into `public/brand/` and `app/`.
3. Download partner integration SVGs into `public/brand/integrations/`. Note source URL inside this file.
4. Copy `backend/fixtures/seed_demo.csv` into `public/seed_demo.csv` via npm script (`pnpm sync:seed`).
5. Render `og.png` from `next/og`.
6. Write the seven illustration components.
7. Lock `lib/copy.ts`.
8. Lock `lib/colors.ts` and Tailwind config.
9. Begin Phase 1 of the requirements checklist.

Steps 2, 3, and 5 can happen in parallel with shell scaffolding; nothing here blocks code start.

---

## 15. Open Items

- [x] **Brand name** — locked to Tendril.
- [?] **Partner logo permission.** If any partner restricts external logo usage in non-affiliated products, we fall back to typeset names. Default: use 1-color marks at small sizes inside chips and credit screens, which is consistent with the partners' typical brand guidelines, but flag for legal review before any public release.
- [~] **OG image content.** Default: monochrome wordmark + tagline `Live GTM change intelligence` on canvas. Override if you want a more promotional treatment.
- [~] **Hackathon attribution.** Footer or `/settings` page mentions "Built for the Bright Data Web Data Unlocked Hackathon" in `/settings` only, never in the main shell.
