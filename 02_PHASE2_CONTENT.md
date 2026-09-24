PHASE 2 — Content system, case studies, Lab, About. Read `AGENTS.md` and `SITE_SPEC.md` first; both are binding. Phase 1 is done and deployed. Still no motion.

## 1. Content collections (`src/content.config.ts`)
```ts
projects: {
  title, slug, summary,              // summary ≤ 140 chars, problem- or result-first
  kind: 'client' | 'engineering',
  status: 'shipped' | 'prototype' | 'research',
  restricted: boolean,               // true → no repo link, no internals
  year, role: string[], stack: string[],
  cover: image(), coverAlt,
  featured: boolean, order: number,
  outcome?: string,                  // verified only
  demoUrl?, repoUrl?,                // repoUrl rejected by schema if restricted
  specs?: { label: string; value: string }[]   // rendered in Plex Mono
}
lab: {
  title, slug, status: 'concept' | 'prototype' | 'validated' | 'archived',
  date, discipline, artifact: image(), artifactAlt, hypothesis,
  model?: string,                    // GLB path for the hardware hall
  telemetry?: string                 // CSV path
}
```
Add a Zod refinement: `restricted && repoUrl` → build error.

## 2. Templates
- `ClientCase.astro`: Problem → Constraints → Approach → Solution → Implementation → Outcome → Next improvements → CTA "Build something similar" (links to /contact with `?type=` prefilled).
- `EngineeringCase.astro`: Objective → Architecture → Constraints → Hardware/firmware → Bench setup → Measurements → Failures & iterations → Status → Links.
- Oxblood full-bleed header on both, with title, one-line summary, role, year, and specs.
- Architecture diagrams as inline SVG components (HTML text labels, not text baked into images).
- Every case ends with prev/next project links + CTA.

## 3. Content files (MDX)
Only from `SITE_SPEC.md §6`. Leave empty sections as visible `TODO(vedant)` blocks in dev and hide them in production builds.
- `client-case-1.mdx`: placeholder structure (candidate: the IoT & Robotics Club site)
- `saarthi.mdx`: full engineering case, flagship
- `prahari.mdx`: engineering, `restricted: true`
- `vajra.mdx`: engineering, `restricted: true`
- Lab: `skynet-setu.mdx`, `saarthi-fusion-benchmark.mdx`, plus 1 placeholder

## 4. Pages
- `/projects`: filter All / Client work / Engineering as real links (`?kind=`), so it works without JS. The first card is large; the rest sit in an asymmetric 2-column grid. Cards show kind, title, summary, role. No tech tags.
- `/projects/[slug]`: template chosen by `kind`.
- `/lab`: hardware hall placeholder block at the top (static images for now), then entries grouped by status.
- `/lab/[slug]`.
- `/about`: photo, 3 short paragraphs (who, why software + hardware, how I work), roles, résumé link. No skill logos.
- Home: wire Selected Work, Lab preview, and Hardware hall strip to the collections.

## 5. Asset checklist
Generate `ASSETS.md` listing every image/model/CSV the site expects: path, dimensions, format, max size, and what the shot must show (e.g. "Saarthi top-down, board centered, diffuse light, 2400×1600").

The hero photo brief must also require:
- The left third of the frame is dark bench with no board in it: on desktop the headline overlaps the photo's left edge, and text must stay readable without a scrim.
- All 4 mounting holes are visible and unobstructed: they are the registration points for aligning the X-ray (KiCad) layer in Phase 3.
- Budgets: desktop source ≤ 150 KB, mobile 4:3 crop ≤ 60 KB (AVIF).

## Report back
Screenshots of each template at 375/1440 · Lighthouse · the `ASSETS.md` · all TODOs.

Do not start Phase 3.
